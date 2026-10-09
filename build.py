"""Builds the GH5 / WoR HUD mods from sources. Never launches the game.

Inputs (read fresh every build, so the mod always matches the installed DE; locations in tools/paths.py):
  - DE theme table 0x8ef7f1be and HUD menu choices 0x1f644846 (tb.pak.xen)
  - World Tour+ theme pak (hud_ghwt_withtime.pak.xen): its descs are the template for the other player configs
  - WoR / GH3:WoR textures and the WoR numeral font, extracted from the user's own copies

Output (build/):
  WoR_HUD/  Mod.ini, WoR_HUD.qb.xen (theme without in-play messages + darker highway metal), hud_ghwor.pak.xen
            (theme pak), gems_ghwor_hud.pak.xen (border)
--package: ONE drop-in zip (mod, paks, HUD fixes plugin + ASI loader, ReShade + GHWoR preset + background-only add-on)
usage: python build.py [--install] [--package]
"""
import json, os, re, shutil, subprocess, sys, tempfile
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import desc_edit, paths, texdict, wor_1g, wor_art, wor_font  # noqa: E402

ROOT = paths.REPO
TOOLS, SDK, GAME, WOR_PNG, WOR_UI_PNG = paths.GH_TOOLS, paths.SDK, paths.GAME, paths.WOR_PNG, paths.WOR_UI_PNG
MOD_NAME = 'WoR_HUD'
PAK_NAME = 'hud_ghwor'
VERSION = '0.44'
BGFX_ADDON = os.path.join(ROOT, 'addon', 'build', 'ghwt_bgfx.addon32')   # option 2 (ReShade add-on, addon/build.bat)
GH5_GRADE = os.path.join(ROOT, 'addon', 'shaders', 'GH5_Grade.fx')
RESHADE_DIR = os.path.join(ROOT, 'extras', 'reshade')                    # vendored shaders, preset, ReShade.ini
OUT = os.path.join(ROOT, 'build', MOD_NAME)

# Player configurations a theme maps to layouts; WT+ provides descs for all of these except hud_2v.
CONFIGS = ['hud_1g', 'hud_2g', 'hud_1v', 'hud_1g1v', 'hud_2g1v', 'hud_3g1v']
# WT+ descs copied into the mod (renamed *_ghwtwithtime -> *_ghwor).
# hud_1g is generated from scratch as WoR's own 1-player layout (tools/wor_1g.py).
WTPLUS_DESCS = [c + '_ghwtwithtime' for c in CONFIGS if c != 'hud_1g'] + ['band_meter_ghwtwithtime', 'solo_play_rock_meter_ghwtwithtime']

# Texture plan: WT+ private textures get mod-owned ids (so they never collide with the WT+ pak's own),
# and may be replaced by WoR art. Source is ('wtplus', <img file>) or ('wor', <png name>).
TEXTURES = {
    '0x3af04b64': ('WoR_HUD_score_box', ('wor', 'band_HUD_star_score_meter')),   # score housing -> WoR star/score meter
    '0x6a16aa24': ('WoR_HUD_band_meter_box', ('wtplus', '0x6a16aa24')),
    'c4a63787': ('WoR_HUD_glow_dot', ('wtplus', '0xc4a63787')),
}


# Extra WoR textures used by restyled elements (no WT+ counterpart): id -> WoR png.
EXTRA_TEXTURES = {
    'WoR_HUD_rm_base': 'RM_Base',            # rock meter tube (64x256, slanted)
    'WoR_HUD_rm_green': 'RM_Green_Glow01',   # LED glow, top section
    'WoR_HUD_rm_yellow': 'RM_Yellow_Glow01', # LED glow, middle section
    'WoR_HUD_rm_red': 'RM_RED_Glow01',       # LED glow, bottom section
    'WoR_HUD_rm_cap': 'Sidebar_Base_cap',    # tube end cap
}

# v0.5 restyle of the solo rock meter desc (meter_container coordinates; the DE drives these elements through
# the desc's props table, so local_ids and nesting are kept). Score -> WoR star/score bar; rock meter -> WoR
# tube with the zone LEDs the DE already toggles (red 0-0.67, yellow 0.67-1.33, green 1.33-2.0).
# Hidden elements point at a fully transparent texture: texture 0x00000000 does NOT hide a sprite, the engine draws
# it as a plain white quad (seen in game in v0.5). Alpha can't be used because the DE drives some of these alphas.
NONE = 'WoR_HUD_blank'
TUBE = dict(dims=(64, 256), just=(0, 1), pos=(2, 113), scale=(0.62, 0.62))
ROCK_METER_EDITS = {
    'band_HUD_meter_body': dict(dims=(512, 128), scale=(0.55, 0.55)),          # texture -> WoR score bar via TEXTURES
    '0x24a05cbc': dict(pos=(120, 80)),                                          # song-time track, into the groove
    '0x40cc99b8': dict(pos=(120, 80)),                                          # song-time fill
    'Score': dict(pos=(176, 87), scale=(0.6, 0.6)),
    'lights_bg': dict(texture='WoR_HUD_rm_base', z=14, **TUBE),
    'green_light': dict(texture='WoR_HUD_rm_green', z=15, blend='Add', **TUBE),
    'yellow_light': dict(texture='WoR_HUD_rm_yellow', z=15, blend='Add', **TUBE),
    'red_light': dict(texture='WoR_HUD_rm_red', z=15, blend='Add', **TUBE),
    'Body': dict(texture='WoR_HUD_rm_cap', z=17, dims=(64, 64), just=(0, 1), pos=(2, 113), scale=(0.62, 0.62)),
    'glow': dict(texture=NONE),
    'band_HUD_meter_outer_glow': dict(texture=NONE),
    'multiplier': dict(texture=NONE),
    'Needle': dict(texture=NONE),            # WoR sliding needle comes in the next step
    'HUD_meter_green_bg': dict(texture=NONE),
    'HUD_meter_yellow_bg': dict(texture=NONE),
    'HUD_meter_red_bg': dict(texture=NONE),
}


def blank_png(w, h):
    """A fully transparent RGBA PNG (the 'hidden' texture)."""
    import struct, zlib
    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    raw = b''.join(b'\0' + b'\0' * 4 * w for _ in range(h))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'{cmd}: {r.stdout}{r.stderr}')
    return r.stdout


def sdk(*args, cwd):
    return run(['node', SDK, *args], cwd)


def qbkey(s):
    return run(['node', '-e', f"console.log((require('./SDKCode/QBKey.js')('{s}')>>>0).toString(16).padStart(8,'0'))"], os.path.dirname(SDK)).strip()


def block(text, header):
    """'<header> { ... }' by brace matching."""
    i = text.index(header)
    j = text.index('{', i)
    depth = 0
    for k in range(j, len(text)):
        depth += {'{': 1, '}': -1}.get(text[k], 0)
        if depth == 0:
            return text[i:k + 1]
    raise ValueError(header)


def extract_decompile(pak, work, only=None):
    """Extract a pak and decompile its .qb.xen files (or just `only`); returns {qb file name: text}."""
    ex = os.path.join(work, os.path.basename(pak).split('.')[0])
    sdk('extract', pak, ex, cwd=os.path.dirname(SDK))
    texts = {}
    for root, _, files in os.walk(ex):
        qbs = [f for f in files if f.endswith('.qb.xen') and (only is None or f in only)]
        if qbs:
            sdk('decompile', *qbs, cwd=root)
            for f in qbs:
                txt = os.path.join(root, f[:-7] + '.txt')
                if os.path.exists(txt):
                    texts[os.path.relpath(os.path.join(root, f), ex)] = open(txt, encoding='utf-8', errors='replace').read()
    return ex, texts


def main():
    work = tempfile.mkdtemp(prefix='worhud_build_')
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # ---- DE sources
    _, tb = extract_decompile(os.path.join(GAME, 'DATA', 'PAK', 'tb.pak.xen'), work, only={'0x29ebe78e.qb.xen', '0xbb76de6b.qb.xen'})
    themes = block(tb['0x29ebe78e.qb.xen'], 'SectionStruct 0x8ef7f1be')
    choices = block(tb['0xbb76de6b.qb.xen'], 'SectionArray 0x1f644846')
    wtp_dir, wtp = extract_decompile(os.path.join(GAME, 'DATA', 'PAK', 'hud_ghwt_withtime.pak.xen'), work)

    # ---- descs: copy WT+ descs, rename to *_ghwor, retarget textures
    desc_by_key = {}
    for text in wtp.values():
        m = re.search(r'SectionStruct (\S+)\s*\{\s*StructHeader\s*\{\s*StructInt descversion', text)
        if m:
            desc_by_key[m.group(1).replace('0x', '').zfill(8)] = block(text, 'SectionStruct ' + m.group(1))
    descs = []
    for name in WTPLUS_DESCS:
        key = qbkey('uidesc_' + name)
        if key not in desc_by_key:
            raise RuntimeError(f'WT+ pak has no desc {name} ({key})')
        d = desc_by_key[key]
        new = 'uidesc_' + name.replace('_ghwtwithtime', '_ghwor')
        # Rename only the name token: the compiler needs whitespace between the name and '{' (without it the
        # whole section is mis-parsed: no header, garbage descversion).
        d = re.sub(r'^SectionStruct \S+?(\s*)\{', lambda m: f'SectionStruct {new}\n{{', d, count=1)
        d = re.sub(r'StructQBKey name = \S+', f'StructQBKey name = {new}', d, count=1)
        for other in WTPLUS_DESCS:  # references to sibling descs inside the pak
            d = d.replace(f'"{other}"', f'"{other.replace("_ghwtwithtime", "_ghwor")}"')
        for old, (new_id, _) in TEXTURES.items():
            d = re.sub(rf'texture = {re.escape(old)}\b', f'texture = {new_id}', d)
        if name == 'solo_play_rock_meter_ghwtwithtime':
            for local_id, changes in ROCK_METER_EDITS.items():
                d = desc_edit.set_elem(d, local_id, **changes)
        descs.append(d)
    descs += wor_1g.all_descs()

    # ---- layouts and theme row
    layouts = [f'SectionStruct WoR_HUD_layout_{c[4:]}\n{{\n\tStructHeader\n\t{{\n\t\tStructQBKey hud_version = nxgui\n'
               f'\t\tStructString desc_interface = "{c}_ghwor"\n\t}}\n}}' for c in CONFIGS]
    wt = block(themes, 'StructStruct 0x90737ab7')
    wor = wt.replace('StructStruct 0x90737ab7', 'StructStruct ghwor', 1)
    # Textures must come from a theme pak: HUD sprites can't see image-handler textures (separate asset context).
    wor = re.sub(r'StructString pak = "[^"]*"', f'StructString pak = "{PAK_NAME}"', wor, count=1)
    assert f'"{PAK_NAME}"' in wor
    # WoR mechanics the DE already implements, switched on by theme flags: the sliding side meter (d38da2b2) and
    # the star meter (d5045305); and this theme's multiplier images (normal f8885a0f, star power d99b7552).
    extra = '\t\t\t\tStructInt d38da2b2 = 1\n\t\t\t\tStructInt d5045305 = 1\n'
    # 882f22a1: the DE's danger blinker (flashes the side meter's red light below 1/3 rock)
    extra += '\t\t\t\tStructInt 0x882f22a1 = 1\n'
    # WoR highway border: the DE's sidebar sprite width x sidebar_x_scale, offset outwards
    sx_, off_ = wor_1g.BORDER_X_SCALE, wor_1g.BORDER_OFFSET
    extra += (f'\t\t\t\tStructFloat sidebar_x_scale = {sx_}\n'
              f'\t\t\t\tStructFloatX2 0x3dacb46b\n\t\t\t\t{{\n\t\t\t\t\tFloats [{-off_:.5f}, 0.00000]\n\t\t\t\t}}\n'
              f'\t\t\t\tStructFloatX2 0x4dd26977\n\t\t\t\t{{\n\t\t\t\t\tFloats [{off_:.5f}, 0.00000]\n\t\t\t\t}}\n')
    # in-play message font (note streaks, Hot Start, band streaks, drum fills, fail hint; DE default
    # fontgrid_text_a6): stock themes set d5927557 and bf72b22c to their own font. The copied WT+ row already has
    # bf72b22c, so it is replaced, not duplicated.
    wor, n = re.subn(r'StructQBKey bf72b22c = \S+', f'StructQBKey bf72b22c = {wor_1g.MSG_FONT}', wor)
    if not n:
        extra += f'\t\t\t\tStructQBKey bf72b22c = {wor_1g.MSG_FONT}\n'
    extra += f'\t\t\t\tStructQBKey 0x18f90ff6 = {wor_1g.BORDER_TEX_NAME}\n'   # theme border texture
    assert 'd5927557' not in wor
    extra += f'\t\t\t\tStructQBKey d5927557 = {wor_1g.MSG_FONT}\n'
    for key, lst in (('f8885a0f', wor_1g.MULT_NORMAL), ('d99b7552', wor_1g.MULT_SP)):
        extra += (f'\t\t\t\tStructArray {key}\n\t\t\t\t{{\n\t\t\t\t\tArrayQBKey\n\t\t\t\t\t[\n'
                  + ''.join(f'\t\t\t\t\t\t{t[0]}\n' for t in lst) + '\t\t\t\t\t]\n\t\t\t\t}\n')
    k = wor.rindex('}', 0, wor.rindex('}'))
    wor = wor[:k] + extra + '\t\t\t' + wor[k:]
    for c in CONFIGS:
        wor = re.sub(rf'StructQBKey {c} = \S+', f'StructQBKey {c} = WoR_HUD_layout_{c[4:]}', wor)
    k = themes.rindex('}', 0, themes.rindex('}'))
    themes2 = (themes[:k] + '\t' + wor + '\n\t' + themes[k:]).replace('SectionStruct 0x8ef7f1be', 'SectionStruct WoR_HUD_themes', 1)
    entry = ('\t\tStructHeader\n\t\t{\n\t\t\tStructString Title = "Guitar Hero: Warriors of Rock"\n'
             '\t\t\tStructQBKey value = ghwor\n\t\t\tStructString value_string = "ghwor"\n\t\t}\n\t')
    k = choices.rindex(']')
    choices2 = (choices[:k] + entry + choices[k:]).replace('SectionArray 0x1f644846', 'SectionArray WoR_HUD_choices', 1)

    # ---- textures -> the theme pak (entry id = checksum of the texture name, like the stock theme paks)
    pak_src = os.path.join(ROOT, 'build', 'pak_src', PAK_NAME)
    if os.path.exists(pak_src):
        shutil.rmtree(pak_src)
    os.makedirs(pak_src)
    # Every texture is an EXTRACTED game texture (copied, or cropped for the multiplier strips); sources are recorded
    # in build/texture_sources.json and verified by the offline tests. The only exception is the fully transparent
    # placeholder used to hide sprites the DE drives but WoR doesn't show.
    pngs, sources = [], {}

    def ship(name, src, box=None, size=None, flip=False):
        p = os.path.join(work, name + '.png')
        if box:
            wor_art.crop_to(src, p, box, size, flip)
        elif flip:
            wor_art.flip_h(src, p)
        else:
            shutil.copy(src, p)
        pngs.append(p)
        sources[name] = {'src': src, 'box': box, 'flip': flip}

    for old, (new_id, (kind, src)) in TEXTURES.items():
        if kind == 'wtplus':
            shutil.copy(os.path.join(wtp_dir, src + '.img.xen'), os.path.join(pak_src, new_id + '.img.xen'))
        else:
            ship(new_id, os.path.join(WOR_PNG, src + '.png'))
    for new_id, src in EXTRA_TEXTURES.items():
        ship(new_id, os.path.join(WOR_PNG, src + '.png'))
    for new_id, src in wor_1g.TEXTURES.items():
        if os.path.isabs(src):          # full path to an extracted png (other WoR paks)
            ship(new_id, src)
            continue
        p = os.path.join(WOR_PNG, src + '.png')
        ship(new_id, p if os.path.exists(p) else os.path.join(WOR_UI_PNG, src + '.png'))
    # multiplier: GH3:WoR's images, one copy cropped out of each 2048x256 strip
    for new_id, src in wor_1g.MULT_NORMAL + wor_1g.MULT_SP:
        ship(new_id, os.path.join(paths.GH3WOR_PNG, src + '.png'), (1, 1, 155, 138), wor_1g.BADGE_TEX)
    # WoR's numeral font, converted from the Xbox format (same layout, PC texture), shipped in the theme pak
    for font_id, src in wor_1g.FONT_SRC.items():
        wor_font.convert(src, os.path.join(pak_src, font_id + '.fnt.xen'))
        sources[font_id] = {'src': src, 'box': None}
    # note-streak counter: GH3:WoR's light images (state 0 off, 1 half, 2 lit). Never under the DE's own names
    # (HUD_score_light_*): stock themes use those too, and unloading our pak on a theme switch took them away
    # ("MISSING TEXTURE" on WT/WT+). Only unique names, which the HUD fixes plugin sets; plus WoR's x1 pink set.
    for name, src in wor_1g.OWN_LIGHTS.items():
        ship(name, os.path.join(paths.GH3WOR_PNG, src + '.png'))
    for name, src in wor_1g.PINK_LIGHTS.items():
        p = os.path.join(paths.GH3WOR_PNG, src + '.png')
        if name.startswith('WoR_HUD_light_0'):
            ship(name, p)
        else:
            out = os.path.join(work, name + '.png')
            wor_art.tint_luma(p, out, wor_1g.PINK_TINT)
            pngs.append(out)
            sources[name] = {'src': p, 'box': None, 'flip': False, 'tint_luma': list(wor_1g.PINK_TINT)}
    # star-power fill: WoR's SP_Fill01 under our own segment names only (the DE's hud_rock_tube_glow_full(_b) are
    # shared with stock themes, see the streak lights above), cut into the slanted
    # parallelogram the segments expect; the colour comes from the segments' rgba, as in WoR. Flipped: the star power
    # tube is mirrored but the DE overwrites the segments' scale, so the mirror is baked into the texture.
    seg_h, seg_w = wor_1g.seg_canvas_size()
    for name in [ours for _, ours in wor_1g.SP_FILL_NAMES]:
        ship(name, os.path.join(WOR_PNG, 'SP_Fill01.png'), wor_1g.SP_FILL_BAND, (64, 16), flip=wor_1g.SP_FILL_FLIP)
        wor_art.slant_band(os.path.join(work, name + '.png'), wor_1g.sp_slant_geom(), wor_1g.SP_FILL_COLS, seg_h, seg_w)
        wor_art.tint_rgb(os.path.join(work, name + '.png'), wor_1g.SP_FILL_RGBA)     # colour baked in (sprites are white)
    # full-length fill for the plugin's smooth meter: the charging look (GH5's darker teal)
    full = os.path.join(work, wor_1g.SP_FULL_NAMES[0] + '.png')
    wor_art.tube_fill(os.path.join(WOR_PNG, 'SP_Base.png'), os.path.join(WOR_PNG, 'SP_Fill01.png'),
                      (wor_1g.SP_FILL_BAND[1], wor_1g.SP_FILL_BAND[3]), (35, 63), wor_1g.SP_FILL_ROWS,
                      int(wor_1g.SP_RIM), wor_1g.SP_CHARGING_RGBA, full, center=wor_1g.TEX_CENTER,
                      flat_bottom=wor_1g.SP_FLAT_BOTTOM)
    pngs.append(full)
    sources[wor_1g.SP_FULL_NAMES[0]] = {'src': os.path.join(WOR_PNG, 'SP_Fill01.png'),
                                        'shape': os.path.join(WOR_PNG, 'SP_Base.png'), 'box': None, 'flip': False}
    # ready look: WoR's Mat_Sp_Ready_Fire (SP_Fill_Glow02 under WoR's noise) as a seamless 60 fps loop; the _b fill
    # (what the DE picks when charged) is its first frame
    glow02 = paths.wor('basic_gems_png', 'a1c363bd.png')
    noise = paths.wor('ui_shared_png2', 'noise_32x32x32.png')
    # + WoR's tube lightning (Tesla needle: Lightining_arc_anim01, 16 frames at 20 fps) along the fill's centre
    arc_src = paths.wor('basic_gems_png', '0c30522c.png')
    frames = wor_art.plasma_frames(full, glow02, noise, wor_1g.SP_PLASMA_FRAMES, **wor_1g.SP_PLASMA_COLOURS,
                                   core_k=wor_1g.SP_PLASMA_CORE_K,
                                   arc=dict(png=arc_src, rows=wor_1g.SP_FILL_ROWS, center=wor_1g.TEX_CENTER,
                                            every=round(wor_1g.SP_PLASMA_FPS / 20)))

    for name, im in zip(wor_1g.SP_PLASMA_NAMES + [wor_1g.SP_FULL_NAMES[1]], frames + [frames[0]]):
        out = os.path.join(work, name + '.png')
        im.save(out)
        pngs.append(out)
        sources[name] = {'src': glow02, 'noise': noise, 'shape': full, 'arc': arc_src, 'box': None, 'flip': False}
    # ready burst: WoR's Ball_lightning01 (4x4 cells of 32 px)
    ball = paths.wor('basic_gems_png', '249c3fc1.png')
    for i, name in enumerate(wor_1g.SP_BALL_NAMES):
        ship(name, ball, (32 * (i % 4), 32 * (i // 4), 32 * (i % 4) + 32, 32 * (i // 4) + 32), (32, 32))
    # WoR's straight star-progress bar and song progress line: soft-edged strips from hud_progression_bar_lead's
    # vertical profile (the DE tints the star bar), the same dot at both tips, WoR's dark progress track
    lead = os.path.join(WOR_PNG, 'hud_progression_bar_lead.png')
    for name, core in ((wor_1g.STAR_BAR_NAME, 0.0), (wor_1g.PROG_FILL_NAME, 0.0), (wor_1g.PROG_TICK_NAME, 0.0)):
        out = os.path.join(work, name + '.png')
        wor_art.soft_strip(lead, out, core=core)
        pngs.append(out)
        sources[name] = {'src': lead, 'box': None, 'flip': False, 'strip': core}
    for name, rgb in ((wor_1g.STAR_LEAD_NAME, wor_1g.STAR_LEAD_RGB), (wor_1g.PROG_LEAD_NAME, wor_1g.PROG_LEAD_RGB)):
        out = os.path.join(work, name + '.png')
        wor_art.comet(lead, out, rgb, head=wor_1g.COMET_HEAD, tail_a=0.0)      # the extracted dot as a soft white aura ball, no tail
        pngs.append(out)
        sources[name] = {'src': lead, 'box': None, 'flip': False, 'comet': list(rgb)}
    ship(wor_1g.PROG_BACK_NAME, os.path.join(WOR_PNG, 'hud_song_progression_back.png'))
    # the star's fire glow (WoR FC_GLOW: band_HUD_gold_star_glow under Fire_2D noise) as a loop the plugin plays
    star_glow = os.path.join(WOR_PNG, 'band_HUD_gold_star_glow.png')
    for name, im in zip(wor_1g.STAR_FIRE_NAMES, wor_art.fire_frames(star_glow, noise, wor_1g.STAR_FIRE_FRAMES)):
        out = os.path.join(work, name + '.png')
        im.save(out)
        pngs.append(out)
        sources[name] = {'src': star_glow, 'noise': noise, 'box': None, 'flip': False}
    # bottom glow and fill-top cap: WoR's SB_Tubeglow01 under unique names
    # neon needles (SB_TubeNeedle01's own frame, drawn like the half divider): the fill-top cap as white core + blue
    # halo (two sprites), the bottom one as both in one texture (one sprite, shown charging and ready)
    caps = [os.path.join(work, n + '.png') for n in wor_1g.SP_GLOW_NAMES[1:]]
    wor_art.neon_sprite(os.path.join(WOR_PNG, wor_1g.SP_NEON_NEEDLE + '.png'), *caps, wor_1g.SP_NEON_RGB)
    bottom = Image.open(caps[1]).convert('RGBA')
    bottom.alpha_composite(Image.open(caps[0]).convert('RGBA'))
    caps.insert(0, os.path.join(work, wor_1g.SP_GLOW_NAMES[0] + '.png'))
    bottom.save(caps[0])
    for n, c in zip(wor_1g.SP_GLOW_NAMES, caps):
        pngs.append(c)
        sources[n] = {'src': os.path.join(WOR_PNG, wor_1g.SP_NEON_NEEDLE + '.png'), 'neon': list(wor_1g.SP_NEON_RGB), 'box': None, 'flip': False}
    p = os.path.join(work, NONE + '.png')          # transparent placeholder (hides sprites)
    open(p, 'wb').write(blank_png(4, 4))
    pngs.append(p)
    json.dump(sources, open(os.path.join(ROOT, 'build', 'texture_sources.json'), 'w'), indent=1)
    preview = os.path.join(ROOT, 'build', 'preview')
    shutil.rmtree(preview, ignore_errors=True)
    os.makedirs(preview)
    for p in pngs:
        shutil.copy(p, preview)
    if pngs:
        # all DXT5: raw PNG inside the theme pak made the DE fall back to the stock HUD pak (no textures at all)
        run(['node', os.path.join(TOOLS, 'png2img.js'), pak_src, *pngs], TOOLS)
    sdk('createpak', pak_src, '-out', os.path.join(OUT, f'{PAK_NAME}.pak.xen'), cwd=os.path.dirname(SDK))
    assert os.path.exists(os.path.join(OUT, f'{PAK_NAME}.pak.xen')), 'createpak failed'
    build_border_gempak(work)
    dark_load, dark_secs = dark_metal_sections(work)

    # Register the pak with the HUD pak-links table through the DE's own AddToGlobalStruct helper (0x325bc724),
    # exactly how the DE registers highway-mod paks (script 0x7c73dda7).
    load = ('Script WoR_HUD_Load [\n'
            '\t:i $printf$%s("WoR_HUD: registering Warriors of Rock HUD theme")\n'
            '\t:i $change$$[8ef7f1be]$ = (~$WoR_HUD_themes$)\n'
            '\t:i $change$$[1f644846]$ = (~$WoR_HUD_choices$)\n'
            # The DE reads HUDTheme from the ini before mods load and matches it against the menu choices; "ghwor"
            # wasn't there yet, so booting with WoR as the saved theme fell back to the first choice's paks (MISSING
            # TEXTURE). Re-read it now, the way the DE re-reads Gem Theme after mods (script 0x1727e98d).
            '\t:i $[67da6f76]$(~$[f26e4c1f]$->$[c98b95d8]$)\n'
            '\t:i $printf$%s("WoR_HUD: HUD Theme re-read from the ini after registering ghwor")\n'
            f'\t:i $WoR_HUD_link$ = :s{{$name$ = %s("{PAK_NAME}"):s}}\n'
            f'\t:i $[325bc724]$$id$ = $[cbcd0af1]$$field$ = ${PAK_NAME}$$element$ = %GLOBAL%$WoR_HUD_link$\n'
            '\t:i $printf$%s("WoR_HUD: theme pak registered with the HUD pak links")\n'
            + f'\t:i $WoR_HUD_gemlink$ = :s{{$name$ = %s("{wor_1g.BORDER_GEM_PAK}"):s}}\n'
            '\t:i $[325bc724]$$id$ = $[af130dc4]$$field$ = $[8a5ce489]$$element$ = %GLOBAL%$WoR_HUD_gemlink$\n'
            '\t:i $printf$%s("WoR_HUD: WoR gem theme repointed to its pak with the WoR highway border")\n' +
            dark_load +
            '\t:i endfunction\n]\n')

    # Scripts first: the compiler was seen to silently drop a Script placed after the large desc sections.
    src = '\n\n'.join(['Unknown [GHWT_HEADER]', load, themes2, choices2, *layouts, *descs, *dark_secs]) + '\n'
    open(os.path.join(OUT, f'{MOD_NAME}.txt'), 'w', encoding='utf-8').write(src)
    open(os.path.join(OUT, 'Mod.ini'), 'w').write('[ModInfo]\nName=GH5 / Warriors of Rock HUD\n'
        'Description=Adds "Guitar Hero: Warriors of Rock" to the HUD Theme options (GH5 / WoR style HUD, no in-play '
        'messages) and darkens the highway metal like GH5.\n'
        f'Author=WitchDoctoR\nVersion={VERSION}\n')
    sdk('compile', f'{MOD_NAME}.txt', cwd=OUT)
    assert os.path.exists(os.path.join(OUT, f'{MOD_NAME}.qb.xen')), 'compile failed'
    # Guard: decompile the binary and check every section made it (script bytecode is encoded, so the strings are
    # not visible in the raw file).
    rt = os.path.join(work, 'roundtrip')
    os.makedirs(rt)
    shutil.copy(os.path.join(OUT, f'{MOD_NAME}.qb.xen'), rt)
    sdk('decompile', f'{MOD_NAME}.qb.xen', cwd=rt)
    back = open(os.path.join(rt, f'{MOD_NAME}.txt'), encoding='utf-8', errors='replace').read()
    want = len(re.findall(r'^(?:Section\w+|Script) ', src, re.M))
    got = len(re.findall(r'(?:Section\w+|Script) \S+\s*(?:babeface\s*)?[\[{]', back))
    lost = [t for t in re.findall(r'\$printf\$%s\("([^"]+)"\)', src) if t not in back]
    if got != want or lost:
        raise RuntimeError(f'round trip lost sections: {got}/{want} decompiled; missing printf: {lost}')
    print('built', OUT, '| descs:', len(descs), '| textures:', len(TEXTURES), '| pak:', os.path.getsize(os.path.join(OUT, f'{PAK_NAME}.pak.xen')), 'bytes')

    if '--install' in sys.argv:
        dst = os.path.join(GAME, 'DATA', 'MODS', MOD_NAME)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(OUT, dst, ignore=shutil.ignore_patterns('*.txt', '*.pak.xen'))
        # the theme pak and the border gem pak go where the stock paks live
        shutil.copy(os.path.join(OUT, f'{PAK_NAME}.pak.xen'), os.path.join(GAME, 'DATA', 'PAK', f'{PAK_NAME}.pak.xen'))
        shutil.copy(os.path.join(OUT, wor_1g.BORDER_GEM_PAK + '.pak.xen'), os.path.join(GAME, 'DATA', 'PAK'))
        print('installed DATA\\PAK\\' + wor_1g.BORDER_GEM_PAK + '.pak.xen')
        print('installed to', dst, '+ DATA\\PAK\\' + PAK_NAME + '.pak.xen')

    if '--package' in sys.argv:
        package()


DARK_K = 0.58          # colour multiplier for the highway's metal (user-approved mock verify/mock_metal_v021.png)
# Highway metal materials (scripts/guitar/guitar_material.qb): border, fret bars, strikeline neck and silver cups.
# Coloured ring edges (col_now_*_dark), lit caps and gems are left alone.
DARK_MATERIALS = ['sys_sidebar2D_sys_sidebar2D', 'sys_fretbar_large_sys_fretbar_large',
                  'sys_fretbar_medium_sys_fretbar_medium', 'sys_fretbar_small_sys_fretbar_small', 'Mat_NB_Neck']
DARK_PATTERNS = []   # v0.24: strikeline cups untouched (their chrome ring already matches GH5)


def _brace_span(text, i):
    """(start of '{', end+1) of the brace block that opens at or after i."""
    j = text.index('{', i)
    depth = 0
    for k in range(j, len(text)):
        depth += {'{': 1, '}': -1}.get(text[k], 0)
        if depth == 0:
            return j, k + 1
    raise ValueError(i)


def darken_materials(arr, k):
    """Give each DARK material a grey m_psPass0MaterialColor (replacing its colour, or adding one)."""
    vec = ('StructArray vectorproperty\n{\n\tArrayFloat\n\t[\n' + ''.join(f'\t\t{v:.6f}\n' for v in (k, k, k, 1.0)) + '\t]\n}')
    names = set(DARK_MATERIALS)
    found = []
    out, pos = [], 0
    for m in re.finditer(r'StructQBKey name = (\S+)\s*\n\s*StructArray materialprops', arr):
        name = m.group(1)
        if name not in names and not any(re.fullmatch(p, name) for p in DARK_PATTERNS):
            continue
        a, b = _brace_span(arr, m.end())
        props = arr[a:b]
        col = re.search(r'(?i)StructQBKey name = m_pspass0materialcolor\s*\n\s*(StructQBString vectorproperty = \S+|StructArray vectorproperty\s*\{.*?\]\s*\})', props, re.S)
        if col:
            props = props[:col.start(1)] + vec + props[col.end(1):]
        else:
            r = props.rindex(']')
            props = props[:r] + 'StructHeader\n{\nStructQBKey name = m_psPass0MaterialColor\n' + vec + '\n}\n' + props[r:]
        out.append(arr[pos:a] + props)
        pos = b
        found.append(name)
    out.append(arr[pos:])
    return ''.join(out), found


def dark_metal_sections(work):
    """Darker highway metal (border, fret bars, strikeline neck and cups) for every theme, like GH5. Data only: the
    game builds its in-game materials at song start from two global arrays in guitar_material.qb; the mod replaces
    them (tb.pak, the DE version) with copies whose metal materials carry a grey colour multiplier.
    Returns (script lines for WoR_HUD_Load, sections)."""
    _, qb = extract_decompile(os.path.join(GAME, 'DATA', 'PAK', 'tb.pak.xen'), work, only={'guitar_material.qb.xen'})   # the DE's own version
    text = next(v for kk, v in qb.items() if kk.endswith('guitar_material.qb.xen'))
    secs, all_found = [], []
    for key, new in (('0x345d04a2', 'WoR_DarkMetal_mats_a'), ('af201180', 'WoR_DarkMetal_mats_b')):
        arr = block(text, f'SectionArray {key}')
        arr, found = darken_materials(arr, DARK_K)
        all_found += found
        secs.append(arr.replace(f'SectionArray {key}', f'SectionArray {new}', 1))
    missing = [n for n in DARK_MATERIALS if n not in all_found]
    assert not missing and len(all_found) == len(DARK_MATERIALS), ('dark metal materials not found', missing, len(all_found))
    load = (f'\t:i $printf$%s("WoR_HUD: darker highway metal, {len(all_found)} materials")\n'
            '\t:i $change$$[345d04a2]$ = (~$WoR_DarkMetal_mats_a$)\n'
            '\t:i $change$$[af201180]$ = (~$WoR_DarkMetal_mats_b$)\n')
    return load, secs


def build_border_gempak(work):
    """WoR's highway border (z_in_game basic_gems 388dd606, decoded from the Xbox dictionary) added to a copy of the
    DE's WoR gem pak. The game reads the HUD theme's border texture (key 18f90ff6) BEFORE the theme pak loads but
    AFTER the gem theme's pak, so the texture rides in the gem pak, which the mod repoints (pak links af130dc4) to
    this copy. Every original record and DDS stays byte-identical (tools/texdict.py round-trips the original)."""
    import struct
    d = open(os.path.join(GAME, 'DATA', 'PAK', 'gems_ghwor.pak.xen'), 'rb').read()
    typ, off, size = struct.unpack('>III', d[0:12])
    assert typ == 0x8bfa5e8e and off == 0x1000, 'unexpected gems_ghwor layout'
    recs = texdict.parse(d[off:off + size])
    assert texdict.build(recs) == d[off:off + size], 'tex dict round trip failed'
    tdir = os.path.join(work, 'border_tex')
    os.makedirs(tdir, exist_ok=True)
    png = os.path.join(tdir, wor_1g.BORDER_TEX_NAME + '.png')
    shutil.copy(wor_1g.BORDER_SRC, png)
    run(['node', os.path.join(TOOLS, 'png2img.js'), tdir, png], TOOLS)
    img = open(os.path.join(tdir, wor_1g.BORDER_TEX_NAME + '.img.xen'), 'rb').read()
    recs.append(texdict.record(int(qbkey(wor_1g.BORDER_TEX_NAME), 16), img[img.index(b'DDS '):]))
    # the star power strike on the gems: WoR's Tesla arc under the stock bolt texture's key (see wor_1g.BOLT_KEY)
    bolt = os.path.join(tdir, 'WoR_HUD_bolt.png')
    wor_art.bolt_sheet(wor_1g.BOLT_SRC, bolt)
    run(['node', os.path.join(TOOLS, 'png2img.js'), tdir, bolt], TOOLS)
    bimg = open(os.path.join(tdir, 'WoR_HUD_bolt.img.xen'), 'rb').read()
    recs = [r for r in recs if r['checksum'] != wor_1g.BOLT_KEY]
    recs.append(texdict.record(wor_1g.BOLT_KEY, bimg[bimg.index(b'DDS '):]))
    tex = texdict.build(recs)
    short = int(qbkey(wor_1g.BORDER_GEM_PAK), 16)
    full = struct.unpack('>I', d[16:20])[0]
    lt = list(struct.unpack('>8I', d[32:64]))
    last_data = d[32 + lt[1]:32 + lt[1] + lt[2]]
    last_off = (0x1000 + len(tex) + 15) & ~15
    lt[1] = last_off - 32
    lt[5] = short
    out = bytearray(0x1000)
    out[0:32] = struct.pack('>8I', typ, 0x1000, len(tex), 0, full, short, 0, 0)
    out[32:64] = struct.pack('>8I', *lt)
    out += tex
    out += b'\0' * (last_off - len(out))
    out += last_data
    out += b'\0' * ((-len(out)) % 0x1000)
    dst = os.path.join(OUT, wor_1g.BORDER_GEM_PAK + '.pak.xen')
    open(dst, 'wb').write(bytes(out))
    print('built', dst, '|', len(recs), 'textures (+ ' + wor_1g.BORDER_TEX_NAME + ')')


def package():
    """ONE Nexus-style drop-in archive mirroring the game folder: installing is "extract into the folder with
    GHWT_Definitive.exe", uninstalling is deleting the listed files. No scripts, no ini edits."""
    dist = os.path.join(ROOT, 'dist')
    shutil.rmtree(dist, ignore_errors=True)
    main = os.path.join(dist, f'GH5-WoR_HUD_{VERSION}')
    # the HUD theme (DE mod folder + its theme pak and border gem pak)
    shutil.copytree(OUT, os.path.join(main, 'DATA', 'MODS', MOD_NAME), ignore=shutil.ignore_patterns('*.txt', '*.pak.xen'))
    os.makedirs(os.path.join(main, 'DATA', 'PAK'))
    shutil.copy(os.path.join(OUT, f'{PAK_NAME}.pak.xen'), os.path.join(main, 'DATA', 'PAK'))
    shutil.copy(os.path.join(OUT, wor_1g.BORDER_GEM_PAK + '.pak.xen'), os.path.join(main, 'DATA', 'PAK'))
    # HUD fixes plugin (smooth star power, streak lights, ...) + its loader (Ultimate ASI Loader, MIT, as dinput8.dll)
    shutil.copy(os.path.join(ROOT, 'plugin', 'build', 'wor_hud_fixes.asi'), main)
    shutil.copy(paths.ASI_LOADER, os.path.join(main, 'dinput8.dll'))
    shutil.copy(os.path.join(RESHADE_DIR, 'THIRD_PARTY_LICENSES.txt'), main)
    # OPTIONAL folder (requirement for the WoR look, not for the HUD): ReShade (d3d9.dll) + the WoR preset + the
    # background-only add-on and its GH5 tone shader; its contents also go next to GHWT_Definitive.exe
    opt = os.path.join(main, 'Optional - ReShade (WoR shaders)')
    os.makedirs(opt)
    shutil.copy(os.path.join(paths.RESHADE, 'd3d9.dll'), opt)
    for f in ('ReShade.ini', 'GHWoR.ini'):
        shutil.copy(os.path.join(RESHADE_DIR, f), opt)
    shutil.copytree(os.path.join(RESHADE_DIR, 'reshade-shaders'), os.path.join(opt, 'reshade-shaders'))
    shutil.copy(GH5_GRADE, os.path.join(opt, 'reshade-shaders', 'Shaders'))
    shutil.copy(BGFX_ADDON, opt)
    shutil.copy(os.path.join(ROOT, 'extras', 'README_main.txt'), os.path.join(main, 'README - GH5-WoR HUD.txt'))
    shutil.make_archive(main, 'zip', main)
    print('packaged:', os.path.basename(main) + '.zip')


if __name__ == '__main__':
    main()
