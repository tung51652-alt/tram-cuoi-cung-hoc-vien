"""Cửa sổ game chính: chọn màn, tự chạy code học viên, phát hoạt cảnh, chấm điểm.

Vòng lặp chính không bao giờ chờ worker: chạy code qua RunManager (poll mỗi
khung hình), chấm điểm trong một luồng nền có thể hủy. Đóng cửa sổ hoặc Ctrl+C
sẽ hủy lượt chấm và thu hồi mọi worker.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import pygame

from engine import ENGINE_VERSION
from engine import persistence as store
from engine.execution.runner import Cancelled, RunManager
from engine.grading.grader import (available_levels, current_hashes, grade_level, grade_submission, load_rubric,
                                   scenario_path)
from engine.grading.practice import PRACTICE_DIR, PRACTICE_LABEL, check_exercise, list_exercises
from engine.world.scenario import load_scenario
from game_ui import content, theme
from game_ui.components.widgets import Button, Overlay
from game_ui.drawing import primitives as P
from game_ui.frame import compose
from game_ui.playback import TracePlayer

ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT / "assets" / "demo"
LEVEL_POINTS = {0: 5, 1: 20, 2: 30, 3: 45}


class App:
    def __init__(self, submission="student", level=None, practice=None, demo=False, size=(1280, 720)):
        self.rubric = load_rubric()
        self.submission = Path(submission).resolve()
        self.settings, warning = store.load_settings()
        self.released = available_levels(self.rubric)
        self.locked_notice = None
        if level is not None:
            if int(level) in self.released:
                self.settings.update(view="level", level=int(level))
            else:
                self.locked_notice = f"Màn {level} chưa mở. Các màn kiểm tra mở vào ngày kiểm tra."
        if practice:
            self.settings.update(view="practice", exercise=practice)
        self.demo = demo
        if self.settings["view"] == "level" and self.settings["level"] not in self.released:
            self.settings["view"] = "practice"
        self.demo = demo and bool(self.released)
        if self.demo and self.settings["view"] == "practice":
            self.settings.update(view="level", level=self.released[0])
        self.exercises = list_exercises()
        if self.settings["exercise"] not in [e["id"] for e in self.exercises]:
            self.settings["exercise"] = self.exercises[0]["id"]
        self.manager = RunManager()
        self.player = TracePlayer([])
        self.running_since = None
        self.last_result = None
        self.paused = False
        self.t = 0.0
        self.panel_scroll = 0
        self.overlay = None
        self.toasts = []
        if warning:
            self.toast(warning, "warn")
        if self.locked_notice:
            self.toast(self.locked_notice, "warn", 6)
        if demo and not self.demo:
            self.toast("Bản này chưa có demo các màn kiểm tra.", "warn", 6)
        self.report, warning = store.read_json(store.RESULTS)
        if warning:
            self.toast(warning, "warn")
        progress, warning = store.read_json(store.PRACTICE)
        self.practice_progress = progress or {}
        self.hints_shown = {}
        self.grade_thread = None
        self.grade_cancel = threading.Event()
        self.grade_outcome = None
        self.grade_label = ""
        self.window_size = size
        self._build_buttons()

    # ------------------------------------------------------------------
    # Tiện ích
    # ------------------------------------------------------------------

    def toast(self, text, kind="ok", seconds=4.0):
        self.toasts.append([text, kind, seconds])

    @property
    def in_practice(self):
        return self.settings["view"] == "practice" and not self.demo

    def mode(self):
        if self.demo:
            return "demo"
        return "practice" if self.in_practice else "public"

    def save_settings(self):
        try:
            store.save_settings(self.settings)
        except OSError as exc:
            self.toast(f"Không lưu được cài đặt: {exc}", "warn")

    def _build_buttons(self):
        self.tabs = []
        x = 196
        if not self.demo:
            self.tabs.append(Button(("practice", None), "Luyện tập", (x, 6, 104, 28)))
            x += 110
        for level in range(4):
            label = f"Màn {level} · {LEVEL_POINTS[level]}đ" if level in self.released else f"Màn {level} · chưa mở"
            self.tabs.append(Button(("level", level), label, (x, 6, 112, 28)))
            x += 118
        y = theme.BOTTOM_BAR.top + 5
        self.actions = []
        x = 10
        for key, label, hotkey, width, primary in (
            ("run", "Chạy lại code", "F5", 150, True), ("grade", "Chấm màn này", "F6", 148, False),
            ("grade_all", "Chấm cả bài", "F7", 134, False), ("tools", "Đề & công cụ", "F1", 140, False),
            ("results", "Kết quả", "F2", 110, False),
        ):
            self.actions.append(Button(key, label, (x, y, width, 30), hotkey, primary))
            x += width + 8
        x = theme.BOTTOM_BAR.right - 10
        for key, label, width in (("reduced", "Ít hiệu ứng", 110), ("speed2", "2x", 44), ("speed1", "1x", 44),
                                  ("speed05", "0.5x", 50), ("pause", "Tạm dừng", 104)):
            x -= width
            self.actions.append(Button(key, label, (x, y, width, 30)))
            x -= 6
        self.practice_buttons = []
        for i, ex in enumerate(self.exercises):
            self.practice_buttons.append(Button(("exercise", ex["id"]), ex["id"][1:].lstrip("0") or ex["id"],
                                                (theme.PANEL.left + 16 + i * 44, theme.PANEL.top + 8, 38, 26)))
        self.practice_buttons.append(Button("reset_practice", "Xóa tiến độ",
                                            (theme.PANEL.right - 104, theme.PANEL.top + 8, 92, 26)))

    def _refresh_buttons(self):
        for tab in self.tabs:
            view, level = tab.key
            tab.active = (view == "practice" and self.in_practice) or (
                view == "level" and not self.in_practice and level == self.settings["level"])
            tab.dimmed = view == "level" and level not in self.released
        grading = self.grade_thread is not None
        for button in self.actions:
            button.active = False
            if button.key in ("grade", "grade_all", "results"):
                button.enabled = not self.demo and not grading
            if button.key == "grade_all":
                button.enabled = button.enabled and bool(self.released)
            if button.key == "grade":
                button.label = "Kiểm tra bài" if self.in_practice else "Chấm màn này"
            if button.key == "pause":
                button.active = self.paused
                button.label = "Tiếp tục" if self.paused else "Tạm dừng"
            if button.key.startswith("speed"):
                button.active = {"speed05": 0.5, "speed1": 1.0, "speed2": 2.0}[button.key] == self.settings["speed"]
            if button.key == "reduced":
                button.active = self.settings["reduced_motion"]
        for button in self.practice_buttons:
            if button.key != "reset_practice":
                ex_id = button.key[1]
                button.active = ex_id == self.settings["exercise"]

    # ------------------------------------------------------------------
    # Chạy code và chấm
    # ------------------------------------------------------------------

    def current_target(self):
        if self.in_practice:
            scenario = load_scenario(PRACTICE_DIR / f"{self.settings['exercise']}.json")
            return self.submission / "practice" / scenario["file"], scenario
        level = self.settings["level"]
        scenario = load_scenario(scenario_path(level, f"L{level}-main", "public"))
        return self.submission / self.rubric["levels"][str(level)]["file"], scenario

    def start_run(self):
        """Nạp source mới và reset thế giới: mỗi lần là một worker mới."""
        self.paused = False
        self.panel_scroll = 0
        if self.demo:
            self.player = TracePlayer(self._demo_events(self.settings["level"]))
            return
        entry, scenario = self.current_target()
        self.player = TracePlayer([{"kind": "start", "state": {**scenario, "goals": [
            {**g, "done": False} for g in scenario.get("goals", [])]}}])
        self.manager.submit("view", entry=entry, submission_root=self.submission, scenario=scenario)
        self.running_since = self.t

    def _demo_events(self, level):
        path = DEMO_DIR / f"level{level}.jsonl"
        events = []
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        except (OSError, ValueError):
            self.toast(f"Thiếu dữ liệu demo {path.name}.", "warn")
        return events

    def poll_run(self):
        self.manager.poll()
        result = self.manager.finished.pop("view", None)
        if result is None:
            return
        self.running_since = None
        self.last_result = result
        self.player = TracePlayer(result["events"])
        if result["status"] in ("timeout", "crash") and not result["events"]:
            self.player.banner = ("timeout", result["error"]["message"] + " " + (result["error"].get("hint") or ""))

    def start_grade(self, kind):
        if self.grade_thread is not None or self.demo:
            return
        self.grade_cancel.clear()
        self.grade_outcome = None
        if kind == "grade" and self.in_practice:
            ex = self.settings["exercise"]
            self.grade_label = f"Đang kiểm tra bài luyện {ex}…"
            job = lambda: ("practice", check_exercise(ex, self.submission, cancel=self.grade_cancel))
        elif kind == "grade":
            level = self.settings["level"]
            self.grade_label = f"Đang chấm màn {level}…"
            job = lambda: ("level", grade_level(level, self.submission, cancel=self.grade_cancel))
        else:
            self.grade_label = "Đang chấm cả bài (4 màn)…"
            job = lambda: ("all", grade_submission(self.submission, levels=self.released, cancel=self.grade_cancel))

        def worker():
            try:
                self.grade_outcome = job()
            except Cancelled:
                self.grade_outcome = ("cancelled", None)
            except Exception as exc:  # noqa: BLE001 — lỗi công cụ, hiện cho người dùng thay vì làm sập game
                self.grade_outcome = ("tool_error", str(exc))

        self.grade_thread = threading.Thread(target=worker, daemon=True)
        self.grade_thread.start()

    def poll_grade(self):
        if self.grade_thread is None or self.grade_thread.is_alive():
            return
        self.grade_thread = None
        kind, data = self.grade_outcome or ("tool_error", "không rõ")
        if kind == "practice":
            self.practice_progress[data["exercise"]] = {
                "done": data["done"], "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            try:
                store.write_json(store.PRACTICE, self.practice_progress)
            except OSError:
                pass
            self.player = TracePlayer(data["events"])
            self.overlay = Overlay(f"{PRACTICE_LABEL}: {data['exercise']} — {data['title']}",
                                   practice_lines(data), theme.GREEN)
        elif kind == "level":
            self.overlay = Overlay(f"Kết quả màn {data['level']} (điểm thử trên bản đồ công bố)",
                                   level_lines(data), theme.CYAN)
            self._merge_level_report(data)
        elif kind == "all":
            self.report = data
            try:
                store.write_json(store.RESULTS, data)
            except OSError as exc:
                self.toast(f"Không lưu được kết quả: {exc}", "warn")
            self.open_results()
        elif kind == "tool_error":
            self.toast(f"Lỗi công cụ chấm (không phải lỗi bài): {data}", "warn", 8)

    def _merge_level_report(self, level_report):
        """Cập nhật màn vừa chấm vào báo cáo đã lưu (các màn khác giữ nguyên, có hash riêng)."""
        hashes = current_hashes(self.submission, [level_report["level"]], self.rubric)
        report = self.report if self.report and self.report.get("rubric_version") == self.rubric["rubric_version"] else None
        if report is None:
            report = {"schema_version": "report/1", "assessment_id": self.rubric["assessment_id"],
                      "engine_version": ENGINE_VERSION, "rubric_version": self.rubric["rubric_version"],
                      "source_hashes": {}, "levels": [], "mode": "public"}
        report["levels"] = [lv for lv in report["levels"] if lv["level"] != level_report["level"]] + [level_report]
        report["levels"].sort(key=lambda lv: lv["level"])
        report["source_hashes"][str(level_report["level"])] = hashes[str(level_report["level"])]
        report["total"] = sum(lv["score"] for lv in report["levels"])
        report["max_total"] = sum(LEVEL_POINTS[lv["level"]] for lv in report["levels"])
        report["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.report = report
        try:
            store.write_json(store.RESULTS, report)
        except OSError:
            pass

    def open_results(self):
        if not self.report:
            self.overlay = Overlay("Kết quả", [("p", "Chưa có kết quả. Bấm \"Chấm cả bài\" (F7) để chấm.")])
            return
        stale = store.staleness(self.report, current_hashes(self.submission, rubric=self.rubric),
                                self.rubric["rubric_version"], ENGINE_VERSION)
        self.overlay = Overlay("Kết quả đã lưu (chạy thử trên bản đồ công bố)", report_lines(self.report, stale))

    def open_tools(self):
        if self.in_practice:
            scenario = load_scenario(PRACTICE_DIR / f"{self.settings['exercise']}.json")
            ex = scenario["id"]
            shown = self.hints_shown.get(ex, 0)
            lines = [("h", scenario["title"]), ("p", scenario["description"]),
                     ("muted", f"File: student/practice/{scenario['file']}"), ("h", "Gợi ý")]
            for i, hint in enumerate(scenario["hints"]):
                lines.append(("todo", hint) if i < shown else ("muted", f"Gợi ý {i + 1}: nhấn H để mở"))
            lines += content.reference_lines(0)[0:]
            self.overlay = Overlay(f"Bài luyện {ex} — {PRACTICE_LABEL}", lines, theme.GREEN)
            return
        level = self.settings["level"]
        _, scenario = self.current_target()
        lines = [("h", scenario.get("title", "")), ("p", scenario.get("description", "")),
                 ("muted", f"File của bạn: student/{self.rubric['levels'][str(level)]['file']}"), ("h", "Mục tiêu và điểm")]
        for crit in self.rubric["criteria"]:
            if crit["level"] == level:
                lines.append(("todo", f"{crit['text']} — {crit['points']} điểm"))
        lines += content.reference_lines(level)
        self.overlay = Overlay(f"Màn {level} — đề và công cụ", lines)

    # ------------------------------------------------------------------
    # Sự kiện
    # ------------------------------------------------------------------

    def select(self, view, level=None, exercise=None):
        if view == "level" and level not in self.released:
            self.toast(f"Màn {level} mở vào ngày kiểm tra. Khi đó hãy cập nhật bản mới (git pull hoặc tải lại).",
                       "warn", 5)
            return
        if view == "practice":
            self.settings["view"] = "practice"
            if exercise:
                self.settings["exercise"] = exercise
        else:
            self.settings.update(view="level", level=level)
        self.save_settings()
        self.start_run()

    def action(self, key):
        if key == "run":
            self.start_run()
        elif key in ("grade", "grade_all"):
            self.start_grade(key)
        elif key == "tools":
            self.open_tools()
        elif key == "results" and not self.demo:
            self.open_results()
        elif key == "pause":
            self.paused = not self.paused
        elif key.startswith("speed"):
            self.settings["speed"] = {"speed05": 0.5, "speed1": 1.0, "speed2": 2.0}[key]
            self.save_settings()
        elif key == "reduced":
            self.settings["reduced_motion"] = not self.settings["reduced_motion"]
            self.save_settings()
        elif key == "reset_practice":
            self.practice_progress = {}
            self.hints_shown = {}
            try:
                store.write_json(store.PRACTICE, {})
            except OSError:
                pass
            self.toast("Đã xóa tiến độ luyện tập (bài làm và kết quả chính thức giữ nguyên).")

    def to_logical(self, pos):
        win_w, win_h = self.window_size
        scale = min(win_w / theme.LOGICAL_SIZE[0], win_h / theme.LOGICAL_SIZE[1])
        off_x = (win_w - theme.LOGICAL_SIZE[0] * scale) / 2
        off_y = (win_h - theme.LOGICAL_SIZE[1] * scale) / 2
        return (pos[0] - off_x) / scale, (pos[1] - off_y) / scale

    def handle(self, event):
        """Trả False khi cần thoát."""
        if event.type == pygame.QUIT:
            return False
        if event.type in (pygame.VIDEORESIZE, pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
            self.window_size = pygame.display.get_surface().get_size()
            return True
        pos = self.to_logical(getattr(event, "pos", pygame.mouse.get_pos()))
        if self.overlay is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h and self.in_practice:
                ex = self.settings["exercise"]
                self.hints_shown[ex] = self.hints_shown.get(ex, 0) + 1
                self.open_tools()
                return True
            if self.overlay.handle(event, pos) == "close":
                self.overlay = None
            return True
        if event.type == pygame.KEYDOWN:
            keys = {pygame.K_F5: "run", pygame.K_F6: "grade", pygame.K_F7: "grade_all", pygame.K_F1: "tools",
                    pygame.K_F2: "results", pygame.K_SPACE: "pause"}
            if event.key in keys:
                self.action(keys[event.key])
            elif event.key == pygame.K_ESCAPE:
                return False
        elif event.type == pygame.MOUSEWHEEL:
            if theme.PANEL.collidepoint(pos):
                self.panel_scroll = max(0, self.panel_scroll + event.y * 2)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tab in self.tabs:
                if tab.hit(pos):
                    self.select(tab.key[0], level=tab.key[1])
                    return True
            for button in self.actions:
                if button.hit(pos):
                    self.action(button.key)
                    return True
            if self.in_practice:
                for button in self.practice_buttons:
                    if button.hit(pos):
                        if button.key == "reset_practice":
                            self.action("reset_practice")
                        else:
                            self.select("practice", exercise=button.key[1])
                        return True
        return True

    # ------------------------------------------------------------------
    # Vẽ
    # ------------------------------------------------------------------

    def draw(self, screen, field):
        self._refresh_buttons()
        compose(screen, field, self.player, self.t, self.mode(), self.settings["speed"], self.paused,
                reduced_motion=self.settings["reduced_motion"], panel_scroll=self.panel_scroll, draw_bars=False,
                panel_rect=theme.PANEL.inflate(0, -42).move(0, 21) if self.in_practice else None)
        if self.in_practice:
            band = pygame.Rect(theme.PANEL.left + 2, theme.PANEL.top, theme.PANEL.width - 2, 42)
            pygame.draw.rect(screen, theme.PANEL_BG, band)
            pygame.draw.line(screen, theme.PANEL_LINE, band.bottomleft, band.bottomright)
        mouse = self.to_logical(pygame.mouse.get_pos())
        self._top_bar(screen, mouse)
        pygame.draw.rect(screen, theme.PANEL_BG, theme.BOTTOM_BAR)
        pygame.draw.line(screen, theme.PANEL_LINE, theme.BOTTOM_BAR.topleft, theme.BOTTOM_BAR.topright, 2)
        for button in self.actions:
            button.draw(screen, button.rect.collidepoint(mouse))
        if self.in_practice:
            for button in self.practice_buttons:
                button.draw(screen, button.rect.collidepoint(mouse))
                if button.key != "reset_practice" and self.practice_progress.get(button.key[1], {}).get("done"):
                    P.icon(screen, "ok", (button.rect.right - 4, button.rect.top + 3), 4)
        if self.running_since is not None:
            self._busy(screen, "Đang chạy code của bạn…", self.t - self.running_since)
        if self.grade_thread is not None:
            self._busy(screen, self.grade_label, self.t, y=110)
        self._toasts(screen)
        if self.overlay is not None:
            self.overlay.draw(screen)

    def _top_bar(self, screen, mouse):
        rect = theme.TOP_BAR
        pygame.draw.rect(screen, theme.PANEL_BG, rect)
        pygame.draw.line(screen, theme.PANEL_LINE, rect.bottomleft, rect.bottomright, 2)
        P.text(screen, "TRẠM CUỐI CÙNG", (rect.left + 14, rect.centery), 16, theme.CYAN, "Bold", "midleft")
        for tab in self.tabs:
            tab.draw(screen, tab.rect.collidepoint(mouse))
        from game_ui.components.panel import MODE_STYLE
        label, color = MODE_STYLE.get(self.mode(), ("", theme.CYAN))
        width = theme.font(12, "SemiBold").size(label)[0] + 10
        P.tag(screen, label, (rect.right - 16 - width / 2, rect.centery), color, 12)

    def _busy(self, screen, text, elapsed, y=60):
        rect = pygame.Rect(0, 0, 360, 40)
        rect.midtop = (theme.PLAYFIELD.centerx, theme.PLAYFIELD.top + y)
        pygame.draw.rect(screen, theme.BG, rect, border_radius=10)
        pygame.draw.rect(screen, theme.CYAN, rect, 2, border_radius=10)
        for i in range(8):
            on = int(elapsed * 10) % 8 == i
            angle = i / 8 * 6.283
            cx, cy = rect.left + 24, rect.centery
            pygame.draw.circle(screen, theme.CYAN if on else (50, 70, 96),
                               (int(cx + 10 * pygame.math.Vector2(1, 0).rotate_rad(angle).x),
                                int(cy + 10 * pygame.math.Vector2(1, 0).rotate_rad(angle).y)), 3)
        P.text(screen, text, (rect.left + 46, rect.centery), 14, theme.TEXT, "SemiBold", "midleft")

    def _toasts(self, screen):
        y = theme.BOTTOM_BAR.top - 12
        for text, kind, _ in reversed(self.toasts[-3:]):
            lines = P.wrap(text, 13, 560)[:2]
            rect = pygame.Rect(0, 0, 600, 16 + 18 * len(lines))
            rect.bottomleft = (16, y)
            pygame.draw.rect(screen, theme.BG, rect, border_radius=8)
            pygame.draw.rect(screen, theme.AMBER if kind == "warn" else theme.GREEN, rect, 2, border_radius=8)
            for i, line in enumerate(lines):
                P.text(screen, line, (rect.left + 12, rect.top + 8 + i * 18), 13, theme.TEXT)
            y = rect.top - 6

    def update(self, dt):
        self.t += dt
        for toast in self.toasts:
            toast[2] -= dt
        self.toasts = [t for t in self.toasts if t[2] > 0]
        self.poll_run()
        self.poll_grade()
        if not self.paused:
            self.player.update(dt * self.settings["speed"])

    def shutdown(self):
        self.grade_cancel.set()
        self.manager.shutdown()
        if self.grade_thread is not None:
            self.grade_thread.join(timeout=3)


# ----------------------------------------------------------------------
# Nội dung overlay kết quả
# ----------------------------------------------------------------------

def _error_lines(err):
    if not err:
        return []
    where = f"{err.get('file')} dòng {err.get('line')}" if err.get("file") else "bài làm"
    lines = [("error", f"Lỗi ở {where}: {err.get('type')}: {err.get('message')}")]
    if err.get("code"):
        lines.append(("code", err["code"].strip()))
    if err.get("hint"):
        lines.append(("p", "Gợi ý: " + err["hint"]))
    return lines


def level_lines(level, stale_reason=None):
    from engine.grading.feedback import progress_line

    lines = [("h", f"Màn {level['level']} — {level['title']}: {level['score']}/{level['max']} điểm ({progress_line(level)})")]
    if stale_reason:
        lines.append(("warn", f"Cần chấm lại: {stale_reason}."))
    for crit in level["criteria"]:
        if crit["passed"]:
            lines.append(("ok", f"{crit['text']} (+{crit['max']})"))
        else:
            lines.append(("todo", f"{crit['text']} (0/{crit['max']}). {crit['hint']}"))
    for case in level["cases"]:
        if case.get("error"):
            lines += _error_lines(case["error"])
            break
    return lines


def report_lines(report, stale):
    lines = [("h", f"Tổng: {report.get('total', 0)}/{report.get('max_total', 100)} điểm"),
             ("muted", f"Chấm lúc {report.get('timestamp', '?')} · rubric {report.get('rubric_version')}")]
    for level in report.get("levels", []):
        lines += level_lines(level, stale.get(str(level["level"])))
    lines.append(("muted", "Điểm chính thức do giảng viên chấm lại từ source bằng engine sạch."))
    return lines


def practice_lines(result):
    lines = [("h", "HOÀN THÀNH" if result["done"] else "Chưa xong — thử lại nhé!"),
             ("muted", "Bài luyện không tính vào điểm bài kiểm tra.")]
    for check in result["checks"]:
        lines.append(("ok" if check["passed"] else "todo", f"{check['text']}: {check['evidence']}"))
    lines += _error_lines(result.get("error"))
    if not result["done"]:
        lines.append(("p", "Mở \"Đề & công cụ\" (F1) và nhấn H để xem gợi ý từng bước."))
    return lines


def run_app(submission="student", level=None, practice=None, demo=False, size=(1280, 720)):
    """Mở cửa sổ game. Không khởi tạo audio: máy không có loa vẫn chơi được."""
    pygame.display.init()
    pygame.font.init()
    app = App(submission, level, practice, demo, size)
    window = pygame.display.set_mode(size, pygame.RESIZABLE)
    pygame.display.set_caption("TRẠM CUỐI CÙNG — Giải cứu trước khi mất điện")
    app.window_size = window.get_size()
    screen = pygame.Surface(theme.LOGICAL_SIZE)
    field = pygame.Surface(theme.PLAYFIELD.size)
    clock = pygame.time.Clock()
    app.start_run()
    try:
        running = True
        while running:
            dt = min(clock.tick(60) / 1000, 0.05)  # kẹp delta khi kéo cửa sổ / mất focus
            for event in pygame.event.get():
                if not app.handle(event):
                    running = False
            app.update(dt)
            app.draw(screen, field)
            win_w, win_h = window.get_size()
            scale = min(win_w / theme.LOGICAL_SIZE[0], win_h / theme.LOGICAL_SIZE[1])
            size_px = (max(1, int(theme.LOGICAL_SIZE[0] * scale)), max(1, int(theme.LOGICAL_SIZE[1] * scale)))
            window.fill((0, 0, 0))
            window.blit(pygame.transform.smoothscale(screen, size_px),
                        ((win_w - size_px[0]) // 2, (win_h - size_px[1]) // 2))
            pygame.display.flip()
    except KeyboardInterrupt:
        pass  # Ctrl+C trong terminal: đóng gọn bên dưới
    finally:
        app.shutdown()
        pygame.quit()
