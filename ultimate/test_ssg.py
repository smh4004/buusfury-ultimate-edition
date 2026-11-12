#!/usr/bin/env python3
"""Super Saiyan God (Nov 9), in the Bomber fight of tools/harness/enemy_test.txt (build `--debug --enemy` first).
  python3 ultimate/test_ssg.py [rom] [work dir]
Goku learns it after the ending once his Super Saiyan is mastered (mastery byte 0 at 250) and the Battle of Gods is over (more flag
zone26.MORE_BOG_DONE, in the bench's flags2). It powers up from a base form to its red-haired copy (build.py SSG_LOOKS) on that figure,
hits 1.75x as hard, drains at half Super Saiyan's rate, and pressed again goes back to base. No Super Saiyan or Kaioken from it."""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')); import bench as BN    # the guest bench (lib/bench.py)
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'), 'tools/scripts']
import zone26
R, forms = T.R, T.forms
G = 0x03001068
MASTERY = BN.MASTERY
FLAGS2 = BN.FLAGS2                                   # outfit.c struct bench: more flags 32-63
BENCH_ON = BN.ON
POST = ['poke8 %08X %02X' % (G + 0x55 + 149 // 8, 1 << 149 % 8)]
SS_MASTERED = BENCH_ON + ['poke8 %08X FA' % MASTERY]
f = zone26.MORE_BOG_DONE - 32
BOG_DONE = ['poke8 %08X %02X' % (FLAGS2 + (f >> 3), 1 << (f & 7))]
SS, KK, SSG = 20, 37, 46
SS_FULL = ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F)]
GODS = (forms['goku_ssg'], forms['goku_b_ssg'], forms['goku_halo_ssg'])
rom = open(T.ROM, 'rb').read()
u = lambda o: struct.unpack_from('<I', rom, o)[0]
ACTORS_AT = 0x840000
def figure(form):
    return u(ACTORS_AT + 4 * (struct.unpack_from('<H', rom, 0x800000 + 24 * form + 0x0E)[0] - 9))
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(out, addr):
    return [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % addr)]
def held(extra, name):
    o = T.run(T.setup([7, 20], None, (0,)) + list(extra) + ['run 300', 'mem %08X 26' % R], name)
    b = b''.join(w.to_bytes(4, 'little') for w in words(o, R)[-1])
    return list(b[0x0D:0x0D + b[0x0C]]), 'bad pc' in o

# 1. Learning it: after the ending, Super Saiyan mastered, the Battle of Gods over; not with any of them missing
s, bad = held(POST + SS_MASTERED + BOG_DONE, 'learn')
print('   Goku holds', s)
check('Super Saiyan God comes after the Battle of Gods with Super Saiyan mastered', SSG in s and not bad)
check('not before the Battle of Gods is over', SSG not in held(POST + SS_MASTERED, 'learn_nobog')[0])
check('not before Super Saiyan is mastered', SSG not in held(POST + BENCH_ON + BOG_DONE, 'learn_nomastery')[0])

# 2. From base to God and back; its figure while it powers up; nothing else from it
def presses(name, skills, seq, watch=False):
    L = T.setup(skills, None, (0,)) + T.AWAY + ['run 2']
    for k in seq:
        L += ['poke8 %08X %02X' % (R + 0x15, k)] + T.FULL + SS_FULL + ['keys B', 'run 2', 'keys']
        if watch: L += [v for _ in range(8) for v in T.AWAY + ['run 4', 'mem %08X 1' % (T.PLAYER_OBJ + 0x58)]]
        L += [v for _ in range(8) for v in T.AWAY + ['run 30']] + ['mem %08X 1' % (R + 0x14)]
    L += ['shot %s_end' % name]
    o = T.run(L, name)
    return [w[0] & 255 for w in words(o, R + 0x14)], [w[0] for w in words(o, T.PLAYER_OBJ + 0x58)], 'bad pc' in o
fs, figs, bad = presses('god', [7, SS, SSG], (2, 2), watch=True)
print('   forms', fs, 'figures while powering up', [hex(x) for x in figs[:8]])
check('Super Saiyan God from base, and back to base', fs[0] in GODS and fs[1] in (0, 1, 2) and not bad)
check('it powers up on its own red-haired figure', figs[:8] and all(x == figure(fs[0]) for x in figs[1:8]))
fs, _, bad = presses('god_ss', [7, SS, SSG], (2, 1))
check('no Super Saiyan from it', fs[0] in GODS and fs[1] == fs[0] and not bad)
fs, _, bad = presses('god_kk', [7, SSG, KK], (1, 2))
check('no Kaioken from it', fs[0] in GODS and fs[1] == fs[0] and not bad)
fs, _, bad = presses('ss_god', [7, SS, SSG], (1, 2))
check('and none from Super Saiyan', fs[0] in (3, 4) and fs[1] == fs[0] and not bad)

# 3. Its strength: 1.75x a base Kamehameha
b0, f0, _ = T.fire('kame_base', [7, 15, SSG], 1, presses=(0,))
g0, fg, bb = T.fire('kame_god', [7, 15, SSG], 1, presses=(0, 2))
print('   Kamehameha %.1f in base (form %d), %.1f as a God (form %d)' % (b0, f0, g0, fg))
check('Super Saiyan God: about 1.75x base', fg in GODS and b0 > 0 and 1.55 < g0 / b0 < 1.95 and not bb)

# 4. Its drain: half Super Saiyan's, at the same mastery
def drain(name, skills):
    L = T.setup(skills, None, (0,)) + T.AWAY + ['run 2', 'poke8 %08X 02' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys']
    L += [v for _ in range(8) for v in T.AWAY + ['run 30']] + SS_FULL + ['mem %08X 1' % (R + 0x1C)]
    L += [v for _ in range(15) for v in T.AWAY + ['run 30']] + ['mem %08X 1' % (R + 0x1C), 'mem %08X 1' % (R + 0x14)]
    o = T.run(L, name); w = words(o, R + 0x1C)
    return (w[0][0] >> 16) - (w[1][0] >> 16), words(o, R + 0x14)[-1][0] & 255
d_ss, f_ss = drain('drain_ss', [7, 15, SS])
d_god, f_god = drain('drain_god', [7, 15, SSG])
print('   pool drained in 450 frames: %d as a Super Saiyan (form %d), %d as a God (form %d)' % (d_ss, f_ss, d_god, f_god))
check('it drains at about half Super Saiyan\'s rate', f_god in GODS and d_ss > 6 and 0.35 < d_god / d_ss < 0.65)

# 5. The figure: crimson hair, no black hair left
import sprites
def frame0(rec):                                   # the idle frame, front view (a player's frame is one piece)
    a = u(rec + 0x54) - 0x08000000
    return list(sprites.frame_image(rom, u(a + 4)).ravel())
img = frame0(figure(forms['goku_ssg']) - 0x08000000)
src = frame0(u(ACTORS_AT + 4 * 106) - 0x08000000)
print('   black pixels: Goku %d, God %d' % (src.count(1), img.count(1)))
check('his hair is no longer black', src.count(1) > 100 and img.count(1) < 20)
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
