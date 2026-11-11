#!/usr/bin/env python3
"""Beerus's reworked side view and a taller Beerus, as pictures for the owner (Nov 11): the pictures of what lib/beerus.py makes
with the new side head (HEAD_SIDE_NEW) and frame() lengthening him, frame for frame what the build writes when build.py BEERUS_LOOK
says so (it says 'old,0,0' until he approves).

  python3 ultimate/beerus_preview.py OUTDIR          (reads baserom.gba; writes PNG sheets and GIFs)

The owner, Nov 11: "Beerus back view isn't that bad the side view sucks though"; "Don't draw a whole new view just base it off a buus
fury shape or the existing sprite already and fill it in better"; "Maybe super janemba tbh"; then of the first look (Janemba's side
head shrunk by vote, a blur): "Use janemba but fix the eyes and ears and maintain visual clarity and attention to detail"; "If you
can also possibly make the sprite a bit taller potentially but not janemba full height". lib/beerus.py says how both are made."""
import os, struct, sys
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import artclean, beerus, goku_black, sprites

B = 0x08000000
KID_BUU, GOKU = 38, 106
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

    def converter(self, new_head=True, tall=(0, 0)):
        """lib/beerus.py's converter as the build makes it (lib/sprites.py build_actors): the new side head or the old, and his height."""
        stand = self.u(self.u(self.list + 4 * KID_BUU) - B + 0x54)
        kst = {v: sprites.frame_image(self.rom, self.u(stand - B + 4 + 4 * v)) for v in (0, 1, 2)}
        return beerus.Beerus(kst, self.one, side=beerus.HEAD_SIDE_NEW if new_head else None, tall=tall)


def placed(out, off, at, size=(112, 112), origin=(84, 56)):
    """A frame on a canvas round the actor's origin: `at` is its box's corner, `off` where the image's corner goes from it."""
    c = np.zeros(size, np.uint8); y, x = origin[0] + at[1] + off[1], origin[1] + at[0] + off[0]
    c[y:y + out.shape[0], x:x + out.shape[1]] = out
    return c


def main(out):
    os.makedirs(out, exist_ok=True)
    R = Rom(); old, new = False, True; cache = {}; convs = {}
    try: font = ImageFont.load_default(size=20)
    except TypeError: font = ImageFont.load_default()

    def fig(conv, slot, v, f, t=0, l=0):
        key = (conv, slot, v, f, t, l)
        if key not in cache:
            got = R.frame(KID_BUU, slot, f, v)
            if got is None or not got[0].any(): cache[key] = None
            else:
                if (conv, t, l) not in convs: convs[conv, t, l] = R.converter(conv, (t, l))
                o, off = convs[conv, t, l].frame(got[0], v); cache[key] = placed(o, off, got[1])
        return cache[key]

    def rgb(c):
        o = R.pal[c].copy(); o[c == 0] = BG; return o.astype(np.uint8)

    def cut(c, box): return rgb(c[box[0]:box[1], box[2]:box[3]])

    def big(im, z): return Image.fromarray(im).resize((im.shape[1] * z, im.shape[0] * z), Image.NEAREST)

    def label(img, texts, z):
        d = ImageDraw.Draw(img)
        for (x, y), t in texts: d.text((x * z + 6, y * z + 6), t, fill=(255, 255, 255), font=font)
        return img

    goku, at = R.frame(GOKU, 0, 0, 0); goku = placed(goku, (0, 0), at)
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
    print('; '.join('%s head, %d + %d rows: %d heads placed, %d missed' % ('new' if k[0] else 'old', k[1], k[2], c.hits + c.manual, c.misses) for k, c in sorted(convs.items())))
    print('\n'.join(sorted(os.listdir(out))))


if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
