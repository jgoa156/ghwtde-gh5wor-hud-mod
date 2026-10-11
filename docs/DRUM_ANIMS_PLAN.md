# Plan: WoR (and GH5) drum animations in GHWT:DE

Status: researched 2026-10-11, not started. Research files (scratch, may be gone):
`%TEMP%\claude\C--\04183b72-...\scratchpad\ghsdk_research` (skahdr.js, skecmp.js, skatrans.js, extractions, notes).

## Findings

- **Source (WoR, your Xbox copy):** `E:\Guitar Hero - Warriors of Rock\data\compressed\PAK\perm_anims.pak.xen`
  (CHNK + deflate; the local GHSDK `extract` handles it: 1020 `.ska.xen`, ~9.7 MB) and
  `data\pak\archive\anim_loops.pak.xen`; frontend drum-stick poses in the frontend_anims pak.
  495 drum-named SKAs:
  - 232 per-hit anims `Drum_<padA><padB>_{Q,M,S}Hit_{L,R}`: **not usable** (see below)
  - 128 pad poses `drum_c1c1`, `drum_c1c1_ik`, ...
  - 71 per-character `gh_drummer_*` default / difference poses
  - 22 DrumDroid, 6 `GH_FE_*_DrumStix`
  - 7 full-body tempo loops `drum_loop_{generic_100, highenergy_075/100/120, loenergy_075/100/120}` (21-53 s,
    40-80 custom keys each)
- **GH5:** no GH5 copy on disk yet (the DE's `DATA\MODS\Guitar Hero 5` is only a setlist). Same engine as WoR,
  unverified. Copy GH5's disc files to the PC first to include it.
- **Format:** WoR and DE SKAs share the header (version 0x68, 128 bones, big-endian). Differences:
  - WoR hit anims have flags 0x960b1200; flag bit 31 = translation keys with **float times** (640/1020 perm_anims
    files, all 226 hit anims); no DE anim (1100+ checked) uses it;
  - Xbox `DEADDEAD` padding (absent on PC);
  - PC translation frames are the same 16 bytes (time + xyz) plus a 12-byte block on the first frame
    (`Drum_Andy_C1C1_120`: 207 x 16 + 12 = 3324).
  - Quaternion encoding and flag bits 6/17/19/28 already appear in DE files.
- **Skeleton:** WoR `emptydefaultcharacter.ske` has the same 128 ordered bone hashes as all 278 DE 128-bone
  skeletons (only parent tables differ; 7 identical): per-bone data maps directly.
- **How the DE drums:** `drummer_info` -> `anim_set = drummer_animations`, start `Drum_Andy_StandardLP_NoTempo`;
  fallback `l_drum_loops_standard_anims_set`: stances (hs, ss, c2s, rs, t1s, t3s, notempo) x idle / good / normal /
  bad x slow / med / fast (075 / 100 / 120). Sets, `drumanimpatterns.qb`, `drumanimtransitions.qb` in qb.pak; tempo
  events `animevents_tempomatching.qb` (848 KB); loop paks registered by `Anim_Loop_DRUM_Pakman_Links`
  (guitar_character_paks). Decompiled DE scripts: `E:\Dev\ghwt\ghwt-extract` (CR line endings).
- **Why WoR's per-hit drumming is not a drop-in:** WoR's tempo-matching table is 60 bytes and it has no
  drumanimpatterns: hits are driven per note by engine logic, no stance loops. The DE has no hit-style anims; it would
  need new playback scripting with unknown engine support. Not recommended.
- **Tools:** our GHSDK (`E:\Dev\ghwt\tools\guitar-hero-sdk`) is upstream HEAD (fretworks, df55ce7): extracts paks, no
  SKA handler. **NXTools** (Blender 4.0+, gitgud.io/fretworks/nxtools) imports GH SKA (incl. float times) and exports
  GHWT-style v104 SKA + imports SKE. Blender isn't installed here.

## Plan

1. **Converter (~1 day):** a node script (next to the GHSDK) that reads a WoR SKA, rewrites the translation time
   encoding to the DE's, clears flag bit 31, strips `DEADDEAD` padding, writes a PC `.ska.xen`.
2. **One-file test (1 game launch, ask first):** convert `drum_loop_loenergy_100` (or `gh_drummer_male_default`),
   put it in a throwaway mod pak under the name of a DE loop it replaces, play a song with a drummer.
   If it plays wrong or not at all: export the same file with NXTools (install Blender) and compare.
3. **Loop set (2-3 days):** a new pak `L_DRUM_Loops_WoR_anims`, an anim-set struct mapping WoR's 7 loops onto the
   DE's slow / med / fast x energy slots, a `Anim_Loop_DRUM_Pakman_Links` entry, tempo-matching events for the long
   loops; optionally the 71 per-character poses and the frontend drum-stick poses.
4. **GH5:** once its files are on disk, same pipeline.

## Risks

- The engine may reject or mis-play converted files (only an in-game test shows it).
- The long loops need tempo-matching event entries.
- The QB side touches core qb.pak / tb content that other mods also edit: keep it in our own mod, swapping symbols
  through the plugin if needed (as the HUD scripts do).
