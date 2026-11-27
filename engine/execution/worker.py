"""Worker chạy bài học viên trong tiến trình riêng.

Gọi bởi runner:  python -B engine/execution/worker.py <job.json>
Tiến trình chính không import bài học viên; mọi lỗi/treo nằm gọn trong worker.
"""

import json
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(job_path):
    # Không ghi .pyc và dùng thư mục cache rỗng: import helper luôn đọc source mới,
    # kể cả khi file đổi trong cùng giây và cùng độ dài.
    sys.dont_write_bytecode = True
    sys.pycache_prefix = tempfile.mkdtemp(prefix="tcc-pyc-")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from engine.execution.inproc import run_case
    from engine.execution.protocol import MAX_TRACE_BYTES, PROTOCOL_VERSION, write_json_atomic

    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    # Lưới an toàn: nếu tiến trình chính bị tắt đột ngột, worker tự thoát sau hạn cứng
    # thay vì chạy mãi (ví dụ vòng lặp vô hạn của bài học viên).
    limit = float(job.get("hard_limit", 30))
    watchdog = threading.Timer(limit, lambda: os._exit(9))
    watchdog.daemon = True
    watchdog.start()
    trace_file = open(job["trace_path"], "w", encoding="utf-8")
    written = [0]

    def sink(event):
        line = json.dumps(event, ensure_ascii=False) + "\n"
        size = len(line.encode("utf-8"))
        if written[0] + size > MAX_TRACE_BYTES:
            return
        trace_file.write(line)
        trace_file.flush()  # ghi ngay để runner đọc được cả khi worker bị kill
        written[0] += size

    try:
        result = run_case(job["entry"], job["submission_root"], job["scenario"],
                          run_id=job["run_id"], max_actions=job.get("max_actions", 2000), sink=sink)
    finally:
        trace_file.close()
    summary = {"protocol": PROTOCOL_VERSION, "run_id": job["run_id"], "case_id": job["scenario"]["id"],
               "status": result["status"], "error": result["error"], "log": result["log"],
               "log_truncated": result["log_truncated"], "trace_truncated": result["trace_truncated"]}
    write_json_atomic(job["result_path"], summary)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main(sys.argv[1]))
