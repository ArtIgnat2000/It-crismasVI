"""Линтер project.json: проверяет то, чего не видит схема scratch-parser.

  * все ссылки на блоки (inputs/next/parent/substack/menu) существуют;
  * все костюмы и звуки, упомянутые в блоках, реально есть у спрайта;
  * переменные и рассылки разрешаются в id;
  * shadow-блоки меню на месте;
  * нет блоков без opcode и подвешенных parent.
"""
import json
import sys
import zipfile


def lint(path):
    problems = []
    z = zipfile.ZipFile(path)
    data = json.loads(z.read('project.json'))
    targets = data['targets']
    stage = targets[0]
    names = {t['name'] for t in targets}
    all_vars = {}   # id -> (name, owner)
    all_bcast = set()
    for t in targets:
        for vid, v in t['variables'].items():
            all_vars[vid] = (v[0], t['name'])
        all_bcast |= set(t.get('broadcasts', {}).keys())
    costumes_of = {t['name']: {c['name'] for c in t['costumes']} for t in targets}
    sounds_of = {t['name']: {s['name'] for s in t['sounds']} for t in targets}

    for t in targets:
        tn = t['name']
        b = t['blocks']
        if not t['costumes']:
            problems.append(f'{tn}: нет костюмов')
        if not t['sounds'] and not t['isStage']:
            pass  # спрайты без звука допустимы
        for bid, blk in b.items():
            op = blk.get('opcode')
            if not op:
                problems.append(f'{tn}/{bid}: блок без opcode')
                continue
            # ссылки
            for key, inp in blk.get('inputs', {}).items():
                if not isinstance(inp, list) or not inp:
                    problems.append(f'{tn}/{bid} ({op}): кривой input {key}={inp}')
                    continue
                kind = inp[0]
                if kind == 1:
                    sh = inp[1]
                    if isinstance(sh, str):
                        if sh not in b:
                            problems.append(f'{tn}/{bid} ({op}) {key}: shadow {sh} не найден')
                        elif not b[sh].get('shadow'):
                            problems.append(f'{tn}/{bid} ({op}) {key}: {sh} не shadow')
                elif kind in (2, 3):
                    ref = inp[1]
                    if isinstance(ref, str):
                        if ref not in b:
                            problems.append(f'{tn}/{bid} ({op}) {key}: блок {ref} не найден')
                    elif not isinstance(ref, list):
                        problems.append(f'{tn}/{bid} ({op}) {key}: неизвестная ссылка {ref}')
            nxt = blk.get('next')
            if nxt and nxt not in b:
                problems.append(f'{tn}/{bid}: next {nxt} не найден')
            par = blk.get('parent')
            if par and par not in b:
                problems.append(f'{tn}/{bid}: parent {par} не найден')
            if blk.get('topLevel') and par:
                problems.append(f'{tn}/{bid}: topLevel-блок имеет parent')
            # поля
            fields = blk.get('fields', {})
            if 'VARIABLE' in fields:
                vid = fields['VARIABLE'][1]
                if vid not in all_vars:
                    problems.append(f'{tn}/{bid} ({op}) {fields["VARIABLE"][0]}: переменная не объявлена')
            if 'LIST' in fields:
                pass
            if 'BROADCAST_OPTION' in fields:
                bid2 = fields['BROADCAST_OPTION'][1]
                if bid2 not in all_bcast:
                    problems.append(f'{tn}/{bid} ({op}) {fields["BROADCAST_OPTION"][0]}: рассылка не объявлена')
            # меню-блоки
            if op in ('looks_costume',):
                cname = fields.get('COSTUME', [None])[0]
                if cname not in costumes_of[tn]:
                    problems.append(f'{tn}/{bid}: костюм «{cname}» отсутствует')
            if op == 'looks_backdrops':
                cname = fields.get('BACKDROP', [None])[0]
                if cname not in costumes_of[stage['name']]:
                    problems.append(f'{tn}/{bid}: фон «{cname}» отсутствует')
            if op == 'sound_sounds_menu':
                sname = fields.get('SOUND_MENU', [None])[0]
                if sname not in sounds_of[tn]:
                    problems.append(f'{tn}/{bid}: звук «{sname}» отсутствует у {tn}')
            if op in ('sensing_touchingobjectmenu', 'sensing_distancetomenu'):
                oname = list(fields.values())[0][0] if fields else None
                if oname not in names and oname != '_edge_':
                    problems.append(f'{tn}/{bid}: объект «{oname}» отсутствует')
            if op == 'sensing_of_object_menu':
                oname = fields.get('OBJECT', [None])[0]
                if oname not in names and oname != 'Stage':
                    problems.append(f'{tn}/{bid}: объект «{oname}» отсутствует')
            if op == 'control_create_clone_of_menu':
                oname = fields.get('CLONE_OPTION', [None])[0]
                if oname not in names and oname != '_myself_':
                    problems.append(f'{tn}/{bid}: клон «{oname}» невозможен')
            if op == 'sensing_keyoptions':
                pass
            # каждый не-topLevel блок, у которого нет ни parent, ни topLevel — сирота
            if not blk.get('topLevel') and not par and not blk.get('shadow'):
                problems.append(f'{tn}/{bid} ({op}): блок-сирота без parent')
            # ровно один next/parent
            if par and blk.get('topLevel'):
                problems.append(f'{tn}/{bid}: конфликт topLevel/parent')
        # все переменные, объявленные сцены, должны встречаться
    # аудит рассылок: у каждого сообщения должен быть отправитель и получатель
    senders, receivers = set(), set()
    for t in targets:
        for blk in t['blocks'].values():
            if blk.get('opcode') == 'event_broadcast' or blk.get('opcode') == 'event_broadcastandwait':
                inp = blk.get('inputs', {}).get('BROADCAST_INPUT')
                if inp and isinstance(inp[1], list) and inp[1][0] == 11:
                    senders.add(inp[1][2])
            if blk.get('opcode') == 'event_whenbroadcastreceived':
                receivers.add(blk['fields']['BROADCAST_OPTION'][0])
    for name in sorted(receivers - senders):
        problems.append(f'рассылка «{name}»: есть получатель, но никто не отправляет')
    for name in sorted(senders - receivers):
        problems.append(f'рассылка «{name}»: отправляется, но никто не принимает')

    # ассеты
    for t in targets:
        for c in t['costumes'] + t['sounds']:
            if c['md5ext'] not in z.namelist():
                problems.append(f'ассет {c["md5ext"]} отсутствует в архиве')
    return problems


if __name__ == '__main__':
    probs = lint(sys.argv[1])
    for p in probs:
        print(' !', p)
    print(f'проблем: {len(probs)}')
    sys.exit(1 if probs else 0)
