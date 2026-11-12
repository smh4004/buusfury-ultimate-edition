"""Super Saiyan 4 Goku, every picture of his (slots 0-21, all three views, each picture once) as the arm fixes leave him: so the
owner can check his arms in every single frame (Nov 12 07:49: "Fix the fucking fur on the arms in every single frame").
  BFU_GOG_ROM=<debug build> python3 ultimate/ssj4_preview/everyframe.py <out dir>
-> ssj4_goku_every_frame_<n>.png and ssj4_goku_arms_last_round.png (the pictures armfur.MORE changes: the 07:4x preview above,
   now below)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import plainback as P, armfur as A
from frames import fr, GOKU, R

NAME = {0: 'standing', 1: 'walk', 2: 'run', 3: 'ki blast', 4: 'combo 1', 5: 'combo 2', 6: 'finisher', 7: 'guard', 8: 'charging',
        9: 'hit', 10: 'powering up', 12: 'victory', 13: 'power-up', 14: 'jump', 15: 'flying', 16: 'spin', 17: 'knocked down',
        18: 'getting up', 21: 'special'}
VIEW = {0: 'front', 1: 'back', 2: 'side'}
BG = (88, 120, 88); BOX = (36, 74, 30, 80)


def rgb(c):
    c = c[BOX[0]:BOX[1], BOX[2]:BOX[3]]; out = R.rgb(c).copy(); out[c == 0] = BG; return out


def big(a, z): return Image.fromarray(a).resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST)


def earlier(k):
    """the preview before this round: every fix but armfur.MORE"""
    c = fr(GOKU, *k); more = A.MORE.get(k, [])
    ent = [e for e in A.FIXES.get(k, []) if e not in more]
    if ent: c = A.apply(c, P.bf_for(k), fr(GOKU, 0, 0, k[2]), ent)
    return P.plain_back(c, P.bf_for(k)) if k[2] == 1 and P.from_behind(fr(GOKU, *k)) else P.fill(c)


def pictures():
    NS = R.slots(GOKU); seen = set(); keys = []
    for s in sorted(NS):
        if s >= 22: continue
        for f in range(NS[s]):
            for d in range(3):
                c = fr(GOKU, s, f, d)
                if c.any() and c.tobytes() not in seen: seen.add(c.tobytes()); keys.append((s, f, d))
    return keys


def grid(keys, fn, path, cols=6, z=5, title=None):
    F = ImageFont.load_default(size=14); H = BOX[1] - BOX[0]; W = BOX[3] - BOX[2]; lab = 18; top = 26 if title else 0
    rows = (len(keys) + cols - 1) // cols
    img = Image.new('RGB', (cols * W * z, top + rows * (H * z + lab)), (30, 40, 30)); d = ImageDraw.Draw(img)
    if title: d.text((6, 5), title, fill=(255, 255, 255), font=ImageFont.load_default(size=18))
    for j, k in enumerate(keys):
        x = (j % cols) * W * z; y = top + (j // cols) * (H * z + lab)
        d.text((x + 4, y + 2), '%s %d, %s' % (NAME.get(k[0], k[0]), k[1] + 1, VIEW[k[2]]), fill=(255, 255, 255), font=F)
        img.paste(big(rgb(fn(k)), z), (x, y + lab))
    img.save(path)


if __name__ == '__main__':
    OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
    keys = pictures(); per = 36
    for i in range(0, len(keys), per):
        grid(keys[i:i + per], P.fixed, OUT + '/ssj4_goku_every_frame_%d.png' % (i // per + 1),
             title='every picture of his, fixed (%d-%d of %d)' % (i + 1, min(len(keys), i + per), len(keys)))
    more = sorted(A.MORE)
    H = BOX[1] - BOX[0]; W = BOX[3] - BOX[2]; z = 6; cols = 5; F = ImageFont.load_default(size=14); rows = []
    for i in range(0, len(more), cols):
        ch = more[i:i + cols]; img = Image.new('RGB', (cols * W * z, 2 * H * z + 22), BG); d = ImageDraw.Draw(img)
        for j, k in enumerate(ch):
            d.text((j * W * z + 4, 3), '%s %d, %s' % (NAME.get(k[0], k[0]), k[1] + 1, VIEW[k[2]]), fill=(255, 255, 255), font=F)
            img.paste(big(rgb(earlier(k)), z), (j * W * z, 22)); img.paste(big(rgb(P.fixed(k)), z), (j * W * z, 22 + H * z))
        rows.append(img)
    head = Image.new('RGB', (cols * W * z, 30), (30, 40, 30))
    ImageDraw.Draw(head).text((6, 6), 'this round: the last preview above, fixed below', fill=(255, 255, 255), font=ImageFont.load_default(size=18))
    rows = [head] + rows; sheet = Image.new('RGB', (cols * W * z, sum(r.height + 6 for r in rows)), (255, 255, 255)); y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.height + 6
    sheet.save(OUT + '/ssj4_goku_arms_last_round.png')
    print(len(keys), 'pictures;', len(more), 'changed this round')
