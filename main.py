"""TRẠM CUỐI CÙNG — Giải cứu trước khi mất điện.

Cách chạy (sau khi cài requirements trong .venv):
    python main.py                 # mở game, nhớ màn đã chọn lần trước
    python main.py --level 2       # mở thẳng màn 2
    python main.py --practice p03  # mở bài luyện p03
    python main.py --demo          # xem demo hoạt cảnh, không tính điểm
    python main.py --grade --headless --submission ./student --output ./results/latest.json
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args(argv):
    parser = argparse.ArgumentParser(description="TRẠM CUỐI CÙNG — game kiểm tra Python.")
    parser.add_argument("--level", type=int, choices=[0, 1, 2, 3], help="Mở/chấm màn này.")
    parser.add_argument("--practice", help="Mở bài luyện, ví dụ p01.")
    parser.add_argument("--demo", action="store_true", help="Xem demo hoạt cảnh (không tính điểm).")
    parser.add_argument("--grade", action="store_true", help="Chấm bài, không mở cửa sổ khi kèm --headless.")
    parser.add_argument("--headless", action="store_true", help="Không mở giao diện (dùng cùng --grade).")
    parser.add_argument("--submission", default=str(ROOT / "student"), help="Thư mục bài làm.")
    parser.add_argument("--output", help="Nơi ghi báo cáo JSON khi chấm.")
    parser.add_argument("--official", action="store_true", help="Chấm trên biến thể ẩn (bản giảng viên).")
    parser.add_argument("--chi-tiet", "--verbose", dest="detailed", action="store_true")
    parser.add_argument("--size", default="1280x720", help="Kích thước cửa sổ, ví dụ 1366x768.")
    return parser.parse_args(argv)


def main(argv=None):
    if sys.version_info < (3, 10):
        print("Cần Python 3.10 trở lên. Bạn đang dùng", sys.version.split()[0])
        return 1
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.headless and not args.grade:
        print("--headless chỉ dùng cùng --grade (game cần cửa sổ để hiển thị).", file=sys.stderr)
        return 2
    if args.grade:
        from engine.grading.__main__ import main as grade_main

        cli = ["--submission", args.submission]
        if args.level is not None:
            cli += ["--level", str(args.level)]
        if args.output:
            cli += ["--output", args.output]
        if args.official:
            cli.append("--official")
        if args.detailed:
            cli.append("--chi-tiet")
        return grade_main(cli)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("Chưa cài pygame-ce cho Python này.\n"
              "Hãy chạy (cùng interpreter bạn dùng để mở game):\n"
              f"    {Path(sys.executable).name} -m pip install -r requirements.txt")
        return 1
    from game_ui.app import run_app

    try:
        width, height = (int(v) for v in args.size.lower().split("x"))
    except ValueError:
        width, height = 1280, 720
    run_app(args.submission, args.level, args.practice, args.demo, (max(640, width), max(360, height)))
    return 0


if __name__ == "__main__":  # bắt buộc trên Windows vì game tạo tiến trình con
    sys.exit(main())
