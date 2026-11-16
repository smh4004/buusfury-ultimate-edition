"""GT looks keep their clothes when they transform (Nov 15, the owner: "make sure his fucking outfit stays the same when he
transforms, and Gohan glasses on and off as well don't change shit make it for both").

Black Star Odyssey's sheet has one Super Saiyan figure for each pair of looks, so the second look borrowed it:
- GT Goten's green jacket went white in Super Saiyan (goten_gt_ssj's figure). goten_gt_green_ssj is that figure with the jacket
  recoloured the way the green look recolours the white one: a pixel the white look has at the same place in the same frame takes the
  green look's colour there; any other jacket pixel takes the green look's usual colour for it (MAP). Hair, face, trousers and effects
  stay. His dance (slot 21) is kid Goten's Super Saiyan dance in the green colours (gt_dance).
- GT Gohan's glasses came off in Super Saiyan and 2 (gohan_gt_ssj's figure, drawn without them), and the look without glasses put them
  back on when he powered down (that figure's power-down ends on the glasses look's stance). Now gohan_gt_ssj (the glasses look's
  Super Saiyan and 2) wears them in every frame his eyes show, and so do the Super Saiyan frames inside the glasses look's own change;
  gohan_gt_ng_ssj (the look without glasses, Super Saiyan and 2) is the old figure with that look's own power-down (slot 11: his hair
  gold, then brown, then black, no glasses).

The glasses are drawn round his Super Saiyan eyes (teal) as the glasses look's frames draw them (glasses()): from the front the rims,
bridge, top and bottom bars and the arms at the face's edge; from the side the rim in front of the eye and the arm behind it. A frame
whose eyes are shut (blinking, hurt) takes the place of the eyes from the frame of the same view whose head matches it best.
The new figures are built after every other actor (build.py add_actors), so no actor id moves."""
import numpy as np
from scipy import ndimage

# --- GT Goten's green jacket --------------------------------------------------------------------------------------------------------
JACKET = (89, 116, 118, 119, 120)
MAP = {116: 187, 118: 187, 119: 252, 120: 253, 89: 249}       # white look -> green look, the colour each index takes most often


def green_frame(c, w=None, g=None):
    """A frame of the white look's Super Saiyan with the green jacket; w, g: the white and green looks' frames at the same place."""
    c = np.asarray(c); out = c.copy()
    lab, n = ndimage.label(np.isin(c, JACKET))
    same = w is not None and g is not None and np.shape(w) == c.shape and np.shape(g) == c.shape
    if same: w, g = np.asarray(w), np.asarray(g)
    for k in range(1, n + 1):
        m = lab == k
        if not np.isin(c[m], (89, 116, 118, 119)).any(): continue      # all white: a hair highlight or a streak, left alone
        for y, x in zip(*np.nonzero(m)):
            v = c[y, x]
            out[y, x] = g[y, x] if same and w[y, x] == v else MAP[v]
    return out


def green_ssj(ssj, white, green):
    """raw_frames {slot: [views]} of goten_gt_ssj -> the green look's; white, green: goten_gt's and goten_gt_green's raw_frames."""
    out = {}
    for s, views in ssj.items():
        out[s] = []
        for v, frames in enumerate(views):
            wv = white.get(s, [[], [], []])[v] if s in white else []
            gv = green.get(s, [[], [], []])[v] if s in green else []
            out[s].append([green_frame(f, wv[i] if i < len(wv) else None, gv[i] if i < len(gv) else None) for i, f in enumerate(frames)])
    return out


# --- GT Gohan's glasses -------------------------------------------------------------------------------------------------------------
RED = (31, 32, 33, 34)
TEAL = (215, 216)                   # his Super Saiyan eyes
WHITE = (117, 120)                  # the eyes' whites
FACE = (1, 16, 200, 201, 202, 203)  # skin, its shading, the outline
D, L = 32, 33                       # the glasses' red, dark and light (the glasses look's own)


def eyes(c):
    """[(top row, bottom row, column)] of each teal eye stripe, left to right."""
    lab, n = ndimage.label(np.isin(c, TEAL), np.ones((3, 3), bool))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if xs.max() == xs.min(): out.append((int(ys.min()), int(ys.max()), int(xs.min())))
    return sorted(out, key=lambda e: e[2])


def _eye_mask(c, E):
    eye = np.zeros(c.shape, bool)
    for y0, y1, x in E:
        if 0 <= x < c.shape[1]: eye[max(y0, 0):y1 + 1, x] = True
        for dx in (-1, 1):
            for y in range(y0 - 1, y1 + 1):
                if 0 <= y < c.shape[0] and 0 <= x + dx < c.shape[1] and c[y, x + dx] in WHITE: eye[y, x + dx] = True
    return eye


def glasses(c, E=None):
    """(frame with the glasses, how) round eyes E (found in c when None); (c, None) when there are none."""
    c = np.asarray(c); E = eyes(c) if E is None else E
    if not E: return c, None
    out = c.copy(); eye = _eye_mask(c, E); H, W = c.shape

    def paint(y, x, v):
        if 0 <= y < H and 0 <= x < W and c[y, x] and not eye[y, x]: out[y, x] = v
    if len(E) >= 2 and E[1][2] - E[0][2] in (2, 3) and abs(E[0][0] - E[1][0]) <= 1:      # from the front: both eyes
        (a0, a1, tl), (b0, b1, tr) = E[0], E[1]
        et, eb = min(a0, b0), max(a1, b1)
        if eb - et + 1 < 3 and et > 0 and c[et - 1, tl - 1] in WHITE: et -= 1               # an eye's white top over a short stripe
        for i, x in enumerate(range(tl - 4, tl + 1)): paint(et - 1, x, (L, D, D, L, L)[i])         # top bars
        for i, x in enumerate(range(tr, tr + 5)): paint(et - 1, x, (L, L, D, D, L)[i])
        for y in range(et, eb + 1):                                                               # rims and bridge
            for x in sorted({tl - 3, tl + 1, tr - 1, tr + 3}): paint(y, x, L if y == et else D)
        for x in (tl - 5, tr + 5):                                                                # the arms, at the face's edge
            if 0 <= et < H and 0 <= x < W and c[et, x] in FACE: paint(et, x, D)
        for i, x in enumerate(range(tl - 3, tl + 1)): paint(eb + 1, x, (D, D, D, L)[i])          # bottom bars
        for i, x in enumerate(range(tr, tr + 4)): paint(eb + 1, x, (L, D, D, D)[i])
        return out, 'front'
    y0, y1, x = max(E, key=lambda e: e[1] - e[0])                                                 # one eye: from the side
    behind = 1 if any(0 <= x + 1 < W and c[y, x + 1] in WHITE for y in range(max(y0 - 1, 0), y1 + 1)) else -1
    et = y0 - 1
    for y in range(et - 1, y1 + 1): paint(y, x - behind, L)                                        # the rim in front of the eye
    for k in (2, 3): paint(et, x + behind * k, D)                                                 # the arm behind it
    return out, 'side'


def _head_match(a, b, E):
    """(score, dy, dx): frame a against frame b's head (its rows down to just under b's eyes E), eyes left out."""
    ys, xs = np.nonzero(b)
    if not len(ys): return 0, 0, 0
    top, bot = ys.min(), max(e[1] for e in E) + 3
    x0, x1 = min(e[2] for e in E) - 7, max(e[2] for e in E) + 8
    region = np.zeros(b.shape, bool); region[top:bot + 1, max(x0, 0):x1] = True
    region &= ~_eye_mask(b, E)
    best = (0, 0, 0)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            ys_, xs_ = np.nonzero(region); y2, x2 = ys_ + dy, xs_ + dx
            ok = (y2 >= 0) & (y2 < a.shape[0]) & (x2 >= 0) & (x2 < a.shape[1])
            if ok.sum() < len(ys_): continue
            av, bv = a[y2, x2], b[ys_, xs_]; use = (av > 0) | (bv > 0)
            if use.sum() < 20: continue
            sc = (av[use] == bv[use]).mean() - 0.003 * (abs(dy) + abs(dx))
            if sc > best[0]: best = (sc, dy, dx)
    return best


def glasses_frames(raw, look=None, views=(0, 2)):
    """raw_frames {slot: [views]} with the glasses on every Super Saiyan frame whose eyes show (or match a frame whose eyes show, or
    whose frame in the glasses look (look: its raw_frames) has them at the same place). Frames that already have them (the glasses
    look's own stance in a power-down) and the back view stay as they are."""
    out = {s: [list(v) for v in vs] for s, vs in raw.items()}
    seen = {v: [] for v in views}; shut = []
    for s, vs in raw.items():
        for v, frames in enumerate(vs):
            for i, f in enumerate(frames):
                f = np.asarray(f)
                if np.isin(f, RED).sum() > 10: continue
                E = eyes(f)
                if E:
                    out[s][v][i], how = glasses(f, E)
                    if v in seen: seen[v].append((f, E))
                elif v in views and np.isin(f, (28, 248, 249)).any(): shut.append((s, v, i, f))
    made = sum(1 for s, vs in raw.items() for v, fr in enumerate(vs) for i, f in enumerate(fr) if out[s][v][i] is not f and (np.asarray(out[s][v][i]) != np.asarray(f)).any())
    matched = []
    for s, v, i, f in shut:                     # eyes shut: the eyes' place from the best-matching head of the same view
        best = None
        for b, E in seen[v]:
            if b.shape != f.shape: continue
            sc, dy, dx = _head_match(f, b, E)
            if best is None or sc > best[0]: best = (sc, dy, dx, E)
        if best and best[0] >= 0.8:
            sc, dy, dx, E = best
            out[s][v][i], _ = glasses(f, [(y0 + dy, y1 + dy, x + dx) for y0, y1, x in E])
            matched.append((s, v, i, round(float(sc), 2)))
            continue
        g = look.get(s, [[], [], []])[v] if look else []
        if i < len(g) and np.shape(g[i]) == f.shape:      # the glasses look's frame at the same place: its glasses where his face is
            g = np.asarray(g[i]); m = np.isin(g, RED) & np.isin(f, FACE)
            body = (f > 0) & (g > 0) & ~np.isin(f, (28, 120, 246, 247, 248, 249)) & ~np.isin(g, (1,) + RED)
            if m.sum() >= 3 and body.sum() and (f[body] == g[body]).mean() >= 0.8:
                o = f.copy(); o[m] = g[m]; out[s][v][i] = o; matched.append((s, v, i, 'look'))
    return out, made, matched


def no_glasses_ssj(ssj, plain_look):
    """gohan_gt_ng_ssj: gohan_gt_ssj's raw_frames (no glasses) with the power-down (slot 11) of the look without glasses, which fades
    his hair from gold through brown to black with no glasses (the old figure's ended on the glasses look's stance)."""
    out = {s: [list(v) for v in vs] for s, vs in ssj.items()}
    pd = plain_look.get('11')
    if not pd or any(np.isin(np.asarray(f), RED).sum() > 10 for v in pd for f in v): raise ValueError('gohan_gt_noglasses: no power-down without glasses')
    out['11'] = [list(v) for v in pd]
    return out
