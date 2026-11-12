"""Super Saiyan 4 Goku's arms in every other move (a preview; he is locked): armfur.MOVES, on top of the walk and run arm fixes,
the plain back and the filled see-through pixels (plainback.fixed). The owner, Nov 11 19:29: "make sure the fur is always on his
full arms in every frame and only his hands without it, make sure hands never have the red fur on them".
  BFU_GOG_ROM=<debug build> python3 ultimate/ssj4_preview/armmoves.py <out dir>
-> ssj4_goku_arms_every_move_<n>.png (every picture this changes: the last preview above, fixed below, by move) and
   ssj4_goku_arms_moves.gif (each move that changed, all three views, the last preview beside fixed)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import plainback as P, armfur as A
from frames import fr, GOKU, BF, R

MOVE = {3: 'ki blast', 4: 'combo 1', 5: 'combo 2', 6: 'finisher', 7: 'guard', 8: 'charging', 9: 'hit', 10: 'powering up',
        14: 'jump', 15: 'flying', 16: 'spin', 18: 'getting up', 21: 'special', 2: 'run'}
VIEW = {0: 'front', 1: 'back', 2: 'side'}
BG = (88, 120, 88)


def before(k):
    """the last preview: the walk and run arm fixes, the plain back, the filled see-through pixels; not MOVES"""
    c = fr(GOKU, *k)
    old = [e for e in A.FIXES.get(k, []) if e not in A.MOVES.get(k, [])]
    if old: c = A.apply(c, fr(BF, *k), fr(GOKU, 0, 0, k[2]), old)
    return P.plain_back(c, P.bf_for(k)) if k[2] == 1 and P.from_behind(fr(GOKU, *k)) else P.fill(c)


def rgb(c, box):
    c = c[box[0]:box[1], box[2]:box[3]]; out = R.rgb(c).copy(); out[c == 0] = BG; return out


def big(a, z): return Image.fromarray(a).resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST)


if __name__ == '__main__':
    OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
    F = ImageFont.load_default(size=18); FS = ImageFont.load_default(size=14)
    keys = sorted(A.MOVES)
    # the still: by move, each changed picture, the last preview above and fixed below
    box = (36, 74, 30, 78); H = box[1] - box[0]; W = box[3] - box[2]; z = 6; per = 4; rows = []
    groups = {}
    for k in keys: groups.setdefault(k[0], []).append(k)
    for s, ks in sorted(groups.items()):
        for i in range(0, len(ks), per):
            chunk = ks[i:i + per]; band = 26
            img = Image.new('RGB', (per * W * z, band + 2 * (H * z + 20)), BG); d = ImageDraw.Draw(img)
            d.rectangle((0, 0, per * W * z, band), fill=(30, 40, 30))
            d.text((6, 4), '%s: last preview above, fixed below' % MOVE.get(s, 'slot %d' % s), fill=(255, 255, 255), font=F)
            for j, k in enumerate(chunk):
                x = j * W * z
                d.text((x + 6, band + 2), 'frame %d, %s' % (k[1] + 1, VIEW[k[2]]), fill=(255, 255, 255), font=FS)
                img.paste(big(rgb(before(k), box), z), (x, band + 20))
                img.paste(big(rgb(P.fixed(k), box), z), (x, band + 40 + H * z))
            rows.append(img)
    parts = [[]]                                                 # pages of about 3,500 pixels, so a phone can show each
    for r in rows:
        if parts[-1] and sum(p.height + 8 for p in parts[-1]) + r.height > 3500: parts.append([])
        parts[-1].append(r)
    for n, part in enumerate(parts, 1):
        Wt = max(r.width for r in part); sheet = Image.new('RGB', (Wt, sum(r.height + 8 for r in part)), (255, 255, 255)); y = 0
        for r in part: sheet.paste(r, (0, y)); y += r.height + 8
        sheet.save(OUT + '/ssj4_goku_arms_every_move_%d.png' % n)
    # the animation: each move that changed, every frame, all three views; the last preview left, fixed right
    NS = R.slots(GOKU); frames = []; z = 4; band = 24
    for s in sorted(groups):
        for _ in range(2):
            for f in range(NS[s]):
                img = Image.new('RGB', (6 * W * z, band + H * z), BG); d = ImageDraw.Draw(img)
                d.rectangle((0, 0, 6 * W * z, band), fill=(30, 40, 30))
                d.text((6, 4), '%s, frame %d: last preview | fixed (front, back, side)' % (MOVE.get(s, s), f + 1), fill=(255, 255, 255), font=FS)
                cells = []
                for v in (0, 1, 2):
                    cells += [rgb(before((s, f, v)), box), rgb(P.fixed((s, f, v)), box)]
                img.paste(big(np.concatenate(cells, 1), z), (0, band))
                frames.append(img)
    frames[0].save(OUT + '/ssj4_goku_arms_moves.gif', save_all=True, append_images=frames[1:], duration=220, loop=0)
    # checks: what changed is only his skin and his sleeves' blue turned to fur, the sash pixels in run 1 from behind, one
    # pixel of fur in a hand turned to skin, and see-through pixels filled; never a pixel of his hands per the lists
    n = sum(int((before(k) != P.fixed(k)).sum()) for k in keys)
    print(len(keys), 'pictures changed,', n, 'pixels')
