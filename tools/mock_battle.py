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

Since the build (2026-10-21) the mock draws the built layout itself: every geometry and texture comes from
tools/wor_battle.py (the tubes baked from our 1-player HUD, each element at its layout position, P2 = P1 translated,
the needle where plugin 1.33 puts it), so the mock and the game can't drift apart. wor_card() keeps the v8 alert card
idea for the card design still to be discussed.

usage: python tools/mock_battle.py <frame.png (2560x1080 or 1280x720)> <out.jpg> [SEP]
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock_fail_popup as fonts, paths, preview_hud, wor_1g, wor_battle  # noqa: E402

SEP = wor_battle.SEP
# measured on the frame (P1, stock spacing; P2 mirrors around x 640); the rails etc. live in tools/wor_battle.py
HW_P1 = [(312, 390), (508, 390), (662, 720), (150, 720)]        # P1 highway incl. rails, for cutting it out
RAIL_L, RAIL_R = wor_battle.RAIL_L, wor_battle.RAIL_R
STRIKE_2P, TOP_2P = wor_battle.STRIKE_2P, wor_battle.TOP_2P
CARD_BOX = (795, 266, 950, 366)                                  # the attack card over P2 ("MEDIUM")
# v6's elements as drawn in the frame (to clean)
V6_RINGS = [((98, 520), 46), ((147, 482), 32), ((174, 447), 24)]
V6_ARC_BOX = (-20, 538, 92, 606)
V6_NEEDLE = ((70, 598), (90, 560))
ICON = os.path.join(paths.DE_EXTRACT, 'gh3wor', 'global_png', 'icon_attack_difficulty.png')
WOR_UI = os.path.join(paths.WOR_EXTRACT, 'ui_shared_png')
_line_x = wor_battle._line_x


def _mirror_pt(p):
    return (1280.0 - p[0], p[1])


def _paste(img, im, centre):
    img.alpha_composite(im, (int(round(centre[0] - im.width / 2)), int(round(centre[1] - im.height / 2))))


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


def needle_at(health):
    """Where the plugin puts the battle needle (screen, P1): the WoR LED stops, linear between them."""
    st = wor_battle.needle_stops()
    hs = wor_battle.HEALTH_STOPS
    i = min(2, int(health / hs[1]))
    t = min(1.0, max(0.0, (health - hs[i]) / (hs[i + 1] - hs[i])))
    return (st[i][0] + (st[i + 1][0] - st[i][0]) * t, st[i][1] + (st[i + 1][1] - st[i][1]) * t)


def build(frame, sep=SEP, health=(1.6, 0.5), cards=('icon', None)):
    """The frame cleaned and the highways moved apart, with the built battle layout drawn like the game would: every
    texture of tools/wor_battle.py at its layout position and size (P2 = P1 translated), the needle where the plugin
    puts it, a card (64 px art at the big slot's card size) in P1's big slot."""
    im, out = clean_and_move(frame, sep)
    tex = wor_battle.textures()
    icon = Image.open(ICON).convert('RGBA')
    tc, (tw, th) = wor_battle.tube_box()
    tube = (int(round(tw / wor_battle.SS)), int(round(th / wor_battle.SS)))
    big_card, _ = wor_battle.card_sizes()
    dx = wor_battle.p2_dx(sep)
    for player, hp in ((1, health[0]), (2, health[1])):
        hud = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        led = 'red' if hp < 2 / 3 else 'yellow' if hp < 4 / 3 else 'green'
        for k in ('body', led):
            _paste(hud, tex[wor_battle.TUBE_TEX[k]].resize(tube, Image.LANCZOS), tc)
        n = tex[wor_battle.NEEDLE_TEX]
        nd = int(round(n.width / wor_battle.SS))
        _paste(hud, n.resize((nd, nd), Image.LANCZOS), needle_at(hp))
        for key, c, size, r_in in wor_battle.slots_on_tube(sep):
            d = int(round(2 * r_in + 3))
            disc = tex[wor_battle.DISC_TEX].resize((d, d), Image.LANCZOS)
            a = np.array(disc).astype(np.float32)
            a[..., :3] = np.array(wor_battle.DISC_RGBA[:3], np.float32)
            a[..., 3] *= wor_battle.DISC_RGBA[3] / 255.0
            _paste(hud, Image.fromarray(a.astype(np.uint8)), c)
            if player == 1 and key == 'big' and cards[0]:
                k = int(round(big_card))
                _paste(hud, icon.resize((k, k), Image.LANCZOS), c)
            _paste(hud, tex[wor_battle.RING_TEX[key]].resize((int(size),) * 2, Image.LANCZOS), c)
        if player == 2:
            shifted = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
            shifted.paste(hud, (int(round(dx)), 0), hud)
            hud = shifted
        out.alpha_composite(hud)
    return im, out.convert('RGB')


def main():
    frame, dst = sys.argv[1], sys.argv[2]
    sep = float(sys.argv[3]) if len(sys.argv) > 3 else SEP
    before, after = build(frame, sep)
    sheet = Image.new('RGB', (1280, 1440 + 60), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), 'NOW (in game, 2026-10-20)', fill=(255, 220, 120))
    sheet.paste(before, (0, 26))
    d.text((10, 752), f'BUILD PREVIEW (tools/wor_battle.py layout): highways {sep:.0f} further apart each; rock tube left '
                      'rail, attack slots where the SP tube goes; alert card stock (not drawn)', fill=(255, 220, 120))
    sheet.paste(after, (0, 772))
    sheet.save(dst, quality=90)
    print('wrote', dst)


if __name__ == '__main__':
    main()
