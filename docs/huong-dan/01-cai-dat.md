# 1. Cài đặt và mở game

⏱ Khoảng 5 phút, chỉ làm **một lần**.

## Bước 1: Cài Python

- Cần **Python 3.10 trở lên**. Tải ở [python.org/downloads](https://www.python.org/downloads/).
- **Windows:** khi cài, nhớ tick ô **"Add python.exe to PATH"** ở màn hình đầu tiên.
- **Ubuntu:** thường có sẵn. Nếu thiếu, chạy `sudo apt install python3 python3-venv`.

Kiểm tra: mở Terminal (Windows: *Command Prompt*) và gõ `python --version` (Ubuntu: `python3 --version`). Thấy `Python 3.10` trở lên là được.

## Bước 2: Lấy game về máy

Chọn **một** trong hai cách:

- **Dùng Git:** `git clone <link repo>`
- **Không dùng Git:** trên trang GitHub bấm **Code → Download ZIP**, rồi giải nén.

## Bước 3: Chạy file cài đặt

| Máy | Làm gì |
|---|---|
| Windows | Mở thư mục game, **bấm đúp `setup.bat`** |
| Ubuntu / macOS | Mở Terminal trong thư mục game, gõ `bash setup.sh` |

File cài đặt tự làm 3 việc:

```
[1/3] Tạo môi trường .venv ...
[2/3] Cài thư viện (cần Internet ở lần đầu) ...
[3/3] Mở game ...
```

Xong là cửa sổ game hiện ra. **Từ lần sau**, cũng chạy đúng file đó để mở game: nó bỏ qua phần đã cài nên mở rất nhanh, và không cần mạng.

## Bước 4: Chọn Python trong VS Code (để VS Code gợi ý code)

1. Mở thư mục game bằng VS Code (**File → Open Folder**).
2. Bấm **Ctrl+Shift+P**, gõ `Python: Select Interpreter`.
3. Chọn dòng có chữ **`.venv`**.

## Gặp sự cố?

| Thấy | Làm |
|---|---|
| `Khong tim thay Python` | Cài lại Python và nhớ tick *Add to PATH* |
| `Không tạo được .venv` (Ubuntu) | `sudo apt install python3-venv` rồi chạy lại |
| `Cài thư viện thất bại` | Kiểm tra mạng, chạy lại file cài đặt |
| Cửa sổ đen hoặc không mở | Chạy lại file cài đặt và đọc dòng báo lỗi cuối cùng |

➡️ Tiếp theo: [2. Làm quen giao diện](02-giao-dien.md)
