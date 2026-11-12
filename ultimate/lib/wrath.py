"""Wrath of the Gods: Beerus's own beam. The owner, Nov 11 18:55: "Change Beerus beam attack to actually fire from the hand and also
give him his own custom light yellow Frieza style finger beam attack not kamehameha called Wrath of the Gods".

What he had: Beerus fights on Kid Buu's behaviour (bog.py), whose beam is the game's enemy beam (behaviour table 0x0804C690: start
0x08033002, each frame 0x080330AA): a Kamehameha, made as a charging ball at the fighter's place plus a step per facing and, on the
behaviour's 9th frame, laid as a beam at another step per facing (both tables at 0x0875925C, set for Kid Buu and shared by every enemy
with this beam). On Beerus the ball sat at his back knee and the beam left from his shins, 11 pixels under his outstretched hand; from
the front and from behind it left 13 pixels to one side of him. While it was out the behaviour showed his ki blast's two arm-out
frames by turns, which from the front are two different arms.

What he has now (outfit.c wrath_start, wrath_update; build.py add_eraser fills their tables from here):
- the pose: his ki blast's wind-up for four frames, then its arm out, held (the owner's rule for a figure with no beam frames, Nov 10:
  "use ki blast frames but dont loop them just make it one smooth sustained transition");
- a glint on his fingertip for the four frames before it fires, in place of the ball (Frieza's Death Beam starts so);
- the beam from that fingertip, in every facing: thin and light yellow.
Nothing is drawn new: the beam is the Kamehameha's own frames (level 1's), every piece squeezed to half its width about the beam's
middle line (near end, body and travelling tip; the burst where it lands and its sparks keep their size), and the glint is the
Kamehameha's smallest charging ball; the blues become the game's light yellows (TINT: colours the palette already has).
The beam's strength, reach, length of time and what it hits are the enemy beam's, untouched: only where it is, how it looks and the
pose are his. Every other enemy with this beam keeps the game's (the two functions do nothing unless the fighter's figure is Beerus).

Frame rows are {box x, y (signed bytes), w, h, attr0, attr1, tiles}: 16 a facing (down, up, left, right) for the beam, its box added to
the beam's place; 3 for the ball, its box taken from the ball's place (so it is centred)."""
import struct
import numpy as np

ROM_BASE = 0x08000000
ENEMY_BEAM_VT, ENEMY_BEAM_VT_REF, VT_ENTRIES = 0x4C690, 0x331D0, 9      # the enemy beam's table of functions, and the one word that names it
ENEMY_START, ENEMY_UPDATE = 0x08033002, 0x080330AA                      # its entries 0 and 1
ENEMY_STEPS = 0x75925C                    # {x, y, layer} for the ball, per facing; then {x, y} for the beam
BEAM_PARAMS, BALL_ROWS = 0x71DA68, (0x721188, 12)                      # the Kamehameha's three levels {damage, strength, ball rows, beam rows}; its ball rows
TINT = {76: 30, 195: 29, 75: 28, 74: 28}  # the Kamehameha's blues -> light yellows (white, 2, stays): (248,248,216), (248,248,144), (248,248,72)
SQUEEZED = (0, 1, 3, 4, 5, 7, 8)          # rows of a facing made thin: the near end (0-1), the body (3-5), the travelling tip (7-8)
ROWS = 16
# His fingertip in the arm-out frame (slot 3, frame 1), from his place (x right, y down), per facing: down, up, left, right. Read off his
# frames (Kid Buu's shapes, lib/beerus.py, 34 rows tall); a figure facing right is the left one mirrored (x -> 15 - x). test_wrath.py
# holds the game to it: the beam's near end must touch his hand on the screen.
FINGER = ((2.5, 6), (1.5, -8), (-8, -10), (23, -10))


def _image(data, at, w, h):
    return np.frombuffer(bytes(data[at:at + w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w).copy()


def _store(data, at, img):
    h, w = img.shape
    data[at:at + w * h] = img.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).tobytes()


def squeeze(img, axis):
    """Half as wide across `axis` (0: a beam lying, 1: a beam standing), about its middle line: the two middle lines stay, the next
    line out takes the one two out, and so on (so the bright core and the rim both survive)."""
    n = img.shape[axis]; out = np.zeros_like(img); half = n // 2
    for k in range(half):                                  # k: lines from the middle
        src = 2 * k
        if src >= half: break
        for side in (-1, 1):
            to = half + k if side > 0 else half - 1 - k; frm = half + src if side > 0 else half - 1 - src
            if axis == 0: out[to] = img[frm]
            else: out[:, to] = img[:, frm]
    return out


def _span(rows, count):
    tiles = [(struct.unpack_from('<I', rows, 12 * k + 8)[0], rows[12 * k + 2] * rows[12 * k + 3]) for k in range(count)]
    tiles = [(t, n) for t, n in tiles if n and 0x08700000 <= t < 0x08800000]
    return min(t for t, _ in tiles), max(t + n for t, n in tiles)


def beam_rows(clean):
    """-> (the 64 beam rows with their tile pointers still the game's, the tiles they cover as one block, that block's address in the
    game): the Kamehameha's level 1 beam, thin and light yellow."""
    head = struct.unpack_from('<I', clean, BEAM_PARAMS + 12)[0] - ROM_BASE
    rows = bytearray(clean[head:head + 12 * 4 * ROWS]); a, b = _span(rows, 4 * ROWS)
    block = bytearray(clean[a - ROM_BASE:b - ROM_BASE]); done = {}
    order = sorted(range(4 * ROWS), key=lambda k: -(rows[12 * k + 2] * rows[12 * k + 3]))        # a block shared at several sizes: the largest first
    for k in order:
        w, h = rows[12 * k + 2], rows[12 * k + 3]; t = struct.unpack_from('<I', rows, 12 * k + 8)[0]
        if not w * h or k % ROWS not in SQUEEZED: continue
        axis = 1 if k // ROWS < 2 else 0
        if t in done:
            if done[t] != axis: raise SystemExit('wrath: beam tiles %08X are used lying and standing' % t)
            continue
        done[t] = axis
        _store(block, t - a, squeeze(_image(block, t - a, w, h), axis))
    table = bytes(TINT.get(v, v) for v in range(256))
    return rows, bytes(block).translate(table) + bytes(256), a      # (the engine copies 256 bytes for a frame whatever its size)


def ball_rows(clean):
    """-> (the ball's 12 rows, their tiles as one block, its address in the game): the first row (shown while he winds up) empty,
    the other two of level 1 the Kamehameha's smallest ball in the middle of their 16x16, light yellow: the glint."""
    at, count = BALL_ROWS
    rows = bytearray(clean[at:at + 12 * count]); a, b = _span(rows, count)
    block = bytearray(clean[a - ROM_BASE:b - ROM_BASE])
    def tile(k): return struct.unpack_from('<I', rows, 12 * k + 8)[0] - a, rows[12 * k + 2], rows[12 * k + 3]
    t0, w0, h0 = tile(0)
    if (w0, h0) != (8, 8) or any(tile(k)[1:] != (16, 16) for k in (1, 2)): raise SystemExit('wrath: the ball rows are not 8x8, 16x16, 16x16')
    small = _image(block, t0, 8, 8)
    for k in (1, 2):
        t, w, h = tile(k); img = np.zeros((16, 16), np.uint8); img[4:12, 4:12] = small; _store(block, t, img)
    block[t0:t0 + 64] = bytes(64)
    table = bytes(TINT.get(v, v) for v in range(256))
    return rows, bytes(block).translate(table) + bytes(256), a


def shown(rows, block, base, k):
    """Row k as it is drawn: (pixels, box x, box y) or None."""
    x, y, w, h, a0, a1, t = struct.unpack_from('<bbBBHHI', rows, 12 * k)
    if not w * h: return None
    img = _image(block, t - base, w, h)
    if a1 & 0x1000: img = img[:, ::-1]
    if a1 & 0x2000: img = img[::-1]
    return img, x, y


def near_end(rows, block, base, facing):
    """Where the beam's near end is from its place, along its line: the pixel nearest the fighter in the near-end rows."""
    ends = []
    for k in (0, 1):
        img, x, y = shown(rows, block, base, facing * ROWS + k); ys, xs = np.nonzero(img)
        ends.append(int((y + ys.min(), y + ys.max(), x + xs.max(), x + xs.min())[facing]))
    return (min, max, max, min)[facing](ends)


def places(clean, rows, block, base):
    """-> (ball steps, beam steps): what to add to the game's own places, per facing (down, up, left, right), so the glint sits on his
    fingertip and the beam's near end overlaps it by a pixel, its middle line through his hand."""
    game_ball = [struct.unpack_from('<ii', clean, ENEMY_STEPS + 12 * f) for f in range(4)]
    game_beam = [struct.unpack_from('<ii', clean, ENEMY_STEPS + 48 + 8 * f) for f in range(4)]
    ball, beam = [], []
    for f, (fx, fy) in enumerate(FINGER):
        end = near_end(rows, block, base, f)
        if f == 0: at = (int(fx + 0.5), int(fy) - 1 - end); tip = (int(fx + 0.5), int(fy) + 1)
        elif f == 1: at = (int(fx + 0.5), int(fy) + 1 - end); tip = (int(fx + 0.5), int(fy) - 1)
        elif f == 2: at = (int(fx) + 1 - end, int(fy) + 1); tip = (int(fx) - 1, int(fy) + 1)
        else: at = (int(fx) - 1 - end, int(fy) + 1); tip = (int(fx) + 2, int(fy) + 1)
        beam.append((at[0] - game_beam[f][0], at[1] - game_beam[f][1])); ball.append((tip[0] - game_ball[f][0], tip[1] - game_ball[f][1]))
    for v in ball + beam:
        if not all(-128 <= c <= 127 for c in v): raise SystemExit('wrath: a step of %s does not fit a byte' % (v,))
    return ball, beam
