"""Battle mode mock, calibrated on an in-game frame (user footage 2026-10-20, 2560x1080, Ultrawide Fix 1.1: the 2D
layer is the centred 1920x1080 picture, the 3D highways keep their 16:9 size).

From the frame (canvas units, 1280x720): the DE puts the 2-player highways at +-x_offset_p2 (~232), each ~490 wide at
the bottom, so with the GH5 highway they touch in the middle; P1's rails run (320,395) -> (170,700) and (500,395) ->
(652,700), strikeline y ~633. The v6 battle layout landed up-left of its targets by a quarter of each element's size:
hud_2d `just` is -1..1 with 0 = centre (we gave 0.5); and its rail was an estimate (mock v7, docs/mocks).

v8 (user 2026-10-20): every battle highway gets the main theme's HUD tubes glued to it, as in 1-player: the rock
meter (WoR tube + LEDs + sliding needle) on the left rail, and the three attack slots where the SP tube goes (right
rail), about the SP tube's length, overlapping a little like the DE's own slot frame. The highways move apart by SEP
each (x_offset_p2 + SEP). The attack card stays above the victim's highway, reskinned after WoR's quickplay challenge
alert (uidesc_quickplay_challenge_alert): the attack icon in WoR's round record frame (meter_challenge_frame) on the
end of its black glass plate (HUD_revive_meter_back / _frame) carrying the attack's name.

The tubes come from our 1-player HUD (tools/preview_hud.py, game calibration), each mapped onto the battle highway by
the affine that takes three points of the 1-player rails (tube bottom / top on its rail, and the other rail) to the
same points of the battle highway (same fraction of the highway height above the strikeline).

usage: python tools/mock_battle.py <frame.png (2560x1080 or 1280x720)> <out.jpg> [SEP]
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock_fail_popup as fonts, paths, preview_hud, wor_1g, wor_battle  # noqa: E402

SEP = 30.0                       # extra x_offset_p2 (each highway moves this far outwards)
# measured on the frame (P1, stock spacing; P2 mirrors around x 640)
HW_P1 = [(312, 390), (508, 390), (662, 720), (150, 720)]        # P1 highway incl. rails, for cutting it out
RAIL_L = ((320.0, 395.0), (170.0, 700.0))                       # P1 left / right rail lines (top, bottom)
RAIL_R = ((500.0, 395.0), (652.0, 700.0))
STRIKE_2P, TOP_2P = 633.0, 393.0                                 # strikeline / top of the battle highways
STRIKE_1P, TOP_1P = 638.0, 300.0                                 # the 1-player highway (tools/mock_base.py)
CARD_BOX = (795, 266, 950, 366)                                  # the attack card over P2 ("MEDIUM")
# v6's elements as drawn in the frame (to clean)
V6_RINGS = [((98, 520), 46), ((147, 482), 32), ((174, 447), 24)]
V6_ARC_BOX = (-20, 538, 92, 606)
V6_NEEDLE = ((70, 598), (90, 560))
ICON = os.path.join(paths.DE_EXTRACT, 'gh3wor', 'global_png', 'icon_attack_difficulty.png')
WOR_UI = os.path.join(paths.WOR_EXTRACT, 'ui_shared_png')
SLOT_OVERLAP = 0.12              # rings overlap along the tube (the DE's slot frame overlaps them)


def _line_x(line, y):
    (x0, y0), (x1, y1) = line
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _mirror_pt(p):
    return (1280.0 - p[0], p[1])


def _paste(img, im, centre):
    img.alpha_composite(im, (int(round(centre[0] - im.width / 2)), int(round(centre[1] - im.height / 2))))


def _y2p(y1p):
    """Same fraction of the highway's height above its strikeline."""
    f = (STRIKE_1P - y1p) / (STRIKE_1P - TOP_1P)
    return STRIKE_2P - f * (STRIKE_2P - TOP_2P)


def _cl(y):
    a, b = wor_1g.BORDER_LINE_L
    return a + b * (710.0 - y)


def _cr(y):
    a, b = wor_1g.BORDER_LINE_R
    return a + b * (710.0 - y)


def _affine(src, dst):
    import cv2
    return cv2.getAffineTransform(np.float32(src), np.float32(dst))


def tube_maps(sep):
    """{('rock' | 'sp'): 2x3 affine} from the 1-player canvas onto P1's battle highway (moved by sep)."""
    yb, yt = wor_1g.LEFT.at(wor_1g.LED_BOTTOM)[1], wor_1g.LEFT.at(wor_1g.LED_TOP)[1]
    L = lambda y: _line_x(RAIL_L, y) - sep
    R = lambda y: _line_x(RAIL_R, y) - sep
    yb2, yt2 = _y2p(yb), _y2p(yt)
    rock = _affine([(_cl(yb), yb), (_cl(yt), yt), (_cr(yb), yb)], [(L(yb2), yb2), (L(yt2), yt2), (R(yb2), yb2)])
    sp = _affine([(_cr(yb), yb), (_cr(yt), yt), (_cl(yb), yb)], [(R(yb2), yb2), (R(yt2), yt2), (L(yb2), yb2)])
    return {'rock': rock, 'sp': sp}


def _apply(m, p):
    return (m[0, 0] * p[0] + m[0, 1] * p[1] + m[0, 2], m[1, 0] * p[0] + m[1, 1] * p[1] + m[1, 2])


def hud_layers(health=1.6):
    """The 1-player HUD's rock tube (with its needle) as an RGBA layer, the score box etc. masked out."""
    roots = preview_hud.hud_roots(game=True)
    preview_hud.GAME_TEXT['on'] = True
    lay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    preview_hud.draw(lay, roots, (0.0, 0.0), 1.0, preview_hud.state(health, 0.0, 1), additive=False)
    a, b = wor_1g.LEFT.at(wor_1g.LED_BOTTOM), wor_1g.LEFT.at(wor_1g.LED_TOP)
    v = np.subtract(b, a)
    v = v / np.hypot(*v)
    n = np.array((-v[1], v[0]))
    p0, p1 = np.array(a) - v * 45, np.array(b) + v * 30
    poly = [tuple(p0 + n * 42), tuple(p1 + n * 42), tuple(p1 - n * 42), tuple(p0 - n * 42)]
    m = Image.new('L', (1280, 720), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    rock = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    rock.paste(lay, (0, 0), Image.composite(lay.split()[3], Image.new('L', (1280, 720), 0), m))
    return rock


def _warp(layer, m):
    import cv2
    a = np.array(layer)
    w = cv2.warpAffine(a, m, (1280, 720), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    return Image.fromarray(w)


def slots_on_tube(sep):
    """[(slot, centre, ring size)] along P1's SP tube line (big at the bottom), the cluster about the tube's length."""
    m = tube_maps(sep)['sp']
    a = _apply(m, wor_1g.RIGHT.at(wor_1g.LED_BOTTOM))
    b = _apply(m, wor_1g.RIGHT.at(wor_1g.LED_TOP))
    length = float(np.hypot(b[0] - a[0], b[1] - a[1]))
    radii = {k: wor_battle.RINGS[k][3] for k in ('big', 'mid', 'small')}
    k = length / (2 * sum(radii.values()) * (1 - SLOT_OVERLAP))
    v = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    out, t = [], 0.0
    for key in ('big', 'mid', 'small'):
        r = radii[key] * k
        t += r
        out.append((key, (a[0] + v[0] * t, a[1] + v[1] * t), 2 * r * wor_battle.ring_canvas(key) / (2 * radii[key])))
        t += r * (1 - 2 * SLOT_OVERLAP)
    return out


def wor_card(name, icon):
    """The attack card after WoR's quickplay challenge alert: icon in the round record frame on a glass plate."""
    back = Image.open(os.path.join(WOR_UI, 'HUD_revive_meter_back.png')).convert('RGBA').resize((200, 50), Image.LANCZOS)
    frame = Image.open(os.path.join(WOR_UI, 'HUD_revive_meter_frame.png')).convert('RGBA').resize((200, 50), Image.LANCZOS)
    rec = Image.open(os.path.join(WOR_UI, 'meter_challenge_frame.png')).convert('RGBA').resize((70, 70), Image.LANCZOS)
    card = Image.new('RGBA', (240, 80), (0, 0, 0, 0))
    card.alpha_composite(back, (36, 15))
    card.alpha_composite(frame, (36, 15))
    t = fonts.text(fonts.TEXT, name, 24, (255, 255, 255))
    card.alpha_composite(t, (36 + 30 + (170 - t.width) // 2, 40 - t.height // 2))
    card.alpha_composite(rec, (5, 5))
    card.alpha_composite(icon.resize((44, 44), Image.LANCZOS), (18, 18))
    return card


def clean_and_move(frame, sep):
    """The frame without our v6 HUD, the card and the highways, then the highways pasted back moved apart."""
    import cv2
    im = Image.open(frame).convert('RGB')
    if im.size != (1280, 720):
        w, h = im.size
        cw = round(h * 16 / 9)
        im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h)).resize((1280, 720), Image.LANCZOS)
    base = np.array(im)
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
    d.ellipse((1026, 396, 1186, 576), fill=255)                       # P2's v6 rings (not an exact mirror of P1's)
    d.ellipse((1108, 536, 1262, 650), fill=255)                       # P2's v6 arc
    d.ellipse((-30, 536, 124, 650), fill=255)                         # P1's v6 arc
    d.rectangle(CARD_BOX, fill=255)
    hw2 = [_mirror_pt(p) for p in HW_P1]
    d.polygon(HW_P1, fill=255)
    d.polygon(hw2, fill=255)
    clean = cv2.inpaint(base, np.array(mask.filter(ImageFilter.MaxFilter(5))), 9, cv2.INPAINT_TELEA)
    out = Image.fromarray(clean).convert('RGBA')
    for poly, dx in ((HW_P1, -sep), (hw2, sep)):
        hm = Image.new('L', (1280, 720), 0)
        ImageDraw.Draw(hm).polygon(poly, fill=255)
        src = im.convert('RGBA')
        src.putalpha(hm.filter(ImageFilter.GaussianBlur(1.2)))
        lay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        lay.paste(src, (int(dx), 0), src)
        out.alpha_composite(lay)
    return im, out


def build(frame, sep=SEP, health=(1.6, 0.5)):
    im, out = clean_and_move(frame, sep)
    tex = wor_battle.textures()
    icon = Image.open(ICON).convert('RGBA')
    maps = tube_maps(sep)
    slots = slots_on_tube(sep)
    # P2's highway is P1's mirrored: the offset that moves P1's set onto P2's highway (left rail -> left rail)
    dx = (1280.0 - _line_x(RAIL_R, STRIKE_2P) + sep) - (_line_x(RAIL_L, STRIKE_2P) - sep)
    for player, hp in ((1, health[0]), (2, health[1])):
        hud = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        hud.alpha_composite(_warp(hud_layers(hp), maps['rock']))          # rock meter on the left rail
        for key, c, size in slots:                                         # slots where the SP tube goes
            r_in = wor_battle.RINGS[key][2] * size / wor_battle.ring_canvas(key)
            disc = Image.new('RGBA', (int(2 * r_in) + 2,) * 2, (0, 0, 0, 0))
            ImageDraw.Draw(disc).ellipse((1, 1, disc.width - 2, disc.height - 2), fill=(10, 10, 14, 210))
            _paste(hud, disc, c)
            if player == 1 and key == 'big':
                _paste(hud, icon.resize((int(r_in * 1.8),) * 2, Image.LANCZOS), c)
            _paste(hud, tex[wor_battle.RING_TEX[key]].resize((int(size),) * 2, Image.LANCZOS), c)
        if player == 2:
            shifted = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
            shifted.paste(hud, (int(round(dx)), 0), hud)
            hud = shifted
        out.alpha_composite(hud)
    card = wor_card('MEDIUM', icon)
    top_c = (1280 - (_line_x(RAIL_L, TOP_2P) + _line_x(RAIL_R, TOP_2P)) / 2 + sep, TOP_2P - 48)
    _paste(out, card, top_c)
    return im, out.convert('RGB')


def main():
    frame, dst = sys.argv[1], sys.argv[2]
    sep = float(sys.argv[3]) if len(sys.argv) > 3 else SEP
    before, after = build(frame, sep)
    sheet = Image.new('RGB', (1280, 1440 + 60), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), 'NOW (in game, 2026-10-20)', fill=(255, 220, 120))
    sheet.paste(before, (0, 26))
    d.text((10, 752), f'MOCK v8: highways {sep:.0f} further apart each; rock tube left rail, attack slots where the SP '
                      'tube goes; WoR alert card', fill=(255, 220, 120))
    sheet.paste(after, (0, 772))
    sheet.save(dst, quality=90)
    print('wrote', dst)


if __name__ == '__main__':
    main()
