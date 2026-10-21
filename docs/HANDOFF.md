# GH5 / WoR HUD mod: session handoff (2026-10-20, 0.49 released, 0.50 WIP)

Start here in a new session. History: `docs/MODLOG.md` (latest sections at the end). Plugin internals:
`docs/PLUGIN_NOTES.md`. Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (git author Guilherme Almeida
<jgoa156@gmail.com>, SSH push works). The mod is credited to **WitchDoctoR** (Mod.ini Author, READMEs).

## Start here (2026-10-20)

State: HUD **0.49** released (releases/, bundles Ultrawide Fix **1.0**). HEAD adds battle mode in the WoR style
(plugin 1.32, tools/wor_battle.py, mock verify/mock_battle_v6.jpg approved 10-16) and the bgfx add-on stepping aside on
DXVK; plugin 1.32 is installed, battle is NOT tested in game. Sibling repos, both released and confirmed working by the
user on 2026-10-20: **Ultrawide Fix 1.1** (ASI plugin, Hor+ 3D FOV, no ReShade needed; only release on its repo) and
**All Main Menu Music 1.0** (10 games in one mod, GitHub Release, World Tour's six always play).

1. **Battle mode rework** (user footage `OneDrive\Videos6-10-20 21-49-06.mp4`, 2560x1080, Ultrawide 1.1): the two
   GH5-width highways touch in the middle (the DE's 2p spacing is for World Tour's narrower highway); the attack slot
   rings float at the outer top corners off the rail with grey striped fills; the attack card shows above the highway
   instead of in a slot; P1's health arc runs off the left edge of the 16:9 area (clipped) and both needles sit outside
   their arcs. Mock v6 was never calibrated to DE positions: calibrate on frames from that clip, mock, get approval.
   (Ultrawide Fix 1.1 is bundled in the package since 6e398df.)
2. **Ask for one test run** (rule: ask before launching): the reworked battle mode, plus the still-unconfirmed 0.48/0.49 items: fail box calibration, YOU ROCK round 3 (letters,
   gravity 3500, glow, the WoR sound via SoundEvent), rock needle stand-in (plugin 1.31), popup message size.
3. **Release 0.50** with the above (`python build.py --package`, zip to releases/, push).
4. **Open decision:** popup up/down arrows (code ships, did not show in game; user: leave it for now).
5. **Backlog (user order):** face-off crash (enable WER LocalDumps first) + face-off layouts; multiplayer / vocals
   layouts (rules in docs/MODES_RULES.md, mocks in docs/mocks); song list side art (user remastering); drum
   animations (docs/DRUM_ANIMS_PLAN.md, not started); full code review of the HUD, ultrawide and menu music repos;
   WoR's Star03 sliver for the burst; the DE's SP highway glow leak; game-catalogue jump menu idea (SELECT key) and
   song list sorting that ignores a leading "The".

## Where things stand

- **Dev folders:** everything lives under `E:\Dev\ghwt`: this repo, `ghwtde-ultrawide-fix` (separate repo, bundled
  in our package), `ghwt-bg-shader`, `tools` (Guitar Hero SDK, NodeROQ), `ghwor-extract`, `ghwt-extract`,
  `reference-video`, `reshade-6.8.0`, `asi-loader-9.7.4`, `game-backup-2026-10-06`, `reshade-backup-2026-10-10`.
  Defaults in `tools/paths.py`.
- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`; config
  `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini` (`HUDTheme=ghwor`,
  `GemTheme=ghwor`, `Preferred*Highway=GH5_Highway`, 2560x1080). The `GHWTDE.ini` in the game folder is not the live one.
- **Released: 0.47** (`releases/GH5-WoR_HUD_0.47.zip`). **Installed: 0.48 WIP** (built from HEAD): mod `WoR_HUD` +
  theme / gem / UI paks (`wor_hud_ui.pak.xen`, 16.7 MB: raw-PNG loading art) + `wor_hud_fixes.asi` **1.27** + ASI
  loader + ReShade (preset, `ghwt_bgfx.addon32`, `ghwtde_ultrawide.addon32` from the ultrawide repo HEAD) + the
  "Main Menu Music Collection" (GH5 mod + WoR; the WoR-only mod is the released one).
- **0.48 WoR menu look** (MODLOG "v0.48 WIP" sections), all choosable as "Guitar Hero: Warriors of Rock":
  helper pills (+ gamertag pill), loading screen (ball, animated plate, raw 2x art; ultrawide: 16:9 + black bars),
  menu popups (WoR frame, black background, one message size, brush bar), failed / song ended box (calibrated on the
  user's WoR screenshot, verify/fail_overlay_v1.jpg), pause menu (black above the gameplay at z 598, title-cased song
  info, right-aligned items), You Rock (WoR's whole exploding-text sequence, lightning / ball / explosion as per-frame
  flipbooks, static glow materials, highway + HUD fade, "YOU ROCK!" fit width 755), star power awarded / activation
  = Band Hero's sounds by default, rock needle travel calibrated to the LED art (wor_1g ZONE_RY / ZONE_YG).
- **Confirmed by the user in game:** pills, menu music, pause (no crash, layout), popup look, loading ball.
  **Awaiting a test (installed):** fail box calibration, You Rock round 3 (gravity, size, glow 128 px), rock needle,
  title-screen flashes (ultrawide), gameplay hidden under pause.
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

## Next steps

1. **Popup arrows: installed, awaiting a test + calibration.** WoR_HUD_create_popup_warning_menu creates two
   sprites under PopupElement, placed from the first / last option's absolute position (GetScreenElementChildren +
   GetScreenElementPosition absolute) + ARROW_UP_DY / ARROW_DN_DY (wor_menus.py); size 0.9 of the mock (49 units),
   3 px closer than the mock. Release HUD 0.49 once they sit right. Older note: WoR's are ui_shared `Dropdown_Arrow` (gold chevron, flipped for down); mock
   `verify/mock_popup_arrows_v1.jpg` awaiting a size pick. The popup descs have no arrow element: add two sprites
   (or repurpose hidden ones: fail desc 0x86431767 / 0x205d5bf9, main mixer_glow_64 / dialog_bg_menu) above the first
   and below the last option. Also untested: popup title #3f352a lower (BANNER_Y - 9), fail box COMPLETED / ON at natural
   width (boxes 400 / 160), figures #e1474e.
2. **After publishing (user, 2026-10-11):** full code review of the 3 projects (HUD, ultrawide, all main menu music)
   for optimisation; WoR's Star03 sliver for the burst; the SP glow leak.
3. **New mod idea (evaluate):** a game-catalogue jump menu opened with SELECT (Xbox) / its PC key, listing the games
   installed (dynamic: each install has a different library); song list sorting optimisations and ignoring a leading
   "The" when sorting / displaying.
4. Later (user): face-off crash + layouts, multiplayer / vocals layouts, song list side art, drum animations.
   Dropped: WoR highway lines (user was wrong about them).

Released 2026-10-11: HUD 0.49 (releases/, 23 MB, bundles Ultrawide Fix 1.0), Ultrawide Fix 1.0. The menu music is one all-games mod
(ghwtde-all-main-menu-music); `build.py --install` does not install it (that repo's build.py does). Popup arrows: code ships but they did not show in game
(user: leave it for now).

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
- Vendored ReShade files: `extras/reshade`. ReShade dll: `E:\Dev\ghwt
eshade-6.8.0`, ASI loader:
  `E:\Dev\ghwtsi-loader-9.7.4` (paths.py `RESHADE`, `ASI_LOADER`). `addon/build/ghwt_bgfx.addon32` = the tested binary.
- The user's game folder was reverted: old install moved to `E:\Dev\ghwt\game-backup-2026-10-06` (incl. GHWTDE.ini.bak);
  GHWTDE.ini now `HUDTheme=ghwor`. Next test = extract the Desktop zip into the game folder (+ the optional folder's
  contents) as a clean user would. Release notes: `docs/RELEASE_NOTES.md`.
- Known issue: the game still crashes SOMETIMES (not only on theme switch); log it, no fix yet.
