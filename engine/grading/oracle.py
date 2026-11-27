"""Oracle độc lập: phát lại trace trên World mới để kiểm tra luật và tính mục tiêu.

Không chạy lại code học viên và không dùng lời giải mẫu. Mỗi event hành động
được áp dụng lại bằng luật engine; kết quả phải khớp với event đã ghi.
"""

from engine.contracts.trace import validate_event
from engine.world.world import World


def replay(scenario, events):
    """Trả (world, problems). problems rỗng nghĩa là trace nhất quán với luật."""
    world = World(scenario)
    problems = []
    if not events or events[0].get("kind") != "start":
        problems.append("Trace thiếu event start.")
    for event in events:
        issues = validate_event(event)
        if issues:
            problems.append(f"Event {event.get('step')}: {', '.join(issues)}")
            continue
        if event["kind"] != "action":
            continue
        ok, reason, _message, _data = world.apply(event["action"], event["actor"], dict(event.get("args") or {}))
        robot = world.robots.get(event["actor"])
        after = None
        if robot is not None:
            after = {"battery": robot["battery"], "location": robot["location"]}
        recorded = event.get("after") or None
        recorded_brief = {"battery": recorded["battery"], "location": recorded["location"]} if recorded else None
        if ok != event.get("ok") or reason != event.get("reason") or after != recorded_brief:
            problems.append(f"Event {event['step']} ({event['action']}) không khớp luật khi phát lại.")
    return world, problems
