<p align="center"><img src="docs/images/cover.png" alt="Trạm Cuối Cùng" width="100%"></p>

# Trạm Cuối Cùng: Hướng dẫn học viên

> **Hiện mới mở khu Luyện tập.** Các màn kiểm tra sẽ mở vào ngày kiểm tra. Hôm đó chạy `git pull` (hoặc tải lại ZIP) để có thêm các màn; bài luyện của bạn vẫn giữ nguyên.

Bạn viết code Python, **robot trong game làm theo đúng code của bạn**. Không cần điều khiển bằng bàn phím, cũng không cần biết làm game.

## Bắt đầu trong 3 bước

**Bước 1: Cài Python 3.10 trở lên** từ [python.org](https://www.python.org/downloads/). Trên Windows nhớ tick ô **"Add python.exe to PATH"**.

**Bước 2: Chạy file cài đặt** trong thư mục game. Lần đầu cần mạng, khoảng 1–3 phút:

| Máy | Làm gì |
|---|---|
| Windows | Bấm đúp **`setup.bat`** |
| Ubuntu / macOS | Mở Terminal trong thư mục game, gõ **`bash setup.sh`** |

Cửa sổ game sẽ mở ra. Lần sau muốn chơi tiếp, chạy lại đúng file đó.

**Bước 3: Làm bài luyện 1** theo [hướng dẫn từng bước](docs/huong-dan/03-bai-dau-tien.md).

![Giao diện game](docs/images/huong-dan/giao-dien.png)

## Vòng làm bài

```
Sửa code trong VS Code  →  Lưu (Ctrl+S)  →  Bấm "Chạy lại code" (F5)  →  Xem robot làm  →  F6 để kiểm tra
```

Không cần tắt game. Mỗi lần chạy lại, mọi thứ được đặt lại từ đầu và game dùng code mới nhất.

## Học theo thứ tự

| # | Bài hướng dẫn | Luyện bằng |
|---|---|---|
| 1 | [Cài đặt và mở game](docs/huong-dan/01-cai-dat.md) | — |
| 2 | [Làm quen giao diện](docs/huong-dan/02-giao-dien.md) | — |
| 3 | [Bài đầu tiên: đánh thức BIP](docs/huong-dan/03-bai-dau-tien.md) | Bài luyện 1 |
| 4 | [Đọc thông tin: robot, địa điểm, mục tiêu](docs/huong-dan/04-doc-thong-tin.md) | Bài luyện 2 |
| 5 | [Di chuyển và pin](docs/huong-dan/05-di-chuyen-va-pin.md) | Bài luyện 3, 8 |
| 6 | [Bị từ chối thì làm gì?](docs/huong-dan/06-bi-tu-choi.md) | Bài luyện 4, 9 |
| 7 | [Vòng lặp và giao hàng](docs/huong-dan/07-giao-hang.md) | Bài luyện 5, 10 |
| 8 | [Đội robot của bạn (OOP)](docs/huong-dan/08-doi-robot.md) | Bài luyện 6 |
| 9 | [Sửa lỗi code](docs/huong-dan/09-sua-loi.md) | Bài luyện 7 |
| 10 | [Xem đề, gợi ý và cách chấm điểm](docs/huong-dan/10-de-va-cham-diem.md) | — |

Tra nhanh mọi lệnh: [Bảng công cụ](docs/BANG_CONG_CU.md), mỗi lệnh có *làm gì*, *dùng khi nào* và *bài luyện để thử*. Trong game bấm **F1**: mỗi bài luyện có danh sách **các việc cần làm**, nhấn **H** để mở từng gợi ý.

## Phím tắt

| F5 | F6 | F7 | F1 | F2 | Space |
|---|---|---|---|---|---|
| Chạy lại code | Kiểm tra / chấm màn | Chấm cả bài | Đề & công cụ (H: gợi ý) | Kết quả | Tạm dừng |

## Hỏi nhanh

- **Có cần biết OOP mới làm được không?** Các nhiệm vụ chính chỉ cần `if`, `for`, `list`, `dict`. OOP có điểm riêng ở Màn 2 và 3.
- **Có cần chia nhiều file không?** Không. Mỗi màn một file là đủ.
- **Bị từ chối có mất điểm không?** Không. Đọc lý do rồi thử cách khác ([xem bài 6](docs/huong-dan/06-bi-tu-choi.md)).
- **Điểm trong game là điểm chính thức à?** Không. Đó là điểm thử. Giảng viên chấm lại từ code bạn nộp.

## Lời cảm ơn

Xin chân thành cảm ơn nhà tài trợ **anh Phạm Minh Khương** (HIT-15), Trưởng ban Đào tạo và Phát triển, đã đồng hành và hỗ trợ dự án.
