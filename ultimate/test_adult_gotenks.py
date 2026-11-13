#!/usr/bin/env python3
"""Adult Gotenks (lib/adult_gotenks.py), played in the emulator. Build first, with him in:
  BFU_ADULT_GOTENKS=1 [BFU_AG_HEAD=head|hair|recolour] BFU_OUT=<dir> python3 ultimate/build.py --debug
  python3 ultimate/test_adult_gotenks.py <dir>/BFU_debug_PERSONAL_USE_ONLY.gba [work dir]
Nov 12, the owner: "Make this separate from the other Gotenks too where it's only possible to use them for those two chars", and 22:46: "Don't
allow any invisible stuff no clipping no stray pixels no backwards head body missing limbs wrong colors missing vest missing hair wrong face".
The dance's button game can't be played by a script (five random moves), so it is pressed through with wrong moves and, where the
fusion native (outfit.c fusion_native) is called, record 5 is given the form a right dance gives (script 13: Gotenks, his Super Saiyan or
Super Saiyan 3 one, by the dancers' class), as test_fusion.py does for Gogeta.
1. Goten and Trunks in their own looks: the game's Gotenks, as ever (each outcome: Gotenks, his Super Saiyan or Super Saiyan 3 one).
2. In GT looks, the same outcome: Adult Gotenks, in the form the game's Gotenks comes out in, playing, the two out of the party.
3. A wrong dance in GT looks: the fat or thin Gotenks as ever, never Adult Gotenks.
4. He changes form as Gotenks does (Super Saiyan, Super Saiyan 3); his rows chain so and back, each his own figure and portraits.
5. Every frame of every head passes the checks (no gi or blue left, no new hole, no stray piece), and nothing jumps to a bad address."""
import json, os, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, HERE + '/lib']
import adult_gotenks as AG
ROM = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/adult_gotenks'; os.makedirs(OUT, exist_ok=True)
MAP = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
RECS, RS, G, COMBAT = 0x03001560, 0x68, 0x03001068, 0x03001988
FORM_SIZE = 24
route = open('tools/harness/long.txt').read().split('\n')[:93]
rom = open(ROM, 'rb').read(); clean = open('baserom.gba', 'rb').read()
u = lambda o: struct.unpack_from('<I', rom, o)[0]
NATIVE_REFS = (0x3F40, 0x4030)
FUSION_NATIVE = u(u(NATIVE_REFS[0]) - 0x08000000 + 4 * 0xA8) & ~1          # (the script's native 0xA8: outfit.c fusion_native)
fails = []


def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)


class Game:
    def __init__(self):
        self.p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', OUT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.bad = False
        self.send('guardon 0x09000000', *route)

    def send(self, *ls):
        for l in ls: self.p.stdin.write(l + '\n')
        self.p.stdin.flush()

    def mem(self, a, n=1):
        self.send('mem %08X %d' % (a, n))
        while True:
            l = self.p.stdout.readline()
            if not l: raise SystemExit('harness ended')
            if 'bad pc' in l: self.bad = True
            if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]

    def forms(self): return [self.mem(RECS + c * RS + 0x14)[0] & 255 for c in range(9)]
    def me(self): return self.mem(G)[0] & 255
    def bits(self, c): return self.mem(RECS + c * RS)[0] & 3

    def bp(self, addr, frames):
        """Run until the CPU is at addr (or frames pass): -> hit?"""
        self.send('bp %08X %d' % (addr, frames), 'mem %08X 1' % G)
        lines = []
        while True:
            l = self.p.stdout.readline()
            if not l: raise SystemExit('harness ended')
            if l.startswith('mem %08x' % G): break
            lines.append(l)
        b = [l for l in lines if l.startswith('bp ')]
        return bool(b) and 'not hit' not in b[0]

    def play_goten(self, goten, trunks):
        """Goten and Trunks join (the debug intro's party hasn't them), Goten in the look `goten` plays, Trunks wears `trunks`."""
        for c in (2, 3): self.send('poke8 %08X 03' % (RECS + c * RS))
        self.send('tap A 60', 'tap A 60', 'run 30'); self.mem(G)
        for k in range(9):                            # Goten's place on Switch Character: Down on each place moves whose form?
            b = self.forms(); self.send('tap DOWN 40', 'run 10'); a = self.forms(); self.send('tap UP 40', 'run 10')
            if [c for c in range(9) if b[c] != a[c]][:1] == [2]: break
            self.send('tap RIGHT 40', 'run 10')
        self.send('poke8 %08X %02X' % (RECS + 2 * RS + 0x14, goten), 'poke8 %08X %02X' % (RECS + 3 * RS + 0x14, trunks), 'run 4', 'tap A 200', 'run 60')

    def dance(self, outcome):
        """Goten dances (the Fusion Dance in his first slot, B in a fight); at the fusion native record 5 is given `outcome` (None: the
        wrong dance's own). -> (did the native come, record 5's form at it)."""
        r = RECS + 2 * RS
        self.send('poke8 %08X 01' % (r + 0x0C), 'poke8 %08X 0C' % (r + 0x0D), 'poke8 %08X 00' % (r + 0x15), 'poke %08X 00000001' % COMBAT,
                  'run 4', 'keys B', 'run 30', 'keys', 'run 10')
        for i in range(30):
            for k in ('keys %s' % ('LEFT', 'RIGHT')[i & 1], 'keys'):
                self.send(k)
                if self.bp(FUSION_NATIVE, 30):
                    self.send('keys'); was = self.mem(RECS + 5 * RS + 0x14)[0] & 255
                    if outcome is not None: self.send('poke8 %08X %02X' % (RECS + 5 * RS + 0x14, outcome))
                    self.send('run 600')
                    return True, was
        self.send('keys')
        return False, None

    def use(self, c, skill, wait=20):
        """Record c holds `skill` (his only one), full ki, and presses B: -> his form after the change (polled for a few seconds)."""
        r = RECS + c * RS
        self.send('poke8 %08X 01' % (r + 0x0C), 'poke8 %08X %02X' % (r + 0x0D, skill), 'poke8 %08X 00' % (r + 0x15), 'poke8 %08X FF' % (r + 0x1A),
                  'poke8 %08X 03' % (r + 0x1B), 'poke8 %08X FF' % (r + 0x1C), 'poke8 %08X 03' % (r + 0x1D), 'poke %08X 00000001' % COMBAT,
                  'run 2', 'keys B', 'run 4', 'keys')
        before = self.mem(r + 0x14)[0] & 255
        for _ in range(wait):
            self.send('run 30')
            f = self.mem(r + 0x14)[0] & 255
            if f != before: break
        self.send('run 240')
        return self.mem(r + 0x14)[0] & 255

    def close(self): self.p.stdin.close(); self.p.wait()


def case(name, goten, trunks, outcome, shot):
    """Goten in one look and Trunks in another dance; at the fusion native record 5 gets `outcome` (None: the wrong dance's own). -> (the
    native came, record 5's form at it, its form after, who plays, Goten's, Trunks's and Gotenks's party bits)."""
    g = Game(); g.play_goten(MAP[goten] if isinstance(goten, str) else goten, MAP[trunks] if isinstance(trunks, str) else trunks)
    playing = g.me()
    came, was = g.dance(outcome)
    f = g.mem(RECS + 5 * RS + 0x14)[0] & 255; g.send('shot ' + shot)
    r = (came and playing == 2, was, f, g.me(), g.bits(2), g.bits(3), g.bits(5))
    print('   %s: Goten played and the native came %s (record 5 form %s there); after: record 5 form %d, playing %d, party bits Goten %d Trunks %d Gotenks %d' % ((name,) + r))
    check('%s: no bad jumps' % name, not g.bad)
    g.close()
    return r


AG_OF = {31: 'adult_gotenks', 34: 'adult_gotenks_ssj', 35: 'adult_gotenks_ssj3'}
# 1-3 in the emulator. The game's own Gotenks first (their own looks: forms 19 and 21, their Super Saiyan 20 and 22), then the GT looks with
# the same outcome: Adult Gotenks in the form the game's Gotenks has after it (the game takes a fused fighter's form down as he comes in).
for name, own, gt_, outcome in (('a right dance', (19, 21), ('goten_gt', 'trunks_gt'), 31),
                                ('a Super Saiyan dance', (20, 22), ('goten_gt_ssj', 'trunks_gt_ssj'), 34),
                                ('a Super Saiyan 3 Gotenks', (19, 21), ('goten_gt_green', 'trunks_gt'), 35)):
    o = case('their own looks, ' + name, *own, outcome, 'own_%d' % outcome)
    n = case('GT looks, ' + name, *gt_, outcome, 'gt_%d' % outcome)
    check("their own looks, %s: the game's Gotenks (form %d), playing, Goten and Trunks out of the party" % (name, o[2]),
          o[0] and o[2] in AG_OF and o[3] == 5 and not o[4] & 1 and not o[5] & 1 and o[6] == 3)
    check('GT looks, %s: Adult Gotenks in that form (%s, form %d), playing, Goten and Trunks out of the party' % (name, AG_OF.get(o[2]), n[2]),
          n[0] and o[2] in AG_OF and n[2] == MAP[AG_OF[o[2]]] and n[3] == 5 and not n[4] & 1 and not n[5] & 1 and n[6] == 3)
# 4: he changes form as Gotenks does (Super Saiyan, then Super Saiyan 3), in his own figures
g = Game(); g.play_goten(MAP['goten_gt'], MAP['trunks_gt']); g.dance(31)
seen = [g.mem(RECS + 5 * RS + 0x14)[0] & 255]; g.send('shot ag_change_0')
for k, skill in enumerate((20, 22)):
    seen.append(g.use(5, skill)); g.send('shot ag_change_%d' % (k + 1))
check('Adult Gotenks changes form: base, Super Saiyan, Super Saiyan 3 (%s)' % seen, seen == [MAP['adult_gotenks'], MAP['adult_gotenks_ssj'], MAP['adult_gotenks_ssj3']])
check('no bad jumps (his changes)', not g.bad); g.close()
w = case('GT looks, a wrong dance', 'goten_gt', 'trunks_gt', None, 'gt_wrong')
check('GT looks, a wrong dance: the fat or thin Gotenks as ever (form %s), never Adult Gotenks (form %d after)' % (w[1], w[2]),
      w[0] and w[1] in (32, 33) and w[2] not in [MAP[v] for v in AG_OF.values()])

# 4: the form rows (the built ROM's table)
TABLE = 0x800000                                  # (the build's form table: form_table, 0x08800000)
rows = {n: rom[TABLE + FORM_SIZE * MAP[n]:TABLE + FORM_SIZE * MAP[n] + FORM_SIZE] for n in AG.ACTORS.values()}
up = {n: r[0x16] for n, r in rows.items()}; down = {n: r[0x17] for n, r in rows.items()}
check('his forms chain up: base -> Super Saiyan -> Super Saiyan 3 (%s)' % up,
      up['adult_gotenks'] == MAP['adult_gotenks_ssj'] and up['adult_gotenks_ssj'] == MAP['adult_gotenks_ssj3'] and up['adult_gotenks_ssj3'] == 255)
check('and down to his base (%s)' % down, down['adult_gotenks_ssj'] == MAP['adult_gotenks'] and down['adult_gotenks_ssj3'] == MAP['adult_gotenks'] and down['adult_gotenks'] == 255)
actors = {n: r[0xE] for n, r in rows.items()}
check('each form has a figure of its own (%s)' % actors, len(set(actors.values())) == 3 and all(a not in (rom[TABLE + FORM_SIZE * f + 0xE] for f in (31, 34, 35)) for a in actors.values()))
ports = {n: list(r[0x10:0x16]) for n, r in rows.items()}
check('and portraits of his own (%s)' % ports, len({p for v in ports.values() for p in v}) == 7 and min(p for v in ports.values() for p in v) > 187)

# 5: every frame of every head
gh = AG.Gohan(clean, 0x6B6BD8); gk = AG.Gotenks(clean, 0x6B6BD8, gh)
for v in ('head', 'hair', 'recolour'):
    for f in AG.ACTORS:
        fr, notes = AG.frames(clean, 0x6B6BD8, f, v, gh=gh, gt=gk)
        bad = AG.problems(gh, fr, notes)
        check('%s head, %s: %d frames, none with a hole, a stray piece or gi colours %s' % (v, f, len(notes), bad[:3]), not bad)
# 6: the grown look's portraits (Gohan's head set into Gotenks's own picture, lib/adult_gotenks.py Portraits.inlay): one skin, one
# background, nothing left of either picture's own (Gotenks's pink skin, Gohan's yellow or cyan behind him, the Super Saiyan pictures'
# purple), the game's frame untouched; and Gotenks's hair is his picture's own: above his brow line pixel for pixel, and nearly all of it
# over the whole picture (the rest is behind his ears, moved up, and Gohan's face)
import numpy as np
AG.set_palette(np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3))
pics = AG.Portraits(clean)
ROWS = np.mgrid[:64, :64][0]
for f in AG.ACTORS:
    kraw = pics.art[{'base': 68, 'ssj': 71, 'ssj3': 73}[f]]; kface = pics.face(kraw)
    khair = pics.hair(kraw, AG.P_HAIR + AG.P_LAV if f == 'base' else AG.P_GOLD + (208, 1)) & ~kface
    top = khair & (ROWS < pics._eyes(kraw, AG._rows_filled(kface))[0] - 4 - AG.LIFT[f])      # (above Gohan's brow line)
    for i, a in enumerate(pics.make('grown', f)):
        inner = a[pics.inner]
        left = {'pink skin': int(np.isin(inner, (37, 212, 213, 214)).sum()), "Gohan's background": int(np.isin(inner, (5, 7, 73, 74)).sum()),
                'purple background': int((inner == 88).sum()) if f != 'base' else 0}
        check('portrait %s %d: nothing of the two pictures left over %s, the frame as the game has it' % (f, i, left),
              not any(left.values()) and (a[pics.frame] == pics.art[69][pics.frame]).all())
        same = a == kraw; share = (same & khair).sum() / khair.sum()
        check("portrait %s %d: Gotenks's hair is his picture's own: all %d pixels above his brow line, %.0f%% of it in the whole picture"
              % (f, i, top.sum(), 100 * share), bool(same[top].all()) and share >= 0.85)
print('screens in', OUT)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
