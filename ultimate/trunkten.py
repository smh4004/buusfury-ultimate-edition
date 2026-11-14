"""Trunkten, the Potara fusion of Goten and Trunks (Nov 14, the owner: "lets start on the Trunkten potara fusion with the green gi and
orange belt and orange undershirt you can maybe use this model as a base but keep the black/purple base hair color inverted from
gotenks"; 17:19, on the first preview: "Try Vegitos hair shape instead and use the Potara from him if he has it"). The model is Teen
Gohan in Goku's gi (teen_bojack.py, approved and locked 16:29): the Super Saiyan frames teen.py makes, his body and face pixel for pixel,
with the clothes teen_bojack.parts finds dressed again and Vegito's hair in place of his.
  his gi (the greys of his top, the purple of his trousers): two greens, GI (BF 215, the lighter greys and purple; 216, the darker),
    its navy edges the gi's dark outline (BF 70), as Vegito's vest is drawn: one colour, its shade and a dark line round it (17:43, the
    owner: "make his gi cleaner like vegitos so you can actually see the shirt and undershirt against each other"). LoG2 has none of
    these colours, so the figure's colour map sends LoG2 indices teen.py never uses to them (CMAP);
  his undershirt, Goku's orange: its sleeves (sleeves(): the top two rows of his gi at each shoulder, outside his neck, as Vegito's
    orange shoulders) and Goku's V under his neck;
  his sash (the reds that don't touch his skin): Goku's orange; his wristbands (the reds on his hands): Goku's navy, as the model's;
  his trousers' navy edge: the darkest green; his socks and shoes: orange, the sash's (17:42, the owner: "make his boots orange to
    match his belt like that first ref pic next to gotenks"), their black as it is.
Hair (head()): BF's Vegito (actor 275, the game's only Vegito: Super Vegito), his stance's head in each view, every pixel of its hair
as BF draws it, laid on the model's face by the eyes (the two games draw them the same size: Vegito's eyes, ears and face are as wide
as Teen Gohan's). Each frame's own head is matched to the stance's head it lies on (front, back, side or the side turned round, moved
up to 8 pixels: like teen's own placing of heads) and Vegito's hair goes there, so it stays put on his head from frame to frame. The
model's hair goes (its gold, its brown outline and its lights); Vegito's covers that place and the air, never his face or anything in
front of his head; where his hair left the forehead or a temple open, Vegito's own skin there (in the model's skin colours).
  base: Gotenks's colours turned round (his crown black and sides purple): the crown purple (Gotenks's purples, BF 148/147/146, 138 the
    outline), the sides and what hangs low black with dark grey lights, as LoG2's black hair: where the head's outline, smoothed, faces
    more than A degrees from up and lies near it (split_hair, once per view); his own dark eyes;
  Super Saiyan and Super Saiyan 2: the model's Super Saiyan 2 golds (no outline, as the owner wanted for it; 17:42: "Make the SSJ1 hair
    color cleaner and the same as SSJ2 Trunkten", Super Vegito's own olive-outlined yellow had been the Super Saiyan's); Super Saiyan's
    eyes the model's teal, Super Saiyan 2's its green.
Potara earrings: Vegito's (BF 29, his sprite's one pixel under each ear), one under each of the model's ears (EARS, the stance's).
Knocked down (animation 3's last two frames) every form has the model's long black hair, as Teen Gohan's approved frames do.
frame() makes a look's frame and checks it (problems()); a frame that fails stops the build. made(look) is sprites.log2_anim's frame
source for the look's figure."""
import struct
import numpy as np
from scipy import ndimage
import teen as T, teen_bojack as B, headfit as F

SKIN = F.cls(T.SKIN_S)
GOLD = F.cls(T.GOLD_S)
GI_MAIN, GI_SHADE, GI_LINE = 0xa3, 0xa4, 0xa5               # LoG2 indices for his gi's green, its shade and its outline (unused by teen.py)
EARRING = 0xbc                                              # the Potara earring (BF 29), a LoG2 index teen.py never uses
CMAP = {GI_MAIN: 215, GI_SHADE: 216, GI_LINE: 70, EARRING: 29}    # -> BF's (actors.json "cmap")
P_LIGHT, P_MAIN, P_SHADE, P_OUT = 0x63, 0xe1, 0xe8, 0xe5    # Gotenks's purples (LoG2 indices that map to BF 148, 147, 146, 138)
PURPLE = (P_LIGHT, P_MAIN, P_SHADE, P_OUT)
GI_GREY = {0x02: GI_MAIN, 0x09: GI_MAIN, 0x0a: GI_MAIN, 0x0b: GI_MAIN, 0x0c: GI_MAIN, 0x0d: GI_SHADE, 0x0e: GI_SHADE}   # his top's greys
SLEEVE = {0x02: 0x20, 0x09: 0x20, 0x0a: 0x20, 0x0b: 0x20, 0x0c: 0x21, 0x0d: 0x21, 0x0e: 0x22, 0x50: 0x20, 0x51: 0x21, 0xd3: 0x22}
SASH = {0x18: 0x20, 0x19: 0x20, 0x1a: 0x21, 0x1b: 0x22}                             # the sash's reds -> Goku's orange
VEE = {0x50: 0x21, 0x4f: 0x20, 0xd7: 0x23}                                          # Goku's navy V -> orange
BOOT = {0x02: 0x20, 0x09: 0x20, 0x0a: 0x20, 0x0b: 0x21, 0x0c: 0x21, 0x0d: 0x22, 0x0e: 0x22, B.DARK: 0x23}   # socks, shoes -> orange
GREENS = (GI_MAIN, GI_SHADE, GI_LINE)
ORANGES = (0x20, 0x21, 0x22, 0x23)
NAVY = (0x4f, 0x50, 0x51, 0xd7)
A, RIM, SIGMA = 70, 0.8, 3.5        # the crown: the outline faces within A degrees of up; the rest: smoothed head (sigma) under RIM
# Vegito's hair (BF colours, darkest first: 25 its outline, 30 its lights) in each look
V_HAIR = (25, 26, 27, 28, 30)
V_EAR = 29
LOOK_HAIR = {'purple': {30: P_LIGHT, 28: P_MAIN, 27: P_MAIN, 26: P_SHADE, 25: P_OUT},
             'black': {30: 0x0f, 28: 0x01, 27: 0x01, 26: 0x01, 25: 0x01},
             'ss2': {30: 0x2c, 28: 0x24, 27: 0x25, 26: 0x26, 25: 0x26}}
LOOK_HAIR['ss'] = LOOK_HAIR['ss2']          # (17:42, the owner: "Make the SSJ1 hair color cleaner and the same as SSJ2 Trunkten")
V_SKIN = {200: 0x72, 201: 0x73, 203: 0x74, 202: 0x15, 16: 0x17}       # Vegito's skin -> the model's (light to dark, the outline)
VEGITO_ACTOR = 275
V_EYES = {0: (-11, 56), 2: (-10, 52)}       # Vegito's eyes in his stance (BF canvas: row from the origin, column)
M_EYES = {0: (-9, 56), 2: (-9, 54)}         # the model's (teen.py's canvas)
BACK = (2, 0)                               # from behind: as from the front (the two games' heads stand alike)
EARS = {0: ((-8, 50), (-8, 62)), 1: ((-8, 49), (-8, 61)), 2: ((-8, 61),), 3: ((-8, 95 - 61),)}     # under the model's ears (stance)
NECK = -7                                   # Vegito's head: his rows above BF's row -7 (his collar)

_bf = None
def use_bf(rom):
    """The clean Buu's Fury ROM Vegito's frames are read from (build.py's `clean`; else baserom.gba)."""
    global _bf
    _bf = rom


def bf_frame(actor, slot, f, d):
    """A BF frame as the game shows it (flips applied) on a 96 x 96 canvas, its origin at (48, 48)."""
    from wfz import decompress_stream
    global _bf
    if _bf is None: _bf = open('baserom.gba', 'rb').read()
    rom = _bf; u = lambda o: struct.unpack_from('<I', rom, o)[0]; base = 0x08000000
    rec = u(0x6B6BD8 + 4 * actor) - base; a = u(rec + 0x54 + 4 * slot) - base
    o = u(a + 4 + 16 * f + 4 * d) - base; c = np.zeros((96, 96), np.uint8)
    for j in range(u(o)):
        p = o + 8 + 12 * j; x, y, w, h = struct.unpack_from('<bbBB', rom, p); t = u(p + 8) - base
        raw = rom[t + 8:t + 8 + u(t + 4)] if u(t) == 0 else bytes(decompress_stream(rom, t + 8, u(t + 4))[0])
        img = np.frombuffer(bytes(raw[:w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
        a1 = struct.unpack_from('<H', rom, p + 6)[0]
        if a1 & 0x1000: img = img[:, ::-1]
        if a1 & 0x2000: img = img[::-1]
        m = img > 0; c[48 + y:48 + y + h, 48 + x:48 + x + w][m] = img[m]
    return c


def moved(m, dy, dx):
    """m moved by (dy, dx), what leaves the canvas dropped."""
    out = np.zeros_like(m); h, w = m.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def split_hair(hair, head):
    """The black part of hair (a head's): where the head's outline, smoothed, faces more than A degrees from up and the smoothed head
    is under RIM (near that outline)."""
    g = ndimage.gaussian_filter(head.astype(float), SIGMA)
    gy, gx = np.gradient(g)
    ang = np.degrees(np.arctan2(np.abs(gx), gy))           # (the outward normal is minus the gradient: up where gy > 0)
    return hair & (ang > A) & (g < RIM)


_vh = {}
def vegito_head(i):
    """Vegito's stance head for the model's stance head i (0 front, 1 back, 2 side, 3 the side turned round), on teen.py's canvas where
    it lies on the model's face: -> (its BF colour indices, the black part of its hair for base)."""
    if i not in _vh:
        d = 2 if i == 3 else i
        c = bf_frame(VEGITO_ACTOR, 0, 0, d)
        c[48 + NECK:] = 0; c[c == V_EAR] = 0
        if d == 1: dy, dx = T.OY - 48 + BACK[0], BACK[1]
        else: (vy, vx), (my, mx) = V_EYES[d], M_EYES[d]; dy, dx = (my + T.OY) - (vy + 48), mx - vx
        v = moved(c, dy, dx)
        if i == 3: v = v[:, ::-1].copy()
        _vh[i] = (v, split_hair(np.isin(v, V_HAIR), v != 0))
    return _vh[i]


def src_head(k, d, f, done):
    """The Super Saiyan head teen.py put on frame (k, d, f), as its source frame draws it (nothing of his body over it): -> (that
    frame, its head), or None where the frame has no head of teen.py's."""
    B.head_mask('ss', k, d, f, done)
    got = B._notes[('ss', k, d, f)]
    if got is None or got[1].get('plain'): return None
    n = got[1]; src = n['s']
    rect = T.head_rect(n['a'], src) if GOLD[src].any() else n['rect']
    return src, T.head_of(src) & T.box_of(done.shape, rect, 1, 1) & (src != 0)


def eyes_of(src, sh):
    return ndimage.label(sh & F.cls({0x40, 0x41})[src], np.ones((3, 3)))[1]


_idle = None
def idle_heads():
    """The model's stance heads (front, back, side, and the side turned round): -> [(head, eyes)]."""
    global _idle
    if _idle is None:
        _idle = []
        for d in range(3):
            src, sh = src_head(0, d, 0, B.teen_frame('base', 0, d, 0))
            _idle.append((sh, eyes_of(src, sh)))
            if d == 2: _idle.append((sh[:, ::-1].copy(), eyes_of(src, sh)))
    return _idle


_where = {}
def where(k, d, f, done):
    """Which stance head the frame's head is and where: the one with as many eyes (where it shows any) that has the most pixels in
    common with it, moved up to 8 pixels. -> (i, dy, dx), or None (no head of teen.py's: knocked down)."""
    if (k, d, f) not in _where:
        got = src_head(k, d, f, done)
        if got is None: _where[k, d, f] = None
        else:
            src, sh = got; ne = eyes_of(src, sh); best = None
            for i, (ish, ie) in enumerate(idle_heads()):
                if ne and ie != ne: continue
                for dy in range(-8, 9):
                    for dx in range(-8, 9):
                        m = moved(ish, dy, dx); score = (m & sh).sum() / float((m | sh).sum())
                        if best is None or score > best[0]: best = (score, i, dy, dx)
            _where[k, d, f] = best[1:]
    return _where[k, d, f]


def head(form, k, d, f):
    """The model's Super Saiyan frame (k, d, f) with Vegito's hair in the look's colours and the Potara earrings: -> (frame, the model's
    hair taken off, Vegito's hair put on, the earrings)."""
    p = B.parts('ss', k, d, f); done, hm = p['done'], p['head']
    none = np.zeros(done.shape, bool)
    at = where(k, d, f, done) if hm.any() else None
    if at is None: return done.copy(), none, none, none
    i, dy, dx = at
    v, blk = vegito_head(i); v = moved(v, dy, dx); blk = moved(blk, dy, dx)
    gold = hm & GOLD[done]; white = hm & (done == 0x02)
    old = gold | (hm & (done == 0x14)) | F.flood(white & F.grown(gold, 1), white, True)
    out = done.copy(); out[old] = 0
    free = out == 0
    hair = np.isin(v, V_HAIR) & free
    for a, b in V_SKIN.items(): out[(v == a) & old & ~hair] = b
    for a in V_HAIR:
        m = hair & (v == a)
        if form == 'base': out[m & ~blk] = LOOK_HAIR['purple'][a]; out[m & blk] = LOOK_HAIR['black'][a]
        else: out[m] = LOOK_HAIR[form][a]
    if form == 'base': out[hm & (done == 0x40)] = 0x01; out[hm & (done == 0x41)] = 0x0f
    if form == 'ss2': out[hm & (done == 0x40)] = 0x31; out[hm & (done == 0x41)] = 0x32
    fill_holes(out, old)
    hair = hair | (old & np.isin(out, HAIR_OUT[form]))         # (a hole filled from his hair is his hair)
    # (what the model's hair alone held to him: a speck of his hand's outline beside it, left in the air: goes, never a white mark)
    lab, n = ndimage.label(out != 0, np.ones((3, 3)))
    if n > 1:
        big = 1 + int(np.argmax(ndimage.sum(out != 0, lab, range(1, n + 1))))
        for j in range(1, n + 1):
            m = lab == j
            if j != big and m.sum() <= 3 and (F.grown(m, 1) & old).any() and not (out[m] == 0x02).any(): out[m] = 0; old |= m
    # (no taller than one 32 x 32 piece: the tips of his hair above it go, their new top his hair's outline)
    ys = np.nonzero((out != 0).any(1))[0]
    if ys.max() - ys.min() >= 32:
        top = ys.max() - 31
        if (out[:top] != 0).any() and not hair[:top][out[:top] != 0].all(): raise T.Off('Trunkten %s, animation %d view %d frame %d: over 32 rows, not by his hair alone' % (form, k, d, f))
        cut = hair & (np.arange(out.shape[0])[:, None] < top)
        edge = hair & ~cut & F.shift(cut, 0, 1)
        out[cut] = 0; hair &= ~cut
        if form == 'base': out[edge & ~blk] = LOOK_HAIR['purple'][25]; out[edge & blk] = LOOK_HAIR['black'][25]
        else: out[edge] = LOOK_HAIR[form][25]
    ear = np.zeros(done.shape, bool)
    for y, x in EARS[i]: ear[y + T.OY, x] = True
    face = SKIN[out] | np.isin(out, (0x15, 0x16, 0x17))
    ear = moved(ear, dy, dx) & (out == 0) & F.grown(face, 1)       # (not where his hair or a hand is, nor off his face)
    out[ear] = EARRING
    return out, old, hair, ear


def fill_holes(out, old):
    """Where the model's hair went and nothing came, closed in by the figure (his fringe over his face where Vegito's ends higher, a
    lock between his hair and his ear): the colour most of its neighbours have, from the edge in. In place."""
    lab, n = ndimage.label(out == 0)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    hole = old & (out == 0) & ~np.isin(lab, border)
    while hole.any():
        got = False
        for y, x in zip(*np.nonzero(hole)):
            nb = out[y - 1:y + 2, x - 1:x + 2][~hole[y - 1:y + 2, x - 1:x + 2]]
            nb = nb[nb != 0]
            if len(nb):
                vals, cnt = np.unique(nb, return_counts=True)
                out[y, x] = vals[np.argmax(cnt)]; hole[y, x] = False; got = True
        if not got: break


def sleeves(top, hm, at):
    """His undershirt's sleeves: the top two rows of his gi's top in each column (top), outside his neck: 4 columns or more either side
    of the middle of his head's lowest rows from the front or behind, 3 or more behind it from the side (his shoulder; at: where())."""
    ys, xs = np.nonzero(hm)
    nx = xs[ys >= ys.max() - 1].mean()
    first = np.where(top.any(0), top.argmax(0), 999)
    Y, X = np.indices(top.shape)
    near = top & (Y - first[None, :] <= 1)
    i = at[0] if at else 0
    if i in (0, 1): return near & (np.abs(X - nx) >= 4)
    return near & ((X - nx >= 3) if i == 2 else (nx - X >= 3))


def wristbands(done):
    """The pieces of red (4-connected) that touch his skin and not his trousers: his wristbands. The rest is his sash."""
    reds = np.isin(done, B.REDS)
    lab, n = ndimage.label(reds)
    out = np.zeros(reds.shape, bool)
    skin = SKIN[done] | np.isin(done, (0x15, 0x16, 0x17))
    for i in range(1, n + 1):
        m = lab == i; ring = F.grown(m, 1) & ~m
        if (ring & skin).any() and not (ring & np.isin(done, (0x50, 0x51))).any(): out |= m
    return out


def make(form, k, d, f):
    """Frame (k, d, f) of the look ('base', 'ss', 'ss2') on teen.py's canvas, in LoG2 colour indices (CMAP's included)."""
    p = B.parts('ss', k, d, f)
    done, shirt, boots, upper, lower, legs, body = (p[n] for n in ('done', 'shirt', 'boots', 'upper', 'lower', 'legs', 'body'))
    c = head(form, k, d, f)[0]
    out = c.copy()
    for a, b in GI_GREY.items(): out[shirt & (done == a)] = b
    for a, b in BOOT.items(): out[boots & (done == a)] = b
    reds = np.isin(done, B.REDS); wb = wristbands(done)
    for a, b in B.RED_TO.items(): out[wb & (done == a)] = b
    for a, b in SASH.items(): out[reds & ~wb & (done == a)] = b
    out[body & (done == 0x50)] = GI_MAIN
    out[body & (done == 0x51)] = GI_SHADE
    out[body & (done == B.EDGE)] = GI_LINE                  # (the gi's edges: its outline)
    if p['head'].any():                                     # (his undershirt's sleeves at his shoulders)
        top = (shirt | (np.isin(done, (B.EDGE, 0x50, 0x51)) & upper & ~legs)) & body
        sl = sleeves(top, p['head'], where(k, d, f, done))
        for a, b in SLEEVE.items(): out[sl & (done == a)] = b
    for y, x, col in B.vee(done, shirt, p['head']): out[y, x] = VEE[col]
    return out


GI_OUT = GREENS + ORANGES + NAVY
HAIR_OUT = {'base': PURPLE + (0x01, 0x0f), 'ss': tuple(LOOK_HAIR['ss'].values()), 'ss2': tuple(LOOK_HAIR['ss2'].values())}


def problems(form, k, d, f, out):
    """What is wrong with a made frame, against the model's frame with Vegito's hair (head()): his outline changed but for the hair; a
    pixel that isn't his clothes changed; any of the model's gold or its brown outline left on his head, or a hole where it was (air
    the figure closes round); Vegito's hair in other than the look's colours, or over his face; an earring not under an ear (touching
    his skin or its outline); the purple gi's colours left on him (its reds and navy edge, a grey of its against his new colours:
    clothing missed); a red that became anything but the sash's orange or a wristband's navy, a wristband not on his hand; a shoe's
    darkest grey made anything but navy beside his boots; his eyes not the look's."""
    p = B.parts('ss', k, d, f); done, hm = p['done'], p['head']
    ref, old, hair, ear = head(form, k, d, f)
    bad = []
    o = ((out != 0) != (ref != 0))
    if o.any(): bad.append('outline changed %d' % o.sum())
    o = ((ref != 0) != (done != 0)) & ~(old | hair | ear | (np.isin(ref, tuple(V_SKIN.values())) & old))
    if o.any(): bad.append('outline changed outside the hair %d' % o.sum())
    cloth = np.isin(done, list(B.CLOTH)) & ~old
    dark = (done == B.DARK) & ~hm
    x = dark & (out != done) & ((out != BOOT[B.DARK]) | ~F.grown(np.isin(out, ORANGES + (0x01,)) & ~dark, 1))
    if x.any(): bad.append('dark grey made something else %d' % x.sum())
    cloth |= dark & (out == BOOT[B.DARK])
    x = (out != ref) & ~cloth
    if x.any(): bad.append('non-clothes changed %d' % x.sum())
    if hm.any() and (old.any() or hair.any()):
        x = (GOLD[out] | (hm & (out == 0x14))) & ~hair
        if x.any(): bad.append("the model's hair left %d" % x.sum())
        lab, n = ndimage.label(out == 0)
        border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
        x = old & (out == 0) & ~np.isin(lab, list(border))
        if x.any(): bad.append('a hole where his hair was %d' % x.sum())
        x = hair & ~np.isin(out, HAIR_OUT[form])
        if x.any(): bad.append("Vegito's hair in other colours %d" % x.sum())
        x = hair & (done != 0) & ~old
        if x.any(): bad.append("Vegito's hair over his face or body %d" % x.sum())
        face = SKIN[out] | np.isin(out, (0x15, 0x16, 0x17))
        lab, n = ndimage.label(ear, np.ones((3, 3)))
        for i in range(1, n + 1):
            if not (F.grown(lab == i, 1) & face).any(): bad.append('an earring off his ear'); break
        eyes = {'base': (0x01, 0x0f), 'ss': (0x40, 0x41), 'ss2': (0x31, 0x32)}[form]
        x = hm & np.isin(done, (0x40, 0x41)) & ~np.isin(out, eyes)
        if x.any(): bad.append('eyes not the look\'s %d' % x.sum())
    gi_out = np.isin(out, GI_OUT)
    lab, nn = ndimage.label(np.isin(out, B.GREYS + (B.DARK,)) & ~hm, np.ones((3, 3)))
    left = np.zeros(out.shape, bool)
    for i in range(1, nn + 1):
        m = lab == i; ring = F.grown(m, 1) & ~m
        white = (out[m] == B.WHITE).all() and (m.sum() >= 3 or (ring & GOLD[out]).any())
        if not white and (ring & (out != 0)).sum() >= 0.5 * ring.sum() and (ring & gi_out).any(): left |= m
        if not (out[m] == B.WHITE).any() and (ring & gi_out).any(): left |= m
    left |= ~hm & (np.isin(out, B.REDS + (B.EDGE,)) | ((done == 0x01) & (out != 0x01) & ~old))
    left |= p['body'] & np.isin(done, (0x50, 0x51)) & ~np.isin(out, GREENS + ORANGES + NAVY)
    if left.any(): bad.append('purple gi colours left %d' % left.sum())
    reds = np.isin(done, B.REDS)
    x = reds & ~np.isin(out, tuple(SASH.values()) + tuple(B.RED_TO.values()))
    if x.any(): bad.append('a red made something else %d' % x.sum())
    wb = reds & np.isin(out, tuple(B.RED_TO.values()))
    skin = SKIN[done] | np.isin(done, (0x15, 0x16, 0x17))
    lab, nn = ndimage.label(wb)
    for i in range(1, nn + 1):
        if not (F.grown(lab == i, 1) & skin).any(): bad.append('a wristband off his hand'); break
    return bad


LOOKS = ('base', 'ss', 'ss2')
_made = {}
def frame(form, k, d, f):
    """Frame (k, view d, f) of the look, made and checked: -> its canvas. Off if it fails a check."""
    if (form, k, d, f) not in _made:
        out = make(form, k, d, f); bad = problems(form, k, d, f, out)
        if bad: raise T.Off('Trunkten, %s, animation %d view %d frame %d: %s' % (form, k, d, f, '; '.join(bad)))
        _made[form, k, d, f] = out
    return _made[form, k, d, f]


def anims(form): return B.anims('ss')


def every():
    """Every frame the build uses of the three looks, made and checked (and cut to the purple record's 32 x 32 piece, as the build
    cuts it). -> how many; Off on the first that isn't right."""
    n = 0
    for form in LOOKS:
        for k in anims(form):
            for d in range(T.views(k)):
                for f in range(T.L.nframes(T.REC['P'], k)):
                    T.cut(frame(form, k, d, f), T.L.raw(T.REC['P'], k, d, f)[:4]); n += 1
    return n


def made(form):
    """sprites.log2_anim's frame source for the look's figure (teen.made, with this look's frames)."""
    return T.made('ss2' if form == 'ss2' else 'ss', canvas=lambda k, d, f: frame(form, k, d, f), anims=anims(form))
