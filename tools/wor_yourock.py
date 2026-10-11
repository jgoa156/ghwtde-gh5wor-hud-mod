"""WoR's YOU ROCK (v0.49): "Guitar Hero: Warriors of Rock" in You Rock Theme.

The DE dispatches You Rock themes inside GuitarEvent_SongWon_Spawned (bytecode the SDK can't decompile); an unknown
value runs the World Tour default, Create_HandsOfGod: the DE's exploding text (create_exploding_text) plus the
Hands of God desc. Plugin 1.26 wraps Create_HandsOfGod; with "ghwor" the wrapper runs WoR's version instead:
  - the exploding "YOU ROCK!" in WoR's title font and light blue (WoR's create_exploding_text: the DE's own, same
    physics helpers, with WoR's font/colour/scale and its effects),
  - WoR's effects ported from your copy (scripts/guitar/menu/yourock.qb, scripts/game/goals/goal_hud.qb): the
    lightning-ball glow behind the letters (You_Rock_Text_Glow), the lightning bolts striking from the screen edges
    (You_Rock_lightning_01 -> p2p_lightning_create), the explosion (UROK_FX_XPLOSION01), renamed WoR_HUD_*;
    p2p_get_connector_length without AbsoluteValue / sqrt (not DE functions): comparisons and Newton's method,
  - WoR's materials for them (Mat_Lightning_*, Mat_UROK_Xplosion1, the spark particles) appended to the in-game
    material array (like the star power highway's) and their textures in every gem pak,
  - an empty HandsOfGod container, so the DE's own cleanup still finds what it expects.
The choice is added to the You Rock option's inline value list (f26e4c1f -> 1265cc79) at mod load.
"""
import os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths, wor_ui  # noqa: E402

THEME, THEME_TITLE = wor_ui.THEME, wor_ui.THEME_TITLE
TITLE_FONT = 'WoR_HUD_title_a1'
# v0.48 video comparison: WoR's lightning, glow balls and explosion are AnimatedTexture_UI flipbooks (bolts 1x16
# cells, balls 4x4 of 32 px at 20 fps, explosion 4x4 of 128 px played once at 30 fps). The DE doesn't animate them:
# it draws the whole sheet squashed (thin lines, a soft fog, a weak burst). So:
#   - sprites (bolts, the balls at their ends, the explosion) get one texture per frame (FLIPBOOKS, in the UI pak),
#     switched by WoR_HUD_flipbook, like the loading screen's wheel;
#   - the glow's particles (a particle system takes one material) get static one-cell materials built like WoR's
#     spark material (ImmediateMode_UI / UI_Col_Tex_2D / Add, which the DE draws): GLOW_MATS.
MATERIALS = ('sys_Particle_Spark01_sys_Particle_Spark01',)
# their textures (WoR basic_gems, keyed by tex\models\highway\<name>.dds): lil_spark, spark02, lil_star
TEXTURES = (0x44e7b154, 0xadbdbfa2, 0x45c726d2)
SHEETS = {   # WoR sheet (basic_gems key) -> (frame texture prefix, cells across, down)
    0x0c30522c: ('WoR_HUD_bolt_', 1, 16),        # lightining_arc_anim01
    0x249c3fc1: ('WoR_HUD_ball_', 4, 4),         # ball_lightning01
    0xeaa76a98: ('WoR_HUD_urok_', 4, 4),         # note_hit_xplosion1
}
GLOW_CELLS = (0, 5, 10, 15)                      # ball cells for the glow's static materials
GLOW_MATS = tuple(f'WoR_HUD_Mat_ball_{c}' for c in GLOW_CELLS)
GLOW_TEX_PATH = 'tex\\models\\highway\\wor_hud_ball_cell{}.dds'
PORTED = {   # WoR script -> source qb (under WOR_EXTRACT/qb)
    'You_Rock_Text_Glow': 'scripts/guitar/menu/yourock.qb.xen',
    'You_Rock_Text_Glow_Cleanup': 'scripts/guitar/menu/yourock.qb.xen',
    'You_Rock_lightning_01': 'scripts/guitar/menu/yourock.qb.xen',
    'UROK_FX_XPLOSION01': 'scripts/guitar/menu/yourock.qb.xen',
    'UROK_FX_XPLOSION01_Cleanup': 'scripts/guitar/menu/yourock.qb.xen',
    'p2p_lightning_create': 'scripts/game/goals/goal_hud.qb.xen',
    'p2p_get_connector_angle': 'scripts/game/goals/goal_hud.qb.xen',
    'p2p_lightning_create_fx': 'scripts/game/goals/goal_hud.qb.xen',
    'p2p_lightning_create_fx_cleanup': 'scripts/game/goals/goal_hud.qb.xen',
    # WoR's exploding text, all of it (v0.48 video comparison: the DE's versions hold the text 2 s, explode it softer
    # and spin it 720 deg; WoR's hits faster, holds ~1.7 s, bursts at 9e6 with 280 deg spins, so the glow goes and the
    # explosion fires at the burst): letters with a black copy 3,4 px down-right (the DE's had an orange edge)
    'create_exploding_text': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
    'split_text_into_physics_array_elements': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
    'do_text_slam': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
    'do_exploding_text_physics': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
    'create_exploding_particles': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
    'do_extra_exploding_particles': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
    'explode_white_screens': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
}




# WoR's lightning bolts are created under root_window (no group the ultrawide add-on can rescale: v0.48 test, they
# stayed in the centred 16:9 picture while the other YOU ROCK themes fill the screen): ours go under FX_CONTAINER, a
# full-screen container the add-on covers like the other YOU ROCK layouts (as it does you_rock_physics).
FX_CONTAINER = 'WoR_HUD_yourock_fx'
YOU_ROCK_FIT_W = 755.0           # WoR 640 (our font's metrics fit it smaller)
YOU_ROCK_TEXT = 'YOU ROCK!'      # WoR's (the DE passes "You Rock!", a localised string GetUpperCaseString leaves as is)
# the gameplay 2D (the DE's toggle_highway / hide_hud ids): highways, vocal highways, HUD
HIDE_ON_YOU_ROCK = ('gem_containerp1', 'gem_containerp2', 'gem_containerp3', 'gem_containerp4', 'vocals_highway_p1',
                    'vocals_highway_p2', 'hud_root')


# the glow's cells: WoR's colours baked in (the particle colours may not apply): between You_Rock_Text_Glow's start
# (123 grey) and end (0,64,255) colours
GLOW_TINT = (90, 140, 255)
_HERE = os.path.dirname(os.path.abspath(__file__))
_OUT = os.path.join(_HERE, '..', 'build', 'pak_src', 'wor_yourock')


YR_SOUND = 'WoR_HUD_you_rock'     # WoR's YOU ROCK sound (You_Rock_Front + _Back + _LFE, global_sfx), in the UI pak
YR_SOUND_SRC = ('You_Rock_Front', 'You_Rock_Back', 'You_Rock_LFE')
YR_SOUND_VOL = 0.0
YR_SOUND_PLAY = True    # test B: play it through a sound event (WoR_HUD_YouRock + _container, like the DE's events)
YR_EVENT = 'WoR_HUD_YouRock'
YR_EVENT_SECTION = (f'SectionStruct {YR_EVENT}_container\n{{\n\tStructHeader\n\t{{\n\t\tStructInt default_priority = 50\n'
                    '\t\tStructQBKey default_buss = front_end\n\t\tStructFloat norepeatfor = 0.10000000149011612\n'
                    '\t\tStructQBKey instancemanagement = ignore\n\t\tStructInt instancelimit = 1\n'
                    '\t\tStructQBKey command = playsound\n\t\tStructQBKey randomness = None\n\t\tStructArray sounds\n'
                    f'\t\t{{\n\t\t\tArrayStruct\n\t\t\t[\n\t\t\t\tStructHeader\n\t\t\t\t{{\n\t\t\t\t\tStructQBKey {YR_SOUND}\n'
                    '\t\t\t\t}\n\t\t\t]\n\t\t}\n\t}\n}\n')


def you_rock_sound(out_dir):
    """WoR's three YOU ROCK layers (Xbox FSB4 XMA in ZONES global_sfx) mixed to stereo, as the DE's sound format: a
    44.1 kHz stereo 320 kb/s MP3 named <sound>.wav.xen (pak entry = checksum of the name, registered by LoadSound)."""
    import wor_menu_music as mm
    work = tempfile.mkdtemp(prefix='woryrsnd_')
    pcm = []
    for n in YR_SOUND_SRC:
        p = paths.wor('all', 'x', 'compressed_ZONES_global_sfx', n + '.wav.xen')
        name, nsamp, nbytes, mode, freq, chans, off = mm.fsb4_samples(p)[0]
        raw = open(p, 'rb').read()[off:off + nbytes]
        x = os.path.join(work, n + '.xma.wav')
        open(x, 'wb').write(mm.xma2_riff(raw, nsamp, freq, chans))
        w = os.path.join(work, n + '.wav')
        mm.ffmpeg('-y', '-i', x, w)
        pcm.append(w)
    out = os.path.join(out_dir, YR_SOUND + '.wav.xen')
    args = []
    for w in pcm:
        args += ['-i', w]
    mm.ffmpeg('-y', *args, '-filter_complex', f'amix=inputs={len(pcm)}:normalize=0,alimiter=limit=0.95:level=false',
              '-ar', '44100', '-ac', '2', '-c:a', 'libmp3lame', '-b:a', '320k', '-joint_stereo', '1',
              # like the DE's own sounds: MPEG frames from byte 0 (the ID3 tag froze the game at YOU ROCK)
              '-id3v2_version', '0', '-write_id3v1', '0', '-map_metadata', '-1', '-f', 'mp3', out)
    assert open(out, 'rb').read(2) == bytes((0xff, 0xfb)), 'YOU ROCK sound: not starting with an MPEG frame'
    shutil.rmtree(work, ignore_errors=True)
    return out


YR_EXPLODE, YR_GRAVITY = 13500000, 3500.0     # burst force (WoR 9000000), g_GRAVITY (DE 1000.0)


def _cells(key):
    from PIL import Image
    prefix, nx, ny = SHEETS[key]
    sheet = Image.open(os.path.join(paths.WOR_EXTRACT, 'basic_gems_png', f'{key:08x}.png')).convert('RGBA')
    w, h = sheet.size[0] // nx, sheet.size[1] // ny
    return [sheet.crop((x * w, y * h, (x + 1) * w, (y + 1) * h)) for y in range(ny) for x in range(nx)]


def ui_images(out_dir):
    """One PNG per flipbook frame (UI pak; sprites tint them with their rgba): returns the paths."""
    out = []
    for key, (prefix, _, _) in SHEETS.items():
        for i, cell in enumerate(_cells(key)):
            path = os.path.join(out_dir, f'{prefix}{i}.png')
            cell.save(path)
            out.append(path)
    return out


def _qbkey(s):
    import zlib
    return ~zlib.crc32(s.lower().encode()) & 0xffffffff


def texture_pngs():
    """[(texture key, png path)] for the gem paks (material textures): WoR's spark textures + the glow's tinted cells."""
    from PIL import Image
    os.makedirs(_OUT, exist_ok=True)
    out = [(k, os.path.join(paths.WOR_EXTRACT, 'basic_gems_png', f'{k:08x}.png')) for k in TEXTURES]
    cells = _cells(0x249c3fc1)
    for c in GLOW_CELLS:
        # 128 px like WoR's whole sheet (a particle's size follows its texture: 32 px cells made the glow 4x smaller)
        r, g, b, a = cells[c].resize((128, 128), Image.LANCZOS).split()
        im = Image.merge('RGBA', [ch.point(lambda v, m=m: v * m // 255) for ch, m in zip((r, g, b), GLOW_TINT)] + [a])
        path = os.path.join(_OUT, f'ball_cell{c}.png')
        im.save(path)
        out.append((_qbkey(GLOW_TEX_PATH.format(c).replace('\\\\', '\\')), path))
    return out


def material_groups(spark_group):
    """The glow's static materials: WoR's spark material group (ImmediateMode_UI, UI_Col_Tex_2D, Add) renamed, with
    one ball cell as its texture."""
    out = []
    for name, c in zip(GLOW_MATS, GLOW_CELLS):
        g = spark_group.replace('StructQBKey name = sys_Particle_Spark01_sys_Particle_Spark01', f'StructQBKey name = {name}')
        g = re.sub(r'textureproperty = \S+', lambda m: 'textureproperty = ' + GLOW_TEX_PATH.format(c), g)
        assert name in g and f'cell{c}.dds' in g
        out.append(g)
    return out


def _decompile(rel):
    src = os.path.join(paths.WOR_EXTRACT, 'qb', *rel.split('/'))
    with tempfile.TemporaryDirectory(prefix='woryr_') as d:
        shutil.copy(src, d)
        name = os.path.basename(src)
        subprocess.run(['node', paths.SDK, 'decompile', name], cwd=d, capture_output=True, check=True)
        return open(os.path.join(d, name[:-len('.qb.xen')] + '.txt'), encoding='utf-8', errors='replace').read()


def _rename(body):
    for n in list(PORTED) + ['p2p_get_connector_length']:
        body = re.sub(r'\$' + re.escape(n) + r'\$', f'$WoR_HUD_{n}$', body)
        body = re.sub(r'StructQBKey ' + re.escape(n) + r'\b', f'StructQBKey WoR_HUD_{n}', body)
    return body


FLIPBOOK = (
    # switches a sprite's texture to <prefix><frame> every `step` game frames until the sprite is gone (loop) or the
    # last frame shows (loop = 0); checks the sprite first (SetScreenElementProps on a missing element crashes)
    'Script WoR_HUD_flipbook [\n'
    '\t${\n\t\tStructInt frames = 16\n\t\tStructInt step = 3\n\t\tStructInt start = 0\n\t\tStructInt loop = 1\n\t}$\n'
    '\t:i $f$ = %GLOBAL%$start$\n'
    '\t:i while\n'
    '\t\t:i if NOT $ScreenElementExists$$id$ = %GLOBAL%$id$\n'
    '\t\t\t:i continue\n'
    '\t\t:i endif\n'
    '\t\t:i $FormatText$$checksumname$ = $tex$%s("%p%f")$p$ = %GLOBAL%$prefix$$f$ = %GLOBAL%$f$\n'
    '\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$id$$texture$ = %GLOBAL%$tex$\n'
    '\t\t:i $f$ = (%GLOBAL%$f$ + %i(1))\n'
    '\t\t:i if (%GLOBAL%$f$ >= %GLOBAL%$frames$)\n'
    '\t\t\t:i if (%GLOBAL%$loop$ = %i(0))\n'
    '\t\t\t\t:i continue\n'
    '\t\t\t:i endif\n'
    '\t\t\t:i $f$ = %i(0)\n'
    '\t\t:i endif\n'
    '\t\t:i $wait$%GLOBAL%$step$$gameframes$\n'
    '\t:i loop_to \n'
    '\t:i endfunction\n]\n')

# sprite material -> (texture prefix, frames, game frames per frame (60 fps), start frame, loop)
SPRITE_FLIPS = {
    'Mat_Lightning_Arc_Anim01': ('WoR_HUD_bolt_', 16, 3, 0, 1),     # 20 fps
    'Mat_Lightning_Arc_Anim02': ('WoR_HUD_bolt_', 16, 3, 8, 1),     # m_Offset 1: another phase
    'Mat_Lightning_ball_anim01': ('WoR_HUD_ball_', 16, 3, 0, 1),
    'Mat_Lightning_ball_anim02': ('WoR_HUD_ball_', 16, 3, 8, 1),
    'Mat_UROK_Xplosion1': ('WoR_HUD_urok_', 16, 2, 0, 0),           # 30 fps, once
}


def _sprite_flipbooks(body):
    """Each `$material$ = $<animated>$` sprite: its first frame as texture, additive, and WoR_HUD_flipbook spawned
    on it right after it is created (its id is kept in the line after the CreateScreenElement)."""
    out, i = '', 0
    for m in re.finditer(r'\$material\$ = \$(\w+)\$', body):
        mat = m.group(1)
        if mat not in SPRITE_FLIPS:
            continue
        prefix, frames, step, start, loop = SPRITE_FLIPS[mat]
        out += body[i:m.start()] + f'$texture$ = ${prefix}{start}$\n\t\t:i $Blend$ = $Add$'
        i = m.end()
    body = out + body[i:]
    # spawn after each `%GLOBAL%$<var>$ = %GLOBAL%$id$` that follows such a sprite
    def spawn(mm):
        blk_start = body.rfind('$CreateScreenElement$', 0, mm.start())
        if body.rfind('$create2dparticlesystem$', 0, mm.start()) > blk_start:
            return mm.group(0)                           # a particle system's id, not a sprite's
        tex = re.search(r'\$texture\$ = \$(WoR_HUD_(?:bolt|ball|urok)_)(\d+)\$', body[blk_start:mm.start()])
        if not tex:
            return mm.group(0)
        prefix, start = tex.group(1), int(tex.group(2))
        frames, step, _, loop = next((f, st, s0, lp) for (pf, f, st, s0, lp) in SPRITE_FLIPS.values()
                                     if pf == prefix and s0 == start)
        return (mm.group(0) + f'\t:i $spawnscriptnow$$WoR_HUD_flipbook$$params$ = :s{{$id$ = %GLOBAL%${mm.group(1)}$'
                f'$prefix$ = %s("{prefix}")$frames$ = %i({frames})$step$ = %i({step})$start$ = %i({start})'
                f'$loop$ = %i({loop}):s}}\n')
    return re.sub(r'\t:i %GLOBAL%\$(\w+)\$ = %GLOBAL%\$id\$\n', spawn, body)


def _glow_materials(body):
    """You_Rock_Text_Glow's particle systems: the animated ball materials -> the static one-cell ones, in turn."""
    k = iter(range(1000))
    return re.sub(r'\$material\$ = \$Mat_Lightning_ball_anim0[12]\$',
                  lambda m: f'$material$ = ${GLOW_MATS[next(k) % len(GLOW_MATS)]}$', body)


def ported_scripts():
    texts = {}
    out = []
    for name, rel in PORTED.items():
        if rel not in texts:
            texts[rel] = _decompile(rel).replace('\r\n', '\n').replace('\r', '\n')
        t = texts[rel]
        m = re.search(r'Script ' + re.escape(name) + r'\b[^\[]*\[', t)
        e = t.index('endfunction', m.end())
        body = t[m.end():e]
        assert not any(a in body for a in ('FIXME', 'select(', ':OFFSET', ':POS(')), f'{name}: decompiler artifact'
        # (thaw_4f %vec2(a,b) = a random float in a..b: the decompiler's spelling, compiled back as such)
        body = _rename(body)
        if name == 'create_exploding_text':
            # our converted WoR title font; the text in capitals ("YOU ROCK!" as in WoR; the DE passes "You Rock!")
            assert body.count('$fontgrid_title_a1$') == 1, 'create_exploding_text: font changed'
            body = body.replace('$fontgrid_title_a1$', f'${TITLE_FONT}$')
            # WoR plays its YOU ROCK sound as the sequence starts (audio_ui_gameplay_play_you_rock_sfx)
            # (sound OFF: $playsound$ of our pak sound froze the game at YOU ROCK twice, with and without an ID3 tag)
            if YR_SOUND_PLAY:
                body = f'\n\t:i $SoundEvent$${{StructQBKey event = {YR_EVENT}}}$' + body
            k = body.index('\t:i $FormatText$$checksumname$ = $cont_id$')
            body = (body[:k] + '\t:i $GetUpperCaseString$%GLOBAL%$text$\n\t:i %GLOBAL%$text$ = %GLOBAL%$uppercasestring$\n'
                    + body[k:])
        if name == 'do_exploding_text_physics':
            # v0.48 test: the letters floated around for ~7 s (WoR: they burst and drop off the bottom in ~1.5 s):
            # WoR's `$apply_gravity$ = $true$` form isn't read by the DE; its own scripts use the bare flags
            a = '$apply_gravity$ = $true$$apply_drag$ = $true$'
            assert body.count(a) == 1, 'do_exploding_text_physics: gravity line changed'
            body = body.replace(a, '$apply_gravity$$apply_drag$')
            # 2026-10-11 test: the letters should burst and fall faster: a 1.5x push (WoR 9000000) and double gravity.
            # The engine's screen element physics reads the global g_GRAVITY (DE value 1000.0, qb.pab); only exploding
            # text uses it in practice, set here for each burst
            a = '%GLOBAL%$explode_const$ = %i(9000000)'
            assert body.count(a) == 1, 'do_exploding_text_physics: explode_const changed'
            body = body.replace(a, f'%GLOBAL%$explode_const$ = %i({YR_EXPLODE})\n\t:i $change$$[6a831c8f]$ = %f({YR_GRAVITY:.1f})')
        if name == 'create_exploding_text':
            # WoR's text is ~1.2x ours (v0.48 videos, same canvas scale: 741 x 90 vs 630 x 72): the splitter scales
            # the word to fit_dims' width, so that is what sets the size
            a = '$fit_dims$ = %vec2(640.0,120.0)'
            assert body.count(a) == 1, 'create_exploding_text: fit_dims changed'
            body = body.replace(a, f'$fit_dims$ = %vec2({YOU_ROCK_FIT_W:.1f},120.0)')
        if name == 'You_Rock_Text_Glow':
            body = _glow_materials(body)
        if name in ('p2p_lightning_create_fx', 'UROK_FX_XPLOSION01'):
            body = _sprite_flipbooks(body)
            assert 'Mat_Lightning' not in body and 'Mat_UROK' not in body, f'{name}: animated material left'
        if name == 'p2p_lightning_create_fx':
            assert body.count('$parent$ = $root_window$') == 1, 'p2p_lightning_create_fx: parent changed'
            body = body.replace('$parent$ = $root_window$', f'$parent$ = ${FX_CONTAINER}$')
        out.append(f'Script WoR_HUD_{name} [' + body + 'endfunction\n]\n')
    # p2p_get_connector_length: |a| / |b| by comparison, the hypotenuse by Newton's method (12 steps)
    out.append(
        'Script WoR_HUD_p2p_get_connector_length [\n'
        '\t${\n\t\tStructFloatX2 source_pos\n\t\t{\n\t\t\tFloats [340.000, 360.000]\n\t\t}\n'
        '\t\tStructFloatX2 target_pos\n\t\t{\n\t\t\tFloats [940.000, 360.000]\n\t\t}\n\t}$\n'
        '\t:i %GLOBAL%$a$ = (%GLOBAL%$source_pos$:a{%i(0):a} - %GLOBAL%$target_pos$:a{%i(0):a})\n'
        '\t:i %GLOBAL%$b$ = (%GLOBAL%$source_pos$:a{%i(1):a} - %GLOBAL%$target_pos$:a{%i(1):a})\n'
        '\t:i if (%GLOBAL%$a$ < %f(0.0))\n\t\t:i %GLOBAL%$a$ = (%f(0.0) - %GLOBAL%$a$)\n\t:i endif\n'
        '\t:i if (%GLOBAL%$b$ < %f(0.0))\n\t\t:i %GLOBAL%$b$ = (%f(0.0) - %GLOBAL%$b$)\n\t:i endif\n'
        '\t:i %GLOBAL%$c_squared$ = ((%GLOBAL%$a$ * %GLOBAL%$a$) + (%GLOBAL%$b$ * %GLOBAL%$b$))\n'
        '\t:i %GLOBAL%$Length$ = (%GLOBAL%$a$ + %GLOBAL%$b$ + %f(1.0))\n'
        '\t:i $i$ = %i(0)\n'
        '\t:i while\n'
        '\t\t:i %GLOBAL%$Length$ = ((%GLOBAL%$Length$ + (%GLOBAL%$c_squared$ / %GLOBAL%$Length$)) * %f(0.5))\n'
        '\t\t:i $i$ = (%GLOBAL%$i$ + %i(1))\n'
        '\t:i loop_to %i(12)\n'
        '\t:i return$connector_length$ = %GLOBAL%$Length$\n'
        '\t:i endfunction\n]\n')
    return '\n'.join(out)


WRAPPER = (
    'Script WoR_HUD_Create_HandsOfGod [\n'
    '\t${StructQBString text = 0x0b24d99b}$\n'
    f'\t:i if NOT (~$[039b769b]$ = ${THEME}$)\n'
    '\t\t:i $WoR_HUD_Create_HandsOfGod_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $destroy_all_exploding_text$\n'
    # WoR clears the highway and HUD before YOU ROCK (v0.48 video: ours showed them for ~0.8 s): faded out here
    + ''.join(f'\t:i if $ScreenElementExists$$id$ = ${e}$\n\t\t:i ${e}$.$se_setprops$$alpha$ = %f(0.0)$time$ = %f(0.2)\n'
              '\t:i endif\n' for e in HIDE_ON_YOU_ROCK) +
    f'\t:i if NOT $ScreenElementExists$$id$ = ${FX_CONTAINER}$\n'
    '\t\t:i $CreateScreenElement$:s{\n'
    f'\t\t\t:i $type$ = $ContainerElement$\n\t\t\t:i $parent$ = $root_window$\n\t\t\t:i $id$ = ${FX_CONTAINER}$\n'
    '\t\t\t:i $dims$ = %vec2(1280.0,720.0)\n\t\t\t:i $just$ = :a{$left$$top$:a}\n\t\t\t:i $Pos$ = %vec2(0.0,0.0)\n'
    '\t\t:i :s}\n'
    '\t:i endif\n'
    f'\t:i $spawnscriptnow$$WoR_HUD_create_exploding_text$$params$ = :s{{$text$ = %s("{YOU_ROCK_TEXT}"):s}}\n'
    '\t:i if $ScreenElementExists$$id$ = $HandsOfGod$\n'
    '\t\t:i $DestroyScreenElement$$id$ = $HandsOfGod$\n'
    '\t:i endif\n'
    '\t:i $CreateScreenElement$:s{\n'
    '\t\t:i $type$ = $ContainerElement$\n\t\t:i $parent$ = $root_window$\n\t\t:i $id$ = $HandsOfGod$\n'
    '\t\t:i $dims$ = %vec2(1280.0,720.0)\n\t:i :s}\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_Create_HandsOfGod_orig [\n'
    '\t:i $printf$%s("WoR_HUD: Create_HandsOfGod placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')


def scripts():
    return WRAPPER + '\n' + FLIPBOOK + '\n' + ported_scripts() + ('\n' + YR_EVENT_SECTION if YR_SOUND_PLAY else '')


def load_script():
    """Add the choice to the You Rock option's inline list, then re-read it from the ini."""
    return ('\t:i $WoR_HUD_yr$ = (~$[f26e4c1f]$->$[1265cc79]$)\n'
            '\t:i $WoR_HUD_yr_list$ = (%GLOBAL%$WoR_HUD_yr$->$[5339ad04]$)\n'
            f'\t:i $WoR_HUD_choice$ = :s{{$Title$ = %s("{THEME_TITLE}")$value$ = ${THEME}$$value_string$ = %s("{THEME}"):s}}\n'
            '\t:i $AddArrayElement$$array$ = %GLOBAL%$WoR_HUD_yr_list$$element$ = %GLOBAL%$WoR_HUD_choice$\n'
            '\t:i $WoR_HUD_yr$ = :s{%GLOBAL%$WoR_HUD_yr$$[5339ad04]$ = %GLOBAL%$array$:s}\n'
            '\t:i $[325bc724]$$id$ = $[f26e4c1f]$$field$ = $[1265cc79]$$element$ = %GLOBAL%$WoR_HUD_yr$\n'
            '\t:i $[67da6f76]$(~$[f26e4c1f]$->$[1265cc79]$)\n'
            '\t:i $printf$%s("WoR_HUD: WoR You Rock theme registered")\n')
