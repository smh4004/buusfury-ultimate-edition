"""32 MB ROM support (from Black Star Odyssey's tools/rom32.py; the decomp's modern build has BF's bytes at every site).

The GBA maps up to 32 MB of cartridge ROM (0x08000000-0x09FFFFFF), and Buu's Fury is 16 MB. Its save chip is a serial
EEPROM (library EEPROM_V124, ROM 0x7B7964). On a cartridge of 16 MB or less the EEPROM answers anywhere in
0x0D000000-0x0DFFFFFF, and BF's library uses 0x0D000000. On a 32 MB cartridge that range is the top half of the ROM
(mirrored), and the EEPROM answers only in 0x0DFFFF00-0x0DFFFFFF (GBATEK). So a 32 MB build must move BF's EEPROM address.

BF builds the address in four places with `movs rX, #0xD0; lsls rX, rX, #20` (r4 at 0x408BA / 0x409B2, the read and write
routines; r0 at 0x40A42 / 0x40A6A, the write routine's ready poll). Each pair (4 bytes) becomes a `bl` to a stub that
loads 0x0DFFFF00 into the register. The stubs go in 0x40AE4-0x40B22, a library routine with no callers and no pointer to
it (likely BF's unused verify-and-retry write, which is also the only caller of 0x40918). Both routines push lr on entry
and restore it from the stack, and no flag set by the old `lsls` is read before the next flag-setting instruction, so
the bl's lr and flags changes are harmless. DMA from 0x0DFFFF00 moves at most 81 halfwords, so it stays inside the window.
"""
import struct

SIZE = 0x2000000
HIGH = (0x1000000, 0x2000000)          # the upper 16 MB: actors marked high (build.py)
EEPROM = 0x0DFFFF00
SITES = {0x408BA: 4, 0x409B2: 4, 0x40A42: 0, 0x40A6A: 0}
DEAD = (0x40AE4, 0x40B22)              # unreferenced library routine (likely unused verify-and-retry)
STUB = {4: 0x40AE4, 0: 0x40AE8}        # ldr rX, [pc, #k]; bx lr  (shared literal at 0x40AEC)
LIT = 0x40AEC


def _bl(src, dst):
    off = (dst - (src + 4)) >> 1
    return struct.pack('<HH', 0xF000 | ((off >> 11) & 0x7FF), 0xF800 | (off & 0x7FF))


def apply(rom, clean):
    """Patch the EEPROM address for a 32 MB cartridge (checks BF's original bytes first)."""
    for a, reg in SITES.items():
        assert rom[a:a + 4] == clean[a:a + 4] == struct.pack('<HH', 0x2000 | reg << 8 | 0xD0, 0x0500 | reg << 3 | reg), hex(a)
    assert rom[DEAD[0]:DEAD[1]] == clean[DEAD[0]:DEAD[1]]
    for reg, at in STUB.items():                    # ldr rX, [pc, #k]: pc = (at + 4) & ~3
        k = (LIT - ((at + 4) & ~3)) // 4
        rom[at:at + 4] = struct.pack('<HH', 0x4800 | reg << 8 | k, 0x4770)
    rom[LIT:LIT + 4] = struct.pack('<I', EEPROM)
    for a, reg in SITES.items():
        rom[a:a + 4] = _bl(a, STUB[reg])
