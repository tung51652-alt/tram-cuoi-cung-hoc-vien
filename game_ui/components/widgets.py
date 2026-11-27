"""Nút bấm và hộp nội dung cuộn được (vẽ trên surface logic 1280x720)."""

import pygame

from game_ui import theme
from game_ui.drawing import primitives as P


class Button:
    def __init__(self, key, label, rect, hotkey=None, primary=False):
        self.key = key
        self.label = label
        self.rect = pygame.Rect(rect)
        self.hotkey = hotkey
        self.primary = primary
        self.active = False
        self.enabled = True
        self.dimmed = False  # vẫn bấm được nhưng hiện mờ (ví dụ màn chưa mở)

    def draw(self, surface, hover):
        if not self.enabled or self.dimmed:
            bg, fg = (30, 40, 56), (90, 104, 124)
        elif self.active:
            bg, fg = theme.CYAN, (10, 20, 30)
        elif self.primary:
            bg, fg = (34, 110, 124) if not hover else (44, 140, 156), theme.WHITE
        else:
            bg, fg = (40, 56, 80) if not hover else (54, 74, 104), theme.TEXT
        pygame.draw.rect(surface, bg, self.rect, border_radius=7)
        if hover and self.enabled:
            pygame.draw.rect(surface, theme.CYAN, self.rect, 1, border_radius=7)
        label = self.label + (f"  {self.hotkey}" if self.hotkey else "")
        size = 13
        while theme.font(size, "SemiBold").size(label)[0] > self.rect.width - 10 and size > 10:
            size -= 1
        P.text(surface, label, self.rect.center, size, fg, "SemiBold", "center")

    def hit(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


class Overlay:
    """Hộp nội dung (đề, công cụ, kết quả) có cuộn bằng bánh xe chuột/phím mũi tên."""

    def __init__(self, title, lines, accent=theme.CYAN):
        self.title = title
        self.lines = lines  # list (kind, text): h, p, code, ok, todo, warn, error, muted
        self.accent = accent
        self.scroll = 0
        self.rect = pygame.Rect(90, 70, 1100, 580)
        self.close_rect = pygame.Rect(self.rect.right - 44, self.rect.top + 10, 32, 32)
        self._rendered = None

    def _layout(self):
        width = self.rect.width - 70
        rows = []
        for kind, value in self.lines:
            size = {"h": 17, "code": 14}.get(kind, 14)
            weight = {"h": "Bold", "code": "SemiBold"}.get(kind, "Regular")
            if kind == "code":
                rows.append((kind, str(value), size, weight))
                continue
            for i, row in enumerate(P.wrap(value, size, width - (22 if kind in ("ok", "todo", "warn", "error") else 0),
                                           weight)):
                rows.append((kind if i == 0 else kind + "+", row, size, weight))
        return rows

    def handle(self, event, logical_pos):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 3)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                self.scroll += 3 if event.key == pygame.K_DOWN else 12
            elif event.key in (pygame.K_UP, pygame.K_PAGEUP):
                self.scroll = max(0, self.scroll - (3 if event.key == pygame.K_UP else 12))
            elif event.key == pygame.K_ESCAPE:
                return "close"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(logical_pos) or not self.rect.collidepoint(logical_pos):
                return "close"
        return None

    def draw(self, surface):
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((5, 8, 14, 170))
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, theme.PANEL_BG, self.rect, border_radius=14)
        pygame.draw.rect(surface, self.accent, self.rect, 2, border_radius=14)
        P.text(surface, self.title, (self.rect.left + 28, self.rect.top + 18), 20, self.accent, "Bold")
        pygame.draw.rect(surface, (50, 66, 92), self.close_rect, border_radius=8)
        P.text(surface, "x", self.close_rect.center, 18, theme.TEXT, "Bold", "center")
        area = pygame.Rect(self.rect.left + 28, self.rect.top + 60, self.rect.width - 56, self.rect.height - 84)
        if self._rendered is None:
            self._rendered = self._layout()
        rows = self._rendered
        per_row = 22
        visible = area.height // per_row
        self.scroll = max(0, min(self.scroll, max(0, len(rows) - visible)))
        clip = surface.get_clip()
        surface.set_clip(area)
        y = area.top
        for kind, value, size, weight in rows[self.scroll:self.scroll + visible]:
            base = kind.rstrip("+")
            x = area.left + (22 if base in ("ok", "todo", "warn", "error") else 0)
            color = {"h": theme.TEXT, "code": theme.CYAN, "ok": theme.GREEN, "todo": theme.TEXT, "warn": theme.AMBER,
                     "error": theme.RED, "muted": theme.MUTED}.get(base, theme.TEXT)
            if base == "h":
                y += 4
            if not kind.endswith("+") and base in ("ok", "todo", "warn", "error"):
                P.icon(surface, base, (area.left + 8, y + 10), 6)
            if base == "code":
                pygame.draw.rect(surface, (12, 20, 32), (area.left, y, area.width, per_row))
                x += 10
            P.text(surface, value, (x, y + 1), size, color, weight)
            y += per_row
        surface.set_clip(clip)
        if len(rows) > visible:
            bar_h = max(30, int(area.height * visible / len(rows)))
            bar_y = area.top + int((area.height - bar_h) * self.scroll / max(1, len(rows) - visible))
            pygame.draw.rect(surface, (60, 80, 110), (self.rect.right - 16, bar_y, 6, bar_h), border_radius=3)
            P.text(surface, "Cuộn chuột hoặc phím mũi tên để xem thêm", (self.rect.centerx, self.rect.bottom - 14),
                   12, theme.MUTED, anchor="center")
