"""Ghi event trace theo schema `trace/1`.

Recorder giữ event trong bộ nhớ và (tùy chọn) gửi từng event tới `sink`
để Phase 2 ghi tăng dần ra file riêng. Event chỉ chứa kiểu JSON cơ bản.
"""

TRACE_SCHEMA = "trace/1"
EVENT_KINDS = ("start", "action", "call_start", "call_end", "planner_report", "log", "error", "end")
END_STATUSES = ("complete", "error", "timeout", "action_limit", "crash")


class Recorder:
    def __init__(self, run_id, case_id, sink=None, max_events=5000):
        self.run_id = run_id
        self.case_id = case_id
        self.sink = sink
        self.max_events = max_events
        self.events = []
        self.truncated = False

    def emit(self, kind, **fields):
        if len(self.events) >= self.max_events:
            self.truncated = True
            return None
        event = {"schema": TRACE_SCHEMA, "run_id": self.run_id, "case_id": self.case_id,
                 "step": len(self.events), "kind": kind}
        event.update(fields)
        self.events.append(event)
        if self.sink is not None:
            self.sink(event)
        return event


def validate_event(event):
    """Trả danh sách vấn đề của một event (rỗng nếu hợp lệ)."""
    problems = []
    if not isinstance(event, dict):
        return ["event không phải dict"]
    if event.get("schema") != TRACE_SCHEMA:
        problems.append("sai schema")
    if event.get("kind") not in EVENT_KINDS:
        problems.append(f"kind lạ: {event.get('kind')!r}")
    if not isinstance(event.get("step"), int):
        problems.append("thiếu step")
    if event.get("kind") == "end" and event.get("status") not in END_STATUSES:
        problems.append("end thiếu status hợp lệ")
    return problems
