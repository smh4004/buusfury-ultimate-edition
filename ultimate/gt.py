"""Dragon Ball GT: fighters, looks and Ledgic, from Black Star Odyssey's sprites (the owner's review sheet, bso_import.py).

The party's GT looks are outfits on the Switch Character screen, with their transformations; Pan and Uub join the guest
slot; Ledgic is a Challenger. Every actor here is built on the BF actor of the form it plays as (so each skill finds the
animation slots it expects); a slot the BSO actor doesn't draw takes one of its own frames that fits (FILL), never the
template's, which would show the wrong character.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# actor: BF actor it is built on (that form's own). Order = actor ids (build.new_actor_ids appends them in this order).
ACTORS = {
    'kid_goku': 106, 'kid_goku_ssj': 109, 'kid_goku_ssj3': 111, 'kid_goku_ssj4': 109,
    'gogeta_ssj4': 93,
    'gohan_gt': 98, 'gohan_gt_noglasses': 98, 'gohan_gt_ssj': 104,
    'goten_gt': 114, 'goten_gt_green': 114, 'goten_gt_ssj': 115,
    'trunks_gt': 260, 'trunks_gt_ssj': 261,
    'vegeta_gt': 270, 'vegeta_gt_tank': 270, 'vegeta_gt_mustache': 270, 'vegeta_gt_ssj': 273, 'vegeta_gt_tank_ssj': 273, 'vegeta_gt_ssj4': 273,
    'pan': 114, 'pan_nobandana': 114, 'pan_bug': 114, 'pan_gi_tan': 114, 'pan_gi_red': 114, 'pan_brapan': 114, 'pan_ssj': 115, 'pan_ssj_spiky': 115,
    'uub': 114, 'majuub': 114,
    'ledgic': 64,
}
# A slot the page doesn't draw: the first of these the actor has (BF slot use: 0 idle, 1 walk, 2 run, 3 / 10 / 13 charge,
# 4-6 melee, 7 / 15 hurt, 8 / 9 / 21 ki, 11 the change back, 14 / 20 strikes, 16-17 knocked down, 18 the pose held firing a skill).
# (21, 0, 4): frames 0-3 of slot 21, whose first frames are the hands-at-the-hip charge of BF's slot 8 (the Kamehameha's) and whose last ones
# are a dash away that a transformation shouldn't show.
FILL = {2: (1,), 3: (8, 21, 4), 5: (4,), 6: (4,), 7: (9,), 8: ((21, 0, 4), 3, 18), 10: ((21, 0, 8), 13, 8, 3), 11: (0,), 12: (0,), 13: (3, 8, 0),
        14: (20, 6, 4), 15: (9, 7), 16: (17,), 18: (3, 8, 0), 19: (14, 6, 0), 20: (14, 6, 4), 21: (8, 3, 10), 22: (0,)}


def _pick(frames, alt):
    s, a, b = alt if isinstance(alt, tuple) else (alt, None, None)
    if s not in frames: return None
    return [v[a:b] for v in frames[s]] if a is not None else frames[s]
# speaker ids for the portraits (page 0 of the sheet), after Goku Black's and Rose's 166-167
PORTRAITS = ('kidgoku', 'pan', 'pan_nobandana', 'pan_bug', 'brapan', 'trunks', 'trunks_ssj', 'gohan', 'gohan_ssj',
             'goten', 'goten_surprised', 'goten_angry', 'goten_ssj', 'goten_ssj_surprised', 'goten_ssj_angry',
             'vegeta', 'vegeta_gt', 'vegeta_ssj4', 'gogeta_ssj4', 'uub')     # Uub: no art yet, the frame alone (see portraits)
FIRST_PORTRAIT = 168


def portrait_id(name):
    return FIRST_PORTRAIT + PORTRAITS.index(name)


def template_slots(rom, actor):
    import struct
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    rec = u(0x6B6BD8 + 4 * actor) - 0x08000000; n = u(rec) & 0xFF
    return [s for s in range(n) if u(rec + 0x54 + 4 * s)], n


# Uub's and Majuub's flying (slot 15; Nov 9, the owner: "Those flying frames are super fucked for Uub/Majuub fix that too"). The sheet draws Uub's
# on kid Goten's flying (as BSO's tools/uub.py does for every Goten-based move) and Majuub's on base Gotenks', whose torso his big hair covers:
# with Uub's smaller head on it Majuub flew as a head with a strip of trousers trailing behind (side), a head on two hands (front). Majuub's
# is now Uub's flying in Majuub's outfit, as the sheet itself does for every move it builds on Goten for both (8, 13, 16, 18-21: Uub's frames,
# his colours swapped); and seen from the front both lose what Goten's legs and boot soles left round the smaller head (a green tuft and grey
# specks above his hair).
GREENS = {216: 0, 251: 1, 252: 2}                 # Uub's tunic and trousers, dark -> light (BFU indices; the sheet's green ramp)
GOLD = {25, 250, 110}                             # sash and wristbands (both looks)
MAJUUB_VEST = 70                                  # Majuub's navy vest (all the sheet's vest shades come out as this one)
MAJUUB_PANTS = {0: 117, 1: 119, 2: 120}           # his white trousers (the sheet's Uub -> Majuub frames: 216 -> 117/118, 251 -> 119/120)
HAIR, SKIN = {1}, {77, 78, 79, 16, 17, 202}
EYE_WHITE = {2}                                   # the eye whites (front views: two eyes on one row)
GOTEN_NAVY = 157                                  # Goten's flickering navy sleeves, left in a few of Uub's frames as dark purple specks


def eye_at(c):
    """(row, column) of the eyes: the eye whites within the figure's top 18 rows."""
    top = np.nonzero(c.any(1))[0].min()
    e = np.argwhere(c[:top + 18] == 2)
    return (int(e[:, 0].min()), int(round(e[:, 1].mean()))) if len(e) else None


def flying_front(c, ref, first):
    """A front flying frame. Its head is his standing head (the sheet pastes the same one), so above the eyes it becomes exactly what the
    standing front frame `ref` has there (lined up by the eyes): Goten's legs and boot soles behind it, and the grey and green specks they
    left in the hair, go. Goten's sleeve flicker (GOTEN_NAVY) takes the first frame's colour at that spot (the frames are the same but for it)."""
    c = c.copy(); e, r = eye_at(c), eye_at(ref)
    if e and r:
        dy, dx = e[0] - r[0], e[1] - r[1]
        moved = np.zeros_like(c)
        ys, xs = np.nonzero(ref)
        ok = (ys + dy >= 0) & (ys + dy < c.shape[0]) & (xs + dx >= 0) & (xs + dx < c.shape[1])
        moved[ys[ok] + dy, xs[ok] + dx] = ref[ys[ok], xs[ok]]
        c[:e[0]] = moved[:e[0]]
    fix = (c == GOTEN_NAVY) & (first != GOTEN_NAVY)
    c[fix] = first[fix]
    return c


def despeck(c):
    """Any GOTEN_NAVY speck left: the commonest colour round it."""
    c = c.copy()
    for y, x in np.argwhere(c == GOTEN_NAVY):
        near = [int(v) for v in c[max(0, y - 1):y + 2, max(0, x - 1):x + 2].ravel() if v and v != GOTEN_NAVY]
        c[y, x] = max(set(near), key=near.count) if near else 0
    return c


def majuub_dress(c, view):
    """Uub's flying frame in Majuub's outfit: the tunic -> his navy vest, the trousers -> his white ones. Seen from the front or behind only his
    back and shoulders show; from the side the trousers start at the sash (its gold in the body's lower rows, behind the fist's wristband)."""
    c = c.copy(); g = np.isin(c, list(GREENS))
    legs = np.zeros(c.shape, bool)
    if view == 2:
        ys, xs = np.nonzero(c); body = np.zeros(c.shape, bool); body[ys.max() - 3:] = True
        fist = np.nonzero(np.isin(c, list(SKIN)) & body)[1]
        gold = np.argwhere(np.isin(c, list(GOLD)) & body)
        gold = gold[gold[:, 1] > (fist.max() + 2 if len(fist) else 0)]
        if len(gold): legs[:, gold[:, 1].min() - 1:] = True
    for y, x in zip(*np.nonzero(g)):
        c[y, x] = MAJUUB_PANTS[GREENS[c[y, x]]] if legs[y, x] else MAJUUB_VEST
    return c


def repair(frames):
    """Uub's and Majuub's flying (above), in place; then no Goten navy specks left in either."""
    if 'uub' not in frames: return
    uub = frames['uub'][15]
    first = uub[0][0]
    uub[0] = [flying_front(c, frames['uub'][0][0][0], first) for c in uub[0]]
    if 'majuub' in frames:
        frames['majuub'][15] = [[majuub_dress(c, v) for c in uub[v]] for v in range(3)]
    for name in ('uub', 'majuub'):
        for views in frames.get(name, {}).values():
            for v in range(3): views[v] = [despeck(c) for c in views[v]]


def actors(clean, pal, lengths):
    """{name: build_actors cfg} for every GT actor."""
    sys.path.insert(0, HERE)
    import bso_import
    frames, info = bso_import.load_all(clean, pal, list(ACTORS))
    frames = {k: {s: [list(v) for v in views] for s, views in f.items()} for k, f in frames.items()}    # (a copy: load_all's is cached)
    repair(frames)
    out = {}
    for name, tpl in ACTORS.items():
        have = dict(frames[name]); slots, n = template_slots(clean, tpl)
        missing = []
        for s in sorted(set(slots) | {10, 11}):          # 10 transforming and 11 changing back, whether or not the template has them
            if s in have or s >= n: continue
            alt = next((a for a in FILL.get(s, (0,)) + (0,) if _pick(frames[name], a) is not None), 0)
            have[s] = _pick(frames[name], alt); missing.append((s, alt))
        cfg = {'template': tpl, 'raw_frames': {str(k): v for k, v in sorted(have.items()) if k < n}, 'compress': True, 'high': True}   # above 16 MB in a 32 MB build
        if name == 'ledgic': cfg['big'] = True
        else: cfg['grow'] = lengths
        out[name] = cfg
    return out


def portraits(one):
    """[64x64 OBJ index arrays] in PORTRAITS order (each in the game's gold frame, as the sheet draws it)."""
    sys.path.insert(0, HERE)
    import bso_import
    got = bso_import.portraits(one)
    stack = np.array([got[p] for p in PORTRAITS if p != 'uub'])
    frame = (stack == stack[0]).all(0)                                 # the gold frame: the same in every portrait
    blue = got['vegeta_gt'][~frame]; blank = got['vegeta_gt'].copy()
    blank[~frame] = np.bincount(blue.astype(int)).argmax()            # Uub: the frame round a plain background (Vegeta's blue), until there is art
    got['uub'] = blank
    return [got[p] for p in PORTRAITS]
