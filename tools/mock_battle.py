"""Battle mode mock, calibrated on an in-game frame (user footage 2026-10-20, 2560x1080, Ultrawide Fix 1.1: the 2D
layer is the centred 1920x1080 picture, the 3D highways keep their 16:9 size).

From the frame (canvas units, 1280x720): the DE puts the 2-player highways at +-x_offset_p2 (~232), each ~490 wide at
the bottom, so with the GH5 highway they touch in the middle; P1's outer rail runs (320,395) -> (170,700). The v6 battle
layout landed up-left of its targets by a quarter of each element's size: hud_2d `just` is -1..1 with 0 = centre (we
gave 0.5), so every element is shifted by (0.5 * size / 2); the rail it was placed against was an estimate.

The mock: the stock frame with our battle HUD removed (inpainted), the highways moved apart by SEP each (x_offset_p2 +
SEP), and the HUD drawn around the measured rail: slot rings stacked just outside it (small at the top, big at the
bottom), the health arc fully inside the 16:9 picture in the corner below them, a held power-up in the big slot, empty
slots dark (no grey stripes), the attack alert card above the victim's highway (the DE's place).

usage: python tools/mock_battle.py <frame.png (2560x1080 or 1280x720)> <out.jpg> [SEP]
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths, wor_battle  # noqa: E402

SEP = 30.0                       # extra x_offset_p2 (each highway moves this far outwards)
# measured on the frame (P1; P2 mirrors around x 640)
HW_P1 = [(312, 390), (508, 390), (662, 720), (150, 720)]        # P1 highway incl. rails: top-left, top-right, bottom
RAIL_TOP, RAIL_BOT = (320.0, 395.0), (170.0, 700.0)              # P1 outer rail (stock spacing)
HUD_P1_BOX = (0, 410, 205, 620)                                  # where our v6 HUD drew (to clean)
# v6's elements as drawn in the frame (to clean): rings (centre, radius), the arc's box, its needle line
V6_RINGS = [((98, 520), 46), ((147, 482), 32), ((174, 447), 24)]
V6_ARC_BOX = (-20, 538, 92, 606)
V6_NEEDLE = ((70, 598), (90, 560))
CARD_BOX = (795, 280, 948, 364)                                  # the attack alert card over P2 ("MEDIUM")
ICON = os.path.join(paths.DE_EXTRACT, 'gh3wor', 'global_png', 'icon_attack_difficulty.png')


def rail_x(y, sep=SEP):
    (x0, y0), (x1, y1) = RAIL_TOP, RAIL_BOT
    return x0 - sep + (x1 - x0) * (y - y0) / (y1 - y0)


def layout(sep=SEP):
    """P1 screen positions: {slot: (centre, drawn size)}, arc pivot and size."""
    out = {}
    for key, y, gap in (('small', 452.0, 14.0), ('mid', 498.0, 14.0), ('big', 558.0, 14.0)):
        size = wor_battle.ring_canvas(key) * {'small': 1.1, 'mid': 1.0, 'big': 0.9}[key]
        r_out = wor_battle.RINGS[key][3] * size / wor_battle.ring_canvas(key)
        out[key] = ((rail_x(y, sep) - r_out - gap, y), size)
    out['arc'] = ((72.0, 690.0), 150.0)
    return out


def _mirror_pt(p):
    return (1280.0 - p[0], p[1])


def _paste(img, im, centre):
    img.alpha_composite(im, (int(round(centre[0] - im.width / 2)), int(round(centre[1] - im.height / 2))))


def build(frame, sep=SEP, health=(1.3, 0.5)):
    import cv2
    im = Image.open(frame).convert('RGB')
    if im.size != (1280, 720):
        w, h = im.size
        cw = round(h * 16 / 9)
        im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).resize((1280, 720), Image.LANCZOS)
    base = np.array(im)
    card = im.crop(CARD_BOX)
    # 1. clean: our v6 HUD (both sides), the card, and both highways (pasted back moved)
    mask = Image.new('L', (1280, 720), 0)
    d = ImageDraw.Draw(mask)
    for mir in (False, True):
        f = (lambda p: _mirror_pt(p)) if mir else (lambda p: p)
        for c, r in V6_RINGS:
            cx, cy = f(c)
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
        a0, b0, a1, b1 = V6_ARC_BOX
        if mir:
            a0, a1 = 1280 - a1, 1280 - a0
        d.ellipse((a0, b0, a1, b1 + 60), fill=255)
        d.line([f(V6_NEEDLE[0]), f(V6_NEEDLE[1])], fill=255, width=10)
    d.line([(1180, 568), (1206, 606)], fill=255, width=14)          # P2's needle (it leans the other way)
    d.ellipse((1036, 416, 1182, 572), fill=255)                       # P2's v6 rings (not an exact mirror of P1's)
    d.rectangle(CARD_BOX, fill=255)
    hw2 = [_mirror_pt(p) for p in HW_P1]
    d.polygon(HW_P1, fill=255)
    d.polygon(hw2, fill=255)
    m = np.array(mask.filter(ImageFilter.MaxFilter(5)))
    clean = cv2.inpaint(base, m, 9, cv2.INPAINT_TELEA)
    out = Image.fromarray(clean).convert('RGBA')
    # the card alone: where the frame differs from the cleaned background
    diff = np.abs(base.astype(int) - clean.astype(int)).sum(axis=2)
    cmask = Image.fromarray(((diff > 60) * 255).astype(np.uint8)).crop(CARD_BOX).filter(ImageFilter.MaxFilter(3))
    card = card.convert('RGBA')
    card.putalpha(cmask)
    # 2. highways moved apart
    for poly, dx in ((HW_P1, -sep), (hw2, sep)):
        hm = Image.new('L', (1280, 720), 0)
        ImageDraw.Draw(hm).polygon(poly, fill=255)
        hm = hm.filter(ImageFilter.GaussianBlur(1.2))
        lay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        src = im.convert('RGBA')
        src.putalpha(hm)
        lay.alpha_composite(src, (int(dx), 0)) if dx >= 0 else lay.paste(src, (int(dx), 0), src)
        out.alpha_composite(lay)
    # 3. our battle HUD
    tex = wor_battle.textures()
    lay_p1 = layout(sep)
    icon = Image.open(ICON).convert('RGBA')
    for player, hp in ((1, health[0]), (2, health[1])):
        mir = player == 2
        hud = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        for key in ('big', 'mid', 'small'):
            c, size = lay_p1[key]
            if mir:
                c = _mirror_pt(c)
            r_in = wor_battle.RINGS[key][2] * size / wor_battle.ring_canvas(key)
            # empty slot: dark glass instead of the grey striped default icon
            disc = Image.new('RGBA', (int(2 * r_in) + 2,) * 2, (0, 0, 0, 0))
            ImageDraw.Draw(disc).ellipse((1, 1, disc.width - 2, disc.height - 2), fill=(10, 10, 14, 200))
            _paste(hud, disc, c)
            if player == 1 and key == 'big':       # a held power-up sits in the big slot
                _paste(hud, icon.resize((int(r_in * 1.8),) * 2, Image.LANCZOS), c)
            ring = tex[wor_battle.RING_TEX[key]].resize((int(size),) * 2, Image.LANCZOS)
            _paste(hud, ring.transpose(Image.FLIP_LEFT_RIGHT) if mir else ring, c)
        # health arc: base, the lit colour for this health, frame, needle (0 = left, 2 = right)
        pivot, asz = lay_p1['arc']
        if mir:
            pivot = _mirror_pt(pivot)
        k = asz / 256.0
        tl = (pivot[0] - k * wor_battle.ARC_PIVOT_TEX[0], pivot[1] - k * wor_battle.ARC_PIVOT_TEX[1])
        colour = 'green' if hp > 1.333 else 'yellow' if hp > 0.667 else 'red'
        for name in ('off', colour, 'frame'):
            a = tex[wor_battle.ARC_TEX[name]].resize((int(asz),) * 2, Image.LANCZOS)
            hud.alpha_composite(a, (int(round(tl[0])), int(round(tl[1]))))
        nd = tex[wor_battle.ARC_TEX['needle']].resize((max(1, int(32 * k)), int(256 * k)), Image.LANCZOS)
        ang = -90.0 + 90.0 * hp                     # degrees from vertical
        pad = Image.new('RGBA', (nd.height * 2, nd.height * 2), (0, 0, 0, 0))
        pad.alpha_composite(nd, (pad.width // 2 - nd.width // 2, pad.height // 2 - nd.height // 2))
        pad = pad.rotate(-ang, resample=Image.BICUBIC)
        hud.alpha_composite(pad, (int(pivot[0] - pad.width / 2), int(pivot[1] - pad.height / 2)))
        out.alpha_composite(hud)
    # 4. the attack alert card over the victim (P2) highway, moved with it
    _paste(out, card, ((CARD_BOX[0] + CARD_BOX[2]) / 2 + sep, (CARD_BOX[1] + CARD_BOX[3]) / 2))
    return im.convert('RGB'), out.convert('RGB')


def main():
    frame, dst = sys.argv[1], sys.argv[2]
    sep = float(sys.argv[3]) if len(sys.argv) > 3 else SEP
    before, after = build(frame, sep)
    sheet = Image.new('RGB', (1280, 1440 + 60), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), 'NOW (in game, 2026-10-20)', fill=(255, 220, 120))
    sheet.paste(before, (0, 26))
    d.text((10, 752), f'MOCK: highways {sep:.0f} further apart each, HUD placed on the measured rail', fill=(255, 220, 120))
    sheet.paste(after, (0, 772))
    sheet.save(dst, quality=90)
    print('wrote', dst)


if __name__ == '__main__':
    main()
