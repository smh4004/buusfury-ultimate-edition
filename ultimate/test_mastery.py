#!/usr/bin/env python3
"""Transformation mastery and what it unlocks (Nov 9), in the Bomber fight of tools/harness/enemy_test.txt (build `--debug --enemy` first).
  python3 ultimate/test_mastery.py [rom] [work dir]
Mastery bytes are outfit.c's MASTERY (the bench's last group): Goku's Super Saiyan is byte 0, his Super Saiyan 3 byte 2, then his
Kamehameha count at byte 21. A tier levels up at MASTERY_L2 (100) and MASTERY_L3 (250), shown as the skill's level; a mastered tier's bar
drains slower (one unit in five skipped at level 2, two at level 3). After the ending, Goku's Super Saiyan 3 at level 3 teaches him Super
Saiyan Blue, and his Kamehameha at level 3 with SUPER_KAME_USES uses the Super Kamehameha."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')); import bench as BN    # the guest bench (lib/bench.py)
R = T.R; G = 0x03001068; forms = T.forms
MASTERY = BN.MASTERY
# a bench of this game's own (magic, generation, and the generation in the game at +0x4F1), so the mastery bytes poked here stay: a fresh
# game has none until something is saved there (outfit.c bench_mine)
BENCH_ON = BN.ON
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(out, addr):
    return [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % addr)]
def poke_mastery(i, v): return BENCH_ON + ['poke8 %08X %02X' % (MASTERY + i, v)]
POST = ['poke8 %08X %02X' % (G + 0x55 + 149 // 8, 1 << 149 % 8)]        # the ending's flag (the byte holds nothing else this early)

def super_saiyan(name, mastery, frames, extra=()):
    L = T.setup([7, 20], None, (0,)) + poke_mastery(0, mastery) + list(extra)
    L += ['poke8 %08X 01' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in T.AWAY + ['run 25']]
    L += ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F), 'mem %08X 26' % R, 'mem %08X 6' % MASTERY]
    L += [v for _ in range(frames // 30) for v in T.AWAY + ['run 30']] + ['mem %08X 26' % R, 'mem %08X 6' % MASTERY]
    o = T.run(L, name)
    return words(o, R), words(o, MASTERY), 'bad pc' in o

# 1. A level: 99 points, then a few seconds as a Super Saiyan; the skill's level follows (record +0x2E + 2 * slot, Super Saiyan in slot 1)
r, m, bad = super_saiyan('level', 99, 600)
lv = r[-1][(0x2E + 2) // 4] >> (8 * ((0x2E + 2) % 4)) & 255
print('   mastery %d -> %d, Super Saiyan level byte %d' % (m[-2][0] & 255, m[-1][0] & 255, lv))
check('mastery grows while transformed and reaches level 2', (m[-1][0] & 255) >= 100 and lv == 1 and not bad)
# 2. A mastered tier drains slower
r0, _, _ = super_saiyan('drain0', 0, 450)
r3, _, _ = super_saiyan('drain3', 250, 450)
d0 = (r0[-2][7] >> 16) - (r0[-1][7] >> 16); d3 = (r3[-2][7] >> 16) - (r3[-1][7] >> 16)
print('   Super Saiyan bar drained: %d unmastered, %d at level 3' % (d0, d3))
check('a mastered Super Saiyan drains about 3/5 as fast', d0 > 6 and 0.45 < d3 / d0 < 0.75)
# 3. Super Saiyan Blue: Goku's Super Saiyan 3 mastered, after the ending
L = T.setup([7, 20], None, (0,)) + POST + poke_mastery(2, 250) + ['run 300', 'mem %08X 26' % R]
o = T.run(L, 'ssb'); rec = words(o, R)[-1]; b = b''.join(w.to_bytes(4, 'little') for w in rec)
print('   Goku skills', list(b[0x0D:0x0D + b[0x0C]]))
check('Super Saiyan Blue comes with Super Saiyan 3 mastered, after the ending', 44 in b[0x0D:0x0D + b[0x0C]] and 'bad pc' not in o)
L = T.setup([7, 20], None, (0,)) + poke_mastery(2, 250) + ['run 300', 'mem %08X 26' % R]
o = T.run(L, 'ssb_story'); b = b''.join(w.to_bytes(4, 'little') for w in words(o, R)[-1])
check('but not during the story', 44 not in b[0x0D:0x0D + b[0x0C]])
# Vegeta (record 4): his Super Saiyan 2 mastered (byte 12) teaches him Super Saiyan Blue after the ending. The party is synced in turn
# (outfit.c player_input), so he needn't be the one fighting; with his six held it waits in his book (+0x22 bit 4: build.py SKILL_BOOK[4])
V = R + 4 * 0x68
def vegeta_blue(extra, name):
    o = T.run(T.setup([7, 20], None, (0,)) + extra + poke_mastery(12, 250) + ['run 600', 'mem %08X 26' % V], name)
    b = b''.join(w.to_bytes(4, 'little') for w in words(o, V)[-1])
    return 44 in b[0x0D:0x0D + b[0x0C]] or b[0x22] >> 4 & 1, list(b[0x0D:0x0D + b[0x0C]]), 'bad pc' in o
got, held, bad = vegeta_blue(POST, 'ssb_vegeta')
print('   Vegeta skills', held)
check('Vegeta: Super Saiyan Blue comes with his Super Saiyan 2 mastered, after the ending', got and not bad)
check('but not during the story', not vegeta_blue([], 'ssb_vegeta_story')[0])
# 4. Super Kamehameha: the Kamehameha at level 3 (Goku's level) and used enough, after the ending
L = T.setup([7, 15], None, (0,)) + POST + ['poke %08X 00FFFFFF' % (R + 0x24)] + poke_mastery(21, 100) + ['run 300', 'mem %08X 26' % R]
o = T.run(L, 'superkame'); b = b''.join(w.to_bytes(4, 'little') for w in words(o, R)[-1])
print('   Goku skills', list(b[0x0D:0x0D + b[0x0C]]))
check('the Super Kamehameha comes with the Kamehameha mastered and used', 43 in b[0x0D:0x0D + b[0x0C]] and 'bad pc' not in o)
k, _, _ = T.fire('kame_l3', [7, 15, 43], 1, level=2)
s, _, b2 = T.fire('superkame_l3', [7, 15, 43], 2, level=2)
print('   Kamehameha %.1f, Super Kamehameha %.1f (both level 3)' % (k, s))
check('the Super Kamehameha hits about 1.4x the Kamehameha', k > 0 and 1.2 < s / k < 1.6 and not b2)
# 5. Kaioken's strength follows its mastery (Goku's Kaioken is byte 5): 1.25x at level 1, 1.75x at level 3
base, _, _ = T.fire('kame_plain', [7, 15, 37], 1)
k1, f1, _ = T.fire('kame_kk1', [7, 15, 37], 1, presses=(0, 2), extra=poke_mastery(5, 0))
k3, f3, b3 = T.fire('kame_kk3', [7, 15, 37], 1, presses=(0, 2), extra=poke_mastery(5, 250))
print('   Kamehameha %.1f; in Kaioken %.1f (level 1), %.1f (level 3)' % (base, k1, k3))
check('Kaioken: about 1.25x at level 1 and 1.75x at level 3', base > 0 and 1.15 < k1 / base < 1.4 and 1.6 < k3 / base < 1.95 and not b3)
# 6. Blue's strength (outfit.c combat_hook): 2x Super Saiyan's, between Super Saiyan 3 (1.75x) and Super Saiyan 4 (2.5x)
ss, f_ss, _ = T.fire('kame_ss', [7, 15, 20, 44], 1, presses=(0, 2))
bl, f_bl, b6 = T.fire('kame_blue', [7, 15, 20, 44], 1, presses=(0, 2, 3))
print('   Kamehameha %.1f as a Super Saiyan (form %d), %.1f in Blue (form %d)' % (ss, f_ss, bl, f_bl))
check('Blue: about 2x Super Saiyan', f_bl in (forms['goku_ssb'], forms['goku_ssb_b']) and ss > 0 and 1.75 < bl / ss < 2.3 and not b6)
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
