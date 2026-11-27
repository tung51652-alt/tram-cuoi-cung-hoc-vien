"""Chạy bài học viên trong worker subprocess, không chặn tiến trình gọi.

- `CaseRun`: một worker cho một case; `poll()` không chặn, đọc trace tăng dần,
  kiểm tra timeout, kill + wait khi quá hạn.
- `RunManager`: hàng đợi có giới hạn số worker; gửi lượt mới cùng khóa sẽ hủy
  lượt cũ (bấm "Chạy lại" liên tục không sinh worker vô hạn).
- `run_case_isolated`: bản chặn dùng cho grader/CLI.
"""

import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from engine.execution.protocol import (
    MAX_RESULT_BYTES, MAX_STDERR_BYTES, MAX_WORKERS, TraceReader, read_json_limited, timeout_for,
    write_json_atomic,
)

ROOT = Path(__file__).resolve().parents[2]
WORKER = Path(__file__).with_name("worker.py")
RUNS_DIR = ROOT / "local" / "runs"


class CaseRun:
    """Một lượt chạy một case trong worker riêng."""

    def __init__(self, entry, submission_root, scenario, run_id=None, timeout=None, max_actions=2000):
        self.run_id = run_id or uuid.uuid4().hex[:12]
        self.case_id = scenario["id"]
        self.timeout = timeout if timeout is not None else timeout_for(scenario.get("level"))
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        self.dir = Path(tempfile.mkdtemp(prefix=f"{self.run_id}-", dir=str(RUNS_DIR)))
        self.trace_path = self.dir / "trace.jsonl"
        self.result_path = self.dir / "result.json"
        self.stderr_path = self.dir / "stderr.txt"
        job = {"run_id": self.run_id, "entry": str(Path(entry).resolve()),
               "submission_root": str(Path(submission_root).resolve()), "scenario": scenario,
               "max_actions": max_actions, "trace_path": str(self.trace_path),
               "hard_limit": self.timeout + 5,
               "result_path": str(self.result_path)}
        write_json_atomic(self.dir / "job.json", job)
        self.reader = TraceReader(self.trace_path)
        self.result = None
        self._stderr = open(self.stderr_path, "wb")
        # stdin đóng: input() nhận EOF thay vì chờ. Không shell=True, dùng đúng interpreter hiện tại.
        self.proc = subprocess.Popen(
            [sys.executable, "-B", str(WORKER), str(self.dir / "job.json")],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=self._stderr, cwd=str(ROOT),
        )
        self.started = time.monotonic()

    @property
    def done(self):
        return self.result is not None

    def poll(self):
        """Không chặn. Trả list event mới; khi xong thì self.result có giá trị."""
        new = self.reader.poll()
        if self.done:
            return new
        code = self.proc.poll()
        if code is None and time.monotonic() - self.started > self.timeout:
            self._finish("timeout")
        elif code is not None:
            new += self.reader.poll()
            self._finish(None)
        return new

    def cancel(self):
        if not self.done:
            self._finish("cancelled")

    def _finish(self, forced_status):
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait()
        self._stderr.close()
        self.reader.poll()
        summary = read_json_limited(self.result_path, MAX_RESULT_BYTES) if forced_status is None else None
        events = list(self.reader.events)
        if summary and summary.get("run_id") == self.run_id:
            status, error = summary["status"], summary["error"]
            log = summary.get("log", "")
        else:
            status = forced_status or "crash"
            error = self._infra_error(status)
            log = ""
            # Trace dở dang: bỏ event "end" nếu có và tự đánh dấu kết thúc do runner.
            events = [e for e in events if e.get("kind") != "end"]
            if events:
                events.append({"schema": "trace/1", "run_id": self.run_id, "case_id": self.case_id,
                               "step": len(events), "kind": "end", "status": "timeout" if status != "crash" else "crash",
                               "by": "runner", "goals_done": None})
        self.result = {"run_id": self.run_id, "case_id": self.case_id, "status": status, "error": error,
                       "events": events, "log": log, "bad_lines": self.reader.bad_lines,
                       "trace_over_limit": self.reader.over_limit,
                       "duration": round(time.monotonic() - self.started, 3)}
        shutil.rmtree(self.dir, ignore_errors=True)

    def _infra_error(self, status):
        if status == "timeout":
            return {"type": "Timeout", "message": f"Chạy quá {self.timeout:g} giây nên đã dừng.", "file": None,
                    "line": None, "code": None,
                    "hint": "Có thể có vòng lặp không bao giờ dừng (while True, hoặc điều kiện không đổi)."}
        if status == "cancelled":
            return {"type": "Cancelled", "message": "Lượt chạy đã bị hủy vì có lượt mới.", "file": None,
                    "line": None, "code": None, "hint": None}
        try:
            stderr = self.stderr_path.read_bytes()[:MAX_STDERR_BYTES].decode("utf-8", "replace")
        except OSError:
            stderr = ""
        return {"type": "WorkerCrash", "message": "Worker dừng bất thường (lỗi công cụ, không phải lỗi bài).",
                "file": None, "line": None, "code": None, "hint": None, "detail": stderr[-2000:]}


class Cancelled(Exception):
    """Lượt chấm bị hủy (ví dụ người dùng đóng cửa sổ)."""


def run_case_isolated(entry, submission_root, scenario, run_id=None, timeout=None, poll_interval=0.01, cancel=None):
    """Chạy một case trong worker và chờ xong (dùng cho grader/CLI).

    `cancel` là threading.Event tùy chọn: khi được set, worker bị thu hồi và ném Cancelled.
    """
    run = CaseRun(entry, submission_root, scenario, run_id=run_id, timeout=timeout)
    try:
        while not run.done:
            if cancel is not None and cancel.is_set():
                run.cancel()
                raise Cancelled()
            run.poll()
            if not run.done:
                time.sleep(poll_interval)
    except BaseException:
        run.cancel()
        raise
    return run.result


class RunManager:
    """Quản lý worker cho giao diện: giới hạn số worker, hủy lượt cũ cùng khóa."""

    def __init__(self, max_workers=MAX_WORKERS):
        self.max_workers = max_workers
        self.active = {}     # key -> CaseRun
        self.queue = []      # (key, kwargs)
        self.finished = {}   # key -> result của lượt mới nhất

    def submit(self, key, **kwargs):
        """Xếp hàng lượt mới cho `key`; hủy lượt đang chạy/đang chờ của cùng key."""
        if key in self.active:
            self.active.pop(key).cancel()
        self.queue = [(k, kw) for k, kw in self.queue if k != key]
        self.finished.pop(key, None)
        self.queue.append((key, kwargs))
        self._start_waiting()

    def _start_waiting(self):
        while self.queue and len(self.active) < self.max_workers:
            key, kwargs = self.queue.pop(0)
            self.active[key] = CaseRun(**kwargs)

    def poll(self):
        """Không chặn. Trả dict key -> list event mới."""
        updates = {}
        for key, run in list(self.active.items()):
            events = run.poll()
            if events:
                updates[key] = events
            if run.done:
                self.finished[key] = run.result
                del self.active[key]
        self._start_waiting()
        return updates

    def shutdown(self):
        """Thu hồi mọi worker (gọi khi đóng cửa sổ hoặc Ctrl+C)."""
        self.queue.clear()
        for run in self.active.values():
            run.cancel()
        self.active.clear()
