"""A level 150 Goku and real fight measurements, for the emulator tests of the post-game quests (test_garlic.py, test_bog.py).

The owner, Nov 9: "Test these with a level 150 Goku or something so he doesnt die so much and has some balancing". Before, the tests
poked Goku's health to its 16-bit top (0x7FFF), which the quests' own level-ups pushed past 32767 into negative numbers (every refill then
left him down), and fought every foe by poking its health to 2: nothing measured how a fight goes.

Rig(send, mem, rom):
  level150()  Goku as a level 150 fighter made the game's way from the save's Goku: EXP at level 150's mark (the cap: no level-ups, so no
              level-up boxes holding scripts), health and ki grown level by level by the game's own formula (sub_08013678; every roll
              the average, 128 of 256), the 3 points a level spent evenly on Strength, Power and Endurance (the stats the player object
              copies, +0x1B0/+0x1B4, too).
  heal()      health and ki back to his maximum.
  spar(name)  a real exchange, nothing poked on either fighter: Goku beside the foe punching for up to `secs` seconds. Records in BAL
              his hits on the foe and the foe's on him as shares of their health, the seconds he'd need at that rate, and prints them.
"""
import struct

REC0, PLAYER, ENEMIES, COUNT = 0x03001560, 0x03001C34, 0x03001BB4, 0x03001BB0
EXP_TABLE, GROWTH, CLASS = 0x6B7084, 0x6B72E0, 0x6B82F8      # EXP per level (151 x u32), growth per class (8 x i32), class per character


def grown(hp, ki, g, levels, roll=128):
    """sub_08013678's growth, `levels` times: health +((r * g0 >> 8) + g1 >> 16) then x(1 + ((r * g2 >> 8) + g3) / 65536); ki the same
    with g4-g7 (its first term has no >> 8)."""
    for _ in range(levels):
        a = (((roll * g[0]) >> 8) + g[1] >> 16) + hp
        hp = (a * (((roll * g[2]) >> 8) + g[3]) >> 16) + a
        b = ((roll * g[4] + g[5]) >> 16) + ki
        ki = (b * (((roll * g[6]) >> 8) + g[7]) >> 16) + b
    return hp, ki


class Rig:
    def __init__(self, send, mem, rom):
        self.send, self.mem, self.rom = send, mem, rom
        self.BAL = {}

    def record(self):
        return bytearray(b''.join(struct.pack('<I', w) for w in self.mem(REC0, 0x68 // 4)))

    def foes(self, row=None):
        n = self.mem(COUNT)[0]
        out = []
        for e in self.mem(ENEMIES, min(n, 8)) if n else []:
            if e and self.mem(e + 0x1D0)[0] & 255 != 1 and (row is None or self.mem(e + 0x224)[0] == row):
                out.append((e, self.mem(e + 0x28C)[0] >> 10))
        return out

    def level150(self):
        r = self.record(); rom = self.rom
        T = struct.unpack_from('<151I', rom, EXP_TABLE)
        level = max(i for i in range(151) if T[i] <= struct.unpack_from('<I', r, 0x24)[0]) + 50      # levels count from 50 (as the game's)
        g = struct.unpack_from('<8i', rom, GROWTH + 0x20 * rom[CLASS + 0x18 * r[0x14]])
        hp, ki = grown(struct.unpack_from('<h', r, 0x18)[0], struct.unpack_from('<h', r, 0x1C)[0], g, 200 - level)
        struct.pack_into('<4h', r, 0x16, hp, hp, ki, ki); struct.pack_into('<I', r, 0x24, T[150])
        for k in range(3): r[0x28 + k] = min(255, r[0x28 + k] + 200 - level)
        self.send(*['poke %08X %08X' % (REC0 + o, struct.unpack_from('<I', r, o)[0]) for o in (0x14, 0x18, 0x1C, 0x24, 0x28)])
        pl = self.mem(PLAYER)[0]
        if pl:
            w1 = self.mem(pl + 0x1B4)[0]
            self.send('poke %08X %08X' % (pl + 0x1B0, r[0x28] | r[0x29] << 16), 'poke %08X %08X' % (pl + 0x1B4, (w1 & 0xFFFF0000) | r[0x2A]))
        return level - 50, hp, ki, list(r[0x28:0x2B])

    def heal(self):
        hp, ki = self.mem(REC0 + 0x18)[0] & 0xFFFF, self.mem(REC0 + 0x1C)[0] & 0xFFFF
        self.send('poke %08X %08X' % (REC0 + 0x14, (self.mem(REC0 + 0x14)[0] & 0xFFFF) | hp << 16), 'poke %08X %08X' % (REC0 + 0x18, ki << 16 | hp))

    def spar(self, name, row=None, secs=12, spot=None):
        """spot(x, y) -> (x, y, facing) of Goku beside a foe at (x, y) (positions <<8; facing 0 down, 1 up, 2 left, 3 right); default just
        below it, facing up."""
        self.heal(); pl = self.mem(PLAYER)[0]
        spot = spot or (lambda x, y: (x, y + (20 << 8), 1))
        f = [x for x in self.foes(row) if x[1] > 0]
        if not f: return None
        foe, fhp = f[0]; mx = self.mem(REC0 + 0x18)[0] & 0xFFFF
        gp, fp, mine, theirs, frames = mx, fhp, [], [], 0
        for k in range(secs * 6):
            if k % 4 == 0:
                x, y, facing = spot(*self.mem(foe + 0x1A0, 2))
                self.send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y), 'poke8 %08X %02X' % (pl + 0x10, facing))
            self.send('tap A 10'); frames += 11
            if foe not in [e for e, _ in self.foes(row)]: mine.append(fp); break       # he fell: his object is gone
            g, h = self.mem(REC0 + 0x16)[0] & 0xFFFF, self.mem(foe + 0x28C)[0] >> 10
            if h < fp: mine.append(fp - h)
            if g < gp: theirs.append(gp - g)
            fp, gp = h, g
            if h <= 0 or g <= mx // 3: break
        b = dict(hit=sum(mine) / max(len(mine), 1) / fhp, kill=fhp / max(sum(mine), 1) * frames / 60, taken=sum(theirs) / max(len(theirs), 1) / mx,
                 rate=sum(theirs) / mx / (frames / 60), hits=len(mine), hurt=len(theirs), hp=fhp)
        self.BAL[name] = b
        print('   BALANCE %-18s Goku\'s hits %5.2f%% of its %d HP (%d), %3.0f s to beat at that rate; its hits %5.2f%% of Goku\'s %d (%d), %4.1f%%/s'
              % (name, 100 * b['hit'], fhp, b['hits'], b['kill'], 100 * b['taken'], mx, b['hurt'], 100 * b['rate']), flush=True)
        self.heal()
        return b
