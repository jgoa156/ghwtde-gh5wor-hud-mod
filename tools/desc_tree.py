"""Flattens a decompiled uidesc (NodeROQ text) into readable rows: element tree, props interface, aliases.

usage: python desc_tree.py <desc.txt> [--props]
"""
import re, sys


def tokens_block(s, i):
    """Return (block_text, end_index) for the {...} or [...] starting at or after i."""
    j = min(x for x in (s.find('{', i), s.find('[', i)) if x >= 0)
    open_c = s[j]; close_c = '}' if open_c == '{' else ']'
    depth = 0
    for k in range(j, len(s)):
        if s[k] in '{[':
            depth += 1
        elif s[k] in '}]':
            depth -= 1
            if depth == 0:
                return s[j:k + 1], k + 1
    raise ValueError('unbalanced')


def field(props, name):
    m = re.search(rf'Struct\w* {name}\b(?: = (\S+))?', props)
    if not m:
        return None
    if m.group(1):
        return m.group(1)
    blk, _ = tokens_block(props, m.end())
    nums = re.findall(r'-?\d+\.\d+|-?\d+', blk)
    return ','.join(nums)


def walk(s, depth=0, out=None):
    """Walk 'StructStruct props {...} StructArray children [...]' pairs recursively."""
    out = [] if out is None else out
    i = 0
    while True:
        m = re.search(r'StructStruct props', s[i:])
        if not m:
            break
        p0 = i + m.start()
        props, p1 = tokens_block(s, p0)
        row = {k: field(props, k) for k in ['local_id', 'type', 'texture', 'Pos', 'dims', 'just', 'pos_anchor', 'Scale',
                                             'rot_angle', 'rgba', 'alpha', 'font', 'text', 'z_priority', 'Blend']}
        row['depth'] = depth
        out.append(row)
        c = re.match(r'\s*StructArray children', s[p1:])
        if c:
            kids, p2 = tokens_block(s, p1 + c.end())
            walk(kids[1:-1], depth + 1, out)
            i = p2
        else:
            i = p1
    return out


def props_interface(s):
    """The desc's top-level 'props' array: name -> (path, target)."""
    m = re.search(r'StructArray props\s*\{\s*ArrayStruct', s)
    if not m:
        return []
    blk, _ = tokens_block(s, m.start())
    out = []
    for h in re.finditer(r'StructQBKey name = (\S+).*?StructQBKey target = (\S+)', blk, re.S):
        path = re.findall(r'validatelocalid = (\S+)', blk[max(0, h.start() - 600):h.start()])
        out.append((h.group(1), h.group(2), '/'.join(path[-3:])))
    return out


if __name__ == '__main__':
    s = open(sys.argv[1], encoding='utf-8', errors='replace').read()
    name = re.search(r'StructQBKey name = (\S+)', s)
    rect = re.search(r'StructArray rect\s*\{\s*ArrayFloat\s*\[([^\]]*)\]', s)
    print('desc', name.group(1) if name else '?', '| rect', ' '.join(rect.group(1).split()) if rect else '')
    if '--props' in sys.argv:
        for n, t, p in props_interface(s):
            print(f'  prop {n:36s} -> {t:12s} via {p}')
    i = s.find('StructStruct elements')
    for r in walk(s[i:] if i >= 0 else s):
        ind = '  ' * r['depth']
        extra = ' '.join(f'{k}={v}' for k, v in r.items() if v not in (None, '') and k not in ('depth', 'local_id', 'type'))
        print(f"{ind}- {r['local_id']} [{r['type']}] {extra}")


def tree(s):
    """Nested element tree of a desc: {'id', 'kids'} (root = the element under 'StructStruct elements')."""
    def parse(seg):
        out = []
        i = 0
        while True:
            m = re.search(r'StructStruct props', seg[i:])
            if not m:
                return out
            p0 = i + m.start()
            props, p1 = tokens_block(seg, p0)
            node = {'id': field(props, 'local_id'), 'kids': []}
            c = re.match(r'\s*StructArray children', seg[p1:])
            if c:
                kids, p2 = tokens_block(seg, p1 + c.end())
                node['kids'] = parse(kids[1:-1])
                i = p2
            else:
                i = p1
            out.append(node)
    roots = parse(s[s.index('StructStruct elements'):])
    return roots[0]


def resolve_paths(s):
    """[(name, ok, chain)] for every alias and prop of a desc: does its index path land on the named elements?"""
    root = tree(s)
    out = []
    for h in re.finditer(r'StructArray path\s*\{(.*?)\]\s*\}\s*StructQBKey name = (\S+)', s, re.S):
        chain = re.findall(r'(?:StructInt index = (\d+)\s*)?StructQBKey validatelocalid = (\S+)', h.group(1))
        node, ok = root, chain[0][1] == root['id']
        for idx, lid in chain[1:]:
            k = int(idx)
            if not ok or k >= len(node['kids']) or node['kids'][k]['id'] != lid:
                ok = False
                break
            node = node['kids'][k]
        out.append((h.group(2), ok, '/'.join(c[1] for c in chain)))
    return out
