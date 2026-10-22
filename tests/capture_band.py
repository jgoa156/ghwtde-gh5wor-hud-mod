"""Bot-played band capture for the multiplayer layouts (no player needed): ONE game launch, ONE line-up, then it stops.
AutoLaunch fixes the players at boot, so one launch covers one line-up (default 3g1v, the full band). The script runs
once: it leaves tests/results/capture_band.done and refuses to launch again while that file exists (delete it to
allow another run).

Uses GHWT:DE's AutoLaunch setup (Players / Part<n> / Bot<n>, run from the title screen by the mod's [WoR_HUD]
TestAutoLaunch=1 hook) and plain screenshots timed from the song start (wor_hud_fixes.log). GHWTDE.ini is backed up and restored after every run. Frames (PNG) land in tests/results/band-<stamp>/.

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


SHOT_AT = [15, 35, 55, 80, 110]        # seconds after the song start (aboutagirl is ~3:30; band SP comes ~1 min in)


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
        stale = os.path.join(H.GAME, 'wor_hud_fixes.log')      # the last run's log would trigger the shots at once
        if os.path.exists(stale):
            os.remove(stale)
        proc = subprocess.Popen([H.EXE], cwd=H.GAME)
        print(f'[{name}] launched PID {proc.pid} ({"+".join(parts)})', flush=True)
        # the game only advances while it is the foreground window (boot screen frozen otherwise): keep it in front
        # and count how often that worked (keep_in_front returns whether the game holds the foreground)
        # Frames: plain screenshots (PIL ImageGrab; the ghwt_bgfx dump add-on writes nothing on this install, run
        # 2026-10-22), timed from the song start: the plugin logs "score font: loaded" when the HUD is created
        # (wor_hud_fixes.log, readable while the game runs; the DE's debug.txt is locked). Shots at SHOT_AT seconds
        # after it, then the game is closed.
        from PIL import ImageGrab
        plugin_log = os.path.join(H.GAME, 'wor_hud_fixes.log')
        held = tries = 0
        song_t = None
        deadline = time.time() + a.wait + 240
        while time.time() < deadline and proc.poll() is None and len(got) < len(SHOT_AT):
            time.sleep(1 if song_t else 5)
            tries += 1
            held += bool(keep_in_front(proc.pid))
            if tries == 3:
                for w in game_windows(proc.pid):
                    print(f'[{name}] window {w[0]:#x} class={w[1]!r} title={w[2]!r} area={w[3]} owner={w[4]:#x}', flush=True)
            if song_t is None:
                try:
                    with open(plugin_log, encoding='utf-8', errors='replace') as f:
                        if 'score font: loaded' in f.read():
                            song_t = time.time()
                            print(f'[{name}] song started (HUD created), shots at +{SHOT_AT} s', flush=True)
                except OSError:
                    pass
                continue
            if time.time() - song_t >= SHOT_AT[len(got)]:
                dst = os.path.join(out, f'{name}_{len(got)}_t{SHOT_AT[len(got)]}.png')
                ImageGrab.grab().save(dst)
                got.append(dst)
                print(f'[{name}] frame {dst}', flush=True)
        print(f'[{name}] foreground held {held}/{tries} checks', flush=True)
        if song_t is None and proc.poll() is None:
            print(f'[{name}] the song never started (no HUD in wor_hud_fixes.log): automation did not get past the menus', flush=True)
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
