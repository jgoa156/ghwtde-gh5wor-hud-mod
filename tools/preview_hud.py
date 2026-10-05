"""Offline mock of the generated WoR 1-player HUD: draws every sprite/text of the generated descs onto a game
screenshot (or a blank 16:9 frame) with simulated DE values, using the GUI rules the descs rely on
(just = anchor, rotation about Pos, container Scale applies to child positions). No game launch needed.

usage: python preview_hud.py <screenshot or -> <out.png> [health 0..2] [sp 0..1] [mult]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desc_gen, wor_1g  # noqa: E402

PREVIEW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'preview')


def load_tex(name):
    p = os.path.join(PREVIEW, name + '.png')
    return Image.open(p).convert('RGBA') if os.path.exists(p) else None


_FONT = {}


def wor_text(text):
    """Text rendered with the shipped WoR numeral font (white glyphs on transparent), or None if not built."""
    import glob
    import font_render
    if 'path' not in _FONT:
        hits = glob.glob(os.path.join(PREVIEW, '..', 'pak_src', '*', wor_1g.SCORE_FONT + '.fnt.xen'))
        _FONT['path'] = hits[0] if hits else None
    if not _FONT['path']:
        return None
    return font_render.render(_FONT['path'], text, bg=(0, 0, 0, 0))


# Measured offset of the game's rendering from this mock (canvas units), per desc, from the v0.17 in-game capture
# (OneDrive\Videos\GH5\modded.mp4, aligned to the canvas by the fret rings): used with --game so the mock
# predicts where the game will actually draw.
# Text: the mock draws WoR-font text slightly larger than the game (same threshold measurement on the v0.17
# capture: score 14 vs 13 px, streak 13 vs 12, star count 17 vs 15) and the streak digits 2 low / 2 right.
TEXT_CALIB = {'Score': (1 / 1.08, (0.0, 0.0)), 'streak_number': (1 / 1.08, (-2.0, -2.5)),
              'star_meter_num': (1 / 1.13, (0.0, 0.0))}
GAME_TEXT = {'on': False}
GAME_CALIB = {'wor_band_meter_1g_ghwor': (1.0, 3.0), 'wor_mult_1g_ghwor': (1.0, 9.0),
              'wor_side_meter_ghwor': (1.0, 9.0)}


def state(health, sp, mult):
    """Prop values the DE would set: local_id -> {field: value}."""
    v = {}
    lights = {'red_light': health < 0.6666, 'yellow_light': 0.6666 <= health < 1.3333, 'green_light': health >= 1.3333}
    for k, on in lights.items():
        v[k] = {'alpha': 1.0 if on else 0.0}
    # side meter needle: piecewise path of script 0x3205f550 (1 non-vocal player)
    pts = [(0, 0), (11, -24), (28, -57), (41, -80)]
    seg = min(2, int(health / 0.6667))
    f = min(1.0, max(0.0, (health - seg * 0.6667) / 0.6667))
    a, b = pts[seg], pts[seg + 1]
    v['side_meter_needle'] = {'pos': (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)}
    for i in range(6):
        fill = min(1.0, max(0.0, sp * 6 - i))
        v[f'sp_seg{i}'] = {'scale': (wor_1g.SP_DEFAULT_SCALE, wor_1g.SP_DEFAULT_SCALE * fill)}   # DE: (default.x, default.y*fill)
    v['nixie'] = {'texture': f'WoR_HUD_mult_{mult}'}
    col = {1: '', 2: '_green', 3: '_purple', 4: '_purple'}.get(mult, '')
    for i, st in enumerate((2, 2, 2, 1, 0)):
        v[f'light{i}'] = {'texture': f'HUD_score_light_{st}{col}'}
    v['songtime_fg'] = {'scale': (150.0, 1.0)}
    v['Score'] = {'text': '45625'}
    v['streak_number'] = {'text': '135'}
    v['star_meter_num'] = {'text': '3'}
    v['star_filler'] = {'scale': (0.7 * 0.55, 1.0)}
    return v


def draw(img, root, origin, k, vals, additive=True):
    """origin: canvas->image transform (ox, oy); k: canvas->image scale."""
    font_cache = {}

    def font(px):
        px = max(6, int(px))
        if px not in font_cache:
            font_cache[px] = ImageFont.truetype(r'C:\Windows\Fonts\bahnschrift.ttf', px)
        return font_cache[px]

    items = []

    import math

    def rotv(v, deg):
        a = math.radians(deg)
        return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))

    def walk(e, base, psc, z0, prot=0.0):
        st = vals.get(e.local_id, {})
        pos = st.get('pos', e.pos)
        off = rotv((pos[0] * psc[0], pos[1] * psc[1]), prot)
        wp = (base[0] + off[0], base[1] + off[1])
        sc = st.get('scale', e.scale)
        z = z0 + e.z
        if e.kind == 'SpriteElement' and not e.hidden:
            items.append((z, 'sprite', e, wp, (sc[0] * psc[0], sc[1] * psc[1]), dict(st, _rot=prot + e.rot)))
        if e.kind == 'TextBlockElement' and not e.hidden and e.alpha > 0:
            items.append((z, 'text', e, wp, (sc[0] * psc[0], sc[1] * psc[1]), st))
        csc = (psc[0] * sc[0], psc[1] * sc[1]) if e.kind == 'ContainerElement' else psc
        crot = prot + (e.rot if e.kind == 'ContainerElement' else 0.0)
        # children are positioned from the container's top-left corner (confirmed in game, v0.7 streak box)
        o = rotv((-(e.just[0] + 1) / 2 * e.dims[0] * csc[0], -(e.just[1] + 1) / 2 * e.dims[1] * csc[1]), crot)
        origin = (wp[0] + o[0], wp[1] + o[1])
        for c in e.children:
            walk(c, origin, csc, z + 0.001, crot)

    for base, r in root:
        walk(r, base, (1.0, 1.0), 0.0)
    for z, kind, e, wp, sc, st in sorted(items, key=lambda t: t[0]):
        alpha = st.get('alpha', e.alpha)
        if alpha <= 0:
            continue
        flip = sc[0] < 0
        w, h = e.dims[0] * abs(sc[0]) * k, e.dims[1] * abs(sc[1]) * k
        cx, cy = origin[0] + wp[0] * k, origin[1] + wp[1] * k
        if kind == 'sprite':
            tex = st.get('texture', e.extra.get('texture'))
            im = load_tex(tex) if tex else Image.new('RGBA', (8, 8), (255, 255, 255, 255))
            if im is None or w < 1 or h < 1:
                continue
            im = im.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
            if flip:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            rgba = st.get('rgba', e.rgba)
            if tuple(rgba) != (255, 255, 255, 255):
                r, g, b, a = im.split()
                im = Image.merge('RGBA', (r.point(lambda p: p * rgba[0] // 255), g.point(lambda p: p * rgba[1] // 255),
                                          b.point(lambda p: p * rgba[2] // 255), a))
            if alpha < 1:
                im.putalpha(im.split()[3].point(lambda p: int(p * alpha)))
            # anchor offset (just) then rotate about the anchor point
            ax, ay = (e.just[0] + 1) / 2 * im.width, (e.just[1] + 1) / 2 * im.height
            pad = int(max(im.size) * 1.5) + 4
            canvas = Image.new('RGBA', (pad * 2, pad * 2), (0, 0, 0, 0))
            canvas.alpha_composite(im, (int(pad - ax), int(pad - ay)))
            canvas = canvas.rotate(-st.get('_rot', e.rot), resample=Image.BICUBIC, center=(pad, pad))
            if additive and e.extra.get('blend') == 'Add':
                base = img.crop((int(cx - pad), int(cy - pad), int(cx - pad) + pad * 2, int(cy - pad) + pad * 2))
                from PIL import ImageChops
                prem = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
                prem.paste(canvas, (0, 0), canvas)
                added = ImageChops.add(base.convert('RGB'), Image.composite(prem, Image.new('RGBA', canvas.size), canvas).convert('RGB'))
                img.paste(added, (int(cx - pad), int(cy - pad)))
            else:
                img.alpha_composite(canvas, (int(cx - pad), int(cy - pad))) if cx - pad >= 0 and cy - pad >= 0 else \
                    img.paste(canvas, (int(cx - pad), int(cy - pad)), canvas)
        else:
            text = st.get('text', '')
            if not text:
                continue
            strip = wor_text(text) if e.extra.get('font') == wor_1g.SCORE_FONT else None
            if strip is not None and GAME_TEXT['on'] and e.local_id in TEXT_CALIB:
                tk, toff = TEXT_CALIB[e.local_id]
                sc = (sc[0] * tk, sc[1] * tk)
                cx, cy = cx + toff[0] * k, cy + toff[1] * k
            if strip is not None:
                # the game draws glyph cells 1:1 at the element scale, text aligned by just inside the block
                tw, th = strip.width * abs(sc[0]) * k, strip.height * abs(sc[1]) * k
                im = strip.resize((max(1, int(round(tw))), max(1, int(round(th)))), Image.LANCZOS)
                rgba = st.get('rgba', e.rgba)
                r, g, b, a = im.split()
                im = Image.merge('RGBA', (r.point(lambda p: p * rgba[0] // 255), g.point(lambda p: p * rgba[1] // 255),
                                          b.point(lambda p: p * rgba[2] // 255),
                                          a.point(lambda p: int(p * alpha * rgba[3] / 255))))
                x = cx - (e.just[0] + 1) / 2 * im.width
                y = cy - (e.just[1] + 1) / 2 * im.height
                img.alpha_composite(im, (int(round(x)), int(round(y))))
                continue
            f = font(36 * sc[1] * k)
            d = ImageDraw.Draw(img)
            bb = d.textbbox((0, 0), text, font=f)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            x = cx - (e.just[0] + 1) / 2 * tw
            y = cy - (e.just[1] + 1) / 2 * th - bb[1]
            d.text((x, y), text, font=f, fill=tuple(e.rgba[:3]) + (int(255 * alpha),))


def hud_roots(game=False):
    """(base, root) for the three generated HUD descs; game=True adds the measured in-game offsets."""
    wor_1g.all_descs()
    R = desc_gen.ROOTS
    g1 = wor_1g.G1
    out = []
    for name, base in (('wor_band_meter_1g_ghwor', (0.0, 0.0)), ('wor_mult_1g_ghwor', g1), ('wor_side_meter_ghwor', g1)):
        GAME_TEXT['on'] = game
        c = GAME_CALIB[name] if game else (0.0, 0.0)
        out.append(((base[0] + c[0], base[1] + c[1]), R[name]))
    return out


def render(src, out, health=1.6, sp=0.6, mult=4, game=False):
    """Draw the generated HUD on src (a screenshot, or '-' for a blank frame) and save it to out."""
    if src == '-':
        img = Image.new('RGBA', (1280, 720), (40, 40, 48, 255))
    else:
        img = Image.open(src).convert('RGBA')
    # The game maps the 1280x720 HUD canvas onto the whole window (ultrawide stretches it horizontally, the 2D
    # highway too), so draw on a canvas-sized layer and stretch that layer onto the screenshot.
    roots = hud_roots(game)
    GAME_TEXT['on'] = game
    if img.size == (1280, 720):
        # canvas-sized frame: draw straight onto it so 'Add' sprites (glows, star power fill) blend like in game
        draw(img, roots, (0.0, 0.0), 1.0, state(health, sp, mult), additive=True)
    else:
        layer = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        draw(layer, roots, (0.0, 0.0), 1.0, state(health, sp, mult), additive=False)
        img.alpha_composite(layer.resize(img.size, Image.LANCZOS))
    img.convert('RGB').save(out)
    print('wrote', out)


def main():
    game = '--game' in sys.argv
    argv = [a for a in sys.argv if a != '--game']
    render(argv[1], argv[2], float(argv[3]) if len(argv) > 3 else 1.6, float(argv[4]) if len(argv) > 4 else 0.6,
           int(argv[5]) if len(argv) > 5 else 4, game)


if __name__ == '__main__':
    main()
