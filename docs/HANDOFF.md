# GH5 / WoR HUD mod: session handoff (2026-10-21, 0.49 released, 0.50 WIP)

Start here in a new session. History: `docs/MODLOG.md` (latest sections at the end). Plugin internals:
`docs/PLUGIN_NOTES.md`. Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (git author Guilherme Almeida
<jgoa156@gmail.com>, SSH push works). The mod is credited to **WitchDoctoR** (Mod.ini Author, READMEs).

## Start here (2026-10-21)

State: HUD **0.49** released (releases/, bundles Ultrawide Fix **1.0**). HEAD has battle mode rebuilt in the WoR style
(plugin 1.33, tools/wor_battle.py, mock docs/mocks/mock_battle_v8.jpg approved 10-20, build preview
docs/mocks/mock_battle_v9_build.jpg) and the bgfx add-on stepping aside on DXVK; HEAD + plugin 1.33 are installed,
battle is NOT tested in game. Sibling repos, both released and confirmed working by the
user on 2026-10-20: **Ultrawide Fix 1.1** (ASI plugin, Hor+ 3D FOV, no ReShade needed; only release on its repo) and
**All Main Menu Music 1.0** (10 games in one mod, GitHub Release, World Tour's six always play).

1. **Battle mode: test 2 fixes built (plugin 1.34, MODLOG "Battle test 2"), awaiting test 3.** (LEDs,
   needle direction, cards into the slots, tube glued.) Earlier: test 1 failed, fixed. Test 1: highways
   far too far apart, sets visible on the wrong side during the intro, every other mode hung at loading (MODLOG, end).
   Fixes installed; test quickplay FIRST (the hang), then battle. Calibrated on the user's footage
   (`OneDrive\Videos\2026-10-20 21-49-06.mp4`); v8 approved. Each highway carries the main theme's rock tube on its
   left rail (needle slid by plugin 1.33 from the DE-turned stand-in) and the three attack slots where the SP tube goes,
   highways 30 apart each (the wrapper moves the returned Pos; x_offset_p2 untouched), P2 = P1's set translated, empty slots dark, cards sized to the
   slots. **The attack alert / card above the highway is stock on purpose: its design is still to be discussed with
   the user** (WoR template idea: uidesc_quickplay_challenge_alert, `wor_card()` in tools/mock_battle.py). What to read
   in `wor_hud_fixes.log` after the test: "battle needle: ..." (stand-in found, rot range, swing 42 or 74), "battle
   card ..." (cards resized), "get_highway_pos_and_scale wrapped". Details: MODLOG "v0.50 WIP + plugin 1.33".
2. **Ask for one test run** (rule: ask before launching): the reworked battle mode, plus the still-unconfirmed 0.48/0.49 items: fail box calibration, YOU ROCK round 3 (letters,
   gravity 3500, glow, the WoR sound via SoundEvent), rock needle stand-in (plugin 1.31), popup message size.
3. **Release 0.50** with the above (`python build.py --package`, zip to releases/, push).
4. **Open decision:** popup up/down arrows (code ships, did not show in game; user: leave it for now).
5. **Backlog (user order):** face-off crash (enable WER LocalDumps first) + face-off layouts; multiplayer / vocals
   layouts (rules in docs/MODES_RULES.md, mocks in docs/mocks); song list side art (user remastering); drum
   animations (docs/DRUM_ANIMS_PLAN.md, not started); full code review of the HUD, ultrawide and menu music repos;
   WoR's Star03 sliver for the burst; the DE's SP highway glow leak; game-catalogue jump menu idea (SELECT key) and
   song list sorting that ignores a leading "The".

## 2026-10-22 late: plugin 1.40 + mod INSTALLED (not tested in game)
- Gluing: tube_maps keep the 1-player angle (uniform scale about the LED span's middle, no shear: the sheared tubes
  looked more tilted); wor_mp.MP_DX -24 corrects the offset into the centred g1/g2 containers (measured on the
  user's face-off shot); SP_NUDGE back to -15. The rail model (RAIL_L/R - SEP) matched the 2-player borders at SEP 22.
- Per-player SP tube = the 1-player tube itself: wor_mp.sp_desc copies every sp_* element of wor_band_meter_1g into
  a container (sp_transform: scale k, pos) -> same local coords, so the plugin's tube engine constants apply; plugin
  1.40 keeps one StarPower per tube (g_tubes[4], g_sp = *g_spp, tube_for(clip)). Our
  WoR_HUD_HUD_attach_widget_player_star_power REPLACES the DE script (swap, no orig): on our tube (child sp_mp exists)
  six segments, the band's band1_starpower in band / co-op, the player's own in face-off types / battle / boss;
  otherwise the DE's three segments. Old WoR_HUD_vs_sptube / vsseg no longer shipped.
- Band (items 9-11): tools/wor_band.py: the quickplay score group (no tubes) as desc wor_band_score_ghwor in every band
  layout (band_meter instance, OFFSET no vocals (-9,-394) / vocals (-37,-324)), every WT+ band prop on hidden sinks
  (instrument icons = the huge guitar, gone); WoR bulb (bulb + nixie digit + 'x') per value WoR_HUD_bandbulb_2/3/4/6/8,
  set by a semultipliernixie on band1_multiplier from our HUD_attach_widget_band_meter wrapper (blank at x1); plugin
  grows it in (0.3 s) when it leaves blank. desc_gen now records PROPS / ALIASES.
- Battle: x_offset_p2 itself = stock + SEP with our theme (saved stock on first call; the highway wrapper no longer
  moves Pos), so the DE's prompts / alerts (PUSH etc., placed at gem pos + x_offset_p2) follow the highways (item 5).
- Streak number: WoR's fit settings (fit_width scale each line if larger + fit_height scale down if larger),
  STREAK_K = SCORE_K (adaptive; if it fails again, STREAK_K_FIXED 0.155).
- SP tube look (item 12): SP_RIM 3 -> 1 (wider fill), SP_NEON_HALO (2.6, 2.6). Plasma 60 frames at 30 fps (pak budget,
  now 3.27 MB).
- Mocks: docs/mocks/mock_faceoff_v9.jpg, mock_band_v9.jpg, mock_battle_v14.jpg.
- STILL TODO: item 0 fade-in (battle pieces now appear in place, no fade), item 13 improvisation purple line (WoR
  av_presets og_highway_drum_freeform + guitar_highway_visualizer: research DE support), the 6th star (user wants
  it; WoR shows 6 on the star at 100%), crash repro (career -> pro face-off, keep debug.txt).

## 2026-10-22: user's test of 1.39 (OPEN, work these first; screenshots in the session)

0. Battle highway pieces must NOT drift into view at song start: fade in like every other mode.
1. CRASH: career face-off, then pro face-off (switching modes) crashes the game.
2. Career face-off: no rock tube glued to the highway, only the versus meter.
3. Versus streak number: size adapts to its digit count AND is centred in its slot (2 digits showed small, "28").
4. Score boxes a few px UP (dial stays): they cover a small part of the dial's bottom.
5. Battle effects sometimes uncalibrated with the highway: the "PUSH" (string cut) popup showed below the highway,
   probably not aligned with the green gem strike either.
6. Power-up icons still too big: the slot border must be visible like WT's default (round icons inside rings).
7. Battle rock tube poorly aligned (quickplay is perfect): angle with two highways? (3 highways later); or move it a few
   px left. Slots: arms still showing a lot: move closer; stack so only part of each circle is behind the one in
   front, crescent order.
8. Face-off / pro face-off / career face-off: pieces still not glued: move both left by some px.
9. Band: pieces poorly aligned; rock tube more tilted than it should be (keep ONE angle always); remove the huge
   guitar icon (the WT band meter's instrument icons); replace the band score meter with the quickplay one; ALL
   players' SP tubes show the band star power (same value on every tube).
10. WoR band score group: a light bulb for the band multiplier that expands out of the score group from x2 up
   (textures already extracted: band_HUD_multiplier_bulb, bulb_x, band_HUD_multiplier_one..eleven).
11. Band score group always top right; with vocals it gains top padding below the vocal highway (user's WoR frames).
12. SP tube (all modes, user's WoR crop): WoR's blue fill is wider (fills more of the tube sideways); the bottom neon
   blurrier with more glow.
13. Improvisation (freeform) sections: WoR shows a purple animated line on the highway; ours a white line. Lead: WoR
   av_presets og_highway_drum_freeform(_rb/_ps3) + scripts/guitar/guitar_highway_visualizer (hudqb decompiled).
DONE + INSTALLED 2026-10-22 ~04:30 (plugin 1.39 names regen, mod): 0 battle containers start in place (OFFSCREEN =
rock_pos: no slide; a fade is not done yet), 2 career face-off (boss_battle) gets no rock tube (CAREER_METER_SCRIPT),
3 streak centred (internal_just 0.5; adaptive size still TODO), 4 BOX_UP 6, 6 CARD_FILL 0.5, 7 VISOR_INSET 9 +
VISOR_GAP 0.72 + ROCK_NUDGE 11, 8 SP_NUDGE -19. Crash analysis: the 03:49 session ended in the DE's 'CRITICAL: Zone
not found' (random venue bug, not the HUD); the 03:47 mode-switch dump (0xc00001a5 at exe+0x5728f2) has no log
(overwritten): reproduce once and keep debug.txt. TODO: 1 (crash repro), 3 adaptive size, 5 battle effects vs
highway, 9-11 band, 12, 13, gluing model, per-player SP tube.

## 2026-10-22 03:xx: user's test of 1.38 (OPEN, work these first)

Face-off: highway spacing OK now (pieces still not glued). Versus dial: the leader's colour must be shinier. Empty
streak lights show the wrong (DE) texture until the first note. 3-4 digit streak fit did NOT work (fit_width
ignored?). Score thousands separators (as in quickplay) not applied to the versus scores. SP tube: not tracked, no
animated lightning when ready (the per-player tube rework). Battle: the slot visors are tilted (the same art on the
streak meter is upright: use it unrotated); the power-up cards still too big.
DONE + INSTALLED 03:30 (plugin 1.39): leader glow blend Add; streak STREAK_K 0.155 (4 digits fit; fit_width is
ignored by the DE); stock light names -> ours on our meters (kStockLights, SetTexture hook: empty state at start);
separators also while the versus needle / battle meter is up (g_vs_seen, g_battle_seen); battle visors upright
(visor_affine: rail map's size only, no rail rotation); CARD_FILL 0.66. Battle needle: 'battle track' log shows the
needle zones and the DE's LEDs agree (green at deg 16.2 > A/3 = 14, A = 42 confirmed by the clamp at 42.0): ask the
user what they expected before changing it.
NEW FEATURE REQUEST (user 2026-10-22): WoR's 6th star: when the last note is hit with 100% notes, the 5-star badge
goes to 6 with the same star animation (quickplay, single and band); user's WoR crop: the gold star shows '6'.

## 2026-10-22: user's in-game test of face-off v6 / battle v12 (OPEN, work these)

Clip `OneDrive\Videos\GH\WTDE_current_faceoff_battle.mp4` + the user's crops (WoR reference: versus meter frames).
1. Versus meter: WoR tints each half: active side bright (P1 blue / P2 red), inactive side dark (dark blue / dark
   red, not brown). Both score boxes are glued to the dial: each box's inner TOP corner touches the dial's bottom
   corner on its side, boxes drawn IN FRONT of the dial. Streak counts of 3-4 digits overflow the square: size per
   digit count, or one size that fits 4 digits.
2. Where the two highways touch, the WoR border sits a few px too high (gap at the bottom): lower the border, then
   move the highways a bit further apart so the borders don't touch.
3. Multiplayer highways (face-off): pieces not glued to the highway; streak lights show the wrong textures (the
   1-player fix from long ago is missing here); SP tube doesn't track (0:36-0:38 P1 has half a bar: no glow, no
   electricity, not at half; texture looks wrong; 0:42 activation drains from below the bottom). Goal: the exact
   1-player (quickplay) setup on every player.
4. Versus needle stops at ~70% of a side (the DE's -51.5..51.5 deg vs our 180-degree dial): remap like the
   quickplay rock needle fix.
5. Battle: rock tube not glued to the highway; highway gap issue in every multiplayer mode (band has more issues,
   later). Slots look perfect: move them a little further under the highway so the arms barely show.
6. Battle cards: right place; shrink the card radius a bit so the slot border shows; z order wrong: the first card
   must be in front, then the next, etc.
Plugin log of the run: battle needle stand-in found, rot range grew to -21.6..37.4 (swing 42); cards moved to slots.
BUILT 2026-10-22 (plugin 1.38 + mod, tests 25/25, NOT installed, mocks docs/mocks/mock_versus_v7_zoom.jpg,
mock_battle_v13.jpg): item 1 (dial red half tinted DIAL_RED_GAIN, boxes hang from the dial corners DIAL_ART /
BOX_ART, in front; streak text fit_width 'scale each line if larger' STREAK_FIT), item 2 (wor_1g.BORDER_DY 4 on the
theme's border offsets + SEP 19 -> 22: UNVERIFIED, needs the game), item 4 (needle_src twin + plugin vs_needle x
NEEDLE_K 1.65), item 5 slots (VISOR_INSET 4 px towards the highway), item 6 (CARD_FILL 0.8; plugin sets card z
19 + (3 - slot) * 0.02, cards recognised by z 19..19.1), item 3 lights (plugin set_lights picks the colour set from
the meter's own badge texture kOurMult; the multiplier query returned x1 in face-off).
User 2026-10-22 on that: streak lights must keep singleplayer colours (x1 IS pink); the real bug is the DE's stock light
textures on the multiplayer meters -> reverted the badge-colour change; plugin our_meter() now also recognises a
meter by any of its lights or a sibling multiplier badge (kOurMult), + log 'streak lights: widget ... set'. Score boxes
tucked BOX_TUCK 15 under the dial (mock docs/mocks/mock_versus_v8_zoom.jpg). Battle rock needle poorly tracked (user
crop: red LED lit, needle at the red / yellow boundary): plugin logs 'battle track: deg / health / zone / t | alphas'
once a second for the next test (compare the zone with the DE-driven LED alphas; then fix kBNeedleD stops or the
angle -> health map). Plugin 1.38 + mod INSTALLED 2026-10-22 03:02 (hash checked; the user had tested the old 1.37 build by mistake).
STILL OPEN: item 3 star power tube per player + gluing, item 5 rock tube gluing (+ needle tracking above). Cause found: the DE moves 2-player
highways in 3D (get_highway_pos_and_scale Pos, scale 1), so on screen the shift shrinks towards the horizon (~y 213,
where RAIL_L / RAIL_R meet); our maps move pieces by a constant SEP (hence ROCK_NUDGE). Plan: (a) a shift(y)
linear in y, zero at the horizon, fitted on the user's clip (f37.5: canvas = crop (240,135,1680,945) of the
letterboxed 1920x1080 frame); (b) per-player 1-player tube: every 1-player sp_* element carried through the player's
rail map (sprites rotated / scaled, clip + feather windows as screen boxes), plus a per-tube geometry table so the
plugin's tube engine (smooth fill, plasma, glows, burst, feathers) runs per tube (StarPower array, widget with 3
segments accepted).

## 2026-10-22: 2-player modes redone from scratch (face-off v6 / battle v12: INSTALLED 01:30, not tested in game)

User (2026-10-21, night, with their WoR 1v1 frame): Face-Off, Pro Face-Off and Battle are 2-player only in the DE, so:
- **Face-Off / Pro Face-Off** (tools/wor_versus.py): WoR's 1v1 layout only: the dial + one score box per player
  (HUD_band_battle_score, P2 mirrored, blue / red stripe): note streak in the small outer square (the DE's
  p1/p2_streak_number_text in the slide window: shown only while the DE's streak is on, its own threshold), score
  in the wide window (commas: plugin hook on the native seinttostring). **Dropped:** placing badges + burst,
  per-player bars, difficulty icons (their textures too: theme pak 3.99 MB). The DE's multiplier nixie lands on a
  hidden element (kVsNixieMap still needs the WoR_HUD_vsmult_* names). Highways keep SP tube + streak meter.
- **Battle** (tools/wor_battle.py): rock tube kept; no streak meter / note streak / SP tube; attack slots = the
  streak meter visor (our WoR_HUD_mult_1 art: ring + arm) three times where the SP tube goes, scales 1 / 0.85 /
  0.72 up the rail, one behind the other, arms on the rail, baked in the battle orientation (WoR_HUD_bvisor; hud_2d
  elements don't rotate); cards in the glass (CARD_FILL), the DE's empty-slot icon blank. The DE rings, disc and
  their textures are gone. Card table changed (kBCard 44 -> 31): **plugin 1.37** built (plugin/build/), not installed.
  User on battle v10 / v11 (2026-10-22): keep the ring and its SHORT arm (the bit joining it to the rail), cut only
  the long stick glued to that arm, which ran behind the stacked rings (VISOR_ARM box kept, the art cut at the rim
  elsewhere; VISOR_RING re-measured: ring centre 113.5, 96.5, rim r 40). v11 wrongly cut the short arm too.
- **Highway spacing (user 2026-10-22):** the games' 2-player highways touch; ours must too, corrected for the WoR
  border's thickness: SEP 30 -> 19 (the clip at 30 showed a 22.5 px gap between the borders at the screen's bottom
  edge; at stock spacing they overlap ~37 px). Every 2-highway layout, the wrapper and the card table follow SEP;
  plugin 1.37 rebuilt with it. mock_battle --current moves the clip's highways from FRAME_SEP 30 to SEP.
- Mocks: `docs/mocks/mock_versus_v6.jpg` (+ `_zoom`), `docs/mocks/mock_battle_v12.jpg` (+ `_zoom`; frame: the user's
  clip 1:15, `python tools/mock_battle.py <frame> <out> --current` for frames of the current build). The grey smear
  on the battle rails is the mock's inpainting of the old rings, not the layout.
- **Face-off crash (2026-10-21 23:48, build v2 + 1.36):** not the HUD. debug.txt: face-off's random venue pick
  (quickplay_choose_random_venue) chose venue 0xc53f60c5, no zone pak loaded ("changing reverb settings to None
  zone"), then apply_band_logo_to_venue -> "CRITICAL: Zone not found" and the DE's crash handler closed the game.
  Pick a venue by hand to test face-off. The earlier dumps (19:13, GHWT_Definitive.exe.39224.dmp) are a different
  crash: access violation in the render path (+0x100fab inside a d3d9 call), mode unknown.
- **Approved and installed 2026-10-22 01:30** (`build.py --install` + plugin 1.37 copied, hash checked). Next: test
  face-off (a fixed venue) and battle.

## Session stopped 2026-10-21, late (user request): where to resume

HEAD = 4fc5bc6 + this note: versus rework v2 + plugin **1.36**, built, tests 25/25. **Installed 2026-10-21** (user said
to apply the plan: `build.py --install` + plugin 1.36 copied to the game, hash checked); **not tested in game yet**.
Mock v2: `docs/mocks/mock_versus_v2.jpg`, `_zoom.jpg`.
User feedback that drove it (their WoR 2v2 frame: team bars "x4 | 150" / "137 | x2", per-player bars "+8 | 100"):
- the DE has teams (p4_pro_faceoff / p8 "Band vs Band": the versus props are per SIDE: band1/2 score, multiplier,
  streak, SP). Team bar (HUD_band_battle_score, P2 mirrored via WoR_HUD_vs_score(_back)_m) = side multiplier AS TEXT in
  the square + side score. Multiplier text = baked textures WoR_HUD_vsmult_1..4 / sp2..sp8 ("x" fontgrid_text_a1 +
  number fontgrid_numeral_A2, white like WoR's uidesc_HUD_band_battle; no SP colour there); plugin 1.36 kVsMult /
  kVsNixieMap swap the DE's HUD_score_nixie_* names to them on those elements.
- per-player bars (competitive_meter back/frame/stripe at 640 -/+ PBAR_DX, PBAR_K 0.70): player note streak (NO "+":
  WoR's "+N" is its point system) | player score, same font/size, SCORE_K 0.26 everywhere. Bound in
  WoR_HUD_HUD_attach_widget_band_faceoff_meter by AttachHudWidget player1/2_status Score / note_streak ->
  pscore_N_text / pstreak_N_text, only when current_num_players = 2 (4p still uses the DE's desc). Third square
  (WoR difficulty icon) empty.
- every highway keeps its SP tube AND streak meter in face-off: wor_mult_mp's alias_player_multiplier now points at a
  hidden stand-in (mult_die_standin), so the DE's face-off Die (GH:588-594, the only user of that alias) kills that.
- the team bar's old "+N" streak window is kept invisible (alias_streak_pN needed by the DE's streak animation).
User's answers (2026-10-21, late): (1) the side streak is shown: in 2-player a side is one player, so that is the
streak in the per-player bar on the highway (kept); in the 4-player team layout it goes left of the team score;
(2) no team layout with only 2 players. Done: the team bars (score_container_N) are alpha 0 in our desc (2-player only;
elements kept for the DE's props and alias_streak_pN). Mock v3 `docs/mocks/mock_versus_v3.jpg` / `_zoom.jpg`.
User on v3 (2026-10-21, late), done in mock v4 (`docs/mocks/mock_versus_v4.jpg` / `_zoom.jpg`), built, tests 25/25,
**NOT installed, awaiting approval** (install = `python build.py --install`; plugin unchanged, 1.36):
- **The mocks v1-v3 were mis-registered:** the clip frames are the 2560x1080 game letterboxed, and the mocks drew the
  canvas over the whole squashed frame. tools/mock_mp.py `register()` now takes the centred 16:9 part (like
  mock_battle); feed it frames straight from the clip (ffmpeg -ss 36 / 128, 1920x1080). The layout geometry
  (wor_battle rails) was right; PBAR_DX had been tuned on the bad mock: the per-player bars now sit on
  highway_top_centre (that was the "streak counter not aligned on the 2nd highway").
- WT streak lights: frame residue in the mock (the DE's player_meter lights; in game our wor_mult_mp replaces that
  desc); the mock now inpaints the DE elements before moving the highways.
- 1st place: the starburst gold (BURST_RGBA, WoR clip hue ~44 deg), normal blend (added, it washed out to white).
- Sides: P1 blue, P2 red (P_RGBA swapped); the dial mirrored (FLIPPED: blue half + blue arc on the left).
- Difficulty: WoR's icon_difficulty_* in the per-player bar's third square (pdiff_N, set by the face-off wrapper from
  playerN_status.difficulty with plain ifs). Theme pak 4.13 MB (limit 4.19 MB).
Then 4-player Pro Face-Off (hud_3g1v): team bars + side streak left of the team score.
Theme pak 4.10 MB (limit 4 MiB = 4.19 MB): budget textures before adding more.
Done: install + push. Next: ask for the test run (checklist below, face-off items updated: team bars + per-player bars
+ streak meter per highway), and get answers to the two open questions above.

## Session stopped 2026-10-21 (earlier): where to resume

Installed in the game = HEAD (mod + plugin 1.35), nothing tested in game since battle test 2. Last user feedback (versus
score bars, from their WoR frame: team bar "x1 | 1", per-player bar "+1 | 1"):
- done: placing squares bigger with the rank inside (RANK_D 78, RANK_FACE), score font SCORE_K 0.30, the streak as
  "+N" in the score bar's first square (window streak_mask_N > container streak_N = alias_streak_pN, WoR "+" texture
  WoR_HUD_plus + the DE's p1/p2_streak_number_text; the DE's face-off streak animation slides it out of the window when
  the streak ends). Mock: tools/mock_mp.py -> scratch; close-up as the user saw it: score bars "+64 45,625".
- the LAST change (streak "+N" window) is built and installed but `python tests/run_offline.py` was NOT re-run and it
  is committed together with this note: run the tests first.
- open question to the user: the multiplier nixie badge still sits at each bar's outer end; WoR shows "x1" as text in
  that bar (the DE only gives the nixie texture, no number). Ask whether to drop the badge from the versus bars.
- user wants it tested next: quickplay, 2-player band, face-off, battle (see the checklist below).

## Built overnight 2026-10-21 (untested; plugin 1.35): test these first

See MODLOG "v0.50 WIP + plugin 1.35". Test in this order (ask before launching; quickplay first):
1. Quickplay 1 player: unchanged? (no messages there already). Then 2-player band / co-op (drums + guitar): per-player
   WoR rock tube (one LED, needle slides; log "multiplayer rock needle: remapped"), WoR SP tube per player (fills?
   which amount: the player's own or the band's?), multiplier badge on the tube top WITHOUT the instrument icon (log
   "multiplier: highway instrument icon ... replaced"), no "01234567" bar, no messages (Hot Start, SP Ready, streaks).
2. Face-off / pro face-off: highways 30 apart, WoR dial + team bars + scores + multiplier nixies, "1st" badge with
   starburst on the LEADER (if it shows on the trailing player, swap lead_1/lead_2 in wor_versus props), SP tubes,
   no rock tube, no messages.
3. Battle (plugin 1.34 fixes + no attack names / alert cards above the highway).
Logs: `wor_hud_fixes.log` (swap lines for hud_create_message, faceoff meter, player health), debug.txt.

## Next: face-off / pro face-off, band, vocals (user 2026-10-21) -- research DONE, first build above

User's current-state clip: `Downloads\Video Project 25.mp4` (0:00-0:53 face-off + pro face-off: the DE's GH3-style top
score bar and dial, highways touching; 0:53-1:46 battle; 1:46-end band: the DE's WT band meter top-left and per-player
bars showing "01234567" placeholder text). WoR references: `OneDrive\Videos\GH\WOR_face_off.mp4`,
`WOR_full_band_gameplay.mp4`, `WOR_microphone_gameplay.mp4`. Earlier parked mock: docs/mocks/mock_modes_v1.jpg,
rules docs/MODES_RULES.md (update it with the research).

User's requirements:
- Remove the messages above the highway (Hot Start, Star Power Ready, attack alerts, etc.) in **all modes** for this
  theme (1-player already ships without them: wor_1g.layout(no_messages=True)).
- Face-off / Pro Face-Off: WoR versus look: per-player score group (WoR's own score bar design), WoR's versus meter
  (different texture from the band meter), a placing per player (1st glows), star power tube + multiplier kept, **no
  rock meter**. Highway spacing like battle. The DE's SP highway effect already works on every highway; the tube not.
- Band: rock meter, star power tube and streak multiplier kept; WoR star power is per player (the DE's is shared:
  find a workaround, e.g. show the same amount on every player). Remove the instrument icon from the highway; use WoR's
  failed-instrument and instrument-icon textures.
- **Research done 2026-10-21: read `docs/MODES_RULES.md` "Research 2026-10-21" (+ docs/research/*).** Original brief:
- Research (mechanical, cheaper model): (1) GH wiki (guitarhero.fandom.com) on both games: versus / face-off / pro
  face-off, band (shared vs per-player SP, band multiplier, revive), multiplier rules per instrument, vocals scoring and
  the precision wording (WT: "Awesome / Strong / Good / Okay / Messy / Weak"-style vs WoR) -- write findings into
  docs/MODES_RULES.md with sources. (2) Identify every HUD asset in the three WoR clips and find it in
  `E:\Dev\ghwt\ghwor-extract` (texture png folders + decompiled descs/scripts: versus meter, score groups, placing
  badges 1st..4th + glow, multiplier bubble, band score / rocket, instrument icons, failed-instrument icons, vocal
  highway parts, precision text); list name -> file -> where used in docs/MODES_RULES.md. (3) The same for the DE's
  current HUD in the user's clip (which descs/layouts the DE uses per mode for our theme: theme rows in hudthemes,
  e.g. 0x6bd128d8 = battle layout; find the face-off and band ones).
- Then (expensive model): mocks per mode on frames of the user's clip, approval, build.



- **Dev folders:** everything lives under `E:\Dev\ghwt`: this repo, `ghwtde-ultrawide-fix` (separate repo, bundled
  in our package), `ghwt-bg-shader`, `tools` (Guitar Hero SDK, NodeROQ), `ghwor-extract`, `ghwt-extract`,
  `reference-video`, `reshade-6.8.0`, `asi-loader-9.7.4`, `game-backup-2026-10-06`, `reshade-backup-2026-10-10`.
  Defaults in `tools/paths.py`.
- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`; config
  `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini` (`HUDTheme=ghwor`,
  `GemTheme=ghwor`, `Preferred*Highway=GH5_Highway`, 2560x1080). The `GHWTDE.ini` in the game folder is not the live one.
- **Released: 0.49** (`releases/GH5-WoR_HUD_0.49.zip`, 23 MB; bundles Ultrawide Fix **1.0**). **Installed (from
  HEAD, version string still 0.49):** mod `WoR_HUD` + theme / gem / UI paks + `wor_hud_fixes.asi` **1.33** (battle
  mode rework) + `ghwtde_ultrawide.asi` / `.ini` **1.1** (no ReShade add-on any more) + ReShade (preset, `ghwt_bgfx.addon32`,
  which steps aside on DXVK). The package (`build.py --package`) bundles Ultrawide 1.1's asi + ini since 6e398df.
  Menu music: All Main Menu Music (its own repo; installed with Guitar Hero, GH II, Encore 80s, Aerosmith on).
- **WoR look, all choosable as "Guitar Hero: Warriors of Rock":** helper pills (+ gamertag pill), loading screen,
  menu popups (WoR frame, black background, brush bar; arrows coded but not showing), failed / song ended box, pause
  menu, You Rock (WoR's exploding text, flipbook lightning / ball / explosion, glow, WoR sound), star power sounds,
  rock needle, battle mode (0.50 WIP, rebuilt 10-21, untested, see Start here 1).
- **Confirmed by the user in game:** pills, menu music, pause (no crash, layout), popup look, loading ball, star power
  highway, career needle, every ultrawide screen; Ultrawide Fix 1.1 and All Main Menu Music 1.0 (2026-10-20).
  **Never confirmed:** fail box calibration, YOU ROCK round 3 (letters, gravity 3500, glow, sound), rock needle
  stand-in (plugin 1.31), popup message size, popup arrows (did not show), battle mode (rebuilt 10-21, untested).
- **Other repos:** Ultrawide Fix 1.1 (github.com/jgoa156/ghwtde-ultrawide-fix: ASI plugin, Hor+ 3D FOV, 2D layer at
  16:9; its 2D hooks go in at Direct3DCreate9 so wor_hud_fixes.asi still finds 0x5a05e0 untouched); All Main Menu
  Music 1.0 (github.com/jgoa156/ghwtde-all-main-menu-music, `python build.py --install <game>`; never replace the DE's
  menu_music_songs from its QBName QB: crashed the game at boot).
- **Confirmed in game (2026-10-10):** WoR star power highway effect (0.47 / plugin 1.24: cyan rail glows, stars up
  the rails, strikeline rush; MODLOG "v0.47"), career rock needle (plugin 1.22), the new preset, every ultrawide screen
  (title, menus, song list, loading, YOU ROCK themes, song intro, left-pinned menus). User: the occasional crash
  seems gone.
- **ReShade preset:** `GHWoRHudModPreset.ini` = Behon's GH5WORStyle v2 (Nexus guitarheroworldtour mod 2021, built on
  Ricochet27's GH5/WoR ReShade) + our GH5_Grade, AdaptiveTonemapper, vort_MotionBlur. qUINT (MXAO, ADOF, sharpen)
  is "all rights reserved": not shipped, users tick it in the ReShade installer. Credits in THIRD_PARTY_LICENSES.txt.
- **Known issues:** face-off crashes (no dump yet: WER LocalDumps for GHWT_Definitive.exe not enabled); face-off /
  battle HUDs not adjusted for ultrawide; the DE's SP highway glow leaks a little above/below the highway (minor);
  the WoR star power highway effect is only checked with one player.
- **Lessons (don't repeat):**
  - a mod cannot redefine a game script (the engine ignores it; `tests/run_offline.py` guards it). Workaround that
    works: ship the logic under a WoR_HUD_ name and let the plugin copy its QB symbol entry over the DE script's
    (symbol table `[0xd48f5c]`, see MODLOG "plugin 1.22"); to wrap a DE script, kScriptSwaps saves the original
    into a placeholder first (MODLOG "v0.47");
  - a CreateScreenElement whose parent doesn't exist crashed the game (SetParent 0x5a0240); plugin 1.24 guards it
    and logs "missing parent" in wor_hud_fixes.log. Our QB printf lines DO reach debug.txt (tagged [0xd8b982c2]);
  - never put a $Func$${...}$ struct argument inside a parenthesised expression (AND/OR): it crashed the game
    (0x5f0a8e); use plain ifs or the $id$ = $x$ form;
  - CreateScreenElement overwrites the calling script's `id` with the new element's; SetScreenElementProps on a
    missing element crashes the game (0x63a133): keep ids in other locals and check ScreenElementExists first;
  - mod list text (Mod.ini / menumusic.ini): only letters, digits, spaces and , . : / (the DE fonts lack the double
    quote and others);
  - the DE doesn't animate AnimatedTexture_UI flipbook materials (WoR's lightning / ball / explosion): it draws the
    whole sheet. Use one texture per frame switched by WoR_HUD_flipbook (sprites) or static one-cell materials built
    on an ImmediateMode_UI / UI_Col_Tex_2D material (particles; a particle's size follows its texture size);
  - WoR scripts can use forms the DE ignores (`$apply_gravity$ = $true$`): prefer the DE's own spelling; DE strings
    are localised keys (GetUpperCaseString leaves them as they are);
  - a desc text whose fit_height is "clip top lines" vanishes when the font is taller than its box;
  - textures that live in `z_in_game` can't be overridden from our paks (the per-song reload wins); gem-pak textures can;
  - after changing star/score geometry in `tools/wor_1g.py`, ALWAYS run `python tools/gen_plugin_names.py` before
    `pluginuild.bat`;
  - send mocks to the user with SendUserFile (writing them to `verify/` is not enough);
  - never insert a line above a script's `${ ... }$` default-parameter block: it voids the defaults (froze YOU ROCK).

## Task list (2026-10-20, user order)

1. Battle mode rework: built 2026-10-21 (Start here 1); the card above the highway is still to be designed with the user.
2. One test run (ask first): battle + every "never confirmed" item above.
3. Release HUD 0.50 (bundles Ultrawide 1.1): bump VERSION in build.py, `python build.py --package`, zip to releases/,
   push; Nexus page text like the other two repos' `docs/NEXUS.txt`.
4. Popup up/down arrows: code ships (WoR_HUD_create_popup_warning_menu, ARROW_UP_DY / ARROW_DN_DY in wor_menus.py) but
   they did not show in game; user: leave it for now.
5. Face-off crash (enable WER LocalDumps for GHWT_Definitive.exe first) + face-off layouts.
6. Multiplayer / vocals layouts (docs/MODES_RULES.md, mocks in docs/mocks).
7. Song list side art (`4b93dd1e` / `b19ce07d`, the user is remastering them).
8. Drum animations (docs/DRUM_ANIMS_PLAN.md + the 10-16 scan; GH5 is now pulled to `E:\Dev\ghwt\gh5-extract`).
9. Full code review of the three repos (HUD, ultrawide, all main menu music) for optimisation.
10. Small visuals: WoR's Star03 sliver for the star power burst; the DE's SP highway glow leak.
11. Ideas to evaluate: game-catalogue jump menu (SELECT / its PC key; each install's library differs); song list
    sorting that ignores a leading "The".
12. All Main Menu Music "now playing" toast (bottom-left: song, artist, game, like EA Trax games): plan in that repo's
    README (Title= / Artist= / Game= per track, a native hook on the menu-song picker, mock first).

Dropped: WoR highway lines (the user was wrong about them); the menu music collection installer (replaced by
All Main Menu Music).

## How to work on it

- `python build.py [--install] [--package]`; `python tests/run_offline.py` (25/25).
- Mocks: `python tools/mock.py <out.png> --crop tubes|tube-ends|score|full --variant "label: NAME=expr" ...`
  (base `verify/mock_inputs/base.png`, rebuilt by `tools/mock_base.py`).
- Plugin: `plugin\build.bat`; after changing star power geometry in `tools/wor_1g.py` run
  `python tools/gen_plugin_names.py` before building it. Copy `plugin/build/wor_hud_fixes.asi` to the game folder.
- Crash dumps: `%LOCALAPPDATA%\CrashDumps`; `python tools/dump_info.py <dmp>`, `tools/dump_mem.py <dmp> <addr> <n> --dis`.
- Refactor guard: `python tools/build_hashes.py save|check <json>`.
- Machine paths: `tools/paths.py` (env overrides). Game assets are never committed.

## Rules you set

- Ask before every game launch, and batch changes into one build.
- Mock first: show the mock and get approval before applying a layout or setting.
- Use only textures and fonts extracted from the games. Cropping, tinting, flipping and compositing are fine.
- The HUD draws above the highway. Prefer targeted fixes over rewrites.
- Screenshot collector (`tests\collect_session.py`): only when asked, started detached (no task notifications).
- Commit and push finished work to the repo.

## Single-zip release (done 2026-10-06)
- `build.py` builds ONE mod (`WoR_HUD`): no-messages layout is the only 1g layout (desc `hud_1g_ghwor`, theme id `ghwor`);
  dark metal sections + `$change$` lines live in `WoR_HUD_Load`. `--package` makes one zip: mod + paks + plugin +
  ASI loader at the root, and `Optional - ReShade (WoR shaders)` (ReShade 6.8.0 d3d9.dll, ReShade.ini, GHWoR.ini,
  reshade-shaders, ghwt_bgfx.addon32). ReShade is listed as a requirement (for the shader look only) in the READMEs.
  Since 6e398df the root also has Ultrawide Fix 1.1 (`ghwtde_ultrawide.asi` + `.ini`); the old addon32 is gone.
- Vendored ReShade files: `extras/reshade`. ReShade dll: `E:\Dev\ghwt
eshade-6.8.0`, ASI loader:
  `E:\Dev\ghwtsi-loader-9.7.4` (paths.py `RESHADE`, `ASI_LOADER`). `addon/build/ghwt_bgfx.addon32` = the tested binary.
- The user's game folder was reverted: old install moved to `E:\Dev\ghwt\game-backup-2026-10-06` (incl. GHWTDE.ini.bak);
  GHWTDE.ini now `HUDTheme=ghwor`. Next test = extract the Desktop zip into the game folder (+ the optional folder's
  contents) as a clean user would. Release notes: `docs/RELEASE_NOTES.md`.
- Known issue: the game still crashes SOMETIMES (not only on theme switch); log it, no fix yet.
