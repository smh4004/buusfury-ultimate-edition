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
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
