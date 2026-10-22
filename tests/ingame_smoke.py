"""In-game smoke test for the WoR HUD theme, fully automated (no player needed).

Uses GHWT:DE's own AutoLaunch (boots straight into a bot-played song) and the ghwt_bgfx ReShade add-on's frame
dump (trigger file), then checks the DE log and the dumped frame. GHWTDE.ini is backed up and always restored.

usage: python ingame_smoke.py [--hud ghwor] [--song aboutagirl] [--wait 45] [--debug-mpm]
exit code: 0 all checks passed, 1 a check failed, 2 the harness itself failed
"""
import argparse, csv, glob, json, os, re, shutil, subprocess, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tools'))
import paths  # noqa: E402
GAME = paths.GAME
EXE = os.path.join(GAME, 'GHWT_Definitive.exe')
CFG_DIR = paths.GAME_CONFIG
INI = os.path.join(CFG_DIR, 'GHWTDE.ini')
LOG = os.path.join(CFG_DIR, 'Logs', 'debug.txt')
DUMPS = os.path.join(GAME, 'ghwt_bgfx_dumps')
TRIGGER = os.path.join(GAME, 'ghwt_bgfx_dump.trigger')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

# Expected values for the WoR theme (see WoR_HUD.txt): its pak and its 1-guitar layout name.
EXPECT = {'ghwor': {'pak': None, 'layout_1g': '0xdb93bd6b'},   # WoR_HUD_layout_1g; everything ships in the mod
          'ghvh': {'pak': 'hud_vh', 'layout_1g': '0x9819ed56'}}
# Pixel shaders the stock HUDs draw after the scene composite (frame dumps 2026-10-02).
HIGHWAY_PS = {'FE74FFEA', '12827EBF', '5DBF7AEB'}
HUD_PS = {'2393BA2D', '86C2E6EF', 'E349266C', 'A43CA4E5'}


def set_ini(text, section, key, value):
    """Set key=value inside [section], preserving everything else (comments, order, duplicate headers)."""
    lines = text.split('\n')
    start = next((i for i, l in enumerate(lines) if l.strip() == f'[{section}]'), None)
    if start is None:
        return text.rstrip('\n') + f'\n\n[{section}]\n{key}={value}\n'
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('[') and lines[i].strip() != f'[{section}]'), len(lines))
    for i in range(start + 1, end):
        if lines[i].split('=', 1)[0].strip() == key:
            lines[i] = f'{key}={value}'
            return '\n'.join(lines)
    lines.insert(start + 1, f'{key}={value}')
    return '\n'.join(lines)


def dump_rows(dump_dir):
    path = os.path.join(dump_dir, 'draws.csv')
    if not os.path.exists(path):
        return [], ''
    text = open(path).read()
    return [r for r in csv.reader(text.splitlines()) if r and not r[0].startswith('#')][1:], text


def is_gameplay(dump_dir):
    """A gameplay frame draws the highway/gem shaders (frame dump 2026-10-02)."""
    rows, _ = dump_rows(dump_dir)
    return any(r[3] in HIGHWAY_PS for r in rows)


def focus_window(pid):
    """Restore and bring the game's main window to the foreground (Win32 via ctypes)."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    for hwnd in found:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)


def game_running():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq GHWT_Definitive.exe'], capture_output=True, text=True).stdout
    return 'GHWT_Definitive.exe' in out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hud', default='ghwor')
    ap.add_argument('--song', default='aboutagirl')
    ap.add_argument('--wait', type=int, default=60, help='seconds from launch before the first frame dump')
    ap.add_argument('--debug-mpm', action='store_true')
    ap.add_argument('--hold', type=int, default=0,
                    help='keep the game running this many seconds after gameplay is reached (song end, pak unload), '
                         'dumping a frame every 20 s; a crash in that window is reported')
    a = ap.parse_args()

    if game_running():
        print('HARNESS: the game is already running; close it first.')
        return 2
    os.makedirs(OUT, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    backup = os.path.join(OUT, f'GHWTDE.ini.backup-{stamp}')
    shutil.copy2(INI, backup)
    original = open(INI, encoding='utf-8', errors='surrogateescape').read()
    dumps_before = set(glob.glob(os.path.join(DUMPS, '*')))
    gameplay_dump = [None]
    proc = None
    try:
        t = original
        for sec, k, v in [('AutoLaunch', 'Enabled', '1'), ('AutoLaunch', 'Song', a.song), ('AutoLaunch', 'Players', '1'),
                          ('AutoLaunch', 'Part', 'guitar'), ('AutoLaunch', 'Bot', '1'), ('AutoLaunch', 'HideHUD', '0'),
                          ('Graphics', 'HUDTheme', a.hud)] + ([('Debug', 'DebugMPM', '1'), ('Debug', 'DebugMPMPaths', '1')] if a.debug_mpm else []):
            t = set_ini(t, sec, k, v)
        open(INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(t)

        if os.path.exists(TRIGGER):
            os.remove(TRIGGER)
        proc = subprocess.Popen([EXE], cwd=GAME)
        print(f'launched PID {proc.pid}; dumping frames until a gameplay frame appears (max {a.wait + 150}s)')
        # AutoLaunch only gets past "press any button" while the game window has focus; a minimized fullscreen
        # game sits on the title screen until attract mode starts (run 2026-10-03 01:55). Keep it in front.
        for _ in range(a.wait // 5):
            time.sleep(5)
            focus_window(proc.pid)
        deadline = time.time() + 150
        while time.time() < deadline and proc.poll() is None:
            seen = set(glob.glob(os.path.join(DUMPS, '*')))
            open(TRIGGER, 'w').close()
            t_end = time.time() + 20
            while time.time() < t_end and not (set(glob.glob(os.path.join(DUMPS, '*'))) - seen):
                time.sleep(1)
            time.sleep(3)  # let the dump finish writing
            new = sorted(set(glob.glob(os.path.join(DUMPS, '*'))) - seen)
            if new and is_gameplay(new[-1]):
                gameplay_dump[0] = new[-1]
                break
            time.sleep(5)
        held = []
        t_hold = time.time() + a.hold
        while a.hold and time.time() < t_hold and proc.poll() is None:
            focus_window(proc.pid)
            open(TRIGGER, 'w').close()
            time.sleep(20)
            held.append(round(a.hold - (t_hold - time.time())))
        if proc.poll() is not None:
            print(f'game exited early (code {proc.returncode})')
        exited = proc.poll()
    finally:
        if proc is not None and proc.poll() is None:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/F'], capture_output=True)
            try:
                proc.wait(15)
            except subprocess.TimeoutExpired:
                pass
        open(INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(original)
        print('GHWTDE.ini restored')

    # ---- evidence ----
    log = open(LOG, encoding='utf-8', errors='replace').read()
    shutil.copy2(LOG, os.path.join(OUT, f'debug-{stamp}.txt'))
    new_dumps = sorted(set(glob.glob(os.path.join(DUMPS, '*'))) - dumps_before)
    exp = EXPECT.get(a.hud, {})
    checks = []

    def check(name, ok, detail=''):
        checks.append({'check': name, 'pass': bool(ok), 'detail': detail})

    attract = 'No band logos in attract mode' in log
    check('harness: AutoLaunch started the song (not attract mode)', not attract,
          'attract mode ran: the window probably lost focus; this run says nothing about the HUD' if attract else '')
    check('mod registered', 'WoR_HUD: registering Warriors of Rock HUD theme' in log)
    check('mod textures registered', 'WoR_HUD: textures registered and loaded' in log)
    crit = [l for l in log.splitlines() if 'CRITICAL' in l]
    check('no CRITICAL in log', not crit, '; '.join(crit[:3]))
    # The paks requested by the theme loader: MPM lines between 'hudtheme_load_paks' and the HUD layout line.
    seg = re.findall(r'hudtheme_load_paks(.*?)HUD layout:', log, re.S)
    loads = sorted(set(re.findall(r'MPM: (pak/hud_[A-Za-z_]+)\.pak\.xen', seg[-1]))) if seg else []
    want_paks = [f"pak/{exp['pak']}"] if exp.get('pak') else []
    check('theme paks as expected', loads == sorted(want_paks + ['pak/hud_shared_assets']), f'loaded: {loads}')
    layouts = re.findall(r'HUD layout: (\S+)', log)
    check('theme layout selected', exp and exp['layout_1g'] in layouts, f'layouts: {sorted(set(layouts))}')
    if a.hud == 'ghwor':
        files = sorted(set(re.findall(r'CreateFileA: [^\n]*\\MODS\\WoR_HUD\\IMAGES\\([^\\\n]+\.img\.xen)', log, re.I)))
        check('mod images opened from the mod folder', len(files) == len(os.listdir(os.path.join(GAME, 'DATA', 'MODS', 'WoR_HUD', 'IMAGES'))),
              f'opened: {files}')
    hud_draws = None
    gd = gameplay_dump[0]
    check('reached gameplay (highway drawn in a dumped frame)', gd is not None, gd or f'{len(new_dumps)} dumps, none in gameplay')
    if gd:
        rows, text = dump_rows(gd)
        inj = re.search(r'injected_at=(-?\d+)', text)
        start = int(inj.group(1)) if inj and int(inj.group(1)) >= 0 else 0
        hud_draws = sum(1 for r in rows if int(r[0]) >= start and r[3] in HUD_PS)
    check('HUD drawn in gameplay (stock HUD shaders after composite)', hud_draws is not None and hud_draws > 0, f'draws: {hud_draws}')
    crash_dir = os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps')
    new_crash = [f for f in glob.glob(os.path.join(crash_dir, 'GHWT_Definitive*.dmp')) if os.path.getmtime(f) > time.mktime(time.strptime(stamp, '%Y%m%d-%H%M%S'))]
    check('no crash (no new crash dump, game still running at the end)', not new_crash and exited is None,
          f'exit code {exited}; dumps {new_crash}')
    unloads = re.findall(r'Unloading pak (0x[0-9a-f]+)', log)
    check('info: paks unloaded during the run', True, ', '.join(unloads[-8:]))

    report = {'stamp': stamp, 'hud': a.hud, 'song': a.song, 'checks': checks, 'dump': gameplay_dump[0]}
    json.dump(report, open(os.path.join(OUT, f'report-{stamp}.json'), 'w'), indent=1)
    for c in checks:
        print(f"{'PASS' if c['pass'] else 'FAIL'}  {c['check']}  {c['detail']}")
    return 0 if all(c['pass'] for c in checks) else 1


if __name__ == '__main__':
    sys.exit(main())
