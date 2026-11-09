"""Mock: WoR's cyan halo on vocal notes of a star power phrase (item 11).

WoR reference (OneDrive\\Videos\\GH\\WOR_microphone_gameplay.mp4 at 53 s, 1280x720 = canvas units 1:1): a star power
phrase's notes keep their yellow outline and get a cyan band hugging the outline ABOVE and BELOW (not at the ends),
~8 units each way, brightest at the outline (~(0,190,185) at ~0.9) and fading to nothing; the box inside stays dark.
Sung notes fill yellow and keep the band.

usage: python tools/mock_sp_note_halo.py <our frame 2560x1080> <out.png> [x_from_px]
Our frames: canvas y = px / 1.5, so one WoR 720p pixel = 1.5 px here.
"""
import sys
from PIL import Image

HALO_RGB = (0, 190, 185)
HALO_A0 = 0.9            # at the outline
HALO_UNITS = 8.5         # canvas units to zero
PX = 1.5                 # frame px per canvas unit
BAND = (120, 270)        # vocal note rows in the frame (px)


def yellow(p):
    r, g, b = p[:3]
    return r > 170 and g > 160 and b < 140


def main(src, out, x_from=0):
    im = Image.open(src).convert('RGB')
    w, h = im.size
    ref = im.copy()
    px, rp = im.load(), ref.load()
    reach = int(round(HALO_UNITS * PX))
    for x in range(x_from, w):
        ys = [y for y in range(*BAND) if yellow(rp[x, y])]
        if not ys:
            continue
        # contiguous run(s) of the note in this column: take the outermost rows
        top, bot = ys[0], ys[-1]
        if bot - top > 40:          # the now-line ball / sparkle, not a note
            continue
        for d in range(1, reach + 1):
            a = HALO_A0 * (1 - (d - 1) / reach)
            for y in (top - d, bot + d):
                if 0 <= y < h and not yellow(rp[x, y]):
                    o = px[x, y]
                    px[x, y] = tuple(int(o[i] * (1 - a) + HALO_RGB[i] * a) for i in range(3))
    # side by side, vocal strip only, 1:1
    crop = (320, 60, 2240, 330)
    a, b = ref.crop(crop), im.crop(crop)
    sheet = Image.new('RGB', (a.width, a.height * 2 + 6), (255, 255, 255))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (0, a.height + 6))
    sheet.save(out)
    im.save(out.replace('.png', '_full.png'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
