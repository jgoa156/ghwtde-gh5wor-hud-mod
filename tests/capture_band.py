"""Bot-played band capture for the multiplayer layouts (no player needed): ONE game launch, ONE line-up, then it stops.
AutoLaunch fixes the players at boot, so one launch covers one line-up (default 3g1v, the full band). The script runs
once: it leaves tests/results/capture_band.done and refuses to launch again while that file exists (delete it to
allow another run).

Uses GHWT:DE's AutoLaunch (Players / Part<n> / Bot<n>) and the ghwt_bgfx add-on's frame dump (final_shown.bmp), like
tests/ingame_smoke.py. GHWTDE.ini is backed up and restored after every run. Frames land in tests/results/band-<stamp>/.

usage: python capture_band.py [--lineup 3g1v|2g|1g1v|2g1v] [--song aboutagirl] [--wait 150] [--frames 5]
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


def game_windows(pid):
    """Visible top-level windows of the game process: [(hwnd, class, title, area, owner)]."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    out = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            r = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(r))
            cls = ctypes.create_unicode_buffer(128)
            user32.GetClassNameW(hwnd, cls, 128)
            title = ctypes.create_unicode_buffer(128)
            user32.GetWindowTextW(hwnd, title, 128)
            out.append((hwnd, cls.value, title.value, (r.right - r.left) * (r.bottom - r.top), user32.GetWindow(hwnd, 4)))
        return True

    user32.EnumWindows(cb, 0)
    return out


def keep_in_front(pid):
    """Bring the game's MAIN window to the front only when no window of the game has the foreground. (2026-10-22: the
    old helper re-focused every visible window of the process, so it kept taking the foreground from the game's own
    fullscreen window: the screen blanked and the boot screen paused. No Alt taps, no restore while in front.)
    Returns True when the game holds the foreground."""
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    fg = user32.GetForegroundWindow()
    owner = wintypes.DWORD()
    user32.GetWindowThreadProcessId(fg, ctypes.byref(owner))
    if owner.value == pid:
        return True
    wins = [w for w in game_windows(pid) if not w[4]]          # unowned top-level windows only
    if not wins:
        return False
    main = max(wins, key=lambda w: w[3])[0]
    if user32.IsIconic(main):
        user32.ShowWindow(main, 9)                              # SW_RESTORE, only when minimized
    fg_thread = user32.GetWindowThreadProcessId(fg, None)
    me = ctypes.windll.kernel32.GetCurrentThreadId()
    attached = fg_thread and fg_thread != me and user32.AttachThreadInput(me, fg_thread, True)
    user32.SetForegroundWindow(main)
    if attached:
        user32.AttachThreadInput(me, fg_thread, False)
    return user32.GetForegroundWindow() == main


def run(name, parts, a, out):
    original = open(H.INI, encoding='utf-8', errors='surrogateescape').read()
    proc = None
    got = []
    try:
        t = original
        # the DE's own AutoLaunch only runs for WTDE developers (WTDE_IsUser); [WoR_HUD] TestAutoLaunch=1 makes the
        # mod's title screen run the same AutoLaunch setup (build.py TEST_AUTOLAUNCH_SCRIPT, plugin 1.42)
        sets = [('WoR_HUD', 'TestAutoLaunch', '1'), ('AutoLaunch', 'Song', a.song), ('AutoLaunch', 'Players', str(len(parts))),
                ('AutoLaunch', 'Venue', 'z_frathouse'), ('AutoLaunch', 'HideHUD', '0'), ('Graphics', 'HUDTheme', 'ghwor')]
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
        # and count how often that worked (keep_in_front returns whether the game holds the foreground)
        held = tries = 0
        for _ in range(a.wait // 5):
            time.sleep(5)
            if proc.poll() is not None:
                break
            tries += 1
            held += bool(keep_in_front(proc.pid))
            if tries == 3:
                for w in game_windows(proc.pid):
                    print(f'[{name}] window {w[0]:#x} class={w[1]!r} title={w[2]!r} area={w[3]} owner={w[4]:#x}', flush=True)
        print(f'[{name}] foreground held {held}/{tries} checks during the boot wait', flush=True)
        if tries and not held:
            print(f'[{name}] WARNING: the game never got the foreground; it stays on the boot screen without it', flush=True)
        deadline = time.time() + 240
        while time.time() < deadline and proc.poll() is None and len(got) < a.frames:
            keep_in_front(proc.pid)
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
    ap.add_argument('--wait', type=int, default=150)
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
