"""Per-player WoR pieces for the 2-highway layout hud_2g (face-off, pro face-off, 2-player co-op / quickplay; user
2026-10-21: "in band, rock meter, star power tube and streak multiplier is kept"). Each player container (g1 / g2) of
our hud_2g copy gets three descs of ours, all authored in screen px for P1 (P2 = translated by wor_battle.p2_dx):

  - Star_Power -> wor_sp_mp_ghwor: the 1-player star power tube itself in a container scaled onto the right rail
    (sp_desc); fed by our HUD_attach_widget_player_star_power (six segments glow0..5) and run by the plugin's tube
    engine per tube (smooth fill, plasma, glows, burst, feathers).
  - BAND_side_meter -> wor_side_mp_ghwor: the WoR rock tube on the left rail (the battle tube textures; same highways),
    one LED per zone (SIDE_meter_red / yellow / green_ON_alpha) and the sliding needle: the DE drives an invisible
    stand-in on its 2-player path (script 0x3205f550: (0,0) (13,-28) (26,-58) (37,-84) at health 0 / .667 / 1.333 /
    2), the plugin places our needle on the WoR LED stops (anchor container found by its scale kMpNeedleAX/AY). The DE
    attaches it only where the mode has per-player health (not face-off types: WoR's versus has no rock meter), so its
    instance in hud_2g starts at alpha 0 and WoR_HUD_HUD_attach_widget_player_health shows it when attached.
  - player_meter -> wor_mult_mp_ghwor: the multiplier badge (this theme's WoR multiplier textures) with its five
    note-streak lights, right of the star power tube (WoR: the multiplier bubble right of each highway). In band
    scoring the DE writes the instrument icon into the x1 slot; the plugin puts our x1 badge back (SetTexture hook).
    The DE kills alias_player_multiplier in face-off types (GH:588-594); ours points at a hidden stand-in, so the
streak meter stays on every highway in face-off too (user 2026-10-21: each highway keeps its SP tube and streak meter).
"""
import math

import numpy as np

import wor_battle as B
import wor_versus as V
from desc_gen import E, desc

SP_NAME, SIDE_NAME, MULT_NAME = 'wor_sp_mp_ghwor', 'wor_side_mp_ghwor', 'wor_mult_mp_ghwor'
NEEDLE_TEX = 'WoR_HUD_mpneedle'            # same art as the battle needle, its own name (plugin)
DE_KNOTS_2P = ((0.0, 0.0), (13.0, -28.0), (26.0, -58.0), (37.0, -84.0))
ANCHOR_SCALE = (1.0313, 1.0313)            # unique: the plugin finds the anchor by it


def _dummy(lid, kind='SpriteElement'):
    return E(lid, kind, dims=(4, 4), alpha=0.0, z=0.0, **({'texture': 'WoR_HUD_blank'} if kind == 'SpriteElement'
                                                            else {'font': V.SCORE_FONT, 'text': '0x00000000', 'shadow': False}
                                                            if kind == 'TextBlockElement' else {}))


def _root(lid, kids, alpha=1.0):
    return E(lid, 'ContainerElement', dims=(1280, 720), just=(-1, -1), alpha=alpha, children=kids)


# ---- star power tube
SP_SEGMENTS = 6


def sp_transform():
    """(container pos, scale) putting the 1-player tube onto P1's multiplayer tube: the rail map is a uniform scale +
    shift (wor_battle.tube_maps keeps the 1-player angle), so the 1-player tube's own elements, in their own desc
    coordinates, sit in one scaled container (the 1-player desc is drawn GAME_CALIB off its coordinates)."""
    import preview_hud
    m = V.sp_map()
    k = float(m[0, 0])
    cal = preview_hud.GAME_CALIB['wor_band_meter_1g_ghwor']
    return (float(m[0, 2]) + k * cal[0], float(m[1, 2]) + k * cal[1]), k


def sp_desc():
    """The 1-player star power tube itself (every sp_* element: body, clip window + six fill segments, feathered top,
    glows, ready burst, marker), unchanged, in a container scaled onto the player's rail (user 2026-10-22: the same tube
    as quickplay on every player, tracked and animated by the plugin's tube engine, one state per tube). The DE's
    widget writes glow0..5 like the 1-player band meter (our HUD_attach_widget_player_star_power: the band's star
    power in band / co-op, the player's own in face-off and battle)."""
    import copy
    import wor_1g, desc_gen
    wor_1g.all_descs()
    src = desc_gen.ROOTS['wor_band_meter_1g_ghwor']
    meter = src                                   # the desc's root is meter_container itself
    kids = [copy.deepcopy(c) for c in meter.children if c.local_id.startswith('sp_')]
    pos, k = sp_transform()
    scaled = E('sp_scaled', 'ContainerElement', pos=pos, dims=(1280, 720), just=(-1, -1), scale=(k, k), children=kids)
    props = [(f'glow{i}_texture', f'sp_seg{i}', 'texture') for i in range(SP_SEGMENTS)]
    props += [(f'glow{i}_scale', f'sp_seg{i}', 'Scale') for i in range(SP_SEGMENTS)]
    return desc(SP_NAME, _root('sp_mp', [scaled]), props)


# ---- rock tube
def needle_knots():
    """Our needle positions (anchor units) at the WoR LED stops, and the anchor's screen position (health-0 stop)."""
    st = B.needle_stops()
    ax, ay = ANCHOR_SCALE
    return st[0], [((x - st[0][0]) / ax, (y - st[0][1]) / ay) for x, y in st]


def side_desc():
    (tc, (tw, th)) = B.tube_box()
    tube = (tw / B.SS, th / B.SS)
    anchor, knots = needle_knots()
    ax, ay = ANCHOR_SCALE
    nd = B._pow2(B.NEEDLE_BOX * B.SS) / B.SS
    mid = ((knots[1][0] + knots[2][0]) / 2, (knots[1][1] + knots[2][1]) / 2)
    kids = [
        E('rock_tube', 'SpriteElement', pos=tc, dims=tube, just=(0, 0), z=13.0, texture=B.TUBE_TEX['body']),
        E('side_meter_red_ON', 'SpriteElement', pos=tc, dims=tube, just=(0, 0), z=14.0, alpha=0.0, texture=B.TUBE_TEX['red']),
        E('side_meter_yellow_ON', 'SpriteElement', pos=tc, dims=tube, just=(0, 0), z=15.0, texture=B.TUBE_TEX['yellow']),
        E('side_meter_green_ON', 'SpriteElement', pos=tc, dims=tube, just=(0, 0), z=16.0, alpha=0.0, texture=B.TUBE_TEX['green']),
        E('needle_anchor', 'ContainerElement', pos=anchor, dims=(4, 4), just=(-1, -1), scale=ANCHOR_SCALE, z=18.0, children=[
            E('needle_src', 'SpriteElement', dims=(4, 4), just=(0, 0), z=18.0, alpha=0.0, texture='WoR_HUD_blank'),
            E('side_meter_needle', 'SpriteElement', pos=mid, dims=(nd / ax, nd / ay), just=(0, 0), z=18.5,
              texture=NEEDLE_TEX)]),
        _dummy('side_meter_red_glow'), _dummy('side_meter_red_rgba_sink'),
    ]
    props = [('side_meter_needle_pos', 'needle_src', 'Pos'), ('side_meter_needle_scale', 'needle_src', 'Scale'),
             ('SIDE_meter_red_ON_alpha', 'side_meter_red_ON', 'alpha'),
             ('SIDE_meter_green_ON_alpha', 'side_meter_green_ON', 'alpha'),
             ('SIDE_meter_yellow_ON_alpha', 'side_meter_yellow_ON', 'alpha'),
             ('SIDE_meter_red_ON_rgba', 'side_meter_red_rgba_sink', 'rgba'),
             ('side_meter_red_glow_rgba', 'side_meter_red_glow', 'rgba')]
    return desc(SIDE_NAME, _root('side_meter_mp', kids), props)


# ---- multiplier
def _sp_tube_change():
    """(rotation delta deg, scale) of the 1-player star power tube mapped onto P1's multiplayer tube."""
    import wor_1g
    m = V.sp_map()
    a, b = np.array(wor_1g.RIGHT.at(wor_1g.LED_BOTTOM)), np.array(wor_1g.RIGHT.at(wor_1g.LED_TOP))
    a2, b2 = np.array(B.apply(m, a)), np.array(B.apply(m, b))
    ang = lambda v: math.degrees(math.atan2(v[0], -v[1]))
    return ang(b2 - a2) - ang(b - a), float(np.hypot(*(b2 - a2)) / np.hypot(*(b - a)))


def mult_desc():
    """The 1-player multiplier badge (WoR's nixie with its stick on the star power tube's top, and the five note-streak
    lights along the stick) mapped onto each multiplayer tube like the tube itself."""
    import preview_hud
    import wor_1g, desc_gen
    wor_1g.all_descs()
    src = desc_gen.ROOTS['wor_mult_1g_ghwor']
    cal = preview_hud.GAME_CALIB['wor_mult_1g_ghwor']
    m = V.sp_map()
    dr, k = _sp_tube_change()
    kids = []
    for e in src.children:
        if e.local_id == 'nixie' or e.local_id.startswith('light'):
            p = B.apply(m, (e.pos[0] + wor_1g.G1[0] + cal[0], e.pos[1] + wor_1g.G1[1] + cal[1]))
            kids.append(E(e.local_id, 'SpriteElement', pos=p, dims=e.dims, just=e.just, scale=(e.scale[0] * k, e.scale[1] * k),
                          rot=e.rot + dr, z=6.0 if e.local_id == 'nixie' else 6.5, texture=e.extra['texture']))
    kids += [_dummy('note_streak', 'TextBlockElement'), _dummy('mult_bg'), _dummy('nixie_rgba_sink'),
             *[_dummy(f'glow{i}') for i in range(3)], _dummy('mult_die_standin')]
    root = _root('mult_mp', kids)
    props = [('note_streak_text', 'note_streak', 'text')]
    props += [(f'light{i}_texture', f'light{i}', 'texture') for i in range(5)]
    for i in range(3):
        props += [(f'glow{i}_texture', f'glow{i}', 'texture'), (f'glow{i}_scale', f'glow{i}', 'Scale')]
    props += [('nixie_texture', 'nixie', 'texture'), ('mult_bg_alpha', 'mult_bg', 'alpha'),
              ('nixie_rgba', 'nixie_rgba_sink', 'rgba')]
    return desc(MULT_NAME, root, props, aliases=[('alias_player_multiplier', 'mult_die_standin')])


def descs():
    return [sp_desc(), side_desc(), mult_desc()]


def textures(battle_textures):
    """Our own name for the multiplayer needle (the battle needle's art)."""
    return {NEEDLE_TEX: battle_textures[B.NEEDLE_TEX]}


def sources():
    return {NEEDLE_TEX: {'src': 'WoR_HUD_needle_glow (mapped like the battle needle)', 'box': None, 'flip': False}}


# ---- hud_2g edits
def _container_topleft(d, lid):
    import re
    a, b = V._element_bounds(d, lid)
    blk = d[a:b]
    pos = [float(v) for v in re.search(r'StructFloatX2 Pos\s*\{\s*Floats \[([-\d.]+), ([-\d.]+)\]', blk).groups()]
    dims = [float(v) for v in re.search(r'StructFloatX2 dims\s*\{\s*Floats \[([-\d.]+), ([-\d.]+)\]', blk).groups()]
    just = [float(v) for v in re.search(r'StructArray just\s*\{\s*ArrayFloat\s*\[\s*([-\d.]+)\s+([-\d.]+)', blk).groups()]
    return (pos[0] - (just[0] + 1) / 2 * dims[0], pos[1] - (just[1] + 1) / 2 * dims[1])


def _append_children(d, lid, blocks):
    """Insert element blocks at the end of element lid's children array (indices of existing children unchanged)."""
    import desc_edit
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


def _set_player_meter(d, g, offset, scale=None):
    """player_meter of container g: our desc, placed so its screen-authored content lands right (scale: the element's
    Scale, for highways smaller than the 2-player ones)."""
    import re
    import desc_edit
    a, b = V._element_bounds(d, g)
    blk = d[a:b]
    m = re.search(r'StructQBKey local_id = player_meter\s*\n', blk)
    pa, pb = desc_edit._block_bounds(blk, m.start())
    p = blk[pa:pb]
    p, n1 = re.subn(r'StructString desc = "[^"]*"', f'StructString desc = "{MULT_NAME}"', p, count=1)
    p, n2 = re.subn(r'StructFloatX2 Pos\s*\{\s*Floats \[[-\d.]+, [-\d.]+\]',
                    f'StructFloatX2 Pos\n{{\n\tFloats [{offset[0]:.5f}, {offset[1]:.5f}]', p, count=1)
    p, n3 = re.subn(r'(StructArray just\s*\{\s*ArrayFloat\s*\[)\s*[-\d.]+\s+[-\d.]+', r'\g<1>\n-1.00000\n-1.00000', p, count=1)
    p, n4 = re.subn(r'(StructArray pos_anchor\s*\{\s*ArrayFloat\s*\[)\s*[-\d.]+\s+[-\d.]+', r'\g<1>\n-1.00000\n-1.00000', p, count=1)
    p = re.sub(r'StructFloat rot_angle = [-\d.]+', 'StructFloat rot_angle = 0.00', p, count=1)
    if scale is not None:
        p, n5 = re.subn(r'StructFloatX2 Scale\s*\{\s*Floats \[[-\d.]+, [-\d.]+\]',
                        f'StructFloatX2 Scale\n{{\n\tFloats [{scale:.5f}, {scale:.5f}]', p, count=1)
        assert n5 == 1, (g, 'Scale')
    assert n1 == n2 == n3 == n4 == 1, (g, n1, n2, n3, n4)
    blk = blk[:pa] + p + blk[pb:]
    return d[:a] + blk + d[b:]


def _hide_child(d, g, child):
    """alpha 0 on container g's child (local ids repeat across containers)."""
    import re
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


# measured 2026-10-22 on the user's face-off screenshot (spacing 22, plugin 1.39): every piece inside g1 / g2 landed
# 21-28 px right of the rail model (battle pieces, outside these containers, landed on it), so the offset into the
# centred player containers is off by this much; corrected once for the SP tube, streak meter and rock tube
MP_DX = -24.0
# measured 2026-10-22 on the user's 1.39 band frame (2 instruments, hud_2g; canvas = (X - 250) * 0.853 of the 2000 px
# ultrawide shot): the rock tube sat +74 right of the rail model on both highways (slope = the model's, the 1-player
# angle), the star power tube +16; after MP_DX the rock tube is still ~50 right, inside the highway on the first gem
ROCK_MP_DX = -50.0


def edit_two_highways(d):
    """The 2-highway layouts (hud_2g: face-off / pro face-off / co-op; hud_2g1v: two instruments + vocals): the
    player containers follow the highways (wor_battle.SEP apart) and get our star power tube, rock tube and multiplier;
    the WT+ copy's own star power child (star_power_1g, not wired by the DE: its local id isn't Star_Power) hides."""
    d = V._shift_pos(d, 'g1', -B.SEP)
    d = V._shift_pos(d, 'g2', B.SEP)
    for p, g in ((1, 'g1'), (2, 'g2')):
        d = _hide_child(d, g, 'star_power_1g')
        tl = _container_topleft(d, g)
        shift = 0.0 if p == 1 else B.p2_dx()
        off = (shift - tl[0] + MP_DX, -tl[1])    # desc content in P1 screen px -> this container
        d = _set_player_meter(d, g, off)
        new = [E('Star_Power', 'descinterface', pos=off, dims=(1280, 720), just=(-1, -1), z=2.0, desc=SP_NAME).render(0),
               E('BAND_side_meter', 'descinterface', pos=(off[0] + ROCK_MP_DX, off[1]), dims=(1280, 720), just=(-1, -1), z=3.0, alpha=0.0,
                 desc=SIDE_NAME).render(0)]     # hidden until the DE attaches health (WoR_HUD_HUD_attach_widget_player_health)
        d = _append_children(d, g, new)
    return d


# ---- hud_3g1v (3 instruments, with or without vocals; 4-player band): the 2-player pieces mapped onto each highway
# Rails measured on the bot captures of 2026-10-22 (tests/capture_band.py, canvas = the centred 16:9 part of the
# 2560x1080 shot): the orange border's centre line, ((x, y) at y 450, (x, y) at y 700). hud_3g and hud_3g1v place the
# highways identically. The 2-player pieces are placed right in game (2g capture), so each 3-highway set is that set
# under one uniform scale + shift (the 1-player angle kept, user rule) fitted on the rails, points matched by their
# fraction of the highway between the vanishing point and the strikeline.
RAILS_2G_P1 = (((275.0, 450.0), (163.5, 700.0)), ((500.5, 450.0), (612.0, 700.0)))
RAILS_3G = [(((136.0, 450.0), (45.0, 700.0)), ((333.5, 450.0), (424.5, 700.0))),
            (((541.0, 450.0), (450.0, 700.0)), ((738.5, 450.0), (829.5, 700.0))),
            (((946.0, 450.0), (855.0, 700.0)), ((1143.5, 450.0), (1234.5, 700.0)))]
STRIKE_Y = 635.0                           # gem rings, both layouts


def _vanish_y(rails):
    (l0, l1), (r0, r1) = rails
    w0, w1 = r0[0] - l0[0], r1[0] - l1[0]
    return l0[1] - w0 * (l1[1] - l0[1]) / (w1 - w0)


def highway_map(dst, src=RAILS_2G_P1):
    """(s, (tx, ty)): screen p on the 2-player P1 highway -> s * p + t on the highway with rails dst (least squares)."""
    yv_s, yv_d = _vanish_y(src), _vanish_y(dst)
    a, b = [], []
    for side in (0, 1):
        for y in np.linspace(520.0, 660.0, 12):          # where the tubes and the multiplier sit
            f = (y - yv_s) / (STRIKE_Y - yv_s)
            yd = yv_d + f * (STRIKE_Y - yv_d)
            xs, xd = B._line_x(src[side], y), B._line_x(dst[side], yd)
            a += [[xs, 1.0, 0.0], [y, 0.0, 1.0]]
            b += [xd, yd]
    s, tx, ty = np.linalg.lstsq(np.array(a), np.array(b), rcond=None)[0]
    return float(s), (float(tx), float(ty))


def edit_three_highways(d):
    """hud_3g1v: our star power tube, rock tube and multiplier on g1..g3 (the DE's own player_meter, with its tiny
    multiplier and pink streak lights, replaced; the layout has no Star_Power / BAND_side_meter children, ours are
    added under the DE's local ids so its attach scripts find them)."""
    for g, rails in zip(('g1', 'g2', 'g3'), RAILS_3G):
        s, (tx, ty) = highway_map(rails)
        tl = _container_topleft(d, g)
        # 2-player P1 content (its own screen px) -> s * p + t here. MP_DX / ROCK_MP_DX are NOT carried over: they
        # correct hud_2g only (its highways are moved apart by our x_offset_p2 change); with them the 3-highway
        # capture of 2026-10-22 showed the SP tubes ~17 px and the rock tubes ~65 px left of their rails, which is
        # s * MP_DX and s * (MP_DX + ROCK_MP_DX) within a few px
        off = (tx - tl[0], ty - tl[1])
        d = _set_player_meter(d, g, off, scale=s)
        new = [E('Star_Power', 'descinterface', pos=off, dims=(1280, 720), just=(-1, -1), scale=(s, s), z=2.0,
                 desc=SP_NAME).render(0),
               E('BAND_side_meter', 'descinterface', pos=off, dims=(1280, 720),
                 just=(-1, -1), scale=(s, s), z=3.0, alpha=0.0, desc=SIDE_NAME).render(0)]
        d = _append_children(d, g, new)
    return d


SCRIPTS = (
    # the DE's HUD_attach_widget_player_star_power, replaced (plugin swap): with this theme six segments (the 1-player
    # tube copy, wor_mp.sp_desc), the band's star power in band / co-op (user 2026-10-22: every player's tube shows the
    # band's), each player's own in face-off types, battle and boss battles; other themes: the DE's own three segments
    'Script WoR_HUD_HUD_attach_widget_player_star_power [\n'
    '\t:i $getplayerinfo$%GLOBAL%$player$$checksum$\n'
    '\t:i $ResolveScreenElementID$$id$ = %GLOBAL%$parent_id$$param$ = $id$\n'
    '\t:i if (~$current_num_players$ > %i(1))\n'
    '\t\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$parent_id$$child$ = $sp_mp$:s}\n'
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
