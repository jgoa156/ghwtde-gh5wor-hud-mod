# GH5 / WoR HUD mod: session handoff (2026-10-05)

Start here when you continue this work in a new session. The full history is in `docs/MODLOG.md` (latest
sections: v0.27-v0.35). Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (author Guilherme Almeida, SSH works).

## Where things stand

- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`. The config is
  `C:\Users\rockb\OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini`
  (`HUDTheme=ghwor_nomsg`, `GemTheme=ghwor`, 2560x1080, `Preferred{Guitarist,Bassist}Highway=GH5_Highway` for testing,
  DOFBlur 3.5).
- **Mod:** `C:\Users\rockb\mods\ghwt-wor-hud` (this repo; see README.md for the layout).
  - `python build.py` builds; `--install` installs into the game; `--package` writes the Nexus zips to `dist\`.
  - `python tests\run_offline.py`: 24/24 pass.
  - Mock: `python tools/mock.py <out.png> --crop tubes|tube-ends|score|full --variant "label: NAME=expr" ...`
    on `verify/mock_inputs/base.png` (rebuilt by `tools/mock_base.py`; it puts the WoR border where the game draws
    it). In-game shots are 2560x1080: resize to 1280x720 to compare with the canvas.
  - Machine paths: `tools/paths.py` (env overrides). Refactor guard: `python tools/build_hashes.py save|check <json>`.
- **Installed (2026-10-05):** HUD v0.35. User-approved: border 12 px closer (BORDER_OFFSET 17.4), tubes on the thick
  bevel (RAIL_OUTSET -13.4 / 15.7), STAR_NUM_K 0.78, SP slanted partial cut, SP 50% ends at the needle, HUD outer
  shadows (option B x0.2), 28 px hard black ball (2 stacked circle_gradient_64) under each tube's curled end, drawn
  under the highway surface. v0.34/v0.35 not yet verified in game.
- **Shaders (user: "perfect"):** ReShade preset `GHWoR.ini` follows the original WoR preset: SSDO (full res) with its
  `ssdonoise.png`, Bloom, SurfaceBlur, vort_MotionBlur, AdaptiveTonemapper, Curves, GH5_Grade, Vibrance
  (AdaptiveTint fails to compile and is off). Toggles: F5 SSDO, F6 Motion Blur, F7 GH5 grade. Background-only
  add-on: source in `addon/`, built as "Background-only shaders". Backups: `C:\Users\rockb\mods\ghwt-bg-shader\backups`.

## Shipping (Nexus, drop-in like CLEO mods: extract into the game folder, no scripts, no ini edits)

1. **Main file, GH5/WoR HUD:** `DATA\MODS\WoR_HUD\` + `DATA\PAK\hud_ghwor.pak.xen` + `DATA\PAK\gems_ghwor_hud.pak.xen`.
   The WoR border needs GemTheme=ghwor (it rides in the WoR gem pak copy).
2. **Optional:** no-messages theme, dark highway metal, background-only shaders (`ghwt_bgfx.addon32` +
   `GH5_Grade.fx`).
3. **Optional, HUD fixes (next):** `.asi` plugin for Ultimate ASI Loader, see `docs/PLUGIN_NOTES.md`.

**Enable/disable switches: skipped for now (user, 2026-10-04).** Revisit with a WTDE build.

## Rules you set

- Ask before every game launch, and batch changes into one build.
- Mock first: show the mock and get approval before applying a layout or setting.
- Use only textures and fonts extracted from the games. Cropping, tinting, flipping and compositing are fine. Never
  commit extracted game assets to the repo.
- The HUD draws above the highway.
- Prefer targeted fixes on the current build over rewrites.
- Screenshot collector (`tests\collect_session.py`): start it only when the user asks, detached (no task
  notifications); it exits when the game does.

## Open items (native plugin unless noted; details in docs/PLUGIN_NOTES.md)

1. 2nd-song streak lights revert to stock (DE script hard-codes the names; our paks stay resident).
2. x1 pink streak lights (x1/x2 share the plain set).
3. SP partial fill at 25/75% (the DE's y-scale squashes the slanted cut).
4. Score thousands commas, SP activation look (no footage).
5. Verify v0.34/v0.35 in game. Helper Pill theme, Menu Popup (later).
