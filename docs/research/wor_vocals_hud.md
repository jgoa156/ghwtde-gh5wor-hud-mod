# WoR singleplayer vocals HUD vs ours (research, 2026-10-25)

Sources:
- `C:\Users\rockb\OneDrive\Videos\GH\WOR_microphone_gameplay.mp4`: Warriors of Rock, original, 1 vocalist, 1280x720, 272 s.
- `C:\Users\rockb\Downloads\Vocals.mp4`: **ours** (the DE with this mod), 1920x1080, 116 s. Guitar + vocals first, then
  vocals only. It is not WoR.
- Our bot frames: `tests/results/band-20261025-213315/1v_t*.png` (vocals only) and `band-20261025-212839` (guitar + vocals).
- WoR descs, decompiled from `ghwor-extract/ui_shared/ui/uidesc_vocals_*.qb.xen` with `sdk.js decompile` (a scratch
  copy, not in the repo): `vocals_all_meters`, `vocals_health_meter`, `vocals_multiplier`,
  `vocals_star_power_meter`, `vocals_phrase_progress_meter`, `vocals_word_compliment`, `vocals_strikes_meter`, and
  `vocals_competitive_*`. Also already decompiled: `ghwor-extract/uidesc/uidesc_vocals_highway.txt` and
  `uidesc_hud_standard_1v.txt`.
- WoR scripts: `ghwor-extract/hudqb/scripts__guitar__hud__hud_widgets.txt`
  (`HUD_attach_widget_vocal_sp_combo_meter`, about lines 640-830), `scripts__guitar__vocals_highway.txt`, `guitar_hud.txt`
  (2099-2190), `guitar_starpower.txt:1461`.
- Textures: `ghwor-extract/ui_shared_png2/` (meters) and `ghwor-extract/z_in_game_png2/` (highway and lyrics). **Every
  texture below exists**; none are missing.

## Layout (1280x720 canvas = the WoR video, measured from the frames at 10 s steps; about ±3 units)

WoR draws a full-width horizontal vocal highway near the BOTTOM of the screen. Every other piece of the vocalist's HUD
sits on its top edge:

| Piece | Canvas box (x0, y0 - x1, y1) |
|---|---|
| Highway top line / bottom line | y 497 / y 597, x 0-1280 (full width) |
| Lyrics band (dark, translucent) | y 600-632, under the highway |
| Now line (green, vertical) | x ≈ 406 |
| **Meter panel** (`Vocal_meters`) | 146,461 - 383,488 |
| └ health meter (3 lamps + needle) | 148,462 - 238,487 |
| └ multiplier ("x4" text on `HUD_meter_combovocal`) | 240,462 - 282,487 |
| └ star power tube | 286,463 - 381,486 |
| └ phrase progress strip (cyan) | 146,492 - 383,499, divider at x ≈ 265 |
| Round badge on the now line | centre (409, 468), d ≈ 43 |
| Score box + star (the same art as the instrument one) | 890,410 - 1120,465 |
| Phrase streak box (orange digits) | 940,467 - 1060,490 |

Our current 1v highway (bot frame t165) spans the same width, but its top / bottom lines sit at canvas y 464 / 567,
33 units higher than WoR's. Our now line is at x ≈ 270 (WoR: about 406).

## Elements

| WoR element | Asset(s) (`ui_shared_png2` unless noted) | WoR desc / script | DE counterpart (what we retarget) | Ours today (1v) | Notes |
|---|---|---|---|---|---|
| Meter panel backing | `vocal_meter_backing` 256x64, `vocal_meter_backing_div` 16x32, `vocal_health_meter_sheen` 128x32 (three sheens) | `vocals_all_meters` (`Vocal_meters` root 256x32; `meters_menu` lays out health_meter, flip_piece = multiplier + compliment, Phrase_Progress_Meter, Star_Power_Meter) | v1 in `hud_1v_ghwor` (our WT+ copy, docs/research/de_layouts.md:147) | none; scattered WT pieces | New desc `wor_vocal_meters_ghwor` put in v1 |
| Rock (health) meter: 3 lamps + needle | `vocal_health_meter` 128x32 (unlit), `_red` / `_amber` / `_green` 32x32, `_needle` 32x32 | `vocals_health_meter`; `HUD_attach_widget_vocal_sp_combo_meter`: needle pos x -55..28 for health 0..2; red / amber / green alpha on health 0-.667 / .667-1.333 / 1.333-2 | DE `HUD_attach_widget_player_health` with the vocal `BAND_top_meter` (de_layouts.md:184) | WoR vertical rock tube stub (top left), wrong for vocals | Same value ranges as the WT widget, so map the DE's props onto our element ids (as `SIDE_meter_*_ON_alpha` / `side_meter_needle_pos`) |
| Multiplier | `HUD_meter_combovocal` 128x128 (backing); text `fontgrid_text_a1` "x" + number, overlay `fontgrid_numeral_A1_b` | `vocals_multiplier`; `secombolights` (no bulbs): text rgba per level (x1 255,180,180; x2 243,169,64; x3 128,236,68; x4 175,101,238; SP 190,10,10) and bg rgba | DE `Band_vocal_multiplier` (v1 `player_meter`; props nixie_texture...) | WT nixie bulbs + green text (handoff 5b: it reads our instrument multiplier art) | Needs our own desc on the v1 `player_meter` alias. The DE drives nixie textures, not text, so the plugin must read the multiplier (g_streak / multiplier hook) or the DE may set a number text. **Uncertain: check what the DE's widget writes to Band_vocal_multiplier.** |
| Star power tube (horizontal) | `vocal_starpower_tube` 128x32 (glass), `vocal_starpower_fill` 128x32, `vocal_starpower_bg`, `vocal_starpower_border`, `vocal_starpower_tube_cap`, `vocals_meter_cap` 128x16 | `vocals_star_power_meter` (fill in a 115x29 window; fill pos x -114..0 for SP 0..100; needle -59..58; `Fill_Post_SPFX` and Tesla FX at 50 %+) | DE vocal star power: the band SP bulbs / the per-player `Star_Power` (`starpower_amount`) | WT-style dark bar with a white dot | The plugin's smooth fill engine could drive it, but it is a horizontal clip: a separate simple version |
| Phrase progress strip | `vocal_starpower_fill` (tinted cyan), `vocal_starpower_tube` | `vocals_phrase_progress_meter` (fill pos x -104..0) | DE vocal phrase meter (WT's "phrase" bar, if present: **uncertain**) | none | The cyan strip under the panel in every WoR frame. It is the phrase or SP-phrase progress |
| Phrase compliment ("EXCELLENT!" etc.) | font only | `vocals_word_compliment` replaces the multiplier + SP area at each phrase end (flip_piece) | DE phrase-quality text (`vocals_highway` font bf72b22c, de_layouts.md:117) | green text on the highway at the comet | WoR shows it IN the panel (frame w_024). Our DE draws it at the comet |
| Badge on the now line | ring + icon (ribbon / target / mic) | probably the RP (power) / character widget (`rp_casey_widget_vocals`, `rp_johnny_timer_vocals` in all_meters) | none | none | **Uncertain**: the icon changes between frames. Skip for singleplayer v1 |
| Vocal highway (band, notes, now bar, lyrics) | `z_in_game_png2`: `lyric_bg_middle`, `lyric_bg_side`, `lyric_stripe_mid` / `_end`, `vocal_fireball_bg` (pitch comet), `vocal_anchor_dot`, `vocal_highway_note_space`; outline / Rush containers | `uidesc_vocals_highway` (root 930x220 at (288,32); now_bar at x 121; pitch_area; lyrics 890x32 at (303,153)); `vocals_highway.txt` | DE vocal highway desc `vocals_highway_wtde` (theme field 0x3fb45eb1, de_layouts.md:116) | WT look: teal note tubes, purple comet | WoR: yellow-outlined note bars (filled solid yellow when hit), green now line, silver top / bottom lines, a dark lyric band. The geometry is in the desc; note colours may be script-driven. **Biggest piece; separate step** |
| Score box + star meter | our 1-player WoR score box (already built) | `HUD_scores_stack` / `star_meter` | `band_meter` in `hud_1v_ghwor` = our `solo_play_rock_meter_ghwor` | a "47000" WT-style text; no WoR score box in the 1v bot frame | Reuse ours, placed at 890,410 above the highway's right half |
| Phrase streak counter | streak box art (ours) | in the score stack | DE vocalist streak position `e9243b3a` (913,438) (de_layouts.md:127) | streak box "25" at the left, over the highway | Move it under the score box like WoR (940,467) |
| Vocal multiplier art in the score box when SP is on | `z_in_game_png2/vocal_HUD_score_2a/3a/4a/6a/8b` | `hud_widgets.txt` 1265: the sp_textures for part Vocals | DE `bc95780d` (vocalist score textures, absent in our theme, de_layouts.md:122) | n/a | Ship them for the theme field |

## Plan (singleplayer vocals, in order)

1. **Meter panel desc** `wor_vocal_meters_ghwor`: backing, health lamps + needle, multiplier text, SP tube, phrase strip,
   with WoR's element ids where the DE's widgets can drive them. Mount it in `hud_1v_ghwor`'s v1 (replacing
   `Band_vocal_multiplier`'s look). Hide our rock tube stub and the nixie bulbs in 1v. **First, read what the DE's
   vocal widgets write** (health, multiplier, starpower_amount props on v1 / band_meter), so we keep the DE's own
   wiring.
2. **Plugin hooks** for whatever the DE does not drive: needle position from health, the multiplier number and colour
   (from the streak-lights hook's multiplier), the SP fill (clip window, horizontal), and the phrase strip.
3. **Score box + streak** in 1v: our WoR score box at (890,410) and the streak box under it.
4. **Vocal highway restyle** (separate approval): lines, lyric band, note bar colours, now-line position (x 406),
   highway moved 33 units down to WoR's y 497-597. Through `vocals_highway_wtde` / the theme's highway desc field.
5. Then guitar + vocals (1g1v) reuses the panel at the same spot.

Risks: the theme may not be able to restyle the DE's vocal highway notes (script-drawn: colours may be hard-coded);
the multiplier text needs the plugin if the DE only swaps nixie textures; 1v has no bot run with SP activation, so
the SP-active look (Tesla FX, red multiplier) isn't verified from our side; the theme pak budget (4 MiB) grows by
about 60 KB for these textures.

## v2 findings (2026-10-26, user review of mock v1: 8 points)

Corrections to the v1 table above:
- **Star power vs phrase progress were swapped.** `vocals_all_meters`: `Star_Power_Meter` (desc
  `vocals_star_power_meter`, Star_Power scale (2.1, 0.35)) is the thin strip **on the highway's top line under the
  panel** (x 145-383, y ~492-499): `vocals_meter_cap` shell, fill `vocals_meter_cap` tinted (0,166,255) Add in a 115x29
  window, `MiddleMark` (2x30, Sub, a 0.5) at 50 %. The white box in the panel's right section is
  `Phrase_Progress_Meter` (`vocals_phrase_progress_meter`): `vocal_starpower_tube` glass + `vocal_starpower_fill`
  tinted (245,255,0) Add (reads white).
- **Panel frame**: `vocal_meter_backing` + `vocal_meter_backing_div` (x2) + `vocal_meter_color_stripe` tinted with
  `vocals_hud_rgba[band]` (band 1 = 77,95,153: the blue rim) + `vocal_meter_color_stripe_ON` (glow, alpha 0 normally,
  driven by `vocal_meter_color_stripe_ON_alpha` / `_rgba` in vocals_highway.txt). These are the "ready" panel textures
  (all in `ui_shared_png2`).
- **Score box (point 5)**: WoR's `uidesc_hud_standard_1v` uses the same `star_meter` desc as 1p
  (`band_HUD_star_score_meter` + `_front`): there is **no separate vocal score-box texture**. Vocal differences are in
  script only: `HUD_attach_star_meter` sets `divide_by_10` on the streak (phrase streak) and `always_show_ns_meter = 1`.
  The vocal-only art `z_in_game_png2/vocal_HUD_score_2a/4a/6a/8b` are the SP multiplier nixies
  (`semultipliernixie sp_textures` for part Vocals, hud_widgets.txt ~1265), not a score box. Uncertain whether the user
  meant the panel art above.
- **Badge (point 6)**: dropped (WT has no challenges/RP widgets; `rp_*` descs in all_meters).

Point by point:
1. **Tip balls**: WoR `uidesc_star_meter` star_tip_FX = 5 sprites: 2x `hud_progression_bar_lead` (Add, 32x20) +
   `star_ball_head` (Fire_UI/Fire_2D on `balloflame`) + 2x `star_ball_effecs` (Fire_UI on the lead, 32x32), all with
   `noise_32x32x32` (animated flicker). Measured on the video: core (lum > 200) **12 x 8** canvas, glow (> 140)
   **16 x 10**. Ours (`WoR_HUD_star_lead` 64x16 at STAR_LEAD_S 1.1): core 7.7 x 6.6, glow 9.9 x 8.8. Match: scale
   **(1.7, 1.3)** on our art, or WoR's own `hud_progression_bar_lead` (32x16, core 10x9 texels) at **(1.2, 0.9)**
   drawn twice (Add) + a 1.6x halo at 0.35 (what the mock does). The fire flicker needs a Fire_UI material (DE?) or a
   plugin alpha wobble.
1.1 **Star animation**: (a) `band_HUD_gold_star_glow` uses material `FC_GLOW` = Fire_UI/Fire_2D on
   `band_HUD_gold_star_glow` with noise (speed 0.01 / 0.2 / 0.1): a constantly flickering glow, alpha by
   `screenelementconditional` on `has_missed_note` (glow only while no note is missed); (b) on every star count change
   `star_meter_change_fx` -> `son_of_HUD_animate_star_meter_flames` (dec/guitar_events.txt:4015): wait 0.3 s, two
   additive `Mat_Meter_Wibble_Glow` sprites (tex `SB_Tubeglow02`, 228 and 128 px, rgba 255,200,64) fade in 0.1 s /
   out 0.3 s, plus three 2D particle bursts in `Star_Earn_FX`: `sys_Particle_lnzflare02` (255,255,128 -> 255,128,0,
   scale .25 -> 1, 0.1 s), `Spark01` gold -> white (scale .5 -> 1.5, 0.25 s), `Spark01` streaks white -> black
   (scale 1.5 -> 5.5 x 0.15); the number sits in a 38x38 `rotating_star_window`. Ours: static `star_shine` (Add) +
   the DE's `Star_Meter_Sparks01` in `star_flame` + the plugin's star fire loop; no wibble glow pair, no lens flare.
2. **Fonts**: lyrics `fontgrid_lyric_a1` (SectionQBKey `vocal_lyric_font`, scale 0.4 / karaoke 0.45 x 0.55, offset
   (0,-44)); multiplier `fontgrid_text_a1` "x" + number with an Add 0.3 overlay in `fontgrid_numeral_A1_b`; phrase
   compliment (`vocals_word_compliment`) `fontgrid_text_a1`; count-in / messages `fontgrid_title_a1`; score
   `fontgrid_numeral_a1` (ours already). All in `ghwor-extract/ui_shared/*.fnt.xen` (tools/wor_font.py converts them).
   Lyric colours: upcoming 210,210,210; sung 0,102,255; scrolling 255,242,213; highlight 254,233,53.
3. **Notes / now line**: notes are 3D-highway materials in `matqb/guitar_material.txt`: `vocal_note_sung` =
   passes `Vocal_Note_Glow` (tex `vocal_highway_note_Glow01`, colour 1.3,0.8,0.6,0.9) + `Vocal_Note_Line`
   (`vocal_highway_note01`, **colour 1,1,0**) + warble; `vocal_note_sung_sp` = `Vocal_Note_Glow_SP`
   (`vocal_highway_note_Glow02`, 0,0.75,0.75,0.9) + the line. Textures (Xbox basic_gems dict, extracted):
   note01 `basic_gems_png/18fc2c43.png`, note01_cap `660d0f87`, Glow01 `954fd9a7`, Glow01_cap `d0fe6a35`, Glow02
   `d2efa377`, Glow02_cap `e97356f0`, spoken01 `db6620de`, Vocal_BM_Gradient `524efa45` (name -> file:
   qbkey of `tex\models\highway\<name>.dds`). Sung paint = the `VocalEKG` shader material, colours set by
   `vocals_paint_star_power_off/on` (vocals_highway_fx.txt 860-893): normal m_psColors0 (0.99,0.99,0.26), SP
   (0.26,1,0.99). Measured: hollow tube 18 canvas tall, edge lines ~4 thick, yellow ~(255,246,38).
   **Now line**: green, ~2 px bright core with a wavy plasma look and a ~30 px soft green glow, silver arrowheads
   (`vocal_health_meter_needle` in uidesc_vocals_highway `visible_highway`) on both lines. **Uncertain**: its texture.
   `now_bar` in uidesc_vocals_highway is an empty hidden container; no `Mat_*` for it found in the vocal scripts. Best
   candidates in basic_gems: vertical lightning strips `ad13f425` / `ee2de665` (tinted green, Add) over a soft column
   (`d96d3be3` / `9ecd4133`); likely engine-drawn by the EKG shader.
4. **Highway position** (video, 9 frames): silver lines at canvas **y 494** (core, rows 493-498) and **596**
   (595-597); lyric band 600-632, lyric glyphs ~612-622; now line x **406** (394-407 across frames); phrase divider
   (grey) x ~642. Ours (1v bot frame): 464 / 567, now line ~270: move down 30, now line +136.
8. **Star power look** (6.webp): the top silver line becomes a cyan glow band (core ~122,251,255, glow 0,166,255,
   +-12 canvas), a cyan glow on the lyric band's bottom edge, the bottom silver line stays silver, SP notes cyan-green
   (yellow line over the cyan SP glow), sung paint cyan, multiplier x8 in pale yellow-green, SP strip draining with a
   white ball at its fill end. Script: `vocals_activate_star_power` -> `Create_Vocals_Star_Power_Effect`, particles
   with material `VH_SP_FX01`, `vocals_highway_border_flash_spawned` (rgba), `vocals_lightning_starpower_spawned*`.

Mock v2: `docs/mocks/mock_vocals_v2.jpg` (WoR frame above, mock below), `mock_vocals_v2_sp.jpg` (star power),
`ref_vocals_v2.jpg` (zoomed WoR vs mock: panel, score box, now line). Black background; panel/lamps/plate/tubes from
the WoR textures at measured geometry; notes and lines drawn at the measured sizes with the WoR note textures' glow;
lyrics in `fontgrid_lyric_a1`; score box = our in-game box with 1.53 digit proportions, commas and WoR-size balls.
Generator: scratch `mock_vocals_v2.py` + `wfont.py` (WoR font renderer), not in the repo.

Open questions: the now-line texture; whether the DE can draw the note line yellow (its vocal note materials /
colours live in the DE's own guitar_material); the Fire_UI flicker (does the DE ship that template?); what the user's
"ready texture for the vocals scoremeter" refers to (the panel art above is the best match).

## Mock

- `docs/mocks/mock_vocals_v1.jpg`: our 1v bot frame (t165). Our left cluster is blacked out, and the WoR panel is
  built from the real WoR textures at the measured geometry, shifted with our highway (dy -33). Our WoR score box is
  copied from the guitar + vocals frame. The badge is a crop from the WoR frame (asset not identified). The highway
  itself is still the DE's (step 4 is not mocked).
- `docs/mocks/ref_vocals_wor.jpg`: a WoR frame (170 s) above the mock, both at 1280 wide.
- Generator: a scratch script (`mock_vocals.py` in the session scratchpad), not in the repo.
