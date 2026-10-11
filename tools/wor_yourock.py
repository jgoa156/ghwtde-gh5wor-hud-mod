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
MATERIALS = ('Mat_Lightning_Arc_Anim01', 'Mat_Lightning_Arc_Anim02', 'Mat_Lightning_ball_anim01',
             'Mat_Lightning_ball_anim02', 'Mat_UROK_Xplosion1', 'sys_Particle_Spark01_sys_Particle_Spark01')
# their textures (WoR basic_gems, keyed by tex\models\highway\<name>.dds): lightining_arc_anim01, ball_lightning01,
# note_hit_xplosion1, lil_spark, spark02, lil_star
TEXTURES = (0x0c30522c, 0x249c3fc1, 0xeaa76a98, 0x44e7b154, 0xadbdbfa2, 0x45c726d2)
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
    # WoR's letters: each letter plus a black copy 3,4 px down-right (the DE's version gives an orange edge)
    'split_text_into_physics_array_elements': 'scripts/guitar/menu/ui_exploding_text.qb.xen',
}


# v0.48 test: the glow and the bolts came out white: the DE doesn't apply the scripts' particle / sprite colours with
# these animated materials, so WoR's colours are baked into the (greyscale) textures: bolts in You_Rock_lightning_01's
# rgba1 / rgba2 average, the lightning balls between You_Rock_Text_Glow's start (123 grey) and end (0,64,255) colours.
TINT = {0x0c30522c: (154, 190, 255), 0x249c3fc1: (90, 140, 255)}


def texture_pngs():
    """[(texture key, png path)]: WoR's effect textures, the tinted ones written to build/pak_src/wor_yourock."""
    from PIL import Image
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'pak_src', 'wor_yourock')
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for k in TEXTURES:
        src = os.path.join(paths.WOR_EXTRACT, 'basic_gems_png', f'{k:08x}.png')
        if k in TINT:
            im = Image.open(src).convert('RGBA')
            r, g, b, a = im.split()
            t = TINT[k]
            im = Image.merge('RGBA', [c.point(lambda v, m=m: v * m // 255) for c, m in zip((r, g, b), t)] + [a])
            src = os.path.join(out_dir, f'{k:08x}.png')
            im.save(src)
        out.append((k, src))
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
        out.append(f'Script WoR_HUD_{name} [' + _rename(body) + 'endfunction\n]\n')
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


# WoR's create_exploding_text, on the DE's version of it (same physics helpers): WoR title font, light blue, WoR's
# effects (glow behind the letters, lightning bolts, then the explosion)
EXPLODING = (
    'Script WoR_HUD_create_exploding_text [\n'
    '\t${\n\t\tStructString parent = "you_rock_physics"\n\t\tStructQBStringQs text = 0x6f6d143d\n'
    '\t\tStructQBKey placement = top\n\t\tStructArray just\n\t\t{\n\t\t\tArrayQBKey\n\t\t\t[\n\t\t\t\tcenter\n\t\t\t\tbottom\n'
    '\t\t\t]\n\t\t}\n\t\tStructInt text_physics = 1\n\t}$\n'
    '\t:i $FormatText$$checksumname$ = $cont_id$%s("%p")$p$ = %GLOBAL%$parent$\n'
    '\t:i if $ScreenElementExists$$id$ = %GLOBAL%$cont_id$\n\t\t:i return\n\t:i endif\n'
    '\t:i if (%GLOBAL%$placement$ = $top$)\n\t\t:i $cont_pos$ = ~$g_ui_exploding_text_top_pos$\n'
    '\t:i else \n\t\t:i $cont_pos$ = ~$g_ui_exploding_text_bottom_pos$\n\t:i endif\n'
    '\t:i $check_screen_for_physics$\n'
    '\t:i if NOT $ScreenElementExists$$id$ = $exploding_particle_container$\n'
    '\t\t:i $create_exploding_particles$\n\t\t:i %GLOBAL%$explode$ = %i(1)\n'
    '\t:i else \n\t\t:i %GLOBAL%$explode$ = %i(0)\n\t:i endif\n'
    '\t:i $WoR_HUD_split_text_into_physics_array_elements$:s{\n'
    '\t\t:i $id$ = $yourock_text$\n\t\t:i $parent$ = %GLOBAL%$parent$\n\t\t:i $text$ = %GLOBAL%$text$\n'
    '\t\t:i $text_pos$ = %vec2(0.0,0.0)\n\t\t:i $cont_pos$ = %GLOBAL%$cont_pos$\n'
    '\t\t:i $space_between$ = %vec2(40.0,0.0)\n\t\t:i $fit_dims$ = %vec2(640.0,120.0)\n'
    '\t\t:i $just$ = %GLOBAL%$just$\n\t\t:i $placement$ = %GLOBAL%$placement$\n'
    '\t\t:i $flags$ = :s{\n'
    '\t\t\t:i $Scale$ = %f(1.05)\n\t\t\t:i $z_priority$ = %i(95)\n'
    f'\t\t\t:i $font$ = ${TITLE_FONT}$\n'
    '\t\t\t:i $rgba$ = :a{%i(100)%i(200)%i(255)%i(255):a}\n\t\t\t:i $alpha$ = %i(1)\n'
    '\t\t:i :s}\n\t\t:i $centered$\n\t:i :s}\n'
    '\t:i $CreateScreenElement$:s{\n'
    '\t\t:i $type$ = $ContainerElement$\n\t\t:i $parent$ = %GLOBAL%$cont_id$\n\t\t:i $dims$ = %vec2(100.0,100.0)\n'
    '\t\t:i $just$ = :a{$center$$center$:a}\n\t\t:i $pos_anchor$ = :a{$center$$center$:a}\n'
    '\t\t:i $Pos$ = %vec2(0.0,30.0)\n\t\t:i $z_priority$ = %i(0)\n\t:i :s}\n'
    '\t:i $fx_id$ = %GLOBAL%$id$\n'
    '\t:i $spawnscriptnow$$WoR_HUD_You_Rock_Text_Glow$$params$ = :s{$parent$ = %GLOBAL%$fx_id$:s}\n'
    '\t:i $spawnscriptnow$$WoR_HUD_You_Rock_lightning_01$\n'
    '\t:i $do_text_slam$:s{\n'
    '\t\t:i $parent$ = %GLOBAL%$parent$\n\t\t:i $explode$ = %GLOBAL%$explode$\n'
    '\t\t:i $text_physics$ = %GLOBAL%$text_physics$\n'
    '\t\t:i $exploding_text_array_size$ = %GLOBAL%$exploding_text_array_size$\n'
    '\t\t:i $cont_pos$ = %GLOBAL%$cont_pos$\n\t:i :s}\n'
    '\t:i $DestroyScreenElement$$id$ = %GLOBAL%$fx_id$\n'
    '\t:i $wait$${\n\t\tStructInt 2\n\t\tStructQBKey gameframes\n\t}$\n'
    '\t:i if NOT $ScreenElementExists$$id$ = %GLOBAL%$cont_id$\n\t\t:i return\n\t:i endif\n'
    '\t:i $CreateScreenElement$:s{\n'
    '\t\t:i $type$ = $ContainerElement$\n\t\t:i $parent$ = %GLOBAL%$cont_id$\n\t\t:i $dims$ = %vec2(100.0,100.0)\n'
    '\t\t:i $just$ = :a{$center$$center$:a}\n\t\t:i $pos_anchor$ = :a{$center$$center$:a}\n'
    '\t\t:i $Pos$ = %vec2(0.0,30.0)\n\t\t:i $z_priority$ = %i(0)\n\t:i :s}\n'
    '\t:i $fx_id$ = %GLOBAL%$id$\n'
    '\t:i $spawnscriptnow$$WoR_HUD_UROK_FX_XPLOSION01$$params$ = :s{$parent$ = %GLOBAL%$fx_id$:s}\n'
    '\t:i endfunction\n]\n')

WRAPPER = (
    'Script WoR_HUD_Create_HandsOfGod [\n'
    '\t${StructQBString text = 0x0b24d99b}$\n'
    f'\t:i if NOT (~$[039b769b]$ = ${THEME}$)\n'
    '\t\t:i $WoR_HUD_Create_HandsOfGod_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $destroy_all_exploding_text$\n'
    '\t:i $spawnscriptnow$$WoR_HUD_create_exploding_text$$params$ = :s{$text$ = %GLOBAL%$text$:s}\n'
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
    return EXPLODING + '\n' + WRAPPER + '\n' + ported_scripts()


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
