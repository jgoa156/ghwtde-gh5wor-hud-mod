"""Fingerprint the build output (sha256 per file) to prove a refactor didn't change what ships.

usage: python tools/build_hashes.py save <file.json>   |   python tools/build_hashes.py check <file.json>"""
import hashlib, json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SKIP = ('preview', 'pak_src')   # mock textures and intermediate pak inputs


def hashes():
    out = {}
    base = os.path.join(ROOT, 'build')
    for root, _, files in os.walk(base):
        if any(s in os.path.relpath(root, base).split(os.sep) for s in SKIP):
            continue
        for f in files:
            p = os.path.join(root, f)
            out[os.path.relpath(p, base).replace(os.sep, '/')] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return out


if __name__ == '__main__':
    mode, path = sys.argv[1], sys.argv[2]
    now = hashes()
    if mode == 'save':
        json.dump(now, open(path, 'w'), indent=1, sort_keys=True)
        print('saved', len(now), 'files')
    else:
        old = json.load(open(path))
        diff = sorted(k for k in set(old) | set(now) if old.get(k) != now.get(k))
        for k in diff:
            print('DIFF', k, 'missing' if k not in now else ('new' if k not in old else 'changed'))
        print('identical' if not diff else f'{len(diff)} files differ', f'({len(now)} files)')
        sys.exit(1 if diff else 0)
