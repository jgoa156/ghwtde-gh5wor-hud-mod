# GH5 / WoR HUD: release notes

## 0.51 (beta) - vocals

`GH5-WoR_HUD_0.51.zip` (plugin `wor_hud_fixes.asi` 1.82), on top of 0.50:
- **Vocals in the WoR style** (vocals only, and the vocalist in band): WoR's meter panel on the vocal highway (health
  lamps and needle, the "xN" multiplier, the phrase box, the star power strip on the highway line), the vocal highway
  at WoR's height with the dark lyric band, WoR's lyric font, sizes and colours, WoR-style notes, a green lightning
  now line (cyan in star power) with arrowheads, star power glow bands, the comet's purple miss sparks hidden, and the
  score box at WoR's vocals spot.
- **Star power tube** redone against WoR footage in every mode: WoR's teal while charging, a soft sloped and domed
  top edge, no top cap while charging, the charged glow and the bottom arc like WoR's, the fill kept inside the glass.
  Multiplayer tubes turn with their highway (2 and 3 highways) and use the same engine.
- **Score box:** wider digits, thousands separators in every mode, WoR's tip balls on the star bar and song line in
  every mode, WoR gold star bar and numeral.
- **Band:** the band multiplier bulb also at x1, with WoR's slide-in popup on every change; tubes on the third
  highway in front of it; rock needle stops as in quickplay.
- **Battle:** each player's rock tube is the band one, slots spaced and moved right, the collect flight of a new attack
  card ends in its slot.
- **Every theme:** purple drum fill; a practice-mode crash guard; the ReShade preset uses the original's blur.
- Bundles **GHWT:DE Ultrawide Fix 1.2** (Hor+ on one more projection: band close-ups no longer zoomed).
- Known: the vocalist's star power strip may stay empty; star power phrase notes have no blue blur yet.

## 0.50 (beta) - multiplayer

`GH5-WoR_HUD_0.50.zip` (plugin `wor_hud_fixes.asi` 1.52), on top of 0.49:
- **Every multiplayer layout in the WoR style**, by the book with singleplayer: band (2 / 3 instrument highways, with
  or without vocals), face-off and pro face-off get the 1-player rock tube, star power tube and multiplier on each
  highway's outer border, at each highway's angle, with the same layering, shadows and effects. Every star power tube
  runs the singleplayer engine (smooth fill, glow, 60 fps plasma, burst). Career face-off (boss battles) has no star
  power tube or score boxes.
- **Versus score boxes:** WoR's 1v1 dial colours (P1 blue / P2 red), each player's note streak and score, the streak
  sized to its digit count.
- **Battle:** each player's rock tube is the band one (same position on the highway, layering and effects), the
  needle follows health, attack slots are WoR streak-meter visors on the rail, behind the highway, aligned with the
  rock tube's top; new attack cards go straight into the big slot.
- No in-play messages in any mode; WoR's 6th star at 100% notes in quickplay; score separators in 2-player modes.
- Crash fixes: switching face-off -> pro face-off (menu desc swaps), orphan HUD elements.
- Bundles **GHWT:DE Ultrawide Fix 1.1** next to the HUD plugin (`ghwtde_ultrawide.asi` + `.ini`, loaded by the same
  ASI loader; no ReShade needed): the 3D view keeps 16:9's vertical field of view, so the highway is no longer zoomed
  in on ultrawide screens. Updating: delete `ghwtde_ultrawide.addon32` from the game folder.
- Recommends **All Main Menu Music** (one menu music mod with ten games' menu songs).
- Known: the microphone's streak meter shows the WoR instrument multiplier art (WoR vocals layout to come).

## 0.49 (beta)

`GH5-WoR_HUD_0.49.zip` (plugin `wor_hud_fixes.asi` 1.31), on top of 0.48:
- Popup title in WoR's brown (#3f352a), a little lower; failed box: COMPLETED / ON at their natural width, the
  percent and difficulty in WoR's red (#e1474e).
- Bundles **GHWT:DE Ultrawide Fix 1.0** (optional folder).
- Menu music links point to the [All Menu Songs Installer repo](https://github.com/jgoa156/ghwtde-all-menu-songs-installer),
  which now also holds the GHWoR Main Menu Music mod.

## 0.48 (beta) - the WoR menus

One drop-in zip, `GH5-WoR_HUD_0.48.zip` (plugin `wor_hud_fixes.asi` 1.31). New since 0.47, all picked as
"Guitar Hero: Warriors of Rock" in the DE's theme options:

- **Helper pills** (button prompts) and the gamertag pill in WoR's colours.
- **Loading screen:** WoR's art, animated plate and spinning load ball (16:9 with black bars on ultrawide).
- **Menu popups:** WoR's frame and banner title, WoR fonts and colours, the red brush bar behind the selected option,
  black background; messages at one size.
- **Failed / song ended box:** WoR's layout (song title, COMPLETED / percent / ON / difficulty in WoR's colours).
- **Pause menu:** WoR's look above the gameplay, song info in title case.
- **YOU ROCK:** WoR's whole sequence (exploding letters with gravity, lightning bolts, glow, explosion) and WoR's
  YOU ROCK sound.
- **Star power:** WoR's Tesla arc on the gems and the burst particles at WoR's size; Band Hero's star power sounds
  (the same as WoR's) by default.
- **Rock needle** follows WoR's LED art (bottom at fail, colour edges at the colour changes, top at full health).
- **Score** with thousands separators.
- Menu music is no longer in this zip: get the GHWoR Main Menu Music mod or the All Menu Songs Installer (below).

**Recommended (separate):**
[GHWoR Main Menu Music](https://github.com/jgoa156/ghwtde-all-menu-songs-installer/tree/main/ghwor-menu-music),
[All Menu Songs Installer](https://github.com/jgoa156/ghwtde-all-menu-songs-installer).

### Known issues
- Face-off can crash; face-off / battle HUDs are not adjusted for ultrawide.
- Band, multiplayer and microphone layouts still use the stock DE layouts.
- The DE's star power highway glow leaks slightly above and below the highway.

## 0.40 (beta, one zip)

Everything ships in one drop-in zip, `GH5-WoR_HUD_0.40.zip`:

- **HUD theme:** "Guitar Hero: Warriors of Rock" (1 guitar / bass / drums player).
  - GH5 look: no in-play messages.
  - Darker highway metal.
  - WoR highway border (Gem Theme = Warriors of Rock).
  - The former No messages and Dark metal add-ons are now part of the theme.
- **HUD fixes plugin:** `wor_hud_fixes.asi`, loaded by the Ultimate ASI Loader (`dinput8.dll`).
  - WoR streak light colours, including pink at x1.
  - Textures stay correct on the 2nd song.
  - Smooth, animated GH5 star power.
  - Theme switch crash fix.
- **Optional - ReShade (WoR shaders):** a separate folder in the zip.
  - Contents: ReShade 6.8.0, the GHWoR preset and its shaders.
  - The background-only add-on keeps effects off the HUD.

**Requirement:** ReShade is needed for the shader look only; the HUD works without it.

### Known issues
- The game sometimes crashes, and not only on theme switch. Under investigation.
- The theme does not apply in Career mode yet.
- Band, multiplayer and microphone layouts still use the stock DE layouts.

## Planned
- Star power look: teal highway wash, neon borders, activation burst, gem lightning.
- WoR layouts for multiplayer and vocals; drums gem theme check against WoR footage.
- Score thousands separators; Helper Pill and Menu Popup themes.
- Crowd models from WoR (needs a Xbox 360 skin converter); drummer animations (very optional).
