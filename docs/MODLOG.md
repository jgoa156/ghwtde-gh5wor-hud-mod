# MODLOG — GHWT:DE background-only shader

## 2026-10-02
- Installed the universal-modder 0.2.0 plugin (user scope). `um` runs on system Python 3.13 (no `uv`); I
  pip-installed pillow, numpy and pyyaml.
- `um scan "D:/Games/Guitar Hero World Tour"` mislabels the engine as ".NET" because it keys on
  `GHWT_Definitive_Launcher.exe`. The real game is native x86 D3D9. Worth a note upstream.
- `um kb search` for "guitar hero" and for HUD/post-process: nothing.
- ReShade 6.8.0 32-bit standard build is installed as `d3d9.dll`. It has limited add-on functionality, so it
  needs the full add-on build before any custom `.addon32` will load.
- Preset `GHWoR.ini` references effects that aren't installed: vort_MotionBlur, AdaptiveTint, RadiantGI.
  `ssdonoise.png` is also missing.
- Route chosen: a custom ReShade add-on that runs `render_effects` at the HUD boundary, gated per frame on
  draw signatures. See MODDING_PLAN.md.
- Packaging decided: one drop-in zip. ReShade `d3d9.dll` plus a single `ghwt_bgfx.addon32`; the frame
  logger becomes its debug mode (see MODDING_PLAN.md, Packaging).

### Phase 0 (approved, done)
- Snapshots:
  - `um backup` **ghwt-reshade-orig** (`20261002-202656.zip`, 84 files): standard `d3d9.dll`, the INIs and
    `reshade-shaders\`.
  - `um backup` **ghwt-saves** (`20261002-202658.zip`): `DATA\MEMCARD`.
- Swapped `d3d9.dll` for ReShade 6.8.0.2156 32-bit **full add-on** (the `ReShade32.dll` inside
  `ReShade_Setup_6.8.0_Addon.exe` from reshade.me).
  - The setup's signer thumbprint `589690208A5E52FB96980C4A6698F50ACD47C49F` equals the old DLL's. It's
    self-signed, so Windows shows "UnknownError".
  - PE machine 0x14C (x86). No "limited add-on" string.
- Headers: `deps/reshade` = crosire/reshade tag v6.8.0 (`18deaa5`), sparse checkout of `include/`.
- **Unknown #1 resolved:** `effect_runtime::render_effects(cmd, rtv, rtv_srgb)` is documented to "prevent
  the usual rendering of effects before swap chain presentation of the current frame". It exists precisely
  to keep effects off UI.
  - With `rtv = 0` it renders nothing but still updates uniforms, so menu frames call it with 0.
  - It may clobber pipeline and render-target state, so save and restore D3D9 state around it.
- **Boot check (20:30):** launched `GHWT_Definitive.exe` directly (PID 37168).
  - `ReShade.log` shows 6.8.0.2156 loaded and the add-on search ran. No limited-add-on message. The only
    error is the known missing `ssdonoise.png`.
  - The process kept responding, then was closed by PID.
- **Gotcha:** the game minimizes itself when it isn't the foreground window (rect at -32000), so a
  screen-copy capture comes out blank.
  - `um win shot` needs `um win setup` (it downloads ffmpeg with gfxcapture), which isn't approved yet.
  - Better for Phase 1: have the add-on save the back buffer itself (ReShade API), which needs no focus and
    no ffmpeg.
- **Next:** Phase 1, build `ghwt_bgfx.addon32` with the frame-dump debug mode.

### Phase 1: tooling built and verified (20:45)
- `src/ghwt_bgfx.cpp` builds with `build.bat` (VS 2026, x86, /MT, W4 clean) to `build/ghwt_bgfx.addon32`
  (192 KB). It exports NAME and DESCRIPTION and imports only KERNEL32.
- Installed to the game folder. `ReShade.log` shows: `Registered add-on "GHWT BGFX" ... API version 20`.
- Features:
  - F10 / overlay button / trigger file `ghwt_bgfx_dump.trigger` dumps one frame to
    `<game>\ghwt_bgfx_dumps\<stamp>\`: `draws.csv`, segment snapshots, `final_game.bmp` (before
    effects) and `final_shown.bmp` (after).
  - F9 scrub mode runs `render_effects` before draw N (PgUp/PgDn, Shift x25).
  - The trigger file works with the game in the background. It minimizes when it isn't the foreground
    window but keeps presenting.
- Verified on D3D9: the `present` event fires before ReShade's effects (`d3d9_swapchain.cpp` on_present), so
  `final_game.bmp` is the game's own frame.

### First dump: title screen ("Press any button to rock"), 22 draws
- **Render structure:**
  - Draws 0–10 go to off-screen full-resolution targets rt0–rt3 (format 21 = A8R8G8B8; rt3 has a depth
    buffer). That's the scene path.
  - **Draw 11 composites onto the back buffer** (rt4, format 22 = X8R8G8B8): PS `DE796938`, a 4-vertex
    full-screen quad.
  - **Draws 12–21 are 2D UI on the back buffer:** PS `2393BA2D` / VS `4A1D3EAB`, alpha blend on, alpha test
    on, src/dst blend 5/6 (SRCALPHA/INVSRCALPHA).
- On the title screen the scene targets are black, so everything visible is UI. `final_shown` confirms the
  preset recolours the logo and text.
- **Plan A looks viable:** the scene reaches the back buffer in one composite draw, and UI is drawn after
  it. Candidate injection point: right after the back-buffer composite (PS `DE796938`), before the first UI
  draw.
- **Candidate gate signal:** whether the scene path drew real geometry (title screen: almost nothing).
  Gameplay and cutscene dumps are needed to confirm.

## Restore path
- Before the 1.4.3.5 update: `D:\Games\Guitar Hero World Tour\_backup_2026-10-02\`
- ReShade/preset: `um backup restore ghwt-reshade-orig --to "D:\Games\Guitar Hero World Tour"`
- Saves: `um backup restore ghwt-saves`

### Auto mode, experimental (20:50)
- Effects are injected before the first draw after the back-buffer composite (PS `DE796938`). Frames
  without a composite call `render_effects` with a zero view, so nothing is applied.
- Settings in ReShade.ini `[GHWT_BGFX]`: `Auto=1`, `CompositePS=DE796938`. Toggle in the overlay.
- Dump `20261002-205104` (loading screen, 166 draws): `injected_at=149`. The post-composite overlay
  ("LOADING..." text, controller pill; PS `2393BA2D`) is clean.
- **But menu art lives in the scene path:** 57 draws with PS `54A68A15` go into rt0 before the composite.
  The board frame still gets recoloured.
  - So Auto alone can't keep menus clean. The gameplay/cutscene gate is required, as planned.
- Loading-screen depth stats: 62 draws with Z-write on, 85 Z-test only, 18 on the back buffer. A
  depth-write count doesn't obviously separate menus from gameplay yet.
- **Waiting on:** user F10 dumps of song gameplay (highway visible), a cutscene, pause and the main menu.

### First gameplay frame (dump 20261002-205715, 519 draws). User: "it works", but the background is darker.
- **Frame structure:**
  - 0–22: 1024² target (shadow/reflection).
  - 24–239: venue/band/crowd into scene target rt2 (Z on).
  - 240–364: four 480² sub-scenes composited into rt2 (PS `850F299B`).
  - 365–375: particles (PS `35182797`).
  - 376–390: the game's own post chain (PS `E5555C99`, `A97C8968`, `50887166` blur, `E1B11BA9`,
    `2D87CE2B`).
  - **391: composite to the back buffer (PS `DE796938`).**
  - **392–518: highway, gems and HUD on the back buffer** (PS `FE74FFEA`, `12827EBF`, `5DBF7AEB`,
    `E39C7998`, `86C2E6EF`, `E349266C`, `A43CA4E5`, plus UI `2393BA2D`; some with Z-write).
- The highway really is drawn after the composite, so Auto keeps it clean. Confirmed by the user in game.
- **Gate idea:** gameplay frames contain the highway shaders after the composite. Cutscenes should have the
  scene + post chain without them. Menus need their own signature: the title and loading screens also run
  `E1B11BA9`/`A97C8968`/`50887166`, so "post chain ran" alone is not enough.
- **Read-backs all failed** in this dump, though `final_shown` (ReShade capture) worked. Probably the device
  was lost: the game created its device with `Windowed=FALSE`, and the user was alt-tabbed to chat. TODO:
  log the HRESULT.
- **Darkening root cause (fixed in code, 20:58):** `render_effects(rtv, rtv_srgb)` got the plain view for
  both. On D3D9, ReShade marks the sRGB view with bit 0 of the surface handle (`d3d9_impl_device.cpp`
  550–581). `PPFX_SSDO.fx` and `AdaptiveTonemapper.fx` have `SRGBWriteEnable = true`, so they wrote linear
  values: darker. Fix: pass `{bb.handle | 1}` as `rtv_srgb`.

### sRGB fix confirmed by the user ("works perfectly"). Remaining issue: song select gets the preset (21:15)
- Dump `20261002-211548` (song select, 469 draws): menu art is drawn through the **same scene path**
  (PS `54A68A15`, `B94C7F19`, `E7D2F58B`, `31668FBC`, ...) + the post chain + composite `DE796938`, then 354
  UI draws.
- Pixel shaders seen only in gameplay (vs. song select, loading, title): `E5555C99` (venue post-chain entry),
  `850F299B` (sub-scene composite), venue/character PS (`E494FF3D`, `2EFB321B`, ...), highway
  (`FE74FFEA`, `12827EBF`, `5DBF7AEB`, ...).
- **Gate implemented (21:16 build, not installed yet):** inject only when `ScenePS` {E5555C99, 850F299B} was
  bound this frame (it runs before the composite, so it's a same-frame decision), or `GameplayPS` was seen
  in the last `GameplayHoldFrames` (30) frames. Otherwise `render_effects` with a zero view.
  - INI: `Gate`, `ScenePS`, `GameplayPS`, `GameplayHoldFrames`.
  - **Unverified:** cutscenes (expected to pass via the venue renderer), and Create-a-Rocker / other menus
    with 3D characters.
- **PR to WTDE:** `fretworks/ghwt-de-volatile` is a distribution repo (compiled zips + hashlist, 0 MRs ever).
  The HUD theme list is compiled into `tb.pab.xen`; no public script source. Public tooling: guitar-hero-sdk,
  noderoq, nodeqbc, nxtools, ghwt-ida.
  - So: build the WoR HUD as a DE mod first, then offer it to Fretworks (Discord) for official inclusion.

### WoR HUD track: groundwork (21:20–21:40)
- The gated add-on build is installed (PID 46208). The user confirmed the sRGB fix: "works perfectly".
  Gate verification on song select is still pending.
- **Settings check** (the user's real config is
  `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini`):
  - Already WoR: `GemTheme=ghwor`, `HitFlameTheme=wor`.
  - WoR available but not set: `SongIntroStyle` (auto), `SPActivationSFX` (default), `TrainingSectionFont`
    (ghvh).
  - `HUDTheme=ghvh`: no WoR option exists.
  - `WindowedMode=0`, which explains the failed read-backs while the user is alt-tabbed.
- **Tools:** `C:\Users\rockb\mods\tools\guitar-hero-sdk` (GHSDK df55ce7, `npm install` done; `Config/config.ini`
  points at `C:\Users\rockb\mods\ghwt-wor-hud`) and `noderoq` (fd0f94c).
  - `tools/img2png.js` converts `.img.xen` to PNG through GHSDK's TexHandler. GHSDK parses argv when
    loaded, so the script hides its own argv.
- **GHWT:DE HUD theme system** (from `tb.pak.xen`, extracted to `C:\Users\rockb\ghwt-extract\tb`):
  - Theme table: struct `0x8ef7f1be` in `0x29ebe78e.qb.xen`. Members: `0x09982fd5` ghwt, `0x90737ab7`
    ghwt_plus (pak `hud_ghwt_withtime`), `d3010702` ghm, `0x79f5b69e` ghsh, `0x048242db` ghvh.
    - Each member has: `pak`, gamertag texture, a layout per player config (`hud_1g`, `hud_2g`, `hud_1v`,
      `hud_1g1v`, `hud_2g1v`, `hud_3g1v`), vocal highway settings, and script hooks (band meter,
      multiplier texture, star meter text, ...).
  - Menu choices: array `0x1f644846` in `0xbb76de6b.qb.xen` (`{Title, value, value_string}`). Option entry
    "HUD Theme": `variable = 0x12ad2474`, INI key `HUDTheme`.
  - **Plan:** a DE script mod `<Folder>_Load` that (1) adds member `ghwor` to `0x8ef7f1be`, (2) appends
    `{Title "Guitar Hero: Warriors of Rock", value ghwor, value_string "ghwor"}` to `0x1f644846`, and (3)
    ships `hud_ghwor.pak.xen`, modelled on `hud_vh` (133 files: 114 images + QB layouts, hashed names).
- **GH3 WoR mod** (Inventor211 et al.):
  - Original: MediaFire `GH3PC_-_WoR_Mod_Installer.7z`, 404,225,019 bytes, sha256 `b0aae371…5020`.
  - Defender CLI unavailable (hr 0x800106ba). No executables were run or extracted.
  - Only `DATA\ZONES\global.pak/.pab` and `DATA\PAK\qb.pak/.pab` were extracted, to
    `C:\Users\rockb\ghwt-extract\gh3wor`. 624 global images converted to `global_png`.
  - Its WoR art sits on GH3 texture names: `HUD_score_body` (score/SP bar with star cap), `HUD_rock_body` +
    `HUD_rock_BG_*` + `HUD_rock_lights_*` (slanted WoR rock tube), `HUD_counter_body` (streak frame), plus
    lightning FX.
  - **Not in the mod:** WoR's gear multiplier, and anything band-specific (GH3 has no band meter).
- Contact sheets: `shots/gh3wor_hud_sheet.png`, `shots/gh3wor_hud_closeup.png`, `shots/hud_vh_sheet.png`.

### Real WoR HUD art from the user's Xbox 360 copy (2026-10-03)
- Copied `Hdd1/Jogos/Guitar Hero - Warriors of Rock` over FTP to `E:\Guitar Hero - Warriors of Rock`
  (1353 files, 5.94 GB, 0 failures) with `tools/xbox_pull.py` (resumable; login from env vars). Gotchas:
  Git Bash rewrote the leading `/Hdd1/...` (use `MSYS_NO_PATHCONV=1`), and this FTP server needs `CWD` then
  `LIST`/`RETR` by name; `LIST <path>` returns the wrong folder.
- Extracted with GHSDK (X360 paks decompile fine) into `C:\Users\rockb\ghwor-extract` (outside the repo):
  - `ZONES/z_in_game.pak.xen` (132 files, 99 images) holds **the in-game HUD art**: band multiplier bulbs
    and numbers 1–11 (nixie style), `band_HUD_gold/silver_star_*`, career star holder, SP tubes
    (`SB_*`, `SP_*`, `RM_*_Glow01`), combo LED meter, battle meters, vocal HUD, `x2..x8` text, demigod
    meter, progression bars, lyric bars.
  - `PAK/ui_shared.pak.xen`: band extras (`hud_amb_*`, revive meter, `band_hud_guitar2`/`microphone2`).
  - `PAK/qb.pak.xen`: 1383 script files incl. `scripts/guitar/hud/hud_widgets.qb.xen` and
    `hud_layouts.qb.xen` (WoR HUD logic: `AttachHudWidget`, `HUD_attach_widget_band_multiplier`,
    `..._sidebar_starpowermeter`, `..._band_rock_meter`).
- Converted PNGs: `z_in_game_png` (99), `ui_shared_png` (344). Contact sheets in `shots/`.
  - **Known issue:** ~8 images in the sheet decode as blue noise (probably an unsupported 360 texture format
    in GHSDK's converter): `lil_plus`, `little_neck`, `lyric_bg_*`, `lyric_stripe_*`, `outline*`,
    `snakehead02`. Not needed for the main HUD so far.
- Note: this is Activision's art from the user's own disc. For the user's install only; do not publish.

### WoR HUD search redone (2026-10-03)
- **Missed last time:** `ZONES/z_in_game.pak.xen` also holds `ui/uidesc_*.qb.xen`, the **WoR HUD layouts**
  (29 files): `hud_standard` (+ `_1p`, `_1v`, `_1g1v`), `hud_sidebar_rockmeter`,
  `hud_sidebar_starpowermeter`, `hud_meter_combo`, `hud_scores_stack`, `star_meter`,
  `career_star_meter(_stripped)`, `hud_revive_band_meter`, `hud_band_battle/versus`, `vocals_highway`, and
  the Warriors power widgets `rp_axel_ankh` (the ankhs in the user's reference screenshot),
  `rp_casey_meter/widget`, `rp_johnny_timer`. Decompiled to `ghwor-extract/uidesc/*.txt`.
- They reference 102 textures. 99 are in `z_in_game` + `ui_shared`; the rest are `0x00000000` and the
  generic `white`, `gradient_128` (being located by the full catalogue).
- **GHSDK's X360 texture converter is wrong for many WoR textures.** New standalone decoder
  `tools/x360img.py`:
  - Format byte = GPU fetch constant (offset 0x28) byte 35: low 6 bits format, top 2 bits endian.
    Pixels at 0x1000.
  - Adds k_8_8 (`0x4a`), k_8 (`0x02`), 8888, DXT1/3/5, DXN. Untiles with XGAddress2DTiledOffset, plus
    the **packed mip tail** offset for textures under 32 px (Xenia `GetPackedMipOffset`; GHSDK only
    handles width == 16).
  - Validated: pixel-identical to GHSDK on textures GHSDK gets right.
  - Fixes 16 garbled `z_in_game` textures (ankhs, snake head, sidebar mini meter, lyric bars, outlines)
    and **77 of 344 in `ui_shared`** (61 DXT1, 9 8_8, 5 8, 2 DXT5), incl. `rp_johnny_mohawk`,
    `rp_judy_vocals_tube*`, `pr_casey_shield_glow`, `meter_frame01`, `vocals_meter_cap`.
  - Use `*_png2` folders from now on; the GHSDK `*_png` outputs are unreliable for X360.
- Full catalogue of every WoR pak (`tools/catalog_paks.sh` → `ghwor-extract/all/catalog.tsv`) running.
- **Full catalogue done:** 739 paks, 731 extracted, 40,439 files (`ghwor-extract/all/catalog.tsv`).
  - All 102 HUD-layout textures are located: 99 in `z_in_game` + `ui_shared`, plus `white` and
    `gradient_128` in `PAK/global_textures`.
  - No other HUD art elsewhere. The other "meter/multiplier" hits are tutorial illustrations, career map,
    song summary, and GH Mix studio.
  - The 8 failed paks: 6 are empty stubs (motd, temp, testpak, ui_testassets, select_training,
    practicepercussion_kick); 2 are `songstat*` (compressed song stats, GHSDK `ExtractFiles` TypeError).
    None are HUD.

### WoR HUD stage 1: in-game test (2026-10-03 01:00–01:10)
- 1st try: option missing. The DE log said `Searching for .qb files in ...\WoR_HUD... Processing 0 scripts`.
  The wiki tutorial says `<Folder>.qb`, but **the current DE only loads `<Folder>.qb.xen`** (every other
  script mod on the install uses `.qb.xen`). Renamed. Log then shows
  `[0xd8b982c2] WoR_HUD: registering Warriors of Rock HUD theme`, and the user confirms the option appears.
- 2nd try: crash when a song loads. Last log line:
  `CRITICAL: pak 0x408ce8d1 does not exist in pakman links: 0xcbcd0af1`.
  - `0x408ce8d1` = `hud_ghwor`. `hudtheme_load_paks` passes `links = cbcd0af1`, the pak-manager table
    in `scripts/guitar/guitar_character_paks.qb` (rows `{name = "<pak>"}` for hud_ghwt_withtime, hud_ghm,
    hud_sh, hud_vh, hud_shared_assets).
  - **Fix:** the mod now also `$change$`s `cbcd0af1` to a copy with a `hud_ghwor` row. Installed 01:09;
    awaiting the user's song test.
  - Gem themes have a sibling table (`af130dc4`, rows like `gems_ghwor`). Every new loadable pak needs a
    row in the matching links table.
- DE log location: `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\Logs\debug.txt`.
  The game locks it exclusively while running.
- Idea to test later: whether a links-table `name` can be a relative path into the mod folder
  (e.g. `../MODS/...`). That would let the theme pak live inside the mod (native) instead of `DATA\PAK`.

### Harness runs and hard constraints found (2026-10-03 01:15–01:30)
- `ghwt-wor-hud/tests/ingame_smoke.py`: AutoLaunch (bot plays the song) + ghwt_bgfx frame dumps until a
  gameplay frame appears; checks the DE log + the frame; GHWTDE.ini backed up and restored.
  Baseline `--hud ghvh` all PASS.
- **Replacing the pak-links table `cbcd0af1` with `$change$` is a use-after-free.** The pak manager holds
  pointers into the boot-time table, so rows map to the wrong paks: ghvh loaded `hud_ghwor`, ghwor loaded
  `hud_ghwt_withtime`. That explains the user's crashes. Removed.
- **A mod cannot replace or swap an existing script.** A redefined `Script 0x30597914` is ignored, and
  `$change$$[30597914]$ = $NewScript$` runs without error but the original still runs. So `af530ac6` was
  never overridden either.
  - Consequence: options whose WoR support needs an extra branch in a DE script (Pause Menu, Menu
    Popup, Tap Trail, probably Helper Pill) **can't be added by a mod**. Only data-table-driven options can
    (HUD theme table, Load Screen table), and only tables read by scripts, not ones cached natively.
- Clean build installed: only `$change$` of the theme table `8ef7f1be` and menu list `1f644846` (both read by
  scripts each time). The WoR theme has no `pak`; `DATA\PAK\hud_ghwor.pak.xen` removed. Selecting WoR now
  gives an empty HUD until the WoR layouts (QB sections in the mod) + IH_* textures exist.
- User feedback: too many game launches. Ask before each in-game run and batch changes (memory saved).

### v0.3: HUD theme fully inside the mod, plus test suite (2026-10-03 01:30–01:45, no game launches)
- **Build:** `ghwt-wor-hud/build.py` generates `build/WoR_HUD/` from sources on every build.
  - Inputs: the theme table + menu list read fresh from the installed `tb.pak` (no drift possible); the
    WT+ pak's 8 uidesc descs copied and renamed `*_ghwor`; textures registered with `IH_AddImage` (path
    `../MODS/WoR_HUD/IMAGES/<id>`, resolved under `DATA\IMAGES`) + `IH_LoadImage category=WoR_HUD`.
  - The WoR theme row is cloned from WT+ (non-classic family), with no `pak` and layouts
    `WoR_HUD_layout_<cfg>` = `{hud_version=nxgui, desc_interface="<cfg>_ghwor"}`.
  - First WoR art: the score housing (`0x3af04b64`) → WoR `band_HUD_star_score_meter`.
- **Engine rules learned (offline):**
  - A layout's `desc_interface "X"` resolves to the QB struct `uidesc_X`.
  - Theme layout structs live in the always-loaded `scripts/guitar/hud/hud_layouts.qb`; theme paks
    supply only the descs + images.
  - DE loose images are PC `.img.xen` = 40-byte header + DXT5 DDS. `tools/png2img.js` produces them
    (round-trip mean error 0.1–0.2/255).
  - **Compiler pitfall:** `SectionStruct name{` without whitespace before `{` is mis-parsed (no header,
    garbage descversion = 9). Fixed in build.py.
  - Script bytecode is encoded, so strings are not greppable in `.qb.xen`. Verify by decompiling.
- **Guards:** build.py decompiles its own output and fails unless every section (17/17) and every printf
  survives.
- **Offline suite:** `tests/run_offline.py`, **14/14 PASS** (build / safety / integrity / drift / decoder).
- Installed v0.3 to `DATA\MODS\WoR_HUD` (game not launched). Next: one in-game run (`ingame_smoke.py`), with
  the user's OK.

### User test of v0.3 + two new issues (2026-10-03 02:05–02:25)
- User: the HUD shows (World Tour+ look = our copied descs; the log confirms layout `0xdb93bd6b` =
  WoR_HUD_layout_1g, and all 3 mod images were loaded from the mod folder). Two issues reported:
  1. **Fretboard texture missing** (strings, frets, gems visible). Also visible in the user's first gameplay
     screenshot, before the WoR theme existed, so it's probably the ghwt_bgfx add-on, not the HUD mod. In
     gameplay dumps the add-on injects right before the first post-composite draw, PS `86C2E6EF`
     (z-write), which is most likely the fretboard (followed by FE74FFEA strings, 12827EBF gems).
     - Add-on restore aligned with ReShade's own `d3d9_impl_state_block.cpp`: explicit `Capture()`,
       Apply first, then explicit `SRGBWRITEENABLE` + sampler 0 `SRGBTEXTURE`, **all** RT slots (empty
       ones too), depth-stencil, viewport last. Built and installed 02:22 (previous kept as
       `build/ghwt_bgfx.addon32.prev`). Unverified.
     - Decisive test for the user: the overlay → Add-ons → GHWT BGFX → untick Auto during a song.
  2. **Crash while saving a guitar with a custom highway**: the log ends in `cas_text_entry` (name
     entry), no script error, so native. Suspects: ReShade input hooks vs the DE keyboard text entry;
     WoR_HUD unlikely. Isolation steps given to the user.
- Ruled out: the GHVH Skulls highway idea (texture `0xe45bfec0` is a stock DE highway from
  `highway_ghvh_skulls`; the mod doesn't touch highways).

### Fixed (user-confirmed 2026-10-03 ~02:30)
- Fretboard back with the ReShade-aligned state restore; character/guitar saving works again (crash not reproduced).

### WoR look tuning (2026-10-03 02:30–02:40, no game launch)
- User: "way too blurry". Reference: A Wise Moose "GHWoR - Motivation Expert 100% FC", 1080p, sampled in the
  browser pane.
  - Background stats (left/right thirds, upper area; `tools/imgstats.py`, same metrics in-browser): WoR p05
    luma 0.008–0.032 (deep blacks), crisp background (little DOF).
  - User frames: p05 0.044–0.071 (lifted blacks).
- Blur sources: SurfaceBlur (radius 4, strength 0.86; full-frame smear), DE `DOFBlur=6.0`, PD80 Bloom
  sigma 30 / mix 0.5.
- Changes (backups in `backups/*.before-worlook-20261003-023718`):
  - SurfaceBlur removed from Techniques.
  - Bloom mix 0.30, sigma 18, limit 0.45.
  - Curves contrast 0.32.
  - New own shader `shaders/WoR_Look.fx` (CAS-style adaptive sharpen 0.6 + aspect-corrected vignette
    0.25 from 0.55), last in the chain. Installed to `reshade-shaders/Shaders`.
  - GHWTDE.ini `DOFBlur` 6.0 → 2.0.
- Unverified in game: WoR_Look compile + look. Awaiting user feedback.

### Feedback on the look + why the WoR art does not show (2026-10-03 02:45–03:00)
- User: image "low quality and noisy"; WoR art still not showing.
- **Noise:** sharpening 0.6 amplified PD80 dither (strength 2) and SSDO speckle (SSDO runs without
  `ssdonoise.png`). Fix (backup `backups/GHWoR.ini.before-denoise-*`): SSDO removed (WoR has no AO),
  WoR_Look Sharpness 0.25, PD80 dither 0.5.
- **WoR art:** the score box shows neither WT+ 0x3af04b64 nor our WoR swap; only the frame layer is drawn.
  - Root cause: image-handler textures live in their own asset context. The DE only uses them inside
    `$setsearchallassetcontexts$` ... `$setsearchallassetcontexts$ Off` (ui_band_mode,
    guitar_character), and HUD creation never enables it, so HUD sprites can't find IH textures.
    The mod can't wrap the HUD scripts.
  - `hud_ghwt_withtime.pak` is loaded at boot whatever the theme (log lines 6601/6613), so WT+ textures
    are always resolvable.
  - Candidate route: native `ReplaceTexture { src_tex_dict_assetname/assetcontext/texturename,
    dest_... }` (used by `apply_band_logo_to_venue`; hooked by the DE as SafeReplaceTexture). The source
    dict/context for IH images is unknown (DLL string `IHND_%08x` is probably the dict name). Needs an
    in-game experiment.

### Reverted to the user preset (2026-10-03 ~03:05)
- User: keep the downloaded WoR preset, only fix the blur. Restored `GHWoR.ini` from `backups/GHWoR.ini.before-worlook-20261003-023718`; only change: SurfaceBlur removed from Techniques. WoR_Look.fx removed from the game (source kept in `shaders/`). GHWTDE.ini `DOFBlur` stays 2.0 (was 6.0; revert via the DE options or the backup).

### SurfaceBlur kept, softened (2026-10-03 ~03:10)
- User: SurfaceBlur is needed for the look; just reduce it. Back in Techniques at its original spot (after Bloom). BlurStrength 0.858 -> 0.45, BlurRadius 4 -> 3; nothing else differs from the downloaded preset (verified by diff against `backups/GHWoR.ini.before-worlook-*`). Backup: `backups/GHWoR.ini.before-softblur-*`. Adjustable live in the ReShade overlay.

### Look check vs GH5 13th Rail + v0.4 (2026-10-03 ~03:15)
- GH5 reference (user link, Rhythm FY "Song 2", 720p, clean capture), 8 frames, background regions:
  median contrast 0.136, p95 0.47, p05 0.025, mean 0.18, sat 0.50.
- User 13th Rail shots: contrast 0.14–0.16 ✓, p95 0.49–0.61 ✓, p05 0–0.09, mean 0.19–0.32, sat 0.68–0.80
  (~1.5×; within GH5's per-lighting-cue swing of 0.20–0.78).
- The user is happy with the look; no changes. Note: a hidden browser pane doesn't paint video frames
  (identical stats); use the visible pane.
- **Texture route v0.4:** image-handler textures are invisible to HUD sprites, so the textures go back into a
  real theme pak `hud_ghwor` (createpak; entry id = checksum of the texture name, like the stock paks).
  - The pak is registered via the DE's own `AddToGlobalStruct` (0x325bc724) on `cbcd0af1`, as the DE does
    for highway mods (0x7c73dda7 → `Highway_Pakman_Links`).
  - Pak goes in `DATA\PAK` for this experiment (moving it into the mod folder comes later).
  - The earlier misrouting probably involved a byte-identical copy of hud_vh (same size, and the DE tracks
    paks by size). Offline 14/14 PASS; installed 03:03.
- Built-in highway ids for forcing via `[Band] Preferred*Highway`: `WoR_Highway` (0x777d99ad),
  `GH5_Highway` (0x81a428d1).
- User priorities: score, rock meter, gems. Gems are already native (`GemTheme=ghwor`).

### v0.4 confirmed + v0.5 score/rock meter restyle (2026-10-03 ~03:20–03:45)
- v0.4 in game: `hud_ghwor` loads via the AddToGlobalStruct-registered link (log: `Loading 0x408ce8d1`),
  unloads/reloads correctly on theme switches, no crash. The WoR texture renders (its bar art is visible
  squeezed into the WT+ slot). The pipeline works end to end.
- DE rock meter interface (WT+ `solo_play_rock_meter`): 22 props.
  - Needle: rock 0–2 → `needle_rot_angle` −66..+66° (rotation only; the alternative branch animates the
    same prop).
  - Zone lights: red/yellow/green `*_light_alpha` via conditional floats (0–.667 / .667–1.333 / 1.333–2).
  - Score/streak via `seinttostring`; star power via `setubes` on glow0–5.
- WoR geometry: score bar 512×128 (drawn 96–397 × 14–98, groove 97–380 × 35–89); RM_Base 64×256
  slanted tube; LED glows by section (green top, yellow middle, red bottom).
- **v0.5:** `tools/desc_edit.py` (element edits by local_id) + `ROCK_METER_EDITS` in build.py.
  - Score → WoR star/score bar (scale 0.55), score text moved into the groove, song-time bar into the
    groove.
  - Rock meter → WoR tube + zone LEDs (the DE toggles them) + end cap.
  - Hidden: WT+ dial, backgrounds, ring, needle.
  - Star-power tubes and streak unchanged.
  - New test `integrity_restyled_desc_keeps_de_interface`. Offline 15/15. Installed (pak 159,744 bytes).
- Next: WoR sliding needle (rotating bar clipped by a windowelement over the tube); multiplier bulb.

## 2026-10-03 v0.5.1 (WoR_HUD)
- In game v0.5: big white box over the score bar + rotated white patch behind the score. Cause: sprites "hidden" with texture 0x00000000 are drawn as plain white quads (zone bgs + glow 256x128, Needle 32x64).
- Fix: hidden sprites point at WoR_HUD_blank (4x4 transparent PNG in hud_ghwor pak). New offline test integrity_no_null_textures. 16/16 PASS.
- Rock tube and zone LEDs confirmed working in game (red/yellow/green follow rock level).

## 2026-10-03 v0.6 (WoR_HUD): WoR 1-player layout
- Found the DE implements GH5/WoR mechanics behind theme flags (hudthemes): d38da2b2 = sliding side meter (BAND_side_meter child of the player container, needle Pos driven 0..2 health along (0,0)->(41,-80); hidden in p1_career/faceoff/battle), d5045305 = star meter (star_filler_scale/rgba, star_meter_num_text, star frame rgba/glow). Widgets attach by element presence (guitar_hud: player_meter, BAND_side_meter, alias_band_meter).
- Multiplier images are theme-configurable: f8885a0f (x1..x4), d99b7552 (SP x2..x8) -> semultipliernixie on player_meter.nixie_texture.
- af530ac6 (classic theme check) is hardcoded to ghm/ghsh/ghvh: affects SP tube default scale (0.3 for us), multiplier colours, some SFX/timings. Not needed for our layout.
- hud_1g is now generated (tools/desc_gen.py + tools/wor_1g.py): left rock rail (RM_Base + LEDs from band meter light alphas) with DE-driven sliding needle (anisotropic anchor scale maps DE path onto the rail), right SP rail with 6 segments on glowN_scale, x-badge on the right rail, WoR score box + star + streak box bottom-right. Offline mock: tools/preview_hud.py.
- Tests 20/20 (new: every desc path resolves in the shipped binary; generated descs cover the DE props of their slot; layout wiring; theme flags).
- Unverified in game: font choice (fontgrid_text_a6), setubes scale semantics, needle under anisotropic parent, z order between band_meter and g1.

## 2026-10-03 v0.7 (WoR_HUD) after first v0.6 test
- HUD canvas 1280x720 is stretched to the window (ultrawide too); the 2D highway lives in the same canvas, geometry from guitar_tweaks highway_guitar1 (playline 655, height 350, top 160, widthoffsetfactor 2.2) via highway_2d generate_pos_table. Rails now computed from those numbers (aspect-independent).
- descinterface instances under g1: instance Pos was applied twice -> now (0,0), content g1-relative. Fixed badge + needle (needle was off-screen).
- CSETubesObserver (GHWT_Definitive.exe vtable 0xa11f3c, update 0x478630): elements come from the `textures` prop list; sets texture to hud_rock_tube_glow_full (0x20273d7b) or _b (0x0a3c8de4, SP active) and Scale = (default.x, default.y*fill). Our pak overrides those two names with WoR SP fill art (stock VH pak overrides zone textures the same way).
- Fonts: DE fonts in DATA/FONTS/wtde_fonts.pak.xen; using 0xe7490e96 (clean sans). GH3:WoR num_a9 has WoR's white digits (GH3 font format; port is a candidate).
- Streak box no longer bound to alias_streak (DE slid it behind the score box). Star frame uses WoR's star_meter offsets.

## 2026-10-03 v0.8 (WoR_HUD)
- CONFIRMED rule: children are positioned from the container's TOP-LEFT (pos - (just+1)/2*dims*scale). v0.7 needle_anchor/streak containers had just (0,0) dims 100 -> offset by half the box (needle floated up-left, streak hid behind score). All content containers now just (-1,-1); test integrity_containers_anchor_top_left; preview_hud models it (reproduces v0.7 in-game needle spot).
- SP fill confirmed working in game (setubes wiring + texture override). Narrowed to tube channel (SP_FILL_W 0.7).
- Needle = SB_Tubeglow01 additive, rotated with the rail, +3 toward tube centre. Score scale 0.4 ending before the star. Badge beside the right rail (BADGE_D 215, out 16).

## 2026-10-03 v0.10 (WoR_HUD) + shader
- Calibrated on a 16:9 WoR frame (WoR highway ~= DE highway on the canvas): rails 35% wide x 68% long from just above the strikeline; tube tails cropped (the "floating" bit); badge at (edge+44, y 443) with metallic ring; score panel star at (1149,579).
- Note-streak counter: DE senotestreaklights sets light0..4_texture to HUD_score_light_{0 off,1 half,2 lit}{,_green,_purple,_blue}; theme pak overrides those 12 names with WoR combo dashes, 5 dashes up the right edge above the badge.
- alias_star_flame -> star container (DE spawns Star_Meter_Sparks01 there on star earned). Song progress line above the score box (songtime_bg/fg). Theme row: sidebar_x_scale 2.0 + sidebar offsets (-2,0)/(2,0) -> thicker highway borders.
- Needle: DE hides/stops the side meter in p1_career, faceoff, battle (97e11003) - by design.
- Shader: GHWoR.ini SurfaceBlur BlurStrength 0.45 -> 0.55 (backup GHWoR.ini.before-moreblur).

## 2026-10-03 v0.11 (WoR_HUD) after user recording vs GH5 "Song 2" footage
- GH5/WoR: rails ARE the highway borders (wide tubes centred on the edge, screen bottom -> ~y430); badge caps the top of the right rail; 10 small streak marks on the border above it (DE: 5 lights x 2 marks); star = dark inside + gold outline, count in gold (DE sends 238,204,120 -> now wired).
- Rails RAIL_SX 0.5, RAIL_SY 1.05, from y700, gap 0. Badge redrawn (smooth disc, thick silver bevel). Streak marks = 2 squares per light texture.
- Shader: SurfaceBlur 0.65, BloomMix 0.6, BloomLimit 0.30 (backup GHWoR.ini.before-bloom). Tools: opencv for frame grabs; browser canvas crop trick for YouTube frames.

## 2026-10-03 v0.12 (WoR_HUD)
- User: use extracted textures, no generated art. Multiplier = GH3:WoR HUD_score_nixie_{1a,2a,3a,4a | 2b,4b,6b,8b} (2048x256 strips, crop (1,1,155,138) -> 160x144): badge + the rail stick above it (stick axis 28.87 deg CCW, end at crop (69,110)). Streak lights = GH3:WoR HUD_score_light_* copied as-is under the DE names (2 marks per light).
- Placement: stick end anchored at the SP rail top (RAIL_TOP_D 250), image rotated by RIGHT.angle+28.87, BADGE_K 0.7; lights along the stick.
- Highway is drawn above the HUD -> rails centred on the edge got half hidden; rails now gap 15 outside the border, RAIL_SX 0.45.
- Removed generated badge/led art (wor_art.badge, led_dash).

## 2026-10-03 v0.13 (WoR_HUD)
- ROOT CAUSE small/misaligned badge: png2img/DDStoIMG pads non-power-of-two PNGs (160x144 -> 256x256 DDS, art top-left) -> sprite showed the art at 160/256 and the just-anchor point moved. Badge frame now 256x256. RULE: texture PNGs must be power-of-two.
- Measured vs GH5 frame at the same canvas scale: score/streak/star within a few px; badge now centre ~(840,450) d~50 (GH5 (848,448) d~50).
- Rails tilt 1.7 deg outward (GH5 SP rail 28.4 vs edge 26.7: perspective sidebars), gap 18 at y700. Star interior: WoR star frame tinted dark under the gold outline. SP half marker (WoR SB_TubeNeedle01) at the middle of the fill span.

## 2026-10-03 v0.14 (WoR_HUD) + shader
- GH3:WoR layout (gh3wor/guitar_hud_2d_career.txt career_hud_2d_elements): nixie pos_off (-278,-230), lights (-235,-165)..(-275,-233) step (-10,-17); GH3 img header display dims = texture dims, elements top-left anchored, 1:1 -> light centres in badge-crop px (58,80),(48,63),(38,46),(28,29),(18,12). Lights now placed via badge_point() with the badge's own transform.
- Rails from y745 x RAIL_SY 1.25 (end below screen). SP fill override recoloured cyan (no white floor).
- Danger blink: theme flag 0x882f22a1 -> DE blinker (887db8fe) toggles SIDE_meter_red_ON_rgba every 0.3 s below 1/3 rock; side meter now has a real red glow over the rock rail (alpha = SIDE_meter_red_ON_alpha from the health widget).
- No stock hook for multiplier-change animation (alias_player_multiplier only Die'd in faceoff).
- Shader: SurfaceBlur 0.80, BloomMix 0.70, BloomLimit 0.27 (backup before-bloom2).

## 2026-10-03 v0.15 (WoR_HUD) - calibrated on user 720p capture vs GH5 720p frame
- GH5 canvas measurements: rails ~12 wide, y ~606 -> ~462 with the bent tail resting on the highway border; badge (849,443) d50; score box x 935..1115 y 562..603; star ~60; score digits ~17 tall, streak ~15; streak box 982..1102.
- Rail tails are intentional (they curl onto the border): no crop; tail is at the texture's bottom-left -> left rail mirrored (negative x scale, like the DE's right sidebars). Tube axis is x=48 (TEX_AXIS_X 16). RAIL_SX 0.5, RAIL_SY 0.64, tail tip y 606, gap 15.
- SCORE_C x 1056, STAR_K = 0.92*SCORE_K, score font scale 0.4, streak 0.34 (right edge 1090).
- preview_hud: draws mirrored sprites; side-by-side compare against a GH5 frame.

## 2026-10-03 shader pass 4 (GHWoR.ini, backup before-bloom3)
- SurfaceBlur BlurStrength 0.80 -> 1.00 (max), BlurRadius 3 -> 4 (max, 9x9); PD80 Bloom BloomMix 0.70 -> 0.85, BloomLimit 0.27 -> 0.22, BlurSigma (bloom width) 30 -> 60.
- SurfaceBlur is now at its slider maximum: further softness needs SurfaceBlurIterations=2 in the ReShade preprocessor definitions.

## 2026-10-03 v0.16 (WoR_HUD) - WoR's own placement data, WoR font
- Ultrawide: DE stretches the whole 1280x720 canvas (2000x844 frame: highway 1.55 px/unit horiz vs 1.17 vert), HUD and highway alike -> canvas-space layout holds on every aspect; the old misalignment was hard-coded coords.
- WoR guitar_tweaks.qb highway_guitar1 == DE geometry (655/350/160/2.2); rockmeter_pos (-5,-130) scale 0.7, ns_meter_pos (2,-320) scale 0.45, sidebar_x_scale 0.32.
- WoR setup_sidebar_rockmeter: meters are children of the highway's sidebar_container_left/right (DE creates the same ones): pos (sidebar_x, sidebar_y) = edge line 25% of height BELOW the playline (340, 742.5), rot +-26.70. Rails now placed from that chain (tube bottom-centre at (-23.954,-130) rock / (26.031,-130.772) SP mirrored) instead of GH5 calibration: tubes span y 615 -> 463, straddling the border, foot intact.
- SP fill: SP_Fill01 strip == SP_Base tube columns; segments drawn in the tube's texture frame, texture shipped flipped (DE overwrites segment scale, can't mirror via scale).
- Score panel offsets from WoR uidesc_star_meter (score_container frame, K0 = 0.574): WoR streak / streak_front / score front glass / bG / star_filler (25 tall behind box) / star at WoR scale; Score scale 0.387*1.35*K0 just (1,-1); streak 0.56*0.9*K0.
- Font: WoR fnt == DE fnt layout (u16 charmap 0x18, 0x0001dead, 36-byte glyphs from 0x200a8, texture ptr at 0x200a4); only the texture differs (Xbox img vs PC img). tools/wor_font.py converts (pad to POT + UV rescale); fontgrid_numeral_a1 shipped in the theme pak as WoR_HUD_num_a1 (UNPROVEN in game: no stock theme pak carries a font).
- Ghost bar = DE songtime_bg/fg: all DE-driven dummies now inside a zero-size windowelement (clipped whatever the DE sets).
- Not done yet: WoR multiplier (uidesc_hud_meter_combo: frame2_apm ring, frame2_back arm, 10 LEDs, colours from HUD_attach_widget_sidebar_notestreak_meter); badge still GH3:WoR nixie. WoR's multiplier centre would be (798,456), i.e. on the edge line.
- Known limitation: FocusedHighway / Bad Trip Mode change the highway height/scale; the static layout assumes both off.

## 2026-10-03 v0.17 (WoR_HUD) - from the user's v0.16 in-game capture (2026-10-03 16-20-25.mp4)
- SP "too many dividers": each of the 6 DE segments drew the WHOLE SP_Fill01 (tapered top + bent tail) -> a seam per segment. Fill texture is now SP_Fill01's straight band rows 44..60 (constant left edge, 64x16 POT, flipped); segment dims drop the 128/124 factor. Only divider left = sp_marker (SB_TubeNeedle01) at the half.
- Rails: RAIL_TUCK 6 canvas units toward the highway, perpendicular to the edge (tubes hug/tuck under the border like WoR; measured ~11 perp from tube centre to border centre in v0.16). Moves LEDs, fill, marker, needle, red glow and multiplier badge with them.
- Streak number: right-aligned (just (1,0)) at streak-texture x +98 from centre (window ends ~220/256), scale 0.56 -> 0.49 (STREAK_NUM_K).
- Star count: scale K0 -> K0*0.62 (STAR_NUM_K); v0.16 digit was ~30 canvas tall vs ~17 in the WoR reference.

## 2026-10-04 v0.18 (WoR_HUD) - calibrated on 2 GH5 frames vs a v0.17 mod frame, aligned by the fixed fret rings
- Mod capture 1266x683 = canvas 1:1 offset (+2,+29) (frets green 435 / orange 845 match exactly).
- Rails: RAIL_TUCK +6 -> -2.5 (GH5 tubes ~9 further out; v0.17 sat on the border).
- Multiplier: BADGE_SHIFT (3.5,-16) -> disc ~(845,447); streak marks LIGHT_SHIFT (4.5,-3.5) -> off the border along (775,385)-(812,445).
- SP half divider: GH5 is a near-level band at y~531 -> sp_marker rot 3 deg (was tube angle), SP_MARKER_UP 8 tex px.
- Score panel: SCORE_C y 585 -> 581; score digits x1.2 (SCORE_TEXT_K), shift (4,-4); star +6 x (STAR_SHIFT); star number nudge (2,-2).

## 2026-10-04 v0.19 PROPOSED (WoR_HUD + shader), mock-first, NOT installed
- User: v0.18 was a regression; restore v0.17; HUD must draw ABOVE the highway; mock before applying. Inputs:
  `OneDrive\Videos\GH5\original.mp4` (GH5) and `modded.mp4` (in-game v0.17, recorded before v0.18 was installed).
- Alignment: same canvas x; modded capture is the canvas shifted up 10 px (fret rings identical size/x). Timeline:
  original = modded + 18 frames. Frame-averaging each video isolates the static HUD (mean_*.png in the session scratchpad).
- Mock calibration (tools/preview_hud.py --game, GAME_CALIB): game = mock + (1,3) for the band meter desc,
  + (1,9) for the g1 descs; text now drawn with the real WoR font. Calibrated v0.17 mock matches the v0.17 capture
  within 0-2 px (badge, lights, score box, star, streak, texts).
- Layering: z_priority is compared screen-wide: the DE highway sidebars (z 3, guitar_highway.txt) drew over our
  rock tube (z 2-2.5). HUD_Z = +10 on every generated element.
- DE silver border sits ~4 units further in than GH5's; tubes placed by GH5's tube-to-border relation:
  RAIL_TUCK_LEFT 3, RAIL_TUCK_RIGHT 5 (v0.17: 6/6).
- Multiplier: BADGE_SHIFT (8,-20), LIGHT_SHIFT (12,-20) (GH5 badge ~(845,446), marks (775,382)-(812,438)).
- Score panel: SCORE_C (1055.6,581), box art + holder + bar stretched x1.039 (SCORE_X_K), score text x1.2
  (GH5 17 px vs 14), streak text 0.573 (14 vs 12), star count 0.82 (20 vs 15), all ~7 px higher.
- SP: divider SB_TubeNeedle01 at (851,528) rot 37 x1.25 (GH5: level-ish arch at y~531); fill rgba teal
  (20,235,180) (GH5 mean 65,139,129; v0.17 read grey-blue 88,126,136).
- Limits: x1 streak lights are pink in GH5 but the DE shares one light set for x1/x2 (hud_widgets
  senotestreaklights); GH5 score has thousands commas (DE string has none); no SP activation in either capture.
- GH5 shows NO "Hot Start!" / "100 Note Streak!" text and no strikeline fire burst at 100 (DE does).
- Shader (data, background luma percentiles): GH5 p10 .022 p50 .143 p90 .504; mod .063/.197/.513 -> mod has
  lifted shadows, same highlights; GH5 also much stronger depth of field. Proposed: new own shader
  shaders/GH5_Grade.fx (soft toe y*y/(y+t)*(1+t), t 0.10 matches GH5 to ~0.01 up to p75) + GHWTDE.ini DOFBlur
  2.0 -> 3.0. Live preset was already at SurfaceBlur 0.90 r3, Bloom mix 0.78 limit 0.245 sigma 45 (undocumented
  pass 5, backup before-bloom4).
- Mocks: ghwt-wor-hud/verify/mock_hud_v019.png, mock_full_v019.png, mock_shader_v019.png.
- 2026-10-04 ~17:52 APPLIED (user approved): HUD v0.19 installed; GH5_Grade.fx installed in
  reshade-shaders/Shaders and added to GHWoR.ini after Curves (Toe 0.10, Strength 1.0); GHWTDE.ini DOFBlur 2.0 -> 3.0.
  Backups: backups/*20261004-175149 (GHWoR.ini, GHWTDE.ini, WoR_HUD mod folder, hud_ghwor.pak.xen). Popups NOT hidden.
- v0.19b (built, NOT installed; user: star/streak text too big, not aligned): single-frame threshold measurements
  (GH5 vs v0.17 capture) + mock text bias (preview TEXT_CALIB: mock 8% big, 13% for star; streak 2 low/2 right).
  Predicted v0.19 in game: score 16 px (GH5 17), streak 15 (14), star 21 (20) and star count ~5 px left of
  GH5's centre (WoR desc anchor sits 3.4 left of the star sprite). v0.19b: SCORE_TEXT_K 1.25, STREAK_NUM_K 0.535,
  STAR_NUM_K 0.78, STAR_NUM_NUDGE (5.5,-2), STREAK_RIGHT 98, SCORE_TEXT_SHIFT (0.4,-2) -> calibrated mock = GH5
  within 1 px (score 17 569-585 r1097, streak 14 610-623 r1084, star 20 569-588 centre 1134).
- Fonts: theme key d5927557 = in-play message font (hud_show_note_streak_combo, HUD_band_streak_notify, drum fill,
  fail hint; DE default fontgrid_text_a6; stock themes use e.g. fontgrid_bordello). WoR fonts convertible with
  tools/wor_font.py: text_a1 (GH5/WoR menu gothic), text_a3 (italic), title_a1 (WoR brush), lyric_a1;
  numerals a1 (current), A1_b (closest to GH5's embossed digits, footed 1), A2. Options: verify/font_options.png.
- 2026-10-04 v0.19b INSTALLED: text per single-frame GH5 measurements. Score digits taller+narrower than WoR's
  (GH5 h17/pitch 19/width 10 vs v0.17 h13/18/9): SCORE_TEXT_KX 1.08, KY 1.26 (non-uniform Scale). DE advance for
  numeral_a1 = 60 font px (pitch 18 at x-scale 0.2997; the mock assumes 58). Streak 0.555 (h14/pitch18 vs 12/15.5).
  Star count 0.78, nudge (5.5,-2). Message font: WoR fontgrid_text_a1 shipped as WoR_HUD_text_a1, theme
  d5927557 + bf72b22c (replaces the copied WT+ fontgrid_text_a6). Numerals A1_b deferred: different metrics
  (cell 46x44, glyph adj -5) and unverified DE spacing rule for it.

## 2026-10-04 restructure: three options, Nexus drop-in packaging
- Options: (1) GH5/WoR HUD (DE mod + theme pak), (2) "Background-only shaders" (ghwt_bgfx add-on + GH5_Grade.fx,
  ReShade default folders, inert without ReShade), (3) HUD fixes (planned .asi for Ultimate ASI Loader; in-memory,
  signature-checked patches: x1 pink lights, score commas, SP activation look).
- Format: extract-into-game-folder archives (`python build.py --package` -> dist\*.zip). Mod.ini now
  "GH5 / Warriors of Rock HUD" v0.19b.
- WTDE menu toggles: not possible by data (settings pages are script-literal option lists in 0xd573b66d.qb; the
  option table f26e4c1f entries are data: variable/text/description/section/key, type 0x535b9828 = on/off).
  Skipped for now; revisit when the functions are compiled into WTDE itself.

## 2026-10-04 v0.20 (built, NOT installed) - user report on v0.19b (videos 18-27-10 glitched, 18-40-33 ok)
- Crash with non-WoR themes: dump 18:32 (CrashDumps\GHWT_Definitive.exe.23568.dmp), code 0xC00000A5 raised at
  exe+0x56b448 while the log buffer shows "Unloading pak 0x408ce8d1" (= hud_ghwor). Only our theme row changed vs
  v0.18. Prime suspect: the 2nd font (text_a1, 512x512) shipped in the theme pak in v0.19b. v0.20 ships no message
  font: d5927557/bf72b22c -> 0x2e5a5f81 (DE bold gothic in DATA\FONTS\wtde_fonts.pak, always loaded). Pak back to
  1089536 bytes (v0.19b's 1490944 also equalled L_GUIT_PicToBurn2_anims.pak). Needs an in-game repro.
- 2nd-song glitch: streak lights drawn with the DE's stock HUD_score_light_* (big pink squares). Those names are
  global textures (no HUD pak defines them); our theme pak overrides by name; after the pak unloads and reloads,
  the stock ones win. Same mechanism as the SP fill override (hud_rock_tube_glow_full). Unresolved.
- SP fill: was ~3 px left of the tube and constant width while the glass leans/widens (22 -> 30 tex px). Each
  segment is now centred on the tube centre line at its mid row and sized to the glass interior (SP_RIM 3).
  Divider on the tube centre line at game y 531 (sp_marker_pos). Fill steps by phrase (DE snaps; GH5 animates):
  native, plugin scope.
- Star: STAR_K 1.15 (GH5 gold star 57x51 vs 48x45 in game, same mask; mock = game size).
- Shader check (background luma p10/p25/p50): GH5 .027/.061/.151; v0.17 .065/.110/.199; video 1 (GH5_Grade, DOF 3)
  .037/.086/.191. Shadows close, mids still bright; DOF 3 did not reduce gradient energy (19.7 vs GH5 12.9).
- Highway colour: highway sprite rgba = global highway_normal; sidebars = global material sys_sidebar2D at
  rgba 255. No theme key -> darkening is global (all themes) or via the add-on.
- Messages: hud_create_message needs GetHUDMessageParent (native); player messages live in our 'message'
  container -> alpha 0 on that container (+ hud_message_fire) hides text and the 100-streak burst.
- WoR assets present for Helper Pill (helper_pill_body/_end/_super_*, helper_icon_universal, pill_128_fill,
  buttons_x360 font) and Menu Popup (dialog_bg/_bord/_universal_bord, car_bord_popup, light_box + WoR scripts).
- 2026-10-04 ~19:30 v0.20 INSTALLED + user test: GHVH no crash (harness run also clean, no new dump) -> crash
  fixed by not shipping the message font. WoR: highway border vanished: theme key 18f90ff6 pointing at a texture in
  our per-song theme pak isn't visible to the material system. Now 18f90ff6 = 0x0d6323dc (GHM's darker worn-metal
  border, global_model_tex_wtde.pak, mean 114 vs 137), nothing ships. Star count sat (+3.3,-3.6) off the gold star's
  shape centre; now anchored on the filled star's centroid (STAR_ART_C 63.69,70.73 of the 128 px overlay).
  Harness: --hold N added (runs past song end, reports new crash dumps). Companion mod WoR_HUD_NoMessages
  installed (HUD Theme "Guitar Hero: Warriors of Rock (no messages)", message/fire containers alpha 0).

### 2nd-song glitch: reproduced and diagnosed (2026-10-04 ~19:40, v0.20 installed)
- Capture: ghwt-wor-hud/verify/session_2nd_song (26 window shots @10 s, debug.txt, ReShade.log; tests/collect_session.py,
  passive: does not launch the game; debug.txt is exclusively locked while the game runs, copied after exit).
- Visible difference song 1 vs 2 (verify/session_2nd_song/cmp_mult.png): only the streak/multiplier lights change.
  Song 1 = our thin WoR dashes (orange/purple); song 2 = the DE's stock chunky blocks (pink/white, brown). Score box,
  star, streak text, tubes, border unaffected. No crash dump.
- Log: song 1 `hudtheme_load_paks` loads hud_ghwor (0x408ce8d1) and hud_shared_assets (0xaa5a1e0e) fresh, AFTER z_in_game
  (line 19265 vs 17396). Song 2: z_in_game is reloaded (line 27179) but `hudtheme_load_paks` logs
  "0x408ce8d1 already loaded. Adding handle 0x90439105" (line 29404) and the same for aa5a1e0e: `hudtheme_unload_paks`
  (mpm_object_unload_paks owner 0x90439105) only drops the handle; the pak stays resident until a theme change/flush.
  So our name-overridden HUD_score_light_* textures were registered before z_in_game's second load and lose to stock.
- Same applies to anything else we override by global name (SP fill trick).
- Candidate fixes: (1) native plugin re-registering the textures; (2) find a pak that IS reloaded per song after
  z_in_game to carry the overrides; (3) a data-only way to make the DE unload hud_ghwor per song (not found).
  gems_ghwor was also only loaded in song 1 (no reload line in song 2), so it is not a candidate.
- Shader mock (verify/mock_shader_v021.png, tools/shader_mock.py): vs GH5 footage Toe 0.10 already matches p50
  (.138 vs .143); Toe 0.16 gives .122. Awaiting user choice of Toe/DOFBlur.

### Shader applied; v0.21 analysis (2026-10-04 ~19:50)
- User approved: Toe 0.12 (GH5_Grade.fx default + GHWoR.ini [GH5_Grade.fx] Toe=0.12) and GHWTDE.ini DOFBlur 3.0 -> 3.5.
  Backups: backups/GHWoR.ini.before-toe012-20261004-194442, GH5_Grade.fx.before-toe012-..., GHWTDE.ini.before-toe012-...
  (revert = copy back; previous values Toe 0.10, DOFBlur 3.0). Mock: ghwt-wor-hud/verify/mock_shader_v021b.png.
- User v0.20 screenshots: (1) highway surface/frets/borders should be darker and the borders thicker like GH5;
  (2) star not centred; (3) SP fill "looks mirrored".
- Star (tools/star_measure.py, same detector on GH5 footage / user shot / mock): GH5 star bbox 1106-1164 x 552-606
  (centre 1135,579; digit 1133.6,580.3); v0.20 in game 1105-1158 (centre 1131.5,579.5; digit 1130.5,581.1) -> star 8%
  small and 3.5 px left. Calibrated mock (mock-game: star -0.5,-1.5; digit -1.5,-2.2): STAR_K 1.24, STAR_SHIFT (4.2,-1.0),
  STAR_NUM_NUDGE (-0.8,-2.0) -> star 59x53 centre (1135.5,580.5), digit (1135.9,580.9). Mock: verify/mock_star_v021.png.
  NOT applied yet (awaiting approval).
- SP fill: teal extents of the real shot match the mock within 1 px; edge-correlation puts the real tube ~(-1,-3) from
  the mock (weak). No mirroring found in verify/sp_mock_vs_real.png; asked the user what looks mirrored.
- Border: v0.20 GHM texture 0x0d6323dc reads as a thin ~5 px blue line (verify/border_cmp.png), v0.19b stock was ~14 px
  silver, GH5 is ~14 px steel with a dark core. WTDE ships highway_gh5 / highway_ghwor paks (ids GH5_Highway
  0x81a428d1, WoR_Highway 0x777d99ad via [Band] Preferred*Highway = global, not theme-only): candidate for the
  surface + frets + borders. Not tested.

### v0.21 installed (2026-10-04 ~20:32)
- User approved the star mock: STAR_K 1.24, STAR_SHIFT (4.2,-1.0), STAR_NUM_NUDGE (-0.8,-2.0).
- SP fill: user says the BLUE TEXTURE is mirrored horizontally vs the tube -> SP_FILL_FLIP False (fill band shipped
  unflipped, content cols 35-63; SP_FILL_COLS follows so the fill stays centred). Mock verify/mock_sp_v021.png.
- Border: back to the DE's stock sidebar (SIDEBAR_TEX None -> no 0x18f90ff6 key; sidebar_x_scale 2.0 = the thick
  v0.19b look the user wants). Remaining ask: darker metal (borders + frets + strikeline rings), global is fine.
  Mock verify/mock_metal_v021.png (metal x0.72 / x0.58 vs GH5). Proposed route: the ReShade add-on darkens those
  textures when the game uploads them (or the future .asi plugin). Not built yet.
- Test: GHWTDE.ini PreferredGuitaristHighway/PreferredBassistHighway = GH5_Highway (user OK; global) to see whether
  WTDE's GH5 highway brings its own darker borders/frets. Backup GHWTDE.ini.before-gh5hw-20261004-203159; v0.20
  backups WoR_HUD.v020-20261004-203159, hud_ghwor.pak.xen.v020-20261004-203159. 24/24 offline tests pass.
- v0.21b (built, NOT installed, awaiting mock approval): user: the teal fill leaves the tube in places; mirroring did
  not help. Cause: the fill used the rock meter's LED span (SP_Base rows 14-237) but the glass is rows ~21-219
  (6-20 top cap, 222-252 curled end) -> fill ran into both caps. SP_GLASS_ROWS (21,219); SP_FILL_FLIP back to True.
  Mocks: verify/mock_sp_v021b.png (tube zoom), verify/mock_full_v021.png (full frame + zooms vs GH5 and v0.20).
  The installed build is still v0.21 (star fix, unflipped fill, stock border) + GH5_Highway ini test.
- v0.21 final INSTALLED (~20:50): user rejected both star power experiments ("looks weird") -> SP fill restored to
  v0.20 exactly (flip True, LED span; tube region pixel-identical to the v0.20 mock). Kept: star fix, stock thick border
  (no 0x18f90ff6). GH5_Highway ini test still set. Open: SP fill/tube fit to revisit later, darker metal.
- v0.21d (built, NOT installed; mock verify/mock_sp_v021e.png): user wants the v0.20 fill look but fitting the tube.
  Layering: new texture WoR_HUD_sp_frame = SP_Base with only the glass interior cut out (wor_art.cut_glass, rows
  21-221, 2 px outline kept), drawn over the fill at z 3.7 (fill 3.5, divider 3.9): hides the overrun at the outline
  and caps. Fill span SP_FILL_ROWS (17,226) instead of 14-237: rows past ~226 are outside the tube silhouette (the
  curl bends sideways) and can't be covered. Same fill texture/flip/colour as v0.20.

### v0.22 built, NOT installed (2026-10-04 ~21:30), awaiting mock approval
- User test of v0.21 (shots images/13,14): at 50% the SP fill stops ~5 px under the divider (fill half = SP_Base row
  125.5, divider row 107) and the bottom pokes past the curled end; at 100% it runs into the top cap. Blue border in
  shot 14 = the DE's SP-full sidebar glow. GH5_Highway gives the diamond-plate surface; borders/frets unchanged.
- SP shaped segments (user idea): each segment has its own texture WoR_HUD_sp_seg0-5 (wor_art.tube_segment: SP_Base
  glass interior per row minus SP_RIM, filled with SP_Fill01's column profile, flipped like the tube), drawn with the
  tube's transform. Lower 3 segments span row 232 -> divider row, upper 3 divider -> row 21, so 50% meets the needle.
  The DE sets texture AND scale on the element glowN_texture names, so each segment is a ContainerElement (rot +
  scale (0.3, 0.3*fill), takes the DE's texture name harmlessly) holding the shaped sprite (bottom-anchored).
  RISK to verify in game: DE setting 'texture' on a container. preview_hud: DE scale now (default.x, default.y*fill)
  (old mock scaled x too -> the "notch"), container rotation now inherited.
- Star count STAR_NUM_K 0.78 -> 0.72 (user: GH5's count 1-2 px smaller).
- New optional mod WoR_HUD_DarkMetal (build_dark_metal; packaged as GH5-WoR_HUD_Dark_highway_metal): the DE builds
  in-game materials at song start from global arrays 0x345d04a2 / af201180 (tb.pak scripts/guitar/guitar_material.qb,
  the DE version; qb.pak has the stock WT one). The mod $change$s them to copies where 33 metal materials get
  m_psPass0MaterialColor [0.72,0.72,0.72,1]: sys_sidebar2D, sys_fretbar_large/medium/small, Mat_NB_Neck,
  Mat_NB_*_Cup_* (incl 4D/5D/DWN). Ring edges/caps/gems untouched. Global (all themes; user OK). Risk: copies freeze
  the DE's arrays at this DE version. Also found: create_in_game_materials_spawned reads the HUD theme sidebar key
  BEFORE hudtheme_load_paks, which is why a sidebar texture in our theme pak was invisible (v0.20).
- Mocks: verify/mock_sp_v022.png, verify/mock_full_v022.png (dark metal approximated by pixel darkening).
- tools/pak_list.py: .pak.xen + .tex dictionary lister (tex entries 0a281300: checksum, w, h, dds off/size).
- v0.22b (built, NOT installed): user: highway metal even darker, star count between 0.78 and 0.72 -> DARK_K 0.58,
  STAR_NUM_K 0.75. Mock verify/mock_full_v022b.png (metal 0.72 vs 0.58, count 0.72 vs 0.75). 24/24 offline.
- v0.22c (built, NOT installed): STAR_NUM_K 0.765 (user). Mocks verify/mock_star_v022c.png, verify/mock_full_v022c.png. 24/24 offline.
- v0.22d (built, NOT installed): user: count back to 0.78; star bg gradient = extracted band_HUD_silver_star_frame (grey radial centre) tinted (130,126,128) as star_bg (WoR_HUD_star_bg); STAR_K 1.24 -> 1.20. Mocks verify/mock_star_v022d.png, mock_full_v022d.png. 24/24 offline.
- v0.23 proposal (mock only, nothing changed in the build): user screenshots images/15,16 = installed v0.21 (nothing
  installed since 20:43). Border on v0.21 capture: bright band ~14 px at rows 620-710, centre lines
  x = 352.5 + 0.518(710-y) / 927.5 - 0.517(710-y); GH5's ~1.4x wider. Proposal: sidebar_x_scale 2.0 -> 2.8 and
  RAIL_TUCK_LEFT 3.0 -> 0.5, RAIL_TUCK_RIGHT 5.0 -> 2.5 (tubes follow the border's outer edge, which moves out ~2.5
  canvas px at the tubes' height). Assumes the DE scales the sidebar about its centre line (to verify in game).
  tools/border_mock.py (inpaints old tubes, re-draws the border from its own row profile widened, redraws the HUD).
  Mocks verify/mock_border_v023.png, verify/mock_full_v023.png.
- v0.23 (built, NOT installed, 24/24 offline): user: wider border OK; tubes must lie ON the border (GH5: coaxial,
  border runs under the tube, curled end rests on it), above the border but below gems/sustains. v0.21 tubes sat
  3-7 px (rock) / 5-9 px (SP) off the border centre and 1.6 deg steeper. New: on_border() rotates each Rail to the
  border centre-line angle (27.4 deg) and shifts it onto the line (measured BORDER_LINE_L/R, game = canvas + (1,9));
  badge/needle/LEDs/SP fill follow the rail. RAIL_Z: tube parts drawn at absolute z 3.02-3.09 (border 3, strikeline
  cups 3.1-3.9, gems native/unknown but above cups) instead of +10. sidebar_x_scale 2.0 -> 2.8. Includes v0.22d
  (shaped SP segments, star 1.20 + silver-frame gradient bg, count 0.78) and WoR_HUD_DarkMetal 0.58.
  RISKS to check in game: tube z vs border/gems (if z accumulates per parent, tubes could fall under the border);
  DE setting 'texture' on the SP segment containers; border scaling about its centre line.
  Mocks: verify/mock_rails_v023.png, verify/mock_full_v023.png (tools/border_mock.py).
- v0.23b (built, NOT installed, 24/24 offline). User on the v0.23 mock: border a bit too thick (GH5 tube is wider than
  the border), corner where the tube cap rests on the border, mock drew the border over the strikeline, HUD tubes
  too grey (add shadows), streak lights misaligned. GH5 f900 grid: tube ~20 px wide (x 389-409 @ y590) coaxial with
  a ~17-20 px border, cap resting on the border at y 597-605 -> coaxial kept; sidebar_x_scale 2.8 -> 2.3.
  Tube shadows: rm_shadow/sp_shadow (tube art tinted black, alpha 0.6, offset (1.5,2), z 3.01) + tube art rgba x0.8
  (RAIL_TINT). Streak lights: LIGHT_SHIFT (12,-20) -> (8,-20) = BADGE_SHIFT (they sat 4 px right of the badge's holder
  bar). border_mock.py keeps saturated pixels and the strikeline rows (draw order: border z3 < cups/neck 3.1+).
  Mocks verify/mock_rails_v023b.png, verify/mock_full_v023b.png.
- v0.23c (built, NOT installed, 24/24 offline): user: border too thick, HUD elements darker like GH5 (per element).
  sidebar_x_scale 2.3 -> 2.0 (GH5 border 17-20 px ~ ours at 2.0). Per-element brightness vs GH5 (5 frames, low-sat
  pixels): rock tube x0.59 (RAIL_TINT_L), SP tube x0.9 (RAIL_TINT_R), score box art+glass x0.63 (SCORE_TINT), streak
  box+front x0.67 (STREAK_TINT); badge already equal. After: score p50 27 = GH5 27, streak 24 = 24, SP 39 vs 45,
  rock 50 vs 60 (its p85 is the lit LED glare). Tube shadows kept. Mocks verify/mock_rails_v023c.png,
  verify/mock_full_v023c.png.
- v0.23d (built, NOT installed, 24/24 offline): user: rock meter slightly left, star power slightly right (like GH5);
  alternate with a black backing behind both tubes. GH5 f700 grid / edge correlation: GH5 tubes sit outward of the
  border (rock ~9-12 px left, SP ~8 px right of the coaxial position) -> RAIL_OUTSET (-9, +8) after on_border(). The
  badge and streak lights follow the SP tube: badge centre now ~847 vs GH5 845 (v0.23c 838). RAIL_BACKING (default
  off): opaque black copies of both tube arts (rm_back/sp_back, z 3.015). Mocks verify/mock_rails_v023d.png (GH5 |
  v0.23c | A | B), verify/mock_full_v023d.png. Not done: GH5's tubes also end ~4-5 px higher.
- v0.23e options (mock only, backing on): RAIL_OUTSET (-9+k, 8-k) for k=1..4 -> verify/mock_rails_v023e.png (GH5 | v0.23d B | 1-4 px in). Awaiting the user's pick.
- v0.23f (built, NOT installed, 24/24 offline): user picked option 4 + B -> RAIL_OUTSET (-5,+4), RAIL_BACKING on,
  RAIL_GAP_FILL (2,4): extra black tube copies shifted 2 and 4 px towards the highway (z 3.012) fill the gap between
  tube and border. Mock verify/mock_rails_v023f.png.
- Findings for the next items: WoR highway art = WoR z_in_game pak/highway/basic_gems/basic_gems.tex.xen (Xbox tex
  dict; new decoder tools/x360tex.py in C:\Users\rockb\mods\tools -> ghwor-extract/basic_gems_png, 144 textures, names
  match the DE's NB_*/FretBar_* by checksum). WoR strikeline cups are IDENTICAL to the DE's. The "hollow" idle cup is
  the dark idle bowl NB_Cup*_Base_01 (mean 58, opaque); the pressed bowl Base_02 is metallic (88) like GH5's idle look
  -> fix = idle cup materials use Base_02 (data, in the materials mod). Candidate WoR border textures: 388dd606
  (64x512 dark steel), 2ed9ac77 (32x512 tapered thin rail). Gem pak links table af130dc4; the selected gem pak loads
  BEFORE create_in_game_materials_spawned (HUD theme pak after), so gem-pak textures are visible to materials.
- v0.24 mocks (nothing built for these yet): (2) WoR border 388dd606 drawn as the border strip (border_mock.py TEX
  mode; 2ed9ac77 turned out to be a tapered wound string, not a rail): verify/mock_border_wor_v024.png (22 / 28 px).
  Needs the texture loaded BEFORE create_in_game_materials_spawned -> must ship in the gem pak (af130dc4 links;
  e.g. our mod repoints the ghwor gem theme's pak to a copy of gems_ghwor + 388dd606) and the HUD theme key
  18f90ff6 names it; caveat: with another gem theme the border texture would be missing. (3) Strikeline cups: all
  cup layers are opaque; the idle bowl Base_01 is a dark dish (rgb ~36,42,47) that reads as a hole; proposal: idle cup
  materials use the metallic pressed bowl Base_02 (rgb ~65,67,70): verify/mock_cups_v024.png.
- v0.25 mock (verify/mock_rails_v025.png, mock_full_v025.png; tools/border_tex_mock.py): WoR border 388dd606 drawn
  like the DE draws its sidebar (whole 64-px texture across the strip, texture carries the taper, bilinear; old border
  inpainted; cups restored on top), x0.58 dark metal, 28 px visible at the bottom. User Q 1.1 (wider highway so the
  strikeline cups sit on the thin inner rail): done by placing the border instead of widening the highway (lanes,
  gems and HUD geometry unchanged): the rail (texture col ~54, 0.24 of the content width from the centre) is put
  under the outermost ring edges (x 387 / 893 at y 638) -> inner edge 393.2 / 886.8. Tubes over WoR's thick bevel
  (GH5 relation): RAIL_OUTSET (-7.4, +7.2). Cups: mocks were wrong (pixel darkening + bowl swap made the chrome ring
  look see-through); v0.21 in-game cups already match GH5 -> no bowl swap, and the materials mod no longer touches
  Mat_NB_*_Cup_* (DARK_PATTERNS = []).
- v0.25b mock: user: multiplier badge + streak lights closer to the border -> BADGE_SHIFT = LIGHT_SHIFT (4,-17) (was (8,-20)); badge centre 840.6,445.4 vs GH5 843,445.4; holder bar now against the border. verify/mock_badge_v025b.png, mock_full_v025b.png.
- v0.25c (built, NOT installed, 24/24 offline; mock verify/mock_v025c.png, mock_full_v025c.png): user: multiplier
  arm behind the highway, multiplier closer, rock meter a bit left / SP a bit right (mostly on WoR's thick bevel,
  a sliver over its thin rail). RAIL_Z['nixie'] = 0.05 (badge image under the highway surface 0.1; streak lights keep
  +10), BADGE/LIGHT_SHIFT (-1,-17) (3 px closer + 2 to cancel the SP tube move), RAIL_OUTSET (-9.4, +9.2).
  Dark-metal mod now 5 materials (cups removed; assert fixed). The WoR border itself is NOT in the build yet
  (gem-pak route still to implement); the mock paints it.
- v0.25d options (mock only; verify/mock_tilt_v025d.png): user: tubes slightly mis-angled vs the border, lean their
  tops in towards the highway, and move them a bit further out. Cause: tubes were aligned to the DE border's centre
  line, but WoR's 388dd606 bevel converges towards its inner edge going up (bevel centre 23.5 texels from the inner
  edge at v480 vs 10 at v100 -> up to ~2.7 deg steeper). New RAIL_TILT (deg, applied in on_border, about
  RAIL_ALIGN_D). Options (tilt, extra out px): 1 (1.0,1.5), 2 (1.5,1.5), 3 (2.0,2.5), 4 (2.7,2.5); the multiplier
  badge/lights stay at the v0.25c position (BADGE_SHIFT recomputed per option). Defaults in the file unchanged.
- v0.25e (built with defaults; options mock only): user picked tilt 1.5 + 2.5 px out -> RAIL_TILT 1.5, RAIL_OUTSET (-11.9,+11.7), BADGE/LIGHT_SHIFT (-2.25,-19.45) keep the v0.25c badge position. New knobs: STAR_OVERLAY_PX (gold outline/shine/glow growth, default 0), SCORE_TEXT_K (score digits, default 1.0, kept on the same line). Mock verify/mock_star_score_v025e.png: star +1/+2/+3 px, score 97/94/91%. 24/24 offline.
- v0.25f (built, NOT installed, 24/24): user: SCORE_TEXT_K 0.85, STAR_OVERLAY_PX 3. Star-count options mock verify/mock_star_score_v025f.png (0.78 now / 0.81 / 0.84 / 0.87); STAR_NUM_K still 0.78 pending the pick.

### v0.25 INSTALLED (2026-10-04 ~23:17), not yet tested in game
- User picks: SCORE_TEXT_K 0.85, STAR_OVERLAY_PX 3, STAR_NUM_K 0.87, RAIL_TILT 1.5, RAIL_OUTSET (-11.9,+11.7),
  BADGE/LIGHT_SHIFT (-2.25,-19.45), black backing + gap fill, tube shadows, per-element tints, multiplier badge at
  z 0.05 (arm behind the highway), shaped SP segments, star gradient bg.
- WoR highway border: DATA/PAK/gems_ghwor_hud.pak.xen = DE gems_ghwor.pak tex dict (31 records byte-identical, via
  tools/texdict.py) + WoR_HUD_border (388dd606, DXT5 via png2img). WoR_HUD_Load repoints the WoR gem theme pak link
  (AddToGlobalStruct af130dc4 field 8a5ce489 = {name "gems_ghwor_hud"}); theme: 18f90ff6 = WoR_HUD_border,
  sidebar_x_scale 4.6, offsets -/+21.3 (ESTIMATES from the DE sidebar01 width; calibrate from the first in-game shot).
  Needs GemTheme=ghwor; with another gem theme the border texture is missing.
- WoR_HUD_DarkMetal installed (5 materials, 0.58). Shader: Toe 0.12, DOFBlur 3.5. GHWTDE.ini GH5_Highway still set.
- Risks for this test: border texture lookup from the gem pak, border width/offset, pak-link override timing (mod
  Load runs at boot; gem paks load per song), SP segment containers, tube z vs border.
- v0.25 CRASHED at song start (user, 23:19): log ends at the 2nd update_hud_layout right after setup_highway; gem
  pak gems_ghwor_hud loaded fine and the game took Sidebar texture 0x245d998a (= WoR_HUD_border). Dumps: AV c0000005
  at GHWT_Definitive.exe+0x19e766 (new; font crash was +0x100fab). Diagnostic v0.25b installed: SP_SHAPED False
  (v0.21 sprite segments), everything else kept incl. the WoR border. Log copy: verify/crash_v025/debug.txt.
- v0.25b test (verify/session_v025b, 33 shots, clean exit): NO crash -> the v0.25 crash was the shaped-SP
  ContainerElements receiving the DE tube texture/scale. WoR border renders from the gem pak. Measured (g17, canvas
  px): visible border ~49 px at y 680 (L 341-390, R 890-939) vs 28 target; centre 8 px inward of the mock's -> next:
  BORDER_X_SCALE 4.6*28/49 = 2.6, BORDER_OFFSET 21.3 + 8.1 = 29.4 (assumes scaling about the sprite centre).
  Rock tube glass reads black in game (RAIL_TINT_L 0.59 over the black backing) while GH5 shows dim red/yellow.
- v0.26 (built, NOT installed, 24/24; mock verify/mock_v026.png, mock_full_v026.png). Root cause of the black tubes:
  desc_gen wrote z_priority with 2 decimals, so the black backing (3.015) became 3.02 = the tube art's z and drew
  over it in game; now 4 decimals. RAIL_TILT 1.75, RAIL_TINT_L 0.85, RAIL_TINT_R 1.0, BADGE/LIGHT_SHIFT (-4.05,-19.87)
  (2 px closer, tilt compensated), STAR_K 1.14 + STAR_NUM_K 0.826 (whole star group -5%), BORDER_X_SCALE 2.6,
  BORDER_OFFSET 29.4, SP_SHAPED False (sprite segments; shaped fill deferred to the plugin).
- v0.26 INSTALLED (user: score back to SCORE_TEXT_K 0.90). Collector -> verify/session_v026.
- v0.26 test (verify/session_v026, 35 shots, clean exit): tubes visible (z fix works), unlit rock sections dim, border ~28-30 px and close to the mock, SP fill full/partial OK, star/score as mocked. Comparison verify/ingame_v026.png. During SP activation the DE's sidebar glow (Mat_sidebar_GLOW_01) draws a wide cyan band at the border (scaled with sidebar_x_scale).
- 2026-10-05: GHWTDE.ini Preferred{Guitarist,Bassist}Highway=GH5_Highway (my 10-04 test) cleared back to empty (user:
  the GH5 highway shouldn't be forced). Face "pixelated shadows": PPFX_SSDO in the GHWoR preset runs at half res
  (pSSDOLOD=.5) and its noise texture ssdonoise.png is missing (ReShade.log ERROR) -> blotchy occlusion; deeper Toe
  makes it more visible. Proposed fix, not applied. Mocks: verify/mock_border_v027.png (border 0/4/8/12 px in, meters
  follow), verify/mock_count_v027.png (0.78/0.75/0.72), verify/mock_sp_slant_v027.png (SP_SLANT_DEG 8.3: partial
  fill top edge level like the divider; currently set in the file, built not installed). 2nd-song lights: NOT fixed
  (gem pak also stays resident: "0x8a5ce489 already loaded").

### v0.27 INSTALLED (2026-10-05)
- User picks: border 12 px closer (BORDER_OFFSET 29.4 -> 17.4, ~1 unit = 1 px at y 680), meters follow:
  RAIL_OUTSET (-11.9,+11.7) -> (0.1,-1.8) (SP 1.5 px further in than the 12 px mock so its gap to the border matches
  the rock meter's, 3-4 px; check verify/mock_sp_align_v027.png). STAR_NUM_K 0.826 -> 0.8075. SP_SLANT_DEG 8.3
  (slanted partial-fill cut, approved). 24/24 offline.
- Shader: PPFX_SSDO removed from GHWoR.ini Techniques (face blotches); settings kept, backup
  backups/GHWoR.ini.before-ssdo-off-20261005-022315. Re-enable by adding PPFXSSDO@PPFX_SSDO.fx back to Techniques.
- GHWTDE.ini Preferred{Guitarist,Bassist}Highway=GH5_Highway again (user, for testing).

### v0.28 INSTALLED (2026-10-05)
- v0.27 test (verify/session_v027b, 57 shots, clean): tubes matched the v0.27 mock within 1 px, but the WoR border
  lands 8.5 px further OUT in game than the mock drew it (edge correlation, 4 shots, both sides) -> tubes sat on the
  thin rail. Mock border for BORDER_OFFSET 17.4 is inner edges 396.7 / 883.3 at y 638 (verify/_bm_tmp/bgame.png).
  RAIL_OUTSET (0.1,-1.8) -> (-8.4,+10.7) (SP +4 px more, user pick from verify/mock_sp_shift_v028.png).
- SP 50% now ends at the half divider: SP_FILL_SPLIT (lower 3 segments tube end -> divider row 106.9, upper 3 divider
  -> top); evenly spaced segments ended 13 px below the needle. Slant margin per segment scales with its height
  (one shared texture). 25/75% stop mid-segment: the DE's y-scale squashes the slant (plugin item).
- STAR_NUM_K 0.80. 2nd-song: stock white streak-light blocks confirmed in song 2 (plugin item).
- Shader: SSDO back ON at full res (pSSDOLOD=1; user: faces too flat with it off). Backup of the off state:
  backups/GHWoR.ini.ssdo-off-*.

### v0.29 INSTALLED (2026-10-05)
- v0.28 test (verify/session_v028b, one song, clean): tubes on the thick bevel, star count/score fine, faces have depth
  with SSDO at full res. User: meters still a bit too on the highway -> RAIL_OUTSET (-8.4,10.7) -> (-11.4,13.7) (3 px
  both sides, mock verify/mock_meters_out2_v029.png). STAR_NUM_K 0.80 -> 0.78 (user).
- User rule: the collector is only started on request, detached with no notifications (memory ghwt-collector-no-background).

### v0.30 (built, NOT installed) + WoR preset shaders installed (2026-10-05)
- User: v0.29 meter positions perfect. HUD outer shadows option B (OUTER_SHADOW_RINGS 1.5/3/5/7.5 px at
  .18/.12/.08/.05, 8 black copies per ring of each target's own art, bias (1,1.5)); targets score_back, streak_box,
  star overlay, rm_back/sp_back (z 3.005). Tube bottom void: black tube silhouette slid down its axis in 1-px steps
  (TUBE_VOID, z 3.012); mock verify/mock_tube_void_v030.png (6/10/14 px), pick pending (file default 10).
- Shaders (user OK to download): the original preset (desktop rar) also runs vort_MotionBlur + AdaptiveTint, which
  weren't installed, and SSDO's ssdonoise.png was missing (blotchy AO). Installed: Textures/ssdonoise.png (GShade, 4x4),
  Shaders/vort/vort_MotionBlur.fx + Includes (vort_Shaders @164e63d, 2023-05, matches the preset's UI_MB_Amount keys),
  Shaders/Daodan/AdaptiveTint.fx + Stats/Tools/Canvas (Daodan317081 master/dev). GHWoR.ini Techniques now in the
  original order + GH5_Grade after Curves. Backup backups/GHWoR.ini.before-wor-shaders-*. SSDO still pSSDOLOD=1.

### v0.30 INSTALLED + add-on release build (2026-10-05)
- HUD v0.30: outer shadows B; tube-end void = 48 px soft black ball (WoR career_map circle_gradient_smooth_64,
  decoded to ghwor-extract/circle_png, shipped as WoR_HUD_void, z 3.003, at tube texture row 254 on the tube centre
  line). The 1-px silhouette extrusion was dropped (user wanted a blurred ball).
- 2nd-song lights: confirmed no data route. hud_widgets hard-codes bulb_textures HUD_score_light_*; HUD/gem paks stay
  on their mpm maps (unload_paks releases handles, maps only flush when another pak loads), z_in_game reloads per
  song after them; theme structs only carry a pak field (no callback). -> plugin.
- ghwt_bgfx add-on: NAME "Background-only shaders", debug tooling (F10 dump, F9 scrub, trigger file, overlay debug
  section) off unless [GHWT_BGFX] Debug=1. Built and installed (old copy in backups/).
- HANDOFF.md rewritten for the current state.

### v0.30 test (2026-10-05, verify/session_v030, 19 shots): songs much darker
- Menus identical to v0.28b (preset gated to gameplay), so the darkening is the new in-song effects: SSDO now runs
  properly with ssdonoise.png (full res, Amount 1.3 / Intensity 1.1) and vort_MotionBlur is new. AdaptiveTint FAILED
  to compile (X3020 in its debug pass) and never ran; removed from Techniques. GH5_Grade (Toe 0.12) was tuned on the
  old stack with broken SSDO. A/B keys added to GHWoR.ini: F5 SSDO, F6 vort_MotionBlur, F7 GH5_Grade.
  Backup backups/GHWoR.ini.before-ab-keys-*.
- Tube balls work in game (user); they need to sit higher, just under the tubes. Height mock on the in-game shot:
  verify/mock_void_height_v031.png (VOID_ROW 254 now, A 236, B 218, C 200, D 182).
- v0.31 INSTALLED: VOID_ROW 254 -> 218 (balls 36 rows up, user pick B). Collector -> verify/session_v031.

### v0.32 (in source, NOT built/installed) 2026-10-05
- User on v0.31 test: shader stack "perfect" (no change). Ball too high -> VOID_ROW 218 -> 236 (18 rows up, set in
  wor_1g.py). Wider/blurrier HUD shadows: add_outer_shadows now uses 12 copies per ring for radii >= 8 px; ring options
  mocked in verify/mock_shadow_wide_v032.png (B now / C / D / E), pick pending.
- v0.32 INSTALLED: shadow option D (rings 2/4.5/7.5/11/15/19 px), VOID_ROW 236. Collector -> verify/session_v032.
- v0.33 INSTALLED: shadows B x0.2 (user), balls z 0.04 (under the highway surface, option 1). Not yet tested.
- v0.34 INSTALLED: RAIL_OUTSET (-11.4,13.7) -> (-13.4,15.7) (tubes 2 px further out, user pick). Plugin notes (x1 pink lights etc.) saved in ghwt-wor-hud/PLUGIN_NOTES.md.
- v0.35 INSTALLED: tube ball 28 px, circle_gradient_64 (harder), 2 stacked copies (user: even harder), z 0.04.

### Refactor (2026-10-05, repo github.com/jgoa156/ghwtde-gh5wor-hud-mod)
- Build output byte-identical before/after (tools/build_hashes.py, 12 files). Offline tests 24/24.
- tools/paths.py holds every machine path (env overrides); build.py, tools and tests use it. Game assets stay out
  of the repo.
- wor_1g.py: dead code removed (shaped SP segments, SP frame, old sidebar options, flags that were always on,
  history constants; history stays here). make_rails() rebuilds the rails after a settings change.
- build.py: matching dead branches removed; wor_art keeps crop_to / flip_h / slant_band.
- Mocks: tools/mock.py (variants as NAME=expr, crops tubes/tube-ends/score/full, --gh5, --shot) over
  verify/mock_inputs/base.png; tools/mock_base.py rebuilds that base (reproduces it exactly). Removed one-offs:
  border_mock, wor_import, star_measure.
- Add-on source moved in as addon/ (deps not committed); MODLOG / HANDOFF / PLUGIN_NOTES / ADDON_PLAN in docs/.

### v0.36 + HUD fixes plugin 1.0 (2026-10-05, built, NOT installed: the game was running)
- User OKs: pink x1 set (GH3:WoR lights luminance-tinted with WoR's x1 colour 255,180,180; off state stays grey),
  Ultimate ASI Loader v9.7.4 (Ultimate-ASI-Loader-NoPDB.zip, x86 dinput8.dll sha256 ec2f4824...617ab), Mod.ini
  author Guilherme Almeida.
- Theme pak: + WoR_HUD_light_{0,1,2}{_pink,'',_green,_purple,_blue}; light elements start on WoR_HUD_light_0.
- plugin/wor_hud_fixes.asi: detour of set_lights 0x476590 for widgets whose first light element's texture (+0x214)
  is one of ours; WoR mapping x1 pink / x2 orange / x3 green / x4 purple / SP blue with the game's mark maths.
  7 byte-checked sites + the 0.5 constant; inert on mismatch. Log: <game>\wor_hud_fixes.log.
- To install: dinput8.dll + wor_hud_fixes.asi into the game folder, python build.py --install.
- v0.37 INSTALLED (game closed): STAR_NUM_K 0.78 -> 0.77 (user); dinput8.dll (ASI loader) + wor_hud_fixes.asi copied to the game folder. Not yet tested in game.
