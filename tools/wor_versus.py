"""Face-Off / Pro Face-Off (2 players) in the WoR versus style (user 2026-10-21; research docs/MODES_RULES.md).

The DE builds both with the hud_2g layout (shared with 2-player co-op / quickplay) and fills its versus meter, the
`HUD_band_battle` descinterface (alias alias_faceoff_meter), with HUD_attach_widget_band_faceoff_meter. That widget only
writes these props (docs/research/de_layouts.md 5): hud_band_battle_meter_needle_rot_angle (faceoff_ratio 1..-1 ->
-51.5..51.5 deg), hud_band_battle_meter_amber_on_alpha (1 when P1 leads by 0.1), ..._violet_on_alpha (P2 leads),
score_1_text / score_2_text, hud_bb_multiplier_nixie_1/2_texture (the DE's nixie names, fixed in the script),
fill_1_1..6 / fill_2_1..6 _texture / _scale (each player's star power, setubes, default scale (1, 1): scale (1, fill)),
p1 / p2_streak_number_text. GHWT:DE plays Face-Off, Pro Face-Off and Battle with 2 players only (user 2026-10-21),
so our desc HUD_band_battle_ghwor is WoR's 1v1 versus layout (user's WoR frame: "x1 | 71621" / "152129 | x1"):
  - the dial (uidesc_HUD_band_battle: blue P1 half left, red P2 half right, the leader's glow + needle);
  - one score box per player beside it (HUD_band_battle_score, P2's mirrored, team stripe on top): the note streak in
    the small outer square (only while the DE's streak is on, blank otherwise), the score in the wide window;
  - no placing badges and no per-player score bars (user 2026-10-21: one score design only);
  - each highway keeps its WoR star power tube and streak meter (tools/wor_mp.py), with WoR's fill under the
    WoR_HUD_vsseg names (the plugin keeps them out of its single-tube smooth fill);
  - the multiplier nixie the DE writes per side lands on a hidden element (still mapped to WoR_HUD_vsmult_* by the
    plugin's kVsNixieMap, so those names must exist);
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
    # the dial mirrored (FLIPPED): its blue half and the blue arc on the left, P1's side (user 2026-10-21: P1 blue,
    # P2 red); the white arc, flipped to the right, takes P2's red tint
    'WoR_HUD_vs_dial': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_OFF.png'),
    'WoR_HUD_vs_glow_l': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_violet_ON.png'),
    'WoR_HUD_vs_glow_r': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_amber_ON.png'),
    'WoR_HUD_vs_needle': os.path.join(WOR_ZIG, 'HUD_band_battle_meter_needle.png'),
    'WoR_HUD_vs_score': os.path.join(WOR_ZIG, 'HUD_band_battle_score.png'),
    'WoR_HUD_vs_score_back': os.path.join(WOR_ZIG, 'HUD_band_battle_score_back.png'),
    'WoR_HUD_vs_stripe': os.path.join(WOR_UI, 'vocal_meter_color_stripe.png'),
}
FLIPPED = ('WoR_HUD_vs_dial', 'WoR_HUD_vs_glow_l', 'WoR_HUD_vs_glow_r')
MIRRORED = {'WoR_HUD_vs_score_m': 'WoR_HUD_vs_score', 'WoR_HUD_vs_score_back_m': 'WoR_HUD_vs_score_back'}
SPTUBE_TEX = 'WoR_HUD_vs_sptube'
SEG_TEX = 'WoR_HUD_vsseg'                  # the plugin renames the DE's fill names to these (not its smooth fill)
SEG_NAMES = (('hud_rock_tube_glow_full', 'WoR_HUD_vsseg'), ('hud_rock_tube_glow_full_b', 'WoR_HUD_vsseg_b'))
# team colours (WoR face-off: blue left team, red right team; user 2026-10-21: P1 blue, P2 red)
P_RGBA = {1: (87, 149, 229, 255), 2: (228, 61, 12, 255)}
SP_NUDGE = np.array((-15.0, 0.0))          # the right rail's tube, towards the highway (see wor_battle.ROCK_NUDGE)
SCORE_FONT = 'WoR_HUD_num_a1'
NIXIE_K = 0.30                             # our multiplier badges: the 154x137 art top-left in a 256 px texture
NIXIE_ART = (154.0, 137.0)                 # (the plugin maps the DE's stock nixie names to them, kNixieMap)
STREAK_SQ = (128.0, 186.0)                 # the score bar art's first square (texture x)
STREAK_SQ_H = 20.0                         # its height on screen
# multiplier as text (user 2026-10-21): one texture per value the DE writes (ours, the DE's nixie name, label)
VSMULT = [('WoR_HUD_vsmult_' + ours.split('mult_')[1], src, src[len('HUD_score_nixie_'):-1])
          for ours, src in [('WoR_HUD_mult_1', 'HUD_score_nixie_1a'), ('WoR_HUD_mult_2', 'HUD_score_nixie_2a'),
                            ('WoR_HUD_mult_3', 'HUD_score_nixie_3a'), ('WoR_HUD_mult_4', 'HUD_score_nixie_4a'),
                            ('WoR_HUD_mult_sp2', 'HUD_score_nixie_2b'), ('WoR_HUD_mult_sp4', 'HUD_score_nixie_4b'),
                            ('WoR_HUD_mult_sp6', 'HUD_score_nixie_6b'), ('WoR_HUD_mult_sp8', 'HUD_score_nixie_8b')]]
WOR_NUM_A2 = os.path.join(paths.WOR_EXTRACT, 'ui_shared', 'fontgrid_numeral_A2.fnt.xen')   # Xbox: wor_font.convert
VSMULT_CANVAS = (64, 32)
VSMULT_NUM_H, VSMULT_X_H = 26, 14          # digit / "x" heights in the texture (WoR: the x is the smaller glyph)
VSMULT_H = 22.0                            # the texture's height on screen (digit ~18 px, the score's size)
SCORE_K = 0.26                             # score numerals (0.62 overflowed the bar, 0.38 still too big: user 2026-10-21)

# ---- layout (screen px)
DIAL_C = (640.0, 322.0)
DIAL_K = 0.62                              # the 256 px dial art
BAR_K = 0.62                               # the 512x64 score bar art (visible 268 px)
BAR_Y = 344.0                              # the score boxes, by the dial
BAR_GAP = 8.0                              # (unused since 2026-10-22: the boxes hang from the dial's corners)
DIAL_ART = (32.0, 226.0, 95.0, 192.0)      # the dial art's visible box in its 256 px texture (x0, x1, y0, y1)
BOX_ART = (121.0, 391.0, 8.0, 59.0)        # the score box art's visible box in its 512x64 texture
# WoR's dark (inactive) red half, from the user's WoR frames (73, 26, 14) against ours in game (68, 31, 25)
DIAL_RED_GAIN = (1.07, 0.84, 0.56)
# the needle: the DE turns it -51.5..51.5 deg (faceoff_ratio); WoR's dial spans ~180 deg, so a full lead stopped at
# ~70% of a side (user 2026-10-22). The DE's angle goes to a hidden twin (marked by its dims); plugin 1.38 turns the
# visible needle by that angle x NEEDLE_K.
NEEDLE_K = 1.65
NEEDLE_SRC_DIMS = 3.125
BOX_TUCK = 15.0                            # the boxes' inner ends this far under the dial (user 2026-10-22: no gap)
STREAK_FIT = 0.9                           # the streak text shrinks to fit this share of its square (3-4 digits)


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
_NUM_A2 = {}


def _num_a2_font():
    if 'p' not in _NUM_A2:
        import tempfile
        import wor_font
        out = os.path.join(tempfile.gettempdir(), 'worhud_fontgrid_numeral_A2.fnt.xen')
        wor_font.convert(WOR_NUM_A2, out)
        _NUM_A2['p'] = out
    return _NUM_A2['p']


def mult_text(label):
    """'x' + the multiplier value, white, bottoms aligned (WoR's mult_X + multiplier_number)."""
    from PIL import Image
    import mock_fail_popup as fonts
    x = fonts.text(fonts.TEXT, 'x', VSMULT_X_H, (255, 255, 255))
    n = fonts.text(_num_a2_font(), label, VSMULT_NUM_H, (255, 255, 255))
    x, n = x.crop(x.getbbox()), n.crop(n.getbbox())
    w = x.width + 1 + n.width
    out = Image.new('RGBA', VSMULT_CANVAS, (0, 0, 0, 0))
    x0, base = (VSMULT_CANVAS[0] - w) // 2, (VSMULT_CANVAS[1] + n.height) // 2
    out.alpha_composite(x, (x0, base - x.height))
    out.alpha_composite(n, (x0 + x.width + 1, base - n.height))
    return out


def textures(textures_dir=None):
    from PIL import Image
    textures_dir = textures_dir or os.path.join(paths.REPO, 'build', 'preview')
    out = {k: Image.open(v).convert('RGBA') for k, v in TEX.items()}
    for k in FLIPPED:
        out[k] = out[k].transpose(Image.FLIP_LEFT_RIGHT)
    out['WoR_HUD_vs_dial'] = _dial_colours(out['WoR_HUD_vs_dial'])
    for ours, _, label in VSMULT:
        out[ours] = mult_text(label)
    for m, src in MIRRORED.items():
        out[m] = out[src].transpose(Image.FLIP_LEFT_RIGHT)
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


def _dial_colours(im):
    """The inactive red half (right, P2's, after the flip) nearer WoR's dark red (user 2026-10-22: ours read brown)."""
    from PIL import Image
    a = np.array(im).astype(np.float32)
    half = a[:, 128:, :3]
    half *= np.array(DIAL_RED_GAIN, np.float32)
    a[:, 128:, :3] = half
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def sources():
    s = {k: {'src': v} for k, v in TEX.items()}
    for k in FLIPPED:
        s[k]['flip'] = True
    s['WoR_HUD_vs_dial']['red_half_gain'] = list(DIAL_RED_GAIN)
    for ours, _, label in VSMULT:
        s[ours] = {'src': WOR_NUM_A2, 'x_font': 'fontgrid_text_a1', 'text': 'x' + label}
    for m, src in MIRRORED.items():
        s[m] = {'src': TEX[src], 'flip': True}
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
                        z=12.0, texture='WoR_HUD_vs_needle'),
                      E('needle_src', 'SpriteElement', pos=(128 * dk, 194 * dk), dims=(NEEDLE_SRC_DIMS, NEEDLE_SRC_DIMS),
                        just=(0, 0), z=0.0, alpha=0.0, texture='WoR_HUD_blank')]))
    # the dial's arc centre on screen (needle pivot); the glows are quarters left / right of it
    piv = (DIAL_C[0], DIAL_C[1] + (194 - 128) * dk)
    glow_l = _sprite('glow_l', 'WoR_HUD_vs_glow_l', (piv[0] - 60 * dk * 0.95, piv[1] - 64 * dk * 0.95 + 4),
                     (128 * dk * 1.05, 128 * dk * 1.05), 4.0, rgba=P_RGBA[1])
    glow_r = _sprite('glow_r', 'WoR_HUD_vs_glow_r', (piv[0] + 60 * dk * 0.95, piv[1] - 64 * dk * 0.95 + 4),
                     (128 * dk * 1.05, 128 * dk * 1.05), 4.0, rgba=P_RGBA[2])
    # score bars: inner end next to the dial
    bar_w = 268 * BAR_K
    half_dial = 98 * dk
    # each box's inner top corner on the dial's bottom corner on its side, the boxes in front of the dial (user
    # 2026-10-22, WoR frames)
    corner_dx = (DIAL_ART[1] - DIAL_ART[0]) / 2 * dk
    corner_y = DIAL_C[1] + (DIAL_ART[3] - 128) * dk
    box_y = corner_y - (BOX_ART[2] - 32) * BAR_K                         # the art's centre height
    for p in (1, 2):
        sgn = -1 if p == 1 else 1
        art_x = DIAL_C[0] + sgn * (corner_dx - BOX_TUCK + (BOX_ART[1] - 256) * BAR_K)
        art_c = (art_x if p == 1 else art_x, box_y)
        bx = art_x - sgn * (258 - 256) * BAR_K                         # visible bar centre (art visible centre x 258)
        sq = ((STREAK_SQ[0] + STREAK_SQ[1]) / 2 - 258) * BAR_K        # the square's centre, from the art's visible centre
        sq_x = bx + (sq if p == 1 else -sq)                            # P2's bar is mirrored
        score_x = bx + bar_w / 2 - 14 if p == 1 else sq_x - (STREAK_SQ[1] - STREAK_SQ[0]) * BAR_K / 2 - 10
        m = '_m' if p == 2 else ''
        mult_h = STREAK_SQ_H * 1.05
        # the score box (user 2026-10-21, WoR 1v1 frame "x1 | 71621" / "152129 | x1"): the note streak in the small
        # square at the outer end, the score (thousands separators: plugin, native seinttostring) in the wide window;
        # P2's art mirrored, so its slots are too. The streak shows only while the DE's streak is on: a window clipped
        # to the square holds a container (alias_streak_pN) with the DE's streak number; HUD_setup_streak_meter_animation
        # slides it out of the window on playerN_streak_ended and back on _started (the DE's threshold).
        sq_w = (STREAK_SQ[1] - STREAK_SQ[0]) * BAR_K
        kids.append(E(f'score_container_{p}', 'ContainerElement', just=(-1, -1), dims=(1280, 720), z=5.0, children=[
            _sprite(f'score_back_{p}', 'WoR_HUD_vs_score_back' + m, art_c,
                    (512 * BAR_K, 64 * BAR_K), 5.0),
            _sprite(f'score_frame_{p}', 'WoR_HUD_vs_score' + m, art_c,
                    (512 * BAR_K, 64 * BAR_K), 6.0),
            _sprite(f'stripe_{p}', 'WoR_HUD_vs_stripe', (bx, box_y - 3), (256 * BAR_K * 1.072, 64 * BAR_K), 7.0,
                    rgba=P_RGBA[p]),
            E(f'score_{p}', 'TextBlockElement', pos=(score_x, box_y + 1), dims=(300, 40), just=(1, 0),
              scale=(SCORE_K, SCORE_K), z=8.0, font=SCORE_FONT, text='0x00000000', shadow=False),
            # the DE writes the side's multiplier texture here (plugin kVsNixieMap): kept, hidden
            E(f'HUD_bb_multiplier_nixie_{p}', 'SpriteElement', pos=(sq_x, box_y + 1),
              dims=(mult_h * VSMULT_CANVAS[0] / VSMULT_CANVAS[1], mult_h), just=(0, 0), z=9.0, alpha=0.0,
              texture=VSMULT[0][0]),
            E(f'streak_mask_{p}', 'windowelement', pos=(sq_x - sq_w / 2, box_y - STREAK_SQ_H / 2),
              dims=(sq_w, STREAK_SQ_H), just=(-1, -1), z=8.0, children=[
                  E(f'streak_{p}', 'ContainerElement', pos=(0, 0), dims=(sq_w, STREAK_SQ_H), just=(-1, -1), z=8.0,
                    children=[
                        E(f'streak_number_{p}', 'TextBlockElement', pos=(sq_w / 2, STREAK_SQ_H / 2 + 1),
                          dims=(sq_w * STREAK_FIT / SCORE_K, 40), just=(0, 0), scale=(SCORE_K, SCORE_K), z=8.0,
                          font=SCORE_FONT, text='0x00000000', shadow=False,
                          fit_width='scale each line if larger')])]),
        ]))
    # who leads: the dial's glow on the leader's side (the DE fades these containers; amber = P1, violet = P2)
    for p, glow in ((1, glow_l), (2, glow_r)):
        kids.append(E(f'lead_{p}', 'ContainerElement', just=(-1, -1), dims=(1280, 720), z=4.0, alpha=0.0,
                      children=[glow]))
    # star power: shown by each player's own tube (wor_mp Star_Power, also in face-off); the versus fill props the
    # DE writes land on hidden stand-ins
    for p in (1, 2):
        for k in range(1, 7):
            kids.append(E(f'fill_{p}_{k}', 'SpriteElement', dims=(4, 4), alpha=0.0, z=0.0, texture='WoR_HUD_blank'))
    return E('HUD_meter_band_battle_master', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=kids)


def versus_desc():
    root = tree()
    props = [('hud_band_battle_meter_needle_rot_angle', 'needle_src', 'rot_angle'),
             ('hud_band_battle_meter_amber_on_alpha', 'lead_1', 'alpha'),
             ('hud_band_battle_meter_violet_on_alpha', 'lead_2', 'alpha'),
             ('score_1_text', 'score_1', 'text'), ('score_2_text', 'score_2', 'text'),
             ('hud_bb_multiplier_nixie_1_texture', 'HUD_bb_multiplier_nixie_1', 'texture'),
             ('hud_bb_multiplier_nixie_2_texture', 'HUD_bb_multiplier_nixie_2', 'texture'),
             ('p1_streak_number_text', 'streak_number_1', 'text'), ('p2_streak_number_text', 'streak_number_2', 'text')]
    for p in (1, 2):
        for k in range(1, 7):
            props += [(f'fill_{p}_{k}_texture', f'fill_{p}_{k}', 'texture'), (f'fill_{p}_{k}_scale', f'fill_{p}_{k}', 'Scale')]
    return desc(NAME, root, props, aliases=[('alias_streak_p1', 'streak_1'), ('alias_streak_p2', 'streak_2')])


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
