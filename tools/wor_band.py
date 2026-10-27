"""Band score group (user 2026-10-22, items 9-11): in every band layout the WT+ band meter (dial, lanes, instrument
icons: the "huge guitar") is replaced by the quickplay score group (wor_1g.band_meter without its tubes), at the top
right like WoR's band HUD (lower, under the vocal highway, when the layout has a vocalist), plus WoR's band
multiplier bulb (uidesc_star_meter band_multiplier: band_HUD_multiplier_bulb with a nixie digit
band_HUD_multiplier_<n> and an "x"), growing out of the score group (plugin 1.40) when it appears and (1.57) on
every multiplier change. Hidden at x1 again (user 2026-10-27; it was shown at x1 for testing on 10-26).

The DE's HUD_attach_widget_band_meter drives the band score, streak, star meter and band star power on this desc like
on the 1-player one; every WT+ band meter prop we don't show (needle, lanes, instrument icons, multiplier text) lands
on a hidden stand-in. Our wrapper of that script adds a semultipliernixie widget on band1_multiplier (values 1-4, x2
in star power: 2 / 4 / 6 / 8) writing the bulb texture (blank only until the widget's first write).
"""
import copy
import os

import paths
from desc_gen import E, desc

NAME = 'wor_band_score_ghwor'
ROOT_ID = 'band_score_wor'
WOR_ZIG = os.path.join(paths.WOR_EXTRACT, 'z_in_game_png2')
BULB_SRC = os.path.join(WOR_ZIG, 'band_HUD_multiplier_bulb.png')
DIGIT_SRC = {n: os.path.join(WOR_ZIG, f'band_HUD_multiplier_{w}.png')
             for n, w in ((1, 'one'), (2, 'two'), (3, 'three'), (4, 'four'), (6, 'six'), (8, 'eight'))}
BULB_TEX = {n: f'WoR_HUD_bandbulb_{n}' for n in DIGIT_SRC}
BULB_ID = 'band_bulb'
# WoR's bulb (uidesc_star_meter band_multiplier): 128 px art; the digit (64 px, scale 0.8) and band_HUD_bulb_x (32 px,
# scale 0.9) centred at these points of it, both at rot_angle -10 (user 2026-10-26, mock docs/mocks/mock_vocals_v4.jpg)
DIGIT_C, DIGIT_S = (64 - 23.7687, 64 - 23.9484), 0.8
X_C, X_S = (64 - 33.3245, 64 - 3.69682), 0.9
X_SRC = os.path.join(WOR_ZIG, 'band_HUD_bulb_x.png')
TILT = 10.0                              # degrees counter-clockwise on screen (WoR's rot_angle -10)
# the popup's orange flash: band_HUD_multiplier_bulb_Glow01, Add, rgba 255,128,0 (alpha driven by the plugin)
GLOW_TEX, GLOW_SRC = 'WoR_HUD_bandbulb_glow', os.path.join(WOR_ZIG, 'band_HUD_multiplier_bulb_Glow01.png')
GLOW_ID = 'band_bulb_glow'
# the popup (WoR HUD_setup_band_mult_animation): from its spot + (118, 32) in the score frame at scale 0.5, 0.3 s
# (the score frame's units are wor_1g.K0 canvas units)
POPUP_FROM = (118.0 * 0.775 / 1.35, 32.0 * 0.775 / 1.35)
POPUP_SCALE, POPUP_TIME = 0.5, 0.3
TEST_CYCLE = (1, 2, 3, 4, 2, 4, 6, 8)   # x1..x4, then star power x2..x8 (every 2 s, tests/capture_band.py --bulb-cycle)
# placement on the 1-player canvas (the score group's own coordinates): the bulb left of the score box
BULB_C = (-140.0, -6.0)                  # from wor_1g.SCORE_C
BULB_D = 84.0                            # drawn size of the 128 px bulb
# the group's offset from its 1-player spot (score box centre wor_1g.SCORE_C ~ (1056, 581)) to WoR's band spot, top
# right (user's WoR frames 2026-10-22: ~(1047, 187) without vocals, ~(1019, 257) under the vocal highway)
OFFSET = {False: (-9.0, -394.0), True: (-37.0 + 130.0, -324.0 - 50.0)}
# vocal layouts (capture 2026-10-22): moved to the right edge like the 2-player spot, and up to just under the lyrics
# line (the 3g1v override of the first capture had it on the lyrics)
# hud_3g1v (3 instruments, 4-player band): measured on the bot capture 2026-10-22 the group sat ~130 px left of the
# 2-player spot and ~87 px below the vocal highway's bottom (y 135); moved to the right edge, top just under it
OFFSET_BY_CONFIG = {}
TUBE_IDS = ('lights_bg', 'red_light', 'yellow_light', 'green_light')
WTPLUS_PROPS = ['multiplier_text', 'band_mult_text'] + [
    f'band_HUD_{k}' for p in range(1, 5) for k in (
        f'p{p}_mask_dims', f'p{p}_fill_rgba', f'instrument_p{p}_texture', f'instrument_p{p}_alpha',
        f'instrument_p{p}_rgba', f'instrument_glow_p{p}_texture', f'instrument_glow_p{p}_alpha',
        f'instrument_glow_p{p}_rgba')]


def _bulb(n):
    from PIL import Image
    out = Image.open(BULB_SRC).convert('RGBA')
    for src, c, s in ((DIGIT_SRC[n], DIGIT_C, 64 * DIGIT_S), (X_SRC, X_C, 32 * X_S)):
        im = Image.open(src).convert('RGBA').resize((round(s), round(s)), Image.LANCZOS)
        im = im.rotate(TILT, Image.BICUBIC, expand=True)
        out.alpha_composite(im, (round(c[0] - im.width / 2), round(c[1] - im.height / 2)))
    return out


def _glow():
    from PIL import Image
    im = Image.open(GLOW_SRC).convert('RGBA')
    r, g, b, a = im.split()
    lum = Image.merge('RGB', (r, g, b)).convert('L')
    return Image.merge('RGBA', (lum, lum.point(lambda v: v // 2), lum.point(lambda v: 0), a))


def textures():
    out = {BULB_TEX[n]: _bulb(n) for n in DIGIT_SRC}
    out[GLOW_TEX] = _glow()
    return out


def sources():
    out = {BULB_TEX[n]: {'src': BULB_SRC, 'digit': DIGIT_SRC[n], 'x': X_SRC, 'tilt': TILT, 'box': None, 'flip': False}
           for n in DIGIT_SRC}
    out[GLOW_TEX] = {'src': GLOW_SRC, 'rgb': [255, 128, 0], 'box': None, 'flip': False}
    return out


def _is_tube(lid):
    return lid.startswith(('sp_', 'rm_')) or 'void' in lid or lid in TUBE_IDS


def _ids(e, out):
    out.add(e.local_id)
    for c in e.children:
        _ids(c, out)
    return out


def score_desc():
    """The quickplay score group, no tubes, moved to the band spot, + the bulb; every band meter prop accepted."""
    import wor_1g, desc_gen
    wor_1g.all_descs()
    src = desc_gen.ROOTS['wor_band_meter_1g_ghwor']
    meter = copy.deepcopy(src)
    meter.children = [c for c in meter.children if not _is_tube(c.local_id)]
    # the DE's star meter (hudthemes 0x08b99cb3) scales the bar by progress x 1.0 with more than one player shown,
    # x 0.7 with one: the 1-player bar is authored for 0.7, so in band it overshot the box by 1 / 0.7 (user
    # 2026-10-22: "the star meter grows past the score group"); the band copy's bar is 0.7 as long
    for c in meter.children:
        if c.local_id == 'star_filler':
            c.dims = (c.dims[0] * 0.7, c.dims[1])
    sc = wor_1g.SCORE_C
    meter.children.append(E(BULB_ID, 'SpriteElement', pos=(sc[0] + BULB_C[0], sc[1] + BULB_C[1]), dims=(BULB_D, BULB_D),
                            just=(0, 0), z=8.0, texture='WoR_HUD_blank'))
    meter.children.append(E(GLOW_ID, 'SpriteElement', pos=(sc[0] + BULB_C[0], sc[1] + BULB_C[1]), dims=(BULB_D, BULB_D),
                            just=(0, 0), z=8.1, alpha=0.0, texture=GLOW_TEX, blend='Add'))
    root = E(ROOT_ID, 'ContainerElement', pos=(0, 0), dims=(1280, 720), just=(-1, -1), children=[meter])
    # the 1-player props, then the WT+ band meter's: any target we dropped (tube lights, segments) or never had (lanes,
    # icons, multiplier text) becomes a hidden stand-in
    props = [p for p in desc_gen.PROPS['wor_band_meter_1g_ghwor']] + [(n, n + '_sink', None) for n in WTPLUS_PROPS]
    have = _ids(root, set())
    sinks, out = [], []
    for name, target, field in props:
        f = field or _field_for(name)
        if target not in have:
            target = name + '_sink'
            if target not in have:
                sinks.append(E(target, 'TextBlockElement' if f == 'text' else 'SpriteElement', dims=(4, 4), alpha=0.0,
                               **({'font': wor_1g.SCORE_FONT, 'text': '0x00000000', 'shadow': False} if f == 'text'
                                  else {'texture': 'WoR_HUD_blank'})))
                have.add(target)
        out.append((name, target, f))
    out.append(('band_bulb_texture', BULB_ID, 'texture'))
    meter.children.append(E('band_sinks', 'ContainerElement', dims=(4, 4), alpha=0.0, children=sinks))
    aliases = desc_gen.ALIASES['wor_band_meter_1g_ghwor']
    return desc(NAME, root, out, aliases)


def _field_for(prop):
    for suffix, f in (('_texture', 'texture'), ('_alpha', 'alpha'), ('_rgba', 'rgba'), ('_dims', 'dims'),
                      ('_text', 'text'), ('_scale', 'Scale')):
        if prop.endswith(suffix):
            return f
    raise ValueError(prop)


def descs():
    return [score_desc()]


def edit_layout(config, d):
    """Our band layouts: the band meter instance shows our score group, moved to the band spot (lower where a
    vocalist plays: every layout but hud_2g)."""
    import re
    import wor_versus as V
    ids = re.findall(r'StructQBKey local_id = (\S+)\s*\n(?:(?!local_id).)*?StructString desc = "band_meter_ghwor"', d, re.S)
    if not ids:
        return d
    lid = ids[0]
    d = d.replace('StructString desc = "band_meter_ghwor"', f'StructString desc = "{NAME}"', 1)
    dx, dy = OFFSET_BY_CONFIG.get(config, OFFSET[config != 'hud_2g'])
    a, b = V._element_bounds(d, lid)
    blk = d[a:b]
    m = re.search(r'StructFloatX2 Pos\s*\{\s*Floats \[([-\d.]+), ([-\d.]+)\]', blk)
    x, y = float(m.group(1)) + dx, float(m.group(2)) + dy
    blk = blk[:m.start()] + f'StructFloatX2 Pos\n{{\n\tFloats [{x:.5f}, {y:.5f}]' + blk[m.end():]
    return d[:a] + blk + d[b:]


# the DE's HUD_attach_widget_band_meter, wrapped (plugin swap with _orig): on our score group, the bulb texture by
# the band multiplier
SCRIPTS = (
    'Script WoR_HUD_HUD_attach_widget_band_meter [\n'
    '\t:i $WoR_HUD_HUD_attach_widget_band_meter_orig$ isNull\n'
    '\t:i if $GotParam$$parent$\n'
    '\t\t:i if $ResolveScreenElementID$$id$ = %GLOBAL%$parent$$param$ = $WoR_HUD_bm_id$\n'
    f'\t\t\t:i if $ScreenElementExists$$id$ = :s{{%GLOBAL%$WoR_HUD_bm_id$$child$ = ${ROOT_ID}$:s}}\n'
    '\t\t\t\t:i $AttachHudWidget$:s{\n'
    '\t\t\t\t\t:i $Input$ = :s{\n'
    '\t\t\t\t\t\t:i $value$ = $band1_multiplier$\n'
    '\t\t\t\t\t:i :s}\n'
    '\t\t\t\t\t:i $output$ = :s{\n'
    '\t\t\t\t\t\t:i $type$ = $semultipliernixie$\n'
    '\t\t\t\t\t\t:i $desc_id$ = %GLOBAL%$WoR_HUD_bm_id$\n'
    '\t\t\t\t\t\t:i $property$ = $band_bulb_texture$\n'
    '\t\t\t\t\t\t:i $player$ = %i(1)\n'
    f'\t\t\t\t\t\t:i $textures$ = :a{{$WoR_HUD_blank${"".join(f"${BULB_TEX[n]}$" for n in (2, 3, 4))}:a}}\n'
    f'\t\t\t\t\t\t:i $sp_textures$ = :a{{{"".join(f"${BULB_TEX[n]}$" for n in (2, 4, 6, 8))}:a}}\n'
    '\t\t\t\t\t:i :s}\n'
    '\t\t\t\t:i :s}\n'
    # test harness (tests/capture_band.py --bulb-cycle): every bulb in turn, each with its popup
    '\t\t\t\t:i $[e5eb89ff]$$section$ = %s("WoR_HUD")$key$ = %s("TestBulbCycle")$default$ = %i(0)\n'
    '\t\t\t\t:i if (%GLOBAL%$value$ = %i(1))\n'
    '\t\t\t\t\t:i $spawnscriptnow$$WoR_HUD_test_bulb_cycle$$params$ = :s{$id$ = %GLOBAL%$WoR_HUD_bm_id$:s}\n'
    '\t\t\t\t:i endif\n'
    '\t\t\t:i endif\n'
    '\t\t:i endif\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_test_bulb_cycle [\n'
    f'\t:i $textures$ = :a{{{"".join(f"${BULB_TEX[n]}$" for n in TEST_CYCLE)}:a}}\n'
    '\t:i $printf$%s("WoR_HUD: test bulb cycle on")\n'
    '\t:i $wait$%f(5.0)$seconds$\n'
    '\t:i while \n'
    '\t\t:i $i$ = %i(0)\n'
    '\t\t:i while \n'
    '\t\t\t:i if NOT $ScreenElementExists$$id$ = %GLOBAL%$id$\n'
    '\t\t\t\t:i return\n'
    '\t\t\t:i endif\n'
    '\t\t\t:i %GLOBAL%$id$.$se_setprops$$band_bulb_texture$ = (%GLOBAL%$textures$:a{%GLOBAL%$i$:a})\n'
    '\t\t\t:i $wait$%f(2.0)$seconds$\n'
    '\t\t\t:i %GLOBAL%$i$ = (%GLOBAL%$i$ + %i(1))\n'
    f'\t\t:i loop_to %i({len(TEST_CYCLE)})\n'
    '\t:i loop_to \n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_HUD_attach_widget_band_meter_orig [\n'
    '\t:i $printf$%s("WoR_HUD: band meter placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')
