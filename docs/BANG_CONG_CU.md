# Bảng công cụ

> Trong game bấm **F1** để xem phần này cho đúng bài đang làm. File này để tra khi không mở game.
> Mỗi lệnh gồm: **làm gì**, **dùng khi nào**, và **bài luyện để dùng thử**.

## Dùng ở mọi màn

### `ctx.goals()`

Cho biết danh sách mục tiêu của bài. Mỗi mục có 'text' (nội dung) và 'done' (xong chưa).

- **Dùng khi:** Muốn biết bài yêu cầu gì, hoặc còn mục tiêu nào chưa xong.
- **Dùng thử:** bài luyện p02

### `ctx.robot('BIP')`

Cho biết thông tin một robot: pin 'battery', vị trí 'location', thẻ 'cards'...

- **Dùng khi:** Trước khi ra lệnh, muốn biết robot còn bao nhiêu pin, đang đứng ở đâu.
- **Dùng thử:** bài luyện p02

### `ctx.robots()`

Giống ctx.robot nhưng trả về danh sách tất cả robot.

- **Dùng khi:** Bài có nhiều robot và bạn cần chọn một con phù hợp.
- **Dùng thử:** bài luyện p09

### `ctx.locations()`

Danh sách mọi địa điểm. Mỗi nơi có 'name' (tên) và 'kind' (loại).

- **Dùng khi:** Muốn xem bản đồ có những nơi nào.
- **Dùng thử:** bài luyện p02

### `ctx.find_location(loại, khu)`

Trả về tên địa điểm đầu tiên đúng loại. Loại 'charger' là trạm sạc.

- **Dùng khi:** Cần tên trạm sạc, đèn hiệu khu A, vùng an toàn... mà không muốn viết cứng tên.
- **Dùng thử:** bài luyện p02

### `ctx.move_to(robot, nơi)`

Robot tự tìm đường và đi tới nơi đó. Không đủ pin hoặc chưa có đường thì đứng yên.

- **Dùng khi:** Mỗi khi cần robot đi đâu đó.
- **Dùng thử:** bài luyện p03

### `ctx.route_cost(robot, nơi)`

Cho biết đi tới nơi đó tốn bao nhiêu pin (chưa có đường thì trả về None). Robot không đi.

- **Dùng khi:** Trước một chặng dài, để biết có cần sạc trước không.
- **Dùng thử:** bài luyện p08

### `ctx.charge(robot)`

Sạc đầy pin. Robot phải đang đứng ở trạm sạc.

- **Dùng khi:** Robot đã tới trạm sạc và sắp hết pin.
- **Dùng thử:** bài luyện p08

### `ctx.go_charge(robot)`

Tự đi tới trạm sạc gần nhất rồi sạc đầy (gộp move_to + charge).

- **Dùng khi:** Muốn sạc nhanh mà không cần biết trạm sạc ở đâu.
- **Dùng thử:** bài luyện p04

### `ctx.say(robot, câu)`

Robot nói một câu (1–80 ký tự). Robot phải đang bật.

- **Dùng khi:** Muốn robot báo tin, hoặc để xem nhanh một giá trị.
- **Dùng thử:** bài luyện p01

## Màn 0 — Đánh thức robot

### `ctx.activate('BIP')`

Bật robot. Robot đang tắt thì không làm được gì.

- **Dùng khi:** Đầu bài, khi robot đang tắt (mắt là một gạch ngang).
- **Dùng thử:** bài luyện p01

## Màn 1 — Cổng cách ly

### `ctx.gates()`

Danh sách cổng, xếp từ gần tới xa: 'id', 'location' (chỗ đứng để mở), 'zone', 'required_card' (cấp thẻ cần), 'is_open'.

- **Dùng khi:** Muốn biết có những cổng nào và cần thẻ gì.
- **Dùng thử:** bài luyện p09

### `ctx.check_gate(robot, cổng)`

Hỏi thử robot mở được cổng không. Không làm gì cả, chỉ trả lời.

- **Dùng khi:** Muốn biết trước để chọn đúng robot, thay vì thử rồi bị từ chối.
- **Dùng thử:** bài luyện p09

### `ctx.open_gate(robot, cổng)`

Mở cổng. Robot phải đứng ở cổng, có thẻ đúng cấp, còn ít nhất 2 pin.

- **Dùng khi:** Robot đã tới chỗ cổng và cần đi qua.
- **Dùng thử:** bài luyện p04

## Màn 2 — Chuyến hàng cuối

### `ctx.packages()`

Danh sách kiện hàng: 'id', 'weight' (nặng), 'location' (đang ở), 'destination' (phải tới), 'status'.

- **Dùng khi:** Muốn biết cần giao kiện nào, đi đâu.
- **Dùng thử:** bài luyện p05

### `ctx.load(robot, kiện)`

Nạp kiện lên robot. Robot và kiện phải ở cùng chỗ, không được quá sức chứa.

- **Dùng khi:** Robot đã tới chỗ kiện hàng.
- **Dùng thử:** bài luyện p05

### `ctx.unload(robot, kiện)`

Dỡ kiện ở chỗ robot đang đứng. Chỉ tính đã giao khi đúng nơi nhận.

- **Dùng khi:** Robot đã tới nơi nhận của kiện.
- **Dùng thử:** bài luyện p05

### `ctx.cargo(robot)`

Cho biết robot đang chở gì: 'items', tổng 'weight', sức chứa 'capacity'.

- **Dùng khi:** Muốn gom nhiều kiện mà không bị quá tải.
- **Dùng thử:** bài luyện p10

### `ctx.receipts()`

Danh sách biên nhận: các kiện đã giao đúng nơi.

- **Dùng khi:** Muốn kiểm tra lại mình đã giao được những kiện nào.
- **Dùng thử:** bài luyện p10

### `ctx.use_planner(obj)`

Giao object lớp con PlannerBase cho game. Game gọi obj.execute(ctx) rồi obj.report().

- **Dùng khi:** Phần OOP của Màn 2: gói cách giao hàng vào một lớp.
- **Dùng thử:** bài luyện p10

## Màn 3 — Đội cứu hộ

### `ctx.tasks()`

Danh sách nhiệm vụ: 'id', 'kind' (repair sửa / rescue cứu), 'location', 'status', 'requires' (phải xong việc nào trước).

- **Dùng khi:** Muốn biết có việc gì, ở đâu, việc nào làm trước.
- **Dùng thử:** bài luyện p06

### `ctx.repair(robot, việc)`

Robot sửa chữa sửa thiết bị. Phải đứng tại chỗ, còn ít nhất 5 pin.

- **Dùng khi:** Robot sửa chữa đã tới chỗ thiết bị hỏng.
- **Dùng thử:** bài luyện p06

### `ctx.rescue(robot, việc)`

Robot cứu hộ bắt đầu dẫn người. Người an toàn khi robot move_to tới vùng an toàn.

- **Dùng khi:** Robot cứu hộ đã tới chỗ người cần cứu.
- **Dùng thử:** bài luyện p06

### `ctx.slots()`

Danh sách slot bạn được tạo robot: 'slot_id' (ví dụ 'R1') và 'specialty'.

- **Dùng khi:** Trước khi tạo robot của mình, để biết dùng slot nào.
- **Dùng thử:** bài luyện p06

### `ctx.register_robot(obj)`

Đăng ký robot lớp con RobotBase của bạn vào game.

- **Dùng khi:** Ngay sau khi tạo object robot.
- **Dùng thử:** bài luyện p06

### `ctx.dispatch(obj, việc)`

Giao một nhiệm vụ cho robot của bạn. Game gọi obj.act(ctx, nhiệm_vụ).

- **Dùng khi:** Mỗi khi muốn robot của bạn làm một việc.
- **Dùng thử:** bài luyện p06

## Ví dụ ngắn

### Đọc lý do bị từ chối

**Để làm gì:** Biết vì sao lệnh không thành công để thử cách khác.

```python
def run(ctx):
    kq = ctx.open_gate('BIP', 'gate_A')
    if not kq.ok:
        ctx.say('BIP', kq.reason)
```

**Kết quả mong đợi:** Nếu không mở được, BIP nói lý do (ví dụ missing_card) và nhật ký có dòng màu cam.

### Đi qua tất cả robot

**Để làm gì:** Ra cùng một lệnh cho mọi robot mà không cần biết tên từng con.

```python
def run(ctx):
    for r in ctx.robots():
        ctx.say(r['id'], 'Sẵn sàng!')
```

**Kết quả mong đợi:** Mỗi robot đang bật nói 'Sẵn sàng!'. Robot đang tắt bị từ chối (inactive).

### Sạc trước chặng dài

**Để làm gì:** Tránh để robot đứng yên giữa đường vì hết pin.

```python
def run(ctx):
    can = ctx.route_cost('BIP', 'rally_point')
    if can is not None and can > ctx.robot('BIP')['battery']:
        ctx.go_charge('BIP')
    ctx.move_to('BIP', 'rally_point')
```

**Kết quả mong đợi:** Thiếu pin thì BIP ghé trạm sạc trước, rồi mới đi tới rally_point.

## Các khóa hay gặp khi `print` dict

| Khóa | Nghĩa |
|---|---|
| `'id'` | tên định danh (dùng khi gọi lệnh) |
| `'name'` | tên hiển thị |
| `'battery'` | pin hiện tại |
| `'max_battery'` | pin tối đa khi sạc đầy |
| `'location'` | đang ở đâu |
| `'cards'` | các cấp thẻ robot có |
| `'active'` | đã bật chưa (True/False) |
| `'capacity'` | sức chứa tối đa |
| `'carrying'` | đang chở những kiện nào |
| `'escorting'` | đang dẫn người của nhiệm vụ nào |
| `'specialty'` | chuyên môn: repair/rescue |
| `'kind'` | loại địa điểm hoặc loại nhiệm vụ |
| `'zone'` | thuộc khu nào |
| `'is_charger'` | có trạm sạc không |
| `'charges_left'` | trạm sạc còn mấy lượt (None = không giới hạn) |
| `'weight'` | khối lượng kiện |
| `'destination'` | nơi phải giao tới |
| `'status'` | trạng thái (waiting/loaded/delivered, open/done...) |
| `'required_card'` | cấp thẻ cần để mở cổng |
| `'is_open'` | cổng đã mở chưa |
| `'broken'` | cổng hỏng, không mở được |
| `'requires'` | phải xong nhiệm vụ này trước |
| `'slot_id'` | tên slot để tạo robot |
| `'text'` | nội dung mục tiêu |
| `'done'` | mục tiêu đã xong chưa |

> Khi chấm chính thức, bài còn chạy trên bản đồ khác cùng luật (tên, thứ tự, pin có thể khác). Hãy đọc dữ liệu qua công cụ, đừng viết cứng tên địa điểm, cổng, kiện.
