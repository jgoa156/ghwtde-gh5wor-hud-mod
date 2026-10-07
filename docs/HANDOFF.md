# GH5 / WoR HUD mod: session handoff (2026-10-05)

Start here in a new session. History: `docs/MODLOG.md` (latest sections at the end). Plugin internals:
`docs/PLUGIN_NOTES.md`. Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (git author Guilherme Almeida
<jgoa156@gmail.com>, SSH push works). The mod is credited to **WitchDoctoR** (Mod.ini Author, READMEs).

## Where things stand

- **Dev folders (moved 2026-10-05):** everything lives under `E:\Dev\ghwt`: this repo, `ghwt-bg-shader`, `tools`
  (Guitar Hero SDK, NodeROQ), `ghwor-extract`, `ghwt-extract`, `reference-video` (GH5 footage). Defaults in `tools/paths.py`.

- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`; config
  `C:\Users\rockb\OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini`
  (`HUDTheme=ghwor_nomsg`, `GemTheme=ghwor`, 2560x1080, `Preferred{Guitarist,Bassist}Highway=GH5_Highway` for testing).
- **Installed (before 2026-10-06 revert):** HUD v0.39 + `dinput8.dll` (Ultimate ASI Loader v9.7.4) + `wor_hud_fixes.asi` 1.12, all in the game
  folder / `DATA`. Verified in game up to plugin 1.1 / v0.38 (streak lights incl. pink x1 and song 2; star power fill
  on song 2). **Not yet tested:** plugin 1.2 theme-switch fix; plugin 1.8 GH5 star power lifecycle + soft fill top + per-frame glide, raw PNG fill/plasma (charging bottom glow, 60 fps
  ready plasma + white cap, 50% ball-lightning burst), star spark centring, wedge star bar; earlier: plugin 1.5 smooth fill (1.3's fill was invisible in
  game: SetPos flag 0 only sets a tween target; 1.4 was still invisible: 0x5a14e0 is SetJust; 1.5 calls the real SetDims 0x5a1290).
- **Layout:** approved and stable (meters, border, score, star count 0.77, outer shadows B x0.2, tube end balls).
- **Shaders (user: "perfect"):** `GHWoR.ini` follows the original WoR preset (SSDO full res + ssdonoise.png,
  Bloom, SurfaceBlur, vort_MotionBlur, AdaptiveTonemapper, Curves, GH5_Grade, Vibrance); F5/F6/F7 toggle SSDO /
  Motion Blur / GH5 grade. Background-only add-on source in `addon/`. Backups: `C:\Users\rockb\mods\ghwt-bg-shader\backups`.

## Next steps

1. **Test v0.39 / plugin 1.5** (ask before launching; collector only on request, detached):
   - star power fill: smooth cut at 25/50/75%, 50% on the needle, lightning once charged, song 2 still fine;
   - theme switch to another HUD theme and back: no crash; send `wor_hud_fixes.log` (font table bounds lines).
   If the clip window doesn't clip the rotated fill (or the fill sits off), the HUD falls back to six segments by
   removing the plugin; debug with the log and `tools/mock.py`.
2. **Star power look** (see PLUGIN_NOTES "Star power look"): mock (b) teal highway wash + neon borders as HUD sprites
   driven by the DE's SP glow value; then plugin work for the activation burst, gem lightning, animated crackle.
3. Multiplayer / vocals layouts: the WoR look is only built for 1 guitar player (band modes, other multiplayer
   modes and the microphone player still use the DE layouts). Drums: verify the DE's ghwor gem theme (gems,
   kick bars, strikeline) against WoR drum footage.
4. Score thousands commas (plugin), Helper Pill / Menu Popup themes (later).
4. Crowd models for the DE (feasibility checked 2026-10-06: possible, but needs a new converter): WoR's crowd is already
   extracted raw in `ghwor-extract/all/x/compressed_ZONES_*/models/real_crowd` (per-venue `crowd_ped_*` / `pedf_*` .skin.xen + .tex.xen,
   ~70-110 KB skins, 200-640 KB textures) plus the shared hands in `ZONES_global` (6 skins). The DE extract has only the 8 hand
   skins. Textures convert with the existing x360tex tooling; the Xbox 360 `.skin.xen` format (big-endian) has no converter in
   the SDK, so the skins need reverse engineering to the DE's PC skin format first. Also needs the crowd animation data
   (`guitar_crowd*.qb`) checked against the DE's.
5. (Extremely optional) Drummer animations from WoR (and GH5, user can extract it later): WoR's are extracted raw
   in `ghwor-extract/all/x/compressed_PAK_perm_anims` (~460 drum `.ska.xen`: Drum_*_Hit_L/R, DrumDroid_*). Xbox
   360 format, no SDK converter; first step is comparing one DE drum animation with its WoR counterpart
   (skeleton/bone ids) before any converter work.
6. Packaging: `build.py --package` doesn't include the plugin + loader yet (Nexus option 3, "HUD fixes").

## How to work on it

- `python build.py [--install] [--package]`; `python tests/run_offline.py` (24/24).
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

## 2026-10-07 session notes (Sonnet) - open items
- v0.42 installed, untested: white aura ball (no tail, scale 1.1) on both score bars, song line glued to the box
  (see MODLOG). Gem strike = WoR Tesla arc under key 9d12571c in gems_ghwor_hud (04e3be8), untested.
- **Score commas: DONE in plugin 1.12 (see MODLOG), untested in game.** (old analysis follows) The score text is NOT a script
  FormatText: hud_widgets.qb attaches a native widget `seinttostring` (input player1_status.Score -> desc property
  `score_text`; band: score_1_text / score_2_text). The comma must be added in the plugin by hooking that widget's int->text
  step (find it from the checksum of "seinttostring" in the exe; see PLUGIN_NOTES for the method used for the streak lights
  and star power widgets). WoR's font has the comma glyph (WoR clip shows "84,225"). Needs reverse engineering: use Opus.
- Shards at star power activation: the user does see something in the DE but "glitchy low poly pixels" (probably the DE's own
  particle draws); WoR's are smooth white leaf slivers drifting right of the highway (Video Project 1, 20.1-20.4 s).
  NewMale_RP_FX / RP_Tesla_* are career rock-power effects (gain multiplier >= 2), gp_starpower_teslasparks01 is the 3D
  stage fx on the band member. Source of the clip's shards still unidentified.
