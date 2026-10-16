# Multiplayer / vocals / face-off rules: GHWT:DE vs WoR (2026-10-16)

Goal: list the WoR mechanics the DE does not have, so the HUD port shows WoR art only for mechanics the DE runs, and
leaves out (or repurposes) widgets for mechanics it doesn't. Sources: decompiled scripts (`ghwt-extract`,
`ghwor-extract`), frames of the user's clips (`WOR_face_off`, `WOR_full_band_gameplay`, `WOR_microphone_gameplay`).
Items marked (verify) come from memory of the games, not from scripts.

## Game modes

| Mode | DE (script `game_mode`) | WoR | HUD action |
|---|---|---|---|
| Career / quickplay 1-4 players | `p1..p4_career`, `p1..p4_quickplay` | yes | port (band layout) |
| Co-op 2p | `p2_coop` | merged into band | port as 2p band |
| Face-Off (alternating sections) | `p2_faceoff` | `p2_faceoff` | port |
| Pro Face-Off | `p2_pro_faceoff`, `p4_pro_faceoff` | yes (in Competitive) | port; 4p Pro Face-Off = WoR 4-lane ranked layout |
| Battle (attacks) | `p2_battle` (+ `battle_do_or_die` option) | **removed** | keep the DE battle HUD; no WoR art exists |
| Streakers, Do or Die, Perfectionist, Momentum, Elimination, team variants, Democracy Rocks vote | **none** | yes (clip 1) | **do not implement** |

## Mechanics

| Mechanic | DE | WoR | HUD action |
|---|---|---|---|
| Per-player star power meter, SP doubles own multiplier (4x, bass 6x, vocals x8 shown) | yes | yes | ported |
| Band multiplier widget (`alias_band_multiplier`) | yes (hud theme) | yes (`HUD_attach_widget_band_multiplier`, rocket x3/x4/x5 next to the band score, clip 2) | port the WoR rocket on the DE value |
| Band streak (`HUD_band_streak_notify` / `_end`, vocal highway `band_streak_lines_alpha`) | yes | yes | port WoR message style |
| Shared band rock meter | yes | yes | ported (needle) |
| **Band Moments** (gem materials `Mat_Gem_*_Band_Moment*`, all players hit a section for a bonus) | **none** | yes | **do not implement**; no band-moment gems |
| **Revive meter** (`HUD_revive_meter_*` textures; failed player comes back as the band plays) | **none** (DE: SP revives a failed player, verify) | yes | **do not implement** the meter; keep the DE revive feedback |
| Quest-mode character powers (Warrior transforms, special multipliers) | none | Quest mode only | out of scope |
| Per-player streak counter under the score | yes | yes (clips 1, 2) | port |
| Ranking badges 1st..4th in competitive | Pro Face-Off 4p only (verify) | yes | port for `p4_pro_faceoff` only |

## Layouts seen in the clips

- Band (clip 2): vocal highway on top with lyrics, 3 instrument lanes, band score + band rocket multiplier + star count
  top-right, per-lane multiplier bubble right of each lane.
- Vocals (clip 3): vocal track mid-screen, multiplier/SP pill left of the now-line, score + stars top-right of the track.
- Competitive 4p (clip 1): per-player score bars over each lane, ranking badge left, multiplier bubble right, central
  needle over lanes 2-3.

## Conclusion

Port: band layout, band multiplier rocket, band streak messages, vocals layout, Face-Off and Pro Face-Off (2p and 4p).
Skip: Band Moments, revive meter, WoR competitive variants (Streakers etc.), Democracy Rocks, Quest powers.
Keep stock DE: Battle mode.
