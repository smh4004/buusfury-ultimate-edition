"""GT Goten's and GT Trunks's Fusion Dance (slot 21): the kid figures' own dance (kid Goten 114 / 115, kid Trunks 260 / 261), every
frame the kid's, the head and skin untouched, the clothes dressed in the GT look's colours.

The dance script plays slot 21 of the partner's form (outfit.c dance_use, native 0x9C). The GT looks came from Black Star Odyssey's
sheets, whose slot 21 is something else (GT Goten: one crouched frame held; GT Trunks: a dash and a kick), so the dance showed
those (Nov 15, the owner: "why the fuck is gt trunks fusion dance so fucked").

The kid's clothes are told apart by colour, then by where they sit: the trousers are the clothing pieces just above the feet
(found by walking up each foot's column), everything else above them is the top. A Goten frame: orange gi top and trousers, navy
undershirt / sleeves / belt / ankle bands, grey shoes. A Trunks frame: dark grey gi, orange wristbands / sash / boots, grey soles.
All 11 dance frames stand on row 30 of the 32-row canvas (goku_black.actor_frames), in every view (the dance faces front)."""
import numpy as np
from scipy import ndimage

ORANGE = (79, 63, 64, 65)            # dark -> light; 78 is orange's darkest, read as 79
NAVY = (93, 94, 95)
GREY = (112, 114, 117, 119)          # Goten's shoes, Trunks's gi (113 is part of Goten's eyes, left alone)
WHITE = 2

# GT colour ramps, dark -> light, read off the GT looks' own stance frames (gt.py, the owner's sheet)
LOOKS = {
    'goten_gt':       {'jacket': (116, 116, 118, 120), 'pants': (86, 168, 90, 91), 'shoes': (208, 17, 82, 82), 'belt': 168},
    'goten_gt_green': {'jacket': (187, 187, 252, 253), 'pants': (86, 168, 90, 91), 'shoes': (208, 17, 82, 82), 'belt': 168},
    # Trunks: his grey gi -> the jacket (grey ramp) and trousers; his orange wristbands -> the jacket's cuffs, sash -> the trousers' crease and belt
    'trunks_gt':      {'jacket': (111, 112, 113, 113), 'cuff': (1, 111, 112, 112), 'pants': (115, 118, 120, 120), 'crease': (115, 115, 118, 118),
                       'shoes': (111, 205, 205, 205), 'belt': 113, 'sole': 111, 'shirt': (176, 174, 174, 174)},
}
SOURCE = {'goten_gt': 114, 'goten_gt_ssj': 115, 'goten_gt_green': 114, 'trunks_gt': 260, 'trunks_gt_ssj': 261}      # (the green look's Super Saiyan plays goten_gt_ssj's figure)


def look_of(name):
    return LOOKS[name.replace('_ssj', '')]


def _trousers(c, cloth, skip):
    """Labels of the clothing pieces right above the feet: walk up each column that reaches the frame's bottom row."""
    lab, n = ndimage.label(np.isin(c, cloth))
    ys, xs = np.nonzero(c); bottom = ys.max(); found = set()
    for x in range(c.shape[1]):
        if not c[bottom, x]: continue
        for y in range(bottom, max(bottom - 9, -1), -1):
            v = c[y, x]
            if lab[y, x] and y < bottom - 1: found.add(lab[y, x]); break
            if v and v not in skip and v != 1 and not lab[y, x]: break
    if found:          # a raised knee (frame 6) doesn't reach the bottom row: any piece that starts no higher than the trousers is trousers too
        top = min(np.nonzero(lab == k)[0].min() for k in found)
        found |= {k for k in range(1, n + 1) if np.nonzero(lab == k)[0].min() >= top and np.nonzero(lab == k)[0].max() < bottom - 1}
    return lab, found, bottom


def _body(c):
    """The figure's largest 8-connected piece: sparkles drawn apart from it keep the kid's own colours."""
    lab, n = ndimage.label(c > 0, np.ones((3, 3), bool))
    if n <= 1: return c > 0
    sizes = ndimage.sum(np.ones(c.shape), lab, range(1, n + 1))
    return lab == 1 + int(np.argmax(sizes))


def goten(c, look):
    """One kid Goten frame (114 / 115) in a GT Goten look."""
    L = LOOKS[look]; c = np.where(c == 78, 79, c); out = c.copy()
    lab, legs, bottom = _trousers(c, ORANGE, set(NAVY) | set(GREY) | {WHITE})
    pants = np.isin(lab, list(legs)) if legs else np.zeros(c.shape, bool)
    top_y = np.nonzero(pants)[0].min() if pants.any() else bottom - 7
    near = ndimage.binary_dilation(pants, np.ones((3, 3), bool)); body = _body(c)
    for y, x in zip(*np.nonzero(body)):
        v = c[y, x]
        if v in ORANGE: out[y, x] = L['pants' if pants[y, x] else 'jacket'][ORANGE.index(v)]
        elif v == 1 and 0 < y < bottom and pants[y + 1, x] and c[y - 1, x] in ORANGE + NAVY: out[y, x] = L['belt']      # his belt
        elif v in NAVY:
            low = near[y, x] or y >= bottom - 3
            out[y, x] = L['pants' if low else 'jacket'][1 + NAVY.index(v)]
        elif (y >= bottom - 3 or (near[y, x] and y > top_y)) and (v in GREY or v == WHITE):      # shoes, a raised foot's too
            out[y, x] = L['shoes'][min(3, GREY.index(v) if v in GREY else 3)]
    return out


def trunks(c, look):
    """One kid Trunks frame (260 / 261) in GT Trunks's look: black jacket over a blue shirt, light grey trousers, brown boots."""
    L = LOOKS[look]; c = np.where(c == 78, 79, c); out = c.copy()
    lab, legs, bottom = _trousers(c, GREY, set(ORANGE))
    pants = np.isin(lab, list(legs)) if legs else np.zeros(c.shape, bool)
    top_y = np.nonzero(pants)[0].min() if pants.any() else bottom - 7
    near = ndimage.binary_dilation(pants, np.ones((3, 3), bool)); body = _body(c)
    jacket = body & np.isin(c, GREY) & ~pants & (np.arange(c.shape[0])[:, None] < bottom - 1)
    for y, x in zip(*np.nonzero(body)):
        v = c[y, x]
        if v in GREY:
            if y >= bottom - 1 and not pants[y, x]: out[y, x] = L['sole']
            else: out[y, x] = L['pants' if pants[y, x] else 'jacket'][GREY.index(v)]
        elif v in ORANGE:
            k = ORANGE.index(v)
            if y >= bottom - 3 and not pants[y, x]: out[y, x] = L['shoes'][k]
            elif y <= top_y - 1 and near[y, x]: out[y, x] = L['belt']
            elif near[y, x] and y >= top_y: out[y, x] = L['crease'][k]
            else: out[y, x] = L['cuff'][k]
    # the shirt: the jacket's middle columns under his chin (the skin just above the jacket's top row), down to the belt
    if jacket.any():
        jt = np.nonzero(jacket)[0].min()
        chin = [x for x in range(c.shape[1]) if c[jt - 1, x] in (200, 201, 202, 203) and body[jt - 1, x]] if jt else []
        if chin:
            cx = int(round(np.mean(chin)))
            for y in range(jt, top_y - 1):
                for x in range(cx - 1, cx + 2):
                    if jacket[y, x]: out[y, x] = L['shirt'][GREY.index(c[y, x])]
    return out


def dance(clean, name):
    """[down, up, side] frame lists for the look's slot 21, from the kid's own dance."""
    import goku_black
    views = goku_black.actor_frames(clean, SOURCE[name])[21]
    look = name.replace('_ssj', '')
    fn = goten if look.startswith('goten') else trunks
    return [[fn(f, look) for f in v] for v in views]
