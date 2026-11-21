#!/usr/bin/env bash
# Идемпотентная установка зависимостей внутрь репозитория (переживает сброс окружения).
set -e
cd "$(dirname "$0")/.."
pip install --quiet --target tools/vendor --upgrade pillow numpy lameenc mutagen 2>&1 | tail -2 || true
# полный набор нужен и сборке (.sb3), и headless-прогону run_vm.js:
# scratch-vm + jsdom + jszip + scratch-storage + scratch-svg-renderer
if [ ! -d tools/node_modules/scratch-vm ] || [ ! -d tools/node_modules/jszip ]; then
  (cd tools && npm i --silent 2>&1 | tail -2)
fi
echo "OK: $(PYTHONPATH=tools/vendor python3 -c 'import PIL,numpy;print("pillow",PIL.__version__,"numpy",numpy.__version__)')"
