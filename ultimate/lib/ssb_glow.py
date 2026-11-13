"""Super Saiyan Blue's glow (outfit.c glow_tick; Nov 12, the owner: "a subtle blue aura post transformation too to go with the lightning",
then "Thin is a good start but can you make it look more flame like or another effect not just the same aura outline"): drawn here, not
taken from the game's aura. N frames of 32x64 (an OBJ 32x64, 8 bpp), the fighter's feet on row FEET, drawn behind him. Values: 1-3 the
flame's rim (outer to inner), 4-6 a spark's streak (white head, light blue, blue); COLOURS gives their colours (build.py finds the
nearest the palette has)."""
import numpy as np
from scipy import ndimage
W, H, N = 32, 64, 8
FEET = 62           # the figure's lowest row in the box (mock.py: the figure spans rows 31-62)
CX = 15.5
COLOURS = {1: (48, 176, 232), 2: (96, 232, 248), 3: (208, 248, 248), 4: (248, 248, 248), 5: (160, 248, 248), 6: (64, 200, 248), 11: (24, 96, 216), 12: (232, 248, 248), 13: (120, 216, 248), 14: (96, 232, 248)}

def noise(seed, cells_x, cells_y, scale_x, scale_y):
    """tileable (in y) smooth value noise sampler: f(x, y) -> 0..1"""
    r = np.random.RandomState(seed).rand(cells_y, cells_x + 1)
    def f(x, y):
        gx = x / scale_x; gy = (y / scale_y) % cells_y
        x0 = np.floor(gx).astype(int); y0 = np.floor(gy).astype(int)
        fx = gx - x0; fy = gy - y0
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
        x0 = np.clip(x0, 0, cells_x - 1); y1 = (y0 + 1) % cells_y
        a = r[y0, x0] * (1 - fx) + r[y0, x0 + 1] * fx
        b = r[y1, x0] * (1 - fx) + r[y1, x0 + 1] * fx
        return a * (1 - fy) + b * fy
    return f

def halfwidth(y, top):
    """the flame's half width by row: feet a little narrow, widest at the waist, then up into a point at `top`"""
    t = (FEET + 2 - y)                  # height above the feet
    hw = np.interp(t, [-3, 0, 6, 16, 24, 30, FEET + 2 - top], [5, 9.5, 12.5, 13, 11.5, 8, 0])
    return np.where(y < top, 0, hw)

TONGUES = ((-6, 22, 0.0, 3.2), (0, 14, 2.1, 3.6), (6, 20, 4.2, 3.2))      # x from the middle, tip row, phase, base half width

LICKS = ((-1, 0.0), (1, 0.33), (-1, 0.62), (1, 0.85))     # side, phase: flames running up the sides

def flame(seed=3, top=16, wobble=5.0, thick=2, tongues=TONGUES, sway=1.6, flick=3.0, licks=LICKS):
    """N frames of a flame's rim (1 = outer pixel, 2 and 3 further in): the body's envelope, open at the feet, and tongues rising over the
    head that sway and stretch, the edges broken by noise scrolling up (seamless over the N frames)"""
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    period = 64.0
    n1 = noise(seed, 6, 8, 6.0, period / 8); n2 = noise(seed + 1, 12, 16, 3.0, period / 16)
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    out = []
    for t in range(N):
        ph = 2 * np.pi * t / N
        s = t * period / N
        nz = 0.65 * n1(xx, yy + s) + 0.35 * n2(xx, yy + s) - 0.5
        hgt = FEET + 1 - yy                                     # rows above the feet
        hw = np.interp(hgt, [-4, 0, 8, 16, 24, 30, 34, 36], [6, 7.5, 11.5, 12.5, 11, 7.5, 3, 0])
        F = 1 - np.abs(xx - CX) / np.maximum(hw, 0.01); F[hw <= 0] = -1
        base = FEET - 26
        for bx, tip, phase, wb in tongues:
            tp = tip + flick * np.sin(2 * ph + phase)           # the tip stretches and drops
            u = np.clip((yy - tp) / (base - tp), 0, 1)          # 0 at the tip, 1 at its base
            cx = CX + bx * (0.6 + 0.4 * u) + sway * np.sin(ph + phase + (base - yy) * 0.22) * (1 - u)
            w = wb * u ** 0.75
            Ft = 1 - np.abs(xx - cx) / np.maximum(w, 0.01); Ft[(yy < tp) | (yy > base + 4)] = -1
            F = np.maximum(F, Ft)
        for side, phase in licks:
            p = (t / N + phase) % 1.0
            yc = FEET - 6 - p * 26
            hwc = float(np.interp(FEET + 1 - yc, [-4, 0, 8, 16, 24, 30, 34, 36], [6, 7.5, 11.5, 12.5, 11, 7.5, 3, 0]))
            xe = CX + side * (hwc + 0.5 - 1.5 * p)
            ry = 3.0 + 2.0 * p; rx = 2.2 - 0.8 * p
            dy = (yy - yc) / ry; dy = np.where(dy < 0, dy * 0.6, dy * 1.4)        # pointed up, round below
            Fl = 1 - np.sqrt(((xx - xe) / rx) ** 2 + dy ** 2)
            F = np.maximum(F, Fl)
        up = np.clip((FEET - yy) / (FEET - top), 0, 1)
        F = F + nz * (0.3 + 0.12 * wobble * up)
        inside = F > 0
        lab, k = ndimage.label(inside)
        if k > 1:
            sizes = ndimage.sum(inside, lab, range(1, k + 1))
            inside = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if v >= 4])
        pad = np.vstack([inside, np.ones((3, W), bool)])        # open at the feet: no edge along the bottom
        e1 = ndimage.binary_erosion(pad, cross, border_value=0)[:H]
        e2 = ndimage.binary_erosion(np.vstack([e1, np.ones((3, W), bool)]), cross, border_value=0)[:H]
        img = np.zeros((H, W), np.uint8)
        img[inside & ~e1] = 1
        if thick >= 2: img[inside & e1 & ~e2] = 2
        if thick >= 3: img[inside & e2 & ~ndimage.binary_erosion(np.vstack([e2, np.ones((3, W), bool)]), cross, border_value=0)[:H]] = 3
        img[:, 0] = img[:, 0] * 0                               # (the box's edges stay clear)
        out.append(img)
    return out

def embers(seed=7, count=9, lo=FEET - 2, hi=6, spread=13):
    """N frames of sparks rising round the fighter: each a streak 4 px long (a white head, then lighter and darker blue), rising and
    drifting, fading to its two blue pixels near the top, gone past it."""
    rs = np.random.RandomState(seed)
    out = [np.zeros((H, W), np.uint8) for _ in range(N)]
    span = lo - hi
    for k in range(count):
        side = -1 if k % 2 else 1
        x0 = CX + side * rs.uniform(5, spread)
        phase = rs.uniform(0, 1); drift = rs.uniform(-1.5, 1.5)
        for t in range(N):
            p = (phase + t / N) % 1.0
            y = lo - p * span
            x = int(round(x0 + drift * p + 0.8 * np.sin(6.28 * (p * 2 + phase))))
            yi = int(round(y))
            if not (0 <= x < W): continue
            trail = (4, 5, 6, 6) if p < 0.7 else (5, 6, 6, 0)        # 4 white, 5 light blue, 6 blue
            for dy, vv in enumerate(trail):
                if vv and 0 <= yi + dy < H and out[t][yi + dy, x] == 0: out[t][yi + dy, x] = vv
    return out

def wisps(seed=5):
    """the flame's tongues only (its rim above the shoulders), no ring round the body"""
    fr = flame(seed, top=10, wobble=7.0, thick=2)
    rows = np.arange(H)[:, None]
    return [np.where(rows < FEET - 20, f, 0).astype(np.uint8) for f in fr]

def merge(a, b):
    return [np.where(x > 0, x, y).astype(np.uint8) for x, y in zip(a, b)]


# "more majestic/godlike" (the owner, Nov 12, 18:56): taller, calmer, coloured by height (deep blue at his feet to white at the tips)
TALL = ((-7, 18, 0.0, 3.4), (0, 4, 2.1, 4.2), (7, 16, 4.2, 3.4), (-3, 10, 1.0, 2.6), (3, 9, 3.1, 2.6))
def graded(frames, low=(11, 1), mid=(1, 2), high=(12, 3)):
    """recolour a rim by height: values 1 (outer) and 2 (inner) become low/mid/high pairs (rows from the feet: up to 18, to 34, above)"""
    out = []
    for f in frames:
        g = f.copy(); rows = np.arange(H)[:, None] + np.zeros((1, W), int)
        for (lo, hi), pair in (((FEET - 18, H), low), ((FEET - 34, FEET - 18), mid), ((0, FEET - 34), high)):
            band = (rows >= lo) & (rows < hi)
            g[band & (f == 1)] = pair[0]; g[band & (f == 2)] = pair[1]
        out.append(g)
    return out
def majestic(seed=3, wobble=3.5, sway=1.1, flick=2.0):
    return flame(seed, top=4, wobble=wobble, thick=2, tongues=TALL, sway=sway, flick=flick)
def inner_ring(frames, gap=3):
    """a second, faint line inside the first (dotted), gap pixels in"""
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    out = []
    for t, f in enumerate(frames):
        inside = f > 0
        filled = ndimage.binary_fill_holes(np.vstack([inside, np.ones((3, W), bool)]))[:H]
        e = filled
        for _ in range(gap): e = ndimage.binary_erosion(np.vstack([e, np.ones((3, W), bool)]), cross, border_value=0)[:H]
        ring = e & ~ndimage.binary_erosion(np.vstack([e, np.ones((3, W), bool)]), cross, border_value=0)[:H]
        yy, xx = np.mgrid[0:H, 0:W]
        g = f.copy(); g[ring & ((yy + xx + t) % 2 == 0) & (g == 0)] = 13
        out.append(g)
    return out
def glints(seed=5, count=5):
    """little four-point stars of light that open and close in place round him (not rising): a god's glint"""
    rs = np.random.RandomState(seed)
    out = [np.zeros((H, W), np.uint8) for _ in range(N)]
    for k in range(count):
        x = int(rs.uniform(3, W - 4)); y = int(rs.uniform(8, FEET - 6)); ph = rs.randint(N)
        if abs(x - CX) < 7 and y > FEET - 34: x = int(CX + (9 if x > CX else -9))
        for t in range(N):
            s = (t - ph) % N
            if s == 0: pts = [(0, 0, 4)]
            elif s == 1: pts = [(0, 0, 4), (-1, 0, 5), (1, 0, 5), (0, -1, 5), (0, 1, 5)]
            elif s == 2: pts = [(0, 0, 5), (-1, 0, 6), (1, 0, 6), (0, -1, 6), (0, 1, 6)]
            else: pts = []
            for dx, dy, v in pts:
                if 0 <= y + dy < H and 0 <= x + dx < W: out[t][y + dy, x + dx] = v
    return out


def depth_inside(f, n=6):
    """for one rim frame: depth[y, x] = 1..n for pixels that far inside the rim (0 elsewhere), the flame open at his feet"""
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    rim = f > 0
    pad = lambda m: np.vstack([m, np.ones((3, W), bool)])
    filled = ndimage.binary_fill_holes(pad(rim))[:H]
    inside = filled & ~rim
    depth = np.zeros((H, W), np.uint8); cur = inside
    for k in range(1, n + 1):
        nxt = ndimage.binary_erosion(pad(cur), cross, border_value=0)[:H]
        depth[cur & ~nxt] = k; cur = nxt
        if not cur.any(): break
    depth[cur] = n
    return depth


def inner_glow(frames, pattern):
    """style 1 with a soft inner aura: pattern(depth, t, yy, xx) -> value to draw (0 none) for the pixels inside the rim"""
    yy, xx = np.mgrid[0:H, 0:W]
    out = []
    for t, f in enumerate(frames):
        d = depth_inside(f)
        g = f.copy(); add = pattern(d, t, yy, xx)
        g[(g == 0) & (add > 0)] = add[(g == 0) & (add > 0)]
        out.append(g)
    return out


def dotted(frames):
    """every other pixel, in a checkerboard that swaps each frame: it reads as see-through without the GBA's blending"""
    yy, xx = np.mgrid[0:H, 0:W]
    return [np.where((yy + xx + t) % 2 == 0, f, 0).astype(np.uint8) for t, f in enumerate(frames)]


def outer(frames):
    """the flame's outer pixel only"""
    return [np.where(f == 1, 1, 0).astype(np.uint8) for f in frames]


STYLES = {'flame': lambda: flame(3, thick=2), 'sparks': lambda: embers(11, 10), 'flame_sparks': lambda: merge(flame(3, thick=2), embers(7, 8)),
          'flame_dotted': lambda: dotted(flame(3, thick=2)), 'flame_outer': lambda: outer(flame(3, thick=2)),
          'm1': lambda: graded(majestic()), 'm2': lambda: inner_ring(graded(majestic())), 'm3': lambda: merge(graded(majestic()), glints()),
          'm4': lambda: merge(inner_ring(graded(majestic())), glints())}
STEP = {'m1': 7, 'm2': 7, 'm3': 7, 'm4': 7}          # game frames per glow frame (outfit.c GLOW_STEP); 4 otherwise
# 1c (the owner's pick, Nov 12, 19:04: "1c looks good use that"): the flame, and inside it a see-through band of light three pixels deep,
# drawn as a second sprite the GBA blends over what is behind him (outfit.c GLOW_BAND: 6/16 of the band over 10/16 of the stage)
STYLES['1c'] = STYLES['flame']
BANDS = {'1c': lambda: inner_glow([np.zeros((H, W), np.uint8)] * 0 + flame(3, thick=2), lambda d, t, yy, xx: np.where((d >= 1) & (d <= 3), 14, 0))}


# From the power-up into the glow (Nov 12, 20:29, the owner on the glow fading in: "Looks choppy is there any way to add a few more frames
# that actually match the vanilla aura shape and then blend into the new one after that one ends better so its more smooth"): the
# power-up's own aura (the field aura, 32x32, three frames, in the form's tint) sits on rows BURST_ROW to BURST_ROW + 31 of the glow's box,
# in its 32 columns (measured in the game: Blue Goku's, x 104-135 and y 55-86 against the glow's 104-135 and 27-90). The transition
# plays its three frames, then TRANS_MORPH frames whose outline goes from the aura's to the flame's (the two shapes' signed distances
# mixed, a little more of the flame's each frame), drawn as the flame's rim is.
BURST_ROW = 28
TRANS_MORPH = 6


def _sdf(m):
    """signed distance to a mask's edge: positive inside"""
    return ndimage.distance_transform_edt(m) - ndimage.distance_transform_edt(~m)


def burst_shape(img):
    """the power-up aura's outline filled: every row between its leftmost and rightmost pixel (it is an oval of flames, open below)"""
    m = np.zeros(img.shape, bool)
    for y in range(img.shape[0]):
        xs = np.nonzero(img[y])[0]
        if len(xs): m[y, xs.min():xs.max() + 1] = True
    return m


def flame_shape(f):
    """a flame frame's inside: its rim and what it closes in (shut along the bottom, where the flame is open at the feet)"""
    pad = np.vstack([f > 0, np.ones((1, W), bool)])
    return ndimage.binary_fill_holes(pad)[:H]


def rim(inside, thick=2):
    """an outline of a shape as the flame draws its own: 1 the outer pixel, 2 the next in, open at the feet"""
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    pad = np.vstack([inside, np.ones((3, W), bool)])
    e1 = ndimage.binary_erosion(pad, cross, border_value=0)[:H]
    e2 = ndimage.binary_erosion(np.vstack([e1, np.ones((3, W), bool)]), cross, border_value=0)[:H]
    img = np.zeros((H, W), np.uint8)
    img[inside & ~e1] = 1
    if thick >= 2: img[inside & e1 & ~e2] = 2
    img[:, 0] = 0
    return img


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])


def transition(burst, lut, flames, morph=TRANS_MORPH):
    """The frames from the power-up's aura into the glow: `burst` its three frames (32x32 palette indices, in the form's tint), `lut` the
    glow's values -> palette indices, `flames` the glow's frames (values). -> 3 + morph frames of 32x64 palette indices: the aura's own
    three, then the aura (its frames in turn) stretched up towards the flame's height and narrowed towards its width, dissolving into the
    flame (an ordered dither: a little more of the flame's pixels and less of the aura's each frame)."""
    out = []
    for b in burst:
        f = np.zeros((H, W), np.uint8); f[BURST_ROW:BURST_ROW + 32, :32] = b[:32, :32]; out.append(f)
    yy, xx = np.mgrid[0:H, 0:W]
    lut = np.asarray(lut, np.uint8)
    bottom = BURST_ROW + 31
    for i in range(1, morph + 1):
        a = i / (morph + 1.0)
        b = burst[(i - 1) % len(burst)][:32, :32]
        sy, sx = 1 + 0.5 * a, 1 - 0.12 * a                 # taller (from its bottom row), narrower (about the middle)
        src_y = np.round(bottom - (bottom - yy) / sy).astype(int) - BURST_ROW
        src_x = np.round(CX + (xx - CX) / sx).astype(int)
        ok = (src_y >= 0) & (src_y < 32) & (src_x >= 0) & (src_x < 32)
        warped = np.zeros((H, W), np.uint8)
        warped[ok] = b[src_y[ok], src_x[ok]]
        fl = lut[flames[(i - 1) % len(flames)]]
        mine = BAYER[yy % 4, xx % 4] < a * 16          # the flame's share of the pixels
        f = np.where(mine, fl, warped).astype(np.uint8)
        f[:, 0] = 0
        out.append(f)
    return out


FADE_OUT = 6


def fadeout(lut, flames, n=FADE_OUT):
    """Full Power Mystic's glow going (the owner, Nov 12 20:51: "make that aura fade out after like 3 more seconds but have the lightning
    remain ... ONLY for him"): the flame (its frames in turn) dissolving away, an ordered dither, a little less of it each frame. -> n
    frames of 32x64 palette indices."""
    yy, xx = np.mgrid[0:H, 0:W]
    lut = np.asarray(lut, np.uint8)
    return [np.where(BAYER[yy % 4, xx % 4] >= (i + 1) / (n + 1.0) * 16, lut[flames[i % len(flames)]], 0).astype(np.uint8) for i in range(n)]


def band_only(frames):
    """the band's pixels alone (value 14), the rim taken out"""
    return [np.where(f == 14, 14, 0).astype(np.uint8) for f in frames]


def tiles4(img, nib):
    """a 32x64 picture of 0 and anything else as a 4 bpp OBJ's tiles (1D order), the drawn pixels colour `nib` of its palette bank"""
    m = (img > 0).astype(np.uint8) * nib
    out = bytearray()
    for ty in range(H // 8):
        for tx in range(W // 8):
            t = m[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            out += bytes(int(t[y, x]) | int(t[y, x + 1]) << 4 for y in range(8) for x in range(0, 8, 2))
    return bytes(out)


def tiles(img):
    """a 32x64 picture as an 8 bpp OBJ's tiles, in 1D order (four across, eight down)"""
    return b''.join(img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].tobytes() for ty in range(H // 8) for tx in range(W // 8))
