"""Удобные конструкторы блоков Scratch 3.0 (используются в game.py)."""
from blocks import Block


# ------------------------------------------------------------------ события
def when_flag():
    return Block('event_whenflagclicked')


def when_bcast(name):
    return Block('event_whenbroadcastreceived', fields={'BROADCAST_OPTION': name})


def when_clicked():
    return Block('event_whenthisspriteclicked')


def when_clone():
    return Block('control_start_as_clone')


def bcast(name):
    return Block('event_broadcast', inputs={'BROADCAST_INPUT': ('bcast', name)})


def bcast_wait(name):
    return Block('event_broadcastandwait', inputs={'BROADCAST_INPUT': ('bcast', name)})


# ------------------------------------------------------------------ контроль
def wait(sec):
    return Block('control_wait', inputs={'DURATION': sec})


def forever(*body):
    return Block('control_forever', inputs={'SUBSTACK': _seq(body)})


def repeat(n, *body):
    return Block('control_repeat', inputs={'TIMES': n, 'SUBSTACK': _seq(body)})


def until(cond, *body):
    return Block('control_repeat_until', inputs={'CONDITION': cond, 'SUBSTACK': _seq(body)})


def if_(cond, *body):
    return Block('control_if', inputs={'CONDITION': cond, 'SUBSTACK': _seq(body)})


def ifelse(cond, body1, body2):
    return Block('control_if_else', inputs={'CONDITION': cond,
                                            'SUBSTACK': _seq(body1),
                                            'SUBSTACK2': _seq(body2)})


def wait_until(cond):
    return Block('control_wait_until', inputs={'CONDITION': cond})


def stop_all():
    return Block('control_stop', fields={'STOP_OPTION': ['all', None]},
                 mutation={'tagName': 'mutation', 'hasnext': 'false'})


def stop_this():
    return Block('control_stop', fields={'STOP_OPTION': ['this script', None]},
                 mutation={'tagName': 'mutation', 'hasnext': 'false'})


def clone_self():
    return Block('control_create_clone_of', inputs={'CLONE_OPTION': ('menu', '_myself_')})


def delete_clone():
    return Block('control_delete_this_clone')


def _seq(body):
    out = []
    for b in body:
        if isinstance(b, list):
            out.extend(b)
        elif b is not None:
            out.append(b)
    return out


# ------------------------------------------------------------------ движение
def goto(x=0, y=0):
    return Block('motion_gotoxy', inputs={'X': x, 'Y': y})


def set_x(x):
    return Block('motion_setx', inputs={'X': x})


def set_y(y):
    return Block('motion_sety', inputs={'Y': y})


def change_x(dx):
    return Block('motion_changexby', inputs={'DX': dx})


def change_y(dy):
    return Block('motion_changeyby', inputs={'DY': dy})


def point_dir(d):
    return Block('motion_pointindirection', inputs={'DIRECTION': d})


def turn_right(d):
    return Block('motion_turnright', inputs={'DEGREES': d})


def glide(sec, x, y):
    return Block('motion_glidesecstoxy', inputs={'SECS': sec, 'X': x, 'Y': y})


def rotation_style(style):
    return Block('motion_setrotationstyle', fields={'STYLE': [style, None]})


# -------------------------------------------------------------------- внешний вид
def say(msg):
    return Block('looks_say', inputs={'MESSAGE': msg})


def say_for(msg, secs):
    return Block('looks_sayforsecs', inputs={'MESSAGE': msg, 'SECS': secs})


def think(msg):
    return Block('looks_think', inputs={'MESSAGE': msg})


def show():
    return Block('looks_show')


def hide():
    return Block('looks_hide')


def costume(name):
    return Block('looks_switchcostumeto', inputs={'COSTUME': ('menu', name)})


def next_costume():
    return Block('looks_nextcostume')


def set_size(v):
    return Block('looks_setsizeto', inputs={'SIZE': v})


def change_size(d):
    return Block('looks_changesizeby', inputs={'CHANGE': d})


def set_effect(effect, v):
    return Block('looks_seteffectto', inputs={'VALUE': v}, fields={'EFFECT': [effect, None]})


def change_effect(effect, v):
    return Block('looks_changeeffectby', inputs={'CHANGE': v}, fields={'EFFECT': [effect, None]})


def clear_fx():
    return Block('looks_cleargraphiceffects')


def to_front():
    return Block('looks_gotofrontback', fields={'FRONT_BACK': ['front', None]})


def to_back():
    return Block('looks_gotofrontback', fields={'FRONT_BACK': ['back', None]})


def go_layers(n):
    return Block('looks_goforwardbackwardlayers', inputs={'NUM': n},
                 fields={'FORWARD_BACKWARD': ['forward', None]})


def backdrop(name):
    return Block('looks_switchbackdropto', inputs={'BACKDROP': ('menu', name)})


# ---------------------------------------------------------------------- звук
def play(name):
    return Block('sound_play', inputs={'SOUND_MENU': ('menu', name)})


def play_wait(name):
    return Block('sound_playuntildone', inputs={'SOUND_MENU': ('menu', name)})


def stop_sounds():
    return Block('sound_stopallsounds')


def set_volume(v):
    return Block('sound_setvolumeto', inputs={'VOLUME': v})


# ------------------------------------------------------------------ сенсоры
def key(k):
    return Block('sensing_keypressed', inputs={'KEY_OPTION': ('menu', k)})


def touching(name):
    return Block('sensing_touchingobject', inputs={'TOUCHINGOBJECTMENU': ('menu', name)})


def dist_to(name):
    return Block('sensing_distanceto', inputs={'DISTANCETOMENU': ('menu', name)})


def mouse_down():
    return Block('sensing_mousedown')


def of_var(sprite, prop):
    return Block('sensing_of', inputs={'OBJECT': ('menu', sprite)}, fields={'PROPERTY': [prop, None]})


def of_prop(sprite, prop):
    return Block('sensing_of', inputs={'OBJECT': ('menu', sprite)}, fields={'PROPERTY': [prop, None]})


def timer():
    return Block('sensing_timer')


def reset_timer():
    return Block('sensing_resettimer')


# ------------------------------------------------------------------ операторы
def add(a, b):
    return Block('operator_add', inputs={'NUM1': a, 'NUM2': b})


def sub(a, b):
    return Block('operator_subtract', inputs={'NUM1': a, 'NUM2': b})


def mul(a, b):
    return Block('operator_multiply', inputs={'NUM1': a, 'NUM2': b})


def div(a, b):
    return Block('operator_divide', inputs={'NUM1': a, 'NUM2': b})


def mod(a, b):
    return Block('operator_mod', inputs={'NUM1': a, 'NUM2': b})


def rnd(a, b):
    return Block('operator_random', inputs={'FROM': a, 'TO': b})


def gt(a, b):
    return Block('operator_gt', inputs={'OPERAND1': a, 'OPERAND2': b})


def lt(a, b):
    return Block('operator_lt', inputs={'OPERAND1': a, 'OPERAND2': b})


def eq(a, b):
    return Block('operator_equals', inputs={'OPERAND1': a, 'OPERAND2': b})


def and_(a, b):
    return Block('operator_and', inputs={'OPERAND1': a, 'OPERAND2': b})


def or_(a, b):
    return Block('operator_or', inputs={'OPERAND1': a, 'OPERAND2': b})


def not_(a):
    return Block('operator_not', inputs={'OPERAND': a})


def join(a, b):
    return Block('operator_join', inputs={'STRING1': a, 'STRING2': b})


def letter(i, s):
    return Block('operator_letter_of', inputs={'LETTER': i, 'STRING': s})


def length(s):
    return Block('operator_length', inputs={'STRING': s})


def mathop(op, x):
    return Block('operator_mathop', inputs={'NUM': x}, fields={'OPERATOR': [op, None]})


# ---------------------------------------------------------------- переменные
def setv(name, val):
    return Block('data_setvariableto', inputs={'VALUE': val}, fields={'VARIABLE': name})


def changev(name, val):
    return Block('data_changevariableby', inputs={'VALUE': val}, fields={'VARIABLE': name})


def show_var(name):
    return Block('data_showvariable', fields={'VARIABLE': name})


def hide_var(name):
    return Block('data_hidevariable', fields={'VARIABLE': name})


def var(name):
    return ('var', name)


UNUSED = (point_dir, turn_right, glide, think, change_effect, letter, length, show_var, hide_var,
          dist_to, stop_this, go_layers, of_prop, of_var, set_volume, reset_timer, mathop, mod)
