"""Per-player WoR pieces for the 2-highway layout hud_2g (face-off, pro face-off, 2-player co-op / quickplay; user
2026-10-21: "in band, rock meter, star power tube and streak multiplier is kept"). Each player container (g1 / g2) of
our hud_2g copy gets three descs of ours, all authored in screen px for P1 (P2 = translated by wor_battle.p2_dx):

  - Star_Power -> wor_sp_mp_ghwor: the WoR star power tube on the highway's right rail (wor_versus' mapped tube) with
    three fill segments glow0..2 (HUD_attach_widget_player_star_power drives a child literally named Star_Power with
    setubes on the player's own starpower_amount, in every mode with more than one player; research
    docs/research/de_layouts.md 8). WoR's fill under the WoR_HUD_vsseg names (plugin: kept out of the smooth fill).
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
def sp_desc():
    (tc, (tw, th)) = V.sp_tube_box()
    kids = [E('sp_tube', 'SpriteElement', pos=tc, dims=(tw / B.SS, th / B.SS), just=(0, 0), z=11.0, texture=V.SPTUBE_TEX)]
    for i, (a, rot, w, h) in enumerate(V.segments(3)):
        # initial scale (1, 1): if the widget takes the element's own scale as its default, the fill still spans the tube
        kids.append(E(f'glow{i}', 'SpriteElement', pos=a, dims=(w, h), just=(0, 1), scale=(1.0, 1.0), rot=rot, z=11.5,
                      texture=V.SEG_TEX, blend='Add'))
    props = []
    for i in range(3):
        props += [(f'glow{i}_texture', f'glow{i}', 'texture'), (f'glow{i}_scale', f'glow{i}', 'Scale')]
    return desc(SP_NAME, _root('sp_mp', kids), props)


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


def _set_player_meter(d, g, offset):
    """player_meter of container g: our desc, placed so its screen-authored content lands right."""
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
        off = (shift - tl[0], -tl[1])            # desc content in P1 screen px -> this container
        d = _set_player_meter(d, g, off)
        new = [E('Star_Power', 'descinterface', pos=off, dims=(1280, 720), just=(-1, -1), z=2.0, desc=SP_NAME).render(0),
               E('BAND_side_meter', 'descinterface', pos=off, dims=(1280, 720), just=(-1, -1), z=3.0, alpha=0.0,
                 desc=SIDE_NAME).render(0)]     # hidden until the DE attaches health (WoR_HUD_HUD_attach_widget_player_health)
        d = _append_children(d, g, new)
    return d


SCRIPTS = (
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
