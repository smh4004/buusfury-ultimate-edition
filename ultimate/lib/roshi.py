"""Master Roshi as a fighter (Nov 9; the project owner: "make Roshi playable too ... reskin whoever ... to make his attack frames").
Buu's Fury only has Roshi standing, walking and cheering (actor 177), so his fighting frames are Krillin's (the build's Krillin, LoG2's
fighter, actor 'krillin'): the same short build and bald head, and Roshi's own pupil. Each frame gets:
  - Roshi's head from his standing frames (bald dome, white brows, sunglasses, moustache), found and placed like lib/headswap.py does
    for Yamcha: Krillin's head is matched in every frame against his own standing head, cleared, and Roshi's is drawn bottom-aligned to
    Krillin's chin (front, back, side; the side head mirrored when the frame faces the other way; turned on its side when lying down);
  - his beard: the white and grey pixels under his chin in each standing view, hanging from the new head;
  - his clothes, the colours of his standing sprite: the gi top stays orange (his shirt), the trousers and belt turn to his purple
    shorts, the boots to his grey sandals, the wristbands to skin.
A frame where Krillin's head isn't found (a blur) keeps Krillin's colours only; misses are counted and printed by the build."""
import numpy as np
import headswap

ORANGE = {4: 166, 64: 165, 63: 161, 207: 159}          # Krillin's gi below the belt -> Roshi's purple shorts (light to dark)
BELT = {176: 165, 161: 161, 158: 159}                  # the belt: part of the shorts
BOOTS = {176: 116, 161: 115, 158: 113}                 # boots -> grey sandals
WRIST = {176: 214, 161: 213, 158: 212}                 # wristbands -> bare forearms
SHIRT = {176: 4, 161: 64, 158: 63}                     # the undershirt at the collar -> his orange shirt
BLUE = set(BELT)
BEARD = {2, 116, 118, 115}                             # white and greys under Roshi's chin
SKIN = {212, 213, 214}


def _crop(img):
    ys, xs = np.nonzero(img)
    return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _components(mask):
    """8-connected components of a boolean mask -> list of (rows, cols) arrays."""
    seen = np.zeros_like(mask); out = []
    h, w = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]: continue
        q = [(y, x)]; seen[y, x] = True; pts = []
        while q:
            a, b = q.pop(); pts.append((a, b))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    Y, X = a + dy, b + dx
                    if 0 <= Y < h and 0 <= X < w and mask[Y, X] and not seen[Y, X]:
                        seen[Y, X] = True; q.append((Y, X))
        pts = np.array(pts); out.append((pts[:, 0], pts[:, 1]))
    return out


class Roshi:
    def __init__(self, krillin, roshi, chin_k, chin_r, beard_rows=7):
        """krillin, roshi: {view: standing frame (BF colour indices)}. chin_k / chin_r: rows (from the top of the figure) where each head ends."""
        self.tpl = {}; self.lying = []; self.hits = self.misses = self.dressed = 0
        self.beard = beard_rows
        for v in (0, 1, 2):
            k = _crop(krillin[v]); r = _crop(roshi[v])
            head_k = k[:chin_k].copy()
            head_k[~np.isin(head_k, list(SKIN | {16, 1, 202, 203}))] = 0     # only the head's own colours: no collar
            head_r = r[:chin_r + beard_rows].copy()
            below = np.zeros(head_r.shape, bool); below[chin_r:] = True
            head_r[below & ~np.isin(head_r, list(BEARD))] = 0                 # under the chin only the beard comes along
            if v == 1: head_r[below] = 0                                       # no beard seen from behind
            ck = np.nonzero(head_k.any(0))[0]; cr = np.nonzero(r[:chin_r].any(0))[0]
            ts = [(head_k, head_r, (ck[0] + ck[-1]) / 2, (cr[0] + cr[-1]) / 2)]
            if v == 2:
                wk, wr = head_k.shape[1], head_r.shape[1]
                ts.append((head_k[:, ::-1], head_r[:, ::-1], wk - 1 - (ck[0] + ck[-1]) / 2, wr - 1 - (cr[0] + cr[-1]) / 2))
                for t in ts:
                    for rot in (1, 3): self.lying.append((np.rot90(t[0], rot), np.rot90(t[1], rot), t, rot))
            self.tpl[v] = ts
        self.chin_k, self.chin_r = chin_k, chin_r

    def _find(self, img, cands, ys):
        best = (0, None, 0, 0); h, w = img.shape
        for t in cands:
            head = t[0]; hh, hw = head.shape; ink = head != 0; total = ink.sum()
            for dy in ys:
                for dx in range(-6, w - hw + 7):
                    y0, y1, x0, x1 = max(dy, 0), min(dy + hh, h), max(dx, 0), min(dx + hw, w)
                    if y1 <= y0 or x1 <= x0: continue
                    sub = ink[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
                    score = ((img[y0:y1, x0:x1] == head[y0 - dy:y1 - dy, x0 - dx:x1 - dx]) & sub).sum() / total
                    if score > best[0]: best = (score, t, dx, dy)
        return best

    def place(self, t, dx, dy, lying):
        """Where Roshi's (possibly turned) head goes: his chin on Krillin's, centres lined up. -> (image, top, left)."""
        ck, cr = self.chin_k, self.chin_r
        if not lying:
            head_k, head_r, kc, rc = t
            return head_r, dy - (cr - ck), int(round(dx + kc - rc))
        head_k, head_r, (_, up_r, kc, rc), rot = t
        wk, wr = t[2][0].shape[1], up_r.shape[1]
        if rot == 1:      # counter-clockwise: the head's top points left, the chin right (upright row y -> column y; column x -> row w-1-x)
            return head_r, int(round(dy + (wk - 1 - kc) - (wr - 1 - rc))), dx + ck - cr
        return head_r, int(round(dy + kc - rc)), dx - self.beard     # clockwise: the chin points left

    def apply(self, src, view):
        img = src.copy(); h, w = img.shape
        body = np.zeros((h, w), bool)                       # the figure without the specks round it (dizzy stars, swipe trails)
        for ys, xs in _components(img != 0):
            if len(ys) >= 12: body[ys, xs] = True
        rows = np.nonzero(body.any(1))[0]; cols = np.nonzero(body.any(0))[0]
        if not len(rows): return img
        top = rows[0]; height, width = rows[-1] - top + 1, cols[-1] - cols[0] + 1
        lying = width >= 1.6 * height
        if lying:
            score, t, dx, dy = self._find(img, self.lying, range(top - 12, top + 8)); ok = t is not None and score >= 0.40
        else:
            score, t, dx, dy = self._find(img, self.tpl[0] + self.tpl[1] + self.tpl[2], range(top - 6, top + 4)); ok = t is not None and score >= 0.45
            if ok:      # the back of his head only where Krillin shows no face (some animations use one run of frames for every direction)
                hk = t[0].shape; inner = img[max(dy + 2, 0):max(dy + hk[0] - 2, 0), max(dx + 2, 0):max(dx + hk[1] - 2, 0)]
                face = (inner == 1).sum() >= 2
                back = any(t is b for b in self.tpl[1])
                if back and face or (not back and not face and view == 1):
                    alt = self._find(img, self.tpl[0] + self.tpl[2] if face else self.tpl[1], range(top - 6, top + 4))
                    if alt[1] is not None and alt[0] >= 0.35: score, t, dx, dy = alt
        head_box = None
        if not ok and not lying:
            blob = self._bald(img, top)
            if blob is not None:                        # Krillin's head turned in a way his standing views don't show: his bald blob, and the nearest view of Roshi's
                y0, y1, x0, x1, cover = blob
                img[cover] = 0
                hr = self.tpl[view][0][1]; rc = self.tpl[view][0][3]
                oy = y1 - self.chin_r; ox = int(round((x0 + x1 - 1) / 2 - rc))
                for y in range(hr.shape[0]):
                    for x in range(hr.shape[1]):
                        Y, X = oy + y, ox + x
                        if 0 <= Y <= rows[-1] and 0 <= X < w and hr[y, x]: img[Y, X] = hr[y, x]
                head_box = (oy, ox) + hr.shape
                self.hits += 1; self.blobs = getattr(self, 'blobs', 0) + 1
                self._dress(img, src, lying, head_box)
                return img
        if ok:
            self.hits += 1
            head_k = t[0]; hk = head_k.shape
            cover = np.zeros((h, w), bool)                  # Krillin's head: his template's pixels, and skin or outline touching them inside its box
            HEADC = SKIN | {16, 1, 202, 203}
            for y in range(hk[0]):
                for x in range(hk[1]):
                    Y, X = y + dy, x + dx
                    if 0 <= Y < h and 0 <= X < w and head_k[y, x] and img[Y, X] in HEADC: cover[Y, X] = True
            q = list(zip(*np.nonzero(cover)))
            while q:
                y, x = q.pop()
                for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if dy - 1 <= Y < dy + hk[0] and dx - 1 <= X <= dx + hk[1] and 0 <= Y < h and 0 <= X < w and not cover[Y, X] and img[Y, X] in HEADC:
                        cover[Y, X] = True; q.append((Y, X))
            img[cover] = 0
            hr, oy, ox = self.place(t, dx, dy, lying)
            ry, rx = hr.shape
            for y in range(ry):
                for x in range(rx):
                    Y, X = oy + y, ox + x
                    if 0 <= Y <= rows[-1] and 0 <= X < w and hr[y, x]: img[Y, X] = hr[y, x]
            head_box = (oy, ox, ry, rx)
        else:
            self.misses += 1
        if head_box and not lying:                         # crawling or lying on his front with the head up: the body runs sideways from the head
            fy, fx = np.nonzero(body)
            hx, chin = head_box[1] + head_box[3] / 2, head_box[0] + self.chin_r
            if max(hx - fx.min(), fx.max() - hx) - head_box[3] / 2 > 2 * (fy.max() - chin):
                self._dress(img, src, True, head_box, crawl=True)
                return img
        self._dress(img, src, lying, head_box)
        return img

    def _bald(self, img, top):
        """The top of an upright figure is Krillin's bald head: the skin-and-outline blob there, about a head's size. -> (y0, y1, x0, x1, mask) or None."""
        h, w = img.shape
        HEADC = SKIN | {16, 1, 202, 203}
        m = np.isin(img, list(HEADC)); m[top + self.chin_k + 2:] = False
        seeds = [(top + d, x) for d in range(3) for x in range(w) if top + d < h and m[top + d, x]]
        if not seeds: return None
        comp = np.zeros((h, w), bool); q = seeds[:]
        for y, x in q: comp[y, x] = True
        while q:
            y, x = q.pop()
            for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= Y < h and 0 <= X < w and m[Y, X] and not comp[Y, X]: comp[Y, X] = True; q.append((Y, X))
        ys, xs = np.nonzero(comp)
        # stop at the neck: the first row under the head's widest part that is much narrower, or the chin's depth
        widths = [comp[y].sum() for y in range(ys.min(), ys.max() + 1)]
        y1 = ys.min() + min(len(widths), self.chin_k)
        comp[y1:] = False
        ys, xs = np.nonzero(comp)
        if not len(ys) or not 8 <= xs.max() - xs.min() + 1 <= 16 or ys.max() - ys.min() + 1 < 8: return None
        return ys.min(), y1, xs.min(), xs.max() + 1, comp

    def _dress(self, img, src, lying, head_box, crawl=False):
        """Shorts, sandals and bare forearms. Blue parts of Krillin's gi are told apart by where they are."""
        h, w = img.shape
        blue = np.isin(src, list(BLUE)) & np.isin(img, list(BLUE))
        rows = np.nonzero(img.any(1))[0]; cols = np.nonzero(img.any(0))[0]
        if not len(rows): return
        bottom = rows[-1]
        comps = _components(blue)
        head_c = None
        if head_box: head_c = (head_box[0] + head_box[2] / 2, head_box[1] + head_box[3] / 2)
        belt = None
        for ys, xs in comps:                                   # the belt: the widest blue band across the waist
            wd, ht = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
            long_, short = (ht, wd) if lying else (wd, ht)
            if long_ >= 4 and long_ >= 1.5 * short:
                if not lying and ys.mean() > bottom - 4: continue    # not the boots
                if head_box and not lying and not head_box[0] + self.chin_r + 1 <= ys.mean() <= head_box[0] + self.chin_r + 10: continue   # not a forearm held high or low
                if belt is None or len(ys) > len(belt[0]): belt = (ys, xs)
        if lying and head_box: belt = None                      # lying: the head says where the waist is better than a short blue patch does
        if belt is not None:
            by, bx = belt[0].mean(), belt[1].mean()
        elif head_box and not lying:                           # no belt in sight (an arm across it): the waist sits five rows under the chin
            by, bx = head_box[0] + self.chin_r + 5, head_c[1]
        elif head_box:                                         # lying: the waist is a head and five pixels from the head's centre, towards the body
            fy, fx = np.nonzero(img)
            way = 1 if fx.mean() > head_c[1] else -1
            by, bx = head_c[0], head_c[1] + way * ((head_box[3] / 2 + 1) if crawl else (self.chin_r / 2 + 9))   # crawling, the body is under the head; lying, beside it
        else:
            return
        self.dressed += 1
        def side_of(y, x):                                     # >0: on the legs' side of the belt
            if not lying: return y - by
            if head_c is None: return 0
            return (x - bx) * (1 if bx > head_c[1] else -1)
        for ys, xs in comps:
            is_belt = belt is not None and len(ys) == len(belt[0]) and (ys == belt[0]).all() and (xs == belt[1]).all()
            if is_belt: table = BELT
            elif (not lying and ys.max() >= bottom - 3) or (lying and min(abs(side_of(y, x)) for y, x in zip(ys, xs)) > 6 and np.mean([side_of(y, x) for y, x in zip(ys, xs)]) > 6):
                table = BOOTS
            elif head_box and not lying and ys.min() <= head_box[0] + self.chin_r + 3 and abs(xs.mean() - head_c[1]) <= 4 and ys.mean() < by:
                table = SHIRT
            else:
                table = WRIST
            for y, x in zip(ys, xs): img[y, x] = table.get(int(img[y, x]), img[y, x])
        legs = np.isin(img, list(ORANGE))
        if belt is None:
            for y, x in zip(*np.nonzero(legs)):
                if side_of(y, x) > 0.5: img[y, x] = ORANGE[int(img[y, x])]
            return
        # the trousers: orange reached from below the belt, which may come up beside it a little (a raised knee) but not over it
        mark = np.zeros((h, w), bool)
        q = [(y, x) for y, x in zip(*np.nonzero(legs)) if side_of(y, x) > 1.5]
        for y, x in q: mark[y, x] = True
        while q:
            y, x = q.pop()
            for Y, X in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= Y < h and 0 <= X < w and legs[Y, X] and not mark[Y, X] and side_of(Y, X) > -3:
                    mark[Y, X] = True; q.append((Y, X))
        for y, x in zip(*np.nonzero(mark)): img[y, x] = ORANGE[int(img[y, x])]
