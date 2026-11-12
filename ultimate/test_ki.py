#!/usr/bin/env python3
"""Super Saiyan 4's own ki bar (outfit.c ssj4_hud / ssj4_drain). Build `--debug --enemy` first.
  python3 ultimate/test_ki.py [rom] [work dir]
Kid Goku: Super Saiyan 3 shows its orange bar; Super Saiyan 4 shows a purple one over the orange he had left, drains the purple, then
carries on with the orange and powers down when that runs out. GT Vegeta (Super Saiyan, then Super Saiyan 4) gets the purple bar too,
Super Saiyan stays yellow and Super Saiyan 3 orange."""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='ki'); os.makedirs(D, exist_ok=True)
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
pal = np.frombuffer(open('baserom.gba', 'rb').read()[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3) >> 3
pal = (pal << 3 | pal >> 2).astype(np.uint8)          # as the harness's screenshots widen 5-bit colour
PURPLE = {tuple(pal[i]) for i in (0x9B, 0x9C, 0x93, 0x94, 0x5B)}
ORANGE = {tuple(pal[i]) for i in (0x6B, 0x6C, 0x04, 0x6D, 0x6E)}
YELLOW = {tuple(pal[i]) for i in (0x1A, 0x1B, 0x1C, 0x1D, 0x1E)}
base = [l for l in open('tools/harness/enemy_test.txt').read().split('\n') if l and not l.startswith('#') and not l.startswith('mem ') and not l.startswith('shot ') and l not in ('tap B 20', 'run 200')]
R = 0x03001560
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)

def play(name, form, presses, after):
    """presses: skill slots pressed in turn (1 = Super Saiyan, 2 = Super Saiyan 3, 3 = Super Saiyan 4); after: script lines once they're done."""
    L = base + ['guardon 0x09000000', 'poke8 %08X 04' % (R + 0x0C), 'poke8 %08X 07' % (R + 0x0D), 'poke8 %08X 14' % (R + 0x0E), 'poke8 %08X 16' % (R + 0x0F), 'poke8 %08X 24' % (R + 0x10), 'run 4']
    L += ['poke8 %08X %02X' % (R + 0x14, form)]
    for k, p in enumerate(presses):      # the first press only waits: see tools/harness/enemy_test.txt (it went while the EEPROM was writing)
        L += ['poke8 %08X %02X' % (R + 0x15, p), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B)] + (['keys B', 'run 2', 'keys'] if k else ['run 2']) + ['run 240']
    L += after
    open(D + '/%s.txt' % name, 'w').write('\n'.join(L) + '\n')
    out = subprocess.run(['tools/harness/harness', ROM, D + '/%s.txt' % name, D], capture_output=True, text=True, timeout=900).stdout
    recs = [[int(x, 16) for x in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem 03001560')]
    sk = [int(l.split(':')[1].split()[0], 16) & 0xFFFF for l in out.splitlines() if l.startswith('mem 0203ffb0')]
    play.rest = sk                                       # the orange put aside, at each step
    return [(w[5] & 255, w[8] & 0xFFFF) for w in recs], 'bad pc' in out

def bar(shot):
    """Counts of purple, orange and yellow pixels in the HUD's EP bar, left to right: (purple, orange, yellow, order)."""
    im = np.array(Image.open("%s/%s.png" % (D, shot)).convert("RGB"))[8:26, 44:100]     # the bars, not the skill icon (Super Saiyan 4's has a purple 4)
    px = [tuple(p) for p in im.reshape(-1, 3)]
    n = lambda s: sum(p in s for p in px)
    cols = lambda s: [x for x in range(im.shape[1]) if any(tuple(im[y, x]) in s for y in range(im.shape[0]))]
    return n(PURPLE), n(ORANGE), n(YELLOW), cols

step = lambda t, n: ['shot %s' % n, 'mem %08X 10' % R, 'mem 0203FFB0 2', 'run %d' % t]
# Kid Goku: Super Saiyan, Super Saiyan 3 (left with 60 orange), Super Saiyan 4
after = []
for t in range(30): after += step(90, 'k%02d' % t)
ss3, bad0 = play('kid_ss3', forms['kid_goku'], [1, 1, 2], ['poke %08X 0000003C' % (R + 0x20), 'run 4'] + step(90, 'ss3') + step(1, 'ss3b'))
p, o, y, cols = bar('ss3')
rate3 = ss3[-2][1] - ss3[-1][1]
check('Kid Goku Super Saiyan 3: an orange bar, no purple', ss3[-1][0] == forms['kid_goku_ssj3'] and o > 20 and p == 0)
seq, bad = play('kid_ss4', forms['kid_goku'], [1, 1, 2], ['poke %08X 0000003C' % (R + 0x20), 'run 4', 'poke8 %08X 03' % (R + 0x15), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'keys B', 'run 2', 'keys', 'run 230'] + after)
rest = play.rest
print('   Kid Goku Super Saiyan 4 (form, pool, orange put aside) every 90 frames:', [a + (b,) for a, b in zip(seq, rest)])
fs = [f for f, _ in seq]
check('no bad jumps', not bad and not bad0)
check('Kid Goku goes Super Saiyan 4', fs[0] == forms['kid_goku_ssj4'])
p, o, y, cols = bar('k00')
check('Super Saiyan 4 shows a purple bar', p > 40)
up = [i for i in range(1, len(seq)) if seq[i][1] > seq[i - 1][1] and seq[i][0] == forms['kid_goku_ssj4']]
check('when the purple runs out, Super Saiyan 4 carries on with the orange he had left', len(up) == 1 and 45 <= seq[up[0]][1] <= 60)
if up:
    drops = [seq[i - 1][1] - seq[i][1] for i in range(1, up[0])]
    print('   Super Saiyan 3 drains %d per 90 frames, Super Saiyan 4\'s purple %s' % (rate3, drops))
    check('the purple drains at about half Super Saiyan 3\'s rate', rate3 > 0 and all(0.35 < v / rate3 < 0.65 for v in drops[1:]))
    check('the orange stays as it is while the purple drains', all(r == rest[0] for r in rest[:up[0]]) and 55 <= rest[0] <= 60)
    od = [seq[i - 1][1] - seq[i][1] for i in range(up[0] + 2, len(seq)) if seq[i][1] > 0 and seq[i][0] == forms['kid_goku_ssj4']]
    check('then the orange drains, at the same slower rate', len(od) >= 2 and all(0.35 < v / rate3 < 0.65 for v in od))
    mid = next(i for i in range(up[0]) if 10 < seq[i][1] < rest[0] - 5)        # purple drained below the orange put aside
    pb, ob, _, cb = bar('k%02d' % mid); pa, oa, _, ca = bar('k%02d' % up[0])
    check('the orange he had left shows past the purple as it drains', pb > 0 and ob > 0 and max(cb(PURPLE)) < max(cb(ORANGE)))
    check('then the bar is orange, with no purple', pa == 0 and oa > 20)
check('Super Saiyan 4 powers down once the orange is gone too', fs[-1] == forms['kid_goku'] and bar('k29')[0] == 0)
# GT Vegeta: Super Saiyan, then Super Saiyan 4 (the first press only waits, as in test_build)
seq, bad = play('vegeta', forms['vegeta_gt'], [1, 1], step(1, 'v_ss') + ['poke8 %08X 03' % (R + 0x15), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'keys B', 'run 2', 'keys', 'run 260'] + step(1, 'v_ss4'))
print('   GT Vegeta (form, pool):', seq)
p, o, y, _ = bar('v_ss')
check('GT Vegeta Super Saiyan: a yellow bar, no purple', seq[0][0] == forms['vegeta_gt_ssj'] and y > 20 and p == 0)
p, o, y, _ = bar('v_ss4')
check('GT Vegeta Super Saiyan 4: a purple bar', seq[1][0] == forms['vegeta_gt_ssj4'] and p > 40 and not bad)
for n in ('ss3', 'k00', 'k05', 'k%02d' % (up[0] if up else 0), 'v_ss4'):
    Image.open('%s/%s.png' % (D, n)).crop((8, 6, 96, 28)).resize((352, 88), Image.NEAREST).save('%s/bar_%s.png' % (D, n))
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
