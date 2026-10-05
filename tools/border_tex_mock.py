"""Mock of WoR's highway border texture (388dd606) drawn like the DE draws its sidebar: the whole 64-px texture
mapped across a strip along each highway edge (the texture carries its own perspective taper), rows along the edge.
Old border erased (inpaint), strikeline cups restored on top (they draw above the border), then the HUD.
Geometry on images/16.jpg (v0.21). Width = visible WoR border at the bottom (texture content 36 texels)."""
import os, sys
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import border_mock as bm

TEX = r'C:\Users\rockb\ghwor-extract\basic_gems_png\388dd606.png'
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
