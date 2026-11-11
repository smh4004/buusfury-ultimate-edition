"""Is the boss bar on the screen what it should be? For the emulator tests: they call it in their own fights.
  bar = barcheck.Bar(rom_bytes, mem)        mem(address, words) reads the emulator's memory
  bar.check()  -> (columns shown or None, [problems])
  barcheck.expect(bar, send, 'Dabura', full=True) -> (ok, what was seen)
The bar is Buu's Fury's own (lib/bossbar.py): the story's boss fights have it from their scripts, and outfit.c bossbar_tick asks the
game for the same one in every fight the mod added (a foe on a stats row that zone26.row_names names). Read here as the game has it:
the foe list, the actor list, the two sprites in OAM, their tiles."""
import struct
import zone26, bossbar
COUNT, FOES, OAM, TILES, AREA, HUD, CAMERA, ACTORS = 0x03001BB0, 0x03001BB4, 0x07000000, 0x06010000, 0x0300197C, 0x03001069, 0x030019BC, 0x03001C4C


def find_table(rom):
    """The ROM's boss table (outfit.c boss_tab) checked whole: its two words are the row count and the table zone26.boss_table makes.
    -> [problems]"""
    tab, names = zone26.boss_table()
    for a_tab in _all(rom, tab):
        if rom.find(struct.pack('<2I', len(tab), 0x08000000 + a_tab)) >= 0: return []
    return ['the ROM has no boss table that points at the rows\' bytes']


def mod_table(rom):
    """The address of the table the mod's bars answer with (outfit.c bossbar_vt): the game's ten functions, but for the fourth ('is
    it shown?'), which is the mod's. Found by what it holds: a table's entries are offsets from the table itself. None if the ROM has
    none (or more than one)."""
    game = [bossbar.VTABLE + struct.unpack_from('<i', rom, bossbar.VTABLE - 0x08000000 + 4 * k)[0] for k in range(10)]
    found = []
    for at in range(0x800000, len(rom) - 40, 4):
        if struct.unpack_from('<i', rom, at)[0] + 0x08000000 + at != game[0]: continue
        rel = struct.unpack_from('<10i', rom, at)
        if all(rel[k] + 0x08000000 + at == game[k] for k in range(10) if k != 3) and 0x08800000 <= rel[3] + 0x08000000 + at < 0x0A000000:
            found.append(0x08000000 + at)
    return found[0] if len(found) == 1 else None


def _all(rom, what):
    i = rom.find(what)
    while i >= 0:
        yield i
        i = rom.find(what, i + 1)


# For a test that runs the emulator from a script file and reads nothing back while it runs: these lines at the moment to look at, then
# dumped(folder) is a `mem` over what they wrote.
DUMPS = ['dump bar_w 02000000 40000', 'dump bar_i 03000000 8000', 'dump bar_o 07000000 400', 'dump bar_v 06010000 8000']


def dumped(folder):
    parts = [(0x02000000, open(folder + '/bar_w.bin', 'rb').read()), (0x03000000, open(folder + '/bar_i.bin', 'rb').read()),
             (0x07000000, open(folder + '/bar_o.bin', 'rb').read()), (0x06010000, open(folder + '/bar_v.bin', 'rb').read())]
    def mem(a, n=1):
        for base, data in parts:
            if base <= a and a + 4 * n <= base + len(data): return list(struct.unpack_from('<%dI' % n, data, a - base))
        raise SystemExit('barcheck: %08X is in none of the dumps' % a)
    return mem


class Bar:
    def __init__(self, rom, mem):
        self.rom, self.mem = rom, mem
        self.table = struct.unpack_from('<I', rom, zone26.STATS_REFS[0])[0]
        self.names = zone26.row_names(); self.key = None; self.max = 0
        self.pictures = {bossbar.picture(rom, c): c for c in range(bossbar.COLS + 1)}
        self.tables = (bossbar.VTABLE, mod_table(rom))          # the game's own bar, and the mod's (the same but for 'shown?')

    def boss(self):
        """(name, health, their rows' health) of the room's boss as outfit.c boss_now reads him: of the mod's foes with a bar, the one
        whose row has the most health, and everyone of his name with him. Name None with nobody (and in the story's own boss fights,
        whose bars are their scripts')."""
        n = self.mem(COUNT)[0]; found = []
        for e in (self.mem(FOES, n) if 0 < n <= 32 else []):
            if not 0x02000000 <= e < 0x02040000 or self.mem(e + 0x1D0)[0] & 255 == 1: continue
            row = self.mem(e + 0x224)[0] - self.table
            who = self.names.get(row // 28) if row >= 0 and row % 28 == 0 else None
            if who is None: continue
            h = self.mem(e + 0x28C)[0]; h = (h - (1 << 32) if h >> 31 else h) >> 10
            whole = struct.unpack_from('<I', self.rom, self.table - 0x08000000 + row + 4)[0]
            found.append((who, max(h, 0), whole))
        if not found: return None, 0, 0
        name = max(found, key=lambda v: v[2])[0]
        return name, sum(v[1] for v in found if v[0] == name), sum(v[2] for v in found if v[0] == name)

    def foes(self):
        """Every foe on the list as boss() weighs it, for a failed check's message: (stats row, name, team byte, health, row health,
        where on the screen)."""
        n = self.mem(COUNT)[0]; out = []; cx, cy = [v - (1 << 32) if v >> 31 else v for v in self.mem(CAMERA, 2)]
        for e in (self.mem(FOES, n) if 0 < n <= 32 else []):
            if not 0x02000000 <= e < 0x02040000: out.append('%08X?' % e); continue
            row = self.mem(e + 0x224)[0] - self.table; h = self.mem(e + 0x28C)[0]; h = (h - (1 << 32) if h >> 31 else h) >> 10
            x, y = [(v - (1 << 32) if v >> 31 else v) >> 8 for v in self.mem(e + 0x1A0, 2)]
            whole = struct.unpack_from('<I', self.rom, self.table - 0x08000000 + row + 4)[0] if 0 <= row < 28 * 1024 and row % 28 == 0 else None
            out.append('row %s (%s) team %d health %s of %s at %d,%d on screen' % (row // 28 if row % 28 == 0 else hex(row), self.names.get(row // 28) if row % 28 == 0 else None,
                                                                              self.mem(e + 0x1D0)[0] & 255, h, whole, x - cx, y - cy))
        return out

    def actors(self):
        """The boss bars on the game's actor list (shown, or unloaded for a moment): [(address, y, speed, columns byte +0x15, target,
        whose: 'game' a script's, 'mod' one outfit.c asked for)]. There is never more than one."""
        out = []
        for base in (ACTORS + 4, ACTORS + 0x40C):
            n = self.mem(base)[0]
            for a in (self.mem(base + 4, n) if 0 < n <= 128 else []):
                if 0x02000000 <= a < 0x02040000 and self.mem(a)[0] in self.tables:
                    w = self.mem(a + 0x10, 3); y = w[2] & 255
                    out.append((a, y - 256 if y > 127 else y, w[1] >> 24, w[1] >> 8 & 255, w[0], 'game' if self.mem(a)[0] == bossbar.VTABLE else 'mod'))
        return out

    def sprites(self):
        """The bar's two sprites in OAM, at rest: the tile number of the first, or None. Both must be there, one after the other, on
        the tiles the game lays out (+0, +8), at the HUD's priority, at y 8."""
        oam = self.mem(OAM, 256)
        for k in range(127):
            got = []
            for j, (a0, a1, tile) in enumerate(bossbar.SPRITES):
                w0, w1 = oam[2 * (k + j)], oam[2 * (k + j) + 1]
                got.append((w0 & 0xFFFF) == (a0 | bossbar.Y) and (w0 >> 16) == a1 and (w1 >> 10 & 3) == 1 and ((w1 & 0x3FF) - tile) & 0x3FF)
            if all(g is not False for g in got) and got[0] == got[1]: return got[0]
        return None

    def read(self):
        """What is on the screen: None (no bar at rest), or the columns of health its tiles show (-1: not the bar's picture at all)."""
        tile = self.sprites()
        if tile is None: return None
        raw = b''.join(struct.pack('<I', w) for w in self.mem(TILES + tile * 32, bossbar.BYTES // 4))
        return self.pictures.get(raw, -1)

    def check(self, max_hp=None):
        """-> (the columns read or None, [problems]). max_hp: the fight's whole health where the foe list no longer tells it (a Cell
        Junior has fallen). With no boss of the mod's in the room nothing is asked of the bar here (the story's fights have their own)."""
        name, hp, full = self.boss(); hud = self.mem(HUD)[0] & 2; key = (self.mem(AREA)[0] & 0xFFFF, name)
        if key != self.key or name is None: self.key = key; self.max = 0
        self.max = max_hp or max(self.max, full, hp)
        got = self.read(); bad = []; bars = self.actors()
        if len(bars) > 1: bad.append('%d boss bars on the actor list' % len(bars))
        if name is None: return got, bad
        if hp <= 0:
            if got is not None: bad.append('the boss bar is still there with the boss fallen')
            return got, bad
        if not hud: return got, bad                      # (a scene: the game's own business with its bar)
        if got is None: return got, bad + ['no boss bar for %s (%d of %d)' % (name, hp, self.max)]
        want = bossbar.columns(hp, self.max)
        if got < 0: bad.append('the bar\'s tiles are not its picture')
        elif got != want: bad.append('%s has %d of %d health: %d columns, the bar shows %d' % (name, hp, self.max, want, got))
        return got, bad


def expect(bar, send, name, tries=40, full=False, **kw):
    """The room's boss is `name` and his bar is up and right (full: with all its columns). The bar is made in the first frames the
    player has control, slides down for sixteen frames, and is drawn the frame after the health changes: looks again a frame later,
    up to `tries` times. -> (ok, what was seen)"""
    for _ in range(tries):
        who = bar.boss()[0]; got, bad = bar.check(**kw)
        if not bad and got is not None and who == name and (not full or got == bossbar.COLS): return True, '%d of %d columns' % (got, bossbar.COLS)
        send('run 1')
    return False, '%s; the boss is %s, the bar shows %s; foes: %s' % ('; '.join(bad) or 'not as asked', who, got, bar.foes())


def gone(bar, send, tries=40):
    """The bar has left the screen and the actor list (it slides out for sixteen frames once the boss has fallen). -> ok"""
    for _ in range(tries):
        if bar.read() is None and not bar.actors(): return True
        send('run 1')
    return False
