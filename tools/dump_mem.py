"""Read process memory captured in a full minidump (Memory64ListStream).

usage: python tools/dump_mem.py <file.dmp> <hex address> <length> [--dis]"""
import struct, sys


class Dump:
    def __init__(self, fn):
        self.d = d = open(fn, 'rb').read()
        _, _, ns, rva = struct.unpack_from('<IIII', d, 0)
        self.st = {}
        for i in range(ns):
            t, s, r = struct.unpack_from('<III', d, rva + 12 * i)
            self.st[t] = (r, s)
        self.ranges = []
        if 5 in self.st:                                # MemoryListStream
            r, _ = self.st[5]
            n = struct.unpack_from('<I', d, r)[0]
            for i in range(n):
                start, size, loc = struct.unpack_from('<QII', d, r + 4 + 16 * i)
                self.ranges.append((start, size, loc))
        if 9 in self.st:
            r, _ = self.st[9]
            n, base_rva = struct.unpack_from('<QQ', d, r)
            off = base_rva
            for i in range(n):
                start, size = struct.unpack_from('<QQ', d, r + 16 + 16 * i)
                self.ranges.append((start, size, off))
                off += size

    def read(self, addr, n):
        for start, size, off in self.ranges:
            if start <= addr and addr + n <= start + size:
                return self.d[off + addr - start: off + addr - start + n]
        return None


if __name__ == '__main__':
    dm = Dump(sys.argv[1])
    a, n = int(sys.argv[2], 16), int(sys.argv[3])
    b = dm.read(a, n)
    if b is None:
        print('not captured')
        sys.exit(1)
    if '--dis' in sys.argv:
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        for i in md.disasm(b, a):
            print(f'{i.address:08x}  {i.mnemonic:6s} {i.op_str}')
    else:
        print(b.hex(' '))
