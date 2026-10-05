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

## RE findings (2026-10-05, GHWT_Definitive.exe image base 0x400000, PE timestamp 0x562b029a)

Note-streak lights widget `senotestreaklights` (QB key 36c22211), class vtable at 0xa11e98:
`[0x476580 type id, 0x476930 dtor, 0x476c30 init(params), 0x476700 on_value(streak)]`.

- **init 0x476c30**: params via CStruct getters (0x4d7800 / 0x4d7020): 0x4bb2084e desc_id -> resolved id at [w+8],
  0x67e6859a player -> [w+0xc], `bulb_textures` (c05f18e6) array copied into the CArray at [w+0x10]
  ([w+0x14] = count, [w+0x18] = data), `bulb_props` 0x88bacaf1 (light0..4_texture) -> five element pointers at
  [w+0x1c..0x2c] (resolved through 0x5f6160 on [w+8]). [w+0x30] = ok flag, [w+0x34] = last streak.
- **on_value 0x476700** -> **set_lights 0x476590(streak)**: mult = thunk 0x42be60(player-1, 1) (thiscall, ecx =
  [0xc0c770]); sp = thunk 0x4649d0(player-1) (ecx = [0xc0d77c]). Both thunks jump through the DE's own section
  (diabolus), so GHWTDE redirects them: call them, don't inline.
  Set: sp -> set 3 (blue); mult > 3 -> set 2 (purple); mult == 3 -> set 1 (green); else set 0 (base) => x1 and x2
  share the base set. Marks c = streak % 10 (10 when a positive multiple of 10, streak clamped to 30, <= 0 -> 0);
  full = int(c * [0xa0f028]) (0.5), half = full + (c & 1); light k: k < full -> state 2 texture, k < half ->
  state 1, else state 0. Each set is a CArray {?, count, data} (count 1 = value inline).
- **SetTexture 0x59e6d0** (thiscall on the element, arg = texture checksum): stores the checksum at
  [element+0x214], then looks the texture up by checksum (0x4fad90 on [0xd4e3c8]) -> this name lookup is where the
  stock z_in_game textures win on song 2.

WoR's own colours (WoR hud_widgets `combolights` led_colors, white LEDs tinted): x1 (255,180,180) pink,
x2 (243,169,64) orange, x3 (128,236,68) green, x4 (175,101,238) purple. GH3:WoR's light images (ours): base =
orange (254,201,66), _green, _purple, _blue; there is no pink set.

### Plan for the lights fix (one detour, fixes both #1 and #2)
- Ship our light sets under unique names (`WoR_HUD_light_{0,1,2}{_pink,'',_green,_purple,_blue}`), so the stock
  `HUD_score_light_*` in z_in_game can't shadow them on song 2. Pink = GH3:WoR base lights desaturated and tinted
  with WoR's x1 colour (needs the user's OK: it's a tint of extracted art).
- Our desc gives the light elements a marker texture (e.g. `WoR_HUD_light_marker`); a hook at the end of init reads
  [element+0x214] to tag WoR widgets.
- Detour set_lights: for tagged widgets, run the same math with WoR's mapping (x1 pink, x2 base/orange, x3 green,
  x4 purple, SP blue) and our names, calling SetTexture 0x59e6d0; otherwise call the original.
- Loader: Ultimate ASI Loader (dinput8.dll; the game imports DINPUT8.dll) + our .asi. Verify the bytes at every
  patch site and stay inert on any mismatch (other DE builds, or the DE already patching the same code).
