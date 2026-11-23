# -*- coding: utf-8 -*-
"""Игра «Последняя посылка» — сборка project.json.

Сценарий:
  Пролог (мастерская, 23:58, диалог) ->
  Акт 1 «Ночной город» (сани, прыжки через сугробы, 5 звёзд) ->
  Акт 2 «Зимний лес» (спуск между ёлками, ещё 5 звёзд) ->
  Акт 3 «Крыша» (метель-босс, продержаться 20 секунд) ->
  Победа (титр «2027», фейерверк) / Проигрыш (кнопка «Ещё раз»).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from blocks import Project, Target, Block, mp3_info  # noqa: E402
import sb  # noqa: E402
from sb import *  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
S = f'{R}/art/sprites'
B = f'{R}/art/backgrounds'
BG = B
U = f'{R}/art/ui'
M = f'{R}/audio/music'
F = f'{R}/audio/foley'
V = f'{R}/audio/voice'

def dur(path):
    """Длительность mp3 в секундах (чтобы не блокироваться на «играть до завершения»)."""
    rate, count = mp3_info(path)
    return round(count / max(rate, 1), 1) + 0.5


# --- композиция сцены (см. docs/09-kompoziciya.md) ---------------------------
# Сцена 480x360. Верхняя полоса (y>=112) — HUD, нижняя (y<=-130) — плашка
# субтитров/подсказок. Игровая зона между ними: ноги персонажей на -126.
# Пол поднят так, чтобы копыта/полозья/подол не заезжали на плашку: у Милы
# рисунок смещён вниз внутри полотна 440x440, её «низ» — GROUND-53.8.
GROUND = -80          # «пол» для героини (центр спрайта), ноги на -133.8
HERO_SIZE = 26
CAP_W, CAP_H = 960, 84   # плашка: PNG 960x84 px = 480x42 единицы
CAP_Y = -157             # центр плашки: занимает y от -178 до -136


# --- недостающие в sb.py блоки
def move_steps(n):
    return Block('motion_movesteps', inputs={'STEPS': n})


def point_towards(name):
    return Block('motion_pointtowards', inputs={'TOWARDS': ('menu', name)})


def stop_other():
    return Block('control_stop', fields={'STOP_OPTION': ['other scripts in sprite', None]},
                 mutation={'tagName': 'mutation', 'hasnext': 'true'})


def x_pos():
    return Block('motion_xposition')


def y_pos():
    return Block('motion_yposition')


def not_act(n):
    return not_(eq(var('акт'), n))


def near_x(name, dist):
    """|x - x(спрайта)| < dist"""
    return lt(mathop('abs', sub(x_pos(), of_prop(name, 'x position'))), dist)


def near_y(name, dist):
    return lt(mathop('abs', sub(y_pos(), of_prop(name, 'y position'))), dist)


def alive():
    return and_(gt(var('жизни'), 0), gt(var('время'), 0))


# =====================================================================  СЦЕНА
stage = Target('Stage', is_stage=True)
for name, fn in [('мастерская', 'bg_workshop'), ('город', 'bg_city'), ('лес', 'bg_forest'),
                 ('крыша', 'bg_roof'), ('победа', 'bg_victory'), ('проигрыш', 'bg_defeat')]:
    stage.costume(name, f'{B}/{fn}.jpg', res=2, center=(480, 360))

for v, init in [('игра', 0), ('акт', 0), ('жизни', 3), ('звёзды', 0), ('время', 150),
                ('победа', 0), ('неуязвим', 0), ('скорость', 6), ('ветер', 0.4),
                ('осталось', 0), ('музыка', 0), ('звук_вкл', 1), ('старт_идёт', 0)]:
    stage.var(v, init)

# ================================================================  ОВЕРЛЭИ
# Атмосферные оверлей-акторы 1.10: тень под персонажем, снег на шапке,
# свечение глаз. Они не клонируются — один экземпляр, который следует за
# персонажем (x/y) и появляется/скрывается вместе с ним.
# Управление: broadcast «Вкл_<имя>» — показать, «Скр_<имя>» — скрыть.
def overlay_actor(name, costume, target, dx=0, dy=0, scale=1):
    t = Target(name)
    t.costume('ов', f'{S}/{costume}')
    t.size = scale
    t.visible = False
    t.script(when_flag(), hide(), goto(0, 0))
    t.script(when_bcast('Сброс'), hide())
    t.script(when_bcast('Стоп'), hide())
    t.script(when_bcast(f'Вкл_{name}'), show())
    t.script(when_bcast(f'Скр_{name}'), hide())
    t.script(when_flag(), forever(
        goto(add(of_prop(target, 'x position'), dx),
             add(of_prop(target, 'y position'), dy)),
        wait(0.05)))
    return t


# оверлей-акторы: тени, снег на шапках, свечение глаз
ov_mila_sh = overlay_actor('Тень_Мила', 'shadow.png', 'Мила', 0, 30, 18)
ov_mila_sn = overlay_actor('Снег_Мила', 'snow_mila.png', 'Мила', -10, -40, 16)
ov_sled_sh = overlay_actor('Тень_Сани', 'shadow.png', 'Сани', 0, 26, 18)
ov_gift_sh = overlay_actor('Тень_Подарок', 'shadow.png', 'Подарок', 0, 28, 16)
ov_star_sh = overlay_actor('Тень_Звезда', 'shadow.png', 'Звезда', 0, 30, 16)
ov_dr_sh = overlay_actor('Тень_Сугроб', 'shadow.png', 'Сугроб', 0, 24, 16)
ov_tr_sh = overlay_actor('Тень_Снежок', 'shadow.png', 'Снежок', 0, 30, 16)
ov_dm_sh = overlay_actor('Тень_ДедМороз', 'shadow.png', 'ДедМороз', 0, 34, 26)
ov_dm_sn = overlay_actor('Снег_ДедМороз', 'snow_santa.png', 'ДедМороз', -6, -30, 18)
ov_sm_sh = overlay_actor('Тень_Снеговик', 'shadow.png', 'Снеговик', 0, 36, 20)
ov_sm_sn = overlay_actor('Снег_Снеговик', 'snow_snowman.png', 'Снеговик', -4, -42, 16)
ov_owl_sh = overlay_actor('Тень_Сова', 'shadow.png', 'Сова', 0, 32, 16)

# Параллакс-слои фонов: дальний слой (небо + силуэты), звёздное небо,
# облака и ближний слой (земля/дома) — сдвигаются при движении Милы.
parallax_actors = {}
for pkey, fn, z in [
    ('far_city', 'bg_city_far.png', 2),
    ('far_forest', 'bg_forest_far.png', 2),
    ('far_roof', 'bg_roof_far.png', 2),
    ('stars', 'stars_sky_0.png', 4),
    ('stars2', 'stars_sky_1.png', 4),
    ('stars3', 'stars_sky_2.png', 4),
    ('clouds', 'clouds_sky.png', 5),
    ('near_city', 'bg_city_near.png', 6),
    ('near_forest', 'bg_forest_near.png', 6),
    ('near_roof', 'bg_roof_near.png', 6),
]:
    t = Target(f'Параллакс_{pkey}')
    # stars/clouds — в art/ui, остальные — в art/backgrounds
    t.costume('ов', f'{U}/{fn}' if pkey in ('stars', 'stars2', 'stars3', 'clouds')
              else f'{BG}/{fn}')
    t.size = 100
    t.visible = False
    t.script(when_flag(), hide())
    t.script(when_bcast('Сброс'), hide())
    t.script(when_bcast('Стоп'), hide())
    # управление по broadcast: «Пара_<название>» — показать
    t.script(when_bcast(f'Пара_{pkey}'), show())
    parallax_actors[pkey] = t
# звёздам — три костюма для мерцания
for pkey in ('stars', 'stars2', 'stars3'):
    for i in (0, 1, 2):
        parallax_actors[pkey].costume(f'{i}', f'{U}/stars_sky_{i}.png')

# виньетка: статичный оверлей, затемняет края экрана (внизу слоя)
vgn = Target('Виньетка')
vgn.costume('ов', f'{BG}/overlay_vignette.png')
vgn.size = 100
vgn.visible = False
vgn.script(when_flag(), hide(), goto(0, 0))
vgn.script(when_bcast('Сброс'), hide())
vgn.script(when_bcast('Стоп'), hide())
vgn.script(when_bcast('ВиньеткаВкл'), show(), to_back())

# Скрипты параллакс-слоёв: мерцание звёзд и сдвиг при движении Милы
parallax_actors['stars'].script(when_flag(), forever(
    wait(rnd(0.8, 1.6)),
    costume('1'), wait(rnd(0.8, 1.6)),
    costume('2'), wait(rnd(0.8, 1.6)),
    costume('0')))
parallax_actors['stars2'].script(when_flag(), forever(
    wait(rnd(0.8, 1.6)),
    costume('2'), wait(rnd(0.8, 1.6)),
    costume('0'), wait(rnd(0.8, 1.6)),
    costume('1')))
parallax_actors['stars3'].script(when_flag(), forever(
    wait(rnd(0.8, 1.6)),
    costume('1'), wait(rnd(0.8, 1.6)),
    costume('2'), wait(rnd(0.8, 1.6)),
    costume('0')))
for pkey, factor in [('far_city', 0.12), ('far_forest', 0.12), ('far_roof', 0.12),
                     ('stars', 0.05), ('stars2', 0.05), ('stars3', 0.05),
                     ('clouds', 0.08), ('near_city', 0.25),
                     ('near_forest', 0.25), ('near_roof', 0.25)]:
    parallax_actors[pkey].script(when_flag(), forever(
        goto(mul(factor, of_prop('Мила', 'x position')), 0), wait(0.05)))


# =================================================================  РЕЖИССЁР
d = Target('Режиссёр')
d.costume('px', f'{U}/px.png')
d.visible = False
d.x, d.y = 0, 0
d.var('играющая', 0)

# по флагу сразу показываем мастерскую и титр, затем запускаем сценарий
d.script(when_flag(),
         setv('старт_идёт', 0),
         backdrop('мастерская'),
         bcast('Старт'))

d.script(when_bcast('Рестарт'), bcast('Старт'))

act1 = [
    setv('акт', 1), setv('скорость', 4.2),
    setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06), setv('музыка', 2),
    bcast_wait('Затемнить'), backdrop('город'), bcast_wait('Осветлить'),
    bcast('Пара_far_city'), bcast('Пара_near_city'),
    bcast('Пара_stars'), bcast('Пара_stars2'), bcast('Пара_stars3'),
    bcast('Пара_clouds'),
    bcast('Акт1'),
    until(or_(gt(var('звёзды'), 4), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    bcast_wait('Реп5'),
    setv('акт', 0), bcast('Стоп'), wait(0.3),
]

act2 = [
    setv('акт', 2), setv('скорость', 6.5),
    bcast('ВиньеткаВкл'),
    # каждый акт — свой заход: сердечки восстанавливаются, счёт звёзд начинается с 0,
    # чтобы на табло всегда было видно «сколько ещё до цели» (5 звёзд за акт)
    setv('жизни', 3), setv('звёзды', 0),
    setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06), setv('музыка', 3),
    bcast_wait('Затемнить'), backdrop('лес'), bcast_wait('Осветлить'),
    bcast('Пара_far_forest'), bcast('Пара_near_forest'),
    bcast('Пара_stars'), bcast('Пара_stars2'), bcast('Пара_stars3'),
    bcast('Акт2'),
    until(or_(gt(var('звёзды'), 4), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    setv('акт', 0), bcast('Стоп'), wait(0.3),
]

act3 = [
    setv('акт', 3), setv('скорость', 6), setv('осталось', 20),
    setv('жизни', 3),
    bcast('ВиньеткаВкл'),
    setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06), setv('музыка', 4),
    bcast_wait('Затемнить'), backdrop('крыша'), bcast_wait('Осветлить'),
    bcast('Пара_far_roof'), bcast('Пара_near_roof'),
    bcast_wait('Реп6'),
    bcast('Акт3'),
    until(or_(lt(var('осталось'), 1), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    setv('акт', 0), bcast('Стоп'), wait(0.3),
    ifelse(alive(), [setv('победа', 1)], [setv('победа', 0)]),
]

win = [
    setv('игра', 0), setv('старт_идёт', 0), setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06),
    bcast('ВиньеткаВкл'),
    bcast_wait('Затемнить'), backdrop('победа'), bcast_wait('Осветлить'),
    setv('музыка', 5),
    bcast_wait('Победа'),
    bcast_wait('Реп8'),
    bcast_wait('Реп10'),
]

lose = [
    setv('игра', 0), setv('старт_идёт', 0), setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06),
    bcast('ВиньеткаВкл'),
    bcast_wait('Затемнить'), backdrop('проигрыш'), bcast_wait('Осветлить'),
    setv('музыка', 6),
    bcast_wait('Проигрыш'),
    bcast_wait('Реп9'),
]

d.script(
    when_bcast('Старт'),
    setv('игра', 0), setv('акт', 0), setv('жизни', 3), setv('звёзды', 0),
    setv('время', 150), setv('победа', 0), setv('неуязвим', 0),
    setv('скорость', 6), setv('ветер', 0.4), setv('осталось', 0),
    setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06),
    bcast('Сброс'), backdrop('мастерская'), wait(0.4),
    bcast('СнегИдёт'),
    # параллакс-слои + звёзды + облака + виньетка. В прологе (дневная
    # мастерская) параллакс/звёзды скрыты — включаются по актам.
    bcast('ВиньеткаВкл'),
    setv('игра', 1),
    setv('музыка', 1),
    bcast_wait('Реп1'), bcast_wait('Реп2'), bcast_wait('Реп3'), bcast_wait('Реп4'),
    act1,
    if_(alive(), act2),
    if_(alive(), act3),
    ifelse(eq(var('победа'), 1), win, lose),
)

# общий таймер «до полуночи» — идёт только во время актов
d.script(when_flag(),
         forever(wait(1),
                 if_(gt(var('акт'), 0), changev('время', -1))))

# обратный отсчёт третьего акта
d.script(when_bcast('Акт3'),
         until(not_act(3),
               wait(1),
               # не уходим в минус: на табло должен остаться 0
               if_(gt(var('осталось'), 0), changev('осталось', -1)),
               if_(eq(var('осталось'), 12), bcast('Реп7'))))

# ==================================================================  МИЛА
h = Target('Мила')
for n in ('idle', 'run', 'jump', 'cheer'):
    h.costume(n, f'{S}/goat_{n}.png')
# кадры мигания (закрытые глаза) и дополнительный кадр бега (шаг ног)
for n in ('idle', 'run', 'jump', 'cheer'):
    h.costume(f'{n}_blink', f'{S}/goat_{n}_blink.png')
h.costume('run_b', f'{S}/goat_run_b.png')
h.sound('голос_3', f'{V}/03_goat_1.mp3')
h.sound('голос_5', f'{V}/05_goat_2.mp3')
h.sound('голос_7', f'{V}/07_goat_3.mp3')
h.sound('голос_9', f'{V}/09_lose.mp3')
h.sound('прыжок', f'{F}/sfx_jump.mp3')
h.sound('приземление', f'{F}/sfx_land.mp3')
h.sound('подбор', f'{F}/sfx_pickup.mp3')
h.sound('удар', f'{F}/sfx_hit.mp3')
h.size = HERO_SIZE
h.rotation_style = 'left-right'
h.var('vy', 0)
h.var('на_земле', 1)
h.var('поза', 'idle')   # текущая поза (idle/run/jump/cheer) — для мигания
h.var('шаг', 0)         # счётчик кадров бега
h.var('миг', 0)         # флаг мигания (защита от конфликта с чередованием кадров)
h.var('покачка', 0)     # пролог-анимация Милы активна (до Акт1, не в финале)

h.script(when_flag(),
         hide(), set_size(HERO_SIZE), rotation_style('left-right'), point_dir(90),
         bcast('Вкл_Тень_Мила'), bcast('Вкл_Снег_Мила'),
         clear_fx(), setv('vy', 0), setv('на_земле', 1), setv('поза', 'idle'),
         setv('шаг', 0), setv('миг', 0))

h.script(when_bcast('Сброс'),
         hide(), clear_fx(), set_size(HERO_SIZE), set_effect('GHOST', 0),
         setv('vy', 0), setv('на_земле', 1), setv('поза', 'idle'),
         setv('шаг', 0), setv('миг', 0), goto(-150, GROUND), point_dir(90))

h.script(when_bcast('Стоп'), hide(), set_effect('GHOST', 0),
         bcast('Скр_Тень_Мила'), bcast('Скр_Снег_Мила'))

# --- мигание: раз в ~3.4 с на 0.12 с переключаем костюм на «закрытые глаза»
#    текущей позы, затем возвращаем. Поза хранится в «поза»; флаг «миг»
#    запрещает чередованию кадров бега менять костюм во время мигания.
h.script(when_flag(), forever(
        wait(3.4),
        setv('миг', 1),
        if_(eq(var('поза'), 'idle'), costume('idle_blink')),
        if_(eq(var('поза'), 'run'), costume('run_blink')),
        if_(eq(var('поза'), 'jump'), costume('jump_blink')),
        if_(eq(var('поза'), 'cheer'), costume('cheer_blink')),
        wait(0.12),
        if_(eq(var('поза'), 'idle'), costume('idle')),
        if_(eq(var('поза'), 'run'), costume('run')),
        if_(eq(var('поза'), 'jump'), costume('jump')),
        if_(eq(var('поза'), 'cheer'), costume('cheer')),
        setv('миг', 0),
        wait(0.2)))

# --- Акт 1: бег с прыжками
h.script(when_bcast('Акт1'),
         show(), set_size(HERO_SIZE), goto(-150, GROUND), point_dir(90),
         setv('покачка', 0),
         costume('run'), setv('поза', 'run'), setv('шаг', 0),
         setv('vy', 0), setv('на_земле', 1), set_effect('GHOST', 0),
         until(not_act(1),
               if_(and_(key('space'), eq(var('на_земле'), 1)),
                   setv('vy', 15), setv('на_земле', 0), play('прыжок'),
                   costume('jump'), setv('поза', 'jump')),
               change_y(var('vy')),
               changev('vy', -1.3),
               if_(lt(y_pos(), GROUND),
                   set_y(GROUND), setv('vy', 0),
                   if_(eq(var('на_земле'), 0), play('приземление')),
                   setv('на_земле', 1), costume('run'), setv('поза', 'run')),
               # анимация бега: чередование кадров шага (ноги кажутся движущимися)
               if_(and_(and_(eq(var('на_земле'), 1), eq(var('поза'), 'run')),
                        eq(var('миг'), 0)),
                   changev('шаг', 1),
                   if_(eq(mod(var('шаг'), 7), 0), costume('run_b'), costume('run'))),
               wait(0))
               )
# --- Акт 2: полёт на санях, управление вверх/вниз
h.script(when_bcast('Акт2'),
         show(), set_size(HERO_SIZE), goto(-130, -60), point_dir(90),
         costume('run'), setv('поза', 'run'), set_effect('GHOST', 0),
         until(not_act(2),
               if_(key('up arrow'), change_y(3.4)),
               if_(key('down arrow'), change_y(-3.4)),
               if_(gt(y_pos(), 95), set_y(95)),
               if_(lt(y_pos(), -54), set_y(-54)),
               wait(0)))

# --- Акт 3: крыша, бег влево-вправо + прыжок
h.script(when_bcast('Акт3'),
         show(), set_size(HERO_SIZE), goto(-150, GROUND), point_dir(90),
         costume('run'), setv('поза', 'run'), setv('шаг', 0),
         setv('vy', 0), setv('на_земле', 1), set_effect('GHOST', 0),
         until(not_act(3),
               if_(key('left arrow'), change_x(-4), point_dir(-90)),
               if_(key('right arrow'), change_x(4), point_dir(90)),
               if_(gt(x_pos(), 210), set_x(210)),
               if_(lt(x_pos(), -210), set_x(-210)),
               if_(and_(key('space'), eq(var('на_земле'), 1)),
                   setv('vy', 15), setv('на_земле', 0), play('прыжок'),
                   costume('jump'), setv('поза', 'jump')),
               change_y(var('vy')),
               changev('vy', -1.3),
               if_(lt(y_pos(), GROUND),
                   set_y(GROUND), setv('vy', 0),
                   if_(eq(var('на_земле'), 0), play('приземление')),
                   setv('на_земле', 1), costume('run'), setv('поза', 'run')),
               if_(and_(and_(eq(var('на_земле'), 1), eq(var('поза'), 'run')),
                        eq(var('миг'), 0)),
                   changev('шаг', 1),
                   if_(eq(mod(var('шаг'), 7), 0), costume('run_b'), costume('run'))),
               wait(0)))

# --- удар: неуязвимость и мерцание (не даёт потерять 3 жизни за секунду)
h.script(when_bcast('Хит'),
         # жизни не уходят в минус: удар засчитывается, только пока они есть
         if_(and_(eq(var('неуязвим'), 0), gt(var('жизни'), 0)),
             setv('неуязвим', 1), changev('жизни', -1), play('удар'),
             repeat(14, set_effect('GHOST', 60), wait(0.09), set_effect('GHOST', 0), wait(0.09)),
             setv('неуязвим', 0)))

h.script(when_bcast('Победа'), show(), clear_fx(), goto(118, -72), set_size(30),
         costume('cheer'), setv('поза', 'cheer'),
         repeat(6, change_y(12), wait(0.09), change_y(-12), wait(0.09)))

h.script(when_bcast('Проигрыш'), show(), clear_fx(), goto(-140, -80), set_size(HERO_SIZE),
         costume('idle'), setv('поза', 'idle'), point_dir(90), set_effect('GHOST', 25))

# --- реплики: текст показывает спрайт «Плашка» (субтитры внизу),
#     здесь — только озвучка и мизансцена. Никаких облачков над сценой.
h.script(when_bcast('Реп2'), show(), goto(95, -78), set_size(HERO_SIZE),
         costume('idle'), setv('поза', 'idle'), point_dir(90), clear_fx(),
         setv('покачка', 1))
# --- первая сцена (пролог): Козочка стоит на сцене и оживает — плавная
#     покачка влево-вправо + дыхание (анимация везде, не только в финале).
#     Скрипт на флаге (не на рассылке): forever на рассылке блокировал бы
#     bcast_wait('Реп2') в режиссёре. Покачка бездействует в Акт1+ (акт != 0),
#     где положение Милы управляется её сценарием — без конфликта.
h.script(when_flag(), forever(
        if_(eq(var('покачка'), 1),
            set_x(add(95, mul(7, mathop('sin', mul(timer(), 1.6))))),
            set_y(add(-78, mul(3, mathop('sin', mul(timer(), 1.6)))))),
        wait(0.05)))
h.script(when_bcast('Реп3'), play('голос_3'))
h.script(when_bcast('Реп5'), play('голос_5'))
h.script(when_bcast('Реп7'), play('голос_7'))
h.script(when_bcast('Реп9'), play('голос_9'))

# ==================================================================  САНИ
sl = Target('Сани')
sl.costume('сани', f'{S}/sleigh.png')
sl.sound('вжух', f'{F}/sfx_swoosh.mp3')
sl.size = 38
sl.visible = False
sl.script(when_flag(), hide())
sl.script(when_bcast('Сброс'), hide())
sl.script(when_bcast('Стоп'), hide())
# сани — транспорт для доставки посылки. В акте 1 Мила бежит, сани следуют за
# ней по земле и прыгают вместе с ней через сугробы (результат сперва висел
# в воздухе над Миной: offset по y был -14 вместо -43). В акте 2 — полёт на
# санях через лес: платформа саней точно под ногами Милы.
sl.script(when_bcast('Акт1'),
         show(), set_size(15), to_back(), reset_timer(),
         bcast('Вкл_Тень_Сани'),
         until(not_act(1),
               # лёгкая тряска беготни: вертикальный кач + слегка кренится
               goto(add(of_prop('Мила', 'x position'), -60),
                    add(add(of_prop('Мила', 'y position'), -38.4),
                        mul(2.5, mathop('sin', mul(timer(), 10))))),
               point_dir(add(90, mul(3, mathop('sin', mul(timer(), 10))))),
               wait(0)))
sl.script(when_bcast('Акт2'),
         show(), set_size(30), to_back(), reset_timer(),
         bcast('Вкл_Тень_Сани'),
         until(not_act(2),
               # полёт: плавный кач и ленивый крен саней в воздухе
               goto(add(of_prop('Мила', 'x position'), -6),
                    add(add(of_prop('Мила', 'y position'), -51),
                        mul(5, mathop('sin', mul(timer(), 6))))),
               point_dir(add(90, mul(5, mathop('sin', mul(timer(), 6))))),
               wait(0)))
sl.script(when_bcast('Акт3'), hide(), bcast('Скр_Тень_Сани'))

# ================================================================  ПОДАРОК
g = Target('Подарок')
g.costume('подарок', f'{S}/gift.png')
g.sound('магия', f'{F}/sfx_magic.mp3')
g.size = 11
g.visible = False
g.script(when_flag(), hide())
g.script(when_bcast('Сброс'), hide())
g.script(when_bcast('Стоп'), hide(), bcast('Скр_Тень_Подарок'))
gift_spot = {1: (-34, 8, 9), 2: (8, -61, 10), 3: (-34, 4, 9)}
for n in (1, 2, 3):
    gx, gy, gs = gift_spot[n]
    g.script(when_bcast(f'Акт{n}'),
             show(), set_size(gs),
             until(not_act(n),
                   # в санях — впереди героини, в беге — за спиной: не висит в воздухе
                   goto(add(of_prop('Мила', 'x position'), gx), add(of_prop('Мила', 'y position'), gy)),
                   ))
    # мерцание — отдельным скриптом, иначе оно тормозило слежение
    g.script(when_bcast(f'Акт{n}'),
             until(not_act(n),
                   repeat(10, change_effect('BRIGHTNESS', 2), wait(0.04),
                          change_effect('BRIGHTNESS', -2), wait(0.04))))
g.script(when_bcast('Победа'), show(), goto(-92, -92), set_size(12), play('магия'),
         bcast('Вкл_Тень_Подарок'),
         repeat(30, turn_right(6), wait(0.03)))

# ==================================================================  ЗВЕЗДА
st = Target('Звезда')
st.costume('звезда', f'{S}/star.png')
st.sound('подбор', f'{F}/sfx_pickup.mp3')
st.size = 11
st.visible = False
st.var('клон', 0)
st.script(when_flag(), hide(), setv('клон', 0))
st.script(when_bcast('Сброс'), hide())
st.script(when_bcast('Стоп'), hide(), bcast('Скр_Тень_Звезда'))
st.script(when_bcast('Стоп'), delete_clone())

for n, period in [(1, 0.9), (2, 0.8)]:
    # рассылки запускают обработчики и в клонах, поэтому клонирует только оригинал
    st.script(when_bcast(f'Акт{n}'),
             hide(),
             if_(eq(var('клон'), 0),
                 wait(1.2),
                 until(not_act(n),
                       clone_self(),
                       wait(rnd(period, period + 0.5)),
                       )))

# ВАЖНО: скрипт клона должен быть РОВНО ОДИН. Пока он объявлялся внутри цикла
# по актам, в спрайте оказывались два одинаковых «когда я — клон»: второй
# (для акта 2) в первом акте сразу видел «акт <> 2», выходил из цикла и удалял
# звезду в момент рождения — поэтому звёзды не долетали до Милы.
st.script(when_clone(), setv('клон', 1), show(), set_size(rnd(11, 14)), point_dir(0),
         bcast('Вкл_Тень_Звезда'),
          # высота под акт: в первом акте только та, до которой Мила достаёт прыжком
          ifelse(eq(var('акт'), 1),
                 [goto(270, rnd(-100, -20))],
                 [goto(270, rnd(-52, 62))]),
          until(or_(lt(x_pos(), -270), eq(var('акт'), 0)),
                change_x(mul(-1, var('скорость'))),
                turn_right(4),
                if_(touching('Мила'), changev('звёзды', 1), play('подбор'), delete_clone()),
                # шаг = кадр: скорость не зависит от мощности компьютера
                wait(0)),
          delete_clone())

# ==================================================================  СУГРОБ
dr = Target('Сугроб')
dr.costume('сугроб', f'{S}/snowdrift.png')
dr.size = 24
dr.visible = False
dr.var('клон', 0)
dr.script(when_flag(), hide(), setv('клон', 0))
dr.script(when_bcast('Сброс'), hide())
dr.script(when_bcast('Стоп'), hide(), bcast('Скр_Тень_Сугроб'))
dr.script(when_bcast('Стоп'), delete_clone())
dr.script(when_bcast('Акт1'),
         hide(),
         if_(eq(var('клон'), 0),
             wait(1.6),
             until(not_act(1),
                   clone_self(),
                   wait(rnd(3.2, 4.4)),
                   )))
dr.script(when_clone(), setv('клон', 1),
         show(), set_size(rnd(14, 17)), goto(280, -116),
         bcast('Вкл_Тень_Сугроб'),
         until(or_(lt(x_pos(), -280), not_act(1)),
               change_x(mul(-1, var('скорость'))),
               # заденет, только если Мила низко (прыжок переносит её через сугроб)
               # задевает, ТОЛЬКО пока Мила стоит на земле: любой прыжок спасает
               if_(and_(and_(near_x('Мила', 20), lt(of_prop('Мила', 'y position'), GROUND + 2)),
                        eq(var('неуязвим'), 0)),
                   bcast('Хит'), delete_clone()),
               wait(0)),
         delete_clone())

# ===================================================================  ЁЛКА
tr = Target('Ёлка')
tr.costume('ёлка', f'{S}/tree.png')
tr.size = 28
tr.visible = False
tr.var('клон', 0)
tr.script(when_flag(), hide(), setv('клон', 0))
tr.script(when_bcast('Сброс'), hide())
tr.script(when_bcast('Стоп'), hide(), bcast('Скр_Тень_Снежок'))
tr.script(when_bcast('Стоп'), delete_clone())
tr.script(when_bcast('Акт2'),
         hide(),
         if_(eq(var('клон'), 0),
             wait(1.4),
             until(not_act(2),
                   clone_self(),
                   wait(rnd(2.6, 3.4)),
                   )))
tr.script(when_clone(), setv('клон', 1),
         show(), set_size(rnd(12, 15)), goto(280, rnd(-100, -66)),
         bcast('Вкл_Тень_Снежок'),
         until(or_(lt(x_pos(), -280), not_act(2)),
               change_x(mul(-1, var('скорость'))),
               turn_right(1),
               if_(and_(and_(near_x('Мила', 24), near_y('Мила', 34)), eq(var('неуязвим'), 0)),
                   bcast('Хит'), delete_clone()),
               wait(0)),
         delete_clone())

# =================================================================  СНЕЖОК
sn = Target('Снежок')
sn.costume('снежок', f'{S}/snowball.png')
sn.sound('снежок_удар', f'{F}/sfx_snowball.mp3')
sn.size = 12
sn.visible = False
sn.var('клон', 0)
sn.script(when_flag(), hide(), setv('клон', 0))
sn.script(when_bcast('Сброс'), hide())
sn.script(when_bcast('Стоп'), hide())
sn.script(when_bcast('Стоп'), delete_clone())
sn.script(when_bcast('Акт3'),
         hide(),
         if_(eq(var('клон'), 0),
             wait(1.0),
             until(not_act(3),
                   clone_self(),
                   wait(rnd(1.3, 2.0)),
                   )))
sn.script(when_clone(), setv('клон', 1),
         show(), goto(of_prop('Метель', 'x position'), of_prop('Метель', 'y position')),
         point_towards('Мила'), turn_right(rnd(-12, 12)),
         until(or_(touching('_edge_'), not_act(3)),
               move_steps(6.5),
               if_(touching('Мила'), play('снежок_удар'), bcast('Хит'), delete_clone()),
               wait(0)))

# ====================================================================  СНЕГ
snow = Target('Снег')
# раньше здесь стоял stars_0.png — картинка HUD «★ 0», из-за неё по экрану
# летали золотые звёздочки с нулями вместо снега
snow.costume('снежинка', f'{U}/snowflake.png')
snow.size = 8
snow.visible = False
snow.var('клон', 0)
snow.script(when_flag(), hide())
snow.script(when_bcast('Сброс'), hide(), delete_clone())
# клоны помечают себя, чтобы не размножались при повторных рассылках
snow.script(when_clone(), setv('клон', 1))
snow.script(when_bcast('СнегИдёт'),
            if_(eq(var('клон'), 0), repeat(26, clone_self(), wait(0.02))))
snow.script(when_clone(),
            show(), set_size(rnd(5, 12)), set_effect('GHOST', rnd(25, 70)),
            goto(rnd(-250, 250), rnd(-180, 180)),
            forever(
                change_y(mul(rnd(1, 3), -1)),
                change_x(var('ветер')),
                if_(lt(y_pos(), -190), set_y(190), set_x(rnd(-250, 250))),
                if_(gt(x_pos(), 250), set_x(-250)),
                if_(lt(x_pos(), -250), set_x(250)),
                wait(0)))

# ===================================================================  МЕТЕЛЬ
mt = Target('Метель')
mt.costume('метель', f'{S}/storm.png')
mt.sound('голос_6', f'{V}/06_storm.mp3')
mt.sound('ветер', f'{F}/sfx_wind.mp3')
mt.size = 38
mt.visible = False
mt.script(when_flag(), hide())
mt.script(when_bcast('Сброс'), hide(), clear_fx())
mt.script(when_bcast('Стоп'), hide())
mt.script(when_bcast('Реп6'),
         show(), goto(140, 45), set_size(34), clear_fx(), point_dir(90),
         play('голос_6'))
mt.script(when_bcast('Акт3'),
         show(), goto(150, 40), set_size(34), clear_fx(), point_dir(90),
         until(not_act(3),
               set_y(rnd(10, 88)),
               turn_right(rnd(-3, 3)),
               if_(eq(mod(var('время'), 4), 0), play('ветер')),
               wait(1.1),
               ))

# ==================================================================  ДЕД МОРОЗ
dm = Target('ДедМороз')
dm.costume('дедмороз', f'{S}/santa.png')
dm.costume('мороз_бlink', f'{S}/santa_blink.png')
for nm, fn in [('осн', 'osn'), ('лево', 'lewo'), ('право', 'prawo')]:
    dm.costume(nm, f'{S}/santa_{fn}.png')
for nm, fn in [('голос_1', '01_narrator'), ('голос_2', '02_santa'),
               ('голос_8', '08_final'), ('голос_10', '10_outro')]:
    dm.sound(nm, f'{V}/{fn}.mp3')
dm.size = 42
dm.visible = False
dm.rotation_style = 'left-right'
dm.var('на_сцене', 0)   # на сцене? (для мигания/дыхания/движения)
dm.var('осн_x', -120)   # основание x (основная позиция на сцене)
dm.var('осн_y', -60)    # основание y для «дыхания»
dm.var('миг', 0)        # счётчик покачиваний
dm.script(when_flag(), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Сброс'), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Стоп'), hide(), setv('на_сцене', 0))
# Пролог: реплику 1 говорит голос за кадром поверх титра — Дед Мороз ещё не вышел.
# Выходит на реплике 2 слева и остаётся до акта. В актах 1–2 его на сцене НЕТ
# (раньше он стоял посреди улицы до самой крыши).
dm.script(when_bcast('Реп1'), hide(), setv('на_сцене', 0), play('голос_1'))
dm.script(when_bcast('Реп2'),
         show(), goto(-120, -60), set_size(34), costume('осн'), point_dir(90),
         bcast('Вкл_Тень_ДедМороз'), bcast('Вкл_Снег_ДедМороз'),
         setv('на_сцене', 1), setv('осн_x', -120), setv('осн_y', -60), setv('миг', 0),
         reset_timer(), play('голос_2'))
dm.script(when_bcast('Реп8'),
         show(), goto(-140, -75), set_size(28), costume('осн'), point_dir(90),
         bcast('Вкл_Тень_ДедМороз'), bcast('Вкл_Снег_ДедМороз'),
         setv('на_сцене', 1), setv('осн_x', -140), setv('осн_y', -75), setv('миг', 0),
         reset_timer(), play('голос_8'))
dm.script(when_bcast('Реп10'), play('голос_10'))
dm.script(when_bcast('Акт1'), hide(), setv('на_сцене', 0),
         bcast('Скр_Тень_ДедМороз'), bcast('Скр_Снег_ДедМороз'))
dm.script(when_bcast('Акт2'), hide(), setv('на_сцене', 0),
         bcast('Скр_Тень_ДедМороз'), bcast('Скр_Снег_ДедМороз'))
dm.script(when_bcast('Акт3'), hide(), setv('на_сцене', 0),
         bcast('Скр_Тень_ДедМороз'), bcast('Скр_Снег_ДедМороз'))
dm.script(when_bcast('Проигрыш'), hide(), setv('на_сцене', 0),
         bcast('Скр_Тень_ДедМороз'), bcast('Скр_Снег_ДедМороз'))
# пухли-снега: слетают на шапку и тают (пока Дед Мороз на сцене)
dm.script(when_bcast('Старт'), forever(
    wait(0.6),
    if_(eq(var('на_сцене'), 1), bcast('Пухляк')),
    wait(0.6)))
# мигание + «дыхание» + покачивание влево-вправо (анимация движения) — только когда на сцене
dm.script(when_flag(), forever(
        wait(0.35),
        if_(eq(var('на_сцене'), 1),
            set_y(add(var('осн_y'), mul(5, mathop('sin', mul(timer(), 2)))))),
        wait(1.7),
        if_(eq(var('на_сцене'), 1), costume('мороз_бlink')),
        wait(0.3),
        if_(eq(var('на_сцене'), 1), costume('осн')),
        # покачивание: шаг влево, шаг вправо, обратно к основанию
        if_(eq(var('на_сцене'), 1),
            if_(eq(mod(var('миг'), 3), 1),
                goto(add(var('осн_x'), -11), add(var('осн_y'), 2)), costume('лево')),
            if_(eq(mod(var('миг'), 3), 2),
                goto(add(var('осн_x'), 11), add(var('осн_y'), 2)), costume('право')),
        ),
        wait(0.25),
        if_(eq(var('на_сцене'), 1),
            goto(var('осн_x'), add(var('осн_y'), mul(5, mathop('sin', mul(timer(), 2))))),
            costume('осн')),
        wait(0.25),
        if_(eq(var('на_сцене'), 1), setv('миг', add(var('миг'), 1)))))

# свечение глаз Снеговика (угольки-глаза мерцают в темноте)
sm_glow = Target('ГлазСнег')
sm_glow.costume('ов', f'{S}/glow_snowman.png')
sm_glow.size = 40
sm_glow.visible = False
sm_glow.script(when_bcast('Старт'), hide(), set_effect('GHOST', 0), goto(0, 0))
sm_glow.script(when_bcast('Сброс'), hide(), set_effect('GHOST', 0))
sm_glow.script(when_bcast('Стоп'), hide())
sm_glow.script(when_bcast('Скр_ГлазСнег'), hide())
sm_glow.script(when_bcast('Вкл_ГлазСнег'), show())

# =================================================================  СНЕГОВИК
sm = Target('Снеговик')
sm.costume('снеговик', f'{S}/snowman.png')
sm.costume('снег_бlink', f'{S}/snowman_blink.png')
for nm, fn in [('осн', 'snow_osn'), ('лево', 'snow_left'), ('право', 'snow_right')]:
    sm.costume(nm, f'{S}/{fn}.png')
sm.sound('голос_4', f'{V}/04_snowman.mp3')
sm.sound('скрип', f'{F}/sfx_step.mp3')
sm.size = 20
sm.visible = False
# без этого «повернуть в направление -90» крутило снеговика на 180° —
# в прологе он стоял вверх ногами (стиль «влево-вправо» только отражает спрайт)
sm.rotation_style = 'left-right'
sm.var('на_сцене', 0)
sm.var('осн_x', 185)
sm.var('осн_y', -88)
sm.var('миг', 0)
sm.script(when_flag(), hide(), setv('на_сцене', 0))
sm.script(when_bcast('Сброс'), hide(), setv('на_сцене', 0))
sm.script(when_bcast('Стоп'), hide(), setv('на_сцене', 0))
sm.script(when_bcast('Реп4'),
         show(), goto(185, -88), set_size(18), costume('осн'), point_dir(-90),
         bcast('Вкл_Тень_Снеговик'), bcast('Вкл_Снег_Снеговик'),
         bcast('Вкл_ГлазСнег'),
         setv('на_сцене', 1), setv('осн_x', 185), setv('осн_y', -88), setv('миг', 0),
         reset_timer(), play('голос_4'))
# свечение глаз: мерцает и следует за Снеговиком, пока он на сцене
sm_glow.script(when_bcast('Реп4'), show(),
               goto(of_prop('Снеговик', 'x position'),
                    add(of_prop('Снеговик', 'y position'), -8)))
sm_glow.script(when_bcast('Старт'), forever(
    wait(0.3),
    if_(gt(of_prop('Снеговик', 'y position'), -900),
        goto(of_prop('Снеговик', 'x position'),
             add(of_prop('Снеговик', 'y position'), -8)),
        repeat(12, change_effect('GHOST', 12), wait(0.06),
               change_effect('GHOST', -12), wait(0.06))),
    wait(0.3)))
sm.script(when_bcast('Акт1'), hide(), setv('на_сцене', 0),
         bcast('Скр_Тень_Снеговик'), bcast('Скр_Снег_Снеговик'),
         bcast('Скр_ГлазСнег'))
# пухли-снега: слетают на шапку и тают (пока Снеговик на сцене)
sm.script(when_bcast('Старт'), forever(
        wait(0.5),
        if_(eq(var('на_сцене'), 1), bcast('Пухляк2')),
        wait(0.5)))
# мигание + «дыхание» + покачивание влево-вправо (анимация движения) — только когда на сцене
sm.script(when_flag(), forever(
        wait(0.35),
        if_(eq(var('на_сцене'), 1),
            set_y(add(var('осн_y'), mul(4, mathop('sin', mul(timer(), 2)))))),
        wait(1.7),
        if_(eq(var('на_сцене'), 1), costume('снег_бlink')),
        wait(0.3),
        if_(eq(var('на_сцене'), 1), costume('осн')),
        # покачивание: шаг влево, шаг вправо, обратно к основанию
        if_(eq(var('на_сцене'), 1),
            if_(eq(mod(var('миг'), 3), 1),
                goto(add(var('осн_x'), -12), add(var('осн_y'), 1)), costume('лево')),
            if_(eq(mod(var('миг'), 3), 2),
                goto(add(var('осн_x'), 12), add(var('осн_y'), 1)), costume('право')),
        ),
        wait(0.25),
        if_(eq(var('на_сцене'), 1),
            goto(var('осн_x'), add(var('осн_y'), mul(4, mathop('sin', mul(timer(), 2))))),
            costume('осн')),
        wait(0.25),
        if_(eq(var('на_сцене'), 1), setv('миг', add(var('миг'), 1)))))

# ====================================================================  СОВА
ov = Target('Сова')
ov.costume('сова', f'{S}/owl.png')
ov.costume('взмах', f'{S}/owl_open.png')
ov.sound('уханье', f'{F}/sfx_owl.mp3')
ov.size = 12
ov.visible = False
ov.script(when_flag(), hide())
ov.script(when_bcast('Сброс'), hide())
ov.script(when_bcast('Стоп'), hide(), bcast('Скр_Тень_Сова'))
ov.script(when_bcast('Акт2'),
         show(), goto(-185, 70), set_size(12), costume('сова'),
         bcast('Вкл_Тень_Сова'),
         until(not_act(2),
               set_y(add(70, mul(12, mathop('sin', mul(var('время'), 60))))),
               # взмахи крыльями: чередование костюмов (крыло поднято/опущено)
               next_costume(),
               if_(eq(mod(var('время'), 5), 0), play('уханье')),
               # свечение глаз Совы в полёте
               bcast('СовГлаз'),
               wait(0.35),
               ))

# ===================================================================  ЧАСЫ
# Циферблат + две стрелки (минутная и часовая) с центром поворота в основании.
# Стрелки плавно вращаются по переменной «время» — обратный отсчёт до полуночи:
# угол = (150 - время) * скорость. При времени 150 стрелки в 12, при 0 — снова
# в 12 (полный оборот за время актов). Минутная — 2.4°/с, часовая — 0.2°/с.
CW = (196, 126)  # центр часов на табло
cf = Target('Часы_циферблат')
cf.costume('часы', f'{U}/clock_face.png')
for n in range(10):
    cf.costume(f'цифра_{n}', f'{U}/count_{n}.png')
cf.size = 20
cf.x, cf.y = CW
# Счётчик: в Акт3 на циферблате — цифра оставшегося отсчёта (осталось 20->0
# по модулю 10); в прологе/актах 1-2 — обычный циферблат. Циферблат не уходит
# за край экрана (260×260 по размеру 20 = 130 px по центру CW=(196, 126)).
cf.script(when_flag(), show(), to_front(), set_size(20), goto(*CW),
          forever(ifelse(eq(var('акт'), 3),
                         [if_(eq(mod(var('осталось'), 10), n), costume(f'цифра_{n}'))
                          for n in range(10)],
                         [costume('часы')])))
cf.script(when_bcast('Сброс'), show(), to_front(), set_size(20), goto(*CW),
          forever(ifelse(eq(var('акт'), 3),
                         [if_(eq(mod(var('осталось'), 10), n), costume(f'цифра_{n}'))
                          for n in range(10)],
                         [costume('часы')])))

# минутная стрелка: длинная, полный оборот за 150 с (2.4°/с)
cm = Target('Часы_минутная')
cm.costume('минутная', f'{U}/clock_hand_min.png', center=(11, 75))
cm.costume('указатель', f'{U}/clock_hand_min.png', center=(11, 75))
cm.size = 30
cm.x, cm.y = CW
# «указатель» — стрелка во время подсветки цифры счётчика
cm.script(when_flag(), show(), to_front(), set_size(30), goto(*CW),
          forever(point_dir(mul(sub(150, var('время')), 2.4)),
                  costume('указатель')))
cm.script(when_bcast('Сброс'), show(), to_front(), set_size(30), goto(*CW))

# часовая стрелка: короткая, 1/12 скорости минутной (0.2°/с)
ch = Target('Часы_часовая')
ch.costume('часовая', f'{U}/clock_hand_hr.png', center=(15, 48))
ch.costume('указатель', f'{U}/clock_hand_hr.png', center=(15, 48))
ch.size = 22
ch.x, ch.y = CW
ch.script(when_flag(), show(), to_front(), set_size(22), goto(*CW),
          forever(point_dir(mul(sub(150, var('время')), 0.2))))
ch.script(when_bcast('Сброс'), show(), to_front(), set_size(22), goto(*CW))

# ====================================================================  HUD
lv = Target('Жизни')
for n in range(4):
    lv.costume(f'жизни_{n}', f'{U}/lives_{n}.png')
lv.size = 22
lv.x, lv.y = -196, 130
lv.script(when_bcast('Сброс'), show(), to_front(), set_size(22), goto(-196, 130))
lv.script(when_flag(), show(), to_front(), set_size(22), goto(-196, 130),
          forever(
              if_(eq(var('жизни'), 3), costume('жизни_3')),
              if_(eq(var('жизни'), 2), costume('жизни_2')),
              if_(eq(var('жизни'), 1), costume('жизни_1')),
              if_(lt(var('жизни'), 1), costume('жизни_0')),
          ))

sc = Target('Счёт')
for n in range(14):
    sc.costume(f'{n}', f'{U}/stars_{n}.png')
sc.size = 16
sc.x, sc.y = 140, 126
sc.script(when_flag(), show(), to_front(), set_size(16), goto(140, 126))
# БАГ 1.7: «Счёт» скрывался на «Победа» и после «Ещё раз» больше не показывался
# (when_flag не перезапускается). Сброс явно возвращает его на место.
sc.script(when_bcast('Сброс'), show(), to_front(), set_size(16), goto(140, 126))
branches = []
for n in range(14):
    branches.append(if_(eq(var('звёзды'), n), costume(f'{n}')))
branches.append(if_(gt(var('звёзды'), 13), costume('13')))
sc.script(when_flag(), forever(*branches))
sc.script(when_bcast('Победа'), hide())

# ==================================================================  ЭКРАН
ek = Target('Экран')
ek.costume('титр', f'{U}/title.png')
ek.costume('победа', f'{U}/win.png')
ek.costume('проигрыш', f'{U}/lose.png')
ek.costume('подсказка', f'{U}/hint.png')
ek.size = 34
ek.x, ek.y = 0, 40
ek.visible = False
ek.script(when_flag(), hide())
# Титр живёт только на первой реплике (голос за кадром) и уходит в фейд,
# как только Дед Мороз выходит на сцену. Раньше он висел поверх героев и облачка.
ek.script(when_bcast('Реп1'),
         to_front(), goto(0, 58), set_size(34), costume('титр'),
         set_effect('GHOST', 100), show(),
         repeat(10, change_effect('GHOST', -10), wait(0.03)))
ek.script(when_bcast('Реп2'),
         repeat(10, change_effect('GHOST', 10), wait(0.03)), hide())
ek.script(when_bcast('Сброс'), hide(), clear_fx())
ek.script(when_bcast('Стоп'), hide())
ek.script(when_bcast('Затемнить'), hide())
# запасной путь запуска: если что-то пошло не так, клик по титру перезапускает игру
ek.script(when_clicked(), bcast('Рестарт'))
ek.script(when_bcast('Акт1'), hide())
ek.script(when_bcast('Акт2'), hide())
ek.script(when_bcast('Акт3'), hide())
ek.script(when_bcast('Победа'),
         show(), goto(0, 124), set_size(24), costume('победа'), set_effect('GHOST', 100),
         repeat(10, change_effect('GHOST', -10), wait(0.03)))
ek.script(when_bcast('Проигрыш'),
         show(), goto(0, 96), set_size(24), costume('проигрыш'), set_effect('GHOST', 100),
         repeat(10, change_effect('GHOST', -10), wait(0.03)))

# =================================================================  ПЛАШКА
# ЕДИНЫЙ спрайт для ВСЕХ надписей внизу сцены: подсказки актов и субтитры реплик.
# Это принципиально: раньше облачка Scratch рисовались над спрайтами и наезжали
# на титр, персонажей и подсказки. Теперь текст — статичная картинка в нижней
# полосе, а сцена остаётся чистой. Одна точка, один размер => наезд невозможен.
cap = Target('Плашка')
# res=2: плашка нарисована в 2x (960 px = 480 единиц) — при res=1 она была бы
# шириной в два экрана, и Scratch клампил бы размер
for n in (1, 2, 3):
    cap.costume(f'акт{n}', f'{U}/hint{n}.png', res=2)
for n in range(1, 11):
    cap.costume(f'реплика{n}', f'{U}/cap{n}.png', res=2)
cap.size = 100
cap.x, cap.y = 0, CAP_Y
cap.visible = False
cap.script(when_flag(), hide())
cap.script(when_bcast('Сброс'), hide(), clear_fx())
cap.script(when_bcast('Стоп'), hide())
cap.script(when_bcast('Затемнить'), hide())

# подсказки по управлению: своя на каждый акт (управление разное)
for n in (1, 2, 3):
    cap.script(when_bcast(f'Акт{n}'),
               to_front(), goto(0, CAP_Y), set_size(100), costume(f'акт{n}'),
               set_effect('GHOST', 100), show(),
               repeat(6, change_effect('GHOST', -16.7), wait(0.03)),
               wait(4.2),
               repeat(6, change_effect('GHOST', 16.7), wait(0.03)),
               hide())

# субтитры реплик: держатся ровно столько, сколько звучит озвучка
VOICE = {1: '01_narrator', 2: '02_santa', 3: '03_goat_1', 4: '04_snowman',
         5: '05_goat_2', 6: '06_storm', 7: '07_goat_3', 8: '08_final',
         9: '09_lose', 10: '10_outro'}
for n, fn in VOICE.items():
    cap.script(when_bcast(f'Реп{n}'),
               to_front(), goto(0, CAP_Y), set_size(100), costume(f'реплика{n}'),
               set_effect('GHOST', 100), show(),
               repeat(6, change_effect('GHOST', -16.7), wait(0.03)),
               wait(dur(f'{V}/{fn}.mp3')),
               repeat(6, change_effect('GHOST', 16.7), wait(0.03)),
               hide())

# ================================================================  ПОДПИСЬ
# Вторая строка под финальными титрами (есть в ассетах, раньше не использовалась).
# Отдельный спрайт, потому что должна висеть одновременно с титром.
sub = Target('Подпись')
sub.costume('год', f'{U}/s2027_sub.png')
sub.costume('провал', f'{U}/lose_sub.png')
sub.size = 30
sub.visible = False
sub.script(when_flag(), hide())
sub.script(when_bcast('Сброс'), hide())
sub.script(when_bcast('Стоп'), hide())
sub.script(when_bcast('Затемнить'), hide())
sub.script(when_bcast('Победа'),
           to_front(), goto(0, 6), set_size(34), costume('год'),
           set_effect('GHOST', 100), show(),
           repeat(10, change_effect('GHOST', -10), wait(0.03)))
sub.script(when_bcast('Проигрыш'),
           to_front(), goto(0, 52), set_size(30), costume('провал'),
           set_effect('GHOST', 100), show(),
           repeat(10, change_effect('GHOST', -10), wait(0.03)))

# ===================================================================  2027
y27 = Target('2027')
y27.costume('год', f'{U}/s2027.png')
y27.sound('магия', f'{F}/sfx_magic.mp3')
y27.size = 26
y27.visible = False
y27.script(when_flag(), hide())
y27.script(when_bcast('Сброс'), hide())
y27.script(when_bcast('Стоп'), hide())
y27.script(when_bcast('Победа'),
            wait(0.4), show(), goto(0, 64), set_size(10), clear_fx(), play('магия'),
            repeat(12, change_size(2), wait(0.03)),
            repeat(80, change_effect('COLOR', 3), wait(0.03)))

# ================================================================  ФЕЙЕРВЕРК
fw = Target('Фейерверк')
fw.costume('искра', f'{U}/spark.png')
fw.sound('салют', f'{F}/sfx_firework.mp3')
fw.size = 8
fw.visible = False
fw.var('клон', 0)
fw.script(when_flag(), hide(), setv('клон', 0))
fw.script(when_bcast('Сброс'), hide())
fw.script(when_bcast('Стоп'), delete_clone(), hide())
fw.script(when_clone(), setv('клон', 1), hide())
fw.script(when_bcast('Победа'),
         hide(), wait(0.3),
         if_(eq(var('клон'), 0), repeat(10, clone_self(), wait(0.22))))
fw.script(when_clone(), setv('клон', 1),
         show(), goto(rnd(-170, 170), rnd(-20, 100)), set_size(rnd(9, 16)),
         set_effect('COLOR', rnd(0, 100)), play('салют'), point_dir(rnd(0, 360)),
         repeat(24, move_steps(4), turn_right(15), change_effect('GHOST', 4), change_size(-0.2), wait(0.02)),
         delete_clone())

# ================================================================  ЭФФЕКТЫ ФОНОВ
# Анимированные эффекты на сцене: дым (мастерская), огоньки (город), оспы (лес),
# метель (крыша), снег (город/лес), дым и крупные салютные вспышки (победа).
# Все эффекты — в безопасной зоне верхней части сцены (y 10..100), ниже HUD
# (y>=112), и убраны на бэкспейд (to_back), чтобы не перекрывать актёров.
def fx_actor(name, costumes, size, sounds=None):
    """Актор эффекта: скрыт, сброшен, остановлен; клонирует сам себя."""
    t = Target(name)
    for i, c in enumerate(costumes):
        t.costume(c, f'{S}/{c}.png')
    t.size = size
    t.visible = False
    t.var('клон', 0)
    t.script(when_flag(), hide(), setv('клон', 0))
    t.script(when_bcast('Сброс'), delete_clone(), hide(), setv('клон', 0))
    t.script(when_bcast('Стоп'), delete_clone(), hide())
    return t


# --- Дым в мастерской: пыли дымят вверх и рассеиваются
smk = fx_actor('Дым', ['fx_smoke_0', 'fx_smoke_1', 'fx_smoke_2'], 12)
smk.script(when_flag(), show(), to_back(), setv('клон', 0),
           until(eq(var('акт'), 1), clone_self(), wait(1.3)))
smk.script(when_bcast('Сброс'), delete_clone(), hide(), setv('клон', 0),
           show(), to_back(),
           until(eq(var('акт'), 1), clone_self(), wait(1.3)))
smk.script(when_clone(), setv('клон', 1), show(), to_back(),
           goto(rnd(-90, 90), 20), set_size(rnd(10, 16)),
           set_effect('GHOST', 0),
           repeat(30, change_y(2.2), change_x(mul(rnd(-1, 1), 0.8)),
                  change_effect('GHOST', 4), wait(0.06)),
           delete_clone())

# --- Огни/огоньки в городе: мерцающие точки в небе
ln = fx_actor('Огни', ['fx_lantern_0', 'fx_lantern_1', 'fx_lantern_2', 'fx_lantern_3'], 10)
ln.script(when_bcast('Акт1'), show(), to_back(),
          setv('клон', 0), clone_self(), clone_self(), clone_self())
ln.script(when_bcast('Акт2'), delete_clone(), hide())
ln.script(when_clone(), setv('клон', add(var('клон'), 1)), show(), to_back(),
          if_(eq(var('клон'), 1), goto(-240, 55)),
          if_(eq(var('клон'), 2), goto(0, 70)),
          if_(eq(var('клон'), 3), goto(240, 55)),
          forever(next_costume(), wait(0.16)))

# --- Снег уже есть у актёра «Снег» (26 клонов, падающие хлопья) — не дублируем.

# --- Овы в лесу: мерцающие оспы, блуждающие в воздухе
ffl = fx_actor('Оспы', ['fx_firefly_0', 'fx_firefly_1', 'fx_firefly_2', 'fx_firefly_3'], 10)
ffl.script(when_bcast('Акт2'), show(), to_back(),
           until(not_act(2), clone_self(), wait(0.8)))
ffl.script(when_clone(), setv('клон', 1), show(), to_back(),
           goto(rnd(-280, 280), rnd(25, 90)), set_size(rnd(8, 13)),
           repeat(45, change_x(mul(rnd(-1, 1), 1.6)), change_y(mul(rnd(-1, 1), 1.0)),
                  next_costume(), change_effect('GHOST', 3), wait(0.08)),
           delete_clone())

# --- Метель на крыше: хлопья метели, проносящиеся по небу
blz = fx_actor('Метель_фон', ['fx_blizzard_0', 'fx_blizzard_1', 'fx_blizzard_2', 'fx_blizzard_3'], 16)
blz.script(when_bcast('Акт3'), show(), to_back(),
           until(not_act(3), clone_self(), wait(0.7)))
blz.script(when_clone(), setv('клон', 1), show(), to_back(),
           goto(-330, rnd(25, 85)), set_size(rnd(14, 20)),
           until(gt(x_pos(), 340),
                 change_x(7), next_costume(), wait(0.1),
                 if_(gt(x_pos(), 340), goto(-330, rnd(25, 85)), wait(0))),
           delete_clone())

# --- Дым и салют на финальном слайде (победа)
smk2 = fx_actor('Дым_финал', ['fx_smoke_0', 'fx_smoke_1', 'fx_smoke_2'], 14)
smk2.script(when_bcast('Победа'), show(), to_back(),
            until(eq(var('победа'), 0), clone_self(), wait(1.1)))
smk2.script(when_bcast('Проигрыш'), delete_clone(), hide())
smk2.script(when_clone(), setv('клон', 1), show(), to_back(),
            goto(rnd(-160, 160), 10), set_size(rnd(12, 18)),
            set_effect('GHOST', 0),
            repeat(34, change_y(2.4), change_x(mul(rnd(-1, 1), 0.9)),
                   change_effect('GHOST', 3.5), wait(0.06)),
            delete_clone())

# --- Крупные салютные вспышки на победе (в дополнение к искрам Фейерверка)
fw2 = fx_actor('Салюты', ['fx_explosion_0', 'fx_explosion_1', 'fx_explosion_2', 'fx_explosion_3'], 14)
fw2.sound('салют', f'{F}/sfx_firework.mp3')
fw2.script(when_bcast('Победа'), hide(), wait(0.8),
           if_(eq(var('клон'), 0), repeat(6, clone_self(), wait(0.5))))
fw2.script(when_clone(), setv('клон', 1),
           show(), goto(rnd(-150, 150), rnd(40, 110)), set_size(rnd(12, 18)),
           set_effect('COLOR', rnd(0, 100)), play('салют'),
           repeat(20, change_size(1.5), change_effect('GHOST', 5), wait(0.04)),
           delete_clone())

# --- Атмосфера 1.10: пухли-снега на шапках персонажей и свечение глаз
puff_santa = fx_actor('Пухли', ['snow_santa'], 1, [])
puff_snowman = fx_actor('Пухли2', ['snow_snowman'], 1, [])
puff_owl = fx_actor('СовГлаз', ['glow_owl'], 1, [])
# пухли-снега: появляются у персонажа и тают
for pf, tgt, off, bcast_name in [
        (puff_santa, 'ДедМороз', (0, -40), 'Пухляк'),
        (puff_snowman, 'Снеговик', (0, -44), 'Пухляк2'),
        (puff_owl, 'Сова', (0, -30), 'СовГлаз')]:
    pf.script(when_bcast(bcast_name),
              goto(add(of_prop(tgt, 'x position'), off[0]),
                   add(of_prop(tgt, 'y position'), off[1])),
              set_effect('GHOST', 0), show(),
              repeat(14,
                     change_size(rnd(0.8, 1.3)), change_effect('GHOST', 8), wait(0.05)),
              set_effect('GHOST', 0), hide())

# ================================================================  ЗАТЕМНЕНИЕ
fd = Target('Затемнение')
fd.costume('чёрный', f'{U}/fade.png')
fd.costume('завеса', f'{U}/veil_snow.png')
fd.size = 100
fd.visible = True
fd.script(when_flag(), to_front(), set_size(100), set_effect('GHOST', 0),
          costume('чёрный'), goto(0, 0))
# затмение-спрайт явно сбрасывается: после «Ещё раз» фад-переход не оставляет
# чёрного экрана (состояние строго равно старту по флагу)
fd.script(when_bcast('Сброс'), to_front(), set_size(100), set_effect('GHOST', 0),
          costume('чёрный'), goto(0, 0))
# Атмосферный переход: «Затемнить» — снежная завеса-веер всплывает и
# медленно плывёт по экрану, затем растворяется; «Осветлить» — чёрная
# завеса наплывает и растворяется. Веер накладывается мягким GHOST-эффектом.
fd.script(when_bcast('Затемнить'), to_front(), set_size(100), costume('завеса'),
          set_effect('GHOST', 100),
          repeat(5,
              change_effect('GHOST', -20), wait(0.04),
              change_x(rnd(-60, 60)), change_y(rnd(-40, 40)), wait(0.04)),
          set_effect('GHOST', 0))
fd.script(when_bcast('Осветлить'), to_front(), set_size(100), costume('чёрный'),
          set_effect('GHOST', 100),
          repeat(5,
              change_effect('GHOST', -20), wait(0.04),
              change_x(rnd(-40, 40)), change_y(rnd(-30, 30)), wait(0.04)),
          set_effect('GHOST', 0))

# ==========================================================  ОБРАТНЫЙ ОТСЧЁТ
# Счётчик обратного отсчёта выведен на циферблат часов (спрайт «Часы_циферблат»,
# костюмы «цифра_N»): цифра = время % 10. Старый отдельный счётчик убран —
# его позиция (245, 190) выходила за правый край экрана (жалопa №1).
# Цель акта 3 понятна: стрелки часов показывают оставшееся время, цифра на
# циферблате — текущую секунду отсчёта.

# ===================================================================  КНОПКИ
btn = Target('Кнопка')
btn.costume('ещё_раз', f'{U}/btn_retry.png')
btn.size = 46
btn.x, btn.y = 0, -112
btn.visible = False
btn.script(when_flag(), hide())
btn.script(when_bcast('Сброс'), hide())
btn.script(when_bcast('Стоп'), hide())
btn.script(when_bcast('Победа'), wait(2.6), show(), to_front(), goto(0, -112), set_size(46))
btn.script(when_bcast('Проигрыш'), wait(1.6), show(), to_front(), goto(0, -112), set_size(46))
btn.script(when_bcast('Рестарт'), hide())
btn.script(when_clicked(), hide(), bcast('Рестарт'))

bs = Target('КнопкаЗвук')
bs.costume('вкл', f'{U}/btn_sound_on.png')
bs.costume('выкл', f'{U}/btn_sound_off.png')
bs.size = 22
bs.x, bs.y = -206, 152
bs.script(when_flag(), show(), to_front(), goto(-206, 152), set_size(22),
          forever(if_(eq(var('звук_вкл'), 1), costume('вкл')),
                  if_(eq(var('звук_вкл'), 0), costume('выкл'))))
bs.script(when_bcast('Сброс'), show(), to_front(), goto(-206, 152), set_size(22))
bs.script(when_clicked(),
          ifelse(eq(var('звук_вкл'), 1),
                 [setv('звук_вкл', 0), stop_sounds()],
                 [setv('звук_вкл', 1)]))

# ==================================================================  МУЗЫКА
mz = Target('Музыка')
mz.costume('px', f'{U}/px.png')
mz.visible = False
mz.volume = 55
mz.sound('мастерская', f'{M}/theme_workshop.mp3')
mz.sound('город', f'{M}/theme_city.mp3')
mz.sound('лес', f'{M}/theme_forest.mp3')
mz.sound('крыша', f'{M}/theme_storm.mp3')
mz.sound('финал', f'{M}/theme_final.mp3')
mz.sound('проигрыш', f'{M}/theme_defeat.mp3')
mz.sound('джингл', f'{M}/jingle_2027.mp3')

mz.script(when_flag(), hide())
mz.script(when_bcast('МузыкаСтоп'), stop_sounds())
mz.script(when_flag(),
          forever(wait_until(eq(var('звук_вкл'), 0)), stop_sounds(), wait(0.3)))

for idx, name in [(1, 'мастерская'), (2, 'город'), (3, 'лес'), (4, 'крыша'),
                  (5, 'финал'), (6, 'проигрыш')]:
    mz.script(when_flag(),
              forever(
                  wait_until(eq(var('музыка'), idx)),
                  until(or_(not_(eq(var('музыка'), idx)), eq(var('звук_вкл'), 0)),
                        play_wait(name)),
                  wait(0.1),
              ))


def build_project():
    p = Project()
    actors = [stage, d, mz, snow, tr, dr, sn, st, sl, h, g, ov, sm, dm, mt,
              cf, cm, ch, lv, sc, ek, sub, cap, y27, fw, fd, btn, bs]
    # оверлей-акторы (тени, снег на шапках) и параллакс-слои фонов
    actors += [vgn, sm_glow, puff_santa, puff_snowman, puff_owl]
    actors += [ov_mila_sh, ov_mila_sn, ov_sled_sh, ov_gift_sh, ov_star_sh,
               ov_dr_sh, ov_tr_sh, ov_dm_sh, ov_dm_sn, ov_sm_sh, ov_sm_sn,
               ov_owl_sh]
    actors += list(parallax_actors.values())
    for t in actors:
        p.add(t)
    return p
