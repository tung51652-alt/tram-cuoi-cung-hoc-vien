"""Phát lại trace thành trạng thái hiển thị theo thời gian (không phụ thuộc pygame).

TracePlayer chỉ đọc event `trace/1`. Mọi số liệu hiển thị cuối mỗi bước (pin, vị
trí, trạng thái cổng/kiện/nhiệm vụ) lấy từ event thật, không từ giá trị mong đợi.
Dữ liệu thiếu/sai kiểu được bỏ qua hoặc đánh dấu ⚠, không làm renderer lỗi.
"""

import math

MOVE_SPEED = 230.0  # pixel logic mỗi giây ở tốc độ 1x
MAX_STEP_SECONDS = 4.0


def _num(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _layout(locations):
    """Tọa độ địa điểm; địa điểm thiếu x/y được xếp tự động trên một vòng tròn."""
    points = {}
    missing = []
    for loc in locations:
        if not isinstance(loc, dict) or not isinstance(loc.get("name"), str):
            continue
        if isinstance(loc.get("x"), (int, float)) and isinstance(loc.get("y"), (int, float)):
            points[loc["name"]] = (max(20.0, min(840.0, float(loc["x"]))), max(20.0, min(620.0, float(loc["y"]))))
        else:
            missing.append(loc["name"])
    for i, name in enumerate(missing):
        angle = 2 * math.pi * i / max(1, len(missing))
        points[name] = (430 + 220 * math.cos(angle), 320 + 220 * math.sin(angle))
    return points


class RobotView:
    def __init__(self, data, points):
        self.id = str(data.get("id", "?"))
        self.name = str(data.get("name", self.id))
        self.specialty = str(data.get("specialty", "general"))
        self.cards = data.get("cards") if isinstance(data.get("cards"), list) else []
        self.location = data.get("location")
        self.x, self.y = points.get(self.location, (430.0, 320.0))
        self.battery = data.get("battery")
        self.max_battery = data.get("max_battery") or 1
        self.active = bool(data.get("active", True))
        self.carrying = list(data.get("carrying") or [])
        self.escorting = data.get("escorting")
        self.facing = 1.0
        self.visible = True
        self.fade = 1.0
        self.anim = None       # "scan", "charge", "repair", "shake", "wake", "load", "spawn"
        self.anim_t = 0.0
        self.highlight = 0.0   # vòng sáng khi đang chạy act() của học viên

    @property
    def battery_ok(self):
        return isinstance(self.battery, (int, float)) and 0 <= self.battery <= max(1, _num(self.max_battery, 1))


class Bubble:
    def __init__(self, actor, text, kind, duration):
        self.actor = actor
        self.text = str(text)[:160]
        self.kind = kind  # "say", "refuse", "ok"
        self.remaining = duration


class Step:
    """Một bước hoạt cảnh ứng với một event hành động."""

    def __init__(self, event, duration):
        self.event = event
        self.duration = max(0.05, min(MAX_STEP_SECONDS, duration))
        self.elapsed = 0.0


class TracePlayer:
    def __init__(self, events):
        self.events = [e for e in (events or []) if isinstance(e, dict)]
        start = next((e for e in self.events if e.get("kind") == "start"), None)
        state = start.get("state") if start and isinstance(start.get("state"), dict) else {}
        self.state = state
        self.level = state.get("level")
        self.title = state.get("title", "")
        self.locations = {l["name"]: dict(l) for l in state.get("locations", []) if isinstance(l, dict) and "name" in l}
        self.points = _layout(state.get("locations", []))
        self.edges = [e for e in state.get("edges", []) if isinstance(e, (list, tuple)) and len(e) >= 3
                      and e[0] in self.points and e[1] in self.points]
        self.gates = {}
        for gate in state.get("gates", []):
            if isinstance(gate, dict) and "id" in gate:
                self.gates[gate["id"]] = {**gate, "open_frac": 1.0 if gate.get("is_open") else 0.0}
        self.robots = {}
        for robot in state.get("robots", []):
            if isinstance(robot, dict):
                view = RobotView(robot, self.points)
                self.robots[view.id] = view
        self.packages = {}
        for pkg in state.get("packages", []):
            if isinstance(pkg, dict) and "id" in pkg:
                self.packages[pkg["id"]] = dict(pkg)
                self._place_package(pkg["id"])
        self.tasks = {}
        for task in state.get("tasks", []):
            if isinstance(task, dict) and "id" in task:
                item = dict(task)
                item["person_xy"] = self._site_xy(item.get("location"), offset=(18, 8))
                item["fx"] = 0.0
                self.tasks[item["id"]] = item
        self.slots = [s for s in state.get("slots", []) if isinstance(s, dict)]
        self.goals = {g["id"]: dict(g) for g in state.get("goals", []) if isinstance(g, dict) and "id" in g}
        self.visited = set()
        self.bubbles = []
        self.log = []            # (kind, text) cho panel sự kiện
        self.prints = []         # dòng print của học viên, hiện sau khi phát xong
        self.banner = None       # (kind, text) lỗi / timeout / kết thúc
        self.steps = [self._make_step(e) for e in self.events if e.get("kind") != "start"]
        self.index = 0
        self.time = 0.0
        self.finished_status = None
        self.has_end = any(e.get("kind") == "end" for e in self.events)
        self.current_call = None

    # ------------------------------------------------------------------
    # Hỗ trợ vị trí
    # ------------------------------------------------------------------

    def _site_xy(self, location, offset=(0, 0)):
        x, y = self.points.get(location, (430.0, 320.0))
        return x + offset[0], y + offset[1]

    def _place_package(self, package_id):
        pkg = self.packages[package_id]
        if pkg.get("carried_by") or pkg.get("status") == "loaded":
            return
        same = sorted(pid for pid, p in self.packages.items()
                      if p.get("location") == pkg.get("location") and not p.get("carried_by"))
        i = same.index(package_id) if package_id in same else 0
        x, y = self._site_xy(pkg.get("location"))
        pkg["x"], pkg["y"] = x - 44 - (i % 2) * 22, y - 16 + (i // 2) * 22

    def _make_step(self, event):
        kind = event.get("kind")
        if kind != "action":
            return Step(event, 0.35 if kind in ("error", "end") else 0.05)
        action, ok = event.get("action"), bool(event.get("ok"))
        if not ok:
            return Step(event, 1.3)
        if action == "move_to":
            path = (event.get("data") or {}).get("path") or []
            length = 0.0
            pts = [self.points[p] for p in path if p in self.points]
            for a, b in zip(pts, pts[1:]):
                length += math.dist(a, b)
            return Step(event, 0.2 + length / MOVE_SPEED)
        return Step(event, {"say": 1.5, "open_gate": 1.2, "check_gate": 0.6, "charge": 0.9, "activate": 0.9,
                            "load": 0.6, "unload": 0.7, "repair": 1.1, "rescue": 0.8, "register": 0.7}.get(action, 0.4))

    # ------------------------------------------------------------------
    # Thời gian
    # ------------------------------------------------------------------

    @property
    def done(self):
        return self.index >= len(self.steps)

    @property
    def progress(self):
        return self.index, len(self.steps)

    def update(self, dt):
        """Tiến thời gian dt giây (đã nhân tốc độ). An toàn với dt lớn."""
        dt = max(0.0, min(_num(dt), 1.0))
        self.time += dt
        for bubble in self.bubbles:
            bubble.remaining -= dt
        self.bubbles = [b for b in self.bubbles if b.remaining > 0]
        for robot in self.robots.values():
            robot.anim_t += dt
            robot.highlight = max(0.0, robot.highlight - dt)
            if robot.anim and robot.anim_t > 1.2:
                robot.anim = None
        for gate in self.gates.values():
            target = 1.0 if gate.get("is_open") else 0.0
            gate["open_frac"] += max(-dt * 2, min(dt * 2, target - gate["open_frac"]))
        for task in self.tasks.values():
            task["fx"] += dt
        while dt > 0 and not self.done:
            step = self.steps[self.index]
            if step.elapsed == 0.0:
                self._begin(step.event)
            use = min(dt, step.duration - step.elapsed)
            step.elapsed += use
            dt -= use
            self._animate(step)
            if step.elapsed >= step.duration - 1e-9:
                self._finish(step.event)
                self.index += 1

    def skip_to_end(self):
        while not self.done:
            self.update(1.0)

    # ------------------------------------------------------------------
    # Áp dụng event
    # ------------------------------------------------------------------

    def _robot(self, event):
        return self.robots.get(str(event.get("actor")))

    def _begin(self, event):
        kind = event.get("kind")
        if kind == "call_start":
            self.current_call = event
            robot = self.robots.get(str(event.get("obj")))
            if robot:
                robot.highlight = 1.5
            if event.get("call") == "dispatch":
                self.log.append(("call", f"dispatch → {event.get('cls', '?')}.act() của {event.get('obj')} ({event.get('task')})"))
            else:
                self.log.append(("call", f"Planner '{event.get('obj')}' bắt đầu execute()"))
            return
        if kind == "call_end":
            self.current_call = None
            return
        if kind == "error":
            err = event.get("error") or {}
            where = f" ({err.get('file')} dòng {err.get('line')})" if err.get("file") else ""
            self.banner = ("error", f"Code dừng vì lỗi {err.get('type', '?')}{where}: {err.get('message', '')}")
            self.log.append(("error", self.banner[1]))
            return
        if kind == "end":
            return
        if kind != "action":
            return
        robot = self._robot(event)
        ok = bool(event.get("ok"))
        message = str(event.get("message", ""))
        self.log.append(("ok" if ok else "refuse", message))
        if robot is None and event.get("action") != "register":
            return
        if not ok:
            robot.anim, robot.anim_t = "shake", 0.0
            self.bubbles.append(Bubble(robot.id, message, "refuse", 1.8))
            return
        action = event.get("action")
        if action == "say":
            text = (event.get("data") or {}).get("text") or (event.get("args") or {}).get("text", "")
            self.bubbles.append(Bubble(robot.id, text, "say", 2.2))
        elif action in ("open_gate", "check_gate"):
            robot.anim, robot.anim_t = "scan", 0.0
        elif action == "charge":
            robot.anim, robot.anim_t = "charge", 0.0
        elif action == "activate":
            robot.anim, robot.anim_t = "wake", 0.0
        elif action == "repair":
            robot.anim, robot.anim_t = "repair", 0.0
        elif action == "register":
            slot_id = str(event.get("actor"))
            slot = next((s for s in self.slots if s.get("slot_id") == slot_id), {})
            data = {"id": slot_id, "name": slot.get("name", slot_id), "specialty": slot.get("specialty"),
                    "battery": (event.get("after") or {}).get("battery"), "max_battery": slot.get("max_battery", 30),
                    "location": slot.get("start"), "active": True}
            view = RobotView(data, self.points)
            view.anim, view.fade = "spawn", 0.0
            self.robots[slot_id] = view
        elif action == "move_to":
            path = [p for p in ((event.get("data") or {}).get("path") or []) if p in self.points]
            robot.path_pts = [self.points[p] for p in path] or [(robot.x, robot.y)]
            robot.path_from_battery = robot.battery
        elif action in ("load", "unload"):
            robot.anim, robot.anim_t = "load", 0.0

    def _animate(self, step):
        event = step.event
        if event.get("kind") != "action" or not event.get("ok"):
            return
        robot = self._robot(event)
        if robot is None:
            return
        t = step.elapsed / step.duration
        action = event.get("action")
        if action == "move_to":
            pts = getattr(robot, "path_pts", None) or [(robot.x, robot.y)]
            x, y = _along(pts, _ease(t))
            if abs(x - robot.x) > 0.01:
                robot.facing = 1.0 if x > robot.x else -1.0
            robot.x, robot.y = x, y
            before = _num(getattr(robot, "path_from_battery", robot.battery), 0)
            after = _num((event.get("after") or {}).get("battery"), before)
            robot.battery = round(before + (after - before) * t)
            self._follow(robot)
        elif action == "register":
            robot.fade = t
        elif action == "open_gate":
            gate = self.gates.get((event.get("args") or {}).get("gate_id"))
            if gate and t > 0.45:
                gate["is_open"] = True
        elif action in ("load", "unload"):
            pid = (event.get("args") or {}).get("package_id")
            pkg = self.packages.get(pid)
            if pkg is not None:
                if action == "load":
                    sx, sy = pkg.get("x", robot.x), pkg.get("y", robot.y)
                    pkg["x"], pkg["y"] = sx + (robot.x - sx) * t, sy + (robot.y - 20 - sy) * t
                else:
                    tx, ty = self._site_xy(robot.location, offset=(0, 26))
                    pkg["x"], pkg["y"] = robot.x + (tx - robot.x) * t, robot.y - 20 + (ty - robot.y + 20) * t

    def _follow(self, robot):
        for i, pid in enumerate(robot.carrying):
            pkg = self.packages.get(pid)
            if pkg is not None:
                pkg["x"], pkg["y"] = robot.x - 10 + i * 7, robot.y - 24 - i * 3
        task = self.tasks.get(robot.escorting)
        if task is not None:
            task["person_xy"] = (robot.x - 22 * robot.facing, robot.y + 6)

    def _finish(self, event):
        kind = event.get("kind")
        if kind == "end":
            self.finished_status = event.get("status")
            if event.get("by") == "runner":
                text = ("Hết thời gian: chưa có trace hoàn chỉnh, chỉ phát phần đã ghi."
                        if event.get("status") == "timeout" else "Lượt chạy dừng bất thường; chỉ phát phần đã ghi.")
                self.banner = ("timeout", text)
            self._update_goals(event.get("goals_done"))
            if self.banner is None and event.get("status") == "complete":
                done = sum(1 for g in self.goals.values() if g.get("done"))
                if self.goals and done == len(self.goals):
                    self.banner = ("done", f"Hoàn thành! Đạt {done}/{len(self.goals)} mục tiêu.")
                else:
                    self.banner = ("todo", f"Chưa hoàn thành: đạt {done}/{len(self.goals)} mục tiêu. "
                                           "Mở \"Đề & công cụ\" (F1) để xem cần làm gì, sửa code rồi bấm Chạy lại (F5).")
            return
        if kind != "action":
            return
        self._update_goals(event.get("goals_done"))
        robot = self._robot(event)
        after = event.get("after") if isinstance(event.get("after"), dict) else None
        if robot is not None and after is not None:
            # Số liệu chốt lấy từ trace thật.
            robot.battery = after.get("battery")
            robot.location = after.get("location", robot.location)
            robot.active = bool(after.get("active", robot.active))
            robot.carrying = list(after.get("carrying") or [])
            robot.escorting = after.get("escorting")
            if event.get("action") == "move_to" and event.get("ok"):
                robot.x, robot.y = self.points.get(robot.location, (robot.x, robot.y))
                for name in (event.get("data") or {}).get("path") or []:
                    self.visited.add(name)
            robot.fade = 1.0
        if not event.get("ok"):
            return
        action = event.get("action")
        args = event.get("args") or {}
        data = event.get("data") or {}
        if action == "open_gate":
            gate = self.gates.get(args.get("gate_id"))
            if gate:
                gate["is_open"] = True
        elif action in ("load", "unload"):
            pkg = self.packages.get(args.get("package_id"))
            if pkg is not None and robot is not None:
                if action == "load":
                    pkg.update(status="loaded", carried_by=robot.id, location=None)
                    self._follow(robot)
                else:
                    pkg.update(status="delivered" if data.get("delivered") else "waiting", carried_by=None,
                               location=robot.location)
                    self._place_package(pkg["id"])
                    self.bubbles.append(Bubble(robot.id, "Đã giao đúng nơi" if data.get("delivered") else "Sai nơi nhận, chưa tính đã giao",
                                               "ok" if data.get("delivered") else "refuse", 1.2))
        elif action == "repair":
            task = self.tasks.get(args.get("task_id"))
            if task:
                task["status"], task["fx"] = "done", 0.0
        elif action == "rescue":
            task = self.tasks.get(args.get("task_id"))
            if task:
                task["status"] = "in_progress"
        if action == "move_to" and data.get("person_safe"):
            task = self.tasks.get(data["person_safe"])
            if task:
                task["status"], task["fx"] = "done", 0.0
                x, y = self._site_xy(robot.location if robot else None)
                saved = sum(1 for t in self.tasks.values() if t.get("status") == "done" and t.get("kind") == "rescue")
                task["person_xy"] = (x - 40 + (saved % 5) * 16, y + 34)
                self.bubbles.append(Bubble(robot.id, "Người đã an toàn", "ok", 1.4))

    def _update_goals(self, done_ids):
        if not isinstance(done_ids, list):
            return
        for gid, goal in self.goals.items():
            goal["done"] = gid in done_ids


def _ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _along(points, t):
    """Điểm trên polyline theo tỉ lệ độ dài t ∈ [0, 1]."""
    if len(points) < 2:
        return points[0]
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    target = t * (sum(lengths) or 1.0)
    for i, seg in enumerate(lengths):
        a, b = points[i], points[i + 1]
        if target <= seg or i == len(lengths) - 1:
            k = 0.0 if seg == 0 else min(1.0, target / seg)
            return a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        target -= seg
    return points[-1]
