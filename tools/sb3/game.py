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
from blocks import Project, Target, Block  # noqa: E402
import sb  # noqa: E402
from sb import *  # noqa: E402

R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
S = f'{R}/art/sprites'
B = f'{R}/art/backgrounds'
U = f'{R}/art/ui'
M = f'{R}/audio/music'
F = f'{R}/audio/foley'
V = f'{R}/audio/voice'

GROUND = -95          # «пол» для героини (центр спрайта)
HERO_SIZE = 26


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

d.script(when_flag(), bcast('Старт'))

d.script(when_bcast('Рестарт'), bcast('Старт'))

act1 = [
    setv('акт', 1), setv('скорость', 6),
    setv('музыка', 0), bcast_wait('МузыкаСтоп'), setv('музыка', 2),
    bcast_wait('Затемнить'), backdrop('город'), bcast_wait('Осветлить'),
    bcast('Акт1'),
    until(or_(gt(var('звёзды'), 4), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    bcast_wait('Реп5'),
    setv('акт', 0), bcast_wait('Стоп'),
]

act2 = [
    setv('акт', 2), setv('скорость', 9),
    setv('музыка', 0), bcast_wait('МузыкаСтоп'), setv('музыка', 3),
    bcast_wait('Затемнить'), backdrop('лес'), bcast_wait('Осветлить'),
    bcast('Акт2'),
    until(or_(gt(var('звёзды'), 9), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    setv('акт', 0), bcast_wait('Стоп'),
]

act3 = [
    setv('акт', 3), setv('скорость', 7), setv('осталось', 20),
    setv('музыка', 0), bcast_wait('МузыкаСтоп'), setv('музыка', 4),
    bcast_wait('Затемнить'), backdrop('крыша'), bcast_wait('Осветлить'),
    bcast_wait('Реп6'),
    bcast('Акт3'),
    until(or_(lt(var('осталось'), 1), or_(lt(var('жизни'), 1), lt(var('время'), 1))), wait(0.1)),
    setv('акт', 0), bcast_wait('Стоп'),
    ifelse(alive(), [setv('победа', 1)], [setv('победа', 0)]),
]

win = [
    setv('игра', 0), setv('старт_идёт', 0), setv('музыка', 0), bcast_wait('МузыкаСтоп'),
    bcast_wait('Затемнить'), backdrop('победа'), bcast_wait('Осветлить'),
    setv('музыка', 5),
    bcast_wait('Победа'),
    bcast_wait('Реп8'),
    bcast_wait('Реп10'),
]

lose = [
    setv('игра', 0), setv('старт_идёт', 0), setv('музыка', 0), bcast_wait('МузыкаСтоп'),
    bcast_wait('Затемнить'), backdrop('проигрыш'), bcast_wait('Осветлить'),
    setv('музыка', 6),
    bcast_wait('Проигрыш'),
    bcast_wait('Реп9'),
]

d.script(
    when_bcast('Старт'),
    if_(eq(var('старт_идёт'), 1), stop_this()),
    setv('старт_идёт', 1),
    setv('игра', 0), setv('акт', 0), setv('жизни', 3), setv('звёзды', 0),
    setv('время', 150), setv('победа', 0), setv('неуязвим', 0),
    setv('скорость', 6), setv('ветер', 0.4), setv('осталось', 0),
    setv('музыка', 0), bcast_wait('МузыкаСтоп'),
    bcast_wait('Сброс'),
    bcast('СнегИдёт'),
    setv('игра', 1),
    wait(0.45),
    backdrop('мастерская'),
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
               changev('осталось', -1),
               if_(eq(var('осталось'), 12), bcast('Реп7'))))

# ==================================================================  МИЛА
h = Target('Мила')
for n in ('idle', 'run', 'jump', 'cheer'):
    h.costume(n, f'{S}/goat_{n}.png')
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

h.script(when_flag(),
         hide(), set_size(HERO_SIZE), rotation_style('left-right'), point_dir(90),
         clear_fx(), setv('vy', 0), setv('на_земле', 1))

h.script(when_bcast('Сброс'),
         hide(), clear_fx(), set_size(HERO_SIZE), set_effect('GHOST', 0),
         setv('vy', 0), setv('на_земле', 1), goto(-150, GROUND), point_dir(90))

h.script(when_bcast('Стоп'), hide(), set_effect('GHOST', 0))

# --- Акт 1: бег с прыжками
h.script(when_bcast('Акт1'),
         show(), set_size(HERO_SIZE), goto(-150, GROUND), point_dir(90),
         costume('run'), setv('vy', 0), setv('на_земле', 1), set_effect('GHOST', 0),
         until(not_act(1),
               if_(and_(key('space'), eq(var('на_земле'), 1)),
                   setv('vy', 13), setv('на_земле', 0), play('прыжок'), costume('jump')),
               change_y(var('vy')),
               changev('vy', -1.3),
               if_(lt(y_pos(), GROUND),
                   set_y(GROUND), setv('vy', 0),
                   if_(eq(var('на_земле'), 0), play('приземление')),
                   setv('на_земле', 1), costume('run')),
               ))

# --- Акт 2: полёт на санях, управление вверх/вниз
h.script(when_bcast('Акт2'),
         show(), set_size(HERO_SIZE), goto(-130, -70), point_dir(90),
         costume('run'), set_effect('GHOST', 0),
         until(not_act(2),
               if_(key('up arrow'), change_y(3.4)),
               if_(key('down arrow'), change_y(-3.4)),
               if_(gt(y_pos(), 95), set_y(95)),
               if_(lt(y_pos(), -150), set_y(-150)),
               ))

# --- Акт 3: крыша, бег влево-вправо + прыжок
h.script(when_bcast('Акт3'),
         show(), set_size(HERO_SIZE), goto(-150, GROUND), point_dir(90),
         costume('run'), setv('vy', 0), setv('на_земле', 1), set_effect('GHOST', 0),
         until(not_act(3),
               if_(key('left arrow'), change_x(-4), point_dir(-90)),
               if_(key('right arrow'), change_x(4), point_dir(90)),
               if_(gt(x_pos(), 210), set_x(210)),
               if_(lt(x_pos(), -210), set_x(-210)),
               if_(and_(key('space'), eq(var('на_земле'), 1)),
                   setv('vy', 13), setv('на_земле', 0), play('прыжок'), costume('jump')),
               change_y(var('vy')),
               changev('vy', -1.3),
               if_(lt(y_pos(), GROUND),
                   set_y(GROUND), setv('vy', 0),
                   if_(eq(var('на_земле'), 0), play('приземление')),
                   setv('на_земле', 1), costume('run')),
               ))

# --- удар: неуязвимость и мерцание (не даёт потерять 3 жизни за секунду)
h.script(when_bcast('Хит'),
         if_(eq(var('неуязвим'), 0),
             setv('неуязвим', 1), changev('жизни', -1), play('удар'),
             repeat(7, set_effect('GHOST', 60), wait(0.09), set_effect('GHOST', 0), wait(0.09)),
             setv('неуязвим', 0)))

h.script(when_bcast('Победа'), show(), clear_fx(), goto(-140, -110), set_size(32), costume('cheer'),
         repeat(6, change_y(12), wait(0.09), change_y(-12), wait(0.09)))

h.script(when_bcast('Проигрыш'), show(), clear_fx(), costume('idle'), set_effect('GHOST', 25))

# --- реплики
h.script(when_bcast('Реп1'), show(), goto(60, -88), set_size(HERO_SIZE),
         costume('idle'), point_dir(90), clear_fx())
h.script(when_bcast('Реп3'), say('Я успею! Только бы не опоздать до полуночи!'),
         play_wait('голос_3'), say(''))
h.script(when_bcast('Реп5'), say('Ещё одна звезда! Ещё немного, и я у цели!'),
         play_wait('голос_5'), say(''))
h.script(when_bcast('Реп7'), say('Смотрите, окно! Там нас ждут и верят в чудо!'),
         play_wait('голос_7'), say(''))
h.script(when_bcast('Реп9'), say('Полночь… Я не успела. Но я попробую снова!'),
         play_wait('голос_9'), say(''))

# ==================================================================  САНИ
sl = Target('Сани')
sl.costume('сани', f'{S}/sleigh.png')
sl.sound('вжух', f'{F}/sfx_swoosh.mp3')
sl.size = 42
sl.visible = False
sl.script(when_flag(), hide())
sl.script(when_bcast('Сброс'), hide())
sl.script(when_bcast('Стоп'), hide())
for n in (1, 2):
    sl.script(when_bcast(f'Акт{n}'),
             show(), set_size(42), to_front(),
             until(not_act(n),
                   goto(add(of_prop('Мила', 'x position'), -10), add(of_prop('Мила', 'y position'), -34)),
                   ))

# ================================================================  ПОДАРОК
g = Target('Подарок')
g.costume('подарок', f'{S}/gift.png')
g.sound('магия', f'{F}/sfx_magic.mp3')
g.size = 18
g.visible = False
g.script(when_flag(), hide())
g.script(when_bcast('Сброс'), hide())
g.script(when_bcast('Стоп'), hide())
for n in (1, 2, 3):
    g.script(when_bcast(f'Акт{n}'),
             show(), set_size(18),
             until(not_act(n),
                   goto(add(of_prop('Мила', 'x position'), -22), add(of_prop('Мила', 'y position'), 34)),
                   repeat(20, change_effect('BRIGHTNESS', 2), wait(0.04),
                          change_effect('BRIGHTNESS', -2), wait(0.04)),
                   ))
g.script(when_bcast('Победа'), show(), goto(0, 40), set_size(40), play('магия'),
         repeat(30, turn_right(6), wait(0.03)))

# ==================================================================  ЗВЕЗДА
st = Target('Звезда')
st.costume('звезда', f'{S}/star.png')
st.sound('подбор', f'{F}/sfx_pickup.mp3')
st.size = 14
st.visible = False
st.script(when_flag(), hide())
st.script(when_bcast('Сброс'), hide())
st.script(when_bcast('Стоп'), hide())
st.script(when_bcast('Стоп'), delete_clone())

for n, ymin, ymax, period in [(1, -95, -30, 1.0), (2, -130, 90, 0.85)]:
    st.script(when_bcast(f'Акт{n}'),
             hide(),
             until(not_act(n),
                   clone_self(),
                   wait(rnd(period, period + 0.5)),
                   ))
    st.script(when_clone(), show(), set_size(rnd(11, 15)), point_dir(0),
              goto(270, rnd(ymin, ymax)),
              until(or_(lt(x_pos(), -270), not_act(n)),
                    change_x(mul(-1, var('скорость'))),
                    turn_right(4),
                    if_(touching('Мила'), changev('звёзды', 1), play('подбор'), delete_clone()),
                    ))
    
# ==================================================================  СУГРОБ
dr = Target('Сугроб')
dr.costume('сугроб', f'{S}/snowdrift.png')
dr.size = 24
dr.visible = False
dr.script(when_flag(), hide())
dr.script(when_bcast('Сброс'), hide())
dr.script(when_bcast('Стоп'), hide())
dr.script(when_bcast('Стоп'), delete_clone())
dr.script(when_bcast('Акт1'),
         hide(),
         until(not_act(1),
               clone_self(),
               wait(rnd(1.1, 2.0)),
               ))
dr.script(when_clone(),
         show(), set_size(rnd(16, 22)), goto(280, GROUND - 25),
         until(or_(lt(x_pos(), -280), not_act(1)),
               change_x(mul(-1, var('скорость'))),
               if_(and_(touching('Мила'), eq(var('неуязвим'), 0)), bcast('Хит'), delete_clone()),
               ))

# ===================================================================  ЁЛКА
tr = Target('Ёлка')
tr.costume('ёлка', f'{S}/tree.png')
tr.size = 28
tr.visible = False
tr.script(when_flag(), hide())
tr.script(when_bcast('Сброс'), hide())
tr.script(when_bcast('Стоп'), hide())
tr.script(when_bcast('Стоп'), delete_clone())
tr.script(when_bcast('Акт2'),
         hide(),
         until(not_act(2),
               clone_self(),
               wait(rnd(0.75, 1.4)),
               ))
tr.script(when_clone(),
         show(), set_size(rnd(24, 34)), goto(280, rnd(-150, 60)),
         until(or_(lt(x_pos(), -280), not_act(2)),
               change_x(mul(-1, var('скорость'))),
               turn_right(1),
               if_(and_(touching('Мила'), eq(var('неуязвим'), 0)), bcast('Хит'), delete_clone()),
               ))

# =================================================================  СНЕЖОК
sn = Target('Снежок')
sn.costume('снежок', f'{S}/snowdrift.png')
sn.sound('снежок_удар', f'{F}/sfx_snowball.mp3')
sn.size = 12
sn.visible = False
sn.script(when_flag(), hide())
sn.script(when_bcast('Сброс'), hide())
sn.script(when_bcast('Стоп'), hide())
sn.script(when_bcast('Стоп'), delete_clone())
sn.script(when_bcast('Акт3'),
         hide(),
         until(not_act(3),
               clone_self(),
               wait(rnd(0.55, 1.0)),
               ))
sn.script(when_clone(),
         show(), goto(of_prop('Метель', 'x position'), of_prop('Метель', 'y position')),
         point_towards('Мила'), turn_right(rnd(-12, 12)),
         until(or_(touching('_edge_'), not_act(3)),
               move_steps(13),
               if_(touching('Мила'), play('снежок_удар'), bcast('Хит'), delete_clone()),
               ))

# ====================================================================  СНЕГ
snow = Target('Снег')
snow.costume('снежинка', f'{U}/stars_0.png')
snow.size = 4
snow.visible = False
snow.var('клон', 0)
snow.script(when_flag(), hide())
snow.script(when_bcast('Сброс'), hide(), delete_clone())
# клоны помечают себя, чтобы не размножались при повторных рассылках
snow.script(when_clone(), setv('клон', 1))
snow.script(when_bcast('СнегИдёт'),
            if_(eq(var('клон'), 0), repeat(26, clone_self(), wait(0.02))))
snow.script(when_clone(),
            show(), set_size(rnd(2, 7)), set_effect('GHOST', rnd(20, 70)),
            goto(rnd(-250, 250), rnd(-180, 180)),
            forever(
                change_y(mul(rnd(1, 3), -1)),
                change_x(var('ветер')),
                if_(lt(y_pos(), -190), set_y(190), set_x(rnd(-250, 250))),
                if_(gt(x_pos(), 250), set_x(-250)),
                if_(lt(x_pos(), -250), set_x(250)),
            ))

# ===================================================================  МЕТЕЛЬ
mt = Target('Метель')
mt.costume('метель', f'{S}/storm.png')
mt.sound('голос_6', f'{V}/06_storm.mp3')
mt.sound('ветер', f'{F}/sfx_wind.mp3')
mt.size = 45
mt.visible = False
mt.script(when_flag(), hide())
mt.script(when_bcast('Сброс'), hide(), clear_fx())
mt.script(when_bcast('Стоп'), hide())
mt.script(when_bcast('Реп6'),
         show(), goto(150, 60), set_size(45), clear_fx(),
         say('Тебе не долететь, козочка!'), play_wait('голос_6'), say(''),
         hide())
mt.script(when_bcast('Акт3'),
         show(), goto(160, 50), set_size(45), clear_fx(), point_dir(90),
         until(not_act(3),
               set_y(rnd(10, 110)),
               turn_right(rnd(-3, 3)),
               if_(eq(mod(var('время'), 4), 0), play('ветер')),
               wait(1.1),
               ))

# ==================================================================  ДЕД МОРОЗ
dm = Target('ДедМороз')
dm.costume('дедмороз', f'{S}/santa.png')
for nm, fn in [('голос_1', '01_narrator'), ('голос_2', '02_santa'),
               ('голос_8', '08_final'), ('голос_10', '10_outro')]:
    dm.sound(nm, f'{V}/{fn}.mp3')
dm.size = 42
dm.visible = False
dm.script(when_flag(), hide())
dm.script(when_bcast('Сброс'), hide())
dm.script(when_bcast('Стоп'), hide())
dm.script(when_bcast('Реп1'),
         show(), goto(-60, -55), set_size(42), costume('дедмороз'),
         say('До Нового года остаётся ровно две минуты…'), play_wait('голос_1'), say(''))
dm.script(when_bcast('Реп2'),
         say('Мила, посылка №2027 так и не доставлена!'), play_wait('голос_2'), say(''))
dm.script(when_bcast('Реп8'),
         show(), goto(-95, -80), set_size(40),
         say('Ты успела, Мила! С Новым 2027 годом!'), play_wait('голос_8'), say(''))
dm.script(when_bcast('Реп10'),
         say('Спасибо тебе, маленькая козочка. Праздник спасён!'), play_wait('голос_10'), say(''))
dm.script(when_bcast('Акт3'), hide())

# =================================================================  СНЕГОВИК
sm = Target('Снеговик')
sm.costume('снеговик', f'{S}/snowman.png')
sm.sound('голос_4', f'{V}/04_snowman.mp3')
sm.sound('скрип', f'{F}/sfx_step.mp3')
sm.size = 26
sm.visible = False
sm.script(when_flag(), hide())
sm.script(when_bcast('Сброс'), hide())
sm.script(when_bcast('Стоп'), hide())
sm.script(when_bcast('Реп4'),
         show(), goto(110, -80), set_size(26),
         say('Полозья смазаны, шеф! Сани готовы!'), play_wait('голос_4'), say(''))
sm.script(when_bcast('Акт1'), hide())

# ====================================================================  СОВА
ov = Target('Сова')
ov.costume('сова', f'{S}/owl.png')
ov.sound('уханье', f'{F}/sfx_owl.mp3')
ov.size = 16
ov.visible = False
ov.script(when_flag(), hide())
ov.script(when_bcast('Сброс'), hide())
ov.script(when_bcast('Стоп'), hide())
ov.script(when_bcast('Акт2'),
         show(), goto(-185, 70), set_size(16),
         until(not_act(2),
               set_y(add(70, mul(12, mathop('sin', mul(var('время'), 60))))),
               if_(eq(mod(var('время'), 5), 0), play('уханье')),
               wait(0.2),
               ))

# ===================================================================  ЧАСЫ
cf = Target('Часы_циферблат')
cf.costume('часы', f'{U}/clock_face.png')
cf.size = 22
cf.x, cf.y = 190, 130
cf.script(when_flag(), show(), to_front(), set_size(22), goto(190, 130))

ch = Target('Часы_стрелка')
ch.costume('стрелка', f'{U}/clock_hand.png')
ch.size = 22
ch.x, ch.y = 190, 130
ch.script(when_flag(), show(), to_front(), set_size(22), goto(190, 130),
          forever(point_dir(mul(var('время'), 2.4))))

# ====================================================================  HUD
lv = Target('Жизни')
for n in range(4):
    lv.costume(f'жизни_{n}', f'{U}/lives_{n}.png')
lv.size = 22
lv.x, lv.y = -195, 128
lv.script(when_flag(), show(), to_front(), set_size(22), goto(-195, 128),
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
sc.x, sc.y = 150, 128
sc.script(when_flag(), show(), to_front(), set_size(16), goto(150, 128))
branches = []
for n in range(14):
    branches.append(if_(eq(var('звёзды'), n), costume(f'{n}')))
branches.append(if_(gt(var('звёзды'), 13), costume('13')))
sc.script(when_flag(), forever(*branches))

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
ek.script(when_bcast('Сброс'), hide(), clear_fx())
ek.script(when_bcast('Стоп'), hide())
ek.script(when_bcast('Затемнить'), hide())
ek.script(when_bcast('Акт1'), hide())
ek.script(when_bcast('Акт2'), hide())
ek.script(when_bcast('Акт3'), hide())
ek.script(when_bcast('Реп1'),
         show(), goto(0, 55), set_size(34), costume('титр'), set_effect('GHOST', 100),
         repeat(10, change_effect('GHOST', -10), wait(0.03)))
ek.script(when_bcast('Победа'),
         show(), goto(0, 100), set_size(30), costume('победа'), set_effect('GHOST', 100),
         repeat(10, change_effect('GHOST', -10), wait(0.03)))
ek.script(when_bcast('Проигрыш'),
         show(), goto(0, 80), set_size(26), costume('проигрыш'), set_effect('GHOST', 100),
         repeat(10, change_effect('GHOST', -10), wait(0.03)))

hint = Target('Подсказка')
for n in (1, 2, 3):
    hint.costume(f'акт{n}', f'{U}/hint{n}.png')
hint.size = 36
hint.x, hint.y = 0, -134
hint.visible = False
hint.script(when_flag(), hide())
hint.script(when_bcast('Сброс'), hide())
# своя подсказка на каждый акт: управление в актах разное
for n in (1, 2, 3):
    hint.script(when_bcast(f'Акт{n}'),
                to_front(), goto(0, -134), set_size(36), costume(f'акт{n}'),
                set_effect('GHOST', 100), show(),
                repeat(8, change_effect('GHOST', -12.5), wait(0.03)),
                wait(4.5),
                repeat(8, change_effect('GHOST', 12.5), wait(0.03)),
                hide())

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
            wait(0.4), show(), goto(90, -10), set_size(10), clear_fx(), play('магия'),
            repeat(12, change_size(6), wait(0.03)),
            repeat(80, change_effect('COLOR', 3), wait(0.03)))

# ================================================================  ФЕЙЕРВЕРК
fw = Target('Фейерверк')
fw.costume('искра', f'{U}/stars_0.png')
fw.sound('салют', f'{F}/sfx_firework.mp3')
fw.size = 8
fw.visible = False
fw.script(when_flag(), hide())
fw.script(when_bcast('Сброс'), hide())
fw.script(when_bcast('Стоп'), delete_clone(), hide())
fw.script(when_clone(), hide())
fw.script(when_bcast('Победа'),
         hide(), wait(0.3),
         repeat(10, clone_self(), wait(0.22)))
fw.script(when_clone(),
         show(), goto(rnd(-180, 180), rnd(0, 120)), set_size(rnd(6, 12)),
         set_effect('COLOR', rnd(0, 100)), play('салют'), point_dir(rnd(0, 360)),
         repeat(24, move_steps(4), turn_right(15), change_effect('GHOST', 4), change_size(-0.2), wait(0.02)),
         delete_clone())

# ================================================================  ЗАТЕМНЕНИЕ
fd = Target('Затемнение')
fd.costume('чёрный', f'{U}/fade.png')
fd.size = 100
fd.visible = True
fd.script(when_flag(), to_front(), set_size(100), set_effect('GHOST', 100), goto(0, 0))
fd.script(when_bcast('Затемнить'), to_front(), set_size(100), set_effect('GHOST', 100),
          repeat(8, change_effect('GHOST', -12.5), wait(0.03)))
fd.script(when_bcast('Осветлить'), to_front(),
          repeat(8, change_effect('GHOST', 12.5), wait(0.03)))

# ===================================================================  КНОПКИ
btn = Target('Кнопка')
btn.costume('ещё_раз', f'{U}/btn_retry.png')
btn.size = 30
btn.x, btn.y = 0, -95
btn.visible = False
btn.script(when_flag(), hide())
btn.script(when_bcast('Сброс'), hide())
btn.script(when_bcast('Стоп'), hide())
btn.script(when_bcast('Победа'), wait(2.6), show(), to_front(), goto(0, -95), set_size(30))
btn.script(when_bcast('Проигрыш'), wait(1.6), show(), to_front(), goto(0, -110), set_size(30))
btn.script(when_clicked(), if_(eq(var('игра'), 0), bcast('Рестарт')))

bs = Target('КнопкаЗвук')
bs.costume('вкл', f'{U}/btn_sound_on.png')
bs.costume('выкл', f'{U}/btn_sound_off.png')
bs.size = 14
bs.x, bs.y = -150, -165
bs.script(when_flag(), show(), to_front(), goto(-150, -165), set_size(14),
          forever(if_(eq(var('звук_вкл'), 1), costume('вкл')),
                  if_(eq(var('звук_вкл'), 0), costume('выкл'))))
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
              cf, ch, lv, sc, ek, hint, y27, fw, fd, btn, bs]:
        p.add(t)
    return p
