"""Offline test suite for the WoR HUD mod. Never launches the game.

  1. build      the mod source compiles, decompiles back, and keeps its contract (keys, load script, sections)
  2. safety     rules learned in game: no $change$ of natively cached tables, no redefinition of DE scripts,
                no theme 'pak' without a registered pak, correct mod file naming
  3. drift      every DE table the mod copies still matches the installed DE (so a DE update can't be silently
                reverted by the mod)
  4. decoder    x360img decodes reference textures to known pixel hashes

usage: python run_offline.py [-k name]      exit code 0 = all pass
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, '..', 'build', 'WoR_HUD'))
SRC = os.path.join(MOD, 'WoR_HUD.txt')
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import paths  # noqa: E402
TOOLS, SDK, GAME = paths.GH_TOOLS, paths.SDK, paths.GAME
GOLDEN = os.path.join(HERE, 'golden_textures.json')

sys.path.insert(0, TOOLS)
results = []


def test(fn):
    results.append(fn)
    return fn


def qbkey(s):
    out = subprocess.run(['node', '-e', f"console.log((require('./SDKCode/QBKey.js')({json.dumps(s)})>>>0).toString(16).padStart(8,'0'))"],
                         cwd=os.path.dirname(SDK), capture_output=True, text=True)
    return out.stdout.strip()


def sdk(*args, cwd):
    return subprocess.run(['node', SDK, *args], cwd=cwd, capture_output=True, text=True)


def flat(s):
    return re.sub(r'\s+', ' ', s)


_cache = {}


def decompiled_mod():
    """Compile the source in a temp dir and decompile the result (round trip)."""
    if 'mod' not in _cache:
        d = tempfile.mkdtemp(prefix='worhud_')
        shutil.copy(SRC, d)
        r = sdk('compile', 'WoR_HUD.txt', cwd=d)
        qb = os.path.join(d, 'WoR_HUD.qb.xen')
        assert os.path.exists(qb), 'compile failed: ' + r.stdout + r.stderr
        os.makedirs(os.path.join(d, 'rt'))
        shutil.copy(qb, os.path.join(d, 'rt'))
        sdk('decompile', 'WoR_HUD.qb.xen', cwd=os.path.join(d, 'rt'))
        _cache['mod'] = (open(qb, 'rb').read(), open(os.path.join(d, 'rt', 'WoR_HUD.txt'), encoding='utf-8', errors='replace').read())
    return _cache['mod']


def de_scripts():
    """Extract the installed DE's script pack (tb) once and return the folder."""
    if 'tb' not in _cache:
        d = tempfile.mkdtemp(prefix='de_tb_')
        sdk('extract', os.path.join(GAME, 'DATA', 'PAK', 'tb.pak.xen'), d, cwd=os.path.dirname(SDK))
        _cache['tb'] = d
    return _cache['tb']


def de_decompiled(rel):
    d = de_scripts()
    src = os.path.join(d, rel)
    work = tempfile.mkdtemp(prefix='de_qb_')
    shutil.copy(src, work)
    sdk('decompile', os.path.basename(src), cwd=work)
    return open(os.path.join(work, os.path.basename(src)[:-len('.qb.xen')] + '.txt'), encoding='utf-8', errors='replace').read()


def section(text, header):
    """A whole 'SectionX name { ... }' block by brace matching."""
    i = text.index(header)
    j = text.index('{', i)
    depth = 0
    for k in range(j, len(text)):
        depth += {'{': 1, '}': -1}.get(text[k], 0)
        if depth == 0:
            return text[i:k + 1]
    raise ValueError(header)


def members(struct_text):
    """Top-level StructStruct members of a struct section: name -> flattened body."""
    out, i = {}, struct_text.index('StructHeader')
    for m in re.finditer(r'StructStruct (\S+)', struct_text):
        # only depth-2 members (directly under the section's StructHeader)
        before = struct_text[:m.start()]
        if before.count('{') - before.count('}') != 2:
            continue
        body = section(struct_text[m.start():], 'StructStruct ' + m.group(1))
        out[m.group(1)] = flat(body)
    return out


# ---------------------------------------------------------------- 1. build
@test
def build_round_trip():
    qb, txt = decompiled_mod()
    assert len(qb) > 1000, 'suspiciously small qb'
    assert 'WoR_HUD: registering Warriors of Rock HUD theme' in txt


@test
def build_keys():
    assert qbkey('ghwor') == 'e18d65fe', 'ghwor key changed: must equal the DE gem/song-intro WoR key'
    _, txt = decompiled_mod()
    load = qbkey('WoR_HUD_Load')
    assert f'Script {load}' in txt or f'Script 0x{load}' in txt, 'load script must be named <Folder>_Load'


@test
def build_menu_entry():
    _, txt = decompiled_mod()
    t = flat(txt)
    assert 'Title = "Guitar Hero: Warriors of Rock" StructQBKey value = e18d65fe StructString value_string = "ghwor"' in t


@test
def build_theme_member():
    _, txt = decompiled_mod()
    t = flat(txt)
    assert 'StructStruct e18d65fe' in t, 'theme table has no ghwor member'


# ---------------------------------------------------------------- 2. safety
CACHED_NATIVELY = {'cbcd0af1': 'HUD pak-links table (use-after-free, 2026-10-03)',
                   'af130dc4': 'gem pak-links table (same mechanism)'}


@test
def safety_no_change_of_native_tables():
    _, txt = decompiled_mod()
    for key, why in CACHED_NATIVELY.items():
        assert f'$change$$[{key}]$' not in txt, f'mod $change$s {key}: {why}'


@test
def safety_no_script_redefinitions():
    """The engine ignores scripts a mod redefines, and $change$ cannot swap them: every mod script must be a new
    WoR_HUD_* symbol (checked on the source, where names are readable)."""
    names = re.findall(r'^Script (\S+)', open(SRC, encoding='utf-8').read(), re.M)
    bad = [n for n in names if not n.startswith('WoR_HUD_')]
    assert not bad, f'mod defines non-namespaced scripts (DE names are ignored at runtime): {bad}'


@test
def safety_theme_pak_registered_the_de_way():
    """The theme's pak must be in the HUD pak-links table (else CRITICAL crash), added through the DE's own
    AddToGlobalStruct helper (0x325bc724), never by replacing the table directly."""
    _, txt = decompiled_mod()
    wor = members(section(txt, 'SectionStruct ' + re.search(r'SectionStruct (\S+)\s*\{\s*StructHeader\s*\{\s*StructStruct 0x09982fd5', txt).group(1)))['e18d65fe']
    m = re.search(r'StructString pak = "([^"]+)"', wor)
    if not m:
        return  # no pak: nothing to register
    pak = m.group(1)
    key = qbkey(pak)
    assert re.search(rf'\$\[325bc724\]\$\$id\$ = \$\[cbcd0af1\]\$\$field\$ = \$\[0*{key.lstrip("0")}\]\$', txt), \
        f'theme pak {pak} ({key}) is not added to the HUD links table with AddToGlobalStruct'
    assert os.path.exists(os.path.join(MOD, pak + '.pak.xen')), f'{pak}.pak.xen was not built'


@test
def safety_mod_folder_layout():
    installed = os.path.join(GAME, 'DATA', 'MODS', 'WoR_HUD')
    if not os.path.isdir(installed):
        return
    names = os.listdir(installed)
    assert 'Mod.ini' in names
    assert 'WoR_HUD.qb.xen' in names, 'the DE only loads <Folder>.qb.xen (not .qb)'
    assert not any(n.endswith('.qb') for n in names)


# ---------------------------------------------------------------- 2b. integrity (would show as a missing HUD in game)
def src_text():
    return open(SRC, encoding='utf-8').read()


@test
def integrity_textures_in_theme_pak():
    """Every mod texture a desc uses must be an entry of the built theme pak (entry id = checksum of the name)."""
    s = src_text()
    used = set(re.findall(r'texture = (WoR_HUD_\w+)', s))
    assert used, 'no mod textures used'
    pak = os.path.join(MOD, 'hud_ghwor.pak.xen')
    work = tempfile.mkdtemp(prefix='pak_')
    sdk('extract', pak, work, cwd=os.path.dirname(SDK))
    entries = {f.split('.')[0].lower().replace('0x', '').zfill(8) for f in os.listdir(work)}
    missing = [t for t in used if qbkey(t) not in entries]
    assert not missing, f'textures used but not in the theme pak: {missing}'
    assert 'IH_AddImage' not in s and 'IH_LoadImage' not in s, 'image-handler textures are invisible to HUD sprites'


@test
def integrity_no_null_textures():
    """A sprite with texture 0x00000000 is drawn as a white quad, not hidden (v0.5 in-game bug)."""
    s = src_text()
    nulls = re.findall(r'texture = (?:0x0+|0)\s', s)
    assert not nulls, f'{len(nulls)} sprites use a null texture; point them at WoR_HUD_blank instead'


@test
def integrity_descs_resolve():
    s = src_text()
    defined = set(re.findall(r'^SectionStruct uidesc_(\w+)', s, re.M))
    referenced = set(re.findall(r'desc_interface = "(\w+_ghwor)"', s)) | set(re.findall(r'desc = "(\w+_ghwor)"', s))
    assert referenced, 'no WoR descs referenced'
    assert referenced <= defined, f'referenced but undefined descs: {referenced - defined}'
    assert '_ghwtwithtime' not in s, 'leftover reference to the WT+ pak (not loaded when WoR is selected)'


@test
def integrity_theme_layouts_defined():
    s = src_text()
    wor = section(s, 'StructStruct ghwor')
    for cfg, layout in re.findall(r'StructQBKey (hud_\w+) = (WoR_HUD_layout_\w+)', wor):
        assert re.search(rf'^SectionStruct {layout}\s', s, re.M), f'{cfg} -> {layout} is not defined'
    assert len(re.findall(r'StructQBKey hud_\w+ = WoR_HUD_layout_', wor)) >= 6, 'theme does not map every player config'


@test
def integrity_restyled_desc_keeps_de_interface():
    """Restyled descs must keep the props table (names, paths, targets) and aliases the DE's scripts drive."""
    sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
    import desc_tree
    s = src_text()
    mod = section(s, 'SectionStruct uidesc_solo_play_rock_meter_ghwor')
    ref = open(paths.de('wtplus_qb', '0x4dcc2f5b.txt'), encoding='utf-8', errors='replace').read()
    assert desc_tree.props_interface(mod) == desc_tree.props_interface(ref), 'props table differs from the WT+ original'
    for local_id in re.findall(r'validatelocalid = (\S+)', ref):
        assert re.search(rf'StructQBKey local_id = {re.escape(local_id)}\s', mod), f'element {local_id} (used by a prop path) is gone'


def _desc_tree():
    sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
    import desc_tree
    return desc_tree


def mod_descs():
    """Every uidesc in the shipped binary (decompiled): section text list."""
    _, back = decompiled_mod()
    starts = [m.start() for m in re.finditer(r'(?m)^SectionStruct ', back)]
    out = []
    for n, i in enumerate(starts):
        d = back[i:starts[n + 1] if n + 1 < len(starts) else None]
        if 'StructInt descversion' in d[:400]:
            out.append(d)
    return out


def mod_desc(name):
    key = qbkey('uidesc_' + name).lstrip('0')
    for d in mod_descs():
        m = re.search(r'StructQBKey name = (?:0x)?0*([0-9a-f]+)\s', d)
        if m and m.group(1) == key:
            return d
    raise AssertionError(f'desc {name} not in the shipped binary')


def prop_names(d):
    return {n.lower() for n, _, _ in _desc_tree().props_interface(d)}


@test
def integrity_every_desc_path_resolves():
    """In the SHIPPED binary, every prop and alias path (root + sibling indexes) lands on the named element.
    A wrong index silently disconnects a meter in game."""
    dt = _desc_tree()
    descs = mod_descs()
    assert len(descs) >= 11, f'only {len(descs)} descs in the binary'
    bad = []
    for d in descs:
        bad += [(n, c) for n, ok, c in dt.resolve_paths(d) if not ok]
    assert not bad, f'unresolved paths: {bad[:5]}'


VH = paths.de('hud_vh_qb')
WTP = paths.de('wtplus_qb')


@test
def integrity_wor_1g_descs_cover_de_props():
    """The generated 1-player descs expose every prop the DE drives for their slot (reference: stock descs that
    fill the same slot: WT+/VH band meter, VH player multiplier, VH 1-guitar side meter)."""
    def ref(path):
        return prop_names(open(path, encoding='utf-8', errors='replace').read())
    checks = {
        'wor_band_meter_1g_ghwor': ref(os.path.join(WTP, '0x4dcc2f5b.txt')) | ref(os.path.join(VH, '0xedb241fe.txt')),
        'wor_mult_1g_ghwor': ref(os.path.join(VH, '0x54da8f3e.txt')),
        'wor_side_meter_ghwor': ref(os.path.join(VH, '0x5a1c3434.txt')),
    }
    for name, want in checks.items():
        missing = want - prop_names(mod_desc(name))
        assert not missing, f'{name} lacks DE props {sorted(missing)}'


@test
def integrity_wor_1g_layout_wiring():
    """The 1-guitar layout carries the children/aliases the DE looks up by name (guitar_hud.qb): player container
    alias, band meter alias, player_meter and BAND_side_meter under the player container."""
    dt = _desc_tree()
    d = mod_desc('hud_1g_ghwor')
    root = dt.tree(d)
    g1 = [k for k in root['kids'] if k['id'] == 'g1']
    assert g1, 'no g1 container'
    kids = {k['id'] for k in g1[0]['kids']}
    for need in ('player_meter', 'BAND_side_meter', 'hud_message_fire', 'message'):
        assert need in kids, f'g1 lacks {need}'
    names = {n for n, ok, _ in dt.resolve_paths(d)}
    for need in ('alias_g1', 'alias_band_meter', 'alias_hud_message_fire_p1', 'alias_g1_side_meter'):
        assert need in names, f'missing alias {need}'
    s = src_text()
    for desc_name in re.findall(r'StructString desc = "(\w+)"', section(s, 'SectionStruct uidesc_hud_1g_ghwor')):
        if desc_name.endswith('_ghwor'):
            assert re.search(rf'^SectionStruct uidesc_{desc_name}\s', s, re.M), f'{desc_name} not defined'


@test
def integrity_sp_tubes_wiring():
    """The DE's tube widget (CSETubesObserver, exe 0x478630) resolves each glowN_TEXTURE prop to its element and sets
    texture AND scale on that element, so glowN_texture and glowN_scale must name the same element (v0.6 bug)."""
    d = mod_desc('wor_band_meter_1g_ghwor')
    paths = {n.lower(): c for n, ok, c in _desc_tree().resolve_paths(d)}
    for i in range(6):
        assert paths[f'glow{i}_texture'] == paths[f'glow{i}_scale'], f'glow{i}: texture and scale on different elements'


@test
def integrity_player_container_descs_at_origin():
    """descinterfaces under the player container (g1) must sit at (0,0): an instance offset is applied twice in
    game (v0.6 badge/needle landed one g1 offset away)."""
    s = flat(section(src_text(), 'SectionStruct uidesc_hud_1g_ghwor'))
    for lid in ('player_meter', 'BAND_side_meter'):
        m = re.search(rf'StructQBKey local_id = {lid} .*?StructFloatX2 Pos \{{ Floats \[([^\]]*)\]', s)
        assert m and all(abs(float(v)) < 1e-6 for v in m.group(1).split(',')), f'{lid} Pos {m and m.group(1)}'


@test
def integrity_containers_anchor_top_left():
    """Children are positioned from their container's TOP-LEFT corner (pos - (just+1)/2*dims*scale; confirmed in
    game: v0.7 streak box and needle were off by half a 100x100 box). Generated containers that hold content
    must be anchored top-left so their Pos is the children's origin."""
    sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
    import desc_gen, wor_1g
    wor_1g.all_descs()
    bad = []

    def walk(e, where):
        if e.kind == 'ContainerElement' and e.children and tuple(e.just) != (-1, -1):
            bad.append(f'{where}/{e.local_id}')
        for c in e.children:
            walk(c, f'{where}/{e.local_id}')
    for name, root in desc_gen.ROOTS.items():
        walk(root, name)
    assert not bad, f'containers not anchored top-left: {bad}'


@test
def integrity_textures_power_of_two():
    """The texture converter pads non-power-of-two PNGs (160x144 -> 256x256 with the art top-left), which shrank
    and shifted the v0.12 multiplier badge in game. Every shipped texture must be power-of-two."""
    from PIL import Image
    import glob
    pngs = glob.glob(os.path.join(HERE, '..', 'build', 'preview', '*.png'))
    assert pngs, 'no build/preview textures (run build.py)'
    bad = []
    for f in pngs:
        w, h = Image.open(f).size
        if w & (w - 1) or h & (h - 1):
            bad.append(f'{os.path.basename(f)} {w}x{h}')
    assert not bad, f'non-power-of-two textures: {bad}'


@test
def integrity_theme_enables_wor_mechanics():
    """The WoR theme row switches on the DE's side meter and star meter and lists its multiplier images, and
    every listed image is in the theme pak."""
    s = src_text()
    wor = flat(section(s, 'StructStruct ghwor'))
    for flag in ('d38da2b2', 'd5045305'):
        assert f'StructInt {flag} = 1' in wor, f'flag {flag} not set'
    for key, n in (('f8885a0f', 4), ('d99b7552', 4)):
        m = re.search(rf'StructArray {key} \{{ ArrayQBKey \[ ([^\]]*)\]', wor)
        assert m and len(m.group(1).split()) == n, f'{key} must list {n} textures like the DE default'
        assert all(t.startswith('WoR_HUD_mult') for t in m.group(1).split())


# ---------------------------------------------------------------- 3. drift
@test
def drift_theme_table():
    de = members(section(de_decompiled('0x29ebe78e.qb.xen'), 'SectionStruct 0x8ef7f1be'))
    _, txt = decompiled_mod()
    mod_tbl = section(txt, 'SectionStruct ' + re.search(r'SectionStruct (\S+)\s*\{\s*StructHeader\s*\{\s*StructStruct 0x09982fd5', txt).group(1))
    mod = members(mod_tbl)
    extra = set(mod) - set(de)
    assert extra == {'e18d65fe'}, f'unexpected additions: {extra}'
    changed = [k for k in de if mod.get(k) != de[k]]
    assert not changed, f'DE theme members changed since the mod copied them (re-copy!): {changed}'


@test
def drift_menu_choices():
    de = flat(section(de_decompiled('0xbb76de6b.qb.xen'), 'SectionArray 0x1f644846'))
    _, txt = decompiled_mod()
    m = re.search(r'SectionArray (\S+)\s*\{\s*ArrayStruct\s*\[\s*StructHeader\s*\{\s*StructString Title = "Guitar Hero: World Tour \+"', txt)
    mod = flat(section(txt, 'SectionArray ' + m.group(1)))
    de_entries = re.findall(r'StructHeader \{ (.*?) \}', de)
    mod_entries = re.findall(r'StructHeader \{ (.*?) \}', mod)
    assert mod_entries[:len(de_entries)] == de_entries, 'DE HUD menu choices changed since the mod copied them'
    assert len(mod_entries) == len(de_entries) + 1


# ---------------------------------------------------------------- 4. decoder
@test
def decoder_golden():
    import x360img
    golden = json.load(open(GOLDEN))
    for rel, want in golden.items():
        img, kind, fb = x360img.decode(paths.wor(rel))
        got = hashlib.sha256(img.tobytes()).hexdigest()
        assert got == want, f'{rel}: decode changed'


def main():
    sel = sys.argv[sys.argv.index('-k') + 1] if '-k' in sys.argv else ''
    failed = 0
    for fn in results:
        if sel not in fn.__name__:
            continue
        try:
            fn()
            print(f'PASS  {fn.__name__}')
        except Exception as e:
            failed += 1
            print(f'FAIL  {fn.__name__}: {e}')
    print(f'{len([f for f in results if sel in f.__name__]) - failed} passed, {failed} failed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
