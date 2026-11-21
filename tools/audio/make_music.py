"""Оригинальный саундтрек M1 «Симфоническая сказка».

Лейтмотив Милы (4 ноты): F#4 – A4 – B4 – D5 — проходит через все темы.
Все темы зациклены бесшовно (хвост реверба заворачивается в начало).
"""
import os
import numpy as np
from synth import (Track, SR, CHORDS, celesta, bell, harp, flute, strings, brass,
                   pizz, timpani, xylo, sleighbell, reverb, stereo, finish, mp3, n)

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'audio', 'music')
os.makedirs(OUT, exist_ok=True)


def save(track, name, loop=True, mix=0.3, decay=2.0):
    x = track.buf
    x = reverb(x, decay=decay, mix=mix)
    loop_len = int(track.beats * track.spb * SR) if loop else None
    x = finish(x, loop_len=loop_len)
    mp3(os.path.join(OUT, name), stereo(x))
    dur = (loop_len or len(x)) / SR
    print(f'{name:24s} {dur:5.1f}s  peak={np.max(np.abs(x)):.2f} rms={np.sqrt(np.mean(x**2)):.3f}')


# ------------------------------------------------------------------ ТЕМА 1
def workshop():
    """Пролог: мастерская, часы, тишина перед рывком. 6/8-ощущение, 84 BPM."""
    t = Track(bpm=84, bars=8)
    prog = ['Dmaj7', 'Bm', 'G', 'A', 'Dmaj7', 'Bm', 'G', 'A']
    for i, ch in enumerate(prog, start=1):
        tones = CHORDS[ch]
        t.chord(i, [m + 12 for m in tones], 4, strings, 0.55)
        t.chord(i, [tones[0] - 12], 2, pizz, 0.5)
        # арпеджио челесты восьмыми
        for k in range(8):
            tone = tones[k % len(tones)] + 24
            t.note((i - 1) * 4 + k * 0.5, 0.5, tone, celesta, 0.30 if k % 2 == 0 else 0.20)
    # лейтмотив — редкими фразами
    t.melody([(1, 0, 2, 'D5'), (1, 2, 2, 'F#5'),
              (3, 0, 2, 'A5'), (3, 2, 2, 'B5'),
              (5, 0, 2, 'A5'), (5, 2, 2, 'F#5'),
              (7, 0, 2, 'E5'), (7, 2, 2, 'D5')], celesta, 0.55)
    t.melody([(2, 0, 4, 'A4'), (4, 0, 4, 'F#4'), (6, 0, 4, 'B4'), (8, 0, 4, 'A4')], flute, 0.20)
    save(t, 'theme_workshop.mp3', mix=0.34, decay=2.4)


# ------------------------------------------------------------------ ТЕМА 2
def city():
    """Акт 1: вальс с бубенцами, бег по ночному городу. 3/4, 132 BPM."""
    t = Track(bpm=132, bars=16, beats_per_bar=3)
    prog = ['D', 'D', 'Bm', 'A', 'G', 'D', 'D', 'A',
            'D', 'G', 'Bm', 'A', 'G', 'D', 'D', 'A']
    for i, ch in enumerate(prog, start=1):
        tones = CHORDS[ch]
        b0 = (i - 1) * 3
        t.chord(i, [tones[0] - 12], 1, pizz, 0.85)
        for k in (1, 2):
            t.note(b0 + k, 1, tones[1] + 12, pizz, 0.35)
            t.note(b0 + k, 0.5, tones[2] + 24, sleighbell, 0.16)
        t.chord(i, [tones[0] + 12, tones[1] + 12, tones[2] + 12], 3, strings, 0.22)
    melody = [(1, 0, 1, 'F#4'), (1, 1, 1, 'A4'), (1, 2, 1, 'B4'),
              (2, 0, 3, 'D5'),
              (3, 0, 1, 'B4'), (3, 1, 1, 'A4'), (3, 2, 1, 'F#4'),
              (4, 0, 3, 'A4'),
              (5, 0, 1, 'G4'), (5, 1, 1, 'A4'), (5, 2, 1, 'B4'),
              (6, 0, 3, 'D5'),
              (7, 0, 1, 'F#4'), (7, 1, 1, 'E4'), (7, 2, 1, 'D4'),
              (8, 0, 2, 'E4'), (8, 2, 1, 'F#4'),
              (9, 0, 1, 'F#4'), (9, 1, 1, 'A4'), (9, 2, 1, 'B4'),
              (10, 0, 1, 'D5'), (10, 1, 1, 'E5'), (10, 2, 1, 'D5'),
              (11, 0, 1, 'B4'), (11, 1, 1, 'A4'), (11, 2, 1, 'G4'),
              (12, 0, 3, 'A4'),
              (13, 0, 1, 'D5'), (13, 1, 1, 'B4'), (13, 2, 1, 'A4'),
              (14, 0, 2, 'F#4'), (14, 2, 1, 'E4'),
              (15, 0, 3, 'D4'),
              (16, 0, 2, 'A4'), (16, 2, 1, 'B4')]
    t.melody(melody, celesta, 0.62, bpb=3)
    t.melody([(m[0], m[1], m[2], m[3][:-1] + str(int(m[3][-1]) + 1)) for m in melody], bell,
             0.13, bpb=3)
    save(t, 'theme_city.mp3', mix=0.26, decay=1.8)


# ------------------------------------------------------------------ ТЕМА 3
def forest():
    """Акт 2: зимний лес, арфа и флейта. 4/4, 96 BPM, Bm."""
    t = Track(bpm=96, bars=8)
    prog = ['Bm', 'G', 'D', 'A', 'Bm', 'G', 'A', 'A']
    for i, ch in enumerate(prog, start=1):
        tones = CHORDS[ch]
        b0 = (i - 1) * 4
        t.chord(i, [m + 12 for m in tones], 4, strings, 0.35)
        for k in range(8):
            tone = tones[k % 3] + 24 + (12 if k >= 6 else 0)
            t.note(b0 + k * 0.5, 0.5, tone, harp, 0.26)
        t.chord(i, [tones[0] - 12], 2, pizz, 0.35)
    t.melody([(1, 0, 2, 'F#4'), (1, 2, 1, 'A4'), (1, 3, 1, 'B4'),
              (2, 0, 2, 'D5'), (2, 2, 2, 'B4'),
              (3, 0, 4, 'A4'),
              (4, 0, 4, 'F#4'),
              (5, 0, 2, 'A4'), (5, 2, 2, 'B4'),
              (6, 0, 2, 'D5'), (6, 2, 2, 'E5'),
              (7, 0, 2, 'F#5'), (7, 2, 1, 'E5'), (7, 3, 1, 'D5'),
              (8, 0, 4, 'B4')], flute, 0.55)
    save(t, 'theme_forest.mp3', mix=0.38, decay=2.6)


# ------------------------------------------------------------------ ТЕМА 4
def final():
    """Финал: оркестровая кульминация, 120 BPM, D-dur."""
    t = Track(bpm=120, bars=8)
    prog = ['D', 'G', 'Bm', 'A', 'D', 'G', 'A', 'D']
    for i, ch in enumerate(prog, start=1):
        tones = CHORDS[ch]
        b0 = (i - 1) * 4
        t.chord(i, [m + 12 for m in tones], 4, brass, 0.55)
        t.chord(i, [m + 24 for m in tones], 4, strings, 0.42)
        t.note(b0, 2, tones[0] - 24, timpani, 0.85)
        t.note(b0 + 2, 2, tones[0] - 12, timpani, 0.55)
        for k in range(8):
            t.note(b0 + k * 0.5, 0.5, tones[k % 3] + 36, bell, 0.13)
    mel = [(1, 0, 1, 'D5'), (1, 1, 1, 'F#5'), (1, 2, 1, 'A5'), (1, 3, 1, 'B5'),
           (2, 0, 2, 'A5'), (2, 2, 2, 'F#5'),
           (3, 0, 2, 'B5'), (3, 2, 1, 'A5'), (3, 3, 1, 'G5'),
           (4, 0, 4, 'F#5'),
           (5, 0, 1, 'D5'), (5, 1, 1, 'F#5'), (5, 2, 1, 'A5'), (5, 3, 1, 'B5'),
           (6, 0, 2, 'D6'), (6, 2, 2, 'B5'),
           (7, 0, 2, 'A5'), (7, 2, 2, 'E5'),
           (8, 0, 4, 'D5')]
    t.melody(mel, brass, 0.75)
    t.melody(mel, bell, 0.22)
    t.melody([(m[0], m[1], m[2], m[3][:-1] + str(int(m[3][-1]) + 1)) for m in mel], celesta, 0.16)
    save(t, 'theme_final.mp3', mix=0.28, decay=2.2)


# ------------------------------------------------------------------ ТЕМА 5
def defeat():
    """Проигрыш: та же тема в миноре, музыкальная шкатулка. 64 BPM."""
    t = Track(bpm=64, bars=6)
    prog = ['Bm', 'G', 'D', 'A', 'Bm', 'Bm']
    for i, ch in enumerate(prog, start=1):
        tones = CHORDS[ch]
        t.chord(i, [m + 12 for m in tones], 4, strings, 0.30)
        for k in range(4):
            t.note((i - 1) * 4 + k, 1, tones[k % 3] + 24, celesta, 0.16)
    t.melody([(1, 0, 2, 'B4'), (1, 2, 2, 'D5'),
              (2, 0, 4, 'F#5'),
              (3, 0, 2, 'E5'), (3, 2, 2, 'D5'),
              (4, 0, 4, 'B4'),
              (5, 0, 2, 'F#4'), (5, 2, 2, 'A4'),
              (6, 0, 4, 'B4')], celesta, 0.62)
    save(t, 'theme_defeat.mp3', mix=0.5, decay=3.2)


# ------------------------------------------------------------------ ТЕМА 6
def storm():
    """Акт 3: метель-босс. 140 BPM, тревожно, тремоло струнных."""
    t = Track(bpm=140, bars=8)
    prog = ['Bm', 'Bm', 'G', 'G', 'Em', 'Em', 'F#', 'F#']
    for i, ch in enumerate(prog, start=1):
        tones = CHORDS[ch]
        b0 = (i - 1) * 4
        for k in range(16):  # тремоло
            t.note(b0 + k * 0.25, 0.25, tones[k % 3] + 12, strings, 0.16)
        t.note(b0, 2, tones[0] - 24, timpani, 0.85)
        t.note(b0 + 2.5, 1, tones[0] - 12, pizz, 0.5)
        if i % 2 == 0:
            t.chord(i, [m + 12 for m in tones], 2, brass, 0.5)
    t.melody([(1, 0, 1, 'B4'), (1, 1, 1, 'C5'), (1, 2, 2, 'B4'),
              (2, 0, 2, 'F#4'), (2, 2, 2, 'D4'),
              (3, 0, 1, 'G4'), (3, 1, 1, 'A4'), (3, 2, 2, 'B4'),
              (4, 0, 4, 'D5'),
              (5, 0, 2, 'E5'), (5, 2, 2, 'D5'),
              (6, 0, 2, 'C5'), (6, 2, 2, 'B4'),
              (7, 0, 4, 'F#4'),
              (8, 0, 2, 'B4'), (8, 2, 1, 'C5'), (8, 3, 1, 'B4')], brass, 0.65)
    save(t, 'theme_storm.mp3', mix=0.24, decay=1.6)


# ------------------------------------------------------------------ ДЖИНГЛ
def jingle():
    """Фанфара «2027» на финал."""
    t = Track(bpm=126, bars=3)
    seq = [(0, 'D5'), (0.5, 'F#5'), (1, 'A5'), (1.5, 'D6')]
    for i in range(3):
        for beat, pitch in seq:
            t.note(i * 4 + beat, 1.0, n(pitch) + (12 if i == 2 else 0), bell, 0.45)
            t.note(i * 4 + beat, 1.0, n(pitch), celesta, 0.3)
    for bar, ch in [(1, 'D'), (2, 'G'), (3, 'D')]:
        tones = CHORDS[ch]
        t.chord(bar, [m + 12 for m in tones], 4, brass, 0.5)
        t.chord(bar, [m + 24 for m in tones], 4, strings, 0.35)
        t.note((bar - 1) * 4, 2, tones[0] - 24, timpani, 0.9)
    save(t, 'jingle_2027.mp3', loop=False, mix=0.3, decay=2.0)


if __name__ == '__main__':
    workshop()
    city()
    forest()
    final()
    defeat()
    storm()
    jingle()
