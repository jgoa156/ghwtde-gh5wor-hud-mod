"""Converts a Warriors of Rock Xbox 360 font (.fnt.xen) to the PC GHWT:DE font format.

Both games share the font layout: header (0x18 bytes), a 65536-entry u16 character map, a 0x0001dead marker,
the glyph table (9 big-endian words per glyph: u0 v0 u1 v1 w h + 3 offsets, UVs normalised), and a texture whose
offset is the u32 at 0x200a4. Only the texture differs: WoR embeds an Xbox img (tiled), the DE a PC img
(40-byte header + DDS). We decode the Xbox texture (x360img), pad it to a power of two (png2img pads anyway, art
top-left), rescale the UVs to the padded size, re-encode with png2img and splice it back in.

usage: python wor_font.py <src.fnt.xen> <out.fnt.xen>
"""
import os, struct, subprocess, sys, tempfile
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
TOOLS = paths.GH_TOOLS
sys.path.insert(0, TOOLS)
import x360img  # noqa: E402

TEX_PTR = 0x200a4
GLYPH_COUNT_GUESS_AT = 0x200a8


def pot(n):
    p = 1
    while p < n:
        p *= 2
    return p


def convert(src, out):
    b = bytearray(open(src, 'rb').read())
    tex_off = struct.unpack_from('>I', b, TEX_PTR)[0]
    work = tempfile.mkdtemp(prefix='worfont_')
    blob = os.path.join(work, 'font_tex.img.xen')
    open(blob, 'wb').write(b[tex_off:])
    img = x360img.decode(blob)[0]           # (PIL image, kind, format byte)
    w, h = img.size
    pw, ph = pot(w), pot(h)
    padded = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    padded.alpha_composite(img.convert('RGBA'), (0, 0))
    png = os.path.join(work, 'font_tex.png')
    padded.save(png)
    subprocess.run(['node', os.path.join(TOOLS, 'png2img.js'), work, png], cwd=TOOLS, check=True,
                   capture_output=True)
    pc_tex = open(os.path.join(work, 'font_tex.img.xen'), 'rb').read()
    # glyph records: from 0x200a8 up to the texture, 36 bytes each
    sx, sy = w / pw, h / ph
    off = 0x200a8
    while off + 36 <= tex_off:
        u0, v0, u1, v1 = struct.unpack_from('>4f', b, off)
        if not all(0.0 <= v <= 1.0 for v in (u0, v0, u1, v1)):
            break
        struct.pack_into('>4f', b, off, u0 * sx, v0 * sy, u1 * sx, v1 * sy)
        off += 36
    head = bytes(b[:tex_off])
    open(out, 'wb').write(head + pc_tex)
    return (w, h), (pw, ph), (off - 0x200a8) // 36


if __name__ == '__main__':
    print(convert(sys.argv[1], sys.argv[2]))
