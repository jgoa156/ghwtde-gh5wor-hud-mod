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


def tint(src_png, out_png, k):
    """Darken an extracted texture's colour by k (alpha untouched)."""
    im = Image.open(src_png).convert('RGBA')
    r, g, b, a = im.split()
    im = Image.merge('RGBA', [c.point(lambda v: int(v * k)) for c in (r, g, b)] + [a])
    im.save(out_png)


def cut_glass(src_png, out_png, rows, rim):
    """Copy of an extracted tube texture with the glass interior made transparent: on texture rows rows[0]..rows[1]
    every pixel more than rim[0] px inside the left alpha edge and rim[1] px inside the right one gets alpha 0. The
    outline, rims and end caps keep their pixels (used as a frame drawn over the meter fill)."""
    im = Image.open(src_png).convert('RGBA')
    px = im.load()
    w, _ = im.size
    for y in range(int(rows[0]), int(rows[1]) + 1):
        cols = [x for x in range(w) if px[x, y][3] > 40]
        if not cols:
            continue
        for x in range(cols[0] + rim[0], cols[-1] - rim[1] + 1):
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
    im.save(out_png)


def tube_segment(tube_png, fill_png, fill_box, rows, rim, out_png, size=(64, 64), flip=False):
    """Fill texture for one star-power segment, shaped like the tube's glass: output row j maps to tube row
    rows[0] + (j + 0.5) / size[1] * (rows[1] - rows[0]); on it, the glass interior (the tube's alpha span minus rim px
    each side) gets the fill art's colour profile (fill_box rows averaged, its opaque columns stretched across the
    interior). Columns keep the tube's own 64-px frame, so the sprite can use the tube's transform. Composite of
    extracted art only."""
    tube = Image.open(tube_png).convert('RGBA')
    tp = tube.load()
    tw, th = tube.size
    band = Image.open(fill_png).convert('RGBA').crop(fill_box)
    bp = band.load()
    bw, bh = band.size
    cols = [x for x in range(bw) if max(bp[x, y][3] for y in range(bh)) > 20]
    prof = []
    for x in range(cols[0], cols[-1] + 1):
        px_ = [bp[x, y] for y in range(bh)]
        prof.append(tuple(int(sum(p[c] for p in px_) / bh) for c in range(4)))
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    op = out.load()
    for j in range(size[1]):
        y = int(rows[0] + (j + 0.5) / size[1] * (rows[1] - rows[0]))
        y = min(max(y, 0), th - 1)
        span = [x for x in range(tw) if tp[x, y][3] > 40]
        if not span:
            continue
        l, r = span[0] + rim, span[-1] - rim
        if r < l:
            continue
        for x in range(l, r + 1):
            t = (x - l + 0.5) / (r - l + 1)
            op[x * size[0] // tw, j] = prof[min(int(t * len(prof)), len(prof) - 1)]
    if flip:
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
    out.save(out_png)



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
