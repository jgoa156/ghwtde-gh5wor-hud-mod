"""Bot-played band capture for the multiplayer layouts (no player needed): ONE game launch, ONE line-up, then it stops.
AutoLaunch fixes the players at boot, so one launch covers one line-up (default 3g1v, the full band). The script runs
once: it leaves tests/results/capture_band.done and refuses to launch again while that file exists (delete it to
allow another run).

Uses GHWT:DE's AutoLaunch setup (Players / Part<n> / Bot<n>, run from the title screen by the mod's [WoR_HUD]
TestAutoLaunch=1 hook) and plain screenshots on a clock from the launch (every 15 s from +90 s until the game quits after the song). GHWTDE.ini, GHWTDE.sav and the Profiles/*.car are backed up and restored after every run (the bot run would save over them). Frames (PNG) land in tests/results/band-<stamp>/.

usage: python capture_band.py [--lineup 3g1v|2g|1g1v|2g1v] [--song ontheroadagain] [--wait 150] [--frames 5]
exit code: 0 frames captured, 1 no gameplay frame (do NOT rerun: report), 2 refused (already ran / game running)
"""
import argparse, glob, os, shutil, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingame_smoke as H  # noqa: E402

# line-up -> the layout the DE picks for it (docs/research/de_layouts.md, update_hud_layout)
LINEUPS = {
    '1g': ['guitar'],                              # quickplay 1 player: the reference the multiplayer pieces copy
    '2g': ['guitar', 'drum'],
    '1v': ['vocals'],
    '1g1v': ['guitar', 'vocals'],
    '2g1v': ['guitar', 'drum', 'vocals'],
    '3g': ['guitar', 'bass', 'drum'],              # 3 instruments, no vocals: hud_3g1v without its vocal highway
    '3g1v': ['guitar', 'bass', 'drum', 'vocals'],
    'faceoff': ['guitar', 'guitar'],
    'profaceoff': ['guitar', 'guitar'],
    'battle': ['guitar', 'guitar'],
}
# line-ups that are not quickplay: [AutoLaunch] GameMode (the DE's AutoLaunch setup 0x581325cc reads it; quickplay
# by player count otherwise)
MODES = {'faceoff': 'p2_faceoff', 'profaceoff': 'p2_pro_faceoff', 'battle': 'p2_battle'}


PLAY_DELAY = 10   # s from the plugin's gameplay marker (title card) to the first notes (2026-10-28 run)
VENUE = 'z_norway'      # Fjord of Swords: every test runs there (user 2026-10-29)
SHOT_FROM, SHOT_EVERY, SHOT_WINDOW = 90, 15, 180   # seconds after the launch: shots start at T+90 and run for 3 minutes
SHOT_UNTIL = SHOT_FROM + SHOT_WINDOW                 # (user 2026-10-22; ontheroadagain plays ~T+100..250 s); the game
# then sits on the results screen (user 2026-10-22: it does not proceed), so it is closed at SHOT_UNTIL


def screen_size():
    """The primary screen's size in physical pixels."""
    import ctypes
    u = ctypes.windll.user32
    u.SetProcessDPIAware()
    return u.GetSystemMetrics(0), u.GetSystemMetrics(1)


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


SAVE_FILES = ['GHWTDE.sav', os.path.join('Profiles', '*.car')]   # in H.CFG_DIR


def backup_save(out):
    """Copy the player's save + profiles aside. The bot run boots without loading them (AutoLaunch skips the memcard
    step) and the game saves its fresh progress over them after the song: 2026-10-22 that wiped the user's save
    (restored from a shadow copy). Returns [(original path, backup path)]."""
    saved = []
    keep = os.path.join(out, 'save-backup')
    os.makedirs(keep, exist_ok=True)
    for pat in SAVE_FILES:
        for f in glob.glob(os.path.join(H.CFG_DIR, pat)):
            dst = os.path.join(keep, os.path.relpath(f, H.CFG_DIR).replace(os.sep, '_'))
            shutil.copy2(f, dst)
            saved.append((f, dst))
    if not any(os.path.basename(f) == 'GHWTDE.sav' for f, _ in saved):
        raise SystemExit('REFUSED: no GHWTDE.sav found to back up; not launching')
    return saved


def restore_save(saved):
    """Put the save back byte for byte and drop files the run created (new profiles)."""
    before = {f for f, _ in saved}
    for pat in SAVE_FILES:
        for f in glob.glob(os.path.join(H.CFG_DIR, pat)):
            if f not in before:
                os.remove(f)
    for f, dst in saved:
        shutil.copy2(dst, f)
    ok = all(open(f, 'rb').read() == open(dst, 'rb').read() for f, dst in saved)
    print(f'save restored ({len(saved)} files, verified: {ok})', flush=True)
    return ok


def run(name, parts, a, out):
    original = open(H.INI, encoding='utf-8', errors='surrogateescape').read()
    saved = backup_save(out)
    proc = None
    got = []
    try:
        t = original
        # the DE's own AutoLaunch only runs for WTDE developers (WTDE_IsUser); [WoR_HUD] TestAutoLaunch=1 makes the
        # mod's title screen run the same AutoLaunch setup (build.py TEST_AUTOLAUNCH_SCRIPT, plugin 1.42)
        sets = [('WoR_HUD', 'TestAutoLaunch', '1'), ('AutoLaunch', 'Song', a.song), ('AutoLaunch', 'Players', str(len(parts))),
                ('AutoLaunch', 'Venue', VENUE), ('AutoLaunch', 'HideHUD', '0'), ('Graphics', 'HUDTheme', 'ghwor'),
                ('AutoLaunch', 'GameMode', MODES.get(name, 'not_defined'))]
        for i, p in enumerate(parts):
            sfx = '' if i == 0 else str(i + 1)
            sets += [('AutoLaunch', 'Part' + sfx, p), ('AutoLaunch', 'Bot' + sfx, '1')]
        if a.bulb_cycle:          # the band bulb steps through x1..x4 and star power x2..x8 (tools/wor_band.py)
            sets.append(('WoR_HUD', 'TestBulbCycle', '1'))
        # --native (user 2026-10-29: "the 1920x1080 resolution is stretched and needs to be windowed so it does not
        # stretch"): the game windowed and borderless at the screen's own size, no scaling of the picture (the INI's
        # own 3840x2160 borderless full screen is scaled onto the 2560x1080 screen)
        if getattr(a, 'native', False):
            w, h = screen_size()
            sets += [('Graphics', 'WindowedMode', '1'), ('Graphics', 'Borderless', '1'),
                     ('Graphics', 'ResolutionX', str(w)), ('Graphics', 'ResolutionY', str(h))]
        if getattr(a, 'sp_states', False):   # fixed star power states (build.py WoR_HUD_test_sp_states)
            sets.append(('WoR_HUD', 'TestSPStates', '1'))
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
        # Frames: plain screenshots (PIL ImageGrab; the ghwt_bgfx dump add-on writes nothing on this install) on a
        # clock from the launch: every SHOT_EVERY s from SHOT_FROM s until the game closes. Both the DE's debug.txt and
        # the plugin's log are locked while the game runs, so nothing in game can time them. Runs 2026-10-22 (bots,
        # 4 players, aboutagirl): gameplay from ~T+100 s to ~T+320 s, results screen, then the game quits by itself
        # (~T+350 s). Pick the gameplay frames afterwards.
        from PIL import ImageGrab
        held = tries = 0
        t0 = time.time()
        shot_from = getattr(a, 'shot_from', 0) or SHOT_FROM   # --from: battle ended at T+100 s (2026-10-29)
        next_shot = t0 + shot_from
        deadline = t0 + (a.until or SHOT_UNTIL)   # --until: close the game earlier (user 2026-10-27: ~1 min of song)
        # --play N (user 2026-10-28: "your runs are going way past 30s ... force kill after that time"): the plugin
        # (1.72) writes wor_hud_gameplay.flag on the song's first star power update; frames run from there and the
        # game is killed N s later. --until stays the hard limit from the launch.
        flag = os.path.join(H.GAME, 'wor_hud_gameplay.flag')
        if os.path.exists(flag):
            os.remove(flag)
        play_from = None
        play = getattr(a, 'play', 0)   # tests/ultrawide_ab.py passes its own namespace
        if play:
            next_shot = deadline + 1
        # --video (2026-10-29: the battle card's collect flight lasts under a second, between frames): the whole
        # screen at 30 fps from the gameplay marker (or SHOT_FROM) to the end, ffmpeg gdigrab, stopped with 'q'
        video = None
        while time.time() < deadline and proc.poll() is None:
            time.sleep(1)
            if play and play_from is None and os.path.exists(flag):
                play_from = time.time() + PLAY_DELAY   # the marker comes with the song's title card
                next_shot = play_from + 1
                deadline = min(deadline, play_from + play)
                print(f'[{name}] gameplay at T+{int(play_from - t0)} s: frames for {play} s', flush=True)
            start = (play_from and play_from - PLAY_DELAY) if play else t0 + shot_from
            if getattr(a, 'video', False) and video is None and start and time.time() >= start:
                video = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'gdigrab', '-framerate', '30',
                                          '-i', 'desktop', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '20',
                                          '-pix_fmt', 'yuv420p', os.path.join(out, f'{name}.mp4')],
                                         stdin=subprocess.PIPE)
                print(f'[{name}] video started at T+{int(time.time() - t0)} s', flush=True)
            if int(time.time() - t0) % 5 == 0:
                tries += 1
                held += bool(keep_in_front(proc.pid))
                if tries == 3:
                    for w in game_windows(proc.pid):
                        print(f'[{name}] window {w[0]:#x} class={w[1]!r} title={w[2]!r} area={w[3]} owner={w[4]:#x}', flush=True)
            if time.time() >= next_shot:
                dst = os.path.join(out, f'{name}_t{int(time.time() - t0):03d}.png')
                ImageGrab.grab().save(dst)
                got.append(dst)
                print(f'[{name}] frame {dst}', flush=True)
                next_shot += (a.every or SHOT_EVERY)
        if video is not None:
            try:
                video.communicate(b'q', timeout=30)
            except subprocess.TimeoutExpired:
                video.kill()
            print(f'[{name}] video {os.path.join(out, name + ".mp4")}', flush=True)
        print(f'[{name}] foreground held {held}/{tries} checks', flush=True)
        if proc.poll() is not None:
            print(f'[{name}] game closed (code {proc.returncode}) after {int(time.time() - t0)} s (it quits by itself after the song)', flush=True)
    finally:
        if proc is not None and proc.poll() is None:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/F'], capture_output=True)
            try:
                proc.wait(15)
            except subprocess.TimeoutExpired:
                pass
        open(H.INI, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(original)
        restore_save(saved)
    for f in ('wor_hud_fixes.log',):
        src = os.path.join(H.GAME, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(out, f'{name}_{f}'))
    # the DE's own log (our printf lines land there): the next launch overwrites it
    dbg = os.path.join(os.path.dirname(H.INI), 'Logs', 'debug.txt')
    if os.path.exists(dbg):
        shutil.copy2(dbg, os.path.join(out, f'{name}_debug.txt'))
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lineup', default='3g1v', choices=sorted(LINEUPS))
    ap.add_argument('--song', default='ontheroadagain')   # on-disc, short (user 2026-10-22); MODS songs load no notes via AutoLaunch
    ap.add_argument('--wait', type=int, default=150)
    ap.add_argument('--frames', type=int, default=5)
    ap.add_argument('--until', type=int, default=0)     # seconds after the launch to close the game (0 = SHOT_UNTIL)
    ap.add_argument('--every', type=int, default=0)      # seconds between frames (0 = SHOT_EVERY)
    ap.add_argument('--play', type=int, default=0)       # seconds of gameplay from the plugin's marker, then kill
    ap.add_argument('--native', action='store_true')     # windowed borderless at the screen's size (no stretching)
    ap.add_argument('--sp-states', action='store_true')  # 25/45/70/100 % then deploy, every 28 s (compare_wor.py)
    ap.add_argument('--bulb-cycle', action='store_true')   # band line-ups: every bulb in turn with its popup
    ap.add_argument('--from', dest='shot_from', type=int, default=0)   # seconds after the launch for the first frame (0 = SHOT_FROM)
    ap.add_argument('--video', action='store_true')      # 30 fps screen video from the gameplay marker (or SHOT_FROM)
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
