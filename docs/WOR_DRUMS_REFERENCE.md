# WoR drums: reference notes (2026-10-06)

Source: user clip `Video Project 1.mp4` (WoR drums, 1920x1080, 30 fps, 72 s), compared with the DE's WoR gem theme
(`gems_ghwor.pak.xen`, 31 textures) and a DE drums run with the mod (screenshot 52).

- HUD: identical to guitar (rock meter tube left, star power tube + multiplier badge right, score box, streak box).
  Our `hud_1g` layout already covers a single drummer (the DE uses hud_1g for any one-player highway).
- Lanes: 5, red / yellow / blue / orange / green, same order as the DE's 5-lane drums.
- Gems: the same silver-capped discs as guitar, lane coloured. Strikeline: the same coloured rings.
- Kick: a silver bar split into 5 segments across the highway (DE gems_ghwor 16fca12b, 512x64). Star power kick:
  teal bar (DE 488778d0). Looks complete; confirm in a DE drums run once the HUD textures load.
- Not in our HUD yet:
  - star bar tip glow: a white glowing dot at the gold bar's leading edge (WoR star meter `star_tip_FX`:
    `HUD_star_lead` sprites, texture `hud_progression_bar_lead`, Add);
  - song progress bar above the score box: thin bar with the same glowing tip (WoR `progress_container`,
    `hud_song_progression_front`, `progress_bar`, `hud_progression_bar_lead`). We hide the DE's song-time bar today.
- The DE drums run (screenshot 52) showed "MISSING TEXTURE" on all our elements: the DE had loaded the stock HUD pak
  (hud_ghwt_withtime) instead of hud_ghwor for that session (see MODLOG, raw PNG revert). Not drums specific.
