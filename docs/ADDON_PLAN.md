# Guitar Hero World Tour: Definitive Edition — background-only shader plan

**Idea:** the ReShade preset runs **only during song gameplay and cutscenes**, and touches **only the
background** (the venue, band, crowd and lighting). It never touches the HUD: note highway, gems, score, rock
meter, star power, lyrics, popups or the pause menu. Menus stay clean.

## Recon (2026-10-02)
- **Install:** `D:\Games\Guitar Hero World Tour`, standalone (not in a store library). GHWT:DE **1.4.3.5** (updated
  today), updater v4.1.
- **Engine:** Neversoft engine (Aspyr's 2009 PC port), **native x86, Direct3D 9** (`Direct3DCreate9`,
  window class `AspyrGH3`). The game runs through `GHWT_Definitive.exe`. The launcher is .NET; that's why
  `um scan` mislabels the whole game as ".NET application", so ignore its Harmony/BepInEx route.
- **Anti-cheat / online:** none found. GHWT:DE has online lobbies (`online_lobby_wtde`) but no anti-cheat. The
  mod is visual-only and has no gameplay effect.
- **Already installed:** **ReShade 6.8.0.2157, 32-bit, as `d3d9.dll`**.
  - It's the **standard build**. Its binary contains the string "only limited add-on functionality is
    available", so it **refuses third-party add-ons**.
  - Active preset: `GHWoR.ini` (SSDO → PD80 Bloom → SurfaceBlur → AdaptiveTonemapper → Curves → Vibrance).
  - Log warnings: `vort_MotionBlur.fx`, `AdaptiveTint.fx` and `RadiantGI.fx` aren't installed, and
    `ssdonoise.png` (needed by SSDO) is missing.
- **Back buffer:** 2560×1080 X8R8G8B8. `EnableAutoDepthStencil=FALSE`, so the game makes its own depth surface,
  and SSDO only works if ReShade's generic depth finds it.
- **Config / logs:** `ReShade.ini`, `ReShade.log`, `GHWTDE.ini`, `debug.txt` (GHWT:DE script log).
  Saves/profile: `DATA\MEMCARD`.
- **Toolchain:** Visual Studio Community 2026 and Build Tools 2019/2022 can build x86 `.addon32`.
- **Knowledge base:** no field notes for Guitar Hero, the Neversoft engine or D3D9 HUD masking. We'd be first.

## Prior art
| Option | D3D9 32-bit? | Notes |
|---|---|---|
| `UIMask.fx` (already installed) | yes | A static hand-painted mask. Wrong tool: the highway moves, is perspective-skewed and translucent, and the HUD changes per mode and instrument. |
| REST, upstream [4lex4nder](https://github.com/4lex4nder/ReshadeEffectShaderToggler) v1.3.23 | **no** (D3D10/11 only) | The established "render effects before shader X" add-on. |
| REST, [Pav-Osmolski fork](https://github.com/Pav-Osmolski/ReshadeEffectShaderToggler) v1.7.1 (2026-09-30) | 32-bit, but D3D10+ | Auto scene colour isn't available on D3D9. |
| REST, [facboy fork](https://github.com/facboy/ReshadeEffectShaderToggler) | **yes, `addon32`** | Adds D3D9 surface back buffers and device-reset safety. **No releases** (we'd build from source), 0 stars, 2 weeks old. Also has no game-state gating. |

**Conclusion:** no existing add-on does both "before the HUD" *and* "only in gameplay/cutscenes" on D3D9. The
facboy fork is useful as a *shader-hunting tool* during recon, but the shipped mod should be our own small
add-on.

## Chosen route: a custom ReShade add-on (`ghwt_bgfx.addon32`)
This is the native-hooks route, but ReShade's add-on API does the D3D9 hooking for us, so no MinHook and no
signature scans.

**How "background only" works: inject before the HUD rather than redrawing the HUD.**
Neversoft renders the 3D scene first (venue, band, crowd, lights) and draws the 2D/overlay layer last
(highway, gems, HUD, lyrics). The add-on:
1. stops ReShade from applying the preset at the end of the frame;
2. watches the draw stream, and at the **first HUD draw of the frame** calls
   `effect_runtime::render_effects()` on the current back-buffer RTV, so the preset runs on a back buffer that
   holds only the background;
3. lets the game draw the HUD on top, untouched.

This *is* "the HUD on top of the shaded background", without duplicating or re-rendering the HUD: we change
*when* the effects run, not what the game draws. It's cheaper than redrawing the HUD, has no extra latency and
can't fall out of sync.

**Gating to gameplay and cutscenes only:** classify every frame from its own draw stream, using signatures
measured in Phase 1:
- **Song gameplay:** highway/gem shaders are present.
- **Cutscene:** venue/band 3D pass present, no highway, no menu-UI shaders.
- **Menus, song select, loading, results:** none of the above, so skip the preset.

Add a few frames of hysteresis so a stray frame can't make it flicker. If the draw signatures turn out
ambiguous, the fallback gate reads GHWT:DE's game state (QB script globals, from memory) instead.

**Plan B (only if Phase 1 shows the HUD interleaved with the scene,** e.g. crowd particles drawn after the
highway, or a game bloom pass after the HUD): redirect the HUD draws into an offscreen RGBA target, run the
preset on the full back buffer, then composite the HUD target on top. That's your "replicate the HUD on top"
idea done literally. It costs more, so only if Plan A can't work.

## Phases
0. **Prerequisites** (each needs your approval: it touches the game folder and downloads files)
   - Snapshot the current state: `um backup create` on `d3d9.dll`, `ReShade.ini`, `GHWoR.ini`, `GHWTDE.ini`
     and `DATA\MEMCARD`.
   - Swap `d3d9.dll` for **ReShade 6.8.0, 32-bit, with full add-on support** (reshade.me). The preset and
     shaders stay as they are.
   - Fetch the ReShade add-on headers (`crosire/reshade` `include/`, tag v6.8.0) into this folder.
1. **Instrument (source of truth):** a tiny `ghwt_framelog.addon32`. A hotkey dumps one frame's draw list to
   CSV: order, VS/PS hash, render target, Z-enable/Z-write, alpha blend, viewport, primitive count.
   - Capture each state: main menu, song select, loading, **guitar gameplay**, **band gameplay**, pause, a
     **venue intro/encore cutscene**, a **career cutscene**, results.
   - Derive (a) the HUD-start boundary and (b) the per-state signatures. Record them in MODLOG.md.
2. **Vertical slice:** in gameplay only, render one obvious effect (Vibrance turned way up) at the HUD
   boundary.
   - Pass: a screenshot shows the venue saturated while the highway and gems keep their stock colours.
3. **Gate:** add cutscenes, exclude every menu state, add hysteresis. Verify each state from Phase 1 with a
   screenshot.
4. **Full preset:** restore `GHWoR.ini`.
   - Install the missing effects and `ssdonoise.png`, or drop them from the preset.
   - Check that SSDO gets real depth (`DisplayDepth.fx`).
   - Check device-reset safety: alt-tab, and the windowed/fullscreen toggle.
5. **Package and record:** README, `um publish check` (no game files), a short before/after clip
   (showcase-video skill), and a field note (`um kb new`).

## Packaging: one drop-in mod, two DLLs (decided 2026-10-02)
The user sees a single zip extracted over the game folder:
`d3d9.dll` (unmodified ReShade 6.8.0 32-bit, full add-on build), `ghwt_bgfx.addon32`, `ghwt_bgfx.ini`,
`ReShade.ini`, the preset `GHWT_BGFX.ini`, and a trimmed `reshade-shaders\` holding only what the preset
uses. An optional `install.ps1` backs up any existing ReShade files first.
- **One add-on.** The Phase 1 frame logger is a debug mode inside `ghwt_bgfx.addon32` (enabled from the INI,
  triggered by a hotkey), not a separate add-on.
- **Rejected options:**
  - A ReShade fork with our code compiled in: we'd own a fork and re-merge on every ReShade release.
  - Our own d3d9 proxy without ReShade: we'd rewrite every effect in the preset by hand.
  - A GHWT:DE `DATA\MODS` mod: it can't reach the D3D9 pipeline.
- **Sharing (if ever):** ship the add-on and preset only, plus a README listing the shader packs to install.
  The third-party `.fx` files have their own licenses.
- **To verify:** does the GHWT:DE updater's integrity check leave `d3d9.dll` and the add-on files alone?

## Done when
In a real session, screenshots show:
- **Gameplay** (guitar and band): preset on the venue; highway, gems and HUD stock.
- **Cutscene:** preset on.
- **Menus, song select, loading, pause, results:** preset off.
- **Alt-tab and resolution change:** no crash.

## Unknowns to resolve first
1. ~~Does `render_effects()` work mid-frame?~~ **Resolved:** yes, it is designed for this and suppresses the end-of-frame pass (see MODLOG, Phase 0).
2. Is the HUD a clean tail of the frame (Plan A), or interleaved with scene draws (Plan B)? Phase 1 answers
   this.
3. Do cutscenes have a draw signature distinct from the 3D backdrops behind menus, if any menus have one?
4. Does the game render the scene into an offscreen target and then copy it to the back buffer? If so, inject
   on that target instead.
5. Does ReShade's generic depth find a usable depth buffer, given `EnableAutoDepthStencil=FALSE`?

## Lab
- **Backups:** `um backup` as in Phase 0. The 1.4.3.5 update backup is already at `_backup_2026-10-02`.
- **Windowed borderless:** already set (`GHWTDE.ini`: `WindowedMode=1`, `Borderless=1`), so screenshots are
  stable.
- **Build output:** `build\` in this folder. Copy only the `.addon32` into the game folder. No game files
  enter this repo.

## WoR presentation tracks (added 2026-10-02, at the user's request)
The user wants the game to look like real Warriors of Rock on Xbox 360: the picture, the HUD, and the highway
and gems. They pointed to the GH3 "Warriors of Rock" mod (Inventor211 et al., 2017) as a source of assets and
logic. They also noted GH5/WoR changed band-game mechanics, so the GHWT:DE repo may need analysing.

| Track | What GHWT:DE already has | Work |
|---|---|---|
| **Highway and gems** | `PAK\gems_ghwor.pak.xen` and `PAK\highway_ghwor.pak.xen` / `highway_gh5.pak.xen` are built in. The `GemTheme` setting and per-character highways in Create-a-Rocker, or `[Band] Preferred*Highway` in the DE INI. | Mostly settings. Confirm the WoR highway ID, and check strikeline and sustain visuals against WoR footage. |
| **HUD** | A `HUDTheme` system (`hudtheme_load_paks` in `tb.pab.xen`) with themes `hud_ghwt_withtime`, `hud_ghm`, `hud_sh`, `hud_vh` plus `hud_shared_assets`. **No WoR/GH5 theme.** | New `hud_ghwor` theme pak, modelled on `hud_vh.pak.xen`'s structure, registered by a DE script mod (QScript, compiled with GHSDK). Art: rock meter, star power, multiplier, from the GH3 WoR mod, extended for WT's band HUD (band meter, 4 lanes), which GH3 never had. |
| **Picture look** | This add-on (background only, songs only). The `GHWoR` preset is a community imitation (likely Nexus "Gh5-WoR shaders on GHWTDE"). | After the sRGB fix: compare frames against real WoR captures, tune the preset, possibly a LUT (`LUT.fx` is installed). Same-venue captures give the best match. |

**Needs approval before downloading:** GHSDK (gitgud.io/fretworks/guitar-hero-sdk, Node.js, already
installed) and the GH3 WoR mod. Prefer the original release over the linkshrink/Drive mirrors.
**Licensing:** assets from the GH3 WoR mod (and Activision's WoR art inside it) are for the user's own
install only. Don't redistribute without the authors' permission, and credit Inventor211 and team.

## WoR as a selectable style in every DE option that offers GH styles (survey 2026-10-03)
Source: options menu struct `f26e4c1f` (`0x5c2f930d.qb`), choice lists in `0xbb76de6b.qb`, consumers found
by searching every `tb` script for each option's global.

| Option (INI key) | WoR today | How the value is used | WoR feasible by mod? |
|---|---|---|---|
| Gem Theme, Hit Flame, Song Intro, SP Activation SFX, Practice Section Style | **built in** | — | — |
| HUD Theme (`HUDTheme`) | no | theme table `0x8ef7f1be` + classic check `af530ac6` | **yes, in progress** (stage 1 installed) |
| Load Screen (`LoadingTheme`) | no | data table `0x613f868c` in `loading_screen.qb`: movie + image names per style | **yes, easiest**: one table row + WoR loading art/movie |
| Pause Menu Theme (`PauseTheme`) | no | `if` chain in `ui_pausemenu` layout (separate builder per style) + `guitar_menu` sounds/textures | yes: override those scripts + WoR pause UI art |
| Menu Popup Theme (`MenuPopupTheme`) | no | `switch` in `menu_popup.qb` (6 places) | yes: override + WoR popup art |
| Helper Pill Theme (`HelperPillTheme`) | no | `guitar_menu` returns the value; probably names the pill textures | likely: WoR helper-pill art |
| Tap Trail (`TapTrailTheme`) | no | `if` in `highway_2d.qb` (builds trail texture list) | yes: override + WoR tap-trail textures |
| Note Streak Alert SFX (`NoteStreakSFX`) | no | `if` chain in `guitar_hud_2d.qb` | yes: override + WoR streak sounds (FSB) |
| Star Power Awarded SFX (`StarPowerEarnedSFX`) | no | `switch` in `global_sound_logic`, `guitar_battle`, `guitar_events` | yes: overrides in 3 scripts + WoR SP sounds |
| Facial / Guitar Strum / Bass Strum anim | no | lookup by name (`facial`, `strum`) in `guitar_character.qb` | risky: needs WoR animations retargeted to WT skeletons |
| Flare Style (`FlareStyle`) | no | **read natively by GHWTDE.dll** (no script reads it) | **no**: needs Fretworks to change the DLL |
| Battle Mode Icon Theme (`AttackIconTheme`) | no | battle scripts | **n/a**: WoR has no Battle mode |
| HUD: Star Meter Color on FC | — | on/off toggle, not a style list (my survey regex matched a shared list) | n/a |

**Cost of script overrides:** overriding a DE script copies its full source into the mod. A DE update that
changes that script would be silently reverted while the mod is installed. Keep overrides minimal (only the
branching function), and re-diff against each new `tb.pab` after updates.

## Packaging decision: "Warriors of Rock" total conversion (user, 2026-10-03)
Scope: only the options WoR **can be added to by our mod** (HUD Theme, Load Screen, Pause Menu, Menu Popup,
Helper Pill, Tap Trail, Note Streak SFX, SP Awarded SFX). Animations, Flare Style and Battle icons are out.
- **One package, three layers:** script mod `DATA\MODS\WoR_Conversion\` (all option entries + minimal
  overrides); WoR theme paks (`DATA\PAK\` unless the DE can load them from the mod folder: to test);
  shader (ReShade `d3d9.dll` + `ghwt_bgfx.addon32` + WoR preset + used shaders, in the game root).
- **`install.ps1`:** backs up replaced files and the current `GHWTDE.ini`; sets every WoR-capable option to
  WoR, including the built-in five (GemTheme, HitFlameTheme, SongIntroStyle, SPActivationSFX,
  TrainingSectionFont). **`uninstall.ps1`:** restores both.
- Each option stays individually selectable in the DE menus; the shader stays toggleable in the overlay.
- Personal use: WoR assets come from the user's own disc. A shareable version must build them from the
  installer's own WoR copy (the extract → x360img → repack pipeline) and ship no Activision files.
- Order: confirm HUD stage 1 → real WoR HUD → Load Screen → Pause/Popup → SFX → Tap Trail/Helper Pills →
  merge into `WoR_Conversion` → installer/uninstaller → updater check.

## Native GHWT:DE format (user, 2026-10-03): replaces the "total conversion installer" idea
The user wants the mod in a form WTDE recognizes natively, not an installer.

**What the DE natively supports** (from GHWTDE.dll strings; the wiki documents only some of it):
- Mod types, detected by ini in each `DATA\MODS` folder: `song.ini`, `character.ini`, `highway.ini`,
  `instrument.ini`, `menumusic.ini`, `category.ini`, **`gems.ini`** (`[GemInfo] Name/Filename`; loads
  `Content\<file>.pak.xen` + `.qb` and registers the theme), `venue.ini`, `folder.ini`, and **`Mod.ini` =
  script mod** (loads every `.qb` / `.qb.xen` in the folder and calls `<Folder>_Load`).
- Pak redirects to a mod's `Content` folder exist **only** for venue / highway / gem mods ("Venue/Highway/Gem
  pak matches"). There is no HUD / loading / pause-theme mod type.
- **Image handler script functions:** `IH_AddImage id= path= category=` (file `<path>\<id>.img.xen` or
  `<path>\IMAGES\<id>.img.xen`), `IH_LoadImage id=|category=`, `IH_UnloadImage id=|category=`. The DE uses
  them for helper pics and character icons.

**Design: one native script mod, no files outside `DATA\MODS` except ReShade's own two:**
```
DATA\MODS\Warriors of Rock\
  Mod.ini                       [ModInfo] (native script mod)
  WoR.qb                        WoR_Load: adds "Guitar Hero: Warriors of Rock" to HUD Theme, Load Screen,
                                Pause Menu, Menu Popup, Helper Pill, Tap Trail, Note Streak SFX, SP Awarded SFX;
                                theme-table rows; minimal overrides of the branching scripts; the HUD
                                layouts themselves as QB sections; IH_AddImage registration of all textures.
  IMAGES\*.img.xen              WoR textures (from x360img PNGs -> PC .img via GHSDK PNGtoIMG / DDStoIMG)
  ReShade\ghwt_bgfx.addon32, WoR preset, Shaders\, Textures\
<game root>\d3d9.dll + ReShade.ini   (the only non-native part: ReShade must sit next to the exe; its
                                      [ADDON] AddonPath / EffectSearchPaths / TextureSearchPaths / PresetPath
                                      point into the mod folder)
```
- Theme textures are loaded with `IH_LoadImage category=wor_hud` when the WoR theme is active and unloaded
  with `IH_UnloadImage category=wor_hud`, so no pak is needed (the stock WT theme has no pak either).
- Sounds (two SFX options) are the open question: there is no sound loader equivalent to IH_*. Options: a
  `menumusic`-style FSB, or reusing sounds already in the DE. To investigate.

**Must verify in game before building on it:**
1. Stage 1 (installed): the `$change$` on the theme table and menu list works, and the redefined `af530ac6`
   overrides the original.
2. `IH_AddImage` with a path inside `DATA\MODS\...`: is the path relative to the game folder, `DATA`, or
   absolute?
3. ReShade `[ADDON] AddonPath` pointing into the mod folder.
