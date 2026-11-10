#!/usr/bin/env python3
"""GT fighters from Black Star Odyssey's review sheet (the owner's BSO_review_all.pdf, one page per actor at 3x).

The pages are the owner's art and are never committed: point BFU_BSO at a folder of the PDF's pages as PNGs
(p-000.png ... p-137.png; `pdftoppm -png -r 72`-style lossless page images, as the owner sent them). Page n is BSO's
actors.json actor n (page 0 is portraits).

Each page lists rows "<slot> <name>, <front|back|side>" of frames on a green field. A frame's place on the game's
32 x 64 canvas isn't printed, so each page is lined up against the BF actor BSO converted its fighting frames from
(their bodies are the same shapes). Colours come back as BF OBJ palette indices: the page images keep every colour
except some greys, which drift a little from page to page, so a grey snaps to the nearest BF grey (near-whites to
240, the shade BSO's shirts use, unless they touch black outline: eye whites, 255).

  python3 ultimate/bso_import.py <page> [out.png]     # a page's frames on the canvas, to check by eye
"""
import json, os, pickle, re, struct, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 0x08000000
ACTORS = 0x6B6BD8
GREEN = (92, 140, 96)
CANVAS = (48, 64)                      # rows, columns: goku_black.actor_frames' 32 x 64 canvas with 16 rows more on top for tall hair
TOP = 16                               # (piece x, y at column x + 24, row y + 40; Inserter.frame keeps row 40 as the feet)
VIEW = {'front': 0, 'back': 1, 'side': 2}

# BSO actors this game uses: page, BSO template (its record and the slots it doesn't list), and the BF actor whose frames
# BSO converted (to line the page up). From BSO's bso/art/actors.json (2026-11-07). "likely" where BSO says so.
PAGES = {
    'kid_goku': (1, 106, 114), 'kid_goku_ssj': (3, 109, 115), 'kid_goku_ssj3': (5, 111, 121), 'kid_goku_ssj4': (7, 106, 106),
    'gogeta_ssj4': (8, 106, 106),
    'pan': (9, 98, 114), 'pan_nobandana': (10, 98, 114), 'pan_bug': (11, 98, 114), 'pan_gi_tan': (12, 98, 114), 'pan_gi_red': (13, 98, 114),
    'pan_ssj': (14, 98, 114), 'pan_ssj_spiky': (15, 98, 114), 'pan_brapan': (16, 98, 114),
    'trunks_gt': (17, 260, 260), 'trunks_gt_ssj': (18, 261, 261),
    'gohan_gt': (19, 275, 98), 'gohan_gt_noglasses': (20, 275, 98), 'gohan_gt_ssj': (21, 276, 104),
    'goten_gt': (22, 117, 98), 'goten_gt_green': (23, 117, 98), 'goten_gt_ssj': (24, 120, 104),
    'vegeta_gt_mustache': (25, 270, 270), 'vegeta_gt': (26, 270, 270), 'vegeta_gt_ssj': (27, 273, 273),
    'vegeta_gt_tank': (28, 271, 270), 'vegeta_gt_tank_ssj': (29, 274, 273), 'vegeta_gt_ssj4': (30, 273, 270),
    'uub': (36, 114, 264), 'majuub': (37, 114, 264),
    'ledgic': (67, 64, 64),
}
# Actors the owner sent again later as BSO's "every frame" sheets (one folder in BFU_BSO, pages p1.png, p2.png ...): each slot's front, back
# and side rows of frames at 4x on the same green field, the slots in turn (their frame counts here, to check the reading). They replace the
# actor's page. SSJ4 Gogeta (Nov 10, the owner: "Also replace the SSJ4 Gogeta with this one"): BSO's finished Gogeta, four pages.
SHEETS = {'gogeta_ssj4': ('gogeta_ssj4_v2', {0: 2, 1: 4, 2: 4, 3: 3, 4: 4, 5: 4, 6: 4, 7: 1, 8: 4, 9: 3, 10: 11, 12: 2, 13: 2, 14: 3, 15: 4, 16: 4,
                                             17: 4, 18: 3, 19: 3})}
# Slots of a sheet left out: Gogeta's 10 is BSO's change into him from base Gogeta (black hair); the look here never changes form, and his
# own power-up stands in if a skill plays it (gt.FILL)
SHEET_SKIP = {'gogeta_ssj4': (10,)}
SHEET_ZOOM = 4
# Pages lined up some other way: Majuub's page has Uub's frame window (his own frames match Uub 264 too loosely to
# line up: the vest and the long hair differ), and Ledgic's source (BF's caped Bruiser, 64x64 pieces) doesn't fit the
# 32-row canvas actor_frames reads, so his idle front's feet go on row FEET and its middle on column 32.
SAME_OFFSET = {'majuub': 'uub'}
FEET = 46
PORTRAITS = ('shenron_bss', 'kidgoku', 'pan', 'trunks', 'trunks_ssj', 'gohan', 'gohan_ssj', 'goten', 'goten_surprised', 'goten_angry', 'goten_ssj',
             'goten_ssj_surprised', 'goten_ssj_angry', 'vegeta', 'vegeta_ssj4', 'giru', 'pan_nobandana', 'pan_bug', 'brapan', 'videl',
             'bulma', 'chichi', 'shu', 'mai', 'goku_adult', 'vegeta_gt', 'gogeta_ssj4', 'omega_shenron', 'syn_shenron', 'eis_shenron', 'nuova_shenron', 'super_baby2',
             'baby_vegeta', 'bulla')      # page 0, row by row (its captions)


def folder():
    d = os.environ.get('BFU_BSO')
    if not d or not os.path.isdir(d): sys.exit('set BFU_BSO to the folder of BSO review pages (p-000.png ...)')
    return d


def runs(v):
    out = []
    if not len(v): return out
    s = p = int(v[0])
    for x in v[1:]:
        x = int(x)
        if x != p + 1: out.append((s, p)); s = x
        p = x
    return out + [(s, p)]


def green(a):
    return (np.abs(a[..., 0] - GREEN[0]) <= 1) & (a[..., 1] == GREEN[1]) & (a[..., 2] == GREEN[2])


def rows_of(n):
    """[(label, [cell RGB arrays])] for page n, in order."""
    import pytesseract
    path = os.path.join(folder(), 'p-%03d.png' % n)
    img = Image.open(path).convert('RGB'); a = np.asarray(img).astype(int); g = green(a)
    out = []
    for y0, y1 in runs(np.nonzero(g.any(1))[0]):
        label = pytesseract.image_to_string(img.crop((0, y0, 190, y0 + 30)).resize((570, 90)), config='--psm 7').strip()
        cells = [a[y0:y1 + 1, x0:x1 + 1] for x0, x1 in runs(np.nonzero(g[y0:y1 + 1].any(0))[0]) if x1 - x0 > 60]   # cells: green columns between dark borders
        out.append((label, cells))
    return out


class Colours:
    def __init__(self, pal):
        self.pal = pal.astype(int)
        self.exact = {tuple(self.pal[i]): i for i in range(255, 0, -1)}
        self.greys = {int(self.pal[i][0]): i for i in range(1, 256) if self.pal[i][0] == self.pal[i][1] == self.pal[i][2]}
        self.greys.setdefault(255, 2)

    def index(self, frame):
        """frame: native RGB (h x w x 3) -> palette indices (0 = the green field)."""
        h, w, _ = frame.shape; out = np.zeros((h, w), np.int16)
        for y in range(h):
            for x in range(w):
                t = tuple(int(v) for v in frame[y, x])
                if t[1:] == GREEN[1:] and abs(t[0] - GREEN[0]) <= 1: continue
                if t in self.exact and not (t[0] == t[1] == t[2] and 241 <= t[0] <= 254): out[y, x] = self.exact[t]; continue
                if t[0] == t[1] == t[2]:
                    if 241 <= t[0] <= 254: out[y, x] = -2           # near-white: decided below
                    else: out[y, x] = self.greys[min(self.greys, key=lambda g: abs(g - t[0]))]
                    continue
                out[y, x] = int(((self.pal[1:] - np.array(t)) ** 2).sum(1).argmin()) + 1
        black = out == self.exact[(0, 0, 0)]
        for y, x in zip(*np.nonzero(out == -2)):
            touch = any(0 <= y + dy < h and 0 <= x + dx < w and black[y + dy, x + dx] for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)))
            out[y, x] = self.greys[255] if touch else self.greys[240]
        return out.astype(np.uint8)


def line_up(cells, ref):
    """Offset (dy, dx) putting page frames on the canvas: canvas[r + dy, c + dx] = cell[r, c]. Sums mask overlap with the source actor's frames."""
    from scipy.signal import correlate2d
    total = None
    for nat, r in zip(cells, ref):
        m = (nat > 0).astype(np.int32); R = np.zeros((CANVAS[0] + 2 * 24, CANVAS[1] + 2 * 24), np.int32)
        R[24 + TOP:24 + CANVAS[0], 24:24 + CANVAS[1]] = r > 0
        c = correlate2d(R, m, mode='valid')                 # c[i, j]: m placed at (i - 24, j - 24) on the canvas
        total = c if total is None else total[:min(total.shape[0], c.shape[0]), :min(total.shape[1], c.shape[1])] + c[:total.shape[0], :total.shape[1]]
    i, j = np.unravel_index(total.argmax(), total.shape)
    return int(i) - 24, int(j) - 24, int(total.max())


def sheet_pages(name):
    d = os.path.join(folder(), SHEETS[name][0]); pages = []
    while os.path.exists(os.path.join(d, 'p%d.png' % (len(pages) + 1))): pages.append(os.path.join(d, 'p%d.png' % (len(pages) + 1)))
    if not pages: sys.exit('%s: no sheet pages (p1.png ...) in %s' % (name, d))
    return pages


def sheet_rows(name, colours):
    """{slot: [front, back, side] frame lists (palette indices)} from an actor's SHEETS pages."""
    _, counts = SHEETS[name]; rows = []
    for path in sheet_pages(name):
        a = np.asarray(Image.open(path).convert('RGB')).astype(int); g = green(a)
        for y0, y1 in runs(np.nonzero(g[:, 150:].any(1))[0]):             # (the labels are left of x 150)
            cells = [a[y0:y1 + 1, x0:x1 + 1] for x0, x1 in runs(np.nonzero(g[y0:y1 + 1].any(0))[0]) if x1 - x0 > 60]
            rows.append([colours.index(c[SHEET_ZOOM // 2::SHEET_ZOOM, SHEET_ZOOM // 2::SHEET_ZOOM]) for c in cells])
    slots = sorted(counts)
    if len(rows) != 3 * len(slots): raise ValueError('%s: %d rows of frames on the sheets, expected %d' % (name, len(rows), 3 * len(slots)))
    got = {}
    for k, s in enumerate(slots):
        views = rows[3 * k:3 * k + 3]
        if any(len(v) != counts[s] for v in views): raise ValueError('%s slot %d: %s frames, expected %d' % (name, s, [len(v) for v in views], counts[s]))
        if s not in SHEET_SKIP.get(name, ()): got[s] = views
    return got


def frames(rom, name, colours, cache=None):
    """{slot: [down, up, side]} canvases (CANVAS-shaped uint8) for a BSO actor."""
    sys.path[:0] = [HERE, os.path.join(HERE, 'lib'), os.path.join(HERE, '..', 'tools', 'scripts')]
    import goku_black
    page, template, source = PAGES[name]
    got = {}
    if name in SHEETS: got = sheet_rows(name, colours)
    else:
        for label, cells in rows_of(page):
            m = re.match(r'(\d+)\s.*,\s*(front|back|side)$', label)
            if not m: raise ValueError('page %d: unreadable row label %r' % (page, label))
            got.setdefault(int(m.group(1)), [None, None, None])[VIEW[m.group(2)]] = [colours.index(c[1::3, 1::3]) for c in cells]
    if name in SAME_OFFSET:
        (dy, dx), score = frames(rom, SAME_OFFSET[name], colours)[1]['offset'], 0
    elif name == 'ledgic':
        ys, xs = np.nonzero(got[0][0][0]); dy, dx, score = FEET - int(ys.max()), 32 - (int(xs.min()) + int(xs.max()) + 1) // 2, 0
    else:
        src = goku_black.actor_frames(rom, source)
        pairs = [(nat, src[s][v][k]) for s, views in got.items() if s in src for v in range(3) for k, nat in enumerate(views[v] or [])
                 if k < len(src[s][v]) and len(views[v]) == len(src[s][v])]
        dy, dx, score = line_up([p[0] for p in pairs], [p[1] for p in pairs])
    out, clipped = {}, 0
    for s, views in got.items():
        if any(v is None for v in views) or len({len(v) for v in views}) != 1:
            raise ValueError('page %d slot %d: views missing or of different lengths' % (page, s))
        out[s] = []
        for v in views:
            lst = []
            for nat in v:
                c = np.zeros(CANVAS, np.uint8); h, w = nat.shape
                for r in range(h):
                    for k in range(w):
                        if nat[r, k] and 0 <= r + dy < CANVAS[0] and 0 <= k + dx < CANVAS[1]: c[r + dy, k + dx] = nat[r, k]
                        elif nat[r, k]: clipped += 1
                lst.append(c)
            out[s].append(lst)
    return out, {'offset': (dy, dx), 'score': score, 'clipped': clipped, 'template': template}


def load_all(rom, pal, names=None):
    """Every actor in PAGES (or names), cached beside the pages by their modification times."""
    names = names or list(PAGES)
    d = folder(); cache = os.path.join(HERE, 'out', 'bso_frames.pkl')
    stamp = {n: [os.path.getmtime(p) for p in sheet_pages(n)] if n in SHEETS else os.path.getmtime(os.path.join(d, 'p-%03d.png' % PAGES[n][0])) for n in names}
    stamp['_code'] = os.path.getmtime(__file__)
    try:
        old = pickle.load(open(cache, 'rb'))
        if old['stamp'] == stamp: return old['frames'], old['info']
    except Exception: pass
    colours = Colours(pal)
    res, info = {}, {}
    for n in names: res[n], info[n] = frames(rom, n, colours)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    pickle.dump({'stamp': stamp, 'frames': res, 'info': info}, open(cache, 'wb'))
    return res, info


def portraits(one):
    """{name: 64x64 OBJ index array} from page 0 (each portrait with its gold frame, 3x on the page). one: RGB -> index
    (build.indexer, which keeps off the menu's animated slots, as for Goku Black's portraits)."""
    a = np.asarray(Image.open(os.path.join(folder(), 'p-000.png')).convert('RGB')).astype(int)
    dark = (a == a[2, 2]).all(2)                      # the page's background
    tiles = []
    for y0, y1 in runs(np.nonzero((~dark).sum(1) > 150)[0]):
        if y1 - y0 < 150: continue
        for x0, x1 in runs(np.nonzero((~dark[y0:y1]).sum(0) > 150)[0]):
            if x1 - x0 >= 150: tiles.append((y0, x0))
    if len(tiles) != len(PORTRAITS): raise ValueError('page 0: %d portraits, expected %d' % (len(tiles), len(PORTRAITS)))
    out = {}
    for name, (y0, x0) in zip(PORTRAITS, tiles):
        cell = a[y0 + 1:y0 + 192:3, x0 + 1:x0 + 192:3]
        out[name] = np.array([[one(cell[r, c]) for c in range(64)] for r in range(64)], np.uint8)
    return out


if __name__ == '__main__':
    rom = open('baserom.gba', 'rb').read()
    pal = np.frombuffer(rom[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    name = sys.argv[1]
    fr, info = frames(rom, name, Colours(pal))
    print(name, info)
    if len(sys.argv) > 2:
        Z = 4; slots = sorted(fr); n = max(len(fr[s][0]) for s in slots)
        W = Image.new('RGB', (n * (48 * Z + 4) + 60, len(slots) * 3 * (32 * Z + 4)), (28, 28, 32))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(W); y = 0
        for s in slots:
            for v in range(3):
                dr.text((2, y + 4), '%d/%d' % (s, v), fill=(220, 220, 220))
                for k, c in enumerate(fr[s][v]):
                    rgb = pal[c].copy(); rgb[c == 0] = GREEN; rgb[:, [24 - 1]] = rgb[:, [24 - 1]]
                    W.paste(Image.fromarray(rgb[:, 8:56].astype(np.uint8)).resize((48 * Z, 32 * Z), 0), (60 + k * (48 * Z + 4), y))
                y += 32 * Z + 4
        W.save(sys.argv[2])
