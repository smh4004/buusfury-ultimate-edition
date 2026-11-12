"""Super Saiyan 4 Goku's arms in his walk and run, every view: fur on the whole arm, the wristband blue, the hand skin. The owner, Nov 11
19:29: "make sure the fur is always on his full arms in every frame and only his hands without it, make sure hands never have the red
fur on them"; Nov 12 07:01, after these fixes were dropped from a preview: "I meant the fur on his arms ... which no you DID NOT FIX
STILL", "Why ... are you working backwards ... we've already fixed multiple times now".

Read against BF Goku's frame under each (same canvas): BF's undershirt sleeve left blue on his shoulder and the arm under it bare skin,
where his standing frames have fur. Each entry is a list for one frame (slot, frame, view):
  ('fur', (row0, row1, col0, col1)): his skin and blue in the box become fur: his standing frame's fur shade at that pixel when it has
  fur there, else the touch-up's shade maps;
  ('blue', box): his fur where BF has his navy wristband becomes the wristband's blue;
  ('gap', box): a see-through pixel in the box becomes his dark fur (31), as on his other side.
His skin includes BF's two darker skin shades 205 and 206, which the sheet left as brown dots in his fur (the owner, Nov 12 07:14:
"Fix the messed up pixel on his right arm in back view": from behind, his right arm had a brown dot in walk frame 3 and run frames
2-4, and a see-through pixel between his sash and his right wristband standing, walking and running).
(First made Nov 12 00:06 in walkfix.py, which also moved his head and his tail; those are out.)"""
import numpy as np

SKIN_FUR = {16: 31, 17: 31, 202: 32, 203: 32, 201: 33, 200: 105, 205: 32, 206: 32}   # armhand.TO_FUR, and BF's 205, 206
BLUE_FUR = {69: 31, 158: 32, 160: 33}                                     # armhand.BLUE_FUR
BF_BAND = {157: 69, 159: 158, 161: 160}                                   # gt.BF_BAND
FURS = (31, 32, 33, 104, 105)

FIXES = {
    # from the side: the walk
    (1, 0, 2): [('fur', (57, 58, 52, 52)), ('fur', (58, 58, 51, 51)), ('fur', (59, 59, 52, 52)),            # the arm swinging forward
                ('fur', (57, 57, 59, 61)), ('fur', (58, 58, 58, 61)), ('fur', (59, 60, 59, 62)), ('fur', (61, 61, 59, 60))],   # and back
    (1, 1, 2): [('fur', (57, 57, 55, 60)), ('fur', (58, 60, 56, 59))],
    (1, 2, 2): [('fur', (56, 57, 59, 61)), ('fur', (58, 58, 60, 61)), ('fur', (59, 59, 60, 60))],
    # from the side: the run (the arm that swings back)
    (2, 0, 2): [('fur', (57, 57, 60, 62))],
    (2, 1, 2): [('fur', (55, 55, 58, 62)), ('fur', (56, 56, 58, 60))],
    (2, 2, 2): [('fur', (57, 57, 60, 63)), ('fur', (58, 58, 61, 62))],
    (2, 3, 2): [('fur', (55, 55, 56, 60)), ('fur', (56, 56, 56, 60)), ('fur', (57, 57, 57, 60))],
    # from the front: the walk
    (1, 0, 0): [('fur', (58, 58, 51, 52)), ('fur', (59, 59, 50, 53)), ('fur', (60, 60, 50, 54)), ('fur', (61, 61, 50, 51)),
                ('fur', (57, 57, 61, 62)), ('fur', (58, 58, 61, 62)), ('fur', (59, 59, 61, 63)), ('fur', (60, 60, 60, 63)), ('fur', (61, 61, 61, 62))],
    (1, 2, 0): [('fur', (58, 58, 60, 61)), ('fur', (59, 59, 59, 62)), ('fur', (60, 60, 58, 62)), ('fur', (61, 61, 61, 62)),
                ('fur', (60, 60, 48, 49)), ('fur', (61, 61, 49, 50))],
    # from the front: the run
    (2, 0, 0): [('fur', (59, 59, 51, 52)), ('fur', (60, 61, 50, 52)), ('fur', (62, 62, 50, 51)), ('fur', (63, 63, 51, 51)), ('fur', (60, 61, 60, 63))],
    (2, 1, 0): [('fur', (56, 56, 49, 49)), ('fur', (57, 57, 49, 50)), ('fur', (58, 58, 49, 51)), ('fur', (59, 59, 51, 52)),
                ('fur', (56, 56, 63, 63)), ('fur', (57, 57, 62, 63)), ('fur', (58, 58, 62, 63)), ('fur', (59, 59, 60, 61))],
    (2, 2, 0): [('fur', (59, 59, 60, 61)), ('fur', (60, 61, 60, 62)), ('fur', (62, 62, 61, 62)), ('fur', (63, 63, 61, 61)), ('fur', (60, 61, 49, 52))],
    # from behind: the walk
    (1, 0, 1): [('fur', (57, 57, 50, 52)), ('fur', (58, 58, 52, 52)), ('fur', (57, 58, 62, 63)), ('fur', (59, 59, 63, 63))],
    (1, 2, 1): [('fur', (56, 56, 59, 60)), ('fur', (57, 57, 58, 61)), ('fur', (58, 59, 58, 61)), ('fur', (56, 60, 47, 48))],
    # from behind: the run
    (2, 0, 1): [('fur', (57, 59, 51, 53)), ('blue', (60, 61, 49, 52)), ('fur', (57, 58, 61, 62))],
    (2, 1, 1): [('fur', (55, 55, 48, 48)), ('fur', (56, 57, 60, 62)), ('fur', (58, 58, 59, 62)), ('blue', (59, 59, 49, 50))],
    (2, 2, 1): [('fur', (57, 59, 57, 60)), ('fur', (56, 59, 48, 49))],
    # from behind: the see-through pixel between his sash and his right wristband (standing, walk 1, 2, 4, run 2, 4)
    (0, 0, 1): [('gap', (60, 60, 59, 59))],
    (1, 1, 1): [('gap', (60, 60, 59, 59))],
}
FIXES[0, 1, 1] = FIXES[0, 0, 1]; FIXES[1, 0, 1] = FIXES[1, 0, 1] + [('gap', (60, 60, 59, 59))]; FIXES[2, 1, 1] = FIXES[2, 1, 1] + [('gap', (59, 59, 59, 59))]
FIXES[1, 3, 1] = FIXES[1, 1, 1]
FIXES[1, 3, 2] = FIXES[1, 1, 2]; FIXES[1, 3, 0] = FIXES.get((1, 1, 0), []); FIXES[2, 3, 0] = FIXES[2, 1, 0]; FIXES[2, 3, 1] = FIXES[2, 1, 1]

# Every other move (Nov 12, after 07:14): each picture read pixel by pixel against BF Goku's frame under it (his wristband
# between hand and arm, his undershirt sleeve at the shoulder) and against the sheet's own bands where BF has no frame like
# it. Ops: 'arm' (row, first col, last col): his skin and BF's sleeve blue there become fur, by shade (darkest skin -> darkest
# fur); 'band': his skin where BF has his wristband or belt becomes the band's blue; 'skin': his fur where BF's hand is becomes
# BF's skin; 'streak': a see-through pixel where BF has his white motion streak takes the streak; ('fill', box, colour): a
# see-through pixel becomes that colour.
def _rows(*spans): return [('arm', (r, r, a, b)) for r, a, b in spans]
MOVES = {
    (2, 0, 1): [('band', (60, 60, 52, 53))],                                                      # run 1 from behind: in the sash
    (3, 0, 0): _rows((57, 52, 53), (58, 51, 53), (59, 51, 52), (60, 52, 52)),                     # ki blast wind-up: left forearm
    (3, 0, 2): _rows((56, 66, 66), (57, 66, 67), (58, 65, 67), (59, 66, 67)),                     # its back forearm, from the side
    (3, 1, 1): _rows((57, 53, 53), (58, 53, 53), (61, 53, 53)),
    (4, 0, 1): _rows((60, 58, 58), (62, 58, 58)),
    (4, 0, 2): _rows((53, 68, 69), (54, 68, 69), (55, 68, 69), (56, 65, 68)),                     # combo: raised back forearm
    (4, 1, 0): _rows((59, 50, 51)),
    (4, 1, 1): _rows((57, 52, 52), (58, 52, 52), (61, 52, 52)),
    (4, 1, 2): _rows((54, 61, 61), (55, 61, 61), (56, 61, 61)),
    (4, 3, 2): _rows((56, 55, 56), (57, 56, 56)),
    (5, 0, 0): _rows((57, 52, 53), (58, 51, 53), (59, 51, 52), (60, 52, 52), (55, 62, 62)),
    (5, 0, 1): _rows((60, 53, 53)),
    (5, 0, 2): _rows((56, 64, 67), (57, 65, 68)),                                                 # raised back forearm
    (5, 1, 2): _rows((56, 47, 51), (57, 49, 49), (57, 51, 51), (59, 47, 50)) + [('streak', (57, 57, 50, 59))],  # the punch
    (5, 2, 2): _rows((60, 43, 45)),
    (6, 0, 0): _rows((56, 50, 51), (57, 49, 51), (58, 49, 50), (59, 50, 50), (55, 63, 63), (56, 63, 64), (57, 64, 65), (58, 64, 64)),
    (6, 0, 1): _rows((62, 57, 57)),
    (6, 0, 2): [('arm', (51, 55, 66, 69))],                                                       # raised back forearm
    (6, 1, 1): _rows((62, 49, 49)),
    (6, 2, 1): _rows((53, 61, 61)),
    (6, 2, 2): _rows((57, 55, 57), (58, 55, 58), (59, 58, 58)),                                   # back forearm above its band
    (6, 3, 0): [('skin', (58, 58, 63, 63))],                                                      # a fur pixel in his right hand
    (6, 3, 1): _rows((59, 50, 50), (60, 48, 48), (61, 48, 48)),
    (6, 3, 2): _rows((57, 59, 59)),
    (7, 0, 1): [('arm', (56, 59, 48, 49)), ('arm', (56, 59, 60, 62))],                            # guard from behind: elbows
    (8, 0, 0): _rows((60, 49, 50), (61, 49, 51), (62, 49, 51), (59, 63, 63), (60, 62, 63), (61, 61, 63), (62, 60, 63), (63, 60, 62)),
    (9, 0, 0): _rows((55, 62, 63), (56, 62, 63), (57, 61, 63), (58, 63, 63)),
    (9, 0, 1): _rows((55, 63, 63), (56, 63, 63)),
    (9, 1, 0): _rows((54, 51, 51), (55, 51, 51), (56, 50, 51), (57, 49, 51), (58, 51, 52),
                     (54, 62, 62), (55, 62, 62), (56, 62, 62), (57, 61, 63), (58, 60, 61)),         # hit: both upper arms
    (9, 2, 1): _rows((56, 60, 62), (57, 59, 63), (58, 60, 63)),                                   # hit from behind: right arm
    (10, 0, 0): _rows((56, 49, 49), (57, 49, 50), (58, 49, 51), (59, 49, 51)),                    # powering up: left forearm
    (10, 2, 0): _rows((55, 50, 50), (56, 49, 50), (57, 49, 51), (58, 50, 52)),
    (10, 9, 0): _rows((55, 52, 52), (56, 50, 50), (56, 52, 52), (57, 50, 52), (58, 50, 52)),
    (14, 0, 0): _rows((59, 62, 64), (60, 61, 64), (61, 61, 64), (62, 62, 63)),                    # jump: right arm
    (15, 0, 2): _rows((62, 47, 52), (63, 47, 53)) + [('fill', (61, 61, 47, 47), 31), ('fill', (59, 59, 45, 45), 1)],  # flying
    (16, 0, 0): _rows((61, 51, 52), (62, 51, 53), (62, 55, 55), (63, 52, 52), (64, 52, 52)),      # spin: left forearm
    (16, 0, 2): _rows((61, 58, 58), (62, 58, 60), (63, 59, 59), (64, 59, 59)),
    (16, 2, 2): _rows((60, 59, 59), (61, 58, 60), (62, 56, 60), (63, 59, 59), (64, 59, 59)),
    (18, 0, 2): _rows((60, 62, 68), (61, 61, 68), (62, 61, 63), (62, 67, 67)),                     # getting up: arm along his knee
    (21, 10, 0): _rows((55, 54, 56), (56, 55, 57), (57, 55, 57)),                                 # as his back in (21, 10, 1)
}
MOVES[15, 1, 2] = MOVES[15, 0, 2]; MOVES[16, 1, 0] = MOVES[16, 2, 0] = MOVES[16, 0, 0]; MOVES[16, 1, 2] = MOVES[16, 0, 2]
# The owner, 07:49, on that preview: "Fix the fucking fur on the arms in every single frame". The frames left as the sheet had
# them are done too, every lone skin pixel on a shoulder or arm, and every patch of blue left on his arms from BF's undershirt
# sleeve or its outline (blue touching his fur and no hand, off his sash and boots): only his wristbands stay blue.
MORE = {
    (3, 0, 1): _rows((58, 57, 58), (59, 57, 58), (60, 58, 58)),
    (9, 1, 2): _rows((57, 63, 63), (58, 62, 64), (59, 62, 64), (60, 62, 64)),
    (18, 0, 0): _rows((57, 52, 52), (58, 52, 52), (59, 52, 52)),
    (4, 0, 0): _rows((55, 49, 49)), (4, 3, 1): _rows((56, 46, 46)), (8, 0, 0): _rows((59, 49, 49)),
    (9, 0, 0): _rows((54, 62, 62)), (18, 1, 0): _rows((58, 61, 61)),
}
SLEEVES = {
    (3, 0, 0): [(56, 52), (57, 51)], (3, 0, 2): [(56, 65), (57, 65)], (3, 1, 0): [(61, 62)], (3, 1, 1): [(56, 53)],
    (3, 2, 0): [(60, 51)], (3, 2, 1): [(56, 58), (57, 60)],
    (4, 0, 1): [(57, 56), (57, 57), (57, 58), (58, 55), (58, 56), (58, 59), (59, 55)], (4, 0, 2): [(57, 65)],
    (4, 1, 0): [(61, 49)], (4, 1, 1): [(56, 53), (57, 53)], (5, 0, 1): [(58, 52)], (5, 1, 0): [(61, 62)],
    (5, 2, 1): [(59, 52), (59, 53)], (6, 0, 0): [(55, 50), (56, 49)],
    (6, 0, 1): [(57, 55), (57, 56), (57, 57), (58, 54), (58, 55), (58, 58)], (6, 3, 1): [(57, 49)], (9, 1, 1): [(59, 51)],
    (10, 6, 0): [(56, 60)], (10, 7, 0): [(58, 49)], (12, 0, 0): [(54, 49), (54, 63)], (12, 0, 1): [(54, 48)],
    (13, 0, 0): [(59, 62), (59, 63)], (14, 0, 0): [(58, 63)], (14, 3, 1): [(55, 48)], (16, 0, 1): [(57, 60), (58, 60)],
    (16, 2, 1): [(58, 60)], (16, 2, 2): [(59, 59), (60, 60), (60, 61), (61, 61)], (9, 1, 2): [(57, 60)],
}
for _k, _v in SLEEVES.items(): MORE[_k] = MORE.get(_k, []) + [('arm', (y, y, x, x)) for y, x in _v]
for _k, _v in MORE.items(): MOVES[_k] = MOVES.get(_k, []) + _v
for _k, _v in MOVES.items(): FIXES[_k] = FIXES.get(_k, []) + _v


def apply(c, b, stand, entries):
    """c: his frame; b: BF Goku's frame of the same slot, frame and view; stand: his standing frame in that view"""
    out = c.copy()
    for e in entries:
        op, (r0, r1, c0, c1) = e[0], e[1]
        for y in range(r0, r1 + 1):
            for x in range(c0, c1 + 1):
                v = int(out[y, x]); bv = int(b[y, x])
                if op == 'fur' and (v in SKIN_FUR or v in BLUE_FUR):
                    out[y, x] = stand[y, x] if int(stand[y, x]) in FURS else SKIN_FUR.get(v, BLUE_FUR.get(v))
                elif op == 'arm' and (v in SKIN_FUR or v in BLUE_FUR): out[y, x] = SKIN_FUR.get(v, BLUE_FUR.get(v))
                elif op == 'blue' and bv in BF_BAND and v in FURS: out[y, x] = BF_BAND[bv]
                elif op == 'band' and v in SKIN_FUR and bv in BF_BAND: out[y, x] = BF_BAND[bv]
                elif op == 'skin' and v in FURS and bv in SKIN_FUR: out[y, x] = bv
                elif op == 'streak' and v == 0 and bv == 2: out[y, x] = 2
                elif op == 'gap' and v == 0: out[y, x] = 31
                elif op == 'fill' and v == 0: out[y, x] = e[2]
    return out
