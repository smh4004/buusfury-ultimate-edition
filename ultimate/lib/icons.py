"""Skill icons: the HUD's 32x16 8bpp images (eight 8x8 tiles, two rows of four), each move with an enabled and a greyed copy.

Super Saiyan 3's icon is Super Saiyan's lightning Z moved one pixel left with a small cyan 3 beside it (colour 0x4B, greyed 0xBA).
New transformation icons are made the same way: the 3 cleared and another digit drawn in its place, in that style.
"""
import numpy as np

W, H = 32, 16
BG = 0x01                                   # the icon window's black
# 5x5 digits in the 3's style (rows top to bottom; '#' = a lit pixel). The 3 is the game's own.
DIGITS = {
    '2': ('.###.', '#...#', '..##.', '.#...', '#####'),
    '3': ('.###.', '#...#', '..##.', '#...#', '.###.'),
    '4': ('#..#.', '#..#.', '#####', '...#.', '...#.'),
}
DIGIT_AT = (14, 5)                          # (x, y) of the 3's box in Super Saiyan 3's icon


def decode(data):
    """512 bytes -> 16x32 index array."""
    a = np.zeros((H, W), np.uint8)
    for t in range(8):
        tx, ty = t % 4, t // 4
        a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = np.frombuffer(bytes(data[t * 64:t * 64 + 64]), np.uint8).reshape(8, 8)
    return a


def encode(a):
    out = bytearray()
    for t in range(8):
        tx, ty = t % 4, t // 4
        out += a[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].astype(np.uint8).tobytes()
    return bytes(out)


def with_digit(ss3_icon, digit, colour, digit_colour_in_ss3):
    """Super Saiyan 3's icon (bytes) with its 3 cleared and `digit` drawn in `colour` (an OBJ palette index)."""
    a = decode(ss3_icon)
    box = a[DIGIT_AT[1]:DIGIT_AT[1] + 5, DIGIT_AT[0]:DIGIT_AT[0] + 5]
    box[box == digit_colour_in_ss3] = BG
    glyph = DIGITS[digit]
    for y, row in enumerate(glyph):
        for x, c in enumerate(row):
            if c == '#': a[DIGIT_AT[1] + y, DIGIT_AT[0] + x] = colour
    return encode(a)


WINDOW = (slice(2, 11), slice(2, 20))      # the picture's window; the rest is the HUD frame and gauge, which keep their colours


def recolour(icon, remap):
    """An icon with its picture (not the frame) through a 256-entry index map (as bytes.translate)."""
    a = decode(icon); w = a[WINDOW]
    a[WINDOW] = np.frombuffer(bytes(remap), np.uint8)[w]
    return encode(a)
