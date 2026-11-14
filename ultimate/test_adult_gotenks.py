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
# 5b: the grown look, the one the build has (Kid Gotenks's own frames grown, AG.grown_frames). No shirt (Nov 13, 21:17, the owner):
# his chest is bare under the vest, as Kid Gotenks's is. Every frame of his three figures in the ROM (the moved actor table, the
# figure his form row names) is the library's; none has the undershirt: against the frames with it (AG.SHIRT), the only pixels that
# differ are the shirt's, each his own skin's colour here.
# Nov 13, 21:48, the owner: "Wtf is that ghost attack frame" (Kid Gotenks's dive, slots 8 and 16, grown: his head had been pulled
# taller). His head is never stretched: in every base frame his hair's purple has as many pixels as in the Kid Gotenks frame it is
# grown from, and where he banks in flight (slot 16, front and side) the frame is Kid Gotenks's own. And he stands where Kid
# Gotenks stands: each frame is in the ROM at the very place the library has it (it was 8 rows higher: he hovered over his shadow),
# his feet in his idle frames on Kid Gotenks's row.
import numpy as np
ACTORS_AT = 0x850000                              # (build.py: the moved actor table)
SHIRT_C, SKIN_C = list(set(AG.G_UNDER.values())), list(AG.G_UNDER)
OUTFIT = AG.G_VEST + AG.G_PANTS                   # (his vest, its yellow padding, his trousers)
TEALS = {}
for f, n in AG.ACTORS.items():
    act = struct.unpack_from('<H', rom, TABLE + FORM_SIZE * MAP[n] + 0xE)[0] - 9
    got = AG.cells(rom, ACTORS_AT, act); teal = AG.grown_frames(clean, 0x6B6BD8, f)
    want = AG.grown_frames(clean, 0x6B6BD8, f, teal=False)     # (in Kid Gotenks's colours: section 5c checks the picture's colours)
    TEALS[f] = (teal, want)
    kid = AG.cells(clean, 0x6B6BD8, AG.GROWN[f])  # (Kid Gotenks's own frames, the game's)
    was = AG.SHIRT; AG.SHIRT = True; worn = AG.grown_frames(clean, 0x6B6BD8, f, teal=False); AG.SHIRT = was
    tot = same = had = px = other = cols = fewer = hair = 0
    for s in want:
        for v in range(3):
            for j, c in enumerate(want[s][v]):
                tot += 1
                same += s in got and j < len(got[s][v]) and bool((got[s][v][j][AG.OUT] == teal[s][v][j]).all())     # (the same pixels at the same place)
                m = worn[s][v][j] != c
                had += bool(m.any()); px += int(m.sum())
                other += int((~(np.isin(worn[s][v][j][m], SHIRT_C) & np.isin(c[m], SKIN_C))).sum())
                kc = kid[s if s in kid else 15][v][j]     # (growing him doubles rows and a column of Kid Gotenks's frame: it adds no colour and
                cols += set(np.unique(c).tolist()) == set(np.unique(kc).tolist())      #  drops none, and no pixel of his outfit is lost)
                fewer += any((c == o).sum() < (kc == o).sum() for o in OUTFIT)
                hair += f == 'base' and int(np.isin(c, AG.G_HAIR).sum()) != int(np.isin(kc, AG.G_HAIR).sum())
    check("grown look, %s (figure %d): all %d frames in the ROM are the library's (%d), his chest bare under the vest: %d of them would "
          "wear the undershirt (%d pixels of it, each his own skin here; %d other pixels differ)" % (f, act, tot, same, had, px, other),
          not AG.SHIRT and same == tot and had >= 40 and other == 0)
    check("grown look, %s: his outfit's colours are Kid Gotenks's (figure %d): %d of %d frames have exactly their Kid Gotenks frame's "
          "colours, %d with less of a vest, padding or trouser colour than it" % (f, AG.GROWN[f], cols, tot, fewer), cols == tot and fewer == 0)
    last = lambda c: int(np.nonzero(c.any(1))[0].max())
    feet = [(last(got[0][v][j][AG.OUT]), last(kid[0][v][j][AG.OUT])) for v in range(3) for j in range(len(kid[0][v]))]
    check("grown look, %s: he stands where Kid Gotenks stands: his feet's row in his idle frames in the ROM and Kid Gotenks's %s" % (f, feet),
          all(a_ == b_ for a_, b_ in feet))
    # (Nov 14, 00:07, the owner: "His posture seems slightly off to the side by a pixel or two fix it": widened on his left only, his
    # body was half a pixel left of his head.) Standing, from the front and from behind, his body below his collar is centred where
    # Kid Gotenks's is
    def mid(c, by):                               # (by: base's frame: where his collar is, and his body is what is the same as in it,
        top = np.nonzero(np.isin(by, AG.G_YEL).any(1))[0].min()      #  not his Super Saiyan hair, yellow too and long)
        xs = np.nonzero(((c == by) & (c > 0))[top:].any(0))[0]
        return (xs.min() + xs.max()) / 2
    kb = AG.cells(clean, 0x6B6BD8, AG.GROWN['base'])
    mids = [(mid(want[0][v][j], TEALS['base'][1][0][v][j]), mid(kid[0][v][j][AG.OUT], kb[0][v][j][AG.OUT])) for v in (0, 1) for j in range(len(kid[0][v]))]
    check("grown look, %s: standing, his body is centred where Kid Gotenks's is, under his head (his, Kid Gotenks's: %s)" % (f, mids),
          all(a_ == b_ for a_, b_ in mids))
    if f == 'base':
        fly = [bool((want[16][v][j] == kid[16][v][j][AG.OUT]).all()) for v in (0, 2) for j in range(len(kid[16][v]))]
        # his bored animation (Nov 13, 23:16, the owner: "That "lying" down is broken"): no wider than Kid Gotenks's, his head as drawn,
        # and lying (frames 1 and 2) his raised legs 2 rows longer: the top of his shoes 2 rows higher, nothing else of the frame moved
        span = lambda a: (np.nonzero(a.any(0))[0].min(), np.nonzero(a.any(0))[0].max())
        bw = [span(want[AG.BORED][v][j]) == span(kid[AG.BORED][v][j][AG.OUT]) for v in range(3) for j in range(3)]
        top = lambda a: np.nonzero(np.isin(a, (112,)).any(1))[0].min()
        hairs = [bool((np.isin(want[AG.BORED][v][j], AG.G_HAIR) == np.isin(kid[AG.BORED][v][j][AG.OUT], AG.G_HAIR)).all()) for v in range(3) for j in (1, 2)]
        lift = [int(top(kid[AG.BORED][v][j][AG.OUT]) - top(want[AG.BORED][v][j])) for v in range(3) for j in (1, 2)]
        check("grown look, base: bored, as wide as Kid Gotenks (%d of 9 frames), lying his head where Kid Gotenks's is (%d of 6) and his legs "
              "longer (the shoes' tops %s rows higher)" % (sum(bw), sum(hairs), lift), all(bw) and all(hairs) and all(x == 2 for x in lift))
        check("grown look, base: his head is never stretched: %d frames whose hair differs in size from Kid Gotenks's; banking in flight "
              "(slot 16, front and side) %d of %d frames are Kid Gotenks's own" % (hair, sum(fly), len(fly)), hair == 0 and all(fly))
# 5c: his outfit in the owner's picture's colours (Nov 13, 23:37, the owner: "Can you change the colors of his waistband/vest/boots to
# this on the right": a black vest, a teal sash and ankle wraps, black boots and wristbands; AG.metamoran). Against the same frames in Kid
# Gotenks's colours, the only pixels changed are his outfit's greys, each to its part's colour (AG.OUTFIT_MAPS); no teal within 2 pixels
# of his hair (but lying, banking and falling, where his body is beside his head); standing
# (every view of every form) the sash at his waist and the wraps at his ankles are teal, and none of his vest beside its padding is left grey.
from scipy import ndimage
TEAL_C = (71, 186, 199)
pairs = {(a, b) for mp in AG.OUTFIT_MAPS.values() for a, b in mp.items()}
for f, (teal, plain) in TEALS.items():
    bad = near = 0; stand = []
    for s in teal:
        for v in range(3):
            for j, c in enumerate(teal[s][v]):
                p = plain[s][v][j]; m = c != p
                bad += sum((int(a), int(b)) not in pairs for a, b in zip(p[m], c[m]))
                hair = TEALS['base'][1][s][v][j] if s in TEALS['base'][1] and len(TEALS['base'][1][s][v]) == len(teal[s][v]) else p
                if s not in (8, 16, 17):    # (lying, banking, falling: his body is beside his head)
                    near += int((np.isin(c, TEAL_C) & ndimage.binary_dilation(np.isin(hair, AG.G_HAIR), iterations=2)).sum())
                if s == 0:
                    ys = np.nonzero(c.any(1))[0]; low = ys.max()
                    pad = ndimage.binary_dilation(np.isin(c, AG.G_YEL)) & np.isin(c, (113, 115))
                    yel = np.nonzero(np.isin(TEALS['base'][1][0][v][j], AG.G_YEL).any(1))[0].max()     # (his padding's last row: base's)
                    waist = int(np.isin(c[yel:low - 4], TEAL_C).sum())
                    if f == 'ssj3' and v == 1: waist = max(waist, 4)      # (from behind his Super Saiyan 3 hair hangs over his waist)
                    stand.append((waist, int(np.isin(c[low - 4:], TEAL_C).sum()), int(pad.sum())))
    check("picture's colours, %s: only his outfit's greys change, each to its part's colour (%d pixels otherwise), no teal by his hair (%d); "
          "standing, teal at his waist and ankles and no grey left in his vest by its padding (teal at the waist, at the ankles, grey: %s)"
          % (f, bad, near, stand), bad == 0 and near == 0 and all(a >= 4 and b >= 4 and g == 0 for a, b, g in stand))
# 6: the grown look's portraits (Gohan's own picture in the outfit under Gotenks's own hair and rolls, lib/adult_gotenks.py
# Portraits.inlay): one skin, one background, nothing left of either picture's own (Gotenks's pink skin, Gohan's yellow or cyan behind
# him, the Super Saiyan pictures' purple), the game's frame untouched; Gotenks's hair is his picture's own (above Gohan's brow line all
# of it but what his ears' tops are in front of, and nearly all of it over the whole picture: the rest is behind Gohan's face, ears and
# shoulders); his collar's rolls whole. Gohan's ears are whole: every pixel of them and of the line round them is in the picture.
# Super Saiyan: his two brows are the same size (the left one was a broken mirror of the right). No shirt (Nov 13, 21:17, the owner:
# "just remove the shirt and do the vest only its not looking right no matter how you do it", "Sprites and portraits both"): his neck
# and shoulders bare, the vest Gotenks's own.
import numpy as np
from scipy import ndimage
AG.set_palette(np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3))
pics = AG.Portraits(clean)
ROWS, COLS = np.mgrid[:64, :64]
bare_c, bare_d = pics.gohan_clean(AG.BARE_BODY); bare_pic, _bg, bare_body = pics._bare(AG.BARE_BODY, bare_c, bare_d)
as_worn = np.arange(256, dtype=np.uint8)          # (Gotenks's picture's vest cloth -> the colours his vest has on his figure)
for _a, _b in AG.VEST_AS_WORN.items(): as_worn[_a] = _b
FIG_VEST = tuple(AG.OUTFIT_MAPS[1][c] for c in AG.G_VEST[:3]) if AG.TEAL else AG.G_VEST[:3]     # (his figure's vest: since Nov 13, 23:37
check("the portraits' vest colours are his figure's: %s, all of them in his frames' vest (%s) or its black line"         #  a shade darker)
      % (sorted(set(AG.VEST_AS_WORN.values())), FIG_VEST), set(AG.VEST_AS_WORN.values()) <= set(FIG_VEST) | {1})
for f in AG.ACTORS:
    kp = {'base': 68, 'ssj': 71, 'ssj3': 73}[f]; kraw = pics.art[kp]; kface = pics.face(kraw)
    khair = pics.hair(kraw, AG.P_HAIR + AG.P_LAV if f == 'base' else AG.P_GOLD + (208, 1)) & ~kface
    ke, kmid = pics._eyes(kraw, AG._rows_filled(kface))
    top = khair & (ROWS < ke - 4 - AG.LIFT[f])      # (above Gohan's brow line)
    rolls = pics.rolls_whole(kp)
    cloth = np.isin(kraw, AG.P_VEST) & ~khair & ~rolls & (ROWS >= ke + 8) & pics.inner     # (Gotenks's vest's cloth: it hangs to the picture's foot)
    lab, _n = ndimage.label(cloth, np.ones((3, 3))); cloth = np.isin(lab, [j for j in np.unique(lab[56:60]) if j])
    by, bx = ke - bare_d['eye'] - AG.LIFT[f], int(round(kmid - bare_d['mid']))             # (Gohan's calm picture, bare, where the portrait has it)
    bare = AG._shift(bare_pic, by, bx); bare_at = AG._shift(bare_body, by, bx, False) & pics.inner
    for i, a in enumerate(pics.make('grown', f)):
        gp = AG.PICS[f][i][0]; gc, d = pics.gohan_clean(gp)
        inner = a[pics.inner]
        left = {'pink skin': int(np.isin(inner, (37, 212, 213, 214)).sum()), "Gohan's background": int(np.isin(inner, (5, 7, 73, 74)).sum()),
                'purple background': int((inner == 88).sum()) if f != 'base' else 0}
        check('portrait %s %d: nothing of the two pictures left over %s, the frame as the game has it' % (f, i, left),
              not any(left.values()) and (a[pics.frame] == pics.art[69][pics.frame]).all())
        same = a == kraw; share = (same & khair).sum() / khair.sum(); whole = (same & rolls).sum() / rolls.sum()
        check("portrait %s %d: Gotenks's hair is his picture's own (%d of %d pixels above his brow line, %.0f%% of it in the whole picture) and "
              "his collar's rolls are whole (%.0f%%)" % (f, i, (same & top).sum(), top.sum(), 100 * share, 100 * whole),
              (same & top).sum() >= 0.98 * top.sum() and share >= 0.85 and whole >= 0.98)
        dy, dx = ke - d['eye'] - AG.LIFT[f], int(round(kmid - d['mid']))
        ears = AG._shift(d['ears'], dy, dx, False) & pics.inner; line = ears & (AG._shift(d['g'], dy, dx) == 208)
        shown = (a[line] == 208).sum()
        check("portrait %s %d: Gohan's ears are whole: %d of the %d pixels of the line round them are in the picture" % (f, i, shown, line.sum()),
              line.sum() >= 30 and shown >= (0.8 if f == 'ssj3' else 0.95) * line.sum())
        if f == 'ssj':
            b = d['brow'] & (ROWS < d['eye']); l, r = int((b & (COLS < d['mid'])).sum()), int((b & (COLS > d['mid'])).sum())
            check("portrait %s %d: his two brows are whole: %d pixels of the left one and %d of the right above his eyes" % (f, i, l, r),
                  min(l, r) >= 12 and abs(l - r) <= 8)
        # no shirt (Nov 13, 21:17): below his ears nothing dark is on him but his own head's (his mouth); his neck and shoulders are
        # Gohan's calm picture's as it is drawn, bare (Portraits._bare), wherever his head, Gotenks's hair, rolls and vest aren't in
        # front; the vest's cloth is where Gotenks's own picture has it, every pixel, in the colours his vest has on his figure (21:39,
        # the owner: "Fix the color of the vest in the portraits and on the body and make sure the colors of the outfit match Kid
        # Gotenks outfit colors"): shade for shade (AG.VEST_AS_WORN), none of his picture's purple left, and its rolls his picture's
        head = (AG._shift(d['face'] & ~d['neck'], dy, dx, False) | ears) & pics.inner
        below = ROWS >= d['eb'] + dy - 1
        shirt = int((np.isin(a, AG.P_DARK) & pics.inner & (a != kraw) & ~head & ~cloth & below).sum())
        near = lambda m: ndimage.binary_dilation(m, np.ones((3, 3), bool))
        region = bare_at & below & ~near(head) & ~rolls & ~khair & ~near(cloth)
        own = int((a == bare)[region].sum()); skin = int(np.isin(a, AG.P_SKIN + (208,))[region].sum()); vest = cloth & ~head
        worn = int((a == as_worn[kraw])[vest].sum()); purple = int((np.isin(a, AG.P_VEST) & ~khair & (ROWS >= ke + 8) & pics.inner).sum())
        check("portrait %s %d: no shirt (%d dark pixels on him below his ears that aren't the vest); his neck and shoulders are bare, "
              "Gohan's calm picture's as drawn (%d of %d pixels its own, %d skin or its line); the vest's cloth is where Gotenks's "
              "picture has it, in his figure's vest's colours (%d of %d pixels, %d purple left)"
              % (f, i, shirt, own, region.sum(), skin, worn, vest.sum(), purple),
              not AG.SHIRT and shirt == 0 and region.sum() >= 90 and own >= 0.95 * region.sum() and skin == region.sum()
              and vest.sum() >= 8 and worn == vest.sum() and purple == 0)
# 7: his sprite memory. Each frame is one piece in the record's share of sprite memory (record +2). 4 KB, as Broly's, worked on foot but
# over the world map he wasn't drawn and the ending's flight never went on to the Lookout (Nov 13, found filming what plays each
# animation): 2 KB, the same for all three forms (a change of size on transforming scrambles other sprites, build.py android17), and
# every piece fits it (the Super Saiyan 3 change's frames grow taller only, adult_gotenks.grown).
for f, n in AG.ACTORS.items():
    act = struct.unpack_from('<H', rom, TABLE + FORM_SIZE * MAP[n] + 0xE)[0] - 9
    rec = u(ACTORS_AT + 4 * act) - 0x08000000; most = 0
    for sl in range(u(rec) & 0xFF):
        an = u(rec + 0x54 + 4 * sl)
        if not an: continue
        an -= 0x08000000
        for k in range(u(an)):
            for v in range(3):
                fp = u(an + 4 + 16 * k + 4 * v) - 0x08000000
                for j in range(u(fp)):
                    w_, h_ = rom[fp + 8 + 12 * j + 2], rom[fp + 8 + 12 * j + 3]; most = max(most, w_ * h_)
    check("%s's sprite memory: %d bytes a frame, his biggest piece %d" % (n, struct.unpack_from('<H', rom, rec + 2)[0], most),
          struct.unpack_from('<H', rom, rec + 2)[0] == 2048 and most <= 2048)
# 8 (with a story build, BFU_ZONE_ROM: BFU_ADULT_GOTENKS=1 build.py --debug --zone): he flies over the world map. The real ending as each
# of his forms (test_story.py's route): its flight shows his figure, and flying on, his flying animation (15) and, turning, his banking
# one (16); then landing reaches West City, as for anyone.
ZONE = os.environ.get('BFU_ZONE_ROM')
if ZONE:
    zrom = open(ZONE, 'rb').read(); zu = lambda o: struct.unpack_from('<I', zrom, o)[0]
    zmap = json.load(open(ZONE.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
    def zrun(lines):
        pth = OUT + '/z.txt'; open(pth, 'w').write('\n'.join(lines) + '\n')
        return subprocess.run(['tools/harness/harness', ZONE, pth, OUT], capture_output=True, text=True, timeout=900).stdout
    zstart = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'guardon 0x09000000']
    zptr = lambda base: int([l for l in zrun(base + ['mem 03001C34 1']).splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
    zpl = zptr(zstart); zrun(zstart + ['dump g 03001068 8a8']); zg = open(OUT + '/g.bin', 'rb').read()
    for f, n in AG.ACTORS.items():
        e = zstart + ['poke8 %08X 02' % (RECS + 8 * RS), 'poke8 %08X %02X' % (G + 0x55 + 149 // 8, zg[0x55 + 149 // 8] & ~(1 << 149 % 8) & 255),
                      'poke8 %08X %02X' % (RECS + 0x14, zmap[n]), 'poke %08X %08X' % (zpl + 0x1A0, 8 << 8), 'run 3', 'keys LEFT', 'run 20', 'keys', 'run 5']
        for k in range(10): e += ['run 200', 'tap A 20']
        e += ['run 200']
        p3 = zptr(e)
        o = zrun(e + ['shot fly_%s' % n, 'mem %08X 1' % (p3 + 0x58), 'mem 07000000 64', 'keys A'] + ['run 2', 'mem %08X 1' % (p3 + 0x50)] * 30 +
                 ['keys A,LEFT'] + ['run 2', 'mem %08X 1' % (p3 + 0x50)] * 30 + ['keys', 'shot fly_turn_%s' % n,
                 'poke %08X %08X' % (p3 + 0x1A0, 1250 << 8), 'poke %08X %08X' % (p3 + 0x1A4, 1200 << 8), 'run 4', 'tap A 100', 'run 60', 'keys A', 'run 300', 'keys', 'run 100', 'mem 0300197C 1'])
        zrec = int([l for l in o.splitlines() if l.startswith('mem %08x' % (p3 + 0x58))][-1].split()[2], 16) - 0x08000000
        slots = {zu(zrec + 0x54 + 4 * sl): sl for sl in range(zu(zrec) & 0xFF) if zu(zrec + 0x54 + 4 * sl)}
        seen = [slots.get(int(l.split(':')[1].split()[0], 16)) for l in o.splitlines() if l.startswith('mem %08x' % (p3 + 0x50))]
        oam = [int(x, 16) for x in [l for l in o.splitlines() if l.startswith('mem 07000000')][-1].split(':')[1].split()]
        drawn = any((oam[2 * i] >> 8 & 1) and (oam[2 * i] >> 14 & 3, oam[2 * i] >> 30) not in ((0, 0), (1, 0)) and (oam[2 * i] & 255) < 120
                    for i in range(32))          # (the flying figure: scaled, so an affine sprite; not the 8 x 8 arrow nor the 16 x 8 shadow)
        land = int([l for l in o.splitlines() if l.startswith('mem 0300197c')][-1].split(':')[1].split()[0], 16) & 0xFFFF
        check('%s flies over the world map: his figure drawn (%s), flying %s, banking in a turn %s, landing reaches West City (%04X)'
              % (n, drawn, 15 in seen[:30], 16 in seen[30:], land), drawn and 15 in seen[:30] and 16 in seen[30:] and land == (1 << 8 | 4) and 'bad pc' not in o)
print('screens in', OUT)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
