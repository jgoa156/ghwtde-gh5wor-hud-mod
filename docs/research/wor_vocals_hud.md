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

## Mock

- `docs/mocks/mock_vocals_v1.jpg`: our 1v bot frame (t165). Our left cluster is blacked out, and the WoR panel is
  built from the real WoR textures at the measured geometry, shifted with our highway (dy -33). Our WoR score box is
  copied from the guitar + vocals frame. The badge is a crop from the WoR frame (asset not identified). The highway
  itself is still the DE's (step 4 is not mocked).
- `docs/mocks/ref_vocals_wor.jpg`: a WoR frame (170 s) above the mock, both at 1280 wide.
- Generator: a scratch script (`mock_vocals.py` in the session scratchpad), not in the repo.
