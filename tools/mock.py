"""Side-by-side mocks of HUD settings, the way every layout change gets approved before a build.

Each --variant is "label" or "label: NAME=expr; NAME=expr" (NAME = a setting in tools/wor_1g.py, expr = Python).
Every variant starts from the file's current values. The HUD is drawn with the game-calibrated preview
(tools/preview_hud.py --game) on the mock base (verify/mock_inputs/base.png, built by tools/mock_base.py), which
puts the WoR border where the game draws it.

examples:
  python tools/mock.py verify/mock_x.png --crop tubes --variant now --variant "+2 out: RAIL_OUTSET=(-15.4, 17.7)"
  python tools/mock.py verify/mock_y.png --crop score --gh5 --variant now --variant "count 0.75: STAR_NUM_K=0.75"
  python tools/mock.py verify/mock_z.png --crop tube-ends --shot shot.png --sp 0.5 --variant now

options: --crop tubes|tube-ends|score|full (default tubes), --sp/--health/--mult (DE state), --gh5 (GH5 reference
column, OneDrive footage frame 700), --shot <png> (an in-game screenshot column), --base <png>."""
import argparse, copy, os, sys, tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths, preview_hud, wor_1g  # noqa: E402

# canvas regions per crop: list of (y0, y1, x0, x1, zoom); each region becomes one row of the sheet
CROPS = {
    'tubes': [(440, 710, 310, 480, 1.6), (440, 710, 800, 970, 1.6)],
    'tube-ends': [(540, 670, 320, 450, 2.4), (540, 670, 840, 970, 2.4)],
    'score': [(520, 650, 1000, 1240, 1.1)],
    'full': [(0, 720, 0, 1280, 0.5)],
}
SETTINGS = {k: copy.deepcopy(v) for k, v in vars(wor_1g).items() if k.isupper()}


def label(im, text, h=24):
    im = im.copy()
    cv2.rectangle(im, (0, 0), (im.shape[1], h), (20, 20, 24), -1)
    cv2.putText(im, text, (5, h - 7), 0, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return im


def apply(assignments):
    for k, v in SETTINGS.items():               # reset to the file's values
        setattr(wor_1g, k, copy.deepcopy(v))
    for part in filter(None, (p.strip() for p in assignments.split(';'))):
        name, expr = part.split('=', 1)
        name = name.strip()
        if name not in SETTINGS:
            raise SystemExit(f'unknown setting {name}')
        setattr(wor_1g, name, eval(expr, {}, {}))
    wor_1g.LEFT, wor_1g.RIGHT = wor_1g.make_rails()


def gh5_frame():
    v = cv2.VideoCapture(os.path.join(paths.GH5_VIDEO, 'original.mp4'))
    v.set(cv2.CAP_PROP_POS_FRAMES, 700)
    ok, f = v.read()
    return f if ok else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('out')
    ap.add_argument('--variant', action='append', default=[])
    ap.add_argument('--crop', default='tubes', choices=CROPS)
    ap.add_argument('--sp', type=float, default=0.5)
    ap.add_argument('--health', type=float, default=1.2)
    ap.add_argument('--mult', type=int, default=4)
    ap.add_argument('--gh5', action='store_true')
    ap.add_argument('--shot')
    ap.add_argument('--base', default=os.path.join(paths.REPO, 'verify', 'mock_inputs', 'base.png'))
    a = ap.parse_args()
    cols = []
    if a.gh5:
        f = gh5_frame()
        if f is not None:
            cols.append(('GH5', f))
    if a.shot:
        cols.append(('in game', cv2.resize(cv2.imread(a.shot), (1280, 720), interpolation=cv2.INTER_AREA)))
    tmp = tempfile.mkdtemp(prefix='mock_')
    for i, var in enumerate(a.variant or ['now']):
        name, _, assigns = var.partition(':')
        apply(assigns)
        p = os.path.join(tmp, f'{i}.png')
        preview_hud.render(a.base, p, a.health, a.sp, a.mult, game=True)
        cols.append((name.strip(), cv2.imread(p)))
    apply('')
    rows = []
    for y0, y1, x0, x1, k in CROPS[a.crop]:
        rows.append(np.hstack([label(cv2.resize(im[y0:y1, x0:x1], None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC), t)
                               for t, im in cols]))
    w = max(r.shape[1] for r in rows)
    sheet = np.vstack([cv2.copyMakeBorder(r, 0, 0, 0, w - r.shape[1], cv2.BORDER_CONSTANT) for r in rows])
    cv2.imwrite(a.out, sheet)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
