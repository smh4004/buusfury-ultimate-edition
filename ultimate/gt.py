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


def actors(clean, pal, lengths):
    """{name: build_actors cfg} for every GT actor."""
    sys.path.insert(0, HERE)
    import bso_import
    frames, info = bso_import.load_all(clean, pal, list(ACTORS))
    out = {}
    for name, tpl in ACTORS.items():
        have = dict(frames[name]); slots, n = template_slots(clean, tpl)
        missing = []
        for s in sorted(set(slots) | {10, 11}):          # 10 transforming and 11 changing back, whether or not the template has them
            if s in have or s >= n: continue
            alt = next((a for a in FILL.get(s, (0,)) + (0,) if _pick(frames[name], a) is not None), 0)
            have[s] = _pick(frames[name], alt); missing.append((s, alt))
        cfg = {'template': tpl, 'raw_frames': {str(k): v for k, v in sorted(have.items()) if k < n}, 'compress': True}
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
