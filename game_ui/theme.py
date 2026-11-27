"""Bảng màu, kích thước logic và font tiếng Việt đóng gói."""

from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent.parent / "assets"

LOGICAL_SIZE = (1280, 720)
PLAYFIELD = pygame.Rect(0, 40, 860, 640)
PANEL = pygame.Rect(860, 40, 420, 640)
TOP_BAR = pygame.Rect(0, 0, 1280, 40)
BOTTOM_BAR = pygame.Rect(0, 680, 1280, 40)

BG = (14, 23, 38)
FLOOR = (27, 42, 63)
FLOOR_ALT = (34, 52, 77)
WALL = (58, 76, 102)
GRID = (40, 58, 84)
CYAN = (58, 214, 232)
AMBER = (255, 176, 32)
RED = (255, 77, 94)
GREEN = (74, 222, 128)
TEXT = (230, 237, 245)
MUTED = (150, 166, 188)
PANEL_BG = (19, 30, 48)
PANEL_LINE = (44, 64, 92)
WHITE = (245, 248, 252)
SHADOW = (6, 10, 18)

LEVEL_TINT = {0: (40, 28, 40), 1: (24, 36, 58), 2: (34, 40, 40), 3: (40, 32, 30), "practice": (26, 40, 52)}
CATEGORY_COLOR = {"medical": (240, 98, 120), "science": (130, 140, 255), "power": (255, 196, 60),
                  "life": (80, 210, 190), "tools": (200, 150, 90)}

_cache = {}


def font(size, weight="Regular"):
    """Font Be Vietnam Pro (Regular/SemiBold/Bold). Thiếu file thì dùng font mặc định."""
    key = (size, weight)
    if key not in _cache:
        path = ASSETS / "fonts" / f"BeVietnamPro-{weight}.ttf"
        try:
            _cache[key] = pygame.font.Font(str(path), size)
        except (OSError, FileNotFoundError):
            _cache[key] = pygame.font.Font(None, size + 4)
    return _cache[key]
