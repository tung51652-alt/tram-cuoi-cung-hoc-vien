"""Bộ công cụ đồng bộ `ctx` mà học viên dùng trong run(ctx).

Mọi công cụ hành động trả về ActionResult và ghi một event trace. Công cụ quan
sát trả về bản sao: sửa dict/list trả về không làm thay đổi thế giới.
"""

import copy
import os

from game_api import _runtime
from game_api.planner_base import PlannerBase
from game_api.results import ActionResult
from game_api.robot_base import RobotBase


class ActionLimitReached(BaseException):
    """Vượt số hành động tối đa của case. Kế thừa BaseException để
    `except Exception` trong bài học viên không nuốt mất."""


def _require_str(value, name, example):
    """Trả id dạng chuỗi. Chấp nhận cả dict lấy từ ctx.robots()/gates()/packages()/
    tasks()/locations() hoặc object robot, để học viên mới không vấp lỗi kiểu dữ liệu."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "slot_id", "name"):
            if isinstance(value.get(key), str):
                return value[key]
    if isinstance(value, RobotBase) and getattr(value, "_rb_initialized", False):
        return value.id
    if value is None:
        raise TypeError(f"{name} đang là None (chưa có giá trị). Ví dụ đúng: {example!r}.")
    raise TypeError(f"{name} phải là chuỗi (ví dụ {example!r}) hoặc dict có khóa 'id', "
                    f"nhận được {type(value).__name__}.")


def _robot_brief(robot):
    if robot is None:
        return None
    return {
        "battery": robot["battery"],
        "location": robot["location"],
        "carrying": list(robot["carrying"]),
        "escorting": robot["escorting"],
        "active": robot["active"],
    }


class Context:
    """Bộ công cụ của một case. Engine tạo mới cho mỗi lần chạy run(ctx)."""

    def __init__(self, world, recorder, student_root=None, max_actions=2000):
        self._world = world
        self._rec = recorder
        self._student_root = os.path.realpath(str(student_root)) if student_root else None
        self._max_actions = max_actions
        self._actions = 0
        self._via = []
        self._call_counter = 0
        self._registered = {}
        self._planner_used = False

    # ------------------------------------------------------------------
    # Nội bộ engine
    # ------------------------------------------------------------------

    def _activate_runtime(self):
        _runtime.current = self

    def _deactivate_runtime(self):
        if _runtime.current is self:
            _runtime.current = None

    def _is_student_code(self, func):
        code = getattr(func, "__code__", None)
        if code is None:
            return False
        filename = os.path.realpath(code.co_filename)
        if self._student_root is None:
            return not filename.startswith(os.path.dirname(os.path.realpath(__file__)))
        return filename.startswith(self._student_root + os.sep)

    def _act(self, action, actor, args, meta=None):
        self._actions += 1
        if self._actions > self._max_actions:
            raise ActionLimitReached(f"Vượt quá {self._max_actions} hành động trong một case.")
        before = _robot_brief(self._world.robots.get(actor))
        ok, reason, message, data = self._world.apply(action, actor, args)
        after = _robot_brief(self._world.robots.get(actor))
        self._rec.emit(
            "action", actor=actor, action=action, args=copy.deepcopy(args), ok=ok, reason=reason,
            message=message, data=copy.deepcopy(data), before=before, after=after,
            goals_done=self._world.done_goal_ids(), via=self._via[-1] if self._via else None,
            meta=meta,
        )
        return ActionResult(ok, reason, message, data)

    # ------------------------------------------------------------------
    # Quan sát (không đổi state, không tính vào giới hạn hành động)
    # ------------------------------------------------------------------

    def goals(self):
        """List mục tiêu của case: dict {id, text, points, done}."""
        return self._world.goal_status()

    def robots(self):
        """List robot: dict {id, name, specialty, battery, max_battery, location, cards, active, capacity, carrying, escorting}."""
        return [self._public_robot(r) for r in self._world.robots.values()]

    def robot(self, robot_id):
        """Dict của một robot, hoặc None nếu không có."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        robot = self._world.robots.get(robot_id)
        return self._public_robot(robot) if robot else None

    @staticmethod
    def _public_robot(robot):
        item = copy.deepcopy(robot)
        item.pop("builtin", None)
        return item

    def locations(self):
        """List địa điểm: dict {name, kind, zone, is_charger, charges_left}."""
        keys = ("name", "kind", "zone", "is_charger", "charges_left")
        return [{k: loc.get(k) for k in keys} for loc in self._world.locations.values()]

    def find_location(self, kind, zone=None):
        """Tên địa điểm đầu tiên thuộc loại `kind` (và khu `zone` nếu có), hoặc None.

        kind: "beacon", "gate", "safe_zone", "dock", "charger" (trạm sạc), ...
        Ví dụ: ctx.find_location("beacon", "A"), ctx.find_location("charger").
        """
        for loc in self._world.locations.values():
            kind_ok = loc["is_charger"] if kind == "charger" else loc["kind"] == kind
            if kind_ok and (zone is None or loc["zone"] == zone):
                return loc["name"]
        return None

    def route_cost(self, robot_id, location):
        """Pin cần để robot đi tới location qua lối đang mở; None nếu không có đường."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        location = _require_str(location, "location", "hub")
        robot = self._world.robots.get(robot_id)
        if robot is None:
            return None
        route = self._world.find_route(robot["location"], location)
        return route[0] if route else None

    def gates(self):
        """List cổng: dict {id, location, zone, required_card, is_open, broken}."""
        return copy.deepcopy(list(self._world.gates.values()))

    def packages(self):
        """List kiện: dict {id, name, weight, category, destination, location, status, carried_by}."""
        return copy.deepcopy(list(self._world.packages.values()))

    def cargo(self, robot_id):
        """Dict {items, weight, capacity} của khoang robot; None nếu không có robot."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        robot = self._world.robots.get(robot_id)
        if robot is None:
            return None
        weight = sum(self._world.packages[i]["weight"] for i in robot["carrying"])
        return {"items": list(robot["carrying"]), "weight": weight, "capacity": robot["capacity"]}

    def receipts(self):
        """List biên nhận đã giao đúng: dict {package_id, destination, step}."""
        return copy.deepcopy(self._world.receipts)

    def tasks(self):
        """List nhiệm vụ: dict {id, kind, location, status, requires, ...}."""
        return copy.deepcopy(list(self._world.tasks.values()))

    def slots(self):
        """List slot robot bạn được tạo: dict {slot_id, specialty, max_battery, start, taken}."""
        return copy.deepcopy(list(self._world.slots.values()))

    # ------------------------------------------------------------------
    # Hành động chung
    # ------------------------------------------------------------------

    def activate(self, robot_id):
        """Bật robot. Gọi lại khi đã bật trả ok với reason "already_active"."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        return self._act("activate", robot_id, {})

    def say(self, robot_id, text):
        """Robot nói một câu 1–80 ký tự. Robot phải đang hoạt động. Không tốn pin."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        return self._act("say", robot_id, {"text": text})

    def move_to(self, robot_id, location):
        """Đi tới địa điểm theo tuyến ngắn nhất qua lối mở. Không đủ pin thì không đi."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        location = _require_str(location, "location", "hub")
        return self._act("move_to", robot_id, {"location": location})

    def charge(self, robot_id):
        """Sạc đầy tại địa điểm có trạm sạc."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        return self._act("charge", robot_id, {})

    def go_charge(self, robot_id):
        """Đi tới trạm sạc gần nhất rồi sạc đầy (gồm một move_to và một charge).

        Trả kết quả của bước bị từ chối, hoặc của charge nếu thành công.
        """
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        robot = self._world.robots.get(robot_id)
        if robot is None:
            return ActionResult(False, "unknown_id", f"Không có robot '{robot_id}'.")
        best = None
        for loc in self._world.locations.values():
            if loc["is_charger"]:
                route = self._world.find_route(robot["location"], loc["name"])
                if route and (best is None or route[0] < best[0]):
                    best = (route[0], loc["name"])
        if best is None:
            return ActionResult(False, "no_path", "Không có đường tới trạm sạc nào.")
        moved = self.move_to(robot_id, best[1])
        if not moved.ok:
            return moved
        return self.charge(robot_id)

    # ------------------------------------------------------------------
    # Màn 1 — cổng
    # ------------------------------------------------------------------

    def check_gate(self, robot_id, gate_id):
        """Kiểm tra open_gate có thành công không, không đổi state."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        gate_id = _require_str(gate_id, "gate_id", "gate_A")
        return self._act("check_gate", robot_id, {"gate_id": gate_id})

    def open_gate(self, robot_id, gate_id):
        """Mở cổng khi đứng tại cổng, có thẻ phù hợp và đủ 2 pin."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        gate_id = _require_str(gate_id, "gate_id", "gate_A")
        return self._act("open_gate", robot_id, {"gate_id": gate_id})

    # ------------------------------------------------------------------
    # Màn 2 — vật tư
    # ------------------------------------------------------------------

    def load(self, robot_id, package_id):
        """Nạp kiện đang nằm cùng vị trí lên robot, trong giới hạn sức chứa."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        package_id = _require_str(package_id, "package_id", "p1")
        return self._act("load", robot_id, {"package_id": package_id})

    def unload(self, robot_id, package_id):
        """Dỡ kiện tại vị trí hiện tại. Chỉ tính đã giao nếu đúng destination."""
        robot_id = _require_str(robot_id, "robot_id", "BIP")
        package_id = _require_str(package_id, "package_id", "p1")
        return self._act("unload", robot_id, {"package_id": package_id})

    def use_planner(self, planner):
        """Giao object lớp con PlannerBase cho engine: engine gọi planner.execute(ctx)
        đúng một lần, rồi ghi lại planner.report()."""
        if not isinstance(planner, PlannerBase):
            raise TypeError("use_planner cần một object thuộc lớp con của PlannerBase.")
        if not getattr(planner, "_pb_initialized", False):
            return ActionResult(False, "not_initialized", "Lớp con chưa gọi super().__init__(name).")
        if self._planner_used:
            return ActionResult(False, "planner_used", "Mỗi case chỉ dùng use_planner một lần.")
        self._planner_used = True
        cls = type(planner)
        self._call_counter += 1
        via = {"call": "planner", "n": self._call_counter, "obj": planner.name}
        self._rec.emit("call_start", call="planner", n=via["n"], obj=planner.name, cls=cls.__qualname__,
                       student_class=self._is_student_code(cls.execute))
        self._via.append(via)
        try:
            planner.execute(self)
        finally:
            self._via.pop()
        reported = planner.report()
        ids = []
        if isinstance(reported, (list, tuple, set)):
            ids = sorted({str(x) for x in reported})[:200]
        self._rec.emit("planner_report", n=via["n"], ids=ids, valid_type=isinstance(reported, (list, tuple, set)))
        self._rec.emit("call_end", call="planner", n=via["n"])
        return ActionResult(True, "ok", "Planner đã chạy xong.", {"reported": ids})

    # ------------------------------------------------------------------
    # Màn 3 — đội robot
    # ------------------------------------------------------------------

    def repair(self, robot_id, task_id):
        """Sửa thiết bị: robot chuyên môn repair, đứng tại site, đủ 5 pin."""
        robot_id = _require_str(robot_id, "robot_id", "R1")
        task_id = _require_str(task_id, "task_id", "t1")
        return self._act("repair", robot_id, {"task_id": task_id})

    def rescue(self, robot_id, task_id):
        """Bắt đầu dẫn người: robot rescue, đứng tại chỗ người, đủ 2 pin.
        Người được an toàn khi robot move_to tới địa điểm kind "safe_zone"."""
        robot_id = _require_str(robot_id, "robot_id", "S1")
        task_id = _require_str(task_id, "task_id", "t4")
        return self._act("rescue", robot_id, {"task_id": task_id})

    def register_robot(self, robot):
        """Đăng ký object lớp con RobotBase vào slot của nó."""
        if not isinstance(robot, RobotBase):
            raise TypeError("register_robot cần object thuộc lớp con của RobotBase.")
        if not getattr(robot, "_rb_initialized", False):
            return ActionResult(False, "not_initialized", "Lớp con chưa gọi super().__init__(slot_id).")
        slot_id = robot.id
        if slot_id in self._registered:
            reason = "already_registered" if self._registered[slot_id] is robot else "slot_taken"
            return ActionResult(False, reason, f"Slot {slot_id} đã được đăng ký.")
        cls = type(robot)
        meta = {"cls": cls.__qualname__, "student_class": self._is_student_code(cls.act)}
        result = self._act("register", slot_id, {}, meta=meta)
        if result.ok:
            self._registered[slot_id] = robot
        return result

    def dispatch(self, robot, task_id):
        """Giao nhiệm vụ cho robot đã đăng ký: engine gọi robot.act(ctx, task)."""
        if not isinstance(robot, RobotBase):
            raise TypeError("dispatch cần object thuộc lớp con của RobotBase.")
        task_id = _require_str(task_id, "task_id", "t1")
        slot_id = getattr(robot, "_rb_slot", {}).get("slot_id")
        if self._registered.get(slot_id) is not robot:
            return ActionResult(False, "not_registered", "Robot chưa được register_robot.")
        task = self._world.tasks.get(task_id)
        if task is None:
            return ActionResult(False, "unknown_id", f"Không có nhiệm vụ '{task_id}'.")
        cls = type(robot)
        act = cls.act
        self._call_counter += 1
        via = {"call": "dispatch", "n": self._call_counter, "obj": slot_id}
        self._rec.emit("call_start", call="dispatch", n=via["n"], obj=slot_id, task=task_id,
                       cls=cls.__qualname__, act_owner=f"{act.__module__}.{act.__qualname__}",
                       student_class=self._is_student_code(act))
        self._via.append(via)
        try:
            robot.act(self, copy.deepcopy(task))
        finally:
            self._via.pop()
        self._rec.emit("call_end", call="dispatch", n=via["n"])
        return ActionResult(True, "ok", f"{slot_id} đã xử lý xong lượt act cho {task_id}.")
