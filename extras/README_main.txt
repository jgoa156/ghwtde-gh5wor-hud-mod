GH5 / Warriors of Rock HUD for Guitar Hero World Tour: Definitive Edition  (BETA)
=========================================================================
By WitchDoctoR

A Guitar Hero 5 / Warriors of Rock style HUD: rock meter and star power tubes along the highway, the WoR
multiplier, score box, star meter and fonts, laid out from GH5 gameplay. Single player (guitar, bass, drums).

REQUIREMENTS
  - Guitar Hero World Tour: Definitive Edition.
  - ReShade 6.x (32-bit, Direct3D 9) for the WoR shader look (lighting, bloom, motion blur, GH5 colour grade).
    The HUD itself works without it. A ready-to-use copy is included in the optional folder (see below).

Install: extract this archive into the game folder (the one with GHWT_Definitive.exe). It adds:
  DATA\MODS\WoR_HUD\            the HUD theme mod (no in-play messages, darker highway metal, like GH5)
  DATA\PAK\hud_ghwor.pak.xen    its textures and fonts
  DATA\PAK\gems_ghwor_hud.pak.xen  the WoR highway border (+ WoR star power strike), Warriors of Rock gems
  DATA\PAK\gems_ghwt_hud.pak.xen, gems_gh3_hud.pak.xen, gems_flat_hud.pak.xen
                                the WoR highway border for the other stock gem themes
  wor_hud_fixes.asi             native fixes (smooth animated star power, WoR star power highway, note-streak lights)
  ghwtde_ultrawide.asi, ghwtde_ultrawide.ini
                                GHWT:DE Ultrawide Fix 1.1 (see ULTRAWIDE SCREENS below); does nothing at 16:9
  dinput8.dll                   Ultimate ASI Loader (MIT), loads the .asi files
Then in game: Options > HUD Theme > "Guitar Hero: Warriors of Rock". Gem Theme = Warriors of Rock gives the full
WoR look; the WoR highway border also shows with the other stock gem themes (custom gem-theme mods keep their own).
If you already use an ASI loader (dinput8.dll), keep yours and only add the .asi files.
Uninstall: delete those items.

OPTIONAL: "Optional - ReShade (WoR shaders)" folder
  Copy its CONTENTS next to GHWT_Definitive.exe:
    d3d9.dll           ReShade 6.8.0 (BSD-3, crosire)
    ReShade.ini        points ReShade at the preset and shaders below
    GHWoRHudModPreset.ini  the Warriors of Rock preset (based on Behon's GH5WORStyle v2, built on Ricochet27's
                       GH5 / WoR ReShade; credits in THIRD_PARTY_LICENSES.txt)
    reshade-shaders\   the shaders the preset uses (licenses in THIRD_PARTY_LICENSES.txt). Not included:
                       qUINT (MXAO, depth of field, sharpen): tick "qUINT" in the ReShade installer for those
    ghwt_bgfx.addon32  background-only add-on: effects apply to the venue, never the HUD or highway
  Already have ReShade? Keep your d3d9.dll and ReShade.ini; copy only GHWoRHudModPreset.ini, ghwt_bgfx.addon32
  and the shaders and the shaders, then pick GHWoRHudModPreset.ini in the ReShade overlay (Home key).

RECOMMENDED (separate downloads, by WitchDoctoR)
  - GHWT:DE All Main Menu Music: the main menu music of ten Guitar Hero games (Warriors of Rock included) in one
    menu music mod; switch games off in its menumusic.ini. https://github.com/jgoa156/ghwtde-all-main-menu-music

KNOWN ISSUES (beta)
  - Switching HUD theme in the options can crash the game. Pick the theme and restart if needed.
  - Band, multiplayer and microphone layouts still use the stock layouts.
  If something else breaks, please send wor_hud_fixes.log (game folder) and a screenshot.

ULTRAWIDE SCREENS
  On screens wider than 16:9 the game stretches the HUD and menus sideways and zooms the 3D view in (the highway
  runs off the bottom). ghwtde_ultrawide.asi (GHWT:DE Ultrawide Fix 1.1, no ReShade needed) keeps 16:9's vertical
  field of view for the 3D view and draws the HUD and menus as a centred 16:9 picture, with full-screen backgrounds
  filling the screen and side panels pinned to the screen edges. Settings in ghwtde_ultrawide.ini. Updating from
  an older HUD zip: delete ghwtde_ultrawide.addon32 from the game folder. Source and standalone release:
  https://github.com/jgoa156/ghwtde-ultrawide-fix
