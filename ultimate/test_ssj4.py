#!/usr/bin/env python3
"""Super Saiyan 4 Goku's touch-up, read straight from a built ROM (no emulator). The owner, Nov 11 evening, over four looks: "use the new
Gogeta hair for the front view of SSJ4 Goku only"; "I don't want that gray strands in the front just the same colors as current";
"Stop with this head bob on the idle stuff"; "make sure the fur is always on his full arms in every frame and only his hands without
it, make sure hands never have the red fur on them"; "Don't take fur off the tail either"; "clean up the stray pixels"; "make his eyes
more yellowish"; "Fix the arms raised pose ... where his base form hair is on the sides"; then, 21:01, "Lock that Goku for now".
  python3 ultimate/test_ssj4.py [rom]
The frame-by-frame lists it holds the ROM to are ssj4_preview/armhand.py's (canvas places as lib4.Rom.frame lays a frame out)."""
import json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, HERE + '/lib', HERE + '/ssj4_preview']
import numpy as np
import lib4, armhand

ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba'
R = lib4.Rom(ROM); forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
AID = struct.unpack_from('<H', R.rom, 0x800000 + 24 * forms['kid_goku_ssj4'] + 0x0E)[0] - 9
SKIN, FUR, BLUE, DARK, GOLD = (200, 201, 202, 203, 16, 17), (31, 32, 33, 104, 105), (69, 158, 160), (1, 111, 112), 110
fails = []


def check(name, ok, note=''):
    print('PASS' if ok else 'FAIL', name, note if not ok else '', flush=True)
    if not ok: fails.append(name)


def fr(s, f, d): return R.frame(AID, s, f, d)
def n(c, colours, box=None):
    m = np.isin(c, colours)
    return int((m[box[0]:box[1] + 1, box[2]:box[3] + 1] if box else m).sum())


slots = R.slots(AID)
check('he has his figure (slots %d)' % len(slots), len(slots) >= 20 and slots.get(0) == 2 and slots.get(18) == 6)
check('his idle stands still, in every view', all((fr(0, 0, d) == fr(0, 1, d)).all() for d in range(3)))
front = fr(0, 0, 0); ys, xs = np.nonzero(front); top = ys.min()
hair = np.isin(front[top:top + 12], DARK); wide = max(int(np.nonzero(r)[0].max() - np.nonzero(r)[0].min() + 1) for r in hair if r.any())
check('his front hair is Gogeta\'s shape (wider than the sheet\'s 22)', wide >= 23, 'widest row %d' % wide)
check('in the two colours his hair had: no lighter grey strands', n(front[top:top + 18], (112,)) == 0, '%d pixels of the lighter grey' % n(front[top:top + 18], (112,)))
check('gold eyes from the front and from the side', n(front, (GOLD,)) == 2 and n(fr(0, 0, 2), (GOLD,)) >= 1, 'front %d, side %d' % (n(front, (GOLD,)), n(fr(0, 0, 2), (GOLD,))))
back = fr(0, 0, 1)
check('no light pixel left on the edge of his hair from behind', n(back, (117,)) == 0)
miss = []
for key, rects in armhand.FISTS.items():
    c = fr(*key)
    for r in rects:
        if n(c, SKIN, r) < 1: miss.append('%s %s' % (key, r))
check('every hand read as drawn in fur is skin (%d frames)' % len(armhand.FISTS), not miss and len(armhand.FISTS) >= 30, '%s' % miss[:6])
bare = []
for key, rects in armhand.ARMS.items():
    c = fr(*key)
    for r in rects:
        if n(c, SKIN, r): bare.append('%s %s: %d' % (key, r, n(c, SKIN, r)))
check('every arm read as left bare is fur (%d frames)' % len(armhand.ARMS), not bare and len(armhand.ARMS) >= 15, '%s' % bare[:6])
left = []
for key, rects in armhand.SLEEVES.items():
    for r in rects:
        if n(fr(*key), BLUE, r): left.append(str(key))
check('no sleeve of BF Goku\'s left in blue', not left, '%s' % left)
# the Kamehameha from the front: his two arms fur down to his wrists, his hands skin under them
bad = []
for f in range(1, 6):
    c = fr(18, f, 0); yy = np.nonzero(c.any(1))[0]; head = yy.min()
    arms, hands = c[head + 16:head + 20, 48:64], c[head + 20:head + 25, 48:64]
    if n(arms, FUR) < 20 or n(arms, SKIN) > 4 or n(hands, SKIN) < 14: bad.append('frame %d: arms fur %d skin %d, hands skin %d' % (f, n(arms, FUR), n(arms, SKIN), n(hands, SKIN)))
check('the Kamehameha from the front: fur arms, hands of skin', not bad, '%s' % bad)
# the arms-raised pose: his own head and hair, the same from every side (BF's faces the camera in all three views)
up = fr(13, 1, 0); yy, xx = np.nonzero(up)
check('arms raised: one frame for all three views', all((fr(13, 1, d) == up).all() for d in (1, 2)))
check('arms raised: his own head (gold eyes, hair behind his arms, no spikes out past them)', n(up, (GOLD,)) == 2 and xx.max() - xx.min() + 1 <= 26 and yy.max() - yy.min() + 1 >= 33,
      'gold %d, %d wide, %d tall' % (n(up, (GOLD,)), xx.max() - xx.min() + 1, yy.max() - yy.min() + 1))
check('arms raised: fur arms, hands of skin, blue wristbands', n(up[yy.min() + 9:yy.min() + 17, :], FUR) >= 40 and n(up[yy.min():yy.min() + 9], SKIN) >= 10 and n(up[yy.min():yy.min() + 10], BLUE) >= 6,
      'fur %d, hand skin %d, band %d' % (n(up[yy.min() + 9:yy.min() + 17, :], FUR), n(up[yy.min():yy.min() + 9], SKIN), n(up[yy.min():yy.min() + 10], BLUE)))
# the tail is fur in his standing frames (never turned to skin by the hand rules)
tail = n(fr(0, 0, 0)[:, 63:], FUR)
check('his tail is fur (out past his hip, standing)', tail >= 12, 'fur %d' % tail)

# --- Super Saiyan 4 Gogeta (the owner, 21:38: "Some weird clipping with Ssj4 Gogeta head and neck on side and back views especially on
# walk frames mainly"; 22:25: "The back ones still doing it it's by a pixel or two moving slightly to the side"; 22:35: "Okay good lock it
# for now"). gogeta_preview/fixes.py is what changed; held here to what the owner saw.
sys.path.insert(0, HERE + '/gogeta_preview')
import fixes
GOG = struct.unpack_from('<H', R.rom, 0x800000 + 24 * forms['gogeta_ssj4'] + 0x0E)[0] - 9
gs = R.slots(GOG)
def gf(s, f, d): return R.frame(GOG, s, f, d)
PADS = (64, 109)
st = gf(0, 0, 1); top = int(np.nonzero(st.any(1))[0].min()); piece = st[top:top + 17]      # his head and his two rows of shoulder pads
moved = []
for s in (1, 2):
    for f in range(4):
        c = gf(s, f, 1); t = int(np.nonzero(c.any(1))[0].min())
        if t - top not in (0, 1) or not (c[t:t + 17] == piece).all(): moved.append('%s %d' % (('walk', 'run')[s - 1], f + 1))
check('Gogeta from behind: head and shoulder pads one piece, never a step sideways, through the walk and the run', not moved and n(piece, PADS) >= 14, '%s' % moved)
def spots(c):
    return [(int(y), int(x)) for y, x in np.argwhere(c == 176) if 2 <= y and x + 3 < c.shape[1] and c[y, x + 1] == 2 and c[y, x + 2] == 77
            and c[y - 2, x + 1] == 0 and c[y - 2, x + 2] == 0 and c[y - 2, x] == 1 and c[y - 2, x + 3] == 1]
left = ['%d.%d/%d' % (s, f, d) for s in gs for f in range(gs[s]) for d in range(3) if spots(gf(s, f, d))]
side = gf(0, 0, 2); eye = [(int(y), int(x)) for y, x in np.argwhere(side == 176) if side[y, x + 1] == 2]
check('Gogeta from the side: no see-through spot over his eye in any frame', not left and eye and side[eye[0][0] - 2, eye[0][1] + 1] == 1 and side[eye[0][0] - 2, eye[0][1] + 2] == 62, '%s' % left[:8])
bare, nofist = [], []
for key, entries in fixes.ALL.items():
    if key[2] == 1: continue                                     # (from behind the head piece moves things; held above)
    c, b = gf(*key), R.frame(106, *key)
    for e in entries:
        if not isinstance(e[0], str) or e[0] not in ('arm', 'bare', 'fist'): continue
        r0, r1, c0, c1 = e[1]; box = np.zeros(c.shape, bool); box[r0:r1 + 1, c0:c1 + 1] = True
        bf_skin = box & np.isin(b, SKIN + (205, 206, 207)); skin = int((bf_skin & np.isin(c, SKIN + (205, 206, 207))).sum())
        if e[0] == 'fist' and not skin: nofist.append('%s %s' % (key, e[1]))
        if e[0] in ('arm', 'bare') and skin: bare.append('%s %s: %d' % (key, e[1], skin))
check('Gogeta walking and running: arms fur where they were bare', not bare, '%s' % bare[:6])
check('Gogeta walking and running: fists skin where they were fur', not nofist, '%s' % nofist[:6])
# his pads as the owner approved them (before: 0-6 pixels from the front and 0-4 from the side as he walked, 0 from the front as he ran).
# Running, the arm that swings forward crosses one shoulder from the front, and from the side in the first run frame it is the
# shoulder itself (BF draws none there): those frames show what is left of a pad.
pads = []
for s, d, least in ((1, 0, 6), (1, 2, 5), (2, 0, 2)):
    for f in range(4):
        c = gf(s, f, d); t = int(np.nonzero(c.any(1))[0].min())
        if n(c[t + 14:t + 20], PADS) < least: pads.append('%s %d %s: %d' % (('walk', 'run')[s - 1], f + 1, ('front', '', 'side')[d], n(c[t + 14:t + 20], PADS)))
check('Gogeta: his shoulder pads in every walk frame, front and side, and the run from the front', not pads, '%s' % pads)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
