"""Super Saiyan 4 Goku: heads and legs the sheet got wrong (a preview; he is locked). The owner, Nov 12 07:59: "Special 11 and 12 have
the wrong hair and the arms are still fucked, spin 2 and spin 3 dont show the front of his head properly, spin 1 side either, spind 3
front legs missing, hit 2 is base goku still".
  - the spin from the side (16, f, 2): BF Goku's own side frame is his front frame mirrored and moved 16 pixels (every pixel the
    same), so his face shows from the side too. The sheet put a back of the head there. Now: his own front frame (with its face,
    hair and arms as fixed) mirrored and moved the same.
  - the spin from the front: his legs curl over his head; the sheet painted BF's boots and trousers there in his fur's reds and
    left holes where BF's outline was (spin 3: "spin 3 front legs missing"; 08:10: "shoes shouldnt be red"). Now: his own boots' and
    trousers' colours, by the colour BF -> him his feet have in every standing frame (BF's boot blue his black and dark grey, BF's
    sole browns his greys, BF's trousers his yellows), and BF's outline black in the holes. His hair stays in front of them.
  - hit 2 from the side (9, 1, 2): the sheet left BF Goku's hair shape and painted his face in fur. Now: the head Super Saiyan 4
    Gogeta's sheet has in that frame (drawn on the same BF frame), its hair in Goku's black and greys (as his front hair, v2.G_MAP),
    its eye his gold, its eyeliner his red.
  - the special's last frame (21, 10, every view): the sheet left BF Goku's hair and his arms bare. Now: the special's frame before
    it (21, 9), which the sheet drew in full, held for the last frame (BF's two frames differ by a lean of a pixel or two)."""
import numpy as np
from scipy import ndimage

SPIN_DX = 16
LEG_MAP = {80: 116, 81: 118, 157: 1, 159: 111, 161: 111, 79: 24, 63: 25, 64: 26, 65: 27, 1: 1}   # his own boots' and trousers' colours
LEG_BF = (80, 81, 157, 159, 161, 79, 63, 64, 65)
HAIR = (1, 111, 112); G_HAIR = (62, 31, 32, 104, 33); G_MAP = {1: 1, 62: 1, 31: 111, 32: 111, 104: 112, 33: 112}
FACE = {16: 16, 17: 17, 200: 200, 201: 201, 202: 202, 77: 77, 78: 78, 2: 2, 158: 110, 175: 110, 176: 110, 127: 31, 129: 31}


def spin_side(front):
    return np.roll(front[:, ::-1], SPIN_DX, 1)


def spin_legs(c, b):
    """c: his spin frame from the front; b: BF's. BF's legs: its boot and trouser colours in the patches that reach the top rows."""
    out = c.copy(); top = np.nonzero(b.any(1))[0].min()
    leg = np.isin(b, LEG_BF); lab, n = ndimage.label(leg, np.ones((3, 3)))
    keep = np.zeros(b.shape, bool)
    for t in range(1, n + 1):
        m = lab == t
        if np.nonzero(m.any(1))[0].min() <= top + 3: keep |= m
    near = ndimage.binary_dilation(keep, np.ones((3, 3))) & (b == 1)                 # BF's outline round them
    for y, x in zip(*np.nonzero(keep | near)):
        if int(out[y, x]) in HAIR: continue                                           # his hair is in front of them
        out[y, x] = LEG_MAP[int(b[y, x])]
    return out


def gogeta_head(c, g):
    """Hit 2 from the side. c: his frame; g: Gogeta's (the same BF frame under both). Gogeta's head: his hair (rows 40-59, its reds
    and the outline on them; below row 53 only right of his shoulder) and his face (rows 47-53, columns 56-63, as drawn). His old head:
    the sheet's hair and the fur it painted over BF's face, above his shoulders. -> his frame with Gogeta's head in his colours"""
    H, W = c.shape; Y, X = np.mgrid[0:H, 0:W]
    area = (Y >= 40) & (Y <= 59) & (X >= 55) & (X <= 77)
    hair = np.isin(g, G_HAIR) & area & ~((Y >= 53) & (X < 57))
    hair |= ndimage.binary_dilation(hair, np.ones((3, 3))) & (g == 1) & area & ~((Y >= 54) & (X < 66))
    face = (Y >= 47) & (Y <= 53) & (X >= 56) & (X <= 63)
    head = hair | face
    out = c.copy()
    old = (Y >= 40) & (Y <= 56) & (X >= 56) & (X <= 72) & (np.isin(c, HAIR) | (np.isin(c, (31, 32, 33, 104, 105)) & (Y <= 53)))
    out[old & ~head] = 0
    for y, x in zip(*np.nonzero(head)):
        v = int(g[y, x]); out[y, x] = G_MAP.get(v, FACE.get(v, v))
    lab, n = ndimage.label(out == 0); edge = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1])
    for t in range(1, n + 1):                                  # pockets the old head left inside the new one (where Gogeta has his
        m = lab == t                                           # shoulder pad behind his hair): the hair's black
        if t not in edge and not (m & ~area).any(): out[m] = 1
    return out


def apply(k, c, fixed):
    """k: (slot, frame, view); c: the frame so far; fixed: the function that gives another frame as fixed (for the mirrored side)"""
    from frames import fr, BF, GOG, GOKU
    s, f, d = k
    if s == 16 and d == 0: return spin_legs(c, fr(BF, *k))
    if s == 16 and d == 2: return spin_side(fixed((s, f, 0)))
    if k == (9, 1, 2): return gogeta_head(c, fr(GOG, *k))
    if s == 21 and f == 10: return fixed((21, 9, 0))
    return c
