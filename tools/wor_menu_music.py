"""Warriors of Rock main menu music as a GHWT:DE menu music mod (same layout as Raccoon_333's "(GH5) Main Menu Music").

Source: your own WoR copy (paths.WOR_XBOX): data/streams/streamall.fsb.xen, an Xbox FSB4 bank of XMA streams indexed by
streamall.dat.xen. WoR plays menu_music_songs (scripts/game/audio/global_sound_definitions.qb): 14 gh6_mm_* clips.
Each is wrapped as an XMA2 RIFF, decoded by ffmpeg (xma2), brought to MM_LUFS with a peak limiter (WoR's streams are
mixed ~12 dB quieter than the GH5 mod's), and encoded to 48 kHz stereo MP3 frames (no tags), as the GH5 mod has them.

DE menu music mod layout:
  menumusic.ini              [MenuMusicInfo] FSBName + Track=<name> lines, then one [<name>] Delay/Volume/Offset each
  Content/<FSBName>.dat.xen  u32 count, u32 qbkey(FSBName), count x {u32 qbkey(track), u32 index, 12 zero bytes} (BE)
  Content/<FSBName>.fsb.xen  FSB4, 80-byte sample headers, MPEG (mode 0x220), data back to back

usage: python wor_menu_music.py <out folder>   (needs ffmpeg on PATH)
"""
import math, os, shutil, struct, subprocess, sys, tempfile, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa: E402

MOD_DIR = 'WoR Main Menu Music'
FSB_NAME = 'WoR_Music_Menu'
# WoR's menu_music_songs, in its order (each: delay 0.0, vol 3, offset 0 in WoR)
TRACKS = ['gh6_mm_bodies', 'gh6_mm_jetcitywoman', 'gh6_mm_chemicalwarfare', 'gh6_mm_bloodlines', 'gh6_mm_ravenous',
          'gh6_mm_hardtosee', 'gh6_mm_waidmannsheil', 'gh6_mm_holywars', 'gh6_mm_imbroken', 'gh6_mm_indians',
          'gh6_mm_psychosocial', 'gh6_mm_reignition', 'gh6_mm_theoutsider', 'gh6_mm_childrenofthegrave']
VOLUME = 6                                   # the GH5 menu music mod's value
MM_LUFS = -14.0
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


def build(out):
    bank = os.path.join(paths.WOR_XBOX, 'data', 'streams', 'streamall.fsb.xen')
    dat = open(os.path.join(paths.WOR_XBOX, 'data', 'streams', 'streamall.dat.xen'), 'rb').read()
    index = {struct.unpack_from('>I', dat, 8 + 20 * k)[0]: struct.unpack_from('>I', dat, 12 + 20 * k)[0]
             for k in range(struct.unpack_from('>I', dat, 0)[0])}
    samples = fsb4_samples(bank)
    work = tempfile.mkdtemp(prefix='wormm_')
    clips = []
    with open(bank, 'rb') as f:
        for t in TRACKS:
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
            clips.append((t, frames, n * 1152))
            print(f'{t:28s} {nsamp / freq:7.2f}s  gain {gain:+.1f} dB  mp3 {len(frames) / 1e6:.1f} MB')
    shutil.rmtree(work, ignore_errors=True)

    mod = os.path.join(out, MOD_DIR)
    shutil.rmtree(mod, ignore_errors=True)
    os.makedirs(os.path.join(mod, 'Content'))
    # FSB4: header, 80-byte sample headers (the GH5 mod's layout), data
    shdrs, data = b'', b''
    for t, frames, nsamp in clips:
        name = (t + '.mp3').encode()[:29]
        shdrs += (struct.pack('<H30s', 80, name) +
                  struct.pack('<IIIII', nsamp, len(frames), 0, nsamp - 4, 0x220) +
                  struct.pack('<iHhHH', 48000, 255, 128, 128, 2) + struct.pack('<ff', 1.0, 10000.0) + bytes(8))
        data += frames
    head = struct.pack('<4sIIIII', b'FSB4', len(clips), len(shdrs), len(data), 0x40000, 0) + bytes(24)
    open(os.path.join(mod, 'Content', FSB_NAME + '.fsb.xen'), 'wb').write(head + shdrs + data)
    dat_out = struct.pack('>II', len(clips), qbkey(FSB_NAME)) + b''.join(
        struct.pack('>II', qbkey(t), i) + bytes(12) for i, (t, _, _) in enumerate(clips))
    open(os.path.join(mod, 'Content', FSB_NAME + '.dat.xen'), 'wb').write(dat_out)
    ini = ['[ModInfo]', f'Name={FSB_NAME}', 'Description=Guitar Hero: Warriors of Rock main menu music (from your own copy)',
           'Author=WitchDoctoR', 'Version=1.0', '', '[MenuMusicInfo]', f'FSBName={FSB_NAME}']
    ini += [f'Track={t}' for t, _, _ in clips] + ['']
    for t, _, _ in clips:
        ini += [f'[{t}]', 'Delay=0.0', f'Volume={VOLUME}', 'Offset=0', '']
    open(os.path.join(mod, 'menumusic.ini'), 'w', newline='\r\n').write('\n'.join(ini))
    return mod


if __name__ == '__main__':
    print(build(sys.argv[1]))
