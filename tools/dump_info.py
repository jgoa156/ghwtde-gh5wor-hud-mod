"""Exception summary of Windows minidumps (code, address as module+offset, access parameters, call-stack guess).

usage: python tools/dump_info.py <file.dmp>..."""
import struct, sys


def parse(fn):
    d = open(fn, 'rb').read()
    _, _, nstreams, rva = struct.unpack_from('<IIII', d, 0)
    streams = {}
    for i in range(nstreams):
        t, size, r = struct.unpack_from('<III', d, rva + 12 * i)
        streams[t] = (r, size)
    r, _ = streams[6]                                   # ExceptionStream
    tid = struct.unpack_from('<I', d, r)[0]
    code, flags, rec, addr, nparams = struct.unpack_from('<IIQQI', d, r + 8)
    params = struct.unpack_from('<4Q', d, r + 8 + 32)
    mods = []
    r, _ = streams[4]                                   # ModuleListStream
    n = struct.unpack_from('<I', d, r)[0]
    for i in range(n):
        o = r + 4 + 108 * i
        base, size = struct.unpack_from('<QI', d, o)
        name_rva = struct.unpack_from('<I', d, o + 20)[0]
        ln = struct.unpack_from('<I', d, name_rva)[0]
        mods.append((base, size, d[name_rva + 4:name_rva + 4 + ln].decode('utf-16le').split('\\')[-1]))

    def where(a):
        m = next((m for m in mods if m[0] <= a < m[0] + m[1]), None)
        return f'{m[2]}+{a - m[0]:#x}' if m else f'{a:#x}'

    print(fn)
    print(f'  exception {code:#010x} at {where(addr)}  params {[hex(p) for p in params[:nparams]]}')
    # thread context of the faulting thread -> esp, then scan the stack for return addresses into modules
    r, _ = streams[3]                                   # ThreadListStream
    n = struct.unpack_from('<I', d, r)[0]
    for i in range(n):
        o = r + 4 + 48 * i
        t = struct.unpack_from('<I', d, o)[0]
        if t != tid:
            continue
        stack_start, stack_size, stack_rva = struct.unpack_from('<QII', d, o + 24)
        ctx_size, ctx_rva = struct.unpack_from('<II', d, o + 40)
        eip, esp = struct.unpack_from('<I', d, ctx_rva + 0xb8)[0], struct.unpack_from('<I', d, ctx_rva + 0xc4)[0]
        print(f'  eip {where(eip)}  esp {esp:#x}')
        frames = []
        for k in range(0, min(stack_size, 0x2000), 4):
            v = struct.unpack_from('<I', d, stack_rva + k)[0]
            w = where(v)
            if '+' in w and (w.startswith('GHWT_Definitive') or w.startswith('GHWTDE') or w.startswith('wor_hud') or w.startswith('ReShade') or w.startswith('d3d9')):
                frames.append(w)
        print('  stack refs:', ', '.join(frames[:24]))


if __name__ == '__main__':
    for f in sys.argv[1:]:
        parse(f)
