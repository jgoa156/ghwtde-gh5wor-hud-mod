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
