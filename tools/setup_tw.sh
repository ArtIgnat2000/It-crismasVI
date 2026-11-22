#!/usr/bin/env bash
# Установка форка виртуальной машины TurboWarp в tools/tw-vm (по demand).
#
# Зачем: чтобы прогонять проект не в официальной scratch-vm, а в TurboWarp —
# форке с JIT-компилятором, который использует официальный клиент TurboWarp.
# Запуск: tools/setup_tw.sh  →  затем  cd tools && node run_vm_tw.js <файл.sb3> <сценарий>
#
# node_modules форка в tools/tw-vm/node_modules игнорируется .gitignore.
set -e
cd "$(dirname "$0")/.."

TW_DIR="tools/tw-vm"
TW_URL="https://codeload.github.com/TurboWarp/scratch-vm/tar.gz/refs/heads/develop"

if [ ! -f "$TW_DIR/package.json" ]; then
    echo "Скачиваю TurboWarp/scratch-vm (develop)…"
    mkdir -p "$TW_DIR"
    curl -sL "$TW_URL" | tar xz -C "$TW_DIR" --strip-components=1
fi

if [ ! -d "$TW_DIR/node_modules/scratch-parser" ]; then
    echo "Устанавливаю зависимости форка…"
    (cd "$TW_DIR" && npm install --omit=dev --no-audit --no-fund --ignore-scripts --strict-ssl=false 2>&1 | tail -2)
fi

node -e "require('./$TW_DIR'); console.log('OK: TurboWarp VM готов — cd tools && node run_vm_tw.js ../dist/Poslednyaya_posylka.sb3 all')"
