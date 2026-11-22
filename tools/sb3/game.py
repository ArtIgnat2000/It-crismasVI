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
    bcast('Акт1'),
    until(or_(gt(var('звёзды'), 4), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    bcast_wait('Реп5'),
    setv('акт', 0), bcast('Стоп'), wait(0.3),
]

act2 = [
    setv('акт', 2), setv('скорость', 6.5),
    # каждый акт — свой заход: сердечки восстанавливаются, счёт звёзд начинается с 0,
    # чтобы на табло всегда было видно «сколько ещё до цели» (5 звёзд за акт)
    setv('жизни', 3), setv('звёзды', 0),
    setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06), setv('музыка', 3),
    bcast_wait('Затемнить'), backdrop('лес'), bcast_wait('Осветлить'),
    bcast('Акт2'),
    until(or_(gt(var('звёзды'), 4), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    setv('акт', 0), bcast('Стоп'), wait(0.3),
]

act3 = [
    setv('акт', 3), setv('скорость', 6), setv('осталось', 20),
    setv('жизни', 3),
    setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06), setv('музыка', 4),
    bcast_wait('Затемнить'), backdrop('крыша'), bcast_wait('Осветлить'),
    bcast_wait('Реп6'),
    bcast('Акт3'),
    until(or_(lt(var('осталось'), 1), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    setv('акт', 0), bcast('Стоп'), wait(0.3),
    ifelse(alive(), [setv('победа', 1)], [setv('победа', 0)]),
]

win = [
    setv('игра', 0), setv('старт_идёт', 0), setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06),
    bcast_wait('Затемнить'), backdrop('победа'), bcast_wait('Осветлить'),
    setv('музыка', 5),
    bcast_wait('Победа'),
    bcast_wait('Реп8'),
    bcast_wait('Реп10'),
]

lose = [
    setv('игра', 0), setv('старт_идёт', 0), setv('музыка', 0), bcast('МузыкаСтоп'), wait(0.06),
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

h.script(when_flag(),
         hide(), set_size(HERO_SIZE), rotation_style('left-right'), point_dir(90),
         clear_fx(), setv('vy', 0), setv('на_земле', 1), setv('поза', 'idle'),
         setv('шаг', 0), setv('миг', 0))

h.script(when_bcast('Сброс'),
         hide(), clear_fx(), set_size(HERO_SIZE), set_effect('GHOST', 0),
         setv('vy', 0), setv('на_земле', 1), setv('поза', 'idle'),
         setv('шаг', 0), setv('миг', 0), goto(-150, GROUND), point_dir(90))

h.script(when_bcast('Стоп'), hide(), set_effect('GHOST', 0))

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
         costume('idle'), setv('поза', 'idle'), point_dir(90), clear_fx())
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
         until(not_act(1),
               # лёгкая тряска беготни: вертикальный кач + слегка кренится
               goto(add(of_prop('Мила', 'x position'), -60),
                    add(add(of_prop('Мила', 'y position'), -38.4),
                        mul(2.5, mathop('sin', mul(timer(), 10))))),
               point_dir(add(90, mul(3, mathop('sin', mul(timer(), 10))))),
               wait(0)))
sl.script(when_bcast('Акт2'),
         show(), set_size(30), to_back(), reset_timer(),
         until(not_act(2),
               # полёт: плавный кач и ленивый крен саней в воздухе
               goto(add(of_prop('Мила', 'x position'), -6),
                    add(add(of_prop('Мила', 'y position'), -51),
                        mul(5, mathop('sin', mul(timer(), 6))))),
               point_dir(add(90, mul(5, mathop('sin', mul(timer(), 6))))),
               wait(0)))
sl.script(when_bcast('Акт3'), hide())

# ================================================================  ПОДАРОК
g = Target('Подарок')
g.costume('подарок', f'{S}/gift.png')
g.sound('магия', f'{F}/sfx_magic.mp3')
g.size = 11
g.visible = False
g.script(when_flag(), hide())
g.script(when_bcast('Сброс'), hide())
g.script(when_bcast('Стоп'), hide())
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
st.script(when_bcast('Стоп'), hide())
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
dr.script(when_bcast('Стоп'), hide())
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
tr.script(when_bcast('Стоп'), hide())
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
for nm, fn in [('голос_1', '01_narrator'), ('голос_2', '02_santa'),
               ('голос_8', '08_final'), ('голос_10', '10_outro')]:
    dm.sound(nm, f'{V}/{fn}.mp3')
dm.size = 42
dm.visible = False
dm.rotation_style = 'left-right'
dm.var('на_сцене', 0)   # на сцене? (для мигания/дыхания)
dm.var('осн_y', -60)    # основание y для «дыхания»
dm.script(when_flag(), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Сброс'), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Стоп'), hide(), setv('на_сцене', 0))
# Пролог: реплику 1 говорит голос за кадром поверх титра — Дед Мороз ещё не вышел.
# Выходит на реплике 2 слева и остаётся до акта. В актах 1–2 его на сцене НЕТ
# (раньше он стоял посреди улицы до самой крыши).
dm.script(when_bcast('Реп1'), hide(), setv('на_сцене', 0), play('голос_1'))
dm.script(when_bcast('Реп2'),
         show(), goto(-120, -60), set_size(34), costume('дедмороз'), point_dir(90),
         setv('на_сцене', 1), setv('осн_y', -60), reset_timer(), play('голос_2'))
dm.script(when_bcast('Реп8'),
         show(), goto(-140, -75), set_size(28), costume('дедмороз'), point_dir(90),
         setv('на_сцене', 1), setv('осн_y', -75), reset_timer(), play('голос_8'))
dm.script(when_bcast('Реп10'), play('голос_10'))
dm.script(when_bcast('Акт1'), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Акт2'), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Акт3'), hide(), setv('на_сцене', 0))
dm.script(when_bcast('Проигрыш'), hide(), setv('на_сцене', 0))
# мигание + «дыхание» (едва заметная качка) — только когда на сцене
dm.script(when_flag(), forever(
        wait(0.35),
        if_(eq(var('на_сцене'), 1),
            set_y(add(var('осн_y'), mul(5, mathop('sin', mul(timer(), 2)))))),
        wait(1.7),
        if_(eq(var('на_сцене'), 1), costume('мороз_бlink')),
        wait(0.3),
        if_(eq(var('на_сцене'), 1), costume('дедмороз'))))

# =================================================================  СНЕГОВИК
sm = Target('Снеговик')
sm.costume('снеговик', f'{S}/snowman.png')
sm.costume('снег_бlink', f'{S}/snowman_blink.png')
sm.sound('голос_4', f'{V}/04_snowman.mp3')
sm.sound('скрип', f'{F}/sfx_step.mp3')
sm.size = 20
sm.visible = False
# без этого «повернуть в направление -90» крутило снеговика на 180° —
# в прологе он стоял вверх ногами (стиль «влево-вправо» только отражает спрайт)
sm.rotation_style = 'left-right'
sm.var('на_сцене', 0)
sm.var('осн_y', -88)
sm.script(when_flag(), hide(), setv('на_сцене', 0))
sm.script(when_bcast('Сброс'), hide(), setv('на_сцене', 0))
sm.script(when_bcast('Стоп'), hide(), setv('на_сцене', 0))
sm.script(when_bcast('Реп4'),
         show(), goto(185, -88), set_size(18), point_dir(-90),
         setv('на_сцене', 1), setv('осн_y', -88), reset_timer(), play('голос_4'))
sm.script(when_bcast('Акт1'), hide(), setv('на_сцене', 0))
# мигание + «дыхание» — только когда на сцене
sm.script(when_flag(), forever(
        wait(0.35),
        if_(eq(var('на_сцене'), 1),
            set_y(add(var('осн_y'), mul(4, mathop('sin', mul(timer(), 2)))))),
        wait(1.7),
        if_(eq(var('на_сцене'), 1), costume('снег_бlink')),
        wait(0.3),
        if_(eq(var('на_сцене'), 1), costume('снеговик'))))

# ====================================================================  СОВА
ov = Target('Сова')
ov.costume('сова', f'{S}/owl.png')
ov.costume('взмах', f'{S}/owl_open.png')
ov.sound('уханье', f'{F}/sfx_owl.mp3')
ov.size = 12
ov.visible = False
ov.script(when_flag(), hide())
ov.script(when_bcast('Сброс'), hide())
ov.script(when_bcast('Стоп'), hide())
ov.script(when_bcast('Акт2'),
         show(), goto(-185, 70), set_size(12), costume('сова'),
         until(not_act(2),
               set_y(add(70, mul(12, mathop('sin', mul(var('время'), 60))))),
               # взмахи крыльями: чередование костюмов (крыло поднято/опущено)
               next_costume(),
               if_(eq(mod(var('время'), 5), 0), play('уханье')),
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
cf.size = 20
cf.x, cf.y = CW
cf.script(when_flag(), show(), to_front(), set_size(20), goto(*CW))
cf.script(when_bcast('Сброс'), show(), to_front(), set_size(20), goto(*CW))

# минутная стрелка: длинная, полный оборот за 150 с (2.4°/с)
cm = Target('Часы_минутная')
cm.costume('минутная', f'{U}/clock_hand_min.png', center=(11, 75))
cm.size = 30
cm.x, cm.y = CW
cm.script(when_flag(), show(), to_front(), set_size(30), goto(*CW),
          forever(point_dir(mul(sub(150, var('время')), 2.4))))
cm.script(when_bcast('Сброс'), show(), to_front(), set_size(30), goto(*CW))

# часовая стрелка: короткая, 1/12 скорости минутной (0.2°/с)
ch = Target('Часы_часовая')
ch.costume('часовая', f'{U}/clock_hand_hr.png', center=(15, 48))
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

# ================================================================  ЗАТЕМНЕНИЕ
fd = Target('Затемнение')
fd.costume('чёрный', f'{U}/fade.png')
fd.size = 100
fd.visible = True
fd.script(when_flag(), to_front(), set_size(100), set_effect('GHOST', 100), goto(0, 0))
# затмение-спрайт явно сбрасывается: после «Ещё раз» фад-переход не оставляет
# чёрного экрана (состояние строго равно старту по флагу)
fd.script(when_bcast('Сброс'), to_front(), set_size(100), set_effect('GHOST', 100), goto(0, 0))
fd.script(when_bcast('Затемнить'), to_front(), set_size(100), set_effect('GHOST', 100),
          repeat(8, change_effect('GHOST', -12.5), wait(0.03)))
fd.script(when_bcast('Осветлить'), to_front(),
          repeat(8, change_effect('GHOST', 12.5), wait(0.03)))

# ==========================================================  ОБРАТНЫЙ ОТСЧЁТ
# Цель третьего акта на табло: счётчик 20 -> 0 в верхней полосе HUD. Раньше
# переменная «осталось» считалась, но на экране её не было — цель акта 3
# была невидима и неизмерима.
cd = Target('Обратный отсчёт')
for n in range(21):
    cd.costume(f'{n}', f'{U}/count_{n}.png')
cd.size = 22
cd.x, cd.y = 0, 130
cd.visible = False
cd.script(when_flag(), hide())
cd.script(when_bcast('Сброс'), hide())
cd.script(when_bcast('Стоп'), hide())
cd.script(when_bcast('Акт3'),
          show(), to_front(), set_size(22), goto(245, 190),
          forever(*[if_(eq(var('осталось'), n), costume(f'{n}')) for n in range(20, -1, -1)]))

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
    for t in [stage, d, mz, snow, tr, dr, sn, st, sl, h, g, ov, sm, dm, mt,
              cf, cm, ch, lv, sc, cd, ek, sub, cap, y27, fw, fd, btn, bs]:
        p.add(t)
    return p
