#!/usr/bin/env python3
"""Sprite frames read straight from a built ROM (no emulator), for the animation bugs the owner found on Nov 9:
  python3 ultimate/test_frames.py [rom]
1. The firing pose (slot 18) of every actor this build adds: the Kamehameha holds frame 0 (the charge) and then shows frames 1 and 2 in turn
   while the beam is out, so a lengthened animation must keep each frame at its number (sprites.INDEXED). Spread out, frame 1 was the charge
   again and every GT fighter dropped back into it every few frames while firing ("the head is way too far back in that one side view").
2. Uub's and Majuub's flying (slot 15; "Those flying frames are super fucked for Uub/Majuub"): Majuub flies in his own outfit on Uub's flying
   (navy vest, white trousers; none of Uub's green), and seen from the front nothing but his hair and face is above his eyes (Goten's legs
   and boot soles left a green tuft and grey specks there). No dark purple specks (Goten's sleeve flicker) in either.
3-5. Feet on the ground, no shadow under either Broly, Super Garlic Jr. 6. GT Vegeta's change and Final Flash frames. 7. Super Saiyan Blue's hair.
8. Super Saiyan 4 Kid Goku's hands on the 10x Kamehameha. 9. Super Saiyan 4 Vegeta's Final Shine wind-up. (7 also: Blue Goku's and Blue
Vegeta's faces stay Super Saiyan's.)"""
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
names = {v: k for k, v in forms.items()}
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
        rows.append(struct.unpack_from('<b', rom, fp - BASE + 5)[0] + int(np.nonzero(img.any(1))[0].max()))
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


# 6. GT Vegeta (Nov 10, the owner: "his ssj4 transformation he did was the fusion dance not transformation frames", "his final shine frames
# are broken"). His change (slot 10) is his own power-up (slot 13): its two poses and then his stance, none of the sheet's "special" (slot 21,
# the arms flung out). Final Flash's code (Final Shine's too) shows slot 19's frames by number, 0-1 charging, 3-4 firing: frames 3 and 4 are
# the push, never frame 0, 1 or 2 again.
for name in ('vegeta_gt', 'vegeta_gt_tank', 'vegeta_gt_mustache', 'vegeta_gt_ssj', 'vegeta_gt_tank_ssj', 'vegeta_gt_ssj4'):
    a = actor_of(forms[name]); ch, pw, sp, st, fl = anim(a, 10), anim(a, 13), anim(a, 21), anim(a, 0), anim(a, 19)
    imgs = lambda fr: [[image(fp).tobytes() if image(fp) is not None else None for fp in f] for f in fr]
    C, P, SP, ST = imgs(ch), imgs(pw), imgs(sp) if sp else [], imgs(st)
    ok = len(C) == 11 and all(C[k][d] in (P[0][d], P[1][d]) for k in range(10) for d in range(3)) and C[10] == ST[0] \
         and not any(C[k][d] == x[d] for k in range(10) for x in SP for d in range(3))
    check('%s changes on his own power-up (slot 13, then his stance), not the sheet\'s "special"' % name, ok)
    F = imgs(fl)
    check('%s\'s Final Flash / Final Shine pushes the beam out: slot 19 frames 3 and 4 are none of 0, 1, 2' % name,
          len(F) >= 5 and all(F[k][d] not in (F[0][d], F[1][d], F[2][d]) for k in (3, 4) for d in range(3)))

# 7. Super Saiyan Blue (Nov 10, the owner: "Get the fucking hair RIGHT according to BUUS FURY GOGETA AND FIX SSB GOKUS HAIR NOT BEING FULLY
# BLUE WHY IS THERE STILL YELLOW"; lib/ssb.py). Blue Gogeta: every frame is one of Buu's Fury's own Super Saiyan Gogeta's (actor 93) in the
# same slot and view, the same figure pixel for pixel, and the only pixels that differ are his hair's (its gold, and the skin shades in it),
# in Blue Goku's hair colours (those his Blue idle has that Super Saiyan Goku's hasn't); no gold left anywhere; one 1 KB piece each.
# Blue Goku and Blue Vegeta: no gold left in their hair (the pure golds 28, 29 and 246 anywhere, or a gold shade on the hair's outer edge).
gk, gg = actor_of(forms['goku_ssb']), actor_of(forms['gogeta_ssb'])
goku_blue = set()
for i, f in enumerate(anim(gk, 0)):
    gimg, bimg = image(f[0]), image(anim(actor_of(3), 0)[i][0])       # Blue Goku's idle against Super Saiyan Goku's: the hair's blues
    if gimg is not None and bimg is not None and gimg.shape == bimg.shape: goku_blue |= set(np.unique(gimg[gimg != bimg]).tolist())
def placed(fp):
    """A frame on a 64 x 64 canvas, where the game draws it (the piece's x, y from the origin)."""
    c = np.zeros((64, 64), np.uint8); img = image(fp)
    if img is None: return None
    x, y = struct.unpack_from('<bb', rom, fp - BASE + 4); h, w = img.shape
    if struct.unpack_from('<H', rom, fp - BASE + 4 + 10)[0] & 0x1000: img = img[:, ::-1]      # a mirrored piece
    c[40 + y:40 + y + h, 24 + x:24 + x + w] = img
    return c
GOLD = [25, 26, 27, 28, 29, 30]
n4 = lambda m: (lambda q: q[:-2, 1:-1] | q[2:, 1:-1] | q[1:-1, :-2] | q[1:-1, 2:])(np.pad(m, 1))
bad_shape, bad_hair, big, gold_left = [], [], [], []
for slot in range(20):
    fr, sf = anim(gg, slot), anim(93, slot)
    if not fr: bad_shape.append((slot, 'missing')); continue
    for i, f in enumerate(fr):
        for d in range(3):
            img = image(f[d])
            if img is None: continue
            if img.shape[0] * img.shape[1] > 1024: big.append((slot, i, d))
            if np.isin(img, GOLD).any(): gold_left.append((slot, i, d, int(np.isin(img, GOLD).sum())))
            if slot in (8, 10, 11) or not sf: continue                       # (his figure lacks these: filled from his own poses)
            blue = placed(f[d]); same = [c for c in (placed(g[d]) for g in sf) if c is not None and (c != 0).tolist() == (blue != 0).tolist()]
            if not same: bad_shape.append((slot, i, d)); continue
            ok = False
            for ss in same:
                diff = blue != ss
                if np.isin(ss[diff], GOLD + [202, 201, 16]).all() and np.isin(blue[diff], list(goku_blue)).all(): ok = True; break   # (none, if no hair shows)
            if not ok: bad_hair.append((slot, i, d))
check('Blue Gogeta is Buu\'s Fury\'s Super Saiyan Gogeta pixel for pixel, the same hair shape%s' % ((': %s' % bad_shape[:6]) if bad_shape else ''), not bad_shape)
check('only his hair changed, into Blue Goku\'s hair colours %s%s' % (sorted(goku_blue), (': %s' % bad_hair[:6]) if bad_hair else ''), goku_blue and not bad_hair)
check('no gold left anywhere on Blue Gogeta%s' % ((': %s' % gold_left[:6]) if gold_left else ''), not gold_left)
check('every Blue Gogeta frame is one piece of at most 1 KB%s' % ((': %s' % big[:6]) if big else ''), not big)
yellow = []
for name in ('goku_ssb', 'goku_ssb_b', 'vegeta_ssb', 'vegeta_ssb_b'):
    for slot in range(22):
        for i, f in enumerate(anim(actor_of(forms[name]), slot) or []):
            for d in range(3):
                img = image(f[d])
                if img is None: continue
                pure = np.isin(img, [28, 29, 246]).sum()                      # his hair's own golds, anywhere
                ys = np.nonzero(img.any(1))[0]
                tips = np.isin(img[ys.min():ys.min() + 4], [202, 201, 16, 2]).sum() if slot <= 2 and len(ys) else 0   # standing, walking, running: the spikes' tips (other poses raise a fist above them)
                if pure or tips: yellow.append((name, slot, i, d, int(pure), int(tips)))
check('Blue Goku\'s and Blue Vegeta\'s hair has no gold left (none of 28, 29, 246; standing, walking or running, no gold shade in the spikes\' top 4 rows)%s' % ((': %s' % yellow[:6]) if yellow else ''), not yellow)
from scipy import ndimage
# ... and only their hair changed (Nov 10, the owner: "Fix some of SSB Goku and vegetas face pixels being blue", "DONT MAKE THEIR FUCKING
# FOREHEAD SKIN BLUE OR THEIR EARS EITHER JUST THE HAIR", "you put the blue pixel back in vegetas face again"): every frame against the
# Super Saiyan figure it's made from, and that against the base figure laid under it (lib/ssb.base_under, the retail ROM's frames):
# - the eyes' whites (white beside an eye's green) are unchanged;
# - no pixel the Super Saiyan figure draws exactly as the base figure does (his skin, forehead, ears) turned blue, unless blue walls it
#   in on all sides (a speck of up to 3);
# - no skin shade with the face's skin (200, 203) or an eye directly left or right of it turned blue, but for Goku's sideburn: seen from
#   the side, on the eye's rows (and the one above), behind the eye.
# And no gold left in the hair ("YOU STILL HAVE LEFT YELLOW ON THE SIDES OF GOKU SSB", "THE SIDES OF GOKUS HAIR AROUND HIS EARS ARE
# YELLOW STILL"): no hair shade the Super Saiyan figure draws differently from the base figure, not beside the face or an eye, left gold
# with blue on three sides; and Goku's sideburn blue (there, a shade drawn differently from the base figure's skin, next to the blue).
import ssb
retail = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'baserom.gba'), 'rb').read()
SKIN_SHADES = (16, 201, 202)
def behind_eye(b):
    """Seen from the side (one eye): the eye's rows and the one above, behind the eye (away from where he looks)."""
    iris = np.isin(b, (215, 216)); zone = np.zeros(b.shape, bool)
    if ndimage.label(iris, np.ones((3, 3)))[1] != 1: return zone
    rows, cols = np.nonzero(iris); fig = np.nonzero(b[rows.min():rows.max() + 1].any(0))[0]
    if cols.min() - fig.min() < fig.max() - cols.max(): zone[rows.min() - 1:rows.max() + 1, cols.max() + 2:] = True
    else: zone[rows.min() - 1:rows.max() + 1, :max(0, cols.min() - 1)] = True
    return zone
face_blue, edge_gold = [], []
for name, ss, base in (('goku_ssb', 3, 0), ('goku_ssb_b', 4, 2), ('vegeta_ssb', 28, 26), ('vegeta_ssb_b', 29, 27), ('vegeta_armor_ssb', forms['vegeta_armor_ss'], None)):
    under = ssb.base_under(retail, actor_of(ss), actor_of(base)) if base is not None else {}
    for slot in range(22):
        A, B = anim(actor_of(forms[name]), slot), anim(actor_of(ss), slot)
        for i, (f, g) in enumerate(zip(A or [], B or [])):
            for d in range(3):
                a, b = image(f[d]), image(g[d])
                if a is None or b is None or a.shape != b.shape: continue
                ew = (b == 2) & ndimage.binary_dilation(np.isin(b, (215, 216)), np.ones((3, 3), bool))
                blue = a != b
                h = np.pad(blue, 1); nh = h[:-2, 1:-1].astype(int) + h[2:, 1:-1] + h[1:-1, :-2] + h[1:-1, 2:]
                ub = under.get((b.shape, b.tobytes()))
                same = (b == ub) & np.isin(b, SKIN_SHADES) if ub is not None else np.zeros(b.shape, bool)
                skin_blue = same & blue
                lab, nl = ndimage.label(skin_blue)
                for k in range(1, nl + 1):
                    m = lab == k
                    if m.sum() <= 3 and blue[ndimage.binary_dilation(m) & ~m].all(): skin_blue &= ~m
                q = np.pad(np.isin(b, (200, 203, 215, 216)) | ew, 1)
                zone = behind_eye(b) if name.startswith('goku') else np.zeros(b.shape, bool)
                outline = blue & np.isin(b, SKIN_SHADES) & (q[1:-1, :-2] | q[1:-1, 2:]) & ~zone
                n = int((ew & blue).sum() + skin_blue.sum() + outline.sum())
                if n: face_blue.append((name, slot, i, d, n))
                if ub is None: continue
                e = np.pad(np.isin(b, (215, 216, 117, 118)) | ew, 1)
                by_eye = e[1:-1, :-2] | e[1:-1, 2:] | e[:-2, 1:-1] | e[2:, 1:-1]
                fc = np.pad(np.isin(b, ssb.FACE) | ew, 1)
                drawn = np.isin(b, SKIN_SHADES) & ~same & ~by_eye & ~blue
                gold = (drawn & ~(fc[1:-1, :-2] | fc[1:-1, 2:] | fc[:-2, 1:-1]) & (nh >= 3)) | \
                       (drawn & zone & ~np.isin(ub, ssb.BASE_HAIR) & (h[1:-1, :-2] | h[1:-1, 2:] | h[:-2, 1:-1]))
                if gold.any(): edge_gold.append((name, slot, i, d, int(gold.sum())))
check('Blue Goku\'s and Blue Vegeta\'s faces aren\'t blue (the eyes\' whites, the base figure\'s skin: face, forehead, ears, and the face\'s outline)%s' % ((': %s' % face_blue[:6]) if face_blue else ''), not face_blue)
check('no gold left in their hair (no gap in it; Goku\'s sideburns blue)%s' % ((': %s' % edge_gold[:6]) if edge_gold else ''), not edge_gold)
eyes = []                                  # his base and Super Saiyan looks: the sheet's eyes were dropped as background (gogeta.frame)
for name in ('gogeta_dbs', 'gogeta_dbs_ss'):
    for slot in range(22):
        for i, f in enumerate(anim(actor_of(forms[name]), slot) or []):
            for d in range(3):
                img = image(f[d])
                if img is None: continue
                lab, n = ndimage.label(ndimage.binary_fill_holes(img != 0) & (img == 0))
                if any((lab == t).sum() <= 4 for t in range(1, n + 1)): eyes.append((name, slot, i, d))
check('Gogeta\'s base and Super Saiyan eyes aren\'t see-through (no pinhole of 4 pixels or fewer inside him)%s' % ((': %s' % eyes[:4]) if eyes else ''), not eyes)

# 8. Super Saiyan 4 Kid Goku's hands (Nov 10, the owner: "Goku hand still red on 10x kame"; gt.ssj4_hands): the sheet drew his arms' fur
# over his hands too. Pushing the beam out from the side (slot 18, frames 1 and 2), the hand at the front of his outstretched arms (the
# figure's three leftmost columns) is skin, not fur, and his forearm behind it is still fur ("You got rid of the fur on his ARMS I said his
# HANDS only": only the firing pose's hands change).
FUR, SKIN = [31, 32, 33, 105], [16, 200, 201, 202, 203]
fr = anim(actor_of(forms['kid_goku_ssj4']), 18); bad = []
for k in (1, 2):
    img = image(fr[k][2]) if fr and k < len(fr) else None
    if img is None: bad.append((k, 'no frame')); continue
    xs = np.nonzero(img.any(0))[0]; front = img[:, xs.min():xs.min() + 3]
    arm = img[:, xs.min() + 6:xs.min() + 12]                             # the forearm behind the hand and its band
    if np.isin(front, FUR).any() or np.isin(front, SKIN).sum() < 6 or np.isin(arm, FUR).sum() < 10:
        bad.append((k, int(np.isin(front, FUR).sum()), int(np.isin(front, SKIN).sum()), int(np.isin(arm, FUR).sum())))
check('Super Saiyan 4 Kid Goku pushes the 10x Kamehameha out with skin hands, his arms still furred ("HANDS only")%s' % (': %s' % bad if bad else ''), not bad)

# 9. Super Saiyan 4 Vegeta's Final Shine wind-up (Nov 10, the owner: "final shine still off"; gt.shine_charge): seen from the side, slot 19
# frames 0-2 left his neck see-through and turned a glove to hair. Laid on BF Vegeta's own frames (actor 270, which his page was drawn on)
# at their best overlap, none of BF's body (not his hair, not the charge glow) is see-through, and frame 2's glove is lavender again.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import goku_black
bfv = goku_black.actor_frames(open('baserom.gba', 'rb').read(), 270)[19][2]
fr = anim(actor_of(forms['vegeta_gt_ssj4']), 19); bad = []
for k in range(3):
    img = image(fr[k][2]); b = bfv[k]; H, W = img.shape
    body = (b != 0) & ~np.isin(b, (1, 112, 5)); best = None
    for dy in range(-4, 5):
        for dx in range(-W, b.shape[1]):
            cv = np.zeros_like(b); y0, x0 = b.shape[0] - H + dy, dx
            ys, xs = slice(max(0, y0), min(b.shape[0], y0 + H)), slice(max(0, x0), min(b.shape[1], x0 + W))
            if ys.stop <= ys.start or xs.stop <= xs.start: continue
            cv[ys, xs] = img[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
            score = ((cv != 0) & body).sum()
            if best is None or score > best[0]: best = (score, int((body & (cv == 0)).sum()), cv)
    upper = best[2][:20]
    if best[1] > 2 or (k == 2 and np.isin(upper, [151, 169]).sum() < 12): bad.append((k, best[1], int(np.isin(upper, [151, 169]).sum())))
check('Super Saiyan 4 Vegeta\'s Final Shine wind-up seen from the side: nothing see-through where BF Vegeta has his body, his glove lavender%s' % (': %s' % bad if bad else ''), not bad)

if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
