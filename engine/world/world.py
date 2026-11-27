"""Trạng thái thế giới có thẩm quyền và luật của mọi hành động.

World không biết gì về code học viên, trace hay đồ họa. Mỗi hành động đi qua
`World.apply(action, actor, args)` và trả về bộ (ok, reason, message, data).
Nhờ vậy oracle có thể phát lại trace trên một World mới để kiểm tra độc lập.
"""

import copy
import heapq

# Chi phí pin công bố cho các thao tác (ngoài di chuyển).
OPEN_GATE_COST = 2
REPAIR_COST = 5
RESCUE_COST = 2
MAX_TEXT_LENGTH = 80


class World:
    """Toàn bộ state của một case. Chỉ engine được sửa trực tiếp."""

    def __init__(self, data):
        self.scenario_id = data["id"]
        self.level = data["level"]
        self.title = data.get("title", "")
        self.locations = {}
        for loc in data.get("locations", []):
            item = dict(loc)
            item.setdefault("kind", "corridor")
            item.setdefault("zone", None)
            item.setdefault("is_charger", False)
            item.setdefault("charges_left", None)
            self.locations[item["name"]] = item
        self.edges = []
        for edge in data.get("edges", []):
            gate_id = edge[3] if len(edge) > 3 else None
            self.edges.append((edge[0], edge[1], int(edge[2]), gate_id))
        self.gates = {}
        for gate in data.get("gates", []):
            item = dict(gate)
            item.setdefault("is_open", False)
            item.setdefault("broken", False)
            self.gates[item["id"]] = item
        self.robots = {}
        for robot in data.get("robots", []):
            self.robots[robot["id"]] = self._new_robot(robot, builtin=True)
        self.packages = {}
        for pkg in data.get("packages", []):
            item = dict(pkg)
            item.setdefault("status", "waiting")
            item.setdefault("carried_by", None)
            self.packages[item["id"]] = item
        self.tasks = {}
        for task in data.get("tasks", []):
            item = dict(task)
            item.setdefault("status", "open")
            item.setdefault("requires", None)
            item.setdefault("escorted_by", None)
            self.tasks[item["id"]] = item
        self.slots = {}
        for slot in data.get("slots", []):
            item = dict(slot)
            item["taken"] = False
            self.slots[item["slot_id"]] = item
        self.goals = [dict(goal) for goal in data.get("goals", [])]
        self.receipts = []
        self.said = []
        self.visited = set()
        for robot in self.robots.values():
            self.visited.add((robot["id"], robot["location"]))
        self.step = 0

    # ------------------------------------------------------------------
    # Tạo và đọc dữ liệu
    # ------------------------------------------------------------------

    @staticmethod
    def _new_robot(spec, builtin):
        battery = int(spec.get("battery", spec.get("max_battery", 0)))
        return {
            "id": spec["id"],
            "name": spec.get("name", spec["id"]),
            "specialty": spec.get("specialty", "general"),
            "battery": battery,
            "max_battery": int(spec.get("max_battery", battery)),
            "location": spec["location"],
            "cards": list(spec.get("cards", [])),
            "active": bool(spec.get("active", True)),
            "capacity": int(spec.get("capacity", 0)),
            "carrying": [],
            "escorting": None,
            "builtin": builtin,
        }

    def robot_snapshot(self, robot_id):
        robot = self.robots.get(robot_id)
        return copy.deepcopy(robot) if robot else None

    def snapshot(self):
        """Bản sao toàn bộ state dùng cho trace `start` và renderer."""
        return {
            "id": self.scenario_id,
            "level": self.level,
            "title": self.title,
            "locations": copy.deepcopy(list(self.locations.values())),
            "edges": [list(e) for e in self.edges],
            "gates": copy.deepcopy(list(self.gates.values())),
            "robots": copy.deepcopy(list(self.robots.values())),
            "packages": copy.deepcopy(list(self.packages.values())),
            "tasks": copy.deepcopy(list(self.tasks.values())),
            "slots": copy.deepcopy(list(self.slots.values())),
            "goals": self.goal_status(),
        }

    def goal_done(self, goal):
        kind = goal.get("type")
        if kind == "robot_at":
            robot = self.robots.get(goal["robot"])
            return bool(robot and robot["active"] and robot["location"] == goal["location"])
        if kind == "said":
            return any(who == goal["robot"] for who, _ in self.said)
        if kind == "said_contains":
            return any(who == goal["robot"] and all(str(v) in text for v in goal["values"])
                       for who, text in self.said)
        if kind == "visited":
            return (goal["robot"], goal["location"]) in self.visited
        if kind == "zone":
            return any(loc == goal["beacon"] for _, loc in self.visited)
        if kind == "delivered":
            pkg = self.packages.get(goal["package"])
            return bool(pkg and pkg["status"] == "delivered")
        if kind == "task":
            task = self.tasks.get(goal["task"])
            return bool(task and task["status"] == "done")
        return False

    def goal_status(self):
        result = []
        for goal in self.goals:
            result.append({
                "id": goal["id"],
                "text": goal.get("text", goal["id"]),
                "points": goal.get("points", 0),
                "done": self.goal_done(goal),
            })
        return result

    def done_goal_ids(self):
        return [g["id"] for g in self.goals if self.goal_done(g)]

    # ------------------------------------------------------------------
    # Đường đi
    # ------------------------------------------------------------------

    def _passable(self, gate_id):
        if gate_id is None:
            return True
        gate = self.gates.get(gate_id)
        return bool(gate and gate["is_open"])

    def find_route(self, start, target):
        """Dijkstra qua các lối đang mở. Trả (cost, path) hoặc None."""
        if start not in self.locations or target not in self.locations:
            return None
        neighbors = {}
        for a, b, cost, gate_id in self.edges:
            if self._passable(gate_id):
                neighbors.setdefault(a, []).append((b, cost))
                neighbors.setdefault(b, []).append((a, cost))
        queue = [(0, [start])]
        best = {start: 0}
        while queue:
            cost, path = heapq.heappop(queue)
            node = path[-1]
            if node == target:
                return cost, path
            if cost > best.get(node, cost):
                continue
            for nxt, step_cost in sorted(neighbors.get(node, [])):
                new_cost = cost + step_cost
                if new_cost < best.get(nxt, new_cost + 1):
                    best[nxt] = new_cost
                    heapq.heappush(queue, (new_cost, path + [nxt]))
        return None

    # ------------------------------------------------------------------
    # Hành động
    # ------------------------------------------------------------------

    def apply(self, action, actor, args):
        """Thực hiện một hành động theo luật. Bị từ chối thì không đổi state."""
        handler = getattr(self, "_do_" + str(action), None)
        if handler is None:
            return False, "unknown_action", f"Không có hành động '{action}'.", {}
        self.step += 1
        return handler(actor, **args)

    def _robot_or_error(self, robot_id, need_active=True):
        robot = self.robots.get(robot_id)
        if robot is None:
            return None, (False, "unknown_id", f"Không có robot '{robot_id}'.", {})
        if need_active and not robot["active"]:
            return None, (False, "inactive", f"Robot {robot_id} chưa được kích hoạt.", {})
        return robot, None

    def _do_activate(self, robot_id):
        robot, err = self._robot_or_error(robot_id, need_active=False)
        if err:
            return err
        if robot["active"]:
            return True, "already_active", f"{robot_id} đã hoạt động từ trước.", {}
        robot["active"] = True
        return True, "ok", f"{robot_id} đã thức dậy.", {}

    def _do_say(self, robot_id, text):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        if not isinstance(text, str) or not (1 <= len(text.strip()) <= MAX_TEXT_LENGTH):
            return False, "invalid_text", f"Lời thoại phải là chuỗi 1–{MAX_TEXT_LENGTH} ký tự.", {}
        self.said.append((robot_id, text.strip()))
        return True, "ok", f'{robot_id}: "{text.strip()}"', {"text": text.strip()}

    def _do_move_to(self, robot_id, location):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        if location not in self.locations:
            return (False, "unknown_id",
                    f"Không có địa điểm '{location}'. Bản đồ chấm có thể dùng tên khác: "
                    "hãy lấy tên từ ctx.locations() hoặc ctx.find_location().", {})
        if robot["location"] == location:
            return True, "already_here", f"{robot_id} đang ở {location}.", {"path": [location], "cost": 0}
        route = self.find_route(robot["location"], location)
        if route is None:
            return False, "no_path", f"Không có lối mở từ {robot['location']} tới {location}.", {}
        cost, path = route
        if cost > robot["battery"]:
            return (False, "low_battery",
                    f"{robot_id} cần {cost} pin để tới {location} nhưng chỉ còn {robot['battery']}.",
                    {"cost": cost})
        robot["battery"] -= cost
        robot["location"] = location
        for node in path:
            self.visited.add((robot_id, node))
        data = {"path": path, "cost": cost}
        task_id = robot["escorting"]
        if task_id and self.locations[location]["kind"] == "safe_zone":
            self.tasks[task_id]["status"] = "done"
            self.tasks[task_id]["escorted_by"] = None
            robot["escorting"] = None
            data["person_safe"] = task_id
        return True, "ok", f"{robot_id} đã tới {location} (tốn {cost} pin).", data

    def _do_charge(self, robot_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        loc = self.locations[robot["location"]]
        if not loc["is_charger"]:
            return False, "not_at_charger", f"{robot['location']} không có trạm sạc.", {}
        if loc["charges_left"] is not None and loc["charges_left"] <= 0:
            return False, "charger_empty", f"Trạm sạc ở {loc['name']} đã hết lượt.", {}
        if loc["charges_left"] is not None:
            loc["charges_left"] -= 1
        robot["battery"] = robot["max_battery"]
        return True, "ok", f"{robot_id} đã sạc đầy ({robot['battery']}).", {}

    def _gate_check(self, robot, gate_id):
        gate = self.gates.get(gate_id)
        if gate is None:
            return False, "unknown_id", f"Không có cổng '{gate_id}'.", {}
        if gate["is_open"]:
            return True, "already_open", f"Cổng {gate_id} đã mở.", {}
        if robot["location"] != gate["location"]:
            return False, "not_at_gate", f"{robot['id']} phải đứng ở {gate['location']} để mở {gate_id}.", {}
        if gate["broken"]:
            return False, "gate_broken", f"Cổng {gate_id} bị hỏng, không mở được.", {}
        if gate["required_card"] not in robot["cards"]:
            return (False, "missing_card",
                    f"{robot['id']} không có thẻ cấp {gate['required_card']} cho {gate_id}.", {})
        if robot["battery"] < OPEN_GATE_COST:
            return False, "low_battery", f"Cần {OPEN_GATE_COST} pin để mở cổng.", {}
        return True, "ok", f"{robot['id']} có thể mở {gate_id}.", {}

    def _do_check_gate(self, robot_id, gate_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        return self._gate_check(robot, gate_id)

    def _do_open_gate(self, robot_id, gate_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        ok, reason, message, data = self._gate_check(robot, gate_id)
        if not ok or reason == "already_open":
            return ok, reason, message, data
        self.gates[gate_id]["is_open"] = True
        robot["battery"] -= OPEN_GATE_COST
        return True, "ok", f"{robot_id} đã mở {gate_id}.", {}

    def _do_load(self, robot_id, package_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        pkg = self.packages.get(package_id)
        if pkg is None:
            return False, "unknown_id", f"Không có kiện '{package_id}'.", {}
        if pkg["status"] == "delivered":
            return False, "already_delivered", f"Kiện {package_id} đã được giao.", {}
        if pkg["status"] == "loaded":
            return False, "already_loaded", f"Kiện {package_id} đang ở trên robot {pkg['carried_by']}.", {}
        if pkg["location"] != robot["location"]:
            return False, "not_here", f"Kiện {package_id} ở {pkg['location']}, không ở {robot['location']}.", {}
        load = sum(self.packages[i]["weight"] for i in robot["carrying"])
        if load + pkg["weight"] > robot["capacity"]:
            return (False, "over_capacity",
                    f"Quá sức chứa: {load} + {pkg['weight']} > {robot['capacity']}.", {})
        pkg["status"] = "loaded"
        pkg["carried_by"] = robot_id
        pkg["location"] = None
        robot["carrying"].append(package_id)
        return True, "ok", f"{robot_id} đã nạp {package_id}.", {}

    def _do_unload(self, robot_id, package_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        if package_id not in robot["carrying"]:
            return False, "not_carrying", f"{robot_id} không chở kiện {package_id}.", {}
        pkg = self.packages[package_id]
        robot["carrying"].remove(package_id)
        pkg["carried_by"] = None
        pkg["location"] = robot["location"]
        if robot["location"] == pkg["destination"]:
            pkg["status"] = "delivered"
            self.receipts.append({"package_id": package_id, "destination": pkg["destination"], "step": self.step})
            return True, "ok", f"Đã giao {package_id} tới {pkg['destination']}.", {"delivered": True}
        pkg["status"] = "waiting"
        return (True, "wrong_destination",
                f"Đã dỡ {package_id} ở {robot['location']}, nhưng nơi nhận là {pkg['destination']}.",
                {"delivered": False})

    def _task_check(self, robot, task_id, kind, cost):
        task = self.tasks.get(task_id)
        if task is None:
            return None, (False, "unknown_id", f"Không có nhiệm vụ '{task_id}'.", {})
        if task["kind"] != kind:
            return None, (False, "wrong_task", f"Nhiệm vụ {task_id} là loại {task['kind']}, không phải {kind}.", {})
        if robot["specialty"] != kind:
            return None, (False, "wrong_specialty", f"{robot['id']} có chuyên môn {robot['specialty']}, không làm được {kind}.", {})
        if task["status"] != "open":
            return None, (False, "task_done", f"Nhiệm vụ {task_id} đã được nhận hoặc đã xong.", {})
        req = task["requires"]
        if req and self.tasks.get(req, {}).get("status") != "done":
            return None, (False, "blocked", f"Nhiệm vụ {task_id} cần hoàn thành {req} trước.", {})
        if robot["location"] != task["location"]:
            return None, (False, "not_here", f"{robot['id']} phải tới {task['location']}.", {})
        if robot["battery"] < cost:
            return None, (False, "low_battery", f"Cần {cost} pin, {robot['id']} chỉ còn {robot['battery']}.", {})
        return task, None

    def _do_repair(self, robot_id, task_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        task, err = self._task_check(robot, task_id, "repair", REPAIR_COST)
        if err:
            return err
        robot["battery"] -= REPAIR_COST
        task["status"] = "done"
        return True, "ok", f"{robot_id} đã sửa xong {task_id}.", {}

    def _do_rescue(self, robot_id, task_id):
        robot, err = self._robot_or_error(robot_id)
        if err:
            return err
        if robot["escorting"]:
            return False, "busy", f"{robot_id} đang dẫn người của {robot['escorting']}.", {}
        task, err = self._task_check(robot, task_id, "rescue", RESCUE_COST)
        if err:
            return err
        robot["battery"] -= RESCUE_COST
        robot["escorting"] = task_id
        task["status"] = "in_progress"
        task["escorted_by"] = robot_id
        return True, "ok", f"{robot_id} đang dẫn người ở {task_id} về vùng an toàn.", {}

    def _do_register(self, slot_id):
        slot = self.slots.get(slot_id)
        if slot is None:
            return False, "unknown_id", f"Không có slot '{slot_id}'.", {}
        if slot["taken"] or slot_id in self.robots:
            return False, "slot_taken", f"Slot {slot_id} đã có robot.", {}
        slot["taken"] = True
        spec = {
            "id": slot_id,
            "name": slot.get("name", slot_id),
            "specialty": slot["specialty"],
            "battery": slot.get("battery", slot["max_battery"]),
            "max_battery": slot["max_battery"],
            "location": slot["start"],
            "active": True,
        }
        self.robots[slot_id] = self._new_robot(spec, builtin=False)
        self.visited.add((slot_id, slot["start"]))
        return True, "ok", f"Đã đăng ký robot vào slot {slot_id}.", {}
