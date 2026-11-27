"""Định dạng phản hồi ngắn gọn cho người mới học (dùng chung CLI và giao diện).

Nguyên tắc: không hiện mã tiêu chí/thuật ngữ kỹ thuật ở chế độ thường; mỗi màn
tối đa 3 việc nên làm tiếp; lỗi chỉ hiện lỗi đầu tiên kèm dòng code và gợi ý.
"""

PROGRESS_NOUN = {0: "mục tiêu", 1: "khu", 2: "kiện", 3: "nhiệm vụ"}
MAX_TODO = 3


def progress_line(level_report):
    """Ví dụ: "Đã giao 2/6 kiện" (tính trên bản đồ chính của màn)."""
    main = level_report["cases"][0]
    noun = PROGRESS_NOUN.get(level_report["level"], "mục tiêu")
    verb = {1: "Đã mở và tới", 2: "Đã giao", 3: "Đã hoàn thành"}.get(level_report["level"], "Đã đạt")
    return f"{verb} {main['goals_done']}/{main['goals_total']} {noun}"


def first_error(level_report):
    for case in level_report["cases"]:
        if case.get("error"):
            return case["error"]
    return None


def format_error(err, indent="   "):
    lines = []
    if err["type"] in ("Timeout", "Cancelled", "WorkerCrash", "ActionLimit"):
        lines.append(f"{indent}⚠ {err['message']}")
    else:
        where = f"{err['file']} dòng {err['line']}" if err.get("file") else "bài làm"
        lines.append(f"{indent}⚠ Lỗi ở {where}:")
        if err.get("code"):
            lines.append(f"{indent}     {err['code'].strip()}")
        lines.append(f"{indent}   {err['type']}: {err['message']}")
    if err.get("hint"):
        lines.append(f"{indent}   Gợi ý: {err['hint']}")
    return lines


def format_level(level_report, detailed=False):
    lines = [f"Màn {level_report['level']} — {level_report['title']}: "
             f"{level_report['score']}/{level_report['max']} điểm  ({progress_line(level_report)})"]
    passed = [c for c in level_report["criteria"] if c["passed"]]
    failed = [c for c in level_report["criteria"] if not c["passed"]]
    if detailed:
        for crit in level_report["criteria"]:
            mark = "✓" if crit["passed"] else "✗"
            lines.append(f"   {mark} [{crit['id']}] {crit['points']}/{crit['max']} {crit['text']} — {crit['evidence']}")
    else:
        if passed and failed:
            lines.append(f"   ✓ Đã làm được {len(passed)}/{len(level_report['criteria'])} phần.")
        if failed:
            lines.append("   Nên làm tiếp:")
            for crit in failed[:MAX_TODO]:
                lines.append(f"     • {crit['text']} (+{crit['max']}). {crit['hint']}")
            if len(failed) > MAX_TODO:
                lines.append(f"     … và {len(failed) - MAX_TODO} phần khác (xem thêm với --chi-tiet).")
        else:
            lines.append("   ✓ Hoàn thành tất cả!")
    err = first_error(level_report)
    if err:
        lines.extend(format_error(err))
    return lines
