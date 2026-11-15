"""Future Trunks at adult height (Nov 15; the owner, on LoG2's Future Trunks drawn at kid Trunks's size and with his head: "Future
Trunks on kid Trunks"; on the preview of a taller one: "Yes"). Every frame of his that stands on its feet gets two more rows in his
legs: two rows of the 12 above his soles are drawn twice, so everything above them sits two rows higher in every such frame alike
(no frame of an animation moves his head by itself). The rows doubled are the ones most like the row under them and narrowest (a
leg straight down, not a kick across), so no shape grows thicker. Frames under MIN_HEIGHT rows (flying, lying down) stay as drawn.
A frame that grows past 32 rows goes into a 32x64 piece: his actors reserve 2 KB of sprite memory a frame (as Android 17's)."""
import numpy as np

LEGS = 12           # rows above the soles where rows may be doubled
SOLES = 2           # the bottom rows (shoes) never doubled
MIN_HEIGHT = 22


def rows_to_double(c, bot, extra):
    """The `extra` rows (in c) of the legs to draw twice: most like the row below, then narrowest; never two side by side."""
    cands = []
    for r in range(max(bot - SOLES - LEGS + 1, 0), bot - SOLES + 1):
        a, b = c[r], c[r + 1]
        on = (a > 0) | (b > 0)
        if not on.any(): continue
        same = ((a == b) & on).sum() / on.sum()
        cands.append((-same, int((a > 0).sum()), -r, r))
    cands.sort()
    out = []
    for _, _, _, r in cands:
        if all(abs(r - q) > 1 for q in out): out.append(r)
        if len(out) == extra: break
    return sorted(out)


def stretched_rows(img, extra=2):
    """(rows of the stretched figure, top row, bottom row) or None for a frame left as drawn."""
    ys = np.nonzero(img.any(1))[0]
    if not len(ys) or ys[-1] - ys[0] + 1 < MIN_HEIGHT: return None
    top, bot = ys[0], ys[-1]
    dup = rows_to_double(img, bot, extra)
    if len(dup) < extra: return None
    rows = []
    for r in range(top, bot + 1):
        rows.append(img[r])
        if r in dup: rows.append(img[r])
    return np.array(rows), top, bot


def stretch_piece(img, fbox, extra=2):
    """A frame (h x w colour indices, 0 clear) placed at fbox (x, y, w, h) from the anchor: (frame, box), stretched, his feet on the
    same row as before. The piece stays its size when the taller figure fits, else becomes 32 or 64 rows (32 wide)."""
    x, y, w, h = fbox
    got = stretched_rows(img, extra)
    if got is None: return img, fbox
    body, top, bot = got
    hc = body.shape[0]
    H = h if hc <= h else 32 if hc <= 32 else 64
    W = w if H == h or (w <= 32 and H == 32 and (w, H) in ((8, 32), (16, 32), (32, 32))) else 32
    if w > W: return img, fbox                       # (no 64-row piece wider than 32: left as drawn)
    below = min(h - 1 - bot, H - hc)                 # clear rows kept under his feet
    out = np.zeros((H, W), img.dtype)
    ox = (W - w) // 2
    out[H - below - hc:H - below, ox:ox + w] = body
    feet = y + bot                                   # his feet's row from the anchor, as before
    return out, (x - ox, feet - (H - 1 - below), W, H)
