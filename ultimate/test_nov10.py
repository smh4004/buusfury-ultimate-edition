#!/usr/bin/env python3
"""The owner's Nov 10 evening reports that aren't frames (build `--debug --enemy` first; the Gogeta check uses the `--debug` build beside it):
  python3 ultimate/test_nov10.py [enemy rom] [work dir]
1. Fights dropped a frame every 64 (two skills_sync in one frame): the game's frame counter goes up by one every frame of a fight.
2. Super Saiyan 2's ki drained at Super Saiyan's rate ("the SSJ2 ki drain seems to be nonexistent"): it drains about 4x as fast.
3. Super Saiyan 2's mastery trains (Goku's mastery byte 1).
4. The HUD's skill icon shows Super Saiyan 2's icon when Super Saiyan's skill took him there.
5. The Skills tab scrolls to the fifth and sixth skills, and SELECT swaps the sixth.
6. Gogeta stays fused after the ending when picked on Switch Character, his story fusion's time spent (record +8 = 0); one already unfused
   comes back; one not joined yet is left for the reward's join.
7. A Super Saiyan pool above the EP maximum (the HUD's bar loops have no bound: bar pixels landed on the sprite palette, "ssj4 Gogeta has a
   weird green outline" in a capture that had filled the pools first) is drawn within the bar's 41 columns."""
import os, sys, re, struct, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
from PIL import Image
import numpy as np
R = T.R; G = 0x03001068
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(o, a): return [[int(v, 16) for v in l.split(':')[1].split()] for l in o.splitlines() if l.startswith('mem %08x' % a)]

# 1. frames
o = T.run(T.setup([7, 15], None, (0,)) + ['run 100'] + [v for k in range(640) for v in ('run 1', 'mem 03000F94 1')], 'frames')
v = [w[0] for w in words(o, 0x03000F94)]; d = [b - a for a, b in zip(v, v[1:])]
print('   frame counter steps over %d frames: %s' % (len(d), {k: d.count(k) for k in set(d)}))
check('no frame dropped in a fight (the counter goes up by one every frame)', len(d) > 600 and set(d) == {1})

# 2-4. Super Saiyan, then 2 through Super Saiyan's skill: the pool (+0x1E) every second, mastery, the HUD's icon
MASTERY = 0x0203F000 + 20 + 20 * 22
BENCH_ON = ['poke 0203F000 32484342', 'poke 0203F004 00001234', 'poke8 03001559 34', 'poke8 0300155A 12']
L = T.setup([7, 20, 35, 22], None, (0,)) + BENCH_ON + ['poke8 %08X 00' % MASTERY, 'poke8 %08X 00' % (MASTERY + 1)]
def press(): return ['poke8 %08X 01' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in T.AWAY + ['run 25']]
def watch(tag, n): return [v for _ in range(n) for v in T.AWAY + ['run 60', 'mem %08X 1' % (R + 0x14), 'mem %08X 1' % (R + 0x1C)]] + ['shot hud_%s' % tag]
L += press() + watch('ss', 10) + ['mem %08X 1' % MASTERY] + press() + watch('ss2', 10) + ['mem %08X 1' % MASTERY]
o = T.run(L, 'ss2')
forms = [w[0] & 255 for w in words(o, R + 0x14)]; pool = [w[0] >> 16 for w in words(o, R + 0x1C)]
ss = [p for f, p in zip(forms, pool) if f == 4]; ss2 = [p for f, p in zip(forms, pool) if f == 76]
rate = lambda p: (p[1] - p[-1]) / max(len(p) - 2, 1)
print('   pool per second: Super Saiyan %.1f, Super Saiyan 2 %.1f' % (rate(ss), rate(ss2)))
check('Super Saiyan 2 drains its pool about 4x as fast as Super Saiyan', len(ss) > 4 and len(ss2) > 4 and 3 < rate(ss2) / max(rate(ss), 0.1) < 5)
m = [w[0] for w in words(o, MASTERY)]
check('Super Saiyan 2 trains its own mastery (Goku\'s byte 1): %s' % [(x >> 8) & 255 for x in m], len(m) == 2 and (m[1] >> 8 & 255) > (m[0] >> 8 & 255))
D = T.D
icon = lambda t: np.asarray(Image.open('%s/hud_%s.png' % (D, t)).convert('RGB'))[8:24, 12:44].astype(int)
diff = (icon('ss') != icon('ss2')).any(2)
check('the HUD\'s skill icon changes in Super Saiyan 2 (Super Saiyan 2\'s icon with its 2): %d pixels differ' % diff.sum(), diff.sum() > 8)

# 5. Skills tab: down to the third row (skills 5 and 6), right, SELECT
SIX = [7, 15, 19, 20, 22, 35]
L = T.setup(SIX, None, (0,)) + ['run 140', 'tap START 80', 'tap A 60', 'tap DOWN 60', 'tap DOWN 40', 'tap DOWN 40', 'shot tab_down', 'tap RIGHT 40',
                                 'mem %08X 3' % (R + 0x0C), 'tap SELECT 40', 'mem %08X 3' % (R + 0x0C)]
o = T.run(L, 'tab')
held = [list(b''.join(x.to_bytes(4, 'little') for x in w)[1:7]) for w in words(o, R + 0x0C)]
print('   skills before and after SELECT on the sixth:', held)
check('the Skills tab reaches the sixth skill and SELECT swaps it', len(held) == 2 and held[0] == SIX and held[1][:5] == SIX[:5] and held[1][5] != 35)

# 6. Gogeta after the ending (the --debug build: Switch Character opens at the end of its intro). a: joined, his story fusion's time spent
# (+8 = 0): picked, he stays fused. b: a pick in the delivered build unfused him (bit 0 clear) after the reward gave him five skills: he is
# back. c: never joined (a new game's three skills) with his flag set, as between the reward's flag and its join: not put in the party
# (party_join would then skip his form, level and skills).
ROMD = T.ROM.replace('_debug_enemy_', '_debug_')
route = [l for l in open('tools/harness/long.txt').read().split('\n')[:93] if not l.startswith('shot ')]
R7 = 0x03001560 + 7 * 0x68
def gogeta(byte0, timer, nskills, pick):
    h = subprocess.Popen(['tools/harness/harness', ROMD, '/dev/stdin', D], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    def send(*ls):
        for l in ls: h.stdin.write(l + '\n')
        h.stdin.flush()
    def mem(a):
        send('mem %08X 1' % a)
        while True:
            l = h.stdout.readline()
            if not l: sys.exit('harness ended')
            if l.startswith('mem %08x' % a): return int(l.split()[2], 16)
    send('guardon 0x09000000', *route, 'poke8 %08X %02X' % (R7, byte0), 'poke %08X %08X' % (R7 + 8, timer & 0xFFFFFFFF), 'poke8 %08X %02X' % (R7 + 0x0C, nskills))
    for f in (149, 878):                                   # the ending, and the post-game's join of Gogeta (bits set, the rest kept)
        a = G + 0x55 + f // 8; w = mem(a & ~3); send('poke %08X %08X' % (a & ~3, w | 1 << (f % 8 + 8 * (a & 3))))
    send('run 70', 'tap A 60', 'tap A 60', 'run 30', *(['tap RIGHT 40'] * 5 + ['tap A 30'] if pick else []), 'run 600')
    cur, rec = mem(G) & 255, mem(R7) & 255
    send('quit'); h.stdin.close(); h.wait(timeout=60)
    print('   in play %d, Gogeta\'s record byte %02X' % (cur, rec))
    return cur, rec
cur, rec = gogeta(3, 0, 3, True)
check('Gogeta picked after the ending stays fused and in play', cur == 7 and rec & 1)
cur, rec = gogeta(2, 0, 5, False)
check('a Gogeta a pick had unfused is back in the party', rec & 1)
cur, rec = gogeta(2, -1, 3, False)
check('a Gogeta the reward has not joined yet is left for its join', not rec & 1)

# 7. pools at 1023 with an EP maximum of 64: where the HUD starts drawing the bars (0x0800BB8A), the two pool lengths (sp + 0x502, + 0x503) are
# within the 41 columns (they were 0x8F each: 102 columns past the table, three stray bytes a column)
over = ['poke8 %08X 40' % (R + 0x1C), 'poke8 %08X 00' % (R + 0x1D), 'poke8 %08X 40' % (R + 0x1A), 'poke8 %08X 00' % (R + 0x1B)] + \
       ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 03' % (R + 0x1F), 'poke8 %08X FF' % (R + 0x20), 'poke8 %08X 03' % (R + 0x21)]
o = T.run(T.setup([7, 15], None, (0,)) + ['run 100'] + over + ['bp 0800BB8A 120', 'mem r13+0x500 1'], 'bars')
bars = [l for l in o.splitlines() if l.startswith('mem 0300')]
lengths = list(int(bars[-1].split(':')[1].split()[0], 16).to_bytes(4, 'little')) if 'bp 0800bb8a hit' in o and bars else []
print('   bar lengths (health, EP, Super Saiyan pool, Super Saiyan 3 pool): %s' % lengths)
check('a Super Saiyan pool above the EP maximum is drawn within the bar\'s 41 columns', len(lengths) == 4 and max(lengths[2:]) <= 41)

if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
