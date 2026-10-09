"""Mock of the star power tube fill textures (charging fill + one ready plasma frame) over WoR's tube base, before and
after a change: python tools/mock_sp_tube.py <out.png> --variant "label: NAME=expr; NAME=expr" ...
Settings: FLAT (bool), CHARGING (rgba), BASE / DARK / HOT (rgb), CORE_K, LINE ((rows, strength) or None),
NEON (rgb or None: WoR's tube needle SB_TubeNeedle01 as a glowing neon line at the ready fill's top and bottom),
LEVEL (ready fill level 0..1 for the top line)."""
import argparse, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import paths, wor_1g, wor_art

DEFAULT = dict(FLAT=False, CHARGING=wor_1g.SP_CHARGING_RGBA, BASE=wor_1g.SP_PLASMA_COLOURS['base'],
               DARK=wor_1g.SP_PLASMA_COLOURS['dark'], HOT=wor_1g.SP_PLASMA_COLOURS['hot'], CORE_K=1.0, LINE=None, NEON=None, LEVEL=0.8)
ZOOM = 4


def render(cfg, work):
    base_png = os.path.join(paths.WOR_PNG, 'SP_Base.png')
    full = os.path.join(work, 'full.png')
    wor_art.tube_fill(base_png, os.path.join(paths.WOR_PNG, 'SP_Fill01.png'),
                      (wor_1g.SP_FILL_BAND[1], wor_1g.SP_FILL_BAND[3]), (35, 63), wor_1g.SP_FILL_ROWS,
                      int(wor_1g.SP_RIM), cfg['CHARGING'], full, center=wor_1g.TEX_CENTER, flat_bottom=cfg['FLAT'])
    frame = wor_art.plasma_frames(full, paths.wor('basic_gems_png', 'a1c363bd.png'),
                                  paths.wor('ui_shared_png2', 'noise_32x32x32.png'), 1, base=cfg['BASE'],
                                  hot=cfg['HOT'], dark=cfg['DARK'], core_k=cfg['CORE_K'], bottom_line=cfg['LINE'],
                                  arc=dict(png=paths.wor('basic_gems_png', '0c30522c.png'), rows=wor_1g.SP_FILL_ROWS,
                                           center=wor_1g.TEX_CENTER, every=3))[0]
    tube = Image.open(base_png).convert('RGBA')
    shade = Image.new('RGBA', tube.size, (0, 0, 0, 0))
    shade.paste(Image.new('RGBA', tube.size, (40, 44, 48, 255)), mask=tube.split()[3])
    # ready fill cut at LEVEL (rows above the level hidden), as the plugin's clip window does
    top_row = int(wor_1g.SP_FILL_ROWS[1] - cfg['LEVEL'] * (wor_1g.SP_FILL_ROWS[1] - wor_1g.SP_FILL_ROWS[0]))
    a = frame.split()[3].point(lambda v: v)
    cut = Image.new('L', frame.size, 0)
    cut.paste(255, (0, top_row, frame.size[0], frame.size[1]))
    from PIL import ImageChops
    frame.putalpha(ImageChops.multiply(a, cut))
    out = []
    for fill, ready in ((Image.open(full).convert('RGBA'), False), (frame, True)):
        im = Image.new('RGBA', tube.size, (12, 14, 18, 255))
        im.alpha_composite(shade)
        im.alpha_composite(fill)
        if ready and cfg['NEON']:
            fa = fill.split()[3]
            bottom = max(y for y in range(fill.size[1]) if fa.getbbox() and max(fa.crop((0, y, fill.size[0], y + 1)).get_flattened_data()) > 128)
            for row in (top_row + 2, bottom - 3):
                im = neon(im, fill, row, cfg['NEON'])
        im = im.crop((20, 0, 64, 256))
        out.append(im.resize((im.size[0] * ZOOM, im.size[1] * ZOOM), Image.LANCZOS))
    return out


def neon(im, fill, row, rgb):
    """WoR's tube needle (SB_TubeNeedle01, the half divider's arc) laid across the fill at `row`, flattened to the
    tube's cross-section and stretched to the glass width: white-hot core + soft halo in rgb, added."""
    from PIL import ImageFilter, ImageChops
    nd = Image.open(os.path.join(paths.WOR_PNG, 'SB_TubeNeedle01.png')).convert('RGBA').rotate(-16.7, Image.BICUBIC)
    nd = nd.crop(nd.split()[3].getbbox())
    xs = [x for x in range(fill.size[0]) if fill.getpixel((x, row))[3] > 60]
    if not xs:
        return im
    w = xs[-1] - xs[0] + 3
    nd = nd.resize((w, max(3, round(nd.size[1] * w / nd.size[0] * 1.0))), Image.LANCZOS)
    a = nd.split()[3]
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
    core = Image.new('RGBA', nd.size, (255, 255, 255, 255)); core.putalpha(a)
    halo = Image.new('RGBA', im.size, (0, 0, 0, 0))
    hx, hy = xs[0] - 1, row - nd.size[1] // 2
    glow = Image.new('RGBA', nd.size, tuple(rgb) + (255,)); glow.putalpha(a)
    halo.paste(glow, (hx, hy), glow)
    halo = halo.filter(ImageFilter.GaussianBlur(3.0))
    layer.paste(core, (hx, hy), core)
    base = im.convert('RGB')
    for lay, k in ((halo, 3.5), (layer, 1.6)):
        rgbl = Image.new('RGB', im.size, (0, 0, 0))
        rgbl.paste(lay.convert('RGB'), (0, 0), lay.split()[3])
        rgbl = rgbl.point(lambda v: min(255, int(v * k)))
        base = ImageChops.add(base, rgbl)
    out = base.convert('RGBA')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--variant', action='append', default=[])
    a = ap.parse_args()
    cols = []
    for v in a.variant or ['current']:
        label, _, sets = v.partition(':')
        cfg = dict(DEFAULT)
        for kv in filter(None, (x.strip() for x in sets.split(';'))):
            k, _, e = kv.partition('=')
            cfg[k.strip()] = eval(e)
        with tempfile.TemporaryDirectory() as work:
            cols.append((label.strip(), render(cfg, work)))
    tw, th = cols[0][1][0].size
    sheet = Image.new('RGB', (len(cols) * (2 * tw + 30), th + 40), (24, 22, 22))
    d = ImageDraw.Draw(sheet)
    for i, (label, (charging, ready)) in enumerate(cols):
        x = i * (2 * tw + 30)
        d.text((x + 6, 8), label, fill=(240, 240, 240))
        d.text((x + 6, 22), 'charging        ready', fill=(160, 160, 160))
        sheet.paste(charging.convert('RGB'), (x, 40))
        sheet.paste(ready.convert('RGB'), (x + tw + 10, 40))
    sheet.save(a.out)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
