"""Báo cáo chấm `report/1` và ghi atomic."""

import json
import os
import tempfile
from pathlib import Path

REPORT_SCHEMA = "report/1"
REQUIRED = ("schema_version", "assessment_id", "engine_version", "rubric_version", "source_hashes",
            "levels", "total", "max_total", "timestamp", "mode")


def validate_report(report):
    return [f"thiếu {key}" for key in REQUIRED if key not in report]


def write_report_atomic(report, path):
    """Ghi JSON UTF-8 qua file tạm rồi os.replace để không để lại file dở."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".report-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_report(path):
    """Đọc báo cáo; trả None nếu thiếu hoặc hỏng (không ảnh hưởng bài làm)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and not validate_report(data) else None
