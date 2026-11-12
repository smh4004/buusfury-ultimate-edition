"""Daima Super Saiyan 4 Goku (the saved preview, v4.frame(..., 'daima_pic'); in no build) with every fix Super Saiyan 4 Goku's preview
has (plainback.fixed). The owner, Nov 12 08:47: "Apply the back shape removal and the arm fur fixes to daima goku ONLY everyone else is
good" (armback); 09:00: "Ok preview the other fixes too" (fixed: the see-through pixels in every view and heads.py).
Daima is the same sheet as Super Saiyan 4 Goku in other colours, pixel for pixel (v4.frame recolours the one shaped frame, 'mix' for
the GT form, 'daima_pic' for Daima), so the fixes carry over by place:
  - armback: armfur.FIXES (his arms), and from behind plainback.plain_back (his back plain, the sash across, the see-through pixel at
    the bottom of his hair). The places that change: where that differs from the GT frame in the build, and where the build's GT frame
    (each picture touched up once, at its first place in the figure: v4's arm fixes of that place) differs from v4's own frame for this
    place by skin, fur or a band (a few pixels of 26 places; the costume-out frames 5-8 differ by a whole head a pixel over and are
    left). Each changed pixel in Daima's colours: his fur (GT 31, 32, 33/104/105 -> 127, 39, 40, v3.LOOKS['daima_pic']); skin, the
    wristbands' blue and white as they are; the sash's blue across his back in his sash's colours (as v4 paints his sash); trousers
    as v3's map; anything else (a black filled in his hair, say) as the nearest pixel of the same GT colour that didn't change.
  - fixed: also the see-through pixels in every view (plainback.see_through on his GT frame; filled as the nearest black: plum in his
    hair), and heads.py: the spin's legs from the front in his own boots' and trousers' colours (LEG_MAP), the spin from the side his
    fixed front mirrored and moved, hit 2 from the side Gogeta's head in his plums (gogeta_head), the special's last frame its frame
    before held.
  BFU_GOG_ROM=<debug build> BFU_SSJ4_ROM=<a build from before the touch-up> python3 ultimate/ssj4_preview/daimafix.py <out dir>
-> ssj4_daima_arms_back_before_fixed.pdf and ssj4_daima_heads_legs_holes_before_fixed.pdf (each changed picture once, before and
   fixed side by side), and the checks: in every frame (but costume out 5-8) Daima's shape is Goku's preview's and his skin and fur
   are where Goku's are; the spin from the side is his front mirrored."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
import v3, v4
import plainback as P, armfur as A
import heads as H
from frames import fr, GOKU, BF, GOG, R as GR

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
    g = fr(GOKU, *k); t, belt = goku(first_place(k) if k[0] < 22 else k); mix = v4.frame(*k, 'mix')   # (the fix its picture has in the game)
    at = t != g
    if k not in HEAD_OVER:                                          # the build's first-place arm fixes v4 doesn't have here
        cg = np.vectorize(lambda v: CLASS.get(int(v), ''))(g); cm = np.vectorize(lambda v: CLASS.get(int(v), ''))(mix)
        at |= (g != mix) & (cg != cm) & (cg != '') & (cm != '')
    return t, at, belt


def armback(k):
    """the arm fur and the plain back (08:47)"""
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


def nearest(k, mix, at, y, x, v):
    """Daima's colour at the nearest unchanged pixel his GT frame has in colour v (a black in his hair is his hair's plum)"""
    ys, xs = np.nonzero(~at & (mix == v))
    if not len(ys): return v
    i = int(np.argmin((ys - y) ** 2 + (xs - x) ** 2)); return int(daima(k)[ys[i], xs[i]])


def body(k):
    """armback and the see-through pixels filled in every view (as plainback.fill: boxed in by his hair or outline) -> (Daima's frame,
    his GT frame the same so far)"""
    out = armback(k); mix = v4.frame(*k, 'mix')
    if k[0] >= 22: return out, mix
    t, at, belt = changes(k); mt = mix.copy(); mt[at] = t[at]
    for y, x in P.see_through(mt):
        out[y, x] = nearest(k, mix, at, y, x, 1); mt[y, x] = 1
    return out, mt


# the spin's legs from the front (heads.spin_legs) in Daima's own colours: the colour BF -> Daima his feet have standing and walking
# (BF's boot blues his blues, BF's sole browns his light blue, BF's trousers his oranges, BF's outline black)
LEG_MAP = {80: 160, 81: 160, 157: 69, 159: 158, 161: 160, 79: 80, 63: 64, 64: 109, 65: 110, 1: 1}
HAIR_D = {1: 127, 111: 39, 112: 39}                                    # v3.LOOKS['daima_pic']['hair']


def spin_legs(out, mt, b):
    from scipy import ndimage
    out = out.copy(); top = np.nonzero(b.any(1))[0].min()
    lab, n = ndimage.label(np.isin(b, H.LEG_BF), np.ones((3, 3))); keep = np.zeros(b.shape, bool)
    for t in range(1, n + 1):
        m = lab == t
        if np.nonzero(m.any(1))[0].min() <= top + 3: keep |= m
    near = ndimage.binary_dilation(keep, np.ones((3, 3))) & (b == 1)
    for y, x in zip(*np.nonzero(keep | near)):
        if int(mt[y, x]) in H.HAIR: continue                           # his hair in front (read on his GT frame: Daima's fur is his hair's plum)
        out[y, x] = LEG_MAP[int(b[y, x])]
    return out


def gogeta_head(out, mt, g):
    """hit 2 from the side: heads.gogeta_head (the old head cleared and Gogeta's head laid, read on his GT frame), in Daima's colours:
    every dark of his head his plums (his own head has no black: hair and the line round his face are plum 127), eyes his hair's
    colour (v4), skin and the eye's white as drawn"""
    from scipy import ndimage
    gt = H.gogeta_head(mt, g); out = out.copy()
    Hh, W = mt.shape; Y, X = np.mgrid[0:Hh, 0:W]
    area = (Y >= 40) & (Y <= 59) & (X >= 55) & (X <= 77)                # heads.gogeta_head's head: its hair and their outline,
    hair = np.isin(g, H.G_HAIR) & area & ~((Y >= 53) & (X < 57))       # and its face
    hair |= ndimage.binary_dilation(hair, np.ones((3, 3))) & (g == 1) & area & ~((Y >= 54) & (X < 66))
    head = hair | ((Y >= 47) & (Y <= 53) & (X >= 56) & (X <= 63))
    for y, x in zip(*np.nonzero((gt != mt) | head)):
        if gt[y, x] == 0: out[y, x] = 0; continue
        if not head[y, x]: out[y, x] = HAIR_D[int(gt[y, x])] if int(gt[y, x]) in HAIR_D else int(gt[y, x]); continue   # a pocket filled
        v = int(g[y, x])
        if v in H.G_MAP: out[y, x] = HAIR_D[H.G_MAP[v]]
        elif v in (158, 175, 176): out[y, x] = HAIR_D[1]
        elif v in (127, 129): out[y, x] = 1
        else: out[y, x] = H.FACE.get(v, v)
    return out


def tail(out, mt, k):
    """from behind, in the combos (slots 4-6; the owner, Nov 12 09:28: "fix the tail on some of those back combo frames where it looks
    disconnected"), his tail where Goku's is: it hangs from his crotch to the floor in front of his legs; v4.boots painted BF Goku's
    boots over it (combo 2's first frame kept only its tip at the floor, combo 1's first had boot across its middle), so it looked cut
    off from him. From his hips down (row 62), Goku's fur over Daima's boot -> his fur again; never a pixel beside his skin (09:46,
    "now it looks attached to his hand": the first version also turned a wristband pixel beside his fist in combo 1's third frame to
    fur, and touched other moves)"""
    if k[0] not in (4, 5, 6): return out
    out = out.copy(); top = 62
    skin = np.isin(out, SKIN); near = np.zeros(out.shape, bool)
    near[1:] |= skin[:-1]; near[:-1] |= skin[1:]; near[:, 1:] |= skin[:, :-1]; near[:, :-1] |= skin[:, 1:]
    m = np.zeros(out.shape, bool); m[top:] = np.isin(mt[top:], list(FUR)) & ~np.isin(out[top:], list(set(FUR.values())))
    m &= np.isin(out, BLUES) & ~near
    for y, x in zip(*np.nonzero(m)): out[y, x] = FUR[int(mt[y, x])]
    for (y, x), v in BRIDGE.get(k, {}).items():
        assert out[y, x] == 0; out[y, x] = FUR[v]
    return out


# the one tail from behind whose top hangs in the air (the sheet's, Goku's too): the finisher's first frame, his right leg kicked out
# sideways; the tail starts two rows below his hip's fur, beside the leg he stands on. Two pixels join it to the hip (GT colours).
BRIDGE = {(6, 0, 1): {(64, 58): 104, (65, 58): 32}}


_groups = {}
def first_place(k):
    """the first place (slot order) Goku's figure has this place's picture at: the game shows one picture there, fixed as for its first
    place (fix_table), so Daima's too"""
    if not _groups:
        for q in keys():
            c = fr(GOKU, *q)
            if c.any(): _groups.setdefault(c.tobytes(), q)
    c = fr(GOKU, *k)
    return _groups.get(c.tobytes(), k) if c.any() else k


_f = {}
def fixed(k, with_tail=True):
    """Daima with every fix Super Saiyan 4 Goku's preview has (plainback.fixed: arms, plain back, see-through pixels, heads.py), and
    (09:28) his tail joined from behind (tail); with_tail=False: the preview before that. A place whose picture is Goku's at an earlier
    place (and Daima's the same there) is that place's (charging and the power-up face the camera in every view, the powering up is
    also the special: Nov 12, the build). The see-through pixels the spin's legs and hit 2's new head leave are filled too."""
    if (k, with_tail) in _f: return _f[k, with_tail]
    s, f, d = k; p0 = first_place(k) if s < 22 else k
    if s >= 22: r = daima(k)
    elif p0 != k and (daima(p0) == daima(k)).all(): r = fixed(p0, with_tail)
    elif s == 21 and f == 10: r = fixed((21, 9, 0), with_tail)          # the special's last frame: the one before it, held
    elif s == 16 and d == 2: r = H.spin_side(fixed((16, f, 0), with_tail))   # the spin from the side: his front, mirrored and moved
    else:
        r, mt = body(k); after = None
        if s == 16 and d == 0: r = spin_legs(r, mt, fr(BF, *p0)); after = H.spin_legs(mt, fr(BF, *p0))
        if k == (9, 1, 2): r = gogeta_head(r, mt, fr(GOG, *k)); after = H.gogeta_head(mt, fr(GOG, *k))
        if after is not None:
            t, at, belt = changes(k); mix = v4.frame(*k, 'mix'); r = r.copy()
            for y, x in P.see_through(after): r[y, x] = nearest(k, mix, at, y, x, 1)
        if d == 1 and with_tail: r = tail(r, mt, k)
    _f[k, with_tail] = r; return r


def keys():
    NS = v4.R.slots(v4.AID)
    return [(s, f, d) for s in sorted(NS) if s < 22 for f in range(NS[s]) for d in range(3)]


if __name__ == '__main__':
    from PIL import Image, ImageDraw, ImageFont
    OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
    ks = keys()
    # 08:47's checks: Daima's arms as Goku's fixed arms, class for class (skin, fur, wristband blue), in every frame
    bad = []; px = 0
    for k in ks:
        dm = armback(k); t, at, belt = changes(k); px += int(at.sum())
        tf = np.isin(t, A.FURS); ts = np.isin(t, SKIN); tb = np.isin(t, BLUES)
        df = np.isin(dm, list(set(FUR.values()))); dsk = np.isin(dm, SKIN)
        dark = np.isin(v4.frame(*k, 'mix'), (1, 111, 112))           # v4's own outline and hair there (Daima draws them as hair)
        n = int(((tf & dsk) | (ts & df) | (tb & ~belt & df))[~dark].sum())
        if n and k not in HEAD_OVER: bad.append((k, n))
    print('arms and back:', sum(int((armback(k) != daima(k)).any()) for k in ks), 'frames,', px, 'pixels; skin for fur or fur for skin:', bad)
    assert not bad
    # the rest (09:00): every frame against Super Saiyan 4 Goku's preview (plainback.fixed): the same shape (so no see-through pixel
    # his hasn't), skin and fur in the same places; the spin from the side his front mirrored
    shape = []; cls = []
    for k in ks:
        dm = fixed(k); g = P.fixed(first_place(k))                  # (the game shows its first place's picture there)
        diff = (dm != 0) != (g != 0)
        for (y, x) in BRIDGE.get(k, {}): diff[y, x] = False                 # (the two pixels that join the finisher's tail)
        if k not in HEAD_OVER and diff.any(): shape.append((k, int(diff.sum())))
        own = np.isin(v4.frame(*k, 'mix'), (1, 111, 112)) if k[0] != 16 and k[:2] != (21, 10) and k != (9, 1, 2) else np.zeros(g.shape, bool)
        n = int(((np.isin(g, A.FURS) & np.isin(dm, SKIN)) | (np.isin(g, SKIN) & np.isin(dm, (127, 39, 40))))[~own].sum())
        if n and k not in HEAD_OVER: cls.append((k, n))
    for f in range(4): assert (fixed((16, f, 2)) == H.spin_side(fixed((16, f, 0)))).all()
    print('shape not as Goku\'s:', shape, '; skin/fur not as Goku\'s:', cls)
    assert not shape and not cls
    NAME = {0: 'standing', 1: 'walk', 2: 'run', 3: 'ki blast', 4: 'combo 1', 5: 'combo 2', 6: 'finisher', 7: 'guard', 8: 'charging',
            9: 'hit', 10: 'powering up', 11: 'costume out', 12: 'victory', 13: 'power-up', 14: 'jump', 15: 'flying', 16: 'spin',
            17: 'knocked down', 18: 'getting up', 19: 'costume in', 21: 'special'}
    VIEW = ('front', 'back', 'side'); BG = (88, 120, 88); BOX = (35, 74, 30, 79); H_ = BOX[1] - BOX[0]; W = BOX[3] - BOX[2]; z = 5
    F = ImageFont.load_default(size=15); FB = ImageFont.load_default(size=17)
    def rgb(c):
        c = c[BOX[0]:BOX[1], BOX[2]:BOX[3]]; im = v4.R.rgb(c).copy(); im[c == 0] = BG; return Image.fromarray(im).resize((W * z, H_ * z), Image.NEAREST)
    def sheet(before, after, path, title):
        """each changed frame once: BEFORE on the left, FIXED on the right, two pairs a row"""
        seen = {}; uniq = []
        for k in ks:
            a, b = before(k), after(k)
            if not (a != b).any(): continue
            key = a.tobytes() + b.tobytes()
            if key not in seen: seen[key] = k; uniq.append([k])
            else: next(u for u in uniq if u[0] == seen[key]).append(k)
        per = 14; cols = 2; cw = 2 * W * z + 30; pages = []
        for p in range(0, len(uniq), per):
            part = uniq[p:p + per]; rows = (len(part) + cols - 1) // cols; lab = 40
            img = Image.new('RGB', (cols * cw, 34 + rows * (H_ * z + lab + 10)), (30, 40, 30)); d = ImageDraw.Draw(img)
            d.text((8, 7), title, fill=(255, 255, 255), font=FB)
            for j, u in enumerate(part):
                k = u[0]; x = (j % cols) * cw; y = 34 + (j // cols) * (H_ * z + lab + 10)
                also = '' if len(u) == 1 else ' (and %d more frame%s the same)' % (len(u) - 1, '' if len(u) == 2 else 's')
                d.text((x + 6, y + 2), '%s %d, %s%s' % (NAME.get(k[0], k[0]), k[1] + 1, VIEW[k[2]], also), fill=(255, 255, 255), font=F)
                d.text((x + 6, y + 20), 'BEFORE', fill=(255, 200, 120), font=F); d.text((x + W * z + 16, y + 20), 'FIXED', fill=(140, 255, 140), font=F)
                img.paste(rgb(before(k)), (x, y + lab)); img.paste(rgb(after(k)), (x + W * z + 10, y + lab))
            pages.append(img)
        pages[0].save(path, save_all=True, append_images=pages[1:], resolution=96)
        print(path, len(uniq), 'pictures,', len(pages), 'pages')
    sheet(daima, armback, OUT + '/ssj4_daima_arms_back_before_fixed.pdf', 'Daima SSJ4 Goku: arms and back. In each pair: BEFORE left, FIXED right')
    sheet(armback, lambda k: fixed(k, False), OUT + '/ssj4_daima_heads_legs_holes_before_fixed.pdf',
          'Daima SSJ4 Goku: heads, spin legs, see-through pixels. Each pair: BEFORE left (the last preview), FIXED right')
    # the tail from behind (09:28, 09:46): each changed frame big, before, fixed, and fixed with the changed pixels in yellow
    tk = [k for k in ks if (fixed(k) != fixed(k, False)).any()]
    cb = (40, 74, 34, 74); ch_, cw_ = cb[1] - cb[0], cb[3] - cb[2]; zz = 9; lab = 24; gap = 14
    def crop(c, mark=None):
        c2 = c[cb[0]:cb[1], cb[2]:cb[3]]; im = v4.R.rgb(c2).copy(); im[c2 == 0] = BG
        if mark is not None: im[mark[cb[0]:cb[1], cb[2]:cb[3]]] = (255, 255, 0)
        return Image.fromarray(im).resize((cw_ * zz, ch_ * zz), Image.NEAREST)
    pages = []
    for p in range(0, len(tk), 2):
        part = tk[p:p + 2]; pw = 3 * (cw_ * zz + gap)
        img = Image.new('RGB', (pw, 40 + len(part) * (ch_ * zz + 2 * lab + 12)), (30, 40, 30)); d = ImageDraw.Draw(img)
        d.text((8, 9), 'Daima SSJ4 Goku from behind: his tail joined (combos only)', fill=(255, 255, 255), font=FB)
        for j, k in enumerate(part):
            y = 40 + j * (ch_ * zz + 2 * lab + 12)
            d.text((6, y + 2), '%s %d, back' % (NAME.get(k[0], k[0]), k[1] + 1), fill=(255, 255, 255), font=FB)
            for i, (t, col) in enumerate((('BEFORE', (255, 200, 120)), ('FIXED', (140, 255, 140)), ('FIXED, changed pixels yellow', (255, 255, 0)))):
                d.text((i * (cw_ * zz + gap) + 6, y + lab + 2), t, fill=col, font=F)
            ch = fixed(k) != fixed(k, False)
            for i, im in enumerate((crop(fixed(k, False)), crop(fixed(k)), crop(fixed(k), ch))): img.paste(im, (i * (cw_ * zz + gap), y + 2 * lab))
        pages.append(img)
    pages[0].save(OUT + '/ssj4_daima_tail_before_fixed.pdf', save_all=True, append_images=pages[1:], resolution=96)
    print('tail:', len(tk), 'frames from behind,', sum(int((fixed(k) != fixed(k, False)).sum()) for k in tk), 'pixels:', tk)
