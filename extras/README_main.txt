GH5 / Warriors of Rock HUD for Guitar Hero World Tour: Definitive Edition  (BETA)
=========================================================================
By WitchDoctoR

A Guitar Hero 5 / Warriors of Rock style HUD: rock meter and star power tubes along the highway, the WoR
multiplier, score box, star meter and fonts, laid out from GH5 gameplay. Single player (guitar, bass, drums).

Install: extract this archive into the game folder (the one with GHWT_Definitive.exe). It adds:
  DATA\MODS\WoR_HUD\            the HUD theme mod
  DATA\PAK\hud_ghwor.pak.xen    its textures and fonts
  DATA\PAK\gems_ghwor_hud.pak.xen  the WoR highway border
  wor_hud_fixes.asi             native fixes (smooth animated star power, note-streak lights)
  dinput8.dll                   Ultimate ASI Loader (MIT), loads the .asi
Then in game: Options > HUD Theme > "Guitar Hero: Warriors of Rock", Gem Theme = Warriors of Rock.
If you already use an ASI loader (dinput8.dll), keep yours and only add the .asi.
Uninstall: delete those items.

KNOWN ISSUES (beta)
  - Switching HUD theme in the options can crash the game. Pick the theme and restart if needed.
  - The theme does not apply in Career mode yet.
  - Band, multiplayer and microphone layouts still use the stock layouts.
  If something else breaks, please send wor_hud_fixes.log (game folder) and a screenshot.

Optional files (separate downloads):
  Background-only shaders     keeps ReShade effects off the HUD and highway (needs ReShade).
