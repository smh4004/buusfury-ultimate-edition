"""The guest bench as outfit.c keeps it, for the tests: where it is in memory and in a save file.

Version 3 (Nov 12, with the 64 KB flash save): struct bench { u32 magic, gen, sum; u8 flags[4], used[8], flags2[4], mastery[22],
spare[14]; struct entry e[48]; }, 1,120 bytes at 0x0203F400. Each game slot's bench is saved in a 4 KB sector of the flash of its own
(sectors 2-4, offset 0x2000 + slot * 0x1000), as it is in memory (no byte swapping).
Versions 2 and 1 were saved in the first 8 KB at 0x1A20 + slot * 496, in the EEPROM file's order (each 8-byte block back to front); the
new build converts them the first time a game reads its bench."""
RAM = 0x0203F400
MAGIC = 0x33484342                       # 'CBH3'
SIZE = 1120
GROUPS = 48
GEN = RAM + 4
SUM = RAM + 8
FLAGS = RAM + 12                         # more flags 0-31
USED = RAM + 16                          # a bit per group
FLAGS2 = RAM + 24                        # more flags 32-63
MASTERY = RAM + 28                       # 22 bytes: one per (character, tier), then Goku's Kamehameha count
ENTRIES = RAM + 64                       # 48 entries of 22 bytes
SPARE = RAM + 50                         # 14 bytes: the guests' mastery (outfit.c guest_tiers, build.py GUEST_MASTERY), then at 13 Gogeta's form + 1
GUEST_MASTERY = SPARE                    # Future Trunks's Super Saiyan, Teen Gohan's Super Saiyan and 2, Goku Black's Rose (Nov 12)
KNOWN2 = SPARE + 4                       # 8 bytes, one per character: their skill books' places 16-23 (Goku's Fusion Dance is his 17th)
STASH_FORM = SPARE + 13                  # while a dance has Gogeta's record, his own form + 1 (his progress in the last entry: outfit.c fused_stash)
STASH_GROUP = GROUPS - 1
ENTRY = 22


def sector(slot):
    """Where a game slot's bench is in the save file."""
    return (2 + slot) << 12


# A bench in memory that goes with the game in play (generation 0x1234), so what a test pokes into it is read as this game's.
ON = ['poke %08X %08X' % (RAM, MAGIC), 'poke %08X 00001234' % GEN, 'poke8 03001559 34', 'poke8 0300155A 12']

# Version 2, as the builds of Nov 9-12 kept it (at 0x0203F000 in memory, at 0x1A20 + slot * 496 in the save's first 8 KB).
V2_MAGIC = 0x32484342
V2_OFFSET = 0x1A20
V2_SIZE = 496
V1_MAGIC = 0x31484342
