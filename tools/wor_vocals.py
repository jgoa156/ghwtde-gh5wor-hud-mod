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
SP_CAP = (145, 491.5, 383, 499.5)
SP_FILL_X, SP_FILL_Y = (147.0, 381.0), (492.5, 498.5)
SP_MARK = (263.5, 491.5, 265.0, 499.5)       # the strip's 50 % mark
SP_SEGS = 3                                  # the DE's setubes on a vocalist: glow0..2
# the v1 container draws at its layout spot (95, 72) + the container calibration (wor_mp.G_CAL): our descs carry canvas
# coordinates, so their instances sit at minus that
V1_POS = (95.0, 72.0)
# the score group: WoR's vocals spot (the mock: our guitar + vocals group moved by (-56.67, +223.33))
SCORE_POS = (17.058 - 56.67, -363.2697 + 223.33)
VH_NAME = 'vocals_highway_ghwor'
VH_DY = 32.0                                 # WoR's vocals_highway root y (the DE's: 0)

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
    kids = [_fit('meter', 'WoR_HUD_v_health', HEALTH, 0.13), *lamps, anchor,
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
            _fit('combo', 'WoR_HUD_v_combo', COMBO, 0.13),
            E('nixie', 'SpriteElement', pos=MULT_BOX[:2], dims=(MULT_BOX[2] - MULT_BOX[0], MULT_BOX[3] - MULT_BOX[1]),
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
              just=(-1, -1), z=0.16, rgba=(25, 25, 30, 255), texture='WoR_HUD_v_cap')]
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


def _mult_image(n, rgb):
    import mock_fail_popup as fonts
    out = Image.new('RGBA', (128, 64), (0, 0, 0, 0))
    x = fonts.text(fonts.TEXT, 'x', 26, rgb)
    x = x.crop(x.getbbox())
    out.alpha_composite(x, (10, 60 - x.height))
    d = fonts.text(fonts.TEXT, str(n), 56, rgb)
    d = d.crop(d.getbbox())
    for dx in (0, 1):                        # WoR's number reads bolder than one pass of text_a1
        out.alpha_composite(d, (46 + dx, 60 - d.height))
    return out


def textures():
    out = {name: _png(name) for name in ART}
    cap = _png('WoR_HUD_v_cap')
    r, g, b, a = cap.split()
    tinted = Image.merge('RGBA', [c.point(lambda v, m=m: v * m // 255) for c, m in zip((r, g, b), (255, 255, 255))] + [a])
    out[SP_FILL] = tinted.transpose(Image.ROTATE_90)
    out.update({MULT_TEX[n]: _mult_image(n, MULT_RGB[n]) for n in MULT_TEX})
    out.update({MULT_SP_TEX[n]: _mult_image(n, MULT_SP_RGB) for n in MULT_SP_TEX})
    return out


def sources():
    s = {name: {'src': os.path.join(d, n + '.png'), 'box': None, 'flip': False} for name, (d, n) in ART.items()}
    s[SP_FILL] = {'src': os.path.join(UI, 'vocals_meter_cap.png'), 'rotated': 90, 'box': None, 'flip': False}
    for n in MULT_TEX:
        s[MULT_TEX[n]] = {'src': 'fontgrid_text_a1', 'text': f'x{n}', 'rgb': list(MULT_RGB[n]), 'box': None, 'flip': False}
    for n in MULT_SP_TEX:
        s[MULT_SP_TEX[n]] = {'src': 'fontgrid_text_a1', 'text': f'x{n}', 'rgb': list(MULT_SP_RGB), 'box': None, 'flip': False}
    return s


def theme_extra():
    """The vocalist's multiplier images (normal / star power) for semultipliernixie."""
    out = ''
    for key, names in (('112feba3', [MULT_TEX[n] for n in (1, 2, 3, 4)]),
                       ('bc95780d', [MULT_SP_TEX[n] for n in (2, 4, 6, 8)])):
        out += (f'\t\t\t\tStructArray {key}\n\t\t\t\t{{\n\t\t\t\t\tArrayQBKey\n\t\t\t\t\t[\n'
                + ''.join(f'\t\t\t\t\t\t{t}\n' for t in names) + '\t\t\t\t\t]\n\t\t\t\t}\n')
    return out


def vocal_highway_desc(de_text):
    """Our copy of the DE's vocals_highway_wtde (section 0x196b50e4 of hud_shared_assets), the root moved to WoR's y."""
    import re
    d = de_text[de_text.index('SectionStruct 0x196b50e4'):]
    nxt = d.find('\nSectionStruct ', 10)
    if nxt > 0:
        d = d[:nxt]
    d = d.replace('SectionStruct 0x196b50e4', f'SectionStruct uidesc_{VH_NAME}', 1)
    d = d.replace('StructQBKey name = 0x196b50e4', f'StructQBKey name = uidesc_{VH_NAME}', 1)
    m = re.search(r'StructQBKey local_id = root\b', d)
    p = re.compile(r'StructFloatX2 Pos\s*\{\s*Floats \[([-\d.]+), ([-\d.]+)\]')
    mm = p.search(d, m.end())
    x, y = float(mm.group(1)), float(mm.group(2))
    return d[:mm.start()] + f'StructFloatX2 Pos\n{{\n\tFloats [{x:.5f}, {y + VH_DY:.5f}]' + d[mm.end():]


def edit_layout(config, d):
    """hud_1v: the score group at WoR's vocals spot instead of the WT+ solo rock meter; the v1 container's multiplier
    replaced by the WoR panel, with the health meter and star power strip next to it."""
    import desc_edit
    import wor_band
    import wor_mp
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
    blocks = [E(child, 'descinterface', pos=pos, dims=(1280, 720), just=(-1, -1), z=2.0, desc=name).render(0)
              for child, name in (('BAND_top_meter', HEALTH_NAME), ('vocal_multiplier_star', SP_NAME))]
    return wor_mp._append_children(d, 'v1', blocks)
