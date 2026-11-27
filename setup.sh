#!/usr/bin/env bash
# Cài đặt môi trường và mở game TRẠM CUỐI CÙNG (Ubuntu / macOS).
#   bash setup.sh            → cài (lần đầu) rồi mở game
#   bash setup.sh --chi-cai  → chỉ cài, không mở game
# Chạy lại bao nhiêu lần cũng được: lần sau sẽ bỏ qua bước đã xong.
set -e
cd "$(dirname "$0")"

echo "== TRẠM CUỐI CÙNG: chuẩn bị môi trường =="

if ! command -v python3 >/dev/null 2>&1; then
    echo "Không tìm thấy python3. Hãy cài Python 3.10 trở lên rồi chạy lại."
    echo "  Ubuntu: sudo apt install python3 python3-venv"
    exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Cần Python 3.10 trở lên. Bạn đang có: $(python3 --version)"
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "[1/3] Tạo môi trường .venv ..."
    if ! python3 -m venv .venv; then
        echo "Không tạo được .venv. Trên Ubuntu hãy chạy: sudo apt install python3-venv"
        rm -rf .venv
        exit 1
    fi
else
    echo "[1/3] Đã có .venv"
fi

echo "[2/3] Cài thư viện (cần Internet ở lần đầu) ..."
if ! .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt; then
    echo "Cài thư viện thất bại. Kiểm tra mạng rồi chạy lại: bash setup.sh"
    exit 1
fi

if [ "$1" = "--chi-cai" ]; then
    echo "[3/3] Đã cài xong. Lần sau mở game bằng: bash setup.sh"
    exit 0
fi

echo "[3/3] Mở game ..."
exec .venv/bin/python main.py "$@"
