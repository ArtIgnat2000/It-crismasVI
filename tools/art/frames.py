# -*- coding: utf-8 -*-
"""Настоящие кадры сцены — композиционный аудит проекта.

Как это работает:
  1. tools/run_vm.js в режиме `frames` прогоняет .sb3 в настоящей scratch-vm и
     записывает состояние сцены в ключевые моменты (позиции, костюмы, размеры,
     повороты, призрачность) — dist/frames.json;
  2. этот скрипт собирает из них картинки РОВНО теми ассетами, что лежат в .sb3,
     и печатает отчёт о наложениях (кто на кого наехал, что залезло в HUD
     или в нижнюю плашку субтитров).

Запуск:
    cd tools && node run_vm.js ../dist/Poslednyaya_posylka.sb3 frames ../dist/frames.json
    cd .. && PYTHONPATH=tools/vendor python3 tools/art/frames.py
"""
import json
import os
import sys
import zipfile

from PIL import Image

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = f'{R}/art/mock/frames'
W, H = 960, 720                      # рендер 2x от сцены 480x360
SB3 = f'{R}/dist/Poslednyaya_posylka.sb3'
# Optional: pass the frames JSON as argv[1] to audit a different set (e.g.
# frames_tw.json produced by the TurboWarp VM).
FRAMES = sys.argv[1] if len(sys.argv) > 1 else f'{R}/dist/frames.json'

# Порядок слоёв «как задумано» (в sb3 порядок задаётся блоками «перейти на передний/
# задний план», здесь он зафиксирован явно — так отчёт воспроизводим).
Z = {
    'Снег': 4,
    'Ёлка': 6, 'Сугроб': 8, 'Звезда': 9, 'Снежок': 12,
    'Сани': 14, 'ДедМороз': 15, 'Мила': 16, 'Сова': 16, 'Снеговик': 17,
    'Подарок': 18, 'Метель': 20,
    'Часы_циферблат': 40, 'Часы_стрелка': 41, 'Жизни': 42, 'Счёт': 43,
    'Обратный отсчёт': 43, 'КнопкаЗвук': 44,
    'Экран': 50, 'Подпись': 51, 'Плашка': 52, '2027': 53, 'Фейерверк': 54,
    'Кнопка': 55, 'Затемнение': 90,
}
TEXT_UI = ['Экран', 'Подпись', 'Плашка', '2027', 'Кнопка', 'Жизни', 'Счёт',
           'Часы_циферблат', 'КнопкаЗвук', 'Обратный отсчёт']
ACTORS = ['Мила', 'ДедМороз', 'Снеговик', 'Метель', 'Сова', 'Сани', 'Подарок',
          'Сугроб', 'Ёлка', 'Звезда']
CAPTION_BAND_TOP = -132              # верх нижней плашки (y <= -132 — «не для актёров»)


class Assets:
    """Ассеты берём напрямую из project.json .sb3 — по имени спрайта и костюма."""

    def __init__(self, path):
        self.zip = zipfile.ZipFile(path)
        pj = json.loads(self.zip.read('project.json').decode('utf-8'))
        self.by_name = {}
        for t in pj['targets']:
            for c in t.get('costumes', []):
                self.by_name[(t['name'], c['name'])] = {
                    'id': c['assetId'], 'fmt': c['dataFormat'],
                    'res': c.get('bitmapResolution', 1) or 1,
                    'w': c.get('width'), 'h': c.get('height'),
                    'rcX': c.get('rotationCenterX'), 'rcY': c.get('rotationCenterY'),
                }
        self.cache = {}

    def asset_of(self, target, costume):
        return self.by_name.get((target, costume))

    def image(self, md5, fmt):
        key = md5 if '.' in md5 else f'{md5}.{fmt}'
        if key not in self.cache:
            with self.zip.open(key) as f:
                im = Image.open(f)
                im.load()
                self.cache[key] = im.convert('RGBA')
        return self.cache[key]


def placed(t, im, meta):
    """Куда и какого размера ляжет костюм: возвращает (картинка 2x, left, top)."""
    res = max(meta.get('res') or 1, 1)
    k = (t['size'] / 100.0) / res * 2                   # px костюма -> px кадра (2x)
    w, h = im.width * k, im.height * k
    img = im.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS) \
        if (im.width, im.height) != (round(w), round(h)) else im

    flip = False
    if t.get('rot') == 'left-right':
        flip = t['dir'] < 0
    angle = 0
    if t.get('rot') not in ('left-right',) and abs(t['dir'] - 90) > 0.5:
        angle = 90 - t['dir']                              # Scratch: 90 = вправо
    if flip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if angle:
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True)

    # точка вращения костюма -> экранные px (2x)
    rcx = float(meta.get('rcX') or im.width / 2) * k
    rcy = float(meta.get('rcY') or im.height / 2) * k
    px = (t['x'] + 240) * 2
    py = (180 - t['y']) * 2
    left = px - rcx
    top = py - rcy
    return img, left, top


def alpha(im, ghost):
    if ghost <= 0:
        return im
    a = im.getchannel('A').point(lambda v: int(v * max(0.0, 1 - ghost / 100.0)))
    out = im.copy()
    out.putalpha(a)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    assets = Assets(SB3)
    data = json.load(open(FRAMES, encoding='utf-8'))
    problems = []

    for sh in data['shots']:
        targets = [t for t in sh['targets']]
        # фон всегда первым, дальше — по задуманному порядку слоёв
        targets.sort(key=lambda t: (0 if t['name'] == 'Stage' else Z.get(t['name'], 30), t['layer']))

        canvas = Image.new('RGBA', (W, H), (6, 10, 24, 255))
        boxes = []
        for t in targets:
            asset = assets.asset_of(t['name'], t['costume'])
            if not asset:
                problems.append(f"{sh['label']}: нет ассета для «{t['name']}/{t['costume']}»")
                continue
            im = assets.image(asset['id'], asset['fmt'])
            if t['name'] == 'Stage':
                canvas.alpha_composite(im.resize((W, H), Image.LANCZOS), (0, 0))
                continue

            img, left, top = placed(t, im, asset)
            img = alpha(img, t['ghost'])
            if t['ghost'] >= 99:
                bb = None
            else:
                bb = img.getbbox()
            canvas.alpha_composite(img, (int(left), int(top)))
            if bb:
                boxes.append({'name': t['name'], 'box': (int(left) + bb[0], int(top) + bb[1],
                                                         int(left) + bb[2], int(top) + bb[3]),
                              'x': t['x'], 'y': t['y'], 'size': t['size']})

        # ---------- отчёт о наложениях
        def unit(v):
            return round(v / 2 - 240, 1) if False else v

        ui = [b for b in boxes if b['name'] in TEXT_UI]
        for i, a in enumerate(ui):
            for b in ui[i + 1:]:
                if overlap(a['box'], b['box']):
                    problems.append(f"{sh['label']}: текст «{a['name']}» наезжает на «{b['name']}»")
        plate = next((b for b in boxes if b['name'] == 'Плашка'), None)
        if plate:
            for b in boxes:
                if b['name'] in ACTORS and overlap(b['box'], plate['box']):
                    problems.append(f"{sh['label']}: «{b['name']}» залез на плашку субтитров")
        # HUD: ничего из актёров не должно перекрывать строку жизней/счёта/часов
        hud = [b for b in boxes if b['name'] in ('Жизни', 'Счёт', 'Часы_циферблат')]
        for b in boxes:
            if b['name'] in ACTORS and b['box'][1] < 40:      # выше y=160 (в 2x: top<40)
                problems.append(f"{sh['label']}: «{b['name']}» влез в верхнюю полосу HUD")

        name = f"{sh['label']}"
        canvas.convert('RGB').save(f'{OUT}/{name}.jpg', quality=92)

    # ---------- контактный лист
    names = [s['label'] for s in data['shots']]
    cols = 3
    rows = (len(names) + cols - 1) // cols
    tw, th = 620, 465
    sheet = Image.new('RGB', (tw * cols + 12 * (cols + 1), th * rows + 12 * (rows + 1)),
                      (8, 12, 24))
    for i, n in enumerate(names):
        im = Image.open(f'{OUT}/{n}.jpg').resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 12)))
    sheet.save(f'{R}/art/mock/_все_кадры.jpg', quality=88)

    print(f'кадров: {len(names)} -> {OUT}')
    if problems:
        print('НАЛОЖЕНИЯ:')
        for p in problems:
            print('  !', p)
    else:
        print('НАЛОЖЕНИЙ НЕТ: текст, HUD и актёры разведены по своим зонам')


def overlap(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


if __name__ == '__main__':
    main()
