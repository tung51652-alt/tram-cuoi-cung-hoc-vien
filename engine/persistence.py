"""Lưu cài đặt, kết quả chấm và tiến độ luyện tập trong local/ (đã gitignore).

Ghi atomic (file tạm + os.replace). Chính sách xung đột khi mở nhiều cửa sổ:
lần ghi sau thắng. File hỏng không chặn game: trả mặc định kèm cảnh báo.
"""

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / "local"
SETTINGS = LOCAL / "settings.json"
RESULTS = LOCAL / "results" / "latest.json"
PRACTICE = LOCAL / "practice" / "progress.json"

DEFAULT_SETTINGS = {"view": "practice", "level": 0, "exercise": "p01", "speed": 1.0, "reduced_motion": False}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_json(path):
    """Trả (data, warning). Thiếu file → (None, None); hỏng → (None, thông báo)."""
    path = Path(path)
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, f"File {path.name} bị hỏng nên đã bỏ qua (bài làm không bị ảnh hưởng)."
    if not isinstance(data, dict):
        return None, f"File {path.name} sai định dạng nên đã bỏ qua."
    return data, None


def load_settings():
    data, warning = read_json(SETTINGS)
    settings = dict(DEFAULT_SETTINGS)
    if data:
        for key, default in DEFAULT_SETTINGS.items():
            if isinstance(data.get(key), type(default)) or (isinstance(default, float) and isinstance(data.get(key), int)):
                settings[key] = data[key]
    if settings["view"] not in ("practice", "level"):
        settings["view"] = "practice"
    if settings["level"] not in (0, 1, 2, 3):
        settings["level"] = 0
    if settings["speed"] not in (0.5, 1.0, 2.0):
        settings["speed"] = 1.0
    return settings, warning


def save_settings(settings):
    write_json(SETTINGS, {k: settings[k] for k in DEFAULT_SETTINGS})


def staleness(report, hashes, rubric_version, engine_version):
    """Dict level -> lý do kết quả cũ cần chấm lại (rỗng nếu còn khớp)."""
    reasons = {}
    if not report:
        return reasons
    for level in report.get("levels", []):
        key = str(level.get("level"))
        if report.get("rubric_version") != rubric_version:
            reasons[key] = "rubric đã đổi"
        elif report.get("engine_version") != engine_version:
            reasons[key] = "engine đã đổi"
        elif report.get("source_hashes", {}).get(key) != hashes.get(key):
            reasons[key] = "code đã sửa sau lần chấm"
    return reasons
