# GH5 / WoR HUD: release notes

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
