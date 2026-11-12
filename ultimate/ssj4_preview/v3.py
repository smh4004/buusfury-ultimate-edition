"""Scratch, third look (the owner, Nov 11 18:44): "Make the eyebrows red too for Daima. Can you use the new Gogeta hair for the front
view of SSJ4 Goku only, and leave the side and back views as the original and show how those look with gifs?"; 18:45, with a picture
of Goku SS4 in GT and in Daima side by side: "Note these too and apply if possible".
  mix        Gogeta's hair shape where the head is seen from the front; the side and back heads as they are; fur a little darker
  daima      the mix in the Daima colours he called "mostly good", with his picture's notes
  daima_pic  the mix in his picture's own colours (plum hair darker than the fur), with the notes
The picture's notes, as far as a 32-pixel figure can show them: eyebrows the hair's colour; no red line round the eye, a red iris;
the waistband the trousers' colour (no blue sash); blue boots with red laces; the tail the fur's colour (it is fur here already).
Not shown at this size: the chest's clover shape (his chest is 8 by 4 pixels) and the bare inner forearm."""
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from v2 import *
import v2

DARK = (1, 111, 112); TROUSERS = (24, 25, 26, 27, 28); BLUES = (69, 157, 158, 159, 160, 161); HAND = (200, 201, 203)
BOOTISH = (116, 118, 206)
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]; N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(mask, nb=N8):
    """[array of (y, x)] of a mask's joined pieces."""
    H, W = mask.shape; seen = np.zeros((H, W), bool); out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]: continue
        q = [(y0, x0)]; seen[y0, x0] = True; got = []
        while q:
            y, x = q.pop(); got.append((y, x))
            for a, b in nb:
                Y, X = y + a, x + b
                if 0 <= Y < H and 0 <= X < W and mask[Y, X] and not seen[Y, X]: seen[Y, X] = True; q.append((Y, X))
        out.append(got)
    return out


def touching(c, comp, colours, nb=N8):
    """How many of a piece's pixels have one of `colours` beside them."""
    H, W = c.shape; n = 0
    for y, x in comp:
        if any(0 <= y + a < H and 0 <= x + b < W and c[y + a, x + b] in colours for a, b in nb): n += 1
    return n


def as_mask(shape, comps):
    m = np.zeros(shape, bool)
    for comp in comps:
        for y, x in comp: m[y, x] = True
    return m


def parts(out, loc):
    """Where things are in a frame (his own colours): -> dict of masks: hair, face (the head's own face pixels), boots (their dark
    pixels), laces (trouser yellow shut inside a boot), wraps (the boots' greys), sash, and the notes on what was found."""
    H, W = out.shape; dark = np.isin(out, DARK); comps = components(dark)
    face = np.zeros((H, W), bool); headbox = np.zeros((H, W), bool)
    if loc is not None:
        sc, x, y, v = loc; t = FULL[v]; f = (t > 0) & ~OLD[v]; f[ROWS:] = False
        for yy, xx in zip(*np.nonzero(f)):
            if 0 <= y + yy < H and 0 <= x + xx < W: face[y + yy, x + xx] = True
        headbox[max(y - 8, 0):y + 12, max(x - 6, 0):x + t.shape[1] + 8] = True
    hair_c, boot_c = [], []
    for comp in comps:
        m = as_mask((H, W), [comp])
        if (loc is not None and (m & headbox).any()) or (loc is None and len(comp) >= 40): hair_c.append(comp)
        elif touching(out, comp, BOOTISH): boot_c.append([q for q in comp if touching(out, [q], BOOTISH)])   # a boot: the dark right by its greys and sole
    hairm = as_mask((H, W), hair_c) & ~face
    if loc is not None:                                    # as the second look had it: what hangs from his head, not his chest's outline
        sc, x, y, v = loc; zone = np.zeros((H, W), bool); zone[max(y - 8, 0):y + 19] = True
        m = hairm & zone; seed = np.zeros((H, W), bool); seed[max(y - 8, 0):y + 6] = m[max(y - 8, 0):y + 6]
        while True:
            n = seed.copy(); n[1:] |= seed[:-1]; n[:-1] |= seed[1:]; n[:, 1:] |= seed[:, :-1]; n[:, :-1] |= seed[:, 1:]; n &= m
            if (n == seed).all(): break
            seed = n
        hairm = seed
    boots = as_mask((H, W), boot_c)
    near = boots.copy()
    for a, b in N8: near |= np.roll(np.roll(boots, a, 0), b, 1)
    wraps = np.isin(out, (116, 117, 118)) & near & ~face
    # trouser yellow that is not part of his trousers: small pieces beside a boot
    laces = np.zeros((H, W), bool)
    for comp in components(np.isin(out, TROUSERS), N4):
        if len(comp) <= 3 and as_mask((H, W), [comp])[near].any(): laces |= as_mask((H, W), [comp])
    sash = np.zeros((H, W), bool)
    for comp in components(np.isin(out, BLUES)):
        tr = touching(out, comp, TROUSERS, N4); hd = touching(out, comp, HAND, N4)
        below_t = sum(1 for y, x in comp if y + 1 < H and out[y + 1, x] in TROUSERS)
        below_h = sum(1 for y, x in comp if y + 1 < H and out[y + 1, x] in HAND + (202, 16))
        if tr >= 3 and below_t > below_h and not (near & as_mask((H, W), [comp])).any(): sash |= as_mask((H, W), [comp])
    return {'hair': hairm, 'face': face, 'boots': boots, 'wraps': wraps, 'laces': laces, 'sash': sash}


FUR = v2.FUR
LOOKS = {
    'daima': {'body': {31: 32, 32: 129, 33: 129, 105: 121, 104: 129, 24: 80, 25: 64, 26: 109, 27: 110, 28: 110}, 'hair': {1: 104, 111: 129, 112: 121}},
    # his picture: hair (96,40,80), fur (144,64,108): the game's plums 127 (120,32,64), 39 (152,24,88), 40 (184,56,120)
    'daima_pic': {'body': {31: 127, 32: 39, 33: 40, 105: 40, 104: 39, 24: 80, 25: 64, 26: 109, 27: 110, 28: 110}, 'hair': {1: 127, 111: 39, 112: 39}},
}
BOOT = {1: 69, 111: 158, 112: 158}; WRAP = {116: 160, 117: 160, 118: 160}; LACE = 33
BROWS = {0: ((11, 8), (11, 9), (11, 10), (11, 12), (11, 13), (11, 14))}        # of the standing head's picture (row, column)
LINER = {0: ((12, 8), (13, 8), (13, 14))}                                      # GT's red line round the eye: Daima's is black
IRIS = {0: ((13, 10), (13, 12)), 2: ((12, 7),)}


def frame(slot, f, d, kind, views=(0,)):
    img = R.frame(AID, slot, f, d)
    if kind == 'now': return img
    out, loc = shaped(slot, f, d, views=views)
    res = out.copy()
    if kind == 'mix':
        for k, to in FUR.items(): res[out == k] = to
        return res
    look = LOOKS[kind]; p = parts(out, loc)
    for k, to in look['body'].items(): res[out == k] = to
    for k, to in look['hair'].items(): res[p['hair'] & (out == k)] = to
    for k, to in BOOT.items(): res[p['boots'] & (out == k)] = to
    for k, to in WRAP.items(): res[p['wraps'] & (out == k)] = to
    res[p['laces']] = LACE
    for k, to in ((69, 24), (157, 24), (158, 25), (159, 25), (160, 26), (161, 26)): res[p['sash'] & (out == k)] = look['body'][to]
    if loc is not None:
        sc, x, y, v = loc; t = FULL[v]; H, W = out.shape
        def at(pts, want, to):
            for yy, xx in pts:
                Y, X = y + yy, x + xx
                if 0 <= Y < H and 0 <= X < W and t[yy, xx] in want and out[Y, X] == t[yy, xx]: res[Y, X] = to
        at(BROWS.get(v, ()), (1, 111), look['hair'][1]); at(LINER.get(v, ()), (31,), 1); at(IRIS.get(v, ()), (25,), 33)
    return res
