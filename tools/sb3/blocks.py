"""Мини-DSL для сборки project.json Scratch 3.0 без редактора.

Каждый блок описывается объектом Block; inputs принимают:
  число / строку            — литерал (shadow math_number / text)
  Block                     — репортёр в слоте (тип слота берётся из таблиц)
  ('var', 'Имя')            — репортёр переменной
  ('bcast', 'Имя')          — рассылка сообщения
  ('menu', 'значение')      — пункт выпадающего списка (shadow-блок)
  [...блоки...]             — SUBSTACK
"""
import hashlib


class Block:
    __slots__ = ('opcode', 'inputs', 'fields', 'shadow', 'mutation')

    def __init__(self, opcode, inputs=None, fields=None, shadow=False, mutation=None):
        self.opcode = opcode
        self.inputs = inputs or {}
        self.fields = fields or {}
        self.shadow = shadow
        self.mutation = mutation

    def __repr__(self):
        return f'<{self.opcode}>'


# слоты, в которых ожидается булево значение
BOOL_INPUTS = {
    ('control_if', 'CONDITION'), ('control_if_else', 'CONDITION'),
    ('control_repeat_until', 'CONDITION'), ('control_wait_until', 'CONDITION'),
    ('control_while', 'CONDITION'), ('operator_and', 'OPERAND1'),
    ('operator_and', 'OPERAND2'), ('operator_or', 'OPERAND1'),
    ('operator_or', 'OPERAND2'), ('operator_not', 'OPERAND'),
}
# слоты, в которых ожидается строка
TEXT_INPUTS = {
    ('looks_say', 'MESSAGE'), ('looks_sayforsecs', 'MESSAGE'),
    ('looks_think', 'MESSAGE'), ('looks_thinkforsecs', 'MESSAGE'),
    ('operator_join', 'STRING1'), ('operator_join', 'STRING2'),
    ('operator_letter_of', 'LETTER'), ('sensing_askandwait', 'QUESTION'),
}
# слоты-меню: (opcode, input) -> (shadow opcode, имя поля)
MENU = {
    ('looks_switchcostumeto', 'COSTUME'): ('looks_costume', 'COSTUME'),
    ('looks_switchbackdropto', 'BACKDROP'): ('looks_backdrops', 'BACKDROP'),
    ('sound_play', 'SOUND_MENU'): ('sound_sounds_menu', 'SOUND_MENU'),
    ('sound_playuntildone', 'SOUND_MENU'): ('sound_sounds_menu', 'SOUND_MENU'),
    ('sensing_touchingobject', 'TOUCHINGOBJECTMENU'): ('sensing_touchingobjectmenu', 'TOUCHINGOBJECTMENU'),
    ('sensing_distanceto', 'DISTANCETOMENU'): ('sensing_distancetomenu', 'DISTANCETOMENU'),
    ('sensing_keypressed', 'KEY_OPTION'): ('sensing_keyoptions', 'KEY_OPTION'),
    ('sensing_of', 'OBJECT'): ('sensing_of_object_menu', 'OBJECT'),
    ('control_create_clone_of', 'CLONE_OPTION'): ('control_create_clone_of_menu', 'CLONE_OPTION'),
    ('motion_goto', 'TO'): ('motion_goto_menu', 'TO'),
    ('motion_glideto', 'TO'): ('motion_glideto_menu', 'TO'),
    ('motion_pointtowards', 'TOWARDS'): ('motion_pointtowards_menu', 'TOWARDS'),
}


def _id(*parts):
    return hashlib.md5(('|'.join(map(str, parts))).encode()).hexdigest()[:20]


class Target:
    """Стадия или спрайт."""

    def __init__(self, name, is_stage=False):
        self.name = name
        self.is_stage = is_stage
        self.costumes = []          # (name, path, bitmap_resolution, cx, cy)
        self.sounds = []            # (name, path)
        self.scripts = []           # list[list[Block]]
        self.variables = {}         # name -> value
        self.lists = {}
        self.x = 0
        self.y = 0
        self.size = 100
        self.direction = 90
        self.visible = True
        self.rotation_style = 'all around'
        self.layer = 1
        self.volume = 100

    # --- декларации
    def costume(self, name, path, res=1, center=None):
        self.costumes.append((name, path, res, center))
        return name

    def sound(self, name, path):
        self.sounds.append((name, path))
        return name

    def var(self, name, value=0):
        self.variables[name] = value
        return name

    def script(self, *blocks):
        seq = []
        for b in blocks:
            if isinstance(b, list):
                seq.extend(b)
            elif b is not None:
                seq.append(b)
        self.scripts.append(seq)
        return seq


class Project:
    def __init__(self):
        self.targets = []

    def add(self, target):
        self.targets.append(target)
        return target

    def serialize(self):
        stage = self.targets[0]
        assert stage.is_stage
        bcasts = {}
        # собираем все имена рассылок
        for t in self.targets:
            for s in t.scripts:
                _collect_bcast(s, bcasts)
        bcast_ids = {name: _id('bcast', name) for name in bcasts}

        out_targets = []
        for idx, t in enumerate(self.targets):
            out_targets.append(self._serialize_target(t, idx, bcast_ids))
        project = {
            'targets': out_targets,
            'monitors': [],
            'extensions': [],
            'meta': {'semver': '3.0.0', 'vm': '0.2.0', 'agent': 'it-christmas-vi/1.9'},
        }
        return project, bcast_ids


def _collect_bcast(blocks, acc):
    for b in blocks:
        if not isinstance(b, Block):
            continue
        if b.opcode == 'event_whenbroadcastreceived':
            acc.setdefault(b.fields['BROADCAST_OPTION'], 1)
        for v in b.inputs.values():
            if isinstance(v, tuple) and v and v[0] == 'bcast':
                acc.setdefault(v[1], 1)
            elif isinstance(v, Block):
                _collect_bcast([v], acc)
            elif isinstance(v, list):
                _collect_bcast(v, acc)


# ----------------------------------------------------------------- сериализация
import os
import struct


def md5_file(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def mp3_info(path):
    """sample rate и число сэмплов MP3 (mutagen, с запасным парсером кадров)."""
    try:
        from mutagen.mp3 import MP3
        a = MP3(path)
        rate = int(a.info.sample_rate)
        return rate, int(round(a.info.length * rate))
    except Exception:
        pass
    data = open(path, 'rb').read()
    i = 0
    if data[:3] == b'ID3':
        size = struct.unpack('>I', b'\x00' + data[6:9])[0] + 10 if False else ((data[6] & 0x7f) << 21 | (data[7] & 0x7f) << 14 | (data[8] & 0x7f) << 7 | (data[9] & 0x7f)) + 10
        i = size
    rates = {0: 44100, 1: 48000, 2: 32000}
    br_table = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
    total = 0
    rate = 44100
    while i + 4 < len(data):
        if data[i] == 0xFF and (data[i + 1] & 0xE0) == 0xE0:
            h = data[i:i + 4]
            ver = (h[1] >> 3) & 3
            layer = (h[1] >> 1) & 3
            br_idx = (h[2] >> 4) & 0xF
            sr_idx = (h[2] >> 2) & 3
            pad = (h[2] >> 1) & 1
            if sr_idx in rates:
                rate = rates[sr_idx]
            if layer == 1 and 0 < br_idx < 15:
                br = br_table[br_idx] * 1000
                frame_len = int(144 * br / rate) + pad
                if frame_len <= 0:
                    break
                total += 1152 if ver == 3 else 576
                i += frame_len
                continue
        i += 1
    if total == 0:  # запасной вариант
        dur = max(len(data) * 8 / 128000, 0.1)
        total = int(dur * rate)
    return rate, total


class _Ser:
    def __init__(self, target, bcast_ids, assets, global_vars=None, global_lists=None):
        self.t = target
        self.bcast_ids = bcast_ids
        self.assets = assets
        self.blocks = {}
        self.n = 0
        # глобальные переменные объявлены на сцене, локальные — в спрайте
        self.var_ids = dict(global_vars or {})
        self.var_ids.update({name: _id('var', target.name, name) for name in target.variables})
        self.list_ids = dict(global_lists or {})
        self.list_ids.update({name: _id('list', target.name, name) for name in target.lists})

    def nid(self):
        self.n += 1
        return f'{self.t.name[:3]}_{self.n}'

    # ---- блоки
    def emit_chain(self, seq, parent=None, top=False):
        first = None
        prev = None
        for b in seq:
            if not isinstance(b, Block):
                continue
            bid = self.nid()
            node = {'opcode': b.opcode, 'next': None,
                    'parent': prev if prev else parent,
                    'inputs': {}, 'fields': {},
                    'shadow': b.shadow, 'topLevel': bool(top and prev is None)}
            if node['topLevel']:
                node['x'] = 40 * ((self.n % 6) + 1)
                node['y'] = 40 * ((self.n // 6) + 1)
            if b.mutation:
                node['mutation'] = dict(b.mutation)
            self.blocks[bid] = node
            if prev:
                self.blocks[prev]['next'] = bid
            else:
                first = bid
            self.emit_inputs(b, bid, node)
            prev = bid
        return first

    def emit_single(self, b, parent):
        return self.emit_chain([b], parent=parent)

    def emit_inputs(self, b, bid, node):
        for key, val in b.inputs.items():
            if isinstance(val, list):                       # SUBSTACK
                first = self.emit_chain(val, parent=bid)
                if first:
                    node['inputs'][key] = [2, first]
                continue
            if isinstance(val, tuple):
                if val[0] == 'var':
                    node['inputs'][key] = [3, [12, val[1], self.var_ids[val[1]]], [4, '0']]
                    continue
                if val[0] == 'bcast':
                    # ВАЖНО: порядок примитива рассылки в sb3 — [11, ИМЯ, id].
                    # Если перепутать, VM ищет рассылку по имени-как-id, не находит
                    # и молча ничего не запускает (игра «не стартует»).
                    node['inputs'][key] = [1, [11, val[1], self.bcast_ids[val[1]]]]
                    continue
                if val[0] == 'menu':
                    mop, mfield = MENU[(b.opcode, key)]
                    mid = self.nid()
                    self.blocks[mid] = {'opcode': mop, 'next': None, 'parent': bid,
                                        'inputs': {}, 'fields': {mfield: [val[1], None]},
                                        'shadow': True, 'topLevel': False}
                    node['inputs'][key] = [1, mid]
                    continue
                if val[0] == 'raw':
                    node['inputs'][key] = val[1]
                    continue
            if isinstance(val, Block):
                cid = self.emit_single(val, bid)
                if (b.opcode, key) in BOOL_INPUTS:
                    node['inputs'][key] = [2, cid]
                elif (b.opcode, key) in TEXT_INPUTS:
                    node['inputs'][key] = [3, cid, [10, '']]
                else:
                    node['inputs'][key] = [3, cid, [4, '0']]
                continue
            if isinstance(val, bool):
                node['inputs'][key] = [1, [4, '1' if val else '0']]
            elif isinstance(val, (int, float)):
                node['inputs'][key] = [1, [4, str(val)]]
            elif isinstance(val, str):
                node['inputs'][key] = [1, [10, val]]
        for key, val in b.fields.items():
            if key == 'VARIABLE' and isinstance(val, str):
                node['fields'][key] = [val, self.var_ids[val]]
            elif key == 'LIST' and isinstance(val, str):
                node['fields'][key] = [val, self.list_ids[val]]
            elif key == 'BROADCAST_OPTION' and isinstance(val, str):
                node['fields'][key] = [val, self.bcast_ids[val]]
            elif isinstance(val, (list, tuple)) and len(val) == 2:
                node['fields'][key] = [val[0], val[1]]
            else:
                node['fields'][key] = [val, None]

    # ---- ассеты
    def costume_json(self, spec):
        name, path, res, center = spec
        md5 = md5_file(path)
        ext = os.path.splitext(path)[1][1:].lower()
        self.assets[f'{md5}.{ext}'] = path
        # width/height и точка вращения обязательны в sb3: без них Scratch
        # ставит центр в (0,0) и спрайт «съезжает» и вращается вокруг угла
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        if center is None:
            center = (w / 2, h / 2)
        return {'name': name, 'bitmapResolution': res, 'md5ext': f'{md5}.{ext}',
                'assetId': md5, 'dataFormat': ext,
                'width': w, 'height': h,
                'rotationCenterX': center[0], 'rotationCenterY': center[1]}

    def sound_json(self, spec):
        name, path = spec
        md5 = md5_file(path)
        ext = os.path.splitext(path)[1][1:].lower()
        self.assets[f'{md5}.{ext}'] = path
        if ext == 'mp3':
            rate, count = mp3_info(path)
        else:
            rate, count = 44100, 44100
        return {'name': name, 'assetId': md5, 'dataFormat': ext, 'rate': rate,
                'sampleCount': count, 'md5ext': f'{md5}.{ext}'}

    def build(self, layer_order):
        blocks_first = {}
        self.scripts_json = []
        for seq in self.t.scripts:
            self.emit_chain(seq, parent=None, top=True)
        out = {
            'isStage': self.t.is_stage,
            'name': self.t.name,
            'variables': {self.var_ids[k]: [k, v] for k, v in self.t.variables.items()},
            'lists': {self.list_ids[k]: [k, []] for k in self.t.lists},
            'broadcasts': {},
            'blocks': self.blocks,
            'comments': {},
            'currentCostume': 0,
            'costumes': [self.costume_json(c) for c in self.t.costumes],
            'sounds': [self.sound_json(s) for s in self.t.sounds],
            'volume': self.t.volume,
            'layerOrder': layer_order,
        }
        if self.t.is_stage:
            out.update({'tempo': 60, 'videoTransparency': 50, 'videoState': 'on',
                        'textToSpeechLanguage': None})
        else:
            out.update({'visible': self.t.visible, 'x': self.t.x, 'y': self.t.y,
                        'size': self.t.size, 'direction': self.t.direction,
                        'draggable': False, 'rotationStyle': self.t.rotation_style})
        return out


def serialize_project(project):
    bcasts = {}
    for t in project.targets:
        for s in t.scripts:
            _collect_bcast(s, bcasts)
    bcast_ids = {name: _id('bcast', name) for name in bcasts}
    assets = {}
    targets = []
    gvars = {name: _id('var', 'Stage', name) for name in project.targets[0].variables}
    glists = {name: _id('list', 'Stage', name) for name in project.targets[0].lists}
    for idx, t in enumerate(project.targets):
        ser = _Ser(t, bcast_ids, assets, gvars, glists)
        tj = ser.build(idx)
        if not t.is_stage:
            tj['broadcasts'] = {}
        targets.append(tj)
    for tj in targets:
        tj['broadcasts'] = {bid: name for name, bid in bcast_ids.items()}
    data = {
        'targets': targets,
        'monitors': [],
        'extensions': [],
        'meta': {'semver': '3.0.0', 'vm': '0.2.0', 'agent': 'it-christmas-vi/1.9'},
    }
    return data, assets
