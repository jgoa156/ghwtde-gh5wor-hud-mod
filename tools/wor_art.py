"""Helpers that prepare extracted WoR / GH3:WoR textures for the theme pak (cropping only: no generated art)."""
from PIL import Image


def crop_to(src_png, out_png, box, size, flip=False):
    """Crop box out of src and place it top-left on a transparent canvas of size (keeps DXT-friendly dims)."""
    src = Image.open(src_png).convert('RGBA').crop(box)
    if flip:
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    out.alpha_composite(src, (0, 0))
    out.save(out_png)


def flip_h(src_png, out_png):
    """Mirror an extracted texture left-right (no other change)."""
    Image.open(src_png).transpose(Image.FLIP_LEFT_RIGHT).save(out_png)


def tint_luma(src_png, out_png, rgb):
    """The image's luminance (normalised to its brightest pixel) times rgb, alpha kept: recolours a lit light."""
    import numpy as np
    a = np.asarray(Image.open(src_png).convert('RGBA')).astype(float)
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    a[..., :3] = (lum / (lum.max() or 1.0))[..., None] * np.array(rgb, float)
    Image.fromarray(np.clip(a + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def tube_fill(tube_png, fill_png, band_rows, fill_cols, rows, rim, tint, out_png, bolts=(), bolt_png=None,
              bolt_k=0.8, center=(51.86, -0.040), frames=16):
    """A fill in the tube texture's own frame (64x256): every row of the glass interior (the tube's alpha span minus
    `rim`) between `rows` gets the fill band's colour profile across its width, times `tint`. bolts: (frame, x offset)
    crackle wires from bolt_png (16 horizontal frames, white on black) added along the tube centre line."""
    import numpy as np
    tube = np.asarray(Image.open(tube_png).convert('RGBA')).astype(float)
    fill = np.asarray(Image.open(fill_png).convert('RGBA')).astype(float)
    prof = fill[band_rows[0]:band_rows[1], fill_cols[0]:fill_cols[1] + 1].mean(0)
    h, w = tube.shape[:2]
    out = np.zeros((h, w, 4))
    for y in range(int(rows[0]), int(rows[1])):
        xs = np.where(tube[y, :, 3] > 128)[0]
        if len(xs) < 2 * rim + 2:
            continue
        x0, x1 = xs[0] + rim, xs[-1] - rim
        idx = np.linspace(0, len(prof) - 1, x1 - x0 + 1)
        for c in range(4):
            out[y, x0:x1 + 1, c] = np.interp(idx, np.arange(len(prof)), prof[:, c])
    out[..., :3] *= np.array(tint[:3], float) / 255.0
    if bolts:
        sheet = Image.open(bolt_png).convert('L')
        fh = sheet.size[1] // frames
        ys = np.arange(int(rows[0]), int(rows[1]))
        for frame, off in bolts:
            wire = sheet.crop((0, frame * fh, sheet.size[0], (frame + 1) * fh)).transpose(Image.ROTATE_90)
            wire = np.asarray(wire.resize((14, len(ys)), Image.BICUBIC)).astype(float) / 255.0
            for k, y in enumerate(ys):
                cx = int(round(center[0] + center[1] * y + off))
                for j in range(14):
                    x = cx - 7 + j
                    if 0 <= x < w and out[y, x, 3] > 0:
                        out[y, x, :3] = np.minimum(255.0, out[y, x, :3] + wire[k, j] * bolt_k * 255.0)
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def tint_rgb(png, rgb):
    """Multiply the image's colour by rgb (alpha kept)."""
    import numpy as np
    a = np.asarray(Image.open(png).convert('RGBA')).astype(float)
    a[..., :3] *= np.array(rgb[:3], float) / 255.0
    Image.fromarray(np.clip(a + 0.5, 0, 255).astype('uint8'), 'RGBA').save(png)


def electrify(band_png, bolt_png, frame, cols, out_png, height=128, strength=0.9, frames=16):
    """The fill band with a lightning wire inside it (GH5's charged star power look): WoR's crackle sheet (16
    horizontal frames, white on black, added on top) turned to run along the tube and fitted to the fill columns.
    The band is stretched to `height` rows first so the wire keeps its detail; alpha is the band's."""
    import numpy as np
    band = Image.open(band_png).convert('RGBA')
    w = band.size[0]
    band = np.asarray(band.resize((w, height), Image.BICUBIC)).astype(float)
    sheet = Image.open(bolt_png).convert('L')
    fh = sheet.size[1] // frames
    wire = sheet.crop((0, frame * fh, sheet.size[0], (frame + 1) * fh)).transpose(Image.ROTATE_90)
    cw = cols[1] - cols[0] + 1
    wire = np.asarray(wire.resize((cw, height), Image.BICUBIC)).astype(float) / 255.0
    lum = np.zeros(band.shape[:2])
    lum[:, cols[0]:cols[1] + 1] = wire
    inside = band[..., 3] > 0
    band[..., :3] = np.where(inside[..., None], band[..., :3] + lum[..., None] * strength * 255.0, band[..., :3])
    Image.fromarray(np.clip(band + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def slant_band(png, geom, cols, h_canvas, w_canvas, out_h=32):
    """Turn the fill band (64 x 16, content columns cols) into a parallelogram on a 64 x out_h canvas: every column
    keeps the band's colour profile, shifted down by slope * (column offset from the content centre). The sprite
    that shows it is h_canvas + 2D tall (see wor_1g.sp_slant_geom), so content height stays h_canvas."""
    d, slope = geom
    im = Image.open(png).convert('RGBA')
    src = im.load()
    w, h = im.size
    total = h_canvas + 2 * d
    out = Image.new('RGBA', (w, out_h), (0, 0, 0, 0))
    op = out.load()
    cx = (cols[0] + cols[1] + 1) / 2
    for x in range(cols[0], cols[1] + 1):
        u = (x + 0.5 - cx) / w * w_canvas            # canvas px from the content centre
        top = d + slope * u                           # canvas px from the sprite top
        for y in range(out_h):
            yc = (y + 0.5) / out_h * total
            v = (yc - top) / h_canvas                 # 0..1 inside the content
            if 0.0 <= v < 1.0:
                op[x, y] = src[x, min(h - 1, int(v * h))]
    out.save(png)


def tube_glow(fill_png, out_png, rgb, spread=3, blur=5.0, core=0.35, ramp=None):
    """Glow for the star power fill: the fill's alpha grown by `spread` px and blurred, in `rgb`, plus a faint copy
    of the fill's own shape (`core`) so the glass reads lit from inside. Drawn additively over the fill.
    ramp (y0, y1): keep only the rows below y0, fading in up to y1 (GH5's charging bar glows at its bottom end)."""
    import numpy as np
    from PIL import ImageFilter
    a = Image.open(fill_png).convert('RGBA').split()[3]
    halo = a.filter(ImageFilter.MaxFilter(2 * spread + 1)).filter(ImageFilter.GaussianBlur(blur))
    h = np.asarray(halo).astype(float) / 255.0
    c = np.asarray(a).astype(float) / 255.0 * core
    lum = np.clip(h * 0.85 + c, 0.0, 1.0)
    if ramp:
        y = np.arange(lum.shape[0], dtype=float)[:, None]
        t = np.clip((y - ramp[0]) / (ramp[1] - ramp[0]), 0.0, 1.0)
        lum = lum * (t * t * (3 - 2 * t))
    out = np.zeros(lum.shape + (4,))
    out[..., :3] = np.array(rgb[:3], float)
    out[..., 3] = lum * 255.0
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def plasma_frames(fill_png, glow_png, noise_png, n, base, hot, dark, contrast=1.0, loop_tiles=((0, 1), (1, -1)),
                  noise_scale=(1.0, 2.0)):
    """GH5's ready star power (WoR material Mat_Sp_Ready_Fire: SP_Fill_Glow02 under a scrolling noise volume) as a
    seamless loop of n frames in the tube fill's own frame. fill_png: the fill (its alpha is the glass interior);
    glow_png: SP_Fill_Glow02 (its brightness across the width is the hot core); noise_png: WoR's noise slice. Two
    copies of the noise scroll by whole tiles over the loop (loop_tiles, tiles per loop for each copy) so the pattern
    churns in place and the last frame meets the first. base/hot/dark: RGB of the fill, its hot core and the blotches."""
    import numpy as np
    fill = np.asarray(Image.open(fill_png).convert('RGBA')).astype(float)
    h, w = fill.shape[:2]
    inside = fill[..., 3] / 255.0
    glow = np.asarray(Image.open(glow_png).convert('L').resize((w, 1), Image.BICUBIC)).astype(float)[0] / 255.0
    # the glow bar's profile across the fill: centre it on the fill's own columns per row
    noise = np.asarray(Image.open(noise_png).convert('L')).astype(float) / 255.0
    nh, nw = noise.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    u0 = xx / w * nw * noise_scale[0]
    v0 = yy / h * nh * noise_scale[1] * (h / w) / 4.0

    def sample(u, v):
        u %= nw
        v %= nh
        x0, y0 = np.floor(u).astype(int), np.floor(v).astype(int)
        fx, fy = u - x0, v - y0
        x1, y1 = (x0 + 1) % nw, (y0 + 1) % nh
        a = noise[y0, x0] * (1 - fx) + noise[y0, x1] * fx
        b = noise[y1, x0] * (1 - fx) + noise[y1, x1] * fx
        return a * (1 - fy) + b * fy

    # hot core across each row: the glow bar profile mapped onto the row's alpha span
    core = np.zeros((h, w))
    for y in range(h):
        xs = np.where(inside[y] > 0.5)[0]
        if len(xs) > 2:
            t = np.clip((np.arange(w) - xs[0]) / max(1, xs[-1] - xs[0]), 0, 1)
            core[y] = np.interp(t * (w - 1), np.arange(w), glow)
    base, hot, dark = (np.array(c, float) for c in (base, hot, dark))
    frames = []
    for k in range(n):
        t = k / n
        a = sample(u0 + loop_tiles[0][0] * nw * t, v0 + loop_tiles[0][1] * nh * t)
        b = sample(u0 * 1.7 + 7.3 + loop_tiles[1][0] * nw * t, v0 * 1.7 + 3.1 + loop_tiles[1][1] * nh * t)
        m = np.clip(((a + b) - 1.0) * 3.0 * contrast + 0.5, 0, 1)      # 0 = blotch, 1 = bright
        col = dark[None, None] + (base - dark)[None, None] * m[..., None]
        col = col + (hot - col) * (core * (0.55 + 0.45 * m))[..., None]
        out = np.zeros((h, w, 4))
        out[..., :3] = col
        out[..., 3] = fill[..., 3]
        frames.append(Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA'))
    return frames
