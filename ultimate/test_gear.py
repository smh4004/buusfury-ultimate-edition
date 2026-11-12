#!/usr/bin/env python3
"""The post-game gear's effects (Nov 9; build.py GEAR, outfit.c), each against the same fight without it, in the Bomber fight of
tools/harness/enemy_test.txt (build `--debug --enemy` first).
  python3 ultimate/test_gear.py [rom] [work dir]
Potara Earrings: Super Saiyan's bar drains a third slower. Gravity Band: mastery grows twice as fast. King Kai's Shades: the Kaioken
costs half the health. Senzu Pouch: health comes back during a fight. The gear is put on by writing the record's slots (+0x3C body,
+0x40 hands, +0x44 feet, +0x48 accessory)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')); import bench as BN    # the guest bench (lib/bench.py)
R = T.R; forms = T.forms
POTARA, GRAVITY, SHADES, SHELL, POUCH = 162, 163, 164, 165, 166
MASTERY = BN.MASTERY                        # outfit.c MASTERY
# a bench of this game's own (magic, generation, and the generation in the game at +0x4F1), so the mastery bytes poked here stay: a fresh
# game has none until something is saved there (outfit.c bench_mine)
BENCH_ON = BN.ON
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(out, addr):
    return [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % addr)]
def wear(slot_off, row): return ['poke %08X %08X' % (R + slot_off, row)]

def transformed(name, skill, gear, frames, extra=()):
    """Goku with Super Saiyan (20) or Kaioken (37) on, wearing `gear` [(offset, row)]; -> record words at the start and after `frames`."""
    L = T.setup([7, skill], None, (0,)) + BENCH_ON + [v for o, r in gear for v in wear(o, r)] + list(extra)
    L += ['poke8 %08X 01' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in T.AWAY + ['run 25']]
    L += ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F), 'mem %08X 12' % R, 'mem %08X 6' % MASTERY]
    L += [v for _ in range(frames // 30) for v in T.AWAY + ['run 30']] + ['mem %08X 12' % R, 'mem %08X 6' % MASTERY]
    o = T.run(L, name)
    r = words(o, R); m = words(o, MASTERY)
    return r[-2], r[-1], m[-2], m[-1], 'bad pc' in o

# Potara: Super Saiyan's pool (+0x1E) over 450 frames
a0, a1, _, _, b0 = transformed('ss_plain', 20, [], 450)
p0, p1, _, _, b1 = transformed('ss_potara', 20, [(0x48, POTARA)], 450)
plain = (a0[7] >> 16) - (a1[7] >> 16); potara = (p0[7] >> 16) - (p1[7] >> 16)       # +0x1E: the high half of word 7
print('   Super Saiyan bar drained: %d plain, %d with the Potara Earrings' % (plain, potara))
check('Potara Earrings: the bar drains about a third slower', plain > 6 and 0.55 < potara / plain < 0.8 and not b0 and not b1)
# Gravity Band: Goku's Super Saiyan mastery (MASTERY[0]) over 1200 frames
_, _, m0, m1, b0 = transformed('mastery_plain', 20, [], 1200)
_, _, g0, g1, b1 = transformed('mastery_gravity', 20, [(0x40, GRAVITY)], 1200)
plain = (m1[0] & 255) - (m0[0] & 255); grav = (g1[0] & 255) - (g0[0] & 255)
print('   Super Saiyan mastery gained: %d plain, %d with the Gravity Band' % (plain, grav))
check('Gravity Band: mastery grows about twice as fast', plain >= 2 and 1.6 <= grav / plain <= 2.5 and not b0 and not b1)
# King Kai's Shades: Kaioken's health cost (+0x16) over 450 frames
k0, k1, _, _, b0 = transformed('kk_plain', 37, [], 450)
s0, s1, _, _, b1 = transformed('kk_shades', 37, [(0x48, SHADES)], 450)
plain = (k0[5] >> 16) - (k1[5] >> 16); shades = (s0[5] >> 16) - (s1[5] >> 16)
print("   Kaioken health spent: %d plain, %d with King Kai's Shades" % (plain, shades))
check("King Kai's Shades: the Kaioken costs about half the health", plain > 4 and 0.35 < shades / plain < 0.65 and not b0 and not b1)
# Senzu Pouch: half health, 720 frames of the fight with the Bomber kept away
def regen(name, gear):
    L = T.setup([7], None, (0,)) + [v for o, r in gear for v in wear(o, r)]
    L += ['run 2', 'mem %08X 12' % R]
    o = T.run(L, name + '0'); hp_max = words(o, R)[-1][6] & 0xFFFF
    L += ['poke8 %08X %02X' % (R + 0x16, (hp_max // 2) & 255), 'poke8 %08X %02X' % (R + 0x17, (hp_max // 2) >> 8), 'mem %08X 12' % R] + [v for _ in range(24) for v in T.AWAY + ['run 30']] + ['mem %08X 12' % R]
    o = T.run(L, name); r = words(o, R)
    return (r[-2][5] >> 16), (r[-1][5] >> 16), hp_max, 'bad pc' in o
h0, h1, mx, b0 = regen('pouch_plain', [])
q0, q1, _, b1 = regen('pouch', [(0x48, POUCH)])
print('   health over 720 frames: %d -> %d plain, %d -> %d with the Senzu Pouch (max %d)' % (h0, h1, q0, q1, mx))
check('Senzu Pouch: health comes back in a fight', q1 - q0 >= 5 * max(1, mx // 100) and q1 - q0 > h1 - h0 and not b1)
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
