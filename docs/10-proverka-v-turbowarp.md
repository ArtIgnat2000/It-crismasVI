# Проверка проекта на TurboWarp — простой способ

TurboWarp — faster & more reliable fork of Scratch 3.0 (официальный клиент
с кэшем/JIT и дополнительными возможностями). Проект «Последняя посылка»
заявлен как Scratch 3.0 project, поэтому он должен запускаться в TurboWarp
без изменений. Два способа проверить:

## 1. Простой способ — ручной, в TurboWarp Desktop (2 минуты)

1. Скачай TurboWarp: https://turbowarp.org (Windows / macOS / Linux —
   ссылки на релизы: https://github.com/TurboWarp/desktop/releases).
2. Открой в нём `dist/Poslednyaya_posylka.sb3` (Файл → Открыть).
3. Нажми **зелёный флаг** ▶.
4. Пройди игру: зелёный флаг → пролог (~17 с) → акт 1 (прыжки) → акт 2
   (полёт) → акт 3 (держаться 20 с) → победа.
5. Проверь ключевые моменты:
   - запуск без ошибок в логах консоли TurboWarp (Ctrl+Shift+I → Console —
     должно быть ни красного);
   - звук, музыка, субтитры работают;
   - кнопка **«ЕЩЁ РАЗ»** перезапускает с самого начала (фон «мастерская»,
     жизни 3, звёзды 0);
   - титр показывает «Scratch 3.0 · версия 1.8».

## 2. Автоматический прогон в TurboWarp-VM (headless)

Полная проверка тех же сценариев, что и для официальной scratch-vm
(см. `docs/08-proverka-zapuska.md`), но в виртуальной машине TurboWarp.

```bash
./tools/setup_tw.sh            # один раз: скачивает форк TurboWarp/scratch-vm
                               # и его зависимости в tools/tw-vm
cd tools
node run_vm_tw.js ../dist/Poslednyaya_posylka.sb3 all
node run_vm_tw.js ../dist/Poslednyaya_posylka.sb3 play
node run_vm_tw.js ../dist/Poslednyaya_posylka.sb3 retry
node run_vm_tw.js ../dist/Poslednyaya_posylka.sb3 frames ../dist/frames_tw.json
cd .. && PYTHONPATH=tools/vendor python3 tools/art/frames.py dist/frames_tw.json
```

`tools/run_vm_tw.js` — та же логика, что и `run_vm.js`, но `scratch-vm`
заменяется на форк TurboWarp (`tools/tw-vm`). Если после перезапуска
окружения пропал `tools/tw-vm/node_modules` — снова `./tools/setup_tw.sh`.

Фактические результаты (версия 1.8, 22.11.2026):

| Прогон | Результат на TurboWarp-VM |
|---|---|
| `all` | победа=1, проигрыш=0, после «ЕЩЁ РАЗ»: акт=0, жизни=3, звёзды=0, время=150, фон=мастерская; **сообщения рантайма: 0** |
| `play` | бот проходит игру: **победа=1, звёзды=5, жизни=2** |
| `retry` | рестарт кнопкой «ЕЩЁ РАЗ» эквивалентен старту по зеленому флагу (различие только в случайной числённости клонов снега) |
| `frames` + `frames.py` | 13 кадров — **НАЛОЖЕНИЙ НЕТ** |

То есть проект запускается и проходится в виртуальной машине TurboWarp
так же, как в официальной scratch-vm.
