"""Bộ chấm headless dùng chung cho CLI và giao diện.

Luồng: chạy run(ctx) trên từng case (World mới) → oracle phát lại trace →
kiểm tra tiêu chí trong rubric.json bằng state/trace thật → báo cáo report/1.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from engine import ENGINE_VERSION
from engine.contracts.report import REPORT_SCHEMA
from engine.execution.inproc import run_case
from engine.execution.runner import run_case_isolated
from engine.grading.hashing import level_source_hash
from engine.grading.oracle import replay
from engine.world.scenario import load_scenario

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_PATH = Path(__file__).with_name("rubric.json")
PUBLIC_DIR = PROJECT_ROOT / "scenarios" / "levels"
HIDDEN_DIR = PROJECT_ROOT / "teacher" / "scenarios" / "hidden"

TOOL_ACTIONS = ("move_to", "repair", "rescue", "charge", "say")
STATUS_TEXT = {"error": "code bị lỗi giữa chừng", "timeout": "chạy quá thời gian", "crash": "worker dừng bất thường",
               "action_limit": "gọi quá nhiều hành động (có thể vòng lặp không dừng)", "cancelled": "lượt chạy bị hủy"}


class ToolError(Exception):
    """Lỗi của công cụ chấm (không phải lỗi bài làm)."""


def load_rubric(path=RUBRIC_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def available_levels(rubric=None):
    """Các màn đã được phát hành (có đủ scenario công bố). Bản luyện tập có thể chưa có màn nào."""
    rubric = rubric or load_rubric()
    result = []
    for level in sorted(rubric["levels"], key=int):
        cases = {c["case"] for c in rubric["criteria"] if str(c["level"]) == level}
        if all((PUBLIC_DIR / f"level{level}" / f"{case}.json").exists() for case in cases):
            result.append(int(level))
    return result


def scenario_path(level, case_id, mode):
    if mode == "official" and int(level) > 0:
        path = HIDDEN_DIR / f"level{level}" / f"{case_id}.json"
        if not path.exists():
            raise ToolError(f"Thiếu biến thể chính thức {path}. Bản học viên chỉ chấm thử trên bản đồ công bố.")
        return path
    return PUBLIC_DIR / f"level{level}" / f"{case_id}.json"


# ----------------------------------------------------------------------
# Kiểm tra từng loại tiêu chí. Mỗi hàm trả (passed, evidence).
# ----------------------------------------------------------------------

def _actions(events):
    return [e for e in events if e["kind"] == "action"]


def _calls(events, call):
    return [e for e in events if e["kind"] == "call_start" and e.get("call") == call]


def _inside(events, n):
    return [e for e in _actions(events) if e.get("via") and e["via"].get("n") == n]


def _check_goal(crit, case):
    world = case["world"]
    goal = next((g for g in world.goals if g["id"] == crit["goal"]), None)
    if goal is None:
        return False, "Scenario không có mục tiêu này."
    done = world.goal_done(goal)
    return done, ("Đạt: " if done else "Chưa đạt: ") + goal.get("text", goal["id"])


def _check_all_goals(_crit, case):
    goals = case["world"].goal_status()
    done = sum(1 for g in goals if g["done"])
    if case["status"] != "complete":
        why = STATUS_TEXT.get(case["status"], "lượt chạy dừng giữa chừng")
        return False, f"Đạt {done}/{len(goals)} mục tiêu nhưng {why}."
    return done == len(goals), f"Đạt {done}/{len(goals)} mục tiêu của tình huống."


def _successful_act_dispatches(events):
    """Dispatch của lớp học viên tạo ≥1 hành động sửa/cứu ok của chính robot đó."""
    result = []
    for call in _calls(events, "dispatch"):
        if not call.get("student_class"):
            continue
        good = [a for a in _inside(events, call["n"])
                if a["ok"] and a["action"] in ("repair", "rescue") and a["actor"] == call["obj"]]
        if good:
            result.append((call, good))
    return result


def _check_planner_use(_crit, case):
    events = case["events"]
    for call in _calls(events, "planner"):
        if not call.get("student_class"):
            continue
        delivered = [a for a in _inside(events, call["n"])
                     if a["ok"] and a["action"] == "unload" and a.get("data", {}).get("delivered")]
        if delivered:
            return True, f"Planner '{call['obj']}' đã giao {len(delivered)} kiện trong execute()."
        return False, "Có planner nhưng chưa giao được kiện nào trong execute()."
    return False, "Chưa dùng ctx.use_planner với lớp con PlannerBase của bạn."


def _check_planner_state(_crit, case):
    events = case["events"]
    for call in _calls(events, "planner"):
        delivered = {a["args"]["package_id"] for a in _inside(events, call["n"])
                     if a["ok"] and a["action"] == "unload" and a.get("data", {}).get("delivered")}
        report = next((e for e in events if e["kind"] == "planner_report" and e["n"] == call["n"]), None)
        if report is None:
            return False, "execute() lỗi nên chưa đọc được report()."
        if not report.get("valid_type"):
            return False, "report() phải trả về list id kiện."
        reported = set(report["ids"])
        if delivered and reported == delivered:
            return True, f"report() khớp {len(delivered)} kiện đã giao."
        return False, f"report() ghi {len(reported)} kiện, thực tế giao {len(delivered)} kiện trong execute()."
    return False, "Chưa dùng ctx.use_planner."


def _student_registered(events):
    return [a for a in _actions(events)
            if a["action"] == "register" and a["ok"] and (a.get("meta") or {}).get("student_class")]


def _check_oop_init(_crit, case):
    regs = _student_registered(case["events"])
    if regs:
        return True, f"Đã đăng ký {len(regs)} robot lớp con: " + ", ".join(r["meta"]["cls"] for r in regs)
    return False, "Chưa có robot lớp con RobotBase nào đăng ký thành công."


def _check_oop_profile(_crit, case):
    events = case["events"]
    for reg in _student_registered(events):
        if any(a["ok"] and a["actor"] == reg["actor"] and a["action"] in TOOL_ACTIONS for a in _actions(events)):
            return True, f"Robot {reg['actor']} đã hành động bằng id của slot."
    return False, "Robot lớp con chưa thực hiện hành động thành công nào."


def _check_oop_act(_crit, case):
    good = _successful_act_dispatches(case["events"])
    if good:
        call, actions = good[0]
        return True, f"{call['cls']}.act() của {call['obj']} đã {actions[0]['action']} thành công."
    if _calls(case["events"], "dispatch"):
        return False, "Đã dispatch nhưng act() chưa tạo hành động sửa/cứu thành công."
    return False, "Có lớp con nhưng chưa được gọi qua ctx.dispatch trong lượt này."


def _check_oop_act2(_crit, case):
    owners = {}
    for call, actions in _successful_act_dispatches(case["events"]):
        for action in actions:
            owners.setdefault(call["act_owner"], set()).add(action["action"])
    kinds = set().union(*owners.values()) if owners else set()
    if len(owners) >= 2 and kinds >= {"repair", "rescue"}:
        return True, f"{len(owners)} lớp khác nhau override act cho cả sửa chữa và cứu hộ."
    return False, f"Có {len(owners)} lớp act thành công, chuyên môn: {sorted(kinds) or 'chưa có'}."


def _check_oop_poly(_crit, case):
    objs = {c["obj"] for c in _calls(case["events"], "dispatch") if c.get("student_class")}
    if len(objs) >= 2:
        return True, f"{len(objs)} object được gọi qua cùng giao diện dispatch: {', '.join(sorted(objs))}."
    return False, f"Mới dispatch {len(objs)} object robot của bạn."


def _check_oop_separate(_crit, case):
    events = case["events"]
    active = set()
    for call in _calls(events, "dispatch"):
        if call.get("student_class") and any(a["ok"] and a["actor"] == call["obj"] for a in _inside(events, call["n"])):
            active.add(call["obj"])
    if len(active) >= 2:
        return True, f"{len(active)} robot có hành động và trạng thái riêng: {', '.join(sorted(active))}."
    return False, f"Mới có {len(active)} robot hành động thành công trong lượt act của chính nó."


CHECKS = {
    "goal": _check_goal, "all_goals": _check_all_goals,
    "planner_use": _check_planner_use, "planner_state": _check_planner_state,
    "oop_init": _check_oop_init, "oop_profile": _check_oop_profile, "oop_act": _check_oop_act,
    "oop_act2": _check_oop_act2, "oop_poly": _check_oop_poly, "oop_separate": _check_oop_separate,
}


# ----------------------------------------------------------------------
# Chấm
# ----------------------------------------------------------------------

def run_and_replay(entry, submission_dir, scenario, run_id, isolate=True, cancel=None):
    """Chạy một case (mặc định trong worker subprocess) rồi phát lại trace bằng oracle."""
    if isolate:
        result = run_case_isolated(entry, submission_dir, scenario, run_id=run_id, cancel=cancel)
    else:
        result = run_case(entry, submission_dir, scenario, run_id=run_id)
    world, problems = replay(scenario, result["events"])
    result["world"] = world
    result["problems"] = problems
    return result


def grade_level(level, submission_dir, mode="public", rubric=None, run_id=None, cancel=None):
    rubric = rubric or load_rubric()
    level = str(level)
    info = rubric["levels"][level]
    submission_dir = Path(submission_dir).resolve()
    entry = submission_dir / info["file"]
    run_id = run_id or uuid.uuid4().hex[:12]
    criteria = [c for c in rubric["criteria"] if str(c["level"]) == level]
    case_ids = []
    for crit in criteria:
        if crit["case"] not in case_ids:
            case_ids.append(crit["case"])
    cases = {}
    for case_id in case_ids:
        scenario = load_scenario(scenario_path(level, case_id, mode))
        cases[case_id] = run_and_replay(entry, submission_dir, scenario, run_id, cancel=cancel)
    results = []
    for crit in criteria:
        case = cases[crit["case"]]
        if case["problems"]:
            passed, evidence = False, "Trace không khớp luật engine: " + case["problems"][0]
        else:
            passed, evidence = CHECKS[crit["check"]](crit, case)
        results.append({"id": crit["id"], "text": crit["text"], "case": crit["case"],
                        "points": crit["points"] if passed else 0, "max": crit["points"],
                        "passed": passed, "evidence": evidence, "hint": None if passed else crit["hint"]})
    case_reports = []
    for case_id, case in cases.items():
        goals = case["world"].goal_status()
        case_reports.append({"case_id": case_id, "status": case["status"], "scoring": True,
                             "goals_done": sum(1 for g in goals if g["done"]), "goals_total": len(goals),
                             "error": case["error"], "log": case["log"][-16000:],
                             "trace_valid": not case["problems"], "events": len(case["events"])})
    statuses = {c["status"] for c in case_reports}
    status = "complete" if statuses == {"complete"} else ("error" if "error" in statuses else "partial")
    return {"level": int(level), "title": info["title"], "file": info["file"],
            "score": sum(r["points"] for r in results), "max": info["max"], "status": status,
            "criteria": results, "cases": case_reports}


def current_hashes(submission_dir, levels=None, rubric=None):
    """Hash source hiện tại của từng màn (dùng để phát hiện kết quả cũ cần chấm lại)."""
    rubric = rubric or load_rubric()
    levels = [str(x) for x in (levels if levels is not None else sorted(rubric["levels"]))]
    names = [info["file"] for info in rubric["levels"].values()]
    return {lv: level_source_hash(submission_dir, rubric["levels"][lv]["file"], names) for lv in levels}


def grade_submission(submission_dir, levels=None, mode="public", rubric=None, cancel=None):
    """Chấm các màn và trả report/1 (dict)."""
    rubric = rubric or load_rubric()
    levels = [str(x) for x in (levels if levels is not None else available_levels(rubric))]
    run_id = uuid.uuid4().hex[:12]
    level_reports = [grade_level(lv, submission_dir, mode, rubric, run_id, cancel) for lv in levels]
    hashes = current_hashes(submission_dir, levels, rubric)
    return {
        "schema_version": REPORT_SCHEMA, "assessment_id": rubric["assessment_id"],
        "engine_version": ENGINE_VERSION, "rubric_version": rubric["rubric_version"],
        "source_hashes": hashes, "run_id": run_id, "mode": mode,
        "levels": level_reports, "total": sum(r["score"] for r in level_reports),
        "max_total": sum(rubric["levels"][lv]["max"] for lv in levels),
        "levels_released": [int(lv) for lv in levels],
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
