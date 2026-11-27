"""Ghép một khung hình logic 1280x720: thanh trên, sân chơi, panel, thanh dưới."""

import pygame

from game_ui import theme
from game_ui.components import panel
from game_ui.drawing import primitives as P
from game_ui.scenes import playfield


def compose(screen, field, player, t, mode="public", speed=1.0, paused=False, footer=None, reduced_motion=False,
            panel_scroll=0, draw_bars=True, panel_rect=None):
    # Ít hiệu ứng: đóng băng các chuyển động trang trí (đèn nhấp nháy, nhún), hoạt cảnh chính vẫn chạy.
    playfield.render(field, player, 0.0 if reduced_motion else t)
    screen.fill(theme.BG)
    screen.blit(field, theme.PLAYFIELD)
    step, total = player.progress
    status = "Đang phát" if not player.done else "Đã phát xong"
    panel.side_panel(screen, panel_rect or theme.PANEL, player, panel_scroll)
    if not draw_bars:
        return
    panel.top_bar(screen, theme.TOP_BAR, player.title or "", mode, f"{status} {step}/{total}", speed, paused)
    pygame.draw.rect(screen, theme.PANEL_BG, theme.BOTTOM_BAR)
    pygame.draw.line(screen, theme.PANEL_LINE, theme.BOTTOM_BAR.topleft, theme.BOTTOM_BAR.topright, 2)
    P.text(screen, footer or "Space: tạm dừng · 1/2/3: tốc độ 0.5x/1x/2x · R: phát lại · Esc: thoát",
           (theme.BOTTOM_BAR.left + 14, theme.BOTTOM_BAR.centery), 13, theme.MUTED, anchor="midleft")
