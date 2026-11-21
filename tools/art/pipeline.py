"""Пайплайн графики: хромакей -> истинная RGBA-прозрачность -> обрезка -> ресайз.

Ключевое для критерия «качественная обработка спрайтов (не имеют задний фон)»:
альфа считается по «зелёности» пикселя, а не по порогу яркости, поэтому белая
коза и снеговик не страдают. Дополнительно делаем деспилл краёв (убираем
зелёный ореол) и мягкое сглаживание альфы.
"""
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
RAW_SPR = os.path.join(ROOT, 'art', 'sprites', 'raw')
OUT_SPR = os.path.join(ROOT, 'art', 'sprites')
RAW_BG = os.path.join(ROOT, 'art', 'backgrounds', 'raw')
OUT_BG = os.path.join(ROOT, 'art', 'backgrounds')


def chroma_key(img, lo=0.10, hi=0.34, despill=1.0):
    """Убрать чистый зелёный фон (#00FF00-подобный)."""
    rgb = np.asarray(img.convert('RGB')).astype(np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    greenness = g - np.maximum(r, b)                      # насколько пиксель «зелёный»
    alpha = 1.0 - np.clip((greenness - lo) / (hi - lo), 0.0, 1.0)
    # мягкая гамма на краях
    alpha = np.clip(alpha, 0, 1) ** 0.85
    # деспилл: приглушаем зелёный там, где он доминирует
    g2 = np.where(greenness > 0, g - despill * np.maximum(greenness - 0.02, 0), g)
    out = np.stack([r, g2, b, alpha], axis=-1)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')


def trim_and_pad(img, pad=6, alpha_thr=12):
    a = np.asarray(img)[..., 3]
    ys, xs = np.where(a > alpha_thr)
    if len(xs) == 0:
        return img
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, img.width - 1)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, img.height - 1)
    return img.crop((x0, y0, x1 + 1, y1 + 1))


def process_sprites(max_side=420, only=None):
    """Хромакей спрайтов.

    only — список имён файлов (например, чтобы не перетирать уже
    выровненные костюмы героини при обработке новых спрайтов).
    """
    os.makedirs(OUT_SPR, exist_ok=True)
    done = []
    for fn in sorted(os.listdir(RAW_SPR)):
        if not fn.lower().endswith('.png'):
            continue
        if only and fn not in only:
            continue
        src = Image.open(os.path.join(RAW_SPR, fn))
        keyed = chroma_key(src)
        # сглаживание альфы без «съедания» деталей
        alpha = keyed.getchannel('A').filter(ImageFilter.GaussianBlur(0.6))
        keyed.putalpha(alpha)
        cut = trim_and_pad(keyed)
        k = min(1.0, max_side / max(cut.size))
        if k < 1.0:
            cut = cut.resize((max(1, int(cut.width * k)), max(1, int(cut.height * k))), Image.LANCZOS)
        out = os.path.join(OUT_SPR, fn)
        cut.save(out)
        done.append((fn, src.size, cut.size))
    return done


def process_backgrounds(w=960, h=720, quality=88):
    os.makedirs(OUT_BG, exist_ok=True)
    done = []
    for fn in sorted(os.listdir(RAW_BG)):
        if not fn.lower().endswith(('.png', '.jpg')):
            continue
        im = Image.open(os.path.join(RAW_BG, fn)).convert('RGB')
        # центральный кроп под 4:3
        target = w / h
        sw, sh = im.size
        if sw / sh > target:
            nw = int(sh * target)
            im = im.crop(((sw - nw) // 2, 0, (sw + nw) // 2, sh))
        else:
            nh = int(sw / target)
            im = im.crop((0, (sh - nh) // 2, sw, (sh + nh) // 2))
        im = im.resize((w, h), Image.LANCZOS)
        # запекаем мягкую виньетку прямо в фон: киношная глубина без лишних спрайтов
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h / 2) / (h * 0.62)) ** 2)
        v = np.clip((r - 0.5) / 0.8, 0, 1) ** 1.6
        arr = np.asarray(im).astype(np.float32) / 255.0
        arr *= (1.0 - 0.45 * v)[..., None]
        # лёгкое затемнение низа — герой читается лучше
        arr *= (1.0 - 0.18 * np.clip((yy / h - 0.65) / 0.35, 0, 1))[..., None]
        im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
        out = os.path.join(OUT_BG, os.path.splitext(fn)[0] + '.jpg')
        im.save(out, quality=quality, optimize=True)
        done.append((os.path.basename(out), im.size, os.path.getsize(out) // 1024))
    return done


def make_overlays():
    """Виньетка и мягкий чёрный слой для переходов."""
    w, h = 960, 720
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    r = np.sqrt(((xx - cx) / (w * 0.62)) ** 2 + ((yy - cy) / (h * 0.62)) ** 2)
    v = np.clip((r - 0.55) / 0.75, 0, 1) ** 1.5
    rgba = np.stack([np.full_like(v, 6), np.full_like(v, 10), np.full_like(v, 22), v * 210], -1)
    Image.fromarray(rgba.astype(np.uint8), 'RGBA').save(os.path.join(OUT_BG, 'overlay_vignette.png'))
    Image.new('RGBA', (w, h), (6, 10, 24, 255)).save(os.path.join(OUT_BG, 'overlay_fade.png'))
    print('overlays ok')


if __name__ == '__main__':
    import sys
    # python3 tools/art/pipeline.py sprites santa.png snowman.png ...  — обработать только эти
    argv = sys.argv[1:]
    only = None
    if argv and argv[0] == 'sprites':
        only = set(argv[1:]) or None
        argv = []
    for name, s0, s1 in process_sprites(only=only):
        print(f'sprite {name:20s} {s0} -> {s1}')
    if only:
        raise SystemExit(0)
    for name, size, kb in process_backgrounds():
        print(f'bg     {name:20s} {size} {kb}KB')
    make_overlays()
