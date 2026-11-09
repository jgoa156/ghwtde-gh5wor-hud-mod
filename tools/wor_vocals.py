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
    'WoR_HUD_v_ppfill': (UI, 'vocal_starpower_fill'),
}
SP_FILL = 'WoR_HUD_v_spfill'                 # WoR's star power fill colours (SP_PROFILE), turned for the segments
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
# phrase end (2026-11-03): the DE has no live phrase progress, only the phrase's quality 0..1 when it ends (its script
# ddb4a0e3, plugin swap -> WoR_HUD_vocal_phrase_end). WoR's grade flip (vocal_highway_hud_animate_feedback_spawned):
# the multiplier and the phrase box fold away (scale y -> 0, 0.1 s), the grade word unfolds over both, holds 0.4 s,
# folds, and the meters unfold again; here the phrase box comes back filled to the phrase's quality in WoR's
# vocal_phrase_progress_fill colours (white < 0.6 <= yellow < 0.8 <= green) and keeps it until the next phrase end.
GRADES = [('SLOPPY!', (225, 30, 30)), ('ROUGH', (255, 140, 0)), ('AVERAGE', (255, 255, 255)),
          ('SOLID', (255, 255, 0)), ('EXCELLENT!', (0, 255, 0))]          # WoR vocal_phrase_qualities (vocals.qb)
GRADE_MIN = (0.0, 0.2, 0.4, 0.6, 0.8)
GRADE_TEX = [f'WoR_HUD_vgrade_{i}' for i in range(len(GRADES))]
# WoR footage (WOR_microphone_gameplay, 11-03): the word sits on the phrase box only (canvas 285..378 x 466..486), ~20 tall,
# tight letters, squeezed to the box's width; the multiplier box folds away beside it
WORD_BOX = (PHRASE[0], 464.0, PHRASE[2], 488.0)
WORD_H = 20.0                                                            # cap height of the word, canvas units
PP_RGB = ((200, 200, 200), (245, 255, 0), (0, 255, 0))
PP_STEPS = (0.6, 0.8)
FLIP_STEPS = 6                                                           # 0.1 s folds, a step per frame at 60 fps
# (user 2026-11-04: the flip must be smoother; 1.88 waited 1/30 s between 3 steps)
# these ride in the always-loaded UI pak (no 4 MiB cap; the theme pak was at 3.68 MB), like the menu popups' art
UI_TEX = GRADE_TEX + ['WoR_HUD_v_ppfill']
# WoR's "Get Ready!" on the vocal highway (user 2026-11-06: abruptly, 5 s before the first vocal note, for 3 s, centred)
GET_READY_TEXT, GET_READY_TEX = 'Get Ready!', 'WoR_HUD_v_getready'
GET_READY_LEAD, GET_READY_SHOW = 5000, 3000                 # ms
GET_READY_NUDGE = (-22.0, -18.7)                    # user 2026-11-06: centre AND middle of the vocal highway (1.91 frames: 33 px right, 28 px low)
GET_READY_DIMS = (430.0, 46.0)                              # canvas units (WoR footage: ~46 units tall)
# (in the theme pak: a desc names it, tests/run_offline.py integrity_textures_in_theme_pak)
# star power strip (mock v5, user 2026-10-26): 9 tall (was 8) and 1 up, a dark border with a light top lip, the 50 %
# mark 5 wide, drawn over the highway's top line
SP_DY = -2.0                                      # user 2026-11-07: "the star power tube visibly needs to go up a bit"
SP_CAP = (145, 493.0 + SP_DY, 383, 501.0 + SP_DY)  # user 2026-10-27: 1 smaller, 2 down
# 2026-11-04 (user, WoR screenshot vs ours; mock verify/mock_vocal_fix_v1.jpg): no border at all, the fill over the
# tube's gloss at the tube's whole inner height, WoR's shinier colours (SP_PROFILE, rows measured top to bottom on the
# WoR frame), a white tip at the fill's end, the 50 % mark 2 px (1.33 canvas units) thinner
SP_FILL_X, SP_FILL_Y = (147.0, 381.0), (493.6 + SP_DY, 500.4 + SP_DY)
SP_MARK = (262.67, 493.0 + SP_DY, 266.33, 501.0 + SP_DY)     # the strip's 50 % mark
SP_PROFILE = [(48, 88, 97), (105, 176, 178), (165, 255, 255), (171, 255, 255), (151, 255, 255), (111, 212, 237),
              (60, 148, 211), (17, 76, 108)]
SP_TIP_TEX = 'WoR_HUD_v_sptip'
SP_TIP_LEN = 6.5                             # canvas units along the strip
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
# 2026-10-27, overlaid on a WoR frame (canvas): the words were centred ~598 (on the bottom line), WoR's ~617: 19 down,
# the band (centred, just y 0) on WoR's 600..632; the now line 12 right (WoR x 405, ours 393)
LYRIC_BAND_Y, LYRIC_BAND_H, LYRIC_BAND_A = 157.0, 32.0, 0.9
LYRICS_Y = 161.0
NOW_BAR_DX = 12.0
# user 2026-10-30: the orange comet (fireball_bg) and its trail must go, the green now line stays: both at scale 0
# (was WoR's fireball_bg 0.35, the DE's 0.55; singing sparks 0.55 -> 0.2, the DE's 1.6 / 1.5 -> 0.5)
# user 2026-11-04: WoR's orange ball shows only while the player makes noise, no trail. WoR's fireball sprite is
# invisible too (vocal_fireball_color alpha 0); its ball is the singing sparks (the DE's own "base" emitter, which only
# runs while singing; "miss" stays invisible). They come back small, orange-yellow, without velocity (no trail) and
# short-lived, so they stay a ball at the now line
COMET_SCALE = 0.0
COMET_SPARK = (0.5, 0.3)                     # singing sparks' start / end scale (the DE's 1.6 / 1.5 -> 0.5)
COMET_SPARK_RGBA = ((255, 200, 60, 255), (255, 90, 0, 0))
COMET_SPARK_TIME = 0.2
# the now line (mock v3, user 2026-10-26): WoR's green crackling lightning, cyan in star power; ours rides in
# pitch_area (x centre 10) from the top line to the bottom one (now_bar y 30 + pitch_area y 18 = 48 below the root;
# the lines' centres at root y 35 / 137). NOW_FRAMES bolts per colour, the plugin (1.58) steps through them.
# user 2026-11-04: WoR's line is thinner and animates at least 3x faster: the sprite at NOW_W_SCALE of its width (bolt
# and halo together, mock verify/mock_vocal_fix_v1.jpg) and a new bolt every frame (plugin 1.89, 60 a second) out of 8;
# frames 4..7 ride in the UI pak (the theme pak is near its cap; the plugin sets them by name)
NOW_FRAMES = 8
NOW_W_SCALE = 0.40   # user 2026-11-06 (later): 0.22 too thin, 'turn it up to 28'; 2026-11-07: "slightly thicker", then 40
#                          # user 2026-11-06: thinner again (0.55 -> 0.35 -> 0.22; WoR's is a hairline)
NOW_TEX = [f'WoR_HUD_vnow_g{i}' for i in range(NOW_FRAMES)]
NOW_SP_TEX = [f'WoR_HUD_vnow_c{i}' for i in range(NOW_FRAMES)]
UI_TEX += NOW_TEX[4:] + NOW_SP_TEX[4:]
NOW_GLOW, NOW_CORE = (20, 200, 20), (190, 255, 150)
NOW_SP_GLOW, NOW_SP_CORE = (0, 190, 255), (210, 255, 255)
NOW_BOX = (10.0, 35.0 - 48.0, 28.0, 137.0 - 35.0)   # (x centre, top, width, height) in pitch_area
# white arrowheads on both lines at the now line (mock v4: 10 x 13, on the lines, over the lightning)
SPIKE_TEX = {'down': 'WoR_HUD_vspike_down', 'up': 'WoR_HUD_vspike_up'}
SPIKE_PAD = (4, 6)                           # texels of shadow room: each side, the tip (2026-11-06)
SPIKE_SHADOW_OFF, SPIKE_SHADOW_BLUR, SPIKE_SHADOW_A = (1, 2), 2.2, 0.62
SPIKE_W, SPIKE_H = 13.0 * (40 + 2 * SPIKE_PAD[0]) / 40, 17.0 * (52 + SPIKE_PAD[1]) / 52   # the arrow stays 13 x 17
# star power (mock v3): a cyan glow band on the top line and along the lyric band's bottom edge, in the root (the top
# line spans root x -221..880; the lyric band's bottom edge is at root y 157)
SP_GLOW_TEX = 'WoR_HUD_vsp_glow'
SP_GLOW_X = (-221.0, 880.0)
SP_GLOW_Y = (35.0, 173.0)
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


def _centred(e):
    """The same sprite with just (0, 0) at its rectangle's centre, so a y scale folds it about its middle."""
    e.pos = (e.pos[0] + e.dims[0] / 2, e.pos[1] + e.dims[1] / 2)
    e.just = (0, 0)
    return e


# inside the tube's glass; 2026-11-07 (user: "the fill of the precision bar needs to go right by some pixels, it's not
# aligned with its bar"): the visible glass is canvas ~289..374 (1v frames, 5x zoom), the fill started at 286 and would
# run past the glass's right end when full
PP_FILL_BOX = (PHRASE[0] + 3.5, PHRASE[1] + 1.0, PHRASE[2] - 3.0, PHRASE[3] - 1.0)
# 1.89 (user 2026-11-04: the box must register while singing): the plugin drives the fill every frame from the DE's
# vocal player object (hits / ticks so far x the phrase's elapsed part), WoR's white / yellow / green (PP_RGB at
# PP_STEPS) by its level, empty again after each grade flip as in WoR; it finds the fill by this z (unique)
PP_FILL_Z = 0.1357


def mult_desc():
    cx, cy = _centre(COMBO)
    fill = _fit('phrase_fill', 'WoR_HUD_v_ppfill', PP_FILL_BOX, PP_FILL_Z, blend='Add')
    # scale x = the live level from the fill's left end (plugin), scale y folds it about the middle (the grade flip)
    fill.pos, fill.just = (fill.pos[0], fill.pos[1] + fill.dims[1] / 2), (-1, 0)
    fill.scale = (0.0, 1.0)
    # the desc starts on the theme pak's blank: the plugin sets the real texture (UI pak) by name
    fill.extra['texture'] = 'WoR_HUD_blank'
    wx, wy = _centre(WORD_BOX)
    kids = [_fit('backing', 'WoR_HUD_v_backing', BACKING, 0.10),
            _fit('stripe', 'WoR_HUD_v_stripe', STRIPE, 0.12, rgba=FRAME_BLUE + (255,)),
            *[_fit(f'div{i}', 'WoR_HUD_v_div', (x - 2.5, 461, x + 2.5, 489), 0.11) for i, x in enumerate(DIVIDERS)],
            # the box is baked into the "xN" images (MULT_STYLE): the combo art only under them
            _fit('combo', 'WoR_HUD_v_combo', COMBO, 0.13, alpha=0.0),
            E('nixie', 'SpriteElement', pos=(cx, cy), dims=(COMBO[2] - COMBO[0], COMBO[3] - COMBO[1]),
              just=(0, 0), z=0.2, texture=MULT_TEX[1]),
            _centred(_fit('phrase_tube', 'WoR_HUD_v_tube', PHRASE, 0.13)),
            fill,
            E('grade_word', 'SpriteElement', pos=(wx, wy), dims=(WORD_BOX[2] - WORD_BOX[0], WORD_BOX[3] - WORD_BOX[1]),
              just=(0, 0), z=0.3, alpha=0.0, scale=(1.0, 0.0), texture='WoR_HUD_blank'),
            _sink('nixie_rgba_sink'), _sink('mult_bg_sink')]
    sinks = [_sink(f'light{i}_sink') for i in range(5)]
    kids += sinks + [_sink('streak_text_sink', 'SpriteElement')]
    root = E('vocal_mult', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)
    props = [('nixie_texture', 'nixie', 'texture'), ('nixie_rgba', 'nixie_rgba_sink', 'rgba'),
             ('mult_bg_alpha', 'mult_bg_sink', 'alpha')]
    props += [(f'light{i}_texture', f'light{i}_sink', 'texture') for i in range(5)]
    # ours, set by WoR_HUD_vocal_grade at each phrase end
    props += [('WoR_nixie_scale', 'nixie', 'Scale'), ('WoR_pp_tube_scale', 'phrase_tube', 'Scale'),
              ('WoR_pp_fill_scale', 'phrase_fill', 'Scale'),
              ('WoR_word_texture', 'grade_word', 'texture'),
              ('WoR_word_scale', 'grade_word', 'Scale'), ('WoR_word_alpha', 'grade_word', 'alpha')]
    return desc(MULT_NAME, root, props)


def sp_desc():
    x0, x1 = SP_FILL_X
    y0, y1 = SP_FILL_Y
    seg = (x1 - x0) / SP_SEGS
    kids = [_fit('cap', 'WoR_HUD_v_cap', SP_CAP, 0.12),
            E('mark', 'SpriteElement', pos=SP_MARK[:2], dims=(SP_MARK[2] - SP_MARK[0], SP_MARK[3] - SP_MARK[1]),
              just=(-1, -1), z=0.16, rgba=(20, 20, 24, 255), texture='WoR_HUD_v_cap')]
    for i in range(SP_SEGS):
        # child (x, y) -> screen (y, -x): the sprite's height runs right along the strip, its width across it. The
        # fill is opaque over the tube (its gloss under the fill, user 2026-11-04)
        fill = E(f'glow{i}', 'SpriteElement', pos=(0.0, 0.0), dims=(y1 - y0, seg), just=(0, -1), scale=(1.0, 0.0),
                 z=0.14, texture=SP_FILL)
        # the white tip at the fill's end: the plugin moves it with the fill and shows it while the segment fills
        tip = E(f'tip{i}', 'SpriteElement', pos=(0.0, 0.0), dims=(y1 - y0 + 2.0, SP_TIP_LEN), just=(0, 0), alpha=0.0,
                z=0.145, texture=SP_TIP_TEX, blend='Add')
        # 2026-10-30 (1v run: the strip never moved): the DE's setubes widget scales the element behind each TEXTURE
        # prop, which was a sink, so the fill never moved. Both props now go to glow{i}_src, the fill's invisible
        # sibling (the DE's texture writes resize it, not the strip); the plugin copies its fill (scale y / x) onto
        # glow{i} every frame, like a multiplayer tube's level source
        src = E(f'glow{i}_src', 'SpriteElement', dims=(4, 4), just=(0, -1), alpha=0.0, z=0.13, texture='WoR_HUD_blank')
        kids.append(E(f'seg{i}', 'ContainerElement', pos=(x0 + i * seg, (y0 + y1) / 2), dims=(4, 4), just=(0, 0),
                      rot=-90.0, z=0.14, children=[fill, src, tip]))
    root = E('vocal_sp', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)
    props = []
    for i in range(SP_SEGS):
        props += [(f'glow{i}_scale', f'glow{i}_src', 'Scale'), (f'glow{i}_texture', f'glow{i}_src', 'texture')]
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


def _spaced(font, s, h, rgb, gap=0.10):
    """A word drawn glyph by glyph (the strip renderer runs the letters together), gap x h between glyphs, h tall."""
    import mock_fail_popup as fonts
    parts = []
    for ch in s:
        if ch == ' ':   # (2026-11-06, "Get Ready!") the font has no space glyph: a gap of 0.35 x h
            parts.append(Image.new('RGBA', (round(0.35 * 160), 1), (0, 0, 0, 0)))
            continue
        t = fonts.text(font, ch, 160, rgb)
        bb = t.getbbox()
        parts.append(t.crop((bb[0], 0, bb[2], t.height)))
    g = round(gap * 160)
    out = Image.new('RGBA', (sum(p.width for p in parts) + g * (len(parts) - 1), max(p.height for p in parts)), (0, 0, 0, 0))
    x = 0
    for p in parts:
        out.alpha_composite(p, (x, 0))
        x += p.width + g
    out = out.crop(out.getbbox())
    return out.resize((max(1, round(out.width * h / out.height)), h), Image.LANCZOS)


def _grade_image(i):
    """The grade word (WoR's vocals_word_compliment: fontgrid_text_a1 in the grade's colour, grey_dk shadow 1 unit down
    right), centred in WORD_BOX at 6 texels per canvas unit."""
    from PIL import ImageFilter
    word, rgb = GRADES[i]
    S = 6
    W, H = round((WORD_BOX[2] - WORD_BOX[0]) * S), round((WORD_BOX[3] - WORD_BOX[1]) * S)
    t = _spaced(_font('fontgrid_text_a1'), word, round(WORD_H * S), rgb)
    if t.width > W - 2 * S:                                  # squeezed to the box's width like WoR's (height kept)
        t = t.resize((W - 2 * S, t.height), Image.LANCZOS)
    x, y = (W - t.width) // 2, (H - t.height) // 2
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0)
    sh.paste(t.getchannel('A'), (x + S, y + S))
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.4))
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 40)] * 3 + [sh]))
    out.alpha_composite(t, (x, y))
    return out.resize((256, 64), Image.LANCZOS)          # ~205 x 36 px at 1080p


def _get_ready_image():
    """WoR's "Get Ready!" on the vocal highway: fontgrid_title_a1 in white with the grade words' dark soft shadow,
    filling GET_READY_DIMS (512 x 64 texture)."""
    from PIL import ImageFilter
    S = 4
    W, H = round(GET_READY_DIMS[0] * S / 3), round(GET_READY_DIMS[1] * S / 3)
    t = _spaced(_font('fontgrid_title_a1'), GET_READY_TEXT, round(H * 0.78), (255, 255, 255))   # WoR's brush title font
    if t.width > W - 2 * S:
        t = t.resize((W - 2 * S, t.height), Image.LANCZOS)
    x, y = (W - t.width) // 2, (H - t.height) // 2
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0)
    sh.paste(t.getchannel('A'), (x + S // 2, y + S // 2))
    sh = sh.filter(ImageFilter.GaussianBlur(S * 0.5))
    out.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, H), 30)] * 3 + [sh]))
    out.alpha_composite(t, (x, y))
    return out.resize((512, 64), Image.LANCZOS)


def pp_rgb(q):
    """WoR's phrase progress fill colour for a quality 0..1."""
    return PP_RGB[sum(q >= s for s in PP_STEPS)]


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
    out = layer(6, 3.5, halo, 1.4)                         # the halo fades out inside the texture
    out.alpha_composite(layer(3, 1.2, halo, 2.0))
    out.alpha_composite(layer(1, 0.4, core, 2.5))
    return out


def _spike(direction):
    """WoR's white arrowhead (vocal_health_meter_needle's shape), 40 x 52 texels, pointing down or up, over a soft dark
    drop shadow (user 2026-11-06: "the spikes need slightly more shadow"). The texture is padded SPIKE_PAD texels on
    the sides and at the tip for the shadow (SPIKE_W / SPIKE_H grow by the same share, so the arrow keeps its size)."""
    from PIL import ImageChops, ImageDraw, ImageFilter
    w, h = 40, 52
    px, pt = SPIKE_PAD
    W, H = w + 2 * px, h + pt
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).polygon(((px - 1, 0), (px + w + 1, 0), (px + w / 2, h + 3)), fill=255)
    sh = ImageChops.offset(sh, *SPIKE_SHADOW_OFF).filter(ImageFilter.GaussianBlur(SPIKE_SHADOW_BLUR))
    im = Image.merge('RGBA', [Image.new('L', (W, H), 0)] * 3 + [sh.point(lambda v: int(v * SPIKE_SHADOW_A))])
    arrow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(arrow)
    d.polygon(((px, 0), (px + w, 0), (px + w / 2, h)), fill=(150, 150, 155, 255))
    d.polygon(((px + 8, 0), (px + w - 8, 0), (px + w / 2, h - 12)), fill=(255, 255, 255, 255))
    im.alpha_composite(arrow)
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


NOTE_S = 4                                                   # note textures are drawn at 4x, then downsampled


def _note_outline(i):
    """Band i's outline in the 4x drawing: (edge_x, edge_y, box), box = the outer rectangle's inclusive pixels."""
    W, H, S = NOTE_W, 32, NOTE_S
    mid = NOTE_BANDS[i] * 2 ** 0.25                          # geometric middle of the band
    k = H / (NOTE_H_CANVAS * 32 / 17)                        # texels per canvas unit, vertically
    edge_y = max(1, round(NOTE_EDGE * k * S))
    edge_x = max(1, round(NOTE_EDGE * W / mid * S))
    return edge_x, edge_y, (edge_x // 2, 7 * S, W * S - 1 - edge_x // 2, 24 * S)


def note_interior(i):
    """The inside of band i's rectangle (between the inner edges of its walls), as fractions of the note sprite:
    (left, right) of its width and (top, bottom) of its height, 0 = the sprite's left / top edge. The sung-note fill
    is laid over exactly this (plugin kVNoteIn*)."""
    ex, ey, (x0, y0, x1, y1) = _note_outline(i)
    w, h = NOTE_W * NOTE_S, 32 * NOTE_S
    return (x0 + ex + 1) / w, (x1 - ex) / w, (y0 + ey + 1) / h, (y1 - ey) / h


def _note(i):
    """Note texture for length band i: the DE's 32-row profile (tube rows 7..24) as WoR's yellow outline with a warm
    blur, end edges NOTE_EDGE units wide for a note of the band's middle length."""
    from PIL import ImageDraw, ImageFilter
    W, H = NOTE_W, 32
    S = NOTE_S
    k = H / (NOTE_H_CANVAS * 32 / 17)                        # texels per canvas unit, vertically
    edge_x, edge_y, box = _note_outline(i)
    big = (W * S, H * S)

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


def _sp_fill():
    """The vocalist's star power fill: WoR's colours across the strip (SP_PROFILE, top to bottom), the same along it;
    opaque. Laid out for the turned segments: texture rows run along the strip, columns across it (top of the strip on
    the right: child (x, y) -> screen (y, -x))."""
    import numpy as np
    prof = np.array(SP_PROFILE, np.float32)
    h, w = 32, 64                                              # across, along (before turning)
    ys = np.linspace(0, len(prof) - 1, h)
    rows = np.stack([[np.interp(y, range(len(prof)), prof[:, c]) for c in range(3)] for y in ys])
    rgb = np.repeat(rows[:, None, :], w, 1)
    im = Image.fromarray(np.dstack([rgb, np.full((h, w), 255.0)]).astype(np.uint8), 'RGBA')
    return im.transpose(Image.ROTATE_270)                      # strip top -> texture right column


def _sp_tip():
    """A soft white blob for the fill's end."""
    from PIL import ImageDraw, ImageFilter
    im = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    a = Image.new('L', (64, 64), 0)
    ImageDraw.Draw(a).ellipse((14, 14, 50, 50), fill=255)
    im.putalpha(a.filter(ImageFilter.GaussianBlur(6)))
    return im


def textures():
    out = {name: _png(name) for name in ART}
    out[SP_FILL] = _sp_fill()
    out[SP_TIP_TEX] = _sp_tip()
    out[PAINT_TEX] = _paint_tex()
    out[FILL_TEX] = _fill_tex()
    for i in range(NOW_FRAMES):
        out[NOW_TEX[i]] = _lightning(NOW_CORE, NOW_GLOW, 11 + i)
        out[NOW_SP_TEX[i]] = _lightning(NOW_SP_CORE, NOW_SP_GLOW, 11 + i)
    out.update({SPIKE_TEX[k]: _spike(k).resize((32, 64), Image.LANCZOS) for k in SPIKE_TEX})   # power-of-two sizes
    out[SP_GLOW_TEX] = _sp_glow()
    out.update({NOTE_TEX[i]: _note(i) for i in range(len(NOTE_TEX))})
    out[METER_SHADE] = _shade(HEALTH[2] - HEALTH[0], HEALTH[3] - HEALTH[1], 1.0, 1.0, True, 1.2).resize((512, 128), Image.LANCZOS)
    out[LAMP_SHADE] = _shade(GREEN[2] - GREEN[0], GREEN[3] - GREEN[1], 2.5, 1.0, False, 2.6).resize((128, 128), Image.LANCZOS)
    out.update({MULT_TEX[n]: _mult_image(n, n) for n in MULT_TEX})
    out.update({MULT_SP_TEX[n]: _mult_image(n, 'sp') for n in MULT_SP_TEX})
    out.update({GRADE_TEX[i]: _grade_image(i) for i in range(len(GRADES))})
    out[GET_READY_TEX] = _get_ready_image()
    return out


def sources():
    s = {name: {'src': os.path.join(d, n + '.png'), 'box': None, 'flip': False} for name, (d, n) in ART.items()}
    for name in NOW_TEX + NOW_SP_TEX + list(SPIKE_TEX.values()) + NOTE_TEX + [SP_GLOW_TEX, METER_SHADE, LAMP_SHADE,
                                                                              SP_FILL, SP_TIP_TEX, PAINT_TEX, FILL_TEX]:
        s[name] = {'src': 'generated (tools/wor_vocals.py)', 'box': None, 'flip': False}
    for n in MULT_TEX:
        s[MULT_TEX[n]] = {'src': 'fontgrid_text_a1 + fontgrid_numeral_A1_b', 'text': f'x{n}', 'style': str(n), 'box': None, 'flip': False}
    for n in MULT_SP_TEX:
        s[MULT_SP_TEX[n]] = {'src': 'fontgrid_text_a1 + fontgrid_numeral_A1_b', 'text': f'x{n}', 'style': 'sp', 'box': None, 'flip': False}
    s[GET_READY_TEX] = {'src': 'fontgrid_title_a1', 'text': GET_READY_TEXT, 'box': None, 'flip': False}
    for i, (word, rgb) in enumerate(GRADES):
        s[GRADE_TEX[i]] = {'src': 'fontgrid_text_a1', 'text': word, 'rgb': list(rgb), 'box': None, 'flip': False}
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
    """QB globals: the DE's comet particle table redefined under its own name with the "miss" sparks invisible (mock
    v3: the purple ball when not singing; every HUD theme: copying a replacement in by script with change ~ crashed
    vocals_create_highway, 2026-10-27), and our star power flag for the plugin."""
    import re
    src = fx_text[fx_text.index('SectionStruct vocals_comet_particle_effects'):]
    depth, end = 0, None
    for k, ch in enumerate(src):
        depth += {'{': 1, '}': -1}.get(ch, 0)
        if ch == '}' and depth == 0:
            end = k + 1
            break
    de = src[:end]
    # every "miss" struct: start colour alpha 0
    wor = re.sub(r'(StructStruct miss\s*\{\s*StructHeader\s*\{\s*StructArray start_color\s*\{\s*ArrayInteger\s*\[\s*\d+\s+\d+\s+\d+\s+)\d+',
                 r'\g<1>0', de)
    assert wor.count('StructStruct miss') == de.count('StructStruct miss') == 2 and wor != de
    # the singing sparks (orange Spark01 at 1.6 / 1.5: a big fireball, user 2026-10-27): WoR draws only a small yellow
    # flare along the sung note
    n_base = 0

    def base(m):
        nonlocal n_base
        n_base += 1
        (s0, e0) = COMET_SPARK_RGBA
        # the QB text takes one array value per line (2026-11-04: "255 200 60 255" on one line compiled to [0])
        def arr(c):
            return '\n' + ''.join(f'\t\t\t\t\t\t\t{v}\n' for v in c) + '\t\t\t\t\t\t'
        blk = re.sub(r'(StructArray start_color\s*\{\s*ArrayInteger\s*\[)[^\]]*(\])', lambda mm: mm.group(1) + arr(s0) + mm.group(2), m.group(0), count=1)
        blk = re.sub(r'(StructArray end_color\s*\{\s*ArrayInteger\s*\[)[^\]]*(\])', lambda mm: mm.group(1) + arr(e0) + mm.group(2), blk, count=1)
        blk = re.sub(r'(StructFloatX2 start_scale\s*\{\s*Floats \[)[^\]]*(\])', rf'\g<1>{COMET_SPARK[0]:.5f}, {COMET_SPARK[0]:.5f}\g<2>', blk, count=1)
        blk = re.sub(r'(StructFloatX2 end_scale\s*\{\s*Floats \[)[^\]]*(\])', rf'\g<1>{COMET_SPARK[1]:.5f}, {COMET_SPARK[1]:.5f}\g<2>', blk, count=1)
        blk, nv = re.subn(r'StructFloat velocity = [-\d.]+', 'StructFloat velocity = 0.00', blk, count=1)
        blk, nt = re.subn(r'StructFloat time = [-\d.]+', f'StructFloat time = {COMET_SPARK_TIME:.2f}', blk, count=1)
        assert nv == nt == 1, (nv, nt)
        return blk
    # each base block from its material to its time (the last field)
    wor = re.sub(r'StructQBKey material = sys_Particle_Spark01_sys_Particle_Spark01\s*StructArray start_color\s*\{\s*ArrayInteger\s*\[\s*255\s+128\s+0\s+255\s*\]\s*\}'
                 r'(?:(?!StructQBKey material).)*?StructFloat time = [-\d.]+', base, wor, flags=re.S)
    assert n_base == 2, n_base
    return '\n'.join([wor, 'SectionInteger WoR_HUD_vocal_sp 0\n', 'SectionInteger WoR_HUD_get_ready 0\n',
                      'SectionInteger WoR_HUD_phrase_start 0\n', 'SectionInteger WoR_HUD_phrase_end 0\n',
                      'SectionInteger WoR_HUD_phrase_ms 0\n'])

def _globals_body(ours):
    if os.environ.get('WOR_NO_VGLOBALS'):          # bisect switch (2026-10-27 crash at vocals_create_highway)
        return ''
    scale = LYRIC_SCALE if ours else LYRIC_SCALE_DE
    col = LYRIC_RGBA if ours else LYRIC_RGBA_DE
    tag = 'wor' if ours else 'de'
    return (f'\t\t:i $change$$vocal_lyric_font_scale$ = %vec2({scale[0]},{scale[1]})\n'
            f'\t\t:i $change$$vocal_scrolling_lyric_rgba$ = {_qb_rgba(col["upcoming"])}\n'
            f'\t\t:i $change$$vocal_scrolling_word_highlight$ = {_qb_rgba(col["current"])}\n'
            f'\t\t:i $change$$vocal_scrolling_lyric_after$ = {_qb_rgba(col["sung"])}\n'
            # 1.89 (user 2026-11-06: no line behind the now line, the sung parts of the notes FILLED as in WoR): the
            # DE's sprite paint (read per highway at its creation, 0x4711f0) instead of the Waveform_UI trace; the
            # segments are ours (WoR_HUD_vocal_create_paint)
            f'\t\t:i $change$$vocal_enable_material_paint$ = %i({0 if ours else 1})\n'
            )   # NOT changed: vocal_gem_colors / vocals_comet_particle_effects (copying them with ~ crashed vocals_create_highway, 2026-10-27)


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
    # 4-player band (hud_3g1v, user 2026-10-27 recording): the vocalist's health meter (our BAND_top_meter instance)
    # never shows, while the same panel in hud_1g1v does; what hides it isn't found in the DE scripts yet. A second after
    # setup, a vocalist's meter that is hidden is shown and the DE's health widget attached to it (as guitar_hud does);
    # its state is logged either way.
    'Script WoR_HUD_vocal_health_start [\n'
    '\t:i if $[4c1beb8d]$$value$ = $WoR_HUD_sp_highway$\n'
    '\t\t:i $KillSpawnedScript$$id$ = $WoR_HUD_vocal_health$\n'
    '\t\t:i $spawnscriptnow$$WoR_HUD_vocal_health$$id$ = $WoR_HUD_vocal_health$\n'
    '\t\t:i $KillSpawnedScript$$id$ = $WoR_HUD_vocal_get_ready$\n'
    '\t\t:i $spawnscriptnow$$WoR_HUD_vocal_get_ready$$id$ = $WoR_HUD_vocal_get_ready$\n'
    '\t\t:i $KillSpawnedScript$$id$ = $WoR_HUD_vocal_phrase_watch$\n'
    '\t\t:i $spawnscriptnow$$WoR_HUD_vocal_phrase_watch$$id$ = $WoR_HUD_vocal_phrase_watch$\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # the phrase box over the whole phrase (user 2026-11-07: "the precision bar needs to be the sum of all notes in the
    # phrase, currently you're doing precision per word"): the song's <prefix>_vocals_phrases (time, flag pairs: the
    # phrase boundaries, ms) gives the current phrase; its notes' total length comes from <prefix>_song_vocals (time,
    # length, pitch), scanned 16 notes a frame from a running pointer (sorted arrays). The plugin reads
    # WoR_HUD_phrase_start / _end / _ms (0 until the scan is done). Stops when the song's arrays are gone.
    'Script WoR_HUD_vocal_phrase_watch [\n'
    '\t:i $change$$WoR_HUD_phrase_start$ = %i(0)\n'
    '\t:i $change$$WoR_HUD_phrase_end$ = %i(0)\n'
    '\t:i $change$$WoR_HUD_phrase_ms$ = %i(0)\n'
    '\t:i $get_song_prefix$$song$ = (~$current_song$)\n'
    '\t:i $FormatText$$checksumname$ = $WoR_notes$%s("%s_song_vocals")$s$ = %GLOBAL%$song_prefix$$addtostringlookup$\n'
    '\t:i $FormatText$$checksumname$ = $WoR_phr$%s("%s_vocals_phrases")$s$ = %GLOBAL%$song_prefix$$addtostringlookup$\n'
    '\t:i if NOT $GlobalExists$$name$ = %GLOBAL%$WoR_notes$$type$ = $array$\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i if NOT $GlobalExists$$name$ = %GLOBAL%$WoR_phr$$type$ = $array$\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $GetArraySize$~%GLOBAL%$WoR_notes$\n'
    '\t:i $WoR_nsize$ = %GLOBAL%$array_size$\n'
    '\t:i $printf$%s("WoR_HUD: phrase watch on")\n'
    '\t:i $GetArraySize$~%GLOBAL%$WoR_phr$\n'
    '\t:i $WoR_psize$ = %GLOBAL%$array_size$\n'
    '\t:i if (%GLOBAL%$WoR_psize$ < %i(2))\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $WoR_pi$ = %i(0)\n'
    '\t:i $WoR_nj$ = %i(0)\n'
    '\t:i $WoR_ms$ = %i(0)\n'
    '\t:i $WoR_done$ = %i(0)\n'
    '\t:i $WoR_start$ = (~%GLOBAL%$WoR_phr$:a{%i(0):a})\n'
    '\t:i $WoR_end$ = %i(999999999)\n'
    '\t:i if (%GLOBAL%$WoR_psize$ > %i(2))\n'
    '\t\t:i $WoR_end$ = (~%GLOBAL%$WoR_phr$:a{%i(2):a})\n'
    '\t:i endif\n'
    '\t:i $change$$WoR_HUD_phrase_start$ = %GLOBAL%$WoR_start$\n'
    '\t:i $change$$WoR_HUD_phrase_end$ = %GLOBAL%$WoR_end$\n'
    '\t:i while \n'
    '\t\t:i if NOT $GlobalExists$$name$ = %GLOBAL%$WoR_notes$$type$ = $array$\n'
    '\t\t\t:i return\n'
    '\t\t:i endif\n'
    '\t\t:i if NOT $GlobalExists$$name$ = %GLOBAL%$WoR_phr$$type$ = $array$\n'
    '\t\t\t:i return\n'
    '\t\t:i endif\n'
    '\t\t:i $getsongtimems$\n'
    # the next phrase (one step a frame: catches up within a few frames after a skipped lead-in)
    '\t\t:i $WoR_pn$ = (%GLOBAL%$WoR_pi$ + %i(2))\n'
    '\t\t:i if (%GLOBAL%$WoR_pn$ < %GLOBAL%$WoR_psize$)\n'
    '\t\t\t:i if (%GLOBAL%$time$ >= (~%GLOBAL%$WoR_phr$:a{%GLOBAL%$WoR_pn$:a}))\n'
    '\t\t\t\t:i $WoR_pi$ = %GLOBAL%$WoR_pn$\n'
    '\t\t\t\t:i $WoR_start$ = (~%GLOBAL%$WoR_phr$:a{%GLOBAL%$WoR_pi$:a})\n'
    '\t\t\t\t:i $WoR_end$ = %i(999999999)\n'
    '\t\t\t\t:i $WoR_pn$ = (%GLOBAL%$WoR_pi$ + %i(2))\n'
    '\t\t\t\t:i if (%GLOBAL%$WoR_pn$ < %GLOBAL%$WoR_psize$)\n'
    '\t\t\t\t\t:i $WoR_end$ = (~%GLOBAL%$WoR_phr$:a{%GLOBAL%$WoR_pn$:a})\n'
    '\t\t\t\t:i endif\n'
    '\t\t\t\t:i $WoR_ms$ = %i(0)\n'
    '\t\t\t\t:i $WoR_done$ = %i(0)\n'
    '\t\t\t\t:i $change$$WoR_HUD_phrase_ms$ = %i(0)\n'
    '\t\t\t\t:i $change$$WoR_HUD_phrase_start$ = %GLOBAL%$WoR_start$\n'
    '\t\t\t\t:i $change$$WoR_HUD_phrase_end$ = %GLOBAL%$WoR_end$\n'
    '\t\t\t:i endif\n'
    '\t\t:i endif\n'
    # the phrase's notes: up to 16 a frame from the running pointer
    '\t\t:i if (%GLOBAL%$WoR_done$ = %i(0))\n'
    '\t\t\t:i while \n'
    '\t\t\t\t:i if (%GLOBAL%$WoR_done$ = %i(0))\n'
    '\t\t\t\t\t:i if (%GLOBAL%$WoR_nj$ < %GLOBAL%$WoR_nsize$)\n'
    '\t\t\t\t\t\t:i $WoR_nt$ = (~%GLOBAL%$WoR_notes$:a{%GLOBAL%$WoR_nj$:a})\n'
    '\t\t\t\t\t\t:i if (%GLOBAL%$WoR_nt$ < %GLOBAL%$WoR_end$)\n'
    '\t\t\t\t\t\t\t:i if (%GLOBAL%$WoR_nt$ >= %GLOBAL%$WoR_start$)\n'
    '\t\t\t\t\t\t\t\t:i $WoR_nl$ = (%GLOBAL%$WoR_nj$ + %i(1))\n'
    '\t\t\t\t\t\t\t\t:i $WoR_ms$ = (%GLOBAL%$WoR_ms$ + (~%GLOBAL%$WoR_notes$:a{%GLOBAL%$WoR_nl$:a}))\n'
    '\t\t\t\t\t\t\t:i endif\n'
    '\t\t\t\t\t\t\t:i $WoR_nj$ = (%GLOBAL%$WoR_nj$ + %i(3))\n'
    '\t\t\t\t\t\t:i else \n'
    '\t\t\t\t\t\t\t:i $WoR_done$ = %i(1)\n'
    '\t\t\t\t\t\t:i endif\n'
    '\t\t\t\t\t:i else \n'
    '\t\t\t\t\t\t:i $WoR_done$ = %i(1)\n'
    '\t\t\t\t\t:i endif\n'
    '\t\t\t\t:i endif\n'
    '\t\t\t:i loop_to %i(16)\n'
    '\t\t\t:i if (%GLOBAL%$WoR_done$ = %i(1))\n'
    '\t\t\t\t:i $change$$WoR_HUD_phrase_ms$ = %GLOBAL%$WoR_ms$\n'
    '\t\t\t:i endif\n'
    '\t\t:i endif\n'
    '\t\t:i $wait$%i(1)$gameframe$\n'
    '\t:i loop_to %i(216000)\n'
    '\t:i endfunction\n]\n\n'
    # WoR's "Get Ready!" (user 2026-11-06: it appears abruptly 5 s before the first vocal note and stays 3 s, centred
    # on the vocal highway): the song's <prefix>_song_vocals array (time, length, pitch per note, ms) gives the first
    # note; one wait to GET_READY_LEAD before it, the text on every vocalist's highway, GET_READY_SHOW later off again
    'Script WoR_HUD_vocal_get_ready [\n'
    '\t:i $wait$%f(0.5)$seconds$\n'
    '\t:i $get_song_prefix$$song$ = (~$current_song$)\n'
    '\t:i $FormatText$$checksumname$ = $WoR_notes$%s("%s_song_vocals")$s$ = %GLOBAL%$song_prefix$$addtostringlookup$\n'
    '\t:i if NOT $GlobalExists$$name$ = %GLOBAL%$WoR_notes$$type$ = $array$\n'
    '\t\t:i $printf$%s("WoR_HUD: get ready: no %s")$s$ = %GLOBAL%$WoR_notes$\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $GetArraySize$~%GLOBAL%$WoR_notes$\n'
    '\t:i if (%GLOBAL%$array_size$ < %i(1))\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    # (1.90's single wait from the song time at the start was off: AutoLaunch skips the lead-in) the song time is
    # polled every frame, up to 10 minutes; at the mark the plugin shows the sprite while WoR_HUD_get_ready is 1
    f'\t:i $WoR_mark$ = ((~%GLOBAL%$WoR_notes$:a{{%i(0):a}}) - %i({GET_READY_LEAD}))\n'
    '\t:i $printf$%s("WoR_HUD: get ready at song time %m ms, first vocal note %n ms")$m$ = %GLOBAL%$WoR_mark$'
    '$n$ = (~%GLOBAL%$WoR_notes$:a{%i(0):a})\n'
    '\t:i while \n'
    '\t\t:i $getsongtimems$\n'
    '\t\t:i if (%GLOBAL%$time$ >= %GLOBAL%$WoR_mark$)\n'
    '\t\t\t:i $printf$%s("WoR_HUD: get ready shown at song time %t ms")$t$ = %GLOBAL%$time$\n'
    '\t\t\t:i $change$$WoR_HUD_get_ready$ = %i(1)\n'
    f'\t\t\t:i $wait$%f({GET_READY_SHOW / 1000:.1f})$seconds$\n'
    '\t\t\t:i $change$$WoR_HUD_get_ready$ = %i(0)\n'
    '\t\t\t:i return\n'
    '\t\t:i endif\n'
    '\t\t:i $wait$%i(1)$gameframe$\n'
    '\t:i loop_to %i(36000)\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_vocal_health [\n'
    '\t:i $wait$%f(1.0)$seconds$\n'
    '\t:i $GameMode_GetNumPlayersShown$\n'
    '\t:i $p$ = %i(1)\n'
    '\t:i while \n'
    '\t\t:i $getplayerinfo$%GLOBAL%$p$$part$\n'
    '\t\t:i if (%GLOBAL%$part$ = $Vocals$)\n'
    '\t\t\t:i $getplayerinfo$%GLOBAL%$p$$hud_parent$\n'
    '\t\t\t:i if $ScreenElementExists$$id$ = $hud_root$\n'
    '\t\t\t\t:i if $hud_root$.$desc_resolvealias$$name$ = %GLOBAL%$hud_parent$$param$ = $parent_id$\n'
    '\t\t\t\t\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$parent_id$$child$ = $BAND_top_meter$:s}\n'
    '\t\t\t\t\t\t:i $ResolveScreenElementID$$id$ = :s{%GLOBAL%$parent_id$$child$ = $BAND_top_meter$:s}$param$ = $meter_id$\n'
    '\t\t\t\t\t\t:i $GetScreenElementProps$$id$ = %GLOBAL%$meter_id$\n'
    '\t\t\t\t\t\t:i $printf$%s("WoR_HUD: vocal health meter p%p alpha %a")$p$ = %GLOBAL%$p$$a$ = %GLOBAL%$alpha$\n'
    '\t\t\t\t\t\t:i if (%GLOBAL%$alpha$ < %f(0.5))\n'
    '\t\t\t\t\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$meter_id$$alpha$ = %i(1)\n'
    '\t\t\t\t\t\t\t:i $HUD_attach_widget_player_health$$Vocals$ = %i(1)$parent_id$ = :s{%GLOBAL%$parent_id$$child$ = $BAND_top_meter$:s}$player$ = %GLOBAL%$p$\n'
    '\t\t\t\t\t\t:i endif\n'
    '\t\t\t\t\t:i else \n'
    '\t\t\t\t\t\t:i $printf$%s("WoR_HUD: vocal health meter p%p: no BAND_top_meter")$p$ = %GLOBAL%$p$\n'
    '\t\t\t\t\t:i endif\n'
    '\t\t\t\t:i endif\n'
    '\t\t\t:i endif\n'
    '\t\t:i endif\n'
    '\t\t:i %GLOBAL%$p$ = (%GLOBAL%$p$ + %i(1))\n'
    '\t:i loop_to %GLOBAL%$num_players_shown$\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_vocal_note_setup_orig [\n'
    '\t:i $printf$%s("WoR_HUD: vocal note setup placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')


def _v2(x, y):
    return f'%vec2({x:.4f},{y:.4f})'


def grade_scripts():
    """Phrase end (plugin swap of the DE's ddb4a0e3, which runs with quality 0..1 and player at every phrase end):
    the DE's own body still runs (its message is hidden by our vocals_message swap, its comet / border flash stay),
    then with our theme WoR's grade flip in the vocalist's panel (props of wor_vocal_mult_ghwor)."""
    wait = '\t\t:i $wait$%i(1)$gameframe$\n'
    fold = [1.0 - (k + 1) / FLIP_STEPS for k in range(FLIP_STEPS)]           # 5/6 .. 0
    grow = [(k + 1) / FLIP_STEPS for k in range(FLIP_STEPS)]                 # 1/6 .. 1
    set_ = '\t\t:i %GLOBAL%$meter_id$.$se_setprops$'
    out = ('Script WoR_HUD_vocal_phrase_end [\n'
           '\t:i $WoR_HUD_vocal_phrase_end_orig$ isNull\n'
           '\t:i if $[4c1beb8d]$$value$ = $WoR_HUD_sp_highway$\n'
           '\t\t:i if NOT $GotParam$$quality$\n'
           '\t\t\t:i $quality$ = %f(1.0)\n'
           '\t\t:i endif\n'
           '\t\t:i $KillSpawnedScript$$id$ = $WoR_HUD_vocal_grade$\n'
           '\t\t:i $spawnscriptnow$$WoR_HUD_vocal_grade$$id$ = $WoR_HUD_vocal_grade$'
           '$params$ = :s{$player$ = %GLOBAL%$player$$quality$ = %GLOBAL%$quality$:s}\n'
           '\t:i endif\n'
           '\t:i endfunction\n]\n\n'
           'Script WoR_HUD_vocal_phrase_end_orig [\n'
           '\t:i $printf$%s("WoR_HUD: vocal phrase end placeholder ran, plugin swap missing")\n'
           '\t:i endfunction\n]\n\n'
           # the vocalist's panel: player_meter of the player's v1 container (as WoR_HUD_vocal_health finds it)
           'Script WoR_HUD_vocal_grade [\n'
           '\t:i $getplayerinfo$%GLOBAL%$player$$hud_parent$\n'
           '\t:i if $ScreenElementExists$$id$ = $hud_root$\n'
           '\t\t:i if $hud_root$.$desc_resolvealias$$name$ = %GLOBAL%$hud_parent$$param$ = $parent_id$\n'
           '\t\t\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$parent_id$$child$ = $player_meter$:s}\n'
           '\t\t\t\t:i $ResolveScreenElementID$$id$ = :s{%GLOBAL%$parent_id$$child$ = $player_meter$:s}$param$ = $meter_id$\n'
           '\t\t\t\t:i $WoR_HUD_vocal_grade_flip$$meter_id$ = %GLOBAL%$meter_id$$quality$ = %GLOBAL%$quality$\n'
           '\t\t\t:i endif\n'
           '\t\t:i endif\n'
           '\t:i endif\n'
           '\t:i endfunction\n]\n\n'
           'Script WoR_HUD_vocal_grade_flip [\n'
           '\t:i $q$ = %GLOBAL%$quality$\n'
           '\t:i if (%GLOBAL%$q$ < %f(0.0))\n\t\t:i $q$ = %f(0.0)\n\t:i endif\n'
           '\t:i if (%GLOBAL%$q$ > %f(1.0))\n\t\t:i $q$ = %f(1.0)\n\t:i endif\n'
           '\t:i $WoR_i$ = %i(0)\n')
    for i, m in enumerate(GRADE_MIN[1:], 1):
        out += f'\t:i if (%GLOBAL%$q$ >= %f({m:.2f}))\n\t\t:i $WoR_i$ = %i({i})\n\t:i endif\n'
    out += ('\t:i $WoR_grades$ = :a{' + ''.join(f'${t}$' for t in GRADE_TEX) + ':a}\n'
            '\t:i $WoR_tex$ = (%GLOBAL%$WoR_grades$:a{%GLOBAL%$WoR_i$:a})\n')
    out += '\t:i if $ScreenElementExists$$id$ = %GLOBAL%$meter_id$\n'
    # 1. the multiplier and the phrase box fold away (the fill folds with the box; its level is the plugin's)
    for s in fold:
        out += (f'{set_}$WoR_nixie_scale$ = {_v2(1, s)}$WoR_pp_tube_scale$ = {_v2(1, s)}'
                f'$WoR_pp_fill_scale$ = {_v2(0, s)}\n{wait}')
    # 2. the grade word unfolds, holds 0.4 s, folds
    out += f'{set_}$WoR_word_texture$ = %GLOBAL%$WoR_tex$$WoR_word_alpha$ = %f(1.0)\n'
    for s in grow:
        out += f'{set_}$WoR_word_scale$ = {_v2(1, s)}\n{wait}'
    out += '\t\t:i $wait$%f(0.4)$seconds$\n'
    for s in fold:
        out += f'{set_}$WoR_word_scale$ = {_v2(1, s)}\n{wait}'
    out += f'{set_}$WoR_word_alpha$ = %f(0.0)\n'
    # 3. the meters unfold; the box starts empty and fills live through the next phrase (WoR)
    for s in grow:
        out += (f'{set_}$WoR_nixie_scale$ = {_v2(1, s)}$WoR_pp_tube_scale$ = {_v2(1, s)}'
                f'$WoR_pp_fill_scale$ = {_v2(0, s)}\n')
        if s < 1.0:
            out += wait
    out += '\t:i endif\n\t:i endfunction\n]\n'
    return out


# The pitch trace (the DE's ekgelement, a Waveform_UI material made by vocals_setup_paint_material): the DE paints it
# orange (user 2026-11-04: "an orange trail behind the green plasma line"); WoR's same script and its star power
# on / off set yellow (cyan in star power), which fills the sung parts of the notes. m_psColors0..7 (x, y, z, w), from
# WoR's vocals_highway_fx (setup = star power off).
PAINT_WOR = {
    'off': [(0.99, 0.91, 0.21, 0.0), (0.99, 0.99, 0.26, 1.5), (1.0, 0.75, 0.12, 0.0), (0.0, 0.0, 0.0, 0.0),
            (2.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.1, 0.0), (1.0, 0.6, 0.2, 0.0), (1.0, 1.0, 0.3, 0.0)],
    'on': [(0.26, 1.0, 0.99, 0.0), (0.26, 1.0, 0.99, 1.0), (0.12, 0.75, 1.0, 0.0), (0.0, 0.0, 0.0, 0.0),
           (0.0, 1.4, 1.4, 0.0), (0.0, 0.0, 0.1, 0.0), (0.2, 0.6, 1.0, 0.0), (0.3, 1.0, 1.0, 0.0)],
}
# the plugin swaps (kScriptSwaps): DE script -> ours; the DE body moves to the _orig placeholder
# sung-note fill (sprite paint, WoR_HUD_vocal_create_paint): texture, height in the note container (notes 15 tall with
# 3-unit outlines), WoR's yellow / star power cyan
PAINT_TEX = 'WoR_HUD_vpaint'
FILL_TEX, FILL_POOL = 'WoR_HUD_vfill', 24          # 1.92: the plugin's own sung-note fill (sprites in note_scale)
PAINT_H = 11.0
# 1.94 (user 2026-11-07: "the filled boxes never can be outside the box, need to be the exact same color as the border
# and needs to be as tall as the rectangle itself so it touches the walls"): the fill is the outline's own colour (in
# star power too: the outlines stay yellow), solid, laid over the rectangle's inside (note_interior) and FILL_OVERLAP
# canvas units into each wall so no dark seam shows between the fill and the walls
PAINT_RGB, PAINT_SP_RGB = NOTE_RGB, (120, 255, 255)
FILL_OVERLAP = 0.75
PAINT_SWAPS = [('vocals_setup_paint_material', 'WoR_HUD_vocal_paint_setup', 'off'),
               ('vocals_paint_star_power_on', 'WoR_HUD_vocal_paint_sp_on', 'on'),
               ('vocals_paint_star_power_off', 'WoR_HUD_vocal_paint_sp_off', 'off')]


def paint_scripts():
    out = ''
    for de, ours, state in PAINT_SWAPS:
        out += (f'Script {ours} [\n'
                '\t:i if NOT $GotParam$$player$\n\t\t:i $player$ = %i(1)\n\t:i endif\n'
                f'\t:i ${ours}_orig$$player$ = %GLOBAL%$player$\n'
                '\t:i if $[4c1beb8d]$$value$ = $WoR_HUD_sp_highway$\n'
                f'\t\t:i $WoR_HUD_vocal_paint_colours$$player$ = %GLOBAL%$player$$state$ = ${state}$\n'
                '\t:i endif\n'
                '\t:i endfunction\n]\n\n'
                f'Script {ours}_orig [\n'
                f'\t:i $printf$%s("WoR_HUD: {ours} placeholder ran, plugin swap missing")\n'
                '\t:i endfunction\n]\n\n')
    out += ('Script WoR_HUD_vocal_paint_colours [\n'
            '\t:i $VocalsHighway_GetId$$player$ = %GLOBAL%$player$\n'
            '\t:i if NOT $ScreenElementExists$$id$ = :s{%GLOBAL%$vocals_highway_id$$child$ = $ekgelement$:s}\n'
            '\t\t:i return\n\t:i endif\n'
            '\t:i $VocalsHighway_GetMaterial$$player$ = %GLOBAL%$player$\n')
    for k, state in enumerate(('on', 'off')):
        out += f'\t:i {"if" if k == 0 else "else"} {"(%GLOBAL%$state$ = $on$)" if k == 0 else ""}\n'.replace('else \n', 'else \n')
        for i, (x, y, z, w) in enumerate(PAINT_WOR[state]):
            out += ('\t\t:i $SetMaterialProperty$$mat$ = %GLOBAL%$vocals_highway_material_text$'
                    f'$prop$ = %s("m_psColors{i}")$x$ = %f({x})$y$ = %f({y})$z$ = %f({z})$w$ = %f({w})\n')
    out += '\t:i endif\n\t:i endfunction\n]\n\n'
    # sprite paint (the engine runs vocals_create_paint for each sung segment, hit = paint_hit / paint_miss /
    # paint_default, at the sung pitch, and stretches the returned stretch_id along it): with the WoR theme a hit
    # segment is a solid fill inside the note (yellow, cyan in star power), misses invisible
    cy, sp = PAINT_RGB, PAINT_SP_RGB
    out += ('Script WoR_HUD_vocal_create_paint [\n'
            '\t:i if NOT ($[4c1beb8d]$$value$ = $WoR_HUD_sp_highway$)\n'
            '\t\t:i $WoR_HUD_vocal_create_paint_orig$ isNull\n'
            '\t\t:i return$id$ = %GLOBAL%$id$$stretch_id$ = %GLOBAL%$stretch_id$\n'
            '\t:i endif\n'
            '\t:i $VocalsHighway_GetId$$player$ = %GLOBAL%$player$\n'
            '\t:i %GLOBAL%$vocals_highway_id$.$desc_resolvealias$$name$ = $alias_note_scale$$param$ = $note_scale$\n'
            f'\t:i $WoR_rgba$ = {_qb_rgba(cy + (0,))}\n'
            '\t:i if (%GLOBAL%$hit$ = $paint_hit$)\n'
            f'\t\t:i $WoR_rgba$ = {_qb_rgba(cy + (255,))}\n'
            '\t\t:i if (~$WoR_HUD_vocal_sp$ = %i(1))\n'
            f'\t\t\t:i $WoR_rgba$ = {_qb_rgba(sp + (255,))}\n'
            '\t\t:i endif\n'
            '\t:i endif\n'
            '\t:i $CreateScreenElement$:s{$parent$ = %GLOBAL%$note_scale$$type$ = $ContainerElement$'
            '$just$ = :a{$left$$center$:a}$Pos$ = %GLOBAL%$Pos$$z_priority$ = %i(6):s}\n'
            '\t:i $container_id$ = %GLOBAL%$id$\n'
            '\t:i $CreateScreenElement$:s{$parent$ = %GLOBAL%$container_id$$local_id$ = $note_left$$type$ = $SpriteElement$'
            '$just$ = :a{$left$$center$:a}$texture$ = $WoR_HUD_blank$$dims$ = %vec2(1.0,1.0)$alpha$ = %f(0.0):s}\n'
            '\t:i $CreateScreenElement$:s{$parent$ = %GLOBAL%$container_id$$local_id$ = $note_middle$$type$ = $SpriteElement$'
            f'$just$ = :a{{$left$$center$:a}}$texture$ = ${PAINT_TEX}$$dims$ = %vec2(1.0,{PAINT_H:.1f})'
            '$rgba$ = %GLOBAL%$WoR_rgba$:s}\n'
            '\t:i $middle_id$ = %GLOBAL%$id$\n'
            '\t:i $CreateScreenElement$:s{$parent$ = %GLOBAL%$container_id$$local_id$ = $note_right$$type$ = $SpriteElement$'
            '$just$ = :a{$left$$center$:a}$texture$ = $WoR_HUD_blank$$dims$ = %vec2(1.0,1.0)$alpha$ = %f(0.0):s}\n'
            '\t:i return$id$ = %GLOBAL%$container_id$$stretch_id$ = %GLOBAL%$middle_id$\n'
            '\t:i endfunction\n]\n\n'
            'Script WoR_HUD_vocal_create_paint_orig [\n'
            '\t:i $printf$%s("WoR_HUD: vocal create paint placeholder ran, plugin swap missing")\n'
            '\t:i endfunction\n]\n')
    return out


DE_NOW_BAR = dict(x=121.0, w=32.0)        # the DE's now_bar in the highway root: pos x, dims w (just right)
DE_PITCH_AREA = dict(x=17.0, w=20.0)      # pitch_area in now_bar: pos x, dims w (just centre)


def now_line_root_x():
    """1.93: the visible now line's x in the vocal highway root (WoR_now_line's centre: now_bar's left edge + pitch_area's
    left edge + NOW_BOX x). 118: 929 px in the 2560x1080 frames (root 288, 1.5 px a unit, 320 px bars), measured 928."""
    bar_left = DE_NOW_BAR['x'] + NOW_BAR_DX - DE_NOW_BAR['w']
    area_left = DE_PITCH_AREA['x'] - DE_PITCH_AREA['w'] / 2
    return bar_left + area_left + NOW_BOX[0]


def _paint_tex():
    """The fill of a sung note segment: white (tinted by the segment's rgba), soft top and bottom edges."""
    import numpy as np
    h, w = 32, 16
    y = np.abs(np.linspace(-1, 1, h))
    a = np.clip((1.0 - y) / 0.25, 0, 1)                       # the outer eighth fades
    v = 1.0 - 0.18 * y ** 2                                    # a little brighter in the middle
    rgb = np.repeat((v * 255)[:, None], w, 1)
    al = np.repeat((a * 255)[:, None], w, 1)
    return Image.fromarray(np.dstack([rgb, rgb, rgb, al]).astype(np.uint8), 'RGBA')


def _fill_tex():
    """1.94: the plugin's sung-note fill: solid opaque white (tinted to the outline's colour), hard edges, so it meets
    the walls with no fade or gradient."""
    return Image.new('RGBA', (16, 16), (255, 255, 255, 255))


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
    # 2026-10-27 (4-player band: the health lamps never showed, the meter logged alpha 1): the panel's backing is on
    # player_meter, whose z is the layout's (2 in hud_1g1v, 11 in hud_3g1v): the health meter and the strip go just above
    # it, or the backing covers them
    import re
    pa, pb = desc_edit._block_bounds(blk, re.search(r'StructQBKey local_id = player_meter\s*\n', blk).start())
    pm_z = float(re.search(r'z_priority = ([-\d.]+)', blk[pa:pb]).group(1))
    zs = {HEALTH_NAME: pm_z + 0.1, SP_NAME: max(SP_Z, pm_z + 0.2)}
    blocks = [E(child, 'descinterface', pos=pos, dims=(1280, 720), just=(-1, -1), z=zs[name], desc=name).render(0)
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
    d = desc_edit.set_elem(d, 'now_bar', pos=(121.0 + NOW_BAR_DX, 30.0))     # the DE's: (121, 30)
    d = desc_edit.set_elem(d, 'fireball_bg', scale=(COMET_SCALE, COMET_SCALE))
    # the highway's background: WoR's dim dark; its bg_rgba prop (the DE's teal) lands on a hidden stand-in
    d = _edit_first(d, 'bG', lambda blk: _rgba(blk, HIGHWAY_BG_RGBA, HIGHWAY_BG_ALPHA))
    d = _retarget_to_new_root_child(d, 'bg_rgba', 'WoR_bg_sink')
    d = wor_mp._append_children(d, 'root', [E('WoR_bg_sink', 'SpriteElement', dims=(4, 4), alpha=0.0,
                                               texture='WoR_HUD_blank').render(0)])
    # the now line (the plugin steps through the frames, green or cyan by WoR_HUD_vocal_sp) and the arrowheads
    xc, top, w, h = NOW_BOX
    kids = [E('WoR_now_line', 'SpriteElement', pos=(xc, top), dims=(w * NOW_W_SCALE, h), just=(0, -1), z=0.5, texture=NOW_TEX[0],
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
    # sung-note fill pool (1.92, user 2026-11-06: "fill the rectangles exactly where they're hit ... a separate logic"):
    # hidden sprites the plugin lays over the stretch of a note that crossed the now line while the singer was on
    # pitch. 1.93: in the root (1.92's in note_scale, created 0 wide, never drew), 1 wide at creation, above the
    # notes' window (z 1) and under the now line and comet (pitch_area, z 4)
    # (1.93 test 3: scaled by its length in x it draws over [pos - length, pos]: the plugin puts pos at the stretch's
    # right end; z 2.2 over the notes (z 2: at 1.5 the notes' dark inside covered it), under the SP glow bands (2.5))
    glows += [E(f'WoR_fill_{i}', 'SpriteElement', pos=(0.0, 0.0), dims=(1.0, PAINT_H), just=(-1, 0), z=2.2, alpha=0.0,
                rgba=PAINT_RGB + (255,), texture=FILL_TEX).render(0) for i in range(FILL_POOL)]
    # WoR's "Get Ready!" (hidden; WoR_HUD_vocal_get_ready shows it), centred on screen between the highway's lines
    glows.append(E('WoR_get_ready', 'SpriteElement', pos=(640.0 - x + GET_READY_NUDGE[0], (SP_GLOW_Y[0] + SP_GLOW_Y[1]) / 2 + GET_READY_NUDGE[1]), dims=GET_READY_DIMS,
                   just=(0, 0), z=3.0, alpha=0.0, texture=GET_READY_TEX).render(0))
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
    if config in ('hud_1g1v', 'hud_2g1v', 'hud_3g1v'):          # the vocal highway at y 0 with more than one player
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
