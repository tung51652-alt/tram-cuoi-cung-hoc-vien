"""Nhân vật vẽ bằng primitive: BIP, KEP, robot sửa chữa, robot cứu hộ, người.

Mỗi loại có silhouette và màu khác nhau, kèm nhãn chữ (không chỉ dựa vào màu).
"""

import math

import pygame

from game_ui import theme
from game_ui.drawing import primitives as P

REPAIR = (255, 140, 66)
RESCUE = (240, 244, 250)
KEP_BODY = (130, 150, 175)


def robot_kind(robot):
    if robot.id == "BIP":
        return "bip"
    if robot.id == "KEP" or 2 in (robot.cards or []):
        return "kep"
    if robot.specialty == "repair":
        return "repair"
    if robot.specialty == "rescue":
        return "rescue"
    return "bip"


def draw_robot(surface, robot, t):
    if not robot.visible:
        return
    kind = robot_kind(robot)
    bob = math.sin(t * 3 + (sum(map(ord, robot.id)) % 7)) * 1.5 if robot.active else 0
    x, y = robot.x, robot.y
    if robot.anim == "shake" and robot.anim_t < 0.5:
        x += math.sin(robot.anim_t * 60) * 3
    layer = pygame.Surface((90, 100), pygame.SRCALPHA)
    cx, cy = 45, 55 + bob
    if robot.highlight > 0:
        pygame.draw.circle(layer, (*theme.CYAN, int(120 * min(1, robot.highlight))), (45, 58), 30, 3)
    {"bip": _bip, "kep": _kep, "repair": _repair, "rescue": _rescue}[kind](layer, cx, cy, robot, t)
    if robot.anim == "charge" and robot.anim_t < 1.0:
        for i in range(3):
            a = t * 6 + i * 2.1
            pygame.draw.line(layer, theme.GREEN, (cx + math.cos(a) * 22, cy + math.sin(a) * 22),
                             (cx + math.cos(a) * 28, cy + math.sin(a) * 28), 3)
    if robot.anim == "scan" and robot.anim_t < 1.0:
        k = robot.anim_t
        pygame.draw.arc(layer, theme.CYAN, (cx - 26, cy - 26, 52, 52), -0.6 + k * 2, 0.6 + k * 2, 3)
    alpha = int(255 * max(0.0, min(1.0, robot.fade)))
    if alpha < 255:
        layer.set_alpha(alpha)
    P.shadow(surface, (x, y + 18), 18, 6)
    surface.blit(layer, (x - 45, y - 55))
    color = {"repair": REPAIR, "rescue": (255, 120, 130), "kep": (210, 200, 120)}.get(kind, theme.CYAN)
    P.tag(surface, robot.id, (x, y - 34 + bob), color)
    P.battery_bar(surface, (x - 6, y + 26), robot.battery, robot.max_battery)


def _eye(layer, cx, cy, robot, t, r=7):
    on = robot.active or (robot.anim == "wake" and robot.anim_t > 0.4)
    blink = (t * 0.7 + (sum(map(ord, robot.id)) % 5)) % 4 < 0.12
    pygame.draw.circle(layer, (20, 30, 44), (cx, cy), r + 2)
    if on and not blink:
        P.glow(layer, (cx, cy), r * 3, theme.CYAN, 60)
        pygame.draw.circle(layer, theme.WHITE, (cx, cy), r)
        pygame.draw.circle(layer, theme.CYAN, (cx + 2 * robot.facing, cy), r // 2 + 1)
    else:
        pygame.draw.line(layer, theme.MUTED, (cx - r, cy), (cx + r, cy), 2)


def _wheels(layer, cx, cy, w=26):
    for dx in (-w // 2, w // 2 - 8):
        pygame.draw.rect(layer, (30, 36, 48), (cx + dx, cy + 12, 8, 8), border_radius=3)


def _bip(layer, cx, cy, robot, t):
    body = theme.CYAN if robot.active else (90, 110, 130)
    _wheels(layer, cx, cy)
    pygame.draw.circle(layer, (20, 90, 110), (cx, cy), 17)
    pygame.draw.circle(layer, body, (cx, cy - 1), 15)
    # tay gắp
    side = robot.facing
    pygame.draw.line(layer, (200, 220, 235), (cx + 13 * side, cy + 2), (cx + 22 * side, cy + 6), 3)
    pygame.draw.line(layer, (200, 220, 235), (cx + 22 * side, cy + 6), (cx + 26 * side, cy + 2), 2)
    pygame.draw.line(layer, (200, 220, 235), (cx + 22 * side, cy + 6), (cx + 26 * side, cy + 10), 2)
    _eye(layer, cx, cy - 3, robot, t)


def _kep(layer, cx, cy, robot, t):
    _wheels(layer, cx, cy, 30)
    rect = pygame.Rect(cx - 16, cy - 15, 32, 28)
    pygame.draw.rect(layer, (70, 84, 104), rect.move(0, 2), border_radius=5)
    pygame.draw.rect(layer, KEP_BODY, rect, border_radius=5)
    pygame.draw.line(layer, (200, 210, 220), (cx + 8, cy - 15), (cx + 12, cy - 28), 2)
    pygame.draw.circle(layer, theme.RED if int(t * 2) % 2 else theme.AMBER, (cx + 12, cy - 29), 3)
    pygame.draw.rect(layer, theme.AMBER, (cx - 6, cy + 2, 12, 8), border_radius=2)  # thẻ cấp 2
    P.text(layer, "2", (cx, cy + 6), 8, (40, 30, 0), "Bold", "center")
    _eye(layer, cx - 4, cy - 6, robot, t, 6)


def _repair(layer, cx, cy, robot, t):
    _wheels(layer, cx, cy, 34)
    rect = pygame.Rect(cx - 18, cy - 10, 36, 24)
    pygame.draw.rect(layer, (160, 80, 30), rect.move(0, 3), border_radius=4)
    pygame.draw.rect(layer, REPAIR, rect, border_radius=4)
    pygame.draw.rect(layer, (40, 40, 40), (cx - 18, cy + 6, 36, 4))  # vạch cảnh báo
    for i in range(0, 36, 8):
        pygame.draw.line(layer, theme.AMBER, (cx - 18 + i, cy + 10), (cx - 14 + i, cy + 6), 2)
    # cờ lê
    angle = math.sin(t * 12) * 0.8 if robot.anim == "repair" else 0.3
    hx, hy = cx + 16 * robot.facing, cy - 6
    ex, ey = hx + math.cos(angle - 1.2) * 16 * robot.facing, hy + math.sin(angle - 1.2) * 16
    pygame.draw.line(layer, (210, 215, 225), (hx, hy), (ex, ey), 4)
    pygame.draw.circle(layer, (210, 215, 225), (int(ex), int(ey)), 5, 2)
    _eye(layer, cx - 4, cy - 2, robot, t, 5)


def _rescue(layer, cx, cy, robot, t):
    _wheels(layer, cx, cy, 26)
    rect = pygame.Rect(cx - 13, cy - 22, 26, 36)
    pygame.draw.rect(layer, (170, 180, 195), rect.move(0, 2), border_radius=8)
    pygame.draw.rect(layer, RESCUE, rect, border_radius=8)
    pygame.draw.rect(layer, theme.RED, (cx - 3, cy - 2, 6, 14))
    pygame.draw.rect(layer, theme.RED, (cx - 7, cy + 2, 14, 6))
    beam = (math.sin(t * 8) + 1) / 2
    pygame.draw.circle(layer, (int(120 + 135 * beam), 60, 70), (cx, cy - 25), 4)
    _eye(layer, cx, cy - 12, robot, t, 5)


def draw_person(surface, pos, t, state):
    """Người cần cứu: ngồi chờ (có dấu !), đi theo robot, hoặc đã an toàn."""
    x, y = pos
    bob = math.sin(t * 7) * 1.5 if state == "following" else 0
    P.shadow(surface, (x, y + 10), 7, 3, 70)
    pygame.draw.rect(surface, (90, 130, 200), (x - 5, y - 4 + bob, 10, 13), border_radius=3)
    pygame.draw.circle(surface, (240, 200, 170), (int(x), int(y - 9 + bob)), 5)
    pygame.draw.arc(surface, theme.AMBER, (x - 6, y - 16 + bob, 12, 10), 0, math.pi, 3)
    if state == "waiting":
        P.tag(surface, "!", (x, y - 24), theme.AMBER, 11)
    elif state == "safe":
        P.check_mark(surface, (x + 9, y - 16), 4)
