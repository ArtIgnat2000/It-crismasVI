"""Псевдокод project.json — чтобы глазами проверить логику скриптов."""
import json, sys, zipfile

def fmt_input(b, key, blocks, depth):
    inp = b['inputs'].get(key)
    if not inp: return ''
    kind = inp[0]
    if kind == 1:
        sh = inp[1]
        if isinstance(sh, str) and sh in blocks:
            m = blocks[sh]; f = list(m['fields'].values())[0][0]
            return str(f)
        if isinstance(sh, list):
            if sh[0] == 4: return sh[1]
            if sh[0] == 10: return repr(sh[1])
            if sh[0] == 11: return '@'+sh[2]
            if sh[0] == 12: return '$'+sh[1]
    if kind in (2, 3):
        ref = inp[1]
        if isinstance(ref, str) and ref in blocks:
            return expr(blocks[ref], blocks, depth)
        if isinstance(ref, list):
            if ref[0] == 12: return '$'+ref[1]
            return str(ref)
    return '?'

def expr(b, blocks, depth=0):
    op = b['opcode']
    name = op.split('_', 1)[1]
    if op.startswith(('data_', 'motion_', 'looks_', 'sensing_', 'operator_', 'sound_', 'event_')) :
        if op.endswith(('variable', 'xposition', 'yposition', 'timer')):
            return name
    ins = ', '.join(f"{k}={fmt_input(b,k,blocks,depth)}" for k in b['inputs'])
    if ins: return f"{name}({ins})"
    if b['fields']:
        return f"{name}{list(b['fields'].values())[0][0]}"
    return name

def show(seq_first, blocks, indent=0, out=None):
    pad = '   ' * indent
    bid = seq_first
    while bid:
        b = blocks[bid]; op = b['opcode']
        if op == 'control_forever':
            out.append(pad + 'ПОВТОРЯТЬ ВСЕГДА:')
            show(b['inputs'].get('SUBSTACK', [None, None])[1], blocks, indent + 1, out)
        elif op == 'control_repeat':
            out.append(pad + f"ПОВТОРИТЬ {fmt_input(b,'TIMES',blocks,indent)}:")
            show(b['inputs'].get('SUBSTACK', [None, None])[1], blocks, indent + 1, out)
        elif op == 'control_repeat_until':
            out.append(pad + f"ПОВТОРЯТЬ ДО ({fmt_input(b,'CONDITION',blocks,indent)}):")
            show(b['inputs'].get('SUBSTACK', [None, None])[1], blocks, indent + 1, out)
        elif op == 'control_if':
            out.append(pad + f"ЕСЛИ ({fmt_input(b,'CONDITION',blocks,indent)}):")
            show(b['inputs'].get('SUBSTACK', [None, None])[1], blocks, indent + 1, out)
        elif op == 'control_if_else':
            out.append(pad + f"ЕСЛИ ({fmt_input(b,'CONDITION',blocks,indent)}):")
            show(b['inputs'].get('SUBSTACK', [None, None])[1], blocks, indent + 1, out)
            out.append(pad + 'ИНАЧЕ:')
            show(b['inputs'].get('SUBSTACK2', [None, None])[1], blocks, indent + 1, out)
        elif op == 'control_wait':
            out.append(pad + f"ждать {fmt_input(b,'DURATION',blocks,indent)} с")
        elif op == 'control_wait_until':
            out.append(pad + f"ждать до ({fmt_input(b,'CONDITION',blocks,indent)})")
        elif op == 'control_create_clone_of':
            out.append(pad + f"создать клон {fmt_input(b,'CLONE_OPTION',blocks,indent)}")
        elif op == 'control_delete_this_clone':
            out.append(pad + 'удалить клон')
        elif op == 'event_broadcast':
            out.append(pad + fmt_input(b, 'BROADCAST_INPUT', blocks, indent))
        elif op == 'event_broadcastandwait':
            out.append(pad + fmt_input(b, 'BROADCAST_INPUT', blocks, indent) + ' и ждать')
        elif op == 'data_setvariableto':
            out.append(pad + f"задать {b['fields']['VARIABLE'][0]} = {fmt_input(b,'VALUE',blocks,indent)}")
        elif op == 'data_changevariableby':
            out.append(pad + f"изменить {b['fields']['VARIABLE'][0]} на {fmt_input(b,'VALUE',blocks,indent)}")
        else:
            ins = ', '.join(f"{k}={fmt_input(b,k,blocks,indent)}" for k in b['inputs'])
            fl = ', '.join(f"{k}={v[0]}" for k, v in b['fields'].items())
            out.append(pad + f"{op}({ins})" + (f" [{fl}]" if fl else ""))
        bid = b['next']

def dump(path, only=None, limit=None):
    d = json.loads(zipfile.ZipFile(path).read('project.json'))
    for t in d['targets']:
        if only and t['name'] not in only: continue
        print(f"\n########## {t['name']}")
        for bid, b in t['blocks'].items():
            if b.get('topLevel'):
                out = []
                if b['opcode'] == 'event_whenbroadcastreceived':
                    out.append(f"КОГДА Я ПОЛУЧУ {b['fields']['BROADCAST_OPTION'][0]}")
                elif b['opcode'] == 'event_whenflagclicked':
                    out.append('КОГДА ЗЕЛЁНЫЙ ФЛАГ')
                elif b['opcode'] == 'event_whenthisspriteclicked':
                    out.append('КОГДА СПРАЙТ НАЖАТ')
                elif b['opcode'] == 'control_start_as_clone':
                    out.append('КОГДА Я — КЛОН')
                show(b['next'], t['blocks'], 1, out)
                print('\n'.join(out))
                print('---')

if __name__ == '__main__':
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    dump(sys.argv[1], only)
