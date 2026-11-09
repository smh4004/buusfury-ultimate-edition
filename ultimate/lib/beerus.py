"""Beerus (Nov 9; the project owner: "Create missing frames for beerus based on whoever is closest"; "Maybe janemba for the ears but idk
you decide"). Buu's Fury has no Beerus. His frames are BF Kid Buu's (actor 38): the same 15 x 31 build as the owner's front sprite
(ultimate/art/beerus_reference.jpg), a bare torso, baggy trousers, wristbands, and the boss's own 19 slots, so a fight that uses Kid Buu's
behaviour plays every animation it expects. Each frame gets:
  - Beerus's head in place of Kid Buu's (antenna and all): the owner's sprite seen from the front; from behind, the same head mirrored with
    the face filled in; from the side, a profile drawn to match, its ear standing up like Janemba's. Kid Buu's head is found in every frame
    by matching it against his standing heads (front, back, side, mirrored and turned for lying frames), cleared, and Beerus's head is drawn
    with its chin on Kid Buu's chin, facing the way Kid Buu's head faced;
  - his collar (white, gold and blue, from the owner's sprite) on the four rows under the chin while he stands;
  - his colours: purple skin, gold wristbands, dark blue trousers with a navy waist and an orange gem, a gold hem, brown shoes.
Effects (white trails, steam, sparks) keep BF's colours. A frame whose head isn't found is counted and printed by the build."""
import hashlib
import numpy as np

# The owner's sprite, one letter a pixel (read off the 16 px grid of beerus_reference.jpg)
REF = ('...B.......B...', '...B.......B...', '..BCB.....BCB..', '..BCB.....BCB..', '..CCCB...BCDE..', '.BCCCB...BCCCB.',
       '.BCCCBBBBBCCCB.', '.BCCBCCCCCBCCB.', '..BCCCCCCCCCB..', '..BCCFFFFFCCB..', '..BCBBFFFBBCB..', '...BCGBFBGCB...',
       '...BFEHFHEFB...', '....BCFCFCB....', '.....BCFCB.....', '..IJICBBBCIJI..', '.DIKJIIIIIJKID.', '.BEIJLMNMLJIEB.',
       '.BCEIIIIIIIECB.', '.BCBCFBCBFCBCB.', '.DFB.OPPPO.BFD.', 'BCEEKEJMJEKEECB', 'BCFBKEJIJEKBFCB', '.BB.KEJMJEK.BB.',
       '...KQGJNJGQK...', '...KQRDJDRQK...', '...KRRLDLRRK...', '...GSEG.GESG...', '...TUVT.TVUT...', '..TUUUT.TUUUT..', '..TTTT...TTTT..')
RGB = {'B': (108, 52, 91), 'C': (121, 63, 103), 'D': (184, 179, 51), 'E': (218, 214, 80), 'F': (154, 82, 130), 'G': (200, 196, 62),
       'H': (0, 0, 0), 'I': (232, 232, 232), 'J': (41, 31, 39), 'K': (11, 71, 133), 'L': (13, 85, 159), 'M': (59, 49, 57), 'N': (237, 126, 8),
       'O': (0, 33, 66), 'P': (1, 45, 92), 'Q': (30, 129, 231), 'R': (26, 107, 188), 'S': (228, 223, 97), 'T': (76, 44, 23),
       'U': (124, 75, 43), 'V': (110, 63, 33)}
SKIN_OF = {'B': 153, 'C': 124, 'F': 150}          # his purple, from colours the game has: outline, skin, light (checked on the sheet)
HEAD_FRONT = REF[:15]
# From behind: the front head mirrored (his earring on the other side), the face filled with skin and a little light on the crown
HEAD_BACK = ('...B.......B...', '...B.......B...', '..BCB.....BCB..', '..BCB.....BCB..', '..EDCB...BCCC..', '.BCCCB...BCCCB.',
             '.BCCCBBBBBCCCB.', '.BCCBCCCCCBCCB.', '..BCCCFFFCCCB..', '..BCCFFFFFCCB..', '..BCCCCCCCCCB..', '...BCCCCCCCB...',
             '...BCCCCCCCB...', '....BCCCCCB....', '.....BBBBB.....')
# From the side, facing left (the game mirrors it): the far ear hidden, the near one standing up at the back of the head as Janemba's
# does in his side view; eye and brow at the front, a short muzzle, the chin under it
HEAD_SIDE = ('.......B..', '.......B..', '......BCB.', '......BCB.', '.....BCCDE', '.....BCCCB', '...BBBCCCB',
             '..BCCCCCCB', '.BCCCCCCCB', '.BFFFCCCCB', 'BFBBBFCCCB', 'BFGBFCCCB.', 'BFHEFCCCB.', '.BFFCCCB..', '..BBBBB...')
COLLAR_FRONT = (REF[15], REF[16], '.BEIIIMNMIIIEB.')     # three of the sprite's four collar rows, the gem on the last: Kid Buu's chest is shorter
COLLAR_BACK = ('..JIIIIIIIIIJ..', '.DEIIIIIIIIIED.', '..BEEEEEEEEEB..')
COLLAR_SIDE = ('..IJIII..', '.DIIKJID.', '..BEEEB..')

KID_SKIN = (38, 39, 40, 41, 42, 43, 44, 45, 46)
SKIN = {38: 153, 39: 153, 40: 138, 41: 124, 42: 124, 43: 150, 44: 150, 45: 151, 46: 151}
BLUR = {127: 153, 123: 138, 124: 124, 134: 150, 125: 151, 126: 151, 135: 151, 136: 151}      # the dash's afterimage pinks
FACE = (1, 3, 31, 32, 33)                         # Kid Buu's eyes and mouth
PANTS = (111, 112, 113, 114, 115, 116, 117, 118, 119, 120)
ACCENT = (1, 62, 63, 64, 65, 79, 109, 111, 16, 77, 78, 81, 211, 248)       # belt, wristbands, shoes
MIN_MATCH = 0.5
# Frames whose head the matcher can't find (a scream, the dash's blur): Kid Buu's frame (sha1 of its pixels, 12 hex) -> the box cleared
# (rows y0..y1, columns x0..x1: his skin, face and blur colours only), the head drawn (0 front, 2 side), its chin row and centre column,
# and whether the collar goes on. Read off grids of each frame (tools: a zoomed sheet with coordinates).
MANUAL = {'aeda01bafc11': (3, 18, 8, 22, 0, 18, 15, True),      # 4.3 front: a three-quarter head, low
          '0e25ad3eb4ae': (0, 15, 8, 22, 0, 15, 15, True),      # 9.1 front: hit, screaming
          '9b8ba6b3b16d': (15, 31, 10, 22, 0, 31, 16, True),    # 12.0: the steam scream, all views
          '96d2736bdd7c': (15, 30, 10, 22, 0, 30, 16, True),    # 12.1
          '63d3a8af6529': (4, 15, 4, 14, 2, 17, 9, False),      # 18.1-18.4: the dash, head first to the left
          '0add4ebfb365': (5, 14, 4, 14, 2, 16, 9, False),
          '0c9e4e5bc22d': (6, 15, 4, 14, 2, 17, 9, False),
          'cbc5638d435a': (4, 14, 4, 14, 2, 16, 9, False)}


def _components(mask):
    """8-connected components of a boolean mask -> list of boolean masks."""
    seen = np.zeros_like(mask); out = []
    h, w = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]: continue
        q = [(y, x)]; seen[y, x] = True; m = np.zeros_like(mask)
        while q:
            a, b = q.pop(); m[a, b] = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    Y, X = a + dy, b + dx
                    if 0 <= Y < h and 0 <= X < w and mask[Y, X] and not seen[Y, X]:
                        seen[Y, X] = True; q.append((Y, X))
        out.append(m)
    return out


def _touch(m, other):
    """Does mask m touch mask other (4-neighbours)?"""
    g = np.zeros_like(m)
    g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
    return bool((g & other & ~m).any())


def _crop(img):
    ys, xs = np.nonzero(img)
    return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


class Beerus:
    def __init__(self, kid_stand, one, chins=(15, 15, 16)):
        """kid_stand: {view: Kid Buu's standing frame (BF colour indices)}; one: RGB -> palette index; chins: the row each standing head ends."""
        def idx(rows):
            out = np.zeros((len(rows), len(rows[0])), np.uint8)
            for y, r in enumerate(rows):
                for x, c in enumerate(r):
                    if c != '.': out[y, x] = SKIN_OF.get(c) or one(np.array(RGB[c]))
            return out
        self.head = {0: idx(HEAD_FRONT), 1: idx(HEAD_BACK), 2: idx(HEAD_SIDE)}
        self.collar = {0: idx(COLLAR_FRONT), 1: idx(COLLAR_BACK), 2: idx(COLLAR_SIDE)}
        self.gold = {k: one(np.array(v)) for k, v in (('dark', (152, 152, 0)), ('mid', (200, 196, 62)), ('light', (228, 223, 97)))}
        self.navy, self.navy2 = one(np.array((0, 33, 66))), one(np.array((1, 45, 92)))
        self.gem = 65
        self.blue = {111: self.navy, 112: self.navy, 113: one(np.array((0, 0, 120))), 114: one(np.array((11, 71, 133))),
                     115: one(np.array((13, 85, 159))), 116: one(np.array((13, 85, 159))), 117: one(np.array((26, 107, 188))),
                     118: one(np.array((26, 107, 188))), 119: one(np.array((30, 129, 231))), 120: one(np.array((30, 129, 231))),
                     2: one(np.array((30, 129, 231)))}
        self.brown = {63: one(np.array((124, 75, 43))), 64: one(np.array((124, 75, 43))), 65: one(np.array((140, 88, 50))),
                      109: one(np.array((140, 88, 50))), 79: 79, 77: 77, 78: 78, 16: 16, 62: 77, 81: one(np.array((124, 75, 43)))}
        # Kid Buu's heads: the rows above each standing chin; every turn and mirror a frame can show
        self.tpl = []
        for v in (0, 1, 2):
            k = kid_stand[v]; rows = np.nonzero(k.any(1))[0]
            h = k[:chins[v] + 1].copy()
            ys, xs = np.nonzero(h)
            h = h[ys.min():, xs.min():xs.max() + 1]
            kinds = [(v, 0, False)] if v != 2 else [(2, 0, False), (2, 0, True)]
            if v in (0, 2):
                kinds += [(v, r, f) for r in (1, 3) for f in ((False, True) if v == 2 else (False,))]
            for kind, rot, flip in kinds:
                t = h[:, ::-1] if flip else h
                self.tpl.append((np.rot90(t, rot).copy(), kind, rot, flip))
        self.hits = self.misses = self.manual = 0; self.missed = []

    def find(self, img):
        """Best (score, template index, x, y) of Kid Buu's head in img."""
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
        hand = MANUAL.get(hashlib.sha1(img.tobytes()).hexdigest()[:12])
        if hand:
            self.manual += 1
            y0, y1, x0, x1, kind, chin, cx, collar = hand
            box = np.zeros((H, W), bool); box[y0:y1 + 1, x0:x1 + 1] = True
            img[box & np.isin(img, KID_SKIN + FACE + tuple(BLUR) + (138, 150))] = 0
            self._dress(img)
            b = self.head[kind]; bh, bw = b.shape
            self._paste(img, b, chin - bh + 1, cx - bw // 2)
            if collar: self._collar(img, kind, False, chin + 1, cx)
            return img
        score, i, x0, y0 = self.find(img)
        head = None
        if i is not None and score >= MIN_MATCH:
            self.hits += 1
            t, kind, rot, flip = self.tpl[i]; th, tw = t.shape
            area = np.zeros((H, W), bool)
            ys, xs = np.nonzero(t)
            for y, x in zip(ys + y0, xs + x0):
                if 0 <= y < H and 0 <= x < W: area[y, x] = True
            grow = area.copy()                                           # the head as drawn here: its own colours touching the template
            near = np.zeros((H, W), bool)                               # around the template, never past the chin (the shoulders stay)
            near[max(y0 - 2, 0) if rot != 3 else y0:y0 + th + (2 if rot != 0 else 0), max(x0 - 2, 0) if rot != 1 else x0:x0 + tw + (2 if rot != 3 else 0)] = True
            headish = np.isin(img, KID_SKIN + FACE) & near
            for _ in range(3):
                g = grow.copy(); g[1:] |= grow[:-1]; g[:-1] |= grow[1:]; g[:, 1:] |= grow[:, :-1]; g[:, :-1] |= grow[:, 1:]
                grow = (g & headish) | area
            cut = grow & np.isin(img, KID_SKIN + FACE + (127, 123, 124, 125, 134, 135, 138, 150))
            img[cut] = 0
            if rot == 0:                                                # what's left of an antenna that swung outside the template:
                chin = y0 + th - 1                                      # skin wholly above the chin, cut off from the body
                for m in _components(np.isin(img, KID_SKIN + FACE)):
                    if np.nonzero(m)[0].max() < chin - 1 and m.sum() <= 24: img[m] = 0
            head = (kind, rot, flip, x0, y0, tw, th)
        else:
            self.misses += 1; self.missed.append((score, view))
        self._dress(img)
        if head:
            kind, rot, flip, x0, y0, tw, th = head
            b = self.head[kind]
            if flip: b = b[:, ::-1]
            b = np.rot90(b, rot)
            bh, bw = b.shape
            # chin on chin, centre on centre: the chin is the template's bottom (upright), or its side when turned
            if rot == 0:
                by, bx = y0 + th - bh, x0 + (tw - bw) // 2
            elif rot == 1:              # turned anticlockwise: the chin points right... the head's top is at the left
                by, bx = y0 + (th - bh) // 2, x0 + tw - bw
            else:
                by, bx = y0 + (th - bh) // 2, x0
            self._paste(img, b, by, bx)
            if rot == 0:
                self._collar(img, kind, flip, y0 + th, x0 + tw // 2)
        return img

    @staticmethod
    def _paste(img, b, by, bx):
        H, W = img.shape
        for y, x in zip(*np.nonzero(b)):
            if 0 <= by + y < H and 0 <= bx + x < W: img[by + y, bx + x] = b[y, x]

    def _collar(self, img, kind, flip, top, cx):
        c = self.collar[kind]
        if flip: c = c[:, ::-1]
        ch, cw = c.shape; skin = np.isin(img, list(set(SKIN.values())))
        for y in range(ch):
            for x in range(cw):
                Y, X = top + y, cx - cw // 2 + x
                if c[y, x] and 0 <= Y < img.shape[0] and 0 <= X < img.shape[1] and skin[Y, X]: img[Y, X] = c[y, x]

    def _dress(self, img):
        src = img.copy()
        pants = np.isin(src, PANTS)
        white = src == 2
        for m in _components(white):                                    # white on the trousers is their light; elsewhere a trail
            if _touch(m, pants) and m.sum() <= 6: pants |= m              # (a dash's streak is a big white patch: it stays white)
        skin = np.isin(src, KID_SKIN)
        acc = np.isin(src, ACCENT)
        for m in _components(acc):
            vals = set(src[m].tolist())
            if vals <= {1} and not (_touch(m, pants) and _touch(m, skin)):   # an outline or a face, not a belt
                continue
            ys, xs = np.nonzero(m); wide, tall = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
            if vals & {77, 78} or not _touch(m, skin):                  # a shoe (its sole, or nothing but trousers round it): cuff -> gold hem
                kind = 'shoe'
            elif _touch(m, pants) and wide >= 5 and wide >= tall + 2:   # a band between the torso and the trousers: the belt (a hand at the
                kind = 'belt'                                           # hip touches both too, but its wristband is no wider than tall)
            else:                                                       # on the skin alone: a wristband
                kind = 'wrist'
            for v in vals:
                sel = m & (src == v)
                if kind == 'shoe':                                      # black over the shoe's colour, or under the trousers: the cuff, gold;
                    if v in (1, 111):                                   # black inside a sole stays black
                        below = np.zeros_like(sel); below[:-1] = np.isin(src[1:], (63, 64, 65, 109, 79))
                        above = np.zeros_like(sel); above[1:] = np.isin(src[:-1], PANTS)
                        img[sel & (below | above)] = self.gold['mid']
                    else:
                        img[sel] = self.brown.get(v, v)
                elif kind == 'belt':
                    img[sel] = {1: self.navy, 111: self.navy, 112: self.navy2, 79: self.navy2, 62: self.navy, 63: self.gold['mid'],
                                64: self.gold['mid'], 109: self.gold['light'], 65: self.gem}.get(v, v)
                else:
                    img[sel] = {1: self.gold['dark'], 111: self.gold['dark'], 79: self.gold['dark'], 62: self.gold['dark'], 63: self.gold['mid'],
                                64: self.gold['mid'], 65: self.gold['light'], 109: self.gold['light']}.get(v, v)
        for k, v in self.blue.items():
            img[pants & (src == k)] = v
        for k, v in SKIN.items(): img[src == k] = v
        for k, v in BLUR.items(): img[src == k] = v
