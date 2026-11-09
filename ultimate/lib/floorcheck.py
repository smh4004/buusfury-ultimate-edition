"""Is a spot walkable floor? Read from a built ROM, so zone 26 rooms and copied rooms count too.

Area table: pointer at zone26.TABLE_LIT, count from the code at zone26.COUNT_INSN (movs r0, #a; lsls r0, #1; adds r0, #b).
Area record (56 bytes): +0 world, +1 area, +0x2C scene, whose first word is the map record + 4. Map record +0x38: the
walkable floor mask (WFZ; 1 bit per 8x8 cell, 256 cells per row; tools/assets/maps.py).

The tests teleport characters by writing their position into memory, which skips the game's collision. If a route has gone
wrong (a resident walked off, a talk missed), the next teleport can put Goku inside a building of the wrong place: Nov 9, the
owner saw such a screenshot ("don't allow this clipping"). `guard` stops the test instead."""
import struct, sys
import numpy as np
from zone26 import TABLE_LIT, COUNT_INSN, AREAS, COUNT, decompress_stream
BASE = 0x08000000


class Floor:
    def __init__(self, rom):
        self.rom = open(rom, 'rb').read() if isinstance(rom, str) else bytes(rom)
        self.masks = {}

    def u32(self, o): return struct.unpack_from('<I', self.rom, o)[0]

    def table(self):
        i = struct.unpack_from('<4H', self.rom, COUNT_INSN)
        if i[1] == 0x0040 and i[0] >> 8 == 0x20 and i[2] >> 8 == 0x30:
            return self.u32(TABLE_LIT) - BASE, 2 * (i[0] & 0xFF) + (i[2] & 0xFF)
        return AREAS, COUNT

    def mask(self, world, area):
        if (world, area) not in self.masks:
            t, n = self.table()
            e = next((t + 56 * q for q in range(n) if (self.rom[t + 56 * q], self.rom[t + 56 * q + 1]) == (world, area)), None)
            if e is None: raise KeyError('no area %d-%02X' % (world, area))
            m = self.u32(self.u32(e + 0x2C) - BASE) - 4 - BASE
            o = self.u32(m + 0x38) - BASE; kind, size = struct.unpack_from('<II', self.rom, o)
            d = self.rom[o + 8:o + 8 + size] if kind == 0 else bytes(decompress_stream(self.rom, o + 8, size)[0])
            self.masks[world, area] = np.unpackbits(np.frombuffer(d, np.uint8), bitorder='little').reshape(-1, 256)
        return self.masks[world, area]

    def walkable(self, world, area, x, y):
        m = self.mask(world, area)
        return 0 <= x < 2048 and 0 <= y < 8 * m.shape[0] and bool(m[y // 8, x // 8])

    def guard(self, at, x, y, what='a character'):
        """at = *(u16 *)0x0300197C (area << 8 | world). Exits the test, as a FAIL, if (x, y) is solid there."""
        world, area = at & 0xFF, at >> 8
        if not self.walkable(world, area, x, y):
            print('FAIL teleporting %s to (%d, %d) would put it inside a wall of area %d-%02X: the route is not where it '
                  'should be' % (what, x, y, world, area), flush=True)
            sys.exit('stopped before a teleport into a wall')
