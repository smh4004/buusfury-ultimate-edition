#!/usr/bin/env python3
"""Beerus's reworked side view and a taller Beerus, as pictures for the owner (Nov 11). NOT part of the build: nothing here reaches a
ROM until he approves; then HEAD_SIDE_NEW and the lengthening move into lib/beerus.py and lib/sprites.py composed_actor.

  python3 ultimate/beerus_preview.py OUTDIR          (reads baserom.gba; writes PNG sheets and GIFs)

The owner, Nov 11: "Beerus back view isn't that bad the side view sucks though"; "Don't draw a whole new view just base it off a buus
fury shape or the existing sprite already and fill it in better"; "Maybe super janemba tbh"; then of the first look (Janemba's side
head shrunk by vote, a blur): "Use janemba but fix the eyes and ears and maintain visual clarity and attention to detail"; "If you
can also possibly make the sprite a bit taller potentially but not janemba full height".

The side head (HEAD_SIDE_NEW, facing left like every side view): Super Janemba's side head (actor 145) gives the shape: a skull as deep
as the front head is wide, the brow over the eye, and both ears showing as both his horns show. On it, the owner's own pixels: his
front sprite's ear twice (the near one with its light inside and his earring, the far one before it with a gap between their tips),
and his eye's gold with a black pupil, two by two under a dark brow so that it reads at the game's size. Three purples, as his sprite.

Taller: Kid Buu's body makes Beerus 30 rows (Goku is 31, Super Janemba 59). Rows are added by seams (seam, costs): a seam is one
pixel in every column, joined from the frame's left edge to its right, laid through the cheapest pixels of Kid Buu's frame; every pixel
on and above it stays and everything below moves down one row, so that part of him is one pixel longer. A leg seam runs through the
trousers, a torso seam through bare skin under the chin (the collar is drawn over the first three rows after, so the new row shows as
belly); belts, wristbands, shoes and the head are never repeated, and a seam that could only be made by cutting one is not made (the
other kind is tried instead). A frame is turned first so that the body hangs below the head (lying frames grow along the body; a
body drawn behind the head, foreshortened, is left alone). The frame is lengthened BEFORE it is dressed as Beerus, so lib/beerus.py
finds Kid Buu's head as it always did."""
import hashlib, os, struct, sys
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import artclean, beerus, goku_black, sprites

B = 0x08000000
KID_BUU, GOKU = 38, 106
HEAD_SIDE_NEW = ('....B...B...',
                 '....B...B...',
                 '...BCB.BFB..',
                 '...BCB.BFB..',
                 '...BCBBCFDE.',
                 '...BCBBCFCB.',
                 '...BBBBCCCBB',
                 '..BCCCCCCCCB',
                 '.BCCCCCCCCCB',
                 '.BFFCCCCCCCB',
                 '.BBBBFCCCCCB',
                 'BFEEBFCCCCB.',
                 'BFHEFFCCCB..',
                 '.BFFFCCBB...',
                 '..BBBBB.....')
LEG = tuple(range(113, 121))                              # Kid Buu's trousers (without 111 and 112, which his belt and wristbands use too)
BODY = beerus.KID_SKIN + beerus.PANTS + beerus.ACCENT
DEAR = 80                                                 # a seam dearer than this would repeat something it shouldn't
BIG = 10 ** 6
BG = np.array((88, 120, 88), np.uint8)                    # the field's green, as the owner's previews have it


class Rom:
    def __init__(self, path='baserom.gba'):
        self.rom = open(path, 'rb').read()
        self.pal = np.frombuffer(self.rom[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3).copy()
        self.usable = np.array([i for i in range(1, 256) if i not in artclean.MENU_SLOTS])
        self.list = self.u(0x3C0) - 4 - B

    def u(self, o): return struct.unpack_from('<I', self.rom, o)[0]

    def one(self, q):
        """The game's colour nearest an RGB (the build's own matcher weighs hue the same way)."""
        q = np.asarray(q, int); p = self.pal[self.usable].astype(int); ch = lambda v: np.stack([v[..., 0] - v[..., 1], v[..., 1] - v[..., 2]], -1)
        return int(self.usable[(((p - q) ** 2).sum(1) + 6 * ((ch(p) - ch(q)) ** 2).sum(1)).argmin()])

    def idx(self, rows):
        out = np.zeros((len(rows), len(rows[0])), np.uint8)
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.': out[y, x] = beerus.SKIN_OF.get(c) or self.one(beerus.RGB[c])
        return out

    def slots(self, aid):
        """[(slot, frames)] of an actor."""
        rec = self.u(self.list + 4 * aid) - B; out = []
        for s in range(self.u(rec) & 0xFF):
            an = self.u(rec + 0x54 + 4 * s)
            if an: out.append((s, self.u(an - B)))
        return out

    def frame(self, aid, slot, f, view):
        """A frame as the build sees it (lib/sprites.py composed_actor): its pieces on its own box. -> (image, (x, y) of the box from
        the actor's origin), or None."""
        rec = self.u(self.list + 4 * aid) - B; an = self.u(rec + 0x54 + 4 * slot) - B; fp = self.u(an + 4 + 4 * (4 * f + view))
        if not fp: return None
        o = fp - B; bx, by, bw, bh = struct.unpack_from('<bbBB', self.rom, o + 4)
        img = np.zeros((bh, bw), np.uint8)
        for j in range(self.u(o)):
            x, y, w, h = struct.unpack_from('<bbBB', self.rom, o + 8 + 12 * j)
            img[y - by:y - by + h, x - bx:x - bx + w] = goku_black.tiles(self.rom, self.u(o + 16 + 12 * j) - B, w, h)
        return img, (bx, by)

    def converter(self, new_head=True):
        """lib/beerus.py's converter as the build makes it (lib/sprites.py build_actors), with the new side head or the built one."""
        stand = self.u(self.u(self.list + 4 * KID_BUU) - B + 0x54)
        kst = {v: sprites.frame_image(self.rom, self.u(stand - B + 4 + 4 * v)) for v in (0, 1, 2)}
        conv = beerus.Beerus(kst, self.one)
        if new_head: conv.head[2] = self.idx(HEAD_SIDE_NEW)
        return conv


def seam(img, cost, lo, hi):
    """The cheapest path from the left edge to the right with one row in every column, in rows lo..hi: neighbours at most a row apart,
    but free between two empty pixels. -> ([row per column], cost)"""
    H, W = img.shape; empty = img == 0
    c = np.full((H, W), BIG, np.int64); c[lo:hi + 1] = cost[lo:hi + 1]
    tot = np.full((H, W), BIG * 100, np.int64); back = np.zeros((H, W), np.int32)
    tot[:, 0] = c[:, 0]
    for x in range(1, W):
        prev = tot[:, x - 1]
        e_rows = np.nonzero(empty[:, x - 1])[0]
        e_best = e_rows[prev[e_rows].argmin()] if len(e_rows) else None
        for r in range(lo, hi + 1):
            best, arg = BIG * 100, r
            for q in (r, r - 1, r + 1):
                if lo <= q <= hi and prev[q] < best: best, arg = prev[q], q
            if empty[r, x] and e_best is not None and prev[e_best] < best: best, arg = prev[e_best], e_best
            tot[r, x] = c[r, x] + best; back[r, x] = arg
    r = int(tot[lo:hi + 1, W - 1].argmin()) + lo; total = int(tot[r, W - 1]); path = [r]
    for x in range(W - 1, 0, -1):
        r = int(back[r, x]); path.append(r)
    return path[::-1], total


def costs(img, cheap, dear=60, other=25):
    """What repeating each pixel costs: 1 in the class to lengthen, more where the pixel differs from the ones above and below it or
    lies in a run of outline (a line across the limb would get thicker), `other` in the rest of the body, `dear` in belts and
    wristbands and three times that in a sole, 0 in the empty."""
    H, W = img.shape
    c = np.full((H, W), other, np.int64)
    c[np.isin(img, cheap)] = 1
    c[np.isin(img, beerus.ACCENT) & ~np.isin(img, cheap)] = dear
    c[np.isin(img, (77, 78))] = dear * 3
    up = np.zeros((H, W), bool); dn = np.zeros((H, W), bool)
    up[1:] = img[1:] != img[:-1]; dn[:-1] = img[:-1] != img[1:]
    dark = np.isin(img, (38, 39, 40, 1, 111, 114))
    c += 3 * (up & dn) + 4 * (dark & np.roll(dark, 1, 1) & np.roll(dark, -1, 1))
    c[img == 0] = 0
    return c


def insert(img, path):
    """One row more: in every column the seam's pixel and all above it stay, and it and all below it go down one."""
    H, W = img.shape; out = np.zeros((H + 1, W), img.dtype)
    for x, r in enumerate(path):
        out[:r + 1, x] = img[:r + 1, x]; out[r + 1:, x] = img[r:, x]
    return out


def head_box(conv, img):
    """(y0, y1, x0, x1) of Kid Buu's head in a frame: lib/beerus.py's own entry where its matcher can't find it."""
    hand = beerus.MANUAL.get(hashlib.sha1(img.tobytes()).hexdigest()[:12])
    if hand: return hand[0], hand[1], hand[2], hand[3]
    score, i, x0, y0 = conv.find(img)
    if i is None or score < beerus.MIN_MATCH: return None
    t = conv.tpl[i][0]; return max(y0, 0), y0 + t.shape[0] - 1, max(x0, 0), x0 + t.shape[1] - 1


def body_dir(img, box):
    """Which way his body runs from his head, by where his legs are (trousers and soles; the whole body where a frame shows no legs):
    'down' standing, crouching or in the air; 'right' or 'left' lying or flying; 'up' when the body is drawn behind the head (he lies
    towards the viewer, foreshortened): nothing to lengthen there."""
    y0, y1, x0, x1 = box
    m = np.isin(img, LEG + (77, 78))
    if m.sum() < 6: m = np.isin(img, BODY); m[y0:y1 + 1, x0:x1 + 1] = False
    ys, xs = np.nonzero(m)
    if not len(ys): return None
    dy, dx = ys.mean() - y1, xs.mean() - (x0 + x1) / 2
    return 'down' if dy >= abs(dx) else 'up' if dy < 0 and -dy >= abs(dx) else 'right' if dx > 0 else 'left'


TURN = {'down': 0, 'right': -1, 'left': 1, 'up': 2}          # np.rot90 turns that bring the body below the head


def tall_frame(conv, img, view, torso, legs, log=None):
    """Kid Buu's frame `torso` + `legs` pixels longer and dressed as Beerus. -> (image, which way it grew: the canvas grows at the
    bottom for 'down', the right for 'right', the left for 'left'; 'up' and 'none' don't grow)"""
    box = head_box(conv, img); way = body_dir(img, box) if box else None
    if way is None:
        if log is not None: log.append(('no head or body', 0))
        return conv.apply(img, view), 'none'
    k = TURN[way]; H, W = img.shape
    mark = np.zeros((H, W), bool); mark[box[0]:box[1] + 1, box[2]:box[3] + 1] = True
    r = np.rot90(img, k).copy(); chin = np.nonzero(np.rot90(mark, k).any(1))[0].max()
    kinds = {} if way == 'up' else {'leg': (LEG + (2,), chin + 2), 'torso': (beerus.KID_SKIN, chin + 1)}
    for kind in ['leg'] * legs + ['torso'] * torso:
        if not kinds: break
        best = None; total = 0
        for kd in (kind, 'torso' if kind == 'leg' else 'leg'):
            cheap, lo = kinds[kd]; ys = np.nonzero((r != 0).any(1))[0]
            if ys.max() - 1 < lo: continue
            path, total = seam(r, costs(r, cheap), lo, ys.max() - 1)
            if 0 < total <= DEAR: best = (kd, path, total); break          # (0: a path through empty pixels only lengthens nothing)
        if log is not None: log.append((best[0] if best else kind + ' not made', best[2] if best else total))
        if best: r = insert(r, best[1])
    s = np.rot90(r, -k).copy()
    key = hashlib.sha1(img.tobytes()).hexdigest()[:12]; hand = beerus.MANUAL.get(key); k2 = None
    if hand:                                              # lib/beerus.py knows this frame by its pixels as they were
        k2 = hashlib.sha1(s.tobytes()).hexdigest()[:12]
        dy = s.shape[0] - H if way == 'up' else 0; dx = s.shape[1] - W if way == 'left' else 0
        beerus.MANUAL[k2] = (hand[0] + dy, hand[1] + dy, hand[2] + dx, hand[3] + dx, hand[4], hand[5] + dy, hand[6] + dx, hand[7])
    out = conv.apply(s, view)
    if k2 and k2 != key: del beerus.MANUAL[k2]
    return out, way


def placed(out, way, img, at, size=(112, 112), origin=(84, 56)):
    """The frame on a canvas round the actor's origin: his feet where they were ('down'), centred along the body when he lies."""
    gy, gx = out.shape[0] - img.shape[0], out.shape[1] - img.shape[1]
    dy = -gy if way == 'down' else 0; dx = {'right': -(gx // 2), 'left': -(gx - gx // 2)}.get(way, 0)
    c = np.zeros(size, np.uint8); y, x = origin[0] + at[1] + dy, origin[1] + at[0] + dx
    c[y:y + out.shape[0], x:x + out.shape[1]] = out
    return c


def main(out):
    os.makedirs(out, exist_ok=True)
    R = Rom(); old, new = R.converter(False), R.converter(True); cache = {}
    try: font = ImageFont.load_default(size=20)
    except TypeError: font = ImageFont.load_default()

    def fig(conv, slot, v, f, t=0, l=0):
        key = (id(conv), slot, v, f, t, l)
        if key not in cache:
            got = R.frame(KID_BUU, slot, f, v)
            if got is None or not got[0].any(): cache[key] = None
            else:
                o, way = tall_frame(conv, got[0], v, t, l); cache[key] = placed(o, way, got[0], got[1])
        return cache[key]

    def rgb(c):
        o = R.pal[c].copy(); o[c == 0] = BG; return o.astype(np.uint8)

    def cut(c, box): return rgb(c[box[0]:box[1], box[2]:box[3]])

    def big(im, z): return Image.fromarray(im).resize((im.shape[1] * z, im.shape[0] * z), Image.NEAREST)

    def label(img, texts, z):
        d = ImageDraw.Draw(img)
        for (x, y), t in texts: d.text((x * z + 6, y * z + 6), t, fill=(255, 255, 255), font=font)
        return img

    goku, at = R.frame(GOKU, 0, 0, 0); goku = placed(goku, 'none', goku, at)
    STAND = (84 - 40, 84 + 10, 56 - 4 - 14, 56 - 4 + 30)
    row = np.concatenate([cut(fig(old, 0, 2, 0), STAND), cut(fig(new, 0, 2, 0), STAND), cut(fig(new, 0, 0, 0), STAND), cut(fig(new, 0, 1, 0), STAND)], 1)
    label(big(row, 10), [((2, 1), 'side view now'), ((46, 1), 'side view new'), ((90, 1), 'front (as it is)'), ((134, 1), 'back (as it is)')], 10).save(out + '/beerus_side_view_now_and_new.png')
    rows = []; texts = []
    for k, (t, l, name) in enumerate(((0, 0, 'as now (30 rows)'), (1, 1, '2 rows taller'), (2, 2, '4 rows taller'))):
        rows.append(np.concatenate([cut(goku, (84 - 40, 84 + 10, 56 - 22, 56 + 22))] + [cut(fig(new, 0, v, 0, t, l), STAND) for v in (0, 2, 1)], 1))
        texts.append(((2, 50 * k + 1), name))
    label(big(np.concatenate(rows, 0), 7), texts, 7).save(out + '/beerus_heights_beside_goku.png')

    def strip(view, t, l, conv, z, name):
        rws = []
        for slot, nf in R.slots(KID_BUU):
            if slot == 17: continue                       # (Kid Buu's dissolving: Beerus's slot 17 is built from slots 9 and 15)
            cells = [c for c in (fig(conv, slot, view, f, t, l) for f in range(nf)) if c is not None]
            if cells: rws.append(cells)
        allm = np.zeros((112, 112), bool)
        for r in rws:
            for c in r: allm |= c > 0
        ys, xs = np.nonzero(allm); y0, y1, x0, x1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
        blank = np.zeros((y1 - y0, x1 - x0, 3), np.uint8); blank[:] = BG
        lines = []; cur = []
        for r in rws:
            if cur and len(cur) + len(r) > 9: lines.append(cur); cur = []
            cur = cur + [rgb(c[y0:y1, x0:x1]) for c in r]
        if cur: lines.append(cur)
        w = max(len(x) for x in lines)
        big(np.concatenate([np.concatenate(x + [blank] * (w - len(x)), 1) for x in lines], 0), z).save(out + '/' + name)

    strip(2, 0, 0, new, 3, 'beerus_side_every_frame_new_head.png')
    strip(2, 2, 2, new, 3, 'beerus_side_every_frame_new_head_4_rows_taller.png')
    strip(0, 2, 2, new, 3, 'beerus_front_every_frame_4_rows_taller.png')
    strip(1, 2, 2, new, 3, 'beerus_back_every_frame_4_rows_taller.png')

    def gif(name, cols, seq, box, z=5, ms=130, reps=3):
        """cols: [(converter, view, torso, legs)] side by side; seq: [(slot, frame)]"""
        fr = []
        for _ in range(reps):
            for slot, f in seq:
                cells = [cut(fig(conv, slot, v, f, t, l) if fig(conv, slot, v, f, t, l) is not None else fig(conv, slot, v, 0, t, l), box) for conv, v, t, l in cols]
                fr.append(big(np.concatenate(cells, 1), z))
        fr[0].save(out + '/' + name, save_all=True, append_images=fr[1:], duration=ms, loop=0, disposal=2)

    nf = dict(R.slots(KID_BUU)); walk = [(1, f) for f in range(nf[1])]
    BOXW = (84 - 42, 84 + 10, 56 - 4 - 16, 56 - 4 + 32); BOXK = (84 - 42, 84 + 10, 56 - 4 - 34, 56 - 4 + 32)
    gif('beerus_walk_side_now_new_and_taller.gif', [(old, 2, 0, 0), (new, 2, 0, 0), (new, 2, 1, 1), (new, 2, 2, 2)], walk, BOXW)
    gif('beerus_walk_front_side_back_4_rows_taller.gif', [(new, 0, 2, 2), (new, 2, 2, 2), (new, 1, 2, 2)], walk, BOXW)
    ki = [(0, 0)] * 2 + [(3, f) for f in range(nf[3])] + [(3, nf[3] - 1)] * 2 + [(0, 0)] * 2
    gif('beerus_ki_blast_side_now_new_and_taller.gif', [(old, 2, 0, 0), (new, 2, 0, 0), (new, 2, 2, 2)], ki, BOXK, ms=150)
    combo = [(0, 0)] + [(s, f) for s in (4, 5, 6) for f in range(nf[s])] + [(0, 0)]
    gif('beerus_combo_side_now_new_and_taller.gif', [(old, 2, 0, 0), (new, 2, 0, 0), (new, 2, 2, 2)], combo, BOXK, ms=140)
    print('heads placed %d (%d by hand), missed %d' % (new.hits, new.manual, new.misses))
    print('\n'.join(sorted(os.listdir(out))))


if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
