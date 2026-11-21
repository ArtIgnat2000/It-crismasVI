require('./smoke_env.js');
// Headless-прогон проекта в scratch-vm: проверяем загрузку, исполнение и перезапуск.
const fs = require('fs');
const VM = require('scratch-vm');
const StorageMod = require('scratch-storage');
const ScratchStorage = StorageMod.ScratchStorage || StorageMod.default || StorageMod;

const file = process.argv[2];
let vnow = 0;
const perf = { now: () => vnow };
const origDateNow = Date.now;
Date.now = () => vnow;
if (global.performance) { try { global.performance.now = () => vnow; } catch (e) {} }

const fakeRenderer = new Proxy({}, {
    get: (t, prop) => {
        if (prop === 'createDrawable') return () => 0;
        if (prop === 'isTouchingDrawables') return () => false;
        if (prop === 'isTouchingObject') return () => false;
        if (prop === 'getBounds') return () => ({ left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 });
        if (prop === 'getBoundsForBubble') return () => ({ left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 });
        if (prop === 'getCurrentSkinSize') return () => ({ width: 100, height: 100 });
        if (prop === 'getSkinSize') return () => [100, 100];
        if (prop === 'getFencedPositionOfDrawable') return (id, x, y) => [x, y];
        if (prop === 'getDrawableOrder') return () => 0;
        if (prop === 'extractDrawableScreenSpace') return () => ({ imageData: null });
        return () => 0;
    }
});

const vm = new VM();
vm.attachStorage(new ScratchStorage());
vm.attachRenderer(fakeRenderer);
try {
    const { SVGRenderer, BitmapAdapter } = require('scratch-svg-renderer');
    vm.attachV2SVGAdapter(new SVGRenderer());
    vm.attachV2BitmapAdapter(new BitmapAdapter());
} catch (e) { console.log('no svg adapter', e.message); }
const t0 = setInterval(() => {}, 1000);

const errors = [];
const origWarn = console.warn, origErr = console.error;
console.warn = (...a) => { errors.push('WARN ' + a.join(' ')); };
console.error = (...a) => { errors.push('ERR ' + a.join(' ')); };

const buf = fs.readFileSync(file);
vm.loadProject(buf).then(async () => {
    console.log('loaded targets:', vm.runtime.targets.map(t => t.getName()).join(', '));

    function run(seconds) {
        const steps = Math.round(seconds * 30);
        for (let i = 0; i < steps; i++) {
            vnow += 1000 / 30;
            try { vm.runtime._step(); } catch (e) { errors.push('STEP ' + (e && e.stack || e)); }
        }
    }
    function dumpVars(tag) {
        const st = vm.runtime.getTargetForStage();
        const out = {};
        for (const id of Object.keys(st.variables)) {
            const v = st.variables[id];
            out[v.name] = v.value;
        }
        console.log(tag, JSON.stringify(out));
    }
    function cloneCount() {
        return vm.runtime.targets.filter(t => !t.isOriginal && t.isOriginal !== undefined).length;
    }

    vm.greenFlag();
    run(3);
    dumpVars('после 3 с:');
    run(10);
    dumpVars('после 13 с:');
    console.log('клонов:', cloneCount());

    vm.greenFlag();
    run(3);
    dumpVars('после перезапуска 3 с:');
    console.log('клонов после рестарта:', cloneCount());

    const uniq = [...new Set(errors)];
    console.log('ошибок/предупреждений:', uniq.length);
    for (const e of uniq.slice(0, 25)) console.log('  ', e.slice(0, 300));
    clearInterval(t0);
    process.exit(uniq.length ? 1 : 0);
}).catch(e => {
    console.error('LOAD FAIL:', e && e.stack || e);
    process.exit(2);
});
