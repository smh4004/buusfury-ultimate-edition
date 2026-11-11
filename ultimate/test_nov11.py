#!/usr/bin/env python3
"""Super Saiyan 3 Goku's Dragon Fist Explosion, played in the emulator (build `--debug` first; no --enemy: a foe's hits mix into the poses):
  python3 ultimate/test_nov11.py [debug rom] [work dir]
Nov 11, the owner: "give ssj3 Goku access to the dragon fist explosion or whatever not the same one ssj4 Goku has but the one from gogeta".
The move is skill 5, Gogeta's; its code shows frames 0-3 of slot 19 by number, which on Goku is Instant Transmission (he vanished and stood
still), so outfit.c dragon_use points it at a pose of its own (slot 29, build.py fist_poses) and dragon_can lets Goku use it only as a
Super Saiyan 3; skills_sync teaches it with Super Saiyan 3 (the 16th and last place in his book).
1. Super Saiyan 3 Goku (forms 5-8, and Kid Goku's): held, the move shows slot 29's frames 0, 1, 2, 3 and then 2 and 3 in turn, never
   Instant Transmission's slot; it costs his Super Saiyan 3 pool; Instant Transmission after it still plays slot 19.
2. Goku in any other form can't use it: no pose, nothing spent.
3. Gogeta's is as it was: slot 19.
4. The book: known once Super Saiyan 3 is known or held (and put in a free slot, as every learned skill), not known without it."""
import json, os, struct, subprocess, sys
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/nov11'; os.makedirs(OUT, exist_ok=True)
rom = open(ROM, 'rb').read(); B = 0x08000000
u = lambda o: struct.unpack_from('<I', rom, o)[0]
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
RECS, RS, G = 0x03001560, 0x68, 0x03001068
POS = {0: 0, 1: 1, 3: 2, 4: 3, 6: 4, 8: 5, 7: 5}
ROUTE = [l for l in open('tools/harness/long.txt').read().split('\n')[:93] if not l.startswith('shot ')]
LIST = u(0x3C0) - B - 4
BOOK_SS3, BOOK_FIST = 6, 15                      # where Super Saiyan 3 (22) and the Dragon Fist Explosion (5) are in Goku's book (build.py SKILL_BOOK)
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def slots(form):
    a = struct.unpack_from('<H', rom, 0x800000 + 24 * form + 0x0E)[0] - 9; rec = u(LIST + 4 * a) - B
    return {u(rec + 0x54 + 4 * s): s for s in range(rom[rec]) if u(rec + 0x54 + 4 * s)}

class Game:
    """The --debug build at Switch Character, wearing `form` (its owner's record; a guest's in the guest slot), holding `skills`."""
    def __init__(self, form, skills):
        self.c = c = rom[0x800000 + 24 * form + 0x0C] if rom[0x800000 + 24 * form + 0x0C] in POS else 8
        self.R = R = RECS + c * RS; self.bad = False
        self.p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', OUT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.POOLS = ['poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D), 'poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 03' % (R + 0x1F),
                      'poke8 %08X FF' % (R + 0x20), 'poke8 %08X 03' % (R + 0x21)]          # the EP maximum first (a pool above it is never asked for)
        self.FULL = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B)] + self.POOLS
        self.send('guardon 0x09000000', *ROUTE)
        if c == 7: self.send('poke8 %08X 03' % R)
        self.send('tap A 60', 'tap A 60', 'run 30', *['tap RIGHT 40'] * POS[c], *self.POOLS, 'poke8 %08X %02X' % (R + 0x14, form), 'run 4', 'tap A 200', *self.POOLS, 'run 60')
        self.hold(skills); self.send('run 30')
        self.worn = (self.mem(R + 0x14)[0] & 255) == form and (self.mem(G)[0] & 255) == c
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
    def hold(self, skills):
        self.send('poke8 %08X %02X' % (self.R + 0x0C, len(skills)), *['poke8 %08X %02X' % (self.R + 0x0D + i, s) for i, s in enumerate(skills)])
    def held(self):
        b = b''.join(x.to_bytes(4, 'little') for x in self.mem(self.R + 0x0C, 2)); return list(b[1:1 + b[0]])
    def known(self): return self.mem(self.R + 0x20)[0] >> 16
    def set_known(self, v): self.send('poke8 %08X %02X' % (self.R + 0x22, v & 255), 'poke8 %08X %02X' % (self.R + 0x23, v >> 8))
    def pose(self):
        po = self.mem(0x03001C34)[0]; an = self.mem(po + 0x50)[0]; w = self.mem(po + 0x10)[0]; f = self.mem(self.R + 0x14)[0] & 255
        return slots(f).get(an), w >> 8 & 255
    def use(self, slot, frames=60, key='LEFT', shot=None):
        """Face `key`, hold B on the skill in `slot` for `frames` and let go; -> the (animation slot, frame) shown every 2 frames, and what it cost
        (EP, the Super Saiyan pool, the Super Saiyan 3 pool)."""
        self.send('keys %s' % key, 'run 2', 'keys', 'run 10', 'poke8 %08X %02X' % (self.R + 0x15, slot), *self.FULL, 'run 1')
        before = [self.mem(self.R + o)[0] & 0xFFFF for o in (0x1A, 0x1E, 0x20)]
        self.send('keys B'); seen = []
        for i in range(frames // 2):
            self.send('run 2'); seen.append(self.pose())
            if shot and i == frames // 4: self.send('shot %s' % shot)
        after = [self.mem(self.R + o)[0] & 0xFFFF for o in (0x1A, 0x1E, 0x20)]
        self.send('keys', 'run 160')
        return seen, [b - a for b, a in zip(before, after)]
    def close(self):
        self.p.stdin.close(); self.p.wait()

def run_of(seen):                                    # the poses in order, repeats folded
    out = []
    for s in seen:
        if not out or out[-1] != s: out.append(s)
    return out

# 1. Super Saiyan 3 Goku: every form of his that is one (the adult's two outfits, with and without the halo; Kid Goku's)
SS3 = [(5, 'Super Saiyan 3 Goku'), (6, 'Super Saiyan 3 Goku (second outfit)'), (7, 'Super Saiyan 3 Goku (form 7)'), (8, 'Super Saiyan 3 Goku (form 8)'),
       (forms['kid_goku_ssj3'], 'Super Saiyan 3 Kid Goku')]
for f, label in SS3:
    for key in ('LEFT', 'DOWN') if f == 5 else ('LEFT',):
        g = Game(f, [5, 14, 7]); seen, cost = g.use(0, key=key, shot='fist_%d_%s' % (f, key)); it, _ = g.use(1, 30); bad = g.bad; g.close()
        r = run_of(seen); fr = [x[1] for x in r if x[0] == 29]
        print('   form %d facing %s: worn %s, poses %s, cost (EP, SS, SS3) %s; then Instant Transmission %s' % (f, key.lower(), g.worn, r[:10], cost, run_of(it)[:5]))
        check('%s holds the Dragon Fist Explosion in its own pose facing %s (slot 29: 0, 1, 2, 3, then 2 and 3 in turn), not Instant Transmission\'s' % (label, key.lower()),
              g.worn and not bad and fr[:4] == [0, 1, 2, 3] and len(fr) >= 6 and set(fr[4:]) <= {2, 3} and not any(x[0] == 19 for x in r))
        check('%s pays for it from his Super Saiyan 3 pool: %s' % (label, cost), cost[0] == 0 and cost[1] == 0 and cost[2] >= 150)
        if f == 5 and key == 'LEFT':
            check('Instant Transmission still plays its own slot after it', any(x[0] == 19 for x in it) and not any(x[0] == 29 for x in it))

# 2. any other Goku: nothing happens, nothing is spent
for f, label in ((0, 'Goku'), (3, 'Super Saiyan Goku'), (forms['kid_goku'], 'Kid Goku'), (forms['kid_goku_ssj4'], 'Super Saiyan 4 Kid Goku')):
    g = Game(f, [5, 7]); seen, cost = g.use(0); bad = g.bad; g.close()
    r = run_of(seen)
    print('   form %d: worn %s, poses %s, cost %s' % (f, g.worn, r[:6], cost))
    # (a Super Saiyan form's own pool drains a little over the second the button is held: the move would cost 300 and more)
    check('%s can\'t use the Dragon Fist Explosion (no pose, nothing spent)' % label, g.worn and not bad and not any(x[0] in (19, 29) for x in r) and cost[0] == 0 and max(cost) < 40)

# 3. Gogeta's
g = Game(41, [5, 7]); seen, cost = g.use(0, shot='fist_gogeta'); bad = g.bad; g.close()
r = run_of(seen); fr = [x[1] for x in r if x[0] == 19]
print('   Gogeta: worn %s, poses %s, cost %s' % (g.worn, r[:10], cost))
check('Gogeta\'s Dragon Fist Explosion is as it was (slot 19: 0, 1, 2, 3, then 2 and 3)', g.worn and not bad and fr[:4] == [0, 1, 2, 3] and set(fr[4:]) <= {2, 3} and not any(x[0] == 29 for x in r))

# 4. the book (skills_sync runs for the fighter on screen every 64 frames)
g = Game(0, [7, 15]); g.set_known(0); g.send('run 140')
k0, h0 = g.known(), g.held()
g.hold([7, 15, 22]); g.send('run 140'); k1, h1 = g.known(), g.held()
g.hold([7, 15, 14, 20, 35, 22]); g.set_known(0); g.send('run 140'); k2, h2 = g.known(), g.held()
g.hold([7, 15]); g.set_known(1 << BOOK_FIST); g.send('run 140'); k3, h3 = g.known(), g.held()
bad = g.bad; g.close()
print('   known bits / held: without Super Saiyan 3 %04x %s; holding it %04x %s; six held %04x %s; a stale bit %04x %s' % (k0, h0, k1, h1, k2, h2, k3, h3))
check('Goku without Super Saiyan 3 doesn\'t know the Dragon Fist Explosion (Kaioken is learned as ever)', not bad and not k0 >> BOOK_FIST & 1 and 5 not in h0 and h0[:2] == [7, 15])
check('holding Super Saiyan 3, he learns it, into a free slot', k1 >> BOOK_FIST & 1 == 1 and h1[:3] == [7, 15, 22] and 5 in h1)
check('with six skills held it is known (SELECT swaps it in) and no slot changes', k2 >> BOOK_FIST & 1 == 1 and h2 == [7, 15, 14, 20, 35, 22])
check('a known bit with no Super Saiyan 3 (the shelved Great Ape\'s place in a Nov 9 save) is cleared', not k3 >> BOOK_FIST & 1 and h3[:2] == [7, 15] and 5 not in h3)

if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
