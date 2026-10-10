# GH5 / WoR HUD mod: session handoff (2026-10-10, v0.47)

Start here in a new session. History: `docs/MODLOG.md` (latest sections at the end). Plugin internals:
`docs/PLUGIN_NOTES.md`. Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (git author Guilherme Almeida
<jgoa156@gmail.com>, SSH push works). The mod is credited to **WitchDoctoR** (Mod.ini Author, READMEs).

## Where things stand

- **Dev folders:** everything lives under `E:\Dev\ghwt`: this repo, `ghwtde-ultrawide-fix` (separate repo, bundled
  in our package), `ghwt-bg-shader`, `tools` (Guitar Hero SDK, NodeROQ), `ghwor-extract`, `ghwt-extract`,
  `reference-video`, `reshade-6.8.0`, `asi-loader-9.7.4`, `game-backup-2026-10-06`, `reshade-backup-2026-10-10`.
  Defaults in `tools/paths.py`.
- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`; config
  `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini` (`HUDTheme=ghwor`,
  `GemTheme=ghwor`, `Preferred*Highway=GH5_Highway`, 2560x1080). The `GHWTDE.ini` in the game folder is not the live one.
- **Installed = released 0.47** (`releases/GH5-WoR_HUD_0.47.zip`, Desktop copy): mod `WoR_HUD` + theme/gem paks +
  `wor_hud_fixes.asi` **1.24** + ASI loader + ReShade (preset `GHWoRHudModPreset.ini`, `ghwt_bgfx.addon32`,
  `ghwtde_ultrawide.addon32` 0.2 beta).
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
    and logs "missing parent" in wor_hud_fixes.log. Our QB printf lines don't reach debug.txt;
  - textures that live in `z_in_game` can't be overridden from our paks (the per-song reload wins); gem-pak textures can;
  - after changing star/score geometry in `tools/wor_1g.py`, ALWAYS run `python tools/gen_plugin_names.py` before
    `pluginuild.bat`;
  - send mocks to the user with SendUserFile (writing them to `verify/` is not enough).

## Next steps

1. **WoR menus, loading screen, pill and helper themes** (next, user, 2026-10-10): research what the DE lets a mod
   theme there and what WoR assets exist. Mock first.
2. WoR highway lines (fret gradient, lighter border bottom, line above the strikeline, strings fading halfway):
   frets/border textures live in gems_ghwt, the strings' material sys_String01 in z_in_game. Mock first.
3. Face-off crash: enable WER LocalDumps (admin) and reproduce; face-off / battle ultrawide layout.
4. Song list side art: the user is remastering `4b93dd1e` / `b19ce07d` (256x2048, setlist_wtde.pak) for higher res.
5. Multiplayer / vocals layouts (only 1 player is WoR-styled); crowd selector (parked: no GH5/WoR crowd peds in the DE).

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
