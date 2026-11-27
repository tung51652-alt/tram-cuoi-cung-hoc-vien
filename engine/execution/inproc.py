"""Chạy một file bài học viên trên một case, ngay trong tiến trình hiện tại.

Phase 1 dùng để chấm headless và kiểm thử. Phase 2 sẽ gọi cùng hàm này bên
trong worker subprocess để tách lỗi/timeout khỏi giao diện.
"""

import builtins
import contextlib
import io
import os
import sys
import traceback
import types
import uuid

from engine.contracts.trace import Recorder
from engine.world.world import World
from game_api.context import ActionLimitReached, Context

MAX_LOG_CHARS = 64 * 1024

HINTS = {
    "SyntaxError": "Kiểm tra dấu ':', thụt lề và ngoặc ở dòng được báo hoặc dòng ngay trên.",
    "IndentationError": "Thụt lề chưa thống nhất; dùng 4 dấu cách cho mỗi mức.",
    "NameError": "Tên biến/hàm chưa được định nghĩa hoặc viết sai chính tả.",
    "TypeError": "Sai kiểu hoặc số lượng tham số; xem bảng công cụ để biết thứ tự tham số.",
    "KeyError": "Dict không có khóa này; in dict ra để xem các khóa có sẵn.",
    "AttributeError": "Object không có thuộc tính/phương thức này; kiểm tra tên và super().__init__.",
    "IndexError": "Vị trí vượt quá độ dài list.",
    "ValueError": "Giá trị không hợp lệ, ví dụ slot không tồn tại.",
    "ImportError": "Không import được; chỉ dùng game_api và file trong student/.",
    "ModuleNotFoundError": "Không tìm thấy module; kiểm tra tên file helper trong student/.",
    "NotImplementedError": "Còn phương thức chưa viết xong.",
    "ZeroDivisionError": "Phép chia cho 0.",
    "EOFError": "Bài không được dùng input(): game tự chạy, không nhập từ bàn phím.",
    "SystemExit": "Không gọi exit()/sys.exit() trong bài.",
    "FileNotFoundError": "File bài làm bị đổi tên hoặc xóa; tên file phải giữ nguyên như đề.",
    "RecursionError": "Hàm gọi lại chính nó quá nhiều lần.",
}


class _BoundedWriter(io.TextIOBase):
    """Ghi log có giới hạn để print liên tục không làm đầy bộ nhớ."""

    def __init__(self, limit):
        self.limit = limit
        self.parts = []
        self.size = 0
        self.truncated = False

    def write(self, text):
        if self.size < self.limit:
            chunk = text[: self.limit - self.size]
            self.parts.append(chunk)
            self.size += len(chunk)
            if len(chunk) < len(text):
                self.truncated = True
        else:
            self.truncated = True
        return len(text)

    def getvalue(self):
        return "".join(self.parts)


def _no_input(*_args, **_kwargs):
    raise EOFError("input() không dùng được trong bài")


def _source_line(path, lineno):
    """Đọc trực tiếp dòng code (không qua linecache để luôn là byte mới)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            for number, text in enumerate(handle, start=1):
                if number == lineno:
                    return text.rstrip()[:200]
    except OSError:
        pass
    return None


def describe_error(exc, submission_root):
    """Chuyển exception thành dict lỗi dễ hiểu, trỏ vào file và dòng code của học viên."""
    root = os.path.realpath(str(submission_root))
    name = type(exc).__name__
    info = {"type": name, "message": str(exc), "file": None, "line": None, "code": None,
            "hint": HINTS.get(name, "Đọc thông điệp lỗi và dòng được báo.")}
    if "NoneType" in info["message"] or "là None" in info["message"]:
        info["hint"] = ("Một giá trị đang là None. Thường do hàm của bạn quên `return`, "
                        "hoặc tìm không thấy nên biến chưa được gán.")
    if isinstance(exc, SyntaxError) and exc.filename:
        path = os.path.realpath(exc.filename)
        info["file"] = os.path.relpath(path, root) if path.startswith(root + os.sep) else os.path.basename(path)
        info["line"] = exc.lineno
        info["message"] = exc.msg
        info["code"] = _source_line(path, exc.lineno) if exc.lineno else None
        return info
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        path = os.path.realpath(frame.filename)
        if path.startswith(root + os.sep):
            info["file"] = os.path.relpath(path, root)
            info["line"] = frame.lineno
            info["code"] = _source_line(path, frame.lineno)
            break
    return info


def run_case(entry_path, submission_root, scenario, run_id=None, max_actions=2000, sink=None):
    """Chạy run(ctx) của entry_path trên một World mới tạo từ `scenario`.

    Trả dict {status, events, error, log, log_truncated}. status thuộc
    complete / error / action_limit. Không bao giờ ném lỗi của học viên ra ngoài.
    """
    run_id = run_id or uuid.uuid4().hex[:12]
    entry_path = os.path.realpath(str(entry_path))
    submission_root = os.path.realpath(str(submission_root))
    world = World(scenario)
    rec = Recorder(run_id, scenario["id"], sink=sink)
    rec.emit("start", scenario=scenario["id"], level=scenario["level"], state=world.snapshot())
    ctx = Context(world, rec, student_root=submission_root, max_actions=max_actions)
    log = _BoundedWriter(MAX_LOG_CHARS)
    status, error = "complete", None
    modules_before = set(sys.modules)
    path_before = list(sys.path)
    old_input = builtins.input
    sys.path.insert(0, submission_root)
    ctx._activate_runtime()
    try:
        if not os.path.exists(entry_path):
            rel = os.path.relpath(entry_path, os.path.dirname(submission_root))
            raise FileNotFoundError(f"Không tìm thấy file {rel}. Kiểm tra tên file trong thư mục student/.")
        with open(entry_path, "rb") as handle:
            source = handle.read()
        module = types.ModuleType("student_entry")
        module.__file__ = entry_path
        builtins.input = _no_input
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            code = compile(source, entry_path, "exec", dont_inherit=True)
            exec(code, module.__dict__)
            run = module.__dict__.get("run")
            if not callable(run):
                raise NameError("Không tìm thấy hàm run(ctx) trong file.")
            run(ctx)
    except ActionLimitReached as exc:
        status = "action_limit"
        error = {"type": "ActionLimit", "message": str(exc), "file": None, "line": None, "code": None,
                 "hint": "Có thể vòng lặp không dừng; kiểm tra điều kiện thoát."}
    except (Exception, SystemExit) as exc:  # noqa: BLE001 — lỗi học viên được ghi lại, không ném tiếp
        status = "error"
        error = describe_error(exc, submission_root)
    finally:
        builtins.input = old_input
        ctx._deactivate_runtime()
        sys.path[:] = path_before
        # Xóa helper học viên khỏi cache để lượt sau nạp byte mới.
        for name in set(sys.modules) - modules_before:
            module_obj = sys.modules.get(name)
            path = getattr(module_obj, "__file__", None) or ""
            if os.path.realpath(path).startswith(submission_root + os.sep):
                del sys.modules[name]
    if error:
        rec.emit("error", error=error)
    rec.emit("end", status=status, goals_done=world.done_goal_ids())
    return {"status": status, "events": rec.events, "error": error,
            "log": log.getvalue(), "log_truncated": log.truncated, "trace_truncated": rec.truncated}
