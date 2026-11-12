#!/usr/bin/env python3
"""Full Power (Nov 9, the owner: "add a full power Mystic form for Mystic Gohan only don't allow any of his other forms to use it"), in the
Bomber fight of tools/harness/enemy_test.txt (build `--debug --enemy` first).
  python3 ultimate/test_fp.py [rom] [work dir]
Gohan learns it with the orange gi (outfit flag build.py MYSTIC_FLAG). It powers up from the orange gi (form 13) to its own form (build.py
FP_LOOKS: the orange gi's figure) with white lightning crackling around him (outfit.c crackle), hits 1.75x as hard, drains at half Super
Saiyan's rate, and pressed again goes back to the orange gi. No Super Saiyan from it, and none of his other forms has it (test_tiers.py)."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'), 'tools/scripts']
R, forms = T.R, T.forms
G = 0x03001068
GOHAN = R + 0x68                                    # the party's records, 0x68 bytes each: Gohan is the second
MYSTIC_FLAG, FP = 860, 47
MYSTIC = ['poke8 %08X %02X' % (G + 0x55 + MYSTIC_FLAG // 8, 1 << MYSTIC_FLAG % 8)]
SS = 20
SS_FULL = ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F)]
ORANGE, FPF = 13, forms['gohan_mystic_fp']
rom = open(T.ROM, 'rb').read()
u = lambda o: struct.unpack_from('<I', rom, o)[0]
ACTORS_AT = struct.unpack_from('<I', rom, 0x3C0)[0] - 0x08000000 - 4      # the actor table (build.py ACTORS_AT; the game's code reads it from this literal)
def figure(form):
    return u(ACTORS_AT + 4 * (struct.unpack_from('<H', rom, 0x800000 + 24 * form + 0x0E)[0] - 9))
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(out, addr):
    return [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % addr)]

# 1. Learning it: with the orange gi; not before. Gohan's record is synced every 512 frames (outfit.c: the party in turn). The rig's save
# has the orange gi already (flags 858-860 in one byte: 0x1C), so each run first takes it and the skill away, then (or not) gives the gi back
FLAG_AT = G + 0x55 + MYSTIC_FLAG // 8
FORGET = ['mem %08X 1' % FLAG_AT, 'poke8 %08X 0C' % FLAG_AT, 'poke8 %08X 00' % (GOHAN + 0x23)]
def gohan(extra, name):
    o = T.run(T.setup([7, 20], None, (0,)) + FORGET + ['mem %08X 26' % GOHAN] + list(extra) + ['run 1100', 'mem %08X 26' % GOHAN], name)
    check('(the rig has the orange gi: flag byte 0x1C)', words(o, FLAG_AT)[0][0] & 0xFF == 0x1C)
    rs = [b''.join(w.to_bytes(4, 'little') for w in ws) for ws in words(o, GOHAN)]
    held = lambda b: list(b[0x0D:0x0D + b[0x0C]])
    known = lambda b: struct.unpack_from('<H', b, 0x22)[0] >> 8 & 1       # FP is ninth in Gohan's book (build.py SKILL_BOOK)
    return held(rs[0]), held(rs[-1]), known(rs[-1]), 'bad pc' in o
h0, h1, k1, bad = gohan(MYSTIC, 'learn')
print('   Gohan holds', h0, 'then', h1, 'known', k1)
check('Full Power comes with the orange gi', (FP in h1 or k1) and FP not in h0 and not bad)
h0, h1, k1, bad = gohan([], 'learn_not')
check('not before', FP not in h1 and not k1 and not bad)

# 2. From the orange gi to Full Power and back; its figure while it powers up; no Super Saiyan from it
def presses(name, skills, seq, watch=False):
    L = T.setup(skills, ORANGE, (0,)) + T.AWAY + ['run 2']
    for k in seq:
        L += ['poke8 %08X %02X' % (R + 0x15, k)] + T.FULL + SS_FULL + ['keys B', 'run 2', 'keys']
        if watch: L += [v for _ in range(8) for v in T.AWAY + ['run 4', 'mem %08X 1' % (T.PLAYER_OBJ + 0x58)]]
        L += [v for _ in range(8) for v in T.AWAY + ['run 30']] + ['mem %08X 1' % (R + 0x14)]
    L += ['shot %s_end' % name]
    o = T.run(L, name)
    return [w[0] & 255 for w in words(o, R + 0x14)], [w[0] for w in words(o, T.PLAYER_OBJ + 0x58)], 'bad pc' in o
fs, figs, bad = presses('fp', [7, SS, FP], (2, 2), watch=True)
print('   forms', fs, 'figures while powering up', [hex(x) for x in figs[:8]])
check('Full Power from the orange gi, and back to it', fs[0] == FPF and fs[1] == ORANGE and not bad)
check('it powers up on its own figure', figs[:8] and all(x == figure(FPF) for x in figs[1:8]))
fs, _, bad = presses('fp_ss', [7, SS, FP], (2, 1))
check('no Super Saiyan from it', fs == [FPF, FPF] and not bad)
fs, _, bad = presses('ss_fp', [7, SS, FP], (1, 2))
check('and none from his Super Saiyan', fs == [forms['gohan_orange_ss']] * 2 and not bad)

# 3. Its strength: 1.75x a Kamehameha in the orange gi
b0, f0, _ = T.fire('kame_orange', [7, 15, FP], 1, form=ORANGE, presses=(0,))
g0, fg, bb = T.fire('kame_fp', [7, 15, FP], 1, form=ORANGE, presses=(0, 2))
print('   Kamehameha %.1f in the orange gi (form %d), %.1f at Full Power (form %d)' % (b0, f0, g0, fg))
check('Full Power: about 1.75x the orange gi', fg == FPF and f0 == ORANGE and b0 > 0 and 1.55 < g0 / b0 < 1.95 and not bb)

# 4. Its drain: half Super Saiyan's
def drain(name, skills):
    L = T.setup(skills, ORANGE, (0,)) + T.AWAY + ['run 2', 'poke8 %08X 02' % (R + 0x15)] + T.FULL + ['keys B', 'run 2', 'keys']
    L += [v for _ in range(8) for v in T.AWAY + ['run 30']] + SS_FULL + ['mem %08X 1' % (R + 0x1C)]
    L += [v for _ in range(15) for v in T.AWAY + ['run 30']] + ['mem %08X 1' % (R + 0x1C), 'mem %08X 1' % (R + 0x14)]
    o = T.run(L, name); w = words(o, R + 0x1C)
    return (w[0][0] >> 16) - (w[1][0] >> 16), words(o, R + 0x14)[-1][0] & 255
d_ss, f_ss = drain('drain_ss', [7, 15, SS])
d_fp, f_fp = drain('drain_fp', [7, 15, FP])
print('   pool drained in 450 frames: %d as a Super Saiyan (form %d), %d at Full Power (form %d)' % (d_ss, f_ss, d_fp, f_fp))
check('it drains at about half Super Saiyan\'s rate', f_ss == forms['gohan_orange_ss'] and f_fp == FPF and d_ss > 6 and 0.35 < d_fp / d_ss < 0.65)

# 5. The lightning is all animated (Nov 9, the owner: "make the entire thing animated ... all or nothing"): the figure is the orange gi's own
# frames, and the crackle (outfit.c crackle) strikes a bolt every 7-13 frames in Full Power and Super Saiyan 2, never in a base form.
# Each strike moves its next time on (BOLT_NEXT): the distinct values seen over 120 frames count the strikes.
check('Full Power\'s figure is the orange gi\'s frames', figure(FPF) != figure(ORANGE) and u(figure(FPF) - 0x08000000 + 0x54) == u(figure(ORANGE) - 0x08000000 + 0x54))
BOLT_NEXT = 0x0203F26C
def strikes(name, skills, form, seq):
    L = T.setup(skills, form, (0,)) + T.AWAY + ['run 2']
    for k in seq:
        L += ['poke8 %08X %02X' % (R + 0x15, k)] + T.FULL + SS_FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in T.AWAY + ['run 30']]
    L += [v for _ in range(24) for v in T.AWAY + ['run 5', 'mem %08X 1' % BOLT_NEXT]] + ['mem %08X 1' % (R + 0x14), 'shot %s' % name]
    o = T.run(L, name)
    return len(set(w[0] for w in words(o, BOLT_NEXT))), words(o, R + 0x14)[-1][0] & 255
n_fp, f1 = strikes('crackle_fp', [7, SS, FP], ORANGE, (2,))
n_ss2, f2 = strikes('crackle_ss2', [7, SS, 15], 0, (1, 1))
n_base, f3 = strikes('crackle_base', [7, SS, FP], ORANGE, ())
print('   strikes in 120 frames: Full Power %d (form %d), Super Saiyan 2 %d (form %d), the orange gi %d (form %d)' % (n_fp, f1, n_ss2, f2, n_base, f3))
check('the crackle strikes in Full Power and Super Saiyan 2, about every 10 frames', f1 == FPF and f2 in (forms['goku_ss2'], forms['goku_ss2_b']) and 8 <= n_fp <= 20 and 8 <= n_ss2 <= 20)
check('and never in a base form', f3 == ORANGE and n_base <= 1)
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
