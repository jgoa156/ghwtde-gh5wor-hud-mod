"""Renders the score box's star-progress slot at 1080p pixel scale (1.5 px per canvas unit) at 15/50/95% fill, the way
the GPU draws it: the DE-scaled wedge filler texture (bilinear) and the box art.
usage: python tools/wedge_check.py <out.png>"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import desc_gen, paths, wor_1g as w

K, X0, Y0, WD, HD = 1.5, 925, 578, 250, 24


def main(out):
    w.band_meter()
    els = {}
    for rt in desc_gen.ROOTS.values():
        stack = [rt]
        while stack:
            e = stack.pop()
            els[e.local_id] = e
            stack += e.children
    f = els['star_filler']
    prev = os.path.join(paths.REPO, 'build', 'preview')
    wedge = Image.open(os.path.join(prev, 'WoR_HUD_star_wedge.png')).convert('RGBA')
    box = Image.open(os.path.join(prev, 'WoR_HUD_score_box.png')).convert('RGBA')
    sk = (w.SCORE_K * w.SCORE_X_K, w.SCORE_K)

    def place(tex, e):
        a = math.radians(e.rot)
        ux = np.array([math.cos(a), math.sin(a)]) * e.dims[0] / tex.width * K
        uy = np.array([-math.sin(a), math.cos(a)]) * e.dims[1] / tex.height * K
        p0 = (np.array(e.pos) - [X0, Y0]) * K - uy * tex.height
        m = np.array([[ux[0], uy[0], p0[0]], [ux[1], uy[1], p0[1]], [0, 0, 1]])
        return tex.transform((int(WD * K), int(HD * K)), Image.AFFINE, tuple(np.linalg.inv(m)[:2].ravel()), Image.BILINEAR)

    rows = []
    for fill in (0.15, 0.5, 0.95):
        im = Image.new('RGBA', (int(WD * K), int(HD * K)), (0, 0, 0, 255))
        d = ImageDraw.Draw(im)
        fw, fh = f.dims[0] * f.scale[0] * fill, f.dims[1]
        tex = wedge.resize((max(1, round(fw * K)), round(fh * K)), Image.BILINEAR)
        r, g, b, a = tex.split()
        tex = Image.merge('RGBA', (r.point(lambda v: v * 249 // 255), g.point(lambda v: v * 193 // 255),
                                   b.point(lambda v: v * 34 // 255), a))
        im.alpha_composite(tex, (round((f.pos[0] - X0) * K), round((f.pos[1] - fh / 2 - Y0) * K)))
        bs = box.resize((int(512 * sk[0] * K), int(128 * sk[1] * K)), Image.BILINEAR)
        im.alpha_composite(bs, (int((w.SCORE_C[0] - 256 * sk[0] - X0) * K), int((w.SCORE_C[1] - 64 * sk[1] - Y0) * K)))
        c = im.crop((0, int(7 * K), im.width, int(20 * K)))
        rows.append(c.resize((c.width * 3, c.height * 6), Image.NEAREST))
    sheet = Image.new('RGBA', (rows[0].width, (rows[0].height + 10) * 3), (60, 0, 0, 255))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, i * (r.height + 10)))
    sheet.save(out)
    print('wrote', out)


if __name__ == '__main__':
    main(sys.argv[1])
