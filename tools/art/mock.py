"""Макеты игровых кадров из настоящих ассетов проекта (как это увидит игрок).

ГЛАВНОЕ: это «дизайнерские» кадры, нарисованные вручную по координатам из
game.py. Авторитетнее — `art/mock/frames/`: там настоящие снимки состояния
scratch-vm (см. tools/art/frames.py). Если правите композицию — правьте оба.

Правила композиции: docs/09-kompoziciya.md.
"""
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


CAP_Y = -157          # единая нижняя плашка: подсказки и субтитры


def hud(frame, lives=3, stars=5):
    put(frame, f'{R}/art/ui/lives_{lives}.png', -196, 130, 22)
    put(frame, f'{R}/art/ui/stars_{stars}.png', 140, 126, 16)
    put(frame, f'{R}/art/ui/clock_face.png', 196, 126, 20)
    put(frame, f'{R}/art/ui/clock_hand.png', 196, 126, 16)
    put(frame, f'{R}/art/ui/btn_sound_on.png', -206, 152, 22)


def titles():
    # 1. Пролог: титр + голос за кадром (персонажей на сцене ещё нет)
    f = bg(f'{R}/art/backgrounds/bg_workshop.jpg')
    put(f, f'{R}/art/ui/title.png', 0, 58, 34)
    hud(f, 3, 0)
    put(f, f'{R}/art/ui/cap1.png', 0, CAP_Y, 100)
    f.convert('RGB').save(f'{OUT}/01_prolog.jpg', quality=90)

    # 1б. Пролог: Дед Мороз и Мила, реплика — субтитром внизу
    f = bg(f'{R}/art/backgrounds/bg_workshop.jpg')
    put(f, f'{R}/art/sprites/santa.png', -120, -60, 34)
    put(f, f'{R}/art/sprites/goat_idle.png', 95, -78, 26)
    hud(f, 3, 0)
    put(f, f'{R}/art/ui/cap2.png', 0, CAP_Y, 100)
    f.convert('RGB').save(f'{OUT}/01b_prolog_dialog.jpg', quality=90)

    # 2. Акт 1 — город: бег с прыжками, саней нет, посылка за спиной
    f = bg(f'{R}/art/backgrounds/bg_city.jpg')
    put(f, f'{R}/art/sprites/snowdrift.png', 150, -120, 18)
    put(f, f'{R}/art/sprites/star.png', 70, -60, 11)
    put(f, f'{R}/art/sprites/goat_run.png', -150, -80, 26)
    put(f, f'{R}/art/sprites/gift.png', -182, -72, 9)
    hud(f, 3, 0)
    put(f, f'{R}/art/ui/hint1.png', 0, CAP_Y, 100)
    f.convert('RGB').save(f'{OUT}/02_act1.jpg', quality=90)

    # 3. Акт 2 — лес: полёт на санях
    f = bg(f'{R}/art/backgrounds/bg_forest.jpg')
    put(f, f'{R}/art/sprites/tree.png', 170, -40, 28)
    put(f, f'{R}/art/sprites/star.png', 40, 0, 11)
    put(f, f'{R}/art/sprites/owl.png', -185, 70, 12)
    put(f, f'{R}/art/sprites/sleigh.png', -136, -74, 30)
    put(f, f'{R}/art/sprites/goat_run.png', -130, -60, 26)
    put(f, f'{R}/art/sprites/gift.png', -156, -78, 10)
    hud(f, 2, 5)
    put(f, f'{R}/art/ui/hint2.png', 0, CAP_Y, 100)
    f.convert('RGB').save(f'{OUT}/03_act2.jpg', quality=90)

    # 4. Акт 3 — крыша, метель
    f = bg(f'{R}/art/backgrounds/bg_roof.jpg')
    put(f, f'{R}/art/sprites/storm.png', 140, 45, 34)
    put(f, f'{R}/art/sprites/snowball.png', 60, 10, 12)
    put(f, f'{R}/art/sprites/goat_run.png', -150, -80, 26)
    put(f, f'{R}/art/sprites/gift.png', -184, -76, 9)
    hud(f, 2, 10)
    put(f, f'{R}/art/ui/hint3.png', 0, CAP_Y, 100)
    f.convert('RGB').save(f'{OUT}/04_act3.jpg', quality=90)

    # 5. Победа
    f = bg(f'{R}/art/backgrounds/bg_victory.jpg')
    put(f, f'{R}/art/sprites/goat_cheer.png', 118, -72, 30)
    put(f, f'{R}/art/sprites/santa.png', -140, -75, 28)
    put(f, f'{R}/art/sprites/gift.png', -92, -92, 12)
    put(f, f'{R}/art/ui/win.png', 0, 124, 24)
    put(f, f'{R}/art/ui/s2027.png', 0, 64, 32)
    put(f, f'{R}/art/ui/s2027_sub.png', 0, 6, 34)
    put(f, f'{R}/art/ui/btn_retry.png', 0, -112, 46)
    hud(f, 3, 0)
    f.convert('RGB').save(f'{OUT}/05_win.jpg', quality=90)

    # 6. Проигрыш
    f = bg(f'{R}/art/backgrounds/bg_defeat.jpg')
    put(f, f'{R}/art/sprites/goat_idle.png', -140, -80, 26)
    put(f, f'{R}/art/ui/lose.png', 0, 96, 24)
    put(f, f'{R}/art/ui/lose_sub.png', 0, 52, 30)
    put(f, f'{R}/art/ui/btn_retry.png', 0, -112, 46)
    hud(f, 0, 0)
    put(f, f'{R}/art/ui/cap9.png', 0, CAP_Y, 100)
    f.convert('RGB').save(f'{OUT}/06_lose.jpg', quality=90)

    # контактный лист
    names = ['01_prolog', '01b_prolog_dialog', '02_act1', '03_act2', '04_act3',
             '05_win', '06_lose']
    tw, th = 640, 480
    sheet = Image.new('RGB', (tw * 2 + 30, th * 4 + 50), (8, 12, 24))
    for i, n in enumerate(names):
        im = Image.open(f'{OUT}/{n}.jpg').resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (10 + (i % 2) * (tw + 10), 10 + (i // 2) * (th + 10)))
    # имя файла отличается от настоящих кадров в art/mock/frames/
    sheet.save(f'{OUT}/_макеты_дизайна.jpg', quality=88)
    print('макеты готовы:', sheet.size)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    titles()
