"""CLI chấm headless (Phase 1). Phase 4 nối vào `main.py --grade --headless`.

    python -m engine.grading --submission student [--level 2] [--official] [--output local/results/latest.json]

Exit code 0 khi tạo được báo cáo (kể cả bài lỗi); 2 khi lỗi công cụ.
"""

import argparse
import sys

from engine.contracts.report import write_report_atomic
from engine.grading.feedback import format_level
from engine.grading.grader import ToolError, available_levels, grade_submission


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chấm bài TRẠM CUỐI CÙNG không cần giao diện.")
    parser.add_argument("--submission", default="student")
    parser.add_argument("--level", type=int, choices=[0, 1, 2, 3])
    parser.add_argument("--official", action="store_true", help="Dùng biến thể ẩn (chỉ có ở bản giảng viên).")
    parser.add_argument("--output")
    parser.add_argument("--chi-tiet", "--verbose", dest="detailed", action="store_true",
                        help="Hiện đủ mọi tiêu chí kèm mã và bằng chứng.")
    args = parser.parse_args(argv)
    released = available_levels()
    if not released:
        print("Bản này mới có khu Luyện tập. Thử: python -m engine.grading.practice --exercise p01")
        return 0
    if args.level is not None and args.level not in released:
        print(f"Màn {args.level} chưa được phát hành (mở vào ngày kiểm tra).")
        return 0
    try:
        report = grade_submission(args.submission, None if args.level is None else [args.level],
                                  mode="official" if args.official else "public")
    except ToolError as exc:
        print(f"Lỗi công cụ chấm: {exc}", file=sys.stderr)
        return 2
    for level in report["levels"]:
        print("\n".join(format_level(level, detailed=args.detailed)))
        print()
    label = "CHÍNH THỨC" if report["mode"] == "official" else "điểm thử trên bản đồ công bố"
    print(f"Tổng: {report['total']}/{report['max_total']} ({label})")
    if args.output:
        write_report_atomic(report, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
