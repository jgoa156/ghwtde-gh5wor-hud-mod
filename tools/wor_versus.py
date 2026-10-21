"""Face-Off / Pro Face-Off (2 players) in the WoR versus style (user 2026-10-21; research docs/MODES_RULES.md).

The DE builds both with the hud_2g layout (shared with 2-player co-op / quickplay) and fills its versus meter, the
`HUD_band_battle` descinterface (alias alias_faceoff_meter), with HUD_attach_widget_band_faceoff_meter. That widget only
writes these props (docs/research/de_layouts.md 5): hud_band_battle_meter_needle_rot_angle (faceoff_ratio 1..-1 ->
-51.5..51.5 deg), hud_band_battle_meter_amber_on_alpha (1 when P1 leads by 0.1), ..._violet_on_alpha (P2 leads),
score_1_text / score_2_text, hud_bb_multiplier_nixie_1/2_texture (the DE's nixie names, fixed in the script),
fill_1_1..6 / fill_2_1..6 _texture / _scale (each player's star power, setubes, default scale (1, 1): scale (1, fill)),
p1 / p2_streak_number_text. Our desc HUD_band_battle_ghwor is WoR's versus meter (uidesc_HUD_band_battle: dial with
team-coloured glows + needle, a score bar per player with the team stripe) plus WoR's per-player pieces the DE can feed:
  - placing: WoR's badge (HUD_place_icon_back/front + "1st" / "2nd" in WoR's text font, baked) at each highway; the
    leader's "1st" badge and starburst (WoR shows the burst for rank 1 only) sit in a container driven by the amber /
    violet alpha, over a static "2nd" badge (a tie shows both "2nd");
  - star power: a WoR tube on each highway's right rail (the 1-player tube mapped like the battle tubes,
    tools/wor_battle.py) filled by the six fill_N_k segments (WoR's SP fill under the WoR_HUD_vsseg names, which the
    plugin keeps out of its single-tube smooth fill);
  - multiplier: the DE's nixie on the score bar's outer end;
  - no rock meter (the DE kills the band meter in face-off types).
Highways: the same spacing as battle (WoR_HUD_get_highway_pos_and_scale moves every 2-highway layout by SEP).
The meter starts at alpha 0 in every layout of ours (the user's HUDBossFOMeter=1 keeps it alive, unattached, in band /
co-op, where it showed "01234567"); WoR_HUD_HUD_attach_widget_band_faceoff_meter shows it when the DE attaches it.
"""
import math
import os

import numpy as np

import paths
import wor_battle as B
from desc_gen import E, desc

NAME = 'HUD_band_battle_ghwor'
WOR_UI = os.path.join(paths.WOR_EXTRACT, 'ui_shared_png')
WOR_ZIG = os.path.join(paths.WOR_EXTRACT, 'z_in_game_png2')
TEX = {   # ours -> extracted WoR png
    'WoR_HUD_vs_dial': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_OFF.png'),
    'WoR_HUD_vs_glow_l': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_amber_ON.png'),
    'WoR_HUD_vs_glow_r': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_violet_ON.png'),
    'WoR_HUD_vs_needle': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_needle.png'),
    'WoR_HUD_vs_score': os.path.join(WOR_ZIG, 'HUD_band_battle_score.png'),
    'WoR_HUD_vs_score_back': os.path.join(WOR_ZIG, 'HUD_band_battle_score_back.png'),
    'WoR_HUD_vs_stripe': os.path.join(WOR_UI, 'vocal_meter_color_stripe.png'),
    'WoR_HUD_starburst': os.path.join(WOR_UI, 'starburst_256.png'),
}
RANK_TEX = {1: 'WoR_HUD_rank_1', 2: 'WoR_HUD_rank_2'}
PLACE_BACK = os.path.join(WOR_UI, 'HUD_place_icon_back.png')
PLACE_FRONT = os.path.join(WOR_UI, 'HUD_place_icon_front.png')
SPTUBE_TEX = 'WoR_HUD_vs_sptube'
SEG_TEX = 'WoR_HUD_vsseg'                  # the plugin renames the DE's fill names to these (not its smooth fill)
SEG_NAMES = (('hud_rock_tube_glow_full', 'WoR_HUD_vsseg'), ('hud_rock_tube_glow_full_b', 'WoR_HUD_vsseg_b'))
# WoR's team colours on its versus meter (uidesc_HUD_band_battle: left glow + stripe, right glow + stripe)
P_RGBA = {1: (228, 61, 12, 255), 2: (87, 149, 229, 255)}
SP_NUDGE = np.array((-15.0, 0.0))          # the right rail's tube, towards the highway (see wor_battle.ROCK_NUDGE)
SCORE_FONT = 'WoR_HUD_num_a1'
NIXIE_K = 0.30                             # our multiplier badges: the 154x137 art top-left in a 256 px texture
NIXIE_ART = (154.0, 137.0)                 # (the plugin maps the DE's stock nixie names to them, kNixieMap)
STREAK_SQ_X = 157.0                         # centre of the score bar art's first square (texture px)
SCORE_K = 0.30                             # score numerals (0.62 overflowed the bar, 0.38 still too big: user 2026-10-21)

# ---- layout (screen px)
DIAL_C = (640.0, 322.0)
DIAL_K = 0.62                              # the 256 px dial art
BAR_K = 0.62                               # the 512x64 score bar art (visible 268 px)
BAR_Y = 352.0
BAR_GAP = 8.0                              # between the dial's outer edge and a bar's inner end
RANK_D = 78.0                              # the badge's 128 px texture: its square (66 px of it) ~40 px on screen
RANK_FACE = (38, 36, 94, 90)               # the square's inner face in the 128 px badge art (the text fits in it)
RANK_BURST = 120.0
RANK_Y = 430.0                             # badge centre height, outside each highway's left rail


def highway_top_centre(p):
    x = (B._line_x(B.RAIL_L, B.TOP_2P) + B._line_x(B.RAIL_R, B.TOP_2P)) / 2 - B.SEP
    return (x if p == 1 else x + B.p2_dx(), B.TOP_2P)


def _p2(pt, p):
    return pt if p == 1 else (pt[0] + B.p2_dx(), pt[1])


# ---- star power tube (P1; P2 translated)
def sp_map():
    m = B.tube_maps()['sp'].copy()
    m[:, 2] += SP_NUDGE
    return m


def _sp_cut():
    import wor_1g
    a, b = np.array(wor_1g.RIGHT.at(wor_1g.LED_BOTTOM)), np.array(wor_1g.RIGHT.at(wor_1g.LED_TOP))
    v = (b - a) / np.hypot(*(b - a))
    n = np.array((-v[1], v[0]))
    p0, p1 = a - v * B.TUBE_EXT[0], b + v * B.TUBE_EXT[1]
    w = B.TUBE_HALF_W
    return [tuple(p0 + n * w), tuple(p1 + n * w), tuple(p1 - n * w), tuple(p0 - n * w)]


SP_BODY_IDS = None


def _sp_body_ids():
    """The 1-player star power tube's body sprites (no fill, no effects)."""
    import wor_1g, desc_gen
    wor_1g.all_descs()
    out = []

    def walk(e):
        lid = e.local_id
        if lid.startswith('sp_') and not lid.startswith(('sp_seg', 'sp_feather', 'sp_glow', 'sp_cap', 'sp_burst', 'sp_clip')):
            out.append(lid)
        for c in e.children:
            walk(c)
    walk(desc_gen.ROOTS['wor_band_meter_1g_ghwor'])
    return set(out)


_BOX = {}


def sp_tube_box(textures_dir=None):
    if 'box' not in _BOX:
        textures(textures_dir)
    return _BOX['box']


def segments(n=6):
    """[(anchor (bottom centre), rot deg, width, height)] of the star power fill segments on P1's tube, screen px:
    the 1-player tube's six segments (wor_1g.sp_segments, in its band meter desc + game calibration) mapped by the
    rail affine; n = 3 merges them in pairs (the DE's per-player band tubes have three)."""
    import wor_1g, preview_hud
    m = sp_map()
    cal = preview_hud.GAME_CALIB['wor_band_meter_1g_ghwor']
    clip = wor_1g.sp_segments()[0]
    cx, cy = clip.pos
    L = m[:, :2]
    segs = []
    for e in clip.children:
        r = math.radians(e.rot)
        up = np.array((math.sin(r), -math.cos(r)))
        across = np.array((math.cos(r), math.sin(r)))
        w, h = e.dims[0] * e.scale[0], e.dims[1] * wor_1g.SP_DEFAULT_SCALE
        a = np.array((cx + e.pos[0] + cal[0], cy + e.pos[1] + cal[1]))
        a2 = B.apply(m, a)
        up2 = L @ (up * h)
        segs.append((np.array(a2), up2, float(np.hypot(*(L @ (across * w))))))
    if n == 3:
        segs = [(segs[i][0], (segs[i + 1][0] + segs[i + 1][1]) - segs[i][0], (segs[i][2] + segs[i + 1][2]) / 2)
                for i in (0, 2, 4)]
    out = []
    for a, up, w in segs:
        out.append(((float(a[0]), float(a[1])), math.degrees(math.atan2(up[0], -up[1])), w, float(np.hypot(*up))))
    return out


# ---- textures
def rank_badge(rank):
    """WoR's placing badge (back + front) with its rank text in WoR's text font (WoR draws the text over the art)."""
    from PIL import Image
    import mock_fail_popup as fonts
    back = Image.open(PLACE_BACK).convert('RGBA')
    out = Image.new('RGBA', back.size, (0, 0, 0, 0))
    out.alpha_composite(back)
    out.alpha_composite(Image.open(PLACE_FRONT).convert('RGBA'))
    x0, y0, x1, y1 = RANK_FACE
    word = {1: '1st', 2: '2nd'}[rank]
    h = int((y1 - y0) * 0.62)
    t = fonts.text(fonts.TEXT, word, h, (255, 255, 255), shadow=True)
    while t.width > (x1 - x0) * 0.86 and h > 8:      # fit the square's face (user: big enough for the numbers)
        h -= 1
        t = fonts.text(fonts.TEXT, word, h, (255, 255, 255), shadow=True)
    out.alpha_composite(t, ((x0 + x1 - t.width) // 2, (y0 + y1 - t.height) // 2))
    return out


def textures(textures_dir=None):
    from PIL import Image
    textures_dir = textures_dir or os.path.join(paths.REPO, 'build', 'preview')
    out = {k: Image.open(v).convert('RGBA') for k, v in TEX.items()}
    # theme pak budget (it must stay under 4 MiB, MODLOG 2026-10-21): the burst is drawn ~120 px
    out['WoR_HUD_starburst'] = out['WoR_HUD_starburst'].resize((128, 128), Image.LANCZOS)
    for r in (1, 2):
        out[RANK_TEX[r]] = rank_badge(r)
    ids = _sp_body_ids()
    m = sp_map()
    cut = _sp_cut()
    big = B._box([B.apply(m, p) for p in cut])
    lay = B._render_1p(textures_dir, keep=ids)
    body = B._warp_crop(lay, m, big, cut)
    x0, y0, x1, y1 = body.getbbox()
    (bx, by), (bw, bh) = big
    c = (bx + ((x0 + x1) / 2 - bw / 2) / B.SS, by + ((y0 + y1) / 2 - bh / 2) / B.SS)
    _BOX['box'] = (c, (B._pow2(x1 - x0 + 8), B._pow2(y1 - y0 + 8)))
    out[SPTUBE_TEX] = B._warp_crop(lay, m, _BOX['box'], cut)
    return out


def sources():
    s = {k: {'src': v} for k, v in TEX.items()}
    for r in (1, 2):
        s[RANK_TEX[r]] = {'src': PLACE_BACK, 'front': PLACE_FRONT, 'text_font': 'fontgrid_text_a1'}
    s[SPTUBE_TEX] = {'src': 'WoR_HUD_sp_base (1-player tube, mapped)', 'battle_tube': True}
    for v in s.values():
        v.setdefault('box', None)
        v.setdefault('flip', False)
    return s


# ---- the desc
def _sprite(lid, tex, pos, size, z, **kw):
    return E(lid, 'SpriteElement', pos=pos, dims=size, just=(0, 0), z=z, texture=tex, **kw)


def tree():
    from PIL import Image
    kids = []
    # dial (WoR uidesc_HUD_band_battle meter_container, scale 0.7 x (1.2, 1.1) there)
    dk = DIAL_K
    kids.append(E('dial', 'SpriteElement', pos=DIAL_C, dims=(256 * dk, 256 * dk), just=(0, 0), z=3.0,
                  texture='WoR_HUD_vs_dial', children=[
                      # the needle pivots at its texture centre (the visible blade is the upper half); WoR puts it
                      # at the dial's arc centre: texture (128, 194) of the 256 px dial
                      E('needle', 'SpriteElement', pos=(128 * dk, 194 * dk), dims=(32 * dk, 256 * dk), just=(0, 0),
                        z=12.0, texture='WoR_HUD_vs_needle')]))
    # the dial's arc centre on screen (needle pivot); the glows are quarters left / right of it
    piv = (DIAL_C[0], DIAL_C[1] + (194 - 128) * dk)
    glow_l = _sprite('glow_l', 'WoR_HUD_vs_glow_l', (piv[0] - 60 * dk * 0.95, piv[1] - 64 * dk * 0.95 + 4),
                     (128 * dk * 1.05, 128 * dk * 1.05), 4.0, rgba=P_RGBA[1])
    glow_r = _sprite('glow_r', 'WoR_HUD_vs_glow_r', (piv[0] + 60 * dk * 0.95, piv[1] - 64 * dk * 0.95 + 4),
                     (128 * dk * 1.05, 128 * dk * 1.05), 4.0, rgba=P_RGBA[2])
    # score bars: inner end next to the dial
    bar_w = 268 * BAR_K
    half_dial = 98 * dk
    for p in (1, 2):
        sgn = -1 if p == 1 else 1
        bx = DIAL_C[0] + sgn * (half_dial + BAR_GAP + bar_w / 2)       # visible bar centre
        art_c = (bx - (258 - 256) * BAR_K, BAR_Y)                     # the art's visible part is centred on x 258
        kids.append(E(f'score_container_{p}', 'ContainerElement', just=(-1, -1), dims=(1280, 720), z=5.0, children=[
            _sprite(f'score_back_{p}', 'WoR_HUD_vs_score_back', art_c, (512 * BAR_K, 64 * BAR_K), 5.0),
            _sprite(f'score_frame_{p}', 'WoR_HUD_vs_score', art_c, (512 * BAR_K, 64 * BAR_K), 6.0),
            _sprite(f'stripe_{p}', 'WoR_HUD_vs_stripe', (bx, BAR_Y - 3), (256 * BAR_K * 1.072, 64 * BAR_K), 7.0,
                    rgba=P_RGBA[p]),
            # score right-aligned at the bar's right end (WoR: "x1 | 82" / "94 x1")
            E(f'score_{p}', 'TextBlockElement', pos=(bx + bar_w / 2 - 14, BAR_Y + 1), dims=(300, 40), just=(1, 0),
              scale=(SCORE_K, SCORE_K), z=8.0, font=SCORE_FONT, text='0x00000000', shadow=False),
            # the streak: just a number in the bar's first square (WoR's "+4 | 64", user 2026-10-21); the square spans
            # texture x 128..186 of the 512 px art, the visible bar is centred on x 258
            E(f'streak_number_{p}', 'TextBlockElement', pos=(bx + (STREAK_SQ_X - 258) * BAR_K, BAR_Y + 1), dims=(200, 40),
              just=(0, 0), scale=(SCORE_K, SCORE_K), z=8.0, font=SCORE_FONT, text='0x00000000', shadow=False),
            # the DE's multiplier nixie at the bar's outer end
            # starts on our x1 badge: the plugin maps the DE's stock nixie names to ours on it; pos = the art's centre
            E(f'HUD_bb_multiplier_nixie_{p}', 'SpriteElement', pos=(bx + sgn * (bar_w / 2 + 26), BAR_Y),
              dims=(256 * NIXIE_K, 256 * NIXIE_K), just=(NIXIE_ART[0] / 256 - 1, NIXIE_ART[1] / 256 - 1), z=9.0,
              texture='WoR_HUD_mult_1'),
        ]))
    # placing: static "2nd" badges, the leader's "1st" + burst in containers the DE fades (amber = P1, violet = P2)
    lead = {1: [glow_l], 2: [glow_r]}
    for p in (1, 2):
        c = _rank_pos(p)
        kids.append(_sprite(f'rank2_{p}', RANK_TEX[2], c, (RANK_D, RANK_D), 10.0))
        lead[p] += [_sprite(f'burst_{p}', 'WoR_HUD_starburst', c, (RANK_BURST, RANK_BURST), 9.5, blend='Add'),
                    _sprite(f'rank1_{p}', RANK_TEX[1], c, (RANK_D, RANK_D), 10.5)]
        kids.append(E(f'lead_{p}', 'ContainerElement', just=(-1, -1), dims=(1280, 720), z=4.0, alpha=0.0,
                      children=lead[p]))
    # star power: shown by each player's own tube (wor_mp Star_Power, also in face-off); the versus fill props the
    # DE writes land on hidden stand-ins
    for p in (1, 2):
        for k in range(1, 7):
            kids.append(E(f'fill_{p}_{k}', 'SpriteElement', dims=(4, 4), alpha=0.0, z=0.0, texture='WoR_HUD_blank'))
    return E('HUD_meter_band_battle_master', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)


def _rank_pos(p):
    """Badge centre: outside the highway's left rail at RANK_Y (WoR: the rank badge left of each highway)."""
    x = B._line_x(B.RAIL_L, RANK_Y) - B.SEP - RANK_D / 2 - 6
    return _p2((x, RANK_Y), p)


def versus_desc():
    root = tree()
    props = [('hud_band_battle_meter_needle_rot_angle', 'needle', 'rot_angle'),
             ('hud_band_battle_meter_amber_on_alpha', 'lead_1', 'alpha'),
             ('hud_band_battle_meter_violet_on_alpha', 'lead_2', 'alpha'),
             ('score_1_text', 'score_1', 'text'), ('score_2_text', 'score_2', 'text'),
             ('hud_bb_multiplier_nixie_1_texture', 'HUD_bb_multiplier_nixie_1', 'texture'),
             ('hud_bb_multiplier_nixie_2_texture', 'HUD_bb_multiplier_nixie_2', 'texture'),
             ('p1_streak_number_text', 'streak_number_1', 'text'), ('p2_streak_number_text', 'streak_number_2', 'text')]
    for p in (1, 2):
        for k in range(1, 7):
            props += [(f'fill_{p}_{k}_texture', f'fill_{p}_{k}', 'texture'), (f'fill_{p}_{k}_scale', f'fill_{p}_{k}', 'Scale')]
    return desc(NAME, root, props)


# ---- edits of the copied WT+ layouts (build.py)
def _element_bounds(d, local_id):
    """(start, end) of the element block (StructHeader { StructStruct props {...} [children] }) of local_id."""
    import re
    import desc_edit
    hits = [m.start() for m in re.finditer(rf'StructQBKey local_id = {re.escape(local_id)}\s*\n', d)]
    if len(hits) != 1:
        raise ValueError(f'{local_id}: {len(hits)} matches')
    a, b = desc_edit._block_bounds(d, hits[0])        # the props' StructHeader { ... }
    a, b = desc_edit._block_bounds(d, a - 1)          # StructStruct props { ... }
    a, b = desc_edit._block_bounds(d, a - 1)          # the element's StructHeader { ... }
    return d.rfind('StructHeader', 0, a), b


def _set_alpha(d, local_id, alpha):
    import re
    a, b = _element_bounds(d, local_id)
    blk, n = re.subn(r'StructFloat alpha = [-\d.]+', f'StructFloat alpha = {alpha:.2f}', d[a:b], count=1)
    assert n == 1, local_id
    return d[:a] + blk + d[b:]


def _shift_pos(d, local_id, dx):
    import re
    a, b = _element_bounds(d, local_id)
    blk = d[a:b]
    m = re.search(r'StructFloatX2 Pos\s*\{\s*Floats \[([-\d.]+), ([-\d.]+)\]', blk)
    x, y = float(m.group(1)) + dx, float(m.group(2))
    blk = blk[:m.start()] + f'StructFloatX2 Pos\n{{\n\tFloats [{x:.5f}, {y:.5f}]' + blk[m.end():]
    return d[:a] + blk + d[b:]


def edit_layout(config, d):
    """The WT+ layout copy `config` (hud_2g, hud_1g1v, ...): the versus meter starts hidden in every layout (only the
    face-off attach shows it); hud_2g gets ours, its player containers follow the highways moved apart and carry our
    per-player star power tube, rock tube and multiplier (tools/wor_mp.py)."""
    import re
    import wor_mp
    ids = re.findall(r'StructQBKey local_id = (\S+)\s*\n(?:(?!local_id).)*?StructString desc = "HUD_band_battle"', d, re.S)
    if not ids:
        return d
    lid = ids[0]
    if config == 'hud_2g':
        a, b = _element_bounds(d, lid)
        new = E(lid, 'descinterface', pos=(0, 0), dims=(1280, 720), just=(-1, -1), z=1.0, alpha=0.0,
                desc=NAME, autosize=False).render(0)
        d = d[:a] + new + d[b:]
    else:
        d = _set_alpha(d, lid, 0.0)
    if config in ('hud_2g', 'hud_2g1v'):          # two instrument highways (+ vocals): our per-player pieces
        d = wor_mp.edit_two_highways(d)
    return d


SCRIPTS = (
    # the versus meter starts hidden in our layouts; the DE attaches it in face-off / pro face-off (and boss battles)
    'Script WoR_HUD_HUD_attach_widget_band_faceoff_meter [\n'
    '\t:i $WoR_HUD_HUD_attach_widget_band_faceoff_meter_orig$ isNull\n'
    '\t:i if $GotParam$$parent_id$\n'
    '\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$parent_id$\n'
    '\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$parent_id$$alpha$ = %i(1)\n'
    '\t\t:i endif\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_HUD_attach_widget_band_faceoff_meter_orig [\n'
    '\t:i $printf$%s("WoR_HUD: faceoff meter placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')
