"""Adult Gotenks: GT Goten and GT Trunks's fusion (Nov 12, 22:09, the owner, with two pictures from Dragon Ball Heroes: "Idea here would be to
base it on the Gohan black suit outfit from BF, then overlay Gotenks head and each SSJ form, vest, and then recolor to fit. I would say do
a sword and non-sword variant but if you do a sword one make the attacks actually functional to go along with their specific outfit.
Make this separate from the other Gotenks too where it's only possible to use them for those two chars, and build a portrait too from
Mystic Gohan or whatever Gohan combined with Gotenks in the cleanest possible way").
22:46, after the first try: "Both glitched bad. Possibly use Mystic Gohans head as a base as an option too and try both Gotenks hair and
Gohans hair recolored in Gotenks colors on top of the style with Gotenks head we started with so 3 total. Don't allow any invisible stuff
no clipping no stray pixels no backwards head body missing limbs wrong colors missing vest missing hair wrong face etc etc".

Nov 13, 08:16: "V2 but the vest/outfit/portraits need a lot of work"; 08:51, the pictures again (three, from Dragon Ball Heroes and a
fan's drawing of him), then "You can do the white pants like kid gotenks honestly but do the top black with the vest". The pictures: the
Metamoran vest, black, its thick padded collar yellow and big on his shoulders; a dark undershirt in its open front; bare arms; brown
leather gloves; a teal sash; baggy white trousers; tall brown boots; Gotenks's hair (black with lavender at the sides) on an adult's face.

The body: Buu's Fury's Mystic Gohan (actor 101, his orange gi: twenty slots) in the outfit (`outfit_parts`, `dress`): his top (the gi on
his head's side of the sash) the black vest, its first two rows from its top edge (round the back of his neck and over his shoulders, not
in front of his neck, where it is open) Gotenks's yellow padding, a roll lit from above; the dark Gohan wore under it the undershirt;
the gi past the sash Kid Gotenks's white trousers (in shadow, Gohan's dark there, his greys); the shoes and the trousers' ends round them
brown boots; the belt the teal sash; the wristbands and the hands past them brown gloves. Three heads (VARIANTS; the owner took 'hair'):
- 'head': Gotenks's own head (actor 117 base, 120 Super Saiyan, 121 Super Saiyan 3) in place of Gohan's, collar on collar.
- 'hair': Gohan's face with Gotenks's hair in place of his.
- 'recolour': Gohan's own head, his hair in Gotenks's colours (black, lavender where Gotenks's is; gold as a Super Saiyan, with Gotenks's
  hair's shading), and as a Super Saiyan 3 Gotenks's long hair behind his own.
Where Gohan's head is: his standing heads (front, back, side, the side mirrored), each matched to the frame's head turned the way the
frame's view has it (HEAD_KIND for the frames whose head turns another way: read off every frame). Every colour is one the game has."""
import struct
import numpy as np
from scipy import ndimage

BASE = 0x08000000
CH, CW = 56, 96                 # the canvas: the sprite's origin at row 48, column 48 (pieces sit at origin + their offset - 8)
OUT = (slice(0, CH), slice(16, 80))      # what goes to the build: 64 columns, bottom-centred on the origin as sprites.Inserter takes it
GOHAN = 101
GOTENKS = {'base': 117, 'ssj': 120, 'ssj3': 121}
VARIANTS = ('head', 'hair', 'recolour', 'grown')

# Gohan's colours (actor 101)
GI = (63, 64, 65, 79, 4)                # (4: the symbol on Goku's gi, in his change's frames)
BLUE = (157, 159, 161, 165)            # (165: the belt's light in Goku's change, which his is drawn from)
SHOES = (77, 80, 81, 206, 248)          # (206 shades his hands too: a shoe is a piece of these that touches no skin)
SKIN = (200, 201, 202, 203, 205)
LINE = 16                               # skin's outline
HAIR = (1, 111, 112)
EYES = (2, 113, 117)
MOUTH = (31, 32, 33)
HEADC = HAIR + SKIN + (LINE,) + EYES + MOUTH

# the outfit (every colour the game's own: the greys of Gotenks's vest, his vest's yellows, teal, brown leather)
SUIT = {79: 111, 63: 112, 64: 113, 65: 114, 4: 112}
PAD = {79: 243, 63: 243, 64: 27, 65: 250, 4: 243}
SASH = {157: 187, 159: 189, 161: 74}
GUARD = {157: 208, 159: 210, 161: 209}
WRAP = {206: 243, 248: 250, 80: 27, 81: 250, 77: 243}
PAD_ROWS = {0: 2, 1: 2, 2: 1, 3: 1}     # rows of padding from the top of his top, by the way his head faces

# Gotenks's hair colours
PURPLE = (138, 146, 147, 148)
GOLD_LINE, LAV_LINE = 202, 138
SSJ_EYES = {113: 215}                   # the iris; the pupil under it (black) -> 216


def cells(rom, actor_list, actor):
    """{slot: [[canvas per frame] for views 0 front, 1 back, 2 side]} of a retail actor."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    rec = u(actor_list + 4 * actor) - BASE; out = {}
    for slot in range(u(rec) & 0xFF):
        a = u(rec + 0x54 + 4 * slot)
        if not a: continue
        a -= BASE; views = [[], [], []]
        for k in range(u(a)):
            for d in range(3):
                fp = u(a + 4 + 16 * k + 4 * d) - BASE; c = np.zeros((CH, CW), np.uint8)
                for j in range(u(fp)):
                    x, y, w, h = struct.unpack_from('<bbBB', rom, fp + 8 + 12 * j); tp = u(fp + 16 + 12 * j) - BASE
                    t, size = u(tp), u(tp + 4)
                    raw = rom[tp + 8:tp + 8 + size] if t == 0 else bytes(decompress_stream(rom, tp + 8, size)[0])
                    img = np.frombuffer(bytes(raw[:w * h]).ljust(w * h, b'\0'), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
                    Y, X = 48 + y - 8, CW // 2 + x - 8
                    m = img > 0; sub = c[Y:Y + h, X:X + w]; mm = m[:sub.shape[0], :sub.shape[1]]
                    sub[mm] = img[:sub.shape[0], :sub.shape[1]][mm]
                views[d].append(c)
        out[slot] = views
    return out


def _lab(m, conn=8):
    return ndimage.label(m, np.ones((3, 3)) if conn == 8 else None)


def collar_row(c, clothes):
    rows = np.nonzero(np.isin(c, clothes).sum(1) >= 2)[0]
    return int(rows.min())


# ---- where Gohan's head is ----------------------------------------------------------------------------------------------------------
U = 72; UO = 24                         # the parts' canvas: Gohan's standing head's top left at (UO, UO)


def gohan_heads(g):
    """{kind: (template, its top left in the standing frame)}: 0 front, 1 back, 2 side (facing left), 3 side facing right."""
    out = {}
    cr = collar_row(g[0][0][0], GI)
    for v in (0, 1, 2):
        c = g[0][v][0]; m = np.zeros(c.shape, bool); m[:cr] = c[:cr] > 0
        lab, k = _lab(m); big = lab == (np.argmax(ndimage.sum(m, lab, range(1, k + 1))) + 1)
        ys, xs = np.nonzero(big)
        out[v] = (np.where(big, c, 0)[ys.min():ys.max() + 1, xs.min():xs.max() + 1], (int(ys.min()), int(xs.min())))
    return out


def on_u(img, at, ty, tx, dy=0, dx=0):
    """An idle frame's pixels (img, from the canvas) onto the parts' canvas, Gohan's standing head (top left ty, tx) at (UO, UO)."""
    u = np.zeros((U, U), np.uint8)
    ys, xs = np.nonzero(img)
    Y, X = ys + dy - ty + UO, xs + dx - tx + UO
    ok = (Y >= 0) & (Y < U) & (X >= 0) & (X < U)
    u[Y[ok], X[ok]] = img[ys[ok], xs[ok]]
    return u


def turn(u, kind, rot):
    """A parts canvas as for a head of `kind` (3: the side's mirrored) turned `rot` quarter turns (counter-clockwise)."""
    return np.rot90(u[:, ::-1] if kind == 3 else u, rot)


def match(c, t, near=None):
    """Best place of template t on frame c: -> (share of t's pixels equal, top, left). near: a mask the template must touch."""
    H, W = c.shape; th, tw = t.shape; ink = np.argwhere(t > 0); total = len(ink)
    P = np.zeros((H + 2 * th, W + 2 * tw), np.uint8); P[th:th + H, tw:tw + W] = c
    acc = np.zeros((H + th, W + tw), np.int32)
    for y, x in ink: acc += P[y:y + H + th, x:x + W + tw] == t[y, x]
    if near is not None:                    # (acc[j] is the template with its top left at j - (th, tw): it covers a pixel y when j0 is y+1..y+th)
        ok = np.zeros_like(acc, bool); ys, xs = np.nonzero(near)
        for y, x in zip(ys, xs): ok[y + 1:y + th + 1, x + 1:x + tw + 1] = True
        acc = np.where(ok, acc, -1)
    j = np.unravel_index(acc.argmax(), acc.shape)
    return acc[j] / total, int(j[0] - th), int(j[1] - tw)


def thick_hair(c, near=None):
    """Gohan's hair: the thick black (each pixel with 6+ of its 3 x 3 in the hair's colours), its biggest piece and the pieces by it,
    with the black edge round them. near: where it may be (round his head)."""
    m = np.isin(c, HAIR)
    core = m & (ndimage.convolve(m.astype(int), np.ones((3, 3), int), mode='constant') >= 6)
    if near is not None: core &= near
    lab, k = _lab(core)
    if not k: return core
    sizes = ndimage.sum(core, lab, range(1, k + 1)); big = int(np.argmax(sizes)) + 1
    keep = lab == big; grown = ndimage.binary_dilation(keep, np.ones((5, 5), bool))
    for i in range(1, k + 1):
        if i != big and sizes[i - 1] >= 4 and (grown & (lab == i)).any(): keep |= lab == i
    # then out along his thin locks: hair-coloured pixels joined to it, a step at a time, never one by his clothes (a collar's black edge)
    # or his eyes (the brows), and never off round his head
    beside = lambda cols: ndimage.binary_dilation(np.isin(c, cols), None)
    side = lambda cols: (lambda e: np.pad(e, 1)[1:-1, :-2] | np.pad(e, 1)[1:-1, 2:])(np.isin(c, cols))       # left or right of one
    ok = m & ~beside(GI + BLUE + SHOES) & ~ndimage.binary_dilation(c == 2, np.ones((3, 3), bool)) & ~side((113, 117))   # (brows, pupils)
    if near is not None: ok &= near
    hair = keep.copy()
    for _ in range(4):
        grow = ndimage.binary_dilation(hair, np.ones((3, 3), bool)) & ok & ~hair
        if not grow.any(): break
        hair |= grow
    edge = ndimage.binary_dilation(keep, np.ones((3, 3), bool)) & m
    if near is not None: edge &= near
    return hair | edge


# Heads that face another way than the frame's view, by the frame where the picture first comes (slot.frame.view; the same picture in
# other places goes with it): kind (0 front, 1 back, 2 side facing left, 3 facing right), quarter turns. A head turned three quarters
# gets the front one (the standing rule). Read off a sheet of every frame, Nov 12.
HEAD_KIND = {
    '3.0.0': (0, 0), '4.0.0': (0, 0), '4.2.0': (0, 0), '6.2.0': (2, 0), '8.0.0': (0, 0), '9.1.0': (0, 0), '9.1.2': (2, 3),
    '16.0.0': (0, 0), '16.1.0': (0, 0), '16.2.0': (0, 0), '16.3.0': (0, 0), '16.0.1': (1, 1), '16.1.1': (1, 1), '16.2.1': (1, 1),
    '17.0.0': (2, 0), '17.1.0': (2, 0), '17.2.0': (2, 0), '17.3.0': (2, 0), '18.0.0': (0, 0), '19.0.0': (0, 0), '19.1.0': (0, 0),
    '19.0.1': (1, 0),
}
# Frames whose head the matcher can't place (arms raised round it, thrown back): its top left by hand, and boxes (y0, y1, x0, x1, inclusive)
# of what is his arms there, never cleared.
HEAD_AT = {}
PROTECT = {}
WIDE_HAIR = {'9.1.2'}                    # his hair streams far behind his head (thrown back by a hit): all of his thick black is his hair


class Gohan:
    def __init__(self, rom, actor_list):
        self.g = cells(rom, actor_list, GOHAN)
        self.heads = gohan_heads(self.g)
        h, (ty, tx) = self.heads[2]
        W = self.g[0][2][0].shape[1]
        self.heads[3] = (h[:, ::-1].copy(), (ty, W - 1 - (tx + h.shape[1] - 1)))
        self.ut = {k: on_u(self._tpl_img(k), None, *self.heads[k][1]) for k in (0, 1, 2)}
        self.ut[3] = self.ut[2]                          # (turn() mirrors kind 3)
        self.first = {}; self.info = {}
        for s in sorted(self.g):
            for d in range(3):
                for j, c in enumerate(self.g[s][d]):
                    key = '%d.%d.%d' % (s, j, d)
                    self.first.setdefault(c.tobytes(), key)

    def _tpl_img(self, k):
        t, (ty, tx) = self.heads[k]
        img = np.zeros((CH, CW), np.uint8); img[ty:ty + t.shape[0], tx:tx + t.shape[1]] = t
        return img

    def head(self, c, view):
        """-> (kind, rot, top, left, score, key): where the frame's head is (the turned template's top left). A frame not of his (the
        change's canvases) gets a key of its own and the head its view has."""
        key = self.first.get(c.tobytes())
        if key is None:
            key = self.first[c.tobytes()] = 'x%d.0.%d' % (len(self.first), view)
        if key in self.info: return self.info[key]
        d = int(key.split('.')[2])
        kind, rot = HEAD_KIND.get(key, (d, 0))
        t = np.rot90(self.heads[kind][0], rot)
        if key in HEAD_AT:
            y, x = HEAD_AT[key]; score = 1.0
        else:
            near = ndimage.binary_dilation(thick_hair(c), np.ones((3, 3), bool))
            score, y, x = match(c, t, near if near.any() else None)
        self.info[key] = (kind, rot, y, x, score, key)
        return self.info[key]

    def place(self, u, kind, rot, y, x):
        """A parts canvas (u, as self.ut) turned and put on the frame: -> canvas (CH x CW)."""
        rt = turn(self.ut[kind], kind, rot); ys, xs = np.nonzero(rt); ry, rx = ys.min(), xs.min()
        ru = turn(u, kind, rot)
        out = np.zeros((CH, CW), np.uint8)
        ys, xs = np.nonzero(ru)
        Y, X = ys - ry + y, xs - rx + x
        ok = (Y >= 0) & (Y < CH) & (X >= 0) & (X < CW)
        out[Y[ok], X[ok]] = ru[ys[ok], xs[ok]]
        return out


# ---- Gotenks's head and hair --------------------------------------------------------------------------------------------------------
VEST = (243, 27, 250)
FACE_C = (200, 201, 202, 203, LINE, 2, 113, 117, 215, 216)


class Gotenks:
    """His head (to the collar) and his hair (the head less his face) on the parts' canvas of each of Gohan's head kinds, collar on
    collar: front and back his neck's middle on Gohan's, the side his neck's middle on Gohan's neck's."""
    def __init__(self, rom, actor_list, gohan):
        self.k = {f: cells(rom, actor_list, a) for f, a in GOTENKS.items()}
        base = self.k['base']; G = gohan.g
        self.parts = {}
        for v in (0, 1, 2):
            b = base[0][v][0]
            cg = collar_row(b, VEST); ch_ = collar_row(G[0][v][0], GI)
            neck_g = np.nonzero(np.isin(b[cg - 1], FACE_C))[0]; neck_h = np.nonzero(np.isin(G[0][v][0][ch_ - 1], FACE_C + HAIR))[0]
            dy = ch_ - cg
            dx = int(round((neck_h.min() + neck_h.max()) / 2 - (neck_g.min() + neck_g.max()) / 2)) if len(neck_g) and len(neck_h) else 0
            head117 = np.zeros(b.shape, bool); head117[:cg] = b[:cg] > 0
            lab, n = _lab(head117); head117 = lab == (np.argmax(ndimage.sum(head117, lab, range(1, n + 1))) + 1)
            # his face: the skin and eyes joined to his eyes' whites, its holes (pupils, a lock over the brow) filled
            fc = head117 & np.isin(b, FACE_C)
            lab, n = _lab(fc, 4)
            ids = set(np.unique(lab[(b == 2) & fc]).tolist()) - {0}
            if v == 1: ids = set()
            face = np.isin(lab, list(ids)) if ids else np.zeros_like(fc)
            face = ndimage.binary_fill_holes(face) & head117
            ty, tx = gohan.heads[v][1]
            for f, frames in self.k.items():
                c = frames[0][v][0]
                head = head117 | ((c != b) & (c > 0) & ~face)          # (Super Saiyan 3's hair down his back and sides)
                if f != 'base':                                        # (the new hair joined to the head, never his body)
                    lab, n = _lab(head); keep = np.isin(lab, list(set(np.unique(lab[head117]).tolist()) - {0})); head = keep
                hd = np.where(head, c, 0); hr = np.where(head & ~face & (np.arange(CH)[:, None] < cg) | (head & ~head117), c, 0)
                self.parts[(f, v)] = (on_u(hd, None, ty, tx, dy, dx), on_u(hr, None, ty, tx, dy, dx), on_u(np.where(face, c, 0), None, ty, tx, dy, dx),
                                      cg + dy - ty + UO)
        for f in self.k:
            self.parts[(f, 3)] = self.parts[(f, 2)]
        self.tiles = {}
        for n, (a, v, y0, y1, x0, x1) in TILES.items():
            img = self.k['ssj3' if a == 121 else 'base'][0][v][0][y0:y1, x0:x1]
            assert img.all(), n
            self.tiles[n] = img.copy()

    def head(self, form, kind): return self.parts[(form, kind)][0]
    def hair(self, form, kind): return self.parts[(form, kind)][1]


# ---- the outfit --------------------------------------------------------------------------------------------------------------------
UP = {0: (-1, 0), 1: (0, -1), 2: (1, 0), 3: (0, 1)}      # quarter turns -> the head's "up" as (dy, dx) on the canvas


def _runs(m):
    """Each pixel of m: the longest run of m through it, across or down."""
    out = np.zeros(m.shape, int)
    for axis in (0, 1):
        a = m if axis == 0 else m.T
        r = np.zeros(a.shape, int)
        for x in range(a.shape[1]):
            y = 0
            while y < a.shape[0]:
                if a[y, x]:
                    e = y
                    while e < a.shape[0] and a[e, x]: e += 1
                    r[y:e, x] = e - y; y = e
                else: y += 1
        out = np.maximum(out, r if axis == 0 else r.T)
    return out


def _depth(m, rot):
    """For each pixel of m: how many pixels of m lie above it, unbroken, counted towards his head (rot: the head's quarter turns)."""
    a = np.rot90(m, -rot)
    d = np.zeros(a.shape, int)
    for y in range(1, a.shape[0]): d[y] = np.where(a[y] & a[y - 1], d[y - 1] + 1, 0)
    return np.rot90(d, rot)


def _side(m, rot):
    """Pixels beside m across his body (left or right of it, his head up)."""
    a = np.rot90(m, -rot); b = np.zeros_like(a); b[:, 1:] |= a[:, :-1]; b[:, :-1] |= a[:, 1:]
    return np.rot90(b, rot)


def outfit_parts(src, kind, rot, headmask):
    """Where each part of the outfit goes on a frame of Gohan's (src): {name: mask}. The pictures (the owner, Nov 13, with three of them,
    and "do the white pants like kid gotenks honestly but do the top black with the vest"): a black vest whose thick padded collar runs
    round his neck, down both edges of its open front and over his shoulders, yellow; a dark undershirt in its opening; bare arms; brown
    leather gloves; a teal sash; Kid Gotenks's white trousers; brown boots."""
    gi = np.isin(src, GI); blue = np.isin(src, BLUE); skin = np.isin(src, SKIN)
    k3 = np.ones((3, 3), bool)
    near_head = ndimage.binary_dilation(headmask, k3)
    # the sash and the wristbands: a sash pixel lies in a run of 3+ blue across or down, by his gi
    belt = blue & (_runs(blue) >= 3) & ndimage.binary_dilation(gi, k3)
    blab, bn = _lab(belt)
    for i in range(1, bn + 1):                                  # (a wristband by a stray pixel of gi is still a wristband)
        m = blab == i
        if (ndimage.binary_dilation(m, k3) & gi).sum() < 4: belt &= ~m
    guard = blue & ~belt
    # his top and his trousers: the pieces of gi on his head's side of the sash, and the rest. Down his body is from his head to his sash
    # where both are (a frame's head may be turned another way than his body: spinning, falling), else the way his head's up says
    Y, X = np.mgrid[:src.shape[0], :src.shape[1]]
    if belt.sum() >= 3 and headmask.any():
        hy, hx = np.argwhere(headmask).mean(0); by, bx = np.argwhere(belt).mean(0)
        vy, vx = by - hy, bx - hx; nv = np.hypot(vy, vx) or 1.0
        along = (Y - hy) * vy / nv + (X - hx) * vx / nv
        rot = (0 if vy > 0 else 2) if abs(vy) >= abs(vx) else (1 if vx > 0 else 3)
    else:
        dy, dx = UP[rot]
        along = -(Y * dy + X * dx).astype(float)                # grows down his body, away from his head
    dist = ndimage.distance_transform_edt(~headmask) if headmask.any() else np.full(src.shape, 99.0)
    level = np.median(along[belt]) if belt.any() else None
    lab, n = _lab(gi); top = np.zeros_like(gi)
    for i in range(1, n + 1):
        m = lab == i
        if dist[m].min() > 3: continue                          # (a leg, an arm's sleeve end: never his top)
        if headmask.any() and along[m].mean() <= along[headmask].mean(): continue    # (his legs seen behind his head, flying at us)
        if level is None or along[m].max() <= level: top |= m
        else: top |= m & (along < level)
    pants = gi & ~top
    # his shoulders: Gohan's short dark sleeves (the dark by his arms' skin, above his sash): the vest's padding sits on them, so it shows
    # whatever his arms do (crossed over his chest, swinging)
    dark = np.isin(src, (1, 111, 112)) & ~near_head
    armskin = skin & ~near_head
    upper = (along < level) if level is not None else (dist <= 8)
    sleeve = dark & ndimage.binary_dilation(armskin, k3) & upper
    slab_, sn_ = _lab(dark & upper)
    sleeve = np.isin(slab_, list(set(np.unique(slab_[sleeve]).tolist()) - {0})) if sn_ else sleeve     # (the whole of each)
    # his undershirt: the dark of Gohan's that his top's gi is round (the open front), and the chest his open gi showed (skin with his top
    # each side of it in its row, near)
    under = dark & ~sleeve & (ndimage.convolve(top.astype(int), np.ones((3, 3), int), mode='constant') >= 2)
    ns_, nt = np.rot90(armskin, -rot), np.rot90(top, -rot)
    chest_n = np.zeros_like(ns_)
    for yy in range(ns_.shape[0]):
        tx = np.nonzero(nt[yy])[0]
        if len(tx) < 2: continue
        for xx in np.nonzero(ns_[yy])[0]:
            lft = tx[tx < xx]; rgt = tx[tx > xx]
            if len(lft) and len(rgt) and xx - lft.max() <= 6 and rgt.min() - xx <= 6: chest_n[yy, xx] = True
    under |= np.rot90(chest_n, rot) & upper
    torso = top | under | sleeve
    # the padded collar: the torso's first two pixels down from its edge towards his head, over his shoulders and round the back of his
    # neck, and his shoulders; in front of his neck the vest is open (from the front its middle, from the side the part before his
    # neck): black there
    first = torso & (_depth(torso, rot) < 2)
    ns = np.rot90(src, -rot).shape                                       # across his body, his head up: the column there
    nx = np.rot90(np.tile(np.arange(ns[1]), (ns[0], 1)), rot)
    open_ = np.zeros_like(top)
    if kind != 1 and headmask.any():
        mid = nx[headmask].mean()
        if kind == 0: open_ = np.abs(nx - mid) <= 2.0
        else:                                    # from the side: the front edge of his torso, row by row (the view faces left, its mirror right)
            nt_ = np.rot90(top | under, -rot); on = np.zeros_like(nt_)
            for yy in range(nt_.shape[0]):
                xs_ = np.nonzero(nt_[yy])[0]
                if len(xs_): on[yy, xs_.min() if kind == 2 else xs_.max()] = True
            open_ = np.rot90(on, rot)
    # the pads sit on his shoulders only (the pictures: black between them): from the front the top's first rows 3 or more pixels out
    # from his neck's middle, from the side its first row; from behind the collar's whole width
    if kind == 0 and headmask.any(): first &= np.abs(nx - nx[headmask].mean()) >= 3.0
    elif kind in (2, 3): first &= _depth(torso, rot) < 1
    pad = (first & ~open_) | sleeve | (top & ndimage.binary_dilation(sleeve, k3) & ~open_ & (_depth(torso, rot) < 3))
    # boots: the shoes' pieces that touch no skin (206 shades his hands too) and his trousers' ends round them
    sh = np.isin(src, SHOES); slab, sn = _lab(sh); shoe = np.zeros_like(sh)
    for i in range(1, sn + 1):
        m = slab == i
        if not (ndimage.binary_dilation(m, k3) & skin).any(): shoe |= m
    foot_dark = np.isin(src, (1, 111, 112)) & ndimage.binary_dilation(shoe, k3) & ~near_head & ~torso
    boot = shoe | (pants & (ndimage.distance_transform_edt(~shoe) <= 1.5)) | foot_dark
    # gloves: his hands, the skin past each wristband (a piece of skin cut off by it that touches neither his top nor his head)
    hand = np.zeros_like(skin)
    if guard.any():
        arm = (skin | (src == LINE)) & ~near_head
        alab, an = _lab(arm & ~guard, 4)
        for i in range(1, an + 1):
            m = alab == i
            if not (ndimage.binary_dilation(m, k3) & guard).any(): continue
            if (ndimage.binary_dilation(m, k3) & (torso | near_head)).any(): continue
            if m.sum() > 14: continue
            hand |= m
    # his trousers in shadow (seen from above or behind, Gohan's drew them dark): the dark joined to them on the far side of the sash
    shade = np.zeros_like(gi)
    if level is not None:
        cand = np.isin(src, (1, 111, 112)) & ~near_head & ~torso & ~boot & (along > level)
        clab, cn = _lab(cand | (pants & ~boot))
        for i in range(1, cn + 1):
            m = clab == i
            if (m & pants).any(): shade |= m & cand
        legs = pants | shade
        if shade.any() and legs.any():                          # (their dark ends are his boots' soles: from behind, spinning)
            tip = shade & (along >= along[legs].max() - 2.5)
            boot |= tip; shade &= ~tip
    return dict(top=top & ~pad, under=under & ~pad, pad=pad & ~boot, pants=pants & ~boot, shade=shade, boot=boot, belt=belt, guard=guard, hand=hand,
                depth=_depth(torso, rot), rot=rot)


# the outfit's colours, every one the game's own
VEST_C = {79: 1, 63: 1, 64: 111, 65: 112, 4: 111, 1: 1, 111: 1, 112: 111}
UNDER_C = {1: 112, 111: 112, 112: 113, 79: 112, 63: 112, 64: 113, 65: 113}
PANTS_C = {79: 114, 63: 117, 64: 119, 65: 2, 4: 119}           # Kid Gotenks's white trousers (his own greys)
PANTS_EDGE = 112
BOOT_C = {79: 77, 63: 80, 64: 81, 65: 206, 4: 81, 248: 206, 206: 81, 80: 80, 81: 81, 77: 77, 1: 77, 111: 77, 112: 80, 16: 77}
SASH_C = {157: 187, 159: 189, 161: 189}
GLOVE_C = {157: 208, 159: 210, 161: 209, 200: 209, 201: 210, 202: 208, 203: 210, 205: 208, 16: 77}
PAD_EDGE, PAD_MID, PAD_LIGHT = 243, 27, 250


def dress(c, src, kind, rot, headmask):
    """Gohan's gi into the outfit (c is changed; src is the frame before any head was changed)."""
    # (Goku's change, which his is drawn from, lights his gi with the shoes' orange: pieces of it inside the gi are the gi's light)
    src = src.copy(); k3 = np.ones((3, 3), bool); gi = np.isin(src, GI)
    lab, n = _lab(src == 248)
    for i in range(1, n + 1):
        m = lab == i; ring = ndimage.binary_dilation(m, k3) & ~m
        if (ring & gi).sum() * 2 > ring.sum(): src[m] = 65
    src[src == 165] = 161
    p = outfit_parts(src, kind, rot, headmask)
    paint = lambda m, table: [c.__setitem__(m & (src == k), v) for k, v in table.items()]
    paint(p['top'], VEST_C); paint(p['under'], UNDER_C)
    paint(p['pants'], PANTS_C); paint(p['shade'], {1: 112, 111: 114, 112: 115})
    edge = p['pants'] & ndimage.binary_dilation(src == 0, None) & (src == 79)
    c[edge] = PANTS_EDGE
    paint(p['boot'], BOOT_C)
    paint(p['belt'], SASH_C); paint(p['guard'], GLOVE_C); paint(p['hand'], GLOVE_C)
    # the padding: Gotenks's yellows, its outer edge the dark one, inside light where Gohan's gi caught the light
    # the padding: Gotenks's yellows, a roll lit from above: its first row light, its second the yellow, its ends (by nothing, across his
    # body) the dark one
    pad = p['pad']
    c[pad] = PAD_MID
    c[pad & (p['depth'] == 0)] = PAD_LIGHT
    below = np.rot90(np.pad(np.rot90(pad, -p['rot']), ((0, 1), (0, 0)))[1:], p['rot'])      # (the next pixel down his body is pad)
    c[pad & ~below & (p['depth'] >= 2)] = PAD_EDGE
    return c


# ---- the three heads ---------------------------------------------------------------------------------------------------------------
def _nearest(values_mask, img):
    """For every pixel, the colour of the nearest pixel of values_mask in img, and how far it is."""
    d, (iy, ix) = ndimage.distance_transform_edt(~values_mask, return_indices=True)
    return img[iy, ix], d


# Patches of the inside of Gotenks's own hair (from behind: no face in them), laid over Gohan's hair as a texture that moves with his head
TILES = {'gold': (121, 1, 28, 34, 40, 56), 'lavender': (117, 1, 27, 31, 43, 52)}      # actor, view, rows y0..y1-1, columns x0..x1-1


def texture(out, where, tile, at, line, clear):
    """Gohan's hair (`where`) in a patch of Gotenks's hair repeated from `at` (his head's top left), its edge by empty pixels the hair's
    outline colour."""
    th, tw = tile.shape
    ys, xs = np.nonzero(where)
    out[ys, xs] = tile[(ys - at[0]) % th, (xs - at[1]) % tw]
    edge = where & ndimage.binary_dilation(clear, None)
    out[edge] = line
    return out


def ssj_eyes(c, area):
    out = c.copy()
    iris = (c == 113) & area
    w = c == 2
    nb = lambda m: np.pad(m, 1)[1:-1, :-2] | np.pad(m, 1)[1:-1, 2:]          # a pixel left or right
    iris &= nb(w) | np.pad(w, 1)[:-2, 1:-1] | np.pad(w, 1)[2:, 1:-1]
    out[iris] = 215
    pupil = (c == 1) & area & nb(w) & np.pad(iris, 1)[:-2, 1:-1]
    out[pupil] = 216
    brow = (c == 1) & area & nb((c == 117)) & ~pupil              # (his brows by the eyes' tops: gold, as Super Saiyan Gohan's)
    out[brow] = GOLD_LINE
    return out


def _enclosed(m):
    """Empty pixels the outside can't reach (holes in the figure)."""
    lab, n = ndimage.label(~m)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    return ~m & ~np.isin(lab, list(edge))


def finish(out, src):
    """No holes and no strays where the new head met the old: a hole the frame didn't have is filled (Gohan's own dark there if it was his
    hair's, else the nearest colour of what is round it); a piece of a few pixels cut off from the figure that was part of a bigger one
    (a lock of Gohan's hair past the new head) goes."""
    for _ in range(4):
        h = _enclosed(out > 0) & ~_enclosed(src > 0)
        if not h.any(): break
        keep = h & np.isin(src, HAIR); out[keep] = src[keep]
        h &= ~keep
        if h.any():
            col, _ = _nearest(out > 0, out); out[h] = col[h]
    lab, n = _lab(out > 0); slab, _ = _lab(src > 0)
    if n > 1:
        sizes = ndimage.sum(out > 0, lab, range(1, n + 1)); big = int(np.argmax(sizes)) + 1
        for i in range(1, n + 1):
            if i == big or sizes[i - 1] > 6: continue
            m = lab == i
            ids = np.unique(slab[m]); whole = len(ids) == 1 and ids[0] and (slab == ids[0]).sum() == m.sum() and (out[m] == src[m]).all()
            if not whole: out[m] = 0
    return out


def build_frame(gh, gt, c, view, form, variant):
    """One frame of Adult Gotenks: -> (canvas, notes)."""
    if not c.any(): return c.copy(), {}
    kind, rot, y, x, score, key = gh.head(c, view)
    foot = gh.place(gh.ut[kind], kind, rot, y, x) > 0
    near = ndimage.binary_dilation(foot, np.ones((9, 9), bool))
    hair = thick_hair(c, None if key in WIDE_HAIR else near)
    protect = np.zeros(c.shape, bool)
    for (y0, y1, x0, x1) in PROTECT.get(key, ()): protect[y0:y1 + 1, x0:x1 + 1] = True
    out = c.copy()
    if variant == 'head':
        ring = ndimage.binary_dilation(foot, np.ones((3, 3), bool))
        erase = (foot & np.isin(c, HEADC)) | (ring & np.isin(c, HAIR) & ndimage.binary_dilation(foot & np.isin(c, HAIR), np.ones((3, 3), bool))) | hair
        erase &= ~protect
        out[erase] = 0
        dress(out, c, kind, rot, foot)
        new = gh.place(gt.head(form, kind), kind, rot, y, x)
        over = np.zeros(c.shape, bool)
        if kind == 1 and form == 'ssj3':                     # his hair down his back: over it
            low = gh.place(np.pad(np.ones((U - gt.parts[(form, kind)][3], U), np.uint8), ((gt.parts[(form, kind)][3], 0), (0, 0))), kind, rot, y, x) > 0
            over = low
        put = (new > 0) & ((out == 0) | over)
        out[put] = new[put]
        finish(out, c)
        return out, {'key': key, 'kind': kind, 'rot': rot, 'score': score, 'left': int((erase & (out == 0)).sum())}
    if variant == 'hair':
        out[hair & ~protect] = 0
        dress(out, c, kind, rot, foot)
        new = gh.place(gt.hair(form, kind), kind, rot, y, x)
        put = (new > 0) & (out == 0)
        out[put] = new[put]
        # what of Gohan's hair Gotenks's doesn't cover is left empty, but for what that would leave a hole in him (his locks over his brow):
        # that is hair, black as Gotenks's fringe, or a Super Saiyan's gold
        holes = hair & _enclosed(out > 0) & ~_enclosed(c > 0)
        if holes.any():
            if form == 'base': out[holes] = 1
            else: texture(out, holes, gt.tiles['gold'], (y, x), GOLD_LINE, np.isin(out, SKIN + (LINE,) + EYES) & ~holes)
        if form != 'base': out = ssj_eyes(out, foot)
        finish(out, c)
        return out, {'key': key, 'kind': kind, 'rot': rot, 'score': score}
    # recolour: his own hair in Gotenks's colours: lavender where the nearest of Gotenks's hair (laid on his head) is, as a Super Saiyan gold
    dress(out, c, kind, rot, foot)
    ref = gh.place(gt.hair(form if form != 'ssj3' else 'ssj', kind), kind, rot, y, x)
    if form == 'base':
        cls_col, _ = _nearest(ref > 0, ref)
        lav = hair & np.isin(cls_col, PURPLE)
        lv = out.copy(); texture(lv, hair, gt.tiles['lavender'], (y, x), LAV_LINE, ((out == 0) | np.isin(out, SKIN + (LINE,) + EYES)) & ~hair)   # (the edge only where his hair's is)
        out[lav] = lv[lav]
    else:
        texture(out, hair, gt.tiles['gold'], (y, x), GOLD_LINE, ((out == 0) | np.isin(out, SKIN + (LINE,) + EYES)) & ~hair)
        out = ssj_eyes(out, foot)
        if form == 'ssj3':                                   # the long hair behind his own
            mane = gh.place(gt.hair('ssj3', kind), kind, rot, y, x)
            over = np.zeros(c.shape, bool)
            if kind == 1:
                over = gh.place(np.pad(np.ones((U - gt.parts[('ssj3', kind)][3], U), np.uint8), ((gt.parts[('ssj3', kind)][3], 0), (0, 0))), kind, rot, y, x) > 0
            put = (mane > 0) & ((out == 0) | (over & ~hair))
            out[put] = mane[put]
            finish(out, c)
    return out, {'key': key, 'kind': kind, 'rot': rot, 'score': score}


# Slots Gohan's gi hasn't (it never changes form): stand-ins (10, the change of form: the power-up's arms raised; 11, an outfit's
# change: his stance)
STAND_IN = {10: 13, 11: 0}


def problems(gh, frames, notes):
    """The checks every frame must pass (the owner, 22:46: "Don't allow any invisible stuff no clipping no stray pixels ... wrong colors"):
    no gi or blue left, no new hole in the figure, no new piece of 4 pixels or less cut off from it. -> ['slot.frame.view: what', ...]"""
    out = []
    for key, n in notes.items():
        src = n.get('src')
        if src is None or not src.any(): continue
        s, j, d = map(int, key.split('.'))
        img = np.zeros((CH, CW), np.uint8); img[OUT] = frames[s][d][j]
        if np.isin(img, GI + BLUE).any(): out.append('%s: gi or blue left' % key)
        h = _enclosed(img > 0) & ~_enclosed(src > 0)
        if h.any(): out.append('%s: a hole of %d pixels' % (key, h.sum()))
        lab, k = _lab(img > 0); slab, _ = _lab(src > 0)
        for i in range(1, k + 1):
            m = lab == i
            if m.sum() > 4: continue
            ids = np.unique(slab[m])
            if not (len(ids) == 1 and ids[0] and (slab == ids[0]).sum() == m.sum() and (img[m] == src[m]).all()):
                out.append('%s: a stray piece of %d pixels' % (key, m.sum()))
    return out
ACTORS = {'base': 'adult_gotenks', 'ssj': 'adult_gotenks_ssj', 'ssj3': 'adult_gotenks_ssj3'}


def from_ssb(canvas):
    """A 32 x 64 canvas of lib/ssb.actor_frames (the origin at row 24, column 24) on this one."""
    c = np.zeros((CH, CW), np.uint8); c[16:48, 16:80] = canvas
    return c


def frames(rom, actor_list, form='base', variant='head', slots=None, gh=None, gt=None, change=None):
    """{slot: [front, back, side frame lists]} (64-column canvases for the build), notes per frame. change: his change of form (slot 10)
    as lib/ssb.actor_frames canvases [views 0, 1, 2] (build.mystic_change: Goku's change with Gohan's head, as Mystic Gohan's)."""
    gh = gh or Gohan(rom, actor_list); gt = gt or Gotenks(rom, actor_list, gh)
    out, notes = {}, {}
    if change is not None and (slots is None or 10 in slots):
        out[10] = [[None] * len(change[d]) for d in range(3)]
        for d in range(3):
            for j, cv in enumerate(change[d]):
                c = from_ssb(cv); img, n = build_frame(gh, gt, c, d, form, variant)
                out[10][d][j] = img[OUT]; notes['10.%d.%d' % (j, d)] = dict(n, src=c)
    for s, views in gh.g.items():
        if slots is not None and s not in slots: continue
        out[s] = [[None] * len(views[d]) for d in range(3)]
        for d in range(3):
            for j, c in enumerate(views[d]):
                img, n = build_frame(gh, gt, c, d, form, variant)
                out[s][d][j] = img[OUT]; notes['%d.%d.%d' % (s, j, d)] = dict(n, src=c)
    if slots is None:
        for s, src in STAND_IN.items():
            if s not in out and src in out: out[s] = out[src]
    return out, notes


# ---- the second attempt: Kid Gotenks grown (Nov 13, 09:40, the owner: "do a second attempt and literally just upscale gotenks to adult size
# and then give him the black sleeveless undershirt from Gohan and see if that's easier"). Gotenks's own frames (117, 120, 121, every slot,
# his own moves and ghost attacks), each with his head up: three rows more of body (one in his chest, one in his thighs, one in his shins,
# everything above each moved up, so his feet stay on the ground: 30 pixels tall to 33, Gohan 31) and one column wider below his collar
# (his body's middle doubled); his bare chest inside the vest the black undershirt (Gohan's black suit's black and greys, by the light
# that was there). His head stays Gotenks's.
GROWN = {'base': 117, 'ssj': 120, 'ssj3': 121}
G_YEL = (243, 27, 250, 242)
G_VEST = (112, 113, 115) + G_YEL
G_PANTS = (114, 117, 119)
G_SKIN = SKIN + (67,)                   # (67: his stomach's shading)
G_UNDER = {200: 113, 201: 112, 202: 111, 203: 112, 205: 111, 67: 112, 16: 1}


def _g_axis(c):
    y = np.isin(c, G_YEL); p = np.isin(c, G_PANTS)
    if y.sum() < 2 or p.sum() < 3: return 0
    vy, vx = np.argwhere(p).mean(0) - np.argwhere(y).mean(0)
    return (0 if vy > 0 else 2) if abs(vy) >= abs(vx) else (1 if vx > 0 else 3)


def _g_chest(n):
    """His bare chest in a frame with his head up: each piece of skin below his collar (split by its outline) that the vest bounds (a
    third or more of what is round it is the vest; arms and hands are bounded by their outline and the background), and the outline
    between two such pieces. Bare from his collar to his trousers' top."""
    yel = np.isin(n, G_YEL)
    out = np.zeros(n.shape, bool)
    if not yel.any(): return out
    collar = np.nonzero(yel.any(1))[0].min()
    rows = np.nonzero(np.isin(n, G_PANTS).sum(1) >= 2)[0]; rows = rows[rows > collar]
    stop = rows.min() if len(rows) else n.shape[0]
    band = np.zeros(n.shape, bool); band[collar + 1:stop] = True
    skin = np.isin(n, G_SKIN) & band
    vest = np.isin(n, G_VEST)
    lab, k = ndimage.label(skin)
    for i in range(1, k + 1):
        m = lab == i
        ring = ndimage.binary_dilation(m) & ~m
        if not ring.any(): continue
        if (ring & vest).sum() * 3 >= ring.sum(): out |= m
    if out.any():                       # (the outline between two pieces of his chest: his pecs' and stomach's lines)
        line = (n == LINE) & band
        both = ndimage.binary_dilation(out, np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0]], bool)) & ndimage.binary_dilation(out, np.array([[0, 0, 0], [0, 0, 1], [0, 0, 0]], bool))
        updown = ndimage.binary_dilation(out, np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], bool)) & ndimage.binary_dilation(out, np.array([[0, 0, 0], [0, 0, 0], [0, 1, 0]], bool))
        out |= line & (both | updown)
    return out


def _g_params(n):
    """Where a frame with his head up grows: (rows to double, from his collar row down; the first row and the column his widening starts
    from) or None."""
    yel = np.isin(n, G_YEL); ys = np.nonzero(n.any(1))[0]
    if not yel.any() or not len(ys): return None
    collar = np.nonzero(yel.any(1))[0].min(); L = ys.max() - collar
    if L < 6: return None
    rows = sorted([collar + max(2, int(round(0.3 * L))), collar + int(round(0.62 * L)), collar + int(round(0.85 * L))], reverse=True)
    c2 = collar                                         # (widened from his collar down: never his face)
    body = np.zeros(n.shape, bool); body[collar:] = n[collar:] > 0
    cx = int(np.round(np.argwhere(body)[:, 1].mean()))
    return rows, c2, cx


def _g_grow(n, prm):
    if prm is None: return n
    rows, c2, cx = prm
    out = n.copy()
    for r in rows:
        top = out[:r + 1].copy(); out[:r] = top[1:]; out[r] = top[r]
    res = out.copy(); res[c2:, :cx] = out[c2:, 1:cx + 1]; res[c2:, cx] = out[c2:, cx]
    return res


def grown(c, ref=None):
    """One of Gotenks's frames (the 56 x 96 canvas) grown, in the undershirt. ref: the same frame of base Gotenks (117), whose body his
    Super Saiyan ones share: where his chest is and how he grows are read off it (his Super Saiyan hair is drawn in skin's colours, and
    from behind his Super Saiyan 3 hair hides his collar)."""
    if not c.any(): return c.copy()
    ref = c if ref is None or not ref.any() else ref
    r = _g_axis(ref); n = np.rot90(c, -r); nr = np.rot90(ref, -r)
    chest = _g_chest(nr) & (n == nr)
    n = n.copy()
    for k, v in G_UNDER.items(): n[chest & (n == k)] = v
    return np.rot90(_g_grow(n, _g_params(nr)), r)


def grown_frames(rom, actor_list, form):
    """{slot: [front, back, side frame lists]} for the build (64-column canvases), from Gotenks's own (GROWN[form])."""
    g = cells(rom, actor_list, GROWN[form]); base = cells(rom, actor_list, GROWN['base'])
    def ref(s, d, j):
        return base[s][d][j] if s in base and len(base[s][d]) == len(g[s][d]) else None
    return {s: [[grown(c, ref(s, d, j))[OUT] for j, c in enumerate(g[s][d])] for d in range(3)] for s in g}


# ---- his portraits (the owner: "build a portrait too from Mystic Gohan or whatever Gohan combined with Gotenks in the cleanest possible
# way"; then three heads): 64 x 64 pictures in the portrait frame, the game's colours, one set per head (VARIANTS), each [calm, serious,
# shouting] for base and Super Saiyan and one for Super Saiyan 3.
# - 'head': Gotenks's own pictures, as they are (his sprite's head is Gotenks's): 69, 68, 70; 72, 71, 71; 73.
# - 'hair': Mystic Gohan's face (46 calm, 45 shouting; serious: 38, the black suit's (the outfit the owner named); Super Saiyan Gohan's 54,
#   51, 53) with Gotenks's hair from the same expression laid over his own hair and the background, never his face.
# - 'recolour': the same pictures, Gohan's own hair: black, lavender where Gotenks's is (its strokes from Gotenks's picture at the same
#   place); as a Super Saiyan his own gold. Super Saiyan 3: Gotenks's long hair behind.
# The Gohan ones in the outfit: Gotenks's background blue; Gotenks's padded collar (its rolls, from his picture of the same
# expression, at the same place, behind the face); what Gohan wears there black (the vest, by luminance into the suit's greys); the chest
# below the neck the black undershirt.
PORTRAIT_TABLE = 0x6F393C
P_SKIN = (16, 17, 18, 19, 20, 21, 23, 37, 67, 68, 82, 83, 84, 204, 205, 212, 213, 214)
P_HAIR = (1, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120)
P_LAV = (85, 86, 87, 88, 89, 90, 91, 137)
P_ROLL = (24, 25, 26, 29, 239)
P_BG = {5: 97, 27: 96, 28: 98, 7: 98, 74: 97, 73: 96, 96: 96, 97: 97, 98: 98, 87: 87, 88: 88, 35: 98, 247: 97, 210: 96}     # yellow, cyan -> Gotenks's blue
BG_OF = {38: (96, 97, 98), 41: (7, 73, 74), 45: (5, 27, 28), 46: (5, 27, 28), 51: (7, 73, 74), 53: (7, 73, 74, 35, 247, 210), 54: (7, 73, 74),
         68: (96, 97, 98), 69: (96, 97, 98), 70: (96, 97, 98), 71: (87, 88), 72: (87, 88), 73: (87, 88)}      # each picture's background
P_GOLD = (2, 26, 28, 29, 30, 110, 205, 208, 209, 239, 247, 248, 249)       # Super Saiyan Gotenks's hair
P_DARK = (1, 111, 112, 113, 114)
P_CLOTHES = (54, 55, 56, 57, 58, 59, 62, 63, 64, 65, 69, 70, 71, 79, 93, 169, 170)    # Gohan's gi, collars, Supreme Kai's clothes          # the vest and undershirt: black, its greys by the light on what was there
PICS = {'base': ((46, 69), (38, 68), (45, 70)), 'ssj': ((54, 72), (51, 71), (53, 71)), 'ssj3': ((54, 73),)}
GOTENKS_PICS = {'base': (69, 68, 70), 'ssj': (72, 71, 71), 'ssj3': (73,)}
ROLLS_FROM = {'base': (69, 68, 70), 'ssj': (72, 71, 71), 'ssj3': (73,)}
P_SSJ_EDGE = (1, 111, 112, 16, 17, 20, 21, 23, 78, 82, 101, 72, 87, 88, 85, 86)     # Super Saiyan Gohan's hair's lines and shades
NECK_HALF = 7
P_LINES = (208, 16, 17, 1)                # the outlines' colours in the pictures
G_SSJ_HAIR = P_GOLD + (78, 82, 85, 86, 87, 88, 21, 23, 1, 111)       # Super Saiyan Gohan's hair, its shades and lines


def portrait_art(rom, i):
    import wfz
    o = struct.unpack_from('<I', rom, PORTRAIT_TABLE + 4 * i)[0] - BASE
    kind, size = struct.unpack_from('<II', rom, o)
    raw = rom[o + 8:o + 8 + 4096] if kind == 0 else bytes(wfz.decompress_stream(rom, o + 8, 4096)[0])
    return np.frombuffer(bytes(raw), np.uint8).reshape(64, 64).copy()


class Portraits:
    def __init__(self, rom):
        self.rom = rom
        ids = sorted({p for v in PICS.values() for pr in v for p in pr} | {p for v in GOTENKS_PICS.values() for p in v})
        self.art = {i: portrait_art(rom, i) for i in ids}
        same = np.ones((64, 64), bool)
        for a in self.art.values(): same &= a == self.art[ids[0]]
        self.frame = same                                       # the gold frame: the same in every picture
        self.inner = ~same

    def bg(self, i, face=None):
        """Picture i's background: its colours, outside his face."""
        a = self.art[i]
        m = np.isin(a, BG_OF[i]) & self.inner
        return m & ~(self.face(a) if face is None else face)

    def face(self, a):
        """His face (the biggest piece of skin, with all inside it: eyes, mouth, brows) and his ears (skin by its sides, above its bottom)."""
        m = np.isin(a, P_SKIN) & self.inner
        lab, n = _lab(m, 4)
        sizes = ndimage.sum(m, lab, range(1, n + 1)); order = np.argsort(-sizes) + 1
        face = ndimage.binary_fill_holes(lab == order[0])
        ys, xs = np.nonzero(face)
        for k in order[1:6]:
            p = lab == k; py, px = np.nonzero(p)
            if p.sum() >= 12 and py.max() <= ys.max() - 4 and (px.max() < xs.min() + 4 or px.min() > xs.max() - 4) and \
               ndimage.binary_dilation(face, np.ones((5, 5), bool))[p].any():
                face |= ndimage.binary_fill_holes(p)
        return face

    def hair(self, a, colours):
        """Hair: pieces of its colours that touch the frame's top or sides (the picture's edge)."""
        m = np.isin(a, colours) & self.inner
        lab, n = _lab(m)
        edge = ndimage.binary_dilation(self.frame, None) & self.inner; edge[40:] = False
        ids = set(np.unique(lab[edge & m]).tolist()) - {0}
        return np.isin(lab, list(ids))

    def rolls(self, g):
        """Gotenks's padded collar in his picture g: its yellows' pieces in the lower part, with their outline."""
        a = self.art[g]
        m = np.isin(a, P_ROLL) & self.inner; m[:40] = False
        lab, n = _lab(m)
        keep = np.zeros_like(m)
        for i in range(1, n + 1):
            if (lab == i).sum() >= 8: keep |= lab == i
        keep = ndimage.binary_fill_holes(keep)
        ring = ndimage.binary_dilation(keep, np.ones((3, 3), bool)) & ~keep & np.isin(a, (1, 17, 208, 2, 18)) & self.inner
        return keep | ring

    def dress(self, a, i, g, face, hair, trim=False):
        """The outfit on a picture a (made from picture i; Gotenks's collar from his picture g; hair: where his hair is now) -> new
        picture. As the owner's pictures (Nov 13): his neck, then the dark undershirt and the black vest, the vest's thick yellow padded
        collar on his shoulders (Gotenks's own rolls, from his picture of the same expression, behind the face and hair); Gotenks's blue
        behind him."""
        out = a.copy()
        bg = self.bg(i, face) & (a == self.art[i])
        for k, v in P_BG.items(): out[bg & (a == k)] = v
        ys, xs = np.nonzero(face); jaw = ys.max(); cx = xs[ys >= jaw - 1].mean()
        Y, X = np.mgrid[:64, :64]
        body = self.inner & ~bg & ~face & ~hair & (Y >= jaw - 14)
        neck = body & np.isin(a, P_SKIN) & (np.abs(X - cx) <= NECK_HALF) & (Y <= jaw + 3)
        clothes = self.inner & ~face & ~hair & np.isin(a, P_CLOTHES)
        dark = (body & ~neck) | clothes
        if trim:                    # (his face's and ears' brown outline stays brown where no cloth is by it: only the shirt's edge is black)
            cloth = dark & ~np.isin(a, (208, 16, 17, 62))
            dark = cloth | (dark & ndimage.binary_dilation(cloth, np.ones((3, 3), bool)))
        lv = np.clip((pal_lum(a) / 255.0 * 4).astype(int), 0, 4)
        out[dark] = np.array(P_DARK)[lv[dark]]
        r = self.rolls(g); src = self.art[g]
        lab, n = _lab(r)
        for k in range(1, n + 1):
            m = lab == k
            if m.sum() < 20: continue
            put = m & ~face & ~hair & self.inner
            out[put] = src[put]
        return out

    def on_gotenks(self, gp, kp, form):
        """Gohan's face (picture gp) on Gotenks's picture kp (Nov 13, the owner on the first two tries: "the portrait hair and vest is
        still messed up"): Gotenks's own hair round it, his padded collar on his shoulders, his background; Gohan's face and ears (each row
        of his face from edge to edge) and his neck under his jaw; what was Gotenks's face that Gohan's doesn't cover the nearest of
        Gotenks's hair or background (under the chin the undershirt); below the jaw all but the collar and the background the dark
        undershirt, by the light that was there."""
        a = self.art[gp]; kart = self.art[kp]
        face = _rows_filled(self.face(a)); kface = _rows_filled(self.face(kart))
        Y, X = np.mgrid[:64, :64]
        ys, xs = np.nonzero(face); jaw = ys.max(); cx = xs[ys >= jaw - 1].mean()
        res = kart.copy()
        lv = np.clip((pal_lum(kart) / 255.0 * 4).astype(int), 0, 4)
        kskin = np.isin(kart, P_SKIN) & self.inner
        kbody = kskin & ~kface & (Y >= 40)
        res[kbody] = np.array(P_DARK)[lv[kbody]]
        khair = self.hair(kart, (P_HAIR + P_LAV) if form == 'base' else P_GOLD + (16, 17, 208, 1)) & ~kface
        col, _ = _nearest((khair | np.isin(kart, BG_OF[kp])) & self.inner & ~kface, kart)
        gap = kface & ~face
        res[gap] = col[gap]
        res[gap & (Y >= jaw - 4)] = 111
        below = self.inner & (Y >= jaw - 2) & ~self.rolls(kp) & ~np.isin(kart, BG_OF[kp]) & ~face
        res[below] = np.array(P_DARK)[np.minimum(lv[below], 2)]
        res[face] = a[face]
        if form != 'base': res[face & np.isin(a, (85, 86, 87, 88))] = LINE        # (Super Saiyan Gohan's purple hair lines: Gotenks's brown)
        res[face & (Y > jaw - 3) & ~np.isin(a, P_SKIN + (1,))] = 112                 # (his collar's light under his jaw)
        neck = np.isin(a, P_SKIN) & ~face & (np.abs(X - cx) <= NECK_HALF) & (Y > jaw - 6) & (Y <= jaw + 3) & self.inner
        res[neck] = a[neck]
        return res

    def older(self, kp, eye_cut=3, nose=3, chin=3, jaw=2):
        """Gotenks's picture kp with an older face (Nov 13, 09:58, the owner: "make the face in portrait look older not kid gotenks"): his
        eyes shorter (rows out of their middle), his face longer (rows doubled where it has nothing but skin, between his eyes and his
        mouth and between his mouth and his chin; what is above moves up, his collar stays), his jaw narrower (from below his eyes to his
        chin each cheek loses up to `jaw` pixels inside its outline, never the mouth)."""
        k = self.art[kp]; face = _rows_filled(self.face(k)); ys, xs = np.nonzero(face); chin_row = ys.max()
        skinish = np.isin(k, P_SKIN)
        def bands(rows):
            out = []
            for r in rows:
                if out and r == out[-1][1] + 1: out[-1][1] = r
                else: out.append([r, r])
            return out
        eye = bands([y for y in range(64) if (face[y] & (k[y] == 2)).sum() >= 2])[0]
        plain = lambda y: face[y].sum() > 0 and (face[y] & ~skinish).sum() <= 2
        feat = [y for y in range(eye[1] + 2, chin_row) if not plain(y)]
        mouth_bot = max(feat) if feat else eye[1] + 8
        cn = [y for y in range(eye[1] + 2, chin_row - 6) if plain(y)]
        cc = [y for y in range(mouth_bot + 1, chin_row - 1) if plain(y)]
        rows = list(range(64)); ops = []
        # (the eye rows that go: ones that are all white across his eyes, no pupil or iris in them: his lids come down)
        wc = {y: int((face[y] & (k[y] == 2)).sum()) for y in range(eye[0], eye[1] + 1)}
        full = [y for y in sorted(wc) if wc[y] >= 0.85 * max(wc.values()) and (face[y] & np.isin(k[y], (1, 113, 117, 215, 216, 73, 74, 75, 99, 100))).sum() <= 4]
        for y in full[:max(0, min(eye_cut, eye[1] - eye[0] + 1 - 5))]: ops.append((y, 'del', 1))     # (never under 5 rows)
        if cn: ops.append((cn[len(cn) // 2], 'dup', nose))
        if cc: ops.append((cc[0], 'dup', chin))
        for r, kind, nn in sorted(ops, reverse=True):
            i = rows.index(r)
            if kind == 'dup': rows[i:i] = [r] * nn
            else: del rows[i:i + nn]
        rows = rows[len(rows) - 64:] if len(rows) >= 64 else [rows[0]] * (64 - len(rows)) + rows
        out = k[rows, :]; out[self.frame] = k[self.frame]
        f2 = _rows_filled(self.face(out)); ys2, xs2 = np.nonzero(f2); chin2 = ys2.max()
        e2 = bands([y for y in range(64) if (f2[y] & (out[y] == 2)).sum() >= 2])[0]
        y0 = e2[1] + 3; cx = xs2[ys2 >= chin2 - 1].mean()
        res = out.copy()
        for y in range(y0, chin2 + 1):
            xs = np.nonzero(f2[y])[0]
            if len(xs) < 6: continue
            d = int(round(jaw * min(1.0, (y - y0) / max(1, (chin2 - y0) * 0.6))))
            if d <= 0: continue
            x0, x1 = xs.min(), xs.max(); c = int(round(cx))
            row = out[y].copy(); new = row.copy(); sk = np.isin(row, P_SKIN)
            ft = [x for x in range(x0 + 2, x1 - 1) if not sk[x]]
            lm = min(min([x for x in ft if x < c] or [c - 3]), c - 3); rm = max(max([x for x in ft if x > c] or [c + 3]), c + 3)
            if lm - x0 > d + 2:
                new[x0 + d:lm] = np.concatenate([row[x0:x0 + 1], row[x0 + 1 + d:lm]]); new[x0:x0 + d] = row[x0 - 1] if x0 > 0 else 0
            if x1 - rm > d + 2:
                new[rm + 1:x1 + 1 - d] = np.concatenate([row[rm + 1:x1 - d], row[x1:x1 + 1]]); new[x1 + 1 - d:x1 + 1] = row[x1 + 1] if x1 < 63 else 0
            res[y] = new
        res[self.frame] = k[self.frame]
        return res

    def gohan_face(self, gp, kp, form, rolls_from):
        """Gohan's own picture gp (his face, neck and proportions) with Gotenks's hair from his picture kp (Nov 13, 10:29, the owner:
        "portraits shit try again with Gohan face and gotenks hair"). Gohan's hair goes, all of it down to his brows (his fringe too);
        Gotenks's hair is laid on sized to Gohan's head: its rows above the eyes stretched from the picture's top to his eyes onto Gohan's
        top to his, below them as they are; its columns by the faces' widths at the eyes, middle on middle; never over Gohan's face below
        his brows. Where Gohan's hair was and Gotenks's isn't: his forehead (inside his face, below the hair in its column) skin, the rest
        the nearest of Gotenks's hair's inside colours, so the hair keeps Gohan's head's outline with no gaps. Then the outfit (`dress`)."""
        a = self.art[gp].copy(); kart = self.art[kp]
        Y, X = np.mgrid[:64, :64]
        gface = self.face(a); kface = self.face(kart)
        gspan = _rows_filled(gface); kspan = _rows_filled(kface)
        def eyes_top(img, sp):
            w = [y for y in range(64) if (sp[y] & (img[y] == 2)).sum() >= 2]
            return w[0] if w else None
        ge = eyes_top(a, gspan); ke = eyes_top(kart, kspan)
        brow = ge - 4
        if form == 'base':
            ghair = self.hair(a, P_HAIR) & ~(gface & (Y >= brow))
            khair = self.hair(kart, P_HAIR + P_LAV) & ~kface
        else:
            ghair = self.hair(a, P_GOLD + (78, 82, 85, 86, 87, 88, 21, 23, 1, 111)) & ~(gface & (Y >= brow))
            khair = self.hair(kart, P_GOLD + (208, 1)) & ~kface
            if form != 'ssj3': khair[46:] = False
        gh = ghair.copy(); gh[brow:] &= ~gspan[brow:]
        a[gh] = 97
        def span_at(sp, y):
            xs = np.nonzero(sp[y])[0]; return xs.min(), xs.max()
        gx0, gx1 = span_at(gspan, ge + 2); kx0, kx1 = span_at(kspan, ke + 2)
        gcx = (gx0 + gx1) / 2; kcx = (kx0 + kx1) / 2; sx = (kx1 - kx0) / max(1, gx1 - gx0)
        T = 4
        ysrc = np.where(Y < ge, T + (Y - T) * (ke - T) / max(1, ge - T), Y - (ge - ke))
        xsrc = kcx + (X - gcx) * sx
        yi = np.clip(np.round(ysrc).astype(int), 0, 63); xi = np.clip(np.round(xsrc).astype(int), 0, 63)
        put = khair[yi, xi] & self.inner & ~(gspan & (Y >= brow))
        a[put] = kart[yi, xi][put]
        left = gh & ~put
        lowest = np.full(64, -1)
        for x in range(64):
            ys_ = np.nonzero(put[:, x])[0]
            if len(ys_): lowest[x] = ys_.max()
        fore = left & gspan & (Y > lowest[None, :]) & (Y < brow + 1)
        col, _ = _nearest(np.isin(a, P_SKIN) & gspan & (Y >= brow) & (Y < ge + 6), a)
        a[fore] = col[fore]
        inside = put & ~np.isin(a, (16, 17, 208, 1, 111) if form != 'base' else (16,))
        hcol, _ = _nearest(inside if inside.any() else put, a)
        rest = left & ~fore
        a[rest] = hcol[rest]
        return self.dress(a, gp, rolls_from, gface, put | rest)

    def transplant(self, gp, kp, form, rolls_from):
        """Gohan's own picture gp from his brows down (his eyes, face, ears, neck), Gotenks's picture kp above them (his hair, his hairline,
        his forehead) and his side hair below them behind Gohan's face (Nov 13, 11:21, the owner on the last try: "Those portraits are
        awful do better"). Gotenks's skin in Gohan's (37 84, 214 67, 213 83, 212 19: the pictures' skins are pink and tan); his picture
        widened by the faces' widths at the eyes (columns doubled 7 out from his face's middle, each side) and moved so his brow line
        (4 rows above his eyes) is Gohan's and his face's middle Gohan's; his frame's edge filled with what is inside it. The same hair for
        every expression (Gotenks's serious picture's, his Super Saiyan serious one's; Super Saiyan 3 his own): it is all above the brows.
        Then the outfit (`dress`)."""
        g = self.art[gp]; k = self.art[kp].copy()
        for a_, b_ in ((37, 84), (214, 67), (213, 83), (212, 19)): k[k == a_] = b_
        col, _ = _nearest(self.inner, k); k[self.frame] = col[self.frame]
        Y, X = np.mgrid[:64, :64]
        gsp = _rows_filled(self.face(g)); ksp = _rows_filled(self.face(self.art[kp]))
        def eye_top(a, sp): return [y for y in range(64) if (sp[y] & (a[y] == 2)).sum() >= 2][0]
        def span(sp, y):
            xs = np.nonzero(sp[y])[0]; return int(xs.min()), int(xs.max())
        ge = eye_top(g, gsp); ke = eye_top(self.art[kp], ksp)
        sg, sk = ge - 4, ke - 4
        gx0, gx1 = span(gsp, ge + 1); kx0, kx1 = span(ksp, ke + 1)
        gcx, kcx = (gx0 + gx1) / 2, (kx0 + kx1) / 2
        n = max(0, (gx1 - gx0) - (kx1 - kx0)); l, r = n // 2, n - n // 2
        lc, rc, c = int(round(kcx - 7)), int(round(kcx + 7)), int(round(kcx))
        cols = list(range(0, lc + 1)) + [lc] * l + list(range(lc + 1, c + 1)) + list(range(c + 1, rc + 1)) + [rc] * r + list(range(rc + 1, 64))
        cols = cols[l:len(cols) - r]
        hairc = P_HAIR + P_LAV if form == 'base' else P_GOLD + (208, 1)
        kw = k[:, cols]; hw = self.hair(self.art[kp], hairc)[:, cols]
        dy, dx = sg - sk, int(round(gcx - kcx))
        ks = np.zeros_like(kw); hs = np.zeros(hw.shape, bool)
        ys, xs = np.nonzero(np.ones(kw.shape, bool)); Yy, Xx = ys + dy, xs + dx
        ok = (Yy >= 0) & (Yy < 64) & (Xx >= 0) & (Xx < 64)
        ks[Yy[ok], Xx[ok]] = kw[ys[ok], xs[ok]]; hs[Yy[ok], Xx[ok]] = hw[ys[ok], xs[ok]]
        out = g.copy()
        top = (Y < sg) & self.inner
        out[top] = ks[top]
        side = (Y >= sg) & hs & np.isin(g, BG_OF[gp]) & self.inner
        if form != 'ssj3': side &= Y < 50
        out[side] = ks[side]
        out[self.frame] = g[self.frame]
        hair_now = (self.hair(out, hairc) & (Y < sg + 2)) | side
        return self.dress(out, gp, rolls_from, self.face(g), hair_now)

    def blend(self, gp, kp, form, rolls_from):
        """Gohan's face (picture gp) under Gotenks's hair (picture kp) with no join to see (Nov 13, 12:03, the owner on `transplant`'s
        straight cut at the brow line: "you can literally see the line where the two are pasted together fucking do it right"). The
        pictures' faces are the same width and middle already (cheek to cheek 30 and 31 pixels), so Gotenks's picture is only moved: his
        brow line (4 rows above his eyes) onto Gohan's, his eyes' middle onto Gohan's; his skin in Gohan's colours.
        - Above the brow line the picture is Gotenks's (his hair, his hairline with its soft edge, his background), but his forehead is
          Gohan's own wherever Gohan's forehead shows clear of his hair (2 pixels clear: the hair's shadow goes with it), so the creases
          and light over Gohan's brows run on up unbroken; where it doesn't show it is Gotenks's forehead with its light taken off.
        - Gohan's brows are kept whole, above the line too: in his face from 7 rows above his eyes down, what is dark and is dark at the
          same place mirrored across his face (a pixel either way) is brow. Dark that isn't, hanging from his hair above, is a lock of it:
          gone, with its shadow each side, his nearest plain skin there.
        - Below the line the picture is Gohan's; Gotenks's side hair carries on down over Gohan's background and hair; Gohan's hair
          between his ears and his face is skin (base: Gotenks has none there), the rest of it background.
        Then the outfit (`dress`, the face's brown outline kept brown where no cloth is by it), and a fleck of shirt cut off from the
        rest (the tip of a collar Gohan wore) taken out."""
        g = self.art[gp]; kraw = self.art[kp]; k = kraw.copy()
        Y, X = np.mgrid[:64, :64]; K3 = np.ones((3, 3), bool)
        for a_, b_ in ((37, 84), (214, 67), (213, 83), (212, 19)): k[k == a_] = b_
        kbg = np.isin(kraw, BG_OF[kp]) & self.inner
        if form != 'base': k[kbg & (kraw == 87)] = 97; k[kbg & (kraw == 88)] = 98
        col, _ = _nearest(self.inner, k); k[self.frame] = col[self.frame]
        def main(a):
            m = np.isin(a, P_SKIN) & self.inner
            lab, n = _lab(m, 4); sizes = ndimage.sum(m, lab, range(1, n + 1))
            return ndimage.binary_fill_holes(lab == (int(np.argmax(sizes)) + 1))
        def eye_top(a, sp): return [y for y in range(64) if (sp[y] & (a[y] == 2)).sum() >= 2][0]
        def eye_mid(a, sp, e):
            xs = np.nonzero((a == 2) & sp & (Y >= e) & (Y < e + 8))[1]; return (xs.min() + xs.max()) / 2
        gface = self.face(g); kface = self.face(kraw)
        gsp = _rows_filled(gface); ksp = _rows_filled(kface)
        gm = _rows_filled(main(g)); km = _rows_filled(main(kraw))
        ge = eye_top(g, gsp); ke = eye_top(kraw, ksp); sg, sk = ge - 4, ke - 4
        gmid = eye_mid(g, gsp, ge)
        dy, dx = sg - sk, int(round(gmid - eye_mid(kraw, ksp, ke)))
        hairc = P_HAIR + P_LAV if form == 'base' else P_GOLD + (208, 1)
        yi = np.clip(Y - dy, 0, 63); xi = np.clip(X - dx, 0, 63)
        L = k[yi, xi]; LH = (self.hair(kraw, hairc) & ~kface)[yi, xi]; LS = (np.isin(k, P_SKIN) & km)[yi, xi]
        ghc = P_HAIR if form == 'base' else G_SSJ_HAIR
        dark_c = P_HAIR if form == 'base' else tuple(c for c in G_SSJ_HAIR if c not in (2, 21, 23, 82, 205))
        raw = self.hair(g, ghc)
        xs = np.nonzero(gm[ge + 2])[0]; m0, m1 = int(xs.min()), int(xs.max())            # (his cheeks)
        bt = ge - 7
        dark = np.isin(g, dark_c) & self.inner
        band = (Y >= bt) & (Y <= ge - 1) & (X > m0) & (X < m1)
        mx = np.clip(np.round(2 * gmid - X).astype(int), 0, 63)
        mir = dark[Y, mx] | dark[Y, np.clip(mx - 1, 0, 63)] | dark[Y, np.clip(mx + 1, 0, 63)]
        brow = dark & band & mir
        cand = dark & band & ~brow
        lab, _n = _lab(cand | (raw & (Y == bt - 1)))
        lock = np.isin(lab, list(set(np.unique(lab[bt - 1]).tolist()) - {0})) & cand
        GH = raw & ~((X >= m0) & (X <= m1) & (Y >= bt) & self.inner)
        clean = np.isin(g, P_SKIN) & gface & ~ndimage.binary_dilation(GH | lock, K3, iterations=2)
        above = (Y < sg) & self.inner; below = (Y >= sg) & self.inner
        Lf = L.copy(); Lf[LS & np.isin(L, (68, 120))] = 84
        out = g.copy()
        out[above] = Lf[above]
        keep = above & ((clean & LS & ~ndimage.binary_dilation(LH, K3, iterations=2)) | brow)
        out[keep] = g[keep]
        lk = lock & below
        if lk.any():
            sh = np.zeros_like(lk); sh[:, 1:] |= lk[:, :-1]; sh[:, :-1] |= lk[:, 1:]
            lk |= sh & np.isin(g, (17, 18, 19, 204)) & ~dark & below
            plain = np.isin(g, (83, 84, 67, 68)) & gface & ~lk & (Y >= sg - 2) & (Y <= ge + 1)
            scol, _ = _nearest(plain, g); out[lk] = scol[lk]
        gbg = np.isin(g, BG_OF[gp]) & self.inner
        ex = np.nonzero(gsp[sg:sg + 12].any(0))[0]; e0, e1 = int(ex.min()), int(ex.max())
        temple = below & GH & (X >= e0) & (X <= e1) & (Y < sg + 12)
        side = below & LH & (gbg | GH) & ~temple
        if form != 'ssj3': side &= Y < 50
        out[side] = L[side]
        rest = below & GH & ~side & ~temple
        if rest.any():
            bcol, _ = _nearest(gbg & ~GH, g)
            out[rest] = np.array([P_BG.get(int(v), int(v)) for v in bcol[rest]], np.uint8)
        if form == 'base' and temple.any():
            for x in np.nonzero(temple.any(0))[0]:
                up = out[sg - 1, x]
                out[temple[:, x], x] = up if up in (83, 84, 67, 19) else 83
        if form != 'base':                  # (Super Saiyan Gohan's hair's dark lines left by his ears: the brown of Gotenks's)
            out[below & np.isin(g, (85, 86, 87, 88)) & (out == g) & ~gbg] = 208
            out[temple & np.isin(g, (1, 111, 112))] = 208
        if form == 'ssj3':                  # (his mane is round his face: a sliver of background, 5 pixels or less across, left between
            hairm = side | temple           #  it and his face or ears is hair)
            solid = gsp | ndimage.binary_dilation(gsp, K3)
            isbg = below & np.isin(out, (96, 97, 98) + BG_OF[gp]) & ~solid & ~hairm
            fill = np.zeros_like(isbg)
            for y in range(sg, 50):
                x = 0
                while x < 64:
                    if isbg[y, x]:
                        e = x
                        while e < 64 and isbg[y, e]: e += 1
                        if e - x <= 5 and x >= 1 and e < 64 and ((hairm[y, x - 1] and solid[y, e]) or (solid[y, x - 1] and hairm[y, e])): fill[y, x:e] = True
                        x = e
                    else: x += 1
            if fill.any():
                inner_h = hairm & ~np.isin(out, (208, 16, 17, 1))
                fcol, _ = _nearest(inner_h if inner_h.any() else hairm, out); out[fill] = fcol[fill]; side = side | fill
        out[self.frame] = g[self.frame]
        hair_now = (LH & above) | side
        no = np.zeros_like(temple)
        res = self.dress(out, gp, rolls_from, gface | (temple if form == 'base' else no), hair_now | (temple if form != 'base' else no), trim=True)
        ch = (res != out) & np.isin(res, P_DARK)
        lab, nc = _lab(ch)
        if nc > 1:
            sizes = ndimage.sum(ch, lab, range(1, nc + 1))
            for i in range(1, nc + 1):
                if sizes[i - 1] > 14: continue
                m = lab == i
                line = m & np.isin(out, (208, 16, 17, 62)); res[line] = out[line]
                m &= ~line
                if m.any():
                    okc = self.inner & ~ch & ~np.isin(res, P_SKIN + (208, 16, 17, 62, 1, 2)) & ~gface
                    ncol, _ = _nearest(okc, res); res[m] = ncol[m]
        return res

    # ---- Gotenks's own picture with Gohan's head set in it (Nov 13, 13:15: the pictures in use) ----
    def _main(self, a):
        """His face without his ears: the biggest piece of skin, its holes filled."""
        m = np.isin(a, P_SKIN) & self.inner
        lab, n = _lab(m, 4); sizes = ndimage.sum(m, lab, range(1, n + 1))
        return ndimage.binary_fill_holes(lab == (int(np.argmax(sizes)) + 1))

    def _eyes(self, a, sp):
        """(the first row of his eyes' whites, the column midway between his eyes)."""
        Y = np.mgrid[:64, :64][0]
        top = [y for y in range(64) if (sp[y] & (a[y] == 2)).sum() >= 2][0]
        xs = np.nonzero((a == 2) & sp & (Y >= top) & (Y < top + 8))[1]
        return top, (xs.min() + xs.max()) / 2

    def rolls_whole(self, kp, top=30):
        """Gotenks's padded collar in his picture kp, to its leaves' tips (`rolls` starts at row 40 and cuts them flat)."""
        a = self.art[kp]; ksp = _rows_filled(self.face(a)); K3 = np.ones((3, 3), bool)
        m = np.isin(a, P_ROLL) & self.inner & ~ksp; m[:top] = False
        lab, n = _lab(m); keep = np.zeros_like(m)
        for i in range(1, n + 1):
            c = lab == i
            if c.sum() >= 8 and np.nonzero(c)[0].max() >= 40: keep |= c
        keep = ndimage.binary_fill_holes(keep)
        return keep | (ndimage.binary_dilation(keep, K3) & ~keep & np.isin(a, (1, 17, 208, 2, 18)) & self.inner & ~ksp)

    def gohan_clean(self, gp):
        """Gohan's picture gp with what of his hair hangs in his face taken out -> (picture, what was found), in his picture's own place.
        His brows are kept whole. Black-haired: in his face from 7 rows above his eyes down, what is dark and is dark at the same place
        mirrored across his face (a pixel either way) is brow; dark that isn't, hanging from his hair above, is a lock of it: gone, with
        its shadow each side, his nearest plain skin there. Super Saiyan (51, 53, 54): a lock hangs by his left brow and ends on it, so
        that brow is his right one's mirrored, and whatever else is dark there goes. His head ends at his chin (where his face's skin
        ends, his jaw's line not counted): under it is his neck, which the outfit takes."""
        g = self.art[gp]; ssj = gp in (51, 53, 54)
        Y, X = np.mgrid[:64, :64]; K3 = np.ones((3, 3), bool)
        gface = self.face(g); gsp = _rows_filled(gface); gm = _rows_filled(self._main(g))
        ge, gmid = self._eyes(g, gsp); sg = ge - 4; bt = ge - 7
        xs = np.nonzero(gm[ge + 2])[0]; m0, m1 = int(xs.min()), int(xs.max())            # (his cheeks)
        dark_c = tuple(c for c in G_SSJ_HAIR if c not in (2, 21, 23, 82, 205)) if ssj else P_HAIR
        raw = self.hair(g, G_SSJ_HAIR if ssj else P_HAIR)
        dark = np.isin(g, dark_c) & self.inner
        band = (Y >= bt) & (Y <= ge - 1) & (X > m0) & (X < m1)
        mx = np.clip(np.round(2 * gmid - X).astype(int), 0, 63)
        out = g.copy(); below = (Y >= sg) & self.inner
        if ssj:
            rb = dark & band & (X > gmid); left = band & (X <= gmid)
            put = left & rb[Y, mx]
            brow = rb | put; lock = dark & left & ~brow
            out[put] = g[Y, mx][put]
        else:
            mir = dark[Y, mx] | dark[Y, np.clip(mx - 1, 0, 63)] | dark[Y, np.clip(mx + 1, 0, 63)]
            brow = dark & band & mir
            cand = dark & band & ~brow
            lab, nl = _lab(cand | (raw & (Y == bt - 1)))
            lock = np.isin(lab, list(set(np.unique(lab[bt - 1]).tolist()) - {0})) & cand
        hair = raw & ~((X >= m0) & (X <= m1) & (Y >= bt) & self.inner)                   # (his hair: not what is in his face)
        clear = np.isin(g, P_SKIN) & gface & ~ndimage.binary_dilation(hair | lock, K3, iterations=2)
        lk = lock & (self.inner if ssj else below)
        if lk.any():
            sh = np.zeros_like(lk); sh[:, 1:] |= lk[:, :-1]; sh[:, :-1] |= lk[:, 1:]
            lk = lk | (sh & np.isin(g, (17, 18, 19, 204)) & ~dark & ~brow & (Y >= bt))
            plain = np.isin(out, (83, 84, 67, 68)) & gface & ~lk & ~brow & (Y >= sg - 2) & (Y <= ge + 1)
            scol, _ = _nearest(plain, out); out[lk] = scol[lk]
        strict = np.isin(g, [c for c in P_SKIN if c not in (16, 17, 18)]) & self.inner
        lab, n = _lab(strict, 4); box = lab[ge:ge + 16, int(gmid) - 8:int(gmid) + 9]
        ids, cnt = np.unique(box[box > 0], return_counts=True)
        chin = int(np.nonzero(lab == ids[np.argmax(cnt)])[0].max())
        return out, dict(g=g, head=gsp & ~hair & (Y <= chin + 1), span=gsp, main=gm, eye=ge, mid=gmid, chin=chin, brow=brow,
                         clear=clear, hair=hair, bg=np.isin(g, BG_OF[gp]) & self.inner & ~gface)

    def inlay(self, gp, kp, form):
        """Gotenks's own picture kp with Gohan's head (picture gp) set into it (Nov 13, 13:15, the owner on `blend`: "The hair is STILL
        FUCKED"). `blend` moved Gotenks's picture onto Gohan's (3 rows of his hair lost off the top), kept Gohan's picture from the brow
        line down and put Gotenks's side hair over it, which left pieces of Gohan's own hair by his brows and ears, background showing
        between his ears and the hair, the collar's leaves cut flat, and his shoulders black beside his ears when he shouts. Here
        Gotenks's picture is the canvas and is not moved: every pixel of his hair, his collar's rolls and what is behind him stays as the
        game has it (his skin in Gohan's colours, the Super Saiyan pictures' purple the blue). Gohan's picture is moved so his eyes sit
        on Gotenks's (their faces are the same width and length: both chins 21 rows under the eyes), and only this of it is used:
        - his head from Gotenks's brow line (4 rows above his eyes) down: his face and ears (`gohan_clean`: no lock of his own hair in
          it); his hair between his ears and his face, and over his temples where Gotenks has none, his skin; where Gotenks's hair
          lies right against his skin (his ears' tops, his temples: his own hair hid their edge) his skin's brown line;
        - above the line Gotenks's own forehead and hairline, the tips of Gotenks's own brows taken off it; Gohan's own skin where his
          forehead shows clear of his hair, and his brows whole;
        - a lock of Gotenks's that hangs in his face (Super Saiyan 3) stays in front of Gohan's;
        - his neck as he has it to 3 rows under his chin (hunched, when he shouts, only the 15 columns under his chin) and under it
          the dark undershirt and vest (by the light on what he wore), from under his ears down only, so his shoulders hunched up
          beside his ears stay out; behind Gotenks's hair and rolls.
        What is left of Gotenks's face that Gohan's doesn't cover (Gohan's jaw is narrower, his ears higher): by his hair what is right
        outside it mirrored in (base: his hair's nearest colour within 2 pixels, else the blue behind him as his other pictures have it
        there); of his body the vest. A Super Saiyan 3 has no brows: Gohan's are his skin, all but the line on his eyes."""
        kraw = self.art[kp]; k = kraw.copy()
        Y, X = np.mgrid[:64, :64]; K3 = np.ones((3, 3), bool)
        for a_, b_ in ((37, 84), (214, 67), (213, 83), (212, 19)): k[k == a_] = b_
        kface = self.face(kraw); ksp = _rows_filled(kface); km = _rows_filled(self._main(kraw))
        ke, kmid = self._eyes(kraw, ksp); sk = ke - 4
        KH = self.hair(kraw, P_HAIR + P_LAV if form == 'base' else P_GOLD + (208, 1)) & ~kface
        rolls = self.rolls_whole(kp)
        if form != 'base':                    # (his hair's colours are his outlines' too: a line is his hair's where it is by his hair)
            core = KH & ~np.isin(kraw, P_LINES)
            KH = core | (KH & ndimage.binary_dilation(core, K3))
        kbg = np.isin(kraw, BG_OF[kp]) & self.inner & ~ksp & ~rolls
        if form != 'base': k[kbg & (kraw == 87)] = 97; k[kbg & (kraw == 88)] = 98
        gc, d = self.gohan_clean(gp); g = d['g']
        dy, dx = ke - d['eye'], int(round(kmid - d['mid']))
        S = lambda a, fill=0: _shift(a, dy, dx, fill)
        G = S(gc); V = S(self.inner, False) & self.inner
        Ghead = S(d['head'], False) & V; Gsp = S(d['span'], False) & V; Gbrow = S(d['brow'], False) & V
        Gclear = S(d['clear'], False) & V; Gbg = S(d['bg'], False) & V; Ghair = S(d['hair'], False) & V
        low = (Y >= sk) & self.inner; above = (Y < sk) & self.inner
        # what stays of Gotenks's picture from his brow line down: his hair, his rolls, what is behind him; not his face's outline
        ring = ndimage.binary_dilation(ksp, K3) & np.isin(kraw, P_LINES) & ~rolls & low
        front = KH & ndimage.binary_erosion(ksp, np.ones((1, 5), bool)) & (Y < ke) & low
        stay = (KH | rolls | kbg) & ~(ring & ~front)
        out = k.copy(); kid = low & ~stay
        # Gohan's neck and, dark, what he wears
        jaw = d['chin'] + dy
        ys, xs = np.nonzero(Ghead); cx = xs[ys >= jaw - 1].mean()
        ears = Ghead & ~S(d['main'], False)
        earb = int(np.nonzero(ears)[0].max()) if ears.any() else jaw - 14
        body = V & ~Gbg & ~Ghead & ~(Gsp & (Y <= jaw + 1)) & (Y >= max(jaw - 14, earb + 1))
        neck = body & np.isin(G, P_SKIN) & (Y <= jaw + 3)
        if (V & ~Gbg & ~Ghead & ~Gsp & ~Ghair & np.isin(G, P_SKIN) & (Y >= sk) & (Y <= earb)).sum() > 20:     # (hunched: his shoulders are up
            neck &= np.abs(X - cx) <= NECK_HALF                                                                #  beside his ears)
        cloth = body & ~neck
        lv = np.clip((pal_lum(G) / 255.0 * 4).astype(int), 0, 4)
        edge = cloth & np.isin(G, (208, 16, 17, 62)); solid = cloth & ~edge
        cloth = solid | (edge & ndimage.binary_dilation(solid, K3))
        can = (kid | kbg) & ~rolls
        put = cloth & can; out[put] = np.array(P_DARK)[lv[put]]
        nearh = ndimage.binary_dilation(Ghead, K3, iterations=2)       # (his jaw's and ears' brown line stays brown; a line further off is cloth)
        putn = (neck | (body & ~cloth & nearh)) & can; out[putn] = G[putn]
        pute = body & ~cloth & ~neck & ~nearh & can; out[pute] = 111; put = put | pute
        done = put | putn
        # his head
        head = Ghead & low
        out[head] = G[head]
        if gp in (51, 53, 54): out[head & np.isin(G, (85, 86, 87, 88))] = 208       # (Super Saiyan Gohan's dark purple lines: Gotenks's brown)
        exs = np.nonzero(Gsp[sk:sk + 12].any(0))[0]; e0, e1 = int(exs.min()), int(exs.max())
        temple = ((Gsp & ~Ghead) | (Ghair & (X >= e0) & (X <= e1) & (Y < sk + 12) & kid)) & low & (Y <= jaw + 1)
        if temple.any():
            scol, _ = _nearest(np.isin(G, (83, 84, 67)) & head, G); out[temple] = scol[temple]
        fr = front & (kraw != 2)
        out[fr] = k[fr]
        done |= head | temple | fr
        # what is left of Gotenks
        left = kid & ~done
        if left.any():
            khz = ndimage.binary_dilation(ksp, K3, iterations=2)
            bodyrem = left & ~khz
            if bodyrem.any():
                if put.any(): c, _ = _nearest(put, out); out[bodyrem] = c[bodyrem]
                else: out[bodyrem] = 111
            headrem = left & khz
            src = stay & ~rolls & KH & ~np.isin(kraw, (208, 16, 17) if form == 'base' else P_LINES + (2,))
            hc, hd = _nearest(src, k)
            if form == 'base':
                near = headrem & (hd <= 2.01); out[near] = hc[near]
                rest = headrem & ~near
                pat = np.zeros((64, 64), np.uint8); have = np.zeros((64, 64), bool)
                for o in (69, 70):                 # (his other two pictures show the blue where this one has his cheeks)
                    a = self.art[o]; m = np.isin(a, (96, 97, 98)) & self.inner & ~have; pat[m] = a[m]; have |= m
                pc, _ = _nearest(have, pat); pat[~have] = pc[~have]
                out[rest] = pat[rest]
            else:
                todo = _mirror_fill(out, headrem, stay & ~kbg, k, kmid)
                out[todo] = hc[todo]
        # above the line
        kskin = np.isin(k, P_SKIN) & km
        Lf = k.copy(); Lf[kskin & np.isin(k, (68, 120))] = 84          # (his forehead's light goes: Gohan's own is kept where his shows)
        kbrow = above & km & ~np.isin(k, P_SKIN) & ~KH & ~ndimage.binary_dilation(KH, K3) & (Y >= ke - 10)
        if kbrow.any():
            pc, _ = _nearest(np.isin(Lf, (83, 84, 67)) & km & above & ~kbrow, Lf); Lf[kbrow] = pc[kbrow]
        out[above] = Lf[above]
        keep = above & ((Gclear & kskin & ~ndimage.binary_dilation(KH, K3, iterations=2)) | Gbrow)
        out[keep] = G[keep]
        if form == 'ssj3':
            b = Gbrow & self.inner
            eye = (out == 2) | (G == 2); e1 = np.roll(eye, -1, 0)
            go = b & ~(e1 | np.roll(e1, 1, 1) | np.roll(e1, -1, 1)) & ~fr
            sc, _ = _nearest(np.isin(out, (83, 84, 67, 68)) & ~go & (Y >= sk - 6) & (Y <= ke + 2) & km, out); out[go] = sc[go]
        # where Gotenks's hair now lies right against Gohan's skin (his ears' tops, his temples: his own hair hid their edge), his skin's line
        core = ((stay & KH) | (left & ~np.isin(out, (96, 97, 98)))) & ~np.isin(out, P_LINES) & ~head & ~temple & low
        n4 = np.zeros_like(core); n4[1:] |= core[:-1]; n4[:-1] |= core[1:]; n4[:, 1:] |= core[:, :-1]; n4[:, :-1] |= core[:, 1:]
        out[(head | temple) & ~fr & np.isin(out, [c for c in P_SKIN if c not in (16, 17)]) & n4] = 208
        out[self.frame] = kraw[self.frame]
        return out

    def gotenks_own(self, kp):
        """Gotenks's own picture kp, his face older (`older`), his bare chest under the vest the black undershirt."""
        k = self.older(kp); face = _rows_filled(self.face(k)); res = k.copy()
        Y, X = np.mgrid[:64, :64]
        ys, xs = np.nonzero(face); jaw = ys.max(); cx = xs[ys >= jaw - 1].mean()
        neck = (np.abs(X - cx) <= 6) & (Y <= jaw + 2)
        chest = np.isin(k, P_SKIN) & self.inner & ~face & (Y >= jaw - 4) & ~neck
        chest |= self.inner & (Y >= jaw + 1) & ~face & ~self.rolls(kp) & ~np.isin(k, BG_OF[kp]) & ~neck & np.isin(k, (2, 118, 119, 120, 21, 67, 83, 84))
        lv = np.clip((pal_lum(k) / 255.0 * 4).astype(int), 0, 4)
        res[chest] = np.array(P_DARK)[np.minimum(lv[chest], 2)]
        return res

    def gohan_own(self, gp, rolls_from):
        """Gohan's own picture gp, his face and hair as they are: what he wears the black undershirt and vest (his shoulders beside his face
        too, high when he shouts), Gotenks's padded collar on his shoulders behind his face and hair, Gotenks's blue behind."""
        a = self.art[gp]; face = self.face(a); hair = self.hair(a, P_HAIR + P_GOLD + P_SSJ_EDGE) & ~face
        res = self.dress(a.copy(), gp, rolls_from, face, hair)
        Y, X = np.mgrid[:64, :64]
        span = _rows_filled(face); jaw = np.nonzero(face)[0].max()
        sh = np.isin(a, P_SKIN) & self.inner & ~span & ~hair & (Y >= jaw - 26) & (res == a)
        lv = np.clip((pal_lum(a) / 255.0 * 4).astype(int), 0, 4)
        res[sh] = np.array(P_DARK)[np.minimum(lv[sh], 2)]
        r = self.rolls(rolls_from); src = self.art[rolls_from]; lab, n = _lab(r)
        for i in range(1, n + 1):
            m = lab == i
            if m.sum() >= 20:
                put = m & ~face & ~hair & self.inner; res[put] = src[put]
        return res

    def make(self, variant, form):
        out = []
        for k, (gp, kp) in enumerate(PICS[form]):
            if variant == 'head':                  # (Gotenks's own pictures as they are: his head, his vest's padded collar)
                out.append(self.art[GOTENKS_PICS[form][k]].copy())
                continue
            if variant == 'grown':                 # (Gohan's face and Gotenks's hair: the owner, Nov 13, 10:29; `inlay`)
                out.append(self.inlay(gp, {'base': 68, 'ssj': 71, 'ssj3': 73}[form], form))
                continue
            if variant == 'hair':                  # (Nov 13, 09:40, the owner: "use one or the other": Gohan's own face and hair)
                out.append(self.gohan_own(gp if form != 'ssj3' else 54, 68 if form == 'base' else 71))
                continue
            a = self.art[gp].copy(); face = self.face(a)
            kart = self.art[kp]; kface = self.face(kart)
            bg = self.bg(gp, face)
            if form == 'base':
                ghair = self.hair(a, P_HAIR) & ~face
                khair = self.hair(kart, P_HAIR + P_LAV) & ~kface
            else:
                ghair = self.hair(a, P_GOLD + P_SSJ_EDGE) & ~face
                khair = self.hair(kart, P_GOLD) & ~kface
                if form != 'ssj3': khair[46:] = False
            put = np.zeros_like(face)
            if variant == 'hair' or form == 'ssj3':
                put = khair & (ghair | bg)
                a[put] = kart[put]
                if form != 'base':                 # (what of Gohan's gold Gotenks's doesn't cover, off his face's span (his brows): in
                    span = np.zeros_like(face)     #  the colour of Gotenks's nearest)
                    for y in range(64):
                        xs = np.nonzero(face[y])[0]
                        if len(xs): span[y, xs.min():xs.max() + 1] = True
                    left = ghair & ~put & ~span
                    col, _ = _nearest(khair, kart); a[left] = col[left]
                    a[ghair & ~put & np.isin(a, (85, 86, 87, 88))] = LINE     # (Gohan's purple hair lines over his brow: Gotenks's brown)
            elif form == 'base':            # recolour: his hair lavender where the nearest of Gotenks's hair is, in Gotenks's strokes there
                lav = np.isin(kart, P_LAV) & khair
                cls, _ = _nearest(khair, kart)
                span = np.zeros_like(face)                   # (never on his brows: only the hair beside and above his face)
                for y in range(64):
                    xs = np.nonzero(face[y])[0]
                    if len(xs): span[y, xs.min():xs.max() + 1] = True
                zone = ghair & np.isin(cls, P_LAV) & ~span
                col, _ = _nearest(lav, kart)
                a[zone] = np.where(lav[zone], kart[zone], col[zone])
            out.append(self.dress(a, gp, ROLLS_FROM[form][k], face, ghair | put))
        return out


def _shift(a, dy, dx, fill=0):
    """a moved dy rows down and dx columns right; what comes in from outside is fill."""
    o = np.full_like(a, fill)
    y0, y1 = max(0, dy), min(64, 64 + dy); x0, x1 = max(0, dx), min(64, 64 + dx)
    o[y0:y1, x0:x1] = a[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    return o


def _mirror_fill(out, rem, ok, src, mid):
    """Each row's run of rem in out: what of src is right outside it (on the side away from the column mid), mirrored into it.
    -> the runs that couldn't be filled (not all of what is outside is ok)."""
    todo = np.zeros_like(rem)
    for y in range(64):
        xs = np.nonzero(rem[y])[0]
        if not len(xs): continue
        for r in np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1):
            a, b = int(r[0]), int(r[-1]); n = b - a + 1
            cols = [a - 1 - i for i in range(n)] if (a + b) / 2 < mid else [b + 1 + (n - 1 - i) for i in range(n)]
            if min(cols) >= 0 and max(cols) < 64 and ok[y, cols].all(): out[y, a:b + 1] = src[y, cols]
            else: todo[y, a:b + 1] = True
    return todo


def _rows_filled(m):
    """m with each row filled from its first pixel to its last."""
    o = m.copy()
    for y in range(m.shape[0]):
        xs = np.nonzero(m[y])[0]
        if len(xs): o[y, xs.min():xs.max() + 1] = True
    return o


def pal_lum(a):
    """Each pixel's light (0-255) in the game's colours."""
    return _PAL_LUM[a]


_PAL_LUM = None


def set_palette(pal):
    global _PAL_LUM
    p = np.asarray(pal, float)
    _PAL_LUM = (0.3 * p[:, 0] + 0.59 * p[:, 1] + 0.11 * p[:, 2])


# The form rows' six expressions (as Gotenks's: calm, calm, shouting, serious, serious, serious), as indices into the seven pictures
# (base calm, serious, shouting; Super Saiyan calm, serious, shouting; Super Saiyan 3)
EXPRESSIONS = {'base': (0, 0, 2, 1, 1, 1), 'ssj': (3, 3, 5, 4, 4, 4), 'ssj3': (6,) * 6}
