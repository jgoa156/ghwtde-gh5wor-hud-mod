# Ultrawide ASI plugin: research notes (2026-10-08)

Goal (user): at a native ultrawide resolution (2560x1080) gameplay renders the 3D scene ultrawide (Hor+, not
stretched); the HUD + 2D highway and every non-gameplay screen (menus, loading, videos, results) render as centred
16:9 (1080p) content with borders. Today the whole frame is stretched horizontally.

All addresses: GHWT_Definitive.exe (image base 0x400000), the build this mod targets.

## 3D scene aspect

- Global float **0xd9ef74** = screen aspect used by the 3D side. Written only by the setter **0x5c7c20**
  (`movss [0xd9ef74], [esp+4]; ret`), called once at boot from 0x4fce6f with the only 16/9 float constant in the
  exe (.rdata 0xa24eec). The game never derives it from the window size, hence the stretch.
- Readers: 0x5546b0, 0x5c1538 / 0x5c1574 (compares it with a threshold at 0xa10b9c and rescales a FOV value:
  aspect-dependent FOV already exists), 0x6371b2, 0x7501cb, 0x75cb70.
- Plan: hook 0x5c7c20 (or patch the write) so the value is the real backbuffer width / height. Expected result:
  Hor+ 3D (wider view, nothing stretched). Needs an in-game check of the venue camera and the 3D highway gems
  (gems are drawn in the 2D canvas, see below, so they should be unaffected).

## 2D canvas (HUD, highway, menus)

- Screen size floats **0xb056a4 / 0xb056a8** (setter 0x52a510, getters 0x52a550 / 0x52a560). Set at 0x503973 from
  the integer backbuffer size at **0xe51440 / 0xe51444**, and at 0x40e9c5 from a settings struct (+0x44 / +0x48).
- UI scale floats **0xb056ac / 0xb056b0** (setter 0x52a530, called at 0x7506c2 from a struct at [edi+0x6c/+0x70]):
  canvas units -> screen pixels. Helpers: 0x52a670 (x * sx), 0x52a690 (y * sy), 0x52a6b0 (x / sx), 0x52a6d0 (y / sy).
  On 2560x1080 these are 2.0 / 1.5: the 1280x720 canvas is stretched.
- Plan for a centred 16:9 canvas: make sx = sy (= height / 720) and add a horizontal offset of
  (width - 1280 * sy) / 2 where canvas POSITIONS become screen pixels (the scale helpers are also used for sizes, so
  the offset can't go into 0x52a670 itself). Next step: find the 2D sprite/text submission that turns element
  positions into screen coordinates (callers of 0x52a670 / 0x52a690; the element draw path near 0x5a2xxx), or apply
  the offset at the D3D level (the 2D pass uses DrawPrimitiveUP with pre-transformed vertices, so a viewport change
  alone won't move them; a vertex x offset in a DrawPrimitiveUP hook for the 2D pass would).
- Menus / loading / videos: same canvas, so the same centring gives the 16:9 borders. Movie playback (Bink) may draw
  outside it; check separately.
- Gameplay vs menus: the user wants the 3D aspect fix in gameplay only; menus are 2D on top of a 3D background scene,
  so applying the 3D aspect everywhere is probably fine (menus' 3D backdrop just widens). To verify in game.

## Risks / checks

- Cursor / click mapping in menus (inverse helpers 0x52a6b0 / 0x52a6d0) must use the same centring.
- ReShade background-only add-on and shaders that use screen size.
- Our HUD layout is in canvas units, so it is unaffected by the centring (it just stops being stretched).
