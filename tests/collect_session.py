"""Passive collector for a manual play session (does not launch or touch the game).

Every INTERVAL s: grab the game window into <out>/shots/. When the game exits: copy debug.txt, ReShade.log
and any new CrashDumps files into <out>. Usage: python collect_session.py <out_dir>
"""
import ctypes, glob, os, shutil, subprocess, sys, time
from ctypes import wintypes
from PIL import ImageGrab

OUT = sys.argv[1]
INTERVAL = 10
CFG = r'C:\Users\rockb\OneDrive\Documentos\My Games\Guitar Hero World Tour Definitive Edition'
GAME = r'D:\Games\Guitar Hero World Tour'
CRASH = os.path.expandvars(r'%LOCALAPPDATA%\CrashDumps')
os.makedirs(os.path.join(OUT, 'shots'), exist_ok=True)
user32 = ctypes.windll.user32


def game_pid():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq GHWT_Definitive.exe', '/FO', 'CSV', '/NH'],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if 'GHWT_Definitive' in line:
            return int(line.split('","')[1])
    return None


def window_rect(pid):
    found = []
    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            r = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(r))
            pt = wintypes.POINT(0, 0)
            user32.ClientToScreen(hwnd, ctypes.byref(pt))
            if r.right > 400:
                found.append((pt.x, pt.y, pt.x + r.right, pt.y + r.bottom))
        return True
    user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return found[0] if found else None


before = set(os.listdir(CRASH)) if os.path.isdir(CRASH) else set()
t_wait = time.time()
while not game_pid() and time.time() - t_wait < 1800:     # wait for the user to launch the game
    time.sleep(2)
pid = game_pid()
t0 = time.time()
log = open(os.path.join(OUT, 'collector.log'), 'a')
def note(s):
    line = '%6.0fs %s' % (time.time() - t0, s)
    print(line, flush=True); log.write(line + '\n'); log.flush()

note('collector start, game pid %s' % pid)
n = 0
while game_pid():
    r = window_rect(game_pid())
    if r:
        try:
            ImageGrab.grab(bbox=r, all_screens=True).save(os.path.join(OUT, 'shots', 's%04d_%04ds.png' % (n, time.time() - t0)))
            n += 1
        except Exception as e:
            note('grab failed: %s' % e)
    time.sleep(INTERVAL)
note('game exited after %d shots' % n)
time.sleep(3)
for src, name in [(os.path.join(CFG, 'Logs', 'debug.txt'), 'debug.txt'), (os.path.join(GAME, 'ReShade.log'), 'ReShade.log'),
                  (os.path.join(CFG, 'GHWTDE.ini'), 'GHWTDE.ini')]:
    try:
        shutil.copy2(src, os.path.join(OUT, name)); note('copied ' + name)
    except Exception as e:
        note('copy %s failed: %s' % (name, e))
for f in sorted(set(os.listdir(CRASH)) - before) if os.path.isdir(CRASH) else []:
    shutil.copy2(os.path.join(CRASH, f), os.path.join(OUT, f)); note('NEW CRASH DUMP ' + f)
note('done')
