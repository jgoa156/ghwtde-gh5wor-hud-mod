"""Mock of the multi-highway layouts with the 1-player pieces on every highway (tools/wor_mp.py, tools/hw_geom.py), on
the 16:9 bot captures (black background): everything outside the highways (the old pieces) is blacked out, then each
highway's pieces are drawn from the built descs under that highway's map. Run build.py first.

usage: python tools/mock_rails.py <out.jpg> [health sp mult]
"""
import copy
import glob
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desc_gen, hw_geom as HG, preview_hud, wor_1g, wor_mp as M  # noqa: E402
from desc_gen import E  # noqa: E402

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tests', 'results')
CASES = [('guitar + vocals (hud_1g1v)', 'band-20261022-210425', 1),
         ('2 instruments + vocals (hud_2g1v)', 'band-20261022-205843', 2),
         ('face-off (hud_2g)', 'band-20261022-211007', 2),
         ('3 instruments + vocals (hud_3g1v)', 'band-20261022-205301', 3)]


def frame(run):
    fs = [f for f in sorted(glob.glob(os.path.join(RESULTS, run, '*.png'))) if os.path.getsize(f) > 100000]
    return Image.open(fs[len(fs) // 2]).convert('RGBA')


def _at(line, y):
    (x0, y0), (x1, y1) = line
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def highways_only(img, n):
    """The highway surfaces only (inside the DE's edges: the old pieces overlap the borders), with each border drawn
    as a flat grey band out to its measured outer edge (hw_geom.BORDER_W)."""
    s0 = HG.STRUCTS[n]
    top, pl = s0['playline'] - s0['height'], s0['playline']
    stx = 640.0 - s0['top_w'] / 2
    sbx = 640.0 - (s0['top_w'] + s0['top_w'] * s0['wof']) / 2
    mask = Image.new('L', img.size, 0)
    out = Image.new('RGBA', img.size, (0, 0, 0, 255))
    d, do = ImageDraw.Draw(mask), ImageDraw.Draw(out)
    for s in HG.shifts(n):
        edge_l = ((stx + s, top), (sbx + s, pl))
        edge_r = ((1280.0 - stx + s, top), (1280.0 - sbx + s, pl))
        ol, orr = HG.outer_border(n, s, 'left'), HG.outer_border(n, s, 'right')
        for edge, outer in ((edge_l, ol), (edge_r, orr)):
            do.polygon([(_at(edge, top), top), (_at(outer, top), top), (_at(outer, 720), 720), (_at(edge, 720), 720)],
                       fill=(92, 94, 100, 255))
        d.polygon([(_at(edge_l, top), top), (_at(edge_r, top), top), (_at(edge_r, 720), 720), (_at(edge_l, 720), 720)],
                  fill=255)
    return Image.composite(img, out, mask)


def state(n, health, sp, mult):
    v = preview_hud.state(health, sp, mult)
    _, _, stops = M.needle_anchor(n)
    seg = min(2, int(health / 0.6667))
    f = min(1.0, max(0.0, (health - seg * 0.6667) / 0.6667))
    a, b = stops[seg], stops[seg + 1]
    v['side_meter_needle'] = {'pos': (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)}
    return v


def roots(n):
    out = []
    g1 = (wor_1g.G1[0] + M.G_CAL[0], wor_1g.G1[1] + M.G_CAL[1])
    for shift in HG.shifts(n):
        for side, name, src in (('right', M.MULT_NAME, g1), ('right', M.SP_NAME, M.ROOT_CAL),
                                ('left', M.SIDE_NAMES[n], M.ROOT_CAL)):
            sim = HG.similarity(n, shift, side)
            k, rot, _ = sim
            wrap = E('inst', 'ContainerElement', pos=HG.apply(sim, src), dims=(1280, 720), just=(-1, -1), scale=(k, k),
                     rot=rot, children=[copy.deepcopy(desc_gen.ROOTS[name])])
            out.append(((0.0, 0.0), wrap))
    return out


def main():
    out = sys.argv[1]
    health, sp, mult = (float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1.6, 0.6, 4)
    M.descs()
    tiles = []
    for title, run, n in CASES:
        img = highways_only(frame(run), n)
        preview_hud.draw(img, roots(n), (0.0, 0.0), 1.0, state(n, health, sp, mult), additive=True)
        ImageDraw.Draw(img).text((12, 8), title, fill=(255, 255, 255, 255))
        tiles.append(img.convert('RGB'))
    sheet = Image.new('RGB', (2560, 1440))
    for i, t in enumerate(tiles):
        sheet.paste(t.resize((1280, 720)), ((i % 2) * 1280, (i // 2) * 720))
    sheet.save(out, quality=90)
    print('wrote', out)


if __name__ == '__main__':
    main()
