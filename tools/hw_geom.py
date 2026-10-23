"""Every highway's outer border, from the DE's own highway geometry, and the map that carries the 1-player pieces onto it
(user 2026-10-23: "from now on we're sticking by the book with how SINGLEPLAYER deals with highway elements").

The DE builds each highway from one struct per number of instrument highways (scripts/guitar/guitar_tweaks.qb
highway_guitar1/2/3: top width, width growth, height, playline; highway_2d.qb generate_pos_table) and shifts the whole
highway sideways by get_highway_pos_and_scale's Pos (2 highways: -+x_offset_p2; 3: the drum centred, the guitars at
-+x_offset_p3 x 1.8; our theme adds wor_battle.SEP / SEP3). Drawn over the 16:9 bot captures of 2026-10-22 these edges
lie exactly on every highway's surface edge (1g1v, 2g1v, face-off, 3g1v). The WoR border sits outside that edge, its
width growing down the highway the same way in every layout (median of each capture's frames, outer edge per row):
4.2 + 19.5 f px with one highway, 4.7 + 18.9 f with two, 5.0 + 18.5 f with three (f = fraction of the height from the
top).

The 1-player pieces keep their relation to that outer border: on another highway, each side's pieces are the 1-player
ones under the similarity that lays the 1-player outer border line onto this one (same fraction of the border at every
point: scale = border length ratio, 0.75 with two highways, the DE's own sidebar_y_scale; rotation = lean change, the
pieces stay parallel to their border as in quickplay)."""
import math

# guitar_tweaks.qb (DE): highway_guitar1 / 2 / 3
STRUCTS = {
    1: dict(playline=655.0, height=350.0, top_w=160.0, wof=2.2),
    2: dict(playline=655.0, height=270.0, top_w=170.0, wof=1.33),
    3: dict(playline=655.0, height=270.0, top_w=152.0, wof=1.2),
}
X_OFFSET_P2, X_OFFSET_P3 = 230.0, 225.0          # guitar_tweaks.qb
BORDER_W = {1: (4.22, 19.54), 2: (4.67, 18.93), 3: (5.03, 18.51)}   # outer border: a + b * f px outside the edge


def shifts(n):
    """Pos.x of each highway (left to right) with our theme (wor_battle's wrapper of get_highway_pos_and_scale)."""
    import wor_battle as B
    if n == 1:
        return [0.0]
    if n == 2:
        return [-(X_OFFSET_P2 + B.SEP), X_OFFSET_P2 + B.SEP]
    return [-(X_OFFSET_P3 + B.SEP3) * 1.8, 0.0, (X_OFFSET_P3 + B.SEP3) * 1.8]


def outer_border(n, shift, side):
    """((x, y) at the highway top, (x, y) at the playline) of the border's outer edge; side 'left' / 'right'."""
    s = STRUCTS[n]
    stx = 640.0 - s['top_w'] / 2
    sbx = 640.0 - (s['top_w'] + s['top_w'] * s['wof']) / 2
    a, b = BORDER_W[n]
    top_y, bot_y = s['playline'] - s['height'], s['playline']
    pts = []
    for f, y in ((0.0, top_y), (1.0, bot_y)):
        x = stx - (stx - sbx) * f - (a + b * f)
        pts.append((x if side == 'left' else 1280.0 - x, y))
    return tuple((x + shift, y) for x, y in pts)


def similarity(n, shift, side):
    """(k, rot_deg, t): canvas point p of the 1-player HUD -> k * R(rot) p + t on this highway's side (R: clockwise
    for rot > 0, as rot_angle does on screen)."""
    (a1, b1), (a2, b2) = outer_border(1, 0.0, side), outer_border(n, shift, side)
    v1 = (b1[0] - a1[0], b1[1] - a1[1])
    v2 = (b2[0] - a2[0], b2[1] - a2[1])
    k = math.hypot(*v2) / math.hypot(*v1)
    rot = math.degrees(math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0]))
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    ra = (k * (c * a1[0] - s * a1[1]), k * (s * a1[0] + c * a1[1]))
    return k, rot, (a2[0] - ra[0], a2[1] - ra[1])


def apply(sim, p):
    k, rot, t = sim
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return (k * (c * p[0] - s * p[1]) + t[0], k * (s * p[0] + c * p[1]) + t[1])
