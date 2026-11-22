"""Процедурные ассеты: титры, кнопки, HUD, часы и заглушки вместо ещё не сгенерированных спрайтов.

Титры рисуются шрифтом DejaVu (поддерживает кириллицу) с тёмной обводкой —
это даёт «киношный» вид и не требует текста внутри AI-картинок.
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
UI = os.path.join(ROOT, 'art', 'ui')
SPR = os.path.join(ROOT, 'art', 'sprites')
os.makedirs(UI, exist_ok=True)

GOLD = (255, 201, 107)
CREAM = (245, 241, 230)
NAVY = (11, 27, 51)
RED = (192, 57, 43)
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


def text_img(text, size, color=GOLD, stroke=6, pad=24, shadow=True):
    f = font(size)
    tmp = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    box = tmp.textbbox((0, 0), text, font=f, stroke_width=stroke)
    w, h = box[2] - box[0] + pad * 2, box[3] - box[1] + pad * 2
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = pad - box[0], pad - box[1]
    if shadow:
        d.text((ox + 5, oy + 6), text, font=f, fill=(4, 8, 18, 170), stroke_width=stroke,
               stroke_fill=(4, 8, 18, 170))
    d.text((ox, oy), text, font=f, fill=color, stroke_width=stroke, stroke_fill=NAVY)
    return im


def rounded(size, radius, fill, outline=None, width=4):
    im = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([width // 2, width // 2, size[0] - width // 2, size[1] - width // 2],
                        radius=radius, fill=fill, outline=outline, width=width)
    return im


def star_polygon(cx, cy, r_out, r_in, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def heart(d, cx, cy, s, fill):
    d.ellipse([cx - s, cy - s * 0.9, cx, cy + s * 0.1], fill=fill)
    d.ellipse([cx, cy - s * 0.9, cx + s, cy + s * 0.1], fill=fill)
    d.polygon([(cx - s, cy - s * 0.15), (cx + s, cy - s * 0.15), (cx, cy + s * 1.05)], fill=fill)


# ------------------------------------------------------------------ титры/кнопки
def titles():
    # ВАЖНО: строки не должны наезжать друг на друга — подпись идёт с чистым зазором
    t = text_img('ПОСЛЕДНЯЯ', 96)
    t2 = text_img('ПОСЫЛКА', 108)
    sub = text_img('Scratch 3.0 · версия 1.9', 30, color=CREAM, stroke=4)
    gap = 14
    w = max(t.width, t2.width, sub.width) + 40
    h = t.height + t2.height + sub.height + gap * 2
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.alpha_composite(t, ((w - t.width) // 2, 0))
    im.alpha_composite(t2, ((w - t2.width) // 2, t.height - 6))
    im.alpha_composite(sub, ((w - sub.width) // 2, t.height + t2.height - 6 + gap))
    im.save(f'{UI}/title.png')

    text_img('С НОВЫМ 2027 ГОДОМ!', 84).save(f'{UI}/win.png')
    text_img('ПОЛНОЧЬ...', 88, color=(200, 220, 240)).save(f'{UI}/lose.png')
    text_img('Метель победила. Но ты можешь ещё раз!', 34, color=CREAM).save(f'{UI}/lose_sub.png')
    text_img('← →  бег      ПРОБЕЛ  прыжок', 36, color=CREAM, stroke=5).save(f'{UI}/hint.png')
    text_img('2027', 210, color=GOLD, stroke=10).save(f'{UI}/s2027.png')
    text_img('Козочка Мила — символ года', 30, color=CREAM, stroke=4).save(f'{UI}/s2027_sub.png')


def buttons():
    for name, label, fill in [('btn_retry', 'ЕЩЁ РАЗ', (192, 57, 43, 255)),
                              ('btn_sound_on', 'ЗВУК: ВКЛ', (30, 58, 95, 255)),
                              ('btn_sound_off', 'ЗВУК: ВЫКЛ', (40, 46, 60, 255))]:
        w, h = (300, 90) if name == 'btn_retry' else (230, 60)
        base = rounded((w, h), 28, fill, outline=(255, 201, 107, 255), width=5)
        lab = text_img(label, 40 if name == 'btn_retry' else 26, color=CREAM, stroke=4, pad=8)
        base.alpha_composite(lab, ((w - lab.width) // 2, (h - lab.height) // 2))
        base.save(f'{UI}/{name}.png')


# ----------------------------------------------------------------------- HUD
def hud():
    for n in range(4):
        im = Image.new('RGBA', (300, 100), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(3):
            cx = 55 + i * 95
            if i < n:
                heart(d, cx, 50, 34, (214, 69, 65, 255))
                heart(d, cx - 3, 47, 30, (255, 120, 110, 255))
            else:
                heart(d, cx, 50, 34, (70, 84, 110, 255))
        im.save(f'{UI}/lives_{n}.png')

    for n in range(14):
        im = Image.new('RGBA', (260, 100), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.polygon(star_polygon(60, 50, 44, 19), fill=GOLD, outline=NAVY)
        f = font(62)
        d.text((118, 50), str(n), font=f, fill=CREAM, anchor='lm', stroke_width=5, stroke_fill=NAVY)
        im.save(f'{UI}/stars_{n}.png')


# --------------------------------------------------- нижняя плашка (субтитры/подсказки)
# Одна геометрия на все тексты снизу: 960x76 px = 480x38 единиц сцены (2x рендер).
# Благодаря этому субтитр и подсказка физически не могут наехать друг на друга —
# это один и тот же спрайт «Плашка» в одной и той же точке.
CAP_W, CAP_H = 960, 84

LINES = {
    1: ('ДЕД МОРОЗ', 'До Нового года две минуты!'),
    2: ('ДЕД МОРОЗ', 'Мила, посылка №2027 не доставлена!'),
    3: ('МИЛА', 'Я успею!'),
    4: ('СНЕЖА', 'Полозья смазаны — сани готовы, шеф! Держись!'),
    5: ('МИЛА', 'Ещё одна звезда!'),
    6: ('МЕТЕЛЬ', 'Не доживёшь до полуночи, козочка!'),
    7: ('МИЛА', 'Смотрите, окно! Там ждут чудо!'),
    8: ('ДЕД МОРОЗ', 'Ты успела, Мила! С Новым 2027 годом!'),
    9: ('МИЛА', 'Полночь… Я не успела. Но я попробую снова!'),
    10: ('ДЕД МОРОЗ', 'Спасибо тебе, козочка. Праздник спасён!'),
}

HINT_LINES = {
    1: 'САНИ   ·   ПРОБЕЛ — ПРЫЖОК   ·   5 ЗВЕЗД',
    2: '↑ ↓ — ПО ЛЕСУ НА САНЯХ   ·   ЕЩЁ 5 ЗВЕЗД',
    3: '← → — БЕГ   ·   ПРОБЕЛ — ПРЫЖОК   ·   ВЫЖИВ ДО ПОЛЫ НОЧИ',
}


def fit_size(text, speaker=None):
    """Подбираем ОДИН размер шрифта на все плашки, чтобы типографика была единой."""
    probe = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    gap = 26 if speaker else 0
    size = 42
    while size > 18:
        f = font(size)
        fs = font(int(size * 0.8))
        wtxt = probe.textbbox((0, 0), text, font=f, stroke_width=3)[2]
        wspk = probe.textbbox((0, 0), speaker, font=fs, stroke_width=3)[2] if speaker else 0
        if wspk + gap + wtxt <= CAP_W - 64:
            return size
        size -= 2
    return 18


def cap_plate(text, speaker=None, color=CREAM, size=None):
    """Тёмная плашка во всю ширину сцены: [золотое имя говорящего] + реплика."""
    im = Image.new('RGBA', (CAP_W, CAP_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, CAP_W - 2, CAP_H - 2], radius=20, fill=(8, 16, 34, 214),
                        outline=(255, 201, 107, 255), width=3)
    probe = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    gap = 26 if speaker else 0
    if size is None:
        size = fit_size(text, speaker)
    f = font(size)
    fs = font(int(size * 0.8))
    wtxt = probe.textbbox((0, 0), text, font=f, stroke_width=3)[2]
    wspk = probe.textbbox((0, 0), speaker, font=fs, stroke_width=3)[2] if speaker else 0
    total = wspk + gap + wtxt
    x = (CAP_W - total) / 2
    y = CAP_H / 2 + 2
    if speaker:
        d.text((x, y - 1), speaker, font=fs, fill=GOLD, anchor='lm',
               stroke_width=3, stroke_fill=(6, 10, 24, 255))
        x += wspk + gap
    d.text((x, y), text, font=f, fill=color, anchor='lm',
           stroke_width=3, stroke_fill=(6, 10, 24, 255))
    return im


def captions():
    """Реплики — статичными субтитрами (озвучка уже есть, облачка перекрывали сцену)."""
    # единый кегль внутри «семейства»: реплики — один, подсказки — другой
    size_c = min(fit_size(t, spk) for spk, t in LINES.values())
    size_h = min(fit_size(t) for t in HINT_LINES.values())
    print('субтитры: кегль', size_c, '· подсказки: кегль', size_h)
    for n, (spk, txt) in LINES.items():
        cap_plate(txt, spk, size=size_c).save(f'{UI}/cap{n}.png')
    for n, txt in HINT_LINES.items():
        cap_plate(txt, size=size_h).save(f'{UI}/hint{n}.png')


def countdown():
    """Обратный отсчёт третьего акта: крупные цифры 20->0 в верхней полосе HUD.

    Цель акта должна быть не просто сформулирована в подсказке, но и измерима:
    счётчик на табло тикает вместе с переменной «осталось»."""
    for n in range(21):
        im = Image.new('RGBA', (180, 100), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        f = font(72)
        txt = str(n)
        w = d.textbbox((0, 0), txt, font=f, stroke_width=5)[2]
        d.text(((180 - w) / 2, 50), txt, font=f, fill=GOLD, anchor='mm',
               stroke_width=5, stroke_fill=NAVY)
        im.save(f'{UI}/count_{n}.png')


def hints():
    """Совместимость: старые подсказки теперь рисуются общей плашкой."""
    captions()


def particles():
    """Снежинка и искра: без них частицы брали картинку HUD «★ 0»."""
    S = 96
    c = S / 2
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(int(c) - 4, 0, -1):
        a = int(46 * (1 - r / (c - 4)) ** 1.7)
        d.ellipse([c - r, c - r, c + r, c + r], fill=(226, 240, 255, a))
    for i in range(6):
        a = math.radians(i * 60)
        dx, dy = math.sin(a), -math.cos(a)
        d.line([c, c, c + dx * (c - 8), c + dy * (c - 8)], fill=(255, 255, 255, 245), width=5)
        for t0 in (0.48, 0.72):
            bx, by = c + dx * (c - 8) * t0, c + dy * (c - 8) * t0
            for sgn in (-1, 1):
                a2 = math.radians(i * 60 + sgn * 52)
                d.line([bx, by, bx + math.sin(a2) * 12, by - math.cos(a2) * 12],
                       fill=(238, 248, 255, 232), width=4)
    im.save(f'{UI}/snowflake.png')

    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(int(c) - 4, 0, -1):
        a = int(70 * (1 - r / (c - 4)) ** 1.8)
        d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 214, 140, a))
    pts = []
    for i in range(8):
        r = (c - 6) if i % 2 == 0 else (c - 6) * 0.26
        a = math.radians(i * 45 - 90)
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=(255, 247, 224, 255), outline=(255, 201, 107, 255))
    im.save(f'{UI}/spark.png')


def clock():
    S = 260
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([8, 8, S - 8, S - 8], fill=(14, 32, 60, 235), outline=GOLD, width=6)
    for i in range(12):
        a = math.radians(i * 30)
        r0, r1 = S * 0.36, S * 0.44
        cx, cy = S / 2, S / 2
        d.line([cx + r0 * math.sin(a), cy - r0 * math.cos(a),
                cx + r1 * math.sin(a), cy - r1 * math.cos(a)],
               fill=CREAM if i % 3 == 0 else (150, 175, 205), width=6 if i % 3 == 0 else 3)
    d.ellipse([S / 2 - 8, S / 2 - 8, S / 2 + 8, S / 2 + 8], fill=GOLD)
    im.save(f'{UI}/clock_face.png')

    h = Image.new('RGBA', (24, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(h)
    d.rounded_rectangle([4, 6, 20, 150], radius=8, fill=(255, 201, 107, 255), outline=NAVY, width=3)
    d.ellipse([2, 140, 22, 180], fill=(192, 57, 43, 255), outline=NAVY, width=3)
    h.save(f'{UI}/clock_hand.png')

    # две стрелки с центром поворота В ЦЕНТРЕ полотна: основание лежит в
    # центре, стрелка торчит вверх. Часовая — короткая и толстая, минутная —
    # длинная и тонкая. Угол 0° (направление «вверх») = 12 часов.
    def hand(w, hh, pivot_y, fill, tip_fill, tip_h, tip_w):
        im = Image.new('RGBA', (w, hh), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        px = w / 2
        # рукав от центра до основания стрелки
        dd.rounded_rectangle([px - w * 0.26, pivot_y - hh * 0.5, px + w * 0.26, pivot_y + 4],
                             radius=int(w * 0.2), fill=fill, outline=NAVY, width=3)
        # стрелка (основание — в pivot_y, верх — в 0)
        dd.polygon([(px - w * 0.16, pivot_y + 2), (px + w * 0.16, pivot_y + 2),
                    (px, tip_h)], fill=fill, outline=NAVY)
        # наконечник
        dd.ellipse([px - tip_w, tip_h - tip_h, px + tip_w, tip_h + tip_h * 0.5],
                   fill=tip_fill, outline=NAVY, width=3)
        return im, (px, pivot_y)

    min_img, min_pivot = hand(22, 150, 75, (255, 201, 107, 255), (192, 57, 43, 255), 18, 4)
    min_img.save(f'{UI}/clock_hand_min.png')
    hr_img, hr_pivot = hand(30, 96, 48, (245, 241, 230, 255), (192, 57, 43, 255), 14, 5)
    hr_img.save(f'{UI}/clock_hand_hr.png')


def mila_run_frame():
    """Дополнительный кадр бега Милы: спрайт поднят на 7 px — ноги кажутся
    поднятыми (шаг). Используется как второй кадр анимации бега (смена костюма,
    а не позиции — коллизии не затронуты)."""
    src = Image.open(f'{SPR}/goat_run.png').convert('RGBA')
    W, H = src.size
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    im.paste(src, (0, -7), src)  # поднять на 7 px, освободить низ
    im.save(f'{SPR}/goat_run_b.png')


def _blink_frame(src_path, out_path, ylo, yhi, lid_h=10, lid_a=235):
    """Становящий кадр мигания: в лицевой полосе (y в [ylo,yhi]) находим
    тёмные кластеры (глаза) и рисуем по каждому тёмную полупрозрачную планку-веко.
    Покрытие по блоку тёмных пикселей — глаза гарантированно закрываются, даже
    без точного знания координат."""
    import numpy as np
    src = Image.open(src_path).convert('RGBA')
    a = np.asarray(src)
    rgb = a[..., :3].astype(int)
    al = a[..., 3]
    dark = (rgb.sum(axis=2) < 180) & (al > 150)
    im = src.copy()
    d = ImageDraw.Draw(im, 'RGBA')
    band = dark[ylo:yhi, :]
    ys, xs = np.nonzero(band)
    if len(xs) == 0:
        im.save(out_path)
        return
    # кластеризация по x с шагом 12
    import collections
    hist = collections.Counter((x // 12) * 12 for x in xs)
    clusters = sorted([k for k, v in hist.items() if v >= 14], key=lambda k: -hist[k])
    for k in clusters[:4]:  # до 4 «глаз»/детали
        sel = (xs >= k) & (xs < k + 12)
        cx = int(xs[sel].mean())
        cy = int(ys[sel].mean()) + ylo
        d.rounded_rectangle([cx - 9, cy - lid_h // 2, cx + 9, cy + lid_h // 2],
                            radius=lid_h // 2, fill=(20, 14, 12, lid_a))
    im.save(out_path)


def santa_blink():
    """Веко на глазах Санта: спрайт 315×420, глаза — левый x≈135-139,
    правый x≈158-162, y≈63-66. Полоса y 100-150 (нос/борода) давала веко
    не в месте — рисуем покрывочно точно на позициях глаз."""
    src = Image.open(f'{SPR}/santa.png').convert('RGBA')
    im = src.copy()
    d = ImageDraw.Draw(im, 'RGBA')
    for cx in (137, 160):  # центры глаз
        d.rounded_rectangle([cx - 6, 61, cx + 6, 68],
                            radius=3, fill=(20, 14, 12, 235))
    im.save(f'{SPR}/santa_blink.png')


def snowman_blink():
    _blink_frame(f'{SPR}/snowman.png', f'{SPR}/snowman_blink.png', 80, 120)


def mila_blink():
    for pose in ('idle', 'run', 'jump', 'cheer'):
        _blink_frame(f'{SPR}/goat_{pose}.png', f'{SPR}/goat_{pose}_blink.png',
                     115, 160)


def effect_wink_closed():
    """Закрытое веко Милы: полупрозрачная мягкая ломаная на позиции глаза
    (dark lid over the eye cluster around (215,142) of the goat sprite)."""
    W, H = 64, 36
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for w in (20, 15, 11):
        d.line([(6, 20 - w // 2), (32, 16 - w // 2), (58, 20 - w // 2)],
               fill=(35, 22, 20, 235), width=w)
    return im


def owl_flap_frame():
    """Кадр взмаха крыла Совы: левое крыло (область x<90) поднимается вверх-влево
    вокруг плеча (88, 62) на 18°. Старое крыло стирается, чтобы не было
    «двойного крыла»; крыло остаётся в области x<90 — лицо не перекрывается."""
    base = Image.open(f'{SPR}/owl.png').convert('RGBA')
    SHOULDER = (88, 62)
    # 1) стираем старое крыло (x < 90)
    arr = np.array(base)
    arr[:, :90, 3] = 0
    base = Image.fromarray(arr)
    # 2) копируем только область крыла и вращаем её вокруг плеча
    wing = Image.open(f'{SPR}/owl.png').convert('RGBA').crop((0, 0, 90, base.height))
    canvas = Image.new('RGBA', base.size, (0, 0, 0, 0))
    canvas.paste(wing, (0, 0), wing)
    rot = canvas.rotate(-18, resample=Image.BICUBIC, center=SHOULDER)
    base.alpha_composite(rot)
    base.save(f'{SPR}/owl_open.png')


def owl_flap_frames():
    owl_flap_frame()


def effect_owl_wings(open_):
    """Крыло Совы в взмахе. Открывается вниз-вперёд, близко к телу (x≈62).
    open_=0 — сложен, open_=1 — раскрыт на 42°."""
    W, H = 150, 220
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = (64, 44, 38)
    wing = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wing)
    for i in range(7):
        x0 = 70 - i * 8
        wd.line([(x0 + i * 2, 30 + i * 16), (18 + i * 2, 120 + i * 10)],
                fill=col, width=9)
    wing = wing.rotate(open_ * 42, resample=Image.BICUBIC, center=(70, 34))
    im = Image.alpha_composite(im, wing)
    d = ImageDraw.Draw(im)
    d.ellipse([62, 24, 82, 44], fill=(48, 34, 30, 255))  # плечевая кость
    return im


def effect_smoke_puff(i):
    """Дым/пар: слой дофельного серого пуффа. i 0..4 — цикл размера."""
    s = [64, 84, 100, 84, 64][i % 5]
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r, a in ((s * 0.36, 110), (s * 0.30, 90), (s * 0.24, 70)):
        cx = s / 2 + (6 if r > s * 0.3 else -5)
        cy = s * 0.46 + (5 if r < s * 0.28 else -4)
        d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8],
                  fill=(196, 193, 186, a))
    return im


def effect_flame(i):
    """Пламя lantern/candle: 4 состояния анимации (48×96)."""
    W, H = 48, 96
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    t = i % 4
    # внутренний ядро
    for dx, sx, sy in ((0, 1.0, 1.0), (0, 0.62, 0.86), (-6 + t * 3, 0.34, 0.6)):
        x, y = W / 2 + dx, H * 0.58
        d.ellipse([x - W * 0.11 * sx, y - H * 0.18 * sy,
                   x + W * 0.11 * sx, y + H * 0.18 * sy],
                  fill=(255, 236, 150, 230))
    # внешний язык
    pts = [(W / 2, H * 0.16 + (8 if t == 1 else -6 if t == 2 else 2)),
           (W * 0.16, H * 0.5), (W * 0.42, H * 0.46),
           (W / 2, H * 0.58), (W * 0.84, H * 0.46),
           (W * 0.84, H * 0.46)]
    d.polygon(pts, fill=(255, 138, 40, 200))
    d.polygon([(W / 2, H * 0.24), (W * 0.26, H * 0.52),
               (W * 0.5, H * 0.58), (W * 0.74, H * 0.52)],
              fill=(255, 190, 80, 150))
    return im


def effect_lantern(i):
    """Тёплое мерцание огонька: 4 кадра мягкого жёлтого света (72×72)."""
    s, t = 72, i % 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = [130, 175, 145, 200][t]
    r = [40, 36, 42, 33][t]
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r],
              fill=(255, 210, 120, a))
    d.ellipse([s / 2 - r * 0.55, s / 2 - r * 0.55,
               s / 2 + r * 0.55, s / 2 + r * 0.55],
              fill=(255, 244, 200, min(a + 60, 240)))
    return im


def effect_firefly(i):
    """Светлячок/мерцающая искорка леса: 36×36, 4 кадра пульсации."""
    s, t = 36, i % 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = [11, 8, 12, 6][t]
    d.ellipse([s / 2 - r * 1.7, s / 2 - r * 1.7,
               s / 2 + r * 1.7, s / 2 + r * 1.7],
              fill=(200, 235, 150, 70))
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r],
              fill=(245, 255, 190, 220))
    return im


def effect_snow_streaks(i):
    """Снежные хлопья/узкие размытые полосы: 144×144, 5 кадров."""
    s, t = 144, i % 5
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = [(0, 0), (10, 8), (6, -6), (-8, 10), (14, -4)][t]
    for x, y, r, a in ((48, 48, 7, 190), (96, 70, 6, 150), (30, 84, 5, 130),
                       (110, 110, 6, 140), (60, 116, 5, 110), (104, 40, 5, 120)):
        d.ellipse([x + rng[0] - r, y + rng[1] - r,
                   x + rng[0] + r, y + rng[1] + r],
                  fill=(235, 242, 250, a))
    return im


def effect_blizzard(i):
    """Метель на крыше: горизонтальная пелена порывов (160×110)."""
    W, H, t = 160, 110, i % 4
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k, (y, a, ph) in enumerate(((28, 170, 0), (50, 140, 1),
                                     (72, 120, 2), (92, 100, 3))):
        x0 = (k * 40 + t * 26) % (W + 80) - 40
        d.line([(x0, y), (x0 + W * 0.62, y + 12)],
               fill=(242, 248, 252, a), width=14)
        d.line([(x0 + 30, y - 8), (x0 + 90, y + 6)],
               fill=(255, 255, 255, a - 30), width=7)
    return im


def effect_explosion(i):
    """Вспышка фейерверка: 4 кадра расходящегося круга (140×140)."""
    s, t = 140, i % 4
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = [14, 30, 44, 52][t]
    a = [250, 200, 120, 50][t]
    col = [(255, 240, 180), (255, 200, 90), (255, 160, 80), (255, 220, 150)][t]
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=(*col, a))
    for k in range(8):
        ang = k * math.pi / 4
        x1 = s / 2 + math.cos(ang) * r
        y1 = s / 2 + math.sin(ang) * r
        x2 = s / 2 + math.cos(ang) * (r + 10 + t * 4)
        y2 = s / 2 + math.sin(ang) * (r + 10 + t * 4)
        d.line([(x1, y1), (x2, y2)], fill=col, width=4)
    return im


def pixel():
    Image.new('RGBA', (8, 8), (0, 0, 0, 0)).save(f'{UI}/px.png')
    # «чёрный экран» для затемнений
    Image.new('RGBA', (960, 720), (6, 10, 24, 255)).save(f'{UI}/fade.png')


# ------------------------------------------------------------------ заглушки
def placeholders():
    """Простые фигуры на месте спрайтов, которых ещё нет (перекрываются AI-артом)."""
    def canvas(w, h, draw_fn):
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(im), w, h)
        return im

    def snowman(d, w, h):
        for i, (y, r) in enumerate([(h - 70, 62), (h - 165, 48), (h - 240, 36)]):
            d.ellipse([w / 2 - r, y - r, w / 2 + r, y + r], fill=(238, 246, 252, 255),
                      outline=(150, 180, 205, 255), width=3)
        d.ellipse([w / 2 - 12, h - 258, w / 2 + 2, h - 244], fill=(40, 40, 45, 255))
        d.ellipse([w / 2 + 6, h - 258, w / 2 + 20, h - 244], fill=(40, 40, 45, 255))
        d.polygon([(w / 2 + 2, h - 232), (w / 2 + 42, h - 226), (w / 2 + 2, h - 220)], fill=(240, 130, 40, 255))
        d.rectangle([w / 2 - 34, h - 290, w / 2 + 34, h - 262], fill=(120, 128, 96, 255))

    def santa(d, w, h):
        d.ellipse([w / 2 - 78, h - 260, w / 2 + 78, h - 60], fill=(170, 40, 40, 255))
        d.ellipse([w / 2 - 52, h - 300, w / 2 + 52, h - 190], fill=(245, 245, 240, 255))
        d.ellipse([w / 2 - 40, h - 288, w / 2 + 40, h - 240], fill=(246, 210, 180, 255))
        d.polygon([(w / 2 - 46, h - 318), (w / 2 + 46, h - 318), (w / 2 + 30, h - 276), (w / 2 - 30, h - 276)],
                  fill=(170, 40, 40, 255))

    def storm(d, w, h):
        for i in range(12):
            r = 40 + i * 6
            a = i * 30
            d.arc([w / 2 - r, h / 2 - r * 0.7, w / 2 + r, h / 2 + r * 0.7], a, a + 200,
                  fill=(150, 200, 235, 220), width=6)
        d.ellipse([w / 2 - 40, h / 2 - 34, w / 2 - 10, h / 2 - 8], fill=(40, 70, 110, 255))
        d.ellipse([w / 2 + 10, h / 2 - 34, w / 2 + 40, h / 2 - 8], fill=(40, 70, 110, 255))

    def owl(d, w, h):
        d.ellipse([w / 2 - 46, h / 2 - 50, w / 2 + 46, h / 2 + 60], fill=(150, 152, 165, 255))
        d.ellipse([w / 2 - 32, h / 2 - 40, w / 2 - 6, h / 2 - 14], fill=(245, 245, 240, 255))
        d.ellipse([w / 2 + 6, h / 2 - 40, w / 2 + 32, h / 2 - 14], fill=(245, 245, 240, 255))
        d.ellipse([w / 2 - 22, h / 2 - 32, w / 2 - 12, h / 2 - 22], fill=(30, 30, 35, 255))
        d.ellipse([w / 2 + 12, h / 2 - 32, w / 2 + 22, h / 2 - 22], fill=(30, 30, 35, 255))

    def sleigh(d, w, h):
        d.rounded_rectangle([30, h - 120, w - 60, h - 70], radius=12, fill=(120, 78, 48, 255))
        d.arc([w - 120, h - 120, w - 20, h - 40], 250, 20, fill=(190, 200, 215, 255), width=10)
        d.rounded_rectangle([40, h - 80, w - 100, h - 62], radius=8, fill=(190, 200, 215, 255))

    def gift(d, w, h):
        d.rounded_rectangle([40, h / 2 - 30, w - 40, h / 2 + 60], radius=10, fill=(230, 170, 60, 255),
                            outline=(120, 70, 20, 255), width=4)
        d.rectangle([w / 2 - 12, h / 2 - 30, w / 2 + 12, h / 2 + 60], fill=(200, 50, 45, 255))
        d.ellipse([w / 2 - 40, h / 2 - 70, w / 2, h / 2 - 30], outline=(200, 50, 45, 255), width=10)
        d.ellipse([w / 2, h / 2 - 70, w / 2 + 40, h / 2 - 30], outline=(200, 50, 45, 255), width=10)

    def star(d, w, h):
        d.polygon(star_polygon(w / 2, h / 2, 70, 30), fill=GOLD, outline=(120, 70, 20, 255))

    def tree(d, w, h):
        for i in range(3):
            top = h / 2 - 120 + i * 55
            d.polygon([(w / 2, top), (w / 2 - 60 - i * 18, top + 100), (w / 2 + 60 + i * 18, top + 100)],
                      fill=(34, 92, 62, 255), outline=(210, 230, 240, 255), width=4)

    def platform(d, w, h):
        d.rounded_rectangle([10, h / 2 - 20, w - 10, h / 2 + 30], radius=16, fill=(120, 78, 48, 255))
        d.rounded_rectangle([10, h / 2 - 30, w - 10, h / 2 + 2], radius=14, fill=(242, 246, 250, 255))

    def drift(d, w, h):
        d.ellipse([10, h / 2, w - 10, h - 10], fill=(240, 246, 252, 255), outline=(170, 200, 220, 255), width=4)

    makers = {
        'santa': (300, 420, santa), 'snowman': (300, 420, snowman), 'storm': (460, 300, storm),
        'owl': (260, 300, owl), 'sleigh': (420, 220, sleigh), 'gift': (220, 260, gift),
        'star': (220, 220, star), 'tree': (300, 460, tree), 'platform': (460, 160, platform),
        'snowdrift': (420, 180, drift),
    }
    made = []
    for name, (w, h, fn) in makers.items():
        out = f'{SPR}/{name}.png'
        if not os.path.exists(out):
            canvas(w, h, fn).save(out)
            made.append(name)
    return made


if __name__ == '__main__':
    titles()
    buttons()
    hud()
    clock()
    hints()
    captions()
    countdown()
    particles()
    pixel()
    effect_wink_closed().save(f'{SPR}/mila_wink_closed.png')
    effect_owl_wings(0).save(f'{SPR}/owl_wing_closed.png')
    effect_owl_wings(1).save(f'{SPR}/owl_wing_open.png')
    effect_smoke_puff(0).save(f'{SPR}/fx_smoke_0.png')
    effect_smoke_puff(1).save(f'{SPR}/fx_smoke_1.png')
    effect_smoke_puff(2).save(f'{SPR}/fx_smoke_2.png')
    effect_flame(0).save(f'{SPR}/fx_flame_0.png')
    effect_flame(1).save(f'{SPR}/fx_flame_1.png')
    effect_flame(2).save(f'{SPR}/fx_flame_2.png')
    effect_flame(3).save(f'{SPR}/fx_flame_3.png')
    effect_lantern(0).save(f'{SPR}/fx_lantern_0.png')
    effect_lantern(1).save(f'{SPR}/fx_lantern_1.png')
    effect_lantern(2).save(f'{SPR}/fx_lantern_2.png')
    effect_lantern(3).save(f'{SPR}/fx_lantern_3.png')
    effect_firefly(0).save(f'{SPR}/fx_firefly_0.png')
    effect_firefly(1).save(f'{SPR}/fx_firefly_1.png')
    effect_firefly(2).save(f'{SPR}/fx_firefly_2.png')
    effect_firefly(3).save(f'{SPR}/fx_firefly_3.png')
    effect_snow_streaks(0).save(f'{SPR}/fx_snow_0.png')
    effect_snow_streaks(1).save(f'{SPR}/fx_snow_1.png')
    effect_snow_streaks(2).save(f'{SPR}/fx_snow_2.png')
    effect_snow_streaks(3).save(f'{SPR}/fx_snow_3.png')
    effect_snow_streaks(4).save(f'{SPR}/fx_snow_4.png')
    effect_blizzard(0).save(f'{SPR}/fx_blizzard_0.png')
    effect_blizzard(1).save(f'{SPR}/fx_blizzard_1.png')
    effect_blizzard(2).save(f'{SPR}/fx_blizzard_2.png')
    effect_blizzard(3).save(f'{SPR}/fx_blizzard_3.png')
    effect_explosion(0).save(f'{SPR}/fx_explosion_0.png')
    effect_explosion(1).save(f'{SPR}/fx_explosion_1.png')
    effect_explosion(2).save(f'{SPR}/fx_explosion_2.png')
    effect_explosion(3).save(f'{SPR}/fx_explosion_3.png')
    mila_run_frame()
    mila_blink()
    santa_blink()
    snowman_blink()
    owl_flap_frames()
    ph = placeholders()
    print('UI готов. Заглушки:', ', '.join(ph) if ph else 'нет (все спрайты на месте)')
