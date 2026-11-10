#!/usr/bin/env python3
"""Sprite frames read straight from a built ROM (no emulator), for the animation bugs the owner found on Nov 9:
  python3 ultimate/test_frames.py [rom]
1. The firing pose (slot 18) of every actor this build adds: the Kamehameha holds frame 0 (the charge) and then shows frames 1 and 2 in turn
   while the beam is out, so a lengthened animation must keep each frame at its number (sprites.INDEXED). Spread out, frame 1 was the charge
   again and every GT fighter dropped back into it every few frames while firing ("the head is way too far back in that one side view").
2. Uub's and Majuub's flying (slot 15; "Those flying frames are super fucked for Uub/Majuub"): Majuub flies in his own outfit on Uub's flying
   (navy vest, white trousers; none of Uub's green), and seen from the front nothing but his hair and face is above his eyes (Goten's legs
   and boot soles left a green tuft and grey specks there). No dark purple specks (Goten's sleeve flicker) in either.
3-5. Feet on the ground, no shadow under either Broly, Super Garlic Jr.'s frames. 6. The Great Ape's frames (boss and playable)."""
import json, struct, sys, os
import numpy as np
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')]
import sprites
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
rom = open(ROM, 'rb').read(); BASE = 0x08000000
u = lambda o: struct.unpack_from('<I', rom, o)[0]
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
LIST = u(0x3C0) - BASE - 4                       # the actor table (build.py relocates it; the code reads it from this literal)
FIRST_NEW = 298                                  # retail actors are 0-297
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)

def actor_of(form): return struct.unpack_from('<H', rom, 0x800000 + 24 * form + 0x0E)[0] - 9
def anim(actor, slot):
    rec = u(LIST + 4 * actor) - BASE
    if (u(rec) & 0xFF) <= slot or not u(rec + 0x54 + 4 * slot): return None
    a = u(rec + 0x54 + 4 * slot) - BASE; n = u(a)
    return [[u(a + 4 + 16 * i + 4 * d) for d in range(3)] for i in range(n)]
def image(fp):
    return sprites.frame_image(rom, fp) if fp and u(fp - BASE) == 1 else None

# 1. slot 18 of every added actor: per view, new frames in order, then only the last one repeated (never back to an earlier frame)
n_actors, bad = 0, []
for a in range(FIRST_NEW, FIRST_NEW + 400):
    p = u(LIST + 4 * a)
    if not BASE <= p < BASE + len(rom) or not 0 < u(p - BASE) & 0xFF <= 32: break
    n_actors += 1
    fr = anim(a, 18)
    if not fr or len(fr) < 2: continue
    for d in range(3):
        seq = [f[d] for f in fr]; seen = []
        for i, f in enumerate(seq):
            if f in seen and (f != seq[i - 1] or any(g != f for g in seq[i:])): bad.append((a, d, seq.index(f), i)); break
            if f not in seen: seen.append(f)
print('   %d added actors; firing poses that go back to an earlier frame: %s' % (n_actors, bad[:8]))
check('every added actor\'s firing pose keeps its frames in order (frames 1 and 2 are never the charge again)', n_actors > 50 and not bad)

# 2. Uub and Majuub flying
UUB, MAJUUB = actor_of(forms['uub']), actor_of(forms['majuub'])
GREEN, NAVY, WHITE, SPECK = {216, 251, 252}, 70, {117, 119, 120}, 157
mj = anim(MAJUUB, 15); ub = anim(UUB, 15)
cols = lambda fr, d: set(np.concatenate([np.unique(image(f[d])) for f in fr]).tolist())
print('   actors: Uub %d, Majuub %d; Majuub\'s flying colours front %s side %s' % (UUB, MAJUUB, sorted(cols(mj, 0)), sorted(cols(mj, 2))))
check('Majuub flies in his own outfit: navy vest, white trousers, none of Uub\'s green',
      all(not (cols(mj, d) & GREEN) for d in range(3)) and NAVY in cols(mj, 0) and NAVY in cols(mj, 2) and cols(mj, 2) & WHITE)
check('Majuub flies in Uub\'s flying poses (same outline, frame by frame)',
      len(mj) == len(ub) and all(np.array_equal(image(a[d]) > 0, image(b[d]) > 0) for a, b in zip(mj, ub) for d in range(3)))
def above_eyes(img):
    e = np.argwhere(img == 2)
    return set(np.unique(img[:e[:, 0].min()]).tolist()) - {0} if len(e) else {'no eyes'}
tops = [above_eyes(image(f[0])) for f in ub + mj]
print('   colours above the eyes, flying at the camera:', sorted(set().union(*tops), key=str))
check('flying at the camera, only hair and face above his eyes (no green tuft, no grey soles)', all(t <= {1, 77, 78, 79, 16, 17, 202, 117} for t in tops))   # (117: the grey top of his eyes)
specks = [(n, s) for n, a in (('uub', UUB), ('majuub', MAJUUB)) for s in range(22) if anim(a, s)
          for f in anim(a, s) for d in range(3) if image(f[d]) is not None and (image(f[d]) == SPECK).any()]
check('no dark purple specks in any of Uub\'s or Majuub\'s frames%s' % (': %s' % sorted(set(specks)) if specks else ''), not specks)

# 3. Feet on the ground (Nov 9, the owner: "fix Broly looking like he's floating still"): the game draws the shadow from the actor record, so
# every form whose record has the same collision boxes (+0x14..+0x53: the same template) stands with its feet on the same row under its origin.
# Broly Full Power copies BF Broly's record (feet 15 rows down) with frames lined up like a fighter's (7): he hovered over his shadow.
# The Great Ape's figures are drawn twice the size about each frame's piece centre (outfit.c big_check; lib/sprites.py 'scale2'), so their
# feet are where the drawn picture ends: the piece's centre, plus twice the rows from there to its last row.
names = {v: k for k, v in forms.items()}
TWICE = {v for k, v in json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json'))).get('actors', {}).items() if k.startswith('oozaru')}
def feet(a, fp, img):
    y, last = struct.unpack_from('<b', rom, fp - BASE + 5)[0], int(np.nonzero(img.any(1))[0].max())
    return y - img.shape[0] // 2 + 2 * last + 1 if a in TWICE else y + last
groups = {}
for f in range(max(forms.values()) + 1):
    a = actor_of(f)
    if not 0 <= a < FIRST_NEW + n_actors: continue
    fr = anim(a, 0)
    if not fr: continue
    rows = []
    for fp in fr[0]:
        img = image(fp)
        if img is None or not img.any(): continue
        rows.append(feet(a, fp, img))
    if rows: groups.setdefault(rom[u(LIST + 4 * a) - BASE + 0x14:u(LIST + 4 * a) - BASE + 0x54], []).append((names.get(f, f), max(rows)))
spread = [v for v in groups.values() if max(r for _, r in v) - min(r for _, r in v) > 2]
print('   %d groups of forms sharing a record\'s boxes; feet rows of broly / broly_fp: %s' % (len(groups), [v for v in groups.values() if any(n == 'broly' for n, _ in v)]))
check('forms built on the same template stand on the same row (no one floats over his shadow)%s' % (': %s' % spread if spread else ''), not spread)

# 4. No ground shadow under either Broly ("Remove the shadow beneath Broly's feet too cause it looks off"): the record's +0xA/+0xB size
# isn't one of the game's four shadows (0x086B759C), so none is made; everyone else keeps theirs.
SHADOWS = {tuple(rom[0x6B759C + 16 * k:0x6B759C + 16 * k + 2]) for k in range(4)}
shadow = lambda f: tuple(rom[u(LIST + 4 * actor_of(f)) - BASE + 0xA:u(LIST + 4 * actor_of(f)) - BASE + 0xC])
print('   shadow sizes: broly %s, broly_fp %s, goku %s, majin_buu %s; the game\'s: %s' % (shadow(forms['broly']), shadow(forms['broly_fp']), shadow(0), shadow(forms['majin_buu']), sorted(SHADOWS)))
check('neither Broly has a ground shadow; Goku and the other big fighters keep theirs',
      shadow(forms['broly']) not in SHADOWS and shadow(forms['broly_fp']) not in SHADOWS and shadow(0) in SHADOWS and shadow(forms['majin_buu']) in SHADOWS)

# 5. Super Garlic Jr. (lib/super_garlic.py, Nov 9: "remove the singlet ... fill his abs ... remove the majin head symbol and give him the brain
# grooves", "Fix the pants and waistband too and don't let it ever overlap the arms"): Spopovich's every frame, none of Spopovich left in it.
actors = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json'))).get('actors', {})
if 'super_garlic' in actors:
    sg, spop = actors['super_garlic'], 243
    SPOP_SKIN = {16, 17, 18, 19, 20, 21, 22, 23, 30, 203, 245, 205, 206, 208, 202, 84, 68, 82, 229, 141, 142, 213}
    YELLOW = {109, 249, 81}
    same, left, mark, teal, n = True, set(), [], 0, 0
    for slot in range(24):
        a, b = anim(sg, slot), anim(spop, slot)
        if (a is None) != (b is None) or (a and len(a) != len(b)): same = False
        for i, views in enumerate(a or []):
            for d, fp in enumerate(views):
                img = image(fp)
                if img is None: continue
                n += 1; cols = set(np.unique(img).tolist())
                left |= cols & (SPOP_SKIN | YELLOW)
                teal += bool(cols & {70, 187, 252, 253, 254})
                for y in range(img.shape[0]):
                    r = img[y]
                    if any(r[x] == 1 and r[x + 2] == 1 and r[x + 4] == 1 and r[x + 1] == 16 and r[x + 3] == 16 for x in range(img.shape[1] - 4)):
                        mark.append((slot, i, d)); break
    check('Super Garlic Jr. has every slot Spopovich\'s behaviour plays, frame for frame (%d frames)' % n, same and n > 100)
    check('no Spopovich left in Super Garlic Jr.: no tan skin, no yellow boots%s' % (': %s' % sorted(left) if left else ''), not left)
    check('no Majin mark on Super Garlic Jr.\'s forehead%s' % (': %s' % mark if mark else ''), not mark)
    check('every Super Garlic Jr. frame is teal', teal == n)
    st = image(anim(sg, 0)[0][0])                                      # standing, from the front: the sash, the trousers, the ears
    ys = [y for y in range(st.shape[0]) if (st[y] == 2).sum() >= 8]
    check('standing, a white sash across his waist with black trousers under it', bool(ys) and ((st[ys[0] + 3] == 112) | (st[ys[0] + 3] == 111) | (st[ys[0] + 3] == 1)).sum() >= 10)
    top = min(y for y in range(st.shape[0]) if st[y].any())
    ears = [x for x in range(st.shape[1]) if st[top + 2:top + 6, x].any()]
    check('standing, his ears stand out on both sides of his head', bool(ears) and max(ears) - min(ears) >= 24)
else:
    check('Super Garlic Jr. is in this build', False)

# 6. The Great Ape (lib/oozaru.py, the owner's sheets): the raid's boss on Broly's record, every slot Broly has, frame for frame; GT Kid Goku's
# and GT Vegeta's figures in every player slot, at least a retail player's length; the fur the game's red-brown ramp (not the grey-green tan
# the nearest colour gave), the mouths dark red, the power-up's aura white, not the sheet's pink ("also make that aura white not pink"); no
# ground shadow; the change starts on the small Saiyan and ends on the ape, the change back the other way round.
if 'oozaru' in actors:
    FUR, PINK, AURA, MOUTH = {62, 208, 207, 211, 212}, {144, 145}, {120, 171}, 31
    boss, apes = actors['oozaru'], (actors['oozaru_kid_goku'], actors['oozaru_vegeta'])
    same = all((anim(boss, s) is None) == (anim(29, s) is None) and (anim(boss, s) is None or len(anim(boss, s)) == len(anim(29, s))) for s in range(22))
    check('the Great Ape boss has every slot BF Broly has, frame for frame', same)
    player = [s for s in range(22) if anim(106, s)]
    full = all(anim(a, s) and len(anim(a, s)) >= len(anim(106, s)) for a in apes for s in player)
    check('both playable Great Apes have every slot BF Goku has, at least as long (%s)' % player, full)
    seen, pink, frames = set(), [], 0
    for a in (boss,) + apes:
        for s in range(22):
            for k, views in enumerate(anim(a, s) or []):
                for d, fp in enumerate(views):
                    img = image(fp)
                    if img is None: continue
                    frames += 1; c = set(np.unique(img).tolist()); seen |= c
                    if c & PINK: pink.append((a, s, k, d))
    check('the fur is the game\'s red-brown ramp, and no grey-green tan (%d frames)' % frames, FUR <= seen and 204 not in seen)
    check('no pink anywhere: the power-up\'s aura is white%s' % (': %s' % pink[:6] if pink else ''), not pink and AURA <= seen)
    roar = image(anim(boss, 21)[1][2])
    check('the roar shows the mouth filled dark red', roar is not None and (roar == MOUTH).sum() >= 6)
    no_shadow = [a for a in (boss,) + apes if tuple(rom[u(LIST + 4 * a) - BASE + 0xA:u(LIST + 4 * a) - BASE + 0xC]) in SHADOWS]
    check('no ground shadow under any Great Ape', not no_shadow)
    height = lambda fp: int(np.count_nonzero(image(fp).any(1)))
    for a in apes:
        ch, back = anim(a, 10), anim(a, 11)
        check('actor %d: the change grows the Saiyan into the ape (%d to %d rows), the change back shrinks him' % (a, height(ch[0][0]), height(ch[-1][0])),
              height(ch[0][0]) < 34 < 48 < height(ch[-1][0]) and height(back[0][0]) > 48 and height(back[-1][0]) < 34)
else:
    check('the Great Ape is in this build', False)

if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
