"""Buu's Fury's own boss bar, as the game builds it: the model the tests compare the screen with. Nothing here goes into the ROM.
The bar is the game's (its actor's vtable 0x0804CE28, made by 0x080195A8, drawn by 0x08019658): two 32x8 sprites of 8-bit tiles at
x 160 and 192, priority 1, on 0x200 bytes of tiles (the second sprite's 8 tile numbers on), the art at 0x087196E4. It has 53 slanted
columns of four pixels each (their offsets into the 0x200 bytes: 0x087198E4, 53 x 4 words); the columns from the health's on are
painted black (colour 1), so it empties from the right. It slides in from above the screen to y 8 and out again.
The story's boss fights get it from their scripts (natives 0x8F and 0x90); the mod's fights from outfit.c bossbar_tick, which keeps
the columns by the game's own rule: health x 53 / the fight's whole health, rounded down (0x0804F874)."""
import struct
ART, COLUMNS, VTABLE, MAKE = 0x7196E4, 0x7198E4, 0x0804CE28, 0x080195A8
COLS, BYTES = 53, 0x200
X, Y = 160, 8                               # where it rests
SPRITES = ((0x6000, 0x40A0, 0), (0x6000, 0x40C0, 8))      # (attribute 0 without its y, attribute 1, tile number from the bar's first)


def picture(rom, cols):
    """The 0x200 bytes the bar's tiles hold with `cols` columns of health."""
    out = bytearray(rom[ART:ART + BYTES])
    for c in range(max(cols, 0), COLS):
        for o in struct.unpack_from('<4I', rom, COLUMNS + 16 * c): out[o] = 1
    return bytes(out)


def columns(hp, whole):
    """The columns the game shows for this much health of that much: rounded down, as its own bars are."""
    return 0 if hp <= 0 or whole <= 0 else min(hp * COLS // whole, COLS)


def image(rom, cols):
    """The picture as colour indices, 8 rows of 64 (for a look: tools that draw it take the palette at 0x701B0 + 768)."""
    raw = picture(rom, cols)
    return [[raw[(x // 8) * 64 + y * 8 + x % 8] for x in range(64)] for y in range(8)]
