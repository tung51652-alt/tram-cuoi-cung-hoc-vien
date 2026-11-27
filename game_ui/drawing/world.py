"""Vẽ môi trường: sàn, hành lang, cổng trượt, đèn hiệu, bệ nhận, khu hỏng, vùng an toàn.

Vẽ theo 3 lớp: hậu cảnh (sàn + trang trí theo màn), địa điểm/vật thể, tiền cảnh
(hiệu ứng khói, đèn báo động). Nhân vật vẽ ở giữa bởi playfield.
"""

import math

import pygame

from game_ui import theme
from game_ui.drawing import primitives as P


def _seed(value):
    return sum(map(ord, str(value)))


def background(surface, level, t):
    tint = theme.LEVEL_TINT.get(level, theme.LEVEL_TINT[1])
    surface.fill(theme.BG)
    for gx in range(0, surface.get_width(), 40):
        for gy in range(0, surface.get_height(), 40):
            base = theme.FLOOR if (gx // 40 + gy // 40) % 2 == 0 else theme.FLOOR_ALT
            color = tuple(min(255, (b + c) // 2) for b, c in zip(base, tint))
            pygame.draw.rect(surface, color, (gx, gy, 40, 40))
            pygame.draw.rect(surface, theme.GRID, (gx, gy, 40, 40), 1)
    w, h = surface.get_size()
    pygame.draw.rect(surface, theme.WALL, (0, 0, w, h), 8)
    pygame.draw.rect(surface, (30, 40, 56), (8, 8, w - 16, h - 16), 2)
    # Đèn báo động mất điện ở bốn góc.
    for i, (cx, cy) in enumerate(((20, 20), (w - 20, 20), (20, h - 20), (w - 20, h - 20))):
        on = (math.sin(t * 3 + i) + 1) / 2
        P.glow(surface, (cx, cy), 26, theme.RED, int(40 + 50 * on))
        pygame.draw.circle(surface, (120 + int(120 * on), 40, 50), (cx, cy), 5)
    if level == 2:
        _conveyor(surface, t)
    if level == 3:
        _escape_ship_bay(surface)


def _conveyor(surface, t):
    rect = pygame.Rect(30, 560, 260, 26)
    pygame.draw.rect(surface, (40, 44, 52), rect, border_radius=6)
    offset = int(t * 30) % 20
    for x in range(rect.left - 20 + offset, rect.right, 20):
        if rect.left < x < rect.right - 4:
            pygame.draw.line(surface, (80, 86, 96), (x, rect.top + 4), (x, rect.bottom - 4), 3)
    P.text(surface, "BĂNG TẢI KHO", (rect.centerx, rect.top - 10), 10, theme.MUTED, "SemiBold", "center")


def _escape_ship_bay(surface):
    w = surface.get_width()
    pygame.draw.rect(surface, (30, 50, 44), (w - 150, 230, 130, 200), border_radius=14)
    pygame.draw.rect(surface, (60, 120, 90), (w - 150, 230, 130, 200), 2, border_radius=14)


def corridors(surface, player):
    """Hành lang nối các địa điểm. Lối qua cổng có vạch cảnh báo."""
    for edge in player.edges:
        a, b = player.points[edge[0]], player.points[edge[1]]
        gate_id = edge[3] if len(edge) > 3 else None
        pygame.draw.line(surface, (16, 24, 36), a, b, 38)
        pygame.draw.line(surface, (52, 68, 92), a, b, 32)
        pygame.draw.line(surface, (44, 58, 80), a, b, 2)
        if gate_id:
            gate = player.gates.get(gate_id, {})
            color = theme.GREEN if gate.get("is_open") else (theme.RED if gate.get("broken") else theme.AMBER)
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            for k in (-0.15, 0.15):
                px, py = mx + (b[0] - a[0]) * k, my + (b[1] - a[1]) * k
                pygame.draw.circle(surface, color, (int(px), int(py)), 3)
    for name, (x, y) in player.points.items():
        pygame.draw.circle(surface, (16, 24, 36), (int(x), int(y)), 22)
        pygame.draw.circle(surface, (56, 74, 100), (int(x), int(y)), 19)


def locations(surface, player, t):
    for name, (x, y) in player.points.items():
        loc = player.locations.get(name, {})
        kind = loc.get("kind")
        drawer = {"gate": _gate_node, "beacon": _beacon, "dock": _dock, "rally": _rally,
                  "safe_zone": _safe_zone, "site": _site}.get(kind)
        if drawer:
            drawer(surface, player, name, loc, x, y, t)
        if loc.get("is_charger"):
            _charger(surface, x, y, t, loc)
        label = name if len(name) <= 14 else name[:13] + "…"
        ly = y + 38 if y + 38 < surface.get_height() - 14 else y + 26
        lx = max(50, min(surface.get_width() - 50, x))
        P.text(surface, label, (lx, ly), 11, theme.MUTED, "SemiBold", "center")


def _charger(surface, x, y, t, loc):
    pygame.draw.circle(surface, (30, 70, 60), (int(x), int(y)), 17, 3)
    pts = [(x - 3, y - 9), (x + 4, y - 9), (x, y - 1), (x + 5, y - 1), (x - 4, y + 10), (x - 1, y + 2), (x - 6, y + 2)]
    pygame.draw.polygon(surface, theme.GREEN, [(int(px) - 22, int(py) - 18) for px, py in pts])
    if loc.get("charges_left") is not None:
        P.text(surface, f"còn {loc['charges_left']} lượt sạc", (x, y - 30), 10, theme.GREEN, anchor="center")


def _gate_node(surface, player, name, loc, x, y, t):
    gate = next((g for g in player.gates.values() if g.get("location") == name), None)
    frame = pygame.Rect(0, 0, 50, 50)
    frame.center = (int(x), int(y))
    pygame.draw.rect(surface, (70, 84, 104), frame, border_radius=6)
    pygame.draw.rect(surface, (20, 28, 40), frame.inflate(-8, -8), border_radius=4)
    if gate is None:
        return
    frac = max(0.0, min(1.0, gate.get("open_frac", 0.0)))
    inner = frame.inflate(-8, -8)
    half = inner.width // 2
    shift = int(half * frac)
    panel_color = (110, 60, 60) if gate.get("broken") else (130, 146, 168)
    clip = surface.get_clip()
    surface.set_clip(inner)  # cánh cửa trượt vào trong khung, không tràn ra ngoài
    pygame.draw.rect(surface, panel_color, (inner.left - shift, inner.top, half, inner.height))
    pygame.draw.rect(surface, panel_color, (inner.centerx + shift, inner.top, half, inner.height))
    pygame.draw.line(surface, (90, 104, 124), (inner.left - shift + half - 2, inner.top), (inner.left - shift + half - 2, inner.bottom), 2)
    surface.set_clip(clip)
    pygame.draw.rect(surface, (70, 84, 104), frame, 4, border_radius=6)
    status = "HỎNG" if gate.get("broken") else ("MỞ" if gate.get("is_open") else "ĐÓNG")
    color = theme.RED if gate.get("broken") else (theme.GREEN if gate.get("is_open") else theme.AMBER)
    pygame.draw.circle(surface, color, (frame.right - 6, frame.top + 6), 4)
    card = gate.get("required_card", "?")
    P.tag(surface, f"{gate.get('id', '?')} · thẻ {card} · {status}", (x, y - 36), color, 10)
    if gate.get("broken"):
        for i in range(3):
            a = t * 9 + i * 2
            pygame.draw.line(surface, theme.AMBER, (x + 20, y - 10), (x + 20 + math.cos(a) * 8, y - 10 + math.sin(a) * 8), 2)


def _beacon(surface, player, name, loc, x, y, t):
    reached = name in player.visited
    color = theme.GREEN if reached else theme.CYAN
    pulse = (math.sin(t * 3) + 1) / 2
    P.glow(surface, (x, y), int(30 + 10 * pulse), color, 70 if reached else 40)
    pygame.draw.circle(surface, color, (int(x), int(y)), int(14 + 6 * pulse), 2)
    pygame.draw.polygon(surface, (200, 210, 225), [(x - 6, y + 10), (x + 6, y + 10), (x + 2, y - 12), (x - 2, y - 12)])
    pygame.draw.circle(surface, color, (int(x), int(y - 14)), 5)
    zone = loc.get("zone") or "?"
    P.tag(surface, f"KHU {zone} · ĐÃ TỚI" if reached else f"KHU {zone}", (x, y - 30), color, 10)


def _dock(surface, player, name, loc, x, y, t):
    pad = pygame.Rect(0, 0, 56, 40)
    pad.center = (int(x), int(y + 4))
    delivered = sum(1 for p in player.packages.values() if p.get("status") == "delivered" and p.get("location") == name)
    pygame.draw.rect(surface, (40, 64, 70), pad, border_radius=6)
    pygame.draw.rect(surface, theme.GREEN if delivered else (90, 140, 150), pad, 2, border_radius=6)
    P.text(surface, "BỆ NHẬN", (pad.centerx, pad.top - 9), 9, theme.MUTED, "SemiBold", "center")
    if delivered:
        P.check_mark(surface, (pad.right - 4, pad.top + 2), 5)


def _rally(surface, player, name, loc, x, y, t):
    pts = [(x + 22 * math.cos(a), y + 22 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
    pygame.draw.polygon(surface, (60, 60, 100), pts)
    pygame.draw.polygon(surface, theme.CYAN, pts, 2)
    pygame.draw.line(surface, theme.WHITE, (x + 8, y - 4), (x + 8, y - 30), 2)
    pygame.draw.polygon(surface, theme.CYAN, [(x + 8, y - 30), (x + 26, y - 24), (x + 8, y - 18)])
    P.text(surface, "ĐIỂM TẬP KẾT", (x, y - 44), 10, theme.CYAN, "SemiBold", "center")


def _safe_zone(surface, player, name, loc, x, y, t):
    zone = pygame.Rect(0, 0, 110, 90)
    zone.center = (int(x), int(y))
    pygame.draw.rect(surface, (34, 80, 60), zone, border_radius=12)
    pygame.draw.rect(surface, theme.GREEN, zone, 2, border_radius=12)
    # tàu thoát hiểm
    ship = [(x - 26, y - 20), (x + 20, y - 20), (x + 34, y - 10), (x + 20, y), (x - 26, y)]
    pygame.draw.polygon(surface, (200, 210, 225), ship)
    pygame.draw.circle(surface, theme.CYAN, (int(x + 12), int(y - 10)), 4)
    flame = 4 + 3 * math.sin(t * 20)
    pygame.draw.polygon(surface, theme.AMBER, [(x - 26, y - 16), (x - 26 - flame, y - 10), (x - 26, y - 4)])
    P.text(surface, "VÙNG AN TOÀN", (x, zone.top - 9), 10, theme.GREEN, "SemiBold", "center")


def _site(surface, player, name, loc, x, y, t):
    repairs = [k for k in player.tasks.values() if k.get("location") == name and k.get("kind") == "repair"]
    for task in repairs:
        fixed = task.get("status") == "done"
        box = pygame.Rect(0, 0, 40, 30)
        box.center = (int(x - 4), int(y))
        pygame.draw.rect(surface, (60, 70, 86), box, border_radius=4)
        pygame.draw.rect(surface, theme.GREEN if fixed else theme.RED, box, 2, border_radius=4)
        for i in range(3):
            on = fixed or int(t * 4 + i) % 3 == 0
            pygame.draw.circle(surface, theme.GREEN if fixed else (theme.RED if on else (80, 40, 40)),
                               (box.left + 8 + i * 10, box.top + 8), 3)
        if not fixed:
            for i in range(4):  # tia lửa
                a = t * 10 + i * 1.7 + _seed(name)
                sx, sy = box.right - 4, box.top + 4
                pygame.draw.line(surface, theme.AMBER, (sx, sy), (sx + math.cos(a) * 9, sy + math.sin(a) * 9), 2)
        if task.get("status") == "done" and task.get("fx", 9) < 1.0:
            P.glow(surface, box.center, 34, theme.GREEN, int(120 * (1 - task["fx"])))
        P.tag(surface, f"{task['id']} {'ĐÃ SỬA' if fixed else 'HỎNG'}", (x - 4, y + 24), theme.GREEN if fixed else theme.RED, 10)


def smoke(surface, player, t):
    """Tiền cảnh: khói trên các khu còn hỏng."""
    for task in player.tasks.values():
        if task.get("kind") != "repair" or task.get("status") == "done":
            continue
        x, y = player.points.get(task.get("location"), (None, None))
        if x is None:
            continue
        layer = pygame.Surface((80, 80), pygame.SRCALPHA)
        for i in range(4):
            k = (t * 0.4 + i / 4) % 1
            pygame.draw.circle(layer, (120, 120, 130, int(70 * (1 - k))), (40 + int(math.sin(k * 6 + i) * 8), int(70 - k * 60)),
                               int(6 + k * 12))
        surface.blit(layer, (x - 40, y - 80))


def packages(surface, player):
    for pkg in player.packages.values():
        if "x" not in pkg:
            continue
        color = theme.CATEGORY_COLOR.get(pkg.get("category"), (180, 180, 190))
        rect = pygame.Rect(0, 0, 14, 12)
        rect.center = (int(pkg["x"]), int(pkg["y"]))
        pygame.draw.rect(surface, theme.SHADOW, rect.move(1, 2), border_radius=2)
        pygame.draw.rect(surface, color, rect, border_radius=2)
        pygame.draw.line(surface, (40, 40, 40), rect.midtop, rect.midbottom, 1)
        if pkg.get("status") == "delivered":
            P.check_mark(surface, (rect.right, rect.top), 4)
        P.text(surface, str(pkg.get("id", "?"))[:6], (rect.centerx, rect.bottom + 6), 9, theme.TEXT, anchor="center")
