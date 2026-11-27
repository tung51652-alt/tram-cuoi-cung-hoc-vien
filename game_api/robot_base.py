"""Lớp nền robot cho màn 3."""

from abc import ABC, abstractmethod

from game_api import _runtime


class RobotBase(ABC):
    """Lớp nền trừu tượng cho robot do bạn viết.

    Khởi tạo bằng id slot được cấp (xem ctx.slots()). Profile (chuyên môn,
    pin tối đa, vị trí xuất phát) lấy từ slot, bạn không tự đặt được.

        class Fixer(RobotBase):
            def __init__(self, slot_id):
                super().__init__(slot_id)
                self.jobs_done = 0
            def act(self, ctx, task):
                ctx.move_to(self.id, task["location"])
                if ctx.repair(self.id, task["id"]):
                    self.jobs_done += 1

    Sau đó: robot = Fixer("R1"); ctx.register_robot(robot); ctx.dispatch(robot, task_id).
    Lỗi: ValueError nếu slot không tồn tại; RuntimeError nếu tạo ngoài run(ctx).
    """

    def __init__(self, slot_id):
        if not isinstance(slot_id, str):
            raise TypeError("slot_id phải là chuỗi, ví dụ 'R1'.")
        ctx = _runtime.current
        if ctx is None:
            raise RuntimeError("Chỉ tạo robot bên trong run(ctx).")
        slot = ctx._world.slots.get(slot_id)
        if slot is None:
            raise ValueError(f"Không có slot '{slot_id}'. Xem ctx.slots().")
        self._rb_slot = dict(slot)
        self._rb_world = ctx._world
        self._rb_initialized = True

    def _rb_require(self):
        if not getattr(self, "_rb_initialized", False):
            raise RuntimeError("Lớp con chưa gọi super().__init__(slot_id).")

    def _rb_live(self):
        return self._rb_world.robots.get(self._rb_slot["slot_id"])

    @property
    def id(self):
        """Id robot, trùng id slot."""
        self._rb_require()
        return self._rb_slot["slot_id"]

    @property
    def specialty(self):
        """Chuyên môn: "repair" hoặc "rescue"."""
        self._rb_require()
        return self._rb_slot["specialty"]

    @property
    def battery(self):
        """Pin hiện tại (đọc trực tiếp từ engine, chỉ đọc)."""
        self._rb_require()
        live = self._rb_live()
        return live["battery"] if live else self._rb_slot.get("battery", self._rb_slot["max_battery"])

    @property
    def location(self):
        """Vị trí hiện tại."""
        self._rb_require()
        live = self._rb_live()
        return live["location"] if live else self._rb_slot["start"]

    @abstractmethod
    def act(self, ctx, task):
        """Xử lý một nhiệm vụ. `task` là dict bản sao từ ctx.tasks()."""
