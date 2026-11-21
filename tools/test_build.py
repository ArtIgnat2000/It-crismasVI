"""Быстрый тест формата: собираем мини-проект и валидируем его."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sb3'))
from blocks import Project, Target
from sb import *
import build

ROOT = os.path.join(os.path.dirname(__file__), '..')

stage = Target('Stage', is_stage=True)
stage.costume('bg_city', f'{ROOT}/art/backgrounds/bg_city.jpg', res=2, center=(480, 360))
stage.costume('bg_forest', f'{ROOT}/art/backgrounds/bg_forest.jpg', res=2, center=(480, 360))
stage.var('жизни', 3)
stage.var('звёзды', 0)

goat = Target('Мила')
for n in ('idle', 'run', 'jump', 'cheer'):
    goat.costume(n, f'{ROOT}/art/sprites/goat_{n}.png')
goat.sound('тема_город', f'{ROOT}/audio/music/theme_city.mp3')
goat.sound('прыжок', f'{ROOT}/audio/foley/sfx_jump.mp3')
goat.x, goat.y, goat.size = -100, -100, 30
goat.var('vy', 0)
goat.script(when_flag(),
            goto(-100, -100), set_size(30), rotation_style('left-right'),
            costume('idle'), show(),
            forever(
                if_(key('space'), play('прыжок'), change_y(20)),
                if_(touching('_edge_'), change_x(-3)),
                changev('звёзды', 0),
            ))
goat.script(when_bcast('Победа'), say_for('Ура!', 2), costume('cheer'))
goat.script(when_clone(), wait(0.5), delete_clone())

p = Project()
p.add(stage)
p.add(goat)
out = os.path.join(ROOT, 'dist', '_test.sb3')
build.build(p, out)
ok = build.validate(out)
print('RESULT:', 'OK' if ok else 'FAIL')
sys.exit(0 if ok else 1)
