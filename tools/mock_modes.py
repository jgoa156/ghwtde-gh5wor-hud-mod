"""Mocks of the other game modes with the WoR theme (face-off, pro face-off, battle, band, vocals, guitar + vocals).

Each mode is built from:
  - the highway of the real in-game mock base (verify/mock_inputs/base.png: a DE frame with the WoR border and no
    HUD), scaled and repeated for each player, with our in-game WoR 1-player HUD (tools/preview_hud.py, game
    calibration) attached to every highway: WoR gives every player the same sidebar set;
  - the mode's own WoR widgets, drawn from WoR's descs (ghwor-extract/uidesc, nested descs inlined, WoR textures):
    band star meter + revive meter (hud_standard), versus scoreboard (HUD_band_versus / comp_scoreboard_player),
    vocals highway (vocals_highway). WoR maps modes to layouts in hud_layouts.qb: band = hud_standard,
    guitar + vocals = hud_standard_1g1v, vocals = hud_standard_1v, versus = HUD_band_versus.
Highway spots per mode are approximate (the game places highways itself, not from the desc).

usage: python tools/mock_modes.py <out.jpg> [mode ...]   modes: faceoff band vocals guitar_vocals battle
"""
import math, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths, preview_hud  # noqa: E402
from desc_gen import E  # noqa: E402
from desc_tree import tokens_block, field  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, '..', 'verify', 'mock_inputs', 'base.png')
UIDESC = os.path.join(paths.WOR_EXTRACT, 'uidesc')
TEX_DIRS = [os.path.join(paths.WOR_EXTRACT, d) for d in ('z_in_game_png2', 'z_in_game_png', 'ui_shared_png2', 'ui_shared_png',
                                                          'basic_gems_png', 'global_model_tex_png', 'zone_global_png')]
_TEX = {}


def load_tex(name):
    if not _TEX:
        for d in TEX_DIRS:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith('.png'):
                        _TEX.setdefault(f[:-4].lower(), os.path.join(d, f))
    if name in (None, '0x00000000'):
        return None
    if name.lower() == 'white':
        return Image.new('RGBA', (8, 8), (255, 255, 255, 255))
    p = _TEX.get(name.lower())
    return Image.open(p).convert('RGBA') if p else None


def _nums(props, name, n=2, default=None):
    v = field(props, name)
    if v is None:
        return default
    try:
        vals = [float(x) for x in v.split(',')][:n]
    except ValueError:                                   # a named value (e.g. rgba = NTSCWhite)
        return default
    if len(vals) < n:
        return default
    return tuple(vals) if n > 1 else vals[0]


def parse_desc(name, depth=0):
    """WoR desc <name> as an E tree; a descinterface element gets its desc's tree as first child."""
    path = os.path.join(UIDESC, f'uidesc_{name}.txt')
    if not os.path.exists(path) or depth > 4:
        return None
    s = open(path, encoding='utf-8', errors='replace').read()

    def parse(seg):
        out, i = [], 0
        while True:
            m = re.search(r'StructStruct props', seg[i:])
            if not m:
                return out
            props, p1 = tokens_block(seg, i + m.start())
            rgba = _nums(props, 'rgba', 4, (255, 255, 255, 255))
            e = E(field(props, 'local_id') or '?', field(props, 'type') or 'ContainerElement',
                  pos=_nums(props, 'Pos', 2, (0, 0)), dims=_nums(props, 'dims', 2, (100, 100)),
                  just=_nums(props, 'just', 2, (0, 0)), scale=_nums(props, 'Scale', 2, (1, 1)),
                  rot=_nums(props, 'rot_angle', 1, 0.0) or 0.0, z=_nums(props, 'z_priority', 1, 0.0) or 0.0,
                  alpha=_nums(props, 'alpha', 1, 1.0), rgba=tuple(int(c) for c in rgba),
                  hidden=field(props, 'hiddenlocal') == 'true', anchor=_nums(props, 'pos_anchor', 2, (-1, -1)),
                  texture=field(props, 'texture'), blend=field(props, 'Blend'), font=field(props, 'font'))
            c = re.match(r'\s*StructArray children', seg[p1:])
            if c:
                kids, p2 = tokens_block(seg, p1 + c.end())
                e.children = parse(kids[1:-1])
                i = p2
            else:
                i = p1
            if e.kind == 'descinterface':
                sub = re.search(r'StructString desc = "([^"]+)"', props)
                inner = parse_desc(sub.group(1), depth + 1) if sub else None
                if inner is not None:
                    e.children = [inner] + e.children
            out.append(e)
    roots = parse(s[s.index('StructStruct elements'):])
    return roots[0] if roots else None


def find(e, lid):
    if e.local_id == lid:
        return e
    for c in e.children:
        r = find(c, lid)
        if r is not None:
            return r
    return None


def prune(e, drop):
    """Remove the elements whose local_id is in drop (and everything under them)."""
    e.children = [c for c in e.children if c.local_id not in drop]
    for c in e.children:
        prune(c, drop)
    return e


_FONTS = {}


def _font(px, bold=True):
    px = max(6, int(px))
    key = (px, bold)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(r'C:\Windows\Fonts\bahnschrift.ttf', px)
    return _FONTS[key]


def render(img, root, texts=None, origin=(0.0, 0.0), k=1.0):
    """Draw an E tree (WoR desc semantics: pos from the parent's pos_anchor point, just = own anchor, Scale applies
    to children). texts: {local_id: text}. origin/k: canvas -> img."""
    texts = texts or {}
    items = []

    def walk(e, rect, psc, z0):
        if e.hidden or e.alpha <= 0:
            return
        x0, y0, w, h = rect
        px = x0 + (e.anchor[0] + 1) / 2 * w + e.pos[0] * psc[0]
        py = y0 + (e.anchor[1] + 1) / 2 * h + e.pos[1] * psc[1]
        sc = (psc[0] * e.scale[0], psc[1] * e.scale[1])
        ew, eh = e.dims[0] * sc[0], e.dims[1] * sc[1]
        ex, ey = px - (e.just[0] + 1) / 2 * ew, py - (e.just[1] + 1) / 2 * eh
        z = z0 + e.z
        if e.kind == 'SpriteElement':
            items.append((z, e, (ex, ey, ew, eh), (px, py)))
        elif e.kind == 'TextBlockElement' and e.local_id in texts:
            items.append((z, e, (ex, ey, ew, eh), (px, py)))
        for c in e.children:
            walk(c, (ex, ey, ew, eh), sc, z + 0.001)

    walk(root, (0, 0, 1280, 720), (1.0, 1.0), 0.0)
    for z, e, (ex, ey, ew, eh), (px, py) in sorted(items, key=lambda t: t[0]):
        X, Y, W, H = origin[0] + ex * k, origin[1] + ey * k, abs(ew) * k, abs(eh) * k
        if e.kind == 'SpriteElement':
            im = load_tex(e.extra.get('texture'))
            if im is None or W < 1 or H < 1:
                continue
            im = im.resize((max(1, int(W)), max(1, int(H))), Image.LANCZOS)
            if ew < 0:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            r, g, b, a = im.split()
            c = e.rgba
            im = Image.merge('RGBA', (r.point(lambda p: p * c[0] // 255), g.point(lambda p: p * c[1] // 255),
                                      b.point(lambda p: p * c[2] // 255), a.point(lambda p: int(p * c[3] / 255 * e.alpha))))
            if e.rot:
                pad = Image.new('RGBA', (im.width * 3, im.height * 3), (0, 0, 0, 0))
                pad.alpha_composite(im, (im.width, im.height))
                im = pad.rotate(-e.rot, resample=Image.BICUBIC)
                X, Y = X - W, Y - H
            if e.extra.get('blend') == 'Add':
                lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                lay.alpha_composite(im, (int(X), int(Y))) if X >= 0 and Y >= 0 else lay.paste(im, (int(X), int(Y)), im)
                from PIL import ImageChops
                rgb = Image.composite(lay, Image.new('RGBA', img.size, (0, 0, 0, 0)), lay).convert('RGB')
                rgb = Image.eval(rgb, lambda p: p)
                img.paste(ImageChops.add(img.convert('RGB'), ImageChops.multiply(rgb, lay.split()[3].convert('RGB'))).convert('RGBA'))
            else:
                lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                lay.paste(im, (int(X), int(Y)), im)
                img.alpha_composite(lay)
        else:
            text = texts[e.local_id]
            f = _font(eh * k * 0.8)
            d = ImageDraw.Draw(img)
            bb = d.textbbox((0, 0), text, font=f)
            tw = bb[2] - bb[0]
            tx = X + (W - tw) / 2 if e.extra.get('just_text', True) else X
            d.text((tx, Y + (H - (bb[3] - bb[1])) / 2 - bb[1]), text, font=f, fill=tuple(e.rgba[:3]) + (255,))


# ---- the player highway (from the mock base) with our in-game WoR HUD


def _player_tile():
    """(tile RGBA 1280x720, mask L) : the base's highway (and its WoR border) with the 1-player WoR HUD, cut out."""
    base = Image.open(BASE).convert('RGBA')
    hud = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    roots = preview_hud.hud_roots(game=True)
    preview_hud.GAME_TEXT['on'] = True
    preview_hud.draw(hud, roots, (0.0, 0.0), 1.0, preview_hud.state(1.6, 0.6, 4), additive=False)
    mask = Image.new('L', (1280, 720), 0)
    cl = lambda y: 352.5 + 0.518 * (710 - y) - 34          # border centre lines (tools/mock_base.py) + its width
    cr = lambda y: 927.5 - 0.517 * (710 - y) + 34
    ImageDraw.Draw(mask).polygon([(cl(292), 292), (cr(292), 292), (cr(720), 720), (cl(720), 720)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    tile = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    tile.paste(base, (0, 0), mask)
    tile.alpha_composite(hud)
    return tile


def _background():
    """The base's venue without the highway: its top band stretched and darkened."""
    base = Image.open(BASE).convert('RGB')
    top = base.crop((0, 0, 1280, 280)).resize((1280, 720), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    return Image.blend(top, Image.new('RGB', top.size, (0, 0, 0)), 0.35).convert('RGBA')


def place_players(img, tile, spots):
    """spots: [(centre x, scale)]: the 1-player tile (highway centred at x 640, bottom at 720) scaled about its
    bottom centre."""
    for cx, s in spots:
        t = tile.resize((int(1280 * s), int(720 * s)), Image.LANCZOS)
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        lay.paste(t, (int(cx - 640 * s), int(720 - 720 * s)), t)
        img.alpha_composite(lay)


# ---- WoR widgets per mode


def band_widgets(desc='hud_standard'):
    """The layout's band star meter and revive meter (the rest: career / power-up / challenge widgets, hidden)."""
    root = parse_desc(desc)
    keep = {'star_meter', 'HUD_revive_band_meter'}
    up = find(root, 'upper_container')
    up.children = [c for c in up.children if c.local_id in keep]
    root.children = [c for c in root.children if c.local_id == 'upper_container']
    sm = find(root, 'star_meter')
    prune(sm, {'Star_Earn_FX', 'star_tip_FX', 'FX_window', 'band_HUD_silver_star_frame', 'band_HUD_gold_star_glow'})
    return root, {'Score': '412,850', 'star_meter_num': '4', 'streak_number': '57'}


def versus_widgets(names=('PLAYER 1', 'PLAYER 2'), scores=('184,230', '171,905')):
    """Two competitive score rows (comp_scoreboard_player, as WoR's versus scoreboard lists them), top left."""
    roots = []
    for i, (n, sc) in enumerate(zip(names, scores)):
        r = parse_desc('comp_scoreboard_player')
        prune(r, {'elimination_icon', 'HUD_Sidebar_RankMeter'})
        r.pos = (60.0, 40.0 + 46 * i)
        r.scale = (0.8, 0.8)
        roots.append((r, {'gamertag': n, 'Score': sc}))
    return roots


def vocals_widget(img):
    """WoR's vocals highway desc (its notes and lyrics are drawn by script: a dark lane, sample phrase bars and
    placeholder lyrics stand in for them)."""
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for y in range(52, 262):
        a = int(150 * min(1, (y - 52) / 20, (262 - y) / 20))
        d.line([(0, y), (1279, y)], fill=(4, 6, 12, a))
    for k, x in enumerate(range(470, 1280, 170)):
        y = 95 + (k * 37) % 80
        d.rounded_rectangle((x, y, x + 130, y + 11), 5, fill=(70, 190, 255, 220))
    d.line([(408, 62), (408, 205)], fill=(255, 255, 255, 200), width=3)
    img.alpha_composite(lay)
    r = parse_desc('vocals_highway')
    if r is not None:
        render(img, r, {})
    d = ImageDraw.Draw(img)
    d.text((640, 222), 'la la la  oh  la la', anchor='mm', font=_font(26), fill=(255, 255, 255, 255))


MODES = {
    # key: (title, player spots [(cx, scale)], vocals highway, widgets)
    'faceoff': ('Face-off / Pro face-off (versus)', [(330, 0.62), (950, 0.62)], False, 'versus'),
    'battle': ('Battle (versus)', [(330, 0.62), (950, 0.62)], False, 'versus'),
    'band': ('Band: 3 instruments + vocals', [(250, 0.5), (640, 0.5), (1030, 0.5)], True, 'hud_standard'),
    'guitar_vocals': ('Guitar + vocals', [(640, 0.72)], True, 'hud_standard_1g1v'),
    'vocals': ('Vocals (microphone)', [], True, 'hud_standard_1v'),
}


def render_mode(key, tile, bg):
    title, spots, vocals, widgets = MODES[key]
    img = bg.copy()
    place_players(img, tile, spots)
    if vocals:
        vocals_widget(img)
    if widgets != 'versus':
        r, t = band_widgets(widgets)
        render(img, r, t)
    else:
        for r, t in versus_widgets():
            render(img, r, t)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 692, 1279, 719), fill=(0, 0, 0, 210))
    d.text((12, 699), f'{title}  |  mock: WoR widgets from WoR descs, per-player WoR HUD from the 1-player theme, '
                      f'highway spots approximate', fill=(235, 235, 235, 255), font=_font(14))
    return img


def main():
    out = sys.argv[1]
    keys = sys.argv[2:] or ['faceoff', 'band', 'guitar_vocals', 'vocals']
    tile, bg = _player_tile(), _background()
    tiles = [render_mode(k, tile, bg) for k in keys]
    cols = 2 if len(tiles) > 1 else 1
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new('RGB', (1280 * cols, 720 * rows), (0, 0, 0))
    for i, t in enumerate(tiles):
        sheet.paste(t.convert('RGB'), ((i % cols) * 1280, (i // cols) * 720))
    sheet.save(out, quality=90)
    print('wrote', out)


if __name__ == '__main__':
    main()
