"""Mock of a wider highway border (sidebar_x_scale) with the meter tubes refitted, on a clean in-game frame.

The border is re-drawn from its own pixel profile (a clean row below the tubes), widened by K about its centre line
and scaled with the highway's perspective; the old tubes are removed by inpainting, then the HUD is drawn with the
tubes tucked by the new values. Geometry measured on images/16.jpg (v0.21, sidebar_x_scale 2.0).
usage: python border_mock.py <frame.jpg> <out.png> K tuck_left tuck_right
"""
import os, sys, runpy
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CL = lambda y: 352.5 + 0.518 * (710 - y)     # border centre lines (v0.21 capture)
CR = lambda y: 927.5 - 0.517 * (710 - y)
REF_Y, HALF = 650, 12                        # reference row and half window of the border profile


def hud(base, out, tl, tr, on_border=True):
    import wor_1g
    wor_1g.RAIL_TUCK_LEFT, wor_1g.RAIL_TUCK_RIGHT = tl, tr
    wor_1g.RAIL_ON_BORDER = on_border
    wor_1g.LEFT = wor_1g.on_border(wor_1g.Rail(wor_1g.LEFT_EDGE, outward=-1.0, mirror=False), wor_1g.BORDER_LINE_L)
    wor_1g.RIGHT = wor_1g.on_border(wor_1g.Rail(wor_1g.RIGHT_EDGE, outward=1.0, mirror=True), wor_1g.BORDER_LINE_R)
    sys.argv = ['preview_hud.py', base, out, '1.2', '0.5', '4', '--game']
    runpy.run_path(os.path.join(HERE, 'preview_hud.py'), run_name='__main__')


TEX = None          # texture strip for the border (e.g. WoR's 388dd606); None = widen the frame's own border
TEX_W = 24.0        # strip width (texture content) on screen at REF_Y
TEX_SHIFT = 0.0     # strip centre offset from the border centre line, towards the highway (+)


def tex_border(clean, img, hsv):
    """Draw the border as a texture strip like the DE does (texture rows along the edge, columns across), both sides."""
    from PIL import Image
    t = np.asarray(Image.open(TEX).convert('RGBA')).astype(np.float32)
    th, tw = t.shape[:2]
    hw0 = CR(REF_Y) - CL(REF_Y)
    out = clean.astype(np.float32)
    for side, c in (('L', CL), ('R', CR)):
        inward = 1 if side == 'L' else -1
        tex = t if side == 'L' else t[:, ::-1]
        for y in range(300, 720):
            v = int((y - 300) / (719 - 300) * (th - 1))
            row = tex[v]
            cols = np.nonzero(row[:, 3] > 20)[0]
            if len(cols) == 0:
                continue
            s0 = (CR(y) - CL(y)) / hw0
            w = TEX_W * s0
            cx = c(y) + inward * TEX_SHIFT * s0
            l, r = cx - w / 2, cx + w / 2
            for x in range(int(np.floor(l)), int(np.ceil(r)) + 1):
                if not (0 <= x < img.shape[1]):
                    continue
                if hsv[y, x, 1] > 80 and hsv[y, x, 2] > 80:
                    continue
                if y >= 612 and (x - c(y)) * inward > HALF * s0 * 0.7:
                    continue
                u = (x - l) / max(w, 1e-3)
                tc = cols[0] + u * (cols[-1] - cols[0])
                px = row[min(int(tc), tw - 1)]
                a = px[3] / 255.0
                out[y, x] = out[y, x] * (1 - a) + px[[2, 1, 0]] * a
    return np.clip(out, 0, 255).astype(np.uint8)


def main(src, out, k, tl, tr):
    img = cv2.imread(src)
    tmp = os.path.join(os.path.dirname(out), '_bm_tmp')
    os.makedirs(tmp, exist_ok=True)
    black = np.zeros_like(img)
    cv2.imwrite(os.path.join(tmp, 'black.png'), black)
    # 1. remove the current tubes (render the current HUD on black -> mask)
    hud(os.path.join(tmp, 'black.png'), os.path.join(tmp, 'cur.png'), 3.0, 5.0, on_border=False)   # v0.21 positions
    cur = cv2.imread(os.path.join(tmp, 'cur.png'))
    m = (cur.max(2) > 8).astype(np.uint8)
    m[:, 1000:] = 0
    m[540:, 900:] = 0
    m[:380] = 0
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    clean = cv2.inpaint(img, m * 255, 6, cv2.INPAINT_TELEA)
    # 2. widen the border: reference profile at REF_Y, stretched by K * perspective about the centre line
    hw0 = CR(REF_Y) - CL(REF_Y)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    for side, c in (('L', CL), ('R', CR)):
        inward = 1 if side == 'L' else -1
        c0 = c(REF_Y)
        prof = img[REF_Y, int(round(c0)) - HALF:int(round(c0)) + HALF + 1].astype(np.float32)
        xs_ref = np.arange(-HALF, HALF + 1, dtype=np.float32)
        for y in range(300, 720):
            s = (CR(y) - CL(y)) / hw0 * k
            cx = c(y)
            half = HALF * s
            for x in range(int(np.floor(cx - half)), int(np.ceil(cx + half)) + 1):
                u = (x - cx) / s
                if abs(u) > HALF or not (0 <= x < img.shape[1]):
                    continue
                # game draw order: the border (z 3) is under the strikeline cups / neck (z 3.1-3.9) and the
                # coloured rings: never paint over saturated pixels, and in the strikeline rows don't grow inward
                if hsv[y, x, 1] > 80 and hsv[y, x, 2] > 80:
                    continue
                s0 = (CR(y) - CL(y)) / hw0
                if y >= 612 and (x - cx) * inward > HALF * s0 * 0.7:
                    continue
                for ch in range(3):
                    clean[y, x, ch] = np.interp(u, xs_ref, prof[:, ch])
    if TEX:
        clean = tex_border(clean, img, hsv)
    cv2.imwrite(os.path.join(tmp, 'border.png'), clean)
    # 3. HUD with the refitted tubes
    hud(os.path.join(tmp, 'border.png'), out, tl, tr, on_border=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
