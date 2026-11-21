"""Макеты игровых кадров из настоящих ассетов проекта (как это увидит игрок)."""
import os
from PIL import Image

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
W, H = 960, 720           # рендер 2x от сцены 480x360
OUT = f'{R}/art/mock'


def px(x):
    return (x + 240) / 480 * W


def py(y):
    return (180 - y) / 360 * H


def put(frame, path, x, y, size):
    im = Image.open(path).convert('RGBA')
    k = size / 100 * 2          # 2x рендер
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    frame.alpha_composite(im, (int(px(x) - im.width / 2), int(py(y) - im.height / 2)))


def bg(path):
    return Image.open(path).convert('RGBA').resize((W, H), Image.LANCZOS)


def hud(frame, lives=3, stars=5):
    put(frame, f'{R}/art/ui/lives_{lives}.png', -195, 128, 22)
    put(frame, f'{R}/art/ui/stars_{stars}.png', 150, 128, 16)
    put(frame, f'{R}/art/ui/clock_face.png', 190, 130, 22)
    put(frame, f'{R}/art/ui/clock_hand.png', 190, 130, 22)


def titles():
    # 1. Пролог
    f = bg(f'{R}/art/backgrounds/bg_workshop.jpg')
    put(f, f'{R}/art/sprites/santa.png', -60, -55, 42)
    put(f, f'{R}/art/sprites/goat_idle.png', 60, -88, 26)
    put(f, f'{R}/art/sprites/snowman.png', 110, -80, 26)
    put(f, f'{R}/art/ui/title.png', 0, 55, 34)
    f.convert('RGB').save(f'{OUT}/01_prolog.jpg', quality=90)

    # 2. Акт 1 — город
    f = bg(f'{R}/art/backgrounds/bg_city.jpg')
    put(f, f'{R}/art/sprites/snowdrift.png', 150, -118, 19)
    put(f, f'{R}/art/sprites/star.png', 70, -60, 13)
    put(f, f'{R}/art/sprites/sleigh.png', -160, -129, 42)
    put(f, f'{R}/art/sprites/goat_run.png', -150, -95, 26)
    put(f, f'{R}/art/sprites/gift.png', -172, -61, 18)
    hud(f, 3, 5)
    f.convert('RGB').save(f'{OUT}/02_act1.jpg', quality=90)

    # 3. Акт 2 — лес
    f = bg(f'{R}/art/backgrounds/bg_forest.jpg')
    put(f, f'{R}/art/sprites/tree.png', 170, -40, 28)
    put(f, f'{R}/art/sprites/star.png', 40, 0, 13)
    put(f, f'{R}/art/sprites/owl.png', -185, 70, 16)
    put(f, f'{R}/art/sprites/sleigh.png', -140, -104, 42)
    put(f, f'{R}/art/sprites/goat_run.png', -130, -70, 26)
    put(f, f'{R}/art/sprites/gift.png', -152, -36, 18)
    hud(f, 2, 8)
    f.convert('RGB').save(f'{OUT}/03_act2.jpg', quality=90)

    # 4. Акт 3 — крыша, метель
    f = bg(f'{R}/art/backgrounds/bg_roof.jpg')
    put(f, f'{R}/art/sprites/storm.png', 160, 50, 45)
    put(f, f'{R}/art/sprites/snowdrift.png', 60, 20, 12)
    put(f, f'{R}/art/sprites/goat_run.png', -150, -95, 26)
    put(f, f'{R}/art/sprites/gift.png', -172, -61, 18)
    hud(f, 2, 10)
    f.convert('RGB').save(f'{OUT}/04_act3.jpg', quality=90)

    # 5. Победа
    f = bg(f'{R}/art/backgrounds/bg_victory.jpg')
    put(f, f'{R}/art/sprites/goat_cheer.png', -140, -110, 32)
    put(f, f'{R}/art/ui/win.png', 0, 100, 30)
    put(f, f'{R}/art/ui/s2027.png', 90, -10, 26)
    put(f, f'{R}/art/ui/btn_retry.png', 0, -95, 30)
    f.convert('RGB').save(f'{OUT}/05_win.jpg', quality=90)

    # 6. Проигрыш
    f = bg(f'{R}/art/backgrounds/bg_defeat.jpg')
    put(f, f'{R}/art/sprites/goat_idle.png', -120, -95, 26)
    put(f, f'{R}/art/ui/lose.png', 0, 70, 26)
    put(f, f'{R}/art/ui/btn_retry.png', 0, -110, 30)
    f.convert('RGB').save(f'{OUT}/06_lose.jpg', quality=90)

    # контактный лист
    names = ['01_prolog', '02_act1', '03_act2', '04_act3', '05_win', '06_lose']
    tw, th = 640, 480
    sheet = Image.new('RGB', (tw * 2 + 30, th * 3 + 40), (8, 12, 24))
    for i, n in enumerate(names):
        im = Image.open(f'{OUT}/{n}.jpg').resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (10 + (i % 2) * (tw + 10), 10 + (i // 2) * (th + 10)))
    sheet.save(f'{OUT}/_все_кадры.jpg', quality=88)
    print('макеты готовы:', sheet.size)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    titles()
