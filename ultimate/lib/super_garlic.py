"""Super Garlic Jr. (the Garlic Jr. quest's last fight, garlic.py) from Spopovich's frames (BF actor 243).

The owner (Nov 9): "make his brain look right, remove the back spikes, give him his big ears ... make sure his legs look more accurate,
if you gotta use someone else like Spopovich legs and frames try it", then "Remove the singlet too and use the half of his body without the
singlet to duplicate and make most of the other half, fill his abs in perfectly accurate to the art style, and then remove the majin head
symbol and give him the brain grooves instead".

Why Spopovich: the ranked search over BF's big fighters. Yakon (the first base) has one three-quarter figure for every view and spikes on his
back; BF Broly is narrower, has big hair and a teal Broly would show next to BFU's own; Spopovich has real front, back and side frames, the
build of Budokai Tenkaichi 2's artwork of Super Garlic Jr. (a mass of muscle, huge shoulders and arms, a small bald head, a wide stance) and a
roaring power-up with an open red mouth.

What changes, frame by frame (each frame's piece, BF indices, by view):
1. The singlet comes off. Front and back views: every pixel it covered above the waist is copied from the bare side of his body, mirrored
   about the body's own axis (measured per frame: the column that makes his bare skin most symmetric); what the mirror can't give (both
   sides covered, or the mirror off his body) is shaded from the singlet's own light and shade in his skin's ramp. Side views: shaded the
   same way (there is no other half to copy). His chest and abs are then checked by hand (ABS).
2. The head: the Majin mark on his forehead becomes the brain-like grooves of his cranium; big pointed Namekian ears; a snarl.
3. Below the waist: baggy black trousers (the briefs and the thighs, grown from the boots through skin, never across an outline, so a fist
   held in front of the hips stays a fist), a white sash at the waist with its tassel in front, pale teal boots.
4. His skin teal (the artwork's), his eyes white.
"""
import hashlib
import numpy as np
from scipy import ndimage as ndi

# ---- Spopovich's colours (BF OBJ palette indices) ----------------------------------------------------------------------------------
OUT = 16                                                        # his outline (and the deepest creases)
RAMP = (18, 19, 20, 21, 22, 23, 30)                             # his skin, dark -> light (17, 81... are rare darks)
SKIN_ALL = (16, 17, 18, 19, 20, 21, 22, 23, 30, 203, 245, 205, 206, 208, 202, 84, 68, 82, 229, 141, 142, 213)
SING = (1, 111, 112, 113, 114, 115)                             # the singlet: black outline, greys
YELLOW = (109, 249, 81)                                         # his boots
# the singlet's light and shade -> his skin's (where nothing can be copied)
SING_TO_SKIN = {111: 18, 112: 21, 113: 20, 114: 23, 115: 30, 1: 18}


def sha(img):
    return hashlib.sha1(np.ascontiguousarray(img).tobytes()).hexdigest()[:12]


def _edge(m):
    """Pixels of a mask next to something outside it (4-neighbours)."""
    p = np.pad(m, 1)
    return m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])


def _near(m, it=1):
    return ndi.binary_dilation(m, iterations=it)


def parts(img):
    """Masks of a frame: figure, boots (with their soles), the singlet (its big components, not touching the boots), white highlight
    specks inside the skin."""
    fig = img > 0
    yel = np.isin(img, YELLOW)
    boot = _near(yel, 2) & np.isin(img, YELLOW + (114, 115, 118, 119, 2, 120, 16, 1, 111, 112, 113)) & fig
    s = np.isin(img, SING) & ~boot
    lab, n = ndi.label(s)
    sing = np.zeros_like(s)
    if n:
        sizes = ndi.sum(s, lab, range(1, n + 1)); big = max(sizes)
        touch = _near(yel) & ~yel
        for i in range(1, n + 1):
            c = lab == i
            if np.isin(img[c], (111, 112)).sum() < 8: continue
            if (c & touch).any(): boot |= c                       # a sole seen from below
            elif (_near(c) & np.isin(img, SKIN_ALL)).any(): sing |= c       # the singlet (every piece of it: a strap over a shoulder too)
    grey = np.isin(img, (113, 114, 115, 116, 117, 118, 119, 120)) & ~boot & ~sing      # a boot's grey sole, seen from behind
    lab, n = ndi.label(grey, np.ones((3, 3)))
    for i in set(lab[_near(boot) & grey].tolist()) - {0}: boot |= lab == i
    white = np.isin(img, (2, 120))
    lab, n = ndi.label(white)
    face = _near(np.isin(img, (1, 119, 113, 32, 33, 36, 62)))      # eyes, brows, teeth, mouths
    outside = _near(~fig)
    speck = np.zeros_like(white)
    for i in range(1, n + 1):
        c = lab == i
        if c.sum() <= 30 and not (c & outside).any() and not (c & face).any(): speck |= c     # a highlight on his skin
    return fig, boot, sing, speck


def axis(img, bare, rows, near_col):
    """Twice the column of the body's mirror axis: the one (within 6 of near_col) under which most bare skin pixels in `rows` land on
    bare skin of the same shade."""
    H, W = img.shape; best = (-1, 2 * near_col)
    ys, xs = np.nonzero(bare & rows)
    for c2 in range(2 * near_col - 12, 2 * near_col + 13):
        m = c2 - xs; ok = (m >= 0) & (m < W)
        same = bare[ys[ok], m[ok]] & (np.abs(img[ys[ok], m[ok]].astype(int) - img[ys[ok], xs[ok]].astype(int)) == 0)
        score = same.sum()
        if score > best[0]: best = (score, c2)
    return best[1]


def front_axis(img, fig, sing):
    """Twice the mirror axis of a front or back frame, from his chest (the rows from 10 to 30 below the top of his head)."""
    H, W = img.shape; row = np.arange(H)[:, None]
    ys = np.nonzero(fig.any(1))[0]; top = ys.min()
    hx = np.nonzero(fig[top:top + 8].any(0))[0]
    bare = fig & np.isin(img, SKIN_ALL) & ~sing
    return axis(img, bare, (row > top + 10) & (row < top + 30), (hx.min() + hx.max()) // 2)


def front_waist(img, fig, sing, c2):
    """A front or back frame's waist: where the briefs begin on his bare side (the side of his torso the singlet leaves bare), the median
    over the eight columns beside the axis of the first singlet row below his chest."""
    H, W = img.shape
    ys = np.nonzero(fig.any(1))[0]; top = ys.min()
    a = c2 // 2
    sides = []
    for cols in (range(a - 8, a), range(a + 1, a + 9)):
        firsts = []
        for x in cols:
            col = sing[top + 20:, x]
            k = np.nonzero(col)[0]
            if len(k): firsts.append(top + 20 + k[0])
        cover = sing[top + 12:top + 26, list(cols)].sum()
        sides.append((cover, firsts))
    cover, firsts = min(sides, key=lambda s: s[0])
    return int(np.median(firsts)) if firsts else None


def unsinglet(img, view, waist, sing, fig, axis2=None):
    """The singlet above the waist taken off (in his own skin colours). -> (image, twice the mirror axis or None, filled mask)."""
    out = img.copy(); H, W = img.shape
    row = np.arange(H)[:, None]
    torso = sing & (row < waist)
    bare = fig & np.isin(img, SKIN_ALL) & ~sing
    c2 = None
    if view in (0, 1) and torso.any():
        ys = np.nonzero(fig.any(1))[0]; top = ys.min()
        hx = np.nonzero(fig[top:top + 8].any(0))[0]
        rows = (row > top + 10) & (row < waist)
        c2 = axis2 if axis2 is not None else axis(img, bare, rows, (hx.min() + hx.max()) // 2)
    rim = _edge(fig)
    left = torso.copy()
    for y, x in zip(*np.nonzero(torso)):
        if rim[y, x]:
            out[y, x] = OUT; left[y, x] = False; continue
        if c2 is not None:
            m = c2 - x
            if 0 <= m < W and bare[y, m] and not (rim[y, m] and img[y, m] == OUT):
                out[y, x] = img[y, m]; left[y, x] = False
    # the rest: his own skin reflected across the nearest edge of the gap (the muscle texture carries on into it, in his own style)
    src = bare & ~(rim & (img == OUT))
    if left.any() and src.any():
        _, (iy, ix) = ndi.distance_transform_edt(~src, return_indices=True)
        for y, x in zip(*np.nonzero(left)):
            qy, qx = iy[y, x], ix[y, x]
            ry, rx = 2 * qy - y, 2 * qx - x
            if 0 <= ry < H and 0 <= rx < W and src[ry, rx]: out[y, x] = img[ry, rx]
            else: out[y, x] = img[qy, qx]
    return out, c2, torso


# ---- the head ----------------------------------------------------------------------------------------------------------------------
# Drawn over Spopovich's own head, in his skin's letters (then made teal with the rest): o outline/deep groove (16), d shade (18), m (20),
# l (21), h (23), H (30), W highlight (2), K black (1), R red (33), r dark red (32); '.' keeps his pixel, ' ' never drawn.
# Grids are placed at (row, column) of his standing frame (slot 0, frame 0) of that view and move with his head (HEAD_AT, found per frame).
CANVAS = (96, 128)        # every coordinate in this module is on this canvas (scratch review tools draw frames on it too): the frame's
WINDOW = (28, 92, 40, 104)  # origin at row 84, column 64; Spopovich's one 64 x 64 piece (at -16, -48 from it, every frame) covers these rows, columns
LETTER = {'o': 16, 'd': 18, 's': 19, 'm': 20, 'l': 21, 'h': 23, 'H': 30, 'W': 2, 'K': 1, 'R': 33, 'r': 32, '9': 119}
HEAD_BOX = {0: (29, 42, 62, 80), 1: (29, 42, 62, 80), 2: (29, 42, 62, 78)}     # his standing head: rows, columns (the template)
# The brain: Budokai Tenkaichi 2's artwork and the Dead Zone settei give Super Garlic Jr. a bald cranium of stacked folds, like a brain's;
# the Majin mark on Spopovich's forehead (front rows 33-35) goes under them.
GROOVES = {        # (row, column) of the grid's top-left in the standing frame; rows of letters
    0: (30, 64, ['    hHHohlm    ',          # the top fold, the crease between the halves of his brain
                 '   hlooooolm   ',          # the first groove, curving down at the sides
                 '   ooHHhhloo   ',
                 '  hHhlllmmlmd  ',          # the second fold (over the Majin mark)
                 '  Hlooooooomd  ',          # the second groove
                 '  ooHHhhllmoo  ']),       # the brow fold above his eyes
    1: (30, 64, ['    hHHohlm    ',
                 '   hlooooolm   ',
                 '   ooHHhhloo   ',
                 '  hHhlllmmlmd  ',
                 '  Hlooooooomd  ',
                 '  ooHHhhllmoo  ']),
    2: (30, 63, ['   hHHhllm    ',           # in profile the folds run from his brow over his crown and down the back of his skull
                 '  hooooolmd   ',
                 '  HHhhlooodd  ',
                 ' lHhhlllmmood ',
                 'oooooooolmmlo ',
                 ' lHHhhoooodlo ']),
}
# The ears: broad points from his temple to his jaw, tips as high as his crown (Kami's and Piccolo's, as on the artwork). Front and back:
# beside his head, over the background only (what's in front of his head stays in front). Side: the near ear, over his head too.
EAR_L = (30, 56, ['o       ',
                  'oo      ',
                  'oho     ',
                  'ohlo    ',
                  ' ohlo   ',
                  ' ohmlo  ',
                  ' oldmlo ',
                  '  oldml ',
                  '  oldml ',
                  '   oldm ',
                  '    ood ',
                  '     oo '])
EAR_R = (30, 79, [r[::-1].replace('h', 'm').replace('l', 'm') for r in EAR_L[2]])
EARS = {0: [EAR_L, EAR_R], 1: [EAR_L, EAR_R],
        2: [(30, 69, ['          o ',
                      '         oo ',
                      '        oho ',
                      '       ohlo ',
                      '      ohldo ',
                      '     ohldo  ',
                      '    ohldo   ',
                      '   oldmo    ',
                      '   oldo     ',
                      '   oldo     ',
                      '   oddo     ',
                      '    oo      '])]}
EAR_OVER_HEAD = {2}
# The snarl (the artwork's open mouth, red, with fangs): his shut mouth (front row 41, side row 41) opened over his chin.
MOUTH = {0: (41, 69, ['oWrWo',
                      'oRRRo',
                      ' ddd ']),
         2: (41, 63, ['oWr',
                      'oRR',
                      ' dd'])}
MOUTH_SHUT = {0: (41, 71, 3), 2: (41, 64, 3)}                    # where his mouth is shut: only then is the snarl drawn


def _grid_pixels(at, rows):
    y0, x0 = at
    for dy, r in enumerate(rows):
        for dx, ch in enumerate(r):
            if ch not in '. ': yield y0 + dy, x0 + dx, LETTER[ch]


SIDE_FLIP = HEAD_BOX[2][2] + HEAD_BOX[2][3] - 1          # a side head turned the other way: column x -> SIDE_FLIP - x
DOME_ROWS = 9                                             # the cranium and brows: the same in every frame (his face changes; this doesn't)
TRY = {0: (0, 2, '2m'), 1: (1,), 2: (2,)}
SEED = {0: (36, 70), 1: (34, 71), 2: (34, 69)}        # a point of his forehead (back: of the back of his head), standing                 # heads a frame of each view may show (a front frame can turn his face aside)


class Heads:
    """Spopovich's standing heads as templates. find(frame, view) -> (score, kind, dy, dx): kind 0 front, 1 back, 2 side, '2m' side turned
    the other way; (dy, dx) from where that head is in its standing frame. Matched on the cranium and brows (DOME_ROWS), which every frame
    draws the same way, and on the whole head; the better."""

    def __init__(self, standing):
        self.tpl = {}
        for v, f in standing.items():
            y0, y1, x0, x1 = HEAD_BOX[v]
            t = f[y0:y1, x0:x1].copy()
            lab, n = ndi.label(t > 0)
            t = np.where(lab == lab[0:3].max(), t, 0) if n else t      # the head itself (the shoulders below are other pieces)
            self.tpl[v] = (t, y0, x0)
            if v == 2: self.tpl['2m'] = (t[:, ::-1].copy(), y0, x0)

    def _match(self, img, t):
        H, W = img.shape; th, tw = t.shape; ink = np.argwhere(t > 0)
        P = np.zeros((H + 2 * th, W + 2 * tw), np.uint8); P[th:th + H, tw:tw + W] = img
        acc = np.zeros((H + th, W + tw), np.int32)
        for y, x in ink: acc += P[y:y + H + th, x:x + W + tw] == t[y, x]
        j = np.unravel_index(acc.argmax(), acc.shape)
        return acc[j] / len(ink), j[0] - th, j[1] - tw

    def find(self, img, view):
        best = (0, view, 0, 0)
        for kind in TRY[view]:
            t, ty, tx = self.tpl[kind]
            for part in (t, t[:DOME_ROWS]):
                score, y, x = self._match(img, part)
                if kind != view: score -= 0.08                        # his own view's head first
                if score > best[0]: best = (score, kind, y - ty, x - tx)
        return best


def majin(img):
    """(dy, dx) of his head in a front frame from the Majin mark on his forehead (its middle row: black, outline, black, outline, black;
    row 34, columns 69-73 standing), or None. Exact where the matcher is not (his face changes from frame to frame; the mark doesn't)."""
    H, W = img.shape
    for y in range(H):
        r = img[y]
        for x in range(W - 4):
            if r[x] == 1 and r[x + 2] == 1 and r[x + 4] == 1 and r[x + 1] == OUT and r[x + 3] == OUT: return y - 34, x - 69
    return None


def crown(out, base, seed, box, grooves):
    """The brain's folds on the top of his head seen from above (bowed forward): grooves across it at the given rows, a pixel lower at its
    sides, each with its lit fold above it."""
    out = out.copy(); H, W = base.shape; y0, y1, x0, x1 = box
    skin = np.isin(base, [k for k in SKIN_ALL if k != OUT]) | (base == 2)
    inbox = np.zeros((H, W), bool); inbox[y0:y1 + 1, x0:x1 + 1] = True
    lab, n = ndi.label(skin & inbox)
    region = lab == lab[seed]
    xs = np.nonzero(region.any(0))[0]; cx, half = (xs.min() + xs.max()) / 2, (xs.max() - xs.min()) / 2
    for g in grooves:
        for x in range(xs.min(), xs.max() + 1):
            y = g + (1 if abs(x - cx) > half * 0.6 else 0)
            if region[y, x]:
                out[y, x] = OUT
                if region[y - 1, x]: out[y - 1, x] = 30 if x < cx else 23
    return out


def _flip(at, rows):
    """A grid of the side head turned the other way."""
    y0, x0 = at; w = max(len(r) for r in rows)
    return (y0, SIDE_FLIP - (x0 + w - 1)), [r.ljust(w)[::-1] for r in rows]


def head(img, kind, shift, base):
    """His head as Super Garlic Jr.'s: the brain's folds over the Majin mark, the ears, the snarl. kind: which head (Heads.find); shift:
    (dy, dx) from where that head is in its standing frame. base: the frame before any change (to tell his head from what is in front)."""
    out = img.copy(); H, W = img.shape; dy, dx = shift
    v = 2 if kind == '2m' else kind
    fix = (lambda at, rows: _flip(at, rows)) if kind == '2m' else (lambda at, rows: (at, rows))
    headish = np.isin(base, SKIN_ALL + (1, 2, 119, 113))
    y0, y1, x0, x1 = HEAD_BOX[v]
    near_head = np.zeros((H, W), bool); near_head[max(y0 + dy, 0):max(y1 + dy, 0), max(x0 + dx, 0):max(x1 + dx, 0)] = True
    # his head itself: his skin inside his head's outline, from his forehead (a fist or an arm over it has its own outline)
    sy, sx = SEED[v]
    if kind == '2m': sx = SIDE_FLIP - sx
    skin = np.isin(base, [k for k in SKIN_ALL if k != OUT]) | (base == 2)
    lab, n = ndi.label(skin & near_head)
    seeds = [lab[y, x] for y in range(sy + dy - 1, sy + dy + 2) for x in range(sx + dx - 2, sx + dx + 3)
             if 0 <= y < H and 0 <= x < W and lab[y, x]]
    region = np.isin(lab, seeds) if seeds else np.zeros((H, W), bool)
    dome = (region | (_near(region) & np.isin(base, (OUT, 1)))) & near_head
    gy, gx, rows = GROOVES[v]
    at, rows = fix((gy, gx), rows)
    for y, x, c in _grid_pixels((at[0] + dy, at[1] + dx), rows):
        if 0 <= y < H and 0 <= x < W and dome[y, x]: out[y, x] = c
    touch = _near(region, 2)
    for ey, ex, rows in EARS[v]:
        at, rows = fix((ey, ex), rows)
        px = list(_grid_pixels((at[0] + dy, at[1] + dx), rows))
        over = WINDOW[0] - min(y for y, x, c in px)
        if over > 0: px = [(y + over, x, c) for y, x, c in px]      # the piece ends there: the ear sits lower, whole, not cut off
        px = [(y, x, c) for y, x, c in px if 0 <= y < H and 0 <= x < W]
        if sum(touch[y, x] for y, x, c in px) < 3: continue            # an ear only where it meets his head (a turned head hides one)
        for y, x, c in px:
            if base[y, x] == 0 or (v in EAR_OVER_HEAD and dome[y, x]): out[y, x] = c
    if v in MOUTH:
        sy, sx, n = MOUTH_SHUT[v]
        cols = [sx + k for k in range(n)]
        if kind == '2m': cols = [SIDE_FLIP - c for c in cols]
        if all(0 <= sy + dy < H and 0 <= c + dx < W and base[sy + dy, c + dx] == OUT for c in cols):
            my, mx, rows = MOUTH[v]
            at, rows = fix((my, mx), rows)
            for y, x, c in _grid_pixels((at[0] + dy, at[1] + dx), rows):
                if 0 <= y < H and 0 <= x < W: out[y, x] = c
    return out


# ---- below the waist, and the colours ----------------------------------------------------------------------------------------------
# Per frame (sha of Spopovich's piece): what the measuring can't see. 'w': the waist row (the sash's top); 'skin': boxes (y0, y1, x0, x1)
# kept as his body (a hand held low); 'pants': boxes made trousers; 'vertical': the waist is a column (he lies along the frame), legs to the
# right of it; 'head': (dy, dx) of his head when the matcher can't see it, or None for no head in the frame.
FRAMES = {
    '76d1371e5cc7': {'head': None},                     # 4.0.1: bent over a punch, his head hidden behind his shoulder
    'abd10c8e20a2': {'head': (1, (6, 3))},              # 4.3.1: only his crown shows above his shoulder
    '92f7c7af5de4': {'w': 63},                          # 9.1.1: hit, from behind (the briefs begin at row 63 on his bare side)
    '983260400b64': {'vertical': 63},                   # 15.0.2: flying along the frame, his hips at column 63 (the briefs begin there)
    'ec79fe000bc9': {'w': 99, 'pants_sing': [(50, 58, 0, 127)], 'sash': False},     # 15.0.0: flying at you, his hips behind his head
    '7d42d7ea76f5': {'w': 74, 'head': None, 'skin': [(74, 90, 48, 63)],   # 17.2.0: on his knees, bowed: the top of his head between his
                                                        # shoulders, his left fist on the ground beside his boot
                     'crown': {'seed': (72, 70), 'box': (63, 80, 62, 78), 'grooves': (66, 69, 72, 75)}},
}
MIN_HEAD = 0.5
TEAL = {16: 70, 17: 187, 18: 187, 19: 187, 20: 252, 21: 252, 22: 253, 23: 253, 30: 254, 203: 252, 245: 253, 205: 187, 206: 187, 208: 70,
        202: 187, 84: 253, 68: 254, 82: 252, 229: 254, 141: 252, 142: 252, 213: 252}          # his skin -> the artwork's teal
PANTS = {16: 1, 17: 111, 18: 111, 19: 111, 20: 112, 21: 112, 22: 112, 23: 112, 30: 113, 203: 112, 245: 113, 205: 111, 206: 111, 208: 1,
         202: 111, 84: 113, 68: 113, 82: 112, 229: 113, 141: 112, 142: 112, 213: 112, 81: 111, 2: 113,
         1: 1, 111: 111, 112: 112, 113: 112, 114: 113, 115: 113}                               # skin or briefs -> black baggy trousers
BOOTS = {109: 199, 249: 254, 81: 186, 114: 186, 115: 199, 118: 254, 119: 254, 2: 255, 120: 255, 16: 70, 1: 70, 111: 70, 112: 186,
         113: 186}                                                                              # yellow wrestling boots -> pale teal
SASH, SASH_SHADE, SASH_EDGE = 2, 118, 1
TASSEL = [(0, 'W'), (0, 'W'), (0, 'W'), (0, 'WW'), (0, 'W8'), (0, '8')]    # the sash's cord in front, ending in a pointed weight


def waist_of(img, view, fig=None, sing=None, c2=None):
    hand = FRAMES.get(sha(img), {})
    if 'w' in hand: return hand['w']
    if fig is None: fig, _, sing, _ = parts(img)
    if view in (0, 1):
        if c2 is None: c2 = front_axis(img, fig, sing)
        w = front_waist(img, fig, sing, c2)
        if w is not None: return w
    ys = np.nonzero(sing.any(1))[0]
    return ys.max() - 10 if len(ys) else img.shape[0]


def _split(passable, seeds):
    """Every passable pixel to the nearest seed set, walking through passable pixels only (4-neighbours); ties go to the first set.
    seeds: [mask, ...] -> label image (0 = reached by none)."""
    from collections import deque
    lab = np.zeros(passable.shape, np.int8); q = deque()
    for i, m in enumerate(seeds, 1):
        for y, x in zip(*np.nonzero(m & passable)):
            if not lab[y, x]: lab[y, x] = i; q.append((y, x))
    H, W = passable.shape
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < H and 0 <= nx < W and passable[ny, nx] and not lab[ny, nx]:
                lab[ny, nx] = lab[y, x]; q.append((ny, nx))
    return lab


def trousers(img, fig, boot, sing, speck, waist, hand):
    """-> (legs, arms): the trousers, and his arms below the waist.
    Below the waist his skin is shared out by what it belongs to: a wave from his upper body (where his arms cross the waist) and a wave
    from his boots walk through his skin, never across an outline, and each pixel goes to the nearer (an arm first on a tie). The legs'
    share, the briefs, and skin that neither reaches but that hangs from the briefs (a thigh behind a knee's outline) are the trousers.
    The arms' share is never trousers or sash, and nor is its outline."""
    H, W = img.shape; row = np.arange(H)[:, None]; col = np.arange(W)[None, :]
    below = fig & ((col >= hand['vertical']) if 'vertical' in hand else (row >= waist))
    skinish = np.isin(img, [k for k in SKIN_ALL if k != OUT]) | speck
    passable = below & skinish & ~boot
    upper = fig & ~below & skinish & ~sing
    arm_seed = passable & _near(upper)
    leg_seed = passable & _near(boot)
    for y0, y1, x0, x1 in hand.get('skin', ()): arm_seed[y0:y1 + 1, x0:x1 + 1] |= passable[y0:y1 + 1, x0:x1 + 1]
    lab = _split(passable, [arm_seed, leg_seed])
    arms = lab == 1
    legs = (lab == 2) | (sing & below)
    loose = passable & (lab == 0)                                   # reached by neither: a thigh behind a knee's outline, or a lone hand
    clab, n = ndi.label(loose)
    briefs = sing & below
    for i in range(1, n + 1):
        c = clab == i
        if (_near(c) & briefs).sum() >= 2: legs |= c
        else: arms |= c
    for y0, y1, x0, x1 in hand.get('pants_sing', ()):
        box = np.zeros_like(legs); box[y0:y1 + 1, x0:x1 + 1] = True
        legs |= box & sing
    for y0, y1, x0, x1 in hand.get('pants', ()):
        box = np.zeros_like(legs); box[y0:y1 + 1, x0:x1 + 1] = True
        legs |= box & fig & ~boot; arms &= ~box
    rim = _near(legs) & below & np.isin(img, (OUT, 1)) & ~boot & ~legs
    legs |= rim & ~_near(arms)
    return legs & ~arms, arms


def baggy(res, legs, fig, boot, arms):
    """Trousers as cloth: his thighs' muscle lines evened out into broad folds (a 3 x 3 majority of the trousers' shades), and the cloth
    a pixel fuller where it meets the background along the outer seams and where it blouses over the boots."""
    out = res.copy(); H, W = res.shape
    shades = (111, 112, 113)
    inner = legs & ~_edge(legs) & np.isin(res, shades)
    P = np.pad(res, 1)
    for y, x in zip(*np.nonzero(inner)):
        win = P[y:y + 3, x:x + 3].ravel()
        win = win[np.isin(win, shades)]
        if len(win) >= 5:
            vals, cnt = np.unique(win, return_counts=True)
            if cnt.max() >= 5: out[y, x] = vals[cnt.argmax()]
    return out
def convert(img, view, heads):
    """One of Spopovich's frames (his piece, BF indices) as Super Garlic Jr.'s."""
    if not img.any(): return img.copy()
    hand = FRAMES.get(sha(img), {})
    fig, boot, sing, speck = parts(img)
    c2 = front_axis(img, fig, sing) if view in (0, 1) else None
    waist = waist_of(img, view, fig, sing, c2)
    H, W = img.shape; row = np.arange(H)[:, None]; col = np.arange(W)[None, :]
    if 'vertical' in hand:
        above = col < hand['vertical']
        out, c2, torso = unsinglet(img, view, H, sing & above, fig, c2)
    else:
        out, c2, torso = unsinglet(img, view, waist, sing, fig, c2)
    legs, arms = trousers(img, fig, boot, sing, speck, waist, hand)
    # the head
    if 'head' in hand: found = hand['head']
    elif view == 0 and majin(img) is not None: found = (0, majin(img))
    else:
        score, kind, dy, dx = heads.find(img, view)
        found = (kind, (dy, dx)) if score >= MIN_HEAD else None
    if found is not None: out = head(out, found[0], found[1], img)
    if 'crown' in hand: out = crown(out, img, **hand['crown'])
    # the colours
    res = out.copy()
    skin = ~legs & ~boot
    for k, v in TEAL.items(): res[skin & (out == k)] = v
    res[skin & speck] = 254
    for k, v in PANTS.items(): res[legs & (img == k)] = v
    for k, v in BOOTS.items(): res[boot & (img == k)] = v
    res = baggy(res, legs, fig, boot, arms)
    # the sash: the trousers' top two rows (or columns), a black edge where it meets the background
    if 'vertical' in hand:
        x = hand['vertical']; sash = legs & ((col == x) | (col == x + 1)); top = legs & (col == x)
    else:
        sash = legs & ((row == waist) | (row == waist + 1)); top = legs & (row == waist)
    if hand.get('sash', True) is False: sash = top = np.zeros_like(legs)
    res[sash] = SASH_SHADE; res[top] = SASH
    res[sash & _edge(fig)] = SASH_EDGE
    if view == 0 and c2 is not None and 'vertical' not in hand:
        tx = c2 // 2 + 4
        for k, (off, r) in enumerate(TASSEL):
            for j, ch in enumerate(r):
                y, x = waist + 2 + k, tx + off + j
                if 0 <= y < H and 0 <= x < W and legs[y, x]: res[y, x] = {'W': 2, '8': 118}[ch]
    return res



class Converter:
    """For sprites.viewed_actor: (Spopovich's piece, view) -> Super Garlic Jr.'s, through the canvas this module's coordinates are on."""
    ACTOR = 243

    def __init__(self, rom, actor_list):
        import struct, sprites
        u = lambda o: struct.unpack_from('<I', rom, o)[0]
        rec = u(actor_list + 4 * self.ACTOR) - 0x08000000
        stand = u(rec + 0x54) - 0x08000000
        self.heads = Heads({v: self.canvas(sprites.frame_image(rom, u(stand + 4 + 4 * v))) for v in (0, 1, 2)})
        self.done = 0

    @staticmethod
    def canvas(piece):
        c = np.zeros(CANVAS, np.uint8); y0, y1, x0, x1 = WINDOW
        c[y0:y1, x0:x1] = piece
        return c

    def __call__(self, piece, view):
        y0, y1, x0, x1 = WINDOW
        if piece.shape != (y1 - y0, x1 - x0): raise ValueError('super_garlic: Spopovich\'s piece is %s, not 64 x 64' % (piece.shape,))
        self.done += 1
        return convert(self.canvas(piece), view, self.heads)[y0:y1, x0:x1]
