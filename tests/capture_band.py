"""Bot-played band captures for the multiplayer layouts (no player needed), one game run per line-up.

Uses GHWT:DE's AutoLaunch (Players / Part<n> / Bot<n>) and the ghwt_bgfx add-on's frame dump (final_shown.bmp), like
tests/ingame_smoke.py. GHWTDE.ini is backed up and restored after every run. Frames land in tests/results/band-<stamp>/.

usage: python capture_band.py [--only 2g,1g1v,2g1v,3g1v] [--song aboutagirl] [--wait 60] [--frames 3]
exit code: 0 every line-up captured, 1 some line-up reached no gameplay frame, 2 the harness itself failed
"""
import argparse, glob, os, shutil, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_smoke as H  # noqa: E402

# line-up -> the layout the DE picks for it (docs/research/de_layouts.md, update_hud_layout)
LINEUPS = {
    '2g': ['guitar', 'drum'],
    '1g1v': ['guitar', 'vocals'],
    '2g1v': ['guitar', 'drum', 'vocals'],
    '3g1v': ['guitar', 'bass', 'drum', 'vocals'],
}


def run(name, parts, a, out):
    original = open(H.INI, encoding='utf-8', errors='surrogateescape').read()
    proc = None
    got = []
    try:
        t = original
        sets = [('AutoLaunch', 'Enabled', '1'), ('AutoLaunch', 'Song', a.song), ('AutoLaunch', 'Players', str(len(parts))),
                ('AutoLaunch', 'HideHUD', '0'), ('Graphics', 'HUDTheme', 'ghwor')]
        for i, p in enumerate(parts):
            sfx = '' if i == 0 else str(i + 1)
            sets += [('AutoLaunch', 'Part' + sfx, p), ('AutoLaunch', 'Bot' + sfx, '1')]
        for sec, k, v in sets:
            t = H.set_ini(t, sec, k, v)
        open(H.INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(t)
        if os.path.exists(H.TRIGGER):
            os.remove(H.TRIGGER)
        proc = subprocess.Popen([H.EXE], cwd=H.GAME)
        print(f'[{name}] launched PID {proc.pid} ({"+".join(parts)})', flush=True)
        for _ in range(a.wait // 5):
            time.sleep(5)
            H.focus_window(proc.pid)
        deadline = time.time() + 150
        while time.time() < deadline and proc.poll() is None and len(got) < a.frames:
            H.focus_window(proc.pid)
            seen = set(glob.glob(os.path.join(H.DUMPS, '*')))
            open(H.TRIGGER, 'w').close()
            t_end = time.time() + 20
            while time.time() < t_end and not (set(glob.glob(os.path.join(H.DUMPS, '*'))) - seen):
                time.sleep(1)
            time.sleep(3)
            new = sorted(set(glob.glob(os.path.join(H.DUMPS, '*'))) - seen)
            if new and H.is_gameplay(new[-1]):
                bmp = os.path.join(new[-1], 'final_shown.bmp')
                if os.path.exists(bmp):
                    dst = os.path.join(out, f'{name}_{len(got)}.bmp')
                    shutil.copy2(bmp, dst)
                    got.append(dst)
                    print(f'[{name}] frame {dst}', flush=True)
            time.sleep(8)
        if proc.poll() is not None:
            print(f'[{name}] game exited early (code {proc.returncode})', flush=True)
    finally:
        if proc is not None and proc.poll() is None:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/F'], capture_output=True)
            try:
                proc.wait(15)
            except subprocess.TimeoutExpired:
                pass
        open(H.INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(original)
    for f in ('wor_hud_fixes.log',):
        src = os.path.join(H.GAME, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out, f'{name}_{f}'))
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=','.join(LINEUPS))
    ap.add_argument('--song', default='aboutagirl')
    ap.add_argument('--wait', type=int, default=60)
    ap.add_argument('--frames', type=int, default=3)
    a = ap.parse_args()
    if H.game_running():
        print('HARNESS: the game is already running; close it first.')
        return 2
    out = os.path.join(H.OUT, 'band-' + time.strftime('%Y%m%d-%H%M%S'))
    os.makedirs(out, exist_ok=True)
    shutil.copy2(H.INI, os.path.join(out, 'GHWTDE.ini.backup'))
    missing = []
    for name in a.only.split(','):
        if not run(name, LINEUPS[name], a, out):
            missing.append(name)
        time.sleep(5)
    print('frames in', out, '| no gameplay frame:', missing or 'none')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
