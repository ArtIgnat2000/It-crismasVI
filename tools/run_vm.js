// Headless-прогон .sb3 в настоящей виртуалке Scratch (scratch-vm).
//
// Что настоящее: все скрипты, блоки, переменные, тайминги wait/повторов,
// планировщик кадров, рассылки, клоны, «касания» (по прямоугольникам костюмов).
// Что заглушено: рисование (canvas/svg не нужны), звук (mp3 не декодируются),
// время (виртуальные часы: 1 шаг = 1/60 с, Date.now двигаем сами).
//
// Запуск:  cd tools && node run_vm.js <файл.sb3> [gameplay|win|lose|all]
//
// Сценарии:
//   gameplay — обычная игра с ботом (пробел / стрелки), ждём смены актов;
//   win      — принудительно «собираем» звёзды и проверяем цепочку победы;
//   lose     — обнуляем жизни и проверяем цепочку проигрыша + «Рестарт»;
//   all      — всё подряд (по умолчанию).

const fs = require('fs');
const VM = require('scratch-vm');
const { ScratchStorage } = require('scratch-storage');

// ---------------------------------------------------------------- браузерные заглушки
class FakeImage {
    constructor() { this.width = 120; this.height = 120; }
    set src(v) { setTimeout(() => this.onload && this.onload(), 0); }
    get src() { return ''; }
}
global.Image = FakeImage;

const fakeCtx = {
    drawImage: () => {}, clearRect: () => {}, fillRect: () => {}, save: () => {}, restore: () => {},
    scale: () => {}, translate: () => {}, rotate: () => {}, beginPath: () => {}, closePath: () => {},
    arc: () => {}, fill: () => {}, stroke: () => {}, moveTo: () => {}, lineTo: () => {},
    getImageData: (x, y, w, h) => ({ data: new Uint8ClampedArray(Math.max(4, w * h * 4)), width: w, height: h }),
    putImageData: () => {}, createImageData: (w, h) => ({ data: new Uint8ClampedArray(Math.max(4, w * h * 4)) }),
    measureText: () => ({ width: 10 }), fillText: () => {}, strokeText: () => {},
};
function makeCanvas(w = 120, h = 120) {
    return {
        width: w, height: h, style: {}, _fake: true,
        getContext: () => fakeCtx,
        toDataURL: () => 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==',
        toBlob: (cb) => cb && cb(null),
        getBoundingClientRect: () => ({ left: 0, top: 0, width: w, height: h }),
        addEventListener: () => {}, appendChild: () => {}, setAttribute: () => {},
    };
}
global.document = {
    createElement: (tag) => (String(tag).toLowerCase() === 'canvas' ? makeCanvas()
        : { style: {}, appendChild: () => {}, setAttribute: () => {}, addEventListener: () => {} }),
    createElementNS: () => makeCanvas(),
    body: { appendChild: () => {}, style: {} },
    documentElement: { style: {} },
    getElementById: () => null,
    addEventListener: () => {},
};
global.window = global;
global.requestAnimationFrame = () => 0;
global.cancelAnimationFrame = () => {};
global.devicePixelRatio = 1;
global.HTMLCanvasElement = function () {};
global.HTMLVideoElement = function () {};
global.Blob = global.Blob || function () {};

const bitmapAdapter = {
    resize: (canvas, w, h) => makeCanvas(w, h),
    convertDataURIToBinary: (dataURI) => Buffer.from(String(dataURI).split(',')[1] || '', 'base64'),
    getPixel: () => [0, 0, 0, 0],
};

// ---------------------------------------------------------------- рендерер-«геометрия»
// Рисовать нечем, но виртуалке нужны позиции и размеры: по ним она считает
// «касается края / другого спрайта». Размеры берём из настоящих костюмов (.sb3).
const drawables = new Map();
const spriteDims = {};          // имя спрайта -> {w, h} (максимум по костюмам)
const costumeDims = {};         // имя спрайта -> {имя костюма: {w, h}}
let vmRef = null;

function dimsOfDrawable(id) {
    const d = drawables.get(id);
    if (!d) return { w: 100, h: 100 };
    let dims = { w: 100, h: 100 };
    if (vmRef) {
        const t = vmRef.runtime.targets.find(x => x.drawableID === id);
        if (t) {
            const cos = (t.sprite.costumes || [])[t.currentCostume || 0];
            const byName = costumeDims[t.getName()] || costumeDims[t.sprite.name];
            dims = (cos && byName && byName[cos.name]) || spriteDims[t.getName()] || dims;
        }
    }
    return dims;
}
function box(id) {
    const d = drawables.get(id);
    if (!d) return { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 };
    const dims = dimsOfDrawable(id);
    const w = dims.w * (d.sx || 1);
    const h = dims.h * (d.sy || 1);
    return { left: d.x - w / 2, right: d.x + w / 2, top: d.y + h / 2, bottom: d.y - h / 2, width: w, height: h };
}
function overlaps(a, b) {
    return a.left < b.right && a.right > b.left && a.bottom < b.top && a.top > b.bottom;
}

const apiCalls = {};
function bump(k) { apiCalls[k] = (apiCalls[k] || 0) + 1; }
let nextDrawable = 1000;
const renderer = {
    createDrawable: () => { const id = nextDrawable++; drawables.set(id, { x: 0, y: 0, sx: 1, sy: 1, visible: true }); return id; },
    destroyDrawable: (id) => drawables.delete(id),
    updateDrawablePosition: (id, pos) => { bump('position'); const d = drawables.get(id); if (d && Array.isArray(pos)) { d.x = pos[0]; d.y = pos[1]; } },
    updateDrawableDirectionScale: (id, dir, scale) => {
        bump('dirScale');
        const d = drawables.get(id);
        // scratch-vm отдаёт масштаб в процентах (26), а не в долях — делим на 100
        if (d && Array.isArray(scale)) { d.sx = Math.abs(scale[0]) / 100; d.sy = Math.abs(scale[1]) / 100; }
        else notes.push('dirScale без массива: ' + JSON.stringify(scale));
    },
    updateDrawableVisible: (id, v) => { const d = drawables.get(id); if (d) d.visible = v; },
    updateDrawableSkinId: () => {},
    updateDrawableEffect: () => {},
    setDrawableOrder: () => 0,
    getDrawableOrder: () => 0,
    createBitmapSkin: () => 1, createSVGSkin: () => 1, createTextSkin: () => 1,
    updateTextSkin: () => {}, destroySkin: () => {},
    getSkinSize: () => [120, 120],
    getCurrentSkinSize: (id) => { const b = box(id); return [b.width, b.height]; },
    getBounds: (id) => box(id),
    getFastBounds: (id) => box(id),
    getBoundsForBubble: (id) => box(id),
    getFencedPositionOfDrawable: (id, pos) => pos,
    isTouchingDrawables: (id, ids) => {
        const a = drawables.get(id);
        if (!a || !a.visible) return false;
        return (ids || []).some(other => {
            const b = drawables.get(other);
            return b && b.visible && other !== id && overlaps(box(id), box(other));
        });
    },
    isTouchingColor: () => false,
    penClear: () => {},
    extractDrawableScreenSpace: () => ({ imageData: null }),
    draw: () => {},
};

// ---------------------------------------------------------------- звук-заглушка
const audioEngine = {
    createBank: () => new Proxy({
        addSoundPlayer: () => {}, playSound: () => {}, stopAllSounds: () => {},
        stop: () => {}, stopSoundsForTarget: () => {}, getSoundState: () => ({ isPlaying: false }),
        setEffects: () => {}, setVolume: () => {},
    }, { get: (t, p) => (p === 'then' ? undefined : (typeof t[p] !== 'undefined' ? t[p] : () => 0)) }),
    decodeSoundPlayer: (sound) => { decodeCalls++; return Promise.resolve(new Proxy({
        id: 'snd-' + (sound.soundId || Math.random()),
        buffer: {
            sampleRate: sound.rate || 44100,
            length: sound.sampleCount || 44100,
            duration: (sound.sampleCount || 44100) / (sound.rate || 44100),
            numberOfChannels: 1,
        },
        play: () => Promise.resolve(), stop: () => {}, isPlaying: () => false,
        on: () => {}, off: () => {}, setPlaybackRate: () => {}, getPlaybackRate: () => 1,
        destroy: () => {}, dispose: () => {},
    // then обязан быть undefined, иначе промис считает объект thenable и висит
    }, { get: (t, p) => (p === 'then' ? undefined : (typeof t[p] !== 'undefined' ? t[p] : () => 0)) })); },
    playSound: (sound, target, cb) => { if (cb) setTimeout(() => cb(), 0); },
    stopAllSounds: () => {}, stopSoundsForTarget: () => {},
    getSoundState: () => ({ isPlaying: false, playbackRate: 1 }),
    getCurrentVolume: () => 0, setVolume: () => {}, isMicActive: () => false,
};

const safeRenderer = new Proxy(renderer, { get: (t, p) => (typeof t[p] !== 'undefined' ? t[p] : () => 0) });
const safeAudio = new Proxy(audioEngine, { get: (t, p) => (p === 'then' ? undefined : (typeof t[p] !== 'undefined' ? t[p] : () => 0)) });

// ---------------------------------------------------------------- виртуалка
const vm = new VM();
vmRef = vm;
vm.attachStorage(new ScratchStorage());
vm.attachRenderer(safeRenderer);
vm.attachAudioEngine(safeAudio);
vm.attachV2BitmapAdapter(bitmapAdapter);

let vnow = 0;
Date.now = () => vnow;                                   // виртуальные часы (wait, таймеры)
try { global.performance.now = () => vnow; } catch (e) {}

const notes = [];
const log = console.log.bind(console);
console.log = (...a) => notes.push(a.join(' '));
console.error = (...a) => notes.push('ERR ' + a.join(' '));
console.warn = (...a) => notes.push('WARN ' + a.join(' '));

const file = process.argv[2];
const scenario = process.argv[3] || 'all';

// размеры костюмов из project.json (для «касаний»)
(function readDims() {
    const zip = new (require('jszip'))();
    return zip.loadAsync(fs.readFileSync(file)).then(z => z.file('project.json').async('string')).then(txt => {
        const pj = JSON.parse(txt);
        for (const t of pj.targets) {
            let w = 0, h = 0;
            costumeDims[t.name] = {};
            for (const c of t.costumes || []) {
                const res = c.bitmapResolution || 1;
                const cw = (c.width || 0) / res, ch = (c.height || 0) / res;
                if (cw && ch) costumeDims[t.name][c.name] = { w: cw, h: ch };
                w = Math.max(w, cw);
                h = Math.max(h, ch);
            }
            if (w && h) spriteDims[t.name] = { w, h };
        }
    });
})();

const STATE = ['игра', 'акт', 'жизни', 'звёзды', 'время', 'победа', 'осталось', 'музыка', 'скорость'];
function vars() {
    const st = vm.runtime.getTargetForStage();
    const out = {};
    for (const id of Object.keys(st.variables)) out[st.variables[id].name] = st.variables[id].value;
    return out;
}
function setVar(name, value) {
    const st = vm.runtime.getTargetForStage();
    for (const id of Object.keys(st.variables)) {
        if (st.variables[id].name === name) { st.variables[id].value = value; return true; }
    }
    return false;
}
function backdropName() {
    const st = vm.runtime.getTargetForStage();
    const c = st.sprite.costumes[st.currentCostume];
    return c ? c.name : '?';
}
function stateStr() {
    const v = vars();
    const tg = {};
    vm.runtime.targets.forEach(t => { tg[t.getName()] = (tg[t.getName()] || 0) + 1; });
    const clones = Object.entries(tg).filter(([, n]) => n > 1).map(([k, n]) => `${k}×${n}`).join(' ');
    const h = hero();
    const hy = h ? ` Мила(x=${h.x.toFixed(0)},y=${h.y.toFixed(0)})` : ' Мила(скрыта)';
    return STATE.filter(k => k in v).map(k => `${k}=${v[k]}`).join(' ') + hy +
        ` фон=${backdropName()} потоков=${vm.runtime.threads.length}` + (clones ? ` клоны: ${clones}` : '');
}

// ---------------------------------------------------------------- шаг и ввод
const keysDown = new Set();
function press(key) {
    if (keysDown.has(key)) return;
    keysDown.add(key);
    vm.postIOData('keyboard', { key, isDown: true });
}
function release(key) {
    if (!keysDown.has(key)) return;
    keysDown.delete(key);
    vm.postIOData('keyboard', { key, isDown: false });
}
function hero() { return vm.runtime.targets.find(t => t.getName() === 'Мила' && t.visible); }
function clonesOf(name) {
    return vm.runtime.targets.filter(t => t.getName() === name && t.visible &&
        !(vm.runtime.targets.indexOf(t) === 0) && typeof t.x === 'number');
}
let spaceHold = 0;
let spaceCooldown = 0;
function tickInput() {
    // переменные из VM приходят строками — приводим к числу
    const v = vars();
    const want = new Set();
    const h = hero();
    const act = Number(v['акт']);
    if (h && Number(v['игра']) === 1) {
        if (act === 1) {
            // прыжок, если впереди сугроб или ёлка
            // прыгаем в последний момент: сугроб в 10..75 px впереди
            // касание наступает, когда сугроб ближе ~90 px, прыжок длится ~0.3 с,
            // поэтому прыгаем заранее — за ~150 px до героя
            const dxs = clonesOf('Сугроб').map(d => d.x - h.x).filter(dx => dx > 180 && dx < 265);
            if (dxs.length && spaceHold === 0) {
                spaceHold = 12;
                if (process.env.VM_TRACE_BOT) notes.push(`BOT t=${(vnow / 1000).toFixed(1)} прыжок, сугроб dx=${dxs[0].toFixed(0)}`);
            }
        } else if (act === 2) {
            // к ближайшей звезде, от ёлки — в сторону
            const stars = clonesOf('Звезда').sort((a, b) => Math.abs(a.x - h.x) - Math.abs(b.x - h.x));
            const trees = clonesOf('Ёлка').filter(t => Math.abs(t.x - h.x) < 150);
            let targetY = stars.length ? stars[0].y : h.y;
            if (trees.length) {
                const t = trees[0];
                targetY = t.y > h.y ? Math.max(-150, t.y - 140) : Math.min(95, t.y + 140);
            }
            if (h.y < targetY - 12) want.add('ArrowUp');
            if (h.y > targetY + 12) want.add('ArrowDown');
        } else if (act === 3) {
            // уклонение от снежков
            const balls = clonesOf('Снежок').filter(b => Math.abs(b.x - h.x) < 190);
            if (balls.length) {
                const b = balls.sort((a, c) => Math.abs(a.x - h.x) - Math.abs(c.x - h.x))[0];
                if (b.y >= h.y - 10 && h.y > -70) want.add('ArrowDown');
                else if (h.y < 30) want.add('ArrowUp');
                else want.add(b.x > h.x ? 'ArrowLeft' : 'ArrowRight');
            }
            if (spaceHold === 0 && spaceCooldown === 0 && Math.random() < 0.03) { spaceHold = 10; spaceCooldown = 60; }
        }
    }
    if (spaceHold > 0) { want.add(' '); spaceHold--; }
    if (spaceCooldown > 0) spaceCooldown--;
    for (const k of [' ', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']) {
        if (want.has(k)) press(k); else release(k);
    }
}

let frame = 0;
function step(n, opts = {}) {
    for (let i = 0; i < n; i++) {
        if (opts.bot) tickInput();
        frame++;
        vnow += 1000 / 60;
        try { vm.runtime._step(); } catch (e) {
            notes.push('STEP_ERR ' + (e && e.stack ? String(e.stack).split('\n').slice(0, 4).join(' | ') : String(e)));
        }
        if (vm.runtime.threads.length > 700) { notes.push('ПЕРЕПОЛНЕНИЕ ПОТОКОВ'); return; }
    }
}
function sec(s, opts) { step(Math.round(s * 60), opts); }

// трассировка запусков обработчиков
const trace = [];
function installTrace() {
    const orig = vm.runtime.startHats.bind(vm.runtime);
    vm.runtime.startHats = function (opcode, fields, target) {
        const th = orig(opcode, fields, target);
        if (/broadcastreceived/.test(opcode)) {
            trace.push(`t=${(vnow / 1000).toFixed(1)} «${fields && fields.BROADCAST_OPTION}» → ${th ? th.length : 0}`);
        }
        return th;
    };
}

const marks = [];
function watch(label, seconds, opts = {}) {
    const parts = [];
    for (let m = 1; m <= Math.round(seconds); m++) {
        sec(1, opts);
        if (m % 2 === 0 || m === 1) parts.push(`[${m}с] ${stateStr()}`);
    }
    log(`--- ${label} ---`);
    parts.forEach(p => log('  ' + p));
    marks.push([label, stateStr()]);
}

// при VM_TRACE_TOUCH=1 пишем все сработавшие «касания» — видно, кто кого задел
function installTouchTrace() {
    const proto = Object.getPrototypeOf(vm.runtime.targets.find(t => !t.isStage));
    const orig = proto.isTouchingSprite;
    proto.isTouchingSprite = function (name) {
        const r = orig.call(this, name);
        if (r) {
            const a = box(this.drawableID);
            notes.push(`TOUCH t=${(vnow / 1000).toFixed(1)} ${this.getName()}(${this.x.toFixed(0)},${this.y.toFixed(0)} s=${this.size}) ~ ${name} герой_y=${hero() ? hero().y.toFixed(0) : '?'}` +
                ` бокс=[${a.left.toFixed(0)}..${a.right.toFixed(0)}]x[${a.bottom.toFixed(0)}..${a.top.toFixed(0)}]`);
        }
        return r;
    };
}

let decodeCalls = 0;
const keepAlive = setInterval(() => {}, 500);
const loadWatch = setInterval(() => {
    log(`  ...загрузка: таргетов ${vm.runtime.targets.length}, декодировано звуков ${decodeCalls}, ожиданий ${notes.length}`);
}, 3000);
if (!process.env.VM_DEBUG_LOAD) clearInterval(loadWatch);
setTimeout(() => { log('WATCHDOG: loadProject не завершился за 90 с'); process.exit(3); }, 90000);

vm.loadProject(fs.readFileSync(file)).then(() => {
    clearInterval(keepAlive);
    clearInterval(loadWatch);
    log('ЗАГРУЗКА: ok, таргетов ' + vm.runtime.targets.length);
    // без этого бюджет кадра нулевой и не выполняется ни один блок
    vm.runtime.currentStepTime = 1000 / 30;
    installTrace();
    if (process.env.VM_TRACE_TOUCH) installTouchTrace();

    // Заглушка рендерера отдаёт не «настоящий» размер скина, поэтому встроенный
    // кламп в RenderedTarget.setSize (min/max относительно текущего размера)
    // давал мусорные проценты (снежинка «7%» превращалась в 65%). В реальном
    // Scratch таких костюмов кламп не касается — фиксируем запрошенный размер.
    (function neutralizeSizeClamp() {
        const proto = Object.getPrototypeOf(vm.runtime.targets.find(t => !t.isStage));
        proto.setSize = function (size) {
            if (this.isStage) return;
            this.size = size;
            if (this.renderer) {
                const {direction, scale} = this._getRenderedDirectionAndScale();
                this.renderer.updateDrawableDirectionScale(this.drawableID, direction, scale);
            }
            this.runtime.requestTargetsUpdate(this);
        };
    })();

    if (scenario === 'keystest') {
        vm.greenFlag();
        sec(19);
        const h = hero();
        log(`до прыжка: Мила y=${h && h.y}`);
        press(' ');
        log('getKeyIsDown(space)=' + vm.runtime.ioDevices.keyboard.getKeyIsDown('space'));
        for (let i = 0; i < 12; i++) { sec(1 / 60); log(`  кадр ${i}: y=${hero() && hero().y}`); }
        process.exit(0);
    }

    // ---------- 0. кадры сцены: снимки состояния для композиционного аудита
    if (scenario === 'frames') {
        const outFile = process.argv[4] || '../dist/frames.json';
        const shots = [];
        const shot = (label) => {
            const list = vm.runtime.targets
                .filter(t => t.visible && t.drawableID !== undefined)
                .map((t, i) => {
                    const cos = (t.sprite.costumes || [])[t.currentCostume || 0] || {};
                    const fx = t.effects || {};
                    return {
                        layer: i, name: t.getName(), x: +t.x.toFixed(2), y: +t.y.toFixed(2),
                        size: +(t.size || 100).toFixed(2), dir: +t.direction || 90,
                        rot: t.rotationStyle,
                        costume: cos.name, md5: cos.assetId || cos.md5,
                        fmt: cos.dataFormat || 'png',
                        rcX: cos.rotationCenterX, rcY: cos.rotationCenterY,
                        res: cos.bitmapResolution || 1,
                        ghost: +(fx.ghost || 0).toFixed(1), bright: +(fx.brightness || 0).toFixed(1),
                        say: t._sayText || '',
                    };
                });
            shots.push({ label, t: +(vnow / 1000).toFixed(2), backdrop: backdropName(), targets: list });
            log(`  кадр «${label}» t=${(vnow / 1000).toFixed(1)}с фон=${backdropName()} видимых ${list.length}`);
        };
        const waitAct = (n, max = 80) => {
            for (let i = 0; i < max * 60 && Number(vars()['акт']) !== n; i++) step(1, { bot: true });
        };
        const waitVar = (name, value, max = 40) => {
            for (let i = 0; i < max * 60 && Number(vars()[name]) !== value; i++) step(1, { bot: true });
        };
        vm.greenFlag();
        sec(2.2);
        shot('01_prolog_title');            // титр + голос за кадром
        sec(5.5);
        shot('02_prolog_dialog');           // Дед Мороз и Мила на сцене
        sec(3.2);
        shot('03_prolog_dialog_mila');
        waitAct(1);
        sec(2.4);
        shot('04_act1_start');              // подсказка акта 1
        setVar('жизни', 20);
        sec(2.0);
        shot('05_act1_play');
        setVar('звёзды', 5);
        waitAct(2);
        sec(2.2);
        shot('06_act2_start');
        setVar('жизни', 20);
        sec(1.6);
        shot('07_act2_play');
        setVar('звёзды', 10);
        waitAct(3);
        sec(3.0);                             // Реп6 (метель) + подсказка акта 3
        shot('08_act3_start');
        sec(3.0);
        shot('09_act3_play');
        setVar('жизни', 20);
        setVar('осталось', 1);
        waitVar('победа', 1);
        sec(3.0);
        shot('10_win');
        sec(4.2);                             // Реп8: Дед Мороз + субтитр + кнопка
        shot('10b_win_finale');
        // проигрыш — со второго запуска
        vm.greenFlag();
        waitAct(1);
        sec(1.0);
        setVar('жизни', 0);
        for (let i = 0; i < 20 * 60 && backdropName() !== 'проигрыш'; i++) step(1, { bot: true });
        sec(2.6);
        shot('11_lose');
        fs.writeFileSync(outFile, JSON.stringify({ file, shots }, null, 1));
        log('  кадры записаны: ' + outFile);
        process.exit(0);
    }

    // ---------- 1. обычная игра
    if (scenario === 'all' || scenario === 'gameplay') {
        vm.greenFlag();
        notes.length = 0;
        watch('флаг → титр → пролог (~17.5 с)', 20);
        log('  рассылки: ' + trace.slice(0, 14).join(' | '));
        trace.length = 0;
        watch('игра с ботом', 45, { bot: true });
        log('  рассылки: ' + trace.slice(0, 14).join(' | '));
    }

    // ---------- 2. победа
    if (scenario === 'all' || scenario === 'win') {
        vm.greenFlag();
        sec(19, { bot: true });                       // пролог
        // запас жизней: сценарий проверяет цепочку победы, а не меткость бота
        setVar('жизни', 20);
        sec(2, { bot: true });
        let v = vars();
        log(`--- победа: старт с акт=${v['акт']} ---`);
        setVar('звёзды', 5);                          // «собрали» 5 звёзд в акте 1
        sec(6, { bot: true });
        setVar('жизни', 20);
        setVar('звёзды', 10);                         // и ещё 5 в акте 2
        sec(8, { bot: true });
        setVar('жизни', 20);
        v = vars();
        log(`  после акта 2: акт=${v['акт']} звёзды=${v['звёзды']} жизни=${v['жизни']}`);
        watch('акт 3 «крыша» (20 с) + финал', 26, { bot: true });
        v = vars();
        log(`  ИТОГ победы: победа=${v['победа']} фон=${backdropName()} игра=${v['игра']}`);
        log('  рассылки финала: ' + trace.slice(-8).join(' | '));
        trace.length = 0;
    }

    // ---------- 3. проигрыш и «Ещё раз»
    if (scenario === 'all' || scenario === 'lose') {
        vm.greenFlag();
        sec(19, { bot: true });
        setVar('жизни', 0);
        watch('проигрыш (жизни=0)', 12, { bot: true });
        let v = vars();
        log(`  ИТОГ проигрыша: победа=${v['победа']} фон=${backdropName()} игра=${v['игра']}`);
        log('  рассылки: ' + trace.slice(-6).join(' | '));
        trace.length = 0;
        // кнопка «Ещё раз» шлёт «Рестарт»
        const st = vm.runtime.getTargetForStage();
        const restart = Object.values(st.variables).find(x => x.type === 'broadcast_msg' && x.name.toLowerCase() === 'рестарт');
        if (restart) {
            vm.runtime.startHats('event_whenbroadcastreceived', { BROADCAST_OPTION: restart.name });
            watch('после «Рестарт» (кнопка «Ещё раз»)', 10, { bot: true });
            v = vars();
            log(`  после рестарта: акт=${v['акт']} жизни=${v['жизни']} звёзды=${v['звёзды']} время=${v['время']} фон=${backdropName()}`);
        } else {
            log('  ВНИМАНИЕ: рассылка «Рестарт» не найдена');
        }
    }

    log('--- вызовы API рендерера: ' + JSON.stringify(apiCalls));
    if (process.env.VM_TRACE_TOUCH) {
        const touches = notes.filter(n => n.startsWith('TOUCH'));
        log('--- касания (' + touches.length + ') ---');
        notes.filter(n => n.startsWith('BOT')).slice(0, 12).forEach(n => log('  ' + n));
        touches.slice(0, 25).forEach(t => log('  ' + t));
    }
    const uniq = [...new Set(notes)].filter(n => !/audio engine|V2 Bitmap|Cannot found image/i.test(n));
    log('--- сообщения рантайма (' + uniq.length + ') ---');
    uniq.slice(0, 12).forEach(n => log('  ' + n.slice(0, 240)));
    process.exit(0);
}).catch(e => {
    clearInterval(keepAlive);
    log('ЗАГРУЗКА: ОШИБКА ' + JSON.stringify(e && (e.stack || e.message || e)));
    process.exit(2);
});

// отладка клавиатуры: node run_vm.js <файл> keystest
