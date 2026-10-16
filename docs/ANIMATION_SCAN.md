# Animation scan: GH5 and WoR dumps vs the DE (2026-10-16)

Sources: GH5 = `E:\Dev\ghwt\gh5-extract\disc` (GoD extract), WoR = `E:\Guitar Hero - Warriors of Rock`, DE = the installed
game. Skeletal animation = `.ska.xen`; scripts = `.qb.xen`. Scripts of the scan: `perm_anims`, `frontend_anims`,
`L_DRUM_Loops_Standard_anims`, `qb.pak` of each game (extracted with the local GHSDK; scratch only).

## Skeletal animations (.ska)

| Category | GH5 | WoR | DE |
|---|---|---|---|
| Drum per-hit (pad pair, Q/M/S hit, L/R) `Drum_<padA><padB>_{Q,M,S}Hit_{L,R}` | 228 | 226 | **0** |
| Drum pad poses / other `drum_*` | 134 | 133 | 177 (`Drum_Andy_*_120` stance transitions) |
| Drummer character poses (`gh_drummer_*`, per-character default / difference) | 67 | 82 | 20 |
| DrumDroid (idle, outro, crowd interaction) | 25 | 13 | 0 |
| Tempo loops `drum_loop_{highenergy,loenergy}_{075,100,120}` | 6 (+ in `L_DRUM_Loops_Standard`, 0.88 MB) | 7 (in `anim_loops.pab`) | 0 (DE uses 186 stance anims, 4.99 MB) |
| Frontend / menu character anims (`gh_fe_*`) | 130 | 130 | 6 |
| Win / lose | 72 | 72 | 225 |
| Crowd | 0 | 0 | 263 |

Only 170 of the 1195 GH5 / 1187 WoR names also exist in the DE (1076 are shared between GH5 and WoR: same engine
generation). So the drum, DrumDroid and frontend sets are all new content for the DE.

### Why the drum anims are not a drop-in (confirms docs/DRUM_ANIMS_PLAN.md)

- GH5 / WoR drum a note with **script-driven hand blending**: `drummer.qb`, `drummer_controls.qb`,
  `drummer_functions.qb`, `drummer_tree.qb`, `drummer_hold.qb`, `drummer_hand_assignment.qb`, `drummer_printer.qb`
  (GH5) use `time_to_hit_*`, `pieces_value_*`, `priority_*_l/r`, `blend_hand_l/r`, `drum_hit`, anim-tree channels.
  The DE has **none of these files**; its drummer runs on tempo-matched stance loops (`drumanimpatterns`,
  `drumanimtransitions`, `animevents_tempomatching`).
- Porting = new playback scripting that needs the engine's anim-tree blend nodes, which may not exist in
  GHWT_Definitive.exe. Only an in-game test can tell; the plan's step 2 (one converted loop, 1 launch) is the cheap probe.
- Usable without new engine logic: GH5 / WoR **tempo loops** (`drum_loop_*`, 6 in GH5, 7 in WoR) and the
  per-character drummer poses, via a converter (WoR flag bit 31 = float time keys; same 128 bones as the DE).
  GH5 ska headers are the same family as WoR's (not yet checked for the float-time flag).

## Scripts (qb)

- GH5 qb files: 1246; WoR 1383; DE 1818. GH5 names missing from both WoR and the DE: **176**:
  - 113 `og_*` audio-visualizer venue presets (`av_presets`: `og_tunnel_*`, `og_enerdonut_*`, `og_frequency_*`,
    `og_lhc_*`, `og_dublin_encore_*`, ...). These are the audio-reactive backdrops behind the highway in the WoR clip
    (frequency lines, circles, tunnels). The DE has its own `av_presets` (`tb_*`), so a port needs the visualizer
    engine support first (not checked).
  - 24 `ui_*` (career gig info / select / venue select, gig complete, failed-three-times warning, import), 9 tutorial
    lessons, 7 `c_*_scripts` (score / multiplier / streak counters), 5 `goal_*`, medley (`guitar_medley*`), trivia,
    challenges, giglist, notetracker menu states.
- Menu / pause / loading / YOU ROCK scripts: GH5 and WoR have the same ones (`guitar_pause`, `freeplay_pause`,
  `generic_menu_animations`, `guitar_intro`, `guitar_transitions`); WoR's versions are already ported
  (0.47-0.49), WoR's differ from GH5's mainly in size (e.g. `guitar_pause` 3984 vs 7088 bytes, `guitar_intro`
  5356 vs 10096), i.e. WoR is the newer, richer version: GH5 adds nothing to port there.

## Recommendation

1. Drum anims: do the plan's converter + one-loop probe (needs one game launch, ask first). Start with WoR's
   `drum_loop_loenergy_100` (or GH5's `L_DRUM_Loops_Standard_anims` copy) mapped onto a DE loop slot.
2. UI animations: nothing left to port from GH5; check only the 24 `ui_*` GH5 files if the user wants career screens.
3. `og_*` visualizers: separate research (engine support), low priority.
