# 4. Đọc thông tin: robot, địa điểm, mục tiêu

Trước khi ra lệnh, hãy **xem thế giới đang có gì**. Các hàm dưới đây chỉ đọc, không làm robot di chuyển.

## Robot

```python
def run(ctx):
    bip = ctx.robot("BIP")
    print(bip)
    print("Pin còn:", bip["battery"])
```

`ctx.robot("BIP")` trả về một **dict**. Các khóa hay dùng:

| Khóa | Ý nghĩa | Ví dụ |
|---|---|---|
| `"battery"` | Pin hiện tại | `17` |
| `"location"` | Đang đứng ở đâu | `"dock_boot"` |
| `"cards"` | Các cấp thẻ đang có | `[1]` |
| `"active"` | Đã bật chưa | `True` |

Muốn xem **tất cả robot** thì dùng vòng lặp:

```python
def run(ctx):
    for r in ctx.robots():
        print(r["id"], r["battery"])
```

## Địa điểm

```python
def run(ctx):
    for loc in ctx.locations():
        print(loc["name"], loc["kind"])
```

Mỗi địa điểm có `"kind"` cho biết loại: `beacon` (đèn hiệu), `gate` (cổng), `dock` (bệ nhận hàng), `safe_zone` (vùng an toàn)... Cần tìm nhanh thì dùng:

```python
def run(ctx):
    tram_sac = ctx.find_location("charger")      # tên địa điểm có trạm sạc
    print("Trạm sạc ở:", tram_sac)
```

## Mục tiêu

```python
def run(ctx):
    for g in ctx.goals():
        print(g["text"], "→ xong" if g["done"] else "→ chưa")
```

## Xem `print` ở đâu?

Sau khi robot làm xong, các dòng `print` của bạn hiện **đầy đủ** ở **cuối Nhật ký** (khung bên phải, cuộn chuột để xem hết). Bấm **F6** để xem toàn bộ trong một cửa sổ lớn. Nếu bạn in một dict (ví dụ `print(ctx.robot("BIP"))`), game giải thích luôn từng khóa như `'battery'`, `'location'` nghĩa là gì.

Cũng có thể cho robot **nói** điều bạn muốn xem:

```python
def run(ctx):
    pin = ctx.robot("BIP")["battery"]
    ctx.say("BIP", f"Pin của mình là {pin}")
```

> Sửa dict nhận được **không** làm thay đổi game, ví dụ gán `bip["battery"] = 100` thì robot vẫn không có thêm pin. Muốn robot làm gì phải gọi công cụ.

🧪 Luyện: **bài 2** (đọc trạng thái).

➡️ Tiếp theo: [5. Di chuyển và pin](05-di-chuyen-va-pin.md)
