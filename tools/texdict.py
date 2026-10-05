"""Read / rebuild a GH:WT PC .tex.xen dictionary (layout of GHSDK TexHandler.Compile). Used to add a texture to a
copy of an existing dictionary while keeping every original record and DDS byte-identical."""
import math, struct


def parse(d):
    assert struct.unpack('>I', d[:4])[0] == 0xFACECAA7, 'not a tex dict'
    count = struct.unpack('>H', d[6:8])[0]
    meta = struct.unpack('>I', d[8:12])[0]
    recs = []
    for i in range(count):
        r = d[meta + i * 40: meta + i * 40 + 40]
        chk, w, h = struct.unpack('>IHH', r[4:12])
        off, size = struct.unpack('>II', r[28:36])
        recs.append(dict(raw=bytearray(r), checksum=chk, w=w, h=h, dds=d[off:off + size]))
    return recs


def record(checksum, dds):
    h, w = struct.unpack('<II', dds[12:20])
    mips = struct.unpack('<I', dds[28:32])[0] or 1
    r = bytearray(40)
    r[0:4] = b'\x0a\x28\x13\x00'
    struct.pack_into('>IHHHHHH', r, 4, checksum, w, h, 1, w, h, 1)
    r[20] = mips; r[21] = 8; r[22] = 5
    return dict(raw=r, checksum=checksum, w=w, h=h, dds=dds)


def padding(n):
    k = 2
    while n / math.pow(2.0, k - 2) > 1.0:
        k += 1
    k -= 1
    return k, int(math.pow(2.0, k) * 12.0 + 28.0)


def build(recs):
    n = len(recs)
    k, pad = padding(n)
    head = bytearray()
    head += struct.pack('>IHH', 0xFACECAA7, 0x011C, n)
    meta_ptr = len(head); head += b'\0' * 8
    head += struct.pack('>III', 0xFFFFFFFF, k, 28)
    head += b'\xef' * pad
    meta = len(head)
    struct.pack_into('>II', head, meta_ptr, meta, meta + n * 44)
    out = head + b'\0' * (n * 40)
    for i, r in enumerate(recs):
        off = len(out)
        raw = bytearray(r['raw'])
        struct.pack_into('>II', raw, 28, off, len(r['dds']))
        out[meta + i * 40: meta + i * 40 + 40] = raw
        out += r['dds']
    return bytes(out)
