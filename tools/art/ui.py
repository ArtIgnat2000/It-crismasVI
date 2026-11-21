"""Процедурные ассеты: титры, кнопки, HUD, часы и заглушки вместо ещё не сгенерированных спрайтов.

Титры рисуются шрифтом DejaVu (поддерживает кириллицу) с тёмной обводкой —
это даёт «киношный» вид и не требует текста внутри AI-картинок.
"""
import math
import os
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
    t = text_img('ПОСЛЕДНЯЯ', 96)
    t2 = text_img('ПОСЫЛКА', 108)
    sub = text_img('новогодняя игра · Scratch 3.0', 34, color=CREAM, stroke=4)
    w = max(t.width, t2.width, sub.width) + 40
    im = Image.new('RGBA', (w, t.height + t2.height + sub.height + 30), (0, 0, 0, 0))
    im.alpha_composite(t, ((w - t.width) // 2, 0))
    im.alpha_composite(t2, ((w - t2.width) // 2, t.height - 10))
    im.alpha_composite(sub, ((w - sub.width) // 2, t.height + t2.height - 20))
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


def hints():
    """Подсказки по управлению: своя на каждый акт (в актах разное управление!)."""
    W, H = 1400, 124
    lines_txt = [
        ('hint1', 'ПРОБЕЛ ПРЫЖОК  ·  СОБЕРИ 5 ЗВЕЗД'),
        ('hint2', '↑ ↓ ВВЕРХ / ВНИЗ  ·  ЕЩЁ 5 ЗВЕЗД'),
        ('hint3', '← → БЕГ  ·  ПРОБЕЛ ПРЫЖОК  ·  ПРОДЕРЖИСЬ 20 С'),
    ]
    probe = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    for fn, text in lines_txt:
        size = 58
        while size > 20:
            if probe.textbbox((0, 0), text, font=font(size), stroke_width=4)[2] <= W - 90:
                break
            size -= 2
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([2, 2, W - 2, H - 2], radius=34, fill=(8, 16, 34, 208),
                            outline=(255, 201, 107, 255), width=4)
        d.text((W / 2, H / 2 - 2), text, font=font(size), fill=CREAM, anchor='mm',
               stroke_width=4, stroke_fill=(6, 10, 24, 255))
        im.save(f'{UI}/{fn}.png')
        print('hint', fn, im.size, 'шрифт', size)



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
    pixel()
    ph = placeholders()
    print('UI готов. Заглушки:', ', '.join(ph) if ph else 'нет (все спрайты на месте)')
