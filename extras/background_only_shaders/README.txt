Background-only shaders (optional file for the GH5 / Warriors of Rock HUD)
=========================================================================
By WitchDoctoR

Makes ReShade apply its effects to the venue only (band, crowd, stage), never to the highway or the HUD, and
only during songs. Without it, ReShade blurs and tints the HUD along with everything else.

Requires ReShade 6.x with full add-on support, installed for GHWT_Definitive.exe (Direct3D 9).
Without ReShade these files do nothing.

Install: extract this archive into the game folder (the one with GHWT_Definitive.exe). It adds:
  ghwt_bgfx.addon32                       the add-on (ReShade loads it automatically)
  reshade-shaders\Shaders\GH5_Grade.fx    optional Guitar Hero 5 tone (tick it in the ReShade overlay;
                                          Toe 0.10 / Strength 1.0 match GH5)
Uninstall: delete those two files.
