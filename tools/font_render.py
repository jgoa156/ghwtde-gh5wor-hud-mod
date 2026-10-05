"""Renders text with a PC (DE) .fnt.xen exactly as laid out in the file: charmap -> glyph -> UV crop of the
font's own texture. Used to check converted WoR fonts offline and by the preview.

usage: python font_render.py <font.fnt.xen> <text> <out.png>
"""
import io, struct, subprocess, sys, os, tempfile
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402
TOOLS = paths.GH_TOOLS


def load(path):
    b = open(path, 'rb').read()
    tex_off = struct.unpack_from('>I', b, 0x200a4)[0]
    glyphs = []
    off = 0x200a8
    while off + 36 <= tex_off:
        g = struct.unpack_from('>4f2f3f', b, off)
        if not all(0.0 <= v <= 1.0 for v in g[:4]):
            break
        glyphs.append(g)
        off += 36
    dds = b[tex_off + 40:]
    tex = Image.open(io.BytesIO(dds)).convert('RGBA')
    return b, glyphs, tex


def glyph_index(b, ch):
    return struct.unpack_from('>H', b, 0x18 + 2 * ord(ch))[0]


def render(path, text, bg=(40, 40, 40, 255)):
    b, glyphs, tex = load(path)
    tw, th = tex.size
    parts, x, hmax = [], 0, 0
    for ch in text:
        g = glyphs[glyph_index(b, ch)]
        u0, v0, u1, v1, w, h = g[:6]
        crop = tex.crop((round(u0 * tw), round(v0 * th), round(u1 * tw), round(v1 * th)))
        parts.append((x, crop))
        x += max(int(w), crop.size[0])
        hmax = max(hmax, crop.size[1])
    out = Image.new('RGBA', (max(x, 1), max(hmax, 1)), bg)
    for px, c in parts:
        out.alpha_composite(c, (px, 0))
    return out


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2]).save(sys.argv[3])
