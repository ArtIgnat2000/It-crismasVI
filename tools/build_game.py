import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sb3'))
import build, game
p = game.build_project()
out = os.path.join(os.path.dirname(__file__), '..', 'dist', 'Poslednyaya_posylka.sb3')
build.build(p, out)
ok = build.validate(out)
sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location('lint', os.path.join(os.path.dirname(__file__), 'lint_sb3.py'))
lint = importlib.util.module_from_spec(spec); spec.loader.exec_module(lint)
probs = lint.lint(out)
for x in probs: print(' !', x)
print(f'линтер: проблем {len(probs)}')
sys.exit(0 if (ok and not probs) else 1)
