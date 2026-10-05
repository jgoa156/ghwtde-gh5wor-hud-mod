# Background-only shaders (ReShade add-on)

`ghwt_bgfx.addon32` makes the ReShade preset apply to the background only (venue, band, crowd) and only during
songs and cutscenes: it calls `effect_runtime::render_effects()` right before the first HUD draw, which also
suppresses ReShade's end-of-frame pass. `shaders/GH5_Grade.fx` is the GH5 tone grade used in the preset
(`WoR_Look.fx` is an earlier experiment). The design notes are in `docs/ADDON_PLAN.md`.

Settings live in `ReShade.ini` under `[GHWT_BGFX]`; the investigation tooling (F10 frame dump, F9 scrub, trigger
file) is off unless `Debug=1`.

## Building

`build.bat` (Visual Studio 2022+ with the C++ x86 tools and a Windows SDK) writes `build\ghwt_bgfx.addon32`.
It needs, under `deps\` (not committed):

- `deps\reshade\`: the ReShade source tree (API 20, ReShade 6.x), for `deps\reshade\include`
- `deps\imgui\`: Dear ImGui 1.92.5 (`imgui.h`)
