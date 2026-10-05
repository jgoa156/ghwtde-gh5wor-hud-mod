"""Generates uidesc sections (NodeROQ source text) from a small element tree.

Prop and alias paths are computed from the tree (root by local_id, then each child by its sibling index), so a
restyle can move elements around freely: the DE only sees the props table names it drives.
"""

PROP_TYPES = {'text': 'string_wchar', 'rot_angle': 'float', 'Pos': 'pair', 'alpha': 'float', 'Scale': 'pair',
              'dims': 'pair', 'rgba': 'array_color', 'texture': 'checksum'}


def _f(v):
    return f'{float(v):.5f}'


class E:
    """One element. kind: SpriteElement, ContainerElement, TextBlockElement, windowelement or descinterface."""

    def __init__(self, local_id, kind, pos=(0, 0), dims=(100, 100), just=(0, 0), scale=(1, 1), rot=0.0, z=0.0,
                 alpha=1.0, rgba=(255, 255, 255, 255), hidden=False, children=(), anchor=(-1, -1), **extra):
        self.local_id, self.kind = local_id, kind
        self.pos, self.dims, self.just, self.scale = pos, dims, just, scale
        self.rot, self.z, self.alpha, self.rgba, self.hidden = rot, z, alpha, rgba, hidden
        self.children = list(children)
        self.anchor = anchor
        self.extra = extra

    def render(self, ind):
        t = '\t' * ind
        L = []
        if self.kind == 'SpriteElement':
            L.append(f'StructQBKey Blend = {self.extra.get("blend", "Blend")}')
            if self.extra.get('texture'):
                L.append(f'StructQBKey texture = {self.extra["texture"]}')
            L.append('StructQBKey material = 0x00000000')
        L += [f'StructQBKey local_id = {self.local_id}', f'StructQBKey type = {self.kind}',
              f'StructQBKey hiddenlocal = {"true" if self.hidden else "false"}',
              f'StructFloat alpha = {self.alpha:.2f}',
              f'StructFloatX2 dims\n{{\n\tFloats [{_f(self.dims[0])}, {_f(self.dims[1])}]\n}}',
              f'StructArray just\n{{\n\tArrayFloat\n\t[\n\t\t{_f(self.just[0])}\n\t\t{_f(self.just[1])}\n\t]\n}}',
              f'StructArray pos_anchor\n{{\n\tArrayFloat\n\t[\n\t\t{_f(self.anchor[0])}\n\t\t{_f(self.anchor[1])}\n\t]\n}}',
              f'StructFloatX2 Pos\n{{\n\tFloats [{_f(self.pos[0])}, {_f(self.pos[1])}]\n}}',
              f'StructFloat z_priority = {self.z:.4f}',
              f'StructFloatX2 Scale\n{{\n\tFloats [{_f(self.scale[0])}, {_f(self.scale[1])}]\n}}',
              f'StructFloat rot_angle = {self.rot:.2f}',
              'StructArray rgba\n{\n\tArrayInteger\n\t[\n' + '\n'.join(f'\t\t{int(c)}' for c in self.rgba) + '\n\t]\n}',
              'StructInt events_blocked = 0', 'StructQBKey preserve_local_orientation = false']
        if self.kind == 'TextBlockElement':
            ij = self.extra.get('internal_just', self.just)
            L += [f'StructQBStringQs text = {self.extra.get("text", "0x00000000")}',
                  f'StructQBKey font = {self.extra["font"]}', 'StructQBKey material = 0x00000000',
                  'StructQBKey single_line = true', 'StructQBKey fit_width = expand dims',
                  'StructQBKey fit_height = expand dims', 'StructQBKey scale_mode = proportional',
                  'StructQBKey text_case = Original',
                  f'StructArray internal_just\n{{\n\tArrayFloat\n\t[\n\t\t{_f(ij[0])}\n\t\t{_f(ij[1])}\n\t]\n}}',
                  'StructFloatX2 internal_scale\n{\n\tFloats [1.00000, 1.00000]\n}',
                  f'StructQBKey Blend = {self.extra.get("blend", "Blend")}', 'StructInt font_spacing = -1',
                  'StructQBKey override_color_tag_alpha = true', 'StructQBKey override_color_tag_rgba = false',
                  f'StructQBKey use_shadow = {"true" if self.extra.get("shadow", True) else "false"}',
                  'StructArray shadow_rgba\n{\n\tArrayInteger\n\t[\n\t\t0\n\t\t0\n\t\t0\n\t\t160\n\t]\n}',
                  'StructFloatX2 shadow_offs\n{\n\tFloats [2.00000, 2.00000]\n}', 'StructFloat line_spacing = 1.00']
        if self.kind == 'descinterface':
            L += [f'StructString desc = "{self.extra["desc"]}"',
                  f'StructQBKey autosizedims = {"true" if self.extra.get("autosize") else "false"}']
        props = '\n'.join(L).replace('\n', '\n\t\t')
        out = f'StructHeader\n{{\n\tStructStruct props\n\t{{\n\t\tStructHeader\n\t\t{{\n\t\t\t' \
              + props.replace('\n\t\t', '\n\t\t\t') + '\n\t\t}\n\t}'
        if self.children:
            kids = '\n'.join(c.render(0) for c in self.children)
            out += '\n\tStructArray children\n\t{\n\t\tArrayStruct\n\t\t[\n' + _indent(kids, 3) + '\n\t\t\n\t\t]\n\t}'
        return _indent(out + '\n}', ind)


def _indent(s, n):
    return '\n'.join(('\t' * n + l) if l else l for l in s.split('\n'))


def find_path(root, local_id):
    """[(local_id, index or None), ...] from root to the unique element named local_id."""
    hits = []

    def walk(e, path):
        if e.local_id == local_id:
            hits.append(path)
        for i, c in enumerate(e.children):
            walk(c, path + [(c.local_id, i)])
    walk(root, [(root.local_id, None)])
    if len(hits) != 1:
        raise ValueError(f'{local_id}: {len(hits)} elements')
    return hits[0]


def _path_text(path):
    rows = []
    for lid, idx in path:
        if idx is None:
            rows.append(f'StructHeader\n{{\n\tStructQBKey validatelocalid = {lid}\n}}')
        else:
            rows.append(f'StructHeader\n{{\n\tStructInt index = {idx}\n\tStructQBKey validatelocalid = {lid}\n'
                        f'\tStructQBKey includeparentowned = false\n}}')
    return 'StructArray path\n{\n\tArrayStruct\n\t[\n' + _indent('\n'.join(rows), 2) + '\n\t\n\t]\n}'


ROOTS = {}   # name -> root element of every desc generated (for previews and tests)


def desc(name, root, props=(), aliases=(), rect=(0, 0, 1280, 720)):
    """props: [(prop_name, local_id, target)]; aliases: [(alias_name, local_id)]."""
    ROOTS[name] = root
    def entries(items, is_prop):
        out = []
        for item in items:
            nm, lid = item[0], item[1]
            path = find_path(root, lid)
            body = _path_text(path) + f'\nStructQBKey name = {nm}\nStructString visiblename = "{nm}"\n' \
                f'StructString help = "{" -> ".join(p[0] for p in path)}"'
            if is_prop:
                body += f'\nStructQBKey target = {item[2]}\nStructQBKey type = {PROP_TYPES[item[2]]}'
            out.append('StructHeader\n{\n' + _indent(body, 1) + '\n}')
        if not out:
            return 'Floats [0.00000, 0.00000]'
        return 'ArrayStruct\n[\n' + _indent('\n'.join(out), 1) + '\n\n]'
    head = (f'StructInt descversion = 9\nStructQBKey name = uidesc_{name}\n'
            'StructArray rect\n{\n\tArrayFloat\n\t[\n' + '\n'.join(f'\t\t{_f(v)}' for v in rect) + '\n\t]\n}\n'
            'StructArray aliases\n{\n' + _indent(entries(aliases, False), 1) + '\n}\n'
            'StructArray props\n{\n' + _indent(entries(props, True), 1) + '\n}\n'
            'StructArray materials\n{\n\tFloats [0.00000, 0.00000]\n}\nStructInt formatversion = 2\n'
            'StructStruct elements\n{\n' + root.render(1) + '\n}')
    return f'SectionStruct uidesc_{name}\n{{\n\tStructHeader\n\t{{\n' + _indent(head, 2) + '\n\t}\n}'


def walk_ids(root):
    out = [root.local_id]
    for c in root.children:
        out += walk_ids(c)
    return out
