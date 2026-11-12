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


def apply(c, b, stand, entries):
    """c: his frame; b: BF Goku's frame of the same slot, frame and view; stand: his standing frame in that view"""
    out = c.copy()
    for op, (r0, r1, c0, c1) in entries:
        for y in range(r0, r1 + 1):
            for x in range(c0, c1 + 1):
                v = int(out[y, x])
                if op == 'fur' and (v in SKIN_FUR or v in BLUE_FUR):
                    out[y, x] = stand[y, x] if int(stand[y, x]) in FURS else SKIN_FUR.get(v, BLUE_FUR.get(v))
                elif op == 'blue' and int(b[y, x]) in BF_BAND and v in FURS: out[y, x] = BF_BAND[int(b[y, x])]
                elif op == 'gap' and v == 0: out[y, x] = 31
    return out
