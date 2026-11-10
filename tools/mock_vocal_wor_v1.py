"""Mock v1 of the 2026-11-10 vocal / band corrections (user, WoR frames in the session), drawn on the full-song band
run band-20261110-034744 (2560x1080, 16:9 area x 320..2240, 1.5 px per canvas unit; vocal highway top line y 94,
bottom line y 247).

Rows (ours above, mock below each time):
  A  vocal highway in star power: grey lines kept, WoR's SP glow = sidebar01_glow01 (9ecd4133) turned 90 deg, cyan
     (Default_SP_FX_Color Color1), 1152 x 64 units centred 200 units right of the highway centre on each line (WoR
     Create_Vocals_Star_Power_Effect), so both ends fade; no cyan line under the lyrics; the big cyan Spark01 layer of
     scrolling_sp shrunk like the yellow one, so the spinning Star01 (64,128,128, rot +-500 deg/s) shows.
  B  vocal highway normal: comet core ~11 units (WoR 96.png) instead of ~17, smaller halo; spoken notes as WoR's
     trapezoids on the bottom line (vocal_highway_note_spoken01 + _cap), silver outline, yellow fill once sung.
  C  vocal panel (x3): strip fill 2 px (~1.5 units) up into its tube, needle 2x, lamps without the gloss; star power
     strip with the tube's charged lightning laid along it.
  D  band tubes (x4): fill lifted 3 px (2 units) along the tube so its bottom arc stays inside the glass.
  E  ultrawide: the vocal highway's lines / background / lyric band stretched to the screen edges.

Out: docs/mocks/mock_vocal_wor_v1.png
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, 'tests', 'results', 'band-20261110-034744')
GEMS = r'E:\Dev\ghwt\ghwor-extract\basic_gems_png'
PREVIEW = os.path.join(ROOT, 'build', 'preview')
OUT = os.path.join(ROOT, 'docs', 'mocks', 'mock_vocal_wor_v1.png')

U = 1.5                    # px per canvas unit in the run frames
TOP_Y, BOT_Y = 94, 247     # line centres
NOW_X = 930
HW = (320, 40, 2240, 330)  # highway crop


def frame(t):
    return Image.open(os.path.join(RUN, f'3g1v_{t}.png')).convert('RGB')


def add(base, layer):
    """additive blend of an RGB layer onto base (same size)"""
    from PIL import ImageChops
    return ImageChops.add(base, layer)


def glow_strip(width, x0, xc, y, colour=(0, 255, 255), gain=1.0):
    """WoR's SP glow on one line: sidebar01_glow01 (64 x 128, long axis vertical) turned 90 deg, 1152 x 64 units"""
    tex = Image.open(os.path.join(GEMS, '9ecd4133.png')).convert('RGBA').rotate(90, expand=True)   # 128 x 64
    L, T = int(1152 * U), int(64 * U)
    tex = tex.resize((L, T), Image.BILINEAR)
    lum = tex.split()[3] if tex.mode == 'RGBA' else tex.convert('L')
    g = Image.eval(tex.convert('L'), lambda v: v)
    a = Image.composite(g, Image.new('L', g.size, 0), lum)
    layer = Image.new('RGB', (width, 2 * T + 400), (0, 0, 0))
    col = Image.new('RGB', (L, T), colour)
    blk = Image.new('RGB', (L, T), (0, 0, 0))
    a = a.point(lambda v: min(255, int(v * gain)))
    layer.paste(Image.composite(col, blk, a), (int(xc - L / 2 - x0), 0))
    return layer.crop((0, 0, width, T)), int(y - T / 2)


def radial(size, sigma, colour, gain=1.0):
    im = Image.new('RGB', (size, size))
    px = im.load()
    c = size / 2
    for yy in range(size):
        for xx in range(size):
            r2 = (xx - c) ** 2 + (yy - c) ** 2
            k = gain * math.exp(-r2 / (2 * sigma * sigma))
            px[xx, yy] = tuple(min(255, int(v * k)) for v in colour)
    return im


def star(size, r_out, r_in, rot, colour):
    im = Image.new('RGB', (size, size))
    d = ImageDraw.Draw(im)
    c = size / 2
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 36 - 90)
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=colour)
    return im.filter(ImageFilter.GaussianBlur(1.2))


def paste_add(base, layer, xy):
    x, y = xy
    box = (x, y, x + layer.width, y + layer.height)
    region = base.crop(box)
    base.paste(add(region, layer), box)


def clean_nowline(src, tint):
    """the now line column (green in src), recoloured"""
    col = src.crop((NOW_X - 14, TOP_Y - 6, NOW_X + 14, BOT_Y + 8))
    px = col.load()
    for yy in range(col.height):
        for xx in range(col.width):
            r, g, b = px[xx, yy]
            if g > r + 20 and g > b + 20:      # green plasma
                px[xx, yy] = (int(g * tint[0]), int(g * tint[1]), int(g * tint[2]))
    return col


# ---- A: star power
def row_a():
    ours = frame('t105')
    clean = frame('t165')
    m = ours.copy()
    # our cyan line glow (top line, lyric band bottom) -> the plain grey line / nothing, outside the panel
    px, cp = m.load(), clean.load()
    cyanish = lambda p: p[1] > p[0] + 50 and p[2] > p[0] + 50
    for y in range(84, 108):                       # top line: cyan pixels -> the plain grey line (not under the panel)
        for x in list(range(320, 528)) + list(range(905, 2240)):
            if cyanish(px[x, y]):
                px[x, y] = cp[x, y] if not cyanish(cp[x, y]) else (0, 0, 0)
    for y in range(288, 318):                      # lyric band bottom: no line in WoR
        for x in range(320, 2240):
            p = px[x, y]
            if p[1] > p[0] + 12 and p[2] > p[0] + 12:
                px[x, y] = (0, 0, 0)
    # the comet: our big cyan ball out (cyan / white pixels around the line), the now line back (cyan in SP)
    for y in range(100, 244):                      # and the ball's dim haze over the whole highway
        for x in range(320, 2240):
            p = px[x, y]
            near = (x - 921) ** 2 + (y - 179) ** 2 < 100 ** 2
            if (p[2] > p[0] + 8 and max(p) < 110) or (near and max(p) < 120 and not p[0] > p[2] + 60):
                px[x, y] = (0, 0, 0)
    for y in range(100, 244):
        for x in range(840, 1030):
            p = px[x, y]
            if cyanish(p) or (min(p) > 150 and abs(p[0] - p[1]) < 40 and p[2] > 150) or (p[2] > p[0] and max(p) > 12):
                px[x, y] = (0, 0, 0)
    nl = Image.new('RGB', m.size)
    ImageDraw.Draw(nl).line([(NOW_X, TOP_Y + 4), (NOW_X, BOT_Y - 4)], fill=(40, 200, 220), width=5)
    nl = nl.filter(ImageFilter.GaussianBlur(2))
    m = add(m, nl)
    dm = ImageDraw.Draw(m)
    dm.line([(NOW_X, TOP_Y + 4), (NOW_X, BOT_Y - 4)], fill=(200, 255, 255), width=1)
    dm.polygon([(NOW_X - 6, TOP_Y + 3), (NOW_X + 6, TOP_Y + 3), (NOW_X, TOP_Y + 15)], fill=(225, 225, 225))
    dm.polygon([(NOW_X - 6, BOT_Y - 3), (NOW_X + 6, BOT_Y - 3), (NOW_X, BOT_Y - 15)], fill=(225, 225, 225))
    px = m.load()
    # WoR glow on both lines: centre 200 units right of the highway centre (canvas 640 + 200 -> our root offset)
    xc = 320 + (640 + 200 + 113) * U        # WoR root 288..1218 (centre 753) + 200 = 953
    for y in (TOP_Y, BOT_Y):
        layer, y0 = glow_strip(1920, 320, xc, y, gain=0.85)
        paste_add(m, layer, (320, y0))
    # comet in star power: small cyan spark + the spinning blue star
    cy = 179
    paste_add(m, radial(80, 7.0, (150, 255, 255), 1.0), (NOW_X - 40, cy - 40))
    paste_add(m, star(80, 21, 9, 18, (80, 170, 235)), (NOW_X - 40 - 6, cy - 40 - 3))
    return ours.crop(HW), m.crop(HW)


# ---- B: normal + spoken notes
def trapezoid(d, x0, x1, base_y, h, fill_to=None):
    """WoR spoken note on the bottom line: slanted caps (45 deg) up to a flat top, silver outline, yellow when sung"""
    top = base_y - h
    poly = [(x0, base_y), (x0 + h, top), (x1 - h, top), (x1, base_y)]
    if fill_to is not None:
        fx = min(fill_to, x1)
        # the sung part: inside the trapezoid, left of fx
        mask = Image.new('L', d.im.size if hasattr(d, 'im') else (1, 1), 0)
    return poly, top


def row_b():
    ours = frame('t090')
    m = ours.copy()
    # comet ~0.6x (core 17 -> 11 units), halo mostly gone
    clean = frame('t165')
    d = ImageDraw.Draw(m)
    po = ours.load()
    for yy in range(140, 217):                     # the ball: its core and its orange halo out, the next note kept
        for xx in range(905, 975):
            p = po[xx, yy]
            core = (xx - 937) ** 2 + (yy - 176) ** 2 < 17 ** 2
            if core or p[1] < 0.8 * p[0]:
                m.putpixel((xx, yy), (0, 0, 0))
    # the sung note under the comet back (its fill column copied up to the line)
    for yy in range(140, 217):
        for xx in range(905, NOW_X - 1):
            m.putpixel((xx, yy), ours.getpixel((895, yy)))
    m.paste(clean_nowline(clean, (0.0, 1.0, 0.0)), (NOW_X - 14, TOP_Y - 6))
    cy = 177
    paste_add(m, radial(40, 4.2, (255, 235, 70), 1.25), (NOW_X - 20, cy - 20))
    # spoken notes (illustration: this song has none): two sung (left of the line), two coming
    h = int(12 * U)
    layer = Image.new('RGBA', m.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    for (x0, x1, sung) in ((480, 560, True), (590, 660, True), (1720, 1800, False), (1830, 1960, False)):
        poly = [(x0, BOT_Y), (x0 + h, BOT_Y - h), (x1 - h, BOT_Y - h), (x1, BOT_Y)]
        if sung:
            dl.polygon(poly, fill=(255, 232, 40, 255))
        dl.line(poly, fill=(190, 190, 190, 255), width=3, joint='curve')
    m = Image.alpha_composite(m.convert('RGBA'), layer).convert('RGB')
    return ours.crop(HW), m.crop(HW)


# ---- C: panel
PANEL = (520, 20, 920, 110)


def row_c():
    out = []
    o = frame('t165')
    m = o.copy()
    px = m.load()
    # strip fill: cyan rows 91..101 -> 89..99 (the tube's rows 88..99)
    for x in range(530, 900):
        colv = [o.getpixel((x, y)) for y in range(84, 106)]
        cyan = [(y, p) for y, p in zip(range(84, 106), colv) if p[2] > p[0] + 40]
        if not cyan:
            continue
        for y, p in cyan:
            if 88 <= y - 2 <= 99:
                px[x, y - 2] = p
        for y in (100, 101):                       # under the tube: the background below it
            px[x, y] = o.getpixel((x, 103))
    # lamps without the gloss: each lamp's interior flat at its centre colour, a 1 px darker rim
    for (x0, x1) in ((543, 584), (587, 626), (628, 668)):
        c = o.getpixel(((x0 + x1) // 2, 62))
        d = ImageDraw.Draw(m)
        d.rectangle((x0, 45, x1, 80), fill=tuple(int(v * 0.85) for v in c))
        d.rectangle((x0 + 2, 47, x1 - 2, 78), fill=c if c[1] > 200 else tuple(int(v * 0.65) for v in c))
    # needle 2x (WoR: most of the lamp's height), tip up, at our needle's x
    d = ImageDraw.Draw(m)
    nx = 659
    d.polygon([(nx, 52), (nx - 7, 81), (nx + 7, 81)], fill=(40, 40, 40))
    d.polygon([(nx, 55), (nx - 5, 80), (nx + 5, 80)], fill=(235, 235, 235))
    out.append((o.crop(PANEL), m.crop(PANEL)))
    # strip lightning (star power frame): the tube's charged bolt laid along the fill
    o2 = frame('t105')
    m2 = o2.copy()
    xs = [x for x in range(525, 905) if (lambda p: p[2] > p[0] + 60)(o2.getpixel((x, 95)))]
    if xs:
        x0, x1 = xs[0], xs[-1]
        import random
        rnd = random.Random(7)
        pts, x = [], x0 + 2
        while x < x1 - 2:
            pts.append((x, 93.5 + rnd.uniform(-3.2, 3.2)))
            x += rnd.randint(3, 7)
        glow = Image.new('RGB', m2.size)
        ImageDraw.Draw(glow).line(pts, fill=(60, 200, 220), width=4)
        glow = glow.filter(ImageFilter.GaussianBlur(1.5))
        m2 = add(m2, glow)
        ImageDraw.Draw(m2).line(pts, fill=(240, 255, 255), width=1)
    out.append((o2.crop(PANEL), m2.crop(PANEL)))
    return out


# ---- D: band tubes
def row_d():
    o = frame('t150')
    m = o.copy()
    res = []
    for cx in (858, 1504, 2150):
        box = (cx + 5, 880, cx + 75, 945)
        reg = o.crop(box)
        rp = reg.load()
        W, H = reg.size
        isfill = lambda p: p[1] > 110 and p[2] > 110 and (p[1] > p[0] + 40 or min(p) > 175)
        # the fill as a layer, moved 3 px up and 2 px left (along the tube); the glass body shows where it was
        dx, dy = -2, -3
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lp = layer.load()
        base = reg.copy()
        bp = base.load()
        for y in range(H):
            for x in range(W):
                if isfill(rp[x, y]):
                    lp[x, y] = rp[x, y] + (255,)
                    bp[x, y] = (44, 46, 50)
        base = base.convert('RGBA')
        base.alpha_composite(layer, (dx, dy))
        res.append((reg, base.convert('RGB')))
    return res


# ---- E: ultrawide
def row_e():
    o = frame('t165')
    m = o.copy()
    # lines: copy a clean line profile to the screen edges
    for (y0, y1) in ((88, 101), (241, 254)):
        prof = o.crop((1500, y0, 1501, y1))
        for x in list(range(0, 470)) + list(range(2024, 2560)):
            m.paste(prof, (x, y0))
    return o, m


def label(img, text, size=26):
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('arialbd.ttf', size)
    except OSError:
        f = ImageFont.load_default()
    d.rectangle((0, 0, d.textlength(text, font=f) + 16, size + 10), fill=(20, 20, 20))
    d.text((8, 4), text, fill=(255, 220, 90), font=f)
    return img


def main():
    W = 1920
    rows = []
    a0, a1 = row_a()
    rows += [label(a0, 'A  ours: star power'), label(a1, 'A  mock: WoR glow (fades at both ends), grey lines, small spark + spinning blue star')]
    b0, b1 = row_b()
    rows += [label(b0, 'B  ours: normal'), label(b1, 'B  mock: comet ~0.6x, spoken notes as trapezoids on the bottom line (illustration)')]
    # C: panels x3 side by side
    c = row_c()
    tiles = []
    for (o, m) in c:
        k = 3
        o = o.resize((o.width * k, o.height * k), Image.NEAREST)
        m = m.resize((m.width * k, m.height * k), Image.NEAREST)
        t = Image.new('RGB', (o.width, o.height * 2 + 6), (255, 0, 255))
        t.paste(o, (0, 0))
        t.paste(m, (0, o.height + 6))
        tiles.append(t)
    crow = Image.new('RGB', (W, tiles[0].height), (30, 30, 30))
    crow.paste(tiles[0], (0, 0))
    crow.paste(tiles[1], (W - tiles[1].width, 0))
    rows.append(label(crow, 'C  panel x3: top ours / bottom mock.  Left: strip 2 px up, needle 2x, flat lamps.  Right: charged lightning on the strip', 22))
    # D: tubes x4
    d = row_d()
    k = 4
    drow = Image.new('RGB', (W, 65 * k), (30, 30, 30))
    x = 0
    for (o, m) in d:
        o = o.resize((o.width * k, o.height * k), Image.NEAREST)
        m = m.resize(o.size, Image.NEAREST)
        drow.paste(o, (x, 0))
        drow.paste(m, (x + o.width + 4, 0))
        x += 2 * o.width + 40
    rows.append(label(drow, 'D  band tube ends x4 (each pair: ours | mock, fill 2 units up along the tube)', 22))
    e0, e1 = row_e()
    e0 = e0.crop((0, 30, 2560, 330)).resize((W, 225))
    e1 = e1.crop((0, 30, 2560, 330)).resize((W, 225))
    rows += [label(e0, 'E  ours: ultrawide 2560x1080'), label(e1, 'E  mock: vocal highway stretched to the screen edges')]
    H = sum(r.height + 10 for r in rows)
    sheet = Image.new('RGB', (W, H), (255, 0, 255))
    y = 0
    for r in rows:
        if r.width != W:
            r = r.resize((W, int(r.height * W / r.width)))
        sheet.paste(r, (0, y))
        y += r.height + 10
    sheet.save(OUT)
    print(OUT, sheet.size)


if __name__ == '__main__':
    main()
