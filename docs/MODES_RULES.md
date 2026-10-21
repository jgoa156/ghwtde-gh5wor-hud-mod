# Multiplayer / vocals / face-off rules: GHWT:DE vs WoR (2026-10-16)

Goal: list the WoR mechanics the DE does not have, so the HUD port shows WoR art only for mechanics the DE runs, and
leaves out (or repurposes) widgets for mechanics it doesn't. Sources: decompiled scripts (`ghwt-extract`,
`ghwor-extract`), frames of the user's clips (`WOR_face_off`, `WOR_full_band_gameplay`, `WOR_microphone_gameplay`).
Items marked (verify) come from memory of the games, not from scripts.

## Game modes

| Mode | DE (script `game_mode`) | WoR | HUD action |
|---|---|---|---|
| Career / quickplay 1-4 players | `p1..p4_career`, `p1..p4_quickplay` | yes | port (band layout) |
| Co-op 2p | `p2_coop` | merged into band | port as 2p band |
| Face-Off (alternating sections) | `p2_faceoff` | `p2_faceoff` | port |
| Pro Face-Off | `p2_pro_faceoff`, `p4_pro_faceoff` | yes (in Competitive) | port; 4p Pro Face-Off = WoR 4-lane ranked layout |
| Battle (attacks) | `p2_battle` (+ `battle_do_or_die` option) | **removed** | keep the DE battle HUD; no WoR art exists |
| Streakers, Do or Die, Perfectionist, Momentum, Elimination, team variants, Democracy Rocks vote | **none** | yes (clip 1) | **do not implement** |

## Mechanics

| Mechanic | DE | WoR | HUD action |
|---|---|---|---|
| Per-player star power meter, SP doubles own multiplier (4x, bass 6x, vocals x8 shown) | yes | yes | ported |
| Band multiplier widget (`alias_band_multiplier`) | yes (hud theme) | yes (`HUD_attach_widget_band_multiplier`, rocket x3/x4/x5 next to the band score, clip 2) | port the WoR rocket on the DE value |
| Band streak (`HUD_band_streak_notify` / `_end`, vocal highway `band_streak_lines_alpha`) | yes | yes | port WoR message style |
| Shared band rock meter | yes | yes | ported (needle) |
| **Band Moments** (gem materials `Mat_Gem_*_Band_Moment*`, all players hit a section for a bonus) | **none** | yes | **do not implement**; no band-moment gems |
| **Revive meter** (`HUD_revive_meter_*` textures; failed player comes back as the band plays) | **none** (DE: SP revives a failed player, verify) | yes | **do not implement** the meter; keep the DE revive feedback |
| Quest-mode character powers (Warrior transforms, special multipliers) | none | Quest mode only | out of scope |
| Per-player streak counter under the score | yes | yes (clips 1, 2) | port |
| Ranking badges 1st..4th in competitive | Pro Face-Off 4p only (verify) | yes | port for `p4_pro_faceoff` only |

## Layouts seen in the clips

- Band (clip 2): vocal highway on top with lyrics, 3 instrument lanes, band score + band rocket multiplier + star count
  top-right, per-lane multiplier bubble right of each lane.
- Vocals (clip 3): vocal track mid-screen, multiplier/SP pill left of the now-line, score + stars top-right of the track.
- Competitive 4p (clip 1): per-player score bars over each lane, ranking badge left, multiplier bubble right, central
  needle over lanes 2-3.

## Conclusion

Port: band layout, band multiplier rocket, band streak messages, vocals layout, Face-Off and Pro Face-Off (2p and 4p).
Skip: Band Moments, revive meter, WoR competitive variants (Streakers etc.), Democracy Rocks, Quest powers.
Battle mode: reworked in the WoR style on our own layout (see HANDOFF / MODLOG; the DE has no WoR art for it).

## Research 2026-10-21 (face-off, band, vocals; user request)

Full reports (with sources): `docs/research/wiki_modes.md` (wiki mechanics), `docs/research/wor_assets.md` (WoR HUD assets
from the three WoR clips, + `docs/research/ui_shared_desc/`, 24 decompiled WoR ui_shared descs), `docs/research/de_layouts.md`
(how the DE builds each mode's HUD). The DE runs WT mechanics: the HUD follows the WT column.

### Mechanics that matter for the port

- Band star power: WT = one shared meter any player can trigger; WoR = per player (+ overflow to teammates). The DE keeps a
  per-player `star_power_amount` AND a band aggregate; the per-player value is only wired to a container child named
  `Star_Power` (or `vocal_multiplier_star`): name ours `Star_Power` for a per-player tube in band (what the engine writes
  into it in band mode is not verified in game). User idea: show the same amount on every player's tube.
- Band multiplier: WT x2-x4 (SP together); WoR up to x11 with band moments (DE has none: don't show). Per-instrument
  multiplier is the same in both (x1-x4, x8 with SP, 10 notes per step); Quest powers: skip.
- Rock meter: WT shared band meter + small individual ones; WoR per-player; WoR's revive meter has no DE mechanic.
- Vocals: WoR's five precision grades (from `vocals.qs.xen`): SLOPPY!, ROUGH, AVERAGE, SOLID, EXCELLENT! (clips only show
  EXCELLENT!); WT proper only flashes a colour at the phrase end (the DE's `vocals_message` can show Excellent / Solid /
  Average / Rough / Sloppy-style text). No "Awesome / Strong / OK" source found.
- Versus: the wiki is unclear on whether WoR's competitive view swaps the rock meter for a versus meter and on a 1st-4th
  ladder; the clips (WOR_face_off) show per-player score bars with a placing badge ("1st" glowing for the leader) and the
  semicircle dial at top centre. The DE has no placing logic (no placing text in its HUD); the dial can show who leads.

### WoR assets (details and paths in wor_assets.md)

| Element | Files (ghwor-extract) |
|---|---|
| per-player score bar, team stripe | ui_shared_png2 `competitive_meter_back`, `competitive_meter_frame`, `competitive_stripe`, `vocal_meter_backing` (desc `uidesc_vocals_competitive_meters`) |
| gap box under the score | `streak`, `streak_front` |
| versus dial + team score bars | z_in_game_png2 `HUD_band_battle_meter_OFF/amber_ON/violet_ON/needle/shadow`, `HUD_band_battle_score(_back)` (`uidesc_hud_band_battle`) |
| placing badge | `HUD_place_icon_back/front` + text; `starburst_256` for the leader (`uidesc_hud_sidebar_rankmeter`) |
| multiplier bubble | `hud_meter_combo_frame2_apm`, `HUD_meter_combo_multiback`, `HUD_meter_combo_LED_01`-`10` |
| band score / stars / bulb / streak | `band_HUD_star_score_meter(_front)`, `band_HUD_gold_star_*`, `band_HUD_silver_star_*`, `band_HUD_multiplier_bulb`, `bulb_x`, `band_HUD_multiplier_one`-`eleven`, `streak(_front)` (`uidesc_star_meter`) |
| vocals pill / highway | `uidesc_vocals_all_meters` + sub-descs, `uidesc_vocals_highway` |
| instrument icons | `band_hud_guitar2`, `bass2`, `drums2`, `microphone2` (no keys); failed = same glyphs as `skull` / `dead_icon` + `vof01` vignettes |

Follow-up (all found, details in wor_assets.md "Follow-up"): failed player = the instrument glyph itself
(`band_hud_*2`; `icon_dead_256` is only an unused script fallback) + `vof01` corner vignettes; team colours band_color1-8 =
uicolorref_palette p1_md (65,75,235) blue, p2_md (238,138,93) orange, p3_md (213,130,190), p4_md (200,187,77), ...;
no per-rank colours (rank text + starburst for 1st only); the bar's right glyph = difficulty icon `icon_difficulty_*`;
WoR has no band-wide rock meter: each highway's sidebar rock tube (`uidesc_hud_sidebar_rockmeter`, what our 1-player HUD
ports); song-start instrument icons `mixer_icon_guitar` / `_bass` / `_drums` / `_vox`.

### How the DE builds each mode (details in de_layouts.md)

- `update_hud_layout` ignores the game mode: only player count + parts pick `hud_2g` (shared by Face-Off, Pro Face-Off 2p,
  Co-op), `hud_3g1v` (4p Pro Face-Off), `hud_1g1v` / `hud_2g1v` (band with vocals), `hud_1v`; battle alone has its own key
  (0x6bd128d8). Our row sets the band layouts to WT+ copies (except `hud_1g`); missing: `hud_2v`, vocalist multiplier arrays
  `112feba3` / `bc95780d`.
- **The "01234567" / "50" placeholders in the band part of the user's clip**: the user's ini has `HUDBossFOMeter=1`, which
  keeps the versus meter (`HUD_band_battle`, a child of every band desc) alive in Band / Co-op with no widget attached, so it
  shows its design defaults (QS `bf2409fb` / `c6081e83`). Fix: our own versus-meter desc, blank when unattached.
- Face-Off / Pro Face-Off: the DE's GH3-style versus bar carries scores, dial, SP bulbs, multipliers, streaks; the rock
  meter is removed by the DE.
- The highway instrument icon is written into the x1 multiplier slot (hw script, after the theme arrays are read): a
  theme array can't stop it; a script copy (symbol swap) is needed.
- Messages above the highway: every per-player / band message goes through `hud_create_message` (11 call sites: note streak,
  Hot Start, Star Power Ready, band streak, band fail hint, drum fill / solo); outside it: `vocals_message`, battle
  `attack_ready_text` (global `show_battle_text`, default 1), battle alerts (`create_battle_alert_frames`, already wrapped).
  Hook: wrap `hud_create_message` (symbol swap) to return early with a theme flag; alpha 0 on `message` /
  `hud_message_fire` in the copied descs covers the per-player ones.

### Plan (needs mocks + approval before building)

1. No messages above the highway in every mode for this theme (hook above). Cheap and independent: can ship first.
2. Face-Off / Pro Face-Off: our own versus-meter desc (template: the VH copy `hud_vh_qb/0x6430019d.txt`) with WoR's score bars,
   dial, placing badge (leader glow bound to the amber / violet alphas), multiplier bubble; highways spaced like battle.
3. Band: WoR band score box + multiplier bulb + streak box, per-player SP tube named `Star_Power` (same amount per player),
   rock meter kept, instrument icon removed from the highway, WoR failed-instrument art.
4. Vocals: WoR vocal meters + grade wording (existing `vocals_message` slots).
