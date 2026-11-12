"""Daima Super Saiyan 4 Goku (the saved preview, v4.frame(..., 'daima_pic'); in no build): the plain back and the arm fur fixes Super
Saiyan 4 Goku's preview has, and nothing else. The owner, Nov 12 08:47: "Apply the back shape removal and the arm fur fixes to daima
goku ONLY everyone else is good".
Daima is the same sheet as Super Saiyan 4 Goku in other colours, pixel for pixel (v4.frame recolours the one shaped frame, 'mix' for
the GT form, 'daima_pic' for Daima), so the fixes carry over by place:
  - Goku's fixed frame here: armfur.FIXES (his arms), and from behind plainback.plain_back (his back plain, the sash across, the
    see-through pixel at the bottom of his hair). Not heads.py and not the see-through fill in the other views (not asked).
  - The places that change: where that differs from the GT frame in the build, and where the build's GT frame (each picture touched up
    once, at its first place in the figure: v4's arm fixes of that place) differs from v4's own frame for this place by skin, fur or
    a band (a few pixels of 26 places; the costume-out frames 5-8 differ by a whole head a pixel over and are left).
  - Each changed pixel in Daima's colours: his fur (GT 31, 32, 33/104/105 -> 127, 39, 40, v3.LOOKS['daima_pic']); skin, the
    wristbands' blue and white as they are; the sash's blue across his back in his sash's colours (as v4 paints his sash); trousers
    as v3's map; anything else (a black filled in his hair, say) as the nearest pixel of the same GT colour that didn't change.
  BFU_GOG_ROM=<debug build> BFU_SSJ4_ROM=<a build from before the touch-up> python3 ultimate/ssj4_preview/daimafix.py <out dir>
-> ssj4_daima_arms_back_before_fixed.pdf (each changed picture once, before and fixed side by side), and the checks: Daima's skin,
   fur and wristbands where Goku's fixed frame has them, in every frame; no hair pixel changed."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
import v3, v4
import plainback as P, armfur as A
from frames import fr, GOKU, R as GR

LOOK = v3.LOOKS['daima_pic']['body']
FUR = {31: LOOK[31], 32: LOOK[32], 33: LOOK[33], 105: LOOK[105], 104: LOOK[33]}   # GT 104 is the sheet's 33/105 (v2.FUR): 40
SKIN = (16, 17, 200, 201, 202, 203, 205, 206); BLUES = (69, 158, 160)
SASH = {69: LOOK[24], 158: LOOK[25], 160: LOOK[26]}                                    # v4: the sash in his trousers' colours
TROUSERS = {t: LOOK[t] for t in (24, 25, 26, 27, 28)}
HEAD_OVER = {(11, f, d) for f in (5, 6, 7, 8) for d in (0, 2)}                        # the build's is another picture (a head over)
CLASS = {**{v: 'skin' for v in SKIN}, **{v: 'fur' for v in A.FURS}, **{v: 'blue' for v in BLUES}}
_d = {}


def daima(k):
    if k not in _d: _d[k] = v4.frame(*k, 'daima_pic')
    return _d[k]


def goku(k):
    """Super Saiyan 4 Goku's frame with the arm fixes and, from behind, the plain back -> (frame, the belt pixels plain_back laid)"""
    g = fr(GOKU, *k); c = g
    if k in A.FIXES: c = A.apply(c, P.bf_for(k), fr(GOKU, 0, 0, k[2]), A.FIXES[k])
    belt = np.zeros(g.shape, bool)
    if k[2] == 1 and P.from_behind(g):
        b = P.bf_for(k); before = c; c = P.plain_back(c, b)
        for y, (x0, x1) in P.belt_rows(b).items(): belt[y, x0:x1 + 1] = True
        belt &= (c != before) & np.isin(c, BLUES)
    return c, belt


def changes(k):
    """-> (Goku's fixed frame, the places Daima changes, the belt places)"""
    g = fr(GOKU, *k); t, belt = goku(k); mix = v4.frame(*k, 'mix')
    at = t != g
    if k not in HEAD_OVER:                                          # the build's first-place arm fixes v4 doesn't have here
        cg = np.vectorize(lambda v: CLASS.get(int(v), ''))(g); cm = np.vectorize(lambda v: CLASS.get(int(v), ''))(mix)
        at |= (g != mix) & (cg != cm) & (cg != '') & (cm != '')
    return t, at, belt


def fixed(k):
    s, f, d = k
    out = daima(k).copy()
    if s >= 22: return out
    t, at, belt = changes(k)
    if not at.any(): return out
    mix = v4.frame(*k, 'mix'); same = ~at & (mix != 0)
    for y, x in zip(*np.nonzero(at)):
        v = int(t[y, x])
        if belt[y, x]: out[y, x] = SASH[v]
        elif v in FUR: out[y, x] = FUR[v]
        elif v in SKIN or v in BLUES or v in (0, 2): out[y, x] = v
        elif v in TROUSERS: out[y, x] = TROUSERS[v]
        else:                                                        # the nearest unchanged pixel of that GT colour
            ys, xs = np.nonzero(same & (mix == v))
            if len(ys):
                i = int(np.argmin((ys - y) ** 2 + (xs - x) ** 2)); out[y, x] = daima(k)[ys[i], xs[i]]
            else: out[y, x] = v
    return out


def keys():
    NS = v4.R.slots(v4.AID)
    return [(s, f, d) for s in sorted(NS) if s < 22 for f in range(NS[s]) for d in range(3)]


if __name__ == '__main__':
    from PIL import Image, ImageDraw, ImageFont
    OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
    ks = keys(); ch = [k for k in ks if (fixed(k) != daima(k)).any()]
    # checks: Daima's arms as Goku's fixed arms, class for class (skin, fur, wristband blue), in every frame
    bad = []; px = 0
    for k in ks:
        dm = fixed(k); t, at, belt = changes(k); px += int(at.sum())
        tf = np.isin(t, A.FURS); ts = np.isin(t, SKIN); tb = np.isin(t, BLUES)
        df = np.isin(dm, list(set(FUR.values()))); dsk = np.isin(dm, SKIN); db = np.isin(dm, BLUES)
        dark = np.isin(v4.frame(*k, 'mix'), (1, 111, 112))           # v4's own outline and hair there (Daima draws them as hair)
        n = int(((tf & dsk) | (ts & df) | (tb & ~belt & df))[~dark].sum())
        if n and k not in HEAD_OVER: bad.append((k, n))
    print(len(ks), 'frames;', len(ch), 'change,', px, 'pixels; frames where Daima has skin for fur or fur for skin or band:', bad)
    assert not bad
    NAME = {0: 'standing', 1: 'walk', 2: 'run', 3: 'ki blast', 4: 'combo 1', 5: 'combo 2', 6: 'finisher', 7: 'guard', 8: 'charging',
            9: 'hit', 10: 'powering up', 11: 'costume out', 12: 'victory', 13: 'power-up', 14: 'jump', 15: 'flying', 16: 'spin',
            17: 'knocked down', 18: 'getting up', 19: 'costume in', 21: 'special'}
    VIEW = ('front', 'back', 'side'); BG = (88, 120, 88); BOX = (35, 74, 30, 79); H = BOX[1] - BOX[0]; W = BOX[3] - BOX[2]; z = 5
    F = ImageFont.load_default(size=15); FB = ImageFont.load_default(size=17)
    def rgb(c):
        c = c[BOX[0]:BOX[1], BOX[2]:BOX[3]]; im = v4.R.rgb(c).copy(); im[c == 0] = BG; return Image.fromarray(im).resize((W * z, H * z), Image.NEAREST)
    # each changed frame once: BEFORE on the left, FIXED on the right, a pair per row, two pairs a row
    seen = {}; uniq = []
    for k in ch:
        key = daima(k).tobytes() + fixed(k).tobytes()
        if key not in seen: seen[key] = k; uniq.append([k])
        else: next(u for u in uniq if u[0] == seen[key]).append(k)
    per = 14; cols = 2; cw = 2 * W * z + 30; pages = []
    for p in range(0, len(uniq), per):
        part = uniq[p:p + per]; rows = (len(part) + cols - 1) // cols; lab = 40
        img = Image.new('RGB', (cols * cw, 34 + rows * (H * z + lab + 10)), (30, 40, 30)); d = ImageDraw.Draw(img)
        d.text((8, 7), 'Daima SSJ4 Goku: arms and back. In each pair: BEFORE left, FIXED right', fill=(255, 255, 255), font=FB)
        for j, u in enumerate(part):
            k = u[0]; x = (j % cols) * cw; y = 34 + (j // cols) * (H * z + lab + 10)
            also = '' if len(u) == 1 else ' (and %d more frame%s the same)' % (len(u) - 1, '' if len(u) == 2 else 's')
            d.text((x + 6, y + 2), '%s %d, %s%s' % (NAME.get(k[0], k[0]), k[1] + 1, VIEW[k[2]], also), fill=(255, 255, 255), font=F)
            d.text((x + 6, y + 20), 'BEFORE', fill=(255, 200, 120), font=F); d.text((x + W * z + 16, y + 20), 'FIXED', fill=(140, 255, 140), font=F)
            img.paste(rgb(daima(k)), (x, y + lab)); img.paste(rgb(fixed(k)), (x + W * z + 10, y + lab))
        pages.append(img)
    pages[0].save(OUT + '/ssj4_daima_arms_back_before_fixed.pdf', save_all=True, append_images=pages[1:], resolution=96)
    print(len(uniq), 'different pictures changed,', len(pages), 'pages')
