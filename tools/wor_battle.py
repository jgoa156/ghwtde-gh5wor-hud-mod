"""Battle mode (p2_battle) in the WoR style (mock docs/mocks/mock_battle_v8.jpg, approved 2026-10-20).

The DE draws battle with a GH3-style hud_2d layout: the theme row's 0x6bd128d8 names it (default
battle_hud_2d_elements). Its rock container holds the health meter (the DE switches the HUD2D_rock_lights_* alphas and turns
HUD2D_rock_needle by element id) and the attack-slot frame. Our layout WoR_HUD_battle keeps every element id and swaps
the art, so each battle highway carries the main theme's tubes like the 1-player HUD:
  - health: the 1-player WoR rock tube (RM_Base + red / yellow / green LEDs) glued to the highway's left rail, its
    glowing needle sliding up the tube. The DE turns HUD2D_rock_needle (here an invisible stand-in); the HUD fixes
    plugin (1.33) reads that angle and slides our needle (WoR_HUD_bneedle) along the tube on the WoR LED stops;
  - attack slots (user 2026-10-21): the streak meter's visor (WoR's multiplier ring with its arm) three times where
    the star power tube goes on the right rail, big at the bottom, smaller each time up the rail, one behind the
    other, every arm on the rail (baked in the battle orientation: hud_2d elements don't rotate); the attack cards sit
    in the glass, an empty slot shows the dark glass. No streak meter, note streak or star power tube in battle;
  - P2 gets the same set translated onto its highway (rock tube on its left rail, slots on its right rail);
  - name plate (theme c2bf76cf): the DE's gamertag desc with WoR's band lobby gamertag bar (tinted by the team colour).
The attack alerts above the highway stay stock (their design is still open).

The tube textures are the 1-player HUD (tools/preview_hud.py, game calibration) rendered and mapped onto the battle
highway by the affine that takes three points of the 1-player rails (tube bottom / top on its rail, and the other rail)
to the same points of the battle highway (same fraction of the highway height above the strikeline), baked at SS
texture px per canvas unit. Rails measured on the user's footage (2026-10-20, tools/mock_battle.py).

The highways move apart by SEP each: WoR_HUD_get_highway_pos_and_scale (plugin swap of get_highway_pos_and_scale)
moves the Pos it returns (canvas x, -+x_offset_p2) out by SEP per player in battle with this theme. The DE's alert
containers (640 -+ x_offset_p2) stay where they were (their design is still open).

The attack cards are created by guitar_battle in screen space at battle_hud_2d_elements.rock_pos + card_*_off (a
global, not the theme layout), 64x64 at z 19; WoR_HUD_create_battle_alert_frames (plugin swap) moves those offsets into
our slots and sets medium_scale / small_scale while this theme is on, and puts the stock ones back otherwise; the plugin
gives the 64x64 cards our big slot's size (BIG_CARD) while our battle needle is on screen.

Coordinates: the hud_2d root container is scaled by the layout's Scale (0.75), so layout positions are screen / 0.75;
the cards are plain 1280x720 screen positions. rock_pos stays stock (280, 100) / (1180, 100): the gamertag plates are
placed relative to the rock container and must not move.
"""
import math
import os

import numpy as np

import paths
import wor_modes

NAME = 'WoR_HUD_battle'                 # the layout struct (theme row 0x6bd128d8)
FLAG = 'WoR_HUD_battle_hud'             # theme flag read by the wrappers
GAMERTAG = 'hud_gamertag_ghwor'         # theme c2bf76cf (desc uidesc_hud_gamertag_ghwor)
SCALE = 0.75
ROCK_POS = {1: (280.0, 100.0), 2: (1180.0, 100.0)}
STOCK_CARD_OFFS = {                     # guitar_battle's stock card offsets (DE themes' battle layouts)
    'card_1_off_p1': (26.0, 114.0), 'card_2_off_p1': (-44.0, 11.0), 'card_3_off_p1': (-53.0, 37.0),
    'card_1_off_p2': (-200.0, 114.0), 'card_2_off_p2': (46.0, 13.0), 'card_3_off_p2': (53.0, 39.0),
}
STOCK_CARD_SCALES = {'medium_scale': 0.55, 'small_scale': 0.4}    # guitar_battle globals
CARD_DIMS = 64.0                        # guitar_battle creates every card 64x64
# where the rock containers wait before sliding in (stock -420 / 1880): our sets reach the screen middle (P1's slots
# ~600, P2's tube ~650), so the stock ones left them on screen, each on the other side (user footage 2026-10-21)
# the DE slides the rock containers in from here at song start; the user wants no drift (2026-10-22: appear in place
# like the other modes), so they start where they end
OFFSCREEN = {1: (280.0, 100.0), 2: (1180.0, 100.0)}

# ---- source textures (extracted game files)
WOR_GAMERTAG = os.path.join(paths.WOR_EXTRACT, 'band_lobby_png', 'bandlobby_bord_gamertag_color.png')   # Xbox, x360img

# attack slots (user 2026-10-21): the streak meter's visor (WoR's multiplier ring + its short arm, no stick; our WoR_HUD_mult_1:
# the x1 art, empty) three times where the SP tube goes, smaller each time up the rail, one behind the other, each
# arm on the rail; the cards sit in the glass
VISOR_SRC = 'WoR_HUD_mult_1'            # built 1-player texture (preview_hud name)
VISOR_TEX = 'WoR_HUD_bvisor'
VISOR_RING = (113.5, 96.5, 31.5, 40.0)  # in that art: ring centre (texture px), glass radius, rim's outer radius
VISOR_ARM = (50, 101, 84, 126)          # in that art: the short arm joining the ring (kept; the stick above it is cut)
VISOR_ART = (154.0, 137.0)              # the art's extent (top-left of the 256 px texture)
VISOR_SCALES = {'big': 1.0, 'mid': 0.85, 'small': 0.72}
VISOR_GAP = 0.72                        # ring centres this many rim radii apart along the rail (a little overlap)
VISOR_SPACE = 2.0                       # + this many canvas units between ring centres (~3 px at 1080p; user 2026-10-26)
VISOR_DX = 2.7                          # the whole set this many canvas units right (~4 px; user 2026-10-26: the arms a
                                        # bit more visible)
# 2026-10-23 (user: the slots must sit BEHIND the highway, like the 1-player multiplier badge): under the highway
# surface (z 0.1); each card goes just above its own slot (CARD_Z), the bottom slot's pair over the middle one's
VISOR_Z = {'big': 0.07, 'mid': 0.06, 'small': 0.05}
CARD_Z = {'big': 0.075, 'mid': 0.065, 'small': 0.055}
CARD_FILL = 0.82                        # a card fills this much of its visor's glass diameter (0.9 hid the rim: user
                                        # 2026-10-22, the slot's border must show around the card). 2026-10-23: the
                                        # cards weren't sized at all before the script (64 px, "huge"); at 0.375 they
                                        # were too small: "just enough so we can see the rim border"
# a new power-up (user 2026-10-29: "no animation when going to the battle slots"): the card slides HORIZONTALLY from
# the strike line's centre (x, at the big slot's height) into the big slot in ARC_FLY s, over the highway (z FLY_Z),
# along WoR's star power ready lightning (the tube's Tesla arc, Lightining_arc_anim01, 16 frames at 20 fps) in red:
# the battle gems' glow (guitar_material Mat_*_Battle, pass 2 colour 2, 0, 0). The arc spans start -> slot, plays
# ARC_FRAMES frames and fades over the last ARC_FADE s. In the UI pak (always loaded, no size cap).
ARC_NAMES = [f'WoR_HUD_barc_{i:02d}' for i in range(16)]
ARC_RGB, ARC_CORE = (255, 24, 16), (255, 205, 195)
ARC_H = 40.0                            # screen height of the arc sprite (the frames are 256 x 64)
ARC_FLY, ARC_FRAMES, ARC_FADE = 0.25, 10, 0.2
FLY_Z = 19.0                            # the DE's own card z: over the highway while it flies
# the needle at full health a little higher (user 2026-10-29: battle's "feels like it could go further up, just
# slightly"): the top segment of the needle path runs this fraction of itself further; the plugin (1.84) lets the
# needle past the last LED stop by up to 25% of that segment (only this script goes past it)
NEEDLE_TOP_EXTRA = 0.10
HUD_Z = 0                               # the layout's z (stock 0); 4 (round 1) put the slots over the rail, but the
                                        # user wants them behind the highway (2026-10-23, test of 1.48)
VISOR_INSET = 9.0                       # screen px the whole slot set moves towards the highway (user 2026-10-22: the
                                        # arms should barely show)
TUBE_TEX = {'body': 'WoR_HUD_btube', 'red': 'WoR_HUD_btube_red', 'yellow': 'WoR_HUD_btube_yellow',
            'green': 'WoR_HUD_btube_green'}
NEEDLE_TEX = 'WoR_HUD_bneedle'          # the visible needle (the plugin finds it by this name)
BLANK = 'WoR_HUD_blank'
GAMERTAG_TEX = 'WoR_HUD_gamertag_bg'

# ---- battle highway geometry, measured on the user's footage (P1, stock spacing, canvas units)
# extra x_offset_p2 (each highway moves this far outwards). The games' 2-player highways touch; the WoR border is
# thicker than the stock sidebars, so at stock spacing the two borders overlapped ~37 px at the screen's bottom edge.
# User 2026-10-22: they must touch, corrected for the thickness: the user's clip (1:15) showed a 22.5 px gap there at
# 30, so 30 - 22.5 / 2 makes the borders meet at the bottom edge.
SEP = 22.0                              # 19 -> 22 (user 2026-10-22): the borders, lowered (wor_1g.BORDER_DY), must not touch
SEP3 = 12.5                             # 3 instrument highways: x_offset_p3 + this (Pos x 1.8, ~22 px each at the bottom;
                                        # capture 2026-10-22: border lines 25.5 apart vs 55.5 on the 2-player highways)
RAIL_L = ((320.0, 395.0), (170.0, 700.0))           # P1 left / right rail lines (top, bottom)
RAIL_R = ((500.0, 395.0), (652.0, 700.0))
STRIKE_2P, TOP_2P = 633.0, 393.0                     # strikeline / top of the battle highways
STRIKE_1P, TOP_1P = 638.0, 300.0                     # the 1-player highway (tools/mock_base.py)
# test 2026-10-21 (user clip "Video Project 25"): on the moved highways the rock tube's centre sat ~24 px off the left
# rail's outer edge (the 3D highway doesn't move like the pasted mock), leaving a gap; the slots touched their rail
ROCK_NUDGE = np.array((11.0, 0.0))     # 15 -> 11 (user 2026-10-22: a few px left)
SS = 2.0                                # tube textures: texture px per canvas unit
SIDE_METER_CALIB = (1.0, 9.0)           # preview_hud.GAME_CALIB of the 1-player side meter (needle) desc
TUBE_HALF_W = 42.0                      # 1-player canvas: half width of the tube cut (normal to the tube line)
TUBE_EXT = (45.0, 30.0)                 # 1-player canvas: the cut runs this far below / above the LED span
HEALTH_STOPS = (0.0, 2.0 / 3.0, 4.0 / 3.0, 2.0)


def _line_x(line, y):
    (x0, y0), (x1, y1) = line
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _y2p(y1p):
    """Same fraction of the highway's height above its strikeline."""
    f = (STRIKE_1P - y1p) / (STRIKE_1P - TOP_1P)
    return STRIKE_2P - f * (STRIKE_2P - TOP_2P)


def _border(line, y):
    a, b = line
    return a + b * (710.0 - y)


def _affine(src, dst):
    """2x3 matrix taking three points onto three points."""
    a = np.array([[x, y, 1.0] for x, y in src])
    return np.linalg.solve(a, np.array(dst, float)).T


def apply(m, p):
    return (m[0, 0] * p[0] + m[0, 1] * p[1] + m[0, 2], m[1, 0] * p[0] + m[1, 1] * p[1] + m[1, 2])


def tube_maps(sep=SEP):
    """{'rock' | 'sp': 2x3 affine} from the 1-player canvas onto P1's battle highway (moved by sep)."""
    import wor_1g
    yb, yt = wor_1g.LEFT.at(wor_1g.LED_BOTTOM)[1], wor_1g.LEFT.at(wor_1g.LED_TOP)[1]
    L = lambda y: _line_x(RAIL_L, y) - sep
    R = lambda y: _line_x(RAIL_R, y) - sep
    cl = lambda y: _border(wor_1g.BORDER_LINE_L, y)
    cr = lambda y: _border(wor_1g.BORDER_LINE_R, y)
    yb2, yt2 = _y2p(yb), _y2p(yt)
    rock = _affine([(cl(yb), yb), (cl(yt), yt), (cr(yb), yb)], [(L(yb2), yb2), (L(yt2), yt2), (R(yb2), yb2)])
    sp = _affine([(cr(yb), yb), (cr(yt), yt), (cl(yb), yb)], [(R(yb2), yb2), (R(yt2), yt2), (L(yb2), yb2)])
    # the 1-player angle kept (user 2026-10-22: the sheared tubes looked more tilted than in quickplay; one angle in
    # every mode): each map = uniform scale (the rail map's size) about the border point at the LED span's middle,
    # which still lands on the rail
    # 2026-10-22 (user, close-up of the 2-player SP tube): the pieces must keep their angle RELATIVE TO THE RAIL, as
    # in quickplay (parallel to it); the 1-player screen angle left them visibly off the 2-player rails, which lean
    # less. So each map = uniform scale x rotation (the 1-player rail's direction onto this rail's; no shear) about
    # the border point at the LED span's middle.
    # The source line is the 1-player TUBE line (not its border), so the multiplayer tube ends up exactly parallel to
    # its rail (rotating border onto rail only gave ~1 deg; the user's close-up still showed the tube ~8 deg off).
    ym = (yb + yt) / 2
    tl_, tr_ = wor_1g.LEFT, wor_1g.RIGHT
    for m, anchor, src_line, dst_line in (
            (rock, (cl(ym), ym), (tl_.at(wor_1g.LED_BOTTOM), tl_.at(wor_1g.LED_TOP)), ((L(yb2), yb2), (L(yt2), yt2))),
            (sp, (cr(ym), ym), (tr_.at(wor_1g.LED_BOTTOM), tr_.at(wor_1g.LED_TOP)), ((R(yb2), yb2), (R(yt2), yt2)))):
        k = math.sqrt(abs(np.linalg.det(m[:, :2])))
        a2 = apply(m, anchor)
        th = (math.atan2(dst_line[1][1] - dst_line[0][1], dst_line[1][0] - dst_line[0][0])
              - math.atan2(src_line[1][1] - src_line[0][1], src_line[1][0] - src_line[0][0]))
        c, s = math.cos(th), math.sin(th)
        m[:, :2] = k * np.array([[c, -s], [s, c]])
        m[:, 2] = (a2[0] - (m[0, 0] * anchor[0] + m[0, 1] * anchor[1]), a2[1] - (m[1, 0] * anchor[0] + m[1, 1] * anchor[1]))
    # 2026-10-23 (user: the battle rock tube sat lower than quickplay's): the rock tube by the book, like every other
    # mode (tools/hw_geom.py): the 1-player outer border laid onto this highway's (battle highways = the DE's 2-highway
    # struct at -(x_offset_p2 + sep)); the slots keep the map above (user: their positions are right)
    import hw_geom as HG
    k, rot_deg, t = HG.similarity(2, -(HG.X_OFFSET_P2 + sep), 'left')
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    rock = np.array([[k * c, -k * s, t[0]], [k * s, k * c, t[1]]])
    return {'rock': rock, 'sp': sp}


def p2_dx(sep=SEP):
    """P2's highway is P1's mirrored: the x offset that moves P1's set onto P2's highway (left rail -> left rail)."""
    return (1280.0 - _line_x(RAIL_R, STRIKE_2P) + sep) - (_line_x(RAIL_L, STRIKE_2P) - sep)


def visor_affine(sep=SEP):
    """2x3 affine: visor art px -> P1 battle screen. The 1-player streak meter badge (nixie of wor_mult_1g: its arm's
    end on the SP tube's top) mapped onto the battle highway like the tubes (tube_maps 'sp')."""
    import desc_gen, preview_hud, wor_1g
    wor_1g.all_descs()
    e = next(c for c in desc_gen.ROOTS['wor_mult_1g_ghwor'].children if c.local_id == 'nixie')
    cal = preview_hud.GAME_CALIB['wor_mult_1g_ghwor']
    anchor = (e.pos[0] + wor_1g.G1[0] + cal[0], e.pos[1] + wor_1g.G1[1] + cal[1])     # the element's just = arm end
    se = wor_1g.BADGE_STICK_END
    m = tube_maps(sep)['sp']

    # upright like the streak meter's own badge (user 2026-10-22: the rail-mapped visors looked tilted): the arm's end
    # goes through the rail map, the art only scales by the map's size (no rail rotation / shear)
    a2 = apply(m, anchor)
    k = math.sqrt(abs(np.linalg.det(m[:, :2])))

    def f(q):
        v = wor_1g.rot(((q[0] - se[0]) * e.scale[0], (q[1] - se[1]) * e.scale[1]), e.rot)
        return (a2[0] + k * v[0], a2[1] + k * v[1])
    return _affine([(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [f((0.0, 0.0)), f((1.0, 0.0)), f((0.0, 1.0))])


def _visor_box(a0):
    """(centre, texture size) of the baked visor at scale 1: the art's corners through a0, SS texture px per unit."""
    pts = [apply(a0, q) for q in ((0, 0), (VISOR_ART[0], 0), (0, VISOR_ART[1]), VISOR_ART)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2), (_pow2((max(xs) - min(xs)) * SS + 6),
                                                                 _pow2((max(ys) - min(ys)) * SS + 6))


def visors(sep=SEP):
    """[(slot, element centre, element dims, glass centre, glass radius)] on P1 (screen): big at the bottom of the SP
    tube's place, mid and small above it, each one the scale-1 visor shrunk about its arm's end and slid along the
    rail (so every arm stays on the rail)."""
    import wor_1g
    a0 = visor_affine(sep)
    m = tube_maps(sep)['sp']
    a = apply(m, wor_1g.RIGHT.at(wor_1g.LED_BOTTOM))
    b = apply(m, wor_1g.RIGHT.at(wor_1g.LED_TOP))
    n = math.hypot(b[0] - a[0], b[1] - a[1])
    v = ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
    k = math.sqrt(abs(np.linalg.det(a0[:, :2])))         # screen units per art px
    arm = apply(a0, wor_1g.BADGE_STICK_END)
    ring = apply(a0, VISOR_RING[:2])
    (bc, (tw, th)) = _visor_box(a0)
    along = lambda p: (p[0] - a[0]) * v[0] + (p[1] - a[1]) * v[1]
    shrink = lambda p, s, tau: (arm[0] + s * (p[0] - arm[0]) + v[0] * tau, arm[1] + s * (p[1] - arm[1]) + v[1] * tau)
    out, t, prev = [], 0.0, None
    for key in ('big', 'mid', 'small'):
        s = VISOR_SCALES[key]
        rim = VISOR_RING[3] * k * s
        t = rim if prev is None else t + (prev + rim) * VISOR_GAP + VISOR_SPACE
        tau = t - along(shrink(ring, s, 0.0))              # slide so the glass centre lands at t along the rail
        out.append((key, shrink(bc, s, tau), (s * tw / SS, s * th / SS), shrink(ring, s, tau), VISOR_RING[2] * k * s))
        prev = rim
    nx, ny = -v[1], v[0]
    if nx > 0:                                          # the normal pointing at the highway (left of P1's right rail)
        nx, ny = -nx, -ny
    # 2026-10-23 (user: the slots' top aligned with the rock meter's top): the set slides along its rail until the
    # top slot's rim top is level with the rock tube's top end (the rm_base art's first row, RM_TOP_ROW)
    rock_top = rock_point(add_cal(wor_1g.LEFT.tex((wor_1g.TEX_CENTER[0] + wor_1g.TEX_CENTER[1] * RM_TOP_ROW,
                                                    RM_TOP_ROW))), 1)
    slot_top = min(g[1] - VISOR_RING[3] * k * VISOR_SCALES[key] for key, _, _, g, _ in out)
    tau = (rock_top[1] - slot_top) / v[1]
    slide = lambda p: (p[0] + v[0] * tau, p[1] + v[1] * tau)
    move = lambda p: slide((p[0] + nx * VISOR_INSET + VISOR_DX, p[1] + ny * VISOR_INSET))
    return [(key, move(c), dims, move(g), r) for key, c, dims, g, r in out]


RM_TOP_ROW = 4.0                        # the rock tube art's (rm_base) first opaque row


def add_cal(p):
    """A 1-player band meter point as drawn in game (preview_hud.GAME_CALIB, the band meter's (1, 3))."""
    return (p[0] + 1.0, p[1] + 3.0)


# ---- the rock tube, by the book (user 2026-10-23: battle must use quickplay's rock meter position, layering, shadows
# and effects): each player gets the band layouts' own rock tube desc (wor_mp.SIDE_NAMES[2], the 2-highway DE needle
# path), placed by the same map as in band (tools/wor_mp.placements: the 1-player outer border laid onto this
# highway's, then moved in by the border overlap lost to scaling). The DE's HUD_attach_widget_player_health drives its
# LEDs; WoR_HUD_battle_needles moves its needle stand-in on the DE's own 2-highway path (script 0x3205f550 doesn't run
# in battle), which the plugin maps onto the WoR LED stops exactly as in band. Parent: battlemode_container (screen
# origin, created at song start, destroyed by the DE afterwards), which draws its descs at (1, 3) like the DE's other
# containers (wor_mp.G_CAL).
BROCK_ID = {1: 'WoR_HUD_brock_p1', 2: 'WoR_HUD_brock_p2'}


def rock_instance(player):
    """(Pos, scale, rot) of player's rock tube desc in battlemode_container."""
    import hw_geom as HG
    import wor_mp as M
    k, rot, t = HG.similarity(2, HG.shifts(2)[player - 1], 'left')
    (px, py), k, rot = M.instance((k, rot, t), M.G_CAL, M.ROOT_CAL)
    return (px + (1.0 - k) * M.OVERLAP_1P['left'], py), k, rot


def rock_point(p, player):
    """Screen point of 1-player band meter point p (as drawn, add_cal) on player's battle rock tube."""
    import hw_geom as HG
    import wor_mp as M
    sim = HG.similarity(2, HG.shifts(2)[player - 1], 'left')
    x, y = HG.apply(sim, p)
    return x + (1.0 - sim[0]) * M.OVERLAP_1P['left'], y


def slots_on_tube(sep=SEP):
    """[(slot, glass centre, element dims, glass radius)] of the visors (the cards' slots), P1 screen."""
    return [(key, c, dims, r) for key, _, dims, c, r in visors(sep)]


def fly_start(sep=SEP):
    """Where a new card starts its slide (P1 screen): the strike line's centre x, at the big slot's height (user
    2026-10-29: just a horizontal move, the distance measured from the bottom slot's centre to the strike line)."""
    big = next(c for key, c, _, _ in slots_on_tube(sep) if key == 'big')
    centre = (_line_x(RAIL_L, STRIKE_2P) + _line_x(RAIL_R, STRIKE_2P)) / 2 - sep
    return (centre, big[1])


def arc_box(player):
    """(centre, dims) of the red arc for player: from the slide's start to the big slot (screen)."""
    big = next(c for key, c, _, _ in slots_on_tube() if key == 'big')
    a, b = (fly_start(), big) if player == 1 else (_p2(fly_start()), _p2(big))
    return ((a[0] + b[0]) / 2, a[1]), (abs(b[0] - a[0]), ARC_H)


def fly_script():
    """WoR_HUD_battlecard_fly (params id, to, mid, dims, player): the red arc centred on mid, dims from the slide's
    start to `to` (constants per player, arc_box), at 20 fps and faded at the end, and the card's slide along it; the
    card goes back under the highway (its slot's z) on arrival."""
    w = ARC_NAMES
    frames = ':a{' + ''.join(f'${n}$' for n in w) + ':a}'
    fly_frames = round(ARC_FLY * 20)
    fade_from = ARC_FRAMES - round(ARC_FADE * 20)
    return ('Script WoR_HUD_battlecard_fly [\n'
            '\t:i $FormatText$$checksumname$ = $WoR_bolt$%s("WoR_HUD_barc_p%p")$p$ = %GLOBAL%$player$\n'
            '\t:i if $ScreenElementExists$$id$ = %GLOBAL%$WoR_bolt$\n'
            '\t\t:i $DestroyScreenElement$$id$ = %GLOBAL%$WoR_bolt$\n'
            '\t:i endif\n'
            '\t:i if $ScreenElementExists$$id$ = $battlemode_container$\n'
            '\t\t:i $CreateScreenElement$:s{$type$ = $SpriteElement$$id$ = %GLOBAL%$WoR_bolt$$parent$ = $battlemode_container$'
            f'$texture$ = ${w[0]}$$Pos$ = %GLOBAL%$mid$$dims$ = %GLOBAL%$dims$$just$ = :a{{$center$$center$:a}}'
            f'$rgba$ = :a{{%i(255)%i(255)%i(255)%i(255):a}}$alpha$ = %i(1)$z_priority$ = %f({FLY_Z - 0.1:.1f})$Blend$ = $add$:s}}\n'
            '\t:i endif\n'
            '\t:i if $ScreenElementExists$$id$ = %GLOBAL%$id$\n'
            f'\t\t:i $LegacyDoScreenElementMorph$:s{{$id$ = %GLOBAL%$id$$Pos$ = %GLOBAL%$to$$time$ = %f({ARC_FLY:.2f}):s}}\n'
            '\t:i endif\n'
            f'\t:i $WoR_frames$ = {frames}\n'
            '\t:i $WoR_f$ = %i(0)\n'
            '\t:i while \n'
            '\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$WoR_bolt$\n'
            '\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$WoR_bolt$$texture$ = (%GLOBAL%$WoR_frames$:a{%GLOBAL%$WoR_f$:a})\n'
            f'\t\t\t:i if (%GLOBAL%$WoR_f$ = %i({fade_from}))\n'
            f'\t\t\t\t:i $LegacyDoScreenElementMorph$:s{{$id$ = %GLOBAL%$WoR_bolt$$alpha$ = %i(0)$time$ = %f({ARC_FADE:.2f}):s}}\n'
            '\t\t\t:i endif\n'
            '\t\t:i endif\n'
            f'\t\t:i if (%GLOBAL%$WoR_f$ = %i({fly_frames}))\n'
            '\t\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$id$\n'
            f'\t\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$id$$z_priority$ = %f({CARD_Z["big"]})\n'
            '\t\t\t:i endif\n'
            '\t\t:i endif\n'
            '\t\t:i $wait$%f(0.05)$seconds$\n'
            '\t\t:i %GLOBAL%$WoR_f$ = (%GLOBAL%$WoR_f$ + %i(1))\n'
            f'\t:i loop_to %i({ARC_FRAMES})\n'
            '\t:i if $ScreenElementExists$$id$ = %GLOBAL%$WoR_bolt$\n'
            '\t\t:i $DestroyScreenElement$$id$ = %GLOBAL%$WoR_bolt$\n'
            '\t:i endif\n'
            '\t:i endfunction\n]\n\n')


def card_sizes():
    """Big card size (screen) and the medium / small scales so each card fills its ring."""
    inner = {key: r_in for key, _, _, r_in in slots_on_tube()}
    big = 2 * inner['big'] * CARD_FILL
    return big, {'medium_scale': 2 * inner['mid'] * CARD_FILL / big, 'small_scale': 2 * inner['small'] * CARD_FILL / big}


# ---- the rock tube
def _tube_cut():
    """The 1-player tube cut (canvas polygon around the LED span)."""
    import wor_1g
    a, b = np.array(wor_1g.LEFT.at(wor_1g.LED_BOTTOM)), np.array(wor_1g.LEFT.at(wor_1g.LED_TOP))
    v = (b - a) / np.hypot(*(b - a))
    n = np.array((-v[1], v[0]))
    p0, p1 = a - v * TUBE_EXT[0], b + v * TUBE_EXT[1]
    return [tuple(p0 + n * TUBE_HALF_W), tuple(p1 + n * TUBE_HALF_W), tuple(p1 - n * TUBE_HALF_W), tuple(p0 - n * TUBE_HALF_W)]


def _pow2(n):
    return 1 << max(0, int(math.ceil(n)) - 1).bit_length()


def _box(points, margin=2.0):
    """A texture box (screen centre, texture size in px) holding the screen points, power-of-two."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    w, h = (max(xs) - min(xs) + 2 * margin) * SS, (max(ys) - min(ys) + 2 * margin) * SS
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2), (_pow2(w), _pow2(h))


def _cut_box():
    m = tube_maps()['rock']
    return _box([apply(m, p) for p in _tube_cut()])


_TUBE_BOX = {}


def tube_box(textures_dir=None):
    """The tube textures' box (screen centre, texture px): power-of-two around the rendered tube (the polygon box
    was twice as large: 4 x 512 px pushed the theme pak past 4 MiB)."""
    if 'box' not in _TUBE_BOX:
        textures(textures_dir)
    return _TUBE_BOX['box']


def needle_stops():
    """Screen centre of the battle needle at health 0 / 0.667 / 1.333 / 2 (P1): the 1-player needle's centre on the
    WoR LED stops (side meter desc + its game calibration), mapped like the tube."""
    import wor_1g
    m = tube_maps()['rock']
    return [(x + NEEDLE_DX, y) for x, y in (apply(m, (p[0] + SIDE_METER_CALIB[0], p[1] + SIDE_METER_CALIB[1]))
                                            for p in (wor_1g.LEFT.at(h) for h in wor_1g.NEEDLE_STOPS))]


NEEDLE_DX = -1.5            # screen px: user 2026-10-23, the white needle a little left on every multiplayer highway


NEEDLE_BOX = 34.0                       # screen size of the needle texture box (the 1-player needle is 40 canvas)


def _render_1p(textures_dir, keep=None, vals=None, health=1.0):
    """The 1-player HUD (game calibration) at SS px per canvas unit, only the `keep` elements (local ids) if given."""
    import copy
    from PIL import Image
    import preview_hud
    old = preview_hud.PREVIEW
    preview_hud.PREVIEW = textures_dir
    try:
        roots = copy.deepcopy(preview_hud.hud_roots(game=True))

        def walk(e):
            if keep is not None and e.kind != 'ContainerElement' and e.local_id not in keep:
                e.hidden = True
            for c in e.children:
                walk(c)
        for _, r in roots:
            walk(r)
        st = preview_hud.state(health, 0.0, 1)
        st.update(vals or {})
        preview_hud.GAME_TEXT['on'] = True
        lay = Image.new('RGBA', (int(1280 * SS), int(720 * SS)), (0, 0, 0, 0))
        preview_hud.draw(lay, roots, (0.0, 0.0), SS, st, additive=False)
        return lay
    finally:
        preview_hud.PREVIEW = old


def _warp_crop(layer, m, box, cut=None):
    """The SS layer mapped by m (canvas affine), cut to `cut` (canvas polygon, before mapping), cropped to box."""
    import cv2
    from PIL import Image, ImageDraw
    if cut is not None:
        mask = Image.new('L', layer.size, 0)
        ImageDraw.Draw(mask).polygon([(x * SS, y * SS) for x, y in cut], fill=255)
        a = np.array(layer)
        a[..., 3] = (a[..., 3].astype(np.uint16) * np.array(mask) // 255).astype(np.uint8)
        layer = Image.fromarray(a)
    ms = m.copy()
    ms[:, 2] *= SS
    (cx, cy), (w, h) = box
    ms[0, 2] -= cx * SS - w / 2           # straight into the texture box
    ms[1, 2] -= cy * SS - h / 2
    a = np.array(layer)
    rgb = a[..., :3].astype(np.float32) * (a[..., 3:4] / 255.0)         # premultiplied: no dark fringes
    pm = np.dstack([rgb, a[..., 3:4].astype(np.float32)])
    w_ = cv2.warpAffine(pm, ms, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = w_[..., 3:4]
    col = np.where(al > 0, w_[..., :3] / np.maximum(al, 1e-6) * 255.0, 0)
    return Image.fromarray(np.dstack([col, al]).clip(0, 255).astype(np.uint8))


def _additive(im):
    """An 'Add'-blended sprite as a plain alpha one (hud_2d sprites blend normally): its brightness becomes alpha, so
    black is see-through like on the 1-player HUD."""
    from PIL import Image
    a = np.array(im).astype(np.float32)
    peak = a[..., :3].max(axis=2, keepdims=True)
    rgb = np.where(peak > 0, a[..., :3] * 255.0 / np.maximum(peak, 1e-6), 0)
    return Image.fromarray(np.dstack([rgb, a[..., 3:4] * peak / 255.0]).clip(0, 255).astype(np.uint8))


def textures(textures_dir=None):
    """{our texture name: PIL image} for the pak. textures_dir: the built 1-player textures (preview_hud names)."""
    from PIL import Image
    textures_dir = textures_dir or os.path.join(paths.REPO, 'build', 'preview')
    out = {}
    # the visor at scale 1, baked in its battle orientation (hud_2d elements don't rotate): each output texel's centre
    # taken back through the art -> screen affine
    a0 = visor_affine()
    (bc, (tw, th)) = _visor_box(a0)
    inv = np.linalg.inv(np.vstack([a0, (0.0, 0.0, 1.0)]))
    o = np.array([[1.0 / SS, 0.0, bc[0] - tw / (2 * SS) + 0.5 / SS], [0.0, 1.0 / SS, bc[1] - th / (2 * SS) + 0.5 / SS],
                  [0.0, 0.0, 1.0]])
    t = inv @ o                                            # texture px -> art px
    art = Image.open(os.path.join(textures_dir, VISOR_SRC + '.png')).convert('RGBA')
    # the ring and its short arm only (user 2026-10-22): the long stick glued to the arm, which ran behind the stacked
    # rings, is cut off (the art kept inside the rim and the arm's box)
    ya, xa = np.mgrid[0:art.height, 0:art.width]
    d = np.hypot(xa - VISOR_RING[0], ya - VISOR_RING[1])
    x0, y0, x1, y1 = VISOR_ARM
    keep = np.maximum(np.clip(VISOR_RING[3] + 1.0 - d, 0.0, 1.0),
                      ((xa >= x0) & (xa <= x1) & (ya >= y0) & (ya <= y1)).astype(float))
    aa = np.array(art)
    aa[..., 3] = (aa[..., 3] * keep).astype(np.uint8)
    art = Image.fromarray(aa)
    out[VISOR_TEX] = art.transform((tw, th), Image.AFFINE, tuple(t[:2].ravel()), resample=Image.BICUBIC)
    # rock tube: the body (no LEDs, no needle), each LED alone, the needle alone (LEDs and needle are additive there)
    m = tube_maps()['rock']
    cut = _tube_cut()
    off = {k: {'alpha': 0.0} for k in ('red_light', 'yellow_light', 'green_light', 'side_meter_needle', 'side_meter_red_ON')}
    big = _cut_box()
    body = _warp_crop(_render_1p(textures_dir, vals=off), m, big, cut)
    x0, y0, x1, y1 = body.getbbox()                     # the LEDs lie inside the body
    (bx, by), (bw, bh) = big
    cx, cy = bx + ((x0 + x1) / 2 - bw / 2) / SS, by + ((y0 + y1) / 2 - bh / 2) / SS
    box = ((cx, cy), (_pow2(x1 - x0 + 8), _pow2(y1 - y0 + 8)))
    _TUBE_BOX['box'] = box
    out[TUBE_TEX['body']] = _warp_crop(_render_1p(textures_dir, vals=off), m, box, cut)
    for c in ('red', 'yellow', 'green'):
        lay = _render_1p(textures_dir, keep={f'{c}_light'}, vals={f'{c}_light': {'alpha': 1.0}})
        out[TUBE_TEX[c]] = _additive(_warp_crop(lay, m, box, cut))          # 'Add' on the 1-player HUD
    # the needle at health 1 (its stop between the 2nd and 3rd knot), cropped around its centre
    import wor_1g
    h1 = (wor_1g.NEEDLE_STOPS[1] + wor_1g.NEEDLE_STOPS[2]) / 2
    c1 = wor_1g.LEFT.at(h1)
    c1 = (c1[0] + SIDE_METER_CALIB[0], c1[1] + SIDE_METER_CALIB[1])
    lay = _render_1p(textures_dir, keep={'side_meter_needle'}, health=1.0)
    nb = (apply(m, c1), (_pow2(NEEDLE_BOX * SS),) * 2)
    out[NEEDLE_TEX] = _additive(_warp_crop(lay, m, nb))                     # 'Add' on the 1-player HUD
    out[GAMERTAG_TEX] = Image.open(WOR_GAMERTAG).convert('RGBA')
    return out


def sources():
    s = {VISOR_TEX: {'src': VISOR_SRC + ' (the 1-player streak meter visor, mapped onto the battle rail)',
                     'battle_tube': True}}
    s[GAMERTAG_TEX] = {'src': WOR_GAMERTAG}
    import wor_1g
    tube = {'body': 'WoR_HUD_rm_base', 'red': 'WoR_HUD_rm_red', 'yellow': 'WoR_HUD_rm_yellow', 'green': 'WoR_HUD_rm_green'}
    for k, name in TUBE_TEX.items():
        s[name] = {'src': wor_1g.TEXTURES.get(tube[k], tube[k]), 'battle_tube': True}
    s[NEEDLE_TEX] = {'src': wor_1g.TEXTURES['WoR_HUD_needle_glow'], 'battle_tube': True}
    for v in s.values():
        v.setdefault('box', None)
        v.setdefault('flip', False)
    return s


# ---- layout struct
def _local(p, player):
    rx, ry = ROCK_POS[player]
    return ((p[0] - rx * SCALE) / SCALE, (p[1] - ry * SCALE) / SCALE)


def _p2(p):
    return (p[0] + p2_dx(), p[1])


def _vec(name, v, ind):
    return f'{ind}StructFloatX2 {name}\n{ind}{{\n{ind}\tFloats [{v[0]:.5f}, {v[1]:.5f}]\n{ind}}}\n'


def _elem(eid, tex, screen_pos, screen_dims, z, alpha=None, rgba=None):
    """A sprite in the rock container, centred on screen_pos (hud_2d just: -1..1, 0 = centre); P2 = P1 translated."""
    ind = '\t\t\t\t\t'
    t = (f'\t\t\t\tStructHeader\n\t\t\t\t{{\n{ind}StructQBKey element_id = {eid}\n'
         f'{ind}StructQBKey element_parent = HUD2D_rock_container\n{ind}StructQBKey texture = {tex}\n')
    t += _vec('pos_off', _local(screen_pos, 1), ind)
    t += _vec('pos_off_p2', _local(_p2(screen_pos), 2), ind)
    t += _vec('dims', (screen_dims[0] / SCALE, screen_dims[1] / SCALE), ind)
    t += f'{ind}StructFloat zoff = {z}\n'
    t += f'{ind}StructArray just\n{ind}{{\n{ind}\tArrayFloat\n{ind}\t[\n{ind}\t\t0.000000\n{ind}\t\t0.000000\n{ind}\t]\n{ind}}}\n'
    if alpha is not None:
        t += f'{ind}StructInt alpha = {alpha}\n'
    if rgba is not None:
        t += f'{ind}StructArray rgba\n{ind}{{\n{ind}\tArrayInteger\n{ind}\t[\n' + ''.join(f'{ind}\t\t{c}\n' for c in rgba) + f'{ind}\t]\n{ind}}}\n'
    return t + '\t\t\t\t}\n'


def card_offsets():
    """guitar_battle's card offsets for our slots: card 1 = rock_pos + off, cards 2 / 3 relative to card 1."""
    c = {key: centre for key, centre, _, _ in slots_on_tube()}
    out = {}
    for p in (1, 2):
        big, mid, small = (c[k] if p == 1 else _p2(c[k]) for k in ('big', 'mid', 'small'))
        rx, ry = ROCK_POS[p]
        out[f'card_1_off_p{p}'] = (big[0] - rx, big[1] - ry)
        out[f'card_2_off_p{p}'] = (mid[0] - big[0], mid[1] - big[1])
        out[f'card_3_off_p{p}'] = (small[0] - big[0], small[1] - big[1])
    return out


def plugin_cards():
    """For the plugin, per slot (P1 big / mid / small, then P2): where guitar_battle sends a card with the stock
    offsets (screen), our slot centre (screen) and the card size there. Test 2026-10-21: the wrapper's $change$ of
    battle_hud_2d_elements' card offsets didn't reach the cards (they landed on the stock spots), so the plugin moves
    each card's morph target from the stock spot to ours."""
    slots = slots_on_tube()
    out = []
    for p in (1, 2):
        rx, ry = ROCK_POS[p]
        c1 = STOCK_CARD_OFFS[f'card_1_off_p{p}']
        big = (rx + c1[0], ry + c1[1])
        stock = [big] + [(big[0] + STOCK_CARD_OFFS[f'card_{n}_off_p{p}'][0], big[1] + STOCK_CARD_OFFS[f'card_{n}_off_p{p}'][1])
                         for n in (2, 3)]
        for (key, c, _, r_in), s in zip(slots, stock):
            out.append((s, c if p == 1 else _p2(c), 2 * r_in * CARD_FILL))
    return out


def plugin_needle():
    """For the plugin: the needle's local offsets (layout units) from the stand-in (at the health-0 stop) per stop."""
    st = needle_stops()
    return [((x - st[0][0]) / SCALE, (y - st[0][1]) / SCALE) for x, y in st]


def layout_struct():
    hdr = '\t\t'
    slots = slots_on_tube()
    centre = {key: c for key, c, _, _ in slots}
    t = f'SectionStruct {NAME}\n{{\n\tStructHeader\n\t{{\n'
    t += _vec('offset4by3_rock', (0, 0), hdr) + _vec('offset4by3_score', (0, 0), hdr)
    t += _vec('offscreen_rock_pos_p1', OFFSCREEN[1], hdr) + _vec('offscreen_rock_pos_p2', OFFSCREEN[2], hdr)
    offs = card_offsets()
    for p in (1, 2):
        t += _vec(f'rock_pos_p{p}', ROCK_POS[p], hdr)
        for n in (1, 2, 3):
            t += _vec(f'card_{n}_off_p{p}', offs[f'card_{n}_off_p{p}'], hdr)
        for n, key in ((2, 'mid'), (3, 'small')):
            pos = centre[key] if p == 1 else _p2(centre[key])
            t += _vec(f'card_default_{n}_p{p}', _local(pos, p), hdr)
    t += f'{hdr}StructFloat Scale = {SCALE}\n{hdr}StructInt z = {HUD_Z}\n'
    for name, v in (('buttons_p2_offset', (510.0, 0.0)), ('string_offset', (200.0, 0.0)),
                    ('green_button_pos', (185.0, 620.0)), ('lefty_green_button_pos', (585.0, 620.0)),
                    ('attack_ready_text_pos_p1', (347.0, 240.0)), ('attack_ready_text_pos_p2', (941.0, 240.0)),
                    ('whammy_bottom_bar_pos_p1', (640.0, 643.0)), ('whammy_bottom_bar_pos_p2', (635.0, 643.0)),
                    ('offscreen_gamertag_pos', (0.0, -400.0)), ('final_gamertag_pos', (0.0, 0.0))):
        t += _vec(name, v, hdr)
    t += f'{hdr}StructArray elements\n{hdr}{{\n\t\t\tArrayStruct\n\t\t\t[\n'
    t += ('\t\t\t\tStructHeader\n\t\t\t\t{\n\t\t\t\t\tStructQBKey parent_container\n'
          '\t\t\t\t\tStructQBKey element_id = HUD2D_rock_container\n\t\t\t\t\tStructQBKey pos_type = offscreen_rock_pos\n\t\t\t\t}\n')
    # health: the rock tube body and one LED per zone. The DE (0x465ab0) switches HUD2D_rock_lights_red / _yellow /
    # _green on below 2/3, 2/3..4/3 and above 4/3 health, like the 1-player LEDs; BG_green / BG_yellow are GH3's dial
    # crossfade layers over an always-on BG_red (test 2026-10-21: as LEDs they lit all three at once), so blank here.
    # 2026-10-23: the rock tube is the band desc now (rock_instance, WoR_HUD_battle_rock); the DE-driven ids stay (it
    # switches their alphas and turns the needle stand-in), blank. Our battle needle stays too, invisible: the plugin
    # still finds it (dims kBNeedleDims, texture WoR_HUD_bneedle) and reads the DE's angle there, which keeps
    # g_battle_seen (score separators while the battle HUD is up) alive
    (tc, (tw, th)) = tube_box()
    tube = (tw / SS, th / SS)
    t += _elem('HUD2D_rock_body', BLANK, tc, (4.0, 4.0), 13, alpha=0)
    for c, z in (('red', 14), ('yellow', 15), ('green', 16)):
        t += _elem(f'HUD2D_rock_lights_{c}', BLANK, tc, (4.0, 4.0), z, alpha=0)
    for eid in ('HUD2D_rock_BG_green', 'HUD2D_rock_BG_red', 'HUD2D_rock_BG_yellow', 'HUD2D_rock_lights_all'):
        t += _elem(eid, BLANK, tc, (4.0, 4.0), 17, alpha=0)
    # needle: the DE turns the stand-in (blank, at the health-0 stop); the plugin slides ours up the tube from it
    st = needle_stops()
    nd = _pow2(NEEDLE_BOX * SS) / SS
    t += _elem('HUD2D_rock_needle', BLANK, st[0], (4.0, 4.0), 18.4)
    # (transparent by its colour, not alpha 0: an alpha-0 element may not get its per-frame update)
    t += _elem('WoR_HUD_battle_needle', NEEDLE_TEX, ((st[1][0] + st[2][0]) / 2, (st[1][1] + st[2][1]) / 2), (nd, nd), 18.5,
               rgba=(255, 255, 255, 0))
    # attack slots: the three visors under the cards (z 19); the DE's default icon of an empty slot stays blank (the
    # visor's own dark glass shows)
    for key, ec, dims, c, r_in in visors():
        t += _elem(f'WoR_HUD_bvisor_{key}', VISOR_TEX, ec, dims, VISOR_Z[key])
    for n, (key, c, dims, r_in) in enumerate(slots, 1):
        t += _elem(f'HUD2D_battle_default_icon2_{n}', BLANK, c, (2 * r_in, 2 * r_in), 18.9)
    t += '\t\t\t]\n\t\t}\n\t}\n}'
    return t


def gamertag_desc(vh_desc):
    """The DE's (Van Halen theme) gamertag desc as uidesc_hud_gamertag_ghwor: WoR's gamertag bar as the plate,
    dark name text on it (WoR's competitive plates); the DE still tints the bar with the team colour."""
    name = 'uidesc_' + GAMERTAG
    d = vh_desc.replace('SectionStruct fee8b1c6', f'SectionStruct {name}', 1).replace('StructQBKey name = fee8b1c6', f'StructQBKey name = {name}', 1)
    assert d.count('StructQBKey texture = 0x529e2bcf') == 1, 'gamertag desc changed'
    d = d.replace('StructQBKey texture = 0x529e2bcf', f'StructQBKey texture = {GAMERTAG_TEX}', 1)
    i = d.index(f'StructQBKey texture = {GAMERTAG_TEX}')
    j = d.index('StructFloat alpha = 0.75', i)
    d = d[:j] + 'StructFloat alpha = 1.00' + d[j + len('StructFloat alpha = 0.75'):]
    k = d.index('StructQBKey local_id = gamertag_name')
    m = d.index('StructArray rgba', k)
    e = d.index(']', m)
    d = d[:m] + 'StructArray rgba\n{\nArrayInteger\n[\n24\n24\n28\n255\n' + d[e:]
    return d[:d.index('SectionStruct 0x18689997')].rstrip() if 'SectionStruct 0x18689997' in d else d


def scripts():
    def changes(offs, scales):
        return (''.join(f'\t\t:i $change$$structurename$ = $battle_hud_2d_elements$${k}$ = %vec2({v[0]:.1f},{v[1]:.1f})\n'
                        for k, v in offs.items())
                + ''.join(f'\t\t:i $change$${k}$ = %f({v:.4f})\n' for k, v in scales.items()))
    big, scales = card_sizes()
    is_ours = f'$[4c1beb8d]$$value$ = ${FLAG}$'
    # 2026-10-23: the attack cards by script. guitar_battle creates each card 64x64 (z battle_hud_2d_elements.z + 19)
    # and morphs it to rock_pos + card_*_off (the newest one: the big slot, scale 1; older ones: medium_scale /
    # small_scale) in update_battlecards_add / _remove; the plugin's card matching (1.32-1.48) never saw a card in the
    # DE (logs of 2026-10-23), so the cards stayed 64 px. Our wrappers run the DE's script, then put every card
    # (current_battlecard_pN, index n-1 = the newest) into its slot: our size (the big card's; the scale gives the
    # others), position, scale and draw priority (CARD_Z: just above its own slot, the bottom pair over the middle).
    keys = ('big', 'mid', 'small')
    centres = {key: c for key, c, _, _ in slots_on_tube()}
    starts = {1: fly_start(), 2: _p2(fly_start())}
    vec = lambda pts: ':a{' + ''.join(f'%vec2({x:.2f},{y:.2f})' for x, y in pts) + ':a}'

    def arc_locals(p):
        (mx, my), (dw, dh) = arc_box(p)
        return (f'\t\t:i %GLOBAL%$WoR_from$ = %vec2({starts[p][0]:.2f},{starts[p][1]:.2f})\n'
                f'\t\t:i %GLOBAL%$WoR_mid$ = %vec2({mx:.2f},{my:.2f})\n'
                f'\t\t:i %GLOBAL%$WoR_adims$ = %vec2({dw:.2f},{dh:.2f})\n')
    flt = lambda vs: ':a{' + ''.join(f'%f({v:.4f})' for v in vs) + ':a}'
    sizes = [1.0, scales['medium_scale'], scales['small_scale']]
    place = (
        'Script WoR_HUD_battlecards_place [\n'
        '\t:i if (~%GLOBAL%$player_status$->$player$ = %i(1))\n'
        '\t\t:i %GLOBAL%$WoR_cards$ = (~$current_battlecard_p1$)\n'
        f'\t\t:i %GLOBAL%$WoR_slots$ = {vec([centres[k] for k in keys])}\n'
        + arc_locals(1) +
        '\t:i else \n'
        '\t\t:i %GLOBAL%$WoR_cards$ = (~$current_battlecard_p2$)\n'
        f'\t\t:i %GLOBAL%$WoR_slots$ = {vec([_p2(centres[k]) for k in keys])}\n'
        + arc_locals(2) +
        '\t:i endif\n'
        f'\t:i %GLOBAL%$WoR_scales$ = {flt(sizes)}\n'
        f'\t:i %GLOBAL%$WoR_z$ = {flt([CARD_Z[k] for k in keys])}\n'
        '\t:i %GLOBAL%$WoR_n$ = (~%GLOBAL%$player_status$->$current_num_powerups$)\n'
        '\t:i %GLOBAL%$WoR_i$ = %i(0)\n'
        '\t:i while \n'
        '\t\t:i if (%GLOBAL%$WoR_i$ < %GLOBAL%$WoR_n$)\n'
        '\t\t\t:i %GLOBAL%$WoR_slot$ = ((%GLOBAL%$WoR_n$ - %i(1)) - %GLOBAL%$WoR_i$)\n'
        '\t\t\t:i if (%GLOBAL%$WoR_slot$ < %i(3))\n'
        '\t\t\t\t:i %GLOBAL%$WoR_id$ = (%GLOBAL%$WoR_cards$:a{%GLOBAL%$WoR_i$:a})\n'
        '\t\t\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$WoR_id$\n'
        f'\t\t\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$WoR_id$$dims$ = %vec2({big:.2f},{big:.2f})'
        '$z_priority$ = (%GLOBAL%$WoR_z$:a{%GLOBAL%$WoR_slot$:a})\n'
        # 2026-10-26 (user: the collect animation must stay, ending in our slots): the newest card (the big slot) is
        # flying in from its note button on battlemode_ready's own 0.3 s morph, which already aims at our big slot
        # (battle_hud_2d_elements is our layout); a second morph here restarted that flight. Only the older cards move.
        '\t\t\t\t\t:i if (%GLOBAL%$WoR_slot$ > %i(0))\n'
        '\t\t\t\t\t\t:i $LegacyDoScreenElementMorph$:s{$id$ = %GLOBAL%$WoR_id$'
        '$Pos$ = (%GLOBAL%$WoR_slots$:a{%GLOBAL%$WoR_slot$:a})$Scale$ = (%GLOBAL%$WoR_scales$:a{%GLOBAL%$WoR_slot$:a})'
        '$alpha$ = %i(1)$time$ = %f(0.3):s}\n'
        # 2026-10-29 (user: still no animation into the slots): a NEW card (the add wrapper sets WoR_HUD_bfly) jumps to
        # the strike line's centre (a 0-time morph replaces the DE's own flight) and WoR_HUD_battlecard_fly slides it
        # into the big slot along the red arc
        '\t\t\t\t\t:i elseif (~$WoR_HUD_bfly$ = %i(1))\n'
        '\t\t\t\t\t\t:i $LegacyDoScreenElementMorph$:s{$id$ = %GLOBAL%$WoR_id$$Pos$ = %GLOBAL%$WoR_from$'
        '$Scale$ = %f(1.0)$alpha$ = %i(1)$time$ = %i(0):s}\n'
        f'\t\t\t\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$WoR_id$$z_priority$ = %f({FLY_Z:.1f})\n'
        '\t\t\t\t\t\t:i $spawnscriptnow$$WoR_HUD_battlecard_fly$$params$ = :s{$id$ = %GLOBAL%$WoR_id$'
        '$mid$ = %GLOBAL%$WoR_mid$$dims$ = %GLOBAL%$WoR_adims$$to$ = (%GLOBAL%$WoR_slots$:a{%i(0):a})'
        '$player$ = (~%GLOBAL%$player_status$->$player$):s}\n'
        '\t\t\t\t\t:i endif\n'
        '\t\t\t\t:i endif\n'
        '\t\t\t:i endif\n'
        '\t\t:i endif\n'
        '\t\t:i %GLOBAL%$WoR_i$ = (%GLOBAL%$WoR_i$ + %i(1))\n'
        '\t:i loop_to %i(3)\n'
        '\t:i $change$$WoR_HUD_bfly$ = %i(0)\n'
        '\t:i endfunction\n]\n\n'
        'SectionInteger WoR_HUD_bfly 0\n\n')
    place += fly_script()
    # 2026-10-23 (user test of 1.50: a new card flew up, then sideways into the big slot): guitar_battle reads every card
    # target from the global battle_hud_2d_elements (rock_pos + card_*_off, also attack_ready_text_pos and z), never
    # from the theme's layout, and the per-field $change$ of its vec2 offsets never took (test 2026-10-21). So each
    # new card first morphed towards the stock big-slot spot (up), then our battlecards_place morphed it to ours
    # (sideways). With this theme the whole global becomes a copy of our layout struct (it carries every field the DE
    # reads, with our card offsets), so the DE's own morphs already aim at our slots; the stock struct is saved once and
    # put back with any other theme (other themes' HUD falls back to that global as its layout).
    place += ('Script WoR_HUD_battle_globals [\n'
              '\t:i if (~$WoR_HUD_battle_saved$ = %i(0))\n'
              '\t\t:i $change$$WoR_HUD_battle_stock$ = (~$battle_hud_2d_elements$)\n'
              '\t\t:i $change$$WoR_HUD_battle_saved$ = %i(1)\n'
              '\t:i endif\n'
              f'\t:i if {is_ours}\n'
              f'\t\t:i $change$$battle_hud_2d_elements$ = (~${NAME}$)\n'
              '\t:i else \n'
              '\t\t:i $change$$battle_hud_2d_elements$ = (~$WoR_HUD_battle_stock$)\n'
              '\t:i endif\n'
              '\t:i endfunction\n]\n\n'
              'SectionInteger WoR_HUD_battle_saved 0\n\n'
              'SectionStruct WoR_HUD_battle_stock\n{\n\tStructHeader\n\t{\n\t\tStructInt WoR_HUD_placeholder = 0\n\t}\n}\n\n')
    for name in ('update_battlecards_add', 'update_battlecards_remove'):
        fly = '\t\t:i $change$$WoR_HUD_bfly$ = %i(1)\n' if name.endswith('_add') else ''
        place += (f'Script WoR_HUD_{name} [\n'
                  '\t:i $WoR_HUD_battle_globals$ isNull\n'
                  f'\t:i $WoR_HUD_{name}_orig$ isNull\n'
                  f'\t:i if {is_ours}\n'
                  + fly +
                  '\t\t:i $WoR_HUD_battlecards_place$ isNull\n'
                  '\t:i endif\n'
                  '\t:i endfunction\n]\n\n'
                  f'Script WoR_HUD_{name}_orig [\n'
                  f'\t:i $printf$%s("WoR_HUD: {name} placeholder ran, plugin swap missing")\n'
                  '\t:i endfunction\n]\n\n')
    place += rock_scripts()
    return place + ('Script WoR_HUD_create_battle_alert_frames [\n'
            f'\t:i if {is_ours}\n'
            + changes(card_offsets(), scales) +
            '\t\t:i $printf$%s("WoR_HUD: battle attack cards moved into the WoR slots")\n'
            '\t:i else \n'
            + changes(STOCK_CARD_OFFS, STOCK_CARD_SCALES) +
            '\t:i endif\n'
            '\t:i $WoR_HUD_battle_globals$ isNull\n'
            '\t:i $WoR_HUD_create_battle_alert_frames_orig$ isNull\n'
            + wor_modes.battle_alerts_off() +          # no attack names / alert cards above the highway
            '\t:i endfunction\n]\n\n'
            # placeholder: the plugin moves the DE script's data here
            'Script WoR_HUD_create_battle_alert_frames_orig [\n'
            '\t:i $printf$%s("WoR_HUD: battle alert frames placeholder ran, plugin swap missing")\n'
            '\t:i endfunction\n]\n\n'
            # highways SEP further apart in every 2-highway layout with this theme (battle, face-off, pro face-off,
            # 2-player co-op / quickplay; user: carry the battle spacing over): the returned Pos (canvas x,
            # -+x_offset_p2) moved out by SEP per player. (2026-10-21: changing the global x_offset_p2 instead added SEP
            # on every call.)
            # 2026-10-22: the DE places battle prompts / alerts at the gems' 2D positions + x_offset_p2 itself (user test:
            # the PUSH prompt off its highway, half behind it), so x_offset_p2 itself is set to its stock value + SEP with
            # this theme (stock otherwise); the stock value is saved on the first call (the 2026-10-21 attempt added SEP
            # on every call). The highways, prompts and alerts then move together.
            'Script WoR_HUD_get_highway_pos_and_scale [\n'
            '\t:i if (~$WoR_HUD_xoff_saved$ = %i(0))\n'
            '\t\t:i $change$$WoR_HUD_xoff_stock$ = (~$x_offset_p2$)\n'
            '\t\t:i $change$$WoR_HUD_xoff_saved$ = %i(1)\n'
            '\t\t:i $change$$WoR_HUD_xoff3_stock$ = (~$x_offset_p3$)\n'
            '\t:i endif\n'
            f'\t:i if {is_ours}\n'
            f'\t\t:i $change$$x_offset_p2$ = (~$WoR_HUD_xoff_stock$ + %f({SEP:.1f}))\n'
            # 3 instrument highways (drum centred, the guitars at -+x_offset_p3 x 1.8): the outer two move out so
            # the thick WoR borders meet instead of overlapping (user 2026-10-22)
            f'\t\t:i $change$$x_offset_p3$ = (~$WoR_HUD_xoff3_stock$ + %f({SEP3:.1f}))\n'
            '\t:i else \n'
            '\t\t:i $change$$x_offset_p2$ = (~$WoR_HUD_xoff_stock$)\n'
            '\t\t:i $change$$x_offset_p3$ = (~$WoR_HUD_xoff3_stock$)\n'
            '\t:i endif\n'
            '\t:i $WoR_HUD_get_highway_pos_and_scale_orig$ isNull\n'
            '\t:i return$Pos$ = %GLOBAL%$Pos$$Scale$ = %GLOBAL%$Scale$\n'
            '\t:i endfunction\n]\n\n'
            'SectionFloat WoR_HUD_xoff_stock 0.00000\n\n'
            'SectionInteger WoR_HUD_xoff_saved 0\n\n'
            'SectionFloat WoR_HUD_xoff3_stock 0.00000\n\n'
            'Script WoR_HUD_get_highway_pos_and_scale_orig [\n'
            '\t:i $printf$%s("WoR_HUD: highway pos placeholder ran, plugin swap missing")\n'
            '\t:i return$Pos$ = %vec2(0.0,0.0)$Scale$ = %vec2(1.0,1.0)\n'
            '\t:i endfunction\n]\n\n'
            # 2026-10-22 (user item 0): the battle pieces fade in like every other mode's HUD. The other modes fade
            # hud_root (created at alpha 0, faded to 1 over 0.25 s by move_2d_elements_to_default after its intro
            # loop); battle's layout has no desc_interface, so no hud_root, and HUD_2D_Container<p> sits at full alpha.
            # setup_hud's wrapper hides each player's container; move_2d_elements_to_default's wrapper runs the DE
            # script and fades both containers at the moment it fades hud_root.
            'Script WoR_HUD_setup_hud [\n'
            '\t:i $WoR_HUD_setup_hud_orig$ isNull\n'
            '\t:i $WoR_HUD_test_sp_start$ isNull\n'   # test harness only (build.py TEST_AUTOLAUNCH_SCRIPT)
            '\t:i $WoR_HUD_vocals_globals$ isNull\n'  # the DE's vocal globals for this theme (tools/wor_vocals.py)
            '\t:i $WoR_HUD_vocal_health_start$ isNull\n'   # the vocalist's health meter in 4-player band (wor_vocals)
            f'\t:i if {is_ours}\n'
            '\t\t:i if (~$game_mode$ = $p2_battle$)\n'
            '\t\t\t:i $FormatText$$checksumname$ = $container$%s("HUD_2D_Container%p")$p$ = %GLOBAL%$player_text$\n'
            '\t\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$container$\n'
            '\t\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$container$$alpha$ = %i(0)\n'
            '\t\t\t:i endif\n'
            '\t\t:i endif\n'
            '\t:i endif\n'
            '\t:i endfunction\n]\n\n'
            'Script WoR_HUD_setup_hud_orig [\n'
            '\t:i $printf$%s("WoR_HUD: setup_hud placeholder ran, plugin swap missing")\n'
            '\t:i endfunction\n]\n\n'
            'Script WoR_HUD_move_2d_elements_to_default [\n'
            f'\t:i if {is_ours}\n'
            '\t\t:i if (~$game_mode$ = $p2_battle$)\n'
            '\t\t\t:i $spawnscriptnow$$WoR_HUD_move_2d_elements_to_default_orig$$params$ = :s{$morph_time$ = %GLOBAL%$morph_time$:s}\n'
            '\t\t\t:i if $[af530ac6]$\n'
            '\t\t\t\t:i $wait$%f(0.5)$seconds$\n'
            '\t\t\t:i endif\n'
            '\t\t\t:i $wait$%GLOBAL%$morph_time$$seconds$\n'
            '\t\t\t:i $WoR_HUD_battle_rock$ isNull\n'
            '\t\t\t:i if $ScreenElementExists$$id$ = $HUD_2D_Containerp1$\n'
            '\t\t\t\t:i $HUD_2D_Containerp1$.$se_setprops$:s{$alpha$ = %i(1)$time$ = %f(0.25):s}\n'
            '\t\t\t:i endif\n'
            '\t\t\t:i if $ScreenElementExists$$id$ = $HUD_2D_Containerp2$\n'
            '\t\t\t\t:i $HUD_2D_Containerp2$.$se_setprops$:s{$alpha$ = %i(1)$time$ = %f(0.25):s}\n'
            '\t\t\t:i endif\n'
            '\t\t\t:i return\n'
            '\t\t:i endif\n'
            '\t:i endif\n'
            '\t:i $WoR_HUD_move_2d_elements_to_default_orig$ isNull\n'
            '\t:i endfunction\n]\n\n'
            'Script WoR_HUD_move_2d_elements_to_default_orig [\n'
            '\t:i $printf$%s("WoR_HUD: 2d hud move placeholder ran, plugin swap missing")\n'
            '\t:i endfunction\n]\n')


def rock_scripts():
    """WoR_HUD_battle_rock (run as the battle pieces fade in): each player's band rock tube desc, attached to its health
    and faded in with the rest; WoR_HUD_battle_needles: its needle stand-in on the DE's 2-highway path every frame."""
    import wor_mp as M
    t = 'Script WoR_HUD_battle_rock [\n\t:i if $ScreenElementExists$$id$ = $battlemode_container$\n'
    for p in (1, 2):
        (x, y), k, rot = rock_instance(p)
        i = BROCK_ID[p]
        t += (f'\t\t:i if NOT $ScreenElementExists$$id$ = ${i}$\n'
              f'\t\t\t:i $CreateScreenElement$:s{{$type$ = $descinterface$$parent$ = $battlemode_container$$id$ = ${i}$'
              f'$desc$ = %s("{M.SIDE_NAMES[2]}")$Pos$ = %vec2({x:.4f},{y:.4f})$just$ = :a{{$left$$top$:a}}'
              '$dims$ = %vec2(1280.0,720.0)$autosizedims$ = $false$'
              # z = band's chain total (wor_mp.Z_TUBES_1P; user 2026-10-25: battle still lacked quickplay's shadows):
              # at 0 the tube's end ball / drop shadow sank under the highway surface
              f'$Scale$ = %vec2({k:.5f},{k:.5f})$rot_angle$ = %f({rot:.4f})$z_priority$ = %f({M.Z_TUBES_1P:.1f})$alpha$ = %i(0):s}}\n'
              f'\t\t\t:i $HUD_attach_widget_player_health$$parent_id$ = ${i}$$player$ = %i({p})\n'
              f'\t\t\t:i $SetScreenElementProps$$id$ = ${i}$$alpha$ = %i(0)\n'
              f'\t\t\t:i ${i}$.$se_setprops$:s{{$alpha$ = %i(1)$time$ = %f(0.25):s}}\n'
              '\t\t:i endif\n')
    t += ('\t\t:i $spawnscriptnow$$WoR_HUD_battle_needles$\n'
          '\t:i endif\n\t:i endfunction\n]\n\n')
    t += ('Script WoR_HUD_battle_needles [\n'
          '\t:i $SetSpawnInstanceLimits$$max$ = %i(1)$management$ = $kill_oldest$\n'
          '\t:i while \n'
          f'\t\t:i if NOT $ScreenElementExists$$id$ = ${BROCK_ID[1]}$\n'
          '\t\t\t:i return\n'
          '\t\t:i endif\n'
          + ''.join(f'\t\t:i $WoR_HUD_battle_needle_set$$player$ = %i({p})$id$ = ${BROCK_ID[p]}$\n' for p in (1, 2)) +
          '\t\t:i $wait$%i(1)$gameframe$\n'
          '\t:i loop_to \n'
          '\t:i endfunction\n]\n\n')
    path = M.NEEDLE_PATHS[2]
    v = lambda q: f'%vec2({q[0]:.2f},{q[1]:.2f})'
    top = tuple(path[3][k] + (path[3][k] - path[2][k]) * NEEDLE_TOP_EXTRA for k in (0, 1))
    # the DE's 0x3205f550 for one player (health 0 / .6666 / 1.3333 / 2 on the path's knots)
    t += ('Script WoR_HUD_battle_needle_set [\n'
          '\t:i if $ScreenElementExists$$id$ = %GLOBAL%$id$\n'
          '\t\t:i $getplayerinfo$%GLOBAL%$player$$current_health$\n'
          '\t\t:i if (%GLOBAL%$current_health$ >= %f(1.3332998))\n'
          f'\t\t\t:i $pos_a$ = {v(path[2])}\n\t\t\t:i $pos_b$ = {v(top)}\n'
          '\t\t\t:i $WoR_t$ = ((%GLOBAL%$current_health$ - %f(1.3332998)) / %f(0.6669999))\n'
          '\t\t:i elseif (%GLOBAL%$current_health$ >= %f(0.6665999))\n'
          f'\t\t\t:i $pos_a$ = {v(path[1])}\n\t\t\t:i $pos_b$ = {v(path[2])}\n'
          '\t\t\t:i $WoR_t$ = ((%GLOBAL%$current_health$ - %f(0.6665999)) / %f(0.6669999))\n'
          '\t\t:i else \n'
          f'\t\t\t:i $pos_a$ = {v(path[0])}\n\t\t\t:i $pos_b$ = {v(path[1])}\n'
          '\t\t\t:i $WoR_t$ = (%GLOBAL%$current_health$ / %f(0.6669999))\n'
          '\t\t:i endif\n'
          '\t\t:i if (%GLOBAL%$WoR_t$ < %f(0.0))\n\t\t\t:i $WoR_t$ = %f(0.0)\n\t\t:i endif\n'
          '\t\t:i if (%GLOBAL%$WoR_t$ > %f(1.0))\n\t\t\t:i $WoR_t$ = %f(1.0)\n\t\t:i endif\n'
          '\t\t:i $final_pos$ = (%GLOBAL%$pos_a$ + ((%GLOBAL%$pos_b$ - %GLOBAL%$pos_a$) * %GLOBAL%$WoR_t$))\n'
          '\t\t:i %GLOBAL%$id$.$se_setprops$$side_meter_needle_pos$ = %GLOBAL%$final_pos$\n'
          '\t:i endif\n'
          '\t:i endfunction\n]\n\n')
    return t


def theme_extra():
    return (f'\t\t\t\tStructQBKey 0x6bd128d8 = {NAME}\n'
            f'\t\t\t\tStructString c2bf76cf = "{GAMERTAG}"\n'
            f'\t\t\t\tStructInt {FLAG} = 1\n')
