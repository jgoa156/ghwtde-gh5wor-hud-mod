# GH5 / WoR HUD: release notes

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
