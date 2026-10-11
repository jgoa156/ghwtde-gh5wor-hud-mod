"""Mock of the WoR "song ended" / "song failed" box (the DE's dialog_box_fail_wtde restyled like our WoR popups):
our dialog frame (WoR's dialog_bg + mirror), WoR title / text fonts, the brush bar behind the selected option.

usage: python tools/mock_fail_popup.py <background screenshot> <out.png>
"""
import os, sys
from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_render  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PAK = os.path.join(ROOT, 'build', 'pak_src', 'wor_hud_ui')
PREVIEW = os.path.join(ROOT, 'build', 'preview')
TITLE, TEXT = os.path.join(PAK, 'WoR_HUD_title_a1.fnt.xen'), os.path.join(PAK, 'WoR_HUD_text_a1.fnt.xen')
GOLD, WHITE, RED, CREAM, BROWN = (238, 190, 92), (255, 255, 255), (232, 36, 44), (232, 214, 170), (60, 34, 14)


def _strip(font, s):
    """Glyphs laid out on a common baseline (bottoms aligned); spaces only advance."""
    b, glyphs, tex = font_render.load(font)
    tw, th = tex.size
    parts, x, cap = [], 0, 0
    for ch in s:
        g = glyphs[font_render.glyph_index(b, ch)]
        if ch == ' ':
            x += int(g[4] * 0.45)
            continue
        u0, v0, u1, v1, w = g[:5]
        crop = tex.crop((round(u0 * tw), round(v0 * th), round(u1 * tw), round(v1 * th)))
        parts.append((x, crop))
        x += max(int(w), crop.size[0]) - 4
        cap = max(cap, crop.size[1])
    out = Image.new('RGBA', (max(x + 4, 1), cap), (0, 0, 0, 0))
    for px, c in parts:
        out.alpha_composite(c, (px, cap - c.size[1]))
    return out


def text(font, s, height, colour, shadow=False):
    im = _strip(font, s)
    im = im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)
    r, g, b, a = im.split()
    out = Image.merge('RGBA', [c.point(lambda v, m=m: v * m // 255) for c, m in zip((r, g, b), colour)] + [a])
    if shadow:
        sh = Image.new('RGBA', (out.width + 4, out.height + 4), (0, 0, 0, 0))
        black = Image.merge('RGBA', [a.point(lambda v: 0)] * 3 + [a])
        sh.alpha_composite(black, (3, 4))
        sh.alpha_composite(out, (0, 0))
        out = sh
    return out


def centre(img, im, cx, cy):
    img.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def row(img, parts, cx, cy, gap=10):
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    x = cx - w / 2
    for p in parts:
        img.alpha_composite(p, (round(x), round(cy - p.height / 2)))
        x += p.width + gap


def main():
    src, out = sys.argv[1], sys.argv[2]
    shot = Image.open(src).convert('RGB')
    w, h = shot.size
    cw = round(h * 16 / 9)
    bg = shot.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).resize((1280, 720), Image.LANCZOS)
    img = ImageEnhance.Brightness(bg).enhance(0.5).convert('RGBA')
    frame = Image.open(os.path.join(PREVIEW, 'WoR_HUD_dialog_frame.png')).convert('RGBA').resize((980, 534), Image.LANCZOS)
    img.alpha_composite(frame, (150, 99))
    centre(img, text(TITLE, 'SONG ENDED', 40, BROWN), 640, 168)                      # banner, no shadow
    centre(img, text(TITLE, 'Freak On a Leash', 50, RED, shadow=True), 640, 262)     # song title (title case)
    row(img, [text(TEXT, 'Completed', 30, CREAM), text(TITLE, '22%', 40, GOLD, True), text(TEXT, 'on', 30, CREAM),
              text(TITLE, 'Expert', 40, GOLD, True)], 640, 318, gap=12)
    bar = Image.open(os.path.join(PREVIEW, 'WoR_HUD_light_bar.png')).convert('RGBA').resize((330, 42), Image.LANCZOS)
    for k, (label, focus) in enumerate((('Retry Song', True), ('New Song', False), ('Main Menu', False))):
        y = 425 + 42 * k
        if focus:
            centre(img, bar, 640, y)
        centre(img, text(TITLE, label, 34, WHITE if focus else GOLD), 640, y)
    img.convert('RGB').save(out)
    print('wrote', out)


if __name__ == '__main__':
    main()
