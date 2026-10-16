"""Battle mode (p2_battle) in the WoR style (mock verify/mock_battle_v6.jpg, approved 2026-10-16).

The DE draws battle with a GH3-style hud_2d layout: the theme row's 0x6bd128d8 names it (default
battle_hud_2d_elements). Its rock container holds the rock dial (the battle health meter: the DE drives
HUD2D_rock_needle and the BG/lights alphas by element id) and the attack-slot frame. Our layout WoR_HUD_battle keeps
every element id and swaps the art:
  - health: WoR's band battle meter arc (HUD_band_battle_meter_*), its needle as the rock needle, beside the highway;
  - attack slots: the DE's own three slot rings (HUD_2p_battle_frame, pixels unchanged, cut apart), stacked along the
    highway's outer rail above the health arc, big at the bottom;
  - name plate (theme c2bf76cf): the DE's gamertag desc with WoR's band lobby gamertag bar (tinted by the team colour).
The attack alerts stay stock (the DE places them over the highway).

The attack cards themselves are created by guitar_battle in screen space at
battle_hud_2d_elements.rock_pos + card_*_off (a global, not the theme layout), so WoR_HUD_create_battle_alert_frames
(the plugin wraps the DE's create_battle_alert_frames, run when the battle HUD is built) moves those offsets into our
slots while this theme is on and puts the stock ones back otherwise.

Coordinates: the hud_2d root container is scaled by the layout's Scale (0.75), so layout positions are screen / 0.75;
the cards are plain 1280x720 screen positions. rock_pos stays stock (280, 100) / (1180, 100): the gamertag plates are
placed relative to the rock container and must not move. P2 mirrors P1 around x = 640.
"""
import os

import paths

NAME = 'WoR_HUD_battle'                 # the layout struct (theme row 0x6bd128d8)
FLAG = 'WoR_HUD_battle_hud'             # theme flag read by the wrapper
GAMERTAG = 'hud_gamertag_ghwor'         # theme c2bf76cf (desc uidesc_hud_gamertag_ghwor)
SCALE = 0.75
ROCK_POS = {1: (280.0, 100.0), 2: (1180.0, 100.0)}
STOCK_CARD_OFFS = {                     # guitar_battle's stock card offsets (DE themes' battle layouts)
    'card_1_off_p1': (26.0, 114.0), 'card_2_off_p1': (-44.0, 11.0), 'card_3_off_p1': (-53.0, 37.0),
    'card_1_off_p2': (-200.0, 114.0), 'card_2_off_p2': (46.0, 13.0), 'card_3_off_p2': (53.0, 39.0),
}

# ---- source textures (extracted game files)
DE_FRAME = os.path.join(paths.DE_EXTRACT, 'z_in_game_png', 'HUD_2p_battle_frame.png')        # DE z_in_game
WOR_ARC = {k: os.path.join(paths.WOR_PNG, f'HUD_band_battle_meter_{k}.png') for k in ('OFF', 'shadow', 'amber_ON', 'needle')}
WOR_GAMERTAG = os.path.join(paths.WOR_EXTRACT, 'band_lobby_png', 'bandlobby_bord_gamertag_color.png')   # Xbox, x360img

# slot rings in the DE texture: centre, inner and outer radius (alpha profile), texture px
RINGS = {'big': (127.0, 178.5, 36.0, 45.5), 'mid': (188.0, 191.0, 22.0, 27.5), 'small': (198.0, 228.5, 13.0, 18.5)}
RING_TEX = {k: f'WoR_HUD_bslot_{k}' for k in RINGS}
ARC_TEX = {'off': 'WoR_HUD_barc_off', 'frame': 'WoR_HUD_barc_frame', 'needle': 'WoR_HUD_barc_needle',
           'green': 'WoR_HUD_barc_green', 'yellow': 'WoR_HUD_barc_yellow', 'red': 'WoR_HUD_barc_red'}
ARC_RGB = {'green': (70, 220, 70), 'yellow': (240, 210, 40), 'red': (230, 40, 30)}
GAMERTAG_TEX = 'WoR_HUD_gamertag_bg'
ARC_PIVOT_TEX = (129.5, 193.0)          # WoR arc centre in its 256 px texture (OFF / shadow bbox)

# ---- P1 layout in screen px (P2 = mirror). Estimated from the user's DE battle screenshot: P1's outer rail runs
# about (246, 394) -> (110, 668); everything sits just outside it. Calibrate from an in-game screenshot.
RAIL_TOP, RAIL_BOTTOM = (246.0, 394.0), (110.0, 668.0)
ARC_PIVOT = (62.0, 640.0)               # health arc centre (its flat bottom)
ARC_SIZE = 150.0                        # drawn size of the 256 px arc textures
SLOTS = {                               # centre, drawn scale of the ring texture (big at the bottom, touching)
    'big': ((127.0, 548.0), 0.9),
    'mid': ((164.0, 500.0), 1.0),
    'small': ((191.0, 463.0), 1.1),
}
DEFAULT_ICON = {'big': 60.0, 'mid': 40.0, 'small': 26.0}     # icon_attack_default2 in an empty slot


def rail_x(y):
    (x0, y0), (x1, y1) = RAIL_TOP, RAIL_BOTTOM
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def ring_canvas(k):
    n = 2 * int(RINGS[k][3] + 2) + 1
    return 1 << (n - 1).bit_length()


def textures():
    """{our texture name: PIL image} for the pak."""
    from PIL import Image, ImageDraw
    import numpy as np
    out = {}
    frame = Image.open(DE_FRAME).convert('RGBA')
    fa = np.array(frame)
    fy, fx = np.mgrid[0:256, 0:256]
    order = ['big', 'mid', 'small']                        # drawn on top of each other in this order in the DE texture

    def band(k):
        cx, cy, r_in, r_out = RINGS[k]
        d = np.hypot(fx - cx, fy - cy)
        return (d >= r_in - 1.0) & (d <= r_out + 1.0)
    for k, (cx, cy, r_in, r_out) in RINGS.items():
        half = int(r_out + 2)
        x0, y0 = int(cx) - half, int(cy) - half
        a = fa.copy()
        mine = band(k)
        # pixels the rings above this one cover (or never drew): taken from the same ring's mirrored side
        hidden = mine & (a[..., 3] < 180)
        for j in order[:order.index(k)]:
            hidden |= mine & band(j)
        for mx, my in ((True, False), (False, True), (True, True)):
            sx = np.clip(np.round(2 * cx - fx if mx else fx).astype(int), 0, 255)
            sy = np.clip(np.round(2 * cy - fy if my else fy).astype(int), 0, 255)
            ok = hidden & ~hidden[sy, sx] & (fa[sy, sx, 3] >= 180)
            a[ok] = fa[sy[ok], sx[ok]]
            hidden &= ~ok
        a[..., 3] = np.where(mine, a[..., 3], 0)            # the ring only: no dial or neighbour pixels
        a = a[y0:y0 + 2 * half + 1, x0:x0 + 2 * half + 1]
        ring = Image.fromarray(a)
        canvas = Image.new('RGBA', (ring_canvas(k),) * 2)           # power-of-two texture, ring centred
        o = (canvas.width - ring.width) // 2
        canvas.alpha_composite(ring, (o, o))
        out[RING_TEX[k]] = canvas
    out[ARC_TEX['off']] = Image.open(WOR_ARC['OFF']).convert('RGBA')
    out[ARC_TEX['frame']] = Image.open(WOR_ARC['shadow']).convert('RGBA')
    out[ARC_TEX['needle']] = Image.open(WOR_ARC['needle']).convert('RGBA')
    # lit arc: WoR's quarter (amber_ON, white) and its mirror make the full semicircle; tinted per health colour
    q = Image.open(WOR_ARC['amber_ON']).convert('RGBA')
    full = Image.new('RGBA', (256, 256))
    qx, qy = int(ARC_PIVOT_TEX[0] - 116), int(ARC_PIVOT_TEX[1] - 117)     # the quarter's centre sits at ~(116, 117)
    full.alpha_composite(q, (qx, qy))
    full.alpha_composite(q.transpose(Image.FLIP_LEFT_RIGHT), (256 - qx - 128, qy))
    for k, rgb in ARC_RGB.items():
        a = np.array(full).astype(np.float32)
        lum = a[..., :3].mean(axis=2, keepdims=True) / 255.0
        a[..., :3] = lum * np.array(rgb, np.float32)
        out[ARC_TEX[k]] = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    out[GAMERTAG_TEX] = Image.open(WOR_GAMERTAG).convert('RGBA')
    return out


def sources():
    s = {RING_TEX[k]: {'src': DE_FRAME, 'ring': list(v)} for k, v in RINGS.items()}
    s.update({ARC_TEX['off']: {'src': WOR_ARC['OFF']}, ARC_TEX['frame']: {'src': WOR_ARC['shadow']},
              ARC_TEX['needle']: {'src': WOR_ARC['needle']}, GAMERTAG_TEX: {'src': WOR_GAMERTAG}})
    s.update({ARC_TEX[k]: {'src': WOR_ARC['amber_ON'], 'mirror_full': True, 'tint': list(rgb)} for k, rgb in ARC_RGB.items()})
    for v in s.values():
        v.setdefault('box', None)
        v.setdefault('flip', False)
    return s


# ---- layout struct
def _mirror(p):
    return (1280.0 - p[0], p[1])


def _local(p, player):
    rx, ry = ROCK_POS[player]
    return ((p[0] - rx * SCALE) / SCALE, (p[1] - ry * SCALE) / SCALE)


def _vec(name, v, ind):
    return f'{ind}StructFloatX2 {name}\n{ind}{{\n{ind}\tFloats [{v[0]:.5f}, {v[1]:.5f}]\n{ind}}}\n'


def _elem(eid, tex, screen_pos, screen_dims, z, just=(0.5, 0.5), alpha=None):
    ind = '\t\t\t\t\t'
    t = (f'\t\t\t\tStructHeader\n\t\t\t\t{{\n{ind}StructQBKey element_id = {eid}\n'
         f'{ind}StructQBKey element_parent = HUD2D_rock_container\n{ind}StructQBKey texture = {tex}\n')
    t += _vec('pos_off', _local(screen_pos, 1), ind)
    t += _vec('pos_off_p2', _local(_mirror(screen_pos), 2), ind)
    t += _vec('dims', (screen_dims[0] / SCALE, screen_dims[1] / SCALE), ind)
    t += f'{ind}StructFloat zoff = {z}\n'
    t += f'{ind}StructArray just\n{ind}{{\n{ind}\tArrayFloat\n{ind}\t[\n{ind}\t\t{just[0]:.6f}\n{ind}\t\t{just[1]:.6f}\n{ind}\t]\n{ind}}}\n'
    if alpha is not None:
        t += f'{ind}StructInt alpha = {alpha}\n'
    return t + '\t\t\t\t}\n'


def card_offsets():
    """guitar_battle's card offsets for our slots: card 1 = rock_pos + off, cards 2 / 3 relative to card 1."""
    c = {k: SLOTS[k][0] for k in SLOTS}
    out = {}
    for p in (1, 2):
        big, mid, small = (c[k] if p == 1 else _mirror(c[k]) for k in ('big', 'mid', 'small'))
        rx, ry = ROCK_POS[p]
        out[f'card_1_off_p{p}'] = (big[0] - rx, big[1] - ry)
        out[f'card_2_off_p{p}'] = (mid[0] - big[0], mid[1] - big[1])
        out[f'card_3_off_p{p}'] = (small[0] - big[0], small[1] - big[1])
    return out


def layout_struct():
    k = ARC_SIZE / 256.0
    arc_c = (ARC_PIVOT[0] + k * (128 - ARC_PIVOT_TEX[0]), ARC_PIVOT[1] + k * (128 - ARC_PIVOT_TEX[1]))
    arc = (ARC_SIZE, ARC_SIZE)
    hdr = '\t\t'
    t = f'SectionStruct {NAME}\n{{\n\tStructHeader\n\t{{\n'
    t += _vec('offset4by3_rock', (0, 0), hdr) + _vec('offset4by3_score', (0, 0), hdr)
    t += _vec('offscreen_rock_pos_p1', (-420.0, 100.0), hdr) + _vec('offscreen_rock_pos_p2', (1880.0, 100.0), hdr)
    offs = card_offsets()
    for p in (1, 2):
        t += _vec(f'rock_pos_p{p}', ROCK_POS[p], hdr)
        for n in (1, 2, 3):
            t += _vec(f'card_{n}_off_p{p}', offs[f'card_{n}_off_p{p}'], hdr)
        for n, key in ((2, 'mid'), (3, 'small')):
            pos = SLOTS[key][0] if p == 1 else _mirror(SLOTS[key][0])
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
    # health arc: unlit base, the three health colours the DE fades (green 16 / yellow 15 / red 14), frame on top
    t += _elem('WoR_HUD_barc_base', ARC_TEX['off'], arc_c, arc, 13)
    t += _elem('HUD2D_rock_BG_green', ARC_TEX['green'], arc_c, arc, 16)
    t += _elem('HUD2D_rock_BG_red', ARC_TEX['red'], arc_c, arc, 14)
    t += _elem('HUD2D_rock_BG_yellow', ARC_TEX['yellow'], arc_c, arc, 15)
    t += _elem('HUD2D_rock_body', ARC_TEX['frame'], arc_c, arc, 20)
    for eid in ('HUD2D_rock_lights_all', 'HUD2D_rock_lights_green', 'HUD2D_rock_lights_red', 'HUD2D_rock_lights_yellow'):
        t += _elem(eid, 'WoR_HUD_blank', arc_c, (4.0, 4.0), 17, alpha=0)
    t += _elem('HUD2D_rock_needle', ARC_TEX['needle'], ARC_PIVOT, (32.0 * k, 256.0 * k), 18.5)
    # attack slots: the DE rings over the cards (z 19), the default icon inside each empty slot
    for key in ('big', 'mid', 'small'):
        pos, s = SLOTS[key]
        size = ring_canvas(key) * s
        t += _elem(f'WoR_HUD_bslot_{key}', RING_TEX[key], pos, (size, size), 20)
    for n, key in ((1, 'big'), (2, 'mid'), (3, 'small')):
        d = DEFAULT_ICON[key]
        t += _elem(f'HUD2D_battle_default_icon2_{n}', 'icon_attack_default2', SLOTS[key][0], (d, d), 18.9)
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
    def changes(offs):
        return ''.join(f'\t\t:i $change$$structurename$ = $battle_hud_2d_elements$${k}$ = %vec2({v[0]:.1f},{v[1]:.1f})\n'
                       for k, v in offs.items())
    return ('Script WoR_HUD_create_battle_alert_frames [\n'
            f'\t:i if $[4c1beb8d]$$value$ = ${FLAG}$\n'
            + changes(card_offsets()) +
            '\t\t:i $printf$%s("WoR_HUD: battle attack cards moved into the WoR slots")\n'
            '\t:i else \n'
            + changes(STOCK_CARD_OFFS) +
            '\t:i endif\n'
            '\t:i $WoR_HUD_create_battle_alert_frames_orig$ isNull\n'
            '\t:i endfunction\n]\n\n'
            # placeholder: the plugin moves the DE script's data here
            'Script WoR_HUD_create_battle_alert_frames_orig [\n'
            '\t:i $printf$%s("WoR_HUD: battle alert frames placeholder ran, plugin swap missing")\n'
            '\t:i endfunction\n]\n')


def theme_extra():
    return (f'\t\t\t\tStructQBKey 0x6bd128d8 = {NAME}\n'
            f'\t\t\t\tStructString c2bf76cf = "{GAMERTAG}"\n'
            f'\t\t\t\tStructInt {FLAG} = 1\n')
