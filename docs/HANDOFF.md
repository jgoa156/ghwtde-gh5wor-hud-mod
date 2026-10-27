# GH5 / WoR HUD mod: session handoff (2026-10-21, 0.49 released, 0.50 WIP)

Start here in a new session. History: `docs/MODLOG.md` (latest sections at the end). Plugin internals:
`docs/PLUGIN_NOTES.md`. Repo: github.com/jgoa156/ghwtde-gh5wor-hud-mod (git author Guilherme Almeida
<jgoa156@gmail.com>, SSH push works). The mod is credited to **WitchDoctoR** (Mod.ini Author, READMEs).

## START HERE (2026-10-27 night): HANDOFF GUIDE: plugin 1.61, section 5m first (verified vs built-not-seen), then 5l / 5k

Everything after this section is older history; read it only for a detail.

### 1. Where things stand
- **Installed:** see the last line of this section (the session that installed it updates it).
- **User-verified:** guitar + vocals and face-off positions looked right (1.45 test); singleplayer was correct before
  round 1 (and should be again with 1.47's fill-size fix).
- **Not verified in game yet:** everything in "What changed" below. The user still has to check band.
- Offline tests: `python tests/run_offline.py` (25/25 at 1.48).

### 2. Rules (user, still in force; more under "Rules you set" further down)
- **Ask before EVERY game launch** (one approval per run). "stop" = kill the capture task, `python ... capture_band`
  and `GHWT_Definitive.exe`, restore GHWTDE.ini + the save from the newest `tests/results/band-*/`, verify hashes.
- **The save is sacred**: only launch through `tests/capture_band.py` (it backs up / restores GHWTDE.sav + Profiles).
- **Never install while the game runs** (its files are locked; check `Get-Process GHWT_Definitive` first).
- Commit and push finished work; keep this guide current; the mod is credited to WitchDoctoR.
- Directive 2026-10-23: **stick by the book with how SINGLEPLAYER deals with highway elements** in every mode: the
  same pieces, effects, shadows, layering and star power behaviour; keep the 2+ player angles (the user likes them);
  pieces exactly on each highway's outer border.
- Star power tube on every highway in face-off, pro face-off, quickplay band and solo quickplay; NOT in career
  face-off (boss battles) and battle. All tube instances must run the same animation / details / effects.

### 3. How the multiplayer HUD works now (don't re-derive)
- **Highway geometry is exact** (`tools/hw_geom.py`): the DE builds each highway from one struct per number of
  instrument highways (DE `scripts/guitar/guitar_tweaks.qb` highway_guitar1/2/3: top width 160/170/152, width growth
  2.2/1.33/1.2, height 350/270/270, playline 655), shifted by Pos.x (x_offset_p2 230, x_offset_p3 225 x 1.8, our
  theme + SEP 22 / SEP3 12.5). These edges sit exactly on every captured highway. The WoR border's outer edge is
  a + b*f px outside (f = fraction from the top): 4.2+19.5f (1 highway), 4.7+18.9f (2), 5.0+18.5f (3).
- **Pieces** (`tools/wor_mp.py`): every player container (g1..g3) of hud_1g1v / hud_2g / hud_2g1v / hud_3g1v shows the
  1-player descs themselves: `wor_sp_mp_ghwor` (every sp_* element), `wor_side_mp1/_mp/_mp3_ghwor` (every rm_*
  element + LEDs + the 1-player needle; one per DE needle path), `wor_mult_mp_ghwor` (the 1-player multiplier + the
  face-off alias stand-in). Each instance is placed by `hw_geom.similarity` (the 1-player outer border laid onto this
  highway's: 0.75 scale and -+3.1 deg on 2 highways) through the real container origins (`container_origins`) + the
  1-player calibration (ROOT_CAL (1,3), G_CAL (1,9)). Guitar + vocals = the identity (it IS the 1-player highway).
- **Layering** = singleplayer's absolute z (wor_1g.RAIL_Z): tubes 3.01-3.09 just above the border (z 3), badge and
  tube balls 0.04-0.05 under the highway surface (0.1).
- **Rock needle**: DE script 0x3205f550 moves an invisible stand-in on a path per number of instrument highways
  (1: (0,0)(11,-24)(28,-57)(41,-80); 2: (0,0)(13,-28)(26,-58)(37,-84); 3+: (-4,2)(8,-32)(21,-67)(33,-100)); the plugin
  finds each anchor by its unique scale (kNeedle*, kMpNeedle*, kMp3Needle*) and maps it onto the WoR LED stops.
  Multiplayer needles sit 1.5 px left (MP_NEEDLE_DX, wor_battle.NEEDLE_DX; user).
- **Star power, every tube** = the 1-player engine (plugin StarPower state per tube, `tube_set`). Singleplayer: the
  band meter widget hook (`tube_update_hook`). Multiplayer: the DE's six segments sit in a zero-size window (sp_src,
  z MP_SRC_Z 3.0525) as the level source; `mp_tube_source` reads level = scale y / x per segment every frame and
  drives our own fill (sp_fill, z MP_FILL_Z 3.0515) in sp_clip, with the same glows, plasma, burst and feathers.
  Our attach (`WoR_HUD_HUD_attach_widget_player_star_power`) must check the RESOLVED Star_Power element: the DE's
  parent_id is the compound `:s{<g> child = Star_Power}` (1.40-1.46 checked `:s{parent_id child = sp_mp}`, which
  never matched). The tube starts hidden and the attach shows it; boss battles / p1_career hide it.
- **Tube textures** are shipped above art size (wor_1g.SP_TEX_SS 4x: sp_base, spfull(_b), neon caps; SP_PLASMA_SS 2x:
  the 120 plasma frames at 60 fps in the UI pak, 24 MB). SetTexture resizes a sprite to its texture, so the plugin's
  `set_tube_texture` keeps the fill at 64x256 after every swap (1.46 blew the fill up 2-4x without it).
- **Streak meter**: the plugin recognises our multiplier by its elements (badge = the only z 0.05, 256x256 element;
  lights = its siblings), not by the texture it shows (the DE's own names used to win the race).
- **Versus score boxes**: the note streak is sized by the plugin by digit count, min(SCORE_K 0.26, 0.155 x 4 /
  digits) (the desc's fit settings do nothing in game); each side's text is found by z (wor_versus.STREAK_Z) and the
  plugin takes each player's streak from the streak-lights hook (g_streak). Career versus hides both score boxes.
- **Battle** (`tools/wor_battle.py`, hud_2d layout): rock tube by the same highway map; slots keep their map (user:
  right); layout z 4 (slots over the rail); cards CARD_FILL 0.375. The plugin finds cards by their parent
  (battlemode_container), sizes them to their slot (1.48: the first card has no scale morph, its size now comes from
  its current scale; it stayed 64 px before) and layers them bottom > middle > top relative to the game's card z.
- **Menus**: our popup / pause descs are copied over the DE globals only when the theme changes (WoR_HUD_popup_ours /
  WoR_HUD_pause_ours): copying them on every popup freed live desc structs (crash exe+0x1feea8 on face-off -> pro
  face-off, found by scanning the first-chance dump's stack for the 0xc0000005 record).

### 4. What changed this session (2026-10-23), by plugin version
- 1.44: per-player tube take-over attempt (superseded by 1.46/1.47).
- 1.45: by-the-book placement in every multi-highway layout; career versus without score/SP; battle rock tube by the
  highway map, smaller cards, slots over the rail; streak meter by elements; SP textures 4x / plasma 2x.
- 1.46: multiplayer tubes driven from the hidden level source; popup/pause swap guard (crash); needle 1.5 px left.
- 1.47: fill keeps 64x256 after texture swaps; attach checks the resolved element.
- 1.48: versus streak sized by digit count; first battle card sized; card layering relative to the game's z.

### 5. Testing and diagnosis
- Logs: `<game>\wor_hud_fixes.log` (this boot) and `wor_hud_fixes.prev.log` (the previous boot). Lines to look for:
  "star power fill: smooth fill active" (singleplayer), "star power: multiplayer tube <ptr> level ..." (each
  multiplayer tube), "2-highway / 3-highway rock needle: remapped", "battle card ... moved / not placed",
  "battle needle: rot range" (the last battle log, 1.43, had the needle stand-in never turning: recheck).
- Captures: `python tests/capture_band.py --lineup <1g1v|2g|2g1v|3g|3g1v|faceoff|profaceoff|battle>` (delete
  `tests/results/capture_band.done` first; ask first). Mock of the placement: `python tools/mock_rails.py <out.jpg>`.
- Crashes: WER dumps in `%LOCALAPPDATA%\CrashDumps`. The 0xc00001a5 one is secondary; the "(1)" dump or a scan of the
  stack for an EXCEPTION_RECORD with code 0xc0000005 gives the real fault (tools/dump_mem.py `Dump`; game code isn't
  in the dump: disassemble from GHWT_Definitive.exe with capstone). Map our plugin with `plugin\build_map.bat`.
- Install without a full rebuild: copy build\WoR_HUD (minus *.txt / *.pak.xen) to DATA\MODS\WoR_HUD, the paks
  (hud_ghwor, gems_*_hud, wor_hud_ui) to DATA\PAK, plugin\build\wor_hud_fixes.asi to the game folder; compare hashes.

### 5b. User test of 1.48 (2026-10-23): what came back
- Star power butchered in EVERY mode (singleplayer too): the fill spilled outside the tube, blocky bands. Cause: the
  round-1 texture supersampling (sp_base / spfull / caps 4x, plasma 2x). Our .img.xen DDS have ONE mip level
  (tools/png2img.js via GHSDK DDStoIMG), so a 256 px texture minified ~2x aliased, and the fill stopped matching the
  tube. Reverted (wor_1g.SP_TEX_SS / SP_PLASMA_SS = 1; the 60 fps plasma stays). Sharper tubes = mipmapped DDS first.
- "Different effects on the multiplayer tubes": the rock tubes compare identical (singleplayer vs guitar + vocals
  crops); the star power differences were the textures above. If 2/3-highway tubes still differ, get a crop.
- Vocals streak meter shows our WoR multiplier art: the vocal player_meter (Band_vocal_multiplier) reads the same
  theme multiplier arrays as the instrument meters, and WT's HUD_score_nixie_* aren't loaded with our theme. Deferred
  (user: leave it until the WoR vocals layout): needs our own vocal multiplier desc + shipped WT nixie copies + a
  plugin mapping on that desc's nixie.

### 5c. User test of the art-size build (2026-10-23, last of the week)
- Singleplayer star power: fixed (user). Every multiplayer tube (guitar + vocals, band, face-off): striped teal
  blocks = the DE's six raw segments. The level-source window sp_src had dims 0 at the clip's spot, and a zero-size
  window does NOT clip (the graveyard windows only work because they sit off screen). sp_src now sits at
  (-4000, -4000); the segments go with it, the plugin still reads their scales.
- Band rock meter: in the red zone no LED lit. SIDE_meter_red_ON_rgba (pulsed by the failing-vignette script
  0x4f63289b) was mapped onto the red LED and faded it out; it now goes to a hidden sink (in quickplay that colour
  never reaches the LED either). Checked against quickplay: same rm_* elements / shadows / gaps / ball / z, one LED
  per health zone from the DE's SIDE_meter_*_ON_alpha, the needle kept (user accepted it in multiplayer).

### 5d. User test after 5c (2026-10-23): plugin 1.49
- Band tubes "floating over the highway" vs quickplay. On guitar + vocals the positions overlay quickplay's pixel for
  pixel (frame blend), so it is layering: our band instances sat under other draw-priority chains (g1 z 1 + instance
  z 2/3 + desc root z 0) than quickplay's (hud_container 0 + band_meter 1 + desc root 10). If the GUI sums parent
  priorities (the only explanation left), the tube-end balls / shadows land over the border instead of under it.
  Now every instance's z = the 1-player chain total minus its container's (wor_mp.Z_TUBES_1P 1, Z_MULT_1P 4;
  container_origins also sums z) and the copied desc roots keep the band meter root's z (10). Harmless if the GUI
  uses absolute priorities.
- Battle slots must be BEHIND the highway (the earlier note meant the opposite of what round 1 did): layout z back
  to 0, slot rings z 0.05-0.07 (under the highway surface 0.1), each card just above its own slot (CARD_Z).
- Battle cards: the plugin's matching never saw one in the DE. Now by script: our wrappers of update_battlecards_add /
  _remove (plugin 1.49 swaps) run the DE's script, then WoR_HUD_battlecards_place puts every card of
  current_battlecard_pN (index n-1 = newest = big slot) into its slot: our size, position, scale, z.
- Battle needle: the 1.48 log and the user's crops agree (the needle sits in the lit LED's zone; the stand-in turns
  -21.6..+40 deg): it tracks health. "Not tracked" = alignment, now by the same highway map as band (round 1).

### 5e. User test of 1.49 (2026-10-23): plugin 1.50
- The z-chain change had no visible effect (the GUI's priorities are absolute; harmless, kept). The real cause of
  "floating" multiplayer tubes, measured on the user's 2000 px frames (guitar + vocals vs quickplay, lit yellow LED
  centroid): the band tubes sat 7.4 px (6 canvas units) higher. Containers draw their descs at (1, 3) like the root;
  the (1, 9) of the v0.17 calibration belongs to the multiplier / side meter descs themselves. wor_mp.G_CAL = (1, 3);
  the side meter needle keeps its own +6 (SIDE_INTRINSIC). On the slanted rail 6 units up = ~3 units outward.
- 2+ highways: the similarity scales the tubes' overlap with the outer border (quickplay: ~9.7 left / ~7.5 right
  canvas units) by 0.75; each group moves inwards by the lost part (wor_mp.OVERLAP_1P).
- Battle: slot stack slides along its rail until its top is level with the rock tube's top (RM_TOP_ROW 4 of
  rm_base); cards CARD_FILL 0.82 (rim visible); the needle stayed at its health-1 spot (both players, any LED): since
  the 1.41 fade-in, move_2d_elements_to_default's tween puts it back on its target every frame. Plugin 1.50 writes
  the needle's tween target too, and logs "battle needle P1 / P2: deg -> health" once per player.

### 5f. User test of 1.50 (2026-10-23, "last stretch"): plugin 1.51
- Accepted: battle slots ("perfect"); band / versus tube layering and shadows.
- Battle needle still not tracking, although the 1.50 log tracked health correctly (deg -21.6..+13.8, zone and t
  moving). Cause: the plugin wrote the needle's pos raw. Nothing else dirties that element in battle (the stand-in only
  turns), so it kept drawing where it was when the container's fade-in ended (the health-1 spot). Plugin 1.51 moves it
  with SetPos(.., 1) (like every other piece the plugin moves) when it changes, and still writes the tween target.
- New attack card: flew up, then sideways into the big slot. guitar_battle reads every card target from the GLOBAL
  battle_hud_2d_elements (fields: rock_pos_p1/2, card_1..3_off_p1/2, attack_ready_text_pos_p1/2, z), never from the
  theme's layout. The per-field $change$ of its vec2 offsets never took, so battlemode_ready morphed each new card
  to the stock spot first, then our battlecards_place morphed it to ours. Now WoR_HUD_battle_globals (called by the
  create_battle_alert_frames / update_battlecards_add / _remove wrappers) saves the stock struct once
  (WoR_HUD_battle_stock) and, with this theme, sets the whole global to a copy of our layout struct WoR_HUD_battle
  (it has every field above, with our offsets), or puts the stock one back otherwise. If the path is still two-legged,
  the global copy didn't take either (check the swap; next idea: wrap battlemode_ready).
- Multiplayer streak meter over the border instead of behind it like solo. 1.51 first moved the badge 4.5 units
  down (source g1 + (1, 9)). WRONG, reverted: the user says every multiplayer position is perfect in band quickplay,
  and the issue is layering only. The real cause is a regression from 1.49's z-chain change. The multiplier
  instance's own z decides how it layers against the highway, not the chain's sum. Up to 1.48 the instance had z 2
  (= solo's player_meter), and the user's guitar + vocals frame at 02:45 (1.48 installed) shows the arm tucked
  behind the border. 1.49 set it to Z_MULT_1P - g1's z = 3 on 2 highways, and since then the arm draws over the
  border's bevel (likely the DE's z 3 sys_sidebar2D sprite: 2.05 under it, 3.05 over it). Now
  wor_mp.Z_MULT_INSTANCE = 2.0 on every multiplier instance; positions back to 1.50's. The tubes keep the chain value
  (user: perfect). So "absolute priorities" (5e) is only half right: the priority that counts seems to be the
  descinterface instance's z + the element's own z, with plain containers and desc roots not counting. Unproven: if
  the arm still shows, this model is wrong.

### 5g. User test of 1.51 (2026-10-23, "final change"): plugin 1.52, release 0.50
- Battle rock tube by the book: each player gets the band layouts' own rock tube desc (wor_mp.SIDE_NAMES[2]) in
  battlemode_container, placed by the band map (wor_battle.rock_instance / rock_point, same overlap correction);
  WoR_HUD_battle_rock creates / attaches / fades them in, WoR_HUD_battle_needles drives each needle stand-in on the
  DE's 2-highway path (script 0x3205f550 doesn't run in battle). The hud_2d tube body / LEDs are blank now (ids kept
  for the DE's alpha switches); our old battle needle stays, transparent by colour, so the plugin still sees battle.
  The slot stack re-aligns to the new rock tube's top.
- Versus streak flashing back to the 4-digit size: a new number re-lays the text out at its desc scale inside the
  element update, after our sizing. 1.52 sizes it again after the update (vs_streak_size).
- Band needle's top stop lower than quickplay: MP_NEEDLE_DX -2 -> 0 (the -2 was asked while the tubes sat 6 units
  high; on the slanted cap a needle moved left sits lower).
- Then the user asked for release 0.50 (with Ultrawide Fix 1.1) published on GitHub. None of 1.52 was seen in game
  before the release.

### 5h. User test of 0.50 (2026-10-25): plugin 1.53 (installed, not seen in game)
- 3-highway star power butchered: a window's children don't take the window's ancestors' rotation, so the fill drew at
  the 1-player angle (measured 26.2 deg vs the tube's 19.6 on the 3g1v capture). place_in_window adds the ancestors'
  rotation to the fill, turns its offset and widens the window by kRotMargin (rot 0 on the 1-player tube: unchanged).
- Band score had no thousands separators (the hook needed the 1-player star bar): also on while a multiplayer tube's
  level source updates (g_mp_seen).
- Score digits wider (user, mock docs/mocks/mock_score_font_v1.png): SCORE_TEXT_KX 1.242, KY 1.147.
- Battle rock tube shadow / end ball missing vs band: battle's instance had chain total 0 (band 1), now z
  Z_TUBES_1P. Unverified hypothesis (no capture, user's call); if it still differs, capture 2g vs battle and diff.
- Vocals: analysis + plan in docs/research/wor_vocals_hud.md, mock docs/mocks/mock_vocals_v1.jpg (not started).

### 5i. 2026-10-26: plugin 1.55 + vocals stages A and B (installed, not seen in game)
- 1.55: balls on every star bar / song line (score_lead_from, from each bar's own update); multiplayer SP feather
  bands no longer grow down (place_in_window grow_bottom), turned tube's cut through the window centre, kTubes 8;
  multiplayer needle MP_NEEDLE_OUT 2.5 (perpendicular to the tube); battle VISOR_SPACE 2 / VISOR_DX 2.7, the newest
  card keeps battlemode_ready's own 0.3 s collect flight (battlecards_place morphs only slots 1-2).
- Vocals stage A (tools/wor_vocals.py, mock v2 approved): hud_1v's v1 gets three descs on the DE's vocal widget slots:
  player_meter = wor_vocal_mult_ghwor (panel backing + blue stripe + dividers + combo plate + "xN" image from the
  theme's vocalist arrays 112feba3 / bc95780d + phrase box, empty), BAND_top_meter = wor_vocal_health_ghwor (lamps on
  TOP_meter_*_ON_alpha, needle on side_meter_needle_pos (0,-105)..(0,-5) in a -90 deg anchor), vocal_multiplier_star =
  wor_vocal_sp_ghwor (3 segments in -90 deg containers on glow0..2_scale). band_meter = the quickplay score group at
  WoR's vocals spot. Theme 0x3fb45eb1 = vocals_highway_ghwor (the DE's vocals_highway_wtde, root y 0 -> 32).
- Research correction: the DE's now line is already at WoR's x (root 288 + now_bar 121); the line at x ~270 in our
  frames is a phrase marker.
- Vocals stage B (same day): VH_DY 29 (not 32: the DE draws 3 units lower than WoR for the same root; lines now at
  canvas 494 / 596 like WoR); lyric band (root's bg_middle / bg_left / bg_right) alpha 0.9 at desc y 141, 32 tall
  (canvas 600..632), lyrics container y 142 (words centred ~617); fireball_bg (comet) scale 0.35 (WoR's); a green now
  line WoR_now_line (texture WoR_HUD_v_nowline = basic_gems d96d3be3 tinted green + a 4 px core) appended to
  pitch_area so it rides at the comet's x; theme row vocal_lyric_font = WoR_HUD_lyric_a1 (WoR fontgrid_lyric_a1,
  converted into the theme pak like the score font); guitar + vocals (hud_1g1v) v1 gets the same panel, 430 units
  higher (the DE places the vocal highway at y 0 with more than one player, 430 with one).

### 5j. 2026-10-26 research (user: bulb, purple fill, vocals art, instrument badges): docs/research/wor_assets.md end
- Band multiplier bulb: built (1.40) but blank at x1, and the DE's band multiplier is x1 unless members' star power
  overlaps, so it is almost never seen; WoR shows it all song (art band_HUD_multiplier_one..eleven exists).
- Purple improvisation fill (drums + vocals): WoR's audio visualizer, not art (the vocals_freeform / _visualizer
  textures are empty render targets); the DE has no visualizer. Only route: recolour the DE's materials (drums
  mat_drum_fill(2), mock_drumfill_v1 pending; vocals VH_FF_FX01 / VH_Crowd_Noise) to WoR's purple 147,0,255.
- Vocals: all WoR vocals art is already decoded; nothing left to extract.
- Instrument badges: decoded now to ghwor-extract\band_lobby_png (bandlobby_bord_instrument + _color + _color_fg) +
  U\icon_*_fill / _out glyphs (sheets docs/research/wor_badges_sheet.png, wor_icons_sheet.png).

### 5k. 2026-10-26 evening: plugin 1.57 (installed, not seen in game)
- Band bulb shown at x1 (user: "turn on the lightbulb for 1x"): WoR_HUD_bandbulb_1 (band_HUD_multiplier_one) is the
  nixie's first texture; plugin 1.57 runs the grow (popup) on every bulb change, not only blank -> bulb, so it pops at
  song start and on each multiplier step.
- Drum fill purple applied (user: "purple color on the current DE line works for now"): DRUM_FILL_RGBA =
  (0.58, 0, 1, 0.8), the mock's strong variant (soft = alpha 0.5). Only the 2nd guitar_material array (af201180)
  holds mat_drum_fill(2). Global to every theme like the dark metal. Vocals freeform (VH_FF_FX01 / VH_Crowd_Noise,
  vocals_highway.qb) NOT recoloured yet.
- Test bots deploy star power (user: "fix tests to actually use star power, at the same time when in bands"):
  DE bots never do (player_status bot_star_power = 0; vocals: global vocal_bot_uses_starpower = 0). With
  TestAutoLaunch=1 our setup_hud wrapper starts WoR_HUD_test_sp (build.py, after TEST_AUTOLAUNCH_SCRIPT): every
  0.25 s, when no one is in star power and all players are ready (>= 50, or band scoring: band1 pool >= n x 100/6),
  it spawns the DE's star_power_activate_and_drain for every player at once (fallback: the ready ones after 20 s).
  Not in battle. debug.txt prints "WoR_HUD: test star power, r of n players ready". Never run yet: if star power
  never shows in captures, check that line first (setup_hud wrapper ran? getplayerinfo checksum ok?).

### 5l. 2026-10-27: plugin 1.58, vocals v3-v5 + panel multiplier + score box + bulb (not seen in game)
User test of 1v (2026-10-26, own recording) -> mocks docs/mocks/mock_vocals_v3.jpg, _v4, _v5, mock_vocals_mult_v1.jpg
(all approved; "don't apply changes to NOTE streak": the streak box under the score is untouched). Built:
- Lyrics: scale 0.4 x 0.4 (DE 0.55 x 0.75); sung words WoR blue (120,112,245), current word WoR yellow (254,233,53),
  upcoming 236. These are DE globals: WoR_HUD_vocals_globals (tools/wor_vocals.py) sets them with our theme and
  puts the DE values back otherwise; run from a wrapper of the DE's per-theme vocal setup 0x74586fa3 (plugin swap)
  and from our setup_hud wrapper (every song).
- Purple ball = the DE comet's "miss" sparks (vocals_comet_particle_effects, start 128,0,255): our copy
  WoR_HUD_vcomet_wor has them at alpha 0 (DE copy WoR_HUD_vcomet_de restored with other themes).
- Notes: theme field c5e00a8d (sung-note texture, DE's 0x74586fa3) -> WoR_HUD_vnote_*; f6faf84b (connector) blank;
  vocal_gem_colors white with our theme (the DE tints its teal art with it). A note is ONE sprite with the texture
  stretched along it (DE art: 32x32 profile, tube rows 7..24), so the rectangle's end edges are in the texture:
  12 length bands (wor_vocals.NOTE_BANDS), the plugin picks the band from the sprite's on-screen width (dims x the
  ancestors' x scales) and logs the first 6 notes ("vocal note: dims ..."). CHECK in game: if the ends look too
  thick/thin, the band calibration (canvas units) is off; if the texture tiles instead of stretching, rethink.
  NOT DONE: star power phrase notes' cyan glow (top/bottom): the DE marks them only by colour (vocal_gem_colors
  index unknown) and the plugin doesn't know the element rgba offset.
- Now line: 4 green / 4 cyan lightning frames, the plugin steps them at 20 fps, cyan while the QB global
  WoR_HUD_vocal_sp = 1 (set/cleared by our GH_Star_Power_Verb_On/Off wrappers for a Vocals player). White
  arrowheads on both lines (sprites in pitch_area). Star power glow bands on the top line and the lyric band's bottom
  edge (root children, faded by the plugin with the same flag).
- Highway background: bG black at 0.45; the DE's bg_rgba prop (the teal) repointed to a hidden root child
  WoR_bg_sink (prop paths address children by index: appended at the end of root, index checked = 17).
- Panel: meter inner shadow + gloss (WoR_HUD_v_meter_shade), per-lamp blurred inner shadow (v_lamp_shade), the "xN"
  images per mock_vocals_mult_v1 (box baked in, combo art hidden), star power strip 9 tall / 1 up / border /
  5-wide mark, its instance at z SP_Z 4 (above the vocal highway's lines, z 2).
- Score (every mode): digits 0.86 as wide (SCORE_TEXT_KX), housing inside x0.45 and the front's rim grown 2 texels
  each side and lifted (wor_1g.ART_EDITS, applied by build.py ship()).
- Bulb: WoR's band_HUD_bulb_x texture (decoded into ghwor-extract z_in_game_png2), digit and x tilted 10 deg CCW
  (WoR rot_angle -10); popup = WoR's slide from behind the score box (+118,+32 frame units, scale 0.5, 0.3 s) with
  the orange Glow01 flash (sprite band_bulb_glow, the plugin moves it with the bulb).
- Tests: tests/capture_band.py --bulb-cycle sets [WoR_HUD] TestBulbCycle=1: the bulb steps x1 x2 x3 x4 then star
  power x2 x4 x6 x8 every 2 s (WoR_HUD_test_bulb_cycle in tools/wor_band.py), each with the popup.

### 5m. 2026-10-27 evening: plugin 1.58 -> 1.61 (see git log for each), what is verified and what is not
Verified in captures: no crash in 1g / 1v / 1g1v / 3g1v (the 1.58 crash at vocals_create_highway was copying
vocal_gem_colors / vocals_comet_particle_effects with change ~$x$: those two are no longer changed; the comet table is
now REDEFINED under its own name in our QB, every theme); lyric size / colours (sung words end WoR blue after a fade
from the current word's yellow); band vocals panel; bulb hidden at x1.
Built, NOT seen in game yet:
- 1.60 band tube fill: a sprite's rotation tweens from +0xd0 to its target +0x114 (SetRot 0x5a1970), so writing +0xd0
  alone never took (1.53-1.59 band fills kept the 1-player angle). set_rot writes both + flag 0x400; sign +rot.
- band score group 50 lower with a vocalist (wor_band VOCAL_DY); 4-player band vocalist health meter shown + DE
  health widget attached a second after setup (WoR_HUD_vocal_health, logs "vocal health meter p%p alpha %a").
- star power fill (all modes): ends on the glass end's arch (wor_1g SP_GLASS_END, glass_mask), the bottom neon traced
  on that arch in texture space (bake_bottom_arc; bake_screen_needle no longer used), 16 feather bands (was 8: the
  charged top's steps looked pixelated).
- 1.61 practice crash guard (build.py PRACTICE_GUARD_SCRIPT, swap of guitar_force_unload_anim_paks, every theme): skips
  anim paks the band still holds (logged "anim pak %p still held"); the crash was mpm_flush_pak's scriptassert.
- 1.61 note diagnostics: every distinct note width and colour (+0x118) logged ("vocal note: ..." / "vocal note
  colour: ..."): needed for the star power phrase notes' cyan glow (their colour is unknown) and the note length bands
  (1.58-1.60 saw only 50.4-wide notes).
Separate mod: E:\Dev\ghwt\ghwtde-venue-filter (local git only): redefines download_LevelZoneArray without Serpent's
Stronghold, The Monument, Rush 2112 Temple, Hypersphere (zone paks with no animations / sounds) + 2 dead keys.
Ultrawide Fix 1.2 (its repo): HorPlusSites bitmask, default 7 (0x711bac added); 8 / 16 = the two other projections,
off (the boot crashes blamed on it were the vocal globals).
Waiting on the user: which single-player tube angle (fill top line vs the tube against the highway); ultrawide band
close-ups on their screen; a GitHub repo for the venue filter.

### 6. Open / next (vocals first; the user approved mock v2 = docs/mocks/mock_vocals_v2.jpg / _sp.jpg)
1. **In-game check of vocals A + B** (vocals-only and guitar + vocals; capture line-up `1v` exists in
   tests/capture_band.py, `1g1v` too; ask before launching). Look for:
   - panel at canvas 141..386 x 457..499 glued on the highway's top line; score group top right (890,410) like the
     mock; if the panel is off by a constant, the v1 container origin / G_CAL (1,3) is the suspect;
   - health needle sliding LEFT->RIGHT with health (0 at the red end). If it runs the wrong way or vertically, the
     -90 deg anchor's sign is wrong: flip rot to +90 (and the needle sprite to -90) in wor_vocals.health_desc;
   - star power strip filling left->right along the top line in 3 segments. Same sign risk (seg containers rot -90);
     the DE may also write glowN_scale x != 1 (strip thickness): then set the fill sprite dims by it;
   - multiplier "x1".."x4" images (WoR colours), "x2".."x8" pale green in star power;
   - lyric font size: the DE's own vocal_lyric_font_scale / offset globals stay; if WoR's font reads too big or small,
     those are DE globals (not theme fields): change them from a theme-conditional wrapper;
   - lyric band dark under the words; now line green at the comet; comet smaller.
   - score commas in vocals-only: plugin 1.56 marks the HUD as ours from any score box update (g_score_seen in
     score_lead_from); check they show.
2. **Vocals still missing** (research in docs/research/wor_vocals_hud.md, "v2 findings"):
   - note look: WoR's notes are thin hollow YELLOW outlines (Vocal_Note_Line colour 1,1,0), solid yellow when sung
     (vocals_paint colours 0.99,0.99,0.26), cyan in star power. They are DE materials in guitar_material
     (vocal_note_sung / _sp, VocalEKG paint): build.py's recolour_materials works on the material arrays but applies
     to EVERY theme (like the dark metal): needs a theme-conditional swap of the arrays (e.g. in the theme-change
     hook where popup/pause descs are swapped) before doing it;
   - star power look (6.webp): cyan glow band on the top line + cyan edge under the lyric band while SP is active:
     extra sprites in vocals_highway_ghwor (alpha 0) shown by a wrapper of vocals_activate_star_power /
     the deactivate script (plugin script swap pattern, kScriptSwaps);
   - phrase meter box: empty (its DE driver is unknown; WoR's vocals_phrase_progress_meter fill x -104..0);
   - "EXCELLENT!" phrase compliment inside the panel (WoR) instead of at the comet (DE vocals_message);
   - star power strip smoothness: if the DE's setubes steps, drive it from the plugin (like mp_tube_source);
   - star animation (WoR FC_GLOW flicker while no note missed + on star change two SB_Tubeglow02 flashes and three
     particle bursts, guitar_events son_of_HUD_animate_star_meter_flames) and thicker tip balls (WoR 12x8 core:
     STAR_LEAD_S (1.7, 1.3) or WoR's hud_progression_bar_lead x2 Add at (1.2, 0.9)) - user asked for both.
3. **1.55 checks** (multiplayer): 3-highway star power fill now turned with its tube (never seen in game; if the fill
   is turned the WRONG way, flip the sign in place_in_window: fill rot0 - rot and the offset rotation), no washed
   band below the fill level on 2/3 highways, needle position, battle slots spacing and the collect flight.
4. If a whole layout's pieces are off by a constant, the container-origin model (G_CAL) is the suspect.
5. Older: practice-mode crash logs, 6th star check.
6. Vocals purple freeform fill (recolour VH_FF_FX01 / VH_Crowd_Noise; mock first).

Installed: plugin 1.58 + mod (5l), 1.57 (5k), on top of plugin 1.56 + mod with vocals stage A + B (commits d05da56, 5b1335f + the stage B commit), 2026-10-26, hashes verified. Not tested in game yet. Release 0.50 on GitHub is 1.52; nothing after it is pushed.

## Session log 2026-10-23 (details behind the guide above)

### Session log 2026-10-23, round 3: plugin 1.47 + mod BUILT (install when the game is closed)

User test of 1.46: quickplay singleplayer SP fill blown up / pixelated, cut into a block; face-off tubes gone.
- Singleplayer: SetTexture sizes a sprite to its texture; with the fill textures at 2-4x (round 1) every plasma frame
  made the fill 2-4x too big (clipped by the window). Plugin 1.47 set_tube_texture keeps the fill at 64x256.
- Multiplayer: since 1.40 our star power attach checked :s{parent_id child = sp_mp}; the DE's parent_id is
  :s{<g> child = Star_Power}, so the check replaced its child and never matched: every multiplayer tube took the DE's
  3-segment branch (no engine; with 1.46's hidden default, no tube). Now checked on the resolved id.

### Session log 2026-10-23, round 2: plugin 1.46

User test of 1.45 (face-off screenshot + needle crop): positions accepted so far (band still to verify). Fixed:
- Crash face-off -> pro face-off: real fault (first-chance dump, EXCEPTION_RECORD scanned on the stack) exe+0x1feea8,
  a QB struct key lookup (binary search, 12-byte entries) on a freed table, called from script code. Ours freed live
  desc structs: wor_menus._swap copied our popup / pause descs over the DE globals on EVERY popup / pause creation.
  Now guarded by WoR_HUD_popup_ours / WoR_HUD_pause_ours (copy only on a theme change). Not proven to be THE cause:
  if it crashes again, scan the new dump the same way (tools/dump_mem.py + struct scan for 0xc0000005).
- Multiplayer star power: no session ever logged the tube hook on a per-player tube (the DE's raw segments showed).
  wor_mp.sp_desc: our own fill (sp_fill, z MP_FILL_Z 3.0515) in sp_clip, the DE's segments in a zero-size window
  (sp_src, z MP_SRC_Z 3.0525); plugin 1.46 mp_tube_source reads the level (scale y / x per segment) every frame and
  runs the 1-player engine (tube_set, shared with the hook). Log: "star power: multiplayer tube ... level ...".
- Career versus: SP tube starts hidden in every multi-highway layout, shown by our attach; hidden (and the score
  boxes) when boss_battle = 1 OR game_mode = p1_career.
- Rock needle 1.5 px left on every multiplayer highway (wor_mp.MP_NEEDLE_DX, wor_battle.NEEDLE_DX).

### Session log 2026-10-23, round 1: every multi-highway layout "by the book" (plugin 1.45)

User evidence 2026-10-23 (`OneDrive\Videos\GH\GHEvidence\`: video + 9 annotated stills, priority list): items 0-5.
Directive: **stick by the book with how SINGLEPLAYER deals with highway elements**; angles in 2+ player modes are fine
(keep them), carry over singleplayer's effects/details and put the pieces exactly on each highway's outer border.

What was found (don't re-derive):
- The DE builds every highway from one struct per number of instrument highways (DE `scripts/guitar/guitar_tweaks.qb`
  highway_guitar1/2/3: top width 160/170/152, width growth 2.2/1.33/1.2, height 350/270/270, playline 655) shifted
  by Pos.x (x_offset_p2 230, x_offset_p3 225 x 1.8; our theme adds SEP 22 / SEP3 12.5). Drawn over the 16:9 bot
  captures these edges are EXACT on every highway (1g1v, 2g1v, face-off, 3g1v): `tools/hw_geom.py`.
- The WoR border's outer edge sits a + b*f px outside that edge (f = fraction of the height from the top), the same in
  every layout: 4.2+19.5f (1), 4.7+18.9f (2), 5.0+18.5f (3) (median capture frames, robust fit, rms < 0.7 px).
- The guitar + vocals highway IS the 1-player highway (video frames overlay exactly).
- Singleplayer's "behind the highway" = absolute draw priorities (wor_1g.RAIL_Z: tubes 3.01-3.09 just above the
  border sprites z 3, badge / tube balls 0.04-0.05 under the highway surface 0.1). The old multiplayer descs had the
  multiplier at z 6-6.5 and the rock tube at 13-18.5 (on top of the highway) and the rock tube was the battle art.
- DE rock needle path (script 0x3205f550) per number of instrument highways: 1 (0,0)(11,-24)(28,-57)(41,-80);
  2 (0,0)(13,-28)(26,-58)(37,-84); 3+ (-4,2)(8,-32)(21,-67)(33,-100).

What changed (built, installed only if the line below says so):
- `tools/wor_mp.py` rewritten: per player the 1-player descs themselves (SP tube: every sp_* element; rock tube: every
  rm_* element + LEDs + the 1-player side meter needle, one desc per needle path wor_side_mp1/_mp/_mp3; multiplier:
  wor_mult_1g copy + face-off alias stand-in), each instance placed by `hw_geom.similarity` (the 1-player outer border
  laid onto this highway's: scale 0.75 on 2 highways, rotation -+3.1 deg) through the real container origins
  (`container_origins`, GUI semantics) + the 1-player calibration (ROOT_CAL (1,3), G_CAL (1,9)). No more MP_DX /
  ROCK_MP_DX / highway_map / inverse maps. On guitar + vocals the map is the identity (the pieces = quickplay's).
- Career versus (boss battles): no score boxes (versus desc score_container_N_alpha set 0 by the attach wrapper), no
  SP tube (star power attach wrapper hides it); streak meter kept.
- Battle: rock tube by the same highway map (ROCK_NUDGE gone; slots keep their map, user: positions right); cards 25%
  smaller (CARD_FILL 0.375: the middle card no longer reaches over the bottom slot); layout z 4 (slots over the rail);
  plugin finds cards by their parent and logs "battle card ... not placed" when it can't match one. Last battle log
  (1.43) showed the needle stand-in never turning (rot 0.0..0.0) and no card placed: check the 1.45 log after a run.
- Streak meter (random wrong default / instrument icon): plugin 1.45 recognises our multiplier by its elements (badge
  = the only z 0.05, 256x256 element; lights = its siblings), not by the texture shown.
- SP tube textures resampled 4x (sp_base, spfull(_b), neon caps) and the 60 fps plasma 2x (UI pak 24 MB, theme 3.0 MB).
- Plugin 1.44's per-player tube take-over (face-off SP spill) is included.
- Mock: `python tools/mock_rails.py docs/mocks/mock_rails_v1.jpg` (pieces on clean highways; the captures' old pieces
  overlap the highway surface, so some leftovers show).

Next: install, ask for ONE capture run per layout (1g1v first: must match quickplay exactly), compare with
`tools/mock_rails.py`; if a whole layout is off by a constant, the container origin model (G_CAL) is the suspect.

## Previous (2026-10-22 night): multiplayer HUD in progress, plugin 1.43 + mod installed (HEAD 547f7bb)

Everything below this section is older history; read it only when a detail is needed.

### Rules the user set today (on top of "Rules you set" further down)
- **Ask before EVERY game launch.** The user approves runs one by one. "stop" means kill everything at once: stop the
  background task, kill `python ... capture_band` and `GHWT_Definitive.exe`, then restore GHWTDE.ini + the save from
  the newest `tests/results/band-*/` (`GHWTDE.ini.backup`, `save-backup/`) and verify the hashes.
- **The save is sacred.** Bot runs boot without loading it and the game saves fresh progress over it after the song.
  On 2026-10-22 that wiped the user's save. `tests/capture_band.py` backs up `GHWTDE.sav` + `Profiles\*.car` and
  restores them after every run; never launch the game from a script that doesn't. Recovery copies:
  `E:\Dev\ghwt\save-recovery` (shadow copies, damaged files, the 05:13 and 11-Oct versions). The user is now on the
  11-Oct save plus their own play (written 19:16 on 10-22).
- When the user says "just capture" / "don't do the analysis", capture and report only.
- The user records the screen during runs; they spot artifacts themselves.

### The capture harness (works; bots play, nobody needs to touch the PC)
- `python tests/capture_band.py --lineup <name>` launches ONCE, then refuses again until
  `tests/results/capture_band.done` is deleted (delete it before each approved run).
- Line-ups: `1g`, `2g` (guitar + drum), `1g1v` (guitar + vocals), `2g1v`, `3g` (guitar + bass + drum), `3g1v` (full
  band), `faceoff`, `profaceoff`, `battle`. Default song `ontheroadagain` (the on-disc one; the user's pick, short).
  **Songs from DATA\MODS load no notes through AutoLaunch** (num917rb2dlc played on empty highways): use on-disc keys
  (`DATA\MUSIC\<key>_1.fsb.xen`).
- How it works: the DE's own [AutoLaunch] is developer-only (guitar_startup skips it while `WTDE_IsUser` = cd840670 is
  true; that reads the devs' `babe.face` key: left alone). The mod's opt-in hook (build.py TEST_AUTOLAUNCH_SCRIPT,
  plugin swap of ui_create_boot_iis) runs the DE's AutoLaunch setup 0x581325cc when `[WoR_HUD] TestAutoLaunch=1`; the
  script sets that + `[AutoLaunch]` Players / Part<n> / Bot<n> / Song / GameMode, and restores the ini afterwards.
- Focus: only the main window (class `AspyrGH3`) is brought forward, and only when no game window has the foreground.
  The old helper also focused ReShade's `D3DProxyWindow`: that blanked the screen and paused the boot.
- Frames: PIL screenshots every 15 s from T+90 s for 3 minutes (SHOT_WINDOW 180), then the game is closed. debug.txt
  and wor_hud_fixes.log are locked while the game runs; the ghwt_bgfx dump add-on writes nothing on this install.
- **Display changed:** the game now runs 3840x2160 (16:9) and screenshots come out 1280x720 = the HUD canvas as is.
  Older captures (2560x1080) need the centred 16:9 crop `(320, 0, 2240, 1080)` resized to 1280x720.
- No venue loads in bot runs (black background): good contrast for measuring.

### State of the multiplayer HUD (what is verified and what is not)
Verified in captures (21:9 runs of 10-22 evening + the 16:9 runs `band-20261022-2053..2115`):
- hud_2g band: WoR pieces on the rails (rock tube needed ROCK_MP_DX -50 on top of MP_DX -24).
- No orange band streak glow on the rails (theme flag `0xcd149bb0` makes highway_streak_glow return): highways look
  like singleplayer.
- hud_3g1v / 3g: singleplayer pieces on all three highways (wor_mp.edit_three_highways, highway_map fitted on
  RAILS_3G), the DE's pink streak stacks + instrument icons gone; three highways spaced (x_offset_p3 + SEP3 12.5)
  so the thick borders meet.

Installed, NOT verified yet:
1. **Pieces parallel to their rails** (75ff862): user close-up showed the 2-player SP tube ~8 deg steeper than its
   rail. wor_battle.tube_maps now rotates the 1-player tube line onto each rail (SP -2.6 deg net, rock +2.95), the SP
   container gets that rotation (sp_transform returns pos, k, rot), 3-highway pieces turn per side, 1g1v's inverse
   carries it. ASSUMPTION to check: DE `rot_angle` > 0 = clockwise on screen (the multiplier code already assumed
   it). If the tube comes out ~5 deg off the other way, flip the sign.
2. A face-off capture of that build exists, **unanalysed**: `tests/results/band-20261022-222943` (11 frames). The
   user said "artifacts were found already" in it: ask what they saw, then measure (rail vs tube angle per row, as
   done in this session: rail highlight line x per row, teal fill edges).
3. hud_1g1v (guitar + vocals): wor_mp.edit_one_highway, the 1-player pieces on its 1-player highway (inverse of each
   piece's map). Was showing the DE's stock pink stack.
4. hud_2g1v: pieces were ~50 px up-left; fix = hud_2g's parent-centre offset (HUD_2G_PARENT_CENTRE: hud_2g's g1/g2
   are placed from NewElement1's centre, pos_anchor 0).
5. Band score group: right edge, just under the lyrics line in vocal layouts (wor_band OFFSET[True]).
6. Band star bar: the DE scales it x1.0 with >1 player (x0.7 with one), so the band copy's bar is 0.7 as long
   (user saw it grow past the box).
7. Band star sparks: the DE's multiplayer sparks d1be6858 use textures we don't ship (MISSING TEXTURE boxes); plugin
   1.43 swaps it to the 1-player Star_Meter_Sparks01 with our theme.
8. Face-off streak number: fixed size 0.155 (the fit settings did nothing in game; "235" was cut off). Adaptive size
   (user wants it) would need the plugin.

**SP fill spill in multiplayer: cause found, plugin 1.44 built (NOT installed: the game was running).**
- Face-off capture `band-20261022-222943`: the same artifact on every frame, both highways: a teal strip with a
  vertical left edge, left of and over the tube, horizontal banding, charging teal although the tube is full, no plasma.
- `wor_hud_fixes.prev.log` of a face-off session ("versus needle: twin found") never logs "star power fill: smooth fill
  active": the tube engine never took the per-player tubes over, so the DE's own six segments (slanted strips) drew,
  cut by the clip window's left edge. Not the WindowElement under the scaled container.
- Why: tube_update_hook only accepted a widget whose first segment shows one of our tube texture names; the per-player
  setubes (player = N) leaves something else there. 1.44: our tube is also recognised by its structure (a feather
  window beside the clip whose fill shows our texture), the DE's raw `_b` name counts as charged, and the first 4
  take-overs log "star power fill: tube ... segment texture XXXXXXXX taken over". If that line never appears in a
  face-off run, the hook isn't called for per-player widgets at all: look there next.
- Install: copy `plugin/build/wor_hud_fixes.asi` to the game folder (with the game closed), then a face-off run.
- **Microphone meter** (v1 player_meter, top right of the vocal highway): our WoR multiplier textures on the WT+
  vocal meter = an anomaly. User: show stock WT for the mic "if possible while we don't have the textures" -> needs
  the WT vocal multiplier textures (not loaded with our theme; extract + ship them, or map back in set_texture_hook).
- **Practice-mode crash when switching from quickplay**: logs were lost to the next launch. Plugin 1.43 now copies
  `wor_hud_fixes.log` -> `wor_hud_fixes.prev.log` at boot (works); the DE `Logs\debug.prev.txt` copy did NOT appear
  (the DE probably restarts debug.txt before our ASI loads): fix or ask the user to copy debug.txt right after a crash.
  WER dumps: `%LOCALAPPDATA%\CrashDumps`; the real exception is on the stack (scan for c0000005), the 0xc00001a5 is
  secondary.
- Still pending from earlier: purple drum-fill pick (soft/strong, docs/mocks/mock_drumfill_v1.jpg, build.py
  DRUM_FILL_RGBA), battle fade-in and 6th star in-game checks, release 0.50.

### Geometry facts learned today (don't re-derive)
- 1-player tube line lean 29.1 deg, 1-player border 27.3, 2-player rail 26.5 (RAIL_L/RAIL_R match the real rails;
  the border highlight measured 26.4 in 16:9). 3-highway rails lean ~20 deg.
- MP_DX / ROCK_MP_DX are hud_2g-only (its containers sit in a centred parent); 3g1v / 2g1v / 1g1v don't use them.
- get_highway_pos_and_scale: 2 non-vocal highways at -+x_offset_p2; 3 at -+x_offset_p3 x 1.8 (drum centred);
  1 non-vocal = the 1-player highway (Pos 0). Our wrapper adds SEP / SEP3 with our theme.
- Layout by line-up: 2 instruments = hud_2g; guitar + vocals = hud_1g1v; 2 instruments + vocals = hud_2g1v;
  3 instruments (with or without vocals) and every 4-player band = hud_3g1v.

## Start here (2026-10-21)

State: HUD **0.49** released (releases/, bundles Ultrawide Fix **1.0**). HEAD has battle mode rebuilt in the WoR style
(plugin 1.33, tools/wor_battle.py, mock docs/mocks/mock_battle_v8.jpg approved 10-20, build preview
docs/mocks/mock_battle_v9_build.jpg) and the bgfx add-on stepping aside on DXVK; HEAD + plugin 1.33 are installed,
battle is NOT tested in game. Sibling repos, both released and confirmed working by the
user on 2026-10-20: **Ultrawide Fix 1.1** (ASI plugin, Hor+ 3D FOV, no ReShade needed; only release on its repo) and
**All Main Menu Music 1.0** (10 games in one mod, GitHub Release, World Tour's six always play).

1. **Battle mode: test 2 fixes built (plugin 1.34, MODLOG "Battle test 2"), awaiting test 3.** (LEDs,
   needle direction, cards into the slots, tube glued.) Earlier: test 1 failed, fixed. Test 1: highways
   far too far apart, sets visible on the wrong side during the intro, every other mode hung at loading (MODLOG, end).
   Fixes installed; test quickplay FIRST (the hang), then battle. Calibrated on the user's footage
   (`OneDrive\Videos\2026-10-20 21-49-06.mp4`); v8 approved. Each highway carries the main theme's rock tube on its
   left rail (needle slid by plugin 1.33 from the DE-turned stand-in) and the three attack slots where the SP tube goes,
   highways 30 apart each (the wrapper moves the returned Pos; x_offset_p2 untouched), P2 = P1's set translated, empty slots dark, cards sized to the
   slots. **The attack alert / card above the highway is stock on purpose: its design is still to be discussed with
   the user** (WoR template idea: uidesc_quickplay_challenge_alert, `wor_card()` in tools/mock_battle.py). What to read
   in `wor_hud_fixes.log` after the test: "battle needle: ..." (stand-in found, rot range, swing 42 or 74), "battle
   card ..." (cards resized), "get_highway_pos_and_scale wrapped". Details: MODLOG "v0.50 WIP + plugin 1.33".
2. **Ask for one test run** (rule: ask before launching): the reworked battle mode, plus the still-unconfirmed 0.48/0.49 items: fail box calibration, YOU ROCK round 3 (letters,
   gravity 3500, glow, the WoR sound via SoundEvent), rock needle stand-in (plugin 1.31), popup message size.
3. **Release 0.50** with the above (`python build.py --package`, zip to releases/, push).
4. **Open decision:** popup up/down arrows (code ships, did not show in game; user: leave it for now).
5. **Backlog (user order):** face-off crash (enable WER LocalDumps first) + face-off layouts; multiplayer / vocals
   layouts (rules in docs/MODES_RULES.md, mocks in docs/mocks); song list side art (user remastering); drum
   animations (docs/DRUM_ANIMS_PLAN.md, not started); full code review of the HUD, ultrawide and menu music repos;
   WoR's Star03 sliver for the burst; the DE's SP highway glow leak; game-catalogue jump menu idea (SELECT key) and
   song list sorting that ignores a leading "The".

## 2026-10-22 late: plugin 1.40 + mod INSTALLED (not tested in game)
- Gluing: tube_maps keep the 1-player angle (uniform scale about the LED span's middle, no shear: the sheared tubes
  looked more tilted); wor_mp.MP_DX -24 corrects the offset into the centred g1/g2 containers (measured on the
  user's face-off shot); SP_NUDGE back to -15. The rail model (RAIL_L/R - SEP) matched the 2-player borders at SEP 22.
- Per-player SP tube = the 1-player tube itself: wor_mp.sp_desc copies every sp_* element of wor_band_meter_1g into
  a container (sp_transform: scale k, pos) -> same local coords, so the plugin's tube engine constants apply; plugin
  1.40 keeps one StarPower per tube (g_tubes[4], g_sp = *g_spp, tube_for(clip)). Our
  WoR_HUD_HUD_attach_widget_player_star_power REPLACES the DE script (swap, no orig): on our tube (child sp_mp exists)
  six segments, the band's band1_starpower in band / co-op, the player's own in face-off types / battle / boss;
  otherwise the DE's three segments. Old WoR_HUD_vs_sptube / vsseg no longer shipped.
- Band (items 9-11): tools/wor_band.py: the quickplay score group (no tubes) as desc wor_band_score_ghwor in every band
  layout (band_meter instance, OFFSET no vocals (-9,-394) / vocals (-37,-324)), every WT+ band prop on hidden sinks
  (instrument icons = the huge guitar, gone); WoR bulb (bulb + nixie digit + 'x') per value WoR_HUD_bandbulb_2/3/4/6/8,
  set by a semultipliernixie on band1_multiplier from our HUD_attach_widget_band_meter wrapper (blank at x1); plugin
  grows it in (0.3 s) when it leaves blank. desc_gen now records PROPS / ALIASES.
- Battle: x_offset_p2 itself = stock + SEP with our theme (saved stock on first call; the highway wrapper no longer
  moves Pos), so the DE's prompts / alerts (PUSH etc., placed at gem pos + x_offset_p2) follow the highways (item 5).
- Streak number: WoR's fit settings (fit_width scale each line if larger + fit_height scale down if larger),
  STREAK_K = SCORE_K (adaptive; if it fails again, STREAK_K_FIXED 0.155).
- SP tube look (item 12): SP_RIM 3 -> 1 (wider fill), SP_NEON_HALO (2.6, 2.6). Plasma 60 frames at 30 fps (pak budget,
  now 3.27 MB).
- Mocks: docs/mocks/mock_faceoff_v9.jpg, mock_band_v9.jpg, mock_battle_v14.jpg.
- STILL TODO: item 0 fade-in (battle pieces now appear in place, no fade), item 13 improvisation purple line (WoR
  av_presets og_highway_drum_freeform + guitar_highway_visualizer: research DE support), the 6th star (user wants
  it; WoR shows 6 on the star at 100%), crash repro (career -> pro face-off, keep debug.txt).

## 2026-10-22: user's test of 1.39 (OPEN, work these first; screenshots in the session)

0. Battle highway pieces must NOT drift into view at song start: fade in like every other mode.
1. CRASH: career face-off, then pro face-off (switching modes) crashes the game.
2. Career face-off: no rock tube glued to the highway, only the versus meter.
3. Versus streak number: size adapts to its digit count AND is centred in its slot (2 digits showed small, "28").
4. Score boxes a few px UP (dial stays): they cover a small part of the dial's bottom.
5. Battle effects sometimes uncalibrated with the highway: the "PUSH" (string cut) popup showed below the highway,
   probably not aligned with the green gem strike either.
6. Power-up icons still too big: the slot border must be visible like WT's default (round icons inside rings).
7. Battle rock tube poorly aligned (quickplay is perfect): angle with two highways? (3 highways later); or move it a few
   px left. Slots: arms still showing a lot: move closer; stack so only part of each circle is behind the one in
   front, crescent order.
8. Face-off / pro face-off / career face-off: pieces still not glued: move both left by some px.
9. Band: pieces poorly aligned; rock tube more tilted than it should be (keep ONE angle always); remove the huge
   guitar icon (the WT band meter's instrument icons); replace the band score meter with the quickplay one; ALL
   players' SP tubes show the band star power (same value on every tube).
10. WoR band score group: a light bulb for the band multiplier that expands out of the score group from x2 up
   (textures already extracted: band_HUD_multiplier_bulb, bulb_x, band_HUD_multiplier_one..eleven).
11. Band score group always top right; with vocals it gains top padding below the vocal highway (user's WoR frames).
12. SP tube (all modes, user's WoR crop): WoR's blue fill is wider (fills more of the tube sideways); the bottom neon
   blurrier with more glow.
13. Improvisation (freeform) sections: WoR shows a purple animated line on the highway; ours a white line. Lead: WoR
   av_presets og_highway_drum_freeform(_rb/_ps3) + scripts/guitar/guitar_highway_visualizer (hudqb decompiled).
DONE + INSTALLED 2026-10-22 ~04:30 (plugin 1.39 names regen, mod): 0 battle containers start in place (OFFSCREEN =
rock_pos: no slide; a fade is not done yet), 2 career face-off (boss_battle) gets no rock tube (CAREER_METER_SCRIPT),
3 streak centred (internal_just 0.5; adaptive size still TODO), 4 BOX_UP 6, 6 CARD_FILL 0.5, 7 VISOR_INSET 9 +
VISOR_GAP 0.72 + ROCK_NUDGE 11, 8 SP_NUDGE -19. Crash analysis: the 03:49 session ended in the DE's 'CRITICAL: Zone
not found' (random venue bug, not the HUD); the 03:47 mode-switch dump (0xc00001a5 at exe+0x5728f2) has no log
(overwritten): reproduce once and keep debug.txt. TODO: 1 (crash repro), 3 adaptive size, 5 battle effects vs
highway, 9-11 band, 12, 13, gluing model, per-player SP tube.

## 2026-10-22 03:xx: user's test of 1.38 (OPEN, work these first)

Face-off: highway spacing OK now (pieces still not glued). Versus dial: the leader's colour must be shinier. Empty
streak lights show the wrong (DE) texture until the first note. 3-4 digit streak fit did NOT work (fit_width
ignored?). Score thousands separators (as in quickplay) not applied to the versus scores. SP tube: not tracked, no
animated lightning when ready (the per-player tube rework). Battle: the slot visors are tilted (the same art on the
streak meter is upright: use it unrotated); the power-up cards still too big.
DONE + INSTALLED 03:30 (plugin 1.39): leader glow blend Add; streak STREAK_K 0.155 (4 digits fit; fit_width is
ignored by the DE); stock light names -> ours on our meters (kStockLights, SetTexture hook: empty state at start);
separators also while the versus needle / battle meter is up (g_vs_seen, g_battle_seen); battle visors upright
(visor_affine: rail map's size only, no rail rotation); CARD_FILL 0.66. Battle needle: 'battle track' log shows the
needle zones and the DE's LEDs agree (green at deg 16.2 > A/3 = 14, A = 42 confirmed by the clamp at 42.0): ask the
user what they expected before changing it.
NEW FEATURE REQUEST (user 2026-10-22): WoR's 6th star: when the last note is hit with 100% notes, the 5-star badge
goes to 6 with the same star animation (quickplay, single and band); user's WoR crop: the gold star shows '6'.

## 2026-10-22: user's in-game test of face-off v6 / battle v12 (OPEN, work these)

Clip `OneDrive\Videos\GH\WTDE_current_faceoff_battle.mp4` + the user's crops (WoR reference: versus meter frames).
1. Versus meter: WoR tints each half: active side bright (P1 blue / P2 red), inactive side dark (dark blue / dark
   red, not brown). Both score boxes are glued to the dial: each box's inner TOP corner touches the dial's bottom
   corner on its side, boxes drawn IN FRONT of the dial. Streak counts of 3-4 digits overflow the square: size per
   digit count, or one size that fits 4 digits.
2. Where the two highways touch, the WoR border sits a few px too high (gap at the bottom): lower the border, then
   move the highways a bit further apart so the borders don't touch.
3. Multiplayer highways (face-off): pieces not glued to the highway; streak lights show the wrong textures (the
   1-player fix from long ago is missing here); SP tube doesn't track (0:36-0:38 P1 has half a bar: no glow, no
   electricity, not at half; texture looks wrong; 0:42 activation drains from below the bottom). Goal: the exact
   1-player (quickplay) setup on every player.
4. Versus needle stops at ~70% of a side (the DE's -51.5..51.5 deg vs our 180-degree dial): remap like the
   quickplay rock needle fix.
5. Battle: rock tube not glued to the highway; highway gap issue in every multiplayer mode (band has more issues,
   later). Slots look perfect: move them a little further under the highway so the arms barely show.
6. Battle cards: right place; shrink the card radius a bit so the slot border shows; z order wrong: the first card
   must be in front, then the next, etc.
Plugin log of the run: battle needle stand-in found, rot range grew to -21.6..37.4 (swing 42); cards moved to slots.
BUILT 2026-10-22 (plugin 1.38 + mod, tests 25/25, NOT installed, mocks docs/mocks/mock_versus_v7_zoom.jpg,
mock_battle_v13.jpg): item 1 (dial red half tinted DIAL_RED_GAIN, boxes hang from the dial corners DIAL_ART /
BOX_ART, in front; streak text fit_width 'scale each line if larger' STREAK_FIT), item 2 (wor_1g.BORDER_DY 4 on the
theme's border offsets + SEP 19 -> 22: UNVERIFIED, needs the game), item 4 (needle_src twin + plugin vs_needle x
NEEDLE_K 1.65), item 5 slots (VISOR_INSET 4 px towards the highway), item 6 (CARD_FILL 0.8; plugin sets card z
19 + (3 - slot) * 0.02, cards recognised by z 19..19.1), item 3 lights (plugin set_lights picks the colour set from
the meter's own badge texture kOurMult; the multiplier query returned x1 in face-off).
User 2026-10-22 on that: streak lights must keep singleplayer colours (x1 IS pink); the real bug is the DE's stock light
textures on the multiplayer meters -> reverted the badge-colour change; plugin our_meter() now also recognises a
meter by any of its lights or a sibling multiplier badge (kOurMult), + log 'streak lights: widget ... set'. Score boxes
tucked BOX_TUCK 15 under the dial (mock docs/mocks/mock_versus_v8_zoom.jpg). Battle rock needle poorly tracked (user
crop: red LED lit, needle at the red / yellow boundary): plugin logs 'battle track: deg / health / zone / t | alphas'
once a second for the next test (compare the zone with the DE-driven LED alphas; then fix kBNeedleD stops or the
angle -> health map). Plugin 1.38 + mod INSTALLED 2026-10-22 03:02 (hash checked; the user had tested the old 1.37 build by mistake).
STILL OPEN: item 3 star power tube per player + gluing, item 5 rock tube gluing (+ needle tracking above). Cause found: the DE moves 2-player
highways in 3D (get_highway_pos_and_scale Pos, scale 1), so on screen the shift shrinks towards the horizon (~y 213,
where RAIL_L / RAIL_R meet); our maps move pieces by a constant SEP (hence ROCK_NUDGE). Plan: (a) a shift(y)
linear in y, zero at the horizon, fitted on the user's clip (f37.5: canvas = crop (240,135,1680,945) of the
letterboxed 1920x1080 frame); (b) per-player 1-player tube: every 1-player sp_* element carried through the player's
rail map (sprites rotated / scaled, clip + feather windows as screen boxes), plus a per-tube geometry table so the
plugin's tube engine (smooth fill, plasma, glows, burst, feathers) runs per tube (StarPower array, widget with 3
segments accepted).

## 2026-10-22: 2-player modes redone from scratch (face-off v6 / battle v12: INSTALLED 01:30, not tested in game)

User (2026-10-21, night, with their WoR 1v1 frame): Face-Off, Pro Face-Off and Battle are 2-player only in the DE, so:
- **Face-Off / Pro Face-Off** (tools/wor_versus.py): WoR's 1v1 layout only: the dial + one score box per player
  (HUD_band_battle_score, P2 mirrored, blue / red stripe): note streak in the small outer square (the DE's
  p1/p2_streak_number_text in the slide window: shown only while the DE's streak is on, its own threshold), score
  in the wide window (commas: plugin hook on the native seinttostring). **Dropped:** placing badges + burst,
  per-player bars, difficulty icons (their textures too: theme pak 3.99 MB). The DE's multiplier nixie lands on a
  hidden element (kVsNixieMap still needs the WoR_HUD_vsmult_* names). Highways keep SP tube + streak meter.
- **Battle** (tools/wor_battle.py): rock tube kept; no streak meter / note streak / SP tube; attack slots = the
  streak meter visor (our WoR_HUD_mult_1 art: ring + arm) three times where the SP tube goes, scales 1 / 0.85 /
  0.72 up the rail, one behind the other, arms on the rail, baked in the battle orientation (WoR_HUD_bvisor; hud_2d
  elements don't rotate); cards in the glass (CARD_FILL), the DE's empty-slot icon blank. The DE rings, disc and
  their textures are gone. Card table changed (kBCard 44 -> 31): **plugin 1.37** built (plugin/build/), not installed.
  User on battle v10 / v11 (2026-10-22): keep the ring and its SHORT arm (the bit joining it to the rail), cut only
  the long stick glued to that arm, which ran behind the stacked rings (VISOR_ARM box kept, the art cut at the rim
  elsewhere; VISOR_RING re-measured: ring centre 113.5, 96.5, rim r 40). v11 wrongly cut the short arm too.
- **Highway spacing (user 2026-10-22):** the games' 2-player highways touch; ours must too, corrected for the WoR
  border's thickness: SEP 30 -> 19 (the clip at 30 showed a 22.5 px gap between the borders at the screen's bottom
  edge; at stock spacing they overlap ~37 px). Every 2-highway layout, the wrapper and the card table follow SEP;
  plugin 1.37 rebuilt with it. mock_battle --current moves the clip's highways from FRAME_SEP 30 to SEP.
- Mocks: `docs/mocks/mock_versus_v6.jpg` (+ `_zoom`), `docs/mocks/mock_battle_v12.jpg` (+ `_zoom`; frame: the user's
  clip 1:15, `python tools/mock_battle.py <frame> <out> --current` for frames of the current build). The grey smear
  on the battle rails is the mock's inpainting of the old rings, not the layout.
- **Face-off crash (2026-10-21 23:48, build v2 + 1.36):** not the HUD. debug.txt: face-off's random venue pick
  (quickplay_choose_random_venue) chose venue 0xc53f60c5, no zone pak loaded ("changing reverb settings to None
  zone"), then apply_band_logo_to_venue -> "CRITICAL: Zone not found" and the DE's crash handler closed the game.
  Pick a venue by hand to test face-off. The earlier dumps (19:13, GHWT_Definitive.exe.39224.dmp) are a different
  crash: access violation in the render path (+0x100fab inside a d3d9 call), mode unknown.
- **Approved and installed 2026-10-22 01:30** (`build.py --install` + plugin 1.37 copied, hash checked). Next: test
  face-off (a fixed venue) and battle.

## Session stopped 2026-10-21, late (user request): where to resume

HEAD = 4fc5bc6 + this note: versus rework v2 + plugin **1.36**, built, tests 25/25. **Installed 2026-10-21** (user said
to apply the plan: `build.py --install` + plugin 1.36 copied to the game, hash checked); **not tested in game yet**.
Mock v2: `docs/mocks/mock_versus_v2.jpg`, `_zoom.jpg`.
User feedback that drove it (their WoR 2v2 frame: team bars "x4 | 150" / "137 | x2", per-player bars "+8 | 100"):
- the DE has teams (p4_pro_faceoff / p8 "Band vs Band": the versus props are per SIDE: band1/2 score, multiplier,
  streak, SP). Team bar (HUD_band_battle_score, P2 mirrored via WoR_HUD_vs_score(_back)_m) = side multiplier AS TEXT in
  the square + side score. Multiplier text = baked textures WoR_HUD_vsmult_1..4 / sp2..sp8 ("x" fontgrid_text_a1 +
  number fontgrid_numeral_A2, white like WoR's uidesc_HUD_band_battle; no SP colour there); plugin 1.36 kVsMult /
  kVsNixieMap swap the DE's HUD_score_nixie_* names to them on those elements.
- per-player bars (competitive_meter back/frame/stripe at 640 -/+ PBAR_DX, PBAR_K 0.70): player note streak (NO "+":
  WoR's "+N" is its point system) | player score, same font/size, SCORE_K 0.26 everywhere. Bound in
  WoR_HUD_HUD_attach_widget_band_faceoff_meter by AttachHudWidget player1/2_status Score / note_streak ->
  pscore_N_text / pstreak_N_text, only when current_num_players = 2 (4p still uses the DE's desc). Third square
  (WoR difficulty icon) empty.
- every highway keeps its SP tube AND streak meter in face-off: wor_mult_mp's alias_player_multiplier now points at a
  hidden stand-in (mult_die_standin), so the DE's face-off Die (GH:588-594, the only user of that alias) kills that.
- the team bar's old "+N" streak window is kept invisible (alias_streak_pN needed by the DE's streak animation).
User's answers (2026-10-21, late): (1) the side streak is shown: in 2-player a side is one player, so that is the
streak in the per-player bar on the highway (kept); in the 4-player team layout it goes left of the team score;
(2) no team layout with only 2 players. Done: the team bars (score_container_N) are alpha 0 in our desc (2-player only;
elements kept for the DE's props and alias_streak_pN). Mock v3 `docs/mocks/mock_versus_v3.jpg` / `_zoom.jpg`.
User on v3 (2026-10-21, late), done in mock v4 (`docs/mocks/mock_versus_v4.jpg` / `_zoom.jpg`), built, tests 25/25,
**NOT installed, awaiting approval** (install = `python build.py --install`; plugin unchanged, 1.36):
- **The mocks v1-v3 were mis-registered:** the clip frames are the 2560x1080 game letterboxed, and the mocks drew the
  canvas over the whole squashed frame. tools/mock_mp.py `register()` now takes the centred 16:9 part (like
  mock_battle); feed it frames straight from the clip (ffmpeg -ss 36 / 128, 1920x1080). The layout geometry
  (wor_battle rails) was right; PBAR_DX had been tuned on the bad mock: the per-player bars now sit on
  highway_top_centre (that was the "streak counter not aligned on the 2nd highway").
- WT streak lights: frame residue in the mock (the DE's player_meter lights; in game our wor_mult_mp replaces that
  desc); the mock now inpaints the DE elements before moving the highways.
- 1st place: the starburst gold (BURST_RGBA, WoR clip hue ~44 deg), normal blend (added, it washed out to white).
- Sides: P1 blue, P2 red (P_RGBA swapped); the dial mirrored (FLIPPED: blue half + blue arc on the left).
- Difficulty: WoR's icon_difficulty_* in the per-player bar's third square (pdiff_N, set by the face-off wrapper from
  playerN_status.difficulty with plain ifs). Theme pak 4.13 MB (limit 4.19 MB).
Then 4-player Pro Face-Off (hud_3g1v): team bars + side streak left of the team score.
Theme pak 4.10 MB (limit 4 MiB = 4.19 MB): budget textures before adding more.
Done: install + push. Next: ask for the test run (checklist below, face-off items updated: team bars + per-player bars
+ streak meter per highway), and get answers to the two open questions above.

## Session stopped 2026-10-21 (earlier): where to resume

Installed in the game = HEAD (mod + plugin 1.35), nothing tested in game since battle test 2. Last user feedback (versus
score bars, from their WoR frame: team bar "x1 | 1", per-player bar "+1 | 1"):
- done: placing squares bigger with the rank inside (RANK_D 78, RANK_FACE), score font SCORE_K 0.30, the streak as
  "+N" in the score bar's first square (window streak_mask_N > container streak_N = alias_streak_pN, WoR "+" texture
  WoR_HUD_plus + the DE's p1/p2_streak_number_text; the DE's face-off streak animation slides it out of the window when
  the streak ends). Mock: tools/mock_mp.py -> scratch; close-up as the user saw it: score bars "+64 45,625".
- the LAST change (streak "+N" window) is built and installed but `python tests/run_offline.py` was NOT re-run and it
  is committed together with this note: run the tests first.
- open question to the user: the multiplier nixie badge still sits at each bar's outer end; WoR shows "x1" as text in
  that bar (the DE only gives the nixie texture, no number). Ask whether to drop the badge from the versus bars.
- user wants it tested next: quickplay, 2-player band, face-off, battle (see the checklist below).

## Built overnight 2026-10-21 (untested; plugin 1.35): test these first

See MODLOG "v0.50 WIP + plugin 1.35". Test in this order (ask before launching; quickplay first):
1. Quickplay 1 player: unchanged? (no messages there already). Then 2-player band / co-op (drums + guitar): per-player
   WoR rock tube (one LED, needle slides; log "multiplayer rock needle: remapped"), WoR SP tube per player (fills?
   which amount: the player's own or the band's?), multiplier badge on the tube top WITHOUT the instrument icon (log
   "multiplier: highway instrument icon ... replaced"), no "01234567" bar, no messages (Hot Start, SP Ready, streaks).
2. Face-off / pro face-off: highways 30 apart, WoR dial + team bars + scores + multiplier nixies, "1st" badge with
   starburst on the LEADER (if it shows on the trailing player, swap lead_1/lead_2 in wor_versus props), SP tubes,
   no rock tube, no messages.
3. Battle (plugin 1.34 fixes + no attack names / alert cards above the highway).
Logs: `wor_hud_fixes.log` (swap lines for hud_create_message, faceoff meter, player health), debug.txt.

## Next: face-off / pro face-off, band, vocals (user 2026-10-21) -- research DONE, first build above

User's current-state clip: `Downloads\Video Project 25.mp4` (0:00-0:53 face-off + pro face-off: the DE's GH3-style top
score bar and dial, highways touching; 0:53-1:46 battle; 1:46-end band: the DE's WT band meter top-left and per-player
bars showing "01234567" placeholder text). WoR references: `OneDrive\Videos\GH\WOR_face_off.mp4`,
`WOR_full_band_gameplay.mp4`, `WOR_microphone_gameplay.mp4`. Earlier parked mock: docs/mocks/mock_modes_v1.jpg,
rules docs/MODES_RULES.md (update it with the research).

User's requirements:
- Remove the messages above the highway (Hot Start, Star Power Ready, attack alerts, etc.) in **all modes** for this
  theme (1-player already ships without them: wor_1g.layout(no_messages=True)).
- Face-off / Pro Face-Off: WoR versus look: per-player score group (WoR's own score bar design), WoR's versus meter
  (different texture from the band meter), a placing per player (1st glows), star power tube + multiplier kept, **no
  rock meter**. Highway spacing like battle. The DE's SP highway effect already works on every highway; the tube not.
- Band: rock meter, star power tube and streak multiplier kept; WoR star power is per player (the DE's is shared:
  find a workaround, e.g. show the same amount on every player). Remove the instrument icon from the highway; use WoR's
  failed-instrument and instrument-icon textures.
- **Research done 2026-10-21: read `docs/MODES_RULES.md` "Research 2026-10-21" (+ docs/research/*).** Original brief:
- Research (mechanical, cheaper model): (1) GH wiki (guitarhero.fandom.com) on both games: versus / face-off / pro
  face-off, band (shared vs per-player SP, band multiplier, revive), multiplier rules per instrument, vocals scoring and
  the precision wording (WT: "Awesome / Strong / Good / Okay / Messy / Weak"-style vs WoR) -- write findings into
  docs/MODES_RULES.md with sources. (2) Identify every HUD asset in the three WoR clips and find it in
  `E:\Dev\ghwt\ghwor-extract` (texture png folders + decompiled descs/scripts: versus meter, score groups, placing
  badges 1st..4th + glow, multiplier bubble, band score / rocket, instrument icons, failed-instrument icons, vocal
  highway parts, precision text); list name -> file -> where used in docs/MODES_RULES.md. (3) The same for the DE's
  current HUD in the user's clip (which descs/layouts the DE uses per mode for our theme: theme rows in hudthemes,
  e.g. 0x6bd128d8 = battle layout; find the face-off and band ones).
- Then (expensive model): mocks per mode on frames of the user's clip, approval, build.



- **Dev folders:** everything lives under `E:\Dev\ghwt`: this repo, `ghwtde-ultrawide-fix` (separate repo, bundled
  in our package), `ghwt-bg-shader`, `tools` (Guitar Hero SDK, NodeROQ), `ghwor-extract`, `ghwt-extract`,
  `reference-video`, `reshade-6.8.0`, `asi-loader-9.7.4`, `game-backup-2026-10-06`, `reshade-backup-2026-10-10`.
  Defaults in `tools/paths.py`.
- **Game:** GHWT:DE at `D:\Games\Guitar Hero World Tour`; config
  `OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition\GHWTDE.ini` (`HUDTheme=ghwor`,
  `GemTheme=ghwor`, `Preferred*Highway=GH5_Highway`, 2560x1080). The `GHWTDE.ini` in the game folder is not the live one.
- **Released: 0.49** (`releases/GH5-WoR_HUD_0.49.zip`, 23 MB; bundles Ultrawide Fix **1.0**). **Installed (from
  HEAD, version string still 0.49):** mod `WoR_HUD` + theme / gem / UI paks + `wor_hud_fixes.asi` **1.33** (battle
  mode rework) + `ghwtde_ultrawide.asi` / `.ini` **1.1** (no ReShade add-on any more) + ReShade (preset, `ghwt_bgfx.addon32`,
  which steps aside on DXVK). The package (`build.py --package`) bundles Ultrawide 1.1's asi + ini since 6e398df.
  Menu music: All Main Menu Music (its own repo; installed with Guitar Hero, GH II, Encore 80s, Aerosmith on).
- **WoR look, all choosable as "Guitar Hero: Warriors of Rock":** helper pills (+ gamertag pill), loading screen,
  menu popups (WoR frame, black background, brush bar; arrows coded but not showing), failed / song ended box, pause
  menu, You Rock (WoR's exploding text, flipbook lightning / ball / explosion, glow, WoR sound), star power sounds,
  rock needle, battle mode (0.50 WIP, rebuilt 10-21, untested, see Start here 1).
- **Confirmed by the user in game:** pills, menu music, pause (no crash, layout), popup look, loading ball, star power
  highway, career needle, every ultrawide screen; Ultrawide Fix 1.1 and All Main Menu Music 1.0 (2026-10-20).
  **Never confirmed:** fail box calibration, YOU ROCK round 3 (letters, gravity 3500, glow, sound), rock needle
  stand-in (plugin 1.31), popup message size, popup arrows (did not show), battle mode (rebuilt 10-21, untested).
- **Other repos:** Ultrawide Fix 1.1 (github.com/jgoa156/ghwtde-ultrawide-fix: ASI plugin, Hor+ 3D FOV, 2D layer at
  16:9; its 2D hooks go in at Direct3DCreate9 so wor_hud_fixes.asi still finds 0x5a05e0 untouched); All Main Menu
  Music 1.0 (github.com/jgoa156/ghwtde-all-main-menu-music, `python build.py --install <game>`; never replace the DE's
  menu_music_songs from its QBName QB: crashed the game at boot).
- **Confirmed in game (2026-10-10):** WoR star power highway effect (0.47 / plugin 1.24: cyan rail glows, stars up
  the rails, strikeline rush; MODLOG "v0.47"), career rock needle (plugin 1.22), the new preset, every ultrawide screen
  (title, menus, song list, loading, YOU ROCK themes, song intro, left-pinned menus). User: the occasional crash
  seems gone.
- **ReShade preset:** `GHWoRHudModPreset.ini` = Behon's GH5WORStyle v2 (Nexus guitarheroworldtour mod 2021, built on
  Ricochet27's GH5/WoR ReShade) + our GH5_Grade, AdaptiveTonemapper, vort_MotionBlur. qUINT (MXAO, ADOF, sharpen)
  is "all rights reserved": not shipped, users tick it in the ReShade installer. Credits in THIRD_PARTY_LICENSES.txt.
- **Known issues:** face-off crashes (no dump yet: WER LocalDumps for GHWT_Definitive.exe not enabled); face-off /
  battle HUDs not adjusted for ultrawide; the DE's SP highway glow leaks a little above/below the highway (minor);
  the WoR star power highway effect is only checked with one player.
- **Lessons (don't repeat):**
  - a mod cannot redefine a game script (the engine ignores it; `tests/run_offline.py` guards it). Workaround that
    works: ship the logic under a WoR_HUD_ name and let the plugin copy its QB symbol entry over the DE script's
    (symbol table `[0xd48f5c]`, see MODLOG "plugin 1.22"); to wrap a DE script, kScriptSwaps saves the original
    into a placeholder first (MODLOG "v0.47");
  - a CreateScreenElement whose parent doesn't exist crashed the game (SetParent 0x5a0240); plugin 1.24 guards it
    and logs "missing parent" in wor_hud_fixes.log. Our QB printf lines DO reach debug.txt (tagged [0xd8b982c2]);
  - never put a $Func$${...}$ struct argument inside a parenthesised expression (AND/OR): it crashed the game
    (0x5f0a8e); use plain ifs or the $id$ = $x$ form;
  - CreateScreenElement overwrites the calling script's `id` with the new element's; SetScreenElementProps on a
    missing element crashes the game (0x63a133): keep ids in other locals and check ScreenElementExists first;
  - mod list text (Mod.ini / menumusic.ini): only letters, digits, spaces and , . : / (the DE fonts lack the double
    quote and others);
  - the DE doesn't animate AnimatedTexture_UI flipbook materials (WoR's lightning / ball / explosion): it draws the
    whole sheet. Use one texture per frame switched by WoR_HUD_flipbook (sprites) or static one-cell materials built
    on an ImmediateMode_UI / UI_Col_Tex_2D material (particles; a particle's size follows its texture size);
  - WoR scripts can use forms the DE ignores (`$apply_gravity$ = $true$`): prefer the DE's own spelling; DE strings
    are localised keys (GetUpperCaseString leaves them as they are);
  - a desc text whose fit_height is "clip top lines" vanishes when the font is taller than its box;
  - textures that live in `z_in_game` can't be overridden from our paks (the per-song reload wins); gem-pak textures can;
  - after changing star/score geometry in `tools/wor_1g.py`, ALWAYS run `python tools/gen_plugin_names.py` before
    `pluginuild.bat`;
  - send mocks to the user with SendUserFile (writing them to `verify/` is not enough);
  - never insert a line above a script's `${ ... }$` default-parameter block: it voids the defaults (froze YOU ROCK).

## Task list (2026-10-20, user order)

1. Battle mode rework: built 2026-10-21 (Start here 1); the card above the highway is still to be designed with the user.
2. One test run (ask first): battle + every "never confirmed" item above.
3. Release HUD 0.50 (bundles Ultrawide 1.1): bump VERSION in build.py, `python build.py --package`, zip to releases/,
   push; Nexus page text like the other two repos' `docs/NEXUS.txt`.
4. Popup up/down arrows: code ships (WoR_HUD_create_popup_warning_menu, ARROW_UP_DY / ARROW_DN_DY in wor_menus.py) but
   they did not show in game; user: leave it for now.
5. Face-off crash (enable WER LocalDumps for GHWT_Definitive.exe first) + face-off layouts.
6. Multiplayer / vocals layouts (docs/MODES_RULES.md, mocks in docs/mocks).
7. Song list side art (`4b93dd1e` / `b19ce07d`, the user is remastering them).
8. Drum animations (docs/DRUM_ANIMS_PLAN.md + the 10-16 scan; GH5 is now pulled to `E:\Dev\ghwt\gh5-extract`).
9. Full code review of the three repos (HUD, ultrawide, all main menu music) for optimisation.
10. Small visuals: WoR's Star03 sliver for the star power burst; the DE's SP highway glow leak.
11. Ideas to evaluate: game-catalogue jump menu (SELECT / its PC key; each install's library differs); song list
    sorting that ignores a leading "The".
12. All Main Menu Music "now playing" toast (bottom-left: song, artist, game, like EA Trax games): plan in that repo's
    README (Title= / Artist= / Game= per track, a native hook on the menu-song picker, mock first).

Dropped: WoR highway lines (the user was wrong about them); the menu music collection installer (replaced by
All Main Menu Music).

## How to work on it

- `python build.py [--install] [--package]`; `python tests/run_offline.py` (25/25).
- Mocks: `python tools/mock.py <out.png> --crop tubes|tube-ends|score|full --variant "label: NAME=expr" ...`
  (base `verify/mock_inputs/base.png`, rebuilt by `tools/mock_base.py`).
- Plugin: `plugin\build.bat`; after changing star power geometry in `tools/wor_1g.py` run
  `python tools/gen_plugin_names.py` before building it. Copy `plugin/build/wor_hud_fixes.asi` to the game folder.
- Crash dumps: `%LOCALAPPDATA%\CrashDumps`; `python tools/dump_info.py <dmp>`, `tools/dump_mem.py <dmp> <addr> <n> --dis`.
- Refactor guard: `python tools/build_hashes.py save|check <json>`.
- Machine paths: `tools/paths.py` (env overrides). Game assets are never committed.

## Rules you set

- Ask before every game launch, and batch changes into one build.
- Mock first: show the mock and get approval before applying a layout or setting.
- Use only textures and fonts extracted from the games. Cropping, tinting, flipping and compositing are fine.
- The HUD draws above the highway. Prefer targeted fixes over rewrites.
- Screenshot collector (`tests\collect_session.py`): only when asked, started detached (no task notifications).
- Commit and push finished work to the repo.

## Single-zip release (done 2026-10-06)
- `build.py` builds ONE mod (`WoR_HUD`): no-messages layout is the only 1g layout (desc `hud_1g_ghwor`, theme id `ghwor`);
  dark metal sections + `$change$` lines live in `WoR_HUD_Load`. `--package` makes one zip: mod + paks + plugin +
  ASI loader at the root, and `Optional - ReShade (WoR shaders)` (ReShade 6.8.0 d3d9.dll, ReShade.ini, GHWoR.ini,
  reshade-shaders, ghwt_bgfx.addon32). ReShade is listed as a requirement (for the shader look only) in the READMEs.
  Since 6e398df the root also has Ultrawide Fix 1.1 (`ghwtde_ultrawide.asi` + `.ini`); the old addon32 is gone.
- Vendored ReShade files: `extras/reshade`. ReShade dll: `E:\Dev\ghwt
eshade-6.8.0`, ASI loader:
  `E:\Dev\ghwtsi-loader-9.7.4` (paths.py `RESHADE`, `ASI_LOADER`). `addon/build/ghwt_bgfx.addon32` = the tested binary.
- The user's game folder was reverted: old install moved to `E:\Dev\ghwt\game-backup-2026-10-06` (incl. GHWTDE.ini.bak);
  GHWTDE.ini now `HUDTheme=ghwor`. Next test = extract the Desktop zip into the game folder (+ the optional folder's
  contents) as a clean user would. Release notes: `docs/RELEASE_NOTES.md`.
- Known issue: the game still crashes SOMETIMES (not only on theme switch); log it, no fix yet.

## 2026-10-22 late 2: 60 fps plasma (built, NOT installed) + band -> face-off crash (open)

- Plasma back to 60 fps / 120 frames: the frames now go into the always-loaded UI pak (wor_hud_ui, 18.35 MB, no 4 MiB
  cap there; the plugin swaps them in by name). Theme pak 3.27 -> 2.17 MB, so ~2 MB of theme budget is free again.
  Plugin rebuilt (names.h regenerated) but neither the mod nor the plugin is installed.
- Crash (user, 1.40): played band, then face-off, crashed entering the song list. Dump
  `%LOCALAPPDATA%\CrashDumps\GHWT_Definitive.exe.3328.dmp` = same as the 03:47 one: exception 0xc00001a5
  (invalid exception handler) at exe+0x5728f2, an MSVC EH funclet (`mov eax, 0xae8314; jmp __CxxFrameHandler`), so a
  C++ exception was thrown and the SEH chain was rejected. wor_hud_fixes.asi+0x2e3b on the stack = set_parent_hook
  (map: plugin/build_map.bat on HEAD's names.h). Last plugin log line: "missing parent: element 318f3a0f asked for
  parent 4ac58b9f" = custom_setlist_continue_helper under custom_setlist_helper_container (DE
  scripts/guitar/menu/states/layouts/ui_setlist: setup_custom_setlist_helpers creates the "continue" pill under that
  container, which ui_create_setlist only makes when for_custom_setlist = 1 and ui_destroy_setlist destroys).
  Next: find why the container is gone in face-off (stale for_custom_setlist / num_songs after band?), and make the
  guard safer: attach orphans to root_window by id instead of parent 0, or skip creating them. Then check whether the
  stock DE (mod off) crashes the same way.

## 2026-10-22 late 3: plugin 1.41 + the 60 fps build INSTALLED (not tested in game)

- Crash re-read: `asi+0x2e3b` on the dump's stack is the return address of set_parent_hook's NORMAL path (parent
  found), so it is a stale stack value (dump_info scans, it doesn't walk), not proof the guard frame was live. The log
  has exactly ONE missing-parent line before the crash, so it is not a duplicate-id re-create.
- SetParent (0x5a0240) with parent 0 takes a separate branch: no parent lookup, the element goes onto the manager's
  top-level list (0x5a35a0 on [element+0xc]) with no window parent. The guard used that branch. 1.41 parents the
  orphan to `root_window` (0x56a1eae3, looked up first; falls back to 0 only if it is missing) so it takes the normal
  branch, still hidden. Log line now says "attached to root_window".
- DE side (why it is orphaned): setup_custom_setlist_helpers creates custom_setlist_continue_helper whenever
  num_songs != 0, and it is called from ui_setlist_choose_song / ui_setlist_custom_remove(_all) without the
  for_custom_setlist check the other callers have; the container exists only when for_custom_setlist = 1
  (ui_create_setlist_spawned) and ui_destroy_setlist destroys it. So a stale band quickplay list (num_songs > 0)
  in the face-off song list is the likely trigger. The stock DE would null-deref in SetParent on the same path.
- Installed now: mod + paks from 49f4158 (60 fps plasma, theme pak 2.27 MB) and plugin 1.41 (hash checked).
- Test (ask first): band -> face-off -> song list (the crash path), then the 1.40 checklist above. If it still
  crashes, enable full dumps (WER LocalDumps DumpType 2) so code pages and the real stack are captured, and try the
  same path with the mod off.

## 2026-10-22 late 4: battle fade-in + 6th star INSTALLED, purple drum fill awaiting a pick (not tested in game)

- Battle fade (item 0): battle's layout has no desc_interface, so no hud_root (the element every other mode fades in:
  created at alpha 0, faded to 1 over 0.25 s by move_2d_elements_to_default after its intro loop). Plugin 1.41 swaps
  setup_hud (wrapper hides HUD_2D_Container<p> in p2_battle with our theme) and move_2d_elements_to_default (in
  p2_battle: spawns the DE script, waits morph_time (+0.5 s when [af530ac6]), fades HUD_2D_Containerp1/p2 to 1 over
  0.25 s). tools/wor_battle.py scripts(). The attack cards live under battlemode_container (not faded, appear later).
- 6th star: build.py SIXTH_STAR_SCRIPT wraps the DE's star rating dbc9b21e (guitar_progression, polled per frame by
  star meter 0x08b99cb3, caps at 5). Returns 6 / progress 1 when: 5 already, theme flag WoR_HUD_sixth_star, gamemode
  type quickplay, no-miss flag [454d9e8b] = 1, and every shown player's notes_hit = total_notes = max_notes (one of
  them is the chart count; unconfirmed which, so the worst case is no 6th star, never an early one). The meter animates
  5 -> 6 itself (sparks + sound). Mock docs/mocks/mock_sixth_star_v1.jpg. If it never shows: log notes_hit /
  total_notes / max_notes at song end to see which field is the chart total.
- Purple line (item 13): WoR's line is an AudioVisualize av_preset (og_highway_drum_freeform, Line primitives RGB
  147,0,255 additive, audio-driven wiggle) drawn into a viewport texture; the DE has no AudioVisualize. Port: tint the
  DE's own scrolling Drum_fill material (mat_drum_fill / mat_drum_fill2, DE colour (1,1,1,0.3)) via build.py
  DRUM_FILL_RGBA (None = off; recolour_materials in dark_metal_sections). Mock docs/mocks/mock_drumfill_v1.jpg: soft
  (0.58,0,1,0.5) vs strong (0.58,0,1,0.8). WAITING for the user's pick.

## 2026-10-22 late 5: BAND / MULTIPLAYER = TOP PRIORITY. Next session (cheaper model): capture + calibrate

User 2026-10-22: "what about the band stuff? ... all problems were there, high priority to multiplayer modes fixing,
remember the elements are not tilted in a different way than in singleplay, dont stop till you're done". The user
approved the bot captures below but wants them run on a cheaper model. Rule unchanged: the user starts that session.

### Step 1: frames come from the USER (automation dropped 2026-10-22)
A bot-played capture script (AutoLaunch + window focus) was tried twice and dropped: the game stayed on the title
screen and the focus handling blanked it (user: "looks fucking useless"). Do not rebuild it. The user sends
screenshots of a quickplay band with vocals (ideally guitar + bass + drums + vocals = hud_3g1v, plus guitar + vocals =
hud_1g1v), 2-3 per line-up incl. one with star power. Calibrate from those.

### Step 2: what is wrong / what to do (in this order)
1. **hud_1g1v and hud_3g1v have NONE of our per-player pieces** (wor_versus.edit_layout only runs
   wor_mp.edit_two_highways for hud_2g / hud_2g1v). Every band with a vocalist and every 4-player band shows the
   DE's stock pieces. Generalise edit_two_highways to N instrument containers (g1..g3) with a rail model per layout
   (measure each highway's left / right rail lines in the captures, like RAIL_L / RAIL_R in tools/wor_battle.py).
2. **Angle rule (user, repeated):** every piece keeps the 1-PLAYER angle: uniform scale + translation of the 1-player
   piece (wor_battle.tube_maps does this: no shear / rotation). Only position and size change per highway.
3. **Rock tube offset (hud_2g):** measured on the user's 1.39 band frame (images/79.jpg of session 7a7f6617; canvas =
   (X - 250) * 0.853, Y * 0.853 for the 2000x844 shot): rock tube +74 right of the rail model on BOTH highways (slope
   matched the model), SP tube +16. 1.40's MP_DX -24 left the rock tube ~+50 inside the highway (on the first gem).
   Applied now (installed, NOT verified): wor_mp.ROCK_MP_DX = -50 on BAND_side_meter only. Verify in 2g_*.bmp: the
   tube should sit just outside the left border like quickplay.
4. **P2 multiplier = a white rectangle** in band (1.39 frame): the instrument-icon swap (plugin set_texture_hook,
   kHighwayIcons) only fires when the badge already shows one of our textures (kOurMult). Check the 1.41 captures; if
   still white, also swap when the element belongs to our mult desc (or set our x1 texture in mult_desc's initial state).
5. **Band top-left WT "ROCK" band meter** still shows (band_meter desc). Item 9-11 wanted the quickplay score group
   top right (wor_band, done in 1.40) and no huge instrument icon; check whether the WT dial must go (ask the user if
   unclear: WoR has no such dial).
6. Then items still open from the 1.39 / 1.40 lists (HANDOFF sections above): band score group padding with vocals,
   bulb grow, every tube shows band SP.
Mock each change on the captures before installing (rule: mock first), batch, install, then ask for the next test.

### Crash notes (2026-10-22, both dumps re-read with the ORIGINAL exception)
The 0xc00001a5 "invalid exception handler" is secondary: the real exception record is on the stack (scan for code
c0000005 in the thread's stack memory). 05:13 dump: access violation at 0x4e6022 (read [ecx+0x214], ecx 0) on the
setlist path (the orphan pill; 1.41 root_window guard). 06:37 dump (1.41, quickplay mid-song, crowd -> GOOD): access
violation at 0x5b88a4 (read [0+4]) in vtable slot 10 of Obj::CCompositeObject / CCompositeObjectInstance / CPlayer
(RTTI): a 3D game object's lookup by its own id returned null. No mod frame on the stack: most likely the DE's venue
object bug (same family as "Zone not found"), not the HUD. Tools used: scratchpad scripts mdexc.py / mdctx.py / rtti.py
(session 6b994b8a); worth moving into tools/dump_info.py if crashes continue.

## 2026-10-22 evening: band automation WORKS + band layouts redone (installed; last 3-highway fix not re-captured)

- **Automation:** `python tests/capture_band.py --lineup 2g|3g|3g1v|1g1v|2g1v` (one launch per call; delete
  tests/results/capture_band.done to allow another). The DE's own [AutoLaunch] is developer-only (guitar_startup skips
  it while WTDE_IsUser (cd840670) is true; that check reads the devs' babe.face key: not touched). The mod's opt-in
  hook (build.py TEST_AUTOLAUNCH_SCRIPT, plugin 1.42 swaps ui_create_boot_iis): with [WoR_HUD] TestAutoLaunch=1 the
  title screen runs the DE's AutoLaunch setup 0x581325cc (players / parts / bots / song from [AutoLaunch]). The script
  sets and restores the ini, keeps ONLY the main window (class AspyrGH3) in front (the old helper also focused
  ReShade's D3DProxyWindow: that was the screen blanking), screenshots every 15 s from T+90 s (PIL ImageGrab; the
  ghwt_bgfx dumps write nothing on this install; debug.txt and wor_hud_fixes.log are locked while the game runs) and
  closes the game at T+330 s (it sits on the results screen otherwise). No venue loads (black background): good for
  calibration. Captures: tests/results/band-20261022-1724xx..1736xx (2g, 3g, 3g1v).
- **hud_2g band:** verified in the capture: rock tube on the left rail (ROCK_MP_DX -50 works), SP tube right, x4,
  score group top right.
- **Orange rail glow gone** in every band layout (theme flag cd149bb0 makes highway_streak_glow return): verified.
- **hud_3g1v (3 instruments with or without vocals):** wor_mp.edit_three_highways: our player_meter / Star_Power /
  BAND_side_meter on g1..g3 = the 2-player pieces under one uniform scale + shift per highway (highway_map, fitted on
  RAILS_3G measured from the captures, 1-player angle kept). Verified: the DE's pink streak stacks + instrument icon
  are gone, x4 badges + SP tubes on every highway, score group top right under the vocal highway
  (wor_band.OFFSET_BY_CONFIG). Last fix (63ac2e6, installed, NOT re-captured): MP_DX / ROCK_MP_DX dropped for
  3 highways (they had put the SP tubes ~17 px and the rock tubes ~65 px left of the rails). Next: one 3g1v capture.
- Still open: band SP fill / per-tube engine with 3 tubes (bots' SP not checked in frames), hud_1g1v and hud_2g1v
  (not captured yet), the purple drum fill pick, the battle fade / 6th star in-game checks.




