#!/usr/bin/env python3
"""Beerus's figure in a built ROM is the look the owner approved (Nov 11, 17:56: "New side view and 34 pixels for sure looks better"):
the new side head (lib/beerus.py HEAD_SIDE_NEW) and him four rows taller (Beerus.frame, two through the torso and two through the legs).
  python3 ultimate/test_beerus.py ROM          (any build; reads baserom.gba and the build's .map.json)
Every frame of his actor is read back from the ROM the way the game lays it out (its pieces at their places, a mirrored frame's pieces
turned) and compared, pixel for pixel, with what lib/beerus.py makes of Kid Buu's frame; a frame that outgrew Kid Buu's box must be made
of pieces the game can draw, and no frame may need more sprite memory than his record reserves."""
import json, struct, sys
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import numpy as np
import beerus_preview as bp, goku_black
LOOK = (True, (2, 2)); STAND = {0: 34, 1: 34, 2: 33}      # the new side head; torso and legs; rows he stands tall, front, back, side
REMAP = {17: [(9, 0), (9, 1), (9, 2)] + [(15, k) for k in range(4)] + [(15, 3)] * 4}      # build.py cfg['beerus']: no death by dissolving
SHAPE = {(8, 8): (0, 0), (16, 16): (0, 1), (32, 32): (0, 2), (64, 64): (0, 3), (16, 8): (1, 0), (32, 8): (1, 1), (32, 16): (1, 2), (64, 32): (1, 3),
         (8, 16): (2, 0), (8, 32): (2, 1), (16, 32): (2, 2), (32, 64): (2, 3)}
path = sys.argv[1]; rom = open(path, 'rb').read(); B = bp.B
u = lambda o: struct.unpack_from('<I', rom, o)[0]
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
aid = json.load(open(path.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['actors']['beerus']
rec = u(u(0x3C0) - 4 - B + 4 * aid) - B; reserve = struct.unpack_from('<H', rom, rec + 2)[0]
R = bp.Rom(); conv = R.converter(*LOOK)
def shown(fp):
    """The frame as the game shows it, on a canvas round the actor's origin. -> (canvas, bytes of sprite memory, [problems])"""
    o = fp - B; c = np.zeros((112, 112), np.uint8); total = 0; bad = []
    for k in range(u(o)):
        x, y, w, h, a0, a1 = struct.unpack_from('<bbBBHH', rom, o + 8 + 12 * k)
        if (w, h) not in SHAPE or (a0 >> 14, a1 >> 14) != SHAPE[w, h]: bad.append('a %dx%d piece with attributes %04X %04X' % (w, h, a0, a1)); continue
        img = goku_black.tiles(rom, u(o + 16 + 12 * k) - B, w, h); total += w * h
        if a1 & 0x1000: img = img[:, ::-1]
        m = img > 0; c[84 + y:84 + y + h, 56 + x:56 + x + w][m] = img[m]
    return c, total, bad
frames = {}; wrong = []; most = 0; odd = []; n = 0; grown = 0
for s in range(rom[rec]):
    an = u(rec + 0x54 + 4 * s)
    if not an: continue
    an -= B
    for j in range(4 * u(an)):
        fp = u(an + 4 + 4 * j); frames[s, j] = fp
        if not fp or s in REMAP: continue
        f, d = divmod(j, 4); v = min(d, 2)
        got, total, bad = shown(fp); odd += ['%d.%d dir %d: %s' % (s, f, d, b) for b in bad]; most = max(most, total); n += 1
        src, at = R.frame(bp.KID_BUU, s, f, d)
        img, off = conv.frame(src, v); want = bp.placed(img, off, at); grown += img.shape != src.shape
        if struct.unpack_from('<H', rom, fp - B + 14)[0] & 0x1000: want = np.roll(want[:, ::-1], 16, 1)       # mirrored about his 16-pixel cell
        if (got != want).any(): wrong.append('%d.%d dir %d (%d pixels)' % (s, f, d, int((got != want).sum())))
check('every frame of his is the approved look, pixel for pixel: %d frames, %d of them lengthened%s' % (n, grown, '; wrong: ' + ', '.join(wrong[:6]) if wrong else ''), n > 150 and grown > 100 and not wrong)
check('every piece of his frames is a size the game draws, with its attributes%s' % ('; ' + '; '.join(odd[:4]) if odd else ''), not odd)
check('his largest frame takes %d bytes of sprite memory; his record reserves %d' % (most, reserve), most <= reserve)
for s, seq in REMAP.items():
    check('slot %d is still built from his hit and knockdown frames' % s, all(frames.get((s, 4 * k + d)) == frames.get((a, 4 * f + d)) for k, (a, f) in enumerate(seq) for d in range(4)))
for v, rows in STAND.items():
    c = shown(frames[0, v])[0]; ys = np.nonzero(c.any(1))[0]
    check('standing %s he is %d rows tall (%d), his feet where Kid Buu\'s were' % (('to the front', 'to the back', 'sideways')[v], rows, ys.max() - ys.min() + 1),
          ys.max() - ys.min() + 1 == rows and ys.max() == 84 + 6)
side = shown(frames[0, 2])[0]; ys, xs = np.nonzero(side); head = side[ys.min():ys.min() + 15]
tips = np.nonzero(head[0])[0]
check('his side view has two ears, their tips four pixels apart, and an eye of two gold pixels over a black pupil',
      len(tips) == 2 and tips[1] - tips[0] == 4 and (head == 1).sum() == 1 and bool((head[11:13] == R.one(bp.beerus.RGB['E'])).sum() >= 3))
print('ALL PASS' if not fails else 'FAILED: %s' % fails)
sys.exit(1 if fails else 0)
