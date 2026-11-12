#!/usr/bin/env python3
"""Kaioken's mastery (Nov 9, second round), in the Bomber fight of tools/harness/enemy_test.txt (build `--debug --enemy` first).
  python3 ultimate/test_kaioken.py [rom] [work dir]
Fully mastered (Goku's Kaioken mastery byte 5 at 250): Kaioken goes on from Super Saiyan too (Super Saiyan Kaioken, back down to Super Saiyan),
costs no health, and brings a bar of its own (0x0203F250, half the fighter's health; cyan over the health bar) that pays its cost and takes the
hits without a stagger; when it runs out the Kaioken ends. Also: Kaioken and Blue power up on their new figure (outfit.c power_to): the player
object's figure (+0x58) during the power-up is the new form's."""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')); import bench as BN    # the guest bench (lib/bench.py)
from PIL import Image
import numpy as np
R, forms = T.R, T.forms
MASTERY = BN.MASTERY
BENCH_ON = BN.ON
MASTERED = BENCH_ON + ['poke8 %08X FA' % (MASTERY + 5)]
GUARD, OBJ = 0x0203F250, T.PLAYER_OBJ
SS, KK, BLUE = 20, 37, 44
SS_FULL = ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F)]      # Super Saiyan's pool full, so it doesn't run dry between presses
rom = open(T.ROM, 'rb').read()
u = lambda o: struct.unpack_from('<I', rom, o)[0]
def figure(f):                    # a form's figure: its row's actor (+0x0E) in the moved actor table
    char = struct.unpack_from('<H', rom, 0x800000 + 24 * f + 0x0E)[0]
    return u(0x840000 + 4 * (char - 9))
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def words(out, addr):
    return [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % addr)]

def kaioken(name, skills, presses, slot, frames, extra=(), near=False, watch_figure=False, after=()):
    """Press skills[slot] (after `presses`), then `frames` with the Bomber kept away (or left beside Goku to fight); every 30 frames read the
    record, the bar and Goku's position (and during the power-up his figure)."""
    L = T.setup(skills, None, presses) + list(extra) + T.AWAY + ['run 2', 'poke8 %08X %02X' % (R + 0x15, slot)] + T.FULL + ['mem %08X 4' % (R + 0x14), 'keys B', 'run 2', 'keys']      # (the first reading: as the press goes in)
    if watch_figure: L += [v for _ in range(8) for v in T.AWAY + ['run 4', 'mem %08X 1' % (OBJ + 0x58)]]
    L += [v for _ in range(240 // 30) for v in T.AWAY + ['run 30']] + list(after)        # the power-up (Kaioken's takes about 160 frames)
    if near:
        o = T.run(L + ['mem %s 2' % T.PX], name + '_pos'); m = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % T.PX, o)[-1]
        stay = ['poke %s %x' % (T.ENEMY_X, int(m[0], 16) - (24 << 8)), 'poke %s %x' % (T.ENEMY_Y, int(m[1], 16))]
        L += stay + ['poke %s %x' % (T.ENEMY_HP, 30000 << 10)]
    look = ['mem %08X 4' % (R + 0x14), 'mem %08X 2' % GUARD, 'mem %s 1' % T.PX]
    L += look
    for _ in range(frames // 30): L += (['run 30'] if near else T.AWAY + ['run 30']) + look
    L += ['shot %s_end' % name]
    o = T.run(L, name)
    rec, guard, px = words(o, R + 0x14), words(o, GUARD), words(o, int(T.PX, 16))
    kaioken.health, kaioken.max, rec = rec[0][0] >> 16, rec[0][1] & 0xFFFF, rec[1:]      # his health and full health as the press goes in
    states = [(r[0] & 255, r[0] >> 16, g[0] & 0xFFFF, g[0] >> 16 & 255, p[0] >> 8) for r, g, p in zip(rec, guard, px)]     # (form, health, bar, bar on, x)
    figs = [w[0] for w in words(o, OBJ + 0x58)] if watch_figure else []
    return states, figs, 'bad pc' in o

# 1. Super Saiyan Kaioken: not before Kaioken is fully mastered; then from Super Saiyan, and pressed again back to Super Saiyan
s, _, bad = kaioken('ss_locked', [7, SS, KK], (0, 1), 2, 60)
check('no Kaioken in Super Saiyan before Kaioken is fully mastered', s[0][0] in (3, 4) and not bad)
for who, base, ss_form, sk in (('Goku', None, None, [7, SS, KK]), ('Kid Goku', forms['kid_goku'], None, [7, SS, KK])):
    L = T.setup(sk, base, (0, 1)) + MASTERED + T.AWAY + ['run 2']
    for k in range(2):
        L += ['poke8 %08X 02' % (R + 0x15)] + T.FULL + SS_FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in T.AWAY + ['run 30']] + ['mem %08X 1' % (R + 0x14)]
    o = T.run(L, 'sskk_' + who.replace(' ', '_'))
    fs = [w[0] & 255 for w in words(o, R + 0x14)]
    want = (forms['goku_ss_kaioken'], forms['goku_ss_b_kaioken']) if base is None else (forms['kid_goku_ssj_kaioken'],)
    print('   %s: Kaioken from Super Saiyan, then again: forms %s' % (who, fs))
    check('%s: Super Saiyan Kaioken once mastered, and back to Super Saiyan' % who, len(fs) == 2 and fs[0] in want and (fs[1] in (3, 4) if base is None else fs[1] == forms['kid_goku_ssj']) and 'bad pc' not in o)
# 2. Mastered: no health cost; the bar pays it, and the Kaioken ends when the bar runs out
s, _, bad = kaioken('kk_bar', [7, SS, KK], (0,), 2, 450, MASTERED)
print('   mastered Kaioken, kept clear of the Bomber: (form, health, bar, on, x) %s ... %s' % (s[0], s[-1]))
check('mastered Kaioken costs no health', s[0][0] == forms['goku_halo_kaioken'] and s[-1][1] == s[0][1] and not bad)
# (half his full health, as kk_start sets it from the record's +0x18. Until the flash save (Nov 12) he always pressed it unhurt, so the
# check read his health; now the Bomber, up some 110 frames sooner, can catch him once before he is kept clear: enemy_test.txt)
print('   health as Kaioken was pressed: %d of %d' % (kaioken.health, kaioken.max))
check('its bar starts at half the health and pays the cost as it goes', s[0][3] == 1 and abs(s[0][2] - kaioken.max // 2) <= 3 and s[-1][2] < s[0][2])
u0, _, _ = kaioken('kk_unmastered', [7, SS, KK], (0,), 2, 450)
check('unmastered Kaioken still costs health, with no bar', u0[0][0] == forms['goku_halo_kaioken'] and u0[-1][1] < u0[0][1] and u0[0][3] == 0)
s, _, bad = kaioken('kk_runs_out', [7, SS, KK], (0,), 2, 300, MASTERED, after=['poke %08X 00010003' % GUARD])     # bar 3, on
print('   bar set to 3: forms %s' % [x[0] for x in s])
check('when the bar runs out the Kaioken ends', s[-1][0] == 2 and not bad)
s, _, bad = kaioken('sskk_runs_out', [7, SS, KK], (0, 1), 2, 300, MASTERED + SS_FULL, after=['poke %08X 00010003' % GUARD] + SS_FULL)
print('   Super Saiyan Kaioken, bar set to 3: forms %s' % [x[0] for x in s])
check('and from Super Saiyan Kaioken it ends in Super Saiyan', s[0][0] in (forms['goku_ss_kaioken'], forms['goku_ss_b_kaioken']) and s[-1][0] in (3, 4) and not bad)
# 3. Hits on a mastered Kaioken (the bar takes them, no stagger): test_guard.py, whose Gunman shoots
# 4. Super Saiyan Kaioken's strength: mastered Kaioken on Super Saiyan's figure, 1.75x Super Saiyan
T.base += MASTERED                               # before the presses: Kaioken from Super Saiyan needs the mastery when pressed
ss, f_ss, _ = T.fire('kame_ss', [7, 15, SS, KK], 1, presses=(0, 2))
kk, f_kk, bb = T.fire('kame_sskk', [7, 15, SS, KK], 1, presses=(0, 2, 3))
del T.base[-len(MASTERED):]
print('   Kamehameha %.1f in Super Saiyan (form %d), %.1f in Super Saiyan Kaioken (form %d)' % (ss, f_ss, kk, f_kk))
check('Super Saiyan Kaioken: about 1.75x Super Saiyan', f_kk in (forms['goku_ss_kaioken'], forms['goku_ss_b_kaioken']) and ss > 0 and 1.55 < kk / ss < 1.95 and not bb)
# 5. Kaioken and Blue power up on their new figure (no Super Saiyan gold while they do)
for name, sk, presses, target in (('kaioken', [7, SS, KK], (0,), 'goku_halo_kaioken'), ('blue', [7, SS, BLUE], (0, 1), 'goku_ssb_b')):
    s, figs, bad = kaioken('fig_' + name, sk, presses, 2, 30, MASTERED if name == 'kaioken' else (), watch_figure=True)
    print('   %s power-up figures %s, %s\'s %x' % (name, [hex(x) for x in figs], target, figure(forms[target])))
    check('%s powers up on its own figure' % name, figs and all(x == figure(forms[target]) for x in figs[1:]) and s[0][0] == forms[target] and not bad)
# 6. The HUD: the bar is drawn cyan over the health bar
img = np.array(Image.open('%s/kk_bar_end.png' % T.D).convert('RGB')).astype(int)[8:16, 38:92]       # the health bar's row
cyan = ((img[..., 2] > 120) & (img[..., 1] > 80) & (img[..., 0] < 100)).sum()
check('the bar shows cyan on the HUD, over the health bar', cyan > 10)
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
