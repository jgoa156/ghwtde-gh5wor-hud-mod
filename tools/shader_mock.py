"""Mock of the background grade + depth of field on in-game footage (background only, like GHWT BGFX).

Base frames come from modded.mp4 (in-game v0.17: no GH5_Grade, DOFBlur 2.0). The grade is the exact GH5_Grade.fx
formula. DOFBlur is the DE's own blur, so the extra blur is approximated with a Gaussian whose sigma grows with
the setting (calibrated so 2.0 -> 3.0 -> 4.5 steps are visible, not measured against the engine).
usage: python shader_mock.py <out.png> [toe_now toe_new dof_now dof_new]
"""
import sys
import cv2
import numpy as np

VID = r'C:\Users\rockb\OneDrive\Videos\GH5'
FRAMES = (200, 560, 900)           # modded frame indices; GH5 original = +18
BASE_DOF = 2.0                     # DOFBlur of modded.mp4


def grab(name, idx):
    v = cv2.VideoCapture(r'%s\%s.mp4' % (VID, name))
    v.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ok, f = v.read()
    assert ok, (name, idx)
    return f


def static_mask():
    """1 on the highway and HUD (excluded from the grade and blur), 0 on the background.

    Hand-drawn on modded.mp4 (1280x720, canvas 10 px up): highway trapezoid with a margin for the rails and
    meters, the multiplier ring, the score panel, and the black capture bar at the top.
    """
    m = np.zeros((720, 1280), np.uint8)
    cv2.fillPoly(m, [np.array([(318, 719), (520, 330), (760, 330), (962, 719)], np.int32)], 1)
    cv2.circle(m, (838, 455), 38, 1, -1)
    cv2.rectangle(m, (925, 540), (1175, 632), 1, -1)
    m[:13] = 1
    return m


def grade(img, toe):
    c = img.astype(np.float32) / 255
    y = 0.2126 * c[..., 2] + 0.7152 * c[..., 1] + 0.0722 * c[..., 0]
    yt = y * y / (y + toe + 1e-6) * (1 + toe)
    return np.clip(c * (yt / np.maximum(y, 1e-5))[..., None], 0, 1)


def blur_for(dof):
    extra = max(dof - BASE_DOF, 0)
    return 0.0 if extra == 0 else 1.2 * extra


def render(img, mask, toe, dof):
    out = grade(img, toe) if toe > 0 else img.astype(np.float32) / 255
    s = blur_for(dof)
    if s > 0:
        out = cv2.GaussianBlur(out, (0, 0), s)
    m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 2)[..., None]
    base = img.astype(np.float32) / 255
    return np.clip(out * (1 - m) + base * m, 0, 1)


def label(img, text):
    cv2.rectangle(img, (0, 0), (img.shape[1], 26), (0, 0, 0), -1)
    cv2.putText(img, text, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def stats(img, mask):
    bg = (mask == 0)
    bg[:, 380:900] = False
    c = img.astype(np.float32) / 255 if img.dtype == np.uint8 else img
    y = 0.2126 * c[..., 2] + 0.7152 * c[..., 1] + 0.0722 * c[..., 0]
    g = cv2.cvtColor((np.clip(c, 0, 1) * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap = np.abs(cv2.Laplacian(g, cv2.CV_32F))
    v = y[bg]
    return np.percentile(v, [10, 50, 90]), float(lap[bg].mean())


if __name__ == '__main__':
    out = sys.argv[1]
    toe_now, toe_new, dof_now, dof_new = (float(x) for x in sys.argv[2:6]) if len(sys.argv) >= 6 else (0.10, 0.16, 3.0, 4.5)
    mask = static_mask()
    cv2.imwrite(out.replace('.png', '_mask.png'), mask * 255)
    rows = []
    allst = {0: [], 1: [], 2: []}
    for idx in FRAMES:
        gh5 = grab('original', idx + 18)
        mod = grab('modded', idx)
        now = render(mod, mask, toe_now, dof_now)
        new = render(mod, mask, toe_new, dof_new)
        for k, im in enumerate((gh5.astype(np.float32) / 255, now, new)):
            allst[k].append(stats(im, mask))
        cols = [label(gh5.copy(), 'GH5 (original)'),
                label((now * 255).astype(np.uint8), 'Now: Toe %.2f, DOFBlur %.1f' % (toe_now, dof_now)),
                label((new * 255).astype(np.uint8), 'Proposed: Toe %.2f, DOFBlur %.1f' % (toe_new, dof_new))]
        rows.append(np.hstack([cv2.resize(c, (640, 360), interpolation=cv2.INTER_AREA) for c in cols]))
    cv2.imwrite(out, np.vstack(rows))
    for k, nm in enumerate(('GH5', 'now', 'proposed')):
        pc = np.mean([s[0] for s in allst[k]], axis=0)
        print('%-9s luma p10 %.3f p50 %.3f p90 %.3f  sharpness %.2f' % (nm, *pc, np.mean([s[1] for s in allst[k]])))
