# DE HUD layouts per mode, as used by our theme (research, 2026-10-21)

Question: which layouts, descs, widgets and scripts the GHWT:DE builds in each mode for our `ghwor` theme, what our
`build.py` sets and what falls back to the DE default (that fallback is what the user sees in
`Downloads\Video Project 25.mp4`). Read-only research: nothing in the mod or the game was changed.

## Conventions and sources

Decompiled DE scripts are in `E:\Dev\ghwt\ghwt-extract` (game assets: never commit them or copies of them).
**Those `.txt` files use bare CR line ends** (`\r`): grep / ripgrep see ONE line and `Read` shows one line. Line numbers
below are CR-delimited (what an editor that treats CR as a line break shows; `tr '\r' '\n' < f` gives the same numbers).
Short names:

| tag | file |
|---|---|
| GH | `ghwt-extract/hudscripts/guitar_hud.txt` (identical: `hud2d/guitar_hud.txt`, `optusers/scripts__guitar__guitar_hud.txt`) |
| G2D | `ghwt-extract/hud2d/guitar_hud_2d.txt` (= `optusers/scripts__guitar__guitar_hud_2d.txt`) |
| HW | `ghwt-extract/hudscripts/hud_widgets.txt` |
| HM | `ghwt-extract/optusers/scripts__guitar__hud__hud_messages.txt` |
| GE | `ghwt-extract/optusers/scripts__guitar__guitar_events.txt` |
| GB, GBI | `optusers/scripts__guitar__guitar_battle.txt`, `optusers/scripts__guitar__guitar_battle_hud_icons.txt` |
| GSP | `ghwt-extract/dec_sp/guitar_starpower.txt` |
| HT | `ghwt-extract/hudthemes.txt` (theme table `0x8ef7f1be`); HL = `ghwt-extract/layouts/hud_layouts.txt` |
| MOD | `ghwt-wor-hud/build/WoR_HUD/WoR_HUD.txt` (our decompiled build, CRLF, normal line numbers) |
| INI | `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini` |
| *orig:* | scripts NOT decompiled in ghwt-extract: the raw `ghwt-extract/tb/scripts/guitar/<name>.qb.xen` (vanilla, same text as the DE's) decompiled by me with `node tools/guitar-hero-sdk/sdk.js decompile` (`gamemode`, `faceoff`, `vocals_highway`, `vocals`, `guitar`, `guitar_events`, `guitar_hud_2d_faceoff/_battle`). Line numbers are of that output after CR->LF. Repro: copy the .qb.xen to a scratch dir and run the SDK there. |
| QS | `D:\Games\Guitar Hero World Tour\DATA\PAK\qs.pak.xen` (UTF-16 `key "text"` table; the keys below were looked up there) |

Many names in the dumps are unresolved checksums (`[hex]` / bare hex). Resolved names below come from context
(`ghwt-extract/menu_0x5c2f930d.txt` option menu, `option_vars.json`, MODLOG), from the SDK's `QBKey.js`, or are marked "?".
Descs of the WT+ family were read from MOD (our `*_ghwor` copies) with `tools/desc_tree.py`; the VH theme's copies
(`ghwt-extract/hud_vh_qb/*.txt`, e.g. `0x6430019d` = `uidesc_HUD_band_battle_ghvh`) were used for the element trees of
descs the WT+ theme does not ship.

---------------------------------------------------------------------------------------------------------------------

## 0. Answer to "why is there 01234567 in the clip": the user's `HUDBossFOMeter=1`

INI:94 `HUDBossFOMeter=1` (and INI:71 `HUDBandMeterBVB=1`, INI:90 `ShowAllSPBulbs=0`, INI:38 `HUDTheme=ghwor`).
`HUDBossFOMeter` is the global `[b593308e]` ("HUD: Boss Battle Entire Face Off Meter", `menu_0x5c2f930d.txt:688`;
declared `SectionInteger b593308e 0`, GH:8). `setup_band_hud` (GH:453-793) creates the layout's `hud_root` and then kills
or attaches the versus meter by game type (`gamemode_gettype` -> faceoff / pro_faceoff / coop / quickplay / career /
battle / boss ..., see `guitar_gamemode` *orig*:1-200):

- GH:499-507: `if NOT (type = faceoff OR pro_faceoff)  if (b593308e = 0)  alias_faceoff_meter.Die` -> **the versus meter is
  only removed in non-versus modes when the option is 0.**
- GH:692-698: `HUD_attach_widget_band_faceoff_meter` (the widgets that fill it) is called only for faceoff / pro_faceoff
  (or boss battle with the option 1).

So with the option on, in Co-op / Band the versus meter (child `HUD_band_battle`, alias `alias_faceoff_meter`, present in
every `hud_2g`, `hud_1g1v`, `hud_2g1v`, `hud_3g1v` desc) stays alive with NO widget attached and shows its design-time
props: `score_1_text`/`score_2_text` = QS `bf2409fb` = **"01234567"**, `p1/p2_streak_number_text` = QS `c6081e83` =
**"50"**, `HUD_score_nixie_1a` multipliers, full star power bulbs, dial needle at 15 deg, `hud_band_battle_meter_amber_on_alpha 0 /
violet 1` (MOD:1211-1232, same in the other descs). That is exactly the clip from 1:46 (3 players: drum + guitar + vocals =
`hud_2g1v`; the top-left World Tour band meter next to it is the normal `band_meter` desc and is correct). A default
install (option 0) does not show it, but nothing guarantees the user's saved option.
Two ways to be immune: (a) our own band-mode descs carry no versus meter child (then the alias just fails to resolve);
(b) our own versus meter desc has empty default texts / invisible defaults so that "alive but unattached" is blank.
For `hud_2g` (shared by Co-op and Face-Off, see 1) only (b) works.

In the face-off part of the clip (0:00-0:53) the versus meter is attached normally ("1255", "0", x2 badge): that is the
DE's `HUD_band_battle` desc (GH3-style: top score bar, dial, 6 bulbs per side).

---------------------------------------------------------------------------------------------------------------------

## 1. How the DE picks the layout (`update_hud_layout`, GH:884-1007)

- `p2_battle` (GH:894-900): theme key `0x6bd128d8` (= a `hud_2d` struct with `elements`/`Scale`, default global
  `battle_hud_2d_elements` = `guitar_hud_2d_battle` *orig*:2-341). Created by `create_2d_hud_elements` (G2D:9-362), not a
  descinterface. Ours: `WoR_HUD_battle` (MOD:48995-49588, tools/wor_battle.py).
- **Every other mode ignores the game mode.** Only "players shown" and the parts count (guitar+bass+rhythm are one "guitar"
  group; drum; vocals), GH:905-981:

  | players | parts | `desired_layout` | modes that land here |
  |---|---|---|---|
  | 1 | guitar/bass or drum | `hud_1g` | p1 career/quickplay, improv/boss |
  | 1 | vocals | `hud_1v` | p1 vocals |
  | 2 | guitar+guitar / drum+drum / guitar+drum | `hud_2g` | **p2_faceoff, p2_pro_faceoff, p2_coop, p2_quickplay/career** |
  | 2 | vocals + guitar or drum | `hud_1g1v` | p2 band |
  | 2 | 2 vocals | `hud_2v` | duet |
  | 3 | vocals + guitar + drum, or vocals + 2 guitar | `hud_2g1v` | p3 band |
  | 3 | 2 guitar + drum | `hud_3g1v` | p3 without vocals |
  | 4 | anything | `hud_3g1v` | p4 band, **p4_pro_faceoff** |
  | (8) | | ? (hud_3g1v by the same switch) | p8_pro_faceoff ("Band vs Band") |

  (A 3-player mix that matches nothing leaves `desired_layout = null` -> "Unknown HUD layout" softassert, GH:1002-1003.)
- GH:989-990: if the **theme row has a key with that name** its VALUE replaces it (`hud_2g = WoR_HUD_layout_2g`).
- GH:997-1003: `change g_hud_2d_struct_used = ~desired_layout` (global struct of the layout). `setup_band_hud` then builds
  `hud_root` from `desc_interface` (GH:458-470) and wires everything by alias. `setup_hud` (GH:361-451, per player) also
  calls `update_hud_layout` (GH:416/456) and builds the legacy `hud_screen_elements` text elements (GH:36-360 data);
  `create_2d_hud_elements` is a no-op for nxgui layouts (no `elements`).
- The DE lists `hud_1d`, `hud_1g1d`, `hud_1d1g1v`, `hud_2d`, ... (HL, `layout_pairs.txt`) but `update_hud_layout` never
  selects the drum variants. `debug_hud_layouts_list` (HL:1-170) is only the debug cycler (GH:795).
- `faceoff_hud_2d_elements`, `career_hud_2d_elements`, `coop_career_hud_2d_elements` (*orig* `guitar_hud_2d_faceoff` /
  `_career` / `_coop_career`) are the GH3 layouts, unused by the DE.

Modes and types (`guitar_gamemode` *orig*): `p1..p4_quickplay` (type quickplay, cooperative for >1), `p1..p4_career`,
`p1_improv`, `p1_boss`, `p2_faceoff` (type faceoff), `p2_pro_faceoff`, `p4_pro_faceoff`, `p8_pro_faceoff` (pro_faceoff),
`p2_coop` (type coop), `p2_battle` (battle), tutorial, training. Boss battle = `boss_battle` global.

## 2. Theme row fields (what the DE reads from the theme struct)

Theme table `0x8ef7f1be` (HT:53-). Our row `ghwor` = copy of WT+'s row `0x90737ab7` (HT:86-104) + `extra` of `build.py`
(rows: MOD:2080-2139; WoR_HUD_layout_*: MOD:2185-2238).

| field | read by / meaning | WT+ (base) | ours now | fallback (what the user sees) |
|---|---|---|---|---|
| `hud_1g` | layout, 1 guitar/drum/bass (GH:989) | `0x5e3d7df2` | `WoR_HUD_layout_1g` -> `hud_1g_ghwor` **own desc** (tools/wor_1g.py) | - |
| `hud_2g` | 2 guitar/drum players: **Face-Off, Pro Face-Off 2p, Co-op** | `0x4f40178b` | `WoR_HUD_layout_2g` -> `hud_2g_ghwor` = WT+ copy | - |
| `hud_1v` | 1 vocalist | `a580a0e8` | `WoR_HUD_layout_1v` -> `hud_1v_ghwor` = WT+ copy | - |
| `hud_2v` | 2 vocalists | absent | **absent** | DE global `hud_2v` (stock desc `hud_2v`, no WoR look) |
| `hud_1g1v` / `hud_2g1v` / `hud_3g1v` | 2p / 3p with vocals / 4p + 3p w/o vocals | WT+ ids | `WoR_HUD_layout_*` -> `*_ghwor` = WT+ copies | - |
| `0x6bd128d8` | battle `hud_2d` layout struct (GH:896) | absent | `WoR_HUD_battle` | `battle_hud_2d_elements` |
| `c2bf76cf` | gamertag desc name, battle only (GH:731-732) | absent | `"hud_gamertag_ghwor"` | `hud_gamertag` |
| `pak` | theme pak | `hud_ghwt_withtime` | `hud_ghwor` | - |
| `0x3fb45eb1` | vocal highway desc | `vocals_highway_wtde` | same | - |
| `bf72b22c` | vocal phrase-quality font (`vocals_highway` *orig*:1195-1236) | `fontgrid_text_a6` | `0x2e5a5f81` | `fontgrid_text_a6` |
| `d5927557` | in-play message font (HM/GSP:895/GE/G2D:1190/HW:520) | absent | `0x2e5a5f81` | `fontgrid_text_a6` |
| `0x642ef3a8` / `e145701d` | vocal phrase text scale / internal scale | 1.2 / - | 1.2 / - | 1.0 / 0.35 |
| `0x21a2c597` | band-streak message style script (HW:526) | absent | absent | `hud_message_band_streak_style` (HM:184) |
| `f8885a0f` / `d99b7552` | per-player multiplier textures normal / SP (HW:1010-1020) | absent | WoR_HUD_mult_* arrays | `band_hud_score_1a..4a` / `_2b..8b` |
| `112feba3` / `bc95780d` | same for vocalists (HW:1024-1032) | absent | **absent** | `band_hud_score_*` / `vocal_HUD_score_*` |
| `d38da2b2` | sliding side meter `BAND_side_meter` | absent | 1 | off |
| `d5045305` | star meter (star count, frame) | 0 | 1 | off |
| `0x882f22a1` | danger blink | absent | 1 | off |
| `sidebar_x_scale`, `0x3dacb46b`, `0x4dd26977`, `0x18f90ff6` | highway border | absent | 2.6, -+17.4, `WoR_HUD_border` | stock |
| `2a5a553e`, `e9243b3a` | streak-meter hide offset / vocalist streak position (HW:1244-1256) | absent | absent | (0,45) / (913,438) |
| `bda08791` | SP flame SFX (HW:1480) | absent | absent | none |
| `0x75e47d17`, `0x54d8f06c` | ? | 1, 1 | 1, 1 | |
| ours: `WoR_HUD_career_meter`, `_sp_highway`, `_battle_hud` | our wrappers' flags | - | 1 | - |

Global options in the INI that change the HUD: `HUDTheme` `[12ad2474]`, `ShowStreakAlways` `[0f27ad3e]` (HW:1222, if 1 the
streak meter animation is skipped = always shown), `ShowAllSPBulbs` `[c8690022]` (HW:1316), `HUDBossFOMeter` `[b593308e]`,
`HUDBandMeterBVB` `[49c92c0e]` (p8 only, GH:510-520), `HUDMultColorStyle` (ad3e958b), `HUDAlwaysVOF`.

## 3. The descs per layout (ours = WT+ copies except `hud_1g`)

Aliases (`g_hud_2d_struct_used.desc_interface` -> `hud_root`, `desc_resolvealias`): per-player container aliases
`alias_g1..g3`, `alias_v1` (the container `getplayerinfo N hud_parent`), plus `alias_band_meter`,
`alias_faceoff_meter`, `alias_boss_meter`, `alias_hud_message_fire_pN` (flame desc). Each player container holds:
`player_meter` (multiplier desc: `player_mult_1d/1g/3p`, vocals `Band_vocal_multiplier`), `message` (ContainerElement:
the message parent), `hud_message_fire` (flame message desc), `gamertag`, and in some descs `Star_Power`/`star_power_1g`.

| desc (ours, MOD line) | aliases | children |
|---|---|---|
| `hud_2g_ghwor` (MOD:2239) | band_meter, faceoff_meter (`HUD_band_battle`), boss_meter (`HUD_boss_battle`), g1, g2, hud_message_fire_p1/p2 | g1 (365,372), g2 (816,371): `hud_message_fire`, `player_meter`=`player_mult_1d`, `message` (430x50), `gamertag`; `band_meter` (23,23); `HUD_band_battle` (0,-22 1280x761); `boss_battle` |
| `hud_1v_ghwor` (MOD:3625) | band_meter, v1 | `band_meter` = `solo_play_rock_meter_ghwor` (our restyled WoR bar+rock tube, MOD:14737); v1: `player_meter`=`Band_vocal_multiplier`, `fire_message_mask`+`hud_message_fire`. No `message`. |
| `hud_1g1v_ghwor` (MOD:4110) | g1, band_meter, v1, faceoff_meter, hud_message_fire_p1 | g1: `player_meter`=`player_mult_1g`, `message`, **`Star_Power`** (`star_power_1g`), `hud_message_fire`, `gamertag`; v1: `Band_vocal_multiplier`, `gamertag`; `band_meter_ghwor`; `HUD_band_battle` |
| `hud_2g1v_ghwor` (MOD:5353) | g1, g2, v1, band_meter, faceoff_meter, hud_message_fire_p1/p2 | g1/g2 (366/824, 416): `player_meter`=`player_mult_1d`, `message`, `star_power_1g` (local id is NOT `Star_Power`, see 8), `hud_message_fire`, `gamertag`; v1; `band_meter` (-76,10); `HUD_band_battle` |
| `hud_3g1v_ghwor` (MOD:7067) | v1, g1..g3, band_meter, faceoff_meter, hud_message_fire_p1..3 | g1..g3 at x 200/610/1009: `player_mult_3p`, `message`, `hud_message_fire`, `gamertag`; v1; `band_meter`; `HUD_band_battle` |
| `band_meter_ghwor` (MOD:9041) | alias_streak, alias_HUD_meter_red_bg, alias_glow, alias_pulse_container, alias_secondary_bulbs, alias_star_flame ... | the top-left WT band meter (dial, band score, band multiplier, 6 SP bulbs, per-player health lane masks, instrument icons, streak banner) |

Shared sub-descs (`HUD_band_battle`, `HUD_boss_battle`, `hud_message_fire`, `player_mult_*`, `star_power_1g`,
`Band_vocal_multiplier`, `hud_gamertag`) are DE globals shipped outside the theme paks (their text is not in ghwt-extract;
hashes `uidesc_HUD_band_battle = bd30fc97` ... not found in any extracted qb). The VH theme ships its own copies
(`*_ghvh`), a perfect structural template: see 5.

---------------------------------------------------------------------------------------------------------------------

## 4. Per mode: layout, creating script, position control

`T` = our theme. "DE default" = the DE's global desc is used (no WoR art).

| mode | `game_mode` / type | layout key -> desc | versus / band meter | per-player elements (script that creates/wires them) | position control | notes |
|---|---|---|---|---|---|---|
| Face-Off 2p | `p2_faceoff` / faceoff | `hud_2g` -> `hud_2g_ghwor` | band_meter + boss die (GH:499-560); `faceoff_meter` kept (`HUD_band_battle`, DE default) and filled by `HUD_attach_widget_band_faceoff_meter` (HW:546-948, GH:692-698) | per-player `player_meter` multiplier is **killed** (GH:588-594 `player_multiplier.Die` for faceoff/pro) -> multiplier only in the versus bar; `message` per player (Hot Start / SP ready / note streak, non-band path); no star power tube on highway (tubes live in the versus bar: `fill_1_1..6`, `fill_2_1..6`); `gamertag` destroyed unless online/`[e29369d4]` (GH:616-676) | desc child Pos (g1/g2 365/816); highway x from `get_highway_pos_and_scale` (plugin wrapper moves it by `x_offset_p2` for battle only); `p2_faceoff` morph-in uses extra `off_set_drop` (GH:1127-1235) | clip 0:00-0:53 |
| Pro Face-Off 2p | `p2_pro_faceoff` / pro_faceoff | same as above | same | same | same | identical HUD to Face-Off |
| Pro Face-Off 4p | `p4_pro_faceoff` / pro_faceoff | `hud_3g1v` -> `hud_3g1v_ghwor` | `faceoff_meter` with `current_num_players > 2` branch: team scores `band1_score`/`band2_score`, team multipliers `band1_multiplier`/`band2_multiplier`, team SP `band1_starpower`/`band2_starpower` (`setubes band=true`), `band1_streak`/`band2_streak`, `faceoff_ratio` (HW:596-760); band_meter dies | g1..g3 + v1 containers with `player_meter` (killed in faceoff), messages, gamertags | desc | 4 players are mapped to g1,g2,g3,v1 by the layout aliases |
| Co-op 2p | `p2_coop` / coop (`cooperative = true`) | `hud_2g` | `band_meter_ghwor` (shared score, band multiplier, band SP bulbs, rock needle, 4 lane masks); faceoff meter should die (option 0) | `player_meter` multiplier on each highway; in band scoring its x1 slot is replaced by the **instrument icon** (HW:1053-1068); streak lights; messages go to the shared `hud_band_messages` | desc | clip: placeholder meter visible with option 1 |
| Band 2p (1 guitar/drum + vocals) | `p2_career/quickplay` | `hud_1g1v` | band_meter + `Star_Power` per-player tube wired (GH:599-600, HW:1171-1190 `starpower_amount`) | g1: multiplier+tube+message+flame, v1: `Band_vocal_multiplier` | desc | the only band layout with a per-player SP tube out of the box |
| Band 3p with vocals | `p3_*` | `hud_2g1v` | band_meter, band SP bulbs only (per-player tubes not wired, see 8) | g1/g2 `player_mult_1d`, v1 | desc | clip 1:46-end |
| Band 3p no vocals / 4p | `p3_*` / `p4_*` | `hud_3g1v` | as above | g1..g3 `player_mult_3p`, v1 | desc | |
| Vocals only | `p1_*` vocals; duet = `hud_2v` | `hud_1v` -> `hud_1v_ghwor` / DE `hud_2v` | `band_meter` alias = our `solo_play_rock_meter_ghwor` (score bar + rock tube) | v1 `Band_vocal_multiplier` (props `nixie_texture`, `nixie_rgba`), vocal highway `vocals_highway_wtde`; phrase quality / SP ready as `vocals_message` text | desc + `vocals_highway_wtde` desc | no `message` container; messages only on the vocal highway |
| Battle | `p2_battle` / battle | theme key `0x6bd128d8` -> `WoR_HUD_battle` (hud_2d) | rock tube + attack slots per highway (our layout) | attack cards (`guitar_battle`), alerts (`create_battle_alert_frames`, GBI:24-433), gamertags only online (GH:716-775) | layout struct fields + plugin wrappers | see MODLOG 0.50 |
| 1 player (ref.) | `p1_*` | `hud_1g` -> own desc | `wor_band_meter_1g_ghwor`, `wor_side_meter_ghwor` | `wor_mult_1g_ghwor`, `Star_Power`, `message` alpha 0 | tools/wor_1g.py | done |

## 5. Element catalogue (what exists, names, who creates it, what positions it)

| element | names | creating / wiring script | position / look control |
|---|---|---|---|
| **score box(es)** per player in versus | `score_container_1/2` > `HUD_band_battle_score` sprite + text `score_1`/`score_2` (VH copy `HUD_band_battle_ghvh`, `hud_vh_qb/0x6430019d.txt`; props `score_1_text`, `score_2_text`) | text: `HUD_attach_widget_band_faceoff_meter` (HW:546): 2p `player1/2_status.Score` -> `seinttostring` -> `score_N_text`; >2 players `band1_score`/`band2_score` | desc layout; font `fontgrid_numeral_a9` set in the desc; placeholder "01234567" = QS `bf2409fb` (no comma formatting: native `seinttostring`) |
| **versus meter** (dial) | `HUD_meter_band_battle_master/meter_container`: `HUD_band_battle_meter_OFF` (dial), `..._needle` (props `hud_band_battle_meter_needle_rot_angle`), `..._amber_ON`, `..._violet_ON`, `..._shadow` | HW:546-575: `faceoff_ratio` (1..-1) -> needle -51.5..51.5 deg; amber alpha = clamp(ratio/0.1), violet alpha = clamp(-ratio/0.1) (value ranges 0..0.1 / -0.1..0) | desc; amber/violet = "who is winning" glows (usable for the 1st-place glow) |
| **band meter / rock meter** (shared) | `band_meter_ghwor`: Body, Needle, green/yellow/red lights, `lights_bg`, `HUD_meter_*_bg`, `multiplier` ring, `Score`, lanes `band_HUD_p1..p4_mask_dims/_fill_rgba`, `instrument_icons`, `streak`, `star_power_lights` | `HUD_attach_widget_band_meter` (HW:5-403): `band_health` -> needle (-66..66) + light alphas (0..0.667 red, 0.667..1.333 yellow, 1.333..2 green); 2+ players: `band1_score`, `band1_streak`, `band1_multiplier` (`sebandmultiplier` -> `band_mult_text`), per-player `health` masks (4 lanes), `band1_starpower` (`setubes band=true`, glow0..5), `HUD_set_band_meter_instrument_icons` (HW:404-465) | desc; killed in face-off types (GH:499-560) |
| **per-player rock meter** | `BAND_side_meter` (needle `side_meter_needle_pos`, `SIDE_meter_*_ON_alpha`) or vocals `BAND_top_meter` | `HUD_attach_widget_player_health` (HW:1089-1170) when `[1f19af1b]` (theme flag d38da2b2 + mode), GH:605-612; hidden in career/faceoff/battle (MODLOG) | desc children of g/v containers (only `hud_1g_ghwor` has it) |
| **star power tube** | solo/1g: `Star_Power` (`star_power_1g`) props `glow0..5_texture/scale`; band: band_meter `star_power_lights`; versus: `fill_1_1..6`, `fill_2_1..6` in `HUD_band_battle`; per player in multi: `glow0..2` | 1p: `setubes` on `starpower_amount` (HW:151-165); multi: `HUD_attach_widget_player_star_power` (HW:1171-1190) only for a child literally named `Star_Power` or `vocal_multiplier_star` (GH:599-603); versus: HW:596-760 | desc; the plugin owns the smooth fill / glow (PLUGIN_NOTES 1-2) |
| **multiplier** | `player_meter` (`player_mult_1d/1g/3p`): `nixie` (`nixie_texture`, `nixie_rgba`, `mult_bg_alpha`), streak lights `light0..4_texture`, `note_streak_text`; versus: `HUD_bb_multiplier_nixie_1/2` + `HUD_band_battle_mult_frame` + `band_HUD_X`; band meter: `multiplier_text` | `HUD_attach_widget_player_multiplier` (HW:950-1088): `senotestreaklights` (WoR colours by the plugin) + `semultipliernixie` with theme arrays `f8885a0f`/`d99b7552` (vocal: `112feba3`/`bc95780d`). Versus meter: textures fixed in the script (`HUD_score_nixie_1a..4a`, SP `_2b.._8b`, HW:596-948, in both the team and the 2-player branch) -- **not theme-configurable** | desc / theme arrays |
| **instrument icon on the highway** | `higway_icon_guitar/_bass/_drum/_mic` (sic) | HW:1053-1068: `if GameMode_IsBandScoring` the x1 entry (index 0) of the multiplier textures is overwritten with the instrument icon, so the badge shows the instrument at x1 and the number from x2. Wiped by `SetArrayElement` AFTER the theme arrays are read -> theme arrays cannot prevent it | script copy under a `WoR_HUD_` name + plugin symbol swap (MODLOG 1.22 pattern), or hide the nixie at x1 |
| **instrument icons in the band meter** | `band_HUD_guitar/_bass/_drums/_microphone` + `_glow`, props `band_HUD_instrument_pN_texture/_alpha/_rgba`, `..._glow_pN_*` | `HUD_set_band_meter_instrument_icons` (HW:404-465); streak colouring `hud_set_band_meter_instrument_streak_color` (HW:466-509: rgba 255,200,0 + glow) | desc |
| **failed instrument** | red sprite `band_hud_guitar2/_bass2/_drums2/_microphone2` (mic scale 1.75), z 400, child of the player's `hud_parent` alias, rgba (255,0,0) | `song_failed_highway_x` (GE:1531-1580) called by `song_failed_show_highways` (GE:1457-1530; skipped for 1p, p2 faceoff/pro) at fail | by alias (g1..) + Pos (80,40) scale 2; vocalist at (530,20) or (500,80) |
| **name plates** | `gamertag` desc (`hud_gamertag`, props `gamertag_name_text`, `gamertag_bg_rgba`, `headset_icon_alpha`) | band path GH:616-676: kept only if `is_network_game` or `[e29369d4]`, else `DestroyScreenElement`; faded out by `fadeout_local_gamertags` (GH:1201-1250). Battle: GH:716-775, online only, desc from theme `c2bf76cf` | desc child Pos; team colours `online_player_slot_bg_team1/2` |
| **band score** | `band_meter` `Score` (`score_text`) | HW:170-200 | desc |
| **streak** | band meter `streak` banner + `streak_number` (`streak_number_text`); versus: `streak_mask/streak/streak_number` (`p1/p2_streak_number_text`, aliases `alias_streak_p1/p2`) | `HUD_setup_streak_meter_animation` (HW:1220-1319): slides the banner in/out on `band1_streak_started/ended` / `playerN_streak_started/ended` events; text widgets `band1_streak` / `note_streak`. `ShowStreakAlways` skips it | desc + theme `2a5a553e`/`e9243b3a` |
| **placing text (1st/2nd)** | **none** in the DE HUD (grep for placing/rank in GH, HW, G2D, HM: nothing) | - | needs our own elements; `amber_on_alpha`/`violet_on_alpha` give "who leads" as an alpha for free (see 9) |
| **band multiplier** | band meter `multiplier_text` / ring | `sebandmultiplier` on `band1_multiplier` (HW:194-200) | desc |

Versus meter element tree (VH copy `HUD_band_battle_ghvh`, the shape our own desc would copy): `HUD_meter_band_battle_master >
meter_container > {HUD_band_battle_meter_shadow, _OFF > _needle, _amber_ON, _violet_ON, tubes_left_1/2 (tube_1_N + fill_1_N),
tubes_right_1/2 (tube_2_N + fill_2_N)}`, `score_container_1/2 > {multiplier_container_N > {HUD_bb_multiplier_nixie_N,
HUD_band_battle_mult_frame, band_HUD_X}, HUD_band_battle_score > score_N, streak_mask > streak > streak_number}`,
`player1/2_message_fire`. Props the DE writes (the only ones attached): `hud_band_battle_meter_needle_rot_angle`,
`..._amber_on_alpha`, `..._violet_on_alpha`, `score_1_text`, `score_2_text`, `hud_bb_multiplier_nixie_1/2_texture`,
`fill_1_1..6_texture/scale`, `fill_2_1..6_texture/scale`, `p1_streak_number_text`, `p2_streak_number_text`, aliases
`alias_streak_p1/p2`. Anything else a custom desc needs must be driven some other way.

## 6. Placeholder text: which and why

| text | key | where | why |
|---|---|---|---|
| `01234567` | QS `bf2409fb` | `score_1_text`/`score_2_text` in every `HUD_band_battle` / `HUD_boss_battle` instance (MOD:1218, 1347 ...) and in the desc itself | design-time default; replaced by `seinttostring` only when `HUD_attach_widget_band_faceoff_meter` runs (face-off / pro face-off / boss with option); in band modes the meter survives because of `HUDBossFOMeter=1` (section 0) |
| `50` | QS `c6081e83` | `p1/p2_streak_number_text`, `streak_number_text` (band meter, solo meter) | same; the band meter's own streak text is set by HW:200 when the widget attaches |
| full SP bulbs / amber-violet dial | `hud_rock_tube_glow_full` | `fill_*_texture`, needle 15 deg | defaults of the same desc |
| `?` / `\L` | QS `e6f8c73c` / `03ac90f0` | `special_event_*` legacy texts, battle alert default text | alpha 0, never shown unless a special event runs |

## 7. Everything that can put text above the highway

All nxgui messages funnel through **`hud_create_message`** (HM:3-52). It returns at once when `hud_root` is missing; for a
per-player message it needs the player's `message` container (`GetHUDMessageParent player=N`, native; no container ->
`return`); for `band` messages it creates `hud_band_messages` under `hud_root` at (640,280) 640x100 (HM:20-40) at runtime
(not part of any desc). Then `hud_wait_and_create_message` (HM:54-123) makes a `TextBlockElement` (font theme
`d5927557`, z 50) and runs the style script (`hud_message_wait_and_die` HM:165, `hud_message_band_streak_style` HM:184,
`hud_message_flame_style*` HM:447-711 -> `HUD_move_flame_container` G2D:1564 moves the `hud_message_fire` desc found by
`alias_hud_message_fire_pN`).

| creator | script (file:line) | text (QS key) | when / modes | parent | in our 1p layout |
|---|---|---|---|---|---|
| note streak | `hud_show_note_streak_combo` G2D:943 (returns for band scoring, G2D:954) | "%d Note Streak!" (`fb053f5e`) | 1p, face-off (non-band); flame style in 1p (G2D:1185) | player `message` | hidden (alpha 0) |
| Hot Start | `hot_start_achieved` (vanilla `guitar_events` *orig*:3087-3153; the DE's copy GE:4321 is undecodable hex but is the same entry) | "Hot Start!" (`09a07a71`) | non-band: `hud_create_message player=P`; band: `band` + band streak style | `message` / `hud_band_messages` | hidden |
| Star Power Ready | `show_star_power_ready` GSP:893-1015 | "Star Power Ready" (`8ba36464`) | band: `hud_create_message band` GSP:909; solo/face-off: flame style GSP:932; vocals: `vocals_message` GSP:917; legacy path (no `hud_root`, i.e. battle) `star_power_ready_text` + `hud_lightning_alert` G2D:1307 | see left | hidden (flame desc alpha 0) |
| band streak | `HUD_band_streak_notify` HW:510 (called from native on band streak events) | "%d Note Band Streak!" (`66bd2b10`), "Streak" (`83b2be80`, a new player joins the streak) | band (+ icons row of `band_HUD_*` 64x64 per streaking player) | `hud_band_messages` | n/a (1p) |
| band fail hint | `song_failed_show_highways` GE:1457-1520 (msg at GE:1512) | "Next time, try using Star Power to save the band." priority 100 | band fail | `hud_band_messages` | n/a |
| drum fill / solo | `hud_show_drumfill_score` G2D:1515 (1p only), `hud_show_drumsolo_score` G2D:1533, `hud_show_drumfill_challenge` G2D:1549 | "%d" (`9b704576`), (`8e2da9b3`), (`200e0af0`) | drums | player `message` | hidden |
| vocal messages | `vocals_message` (`vocals_highway` *orig*:1195-1236; callers `vocals_freeform_*`, `vocals_ingame_change_mic_volume`, `show_star_power_ready`, the phrase quality in `vocals` *orig*) | phrase quality "Weak" `989466aa`, "OK" `0e41fe46`, "Good" `22f31f1b`, "EXCELLENT!" `82bb7a47` (+ a bottom tier `ad88e646`), freeform points, mic volume, SP ready | vocals | `vocalist_phrase_status` TextBlock on the **vocal** highway at (343,31) | n/a; this is the precision text (`vocal_phrase_qualities` *orig vocals*:402-500, levels 0 / .2 / .4 / .6 / .8) |
| battle attack text | `attack_ready_text` GB:1157-1310 (guard `show_battle_text`, global default 1, `guitar` *orig*:134, GB:1148) | attack names (`battlemode_powerups.name_text`) | battle; draws only in the ghm/ghsh/ghvh branches and a default branch using the **global** `battle_hud_2d_elements.attack_ready_text_pos_pN` (GB:1286-1310), not our `WoR_HUD_battle` | `battlemode_container` | n/a |
| battle alerts | `create_battle_alert_frames` GBI:24-433 + `update_battle_alert_icon` GBI:472-692 ("Lefty Flip" etc, keys `99ed6c3c/71fd8268/b49b509a/41f71875/...`), `alpha_in_or_out_battle_hud` GBI:752 | the attack icon + name above each highway (clip 1:22) | battle | `battle_alert_container_pN` at highway top | n/a; **we already wrap `create_battle_alert_frames`** (MOD:1753) |
| battle misc | broken-string arrows/text GB:3400-3440; legacy `hud_screen_elements` texts (GH:36-360: `double_notes_text`, `mine_attack_text`, `difficulty_up_text`, `lefty_notes_text`, `broken_string_text`, `whammy_attack_text`, `lightning_text`, `steal*_text`, `special_event_*`; all alpha 0 until a script morphs them; positions (640,230-300), x*0.4 + 640*(p-1) for >1 player) | | battle / special events | `hud_destroygroup_windowpN` | n/a |
| failed icon | `song_failed_highway_x` (red instrument icon) | - | fail | player alias | n/a |

## 8. Star power: per player or shared in band?

Evidence (all in the decompiled scripts):

1. Every player has his own `player_status.star_power_amount` and activates it himself: `GuitarEvent_StarPowerOn/Off`
   take `player` (GE:1225-1283), `star_power_activate_and_drain player_status player player_text` is per player
   (`training_band_tutorial` 785-800 sets each of the 4 `player_status.star_power_amount = 100` and activates each),
   4p achievement `all_players_using_starpower` (GE:1235). The per-player HUD input `starpower_amount` exists for every
   player (HW:1171-1190 `HUD_attach_widget_player_star_power`, `current_num_players > 1`, `glow0..2`).
2. Separately a **band** aggregate exists: `band1_status.star_power_amount/_display_amount` (tutorial 773-800 writes it next
   to the players'), shown by the band meter bulbs (`band1_starpower`, HW:335-349) and the "Star Power Ready" band
   message (GSP:902-912). In versus teams `band1_starpower` / `band2_starpower` (HW:640-700).
3. So the DE does NOT lack a per-player value; it only **wires** it where the container child is literally named
   `Star_Power` / `vocal_multiplier_star` (GH:599-603). Our WT+-copied `hud_2g`, `hud_2g1v`, `hud_3g1v` name it
   `star_power_1g` (or have none), so nothing drives their tubes; `hud_1g1v` has `Star_Power` and works. A layout of ours
   that names the SP tube child `Star_Power` gets a per-player tube in band mode "for free" (glow0..2 props = 3 segments
   0-100; the 1p tube uses glow0..5). Unverified in game: what the native fills `player_status.star_power_amount` with
   in band (own phrases vs average); the tutorial writes 100 to both.

## 9. Hooks (what looks promising)

**(a) hide messages everywhere**
1. `message` containers: set alpha 0 on `message` and `hud_message_fire` in `hud_2g/1g1v/2g1v/3g1v_ghwor` (what
   `wor_1g.layout(no_messages=True)` does, `desc_edit.set_elem(d, 'message', alpha=0)` for the copies). Per-player messages
   are then invisible. Option: delete the `message` container: `GetHUDMessageParent` fails and `hud_create_message`
   returns before creating anything (cheaper; untested in game).
2. Band messages (`hud_band_messages`, band streak, SP ready in band, fail hint) are created at runtime under `hud_root`,
   so no desc edit reaches them. Cleanest single hook: **wrap `hud_create_message`** with the existing wrapper pattern
   (ship `WoR_HUD_hud_create_message`, plugin copies its symbol entry over the DE's and saves the original, as for
   `get_highway_pos_and_scale`): `if theme has WoR_HUD_no_messages -> return` (optionally keep `priority >= 100`, the fail
   hint). This covers all 11 call sites in all modes at once (table 7), flame styles included.
3. Not covered by 2: `vocals_message` (vocal highway; this is the precision text, restyle rather than hide), battle
   (`attack_ready_text`: `change show_battle_text = 0`; alerts: our wrapper of `create_battle_alert_frames`), legacy battle
   texts.

**(b) per-mode score/meter designs**
1. Own versus meter desc (`HUD_band_battle_ghwor`, copy of the VH tree in 5) referenced from our `hud_2g/hud_3g1v` copies:
   the DE only needs the prop names listed in 5. WoR look: swap sprites/fonts; **1st-place glow for free**: the amber / violet
   alpha props are 1 when P1 / P2 leads and 0 at a tie, so a "1st" badge bound to them (and a static "2nd" badge below)
   gives placing without script. Textures of the nixie multipliers are hard-coded names in `HUD_attach_widget_band_faceoff_meter`
   -> either keep `HUD_score_nixie_*` sprites that we re-skin via a unique-name texture swap in the plugin (as for the streak
   lights) or ship a script copy (symbol swap).
2. The versus meter must be blank when unattached (section 0) -> empty default texts, `p1/p2_streak_number_text`, hidden needle.
3. Rock meter: band modes keep `band_meter_ghwor` (WoR-restyle it like `solo_play_rock_meter_ghwor`, ROCK_METER_EDITS in
   build.py); the face-off removes it by script (`alias_band_meter.Die`), so the "no rock meter in face-off" rule is already
   the DE behaviour.
4. Per-player SP tube: name the child `Star_Power` (section 8). Multiplier / instrument icon: script copy of
   `HUD_attach_widget_player_multiplier` without the `IsBandScoring` block (HW:1053-1068) via the same symbol-swap pattern.
5. `hud_2v` is missing from our theme row: add `hud_2v` (our own desc or `WoR_HUD_layout_1v`) so duets don't fall back
   to the stock desc.
6. Same desc serves Co-op and Face-Off in `hud_2g`: elements that must differ by mode have to be hidden by the DE's own
   kills (`alias_faceoff_meter`, `alias_band_meter`, `player_multiplier` are killed by type) or by script wrappers on
   `setup_band_hud`'s attach calls.

## 10. Not verified / open

- Whether `GameMode_IsBandScoring` is true for 2p Co-op and quickplay 2p (native). Evidence: the scripts take the band branch
  for p2+ cooperative modes and the note-streak / Hot Start paths differ; the clip's face-off shows per-player "Hot Start!"
  (non-band) and the band part shows instrument icons (band).
- The text of the shared descs `HUD_band_battle`, `player_mult_*`, `hud_message_fire` (only the VH copies and our instance
  overrides were read).
- Native-side fill of `player_status.star_power_amount` in band mode.
- `hot_start_achieved`'s exact DE body (decompiler left hex), message removal by deleting `message`.
- `p8_pro_faceoff` layout (not reachable in a normal DE menu).
