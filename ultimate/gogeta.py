"""DBS Gogeta from the supplied sheet (ripped by Mister Man, edited by Azure-Oni): base, SSJ and SSB, 32x32 cells cleaned of JPEG noise."""
import json, os
import numpy as np
from PIL import Image

SHEET = 'ultimate/art/gogeta_sheet.jpg'
# Each form is four rows of cells: down, side, up, then shared poses. Each animation lists cell numbers on the first three rows,
# or ('x', n) for a cell on the fourth row, which only has a side view. VIEWS overrides an animation on one view, whose cell numbers differ.
ANIMS = {
    'idle': [0, 1], 'walk': [2, 3, 4, 5], 'run': [6, 7, 8, 9], 'combo1': [10, 11, 12, 13], 'combo2': [14, 15, 17, 18], 'combo3': [21, 22, 23, 24],
    'blast': [19, 20, 19], 'fire': [19, 20, 20], 'kick': [26, 27, 28], 'powerup': [38, 39], 'hurt': [34],
    'tumble': [('x', 5), ('x', 6), ('x', 7), ('x', 8)], 'down': [('x', 9), ('x', 10), ('x', 11), ('x', 12)], 'rise': [('x', 13), ('x', 14), ('x', 15)],
}
VIEWS = {('powerup', 2): [36, 37], ('combo1', 1): [11, 12, 13, 14], ('combo2', 1): [15, 16, 17, 18], ('blast', 1): [18, 19, 18], ('fire', 1): [18, 19, 19]}
# Animation slots, following the order in actors.json: 0 idle, 1 walk, 2 run, 3 and 10 and 13 charge, 4-6 melee, 7 and 15 hurt, 8 9 21 ki, 14 and 20 strikes, 16-17 knocked down, 18 the pose held while firing a skill.
# Slot 18 is 'fire', not 'blast': the Kamehameha holds frame 0 and then shows frames 1 and 2 in turn while the beam is out (sprites.INDEXED), so
# blast's third cell (the wind-up again) put Gogeta back into the wind-up every few frames while firing (test_frames.py).
SLOTS = {0: 'idle', 1: 'walk', 2: 'run', 3: 'powerup', 4: 'combo1', 5: 'combo2', 6: 'combo3', 7: 'hurt', 8: 'blast', 9: 'blast', 10: 'powerup', 11: 'idle',
         12: 'idle', 13: 'powerup', 14: 'kick', 15: 'hurt', 16: 'tumble', 17: 'down', 18: 'fire', 19: 'idle', 20: 'kick', 21: 'blast'}
FORMS = {'ssb': 0, 'ssj': 4, 'base': 8}     # first band of each form


def grid(a):
    bright = (a[..., 1] > 98) & (a[..., 0] < 40) & (a[..., 2] > 100)
    bands = []; s = None
    frac = bright[:, :600].mean(1)
    for y, v in enumerate(frac[:416]):
        if v < 0.6 and s is None: s = y
        if v >= 0.6 and s is not None:
            if y - s > 20: bands.append((s, y))
            s = None
    cells = []
    for y0, y1 in bands:
        col = bright[y0:y1].mean(0); c = []; s = None
        for x, v in enumerate(col):
            if v < 0.7 and s is None: s = x
            if v >= 0.7 and s is not None:
                if x - s > 8: c.append((s, x))
                s = None
        cells.append(c)
    return bands, cells


def parts(mask):
    seen = np.zeros_like(mask); out = []
    for start in zip(*np.nonzero(mask)):
        if seen[start]: continue
        part = []; todo = [start]; seen[start] = True
        while todo:
            y, x = todo.pop(); part.append((y, x))
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; todo.append((ny, nx))
        out.append(part)
    return out


def tidy(c, m):
    """Edge ink goes to the outline's black; one-pixel whiskers that JPEG left against the background go."""
    c = c.copy(); m = m.copy()
    def neighbours(m):
        p = np.pad(m, 1); return p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    for _ in range(2):
        m &= ~((neighbours(m) <= 1) & (c.sum(2) < 330))
    edge = m & (neighbours(m) < 4)
    dark = edge & (c.sum(2) < 300)
    c[dark] = 0
    return c, m


def raw_mask(a, bands, cells, band, n):
    """One cell's figure on its whole box, before cut() crops it: (rgb, mask)."""
    y0, y1 = bands[band]; x0, x1 = cells[band][n]
    c = a[y0:y1, x0:x1]
    d = np.abs(c - np.array((0, 76, 78))).sum(2)
    m = (d > 62) & ~((c[..., 0] < 30) & (np.abs(c[..., 1] - c[..., 2]) < 26) & (c[..., 1] < 150) & (c[..., 1] > 50))
    keep = np.zeros_like(m)
    for p in parts(m):
        if len(p) >= 10:
            for q in p: keep[q] = True
    return tidy(c, keep)


def cut(a, bands, cells, band, n):
    """One cell as (rgb, mask): the dark cell background goes by colour, stray compression specks by size."""
    c, keep = raw_mask(a, bands, cells, band, n)
    ys, xs = np.nonzero(keep)
    return c[ys.min():ys.max() + 1, xs.min():xs.max() + 1], keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def flatten(a, bands, cells, form, colours=14):
    """One colour table for a whole form, so JPEG's pixel-to-pixel colour drift becomes the flat colours the sprites were drawn with."""
    b = FORMS[form]; ink = []
    for r in range(4):
        for n in range(len(cells[b + r])):
            try: c, m = cut(a, bands, cells, b + r, n)
            except ValueError: continue
            ink.append(c[m])
    ink = np.concatenate(ink).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(ink.reshape(-1, 1, 3)).quantize(colours, method=Image.Quantize.MEDIANCUT, kmeans=4)
    table = np.array(im.getpalette()[:colours * 3]).reshape(-1, 3)
    return lambda q: table[((table - q) ** 2).sum(1).argmin()]


def despeckle(rgb, m):
    """A pixel unlike all four neighbours is compression noise (the sprites use blocks of colour), so it takes the commonest colour around it. Black ink stays: it is outline and eyes."""
    out = rgb.copy(); h, w = m.shape
    for y in range(h):
        for x in range(w):
            if not m[y, x] or rgb[y, x].sum() < 60: continue
            around = [tuple(rgb[y + j, x + i]) for j, i in ((-1, 0), (1, 0), (0, -1), (0, 1)) if 0 <= y + j < h and 0 <= x + i < w and m[y + j, x + i]]
            if len(around) >= 3 and tuple(rgb[y, x]) not in around:
                near = [v for v in around if sum(v) >= 60] or around
                out[y, x] = max(set(near), key=near.count)
    return out


def hair_tone(v, form):
    """Is this colour one of the hair's? Blue or yellow by form; base hair is black, so it has no highlights to clean."""
    r, g, b = int(v[0]), int(v[1]), int(v[2])
    if form == 'ssb': return b > r + 50 and g > r + 20
    if form == 'ssj': return r > b + 70 and g > b + 60 and abs(r - g) < 45
    return False


def calm_hair(rgb, m, form):
    """JPEG sparks the hair with near-white pixels. Where hair colours surround one, it takes the lightest hair colour next to it."""
    out = rgb.copy(); h, w = m.shape
    for y in range(h):
        for x in range(w):
            if not m[y, x] or rgb[y, x].min() < 175: continue
            around = [tuple(rgb[j, i]) for j in range(max(0, y - 1), min(h, y + 2)) for i in range(max(0, x - 1), min(w, x + 2)) if m[j, i] and (j, i) != (y, x)]
            tones = [v for v in around if hair_tone(v, form)]
            if len(tones) >= 2: out[y, x] = max(tones, key=sum)
    return out


def flat_cell(c, m, flat, form):
    rgb = np.zeros(c.shape, int)
    for y, x in zip(*np.nonzero(m)): rgb[y, x] = flat(c[y, x])
    return despeckle(calm_hair(rgb, m, form), m)


def cells_of(name):
    """The cells of one animation as [(sheet row 0-3, cell number, mirrored)], in sprites.py's order: down, up, side (the sheet's is down,
    side, up; its side views face right, the game's face left and it mirrors them)."""
    out = []
    for row in (0, 2, 1):
        for f in VIEWS.get((name, row), ANIMS[name]):
            out.append((3, f[1], row == 1) if isinstance(f, tuple) else (row, f, row == 1))
    return out


def place(a, bands, cells, form, row, n, flip):
    """One cell cut from the sheet and where it goes on its 32x32 frame: (rgb, mask, top, left) (the feet on the bottom row, centred), and
    the box it was cut from: (sheet y, sheet x) of the cut's corner. (A cell over 32 keeps its bottom rows and left columns.)"""
    b = FORMS[form]; y0, _ = bands[b + row]; x0, _ = cells[b + row][n]
    c, m = cut(a, bands, cells, b + row, n)
    ys, xs = np.nonzero(raw_mask(a, bands, cells, b + row, n)[1])
    corner = (y0 + ys.min(), x0 + xs.min())
    if flip: c, m = c[:, ::-1], m[:, ::-1]
    h, w = m.shape
    if h > 32 or w > 32: h2, w2 = min(h, 32), min(w, 32); c, m = c[h - h2:, :w2], m[h - h2:, :w2]; h, w = h2, w2
    return c, m, 32 - h, (32 - w) // 2, corner


EYE_HOLE = 4          # a see-through patch this small inside the figure is an eye (or a pinhole), not a gap between limbs
HAIR = (1, 25, 28, 242)   # his hair's black and gold (a pinhole with only these round it is in his hair, and takes their colour)


def frame(a, bands, cells, flat, form, row, n, flip, one):
    """One cell as its indexed 32x32 frame, and (top, left, corner, width) of place(). The sheet's eyes are near its background's teal, so
    cut() drops them and they were see-through (Nov 10): a patch of up to EYE_HOLE pixels the figure closes round takes the sheet's own
    colour there."""
    from scipy import ndimage
    c, m, top, left, corner = place(a, bands, cells, form, row, n, flip)
    img = np.zeros((32, 32), np.uint8); rgb = flat_cell(c, m, flat, form)
    for y, x in zip(*np.nonzero(m)):
        img[top + y, left + x] = one(rgb[y, x])
    holes, k = ndimage.label(ndimage.binary_fill_holes(img != 0) & (img == 0))
    for t in range(1, k + 1):
        hole = holes == t
        if hole.sum() > EYE_HOLE: continue
        for Y, X in zip(*np.nonzero(hole)):
            y, x = Y - top, X - left
            around = [int(img[j, i]) for j, i in ((Y - 1, X), (Y + 1, X), (Y, X - 1), (Y, X + 1)) if 0 <= j < 32 and 0 <= i < 32]
            if around and all(v in HAIR for v in around): img[Y, X] = max(set(around), key=around.count)   # a pinhole in his hair
            elif 0 <= y < c.shape[0] and 0 <= x < c.shape[1]: img[Y, X] = one(c[y, x])
    return img, (top, left, corner, m.shape[1])


def write_frames(out, form, one):
    """Save indexed 32x32 cells named for sprites.slot_frames. one(rgb) -> palette index."""
    a = np.array(Image.open(SHEET).convert('RGB')).astype(int); bands, cells = grid(a)
    flat = flatten(a, bands, cells, form)
    for name in ANIMS:
        for i, (row, n, flip) in enumerate(cells_of(name)):
            img, _ = frame(a, bands, cells, flat, form, row, n, flip, one)
            Image.fromarray(img).save('%s/gg%s_%s_%02d.png' % (out, form, name, i))


def slots(form):
    return {str(s): 'gg%s_%s' % (form, n) for s, n in SLOTS.items()}
