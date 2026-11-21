#!/usr/bin/env bash
# Идемпотентная установка зависимостей внутрь репозитория (переживает сброс окружения).
set -e
cd "$(dirname "$0")/.."
pip install --quiet --target tools/vendor --upgrade pillow numpy lameenc 2>&1 | tail -2 || true
if [ ! -d tools/node_modules/scratch-parser ]; then
  (cd tools && npm init -y >/dev/null 2>&1; npm i --silent scratch-parser@6 scratch-storage@3 2>&1 | tail -2)
fi
echo "OK: $(PYTHONPATH=tools/vendor python3 -c 'import PIL,numpy;print("pillow",PIL.__version__,"numpy",numpy.__version__)')"
