"""The enemy beam from the hand, for every figure that fires it (Nov 12, the owner, 21:40: "Make the beam actually come from Cell's hand
too not the floor", "Scan all NPCs too for this especially big sized ones").

The enemy beam is Kid Buu's (behaviour table 0x0804C690, lib/wrath.py tells it): a ball at the fighter's place plus a step per facing,
laid as a beam on the behaviour's 9th frame at another step (0x0875925C), both set once for Kid Buu's figure. Every enemy on stats rows 60
and 61 (Kid Buu's type, 0x08759220) fires it, whatever his figure, and from those steps (read off the game's frames and its beam rows,
place-relative):
  - facing left, the beam's near end is at x 0, its middle line at y 1.5: a figure's waist, inside his arm (Kid Buu's hand: -8, -6);
  - facing right, the near end is at x 31, 8 pixels past a Kid Buu-sized hand (23);
  - facing down, at (15.5, 7): his right foot; facing up, at (15.5, -8): beside his chest, from his right side.
On Perfect Cell (64x64, his hand 30 pixels above his place) it left from his feet from every side. Beerus has his own (wrath.py).

Each figure here gets the ball at his fingertip in the frame he fires from (his own two-handed beam's, POSE, or with none the ki blast's,
slot 3; frame 1, the hands or the arm out, held from the behaviour's second frame: outfit.c wrath_update, the owner's rule of Nov 10 for
beams with no beam frames, "use ki blast frames but dont loop them just make it one smooth sustained transition"), and the beam drawn from
there; it hits where the game's did (steps below). The side points are that frame's outermost pixel (the hand) and the mean row of its
four outermost columns; down and up were read off the frames (a hand near his middle, its far edge: Perfect Cell's from the front is the
fist at his belly, the raised palm being 16 pixels out to his side). test_hands.py holds the built ROM to the side points and the game
to all four."""

# Fingertips (x right, y down from the fighter's place) per facing: down, up, left, right. Facing right is its own frame (the game's view 3,
# the side view flipped about its box), so its point is read off that frame too.
HANDS = {
    # no beam frames of their own: the ki blast's arm out (slot 3, frame 1)
    'kid_buu':      ((1.5, 6), (0, -7), (-8, -6), (23, -6)),
    'cell_perfect': ((10.5, -15), (10.5, -57), (-13, -29), (36, -29)),
    'broly':        ((22, 4), (-6.5, -16), (-16, -18.5), (47, -18.5)),
    'piccolo':      ((2, 4), (1, -7), (-8, -11.5), (23, -11.5)),
    'android18':    ((3, 3), (13, -25), (-6, -4.5), (21, -4.5)),
    # their own two-handed beam (POSE, frame 1: both hands pushed out): from the front the cupped hands' lower edge, from behind (hands
    # hidden) the top of the arms' reach, from the side the hands' outermost pixel
    'goku':         ((11, -1), (13, -8), (-4, -8.5), (19, -8.5)),
    'goku_black':   ((11, -1), (13, -8), (-4, -8.5), (19, -8.5)),
    'goku_rose':    ((9.5, -1), (9, -6), (-5, -7), (20, -7)),
    'gohan':        ((9.5, -1), (9, -8), (-4, -7), (19, -7)),
    'uub':          ((8, 1), (6.5, -1), (-1, -5.5), (16, -5.5)),
    'majuub':       ((8.5, 1), (6.5, -2), (-1, -5.5), (16, -5.5)),
    'pan':          ((7, -4), (6.5, -4), (-1, -3), (16, -3)),
    'vegeta':       ((8, -3), (7.5, -6), (-8, -8), (23, -8)),
}
# The figures with a two-handed beam of their own fire in it (the owner, 22:09: "Obviously don't use that beam attack for every single
# character who already have two handed beam attacks but use it when a character doesn't like Broly or Cell etc."): the Kamehameha's slot
# 18 (frame 0 the hands drawn back, 1 and 2 pushed out), Vegeta's beam pose 31 (build.py beam_poses: the wind-up, then Final Flash's push).
POSE = {'goku': 18, 'goku_black': 18, 'goku_rose': 18, 'gohan': 18, 'uub': 18, 'majuub': 18, 'pan': 18, 'vegeta': 31}
# The game's own figures, by actor id (the others are the mod's: build.py NEW_ACTORS)
RETAIL = {'kid_buu': 38, 'broly': 29, 'goku': 106, 'vegeta': 270, 'gohan': 101}
MAX = 24                                    # outfit.c HAND_MAX


def game_rows(clean):
    """The enemy beam's own rows (the Kamehameha's level 1), as wrath.places reads them: (rows, block, base)."""
    import struct, wrath
    head = struct.unpack_from('<I', clean, wrath.BEAM_PARAMS + 12)[0] - wrath.ROM_BASE
    rows = clean[head:head + 12 * 4 * wrath.ROWS]; a, b = wrath._span(rows, 4 * wrath.ROWS)
    return rows, clean[a - wrath.ROM_BASE:b - wrath.ROM_BASE] + bytes(256), a


def steps(clean):
    """-> {name: (ball, beam, lift)} per facing (down, up, left, right), what outfit.c adds to the game's places: the ball moves to the
    fingertip; the beam's place (where it hits) moves only along its line (its near end to the fingertip), and across its line it is drawn
    moved (lift: on the screen only). So it still hits what the game's beam hits: the enemy lines up his place with the player's before
    firing, and a big figure's hand is far above his place (Perfect Cell's 29 pixels: moved there, his beam passed over a player level
    with him). From the side the lift is the hand's height over the ground the beam travels along; from the front and back each figure's
    hand is one near his middle, so the beam drawn touches the player it hits."""
    import wrath
    rows = game_rows(clean); out = {}
    for name, f in HANDS.items():
        ball, beam = wrath.places(clean, *rows, finger=f)
        move = [(x, 0) if k >= 2 else (0, y) for k, (x, y) in enumerate(beam)]
        lift = [(0, y) if k >= 2 else (x, 0) for k, (x, y) in enumerate(beam)]
        out[name] = (ball, move, lift)
    return out
