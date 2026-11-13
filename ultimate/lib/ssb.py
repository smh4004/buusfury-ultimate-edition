"""Super Saiyan Blue hair, every pixel of it (Nov 10, the owner: "FIX SSB GOKUS HAIR NOT BEING FULLY BLUE WHY IS THERE STILL YELLOW").

BF's Super Saiyan hair and skin share colours (202, 201 and 16 are both a hair's shading and a face's), so build.ssb_hair took a ramp pixel
for hair only within 3 pixels of the hair's own highlights (28, 29, 2) and nearer them than the face: the spike tips, the outline far from
a highlight and the hairline stayed gold. Here each Super Saiyan frame is laid on the same frame of the base figure (same slot, frame and
view, where the game draws them): a ramp pixel is hair where the base figure has its black hair or nothing, and it is kept with the patch
of such pixels it touches that holds the hair's highlights (so his arms, where a pose moved them, stay skin). The old rule's pixels count
too; a frame the base figure lacks keeps the old rule alone.
"""
import struct
import numpy as np

BASE, ACTOR_LIST = 0x08000000, 0x6B6BD8
LIGHTS = (28, 29, 2)            # the hair's highlights
FACE = (200, 203, 215, 216, 117)  # the face's own colours (its light skin, the eyes)
IRIS = (215, 216)               # the eyes' green
SKIN = (16, 202, 201)           # the skin's shades, which the hair's ramp shares
ISLAND = 3                      # hair_mask: a speck of skin shades this small that the hair walls in is hair
HEAD = 4                        # fill: the hairline and the temples are this near an eye
BASE_HAIR = (0, 1, 112)         # nothing, or the base figure's black hair (and its grey shine)
O = 48                          # canvas margin
SHIFT = 3                       # how far base_under looks for the base figure
NOT_BODY = (0, 1, 112, 16, 202, 201, 28, 29, 2, 246)   # not the body's own colours: nothing, black hair, the Super Saiyan ramp


def _frames(rom, actor):
    """{(slot, frame, view): frame pointer} for views 0-2."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    rec = u(ACTOR_LIST + 4 * actor) - BASE; out = {}
    for s in range(u(rec) & 0xFF):
        ap = u(rec + 0x54 + 4 * s)
        if not ap: continue
        ap -= BASE
        for k in range(u(ap)):
            for d in range(3):
                fp = u(ap + 4 + 4 * (4 * k + d))
                if BASE < fp < BASE + len(rom): out[(s, k, d)] = fp - BASE
    return out


def _pieces(rom, fp):
    """[(x, y, image, mirrored)] of a frame's pieces."""
    import goku_black
    u = lambda o: struct.unpack_from('<I', rom, o)[0]; out = []
    for i in range(u(fp)):
        o = fp + 4 + 16 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, o)
        if not 0 < u(o + 12) - BASE < len(rom) or not w or not h: continue
        out.append((x, y, goku_black.tiles(rom, u(o + 12) - BASE, w, h), bool(struct.unpack_from('<H', rom, o + 10)[0] & 0x1000)))
    return out


def base_under(rom, ss, base):
    """{(shape, bytes) of a Super Saiyan piece: the base figure's pixels under it} over every frame both figures have. The two figures are
    not always drawn in the same place (Goku's side view: the Super Saiyan figure stands 2 pixels left of the base one), so the base
    figure is shifted up to SHIFT pixels to where its body (the colours that are neither hair nor shared with it) matches the piece best;
    a piece used in several frames takes the frame where it matches best."""
    B = _frames(rom, base); out = {}
    for key, fp in _frames(rom, ss).items():
        if key not in B: continue
        canvas = np.zeros((64 + 2 * O, 64 + 2 * O), np.uint8)
        for x, y, t, flip in _pieces(rom, B[key]):
            if flip: t = t[:, ::-1]
            h, w = t.shape; c = canvas[O + y:O + y + h, O + x:O + x + w]; m = t[:c.shape[0], :c.shape[1]] != 0
            c[m] = t[:c.shape[0], :c.shape[1]][m]
        for x, y, t, flip in _pieces(rom, fp):
            h, w = t.shape; body = (t != 0) & ~np.isin(t, NOT_BODY); best = None
            for dy, dx in sorted(((dy, dx) for dy in range(-SHIFT, SHIFT + 1) for dx in range(-SHIFT, SHIFT + 1)), key=lambda d: abs(d[0]) + abs(d[1])):
                under = canvas[O + y + dy:O + y + dy + h, O + x + dx:O + x + dx + w]
                under = under[:, ::-1] if flip else under                                     # (in the piece's own orientation)
                score = ((under == t) & body).sum() / max(1, body.sum())
                if best is None or score > best[0]: best = (score, under.copy())
            k = (t.shape, t.tobytes())
            if k not in out or best[0] > out[k][0]: out[k] = best
    return {k: v[1] for k, v in out.items()}


def piece_unders(rom, fp, ref):
    """Blue's change (Nov 12, the owner: "Gokus hair turns SSJ3 in the SSB transformation", "make them not raise their hands but do the
    normal pose"): the base figure's own change (slot 10) has the Super Saiyan frames, and before them the same pose with his black hair.
    {piece index: the pixels of frame `ref` (that black-haired frame) under the piece} for each piece of frame `fp` (file offsets), found
    as base_under finds them."""
    import goku_black
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    canvas = np.zeros((64 + 2 * O, 64 + 2 * O), np.uint8)
    for x, y, t, flip in _pieces(rom, ref):
        if flip: t = t[:, ::-1]
        h, w = t.shape; c = canvas[O + y:O + y + h, O + x:O + x + w]; m = t[:c.shape[0], :c.shape[1]] != 0
        c[m] = t[:c.shape[0], :c.shape[1]][m]
    out = {}
    for i in range(u(fp)):
        o = fp + 4 + 16 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, o)
        if not 0 < u(o + 12) - BASE < len(rom) or not w or not h: continue
        t = goku_black.tiles(rom, u(o + 12) - BASE, w, h); flip = bool(struct.unpack_from('<H', rom, o + 10)[0] & 0x1000)
        body = (t != 0) & ~np.isin(t, NOT_BODY); best = None
        for dy, dx in sorted(((dy, dx) for dy in range(-SHIFT, SHIFT + 1) for dx in range(-SHIFT, SHIFT + 1)), key=lambda d: abs(d[0]) + abs(d[1])):
            under = canvas[O + y + dy:O + y + dy + h, O + x + dx:O + x + dx + w]
            under = under[:, ::-1] if flip else under
            score = ((under == t) & body).sum() / max(1, body.sum())
            if best is None or score > best[0]: best = (score, under.copy())
        out[i] = best[1]
    return out


def tint_piece(img, under, to, sides=False, eyes=False, iris=IRIS):
    """One piece's hair blue against `under` (tint's rule for a piece whose base pixels are known)."""
    hair = hair_mask(img, under, list(to), sides)
    out = img.copy()
    for k, v in to.items(): out[hair & (img == k)] = v
    return face(img, out, under, to, iris) if eyes else out


def eye_whites(img):
    """The whites of the eyes: white (2, also the hair's brightest) beside the green of an eye (Nov 10, the owner: "Fix some of SSB Goku
    and vegetas face pixels being blue": the hair rules took them, and the face pixels near them, for hair)."""
    from scipy import ndimage
    return (img == 2) & ndimage.binary_dilation(np.isin(img, IRIS), np.ones((3, 3), bool))


def old_rule(img, ramp):
    """build.ssb_hair's rule (cut 3): a ramp pixel within 3 pixels of the hair's highlights and nearer them than the face; the eyes'
    whites are face, not highlights."""
    from scipy import ndimage
    ew = eye_whites(img)
    dh = ndimage.distance_transform_edt(~(np.isin(img, LIGHTS) & ~ew))
    df = ndimage.distance_transform_edt(~(np.isin(img, FACE) | ew))
    return np.isin(img, ramp) & ~ew & (dh < df) & (dh <= 3)


def hair_mask(img, under, ramp, sides=False):
    """The Super Saiyan hair in one piece `img` (see the note above); `under` the base figure's pixels under it, or None (the old rule
    alone). A pixel only the base figure makes hair that has the figure's body (not hair, not empty) to its left, its right or above it is
    the face's or the neck's outline where the base figure's hair hung over it (Vegeta's brow and jaw, Goku's cheeks; Nov 10, the owner:
    "Fix some of SSB Goku and vegetas face pixels being blue"); with the body only below it, it is the hairline and stays hair. Then
    `fill` and `sideburns`. Last, nothing drawn exactly as on the base figure is hair: that is his skin, his forehead between the bangs
    and his ears (Nov 10, the owner: "DONT MAKE THEIR FUCKING FOREHEAD SKIN BLUE OR THEIR EARS EITHER JUST THE HAIR"), unless it is in a
    speck of up to ISLAND pixels the hair walls in on every side."""
    from scipy import ndimage
    old = old_rule(img, ramp)
    if under is None: return old
    same = (img == under) & np.isin(img, SKIN)                                   # (his skin's shades only: a ki blast stays as it was)
    cand = np.isin(img, ramp) & ~eye_whites(img) & (np.isin(under, BASE_HAIR) | old)
    lab, n = ndimage.label(cand, np.ones((3, 3)))
    keep = set(np.unique(lab[old | (cand & np.isin(img, LIGHTS))]).tolist()) - {0}
    add = np.isin(lab, list(keep)) & ~old
    p = np.pad((img != 0) & ~cand, 1)                                              # the body
    side = p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, 1:-1]                              # left, right, above
    hair = old | (add & ~side)
    lab, n = ndimage.label(hair, np.ones((3, 3)))                                 # what that cut off from the hair (a stub under Vegeta's ear)
    hair = np.isin(lab, list(set(np.unique(lab[old | (hair & np.isin(img, LIGHTS))]).tolist()) - {0}))
    hair = fill(img, hair, under, ramp, same)
    for _ in range(4):                                                            # (each closes gaps for the other)
        more = fill(img, sideburns(img, hair, under, ramp, same) if sides else hair, under, ramp, same)
        if (more == hair).all(): break
        hair = more
    hair &= ~same
    lab, n = ndimage.label(np.isin(img, ramp) & ~hair)                            # (but a speck of up to ISLAND pixels the hair walls in
    for k in range(1, n + 1):                                                     # on every side is the hair's: no skin shows there)
        m = lab == k
        if m.sum() <= ISLAND and hair[ndimage.binary_dilation(m) & ~m].all(): hair = hair | m
    return hair


def sideburns(img, hair, under, ramp, same):
    """Hair the Super Saiyan figure draws where the base figure has skin: Goku's sideburn in front of his ear, and the hair down the back
    of his head, seen from the side (Nov 10, the owner: "THE SIDES OF GOKUS HAIR AROUND HIS EARS ARE YELLOW STILL"). Seen from the side
    only (one eye), on the eye's rows (and the one above), behind the eye only (away from his face), not beside an eye: a ramp pixel
    drawn differently from the base figure with hair at its left, its right or above it is hair; repeated. Never his face: Vegeta's cheek
    and forehead (Nov 10, the owner: "you put the blue pixel back in vegetas face again")."""
    from scipy import ndimage
    iris = np.isin(img, IRIS)
    lab, n = ndimage.label(iris, np.ones((3, 3)))
    if n != 1: return hair                                                        # facing us (or no face): nothing
    rows, cols = np.nonzero(iris)
    figure = np.nonzero(img[rows.min():rows.max() + 1].any(0))[0]
    zone = np.zeros(img.shape, bool)
    if cols.min() - figure.min() < figure.max() - cols.max(): zone[rows.min() - 1:rows.max() + 1, cols.max() + 2:] = True   # facing left
    else: zone[rows.min() - 1:rows.max() + 1, :max(0, cols.min() - 1)] = True                                               # facing right
    eyes = iris | np.isin(img, (117, 118)) | eye_whites(img)
    p = np.pad(eyes, 1); by_eye = p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, 1:-1] | p[2:, 1:-1]
    cand = zone & np.isin(img, ramp) & ~eye_whites(img) & ~same & ~by_eye & ~np.isin(under, BASE_HAIR)
    for _ in range(8):
        h = np.pad(hair, 1)
        add = cand & ~hair & (h[1:-1, :-2] | h[1:-1, 2:] | h[:-2, 1:-1])
        if not add.any(): break
        hair = hair | add
    return hair


def fill(img, hair, under, ramp, same=None):
    """The hair's shades the rules above left gold at its edge (Nov 10, the owner: "YOU STILL HAVE LEFT YELLOW ON THE SIDES OF GOKU SSB"):
    a ramp pixel with no skin or eye to its left, its right or above it is hair if hair is on three of its sides (a gap in the bangs), if
    hair is above it and the face below it (the hair's last row over the face), if hair is above it and on one side and the base figure
    has its hair there, or if hair is on one side and nothing on the rest and the base figure has its hair there (a side lock's end).
    Repeated while it adds any; then, once (repeated it would run on down the side of the face), a ramp pixel with hair above it and to
    one side: the hair's inner corner by the temple. The hairline and the temples are within HEAD pixels of an eye (so not the top of a
    shoulder under the hair, running)."""
    face = np.pad(np.isin(img, FACE) | eye_whites(img), 1)
    beside = face[1:-1, :-2] | face[1:-1, 2:] | face[:-2, 1:-1]
    from scipy import ndimage
    head = ndimage.binary_dilation(np.isin(img, IRIS) | eye_whites(img), np.ones((2 * HEAD + 1, 2 * HEAD + 1), bool))
    below = face[2:, 1:-1] & head                                                # (the face's skin, not an arm's or a shoulder's)
    shade = np.isin(img, ramp) & ~eye_whites(img) & ~beside & (~same if same is not None else True)
    based = np.isin(under, BASE_HAIR) if under is not None else np.zeros(img.shape, bool)
    e = np.pad(img == 0, 1); ne = e[:-2, 1:-1].astype(int) + e[2:, 1:-1] + e[1:-1, :-2] + e[1:-1, 2:]
    def grow(hair):
        for _ in range(8):
            h = np.pad(hair, 1); nh = h[:-2, 1:-1].astype(int) + h[2:, 1:-1] + h[1:-1, :-2] + h[1:-1, 2:]
            add = shade & ~hair & ((nh >= 3) | (h[:-2, 1:-1] & (below | (nh >= 2) & based)) | ((nh >= 1) & (nh + ne >= 3) & based))
            if not add.any(): break
            hair = hair | add
        return hair
    hair = grow(hair)
    h = np.pad(hair, 1)                                                           # then, once, the hair's inner corners: hair above it and
    hair = grow(hair | (shade & head & h[:-2, 1:-1] & (h[1:-1, :-2] | h[1:-1, 2:])))   # beside it (where his hair wraps the temple), again
    return hair


EYE_GREYS = (117, 118)          # the eyes' grey (their shaded white)
LOG2_IRIS = (12, 11)            # the armour Vegetas' eyes (Gero's Legacy greens): light, dark
CROSS = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)


def face(img, out, under, to, iris=IRIS):
    """Blue's eyes and brows (Nov 11, the owner: "eyebrows and pupils match their hair"). The pupils' green takes the hair's blue (the
    light green) and its dark blue (the dark green). The brows are the face's dark shades (16 and 202) in the row over the eyes, from two
    pixels before the first eye to two past the last: never at the figure's edge (the forehead's outline, seen from the side), never a
    pixel the base figure draws in the same skin shade (Goku's forehead by his hairline), never one the hair already took. They take the
    hair's colour for that shade. `iris` is (light, dark)."""
    from scipy import ndimage
    eyes = np.isin(img, iris)
    if not eyes.any(): return out
    out = out.copy()
    out[img == iris[0]] = to[202]; out[img == iris[1]] = to[16]
    whites = (np.isin(img, (2, 120))) & ndimage.binary_dilation(eyes, np.ones((3, 3), bool))
    ys, xs = np.nonzero(eyes | np.isin(img, EYE_GREYS) | whites)
    r0 = ys.min()
    if r0 == 0: return out
    band = np.zeros(img.shape, bool); band[r0 - 1, max(0, xs.min() - 2):xs.max() + 3] = True
    edge = ndimage.binary_dilation(img == 0, CROSS); edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    same = (under == img) & ~np.isin(under, (1, 16)) if under is not None else np.zeros(img.shape, bool)
    brow = band & np.isin(img, (16, 202)) & (out == img) & ~edge & ~same
    for k in (16, 202): out[brow & (img == k)] = to[k]
    return out


def tint(rom, ss, base, to, sides=False, eyes=False, iris=IRIS):
    """A tint function (sprites.tinted_actor) turning Super Saiyan figure `ss`'s hair blue: {ramp index: blue index} `to`, the hair found
    against base figure `base` (or the old rule alone when base is None); `sides`: the hair round his ears seen from the side (sideburns;
    Goku only); `eyes`: the pupils and brows too (face)."""
    under = base_under(rom, ss, base) if base is not None else {}
    ramp = list(to)
    def fn(img):
        u = under.get((img.shape, img.tobytes()))
        hair = hair_mask(img, u, ramp, sides)
        out = img.copy()
        for k, v in to.items(): out[hair & (img == k)] = v
        return face(img, out, u, to, iris) if eyes else out
    return fn


# Super Saiyan Blue Gogeta (Nov 10, the owner: "Literally look at SSJ Gogeta, turn that hair blue colored and use SSB Gokus hair as a
# reference but DONT CHANGE THE SSJ GOGETA HAIR SHAPE", then "Get the fucking hair RIGHT according to BUUS FURY GOGETA"): Buu's Fury's own
# Super Saiyan Gogeta (actor 93, forms 41 and 44), every frame, the hair blue as Blue Goku's. His gold runs 25 (the outline and darkest),
# 26, 27, 28, 29 and 30 (the lightest); by shade they take Goku's Blue colours as Goku's own gold does: his 202 (the outline and dark strands) the
# blue, 201 the shade, 28 the cyan, 29 and white the near-white (and 16, the dark by his face, the dark blue). So 25 the blue (49% of his
# hair, Goku's blue 47%), 26 and 27 the shade (31%, Goku's 23%), 28 the cyan (13%, 17%), 29 and 30 the near-white (8%, 13%). Where his hair's
# shading uses the skin's 202, 201 and 16 (beside his face), those pixels go as Goku's do.
GOGETA = 93
GOGETA_GOLD = {25: 202, 26: 201, 27: 201, 28: 28, 29: 29, 30: 29}    # his gold -> the Goku gold of the same shade
GOGETA_FILL = {8: 9, 11: 0}                                     # slots his figure lacks: the ki blast's, the stance
NEAR = 4                                                        # gold this far from his hair's mass is still hair (his side locks'
                                                                # ends by the jaw: every bit of his gold is within 4 pixels, Nov 10)


def gogeta_hair_mask(img):
    """Gogeta's hair in one frame: his gold (25-30) in the patch of it that is his hair (and bits within NEAR), and the skin shades among
    it (202, 201, 16 with at least two gold neighbours)."""
    from scipy import ndimage
    gold = np.isin(img, list(GOGETA_GOLD))
    if not gold.any(): return gold
    lab, n = ndimage.label(gold, np.ones((3, 3)))
    main = lab == np.bincount(lab.ravel())[1:].argmax() + 1
    near = ndimage.distance_transform_edt(~main) <= NEAR
    hair = np.isin(lab, [t for t in range(1, n + 1) if (near & (lab == t)).any()])
    for _ in range(2):
        p = np.pad(hair, 1)
        k = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        hair |= np.isin(img, (202, 201, 16)) & (k >= 2)
    return hair


def actor_frames(rom, actor):
    """goku_black.actor_frames (32 x 64 canvases, the origin at row 24, column 24), but a mirrored piece drawn mirrored: his knockdown's side
    view (slot 16) is stored the other way round with the mirror bit set."""
    out = {}
    for (s, k, d), fp in sorted(_frames(rom, actor).items()):
        views = out.setdefault(s, [[], [], []]); canvas = np.zeros((32, 64), np.uint8)
        for x, y, t, flip in _pieces(rom, fp):
            if flip: t = t[:, ::-1]
            for r in range(t.shape[0]):
                for c in range(t.shape[1]):
                    R, C = y + 24 + r, x + 24 + c
                    if t[r, c] and 0 <= R < 32 and 0 <= C < 64: canvas[R, C] = t[r, c]
        while len(views[d]) < k: views[d].append(np.zeros((32, 64), np.uint8))
        views[d].append(canvas)
    return out


def gogeta_frames(rom, to, lengths=None, eyes=False):
    """{slot: [[canvas, ...] for views]} of Blue Gogeta: actor 93's frames (goku_black.actor_frames canvases) with his hair blue. `to` is
    {Goku gold index: blue index} (build.SSB_HAIR through the indexer). His change (slot 10): his figure has none of its own, so his
    power-up's (slot 13) crouch, fists at his sides, ten times, then his stance: a retail change's 11 frames (until Nov 12 the crouch twice
    and the shout, arms up, eight times)."""
    frames = actor_frames(rom, GOGETA)
    lut = {g: to[k] for g, k in GOGETA_GOLD.items()}
    lut.update({k: to[k] for k in (202, 201, 16)})
    def blue(c):
        hair = gogeta_hair_mask(c); out = c.copy()
        for k, v in lut.items(): out[hair & (c == k)] = v
        return face(c, out, None, to) if eyes else out
    out = {s: [[blue(c) for c in views[v]] for v in range(3)] for s, views in frames.items()}
    for s, src in GOGETA_FILL.items():
        if s not in out: out[s] = out[src]
    p13, p0 = out[13], out[0]
    out[10] = [[p13[v][0]] * 10 + [p0[v][0]] for v in range(3)]       # the crouch, fists at his sides, ten times, then his stance (Nov 12,
    return out                                                           # the owner: "not raise their hands"; it had the shout, arms up)
