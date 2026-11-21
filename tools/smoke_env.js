// DOM-окружение для scratch-vm/scratch-svg-renderer в Node.
const { JSDOM } = require('jsdom');
const napi = require('@napi-rs/canvas');
const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.HTMLElement = dom.window.HTMLElement;
global.XMLSerializer = dom.window.XMLSerializer;
global.DOMParser = dom.window.DOMParser;
global.Node = dom.window.Node;
global.CanvasRenderingContext2D = napi.CanvasRenderingContext2D || function () {};
global.Image = napi.Image;
global.window.Image = napi.Image;
global.requestAnimationFrame = (cb) => setTimeout(() => cb(0), 16);
global.cancelAnimationFrame = (id) => clearTimeout(id);
// canvas-элементы jsdom отдаём в нативную реализацию
const origCreate = document.createElement.bind(document);
document.createElement = (tag) => {
    const el = origCreate(tag);
    if (String(tag).toLowerCase() === 'canvas') {
        const c = napi.createCanvas(300, 150);
        el.getContext = (...a) => c.getContext(...a);
        Object.defineProperty(el, 'width', { get: () => c.width, set: (v) => { c.width = v; }, configurable: true });
        Object.defineProperty(el, 'height', { get: () => c.height, set: (v) => { c.height = v; }, configurable: true });
        el.toDataURL = () => c.toDataURL();
        el._native = c;
    }
    return el;
};
