# -*- coding: utf-8 -*-
"""Круглый снежок для снарядов Метели.

Арт сугроба — широкий и низкий, а летящий снаряд должен быть круглым
(и не «плюхаться» при повороте). Поэтому берём центральный квадрат
сугроба и вырезаем по кругу.

Запуск: PYTHONPATH=tools/vendor python3 tools/art/snowball.py
Результат: art/sprites/snowball.png (прозрачный фон, 320x320)
"""
import os

import numpy as np
from PIL import Image, ImageFilter

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(R, 'art', 'sprites', 'snowdrift.png')
OUT = os.path.join(R, 'art', 'sprites', 'snowball.png')
SIZE = 320


def main():
    im = Image.open(SRC).convert('RGBA')
    bbox = im.getbbox() or (0, 0, im.width, im.height)
    im = im.crop(bbox)
    side = min(im.size)
    left = (im.width - side) // 2
    top = (im.height - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.LANCZOS)

    # круговая маска с мягким краем — снежок остаётся пушистым, но круглым
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    cx = cy = (SIZE - 1) / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (SIZE * 0.46)
    mask = np.clip((1.0 - r) / 0.18, 0.0, 1.0)

    src = np.asarray(im).astype(np.float32) / 255.0
    alpha = src[..., 3] * mask
    # лёгкое затемнение к краю — объём, иначе круг выглядит плоским
    shade = 1.0 - 0.22 * np.clip(r, 0, 1) ** 2
    rgb = np.clip(src[..., :3] * shade[..., None], 0, 1)
    out = np.dstack([rgb, alpha])
    img = Image.fromarray((out * 255).astype(np.uint8), 'RGBA')
    img.putalpha(img.getchannel('A').filter(ImageFilter.GaussianBlur(0.6)))
    img.save(OUT)
    print(f'снежок: {OUT} {img.size}, {os.path.getsize(OUT) // 1024} КБ')


if __name__ == '__main__':
    main()
