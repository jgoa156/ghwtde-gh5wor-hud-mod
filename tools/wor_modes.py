"""Multiplayer modes in the WoR style (user 2026-10-21; research: docs/MODES_RULES.md "Research 2026-10-21",
docs/research/de_layouts.md).

1. No messages above the highway in any mode with this theme (WoR shows none; the 1-player layout already hides its
   own, wor_1g.layout(no_messages=True)). Every per-player and band message of the DE goes through hud_create_message
   (note streaks, Hot Start, Star Power Ready, band streaks, the band fail hint, drum fills / solos; it also creates the
   band message container at runtime, so no desc edit reaches those): WoR_HUD_hud_create_message (plugin swap) returns
   before it when the theme has WoR_HUD_no_messages. The vocal phrase grades (vocals_message, on the vocal highway) are
   not messages above a highway and stay. Battle: its attack names (attack_ready_text, gated by the global
   show_battle_text) and attack alert cards (battle_alert_containerp1 / p2, built by create_battle_alert_frames, which
   wor_battle already wraps) are switched off there.
"""

FLAG = 'WoR_HUD_no_messages'
IS_OURS = f'$[4c1beb8d]$$value$ = ${FLAG}$'


def theme_extra():
    return f'\t\t\t\tStructInt {FLAG} = 1\n'


def battle_alerts_off():
    """Lines for the battle alert wrapper (after the DE's create_battle_alert_frames ran): with this theme the
    attack names and alert cards stay hidden; other themes get them back."""
    hide = ''.join(
        f'\t\t:i $extendcrc$$battle_alert_container$%s("p{p}")$out$ = $WoR_HUD_alert_id$\n'
        '\t\t:i if $ScreenElementExists$$id$ = %GLOBAL%$WoR_HUD_alert_id$\n'
        '\t\t\t:i $SetScreenElementProps$$id$ = %GLOBAL%$WoR_HUD_alert_id$$alpha$ = %i(0)\n'
        '\t\t:i endif\n' for p in (1, 2))
    return (f'\t:i if {IS_OURS}\n'
            '\t\t:i $change$$show_battle_text$ = %i(0)\n'
            + hide +
            '\t:i else \n'
            '\t\t:i $change$$show_battle_text$ = %i(1)\n'
            '\t:i endif\n')


SCRIPTS = (
    'Script WoR_HUD_hud_create_message [\n'
    f'\t:i if {IS_OURS}\n'
    '\t\t:i return\n'
    '\t:i endif\n'
    '\t:i $WoR_HUD_hud_create_message_orig$ isNull\n'
    '\t:i endfunction\n]\n\n'
    # placeholder: the plugin moves the DE script's data here
    'Script WoR_HUD_hud_create_message_orig [\n'
    '\t:i $printf$%s("WoR_HUD: hud message placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')
