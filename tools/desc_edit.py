"""Edits one element of a uidesc (NodeROQ source text) by its local_id.

The DE's HUD scripts address elements through the desc's props table (name -> path/target), so elements can be
restyled freely as long as their local_ids, nesting and the props table stay intact.
"""
import re


def _block_bounds(s, i):
    """Bounds of the innermost '{ ... }' that contains index i."""
    depth, j = 0, i
    while j >= 0:
        if s[j] == '}':
            depth += 1
        elif s[j] == '{':
            if depth == 0:
                break
            depth -= 1
        j -= 1
    depth, k = 0, j
    for k in range(j, len(s)):
        depth += {'{': 1, '}': -1}.get(s[k], 0)
        if depth == 0:
            break
    return j, k + 1


def _floats2(name, x, y):
    return (rf'(StructFloatX2 {name}\s*\{{\s*Floats \[)[^\]]*(\])', rf'\g<1>{x:.5f}, {y:.5f}\g<2>')


def set_elem(desc, local_id, texture=None, pos=None, dims=None, scale=None, just=None, z=None, blend=None,
             alpha=None, rot=None, rgba=None):
    """Return desc with the element <local_id> changed. Raises if the element is missing or ambiguous."""
    hits = [m.start() for m in re.finditer(rf'StructQBKey local_id = {re.escape(local_id)}\s*\n', desc)]
    if len(hits) != 1:
        raise ValueError(f'local_id {local_id}: {len(hits)} matches')
    a, b = _block_bounds(desc, hits[0])
    blk = desc[a:b]

    def sub(pattern, repl, text, what):
        new, n = re.subn(pattern, repl, text, count=1)
        if n != 1:
            raise ValueError(f'{local_id}: no {what} field')
        return new

    if texture is not None:
        if re.search(r'StructQBKey texture = \S+', blk):
            blk = sub(r'StructQBKey texture = \S+', f'StructQBKey texture = {texture}', blk, 'texture')
        else:
            blk = blk.replace('{', '{\n\tStructQBKey texture = ' + texture, 1)
    if pos is not None:
        blk = sub(*_floats2('Pos', *pos), blk, 'Pos')
    if dims is not None:
        blk = sub(*_floats2('dims', *dims), blk, 'dims')
    if scale is not None:
        blk = sub(*_floats2('Scale', *scale), blk, 'Scale')
    if just is not None:
        blk = sub(r'(StructArray just\s*\{\s*ArrayFloat\s*\[)[^\]]*(\])',
                  rf'\g<1>\n{just[0]:.5f}\n{just[1]:.5f}\n\g<2>', blk, 'just')
    if z is not None:
        blk = sub(r'StructFloat z_priority = \S+', f'StructFloat z_priority = {z:.2f}', blk, 'z_priority')
    if blend is not None:
        blk = sub(r'StructQBKey Blend = \S+', f'StructQBKey Blend = {blend}', blk, 'Blend')
    if alpha is not None:
        blk = sub(r'StructFloat alpha = \S+', f'StructFloat alpha = {alpha:.2f}', blk, 'alpha')
    if rot is not None:
        blk = sub(r'StructFloat rot_angle = \S+', f'StructFloat rot_angle = {rot:.2f}', blk, 'rot_angle')
    if rgba is not None:
        blk = sub(r'(StructArray rgba\s*\{\s*ArrayInteger\s*\[)[^\]]*(\])',
                  r'\g<1>\n' + '\n'.join(str(int(c)) for c in rgba) + r'\n\g<2>', blk, 'rgba')
    return desc[:a] + blk + desc[b:]


def get_elem(desc, local_id):
    """The props block of an element (for tests and inspection)."""
    m = re.search(rf'StructQBKey local_id = {re.escape(local_id)}\s*\n', desc)
    a, b = _block_bounds(desc, m.start())
    return desc[a:b]
