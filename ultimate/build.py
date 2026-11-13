#!/usr/bin/env python3
"""Buu's Fury Ultimate Edition build. Run from the repo root.

    python3 ultimate/build.py [--debug]

Needs baserom.gba (clean USA Buu's Fury, checked by SHA-1) and assets from `make extract`.
Steps: apply edits to assets (debug only for now), `make modern`, move the form table past the ROM's old end,
append ultimate/forms.json rows, then write ultimate/out/BFU[_debug].bps and a personal-use .gba.
Asset edits are always undone afterwards, so assets/ stays a clean extract.
"""
import colorsys, hashlib, json, os, re, shutil, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.join('tools'))
sys.path.insert(0, 'ultimate/lib')
import bps
import numpy as np
import sprites, artclean, wfz
import icons as iconlib
sys.path.insert(0, 'ultimate')
import gogeta
import goku_black
import ssb
import gt
import garlic_art
import super_garlic

CLEAN_SHA1 = 'f1c4b07554d2a3b1ad2f325307051e775ce68087'
ROM_BASE = 0x08000000
FORMS, FORM_COUNT, FORM_SIZE = 0x6B82EC, 54, 24
NATIVES = 0x55098
NATIVE_REFS = (0x3F40, 0x4030)      # the only two literals naming the native table
CODE_END = 0x54FBC
HEAP_WORDS = 0xFDFE - 0x400      # the top 4 KB of work RAM belongs to outfit.c
SPACE = 0x800000                 # new data starts at the old 8 MB end: forms, then code
ACTORS_AT = 0x850000             # moved actor table and imported sprites (0x840000 until Nov 12: the code area before it had filled up)
NEW_ACTORS = {}                  # the new actors' ids, once add_actors has made them (main)
BEERUS_LOOK = 'new,2,2'          # Beerus's side head, pixels of torso, pixels of legs added (see cfg['beerus']). The owner, Nov 11 17:56: "New side view and 34 pixels for sure looks better"
ROM32 = '--rom16' not in sys.argv  # 32 MB: the GT actors live above 16 MB and the save chip moves to 0x0DFFFF00 (lib/rom32.py). --rom16: the old 16 MB layout
COMBO_SHA1 = 'f02d179accbeb9b68bcaef8720eb0ae426dde6ee'
PROTO = os.environ.get('BFU_PROTO', 'protoD.gba')   # Prototype D cart: Super 13 and Zone 26
LOG2 = os.environ.get('BFU_LOG2', 'log2.gba')      # Legacy of Goku II (USA): Zone 26's snow tiles
COMBO = os.environ.get('BFU_COMBO', 'combo.gba')   # Legacy of Goku I & II cart; LoG2 = its second 8 MB
JOIN_NATIVE = 0xFE               # party_join in outfit.c. The mod's natives are 0xF8-0xFF (the native table moved and grown: retail has 248)
BOMB_FX, BOMB_AT = 0xFB, 0xFC     # the Spirit Bomb scene's effects
ERASER_SKILL = 24                # a new row past the retail table: Big Bang's code with green frames
ERASER_UI = 1534                 # strings past the retail table: name, description of each new move
BOMBER_SKILL = 25
PORTRAITS = (20, 90, 94)         # LoG2 portrait table: Android 17, Future Trunks, Super Saiyan Future Trunks = speaker ids 163, 164, 165
SS2_FLAG = 864                   # + the owner's party slot: set where the story reaches Super Saiyan 2
BLITZ_SKILL = 27                 # Android 17 and 18
DISC_SKILL = 28                  # Krillin and Android 18: LoG2's spinning gold disc on Big Bang's code
POWER_UP_VT = 0x4E2B0            # the state a transformation runs in
SUPER13_SKILL, SUPER17_SKILL = 30, 31     # Android 13 and Android 17 transform: Super Saiyan's mechanics under their own names
WAVE_SKILL = 29                  # Full Power Energy Wave, from Gero's Legacy: the Electric Kamehameha's code with green frames
BEAM_SKILL = 26                  # Special Beam Cannon: the Kamehameha's code with gold and purple frames
ROSE_SKILL, BLACK_KAME_SKILL = 32, 33      # Goku Black: Super Saiyan Rose (Super Saiyan's mechanics), Black Kamehameha (the Kamehameha's code, purple, or pink as Rose)
BLACK_NAME_UI, ROSE_NAME_UI = 1534 + 42, 1534 + 43     # form names, after Glacier's
GT_NAME_UI = 1534 + 44            # Pan, Uub, Majuub, Brapan (forms.json uses these numbers)
MAJUUB_SKILL = 34                # Uub becomes Majuub: Super Saiyan's mechanics, Android 13's aura-less power-up
# Transformations and moves added Nov 9 (owner): each its own row, icon and name
SS2_SKILL, SS4_SKILL, KAIOKEN_SKILL = 35, 36, 37                  # Super Saiyan 2 and 4 (Super Saiyan 3's icon with a 2 / a purple 4), Kaioken (a red Z)
GALICK_SKILL, TENX_SKILL, FINAL_SHINE_SKILL, DRAGON4_SKILL = 38, 39, 40, 41     # Kamehameha's code violet / red, Final Flash's green, Dragon Fist's red
SOLAR_FLARE_SKILL, SUPER_KAME_SKILL = 42, 43
MAX_POWER_SKILL = 45             # Master Roshi's Max Power (Nov 9)
STORY_MARKS = ((858, 38), (860, 132), (864, 120))     # outfits.json unlocks whose scene also sets a story flag: (unlock flag, scene's flag; outfit.c story_sync)
SSG_SKILL = 46                   # Super Saiyan God (Nov 9): Goku, from base, after the Battle of Gods ritual with Super Saiyan mastered
FP_SKILL = 47                    # Full Power (Nov 9): Mystic Gohan only, from his orange gi (form 13), learned with it (outfit flag MYSTIC_FLAG)
# The Great Ape, shelved (Nov 10, the owner: "Remove the whole great ape thing from the game and shelf it for now it just looks bad honestly
# needs a redo for sprites"; its code is on the branch shelf/great-ape). Its ids stay taken, so a save from the Nov 9 build reads nothing past
# a table: skills 48 (the Great Ape) and 49 (the Chou Makouhou) are empty rows, and its three forms (159-161) copies of the GT looks they
# changed from. outfit.c shelved_fix takes those skills out of a fighter's slots and puts him back in his own look.
SHELVED_SKILLS = (48, 49)
SHELVED_FORMS = ('kid_goku', 'vegeta_gt', 'vegeta_gt_tank')     # forms 159, 160, 161 in the Nov 9 build, in this order
SHELVED_FIRST_FORM = 159
POTARA_SKILL, DANCE_SKILL = 50, 12      # the Potara (Nov 12: its own skill, for more fusions to come; Goku and Vegeta, all four Trials won), the Fusion Dance (retail; Goku and Vegeta after the ending): outfit.c potara_*, dance_use
POTARA_PAIRS = ((6, 0, 4),)     # (fused, dancer, dancer): outfit.c potara_pairs
POTARA_LOOK, POTARA_SECONDS = 284, 3600     # Vegito's look (native 0x9D, as the story's Potara scene sets it); an hour (Dragon Ball Super: the Potara's limit for mortals)
SKILL_IDS_END = 51               # one past the last skill row (checked once the table is built)
MYSTIC_FLAG = 860                # outfits.json: the Elder Kai's scene gives Gohan the orange gi (outfit 110)
CELL_UNLOCKS = (873, 874, 875, 879)    # outfits.json: the Cell Games' prize opens the Saiyan armor (Gohan, Trunks, Vegeta) and Future Trunks
# Post-game gear (Nov 9): rows past the game's 162, each working on the new moves (outfit.c reads them). (row, name, text, base row for the
# picture, slot 0 body 1 hands 2 feet 3 accessory, STR POW PDEF KDEF SPD, EXP bonus /256, picture hue or None)
GEAR_POTARA, GEAR_GRAVITY, GEAR_SHADES, GEAR_SHELL, GEAR_POUCH, GEAR_NECKLACE = 162, 163, 164, 165, 166, 167
GEAR = ((GEAR_POTARA, 'Potara Earrings', "The Supreme Kai's earrings. Every transformation drains its ki a third slower.", 153, 3, (0, 10, 10, 10, 0), 0, 95),
        (GEAR_GRAVITY, 'Gravity Band', "Bulma built it for Vegeta's training. Transformations are mastered twice as fast.", 67, 1, (10, 0, 5, 5, -5), 0, 215),
        (GEAR_SHADES, "King Kai's Shades", "King Kai's own sunglasses. The Kaioken wears on your health half as much.", 117, 3, (0, 5, 5, 5, 0), 0, None),
        (GEAR_SHELL, 'Turtle Shell', "Master Roshi's training shell. Heavy and slow, but you learn twice as fast.", 13, 0, (0, 0, 20, 20, -20), 256, 120),
        (GEAR_POUCH, 'Senzu Pouch', "Korin's pouch of Senzu crumbs. Slowly restores your health in battle.", 121, 3, (0, 0, 5, 5, 0), 0, 75),
        # the Garlic Jr. quest's prize (garlic.py): the owner chose +END and +Ki; its picture is the game's Garlic Necklace (row 135), darker
        (GEAR_NECKLACE, "Garlic Jr.'s Necklace", "Garlic Jr. wore it under the Makyo Star. Raises your Endurance and Ki.", 135, 3, (0, 12, 12, 12, 0), 0, 280))
GEAR_TABLE, GEAR_COUNT = 0x6F82EC, 162
GEAR_REFS = (0x2BFC, 0x453C, 0x4814, 0xD528, 0x13E28, 0x16FBC, 0x1D400, 0x1D5F0, 0x1D968, 0x1DC74, 0x1DF88, 0x1FB4C, 0x2BD44, 0x31844, 0x31C3C, 0x321B8, 0x325AC)
ROSHI_NAME_UI = GT_NAME_UI + 4   # 'Master Roshi', 'Max Power Roshi' (forms.json uses these numbers)
SSG_NAME_UI = ROSHI_NAME_UI + 2  # 'Super Saiyan God'
FP_NAME_UI = SSG_NAME_UI + 1     # 'Full Power Gohan'
TEEN_NAME_UI = FP_NAME_UI + 3    # 'Teen Gohan' (after Majuub's name and text; forms.json uses this number)
# Kaioken: each base look that can use it -> (its form, owner, the actor its red copy is made from). Goku's three, Kid Goku's, and the humans'.
KAIOKEN = {'goku': (0, 0, 106), 'goku_b': (1, 0, 107), 'goku_halo': (2, 0, 108), 'kid_goku': ('kid_goku', 0, 'kid_goku'),
           'goku_ss': (3, 0, 109), 'goku_ss_b': (4, 0, 110), 'kid_goku_ssj': ('kid_goku_ssj', 0, 'kid_goku_ssj'),      # Super Saiyan Kaioken (Kaioken fully mastered)
           'krillin': ('krillin', 8, 'krillin'), 'tien': ('tien', 8, 'tien_player'), 'yamcha': ('yamcha', 8, 'yamcha_player'),
           'videl': ('videl', 8, 'videl_player'), 'hercule': ('hercule', 8, 'hercule_player')}
SS_KAIOKEN = ('goku_ss', 'goku_ss_b', 'kid_goku_ssj')     # their rows go after Blue's, so the forms that were already there keep their numbers
# Super Saiyan God: each of Goku's base looks -> (its form, owner, the actor its red-haired copy is made from). Rows after Super Saiyan Kaioken's.
SSG_LOOKS = {'goku_ssg': (0, 0, 106), 'goku_b_ssg': (1, 0, 107), 'goku_halo_ssg': (2, 0, 108)}
SSG_HAIR = ((120, 32, 64), (200, 32, 64))         # his hair: edge and fill (crimson, from colours the game has)
# Nov 11 (the owner, 19:26 and 19:49): Super Saiyan God's eyes red as his hair; Super Saiyan Blue's pupils and brows the hair's blues, a
# light cyan aura (Super Saiyan's gold shade for shade, SSB_AURA), and Super Saiyan 2's bolts toned down in Blue's colours (SSB_BOLTS,
# outfit.c crackle). Built with BFU_LOOK170=1 until the owner approves the preview.
LOOK170 = os.environ.get('BFU_LOOK170', '1') != '0'      # on since the owner's pick of the glow (Nov 12, 19:04); BFU_LOOK170=0 builds without
GLOW_STYLE = os.environ.get('BFU_GLOW', '1c')       # Blue's glow (lib/ssb_glow.py STYLES): the owner's pick (Nov 12, 19:04: "1c looks good use that")
GLOW_ALPHA = (6, 10)
GLOW_MORE = os.environ.get('BFU_GLOW_MORE', '1') != '0'      # the glow in Super Saiyan God's reds and Rose's pinks too (owner, Nov 12 19:35 drafts, 19:42: "Auras all look good to lock in")
CELL_BEAM = os.environ.get('BFU_CELL_BEAM', '0') != '0'      # Perfect Cell fires in LoG2's firing frames, not his idle (Nov 12, the owner's preview: off until he OKs it)
# Each kind's colours for lib/ssb_glow.py's shades (its COLOURS keys, dark to light: 11 1 6 2 13 5 3 12 4; 14 the band): 0 Blue (ssb_glow's
# own), 1 Super Saiyan God (crimson to orange, a gold-white core), 2 Rose (magenta to pink, as Rose's power-up aura). Nearest palette entries.
GLOW_KINDS = (None,
              {11: (136, 16, 24), 1: (200, 32, 32), 6: (232, 64, 40), 2: (248, 104, 56), 13: (248, 136, 80), 5: (248, 176, 112), 3: (248, 216, 168),
               12: (248, 232, 200), 4: (248, 248, 248), 14: (248, 96, 48)},
              {11: (120, 16, 88), 1: (192, 40, 136), 6: (224, 64, 168), 2: (248, 104, 200), 13: (248, 136, 216), 5: (248, 176, 232), 3: (248, 208, 240),
               12: (248, 232, 248), 4: (248, 248, 248), 14: (248, 104, 200)},
              # 3 Full Power Mystic (the owner, 20:48: "Add that to mystic gohan full power too"): silver-white with a cool blue, as his
              # white lightning and Max Power's white aura (FP_BOLTS)
              {11: (104, 120, 168), 1: (168, 184, 224), 6: (192, 208, 240), 2: (216, 224, 248), 13: (224, 232, 248), 5: (232, 240, 248),
               3: (240, 244, 248), 12: (248, 248, 248), 4: (248, 248, 248), 14: (208, 216, 248)})                                # 1c's see-through band: 6/16 of it over 10/16 of the stage (outfit.c GLOW_ALPHA)
SSB_AURA = {(248, 168, 0): (48, 176, 232), (248, 208, 0): (96, 232, 248), (248, 248, 0): (160, 248, 248), (248, 248, 144): (208, 248, 248), (248, 248, 216): (232, 248, 248)}
SSB_BOLTS = ((32, 128, 248), (200, 248, 248))     # glow, core
# Full Power Mystic: Gohan's orange-gi form -> (its form, owner, its figure: the orange gi's). Rows after Super Saiyan God's.
FP_LOOKS = {'gohan_mystic_fp': (13, 1, 101)}
FP_BOLTS = ((176, 200, 248), (248, 248, 248))     # the crackle's lightning: a cool white fade and a white core (Max Power's aura is the same white)
# Super Saiyan Blue for Goku and Vegeta (post-game mastery): each Super Saiyan form -> its Blue, a Super Saiyan 3 class copy whose hair is blue.
SSB_LOOKS = {'goku_ssb': (3, 5, 0, 109, 0), 'goku_ssb_b': (4, 6, 0, 110, 2), 'vegeta_ssb': (28, 5, 4, 273, 26), 'vegeta_ssb_b': (29, 5, 4, 274, 27),
             'vegeta_armor_ssb': ('vegeta_armor_ss', 5, 4, 'vegeta_armor_ss', 'vegeta_armor')}     # name: (its Super Saiyan form, row copied, owner, actor, base form)
SSB_FORMS = tuple((v[0], k) for k, v in SSB_LOOKS.items())
# Blue's change (lib/sprites.py change_slot): name -> (the base form whose figure's change it takes, its frames, the black-haired frame)
_SSB_SEQ = [2, 2, 3, 4, 5, 6, 7, 8, 9, 9, 'stance']
SSB_CHANGE = {'goku_ssb': (0, _SSB_SEQ, 1), 'goku_ssb_b': (2, _SSB_SEQ, 1), 'vegeta_ssb': (26, _SSB_SEQ, 1), 'vegeta_ssb_b': (27, _SSB_SEQ, 1),
              'vegeta_armor_ssb': ('vegeta_armor', [6, 7, 8, 9, 10, 6, 7, 8, 9, 10, 'stance'], 0)}     # (LoG2's change: black 0-2, gold 6-10)
# The blue: Super Saiyan's hair ramp (BF indices) -> DBS Gogeta's Blue tones (gogeta.py's sheet, flattened), lightest as his lightest
SSB_HAIR = {16: (24, 64, 160), 202: (24, 128, 240), 201: (69, 199, 246), 28: (86, 246, 246), 29: (200, 248, 248), 2: (200, 248, 248),
            246: (200, 248, 248)}     # (246: Vegeta's palest gold, Nov 10: it stayed yellow)
KAIOKEN_TINT = 0.3                  # how far each colour goes towards red (outlines stay)


BOLT_PIECE = 16                     # a crackle bolt's sprite piece (outfit.c BOLT_BYTES is its square)


def crackle_frames(seed, glow, core):
    """One bolt of the crackle (outfit.c crackle) as four 32x32 frames of colour indices: it strikes (the top half), stands with a little
    branch, jumps a pixel, then breaks up in the fade colour. A one-pixel core with a one-pixel edge on one side (Nov 9, the owner: "a bit
    too much lightning and too thick"), a short zigzag about the frame's middle."""
    import random
    rng = random.Random(seed)
    def path(x, y, n):
        pts = [(x, y)]
        for _ in range(n):
            dx, dy = rng.choice((-2, -1, 1, 2)), rng.choice((2, 2, 3))
            for _ in range(dy): y += 1; pts.append((x, y))
            for _ in range(abs(dx)):
                x = max(3, min(28, x + (1 if dx > 0 else -1))); pts.append((x, y))
        return [(a, b) for a, b in pts if b < 31]
    main = path(rng.randint(14, 17), 9, 5)                   # about 12 px tall
    k = len(main) // 2
    branch = path(main[k][0], main[k][1], 1)
    jit = [(min(28, max(3, x + (1 if (y // 4) % 2 else -1))), y) for x, y in main]
    def draw(*lines, colour=core, broken=False):
        img = np.zeros((32, 32), np.uint8)
        for line in lines:                                   # a one-pixel edge in the fade colour on one side only
            for x, y in line:
                if not (broken and (y // 2) % 2) and img[y, x + 1] == 0: img[y, x + 1] = glow
        for line in lines:
            for x, y in line:
                if not (broken and (y // 2) % 2): img[y, x] = colour
        return img
    return [draw(main[:len(main) // 2]), draw(main, branch), draw(jit), draw(jit, colour=glow, broken=True)]


def mystic_change(clean):
    """Full Power Mystic's change, as canvases for sprites.py (_change_canvases): see add_actors."""
    import ssb
    goku, school, gi = ssb.actor_frames(clean, 106), ssb.actor_frames(clean, 98), ssb.actor_frames(clean, 101)
    head = school[10][0][1][:15].copy()
    hair = head[:8] != 0; head[:8][hair] = 1                       # his hair's brown flash (the change into gold) black: Mystic's stays black
    dark = np.arange(256, dtype=np.uint8)                           # Goku's blue undershirt and boots -> the orange gi's black ones (actor
    for k, v in {157: 111, 159: 112, 161: 1, 165: 111, 80: 111, 81: 112}.items(): dark[k] = v    # 101: its belt and wristbands stay blue)
    out = []
    for k in _SSB_SEQ[:-1]:
        c = goku[10][0][k].copy(); c[:15] = 0
        c[:15][head != 0] = head[head != 0]
        c[15:18] = dark[c[15:18]]; c[26:] = dark[c[26:]]
        out.append(c)
    out.append(gi[0][0][0])
    return [out, out, out]


def kaioken_rows(clean):
    """Kaioken's forms: the base row's copy with the red actor, in the Super Saiyan class (drain, +5) with no form above, back down to the base.
    Then Super Saiyan Blue's: Super Saiyan 3's row (its class: the orange pool, +15) with the blue actor, the owner's portraits, down to base."""
    kk = lambda n, base, owner: {'id': n + '_kaioken', 'copy': base, 'actor': n + '_kaioken', 'owner': owner, 'flags': 0x51, 'up': 255, 'down': base}
    rows = [kk(n, base, owner) for n, (base, owner, _) in KAIOKEN.items() if n not in SS_KAIOKEN]
    for n, (ss, row, owner, _, base) in SSB_LOOKS.items():
        portraits = list(clean[FORMS + FORM_SIZE * (ss if isinstance(ss, int) else 28) + 0x10:][:6])
        rows.append({'id': n, 'copy': row, 'actor': n, 'owner': owner, 'name': 1057, 'portrait': portraits, 'up': 255, 'down': base})
    rows += [kk(n, *KAIOKEN[n][:2]) for n in SS_KAIOKEN]
    # Super Saiyan God: the base row's copy with the red-haired actor, Super Saiyan's class (its drain, halved in outfit.c), back down to base
    rows += [{'id': n, 'copy': base, 'actor': n, 'owner': owner, 'flags': 0x51, 'up': 255, 'down': base, 'name': SSG_NAME_UI}
             for n, (base, owner, _) in SSG_LOOKS.items()]
    # Full Power Mystic: the orange gi's row copied, Super Saiyan's class (its drain, halved in outfit.c, and +5 taken off there), back down to it
    rows += [{'id': n, 'copy': base, 'actor': n, 'owner': owner, 'flags': 0x51, 'up': 255, 'down': base, 'name': FP_NAME_UI}
             for n, (base, owner, _) in FP_LOOKS.items()]
    # the shelved Great Ape's forms: each a copy of the look it changed from (see SHELVED_FORMS), changing no further
    return rows + [{'id': 'shelved_ape_' + n, 'copy': n, 'actor': n, 'owner': 0 if n == 'kid_goku' else 4, 'up': 255, 'down': n} for n in SHELVED_FORMS]


# The beam's body rows (the Kamehameha's, and every beam built on it): levels 1-2 point at 0x721188 and level 3 at 0x7211F4, nine rows on.
# The engine's shimmer for levels 1-2 runs on past their nine rows into level 3's three (rows 9-11), so it is one 12-row block. Copying nine
# rows per level put the next copy (the beam's head pieces) in rows 9-11: the Galick Gun drew a row of round heads along its body every
# other frame (Nov 9, the owner: "galick gun sprite is messed up"; the Special Beam Cannon and Black's Kamehameha had it too).
BEAM_BODY = (0x721188, 12)


def region_rows(clean, out, remap, put, cache, size_of=lambda o, k: o[k + 2] * o[k + 3], lo=None, hi=None):
    """Recolour the tiles of a set of frame rows (`out`, 12 bytes a row, the tile pointer at +8) as ONE copy of the whole span they cover,
    every row pointing at the same offset in it as in the game's own data. The game loads a beam's tiles as one block and finds a frame's
    by its offset from the first: copies made a block at a time (and a block at the first size seen: 0x08719E68 is used as 64, 128 and
    256 bytes) put other frames' tiles in those places, and the Galick Gun's, 10x's and Super Kamehameha's tubes came out as rounded pills
    with stray coloured squares (Nov 9, the owner: "fix every beam so they don't have that fucked up garbled texture"). `cache` holds the
    span copies of one recolouring; size_of(out, k) is a row's tile bytes (header layouts differ)."""
    rows = [(k, struct.unpack_from('<I', out, k + 8)[0]) for k in range(0, len(out) - 11, 12)]
    spans = [(t, size_of(out, k)) for k, t in rows if 0x08700000 <= t < 0x08800000 and size_of(out, k)]
    if not spans: return out
    a = lo if lo is not None else min(t for t, _ in spans)
    b = hi if hi is not None else max(t + n for t, n in spans)
    if (a, b) not in cache: cache[(a, b)] = put(bytes(clean[a - ROM_BASE:b - ROM_BASE]).translate(remap))
    for k, t in rows:
        if a <= t < b: struct.pack_into('<I', out, k + 8, cache[(a, b)] + t - a)
    return out


def body_block(frames):
    """frames(rom offset, rows) -> its recoloured copy; -> body pointer -> the same rows in one copy of the whole block."""
    at = frames(BEAM_BODY[0], BEAM_BODY[1])
    def body_at(body):
        o = body - ROM_BASE - BEAM_BODY[0]
        if not 0 <= o < 12 * BEAM_BODY[1] or o % 12: sys.exit('beam body rows moved: %X' % body)
        return at + o
    return body_at


def ssg_hair(one):
    """Goku's black hair -> Super Saiyan God's crimson. His hair is the only big black patch on him (eyes and brows are a few pixels each):
    every black area of 12 pixels or more, its edge darker. LOOK170: his eyes too, red as his hair (the pupil's black the edge's red,
    its grey middle the fill's): the black beside an eye's white, and the dark grey (113) between."""
    from scipy import ndimage
    edge, fill = one(np.array(SSG_HAIR[0])), one(np.array(SSG_HAIR[1]))
    cross = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    def fn(img):
        black = img == 1
        lab, n = ndimage.label(black, np.ones((3, 3)))
        sizes = ndimage.sum(black, lab, range(1, n + 1))
        hair = np.isin(lab, [k + 1 for k, v in enumerate(sizes) if v >= 12])
        inner = ndimage.binary_erosion(hair, np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
        out = img.copy(); out[hair] = edge; out[inner] = fill
        if LOOK170:
            mid = (img == 113) & ndimage.binary_dilation(img == 2, cross)
            out[(img == 1) & ~hair & ndimage.binary_dilation((img == 2) | mid, cross)] = edge; out[mid] = fill
        return out
    return fn


def kaioken_remap(pal, one):
    def colour(v):
        if v == 0: return 0
        r, g, b = (int(c) for c in pal[v])
        if max(r, g, b) < 48: return v
        a = KAIOKEN_TINT
        return one(np.array((r * (1 - a) + 248 * a, g * (1 - a) * 0.75, b * (1 - a) * 0.75)))
    return bytes(colour(v) for v in range(256))


# The skill book (outfit.c): per party character, the skills the loadout can hold beyond the six slots (record +0x13 is not a seventh: it is the equipment flags byte). 21 is the story's locked Super Saiyan.
DRAGON_FIST_TEXT = 'Hold the B Button to make a giant dragon of energy; steer its head with the +Control Pad and release to bite. Goku: as a Super Saiyan 3.'
SUPER_KAME_USES = 100               # Kamehameha uses at its top level (and after the ending) to master it into the Super Kamehameha
MASTERY_L2, MASTERY_L3 = 100, 250   # a transformation's mastery units (outfit.c ss_tick / ssj4_refill) for its Level 2 and 3
# (literal ids: test_build.py reads this with ast.literal_eval; 47 is FP_SKILL. Goku's 5, Dragon Fist Explosion as a Super Saiyan 3, fills his
# sixteenth and last place: the known-skills word has 16 bits.)
# (Nov 12: Goku's fourteenth place, the story's locked Super Saiyan (21), is the Potara (50) now: 21 is held only while the story locks his
# Super Saiyan and the story swaps it back itself; outfit.c skills_swap keeps it in its slot. A book has 24 places since: the record's 16
# known bits, then 8 more per character in the bench (outfit.c KNOWN2): Goku's Fusion Dance (12) is his seventeenth.)
BOOK_PLACES = 24
SKILL_BOOK = {0: (7, 15, 43, 14, 20, 35, 22, 36, 44, 37, 19, 39, 41, 50, 46, 5, 12), 1: (7, 20, 35, 6, 17, 18, 26, 21, 47), 2: (7, 20, 16, 8, 12, 21),
              3: (7, 20, 35, 4, 11, 12, 21), 4: (7, 20, 35, 36, 44, 10, 2, 38, 40, 21, 50, 12), 5: (7, 20, 22, 13, 23, 21), 6: (7, 20, 35, 1, 9, 21),
              7: (7, 3, 5, 20, 44)}
# A move's level by the character's level (Player_GetLevel, 50-200), as the level-up script 0x0877C9E8 grants them: (character, skill,
# level for Level 2 or 0 = from the start (a story grant), level for Level 3). The new beams follow the move they're built on.
LEVEL_STEPS = ((0, 14, 75, 125), (0, 15, 100, 150), (0, 43, 100, 150), (0, 39, 100, 150), (1, 17, 75, 125), (1, 6, 100, 150), (2, 16, 100, 150),
               (2, 8, 0, 125), (3, 4, 75, 125), (3, 11, 100, 150), (4, 10, 100, 150), (4, 2, 0, 125), (4, 38, 100, 150), (4, 40, 100, 150))
KAME_VARIANTS = (   # name, skill, strength x, beam colours (Kamehameha's two ramps, as KAME_TINT), title, text
    ('galick', GALICK_SKILL, 1.0, {2: (240, 236, 255), 76: (200, 184, 255), 195: (160, 128, 248), 75: (112, 72, 224), 74: (48, 24, 128),
                                    30: (240, 236, 255), 29: (216, 208, 255), 28: (184, 160, 255), 5: (160, 128, 248), 27: (136, 96, 240), 110: (112, 72, 224), 109: (80, 48, 176), 4: (48, 24, 128)},
     'Galick Gun', 'Hold the B Button to gather energy in both hands, then release a long violet beam.'),
    ('tenx', TENX_SKILL, 1.5, {2: (255, 240, 232), 76: (255, 184, 168), 195: (248, 104, 80), 75: (208, 32, 24), 74: (112, 0, 0),
                                30: (255, 240, 232), 29: (255, 208, 192), 28: (255, 160, 136), 5: (248, 104, 80), 27: (232, 64, 48), 110: (208, 32, 24), 109: (160, 8, 8), 4: (112, 0, 0)},
     '10x Kamehameha', 'Super Saiyan 4 only. Hold the B Button to emit a huge red Kamehameha, 1.5x as strong.'),
    ('superkame', SUPER_KAME_SKILL, 1.4, {2: (255, 255, 255), 76: (224, 248, 255), 195: (152, 232, 255), 75: (64, 184, 248), 74: (24, 96, 200),
                                           30: (255, 255, 255), 29: (232, 248, 255), 28: (192, 240, 255), 5: (152, 232, 255), 27: (104, 208, 255), 110: (64, 184, 248), 109: (40, 136, 224), 4: (24, 96, 200)},
     'Super Kamehameha', 'A mastered Kamehameha. Hold the B Button to emit a brighter, wider beam, 1.4x as strong.'),
)
BLACK_PORTRAIT = 166             # speaker ids: Goku Black, then Rose
# The Kamehameha's colours, by brightness: a cyan set (levels 1-2) and a gold set (level 3). Black's ki is dark purple and Rose's pink.
KAME_TINT = {'black': {2: (240, 208, 248), 76: (216, 144, 240), 195: (176, 80, 224), 75: (120, 32, 176), 74: (56, 0, 88),
                       30: (240, 208, 248), 29: (224, 168, 248), 28: (208, 128, 240), 5: (176, 80, 224), 27: (144, 48, 200), 110: (120, 32, 176), 109: (88, 16, 136), 4: (56, 0, 88)},
             'rose': {2: (255, 232, 248), 76: (248, 184, 232), 195: (240, 136, 216), 75: (224, 64, 192), 74: (144, 0, 120),
                      30: (255, 232, 248), 29: (248, 200, 240), 28: (248, 168, 232), 5: (240, 136, 216), 27: (232, 104, 208), 110: (224, 64, 192), 109: (184, 24, 160), 4: (144, 0, 120)}}
BLAST_HUE = {'black': 280, 'rose': 320}    # their ki blasts
# Strength against Big Bang per skill level: 2.5x and 2x in total damage. Each hit rounds down, which costs low levels more, so they get a bigger multiplier (measured on Android 13 at Power 80).
NEW_MOVES = (('eraser', ERASER_SKILL, (2.95, 2.85, 2.45), 'Eraser Cannon', 'Press the B Button and release to emit a large ball of green energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (0.2, 0.6, 1, 0, 0.15, 0.6)),
             ('bomber', BOMBER_SKILL, (2.4, 2.2, 2), 'SS Deadly Bomber', 'Press the B Button and release to emit a large ball of reddish pink energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (1, 0, 0.03, 0.55, 0.12, 0.45)),
             ('blitz', BLITZ_SKILL, (1, 1, 1), 'Power Blitz', 'Press the B Button and release to emit a large ball of golden energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (1, 0, 0.75, 0.1, 0.05, 0.3)),
             ('disc', DISC_SKILL, (2.4, 2.2, 2), 'Destructo Disc', 'Press the B Button and release to throw a spinning disc of energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (1, 0, 0.85, 0.15, 0.1, 0.8)))
SUPER_BLUE_SKILL = 44            # Super Saiyan Blue (Nov 9: its own row; retail stub 21 stays the story's locked Super Saiyan)
OLD_SUPER_BLUE = 21              # where it was before: saves holding it are moved on (outfit.c skills_sync)
BROLY_DEFEAT = 'assets/scripts/gUnknown_0879321C.evt'
FUSION_END = 'assets/scripts/gUnknown_0879A4CC.evt'     # global script 503: a fusion's time is up
DEBUG_NATIVE = 0xDB              # debug builds only: "save to slot 1". No script calls 0xDB (equipment uses 0xDF-0xE8 and 0xF5, the death script 0xF7)
OUT = os.environ.get('BFU_OUT', 'ultimate/out')
SAIYAMAN = [(10, 14), (15, 'saiyaman_from_green'), (13, 'saiyaman_from_orange'), ('gohan_gt', 'saiyaman_from_gt'), ('gohan_gt_noglasses', 'saiyaman_from_gt_ng'),
            ('gohan_armor', 'saiyaman_from_armor')]       # Nov 10: armour Gohan came back from the costume in the school uniform
ACTORS_FILE = 'assets/areas/a033_w01_01_Snakeway.actors'
INTRO = 'assets/scripts/gUnknown_0877CBF0.evt'
ENDING = 'assets/scripts/gUnknown_08796114.evt'
FIELD = 'assets/scripts/gUnknown_08780550.evt'


SKILL_ROWS, UI_TABLE = 0x71DAF8, 0x6BCE8
SKILLS, SPIRIT_SKILL, SPIRIT_NAME = 0x71DB04, 19, 1050      # UI 1050 and 1053 are unused text
UI = 'assets/text/ui_strings.txt'
ACTOR_BASE = 298


def new_actor_ids():
    """Ids add_actors will give: actors.json's new actors in order, then Super 13 and Android 13. Checked after the build."""
    cfg = json.load(open('ultimate/actors.json'))
    n = ACTOR_BASE + sum(1 for k, a in cfg.items() if not k.startswith('_') and 'replace' not in a and not a.get('last'))
    return {'super13': n, 'android13': n + 1, 'broly_fp': n + 2, 'gogeta_dbs': n + 3, 'gogeta_dbs_ss': n + 4, 'gogeta_ssb': n + 5, 'android13_player': n + 6, 'super13_player': n + 7, 'goku_ss2': n + 8, 'goku_ss2_b': n + 9, 'gohan_ss2': n + 10, 'gohan_green_ss2': n + 11, 'vegeta_ss2': n + 12, 'vegeta_ss2_b': n + 13, 'vegeta_armor_ss2': n + 14, 'gohan_armor_ss2': n + 15, 'trunks_ss2': n + 16, 'trunks_armor_ss2': n + 17, 'vegito_ss2': n + 18, 'super17': n + 19, 'android13_absorb': n + 20, 'cell_imperfect': n + 21, 'cell_semi': n + 22, 'cell_perfect': n + 23, 'cell_junior': n + 24, **{'dragon_ball_%d' % (k + 1): n + 25 + k for k in range(7)}, 'goku_black': n + 32, 'goku_rose': n + 33, **{k: n + 34 + i for i, k in enumerate(gt.ACTORS)}, **{k: n + 34 + len(gt.ACTORS) + i for i, k in enumerate(garlic_art.ACTORS)}}


DEATH_SCRIPT = 'assets/scripts/gUnknown_0877C5A4.evt'
POPO_NPC = 'assets/scripts/gUnknown_08786E68.evt'   # Mr. Popo on the Lookout: after the ending, the Hyperbolic Time Chamber
HUB_NPC = 'assets/scripts/gUnknown_08783D30.evt'    # a Hercule City resident: post-game, the tournament official's Challenge Board
TOUR_NPC = 'assets/scripts/gUnknown_08785590.evt'   # the West City resident to the west
QUEST_NPC = 'assets/scripts/gUnknown_08785580.evt'   # the West City resident outside the Z-Mart
ROSHI_NPC = 'assets/scripts/gUnknown_08786C38.evt'   # Master Roshi on his island (5:1): after the ending he joins (Nov 9)


UI_EDITS = {1051: 'Press the B Button to transform into a Super Saiyan Blue. You must already be a Super Saiyan to use this technique.', 1052: 'Android 13', 1054: 'DBS Gogeta', 1055: 'SSB Gogeta', 1056: 'Super 13', 1057: 'Super Saiyan Blue'}


def form_row(name):
    rows = json.load(open('ultimate/forms.json'))['rows']
    return FORM_COUNT + [r['id'] for r in rows].index(name)


def broly_defeat(src):
    """Beating Broly in the story adds him to the party, and says so once the fight's closing scene has played."""
    head = '    call set_flag(111)\n'
    tail = '    call 0x7B(50)\n    call 0x33(0)\n    end\n'
    if src.count(head) != 1 or not src.endswith(tail):
        sys.exit('Broly defeat script changed')
    src = src.replace(head, head + '    pushn 8, %d\n    call 0x%X\n' % (form_row('broly'), JOIN_NATIVE))
    return src[:-len(tail)] + '''    call 0x7B(50)
    end
step 2 say 0x00 "Broly joins you! Pick him on the Switch Character menu."
step 3 code
    call 0x33(0)
    end
'''


def quest_npc(src):
    """The resident's list, with the Battle of Gods' scenes (ultimate/bog.py) and the Garlic Jr. quest's (ultimate/garlic.py) after it: step 1
    first asks whether you're at Capsule Corporation or in one of the movies' places (Whis, Beerus, King Kai and the party guests, Dende,
    Korin, Hercule, Garlic Jr. and his scene rooms all point at this list), and goes there."""
    import zone26, bog, garlic
    text = quest_npc_story(src)
    m = len(re.findall(r'(?m)^step ', text))                   # steps so far: the quests' are numbered on from here (counted from 0)
    rooms = zone26.garlic_rooms()
    chars = {k: v + 9 for k, v in new_actor_ids().items() if k in garlic_art.ACTORS}
    steps = bog.steps(zone26.MORE_GET, zone26.MORE_PUT) + garlic.steps(zone26.MORE_GET, zone26.MORE_PUT, rooms, chars)
    number = {n: m + k for k, (n, _) in enumerate(steps)}; number['END'] = m + len(steps)
    # The story steps end the list with `push m` (one past their last step). With the scenes appended that is the first scene,
    # so every such end now goes past the scenes instead: before Nov 9's fix, talking to the resident after the ending ran the
    # quest's dispatcher and he never sent you to Hercule City.
    ends = len(re.findall(r'\bpush %d\b' % m, text))
    text, n = re.subn(r'(?m)^(\s+)push %d\n(\s+)end$' % m, lambda q: '%spush %d\n%send' % (q.group(1), number['END'], q.group(2)), text)
    if n != ends or not n or number['END'] > 255: sys.exit("the resident's script ends its list in a way quest_npc doesn't know")
    get = lambda f: '    pushn %d\n    call 0x%X\n' % (f, zone26.MORE_GET)
    here = [bog.CAPSULE, bog.KAI]                               # the quest's people stand at Capsule Corporation and on Grand Kai's Planet
    branch = ''.join(get(bog.Q_AREA) + '    pushn %d\n    eq\n    jz G%d\n    push %d\n    end\nG%d:\n' % (a << 8 | w, k, number['bog'], k) for k, (w, a) in enumerate(here))
    branch += ''.join(get(garlic.Q_AREA) + '    pushn %d\n    eq\n    jz Q%d\n    push %d\n    end\nQ%d:\n' % (a << 8 | w, k, number['garlic'], k)
                      for k, (w, a) in enumerate(garlic.places(rooms)))
    if text.count('step 1 code\n') != 1: sys.exit("the resident's script changed")
    text = text.replace('step 1 code\n', 'step 1 code\n' + branch, 1)
    return text.rstrip() + '\n' + ''.join('step auto %s' % re.sub(r'\{(\w+)\}', lambda q: str(number[q.group(1)]), t) for _, t in steps)


def quest_npc_story(src):
    """Post-game, this resident sends you to Zone 26, and rewards you once Super 13 is beaten (his death script runs this list).
    The last two steps are the door of the fight for anyone but Goku (Nov 11, the owner: "make the Super 13 fight specifically only
    startable and maybe only playable as Goku"; its finish is his Spirit Bomb): zone26.py's trigger at the door runs this list, step 1
    sees the area, and Goku is made to play (any fusion ended first, more_get(250)) and taken in. The finish ends a fusion too, before
    it makes Goku play: one danced mid-fight left Goku and Vegeta out of the party for good ("just in case": the Fusion Dance can't be
    used in the fight now, outfit.c fusion_can).
    A step's `push N` jumps to the Nth step counting from 0, the same number the following step's position gets; past the last step ends the list."""
    import zone26
    head, old = src.split('step 1 say', 1)
    ids = new_actor_ids(); super13 = ids['super13'] + 9; absorb = ids['android13_absorb'] + 9
    door = '    pushn 251\n    call 0x%X\n    pushn %d\n    eq\n    jz L9\n    push 25\n    end\nL9:\n' % (zone26.MORE_GET, zone26.S13_DOOR[1] << 8 | zone26.S13_DOOR[0])
    return head + 'step 1 code\n' + door + '''    pushn 888
    call flag
    pushn 887
    call not_flag
    and
    jz L8
    push 22
    end
L8:
    pushn 881
    call flag
    pushn 884
    call not_flag
    and
    jz L4
    push 13
    end
L4:
    pushn 886
    call flag
    pushn 882
    call not_flag
    and
    jz L5
    push 16
    end
L5:
    pushn 883
    call flag
    jz L1
    push 11
    end
L1:
    pushn 882
    call flag
    jz L2
    push 7
    end
L2:
    pushn 884
    call flag
    jz L7
    push 27
    end
L7:
    call flag(149)
    jz L3
    push 3
L3:
    end
step 2 say''' + old.rstrip() + '''
step auto code
    push 27
    end
step auto say 0x85 "Something's wrong past the Z-Mart. Dr. Gero's old computer has woken up!"
step auto say 0x85 "It built one last Android, up in the snow. Hurry!"
step auto code
    call 0x78(30)
    pushn 26, 1, 1, 128, 240
    call 0x77
    call 0x79(30)
    end
step auto code
    push 27
    end
step auto say 0x85 "The signal stopped! You beat Super 13!"
step auto say 0x85 "And you've made new allies out there! See the Switch Character menu."
step auto say 0x85 "And Goku, you learned the Spirit Bomb! Press L to select it."
step auto code
    pushn 883
    call set_flag
    pushn 0, 19
    call 0xA4
    pushn 1, 26
    call 0xA4
    pushn 876
    call set_flag
    pushn 877
    call set_flag
    pushn 880
    call set_flag
    pushn 8, %d
    call 0x%X
    push 27
    end
step auto say 0x85 "Want a real fight? Hercule City has a Challenge Board now. Ask the tournament official!"
step auto code
    push 27
    end
step auto code
    pushn %d, 120, 214
    call 0x35
    end
step auto say 0x00 "Android 13 pulls in the broken parts of 14 and 15!"
step auto code
    pushn 884
    call set_flag
    call play_sfx(24)
    call wait(120)
    call 0x7A(6)
    call 0x7B(6)
    call 0x7A(6)
    call 0x7B(6)
    call 0x7A(24)
    pushn %d, 120, 214
    call 0x35
    pushn %d, 17, 0
    call 0x51
    call 0x7B(40)
    call wait(50)
    pushn 5, 200, 200, 255, 10
    call 0x4C
    pushn %d, 20, 0
    call 0x51
    call wait(40)
    push 27
    end
step auto say 0x02 "He's still standing! I need everyone's energy!"
step auto code
    pushn 250
    call 0x%X
    jz L5
L5:
    call 0x95(0)
    pushn %d, 120, 214
    call 0x35
    pushn 100, 15
    call 0x2A
    push 120
    set 0x04
    push 250
    set 0x05
    push 6
    set 0x06
    call 0xFB(40)
    push 58
    loop_begin
L1:
    call 0x04
    call 0x05
    call 0x06
    call 0xF4(255)
    call 0xFB(1)
    inc 0x06
    dec 0x05
    call wait(2)
    loop L1
    end
step auto say 0x00 "Push the Spirit Bomb! Press the A Button fast!"
step auto code
    call 0xC6
    end
step auto code
    pushn 5, 200, 200, 255, 10
    call 0x4C
    push 40
    loop_begin
L1:
    call 0x04
    call 0x05
    call 0x06
    call 0xF4(255)
    call 0xFB(1)
    call wait(1)
    loop L1
    pushn %d, 9, 0
    call 0x51
    push 90
    loop_begin
L3:
    call 0x04
    call 0x05
    call 0x06
    call 0xF4(255)
    call 0xFB(1)
    call 0x19(10)
    push 0
    eq
    jz L4
    call play_sfx(24)
    pushn 5, 200, 200, 255, 10
    call 0x4C
L4:
    call wait(1)
    loop L3
    pushn %d, 16, 0
    call 0x51
    call play_sfx(24)
    call 0x7A(3)
    pushn 400, 400, 1
    call 0xF4(255)
    call 0x7B(10)
    call play_sfx(24)
    call 0x7A(3)
    call 0x7B(10)
    call 0x7A(4)
    call wait(20)
    call 0x7B(40)
    call wait(30)
    call 0xFB(0)
    pushn 882
    call set_flag
    call max_hp
    set hp
    call max_ki
    set ki
    call 0x78(60)
    pushn 4, 1, 1, 320, 392
    call 0x77
    call 0x79(30)
    call 0x2F
    call 0x33(0)
    end
step auto code
    push 27
    end
step auto say 0x85 "You beat all nine! Majin Buu, Super Janemba and Kid Buu join you. See Switch Character."
step auto code
    pushn 887
    call set_flag
    push 27
    end
step auto code
    end
step auto say 0x00 "Only Goku can win this fight. He steps in."
step auto code
    pushn 250
    call 0x%X
    jz L1
L1:
    call 0x95(0)
    call 0x78(20)
    pushn 884
    call flag
    pushn 886
    call not_flag
    and
    jz L2
    pushn 26, 17, 1, 120, 276
    jmp L3
L2:
    pushn 26, 15, 1, 120, 276
L3:
    call 0x77
    call 0x79(20)
    push 27
    end
''' % (form_row('android13'), JOIN_NATIVE, absorb, super13, super13, super13, zone26.MORE_GET, super13, super13, super13, zone26.MORE_GET)


def tournament_npc(src):
    """The West City resident who ran the World Tournament now sends you to Hercule City. A debug zone build also uses him as a test's way into that city."""
    head, old = src.split('step 1 say', 1)
    warp = '    call 0xCA\n    call 0x95\n    call 0xD8\n' if '--trailer' in sys.argv else '    pushn 3, 1, 1, 208, 134\n'     # a trailer build takes the room from RAM a filming script pokes
    hook = '    pushn 862\n    call flag\n    jz L0\n    call 0x78(30)\n' + warp + '    call 0x77\n    call 0x79(30)\n    push 4\n    end\nL0:\n' if '--zone' in sys.argv else ''
    credits = '''step 2 say 0x00 "Buu's Fury: Ultimate Edition\\nComing Soon"
step auto say 0x00 "An unofficial fan project. Dragon Ball Z and Buu's Fury belong to their owners."
step auto say 0x00 "Broly Full Power sprites by Azure-Oni, ripped by DBZdogs."
step auto say 0x00 "Gogeta sprites ripped by Mister Man, edited by Azure-Oni."
step auto code
    push 7
    end
''' if '--trailer' in sys.argv else None
    if credits:
        return head + 'step 1 code\n' + hook.replace('push 4', 'push 7') + """    pushn 883
    call flag
    jz L2
    push 5
    end
L2:
    end
""" + credits + """step auto say 0x5E "The World Tournament has moved to Hercule City. Ask the tournament official!"
step auto code
    end
"""
    return head + 'step 1 code\n' + hook + """    pushn 883
    call flag
    jz L2
    push 2
    end
L2:
    end
step 2 say""" + old.rstrip() + """
step auto say 0x5E "The World Tournament has moved to Hercule City. Ask the tournament official!"
step auto code
    end
"""


def death_script(src):
    """The game's death script: a lost Time Chamber fight rests you and goes back to the Lookout, the way the Lazarus Crystal revives you."""
    import zone26
    first = 'step 7 zcode'
    if first not in src: sys.exit('death script changed')
    head, rest = src.split(first, 1)
    line, body = rest.split('\n', 1)
    home = zone26.spar_off() + '    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n    call 0x78(30)\n    pushn 6, 1, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    push 4\n    end\n' % zone26.SPAR_HOME     # steps count from 0 here: 4 is the list's end, while just `end` would run on into the next step and the game over
    new = '    pushn %d\n    call flag\n    pushn %d\n    call flag\n    and\n    jz L9\n' % zone26.CELL_COUNT + home + 'L9:\n'
    import bog, garlic
    gods = bog.death_branch(zone26.MORE_PUT, zone26.MORE_GET)       # a Beerus fight lost: the story goes on
    gods = garlic.death_branch(zone26.MORE_PUT, zone26.MORE_GET) + gods    # a Garlic Jr. quest fight lost: back to the Lookout or the main street
    endless = gods + '    pushn 1\n    call 0x%X\n    jz L8\n    pushn 3\n    call 0x%X\n    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n    call 0x78(30)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    push 4\n    end\nL8:\n' % (zone26.LADDER, zone26.LADDER)
    return head + first + line + '\n' + endless + new + body


def symbol_items_icon(item):
    """Where the item's menu icon is in the base ROM (items.csv names it)."""
    import csv
    rows = list(csv.reader(open('assets/tables/items.csv', encoding='latin1')))
    head = next(r for r in rows if r and r[0] == 'index')
    row = next(r for r in rows if r and r[0] == str(item))
    return int(row[head.index('icon')].split('_')[1], 16) - ROM_BASE


def popo_npc(src):
    """After the ending Mr. Popo opens the Hyperbolic Time Chamber: a category, then a partner, up to four to a page. Before it he says what he always said."""
    import zone26
    speaker = 0x63
    steps = []
    def say(name, text):
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, text      # long lines reset the game; 64-67 look like ROM pointers to the shifter
        steps.append((name, 'say 0x%02X "%s"\n' % (speaker, text)))
    def code(name, text): steps.append((name, 'code\n' + text))
    def choose(name, targets):
        code(name, ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    push {%s}\n    end\nL%d:\n' % (k, k + 1, t, k + 1) for k, t in enumerate(targets)) + '    push {END}\n    end\n')
    say('hello', "The Hyperbolic Time Chamber is open. A day inside is a year outside. Train against who?")
    pages = zone26.SPAR
    say('menu1', '\\n'.join('- %s' % c for c, _ in pages[:3]) + '\\n- More')
    choose('menu1_go', ['cat0', 'cat1', 'cat2', 'menu2'])
    say('menu2', '\\n'.join('- %s' % c for c, _ in pages[3:]) + '\\n- Waves')
    choose('menu2_go', ['cat3', 'cat4', 'cat5', 'waves'])
    # Waves: a category's four in a row, no rest between. The first clear of each gives stat points.
    say('waves', "Waves: all four of a group in a row, no rest. Clear one the first time for %d stat points." % zone26.WAVE_POINTS)
    say('waves1', '\\n'.join('- %s' % c for c, _ in pages[:3]) + '\\n- More')
    choose('waves1_go', ['wave0', 'wave1', 'wave2', 'waves2'])
    say('waves2', '\\n'.join('- %s' % c for c, _ in pages[3:]) + '\\n- Back')
    choose('waves2_go', ['wave3', 'wave4', 'wave5', 'menu1'])
    for k, (c, people) in enumerate(pages):
        broly = any(p[0] == 'Broly' for p in people)
        gate, tail = ('    call flag(111)\n    jz L1\n', 'L1:\n    push {locked}\n    end\n') if broly else ('', '')
        code('wave%d' % k, gate + zone26.spar_on() + '    call 0x78(30)\n    pushn 26, %d, 1, 120, 150\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.challenge_room('wave%d' % k) + tail)
    room = zone26.spar_first()
    for c, (_, people) in enumerate(pages):
        say('cat%d' % c, '\\n'.join('- %s' % p[0] for p in people))
        choose('cat%d_go' % c, ['p%d' % (room + k) for k in range(len(people))])
        room += len(people)
    say('locked', "You have not met that one yet.")
    code('locked_end', '    push {END}\n    end\n')
    room = zone26.spar_first()
    for _, people in pages:
        for name, row, _ in people:
            gate = '    call flag(111)\n    jz L1\n' if name == 'Broly' else ''
            tail = 'L1:\n    push {locked}\n    end\n' if name == 'Broly' else ''
            code('p%d' % room, gate + zone26.spar_on() + '    call 0x78(30)\n    pushn 26, %d, 1, 120, 150\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % room + tail)
            room += 1
    # The Dragon Balls. A ball on the map starts this same list, so the first thing it does is ask where it is.
    balls = new_actor_ids()
    for k in range(7):
        steps.append(('ball%d' % k, 'say 0x00 "You found the %d-Star Dragon Ball!"\n' % (k + 1)))
        code('ball%d_go' % k, '    call 0x80(%d)\n    pushn %d, 0, 0\n    call 0x35\n    push {END}\n    end\n' % (zone26.BALL_ITEM + k, balls['dragon_ball_%d' % (k + 1)] + 9))
    steps.append(('summon', 'say 0x%02X "All seven Dragon Balls! Stand back. I will call the Eternal Dragon."\n' % speaker))
    code('summon_go', '    call music(40)\n    call play_sfx(23)\n    call 0x7A(20)\n    pushn 4, 20, 2, 120, 176\n    call load_scene\n    pushn 0, 228, 221\n    call 0x69\n    pushn 1, 244, 221\n    call 0x69\n    pushn 2, 220, 236\n    call 0x69\n    pushn 3, 236, 236\n    call 0x69\n    pushn 4, 252, 236\n    call 0x69\n    pushn 5, 228, 251\n    call 0x69\n    pushn 6, 244, 251\n    call 0x69\n    call 0x64(0)\n    call 0x64(1)\n    call 0x64(2)\n    call 0x64(3)\n    call 0x64(4)\n    call 0x64(5)\n    call 0x64(6)\n    call 0x7B(90)\n    end\n')
    dragon = 0x7A
    steps.append(('wish_say', 'say 0x%02X "You who have gathered the Dragon Balls, speak your wish!"\n' % dragon))
    steps.append(('wish', 'say 0x%02X "- Greater power\\n- Riches\\n- New fighters\\n- More"\n' % dragon))
    choose('wish_go', ['w_power', 'w_rich', 'w_fighters', 'wish2'])
    steps.append(('wish2', 'say 0x%02X "- Super Saiyan 2\\n- A legendary treasure\\n- Hidden potential\\n- More"\n' % dragon))     # Nov 9: more wishes
    choose('wish2_go', ['w_ss2', 'treasure', 'w_potential', 'wish3'])
    steps.append(('wish3', 'say 0x%02X "- Turn back time\\n- Back"\n' % dragon))
    choose('wish3_go', ['w_time', 'wish'])
    # New Game+ (outfit.c new_game_plus): the story from its opening (global script 38), with everything the party has
    steps.append(('w_time', 'say 0x%02X "Time turns back to the day Goku returned. You keep your strength, but your foes grow stronger!"\n' % dragon))
    code('w_time_go', ''.join('    call take_item(%d)\n' % (zone26.BALL_ITEM + k) for k in range(7)) + '    call 0x7A(30)\n    pushn 2\n    call 0x%X\n    call 0x95(0)\n    push {to_opening}\n    end\n' % zone26.WISH_NATIVE)
    if 'step 19 raw 7 00 50 05 78 08' not in open(INTRO).read(): sys.exit("the intro's jump to the opening changed")
    steps.append(('to_opening', 'raw 7 00 50 05 78 08\n'))      # as the intro's last step: a type 7 step goes on to another list, here the opening (0x08780550)
    steps.append(('treasure', 'say 0x%02X "- Potara Earrings\\n- Gravity Band\\n- King Kai\'s Shades\\n- Senzu Pouch"\n' % dragon))
    choose('treasure_go', ['w_gear%d' % k for k in range(4)])
    for k, row in enumerate((GEAR_POTARA, GEAR_GRAVITY, GEAR_SHADES, GEAR_POUCH)):
        code('w_gear%d' % k, '    call 0x93(%d)\n    push {done}\n    end\n' % row)
    code('w_potential', '    pushn 1\n    call 0x%X\n    push {done}\n    end\n' % zone26.WISH_NATIVE)
    code('w_power', '    pushn 0\n    call 0x%X\n    push {done}\n    end\n' % zone26.WISH_NATIVE)
    code('w_rich', '    pushn %d\n    call 0x%X\n    push {done}\n    end\n' % (zone26.BALL_ZENIE, zone26.ADD_ZENIE))
    code('w_fighters', '    pushn 887\n    call set_flag\n    push {done}\n    end\n')
    code('w_ss2', ''.join('    pushn %d\n    call set_flag\n' % (SS2_FLAG + k) for k in range(9)) + '    push {done}\n    end\n')
    steps.append(('done', 'say 0x%02X "It is done. Farewell!"\n' % dragon))
    code('wish_end', ''.join('    call take_item(%d)\n' % (zone26.BALL_ITEM + k) for k in range(7)) + '    call 0x7A(30)\n    pushn 6, 1, 1, %d, %d\n    call 0x77\n    call 0x7B(40)\n    push {END}\n    end\n' % zone26.SPAR_HOME)
    code('last', '    end\n')
    number = {n: k + 2 for k, (n, _) in enumerate(steps)}; number['END'] = len(steps) + 2      # counted from 0; the first two are his old line
    head, old = src.split('step 1 code', 1)
    if '    push 5\n' not in old or not old.rstrip().endswith('call 0x16\n    end'):
        sys.exit("Mr. Popo's script changed")
    old = old.replace('    push 5\n', '    push %d\n' % number['END']).rstrip()
    old = old[:-len('end')] + 'push %d\n    end\n' % number['END']
    first = ''.join('\n    call 0x%X\n    push %d\n    eq\n    jz B%d\n    push %d\n    end\nB%d:' % (zone26.BALL_NATIVE, k + 1, k, number['ball%d' % k], k) for k in range(7))
    all7 = ''.join('\n    call 0x7F(%d)%s' % (zone26.BALL_ITEM + k, '\n    and' if k else '') for k in range(7))
    first += all7 + '\n    jz A9\n    call flag(149)\n    jz A9\n    push %d\n    end\nA9:' % number['summon']
    first += '\n    call flag(149)\n    jz L9\n    push %d\n    end\nL9:' % number['hello']
    line, rest = old.split('\n', 1)
    return head + 'step 1 code' + line + first + '\n' + rest + ''.join('step auto %s' % re.sub(r'\{(\w+)\}', lambda m: str(number[m.group(1)]), t) for _, t in steps)


def roshi_npc(src):
    """Master Roshi, Kame House (5:1). The story's line stays as it was; after the ending he asks to come along, and joins the guest slot."""
    import zone26
    if 'step 1 code' not in src or '    push 4\n' not in src or 'step 3 code' not in src: sys.exit("Roshi's script changed")
    more = lambda n: '    pushn %d\n    call 0x%X\n' % (n, zone26.MORE_GET)
    put = lambda n, v: '    pushn %d, %d\n    call 0x%X\n' % (n, v, zone26.MORE_PUT)
    steps = [('ask', 'say 0x61 "Heh heh! You\'ve gotten strong. Mind if this old man tags along? I\'ve still got a trick or two!"\n'),
             ('join', 'code\n' + put(zone26.MORE_ROSHI, 1) + '    call 0x93(%d)\n    push {joined}\n    end\n' % GEAR_SHELL),     # and his old training shell
             ('joined', 'say 0x00 "Master Roshi joined you! Choose him in Switch Character."\n'),
             ('joined_end', 'code\n    push {END}\n    end\n'),
             ('ready', 'say 0x61 "Ready when you are! Just don\'t tell Chi-Chi I\'m out fighting!"\n'),
             ('ready_end', 'code\n    push {END}\n    end\n')]
    for _, t in steps:
        for m in re.finditer(r'say 0x\w+ "([^"]*)"', t):
            n = len(m.group(1)); assert n < 100 and not 64 <= n <= 67, m.group(1)
    number = {n: k + 3 for k, (n, _) in enumerate(steps)}; number['END'] = len(steps) + 3      # counted from 0; the first three are his story steps
    post = '    call flag(149)\n    jz R9\n' + more(zone26.MORE_ROSHI) + '    jz R8\n    push %d\n    end\nR8:\n    push %d\n    end\nR9:\n    push %d\n' % (number['ready'], number['ask'], number['END'])
    out = src.replace('L1:\n    push 4\n', 'L1:\n' + post, 1)
    if not out.rstrip().endswith('    call set_flag(42)\n    end'): sys.exit("Roshi's script changed")
    out = out.rstrip()[:-len('end')] + 'push %d\n    end\n' % number['END']        # the story line's last step stops there, not in the new ones
    return out + ''.join('step auto %s' % re.sub(r'\{(\w+)\}', lambda m: str(number[m.group(1)]), t) for _, t in steps)


def hub_npc(src):
    """Hercule City's tournament official (character 192, speaker 0x62), once Super 13 is beaten: the Challenge Board. Before that his list is the resident's old line."""
    import zone26
    head, old = src.split('step 1 say', 1)
    speaker = 0x62
    steps = []                                 # (name, text of the step); a {name} in the text becomes that step's number
    def say(name, text):
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, text      # long lines reset the game; 64-67 look like ROM pointers to the shifter
        steps.append((name, 'say 0x%02X "%s"\n' % (speaker, text)))
    def code(name, text): steps.append((name, 'code\n' + text))
    trials = zone26.TRIALS
    won = lambda k: zone26.TRIAL_WON + k
    paid = lambda k: zone26.TRIAL_PAID + k
    picker_first = '    call 0x8D\n    call 0x%X\n    push {END}\n    end\n' % DEBUG_NATIVE if os.environ.get('BFU_SLOT_TEST') else ''   # test_slots.py: open Switch Character and save here
    if os.environ.get('BFU_HUB_EVENT'): picker_first = '    pushn %s, 0, 0\n    call run_event\n    push {END}\n    end\n' % os.environ['BFU_HUB_EVENT']     # a test plays one of the game's scripts by talking to the official
    if os.environ.get('BFU_HUB_WARP'): picker_first = '    pushn %s\n    call 0x77\n    push {END}\n    end\n' % os.environ['BFU_HUB_WARP']     # a test goes straight to a room by talking to the official
    more = lambda n: '    pushn %d\n    call 0x%X\n' % (n, zone26.MORE_GET)
    put = lambda n, v: '    pushn %d, %d\n    call 0x%X\n' % (n, v, zone26.MORE_PUT)
    lad = lambda op: '    pushn %d\n    call 0x%X\n' % (op, zone26.LADDER)
    def pending(test, name, lab): return test + '    jz %s\n    push {%s}\n    end\n%s:\n' % (lab, name, lab)
    museum_done = '    pushn 341, 5\n    call 0xBA\n    push 25\n    eq\n    pushn 346, 4\n    call 0xBA\n    push 15\n    eq\n    and\n'
    race_won = '    call 0x7F(61)\n    pushn 234\n    call flag\n    or\n'
    start = picker_first + """    pushn 883
    call not_flag
    jz L0
    end
L0:
""" + pending(more(zone26.MORE_RANK_NEW), 'rank', 'P1') + pending(more(zone26.MORE_ENDLESS_NEW), 'endless_done', 'P2') + pending(more(zone26.MORE_HARD) + more(zone26.MORE_HARD_PAID) + '    push 0\n    eq\n    and\n', 'hard_won', 'P3') + pending(more(zone26.MORE_HERC_WON) + more(zone26.MORE_HERCULE) + '    push 0\n    eq\n    and\n', 'herc_won', 'P4') + pending(more(zone26.MORE_BLACK_WON), 'black_won', 'P7') + pending(more(zone26.MORE_LEDGIC_WON), 'ledgic_won', 'P8') + pending(more(zone26.MORE_UUB_WON), 'uub_won', 'P9') + pending(race_won + more(zone26.MORE_RACE) + '    push 0\n    eq\n    and\n', 'race_won', 'P5') + pending(museum_done + more(zone26.MORE_MUSEUM) + '    push 0\n    eq\n    and\n', 'museum_won', 'P6') + """
    pushn 889
    call flag
    pushn 890
    call not_flag
    and
    jz L1
    push {tour_won}
    end
L1:
    pushn 888
    call flag
    pushn 887
    call not_flag
    and
    jz L2
    push {rush_won}
    end
L2:
    pushn %d
    call flag
    pushn %d
    call not_flag
    and
    jz C1
    push {cell_won}
    end
C1:
""" % (zone26.CELL_WON, zone26.CELL_PAID)
    for k in range(len(trials)):
        start += '    pushn %d\n    call flag\n    pushn %d\n    call not_flag\n    and\n    jz T%d\n    push {trial%d}\n    end\nT%d:\n' % (won(k), paid(k), k, k, k)
    allpaid = ''.join('    pushn %d\n    call flag\n%s' % (paid(k), '    and\n' if k else '') for k in range(len(trials)))
    start += allpaid + '    pushn %d\n    call not_flag\n    and\n    jz L3\n    push {all_won}\n    end\nL3:\n' % zone26.TRIAL_ALL
    for k in range(len(zone26.TRIALS2)):          # Trials II: won and not yet paid
        start += more(zone26.MORE_T2_WON + k) + more(zone26.MORE_T2_PAID + k) + '    push 0\n    eq\n    and\n    jz U%d\n    push {trial2_%d}\n    end\nU%d:\n' % (k, k, k)
    start += ''.join(more(zone26.MORE_T2_PAID + k) + ('    and\n' if k else '') for k in range(len(zone26.TRIALS2))) + more(zone26.MORE_T2_ALL) + '    push 0\n    eq\n    and\n    jz U9\n    push {all2_won}\n    end\nU9:\n    push {board}\n    end\n'
    code('start', start)
    steps.append(('old', 'say' + old.rstrip() + '\n'))
    code('after_old', '    push {END}\n    end\n')
    say('board', "Welcome to the Challenge Board! Pick your challenge!")
    say('menu', "- Boss Rush\\n- World Tournament\\n- Trials\\n- More")
    code('menu_go', """    call 0x18
    push 0
    eq
    jz L1
    push {rush}
    end
L1:
    call 0x18
    push 1
    eq
    jz L2
    push {bracket}
    end
L2:
    call 0x18
    push 2
    eq
    jz L3
    push {trials}
    end
L3:
    call 0x18
    push 3
    eq
    jz L4
    push {more}
    end
L4:
    push {END}
    end
""")
    say('rush', "Boss Rush! Nine bosses, one health bar. Good luck!")
    code('rush_go', """    call 0x78(30)
    pushn 26, %d, 1, 120, 276
    call 0x77
    call 0x79(30)
    push {END}
    end
""" % zone26.RUSH_FIRST)
    code('bracket', '    pushn 890\n    call flag\n    jz L1\n    push {tier}\n    end\nL1:\n' + put(zone26.MORE_TIER, 0) + '    push {mode}\n    end\n')
    say('tier', "- Normal bracket\\n- Hard bracket\\n- Endless\\n- Not now")
    code('tier_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n' + put(zone26.MORE_TIER, 0) + '    push {mode}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n' + put(zone26.MORE_TIER, 1) + '    push {mode}\n    end\nL2:\n    call 0x18\n    push 2\n    eq\n    jz L3\n' + more(zone26.MORE_HARD) + '    jz L4\n    push {endless}\n    end\nL4:\n    push {locked}\n    end\nL3:\n    push {END}\n    end\n')
    say('locked', "Win the Hard bracket first and Endless opens up.")
    code('locked_go', '    push {END}\n    end\n')
    say('endless', "Endless! Fight until you fall. Every win pays more, and you keep it all.")
    code('endless_go', '    call 0x78(30)\n    push 26\n' + lad(0) + '    pushn 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n')
    steps.append(('endless_done', 'saycode 0x%02X "That run: %%d wins. Your best: %%d."\n' % speaker + lad(4) + lad(5) + '    end\n'))
    code('endless_done_go', put(zone26.MORE_ENDLESS_NEW, 0) + '    push {start}\n    end\n')
    say('hard_won', "Hard bracket cleared! 300,000 Zenie, Endless is open, and Pikkon and Piccolo join you.")
    code('hard_won_go', put(zone26.MORE_HARD_PAID, 1) + put(zone26.MORE_PIKKON, 1) + '    push {start}\n    end\n')
    say('herc_won', "Hercule says he let you win, and he's joining your team to teach you more!")
    code('herc_won_go', put(zone26.MORE_HERCULE, 1) + '    push {start}\n    end\n')
    steps.append(('black_won', 'say 0x%02X "A mortal, beating a god? Very well. I will fight at your side, for now."\n' % (BLACK_PORTRAIT + 1)))
    code('black_won_go', put(zone26.MORE_BLACK, 1) + put(zone26.MORE_BLACK_WON, 0) + '    push {black_joins}\n    end\n')
    say('black_joins', "Goku Black joins you! See Switch Character.")
    code('black_joins_go', '    push {start}\n    end\n')
    say('ledgic_won', "Ledgic is down! Someone in the crowd saw the whole thing...")
    steps.append(('pan_says', 'say 0x%02X "That was amazing! I\'m coming with you too. Grandpa would want me to!"\n' % gt.portrait_id('pan')))
    code('ledgic_won_go', put(zone26.MORE_GT, 1) + put(zone26.MORE_LEDGIC_WON, 0) + '    push {gt_joins}\n    end\n')
    say('gt_joins', "Pan joins you, and the GT looks are open! See Switch Character.")
    code('gt_joins_go', '    push {start}\n    end\n')
    say('uub_won', "Uub says that was the best fight he's had. He wants to train with you!")
    code('uub_won_go', put(zone26.MORE_UUB, 1) + put(zone26.MORE_UUB_WON, 0) + '    push {uub_joins}\n    end\n')
    say('uub_joins', "Uub joins you! See Switch Character.")
    code('uub_joins_go', '    push {start}\n    end\n')
    say('race_won', "You beat the school's race record! Here's 50,000 Zenie.")
    code('race_won_go', put(zone26.MORE_RACE, 1) + '    pushn %d\n    call 0x%X\n    push {start}\n    end\n' % (zone26.RACE_PRIZE, zone26.ADD_ZENIE))
    say('museum_won', "The museum is complete, all 40 exhibits! A million Zenie and five Lazarus Crystals!")
    code('museum_won_go', put(zone26.MORE_MUSEUM, 1) + '    pushn %d\n    call 0x%X\n    pushn %d, %d\n    call 0x81\n    push {start}\n    end\n' % (zone26.MUSEUM_PRIZE, zone26.ADD_ZENIE, zone26.MUSEUM_ITEM, zone26.MUSEUM_ITEMS))
    code('rank', ''.join(lad(7) + '    push %d\n    eq\n    jz R%d\n    push {rank%d}\n    end\nR%d:\n' % (r, r, r, r) for r in (4, 3, 2)) + '    push {rank1}\n    end\n')
    for r, (letter, words) in enumerate((('C', "You made it, barely."), ('B', "A solid run."), ('A', "A fine run!"), ('S', "Barely a scratch!")), 1):
        say('rank%d' % r, "Boss Rush rank: %s! %s That's %s Zenie." % (letter, words, format(zone26.RANK_PRIZE[r - 1], ',')))
        code('rank%d_go' % r, put(zone26.MORE_RANK_NEW, 0) + '    pushn %d\n    call 0x%X\n    push {start}\n    end\n' % (zone26.RANK_PRIZE[r - 1], zone26.ADD_ZENIE))
    say('mode', "How's your bracket?\\n- Random draw\\n- Pick my opponents\\n- Not now")
    draw = ''.join('    pushn %d\n    call 0x19(%d)\n    call 0x%X\n' % (r, len(p), zone26.TOUR_PICK) for r, p in enumerate(zone26.TOUR_POOLS))
    code('mode_go', """    call 0x18
    push 0
    eq
    jz L1
""" + draw + """    push {enter}
    end
L1:
    call 0x18
    push 1
    eq
    jz L2
    push {pick0}
    end
L2:
    push {END}
    end
""")
    for r, title in enumerate(("First round. Pick your opponent!", "Second round. Who's next?", "The final! Who do you want?")):
        names = zone26.TOUR_NAMES[r]; nxt = 'pick%d' % (r + 1) if r < 2 else 'enter'
        def picks(base): return ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    pushn %d, %d\n    call 0x%X\n    push {%s}\n    end\nL%d:\n' % (v, v + 1, r, base + v, zone26.TOUR_PICK, nxt, v + 1) for v in range(3))
        say('pick%d' % r, title)
        say('a%d' % r, '\\n'.join('- ' + n for n in names[:3] + ('More',)))
        code('a%d_go' % r, picks(0) + '    call 0x18\n    push 3\n    eq\n    jz L9\n    push {b%d}\n    end\nL9:\n    push {END}\n    end\n' % r)
        say('b%d' % r, '\\n'.join('- ' + n for n in names[3:] + ('Back',)))
        code('b%d_go' % r, picks(3) + '    push {a%d}\n    end\n' % r)
    code('enter', more(zone26.MORE_TIER) + '    jz H1\n    pushn %d\n    call flag\n    jz H2\n    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\nH2:\n' % (zone26.TOUR_ORDERED, zone26.tier_first(1)) + zone26.tour_draw(0, 1) + '    push {END}\n    end\nH1:\n' + """    pushn %d
    call flag
    jz L1
    call 0x78(30)
    pushn 26, %d, 1, 360, 420
    call 0x77
    call 0x79(30)
    push {END}
    end
L1:
%s    push {END}
    end
""" % (zone26.TOUR_ORDERED, zone26.tour_first(), zone26.tour_draw(0)))
    say('trials', "Four trials, as the hero named. Zenie and gear for each, and a prize for all four!")
    say('trial_menu', '\\n'.join('- %s vs %s' % (t[1], t[4]) for t in trials))
    code('trial_go', ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    call 0x95(%d)\n    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\nL%d:\n' % (k, k + 1, t[0], zone26.trial_first() + k, k + 1) for k, t in enumerate(trials)) + '    push {END}\n    end\n')
    def status(name, flag, done, todo, nxt):
        code(name, '    pushn %d\n    call flag\n    jz L1\n    push {%s_done}\n    end\nL1:\n    push {%s_todo}\n    end\n' % (flag, name, name))
        say(name + '_done', done)
        code(name + '_skip', '    push {%s}\n    end\n' % nxt)
        say(name + '_todo', todo)
        code(name + '_next', '    push {%s}\n    end\n' % nxt)
    status('rewards', 887, "Boss Rush: cleared! Majin Buu, Super Janemba and Kid Buu are on your side.", "Boss Rush: win it and Majin Buu, Super Janemba and Kid Buu join you.", 'rew2')
    status('rew2', 890, "World Tournament: cleared! Each win pays 100,000 Zenie.", "World Tournament: each win pays 100,000 Zenie.", 'rew3')
    status('rew3', zone26.TRIAL_ALL, "Trials: all four cleared! You earned the Geromantium Bandana.", "Trials: Zenie and gear each. All four: Geromantium Bandana and ten Senzu Beans.", 'rew5')
    status('rew5', zone26.CELL_PAID, "Cell Games: cleared! You won Saiyan armor, Future Trunks and 200,000 Zenie.", "Cell Games: win all four fights for Saiyan armor, Future Trunks and 200,000 Zenie.", 'rew6')
    say('rew6', "Dragon Balls: seven lie near the landing pads of seven lands. Bring them to Mr. Popo.")
    code('rew6_go', '    push {rew4}\n    end\n')
    say('rew4', "Time Chamber: Mr. Popo on Kami's Lookout lets you spar with old foes, for less EXP.")
    code('rew4_go', '    push {rew_rank}\n    end\n')
    code('rew_rank', ''.join(lad(8) + '    push %d\n    eq\n    jz R%d\n    push {best%d}\n    end\nR%d:\n' % (r, r, r, r) for r in (4, 3, 2, 1)) + '    push {best0}\n    end\n')
    for r, text in enumerate(("Boss Rush rank: not yet earned. The more health you finish with, the better.", "Boss Rush best rank: C.", "Boss Rush best rank: B.", "Boss Rush best rank: A.", "Boss Rush best rank: S!")):
        say('best%d' % r, text)
        code('best%d_go' % r, '    push {rew_ladder}\n    end\n')
    steps.append(('rew_ladder', 'saycode 0x%02X "Endless: your best run is %%d wins."\n' % speaker + lad(5) + '    end\n'))
    steps.append(('rew_museum', 'saycode 0x%02X "Museum: %%d of 25 Hercule and %%d of 15 Z-Fighter exhibits."\n' % speaker + '    pushn 341, 5\n    call 0xBA\n    pushn 346, 4\n    call 0xBA\n    end\n'))
    code('rew_museum_go', '    push {END}\n    end\n')
    say('more', "- Cell Games\\n- Rewards\\n- Challengers\\n- Next")
    code('more_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n    push {cell}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n    push {rewards}\n    end\nL2:\n    call 0x18\n    push 2\n    eq\n    jz L3\n    push {challengers}\n    end\nL3:\n    push {more2}\n    end\n')
    say('more2', "- Trials II\\n- Dojo\\n- Back")
    code('more2_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n    pushn %d\n    call flag\n    jz L4\n    push {trials2}\n    end\nL4:\n    push {no_trials2}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n    push {dojo}\n    end\nL2:\n    push {menu}\n    end\n' % zone26.TRIAL_ALL)
    say('no_trials2', "Clear the first four Trials and claim their prize. Then come back for harder ones!")
    code('no_trials2_go', '    push {END}\n    end\n')
    say('trials2', "Trials II: harder foes, more Zenie and better gear. Clear all four for a set of Geromantium!")
    say('trial2_menu', '\\n'.join('- %s vs %s' % (t[1], t[4]) for t in zone26.TRIALS2))
    code('trial2_go', ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    call 0x95(%d)\n    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\nL%d:\n' % (k, k + 1, t[0], zone26.challenge_room('trial2_%d' % k), k + 1) for k, t in enumerate(zone26.TRIALS2)) + '    push {END}\n    end\n')
    for k, t in enumerate(zone26.TRIALS2):
        say('trial2_%d' % k, "Well done, %s! You beat %s! Take %s Zenie and the %s." % (t[1], t[4], '{:,}'.format(zone26.TRIAL2_PRIZE), t[6]))
        code('trial2_%d_go' % k, put(zone26.MORE_T2_PAID + k, 1) + '    pushn %d\n    call 0x%X\n    call 0x93(%d)\n    push {END}\n    end\n' % (zone26.TRIAL2_PRIZE, zone26.ADD_ZENIE, t[5]))
    say('all2_won', "All of Trials II cleared! Geromantium gear, ten Senzu Beans, and Super Saiyan 4 Gogeta joins you!")
    code('all2_won_go', put(zone26.MORE_T2_ALL, 1) + '    pushn %d, %d\n    call 0x81\n' % (zone26.TRIAL_ITEM, zone26.TRIAL_ITEMS) + ''.join('    call 0x93(%d)\n' % g for g in zone26.TRIAL2_GEAR) + '    push {END}\n    end\n')
    # Dojo: a page of fighters, then a fight with a CPU copy of the one picked, if you have them
    say('dojo', "The Dojo: spar with a copy of any fighter you've met. Each win pays %s Zenie." % '{:,}'.format(zone26.DOJO_PRIZE))
    say('dojo_menu', '\\n'.join('- %s' % c for c, _ in zone26.DOJO) + '\\n- Back')
    code('dojo_menu_go', ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    push {dojo_page%d}\n    end\nL%d:\n' % (k, k + 1, k, k + 1) for k in range(len(zone26.DOJO))) + '    push {menu}\n    end\n')
    n = 0
    for k, (_, people) in enumerate(zone26.DOJO):
        say('dojo_page%d' % k, '\\n'.join('- %s' % p[0] for p in people) + '\\n- Back')
        go = ''
        for i, (name, actor, lock) in enumerate(people):
            test = ('    pushn %d\n    call flag\n' % lock[1] if lock[0] == 'flag' else more(lock[1])) if lock else '    push 1\n'
            go += '    call 0x18\n    push %d\n    eq\n    jz L%d\n' % (i, i + 1) + test + '    jz N%d\n    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\nN%d:\n    push {dojo_locked}\n    end\nL%d:\n' % (i, zone26.challenge_room('dojo%d' % n), i, i + 1)
            n += 1
        code('dojo_page%d_go' % k, go + '    push {dojo_menu}\n    end\n')
    say('dojo_locked', "You haven't met that fighter yet.")
    code('dojo_locked_go', '    push {END}\n    end\n')
    say('challengers', "- Hercule's dare\\n- Goku Black\\n- GT challengers\\n- Back")
    code('challengers_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n    pushn 890\n    call flag\n    jz L4\n    push {dare}\n    end\nL4:\n    push {no_dare}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n' + more(zone26.MORE_HARD) + '    jz L5\n    push {black}\n    end\nL5:\n    push {no_black}\n    end\nL2:\n    call 0x18\n    push 2\n    eq\n    jz L3\n    push {gt}\n    end\nL3:\n    push {more}\n    end\n')
    say('gt', "- Ledgic\\n- Uub\\n- Back")
    code('gt_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n' + more(zone26.MORE_BLACK) + '    jz L4\n    push {ledgic}\n    end\nL4:\n    push {no_ledgic}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n' + more(zone26.MORE_GT) + '    jz L5\n    push {uub}\n    end\nL5:\n    push {no_uub}\n    end\nL2:\n    push {challengers}\n    end\n')
    say('no_ledgic', "A huge caped bodyguard wants whoever beat Goku Black. Come back when that's you.")
    code('no_ledgic_go', '    push {END}\n    end\n')
    say('ledgic', "Ledgic, Don Kee's bodyguard, wants a fight. He's huge, and he hits just as hard!")
    code('ledgic_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.challenge_room('ledgic'))
    say('no_uub', "Uub is training far from here. Beat Ledgic and he may hear about you.")
    code('no_uub_go', '    push {END}\n    end\n')
    say('uub', "Uub came all this way to test himself against you. He says he's got a trick or two!")
    code('uub_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.challenge_room('uub'))
    say('no_black', "A man in a black gi is asking for the Hard bracket's champion. That's not you yet.")
    code('no_black_go', '    push {END}\n    end\n')
    steps.append(('black', 'say 0x%02X "So you are the champion. Show me how far a mortal can climb."\n' % BLACK_PORTRAIT))
    code('black_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.black_room(0))
    say('no_dare', "Hercule only fights champions. Win a tournament first!")
    code('no_dare_go', '    push {END}\n    end\n')
    say('dare', "Hercule dares you to fight him! He's sure it's a dream match. For him, that is.")
    code('dare_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.hercule_room())
    say('cell', "The Cell Games! Four fights in a row at the old arena. Your health carries over. Good luck!")
    code('cell_go', '    pushn %d\n    call clear_flag\n    pushn %d\n    call clear_flag\n    call 0x78(30)\n    pushn 26, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % (*zone26.CELL_COUNT, zone26.cell_first(), *zone26.CELL_START))
    say('cell_won', "You beat Perfect Cell! 200,000 Zenie, Saiyan armor for three, and Future Trunks joins you!")
    code('cell_won_go', ''.join('    pushn %d\n    call set_flag\n' % f for f in (zone26.CELL_PAID,) + CELL_UNLOCKS) + '    pushn %d\n    call 0x%X\n    push {END}\n    end\n' % (zone26.CELL_PRIZE, zone26.ADD_ZENIE))
    say('tour_won', "You won the World Tournament! 100,000 Zenie, and Yamcha, Krillin and Videl want to join you!")
    code('tour_won_go', '    pushn 890\n    call set_flag\n' + put(zone26.MORE_YAMCHA, 1) + '    push {END}\n    end\n')
    say('rush_won', "You beat all nine! Majin Buu, Super Janemba and Kid Buu join you. See Switch Character.")
    code('rush_won_go', '    pushn 887\n    call set_flag\n    push {END}\n    end\n')
    for k, t in enumerate(trials):
        say('trial%d' % k, "Well done, %s! You beat %s! Take 30,000 Zenie and the %s." % (t[1], t[4], t[6]))
        code('trial%d_go' % k, '    pushn %d\n    call set_flag\n    pushn %d\n    call 0x%X\n    call 0x93(%d)\n' % (paid(k), zone26.TRIAL_PRIZE, zone26.ADD_ZENIE, t[5]) + more(zone26.MORE_TIEN) + '    jz L1\n    push {END}\n    end\nL1:\n    push {tien}\n    end\n')
    say('tien', "Tien saw that fight, and he'd like to join you. See Switch Character.")
    code('tien_go', put(zone26.MORE_TIEN, 1) + '    push {END}\n    end\n')
    say('all_won', "All four trials cleared! Take this Geromantium Bandana and ten Senzu Beans.")
    code('all_won_go', '    pushn %d\n    call set_flag\n    pushn %d, %d\n    call 0x81\n    call 0x93(%d)\n    push {END}\n    end\n' % (zone26.TRIAL_ALL, zone26.TRIAL_ITEM, zone26.TRIAL_ITEMS, zone26.TRIAL_GEAR))
    code('last', '    end\n')
    for name, text in steps:
        for m in re.finditer(r'say(?:code)? 0x\w+ "([^"]*)"', text):
            n = len(m.group(1).replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, m.group(1)
            if m.group(1).startswith('- '): assert all(len(l) <= 22 for l in m.group(1).split('\\n')), 'menu line too wide (it wraps and breaks the menu): ' + m.group(1)
    number = {n: k for k, (n, _) in enumerate(steps)}; number['END'] = len(steps)
    return head + ''.join('step auto %s' % re.sub(r'\{(\w+)\}', lambda m: str(number[m.group(1)]), t) for _, t in steps)


def debug_edits(first_form):
    """Join Vegito and guest Broly at the start, and open the picker, then save, when the intro ends."""
    heal = ''.join('    push %d\n    set %s\n' % (v, n) for v, n in ((500, 'max_hp'), (500, 'hp'), (100, 'max_ki'), (100, 'ki')))
    import zone26
    flags = ''.join('    pushn %d\n    call set_flag\n' % f for f in sorted({o['flag'] for l in json.load(open('ultimate/outfits.json'))['characters'].values() for o in l if o['flag'] and o['flag'] < zone26.MORE_FLAG}))
    flags += ''.join('    pushn %d\n    call set_flag\n' % u['flag'] for u in json.load(open('ultimate/outfits.json'))['unlocks'] if u['flag'] >= SS2_FLAG)
    if '--zone' in sys.argv: flags += '    pushn 149\n    call set_flag\n    pushn 0, 19\n    call 0xA4\n'
    join = ('step auto code\n' + flags + '    call 0x97(1)\n    call 0x97(3)\n    call 0x97(4)\n    call 0x97(6)\n    call 0x97(8)\n    call 0x95(3)\n' + heal + '    call 0xD0(21)\n    call 0x95(4)\n' + heal + '    call 0xD0(26)\n    call 0x95(1)\n' + heal + '    call 0xD0(15)\n    pushn 1, 107\n    call 0x9D\n    call 0xA4(1, 18)\n    call 0xA4(1, %d)\n' % BEAM_SKILL + '    call 0x95(6)\n' + heal + '    call 0x95(8)\n' + heal + '    pushn 8, 8\n    call 0xA4\n    pushn 8, %d\n    call 0xA4\n' % ERASER_SKILL +
            '    call 0xD0(%d)\n    call 0x95(0)\n    end\n' % first_form)
    s = open(INTRO).read()
    assert 'step 19 raw' in s
    open(INTRO, 'w').write(s.replace('step 19 raw', join + 'step 19 raw', 1))
    if '--zone' in sys.argv:                             # the debug door to the ending starts from its last scene
        e = open(ENDING).read()
        e, n = re.subn(r'(?m)^(step 1 z?code[^\n]*\n)', r'\1    push 66\n    end\n', e, 1)
        if n != 1: sys.exit('ending step 1 is not code')
        open(ENDING, 'w').write(e)
    if '--enemy' in sys.argv:
        open(ACTORS_FILE, 'a').write('enemy %s 0x70 0xB0 %s   ; debug: a Bomber to test attacks on (BFU_RIG_ENEMY="row character": another, e.g. test_guard.py\'s Gunman)\n' % tuple(os.environ.get('BFU_RIG_ENEMY', '8 34').split()))
    s = open(FIELD).read()
    zone = '--zone' in sys.argv
    tail = '    set 0x10\n    end\n'
    i = s.rfind(tail)
    assert i > 0
    open(FIELD, 'w').write(s[:i] + (tail if zone else '    set 0x10\n    call 0x8D\n    call 0x%X\n    end\n' % DEBUG_NATIVE) + s[i + len(tail):])


def unlock_edits():
    """Set each outfit's unlock flag where the story first gives that outfit."""
    cfg = json.load(open('ultimate/outfits.json'))
    touched = {}
    for u in cfg['unlocks']:
        p = 'assets/scripts/%s.evt' % u['list']
        s = open(p).read()
        touched.setdefault(p, s)
        site = u.get('after', u.get('find'))
        if site not in s:
            sys.exit('unlock site not found in ' + p)
        flag = '    pushn %d\n    call set_flag\n' % u['flag']
        open(p, 'w').write(s.replace(site, site + flag if 'after' in u else flag + site, 1))
    return touched


def unlock_edits_paths():
    cfg = json.load(open('ultimate/outfits.json'))
    return {'assets/scripts/%s.evt' % u['list']: open('assets/scripts/%s.evt' % u['list']).read() for u in cfg['unlocks']}


def save_stub(addr):
    """Thumb native: sub_08004962(&G, the slot being played, position, 0), the game's full save call."""
    src = """.syntax unified
.thumb
push {r4, lr}
sub sp, #8
ldr r0, =0x03001068
ldr r1, =0x03001910
ldrb r1, [r1]
movs r2, #0
str r2, [sp]
movs r2, #120
str r2, [sp, #4]
mov r2, sp
movs r3, #0
ldr r4, =0x08004963
bl 1f
add sp, #8
pop {r4}
pop {r0}
bx r0
1: bx r4
.ltorg
"""
    d = tempfile.mkdtemp()
    open(d + '/s.s', 'w').write(src)
    subprocess.run(['arm-none-eabi-as', '-mthumb', '-mcpu=arm7tdmi', d + '/s.s', '-o', d + '/s.o'], check=True)
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', d + '/s.o', d + '/s.bin'], check=True)
    return open(d + '/s.bin', 'rb').read()


def find_once(rom, needle, what):
    i = rom.find(needle)
    if i < 0 or rom.find(needle, i + 1) >= 0:
        sys.exit('%s: expected exactly one match' % what)
    return i


ANDROID13_SLOTS = {str(s): 'a13_idle' for s in range(22)}
ANDROID13_SLOTS.update({'10': 'a13_absorb!front', '1': 'a13_walk', '2': 'a13_walk', '4': 'a13_lunge', '5': 'a13_lunge', '6': 'a13_lunge', '9': 'a13_idle', '18': 'a13_hold', '19': 'a13_lunge', '20': 'a13_lunge', '21': 'a13_lunge', '3': 'a13_blast'})
A13_PAD = 8                      # columns of the sheet's background either side of a cell, for an arm drawn out past it (a13_pose)


def android13_frames(out, usable, pal):
    """Cut the walk sheet into 32x32 indexed cells (cap version), dropping the shadow drawn into each frame: the game adds its own."""
    from PIL import Image
    sheet = np.array(Image.open('ultimate/art/android13_sheet.png').convert('RGB')).astype(int)
    bg = sheet[0, 0]
    cols, rows = ((75, 93), (99, 117), (123, 141)), ((1, 32), (33, 64), (66, 96), (97, 128))
    u = np.array(usable); p = pal[u].astype(int)
    PAD = A13_PAD
    def cell(r, c, edit=None):
        (y0, y1), (x0, x1) = rows[r], cols[c]
        a = sheet[y0:y1, x0 - 1:x1 + 1].copy(); w = a.shape[1]
        side = np.tile(bg, (a.shape[0], PAD, 1)); a = np.concatenate([side, a, side], 1)
        if edit: edit(a, bg)
        m = (a != bg).any(2)
        black = (a.sum(2) == 0)
        foot = m.shape[0] - 5                               # the shadow: pure black in the bottom rows
        m[foot:][black[foot:]] = False
        ys = np.nonzero(m.any(1))[0]; h = ys[-1] + 1
        img = np.zeros((32, 32), np.uint8); ox = (32 - w) // 2 - PAD; oy = 32 - h
        for y in range(h):
            for x in range(a.shape[1]):
                if m[y, x] and 0 <= x + ox < 32:
                    q = a[y, x]; ch = lambda v: np.stack([v[..., 0] - v[..., 1], v[..., 1] - v[..., 2]], -1)
                    d = ((p - q) ** 2).sum(1) + 6 * ((ch(p) - ch(q)) ** 2).sum(1)
                    img[y + oy, x + ox] = u[d.argmin()]
        return img
    DOWN, UP, RIGHT = 2, 0, 3                               # the engine's side frames face left, so that's the row it wants
    def save(name, frames):
        for i, f in enumerate(frames):
            Image.fromarray(f).save('%s/%s_%02d.png' % (out, name, i))
    save('a13_idle', [cell(d, 1) for d in (DOWN, UP, RIGHT)])
    save('a13_walk', [cell(d, c) for d in (DOWN, UP, RIGHT) for c in (1, 0, 1, 2)])
    save('a13_lunge', [cell(d, c) for d in (DOWN, UP, RIGHT) for c in (0, 2)])
    # His attacks (Nov 10, the owner: "Android 13 bombers attack frames still fucked": the sheet has only his walk, so every move showed his stance
    # or a step): his own standing frames with the near arm redrawn (a13_pose), in the sheet's colours. Ki blast: the fist back, the arm out, then
    # both arms out (the Electric Kamehameha's push: held_poses makes his slot 31 of frames 0, 2, 2). Held balls (SS Deadly Bomber): the arm out.
    import a13_pose as A
    save('a13_blast', [cell(DOWN, 1, A.front_windup), cell(DOWN, 1, A.front_thrust), cell(DOWN, 1, A.front_thrust)] + [cell(UP, 1)] * 3 +
         [cell(RIGHT, 1, A.side_windup), cell(RIGHT, 1, A.side_thrust), cell(RIGHT, 1, A.side_push)])
    save('a13_hold', [cell(DOWN, 1, A.front_thrust), cell(UP, 1), cell(RIGHT, 1, A.side_thrust)])
    for i in range(6):                                      # absorbing 14's and 15's cores: the owner's sheet as cleaned for Gero's Legacy, already in the game's OBJ colours
        Image.fromarray(np.array(Image.open('ultimate/art/android13_absorb/a%d.png' % i))).save('%s/a13_absorb_%02d.png' % (out, i))


# Broly Full Power: made by Azure-Oni, ripped by DBZdogs. Frames as (x0, x1) on the down, up and side rows.
BROLY_FRAMES = {
    'idle': (((0, 46),), ((0, 46),), ((0, 27),)),
    'walk': (((94, 140), (158, 199), (225, 266), (287, 333)), ((93, 133), (153, 199), (218, 264), (289, 329)), ((98, 123), (142, 168), (172, 200), (205, 231))),
    'combo': (((347, 390), (406, 455), (478, 514)), ((349, 396), (410, 460), (462, 506)), ((327, 366), (372, 422), (444, 494))),
    'slam': (((600, 662), (665, 721)), ((585, 647), (658, 721)), ((599, 632), (647, 702))),
    'strike': (((756, 804), (817, 858)), ((754, 801), (816, 857)), ((750, 788), (822, 871))),
}
BROLY_SLOTS = {str(s): 'bfp_idle' for s in range(22)}
BROLY_SLOTS.update({'1': 'bfp_walk', '2': 'bfp_walk', '4': 'bfp_combo', '5': 'bfp_strike', '6': 'bfp_slam', '8': 'bfp_slam', '9': 'bfp_idle', '10': 'bfp_slam', '13': 'bfp_slam', '14': 'bfp_strike', '20': 'bfp_strike', '21': 'bfp_slam'})
# Firing: the strike's wind-up, then his open hand thrust out, held (Nov 10, the owner: "Why doesn't Broly have attack frames for shooting his eraser
# cannon": slots 3, the ki blast, and 18, the pose Eraser Cannon's Big Bang code holds, were his idle). Each keeps its frame numbers, the hand
# out from the second frame on (cfg 'indexed'), as a retail ki blast's.
BROLY_SLOTS.update({'3': 'bfp_strike', '18': 'bfp_strike'})
BROLY_INDEXED = [3, 18]


def indexer(usable, pal):
    """RGB to the game's OBJ palette, with colour shifts weighted so neutrals don't land on tints."""
    u = np.array(usable); p = pal[u].astype(int); cache = {}
    def ch(v): return np.stack([v[..., 0] - v[..., 1], v[..., 1] - v[..., 2]], -1)
    def one(q):
        q = np.asarray(q, dtype=int)         # a uint8 colour would wrap in the differences below
        k = tuple(int(v) for v in q)
        if k not in cache:
            d = ((p - q) ** 2).sum(1) + 6 * ((ch(p) - ch(q)) ** 2).sum(1)
            cache[k] = int(u[d.argmin()])
        return cache[k]
    return one


def broly_frames(out, usable, pal):
    from PIL import Image
    sheet = np.array(Image.open('ultimate/art/broly_full_power_sheet.png').convert('RGB')).astype(int)
    bg = sheet[0, 0]; one = indexer(usable, pal)
    fg = (sheet[:232] != bg).any(2)
    def cell(row, x0, x1):
        # this frame's rows: the row-th block of ink in its own columns (the sheet's rows aren't level)
        ink = fg[:, x0:x1 + 1].any(1); ys = np.nonzero(ink)[0]
        blocks = np.split(ys, np.nonzero(np.diff(ys) > 2)[0] + 1)
        blocks = [k for k in blocks if len(k) > 20]
        y0, y1 = blocks[row][0], blocks[row][-1] + 1
        a = sheet[y0:y1, x0:x1 + 1]; m = fg[y0:y1, x0:x1 + 1]
        h, w = m.shape
        if h > 64 or w > 64: sys.exit('Broly frame %dx%d is over the 64x64 sprite limit' % (w, h))
        img = np.zeros((64, 64), np.uint8)
        for y, x in zip(*np.nonzero(m)):
            img[64 - h + y, (64 - w) // 2 + x] = one(a[y, x])
        return img
    for name, rows in BROLY_FRAMES.items():
        n = 0
        for row, spans in enumerate(rows):
            for x0, x1 in spans:
                c = cell(row, x0, x1)
                if row == 2: c = c[:, ::-1]        # the sheet's side views face the way this game's don't
                Image.fromarray(c).save('%s/bfp_%s_%02d.png' % (out, name, n)); n += 1


def player_anim_lengths(clean):
    """Longest animation per slot across the retail player forms. Skills pick a frame by number, assuming a player's animation is as long as these, and
    past the end of a shorter one they read garbage as a frame (that is how Super 13's three-frame slot 19 crashed the Ghost Attack)."""
    u = lambda o: struct.unpack_from('<I', clean, o)[0]
    table = sprites.ACTOR_LIST; out = {}
    for f in range(FORM_COUNT):
        char = struct.unpack_from('<H', clean, FORMS + FORM_SIZE * f + 0x0E)[0]
        if char < 9: continue
        rec = u(table + 4 * (char - 9)) - ROM_BASE
        for s in range(u(rec) & 0xFF):
            a = u(rec + 0x54 + 4 * s)
            if a: out[s] = max(out.get(s, 0), u(a - ROM_BASE))
    return out


# Super Saiyan 4's ki bar (outfit.c ssj4_hud / ssj4_drain). The HUD's EP bar images are 48x16 8bpp pixel blocks indexed by the offsets of the
# draw buffer (the three HUD sprites' 0x500 bytes of tiles): green's bar part at 0x7137D8 (copied whole), yellow 0x713AD8, orange 0x713FD8. The purple one is the orange with its five shades swapped for the OBJ palette's purples (no palette change).
SSJ4_PURPLE = {0x6B: 0x9B, 0x6C: 0x9C, 0x04: 0x93, 0x6D: 0x94, 0x6E: 0x5B}
BAR_COLS, ORANGE_BAR = 0x71F40, 0x713FD8


def ssj4_bar(rom):
    offs = [struct.unpack_from('<I', rom, BAR_COLS + 16 * c + 4 * k)[0] for c in range(41) for k in range(3)]
    if not all(o < 0x500 for o in offs):
        sys.exit('EP bar column table changed')
    orange = rom[ORANGE_BAR:ORANGE_BAR + 0x500]
    if not {orange[o] for o in offs} <= set(SSJ4_PURPLE) | {1}:
        sys.exit('orange EP bar changed: %s' % sorted({orange[o] for o in offs}))
    return bytes(SSJ4_PURPLE.get(b, b) for b in orange)


# Mastered Kaioken's bar (outfit.c kk_hud): the HP bar's columns (41 x 3 pixel offsets into the HUD buffer at 0x71CB0) painted cyan over the red,
# as Super Saiyan's pools are painted over the EP bar. The base bar image (0x7137D8) sits at buffer offset 0x200.
HP_COLS, HP_BAR = 0x71CB0, 0x7137D8
KK_CYAN = {3: (0, 216, 248), 32: (0, 104, 152), 33: (0, 152, 200), 34: (72, 232, 248), 35: (152, 248, 248)}


def kk_bar(rom, clean):
    offs = [struct.unpack_from('<I', rom, HP_COLS + 16 * c + 4 * k)[0] for c in range(41) for k in range(3)]
    if not all(0x200 <= o < 0x500 for o in offs):
        sys.exit('HP bar column table changed')
    img = rom[HP_BAR:HP_BAR + 0x300]
    if not {img[o - 0x200] for o in offs} <= set(KK_CYAN):
        sys.exit('HP bar colours changed: %s' % sorted({img[o - 0x200] for o in offs}))
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    one = indexer([i for i in range(1, 256) if i not in artclean.MENU_SLOTS], pal)
    out = bytearray(0x500)
    for o in offs: out[o] = one(np.array(KK_CYAN[img[o - 0x200]]))
    return bytes(out)


def thumb_bl(at, to):
    off = to - (at + 4)
    return struct.pack('<HH', 0xF000 | (off >> 12) & 0x7FF, 0xF800 | (off >> 1) & 0x7FF)


def buu_merge_hook(rom, sym):
    """Kid Buu's behaviour taking his copy back with no copy there (Perfect Cell): outfit.c buu_merge in its state table's second method."""
    VT = 0x4B148
    if ROM_BASE + VT + struct.unpack_from('<i', rom, VT + 4)[0] != 0x08032DC9: sys.exit('Kid Buu\'s merge state changed')
    struct.pack_into('<i', rom, VT + 4, (sym['buu_merge'] | 1) - (ROM_BASE + VT))


def ssj4_ki_hooks(rom, sym):
    DRAIN = 0xE506                   # the Super Saiyan 3 class's drain: from here ssj4_drain decides, then jumps back to either branch
    if rom[DRAIN:DRAIN + 10] != bytes.fromhex('0a14011c20310b889342'):
        sys.exit('Super Saiyan 3 drain changed: %s' % rom[DRAIN:DRAIN + 10].hex())
    rom[DRAIN:DRAIN + 10] = bytes.fromhex('014b1847c046') + struct.pack('<I', sym['ssj4_drain'] | 1)
    HUD = 0xBCAE                     # the HUD's copy of its bars to VRAM: ssj4_hud(widget, buffer) recolours and copies
    if rom[HUD:HUD + 18] != bytes.fromhex('a08971490522400140181202291c3df03cfa'):
        sys.exit('HUD copy changed: %s' % rom[HUD:HUD + 18].hex())
    rom[HUD:HUD + 18] = bytes.fromhex('201c291c024b') + thumb_bl(HUD + 6, 0x46AA6) + bytes.fromhex('02e0c046') + struct.pack('<I', sym['ssj4_hud'] | 1)
    XFORM_AT = 0x1C35C               # the end of a power-up: the record's new form (row +0x16) -> xform_hook, which lets Kaioken and Blue choose theirs
    if rom[XFORM_AT:XFORM_AT + 8] != bytes.fromhex('b87d207543001818'):
        sys.exit('power-up end changed: %s' % rom[XFORM_AT:XFORM_AT + 8].hex())
    rom[XFORM_AT:XFORM_AT + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['xform_hook'] | 1)
    SS_DRAIN = 0xE42C                # Super Saiyan's drain taking a unit from +0x1E -> ss_drain_hook (Kaioken's health cost, mastery's slower drain)
    if rom[SS_DRAIN:SS_DRAIN + 8] != bytes.fromhex('011c1e310a88002a'):
        sys.exit('Super Saiyan drain changed: %s' % rom[SS_DRAIN:SS_DRAIN + 8].hex())
    rom[SS_DRAIN:SS_DRAIN + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['ss_drain_hook'] | 1)


def add_actors(rom, clean):
    combo = open(COMBO, 'rb').read()
    if hashlib.sha1(combo).hexdigest() != COMBO_SHA1:
        sys.exit('%s is not the Legacy of Goku I & II (USA) cart (SHA-1 mismatch); set BFU_COMBO.' % COMBO)
    cfg = json.load(open('ultimate/actors.json'))
    slots = cfg.pop('_slots')
    for k, a in cfg.items():
        if not k.startswith('_') and 'replace' not in a and 'log2_record' in a: a['log2_slots'] = {k: v for k, v in slots.items() if int(k) not in a.get('keep_own', ())}
    # Teen Gohan's Super Saiyan and Super Saiyan 2 in the purple gi (teen.py, approved Nov 11): every frame made and checked before any is
    # written, then each figure's frames come from teen.made in place of the purple record's (actors.json log2_source).
    import teen
    teen.use(combo[0x800000:])
    try: print('teen gohan: %d frames made and checked' % teen.every())
    except teen.Off as e: sys.exit(str(e))
    def checked(fn):
        def source(*args):
            try: return fn(*args)
            except teen.Off as e: sys.exit(str(e))
        return source
    for k, a in cfg.items():
        if isinstance(a, dict) and isinstance(a.get('log2_source'), str): a['log2_source'] = checked(teen.made(a['log2_source']))
    # The Saiyan armor's Super Saiyan 2 stance: the Super Saiyan stance (arms down) with r55's head (Nov 12, the owner: "SSJ2 Teen Gohan idle
    # pose his hands are raised up instead of down, if you can fix that to standard"; teen.armor2)
    cfg['gohan_armor_ss2_art']['log2_source'] = checked(teen.armor2())
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    usable = [i for i in range(1, 256) if i not in artclean.MENU_SLOTS]
    cfg['super13'] = {'proto_actor': 230}
    clean_dir = tempfile.mkdtemp()
    android13_frames(clean_dir, usable, pal)
    cfg['android13'] = {'template': 157, 'slots': ANDROID13_SLOTS}
    broly_frames(clean_dir, usable, pal)
    # origin_dy 8: BF's Broly (actor 29, whose record this one copies, shadow and all) stands with his feet 15 rows under his origin, a normal fighter 7;
    # the sheet's frames were lined up like a fighter's, so he hovered over his shadow (Nov 9, the owner: "fix Broly looking like he's floating")
    cfg['broly_fp'] = {'template': 29, 'slots': BROLY_SLOTS, 'big': True, 'stretch': True, 'origin_dy': 8, 'indexed': BROLY_INDEXED}
    # and no ground shadow for either Broly (the owner, same day: "Remove the shadow beneath Broly's feet too cause it looks off"): BF's
    # 24x10 oval, the biggest the game has, sat out past his boots in every pose. The story's Broly is the same record (actor 29).
    cfg['_no_shadow'] = [29, 'broly_fp', 'broly_player']
    one = indexer(usable, pal); lengths = player_anim_lengths(clean)
    cfg['broly_fp']['grow'] = lengths
    for actor, form in (('gogeta_dbs', 'base'), ('gogeta_dbs_ss', 'ssj')):
        gogeta.write_frames(clean_dir, form, one)
        cfg[actor] = {'template': 93, 'slots': gogeta.slots(form), 'stretch': True, 'grow': lengths}
    # Super Saiyan Blue Gogeta: Buu's Fury's own Super Saiyan Gogeta (actor 93), every frame, his hair in Blue Goku's colours shade for shade
    # (lib/ssb.py gogeta_frames). Nov 9-10 tries on DBS Gogeta's sheet figure are gone (the owner: "Literally look at SSJ Gogeta, turn that
    # hair blue colored and use SSB Gokus hair as a reference but DONT CHANGE THE SSJ GOGETA HAIR SHAPE", "Get the fucking hair RIGHT
    # according to BUUS FURY GOGETA"). He changes to it from DBS Gogeta's Super Saiyan as before (outfit.c ssb_use).
    cfg['gogeta_ssb'] = {'template': ssb.GOGETA, 'raw_frames': {str(k): v for k, v in ssb.gogeta_frames(clean, {k: one(np.array(v)) for k, v in SSB_HAIR.items()}, eyes=LOOK170).items()},
                         'compress': True, 'high': True, 'grow': lengths}
    for name in ('piccolo', 'android17', 'android18', 'krillin', 'future_trunks', 'future_trunks_ss', 'videl_player', 'kid_buu_player', 'majin_buu_player', 'super_janemba_player', 'tien_player', 'yamcha_player', 'pikkon_player', 'hercule_player'):
        cfg[name]['grow'] = lengths
    # Slot 19 frames stay in place (sprites.INDEXED, Nov 10: the charged ball holds frames 2 and 3), but Janemba's and Super 13's are their
    # boss records' longer attacks: spread out, the hold stays on the sword raised, the crouch (as approved). (Majin Buu's was too, held on
    # his boss attack's lightning round his head: now a punch of his own, fighter_poses.)
    cfg['super_janemba_player']['even'] = [19]
    # The LoG2 figures' slots that depend on what their record has (Nov 10, the owner on armour Gohan, Trunks and Vegeta, Future Trunks,
    # Android 17 and 18: run, ki blast, Big Bang, Final Flash and transformation frames "fucked"). Read off the frames: LoG2's 2 is being hurt
    # (it was the run), 13 the dash (the run; NPC records have none: their walk), 11 the power-up (fists in, then arms up), 12 flying, 9 the
    # change into the next form. Slot 18, held while firing, is the ki pose's arm out (actors.json _slots): LoG2's own animation 18 is a sword
    # or ki slash on the armour and Trunks records (Big Bang threw a slash), and only Piccolo's is a firing pose (his override).
    l2 = combo[0x800000:]
    def l2_has(ref, k):
        rec = sprites.log2_rec(l2, ref)
        return any(0x08800000 <= struct.unpack_from('<I', l2, rec + 0x4C + 16 * k + 4 * d)[0] < 0x09000000 for d in range(4))
    for name, a in cfg.items():
        if name.startswith('_') or name.startswith('cell_') or not isinstance(a, dict) or 'log2_record' not in a or 'replace' in a: continue
        ov = a.setdefault('log2_overrides', {}); own = set(a.get('keep_own', ()))
        dyn = {'2': 13 if l2_has(a['log2_record'], 13) else 1, '13': 11 if l2_has(a['log2_record'], 11) else 0}
        if l2_has(a['log2_record'], 12): dyn['15'] = 12
        if l2_has(a['log2_record'], 9): dyn['10'] = 9
        for k, v in dyn.items():
            if int(k) not in own: ov.setdefault(k, v)
    cfg['android13_player'] = {'template': 93, 'slots': ANDROID13_SLOTS, 'stretch': True, 'grow': lengths, 'reserve': 4096}    # the boss's small record can't carry a playable form
    # His beam (the Electric Kamehameha's code: slot 18 frame 0 while charging, then 1 and 2 by turns): the prototype's slot 18 has the charge,
    # the thrust, then four frames of him flexing with his arms up, so the thrust and a flex flickered by turns (Nov 10, the owner: "Why the fuck
    # is super android 13s beam attack frames so glitched out"). The charge, then the thrust held ('reframe').
    cfg['super13_player'] = {'proto_actor': 230, 'stance_back': True, 'even': [19], 'fill': {8: 9, 10: 9, 11: 0, 12: 0, 13: 9, 14: 4, 15: 7, 16: 17}, 'grow': lengths,
                             'reframe': {'18': [0, 1, 1, 1, 1, 1]}}
    for name, source in (('goku_ss2', 109), ('goku_ss2_b', 110), ('gohan_ss2', 104), ('gohan_green_ss2', 105), ('vegeta_ss2', 273), ('vegeta_ss2_b', 274), ('vegeta_armor_ss2', 'vegeta_armor_ss'), ('gohan_armor_ss2', 'gohan_armor_ss2_art'), ('trunks_ss2', 261), ('trunks_armor_ss2', 'trunks_armor_ss'), ('vegito_ss2', 276)):
        cfg[name] = {'same_as': source}
    cfg['android17']['reserve'] = 2048                  # the same as Super 17's: a change of size on transforming re-allocates OBJ memory and scrambled other sprites
    cfg['super17'] = {**cfg['android17'], 'size_scale': [1.12, 1.1], 'reserve': 2048}     # slightly taller and bulkier, as in Gero's Legacy
    cfg['android13_absorb'] = {'template': 152, 'slots': {'0': 'a13_absorb!front', '1': 'a13_absorb!front'}}     # a cutscene figure: only an idle animation plays by itself, as in Gero's Legacy
    for name, rec in (('cell_imperfect', 'r25'), ('cell_semi', 'r26'), ('cell_perfect', 'r27'), ('cell_junior', 'r28')):      # LoG2's own sprites, whole: 64x64 like the prototype's Super 13 (the Juniors are smaller)
        cfg[name] = {'template': 38, 'stretch': True, 'reserve': 1024 if name == 'cell_junior' else 4096, 'log2_record': rec,
                     # Perfect Cell fights with Kid Buu's row, whose beam plays slot 3 (Kid Buu's: standing, then the arm out, held): it was LoG2's
                     # idle, so he fired his beams standing with his arms down (Nov 12, the owner: "Perfect Cell Kamehameha frames glitched").
                     # Now LoG2's ki (animation 5): its side and back views go hand in -> arm out -> arm out, but its front view has the arm out
                     # in frame 0 and the fists-in crouch in 1-2, so the front is reordered to crouch -> arm out -> arm out
                     **({'reframe_view': {'3': {'0': [1, 0, 0]}}} if name == 'cell_perfect' and CELL_BEAM else {}),
                     'log2_slots': {**{str(k): 0 for k in range(22)}, **({'3': 5} if name == 'cell_perfect' and CELL_BEAM else {}), '1': 1, '2': 1, '4': 6, '5': 7, '6': 7, '7': '3@0:1' if name != 'cell_junior' else '2@0:1', '8': 5, '9': 5, '10': 5, '13': 5, '14': 6, '15': 2, '16': 3 if name != 'cell_junior' else 2, '17': 3 if name != 'cell_junior' else 2, '18': 5, '19': 5, '20': 6, '21': 5}}
    for k in range(7):                                   # the game's own item icons, as things you can walk up to
        p = symbol_items_icon(16 + k)
        t, size = struct.unpack_from('<II', clean, p); icon = np.frombuffer(bytes(wfz.decompress_stream(clean, p + 8, size)[0]), np.uint8).reshape(16, 16)
        cfg['dragon_ball_%d' % (k + 1)] = {'template': 152, 'raw_frames': {str(sl): [[icon], [icon], [icon]] for sl in (0, 1)}}
    looks, _ = goku_black.build(clean, one)      # Goku Black and Rose: every frame of Goku and Super Saiyan Goku, from the owner's sheet or in its colours
    cfg['goku_black'] = {'template': goku_black.SOURCE['black'], 'raw_frames': {str(k): v for k, v in looks['black'].items()}}
    cfg['goku_rose'] = {'template': goku_black.SOURCE['rose'], 'raw_frames': {str(k): v for k, v in looks['rose'].items()}}
    cfg.update(gt.actors(clean, pal, lengths))      # GT: Black Star Odyssey's fighters (bso_import.py; BFU_BSO points at the owner's sheet)
    # The Garlic Jr. quest (garlic.py; lib/garlic_art.py): Garlic Jr. is kid Goten's frames with his head on Pilaf's (the owner's choice) and his
    # cloak, cassock and shoes; Super Garlic Jr. is Spopovich's frames made his (the owner's choice); the Spice Boys and the Makyans are fighters of the
    # same build recoloured. Each keeps the record (and so the slots) of the fighter whose behaviour row it fights with. Right after the GT
    # actors, so their ids are fixed (new_actor_ids): the quest's scenes name them.
    frames, conv = garlic_art.garlic_jr_frames(clean, sprites.ACTOR_LIST)
    print('garlic_jr: heads placed %d (%d by hand), missed %d' % (conv.hits, conv.manual, conv.misses))
    if conv.misses: sys.exit('garlic_jr: Goten\'s head not found in %d frames (add them to garlic_art.MANUAL)' % conv.misses)
    cfg['garlic_jr'] = {'template': garlic_art.GARLIC_BODY, 'raw_frames': {str(k): v for k, v in sorted(frames.items())}, 'compress': True, 'high': True}
    for name, (src, fn) in garlic_art.TINTS.items():
        cfg[name] = {'tint_of': src, 'tint': fn, 'high': True}
    sg = super_garlic.Converter(clean, sprites.ACTOR_LIST)       # Super Garlic Jr.: Spopovich's frames, the singlet off, the brain's folds, ears
    cfg['super_garlic'].update(tint=sg, by_view=True)           # (lib/super_garlic.py; the owner's choice of base, Nov 9)
    cfg['spice']['fill'] = {'11': 0}          # Majin Vegeta's row (Spice's behaviour) is for his Super Saiyan figure, which has slot 11; BF Vegeta's has not
    cfg['gohan_gt_ss2'] = {'same_as': 'gohan_gt_ssj'}     # GT Gohan's Super Saiyan 2: his Super Saiyan's figure, with the crackle (outfit.c)
    # Super Saiyan Blue's hair (lib/ssb.py; Nov 10, the owner: "FIX SSB GOKUS HAIR NOT BEING FULLY BLUE WHY IS THERE STILL YELLOW"): each
    # Super Saiyan frame against its base figure's, so the spike tips and the hairline turn too
    to = {k: one(np.array(v)) for k, v in SSB_HAIR.items()}
    for n, (_, _, _, src, base) in SSB_LOOKS.items():
        under = struct.unpack_from('<H', clean, FORMS + FORM_SIZE * base + 0x0E)[0] - 9 if isinstance(src, int) and isinstance(base, int) else None
        cfg[n] = {'tint_of': src, 'tint': ssb.tint(clean, src, under, to, sides=n.startswith('goku'), eyes=LOOK170,
                                                   iris=ssb.LOG2_IRIS if src == 'vegeta_armor_ss' else ssb.IRIS), 'high': True}   # (his sideburns)
        # His change (slot 10): his Super Saiyan change's own pose, the hair blue (Nov 12, the owner: "Gokus hair turns SSJ3 in the SSB
        # transformation", "change the Vegeta and Gogeta SSB transformation pose and make them not raise their hands but do the normal pose").
        # Goku's Super Saiyan figure's change was the one into Super Saiyan 3 (the hair grows); Vegeta's was his power-up, arms up. The base
        # figure's change (BF's: black hair in frame 1, then the Super Saiyan frames 2-9 in the same pose) with the hair found against frame 1.
        if n in SSB_CHANGE:
            act, seq, ref = SSB_CHANGE[n]
            act = struct.unpack_from('<H', clean, FORMS + FORM_SIZE * act + 0x0E)[0] - 9 if isinstance(act, int) else act
            cfg[n]['change'] = {'actor': act, 'seq': seq, 'ref': ref,
                                'tint': (lambda sides, iris: lambda img, under: ssb.tint_piece(img, under, to, sides, LOOK170, iris))(n.startswith('goku'), ssb.LOG2_IRIS if src == 'vegeta_armor_ss' else ssb.IRIS)}
    red = kaioken_remap(pal, one)
    for n, (_, _, src) in KAIOKEN.items():
        cfg[n + '_kaioken'] = {'tint_of': src, 'tint': red, 'high': True}
    god = ssg_hair(one)
    for n, (_, _, src) in SSG_LOOKS.items():
        cfg[n] = {'tint_of': src, 'tint': god, 'high': True}
    cfg['roshi_player'] = {'roshi_of': 'krillin', 'head_of': 177, 'chin': [12, 11], 'high': True}     # Master Roshi: Krillin's frames, Roshi's head and clothes (lib/roshi.py)
    # Beerus (Battle of Gods, post-game): every frame of Kid Buu (actor 38, the boss's own 19 slots) with Beerus's head, collar and clothes
    # (lib/beerus.py). Slot 17 is Kid Buu's death by dissolving (likely only the ending plays it): Beerus's is a hit, then the knockdown.
    # BEERUS_LOOK: his side head ('old', or 'new': lib/beerus.py HEAD_SIDE_NEW) and how many pixels longer his torso and legs are, as the
    # owner approved them from his preview (ultimate/beerus_preview.py); BFU_BEERUS=old,0,0 tries another look without changing the line.
    # test_beerus.py holds the ROM to the approved look, frame by frame.
    look = os.environ.get('BFU_BEERUS', BEERUS_LOOK).split(',')
    cfg['beerus'] = {'beerus_of': 38, 'one': one, 'high': True, 'side': look[0], 'tall': (int(look[1]), int(look[2])),
                     'remap': {'17': [(9, 0), (9, 1), (9, 2)] + [(15, k) for k in range(4)] + [(15, 3)] * 4}}
    import whis                                            # Whis: Kibito's frames in his colours (lib/whis.py)
    cfg['whis'] = {'tint_of': 149, 'tint': whis.recolour(one), 'high': True}
    # Orange-gi Gohan's Super Saiyan and 2 (Nov 9): the game has no such figure, so form 58 used the school uniform's (actor 104) and he
    # changed clothes as he powered up. His own frames (actor 101) with the school Super Saiyan's gold hair: the pixels where actor 104
    # differs from the school base (98). Slot 20 (the spin attack) is the orange gi's slot 19; slot 11 (powering down) has no base frames.
    cfg['gohan_orange_ss'] = {'hairswap': {'base': 101, 'ref': 98, 'ss': 104, 'slots': {'20': [20, 19]}, 'idle_slots': [11]}, 'high': True}
    cfg['gohan_orange_ss2'] = {'same_as': 'gohan_orange_ss'}
    # Full Power Mystic: the orange gi's own figure (actor 101) under its own id; its lightning is the crackle (outfit.c), its power-up the orange gi's (_powerup)
    for n, (_, _, src) in FP_LOOKS.items():
        cfg[n] = {'same_as': src}
    # Full Power Mystic's change (Nov 12, 20:51, the owner: "Fix his transformation stance too"; 20:55: "Don't use the crouch for Mystic
    # Gohans power up use the same one Goku and Vegeta had"): BF's Super Saiyan change pose, which the orange gi (actor 101) never had:
    # BF Goku's change (actor 106, slot 10: the shout, fists at his sides, the dust; his orange gi, blue wristbands, belt and boots, as
    # Gohan's Mystic gi) with Gohan's head from his own change (actor 98, the school uniform: frame 1, the same shout in the same place,
    # rows 0-14; its hair black, as it stays), frames 2-9 as Blue's, then his stance. The orange gi's own Super Saiyan change keeps its shout.
    cfg['_change_canvases'] = {n: mystic_change(clean) for n in FP_LOOKS}
    cfg['_powerup_still'] = []
    cfg['_powerup'] = [101, 104, 105, 'gohan_orange_ss', 273, 274, 261, 276, 'vegeta_armor_ss', 'trunks_armor_ss', 'future_trunks_ss', 'gohan_armor_ss2_art',
                      'gohan_gt_ssj']     # armour Gohan's Super Saiyan has LoG2's own change into 2 (its animation 9). GT Gohan's (Nov 10): his slot 10
                                          # was the base's change, so into 2 he went back to black hair and glasses first (test_frames 14)
    cfg['broly_player'] = {'template': 29}       # the playable Broly's own copy of the story's figure: his slot 18 is the Eraser Cannon's pose (fighter_poses), the boss keeps his. Last: scripts name the ids before it
    # Great Saiyaman worn over another outfit (the saiyaman_from_ forms): BF's figure (actor 102) ends its change back (slots 11 and 19)
    # on the school uniform, grey then full, so every other outfit flashed the school uniform before its own (seen in the Nov 10 GIFs).
    # A copy that ends on the white figure instead; the school uniform's own Great Saiyaman (form 14) keeps BF's. After broly_player.
    cfg['saiyaman_outfit'] = {'template': 102, 'reframe': {'11': [0, 1, 2, 3, 4, 5, 5, 5, 5], '19': [0, 1, 2, 3, 4, 5, 5, 5, 5]}}
    for name in [k for k, a in cfg.items() if isinstance(a, dict) and a.get('last')]:     # actors.json "last": after every other actor, so no
        cfg[name] = cfg.pop(name)                                                             # id the build had before moves (Teen Gohan, Nov 12)
    ids, end = sprites.build_actors(rom, cfg, clean_dir, ACTORS_AT, combo[0x800000:], lambda act: (usable, pal), open(PROTO, 'rb').read(), high=0x1000000 if ROM32 else None)
    return ids, fighter_poses(rom, ids, powerup_frames(rom, ids, end))


# The LoG2 figures' changes of form (Nov 10, the owner: armour Gohan "ssj1 he lifts his arms ssj2 he punches while transforming", "when he
# destransforms it shows great saiyaman outfit", Trunks "Same shit ... Also shows kid Trunks on de transforming", armour Vegeta "transformation
# frames fucked"). (figure, the next form's figure or None, the form it powers down to or None.) A change plays slot 10 on the figure it starts
# from, in whatever view he faces, and powering down plays slot 11 on the figure it leaves: every view gets the front frames, as GT Vegeta's
# change (approved Nov 10). Slot 10: LoG2's own change where the record has one (actors.json: its animation 9; base Vegeta, Trunks and Future
# Trunks to Super Saiyan, armour Gohan's Super Saiyan to 2), else his fists-in power-up frame twice, the next form's eight times, then the next
# form's stance. Slot 11 was the template's (retail Gohan's, kid Trunks'): now LoG2's change played backwards where the base has one (Super Saiyan
# fading to base), else his stance twice and the base's twice, as retail's four-frame power-down.
LOG2_CHANGES = (('gohan_armor', 'gohan_armor_ss', None), ('gohan_armor_ss', 'gohan_armor_ss2_art', 'gohan_armor'), ('gohan_armor_ss2_art', None, 'gohan_armor'),
                ('trunks_armor', 'trunks_armor_ss', None), ('trunks_armor_ss', None, 'trunks_armor'), ('vegeta_armor', 'vegeta_armor_ss', None),
                ('vegeta_armor_ss', None, 'vegeta_armor'), ('vegeta_armor_ssb', None, 'vegeta_armor'), ('future_trunks', 'future_trunks_ss', None),
                ('future_trunks_ss', None, 'future_trunks'), ('android17', 'super17', None),
                ('teen_gohan', 'teen_gohan_ss', None), ('teen_gohan_ss', 'teen_gohan_ss2', 'teen_gohan'), ('teen_gohan_ss2', None, 'teen_gohan'))
LOG2_OWN_CHANGE = ('gohan_armor_ss', 'trunks_armor', 'vegeta_armor', 'future_trunks')     # their slot 10 is LoG2's animation 9
TEEN_FORMS = ('teen_gohan', 'teen_gohan_ss', 'teen_gohan_ss2', 'gohan_armor', 'gohan_armor_ss', 'gohan_armor_ss2')     # outfit.c is_teen: Teen Gohan's (Nov 12)
FT_ARMOR = ('trunks_armor', 'trunks_armor_ss', 'trunks_armor_ss2')     # outfit.c ft_armor: Future Trunks's Saiyan armor (Trunks's until Nov 12)
MASENKO_FIGURES = ('gohan_armor', 'gohan_armor_ss', 'gohan_armor_ss2_art', 'piccolo', 'teen_gohan', 'teen_gohan_ss', 'teen_gohan_ss2')     # the Masenko (Gohan's, Piccolo's) plays slot 12: arms up, then the arm out; LoG2 figures had their stance


def fighter_poses(rom, ids, at):
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    def put(data):
        nonlocal at
        at = (at + 3) & ~3; rom[at:at + len(data)] = data; at += len(data)
        return ROM_BASE + at - len(data)
    def rec_of(name): return u(ACTORS_AT + 4 * ids[name]) - ROM_BASE
    def anim(rec, slot):
        ap = u(rec + 0x54 + 4 * slot) if slot < rom[rec] else 0
        if not ap: return None
        a = ap - ROM_BASE
        return [[u(a + 4 + 16 * k + 4 * v) for v in range(4)] for k in range(u(a))]
    def need(name, slot, k):
        an = anim(rec_of(name), slot)
        if not an or len(an) <= k: sys.exit('%s: slot %d has no frame %d' % (name, slot, k))
        return an[k]
    def set_slot(name, slot, frames):                     # frames: [[4 views]...]
        rec = rec_of(name)
        if slot >= rom[rec]: sys.exit('%s: no slot %d' % (name, slot))
        struct.pack_into('<I', rom, rec + 0x54 + 4 * slot, put(struct.pack('<I', len(frames)) + b''.join(struct.pack('<4I', *f) for f in frames)))
    front = lambda f: [f[0]] * 4
    for fig, nxt, down in LOG2_CHANGES:
        if fig in SSB_CHANGE: pass                          # Blue's change: his Super Saiyan change's pose, blue (sprites.change_slot)
        elif fig in LOG2_OWN_CHANGE:
            ten = anim(rec_of(fig), 10)
            if not ten: sys.exit('%s: no LoG2 change' % fig)
            set_slot(fig, 10, [front(ten[i * len(ten) // 11]) for i in range(11)])     # 11 frames, as a retail power-up
        else:
            to = nxt or fig
            set_slot(fig, 10, [front(need(fig, 13, 0))] * 2 + [front(need(to, 13, 0 if nxt else 1))] * 8 + [front(need(to, 0, 0))])
        if down:
            base10 = anim(rec_of(down), 10) if down in LOG2_OWN_CHANGE else None
            if base10 and fig != 'vegeta_armor_ssb':          # (Blue fades through his own stance: the base's change has gold hair)
                k = len(base10)
                set_slot(fig, 11, [front(base10[k - 1 - i * k // 4]) for i in range(4)])     # its change backwards, in four frames
            else:
                set_slot(fig, 11, [front(need(fig, 0, 0))] * 2 + [front(need(down, 0, 0))] * 2)
    for fig in MASENKO_FIGURES:
        set_slot(fig, 12, [need(fig, 13, 1), need(fig, 3, 2)])
    # Base Broly's Eraser Cannon (Big Bang's code shows slot 18 frames 0 and 1 by turns while held, then 1): BF's Broly's slot 18 is his boss
    # moves (arms crossed, a fist up). His ki blast's hand out, held (Nov 10, the owner: "broly eraser cannon attack frames still fucked").
    set_slot('broly_player', 18, [need('broly_player', 3, 1)] * 3)
    # Pikkon's figure (BF's actor 215) has no firing pose: slot 18 was filled with his being-hit frames, so his wave played a recoil. His ki
    # blast's thrust, held.
    # (six frames, as long as a retail player's slot 18: skills pick its frames by number)
    set_slot('pikkon_player', 18, [need('pikkon_player', 3, 1)] * 6)
    # Armour Gohan's Great Saiyaman change (slot 19) was ten frames of his ki push from LoG2's default slot map: his arms up, as his power-up,
    # then the school uniform's flash into the costume (retail Gohan, actor 98: frames 4-9, a white figure and Great Saiyaman coming out of it).
    flash = anim(u(ACTORS_AT + 4 * 98) - ROM_BASE, 19)
    if not flash or len(flash) != 10: sys.exit('retail Gohan (actor 98): no ten-frame Great Saiyaman change')
    set_slot('gohan_armor', 19, [need('gohan_armor', 13, 0)] + [need('gohan_armor', 13, 1)] * 3 + flash[4:])
    # Energy Punch (skill 8) shows slot 19's frames 0-3 by number, then 2 and 3 in turn while held. Pikkon, Kid Buu and Android 13 had
    # their stance there (filled from slot 0), Full Power Broly his sheet's idle: their ki blast's wind-up, then its arm out held (ten frames,
    # a retail player's slot 19: the Ghost Attack once read past a shorter one). test_frames.
    # Majin Buu's was his boss record's attack (lightning round his head, then his antenna's beam), so the hold showed the lightning and no
    # punch (Nov 10, the owner: "fat Majin Buu energy punch looks bugged"): the same as the others.
    for name in ('pikkon_player', 'kid_buu_player', 'majin_buu_player', 'android13_player', 'broly_fp', 'broly_player'):     # (Broly's was his boss barrier: a golden shell)
        set_slot(name, 19, [need(name, 3, 0)] * 2 + [need(name, 3, 1)] * 8)
    # GT Trunks's slot 18 (from his BSO figure, where 18 is getting up) lay on the ground: his Flame Kamehameha fired lying down (seen in
    # the Nov 10 move GIFs). His ki blast's wind-up, then its arm out held.
    for name in ('trunks_gt', 'trunks_gt_ssj'):
        set_slot(name, 18, [need(name, 3, 0)] + [need(name, 3, 1)] * 5)
    # GT Goten's (from his BSO figure) is a flying kick and a spin, and Super Saiyan 4 Gogeta's (the owner's sheet) a vanish, so the hold
    # showed a kick or nothing: the stance, their ki blast's wind-up, then its arm out held.
    # Super Saiyan 4 Goku's too (his BSO figure's slot 19 is base Goku's Instant Transmission: the stance, a fade, a line), and the Super
    # Dragon Fist (outfit.c dragon4_use: the Dragon Fist's code, which shows slot 19 the same way and carries him along with the dragon) made
    # him vanish (Nov 10, the owner: "SSJ4 Goku does instant transmission on dragon fist"). No form of his in that figure has Instant
    # Transmission (kid Goku's moves: Energy Blast, the Kamehamehas, the Dragon Fist), so nothing else plays the slot.
    for name in ('goten_gt', 'goten_gt_ssj', 'goten_gt_green', 'gogeta_ssj4', 'kid_goku_ssj4'):
        set_slot(name, 19, [need(name, 0, 0), need(name, 3, 0)] + [need(name, 3, 1)] * 8)
    # Full Power Broly's (approved Nov 10 as the strike's wind-up, then the hand out) flickered the same way: frame 0 is the wind-up. The hand out.
    set_slot('broly_fp', 18, [need('broly_fp', 18, 1)] * len(anim(rec_of('broly_fp'), 18)))
    return at


def powerup_frames(rom, ids, at):
    """Kaioken and Blue power up on their new figure (outfit.c power_to), whose slot 10 is a recoloured copy of a transformation: Goku's base slot 10
    turns his hair gold from its third frame, and his Super Saiyan's grows into Super Saiyan 3's on its last. Kaioken from base keeps his first two
    frames (the crouch, then the shout with his own hair) and ends on his stance; Blue and Super Saiyan Kaioken end on their stance instead of the
    long hair. 11 frames, as a retail power-up."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    def rec_of(name): return u(ACTORS_AT + 4 * ids[name]) - ROM_BASE
    def put(data):
        nonlocal at
        at = (at + 3) & ~3; rom[at:at + len(data)] = data; at += len(data)
        return ROM_BASE + at - len(data)
    def frame(rec, slot, k):
        a = u(rec + 0x54 + 4 * slot) - ROM_BASE
        if k >= u(a): sys.exit('slot %d has no frame %d' % (slot, k))
        return rom[a + 4 + 16 * k:a + 4 + 16 * k + 16]
    def set10(name, frames):
        rec = rec_of(name)
        if rom[rec] <= 10: sys.exit('%s: no slot 10' % name)
        struct.pack_into('<I', rom, rec + 0x54 + 40, put(struct.pack('<I', 11) + b''.join(frames)))
    for n in ('goku', 'goku_halo'):
        r = rec_of(n + '_kaioken')
        if u(u(r + 0x54 + 40) - ROM_BASE) != 11: sys.exit('%s_kaioken: slot 10 is not an 11-frame power-up' % n)
        set10(n + '_kaioken', [frame(r, 10, 0)] + [frame(r, 10, 1)] * 9 + [frame(r, 0, 0)])
    # Goku's form 1 (a 16-slot figure, likely only for scenes) has no slot 10 at all: his Kaioken copy borrows the gi's power-up
    struct.pack_into('<I', rom, rec_of('goku_b_kaioken') + 0x54 + 40, u(rec_of('goku_kaioken') + 0x54 + 40))
    for n in ('goku_ssg', 'goku_halo_ssg'):                       # Super Saiyan God: the crouch, the shout (red hair), his stance
        r = rec_of(n)
        if u(u(r + 0x54 + 40) - ROM_BASE) != 11: sys.exit('%s: slot 10 is not an 11-frame power-up' % n)
        set10(n, [frame(r, 10, 0)] + [frame(r, 10, 1)] * 9 + [frame(r, 0, 0)])
    struct.pack_into('<I', rom, rec_of('goku_b_ssg') + 0x54 + 40, u(rec_of('goku_ssg') + 0x54 + 40))
    for n in ('goku_ss_kaioken', 'goku_ss_b_kaioken', 'goku_ssb', 'goku_ssb_b'):
        r = rec_of(n)
        if u(u(r + 0x54 + 40) - ROM_BASE) != 11: sys.exit('%s: slot 10 is not an 11-frame power-up' % n)
        set10(n, [frame(r, 10, k) for k in range(10)] + [frame(r, 0, 0)])
    return at


def patch_forms(rom, clean, cfg, actors):
    old = find_once(rom, clean[FORMS:FORMS + FORM_SIZE * FORM_COUNT], 'form table')
    rows = bytearray(rom[old:old + FORM_SIZE * FORM_COUNT])
    index = {}
    ids = {r['id']: k for k, r in enumerate(cfg['rows'])}
    for k, r in enumerate(cfg['rows']):
        src = r['copy'] if isinstance(r['copy'], int) else index[r['copy']]     # a retail row, or a new one made above
        row = bytearray(rows[FORM_SIZE * src:FORM_SIZE * (src + 1)])
        if 'name' in r:
            struct.pack_into('<HH', row, 2, r['name'], r.get('status_name', r['name']))
        row[0x0C] = r['owner']
        struct.pack_into('<H', row, 0x0E, actors[r['actor']] + 9 if 'actor' in r else r['character'])
        if 'portrait' in r:                                 # one speaker id, or the six expressions; "gt:<name>" a GT portrait
            ps = r['portrait'] if isinstance(r['portrait'], list) else [r['portrait']] * 6
            row[0x10:0x16] = bytes(gt.portrait_id(v[3:]) if isinstance(v, str) else v for v in ps)
        for off, key in ((0x16, 'up'), (0x17, 'down')):
            v = r.get(key, 255)
            row[off] = v if isinstance(v, int) else FORM_COUNT + ids[v]
        if 'flags' in r:
            struct.pack_into('<H', row, 0, r['flags'])
            if r['flags'] & 1: struct.pack_into('<I', row, 8, 0x03001B78)     # the Super Saiyan behaviour object: a guest's row was copied from a form without it
        rows += row
        index[r['id']] = FORM_COUNT + k
    for k, e in cfg.get('edit', {}).items():
        o = FORM_SIZE * int(k)
        if 'up' in e: rows[o + 0x16] = index[e['up']]
        if 'down' in e: rows[o + 0x17] = index[e['down']]
    for f in range(len(rows) // FORM_SIZE):                 # a form that can transform needs slot 10 (see sprites.py)
        up, char = rows[FORM_SIZE * f + 0x16], struct.unpack_from('<H', rows, FORM_SIZE * f + 0x0E)[0]
        if up != 255 and char >= 9:
            rec = struct.unpack_from('<I', rom, ACTORS_AT + 4 * (char - 9))[0] - ROM_BASE
            if struct.unpack_from('<I', rom, rec)[0] & 0xFF <= 10 or not struct.unpack_from('<I', rom, rec + 0x54 + 40)[0]:
                sys.exit('form %d can transform but its actor has no slot 10' % f)
    for f in range(len(rows) // FORM_SIZE):                 # changing back plays slot 11, and an empty one draws junk from address 0 over other sprites' tiles: a short stance instead
        char = struct.unpack_from('<H', rows, FORM_SIZE * f + 0x0E)[0]
        if rows[FORM_SIZE * f] & 1 and rows[FORM_SIZE * f + 0x17] != 255 and char >= 9:
            rec = struct.unpack_from('<I', rom, ACTORS_AT + 4 * (char - 9))[0] - ROM_BASE
            if rom[rec] <= 11:
                sys.exit('form %d changes back but its actor has no slot 11' % f)
            if not struct.unpack_from('<I', rom, rec + 0x54 + 44)[0]:
                print('form %d: slot 11 was empty' % f)
                struct.pack_into('<I', rom, rec + 0x54 + 44, struct.unpack_from('<I', rom, rec + 0x54)[0])
    # Vegito's forms count a fusion's time down and show it (flags bit 3, as Gogeta's and Gotenks's: the fusion classes' tick, the HUD's
    # timer), for the Potara (Nov 12, outfit.c potara_use). The story's Vegito has no limit (-1), which neither counts nor shows.
    for f in (39, 40, index['vegito_ss2']):
        if rows[FORM_SIZE * f + 0x0C] != 6: sys.exit('form %d is not Vegito\'s' % f)
        rows[FORM_SIZE * f] |= 8
    if len(rows) // FORM_SIZE > 255:
        sys.exit('too many forms: 255 is the "none" marker')
    rom[SPACE:SPACE + len(rows)] = rows
    n = 0
    for o in range(0, CODE_END, 4):
        if struct.unpack_from('<I', rom, o)[0] == ROM_BASE + old:
            struct.pack_into('<I', rom, o, ROM_BASE + SPACE)
            n += 1
    if n != 37:
        sys.exit('form table: expected 37 code references, found %d' % n)
    return index, SPACE + len(rows)


FLASH_SAVE = True                # the 64 KB flash save (the owner, Nov 12 11:34: "switch the game to flash save"); the guest bench needs it since version 3
if os.environ.get('BFU_EEPROM'): sys.exit('BFU_EEPROM: no EEPROM builds since the guest bench moved into the flash (Nov 12)')
FLASH_INIT_WAS = 'f8b5041c402000f0'  # BF's start-up EEPROM read (0x0803FB7C): push, mov r4, r0, movs r0, #0x40, bl...
FLASH_CODE = b'BFUE'                 # the game code a flash build carries: VBA-M's list of known games holds BG3E to the 8 KB EEPROM


def flash_header(rom):
    """The flash save (every build since Nov 12): VBA-M (its libretro core, its desktop builds, Delta's core) and gpSP read the save type from
    the save library's tag in the ROM (mGBA decides by the first access), and VBA-M's list of known games (libretro, desktop) holds Buu's
    Fury (BG3E) to the 8 KB EEPROM, so the tag names a 64 KB flash chip and the game code is the Ultimate Edition's own; the header's
    check byte follows. The tag must be the only one: VBA-M takes EEPROM_ or SRAM_ anywhere in the ROM over FLASH."""
    TAG = 0x7B7964
    if rom[TAG:TAG + 11] != b'EEPROM_V124' or rom[0xAC:0xB0] != b'BG3E': sys.exit('ROM tag or game code changed')
    rom[TAG:TAG + 11] = b'FLASH_V126\0'
    rom[0xAC:0xB0] = FLASH_CODE
    rom[0xBD] = (-sum(rom[0xA0:0xBD]) - 0x19) & 0xFF
    if any(rom.find(t) >= 0 for t in (b'EEPROM_', b'SRAM_', b'FLASH1M_', b'FLASH512_')) or rom.count(b'FLASH') != 1: sys.exit('another save tag in the ROM')


def symbol(name):
    out = subprocess.run(['arm-none-eabi-nm', 'buusfury_modern.elf'], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        p = line.split()
        if p[-1] == name:
            return int(p[0], 16)
    sys.exit('symbol %s not found' % name)


BENCH_OLD = ('broly', 'broly_fp', 'android13', 'piccolo', 'future_trunks', 'android17', 'android18', 'krillin', 'videl', 'majin_buu', 'super_janemba', 'kid_buu', 'tien', 'yamcha', 'pikkon', 'hercule')
BENCH_GROUPS = 48                # outfit.c's GROUPS: fighters the save can keep progress for (bench version 3, Nov 12: the flash save)
# The guests' transformation mastery (outfit.c guest_tiers, Nov 12): (a guest outfit, tier: 0 Super Saiyan's, 1 Super Saiyan 2's), the
# fighter's own byte in the bench's spare field, in this order (saves keep them by place: add new ones at the end). Only the Saiyan
# transformations each has in the series: Goku Black's Rose is his Super Saiyan's tier.
GUEST_MASTERY = (('future_trunks', 0), ('teen_gohan', 0), ('teen_gohan', 1), ('goku_black', 0))


def bench_groups(guests):
    """Each guest outfit's bench group (outfit.c bench_group): the fighters saves already hold keep their groups (Full Power is Broly's), and new ones take the next."""
    names = [o['form'] for o in guests]
    if tuple(names[:len(BENCH_OLD)]) != BENCH_OLD:
        sys.exit('guest list changed: older saves keep progress by this order; add new guests at the end')
    out = [0, 0] + list(range(1, len(BENCH_OLD) - 1))
    shared = dict(zip(BENCH_OLD, out))              # a new look can share an old fighter's group (Future Trunks's armor, Nov 12)
    for o in guests[len(BENCH_OLD):]:               # new guests take the next groups; looks of one fighter ("bench") share theirs
        key = o.get('bench', o['form'])
        if key not in shared: shared[key] = max(out) + 1
        out.append(shared[key])
    if max(out) >= BENCH_GROUPS - 1:            # (the last group keeps Gogeta's own progress while a dance has his record: outfit.c fused_stash)
        sys.exit('more guests than the save has room for (%d)' % (BENCH_GROUPS - 1))
    src = open('ultimate/src/outfit.c').read(); body = src[src.index('static void guest_sync'):]; body = body[:body.index('u8 *r =')]
    for name, count in re.findall(r'(\w+)\[\] = \{(\d+),', body):
        if int(count) > 5:
            sys.exit('%s has %s moves: the bench keeps five skill levels' % (name, count))
    return out


def map_marks(clean):
    """The flight map's markers (outfit.c minimap_draw): the centre of every named place on Earth's map (area 0:50's exit list 0x0807387C,
    35 {condition, record}: a name record starts 0x080076C5, then its box and UI string), on the mini-map: X = 160 + x / 44.75,
    Y = -1.25 + y / 44.75 (Black Star Odyssey measured it), less 3 for the 8x8 sprite's middle. Places that come and go (the Giant
    Airship) and the controls line are left out; the Lookout and the wasteland it leaves share one spot."""
    EXITS, NAME_FN = 0x7387C, 0x080076C5
    seen = []
    for i in range(35):
        cond, rec = struct.unpack_from('<II', clean, EXITS + 8 * i)
        if struct.unpack_from('<I', clean, rec - ROM_BASE)[0] != NAME_FN: continue
        x0, y0, x1, y1 = struct.unpack_from('<4H', clean, rec - ROM_BASE + 8)
        if x1 > 4000 or (cond and (x0, y0) != (593, 1025)): continue
        m = (int(round(160 + (x0 + x1) / 2 / 44.75)) - 3, int(round(-1.25 + (y0 + y1) / 2 / 44.75)) - 3)
        if m not in seen: seen.append(m)
    if len(seen) != 13: sys.exit('world map places changed: %d' % len(seen))
    return seen


def glow_band_colour(clean, colour=None):
    """1c's band colour (lib/ssb_glow.py COLOURS[14]) as the palette entry nearest it that a 16-colour sprite can use (not the first of its
    bank, which is see-through): the band's sprite takes that entry's bank, and draws with its place in it."""
    import ssb_glow
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    return indexer([i for i in range(1, 256) if i not in artclean.MENU_SLOTS and i & 15], pal)(np.array(colour or ssb_glow.COLOURS[14]))


def add_outfits(rom, clean, at, art):
    """Compile the outfit code with its table at `at`, then point the Switch Character screen's vtable at it."""
    cfg = json.load(open('ultimate/outfits.json'))['characters']
    index, table = [], []
    fm = json.load(open(OUT + '/_forms.json'))
    for c in range(9):
        lst = cfg.get(str(c), [])
        index.append('{%d,%d}' % (len(table), len(lst)))
        form = lambda v: v if isinstance(v, int) else fm[v]
        table += ['{%d,%d,%d,(const u16 *)L"%s"}' % (form(o['form']), form(o.get('also', 255)), o['flag'], o['name']) for o in lst]
    d = tempfile.mkdtemp()
    lost = [o['form'] for o in cfg['1'] if o['form'] not in [b for b, _ in SAIYAMAN]]
    if lost: sys.exit('Great Saiyaman has no way back to these Gohan outfits (build.py SAIYAMAN, a saiyaman_from_ row in forms.json): %s' % lost)
    pairs = ['{%d,%d}' % (base if isinstance(base, int) else fm[base], 14 if row == 14 else fm[row]) for base, row in SAIYAMAN]
    c = open('ultimate/src/outfit.c').read() + '\nconst u16 outfit_index[9][2] = {%s};\nconst struct outfit outfit_table[] = {%s};\nconst u8 saiyaman_map[][2] = {%s};\nconst int saiyaman_count = %d;\nconst u8 ss2_rows[] = {%s,255};\nconst u8 ssj4_rows[] = {%s,255};\nconst u8 ssj3_goku_rows[] = {%s,255};\n' % (','.join(index), ','.join(table) or '{0,0,0,0}', ','.join(pairs), len(pairs), ','.join(str(v) for k, v in fm.items() if k.endswith(('_ss2', '_ss2_b'))), ','.join(str(v) for k, v in fm.items() if k.endswith('ssj4')), ','.join(str(v) for v in SSJ3_GOKU + (fm['kid_goku_ssj3'],)))
    c += 'const u8 ssj4_bar[0x500] = {%s};\n' % ','.join(map(str, ssj4_bar(rom)))
    c += 'const u8 kk_bar[0x500] = {%s};\n' % ','.join(map(str, kk_bar(rom, clean)))
    c += 'const u8 map_marks[][2] = {%s};\nconst int map_mark_count = %d;\n' % (','.join('{%d,%d}' % m for m in map_marks(clean)), len(map_marks(clean)))
    if max(len(b) for b in SKILL_BOOK.values()) > BOOK_PLACES: sys.exit('a skill book has more than %d places' % BOOK_PLACES)
    c += 'const u8 skill_book[8][%d] = {%s};\n' % (BOOK_PLACES, ','.join('{%s}' % ','.join(str(v) for v in SKILL_BOOK[k] + (255,) * (BOOK_PLACES - len(SKILL_BOOK[k]))) for k in range(8)))
    c += 'const u8 level_steps[][4] = {%s{255,255,255,255}};\n' % ''.join('{%d,%d,%d,%d},' % t for t in LEVEL_STEPS)
    c += 'const u8 kaioken_map[][2] = {%s{255,255}};\n' % ''.join('{%d,%d},' % (base if isinstance(base, int) else fm[base], fm[n + '_kaioken']) for n, (base, _, _) in KAIOKEN.items())
    c += 'const u8 ssg_map[][2] = {%s{255,255}};\n' % ''.join('{%d,%d},' % (base, fm[n]) for n, (base, _, _) in SSG_LOOKS.items())
    c += 'const u8 fp_map[][2] = {%s{255,255}};\n' % ''.join('{%d,%d},' % (base, fm[n]) for n, (base, _, _) in FP_LOOKS.items())
    c += 'const u8 ssb_map[][2] = {%s{255,255}};\n' % ''.join('{%d,%d},' % (fm[a] if isinstance(a, str) else a, fm[b]) for a, b in SSB_FORMS if b in fm)
    open(d + '/o.c', 'w').write(c)
    import zone26
    groups = bench_groups(cfg['8'])
    GLOW_BAND_COLOUR = glow_band_colour(clean)
    gnames = [o['form'] for o in cfg['8']]
    guest_tiers = ','.join('{%d,%d}' % (groups[gnames.index(n)], t) for n, t in GUEST_MASTERY)
    if len(GUEST_MASTERY) > 4: sys.exit('the bench keeps four guest mastery bytes (its spare 0-3)')
    flags = ['-mthumb', '-mcpu=arm7tdmi', '-O2', '-ffreestanding', '-fno-builtin', '-nostdlib', '-fshort-wchar', '-DHEAP_WORDS=0x%X' % HEAP_WORDS, '-DERASER_SKILL=%d' % ERASER_SKILL, '-DBOMBER_SKILL=%d' % BOMBER_SKILL, '-DBEAM_SKILL=%d' % BEAM_SKILL, '-DWAVE_SKILL=%d' % WAVE_SKILL, '-DSUPER13_SKILL=%d' % SUPER13_SKILL, '-DSUPER17_SKILL=%d' % SUPER17_SKILL, '-DBLITZ_SKILL=%d' % BLITZ_SKILL, '-DFORM_KID_BUU=%d' % fm['kid_buu'], '-DSHELVED_SKILLS={%s}' % ','.join(map(str, SHELVED_SKILLS)), '-DSHELVED_FORMS={%s}' % ','.join('{%d,%d}' % (fm['shelved_ape_' + n], fm[n]) for n in SHELVED_FORMS), '-DFORM_MAJIN_BUU=%d' % fm['majin_buu'], '-DFORM_JANEMBA=%d' % fm['super_janemba'], '-DDISC_SKILL=%d' % DISC_SKILL, '-DFORM_ANDROID17=%d' % fm['android17'], '-DFORM_ANDROID18=%d' % fm['android18'], '-DFORM_KRILLIN=%d' % fm['krillin'], '-DFORM_VIDEL=%d' % fm['videl'], *(['-DDEBUG_OPEN'] if '--debug' in sys.argv else []), *(['-DFLASH_SAVE'] if FLASH_SAVE else []), *(['-DLOOK170'] if LOOK170 else []), *(['-DGLOW_MORE'] if GLOW_MORE else []), '-DGLOW_FRAMES=8', '-DGLOW_TRANS=%d' % (3 + __import__('ssb_glow').TRANS_MORPH), '-DGLOW_FADE=%d' % __import__('ssb_glow').FADE_OUT, '-DGLOW_STEP=%d' % __import__('ssb_glow').STEP.get(GLOW_STYLE, 4), *(['-DGLOW_BAND=%d' % GLOW_BAND_COLOUR, '-DGLOW_ALPHA=0x%X' % (GLOW_ALPHA[0] | GLOW_ALPHA[1] << 8)] if GLOW_STYLE in __import__('ssb_glow').BANDS else []), '-DTIER_ROOMS=%s' % zone26.tier_rooms(), '-DENDLESS_STEP=%d' % zone26.ENDLESS_STEP, '-DENDLESS_CAP=%d' % zone26.ENDLESS_CAP, '-DFORM_TIEN=%d' % fm['tien'], '-DFORM_BLACK=%d' % fm['goku_black'], '-DFORM_ROSE=%d' % fm['goku_rose'], '-DFORM_PAN=%d' % fm['pan'], '-DFORM_PAN_LAST=%d' % fm['pan_brapan'], '-DFORM_UUB=%d' % fm['uub'], '-DFORM_MAJUUB=%d' % fm['majuub'], '-DFORM_GOGETA_SSJ4=%d' % fm['gogeta_ssj4'], '-DFORM_GOGETA_DBS_SS=%d' % fm['gogeta_dbs_ss'], '-DSSB_SKILL=%d' % SUPER_BLUE_SKILL, '-DKAIOKEN_SKILL=%d' % KAIOKEN_SKILL, '-DSSG_SKILL=%d' % SSG_SKILL, '-DFP_SKILL=%d' % FP_SKILL, '-DMYSTIC_FLAG=%d' % MYSTIC_FLAG, '-DMORE_BOG_DONE=%d' % zone26.MORE_BOG_DONE, '-DSTATS_REF=0x%X' % zone26.STATS_REFS[0], '-DSTATS_ROWS=%d' % zone26.STATS_COUNT, '-DPHASE1_ROW=%d' % zone26.PHASE1_ROW, '-DBOSS_ROW=%d' % zone26.BOSS_ROW, '-DARENA_ROOMS=0x%X' % zone26.arena_rooms(), '-DSTORY_UNLOCKS={%s}' % ','.join(str(u['flag']) for u in json.load(open('ultimate/outfits.json'))['unlocks']), '-DSTORY_MARKS={%s}' % ','.join('{%d,%d}' % m for m in STORY_MARKS), '-DMORE_BOG_FIGHT=%d' % zone26.bog.MORE_BOG_FIGHT, '-DMORE_GJ_DONE=%d' % zone26.garlic.GJ_DONE, '-DMORE_BOG_RITUAL=%d' % zone26.bog.MORE_BOG_RITUAL, '-DSOLAR_SKILL=%d' % SOLAR_FLARE_SKILL, '-DMAX_POWER_SKILL=%d' % MAX_POWER_SKILL, '-DGEAR_POTARA=%d' % GEAR_POTARA, '-DGEAR_GRAVITY=%d' % GEAR_GRAVITY, '-DGEAR_SHADES=%d' % GEAR_SHADES, '-DGEAR_POUCH=%d' % GEAR_POUCH, '-DFORM_ROSHI=%d' % fm['roshi'], '-DSS2_SKILL=%d' % SS2_SKILL, '-DGOGETA_FLAG=%d' % json.load(open('ultimate/outfits.json'))['characters']['7'][0]['flag'], '-DFORM_ROSHI_MAX=%d' % fm['roshi_max'], '-DTENX_SKILL=%d' % TENX_SKILL, '-DDRAGON4_SKILL=%d' % DRAGON4_SKILL, '-DFINAL_SHINE_SKILL=%d' % FINAL_SHINE_SKILL, '-DGALICK_SKILL=%d' % GALICK_SKILL, '-DSUPER_KAME_SKILL=%d' % SUPER_KAME_SKILL, '-DSUPER_KAME_USES=%d' % SUPER_KAME_USES, '-DMASTERY_L2=%d' % MASTERY_L2, '-DMASTERY_L3=%d' % MASTERY_L3, '-DMORE_GT_FLAG=%d' % zone26.MORE_GT, '-DMAJUUB_SKILL=%d' % MAJUUB_SKILL, '-DROSE_SKILL=%d' % ROSE_SKILL, '-DBLACK_KAME_SKILL=%d' % BLACK_KAME_SKILL, '-DBENCH_GROUP_LIST=%s' % ','.join(map(str, groups)), '-DGUEST_TIERS=%s' % guest_tiers, '-DPOTARA_SKILL=%d' % POTARA_SKILL, '-DDANCE_SKILL=%d' % DANCE_SKILL, '-DTRIAL_ALL=%d' % zone26.TRIAL_ALL, '-DSS4_SKILL=%d' % SS4_SKILL, '-DFORM_YAMCHA=%d' % fm['yamcha'], '-DFORM_PIKKON=%d' % fm['pikkon'], '-DFORM_HERCULE=%d' % fm['hercule'], '-DFORM_FUTURE_TRUNKS=%d' % fm['future_trunks'], '-DTEEN_FORMS=%s' % ','.join(str(fm[n]) for n in TEEN_FORMS), '-DFT_ARMOR=%s' % ','.join(str(fm[n]) for n in FT_ARMOR), '-DFORM_SAIYAMAN_ARMOR=%d' % fm['saiyaman_from_armor'], '-DSS2_FLAG=%d' % SS2_FLAG, '-DTOUR_PICK_FLAG=%d' % zone26.TOUR_PICKS, '-DFORM_BROLY=%d' % fm['broly'], '-DFORM_FP=%d' % fm['broly_fp'], '-DFORM_PICCOLO=%d' % fm['piccolo'], '-DFORM_A13=%d' % fm['android13'], '-DBALL_AREAS={%s}' % ','.join(str(b[1] << 8 | b[0]) for b in zone26.BALLS), '-DFORM_S13=%d' % fm['super13'], '-DFORM_S17=%d' % fm['super17'], '-DSOUND_MOVE=0x%X' % symbol('gUnknown_0831947C'), '-DFONT=0x%X' % symbol('gUnknown_0807012C'), '-DMELEE_RECTS=0x083C344C', '-DSOUND_HIT=0x%X' % symbol('gUnknown_083192A8')]
    syms = ['-Wl,--defsym=form_table=0x%X' % (ROM_BASE + SPACE), '-Wl,-Ttext=0x%X' % (ROM_BASE + at), '-Wl,-e,picker_update', '-Wl,--no-warn-rwx-segments']
    lib = subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-print-libgcc-file-name'], capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(['arm-none-eabi-gcc'] + flags + syms + [d + '/o.c', lib, '-o', d + '/o.elf'], check=True)
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', d + '/o.elf', d + '/o.bin'], check=True)
    code = open(d + '/o.bin', 'rb').read()
    nm = subprocess.run(['arm-none-eabi-nm', d + '/o.elf'], capture_output=True, text=True, check=True).stdout
    sym = {l.split()[2]: int(l.split()[0], 16) for l in nm.splitlines() if len(l.split()) == 3}
    writable = [l.split()[2] for l in nm.splitlines() if len(l.split()) == 3 and l.split()[1] in 'bBdD' and not l.split()[2].startswith('_')]
    if writable:                                          # the code sits in ROM: a variable linked after it reads ROM and its writes go nowhere
        sys.exit('outfit.c has writable statics (put them in work RAM): %s' % writable)
    if set(rom[at:at + len(code)]) != {0xFF}:
        sys.exit('outfit code space is not free')
    rom[at:at + len(code)] = code
    vt = symbol('_0804A5E0') - ROM_BASE
    for slot, want, name in ((5, 0x0802EBA5, 'picker_update'), (8, 0x0802ECEB, 'picker_input')):
        if ROM_BASE + vt + struct.unpack_from('<i', rom, vt + 4 * slot)[0] != want:
            sys.exit('vtable slot %d changed' % slot)
        struct.pack_into('<i', rom, vt + 4 * slot, (sym[name] | 1) - (ROM_BASE + vt))
    for vt, want, name in ((0x4C384, 0x08012D8B, 'state_a'), (0x4BEF0, 0x08012DEF, 'state_b'), (0x4C790, 0x08013023, 'state_c'), (0x4C3A8, 0x080131BB, 'state_d')):
        if ROM_BASE + vt + struct.unpack_from('<i', rom, vt + 8)[0] != want:
            sys.exit('state vtable changed at 0x%X' % vt)
        struct.pack_into('<i', rom, vt + 8, (sym[name] | 1) - (ROM_BASE + vt))
    if rom[0x3C344C:0x3C348C] != clean[0x3C344C:0x3C348C]:
        sys.exit('melee rectangles moved')
    IN, OUT_SITE = 0x1C5F2, 0x1C2D2
    if rom[IN:IN + 10] != bytes.fromhex('0e202875301cff305130') or rom[OUT_SITE:OUT_SITE + 8] != bytes.fromhex('0a202875301cf030'):
        sys.exit('Great Saiyaman code changed')
    rom[IN:IN + 10] = bytes.fromhex('0149fe460847') + struct.pack('<I', sym['saiyaman_hook_in'] | 1)
    rom[OUT_SITE:OUT_SITE + 12] = bytes.fromhex('0149fe460847') + struct.pack('<I', sym['saiyaman_hook_out'] | 1) + bytes.fromhex('c046')
    patch_slot_read(rom, sym)
    hud_icon_hook(rom, sym)
    vt = sym['spirit_vt'] - ROM_BASE                      # 0 delete, 2 update every frame, others do nothing
    for k, name in enumerate(('spirit_destroyed', 'spirit_nop', 'spirit_update', 'spirit_nop', 'spirit_nop', 'spirit_nop')):
        struct.pack_into('<i', rom, vt + 4 * k, (sym[name] | 1) - (ROM_BASE + vt))
    # The native table, moved and grown to the 256 a script's u8 can name: retail's 248 stay as they are (equipment's effect scripts use
    # 0xDF-0xE8 and 0xF5, the level-up script 0xEA), and the mod's own natives take 0xF8-0xFF.
    tab = (at + len(code) + 3) & ~3
    if any(struct.unpack_from('<I', rom, lit)[0] != ROM_BASE + NATIVES for lit in NATIVE_REFS):
        sys.exit('native table reference moved')
    if set(rom[tab:tab + 1024]) != {0xFF}:
        sys.exit('no room for the native table')
    rom[tab:tab + 4 * 248] = clean[NATIVES:NATIVES + 4 * 248]
    for lit in NATIVE_REFS: struct.pack_into('<I', rom, lit, ROM_BASE + tab)
    import zone26
    mine = {JOIN_NATIVE: 'party_join', zone26.ADD_ZENIE: 'add_zenie', zone26.MORE_GET: 'more_get', BOMB_FX: 'bomb_fx', BOMB_AT: 'bomb_at',
            zone26.BALL_NATIVE: 'ball_here', zone26.TOUR_PICK: 'tour_pick', zone26.TOUR_GET: 'tour_get'}
    if sorted(mine) != list(range(0xF8, 0x100)): sys.exit('mod natives: %s' % sorted(mine))
    for n, name in mine.items(): struct.pack_into('<I', rom, tab + 4 * n, sym[name] | 1)
    for n, name in ((zone26.LADDER, 'ladder'), (zone26.MORE_PUT, 'more_put'), (zone26.WISH_NATIVE, 'wish_power')):     # retail natives no script calls
        struct.pack_into('<I', rom, tab + 4 * n, sym[name] | 1)
    for n, name, was in ((0xA4, 'skill_add', 0x08002AB7), (0xA5, 'skill_remove', 0x08002AE5), (0xA6, 'skill_replace', 0x08002B13),    # the skill book keeps in step
                         (0xA8, 'fusion_native', 0x08002EE3)):      # the fusion: Gogeta's own progress kept, Super Saiyan 4 Gogeta (Nov 12)
        if struct.unpack_from('<I', rom, tab + 4 * n)[0] != was: sys.exit('native 0x%X changed' % n)
        struct.pack_into('<I', rom, tab + 4 * n, sym[name] | 1)
    # The Potara's scene (outfit.c potara_use, one event list per pair): a flash, the fused fighter's look (as the story's Potara scene
    # sets Vegito's), the game's fusion native (him, who started it, the two of them, his time), he plays, and the flash fades.
    import bfscript
    if POTARA_PAIRS != ((6, 0, 4),): sys.exit('outfit.c potara_pairs: keep it as POTARA_PAIRS')
    potara_at = tab + 1024                # (add_eraser's space starts after them)
    for k, (fused, a, b) in enumerate(POTARA_PAIRS):
        code_ = bfscript.asm('''    call 0x7A(10)
    pushn %d, %d
    call 0x9D
    push %d
    call 0x15
    call 0x15
    push %d
    call 0x15
    sub
    pushn %d
    call 0xA8
    call 0x95(%d)
    call 0x7B(10)
    end
''' % (fused, POTARA_LOOK, fused, a + b, POTARA_SECONDS, fused))
        step = (potara_at + 3) & ~3; lst = (step + 3 + len(code_) + 3) & ~3; potara_at = lst + 8
        if set(rom[step:potara_at]) != {0xFF}: sys.exit('no room for the Potara scene')
        rom[step:step + 3 + len(code_)] = struct.pack('<HB', 1, 0) + bytes(code_)          # step 1, a code block
        struct.pack_into('<II', rom, lst, ROM_BASE + step, 0)                                # the list: that step, then the end
        struct.pack_into('<I', rom, sym['potara_list'] - ROM_BASE + 4 * k, ROM_BASE + lst)
    SKILL_TAB = 0x4B024                  # the pause menu's Skills tab: setup (slot 1) learns what play has earned, keys (slot 10) swap with SELECT
    for slot, want, name in ((1, 0x080171A9, 'skilltab_setup'), (10, 0x080175FD, 'skilltab_keys')):
        if ROM_BASE + SKILL_TAB + struct.unpack_from('<i', rom, SKILL_TAB + 4 * slot)[0] != want: sys.exit('Skills tab vtable changed')
        struct.pack_into('<i', rom, SKILL_TAB + 4 * slot, (sym[name] | 1) - (ROM_BASE + SKILL_TAB))
    # The Skills tab shows two rows of two (+0x11C the first shown, +0x120 the cursor). Its draw (sub_08017350) kept the first shown no more
    # than 4 before the cursor's row, so with six skills the cursor on 5 or 6 sat in a third row off the window (Nov 10, the owner: "you can't
    # scroll down to view the other 2 or swap them"; retail fighters hold four). 2: the cursor's row is always the second shown.
    if rom[0x17392:0x17394] != b'\x04\x39': sys.exit('Skills tab scroll changed')
    rom[0x17392] = 0x02
    if '--trailer' in sys.argv: struct.pack_into('<I', rom, tab + 4 * 0xD8, sym['trailer_warp'] | 1)
    if '--trailer' in sys.argv: struct.pack_into('<I', rom, tab + 4 * 0xCA, sym['trailer_slot'] | 1)
    row = SKILLS + 24 * SPIRIT_SKILL                     # an unused skill row: its stubs become the Spirit Bomb
    if struct.unpack_from('<II', rom, row + 4) != (0x08019D25, 0x08019D29):
        sys.exit('skill row %d is in use' % SPIRIT_SKILL)
    struct.pack_into('<HHII', rom, row, SPIRIT_NAME, SPIRIT_NAME + 3, sym['spirit_usable'] | 1, sym['spirit_use'] | 1)
    rom[row - 8:row] = rom[SKILLS + 24 * 15 - 8:SKILLS + 24 * 15]       # the Kamehameha's icons; no level (0xFF, as the stub had)
    row = SKILLS + 24 * 20                               # Super Saiyan's use goes up to Super Saiyan 2 where a form has one; Super Saiyan 3 waits for it
    if struct.unpack_from('<II', rom, row + 4) != (0x0801A4C5, 0x0801A513) or struct.unpack_from('<I', rom, SKILLS + 24 * 22 + 4)[0] != 0x0801A55F:
        sys.exit('Super Saiyan skill rows changed')
    struct.pack_into('<II', rom, row + 4, sym['ss_can'] | 1, sym['ss_use'] | 1)    # no Super Saiyan in Kaioken
    rom[row - 12] = rom[SKILLS + 24 * 22 - 12] = 2            # Super Saiyan and 3 show a level: their mastery (outfit.c mastery_level)
    if struct.unpack_from('<I', rom, SKILLS + 24 * 15 + 8)[0] != 0x0801A35B: sys.exit('Kamehameha use changed')
    struct.pack_into('<I', rom, SKILLS + 24 * 15 + 8, sym['kame_use'] | 1)      # counts Goku's uses towards the Super Kamehameha
    struct.pack_into('<I', rom, SKILLS + 24 * 22 + 4, sym['ss3_can'] | 1)
    if struct.unpack_from('<I', rom, SKILLS + 24 * 22 + 8)[0] != 0x0801A5BD: sys.exit('Super Saiyan 3 use changed')
    struct.pack_into('<I', rom, SKILLS + 24 * 22 + 8, sym['ss3_use'] | 1)
    # The flag array runs into other bit arrays: map rooms visited at G+0x8D (flag 448 up) and Scouter entries at G+0xC5 . Custom flags live in their gaps: see zone26.py.
    rooms = max(struct.unpack_from('<H', rom, struct.unpack_from('<I', rom, struct.unpack_from('<I', rom, 0x74C948 + 4 * w)[0] - ROM_BASE + 0x18 + 4 * i)[0] - ROM_BASE + 2)[0]
                for w in range(0x37) for i in range(struct.unpack_from('<i', rom, struct.unpack_from('<I', rom, 0x74C948 + 4 * w)[0] - ROM_BASE + 0x14)[0]))
    if rooms >= 410:
        sys.exit('map rooms now reach flag %d' % (448 + rooms))
    HEAP = 0x3D4D0                   # the heap's setup: heap_init replaces it, keeping the top of work RAM out of the heap
    if rom[HEAP:HEAP + 8] != bytes.fromhex('97489849984a0860') or struct.unpack_from('<I', rom, 0x3D738)[0] != 0xFDFE:
        sys.exit('heap setup changed')
    rom[HEAP:HEAP + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['heap_init'] | 1)
    WRITE = 0x3FBDE                  # the EEPROM write: save_write replaces it. The address isn't word-aligned, so the literal starts 10 bytes in
    if rom[WRITE:WRITE + 14] != bytes.fromhex('f8b50068171c0e1c1d1c002825d0'):
        sys.exit('EEPROM write changed: %s' % rom[WRITE:WRITE + 14].hex())
    rom[WRITE:WRITE + 14] = bytes.fromhex('10b4014ca44610bc6047') + struct.pack('<I', sym['save_write'] | 1)
    if FLASH_SAVE:                         # the 64 KB flash save (outfit.c FLASH_SAVE); its start-up read replaces the EEPROM's
        INIT = 0x3FB7C
        if rom[INIT:INIT + 8] != bytes.fromhex(FLASH_INIT_WAS): sys.exit('EEPROM start-up read changed: %s' % rom[INIT:INIT + 8].hex())
        rom[INIT:INIT + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['save_init'] | 1)
    for vt, slot, want, name in ((0x4AEF8, 0x28, 0x0802084D, 'beam_update'), (0x4C9F0, 0x84, 0x0804F8C9, 'player_input'), (0x4D8A0, 0x10, 0x08027A75, 'minimap_draw'), (0x4C9F0, 0x24, 0x08010DDF, 'guard_msg')):     # every beam's update, the player's keys, the flight map's mini-map, the player's hits
        if ROM_BASE + vt + struct.unpack_from('<i', rom, vt + slot)[0] != want:
            sys.exit('vtable changed at 0x%X' % (vt + slot))
        struct.pack_into('<i', rom, vt + slot, (sym[name] | 1) - (ROM_BASE + vt))
    DAMAGE = 0xE9D8                  # Combat_Damage's first 8 bytes: combat_orig runs them, then comes back
    if rom[DAMAGE:DAMAGE + 8] != bytes.fromhex('f0b5061c0c1c0831'):
        sys.exit('Combat_Damage changed: %s' % rom[DAMAGE:DAMAGE + 8].hex())
    rom[DAMAGE:DAMAGE + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['combat_hook'] | 1)
    ssj4_ki_hooks(rom, sym)
    buu_merge_hook(rom, sym)
    end, art = add_eraser(rom, clean, sym, (potara_at + 3) & ~3, art)    # after the row edits above: it moves the skill table (and after the Potara's scene)
    i = rom.find(bytes.fromhex('092c'), 0x4C70, 0x4C84)    # Select Game draws 8 characters, not the guest slot: Broly's size covered the text
    if i < 0:
        sys.exit('Select Game party loop changed')
    rom[i:i + 2] = bytes.fromhex('082c')
    return end, art


BEAM_POSE = 31                   # outfit.c BEAM_POSE: the actor slot a Kamehameha-code move uses when the fighter's slot 18 can't carry it
KAME_CODE = (15, GALICK_SKILL, TENX_SKILL, SUPER_KAME_SKILL)
KAME_GUESTS = ('krillin', 'tien', 'yamcha', 'krillin_kaioken', 'tien_kaioken', 'yamcha_kaioken', 'roshi', 'roshi_max', 'future_trunks', 'future_trunks_ss', 'goku_black', 'goku_rose')


# Vegeta in Saiyan armour (LoG2's figures): slot 18 is LoG2's own firing animation, a slash with arcs, so his Galick Gun threw punches (Nov 10, the
# owner: "Why is vegeta fucking punching while shooting the galick gun and not holding his hands out normally like the kamehameha frames do").
# Each gets a Galick Gun pose as BF's Vegeta does (beam_poses), from his own frames: the charge, then both hands out.
ARMOUR_GALICK = ('vegeta_armor', 'vegeta_armor_ss', 'vegeta_armor_ss2', 'vegeta_armor_ssb')
# The side push: his ki blast's arm out (slot 19 frame 2, LoG2 animation 5 frame 2) with the far fist gone from his back, (y, x): (was, now):
# the bodysuit's blues there instead
ARMOUR_FIST = {(18, 18): (115, 159), (19, 18): (120, 159), (19, 19): (115, 159), (20, 18): (116, 159), (20, 19): (118, 161), (20, 20): (115, 159),
               (21, 18): (120, 159), (21, 19): (118, 159), (21, 20): (115, 157), (22, 18): (115, 157), (22, 19): (115, 157)}
ARMOUR_FAR = (1, 3)                 # and the far arm laid under the near one: its glove and sleeve one pixel back and three down,
ARMOUR_DARK = {120: 118, 119: 117, 118: 117, 117: 116, 161: 159}    # a shade darker, seen only where nothing is in front of it


ARMOUR_NECK = 17                    # front views: his head is the rows above this (LoG2's frames of him all stand the same there)


def armour_pose(rom, rec, base, put):
    """The Galick Gun pose (3 frames: the charge, then the push twice) of an armour Vegeta figure (record `rec`), from its own frames.
    Side: the ki blast's wind-up (slot 19 frame 0), then its arm out with the other arm under it (two_hands). Front: LoG2's ki charge (base Vegeta's
    slot 24, record `base`: LoG2's Super Saiyan has none): hands together, then at his chest with the ki in them, under the figure's own head (its
    stance's). Back: the wind-up, then the power-up's back (slot 13 frame 0), arms out of sight in front of him. Frames keep their piece; only the
    tiles are new."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    def fp(slot, i, v, rec=rec):
        a = u(rec + 0x54 + 4 * slot) - ROM_BASE if slot < rom[rec] else -ROM_BASE
        if a < 0 or i >= u(a): sys.exit('armour Galick pose: the figure has no slot %d frame %d' % (slot, i))
        return u(a + 4 + 16 * i + 4 * v)
    def retiled(f, img):
        o = f - ROM_BASE
        if u(o) != 1: sys.exit('armour Galick pose: a frame of %d pieces' % u(o))
        h, w = img.shape
        data = img.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
        body = bytearray(rom[o:o + 20]); struct.pack_into('<I', body, 16, put(struct.pack('<II', 0, len(data)) + data))
        return body
    def two_hands(img):
        out = img.copy()
        for (y, x), (was, now) in ARMOUR_FIST.items():
            if img[y, x] != was: sys.exit('armour Galick pose: the ki blast frame is not as drawn at (%d, %d): %d' % (y, x, img[y, x]))
            out[y, x] = now
        dx, dy = ARMOUR_FAR; far = np.zeros(img.shape, bool)
        for y in range(13, 20):                    # the near arm: glove and sleeve, left of his shoulder
            for x in range(1, 12):
                if img[y, x] and not out[y + dy, x + dx]:
                    out[y + dy, x + dx] = ARMOUR_DARK.get(int(img[y, x]), img[y, x]); far[y + dy, x + dx] = True
        t = np.pad(out == 0, 1)
        edge = far & (t[:-2, 1:-1] | t[2:, 1:-1] | t[1:-1, :-2] | t[1:-1, 2:])
        out[edge] = np.where(np.isin(out[edge], (157, 159, 161)), 157, 115)     # its outline: the sleeve's or the glove's
        return out
    def view(slot, i, v, edit=None):               # a frame of his, as it is or edited
        f = fp(slot, i, v)
        return put(bytes(retiled(f, edit(sprites.frame_image(rom, f))))) if edit else f
    def side(slot, i, edit=None):                  # views 2 and 3 (3 is 2 flipped: the same tiles)
        a = view(slot, i, 2, edit)
        if not edit: return a, fp(slot, i, 3)
        b = bytearray(rom[fp(slot, i, 3) - ROM_BASE:fp(slot, i, 3) - ROM_BASE + 20]); struct.pack_into('<I', b, 16, u(a - ROM_BASE + 16))
        return a, put(bytes(b))
    def front(i):
        body, head = fp(24, i, 0, base), fp(0, 0, 0)
        if rom[body - ROM_BASE + 4:body - ROM_BASE + 12] != rom[head - ROM_BASE + 4:head - ROM_BASE + 12]: sys.exit('armour Galick pose: front frames of other sizes')
        out = sprites.frame_image(rom, body).copy(); out[:ARMOUR_NECK] = sprites.frame_image(rom, head)[:ARMOUR_NECK]
        return put(bytes(retiled(head, out)))
    def lone(img):                                 # without the power-up's sparks off his body
        from scipy import ndimage
        lab, n = ndimage.label(img > 0)
        if n < 2: return img
        return np.where(lab == np.bincount(lab.ravel())[1:].argmax() + 1, img, 0).astype(img.dtype)
    charge = [front(0), view(19, 0, 1), *side(19, 0)]
    push = [front(1), view(13, 0, 1, lone), *side(19, 2, two_hands)]
    return put(struct.pack('<I', 3) + struct.pack('<12I', *charge, *push, *push))


# Master Roshi's Kamehameha (16:28, the owner: "fix roshis kamehameha frames too"): his figure is Krillin's (LoG2 animation 5, the ki throw, in
# slot 18) with his head and clothes, so he charged with a hand up behind his head and fired one-handed, his other hand thrown back. He gets a
# Kamehameha pose of his own (slot 31; outfit.c kame_use plays it): side, both hands cupped at his back hip, then both pushed out; front, the
# throw's crouch with his hands at his belly; back, his back with his arms down (the throw's back raises an arm). (y, x) in slot 18 frame 2's
# side view, checked pixel by pixel: the build stops if the frame differs.
ROSHI_KAME = ('roshi', 'roshi_max')
ROSHI_NEAR = (14, 21, 0, 14)        # the near arm, thrown out in front: rows 14-20, columns 0-13
ROSHI_BACK = {(16, 26): 16, (17, 26): 16, (18, 24): 213, (18, 25): 212, (18, 26): 16, (19, 24): 16, (19, 25): 16}    # the far hand behind him
ROSHI_HANDS = ((18, 22, (16, 212, 213, 212, 16)), (19, 22, (16, 213, 214, 213, 16)), (20, 22, (16, 212, 213, 212, 16)), (21, 23, (16, 16, 16)))   # cupped at his hip
ROSHI_FAR = (1, 2)                  # the far arm laid under the near one, as the armour Vegeta's (ARMOUR_DARK)


def roshi_pose(rom, rec, put):
    """Master Roshi's Kamehameha pose (3 frames: the charge, then the push twice), from his own slot 18 (see ROSHI_KAME)."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    def fp(slot, i, v):
        a = u(rec + 0x54 + 4 * slot) - ROM_BASE
        return u(a + 4 + 16 * i + 4 * v)
    if u(fp(18, 2, 2) - ROM_BASE) != 1: sys.exit('Roshi Kamehameha pose: a frame of more than one piece')
    base = sprites.frame_image(rom, fp(18, 2, 2)).copy()
    for (y, x), was in ROSHI_BACK.items():
        if base[y, x] != was: sys.exit('Roshi Kamehameha pose: slot 18 frame 2 is not as drawn at (%d, %d): %d' % (y, x, base[y, x]))
    base[[y for y, _ in ROSHI_BACK], [x for _, x in ROSHI_BACK]] = 0
    y0, y1, x0, x1 = ROSHI_NEAR
    charge = base.copy(); charge[y0:y1, x0:x1] = 0
    for y, x, row in ROSHI_HANDS: charge[y, x:x + len(row)] = row
    push = base.copy(); dx, dy = ROSHI_FAR; far = np.zeros(push.shape, bool)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if base[y, x] and y + dy < push.shape[0] and not push[y + dy, x + dx]:
                push[y + dy, x + dx] = ARMOUR_DARK.get(int(base[y, x]), base[y, x]); far[y + dy, x + dx] = True
    t = np.pad(push == 0, 1)
    edge = far & (t[:-2, 1:-1] | t[2:, 1:-1] | t[1:-1, :-2] | t[1:-1, 2:])
    push[edge] = 16
    def side(img):                                 # views 2 and 3 (3: the same tiles flipped), on slot 18 frame 2's piece
        o = fp(18, 2, 2) - ROM_BASE; h, w = img.shape
        data = img.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes(); tiles = put(struct.pack('<II', 0, len(data)) + data)
        out = []
        for v in (2, 3):
            b = bytearray(rom[fp(18, 2, v) - ROM_BASE:fp(18, 2, v) - ROM_BASE + 20]); struct.pack_into('<I', b, 16, tiles); out.append(put(bytes(b)))
        return out
    c = [fp(18, 1, 0), fp(18, 0, 1), *side(charge)]
    p = [fp(18, 2, 0), fp(18, 0, 1), *side(push)]
    return put(struct.pack('<I', 3) + struct.pack('<12I', *c, *p, *p))


def beam_poses(rom, put, put_art):
    """The Kamehameha's code (behaviour 0x0804D9F8) shows frames 0-2 of the fighter's slot 18: 0 while charging, then 1 and 2 by turns. Vegeta's figures
    hold his Big Bang there, two frames, so his Galick Gun drew a third frame from past the animation: junk over other sprites' tiles. Each such figure
    gets a pose of its own in slot BEAM_POSE (outfit.c beam_pose): his ki blast's wind-up (slot 3, frame 0), then Final Flash's push with both hands
    (slot 19, frame 3). Then every form that can hold one of those moves is checked."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    fm = json.load(open(OUT + '/_forms.json')); total = max(fm.values()) + 1
    def record(f):
        char = struct.unpack_from('<H', rom, SPACE + FORM_SIZE * f + 0x0E)[0]
        return (char, u(ACTORS_AT + 4 * (char - 9)) - ROM_BASE) if char >= 9 else (char, None)
    def frames(rec, slot):
        if slot >= rom[rec] or not u(rec + 0x54 + 4 * slot): return 0
        return u(u(rec + 0x54 + 4 * slot) - ROM_BASE)
    made = {}
    for f in range(total):
        char, rec = record(f)
        if rec is None or rom[SPACE + FORM_SIZE * f + 0x0C] != 4 or frames(rec, 18) >= 3 or char in made: continue
        if frames(rec, 3) < 1 or frames(rec, 19) < 4:
            sys.exit('form %d: no ki blast or Final Flash frames for a Galick Gun pose' % f)
        blast, flash = u(rec + 0x54 + 12) - ROM_BASE, u(rec + 0x54 + 76) - ROM_BASE
        pose = put(struct.pack('<I', 3) + rom[blast + 4:blast + 20] + rom[flash + 4 + 48:flash + 4 + 64] * 2)
        n = rom[rec]; new = bytearray(rom[rec:rec + 0x54 + 4 * n]) + bytes(4 * (BEAM_POSE + 1 - n))
        new[0] = BEAM_POSE + 1; struct.pack_into('<I', new, 0x54 + 4 * BEAM_POSE, pose)
        struct.pack_into('<I', rom, ACTORS_AT + 4 * (char - 9), put(bytes(new)))
        made[char] = f
    armour = {}
    base = record(fm[ARMOUR_GALICK[0]])[1]
    for name in ARMOUR_GALICK:
        char, rec = record(fm[name])
        if char in made or char in armour: continue
        pose = armour_pose(rom, rec, base, put_art)       # (with the sprites: the code area is full)
        n = rom[rec]; new = bytearray(rom[rec:rec + 0x54 + 4 * n]) + bytes(4 * (BEAM_POSE + 1 - n))
        new[0] = BEAM_POSE + 1; struct.pack_into('<I', new, 0x54 + 4 * BEAM_POSE, pose)
        struct.pack_into('<I', rom, ACTORS_AT + 4 * (char - 9), put_art(bytes(new)))
        armour[char] = name
    made.update(armour)
    char, rec = record(fm[ROSHI_KAME[0]])
    if any(record(fm[n])[0] != char for n in ROSHI_KAME): sys.exit('Roshi Kamehameha pose: his forms are on different figures')
    pose = roshi_pose(rom, rec, put_art)
    n = rom[rec]; new = bytearray(rom[rec:rec + 0x54 + 4 * n]) + bytes(4 * (BEAM_POSE + 1 - n))
    new[0] = BEAM_POSE + 1; struct.pack_into('<I', new, 0x54 + 4 * BEAM_POSE, pose)
    struct.pack_into('<I', rom, ACTORS_AT + 4 * (char - 9), put_art(bytes(new)))
    made[char] = fm[ROSHI_KAME[0]]
    print('Galick Gun pose for figures', sorted(made))
    books = {c: s for c, s in SKILL_BOOK.items() if set(s) & set(KAME_CODE)}
    for f in range(total):
        owner = rom[SPACE + FORM_SIZE * f + 0x0C]
        if owner in books or f in [fm[g] for g in KAME_GUESTS if g in fm]:
            char, rec = record(f)
            # Goku's own figures all carry a three-frame Kamehameha but form 1, a 16-slot figure (likely only for scenes), which retail leaves as it is
            if rec is not None and frames(rec, 18) < 3 and not frames(rec, BEAM_POSE) and owner != 0:
                sys.exit('form %d (figure %d) can hold a Kamehameha-code move but its slot 18 has %d frames' % (f, char, frames(rec, 18)))


# Kamehameha-code moves (and the Electric Kamehameha's) on the LoG2 figures: slot BEAM_POSE (outfit.c beam_pose), the fist in while charging,
# then the arm out (their slot 3: LoG2's ki frames). Slot 18 (Big Bang's code, Eraser Cannon, Blitz, Destructo Disc: frames 0 and 1 by turns
# while held) is the arm out only (actors.json): with the fist in as frame 0 it flickered between the two (Nov 10, the owner: Android 17's and
# 18's "blast attack frames fucked", Krillin's "Destructo disc frames fucked"). Armour Vegeta's Final Flash (slot 19: frames 0-1 charging, 2,
# then 3-4 firing) is his Galick Gun pose's frames (approved Nov 10): the charge, then both hands out; it was LoG2's one-armed ki frames.
SS2_POSE = 30                    # outfit.c SS2_POSE: Goku's Super Saiyan figures' change into Super Saiyan 2
FIST_POSE = 29                   # outfit.c FIST_POSE: Goku's Super Saiyan 3 figures' Dragon Fist Explosion
SSJ3_GOKU = (5, 6, 7, 8)         # the original game's Super Saiyan 3 Goku forms (figures 111 and 112: alive and with his halo, each twice); Kid Goku's is by name
BEAM_FORMS = ('android13', 'krillin', 'krillin_kaioken', 'tien', 'tien_kaioken', 'future_trunks', 'future_trunks_ss', 'android17', 'super17', 'android18',
              'gohan_armor', 'gohan_armor_ss', 'gohan_armor_ss2', 'trunks_armor', 'trunks_armor_ss', 'trunks_armor_ss2', 'teen_gohan', 'teen_gohan_ss', 'teen_gohan_ss2',
              'kid_buu', 'majin_buu')    # the Buus' Kamehameha (Nov 10): their slot 18 is a boss move (Kid Buu's rush, Majin Buu's antenna beam)
# The rule for a figure with no beam frames of its own (Nov 10, 21:20, the owner: "Never use guards as an attack frame, use ki blast frames
# but dont loop them just make it one smooth sustained transition on beams if none exist"): the ki blast's wind-up while it charges, then
# its arm out, the same frame twice (the Kamehameha's code shows frames 1 and 2 in turn while the beam is out), so it is held, not looped.
# (A try at Majin Buu's guard for the charge, his hands by the ball, went out with that.) test_frames checks both halves.


def held_poses(rom, put_art):
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    fm = json.load(open(OUT + '/_forms.json'))
    def record(name):
        char = struct.unpack_from('<H', rom, SPACE + FORM_SIZE * fm[name] + 0x0E)[0]
        return char, u(ACTORS_AT + 4 * (char - 9)) - ROM_BASE
    def frames(rec, slot):
        ap = u(rec + 0x54 + 4 * slot) if slot < rom[rec] else 0
        if not ap: return []
        return [[u(ap - ROM_BASE + 4 + 16 * k + 4 * v) for v in range(4)] for k in range(u(ap - ROM_BASE))]
    done = set()
    for name in BEAM_FORMS:
        char, rec = record(name)
        if char in done: continue
        if frames(rec, BEAM_POSE): sys.exit('%s: already has a beam pose' % name)
        ki = frames(rec, 3)
        if len(ki) < 3: sys.exit('%s: no three ki frames' % name)
        pose = put_art(struct.pack('<I', 3) + b''.join(struct.pack('<4I', *f) for f in (ki[0], ki[2], ki[2])))
        n = rom[rec]; new = bytearray(rom[rec:rec + 0x54 + 4 * n]) + bytes(4 * (BEAM_POSE + 1 - n))
        new[0] = BEAM_POSE + 1; struct.pack_into('<I', new, 0x54 + 4 * BEAM_POSE, pose)
        struct.pack_into('<I', rom, ACTORS_AT + 4 * (char - 9), put_art(bytes(new)))
        done.add(char)
    # Goku's change from Super Saiyan to 2 (outfit.c to_ss2, slot SS2_POSE): his Super Saiyan figures' slot 10 is BF's change into Super Saiyan 3,
    # so going up to 2 grew his hair long. His power-up's crouch twice, arms up eight times, his stance, front in every view, as slot 10's 11.
    for f in (3, 4):                                                   # Super Saiyan Goku, alive and with his halo (actors 109, 110)
        char = struct.unpack_from('<H', rom, SPACE + FORM_SIZE * f + 0x0E)[0]; rec = u(ACTORS_AT + 4 * (char - 9)) - ROM_BASE
        up, stand = frames(rec, 13), frames(rec, 0)
        if len(up) < 2 or len(frames(rec, 10)) != 11: sys.exit('form %d: no power-up or no 11-frame change' % f)
        pose = put_art(struct.pack('<I', 11) + b''.join(struct.pack('<4I', *[fr[0]] * 4) for fr in [up[0]] * 2 + [up[1]] * 8 + [stand[0]]))
        n = rom[rec]; new = bytearray(rom[rec:rec + 0x54 + 4 * n]) + bytes(4 * max(0, SS2_POSE + 1 - n))
        new[0] = max(n, SS2_POSE + 1); struct.pack_into('<I', new, 0x54 + 4 * SS2_POSE, pose)
        struct.pack_into('<I', rom, ACTORS_AT + 4 * (char - 9), put_art(bytes(new)))
    for name in ARMOUR_GALICK:
        char, rec = record(name)
        if char in done: continue
        g = frames(rec, BEAM_POSE)
        if len(g) != 3: sys.exit('%s: no Galick Gun pose' % name)
        struct.pack_into('<I', rom, rec + 0x54 + 4 * 19, put_art(struct.pack('<I', 5) + b''.join(struct.pack('<4I', *f) for f in (g[0], g[0], g[1], g[1], g[2]))))
        done.add(char)


def fist_poses(rom, put_art):
    """Dragon Fist Explosion on Goku's Super Saiyan 3 figures (Nov 11, the owner: "give ssj3 Goku access to the dragon fist explosion"):
    the move's code (0x0801ABBE) shows the fighter's slot 19 by frame number, 0 to 3 as it winds up and then 2 and 3 in turn while the
    dragon is out, and their slot 19 is Instant Transmission's three frames. Each gets a pose of its own in slot FIST_POSE (outfit.c
    dragon_use), as Super Saiyan 4 Goku's slot 19 is built: his stance, his ki blast's wind-up, then its arm out twice (held, not
    looped: the owner's Nov 10 rule for a figure with no frames of its own for a move)."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    fm = json.load(open(OUT + '/_forms.json')); total = max(fm.values()) + 1
    forms = SSJ3_GOKU + (fm['kid_goku_ssj3'],)
    def frames(rec, slot):
        ap = u(rec + 0x54 + 4 * slot) if slot < rom[rec] else 0
        if not ap: return []
        return [[u(ap - ROM_BASE + 4 + 16 * k + 4 * v) for v in range(4)] for k in range(u(ap - ROM_BASE))]
    figures = {struct.unpack_from('<H', rom, SPACE + FORM_SIZE * f + 0x0E)[0] for f in forms}
    for f in range(total):                           # no Super Saiyan 3 Goku form left out: any form of his on one of these figures
        row = rom[SPACE + FORM_SIZE * f:SPACE + FORM_SIZE * (f + 1)]
        if row[0x0C] == 0 and struct.unpack_from('<H', row, 0x0E)[0] in figures and f not in forms:
            sys.exit('form %d is a Super Saiyan 3 Goku and not in SSJ3_GOKU: he could not use Dragon Fist Explosion in it' % f)
    for char in sorted(figures):
        rec = u(ACTORS_AT + 4 * (char - 9)) - ROM_BASE
        stand, ki = frames(rec, 0), frames(rec, 3)
        if not stand or len(ki) < 3 or frames(rec, FIST_POSE): sys.exit('figure %d: no stance or three ki frames for a Dragon Fist pose, or slot %d taken' % (char - 9, FIST_POSE))
        pose = put_art(struct.pack('<I', 4) + b''.join(struct.pack('<4I', *fr) for fr in (stand[0], ki[0], ki[2], ki[2])))
        n = rom[rec]; new = bytearray(rom[rec:rec + 0x54 + 4 * n]) + bytes(4 * max(0, FIST_POSE + 1 - n))
        new[0] = max(n, FIST_POSE + 1); struct.pack_into('<I', new, 0x54 + 4 * FIST_POSE, pose)
        struct.pack_into('<I', rom, ACTORS_AT + 4 * (char - 9), put_art(bytes(new)))


def front_changes(rom, put_art):
    """Every mod figure's change of form (slot 10, a form with one above it) and power-down (slot 11, a Super Saiyan-class form with one below)
    shows its front in every view, as GT Vegeta's (Nov 10, the owner: "they should all be the same anyways"): the game plays them in whatever
    view the fighter faces, and a side or back view of a change looked like an attack (armour Gohan "lifts his arms", "punches"). test_frames 13."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    fm = json.load(open(OUT + '/_forms.json')); done = set()
    locked = {fm[n] for n in json.load(open('ultimate/locked.json'))['forms']}      # approved figures stay as approved (lib/lock.py)
    import bso_import
    locked |= {fm[n] for n in bso_import.SHEETS if n in fm}                       # and the owner's own every-frame sheets are drawn as he sent them
    for f in range(max(fm.values()) + 1):
        row = rom[SPACE + FORM_SIZE * f:SPACE + FORM_SIZE * f + FORM_SIZE]
        char = struct.unpack_from('<H', row, 0x0E)[0]
        if f < FORM_COUNT or row[0x0C] > 8 or char < 9 + ACTOR_BASE or f in locked: continue
        rec = u(ACTORS_AT + 4 * (char - 9)) - ROM_BASE
        for slot, want in ((10, row[0x16] != 255), (11, row[0] & 1 and row[0x17] != 255)):
            if not want or slot >= rom[rec] or not u(rec + 0x54 + 4 * slot) or (rec, slot) in done: continue
            a = u(rec + 0x54 + 4 * slot) - ROM_BASE; n = u(a)
            frames = [[u(a + 4 + 16 * i + 4 * v) for v in range(4)] for i in range(n)]
            if all(len(set(fr)) == 1 for fr in frames): continue
            struct.pack_into('<I', rom, rec + 0x54 + 4 * slot, put_art(struct.pack('<I', n) + b''.join(struct.pack('<4I', *[fr[0]] * 4) for fr in frames)))
            done.add((rec, slot))


def add_eraser(rom, clean, sym, at, art):
    """Eraser Cannon and SS Deadly Bomber: recoloured copies of Big Bang's two ball animations and icons, each move's parameter table (its last word scales the damage)
    and behaviour, new skill rows, and new UI strings."""
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    one = indexer([i for i in range(1, 256) if i not in artclean.MENU_SLOTS], pal)
    def put(data):
        nonlocal at
        at = (at + 3) & ~3; o = at; rom[o:o + len(data)] = data; at += len(data)
        return ROM_BASE + o
    def put_art(data):                           # tiles: with the sprites, past the code area
        nonlocal art
        art = (art + 3) & ~3; o = art; rom[o:o + len(data)] = data; art += len(data)
        return ROM_BASE + o
    PARAMS, OLD_VT = 0x76ACC0, 0x4D05C                    # Big Bang's table: levels 1 and 2 cyan ball, level 3 gold
    icons = struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 2 + 4)
    rows, strings = {}, []
    for name, skill, power, title, text, tint in NEW_MOVES:
        def recolour(v):
            if v == 0: return 0
            r, g, b = (int(x) for x in pal[v]); top = max(r, g, b); pale = min(r, g, b) / 255
            return one(np.array((top * (tint[0] + tint[1] * pale), top * (tint[2] + tint[3] * pale), top * (tint[4] + tint[5] * pale))).astype(int))
        remap = bytes(recolour(v) for v in range(256)); copies = {}
        def ball(rec):
            """One animation: four facings of 120 bytes, each up to ten {header, attributes, tile data} rows."""
            out = region_rows(clean, bytearray(clean[rec:rec + 480]), remap, put, copies, lambda o, k: (struct.unpack_from('<I', o, k)[0] >> 16 & 255) * (struct.unpack_from('<I', o, k)[0] >> 24 & 255))
            return put(bytes(out))
        if name == 'disc':
            l2u = open(LOG2, 'rb').read()      # USA cart: palette and tiles at the addresses its decomp gives
            l2pal = np.frombuffer(l2u[0x3ECEA4:0x3ECEA4 + 768], np.uint8).reshape(256, 3)
            l2map = bytes(0 if v == 0 else one(l2pal[v]) for v in range(256))
            spin = [put(l2u[t:t + 512].translate(l2map)) for t in (0x6DDA34, 0x6DDC34)]
            def ball(rec, place=((16, 4), (16, 12), (28, 8), (4, 8))):
                """The same rows and timing as Big Bang's ball, showing the two 32x16 frames of the disc in turn."""
                out = bytearray(clean[rec:rec + 480])
                for k in range(0, 480, 12):
                    if struct.unpack_from('<I', out, k + 8)[0]:
                        x, y = place[k // 120]
                        struct.pack_into('<4BII', out, k, x, y, 32, 16, 0x80006000, spin[(k // 12) & 1])
                return put(bytes(out))
        balls = {}; table = sym[name + '_params'] - ROM_BASE
        for i in range(3):
            a, b, rec, strength = struct.unpack_from('<4I', clean, PARAMS + 16 * i)
            balls.setdefault(rec, ball(rec - ROM_BASE))
            struct.pack_into('<4I', rom, table + 16 * i, a, b, balls[rec], int(strength * power[i]))
        vt = sym[name + '_vt'] - ROM_BASE                 # the behaviour's other methods stay Big Bang's: only the start differs
        for k in range(9):
            fn = ROM_BASE + OLD_VT + struct.unpack_from('<i', clean, OLD_VT + 4 * k)[0]
            struct.pack_into('<i', rom, vt + 4 * k, ((sym[name + '_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
        row = bytearray(clean[SKILL_ROWS + 24 * 2:SKILL_ROWS + 24 * 3])
        struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], remap)) for p in icons])
        struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
        struct.pack_into('<I', row, 20, sym[name + '_use'] | 1)
        rows[skill] = bytes(row)
        strings += [put(t.encode('utf-16-le') + b'\0\0') for t in (title, text)]
    # Special Beam Cannon: copies of the Kamehameha's frame records, each {header, attributes, tile data} rows. The core goes pale yellow, the middle gold, and the rim purple.
    BEAM_TINT = {2: (248, 248, 216), 30: (248, 248, 216), 29: (248, 248, 144), 76: (248, 248, 72), 28: (248, 248, 72), 5: (248, 248, 72), 195: (248, 208, 0), 27: (248, 208, 0), 110: (248, 208, 0),
                 75: (168, 48, 224), 109: (168, 48, 224), 74: (112, 24, 168), 4: (112, 24, 168)}
    def beam_colour(v):
        if v == 0: return 0
        return one(np.array(BEAM_TINT.get(v, tuple(pal[v])), dtype=int))
    remap = bytes(beam_colour(v) for v in range(256)); copies = {}
    def frames(o, count):
        return put(bytes(region_rows(clean, bytearray(clean[o:o + 12 * count]), remap, put, copies)))
    BEAM_PARAMS, BEAM_VT = 0x71DA68, 0x4D9F8
    # The beam itself is LoG2's Special Beam Cannon: 7 rows a facing (muzzle 2, body 3, tip 2) laid into BF's 16-row facings (muzzle 0-1, body 3-5 and spare frame 6, tip 7-8 and 10-11).
    # Rows 13-14, a small end piece LoG2 doesn't have, keep the recoloured Kamehameha's. Every level uses this one thin shape.
    l2 = open(LOG2, 'rb').read(); L2_ART = 0x6E4560
    l2pal = np.frombuffer(l2[0x3ECEA4:0x3ECEA4 + 768], np.uint8).reshape(256, 3).astype(int)    # sprite palette in the USA cart
    l2map = bytes(0 if v == 0 else one(l2pal[v]) for v in range(256)); l2tiles = {}
    record = bytearray(rom[frames(struct.unpack_from('<I', clean, BEAM_PARAMS + 12)[0] - ROM_BASE, 64) - ROM_BASE:][:768])
    for facing in range(4):
        for bf, row in ((0, 0), (1, 1), (3, 2), (4, 3), (5, 4), (7, 5), (8, 6), (10, 5), (11, 6)):
            hdr, attr, tiles = struct.unpack_from('<III', l2, L2_ART + 12 * (facing * 7 + row))
            if tiles not in l2tiles:                     # always the whole 256-byte block: a short row still has the engine copy all of it
                t = tiles - ROM_BASE; l2tiles[tiles] = put(l2[t:t + 256].translate(l2map))
            struct.pack_into('<III', record, 12 * (facing * 16 + bf), hdr, attr, l2tiles[tiles])
        struct.pack_into('<I', record, 12 * (facing * 16 + 6) + 8, struct.unpack_from('<I', record, 12 * (facing * 16 + 5) + 8)[0])
    beam_art = put(bytes(record))
    shape, table = {}, sym['beam_params'] - ROM_BASE
    body_at = body_block(frames)
    for i in range(3):
        a, strength, body, head = struct.unpack_from('<4I', clean, BEAM_PARAMS + 16 * i)
        shape.setdefault(body, body_at(body))
        struct.pack_into('<4I', rom, table + 16 * i, a, strength, shape[body], beam_art)
    vt = sym['beam_vt'] - ROM_BASE
    for k in range(9):
        fn = ROM_BASE + BEAM_VT + struct.unpack_from('<i', clean, BEAM_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['beam_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
    row = bytearray(clean[SKILL_ROWS + 24 * 15:SKILL_ROWS + 24 * 16])
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], remap)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 15 + 4)])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['beam_use'] | 1)
    rows[BEAM_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Special Beam Cannon', 'Press the B Button and hold it to charge, then release to fire a thin beam of energy from your fingertips.', 'Android 17', 'Future Trunks')]
    # Full Power Energy Wave and the androids' blue blasts. The hues and the method are Gero's Legacy's (tools/kifx.py); here they're copies, since Gohan and everyone else keep the originals.
    def shifted(hue):
        def colour(v):
            if v == 0: return 0
            h, s, b = colorsys.rgb_to_hsv(*(pal[v] / 255.0))
            if s < 0.12: return v                     # whites and greys stay: the hot core
            return one((np.array(colorsys.hsv_to_rgb(hue, s, b)) * 255).astype(int))
        return bytes(colour(v) for v in range(256))
    green, blue = shifted(125 / 360), shifted(215 / 360)
    WAVE_PARAMS, WAVE_VT, BALL_TILES, BALL_RECS, WAVE_TILES = 0x725018, 0x4E2D8, (0x720864, 0x721164), (0x721164, 0x721218), (0x721218, 0x724718)
    if struct.unpack_from('<I', clean, 0x1AE1C)[0] != ROM_BASE + WAVE_PARAMS:
        sys.exit('wave table moved')
    moved = []                                        # every tile pointer falls in one of these blocks. A frame can have the engine copy more than its width and height say, so whole blocks are copied
    for lo, hi in (BALL_TILES, WAVE_TILES):
        moved.append((lo, hi, put(clean[lo:hi].translate(green))))
    def rebase(p):
        for lo, hi, new in moved:
            if lo <= p - ROM_BASE < hi: return new + p - ROM_BASE - lo
        sys.exit('wave frame outside its tiles: 0x%X' % p)
    def wave_records(lo, hi):
        out = bytearray(clean[lo:hi])
        for k in range(0, hi - lo, 12):
            p = struct.unpack_from('<I', out, k + 8)[0]
            if p: struct.pack_into('<I', out, k + 8, rebase(p))
        return out
    ball_new = put(bytes(wave_records(*BALL_RECS)))
    table = sym['wave_params'] - ROM_BASE
    for i in range(3):
        a, strength, ball_rec, head = struct.unpack_from('<4I', clean, WAVE_PARAMS + 16 * i)
        struct.pack_into('<4I', rom, table + 16 * i, a, strength, ball_new + ball_rec - ROM_BASE - BALL_RECS[0], put(bytes(wave_records(head - ROM_BASE, head - ROM_BASE + 768))))
    vt = sym['wave_vt'] - ROM_BASE
    for k in range(9):
        fn = ROM_BASE + WAVE_VT + struct.unpack_from('<i', clean, WAVE_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['wave_start'] | 1) if k == 0 else (sym['wave_update'] | 1) if k == 2 else fn) - (ROM_BASE + vt))   # (2: the update, outfit.c wave_update)
    row = bytearray(clean[SKILL_ROWS + 24 * 6:SKILL_ROWS + 24 * 7])
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], green)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 6 + 4)])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['wave_use'] | 1)
    rows[WAVE_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Full Power Energy Wave', 'Press the B Button and hold it to charge, then release to fire a wave of green energy.  Hold the B Button to keep firing.')]
    for skill, name, text in ((SUPER13_SKILL, 'Super 13', 'Press the B Button to absorb the cores of Android 14 and Android 15 and become Super 13: attacks hit 1.5x as hard. Press it again to change back.'),
                              (SUPER17_SKILL, 'Super 17', 'Press the B Button to become Super 17: attacks hit 1.5x as hard. Press it again to change back.')):
        row = bytearray(clean[SKILL_ROWS + 24 * 20:SKILL_ROWS + 24 * 21])
        struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
        struct.pack_into('<II', row, 16, sym['super_can'] | 1, sym['super_use'] | 1)
        rows[skill] = bytes(row)
        strings += [put(t.encode('utf-16-le') + b'\0\0') for t in (name, text)]
    # Goku Black. Rose is Super Saiyan's row under its own name (its use is ss_use, as Goku's). The Black Kamehameha is the Kamehameha's code with Black's purple frames,
    # or Rose's pink ones: black_kame_start picks by form. Its icons are the Kamehameha's in Black's purple.
    row = bytearray(rom[SKILLS - 12 + 24 * 20:SKILLS - 12 + 24 * 21]); row[0] = 0xFF      # Rose: no level (Super Saiyan's shows mastery)
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    pink = shifted(325 / 360)                   # Rose's aura and icon: Super Saiyan's, pink
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], pink)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 20 + 4)])
    struct.pack_into('<I', row, 20, sym['rose_use'] | 1)
    rows[ROSE_SKILL] = bytes(row)
    red = shifted(4 / 360)                      # Super Saiyan 4's aura: Super Saiyan's, red
    ssb_blue = shifted(200 / 360)               # Super Saiyan Blue's
    def whitened(v):                            # Max Power's aura: Super Saiyan's, white with a cool edge
        if v == 0: return 0
        c = pal[v].astype(int); g = int(c.mean())
        return one(np.array((min(255, g + 70), min(255, g + 80), min(255, g + 100))))
    white = bytes(whitened(v) for v in range(256))
    ssb_aura = bytes(0 if v == 0 else one(np.array(SSB_AURA[tuple(int(c) for c in pal[v])])) if tuple(int(c) for c in pal[v]) in SSB_AURA else v for v in range(256)) if LOOK170 else ssb_blue
    if LOOK170:                                 # Blue's glow (outfit.c glow_tick): drawn by lib/ssb_glow.py, the style the owner picks (BFU_GLOW)
        import ssb_glow
        style = GLOW_STYLE
        rims = ssb_glow.STYLES[style](); bands = ssb_glow.band_only(ssb_glow.BANDS[style]()) if style in ssb_glow.BANDS else None
        ptrs, band, band_at, trans = [], [], [], []
        def field_aura(tint):                    # the power-up's field aura (three 32x32 frames), in a power-up's tint
            out = []
            for k in range(3):
                t = struct.unpack_from('<I', clean, 0x752D28 + 12 * k + 8)[0] - ROM_BASE
                out.append(np.frombuffer(clean[t:t + 1024].translate(tint), np.uint8).reshape(4, 4, 8, 8).transpose(0, 2, 1, 3).reshape(32, 32))
            return out
        for colours, tint in [(ssb_glow.COLOURS, ssb_aura)] + list(zip(GLOW_KINDS[1:], (red, pink, white)) if GLOW_MORE else ()):     # outfit.c GLOW_KINDS: each kind's
            lut = np.zeros(16, np.uint8)                                                                                     # frames, then the next's
            for k, c in colours.items(): lut[k] = one(np.array(c))
            ptrs += [put_art(ssb_glow.tiles(lut[f])) for f in rims]
            last_lut = lut
            trans += [put_art(ssb_glow.tiles(f)) for f in ssb_glow.transition(field_aura(tint), lut, rims)]     # (Blue's power-up aura, God's
                                                                                                                # Super Saiyan 4 red one, Rose's pink)
            if bands:                              # the see-through band: 4 bpp, one colour (glow_band_colour), its own sprite
                at_ = glow_band_colour(clean, colours[14]); band_at.append(at_)
                band += [put_art(ssb_glow.tiles4(f, at_ & 15)) for f in bands]
        struct.pack_into('<%dI' % len(ptrs), rom, sym['glow_frames'] - ROM_BASE, *ptrs)
        struct.pack_into('<%dI' % len(trans), rom, sym['glow_trans'] - ROM_BASE, *trans)
        if GLOW_MORE:                            # Full Power Mystic's glow fades out after three seconds (the last kind's colours)
            fade = [put_art(ssb_glow.tiles(f)) for f in ssb_glow.fadeout(last_lut, rims)]
            struct.pack_into('<%dI' % len(fade), rom, sym['glow_fadeout'] - ROM_BASE, *fade)
        if bands:
            struct.pack_into('<%dI' % len(band), rom, sym['glow_band'] - ROM_BASE, *band)
            rom[sym['glow_band_at'] - ROM_BASE:sym['glow_band_at'] - ROM_BASE + len(band_at)] = bytes(band_at)
        vt = sym['glow_vt'] - ROM_BASE; BEAM_ACTOR_VT_ = 0x4AEF8
        mine = {0: 'glow_destroy', 2: 'bomb_nop', 3: 'bomb_one', 4: 'glow_draw_oam', 6: 'bomb_zero', 9: 'bomb_zero', 10: 'bomb_nop'}
        for k in range(14):
            fn = (sym[mine[k]] | 1) if k in mine else ROM_BASE + BEAM_ACTOR_VT_ + struct.unpack_from('<i', clean, BEAM_ACTOR_VT_ + 4 * k)[0]
            struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    for who, tint in (('rose', pink), ('ssj4', red), ('ssb', ssb_aura), ('maxp', white)):
        for name, at_, count in ((who + '_aura_field', 0x752D28, 3), (who + '_aura_other', 0x7520D4, 7)):
            out = bytearray(clean[at_:at_ + 12 * count])
            for k in range(0, 12 * count, 12):
                t = struct.unpack_from('<I', out, k + 8)[0] - ROM_BASE
                struct.pack_into('<I', out, k + 8, put_art(clean[t:t + out[k + 2] * out[k + 3]].translate(tint)))
            rom[sym[name] - ROM_BASE:sym[name] - ROM_BASE + 12 * count] = out
        vt = sym[who + '_vt'] - ROM_BASE
        for k in range(14):
            fn = (sym[who + '_start'] | 1) if k == 0 else ROM_BASE + POWER_UP_VT + struct.unpack_from('<i', clean, POWER_UP_VT + 4 * k)[0]
            struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    # The crackle around a Super Saiyan 2 and Full Power (outfit.c crackle): three bolts of four frames (crackle_frames) per colour set, in
    # the spark frame format of the hit sparks (0x712FDC): origin x, y, width, height, OAM attributes (256 colours, square, 16x16), tiles.
    # Each bolt is drawn on a 32x32 frame about its middle, but is at most 10 wide and 14 tall: it is stored as the 16x16 piece that
    # holds all four of its frames (the same pixels on screen, the origin moved with the cut), so a bolt takes 256 bytes of sprite
    # memory, not 1 KB. Sprite memory's allocator never joins freed blocks: two 1 KB bolts out at once left a 1 KB block cut off the
    # largest free one for good, and at Volcano Summit Broly's first conversation, which needs all but 960 bytes of it, then took Broly's
    # own 4 KB (Nov 11: he wasn't drawn while he spoke to a Super Saiyan 2). The build stops if a bolt no longer fits the piece.
    for who, (g, c) in (('ss2', ((96, 248, 248), (200, 248, 248))), ('fp', FP_BOLTS), ('ssb', SSB_BOLTS)):
        gi, ci = one(np.array(g)), one(np.array(c))
        out = bytearray()
        for b in range(3):
            frames_ = crackle_frames(31 * b + {'fp': 7, 'ssb': 5}.get(who, 3), gi, ci)
            ys, xs = np.where(np.any([f > 0 for f in frames_], axis=0))
            x0, y0 = min(int(xs.min()), 16), min(int(ys.min()), 16)
            if xs.max() >= x0 + BOLT_PIECE or ys.max() >= y0 + BOLT_PIECE: sys.exit('crackle bolt %s %d does not fit a %dx%d piece' % (who, b, BOLT_PIECE, BOLT_PIECE))
            for img in frames_:
                cut = img[y0:y0 + BOLT_PIECE, x0:x0 + BOLT_PIECE]
                out += struct.pack('<bbBBHHI', 16 - x0, 16 - y0, BOLT_PIECE, BOLT_PIECE, 0x2000, 0x4000,
                                   put_art(cut.reshape(BOLT_PIECE // 8, 8, BOLT_PIECE // 8, 8).transpose(0, 2, 1, 3).tobytes()))
        rom[sym['bolt_' + who] - ROM_BASE:sym['bolt_' + who] - ROM_BASE + len(out)] = out
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Super Saiyan Rose', 'Press the B Button to transform into Super Saiyan Rose: attacks hit 1.5x as hard.  Press it again to change back.')]
    for form in ('black', 'rose'):
        tint = KAME_TINT[form]
        remap = bytes(0 if v == 0 else one(np.array(tint.get(v, tuple(pal[v])), dtype=int)) for v in range(256)); copies = {}
        def frames(o, count):
            return put(bytes(region_rows(clean, bytearray(clean[o:o + 12 * count]), remap, put_art, copies)))
        shape, table = {}, sym[form + '_params'] - ROM_BASE
        body_at = body_block(frames)
        for i in range(3):
            a, strength, body, head = struct.unpack_from('<4I', clean, BEAM_PARAMS + 16 * i)
            shape.setdefault(body, body_at(body)); shape.setdefault(head, frames(head - ROM_BASE, 64))
            struct.pack_into('<4I', rom, table + 16 * i, a, strength, shape[body], shape[head])
        if form == 'black': icon_map = remap
    vt = sym['black_kame_vt'] - ROM_BASE
    for k in range(9):
        fn = ROM_BASE + BEAM_VT + struct.unpack_from('<i', clean, BEAM_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['black_kame_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
    row = bytearray(clean[SKILL_ROWS + 24 * 15:SKILL_ROWS + 24 * 16])
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], icon_map)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 15 + 4)])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['black_kame_use'] | 1)
    rows[BLACK_KAME_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Black Kamehameha', 'Hold the B Button to emit a long beam of dark energy.')]
    new_strings = []                             # the Nov 9 moves' names: after every fixed id below
    def new_text(*texts):
        first = len(new_strings); new_strings.extend(texts); return first
    for k, (name, skill, power, tint, title, text) in enumerate(KAME_VARIANTS):     # Galick Gun, 10x Kamehameha: the Kamehameha's code, own frames and strength
        remap = bytes(0 if v == 0 else one(np.array(tint.get(v, tuple(pal[v])), dtype=int)) for v in range(256)); copies = {}
        def frames(o, count):
            return put(bytes(region_rows(clean, bytearray(clean[o:o + 12 * count]), remap, put_art, copies)))
        shape, table = {}, sym['kv_params'] - ROM_BASE + 48 * k
        body_at = body_block(frames)
        for i in range(3):
            a, strength, body, head = struct.unpack_from('<4I', clean, BEAM_PARAMS + 16 * i)
            shape.setdefault(body, body_at(body)); shape.setdefault(head, frames(head - ROM_BASE, 64))
            struct.pack_into('<4I', rom, table + 16 * i, min(int((a >> 16) * power), 0xFFFF) << 16 | a & 0xFFFF, strength, shape[body], shape[head])   # +0's top half: the damage (41, 164, 328 by level)
        vt = sym['kv_vt'] - ROM_BASE + 36 * k
        for j in range(9):
            fn = ROM_BASE + BEAM_VT + struct.unpack_from('<i', clean, BEAM_VT + 4 * j)[0]
            struct.pack_into('<i', rom, vt + 4 * j, ((sym[name + '_start'] | 1) if j == 0 else fn) - (ROM_BASE + vt))
        row = bytearray(clean[SKILL_ROWS + 24 * 15:SKILL_ROWS + 24 * 16])
        struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], remap)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 15 + 4)])
        struct.pack_into('<I', row, 12, new_text(title, text))       # an index into new_strings for now: made a UI id when they are placed
        if skill == TENX_SKILL: struct.pack_into('<I', row, 16, sym['ssj4_kame_can'] | 1)
        struct.pack_into('<I', row, 20, sym[name + '_use'] | 1)
        rows[skill] = row
    beam_poses(rom, put, put_art)
    held_poses(rom, put_art)
    fist_poses(rom, put_art)
    front_changes(rom, put_art)
    vt = sym['kame_vt'] - ROM_BASE                       # Master Roshi's Kamehameha: the Kamehameha's behaviour with its update wrapped (outfit.c kame_update)
    for k in range(9):
        fn = ROM_BASE + BEAM_VT + struct.unpack_from('<i', clean, BEAM_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['kame_update'] | 1) if k == 2 else fn) - (ROM_BASE + vt))
    def tinted_frames(rows_at, count, lo, hi, remap, cache):
        """A copy of `count` {header, attributes, tiles} rows whose tiles in [lo, hi) are recoloured (each block once)."""
        out = bytearray(clean[rows_at - ROM_BASE:rows_at - ROM_BASE + 12 * count])
        return bytes(region_rows(clean, out, remap, put_art, cache, lambda o, k: (struct.unpack_from('<I', o, k)[0] >> 16 & 255) * (struct.unpack_from('<I', o, k)[0] >> 24 & 255), lo, hi))
    def behaviour(vt_sym, orig_vt, mine):
        vt = sym[vt_sym] - ROM_BASE
        for j in range(9):
            fn = (sym[mine[j]] | 1) if j in mine else ROM_BASE + orig_vt + struct.unpack_from('<i', clean, orig_vt + 4 * j)[0]
            struct.pack_into('<i', rom, vt + 4 * j, fn - (ROM_BASE + vt))
    def move_row(base_skill, remap, title, text, usable, use):
        row = bytearray(clean[SKILL_ROWS + 24 * base_skill:SKILL_ROWS + 24 * base_skill + 24])
        struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], remap)) for p in struct.unpack_from('<II', row, 4)])
        struct.pack_into('<I', row, 12, new_text(title, text))
        if usable: struct.pack_into('<I', row, 16, sym[usable] | 1)
        struct.pack_into('<I', row, 20, sym[use] | 1)
        return row
    # Final Shine: Final Flash's beam (rows 0x76174C: frames, 8, damage by level) green and 1.5x as strong. Vegeta as Super Saiyan 4.
    FLASH_PARAMS, FLASH_VT, FLASH_ART = 0x76174C, 0x4D9D4, (0x0875F000, 0x08761800)
    def shine_green(v):                       # Final Flash's white core goes light green and its pale edges a deeper green, so the beam reads green, not white
        if v == 0: return 0
        h, s, b = colorsys.rgb_to_hsv(*(pal[v] / 255.0))
        if s < 0.12 and b > 0.9: return one((176, 248, 176))
        if s < 0.12: return v
        return one((np.array(colorsys.hsv_to_rgb(140 / 360, min(1.0, s * 2 + 0.3), b * 0.9)) * 255).astype(int))
    green_shine = bytes(shine_green(v) for v in range(256)); cache = {}; table = sym['shine_params'] - ROM_BASE
    for i in range(3):
        frames_at, eight, damage = struct.unpack_from('<3I', clean, FLASH_PARAMS + 12 * i)
        struct.pack_into('<3I', rom, table + 12 * i, put(tinted_frames(frames_at, 8, *FLASH_ART, green_shine, cache)), eight, int(damage * 1.5))
    behaviour('shine_vt', FLASH_VT, {2: 'shine_update'})
    rows[FINAL_SHINE_SKILL] = move_row(10, green_shine, 'Final Shine', 'Super Saiyan 4 only. Hold the B Button to fire a green beam across the land, 1.5x as strong as Final Flash.', 'ssj4_flash_can', 'shine_use')
    # Super Saiyan 4's Dragon Fist: the dragon's rows (0x77AD10, 4 facings x 4 rows) red, its hits 1.25x (outfit.c). Kid Goku as Super Saiyan 4.
    DRAGON_ROWS, DRAGON_VT, DRAGON_ART = 0x77AD10, 0x4D9B0, (0x08771000, 0x0877AD10)
    red = shifted(0 / 360); cache = {}
    rom[sym['red_dragon'] - ROM_BASE:sym['red_dragon'] - ROM_BASE + 0xC0] = tinted_frames(ROM_BASE + DRAGON_ROWS, 16, *DRAGON_ART, red, cache)
    behaviour('dragon4_vt', DRAGON_VT, {2: 'dragon4_update', 3: 'dragon4_end'})
    rows[DRAGON4_SKILL] = move_row(5, red, 'Super Dragon Fist', 'Super Saiyan 4 only. Hold the B Button to make a giant red dragon of energy; steer its head with the +Control Pad and release to bite. 1.25x as strong.', 'ssj4_dragon_can', 'dragon4_use')
    # Solar Flare (Tien, Krillin): Big Bang's starburst (row 4's icon) bleached towards white; the flash and stun are outfit.c's.
    def paled(v):
        if v == 0: return 0
        c = pal[v].astype(int)
        return one(c + ((255 - c) * 0.6).astype(int))
    pale = bytes(paled(v) for v in range(256))
    rows[SOLAR_FLARE_SKILL] = move_row(4, pale, 'Solar Flare', 'Press the B Button to flash a blinding light: every ordinary enemy on screen is stunned for a few seconds. Bosses are not fooled. Six seconds between flashes.', 'solar_can', 'solar_use')
    rows[SOLAR_FLARE_SKILL][0] = 0xFF
    # The transformations' own rows (Nov 9). Super Saiyan 2 and 4: Super Saiyan 3's icon with a 2 (cyan as its 3) or a purple 4. Kaioken: Super
    # Saiyan's Z in red. Super Saiyan Blue: the Z in blue (its name and text are UI 1057 and 1051, UI_EDITS).
    ss3_icons = [clean[p - ROM_BASE:p - ROM_BASE + 0x200] for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 22 + 4)]
    ss_icons = [clean[p - ROM_BASE:p - ROM_BASE + 0x200] for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 20 + 4)]
    def tier_row(base_skill, icons, usable, use, texts):
        row = bytearray(clean[SKILL_ROWS + 24 * base_skill:SKILL_ROWS + 24 * base_skill + 24])
        row[0] = 2                                   # a level: its mastery
        struct.pack_into('<II', row, 4, *[put_art(i) for i in icons])
        struct.pack_into('<III', row, 12, new_text(*texts), sym[usable] | 1, sym[use] | 1)
        return row
    rows[SS2_SKILL] = tier_row(22, (iconlib.with_digit(ss3_icons[0], '2', 0x4B, 0x4B), iconlib.with_digit(ss3_icons[1], '2', 0xBA, 0xBA)), 'ss2_can', 'ss2_use',
        ('Super Saiyan 2', 'Press the B Button to transform into a Super Saiyan 2: attacks hit 1.5x as hard. You must already be a Super Saiyan. Press it again to change back.'))
    rows[SS4_SKILL] = tier_row(22, (iconlib.with_digit(ss3_icons[0], '4', 0x94, 0x4B), iconlib.with_digit(ss3_icons[1], '4', 0x56, 0xBA)), 'ss4_can', 'ss4_use',
        ('Super Saiyan 4', 'Press the B Button to transform into a Super Saiyan 4: attacks hit 2.5x as hard, on a ki bar of its own. You must be in the form below it. Press it again to change back.'))
    kk_red = shifted(0 / 360)
    rows[KAIOKEN_SKILL] = tier_row(20, [iconlib.recolour(i, kk_red) for i in ss_icons], 'kaioken_can', 'kaioken_use',
        ('Kaioken', 'Press B for the Kaioken: hits 1.25x as hard, up to 1.75x as you master it, but it wears on your health. Not with Super Saiyan.'))
    rows[SSG_SKILL] = tier_row(20, [iconlib.recolour(i, shifted(340 / 360)) for i in ss_icons], 'ssg_can', 'ssg_use',
        ('Super Saiyan God', 'Press the B Button to become a Super Saiyan God: attacks hit 1.75x as hard and its ki drains slowly. From base form. Press it again to change back.'))
    ssb_row = bytearray(clean[SKILL_ROWS + 24 * 22:SKILL_ROWS + 24 * 22 + 24])
    struct.pack_into('<II', ssb_row, 4, *[put_art(iconlib.recolour(i, ssb_blue)) for i in ss_icons])
    struct.pack_into('<HHII', ssb_row, 12, 1057, 1051, sym['ssb_can'] | 1, sym['ssb_use'] | 1)
    ssb_row[0] = 2
    rows[SUPER_BLUE_SKILL] = bytes(ssb_row)
    # The Spirit Bomb's icon (Nov 10, the owner: "the fucking spirit bomb has the kamehameha icon still"): its row was a retail stub with the
    # Kamehameha's. A round ball in the bomb's own colours (spirit_bomb.png: 7 rim, 195 body, 196 core), lit from the top left, on the
    # Kamehameha icon's frame; the greyed copy uses that icon's greyed colours by brightness.
    kame_icons = [iconlib.decode(clean[p - ROM_BASE:p - ROM_BASE + 0x200]) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 15 + 4)]
    def lum(v): return int(pal[v].astype(int).sum())
    grey_pick = sorted({int(v) for v in np.unique(kame_icons[1][iconlib.WINDOW]) if v != iconlib.BG}, key=lum)
    spirit = []
    for k, icon in enumerate(kame_icons):
        a = icon.copy(); w = a[iconlib.WINDOW]; w[:] = iconlib.BG
        cy, cx, r = 4.0, 9.0, 4.4                                        # the window is 9 x 18
        for y in range(w.shape[0]):
            for x in range(w.shape[1]):
                d = ((y - cy) ** 2 + (x - cx) ** 2) ** 0.5
                if d > r: continue
                lit = ((y - (cy - 1.5)) ** 2 + (x - (cx - 1.5)) ** 2) ** 0.5
                v = 196 if lit < 1.6 else 195 if d < r - 1.1 else 7
                if k: v = grey_pick[min(len(grey_pick) - 1, {7: 0, 195: len(grey_pick) // 2, 196: len(grey_pick) - 1}[v])]
                w[y, x] = v
        for y, x in ((0, 3), (1, 15), (7, 2), (8, 16), (4, 1), (2, 17)):   # a few motes drawn in
            w[y, x] = 195 if not k else grey_pick[len(grey_pick) // 2]
        spirit.append(put_art(iconlib.encode(a)))
    struct.pack_into('<II', rom, SKILL_ROWS + 24 * SPIRIT_SKILL + 4, *spirit)
    import zone26 as z26
    if ERASER_UI + len(strings) > z26.CELL_NAME_UI: sys.exit('move CELL_NAME_UI up')
    while ERASER_UI + len(strings) < z26.CELL_NAME_UI: strings.append(put(b'\0\0'))
    strings.append(put('The Cell Games Arena'.encode('utf-16-le') + b'\0\0'))
    strings.append(put('Glacier'.encode('utf-16-le') + b'\0\0'))
    if ERASER_UI + len(strings) != BLACK_NAME_UI: sys.exit('form names moved')
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Goku Black', 'Super Saiyan Rose')]
    if ERASER_UI + len(strings) != GT_NAME_UI: sys.exit('GT names moved')
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Pan', 'Uub', 'Majuub', 'Brapan')]
    if ERASER_UI + len(strings) != ROSHI_NAME_UI: sys.exit('Roshi names moved')
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Master Roshi', 'Max Power Roshi')]
    if ERASER_UI + len(strings) != SSG_NAME_UI: sys.exit('Super Saiyan God name moved')
    strings.append(put('Super Saiyan God'.encode('utf-16-le') + b'\0\0'))
    if ERASER_UI + len(strings) != FP_NAME_UI: sys.exit('Full Power name moved')
    strings.append(put('Full Power Gohan'.encode('utf-16-le') + b'\0\0'))
    row = bytearray(clean[SKILL_ROWS + 24 * 20:SKILL_ROWS + 24 * 21])          # Majuub: Super Saiyan's row, its own name and use
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['majuub_use'] | 1)
    rows[MAJUUB_SKILL] = bytes(row)
    row = bytearray(clean[SKILL_ROWS + 24 * 20:SKILL_ROWS + 24 * 21])          # Max Power: Super Saiyan's row, its Z in white, its own name and use
    row[0] = 0xFF
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], white)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 20 + 4)])
    struct.pack_into('<I', row, 12, new_text('Max Power', 'Press the B Button to bulk up to full power: attacks hit 1.5x as hard. It drains like Super Saiyan. Press it again to calm down.'))
    struct.pack_into('<I', row, 20, sym['maxp_use'] | 1)
    rows[MAX_POWER_SKILL] = row
    row = bytearray(clean[SKILL_ROWS + 24 * 20:SKILL_ROWS + 24 * 21])          # Full Power: Super Saiyan's row, its Z in violet, no level (not a mastered tier)
    row[0] = 0xFF
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], shifted(275 / 360))) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 20 + 4)])
    struct.pack_into('<III', row, 12, new_text('Full Power', 'Press the B Button to unleash Mystic Gohan\'s full power: attacks hit 1.75x as hard and its ki drains slowly. In his orange gi only. Press it again to calm down.'),
                     sym['fp_can'] | 1, sym['fp_use'] | 1)
    rows[FP_SKILL] = row
    row = bytearray(clean[SKILL_ROWS + 24 * 12:SKILL_ROWS + 24 * 13])          # the Potara: the Fusion Dance's row (its icon, in the earrings' gold), its own name, check and use
    struct.pack_into('<II', row, 4, *[put_art(iconlib.recolour(clean[p - ROM_BASE:p - ROM_BASE + 0x200], shifted(50 / 360))) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 12 + 4)])
    struct.pack_into('<III', row, 12, new_text('Potara', 'Put on a Potara earring and fuse with your partner, who must be in the party. Goku and Vegeta: Vegito, for an hour of his fighting.'),
                     sym['potara_can'] | 1, sym['potara_use'] | 1)
    rows[POTARA_SKILL] = row
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Majuub', 'Press the B Button to draw on Majin Buu\'s power and become Majuub: attacks hit 1.5x as hard.  Press it again to change back.')]
    if ERASER_UI + len(strings) != TEEN_NAME_UI: sys.exit('Teen Gohan name moved')
    strings.append(put('Teen Gohan'.encode('utf-16-le') + b'\0\0'))
    base_new = ERASER_UI + len(strings)          # the Nov 9 moves' names and descriptions, after everything with a fixed id
    strings += [put_art(t.encode('utf-16-le') + b'\0\0') for t in new_strings]     # with the art: the code area fills up (Nov 9)
    for skill, row in rows.items():
        if isinstance(row, bytearray):
            i = struct.unpack_from('<I', row, 12)[0]
            struct.pack_into('<HH', row, 12, base_new + i, base_new + i + 1)
            rows[skill] = bytes(row)
    BLAST_TILES, BLAST_TABLE, BLAST_SITE = (0x71300C, 0x71370C), 0x71370C, 0x197F2
    if rom[BLAST_SITE:BLAST_SITE + 14] != bytes.fromhex('207cbc4a41000918090189182165'):
        sys.exit('player blast code changed')
    blue_new = put(clean[BLAST_TILES[0]:BLAST_TILES[1]].translate(blue))
    frames_new = bytearray(clean[BLAST_TABLE:BLAST_TABLE + 192])
    for k in range(0, 192, 12):
        p = struct.unpack_from('<I', frames_new, k + 8)[0]
        if not BLAST_TILES[0] <= p - ROM_BASE < BLAST_TILES[1]:
            sys.exit('blast frame outside its tiles: 0x%X' % p)
        struct.pack_into('<I', frames_new, k + 8, blue_new + p - ROM_BASE - BLAST_TILES[0])
    rom[sym['blue_blast'] - ROM_BASE:sym['blue_blast'] - ROM_BASE + 192] = frames_new
    for form, hue in BLAST_HUE.items():         # Goku Black's and Rose's, the same way
        tiles_new = put_art(clean[BLAST_TILES[0]:BLAST_TILES[1]].translate(shifted(hue / 360)))
        fr = bytearray(clean[BLAST_TABLE:BLAST_TABLE + 192])
        for k in range(0, 192, 12):
            struct.pack_into('<I', fr, k + 8, tiles_new + struct.unpack_from('<I', fr, k + 8)[0] - ROM_BASE - BLAST_TILES[0])
        rom[sym[form + '_blast'] - ROM_BASE:sym[form + '_blast'] - ROM_BASE + 192] = fr
    rom[BLAST_SITE:BLAST_SITE + 14] = bytes.fromhex('01490847c046') + struct.pack('<I', sym['blast_hook'] | 1) + bytes.fromhex('c046c046')
    # The Spirit Bomb's sprite: ultimate/art/spirit_bomb.png, a whole picture on plain white. One 64x64 frame per 8 pixels of size: up to 64 across the whole orb, above that its top left quarter.
    from PIL import Image
    orb = np.array(Image.open('ultimate/art/spirit_bomb.png').convert('RGB'))
    colours = {(7, 238, 255): 7, (158, 255, 245): 195, (247, 255, 255): 196, (255, 255, 255): 0}
    idx = np.zeros(orb.shape[:2], np.uint8)
    for rgb, v in colours.items(): idx[(orb == rgb).all(2)] = v
    if len(set(map(tuple, orb.reshape(-1, 3)))) != 4:
        sys.exit('spirit_bomb.png has colours the build does not know')
    def nearest(a, w, h):
        ys = (np.arange(h) * a.shape[0] // h); xs = (np.arange(w) * a.shape[1] // w)
        return a[ys][:, xs]
    def linear(img):
        return b''.join(img[y:y + 8, x:x + 8].tobytes() for y in range(0, 64, 8) for x in range(0, 64, 8))
    table = sym['bomb_frames'] - ROM_BASE
    for k in range(12):
        size = (k + 1) * 8; cell = np.zeros((64, 64), np.uint8)
        if size <= 64:
            o = (64 - size) // 2; cell[o:o + size, o:o + size] = nearest(idx, size, size)
        else:
            whole = nearest(idx, size, size); q = whole[:size // 2, :size // 2]; cell[64 - size // 2:, 64 - size // 2:] = q
        struct.pack_into('<I', rom, table + 4 * k, put(linear(cell)))
    vt = sym['bomb_vt'] - ROM_BASE; BEAM_ACTOR_VT = 0x4AEF8
    mine = {0: 'bomb_destroy', 2: 'bomb_nop', 3: 'bomb_one', 4: 'bomb_draw_oam', 6: 'bomb_zero', 9: 'bomb_zero', 10: 'bomb_nop'}
    for k in range(14):
        fn = (sym[mine[k]] | 1) if k in mine else ROM_BASE + BEAM_ACTOR_VT + struct.unpack_from('<i', clean, BEAM_ACTOR_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    # The boss bar (outfit.c bossbar): which stats rows are the mod's boss fights (zone26.boss_table). The bar itself is the game's own:
    # its actor, art and code; the mod's bars use the game's table with one entry of ten answered by the mod.
    import zone26
    tab, _ = zone26.boss_table()
    struct.pack_into('<2I', rom, sym['boss_tab'] - ROM_BASE, len(tab), put(tab))
    vt = sym['bossbar_vt'] - ROM_BASE; GAME_BAR_VT = 0x4CE28            # the game's boss bar table, its 'shown?' (3) answered by outfit.c
    for k in range(10):
        fn = (sym['bossbar_visible'] | 1) if k == 3 else ROM_BASE + GAME_BAR_VT + struct.unpack_from('<i', clean, GAME_BAR_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    # Wrath of the Gods (lib/wrath.py; outfit.c wrath_start, wrath_update): Beerus's own beam. The enemy beam's table of functions becomes
    # the mod's copy for every enemy (the one word that names it), its start and every-frame wrapped; his thin light-yellow frames and
    # where they go from his fingertip are made there from the Kamehameha's own.
    import wrath
    if struct.unpack_from('<I', rom, wrath.ENEMY_BEAM_VT_REF)[0] != ROM_BASE + wrath.ENEMY_BEAM_VT: sys.exit('the word that names the enemy beam\'s table moved')
    vt = sym['wrath_vt'] - ROM_BASE
    for k in range(wrath.VT_ENTRIES):
        fn = ROM_BASE + wrath.ENEMY_BEAM_VT + struct.unpack_from('<i', clean, wrath.ENEMY_BEAM_VT + 4 * k)[0]
        if k < 2 and fn != (wrath.ENEMY_START, wrath.ENEMY_UPDATE)[k] + 1: sys.exit('the enemy beam\'s table is not as lib/wrath.py has it')
        struct.pack_into('<i', rom, vt + 4 * k, ((sym[('wrath_start', 'wrath_update')[k]] | 1) if k < 2 else fn) - (ROM_BASE + vt))
    struct.pack_into('<I', rom, wrath.ENEMY_BEAM_VT_REF, ROM_BASE + vt)
    made = []
    for rows_, block, base in (wrath.ball_rows(clean), wrath.beam_rows(clean)):
        tiles = put_art(block)
        for k in range(0, len(rows_), 12):
            t = struct.unpack_from('<I', rows_, k + 8)[0]
            if base <= t < base + len(block): struct.pack_into('<I', rows_, k + 8, tiles + t - base)
        made.append(put(bytes(rows_)))
    for i in range(3):                               # (the enemy beam only ever asks for the first level: all three are his)
        struct.pack_into('<4I', rom, sym['wrath_params'] - ROM_BASE + 16 * i, *struct.unpack_from('<II', clean, wrath.BEAM_PARAMS), *made)
    ball, beam = wrath.places(clean, *wrath.beam_rows(clean))
    struct.pack_into('<16b', rom, sym['wrath_at'] - ROM_BASE, *[int(c) for v in ball + beam for c in v])
    struct.pack_into('<I', rom, sym['wrath_who'] - ROM_BASE, ROM_BASE + ACTORS_AT + 4 * NEW_ACTORS['beerus'])
    vt = sym['absorb_vt'] - ROM_BASE
    for k in range(14):
        fn = (sym['absorb_start'] | 1) if k == 0 else ROM_BASE + POWER_UP_VT + struct.unpack_from('<i', clean, POWER_UP_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    # The post-game gear (GEAR): the table moves to the art area with the new rows after the game's, and its 17 references follow.
    gear = bytearray(clean[GEAR_TABLE:GEAR_TABLE + 44 * GEAR_COUNT])
    for row_id, name, text, base, slot, stats, exp, hue in GEAR:
        if row_id != len(gear) // 44: sys.exit('gear rows out of order')
        g = bytearray(clean[GEAR_TABLE + 44 * base:GEAR_TABLE + 44 * base + 44])
        struct.pack_into('<HH', g, 0, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
        strings += [put(t.encode('utf-16-le') + b'\0\0') for t in (name, text)]
        p = struct.unpack_from('<I', g, 0x10)[0] - ROM_BASE; t_, size = struct.unpack_from('<II', clean, p)
        pic = bytes(wfz.decompress_stream(clean, p + 8, size)[0]) if t_ else bytes(clean[p + 8:p + 8 + size])
        if hue is not None: pic = pic.translate(shifted(hue / 360))
        struct.pack_into('<I', g, 0x10, put_art(struct.pack('<II', 0, len(pic)) + pic))
        g[0x14], g[0x15] = slot, 51                                     # worn from level 1
        g[0x16:0x1B] = bytes(v & 255 for v in stats)
        struct.pack_into('<IiII', g, 0x1C, exp, -1, 0, 0)               # not sold; no flags or effect script: outfit.c does the work
        gear += g
    at_gear = put_art(bytes(gear))
    for ref in GEAR_REFS:
        if struct.unpack_from('<I', rom, ref)[0] != ROM_BASE + GEAR_TABLE: sys.exit('gear table reference moved: 0x%X' % ref)
        struct.pack_into('<I', rom, ref, at_gear)
    for k in SHELVED_SKILLS:                       # the shelved Great Ape's skill ids: the empty row (a save from Nov 9 can hold them)
        if k in rows: sys.exit('skill %d is the shelved Great Ape\'s: give a new skill another id' % k)
        rows[k] = bytes(clean[SKILL_ROWS:SKILL_ROWS + 24])
    if max(rows) + 1 != SKILL_IDS_END:
        sys.exit('the skill table ends at %d: update SKILL_IDS_END (outfit.c drops ids past it from saves)' % (max(rows) + 1))
    for k in range(ERASER_SKILL, max(rows) + 1):   # ids not built yet: the empty row, so the table stays in id order
        rows.setdefault(k, bytes(clean[SKILL_ROWS:SKILL_ROWS + 24]))
    # Dragon Fist Explosion (the original row 5): Gogeta's, and Goku's as a Super Saiyan 3 (outfit.c dragon_can, dragon_use). The
    # row is changed where it lies, before the table is copied out below; its description (UI string 1321) says whose it is.
    if struct.unpack_from('<HH', rom, SKILL_ROWS + 24 * 5 + 12) != (1320, 1321) or struct.unpack_from('<II', rom, SKILL_ROWS + 24 * 5 + 16) != (0x08019E9F, 0x08019EB9):
        sys.exit('skill row 5 is not the original Dragon Fist Explosion')
    struct.pack_into('<II', rom, SKILL_ROWS + 24 * 5 + 16, sym['dragon_can'] | 1, sym['dragon_use'] | 1)
    # The Fusion Dance (row 12) can't be used in Super 13's fight (outfit.c fusion_can); changed where it lies too.
    if struct.unpack_from('<II', rom, SKILL_ROWS + 24 * 12 + 16) != (0x0801A169, 0x0801A19F):
        sys.exit('skill row 12 is not the original Fusion Dance')
    struct.pack_into('<II', rom, SKILL_ROWS + 24 * 12 + 16, sym['fusion_can'] | 1, sym['dance_use'] | 1)     # (Goku's and Vegeta's Super Saiyan 4 dance: dance_use)
    if struct.unpack_from('<I', rom, 0x13618)[0] != ROM_BASE + SKILL_ROWS:
        sys.exit('skill table reference moved')
    struct.pack_into('<I', rom, 0x13618, put(bytes(rom[SKILL_ROWS:SKILL_ROWS + 24 * ERASER_SKILL]) + b''.join(rows[k] for k in sorted(rows))))
    ptrs = find_once(rom, clean[UI_TABLE:UI_TABLE + 64], 'UI string table')
    table = bytearray(rom[ptrs:ptrs + 4 * ERASER_UI])                    # (Dragon Fist Explosion's description: Goku's too)
    struct.pack_into('<I', table, 4 * 1321, put(DRAGON_FIST_TEXT.encode('utf-16-le') + b'\0\0'))
    new = put(bytes(table) + struct.pack('<%dI' % len(strings), *strings))
    n = 0
    for o in range(0, CODE_END, 4):
        if struct.unpack_from('<I', rom, o)[0] == ROM_BASE + ptrs:
            struct.pack_into('<I', rom, o, new); n += 1
    if n != 51:
        sys.exit('UI table: expected 51 references, found %d' % n)
    t = struct.unpack_from('<I', rom, 0x13618)[0] - ROM_BASE      # the retail moves keep their level byte and icons (row +0..+11)
    bad = [k for k in range(ERASER_SKILL) if k not in (SPIRIT_SKILL, 20, 22) and rom[t + 24 * k:t + 24 * k + 12] != clean[SKILL_ROWS + 24 * k:SKILL_ROWS + 24 * k + 12]]
    if bad:
        sys.exit('skill rows %s lost their level or icons' % bad)
    return at, art


def add_portraits(rom, clean, at):
    """Android 17 and Future Trunks: LoG2's portraits (the import Gero's Legacy uses) in Buu's Fury's gold frame, on speaker ids past the 163 retail ones."""
    LIT, TABLE, COUNT, TEMPLATE = 0x12194, 0x6F393C, 163, 9        # the frame comes from Android 18's portrait
    if struct.unpack_from('<I', rom, LIT)[0] != ROM_BASE + TABLE:
        sys.exit('portrait table reference moved')
    combo = open(COMBO, 'rb').read()[0x800000:]
    l2pal = np.frombuffer(combo[0x3ECD1C + 768:0x3ECD1C + 1536], np.uint8).reshape(256, 3)
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    one = indexer([i for i in range(1, 256) if i not in artclean.MENU_SLOTS], pal)
    remap = np.array([one(l2pal[v]) for v in range(256)], np.uint8)
    def art(data, o):
        kind, size = struct.unpack_from('<II', data, o)
        raw = data[o + 8:o + 8 + 4096] if kind == 0 else bytes(wfz.decompress_stream(data, o + 8, 4096)[0])
        return np.frombuffer(raw, np.uint8).reshape(64, 64)
    frame = art(clean, struct.unpack_from('<I', clean, TABLE + 4 * TEMPLATE)[0] - ROM_BASE)
    table = list(struct.unpack_from('<%dI' % COUNT, clean, TABLE))
    table_at = (at + 3) & ~3; cur = table_at + 4 * 256
    for k in PORTRAITS:
        img = frame.copy()
        img[4:60, 4:60] = remap[art(combo, struct.unpack_from('<I', combo, 0x3ECB6C + 4 * k)[0] - 0x08800000)[4:60, 4:60]]
        rom[cur:cur + 4104] = struct.pack('<II', 0, 4096) + img.tobytes()
        table.append(ROM_BASE + cur); cur += 4104
    if len(table) != BLACK_PORTRAIT: sys.exit('portrait ids moved')
    for img in goku_black.portraits(one).values():        # Goku Black and Rose, from the owner's sheet, frame and all
        rom[cur:cur + 4104] = struct.pack('<II', 0, 4096) + img.astype(np.uint8).tobytes()
        table.append(ROM_BASE + cur); cur += 4104
    if len(table) != gt.FIRST_PORTRAIT: sys.exit('GT portrait ids moved')
    for img in gt.portraits(one):                        # GT, from the owner's Black Star Odyssey sheet, frame and all
        rom[cur:cur + 4104] = struct.pack('<II', 0, 4096) + img.astype(np.uint8).tobytes()
        table.append(ROM_BASE + cur); cur += 4104
    rom[table_at:table_at + 4 * 256] = struct.pack('<%dI' % len(table), *table) + bytes(4 * (256 - len(table)))
    struct.pack_into('<I', rom, LIT, ROM_BASE + table_at)
    return cur


# The press-fast meters (native 0xC6: pulling the Z-Sword, pushing the Spirit Bomb at the end of the story and at Super 13's; sub_080301B8): each
# press of A, B or the +Control Pad adds 10 towards 85, and each frame without one keeps 31/32 of it (rounded down: at least 1 lost a frame), so
# only 12 or more presses a second ever fill it (Nov 9, the owner: "impossible to fill up even when spamming the A button as fast as humanly
# possible"). Now a press adds 16 and a frame without one keeps 127/128 (1 a frame below 128): about 5 presses a second fill it in 3 seconds,
# 7 in about 1 (measured in the emulator: test_zone26.py presses it 6 times a second). (address, old, new) Thumb instructions.
MASH_PATCHES = ((0x301CA, 0x330A, 0x3310),          # adds r3, #10 -> #16
                (0x301E6, 0x014B, 0x01CB),          # lsls r3, r1, #5 -> #7
                (0x301EA, 0x1149, 0x11C9))          # asrs r1, r1, #5 -> #7 (with the subs between: x * 127 / 128)


def mash_retune(rom):
    for at, old, new in MASH_PATCHES:
        if struct.unpack_from('<H', rom, at)[0] != old: sys.exit('the press-fast meter moved: %X' % at)
        struct.pack_into('<H', rom, at, new)


def thumb_bl(at, to):
    d = (to - (at + 4)) >> 1
    return struct.pack('<HH', 0xF000 | (d >> 11 & 0x7FF), 0xF800 | (d & 0x7FF))


VENEERS = NATIVES          # the retail native table's old place (it moved: main), free for veneers to the mod's far code


def hud_icon_hook(rom, sym):
    """The HUD's skill icon asks hud_skill_row (outfit.c) for the held skill's row instead of sub_080135A2, through a veneer in reach of a bl."""
    SITE = 0xBAE6
    if rom[SITE - 4:SITE + 4] != bytes.fromhex('697d281c') + thumb_bl(SITE, 0x135A2):
        sys.exit('the HUD skill icon call moved: %s' % rom[SITE - 4:SITE + 4].hex())
    v = VENEERS
    if rom[v:v + 8] != open('baserom.gba', 'rb').read()[v:v + 8]: sys.exit('veneer area in use')
    rom[v:v + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['hud_row_guard'] | 1)      # (caps the pool bars' lengths on its way to hud_skill_row)
    rom[SITE:SITE + 4] = thumb_bl(SITE, v)


def patch_slot_read(rom, sym):
    """Send the game's three save-slot reads through slot_read. Code that far away is out of bl range, so sub_08004A76's
    18 bytes become two veneers; its one job moves to slot_area."""
    AREA, VENEER = 0x4A76, 0x4A7A
    if rom[AREA:AREA + 18] != bytes.fromhex('45214901401808b54178007803f0bbff08bd'):
        sys.exit('sub_08004A76 changed: %s' % rom[AREA:AREA + 18].hex())
    rom[AREA:AREA + 18] = bytes.fromhex('024a1047024a1047') + bytes(2) + struct.pack('<II', sym['slot_area'] | 1, sym['slot_read'] | 1)
    sites = [i for i in range(0x4000, 0x30000, 2) if rom[i:i + 4] == thumb_bl(i, 0x48A0)]
    if len(sites) != 3:
        sys.exit('expected 3 save-slot reads, found %s' % [hex(i) for i in sites])
    for i in sites:
        rom[i:i + 4] = thumb_bl(i, VENEER)


def ssj4_goku(rom, actors, at):
    """Super Saiyan 4 Goku's touch-up (the owner, Nov 11 21:01, on its fourth look: "Lock that Goku for now"): Gogeta's hair shape on his
    front head in his own hair colours, hands of skin and arms of fur in every frame, his idle still, the arms-raised pose with his own
    head, gold eyes. gt.py makes him from the sheet as before; here every frame of that figure goes through the table that
    ssj4_preview/ssj4_table.py makes from the ROM so far (README, Nov 11 evening). -> (the end of what was written, (frames, records))"""
    sys.path.insert(0, 'ultimate/ssj4_preview')
    import ssj4_table
    u = lambda o: struct.unpack_from('<I', rom, o)[0]; aid = actors['kid_goku_ssj4']
    tmp = tempfile.NamedTemporaryFile(suffix='.gba', delete=False); tmp.write(rom); tmp.close()
    try: table, changed = ssj4_table.make(tmp.name, aid, actors['gogeta_ssj4'], OUT + '/ssj4_cache.pkl')
    finally: os.unlink(tmp.name)
    ins = sprites.Inserter(rom, (at + 3) & ~3); hits = [0]
    def fn(img, view):
        got = table.get(ssj4_table.key(img))
        if got is None: return img
        hits[0] += 1
        return got
    rec = sprites.composed_actor(ins, rom, u(ACTORS_AT + 4 * aid) - ROM_BASE, fn)
    struct.pack_into('<I', rom, ACTORS_AT + 4 * aid, ins.put(bytes(rec)))
    if changed < 100 or not hits[0]: sys.exit('Super Saiyan 4 Goku: the touch-up found only %d frames to change (%d records)' % (changed, hits[0]))
    return ins.cur, (changed, hits[0])


def gogeta_fix(rom, actors, at):
    """Super Saiyan 4 Gogeta's head, neck and shoulders (the owner, Nov 11 21:38: "Some weird clipping with Ssj4 Gogeta head and neck on
    side and back views especially on walk frames mainly"; 22:25: "The back ones still doing it it's by a pixel or two moving slightly to
    the side"; 22:35, of the second preview: "Okay good lock it for now"). gt.py makes him from the owner's sheet as before; here every
    frame goes through the table gogeta_preview/gogeta_table.py makes from the ROM so far (fixes.py: his idle, walk and run frames; from the
    side the see-through spot over his eye wherever his head is). After Super Saiyan 4 Goku's touch-up, which reads Gogeta's hair.
    -> (the end of what was written, (pictures changed, frame records through it))"""
    sys.path.insert(0, 'ultimate/gogeta_preview')
    import gogeta_table, ssj4_table
    u = lambda o: struct.unpack_from('<I', rom, o)[0]; aid = actors['gogeta_ssj4']
    tmp = tempfile.NamedTemporaryFile(suffix='.gba', delete=False); tmp.write(rom); tmp.close()
    try: table, changed = gogeta_table.make(tmp.name, aid, actors['kid_goku_ssj4'], OUT + '/gogeta_cache.pkl')
    finally: os.unlink(tmp.name)
    ins = sprites.Inserter(rom, (at + 3) & ~3); hits = [0]
    def fn(img, view):
        got = table.get(ssj4_table.key(img))
        if got is None: return img
        hits[0] += 1
        return got
    rec = sprites.composed_actor(ins, rom, u(ACTORS_AT + 4 * aid) - ROM_BASE, fn)
    struct.pack_into('<I', rom, ACTORS_AT + 4 * aid, ins.put(bytes(rec)))
    if changed < 60 or hits[0] < changed: sys.exit('Super Saiyan 4 Gogeta: the fixes found only %d pictures to change (%d records)' % (changed, hits[0]))
    return ins.cur, (changed, hits[0])


def ssj4_fix(rom, actors, at):
    """Super Saiyan 4 Goku's preview fixes (the owner, Nov 12: the arms "CONSISTENT IN EVERY FRAME EVERY PIXEL", the plain back, the
    spin, hit 2 from the side, the special's last frame, the see-through pixels; 08:47 "everyone else is good", 09:55 "Do 174 and 175
    now"). After his touch-up and Gogeta's fixes (hit 2's head is read from Gogeta's fixed frame): every frame of his figure goes through
    the table ssj4_preview/fix_table.py makes from the ROM so far. -> (the end of what was written, (pictures changed, frame records))"""
    sys.path.insert(0, 'ultimate/ssj4_preview')
    import fix_table, ssj4_table
    u = lambda o: struct.unpack_from('<I', rom, o)[0]; aid = actors['kid_goku_ssj4']
    tmp = tempfile.NamedTemporaryFile(suffix='.gba', delete=False); tmp.write(rom); tmp.close()
    try: table, changed = fix_table.make(tmp.name, aid, actors['gogeta_ssj4'], OUT + '/ssj4_fix_cache.pkl')
    finally: os.unlink(tmp.name)
    ins = sprites.Inserter(rom, (at + 3) & ~3); hits = [0]
    def fn(img, view):
        got = table.get(ssj4_table.key(img))
        if got is None: return img
        hits[0] += 1
        return got
    rec = sprites.composed_actor(ins, rom, u(ACTORS_AT + 4 * aid) - ROM_BASE, fn)
    struct.pack_into('<I', rom, ACTORS_AT + 4 * aid, ins.put(bytes(rec)))
    if changed < 60 or hits[0] < changed: sys.exit('Super Saiyan 4 Goku: the preview fixes found only %d pictures to change (%d records)' % (changed, hits[0]))
    return ins.cur, (changed, hits[0])


IDLE_MAX = 20                        # pixels: the game's own idles differ by 3 to 15 between their two frames (a breath in the chest)
IDLE_WAITS = ()                      # (Super Saiyan 4 Goku waited here for the owner's word on his touch-up; it has his own still idle now)


def frame_canvas(rom, fp, size=128, origin=64):
    """A frame as the game lays it out, on a canvas round the actor's origin."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    o = fp - ROM_BASE; c = np.zeros((size, size), np.uint8)
    for i in range(u(o)):
        p = o + 8 + 12 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, p); img = goku_black.tiles(rom, u(p + 8) - ROM_BASE, w, h)
        a1 = struct.unpack_from('<H', rom, p + 6)[0]
        if a1 & 0x1000: img = img[:, ::-1]
        if a1 & 0x2000: img = img[::-1]
        m = img > 0; c[origin + y:origin + y + h, origin + x:origin + x + w][m] = img[m]
    return c


def idle_still(rom, index):
    """The owner, Nov 11 19:17: "Stop with this head bob on the idle stuff how are we doing this again". The game's own figures breathe:
    their two idle frames differ by a few pixels of the chest. Some of the sheets' figures have a second idle frame with the head a pixel
    to one side, or another pose altogether (Gogeta's: eyes closed, and a walk frame from behind), which reads as a twitch. A rule, so
    it cannot come back with the next figure: any playable form's new actor whose two idle frames differ by more than IDLE_MAX pixels
    in a view shows its first idle frame for both in that view (the second frame's pointer becomes the first's; nothing is redrawn).
    -> [(form, [views])]. test_frames.py holds every form to it."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    names = {f: n for n, f in index.items()}; seen = set(); done = []
    for f in range(max(index.values()) + 1):
        actor = struct.unpack_from('<H', rom, SPACE + FORM_SIZE * f + 0x0E)[0] - 9
        if actor < ACTOR_BASE or actor in seen or names.get(f) in IDLE_WAITS: continue
        seen.add(actor)
        ptr = u(ACTORS_AT + 4 * actor)
        if not ROM_BASE < ptr < ROM_BASE + len(rom): continue
        rec = ptr - ROM_BASE; ap = u(rec + 0x54)
        if not ap or u(ap - ROM_BASE) < 2: continue
        a = ap - ROM_BASE; views = []
        if a < SPACE: continue                                    # (an animation of the game's own, shared with its actor)
        for v in range(4):
            f0, f1 = u(a + 4 + 4 * v), u(a + 4 + 16 + 4 * v)
            if not f0 or not f1 or f0 == f1: continue
            if int((frame_canvas(rom, f0) != frame_canvas(rom, f1)).sum()) > IDLE_MAX:
                struct.pack_into('<I', rom, a + 4 + 16 + 4 * v, f0); views.append(('front', 'back', 'left', 'right')[v])
        if views: done.append((names.get(f, 'form %d' % f), views))
    return done


def main():
    debug = '--debug' in sys.argv
    clean = open('baserom.gba', 'rb').read()
    if hashlib.sha1(clean).hexdigest() != CLEAN_SHA1:
        sys.exit("baserom.gba isn't the clean Buu's Fury (USA) ROM (SHA-1 mismatch).")
    if not os.path.exists('assets/manifest.json'):
        subprocess.run(['make', 'extract'], check=True, stdout=subprocess.DEVNULL)
    cfg = json.load(open('ultimate/forms.json'))
    cfg['rows'] += kaioken_rows(clean)
    if [r['id'] for r in cfg['rows']].index('shelved_ape_kid_goku') + FORM_COUNT != SHELVED_FIRST_FORM:
        sys.exit('the shelved Great Ape forms moved off 159-161 (a Nov 9 save reads them there): keep them there, new forms after them')
    if len(cfg['rows']) + FORM_COUNT != SHELVED_FIRST_FORM + len(SHELVED_FORMS):
        sys.exit('a form row was added before the shelved Great Ape forms: saved form ids after it would move (forms.json rows_after)')
    cfg['rows'] += cfg.pop('rows_after', [])          # new forms (Nov 10 on), from 162
    saved = {p: open(p).read() for p in (INTRO, FIELD, ACTORS_FILE, ENDING)}
    try:
        for p, s in unlock_edits_paths().items():
            saved.setdefault(p, s)
        unlock_edits()
        saved.setdefault(QUEST_NPC, open(QUEST_NPC).read())
        saved.setdefault(UI, open(UI).read())
        open(UI, 'w').write(re.sub(r'(?m)^1053\t.*$', '1053\tPress the B Button to gather energy above you, then throw it. It uses half your energy.', re.sub(r'(?m)^1050\t.*$', '1050\tSpirit Bomb', saved[UI])))
        saved.setdefault(BROLY_DEFEAT, open(BROLY_DEFEAT).read())
        open(BROLY_DEFEAT, 'w').write(broly_defeat(saved[BROLY_DEFEAT]))
        # A fusion's end (global script 503) took Gogeta out by name whoever had fused: it takes out whoever plays now (the fused fighter:
        # Gogeta, or the Potara's Vegito, Nov 12). Gotenks's branch already did.
        saved.setdefault(FUSION_END, open(FUSION_END).read())
        if saved[FUSION_END].count('    call 0x98(7)\n') != 1: sys.exit('global script 503 changed')
        open(FUSION_END, 'w').write(saved[FUSION_END].replace('    call 0x98(7)\n', '    call 0x15\n    call 0x98\n'))
        ui = open(UI).read()
        for k, v in UI_EDITS.items():
            ui, n = re.subn(r'(?m)^%d\t.*$' % k, '%d\t%s' % (k, v), ui)
            if n != 1: sys.exit('UI string %d not found' % k)
        open(UI, 'w').write(ui)
        npc = quest_npc(saved[QUEST_NPC])
        open(QUEST_NPC, 'w').write(npc)
        saved.setdefault(TOUR_NPC, open(TOUR_NPC).read())
        open(TOUR_NPC, 'w').write(tournament_npc(saved[TOUR_NPC]))
        saved.setdefault(HUB_NPC, open(HUB_NPC).read())
        open(HUB_NPC, 'w').write(hub_npc(saved[HUB_NPC]))
        saved.setdefault(POPO_NPC, open(POPO_NPC).read())
        open(POPO_NPC, 'w').write(popo_npc(saved[POPO_NPC]))
        saved.setdefault(ROSHI_NPC, open(ROSHI_NPC).read())
        open(ROSHI_NPC, 'w').write(roshi_npc(saved[ROSHI_NPC]))
        saved.setdefault(DEATH_SCRIPT, open(DEATH_SCRIPT).read())
        open(DEATH_SCRIPT, 'w').write(death_script(saved[DEATH_SCRIPT]))
        if debug:
            debug_edits(FORM_COUNT)
        subprocess.run(['make', 'modern'], check=True, stdout=subprocess.DEVNULL)
    finally:
        for p, s in saved.items():
            open(p, 'w').write(s)
    rom = bytearray(open('buusfury_modern.gba', 'rb').read())
    if len(rom) != 0x800000 or set(rom[-16:]) != {0xFF}:
        sys.exit('modern ROM has outgrown the 8 MB base; move SPACE')
    rom += b'\xff' * (0x1800000 if ROM32 else 0x800000)
    actors, actors_end = add_actors(rom, clean)
    NEW_ACTORS.update(actors)
    index, free = patch_forms(rom, clean, cfg, actors)
    os.makedirs(OUT, exist_ok=True)
    json.dump(index, open(OUT + '/_forms.json', 'w'))
    free, actors_end = add_outfits(rom, clean, (free + 3) & ~3, actors_end)
    sys.path.insert(0, 'ultimate')
    import zone26
    mash_retune(rom)
    zone_end, zone_info = zone26.apply(rom, clean, PROTO, LOG2, actors_end, actors, debug and '--zone' in sys.argv, symbol('gUnknown_08785580'), symbol('gUnknown_08796114'), symbol('gUnknown_08786E68'))
    print('zone 26 tiles:', zone_info)
    actors_end = add_portraits(rom, clean, zone_end)      # 4 KB each: they live with the art, past the code area
    if {k: actors[k] for k in new_actor_ids()} != new_actor_ids():
        sys.exit('actor ids differ from the ones the quest script used')
    npc = symbol('gUnknown_080783A0') - ROM_BASE      # the quest giver stands still: his wander box shrinks to his own spot
    struct.pack_into('<4H', rom, npc - 8, 320, 360, 320, 360)
    struct.pack_into('<4H', rom, symbol('gUnknown_080783CC') - ROM_BASE - 8, 96, 328, 96, 328)      # and so does the tournament's
    struct.pack_into('<4H', rom, symbol('gUnknown_08078EA0') - ROM_BASE + 8, 288, 472, 288, 472)   # and Mr. Popo: he opens the Time Chamber
    roshi_box = symbol('gUnknown_08078D20') - ROM_BASE - 8                                          # and Master Roshi on his island: he joins after the ending
    if struct.unpack_from('<4H', rom, roshi_box) != (288, 360, 440, 448): sys.exit("Roshi's wander box moved")
    struct.pack_into('<4H', rom, roshi_box, 392, 376, 392, 376)
    if debug:
        at = (free + 3) & ~3
        code = save_stub(at)
        rom[at:at + len(code)] = code
        tab = struct.unpack_from('<I', rom, NATIVE_REFS[0])[0] - ROM_BASE      # the moved table
        struct.pack_into('<I', rom, tab + 4 * DEBUG_NATIVE, ROM_BASE + at + 1)
    os.makedirs(OUT, exist_ok=True)
    name = ('BFU_debug_enemy' if '--enemy' in sys.argv else 'BFU_debug_zone' if '--zone' in sys.argv else 'BFU_debug') if debug else 'BFU'
    high_end = sprites.HIGH_END or 0x1000000
    print('room left: code %d KB, art %d KB%s' % ((ACTORS_AT - free) >> 10, (0x1000000 - actors_end) >> 10, ', above 16 MB %d KB' % ((0x2000000 - high_end) >> 10) if ROM32 else ''))
    if free >= ACTORS_AT or actors_end > 0x1000000 or high_end > 0x2000000:
        sys.exit('ROM layout overflow: code ends %X (limit %X), sprites end %X, high sprites end %X' % (free, ACTORS_AT, actors_end, high_end))
    if ROM32:
        import rom32
        rom32.apply(rom, clean)                       # BF's EEPROM at 0x0DFFFF00, where a 32 MB cartridge answers
        size = rom32.SIZE
    else:
        size = (actors_end + 0xFFFFF) & ~0xFFFFF
    if FLASH_SAVE: flash_header(rom)
    actors_end, touched = ssj4_goku(rom, actors, actors_end)
    print('Super Saiyan 4 Goku: %d frames touched up, %d frame records through it' % touched)
    actors_end, touched = gogeta_fix(rom, actors, actors_end)
    print('Super Saiyan 4 Gogeta: %d pictures fixed, %d frame records through them' % touched)
    actors_end, touched = ssj4_fix(rom, actors, actors_end)
    print('Super Saiyan 4 Goku: %d pictures fixed as previewed, %d frame records through them' % touched)
    if actors_end > 0x1000000: sys.exit('ROM layout overflow after the Super Saiyan 4 passes: sprites end %X' % actors_end)
    still = idle_still(rom, index)
    if still: print('idles made still (their second frame moved the head or changed pose): %s' % ', '.join('%s %s' % (n, '/'.join(v)) for n, v in still))
    import lock                                       # approved figures (locked.json): the build stops if one changed
    lock.check(rom, index, lambda f: struct.unpack_from('<I', rom, ACTORS_AT + 4 * (struct.unpack_from('<H', rom, SPACE + FORM_SIZE * f + 0x0E)[0] - 9))[0] - ROM_BASE)
    out = bytes(rom[:size])
    if bps.apply(clean, bps.make(clean, out)) != out:
        sys.exit('BPS round trip failed')
    open('%s/%s.bps' % (OUT, name), 'wb').write(bps.make(clean, out))
    open('%s/%s_PERSONAL_USE_ONLY.gba' % (OUT, name), 'wb').write(out)
    ss2_lists = {str(u['flag']): symbol(u['list']) - ROM_BASE for u in json.load(open('ultimate/outfits.json'))['unlocks'] if u['flag'] >= SS2_FLAG}
    json.dump({'forms': index, 'first_free': hex(free), 'ss2_lists': ss2_lists, 'actors': {k: actors[k] for k in ('beerus', 'whis', 'garlic_jr', 'super_garlic', 'spice', 'vinegar', 'mustard', 'salt', 'makyan')}}, open('%s/%s.map.json' % (OUT, name), 'w'), indent=1)
    print('%s: %d bytes, sha1 %s, patch %d bytes, forms %s' % (name, len(out), hashlib.sha1(out).hexdigest(),
          os.path.getsize('%s/%s.bps' % (OUT, name)), index))


main()
