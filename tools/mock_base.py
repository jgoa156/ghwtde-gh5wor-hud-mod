"""Builds the mock background (verify/mock_inputs/base.png): a clean in-game frame with the HUD removed, the highway
metal darkened like WoR_HUD_DarkMetal, and WoR's border (388dd606) drawn where the game puts it, so tools/mock.py
can draw the HUD on top. The DE maps the whole 64-px border texture across a strip along each edge (rows along the
edge, its own perspective taper); the strikeline cups are restored on top (they draw above the border).

usage: python tools/mock_base.py [frame.jpg hud_mask.png out.png]   (defaults: verify/mock_inputs/)"""
import os, sys
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths  # noqa: E402


class bm:
    """Border centre lines measured on the v0.21 capture (canvas px)."""
    CL = staticmethod(lambda y: 352.5 + 0.518 * (710 - y))
    CR = staticmethod(lambda y: 927.5 - 0.517 * (710 - y))


TEX = paths.wor('basic_gems_png', '388dd606.png')
V_TOP, V_BOT = 300.0, 735.0          # screen rows mapped to texture rows 0 / 511
CUPS = [(437, 638), (539, 638), (640, 638), (741, 638), (843, 638)]
CUP_R = (44, 17)
EDGE_SLOPE = 0.518


def tex_rows():
    t = np.asarray(Image.open(TEX).convert('RGBA')).astype(np.float32)
    return t


def draw(base, inner_l, inner_r, width_px, dark=0.58):
    """inner_l/inner_r: x of the border's inner edge (texture column 62) at y=638 on each side."""
    t = tex_rows()
    th, tw = t.shape[:2]
    k_bot = width_px / 36.0                  # screen px per texel at the reference row (v ~ 480)
    hw0 = bm.CR(638) - bm.CL(638)
    out = base.astype(np.float32)
    for side in ('L', 'R'):
        for y in range(int(V_TOP), 720):
            v = (y - V_TOP) / (V_BOT - V_TOP) * (th - 1)
            s = (bm.CR(y) - bm.CL(y)) / hw0
            k = k_bot * s
            if side == 'L':
                xin = inner_l + EDGE_SLOPE * (638 - y)
            else:
                xin = inner_r - EDGE_SLOPE * (638 - y)
            x0 = int(np.floor(xin - 64 * k)) - 1 if side == 'L' else int(np.floor(xin)) - 1
            x1 = int(np.ceil(xin)) + 1 if side == 'L' else int(np.ceil(xin + 64 * k)) + 1
            for x in range(max(0, x0), min(base.shape[1], x1)):
                # texture column: col 62 at the inner edge, outward = lower columns
                col = 62.0 - ((xin - x) / k if side == 'L' else (x - xin) / k)
                if col < 0 or col > 63:
                    continue
                c0 = int(col); f = col - c0; c1 = min(c0 + 1, 63)
                v0 = int(v); g = v - v0; v1 = min(v0 + 1, th - 1)
                px = (t[v0, c0] * (1 - f) + t[v0, c1] * f) * (1 - g) + (t[v1, c0] * (1 - f) + t[v1, c1] * f) * g
                a = px[3] / 255.0
                if a <= 0.01:
                    continue
                rgb = px[[2, 1, 0]] * dark
                out[y, x] = out[y, x] * (1 - a) + rgb * a
    return np.clip(out, 0, 255).astype(np.uint8)


def erase_old_border(img):
    m = np.zeros(img.shape[:2], np.uint8)
    for c in (bm.CL, bm.CR):
        for y in range(290, 720):
            s = (bm.CR(y) - bm.CL(y)) / (bm.CR(650) - bm.CL(650))
            h = 12 * s + 2
            cv2.line(m, (int(c(y) - h), y), (int(c(y) + h), y), 1, 1)
    return cv2.inpaint(img, m * 255, 5, cv2.INPAINT_TELEA)


def cup_mask(shape):
    m = np.zeros(shape[:2], np.uint8)
    for cx, cy in CUPS:
        cv2.ellipse(m, (cx, cy), CUP_R, 0, 0, 360, 1, -1)
    return m.astype(bool)


# Where the game draws the WoR border for BORDER_OFFSET 17.4 / BORDER_X_SCALE 2.6: inner edges at y 638, width.
BORDER_INNER = (396.7, 883.3)
BORDER_W = 28.0


def make(frame, hud_png, out):
    """frame: an in-game shot on the 1280x720 canvas; hud_png: a render of the HUD alone on black (its pixels are
    inpainted away)."""
    img = cv2.imread(frame)
    cups = cup_mask(img.shape)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hw = np.zeros(img.shape[:2], np.uint8)
    cv2.fillPoly(hw, [np.array([(300, 719), (520, 280), (762, 280), (985, 719)], np.int32)], 1)
    s, v = hsv[..., 1] / 255, hsv[..., 2] / 255
    wt = (hw == 1) * np.clip((0.30 - s) / 0.15, 0, 1) * np.clip((v - 0.30) / 0.15, 0, 1) * (~cups)
    wt = cv2.GaussianBlur(wt.astype(np.float32), (0, 0), 0.8)[..., None]
    dark = np.clip(img * (1 - wt) + img * 0.58 * wt, 0, 255).astype(np.uint8)
    cur = cv2.imread(hud_png)
    tm = (cur.max(2) > 8).astype(np.uint8)
    tm[:, 1000:] = 0
    tm[540:, 900:] = 0
    tm[:380] = 0
    clean = erase_old_border(cv2.inpaint(dark, cv2.dilate(tm, np.ones((7, 7), np.uint8)) * 255, 6, cv2.INPAINT_TELEA))
    res = draw(clean, BORDER_INNER[0], BORDER_INNER[1], BORDER_W)
    res[cups] = dark[cups]
    cv2.imwrite(out, res)
    print('wrote', out)


if __name__ == '__main__':
    d = os.path.join(paths.REPO, 'verify', 'mock_inputs')
    a = sys.argv[1:] or [os.path.join(d, 'frame_v021.jpg'), os.path.join(d, 'hud_v021.png'), os.path.join(d, 'base.png')]
    make(*a)
