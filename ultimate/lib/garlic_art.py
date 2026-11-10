"""The Garlic Jr. quest's fighters (Nov 9; the project owner: "create the Garlic Jr based off Pilaf/Yakon"), all from Buu's Fury's own
sprites, recoloured or with a head swapped. Colours are the game's own palette entries (no new colours).

Garlic Jr. (Dragon Ball Wiki: "a small, turquoise alien with pointy ears and green spots above his head ... white eyes with small black
pupils ... a burly robe with a white hood ... a black cassock with a gold-colored castle emblem on a red background with a light blue
line ... black pants and blue shoes"). Buu's Fury has no Garlic Jr.; Pilaf (actor 214) is the owner's choice for him (the wiki: "He oddly
resembles Emperor Pilaf"). The closest sources, measured over every BF actor (the sprite skill's ranked search):
  - Pilaf 214: his look and build (a big head on a short body), but only standing, walking and one pose (slots 0, 1, 18);
  - Babidi 19: a small robed figure with a cape, but no fighting: his behaviour stands still (tried in the emulator, Nov 9);
  - Piccolo with the cape and turban 213: cape, ears and 14 fighting slots, but an adult's height: with Garlic Jr.'s head he would be
    35 px tall, past the 32 x 32 frame;
  - kid Goten 114: Pilaf's build (28 px, the head half his height), every fighting slot, and a behaviour (row 39) the post-game
    tournament already uses. Chosen for the body.
So every frame of kid Goten gets: Garlic Jr.'s head in place of Goten's, built on Pilaf's (his face, eyes and mouth from Pilaf's own
frames, read from the ROM; his hat becomes Garlic Jr.'s bald crown with its green spots, drawn here, and the ears grow into his long
pointed ones), facing the way Goten's head faced; Pilaf's white ruff as Garlic Jr.'s white hood and scarf round the neck; the gi as his
black cassock with the red emblem and gold castle on the chest (front); turquoise hands; blue shoes.

Super Garlic Jr. (Yakon, actor 291, the owner's choice: the same hulking build; the wiki: "When in his transformed state, his clothes are
shattered except for his pants and shoes"): Yakon's green as Super Garlic Jr.'s dark teal, his eyes white, his horns the pointed ears'
colour, his legs in dark pants and his clawed feet in blue shoes.

The Spice Boys and the Makyans: recolours of fighters of the same build (spice(), vinegar(), mustard(), salt(), makyan())."""
import hashlib, struct
import numpy as np
from beerus import _components, _touch

BASE = 0x08000000
CELL = (40, 64)                 # frames are drawn on cells this size: the bottom row's middle is the actor's origin (sprites.Inserter.frame)


def actor_cells(rom, actor_list, actor, cell=CELL):
    """{slot: [[cell, ...] for views 0 front, 1 back, 2 side]} of a retail actor, every piece of each frame on a cell (BF indices)."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    rec = u(actor_list + 4 * actor) - BASE; out = {}
    ch, cw = cell
    for slot in range(u(rec) & 0xFF):
        a = u(rec + 0x54 + 4 * slot)
        if not a: continue
        a -= BASE; views = [[], [], []]
        for k in range(u(a)):
            for d in range(3):
                fp = u(a + 4 + 16 * k + 4 * d) - BASE; c = np.zeros(cell, np.uint8)
                for j in range(u(fp)):
                    x, y, w, h = struct.unpack_from('<bbBB', rom, fp + 8 + 12 * j); tp = u(fp + 16 + 12 * j) - BASE
                    t, size = u(tp), u(tp + 4)
                    raw = rom[tp + 8:tp + 8 + size] if t == 0 else bytes(decompress_stream(rom, tp + 8, size)[0])
                    img = np.frombuffer(bytes(raw[:w * h]).ljust(w * h, b'\0'), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
                    Y, X = ch + y - 8, cw // 2 + x - 8            # piece offsets are from the origin + 8 (sprites.Inserter.piece)
                    assert Y >= 0 and X >= 0 and Y + h <= ch + 8 and X + w <= cw, (actor, slot, k, d)
                    m = img > 0
                    sub = c[Y:Y + h, X:X + w]; mm = m[:sub.shape[0], :sub.shape[1]]
                    sub[mm] = img[:sub.shape[0], :sub.shape[1]][mm]
                views[d].append(c)
        out[slot] = views
    return out

# ---- colours (BF OBJ palette indices) ----------------------------------------------------------------------------------------------
TEAL = {'#': 1, 'D': 186, 'S': 199, 'M': 253, 'L': 254, 'H': 255}       # Garlic Jr.'s skin: outline, dark, shade, mid, light, highlight
SPOT = {'G': 237, 'g': 230}                                            # the green spots on his crown
EXTRA = {'W': 2, 'K': 1, 'R': 33, 'r': 32, 'Y': 110, 'y': 248, 'c': 191, 'C': 182}
INK = {**TEAL, **SPOT, **EXTRA}
# Pilaf's face colours -> Garlic Jr.'s (by brightness): his blues, dark to light, 159 175 173 174 164 98 99 181
PILAF_FACE = {159: 186, 175: 186, 173: 253, 174: 199, 164: 199, 98: 253, 99: 254, 181: 255, 1: 1, 2: 2}
PILAF_RUFF = {112: 115, 113: 116, 114: 117, 115: 117, 116: 118, 117: 118, 118: 119, 119: 2, 2: 2}   # his grey ruff -> a white scarf
ROBE = {79: 1, 63: 111, 64: 112, 65: 113}                              # Goten's gi -> the black cassock
SLEEVE = {93: 1, 94: 111, 95: 112, 161: 113, 157: 1, 159: 111}        # his navy undershirt (and its flickering purples) -> the cassock's sleeves
SHOE = {93: 160, 94: 176, 95: 174, 161: 164, 114: 160, 117: 176, 119: 174, 2: 174, 112: 1, 113: 160}   # his boots -> blue shoes
SKIN = {16: 186, 206: 199, 202: 199, 203: 253, 201: 253, 200: 254}    # Goten's skin -> Garlic Jr.'s
GOTEN_SKIN = tuple(SKIN)
GOTEN_EYES = (2, 117, 113, 31, 32, 33)          # his eyes and his open mouth
GI = tuple(ROBE)
NAVY = tuple(SLEEVE)
SOLE = 114
EMBLEM = ('YrYrY',            # the castle shield on his chest: a red field, the gold castle with its battlements and door, the
          'rYYYr',            # light blue edge round its point
          'rYRYr',
          'crrrc',
          '.crc.')
CAPE_WHITE = (117, 119, 2)    # the cape: shade, mid, light
CAPE_RED = 32                 # its lining
CAPE_BACK = {79: 117, 63: 118, 64: 119, 65: 2, 93: 117, 94: 118, 95: 119, 161: 2}   # seen from behind, over the gi and sleeves
CAPE_STOP = (160, 176, 174, 164)   # the shoes: the cape ends above them
CUFF, HEM = 191, 191          # his sleeves' cuffs and the hem's line: light blue

# ---- Garlic Jr.'s head, one letter a pixel ('?' = Pilaf's own pixel there, recoloured) -------------------------------------------
# The rows marked '?' are Pilaf's face rows (front and side: his eyes, mouth and chin) read from his standing frame at build time; the
# crown above them is Garlic Jr.'s (Pilaf wears a hat). FACE_ROW: the row of Pilaf's figure (from its top) where the '?' rows start.
HEAD = {
    0: ('.......#####.......',
        '.....##HHHLM##.....',
        '....#HHGGLLMMS#....',
        '...#HHGgGLLMGMS#...',
        '...#HLHGLLMGgGS#...',
        '#..#HLLLMMMMGMS#..#',
        '#H.#LLMMMMMMMMS#.S#',
        '.#H#LMDMMMMMDMS#S#.',
        '..#HLMMDDMDDMMSS#..',
        '..#?????????????#..',
        '...#???????????#...',
        '....#?????????#....',
        '.....#########.....'),
    1: ('.......#####.......',          # from behind: the crown down to the neck, the ears either side
        '.....##MLHHH##.....',
        '....#SMMGGLLHH#....',
        '...#SMGgGMLLHHH#...',
        '...#SMMGMMLLGHH#...',
        '#..#SMMMMMLGgGH#..#',
        '#S.#SMMMMMMLLGH#.H#',
        '.#S#SMMMMMMMLLH#H#.',
        '..#SSMMMMMMMMLHH#..',
        '..#SMMMMMMMMMMLH#..',
        '...#SMMMMMMMMLH#...',
        '....#SSMMMMMSS#....',
        '.....#########.....'),
    2: ('.....#####......',              # from the side, facing left (the game mirrors it): the ear points up and back
        '...##HHHLM##....',
        '..#HHGGLLMMS#...',
        '.#HHGgGLLMGMS#..',
        '.#HLHGLLMGgGS#.#',
        '#HLLLLMMMMGMS#S#',
        '#HLLMMMMMMMS#SS#',
        '#LMDMMMMMMS#SS#.',
        '#MMDDMMMMMSSS#..',
        '#???????????#...',
        '#???????????#...',
        '.#?????????#....',
        '..#########.....'),
}
FACE_ROW = {0: 12, 2: 12}      # Pilaf's eye row, from the top of his figure (his hat's tip)
FACE_DX = {0: 2, 2: 1}         # his figure's left edge, in the head's columns


def _letters(rows):
    out = np.zeros((len(rows), max(len(r) for r in rows)), np.uint8)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c not in '.?': out[y, x] = INK[c]
    return out


def garlic_heads(pilaf):
    """{view: index image} of Garlic Jr.'s head. pilaf: {view: Pilaf's standing frame (BF indices)}."""
    out = {}
    for v, rows in HEAD.items():
        img = _letters(rows)
        if v in FACE_ROW:
            p = pilaf[v]; ys, xs = np.nonzero(p); top, left = ys.min(), xs.min()
            q0 = min(y for y, r in enumerate(rows) if '?' in r)
            for y, r in enumerate(rows):
                for x, c in enumerate(r):
                    if c != '?': continue
                    py, px = top + FACE_ROW[v] + y - q0, left + x - FACE_DX[v]
                    val = int(p[py, px]) if 0 <= py < p.shape[0] and 0 <= px < p.shape[1] else 0
                    img[y, x] = PILAF_FACE.get(val, 253) if val else 253
        out[v] = img
    return out


def _head_of(frame, below=GI + NAVY):
    """The head in a standing frame: the largest piece above the first row with 2+ clothing pixels. -> (crop, top row, left column)."""
    rows = np.nonzero(np.isin(frame, below).sum(1) >= 2)[0]
    top = rows.min() if len(rows) else frame.shape[0]
    m = np.zeros(frame.shape, bool); m[:top] = frame[:top] > 0
    best = max(_components(m), key=lambda c: c.sum())
    ys, xs = np.nonzero(best)
    crop = np.where(best, frame, 0)[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return crop


def _paste(img, b, by, bx, over=False):
    """The new head, over what is empty there only: Goten's head is cut away first, so what's left (arms raised, a guard, a fist
    thrown across the face) stays in front of it. over: in front of everything (Garlic Jr.'s head is wider than Goten's: where Goten
    holds his arms tight beside his head, they go behind Garlic Jr.'s)."""
    H, W = img.shape
    for y, x in zip(*np.nonzero(b)):
        Y, X = by + y, bx + x
        if 0 <= Y < H and 0 <= X < W and (over or not img[Y, X]): img[Y, X] = b[y, x]


MIN_MATCH = 0.5
# Frames whose head the matcher can't place (a blur, a head turned past any standing pose): the frame's sha1 (12 hex) -> (rows y0..y1 and
# columns x0..x1 cleared of Goten's head colours, the head drawn (0 front, 1 back, 2 side, 3 side mirrored), its chin row and centre
# column, and whether the scarf goes on). Read off grids of each frame.
MANUAL = {'352ba442e3c0': (11, 24, 29, 34, 0, 24, 32, False)}    # 13.1 (all views): powering up, arms raised beside the head, looking up


class GarlicJr:
    """Kid Goten's frames as Garlic Jr.'s (see the module's docstring). goten, pilaf: {view: that actor's standing frame}."""

    def __init__(self, goten, pilaf):
        self.head = garlic_heads(pilaf)
        self.head[3] = self.head[2][:, ::-1]
        # Pilaf's ruff, the rows under his chin, as the white hood and scarf: (rows, columns) of the ruff from his standing frame
        self.scarf = {}
        for v in (0, 1, 2):
            p = pilaf[v]; ys, xs = np.nonzero(p); top = ys.min()
            band = p[top + 15:top + 18].copy()                   # three rows of his ruff, under the chin
            band = np.where(np.isin(band, list(PILAF_RUFF)), band, 0)
            bx = np.nonzero(band.any(0))[0]
            band = band[:, bx.min():bx.max() + 1] if len(bx) else band
            self.scarf[v] = np.vectorize(lambda c: PILAF_RUFF.get(int(c), 0))(band).astype(np.uint8)
        self.scarf[3] = self.scarf[2][:, ::-1]
        # Goten's heads: every turn a frame can show (front, back, side both ways; front and side on their sides, lying down)
        self.tpl = []
        for v in (0, 1, 2):
            h = _head_of(goten[v])
            kinds = [(v, 0, False)] + ([(2, 0, True)] if v == 2 else [])
            if v in (0, 2):
                kinds += [(v, r, f) for r in (1, 3) for f in ((False, True) if v == 2 else (False,))]
            for kind, rot, flip in kinds:
                t = h[:, ::-1] if flip else h
                self.tpl.append((np.rot90(t, rot).copy(), kind, rot, flip))
        self.hits = self.misses = self.manual = 0; self.missed = []

    def find(self, img):
        """Best (score, template index, x, y) of Goten's head in img."""
        H, W = img.shape; best = (0, None, 0, 0)
        for i, (t, kind, rot, flip) in enumerate(self.tpl):
            th, tw = t.shape; ink = np.argwhere(t > 0); total = len(ink)
            P = np.zeros((H + 2 * th, W + 2 * tw), np.uint8); P[th:th + H, tw:tw + W] = img
            acc = np.zeros((H + th, W + tw), np.int32)
            for y, x in ink:
                acc += P[y:y + H + th, x:x + W + tw] == t[y, x]
            j = np.unravel_index(acc.argmax(), acc.shape)
            score = acc[j] / total
            if score > best[0]: best = (score, i, j[1] - tw, j[0] - th)
        return best

    def apply(self, img, view=None):
        img = img.copy()
        if not img.any(): return img
        H, W = img.shape
        ys, xs = np.nonzero(img); fw, fh = np.ptp(xs) + 1, np.ptp(ys) + 1      # the whole figure, as Goten drew it
        hand = MANUAL.get(hashlib.sha1(img.tobytes()).hexdigest()[:12])
        if hand:
            self.manual += 1
            y0, y1, x0, x1, kind, chin, cx, scarf = hand
            box = np.zeros((H, W), bool); box[y0:y1 + 1, x0:x1 + 1] = True
            img[box & np.isin(img, (1,) + GOTEN_SKIN + GOTEN_EYES)] = 0
            src = img.copy(); self._dress(img, src)
            b = self.head[kind]; bh, bw = b.shape
            if scarf: self._scarf(img, src, min(kind, 2) if kind != 3 else 3, chin + 1, cx)
            _paste(img, b, chin - bh + 1, cx - bw // 2, over=True)
            return img
        score, i, x0, y0 = self.find(img)
        head = None
        if i is not None and score >= MIN_MATCH:
            self.hits += 1
            t, kind, rot, flip = self.tpl[i]; th, tw = t.shape
            area = np.zeros((H, W), bool)
            for y, x in zip(*np.nonzero(t)):
                if 0 <= y + y0 < H and 0 <= x + x0 < W: area[y + y0, x + x0] = True
            near = np.zeros((H, W), bool)                               # around the template, never past the chin (the shoulders stay)
            near[max(y0 - 2, 0) if rot != 3 else y0:y0 + th + (2 if rot != 0 else 0), max(x0 - 2, 0) if rot != 1 else x0:x0 + tw + (2 if rot != 3 else 0)] = True
            headish = np.isin(img, (1,) + GOTEN_SKIN + GOTEN_EYES) & near
            grow = area.copy()
            for _ in range(2):
                g = grow.copy(); g[1:] |= grow[:-1]; g[:-1] |= grow[1:]; g[:, 1:] |= grow[:, :-1]; g[:, :-1] |= grow[:, 1:]
                grow = (g & headish) | area
            img[grow & np.isin(img, (1,) + GOTEN_SKIN + GOTEN_EYES)] = 0
            wide = np.zeros((H, W), bool); wide[max(y0 - 4, 0):y0 + th + 4, max(x0 - 4, 0):x0 + tw + 4] = True
            for m in _components(img == 1):                             # a tuft of his hair left by itself round the head
                if m.sum() <= 6 and (m & wide).any() and not _touch(m, (img > 1)): img[m] = 0
            head = (kind, rot, flip, x0, y0, tw, th, t)
        else:
            self.misses += 1; self.missed.append((score, view))
        src = img.copy()
        self._dress(img, src)
        if head:
            kind, rot, flip, x0, y0, tw, th, t = head
            k = 3 if (kind == 2 and flip) else kind
            b = np.rot90(self.head[k], rot); bh, bw = b.shape
            if rot == 0:                                                # chin on chin: the head's bottom on the template's bottom row,
                bottom = np.nonzero(t[-1])[0]                           # centred on Goten's chin there
                cx = x0 + int(round(bottom.mean())); by = y0 + th - bh + 1
                flat = fw > 1.15 * fh                                   # lying, or flying flat: no scarf rows under the chin, no hanging cape
                if not flat: self._scarf(img, src, k, y0 + th, cx)
                bxs = np.nonzero(self.head[k][-1])[0]
                _paste(img, b, by, cx - int(round(bxs.mean())))
            elif rot == 1:                                              # turned anticlockwise: the chin points right
                _paste(img, b, y0 + (th - bh) // 2, x0 + tw - bw)
            else:
                _paste(img, b, y0 + (th - bh) // 2, x0)
        return img

    def _scarf(self, img, src, kind, top, cx):
        """His cloak (Dead Zone; Budokai Tenkaichi 2's artwork): a thick white scarf wrapped round the neck and shoulders (Pilaf's ruff, three
        rows under the chin, over the cassock, sleeves and neck), the castle shield on the chest below it (front), and the long white cape
        lined in red hanging from the shoulders to the floor behind him: over his back seen from behind, a strip down each side from the
        front, trailing behind from the side."""
        s = self.scarf[kind]; sh, sw = s.shape
        body = np.isin(src, GI + NAVY + (112, 113))
        for y in range(sh):
            for x in range(sw):
                Y, X = top + y, cx - sw // 2 + x
                if s[y, x] and 0 <= Y < img.shape[0] and 0 <= X < img.shape[1] and body[Y, X]: img[Y, X] = s[y, x]
        if kind == 0: self._emblem(img, src, top + sh, cx)
        self._cape(img, src, kind, top + 1)

    def _emblem(self, img, src, top, cx):
        """The castle emblem on the chest, seen from the front: a red shield with the gold castle, edged in light blue (over the cassock
        and the belt; never over a hand in front of him)."""
        e = _letters(EMBLEM)
        cloth = np.isin(src, GI + NAVY + (1, 112, 113))
        for y, x in zip(*np.nonzero(e)):
            Y, X = top + y, cx - e.shape[1] // 2 + x
            if 0 <= Y < img.shape[0] and 0 <= X < img.shape[1] and cloth[Y, X]: img[Y, X] = e[y, x]

    def _cape(self, img, src, kind, top):
        """The cape, from the shoulders (row `top`) to the rows above the shoes."""
        H, W = img.shape
        robe = np.isin(src, GI)                                         # the cassock (Goten's gi): what the cape hangs behind
        shoes = np.isin(img, CAPE_STOP)
        cloth = np.isin(src, GI + NAVY)
        ys = np.nonzero(cloth.any(1))[0]
        if not len(ys): return
        sy = np.nonzero(shoes.any(1))[0]
        bottom = (sy.min() - 1) if len(sy) and sy.min() > top else ys.max()
        rows = range(top, bottom + 1)
        if kind == 1:                                                    # from behind: over his back and the backs of his sleeves (and
            for y in rows:                                               # the belt between them), its edges outlined, flaring at the hem
                xs = np.nonzero(cloth[y])[0]
                if not len(xs): continue
                for x in range(xs.min(), xs.max() + 1):
                    v = int(src[y, x])
                    if v in CAPE_BACK or (v in (1, 112, 113) and x not in (xs.min(), xs.max())): img[y, x] = CAPE_BACK.get(v, CAPE_WHITE[1])
                if y >= bottom - 2:
                    for x, d in ((xs.min() - 1, -1), (xs.max() + 1, 1)):
                        if 0 <= x < W and not img[y, x]: img[y, x] = 1
            return
        # from the front or the side: a sheet hanging straight from the shoulders, a little wider toward the floor, seen wherever nothing of
        # him is in front of it (an arm hanging over it, a fist held out); its edge outlined, its red lining showing in the last rows
        sides = (-1, 1) if kind == 0 else (1,) if kind == 2 else (-1,)
        span = max(bottom - top, 1)
        for d in sides:
            sh = [x for y in range(top, min(top + 3, bottom + 1)) for x in np.nonzero(cloth[y])[0]]
            if not sh: continue
            base = (min(sh) - 1) if d < 0 else (max(sh) + 1)
            side = robe if kind == 0 else cloth                          # (from the side his sleeve often covers the cassock)
            last = None
            for y in rows:
                xs = np.nonzero(side[y])[0]
                if len(xs): last = xs.min() if d < 0 else xs.max()
                if last is None: continue
                edge = base + d * ((y - top) * 2 // span + (1 if kind != 0 else 0))
                x = last + d
                while (x >= edge if d < 0 else x <= edge) and 0 <= x < W:
                    if not img[y, x]:
                        img[y, x] = 1 if x == edge else CAPE_RED if (y > bottom - 2 and abs(x - edge) >= 2) else CAPE_WHITE[2 if abs(x - edge) == 1 else 1]
                    x += d

    def _dress(self, img, src):
        """Goten's gi -> the black cassock (sleeves too) with its light blue hem and cuffs, his boots -> blue shoes, his skin -> Garlic
        Jr.'s. Effects keep their colours."""
        navy = np.isin(src, NAVY)
        shoe = np.zeros_like(navy)
        for m in _components(np.isin(src, (SOLE, 117, 119, 112, 113) + NAVY)):
            if (src[m] == SOLE).any(): shoe |= m                       # a boot: navy, its grey band and its sole, together
        for m in _components(src == 2):                                 # its white: small and against the boot (a swoosh is neither)
            if m.sum() <= 3 and _touch(m, shoe): shoe |= m
        skin = np.isin(src, GOTEN_SKIN)
        robe = np.isin(src, GI)
        for k, v in SHOE.items(): img[shoe & (src == k)] = v
        for k, v in ROBE.items(): img[src == k] = v
        for k, v in SLEEVE.items(): img[navy & ~shoe & (src == k)] = v
        for k, v in SKIN.items(): img[src == k] = v
        near = lambda m: np.pad(m, 1)[2:, 1:-1] | np.pad(m, 1)[:-2, 1:-1] | np.pad(m, 1)[1:-1, 2:] | np.pad(m, 1)[1:-1, :-2]
        img[navy & ~shoe & near(skin) & (src != 93)] = CUFF            # the sleeves' light blue cuffs, at the hands
        below = np.zeros_like(robe); below[:-1] = shoe[1:]
        img[robe & below & (src != 79)] = HEM                          # the cassock's light blue hem, just above the shoes


# ---- Super Garlic Jr.: Spopovich's frames (actor 243) made his, in lib/super_garlic.py (the owner, Nov 9: Yakon's had the wrong head, back
# spikes and legs) ---------------------------------------------------------------------------------------------------------------------


# ---- the Spice Boys and the Makyans: fighters of the same build, recoloured --------------------------------------------------------
# The ranked search over BF's fighters (Nov 9): each Spice Boy is built on the fighter closest in build and cut, with every slot its
# behaviour row plays.
#   Spice (tall, lean; spiky white hair, light blue skin, red eyes; pink armour over a dark purple leotard, pink bracers and boots with
#     white tips): BF Vegeta, actor 270 (the same lean build, swept spiky hair, a sleeveless suit, gloves and boots), as Majin Vegeta's
#     enemy row 70;
#   Vinegar (big, muscular; long dark brown hair under a beige fur hat; light purple skin; musk green armour over a dark blue leotard;
#     white boots with green tips): Olibu, actor 197 (big, muscular, long hair), on his own row 85;
#   Mustard (tall, muscular; a brown frog's face; long red hair; a black leotard with light purple chest; purple gloves and boots):
#     Idasa, actor 134 (muscular, a mane of hair, a bare chest), on his own row 49;
#   Salt (short; red skin; a brown fur hat; a yellow fur collar; a black jacket with light green shoulders; white gloves; light blue
#     trousers; white and brown boots): kid Trunks, actor 260 (short; his hair the shape of a fur hat), on his own row 130.
# (Each from the Dragon Ball Wiki's descriptions; "likely" where the anime's colours vary.)
def _thick(mask):
    """The part of a mask at least two pixels thick (an outline is one): a 2 x 2 opening."""
    m = mask & np.roll(mask, 1, 0) & np.roll(mask, 1, 1) & np.roll(np.roll(mask, 1, 0), 1, 1)
    return m | np.roll(m, -1, 0) | np.roll(m, -1, 1) | np.roll(np.roll(m, -1, 0), -1, 1)


def _edge(mask):
    """Pixels of a mask next to something outside it (4-neighbours)."""
    p = np.pad(mask, 1)
    inner = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return mask & ~inner


def _remap(out, img, where, table):
    for k, v in table.items(): out[where & (img == k)] = v


def _rows(img, cloth):
    """(top of the clothes, bottom of the figure) in a frame: the first row with 3+ clothing pixels, the last row drawn."""
    ys = np.nonzero(np.isin(img, cloth).sum(1) >= 3)[0]; fy = np.nonzero(img.any(1))[0]
    return (ys.min() if len(ys) else fy.min()), fy.max()


SPICE_SKIN = {16: 72, 206: 73, 202: 73, 203: 74, 201: 74, 200: 75, 204: 72, 208: 72, 245: 75, 83: 75}
SPICE_SUIT = {93: 85, 94: 86, 95: 153, 157: 85, 158: 86, 159: 153, 161: 154, 162: 154, 96: 154, 69: 85}
SPICE_PINK = {93: 39, 94: 40, 95: 41, 157: 39, 158: 40, 159: 41, 161: 44, 162: 44, 96: 44, 69: 39}     # the armour over his suit
SPICE_GEAR = {112: 39, 113: 39, 114: 40, 115: 40, 116: 41, 117: 41, 118: 44, 119: 44, 120: 2}      # gloves, boots -> pink
SPICE_HAIR = (118, 119, 2)


def spice(img):
    """One of BF Vegeta's frames as Spice's."""
    out = img.copy()
    if not img.any(): return out
    H, W = img.shape; row = np.arange(H)[:, None]
    top, bottom = _rows(img, tuple(SPICE_SUIT))
    hair = (_thick(img == 1) | np.isin(img, tuple(SPICE_SUIT))) & (row < top)      # his black hair (and its blue lights) above the suit
    hair &= _thick(hair)
    inner = hair & ~_edge(hair)
    out[hair] = 1                                                       # outline; inside it white, a light grey band round the edge
    out[inner] = SPICE_HAIR[0]
    out[inner & ~_edge(inner)] = SPICE_HAIR[2]
    out[np.isin(img, tuple(SPICE_SUIT)) & (row < top) & ~hair] = SPICE_HAIR[1]     # the thin tips' blue lights
    _remap(out, img, np.ones_like(hair), SPICE_SKIN)
    armour = (row >= top) & (row < top + 4)
    _remap(out, img, armour, SPICE_PINK)
    _remap(out, img, ~armour & ~hair, SPICE_SUIT)
    _remap(out, img, (row >= top) & (row < bottom - 1), SPICE_GEAR)
    _remap(out, img, row < top, {112: SPICE_HAIR[0], 118: SPICE_HAIR[2], 127: SPICE_HAIR[1], 40: SPICE_HAIR[1], 41: SPICE_HAIR[2]})   # his hair's own lights
    _remap(out, img, row >= bottom - 1, {**{k: 2 for k in SPICE_GEAR}, 243: 2, 24: 119, 25: 119})   # the boots' white tips
    return out


VINEGAR_HAIR = {248: 77, 109: 78, 110: 208, 250: 79}
VINEGAR_HAT = {248: 83, 109: 21, 110: 22, 250: 245}
VINEGAR_SKIN = {16: 169, 17: 169, 206: 169, 202: 90, 203: 90, 201: 91, 200: 91}
VINEGAR_ARMOUR = {113: 24, 115: 24, 116: 25, 117: 230, 118: 230, 119: 237, 120: 237}      # (white stays: his lights, and swooshes)
VINEGAR_SUIT = {113: 69, 115: 69, 116: 157, 117: 158, 118: 158, 119: 94, 120: 94}
VINEGAR_BOOT = {77: 117, 78: 119, 79: 2, 81: 2, 16: 117, 17: 119}
VINEGAR_TIP = {77: 251, 78: 252, 79: 252, 81: 253, 16: 251, 17: 252}


def vinegar(img):
    """One of Olibu's frames as Vinegar's."""
    out = img.copy()
    if not img.any(): return out
    H, W = img.shape; row = np.arange(H)[:, None]
    fy = np.nonzero(img.any(1))[0]; top_, bottom = fy.min(), fy.max()
    hair = np.isin(img, list(VINEGAR_HAIR))
    hy = np.nonzero(hair.any(1))[0]
    hat = hair & (row < (hy.min() + 4 if len(hy) else 0))               # the top of his hair: the fur hat
    _remap(out, img, hat, VINEGAR_HAT); _remap(out, img, hair & ~hat, VINEGAR_HAIR)
    _remap(out, img, row < (hy.min() + 7 if len(hy) else 0), {63: 83, 64: 21, 65: 22})       # Olibu's headband: the hat's rim
    cloth = np.zeros(img.shape, bool)                                   # his clothes: white pieces with Olibu's grey shading in them
    for m in _components(np.isin(img, list(VINEGAR_ARMOUR))):           # (a swoosh is plain white)
        if np.isin(img[m], (113, 115, 116, 117, 118)).sum() >= 3: cloth |= m
    cy = np.nonzero(cloth.sum(1) >= 3)[0]
    belt = np.nonzero((np.isin(img, (77, 78, 79)) & cloth.any(1)[:, None]).sum(1) >= 3)[0]
    split = belt.min() if len(belt) else (cy.min() + cy.max()) // 2 if len(cy) else H
    feet = row > bottom - 6
    _remap(out, img, cloth & (row < split), VINEGAR_ARMOUR)
    _remap(out, img, cloth & (row >= split), VINEGAR_SUIT)
    _remap(out, img, ~feet & ~hair, VINEGAR_SKIN)
    _remap(out, img, feet & (row < bottom), VINEGAR_BOOT)
    _remap(out, img, feet & (row >= bottom), VINEGAR_TIP)
    return out


MUSTARD_HAIR = {248: 31, 249: 32, 250: 104}
MUSTARD_SKIN = {16: 77, 202: 204, 203: 205, 201: 206, 200: 17, 206: 205, 17: 206}
MUSTARD_TORSO = {16: 1, 202: 111, 203: 112, 201: 170, 200: 91, 206: 111, 17: 112}       # the leotard; its light purple chest
MUSTARD_PANTS = {31: 1, 32: 111, 104: 112, 33: 113}
MUSTARD_GEAR = {112: 85, 113: 86, 114: 86, 115: 153, 116: 153, 117: 154, 118: 155, 119: 155}


def mustard(img):
    """One of Idasa's frames as Mustard's."""
    out = img.copy()
    if not img.any(): return out
    H, W = img.shape; row = np.arange(H)[:, None]; col = np.arange(W)[None, :]
    pants = np.isin(img, list(MUSTARD_PANTS))
    py = np.nonzero(pants.any(1))[0]; px = np.nonzero(pants.any(0))[0]
    hair = np.isin(img, list(MUSTARD_HAIR))
    hy = np.nonzero(hair.any(1))[0]
    chin = hy.max() if len(hy) else 0
    skin = np.isin(img, list(MUSTARD_SKIN))
    torso = np.zeros_like(skin)
    if len(py) and len(px):
        torso = skin & (row > chin + 1) & (row < py.min()) & (col >= px.min()) & (col <= px.max())
    _remap(out, img, hair, MUSTARD_HAIR)
    _remap(out, img, torso, MUSTARD_TORSO)
    _remap(out, img, skin & ~torso, MUSTARD_SKIN)
    _remap(out, img, pants, MUSTARD_PANTS)
    _remap(out, img, np.ones_like(skin), MUSTARD_GEAR)
    return out


SALT_HAT = {137: 81, 138: 77, 146: 78, 147: 208, 148: 79, 157: 77, 161: 78}
SALT_SKIN = {16: 31, 206: 32, 205: 32, 202: 104, 203: 121, 201: 121, 200: 247}
SALT_GLOVE = {16: 115, 206: 117, 205: 117, 202: 118, 203: 119, 201: 119, 200: 2}
SALT_JACKET = {79: 1, 63: 111, 64: 112, 65: 221}
SALT_PANTS = {79: 180, 63: 182, 64: 178, 65: 179}
SALT_COLLAR = {79: 248, 63: 249, 64: 110, 65: 250, 16: 248, 206: 249, 202: 249, 203: 110, 201: 250, 200: 250}
SALT_BOOT = {112: 77, 113: 78, 114: 208, 115: 116, 117: 118, 119: 2}


def salt(img):
    """One of kid Trunks's frames as Salt's: his hair is the fur hat, pulled down to his eyes."""
    out = img.copy()
    if not img.any(): return out
    H, W = img.shape; row = np.arange(H)[:, None]; col = np.arange(W)[None, :]
    gi = np.isin(img, list(SALT_JACKET))
    top, bottom = _rows(img, tuple(SALT_JACKET))
    gy = np.nonzero(gi.any(1))[0]
    sash = np.nonzero((np.isin(img, (112, 114)) & (row > top)).sum(1) >= 3)[0]
    split = sash.min() if len(sash) else (gy.min() + gy.max()) // 2 if len(gy) else H
    neck = np.nonzero(gi[top])[0] if len(gy) else np.array([W // 2])
    nx = int(neck.mean()) if len(neck) else W // 2
    _remap(out, img, np.ones_like(gi), SALT_HAT)
    _remap(out, img, gi & (row < split), SALT_JACKET)
    _remap(out, img, gi & (row >= split), SALT_PANTS)
    _remap(out, img, row < top, SALT_SKIN)                              # his face
    _remap(out, img, row >= top, SALT_GLOVE)                            # his hands: white gloves
    _remap(out, img, (row >= top - 1) & (row <= top) & (np.abs(col - nx) <= 4), SALT_COLLAR)    # the fur collar round his neck
    _remap(out, img, row > bottom - 4, SALT_BOOT)
    return out


MAKYAN_SKIN = {16: 113, 205: 114, 206: 114, 202: 115, 203: 116, 201: 117, 200: 118}    # the mist's grey pallor
MAKYAN_CLOTH = {153: 69, 154: 69, 155: 157, 157: 85}                    # the purple sash -> dark
MAKYAN_EYES = {2: 34}                                                    # red eyes (likely: the anime's Makyans glare)


def makyan(img):
    """One of the Majin fighter's frames (actor 164) as a townsman under the Black Water Mist."""
    out = img.copy()
    if not img.any(): return out
    _remap(out, img, np.ones(img.shape, bool), {**MAKYAN_SKIN, **MAKYAN_CLOTH})
    return out


GARLIC_BODY, PILAF = 114, 214
GARLIC_STAND_IN = {10: 0, 21: 0}     # Goten's Super Saiyan change (10) and fusion dance (21): Garlic Jr. has neither (the owner, Nov 9:
                                     # "Don't give Garlic fusion frames cause he doesn't need them"); they hold his standing frames, as an
                                     # empty slot would draw junk


def garlic_jr_frames(rom, actor_list):
    """{slot: [front, back, side frame lists]} of Garlic Jr. (raw cells for build_actors), and the converter (its counts)."""
    g = actor_cells(rom, actor_list, GARLIC_BODY); p = actor_cells(rom, actor_list, PILAF)
    conv = GarlicJr({v: g[0][v][0] for v in (0, 1, 2)}, {v: p[0][v][0] for v in (0, 1, 2)})
    out = {}
    for s, views in g.items():
        if s in GARLIC_STAND_IN: continue
        out[s] = [[conv.apply(c, d) for c in views[d]] for d in range(3)]
    for s, src in GARLIC_STAND_IN.items():
        if s in g: out[s] = out[src]
    return out, conv


# The quest's actors, in id order (build.py adds them right after the GT actors; new_actor_ids lists them): Garlic Jr., then the recolours
# (Super Garlic Jr.'s figure is super_garlic.Converter's, by view; None here)
TINTS = {'super_garlic': (243, None), 'spice': (270, spice), 'vinegar': (197, vinegar), 'mustard': (134, mustard), 'salt': (260, salt),
         'makyan': (164, makyan)}
ACTORS = ('garlic_jr',) + tuple(TINTS)
