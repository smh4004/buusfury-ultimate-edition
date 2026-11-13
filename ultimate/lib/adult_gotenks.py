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
G_VEST = (112, 113, 115)
G_PANTS = (114, 117, 119)
G_UNDER = {200: 113, 201: 112, 202: 111, 203: 112, 205: 111, 16: 1}


def _g_axis(c):
    y = np.isin(c, G_YEL); p = np.isin(c, G_PANTS)
    if y.sum() < 2 or p.sum() < 3: return 0
    vy, vx = np.argwhere(p).mean(0) - np.argwhere(y).mean(0)
    return (0 if vy > 0 else 2) if abs(vy) >= abs(vx) else (1 if vx > 0 else 3)


def _g_undershirt(n):
    yel = np.isin(n, G_YEL); vest = yel | np.isin(n, G_VEST)
    if not yel.any(): return n
    collar = np.nonzero(yel.any(1))[0].min()
    out = n.copy()
    rows = np.nonzero(np.isin(n, G_PANTS).sum(1) >= 2)[0]; rows = rows[rows > collar]
    stop = rows.min() if len(rows) else n.shape[0]
    for y in range(collar + 1, stop):
        vx = np.nonzero(vest[y])[0]
        for x in np.nonzero(np.isin(n[y], SKIN + (LINE,)))[0]:
            l = vx[vx < x]; r = vx[vx > x]
            if len(l) and len(r) and x - l.max() <= 5 and r.min() - x <= 5: out[y, x] = G_UNDER.get(int(n[y, x]), n[y, x])
    return out


def _g_grow(n):
    yel = np.isin(n, G_YEL); ys = np.nonzero(n.any(1))[0]
    if not yel.any() or not len(ys): return n
    collar = np.nonzero(yel.any(1))[0].min(); L = ys.max() - collar
    if L < 6: return n
    out = n.copy()
    for r in sorted([collar + max(2, int(round(0.3 * L))), collar + int(round(0.62 * L)), collar + int(round(0.85 * L))], reverse=True):
        top = out[:r + 1].copy(); out[:r] = top[1:]; out[r] = top[r]
    c2 = max(0, collar - 3); body = np.zeros(out.shape, bool); body[c2:] = out[c2:] > 0
    if body.any():
        cx = int(np.round(np.argwhere(body)[:, 1].mean()))
        res = out.copy(); res[c2:, :cx] = out[c2:, 1:cx + 1]; res[c2:, cx] = out[c2:, cx]; out = res
    return out


def grown(c):
    """One of Gotenks's frames (the 56 x 96 canvas) grown, in the undershirt."""
    if not c.any(): return c.copy()
    r = _g_axis(c); n = np.rot90(c, -r)
    return np.rot90(_g_grow(_g_undershirt(n)), r)


def grown_frames(rom, actor_list, form):
    """{slot: [front, back, side frame lists]} for the build (64-column canvases), from Gotenks's own (GROWN[form])."""
    g = cells(rom, actor_list, GROWN[form])
    return {s: [[grown(c)[OUT] for c in g[s][d]] for d in range(3)] for s in g}


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

    def dress(self, a, i, g, face, hair):
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

    def gotenks_own(self, kp):
        """Gotenks's own picture kp, his bare chest under the vest the black undershirt."""
        k = self.art[kp]; face = _rows_filled(self.face(k)); res = k.copy()
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
            if variant == 'grown':                 # (Gotenks's own pictures, his bare chest the black undershirt)
                out.append(self.gotenks_own(GOTENKS_PICS[form][k]))
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
