"""The Great Ape (Oozaru), from the owner's sheets in ultimate/art/oozaru/ (the review sheets of the package made in the "Oozaru sprite
sheet prompt" chat: 64 x 64 frames drawn at 3x on 192 x 192 tiles; mouths filled dark red, never see-through).

oozaru_moves.png: seven rows of tiles (x = 4 + 198 k, y = 12 + 212 r), each labelled at its top left:
  idle      fr fr th th si si ba ba            walk  fr x4, si x4, ba x4
  combo     combo1 si x4, combo2 si x3, slam si x3
  kiblast   mouthblast si x6, beam si x3, impact si x3
  hurt      block si x2, hurt si x2, knockdown si x3, getup si x2
  transform transform si x6                    powerup  powerup fr x4, taunt fr x2
oozaru_transformations.png: five rows of six frames (x = 190 + 192 k, y = 200 r): goku_bf, vegeta_bf, kid_goku_gt, vegeta_gt (each the
  Saiyan, his eyes red and his tail out, the half-grown ape in his trousers, then the ape roaring, fists high, settling), golden_ape.
Side views face left (the game mirrors them); th (three-quarter) views have no use in this game (front, back, side).
"""
import numpy as np

SCALE, CELL = 3, 64
TILE_BG = (60, 64, 80)
LABEL_ROWS = 14                           # the tile's label (yellow text, top left) lies in its first 14 sheet rows
MOVES = (('idle', ('fr', 'fr', 'th', 'th', 'si', 'si', 'ba', 'ba')),
         ('walk', ('fr',) * 4 + ('si',) * 4 + ('ba',) * 4),
         ('combo', ('combo1',) * 4 + ('combo2',) * 3 + ('slam',) * 3),
         ('kiblast', ('mouthblast',) * 6 + ('beam',) * 3 + ('impact',) * 3),
         ('hurt', ('block',) * 2 + ('hurtsi',) * 2 + ('knockdown',) * 3 + ('getup',) * 2),
         ('transform', ('transform',) * 6),
         ('powerup', ('powerup',) * 4 + ('taunt',) * 2))
TRANSFORMS = ('goku_bf', 'vegeta_bf', 'kid_goku_gt', 'vegeta_gt', 'golden_ape')


def _cell(sheet, x0, y0):
    """One tile's frame at 1x: the middle pixel of each 3 x 3 block; the tile's background and its label clear. -> RGBA (64, 64, 4)"""
    t = sheet[y0:y0 + CELL * SCALE, x0:x0 + CELL * SCALE].astype(int)
    lab = np.zeros(t.shape[:2], bool)
    yellow = (t[..., 0] > 180) & (t[..., 1] > 180) & (t[..., 2] < 120)          # the label's text
    lab[:LABEL_ROWS] = yellow[:LABEL_ROWS]
    small = t[SCALE // 2::SCALE, SCALE // 2::SCALE][:CELL, :CELL]
    clear = (small == TILE_BG).all(2) | lab[SCALE // 2::SCALE, SCALE // 2::SCALE][:CELL, :CELL]
    out = np.zeros((CELL, CELL, 4), np.uint8)
    out[..., :3] = small; out[..., 3] = np.where(clear, 0, 255)
    from scipy import ndimage as ndi                  # the label's anti-aliased edge: small specks alone in the label's corner
    lab, n = ndi.label(out[..., 3] > 0, np.ones((3, 3)))
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 10 and ys.max() < LABEL_ROWS // SCALE + 2 and xs.max() < 40: out[lab == i] = 0
    return out


def blocky(sheet, x0, y0):
    """How far the tile is from being exact 3 x 3 blocks (0: every block one colour)."""
    t = sheet[y0:y0 + CELL * SCALE, x0:x0 + CELL * SCALE].astype(int)
    b = t.reshape(CELL, SCALE, CELL, SCALE, 3)
    return float((b != b[:, :1, :, :1]).any(4).mean())


def frames(art_dir):
    """{'moves': {(row name, view or move): [RGBA frames]}, 'transforms': {name: [6 RGBA frames]}}"""
    from PIL import Image
    mv = np.array(Image.open(art_dir + '/oozaru_moves.png').convert('RGB'))
    tr = np.array(Image.open(art_dir + '/oozaru_transformations.png').convert('RGB'))
    out = {'moves': {}, 'transforms': {}}
    for r, (row, tags) in enumerate(MOVES):
        for k, tag in enumerate(tags):
            out['moves'].setdefault((row, tag), []).append(clean(_cell(mv, 4 + 198 * k, 12 + 212 * r)))
    for r, name in enumerate(TRANSFORMS):            # the change: the ape's frames cleaned (2 on); the small Saiyan as drawn
        out['transforms'][name] = [clean(c) if k >= 2 else c for k, c in enumerate(_cell(tr, 190 + 192 * k, 200 * r) for k in range(6))]
    return out


# ---- clean-up (Nov 9, the owner: "clean up all the ape frames in general especially the face and hands and stuff") -------------------
# The sheets' frames carry noise from the generator: one-pixel flecks of another shade in the fur, dark specks inside the tan fists, feet
# and muzzle, tan dots in the fur, white flecks on the chest. Twice over, each pixel takes the colour that holds at least three of its four
# neighbours when both are fur shades, both tan shades, or a dark speck sits in tan (or a tan dot in fur); a fur pixel also takes a fur
# shade that holds six of its eight neighbours; a white fleck with no mouth, eye or outline beside it (not a tooth, not a glint) takes the
# fur or tan around it. Lines (a finger crease, a muscle edge, the mouth's outline) keep two like neighbours and stay.
OUTLINE = (36, 16, 12)
FUR_TONES = ((82, 42, 32), (106, 62, 46), (134, 88, 70), (170, 130, 112))
SKIN_TONES = ((104, 60, 16), (168, 112, 48), (212, 160, 90), (238, 194, 126))
WHITES = ((255, 255, 240), (248, 248, 240), (252, 244, 252))
FACE = ((96, 24, 16), (200, 32, 20), (236, 120, 120), OUTLINE)


def clean(f, passes=2):
    f = f.copy(); h, w = f.shape[:2]
    for _ in range(passes):
        src = [[tuple(int(v) for v in f[y, x, :3]) if f[y, x, 3] else None for x in range(w)] for y in range(h)]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                p = src[y][x]
                if p is None: continue
                nb = [src[y - 1][x], src[y + 1][x], src[y][x - 1], src[y][x + 1]]
                n8 = nb + [src[y - 1][x - 1], src[y - 1][x + 1], src[y + 1][x - 1], src[y + 1][x + 1]]
                best = max(set(nb), key=nb.count)
                new = None
                if best is not None and best != p and nb.count(best) >= 3:
                    if ((p in FUR_TONES and best in FUR_TONES) or (p in SKIN_TONES and best in SKIN_TONES)
                            or ((p in FUR_TONES or p == OUTLINE) and best in SKIN_TONES) or (p in SKIN_TONES and best in FUR_TONES)):
                        new = best
                if new is None and p in FUR_TONES:
                    b8 = max(set(n8), key=n8.count)
                    if b8 in FUR_TONES and b8 != p and n8.count(b8) >= 6: new = b8
                if new is None and p in WHITES and not any(q in FACE for q in n8):
                    around = [q for q in n8 if q in FUR_TONES or q in SKIN_TONES]
                    if len(around) >= 5: new = max(set(around), key=around.count)
                if new is not None: f[y, x, :3] = new
    return f


# ---- the frames each actor plays, by slot --------------------------------------------------------------------------------------------
# An entry per slot: one spec for every view, or three (front, back, side): (sheet row, tag, [frame numbers]); 'T' is the character's own
# transformation row, 'T-' that row backwards. The sheet draws most moves from the side only: those play in every view (as BF's own big
# bosses do), and docs/art_prompts... note what front and back frames would add.
FRONT = lambda row, tag, ks: ((row, tag, ks),)
BOSS = {                                  # on BF Broly's record and behaviour (his row 10): his slots, his frame counts
    0: (('idle', 'fr', [0, 1]), ('idle', 'ba', [0, 1]), ('idle', 'si', [0, 1])),
    1: (('walk', 'fr', [0, 1, 2, 3]), ('walk', 'ba', [0, 1, 2, 3]), ('walk', 'si', [0, 1, 2, 3])),
    2: (('walk', 'fr', [0, 1, 2, 3]), ('walk', 'ba', [0, 1, 2, 3]), ('walk', 'si', [0, 1, 2, 3])),
    3: (('kiblast', 'mouthblast', [1, 3, 4]),),
    4: (('combo', 'combo1', [0, 1, 2, 3]),),
    5: (('combo', 'combo2', [0, 1, 1, 2]),),
    6: (('combo', 'slam', [0, 0, 1, 2]),),
    7: (('hurt', 'block', [0]),),
    9: (('hurt', 'hurtsi', [0, 1, 1]),),
    13: (('idle', 'fr', [0, 1]), ('idle', 'ba', [0, 1]), ('idle', 'si', [0, 1])),      # Broly's 13 is his stance (the same frames as 0)
    17: (('hurt', 'hurtsi', [1]), ('hurt', 'knockdown', [0, 1, 2, 2, 2, 2, 2])),       # his fall (Broly's last fight frames): down, and stays down
    18: (('combo', 'combo2', [0, 1, 2, 2]),),
    19: (('powerup', 'powerup', [0, 1, 2, 3, 2, 3, 2, 3]),),
    20: (('combo', 'slam', [0, 0, 1, 1, 2, 2]),),
    21: (('kiblast', 'mouthblast', [0, 1, 2, 3, 4, 5]),),
}
# FIRE: the game draws a fighter's blasts and beams from where a fighter's hands are, about 13 pixels up, just in front of his feet (measured
# on the ape: the first build's mouth-glow firing pose had a Kamehameha come out of his knees). So the ape fires from the ground: fists up
# (the charge), then pounded down in front of him, where the blast or beam starts. The sheet's mouth blast stays the boss's own attack.
PLAYER = {                                # a playable Great Ape (GT Kid Goku's, GT Vegeta's): BF's player slots
    0: BOSS[0], 1: BOSS[1], 2: BOSS[2],
    3: (('combo', 'slam', [0, 1, 1]),),                                    # ki blast: fists up, then down on the ground in front (see FIRE)
    4: (('combo', 'combo1', [0, 1, 2, 3]),), 5: (('combo', 'combo2', [0, 1, 2]),), 6: (('combo', 'slam', [0, 1, 2]),),
    7: (('hurt', 'block', [0]),),
    8: (('kiblast', 'mouthblast', [0, 1]), ('combo', 'slam', [0, 0])),      # a beam's charge: a roar, then fists up
    9: (('hurt', 'hurtsi', [0, 1, 1]),),
    10: ('T',), 11: ('T-',),                                                # his transformation; and back
    12: (('powerup', 'taunt', [0, 1]),),                                   # victory: the chest-beat
    13: (('powerup', 'powerup', [0, 1, 2, 3]),),
    14: (('combo', 'slam', [0, 1, 2]),),
    15: (('hurt', 'knockdown', [2, 2, 2, 2]),),                              # lying down
    16: (('hurt', 'knockdown', [0, 1, 2, 2]),),                              # sent tumbling: an ape falls instead
    17: (('hurt', 'knockdown', [0, 1, 2, 2]),),                              # knocked down
    18: (('combo', 'slam', [0, 1, 1]),),                                   # the pose held while a skill fires (see FIRE)
    19: (('kiblast', 'mouthblast', [1, 2, 2, 3, 4]),),                      # Final Flash's slot: the Chou Makouhou (Final Flash's code shows 0 and 1
                                                                             # by turns as it gathers, 2, then 3 and 4 by turns as it fires): the roar,
                                                                             # the glow in his mouth, the blast leaving it (outfit.c flash_draw)
    20: (('powerup', 'powerup', [2, 3, 2]),),
    21: (('kiblast', 'mouthblast', [0, 0, 1, 1]), ('combo', 'slam', [0, 0, 0, 0, 1, 1, 1])),     # the long charge: a roar, fists up, fists down
}


def _views(spec):
    return spec if len(spec) == 3 and all(isinstance(s, tuple) for s in spec) else None


def slot_frames(F, table, character=None, index=None):
    """{slot: [front frames, back frames, side frames]} (RGBA, or BF indices through `index`) for an actor's table (BOSS or PLAYER)."""
    tr = F['transforms'].get(character) if character else None
    conv = (lambda f: index(f)) if index else (lambda f: f)
    out = {}
    for slot, spec in table.items():
        if spec[0] in ('T', 'T-'):
            if tr is None: continue
            seq = tr if spec[0] == 'T' else tr[::-1]
            fr = [conv(f) for f in seq]; out[slot] = [fr, fr, fr]; continue
        views = _views(spec)
        if views:
            out[slot] = [[conv(f) for row, tag, ks in (v,) for k in ks for f in (F['moves'][(row, tag)][k],)] for v in views]
            continue
        fr = [conv(F['moves'][(row, tag)][k]) for row, tag, ks in spec for k in ks]
        out[slot] = [fr, fr, fr]
    return out


# ---- colours ---------------------------------------------------------------------------------------------------------------------------
# The game's own palette (no colour is added or changed, as for every BFU figure). The nearest-colour indexer put the fur's outline and its
# shadow on one entry (48, 16, 0) and its light on a grey-green tan (120, 96, 64): the ape came out a dark blot with green muscles. The fur
# is the palette's red-brown ramp instead, one step each, outline to highlight, so the sheet's five tones stay five (a little more orange
# than the sheet's; the palette has no browns that grey). Everything else (the muzzle, hands and feet, eyes, teeth, the mouth's dark red,
# the blast, the Saiyans' clothes in the change) is the nearest colour.
FUR = {(36, 16, 12): 62, (82, 42, 32): 208, (106, 62, 46): 207, (134, 88, 70): 211, (170, 130, 112): 212}


# The power-up's aura (and two sparks of the slam's dust) is pink on the sheet; the owner (Nov 9): "also make that aura white not pink ... For
# the ape". Its light fill goes white and its outer edge a cool pale grey, as Max Power's white aura (the nearest of the game's colours).
AURA = {(248, 168, 248): (248, 248, 248), (224, 96, 228): (176, 192, 224)}


def to_index(one):
    """RGBA frame -> the game's colour indices (`one`: build.indexer's nearest colour; 0 where the frame is clear)."""
    def conv(f):
        out = np.zeros(f.shape[:2], np.uint8)
        for y, x in zip(*np.nonzero(f[..., 3])):
            c = tuple(int(v) for v in f[y, x, :3])
            out[y, x] = FUR.get(c) or one(np.array(AURA.get(c, c)))
        return out
    return conv


# ---- the skill's icon ------------------------------------------------------------------------------------------------------------------
# The owner (Nov 9): "make it so it has a custom oozaru icon to distinguish from SSJ icon". The Great Ape's head, roaring (red eyes, the
# fangs, the tan muzzle), and the full moon behind him, in the HUD icon's 16 x 9 picture (icons.drawn), on Super Saiyan's frame. The fur is
# FUR's browns; the greyed copy (a skill that can't be used now) darkens each colour a step, as the game's own greyed icons do (Super Saiyan's
# yellows go to the same browns and grey).
ACTORS = ('oozaru', 'oozaru_kid_goku', 'oozaru_vegeta')      # the boss, and the two playable figures (build.py new_actor_ids: in this order)
ICON = ('..K.K.K.K...yWy.',
        '.KDDDDDDDK.yWWWy',
        '.KFLFFFLFK.YWWWY',
        'KFKRRKRRKFKYyWyY',
        'KFMmMMMmMFK.YYY.',
        '.KMMOOOMMK......',
        '.KMTOOOTMK......',
        '..KMOOOMK.......',
        '...KMMMK........')
# The Chou Makouhou's icon (Nov 9, the owner: "give it a new icon as well"): the ape's head side on, red eye, jaws open, the yellow beam
# leaving his mouth; the same colours as the Great Ape's (Y, y and W are the moon's yellows there)
BEAM_ICON = ('..KKKK..........',
             '.KDDDDKK........',
             'KDFLLFFDK.......',
             'KFFFKRFMMK...YYY',
             'KFFFFFMMMMKYyyyy',
             'KFFFFFMKTOyWWWWW',
             'KFFFFFMKOOyWWWWW',
             '.KFFFFMMTKYyyyyy',
             '..KKKKKKK....YYY')
ICON_COLOURS = {'K': 62, 'D': 208, 'F': 207, 'L': 211, 'M': 201, 'm': 200, 'R': 3, 'O': 31, 'T': 2, 'Y': 28, 'y': 29, 'W': 246}
ICON_GREYED = {'K': 62, 'D': 62, 'F': 208, 'L': 207, 'M': 204, 'm': 205, 'R': 104, 'O': 77, 'T': 115, 'Y': 205, 'y': 204, 'W': 115}
