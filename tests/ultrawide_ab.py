"""Automated ultrawide Hor+ check (user 2026-10-28: "how do we fully validate the ultrawide fix?").

Two bot runs of the same song and line-up, differing only in ghwtde_ultrawide.ini HorPlus (0 = the game's zoomed-in
3D view, 1 = the fix: 16:9's vertical field of view). Every run goes through capture_band.run, so the save, the
Profiles and GHWTDE.ini are backed up and restored; ghwtde_ultrawide.ini is restored here. The gameplay highways are
3D, so their on-screen scale tells the vertical FOV: the horizontal FOV is fixed by the game, hence at 21:9 the
zoomed-in view magnifies by (16/9) / (w/h) ^ -1 = (w/h) / (16/9) (2560x1080: 1.333). The script matches features on the
lower half of the frames (highways, no HUD) between the two runs, estimates the scale and prints PASS when the fix's
view is smaller by that factor (+-4%). It also writes a side-by-side image per frame pair.

Usage:  python tests\\ultrawide_ab.py [--lineup 1g] [--until 112]      (asks nothing: only run it after the user's OK)
"""
import argparse, glob, os, shutil, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture_band as C  # noqa: E402
import ingame_smoke as H  # noqa: E402

UW_INI = os.path.join(H.GAME, 'ghwtde_ultrawide.ini')


def set_horplus(v):
    t = open(UW_INI, encoding='utf-8', errors='surrogateescape').read()
    t = H.set_ini(t, 'GHWTDE_ULTRAWIDE', 'HorPlus', str(v))
    open(UW_INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(t)


def scale_between(a_png, b_png):
    """(scale, matches) of b relative to a (b = a magnified by `scale`), on the lower half of the frames."""
    import cv2
    import numpy as np
    a, b = cv2.imread(a_png, 0), cv2.imread(b_png, 0)
    h = a.shape[0]
    a, b = a[int(h * 0.45):int(h * 0.97)], b[int(h * 0.45):int(h * 0.97)]
    orb = cv2.ORB_create(4000)
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None:
        return None, 0
    m = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(m) < 12:
        return None, len(m)
    pa = np.float32([ka[x.queryIdx].pt for x in m])
    pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=3.0)
    if M is None:
        return None, len(m)
    return float(np.hypot(M[0, 0], M[0, 1])), int(inl.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lineup', default='1g', choices=sorted(C.LINEUPS))
    ap.add_argument('--song', default='ontheroadagain')
    ap.add_argument('--until', type=int, default=125)     # shots at T+90, 100, 110, 120
    ap.add_argument('--every', type=int, default=10)
    ap.add_argument('--wait', type=int, default=150)
    ap.add_argument('--frames', type=int, default=5)
    ap.add_argument('--bulb-cycle', action='store_true')
    a = ap.parse_args()
    a.native = True          # always windowed at the screen's own size: a scaled picture can't validate the FOV
    if H.game_running():
        print('REFUSED: the game is already running; close it first.')
        return 2
    stamp = time.strftime('%Y%m%d-%H%M%S')
    outs = {}
    original = open(UW_INI, encoding='utf-8', errors='surrogateescape').read()
    try:
        for hp in (0, 1):
            set_horplus(hp)
            out = os.path.join(H.OUT, f'uw-{stamp}-horplus{hp}')
            os.makedirs(out, exist_ok=True)
            C.run(a.lineup, C.LINEUPS[a.lineup], a, out)
            outs[hp] = out
    finally:
        open(UW_INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(original)
    import cv2
    import numpy as np
    from PIL import Image
    fa, fb = sorted(glob.glob(outs[0] + '/*_t*.png')), sorted(glob.glob(outs[1] + '/*_t*.png'))
    if not fa or not fb:
        print('RESULT: missing frames', len(fa), len(fb))
        return 1
    w, h = Image.open(fa[0]).size
    want = (w / h) / (16 / 9)
    ok = 0
    for i, (x, y) in enumerate(zip(fa, fb)):
        s, n = scale_between(y, x)    # the zoomed-in view (x) relative to the fix's (y)
        print(f'pair {i}: zoomed-in / fix = {s if s is None else round(s, 3)} (inliers {n}; expected {want:.3f})')
        ok += bool(s and abs(s - want) / want < 0.04)
        sbs = Image.new('RGB', (w, h * 2))
        sbs.paste(Image.open(x), (0, 0))
        sbs.paste(Image.open(y), (0, h))
        sbs.resize((w // 2, h)).save(os.path.join(H.OUT, f'uw-{stamp}-pair{i}.png'))
    print(f'RESULT: {"PASS" if ok == min(len(fa), len(fb)) else "FAIL/INCONCLUSIVE"} ({ok} of {min(len(fa), len(fb))} pairs); '
          f'frames in {outs[0]} and {outs[1]}, side by side: {H.OUT}\\uw-{stamp}-pair*.png')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
