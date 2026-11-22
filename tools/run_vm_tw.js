// Прогон .sb3 на виртуальной машине TurboWarp (форк scratch-vm).
//
// Использование: cd tools && node run_vm_tw.js <файл.sb3> <сценарий> [frames.json]
// То же, что run_vm.js, но с заменой require('scratch-vm') на форк
// TurboWarp/scratch-vm (то же API, но JIT-компилятор и отличия в расписании).
// Это реальная проверка совместимости проекта с TurboWarp.
//
// node_modules форка живёт в tools/tw-vm/node_modules — если пропали после
// перезапуска окружения: cd tools/tw-vm && npm i --omit=dev --ignore-scripts
// (npm требует --strict-ssl=false в этой среде для github:-зависимостей).

const Module = require('module');
const path = require('path');

// подменяем require('scratch-vm') на локальный форк TurboWarp
const twVm = require(path.join(__dirname, 'tw-vm'));
const origLoad = Module._load;
Module._load = function (request, parent, isMain) {
    if (request === 'scratch-vm') return twVm;
    return origLoad.apply(this, arguments);
};

require('./run_vm.js');
