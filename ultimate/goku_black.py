"""Goku Black and Super Saiyan Rose from the owner's sheet (ultimate/art/goku_black/sheet.png, artist not stated on it).

The sheet's frames are Buu's Fury Goku's own poses: Black's are actor 106's with his gi, sash and boots redrawn, Rose's are Super Saiyan
Goku's (actor 109) with pink hair. They cover about a third of each actor's frames. Each frame of 106 and 109 is either:
  - the sheet's frame of that pose, used exactly as drawn (`python3 ultimate/goku_black.py match` finds them once and keeps the answers
    in ultimate/art/goku_black/frames.json: it takes a few minutes), or
  - Goku's own frame in Black's (or Rose's) colours, learned pixel by pixel from the frames the sheet does have. Nothing is drawn.

Frames are laid on 64x32 canvases with Buu's Fury's origin rule (sprites.Inserter.frame: the canvas's bottom centre is the actor origin),
so a piece at (x, y) of a retail frame lands at canvas column x + 24 and row y + 24.
"""
import json, os, struct, sys
import numpy as np
from PIL import Image

SHEET = 'ultimate/art/goku_black/sheet.png'
MATCHES = 'ultimate/art/goku_black/frames.json'
BASE, ACTOR_LIST = 0x08000000, 0x6B6BD8
SOURCE = {'black': 106, 'rose': 109}          # Buu's Fury Goku and Super Saiyan Goku
USE, LEARN = 0.9, 0.93                         # outline match needed to use a sheet frame, and to learn colours from it
PORTRAITS = {'black': (481, 96, 64), 'rose': (481, 163, 64)}    # (x, y, size) of the sheet's portraits, gold frame included
ROSE_ROW = 190                                 # sheet rows below this y are Rose's
LIGHT, DARK = (0, 128, 128), (0, 64, 64)       # the sheet's background and its frame boxes


def cells(sheet):
    """Every frame on the sheet: [(y, x, mask, rgb)] in reading order, cropped to their ink."""
    from scipy import ndimage
    a = sheet.astype(int); bg = (a == LIGHT).all(2) | (a == DARK).all(2); ink = ~bg
    lab, _ = ndimage.label(~(a == LIGHT).all(2)); out = []
    for s in ndimage.find_objects(lab):
        h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
        if h < 20 or h > 40: continue                       # the portraits and the two cut-off scraps beside them
        m = ink[s]; xs = np.nonzero(m.any(0))[0]
        groups = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1) if w > 40 else [xs]     # two frames that share a box
        for g in groups:
            if len(g) < 3: continue
            mm = m[:, g[0]:g[-1] + 1]; ys = np.nonzero(mm.any(1))[0]
            y0, x0 = s[0].start + ys[0], s[1].start + g[0]
            out.append((int(y0), int(x0), mm[ys[0]:ys[-1] + 1], a[y0:y0 + ys[-1] - ys[0] + 1, x0:x0 + len(mm[0])]))
    out.sort(key=lambda c: (c[0] // 12, c[1]))
    return out


def tiles(rom, o, w, h):
    from wfz import decompress_stream
    t, size = struct.unpack_from('<II', rom, o)
    raw = rom[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(rom, o + 8, size)[0])
    return np.frombuffer(bytes(raw), np.uint8)[:w * h].reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)


def actor_frames(rom, actor):
    """{slot: [[frame, ...] for views down, up, side]}, each frame a 32x64 canvas of OBJ indices."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    rec = u(ACTOR_LIST + 4 * actor) - BASE; out = {}
    for slot in range(u(rec) & 0xFF):
        a = u(rec + 0x54 + 4 * slot)
        if not a: continue
        a -= BASE; n = u(a); views = [[], [], []]
        for f in range(n):
            for d in range(3):
                fp = u(a + 4 + 4 * (f * 4 + d)) - BASE; canvas = np.zeros((32, 64), np.uint8)
                for i in range(u(fp) if 0 < fp < len(rom) else 0):
                    o = fp + 4 + 16 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, o)
                    if not 0 < u(o + 12) - BASE < len(rom) or not w or not h: continue      # a few retail frames point nowhere
                    t = tiles(rom, u(o + 12) - BASE, w, h)
                    for r in range(h):
                        for c in range(w):
                            R, C = y + 24 + r, x + 24 + c
                            if t[r, c] and 0 <= R < 32 and 0 <= C < 64: canvas[R, C] = t[r, c]
                views[d].append(canvas)
        out[slot] = views
    return out


# A front and a back view share an outline: skin in the top of the figure tells them apart (a back view shows hair and at most a little neck).
SKIN_INDEX = [16, 200, 201, 202, 203, 205, 206]
SKIN_RGB = [(128, 80, 24), (168, 120, 56), (216, 168, 96), (240, 192, 112), (192, 144, 80), (144, 96, 40), (160, 104, 48)]
FACE_MIN = {'goku': 8, 'black': 16, 'rose': 4}      # measured: Black's back views show 0-14 skin pixels and fronts 18 or more; Rose's backs 0-3, fronts 5 or more


def top_of(a):
    return a[:max(1, int(0.45 * len(a)))]


def goku_face(canvas):
    ys = np.nonzero((canvas != 0).any(1))[0]
    return int(np.isin(top_of(canvas[ys[0]:ys[-1] + 1]), SKIN_INDEX).sum()) >= FACE_MIN['goku']


def sheet_face(c, form):
    top, m = top_of(c[3]), top_of(c[2])
    return int(sum(((top == s).all(2) & m).sum() for s in SKIN_RGB)) >= FACE_MIN[form]


def match(rom):
    """Find the sheet's frame for each pose of 106 and 109. Slow: run once, keep frames.json."""
    from scipy.signal import correlate2d
    sheet = np.array(Image.open(SHEET).convert('RGB')); cs = cells(sheet)
    result = {'cells': [[c[0], c[1], int(c[2].shape[0]), int(c[2].shape[1])] for c in cs]}
    goku = actor_frames(rom, SOURCE['black'])
    for form, actor in SOURCE.items():
        mine = [i for i, c in enumerate(cs) if (c[0] >= ROSE_ROW) == (form == 'rose')]
        faces = {i: sheet_face(cs[i], form) for i in mine}
        frames = actor_frames(rom, actor); picks = []
        for slot, views in frames.items():
            for d, fr in enumerate(views):
                for f, canvas in enumerate(fr):
                    m = canvas != 0
                    if not m.any(): continue
                    ys, xs = np.nonzero(m.any(1))[0], np.nonzero(m.any(0))[0]
                    bm = m[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1].astype(int); best = (0, None)
                    face = goku_face(goku[slot][d][f] if f < len(goku.get(slot, [[], [], []])[d]) else canvas)     # Super Saiyan hair is in skin shades too: go by base Goku's frame of the same pose
                    for i in mine:
                        for flip in (0, 1):
                            cm = (cs[i][2][:, ::-1] if flip else cs[i][2]).astype(int)
                            inter = correlate2d(bm, cm, mode='full'); iou = inter / (bm.sum() + cm.sum() - inter)
                            y, x = np.unravel_index(iou.argmax(), iou.shape)
                            if faces[i] != face: continue
                            if iou[y, x] > best[0]:
                                best = (float(iou[y, x]), (i, flip, int(ys[0] + y - cm.shape[0] + 1), int(xs[0] + x - cm.shape[1] + 1)))
                    if best[1]: picks.append([int(slot), d, f, round(best[0], 3), *best[1]])
        result[form] = picks
        print(form, sum(p[3] >= USE for p in picks), 'of', len(picks), 'frames from the sheet', flush=True)
    json.dump(result, open(MATCHES, 'w'), indent=0)


def build(rom, one):
    """{'black': {slot: [down, up, side]}, 'rose': {...}}, every frame of 106 and 109 in Black's and Rose's looks.
    one: RGB -> OBJ index (build.indexer)."""
    sheet = np.array(Image.open(SHEET).convert('RGB')); cs = cells(sheet); saved = json.load(open(MATCHES))
    if [[c[0], c[1], int(c[2].shape[0]), int(c[2].shape[1])] for c in cs] != saved['cells']:
        sys.exit('%s changed since %s was made: run python3 ultimate/goku_black.py match' % (SHEET, MATCHES))
    def indexed(c, flip):
        m, rgb = c[2], c[3]
        if flip: m, rgb = m[:, ::-1], rgb[:, ::-1]
        out = np.zeros(m.shape, np.uint8)
        for y, x in zip(*np.nonzero(m)): out[y, x] = one(rgb[y, x])
        return out
    looks, learned = {}, {}
    for form, actor in SOURCE.items():
        frames = actor_frames(rom, actor); placed = {}
        for slot, d, f, score, i, flip, y, x in saved[form]:
            if score < USE: continue
            img = indexed(cs[i], flip); canvas = np.zeros((32, 64), np.uint8)
            for r in range(img.shape[0]):
                for c in range(img.shape[1]):
                    R, C = y + r, x + c
                    if img[r, c] and 0 <= R < 32 and 0 <= C < 64: canvas[R, C] = img[r, c]
            placed[slot, d, f] = (canvas, score)
        # Goku's colour -> the sheet's, wherever the two line up well. The same colour of Goku's turns into different ones by height
        # (his blue is Black's black undershirt, red sash and grey boots), so votes are kept per sixth of the body's height.
        votes = {}
        for (slot, d, f), (canvas, score) in placed.items():
            if (slot, d, f) not in placed: continue
            if score < LEARN: continue
            src = frames[slot][d][f]; band = bands(src)
            both = (src != 0) & (canvas != 0)
            for r, c in zip(*np.nonzero(both)):
                keys = [(int(src[r, c]), band[r])] if band is not None else []
                if int(src[r, c]) not in KEEP: keys.append((int(src[r, c]), None))
                for key in keys:
                    v = votes.setdefault(key, {}); v[int(canvas[r, c])] = v.get(int(canvas[r, c]), 0) + 1
        def wanted(k, v):
            if sum(v.values()) < 8: return False
            if k[0] in KEEP:          # skin and white stay, except where the sheet all but always changes them: Super Saiyan's hair shares skin's shades
                return form == 'rose' and k[1] is not None and max(v.values()) >= 0.8 * sum(v.values())
            return k[1] is None or max(v.values()) >= SHARE * sum(v.values())
        learned[form] = {k: max(v, key=v.get) for k, v in votes.items() if wanted(k, v)}     # a colour seen at that height goes the sheet's way there; elsewhere its commonest
        looks[form] = (frames, placed)
    out = {}
    for form, (frames, placed) in looks.items():
        def recolour(fr, slot):
            maps = [learned['rose'], learned[form]] if form == 'black' and slot == TRANSFORM else [learned[form]]    # Black's transformation flashes Super Saiyan hair: Rose's pink
            band = bands(fr); res = fr.copy()
            for r, c in zip(*np.nonzero(fr)):
                a = int(fr[r, c])
                for m in maps:
                    b = m.get((a, band[r])) if band is not None else None
                    if b is None: b = m.get((a, None))
                    if b is not None: res[r, c] = b
            return res
        res = {}
        for slot, views in frames.items():
            res[slot] = [[placed[slot, d, f][0] if (slot, d, f) in placed else recolour(fr, slot) for f, fr in enumerate(views[d])] for d in range(3)]
        out[form] = res
    return out, {f: len(looks[f][1]) for f in looks}


KEEP = {1, 2, 16, 200, 201, 202, 203, 205, 206} | set(range(111, 121))     # outline, white, skin and greys stay as Goku has them
SHARE = 0.3
TRANSFORM = 10
BANDS = 12


def bands(fr):
    """Each row's twelfth of an upright figure's height, or None for one lying or flying flat (no up and down to go by)."""
    rows = np.nonzero((fr != 0).any(1))[0]; cols = np.nonzero((fr != 0).any(0))[0]
    if not len(rows): return None
    h, w = rows[-1] - rows[0] + 1, cols[-1] - cols[0] + 1
    if w > 1.3 * h: return None
    return {r: min(BANDS - 1, BANDS * (r - rows[0]) // h) for r in range(32)}


def portraits(one):
    """{'black': 64x64, 'rose': 64x64} OBJ indices (the sheet draws them in the game's gold frame)."""
    sheet = np.array(Image.open(SHEET).convert('RGB')).astype(int); out = {}
    for form, (x, y, n) in PORTRAITS.items():
        p = sheet[y:y + n, x:x + n]; img = np.zeros((n, n), np.uint8)
        for r in range(n):
            for c in range(n): img[r, c] = one(p[r, c])
        out[form] = img
    return out


if __name__ == '__main__' and sys.argv[1:] == ['match']:
    sys.path[:0] = ['ultimate/lib', 'tools/scripts']
    match(open('baserom.gba', 'rb').read())
