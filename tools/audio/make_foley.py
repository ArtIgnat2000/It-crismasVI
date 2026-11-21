"""Фоли-эффекты проекта (всё синтезируется, ничего не скачивается)."""
import os
import numpy as np
from synth import (SR, RNG, lp, hp, bp, bell, celesta, timpani, xylo, mp3, stereo, finish, hz, n)

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'audio', 'foley')
os.makedirs(OUT, exist_ok=True)


def add_at(buf, sig, j):
    """Добавить сигнал в буфер с обрезкой по границе."""
    j = max(0, int(j))
    k = min(len(buf) - j, len(sig))
    if k > 0:
        buf[j:j + k] += sig[:k]


def noise(dur):
    return RNG.standard_normal(int(dur * SR))


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def save(name, x, loop=False, gain=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * gain
    if loop:
        # бесшовная петля: короткий кроссфейд
        f = int(0.08 * SR)
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    mp3(os.path.join(OUT, name), stereo(x), bitrate=112)
    print(f'{name:22s} {len(x)/SR:4.2f}s')


# --- шаги/прыжки
def step_snow():
    d = 0.09
    x = noise(d) * np.exp(-45 * tt(d))
    x = bp(x, 500, 4200)
    crunch = noise(d) * (np.abs(np.sin(2 * np.pi * 90 * tt(d))) > 0.7) * np.exp(-22 * tt(d))
    save('sfx_step.mp3', x * 0.8 + bp(crunch, 900, 6000) * 0.5)


def jump():
    d = 0.22
    t = tt(d)
    f = 330 * np.exp(-2.2 * t) + 520
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-9 * t)
    x += 0.2 * hp(noise(d), 2500) * np.exp(-25 * t)
    save('sfx_jump.mp3', x)


def land():
    d = 0.25
    t = tt(d)
    x = np.sin(2 * np.pi * 90 * np.exp(-6 * t) * t) * np.exp(-14 * t)
    x += 0.35 * lp(noise(d), 800) * np.exp(-30 * t)
    save('sfx_land.mp3', x)


# --- игровые события
def pickup():
    x = np.zeros(int(0.45 * SR))
    for i, m in enumerate(['D6', 'F#6', 'A6']):
        s = bell(hz(n(m)), 0.35, 1.0)
        j = int(i * 0.055 * SR)
        add_at(x, s * 0.55, j)
    save('sfx_pickup.mp3', x)


def hit():
    d = 0.4
    t = tt(d)
    x = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-5 * t)) / SR) * np.exp(-9 * t)
    x += 0.6 * lp(noise(d), 1200) * np.exp(-22 * t)
    save('sfx_hit.mp3', x, gain=0.85)


def swoosh():
    d = 0.7
    t = tt(d)
    x = noise(d) * (0.3 + 0.7 * np.sin(np.pi * t / d))
    x = bp(x, 300, 3500)
    x *= np.exp(-3 * t)
    save('sfx_swoosh.mp3', x, gain=0.7)


def wind_loop():
    d = 4.0
    t = tt(d)
    x = noise(d)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.35 * t + 1.0) * np.sin(2 * np.pi * 0.11 * t)
    x = bp(x * lfo, 220, 1400)
    x += 0.3 * bp(noise(d), 1800, 5200) * (0.4 + 0.6 * np.sin(2 * np.pi * 0.7 * t) ** 2) * 0.3
    save('sfx_wind.mp3', x, loop=True, gain=0.6)


def tick():
    d = 0.07
    x = hp(noise(d), 3500) * np.exp(-90 * tt(d)) + 0.5 * np.sin(2 * np.pi * 2200 * tt(d)) * np.exp(-70 * tt(d))
    save('sfx_tick.mp3', x, gain=0.5)


def clock_chime():
    x = np.zeros(int(3.2 * SR))
    for i, m in enumerate(['D3', 'A3', 'D4']):
        s = bell(hz(n(m)), 2.6, 1.0, ring=1.2, bright=0.6)
        j = int(i * 0.75 * SR)
        add_at(x, s * 0.6, j)
    x += 0.2 * lp(noise(3.2), 300) * np.exp(-1.5 * tt(3.2))
    save('sfx_chime.mp3', x, gain=0.9)


def firework():
    d = 1.6
    t = tt(d)
    boom = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-3 * t)) / SR) * np.exp(-6 * t)
    crackle = hp(noise(d), 4000) * (RNG.random(len(t)) > 0.985).astype(float) * np.exp(-2.5 * t)
    crackle = np.convolve(crackle, np.ones(60) / 60, mode='same')
    save('sfx_firework.mp3', boom * 0.9 + crackle * 2.0, gain=0.85)


def magic():
    d = 1.0
    x = np.zeros(int(d * SR))
    for i in range(10):
        m = n('D5') + int(i * 2)
        s = bell(hz(m), 0.5, 1.0)
        j = int(i * 0.06 * SR)
        add_at(x, s * 0.3, j)
    save('sfx_magic.mp3', x)


def owl():
    d = 0.9
    t = tt(d)
    f = 380 + 40 * np.sin(2 * np.pi * 6 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-3.5 * t) * (np.sin(np.pi * t / d) ** 0.7)
    save('sfx_owl.mp3', x, gain=0.45)


def pop():
    d = 0.18
    t = tt(d)
    x = np.sin(2 * np.pi * np.cumsum(600 * np.exp(-9 * t)) / SR) * np.exp(-18 * t)
    save('sfx_pop.mp3', x, gain=0.55)


def sleigh_bells():
    d = 1.2
    x = np.zeros(int(d * SR))
    for i in range(14):
        m = n('A6') + int(RNG.integers(-2, 3))
        s = bell(hz(m), 0.25, 1.0, ring=6)
        j = int(i * 0.08 * SR + RNG.uniform(0, 0.02) * SR)
        add_at(x, s * RNG.uniform(0.15, 0.35), j)
    save('sfx_bells.mp3', x, gain=0.6)


def transition():
    d = 0.5
    t = tt(d)
    x = bp(noise(d), 200, 6000) * np.exp(-5 * t)
    x += 0.4 * np.sin(2 * np.pi * np.cumsum(1400 * np.exp(-7 * t)) / SR) * np.exp(-9 * t)
    save('sfx_whoosh.mp3', x, gain=0.55)


def click():
    d = 0.09
    x = hp(noise(d), 2000) * np.exp(-70 * tt(d))
    add_at(x, 0.4 * xylo(hz(n('C6')), 0.06, 1.0), 0)
    save('sfx_click.mp3', x, gain=0.4)


def snowball_hit():
    d = 0.35
    t = tt(d)
    x = lp(noise(d), 2500) * np.exp(-16 * t) + 0.5 * np.sin(2 * np.pi * 140 * t) * np.exp(-20 * t)
    save('sfx_snowball.mp3', x, gain=0.7)


if __name__ == '__main__':
    for f in (step_snow, jump, land, pickup, hit, swoosh, wind_loop, tick, clock_chime,
              firework, magic, owl, pop, sleigh_bells, transition, click, snowball_hit):
        f()
