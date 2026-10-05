"""List a GH:WT .pak.xen (big-endian 32-byte entries) and the textures inside its .tex dictionaries.
usage: python pak_list.py <pak.xen> [--dump outdir]"""
import os, struct, sys


def entries(d):
    pos = 0
    while pos + 32 <= len(d):
        typ, off, size, a, full, short, unk, flags = struct.unpack('>8I', d[pos:pos + 32])
        if size == 0 and off == 0 and typ == 0:
            break
        yield dict(pos=pos, type=typ, start=pos + off, size=size, full=full, short=short, flags=flags)
        if typ in (0xb524565f, 0x2cb3ef3b) or off == 0:   # .last
            break
        pos += 32


def textures(blob):
    """DDS images in a .tex dictionary: (checksum, w, h, dds bytes)."""
    out = []
    i = 0
    while True:
        j = blob.find(b'DDS ', i)
        if j < 0:
            break
        h, w = struct.unpack('<II', blob[j + 12:j + 20])
        fourcc = blob[j + 84:j + 88]
        out.append((j, w, h, fourcc))
        i = j + 4
    return out


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for e in entries(d):
        blob = d[e['start']:e['start'] + e['size']]
        tx = textures(blob) if b'DDS ' in blob else []
        print('type %08x full %08x short %08x size %8d %s' % (e['type'], e['full'], e['short'], e['size'],
              ' '.join('%dx%d%s' % (w, h, f.decode('latin1')) for _, w, h, f in tx[:12]) + (' ...(%d)' % len(tx) if len(tx) > 12 else '')))


def tex_dict(blob):
    """Entries of a .tex dictionary (40-byte records starting 0a281300): checksum, w, h, dds offset, size."""
    import re
    out = []
    for m in re.finditer(rb'\x0a\x28\x13\x00', blob):
        p = m.start()
        chk, w, h = struct.unpack('>IHH', blob[p + 4:p + 12])
        off, size = struct.unpack('>II', blob[p + 28:p + 36])
        if blob[off:off + 4] == b'DDS ':
            out.append(dict(rec=p, checksum=chk, w=w, h=h, off=off, size=size))
    return out
