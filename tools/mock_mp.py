"""Mocks of the 2-highway layouts (tools/wor_versus.py, tools/wor_mp.py) on frames of the user's DE clip
(Downloads\\Video Project 25.mp4): face-off (0:36) and 2-player band (2:08), with the DE's elements we replace removed
(GH3-style versus bar, "01234567" placeholder bar, per-player multipliers / streak lights / instrument icons) and the
highways moved apart like battle. Drawn from the built descs and textures (run build.py first).

usage: python tools/mock_mp.py <faceoff frame> <band frame> <out.jpg>
"""
import copy, os, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mock_battle, paths, preview_hud, wor_1g, wor_battle as B, wor_mp as M, wor_versus as V  # noqa: E402
import desc_gen  # noqa: E402

FACEOFF_REMOVE = [(360, 278, 925, 356), (555, 505, 615, 610), (1015, 505, 1075, 610)]
BAND_REMOVE = [(268, 280, 1015, 352), (548, 470, 615, 610), (1010, 470, 1080, 610)]


def clean_and_move(frame, boxes, sep=B.SEP):
    import cv2
    im = Image.open(frame).convert('RGB')
    mask = Image.new('L', (1280, 720), 0)
    d = ImageDraw.Draw(mask)
    for b in boxes:
        d.rectangle(b, fill=255)
    hw1 = mock_battle.HW_P1
    hw2 = [(1280 - x, y) for x, y in hw1]
    d.polygon(hw1, fill=255)
    d.polygon(hw2, fill=255)
    clean = cv2.inpaint(np.array(im), np.array(mask.filter(ImageFilter.MaxFilter(5))), 9, cv2.INPAINT_TELEA)
    out = Image.fromarray(clean).convert('RGBA')
    for poly, dx in ((hw1, -sep), (hw2, sep)):
        hm = Image.new('L', (1280, 720), 0)
        ImageDraw.Draw(hm).polygon(poly, fill=255)
        src = im.convert('RGBA')
        src.putalpha(hm.filter(ImageFilter.GaussianBlur(1.2)))
        lay = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        lay.paste(src, (int(dx), 0), src)
        out.alpha_composite(lay)
    return im, out


def _set(root, lid, **kw):
    def walk(e):
        if e.local_id == lid:
            for k, v in kw.items():
                setattr(e, k, v)
        for c in e.children:
            walk(c)
    walk(root)


def needle_pos(health):
    _, k = M.needle_knots()
    i = min(2, int(health / (2 / 3)))
    t = min(1.0, max(0.0, (health - i * 2 / 3) * 1.5))
    return (k[i][0] + (k[i + 1][0] - k[i][0]) * t, k[i][1] + (k[i + 1][1] - k[i][1]) * t)


def per_player(sp, health=None, mult=None):
    """[(root, vals)] of one player's pieces (P1 screen px)."""
    out = []
    root = copy.deepcopy(desc_gen.ROOTS[M.SP_NAME])
    vals = {}
    n = sp * 3
    for i in range(3):
        vals[f'glow{i}'] = {'scale': (1.0, max(0.0, min(1.0, n - i)))}
    out.append((root, vals))
    if health is not None:
        root = copy.deepcopy(desc_gen.ROOTS[M.SIDE_NAME])
        led = 'red' if health < 2 / 3 else 'yellow' if health < 4 / 3 else 'green'
        vals = {f'side_meter_{c}_ON': {'alpha': 1.0 if c == led else 0.0} for c in ('red', 'yellow', 'green')}
        vals['side_meter_needle'] = {'pos': needle_pos(health)}
        out.append((root, vals))
    if mult is not None:
        root = copy.deepcopy(desc_gen.ROOTS[M.MULT_NAME])
        vals = {'nixie': {'texture': f'WoR_HUD_mult_{mult}'}}
        for i in range(5):
            vals[f'light{i}'] = {'texture': 'WoR_HUD_light_2' if i < 3 else 'WoR_HUD_light_0'}
        out.append((root, vals))
    return out


def draw_all(img, items):
    for base, root, vals in items:
        preview_hud.draw(img, [(base, root)], (0.0, 0.0), 1.0, vals, additive=True)


def faceoff(frame):
    before, img = clean_and_move(frame, FACEOFF_REMOVE)
    root = copy.deepcopy(V.tree())
    for c in [e for e in root.children if e.local_id == 'lead_2'][0].children:
        c.hidden = True                                   # P1 leads (preview_hud doesn't multiply container alpha)
    for e in [e for e in root.children if e.local_id.startswith('score_container_')]:
        for c in e.children:
            c.hidden = True                               # team bars: alpha 0 in 2-player (same reason)
    _set(root, 'needle', rot=-22.0)
    vals = {'score_1': {'text': '45,625'}, 'score_2': {'text': '31,210'}, 
            'HUD_bb_multiplier_nixie_1': {'texture': 'WoR_HUD_vsmult_3'},
            'HUD_bb_multiplier_nixie_2': {'texture': 'WoR_HUD_vsmult_1'},
            'pscore_1': {'text': '45,625'}, 'pscore_2': {'text': '31,210'}, 'pstreak_1': {'text': '64'},
            'pstreak_2': {'text': '12'}}
    items = [((0.0, 0.0), root, vals)]
    for p, sp, mult in ((1, 0.7, 3), (2, 0.3, 1)):     # each highway keeps its streak meter (user 2026-10-21)
        base = (0.0 if p == 1 else B.p2_dx(), 0.0)
        items += [(base, r, v) for r, v in per_player(sp, None, mult)]
    draw_all(img, items)
    return before, img


def band(frame):
    before, img = clean_and_move(frame, BAND_REMOVE)
    items = []
    for p, sp, health, mult in ((1, 0.55, 1.1, 2), (2, 0.2, 0.5, 1)):
        base = (0.0 if p == 1 else B.p2_dx(), 0.0)
        items += [(base, r, v) for r, v in per_player(sp, health, mult)]
    draw_all(img, items)
    return before, img


def main():
    fo, bd, dst = sys.argv[1:4]
    wor_1g.all_descs()
    V.versus_desc()
    M.descs()
    old = preview_hud.PREVIEW
    preview_hud.PREVIEW = os.path.join(paths.REPO, 'build', 'preview')
    preview_hud.GAME_TEXT['on'] = False
    try:
        rows = [('FACE-OFF NOW (user clip 0:36)', 'FACE-OFF MOCK: WoR versus meter + placing (1st glows) + per-player WoR star '
                 'power tube; no rock meter, no messages; highways apart'),
                ('BAND NOW (user clip 2:08)', 'BAND MOCK: per-player WoR rock tube (one LED + needle), star power tube, '
                 'multiplier (no instrument icon); placeholder bar hidden; band meter unchanged')]
        pics = [faceoff(fo), band(bd)]
    finally:
        preview_hud.PREVIEW = old
    sheet = Image.new('RGB', (2560, 2 * (720 + 26)), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    for r, ((t0, t1), (a, b)) in enumerate(zip(rows, pics)):
        y = r * (720 + 26)
        d.text((10, y + 6), t0, fill=(255, 220, 120))
        d.text((1290, y + 6), t1, fill=(255, 220, 120))
        sheet.paste(a, (0, y + 26))
        sheet.paste(b.convert('RGB'), (1280, y + 26))
    sheet.save(dst, quality=88)
    print('wrote', dst)


if __name__ == '__main__':
    main()
