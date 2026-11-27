"""Lớp nền cho object quản lý phương án giao hàng ở màn 2."""

from abc import ABC, abstractmethod


class PlannerBase(ABC):
    """Lớp nền trừu tượng cho phương án giao hàng của bạn.

    Viết lớp con, gọi super().__init__(name), override execute() và report(),
    rồi giao object cho engine:

        class Courier(PlannerBase):
            def __init__(self):
                super().__init__("Courier")
                self.done = []
            def execute(self, ctx):
                ...  # dùng ctx.load / ctx.move_to / ctx.unload
            def report(self):
                return self.done

        def run(ctx):
            ctx.use_planner(Courier())
    """

    def __init__(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tên planner phải là chuỗi không rỗng.")
        self._pb_name = name.strip()
        self._pb_initialized = True

    @property
    def name(self):
        """Tên planner đặt lúc khởi tạo."""
        if not getattr(self, "_pb_initialized", False):
            raise RuntimeError("Lớp con chưa gọi super().__init__(name).")
        return self._pb_name

    @abstractmethod
    def execute(self, ctx):
        """Thực hiện phương án giao hàng bằng các công cụ của ctx."""

    @abstractmethod
    def report(self):
        """Trả list id các kiện mà planner ghi nhận đã giao thành công."""
