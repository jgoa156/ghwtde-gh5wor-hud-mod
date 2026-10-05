# Native plugin notes (HUD fixes .asi) — collected 2026-10-05

Scope when we start the plugin (Ultimate ASI Loader, `dinput8.dll`; in-memory patches only, byte-signature checked,
inert on unknown DE builds, active only with the WoR HUD theme). Game: GHWT_Definitive.exe, GHWT:DE 1.4.3.5.

## 1. x1 streak lights pink (user asked 2026-10-05: "why can't the 1x points be pink like the original?")

- The note-streak lights are driven by the DE script `hud_widgets` (`senotestreaklights` HUD widget). It carries a
  `bulb_textures` array of FOUR sets, each three textures (state 0/1/2):
  plain `HUD_score_light_0/1/2`, `_green`, `_purple`, `_blue`. The script is hard-coded; theme tables can't change it.
- The DE picks the set by multiplier colour; x1 and x2 share the plain set (the original GH5/WoR: x1 pink, x2 green,
  x3/x4 purple/blue). Our mod only supplies textures under those names (`STREAK_LIGHTS` in `tools/wor_1g.py`:
  `HUD_score_light_{0,1,2}{'', _green, _purple, _blue}` mapped to GH3:WoR images), so making the plain set pink would
  also turn x2 pink.
- Plugin job: find where `senotestreaklights` selects the bulb set from the multiplier (native code, near the exe
  function that handles `bulb_textures`) and either (a) give x1 its own set index with a new pink texture set shipped
  in `hud_ghwor.pak`, or (b) swap texture names for x1 at draw time.
- Source for pink: GH3:WoR streak light images in `C:\Users\rockb\ghwt-extract\gh3wor\global_png`
  (see `STREAK_LIGHTS` / build.py). Check which pink variant exists there before shipping anything.

## 2. Second-song texture reverts (streak lights fall back to stock blocks on song 2+)

- Cause (diagnosed 2026-10-04, re-checked 2026-10-05): `hud_ghwor.pak` and `gems_ghwor_hud.pak` stay resident on their
  pak-manager maps between songs ("already loaded. Adding handle"), while `z_in_game` reloads every song after them,
  so its stock `HUD_score_light_*` win the name lookup. Theme structs only carry a `pak` field; no per-song hook.
- Plugin job: re-register our light textures after `z_in_game` loads, or redirect the lookup. Logs:
  `verify/session_2nd_song`, `verify/session_v027b` (song 2 shows stock white blocks).

## 3. Shaped star power fill at 25/75%

- The DE tube widget sets texture AND scale on the element named by `glowN_texture`; the y-scale squashes our slanted
  fill cut on a partial segment (about half as steep, ~2 px low). Making that element a ContainerElement crashed the
  game (AV at exe+0x19e766). The plugin could draw a shaped fill itself.

## 4. Other plugin items

- Score thousands commas (native `seinttostring`).
- Star power activation look (no footage yet).
- Rules: ask before any game launch; verify with a mock first when it changes the layout.
