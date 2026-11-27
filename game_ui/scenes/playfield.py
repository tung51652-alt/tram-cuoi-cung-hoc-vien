"""Sân chơi: hậu cảnh → hành lang/địa điểm → vật thể/nhân vật → hiệu ứng/tiền cảnh."""

import pygame

from game_ui import theme
from game_ui.drawing import primitives as P
from game_ui.drawing import robots as R
from game_ui.drawing import world as W


def render(surface, player, t):
    """Vẽ toàn bộ sân chơi (kích thước theme.PLAYFIELD) lên `surface`."""
    W.background(surface, player.level, t)
    W.corridors(surface, player)
    W.locations(surface, player, t)
    for task in player.tasks.values():
        if task.get("kind") == "rescue":
            state = {"open": "waiting", "in_progress": "following", "done": "safe"}.get(task.get("status"), "waiting")
            R.draw_person(surface, task.get("person_xy", (430, 320)), t, state)
    # Robot đứng cùng chỗ được dàn ngang để không che nhau (chỉ lệch khi vẽ).
    groups = {}
    for robot in player.robots.values():
        groups.setdefault((round(robot.x), round(robot.y)), []).append(robot)
    for robot in sorted(player.robots.values(), key=lambda r: r.y):
        group = groups[(round(robot.x), round(robot.y))]
        shift = (group.index(robot) - (len(group) - 1) / 2) * 54 if len(group) > 1 else 0
        robot.x += shift
        R.draw_robot(surface, robot, t)
        robot.x -= shift
    W.packages(surface, player)
    W.smoke(surface, player, t)
    bounds = surface.get_rect().inflate(-12, -12)
    for bubble in player.bubbles:
        robot = player.robots.get(bubble.actor)
        if robot:
            P.bubble(surface, (robot.x, robot.y - 42), bubble.text, bubble.kind, bounds=bounds)
    goals = list(player.goals.values())
    if player.done and goals and all(g.get("done") for g in goals):
        _power_restored(surface, t)
    if player.banner:
        _banner(surface, *player.banner)


def _power_restored(surface, t):
    """Cảnh kết thúc: điện được bật lại khi mọi mục tiêu của case đã đạt."""
    light = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    light.fill((255, 236, 170, 26))
    surface.blit(light, (0, 0))
    for x in range(60, surface.get_width(), 120):
        P.glow(surface, (x, 14), 40, (255, 230, 150), 90)
        pygame.draw.circle(surface, (255, 240, 190), (x, 14), 6)
    P.tag(surface, "ĐIỆN ĐÃ ĐƯỢC KHÔI PHỤC", (surface.get_width() // 2, 34), theme.GREEN, 15)


def _banner(surface, kind, message):
    color = {"error": theme.RED, "timeout": theme.AMBER, "done": theme.GREEN, "todo": theme.AMBER}.get(kind, theme.CYAN)
    lines = P.wrap(message, 14, surface.get_width() - 80, "SemiBold")[:3]
    rect = pygame.Rect(20, surface.get_height() - 30 - 22 * len(lines), surface.get_width() - 40, 22 * len(lines) + 14)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*theme.BG, 225), layer.get_rect(), border_radius=10)
    pygame.draw.rect(layer, color, layer.get_rect(), 2, border_radius=10)
    surface.blit(layer, rect)
    for i, line in enumerate(lines):
        P.text(surface, line, (rect.left + 16, rect.top + 7 + i * 22), 14, color, "SemiBold")
