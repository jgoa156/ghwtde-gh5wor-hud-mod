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
              bolt_k=0.8, center=(51.86, -0.040), frames=16, soften=1.4, flat_bottom=False):
    """A fill in the tube texture's own frame (64x256): every row of the glass interior (the tube's alpha span minus
    `rim`) between `rows` gets the fill band's colour profile across its width, times `tint`. bolts: (frame, x offset)
    crackle wires from bolt_png (16 horizontal frames, white on black) added along the tube centre line."""
    import numpy as np
    tube = np.asarray(Image.open(tube_png).convert('RGBA')).astype(float)
    fill = np.asarray(Image.open(fill_png).convert('RGBA')).astype(float)
    prof = fill[band_rows[0]:band_rows[1], fill_cols[0]:fill_cols[1] + 1].mean(0)
    h, w = tube.shape[:2]
    out = np.zeros((h, w, 4))
    spans = {y: np.where(tube[y, :, 3] > 128)[0] for y in range(int(rows[0]), int(rows[1]))}
    widths = {y: xs[-1] - xs[0] for y, xs in spans.items() if len(xs) >= 2}
    full_w = max(widths.values())
    last_full = max(y for y, wd in widths.items() if wd >= full_w - 1)   # below it the base art bends into its tail
    for y in range(int(rows[0]), int(rows[1])):
        xs = spans[y]
        if flat_bottom and y > last_full:
            xs = spans[last_full]     # keep the glass's full width down to the last row: a flat bottom, no curve
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
    img = Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA')
    if soften:   # blur the alpha so the rim and the cut corners are smooth, not pixel-hard
        from PIL import ImageFilter
        img.putalpha(img.split()[3].filter(ImageFilter.GaussianBlur(soften)))
    img.save(out_png)


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
                  noise_scale=(0.5, 1.0), smooth=1.2, arc=None, core_k=1.0, bottom_line=None):
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
    line = np.zeros((h, w))
    if bottom_line:
        for x in range(w):
            ys = np.where(inside[:, x] > 0.5)[0]
            if len(ys):
                d = ys[-1] - np.arange(h)
                line[:, x] = np.where((d >= 0), np.clip(1.0 - d / float(bottom_line[0]), 0, 1), 0) ** 1.5
    frames = []
    for k in range(n):
        t = k / n
        a = sample(u0 + loop_tiles[0][0] * nw * t, v0 + loop_tiles[0][1] * nh * t)
        b = sample(u0 * 1.7 + 7.3 + loop_tiles[1][0] * nw * t, v0 * 1.7 + 3.1 + loop_tiles[1][1] * nh * t)
        m = np.clip(((a + b) - 1.0) * 3.0 * contrast + 0.5, 0, 1)      # 0 = blotch, 1 = bright
        col = dark[None, None] + (base - dark)[None, None] * m[..., None]
        col = col + (hot - col) * (core_k * core * (0.55 + 0.45 * m))[..., None]
        if bottom_line:   # (rows, strength): a bright line along the fill's bottom edge, fading upwards
            col = col + (hot - col) * (bottom_line[1] * line)[..., None]
        out = np.zeros((h, w, 4))
        out[..., :3] = col
        out[..., 3] = fill[..., 3]
        img = Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA')
        if smooth:   # soften the noise so DXT5's 4x4 blocks stay invisible (the alpha keeps the fill's shape)
            from PIL import ImageFilter
            a_ch = img.split()[3]
            img = img.filter(ImageFilter.GaussianBlur(smooth))
            img.putalpha(a_ch)
        if arc:
            img = add_arc(img, k, **arc)
        frames.append(img)
    return frames


def add_arc(img, k, png, rows, center, frames=16, every=3, width=0.8, strength=1.0, blur=0.7):
    """WoR's ready tube lightning (Tesla needle, Mat_Lightning_Arc_Anim02: Lightining_arc_anim01, 16 frames at 20 fps)
    drawn into plasma frame k: arc frame (k // every) % frames, turned to run along the tube's centre line
    (texture x = center[0] + center[1] * y over rows), `width` of the fill's width, added in white inside the fill."""
    import numpy as np
    from PIL import ImageFilter
    a = np.asarray(img).astype(float)
    h, w = a.shape[:2]
    sheet = Image.open(png).convert('L')
    fh = sheet.size[1] // frames
    f = (k // every) % frames
    wire = sheet.crop((0, f * fh, sheet.size[0], (f + 1) * fh)).transpose(Image.ROTATE_90)
    inside = a[..., 3] / 255.0
    span = [int(rows[0]), int(rows[1])]
    xs = np.where(inside[(span[0] + span[1]) // 2] > 0.5)[0]
    ww = max(4, int(round((xs[-1] - xs[0] + 1) * width))) if len(xs) else 12
    wire = wire.resize((ww, span[1] - span[0]), Image.BICUBIC).filter(ImageFilter.MaxFilter(3))   # keep the bolt's weight
    wire = np.asarray(wire).astype(float) / 255.0
    lum = np.zeros((h, w))
    for i, y in enumerate(range(span[0], span[1])):
        row = np.where(inside[y] > 0.5)[0]          # follow the fill's own centre (the art is slanted)
        cx = (row[0] + row[-1] + 1) / 2 if len(row) else center[0] + center[1] * y
        x0 = int(round(cx - ww / 2))
        lo, hi = max(0, x0), min(w, x0 + ww)
        if hi > lo:
            lum[y, lo:hi] = wire[i, lo - x0:hi - x0]
    if blur:   # a soft core plus a wider halo, like the arc's glow in WoR footage
        src = Image.fromarray((np.clip(lum, 0, 1) * 255).astype('uint8'))
        core = np.asarray(src.filter(ImageFilter.GaussianBlur(blur))).astype(float) / 255.0
        halo = np.asarray(src.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(blur * 3))).astype(float) / 255.0
        lum = np.clip(core * 1.3 + halo * 0.7, 0, 1)
    a[..., :3] = a[..., :3] + (255.0 - a[..., :3]) * (lum * strength * inside)[..., None]
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype('uint8'), 'RGBA')


def soft_strip(src_png, out_png, size=(64, 16), rgb=(255, 255, 255), core=0.0):
    """A horizontal bar texture with soft (anti-aliased) top and bottom edges: the vertical brightness profile of an
    extracted glow sprite's centre column (WoR's hud_progression_bar_lead), stretched along the bar, in `rgb`;
    core > 0 mixes white into the brightest rows."""
    import numpy as np
    src = Image.open(src_png).convert('RGBA')
    col = np.asarray(src.resize((1, size[1]), Image.BICUBIC)).astype(float)[:, 0]
    prof = np.maximum(col[:, 3], col[:, :3].max(axis=1)) / 255.0
    prof = np.sqrt(prof / max(prof.max(), 1e-6))     # flatter: a bar, not a dot's falloff
    out = np.zeros((size[1], size[0], 4))
    rgbv = np.array(rgb, float)
    out[..., :3] = rgbv + (255.0 - rgbv) * (core * prof ** 4)[:, None, None]
    out[..., 3] = (prof * 255.0)[:, None]
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def fire_frames(glow_png, noise_png, n, strength=2.0, flick=0.4, scale=0.18, size=64):
    """WoR's star glow (FC_GLOW / progression_head: Fire_2D over band_HUD_gold_star_glow with a scrolling noise
    volume) as a seamless n-frame loop: the glow's pixels are displaced and its alpha modulated by WoR's noise
    scrolling a whole tile per loop, so the outline's fiery halo licks and flickers in place."""
    import numpy as np
    g = np.asarray(Image.open(glow_png).convert('RGBA').resize((size, size), Image.LANCZOS)).astype(float)   # a glow: 64 px is plenty
    h, w = g.shape[:2]
    noise = np.asarray(Image.open(noise_png).convert('L')).astype(float) / 255.0
    nh, nw = noise.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(float)

    def sample(arr, u, v):
        H, W = arr.shape[:2]
        u %= W
        v %= H
        x0, y0 = np.floor(u).astype(int), np.floor(v).astype(int)
        fx, fy = u - x0, v - y0
        x1, y1 = (x0 + 1) % W, (y0 + 1) % H
        fx = fx[..., None] if arr.ndim == 3 else fx
        fy = fy[..., None] if arr.ndim == 3 else fy
        a = arr[y0, x0] * (1 - fx) + arr[y0, x1] * fx
        b = arr[y1, x0] * (1 - fx) + arr[y1, x1] * fx
        return a * (1 - fy) + b * fy

    out = []
    for k in range(n):
        t = k / n
        n1 = sample(noise, xx * scale * nw / w * 4, yy * scale * nh / h * 4 + nh * t)
        n2 = sample(noise, xx * scale * nw / w * 6 + 11.0 + nw * t, yy * scale * nh / h * 6 + 5.0)
        dx, dy = (n1 - 0.5) * strength, (n2 - 0.5) * strength - abs(n1 - 0.5) * strength   # licks upward
        px = np.clip(xx + dx, 0, w - 1)
        py = np.clip(yy + dy, 0, h - 1)
        im = sample(g, px, py)
        im[..., 3] *= np.clip(1.0 - flick + flick * 2.0 * (0.5 * (n1 + n2)), 0, 1.0)
        out.append(Image.fromarray(np.clip(im + 0.5, 0, 255).astype('uint8'), 'RGBA'))
    return out


def edge_strip(src_png, box, out_png, size=(16, 16)):
    """A black strip whose alpha ramps 255 -> 0 top to bottom (smooth, anti-aliased edge for rotated masks), cut from
    an extracted texture's region `box` (only its footprint is used; the colour is forced to black)."""
    import numpy as np
    src = Image.open(src_png).convert('RGBA').crop(box).resize(size, Image.BICUBIC)
    a = np.asarray(src).astype(float)
    ramp = np.linspace(255.0, 0.0, size[1])[:, None] * np.ones((1, size[0]))
    a[..., :3] = 0.0
    a[..., 3] = ramp
    Image.fromarray(a.astype('uint8'), 'RGBA').save(out_png)


def wedge_strip(src_png, box, out_png, size=(256, 16), left=0.4, pad=1, ss=8):
    """GH5's star-progress bar shape: a white wedge with a flat bottom whose top edge rises from `left` of the height at
    the left end to the full height at the right, anti-aliased (ss x supersampled), on a transparent canvas of `size`
    with `pad` px clear rows top and bottom. Cut from an extracted texture's footprint `box` (the colour is forced to
    white: the DE tints the filler)."""
    import numpy as np
    w, h = size
    Image.open(src_png).convert('RGBA').crop(box)          # provenance: the shape lives in WoR's score meter slot
    W, H = w * ss, h * ss
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    top0, bottom = pad * ss, (h - pad) * ss
    hgt = (bottom - top0) * (left + (1.0 - left) * (xx + 0.5) / W)
    inside = (yy + 0.5 >= bottom - hgt) & (yy + 0.5 < bottom)
    a = inside.reshape(h, ss, w, ss).mean(axis=(1, 3)) * 255.0
    out = np.zeros((h, w, 4))
    out[..., :3] = 255.0
    out[..., 3] = a
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def comet(lead_png, out_png, tail_rgb, size=(64, 16), head=0.8, tail_len=0.32, tail_a=0.9, head_r=3.2):
    """The progress-bar dot with a tail (WoR's HUD_star_lead / hud_progression_bar_lead on both bars): the extracted lead
    sprite's blob, white and glowing, at `head` of the width, plus a soft tail of `tail_rgb` trailing to its left (it
    fades over `tail_len` of the width), the vertical profile taken from the same sprite so the edges stay soft."""
    import numpy as np
    src = Image.open(lead_png).convert('RGBA')
    col = np.asarray(src.resize((1, size[1]), Image.BICUBIC)).astype(float)[:, 0]
    prof = np.maximum(col[:, 3], col[:, :3].max(axis=1)) / 255.0
    prof = prof / max(prof.max(), 1e-6)
    w, h = size
    x = np.arange(w, dtype=float)[None, :]
    hx = head * w
    dx = hx - x                                          # >0 = behind the head
    tail = np.where(dx > 0, np.exp(-dx / (tail_len * w / 3.0)), 0.0) * tail_a
    y = (np.arange(h, dtype=float)[:, None] - (h - 1) / 2.0) / (h / 2.0)
    blob = np.exp(-(((x - hx) / head_r) ** 2 + (y * h / 2.0 / (head_r * 0.9)) ** 2))          # the bright dot
    halo = np.exp(-(((x - hx) / (head_r * 2.2)) ** 2 + (y * h / 2.0 / (head_r * 1.8)) ** 2)) * 0.55
    narrow = np.exp(-(y / 0.55) ** 2)                       # the tail hugs the bar: thinner than the halo
    a = np.clip(np.maximum(tail * narrow, halo) * prof[:, None] ** 0.5 + blob, 0, 1)
    white = np.clip(blob + halo * 0.7, 0, 1)[..., None]
    rgb = np.array(tail_rgb, float)[None, None] * (1 - white) + 255.0 * white
    out = np.zeros((h, w, 4))
    out[..., :3] = rgb
    out[..., 3] = a * 255.0
    Image.fromarray(np.clip(out + 0.5, 0, 255).astype('uint8'), 'RGBA').save(out_png)


def bolt_sheet(arc_png, out_png, cells=8, cell=(128, 512)):
    """The star power strike's art in the DE's own bolt layout (big_lighning01: `cells` vertical cells of `cell` px, thick
    start on top, tip at the bottom = the gem) from WoR's Tesla arc sheet (Lightining_arc_anim01: 16 horizontal 256 x 64
    frames, start ball on the left). Every second frame is used; each cell is WoR's two layers (GuitarEvent_StarSequenceBonus:
    Mat_Lightning_Arc_Anim01 white-cyan, Anim02 cyan at half alpha, one frame later), turned 90 degrees clockwise so the
    arc's tip points down, and enlarged 2x to the cell."""
    import numpy as np
    sheet = Image.open(arc_png).convert('RGBA')
    n = sheet.size[1] // 64
    fw, fh = sheet.size[0], 64
    frames = [sheet.crop((0, i * fh, fw, (i + 1) * fh)) for i in range(n)]
    out = Image.new('RGBA', (cell[0] * cells, cell[1]), (0, 0, 0, 0))
    for c in range(cells):
        f = (2 * c) % n
        a = np.asarray(frames[f]).astype(float)
        b = np.asarray(frames[(f + 1) % n]).astype(float)
        lum_a = a[..., :3].max(axis=2) / 255.0       # the sheet is white on black (alpha is opaque): brightness is the shape
        lum_b = b[..., :3].max(axis=2) / 255.0
        alpha = np.clip(lum_a + lum_b * 0.5, 0, 1)
        rgb = np.zeros(a.shape[:2] + (3,))
        w = np.clip(lum_a / np.maximum(alpha, 1e-6), 0, 1)[..., None]
        rgb[...] = np.array([200, 255, 255], float) * w + np.array([0, 255, 255], float) * (1 - w)
        im = np.zeros(a.shape[:2] + (4,))
        im[..., :3] = rgb
        im[..., 3] = alpha * 255.0
        fr = Image.fromarray(np.clip(im + 0.5, 0, 255).astype('uint8'), 'RGBA').rotate(-90, expand=True)
        fr = fr.resize(cell, Image.BICUBIC)
        out.alpha_composite(fr, (c * cell[0], 0))
    out.save(out_png)


def shrink_into(src_png, out_png, canvas, content, alpha=1.0):
    """The extracted sprite scaled to `content` px, centred on a transparent `canvas` px square (the game draws the
    canvas at its own scale, so the art comes out content/canvas as big), alpha multiplied by `alpha`."""
    im = Image.open(src_png).convert('RGBA').resize((content, content), Image.LANCZOS)
    if alpha != 1.0:
        im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha + 0.5)))
    out = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    out.alpha_composite(im, ((canvas - content) // 2, (canvas - content) // 2))
    out.save(out_png)


def neon_needle_layers(needle_png, width, rgb, halo_blur=3.0):
    """WoR's tube needle (SB_TubeNeedle01, the star power tube's half divider arc) flattened to the tube's
    cross-section (texture frame) and stretched to `width` px: (core, halo) RGBA images of the same size, the core
    white, the halo `rgb` and blurred, both padded by the blur."""
    from PIL import ImageFilter
    nd = Image.open(needle_png).convert('RGBA').rotate(-16.7, Image.BICUBIC)
    nd = nd.crop(nd.split()[3].getbbox())
    nd = nd.resize((width, max(3, round(nd.size[1] * width / nd.size[0]))), Image.LANCZOS)
    pad = int(halo_blur * 3)
    a = Image.new('L', (nd.size[0] + 2 * pad, nd.size[1] + 2 * pad), 0)
    a.paste(nd.split()[3], (pad, pad))
    core = Image.new('RGBA', a.size, (255, 255, 255, 255))
    core.putalpha(a)
    halo = Image.new('RGBA', a.size, tuple(rgb) + (255,))
    halo.putalpha(a.filter(ImageFilter.GaussianBlur(halo_blur)).point(lambda v: min(255, int(v * 2.6))))
    return core, halo, pad


def neon_bottom(img, needle_png, rgb, halo_blur=3.0):
    """A neon needle along the bottom edge of a tube fill texture (64x256 frame): the arc spans the fill's width at
    its last rows and its lowest point sits exactly on the fill's bottom edge."""
    import numpy as np
    a = np.asarray(img.split()[3])
    rows = np.where(a.max(1) > 128)[0]
    bottom = rows[-1]
    xs = np.where(a[bottom - 3] > 128)[0]          # the glass width just above the edge
    core, halo, pad = neon_needle_layers(needle_png, int(xs[-1] - xs[0] + 1), rgb, halo_blur)
    ca = np.asarray(core.split()[3])
    low = np.where(ca.max(1) > 128)[0][-1]          # the arc's lowest opaque row in its own image
    x, y = int(xs[0]) - pad, int(bottom) - int(low)
    out = img.copy()
    out.alpha_composite(halo, (x, y)) if x >= 0 and y >= 0 else out.paste(halo, (x, y), halo)
    out.alpha_composite(core, (x, y)) if x >= 0 and y >= 0 else out.paste(core, (x, y), core)
    return out


def neon_sprite(needle_png, out_core, out_halo, rgb, halo_blur=1.4, halo_gain=1.8):
    """The tube needle in its own 64x64 frame (same placement as SB_TubeNeedle01, so the half divider's rotation and
    scale apply) as a white core and an `rgb` blurred halo: the neon cap at the fill top. Only the needle's bright
    edge line glows (alpha x brightness): its darker lower band, taken as a silhouette, read as a second arc."""
    from PIL import ImageChops, ImageFilter
    nd = Image.open(needle_png).convert('RGBA')
    lum = nd.convert('L').point(lambda v: max(0, min(255, int((v - 100) * 255 / 60))))    # the bright line only
    a = ImageChops.multiply(nd.split()[3], lum)
    peak = max(1, a.getextrema()[1])          # the needle art is semi-transparent: its line peaks at full alpha
    a = a.point(lambda v: 0 if v < 48 else min(255, int(v * 255 / peak)))
    core = Image.new('RGBA', nd.size, (255, 255, 255, 255))
    core.putalpha(a)
    core.save(out_core)
    halo = Image.new('RGBA', nd.size, tuple(rgb) + (255,))
    halo.putalpha(a.filter(ImageFilter.GaussianBlur(halo_blur)).point(lambda v: min(255, int(v * halo_gain))))
    halo.save(out_halo)
