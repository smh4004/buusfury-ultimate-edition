"""Super Saiyan Blue Gogeta's hair from Super Saiyan Blue Goku's (Nov 10, the owner: "Gogeta blues hair is still fucked too looks totally
wrong. Use SSB Golu [Goku] and a basis and get the color and shape fully accurate").

Gogeta's figure is his Super Saiyan's (the DBS sheet's cells, gogeta.py). Its gold hair is a rounded mass in a black outline, so turned blue
it was a flat cyan blob. Each of his frames now loses that hair (the gold, its black outline and the black strokes inside it) and takes
the hair of the Goku frame whose hair is the closest shape in the same view (BF's Super Saiyan Goku, actor 109, every frame; view = down,
up or side, so a back is never given a front's hair, and a fall's tilted head finds Goku's own fall), turned blue exactly as Goku's Super
Saiyan Blue is (build.ssb_hair: a dark blue edge, two blues and the pale highlights, no black). Goku's hair is laid where his best overlap
puts it, only over empty pixels and Gogeta's old hair: never over the face, the eyes or the body.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GOKU_SS = 109                 # BF Super Saiyan Goku (his Blue is this figure with ssb_hair)
BLACK = (1,)                  # the outline's black (0 is see-through)
SHIFT = 7                     # how far (pixels, each way) a template is slid to find its best overlap
# Gogeta's slots where he stands up (all but the hit, flying and falls: 7, 15, 16, 17) take hair from Goku's standing poses only (idle, walk,
# run, ki, melee, power-up, strikes, firing): his victory pose and his falls tilt the head, and their flattened hair could overlap best.
FALLS = (7, 15, 16, 17)
STANDING = (0, 1, 2, 3, 4, 5, 6, 8, 9, 13, 14, 18, 20, 21)


def goku_templates(clean, ssb):
    """{view: [(blue image, hair mask, Goku's slot)]}: every distinct hair of BF Super Saiyan Goku's frames, cropped to the hair, turned
    blue by `ssb` (build.ssb_hair's function: the hair is exactly the pixels it changes)."""
    sys.path[:0] = [os.path.dirname(HERE)]
    import goku_black
    from scipy import ndimage
    out = {0: [], 1: [], 2: []}; seen = set()
    for slot, views in goku_black.actor_frames(clean, GOKU_SS).items():
        for d in range(3):
            for c in views[d]:
                blue = ssb(c); hair = blue != c
                if hair.sum() < 12: continue
                lab, n = ndimage.label(hair, np.ones((3, 3)))             # the hair itself: sparks of his Super Saiyan glow apart from it go
                if n > 1: hair = lab == np.bincount(lab.ravel())[1:].argmax() + 1
                ys, xs = np.nonzero(hair)
                crop = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
                img, m = np.where(hair, blue, 0)[crop].astype(np.uint8), hair[crop]
                key = (d, img.shape, img.tobytes())
                if key in seen: continue
                seen.add(key); out[d].append((img, m, slot))
    return out


def gogeta_hair(a, b, only_hair, shared):
    """Gogeta's hair in his Super Saiyan frame `a` (index image) with `b` his base frame on the same grid: the gold (only_hair everywhere,
    the shared gold only where his base figure has black hair or nothing), the black strokes inside it, and its black outer outline."""
    gold = np.isin(a, list(only_hair)) | (np.isin(a, list(shared)) & np.isin(b, [0, 1]))
    black = np.isin(a, BLACK)
    def nb(m):
        p = np.pad(m, 1)
        return [p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]
    hair = gold.copy()
    for _ in range(2):                     # strokes and the edge: black beside the hair and beside nothing, or inside it
        n = nb(hair); empty = nb(a == 0); body = nb(~hair & (a != 0) & ~black)
        k = sum(x.astype(int) for x in n)
        edge = black & (k >= 1) & np.any(empty, 0) & ~np.any(body, 0)
        inner = black & (k >= 3)
        hair |= edge | inner
    return hair


LOSS = 0.01                   # a hair pixel that won't fit the 32 rows above his feet costs this much overlap


def best(hair, body, d, templates, pool=None):
    """The template (and its offset onto `hair`'s grid) whose hair overlaps Gogeta's most (intersection over union), less LOSS for each of
    its pixels that falls above the 32 rows a frame has (his feet stay where they are, so those spike tips are cut off): a hair a little
    taller than his can win, a flattened one doesn't win only because it fits."""
    H, W = hair.shape; top = None
    ys, xs = np.nonzero(hair)
    if not len(ys): return None
    cy, cx = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
    by, _ = np.nonzero(body)
    first = (by.max() if len(by) else ys.max()) - 31                # the highest row one 32-row piece standing on his feet reaches
    area = hair.sum()
    for img, m, slot in templates[d]:
        if pool is not None and slot not in pool: continue
        h, w = m.shape; rows = m.sum(1)
        for dy in range(-SHIFT, SHIFT + 1):
            for dx in range(-SHIFT, SHIFT + 1):
                y0, x0 = cy - h // 2 + dy, cx - w // 2 + dx
                ty0, tx0 = max(0, -y0), max(0, -x0); ty1, tx1 = min(h, H - y0), min(w, W - x0)
                if ty1 <= ty0 or tx1 <= tx0: continue
                inter = (m[ty0:ty1, tx0:tx1] & hair[y0 + ty0:y0 + ty1, x0 + tx0:x0 + tx1]).sum()
                iou = inter / (area + m.sum() - inter)
                lost = rows[:max(0, min(h, first - y0))].sum()
                score = iou - LOSS * lost
                if top is None or score > top[0]: top = (score, iou, (img, m), (y0, x0))
    return top


PAD = 16                      # room round a frame for the new hair: the result is cut back to one piece (blue_hair_actor's put_frame)


def blue(a, b, d, templates, only_hair, shared, slot=0):
    """Gogeta's frame `a` with Super Saiyan Blue Goku's hair in place of his own (see the module's note); `d` 0-3 (3, the mirrored side
    view, is the side view's own image). The frame is laid on a canvas PAD wider each side and PAD taller above, so the spikes have room,
    and the hair is the best overlap less what falls above the 32 rows one piece (1 KB of OBJ memory, as every frame) has over his feet. The black of
    Gogeta's old outline left along the new hair's outer edge goes (Goku's Blue hair has a dark blue edge, no black).
    Returns (canvas, (x, y) of the canvas's corner from the frame's, overlap)."""
    a, b = np.pad(a, ((PAD, 0), (PAD, PAD))), np.pad(b, ((PAD, 0), (PAD, PAD)))
    hair = gogeta_hair(a, b, only_hair, shared)
    body = (a != 0) & ~hair
    found = best(hair, body, min(d, 2), templates, None if slot in FALLS else STANDING)
    if not found or found[2] is None: return a, (-PAD, -PAD), 0.0
    _, iou, (img, m), (y0, x0) = found
    out = a.copy(); out[hair] = 0; new = np.zeros(a.shape, bool)
    h, w = m.shape; H, W = a.shape
    for y in range(h):
        for x in range(w):
            Y, X = y0 + y, x0 + x
            if m[y, x] and 0 <= Y < H and 0 <= X < W and (a[Y, X] == 0 or hair[Y, X]): out[Y, X] = img[y, x]; new[Y, X] = True
    def nb(m):
        p = np.pad(m, 1)
        return np.stack([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
    for _ in range(2):
        black = np.isin(out, BLACK); body = (out != 0) & ~black & ~new
        stray = black & nb(new).any(0) & nb(out == 0).any(0) & ~nb(body).any(0)
        orphan = black & nb(hair).any(0) & ~nb((out != 0) & ~black).any(0)       # a bit of the old outline left on its own
        out[stray | orphan] = 0
    return out, (-PAD, -PAD), iou
