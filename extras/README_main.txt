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
  DATA\PAK\gems_ghwor_hud.pak.xen  the WoR highway border
  wor_hud_fixes.asi             native fixes (smooth animated star power, note-streak lights)
  dinput8.dll                   Ultimate ASI Loader (MIT), loads the .asi
Then in game: Options > HUD Theme > "Guitar Hero: Warriors of Rock", Gem Theme = Warriors of Rock.
If you already use an ASI loader (dinput8.dll), keep yours and only add the .asi.
Uninstall: delete those items.

OPTIONAL: "Optional - ReShade (WoR shaders)" folder
  Copy its CONTENTS next to GHWT_Definitive.exe:
    d3d9.dll           ReShade 6.8.0 (BSD-3, crosire)
    ReShade.ini        points ReShade at the preset and shaders below
    GHWoR.ini          the Warriors of Rock preset (F5 SSDO, F6 motion blur, F7 GH5 grade)
    reshade-shaders\   the shaders the preset uses (licenses in THIRD_PARTY_LICENSES.txt)
    ghwt_bgfx.addon32  background-only add-on: effects apply to the venue, never the HUD or highway
  Already have ReShade? Keep your d3d9.dll and ReShade.ini; copy only GHWoR.ini, ghwt_bgfx.addon32 and the
  shaders, then pick GHWoR.ini in the ReShade overlay (Home key).

KNOWN ISSUES (beta)
  - Switching HUD theme in the options can crash the game. Pick the theme and restart if needed.
  - The theme does not apply in Career mode yet.
  - Band, multiplayer and microphone layouts still use the stock layouts.
  If something else breaks, please send wor_hud_fixes.log (game folder) and a screenshot.
