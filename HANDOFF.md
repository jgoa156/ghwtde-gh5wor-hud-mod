# GH5 / WoR HUD mod: session handoff (2026-10-05)

Start here when you continue this work in a new session. The full history is in
`C:\Users\rockb\mods\ghwt-bg-shader\MODLOG.md` (latest sections: v0.27-v0.30).

## Where things stand

- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`. The config is
  `C:\Users\rockb\OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini`
  (`HUDTheme=ghwor_nomsg`, `GemTheme=ghwor`, 2560x1080, `Preferred{Guitarist,Bassist}Highway=GH5_Highway` for testing,
  DOFBlur 3.5).
- **Mod:** `C:\Users\rockb\mods\ghwt-wor-hud`.
  - `python build.py` builds; `--install` installs `DATA\MODS\WoR_HUD` (+ NoMessages, DarkMetal) and
    `DATA\PAK\hud_ghwor.pak.xen` + `DATA\PAK\gems_ghwor_hud.pak.xen` (WoR highway border); `--package` writes the
    Nexus drop-in zips to `dist\`.
  - `python tests\run_offline.py`: 24/24 pass.
  - Mock: `tools\preview_hud.py <base.png> <out.png> <health> <sp> <mult> --game`. For the layout use the base
    `verify\_bm_tmp\bgame.png`: it draws the WoR border where the game actually puts it (inner edges 396.7 / 883.3 at
    y 638 for BORDER_OFFSET 17.4). In-game shots are 2560x1080: resize to 1280x720 to compare with the canvas.
- **Installed (2026-10-05):** HUD v0.30, not yet tested in game. User-approved layout as of v0.29 (meters
  "perfect"): border 12 px closer (BORDER_OFFSET 17.4), RAIL_OUTSET (-11.4, 13.7), STAR_NUM_K 0.78, SP slanted
  partial cut (SP_SLANT_DEG 8.3), SP 50% ends at the needle (SP_FILL_SPLIT). v0.30 adds HUD outer shadows (option B)
  and a 48 px soft black ball behind each tube's curled end (WoR `circle_gradient_smooth_64` tinted black).
- **Shaders:** ReShade preset `GHWoR.ini` now matches the original WoR preset (desktop rar): SSDO (full res,
  pSSDOLOD=1) with its `ssdonoise.png`, Bloom, SurfaceBlur, vort_MotionBlur, AdaptiveTonemapper, AdaptiveTint,
  Curves, GH5_Grade, Vibrance. Downloaded shaders live in `reshade-shaders\Shaders\vort` and `\Daodan`.
  Background-only add-on rebuilt as "Background-only shaders" (debug tooling off unless `[GHWT_BGFX] Debug=1`).
  Backups: `ghwt-bg-shader\backups\`.

## Shipping (Nexus, drop-in like CLEO mods: extract into the game folder, no scripts, no ini edits)

1. **Main file, GH5/WoR HUD:** `DATA\MODS\WoR_HUD\` + `DATA\PAK\hud_ghwor.pak.xen` + `DATA\PAK\gems_ghwor_hud.pak.xen`.
   The WoR border needs GemTheme=ghwor (it rides in the WoR gem pak copy).
2. **Optional, Background-only shaders:** `ghwt_bgfx.addon32` + `reshade-shaders\Shaders\GH5_Grade.fx`. Release build
   done (2026-10-05); package step still to update for the new name.
3. **Optional, HUD fixes (not started):** `.asi` plugin for Ultimate ASI Loader (see open items).

**Enable/disable switches: skipped for now (user, 2026-10-04).** Revisit with a WTDE build.

## Rules you set

- Ask before every game launch, and batch changes into one build.
- Mock first: show the mock and get approval before applying a layout or setting.
- Use only textures and fonts extracted from the games. Cropping, tinting, flipping and compositing are fine.
- The HUD draws above the highway.
- Prefer targeted fixes on the current build over rewrites.
- Screenshot collector (`tests\collect_session.py`): start it only when the user asks, detached (no task
  notifications); it exits when the game does.

## Open items (all need the native plugin unless noted; details in PLUGIN_NOTES.md)

1. **2nd-song streak lights:** the DE script `hud_widgets` hard-codes the bulb texture names
   (`HUD_score_light_*`). Our HUD and gem paks stay on their pak-manager maps between songs, while `z_in_game`
   reloads every song after them, so its stock lights win the name lookup. Theme tables have no per-song callback
   (checked 2026-10-05). Fix: a plugin that re-registers our textures after `z_in_game`, or redirects the lookup.
2. **SP partial fill at 25/75%:** the DE scales each segment's height, which squashes the slanted cut. The plugin
   could draw a shaped fill.
3. x1 pink streak lights, score thousands commas, SP activation look (no footage).
4. Verify v0.30 in game (shadows, tube balls) and the new shader stack (ReShade.log: all effects compile?).
5. Helper Pill theme, Menu Popup (later).
