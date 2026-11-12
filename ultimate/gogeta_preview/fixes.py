"""Super Saiyan 4 Gogeta's head, neck, shoulders and arms, frame by frame. The owner, Nov 11 21:38: "Some weird clipping with Ssj4 Gogeta
head and neck on side and back views especially on walk frames mainly".

What was read, each frame against BF Goku's frame under it (the sheet's standing, walking and running frames were made by another road
than its fighting frames, and it shows):
- from the side his head has two see-through pixels over his eye, in every frame (HOLE);
- his orange shoulder pads come and go: BF's sleeve was painted vest grey, black, or the sash's blue, so a pad is whole in one frame, half
  in the next, gone in the third, and blue sits on his shoulder;
- arms left bare (BF's arm skin unturned, often one column of it down the outside of a fur arm), and fists turned to fur instead, some
  with a blue ankle band across them.
The fixes hold to his own standing frames and the rules the owner gave for these figures: pads on BF's sleeves in the pad's two oranges,
fur on the whole arm, the dark wristband, skin on the fist only, nothing outside BF's outline.

Each entry is a list for one frame (slot, frame, view): (row, column, letters) in patch.ABC ('_' leaves a pixel, 's' is BF's own skin),
or ('arm' | 'bare' | 'fist' | 'band', (row0, row1, col0, col1)) as patch.apply reads them. Slots 0-2 only so far (idle, walk, run)."""
BACK = {
    # walk, from behind
    (1, 0, 1): [(56, 46, '..#OOO'), (57, 46, '.#OPPOO'), (58, 48, 'pP'), (58, 52, 'O'), (59, 48, 'pP')],
    (1, 1, 1): [(55, 48, 'OO'), (56, 48, 'OOOO'), (57, 47, 'pPPO'), (58, 47, 'pP'), (59, 47, 'p')],
    (1, 2, 1): [(56, 59, 'OO#'), (57, 58, 'OPpO#.'), (58, 59, 'Ppp'), (59, 59, 'ppp'), (59, 48, 'pp#'), (60, 48, 'xxx')],
    # run, from behind
    (2, 0, 1): [(56, 47, '..#OOO'), (57, 47, '.#OPPOO'), (58, 49, 'pPP'), (58, 53, 'O'), (59, 49, 'pP'),
                (56, 59, 'oO'), (56, 61, 'p'), (57, 61, 'p'), (58, 61, 'p')],
    (2, 1, 1): [(55, 48, 'OO'), (56, 48, 'OO'), (57, 48, 'p'), (58, 48, 'p'), (55, 61, 'OO'), (56, 61, 'OO'), (57, 61, 'Pp'), (58, 62, 'p')],
    (2, 2, 1): [(56, 60, '##'), (57, 58, 'Pp'), (58, 58, 'Ppp'), (59, 58, 'Ppp')],
}
BACK[1, 3, 1] = BACK[1, 1, 1]; BACK[2, 3, 1] = BACK[2, 1, 1]
# (the see-through spot over his eye is filled in every side frame by fixed.hole, wherever his head is: no entry here)
SIDE = {
    (0, 0, 2): [('fist', (62, 65, 55, 59)), (62, 58, 'g')],
    # walk, from the side
    (1, 0, 2): [(57, 59, 'oo'), (58, 58, 'Op'), ('arm', (58, 61, 59, 62)), (61, 62, 'G'), ('fist', (63, 65, 60, 63))],
    (1, 1, 2): [(56, 59, 'P'), (57, 55, 'OoooPp'), ('arm', (58, 60, 56, 59)), ('fist', (62, 65, 54, 58))],
    (1, 2, 2): [(57, 54, 'OOO'), (58, 55, 'ooP'), (59, 56, 'pp'), ('arm', (59, 63, 53, 56)), ('arm', (56, 59, 60, 61))],
    (1, 3, 2): [(56, 59, 'P'), (57, 55, 'OoooPp'), ('arm', (58, 60, 56, 59)), ('fist', (62, 65, 55, 59))],
    # run, from the side
    (2, 0, 2): [('fist', (58, 60, 49, 53)), ('band', (57, 58, 48, 49)), ('arm', (57, 57, 61, 62)), ('fist', (57, 58, 65, 67))],
    (2, 1, 2): [(55, 58, 'O'), (56, 58, 'O'), ('arm', (55, 56, 59, 62)), ('band', (56, 57, 59, 63)), ('fist', (57, 60, 61, 64)), ('fist', (56, 59, 51, 54))],
    (2, 2, 2): [(58, 55, 'OOO'), (59, 56, 'ooP'), ('arm', (59, 59, 54, 55)), ('fist', (58, 60, 49, 52)), ('arm', (57, 58, 61, 63))],
    (2, 3, 2): [(55, 56, 'OOOO'), (56, 56, 'O'), ('arm', (56, 56, 57, 59)), ('fist', (59, 62, 56, 59))],
}
SIDE[0, 1, 2] = SIDE[0, 0, 2]
FRONT = {
    (0, 0, 0): [(59, 48, 'p'), (59, 64, 'p')],
    # walk, from the front
    (1, 0, 0): [(58, 51, 'OO'), (59, 50, 'OPpO'), (60, 54, 'O'), (57, 61, 'O'), (58, 61, 'O'), ('bare', (60, 61, 50, 53)), ('bare', (59, 61, 61, 63)),
                ('band', (63, 63, 51, 52)), ('fist', (63, 65, 52, 55))],
    (1, 1, 0): [('bare', (58, 59, 48, 52)), ('bare', (58, 59, 60, 64))],
    (1, 2, 0): [(58, 60, 'OO'), (59, 59, 'OPpO'), (60, 58, 'O'), ('bare', (60, 61, 59, 62)), ('band', (63, 63, 60, 61)), ('fist', (63, 65, 57, 60))],
    # run, from the front
    (2, 0, 0): [(59, 51, 'OO'), ('bare', (60, 63, 50, 52)), ('bare', (60, 61, 61, 63)), ('fist', (61, 64, 54, 57)), ('band', (60, 63, 52, 54))],
    (2, 1, 0): [(55, 50, 'O'), (56, 50, 'OO'), (57, 51, 'O'), (55, 62, 'O'), (56, 62, 'O'), (57, 62, 'O'), ('bare', (57, 59, 49, 52)), ('bare', (58, 59, 60, 63))],
    (2, 2, 0): [(59, 60, 'OO'), ('bare', (60, 63, 60, 62)), ('bare', (60, 61, 49, 51)), ('fist', (61, 64, 55, 58)), ('band', (60, 63, 58, 60))],
}
FRONT[0, 1, 0] = FRONT[0, 0, 0]; FRONT[1, 3, 0] = FRONT[1, 1, 0]; FRONT[2, 3, 0] = FRONT[2, 1, 0]
ALL = {}
for t in (BACK, SIDE, FRONT): ALL.update(t)
