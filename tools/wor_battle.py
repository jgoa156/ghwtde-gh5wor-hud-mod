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
OFFSCREEN = {1: (-700.0, 100.0), 2: (2100.0, 100.0)}

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
VISOR_GAP = 0.94                        # ring centres this many rim radii apart along the rail (a little overlap)
VISOR_Z = {'big': 18.3, 'mid': 18.2, 'small': 18.1}   # under the cards (z 19): the glass is opaque
CARD_FILL = 0.8                         # a card fills this much of its visor's glass diameter (0.9 hid the rim: user
                                        # 2026-10-22, the slot's border must show around the card)
VISOR_INSET = 4.0                       # screen px the whole slot set moves towards the highway (user 2026-10-22: the
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
RAIL_L = ((320.0, 395.0), (170.0, 700.0))           # P1 left / right rail lines (top, bottom)
RAIL_R = ((500.0, 395.0), (652.0, 700.0))
STRIKE_2P, TOP_2P = 633.0, 393.0                     # strikeline / top of the battle highways
STRIKE_1P, TOP_1P = 638.0, 300.0                     # the 1-player highway (tools/mock_base.py)
# test 2026-10-21 (user clip "Video Project 25"): on the moved highways the rock tube's centre sat ~24 px off the left
# rail's outer edge (the 3D highway doesn't move like the pasted mock), leaving a gap; the slots touched their rail
ROCK_NUDGE = np.array((15.0, 0.0))
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
    rock[:, 2] += ROCK_NUDGE
    sp = _affine([(cr(yb), yb), (cr(yt), yt), (cl(yb), yb)], [(R(yb2), yb2), (R(yt2), yt2), (L(yb2), yb2)])
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

    def f(q):
        v = wor_1g.rot(((q[0] - se[0]) * e.scale[0], (q[1] - se[1]) * e.scale[1]), e.rot)
        return apply(m, (anchor[0] + v[0], anchor[1] + v[1]))
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
        t = rim if prev is None else t + (prev + rim) * VISOR_GAP
        tau = t - along(shrink(ring, s, 0.0))              # slide so the glass centre lands at t along the rail
        out.append((key, shrink(bc, s, tau), (s * tw / SS, s * th / SS), shrink(ring, s, tau), VISOR_RING[2] * k * s))
        prev = rim
    nx, ny = -v[1], v[0]
    if nx > 0:                                          # the normal pointing at the highway (left of P1's right rail)
        nx, ny = -nx, -ny
    move = lambda p: (p[0] + nx * VISOR_INSET, p[1] + ny * VISOR_INSET)
    return [(key, move(c), dims, move(g), r) for key, c, dims, g, r in out]


def slots_on_tube(sep=SEP):
    """[(slot, glass centre, element dims, glass radius)] of the visors (the cards' slots), P1 screen."""
    return [(key, c, dims, r) for key, _, dims, c, r in visors(sep)]


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
    return [apply(m, (p[0] + SIDE_METER_CALIB[0], p[1] + SIDE_METER_CALIB[1]))
            for p in (wor_1g.LEFT.at(h) for h in wor_1g.NEEDLE_STOPS)]


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
    t += f'{hdr}StructFloat Scale = {SCALE}\n{hdr}StructInt z = 0\n'
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
    (tc, (tw, th)) = tube_box()
    tube = (tw / SS, th / SS)
    t += _elem('HUD2D_rock_body', TUBE_TEX['body'], tc, tube, 13)
    for c, z, a in (('red', 14, 0), ('yellow', 15, 1), ('green', 16, 0)):    # the song starts at health 1 (yellow)
        t += _elem(f'HUD2D_rock_lights_{c}', TUBE_TEX[c], tc, tube, z, alpha=a)
    for eid in ('HUD2D_rock_BG_green', 'HUD2D_rock_BG_red', 'HUD2D_rock_BG_yellow', 'HUD2D_rock_lights_all'):
        t += _elem(eid, BLANK, tc, (4.0, 4.0), 17, alpha=0)
    # needle: the DE turns the stand-in (blank, at the health-0 stop); the plugin slides ours up the tube from it
    st = needle_stops()
    nd = _pow2(NEEDLE_BOX * SS) / SS
    t += _elem('HUD2D_rock_needle', BLANK, st[0], (4.0, 4.0), 18.4)
    t += _elem('WoR_HUD_battle_needle', NEEDLE_TEX, ((st[1][0] + st[2][0]) / 2, (st[1][1] + st[2][1]) / 2), (nd, nd), 18.5)
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
    _, scales = card_sizes()
    is_ours = f'$[4c1beb8d]$$value$ = ${FLAG}$'
    return ('Script WoR_HUD_create_battle_alert_frames [\n'
            f'\t:i if {is_ours}\n'
            + changes(card_offsets(), scales) +
            '\t\t:i $printf$%s("WoR_HUD: battle attack cards moved into the WoR slots")\n'
            '\t:i else \n'
            + changes(STOCK_CARD_OFFS, STOCK_CARD_SCALES) +
            '\t:i endif\n'
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
            'Script WoR_HUD_get_highway_pos_and_scale [\n'
            '\t:i $WoR_HUD_get_highway_pos_and_scale_orig$ isNull\n'
            '\t:i if (%GLOBAL%$num_non_vocals_players$ = %i(2))\n'
            f'\t\t:i if {is_ours}\n'
            '\t\t\t:i if (%GLOBAL%$non_vocalist_player$ = %i(1))\n'
            f'\t\t\t\t:i %GLOBAL%$Pos$ = (%GLOBAL%$Pos$ - %vec2({SEP:.1f},0.0))\n'
            '\t\t\t:i else \n'
            f'\t\t\t\t:i %GLOBAL%$Pos$ = (%GLOBAL%$Pos$ + %vec2({SEP:.1f},0.0))\n'
            '\t\t\t:i endif\n'
            '\t\t:i endif\n'
            '\t:i endif\n'
            '\t:i return$Pos$ = %GLOBAL%$Pos$$Scale$ = %GLOBAL%$Scale$\n'
            '\t:i endfunction\n]\n\n'
            'Script WoR_HUD_get_highway_pos_and_scale_orig [\n'
            '\t:i $printf$%s("WoR_HUD: highway pos placeholder ran, plugin swap missing")\n'
            '\t:i return$Pos$ = %vec2(0.0,0.0)$Scale$ = %vec2(1.0,1.0)\n'
            '\t:i endfunction\n]\n')


def theme_extra():
    return (f'\t\t\t\tStructQBKey 0x6bd128d8 = {NAME}\n'
            f'\t\t\t\tStructString c2bf76cf = "{GAMERTAG}"\n'
            f'\t\t\t\tStructInt {FLAG} = 1\n')
