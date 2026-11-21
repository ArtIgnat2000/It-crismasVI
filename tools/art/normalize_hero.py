# -*- coding: utf-8 -*-
"""Выравнивание костюмов героини (Мила) на общее полотно.

Зачем: костюмы нарисованы ИИ по отдельности и получились разного размера
(265x420, 419x331, 353x420, 276x420). В Scratch точка вращения — центр
костюма, поэтому при смене «бежит → прыгает» героиня визуально прыгала бы
вверх-вниз и дёргалась по ширине.

Что делаем: масштаб НЕ меняем (герой остаётся одного физического размера),
но каждый костюм кладём на общее прозрачное полотно 440x440 так, чтобы:
  * альфа-обрезка костюма была по центру по горизонтали;
  * низ обрезки стоял на общей линии (ноги/живот на одном уровне).

Запуск:  PYTHONPATH=tools/vendor python3 tools/art/normalize_hero.py
Оригиналы сохраняются в art/raw/goat_<костюм>_orig.png (один раз).
"""
import os
import shutil

from PIL import Image

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SPRITES = os.path.join(R, 'art', 'sprites')
RAW = os.path.join(R, 'art', 'raw')

CANVAS = 440          # сторона общего полотна
BASELINE = 425        # линия «низа» персонажа на полотне


def normalize(path):
    im = Image.open(path).convert('RGBA')
    bbox = im.getbbox()
    if not bbox:
        raise SystemExit(f'пустая картинка: {path}')
    body = im.crop(bbox)
    if body.width > CANVAS or body.height > CANVAS:
        k = min(CANVAS / body.width, BASELINE / body.height)
        body = body.resize((max(1, round(body.width * k)), max(1, round(body.height * k))),
                           Image.LANCZOS)
    canvas = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    x = (CANVAS - body.width) // 2
    y = BASELINE - body.height
    canvas.paste(body, (x, max(0, y)), body)
    canvas.save(path)
    return im.size, canvas.size, body.size


def main():
    os.makedirs(RAW, exist_ok=True)
    for name in ('idle', 'run', 'jump', 'cheer'):
        path = os.path.join(SPRITES, f'goat_{name}.png')
        backup = os.path.join(RAW, f'goat_{name}_orig.png')
        if not os.path.exists(backup):
            shutil.copy2(path, backup)
        was, now, body = normalize(path)
        print(f'goat_{name}: было {was} -> полотно {now}, персонаж {body}')


if __name__ == '__main__':
    main()
