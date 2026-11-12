"""Scratch, fourth look (the owner, Nov 11 19:17): "Stop with this head bob on the idle stuff how are we doing this again. And you managed to
mess up the fur on the hands and arms all over again when we fixed that already on all the sprites. Also clean up the stray pixels and
clipping in his hair, stray on back view and clipping kind of at the bottom on front view. Also make his eyes more yellowish accurately
to regular SSJ4 Goku"; Daima: "same shit with the back view stray pixel and the head bob idle, the colors look good now though can you
just make his eyes the color to match the hair and eyebrows and then fix his boots color so they actually look right with the blue and
the red stripe in all frames".
  - idle: the second idle frame was the first with its head a pixel to the left (the sheet's): now the two are the same frame
  - the Kamehameha from the front: the sheet turned BF Goku's hands, wristbands and all, to fur (a red mass on his chest): the hands
    between his two wristbands get BF Goku's skin back and the bands their blue; his forearms keep their fur
  - hair: the light grey pixel on the back head's left edge is gone; the new front hair ends in strands, not in a flat cut
  - eyes: gold (GT); Daima: the hair's colour
  - Daima's boots: BF Goku's own boots, frame for frame (the sheet was drawn on his frames): their blues, their laces red"""
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
sys.path.insert(0, 'ultimate')
import v2
from v2 import *
import v3, hands as H, gt, armhand
from scipy import ndimage

# the new front hair's last rows, as strands (Gogeta's locks end in two points a side)
TIPS = {14: '..###a####.......####ba#.', 15: '..###aa###.......###ba###', 16: '...##a.##.........##.a##.', 17: '....#...#.........#...#..'}
def front_hair():
    """Gogeta's front hair (rows 0-13), ending in strands; in the two colours his hair has now, black and its one dark grey (the
    owner, Nov 11 20:10: "I don't want that gray strands in the front just the same colors as current"): the lighter grey that
    drew strands by his face is black."""
    h = v2.gogeta_hair(0); out = np.zeros((18, h.shape[1]), h.dtype); out[:14, :] = h[:14]
    for y, row in TIPS.items():
        for x, ch in enumerate(row):
            if x < out.shape[1]: out[y, x] = {'.': 0, '#': 1, 'a': 111, 'b': 112}[ch]
    out[out == 112] = 1
    return out
v2.NEW[0] = front_hair()
STRAY = {1: ((7, 1, 117, 0), (5, 21, 112, 111))}       # the back head's light pixels on its edges (row, column, colour, what it becomes)
GOLD = 110                                      # (248,208,0)
BF_BLUE = {157: 69, 159: 158, 161: 160}
BF_LACE = {63: 33, 64: 33, 65: 105, 79: 32, 78: 32}     # BF Goku's boot laces (his gi's oranges) -> reds
BOOT_DARK = (1, 111, 112, 116, 117, 118, 206)
BOOT_FALL = {1: 69, 111: 158, 112: 158, 116: 160, 117: 160, 118: 160, 206: 118}


def bf_pick(c, slot, d):
    """-> (which of BF Goku's frames of this slot and view fits best, that frame laid on c) or (None, None)"""
    best = None
    for k, b in enumerate(H.bf_frames(slot, d)):
        if not b.any(): continue
        n, dy, dx = H.lay(b, c)
        if best is None or n > best[0]: best = (n, dy, dx, k, b)
    if best is None: return None, None
    n, dy, dx, k, b = best
    return k, np.roll(np.roll(b, dy, 0), dx, 1)


def bf_for(c, slot, d): return bf_pick(c, slot, d)[1]


BF_GI = (63, 64, 65, 79, 78)
SLEEVE_FUR = {69: 31, 158: 32, 160: 33}
def kame_hands(c, slot, d, loc):
    """The Kamehameha seen from the front. BF Goku's frame: his two arms come in from his sleeves to his wrists, which meet in the
    middle (two slanting strokes of wristband blue in the lowest rows of blue inside the mass of skin), and his hands are the skin from
    that row down, the lower hand's fingers over his thigh. The sheet turned all of it to fur. The owner's own Super Saiyan 4 Gogeta,
    drawn on the same frame, shows what is meant: fur down to the wrists, hands of skin under them. So: BF's hands get his skin back
    and the bands at his wrists their blue; his arms keep their fur, and BF's other blue there (his sleeves: he has none) is fur."""
    if slot != 18 or d != 0 or loc is None: return c
    which, b = bf_pick(c, slot, d)
    if b is None: return c
    top = loc[2]; out = c.copy(); furs = gt.SS4_FUR | {16, 104}
    blue = np.isin(b, list(gt.BF_BAND)); blue[:top + 15] = False; blue[top + 23:] = False                 # (under them his boots)
    lab, n = ndimage.label(blue, np.ones((3, 3)))
    for t in range(1, n + 1):
        if (lab == t).sum() > 16: blue[lab == t] = False                          # (his sash)
    rows = np.nonzero(blue.any(1))[0]
    if not len(rows): return c
    r0 = rows.max()
    hand = np.isin(b, list(gt.BF_SKIN)); hand[:r0] = False; hand[r0 + 6:] = False
    if which == 0:
        # the wind-up, his hands cupped at his hip: the sheet kept both wristbands (and his sash beside them) and drew the hands
        # under them as fur: only those turn to skin
        hand[r0 + 2:] = False
        for y, x in zip(*np.nonzero(hand)):
            if c[y, x] in furs: out[y, x] = b[y, x]
        return out
    near = ndimage.binary_dilation(hand, np.ones((3, 3)))
    band = blue & near; band[:r0 - 1] = False
    for y, x in zip(*np.nonzero(hand)):
        if c[y, x] in furs: out[y, x] = b[y, x]
    for y, x in zip(*np.nonzero(band)):
        if c[y, x] in furs or int(c[y, x]) in SLEEVE_FUR: out[y, x] = gt.BF_BAND[int(b[y, x])]
    for y, x in zip(*np.nonzero(blue & ~band)):
        if int(c[y, x]) in SLEEVE_FUR: out[y, x] = SLEEVE_FUR[int(c[y, x])]
    return out


BOOT_LIKE = BOOT_DARK + (16, 17, 205, 206, 207, 24, 25, 26, 69, 158, 160)
BF_TROUSER = {63: 25, 64: 26, 65: 27, 79: 24}
SOLE = (80, 81); SHEET_LACE = {24: 32, 25: 33, 26: 33, 27: 105, 28: 105}
def boots(out, c0, slot, d, hair, top=None, stripe=True):
    """-> {(y, x): colour}: Daima's boots are BF Goku's at the same pixels (the sheet was drawn on his frames): each patch of BF's boot
    blue over which the sheet has its GT boot (dark, grey, sole brown: not fur, skin or hair) gets BF's blues back, and BF's laces
    inside it turn red. BF's other blues (wristbands, sash, undershirt) lie under the sheet's fur, skin and own blue: left alone."""
    b = bf_for(c0, slot, d); res = {}
    if b is None: return res
    blue = np.isin(b, list(BF_BLUE)); lab, n = ndimage.label(blue, np.ones((3, 3))); keep = np.zeros(out.shape, bool)
    for t in range(1, n + 1):
        m = lab == t; under = out[m]
        like = np.isin(under, BOOT_LIKE) & ~hair[m]; dark = np.isin(under, BOOT_DARK + (16, 17, 205, 206, 207)) & ~hair[m]
        if dark.sum() >= 2 and like.sum() * 2 >= m.sum() and not np.isin(under, (69, 158, 160)).sum() * 2 > m.sum(): keep |= m & (out > 0) & ~hair
    for y, x in zip(*np.nonzero(keep)): res[y, x] = BF_BLUE[int(b[y, x])]
    cnt = ndimage.convolve(keep.astype(int), np.ones((3, 3)), mode='constant')
    lace = np.isin(b, list(BF_LACE)) & (cnt >= 3) & ~keep & (out > 0) & ~hair & ~np.isin(out, list(gt.SS4_FUR) + [104, 200, 201, 203])
    for y, x in zip(*np.nonzero(lace)): res[y, x] = BF_LACE[int(b[y, x])]
    # what is left of the sheet's own boot beside those (BF's boot was a pixel smaller here and there): the sheet's dark made blue
    grown = ndimage.binary_dilation(keep | lace, np.ones((3, 3)))
    for y, x in zip(*np.nonzero(grown & ~keep & ~lace & np.isin(out, BOOT_DARK) & ~hair)): res[y, x] = BOOT_FALL[int(out[y, x])]
    # The frames where the sheet posed his legs its own way (BF's boots are not under the sheet's): the sheet's own boot. Its boots
    # are the only things drawn in grey and in BF's sole browns; a patch of black, grey and sole (not his hair or face) with one of
    # those in it, or lying on a boot already found, is a boot as far as five pixels from them; farther up the same patch is a leg
    # the sheet painted black. A row of trouser yellow shut between two rows of boot is the sheet's lace: red.
    bootc = np.isin(out, BOOT_DARK + SOLE) & ~hair; lab, n = ndimage.label(bootc, np.ones((3, 3)))
    seed = np.isin(out, (116, 118) + SOLE) & bootc; bfb = ndimage.binary_dilation(keep | lace, np.ones((3, 3))) & bootc
    legs = np.zeros(out.shape, bool); H = out.shape[0]
    for t in range(1, n + 1):
        m = lab == t; start = m & (seed | keep | lace)
        if not (m & seed).any() and (m & bfb).sum() < 3: continue
        if not start.any(): start = m & bfb
        part = start.copy()
        for _ in range(5): part = ndimage.binary_dilation(part, np.ones((3, 3))) & m
        legs |= m & ~part
        for y, x in zip(*np.nonzero(part)):
            if (y, x) not in res and int(out[y, x]) in BOOT_FALL: res[y, x] = BOOT_FALL[int(out[y, x])]
        up = np.roll(part, 1, 0); down = np.roll(part, -1, 0)
        for y, x in zip(*np.nonzero(np.isin(out, (24, 25, 26, 27, 28)) & up & down)): res[y, x] = SHEET_LACE[int(out[y, x])]
        if stripe and not any(res.get((y, x)) in (33, 32, 105) for y, x in zip(*np.nonzero(ndimage.binary_dilation(part, np.ones((3, 3)))))):
            ys = np.nonzero(part.any(1))[0]; y = max(ys.min(), ys.max() - 2); xs = np.nonzero(part[y])[0]
            inner = [x for x in xs if part[y, x - 1] and part[y, x + 1]] or [int(xs[len(xs) // 2])]
            for x in inner[max(0, len(inner) // 2 - 1):len(inner) // 2 + 1]: res[y, x] = 33                          # his lace: a red stroke
    # a leg the sheet painted in its boot's black from the thigh down (a bent leg, here and there): with a blue boot under it that
    # reads as black shorts. Where BF Goku has his trousers there, it is trousers (the sheet's own yellows, by BF's shade)
    for y, x in zip(*np.nonzero(legs & np.isin(b, list(BF_TROUSER)))):
        if (y, x) not in res: res[y, x] = -BF_TROUSER[int(b[y, x])]              # (negative: one of his own colours, still to be given the look's)
    return res


def uncovered(out, c0, loc):
    """The new front hair is wider than the old: a hand raised beside his head (skin seven pixels or more to either side of his
    face's middle) that it would lie over stays in front of it, with the wristband beside it."""
    if loc is None or loc[3] != 0: return out
    res = out.copy(); hx = int(loc[1]) + FULL[0].shape[1] // 2
    over = np.isin(out, (1, 111, 112)) & ~np.isin(c0, (1, 111, 112))
    far = np.zeros(out.shape, bool); far[:, :max(hx - 6, 0)] = True; far[:, hx + 7:] = True
    hand = over & far & np.isin(c0, (200, 201, 202, 203, 16, 17))
    band = over & np.isin(c0, (69, 158, 160)) & ndimage.binary_dilation(hand, np.ones((3, 3)))
    res[hand | band] = c0[hand | band]
    return res


ARMS_UP = (13, 1)            # the power-up's second frame: his arms raised, fists beside his head
def arms_up():
    """The owner, Nov 11 20:53: "Fix the arms raised pose for Goku ssj4 on both where his base form hair is on the sides while his ssj4
    is in the center". The sheet kept BF Goku's whole head there (his black spikes out past both arms, his shouting face) and gave
    his arms fur on three columns of four. BF's frame faces the camera in all three views, and so does this.
    BF's head (his hair, and his face between the arms) comes off; Super Saiyan 4's front head goes on where BF's eyes are (two rows
    higher than standing), its hair behind the raised arms and fists; the arms' leftover skin columns turn to fur, the wristband's
    one skin pixel to its blue. -> (frame, where the head is, which pixels are the new hair)"""
    c = R.frame(AID, *ARMS_UP, 0).copy(); b = R.frame(106, *ARMS_UP, 0); H, W = c.shape
    stand = v2.locate(R.frame(AID, 0, 0, 0)); eyes = lambda a: np.nonzero((a == 2).any(1))[0].min()
    x, y = int(stand[1]), int(stand[2]) + int(eyes(b)) - int(eyes(R.frame(106, 0, 0, 0)))
    t = FULL[0]; hair = v2.NEW[0]; dx, dy = v2.G_OFF[0]
    face = (t > 0) & ~OLD[0]; face[ROWS:] = False
    face[ROWS:, 7:16] = t[ROWS:, 7:16] > 0                           # his chin and neck; not the template's shoulders (his arms are up)
    gone = np.zeros(c.shape, bool); gone[:y + 18] = b[:y + 18] == 1   # BF's hair, eyebrows and pupils
    wx = np.nonzero((b == 2).any(0))[0]; f0, f1 = int(wx.min()) - 1, int(wx.max()) + 1          # BF's face: between his arms, by the whites of his eyes
    gone[y + 8:y + 17, f0:f1] |= b[y + 8:y + 17, f0:f1] > 0
    gone &= ~np.isin(b, list(gt.BF_BAND))
    arm = np.zeros(c.shape, bool)                                    # his arms from the wristbands down to his shoulders: BF's skin outside his face
    arm[y + 8:y + 17] = np.isin(b[y + 8:y + 17], list(gt.BF_SKIN)) & ~gone[y + 8:y + 17]
    out = c.copy(); out[gone] = 0
    for yy, xx in zip(*np.nonzero(hair)):
        Y, X = y + dy + yy, x + dx + xx
        if 0 <= Y < H and 0 <= X < W and out[Y, X] == 0: out[Y, X] = hair[yy, xx]
    for yy, xx in zip(*np.nonzero(face)):
        Y, X = y + yy, x + xx
        if gone[Y, X] or c[Y, X] == 0 or (yy >= ROWS and not arm[Y, X]): out[Y, X] = t[yy, xx]
    for Y, X in zip(*np.nonzero(arm)):
        if int(out[Y, X]) in armhand.TO_FUR and out[Y, X] == c[Y, X]: out[Y, X] = armhand.TO_FUR[int(out[Y, X])]
    band = np.isin(b, list(gt.BF_BAND)) & np.isin(out, (16, 17, 200, 201, 202, 203)); band[y + 9:] = False
    for Y, X in zip(*np.nonzero(band)): out[Y, X] = gt.BF_BAND[int(b[Y, X])]
    mine = np.zeros(c.shape, bool)
    for yy, xx in zip(*np.nonzero(hair)):
        Y, X = y + dy + yy, x + dx + xx
        if 0 <= Y < H and 0 <= X < W and out[Y, X] == hair[yy, xx] and (gone[Y, X] or c[Y, X] == 0): mine[Y, X] = True
    return out, (1.0, x, y, 0), mine


def frame(slot, f, d, kind):
    """kind: 'now'; 'mix' (GT: the new front hair; side and back as they are); 'daima', 'daima_pic'"""
    if kind == 'now': return R.frame(AID, slot, f, d)
    if slot == 0: f = 0                                              # the idle's frames are one frame: no head bob
    c0 = R.frame(AID, slot, f, d)
    hair_is = None
    if (slot, f) == ARMS_UP: out, loc, hair_is = arms_up(); c0 = out
    else:
        out, loc = shaped(slot, f, d, views=(0,))
        out = uncovered(out, c0, loc)
        out = kame_hands(out, slot, d, loc)
    if (slot, d) != (18, 0) and (slot, f) != ARMS_UP: out, _ = armhand.everything(out, bf_for(c0, slot, d), loc, (slot, f, d), c0)   # (that view is kame_hands')
    if loc is not None:
        sc, x, y, v = loc
        for yy, xx, col, to in STRAY.get(v, ()):
            if out[y + yy, x + xx] == col: out[y + yy, x + xx] = to
    res = out.copy()
    def at(pts, want, to):
        sc, x, y, v = loc; t = FULL[v]; Hh, W = out.shape
        for yy, xx in pts:
            Y, X = y + yy, x + xx
            if 0 <= Y < Hh and 0 <= X < W and t[yy, xx] in want and out[Y, X] == t[yy, xx]: res[Y, X] = to
    if kind == 'mix':
        for k, to in v2.FUR.items(): res[out == k] = to
        if loc is not None: at(v3.IRIS.get(loc[3], ()), (25,), GOLD)
        return res
    look = v3.LOOKS[kind]; p = v3.parts(out, loc)
    if hair_is is not None: p['hair'] = hair_is                      # (his arms cut the hair in pieces there: it is known exactly)
    for k, to in look['body'].items(): res[out == k] = to
    for k, to in look['hair'].items(): res[p['hair'] & (out == k)] = to
    for k, to in ((69, 24), (157, 24), (158, 25), (159, 25), (160, 26), (161, 26)): res[p['sash'] & (out == k)] = look['body'][to]
    dark = np.isin(out, v3.DARK); hairc = np.zeros(out.shape, bool)
    for comp in v3.components(dark):
        m = v3.as_mask(out.shape, [comp])
        if (p['hair'] & m).any() or (p['face'] & m).any(): hairc |= m
    nothair = np.zeros(out.shape, bool)
    if slot == 15 and d == 1:                                        # flying, from behind: his soles, joined to his hair by a pixel of outline
        sash = np.nonzero(np.isin(out, (69, 158, 160)).any(1))[0]
        if len(sash): nothair[sash.max() + 1:] = True
    for (yy, xx), col in boots(out, c0, slot, d, (hairc & ~nothair) | p['face'], None if loc is None else loc[2], stripe=not nothair.any()).items():
        res[yy, xx] = col if col >= 0 else look['body'][-col]
    if loc is not None:
        at(v3.BROWS.get(loc[3], ()), (1, 111), look['hair'][1]); at(v3.LINER.get(loc[3], ()), (31,), 1); at(v3.IRIS.get(loc[3], ()), (25,), look['hair'][1])
    return res
