"""WoR menu look outside the HUD: helper pills and the song loading screen (v0.48).

Both go into one always-loaded pak (UI_PAK, loaded by WoR_HUD_Load with LoadPak like the DE's wtde_gig_posters), so
menu sprites see its images and fonts. It also carries WoR's pill text font (PILL_FONT); being loaded once and never
unloaded, it avoids the v0.19b crash (a font unloaded with a theme pak).

- Helper pills: a "ghwor" entry in the DE's pill theme table e8b85065 (choices list 0x12ec77b9): WoR's fret-cap
  button glyphs (cropped from WoR's buttons_x360 font texture), a dark grey translucent pill without outline and
  near-white text in WoR's fontgrid_text_a1 (user reference, 2026-10-10: WoR pause menu / song list pills).
- Loading screen: WoR's ingame_loading art (data/compressed/UI_IMAGES/LOADING, CHNK + deflate) with its load wheel
  (lightning strip) baked into the ring, as one full-screen sprite in our desc WoR_HUD_loading, registered through
  the DE's own loadtheme_add_struct (0x054f4a16). The DE still plays the theme's movie under the desc (z 200000 vs
  500000); it gets the smallest one.
"""
import math, os, struct, sys, zlib
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desc_gen, paths, wor_1g  # noqa: E402
from desc_gen import E  # noqa: E402
sys.path.insert(0, paths.GH_TOOLS)
import x360img  # noqa: E402

UI_PAK = 'wor_hud_ui'
THEME = 'ghwor'                                        # value checksum e18d65fe, same as the HUD theme
THEME_TITLE = 'Guitar Hero: Warriors of Rock'

# ---- helper pills
PILL_COLOURS = ('green', 'red', 'yellow', 'blue', 'orange')
PILL_IMAGE = {c: f'WoR_HUD_pill_{c}' for c in PILL_COLOURS}
# fret caps in WoR's buttons_x360 font texture (508x208)
PILL_CAP_BOX = {'green': (471, 111, 498, 157), 'red': (3, 160, 29, 206), 'yellow': (34, 160, 61, 206),
                'blue': (66, 160, 93, 206), 'orange': (98, 160, 125, 206)}
PILL_BG = (0, 0, 0, 110)             # WoR: black, see-through (user crops 2026-10-10; 150 was a bit strong)
PILL_TEXT = (255, 255, 255, 255)     # WoR: pure white
# WoR's own pill text font (fontgrid_text_a1, converted to the PC format), in the UI pak. This pak is loaded once and
# never unloaded, so the v0.19b crash (a font unloaded with a theme pak) can't happen.
PILL_FONT = 'WoR_HUD_text_a1'
PILL_FONT_SRC = paths.wor('ui_shared', 'fontgrid_text_a1.fnt.xen')
PILL_FONT_SCALE = 0.9                # its caps are 42-43 high; the DE pill font's cells 28 at 1.4
# helper_gamertag_pill: the icon sprite (helper_button, 62x62, Scale = <colour>_scale) sits centred in its container
# (helper_button_container, 62x62 + <colour>_dims, scale 1.4), and the text follows the CONTAINER in the pill's
# horizontal menu. v0.48 shrank only the container (the sprite stayed 62 wide, over the text) and drew a 32x64 cap
# squeezed into the square sprite (twice too wide). Now: square cap texture, sprite 0.9, container as wide as the
# cap's visible width plus a small gap (cap ~47% of the texture width).
PILL_SCALE = 0.9
PILL_DIMS_ADD = (-28.0, 0.0)


def pill_theme_struct():
    """The pill theme table entry (StructStruct body) for THEME."""
    L = [f'StructQBKey font = {PILL_FONT}', f'StructFloat font_scale = {PILL_FONT_SCALE:.6f}']
    for c in PILL_COLOURS:
        L.append(f'StructQBKey {c} = {PILL_IMAGE[c]}')
        L.append(f'StructFloatX2 {c}_dims\n{{\n\tFloats [{PILL_DIMS_ADD[0]:.5f}, {PILL_DIMS_ADD[1]:.5f}]\n}}')
        L.append(f'StructFloatX2 {c}_scale\n{{\n\tFloats [{PILL_SCALE:.5f}, {PILL_SCALE:.5f}]\n}}')
    for k, v in (('bg_color', PILL_BG), ('text_color', PILL_TEXT)):
        L.append(f'StructArray {k}\n{{\n\tArrayInteger\n\t[\n' + ''.join(f'\t\t{x}\n' for x in v) + '\t]\n}')
    body = '\n'.join(L)
    return 'SectionStruct WoR_HUD_pill_theme\n{\n\tStructHeader\n\t{\n' + '\n'.join('\t\t' + l for l in body.split('\n')) + '\n\t}\n}'


def font_texture(fnt):
    """The texture of a WoR (Xbox) .fnt.xen."""
    d = open(fnt, 'rb').read()
    off = struct.unpack_from('>I', d, 0x200a4)[0]
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'worui_font_tex.img.xen')
    open(tmp, 'wb').write(d[off:])
    return x360img.decode(tmp)[0].convert('RGBA')


def pill_images(out_dir):
    """Writes the five cap PNGs (named by image id); returns their paths."""
    tex = font_texture(paths.wor('ui_shared', 'buttons_x360.fnt.xen'))
    assert tex.size == (508, 208), tex.size
    out = []
    for c in PILL_COLOURS:
        cap = tex.crop(PILL_CAP_BOX[c])
        im = Image.new('RGBA', (64, 64), (0, 0, 0, 0))              # square like the sprite, cap centred
        cap = cap.resize((round(cap.size[0] * 54 / cap.size[1]), 54), Image.LANCZOS)
        im.alpha_composite(cap, ((64 - cap.size[0]) // 2, 5))
        p = os.path.join(out_dir, PILL_IMAGE[c] + '.png')
        im.save(p)
        out.append(p)
    return out


# ---- loading screen
LOAD_TEX = 'WoR_HUD_loading'
LOAD_DESC = 'WoR_HUD_loading'                          # uidesc_WoR_HUD_loading
LOAD_MOVIE = 'loading_flipbook_ghm'                    # smallest DE loading movie (hidden under the desc)
LOAD_DIR = ('data', 'compressed', 'UI_IMAGES', 'LOADING')
# the ring's hole in the 1024x512 art (centre = centroid of its dark pixels, radius): WoR spins load_wheel at
# (1015,192) of 1280x720. v0.48 test: (815, 140.5) put the ball a few pixels right.
RING = (811.9, 139.1, 50.0)
# the LOADING plate (frame included) in the art: its own sprite (WoR animates the red with a slow moving mottle), so
# on ultrawide it can sit whole at the bottom while the picture is anchored for the ring (both can't fit at WoR's
# 16:9 shape); the picture has the plate painted out
PLATE_BOX = (682, 399, 938, 463)
PLATE_TEX = 'WoR_HUD_load_plate_'                              # + frame number 0..PLATE_FRAMES-1
PLATE_FRAMES = 64                                              # 4 px of mottle apart, with the wheel's frame counter
PLATE_ALIAS = 'WoR_HUD_plate_alias'
PLATE_POS = (PLATE_BOX[0] * 1280 / 1024, PLATE_BOX[1] * 720 / 512)
PLATE_DIMS = ((PLATE_BOX[2] - PLATE_BOX[0]) * 1280 / 1024, (PLATE_BOX[3] - PLATE_BOX[1]) * 720 / 512)
# the load wheel (user video 2026-10-10): a ball in the ring's hole (0.83 of it, a dark gap around), brown, lit from
# above, with WoR's load_wheel strip (256x128: lightning across a brown background) wrapped round it and turning, so the
# thick lightning flows sideways and bulges with the ball. Pre-rendered frames (sphere projection of a WHEEL_WIN window
# of the strip), switched every game frame by WoR_HUD_loading_anim while our desc is up (found through its alias).
# 64 frames, 4 px of strip apart: ~3 ball widths a second at 60 fps, as in the video.
WHEEL_TEX = 'WoR_HUD_load_wheel_'                              # + frame number 0..WHEEL_FRAMES-1
WHEEL_FRAMES = 64
WHEEL_WIN = (128.0, 100.0)                                     # strip px across / down the ball's visible face
WHEEL_BALL = (82, 44, 28)                                      # the ball's brown (video: mean 118,78,39 with lightning)
WHEEL_ALIAS = 'WoR_HUD_wheel_alias'
WHEEL_POS = (RING[0] * 1280 / 1024, RING[1] * 720 / 512)       # canvas units
WHEEL_DIMS = (0.83 * 2 * RING[2] * 1280 / 1024, 0.83 * 2 * RING[2] * 720 / 512)   # 0.83 of the hole as shown


def wor_xbox_img(*parts):
    """A WoR data/compressed image: CHNK header (0x80) + raw deflate, or a plain Xbox img."""
    raw = open(os.path.join(paths.WOR_XBOX, *parts), 'rb').read()
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'worui_' + parts[-1])
    open(tmp, 'wb').write(zlib.decompressobj(-15).decompress(raw[0x80:]) if raw[:4] == b'CHNK' else raw)
    return x360img.decode(tmp)[0].convert('RGBA')


def loading_art():
    """WoR's ingame_loading with the LOADING plate painted out (the band just above it, feathered over 10 px); the
    hole is filled by the load wheel sprite, the plate is its own sprite (plate_frames)."""
    bg = wor_xbox_img(*LOAD_DIR, 'ingame_loading.img.xen')
    assert bg.size == (1024, 512), bg.size
    x0, y0, x1, y1 = PLATE_BOX
    h = y1 - y0
    patch = bg.crop((x0, y0 - h, x1, y0))
    mask = Image.new('L', patch.size, 255)
    mp = mask.load()
    f = 10
    for y in range(h):
        for x in range(x1 - x0):
            d = min(x, x1 - x0 - 1 - x, y, h - 1 - y)
            mp[x, y] = min(255, round(255 * d / f)) if d < f else 255
    bg.paste(patch, (x0, y0), mask)
    return bg


def plate_frames():
    """PLATE_FRAMES frames of the LOADING plate (as in the art), its red area (not the letters or their glow) with a
    dark-red mottle drifting left: WoR's load_wheel strip background (the same grain) as the noise, tileable."""
    art = wor_xbox_img(*LOAD_DIR, 'ingame_loading.img.xen').convert('RGBA')
    plate = art.crop(PLATE_BOX)
    strip = wor_xbox_img(*LOAD_DIR, 'load_wheel.img.xen').convert('L')
    w, h = plate.size
    noise = strip.resize((256, 128)).load()                  # 256 px period (the strip tiles sideways)
    lo, hi = 255, 0
    for x in range(0, 256, 2):
        for y in range(0, 128, 2):
            lo, hi = min(lo, noise[x, y]), max(hi, noise[x, y])
    pp = plate.load()
    red = [[pp[x, y][0] > 120 and pp[x, y][1] < 70 and pp[x, y][2] < 60 for y in range(h)] for x in range(w)]
    # the plate's own shape (not the background around it): saturated (red, gold) or near-black (outline) pixels,
    # each row filled between its outermost ones, edge feathered 1 px
    shape = Image.new('L', (w, h), 0)
    sp_ = shape.load()
    for y in range(h):
        hits = []
        for x in range(w):
            r, g, b = pp[x, y][:3]
            mx, mn = max(r, g, b), min(r, g, b)
            if (mx > 0 and (mx - mn) / mx > 0.38 and mx > 90) or mx < 45:
                hits.append(x)
        if len(hits) > 4:
            for x in range(hits[0], hits[-1] + 1):
                sp_[x, y] = 255
    shape = shape.filter(ImageFilter.GaussianBlur(0.8))
    plate.putalpha(shape)
    pp = plate.load()
    frames = []
    for k in range(PLATE_FRAMES):
        out = plate.copy()
        op = out.load()
        off = k * 256 // PLATE_FRAMES
        for x in range(w):
            for y in range(h):
                if not red[x][y]:
                    continue
                n = (noise[(x * 2 + off) % 256, (y * 2) % 128] - lo) / max(1, hi - lo)
                r, g, b, a = op[x, y]
                k_ = 0.62 + 0.55 * n                               # darker and lighter flecks
                op[x, y] = (min(255, round(r * k_)), min(255, round(g * k_)), min(255, round(b * k_)), a)
        frames.append(out)
    return frames


def wheel_frames():
    """WHEEL_FRAMES 128x128 frames of the ball: a brown ball lit from above-front, mottled with the strip's own dark
    texture, and the strip's light (lightning, above its near-black background) added on top. Each pixel of the disc
    maps through a sphere to the strip (longitude -> strip x, latitude -> strip y around the lightning's middle row),
    the strip turned by k*256/WHEEL_FRAMES; round, soft 1.5 px edge."""
    strip = wor_xbox_img(*LOAD_DIR, 'load_wheel.img.xen').convert('RGB')
    assert strip.size == (256, 128), strip.size
    sp = strip.load()
    rows = [sum(sum(sp[x, y]) for x in range(256)) for y in range(128)]
    mid = max(range(128), key=lambda y: sum(rows[max(0, y - 6):y + 7]))      # the lightning band's middle row
    bgpx = sorted(sp[x, y] for x in range(0, 256, 4) for y in (4, 8, 120, 124))
    floor = bgpx[len(bgpx) // 2]                                              # its near-black background
    lum = lambda c: (c[0] + c[1] + c[2]) / 3
    fl = lum(floor)
    n, step = 128, 256 / WHEEL_FRAMES
    frames = []
    for k in range(WHEEL_FRAMES):
        out = Image.new('RGBA', (n, n), (0, 0, 0, 0))
        op = out.load()
        for py in range(n):
            for px in range(n):
                x, y = (px + 0.5) / (n / 2) - 1, (py + 0.5) / (n / 2) - 1
                r2 = x * x + y * y
                if r2 >= 1.0:
                    continue
                z = math.sqrt(1 - r2)
                lon = math.atan2(x, z) / (math.pi / 2)            # -1..1 across the face
                lat = math.asin(max(-1.0, min(1.0, y))) / (math.pi / 2)
                sx = (lon * WHEEL_WIN[0] / 2 + k * step) % 256
                sy = min(127.0, max(0.0, mid + lat * WHEEL_WIN[1] / 2))
                c = sp[int(sx), int(sy)]
                light = 0.45 + 0.55 * max(0.0, 0.35 * -y + 0.9 * z)  # from above-front
                mottle = 0.8 + 0.4 * min(1.0, lum(c) / max(1.0, 2 * fl))
                glow = [max(0, v - f) * w for v, f, w in zip(c, floor, (1.35, 1.1, 0.8))]   # redder glow
                rgb = tuple(min(255, round(b * light * mottle + g)) for b, g in zip(WHEEL_BALL, glow))
                a = round(255 * max(0.0, min(1.0, (1.0 - math.sqrt(r2)) * n / 2 / 1.5)))
                op[px, py] = rgb + (a,)
        frames.append(out)
    return frames

def loading_desc():
    root = E('WoR_HUD_loading_root', 'ContainerElement', dims=(1280, 720), just=(-1, -1), children=[
        E('WoR_HUD_loading_bg', 'SpriteElement', dims=(1280, 720), just=(-1, -1), texture=LOAD_TEX),
        E('WoR_HUD_loading_wheel', 'SpriteElement', pos=WHEEL_POS, dims=WHEEL_DIMS, just=(0, 0), z=1.0,
          texture=WHEEL_TEX + '0'),
        E('WoR_HUD_loading_plate', 'SpriteElement', pos=PLATE_POS, dims=PLATE_DIMS, just=(-1, -1), z=1.0,
          texture=PLATE_TEX + '0')])
    return desc_gen.desc(LOAD_DESC, root, aliases=[(WHEEL_ALIAS, 'WoR_HUD_loading_wheel'),
                                                   (PLATE_ALIAS, 'WoR_HUD_loading_plate')])


# Wrappers (plugin 1.25 kScriptSwaps moves each DE script to its *_orig placeholder and puts the wrapper in its place)
WAIT_FRAME = '$wait$${\n\t\tStructInt 1\n\t\tStructQBKey gameframe\n\t\tStructQBKey ignoreslomo\n\t}$'
SCRIPTS = (
    # create_loading_screen: after the DE's own, animate our wheel if our desc is the one up
    'Script WoR_HUD_create_loading_screen [\n'
    '\t:i $WoR_HUD_create_loading_screen_orig$ isNull\n'
    '\t:i if $ScreenElementExists$${StructQBKey id = loading_screen_container}$\n'
    f'\t\t:i if $loading_screen_container$.$desc_resolvealias$$name$ = ${WHEEL_ALIAS}$\n'
    '\t\t\t:i $KillSpawnedScript$$name$ = $WoR_HUD_loading_anim$\n'
    '\t\t\t:i $spawnscriptnow$$WoR_HUD_loading_anim$\n'
    '\t\t:i endif\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # next wheel frame every game frame until the loading screen goes ("continue" is NodeROQ's break)
    'Script WoR_HUD_loading_anim [\n'
    '\t:i $frame$ = %i(0)\n'
    '\t:i while\n'
    '\t\t:i if NOT $ScreenElementExists$${StructQBKey id = loading_screen_container}$\n'
    '\t\t\t:i continue\n'
    '\t\t:i endif\n'
    f'\t\t:i if NOT $loading_screen_container$.$desc_resolvealias$$name$ = ${WHEEL_ALIAS}$\n'
    '\t\t\t:i continue\n'
    '\t\t:i endif\n'
    '\t\t:i $frame$ = (%GLOBAL%$frame$ + %i(1))\n'
    f'\t\t:i if (%GLOBAL%$frame$ > %i({WHEEL_FRAMES - 1}))\n'
    '\t\t\t:i $frame$ = %i(0)\n'
    '\t\t:i endif\n'
    f'\t\t:i $FormatText$$checksumname$ = $wheel_tex$%s("{WHEEL_TEX}%f")$f$ = %GLOBAL%$frame$\n'
    '\t\t:i %GLOBAL%$resolved_id$.$se_setprops$$texture$ = %GLOBAL%$wheel_tex$\n'
    # the plate: same frame counter (its mottle drifts 2 plate px a frame)
    f'\t\t:i if $loading_screen_container$.$desc_resolvealias$$name$ = ${PLATE_ALIAS}$\n'
    f'\t\t\t:i $FormatText$$checksumname$ = $plate_tex$%s("{PLATE_TEX}%f")$f$ = %GLOBAL%$frame$\n'
    '\t\t\t:i %GLOBAL%$resolved_id$.$se_setprops$$texture$ = %GLOBAL%$plate_tex$\n'
    '\t\t:i endif\n'
    f'\t\t:i {WAIT_FRAME}\n'
    '\t:i loop_to\n'
    '\t:i endfunction\n]\n\n'
    # set_user_control_color: with the WoR pill theme, screens can't force their own pill colours (the song list
    # asks for grey pills with black text)
    'Script WoR_HUD_set_user_control_color [\n'
    '\t:i $[795f4c8c]$\n'
    f'\t:i if (%GLOBAL%$[7d211cbc]$ = ${THEME}$)\n'
    '\t\t:i $WoR_HUD_set_user_control_color_orig$\n'
    '\t:i else \n'
    '\t\t:i $WoR_HUD_set_user_control_color_orig$ isNull\n'
    '\t:i endif\n'
    '\t:i endfunction\n]\n\n'
    # placeholders: the plugin moves the DE scripts' data here
    'Script WoR_HUD_create_loading_screen_orig [\n'
    '\t:i $printf$%s("WoR_HUD: create_loading_screen placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n\n'
    'Script WoR_HUD_set_user_control_color_orig [\n'
    '\t:i $printf$%s("WoR_HUD: set_user_control_color placeholder ran, plugin swap missing")\n'
    '\t:i endfunction\n]\n')


def load_script():
    """WoR_HUD_Load lines: load the pak, register both themes, then re-read both settings from the ini (the DE
    read them before mods loaded, when "ghwor" wasn't a choice yet)."""
    return (f'\t:i $LoadPak$%s("pak/{UI_PAK}.pak")\n'
            '\t:i $WoR_HUD_pill$ = (~$WoR_HUD_pill_theme$)\n'
            f'\t:i $[325bc724]$$id$ = $[e8b85065]$$field$ = ${THEME}$$element$ = %GLOBAL%$WoR_HUD_pill$\n'
            f'\t:i $WoR_HUD_pill_choice$ = :s{{$Title$ = %s("{THEME_TITLE}")$value$ = ${THEME}$$value_string$ = %s("{THEME}"):s}}\n'
            '\t:i $[6f2c7249]$$id$ = $[12ec77b9]$$element$ = %GLOBAL%$WoR_HUD_pill_choice$\n'
            f'\t:i $[054f4a16]$$id$ = %s("{THEME}")$name$ = %s("{THEME_TITLE}")$movie$ = %s("{LOAD_MOVIE}")'
            f'$[072c72a6]$ = %s("{LOAD_DESC}")$[dd1eca4d]$ = %s("loading_online")$[0b0f8ce0]$ = %s("loading_online")\n'
            '\t:i $[67da6f76]$(~$[f26e4c1f]$->$[7d211cbc]$)\n'
            '\t:i $[67da6f76]$(~$[f26e4c1f]$->$load_screen$)\n'
            '\t:i $printf$%s("WoR_HUD: WoR helper pills and loading screen registered")\n')
