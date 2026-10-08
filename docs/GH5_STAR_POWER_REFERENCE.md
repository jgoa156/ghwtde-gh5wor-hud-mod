# GH5 star power meter: reference analysis (2026-10-06)

Source: user clip `Video Project.mp4` (GH5, 1920x1080, 30 fps, 81 s; full star power lifecycle), measured frame by
frame along the tube (1330,900) -> (1230,700), plus WoR's own files (same HUD as GH5):
`uidesc_hud_sidebar_starpowermeter`, `scripts/guitar/hud/hud_widgets` (HUD_attach_widget_sidebar_starpowermeter),
`scripts/guitar/guitar_starpower`, `scripts/guitar/guitar_material` (decompiled to `ghwor-extract/matqb`).

## Timeline of the clip

| Time | Event | What the meter does |
|---|---|---|
| 3.70 s | first star phrase completed | fill appears in ONE frame (no growth animation) to ~25%; cyan lightning bolts flash beside the tube for ~0.25 s (3.77-3.97) and white sparkle stars drift for ~0.8 s (to ~4.6) |
| 3.7-39.4 s | charging (< 50%) | flat, darker teal fill, RGB ~(30,117,105); only the bottom tip is brighter, ~(68,170,159), a soft bottom glow |
| 39.47 s | crosses 50% (ready) | jumps in one frame to ~75%; burst of white/cyan sparks out of the fill top for ~0.4 s (39.47-39.87); from the same frame the whole fill switches to the "ready" look |
| 39.5-63.7 s | ready, idle | bright cyan RGB ~(127,231,228), top of the fill near white ~(179,243,234) with a halo spilling outside the tube; mottled "plasma" texture moving in place (no scrolling along the tube; frame differences peak every 3 video frames) |
| 63.8 s | activation | whole-highway teal flash (~0.2 s), highway borders turn neon teal, multiplier x4 -> x8 |
| 63.8-73.8 s | active, draining | fill shrinks continuously (smooth), keeps the ready look, white-hot cap at the fill top follows the level |
| 73.87 s | empty | fill gone in one frame; tube back to dark |

## How WoR builds it (uidesc_hud_sidebar_starpowermeter)

| Element | Art | Driven by (hud_widgets) |
|---|---|---|
| Fill_Pre_SP | SP_Fill01, Add, alpha 0.6 | scale y 0->1 over SP 0-49 |
| Fill_Post_SP | SP_Fill01, Add, alpha 0.6 | scale y 0->1 over SP 50-100 |
| Fill_Post_SPFX | material Mat_Sp_Ready_Fire | scale y 0->1 over SP 0-100; alpha by SEStarPowerMeterFX from 50 |
| Fill_Fudge_hider | SB_Tubeglow01, Add, alpha 0.5 | on when SP >= 1 (the charging bar's soft bottom glow) |
| needle_white / needle_color | SB_Tubeglow01, Add (1.0 / 0.5) | SEStarPowerMeterFX from 50: the white-hot cap at the fill top |
| needle_container | - | pos (12,-2) -> (19,-205), scale (1.1,0.75) -> (0.7,1.0), rot -5 -> 0 over SP 0-100 |
| Tesla_needle, RP_Tesla_FX_LV1/LV2 (FX_LV1/LV2) | Mat_Lightning_Arc_Anim02 / _OB_02 | Tesla needle follows SP 0-49; RP_Tesla_FX scale (0,1) -> (1,1.5) over SP 0-100 |
| RP_Tesla_Spark_FX01/02 | Mat_Lightning_ball_anim01 | spark balls (alpha 0 by default) |

## Materials (guitar_material)

- **Mat_Sp_Ready_Fire**: template Fire2D. `SP_Fill_Glow02.dds` (basic_gems_png/a1c363bd.png, 64x128, a soft
  vertical glow bar) distorted and masked by a scrolling 3D noise volume `noise_32x32x32.dds` (tiling 1,2,1; speed
  X 0.1, Y 0.4, Z 1.1; mask distortion 0.21/0.20; colour distortion 0.03). This is the moving plasma texture.
- **Mat_Lightning_Arc_Anim02**: AnimatedTexture_UI, loop, Add. `Lightining_arc_anim01.dds`
  (basic_gems_png/0c30522c.png, 16 frames), **20 fps**. `_OB_02` is the same at colour x2, alpha x4.
- **Mat_Lightning_ball_anim01**: `Ball_lightning01.dds` (basic_gems_png/249c3fc1.png, 4x4 cells), **20 fps**, loop.

## Events (guitar_starpower)

- `show_star_power_ready` (SP reaches 50%): the "star power available" sound, then `lil_SP_Squirt` when no star
  power was used yet: a 2D particle burst at the needle container (the fill top), material
  `sys_Particle_Spark01`, colour white -> cyan (0,255,255) fading to alpha 0, scale 1.25 -> 0.25, emitted for 0.25 s
  (rate 0.01 s, spread 180 deg around 66 deg, velocity 3.3, friction (0,12)), each particle lives 0.55 s. These are
  the sparks at 39.47 s.
- Activation: `Create_Highway_Star_Power_Effect` (highway and sidebar glows `Mat_sidebar_GLOW_02`, Pandora colours
  at multiplier 3+/6+) and `Do_StarPower_TeslaFX` (tesla arcs on the band member). Highway scope, not the meter.
- The 3.70 s lightning beside the tube comes with the star phrase completion (highway/gem effect), not the meter.

## Consequences for our meter

1. GH5 does not tween the fill: it jumps in one frame. What makes it feel alive is the burst at the fill top and the
   ready look switching on. (A short tween is still an option; the user asked for smoother growth.)
2. Below 50%: flat dark teal plus a soft glow at the bottom only (Fill_Fudge_hider = SB_Tubeglow01).
3. From 50%: the plasma (SP_Fill_Glow02 x moving noise), bright cyan, plus the white-hot cap (SB_Tubeglow01 at the
   fill top, alpha 1.0 white + 0.5 colour). Ours can pre-render the Fire2D look into a flipbook and cycle it.
4. Animation rates: lightning and ball lightning 20 fps loops; the plasma is continuous noise (a 20 fps flipbook of
   it is close enough).
5. Ready burst: ~0.25 s of white -> cyan sparks out of the fill top, gone by ~0.8 s.

## Clone Hero / WoR star power on the DE (2026-10-08)

- The DE already ports WoR's highway star power look (`Create_Highway_Star_Power_Effect`: sidebar glows
  `Mat_sidebar_GLOW_02`, `Mat_Star03` star-outline particles drifting up the highway, spark/star particles) as DE script
  0x68e7427a in tb `guitar_starpower.qb`, gated by the global `af5331bb` (SectionQBKey, default `ghwt`). Values (DE
  options list c3cc2385 in menu 0xbb76de6b): `ghwt` "Guitar Hero: World Tour" (classic: sidebar arcs), `gh6_standard`
  (0x8f24bf5c) "WOR: Standard FX", `gh6_pandora` (0x273bb215) "WOR: SP Nova FX (Pandora)". When it is not `ghwt`,
  `setup_highway` (guitar_highway.qb) also hides the sidebar arcs (`sidebar_*_Lightning02`, alpha 0) - exactly the
  Clone Hero look (smooth cyan rails, star outlines, no side arcs).
- The materials it uses (`Mat_sidebar_GLOW_02`, `Mat_Star03`) are not in tb `guitar_material.qb`'s arrays; WoR textures:
  sidebar01_glow02 = basic_gems d96d3be3 (32x128 soft bar), Star03 = 42235207 (128 px outlined star). If the DE option
  shows missing textures, the mod can add both materials to the arrays it already replaces and ship the textures in the
  gem pak (key = checksum of `tex\models\highway\<name>.dds`), and set `af5331bb` from WoR_HUD_Load.
- Clone Hero clip (2026-10-08 02-24-49): activation at ~12.6 s turns the highway teal with glowing cyan rails and a
  short sweep of star outlines; phrase bolts as ours; while active, cyan gems and cyan-green hit flames.

### Result of the DE check (user, 2026-10-08): the "WOR: Standard FX" option does not exist / has no effect
- The DE ships the WoR highway effect script (0x68e7427a = Create_Highway_Star_Power_Effect, tb guitar_starpower.qb) and
  the value list c3cc2385, but: no script ever spawns 0x68e7427a (its hash occurs only at its definition in all extracted
  qb/exe/dll), no option entry references list c3cc2385 (menu 0x5c2f930d), nothing assigns the global af5331bb (default
  ghwt), and the materials it needs (Mat_Star03, Mat_sidebar_GLOW_02) are not defined in tb guitar_material.qb. It is an
  unfinished port.
- To clone the Clone Hero / WoR highway look the mod would have to: (1) define Mat_Star03 + Mat_sidebar_GLOW_02 in the
  material arrays it already replaces and ship their textures in the gem pak, (2) set af5331bb to gh6_standard
  (0x8f24bf5c) from WoR_HUD_Load (this also hides the sidebar arcs in setup_highway), and (3) get 0x68e7427a spawned at
  star power activation and killed at the end (Kill_Highway_Star_Power_Effect) with the player param: the plugin would
  detect activation (it already hooks the SP tube / IsStarPower) and spawn the script natively (needs the engine's
  spawn-script function located and called).
