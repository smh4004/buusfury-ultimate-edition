"""Putting one figure's head on another's frames without it sitting off the neck (Nov 11, the owner: "make sure the new Teen Gohan
sprites don't have any alignment issues with the head or neck and don't allow that to happen anymore"). The rule: nothing is taken
from a frame before the frame is PLACED on the one it goes onto, by pixels both must share (the same face, the same armor), and a frame
that can't be placed with certainty stops the build (Off). Records place their own frames a pixel left, right, up or down of each
other, so "the same spot on the canvas" is not the same spot on the body.
Frames here are 2D arrays of colour indices on one canvas (0 = nothing), all cut the same way round their record's origin."""
import numpy as np


class Off(Exception):
    """A frame that can't be placed or doesn't pass its checks: the build must stop, never guess."""


def cls(*sets):
    m = np.zeros(256, bool)
    for s in sets: m[list(s)] = True
    return m


def shift(a, dx, dy):
    out = np.zeros_like(a); h, w = a.shape
    ys, xs = slice(max(dy, 0), h + min(dy, 0)), slice(max(dx, 0), w + min(dx, 0))
    yt, xt = slice(max(-dy, 0), h + min(-dy, 0)), slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yt, xt]; return out


def witness(a, b, c, R=5):
    """Every offset of b on a scored for the pixels of b in class c: -> ((dx, dy), equal there, meeting there, the next best's equal).
    Equal: b's pixel lands on the same colour in a. Meeting: it lands on any pixel of the class."""
    res = []
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            sb = shift(b, dx, dy); k = c[sb]
            res.append((int(((a == sb) & k).sum()), -abs(dx) - abs(dy), (dx, dy), int((c[a] & k).sum())))
    res.sort(reverse=True)
    return res[0][2], res[0][0], res[0][3], res[1][0]


def place(a, b, what, *witnesses):
    """Where b sits on a, or Off. Each witness is (class, least equal pixels, least share of the pixels that meet, how far ahead of the
    next best offset). One witness that passes all three places the frame; so do two that pass the first two and name the same
    offset (two kinds of pixels agreeing is as good as one standing clear). A witness with enough pixels that names another offset
    than the one chosen stops the build."""
    seen = []
    for c, least, share, ahead in witnesses:
        o, eq, meet, nxt = witness(a, b, c)
        seen.append((o, eq, meet, nxt, eq >= least and eq >= share * meet, eq >= ahead * nxt))
    clear = [w[0] for w in seen if w[4] and w[5]]
    solid = [w[0] for w in seen if w[4]]
    pick = clear[0] if clear else next((o for o in solid if solid.count(o) >= 2), None)
    tell = '; '.join('%+d%+d %d of %d, next %d' % (*w[0], w[1], w[2], w[3]) for w in seen)
    if pick is None: raise Off('%s: nothing places it (%s)' % (what, tell))
    if any(o != pick for o in solid): raise Off('%s: the witnesses disagree (%s)' % (what, tell))
    return pick


def flood(seed, grow, eight=False):
    """The pixels of `grow` that hang together with `seed` (4 neighbours, or 8)."""
    m = seed & grow
    while True:
        n = m.copy(); n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        if eight:
            n[1:, 1:] |= m[:-1, :-1]; n[1:, :-1] |= m[:-1, 1:]; n[:-1, 1:] |= m[1:, :-1]; n[:-1, :-1] |= m[1:, 1:]
        n &= grow
        if (n == m).all(): return m
        m = n


def ringed(cand, head):
    """Of the candidate pixels, those with head (or other such candidates) on all four sides: what lies inside a head."""
    blk = cand.copy()
    while True:
        ok = head | blk; inside = blk.copy()
        inside[1:] &= ok[:-1]; inside[:-1] &= ok[1:]; inside[:, 1:] &= ok[:, :-1]; inside[:, :-1] &= ok[:, 1:]
        inside[0] = inside[-1] = False; inside[:, 0] = inside[:, -1] = False
        if (inside == blk).all(): return blk
        blk = inside


def face_at(body, made, skin):
    """Where the finished frame's face sits against the frame its body came from, by the skin both show: (offset, equal, meeting,
    next best). The offset must be (0, 0)."""
    return witness(body, np.where(skin[made], made, 0), skin)


def holes(made):
    """Empty pixels with the figure on all four sides."""
    f = made != 0; h = ~f
    h[1:] &= f[:-1]; h[:-1] &= f[1:]; h[:, 1:] &= f[:, :-1]; h[:, :-1] &= f[:, 1:]
    h[0] = h[-1] = False; h[:, 0] = h[:, -1] = False
    return h


def grown(m, r):
    """m with every pixel within r of it (a square)."""
    out = m.copy(); h, w = m.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            ys, xs = slice(max(dy, 0), h + min(dy, 0)), slice(max(dx, 0), w + min(dx, 0))
            yt, xt = slice(max(-dy, 0), h + min(-dy, 0)), slice(max(-dx, 0), w + min(-dx, 0))
            out[ys, xs] |= m[yt, xt]
    return out
