"""Imports element subtrees from Warriors of Rock's own uidescs (decompiled, ghwor-extract/uidesc) as desc_gen
elements, so the WoR HUD is built from WoR's real layout data instead of hand-measured coordinates.

A WoR descinterface instance (autosizedims) is a box of the desc's rect size whose children sit at
(editor pos - rect origin). `instance()` reproduces that box as a ContainerElement, so the engine composes the
transforms (anchors, scales, rotations, mirroring) exactly like WoR does.
"""
import os, re
import desc_tree
from desc_gen import E

UIDESC = r'C:\Users\rockb\ghwor-extract\uidesc'
NAMED_RGBA = {'NTSCWhite': (235, 235, 235, 255), 'white': (255, 255, 255, 255), 'black': (0, 0, 0, 255)}


def _pair(v, default=(0.0, 0.0)):
    if not v:
        return default
    a = [float(x) for x in v.split(',')]
    return (a[0], a[1])


def _rgba(v):
    if not v:
        return (255, 255, 255, 255)
    if v in NAMED_RGBA:
        return NAMED_RGBA[v]
    if re.fullmatch(r'[\d,]+', v):
        return tuple(int(x) for x in v.split(','))
    return (255, 255, 255, 255)        # other named colours (green_md...) only appear on elements we restyle


class Desc:
    def __init__(self, name):
        self.text = open(os.path.join(UIDESC, f'uidesc_{name}.txt'), encoding='utf-8', errors='replace').read()
        r = re.search(r'StructArray rect\s*\{\s*ArrayFloat\s*\[([^\]]*)\]', self.text)
        self.rect = tuple(float(x) for x in r.group(1).split())
        rows = desc_tree.walk(self.text[self.text.find('StructStruct elements'):])
        self.root = self._build(rows)

    @staticmethod
    def _build(rows):
        stack, root = [], None
        for r in rows:
            kind = r['type']
            kw = {}
            if kind == 'SpriteElement':
                tex = r['texture']
                kw['texture'] = None if tex in (None, '0x00000000') else tex
                kw['blend'] = r['Blend'] or 'Blend'
            if kind == 'TextBlockElement':
                kw['font'] = r['font']
                kw['text'] = r['text'] or '0x00000000'
                kw['blend'] = r['Blend'] or 'Blend'
            e = E(r['local_id'], kind, pos=_pair(r['Pos']), dims=_pair(r['dims'], (100.0, 100.0)),
                  just=_pair(r['just']), scale=_pair(r['Scale'], (1.0, 1.0)), rot=float(r['rot_angle'] or 0),
                  z=float(r['z_priority'] or 0), alpha=float(r['alpha'] or 1), rgba=_rgba(r['rgba']),
                  anchor=_pair(r['pos_anchor'], (-1.0, -1.0)), **kw)
            e.wor_kind = kind
            while stack and stack[-1][0] >= r['depth']:
                stack.pop()
            if stack:
                stack[-1][1].children.append(e)
            else:
                root = e
            stack.append((r['depth'], e))
        return root

    def find(self, local_id, node=None):
        node = node or self.root
        if node.local_id == local_id:
            return node
        for c in node.children:
            f = self.find(local_id, c)
            if f:
                return f
        return None

    def instance(self, local_id, pos, just, scale, anchor=(-1.0, -1.0), z=0.0, rot=0.0, keep=None):
        """A ContainerElement standing in for a descinterface instance of this desc, holding its root element
        (positions relative to the rect origin). keep: optional predicate(element) -> bool pruning children."""
        rx, ry, rw, rh = self.rect
        root = self.root
        root.pos = (root.pos[0] - rx, root.pos[1] - ry)
        if keep:
            prune(root, keep)
        return E(local_id, 'ContainerElement', pos=pos, dims=(rw, rh), just=just, scale=scale, anchor=anchor,
                 z=z, rot=rot, children=[root])


def prune(node, keep):
    node.children = [c for c in node.children if keep(c)]
    for c in node.children:
        prune(c, keep)


def walk(node):
    yield node
    for c in node.children:
        yield from walk(c)


def textures(node):
    return sorted({e.extra.get('texture') for e in walk(node) if e.kind == 'SpriteElement' and e.extra.get('texture')})
