#!/usr/bin/env python3
"""Perfect guard (Nov 9): R pressed just before an enemy ki blast lands, facing it, sends the blast back and takes no damage.
Needs an enemy rig whose enemy shoots: BFU_RIG_ENEMY="44 137" (a Gunman) BFU_OUT=<dir> python3 ultimate/build.py --debug --enemy
  python3 ultimate/test_guard.py <dir> [work dir]
Drives the emulator live: watches the actor list (0x03001C4C: count +4, pointers from +8) for the enemy blast (vtable 0x0804B454: team
+0x11, position +0x20) and presses R as one closes in."""
import os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='guard'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
sys.argv = [sys.argv[0], ROM, D]
import test_moves as T
R = T.R; PLAYER = 0x03001C34; BLAST_VTS = (0x0804B454, 0x08049F0C)      # an enemy's ki blast; a gunman's shot
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
class H:
    def __init__(self):
        env = dict(os.environ); env.pop('HARNESS_SAV', None)
        self.p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', D], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
        self.bad = False
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
    def blasts(self):
        n = self.mem(0x03001C50)[0]
        out = []
        for p in (self.mem(0x03001C54, n) if n else []):
            w = self.mem(p, 26)
            if w[0] in BLAST_VTS: out.append((p, w))
        return out
    def close(self):
        self.p.stdin.close(); self.p.wait()

def fight(guard, frames=900):
    """-> (health lost, blasts seen, blasts sent back). The enemy (the first in the enemy list, 0x03001BB4) is kept 80 px to the left."""
    h = H(); h.send(*T.setup([7], None, (0,)))
    pl = h.mem(PLAYER)[0]; px, py = h.mem(pl + 0x1A0, 2); e = h.mem(0x03001BB4)[0]
    place = ['poke %08X %x' % (e + 0x1A0, px - (80 << 8)), 'poke %08X %x' % (e + 0x1A4, py)]
    h.send(*(place + ['keys LEFT', 'run 2', 'keys', 'run 2']))
    hp0 = h.mem(R + 0x14)[0] >> 16; seen, back, pressed = set(), set(), {}; ehp0 = h.mem(e + 0x28C)[0]
    for f in range(0, frames, 2):
        h.send(*(place if f % 60 == 0 else []), 'poke8 %08X 02' % (pl + 0x10), 'run 2')      # keep him there, and Goku facing left, towards him
        for p, w in h.blasts():
            seen.add(p)
            if (w[0] == BLAST_VTS[0] and w[0x58 // 4] & 255) or w[0x1C // 4] == pl: back.add(p)
            bx = w[0x20 // 4] >> 8                                  # x in 1/256 px
            if guard and p not in pressed and 0 < (px >> 8) - bx < 26:
                pressed[p] = f; h.send('keys R', 'run 2', 'keys')
    hp1 = h.mem(R + 0x14)[0] >> 16; ehp1 = h.mem(e + 0x28C)[0]
    h.send('shot guard_%d' % guard); h.mem(R); bad = h.bad; h.close()
    return hp0 - hp1, len(seen), len(back), bad, ehp0 - ehp1
lost0, seen0, back0, bad0, hurt0 = fight(False)
print('   no guard: lost %d health to %d blasts' % (lost0, seen0))
lost1, seen1, back1, bad1, hurt1 = fight(True)
print('   perfect guard: lost %d health, %d blasts, %d sent back' % (lost1, seen1, back1))
check('the Gunman shoots, and his blasts hurt', seen0 > 0 and lost0 > 0 and not bad0)
check('a perfect guard sends the blasts back', back1 > 0 and not bad1)
check('and takes less damage than standing there', lost1 < lost0)
print('   the Gunman lost %d health to his own shots (a shot only ever hits the player\'s side: its hit is built with team 0, 0x08027562)' % hurt1)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
