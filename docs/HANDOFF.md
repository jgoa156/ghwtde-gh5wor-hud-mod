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

## 2026-10-22: 2-player modes redone from scratch (mocks v5 / battle v10, built, NOT installed)

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
- Next after approval: `python build.py --install`, copy plugin/build/wor_hud_fixes.asi (1.37) to the game, test
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
