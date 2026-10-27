"""Singleplayer vocals in the WoR style (user-approved mock docs/mocks/mock_vocals_v2.jpg, research
docs/research/wor_vocals_hud.md).

WoR draws the vocalist's meters as one panel on the vocal highway's top edge (uidesc_vocals_all_meters): a backing with
a blue colour stripe, the health meter (three lamps + a needle sliding with health), the multiplier ("x4" in WoR's text
font on HUD_meter_combovocal), the phrase meter box, and the star power strip lying on the highway's top line. The
geometry is the mock's (measured on the WoR video, 1280x720 canvas), every texture is WoR's own.

The DE wires a vocalist through three children of the layout's v1 container (scripts/guitar/hud/guitar_hud.qb
585-609), so the panel is three descs placed there, each answering one DE widget:
  player_meter          HUD_attach_widget_player_multiplier: semultipliernixie -> nixie_texture, from the theme's
                        vocalist arrays 112feba3 / bc95780d (our "x1".."x4" / star power "x2".."x8" images)
  BAND_top_meter        HUD_attach_widget_player_health Vocals=1: side_meter_needle_pos (0,-105)..(0,-5) for health
                        0..2, TOP_meter_red / yellow / green_ON_alpha. The needle's anchor is turned -90 deg so the
                        DE's vertical range slides it along WoR's horizontal health meter (x -55..28 meter units).
  vocal_multiplier_star HUD_attach_widget_player_star_power: setubes on starpower_amount -> glow0..2_scale. Three
                        segments of the strip, each in a container turned -90 deg so the DE's fill (its y scale) runs
                        along the strip.
The score group is the quickplay one (wor_band.score_desc) at WoR's vocals spot. The vocal highway is our copy of the
DE's vocals_highway_wtde (theme field 0x3fb45eb1), moved down to WoR's place (WoR's root is at y 32, the DE's at 0).
"""
import os

from PIL import Image

import paths
from desc_gen import E, desc

UI = os.path.join(paths.WOR_EXTRACT, 'ui_shared_png2')
ZIG = os.path.join(paths.WOR_EXTRACT, 'z_in_game_png2')
# our texture name -> WoR art
ART = {
    'WoR_HUD_v_backing': (UI, 'vocal_meter_backing'),
    'WoR_HUD_v_div': (UI, 'vocal_meter_backing_div'),
    'WoR_HUD_v_stripe': (UI, 'vocal_meter_color_stripe'),
    'WoR_HUD_v_health': (UI, 'vocal_health_meter'),
    'WoR_HUD_v_red': (UI, 'vocal_health_meter_red'),
    'WoR_HUD_v_amber': (UI, 'vocal_health_meter_amber'),
    'WoR_HUD_v_green': (UI, 'vocal_health_meter_green'),
    'WoR_HUD_v_needle': (UI, 'vocal_health_meter_needle'),
    'WoR_HUD_v_sheen': (UI, 'vocal_health_meter_sheen'),
    'WoR_HUD_v_combo': (UI, 'HUD_meter_combovocal'),
    'WoR_HUD_v_tube': (UI, 'vocal_starpower_tube'),
    'WoR_HUD_v_cap': (UI, 'vocals_meter_cap'),
}
SP_FILL = 'WoR_HUD_v_spfill'                 # vocals_meter_cap tinted WoR's star power blue, turned for the segments
SP_RGB = (0, 166, 255)                       # vocals_star_power_meter vocal_starpower_fill rgba
FRAME_BLUE = (77, 95, 153)                   # vocals_hud_rgba[band 1]: the colour stripe
# multiplier colours (vocals_multiplier, secombolights): x1..x4, and star power
MULT_RGB = {1: (255, 180, 180), 2: (243, 169, 64), 3: (128, 236, 68), 4: (175, 101, 238)}
MULT_SP_RGB = (225, 240, 150)
MULT_TEX = {n: f'WoR_HUD_vmult_{n}' for n in (1, 2, 3, 4)}
MULT_SP_TEX = {n: f'WoR_HUD_vmult_sp{n}' for n in (2, 4, 6, 8)}
# the "xN" image (mock docs/mocks/mock_vocals_mult_v1.jpg, user 2026-10-27: "not wide enough and the colour is wrong"):
# WoR's x (~12 tall, bottom left) and digit (~20 tall, its text font 1.2 wide + numeral_A1_b at 0.3 on top) fill the
# box; pale digit with a glow in the multiplier colour, coloured x, on a dark box tinted the same way. The box is
# baked into each image (the combo sprite is hidden). (x colour, digit fill, glow, box tint), measured for x4 and x8.
MULT_STYLE = {
    1: ((235, 150, 150), (255, 228, 228), (235, 120, 120), (52, 36, 38)),
    2: ((243, 160, 60), (255, 232, 196), (243, 150, 50), (54, 42, 30)),
    3: ((110, 220, 70), (226, 255, 210), (100, 220, 60), (36, 50, 34)),
    4: ((150, 100, 235), (238, 212, 255), (175, 101, 238), (46, 36, 62)),
    'sp': ((150, 235, 150), (228, 252, 222), (80, 210, 85), (34, 42, 44)),
}

# ---- geometry (canvas, the mock's boxes: a texture's opaque bounding box is fitted to each)
BACKING = (141, 457, 386, 494)
STRIPE = (141, 457, 386, 474)
DIVIDERS = (238.5, 281.5)                    # x centres, 5 wide, y 461..489
HEALTH = (148, 462, 234, 487)
GREEN = (205, 463, 233, 486)                 # the green lamp; red / amber at WoR's offsets in the meter art
LAMP_DX = {'red': -34.9185 - 24.1856, 'amber': -5.58585 - 24.1856, 'green': 0.0}   # vocals_health_meter, meter texels
NEEDLE = (226, 474, 235, 488)                # at full health
NEEDLE_RANGE = 28.0 - (-55.0)                # meter units for health 0..2 (HUD_attach_widget_vocal_sp_combo_meter)
SHEEN = (148, 462, 236, 475)
COMBO = (241, 463, 279, 487)
MULT_BOX = (241, 465, 281, 485)              # the "xN" image (40 x 20 canvas = 128 x 64 texels)
PHRASE = (285, 465, 378, 487)
# star power strip (mock v5, user 2026-10-26): 9 tall (was 8) and 1 up, a dark border with a light top lip, the 50 %
# mark 5 wide, drawn over the highway's top line
SP_CAP = (145, 491.0, 383, 500.0)
SP_FILL_X, SP_FILL_Y = (147.0, 381.0), (493.0, 498.0)
SP_MARK = (262.0, 491.0, 267.0, 500.0)       # the strip's 50 % mark
SP_BORDER = (144, 490.0, 384, 501.0)
SP_BORDER_TEX = 'WoR_HUD_v_spborder'
SP_Z = 4.0                                   # above the vocal highway's lines (its outline sprites: z 2)
# health meter (mock v5): an inner shadow (top + left) and a white gloss over the meter, and a blurred inner shadow in
# each lamp cell
METER_SHADE = 'WoR_HUD_v_meter_shade'
LAMP_SHADE = 'WoR_HUD_v_lamp_shade'
SP_SEGS = 3                                  # the DE's setubes on a vocalist: glow0..2
# the v1 container draws at its layout spot (95, 72) + the container calibration (wor_mp.G_CAL): our descs carry canvas
# coordinates, so their instances sit at minus that
V1_POS = (95.0, 72.0)
# the score group: WoR's vocals spot (the mock: our guitar + vocals group moved by (-56.67, +223.33))
SCORE_POS = (17.058 - 56.67, -363.2697 + 223.33)
VH_NAME = 'vocals_highway_ghwor'
# the root moves down so the silver lines land on WoR's canvas y 494 / 596 (WoR's own root is at y 32; ours draws 3
# units lower than WoR's for the same root, measured: the DE's lines at 464 / 567 with root y 0)
VH_DY = 29.0
# lyric band: WoR's dark band at canvas y 600..632 with the words centred at ~617 (the DE: a 0.4 alpha band 39 tall a
# little lower, words centred ~11 units lower); desc y = canvas y - 430 (the DE's 1-player instance) - VH_DY
LYRIC_BAND_Y, LYRIC_BAND_H, LYRIC_BAND_A = 141.0, 32.0, 0.9
LYRICS_Y = 142.0
COMET_SCALE = 0.35                           # WoR's fireball_bg (the DE's: 0.55)
# the now line (mock v3, user 2026-10-26): WoR's green crackling lightning, cyan in star power; ours rides in
# pitch_area (x centre 10) from the top line to the bottom one (now_bar y 30 + pitch_area y 18 = 48 below the root;
# the lines' centres at root y 35 / 137). NOW_FRAMES bolts per colour, the plugin (1.58) steps through them.
NOW_FRAMES = 4
NOW_TEX = [f'WoR_HUD_vnow_g{i}' for i in range(NOW_FRAMES)]
NOW_SP_TEX = [f'WoR_HUD_vnow_c{i}' for i in range(NOW_FRAMES)]
NOW_GLOW, NOW_CORE = (20, 200, 20), (190, 255, 150)
NOW_SP_GLOW, NOW_SP_CORE = (0, 190, 255), (210, 255, 255)
NOW_BOX = (10.0, 35.0 - 48.0, 28.0, 137.0 - 35.0)   # (x centre, top, width, height) in pitch_area
# white arrowheads on both lines at the now line (mock v4: 10 x 13, on the lines, over the lightning)
SPIKE_TEX = {'down': 'WoR_HUD_vspike_down', 'up': 'WoR_HUD_vspike_up'}
SPIKE_W, SPIKE_H = 10.0, 13.0
# star power (mock v3): a cyan glow band on the top line and along the lyric band's bottom edge, in the root (the top
# line spans root x -221..880; the lyric band's bottom edge is at root y 157)
SP_GLOW_TEX = 'WoR_HUD_vsp_glow'
SP_GLOW_X = (-221.0, 880.0)
SP_GLOW_Y = (35.0, 157.0)
SP_GLOW_H = 26.0
# the highway's background (the DE: white 0.3 tinted teal by its bg_rgba prop): WoR's dim dark
HIGHWAY_BG_RGBA, HIGHWAY_BG_ALPHA = (0, 0, 0, 255), 0.45
# notes (mock v5): WoR's thin yellow outline, rectangular, with a warm blur. The DE draws a note as one sprite with
# the theme's sung-note texture (field c5e00a8d, a 32-row profile: tube rows 7..24) stretched along it, so the end
# edges are in the texture: one texture per length band (the plugin picks the band from the sprite's width on screen),
# each with ends ~3 canvas units wide. The connector between notes (field f6faf84b) is blank like WoR.
NOTE_W = 256
NOTE_BANDS = [12.0 * 2 ** (i / 2) for i in range(12)]      # lower edges of the length bands, canvas units
NOTE_TEX = [f'WoR_HUD_vnote_{i}' for i in range(len(NOTE_BANDS))]
NOTE_RGB, NOTE_CORE, NOTE_GLOW = (255, 244, 60), (255, 255, 190), (255, 215, 70)
NOTE_EDGE = 3.0                                             # outline thickness, canvas units
NOTE_H_CANVAS = 15.0                                        # vocal_sung_note_height
# lyrics (mock v3): WoR's scale 0.4 (the DE: 0.55 x 0.75); sung words WoR blue, the current one WoR yellow
LYRIC_SCALE = (0.4, 0.4)
LYRIC_RGBA = {'upcoming': (236, 236, 236, 255), 'current': (254, 233, 53, 255), 'sung': (120, 112, 245, 255)}
LYRIC_RGBA_DE = {'upcoming': (200, 200, 200, 255), 'current': (240, 60, 240, 255), 'sung': (64, 64, 64, 255)}
LYRIC_SCALE_DE = (0.55, 0.75)
LYRIC_FONT = 'WoR_HUD_lyric_a1'
FONT_SRC = {LYRIC_FONT: paths.wor('ui_shared', 'fontgrid_lyric_a1.fnt.xen')}

HEALTH_NAME, MULT_NAME, SP_NAME = 'wor_vocal_health_ghwor', 'wor_vocal_mult_ghwor', 'wor_vocal_sp_ghwor'


def _png(name):
    d, n = ART[name]
    return Image.open(os.path.join(d, n + '.png')).convert('RGBA')


def _fit(lid, tex, box, z, **kw):
    """A sprite whose texture's opaque bounding box lands on canvas box (x0, y0, x1, y1)."""
    im = _png(tex) if tex in ART else None
    w, h = im.size
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox() or (0, 0, w, h)
    sx, sy = (box[2] - box[0]) / (bb[2] - bb[0]), (box[3] - box[1]) / (bb[3] - bb[1])
    return E(lid, 'SpriteElement', pos=(box[0] - bb[0] * sx, box[1] - bb[1] * sy), dims=(w * sx, h * sy), just=(-1, -1),
             z=z, texture=tex, **kw)


def _texel_scale(tex, box):
    im = _png(tex)
    bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    return (box[2] - box[0]) / (bb[2] - bb[0])


def _sink(lid, kind='SpriteElement'):
    return E(lid, kind, dims=(4, 4), alpha=0.0, texture='WoR_HUD_blank')


def _centre(box):
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def health_desc():
    s = _texel_scale('WoR_HUD_v_health', HEALTH)
    gx, gy = _centre(GREEN)
    gw, gh = GREEN[2] - GREEN[0], GREEN[3] - GREEN[1]
    lamps = []
    for c, a in (('red', 0.0), ('amber', 1.0), ('green', 0.0)):           # a song starts at health 1 (amber)
        cx = gx + LAMP_DX[c] * s
        lamps.append(_fit(f'lamp_{c}', f'WoR_HUD_v_{c}', (cx - gw / 2, gy - gh / 2, cx + gw / 2, gy + gh / 2), 0.14,
                          alpha=a, blend='Add'))
    # needle: health 2 at NEEDLE, health 0 NEEDLE_RANGE meter units left; the DE moves needle_src from (0,-105) to
    # (0,-5) in an anchor turned -90 deg (child (0, y) -> screen (y, 0)) and scaled k
    k = NEEDLE_RANGE * s / 100.0
    nx2, ny = _centre(NEEDLE)
    anchor_x = (nx2 - NEEDLE_RANGE * s) + 105.0 * k
    nd = _fit('needle', 'WoR_HUD_v_needle', NEEDLE, 0.5)
    nd.pos, nd.just, nd.rot = (0.0, 0.0), (0, 0), 90.0
    nd.dims = (nd.dims[0] / k, nd.dims[1] / k)
    src = E('needle_src', 'ContainerElement', pos=(0.0, -5.0), dims=(4, 4), just=(0, 0), z=0.5, children=[nd])
    anchor = E('needle_anchor', 'ContainerElement', pos=(anchor_x, ny), dims=(4, 4), just=(0, 0), scale=(k, k),
               rot=-90.0, z=0.5, children=[src])
    # inner shadows: one over the meter (top + left edge, and the gloss), one per lamp cell, both above the lamps
    shades = [E('meter_shade', 'SpriteElement', pos=(HEALTH[0], HEALTH[1]), dims=(HEALTH[2] - HEALTH[0], HEALTH[3] - HEALTH[1]),
                just=(-1, -1), z=0.145, texture=METER_SHADE)]
    for c in ('red', 'amber', 'green'):
        cx = gx + LAMP_DX[c] * s
        shades.append(E(f'lamp_shade_{c}', 'SpriteElement', pos=(cx, gy), dims=(gw, gh), just=(0, 0), z=0.146,
                        texture=LAMP_SHADE))
    kids = [_fit('meter', 'WoR_HUD_v_health', HEALTH, 0.13), *lamps, *shades, anchor,
            _fit('sheen', 'WoR_HUD_v_sheen', SHEEN, 0.15, alpha=0.7),
            _sink('red_rgba_sink'), _sink('red_glow_sink')]
    root = E('vocal_health', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)
    props = [('side_meter_needle_pos', 'needle_src', 'Pos'), ('side_meter_needle_scale', 'needle_src', 'Scale'),
             ('TOP_meter_red_ON_alpha', 'lamp_red', 'alpha'), ('TOP_meter_yellow_ON_alpha', 'lamp_amber', 'alpha'),
             ('TOP_meter_green_ON_alpha', 'lamp_green', 'alpha'),
             ('TOP_meter_red_ON_rgba', 'red_rgba_sink', 'rgba'), ('top_red_glow_rgba', 'red_glow_sink', 'rgba')]
    return desc(HEALTH_NAME, root, props)


def mult_desc():
    kids = [_fit('backing', 'WoR_HUD_v_backing', BACKING, 0.10),
            _fit('stripe', 'WoR_HUD_v_stripe', STRIPE, 0.12, rgba=FRAME_BLUE + (255,)),
            *[_fit(f'div{i}', 'WoR_HUD_v_div', (x - 2.5, 461, x + 2.5, 489), 0.11) for i, x in enumerate(DIVIDERS)],
            # the box is baked into the "xN" images (MULT_STYLE): the combo art only under them
            _fit('combo', 'WoR_HUD_v_combo', COMBO, 0.13, alpha=0.0),
            E('nixie', 'SpriteElement', pos=COMBO[:2], dims=(COMBO[2] - COMBO[0], COMBO[3] - COMBO[1]),
              just=(-1, -1), z=0.2, texture=MULT_TEX[1]),
            _fit('phrase_tube', 'WoR_HUD_v_tube', PHRASE, 0.13),
            _sink('nixie_rgba_sink'), _sink('mult_bg_sink')]
    sinks = [_sink(f'light{i}_sink') for i in range(5)]
    kids += sinks + [_sink('streak_text_sink', 'SpriteElement')]
    root = E('vocal_mult', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)
    props = [('nixie_texture', 'nixie', 'texture'), ('nixie_rgba', 'nixie_rgba_sink', 'rgba'),
             ('mult_bg_alpha', 'mult_bg_sink', 'alpha')]
    props += [(f'light{i}_texture', f'light{i}_sink', 'texture') for i in range(5)]
    return desc(MULT_NAME, root, props)


def sp_desc():
    x0, x1 = SP_FILL_X
    y0, y1 = SP_FILL_Y
    seg = (x1 - x0) / SP_SEGS
    kids = [_fit('cap', 'WoR_HUD_v_cap', SP_CAP, 0.12),
            E('mark', 'SpriteElement', pos=SP_MARK[:2], dims=(SP_MARK[2] - SP_MARK[0], SP_MARK[3] - SP_MARK[1]),
              just=(-1, -1), z=0.16, rgba=(20, 20, 24, 255), texture='WoR_HUD_v_cap'),
            E('border', 'SpriteElement', pos=SP_BORDER[:2], dims=(SP_BORDER[2] - SP_BORDER[0], SP_BORDER[3] - SP_BORDER[1]),
              just=(-1, -1), z=0.17, texture=SP_BORDER_TEX)]
    for i in range(SP_SEGS):
        # child (x, y) -> screen (y, -x): the sprite's height runs right along the strip, its width across it
        fill = E(f'glow{i}', 'SpriteElement', pos=(0.0, 0.0), dims=(y1 - y0, seg), just=(0, -1), scale=(1.0, 0.0),
                 z=0.14, rgba=SP_RGB + (255,), texture=SP_FILL, blend='Add')
        kids.append(E(f'seg{i}', 'ContainerElement', pos=(x0 + i * seg, (y0 + y1) / 2), dims=(4, 4), just=(0, 0),
                      rot=-90.0, z=0.14, children=[fill]))
        kids.append(_sink(f'glow{i}_tex_sink'))
    root = E('vocal_sp', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)
    props = []
    for i in range(SP_SEGS):
        props += [(f'glow{i}_scale', f'glow{i}', 'Scale'), (f'glow{i}_texture', f'glow{i}_tex_sink', 'texture')]
    return desc(SP_NAME, root, props)


def descs():
    return [health_desc(), mult_desc(), sp_desc()]


def _font(name):
    """A WoR font converted to the PC format (cached under build/fonts_cache)."""
    import wor_font
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'fonts_cache', name + '.fnt.xen')
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        wor_font.convert(paths.wor('ui_shared', name + '.fnt.xen'), out)
    return out


def _glyphs(font, s, h, rgb, kx=1.0):
    import mock_fail_popup as fonts
    t = fonts.text(font, s, 160, rgb)
    t = t.crop(t.getbbox())
    return t.resize((max(1, round(t.width * h / t.height * kx)), h), Image.LANCZOS)


def _mult_image(n, style):
    """The "xN" image with its box (MULT_STYLE), drawn at 6 texels per canvas unit over the COMBO box (38 x 24)."""
    from PIL import ImageDraw, ImageFilter
    xc, fill, glow, tint = MULT_STYLE[style]
    S = 6
    W, H = round((COMBO[2] - COMBO[0]) * S), round((COMBO[3] - COMBO[1]) * S)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((0, 0, W - 1, H - 1), 4 * S, fill=tint + (255,))
    d.rounded_rectangle((S, S, W - 1 - S, H // 2), 3 * S, fill=tuple(min(255, c + 14) for c in tint) + (255,))
    text, num_b = _font('fontgrid_text_a1'), _font('fontgrid_numeral_A1_b')
    x = _glyphs(text, 'x', 12 * S, xc)
    dg = _glyphs(text, str(n), 20 * S, fill, kx=1.2)
    over = _glyphs(num_b, str(n), 20 * S, (255, 255, 255), kx=1.2).resize(dg.size, Image.LANCZOS)
    over.putalpha(over.getchannel('A').point(lambda v: int(v * 0.3)))
    dg.alpha_composite(over)
    dx, dy = W - dg.width - 3 * S, (H - dg.height) // 2
    a = Image.new('L', (W, H), 0)
    a.paste(dg.getchannel('A'), (dx, dy))
    a = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(6.6))
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), c) for c in glow] + [a.point(lambda v: min(255, v * 2))]))
    out.alpha_composite(dg, (dx, dy))
    out.alpha_composite(x, (2 * S, H - x.height - 3 * S))
    return out.resize((256, 128), Image.LANCZOS)


def _lightning(core, halo, seed):
    """One frame of the now line: a jagged bolt with a soft halo (64 x 256 texels over NOW_BOX's 28 x 102 units)."""
    import random
    from PIL import ImageDraw, ImageFilter
    W, H = 64, 256
    kx = W / NOW_BOX[2]
    rnd = random.Random(seed)
    pts, y = [], 0.0
    while y < H:
        pts.append((W / 2 + rnd.uniform(-2.2, 2.2) * kx, y))
        y += rnd.uniform(3, 7) * H / NOW_BOX[3]
    pts.append((W / 2, H))

    def layer(width, blur, rgb, k):
        m = Image.new('L', (W, H), 0)
        ImageDraw.Draw(m).line(pts, fill=255, width=max(1, round(width * kx)))
        m = m.filter(ImageFilter.GaussianBlur(blur * kx)).point(lambda v: min(255, int(v * k)))
        return Image.merge('RGBA', [Image.new('L', (W, H), c) for c in rgb] + [m])
    out = layer(10, 7, halo, 1.4)
    out.alpha_composite(layer(3, 1.2, halo, 2.0))
    out.alpha_composite(layer(1, 0.4, core, 2.5))
    return out


def _spike(direction):
    """WoR's white arrowhead (vocal_health_meter_needle's shape), 40 x 52 texels, pointing down or up."""
    from PIL import ImageDraw
    w, h = 40, 52
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon(((0, 0), (w, 0), (w / 2, h)), fill=(150, 150, 155, 255))
    d.polygon(((8, 0), (w - 8, 0), (w / 2, h - 12)), fill=(255, 255, 255, 255))
    return im if direction == 'down' else im.transpose(Image.FLIP_TOP_BOTTOM)


def _sp_glow():
    """A soft horizontal cyan band (32 x 64): the star power glow on a line."""
    from PIL import ImageDraw, ImageFilter
    m = Image.new('L', (32, 64), 0)
    ImageDraw.Draw(m).rectangle((0, 28, 31, 35), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v * 1.8)))
    core = Image.new('L', (32, 64), 0)
    ImageDraw.Draw(core).rectangle((0, 30, 31, 33), fill=255)
    core = core.filter(ImageFilter.GaussianBlur(1))
    out = Image.merge('RGBA', [Image.new('L', (32, 64), c) for c in NOW_SP_GLOW] + [m])
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', (32, 64), c) for c in (150, 250, 255)] + [core]))
    return out


def _note(i):
    """Note texture for length band i: the DE's 32-row profile (tube rows 7..24) as WoR's yellow outline with a warm
    blur, end edges NOTE_EDGE units wide for a note of the band's middle length."""
    from PIL import ImageDraw, ImageFilter
    W, H = NOTE_W, 32
    S = 4                                                    # drawn at 4x
    mid = NOTE_BANDS[i] * 2 ** 0.25                          # geometric middle of the band
    k = H / (NOTE_H_CANVAS * 32 / 17)                        # texels per canvas unit, vertically
    edge_y = max(1, round(NOTE_EDGE * k * S))
    edge_x = max(1, round(NOTE_EDGE * W / mid * S))
    big = (W * S, H * S)
    box = (edge_x // 2, 7 * S, W * S - 1 - edge_x // 2, 24 * S)

    def outline(fill, ex, ey, inset=0):
        m = Image.new('L', big, 0)
        dr = ImageDraw.Draw(m)
        x0, y0, x1, y1 = box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset
        dr.rectangle((x0, y0, x1, y0 + ey), fill=fill)
        dr.rectangle((x0, y1 - ey, x1, y1), fill=fill)
        dr.rectangle((x0, y0, x0 + ex, y1), fill=fill)
        dr.rectangle((x1 - ex, y0, x1, y1), fill=fill)
        return m
    glow = outline(255, edge_x + 2 * S, edge_y + S).filter(ImageFilter.GaussianBlur(2.8 * k * S))
    out = Image.merge('RGBA', [Image.new('L', big, c) for c in NOTE_GLOW] + [glow.point(lambda v: min(255, int(v * 1.35)))])
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', big, c) for c in NOTE_RGB] + [outline(255, edge_x, edge_y)]))
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', big, c) for c in NOTE_CORE] +
                                    [outline(255, max(1, edge_x // 3), max(1, edge_y // 3), inset=edge_y // 3)]))
    return out.resize((W, H), Image.LANCZOS)


def _shade(w, h, top, left, gloss, blur):
    """An inner shadow for a w x h canvas box (8 texels per unit): dark at the top (and left) edges, blurred, with an
    optional white gloss across the top half."""
    from PIL import ImageDraw, ImageFilter
    S = 8
    W, H = round(w * S), round(h * S)
    m = Image.new('L', (W + 16 * S, H + 16 * S), 255)
    ImageDraw.Draw(m).rectangle((8 * S + left * S, 8 * S + top * S, 8 * S + W - S, 8 * S + H - S), fill=0)
    m = m.filter(ImageFilter.GaussianBlur(blur * S)).crop((8 * S, 8 * S, 8 * S + W, 8 * S + H))
    out = Image.merge('RGBA', [Image.new('L', (W, H), 0)] * 3 + [m.point(lambda v: int(v * 0.85))])
    if gloss:
        g = Image.new('L', (W, H), 0)
        dr = ImageDraw.Draw(g)
        for y in range(round(12 / 25 * H)):
            dr.line((2 * S, S + y, W - 2 * S, S + y), fill=int(150 * (1 - y / (12 / 25 * H)) ** 1.3))
        out.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 255)] * 3 + [g]))
    return out


def _sp_border():
    """The star power strip's border (SP_BORDER, 8 texels per unit): a dark outer edge and a light top lip."""
    from PIL import ImageDraw
    S = 8
    w, h = SP_BORDER[2] - SP_BORDER[0], SP_BORDER[3] - SP_BORDER[1]
    im = Image.new('RGBA', (round(w * S), round(h * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), 3 * S, outline=(20, 20, 24, 255), width=S)
    d.line((2 * S, S + S // 2, im.width - 2 * S, S + S // 2), fill=(150, 150, 158, 255), width=S)
    return im


def textures():
    out = {name: _png(name) for name in ART}
    cap = _png('WoR_HUD_v_cap')
    r, g, b, a = cap.split()
    tinted = Image.merge('RGBA', [c.point(lambda v, m=m: v * m // 255) for c, m in zip((r, g, b), (255, 255, 255))] + [a])
    out[SP_FILL] = tinted.transpose(Image.ROTATE_90)
    for i in range(NOW_FRAMES):
        out[NOW_TEX[i]] = _lightning(NOW_CORE, NOW_GLOW, 11 + i)
        out[NOW_SP_TEX[i]] = _lightning(NOW_SP_CORE, NOW_SP_GLOW, 11 + i)
    out.update({SPIKE_TEX[k]: _spike(k).resize((32, 64), Image.LANCZOS) for k in SPIKE_TEX})   # power-of-two sizes
    out[SP_GLOW_TEX] = _sp_glow()
    out.update({NOTE_TEX[i]: _note(i) for i in range(len(NOTE_TEX))})
    out[METER_SHADE] = _shade(HEALTH[2] - HEALTH[0], HEALTH[3] - HEALTH[1], 1.0, 1.0, True, 1.2).resize((512, 128), Image.LANCZOS)
    out[LAMP_SHADE] = _shade(GREEN[2] - GREEN[0], GREEN[3] - GREEN[1], 2.5, 1.0, False, 2.6).resize((128, 128), Image.LANCZOS)
    out[SP_BORDER_TEX] = _sp_border().resize((1024, 64), Image.LANCZOS)
    out.update({MULT_TEX[n]: _mult_image(n, n) for n in MULT_TEX})
    out.update({MULT_SP_TEX[n]: _mult_image(n, 'sp') for n in MULT_SP_TEX})
    return out


def sources():
    s = {name: {'src': os.path.join(d, n + '.png'), 'box': None, 'flip': False} for name, (d, n) in ART.items()}
    s[SP_FILL] = {'src': os.path.join(UI, 'vocals_meter_cap.png'), 'rotated': 90, 'box': None, 'flip': False}
    for name in NOW_TEX + NOW_SP_TEX + list(SPIKE_TEX.values()) + NOTE_TEX + [SP_GLOW_TEX, METER_SHADE, LAMP_SHADE,
                                                                              SP_BORDER_TEX]:
        s[name] = {'src': 'generated (tools/wor_vocals.py)', 'box': None, 'flip': False}
    for n in MULT_TEX:
        s[MULT_TEX[n]] = {'src': 'fontgrid_text_a1 + fontgrid_numeral_A1_b', 'text': f'x{n}', 'style': str(n), 'box': None, 'flip': False}
    for n in MULT_SP_TEX:
        s[MULT_SP_TEX[n]] = {'src': 'fontgrid_text_a1 + fontgrid_numeral_A1_b', 'text': f'x{n}', 'style': 'sp', 'box': None, 'flip': False}
    return s


def theme_extra():
    """The vocalist's multiplier images (normal / star power) for semultipliernixie, and the note textures read by the
    DE's per-theme vocal setup (0x74586fa3: sung c5e00a8d, connector f6faf84b). The lyric font field is set by
    build.py: the copied WT+ row may already have one."""
    out = ''
    for key, names in (('112feba3', [MULT_TEX[n] for n in (1, 2, 3, 4)]),
                       ('bc95780d', [MULT_SP_TEX[n] for n in (2, 4, 6, 8)])):
        out += (f'\t\t\t\tStructArray {key}\n\t\t\t\t{{\n\t\t\t\t\tArrayQBKey\n\t\t\t\t\t[\n'
                + ''.join(f'\t\t\t\t\t\t{t}\n' for t in names) + '\t\t\t\t\t]\n\t\t\t\t}\n')
    out += f'\t\t\t\tStructQBKey c5e00a8d = {NOTE_TEX[len(NOTE_TEX) // 2]}\n'
    out += '\t\t\t\tStructQBKey f6faf84b = WoR_HUD_blank\n'
    return out


def _qb_rgba(c):
    return ':a{' + ''.join(f'%i({v})' for v in c) + ':a}'


def global_sections(fx_text):
    """QB globals: the DE's comet particles as they are (restored with other themes) and ours with the "miss" sparks
    invisible (mock v3: the purple ball when not singing); the note colours (the DE tints its teal note art with
    vocal_gem_colors; ours are coloured in the texture); our star power flag for the plugin."""
    import re
    src = fx_text[fx_text.index('SectionStruct vocals_comet_particle_effects'):]
    depth, end = 0, None
    for k, ch in enumerate(src):
        depth += {'{': 1, '}': -1}.get(ch, 0)
        if ch == '}' and depth == 0:
            end = k + 1
            break
    de = src[:end]
    wor = de.replace('vocals_comet_particle_effects', 'WoR_HUD_vcomet_wor', 1)
    # every "miss" struct: start colour alpha 0
    wor = re.sub(r'(StructStruct miss\s*\{\s*StructHeader\s*\{\s*StructArray start_color\s*\{\s*ArrayInteger\s*\[\s*\d+\s+\d+\s+\d+\s+)\d+',
                 r'\g<1>0', wor)
    assert wor.count('StructStruct miss') == de.count('StructStruct miss') and ' 255 ]' not in wor[wor.find('StructStruct miss'):][:200]
    de = de.replace('vocals_comet_particle_effects', 'WoR_HUD_vcomet_de', 1)

    def gems(name, c):
        return (f'SectionArray {name}\n{{\n\tArrayArray\n\t[\n'
                + ''.join(f'\t\tArrayInteger\n\t\t[\n' + ''.join(f'\t\t\t{v}\n' for v in c) + '\t\t]\n' for _ in range(7))
                + '\t]\n}\n')
    return '\n'.join([de, wor, gems('WoR_HUD_vgem_de', (64, 255, 255, 255)), gems('WoR_HUD_vgem_wor', (255, 255, 255, 255)),
                      'SectionInteger WoR_HUD_vocal_sp 0\n'])


def _globals_body(ours):
    scale = LYRIC_SCALE if ours else LYRIC_SCALE_DE
    col = LYRIC_RGBA if ours else LYRIC_RGBA_DE
    tag = 'wor' if ours else 'de'
    return (f'\t\t:i $change$$vocal_lyric_font_scale$ = %vec2({scale[0]},{scale[1]})\n'
            f'\t\t:i $change$$vocal_scrolling_lyric_rgba$ = {_qb_rgba(col["upcoming"])}\n'
            f'\t\t:i $change$$vocal_scrolling_word_highlight$ = {_qb_rgba(col["current"])}\n'
            f'\t\t:i $change$$vocal_scrolling_lyric_after$ = {_qb_rgba(col["sung"])}\n'
            f'\t\t:i $change$$vocal_gem_colors$ = ~$WoR_HUD_vgem_{tag}$\n'
            f'\t\t:i $change$$vocals_comet_particle_effects$ = ~$WoR_HUD_vcomet_{tag}$\n')


# The DE's vocal globals switched with the theme: the DE's per-theme vocal setup 0x74586fa3 (notes, lyric font) is
# wrapped (plugin 1.58 swap), and setup_hud runs the same at every song (tools/wor_battle.py's wrapper).
SCRIPTS = (
    'Script WoR_HUD_vocals_globals [\n'
    '\t:i if $[4c1beb8d]$$value$ = $WoR_HUD_sp_highway$\n'
    + _globals_body(True) +
    '\t:i else \n'
    + _globals_body(False) +
    '\t:i endif\n'
    '\t:i $change$$WoR_HUD_vocal_sp$ = %i(0)\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_vocal_note_setup [\n'
    '\t:i $WoR_HUD_vocal_note_setup_orig$ isNull\n'
    '\t:i $WoR_HUD_vocals_globals$ isNull\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_vocal_note_setup_orig [\n'
    '\t:i $printf$%s("WoR_HUD: vocal note setup placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')


def _panel_in_v1(d, dy):
    """The panel in a band layout's v1 container (guitar + vocals): the vocal highway sits at y 0 there (the DE's
    vocals_create_highway with more than one player), dy from its 1-player y 430."""
    import desc_edit
    import wor_mp
    import wor_versus as V
    ox, oy = wor_mp.container_origins(d)['v1'][:2]
    pos = (-ox - wor_mp.G_CAL[0], dy - oy - wor_mp.G_CAL[1])
    a, b = V._element_bounds(d, 'v1')
    blk = d[a:b].replace('StructString desc = "Band_vocal_multiplier"', f'StructString desc = "{MULT_NAME}"', 1)
    blk = desc_edit.set_elem(blk, 'player_meter', pos=pos, dims=(1280, 720))
    try:
        blk = desc_edit.set_elem(blk, 'player_meter', just=(-1, -1))
    except ValueError:
        pass
    d = d[:a] + blk + d[b:]
    blocks = [E(child, 'descinterface', pos=pos, dims=(1280, 720), just=(-1, -1), z=SP_Z if name == SP_NAME else 2.0,
                desc=name).render(0)
              for child, name in (('BAND_top_meter', HEALTH_NAME), ('vocal_multiplier_star', SP_NAME))]
    return wor_mp._append_children(d, 'v1', blocks)


def vocal_highway_desc(de_text):
    """Our copy of the DE's vocals_highway_wtde (section 0x196b50e4 of hud_shared_assets), the root moved to WoR's y."""
    import re
    d = de_text[de_text.index('SectionStruct 0x196b50e4'):]
    nxt = d.find('\nSectionStruct ', 10)
    if nxt > 0:
        d = d[:nxt]
    d = d.replace('SectionStruct 0x196b50e4', f'SectionStruct uidesc_{VH_NAME}', 1)
    d = d.replace('StructQBKey name = 0x196b50e4', f'StructQBKey name = uidesc_{VH_NAME}', 1)
    import desc_edit
    import wor_mp
    m = re.search(r'StructQBKey local_id = root\b', d)
    p = re.compile(r'StructFloatX2 Pos\s*\{\s*Floats \[([-\d.]+), ([-\d.]+)\]')
    mm = p.search(d, m.end())
    x, y = float(mm.group(1)), float(mm.group(2))
    d = d[:mm.start()] + f'StructFloatX2 Pos\n{{\n\tFloats [{x:.5f}, {y + VH_DY:.5f}]' + d[mm.end():]
    # the lyric band (the root's own bg_* row; the copies under NewElement1 / static_next_phrase_bg are other views)
    for lid in ('bg_middle', 'bg_left', 'bg_right'):
        d = _edit_first(d, lid, lambda blk: _band(blk))
    d = desc_edit.set_elem(d, 'lyrics', pos=(303.0, LYRICS_Y))
    d = desc_edit.set_elem(d, 'fireball_bg', scale=(COMET_SCALE, COMET_SCALE))
    # the highway's background: WoR's dim dark; its bg_rgba prop (the DE's teal) lands on a hidden stand-in
    d = _edit_first(d, 'bG', lambda blk: _rgba(blk, HIGHWAY_BG_RGBA, HIGHWAY_BG_ALPHA))
    d = _retarget_to_new_root_child(d, 'bg_rgba', 'WoR_bg_sink')
    d = wor_mp._append_children(d, 'root', [E('WoR_bg_sink', 'SpriteElement', dims=(4, 4), alpha=0.0,
                                               texture='WoR_HUD_blank').render(0)])
    # the now line (the plugin steps through the frames, green or cyan by WoR_HUD_vocal_sp) and the arrowheads
    xc, top, w, h = NOW_BOX
    kids = [E('WoR_now_line', 'SpriteElement', pos=(xc, top), dims=(w, h), just=(0, -1), z=0.5, texture=NOW_TEX[0],
              blend='Add').render(0),
            E('WoR_spike_top', 'SpriteElement', pos=(xc, top - 1.0), dims=(SPIKE_W, SPIKE_H), just=(0, -1), z=0.6,
              texture=SPIKE_TEX['down']).render(0),
            E('WoR_spike_bottom', 'SpriteElement', pos=(xc, top + h + 1.0), dims=(SPIKE_W, SPIKE_H), just=(0, 1), z=0.6,
              texture=SPIKE_TEX['up']).render(0)]
    d = wor_mp._append_children(d, 'pitch_area', kids)
    # star power glow bands (the plugin fades them in while WoR_HUD_vocal_sp is set)
    glows = [E(f'WoR_sp_glow_{i}', 'SpriteElement', pos=(SP_GLOW_X[0], y), dims=(SP_GLOW_X[1] - SP_GLOW_X[0], SP_GLOW_H),
               just=(-1, 0), z=2.5, alpha=0.0, texture=SP_GLOW_TEX, blend='Add').render(0)
             for i, y in enumerate(SP_GLOW_Y)]
    return wor_mp._append_children(d, 'root', glows)


def _root_child_count(d):
    """Number of children of the desc's root element (a prop path addresses a child by its index)."""
    import wor_versus as V
    a, b = V._element_bounds(d, 'root')
    blk = d[a:b]
    j = blk.index('[', blk.index('StructArray children'))
    sq = br = n = 0
    for k in range(j, len(blk)):
        ch = blk[k]
        sq += {'[': 1, ']': -1}.get(ch, 0)
        br += {'{': 1, '}': -1}.get(ch, 0)
        if sq == 0:
            break
        if sq == 1 and br == 0 and blk.startswith('StructHeader', k):
            n += 1
    return n


def _retarget_to_new_root_child(d, prop, lid):
    """Point prop's path at a child of root named lid that will be appended next (index = current child count)."""
    i = d.index(f'StructQBKey name = {prop}\n')
    a = d.rindex('StructArray path', 0, i)
    j = d.index('[', a)
    depth = 0
    for e in range(j, i):
        depth += {'[': 1, ']': -1}.get(d[e], 0)
        if depth == 0:
            break
    path = ('[\n\tStructHeader\n\t{\n\t\tStructQBKey validatelocalid = root\n\t}\n'
            f'\tStructHeader\n\t{{\n\t\tStructInt index = {_root_child_count(d)}\n\t\tStructQBKey validatelocalid = {lid}\n'
            '\t\tStructQBKey includeparentowned = false\n\t}\n]')
    return d[:j] + path + d[e + 1:]


def _rgba(blk, rgba, alpha):
    import re
    blk = re.sub(r'StructFloat alpha = \S+', f'StructFloat alpha = {alpha:.2f}', blk, count=1)
    return re.sub(r'(StructArray rgba\s*\{\s*ArrayInteger\s*\[)[^\]]*(\])',
                  lambda mm: mm.group(1) + '\n' + ''.join(f'\t{v}\n' for v in rgba) + mm.group(2), blk, count=1)


def _edit_first(d, lid, fn):
    """Apply fn to the props block of the first element named lid."""
    import re
    import desc_edit
    m = re.search(rf'StructQBKey local_id = {lid}\s*\n', d)
    a, b = desc_edit._block_bounds(d, m.start())
    return d[:a] + fn(d[a:b]) + d[b:]


def _band(blk):
    import re
    blk = re.sub(r'StructFloat alpha = \S+', f'StructFloat alpha = {LYRIC_BAND_A:.2f}', blk, count=1)
    blk = re.sub(r'(StructFloatX2 Pos\s*\{\s*Floats \[)([-\d.]+), [-\d.]+(\])',
                 lambda mm: f'{mm.group(1)}{mm.group(2)}, {LYRIC_BAND_Y:.5f}{mm.group(3)}', blk, count=1)
    return re.sub(r'(StructFloatX2 Scale\s*\{\s*Floats \[)([-\d.]+), [-\d.]+(\])',
                  lambda mm: f'{mm.group(1)}{mm.group(2)}, {LYRIC_BAND_H / 30.0:.5f}{mm.group(3)}', blk, count=1)


def edit_layout(config, d):
    """hud_1v: the score group at WoR's vocals spot instead of the WT+ solo rock meter; the v1 container's multiplier
    replaced by the WoR panel, with the health meter and star power strip next to it."""
    import desc_edit
    import wor_band
    import wor_mp
    if config == 'hud_1g1v':
        return _panel_in_v1(d, dy=-430.0)
    if config != 'hud_1v':
        return d
    d = d.replace('StructString desc = "solo_play_rock_meter_ghwor"', f'StructString desc = "{wor_band.NAME}"', 1)
    d = desc_edit.set_elem(d, 'band_meter', pos=SCORE_POS, z=11.0)
    d = d.replace('StructString desc = "Band_vocal_multiplier"', f'StructString desc = "{MULT_NAME}"', 1)
    pos = (-V1_POS[0] - wor_mp.G_CAL[0], -V1_POS[1] - wor_mp.G_CAL[1])
    d = desc_edit.set_elem(d, 'player_meter', pos=pos, dims=(1280, 720))
    try:
        d = desc_edit.set_elem(d, 'player_meter', just=(-1, -1))
    except ValueError:
        pass                                 # no float just array: the WT+ instance is left / top already
    blocks = [E(child, 'descinterface', pos=pos, dims=(1280, 720), just=(-1, -1), z=SP_Z if name == SP_NAME else 2.0,
                desc=name).render(0)
              for child, name in (('BAND_top_meter', HEALTH_NAME), ('vocal_multiplier_star', SP_NAME))]
    return wor_mp._append_children(d, 'v1', blocks)
