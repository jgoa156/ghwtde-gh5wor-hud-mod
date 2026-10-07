# GH5 / Warriors of Rock HUD for GHWT: Definitive Edition

By WitchDoctoR.

A data-only HUD theme for *Guitar Hero World Tour: Definitive Edition* that rebuilds the Guitar Hero 5 /
Warriors of Rock gameplay HUD from the games' own art: rock meter and star power tubes on the WoR highway border,
the score / star / note-streak panel, the multiplier badge and soft HUD shadows. It adds
"Guitar Hero: Warriors of Rock" to the DE's HUD Theme options; nothing in the game is overwritten.

## What ships (one Nexus drop-in zip, built by `python build.py --package`)

**Requirement:** ReShade 6.x (32-bit, D3D9) for the WoR shader look; the HUD works without it. A copy ships in
the zip's optional folder.

| Part | Installs into the game folder | Notes |
|---|---|---|
| HUD theme | `DATA\MODS\WoR_HUD\`, `DATA\PAK\hud_ghwor.pak.xen`, `DATA\PAK\gems_ghwor_hud.pak.xen` | HUD Theme = Warriors of Rock (no in-play messages, darker highway metal); the WoR border needs Gem Theme = WoR |
| HUD fixes | `dinput8.dll` (Ultimate ASI Loader), `wor_hud_fixes.asi` | WoR streak light colours, textures on the 2nd song, smooth star power, theme switch crash |
| Optional - ReShade (WoR shaders) | `d3d9.dll`, `ReShade.ini`, `GHWoR.ini`, `reshade-shaders\`, `ghwt_bgfx.addon32` | ReShade 6.8.0 + the WoR preset; the add-on keeps effects off the HUD |

## Building

Requirements: Python 3 with Pillow, OpenCV and NumPy; Node.js; a Guitar Hero SDK checkout (`sdk.js`,
`png2img.js`) with `x360img.py`; the DE installed; textures extracted from your own Warriors of Rock copy. Game
assets are not in this repository: set the locations in `tools/paths.py` or through the environment variables it
lists (`GAME`, `GAME_CONFIG`, `GH_TOOLS`, `WOR_EXTRACT`, `DE_EXTRACT`, `GH5_VIDEO`, `RESHADE`, `ASI_LOADER`).

```
python build.py              # build/WoR_HUD
python build.py --install    # copy into the game folder
python build.py --package    # dist/GH5-WoR_HUD_<version>.zip
python tests/run_offline.py  # offline checks (never launches the game)
```

The add-on is built separately with `addon\build.bat` (Visual Studio C++ x86 tools; ReShade and Dear ImGui
sources in `addon\deps`, see `addon/README.md`).

## Layout

- `build.py`: builds, installs and packages the mods.
- `tools/wor_1g.py`: the HUD itself (every position, size, tint and shadow setting is at the top of its section).
- `tools/`: desc generator, texture / font converters, pak helpers, `paths.py`.
- `tools/mock.py`: side-by-side mocks of settings on a calibrated in-game base (`tools/mock_base.py`), used to
  approve every layout change before a build; `tools/preview_hud.py` is the renderer.
- `tools/build_hashes.py`: fingerprints the build output (refactors must keep it identical).
- `tests/`: offline suite, in-game smoke test, passive screenshot collector.
- `addon/`: the background-only shaders ReShade add-on and the GH5 grade shader.
- `plugin/`: the HUD fixes plugin (`wor_hud_fixes.asi`); `tools/gen_plugin_names.py` writes its generated header.
- `docs/`: `HANDOFF.md` (current state), `MODLOG.md` (full history), `PLUGIN_NOTES.md` (plugin reverse engineering).
