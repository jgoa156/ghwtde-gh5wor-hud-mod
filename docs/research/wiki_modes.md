# GHWT vs GH:WoR - gameplay modes and HUD-relevant mechanics (wiki research)

Date: 2026-10-21. Read-only web research; nothing was run or modified.

Abbreviations: WT = Guitar Hero World Tour (the engine GHWT:DE runs), WoR = Guitar Hero: Warriors of Rock, SP = star power.
"FW:" = prefix https://guitarhero.fandom.com/wiki/ (e.g. FW:Rock_Meter = https://guitarhero.fandom.com/wiki/Rock_Meter).

Method note: WebFetch on guitarhero.fandom.com returned HTTP 402 / Cloudflare challenge. The same wiki pages were read as raw wikitext through the
public MediaWiki API (https://guitarhero.fandom.com/api.php?action=parse&page=TITLE&prop=wikitext). Cited URLs are the normal article URLs.
Wikipedia, Gaming Bolt and The Sixth Axis were read via WebFetch. Official manuals (Scribd, manua.ls, GameFAQs boards) could NOT be read
(403 / cover only), so exact on-screen strings and several HUD-layout questions are marked "(unverified)".

Source quality caveat: the wiki is fan-written, partly contradicts itself (flagged CONFLICT below) and says almost nothing about the WoR
competitive HUD. Anything about exact on-screen layout in Face-Off / Pro Face-Off in WoR needs a screenshot or an in-game check.

---------------------------------------------------------------------------------------------------------------------------------------

## 1. Summary table

| Mechanic | WT | WoR | Consequence for a HUD port |
|---|---|---|---|
| Face-Off (alternating sections) | Exists. Players take turns on sections, each picks own difficulty, song cannot be failed by missing notes. | CONFLICT: FW:Face-Off says it appeared "up until" WoR (ambiguous); FW:New_gameplay_features lists Face-Off for WoR; the RockFest list has only Pro Face-Off. Unverified. | DE only needs the WT Face-Off layout; do not import a WoR Face-Off HUD. |
| Pro Face-Off (whole song, highest score) | Exists. Older games and (per wiki video caption) WT show a center meter between the two highways, needle leaning toward the player with the higher score. Lower difficulty earns more points per note. | Exists as a RockFest mode: "standard score attack mode, highest score wins points" (Wikipedia GH5). A review says after song checkpoints it shows the gap to the next-ranked player. Center needle in WoR: unverified. | The WoR "gap to next-ranked player" popup is WoR/GH5-only. In DE show only the score difference / leader that the engine computes. |
| Rock meter in Face-Off / Pro Face-Off | Face-Off: "will not fail the song". Whether a rock meter is drawn: unverified. GH3-era versus uses a needle meter instead. | Unverified. FW:Cooperative says WoR uses an orange/purple versus meter instead of a rock meter, but the sentence is garbled with no second source. | Do not draw a WoR rock meter in DE competitive modes; keep the WT center indicator. Verify in game. |
| Placings 1st..4th | Face-Off / Pro Face-Off are 2-player. No placing text found. | RockFest: 4 local / 8 online players, per-section points (Perfectionist 4/2/1 for 1st/2nd/3rd per The Sixth Axis GH5 preview). | A 1st-4th ladder is GH5/WoR-only. DE has no RockFest; do not add it. |
| Band: star power | SHARED single SP meter; any player can use it; simultaneous use raises the band multiplier. | INDIVIDUAL meter per player; "Star Power overload" spills excess into others' meters. | DE needs one shared SP meter (WT). A per-player WoR SP tube on each highway would be wrong. |
| Band: rock meter | Shared band meter (average of members) plus small individual meters (4 bars). | No shared meter; each player has own meter beside the highway; revival meter when someone fails. | Keep shared band meter; per-player small meters are fine (WT has them). No revival meter in DE. |
| Band multiplier | Black circle beside the rock meter. SP used simultaneously: band multiplier x2 -> x4. No band moments. | Light bulb on the score meter. Max x11 = 4 (all x4) + 4 (all in SP) + 3 (band moment). Band moments not in Quest. | WT has no band-moment contribution and a smaller range. Do not show x11 / band-moment prompts in DE. |
| Revive / rescue | None. Zero-meter player keeps playing but drains the band meter; band fails when shared meter empties. (CONFLICT: FW:Rock_Meter says one player in red "can cause the whole band to fail".) | Revival: failed player gets a red/green revival meter (GH5), others must play well for a limited time or the band fails. Revived player loses SP, restarts in yellow. | No revival UI in DE. Failed-player state must follow WT behaviour. |
| Per-instrument multiplier | Up to x4; x8 with SP (2,4,6,8). 10 consecutive notes per step. | Same baseline; Quest/Power-Challenge powers change it (min x2, max x5/x6, SP x3/x6; x10/x12 shown blue). | Plain x1-x4 / x2-x8 is correct for DE. Skip power-based x5/x6/x10/x12 colours. |
| Vocal judgement wording | WT proper: only a coloured flash at end of phrase. Text ratings Excellent / Solid / Average / Rough / Sloppy first appear in Metallica and later WT-engine games. | No text ratings. A small bar beside the rock meter fills white -> yellow -> green. | "Awesome / Strong / OK" were NOT found anywhere (unverified). WoR has no wording to copy; keep WT-engine behaviour. |
| Vocal star power | From solid/excellent phrases, star sequences, "hype" sections. | Only excellent on blue star-power phrases, plus SP overload; hypes removed; freeform gives no points. | DE keeps the WT set of sources. |
| Failed-instrument display | Instrument icon in the multiplier circle at x1 in band. Distinct failed look: unverified. | Large X over a highway for a failed band moment (not a fail). Red screen glow when meter is red. Failed-player icon: unverified. | Do not copy WoR's X / revival visuals. Check in game what DE shows for a zero-meter player. |
| Battle mode | Present: power-ups replace SP; rock meter present. | Not present (only Wii "Roadie Battle"). | No battle UI needed for the WoR-style port; if WT Battle is playable in DE keep the WT battle HUD. |

---------------------------------------------------------------------------------------------------------------------------------------

## 2. Versus modes

### 2.1 Face-Off (alternating sections)
- "In Face-Off, players take turns playing sections of a song or occasionally playing at the same time in a call-and-response-style game.
  Both players can select their own difficulty level and will not fail the song if multiple notes are missed. The objective ... is to have a
  higher score than your opponent by the end of the song." Source: https://guitarhero.fandom.com/wiki/Face-Off
- Same page: "Face-Off has appeared in every main iteration of the Guitar Hero series up until Guitar Hero: Warriors of Rock." Ambiguous whether WoR is included.
- Mode matrix: WT has Band, Face-Off, Pro Face-Off, Battle; WoR has Band, Face-Off, Pro Face-Off, Mii Freestyle (Wii), Roadie Play plus a RockFest list
  (Do-or-Die, Elimination, Momentum, Momentum+, Perfectionist, Pro Face-Off, Streakers). Source: https://guitarhero.fandom.com/wiki/New_gameplay_features
- The RockFest page itself lists Pro Face-Off but no Face-Off. Source: https://guitarhero.fandom.com/wiki/RockFest
- WT tutorial (Shirley Crowley) covers "Band vs Band" and Face-Off modes. Source: https://guitarhero.fandom.com/wiki/Tutorial
- Wikipedia WoR: GH5 competitive modes carried over and were "expanded to include band-vs-band variants" (Pro Face-Off not named).
  Source: https://en.wikipedia.org/wiki/Guitar_Hero:_Warriors_of_Rock
- WT career Guitar Duels (Zakk Wylde / Ted Nugent) behave like Pro Face-Off: no power-ups, AI streak resets on each hit, higher score wins.
  Source: https://guitarhero.fandom.com/wiki/Battle_Mode

### 2.2 Pro Face-Off (whole song, highest score)
- "all available players play an entire song together ... The objective ... is to get the highest score ... everyone sharing the same note chart (unless on different difficulties)."
- "In older Guitar Hero games, a meter sits in the center of the screen, between the two note highways. Initially, a needle sits at the center of the meter, and as the
  song progresses, the needle leans towards the player with the current highest score."
- Handicap: lower-difficulty players earn more score per note. The page's example video is a WT Hard-vs-Expert match.
  Source: https://guitarhero.fandom.com/wiki/Pro_Face-Off
  ("older games" wording: needle meter confirmed for GH2/GH3 era; only implied for WT by the example video; unverified for WoR.)
- WT multiplier HUD in Face-Off / Pro Face-Off: highways keep bulbs on the side but "the number is next to their score meters, resembling GH3's multiplier"; the note-streak
  counter appears after 30 notes and disappears on a miss. Source: https://guitarhero.fandom.com/wiki/Multiplier
- WoR/GH5 Pro Face-Off: "A standard score attack mode, with the highest score winning points" (Wikipedia GH5). A WoR review says after certain "checkpoints" it shows how far you
  are from the next-ranked player. Sources: https://en.wikipedia.org/wiki/Guitar_Hero_5 ; https://gamingbolt.com/guitar-hero-warriors-of-rock-reviewed

### 2.3 Scores and placings
- WT Face-Off / Pro Face-Off: 2 players, winner = higher score. No 1st-4th text found (unverified for any on-screen "1st/2nd" strings).
- WoR / GH5 RockFest: 4 local / 8 online players, scoring by sections (~30 s each, Wikipedia GH5 https://en.wikipedia.org/wiki/Guitar_Hero_5):
  - Perfectionist: per section highest hit% gets 4 points, second 2, third 1 (https://www.thesixthaxis.com/2009/08/05/guitar-hero-5-rockfest-revealed/)
  - Elimination: lowest score cut when the timer ends; last player wins (same source)
  - Do or Die: 3 misses in a section = out until next section; points per section survived (https://guitarhero.fandom.com/wiki/RockFest)
  - Streakers; Momentum (start Medium, +difficulty after 20 notes, -difficulty after 3 misses); Momentum+ (WoR: SP drops opponents to Beginner) (Gaming Bolt, RockFest)

### 2.4 Rock meter vs versus meter
- FW:Cooperative: "There's also a versus mode, which replaces the rock meter for a meter of Orange and Purple. When said color of either side of the needle is on, that player wins.
  This is used later in Guitar Hero: Warrior of Rock." Source: https://guitarhero.fandom.com/wiki/Cooperative
  -> The WoR claim has no second source and the text is garbled: UNVERIFIED. It is the only hint that WoR competitive uses a versus meter.
- FW:Rock_Meter: the GH3 co-op meter "resembles the face-off indicator more"; in WoR/GH5 each player has a rock meter beside their highway (band and solo).
  Source: https://guitarhero.fandom.com/wiki/Rock_Meter
- Whether a rock meter is drawn in WT Face-Off / Pro Face-Off or in WoR Pro Face-Off is not stated in any page I could read (unverified).
  Face-Off players "will not fail the song" (FW:Face-Off), implying no fail-capable rock meter there.
- What the center meter shows (WT Pro Face-Off): per FW:Pro_Face-Off, which player currently has the higher score (leader indicator). How needle deflection scales with the
  score gap is not documented (unverified).

---------------------------------------------------------------------------------------------------------------------------------------

## 3. Band / full-band mode

### 3.1 Star power: shared vs individual
- WT: "the band also shares the same 'Star Power' meter, though any player may activate it at any time" (Wikipedia WT).
  "Star power is shared in one meter and when there is enough in the meter any band member can use it. If multiple band members use star power within the same time
  period the band multiplier will increase from x2 to x4." (FW:Band)
  "In pre-Guitar Hero 5 games, Star Power is shared equally ... can be used simultaneously. This achieves an even greater band multiplier." (FW:Star_Power)
  Sources: https://en.wikipedia.org/wiki/Guitar_Hero_World_Tour ; https://guitarhero.fandom.com/wiki/Band ; https://guitarhero.fandom.com/wiki/Star_Power
- WT SP meter HUD: six amp bulbs on top of the rock meter; "In Band mode, all 6 bulbs are visible no matter how full or empty the star power meter is."
  Source: https://guitarhero.fandom.com/wiki/Star_Power_Meter
- WoR: "the star power meter isn't shared, and every player has their own individual star power meter"; "star power overload": excess from a full meter is divided
  among members whose meters are not full. Sources: https://guitarhero.fandom.com/wiki/Band ; https://guitarhero.fandom.com/wiki/Star_Power ;
  https://en.wikipedia.org/wiki/Guitar_Hero_5 ("Star Power is now tracked separately for each player").
- WoR SP meter: vertical tube on the right of the highway, fills bottom-to-top, flashes at the middle line (50% minimum to activate); a full meter lasts 8 measures (menu tip).
  Source: https://guitarhero.fandom.com/wiki/Star_Power_Meter
- From WT on, SP phrases keep appearing while SP is active and can prolong it (FW:Star_Power).
- Activation: guitar tilt or SP button; drums: both cymbals (WT: notes missed during activation are auto-played); vocals: tap/blow the mic or press a button (FW:Star_Power).

### 3.2 Multipliers (band, streak, per instrument)
- Per player: x1 -> x2 -> x3 -> x4, advancing every 10 consecutive notes; SP doubles it (x2, x4, x6, x8); a miss / overstrum drops it. WT: 4x cap, doubled by SP (Wikipedia WT).
  Sources: https://guitarhero.fandom.com/wiki/Multiplier ; https://en.wikipedia.org/wiki/Guitar_Hero_World_Tour
- Streak counter: appears after 30 consecutive notes, vanishes on miss/overstrum (WT-styled games and GH3). Same Multiplier page.
- WT band multiplier: "a black circle near the Rock Meter in World Tour" (a light bulb on the score meter in the other games). In WT band play, at x1 the multiplier circle shows the
  player's instrument icon. Rises when members use SP in the same period (x2 -> x4). Score, score meter and streak meter are shared (FW:Band).
- WT "Unison Bonuses": a player on a streak gets an orange-glowing highway; when all members glow, the band is on a streak and gets points for playing in unison.
  Source: https://guitarhero.fandom.com/wiki/Band
- WoR/GH5 band multiplier: light bulb; max x11 when all four have SP active and hit a band moment (4 + 4 + 3). Band moments (fiery notes) add +3; if a member errs,
  GH5/BH show "Band Moment Failed", WoR shows a large X over that player's highway. No band moments in Quest.
  Sources: https://guitarhero.fandom.com/wiki/Star_Power (Band Moments) ; https://guitarhero.fandom.com/wiki/Multiplier
- WoR-only powers (Quest / Power Challenges, not competitive, not DE): Speed Freak (min x2, 5-note steps), Multiplier Extender (max x5 / x6), Star Power Nova (SP multiplier x3 / x6),
  Streak Guardian (rechargeable shields, 3 s), Resurrector, Crowd Hyper. HUD: x5/x6 red; with SP x10/x12 blue with red number.
  Sources: https://guitarhero.fandom.com/wiki/Guitar_Hero:_Warriors_of_Rock/Quest ; https://guitarhero.fandom.com/wiki/Multiplier
- Drums: same streak/multiplier rules; SP by hitting both cymbals. Marked drum solo sections score any notes (https://guitarhero.fandom.com/wiki/Guitar_Hero_World_Tour).
- Vocals multiplier: see section 4.

### 3.3 Rock meter, failing, revive
- WT: whole band shares the rock meter; each player also has an individual meter between the Rock and Score meters (four bars); band multiplier to the right of the rock meter.
  "If one hits red, it can cause the whole band to fail." Source: https://guitarhero.fandom.com/wiki/Rock_Meter
  FW:Band: the band rock meter "is the average of every member's own meter"; score and streak meters are shared.
  CONFLICT (softer): Wikipedia WT says a zero-meter player "can still continue to play, but they drain the overall performance meter for the band". No revive.
  Source: https://en.wikipedia.org/wiki/Guitar_Hero_World_Tour
- WoR/GH5: no shared meter. "Everyone has their own rock meter and if one fails, the remaining players can revive them." Red meter = flashing red glow around the screen.
  Source: https://guitarhero.fandom.com/wiki/Rock_Meter
  Revival: a red/green meter appears; full green restarts the failed player at the current point; full red fails the band; revived players lose SP and restart in yellow;
  repeated failures drain faster. Source: https://guitarhero.fandom.com/wiki/Band ; Wikipedia WoR: "remaining members must play well enough for a limited time".
- Highways in WT band: vocals top, guitar left, drums middle, bass right (FW:Band). Individual meters sit under the band meter in WT; in Metallica / Smash Hits / Van Halen they sit on the left
  of each highway, and in GH5/BH/WoR on the side of the highway (top-left of the vocal highway) (FW:Band, FW:Rock_Meter).
- Meter motion (all games): hit = needle +1, miss/overstrum = -3; start in the middle; encores start in middle green (FW:Rock_Meter).

---------------------------------------------------------------------------------------------------------------------------------------

## 4. Vocals / microphone

- Pitch tunnel + comet; lower difficulties have larger pitch hitboxes. "In Guitar Hero World Tour, the only rating the player would get was a colored flash which
  would appear upon finishing a phrase." Source: https://guitarhero.fandom.com/wiki/Vocals
- Text ratings: "From Guitar Hero: Metallica onwards, the player would receive ratings ...: Excellent, Solid, Average, Rough and Sloppy."
  Table for WT-styled games: Sloppy (red, Beginner, 100 pts), Rough (orange, Easy, 200), Average (white, Medium, 300), Solid (yellow, Hard, 400), Excellent (green, Expert, 500). Same page.
  CONFLICT: the table header says "World Tour-styled games" and FW:Star_Power says WT vocalists get SP from "solid" or "excellent" ratings, but FW:Vocals says WT itself only flashed a colour.
  A contemporary review likewise describes only coloured light per phrase (https://www.gamerevolution.com/review/42242-guitar-hero-world-tour-review, snippet only).
  The strings "Awesome / Strong / OK" were not found anywhere: UNVERIFIED.
- WoR (and GH5/BH): "Located next to the rock meter there is a small bar. While singing the bar will fill will color. The color varies from white to yellow to green. Also the amount of points
  attained depends on the size of the phrase and how much the tunnel was filled." No text ratings. Same page.
- Spoken ("talkie") notes: WT red, same size as sung notes; Metallica era silver; GH5/BH larger in the middle of the highway; WoR at the bottom. Beginner = all spoken.
- Styles: WT-engine has Static and Scrolling; GH5/BH/WoR add Karaoke (sung lyrics turn blue).
- SP, WT-engine: solid/excellent phrase, star sequences, or "hype" sections (blue clapping hands; hypes also boost the rock meter). Activate by tapping mic top, blowing, or Square (FW:Star_Power, FW:Vocals).
- SP, WoR: "only two ways" - excellent on a (blue) star-power phrase, or SP overload in band play. A band moment on vocals needs an excellent rating. Same pages.
- Freeform: WT/Metallica freeform gives points and a multiplier that grows with better singing; SP multiplies it. GH5/WoR: freeform "no longer grant the player points ... only purpose ... boost the rock meter".
- Vocals multiplier: WT-engine ties the 4x multiplier to excellent ratings ("raise/maintain a 4x multiplier"). No fuller ladder found (unverified).

---------------------------------------------------------------------------------------------------------------------------------------

## 5. Instrument-failure display and instrument icons

The sources are thin here:
- WT: instrument icon shown inside the multiplier circle at x1 in band (https://guitarhero.fandom.com/wiki/Multiplier). A distinct failed/greyed icon for a zero-meter member: unverified;
  Wikipedia only says that player keeps playing while draining the band meter.
- FW:Band's gallery has an image captioned "A band member failing" (Metallica-era, WT engine) but no text describes it.
- WoR/GH5: a failed player triggers the band revival meter (FW:Band); red full-screen glow when a meter is red (FW:Rock_Meter). A large X over a highway marks a failed Band Moment
  (FW:Star_Power), not a failed player. A per-player failed icon on the highway in WoR: unverified.
- Instrument icons on WoR highways: unverified (WoR multiplier is a numbered circle with 10 bulbs on the right of the highway).
- Highway skins: WT has genre highways; GH5/BH/WoR use one black design each (WoR: a demon). Source: https://guitarhero.fandom.com/wiki/Highways

---------------------------------------------------------------------------------------------------------------------------------------

## 6. Battle mode in WT (completeness)

- Present in WT ("Existing competitive modes ... including the Battle Mode from Guitar Hero III, are also present"); full bands can compete online in Battle of the Bands
  (details unverified). Source: https://en.wikipedia.org/wiki/Guitar_Hero_World_Tour
- Power-ups replace SP: battle gem sequences replace SP phrases; up to 3 stored; triggered with the SP button / tilt; a new one replaces the latest if full (wiki text written for GH3,
  applies to later titles). WT-onward items: "Mines" (grey notes that sharply lower the rock meter and cost the latest power-up) and "Powerup Steal".
  Source: https://guitarhero.fandom.com/wiki/Battle_Mode
- Rock meter: yes (power-ups aim to make the opponent fail; Mines reduce it directly). FW:Rock_Meter's gallery lists a battle-mode rock meter for GHM; WT look unverified.
- Tie-break: WT onward uses "Do or Die!" (song repeats faster, some power-up effects doubled) instead of GH3's Sudden Death / Death Drain. Same Battle_Mode page.
- WoR has no Battle mode (only Wii Roadie Battle via Nintendo DS): https://guitarhero.fandom.com/wiki/New_gameplay_features

---------------------------------------------------------------------------------------------------------------------------------------

## 7. Notes for GHWT:DE
- GHWT:DE is a mod/rebuild of WT (https://guitarhero.fandom.com/wiki/Guitar_Hero_World_Tour:_Definitive_Edition). Its documented additions are content, gem themes (including WoR gems), practice speeds,
  mic selection and HOPO/tap chords (v1.3); the wiki does not describe it adding WoR mechanics (per-player SP, band moments, revival, RockFest). So the gameplay rules a WoR-looking HUD
  must serve are the WT column above.
- Resulting HUD rules: one shared SP meter; shared band rock meter + small individual meters; WT band multiplier (x2 -> x4, no band moments, no x11); no revival meter; no 1st-4th ladder;
  vocal feedback limited to the WT-engine scheme.

## 8. Items still unverified (check in game or with manuals/screenshots)
1. Whether a rock meter is drawn in WT Face-Off / Pro Face-Off and in WoR Pro Face-Off; the center needle meter in WoR.
2. The orange/purple "versus meter" claim for WoR (single garbled wiki sentence).
3. Exact vocal text strings in WT proper (wiki conflict); the strings "Awesome / Strong / OK".
4. Per-player failed-instrument icon (WT and WoR).
5. WT Battle of the Bands, the WT battle rock meter look, and the maximum WT band multiplier (only "x2 -> x4" stated).
6. Official WT / WoR manuals were not readable.

## 9. Sources
- https://guitarhero.fandom.com/wiki/Face-Off
- https://guitarhero.fandom.com/wiki/Pro_Face-Off
- https://guitarhero.fandom.com/wiki/RockFest
- https://guitarhero.fandom.com/wiki/Cooperative
- https://guitarhero.fandom.com/wiki/Band
- https://guitarhero.fandom.com/wiki/Star_Power
- https://guitarhero.fandom.com/wiki/Star_Power_Meter
- https://guitarhero.fandom.com/wiki/Multiplier
- https://guitarhero.fandom.com/wiki/Rock_Meter
- https://guitarhero.fandom.com/wiki/Vocals
- https://guitarhero.fandom.com/wiki/Battle_Mode
- https://guitarhero.fandom.com/wiki/Highways
- https://guitarhero.fandom.com/wiki/Tutorial
- https://guitarhero.fandom.com/wiki/New_gameplay_features
- https://guitarhero.fandom.com/wiki/Guitar_Hero_World_Tour
- https://guitarhero.fandom.com/wiki/Guitar_Hero:_Warriors_of_Rock
- https://guitarhero.fandom.com/wiki/Guitar_Hero:_Warriors_of_Rock/Quest
- https://guitarhero.fandom.com/wiki/Guitar_Hero_5
- https://guitarhero.fandom.com/wiki/Guitar_Hero_World_Tour:_Definitive_Edition
- https://en.wikipedia.org/wiki/Guitar_Hero_World_Tour
- https://en.wikipedia.org/wiki/Guitar_Hero:_Warriors_of_Rock
- https://en.wikipedia.org/wiki/Guitar_Hero_5
- https://gamingbolt.com/guitar-hero-warriors-of-rock-reviewed
- https://www.thesixthaxis.com/2009/08/05/guitar-hero-5-rockfest-revealed/
- https://gameinformer.com/b/news/archive/2010/06/16/guitar-hero-warriors-of-rock-hands-on (checked, no HUD info)
- Not readable: Scribd WT manual, manua.ls WoR Wii manual (cover only), GameFAQs WT boards (403).
