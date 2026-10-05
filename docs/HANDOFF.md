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
- **Installed:** HUD v0.39 + `dinput8.dll` (Ultimate ASI Loader v9.7.4) + `wor_hud_fixes.asi` 1.3, all in the game
  folder / `DATA`. Verified in game up to plugin 1.1 / v0.38 (streak lights incl. pink x1 and song 2; star power fill
  on song 2). **Not yet tested:** plugin 1.2 theme-switch fix, plugin 1.3 + v0.39 smooth star power fill.
- **Layout:** approved and stable (meters, border, score, star count 0.77, outer shadows B x0.2, tube end balls).
- **Shaders (user: "perfect"):** `GHWoR.ini` follows the original WoR preset (SSDO full res + ssdonoise.png,
  Bloom, SurfaceBlur, vort_MotionBlur, AdaptiveTonemapper, Curves, GH5_Grade, Vibrance); F5/F6/F7 toggle SSDO /
  Motion Blur / GH5 grade. Background-only add-on source in `addon/`. Backups: `C:\Users\rockb\mods\ghwt-bg-shader\backups`.

## Next steps

1. **Test v0.39 / plugin 1.3** (ask before launching; collector only on request, detached):
   - star power fill: smooth cut at 25/50/75%, 50% on the needle, lightning once charged, song 2 still fine;
   - theme switch to another HUD theme and back: no crash; send `wor_hud_fixes.log` (font table bounds lines).
   If the clip window doesn't clip the rotated fill (or the fill sits off), the HUD falls back to six segments by
   removing the plugin; debug with the log and `tools/mock.py`.
2. **Star power look** (see PLUGIN_NOTES "Star power look"): mock (b) teal highway wash + neon borders as HUD sprites
   driven by the DE's SP glow value; then plugin work for the activation burst, gem lightning, animated crackle.
3. Score thousands commas (plugin), Helper Pill / Menu Popup themes (later).
4. Packaging: `build.py --package` doesn't include the plugin + loader yet (Nexus option 3, "HUD fixes").

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
