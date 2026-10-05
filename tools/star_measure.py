"""Gold star outline bbox / star-count digit centre in a 1280x720 frame (same detector for GH5 footage, in-game shots, mock)."""
import sys
import cv2
import numpy as np


def measure(im, x0=1090, x1=1190, y0=535, y1=630):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = [hsv[y0:y1, x0:x1, i] for i in range(3)]
    yel = (h > 14) & (h < 38) & (s > 120) & (v > 150)
    yel = cv2.morphologyEx(yel.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
    ys, xs = np.nonzero(yel)
    bb = (xs.min() + x0, xs.max() + x0, ys.min() + y0, ys.max() + y0)
    # digit: yellow pixels inside the star's inner area (central 40% of the bbox)
    cx, cy = (bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2
    w, hh = bb[1] - bb[0], bb[3] - bb[2]
    inner = np.zeros_like(yel)
    inner[int(cy - 0.2 * hh - y0):int(cy + 0.25 * hh - y0), int(cx - 0.14 * w - x0):int(cx + 0.14 * w - x0)] = True
    dys, dxs = np.nonzero(yel & inner)
    dig = (dxs.mean() + x0, dys.mean() + y0, dxs.min() + x0, dxs.max() + x0, dys.min() + y0, dys.max() + y0) if len(dxs) else None
    return bb, (cx, cy), dig


if __name__ == '__main__':
    for p in sys.argv[1:]:
        if p.endswith('.mp4'):
            v = cv2.VideoCapture(p)
            for idx in (700, 1000):
                v.set(cv2.CAP_PROP_POS_FRAMES, idx); ok, f = v.read()
                print(p[-12:], idx, measure(f))
        else:
            print(p[-30:], measure(cv2.imread(p)))
