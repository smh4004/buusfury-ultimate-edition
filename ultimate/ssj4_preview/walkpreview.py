"""Super Saiyan 4 Goku's stand, walk and run as they are and with walkfix.py's fixes, for the owner (whole figures on the game's green):
a still per view, GIFs of the walk and the run in three views, and from behind alone, bigger.
  BFU_GOG_ROM=<debug build> python3 ultimate/ssj4_preview/walkpreview.py <out dir>"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json, struct
from frames import fr, GOKU, BF, R, ROM
import walkfix
_forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
VEGETA = R.frame(struct.unpack_from('<H', R.rom, 0x800000 + 24 * _forms['vegeta_gt_ssj4'] + 0x0E)[0] - 9, 0, 0, 1)

OUT = sys.argv[1]; BG = (88, 120, 88); BOX = (37, 72, 39, 80); H = BOX[1] - BOX[0]; W = BOX[3] - BOX[2]
F = ImageFont.load_default(size=16); FS = ImageFont.load_default(size=13)


NS = {a: R.slots(a) for a in (GOKU, BF)}
_bf = {}
def bf_for(k):
    """BF Goku's frame his frame k was drawn on: the same place when BF's slot has as many frames, else the BF frame of that view that
    overlaps his most (everything but the hair), laid on his"""
    s, f, d = k
    if NS[BF].get(s) == NS[GOKU].get(s): return fr(BF, *k)
    if k in _bf: return _bf[k]
    c = fr(GOKU, *k); cm = (c > 0) & ~np.isin(c, (1, 111, 112)); best = None
    for t, n in NS[BF].items():
        for g in range(n):
            b = fr(BF, t, g, d); bm = (b > 0) & ~np.isin(b, (1, 111, 112))
            if not bm.any(): continue
            for dy in range(-3, 4):
                for dx in range(-4, 5):
                    m = int((np.roll(np.roll(bm, dy, 0), dx, 1) & cm).sum())
                    if best is None or m > best[0]: best = (m, dy, dx, b)
    _bf[k] = np.roll(np.roll(best[3], best[1], 0), best[2], 1); return _bf[k]
def fixed(k): return walkfix.apply(fr(GOKU, *k), bf_for(k), walkfix.FIXES.get(k, []), fr(GOKU, 0, 0, k[2]), VEGETA, k[2])
def cell(c):
    c = c[BOX[0]:BOX[1], BOX[2]:BOX[3]]; rgb = R.rgb(c).copy(); rgb[c == 0] = BG; return rgb
now = lambda k: cell(fr(GOKU, *k)); new = lambda k: cell(fixed(k))
big = lambda im, z: Image.fromarray(im).resize((im.shape[1] * z, im.shape[0] * z), Image.NEAREST)
VIEWS = ((2, 'side'), (1, 'back'), (0, 'front'))


def still(d, name, z=6):
    lines = [[(0, 0, d)] + [(1, f, d) for f in range(4)], [(2, f, d) for f in range(4)]]; band = 22
    Wp = 5 * W * z; img = Image.new('RGB', (Wp, 4 * H * z + 4 * band), BG); dr = ImageDraw.Draw(img); y = 0
    for li, line in enumerate(lines):
        for what, fn in (('now', now), ('fixed', new)):
            dr.rectangle((0, y, Wp, y + band), fill=(30, 40, 30))
            dr.text((6, y + 2), '%s, %s: %s' % (name, ('standing and walk', 'run')[li], what), fill=(255, 255, 255), font=F); y += band
            img.paste(big(np.concatenate([fn(k) for k in line], 1), z), (0, y)); y += H * z
    return img


def gif(path, seq, ms, views=VIEWS, z=5, reps=3):
    frames = []; band = 20
    for _ in range(reps):
        for s, f in seq:
            img = Image.new('RGB', (len(views) * W * z, 2 * H * z + 2 * band), BG); dr = ImageDraw.Draw(img); y = 0
            for what, fn in (('now', now), ('fixed', new)):
                dr.rectangle((0, y, len(views) * W * z, y + band), fill=(30, 40, 30))
                for i, (d, v) in enumerate(views): dr.text((i * W * z + 6, y + 2), '%s, %s' % (what, v), fill=(255, 255, 255), font=FS)
                y += band; img.paste(big(np.concatenate([fn((s, f, d)) for d, _ in views], 1), z), (0, y)); y += H * z
            frames.append(img)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=ms, loop=0)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for d, v in VIEWS: still(d, 'from the ' + v if v != 'back' else 'from behind').save('%s/ssj4_goku_%s_now_and_fixed.png' % (OUT, v))
    gif(OUT + '/ssj4_goku_walk_now_and_fixed.gif', [(1, f) for f in range(4)], 150)
    gif(OUT + '/ssj4_goku_run_now_and_fixed.gif', [(2, f) for f in range(4)], 110)
    gif(OUT + '/ssj4_goku_from_behind_walk_now_and_fixed.gif', [(1, f) for f in range(4)], 170, views=((1, 'back'),), z=8)
    gif(OUT + '/ssj4_goku_from_behind_run_now_and_fixed.gif', [(2, f) for f in range(4)], 120, views=((1, 'back'),), z=8)
    # every frame of his from behind, now above fixed, slot by slot (the tail is in all of them)
    n = R.slots(GOKU); lines = []; per = 10
    cells = [(s, f) for s in sorted(n) if s < 22 for f in range(n[s]) if fr(GOKU, s, f, 1).any()]
    seen = set(); keep = []
    for s, f in cells:
        k = fr(GOKU, s, f, 1).tobytes()
        if k in seen: continue
        seen.add(k); keep.append((s, f))
    z = 3; rows = []
    for i in range(0, len(keep), per):
        chunk = keep[i:i + per] + [None] * (per - len(keep[i:i + per]))
        for fn in (now, new):
            rows.append(np.concatenate([fn((s, f, 1)) if s is not None else np.full((H, W, 3), BG, np.uint8) for s, f in
                                        [(c if c else (None, None)) for c in chunk]], 1))
        rows.append(np.full((3, per * W, 3), 255, np.uint8))
    big(np.concatenate(rows, 0), z).save(OUT + '/ssj4_goku_every_frame_from_behind_now_and_fixed.png')
    print(sorted(os.listdir(OUT)))
