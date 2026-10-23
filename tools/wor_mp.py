"""Per-player WoR pieces on every multi-highway layout (hud_1g1v, hud_2g, hud_2g1v, hud_3g1v; user 2026-10-21: "in band,
rock meter, star power tube and streak multiplier is kept"; 2026-10-23: "sticking by the book with how SINGLEPLAYER
deals with highway elements").

Each player container (g1 / g2 / g3) shows the 1-player pieces themselves, copied element for element (shadows, gaps,
balls, glows, draw priorities: the tubes just above the DE's border, the badge and the balls under the highway surface),
and placed by one map per highway side (tools/hw_geom.py): the 1-player outer border laid onto this highway's, from
the DE's own highway geometry. On the guitar + vocals layout the highway is the 1-player one, so that map is the
identity and the pieces sit exactly where quickplay puts them.

  - Star_Power -> wor_sp_mp_ghwor: the 1-player star power tube (every sp_* element); fed by our
    HUD_attach_widget_player_star_power (six segments glow0..5) and run by the plugin's tube engine per tube.
  - BAND_side_meter -> wor_side_mp<n>_ghwor: the 1-player rock tube (every rm_* element and the LED lights) with the
    1-player side meter's sliding needle. The DE drives that needle's invisible stand-in on the path of the layout's
    number of instrument highways (script 0x3205f550: 1, 2, or 3+); each variant's anchor has its own scale, which is
    how the plugin finds it and maps the DE path onto the WoR LED stops. The DE's per-zone ON alphas light the
    1-player LEDs. The DE attaches it only where the mode has per-player health (not face-off types), so it starts at
    alpha 0 and WoR_HUD_HUD_attach_widget_player_health shows it when attached.
  - player_meter -> wor_mult_mp_ghwor: the 1-player multiplier badge with its five note-streak lights. The DE kills
    alias_player_multiplier in face-off types (GH:588-594); ours points at a hidden stand-in, so the streak meter stays
    on every highway in face-off too.
"""
import copy
import math
import re

import hw_geom as HG
import wor_battle as B
import wor_versus as V
from desc_gen import E, desc

SP_NAME, MULT_NAME = 'wor_sp_mp_ghwor', 'wor_mult_mp_ghwor'
SIDE_NAMES = {1: 'wor_side_mp1_ghwor', 2: 'wor_side_mp_ghwor', 3: 'wor_side_mp3_ghwor'}
# The DE's rock needle path per number of instrument highways (script 0x3205f550: health 0 / .667 / 1.333 / 2)
NEEDLE_PATHS = {1: ((0.0, 0.0), (11.0, -24.0), (28.0, -57.0), (41.0, -80.0)),
                2: ((0.0, 0.0), (13.0, -28.0), (26.0, -58.0), (37.0, -84.0)),
                3: ((-4.0, 2.0), (8.0, -32.0), (21.0, -67.0), (33.0, -100.0))}
# where the game draws the 1-player descs (preview_hud.GAME_CALIB, measured on the v0.17 capture): root-level descs
# (the band meter: both tubes) at their coordinates + ROOT_CAL, g1's descs (multiplier, side meter) at g1 + G_CAL
# 2026-10-23 (user test of 1.49, guitar + vocals vs quickplay): every container draws its descs like the root,
# (1, 3); the (1, 9) measured on the v0.17 capture belongs to the multiplier / side meter descs themselves (their
# content draws 6 lower), not to g1. With G_CAL (1, 9) every multiplayer tube sat 6 units too high (the lit LED 7.4 px
# higher than quickplay's in the user's 2000 px frames), i.e. off the border on the slanted rail.
ROOT_CAL, G_CAL = (1.0, 3.0), (1.0, 3.0)
SIDE_INTRINSIC = (0.0, 6.0)   # the 1-player side meter desc's own +6 (its needle, moved into a band-meter-like desc)
# how far the 1-player tubes' inner edges reach over the outer border (canvas units at the LED span, measured on the
# rm_base / sp_base art through wor_1g.LEFT / RIGHT): the similarity scales that overlap with the highway (0.75 on
# 2 highways); the pieces move inwards by the lost part so they stay attached to the border like in quickplay
OVERLAP_1P = {'left': 9.7, 'right': 7.5}
# the 1-player layout's draw-priority chains (hud_1g_ghwor): the tubes sit in band_meter (hud_container 0 + 1), the
# multiplier in g1 / player_meter (0 + 2 + 2)
Z_TUBES_1P, Z_MULT_1P = 1.0, 4.0
Z_MULT_INSTANCE = 2.0         # hud_1g_ghwor's player_meter z (wor_1g.layout): the multiplier instances' own z
LAYOUTS = {'hud_1g1v': (1, ('g1',)), 'hud_2g': (2, ('g1', 'g2')), 'hud_2g1v': (2, ('g1', 'g2')),
           'hud_3g1v': (3, ('g1', 'g2', 'g3'))}


def _dummy(lid, kind='SpriteElement'):
    return E(lid, kind, dims=(4, 4), alpha=0.0, z=0.0, **({'texture': 'WoR_HUD_blank'} if kind == 'SpriteElement'
                                                            else {'font': V.SCORE_FONT, 'text': '0x00000000', 'shadow': False}
                                                            if kind == 'TextBlockElement' else {}))


def _root(lid, kids, alpha=1.0):
    return E(lid, 'ContainerElement', dims=(1280, 720), just=(-1, -1), alpha=alpha, children=kids)


def _one_player():
    import wor_1g, desc_gen
    wor_1g.all_descs()
    return desc_gen


# ---- star power tube
SP_SEGMENTS = 6
MP_FILL_Z, MP_SRC_Z = 3.0515, 3.0525      # unique draw priorities: how the plugin finds our fill and the level source


def sp_desc():
    """The 1-player star power tube itself (every sp_* element of the band meter: body, clip window + six fill
    segments, feathered top, glows, ready burst, marker) in its own coordinates (user 2026-10-22: the same tube as
    quickplay on every player, one tube engine state per tube). The DE's widget writes glow0..5 like the 1-player band
    meter (our HUD_attach_widget_player_star_power: the band's star power in band / co-op, the player's own in face-off
    and battle)."""
    import wor_1g
    dg = _one_player()
    kids = [copy.deepcopy(c) for c in dg.ROOTS['wor_band_meter_1g_ghwor'].children if c.local_id.startswith('sp_')]
    # 2026-10-23: the per-player widget never reached the plugin's tube hook (no "smooth fill active" in any
    # multiplayer session: the DE's own six segments showed, cut by the clip window). Here the clip window holds our
    # own fill (sp_fill: the sprite the 1-player engine makes of segment 0) and the DE's segments sit in a zero-size
    # window (sp_src, clipped away) that only carries the level: the plugin reads it from their scales every frame
    # (MP_SRC_Z / MP_FILL_Z mark the two windows' contents) and runs the 1-player engine on sp_clip.
    clip = next(c for c in kids if c.local_id == 'sp_clip')
    segs = clip.children
    fill = copy.deepcopy(segs[0])
    g = wor_1g.plugin_geometry()
    fill.local_id = 'sp_fill'
    fill.pos = (g['kFillX'] - g['kClipX'], g['kFillY'] - g['kClipY'])
    fill.dims, fill.scale, fill.z = (64, 256), (g['kFillSX'], g['kFillSY']), MP_FILL_Z
    fill.extra = dict(fill.extra, texture=wor_1g.SP_FULL_NAMES[0])
    clip.children = [fill]
    # off screen (user test 2026-10-23: a zero-size window does NOT clip; the segments drew over every multiplayer
    # tube as striped teal blocks; the DE's graveyard windows work because they sit off screen). The segments are
    # placed from the window's corner, so they go with it; the plugin only reads their scales.
    kids.append(E('sp_src', 'windowelement', pos=(-4000.0, -4000.0), dims=(0, 0), just=(-1, -1), z=MP_SRC_Z,
                  children=segs))
    props = [(f'glow{i}_texture', f'sp_seg{i}', 'texture') for i in range(SP_SEGMENTS)]
    props += [(f'glow{i}_scale', f'sp_seg{i}', 'Scale') for i in range(SP_SEGMENTS)]
    root = _root('sp_mp', kids)
    root.z = dg.ROOTS['wor_band_meter_1g_ghwor'].z            # the band meter root's (lifted) z, as in quickplay
    return desc(SP_NAME, root, props)


# ---- rock tube
ROCK_PARTS = ('lights_bg', 'red_light', 'yellow_light', 'green_light')
MP_NEEDLE_DX = -2.0         # desc units (~1.5 screen px on the 2- and 3-highway layouts): user 2026-10-23, the white needle
                            # a little left on every multiplayer highway


def needle_anchor(n):
    """(anchor pos, anchor scale, our needle stops in anchor units) for the DE path of n instrument highways, on the
    1-player rock tube (canvas): the anchor maps the path's start onto NEEDLE_H0 and its end onto NEEDLE_H2, like the
    1-player side meter (n = 1 gives its anchor exactly)."""
    import wor_1g
    path = NEEDLE_PATHS[n]
    (sx, sy), (ex, ey) = path[0], path[-1]
    a, b = wor_1g.LEFT.at(wor_1g.NEEDLE_H0), wor_1g.LEFT.at(wor_1g.NEEDLE_H2)
    ax, ay = (b[0] - a[0]) / (ex - sx), (b[1] - a[1]) / (ey - sy)
    stops = []
    for h in wor_1g.NEEDLE_STOPS:
        g = (h - wor_1g.NEEDLE_H0) / (wor_1g.NEEDLE_H2 - wor_1g.NEEDLE_H0)
        stops.append((sx + (ex - sx) * g, sy + (ey - sy) * g))
    return (a[0] - ax * sx, a[1] - ay * sy), (ax, ay), stops


def side_desc(n):
    """The 1-player rock tube (band meter rm_* elements + LED lights, canvas coordinates) with the 1-player side meter's
    needle (its anchor for this layout's DE needle path, moved from g1's coordinates into the band meter's: + G1 + the
    calibration difference, so it sits on the tube exactly as in quickplay)."""
    import wor_1g
    dg = _one_player()
    kids = [copy.deepcopy(c) for c in dg.ROOTS['wor_band_meter_1g_ghwor'].children
            if c.local_id.startswith('rm_') or c.local_id in ROCK_PARTS]
    for c in kids:
        if c.local_id in ('red_light', 'green_light'):
            c.alpha = 0.0                            # health starts in the yellow zone; the DE sets them on attach
    side = dg.ROOTS['wor_side_meter_ghwor']
    needle = copy.deepcopy(next(c for c in side.children if c.local_id == 'needle_anchor'))
    pos, (ax, ay), _ = needle_anchor(n)
    needle.pos = (pos[0] + SIDE_INTRINSIC[0] + MP_NEEDLE_DX, pos[1] + SIDE_INTRINSIC[1])
    needle.scale = (ax, ay)
    nd = 40.0                                        # needle size on screen (wor_1g.side_meter)
    for c in needle.children:
        if c.extra.get('texture') == 'WoR_HUD_needle_glow':
            c.dims = (nd / ax, nd / ay)
    kids.append(needle)
    kids.append(_dummy('side_meter_red_glow'))
    kids.append(_dummy('side_meter_red_rgba_sink'))
    props = [('side_meter_needle_pos', 'needle_src', 'Pos'), ('side_meter_needle_scale', 'needle_src', 'Scale'),
             ('SIDE_meter_red_ON_alpha', 'red_light', 'alpha'),
             ('SIDE_meter_yellow_ON_alpha', 'yellow_light', 'alpha'),
             ('SIDE_meter_green_ON_alpha', 'green_light', 'alpha'),
             # the DE pulses this colour (failing vignette, 0x4f63289b); in quickplay it goes to the side meter's own
             # overlay, never to the LED: on the LED it faded the red light out (user test 2026-10-23: band rock
             # meter in the red zone with no LED lit)
             ('SIDE_meter_red_ON_rgba', 'side_meter_red_rgba_sink', 'rgba'),
             ('side_meter_red_glow_rgba', 'side_meter_red_glow', 'rgba')]
    root = _root('side_mp', kids)
    root.z = dg.ROOTS['wor_band_meter_1g_ghwor'].z            # the band meter root's (lifted) z, as in quickplay
    return desc(SIDE_NAMES[n], root, props)


# ---- multiplier + note-streak lights
def mult_desc():
    """The 1-player multiplier desc (badge, stick, five lights, glows, background: g1 coordinates) + the face-off
    alias stand-in."""
    dg = _one_player()
    root = copy.deepcopy(dg.ROOTS['wor_mult_1g_ghwor'])
    root.children.append(_dummy('mult_die_standin'))
    props = list(dg.PROPS['wor_mult_1g_ghwor'])
    return desc(MULT_NAME, root, props, aliases=[('alias_player_multiplier', 'mult_die_standin')])


def descs():
    return [sp_desc(), mult_desc()] + [side_desc(n) for n in sorted(SIDE_NAMES)]


def textures(battle_textures):
    return {}


def sources():
    return {}


# ---- layout edits
def _parse_tree(d):
    """The layout desc's element tree: nested dicts (id, pos, dims, just, anchor, scale, kids)."""
    from desc_tree import tokens_block, field

    def nums(props, name, default):
        v = field(props, name)
        if v is None:
            return default
        try:
            vals = [float(x) for x in v.split(',')]
        except ValueError:
            return default
        return tuple(vals[:2]) if len(vals) >= 2 else default

    def parse(seg):
        out, i = [], 0
        while True:
            m = re.search(r'StructStruct props', seg[i:])
            if not m:
                return out
            props, p1 = tokens_block(seg, i + m.start())
            zp = field(props, 'z_priority')
            try:
                zp = float(zp) if zp is not None else 0.0
            except ValueError:
                zp = 0.0
            node = dict(id=field(props, 'local_id'), pos=nums(props, 'Pos', (0.0, 0.0)),
                        dims=nums(props, 'dims', (100.0, 100.0)), just=nums(props, 'just', (-1.0, -1.0)),
                        anchor=nums(props, 'pos_anchor', (-1.0, -1.0)), scale=nums(props, 'Scale', (1.0, 1.0)),
                        z=zp, kids=[])
            c = re.match(r'\s*StructArray children', seg[p1:])
            if c:
                kids, p2 = tokens_block(seg, p1 + c.end())
                node['kids'] = parse(kids[1:-1])
                i = p2
            else:
                i = p1
            out.append(node)
    return parse(d[d.index('StructStruct elements'):])[0]


def container_origins(d):
    """{local id: (top-left x, y, scale, z sum)} of every element, by the GUI's placement (pos from the parent's
    pos_anchor point, just = the element's own anchor, Scale applies to children; tools/mock_modes.render); z sum =
    the element's z_priority plus its ancestors'."""
    out = {}

    def walk(e, rect, psc, pz):
        x0, y0, w, h = rect
        px = x0 + (e['anchor'][0] + 1) / 2 * w + e['pos'][0] * psc[0]
        py = y0 + (e['anchor'][1] + 1) / 2 * h + e['pos'][1] * psc[1]
        sc = (psc[0] * e['scale'][0], psc[1] * e['scale'][1])
        ew, eh = e['dims'][0] * sc[0], e['dims'][1] * sc[1]
        ex, ey = px - (e['just'][0] + 1) / 2 * ew, py - (e['just'][1] + 1) / 2 * eh
        z = pz + e['z']
        out.setdefault(e['id'], (ex, ey, sc[0], z))
        for c in e['kids']:
            walk(c, (ex, ey, ew, eh), sc, z)
    walk(_parse_tree(d), (0.0, 0.0, 1280.0, 720.0), (1.0, 1.0), 0.0)
    return out


def instance(sim, origin, src):
    """(Pos, Scale, rot) of a descinterface in a container whose drawn top-left is `origin` (scale 1), so that its
    content, drawn by the 1-player layout at src + content, lands at sim(src + content)."""
    k, rot, t = sim
    p = HG.apply((k, rot, (0.0, 0.0)), src)
    return (p[0] + t[0] - origin[0], p[1] + t[1] - origin[1]), k, rot


def _put_child(d, g, child, block):
    """Replace container g's child `child` with block (same place in the children array), or append it."""
    import desc_edit
    a, b = V._element_bounds(d, g)
    blk = d[a:b]
    m = re.search(rf'StructQBKey local_id = {re.escape(child)}\s*\n', blk)
    if not m:
        return _append_children(d, g, [block])
    pa, pb = desc_edit._block_bounds(blk, m.start())       # the props' StructHeader { ... }
    pa, pb = desc_edit._block_bounds(blk, pa - 1)          # StructStruct props { ... }
    pa, pb = desc_edit._block_bounds(blk, pa - 1)          # the element's StructHeader { ... }
    pa = blk.rfind('StructHeader', 0, pa)
    return d[:a] + blk[:pa] + block + blk[pb:] + d[b:]


def _append_children(d, lid, blocks):
    """Insert element blocks at the end of element lid's children array (indices of existing children unchanged)."""
    a, b = V._element_bounds(d, lid)
    blk = d[a:b]
    k = blk.index('StructArray children')
    j = blk.index('[', k)
    depth = 0
    for e in range(j, len(blk)):
        depth += {'[': 1, ']': -1}.get(blk[e], 0)
        if depth == 0:
            break
    blk = blk[:e] + '\n' + '\n'.join(blocks) + '\n' + blk[e:]
    return d[:a] + blk + d[b:]


def _hide_child(d, g, child):
    """alpha 0 on container g's child (local ids repeat across containers)."""
    import desc_edit
    a, b = V._element_bounds(d, g)
    blk = d[a:b]
    m = re.search(rf'StructQBKey local_id = {re.escape(child)}\s*\n', blk)
    if not m:
        return d
    pa, pb = desc_edit._block_bounds(blk, m.start())
    p, n = re.subn(r'StructFloat alpha = [-\d.]+', 'StructFloat alpha = 0.00', blk[pa:pb], count=1)
    assert n == 1, (g, child)
    return d[:a] + blk[:pa] + p + blk[pb:] + d[b:]


def placements(config, d=None):
    """[(container, child, desc, (Pos, Scale, rot), z, alpha)] for layout `config` (d: its text, for the container
    origins; the guitar + vocals and 2-highway layouts' containers are read from it)."""
    import wor_1g
    n, groups = LAYOUTS[config]
    org = container_origins(d)
    out = []
    for g, shift in zip(groups, HG.shifts(n)):
        ox, oy, sc, gz = org[g]
        assert abs(sc - 1.0) < 1e-6, (config, g, sc)
        o = (ox + G_CAL[0], oy + G_CAL[1])
        left, right = HG.similarity(n, shift, 'left'), HG.similarity(n, shift, 'right')
        g1 = (wor_1g.G1[0] + G_CAL[0], wor_1g.G1[1] + G_CAL[1])
        # the instance's z makes its chain of draw priorities sum to the 1-player one (Z_TUBES_1P / Z_MULT_1P), so
        # every element layers against the highway exactly as in quickplay (user 2026-10-23: the band tubes, at
        # quickplay's exact spot, looked like floating over the highway)
        zt = Z_TUBES_1P - gz
        # 2026-10-23 (user tests of 1.50 / 1.51): the multiplier gets the 1-player player_meter's own z instead. What
        # layers it against the highway is the instance's own z, not the chain's sum: up to 1.48 it was 2 and the
        # badge's arm went behind the border (user frame, guitar + vocals, 02:45 with 1.48); 1.49's chain total made it
        # 4 - g1's z = 3 on 2 highways, and the arm has drawn over the border's bevel since (the DE's z 3 sidebar
        # sprite: 2.05 under it, 3.05 over it). The tubes keep the chain value (user: perfect in band quickplay).
        zm = Z_MULT_INSTANCE

        def inward(inst, side, k):
            (px, py), sc, rot = inst
            d = (1.0 - k) * OVERLAP_1P[side] * (1.0 if side == 'left' else -1.0)
            return (px + d, py), sc, rot
        out += [(g, 'player_meter', MULT_NAME, inward(instance(right, o, g1), 'right', right[0]), zm, 1.0),
                (g, 'Star_Power', SP_NAME, inward(instance(right, o, ROOT_CAL), 'right', right[0]), zt, 0.0),
                (g, 'BAND_side_meter', SIDE_NAMES[n], inward(instance(left, o, ROOT_CAL), 'left', left[0]), zt, 0.0)]
    return out


def edit_highways(config, d):
    """Layout `config`: the 2-highway layouts' player containers follow the highways (their gamertags and messages);
    every player container gets the 1-player pieces on its highway (placements); the WT+ copies' own star power child
    (star_power_1g, not wired by the DE) hides."""
    n, groups = LAYOUTS[config]
    if n == 2:
        d = V._shift_pos(d, 'g1', -B.SEP)
        d = V._shift_pos(d, 'g2', B.SEP)
    for g in groups:
        d = _hide_child(d, g, 'star_power_1g')
    for g, child, name, (pos, k, rot), z, alpha in placements(config, d):
        block = E(child, 'descinterface', pos=pos, dims=(1280, 720), just=(-1, -1), scale=(k, k), rot=rot, z=z,
                  alpha=alpha, desc=name).render(0)
        d = _put_child(d, g, child, block)
    return d


SCRIPTS = (
    # the DE's HUD_attach_widget_player_star_power, replaced (plugin swap): with this theme six segments (the 1-player
    # tube copy, wor_mp.sp_desc), the band's star power in band / co-op (user 2026-10-22: every player's tube shows the
    # band's), each player's own in face-off types, battle and boss battles; other themes: the DE's own three segments
    'Script WoR_HUD_HUD_attach_widget_player_star_power [\n'
    '\t:i $getplayerinfo$%GLOBAL%$player$$checksum$\n'
    '\t:i $ResolveScreenElementID$$id$ = %GLOBAL%$parent_id$$param$ = $id$\n'
    '\t:i if (~$current_num_players$ > %i(1))\n'
    # parent_id is the DE's compound id :s{<g container> child = Star_Power}: our desc's root (sp_mp) is a child of the
    # RESOLVED element (2026-10-23: the check on :s{parent_id child = sp_mp} replaced its child = Star_Power and never
    # matched, so every multiplayer tube took the DE's 3-segment branch)
    '\t\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$id$$child$ = $sp_mp$:s}\n'
    # career versus (boss battles): no star power tube (user 2026-10-23, WoR reference: only the streak meter)
    '\t\t\t:i if ((~$boss_battle$ = %i(1)) OR (~$game_mode$ = $p1_career$))\n'
    '\t\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$id$$alpha$ = %i(0)\n'
    '\t\t\t\t:i return\n'
    '\t\t\t:i endif\n'
    # the tube starts hidden (career versus doesn't attach star power at all: user 2026-10-23, it still showed)
    '\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$id$$alpha$ = %i(1)\n'
    '\t\t\t:i $sp_band$ = %i(1)\n'
    '\t\t\t:i if (~$game_mode$ = $p2_faceoff$)\n\t\t\t\t:i %GLOBAL%$sp_band$ = %i(0)\n\t\t\t:i endif\n'
    '\t\t\t:i if (~$game_mode$ = $p2_pro_faceoff$)\n\t\t\t\t:i %GLOBAL%$sp_band$ = %i(0)\n\t\t\t:i endif\n'
    '\t\t\t:i if (~$game_mode$ = $p4_pro_faceoff$)\n\t\t\t\t:i %GLOBAL%$sp_band$ = %i(0)\n\t\t\t:i endif\n'
    '\t\t\t:i if (~$game_mode$ = $p2_battle$)\n\t\t\t\t:i %GLOBAL%$sp_band$ = %i(0)\n\t\t\t:i endif\n'
    '\t\t\t:i if (~$boss_battle$ = %i(1))\n\t\t\t\t:i %GLOBAL%$sp_band$ = %i(0)\n\t\t\t:i endif\n'
    '\t\t\t:i if (%GLOBAL%$sp_band$ = %i(1))\n'
    '\t\t\t\t:i $AttachHudWidget$:s{\n'
    '\t\t\t\t:i $Input$ = :s{\n'
    '\t\t\t\t\t:i $value$ = $band1_starpower$\n'
    '\t\t\t\t:i :s}\n'
    '\t\t\t\t:i $output$ = :s{\n'
    '\t\t\t\t\t:i $type$ = $setubes$\n'
    '\t\t\t\t\t:i $desc_id$ = %GLOBAL%$id$\n'
    '\t\t\t\t\t:i $band$ = $true$\n'
    '\t\t\t\t\t:i $band_num$ = %i(1)\n'
    '\t\t\t\t\t:i $default_scale$ = %vec2(1.0,1.0)\n'
    '\t\t\t\t\t:i $value_range$ = :a{%f(0.0)%f(100.0):a}\n'
    '\t\t\t\t\t:i $textures$ = :a{$glow0_texture$$glow1_texture$$glow2_texture$$glow3_texture$$glow4_texture$$glow5_texture$:a}\n'
    '\t\t\t\t\t:i $scales$ = :a{$glow0_scale$$glow1_scale$$glow2_scale$$glow3_scale$$glow4_scale$$glow5_scale$:a}\n'
    '\t\t\t\t:i :s}\n'
    '\t\t\t:i :s}\n'
    '\t\t\t:i else \n'
    '\t\t\t:i $AttachHudWidget$:s{\n'
    '\t\t\t\t:i $Input$ = :s{\n'
    '\t\t\t\t\t:i $object$ = %GLOBAL%$checksum$\n'
    '\t\t\t\t\t:i $value$ = $starpower_amount$\n'
    '\t\t\t\t:i :s}\n'
    '\t\t\t\t:i $output$ = :s{\n'
    '\t\t\t\t\t:i $type$ = $setubes$\n'
    '\t\t\t\t\t:i $desc_id$ = %GLOBAL%$id$\n'
    '\t\t\t\t\t:i $player$ = %GLOBAL%$player$\n'
    '\t\t\t\t\t:i $value_range$ = :a{%f(0.0)%f(100.0):a}\n'
    '\t\t\t\t\t:i $textures$ = :a{$glow0_texture$$glow1_texture$$glow2_texture$$glow3_texture$$glow4_texture$$glow5_texture$:a}\n'
    '\t\t\t\t\t:i $scales$ = :a{$glow0_scale$$glow1_scale$$glow2_scale$$glow3_scale$$glow4_scale$$glow5_scale$:a}\n'
    '\t\t\t\t:i :s}\n'
    '\t\t\t:i :s}\n'
    '\t\t\t:i endif\n'
    '\t\t:i else \n'
    '\t\t\t:i $AttachHudWidget$:s{\n'
    '\t\t\t\t:i $Input$ = :s{\n'
    '\t\t\t\t\t:i $object$ = %GLOBAL%$checksum$\n'
    '\t\t\t\t\t:i $value$ = $starpower_amount$\n'
    '\t\t\t\t:i :s}\n'
    '\t\t\t\t:i $output$ = :s{\n'
    '\t\t\t\t\t:i $type$ = $setubes$\n'
    '\t\t\t\t\t:i $desc_id$ = %GLOBAL%$id$\n'
    '\t\t\t\t\t:i $player$ = %GLOBAL%$player$\n'
    '\t\t\t\t\t:i $value_range$ = :a{%f(0.0)%f(100.0):a}\n'
    '\t\t\t\t\t:i $textures$ = :a{$glow0_texture$$glow1_texture$$glow2_texture$:a}\n'
    '\t\t\t\t\t:i $scales$ = :a{$glow0_scale$$glow1_scale$$glow2_scale$:a}\n'
    '\t\t\t\t:i :s}\n'
    '\t\t\t:i :s}\n'
    '\t\t:i endif\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # the per-player rock tube starts hidden; shown where the DE attaches per-player health (not face-off types)
    'Script WoR_HUD_HUD_attach_widget_player_health [\n'
    '\t:i $WoR_HUD_HUD_attach_widget_player_health_orig$ isNull\n'
    '\t:i if $GotParam$$parent_id$\n'
    '\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$parent_id$\n'
    '\t\t\t:i $ResolveScreenElementID$$id$ = %GLOBAL%$parent_id$$param$ = $WoR_HUD_meter_id$\n'
    '\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$WoR_HUD_meter_id$$alpha$ = %i(1)\n'
    '\t\t:i endif\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_HUD_attach_widget_player_health_orig [\n'
    '\t:i $printf$%s("WoR_HUD: player health placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')
