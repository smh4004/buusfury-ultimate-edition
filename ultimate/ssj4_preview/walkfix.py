"""Super Saiyan 4 Goku's walk and run, read the way Super Saiyan 4 Gogeta's were (Nov 11-12): each frame against BF Goku's frame under
it. Leftovers of the touch-up, found while reading Gogeta's (the owner, 21:38 of Gogeta: "Some weird clipping ... head and neck on side
and back views especially on walk frames mainly"; 22:25: "The back ones still doing it it's by a pixel or two moving slightly to the
side"; then, 00:06, of this one: "Send it what are you waiting for"):
- BF's undershirt sleeve left blue on his shoulder and the arm under it bare skin, where his standing frames have fur: from the side in
  every walk frame and in the run (the arm swinging back), from the front and from behind in the walk and the run;
- from behind, his head one column left in the first walk frame (BF Goku's own head does it there), so it steps sideways.
Fixed to his own standing frames: fur from the shoulder to the wristband, the wristband blue, the hand skin.
Then, 00:24, of that first preview: "Back view is fucked run frames are fucked"; a tail from behind tried next (Vegeta's curl) and taken
out again (00:49: "You made the tail worse and also I meant his back itself but now both are broken wtf"): the sheet's tail stays.
Asked (00:5x): "Back shape warped and morphed with tail", from behind; where the tail sits: no preference. From behind the sheet's tail
grows out of his crotch four pixels wide and runs down his left leg to the floor (in the run past it, in the air), so his lower body
and the tail are one warped shape. tail(): the tail off, BF Goku's leg under it back in his own leg colours (BF's navy boots his dark
ones, laces and hem in them grey; BF's orange trousers his yellow ones), skin and blue the sheet left on his trousers off, and a tail
of his own reds hanging from the base of his spine (the middle of his sash's bottom row) straight down between his legs to his knees,
two pixels wide, lit on its left. Frames that show his back only (no face). And the head step of the first walk frame from behind is
taken out by moving the whole frame a column (not his head alone, which bent his back at the seam).

Each entry is a list for one frame (slot, frame, view), applied in order to his frame on lib4.Rom.frame's canvas:
  ('fur', (row0, row1, col0, col1)): his skin and blue in the box become fur: his standing frame's fur shade at that pixel when it
  has fur there (so a hanging arm shades as it does when he stands), else the touch-up's own shade maps;
  ('blue', box): his fur where BF has his navy wristband becomes the wristband's blue;
  ('shift', row0, row1, columns): those rows move sideways.
A preview: he is locked (the owner, 21:01: "Lock that Goku for now"; 18:13: "Don't make changes to SSJ4 Goku without verifying first")."""
import numpy as np

SKIN_FUR = {16: 31, 17: 31, 202: 32, 203: 32, 201: 33, 200: 105}          # armhand.TO_FUR
BLUE_FUR = {69: 31, 158: 32, 160: 33}                                     # armhand.BLUE_FUR
BF_BAND = {157: 69, 159: 158, 161: 160}                                   # gt.BF_BAND
FURS = (31, 32, 33, 104, 105)

FIXES = {
    # from the side: the walk
    (1, 0, 2): [('fur', (57, 58, 52, 52)), ('fur', (58, 58, 51, 51)), ('fur', (59, 59, 52, 52)),            # the arm swinging forward
                ('fur', (57, 57, 59, 61)), ('fur', (58, 58, 58, 61)), ('fur', (59, 60, 59, 62)), ('fur', (61, 61, 59, 60))],   # and back
    (1, 1, 2): [('fur', (57, 57, 55, 60)), ('fur', (58, 60, 56, 59))],
    (1, 2, 2): [('fur', (56, 57, 59, 61)), ('fur', (58, 58, 60, 61)), ('fur', (59, 59, 60, 60))],
    # from the side: the run (the arm that swings back)
    (2, 0, 2): [('fur', (57, 57, 60, 62))],
    (2, 1, 2): [('fur', (55, 55, 58, 62)), ('fur', (56, 56, 58, 60))],
    (2, 2, 2): [('fur', (57, 57, 60, 63)), ('fur', (58, 58, 61, 62))],
    (2, 3, 2): [('fur', (55, 55, 56, 60)), ('fur', (56, 56, 56, 60)), ('fur', (57, 57, 57, 60))],
    # from the front: the walk
    (1, 0, 0): [('fur', (58, 58, 51, 52)), ('fur', (59, 59, 50, 53)), ('fur', (60, 60, 50, 54)), ('fur', (61, 61, 50, 51)),
                ('fur', (57, 57, 61, 62)), ('fur', (58, 58, 61, 62)), ('fur', (59, 59, 61, 63)), ('fur', (60, 60, 60, 63)), ('fur', (61, 61, 61, 62))],
    (1, 2, 0): [('fur', (58, 58, 60, 61)), ('fur', (59, 59, 59, 62)), ('fur', (60, 60, 58, 62)), ('fur', (61, 61, 61, 62)),
                ('fur', (60, 60, 48, 49)), ('fur', (61, 61, 49, 50))],
    # from the front: the run
    (2, 0, 0): [('fur', (59, 59, 51, 52)), ('fur', (60, 61, 50, 52)), ('fur', (62, 62, 50, 51)), ('fur', (63, 63, 51, 51)), ('fur', (60, 61, 60, 63))],
    (2, 1, 0): [('fur', (56, 56, 49, 49)), ('fur', (57, 57, 49, 50)), ('fur', (58, 58, 49, 51)), ('fur', (59, 59, 51, 52)),
                ('fur', (56, 56, 63, 63)), ('fur', (57, 57, 62, 63)), ('fur', (58, 58, 62, 63)), ('fur', (59, 59, 60, 61))],
    (2, 2, 0): [('fur', (59, 59, 60, 61)), ('fur', (60, 61, 60, 62)), ('fur', (62, 62, 61, 62)), ('fur', (63, 63, 61, 61)), ('fur', (60, 61, 49, 52))],
    # from behind: the walk
    (1, 0, 1): [('fur', (57, 57, 50, 52)), ('fur', (58, 58, 52, 52)), ('fur', (57, 58, 62, 63)), ('fur', (59, 59, 63, 63)), ('shift', 0, 95, 1)],
    (1, 2, 1): [('fur', (56, 56, 59, 60)), ('fur', (57, 57, 58, 61)), ('fur', (58, 59, 58, 61)), ('fur', (56, 60, 47, 48))],
    # from behind: the run
    (2, 0, 1): [('fur', (57, 59, 51, 53)), ('blue', (60, 61, 49, 52)), ('fur', (57, 58, 61, 62))],
    (2, 1, 1): [('fur', (55, 55, 48, 48)), ('fur', (56, 57, 60, 62)), ('fur', (58, 58, 59, 62)), ('blue', (59, 59, 49, 50))],
    (2, 2, 1): [('fur', (57, 59, 57, 60)), ('fur', (56, 59, 48, 49))],
}
FIXES[1, 3, 2] = FIXES[1, 1, 2]; FIXES[1, 3, 0] = FIXES.get((1, 1, 0), []); FIXES[2, 3, 0] = FIXES[2, 1, 0]; FIXES[2, 3, 1] = FIXES[2, 1, 1]
NAVY = (157, 159, 161); ORANGE = (63, 64, 65, 79); SKINS = (200, 201, 202, 203, 16, 17)
BOOT = {157: 1, 159: 111, 161: 111, 80: 116, 81: 118, 206: 206, 16: 16, 1: 1}
TROUSER = {63: 25, 64: 26, 65: 27, 79: 24}
TAIL = ((0, (104, 31)), (1, (104, 31)), (2, (32, 31)), (3, (104, 31)), (4, (32, 31)), (5, (104, 31)), (6, (31,)))   # rows from its root


def tail_mask(c, top=62):
    """from behind: the sheet's tail, the fur below his hands' top row that reaches row 67 or lower"""
    from scipy import ndimage
    fur = np.isin(c, FURS); fur[:top] = False
    lab, n = ndimage.label(fur, np.ones((3, 3))); t = np.zeros_like(fur)
    for i in range(1, n + 1):
        m = lab == i
        if np.nonzero(m)[0].max() >= 67: t |= m
    return t


def from_behind(c):
    """a frame that shows his back (BF draws some poses facing the camera in every view: the power-up, the change, the victory): no
    face, so no skin and no gold eyes in his head's rows"""
    ys = np.nonzero(c.any(1))[0]
    if not len(ys): return False
    head = c[ys.min():ys.min() + 16]
    return not np.isin(head, (110,)).any() and int(np.isin(head, SKINS).sum()) < 3


def leg_colour(b, y, x):
    v = int(b[y, x])
    if v in BOOT: return BOOT[v]
    if v in ORANGE:
        for yy in range(64, y + 1):
            if np.isin(b[yy, max(x - 2, 0):x + 3], NAVY).any(): return 111
        return TROUSER[v]
    return v if v in SKINS else 0


def spine(c):
    """the base of his spine from behind: under the middle of his sash's bottom row"""
    rows = [y for y in range(57, 64) if np.isin(c[y, 52:61], (69, 158, 160)).sum() >= 3]      # (his middle: the wristbands and the
    if not rows: return None                                                                  # sleeves' blue are out at his sides)
    y = rows[0]
    while y + 1 in rows: y += 1
    xs = np.nonzero(np.isin(c[y, 52:61], (69, 158, 160)))[0]
    return y + 1, 52 + int(round((xs.min() + xs.max()) / 2))


def tail(c, b):
    t = tail_mask(c)
    if not t.any() or not from_behind(c): return c
    out = c.copy()
    for y, x in np.argwhere(t): out[y, x] = leg_colour(b, y, x) if b[y, x] else 0
    for y, x in np.argwhere(np.isin(out, SKINS + (69, 158, 160))):
        if y >= 64 and int(b[y, x]) in NAVY + ORANGE: out[y, x] = leg_colour(b, y, x)
    sp = spine(out)
    if sp is None: return out
    r0, c0 = sp
    for dy, cols in TAIL:
        for dx, v in enumerate(cols): out[r0 + dy, c0 + dx] = v
    return out


def apply(c, b, entries, stand=None, view=None):
    """c: his frame; b: BF Goku's frame of the same slot, frame and view (same canvas); stand: his standing frame in that view; view 1
    (from behind): the tail too, before any 'shift'."""
    out = tail(c, b) if view == 1 else c.copy()
    for e in entries:
        if e[0] == 'shift':
            _, r0, r1, dx = e; out[r0:r1 + 1] = np.roll(out[r0:r1 + 1], dx, 1); continue
        op, (r0, r1, c0, c1) = e
        for y in range(r0, r1 + 1):
            for x in range(c0, c1 + 1):
                v = int(out[y, x])
                if op == 'fur' and (v in SKIN_FUR or v in BLUE_FUR):
                    out[y, x] = stand[y, x] if stand is not None and int(stand[y, x]) in FURS else SKIN_FUR.get(v, BLUE_FUR.get(v))
                elif op == 'blue' and int(b[y, x]) in BF_BAND and v in FURS: out[y, x] = BF_BAND[int(b[y, x])]
    return out
