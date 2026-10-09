# GH5 / WoR HUD mod: session handoff (2026-10-09)

Start here in a new session. History: `docs/MODLOG.md` (latest sections at the end). Plugin internals:
`docs/PLUGIN_NOTES.md`. Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (git author Guilherme Almeida
<jgoa156@gmail.com>, SSH push works). The mod is credited to **WitchDoctoR** (Mod.ini Author, READMEs).

## Where things stand

- **Dev folders:** everything lives under `E:\Dev\ghwt`: this repo, `ghwt-bg-shader`, `tools` (Guitar Hero SDK, NodeROQ),
  `ghwor-extract`, `ghwt-extract`, `reference-video`, `reshade-6.8.0`, `asi-loader-9.7.4`, `game-backup-2026-10-06`.
  Defaults in `tools/paths.py`. User reference clips: `C:\Users\rockb\OneDrive\Videos\GH\WOR.mp4` (WoR), `GH5.mp4`;
  test recordings land in `C:\Users\rockb\Downloads\Video Project N.mp4` and `C:\Users\rockb\OneDrive\Videos`.
- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`; config `...\Guitar Hero World Tour Definitive Edition\GHWTDE.ini`
  (`HUDTheme=ghwor`, `GemTheme=ghwor`, 2560x1080).
- **Installed now:** HUD v0.43 (one mod `WoR_HUD`: no-messages layout + dark metal built in) + `gems_ghwor_hud` (border +
  WoR Tesla arc bolt) + `wor_hud_fixes.asi` **1.13** + `dinput8.dll` (ASI loader) + ReShade.
- **Confirmed in game (2026-10-07):** layout, shaders, streak lights, SP fill, WoR Tesla arc gem strike, score commas
  ("6,705", plugin 1.12), white aura balls on both score bars at the bar tips, song line glued to the box, star back to
  the v0.40 look.
- **Installed, NOT yet tested:** plugin 1.13: star power phrase burst particles at WoR size (Create2DParticleSystem hook,
  see MODLOG). Check the log line "star power burst: particle sizes hooked" and the size of the blue/white stars when a SP
  phrase completes.
- **Known issues:** the game still crashes SOMETIMES (not only on theme switch), no fix yet; the DE's SP highway glow
  leaks a little above/below the highway (user: minor, leave it); burst particles keep the DE textures (WoR's Star03
  sliver would need a material swap: the DE textures live in z_in_game, which reloads per song and shadows ours).
- **Lessons (don't repeat):**
  - a mod cannot redefine a game script (the engine ignores it; `tests/run_offline.py` guards it);
  - textures that live in `z_in_game` can't be overridden from our paks (the per-song reload wins); gem-pak textures can;
  - after changing star/score geometry in `tools/wor_1g.py`, ALWAYS run `python tools/gen_plugin_names.py` before
    `plugin\build.bat` (v0.42 shipped with stale ball offsets);
  - send mocks to the user with SendUserFile (writing them to `verify/` is not enough).
- **Desktop zip is stale** (0.40): rebuild with `python build.py --package` and copy it to the Desktop after the next test.

## Latest (2026-10-09): v0.44 + plugin 1.15 installed, NOT yet tested (see MODLOG last section)
- Test: boot with HUDTheme=ghwor (log line "WoR_HUD: HUD Theme re-read..."), textures must load; theme switches
  both ways; song line (track = gold bar span, 50% tick); SP tube (flat bottom, lighter blue ready, neon needles).
- Ultrawide: canvas scale 0xd5ab7c/80 (2.0/1.5 at 2560x1080) written by GHWTDE.dll; fix = sprite sizes on the y scale.
- Highway SP effect (stars up the highway, glowing rails): researched only, plan in docs/GH5_STAR_POWER_REFERENCE.md.

## Next steps

1. **Next test** (ask before launching): SP burst particle size (plugin 1.13); regression-check the rest.
2. Rebuild the single zip (`--package`), update `docs/RELEASE_NOTES.md`, copy the zip to the Desktop.
3. Optional polish: WoR's Star03 sliver texture for the burst (material swap in the same hook: config +0x44 is the
   material checksum; needs a material whose texture lives in a pak we control). Star: user chose "regress to 0.40";
   mocks A/B are in `verify/mock_star_v043_x2.png` if it is revisited.
4. Multiplayer / vocals layouts (only 1 player is WoR-styled); drums gem theme check against WoR footage.
5. **Native ultrawide fix as an ASI plugin** (user: at 2560x1080 the WHOLE game is stretched). Leads (GHWT_Definitive.exe, 2026-10-08):
   the engine's screen aspect is a global float at 0xd9ef74, written at boot by the setter 0x5c7c20 (called from 0x4fce6f with the
   only 16/9 float constant, .rdata 0xa24eec); readers: 0x5546b0, 0x5c1538 / 0x5c1574 (FOV adjust, already aspect dependent),
   0x6371b2, 0x7501cb, 0x75cb70. Plan: hook 0x5c7c20 to pass the real window aspect (3D un-stretch / Hor+), then find the 2D canvas
   mapping (1280x720 canvas stretched to the window; refs 0x52a51a..0x52a562) and keep the canvas at 16:9 centred or anchor the
   sides; our border / tubes / score are placed in canvas space, so they would need re-checking. Also videos/menus.
6. Helper Pill / Menu Popup themes (later); crowd models and drummer animations (optional, need Xbox 360 converters).

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
