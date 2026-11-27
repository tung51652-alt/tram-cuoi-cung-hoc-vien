"""Kiểm tra bài luyện màn 0. Kết quả có nhãn LUYỆN TẬP, không vào tổng điểm bài kiểm tra.

    python -m engine.grading.practice --exercise p03 [--submission student]
"""

import argparse
import sys
import uuid
from pathlib import Path

from engine.grading.feedback import format_error
from engine.grading.grader import CHECKS, PROJECT_ROOT, run_and_replay
from engine.world.scenario import load_scenario

PRACTICE_DIR = PROJECT_ROOT / "scenarios" / "practice"
PRACTICE_LABEL = "LUYỆN TẬP — không tính điểm bài kiểm tra"


def list_exercises():
    return [load_scenario(path) for path in sorted(PRACTICE_DIR.glob("p*.json"))]


def check_exercise(exercise_id, submission_dir, run_id=None, cancel=None):
    """Chạy một bài luyện. Chỉ nạp file của bài đó (và helper cấp gốc nếu file import)."""
    scenario = load_scenario(PRACTICE_DIR / f"{exercise_id}.json")
    submission_dir = Path(submission_dir).resolve()
    entry = submission_dir / "practice" / scenario["file"]
    case = run_and_replay(entry, submission_dir, scenario, run_id or uuid.uuid4().hex[:12], cancel=cancel)
    checks = []
    for spec in scenario["checks"]:
        if case["problems"]:
            passed, evidence = False, "Trace không khớp luật engine."
        else:
            passed, evidence = CHECKS[spec["type"]](spec, case)
        checks.append({"text": spec["text"], "passed": passed, "evidence": evidence})
    goals = case["world"].goal_status()
    return {"mode": "practice", "label": PRACTICE_LABEL, "scoring": False, "exercise": exercise_id,
            "title": scenario["title"], "status": case["status"], "error": case["error"], "log": case["log"][-2000:],
            "done": all(c["passed"] for c in checks), "checks": checks, "goals": goals, "hints": scenario["hints"],
            "events": case["events"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chạy thử bài luyện màn 0.")
    parser.add_argument("--exercise", required=True)
    parser.add_argument("--submission", default="student")
    args = parser.parse_args(argv)
    result = check_exercise(args.exercise, args.submission)
    print(f"[{result['label']}] {result['exercise']} — {result['title']}: "
          f"{'HOÀN THÀNH' if result['done'] else 'chưa xong'}")
    for check in result["checks"]:
        print(f"   {'✓' if check['passed'] else '✗'} {check['text']}: {check['evidence']}")
    if result["error"]:
        print("\n".join(format_error(result["error"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
