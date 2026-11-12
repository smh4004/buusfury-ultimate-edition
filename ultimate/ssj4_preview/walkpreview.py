"""Super Saiyan 4 Goku's stand, walk and run as they are and with walkfix.py's fixes, for the owner (whole figures on the game's green):
a still per view, GIFs of the walk and the run in three views, and from behind alone, bigger.
  BFU_GOG_ROM=<debug build> python3 ultimate/ssj4_preview/walkpreview.py <out dir>"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from frames import fr, GOKU, BF, R
import walkfix

OUT = sys.argv[1]; BG = (88, 120, 88); BOX = (37, 72, 39, 80); H = BOX[1] - BOX[0]; W = BOX[3] - BOX[2]
F = ImageFont.load_default(size=16); FS = ImageFont.load_default(size=13)


def fixed(k): return walkfix.apply(fr(GOKU, *k), fr(BF, *k), walkfix.FIXES.get(k, []), fr(GOKU, 0, 0, k[2]))
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
    print(sorted(os.listdir(OUT)))
