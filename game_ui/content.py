"""Nội dung hướng dẫn trong game (F1) và tài liệu Bảng công cụ: một nguồn duy nhất.

Mỗi công cụ có: cách gọi, làm gì (câu đơn giản), dùng khi nào, và bài luyện được dùng thử.
"""

# (cách gọi, làm gì, dùng khi nào, bài luyện)
COMMON = [
    ("ctx.goals()", "Cho biết danh sách mục tiêu của bài. Mỗi mục có 'text' (nội dung) và 'done' (xong chưa).",
     "Muốn biết bài yêu cầu gì, hoặc còn mục tiêu nào chưa xong.", "p02"),
    ("ctx.robot('BIP')", "Cho biết thông tin một robot: pin 'battery', vị trí 'location', thẻ 'cards'...",
     "Trước khi ra lệnh, muốn biết robot còn bao nhiêu pin, đang đứng ở đâu.", "p02"),
    ("ctx.robots()", "Giống ctx.robot nhưng trả về danh sách tất cả robot.",
     "Bài có nhiều robot và bạn cần chọn một con phù hợp.", "p09"),
    ("ctx.locations()", "Danh sách mọi địa điểm. Mỗi nơi có 'name' (tên) và 'kind' (loại).",
     "Muốn xem bản đồ có những nơi nào.", "p02"),
    ("ctx.find_location(loại, khu)", "Trả về tên địa điểm đầu tiên đúng loại. Loại 'charger' là trạm sạc.",
     "Cần tên trạm sạc, đèn hiệu khu A, vùng an toàn... mà không muốn viết cứng tên.", "p02"),
    ("ctx.move_to(robot, nơi)", "Robot tự tìm đường và đi tới nơi đó. Không đủ pin hoặc chưa có đường thì đứng yên.",
     "Mỗi khi cần robot đi đâu đó.", "p03"),
    ("ctx.route_cost(robot, nơi)", "Cho biết đi tới nơi đó tốn bao nhiêu pin (chưa có đường thì trả về None). Robot không đi.",
     "Trước một chặng dài, để biết có cần sạc trước không.", "p08"),
    ("ctx.charge(robot)", "Sạc đầy pin. Robot phải đang đứng ở trạm sạc.",
     "Robot đã tới trạm sạc và sắp hết pin.", "p08"),
    ("ctx.go_charge(robot)", "Tự đi tới trạm sạc gần nhất rồi sạc đầy (gộp move_to + charge).",
     "Muốn sạc nhanh mà không cần biết trạm sạc ở đâu.", "p04"),
    ("ctx.say(robot, câu)", "Robot nói một câu (1–80 ký tự). Robot phải đang bật.",
     "Muốn robot báo tin, hoặc để xem nhanh một giá trị.", "p01"),
]

BY_LEVEL = {
    0: [("ctx.activate('BIP')", "Bật robot. Robot đang tắt thì không làm được gì.",
         "Đầu bài, khi robot đang tắt (mắt là một gạch ngang).", "p01")],
    1: [("ctx.gates()", "Danh sách cổng, xếp từ gần tới xa: 'id', 'location' (chỗ đứng để mở), 'zone', "
         "'required_card' (cấp thẻ cần), 'is_open'.", "Muốn biết có những cổng nào và cần thẻ gì.", "p09"),
        ("ctx.check_gate(robot, cổng)", "Hỏi thử robot mở được cổng không. Không làm gì cả, chỉ trả lời.",
         "Muốn biết trước để chọn đúng robot, thay vì thử rồi bị từ chối.", "p09"),
        ("ctx.open_gate(robot, cổng)", "Mở cổng. Robot phải đứng ở cổng, có thẻ đúng cấp, còn ít nhất 2 pin.",
         "Robot đã tới chỗ cổng và cần đi qua.", "p04")],
    2: [("ctx.packages()", "Danh sách kiện hàng: 'id', 'weight' (nặng), 'location' (đang ở), "
         "'destination' (phải tới), 'status'.", "Muốn biết cần giao kiện nào, đi đâu.", "p05"),
        ("ctx.load(robot, kiện)", "Nạp kiện lên robot. Robot và kiện phải ở cùng chỗ, không được quá sức chứa.",
         "Robot đã tới chỗ kiện hàng.", "p05"),
        ("ctx.unload(robot, kiện)", "Dỡ kiện ở chỗ robot đang đứng. Chỉ tính đã giao khi đúng nơi nhận.",
         "Robot đã tới nơi nhận của kiện.", "p05"),
        ("ctx.cargo(robot)", "Cho biết robot đang chở gì: 'items', tổng 'weight', sức chứa 'capacity'.",
         "Muốn gom nhiều kiện mà không bị quá tải.", "p10"),
        ("ctx.receipts()", "Danh sách biên nhận: các kiện đã giao đúng nơi.",
         "Muốn kiểm tra lại mình đã giao được những kiện nào.", "p10"),
        ("ctx.use_planner(obj)", "Giao object lớp con PlannerBase cho game. Game gọi obj.execute(ctx) rồi obj.report().",
         "Phần OOP của Màn 2: gói cách giao hàng vào một lớp.", "p10")],
    3: [("ctx.tasks()", "Danh sách nhiệm vụ: 'id', 'kind' (repair sửa / rescue cứu), 'location', 'status', "
         "'requires' (phải xong việc nào trước).", "Muốn biết có việc gì, ở đâu, việc nào làm trước.", "p06"),
        ("ctx.repair(robot, việc)", "Robot sửa chữa sửa thiết bị. Phải đứng tại chỗ, còn ít nhất 5 pin.",
         "Robot sửa chữa đã tới chỗ thiết bị hỏng.", "p06"),
        ("ctx.rescue(robot, việc)", "Robot cứu hộ bắt đầu dẫn người. Người an toàn khi robot move_to tới vùng an toàn.",
         "Robot cứu hộ đã tới chỗ người cần cứu.", "p06"),
        ("ctx.slots()", "Danh sách slot bạn được tạo robot: 'slot_id' (ví dụ 'R1') và 'specialty'.",
         "Trước khi tạo robot của mình, để biết dùng slot nào.", "p06"),
        ("ctx.register_robot(obj)", "Đăng ký robot lớp con RobotBase của bạn vào game.",
         "Ngay sau khi tạo object robot.", "p06"),
        ("ctx.dispatch(obj, việc)", "Giao một nhiệm vụ cho robot của bạn. Game gọi obj.act(ctx, nhiệm_vụ).",
         "Mỗi khi muốn robot của bạn làm một việc.", "p06")],
}

# Ví dụ ngắn trong F1: để làm gì, code, kết quả mong đợi.
EXAMPLES = [
    {"title": "Đọc lý do bị từ chối",
     "purpose": "Biết vì sao lệnh không thành công để thử cách khác.",
     "code": ["kq = ctx.open_gate('BIP', 'gate_A')", "if not kq.ok:", "    ctx.say('BIP', kq.reason)"],
     "expected": "Nếu không mở được, BIP nói lý do (ví dụ missing_card) và nhật ký có dòng màu cam."},
    {"title": "Đi qua tất cả robot",
     "purpose": "Ra cùng một lệnh cho mọi robot mà không cần biết tên từng con.",
     "code": ["for r in ctx.robots():", "    ctx.say(r['id'], 'Sẵn sàng!')"],
     "expected": "Mỗi robot đang bật nói 'Sẵn sàng!'. Robot đang tắt bị từ chối (inactive)."},
    {"title": "Sạc trước chặng dài",
     "purpose": "Tránh để robot đứng yên giữa đường vì hết pin.",
     "code": ["can = ctx.route_cost('BIP', 'rally_point')", "if can is not None and can > ctx.robot('BIP')['battery']:",
              "    ctx.go_charge('BIP')", "ctx.move_to('BIP', 'rally_point')"],
     "expected": "Thiếu pin thì BIP ghé trạm sạc trước, rồi mới đi tới rally_point."},
]

# Giải thích các khóa hay gặp khi print dict.
KEY_HELP = {
    "id": "tên định danh (dùng khi gọi lệnh)", "name": "tên hiển thị", "battery": "pin hiện tại",
    "max_battery": "pin tối đa khi sạc đầy", "location": "đang ở đâu", "cards": "các cấp thẻ robot có",
    "active": "đã bật chưa (True/False)", "capacity": "sức chứa tối đa", "carrying": "đang chở những kiện nào",
    "escorting": "đang dẫn người của nhiệm vụ nào", "specialty": "chuyên môn: repair/rescue",
    "kind": "loại địa điểm hoặc loại nhiệm vụ", "zone": "thuộc khu nào", "is_charger": "có trạm sạc không",
    "charges_left": "trạm sạc còn mấy lượt (None = không giới hạn)", "weight": "khối lượng kiện",
    "destination": "nơi phải giao tới", "status": "trạng thái (waiting/loaded/delivered, open/done...)",
    "required_card": "cấp thẻ cần để mở cổng", "is_open": "cổng đã mở chưa", "broken": "cổng hỏng, không mở được",
    "requires": "phải xong nhiệm vụ này trước", "slot_id": "tên slot để tạo robot", "text": "nội dung mục tiêu",
    "done": "mục tiêu đã xong chưa",
}

NOTE_HIDDEN = ("Khi chấm chính thức, bài còn chạy trên bản đồ khác cùng luật (tên, thứ tự, pin có thể khác). "
               "Hãy đọc dữ liệu qua công cụ, đừng viết cứng tên địa điểm, cổng, kiện.")


def all_tools():
    tools = list(COMMON)
    for level in sorted(BY_LEVEL):
        tools += BY_LEVEL[level]
    return tools


def tool_lines(tools):
    """Mỗi công cụ là một khối: lệnh, làm gì, dùng khi nào, cách nhau bằng khoảng trống."""
    lines = []
    for call, what, when, practice in tools:
        lines += [("code", call), ("desc", what), ("when", f"Dùng khi: {when}"),
                  ("muted", f"Dùng thử ở bài luyện {practice}"), ("gap", "")]
    return lines


def example_lines():
    lines = [("h", "Ví dụ ngắn")]
    for ex in EXAMPLES:
        lines += [("p", ex["title"]), ("desc", f"Để làm gì: {ex['purpose']}")]
        lines += [("code", row) for row in ex["code"]]
        lines += [("ok", f"Kết quả mong đợi: {ex['expected']}"), ("gap", "")]
    return lines


def reference_lines(level):
    """Các dòng (kiểu, nội dung) cho màn F1 của một màn kiểm tra."""
    lines = [("h", "Công cụ riêng của màn này")] + tool_lines(BY_LEVEL.get(level, []))
    lines += [("h", "Công cụ dùng ở mọi màn")] + tool_lines(COMMON)
    lines += example_lines()
    if level in (1, 2, 3):
        lines.append(("warn", NOTE_HIDDEN))
    return lines


def practice_tool_lines(names):
    """Chỉ các công cụ bài luyện này cần (theo danh sách 'tools' trong file bài)."""
    chosen = [t for t in all_tools() if t[0].split("(")[0] in names]
    return [("h", "Công cụ dùng trong bài này")] + tool_lines(chosen)


def explain_keys(text, limit=8):
    """Giải thích các khóa quen thuộc xuất hiện trong chuỗi print (ví dụ in dict robot)."""
    found = []
    for key, meaning in KEY_HELP.items():
        if f"'{key}'" in text and key not in [k for k, _ in found]:
            found.append((key, meaning))
    return found[:limit]
