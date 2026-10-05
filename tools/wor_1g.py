"""The GH5 / Warriors of Rock single-guitar HUD (descs for the DE's nxgui HUD), laid out like WoR's 1-player screen:

  * rock meter: WoR's rock tube (RM_Base + red/yellow/green LEDs) on the LEFT highway border, with a needle that
    slides up it. The DE drives the slide (BAND_side_meter -> side_meter_needle_pos, theme flag d38da2b2); the LEDs
    come from the band meter's light alphas, so they also work where the DE hides side meters (career);
  * star power: WoR's SP tube on the RIGHT border, filled by six segments driven by the DE's SP tube widget;
  * multiplier: GH3:WoR's x1..x4 badge at the top of the SP tube, with the note-streak lights on its arm
    (nixie_texture; the badge images are this theme's multiplier textures, theme keys f8885a0f / d99b7552);
  * score: WoR's score box with the star (star count inside), the star-progress fill behind its slot and the
    note-streak box underneath (bottom right of the highway).

All coordinates are on the 1280x720 HUD canvas: every descinterface instance is placed so its desc coordinates ARE
canvas coordinates. Elements the DE drives but WoR doesn't show are kept as hidden dummies so every prop resolves.
The tuning values below were set against GH5 footage and the user's in-game tests; the history is in docs/MODLOG.md.
"""
import copy
import math

import paths
from desc_gen import E, desc

SCORE_FONT = 'WoR_HUD_num_a1'  # WoR's fontgrid_numeral_a1, converted to the PC format (tools/wor_font.py), in the theme pak
FONT_SRC = {SCORE_FONT: paths.wor('ui_shared', 'fontgrid_numeral_a1.fnt.xen')}
# In-play messages (theme key d5927557): the DE's own bold gothic, always loaded from DATA\FONTS\wtde_fonts.pak.
# Never ship a second font in the theme pak: the game crashed unloading one (v0.19b).
MSG_FONT = '0x2e5a5f81'
BLANK = 'WoR_HUD_blank'      # fully transparent texture: hides sprites the DE drives (texture 0 draws a white quad)
G1 = (592.0, 350.0)          # player container position in the layout (the DE resolves alias_g1)
HUD_Z = 10.0                 # added to every element's draw priority: above the highway and its SP glow (z 6),
                             # below the fail vignette (25). z is compared screen-wide.

# ---------------------------------------------------------------- highway and tube geometry
# Highway edges on the canvas, computed like the DE (highway_2d generate_pos_table with highway_guitar1: playline
# 655, height 350, top width 160, widthoffsetfactor 2.2). Ultrawide stretches the HUD and the highway alike.
HW_PLAYLINE, HW_HEIGHT, HW_TOP_W, HW_WIDTH_FACTOR = 655.0, 350.0, 160.0, 2.2
HW_BOTTOM_W = HW_TOP_W + HW_TOP_W * HW_WIDTH_FACTOR
LEFT_EDGE = ((640.0 - HW_BOTTOM_W / 2, HW_PLAYLINE), (640.0 - HW_TOP_W / 2, HW_PLAYLINE - HW_HEIGHT))
RIGHT_EDGE = ((640.0 + HW_BOTTOM_W / 2, HW_PLAYLINE), (640.0 + HW_TOP_W / 2, HW_PLAYLINE - HW_HEIGHT))
# Tube textures (RM_Base / SP_Base, 64x256): the art carries a perspective lean and widens towards its curled end.
TEX_CENTER = (51.86, -0.040)      # tube centre line: x = a + b*y (texture px)
LED_BOTTOM, LED_TOP = 19.0, 242.0   # LED span along the tube, px from the texture bottom
# WoR's placement (guitar_tweaks highway_guitar1 + setup_sidebar_rockmeter + the sidebar meter descs): the sidebar
# container sits on the edge line 25% of the highway height below the playline, rotated by the edge angle; the
# meter desc goes in it at (-5,-130), scale 0.7 (star power mirrored). The tube sprite's bottom-centre sits at
# ROCK/SP_TUBE_BOTTOM in that container.
RAIL_SX = RAIL_SY = 0.7
SIDEBAR_Y = HW_PLAYLINE + 0.25 * HW_HEIGHT
SIDEBAR_X = (640.0 - HW_BOTTOM_W / 2) - 0.25 * (HW_BOTTOM_W - HW_TOP_W) / 2
ROCK_TUBE_BOTTOM = (-23.954, -130.0)
SP_TUBE_BOTTOM = (26.031, -130.772)
RAIL_TUCK_LEFT, RAIL_TUCK_RIGHT = 3.0, 5.0   # initial shift towards the highway (before on_border aligns them)
DE_NEEDLE_END = (41.0, -80.0)       # the DE's 1-player side meter needle path: health 0 -> (0,0), 2 -> this

# The tubes lie ON the WoR highway border, coaxial with it. Border centre lines measured in game (x = a + b*(710-y),
# game px); the side-meter descs draw at game = canvas + RAIL_GAME_CAL.
BORDER_LINE_L = (352.5, 0.518)
BORDER_LINE_R = (927.5, -0.517)
RAIL_GAME_CAL = (1.0, 9.0)
RAIL_ALIGN_D = 130.0            # tube height (texture px above the bottom) where the centre lines are made to meet
RAIL_TILT = 1.75                # extra lean of each tube's top towards the highway (deg)
RAIL_OUTSET = (-13.4, 15.7)     # horizontal canvas px from the border centre line (rock, star power)

# ---------------------------------------------------------------- look: tints, shadows, layering
RAIL_TINT_L = (217, 217, 217, 255)  # rock tube art
RAIL_TINT_R = (255, 255, 255, 255)  # star power tube art
SCORE_TINT = (161, 161, 161, 255)   # score box art + glass
STREAK_TINT = (171, 171, 171, 255)  # streak box art + front
RAIL_SHADOW_A = 0.6                 # tube drop shadow (the tube art tinted black)
RAIL_SHADOW_OFF = (1.5, 2.0)        # canvas px, down-right
RAIL_GAP_FILL = (2.0, 4.0)          # black tube copies shifted towards the highway: no gap to the border
# Soft black ball behind each tube's curled end (WoR's circle_gradient_64 tinted black), under the highway surface.
VOID_D = 28.0                   # diameter, canvas px
VOID_STACK = 2                  # copies stacked for a harder edge (1-(1-a)^n)
VOID_A = 1.0
VOID_ROW = 236.0                # tube texture row of the ball centre
VOID_OFF = ((0.0, 0.0), (0.0, 0.0))   # extra canvas (x, y) per side (rock, star power)
# Outer shadows: rings of black copies of each target's own art at low alpha (a faked blur from the extracted texture).
OUTER_SHADOW = True
OUTER_SHADOW_RINGS = ((1.5, 0.036), (3.0, 0.024), (5.0, 0.016), (7.5, 0.01))   # (radius canvas px, alpha per copy)
OUTER_SHADOW_BIAS = (1.0, 1.5)
OUTER_SHADOW_TARGETS = {'score_back': None, 'streak_box': None, 'band_hud_star_overlay': None,
                        'rm_back': 3.005, 'sp_back': 3.005}   # id -> absolute z (None: just under the target)

# Absolute draw priorities by local_id, set after lift(): the tubes draw just above the highway border (sidebar
# sprites z 3) and below the strikeline cups (3.1-3.9) and gems; the multiplier badge (its arm goes behind the
# highway) and the tube balls draw under the highway surface (0.1).
RAIL_Z = {'rm_shadow': 3.01, 'sp_shadow': 3.01, 'rm_gap0': 3.012, 'rm_gap1': 3.012, 'sp_gap0': 3.012, 'sp_gap1': 3.012,
          'rm_back': 3.015, 'sp_back': 3.015, 'lights_bg': 3.02, 'red_light': 3.04, 'yellow_light': 3.04,
          'green_light': 3.04, 'sp_base': 3.02, 'sp_marker': 3.08,
          'needle_anchor': 3.09, 'side_meter_needle': 3.09, 'side_meter_red_ON': 3.06, 'nixie': 0.05}
RAIL_Z.update({f'sp_seg{i}': 3.05 for i in range(6)})
RAIL_Z.update({f'{t}_void{n}': 0.04 for t in ('rm', 'sp') for n in ('', '1', '2', '3')})


def edge_angle(edge):
    (x0, y0), (x1, y1) = edge
    return math.degrees(math.atan2(x1 - x0, y0 - y1))      # degrees clockwise from vertical


def rot(v, deg):
    """Rotate a canvas vector clockwise (y down) by deg, as the GUI does for rot_angle > 0."""
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def add(*vs):
    return (sum(v[0] for v in vs), sum(v[1] for v in vs))


def scale(v, k):
    return (v[0] * k, v[1] * k)


class Rail:
    """One sidebar tube. The sprite is anchored at its texture bottom-centre (just (0,1)), mirrored by a negative x
    scale; a texture pixel q maps to pos + R(rot) * ((qx - 32) * sx, (qy - 256) * RAIL_SY)."""

    def __init__(self, edge, outward, mirror):
        self.sx = -RAIL_SX if mirror else RAIL_SX
        self.edge, self.outward = edge, outward
        self.rot = edge_angle(edge)        # WoR: the meter is unrotated inside the edge-rotated sidebar container
        container = (640.0 + outward * (640.0 - SIDEBAR_X), SIDEBAR_Y)
        self.pos = add(container, rot(SP_TUBE_BOTTOM if mirror else ROCK_TUBE_BOTTOM, self.rot),
                       rot((-outward * (RAIL_TUCK_RIGHT if mirror else RAIL_TUCK_LEFT), 0.0), self.rot))
        self.refresh()

    def refresh(self):
        c0, c1 = self.at(LED_BOTTOM), self.at(LED_TOP)
        self.angle = math.degrees(math.atan2(c1[0] - c0[0], c0[1] - c1[1]))     # centre-line angle on screen

    def tex(self, q):
        """Canvas point of texture pixel q."""
        return add(self.pos, rot(((q[0] - 32.0) * self.sx, (q[1] - 256.0) * RAIL_SY), self.rot))

    def at(self, d):
        """Canvas point on the tube's centre line, d texture px above the texture bottom."""
        y = 256.0 - d
        return self.tex((TEX_CENTER[0] + TEX_CENTER[1] * y, y))

    def sprite(self, local_id, texture, z, blend='Blend', offset=(0.0, 0.0), **kw):
        return E(local_id, 'SpriteElement', pos=add(self.pos, offset), dims=(64, 256), just=(0, 1),
                 scale=(self.sx, RAIL_SY), rot=self.rot, z=z, texture=texture, blend=blend, **kw)


def on_border(rail, line):
    """Rotate the rail about its anchor so its centre line runs parallel to the border line (+RAIL_TILT), then shift
    it horizontally onto the line at RAIL_ALIGN_D, plus RAIL_OUTSET."""
    a, b = line
    target = math.degrees(math.atan2(b, 1.0)) + (RAIL_TILT if rail.outward < 0 else -RAIL_TILT)
    rail.rot += target - rail.angle
    rail.refresh()
    p = rail.at(RAIL_ALIGN_D)
    tx = a + b * (710.0 - (p[1] + RAIL_GAME_CAL[1])) - RAIL_GAME_CAL[0]
    rail.pos = (rail.pos[0] + tx - p[0] + (RAIL_OUTSET[0] if rail.outward < 0 else RAIL_OUTSET[1]), rail.pos[1])
    rail.refresh()
    return rail


def make_rails():
    """(rock, star power) rails for the current settings; call again after changing them (mocks do)."""
    return (on_border(Rail(LEFT_EDGE, outward=-1.0, mirror=False), BORDER_LINE_L),   # rock meter: unmirrored (WoR)
            on_border(Rail(RIGHT_EDGE, outward=1.0, mirror=True), BORDER_LINE_R))    # star power: mirrored


LEFT, RIGHT = make_rails()


def dummy(local_id, kind='SpriteElement', **kw):
    if kind == 'TextBlockElement':
        return E(local_id, kind, alpha=0.0, hidden=True, font=SCORE_FONT, dims=(10, 10), **kw)
    if kind == 'SpriteElement':
        return E(local_id, kind, dims=(4, 4), texture=BLANK, alpha=0.0, **kw)
    return E(local_id, kind, dims=(4, 4), **kw)


def graveyard(local_id, children):
    """A zero-size window: clips the DE-driven elements WoR doesn't show, whatever the DE sets on them."""
    return E(local_id, 'windowelement', pos=(-64, -64), dims=(0, 0), just=(-1, -1), children=children)


def lift(root):
    """Add HUD_Z to every element's draw priority (keeps their relative order)."""
    def walk(e):
        e.z = e.z + HUD_Z
        for c in e.children:
            walk(c)
    walk(root)
    return root


def rail_z(root):
    def walk(e):
        if e.local_id in RAIL_Z:
            e.z = RAIL_Z[e.local_id]
        for c in e.children:
            walk(c)
    walk(root)
    return root


def add_outer_shadows(root):
    if not OUTER_SHADOW:
        return root

    def walk(e):
        out = []
        for c in e.children:
            walk(c)
            if c.local_id in OUTER_SHADOW_TARGETS:
                n = 0
                for r, a in OUTER_SHADOW_RINGS:
                    nd = 8 if r < 8.0 else 12            # more copies on wide rings so the blur stays smooth
                    for k in range(nd):
                        ang = math.radians(360.0 / nd * k)
                        s = copy.deepcopy(c)
                        s.children = []
                        s.local_id = f'{c.local_id}_os{n}'
                        s.pos = (c.pos[0] + OUTER_SHADOW_BIAS[0] + r * math.cos(ang),
                                 c.pos[1] + OUTER_SHADOW_BIAS[1] + r * math.sin(ang))
                        s.rgba, s.alpha = (0, 0, 0, 255), a
                        s.extra = dict(c.extra, blend='Blend')
                        zabs = OUTER_SHADOW_TARGETS[c.local_id]
                        if zabs is None:
                            s.z = c.z - 0.05
                        else:
                            RAIL_Z[s.local_id] = zabs
                        out.append(s)
                        n += 1
            out.append(c)
        e.children = out
    walk(root)
    return root


def tube_void_centres():
    return [(t, add(rail.tex((TEX_CENTER[0] + TEX_CENTER[1] * VOID_ROW, VOID_ROW)), off))
            for t, rail, off in (('rm', LEFT, VOID_OFF[0]), ('sp', RIGHT, VOID_OFF[1]))]


# ---------------------------------------------------------------- score / band meter (alias_band_meter)
SCORE_C = (1055.6, 581.0)       # centre of the 512x128 score box texture
SCORE_K = 0.775                 # WoR's own on-screen scale for it (1.35 * 0.7 * 0.82)
SCORE_X_K = 1.039               # GH5's box is ~8 px longer: box, star holder, star, bar and slot stretch about SCORE_C
# Everything else in the panel uses WoR's uidesc_star_meter offsets in its score_container frame (canvas units per
# frame unit K0; score_bg centre at BG_OFF in that frame).
K0 = SCORE_K / 1.35
BG_OFF = (37.011, 16.931)
SCORE_TEXT_KX = 1.08            # GH5 digits are wider (pitch 19 vs 18) ...
SCORE_TEXT_KY = 1.26            # ... and taller (17 px vs 13) than WoR's numerals
SCORE_TEXT_K = 0.90             # overall score digit size, kept centred on the same line
SCORE_TEXT_SHIFT = (0.4, -2.0)
STAR_K = 1.14                   # gold star size
STAR_SHIFT = (4.2, -1.0)        # relative to the (stretched) panel
STAR_ART_C = (63.69, 70.73)     # centre of mass of the filled gold star in its 128 px texture
STAR_OVERLAY_PX = 3.0           # gold outline (overlay/shine/glow) grows by this many px
STAR_BG_RGBA = (130, 126, 128, 255)   # dims the silver frame's grey centre to GH5's
STAR_NUM_K = 0.78               # star count size
STAR_NUM_NUDGE = (-0.8, -2.0)   # the count is centred on the gold star's shape
STREAK_SHIFT = (-1.6, 1.0)      # relative to the panel (not stretched)
STREAK_TEXT_Y = 1.55            # streak-texture px from its centre
STREAK_RIGHT = 98.0             # streak text right edge, streak-texture px from its centre
STREAK_NUM_K = 0.555            # streak digit size


def sx(p):
    """Stretch a canvas point horizontally about the score box centre (SCORE_X_K)."""
    return (SCORE_C[0] + (p[0] - SCORE_C[0]) * SCORE_X_K, p[1])


def sm(x, y):
    """Canvas point of a WoR star_meter score_container-frame point."""
    return (SCORE_C[0] + (x - BG_OFF[0]) * K0, SCORE_C[1] + (y - BG_OFF[1]) * K0)


# ---------------------------------------------------------------- star power fill
SP_SEGMENTS = 6
SP_DEFAULT_SCALE = 0.3          # the DE's star-power tube scale for non-classic themes (hud_widgets)
SP_FILL_BAND = (0, 44, 64, 60)  # SP_Fill01 rows without its tapered top / bent tail (shipped as 64x16)
SP_FILL_FLIP = True             # mirrored like the tube (the DE overwrites the segments' scale, so it's baked in)
SP_FILL_COLS = (0, 28)          # fill band texture columns holding the fill art (after the flip)
SP_FILL_ROWS = (14.0, 237.0)    # SP_Base rows the six segments span
SP_FILL_RGBA = (20, 235, 180, 235)   # GH5's teal
SP_RIM = 3.0                    # tube rim on each side, texture px (the fill sits inside the glass)
SP_SLANT_DEG = 8.3              # screen angle of a partial segment's top edge (level-ish, like the divider)
SP_MARKER_Y = 528.0             # GH5's half divider (canvas y); x = tube centre
SP_MARKER_ROT = 37.0            # SB_TubeNeedle01 turned into GH5's level-ish arch
SP_MARKER_K = 1.25              # GH5's divider spans the whole tube


def sp_tube_width(y):
    """Width of SP_Base's tube at texture row y (alpha span: 22 px at row 20, 30 px at row 220)."""
    return 22.0 + 0.04 * (y - 20.0)


def sp_divider_row():
    """SP_Base texture row (from the top) of the half divider: where the tube centre line crosses SP_MARKER_Y."""
    lo, hi = 0.0, 256.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if RIGHT.at(256.0 - mid)[1] < SP_MARKER_Y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def sp_fill_rows():
    """[(top row, bottom row)] of the segments, bottom first: the lower half runs from the tube end to the half
    divider, the upper half from the divider to the top, so 50% (3 full segments) ends at the needle."""
    d, n = sp_divider_row(), SP_SEGMENTS // 2
    lo, hi = (SP_FILL_ROWS[1] - d) / n, (d - SP_FILL_ROWS[0]) / n
    return ([(SP_FILL_ROWS[1] - (i + 1) * lo, SP_FILL_ROWS[1] - i * lo) for i in range(n)]
            + [(d - (i + 1) * hi, d - i * hi) for i in range(n)])


def sp_slant_geom():
    """(D, slope) of the slanted fill cut: slope = local dy/dx (canvas), D = half the vertical spread of the cut over
    the fill's width (canvas px)."""
    slope = math.tan(math.radians(SP_SLANT_DEG - RIGHT.rot))
    width = (sp_tube_width(125.0) - 2 * SP_RIM) * RAIL_SX
    return abs(slope) * width / 2, slope


def seg_canvas_size():
    """(height, width) of the mean segment on the canvas: the shared slanted fill texture is made for it."""
    h = (SP_FILL_ROWS[1] - SP_FILL_ROWS[0]) / SP_SEGMENTS * RAIL_SY
    w = (sp_tube_width(125.0) - 2 * SP_RIM) * RAIL_SX * 64.0 / (SP_FILL_COLS[1] - SP_FILL_COLS[0] + 1)
    return h, w


def sp_segments():
    """Six sprite segments; the DE writes each one's texture and scale (glow{i}_texture / glow{i}_scale). The shared
    fill texture is a parallelogram, so each sprite is taller by the slant and sits d lower (the content bottom at
    the tube centre stays put); the slant margin scales with the segment's height."""
    seg_h = seg_canvas_size()[0]
    segs = []
    for i, (top, y0) in enumerate(sp_fill_rows()):
        ym = y0 - (y0 - top) / 2
        wc = (sp_tube_width(ym) - 2 * SP_RIM) * RAIL_SX * 64.0 / (SP_FILL_COLS[1] - SP_FILL_COLS[0] + 1)
        content_c = ((SP_FILL_COLS[0] + SP_FILL_COLS[1] + 1) / 2 / 64.0 - 0.5) * wc
        base = add(RIGHT.tex((TEX_CENTER[0] + TEX_CENTER[1] * ym, y0)), rot((-content_c, 0.0), RIGHT.rot))
        h = (y0 - top) * RAIL_SY
        d = sp_slant_geom()[0] * h / seg_h
        base = add(base, rot((0.0, d), RIGHT.rot))
        h = h + 2 * d
        segs.append(E(f'sp_seg{i}', 'SpriteElement', pos=base, just=(0, 1), rot=RIGHT.rot, z=3.5,
                      dims=(wc / SP_DEFAULT_SCALE, h / SP_DEFAULT_SCALE), scale=(SP_DEFAULT_SCALE, 0.0),
                      rgba=SP_FILL_RGBA, texture='hud_rock_tube_glow_full', blend='Add'))
    return segs


def sp_marker_pos():
    """Point on the star power tube's centre line at canvas height SP_MARKER_Y."""
    lo, hi = LED_BOTTOM, LED_TOP
    for _ in range(40):
        mid = (lo + hi) / 2
        if RIGHT.at(mid)[1] > SP_MARKER_Y:
            lo = mid
        else:
            hi = mid
    return RIGHT.at((lo + hi) / 2)


def band_meter():
    # WoR star_meter: star_meter_container centre sc; star frame / overlay / number / filler relative to it
    sc = sm(2.733, 35.653)
    sc_star = add(sx(sc), STAR_SHIFT)      # the star rides on the stretched box's star holder
    SOV = (57.0 + STAR_OVERLAY_PX) / 57.0  # gold outline growth factor
    star = add(sc_star, scale((164.83, -29.77), K0))
    overlay = add(sc_star, scale((165.368, -31.2023), K0))
    filler_l = sx(add(sc, scale((-171.40, -4.25), K0)))
    s_box = add(sm(8.209, 75.272), STREAK_SHIFT)      # streak sprite centre (scale 0.9 in the frame)
    segs = sp_segments()
    sk = K0 * 0.9                                      # streak sprite scale on the canvas
    streak = E('streak', 'ContainerElement', just=(-1, -1), z=3.0, children=[
        E('streak_box', 'SpriteElement', pos=s_box, dims=(256, 64), scale=(sk, sk), z=3.0,
          rgba=STREAK_TINT, texture='WoR_HUD_streak'),
        E('streak_number', 'TextBlockElement', pos=add(s_box, scale((STREAK_RIGHT, STREAK_TEXT_Y), sk)), dims=(300, 100),
          just=(1, 0), scale=(sk * STREAK_NUM_K, sk * STREAK_NUM_K), z=3.2, rgba=(255, 128, 0, 255), font=SCORE_FONT,
          text='c6081e83', shadow=False),
        E('streak_front', 'SpriteElement', pos=add(s_box, scale((3.268, 2.816), sk)), dims=(256, 64),
          scale=(sk, sk), z=3.4, rgba=STREAK_TINT, texture='WoR_HUD_streak_front'),
    ])
    box_tl = (SCORE_C[0] - 256 * SCORE_K, SCORE_C[1] - 64 * SCORE_K)
    star_k = SCORE_K * STAR_K
    root = E('meter_container', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        # score box: star-progress fill behind the box art, black slot behind both, glass front over the score
        E('star_filler', 'SpriteElement', pos=filler_l, dims=(306 * K0 / 0.7 * SCORE_X_K, 25 * K0), just=(-1, 0),
          scale=(0.7, 1.0), z=4.0, rgba=(249, 193, 34, 255)),
        E('score_back', 'SpriteElement', pos=SCORE_C, dims=(512, 128), scale=(SCORE_K * SCORE_X_K, SCORE_K), z=5.0,
          rgba=SCORE_TINT, texture='WoR_HUD_score_box'),
        E('Score', 'TextBlockElement',
          pos=add(box_tl, scale((315.151, 44.783), SCORE_K), SCORE_TEXT_SHIFT, (0.0, (1.0 - SCORE_TEXT_K) * 8.5)),
          dims=(536, 65), just=(1, -1),
          scale=(0.386667 * SCORE_K * SCORE_TEXT_KX * SCORE_TEXT_K, 0.386667 * SCORE_K * SCORE_TEXT_KY * SCORE_TEXT_K),
          z=6.0, font=SCORE_FONT, text='0x00000000', shadow=False),
        E('score_front', 'SpriteElement', pos=sx(sm(40.857, 18.429)), dims=(512, 128), scale=(SCORE_K * SCORE_X_K, SCORE_K),
          z=7.0, rgba=SCORE_TINT, texture='WoR_HUD_score_front'),
        E('band_hud_star_frame', 'SpriteElement', pos=star, dims=(128, 128), scale=(star_k, star_k), z=9.0,
          texture=BLANK),
        E('star_bg', 'SpriteElement', pos=star, dims=(128, 128), scale=(star_k, star_k), z=8.5,
          rgba=STAR_BG_RGBA, texture='WoR_HUD_star_bg'),
        E('band_hud_star_overlay', 'SpriteElement', pos=overlay, dims=(128, 128), scale=(star_k * SOV, star_k * SOV),
          z=10.0, texture='WoR_HUD_star_overlay'),
        E('band_HUD_gold_star_glow', 'SpriteElement', pos=add(overlay, scale((1.065, 1.123), SCORE_K)),
          dims=(128, 128), scale=(SCORE_K * 0.8 * STAR_K * SOV, SCORE_K * 0.8 * STAR_K * SOV), z=11.0, alpha=0.0,
          texture='WoR_HUD_star_glow', blend='Add'),
        E('star_meter_num', 'TextBlockElement',
          pos=add(overlay, scale((STAR_ART_C[0] - 64, STAR_ART_C[1] - 64), star_k), STAR_NUM_NUDGE),
          dims=(40, 50), just=(0, 0), scale=(K0 * STAR_NUM_K, K0 * STAR_NUM_K), z=12.0, rgba=(249, 193, 34, 255),
          font=SCORE_FONT, text='0x4a4d8830', shadow=False),
        streak,
        E('slot_bg', 'SpriteElement', pos=sx(add(sc, scale((-13.02, -8.03), K0))),
          dims=(309, 50), scale=(K0 * SCORE_X_K, K0), z=3.9, rgba=(0, 0, 0, 255)),
        E('star_flame', 'ContainerElement', pos=star, dims=(4, 4), just=(-1, -1), z=13.0),   # DE star-earned sparks
        E('star_shine', 'SpriteElement', pos=overlay, dims=(128, 128), scale=(star_k * SOV, star_k * SOV), z=10.5,
          alpha=0.45, texture='WoR_HUD_star_overlay', blend='Add'),
        # tubes: drop shadow, black backing (+ gap fill) and the end balls under the art, then the art
        LEFT.sprite('rm_shadow', 'WoR_HUD_rm_base', z=2.0, rgba=(0, 0, 0, 255), alpha=RAIL_SHADOW_A, offset=RAIL_SHADOW_OFF),
        RIGHT.sprite('sp_shadow', 'WoR_HUD_sp_base', z=2.0, rgba=(0, 0, 0, 255), alpha=RAIL_SHADOW_A, offset=RAIL_SHADOW_OFF),
        LEFT.sprite('rm_back', 'WoR_HUD_rm_base', z=2.0, rgba=(0, 0, 0, 255)),
        RIGHT.sprite('sp_back', 'WoR_HUD_sp_base', z=2.0, rgba=(0, 0, 0, 255)),
        *[E(f'{t}_void' + (f'{n}' if n else ''), 'SpriteElement', pos=c, dims=(64, 64),
            scale=(VOID_D / 64.0, VOID_D / 64.0), z=2.0, rgba=(0, 0, 0, 255), alpha=VOID_A, texture='WoR_HUD_void')
          for t, c in tube_void_centres() for n in range(VOID_STACK)],
        *[e for i, g in enumerate(RAIL_GAP_FILL) for e in (
            LEFT.sprite(f'rm_gap{i}', 'WoR_HUD_rm_base', z=2.0, rgba=(0, 0, 0, 255), offset=rot((g, 0.0), LEFT.rot)),
            RIGHT.sprite(f'sp_gap{i}', 'WoR_HUD_sp_base', z=2.0, rgba=(0, 0, 0, 255), offset=rot((-g, 0.0), RIGHT.rot)))],
        LEFT.sprite('lights_bg', 'WoR_HUD_rm_base', z=2.0, rgba=RAIL_TINT_L),
        LEFT.sprite('red_light', 'WoR_HUD_rm_red', z=2.5, blend='Add'),
        LEFT.sprite('yellow_light', 'WoR_HUD_rm_yellow', z=2.5, blend='Add'),
        LEFT.sprite('green_light', 'WoR_HUD_rm_green', z=2.5, blend='Add'),
        RIGHT.sprite('sp_base', 'WoR_HUD_sp_base', z=3.0, rgba=RAIL_TINT_R),
        *segs,
        E('sp_marker', 'SpriteElement', pos=sp_marker_pos(), dims=(64, 64),     # GH5's half divider
          scale=(RAIL_SX * 1.1 * SP_MARKER_K, RAIL_SX * 1.1 * SP_MARKER_K), rot=SP_MARKER_ROT, z=3.9,
          texture='WoR_HUD_needle'),
        graveyard('grave', [
            dummy('Needle'), dummy('glow'), dummy('songtime_bg'), dummy('songtime_fg'),
            dummy('HUD_meter_green_bg'), dummy('HUD_meter_yellow_bg'), dummy('HUD_meter_red_bg'),
            dummy('secondary_bulbs', 'ContainerElement'), dummy('streak_anim_sink', 'ContainerElement')]),
    ])
    props = [('score_text', 'Score', 'text'), ('needle_rot_angle', 'Needle', 'rot_angle'),
             ('Needle_pos', 'Needle', 'Pos'),
             ('green_light_alpha', 'green_light', 'alpha'), ('yellow_light_alpha', 'yellow_light', 'alpha'),
             ('red_light_alpha', 'red_light', 'alpha'), ('streak_number_text', 'streak_number', 'text')]
    props += [(f'glow{i}_texture', f'sp_seg{i}', 'texture') for i in range(SP_SEGMENTS)]
    props += [(f'glow{i}_scale', f'sp_seg{i}', 'Scale') for i in range(SP_SEGMENTS)]
    props += [('hud_meter_green_bg_alpha', 'HUD_meter_green_bg', 'alpha'),
              ('hud_meter_yellow_bg_alpha', 'HUD_meter_yellow_bg', 'alpha'),
              ('hud_meter_red_bg_alpha', 'HUD_meter_red_bg', 'alpha'),
              ('star_meter_num_text', 'star_meter_num', 'text'),
              ('band_hud_star_frame_rgba', 'band_hud_star_frame', 'rgba'),
              ('star_filler_scale', 'star_filler', 'Scale'), ('star_filler_rgba', 'star_filler', 'rgba'),
              ('star_meter_num_rgba', 'star_meter_num', 'rgba'),
              ('band_hud_star_overlay_rgba', 'band_hud_star_overlay', 'rgba'),
              ('band_hud_gold_star_glow_alpha', 'band_HUD_gold_star_glow', 'alpha')]
    aliases = [('alias_glow', 'glow'), ('alias_streak', 'streak_anim_sink'), ('0x80a7370b', 'songtime_bg'),
               ('e4cbf20f', 'songtime_fg'), ('alias_secondary_bulbs', 'secondary_bulbs'),
               ('alias_HUD_meter_red_bg', 'HUD_meter_red_bg'), ('alias_star_flame', 'star_flame')]
    return desc('wor_band_meter_1g_ghwor', rail_z(lift(add_outer_shadows(root))), props, aliases)


# ---------------------------------------------------------------- multiplier badge (player_meter)
# GH3:WoR multiplier image (HUD_score_nixie_*, cropped to 160x144): a stick at 28.87 deg from vertical ending at
# BADGE_STICK_END, and the badge disc beside it. The stick continues the star power tube upward (behind the highway);
# the streak lights sit on the stick.
BADGE_TEX = (256, 256)           # power of two: other sizes get padded by the converter
BADGE_STICK_END = (69.0, 110.0)  # crop px: bottom of the stick = top of the star power tube
BADGE_STICK_ANGLE = -28.87
BADGE_K = 0.7                    # canvas units per crop px
RAIL_TOP_D = 252.0               # texture px along the tube where the stick takes over (tube top)
BADGE_TUCK = 5.0                 # towards the highway
BADGE_SHIFT = (-4.05, -19.87)
LIGHT_SHIFT = (-4.05, -19.87)    # the streak marks sit inside the badge art's holder bar
# GH3:WoR career_hud_2d_elements light positions in badge-crop px (light0 = lowest); each image holds 2 of 10 marks
LED_CROP = [(58.0, 80.0), (48.0, 63.0), (38.0, 46.0), (28.0, 29.0), (18.0, 12.0)]


def badge_point(top, turn, q):
    """Canvas point of badge-crop pixel q (the image is anchored at its stick end on `top`, turned, scaled)."""
    v = ((q[0] - BADGE_STICK_END[0]) * BADGE_K, (q[1] - BADGE_STICK_END[1]) * BADGE_K)
    return add(top, rot(v, turn))


def player_meter():
    top = add(RIGHT.at(RAIL_TOP_D), rot((-BADGE_TUCK, 0.0), RIGHT.angle))
    badge = add(top, BADGE_SHIFT, (-G1[0], -G1[1]))
    turn = RIGHT.angle - BADGE_STICK_ANGLE          # align the image's stick with the tube
    just = (2 * BADGE_STICK_END[0] / BADGE_TEX[0] - 1, 2 * BADGE_STICK_END[1] / BADGE_TEX[1] - 1)
    leds = [E(f'light{i}', 'SpriteElement', pos=add(badge_point(top, turn, q), LIGHT_SHIFT, (-G1[0], -G1[1])),
              dims=(32, 32), scale=(BADGE_K, BADGE_K), rot=turn, z=6.5, texture=LIGHT_MARKER)
            for i, q in enumerate(LED_CROP)]
    root = E('container', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        E('nixie', 'SpriteElement', pos=badge, dims=BADGE_TEX, just=just, scale=(BADGE_K, BADGE_K), rot=turn, z=6.0,
          texture='WoR_HUD_mult_1'),
        *leds,
        dummy('note_streak', 'TextBlockElement'), dummy('mult_bg'), dummy('nixie_rgba_sink'),
        *[dummy(f'glow{i}') for i in range(3)],
    ])
    props = [('note_streak_text', 'note_streak', 'text')]
    props += [(f'light{i}_texture', f'light{i}', 'texture') for i in range(5)]
    for i in range(3):
        props += [(f'glow{i}_texture', f'glow{i}', 'texture'), (f'glow{i}_scale', f'glow{i}', 'Scale')]
    props += [('nixie_texture', 'nixie', 'texture'), ('mult_bg_alpha', 'mult_bg', 'alpha'),
              ('nixie_rgba', 'nixie_rgba_sink', 'rgba')]
    return desc('wor_mult_1g_ghwor', rail_z(lift(root)), props)


# ---------------------------------------------------------------- sliding rock needle (BAND_side_meter)
def needle_anchor_scale():
    """Anchor scale that stretches the DE's needle path onto the left tube's LED span."""
    a, b = LEFT.at(LED_BOTTOM), LEFT.at(LED_TOP)
    return ((b[0] - a[0]) / DE_NEEDLE_END[0], (b[1] - a[1]) / DE_NEEDLE_END[1])


def side_meter():
    ax, ay = needle_anchor_scale()
    anchor = add(LEFT.at(LED_BOTTOM), (-G1[0], -G1[1]))
    nd = 40.0                    # needle size on screen (WoR's glowing slider)
    needle = E('side_meter_needle', 'SpriteElement', dims=(nd / ax, nd / ay), just=(0, 0), z=20.0,
               rot=LEFT.angle, texture='WoR_HUD_needle_glow', blend='Add')
    root = E('side_meter_band', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        E('needle_anchor', 'ContainerElement', pos=anchor, just=(-1, -1), scale=(ax, ay), z=20.0, children=[needle]),
        E('side_meter_red_ON', 'SpriteElement', pos=add(LEFT.pos, (-G1[0], -G1[1])), dims=(64, 256),
          just=(0, 1), scale=(LEFT.sx, RAIL_SY), rot=LEFT.rot, z=19.0, alpha=0.0, texture='WoR_HUD_rm_red',
          blend='Add'),
        *[dummy(f'side_meter_{c}_ON') for c in ('yellow', 'green')],
        dummy('side_meter_red_glow'),
    ])
    props = [('side_meter_needle_pos', 'side_meter_needle', 'Pos'),
             ('side_meter_needle_scale', 'side_meter_needle', 'Scale'),
             ('SIDE_meter_red_ON_alpha', 'side_meter_red_ON', 'alpha'),
             ('SIDE_meter_green_ON_alpha', 'side_meter_green_ON', 'alpha'),
             ('SIDE_meter_yellow_ON_alpha', 'side_meter_yellow_ON', 'alpha'),
             ('SIDE_meter_red_ON_rgba', 'side_meter_red_ON', 'rgba'),
             ('side_meter_red_glow_rgba', 'side_meter_red_glow', 'rgba')]
    return desc('wor_side_meter_ghwor', rail_z(lift(root)), props)


# ---------------------------------------------------------------- the 1-guitar layout
def layout(no_messages=False):
    """The 1-guitar layout. no_messages: GH5 shows no in-play text (Hot Start, note streaks) and no streak flame
    burst; the DE still creates them, inside 'message' / 'hud_message_fire', so those containers are drawn at alpha 0
    (a container's alpha multiplies into its children). Used by the WoR_HUD_NoMessages companion mod."""
    hide = 0.0 if no_messages else 1.0
    off = (0.0, 0.0)   # content is authored g1-relative
    g1 = E('g1', 'ContainerElement', pos=G1, just=(-1, -1), z=2.0, children=[
        E('player_meter', 'descinterface', pos=off, just=(-1, -1), z=2.0, desc='wor_mult_1g_ghwor'),
        E('message', 'ContainerElement', pos=(50, -140), dims=(600, 50), just=(0, -1), z=0.02, alpha=hide),
        E('Star_Power', 'descinterface', pos=(-422.038, -69.0104), dims=(698.071, 339.475), just=(-1, -1),
          scale=(0.8, 0.8), z=2.0, hidden=True, desc='star_power_1g', autosize=True),
        E('hud_message_fire', 'descinterface', dims=(300, 400), just=(0, 1), anchor=(0, 1), z=0.01, alpha=hide,
          desc='hud_message_fire', autosize=True),
        E('BAND_side_meter', 'descinterface', pos=off, just=(-1, -1), z=3.0, desc='wor_side_meter_ghwor'),
    ])
    root = E('hud_container', 'ContainerElement', just=(-1, -1), children=[
        g1,
        E('band_meter', 'descinterface', just=(-1, -1), z=1.0, desc='wor_band_meter_1g_ghwor'),
    ])
    aliases = [('alias_g1', 'g1'), ('alias_band_meter', 'band_meter'),
               ('alias_hud_message_fire_p1', 'hud_message_fire'), ('alias_g1_side_meter', 'BAND_side_meter')]
    return desc('hud_1g_ghwor_nomsg' if no_messages else 'hud_1g_ghwor', root, aliases=aliases)


def all_descs():
    return [layout(), band_meter(), player_meter(), side_meter()]


# ---------------------------------------------------------------- shipped textures
# mod texture name -> WoR png name (z_in_game, else ui_shared) or a full path
TEXTURES = {
    'WoR_HUD_score_front': 'band_HUD_star_score_meter_front',
    'WoR_HUD_streak': 'streak',
    'WoR_HUD_streak_front': 'streak_front',
    'WoR_HUD_star_frame': 'band_HUD_gold_star_frame',
    'WoR_HUD_star_bg': 'band_HUD_silver_star_frame',   # its grey radial centre is GH5's star background gradient
    'WoR_HUD_star_overlay': 'band_HUD_gold_star_overlay',
    'WoR_HUD_star_glow': 'band_HUD_gold_star_glow',
    'WoR_HUD_cap': 'Sidebar_Base_cap',
    'WoR_HUD_sp_base': 'SP_Base',
    'WoR_HUD_sp_fill': 'SP_Fill01',
    'WoR_HUD_needle': 'SB_TubeNeedle01',
    'WoR_HUD_needle_glow': 'SB_Tubeglow01',
    'WoR_HUD_void': paths.wor('circle_png', 'circle_gradient_64.png'),   # WoR global_textures
}
# Multiplier images: (theme texture name, GH3:WoR source). Normal x1..x4, star power x2..x8.
MULT_NORMAL = [('WoR_HUD_mult_1', 'HUD_score_nixie_1a'), ('WoR_HUD_mult_2', 'HUD_score_nixie_2a'),
               ('WoR_HUD_mult_3', 'HUD_score_nixie_3a'), ('WoR_HUD_mult_4', 'HUD_score_nixie_4a')]
MULT_SP = [(f'WoR_HUD_mult_sp{n}', f'HUD_score_nixie_{n}b') for n in (2, 4, 6, 8)]
# Note-streak lights: GH3:WoR's images under the DE's own names (state 0/1/2 x base/green/purple/blue). The DE script
# hard-codes these names and shares the base set between x1 and x2, and the stock z_in_game textures shadow them
# from the 2nd song on. The HUD fixes plugin (plugin/) switches our widgets to the unique WoR_HUD_light_* names
# below, with WoR's x1 pink; without the plugin the DE keeps using the stock names.
STREAK_LIGHTS = [f'HUD_score_light_{st}{c}' for st in range(3) for c in ('', '_green', '_purple', '_blue')]
LIGHT_SETS = ('_pink', '', '_green', '_purple', '_blue')     # plugin order: x1, x2, x3, x4, star power
OWN_LIGHTS = {f'WoR_HUD_light_{st}{c}': f'HUD_score_light_{st}{c}' for st in range(3) for c in LIGHT_SETS if c != '_pink'}
PINK_TINT = (255, 180, 180)          # WoR's x1 colour (hud_widgets combolights led_colors)
PINK_LIGHTS = {f'WoR_HUD_light_{st}_pink': f'HUD_score_light_{st}' for st in range(3)}   # off state stays grey
LIGHT_MARKER = 'WoR_HUD_light_0'     # the light elements' starting texture: the plugin recognises our widgets by it

# WoR's highway border (z_in_game basic_gems 388dd606: thick dark bevel + thin inner rail), shipped in a copy of the
# WoR gem pak (the game reads the theme's border texture, key 18f90ff6, before the theme pak loads). Needs
# GemTheme=ghwor. The DE stretches it across its sidebar sprite (sidebar_x_scale) and offsets it (~1 unit = 1 px).
BORDER_SRC = paths.wor('basic_gems_png', '388dd606.png')
BORDER_TEX_NAME = 'WoR_HUD_border'
BORDER_GEM_PAK = 'gems_ghwor_hud'
BORDER_X_SCALE = 2.6
BORDER_OFFSET = 17.4
