"""Мини-синтезатор для оригинального саундтрека проекта «Последняя посылка».

Всё генерируется с нуля (никаких чужих сэмплов): осцилляторы, огибающие,
FFT-фильтры, свёрточный ревер. Выход — WAV/MP3 44.1 кГц.
"""
import numpy as np

SR = 44100
RNG = np.random.default_rng(2027)

NOTES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6,
         'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def n(name):
    """'F#4' -> midi-номер."""
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + NOTES[pitch]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


# ---------------------------------------------------------------- фильтры
def lp(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1.0 / np.sqrt(1.0 + (f / max(fc, 1)) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def hp(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = 1.0 - 1.0 / np.sqrt(1.0 + (f / max(fc, 1)) ** (2 * order))
    return np.fft.irfft(X * H, len(x))


def bp(x, lo, hi):
    return lp(hp(x, lo), hi)


# ------------------------------------------------------------- инструменты
def _env(n_s, a, d, s, r, sus=0.7):
    """ADSR-огибающая длиной n_s сэмплов."""
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    a_n = max(a_n, 1)
    s_n = max(n_s - a_n - d_n - r_n, 1)
    env = np.concatenate([
        np.linspace(0, 1, a_n, endpoint=False),
        np.linspace(1, sus, d_n, endpoint=False),
        np.full(s_n, sus),
        np.linspace(sus, 0, r_n),
    ])
    return env[:n_s] if len(env) >= n_s else np.pad(env, (0, n_s - len(env)))


def bell(f, dur, vel=1.0, ring=3.2, bright=1.0):
    """Челеста / колокольчик: негармонические партиалы."""
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    parts = [(1.0, 1.0, 1.0), (2.01, 0.42, 1.7), (3.0, 0.20 * bright, 2.4),
             (4.07, 0.10 * bright, 3.2), (5.43, 0.05 * bright, 4.4)]
    s = np.zeros(ns)
    for ratio, amp, dec in parts:
        s += amp * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-ring * dec * tt)
    s *= np.minimum(1, tt / 0.003)
    return s * vel


def harp(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = np.zeros(ns)
    for i, (ratio, amp, dec) in enumerate([(1, 1, 2.2), (2, .35, 3.4), (3, .16, 5), (4, .07, 7)]):
        s += amp * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-dec * tt)
    s += 0.25 * lp(RNG.standard_normal(ns), 4000) * np.exp(-40 * tt)
    s *= np.minimum(1, tt / 0.002)
    return s * vel


def celesta(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt) * np.exp(-6 * tt)
         + 0.08 * np.sin(6 * np.pi * f * tt) * np.exp(-9 * tt))
    s *= np.exp(-2.6 * tt) * np.minimum(1, tt / 0.002)
    return s * vel


def flute(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    vib = 0.005 * np.sin(2 * np.pi * 5.1 * tt)
    ph = 2 * np.pi * f * (tt + vib * tt)
    s = np.sin(ph) + 0.16 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    breath = lp(RNG.standard_normal(ns), 2600) * 0.035
    env = np.minimum(1, tt / 0.07) * np.minimum(1, (dur - tt) / 0.12)
    return (s + breath) * np.clip(env, 0, 1) * vel


def strings(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = np.zeros(ns)
    for det in (-0.006, 0.0, 0.007):
        s += 2 * ((tt * f * (1 + det)) % 1.0) - 1.0
    s = lp(s / 3.0, 2100, 2)
    s = s + 0.3 * np.sin(2 * np.pi * f * tt)
    return s * _env(ns, 0.55, 0.25, 0, 0.5, 0.85) * vel * 0.5


def brass(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = np.zeros(ns)
    for det in (-0.004, 0.005):
        s += 2 * ((tt * f * (1 + det)) % 1.0) - 1.0
    s = lp(s / 2.0, 1500 + 2500 * min(dur, 0.4), 3) + 0.5 * np.sin(2 * np.pi * f * tt)
    return s * _env(ns, 0.09, 0.15, 0, 0.2, 0.8) * vel * 0.45


def pizz(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = (2 * ((tt * f) % 1.0) - 1.0) + 0.5 * np.sin(2 * np.pi * f * tt)
    s = lp(s, 900, 2) * np.exp(-7 * tt) * np.minimum(1, tt / 0.004)
    return s * vel * 0.8


def timpani(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    glide = f * (1 + 0.35 * np.exp(-28 * tt))
    s = np.sin(2 * np.pi * np.cumsum(glide) / SR) * np.exp(-3.2 * tt)
    s += 0.5 * lp(RNG.standard_normal(ns), 700) * np.exp(-30 * tt)
    return s * vel * 0.9


def xylo(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 3 * f * tt)
         + 0.15 * np.sin(2 * np.pi * 6.2 * f * tt)) * np.exp(-14 * tt)
    return s * vel * 0.6


def sleighbell(f, dur, vel=1.0):
    ns = int(dur * SR)
    tt = np.arange(ns) / SR
    s = np.zeros(ns)
    for ratio in (1, 2.4, 3.7, 5.1, 6.8):
        s += RNG.uniform(0.3, 1.0) * np.sin(2 * np.pi * f * ratio * tt) * np.exp(-16 * tt)
    s += 0.4 * hp(RNG.standard_normal(ns), 6000) * np.exp(-45 * tt)
    return s * vel * 0.5


# ------------------------------------------------------------------- микс
class Track:
    def __init__(self, bpm, bars, beats_per_bar=4):
        self.bpm = bpm
        self.spb = 60.0 / bpm
        self.beats = bars * beats_per_bar
        self.length = int(self.beats * self.spb * SR) + SR // 4
        self.buf = np.zeros(self.length)

    def add(self, sig, start_beat, gain=1.0):
        i = int(start_beat * self.spb * SR)
        j = min(i + len(sig), len(self.buf))
        if i < len(self.buf) and j > i:
            self.buf[i:j] += sig[:j - i] * gain

    def note(self, beat, dur_beats, midi, inst, gain=1.0):
        dur = dur_beats * self.spb * 1.25
        if inst in (celesta, bell, harp, xylo, sleighbell, pizz, timpani):
            sig = inst(hz(midi), max(dur, 0.12), 1.0)
        else:
            sig = inst(hz(midi), max(dur, 0.12), 1.0)
        self.add(sig, beat, gain)

    def melody(self, notes, inst, gain=1.0, bpb=4):
        """notes: [(bar, beat, dur, 'D5'), ...] — bar с 1."""
        for bar, beat, dur, pitch in notes:
            self.note((bar - 1) * bpb + beat, dur, n(pitch), inst, gain)

    def chord(self, bar, midis, dur, inst, gain=1.0, bpb=4):
        for m in midis:
            self.note((bar - 1) * bpb, dur, m, inst, gain)


CHORDS = {
    'D': [50, 54, 57], 'Dmaj7': [50, 54, 57, 61], 'A': [45, 49, 52], 'Bm': [47, 50, 54],
    'G': [43, 47, 50], 'Em': [40, 43, 47], 'F#m': [42, 46, 49], 'E': [40, 44, 47],
    'B': [47, 51, 54], 'F#': [42, 46, 49],
}


def reverb(x, decay=2.2, mix=0.28, predelay=0.02, bright=4500):
    """Свёрточный ревер с синтетическим импульсом (стерео)."""
    ir_n = int(decay * SR)
    tt = np.arange(ir_n) / SR
    ir = RNG.standard_normal(ir_n) * np.exp(-4.5 * tt / decay)
    ir = lp(ir, bright)
    ir[:int(predelay * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    n_fft = 1 << int(np.ceil(np.log2(len(x) + ir_n)))
    wet = np.fft.irfft(np.fft.rfft(x, n_fft) * np.fft.rfft(ir, n_fft), n_fft)[:len(x)]
    return (1 - mix) * x + mix * wet


def stereo(x, width=0.9):
    """Псевдостерео: небольшая задержка + разная панорама."""
    d = int(0.006 * SR)
    left = np.concatenate([x, np.zeros(d)])[:len(x)]
    right = np.concatenate([np.zeros(d), x])[:len(x)]
    return np.stack([left * (1 + 0.1 * width), right * (1 - 0.1 * width)], axis=1)


def finish(x, loop_len=None, peak=0.9, drive=1.15):
    """Ревер, мягкий лимитер, нормализация. loop_len — длина цикла в сэмплах (шов без щелчка)."""
    x = x / (np.max(np.abs(x)) + 1e-9)
    x = np.tanh(x * drive) / np.tanh(drive)
    if loop_len:
        tail = x[loop_len:]
        y = x[:loop_len].copy()
        k = min(len(tail), len(y))
        y[:k] += tail[:k]
        x = y
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    return x


def mp3(path, stereo_float, bitrate=128):
    """Сохранить стерео float [-1..1] в mp3 (lameenc) или wav, если его нет."""
    import lameenc
    data = (np.clip(stereo_float, -1, 1) * 32767).astype(np.int16)
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    enc = lameenc.Encoder()
    enc.set_bit_rate(bitrate)
    enc.set_in_sample_rate(SR)
    enc.set_channels(2)
    enc.set_quality(2)
    out = enc.encode(data.tobytes())
    out += enc.flush()
    with open(path, 'wb') as f:
        f.write(bytes(out))


def wav(path, stereo_float):
    import wave
    data = (np.clip(stereo_float, -1, 1) * 32767).astype(np.int16)
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
