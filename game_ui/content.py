"""Nội dung hướng dẫn hiển thị trong game: bảng công cụ theo màn và ví dụ ngắn.

Viết ngắn cho người mới. Mỗi công cụ: cách gọi, trả về gì, khi nào bị từ chối.
"""

COMMON = [
    ("ctx.goals()", "List mục tiêu: mỗi mục là dict có 'text' và 'done'."),
    ("ctx.robots() / ctx.robot('BIP')", "Thông tin robot: 'battery', 'location', 'cards', 'capacity'..."),
    ("ctx.locations()", "List địa điểm: 'name', 'kind' (beacon, gate, dock, safe_zone...), 'zone', 'is_charger'."),
    ("ctx.find_location(kind, zone)", "Tên địa điểm đầu tiên đúng loại. Ví dụ ctx.find_location('beacon', 'A')."),
    ("ctx.move_to(robot, nơi)", "Tự tìm đường và đi. Từ chối nếu không có lối mở (no_path) hoặc thiếu pin (low_battery)."),
    ("ctx.route_cost(robot, nơi)", "Số pin cần để đi tới nơi đó; None nếu chưa có đường. Không tốn pin."),
    ("ctx.charge(robot) / ctx.go_charge(robot)", "Sạc đầy tại trạm sạc / tự đi tới trạm gần nhất rồi sạc."),
    ("ctx.say(robot, câu)", "Robot nói câu 1–80 ký tự. Robot phải đang bật."),
]

BY_LEVEL = {
    0: [("ctx.activate('BIP')", "Bật robot. Gọi lại khi đã bật vẫn ổn (already_active).")],
    1: [("ctx.gates()", "List cổng (từ gần tới xa): 'id', 'location', 'zone', 'required_card', 'is_open', 'broken'."),
        ("ctx.check_gate(robot, cổng)", "Hỏi thử có mở được không, không đổi gì."),
        ("ctx.open_gate(robot, cổng)", "Robot phải đứng ở cổng, có thẻ đúng cấp, còn ≥2 pin. Từ chối: missing_card, gate_broken, not_at_gate.")],
    2: [("ctx.packages()", "List kiện: 'id', 'name', 'weight', 'destination', 'location', 'status'."),
        ("ctx.load(robot, kiện) / ctx.unload(robot, kiện)", "Nạp kiện ở cùng chỗ (không quá sức chứa) / dỡ tại chỗ đang đứng. Chỉ tính đã giao khi dỡ đúng 'destination'."),
        ("ctx.cargo(robot)", "Khoang đang chở: 'items', 'weight', 'capacity'."),
        ("ctx.receipts()", "List biên nhận các kiện đã giao đúng nơi."),
        ("class X(PlannerBase) + ctx.use_planner(obj)", "Phần OOP: viết execute(self, ctx) và report(self) trả list id đã giao.")],
    3: [("ctx.tasks()", "List nhiệm vụ: 'id', 'kind' (repair/rescue), 'location', 'status', 'requires'."),
        ("ctx.repair(robot, việc)", "Robot sửa chữa đứng tại chỗ, đủ 5 pin. Từ chối: wrong_specialty, blocked, task_done."),
        ("ctx.rescue(robot, việc)", "Robot cứu hộ bắt đầu dẫn người; người an toàn khi robot move_to tới safe_zone."),
        ("ctx.slots()", "Các slot bạn được tạo robot: 'slot_id', 'specialty'."),
        ("class X(RobotBase) + ctx.register_robot(obj)", "Viết act(self, ctx, task); dùng self.id, self.battery."),
        ("ctx.dispatch(obj, task_id)", "Engine gọi obj.act(ctx, task) cho bạn. Có sẵn robot H1 (sửa) và H2 (cứu).")],
}

EXAMPLES = [
    "Đọc lý do từ chối:\n  kq = ctx.open_gate('BIP', 'gate_A')\n  if not kq.ok:\n      print(kq.reason, kq.message)",
    "Có thể truyền nguyên dict:\n  for r in ctx.robots():\n      ctx.move_to(r, 'hub')",
]

NOTE_HIDDEN = ("Khi chấm chính thức, bài còn chạy trên bản đồ khác cùng luật (tên, thứ tự, pin có thể khác). "
               "Hãy đọc dữ liệu qua công cụ, đừng viết cứng id.")


def reference_lines(level):
    """Các dòng (kiểu, nội dung) cho màn tra cứu."""
    lines = [("h", "Công cụ của màn")]
    tools = BY_LEVEL.get(level, []) + COMMON
    for call, desc in tools:
        lines.append(("code", call))
        lines.append(("p", desc))
    lines.append(("h", "Ví dụ ngắn"))
    for example in EXAMPLES:
        for row in example.split("\n"):
            lines.append(("code", row))
        lines.append(("p", ""))
    if level in (1, 2, 3):
        lines.append(("warn", NOTE_HIDDEN))
    return lines
