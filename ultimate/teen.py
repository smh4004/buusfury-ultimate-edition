"""Teen Gohan's purple gi as a Super Saiyan and a Super Saiyan 2 (Nov 11, the owner: "add base/SSJ1/SSJ2 Teen Gohan to the Cell
Games unlocks", "Check if Teen Gohan base/1/2 are in LoG2 and use those if so", "make sure the new Teen Gohan sprites don't have any
alignment issues with the head or neck").
LoG2 draws those forms only in the Saiyan armor (r56 Super Saiyan, r55 Super Saiyan 2) and the purple gi only with his long black
hair (r50). It also draws the armor with that long-haired head (r52) and with short black hair (r53), pose for pose. Every record
places its frames by itself (r56's front frames sit a pixel left of r53's, others a pixel up or down), so nothing is taken from a
frame before it is placed (lib/headfit.py: by the head two frames share, or the armor they share), and a frame that can't be placed
stops the build.
  short(): the purple frame with the short black hair. His long hair is every black pixel that hangs together with the head he
    shares with the long-haired armor frame (the gi has no black of its own above the shoes: its outlines are navy and brown). It
    goes; the short-haired armor frame's head pixels come; what was under it is nothing, or gi where the gi closes round it.
  ss(): the short-haired frame with r56's head, from r56's frame of the same pose.
  ss2(): the Super Saiyan frame with r55's head: r55's frame of the same pose, or, where r55 stands another way (its idle has the
    hands on the hips), a donor pair of the same view whose r56 head is this frame's golden head; then r55's own head for the frame,
    placed on the donor's by its gold (the idle's own hair and blink).
  (Nov 14, every animation a slot of his plays, for both forms: where LoG2 lacks a record for a pose, bare_place and ss_place place the
  frames through others that draw the same heads, best2_checked and swap2 make the Super Saiyan 2 frames r55 never draws, and still2
  keeps the Super Saiyan 2 stance's hair still.)
check() is run on every finished frame, and every() makes and checks every frame the build uses before the build writes one: a frame
that can't be placed, or fails a check, stops the build (the owner: "don't allow that to happen anymore").
The build: use(l2) once, every(), then made(form) is sprites.log2_anim's frame source for the two figures."""
import struct, sys
import numpy as np
import headfit as F
from headfit import Off
RECORDS = {'P': 'r50', 'AL': 'r52', 'AS': 'r53', 'S1': 'r56', 'S2': 'r55'}
OX, OY, CW, CH = 48, 72, 96, 96             # every frame goes on one canvas, its record's origin here


class Log2:
    """LoG2's frames as they are shown (a flipped frame turned round), each on the canvas."""
    def __init__(self, l2):
        import sprites
        self.l2, self.B, self.sprites = l2, sprites.L2_BASE, sprites
        self.pal = np.frombuffer(l2[sprites.L2_PAL + 768:sprites.L2_PAL + 1536], np.uint8).reshape(256, 3)
    def u(self, o): return struct.unpack_from('<I', self.l2, o)[0]
    def rec(self, n): return self.sprites.log2_rec(self.l2, n)
    def dirs(self, r, k): return [self.u(r + 0x4C + 16 * k + 4 * d) for d in range(4)]
    def nframes(self, r, k):
        ds = self.dirs(r, k); B = self.B
        if not any(B <= x < B + len(self.l2) for x in ds): return 0
        us = sorted(set(x for x in ds if x)); gaps = [b - a for a, b in zip(us, us[1:])]
        if gaps: return min(gaps) // 12
        n = 1
        while n < 12:
            q = us[0] - B + 12 * n; x, y, w, h = struct.unpack_from('<bbBB', self.l2, q); tp = self.u(q + 8)
            if not (w and h and w * h <= 4096 and B <= tp < B + len(self.l2)): break
            n += 1
        return n
    def raw(self, r, k, d, f):
        from wfz import decompress_stream
        ds = self.dirs(r, k); p = ds[d] or ds[2] or (sorted(x for x in ds if x) or [0])[0]; B = self.B
        if not p: return None
        q = p - B + 12 * f; x, y, w, h = struct.unpack_from('<bbBB', self.l2, q); attr, tp = struct.unpack_from('<II', self.l2, q + 4)
        if not (w and h and w * h <= 4096 and B <= tp < B + len(self.l2)): return None
        o = tp - B; t, size = struct.unpack_from('<II', self.l2, o)
        data = self.l2[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(self.l2, o + 8, size)[0])
        px = np.frombuffer(data, np.uint8)[:w * h].reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
        if attr & 0x10000000: px = px[:, ::-1]
        return x, y, w, h, px, attr
    def placed(self, r, k, d, f):
        v = self.raw(r, k, d, f)
        if v is None: return None
        x, y, w, h, px, attr = v; c = np.zeros((CH, CW), np.uint8)
        c[OY + y:OY + y + h, OX + x:OX + x + w] = px
        return c
    def rgb(self, c, bg=(70, 90, 70)):
        out = self.pal[c].copy(); out[c == 0] = bg; return out.astype(np.uint8)


L = None; REC = {}
def use(l2):
    """The LoG2 half of the combo cart the frames come from. Once, before anything else."""
    global L, REC
    L = Log2(l2); REC = {n: L.rec(v) for n, v in RECORDS.items()}
    _short.clear(); _own.clear(); _made.clear()
SKIN_S, BROWN_S, GOLD_S, EYES_S = {0x72, 0x73, 0x74, 0x75}, set(range(0x10, 0x18)) | {0x71}, {0x2e, 0x78, 0x24, 0x25, 0x26, 0x27, 0x2c}, {0x40, 0x41, 0x31, 0x32}
SUIT_S = set(range(0x02, 0x0e)) | {0x28, 0x29, 0x2a, 0x4f, 0x50, 0x51}       # the armor: whites and greys, the straps' yellows, the suit's blues
SKIN, SUIT, GOLDC = F.cls(SKIN_S), F.cls(SUIT_S), F.cls(GOLD_S)
HEADMARK = F.cls(SKIN_S, {0x0f})          # what places a black-haired head: its face, and the grey lights in its hair
HAIRB = F.cls({0x01, 0x0f})               # black and its grey light: black hair, and every black outline
GIC = F.cls({0x50, 0x51, 0xd3})           # the gi's purples and its navy
FACE = F.cls(SKIN_S, BROWN_S)
CORE = F.cls(GOLD_S, BROWN_S, SKIN_S, EYES_S)
GOLDISH = F.cls(GOLD_S, BROWN_S)
NEUTRAL = F.cls(set(range(0x01, 0x10)))   # black, white and the greys between
EVERY = F.cls(set(range(1, 256)))
DONORS = [(k, f) for k in (1, 13, 2, 5, 6, 7, 8, 3) for f in range(4)]
MAX_MISS = 8                              # a donor's golden head may differ from this frame's by a strand, no more
def one_view(n, k): return len(set(L.dirs(REC[n], k))) == 1
STRAY = 0xef                              # one magenta pixel under his fringe in r55's side walk (frames 1 and 3), a colour none of the
                                          # five records uses anywhere else: a slip of LoG2's, left out of the frames made here
def get(n, k, d, f):
    c = L.placed(REC[n], k, d, f) if L.nframes(REC[n], k) > f else None
    if c is not None and n == 'S2': c[c == STRAY] = 0
    return c
def head_rect(a, s):
    """Where the head is: (top row, bottom row, left, right), a little over. From the Super Saiyan armor frame placed on this one: its
    gold and the face that hangs together with it (never his hands: all skin once counted, and in a lunge the 'head' reached his
    shoes). A frame the Super Saiyan record draws with black hair (knocked down) has no gold: the skin and hair lights above the waist."""
    gold = GOLDC[s] if s is not None else np.zeros(a.shape, bool)
    if gold.any():
        gy = np.where(gold.any(1))[0]; near = np.zeros(a.shape, bool); near[:gy.max() + 7] = True
        ys, xs = np.where(F.flood(gold, CORE[s] & near, True))
        return ys.min() - 2, ys.max() + 2, xs.min() - 3, xs.max() + 3
    ys, xs = np.where(HEADMARK[a]); top = ys.min(); keep = ys <= top + 14
    return top - 8, ys[keep].max(), xs[keep].min() - 9, xs[keep].max() + 9
def box_of(shape, rect, down=0, side=0):
    y0, y1, x0, x1 = rect; m = np.zeros(shape, bool)
    m[max(y0, 0):y1 + 1 + down, max(x0 - side, 0):x1 + 1 + side] = True
    return m
def head_box(n, down=0, side=0): return box_of(n['a'].shape, n['rect'], down, side)
def gi_fill(out, mask, p, keep):
    """Pixels in `mask` (body the hair hid) get the gi colour nearest in their row, from P's pixels in `keep`."""
    ok = keep & GIC[p]; ys_all, xs_all = np.where(ok)
    for y, x in zip(*np.where(mask)):
        row = np.where(ok[y])[0]
        if len(row): out[y, x] = p[y, row[np.abs(row - x).argmin()]]
        elif len(ys_all): i = (np.abs(ys_all - y) * 3 + np.abs(xs_all - x)).argmin(); out[y, x] = p[ys_all[i], xs_all[i]]
    return int(mask.sum())
# Body the purple record never drew (his long hair covers it: his back in the views from behind, a forearm beside his head) is the
# armor frame's, pixel by pixel in the purple record's colours, by what the purple frame shows of the same part right beside it:
#   a plate, glove or boot (whites, greys, strap yellows): where the purple frame shows skin on that same piece within three pixels,
#     his bare hand; where it shows a sock's greys or a shoe, those (kept as they are); else his gi (a plate on his chest or back)
#   the suit's blues: the gi's own, or his bare forearm where the purple frame shows skin within two pixels and no gi
#   a black outline: the brown round skin, black round a shoe, else the navy round the gi
# (Filled from whatever lay nearest, his back took his wristband's grey; filled as gi throughout, his wrist had a purple speck; voted
# on by whole pieces, a glove held against his chest turned his back to skin.)
AS_GI = {0x01: 0xd3, 0x0f: 0xd3, 0x0e: 0xd3, 0x0d: 0xd3, 0x0c: 0x51, 0x0b: 0x51, 0x0a: 0x51, 0x09: 0x51, 0x02: 0x51, 0x28: 0x50, 0x29: 0x51, 0x2a: 0x51,
         0x4f: 0x50, 0x50: 0x50, 0x51: 0x51, 0xd3: 0xd3}
AS_SKIN = {0x02: 0x72, 0x09: 0x72, 0x0a: 0x73, 0x0b: 0x74, 0x0c: 0x74, 0x0d: 0x17, 0x0e: 0x17, 0x0f: 0x17, 0x28: 0x73, 0x29: 0x74, 0x2a: 0x75,
           0x4f: 0x73, 0x50: 0x74, 0x51: 0x75, 0x01: 0x17}
PLATE = F.cls(set(range(0x02, 0x10)), {0x28, 0x29, 0x2a})
BLUE = F.cls({0x4f, 0x50, 0x51})
RED = F.cls({0x18, 0x19, 0x1a, 0x1b})     # his wristbands and his sash
STRAP = F.cls({0x28, 0x29, 0x2a})         # the yellows of the armor's straps
SMALL = 6                                 # pixels: a piece of plate no bigger is a glove's or a boot's end, never a chest or back plate
def pieces(m):
    """The mask's pieces that hang together (8 neighbours), numbered from 1."""
    lab = np.zeros(m.shape, np.int32); left = m.copy(); n = 0
    while left.any():
        y, x = np.argwhere(left)[0]; seed = np.zeros(m.shape, bool); seed[y, x] = True
        piece = F.flood(seed, left, True); n += 1; lab[piece] = n; left &= ~piece
    return lab
def streak(src, p):
    """The white streaks a blow leaves in the air, in the armor frame `src`: white one pixel wide with nothing on both sides of it,
    that hangs together (through white) with white the purple frame `p` draws in the very same place; or a whole piece of pure white
    the purple frame draws part of. They are no plate: where his hair lay over one, it stays white. (As a plate it turned to gi: a
    purple line behind his head in the high kick.)"""
    w = src == 0x02; e = src == 0
    thin = w & ((F.shift(e, 0, 1) & F.shift(e, 0, -1)) | (F.shift(e, 1, 0) & F.shift(e, -1, 0)))
    line = thin & F.flood(w & (p == 0x02), w, True)
    lab = pieces(PLATE[src])                  # and a piece that is white all through (a plate, a glove, a boot has its greys), where the
    for i in set(lab[w & (p == 0x02)].tolist()) - {0}:        # purple frame draws at least two pixels of it
        if (src[lab == i] == 0x02).all() and int(((lab == i) & (p == 0x02)).sum()) >= 2: line |= lab == i
    return line
def body_fill(out, mask, src, a, p, keep, **old):
    """Pixels in `mask` (body the hair hid, which the armor frame `src` draws) in the purple record's colours (above)."""
    if not mask.any(): return 0
    seen = (p != 0) & (~HAIRB[p] | ground(p)); lab = pieces(PLATE[src]); new = {}      # (all of his body the frame shows, hair apart)
    line = streak(src, p); size = np.bincount(lab.ravel())
    foot = socks(p, np.zeros(p.shape, bool)) | (ground(p) & HAIRB[p])       # his socks and shoes, never his collar: the white shirt's greys
    foot |= (p == 0x02) & F.grown(foot, 1)                                  # round his neck kept the back plate's greys and a strap's yellow
                                                                            # in the middle of his back
    # A hidden stretch of the suit's blue (hanging together by its sides) that touches none of the gi's purple the frame shows, but the
    # brown that outlines his skin: a bare arm (behind his back in the side views, between the navy edge of his chest and its own brown).
    arm = np.zeros(p.shape, bool); hid = pieces4(mask & BLUE[src]); cloth = seen & ((p == 0x50) | (p == 0x51)); bare = seen & FACE[p]
    for i in range(1, hid.max() + 1):
        by = beside(hid == i)
        if not (by & cloth).any() and (by & bare).any(): arm |= hid == i
    # The glove at the end of such an arm is his bare hand: a piece of plate that touches the arm, with none of the straps' yellow in
    # it (a chest or back plate has them: all under his hair in a view from behind, it turned his back to skin), and of which the
    # frame shows no gi and no sock or shoe.
    hand = set()
    for i in set(lab[F.grown(arm, 1) & (lab > 0)].tolist()):
        m = seen & (lab == i)
        if not STRAP[src[lab == i]].any() and not GIC[p[m]].any() and not foot[m].any(): hand.add(i)
    for y, x in zip(*np.where(mask)):
        c = int(src[y, x]); r = 3 if PLATE[c] else 2
        if line[y, x]: new[y, x] = c; continue
        win = (slice(max(y - r, 0), y + r + 1), slice(max(x - r, 0), x + r + 1)); sel = seen[win]; q = p[win]
        if PLATE[c]: sel = sel & (lab[win] == lab[y, x])
        skin, grey, gi = int((sel & FACE[q]).sum()), int((sel & foot[win]).sum()), int((sel & GIC[q]).sum())
        if PLATE[c] and lab[y, x] in hand: new[y, x] = AS_SKIN.get(c, 0x74)
        elif PLATE[c] and skin + grey + gi < 3 and size[lab[y, x]] <= SMALL:      # a small piece with too little showing this near (a glove's
            m = seen & (lab == lab[y, x]); q = p[m]  # tip beside his head, the rest under his hair): what the frame shows of the whole piece,
                                                     # a red wristband counting as his hand. (A back plate judged so turned to skin.)
            skin, grey, gi = int((FACE[q] | RED[q]).sum()), int(foot[m].sum()), int(GIC[q].sum())
            new[y, x] = AS_SKIN.get(c, 0x74) if skin and skin >= grey and skin > gi else c if grey and grey > gi else AS_GI.get(c, 0x51)
        elif PLATE[c]: new[y, x] = AS_SKIN.get(c, 0x74) if skin >= 3 and skin >= grey and skin > gi else c if grey >= 3 and grey > gi else AS_GI.get(c, 0x51)
        elif BLUE[c]: new[y, x] = AS_SKIN[c] if (skin >= 2 and gi == 0) or arm[y, x] else AS_GI[c]
        elif c == 0x01: new[y, x] = 0x17 if skin > max(grey, gi) else 0x01 if grey > gi else 0xd3
        else: new[y, x] = c
    for (y, x), c in new.items(): out[y, x] = c
    return int(mask.sum())
def beside(m):
    """The pixels next to the mask (4 neighbours), not in it."""
    return (F.shift(m, 1, 0) | F.shift(m, -1, 0) | F.shift(m, 0, 1) | F.shift(m, 0, -1)) & ~m
def pieces4(m):
    """The mask's pieces that hang together by their sides (4 neighbours), numbered from 1."""
    lab = np.zeros(m.shape, np.int32); left = m.copy(); n = 0
    while left.any():
        y, x = np.argwhere(left)[0]; seed = np.zeros(m.shape, bool); seed[y, x] = True
        piece = F.flood(seed, left); n += 1; lab[piece] = n; left &= ~piece
    return lab
def closed_in(mask, body):
    """Of the pixels in `mask`, those with body somewhere to their left and to their right in the row."""
    left = np.maximum.accumulate(body, 1); right = np.maximum.accumulate(body[:, ::-1], 1)[:, ::-1]
    return mask & left & right
OUTLINE = F.cls(BROWN_S, {0xd3, 0x01})        # the browns round skin, the navy round the gi, black
GREY = F.cls(set(range(0x0a, 0x0f)))        # his socks and the lights on his shoes (and the shading of an eye)
def ground(p):
    """His shadow, and the shoes that stand on it: the black of the frame's lowest rows that hangs together with its bottom rows
    (the shadow is rows 5 to 7 under the origin in every record; in the air there is none). In a lunge the long hair comes within
    a few pixels of the shadow, and the shadow went with it."""
    g = np.zeros(p.shape, bool); ys = np.where((p != 0).any(1))[0]
    if not len(ys) or ys.max() != OY + 7: return g
    low = g.copy(); low[OY + 3:OY + 8] = True
    seed = g.copy(); seed[OY + 5:OY + 8] = True
    return F.flood(seed & HAIRB[p], HAIRB[p] & low, True)
RIM = F.cls({0x02}, set(range(0x09, 0x0f)))  # white and the greys (not the hair's own light, 0x0f)
def inner(p):
    """The inside of a shoe: a small piece of black (hanging together by its sides) with white or grey along most of its edge. His
    hair is never closed in by greys. (In the high kick his foot is up beside his face: its greys touch the face's outline and lie
    in the head's box, so they did not count as a sock's, the shoe's black went as hair, and the armor's white boot came in its
    place. Seen from behind in the kick, the sole is a black band open at both ends: all four sides was asking too much.)"""
    lab = pieces4(p == 0x01); out = np.zeros(p.shape, bool); size = np.bincount(lab.ravel())
    for i in range(1, lab.max() + 1):
        if size[i] > SHOE: continue
        by = beside(lab == i)
        if RIM[p][by].sum() * 10 >= by.sum() * SHOE_RIM and not SKIN[p][by].any(): out |= lab == i      # (beside skin: the pupil of an eye)
    return out
SHOE, SHOE_RIM = 16, 7                       # a shoe's black: at most 16 pixels, at least 7 in 10 of the pixels round it white or grey
def socks(p, head):
    """The greys of his socks and shoes: every grey off his head but those that hang together with a grey beside skin (his
    wristbands, and the white shirt under his gi from the collar down)."""
    g = GREY[p]
    return g & ~F.flood(F.grown(FACE[p], 1) & g, g, True) & ~head
RIMLINE = F.cls({0x14, 0x17, 0xd3})        # the outlines of the purple figure: brown round skin, navy round the gi
_short = {}
NOFACE = F.cls(SKIN_S, BROWN_S, {0x0f})     # the face, its outlines and the hair's light: what the purple and short-haired frames share
def top_of(c, rows=16):
    """The frame's top rows (its head), nothing else."""
    ys = np.where((c != 0).any(1))[0]; m = np.zeros(c.shape, bool)
    if len(ys): m[ys.min():ys.min() + rows] = True
    return np.where(m, c, 0)
def through(k, d, f, nx, ny, cx, cy, direct, what, own=None, only=None):
    """Where record ny's frame (k, d, f) sits on record nx's, for a frame where the two can't be placed on each other directly (their
    bodies are drawn too differently there). Through other frames of the same view: one whose nx frame draws this very head, every pixel
    (in class cx) and whose ny frame draws much the same head (cy, 8 in 10 pixels), where the two records place their frames on each
    other directly; that placing, moved as the two heads lie against these. Each such frame votes, and so does `own`, the direct
    witness's offset where it is fair (8 in 10 pixels) though not clear. (Only frames record `only` draws too, where given.) The offset with the most votes, at least two and more than any
    other, places the frame; else Off."""
    x, y = get(nx, k, d, f), get(ny, k, d, f); votes = []
    if own is not None: votes.append(own)
    for k2 in range(20):
        if k2 == k or one_view('P', k2) != one_view('P', k): continue
        for f2 in range(L.nframes(REC['P'], k2)):
            x2, y2 = get(nx, k2, d, f2), get(ny, k2, d, f2)
            if x2 is None or y2 is None or (only and get(only, k2, d, f2) is None): continue
            ox, eq, meet, nxt = F.witness(top_of(x), top_of(x2), cx)
            if eq < 60 or eq < meet: continue
            oy, eqy, meety, nxty = F.witness(top_of(y), top_of(y2), cy)
            if eqy < 0.8 * meety: continue
            try: o2 = direct(k2, d, f2)
            except Off: continue
            votes.append((o2[0] + ox[0] - oy[0], o2[1] + ox[1] - oy[1]))
    tally = sorted(((votes.count(o), o) for o in set(votes)), reverse=True)
    if not tally or tally[0][0] < 2 or (len(tally) > 1 and tally[1][0] == tally[0][0]):
        raise Off('%s: nothing places it (votes %s)' % (what, tally))
    return tally[0][1]
def fair(a, b, c):
    """The direct witness's offset of b on a for class c, where at least 8 in 10 of its pixels agree; else None."""
    o, eq, meet, nxt = F.witness(a, b, c)
    return o if eq >= 8 and eq >= 0.8 * meet else None
def bare_place(k, d, f, p, a):
    """Where the short-haired armor frame sits on the purple one for a pose LoG2 draws no long-haired armor frame of (the charged hit, 16):
    by what the two share of the head (face, outlines, the hair's light) where that is clear, else through frames that draw these heads
    (through())."""
    try: return F.place(p, a, 'short-haired armor on the purple frame', (NOFACE, 8, 0.8, 1.6), (F.cls(SKIN_S), 8, 0.8, 1.6))
    except Off: pass
    return through(k, d, f, 'P', 'AS', NOFACE | HAIRB, NOFACE | HAIRB, lambda k2, d2, f2: short(k2, d2, f2)['o_a'],
                   'short-haired armor on the purple frame', fair(p, a, NOFACE), only='AL')
def ss_place(k, d, f, a_raw, s_raw):
    """Where the Super Saiyan armor frame sits on the short-haired armor frame: by their armor where that is clear (the same pose drawn
    alike), else through frames that draw these two heads (the charged hit's leaps: r56 draws them higher than r53)."""
    try: return F.place(a_raw, s_raw, 'Super Saiyan armor on the short-haired armor', (SUIT, 30, 0.7, 1.6), (SKIN, 8, 0.8, 1.6))
    except Off as e: first = e
    # (in the charged hit's leaps r56 draws him six or seven rows higher than r53 does: past the five rows the witnesses look across,
    # so they look again from five rows up)
    try:
        o = F.place(a_raw, F.shift(s_raw, 0, -5), 'Super Saiyan armor on the short-haired armor', (SUIT, 30, 0.7, 1.6), (SKIN, 8, 0.8, 1.6))
        return (o[0], o[1] - 5)
    except Off: pass
    def direct(k2, d2, f2):
        return F.place(get('AS', k2, d2, f2), get('S1', k2, d2, f2), 'Super Saiyan armor on the short-haired armor', (SUIT, 30, 0.7, 1.6), (SKIN, 8, 0.8, 1.6))
    try: return through(k, d, f, 'AS', 'S1', NOFACE | HAIRB, NOFACE | GOLDC, direct, 'Super Saiyan armor on the short-haired armor')
    except Off as e: raise Off('%s; %s' % (first, e))
def short(k, d, f):
    if (k, d, f) in _short: return _short[k, d, f]
    p, al, a = get('P', k, d, f), get('AL', k, d, f), get('AS', k, d, f)
    if p is None or a is None: raise Off('no frame')
    if al is not None:
        o1 = F.place(p, al, 'long-haired armor head on the purple head', (HEADMARK, 8, 0.85, 1.6), (HAIRB, 60, 0.9, 1.3))
        al = F.shift(al, *o1)
        o2 = F.place(al, a, 'short-haired armor on long-haired armor', (SUIT, 30, 0.5, 1.6), (HEADMARK, 6, 0.85, 1.6))     # (r52 wears shoulder pads, r53 none: the rest is equal)
    else:
        o1 = (0, 0); o2 = bare_place(k, d, f, p, a)
    a = F.shift(a, *o2)
    a_raw, s_raw = get('AS', k, d, f), get('S1', k, d, f); o_s = s = None
    if s_raw is not None:
        o_s = ss_place(k, d, f, a_raw, s_raw)
        s = F.shift(s_raw, o1[0] + o2[0] + o_s[0], o1[1] + o2[1] + o_s[1])
    rect = head_rect(a, s); box = box_of(p.shape, rect); wide = box_of(p.shape, rect, 14, 8)
    # His long hair: what the long-haired armor frame has of it too (both), the black the two share on the head, and the locks only
    # the purple record draws (one lies over his shoulder in the front views, four rows under the hair it belongs to): black within
    # reach of that hair. Never his shoes: black beside a sock's or a shoe's grey, or two pixels from one where the armor frame has
    # its boot, or standing on his shadow. (Seen from behind in a punch, a shoe is dark grey and black right under the hair that
    # hangs down his back: it went with the hair, and the armor's grey boot came in its place.)
    feet = ground(p); bare = al is None
    if bare:
        # (no long-haired armor frame: the purple frame's black in and round the head, never his shoes, is his long hair; the short-haired
        # armor frame with that hair over it stands for the long-haired one. In these leaps his feet pass over his head: a shoe's greys
        # in the head's box are his shoe's all the same.)
        sock = socks(p, np.zeros(p.shape, bool))
        shoe = HAIRB[p] & (F.grown(sock, 1) | (NEUTRAL[a] & F.grown(sock, 2))) | inner(p)
        al = a.copy(); m = HAIRB[p] & wide & ~feet & ~shoe; al[m] = p[m]
    both = (al != a) & (p == al) & HAIRB[al] & ~feet
    hair = both | (HAIRB[p] & HAIRB[al] & (p == al) & box & ~feet)
    sock = socks(p, np.zeros(p.shape, bool) if bare else box)
    shoe = HAIRB[p] & (F.grown(sock, 1) | (NEUTRAL[a] & F.grown(sock, 2)))      # beside a sock's grey, or where the armor has its boot
    shoe |= inner(p)                                                           # and a shoe's black inside its grey rim, wherever it is
    lock = HAIRB[p] & ~feet & ~shoe & wide
    while True:
        more = hair | (F.grown(hair, 4) & lock)
        if (more == hair).all(): break
        hair = more
    out = p.copy()
    keep = hair & HAIRB[a] & box                                   # short hair is there as well
    out[keep] = a[keep]
    gone = hair & ~keep
    body = (p != 0) & ~hair
    show = gone & (a != 0) & ~FACE[a]                              # the short-haired figure's body, where the long hair was
    fill = closed_in(show, body)                                   # the gi closes round it: gi under the hair
    edge = show & ~fill                                            # the body's own edge was under the hair (seen from behind, his hair
    out[gone] = 0                                                  # covers his back): the armor frame's body, in the gi's colours
    # The armor's sleeves and shoulders are a pixel wider than his bare arms and the gi's shoulders: one hidden pixel by itself in its
    # row, right outside an outline the purple frame draws (brown round his skin, navy round the gi), is nothing of his. (A lock lies
    # over his shoulder in the front views: filled in, that arm stood a pixel wider than the other.)
    # Not where his body goes on both over and under it (the tip of a hand's outline: dropped, the hand had a notch).
    rim = body & RIMLINE[p]; lone = edge & ~F.shift(show, 1, 0) & ~F.shift(show, -1, 0) & (F.shift(rim, 1, 0) | F.shift(rim, -1, 0))
    firm = body | (show & ~lone)                                   # his body as the frame shows it, and as it was under the hair
    over = F.shift(firm, 0, 1); under = F.shift(firm, 0, -1)       # ... right over / right under the pixel
    while True:                                                    # (through a run of such pixels one over the other)
        o_, u_ = over | (lone & F.shift(over & lone, 0, 1)), under | (lone & F.shift(under & lone, 0, -1))
        if (o_ == over).all() and (u_ == under).all(): break
        over, under = o_, u_
    edge &= ~(lone & ~(over & under))
    skin = gone & FACE[a]; out[skin] = a[skin]                     # his neck
    body_fill(out, fill | edge, a, a, p, ~hair)
    fill = fill | edge
    if bare:
        # (the leaps: under his long hair lay the blow's white streak, which the short-haired armor frame draws a pixel off the purple
        # frame's; filled from it, a speck of gi stood in the streak. A speck of gi with no gi beside it and nothing round it but hair,
        # white and the air is the streak's white where white is beside it, else the air.)
        gi = GIC[out] & fill; body = (out != 0) & ~(F.cls({0x01, 0x0f, 0x02}))[out] & ~GIC[out]
        speck = gi & ~(F.shift(GIC[out], 1, 0) | F.shift(GIC[out], -1, 0) | F.shift(GIC[out], 0, 1) | F.shift(GIC[out], 0, -1)) & ~F.grown(body, 1)
        out[speck] = np.where(F.grown(out == 0x02, 1)[speck], 0x02, 0)
    more = (al != a) & (p == al) & (HAIRB | FACE)[a] & box & ~hair  # short hair where the long-haired head has none
    out[more] = a[more]
    _short[k, d, f] = dict(out=out, a=a, fill=fill, hair=hair, o_long=o1, o_short=o2, o_a=(o1[0] + o2[0], o1[1] + o2[1]), fills=int(fill.sum()),
                           rect=rect, s=s, o_s=o_s, both=(al != a) & (p == al) & HAIRB[al])
    return _short[k, d, f]
def head_of(s):
    """The head in a Super Saiyan armor frame. By colour: gold, the browns that outline hair and skin, skin, the eyes (the armor has
    none of them). White is armor too: a light in the hair is white that gold and white lead to from gold (never across the hair's
    brown outline, where a white collar may lie). Black, white and grey with head on all four sides are in it (a pupil, the white of an eye)."""
    h = CORE[s] | ((s == 0x02) & F.flood(GOLDC[s], GOLDC[s] | (s == 0x02)))
    return h | F.ringed(NEUTRAL[s] & ~h, h)
def mend(out, p, src, sh, keep, a):
    """A pixel left empty with the figure on all four sides, that neither the purple frame nor the head's own frame has empty: the
    head's frame's pixel there, or gi where that shows armor."""
    for _ in range(3):
        h = F.holes(out) & ~F.holes(p) & (src != 0)
        if not h.any(): break
        arm = h & SUIT[src] & (src != 0x02)
        out[h & ~arm] = src[h & ~arm]
        body_fill(out, arm, src, a, sh, keep & ~h)
    return out
def ss(k, d, f):
    """Frame (k, d, f) of the purple gi as a Super Saiyan. -> (canvas, notes)"""
    A = short(k, d, f); sh = A['out']
    if A['s'] is None: raise Off('no frame')
    o_s = A['o_s']; a = A['a']; o = (A['o_a'][0] + o_s[0], A['o_a'][1] + o_s[1]); s = A['s']
    if not GOLDC[s].any():        # r56 draws this frame with the black hair (knocked down, LoG2 shows the base look): the purple frame as it is
        p = get('P', k, d, f)
        return p, dict(o_long=A['o_long'], o_short=A['o_short'], o_ss=o_s, o_s1=o, fills=0, fills2=0, left=0, s=s, a=a, short=sh, p=p, filled=np.zeros(p.shape, bool),
                       hair=A['hair'], placed=np.zeros(p.shape, bool), plain=True, rect=A['rect'], both=A['both'])
    # Only the head changes hands. (The two armor records don't draw their shadows on the same rows in every frame: taken over the whole
    # figure, the difference hollowed his shadow out in the lunge.)
    ch = (a != s) & box_of(a.shape, A['rect'], 1, 1) & ~ground(get('P', k, d, f))
    head = ch & head_of(s)
    if get('AL', k, d, f) is None:
        # (the charged hit's leaps, which LoG2 draws no long-haired armor frame of: his feet pass over his head, in front of it. The purple
        # frame's shoes there stay (their greys, and the black beside them), and so does what r56 draws of its boot round them.)
        pf = get('P', k, d, f); sock = socks(pf, np.zeros(pf.shape, bool))
        shoe = sock | (HAIRB[pf] & F.grown(sock, 1) & ~A['hair']) | (HAIRB[pf] & F.grown(sock, 1) & (pf == sh))
        head &= ~F.flood(F.grown(shoe, 1) & NEUTRAL[s] & ~GOLDC[s], NEUTRAL[s] & ~GOLDC[s])
        head &= ~shoe
    may = (sh == 0) | HAIRB[sh] | A['fill'] | (sh == a) | (FACE[sh] & (FACE | HAIRB)[a])
    out = sh.copy(); out[head & may] = s[head & may]
    gone = ch & (s == 0) & (sh == a) & (HAIRB | FACE)[a]            # short hair with nothing behind it now
    out[gone] = 0
    body = ch & ~head & (s != 0) & HAIRB[a] & (sh == a)             # armor from under the short hair: gi
    fills = body_fill(out, body, s, a, sh, ~(ch | A['fill']))
    mend(out, get('P', k, d, f), s, sh, ~(ch | A['fill']), a)
    if get('AL', k, d, f) is None:            # (the leaps: his shoe over his head is the purple frame's, to two pixels from its greys)
        pf = get('P', k, d, f); zone = NEUTRAL[pf] & F.grown(socks(pf, np.zeros(pf.shape, bool)), 2) & ~GOLDC[out] & (out != pf)
        out[zone] = pf[zone]
    left = ch & ~(head & may) & ~gone & ~body & ((HAIRB | FACE)[a] | head)
    return out, dict(o_long=A['o_long'], o_short=A['o_short'], o_ss=o_s, o_s1=o, fills=A['fills'], fills2=fills, left=int(left.sum()), s=s, a=a, short=sh, p=get('P', k, d, f),
                     filled=A['fill'] | body, hair=A['hair'], placed=head & may, rect=A['rect'], both=A['both'])
def ss2(k, d, f, donor=None, loose=False):
    base, n1 = ss(k, d, f)
    k2, f2 = donor or (k, f)
    s1_raw, s2_raw = get('S1', k2, d, f2), get('S2', k2, d, f2)
    if s1_raw is None or s2_raw is None: raise Off('no frame')
    o_2 = F.place(s1_raw, s2_raw, 'Super Saiyan 2 armor on the Super Saiyan armor', (SUIT, 30, 0.7, 1.6), (SKIN, 8, 0.8, 1.6))
    o_1 = n1['o_s1'] if donor is None else F.place(base, s1_raw, "the donor's golden head on this frame's", (GOLDC, 60, 0.95, 1.15), (F.cls(SKIN_S, EYES_S), 8, 0.8, 1.6))
    s1 = F.shift(s1_raw, *o_1); s2 = F.shift(s2_raw, o_1[0] + o_2[0], o_1[1] + o_2[1])
    if n1.get('plain'):
        if donor is not None or GOLDC[s2].any(): raise Off('r56 shows the base look here and r55 does not')
        return base, dict(n1, o_2=o_2, o_donor=None, donor=None, fills3=0, left2=0, miss=0, like=0, s2=s2, s1=s1, placed2=n1['placed'])
    h1, h2 = head_of(s1), head_of(s2)
    miss = int((h1 & (base != s1)).sum() + (GOLDC[base] & ~GOLDC[s1]).sum()) if donor is not None else 0      # the donor's Super Saiyan head against this frame's
    if loose:
        # (where no donor passes that: its head only (its gold and the face that hangs together with it), and only where this frame shows
        # its own head, not his body in front of it. Flying, his hands are beside his head and his collar under it: counted, they turned
        # every donor away.)
        front = (base != 0) & ~n1['placed'] & ~GOLDISH[base]
        miss = int((head_only(s1) & (base != s1) & ~front).sum() + (GOLDC[base] & ~GOLDC[s1]).sum())
    if miss > MAX_MISS: raise Off("the donor's golden head is another drawing (%d pixels)" % miss)
    rect = n1['rect']
    if GOLDC[s2].any(): r2 = head_rect(n1['a'], s2); rect = (min(rect[0], r2[0]), max(rect[1], r2[1]), min(rect[2], r2[2]), max(rect[3], r2[3]))
    ch = (s1 != s2) & box_of(s1.shape, rect, 1, 1) & ~ground(get('P', k, d, f))
    head = ch & h2
    mine = (base == s1) | (base == 0) | GOLDISH[base] | n1['filled']
    out = base.copy(); out[head & mine] = s2[head & mine]
    # What the first head lay over and the second doesn't: the purple frame's own pixel where it has one that is no hair (a raised
    # shoe behind a spike of the first hair), else nothing, or the body the second armor frame shows there.
    pf = get('P', k, d, f); back = ch & ~(head & mine) & h1 & (base == s1) & (pf != 0) & ~n1['hair']
    out[back] = pf[back]
    gone = ch & (s2 == 0) & h1 & ((base == s1) | GOLDC[base]) & ~back
    out[gone] = 0
    body = ch & ~head & (s2 != 0) & h1 & (base == s1) & ~back
    fills = body_fill(out, body, s2, n1['a'], n1['short'], ~(ch | n1['filled']) & ~GOLDISH[base])
    stray = GOLDC[out] & ~GOLDC[s2]                       # gold of the first head that the second hasn't (a donor's strand)
    out[stray] = 0
    mend(out, get('P', k, d, f), s2, n1['short'], ~(ch | n1['filled']) & ~GOLDISH[base], n1['a'])
    left = ch & ~(head & mine) & ~gone & ~body & (h1 | head)
    own = get('S2', k, d, f); like = 0
    if donor is not None and own is not None: like = F.witness(own, s2, GOLDC)[1]       # how much of r55's own head for this frame the donor's is
    return out, dict(n1, o_2=o_2, o_donor=o_1 if donor is not None else None, donor=donor, fills3=fills, left2=int(left.sum()), miss=miss, like=like, s2=s2, s1=s1,
                     filled=n1['filled'] | body, placed2=(head & mine))
_own = {}
def best2(k, d, f):
    """Frame (k, d, f) of the purple gi as a Super Saiyan 2. -> (canvas, notes)"""
    try: return ss2(k, d, f)
    except Off as e: first = e
    own_raw = get('S2', k, d, f)
    if own_raw is not None and f != 0:        # r55 places the frames of one animation itself: where the first frame's head sits, this one's sits
        if (k, d) not in _own:
            try: best2(k, d, 0)
            except Off: pass
        if (k, d) in _own:
            base, n1 = ss(k, d, f)
            return own_on(base, dict(n1, o_2=(0, 0), o_donor=None, donor='frame 0', fills3=0, left2=0, miss=0, like=0), own_raw, _own[k, d], head_of(n1['s']) & (base == n1['s']))
    found = []
    for k2, f2 in DONORS:
        if (k2, f2) == (k, f): continue
        try: found.append(ss2(k, d, f, (k2, f2)))
        except Off: continue
    if not found: raise Off('no frame of r55 fits (its own: %s)' % first)
    out, n = min(found, key=lambda v: (v[1]['miss'], -v[1]['like']))   # the same golden head; of those, the one most like r55's own head here
    if own_raw is None: return out, n
    try: o = F.place(out, own_raw, "r55's own head on the donor's", (GOLDC, 60, 0.85, 1.15))
    except Off: return out, n                 # r55's own head here is another drawing altogether: the donor's stays
    if f == 0: _own[k, d] = o
    return own_on(out, n, own_raw, o, ((head_of(n['s2']) | head_of(n['s'])) & CORE[out]) | GOLDC[out])
def best2_checked(k, d, f):
    """best2's frame where it passes check(); else the donors again, each head judged by itself only (ss2 loose), the nearest first, the
    first that passes check(). (The frames best2 made before keep their donors: only frames it couldn't make, or made wrong, look again.)"""
    try:
        out, n = best2(k, d, f)
        if not check(k, d, f, out, n, True): return out, n
        first = Off('; '.join(check(k, d, f, out, n, True)))
    except Off as e: first = e
    found = []
    for k2 in range(20):
        if one_view('P', k2) != one_view('P', k) and d: continue
        for f2 in range(L.nframes(REC['S2'], k2)):
            if (k2, f2) == (k, f): continue
            try: found.append(ss2(k, d, f, (k2, f2), loose=True))
            except Off: continue
    own_raw = get('S2', k, d, f); why = []
    for out, n in sorted(found, key=lambda v: (v[1]['miss'], -v[1]['like'])):
        if n['miss'] > MAX_MISS: break
        if own_raw is not None:            # r55's own head for the frame, where it lies on the donor's (as best2 does)
            try:
                o = F.place(out, own_raw, "r55's own head on the donor's", (GOLDC, 60, 0.85, 1.15))
                o2, n2 = own_on(out, n, own_raw, o, ((head_of(n['s2']) | head_of(n['s'])) & CORE[out]) | GOLDC[out])
                bad = check(k, d, f, o2, n2, True)
                if not bad: return o2, n2
                why.append('donor %s with its own head: %s' % (n['donor'], '; '.join(bad)))
            except Off as e: why.append(str(e))
        bad = check(k, d, f, out, n, True)
        if not bad: return out, n
        why.append('donor %s: %s' % (n['donor'], '; '.join(bad)))
    try:
        out, n = swap2(k, d, f); bad = check(k, d, f, out, n, True)
        if not bad: return out, n
        why.append('the Super Saiyan 2 head of a made frame: %s' % '; '.join(bad))
    except Off as e: why.append(str(e))
    raise Off('no frame of r55 fits (first: %s; %s)' % (first, ' | '.join(why[:4])))
def swap2(k, d, f):
    """The last way to a Super Saiyan 2 frame, for a pose r55 never draws and no donor of its fits (the power-up's arms up, where the
    Super Saiyan head stands squeezed between his fists; the flinch from behind, his hands on his head): this frame's Super Saiyan head
    swapped for the Super Saiyan 2 head of an approved frame of the same view whose Super Saiyan head is this one, by its face (or, from
    behind, by its gold), the most alike first. Only over what this frame shows of its head and the air round it: his arms and hands stay
    in front of it."""
    base, n1 = ss(k, d, f)
    if n1.get('plain') or not GOLDC[base].any(): raise Off('no golden head to swap')
    whole = head_only(base)
    mine = whole & (n1['placed'] | GOLDISH[base])                      # this frame's own head, as made
    face = F.cls(SKIN_S, EYES_S); cls = face if F.cls(EYES_S)[np.where(whole, base, 0)].any() else GOLDC
    if cls is face:                                                     # (with a face: the head is the columns its hair and eyes take,
        xs = np.where((GOLDC | F.cls(EYES_S))[np.where(whole, base, 0)].any(0))[0]     # his fists and arms beside it are not)
        span = np.zeros(base.shape, bool); span[:, xs.min():xs.max() + 1] = True
        mine = whole & span
    best = None
    for k2 in APPROVED2:
        if one_view('P', k2) != one_view('P', k) and d: continue
        for f2 in range(L.nframes(REC['P'], k2)):
            if (k2, f2) == (k, f): continue
            try: r1, r2 = frame('ss', k2, d, f2), frame('ss2', k2, d, f2)
            except Off: continue
            h1 = np.where(head_only(r1) & (F.grown(F.cls(EYES_S)[r1], 3) if cls is face else True), r1, 0)    # (by the face: round the eyes only, never
            o, eq, meet, nxt = F.witness(np.where(whole, base, 0), h1, cls)                                     # the hands beside it)
            if eq < 8 or eq < 0.7 * meet or eq < 1.3 * nxt: continue
            if best is None or eq / meet > best[0]: best = (eq / meet, (k2, f2), o, r1, r2)
    if best is None: raise Off('no approved Super Saiyan 2 frame has this Super Saiyan head')
    _, don, o, r1, r2 = best
    r1, r2 = F.shift(r1, *o), F.shift(r2, *o)
    h2 = head_only(r2)
    out = base.copy()
    out[mine & GOLDISH[base]] = 0                                       # the first head's hair (gold and its outline) goes
    put = h2 & ((base == 0) | mine)                                     # the second head over his head and the air round it, never over
    out[put] = r2[put]                                                  # his body in front of it
    for a, b in ((0x40, 0x31), (0x41, 0x32)): out[mine & ~put & (out == a)] = b     # (an eye of the first head left: the second's green)
    # A frame is one piece of at most 32 rows (fit_rows). Where the first head already took them all (the power-up's arms up: his fists
    # stand at the top of his hair), the second's taller hair stops where the first's did, its gold left bare there outline, as fit_rows
    # leaves it: rows of hair taken from over his face would have squeezed his fists with them.
    ys = np.where((out != 0).any(1))[0]
    if ys.max() - ys.min() + 1 > ROWS:
        top = max(np.where((base != 0).any(1))[0].min(), ys.max() - ROWS + 1)
        cut = np.zeros(out.shape, bool); cut[:top] = True
        fists = np.where(((base != 0) & ~whole).any(1))[0].min()       # (over his fists the second hair stands only where the first did)
        cut[:fists] |= (base == 0)[:fists]
        if (cut & (out != 0) & ~put).any(): raise Off('too tall, and not by the second head alone')
        out[cut] = 0
        e = out == 0; bare = GOLDC[out] & (F.shift(e, 1, 0) | F.shift(e, -1, 0) | F.shift(e, 0, 1) | F.shift(e, 0, -1))
        out[bare & F.grown(cut, 1)] = 0x14
    return out, dict(n1, s2=r2, s1=r1, donor='made frame %s' % (don,), o_donor=o, miss=0, like=0, fills3=0, left2=0, o_2=(0, 0),
                     placed2=put, filled=n1['filled'])
def own_on(out, n, own_raw, o, was):
    """r55's own head for the frame at offset o, in place of the head pixels `was` on the canvas."""
    own = F.shift(own_raw, *o); ho = head_of(own)
    new = out.copy()
    over = was & ~ho                                               # what the donor's head had beyond r55's own
    new[over & (own == 0)] = 0
    # Where r55 draws its armor there, the pixel is not this frame's body: r55 stands another way (that is why its head comes by
    # itself). The outline the head had there stays (the back of his neck); gold goes, and what this pose's own armor frame has
    # under it comes as gi. (Taken from r55, its shoulder strap stood as a purple collar behind his neck in the side stance.)
    arm = over & SUIT[own] & GOLDC[out]
    new[arm] = 0
    under = arm & SUIT[n['a']]
    body_fill(new, under, n['a'], n['a'], n['short'], ~(was | ho | n['filled']) & ~GOLDISH[out])
    ok = (ho & ((out == 0) | was | HAIRB[out] | n['filled'] | (out == own))) | (over & (own != 0) & ~SUIT[own])
    new[ok] = own[ok]
    mend(new, n['p'], own, n['short'], ~(was | ho | n['filled']) & ~GOLDISH[out], n['a'])
    return new, dict(n, o_own=o, own_changed=int((new != out).sum()), s2=own, filled=n['filled'] | under)
def check(k, d, f, out, n, two):
    """What is wrong with a finished frame (nothing, if it is right): the face off the place the purple frame has it; black hair left
    over; a hole the head it came from hasn't; nothing under the chin where the purple frame had his neck."""
    p = get('P', k, d, f); bad = []
    if n.get('plain'): return [] if (out == p).all() else ['the base look is not the purple frame']
    src = n['s2'] if two else n['s']
    hs = head_of(src); gold = GOLDC[src]
    rect = head_rect(n['a'], src) if gold.any() else n['rect']        # (the second form's hair stands higher than the first's)
    box = lambda down=0, side=0: box_of(p.shape, rect, down, side)
    hb = box(1)
    o, eq, meet, nxt = F.face_at(p, np.where(hb, out, 0), SKIN)
    faces = int((SKIN[out] & hb).sum())
    # (the face where the purple frame has it: half its skin on the purple frame's, or, where r56 draws that face another way (the charged
    # hit's leap), twice as much as anywhere else)
    if faces >= 10 and (o != (0, 0) or (eq * 2 < meet and eq < 2 * nxt) or eq <= nxt): bad.append('the face is at %+d%+d (%d of %d skin pixels equal, next %d)' % (*o, eq, meet, nxt))
    # Black hair left over, looked for in ways that don't lean on the mask the hair was taken with: black where the Super Saiyan armor
    # frame draws nothing within two pixels; black in or beside the new head that that frame hasn't there; black that the two armor
    # records say is long hair. His shadow and the shoes on it are his own.
    feet = ground(p); near = F.grown(F.flood(gold, hs, True), 4) if gold.any() else box(4, 4)
    # (where the head came from another frame of r55's, a donor standing another way, his body is where this frame's own Super Saiyan armor
    # frame draws it: flying, his shoes trail behind him where the donor has nothing, and they are no hair)
    body = (src != 0) | (n['s'] != 0) if n.get('donor') else src != 0
    old = HAIRB[out] & ~feet & ((HAIRB[p] & ~F.grown(body, 2)) | (~HAIRB[src] & near & hb & ~inner(p)) | n['both'])     # (a shoe held up beside his face is no hair)
    if get('AL', k, d, f) is None:            # (the charged hit's leaps: his shoe over his head, the black beside its greys, is no hair)
        old &= ~(HAIRB[p] & (out == p) & F.grown(socks(p, np.zeros(p.shape, bool)), 2))
    if old.sum(): bad.append('%d pixels of the black hair are left' % old.sum())
    lost = (feet | ((inner(p) | (HAIRB[p] & F.grown(socks(p, box(2)), 1))) & ~n['both'])) & (out != p)  # (flying, his hair streams back over his heels: the armor records say so)
    lost &= ~(hs & (out == src))                                    # (a spike of the new hair in front of a raised shoe, as its own frame draws it)
    if lost.sum(): bad.append('%d pixels of his shoes or shadow changed' % lost.sum())
    body = (out != p) & ~(box(3) | n['hair'] | n['filled'])
    if body.sum(): bad.append('%d pixels of the body changed away from the head' % body.sum())
    gap = (n['s'] != 0) & ~HAIRB[n['s']] & ~F.grown(out != 0, 2)    # (the first form's frame: the pose is this one's, and the two records'
                                                                    # bodies sit within two pixels of each other; their shadows needn't)
    if gap.sum() >= 3: bad.append('%d pixels of his body are missing (the armor frame draws him there, this one nothing near)' % gap.sum())
    cloth = (GIC | NEUTRAL)[out] & hb & ~(GIC | NEUTRAL)[p] & ~n['filled'] & ~hs & ~(HAIRB[out] & HAIRB[n['a']])
    if cloth.sum(): bad.append('%d pixels of gi or grey at the head that neither the purple frame nor the new head has' % cloth.sum())
    # Armor left in the purple gi: a colour that neither the purple frame nor the new head has and no skin, gi or wristband is (a
    # strap's yellow); and plate (white, grey) in the body that was under his hair with no white, grey or shoe of the purple frame's
    # own beside it and no streak of its own leading to it (the back plate's greys in the middle of his back).
    known = np.zeros(256, bool); known[np.unique(p)] = True; known[np.unique(src[hs])] = True
    odd = (out != 0) & ~known[out] & ~(GIC | FACE | RED)[out]
    if odd.sum(): bad.append('%d pixels in colours of the armor (%s)' % (odd.sum(), ', '.join('%02x' % c for c in np.unique(out[odd]))))
    own = (RIM[p] | (HAIRB[p] & (out == p))) & ~n['hair']           # the purple frame's own whites and greys, and the black of his shoes
    plate = n['filled'] & PLATE[out] & ~hs & ~F.grown(own, 1) & ~F.flood((p == 0x02) & (out == 0x02), out == 0x02, True)
    if plate.sum(): bad.append('%d pixels of armor plate are left in his body' % plate.sum())
    e = out == 0
    wisp = GIC[out] & ~GIC[p] & ((F.shift(e, 0, 1) & F.shift(e, 0, -1)) | (F.shift(e, 1, 0) & F.shift(e, -1, 0)))
    if wisp.sum() >= 2: bad.append('%d pixels of gi stand one pixel wide in the air (a streak or a strap taken for his body)' % wisp.sum())
    new_holes = F.holes(out) & ~F.holes(src) & ~F.holes(p) & (src != 0)
    if new_holes.sum(): bad.append('%d holes' % new_holes.sum())
    # A speck of gi in his hair (a strap of r55's armor beside its own head turned to gi over his hair, the charged hit's leap from behind,
    # Nov 14): gi with no gi beside it and nothing round it but hair, white and the air, and none of the purple frame's gi within a pixel.
    gi = GIC[out]; body = (out != 0) & ~(GOLDC | F.cls({0x14, 0x02}))[out] & ~gi
    alone = gi & ~(F.shift(gi, 1, 0) | F.shift(gi, -1, 0) | F.shift(gi, 0, 1) | F.shift(gi, 0, -1)) & ~F.grown(body, 1) & ~F.grown(GIC[p], 1)
    if alone.sum(): bad.append('%d specks of gi by themselves' % alone.sum())
    if two:
        # His eyes where the Super Saiyan frame of the pose has them (within two pixels): a head that came by another frame's offset and
        # lay a few rows low covered his face with hair (the flinch, his hands on his head, Nov 14), and too little skin showed for the
        # face test.
        one = frame('ss', k, d, f) if k in ANIMS['ss'] else ss(k, d, f)[0]
        e1, e2 = np.argwhere(EYES[one]), np.argwhere(EYES[out])
        if len(e1) >= 2 and (not len(e2) or np.abs(e1.mean(0) - e2.mean(0)).max() > 2):
            bad.append('his eyes are not where the Super Saiyan frame has them (%d of %d)' % (len(e2), len(e1)))
    ys = np.where(SKIN[out] & box(2))[0]
    if len(ys):
        y = ys.max(); cols = np.where(SKIN[out][y] & box(2)[y])[0]
        gap = [x for x in cols if out[y + 1, x] == 0 and p[y + 1, x] != 0 and not n['hair'][y + 1, x]]
        if gap: bad.append('nothing under the chin at %d columns' % len(gap))
    return bad
# What the build uses of LoG2's animations (sprites.py: actors.json _slots and the two figures' own in build.py): every animation a slot of
# the purple figure plays, for both forms (Nov 14, the owner: "fix all those not used frames cause its probably his kamehameha and masenko
# and ki blast and shit never do that again"). Until then the Super Saiyan 2 figure had no power-up (11: the Masenko's arms up and the
# change into it showed his stance), no flight (12) and neither form the charged hit (16) or the flinch (4), which r55 or r52 never draw:
# best2_checked and bare_place make them now. (LoG2's 9, 14, 17 and 18, the change, the hands-together charge, the halo and the record's
# own firing pose, are played by no slot of his.)
ANIMS = {'ss': (0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 16), 'ss2': (0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 16)}
APPROVED = (0, 1, 2, 3, 5, 6, 7, 8, 11, 12, 13)     # the Super Saiyan animations the owner approved on Nov 11
APPROVED2 = (0, 1, 2, 3, 5, 6, 7, 8, 13)     # the Super Saiyan 2 animations the owner approved on Nov 11: swap2 takes its heads from these only
MAKERS = {'ss': lambda k, d, f: ss(k, d, f), 'ss2': lambda k, d, f: best2_checked(k, d, f)}
ROWS = 32                                    # a fighter's frame is one piece of at most 32 rows (1 KB of sprite memory)
def fit_rows(out, p):
    """A finished frame over 32 rows, made to fit. (In one frame, the side view of the second combo's lunge, the purple record holds
    his head two pixels higher than the armor records do, and the golden hair stands taller than the black: 34 rows from the tips
    of his hair to the bottom of his shadow.) Rows of his hair go, one at a time: of the rows over his face, the one whose loss
    shows least (it is most like the row under it, and the rows it parts are most alike). Gold left bare at the edge becomes
    outline, as in every frame LoG2 draws. His face, neck, body and shadow are as they were. Off if it can't be done so."""
    ys = np.where((out != 0).any(1))[0]; over = ys.max() - ys.min() + 1 - ROWS
    if over <= 0: return out
    new = out.copy(); core = F.cls(SKIN_S, EYES_S)
    for _ in range(over):
        top = np.where((new != 0).any(1))[0].min(); face = np.where(core[new].any(1))[0].min()        # the first row with skin or an eye
        if face - top < 6: raise Off('%d rows too high, and too little hair over the face to take them from' % over)
        cost = {y: int((new[y] != new[y + 1]).sum()) + int((new[y - 1] != new[y + 1]).sum()) for y in range(top + 1, face - 1)}
        y = min(cost, key=lambda v: (cost[v], v))
        new[top + 1:y + 1] = new[top:y]; new[top] = 0
    e = new == 0; bare = GOLDC[new] & (F.shift(e, 1, 0) | F.shift(e, -1, 0) | F.shift(e, 0, 1) | F.shift(e, 0, -1))
    new[bare] = 0x14
    face = np.where(core[new].any(1))[0].min()
    if (new[face:] != out[face:]).any(): raise Off('fitting the rows changed him under his hair')
    return new
_made = {}
EYES = F.cls(EYES_S)
def still2(d, f):
    """Frame f of the Super Saiyan 2 stance, view d: frame 0 with only the Super Saiyan stance's blink (Nov 14, the owner: "Why is his ssj2
    hair moving in idle frames"). r55 waves the hair from frame to frame; the Super Saiyan and base stances only blink. Where frame f of
    the Super Saiyan stance differs from its frame 0 (his eyes shut, nothing else), the pixels of the second head's eyes (the green and the
    whites and greys beside it) take frame f's. Off if the Super Saiyan stance changes anything but the eyes."""
    out = frame('ss2', 0, d, 0).copy(); a, b = frame('ss', 0, d, 0), frame('ss', 0, d, f)
    blink = a != b
    if (blink & ~F.grown(EYES[a] | EYES[b], 1)).any(): raise Off('Teen Gohan ss stance, view %d frame %d: changes more than the eyes' % (d, f))
    eye = blink & (EYES[out] | (NEUTRAL[out] & F.grown(EYES[out], 1)))
    out[eye] = b[eye]
    return out
def frame(form, k, d, f):
    """Frame (k, view d, f) of `form` ('ss' or 'ss2'), made and checked: -> its canvas. Off if it can't be made right."""
    if form == 'ss2' and k == 0 and f > 0:
        if ('still', d, f) not in _made: _made['still', d, f] = still2(d, f)
        return _made['still', d, f]
    if (form, k, d, f) not in _made:
        try: out, n = MAKERS[form](k, d, f)
        except Off as e: raise Off('Teen Gohan %s, animation %d view %d frame %d: %s' % (form, k, d, f, e))
        bad = check(k, d, f, out, n, form == 'ss2')
        if bad: raise Off('Teen Gohan %s, animation %d view %d frame %d: %s' % (form, k, d, f, '; '.join(bad)))
        if k not in (APPROVED if form == 'ss' else APPROVED2): out = marks(out, get('P', k, d, f))
        try: _made[form, k, d, f] = fit_rows(out, get('P', k, d, f))
        except Off as e: raise Off('Teen Gohan %s, animation %d view %d frame %d: %s' % (form, k, d, f, e))
    return _made[form, k, d, f]
def marks(out, p):
    """The purple frame's dizzy stars and sweat marks (pieces of white of at most six pixels, with nothing round most of them) in front
    of the new head where its hair lay over them (Nov 14: the second head's bigger hair had covered the flinch's stars in some frames
    and not in others). Only the animations made since Nov 14: the approved ones stay as they were."""
    out = out.copy(); lab = pieces(p != 0); size = np.bincount(lab.ravel())
    for i in range(1, lab.max() + 1):
        m = lab == i
        if size[i] > 6 or not (p[m] == 0x02).all(): continue
        ring = F.grown(m, 1) & ~m
        if (p[ring] == 0).sum() * 2 < ring.sum(): continue
        put = m & ((out == 0) | GOLDISH[out]); out[put] = 0x02
    w = pieces(p == 0x02)                                     # (and white the purple frame draws beside his long hair, nothing else)
    for i in range(1, w.max() + 1):
        m = w == i; ring = F.grown(m, 1) & ~m
        if m.sum() > 6 or (ring & (p != 0) & ~HAIRB[p]).any() or not (p[ring] == 0).any(): continue
        put = m & ((out == 0) | GOLDISH[out]); out[put] = 0x02
    return out
def views(k): return 1 if one_view('P', k) else 3
def every():
    """Every frame the build uses, made and checked. -> how many; Off on the first that isn't right."""
    n = 0
    for form in ('ss', 'ss2'):
        for k in ANIMS[form]:
            for d in range(views(k)):
                for f in range(L.nframes(REC['P'], k)): frame(form, k, d, f); n += 1
    return n
def cut(canvas, box):
    """The canvas as one 32x32 piece: -> (pixels, (x, y, 32, 32) from the origin). The piece is the purple frame's own where the new
    head fits inside it, else moved the least that takes the head in. Off if the figure is more than 32 across or high."""
    ys, xs = np.nonzero(canvas)
    if not len(ys): raise Off('an empty frame')
    x0, x1, y0, y1 = xs.min() - OX, xs.max() - OX, ys.min() - OY, ys.max() - OY
    if x1 - x0 >= 32 or y1 - y0 >= 32: raise Off('the figure is %dx%d: over one 32x32 piece' % (x1 - x0 + 1, y1 - y0 + 1))
    px, py = box[0], box[1]
    if box[2] != 32: px = box[0] - (32 - box[2]) // 2
    if box[3] != 32: py = box[1] + box[3] - 32            # (a shorter piece: keep its feet where they are)
    px = min(max(px, x1 - 31), x0); py = min(max(py, y1 - 31), y0)
    return canvas[OY + py:OY + py + 32, OX + px:OX + px + 32].copy(), (px, py, 32, 32)
def made(form):
    """sprites.log2_anim's frame source for the figure: (record, animation, direction, frame) -> (pixels as shown, box as shown); None for
    another record's. An animation of the purple record that isn't in ANIMS stops the build (it would be the purple record's own frames,
    long black hair: actors.json gives the figures none). Direction 3 (facing right) is the side view mirrored, as the purple record shows it: its entry is the side view's pixels
    with the mirror flag (checked here), and the game stores a mirrored frame's box where it is shown (x = 16 - w - x)."""
    def source(rec, k, d, f):
        if rec != REC['P']: return None
        if k not in ANIMS[form]: raise Off('Teen Gohan %s: a slot asks for the purple record\'s animation %d, which teen.py doesn\'t make' % (form, k))
        v = min(d, views(k) - 1); box = L.raw(REC['P'], k, v, f)[:4]
        px, (x, y, w, h) = cut(frame(form, k, v, f), box)
        a2, a = (L.raw(REC['P'], k, e, f)[5] & 0x10000000 for e in (v, d))
        if v == d or views(k) == 1:
            if a: raise Off('Teen Gohan %s, animation %d direction %d frame %d: the purple record mirrors it' % (form, k, d, f))
            return px, (x, y, w, h)
        r2, r3 = L.raw(REC['P'], k, v, f), L.raw(REC['P'], k, d, f)
        if d != 3 or a2 or not a or not np.array_equal(r3[4], r2[4][:, ::-1]) or (r3[0], r3[1]) != (16 - r2[2] - r2[0], r2[1]):
            raise Off('Teen Gohan %s, animation %d direction %d frame %d: not the side view mirrored in the purple record' % (form, k, d, f))
        return px[:, ::-1], (16 - w - x, y, w, h)
    return source
# The Saiyan armor's Super Saiyan 2 stance (Nov 12, the owner: "noticed SSJ2 Teen Gohan idle pose his hands are raised up instead of
# down, if you can fix that to standard"): r55's idle stands with his arms out and the hands up at his hips; the armor's Super Saiyan
# (r56) stands with them down. The Super Saiyan stance with r55's own head for the frame: placed on it by the face (skin and eyes), the
# first head's gold gone, the second head's gold, its outline, face and eyes (what hangs together with its gold above the shoulders) on.
def head_only(c):
    """The head of an armor frame: its gold and the face and outline that hang together with it, no lower than 7 rows under the gold."""
    gold = GOLDC[c]
    if not gold.any(): return gold
    gy = np.where(gold.any(1))[0]; near = np.zeros(c.shape, bool); near[:gy.max() + 7] = True
    h = F.flood(gold, CORE[c] & near, True)
    return h | F.ringed(NEUTRAL[c] & ~h, h)
def armor_ss2_idle(d, f):
    """Frame f, view d of the armor's Super Saiyan 2 stance. -> canvas. Off if it can't be made right."""
    s1, s2_raw = get('S1', 0, d, f), get('S2', 0, d, f)
    if s1 is None or s2_raw is None: raise Off('no frame')
    # By the face: the two records draw it a little differently (r55's is shouting), so the offset whose skin and eyes agree most, and
    # it must be within a pixel of where the records put it (they place their frames alike). From behind, no face: where they put it.
    o, eq, meet, nxt = F.witness(s1, np.where(head_only(s2_raw), s2_raw, 0), F.cls(SKIN_S, EYES_S), 2)
    if meet < 8: o = (0, 0)
    elif abs(o[0]) > 1 or abs(o[1]) > 1 or eq <= nxt: raise Off("r55's head doesn't sit on r56's stance (%+d%+d, %d of %d, next %d)" % (*o, eq, meet, nxt))
    s2 = F.shift(s2_raw, *o); h1, h2 = head_only(s1), head_only(s2)
    out = s1.copy()
    out[h1 & ~h2 & (GOLDC | BROWN)[s1]] = 0           # the first head's hair (gold, and its brown outline) where the second has none
    out[h2] = s2[h2]
    bad = []
    if (GOLDC[out] & ~h2).sum(): bad.append('%d pixels of the first head\'s gold are left' % (GOLDC[out] & ~h2).sum())
    lost = (s1 != 0) & ~(h1 | h2) & (out != s1)
    if lost.sum(): bad.append('%d pixels of the body changed' % lost.sum())
    new_holes = F.holes(out) & ~F.holes(s1) & ~F.holes(s2)
    if new_holes.sum(): bad.append('%d holes' % new_holes.sum())
    if bad: raise Off('Teen Gohan armor Super Saiyan 2 stance, view %d frame %d: %s' % (d, f, '; '.join(bad)))
    return out
BROWN = F.cls(BROWN_S)
def armor2():
    """sprites.log2_anim's frame source for the armor's Super Saiyan 2 figure (actors.json gohan_armor_ss2_art): its stance (r55's
    animation 0) made by armor_ss2_idle, in r55's own box for the frame (moved to take the head in); every other frame r55's own (None)."""
    def source(rec, k, d, f):
        if rec != REC['S2'] or k != 0: return None
        nv = 1 if one_view('S2', 0) else 3
        v = min(d, nv - 1); box = L.raw(REC['S2'], 0, v, f)[:4]
        px, (x, y, w, h) = cut(armor_ss2_idle(v, f), box)
        a2, a = (L.raw(REC['S2'], 0, e, f)[5] & 0x10000000 for e in (v, d))
        if v == d or nv == 1:
            if a: raise Off('Teen Gohan armor Super Saiyan 2 stance, direction %d frame %d: r55 mirrors it' % (d, f))
            return px, (x, y, w, h)
        r2, r3 = L.raw(REC['S2'], 0, v, f), L.raw(REC['S2'], 0, d, f)
        if d != 3 or a2 or not a or not np.array_equal(r3[4], r2[4][:, ::-1]) or (r3[0], r3[1]) != (16 - r2[2] - r2[0], r2[1]):
            raise Off('Teen Gohan armor Super Saiyan 2 stance, direction %d frame %d: not the side view mirrored in r55' % (d, f))
        return px[:, ::-1], (16 - w - x, y, w, h)
    return source
if __name__ == '__main__':
    import os
    from PIL import Image, ImageDraw
    sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
    use(open(os.environ['BFU_COMBO'], 'rb').read()[0x800000:])
    out = sys.argv[1]; Z = int(sys.argv[2]); ks = [int(a) for a in sys.argv[3:]]
    rows = []; labels = []; problems = 0
    for k in ks:
        for d in range(1 if one_view('P', k) else 3):
            cells = []
            for f in range(L.nframes(REC['P'], k)):
                p = get('P', k, d, f); cells.append(L.rgb(p[32:82, 28:70]))
                for name, fn in (('SS ', ss), ('SS2', best2)):
                    if name == 'SS2' and k not in ANIMS['ss2']: cells.append(np.zeros((50, 42, 3), np.uint8)); continue
                    try:
                        c, n = fn(k, d, f); bad = check(k, d, f, c, n, name == 'SS2'); problems += bool(bad)
                        extra = '' if name == 'SS ' else ' | 2: %+d%+d donor %s%s fills %d left %d miss %d%s' % (
                            *n['o_2'], n['donor'] or 'own', ' %+d%+d' % n['o_donor'] if n['o_donor'] else '', n['fills3'], n['left2'], n['miss'], ' own head %+d%+d' % n['o_own'] if 'o_own' in n else '')
                        print('anim %2d view %d frame %d %s: long %+d%+d short %+d%+d ss %+d%+d fills %d+%d left %d%s%s' % (
                            k, d, f, name, *n['o_long'], *n['o_short'], *n['o_ss'], n['fills'], n['fills2'], n['left'], extra, ' || WRONG: ' + '; '.join(bad) if bad else ''))
                    except Off as e: c = None; problems += 1; print('anim %2d view %d frame %d %s: OFF %s' % (k, d, f, name, e))
                    cells.append(L.rgb(c[32:82, 28:70]) if c is not None else np.zeros((50, 42, 3), np.uint8))
            rows.append(np.concatenate(cells, 1)); labels.append('anim %d view %d: per frame purple | SS | SS2' % (k, d))
    w = max(r.shape[1] for r in rows); rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0))) for r in rows]
    im = Image.fromarray(np.concatenate(rows, 0)); im = im.resize((im.size[0] * Z, im.size[1] * Z), Image.NEAREST); dr = ImageDraw.Draw(im)
    for i, t in enumerate(labels): dr.text((4, i * 50 * Z + 2), t, fill=(255, 255, 0))
    im.save(out); print(out, im.size, 'frames with problems:', problems)
