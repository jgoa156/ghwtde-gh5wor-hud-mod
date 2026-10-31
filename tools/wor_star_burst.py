"""WoR's star-earned burst (son_of_HUD_animate_star_meter_flames: wait 0.3 s, two Mat_Meter_Wibble_Glow flashes, a lens
flare and two spark bursts around the star) as a frame loop on our star.

The DE has neither the glow material nor its texture (SB_Tubeglow02 extracts black), so instead of rebuilding the
particle systems the burst is lifted from WoR footage (paths.WOR_VIDEO, the 0 -> 1 star at 11.2 s): 24 frames at 30 fps
around the star, minus the still frame (an additive layer), WoR's own star rim and digits filled from the glow around
them, and cut where WoR's score box covers it (the box is drawn over the burst there, ours sits in the same place).
The frames are cached in WOR_EXTRACT (game footage is never committed) and ride in the UI pak.

With the WoR HUD theme, Star_Meter_Sparks01 (the DE's 4 note-hit explosions, also run for the band by
WoR_HUD_star_sparks_mp) is swapped for WoR_HUD_star_burst (plugin 1.87), which plays the frames in the star_flame
container; other themes keep the DE's sparks."""
import os
import subprocess

import numpy as np
from PIL import Image

import paths

NAMES = [f'WoR_HUD_starburst_{i:02d}' for i in range(24)]
FPS = 30.0
DELAY = 0.3                     # WoR waits 0.3 s after the count changes (clip: 0.37 s)
T0, F0 = 10.8, 12               # clip time read from, first burst frame (11.20 s)
CROP = (1554, 710, 340, 330)    # x, y, w, h in the 1080p clip around WoR's star
WOR_STAR = (1715.0, 871.0)      # WoR star rim centre in the clip
K = 1.2                         # our star rim (106 x 100 capture px) / WoR's (86 x 84)
CAPTURE_K = 1.5                 # capture px per canvas unit (1080p)
NUDGE = (1.3, 3.0)              # our rim centre (capture 2023, 865) vs the star element's centre, canvas units
TEX = 256
Z = 13.5                        # over the star (number 12) whether z counts in the container or the HUD


def sprite():
    """(pos in star_flame, dims), canvas units: star_flame's (64, 64) is our star's centre."""
    x, y, w, h = CROP
    c = (x + w / 2 - WOR_STAR[0], y + h / 2 - WOR_STAR[1])
    k = K / CAPTURE_K
    return (64.0 + NUDGE[0] + c[0] * k, 64.0 + NUDGE[1] + c[1] * k), (w * k, h * k)


def _clip(n):
    x, y, w, h = CROP
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(T0), '-i', paths.WOR_VIDEO, '-frames:v', str(n),
                          '-vf', f'crop={w}:{h}:{x}:{y}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def _lift():
    from scipy import ndimage
    x0, y0, w, h = CROP
    clip = _clip(54)
    n = len(NAMES)
    still = np.minimum(clip[4], clip[-1])                    # after the count change, before / after the burst
    fx = np.clip(clip - still[None], 0, 255)
    gold = (still[..., 0] > 140) & (still[..., 1] > 100) & (still[..., 2] < 120)
    rim_l = 1672 - x0
    quiet = np.concatenate([clip[:F0], clip[F0 + n:]])
    box = (quiet.max(axis=-1) > 110).any(axis=0) | (still.max(axis=-1) > 45)
    box[:, rim_l + 4:] = False
    mask = ndimage.binary_dilation(gold | box, iterations=3)
    ys, _ = np.nonzero(box)
    occ = np.zeros((h, w), np.float32)
    occ[ys.min():ys.max() + 1, :rim_l + 6] = 1.0
    occ = ndimage.gaussian_filter(occ, 2.0)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.clip(np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy]) / 20.0, 0, 1)
    out = []
    for f in fx[F0:F0 + n]:
        keep = (~mask).astype(np.float32)
        for s in (3, 6, 12):                                  # masked pixels: normalised blur of the glow around them
            num = np.stack([ndimage.gaussian_filter(f[..., c] * keep, s) for c in range(3)], -1)
            den = ndimage.gaussian_filter(keep, s)[..., None]
            f = np.where(mask[..., None] & (den > 0.05), num / np.maximum(den, 1e-3), f)
            keep = np.maximum(keep, (den[..., 0] > 0.05) & mask)
        f = np.clip(f - 6.0, 0, None) * (255.0 / 249.0)     # compression noise floor
        f *= ((1.0 - occ) * edge)[..., None]
        rgb = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((TEX, TEX), Image.LANCZOS)
        out.append(Image.merge('RGBA', (*rgb.split(), Image.new('L', (TEX, TEX), 255))))
    return out


def frames(cache=None):
    """The burst frames (RGBA, TEX x TEX, additive), lifted once and cached under WOR_EXTRACT."""
    cache = cache or paths.wor('star_burst_png')
    files = [os.path.join(cache, n + '.png') for n in NAMES]
    if not all(os.path.isfile(f) for f in files):
        os.makedirs(cache, exist_ok=True)
        for im, f in zip(_lift(), files):
            im.save(f)
    return files


def script():
    pos, dims = sprite()
    tex = ':a{' + ''.join(f'${n}$' for n in NAMES) + ':a}'
    return ('Script WoR_HUD_star_burst [\n'
            '\t:i if $[4c1beb8d]$$value$ = $WoR_HUD_sixth_star$\n'
            '\t\t:i if $ScreenElementExists$${StructQBKey id = WoR_HUD_star_burst}$\n'
            '\t\t\t:i $DestroyScreenElement$${StructQBKey id = WoR_HUD_star_burst}$\n'
            '\t\t:i endif\n'
            f'\t\t:i $wait$%f({DELAY:.2f})$seconds$\n'
            '\t\t:i if NOT $ScreenElementExists$$id$ = %GLOBAL%$parent$\n\t\t\t:i return\n\t\t:i endif\n'
            '\t\t:i $CreateScreenElement$:s{$type$ = $SpriteElement$$id$ = $WoR_HUD_star_burst$$parent$ = %GLOBAL%$parent$'
            f'$texture$ = ${NAMES[0]}$$dims$ = %vec2({dims[0]:.2f},{dims[1]:.2f})$Pos$ = %vec2({pos[0]:.2f},{pos[1]:.2f})'
            '$just$ = :a{$center$$center$:a}$rgba$ = :a{%i(255)%i(255)%i(255)%i(255):a}'
            f'$z_priority$ = %f({Z:.1f})$Blend$ = $add$:s}}\n'
            f'\t\t:i $WoR_frames$ = {tex}\n'
            '\t\t:i $WoR_f$ = %i(0)\n'
            '\t\t:i while \n'
            '\t\t\t:i if NOT $ScreenElementExists$${StructQBKey id = WoR_HUD_star_burst}$\n\t\t\t\t:i return\n\t\t\t:i endif\n'
            '\t\t\t:i $SetScreenElementProps$$id$ = $WoR_HUD_star_burst$$texture$ = (%GLOBAL%$WoR_frames$:a{%GLOBAL%$WoR_f$:a})\n'
            f'\t\t\t:i $wait$%f({1.0 / FPS:.4f})$seconds$\n'
            '\t\t\t:i %GLOBAL%$WoR_f$ = (%GLOBAL%$WoR_f$ + %i(1))\n'
            f'\t\t:i loop_to %i({len(NAMES)})\n'
            '\t\t:i $DestroyScreenElement$${StructQBKey id = WoR_HUD_star_burst}$\n'
            '\t:i else \n'
            '\t\t:i $WoR_HUD_star_burst_orig$ isNull\n'
            '\t:i endif\n'
            '\t:i endfunction\n]\n\n'
            'Script WoR_HUD_star_burst_orig [\n'
            '\t:i $printf$%s("WoR_HUD: star burst placeholder ran, plugin swap missing")\n'
            '\t:i endfunction\n]\n')
