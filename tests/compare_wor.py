"""Measure our HUD against WoR footage (plan step 1, 2026-10-28: "as detailed and close to the original as possible").

Reference: the user's WoR 1-guitar capture (1920x1080, GH\\WOR.mp4). Ours: capture_band.py frames of the 1g line-up
(2560x1080, the HUD drawn 1920 wide at x 320). Each element is found by template matching (the score box, the star
power tube), then sampled with a mask (the fill's teal pixels, the gold numeral, the brightest line pixels...). The
star power frames are sorted into charging / ready / active on both sides (the highway rails turn cyan while active;
a ready fill is much brighter than a charging one) and compared state by state.

Output: per element the colour on both sides, the CIEDE2000 difference (< 3: barely visible) and the position
offset in pixels, as text and JSON, plus a side-by-side sheet. Run:
    python tests\\compare_wor.py <capture folder> [--ref path\\WOR.mp4]
"""
import argparse, glob, json, math, os, subprocess, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REF_VIDEO = os.path.expanduser(r'~\OneDrive\Videos\GH\WOR.mp4')
REF_DIR = os.path.join(HERE, 'reference', 'wor_1g')
UI_X = 320                     # our 2560-wide capture draws the 1920-wide HUD from x 320

# WoR-frame boxes (1920x1080). The score box and the tube are the anchors; element boxes are relative to them.
SCORE_BOX = (1400, 800, 1780, 960)
TUBE_BOX = (1235, 740, 1345, 960)
SCORE_ELEMENTS = {             # (box in WoR coords, mask, share of pixels kept)
    'song line': ((1415, 830, 1450, 842), 'bright', 0.25),
    'star bar': ((1425, 886, 1470, 898), 'bright', 0.25),
    'score digits': ((1520, 852, 1665, 888), 'bright', 0.20),
    'star numeral': ((1700, 852, 1728, 888), 'gold', 0.30),
    'star rim': ((1665, 830, 1760, 905), 'gold', 0.15),
}
REF_TIMES = {'charging': range(34, 41), 'ready': range(41, 55), 'active': range(55, 61), 'score': range(10, 70, 6)}


def ref_frames(video=REF_VIDEO):
    os.makedirs(REF_DIR, exist_ok=True)
    out = {}
    for state, ts in REF_TIMES.items():
        out[state] = []
        for t in ts:
            p = os.path.join(REF_DIR, f'{state}_{t:03d}.png')
            if not os.path.exists(p):
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', video, '-frames:v', '1', p], check=True)
            out[state].append(p)
    return out


# ---- colour
def _lab(rgb):
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    x, y, z = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    f = lambda t: np.where(t > 216 / 24389, np.cbrt(t), (24389 / 27 * t + 16) / 116)
    fx, fy, fz = f(x / 0.95047), f(y), f(z / 1.08883)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de2000(c1, c2):
    L1, a1, b1 = _lab(c1)
    L2, a2, b2 = _lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = a1 * (1 + G), a2 * (1 + G)
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p, h2p = math.degrees(math.atan2(b1, a1p)) % 360, math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    if C1p * C2p == 0:
        dh = 0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    hm = h1p + h2p
    if C1p * C2p != 0:
        hm = (h1p + h2p + 360) / 2 if abs(h1p - h2p) > 180 else (h1p + h2p) / 2
    T = (1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm))
         + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.20 * math.cos(math.radians(4 * hm - 63)))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cmp, 1 + 0.015 * Cmp * T
    Rt = -2 * math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-((hm - 275) / 25) ** 2)))
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def sample(px, mask, keep):
    p = px.reshape(-1, 3).astype(float)
    mx, mn = p.max(1), p.min(1)
    sat = (mx - mn) / np.maximum(mx, 1)
    if mask == 'fill':
        p = p[(sat > 0.3) & (mx > 60) & (p[:, 1] > p[:, 0] + 25) & (p[:, 2] > p[:, 0] + 15)]   # teal / cyan only
    elif mask == 'plasma':   # charged / active: the bright fill only (the venue's star power glow behind the tube is dim)
        p = p[(sat > 0.25) & (mx > 120) & (p[:, 1] > p[:, 0] + 25) & (p[:, 2] > p[:, 0] + 15)]
    elif mask == 'gold':
        p = p[(sat > 0.35) & (p[:, 0] >= p[:, 2])]
    if len(p) < 12:
        return None, len(p)
    if mask not in ('fill', 'plasma'):
        lum = p.sum(1)
        p = p[lum >= np.quantile(lum, 1 - keep)]
    return np.median(p, 0), len(p)


# ---- locating
def locate(img, tmpl, guess, r=60):
    import cv2
    g = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
    t = cv2.cvtColor(np.asarray(tmpl), cv2.COLOR_RGB2GRAY)
    x0, y0 = max(0, guess[0] - r), max(0, guess[1] - r)
    win = g[y0:guess[1] + t.shape[0] + r, x0:guess[0] + t.shape[1] + r]
    res = cv2.matchTemplate(cv2.Canny(win, 40, 120), cv2.Canny(t, 40, 120), cv2.TM_CCORR_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    return (x0 + loc[0], y0 + loc[1]), score


def sp_state(img, tube_xy):
    """'active' when the highway rail left of the tube is cyan, 'ready' / 'charging' by the fill's brightness,
    None when the tube is empty."""
    a = np.asarray(img).astype(float)
    x, y = tube_xy
    side = np.median(a[y + 40:y + 180, x + 110:x + 200].reshape(-1, 3), 0)   # right of the tube: black, cyan glow while active
    if side[1] > 40 and side[1] > side[0] + 15:
        return 'active'
    c, n = sample(a[y:y + 220, x:x + 110], 'fill', 0)
    if c is None or n < 150:
        return None
    return 'ready' if c.max() > 135 else 'charging'


BOTTOM_GLOW = (83, 138, 110, 160)   # WoR's bottom glow inside the tube crop (TUBE_BOX coordinates)


def glows(tube, state):
    """(top glow, bottom glow) colours in a tube crop (array): the brightest third of the teal pixels in the 12 rows
    from the fill's top (charged / active only: WoR's soft top glow) and in BOTTOM_GLOW."""
    out = [None, None]
    t = tube.astype(float)
    m = (t.max(2) > 120) & (t[..., 1] > t[..., 0] + 25) & (t[..., 2] > t[..., 0] + 15)
    if state in ('ready', 'active') and m.any():
        top = int(np.nonzero(m.any(1))[0].min())
        p = t[top:top + 12][m[top:top + 12]]
        if len(p) >= 12:
            out[0] = np.median(p[p.sum(1) >= np.quantile(p.sum(1), 2 / 3)], 0)
    x0, y0, x1, y1 = BOTTOM_GLOW
    p = t[y0:y1, x0:x1][m[y0:y1, x0:x1]]
    if len(p) >= 12:
        out[1] = np.median(p[p.sum(1) >= np.quantile(p.sum(1), 2 / 3)], 0)
    return out


def crop(img, box, d=(0, 0)):
    return img.crop((box[0] + d[0], box[1] + d[1], box[2] + d[0], box[3] + d[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('capture')
    ap.add_argument('--ref', default=REF_VIDEO)
    a = ap.parse_args()
    refs = ref_frames(a.ref)
    ref0 = Image.open(refs['score'][0]).convert('RGB')
    score_t, tube_t = crop(ref0, SCORE_BOX), crop(Image.open(refs['ready'][3]).convert('RGB'), TUBE_BOX)
    ours = sorted(glob.glob(os.path.join(a.capture, '*_t*.png')))
    if not ours:
        print('no frames in', a.capture)
        return 1
    res = {}

    def add(name, side, c):
        if c is not None:
            res.setdefault(name, {}).setdefault(side, []).append(c)

    # reference side
    for st in ('charging', 'ready', 'active'):
        for p in refs[st]:
            im = np.asarray(Image.open(p).convert('RGB'))
            tube = im[TUBE_BOX[1]:TUBE_BOX[3], TUBE_BOX[0]:TUBE_BOX[2]]
            add(f'SP fill ({st})', 'wor', sample(tube, 'fill' if st == 'charging' else 'plasma', 0)[0])
            tg, bg = glows(tube, st)
            add(f'SP top glow ({st})', 'wor', tg)
            add(f'SP bottom glow ({st})', 'wor', bg)
    for p in refs['score']:
        im = np.asarray(Image.open(p).convert('RGB'))
        for n, (b, m, k) in SCORE_ELEMENTS.items():
            add(n, 'wor', sample(im[b[1]:b[3], b[0]:b[2]], m, k)[0])
    # our side
    offs, sheet = {}, []
    for p in ours:
        img = Image.open(p).convert('RGB')
        im = np.asarray(img)
        (sx, sy), ss = locate(img, score_t, (SCORE_BOX[0] + UI_X, SCORE_BOX[1]))
        (tx, ty), ts = locate(img, tube_t, (TUBE_BOX[0] + UI_X, TUBE_BOX[1]))
        ds, dt = (sx - SCORE_BOX[0], sy - SCORE_BOX[1]), (tx - TUBE_BOX[0], ty - TUBE_BOX[1])
        offs.setdefault('score box', []).append((ds[0] - UI_X, ds[1], ss))
        offs.setdefault('SP tube', []).append((dt[0] - UI_X, dt[1], ts))
        for n, (b, m, k) in SCORE_ELEMENTS.items():
            add(n, 'ours', sample(im[b[1] + ds[1]:b[3] + ds[1], b[0] + ds[0]:b[2] + ds[0]], m, k)[0])
        st = sp_state(img, (tx, ty))
        if st:
            tube = im[ty:ty + 220, tx:tx + 110]
            add(f'SP fill ({st})', 'ours', sample(tube, 'fill' if st == 'charging' else 'plasma', 0)[0])
            tg, bg = glows(tube, st)
            add(f'SP top glow ({st})', 'ours', tg)
            add(f'SP bottom glow ({st})', 'ours', bg)
        sheet.append((os.path.basename(p), st, crop(img, SCORE_BOX, ds), crop(img, TUBE_BOX, dt)))

    lines, out = [], {}
    for n, sides in res.items():
        w, o = sides.get('wor'), sides.get('ours')
        if not w or not o:
            lines.append(f'{n:22s} {"no reference" if not w else "not seen in our frames"}')
            continue
        cw, co = np.median(w, 0), np.median(o, 0)
        d = de2000(cw, co)
        out[n] = {'wor': [int(v) for v in cw], 'ours': [int(v) for v in co], 'dE': round(d, 1), 'n': [len(w), len(o)]}
        lines.append(f'{n:22s} WoR {tuple(int(v) for v in cw)!s:16s} ours {tuple(int(v) for v in co)!s:16s} '
                     f'dE {d:5.1f} {"PASS" if d < 3 else "off"}')
    for n, v in offs.items():
        good = [x for x in v if x[2] > 0.25]
        if good:
            dx, dy = np.median([g[0] for g in good]), np.median([g[1] for g in good])
            out[n + ' offset'] = [float(dx), float(dy)]
            lines.append(f'{n + " offset":22s} dx {dx:+.0f} px, dy {dy:+.0f} px vs WoR ({len(good)} frames matched)')
    report = '\n'.join(lines)
    print(report)
    open(os.path.join(a.capture, 'compare_wor.txt'), 'w').write(report + '\n')
    json.dump(out, open(os.path.join(a.capture, 'compare_wor.json'), 'w'), indent=1)
    # sheet: WoR reference (score, then each SP state) on top, our frames below
    tiles = [('WoR score', crop(ref0, SCORE_BOX), None)]
    for st in ('charging', 'ready', 'active'):
        tiles.append((f'WoR {st}', None, crop(Image.open(refs[st][len(refs[st]) // 2]).convert('RGB'), TUBE_BOX)))
    W = 380 + 8 + 110 * 2
    rows = [(n, s, t) for n, s, t in tiles] + [(f'{n} {st or ""}', s, t) for n, st, s, t in sheet]
    sh = Image.new('RGB', (W, 230 * len(rows)), (30, 30, 34))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(sh)
    for i, (n, s, t) in enumerate(rows):
        y = i * 230
        if s is not None:
            sh.paste(s, (0, y + 14))
        if t is not None:
            sh.paste(t, (388, y + 6))
        dr.text((4, y), n, fill=(230, 230, 230))
    sh.save(os.path.join(a.capture, 'compare_wor.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
