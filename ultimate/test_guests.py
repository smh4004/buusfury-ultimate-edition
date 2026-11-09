#!/usr/bin/env python3
"""The human guests' Nov 9 moves (build `--debug --enemy` first): Kaioken for Krillin, Tien, Yamcha, Videl and Hercule, and Solar Flare
(Krillin, Tien) in the Bomber fight of tools/harness/enemy_test.txt.
  python3 ultimate/test_guests.py [rom] [work dir]
Solar Flare: the white flash, the Bomber stunned (the game's state 1 on its state stack, 0x0870F51C) and held still for its 150 frames,
then fighting again; the cost taken; and not usable twice at once."""
import json, os, re, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
D = T.D; forms = T.forms; R = T.R
E0 = 0x0202D2CC                                   # the Bomber (its x at +0x1A0 is test_moves' ENEMY_X)
STUN_DESC = 0x0870F51C
KK, SOLAR = 37, 42
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(out, addr):
    return [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % addr)]

# Kaioken on each human guest's figure: the form changes to its red copy, health drains, a second press stops it.
for who in ('krillin', 'tien', 'yamcha', 'videl', 'hercule'):
    L = T.setup([7, KK], forms[who], (0,)) + ['mem %08X 2' % (R + 0x14)]
    L += ['poke8 %08X 01' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(12) for v in T.AWAY + ['run 25']]
    L += ['shot kk_%s' % who, 'mem %08X 2' % (R + 0x14)]
    L += ['poke8 %08X 01' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in T.AWAY + ['run 25']] + ['mem %08X 2' % (R + 0x14)]
    o = T.run(L, 'kk_' + who)
    w = words(o, R + 0x14)
    fs = [x[0] & 255 for x in w]; hp = [x[0] >> 16 for x in w]
    print('   %s: forms %s, health %s' % (who, fs, hp))
    check('%s: Kaioken, its health cost, and off again' % who, len(fs) == 3 and fs[0] == forms[who] and fs[1] == forms[who + '_kaioken'] and hp[1] < hp[0] and fs[2] == forms[who] and 'bad pc' not in o)

# Solar Flare: Krillin's figure, the Bomber 50 px away.
o = T.run(T.setup([7, SOLAR], forms['krillin'], (0,)) + ['run 4', 'mem %s 2' % T.PX], 's0'); m = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % T.PX, o)[-1]
near = ['poke %s %x' % (T.ENEMY_X, int(m[0], 16) - (50 << 8)), 'poke %s %x' % (T.ENEMY_Y, int(m[1], 16))]
L = T.setup([7, SOLAR], forms['krillin'], (0,)) + ['run 4'] + near + ['run 2', 'mem %08X 1' % (R + 0x1A)]
L += ['poke8 %08X 01' % (R + 0x15)] + T.FULL + ['poke8 %08X 00' % (R + 0x1A), 'poke8 %08X 02' % (R + 0x1B), 'mem %08X 1' % (R + 0x1A), 'keys B', 'run 2', 'keys', 'run 4', 'shot solar_flash', 'mem 05000000 1', 'mem %08X 1' % (R + 0x1A)]
L += ['keys B', 'run 2', 'keys', 'mem %08X 1' % (R + 0x1A)]          # again at once: not usable while the first runs
for k in range(10):
    L += ['run 20', 'mem %08X 1' % (E0 + 0x1A0), 'mem %08X 6' % (E0 + 0x23C)] + (['shot solar_%d' % k] if k in (0, 4, 9) else [])
o = T.run(L, 'solar')
ep = [x[0] & 0xFFFF for x in words(o, R + 0x1A)]
xs = [x[0] for x in words(o, E0 + 0x1A0)]
stack = words(o, E0 + 0x23C)
top = [s[2 * s[0]] if 1 <= s[0] <= 2 else 0 for s in stack]   # {depth, then (state, descriptor) pairs}
print('   ki %s; Bomber x %s; top state %s' % (ep, [x >> 8 for x in xs], [hex(t) for t in top]))
shot = np.array(Image.open('%s/solar_flash.png' % D).convert('RGB')).astype(int)
check('Solar Flare: the screen flashes white', shot.mean() > 170)
check('Solar Flare costs its ki, once', len(ep) == 4 and ep[1] - ep[2] == 40 and ep[3] == ep[2])
stunned = [t == STUN_DESC for t in top]
check('Solar Flare stuns the Bomber for about 150 frames', all(stunned[:7]) and not stunned[-1])
check('the stunned Bomber stays put', len(set(xs[:7])) == 1)
check('the Bomber fights again afterwards', not stunned[-1] and 'bad pc' not in o)
# Master Roshi (guest): Krillin's fighting frames with his head and clothes. Every move, then Max Power: his form goes up, hits 1.5x.
if 'roshi' in forms:
    k0, f0, b0 = T.fire('roshi_kame', [7, 8, 15, 45], 2, forms['roshi'], (0,))
    k1, f1, b1 = T.fire('roshi_kame_max', [7, 8, 15, 45], 2, forms['roshi'], (0, 3))
    print('   Roshi: Kamehameha %.1f (form %d), in Max Power %.1f (form %d)' % (k0, f0, k1, f1))
    check('Roshi fires the Kamehameha', k0 > 0 and f0 == forms['roshi'] and not b0)
    check('Max Power: his form goes up and the Kamehameha hits harder (Super Saiyan\'s stat boost, then 1.5x)', f1 == forms['roshi_max'] and 1.6 < k1 / k0 < 2.2 and not b1)
    # his figure from the start: the form set during the intro, before the field loads the player's actor
    k = [i for i, l in enumerate(T.base) if l == 'tap A 100'][20]
    T.base[k:k] = ['poke8 %08X %02X' % (R + 0x14, forms['roshi'])]
    L = T.setup([7, 8, 15, 45], forms['roshi'], (0,)) + ['keys RIGHT', 'run 20', 'shot roshi_walk', 'keys', 'run 4']
    for i_ in range(3):
        L += ['poke8 %08X %02X' % (R + 0x15, i_)] + T.FULL + ['keys B', 'run 12', 'shot roshi_move%d' % i_, 'run 48', 'keys'] + [v for _ in range(6) for v in T.AWAY + ['run 25']]
    L += ['tap A 10', 'shot roshi_punch', 'run 40', 'mem %08X 1' % (R + 0x14)]
    o = T.run(L, 'roshi')
    del T.base[k]
    check('Roshi uses every move and punches with no bad jumps', 'bad pc' not in o)
sheet = [np.array(Image.open('%s/%s.png' % (D, n)).convert('RGB')) for n in ['solar_flash', 'solar_0', 'solar_4', 'solar_9'] + ['kk_' + w for w in ('krillin', 'tien', 'yamcha', 'videl', 'hercule')]]
Image.fromarray(np.concatenate([np.concatenate(sheet[:4], 1), np.concatenate(sheet[4:] + [np.zeros_like(sheet[0])] * 3, 1)[:, :240 * 4]], 0)).save(D + '/guests.png')
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
