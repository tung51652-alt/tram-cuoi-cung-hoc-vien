"""Đọc file scenario JSON (UTF-8) thành dict đã kiểm tra tối thiểu."""

import json
from pathlib import Path

REQUIRED_KEYS = ("id", "level", "locations", "goals")


def load_scenario(path):
    """Đọc scenario; ném ValueError kèm tên file nếu thiếu khóa bắt buộc."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ValueError(f"Scenario {path.name} thiếu khóa: {', '.join(missing)}")
    names = {loc["name"] for loc in data["locations"]}
    for edge in data.get("edges", []):
        if edge[0] not in names or edge[1] not in names:
            raise ValueError(f"Scenario {path.name}: cạnh {edge} trỏ tới địa điểm không tồn tại")
    return data
