"""Сборка .sb3 (ZIP: project.json + md5-ассеты) и валидация."""
import json
import os
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(__file__))
from blocks import Project, Target, serialize_project  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def build(project, out_path):
    data, assets = serialize_project(project)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('project.json', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
        for name, path in assets.items():
            z.write(path, name)
    size = os.path.getsize(out_path)
    nblocks = sum(len(t['blocks']) for t in data['targets'])
    print(f'собрано: {out_path}  {size/1024/1024:.2f} МБ, таргетов {len(data["targets"])}, блоков {nblocks}, ассетов {len(assets)}')
    return out_path, data


def validate(path):
    """Структурная проверка через scratch-parser (официальный парсер Scratch)."""
    js = os.path.join(ROOT, 'tools', 'validate.js')
    r = subprocess.run(['node', js, path], capture_output=True, text=True,
                       cwd=os.path.join(ROOT, 'tools'),
                       env={**os.environ, 'NODE_PATH': os.path.join(ROOT, 'tools', 'node_modules')})
    print((r.stdout or '').strip())
    if r.returncode != 0:
        print((r.stderr or '').strip())
    return r.returncode == 0
