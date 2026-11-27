"""Hợp đồng giữa tiến trình chính và worker.

Tiến trình chính ghi `job.json`; worker ghi `trace.jsonl` (từng dòng, tăng dần)
và `result.json` (ghi atomic khi xong). Không dùng stdout và không dùng pickle.
"""

import json
import os
import tempfile
from pathlib import Path

PROTOCOL_VERSION = "worker/1"
DEFAULT_TIMEOUT = 5.0          # giây mỗi case
TIMEOUT_BY_LEVEL = {3: 10.0}   # màn 3 có nhiều bước hơn
MAX_TRACE_BYTES = 2 * 1024 * 1024
MAX_RESULT_BYTES = 512 * 1024
MAX_STDERR_BYTES = 16 * 1024
MAX_WORKERS = 2


def timeout_for(level):
    try:
        return TIMEOUT_BY_LEVEL.get(int(level), DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


def write_json_atomic(path, data):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False)
    os.replace(tmp, path)


def read_json_limited(path, limit):
    """Đọc JSON tối đa `limit` byte; None nếu thiếu, quá lớn hoặc hỏng."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read(limit + 1)
    except OSError:
        return None
    if len(raw) > limit:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


class TraceReader:
    """Đọc trace.jsonl tăng dần, chỉ nhận dòng hoàn chỉnh và trong giới hạn."""

    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.buffer = b""
        self.events = []
        self.bad_lines = 0
        self.over_limit = False

    def poll(self):
        """Trả list event mới đọc được kể từ lần trước."""
        new = []
        if self.over_limit or not self.path.exists():
            return new
        with open(self.path, "rb") as handle:
            handle.seek(self.offset)
            chunk = handle.read(max(0, MAX_TRACE_BYTES - self.offset))
        self.offset += len(chunk)
        if self.offset >= MAX_TRACE_BYTES:
            self.over_limit = True
        self.buffer += chunk
        *lines, self.buffer = self.buffer.split(b"\n")
        for line in lines:
            if not line.strip():
                continue
            try:
                event = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                self.bad_lines += 1
                continue
            if isinstance(event, dict):
                new.append(event)
                self.events.append(event)
            else:
                self.bad_lines += 1
        return new
