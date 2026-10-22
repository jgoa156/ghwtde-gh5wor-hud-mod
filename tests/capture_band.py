"""Bot-played band capture for the multiplayer layouts (no player needed): ONE game launch, ONE line-up, then it stops.
AutoLaunch fixes the players at boot, so one launch covers one line-up (default 3g1v, the full band). The script runs
once: it leaves tests/results/capture_band.done and refuses to launch again while that file exists (delete it to
allow another run).

Uses GHWT:DE's AutoLaunch (Players / Part<n> / Bot<n>) and the ghwt_bgfx add-on's frame dump (final_shown.bmp), like
tests/ingame_smoke.py. GHWTDE.ini is backed up and restored after every run. Frames land in tests/results/band-<stamp>/.

usage: python capture_band.py [--lineup 3g1v|2g|1g1v|2g1v] [--song aboutagirl] [--wait 120] [--frames 5]
exit code: 0 frames captured, 1 no gameplay frame (do NOT rerun: report), 2 refused (already ran / game running)
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
        # the game only advances while it is the foreground window (boot screen frozen otherwise): keep it in front
        # and count how often that worked (H.focus_window returns whether the game holds the foreground)
        held = tries = 0
        for _ in range(a.wait // 2):
            time.sleep(2)
            if proc.poll() is not None:
                break
            tries += 1
            held += bool(H.focus_window(proc.pid))
        print(f'[{name}] foreground held {held}/{tries} checks during the boot wait', flush=True)
        if tries and not held:
            print(f'[{name}] WARNING: the game never got the foreground; it stays on the boot screen without it', flush=True)
        deadline = time.time() + 240
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
            print(f'[{name}] game exited early (code {proc.returncode}): closed by hand, or crashed (check %LOCALAPPDATA%/CrashDumps)', flush=True)
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
    ap.add_argument('--lineup', default='3g1v', choices=sorted(LINEUPS))
    ap.add_argument('--song', default='aboutagirl')
    ap.add_argument('--wait', type=int, default=120)
    ap.add_argument('--frames', type=int, default=5)
    a = ap.parse_args()
    done = os.path.join(H.OUT, 'capture_band.done')
    if os.path.exists(done):
        print(f'REFUSED: the capture already ran ({open(done).read().strip()}). One run only; delete {done} to allow another.')
        return 2
    if H.game_running():
        print('REFUSED: the game is already running; close it first.')
        return 2
    out = os.path.join(H.OUT, 'band-' + time.strftime('%Y%m%d-%H%M%S'))
    os.makedirs(out, exist_ok=True)
    shutil.copy2(H.INI, os.path.join(out, 'GHWTDE.ini.backup'))
    open(done, 'w').write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {a.lineup} -> {out}\n')   # before launching: one run, even if it fails
    got = run(a.lineup, LINEUPS[a.lineup], a, out)
    print(f'RESULT: {len(got)} frame(s) in {out}' if got else f'RESULT: no gameplay frame captured ({out})')
    return 0 if got else 1


if __name__ == '__main__':
    sys.exit(main())
