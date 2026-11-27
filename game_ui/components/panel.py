"""Thanh trên và panel bên phải: chế độ chạy, mục tiêu, tiến độ, sự kiện gần nhất."""

import pygame

from game_ui import theme
from game_ui.drawing import primitives as P

MODE_STYLE = {
    "official": ("CHÍNH THỨC", theme.CYAN), "public": ("CHẠY THỬ", theme.CYAN),
    "practice": ("LUYỆN TẬP — không tính điểm", theme.GREEN), "demo": ("DEMO — không tính điểm", theme.AMBER),
}


def top_bar(surface, rect, title, mode, status_text, speed=1.0, paused=False):
    pygame.draw.rect(surface, theme.PANEL_BG, rect)
    pygame.draw.line(surface, theme.PANEL_LINE, rect.bottomleft, rect.bottomright, 2)
    P.text(surface, "TRẠM CUỐI CÙNG", (rect.left + 14, rect.centery), 16, theme.CYAN, "Bold", "midleft")
    P.text(surface, title, (rect.left + 190, rect.centery), 15, theme.TEXT, "SemiBold", "midleft")
    label, color = MODE_STYLE.get(mode, (str(mode).upper(), theme.CYAN))
    width = theme.font(12, "SemiBold").size(label)[0] + 10
    badge = P.tag(surface, label, (rect.right - 20 - width / 2, rect.centery), color, 12)
    info = f"{status_text}  ·  {'TẠM DỪNG' if paused else f'tốc độ {speed:g}x'}"
    P.text(surface, info, (badge.left - 14, rect.centery), 13, theme.MUTED, anchor="midright")


def side_panel(surface, rect, player, scroll=0):
    """Panel mục tiêu và nhật ký; nội dung dài được cắt theo vùng, không ép chữ nhỏ."""
    pygame.draw.rect(surface, theme.PANEL_BG, rect)
    pygame.draw.line(surface, theme.PANEL_LINE, rect.topleft, rect.bottomleft, 2)
    x, y = rect.left + 16, rect.top + 12
    goals = list(player.goals.values())
    done = sum(1 for g in goals if g.get("done"))
    P.text(surface, f"Mục tiêu  {done}/{len(goals)}", (x, y), 16, theme.TEXT, "Bold")
    y += 28
    for goal in goals[:8]:
        ok = goal.get("done")
        P.icon(surface, "ok" if ok else "todo", (x + 7, y + 9))
        for i, line in enumerate(P.wrap(goal.get("text", goal.get("id")), 13, rect.width - 56)[:2]):
            P.text(surface, line, (x + 22, y + i * 17), 13, theme.TEXT if ok else theme.MUTED)
            last = i
        y += 18 * (last + 1) + 4
    y += 6
    carried = [f"{r.id}: {', '.join(r.carrying)}" for r in player.robots.values() if r.carrying]
    if player.packages:
        delivered = sum(1 for p in player.packages.values() if p.get("status") == "delivered")
        P.text(surface, f"Đã giao {delivered}/{len(player.packages)} kiện · đang chở: {'; '.join(carried) or 'không'}",
               (x, y), 12, theme.CYAN)
        y += 22
    step, total = player.progress
    P.text(surface, f"Sự kiện {step}/{total}", (x, y), 15, theme.TEXT, "Bold")
    y += 24
    pygame.draw.line(surface, theme.PANEL_LINE, (x, y - 4), (rect.right - 16, y - 4))
    area = pygame.Rect(x, y, rect.width - 32, rect.bottom - y - 10)
    clip = surface.get_clip()
    surface.set_clip(area)
    lines = []
    entries = list(player.log)
    if player.done and getattr(player, "prints", None):
        entries.append(("print_head", "Bạn đã print:"))
        entries += [("print", line) for line in player.prints]
    for kind, message in entries:
        color = {"ok": theme.TEXT, "refuse": theme.AMBER, "error": theme.RED, "call": theme.CYAN,
                 "print_head": theme.GREEN, "print": (190, 232, 200)}.get(kind, theme.TEXT)
        icon = {"refuse": "warn", "error": "error", "call": "call", "print_head": None, "print": None}.get(kind, "dot")
        wrapped = P.wrap(message, 12, area.width - 18)
        for i, line in enumerate(wrapped[:3]):
            lines.append((icon if i == 0 else None, line, color))
    visible = area.height // 16
    start = max(0, len(lines) - visible - scroll)
    for i, (icon, line, color) in enumerate(lines[start:start + visible]):
        if icon:
            P.icon(surface, icon, (area.left + 5, area.top + i * 16 + 8), 5)
        P.text(surface, line, (area.left + 14, area.top + i * 16), 12, color)
    surface.set_clip(clip)
