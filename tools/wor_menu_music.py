"""Main menu music collection for GHWT:DE: every game's menu songs in ONE menu music mod, so the DE shuffles them all.

The DE loads only one menu music mod ("ERROR: Exceeded limit of 1 menu music mod." in Logs\\debug.txt), so each game
is a SOURCE merged into one bank. Sources:
  - existing DE menu music mods (e.g. Raccoon_333's "(GH5) Main Menu Music", kept in paths.MENU_MUSIC_SOURCES, NOT in
    DATA\\MODS): their MP3 samples are copied as they are, with their ini Delay/Volume/Offset;
  - Warriors of Rock, from your own copy (paths.WOR_XBOX): data/streams/streamall.fsb.xen is an Xbox FSB4 bank of XMA
    streams indexed by streamall.dat.xen; WoR plays menu_music_songs (scripts/game/audio/global_sound_definitions.qb),
    14 gh6_mm_* clips. Each is wrapped as an XMA2 RIFF, decoded by ffmpeg (xma2), brought to MM_LUFS with a peak
    limiter (WoR's streams are mixed ~12 dB quieter than the GH5 mod's) and encoded to 48 kHz stereo MP3 frames.
More games: add a source function returning clips.

DE menu music mod layout:
  menumusic.ini              [MenuMusicInfo] FSBName + Track=<name> lines, then one [<name>] Delay/Volume/Offset each
  Content/<FSBName>.dat.xen  u32 count, u32 qbkey(FSBName), count x {u32 qbkey(track), u32 index, 12 zero bytes} (BE)
  Content/<FSBName>.fsb.xen  FSB4, 80-byte sample headers, MPEG (mode 0x220), data back to back

usage: python wor_menu_music.py <out folder>   (needs ffmpeg on PATH)
"""
import glob, math, os, shutil, struct, subprocess, sys, tempfile, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

MOD_DIR = 'Main Menu Music Collection'
FSB_NAME = 'Menu_Music_Collection'
# WoR's menu_music_songs, in its order (each: delay 0.0, vol 3, offset 0 in WoR)
WOR_TRACKS = ['gh6_mm_bodies', 'gh6_mm_jetcitywoman', 'gh6_mm_chemicalwarfare', 'gh6_mm_bloodlines', 'gh6_mm_ravenous',
              'gh6_mm_hardtosee', 'gh6_mm_waidmannsheil', 'gh6_mm_holywars', 'gh6_mm_imbroken', 'gh6_mm_indians',
              'gh6_mm_psychosocial', 'gh6_mm_reignition', 'gh6_mm_theoutsider', 'gh6_mm_childrenofthegrave']
WOR_VOLUME = 6                               # the GH5 menu music mod's value
MM_LUFS = -10.0                              # the GH5 mod's tracks are ~-9.5 (user: -14 was too quiet next to them)
MP3_QUALITY = '2'                            # LAME VBR ~190 kb/s (the GH5 mod: ~166 kb/s VBR)


def qbkey(s):
    return ~zlib.crc32(s.lower().encode()) & 0xffffffff


def fsb4_samples(path):
    """[(name, samples, bytes, mode, freq, chans, data offset)] of an FSB4 bank."""
    with open(path, 'rb') as f:
        h = f.read(48)
        magic, num, shdr, _ = struct.unpack_from('<4sIII', h, 0)
        assert magic == b'FSB4', magic
        hdr = f.read(shdr)
    out, p, off = [], 0, 48 + shdr
    for _ in range(num):
        size = struct.unpack_from('<H', hdr, p)[0]
        name = hdr[p + 2:p + 32].split(b'\0')[0].decode('latin-1')
        nsamp, nbytes, _, _, mode = struct.unpack_from('<IIIII', hdr, p + 32)
        freq, _, _, _, chans = struct.unpack_from('<iHhHH', hdr, p + 52)
        out.append((name, nsamp, nbytes, mode, freq, chans, off))
        off += nbytes
        p += size
    return out


def read_ini(path):
    """{section: {key: [values]}} (Track repeats)."""
    out, sec = {}, None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            sec = out.setdefault(line[1:-1], {})
        elif '=' in line and sec is not None:
            k, v = line.split('=', 1)
            sec.setdefault(k.strip(), []).append(v.strip())
    return out


# ---- sources: each returns [(track name, mp3 frames, samples, delay, volume, offset)]

def source_menu_music_mod(folder):
    """An existing DE menu music mod (MP3 FSB4), copied as it is."""
    ini = read_ini(os.path.join(folder, 'menumusic.ini'))
    fsb_name = ini['MenuMusicInfo']['FSBName'][0]
    bank = os.path.join(folder, 'Content', fsb_name + '.fsb.xen')
    dat = open(os.path.join(folder, 'Content', fsb_name + '.dat.xen'), 'rb').read()
    index = {struct.unpack_from('>I', dat, 8 + 20 * k)[0]: struct.unpack_from('>I', dat, 12 + 20 * k)[0]
             for k in range(struct.unpack_from('>I', dat, 0)[0])}
    samples = fsb4_samples(bank)
    clips = []
    with open(bank, 'rb') as f:
        for t in ini['MenuMusicInfo']['Track']:
            name, nsamp, nbytes, mode, freq, chans, off = samples[index[qbkey(t)]]
            assert mode & 0x200 and freq == 48000 and chans == 2, (folder, name, hex(mode))
            f.seek(off)
            s = ini.get(t, {})
            clips.append((t, f.read(nbytes), nsamp, s.get('Delay', ['0.0'])[0], s.get('Volume', ['6'])[0],
                          s.get('Offset', ['0'])[0]))
    print(f'{os.path.basename(folder)}: {len(clips)} tracks copied')
    return clips


def xma2_riff(raw, samples, freq, chans):
    """Raw FSB4 XMA data as an XMA2 WAVE file (WAVEFORMATEX 0x166 + XMA2WAVEFORMATEX)."""
    block = 0x10000
    xma2 = struct.pack('<HIIIIIIIBBH', (chans + 1) // 2, {1: 0x4, 2: 0x3}.get(chans, 0), samples, block, 0, samples,
                       0, 0, 0, 4, max(1, math.ceil(len(raw) / block)))
    fmt = struct.pack('<HHIIHHH', 0x166, chans, freq, freq * chans * 2, 2048, 16, len(xma2)) + xma2
    body = b'WAVE' + b'fmt ' + struct.pack('<I', len(fmt)) + fmt + b'data' + struct.pack('<I', len(raw)) + raw
    return b'RIFF' + struct.pack('<I', len(body)) + body


def ffmpeg(*args):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return r.stderr


def loudness(wav):
    err = ffmpeg('-i', wav, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-')
    line = [l for l in err.splitlines() if l.strip().startswith('I:')][-1]
    return float(line.split()[1])


MP3_RATES = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]


def mp3_frames(data):
    """Data from the first MPEG-1 Layer III frame on, and its frame count (1152 samples each)."""
    i = 0
    while not (data[i] == 0xff and data[i + 1] & 0xfe == 0xfa):
        i += 1
    start, n = i, 0
    while i + 4 <= len(data):
        b1, b2 = data[i + 1], data[i + 2]
        assert data[i] == 0xff and b1 & 0xfe == 0xfa, f'lost sync at {i}'
        assert (b2 >> 2) & 3 == 1, 'not 48 kHz'
        i += 144 * MP3_RATES[b2 >> 4] * 1000 // 48000 + ((b2 >> 1) & 1)
        n += 1
    return data[start:i], n


def source_wor():
    """Warriors of Rock's 14 menu songs, from your own copy's stream bank."""
    bank = os.path.join(paths.WOR_XBOX, 'data', 'streams', 'streamall.fsb.xen')
    dat = open(os.path.join(paths.WOR_XBOX, 'data', 'streams', 'streamall.dat.xen'), 'rb').read()
    index = {struct.unpack_from('>I', dat, 8 + 20 * k)[0]: struct.unpack_from('>I', dat, 12 + 20 * k)[0]
             for k in range(struct.unpack_from('>I', dat, 0)[0])}
    samples = fsb4_samples(bank)
    work = tempfile.mkdtemp(prefix='wormm_')
    clips = []
    with open(bank, 'rb') as f:
        for t in WOR_TRACKS:
            name, nsamp, nbytes, mode, freq, chans, off = samples[index[qbkey(t)]]
            assert name.split('.')[0] == t and mode & 0x01000000 and freq == 48000 and chans == 2, (name, mode)
            f.seek(off)
            src = os.path.join(work, t + '.xma.wav')
            open(src, 'wb').write(xma2_riff(f.read(nbytes), nsamp, freq, chans))
            pcm = os.path.join(work, t + '.wav')
            ffmpeg('-y', '-i', src, pcm)
            gain = MM_LUFS - loudness(pcm)
            mp3 = os.path.join(work, t + '.mp3')
            ffmpeg('-y', '-i', pcm, '-af', f'volume={gain:.2f}dB,alimiter=limit=0.89:level=false', '-ar', '48000',
                   '-ac', '2', '-c:a', 'libmp3lame', '-q:a', MP3_QUALITY, '-write_xing', '0', '-id3v2_version', '0',
                   '-map_metadata', '-1', mp3)
            frames, n = mp3_frames(open(mp3, 'rb').read())
            clips.append((t, frames, n * 1152, '0.0', str(WOR_VOLUME), '0'))
            print(f'{t:28s} {nsamp / freq:7.2f}s  gain {gain:+.1f} dB  mp3 {len(frames) / 1e6:.1f} MB')
    shutil.rmtree(work, ignore_errors=True)
    return clips


def write_mod(out, clips):
    mod = os.path.join(out, MOD_DIR)
    shutil.rmtree(mod, ignore_errors=True)
    os.makedirs(os.path.join(mod, 'Content'))
    names = [c[0].lower() for c in clips]
    assert len(set(names)) == len(names), 'duplicate track names across sources'
    # FSB4: header, 80-byte sample headers (the GH5 mod's layout), data
    shdrs = b''
    for t, frames, nsamp, *_ in clips:
        shdrs += (struct.pack('<H30s', 80, (t + '.mp3').encode()[:29]) +
                  struct.pack('<IIIII', nsamp, len(frames), 0, nsamp - 4, 0x220) +
                  struct.pack('<iHhHH', 48000, 255, 128, 128, 2) + struct.pack('<ff', 1.0, 10000.0) + bytes(8))
    size = sum(len(c[1]) for c in clips)
    with open(os.path.join(mod, 'Content', FSB_NAME + '.fsb.xen'), 'wb') as f:
        f.write(struct.pack('<4sIIIII', b'FSB4', len(clips), len(shdrs), size, 0x40000, 0) + bytes(24) + shdrs)
        for c in clips:
            f.write(c[1])
    dat = struct.pack('>II', len(clips), qbkey(FSB_NAME)) + b''.join(
        struct.pack('>II', qbkey(c[0]), i) + bytes(12) for i, c in enumerate(clips))
    open(os.path.join(mod, 'Content', FSB_NAME + '.dat.xen'), 'wb').write(dat)
    ini = ['[ModInfo]', f'Name={FSB_NAME}',
           'Description=Main menu music from every game (GH5 mod by Raccoon_333 + Warriors of Rock from your own copy), shuffled',
           'Author=WitchDoctoR', 'Version=1.0', '', '[MenuMusicInfo]', f'FSBName={FSB_NAME}']
    ini += [f'Track={c[0]}' for c in clips] + ['']
    for t, _, _, delay, vol, offset in clips:
        ini += [f'[{t}]', f'Delay={delay}', f'Volume={vol}', f'Offset={offset}', '']
    open(os.path.join(mod, 'menumusic.ini'), 'w', newline='\r\n').write('\n'.join(ini))
    print(f'{MOD_DIR}: {len(clips)} tracks, {size / 1e6:.0f} MB')
    return mod


def build(out):
    clips = []
    for folder in sorted(glob.glob(os.path.join(paths.MENU_MUSIC_SOURCES, '*'))):
        if os.path.exists(os.path.join(folder, 'menumusic.ini')):
            clips += source_menu_music_mod(folder)
    clips += source_wor()
    return write_mod(out, clips)


if __name__ == '__main__':
    print(build(sys.argv[1]))
