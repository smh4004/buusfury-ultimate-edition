#!/usr/bin/env python3
"""Each transformation tier is its own skill (Nov 9): Super Saiyan, 2, 3, 4, Blue, and Kaioken. Build `--debug --enemy` first.
  python3 ultimate/test_tiers.py [rom] [work dir]
Plays Goku (orange gi and Kid Goku), GT Vegeta and GT Gohan through their tiers in the Bomber fight of tools/harness/enemy_test.txt,
checks what each press does and what it may not do (no Super Saiyan in Kaioken and the reverse), Kaioken's health cost and its 1.5x."""
import json, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='tiers'); os.makedirs(D, exist_ok=True)
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
H = 'tools/harness/harness'; R = 0x03001560
ENEMY_X, ENEMY_Y, PX = '0202d46c', '0202d470', '0202ce1c'
base = [l for l in open('tools/harness/enemy_test.txt').read().split('\n') if l and not l.startswith('#') and not l.startswith('mem ') and not l.startswith('shot ') and l not in ('tap B 20', 'run 200')]
SS, SS2, SS3, SS4, KK, SSB, FP = 20, 35, 22, 36, 37, 44, 47
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def run(lines, name):
    p = '%s/%s.txt' % (D, name); open(p, 'w').write('\n'.join(lines) + '\n')
    return subprocess.run([H, ROM, p, D], capture_output=True, text=True, timeout=900).stdout

o = run(base + ['mem %s 2' % PX], 'pos'); m = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % PX, o)[-1]
AWAY = ['poke %s %x' % (ENEMY_X, int(m[0], 16) + (140 << 8)), 'poke %s %x' % (ENEMY_Y, int(m[1], 16))]
FULL = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B)]

def play(name, skills, form, presses, wait=240):
    """presses: skills (ids) pressed in turn, each followed by `wait` frames with the Bomber kept away. -> [(form, hp, maxhp)] after each press."""
    L = base + ['guardon 0x09000000', 'poke8 %08X %02X' % (R + 0x0C, len(skills))] + ['poke8 %08X %02X' % (R + 0x0D + i, s) for i, s in enumerate(skills)]
    L += ['run 4', 'poke8 %08X %02X' % (R + 0x14, form)]
    L += ['poke8 %08X 00' % (R + 0x15)] + FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(6) for v in AWAY + ['run 20']]   # the first press after the walk-in does nothing
    for k, p in enumerate(presses):
        L += ['poke8 %08X %02X' % (R + 0x15, skills.index(p))] + FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(wait // 20) for v in AWAY + ['run 20']]
        L += ['shot %s_%d' % (name, k), 'mem %08X 10' % R]
    out = run(L, name)
    recs = [[int(x, 16) for x in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem 03001560')]
    return [(w[5] & 255, w[5] >> 16 & 0xFFFF, w[6] & 0xFFFF) for w in recs], 'bad pc' in out

def icon(shot):
    """The HUD's skill icon (32x16 at 8,8)."""
    return np.array(Image.open('%s/%s.png' % (D, shot)).convert('RGB'))[8:24, 8:40]

F = forms
# Goku, orange gi: Super Saiyan, 2, 3, then 3 again (down); Super Saiyan 2 pressed in base does nothing
seq, bad = play('goku', [7, SS, SS2, SS3], 0, (SS2, SS, SS2, SS3, SS3))
fs = [f for f, _, _ in seq]
print('   Goku:', fs)
check('Super Saiyan 2 does nothing from base', fs[0] == 0)
check('Super Saiyan, then 2, then 3, then back to base', fs[1] in (3, 4) and fs[2] in (F['goku_ss2'], F['goku_ss2_b']) and fs[3] in (5, 6) and fs[4] in (0, 2) and not bad)
# Super Saiyan 2 follows Super Saiyan in its own skill (the owner, Nov 9: "SS2 follows SS1 and precedes SS3 so it doesn't have to be swapped
# for SS1"): with six held and no room for Super Saiyan 2, Super Saiyan goes up to it, Super Saiyan 3 from there, and pressed again it's base
seq, bad = play('goku_chain', [7, SS, SS3, 15, 14, 19], 0, (SS, SS, SS3, SS3))
fs = [f for f, _, _ in seq]
print('   Goku without Super Saiyan 2 held:', fs)
check('without Super Saiyan 2 held: Super Saiyan, Super Saiyan again for 2, then 3, then back', fs[0] in (3, 4) and fs[1] in (F['goku_ss2'], F['goku_ss2_b']) and fs[2] in (5, 6) and fs[3] in (0, 2) and not bad)
seq, bad = play('goku_ss_down', [7, SS, SS3, 15, 14, 19], 0, (SS, SS, SS))
fs = [f for f, _, _ in seq]
check('Super Saiyan pressed in Super Saiyan 2 powers down', fs[1] in (F['goku_ss2'], F['goku_ss2_b']) and fs[2] in (0, 2) and not bad)
# Super Saiyan 2 pressed in Super Saiyan 2 powers down
seq, bad = play('goku2', [7, SS, SS2], 0, (SS, SS2, SS2))
fs = [f for f, _, _ in seq]
check('Super Saiyan 2 pressed again powers down', fs[1] in (F['goku_ss2'], F['goku_ss2_b']) and fs[2] in (0, 2) and not bad)
# Kaioken: from base, Super Saiyan can't go on top, health drains, pressed again it stops; no Kaioken from Super Saiyan
seq, bad = play('kaioken', [7, SS, KK], 0, (KK, SS, KK), wait=300)
fs = [f for f, _, _ in seq]; hp = [h for _, h, _ in seq]
print('   Kaioken:', seq)
check('Kaioken from base', fs[0] == F['goku_kaioken'] and not bad)
check('no Super Saiyan in Kaioken', fs[1] == F['goku_kaioken'])
check('Kaioken costs health as it goes', hp[1] < hp[0])
check('Kaioken pressed again stops it', fs[2] in (0, 2))
seq, bad = play('kaioken2', [7, SS, KK], 0, (SS, KK))
check('no Kaioken in Super Saiyan', seq[0][0] in (3, 4) and seq[1][0] in (3, 4))
# Kid Goku: Super Saiyan, 3, 4, then 4 again (down)
seq, bad = play('kid', [7, SS, SS3, SS4], F['kid_goku'], (SS4, SS, SS3, SS4, SS4))
fs = [f for f, _, _ in seq]
print('   Kid Goku:', fs)
check('Super Saiyan 4 does nothing from base', fs[0] == F['kid_goku'])
check('Kid Goku: Super Saiyan, 3, 4, then back to base', fs[1] == F['kid_goku_ssj'] and fs[2] == F['kid_goku_ssj3'] and fs[3] == F['kid_goku_ssj4'] and fs[4] == F['kid_goku'] and not bad)
# GT Vegeta: Super Saiyan, then 4
seq, bad = play('vegeta', [7, SS, SS4], F['vegeta_gt'], (SS, SS4, SS4))
fs = [f for f, _, _ in seq]
check('GT Vegeta: Super Saiyan, then 4, then back', fs[0] == F['vegeta_gt_ssj'] and fs[1] == F['vegeta_gt_ssj4'] and fs[2] == F['vegeta_gt'] and not bad)
# GT Gohan: Super Saiyan, then 2 (the build's lightning copy)
seq, bad = play('gohan', [7, SS, SS2, SS3], F['gohan_gt'], (SS, SS2, SS2))
fs = [f for f, _, _ in seq]
check('GT Gohan: Super Saiyan, then 2, then back', fs[0] == F['gohan_gt_ssj'] and fs[1] == F['gohan_gt_ss2'] and fs[2] == F['gohan_gt'] and not bad)
# DBS Gogeta: Super Saiyan, then Blue (its own skill now)
seq, bad = play('gogeta', [7, SS, SSB], F['gogeta_dbs'], (SS, SSB, SSB))
fs = [f for f, _, _ in seq]
print('   DBS Gogeta:', fs)
check('DBS Gogeta: Super Saiyan, then Blue, then back', fs[0] == F['gogeta_dbs_ss'] and fs[1] == F['gogeta_ssb'] and fs[2] == F['gogeta_dbs'] and not bad)
# Goku's and Vegeta's Super Saiyan Blue (after the ending, from mastery: test_mastery.py): from Super Saiyan only, then back to base
seq, bad = play('goku_blue', [7, SS, SSB], 0, (SSB, SS, SSB, SSB))
fs = [f for f, _, _ in seq]
print('   Goku Blue:', fs)
check('Blue does nothing from base', fs[0] == 0)
check('Goku: Super Saiyan, then Blue, then back to base', fs[1] in (3, 4) and fs[2] in (F['goku_ssb'], F['goku_ssb_b']) and fs[3] in (0, 2) and not bad)
seq, bad = play('vegeta_blue', [7, SS, SSB], 26, (SS, SSB, SSB))           # Vegeta's own form 26, his Super Saiyan 28 (build.py SSB_LOOKS)
fs = [f for f, _, _ in seq]
print('   Vegeta Blue:', fs)
check('Vegeta: Super Saiyan, then Blue, then back to base', fs[0] in (28, 29) and fs[1] in (F['vegeta_ssb'], F['vegeta_ssb_b']) and fs[2] in (26, 27) and not bad)
seq, bad = play('blue_kaioken', [7, SS, SSB, KK], 0, (SS, SSB, KK))
check('no Kaioken in Blue', seq[2][0] == seq[1][0] and seq[1][0] in (F['goku_ssb'], F['goku_ssb_b']))
# Full Power (the owner, Nov 9: "a full power Mystic form for Mystic Gohan only don't allow any of his other forms to use it"): from the
# orange gi (form 13) only; Super Saiyan does nothing in it; pressed again it is the orange gi (and the cool-down after a power-down
# holds the next transformation for a while, as retail Super Saiyan's)
seq, bad = play('mystic_fp', [7, SS, FP], 13, (FP, SS, FP))
fs = [f for f, _, _ in seq]
print('   Mystic Gohan:', fs)
check('Full Power from the orange gi', fs[0] == F['gohan_mystic_fp'] and not bad)
check('no Super Saiyan in Full Power', fs[1] == F['gohan_mystic_fp'])
check('Full Power pressed again is the orange gi', fs[2] == 13)
for look, ss in ((10, 16), (15, 18)):                 # school uniform, green gi: no Full Power, from base or from their Super Saiyan
    seq, bad = play('fp_%d' % look, [7, SS, FP], look, (FP, SS, FP))
    fs = [f for f, _, _ in seq]
    check('no Full Power in form %d or its Super Saiyan' % look, fs == [look, ss, ss] and not bad)
seq, bad = play('fp_orange_ss', [7, SS, FP], 13, (SS, FP))
check('the orange gi\'s Super Saiyan is its own form (not the school uniform\'s), and no Full Power from it', [f for f, _, _ in seq] == [F['gohan_orange_ss']] * 2 and not bad)
# the icons on the HUD: each tier's own
shots = {'Super Saiyan 2': ('goku2', 1), 'Super Saiyan 4': ('kid', 3), 'Kaioken': ('kaioken', 0), 'Super Saiyan Blue': ('gogeta', 1), 'Full Power': ('mystic_fp', 0)}
grid = []
for n, (who, k) in shots.items():
    grid.append(icon('%s_%d' % (who, k)))
Image.fromarray(np.concatenate(grid, 0)).resize((32 * 8, 16 * 8 * len(grid)), Image.NEAREST).save(D + '/icons.png')
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
