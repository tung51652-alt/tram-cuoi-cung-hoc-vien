# Bảng công cụ

> Trong game bấm **F1** để xem bảng này cho đúng màn đang chơi. File này để tra khi không mở game.

## Dùng ở mọi màn

| Gọi | Làm gì |
|---|---|
| `ctx.goals()` | List mục tiêu: mỗi mục là dict có 'text' và 'done'. |
| `ctx.robots() / ctx.robot('BIP')` | Thông tin robot: 'battery', 'location', 'cards', 'capacity'... |
| `ctx.locations()` | List địa điểm: 'name', 'kind' (beacon, gate, dock, safe_zone...), 'zone', 'is_charger'. |
| `ctx.find_location(kind, zone)` | Tên địa điểm đầu tiên đúng loại. Ví dụ ctx.find_location('beacon', 'A'). |
| `ctx.move_to(robot, nơi)` | Tự tìm đường và đi. Từ chối nếu không có lối mở (no_path) hoặc thiếu pin (low_battery). |
| `ctx.route_cost(robot, nơi)` | Số pin cần để đi tới nơi đó; None nếu chưa có đường. Không tốn pin. |
| `ctx.charge(robot) / ctx.go_charge(robot)` | Sạc đầy tại trạm sạc / tự đi tới trạm gần nhất rồi sạc. |
| `ctx.say(robot, câu)` | Robot nói câu 1–80 ký tự. Robot phải đang bật. |

## Màn 0 — Đánh thức robot

| Gọi | Làm gì |
|---|---|
| `ctx.activate('BIP')` | Bật robot. Gọi lại khi đã bật vẫn ổn (already_active). |

## Màn 1 — Cổng cách ly

| Gọi | Làm gì |
|---|---|
| `ctx.gates()` | List cổng (từ gần tới xa): 'id', 'location', 'zone', 'required_card', 'is_open', 'broken'. |
| `ctx.check_gate(robot, cổng)` | Hỏi thử có mở được không, không đổi gì. |
| `ctx.open_gate(robot, cổng)` | Robot phải đứng ở cổng, có thẻ đúng cấp, còn ≥2 pin. Từ chối: missing_card, gate_broken, not_at_gate. |

## Màn 2 — Chuyến hàng cuối

| Gọi | Làm gì |
|---|---|
| `ctx.packages()` | List kiện: 'id', 'name', 'weight', 'destination', 'location', 'status'. |
| `ctx.load(robot, kiện) / ctx.unload(robot, kiện)` | Nạp kiện ở cùng chỗ (không quá sức chứa) / dỡ tại chỗ đang đứng. Chỉ tính đã giao khi dỡ đúng 'destination'. |
| `ctx.cargo(robot)` | Khoang đang chở: 'items', 'weight', 'capacity'. |
| `ctx.receipts()` | List biên nhận các kiện đã giao đúng nơi. |
| `class X(PlannerBase) + ctx.use_planner(obj)` | Phần OOP: viết execute(self, ctx) và report(self) trả list id đã giao. |

## Màn 3 — Đội cứu hộ

| Gọi | Làm gì |
|---|---|
| `ctx.tasks()` | List nhiệm vụ: 'id', 'kind' (repair/rescue), 'location', 'status', 'requires'. |
| `ctx.repair(robot, việc)` | Robot sửa chữa đứng tại chỗ, đủ 5 pin. Từ chối: wrong_specialty, blocked, task_done. |
| `ctx.rescue(robot, việc)` | Robot cứu hộ bắt đầu dẫn người; người an toàn khi robot move_to tới safe_zone. |
| `ctx.slots()` | Các slot bạn được tạo robot: 'slot_id', 'specialty'. |
| `class X(RobotBase) + ctx.register_robot(obj)` | Viết act(self, ctx, task); dùng self.id, self.battery. |
| `ctx.dispatch(obj, task_id)` | Engine gọi obj.act(ctx, task) cho bạn. Có sẵn robot H1 (sửa) và H2 (cứu). |

## Ví dụ ngắn

**Đọc lý do từ chối:**

```python
kq = ctx.open_gate('BIP', 'gate_A')
if not kq.ok:
    print(kq.reason, kq.message)
```

**Có thể truyền nguyên dict:**

```python
for r in ctx.robots():
    ctx.move_to(r, 'hub')
```

> Khi chấm chính thức, bài còn chạy trên bản đồ khác cùng luật (tên, thứ tự, pin có thể khác). Hãy đọc dữ liệu qua công cụ, đừng viết cứng id.
