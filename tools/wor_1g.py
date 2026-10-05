"""The Warriors of Rock single-guitar HUD, laid out like WoR's own 1-player screen:

  * rock meter: a thin lit rail along the highway's LEFT edge (RM_Base + red/yellow/green LEDs), with a needle
    that slides up the rail. The DE drives the slide itself (BAND_side_meter -> side_meter_needle_pos, theme flag
    d38da2b2); the LEDs come from the band meter's light alphas so they also work where the DE hides side meters
    (career);
  * star power: a rail along the RIGHT edge (SP_Base) filled by six segments driven by the DE's SP tube widget;
  * multiplier: a small x2/x3/x4 badge on the right rail (nixie_texture; the badge images are this theme's
    multiplier textures, theme keys f8885a0f / d99b7552);
  * score: WoR's score box with the star (star count inside) and the star-progress fill behind its slot, plus the
    note-streak box underneath (bottom-right of the highway).

All coordinates are the 1280x720 HUD canvas. Every descinterface instance is placed so its desc coordinates ARE
canvas coordinates. Elements the DE drives but WoR doesn't show are kept as hidden dummies so every prop resolves.
"""
import math
from desc_gen import E, desc

SCORE_FONT = 'WoR_HUD_num_a1'  # WoR's fontgrid_numeral_a1, converted to the PC format (tools/wor_font.py), in the theme pak
# In-play messages (theme key d5927557): the DE's own bold gothic, the GH5/WoR menu face a little thicker than WoR's
# text_a1, always loaded from DATA\FONTS\wtde_fonts.pak. v0.19b shipped text_a1 inside the theme pak instead, and
# the game crashed while unloading that pak (crash suspect), so no second font ships any more.
MSG_FONT = '0x2e5a5f81'
FONT_SRC = {SCORE_FONT: r'C:\Users\rockb\ghwor-extract\ui_shared\fontgrid_numeral_a1.fnt.xen'}
BLANK = 'WoR_HUD_blank'
G1 = (592.0, 350.0)          # player container position in the layout (the DE resolves alias_g1)

# Highway edges on the 1280x720 HUD canvas, computed exactly like the DE does (highway_2d generate_pos_table
# with highway_guitar1: playline 655, height 350, top width 160, widthoffsetfactor 2.2). The highway and the HUD
# share this canvas on every resolution (ultrawide stretches both alike), so these hold everywhere.
HW_PLAYLINE, HW_HEIGHT, HW_TOP_W, HW_WIDTH_FACTOR = 655.0, 350.0, 160.0, 2.2
HW_BOTTOM_W = HW_TOP_W + HW_TOP_W * HW_WIDTH_FACTOR
LEFT_EDGE = ((640.0 - HW_BOTTOM_W / 2, HW_PLAYLINE), (640.0 - HW_TOP_W / 2, HW_PLAYLINE - HW_HEIGHT))
RIGHT_EDGE = ((640.0 + HW_BOTTOM_W / 2, HW_PLAYLINE), (640.0 + HW_TOP_W / 2, HW_PLAYLINE - HW_HEIGHT))
# Rails = WoR's sidebar tubes (RM_Base rock meter, SP_Base star power), built like WoR's setup_sidebar_rockmeter:
# the rock meter UNMIRRORED on the left, the star power meter MIRRORED (scale -x) on the right. The tube art already
# carries a perspective lean and widens towards its bent tail (texture bottom), which rests on the highway border.
# Texture geometry (64x256, alpha fits over rows 30..225):
TEX_CENTER = (51.86, -0.040)      # tube centre line:      x = a + b*y
TEX_EDGE = (61.88, -0.019)        # border-side tube edge: x = a + b*y (the right edge, unmirrored)
TEX_TIP = (36.5, 253.0)           # bottom of the bent tail
TEX_TOP_Y = 4.0                   # top of the tube cap
# Placement = WoR's own (guitar_tweaks highway_guitar1 + setup_sidebar_rockmeter + the sidebar meter descs):
# the highway's sidebar container sits on the edge line 25% of the highway height BELOW the playline
# (generate_pos_table sidebar_x/y), rotated by the edge angle; the meter desc goes in it at rockmeter_pos (-5,-130)
# with scale 0.7 (star power: x negated and mirrored). Inside the desc, the tube sprite's bottom-centre sits at
# (-23.954,-130) (rock) / (26.031,-130.772) (star power) of the container, both derived from the desc rects,
# just (0.5,1) / (0.6,1) and Master_Container + background offsets.
RAIL_SX = 0.7
RAIL_SY = 0.7
SIDEBAR_Y = HW_PLAYLINE + 0.25 * HW_HEIGHT
SIDEBAR_X = (640.0 - HW_BOTTOM_W / 2) - 0.25 * (HW_BOTTOM_W - HW_TOP_W) / 2
ROCK_TUBE_BOTTOM = (-23.954, -130.0)
SP_TUBE_BOTTOM = (26.031, -130.772)
# Tubes rest against the highway border like GH5's (the HUD is drawn ABOVE the highway: see HUD_Z): shift each
# tube this many canvas units towards the highway, perpendicular to the edge. The DE draws its silver border ~4 units
# further in than GH5 does, so these follow GH5's tube-to-border relation rather than GH5's absolute position.
RAIL_TUCK_LEFT = 3.0     # rock meter (v0.17: 6)
RAIL_TUCK_RIGHT = 5.0    # star power (v0.17: 6)
# Draw priority added to every element of the generated descs. The DE compares z across the whole screen: the
# highway's silver sidebars are z 3 and drew over the v0.17/v0.18 rock tube (z 2-2.5); +10 puts the HUD above
# the highway, its sidebars and their star power glow (z 6), still below the fail vignette (25).
HUD_Z = 10.0
LED_BOTTOM, LED_TOP = 19.0, 242.0   # LED span along the tube, px from the texture bottom
LED_SPAN = LED_TOP - LED_BOTTOM
# The DE's 1-player side meter needle path (script 0x3205f550): health 0 -> (0,0), 2 -> (41,-80).
DE_NEEDLE_END = (41.0, -80.0)


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
        # WoR: the meter is unrotated inside the highway's sidebar container, which carries the edge angle
        self.rot = edge_angle(edge)
        container = (640.0 + outward * (640.0 - SIDEBAR_X), SIDEBAR_Y)
        self.pos = add(container, rot(SP_TUBE_BOTTOM if mirror else ROCK_TUBE_BOTTOM, self.rot),
                       rot((-outward * (RAIL_TUCK_RIGHT if mirror else RAIL_TUCK_LEFT), 0.0), self.rot))
        self.refresh()

    def refresh(self):
        # tube centre line
        c0, c1 = self.tex(self._center(LED_BOTTOM)), self.tex(self._center(LED_TOP))
        self.angle = math.degrees(math.atan2(c1[0] - c0[0], c0[1] - c1[1]))     # centre-line angle on screen
        self.up = rot((0.0, -1.0), self.angle)

    def _vec(self, q, origin):
        """Canvas vector from texture pixel origin to texture pixel q."""
        return rot(((q[0] - origin[0]) * self.sx, (q[1] - origin[1]) * RAIL_SY), self.rot)

    def tex(self, q):
        """Canvas point of texture pixel q."""
        return add(self.pos, self._vec(q, (32.0, 256.0)))

    @staticmethod
    def _center(d):
        y = 256.0 - d
        return (TEX_CENTER[0] + TEX_CENTER[1] * y, y)

    def at(self, d):
        """Canvas point on the tube's centre line, d texture px above the texture bottom."""
        return self.tex(self._center(d))

    @property
    def sprite_pos(self):
        return self.pos

    def sprite(self, local_id, texture, z, blend='Blend', offset=(0.0, 0.0), **kw):
        return E(local_id, 'SpriteElement', pos=add(self.pos, offset), dims=(64, 256), just=(0, 1), scale=(self.sx, RAIL_SY),
                 rot=self.rot, z=z, texture=texture, blend=blend, **kw)


def edge_x(edge, y):
    (x0, y0), (x1, y1) = edge
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


# v0.23 (user, GH5 footage): the tubes lie ON the highway border, coaxial with it (the border runs under the tube and
# the tube's curled end rests on it). Border centre lines measured on the v0.21 capture (images/16.jpg, game px):
# x = a + b*(710 - y). The side-meter descs draw at game = canvas + RAIL_GAME_CAL (preview GAME_CALIB), so the
# target lines are converted to canvas before aligning. The wider border (sidebar_x_scale 2.8) keeps the centre line.
RAIL_ON_BORDER = True
BORDER_LINE_L = (352.5, 0.518)
BORDER_LINE_R = (927.5, -0.517)
RAIL_GAME_CAL = (1.0, 9.0)
RAIL_OUTSET = (-13.4, 15.7)     # v0.29 (both 3 px further out, user pick; v0.28 -8.4/10.7)
_RAIL_OUTSET_V028 = (-8.4, 10.7)   # v0.28 (SP +4 px right, user pick): in game the border sits 8.5 px further out than the v0.27 mock (4 shots, both sides); tubes follow so they sit on the thick bevel as mocked
_RAIL_OUTSET_V027 = (0.1, -1.8)  # v0.27: follow the border 12 px in (user pick); SP 1.5 px more in to match the rock meter's gap
_RAIL_OUTSET_V025E = (-11.9, 11.7)    # v0.25e: user picked tilt 1.5 + 2.5 px further out (v0.25c -9.4/+9.2)
_RAIL_OUTSET_V025C = (-9.4, 9.2)      # v0.25c: on WoR's thick bevel, a sliver over its thin rail (v0.25 mock -7.4/+7.2)
_RAIL_OUTSET_V023E = (-5.0, 4.0)      # v0.23e: user picked option 4 (4 px back towards the highway)
_RAIL_OUTSET_V023D = (-9.0, 8.0)      # v0.23d: GH5's tubes sit outward of the border (grid read, f700: rock ~9-12 px left,
                                # star power ~8 px right of the coaxial position); horizontal canvas px
RAIL_TILT = 1.75                 # deg, see on_border() (v0.25e, user)
RAIL_BACKING = True             # v0.23e: user picked B
RAIL_GAP_FILL = (2.0, 4.0)      # extra black backing copies shifted towards the highway: fills the gap to the border
_RAIL_BACKING_OLD = False           # opaque black copy of each tube behind it (alternate look: no see-through glass)
RAIL_ALIGN_D = 130.0            # tube height (px above the texture bottom) where the centre lines are made to meet


def on_border(rail, line):
    """Rotate the rail about its anchor so its centre line runs parallel to the border line, then shift it
    horizontally so they coincide (at RAIL_ALIGN_D)."""
    if not RAIL_ON_BORDER:
        return rail
    a, b = line
    target = math.degrees(math.atan2(b, 1.0))         # border centre-line angle (going up), same convention as .angle
    # RAIL_TILT: extra lean of the tube's top towards the highway (WoR's border bevel converges towards its inner
    # edge going up, so its centre line is steeper than the strip; up to ~2.7 deg)
    target += RAIL_TILT if rail.outward < 0 else -RAIL_TILT
    rail.rot += target - rail.angle
    rail.refresh()
    p = rail.at(RAIL_ALIGN_D)
    gy = p[1] + RAIL_GAME_CAL[1]
    tx = a + b * (710.0 - gy) - RAIL_GAME_CAL[0]
    rail.pos = (rail.pos[0] + tx - p[0] + (RAIL_OUTSET[0] if rail.outward < 0 else RAIL_OUTSET[1]), rail.pos[1])
    rail.refresh()
    return rail


LEFT = on_border(Rail(LEFT_EDGE, outward=-1.0, mirror=False), BORDER_LINE_L)    # rock meter: unmirrored (WoR)
RIGHT = on_border(Rail(RIGHT_EDGE, outward=1.0, mirror=True), BORDER_LINE_R)    # star power: mirrored (WoR: scale (-s, s))


def dummy(local_id, kind='SpriteElement', **kw):
    if kind == 'TextBlockElement':
        return E(local_id, kind, alpha=0.0, hidden=True, font=SCORE_FONT, dims=(10, 10), **kw)
    if kind == 'SpriteElement':
        return E(local_id, kind, dims=(4, 4), texture=BLANK, alpha=0.0, **kw)
    return E(local_id, kind, dims=(4, 4), **kw)


def lift(root):
    """Add HUD_Z to every element's draw priority (keeps their relative order)."""
    def walk(e):
        e.z = e.z + HUD_Z
        for c in e.children:
            walk(c)
    walk(root)
    return root


# v0.23: the tubes draw just above the highway border (sidebar sprites z 3) and below the strikeline cups (3.1-3.9)
# and the gems, instead of HUD_Z: absolute draw priorities by local_id, set after lift().
# v0.23c: per-element darkening measured against GH5 (5 frames, low-saturation pixels, median / p85 brightness):
# rock tube highlights 221 vs GH5 88 (p85), star power tube already slightly darker than GH5, score box 43 vs 27
# (p50), streak box 36 vs 24, multiplier badge equal.
RAIL_TINT_L = (217, 217, 217, 255)  # rock meter tube art x0.59
RAIL_TINT_R = (255, 255, 255, 255)  # star power tube art x0.9
SCORE_TINT = (161, 161, 161, 255)   # score box art + glass x0.63
STREAK_TINT = (171, 171, 171, 255)  # streak box art + front x0.67
RAIL_TINT = RAIL_TINT_L
RAIL_SHADOW_A = 0.6
RAIL_SHADOW_OFF = (1.5, 2.0)        # canvas px, down-right
RAIL_Z = {'rm_shadow': 3.01, 'sp_shadow': 3.01, 'rm_gap0': 3.012, 'rm_gap1': 3.012, 'sp_gap0': 3.012, 'sp_gap1': 3.012, 'rm_back': 3.015, 'sp_back': 3.015, 'lights_bg': 3.02, 'red_light': 3.04, 'yellow_light': 3.04, 'green_light': 3.04,
          'sp_base': 3.02, 'sp_frame': 3.07, 'sp_marker': 3.08,
          'needle_anchor': 3.09, 'side_meter_needle': 3.09, 'side_meter_red_ON': 3.06}
RAIL_Z.update({f'sp_seg{i}': 3.05 for i in range(6)})
# v0.25c (user): the multiplier's arm goes behind the highway -> the badge image draws under the highway surface (0.1)
RAIL_Z['nixie'] = 0.05
RAIL_Z.update({f'{t}_void{n}': 0.04 for t in ('rm', 'sp') for n in ('', '1', '2', '3')})   # v0.33 (user): the ball draws under the highway surface (0.1), like the multiplier badge (0.05); was 3.003
RAIL_Z.update({f'sp_seg{i}_fill': 3.05 for i in range(6)})


# v0.30 (user): soft outer shadows so the HUD blends into the highway like GH5's. Each target sprite gets rings of
# copies of its own art tinted black at low alpha (8 directions per ring, biased down-right): a faked blur, built
# only from the element's extracted texture. Copies sit just under the target (tube copies under the tube shadow).
VOID_D = 28.0                   # v0.35 (user): smaller, darker, harder ball (was 48, smooth gradient)
VOID_STACK = 2                  # copies stacked for a harder edge
VOID_A = 1.0
VOID_ROW = 236.0                 # tube texture row of the ball centre (the curled end)
VOID_OFF = ((0.0, 0.0), (0.0, 0.0))   # extra canvas (x, y) per side (rock, star power)
OUTER_SHADOW = True
OUTER_SHADOW_RINGS = ((1.5, 0.036), (3.0, 0.024), (5.0, 0.016), (7.5, 0.01))   # v0.33 (user): option B x0.2; D was 2/4.5/7.5/11/15/19 at .14-.02, B x1 .18/.12/.08/.05
OUTER_SHADOW_BIAS = (1.0, 1.5)
OUTER_SHADOW_TARGETS = {'score_back': None, 'streak_box': None, 'band_hud_star_overlay': None,
                        'rm_back': 3.005, 'sp_back': 3.005}           # id -> absolute z (None: just under the target)


def tube_void_centres():
    return [(t, add(rail.tex((TEX_CENTER[0] + TEX_CENTER[1] * VOID_ROW, VOID_ROW)), off))
            for t, rail, off in (('rm', LEFT, VOID_OFF[0]), ('sp', RIGHT, VOID_OFF[1]))]


def add_outer_shadows(root):
    import copy
    if not OUTER_SHADOW:
        return root

    def walk(e):
        out = []
        for c in e.children:
            walk(c)
            if c.local_id in OUTER_SHADOW_TARGETS:
                n = 0
                for r, a in OUTER_SHADOW_RINGS:
                    nd = 8 if r < 8.0 else 12            # more copies on the wide rings so the blur stays smooth
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


def rail_z(root):
    def walk(e):
        if e.local_id in RAIL_Z:
            e.z = RAIL_Z[e.local_id]
        for c in e.children:
            walk(c)
    walk(root)
    return root


def graveyard(local_id, children):
    return E(local_id, 'windowelement', pos=(-64, -64), dims=(0, 0), just=(-1, -1), children=children)


# ---------------------------------------------------------------- score / band meter (alias_band_meter)
SCORE_C = (1055.6, 581.0)       # centre of the 512x128 score box texture (WoR frame: star at (1149, 579))
SCORE_K = 0.775                 # WoR's own on-screen scale for it (1.35 * 0.7 * 0.82)
# GH5's score box is ~8 longer than WoR's at this scale (left end 5 further left, star 3 further right): the box art,
# its star holder, the star, the progress bar and its slot are stretched horizontally about SCORE_C by this factor
SCORE_X_K = 1.039
# Everything else in the panel is placed with WoR's uidesc_star_meter offsets, expressed in its score_container
# frame (canvas units per frame unit K0 = 0.7 * 0.82; score_bg centre at BG_OFF in that frame).
K0 = SCORE_K / 1.35
BG_OFF = (37.011, 16.931)


def score_tex(x, y):
    """Canvas point of a pixel of the score box texture."""
    return (SCORE_C[0] + (x - 256) * SCORE_K, SCORE_C[1] + (y - 64) * SCORE_K)


def sx(p):
    """Stretch a canvas point horizontally about the score box centre (SCORE_X_K)."""
    return (SCORE_C[0] + (p[0] - SCORE_C[0]) * SCORE_X_K, p[1])


def sm(x, y):
    """Canvas point of a WoR star_meter score_container-frame point."""
    return (SCORE_C[0] + (x - BG_OFF[0]) * K0, SCORE_C[1] + (y - BG_OFF[1]) * K0)


SP_SEGMENTS = 6
SP_FILL_FLIP = True             # mirrored like the tube (an unflipped test in the v0.21 mock did not help: the misfit was the span)
SP_FILL_COLS = (35, 63) if not SP_FILL_FLIP else (0, 28)   # fill band texture columns holding the fill art
# v0.22 (user idea): shaped segments. Each of the six segments has its OWN texture cut from SP_Base's glass
# interior for its rows (row by row: alpha span minus SP_RIM), filled with SP_Fill01's colour profile, and is drawn
# with the tube's own transform, so the fill can't leave the glass anywhere. The DE writes one texture name into all
# segments (glow{i}_texture); that prop names a container per segment (see sp_segments). Lower 3 segments run
# from SP_FILL_BOTTOM up to the divider row, upper 3 from the divider to SP_FILL_TOP: at 50% the fill meets the needle.
SP_SHAPED = False             # v0.25b diagnostic: v0.25 crashed at song start (containers receiving the DE tube texture are the prime suspect)
SP_FILL_TOP, SP_FILL_BOTTOM = 21.0, 232.0   # SP_Base rows: glass starts under the top cap; the curled end's glass
SP_SEG_TEX = (64, 64)           # per-segment texture size (POT)
# v0.21 layering experiment (frame over the fill), off with shaped segments
SP_FRAME = False
SP_FRAME_ROWS = (21, 221)
SP_FRAME_RIM = (2, 2)
SP_SLANT_DEG = 8.3              # screen angle of the partial fill's top edge (None = square to the tube)
SP_FILL_ROWS = (14.0, 237.0)    # v0.20 span (only used when SP_SHAPED is False)
SP_FILL_SPLIT = True            # v0.28: lower 3 segments end at the half divider (50% meets the needle)
SP_RIM = 3.0                    # tube rim on each side, texture px (the fill sits inside the glass)


def sp_tube_width(y):
    """Width of SP_Base's tube at texture row y (alpha span: 22 px at row 20, 30 px at row 220)."""
    return 22.0 + 0.04 * (y - 20.0)


# Values below measured against GH5 (OneDrive\Videos\GH5\original.mp4, frame-averaged, fret-aligned) with the
# game-calibrated mock (tools/preview_hud.py --game); see MODLOG v0.19.
SP_MARKER_Y = 528.0             # GH5's half divider at game y 531 (band meter game offset +3); x = tube centre
SP_MARKER_ROT = 37.0            # SB_TubeNeedle01's arc chord is -28.7 deg; GH5's divider is a level-ish arch (+8.7)
SP_MARKER_K = 1.25              # GH5's divider spans the whole tube
SP_FILL_RGBA = (20, 235, 180, 235)   # GH5 fill is teal (mean 65,139,129); v0.17's (70,205,255) read grey-blue
SCORE_TEXT_KX = 1.08             # GH5 digits: 1.11x as wide, pitch 19 vs 18 (v0.17 capture)
SCORE_TEXT_K = 0.90              # overall score digit size (user: a bit smaller; kept centred on the same line)
SCORE_TEXT_KY = 1.26             # GH5 digits: 17 px tall vs 13 (taller, narrower than WoR's numerals)
SCORE_TEXT_SHIFT = (0.4, -2.0)  # relative to the panel: GH5 digit tops at 569
STAR_K = 1.14                   # GH5 gold star 57x51 px vs 48x45 in v0.19b (same mask), user: a little bigger
STAR_SHIFT = (4.2, -1.0)         # relative to the (stretched) panel
STAR_ART_C = (63.69, 70.73)     # centre of mass of the filled gold star in its 128 px texture (5-point stars sit low)
STAR_OVERLAY_PX = 3.0         # gold star outline (overlay/shine/glow) grows by this many px (GH5 star ~57 px)
STAR_BG_RGBA = (130, 126, 128, 255)    # dims the silver frame's grey centre to GH5's (~65,60,60 at the middle)
STAR_NUM_NUDGE = (-0.8, -2.0)     # the count is centred on the gold star's shape (user, v0.20 test: it sat 3 px right/up)
STREAK_SHIFT = (-1.6, 1.0)      # relative to the panel (not stretched)
STREAK_TEXT_Y = 1.55            # streak-texture px from its centre (WoR desc 9.289): GH5 digits 7 higher
SP_FILL_BAND = (0, 44, 64, 60)  # SP_Fill01 rows without its tapered top / bent tail, constant edge (64x16, POT)
STREAK_RIGHT = 98.0             # streak text right edge, streak-texture px from its centre (window ends at ~220/256)
STREAK_NUM_K = 0.555           # GH5 streak digits 14 px tall / pitch 18 (v0.17 at 0.49: 12 / 15.5)
STAR_NUM_K = 0.78               # GH5's star count 20 px tall (v0.17 at 0.62: 15)
SP_DEFAULT_SCALE = 0.3          # the DE's star-power tube scale for non-classic themes (hud_widgets)



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


def sp_segment_rows():
    """[(top row, bottom row)] of the six segments, bottom segment first."""
    d = sp_divider_row()
    n = SP_SEGMENTS // 2
    lower = [(SP_FILL_BOTTOM - (i + 1) * (SP_FILL_BOTTOM - d) / n, SP_FILL_BOTTOM - i * (SP_FILL_BOTTOM - d) / n) for i in range(n)]
    upper = [(d - (i + 1) * (d - SP_FILL_TOP) / n, d - i * (d - SP_FILL_TOP) / n) for i in range(n)]
    return lower + upper


def sp_segments():
    segs = []
    if SP_SHAPED:
        for i, (top, bot) in enumerate(sp_segment_rows()):
            # The DE's tube widget sets texture AND scale on the element glowN_texture names (exe 0x478630), so
            # both props go to a container: the texture name is ignored there, the scale (0.3, 0.3*fill) squashes
            # the shaped sprite inside it towards the container origin = the segment's bottom-centre on the tube
            segs.append(E(f'sp_seg{i}', 'ContainerElement', pos=RIGHT.tex((32.0, bot)), dims=(0, 0), just=(-1, -1),
                          rot=RIGHT.rot, scale=(SP_DEFAULT_SCALE, 0.0), z=3.5, children=[
                E(f'sp_seg{i}_fill', 'SpriteElement', pos=(0.0, 0.0), just=(0, 1), z=3.5,
                  dims=(64.0 * RAIL_SX / SP_DEFAULT_SCALE, (bot - top) * RAIL_SY / SP_DEFAULT_SCALE),
                  rgba=SP_FILL_RGBA, texture=f'WoR_HUD_sp_seg{i}', blend='Add')]))
        return segs
    for i, (top, y0) in enumerate(sp_fill_rows()):
        seg_len = y0 - top
        ym = y0 - seg_len / 2
        inner = sp_tube_width(ym) - 2 * SP_RIM
        wc = inner * RAIL_SX * 64.0 / (SP_FILL_COLS[1] - SP_FILL_COLS[0] + 1)
        content_c = ((SP_FILL_COLS[0] + SP_FILL_COLS[1] + 1) / 2 / 64.0 - 0.5) * wc
        centre = RIGHT.tex((TEX_CENTER[0] + TEX_CENTER[1] * ym, y0))
        base = add(centre, rot((-content_c, 0.0), RIGHT.rot))
        h = seg_len * RAIL_SY
        if SP_SLANT_DEG is not None:
            # slanted cut: the shared fill texture is a parallelogram (sp_slant_geom) made for the mean segment
            # height; the sprite is taller by the slant and sits d lower, so the content bottom at the tube centre
            # stays where it was. One texture for all segments: the slant margin scales with the segment's height.
            d = sp_slant_geom()[0] * h / SEG_H_CANVAS
            base = add(base, rot((0.0, d), RIGHT.rot))
            h = h + 2 * d
        segs.append(E(f'sp_seg{i}', 'SpriteElement', pos=base, just=(0, 1), rot=RIGHT.rot, z=3.5,
                      dims=(wc / SP_DEFAULT_SCALE, h / SP_DEFAULT_SCALE),
                      scale=(SP_DEFAULT_SCALE, 0.0),
                      rgba=SP_FILL_RGBA, texture='hud_rock_tube_glow_full', blend='Add'))
    return segs


def sp_fill_rows():
    """[(top row, bottom row)] of the sprite segments, bottom first. v0.28: the lower half runs from the tube end
    to the half divider, the upper half from the divider to the top, so 50% (3 full segments) ends at the needle
    (evenly spaced segments ended 18.6 rows = 13 px below it)."""
    if not SP_FILL_SPLIT:
        n = (SP_FILL_ROWS[1] - SP_FILL_ROWS[0]) / SP_SEGMENTS
        return [(SP_FILL_ROWS[1] - (i + 1) * n, SP_FILL_ROWS[1] - i * n) for i in range(SP_SEGMENTS)]
    d, n = sp_divider_row(), SP_SEGMENTS // 2
    lo, hi = (SP_FILL_ROWS[1] - d) / n, (d - SP_FILL_ROWS[0]) / n
    return ([(SP_FILL_ROWS[1] - (i + 1) * lo, SP_FILL_ROWS[1] - i * lo) for i in range(n)]
            + [(d - (i + 1) * hi, d - i * hi) for i in range(n)])


def sp_slant_geom():
    """(D, slope) of the slanted fill cut: the partial segment's top edge runs at SP_SLANT_DEG on screen
    (clockwise positive, like the divider) instead of square to the tube. slope = local dy/dx (canvas), D = half
    the vertical spread of the cut over the fill's width (canvas px)."""
    import math
    theta = math.radians(SP_SLANT_DEG - RIGHT.rot)
    slope = math.tan(theta)
    width = (sp_tube_width(125.0) - 2 * SP_RIM) * RAIL_SX
    return abs(slope) * width / 2, slope

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
    SOV = (57.0 + STAR_OVERLAY_PX) / 57.0                 # gold outline growth factor
    star = add(sc_star, scale((164.83, -29.77), K0))
    star_c = star
    overlay = add(sc_star, scale((165.368, -31.2023), K0))
    filler_l = sx(add(sc, scale((-171.40, -4.25), K0)))
    s_box = add(sm(8.209, 75.272), STREAK_SHIFT)      # streak sprite centre (scale 0.9 in the frame)
    segs = sp_segments()
    sk = K0 * 0.9                                      # streak sprite scale on the canvas
    streak = E('streak', 'ContainerElement', just=(-1, -1), z=3.0, children=[
        E('streak_box', 'SpriteElement', pos=s_box, dims=(256, 64), scale=(sk, sk), z=3.0,
          rgba=STREAK_TINT, texture='WoR_HUD_streak'),
        # right-aligned inside the streak window (WoR reference), a bit smaller than WoR's desc scale 0.56
        E('streak_number', 'TextBlockElement', pos=add(s_box, scale((STREAK_RIGHT, STREAK_TEXT_Y), sk)), dims=(300, 100),
          just=(1, 0), scale=(sk * STREAK_NUM_K, sk * STREAK_NUM_K), z=3.2, rgba=(255, 128, 0, 255), font=SCORE_FONT,
          text='c6081e83', shadow=False),
        E('streak_front', 'SpriteElement', pos=add(s_box, scale((3.268, 2.816), sk)), dims=(256, 64),
          scale=(sk, sk), z=3.4, rgba=STREAK_TINT, texture='WoR_HUD_streak_front'),
    ])
    box_tl = (SCORE_C[0] - 256 * SCORE_K, SCORE_C[1] - 64 * SCORE_K)
    root = E('meter_container', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        # score box: star-progress fill behind the box art (WoR FX_window/star_filler), black bG behind both,
        # glass front over the score
        E('star_filler', 'SpriteElement', pos=filler_l, dims=(306 * K0 / 0.7 * SCORE_X_K, 25 * K0), just=(-1, 0),
          scale=(0.7, 1.0), z=4.0, rgba=(249, 193, 34, 255)),
        E('score_back', 'SpriteElement', pos=SCORE_C, dims=(512, 128), scale=(SCORE_K * SCORE_X_K, SCORE_K), z=5.0,
          rgba=SCORE_TINT, texture='WoR_HUD_score_box'),
        E('Score', 'TextBlockElement', pos=add(box_tl, scale((315.151, 44.783), SCORE_K), SCORE_TEXT_SHIFT, (0.0, (1.0 - SCORE_TEXT_K) * 8.5)),
          dims=(536, 65), just=(1, -1), scale=(0.386667 * SCORE_K * SCORE_TEXT_KX * SCORE_TEXT_K, 0.386667 * SCORE_K * SCORE_TEXT_KY * SCORE_TEXT_K), z=6.0, font=SCORE_FONT,
          text='0x00000000', shadow=False),
        E('score_front', 'SpriteElement', pos=sx(sm(40.857, 18.429)), dims=(512, 128), scale=(SCORE_K * SCORE_X_K, SCORE_K),
          z=7.0, rgba=SCORE_TINT, texture='WoR_HUD_score_front'),
        E('band_hud_star_frame', 'SpriteElement', pos=star, dims=(128, 128), scale=(SCORE_K * STAR_K, SCORE_K * STAR_K), z=9.0,
          texture=BLANK),
        E('star_bg', 'SpriteElement', pos=star, dims=(128, 128), scale=(SCORE_K * STAR_K, SCORE_K * STAR_K), z=8.5,
          rgba=STAR_BG_RGBA, texture='WoR_HUD_star_bg'),
        E('band_hud_star_overlay', 'SpriteElement', pos=overlay, dims=(128, 128), scale=(SCORE_K * STAR_K * SOV, SCORE_K * STAR_K * SOV),
          z=10.0, texture='WoR_HUD_star_overlay'),
        E('band_HUD_gold_star_glow', 'SpriteElement', pos=add(overlay, scale((1.065, 1.123), SCORE_K)),
          dims=(128, 128), scale=(SCORE_K * 0.8 * STAR_K * SOV, SCORE_K * 0.8 * STAR_K * SOV), z=11.0, alpha=0.0, texture='WoR_HUD_star_glow',
          blend='Add'),
        E('star_meter_num', 'TextBlockElement', pos=add(overlay, scale((STAR_ART_C[0] - 64, STAR_ART_C[1] - 64), SCORE_K * STAR_K), STAR_NUM_NUDGE),
          dims=(40, 50),
          just=(0, 0), scale=(K0 * STAR_NUM_K, K0 * STAR_NUM_K), z=12.0, rgba=(249, 193, 34, 255), font=SCORE_FONT,
          text='0x4a4d8830',
          shadow=False),
        streak,
        E('slot_bg', 'SpriteElement', pos=sx(add(sc, scale((-13.02, -8.03), K0))),
          dims=(309, 50), scale=(K0 * SCORE_X_K, K0), z=3.9, rgba=(0, 0, 0, 255)),
        # the DE spawns its star-earned sparks inside alias_star_flame
        E('star_flame', 'ContainerElement', pos=star_c, dims=(4, 4), just=(-1, -1), z=13.0),
        E('star_shine', 'SpriteElement', pos=overlay, dims=(128, 128), scale=(SCORE_K * STAR_K * SOV, SCORE_K * STAR_K * SOV), z=10.5,
          alpha=0.45, texture='WoR_HUD_star_overlay', blend='Add'),
        # rock meter rail (left): tube, LEDs (DE light alphas), end cap
        # v0.23b: drop shadows under the tubes (same art tinted black) and darker tube art, like GH5's
        LEFT.sprite('rm_shadow', 'WoR_HUD_rm_base', z=2.0, rgba=(0, 0, 0, 255), alpha=RAIL_SHADOW_A, offset=RAIL_SHADOW_OFF),
        RIGHT.sprite('sp_shadow', 'WoR_HUD_sp_base', z=2.0, rgba=(0, 0, 0, 255), alpha=RAIL_SHADOW_A, offset=RAIL_SHADOW_OFF),
        *([LEFT.sprite('rm_back', 'WoR_HUD_rm_base', z=2.0, rgba=(0, 0, 0, 255)),
           RIGHT.sprite('sp_back', 'WoR_HUD_sp_base', z=2.0, rgba=(0, 0, 0, 255))] if RAIL_BACKING else []),
        # v0.30 (user): a soft black ball behind each tube's curled bottom end, so nothing shows under it
        # VOID_STACK copies on top of each other: a harder, darker edge from the same texture (1-(1-a)^n)
        *([E(f'{t}_void' + (f'{n}' if n else ''), 'SpriteElement', pos=c, dims=(64, 64), scale=(VOID_D / 64.0, VOID_D / 64.0),
             z=2.0, rgba=(0, 0, 0, 255), alpha=VOID_A, texture='WoR_HUD_void')
           for t, c in tube_void_centres() for n in range(VOID_STACK)] if VOID_D else []),
        *([e for i, g in enumerate(RAIL_GAP_FILL) for e in (
            LEFT.sprite(f'rm_gap{i}', 'WoR_HUD_rm_base', z=2.0, rgba=(0, 0, 0, 255), offset=rot((g, 0.0), LEFT.rot)),
            RIGHT.sprite(f'sp_gap{i}', 'WoR_HUD_sp_base', z=2.0, rgba=(0, 0, 0, 255), offset=rot((-g, 0.0), RIGHT.rot)))]
          if RAIL_BACKING else []),
        LEFT.sprite('lights_bg', 'WoR_HUD_rm_base', z=2.0, rgba=RAIL_TINT_L),
        LEFT.sprite('red_light', 'WoR_HUD_rm_red', z=2.5, blend='Add'),
        LEFT.sprite('yellow_light', 'WoR_HUD_rm_yellow', z=2.5, blend='Add'),
        LEFT.sprite('green_light', 'WoR_HUD_rm_green', z=2.5, blend='Add'),
        # star power rail (right): tube, fill segments (DE tube scales), end cap
        RIGHT.sprite('sp_base', 'WoR_HUD_sp_base', z=3.0, rgba=RAIL_TINT_R),
        *([RIGHT.sprite('sp_frame', 'WoR_HUD_sp_frame', z=3.7)] if SP_FRAME else []),
        *segs,
        # GH5: the half divider is a near-horizontal band at canvas y ~531, not perpendicular to the tube
        E('sp_marker', 'SpriteElement', pos=sp_marker_pos(), dims=(64, 64),
          scale=(RAIL_SX * 1.1 * SP_MARKER_K, RAIL_SX * 1.1 * SP_MARKER_K), rot=SP_MARKER_ROT, z=3.9,
          texture='WoR_HUD_needle'),
        # driven by the DE, not shown in WoR (the song-time bar was the "ghost bar" above the score box): a
        # zero-size window clips them whatever texture / dims / alpha the DE sets
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
# GH3:WoR multiplier image (HUD_score_nixie_*, cropped to 160x144): a stick at 28.87 deg from vertical (axis
# x = 9.5 + 0.55 * y in crop px) ending at ~(69, 110), and the badge disc beside it. The stick continues the star
# power rail upward; the streak lights sit on the stick.
BADGE_TEX = (256, 256)           # power of two: other sizes get padded by the converter
BADGE_STICK_END = (69.0, 110.0)  # crop px: bottom of the stick = top of the star power rail
BADGE_STICK_ANGLE = -28.87     # the stick leans up-left, like the right highway edge (negative = CCW)
BADGE_K = 0.7                    # canvas units per crop px
RAIL_TOP_D = 252.0               # texture px along the rail where the stick takes over (tube top)
BADGE_TUCK = 5.0                 # shift towards the highway so the arm runs under the highway border
# GH3:WoR career_hud_2d_elements: nixie at (-278,-230), lights 1..5 at (-235,-165)..(-275,-233) step (-10,-17),
# all 1:1 and top-left anchored -> light centres in badge-crop px (light0 = lowest):
LED_CROP = [(58.0, 80.0), (48.0, 63.0), (38.0, 46.0), (28.0, 29.0), (18.0, 12.0)]


def badge_point(top, turn, q):
    """Canvas point of badge-crop pixel q (the image is anchored at its stick end on `top`, turned, scaled)."""
    v = ((q[0] - BADGE_STICK_END[0]) * BADGE_K, (q[1] - BADGE_STICK_END[1]) * BADGE_K)
    return add(top, rot(v, turn))


def edge_x(edge, y):
    (x0, y0), (x1, y1) = edge
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


# GH5 frames (fret-aligned): badge centre (845,447) and the streak marks along (775,385)-(812,445), off the border
BADGE_SHIFT = (-4.05, -19.87)  # v0.25e: same badge position as v0.25c after the tube tilt/shift
_BADGE_SHIFT_V025C = (-1.0, -17.0)  # v0.25c: 3 px closer + 2 px to cancel the SP tube's move; was (4,-17)
_BADGE_SHIFT_V025B = (4.0, -17.0)   # GH5 badge centre ~(843.5,445); v0.25 (user): 4 left / 3 down, holder against the border
LIGHT_SHIFT = (-4.05, -19.87)    # = BADGE_SHIFT: the marks sit inside the badge art's holder bar (v0.23: 4 px right of it)


def player_meter():
    top = add(RIGHT.at(RAIL_TOP_D), rot((-BADGE_TUCK, 0.0), RIGHT.angle))   # towards the highway
    badge = add(top, BADGE_SHIFT, (-G1[0], -G1[1]))
    turn = RIGHT.angle - BADGE_STICK_ANGLE          # align the image's stick with the rail
    just = (2 * BADGE_STICK_END[0] / BADGE_TEX[0] - 1, 2 * BADGE_STICK_END[1] / BADGE_TEX[1] - 1)
    leds = []
    for i, q in enumerate(LED_CROP):   # each GH3:WoR light image holds 2 of WoR's 10 marks
        p = add(badge_point(top, turn, q), LIGHT_SHIFT, (-G1[0], -G1[1]))
        leds.append(E(f'light{i}', 'SpriteElement', pos=p, dims=(32, 32), scale=(BADGE_K, BADGE_K), rot=turn,
                      z=6.5, texture='HUD_score_light_0'))
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
    """Anchor scale that stretches the DE's needle path onto the left rail's LED span."""
    a, b = LEFT.at(LED_BOTTOM), LEFT.at(LED_TOP)
    end = (b[0] - a[0], b[1] - a[1])
    return (end[0] / DE_NEEDLE_END[0], end[1] / DE_NEEDLE_END[1])


def side_meter():
    ax, ay = needle_anchor_scale()
    # +3 toward the tube centre: the DE's path bends slightly left of the straight rail between its end points
    anchor = add(LEFT.at(LED_BOTTOM), (-G1[0], -G1[1]))
    nd = 40.0                    # needle size on screen (WoR's glowing slider)
    needle = E('side_meter_needle', 'SpriteElement', dims=(nd / ax, nd / ay), just=(0, 0), z=20.0,
               rot=LEFT.angle, texture='WoR_HUD_needle_glow', blend='Add')
    root = E('side_meter_band', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        E('needle_anchor', 'ContainerElement', pos=anchor, just=(-1, -1), scale=(ax, ay), z=20.0, children=[needle]),
        E('side_meter_red_ON', 'SpriteElement', pos=add(LEFT.sprite_pos, (-G1[0], -G1[1])), dims=(64, 256),
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
    off = (0.0, 0.0)   # content is authored g1-relative; an offset here was applied twice in game
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


# WoR textures these descs use: mod texture name -> WoR png (z_in_game / ui_shared).
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
    # v0.30 tube-end void: WoR's soft radial gradient (career_map circle_gradient_smooth_64), drawn tinted black
    'WoR_HUD_void': r'C:\Users\rockb\ghwor-extract\circle_png\circle_gradient_64.png',   # v0.35: the harder WoR gradient (global_textures)
}

# Multiplier images: (theme texture name, GH3:WoR source). Normal x1..x4, star power x2..x8.
GH3WOR_PNG = r'C:\Users\rockb\ghwt-extract\gh3wor\global_png'
MULT_NORMAL = [('WoR_HUD_mult_1', 'HUD_score_nixie_1a'), ('WoR_HUD_mult_2', 'HUD_score_nixie_2a'),
               ('WoR_HUD_mult_3', 'HUD_score_nixie_3a'), ('WoR_HUD_mult_4', 'HUD_score_nixie_4a')]
MULT_SP = [(f'WoR_HUD_mult_sp{n}', f'HUD_score_nixie_{n}b') for n in (2, 4, 6, 8)]
# Note-streak lights: GH3:WoR's images under the DE's own names (state 0/1/2 x base/green/purple/blue)
STREAK_LIGHTS = [f'HUD_score_light_{st}{c}' for st in range(3) for c in ('', '_green', '_purple', '_blue')]

# Highway side borders (theme key 18f90ff6, read by the DE's material setup at song start). It must name a texture
# the material system can see: a texture in our per-song theme pak made the border vanish (v0.20 test), so this uses
# the GH Metallica theme's darker worn-metal border (0x0d6323dc, in the always-loaded global_model_tex_wtde.pak;
# mean 114 vs the stock sidebar01's 137). Theme-only: other themes keep their own border.
SIDEBAR_TEX = None   # v0.21 (user): back to the DE's stock border (thick at sidebar_x_scale 2.0); GHM's read as a thin blue line
# v0.25: WoR's own highway border (thick dark bevel + thin inner rail), shipped in a copy of the WoR gem pak.
# Placement from the approved mock (verify/mock_full_v025.png): 28 px visible at the strikeline, thin rail under the
# outermost rings. The DE maps the whole texture across its sidebar sprite: its stock sidebar01 (32 px wide, 28 texels
# of content) shows ~19 px at scale 2.0 -> sprite ~21.7 px; WoR's 64-px texture has 36 texels of content -> scale 4.6
# for 28 px, and the strip moves out ~19 px so its inner edge (texel 62.5) lands at x 393 (left) at y 638.
# Estimates: verify in game.
WOR_BORDER = True
BORDER_SRC = r'C:\Users\rockb\ghwor-extract\basic_gems_png\388dd606.png'
BORDER_TEX_NAME = 'WoR_HUD_border'
BORDER_GEM_PAK = 'gems_ghwor_hud'
BORDER_X_SCALE = 2.6
BORDER_OFFSET = 17.4             # v0.27: 12 px closer to the highway (user pick; v0.26 29.4, ~1 unit = 1 px at y 680)
SIDEBAR_SRC = None   # no border texture ships in our pak
SIDEBAR_K = None


# slanted fill texture geometry (shared texture, so one mean segment size)
SEG_H_CANVAS = (SP_FILL_ROWS[1] - SP_FILL_ROWS[0]) / SP_SEGMENTS * RAIL_SY
SEG_W_CANVAS = (sp_tube_width(125.0) - 2 * SP_RIM) * RAIL_SX * 64.0 / (SP_FILL_COLS[1] - SP_FILL_COLS[0] + 1)
