"""Hàm vẽ cơ bản: bóng đổ, chữ có xuống dòng, bong bóng thoại, thanh pin."""

import math

import pygame

from game_ui import theme


def shadow(surface, center, rx, ry, alpha=90):
    layer = pygame.Surface((rx * 2 + 4, ry * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(layer, (*theme.SHADOW, alpha), layer.get_rect().inflate(-4, -4))
    surface.blit(layer, (center[0] - rx - 2, center[1] - ry - 2))


def glow(surface, center, radius, color, alpha=70):
    layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(4, 0, -1):
        pygame.draw.circle(layer, (*color, int(alpha * i / 4 / 2)), (radius, radius), int(radius * i / 4))
    surface.blit(layer, (center[0] - radius, center[1] - radius))


# Be Vietnam Pro không có các ký hiệu này: thay bằng ký tự có sẵn, biểu tượng vẽ riêng bằng icon().
GLYPH_FALLBACK = {"✓": "", "✗": "x", "✖": "x", "⚠": "!", "▶": ">", "→": "->", "○": "o"}


def clean(value):
    out = str(value)
    for bad, good in GLYPH_FALLBACK.items():
        out = out.replace(bad, good)
    return " ".join(out.split()) if out != str(value) else out


def text(surface, value, pos, size=14, color=theme.TEXT, weight="Regular", anchor="topleft"):
    image = theme.font(size, weight).render(clean(value), True, color)
    rect = image.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    surface.blit(image, rect)
    return rect


def wrap(value, size, width, weight="Regular"):
    """Chia chữ thành dòng không vượt `width` pixel; từ quá dài bị cắt theo ký tự."""
    fnt = theme.font(size, weight)
    lines, line = [], ""
    for word in clean(value).split():
        trial = f"{line} {word}".strip()
        if fnt.size(trial)[0] <= width:
            line = trial
            continue
        if line:
            lines.append(line)
        while fnt.size(word)[0] > width and len(word) > 1:
            cut = len(word)
            while cut > 1 and fnt.size(word[:cut])[0] > width:
                cut -= 1
            lines.append(word[:cut])
            word = word[cut:]
        line = word
    if line:
        lines.append(line)
    return lines or [""]


def bubble(surface, anchor, value, kind="say", max_width=230, bounds=None):
    """Bong bóng thoại phía trên `anchor`; được kẹp trong `bounds` để không tràn."""
    color = {"say": theme.WHITE, "refuse": theme.AMBER, "ok": theme.GREEN}.get(kind, theme.WHITE)
    fg = (20, 28, 40)
    pad = 26 if kind in ("refuse", "ok") else 10
    lines = wrap(value, 13, max_width - 20 - pad)[:4]
    fnt = theme.font(13)
    w = max(fnt.size(l)[0] for l in lines) + 10 + pad
    h = len(lines) * 18 + 12
    rect = pygame.Rect(0, 0, w, h)
    rect.midbottom = (int(anchor[0]), int(anchor[1]) - 10)
    if bounds is not None:
        rect.clamp_ip(bounds)
    pygame.draw.rect(surface, theme.SHADOW, rect.move(2, 3), border_radius=9)
    pygame.draw.rect(surface, color, rect, border_radius=9)
    tip_x = max(rect.left + 12, min(rect.right - 12, int(anchor[0])))
    pygame.draw.polygon(surface, color, [(tip_x - 6, rect.bottom - 1), (tip_x + 6, rect.bottom - 1),
                                         (tip_x, rect.bottom + 8)])
    if kind in ("refuse", "ok"):
        icon(surface, "warn_dark" if kind == "refuse" else "ok_dark", (rect.left + 15, rect.top + 15))
    for i, line in enumerate(lines):
        text(surface, line, (rect.left + pad, rect.top + 6 + i * 18), 13, fg)


def battery_bar(surface, center, battery, max_battery, width=38):
    """Thanh pin kèm số thật. Giá trị lạ vẫn hiện số thật và dấu ⚠."""
    x, y = int(center[0] - width / 2), int(center[1])
    pygame.draw.rect(surface, (10, 16, 26), (x - 1, y - 1, width + 2, 7), border_radius=3)
    valid = isinstance(battery, (int, float)) and not isinstance(battery, bool) and math.isfinite(battery)
    maximum = max_battery if isinstance(max_battery, (int, float)) and max_battery > 0 else 1
    frac = max(0.0, min(1.0, battery / maximum)) if valid else 0.0
    color = theme.GREEN if frac > 0.5 else theme.AMBER if frac > 0.2 else theme.RED
    if frac > 0:
        pygame.draw.rect(surface, color, (x, y, int(width * frac), 5), border_radius=2)
    label = f"{battery:g}" if valid else str(battery)
    if not valid or battery < 0 or battery > maximum:
        label = "!" + label + " (bất thường)"
    text(surface, label, (x + width + 4, y - 5), 11, theme.TEXT if valid else theme.AMBER)


def tag(surface, value, center, color=theme.CYAN, size=11):
    image = theme.font(size, "SemiBold").render(str(value), True, (12, 20, 32))
    rect = image.get_rect(center=(int(center[0]), int(center[1]))).inflate(10, 4)
    pygame.draw.rect(surface, color, rect, border_radius=6)
    surface.blit(image, image.get_rect(center=rect.center))
    return rect


def check_mark(surface, center, size=10, color=theme.GREEN):
    x, y = center
    pygame.draw.lines(surface, color, False, [(x - size, y), (x - size / 3, y + size * 0.7), (x + size, y - size * 0.7)], 4)


def icon(surface, kind, center, size=7):
    """Biểu tượng vẽ tay: ok, todo, warn, error, call (và *_dark cho nền sáng)."""
    x, y = int(center[0]), int(center[1])
    dark = kind.endswith("_dark")
    kind = kind.replace("_dark", "")
    if kind == "ok":
        color = (20, 90, 50) if dark else theme.GREEN
        pygame.draw.lines(surface, color, False, [(x - size, y), (x - size // 3, y + size * 2 // 3), (x + size, y - size * 2 // 3)], 3)
    elif kind == "todo":
        pygame.draw.circle(surface, theme.MUTED, (x, y), size - 1, 2)
    elif kind == "warn":
        color = (90, 60, 0) if dark else theme.AMBER
        pts = [(x, y - size), (x + size, y + size - 1), (x - size, y + size - 1)]
        pygame.draw.polygon(surface, color, pts, 0 if not dark else 2)
        pygame.draw.line(surface, theme.BG if not dark else color, (x, y - size // 3), (x, y + size // 3), 2)
    elif kind == "error":
        pygame.draw.line(surface, theme.RED, (x - size + 1, y - size + 1), (x + size - 1, y + size - 1), 3)
        pygame.draw.line(surface, theme.RED, (x - size + 1, y + size - 1), (x + size - 1, y - size + 1), 3)
    elif kind == "call":
        pygame.draw.polygon(surface, theme.CYAN, [(x - size // 2, y - size + 1), (x + size - 1, y), (x - size // 2, y + size - 1)])
    else:
        pygame.draw.circle(surface, theme.TEXT, (x, y), 2)
