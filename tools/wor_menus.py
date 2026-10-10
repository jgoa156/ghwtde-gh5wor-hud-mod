"""WoR popup boxes and pause menu (v0.49): "Guitar Hero: Warriors of Rock" choices for Menu Popup Theme and Pause Menu
Theme (mocks approved 2026-10-10: verify/mock_wor_popup.jpg, verify/mock_wor_pause.jpg).

The DE hardcodes both themes in its scripts: an unknown value falls to the GHWT:DE branch of the popup scripts
(descs dialog_box*_wtde) and to the World Tour branch of the pause scripts (desc pause_menu, generic make_menu items).
So "ghwor" runs those branches with:
  - the branch's desc globals pointed at our WoR descs while the theme is on (and back at the saved DE ones when not),
    by wrappers around create_popup_warning_menu and ui_create_pausemenu. Our descs keep every prop and alias the
    DE scripts use. The popup descs are the DE's own wtde descs restyled (desc_edit); the pause desc is our own.
  - wrappers for what a desc can't do: the popup options (WoR title font, gold; a red brush bar behind the selected
    one), their focus/unfocus, the popup title colour; the pause song title/artist line, the generic menu items'
    font/colour/alignment and their focus/unfocus (menu_item_focus / _unfocus) while our pause menu is up.
The wrappers replace the DE scripts through plugin 1.26's kScriptSwaps (the DE scripts move to *_orig placeholders).
Assets (frame, brush bar, WoR title font) ship in wor_ui.UI_PAK.
"""
import os, re, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desc_edit, desc_gen, paths, wor_ui  # noqa: E402
from desc_gen import E  # noqa: E402

THEME, THEME_TITLE = wor_ui.THEME, wor_ui.THEME_TITLE
TITLE_FONT = 'WoR_HUD_title_a1'                          # WoR's fontgrid_title_a1 (song titles, menu items)
TITLE_FONT_SRC = paths.wor('ui_shared', 'fontgrid_title_a1.fnt.xen')
TEXT_FONT = wor_ui.PILL_FONT                             # WoR's fontgrid_text_a1
BLANK, WHITE, FRAME, BAR = 'WoR_HUD_ui_blank', 'WoR_HUD_white', 'WoR_HUD_dialog_frame', 'WoR_HUD_light_bar'
GOLD, WHITE_C, RED = (238, 190, 92, 255), (255, 255, 255, 255), (232, 36, 44, 255)
CREAM, BROWN = (232, 214, 170, 255), (60, 34, 14, 255)

# ---- assets


def images(out_dir):
    """Frame (WoR's dialog_bg left half + its mirror), brush bar, blank and white; returns the PNG paths."""
    ui = paths.WOR_UI_PNG
    half = Image.open(os.path.join(ui, 'dialog_bg.png')).convert('RGBA')
    frame = Image.new('RGBA', (1024, 512))
    frame.paste(half, (0, 0))
    frame.paste(half.transpose(Image.FLIP_LEFT_RIGHT), (512, 0))
    out = []
    for name, im in ((FRAME, frame), (BAR, Image.open(os.path.join(ui, 'light_bar.png')).convert('RGBA')),
                     (BLANK, Image.new('RGBA', (8, 8), (0, 0, 0, 0))), (WHITE, Image.new('RGBA', (8, 8), (255,) * 4))):
        p = os.path.join(out_dir, name + '.png')
        im.save(p)
        out.append(p)
    return out


# ---- popup descs: the DE's wtde ones (ui_shared_wtde.pak), restyled
DLG = {   # ours -> (DE desc global, file in ui_shared_wtde, title id, message id, vmenu container y or None)
    'main': ('3de6e82d', '0xc5233a7c.qb.xen', 'dlog_title', 'dlog_message', 137.0),
    'long': ('64c0d8c0', '0x8914e320.qb.xen', 'dlog_title', 'dlog_message', 150.0),
    'none': ('a26a853d', '0x0d1e6a8a.qb.xen', 'alert_title', 'alert_message', None),
}
HIDE_TEX = ('0x7aa12d50', 'mixer_glow_64', 'dialog_side_chain', 'dialog_chain', 'dialog_bg_menu')
BANNER_Y = 168.0                                          # the frame's gold banner middle (canvas units)


def popup_desc(kind, de_text):
    """Our WoR version of one DE wtde dialog desc (same tree, props and aliases)."""
    key, _, title, message, menu_y = DLG[kind]
    t = de_text.replace('\r\n', '\n').replace('\r', '\n')
    m = re.search(r'SectionStruct (?:0x)?0*' + key.lstrip('0') + r'\b', t)
    i = m.start()
    j, depth = t.index('{', i), 0
    for k in range(j, len(t)):
        depth += {'{': 1, '}': -1}.get(t[k], 0)
        if depth == 0:
            break
    d = t[i:k + 1]
    name = f'WoR_HUD_dlg_{kind}'
    d = re.sub(r'^SectionStruct \S+?\s*\{', f'SectionStruct uidesc_{name}\n{{', d, count=1)
    d = re.sub(r'StructQBKey name = \S+', f'StructQBKey name = uidesc_{name}', d, count=1)
    for tex in HIDE_TEX:
        d = re.sub(rf'StructQBKey texture = {re.escape(tex)}\b', f'StructQBKey texture = {BLANK}', d)
    d = desc_edit.set_elem(d, 'dialog_bg', texture=FRAME, pos=(0, 0), dims=(980, 534))
    d = desc_edit.set_elem(d, 'title_text_container', pos=(640, BANNER_Y - 15))
    d = desc_edit.set_elem(d, title, font=TITLE_FONT, dims=(560, 44), rgba=BROWN)
    d = desc_edit.set_elem(d, message, font=TEXT_FONT, pos=(640, 232), dims=(720, 150), scale=(0.67, 0.67), rgba=CREAM)
    if menu_y is not None:
        d = desc_edit.set_elem(d, 'dlog_vmenu_container', pos=(0.13092, menu_y))
    return d


# ---- pause desc (ours; the DE pause scripts use: title_text, glow_alpha, alias_menu, alias_pause_fist_container)


def pause_desc():
    root = E('pause_bg', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        E('WoR_pause_black', 'SpriteElement', dims=(1280, 720), just=(-1, -1), texture=WHITE, rgba=(8, 9, 10, 255)),
        E('WoR_glow', 'SpriteElement', dims=(8, 8), texture=BLANK, alpha=0.0),            # glow_alpha (pulsed)
        E('pause_fist_container', 'ContainerElement', dims=(1280, 720), just=(-1, -1)),   # slid in: kept empty
        E('WoR_song', 'TextBlockElement', pos=(176, 62), dims=(900, 70), just=(-1, -1), scale=(0.8, 0.8), z=2,
          rgba=RED, font=TITLE_FONT, internal_just=(-1, -1)),
        E('WoR_artist', 'TextBlockElement', pos=(178, 146), dims=(900, 40), just=(-1, -1), scale=(0.63, 0.63), z=2,
          rgba=CREAM, font=TEXT_FONT, internal_just=(-1, -1)),
        E('title', 'TextBlockElement', pos=(1232, 146), dims=(400, 60), just=(1, -1), scale=(0.76, 0.76), z=2,
          rgba=GOLD, font=TITLE_FONT, internal_just=(1, -1)),
        E('menu', 'ContainerElement', pos=(1212, 268), dims=(400, 300), just=(1, -1), z=3)])
    return desc_gen.desc('WoR_HUD_pause', root,
                         props=[('title_text', 'title', 'text'), ('glow_alpha', 'WoR_glow', 'alpha'),
                                ('WoR_song_text', 'WoR_song', 'text'), ('WoR_artist_text', 'WoR_artist', 'text')],
                         aliases=[('alias_menu', 'menu'), ('alias_pause_fist_container', 'pause_fist_container')])


PAUSE_DE = '0be28f31'                                     # uidesc_pause_menu


# ---- scripts


def _rgba(c):
    return ':a{' + ''.join(f'%i({v})' for v in c) + ':a}'


WAIT = '$wait$${\n\t\tStructInt 1\n\t\tStructQBKey gameframe\n\t}$'
IS_POPUP = f'(~$[14710f34]$ = ${THEME}$)'
IS_PAUSE = f'(~$[074101eb]$ = ${THEME}$)'

SAVE_LOAD = (''.join(f'\t:i $change$$WoR_HUD_de_dlg_{k}$ = (~$[{v[0]}]$)\n' for k, v in DLG.items()) +
             f'\t:i $change$$WoR_HUD_de_pause$ = (~$[{PAUSE_DE}]$)\n')


def _swap(on):
    """Point the DE desc globals at ours (on) or back at the saved DE ones."""
    if on == 'popup':
        return ''.join(f'\t\t:i $change$$[{v[0]}]$ = (~$uidesc_WoR_HUD_dlg_{k}$)\n' for k, v in DLG.items())
    if on == 'popup_de':
        return ''.join(f'\t\t:i $change$$[{v[0]}]$ = (~$WoR_HUD_de_dlg_{k}$)\n' for k, v in DLG.items())
    if on == 'pause':
        return f'\t\t:i $change$$[{PAUSE_DE}]$ = (~$uidesc_WoR_HUD_pause$)\n'
    return f'\t\t:i $change$$[{PAUSE_DE}]$ = (~$WoR_HUD_de_pause$)\n'


SCRIPTS = (
    # ---- popup
    'Script WoR_HUD_create_popup_warning_menu [\n'
    f'\t:i if {IS_POPUP}\n' + _swap('popup') + '\t:i else \n' + _swap('popup_de') + '\t:i endif\n'
    '\t:i $WoR_HUD_create_popup_warning_menu_orig$ isNull\n'
    '\t:i if $GotParam$$menu_id$\n'
    '\t\t:i return$menu_id$ = %GLOBAL%$menu_id$\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_create_popup_warning_text [\n'
    '\t:i $WoR_HUD_create_popup_warning_text_orig$ isNull\n'
    f'\t:i if {IS_POPUP}\n'
    f'\t\t:i $PopupElement$.$setprops$:s{{$PopupTitle_rgba$ = {_rgba(BROWN)}:s}}\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # one option: the DE's GHWT:DE branch, in WoR's title font and gold, with a hidden brush bar behind
    'Script WoR_HUD_create_popup_warning_menu_option [\n'
    f'\t:i if NOT {IS_POPUP}\n'
    '\t\t:i $WoR_HUD_create_popup_warning_menu_option_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i %GLOBAL%$focus_params$ = :s{$use_highlight$ = %i(0):s}\n'
    '\t:i if $StructureContains$$structure$ = %GLOBAL%$option$$func_params$\n'
    '\t\t:i %GLOBAL%$func_params$ = (%GLOBAL%$option$->$func_params$)\n'
    '\t:i endif\n'
    '\t:i $sound_func$ = $[fcf0dd3b]$\n'
    '\t:i if $StructureContains$$structure$ = %GLOBAL%$option$$sound_func$\n'
    '\t\t:i $sound_func$ = (%GLOBAL%$option$->$sound_func$)\n'
    '\t:i endif\n'
    '\t:i if $StructureContains$$structure$ = %GLOBAL%$option$$no_sound$\n'
    '\t\t:i $sound_func$ = $NullScript$\n'
    '\t:i endif\n'
    '\t:i $CreateScreenElement$:s{\n'
    '\t\t:i $type$ = $TextBlockElement$\n'
    '\t\t:i $dims$ = %GLOBAL%$dims$\n'
    f'\t\t:i $font$ = ${TITLE_FONT}$\n'
    '\t\t:i $parent$ = %GLOBAL%$parent$\n'
    '\t\t:i $local_id$ = $text$\n'
    f'\t\t:i $rgba$ = {_rgba(GOLD)}\n'
    '\t\t:i $font_spacing$ = %i(0)\n'
    '\t\t:i $just$ = :a{$center$$center$:a}\n'
    '\t\t:i $internal_just$ = :a{$center$$center$:a}\n'
    '\t\t:i $z_priority$ = (%GLOBAL%$z$ + %i(2))\n'
    '\t\t:i (%GLOBAL%$option$)\n'
    '\t\t:i $fit_width$ = $scale each line if larger$\n'
    '\t\t:i $fit_height$ = $scale to fit$\n'
    '\t\t:i $scale_mode$ = $proportional$\n'
    '\t\t:i $event_handlers$ = :a{\n'
    '\t\t\t:i :s{$focus$$menu_popup_focus$$params$ = %GLOBAL%$focus_params$:s}\n'
    '\t\t\t:i :s{$unfocus$$menu_popup_unfocus$$params$ = %GLOBAL%$focus_params$:s}\n'
    '\t\t\t:i :s{$pad_choose$%GLOBAL%$sound_func$:s}\n'
    '\t\t\t:i :s{$pad_choose$(%GLOBAL%$option$->$func$)$params$ = %GLOBAL%$func_params$:s}\n'
    '\t\t:i :a}\n'
    '\t:i :s}\n'
    '\t:i $CreateScreenElement$:s{\n'
    '\t\t:i $type$ = $SpriteElement$\n'
    '\t\t:i $parent$ = %GLOBAL%$id$\n'
    '\t\t:i $local_id$ = $WoR_HUD_bar$\n'
    f'\t\t:i $texture$ = ${BAR}$\n'
    '\t\t:i $dims$ = %vec2(330.0,42.0)\n'
    '\t\t:i $pos_anchor$ = :a{$center$$center$:a}\n'
    '\t\t:i $just$ = :a{$center$$center$:a}\n'
    '\t\t:i $alpha$ = %i(0)\n'
    '\t\t:i $z_priority$ = (%GLOBAL%$z$ + %i(1))\n'
    '\t:i :s}\n'
    '\t:i if $StructureContains$$structure$ = %GLOBAL%$option$$not_focusable$\n'
    '\t\t:i %GLOBAL%$id$.$se_setprops$$non_focusable$$rgba$ = ((~$g_menu_colors$)->$alert_red$)\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_menu_popup_focus [\n'
    f'\t:i if NOT {IS_POPUP}\n'
    '\t\t:i $WoR_HUD_menu_popup_focus_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $obj_getid$\n'
    f'\t:i %GLOBAL%$ObjID$.$se_setprops$$rgba$ = {_rgba(WHITE_C)}\n'
    '\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$ObjID$$child$ = $WoR_HUD_bar$:s}\n'
    '\t\t:i $SetScreenElementProps$$id$ = :s{%GLOBAL%$ObjID$$child$ = $WoR_HUD_bar$:s}$alpha$ = %i(1)\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_menu_popup_unfocus [\n'
    f'\t:i if NOT {IS_POPUP}\n'
    '\t\t:i $WoR_HUD_menu_popup_unfocus_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $obj_getid$\n'
    f'\t:i %GLOBAL%$ObjID$.$se_setprops$$rgba$ = {_rgba(GOLD)}\n'
    '\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$ObjID$$child$ = $WoR_HUD_bar$:s}\n'
    '\t\t:i $SetScreenElementProps$$id$ = :s{%GLOBAL%$ObjID$$child$ = $WoR_HUD_bar$:s}$alpha$ = %i(0)\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # ---- pause
    'Script WoR_HUD_ui_create_pausemenu [\n'
    f'\t:i if {IS_PAUSE}\n' + _swap('pause') + '\t:i else \n' + _swap('pause_de') + '\t:i endif\n'
    '\t:i $WoR_HUD_ui_create_pausemenu_orig$ isNull\n'
    f'\t:i if {IS_PAUSE}\n'
    '\t\t:i if $ScreenElementExists$$id$ = $pausemenu_bg$\n'
    '\t\t\t:i $WoR_HUD_pause_song_info$\n'
    '\t\t\t:i $WoR_HUD_pause_style_items$\n'
    '\t\t:i endif\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_pause_song_info [\n'
    '\t:i $get_song_title$$song$ = (~$current_song$)\n'
    '\t:i $get_song_artist_text$$song$ = (~$current_song$)\n'
    '\t:i $get_song_artist$$song$ = (~$current_song$)\n'
    '\t:i $FormatText$$textname$ = $WoR_line$%s("%a %b")$a$ = %GLOBAL%$song_artist_text$$b$ = %GLOBAL%$song_artist$\n'
    '\t:i $pausemenu_bg$.$se_setprops$$WoR_song_text$ = %GLOBAL%$song_title$$WoR_artist_text$ = %GLOBAL%$WoR_line$\n'
    '\t:i endfunction\n]\n\n'
    # the generic menu's items (container + text child): WoR title font, gold, right-aligned
    'Script WoR_HUD_pause_style_items [\n'
    '\t:i if NOT $ScreenElementExists$$id$ = $current_menu$\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $GetScreenElementChildren$$id$ = $current_menu$\n'
    '\t:i $GetArraySize$%GLOBAL%$children$\n'
    '\t:i $i$ = %i(0)\n'
    '\t:i while\n'
    '\t\t:i $item$ = (%GLOBAL%$children$:a{%GLOBAL%$i$:a})\n'
    '\t\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$item$$child$ = $text$:s}\n'
    f'\t\t\t:i $SetScreenElementProps$$id$ = :s{{%GLOBAL%$item$$child$ = $text$:s}}$font$ = ${TITLE_FONT}$$rgba$ = {_rgba(GOLD)}'
    '$just$ = :a{$right$$center$:a}$internal_just$ = :a{$right$$center$:a}\n'
    '\t\t:i endif\n'
    '\t\t:i $i$ = (%GLOBAL%$i$ + %i(1))\n'
    '\t:i loop_to %GLOBAL%$array_size$\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_menu_item_focus [\n'
    # two plain ifs: a ${...}$ struct argument inside a parenthesised AND crashed the game (QB reader, 0x5f0a8e)
    f'\t:i if NOT {IS_PAUSE}\n'
    '\t\t:i $WoR_HUD_menu_item_focus_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i if NOT $ScreenElementExists$$id$ = $pausemenu_bg$\n'
    '\t\t:i $WoR_HUD_menu_item_focus_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    f'\t:i $SetScreenElementProps$$id$ = :s{{%GLOBAL%$id$$child$ = $text$:s}}$font$ = ${TITLE_FONT}$$rgba$ = {_rgba(WHITE_C)}\n'
    '\t:i if NOT $ScreenElementExists$$id$ = :s{%GLOBAL%$id$$child$ = $WoR_HUD_bar$:s}\n'
    '\t\t:i $CreateScreenElement$:s{\n'
    '\t\t\t:i $type$ = $SpriteElement$\n'
    '\t\t\t:i $parent$ = %GLOBAL%$id$\n'
    '\t\t\t:i $local_id$ = $WoR_HUD_bar$\n'
    f'\t\t\t:i $texture$ = ${BAR}$\n'
    '\t\t\t:i $dims$ = %vec2(330.0,46.0)\n'
    '\t\t\t:i $pos_anchor$ = :a{$right$$center$:a}\n'
    '\t\t\t:i $just$ = :a{$right$$center$:a}\n'
    '\t\t\t:i $Pos$ = %vec2(10.0,0.0)\n'
    '\t\t\t:i $z_priority$ = %i(1)\n'
    '\t\t:i :s}\n'
    '\t:i endif\n'
    '\t:i $SetScreenElementProps$$id$ = :s{%GLOBAL%$id$$child$ = $WoR_HUD_bar$:s}$alpha$ = %i(1)\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_menu_item_unfocus [\n'
    f'\t:i if NOT {IS_PAUSE}\n'
    '\t\t:i $WoR_HUD_menu_item_unfocus_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i if NOT $ScreenElementExists$$id$ = $pausemenu_bg$\n'
    '\t\t:i $WoR_HUD_menu_item_unfocus_orig$ isNull\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    f'\t:i $SetScreenElementProps$$id$ = :s{{%GLOBAL%$id$$child$ = $text$:s}}$font$ = ${TITLE_FONT}$$rgba$ = {_rgba(GOLD)}\n'
    '\t:i if $ScreenElementExists$$id$ = :s{%GLOBAL%$id$$child$ = $WoR_HUD_bar$:s}\n'
    '\t\t:i $SetScreenElementProps$$id$ = :s{%GLOBAL%$id$$child$ = $WoR_HUD_bar$:s}$alpha$ = %i(0)\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # placeholders: the plugin moves the DE scripts' data here
    + ''.join(f'Script WoR_HUD_{s}_orig [\n'
              f'\t:i $printf$%s("WoR_HUD: {s} placeholder ran, plugin swap missing")\n'
              '\t:i endfunction\n]\n\n'
              for s in ('create_popup_warning_menu', 'create_popup_warning_text', 'create_popup_warning_menu_option',
                        'menu_popup_focus', 'menu_popup_unfocus', 'ui_create_pausemenu', 'menu_item_focus',
                        'menu_item_unfocus')))

# DE script -> wrapper (plugin kScriptSwaps; the order there doesn't matter)
SWAPS = ('create_popup_warning_menu', 'create_popup_warning_text', 'create_popup_warning_menu_option',
         'menu_popup_focus', 'menu_popup_unfocus', 'ui_create_pausemenu', 'menu_item_focus', 'menu_item_unfocus')


def load_script():
    """WoR_HUD_Load lines: save the DE descs we swap, add both choices, re-read both settings from the ini."""
    out = SAVE_LOAD
    for lst, entry in (('1b1562e7', '76be7b6c'), ('06eb9e90', 'b995aa32')):
        out += (f'\t:i $WoR_HUD_choice$ = :s{{$Title$ = %s("{THEME_TITLE}")$value$ = ${THEME}$$value_string$ = %s("{THEME}"):s}}\n'
                f'\t:i $[6f2c7249]$$id$ = $[{lst}]$$element$ = %GLOBAL%$WoR_HUD_choice$\n'
                f'\t:i $[67da6f76]$(~$[f26e4c1f]$->$[{entry}]$)\n')
    return out + '\t:i $printf$%s("WoR_HUD: WoR popup and pause menu themes registered")\n'


def sections(de_texts):
    """Our descs + placeholders for the saved DE descs. de_texts: {file name: decompiled text} of ui_shared_wtde."""
    out = [popup_desc(k, de_texts[v[1]]) for k, v in DLG.items()] + [pause_desc()]
    out += [f'SectionStruct WoR_HUD_de_dlg_{k}\n{{\n\tStructHeader\n\t{{\n\t\tStructInt unset = 1\n\t}}\n}}' for k in DLG]
    out += ['SectionStruct WoR_HUD_de_pause\n{\n\tStructHeader\n\t{\n\t\tStructInt unset = 1\n\t}\n}']
    return out
