#!/usr/bin/env python3
"""The Nov 9 moves in a fight (build `--debug --enemy` first): each one fired at the Bomber of tools/harness/enemy_test.txt,
measured against the move it is built on, with screenshots of it in flight.
  python3 ultimate/test_moves.py [rom] [work dir]"""
import json, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='moves'); os.makedirs(D, exist_ok=True)
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
H = 'tools/harness/harness'; R = 0x03001560
ENEMY_HP, ENEMY_X, ENEMY_Y, PX = '0202d558', '0202d46c', '0202d470', '0202ce1c'
base = [l for l in open('tools/harness/enemy_test.txt').read().split('\n') if l and not l.startswith('#') and not l.startswith('mem ') and not l.startswith('shot ') and l not in ('tap B 20', 'run 200')]
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def run(lines, name='r'):
    p = '%s/%s.txt' % (D, name); open(p, 'w').write('\n'.join(lines) + '\n')
    return subprocess.run([H, ROM, p, D], capture_output=True, text=True, timeout=900).stdout
def last(out, addr):
    return [int(v, 16) for v in re.findall(r'mem %s: ([0-9a-f]+)' % addr.lower(), out)]

o = run(base + ['mem %s 2' % PX]); m = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % PX, o)[-1]
X0, Y0 = int(m[0], 16), int(m[1], 16)
AWAY = ['poke %s %x' % (ENEMY_X, X0 + (120 << 8)), 'poke %s %x' % (ENEMY_Y, Y0)]
FULL = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)]

def setup(skills, form=None, presses=()):
    """Goku with these skills (and form), after the transformation presses (slots into `skills`); the Bomber kept away."""
    L = base + ['poke8 %08X %02X' % (R + 0x0C, len(skills))] + ['poke8 %08X %02X' % (R + 0x0D + i, s) for i, s in enumerate(skills)] + ['run 4']
    if form is not None: L += ['poke8 %08X %02X' % (R + 0x14, form)]
    for p in presses:
        L += ['poke8 %08X %02X' % (R + 0x15, p)] + FULL + ['keys B', 'run 2', 'keys'] + [v for _ in range(8) for v in AWAY + ['run 30']]
    return L

PLAYER_OBJ = 0x0202CC7C            # the player's object (0x03001C34 points here in this fight): +0x50 its animation, +0x11 the frame a move's code shows
watched = []
def fire(name, skills, slot, form=None, presses=(0,), hold=50, after=40, level=None, extra=(), watch=False):
    """Fire skills[slot] at the Bomber 40 px to the left; -> (HP it lost, form, bad jump). The first press after the walk-in does nothing (test_build), so one goes first.
    watch: also note (animation, frame shown) every 5 frames of the hold in `watched`."""
    L = setup(skills, form, presses) + list(extra) + AWAY + ['run 1', 'poke %s %x' % (ENEMY_HP, 9000 << 10), 'keys LEFT', 'run 2', 'keys', 'run 2']
    o = run(L + ['mem %s 2' % PX], name); m = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % PX, o)[-1]
    near = ['poke %s %x' % (ENEMY_X, int(m[0], 16) - (40 << 8)), 'poke %s %x' % (ENEMY_Y, int(m[1], 16))]
    L += near + ['poke8 %08X %02X' % (R + 0x15, slot)] + FULL
    if level is not None: L += ['poke8 %08X %02X' % (R + 0x2E + 2 * slot, level)]
    look = ['mem %08X 1' % (PLAYER_OBJ + 0x50), 'mem %08X 1' % (PLAYER_OBJ + 0x10)] if watch else []
    L += ['keys B'] + [v for k in range(hold // 5) for v in near + ['run 5'] + look + (['shot %s_hold' % name] if k == hold // 10 else [])]
    L += ['keys'] + [v for k in range(after // 5) for v in near + ['run 5'] + (['shot %s_fly' % name] if k == 2 else [])]
    o = run(L + ['mem %s 1' % ENEMY_HP, 'mem %08X 1' % (R + 0x14)], name)
    if watch: watched[:] = list(zip(last(o, '%08X' % (PLAYER_OBJ + 0x50)), [v >> 8 & 255 for v in last(o, '%08X' % (PLAYER_OBJ + 0x10))]))
    hp = last(o, ENEMY_HP)[-1]; hp = hp - (1 << 32) if hp >= 1 << 31 else hp
    return 9000 - hp / 1024, last(o, '%08X' % (R + 0x14))[-1] & 255, 'bad pc' in o

if __name__ == '__main__':
    kame, _, b0 = fire('kame', [7, 15, 38], 1)
    galick, _, b1 = fire('galick', [7, 15, 38], 2)
    print('   Kamehameha %.1f, Galick Gun %.1f' % (kame, galick))
    check('Galick Gun fires and hurts like the Kamehameha', kame > 0 and 0.8 < galick / kame < 1.25 and not b0 and not b1)
    tenx_base, _, _ = fire('tenx_base', [7, 39], 1)
    check('10x Kamehameha does nothing outside Super Saiyan 4', tenx_base == 0)
    k4, f4, _ = fire('kame4', [7, 15, 20, 22, 39, 36], 1, forms['kid_goku'], (2, 2, 3, 5))
    t4, f5, b2 = fire('tenx4', [7, 15, 20, 22, 39, 36], 4, forms['kid_goku'], (2, 2, 3, 5))
    print('   Super Saiyan 4: Kamehameha %.1f, 10x Kamehameha %.1f (forms %d %d)' % (k4, t4, f4, f5))
    check('10x Kamehameha in Super Saiyan 4: about 1.5x his Kamehameha', f5 == forms['kid_goku_ssj4'] and k4 > 0 and 1.3 < t4 / k4 < 1.7 and not b2)
    VEG = (2, 2, 5)                              # GT Vegeta: Super Saiyan, then Super Saiyan 4
    ff, f1, _ = fire('flash4', [7, 10, 20, 22, 40, 36], 1, forms['vegeta_gt'], VEG)
    sh, f2, b3 = fire('shine4', [7, 10, 20, 22, 40, 36], 4, forms['vegeta_gt'], VEG)
    print('   GT Vegeta Super Saiyan 4: Final Flash %.1f, Final Shine %.1f (forms %d %d)' % (ff, sh, f1, f2))
    check('Final Shine in Super Saiyan 4: about 1.5x his Final Flash', f2 == forms['vegeta_gt_ssj4'] and ff > 0 and 1.3 < sh / ff < 1.7 and not b3)
    sh0, _, _ = fire('shine_base', [7, 40], 1, forms['vegeta_gt'])
    check('Final Shine does nothing outside Super Saiyan 4', sh0 == 0)
    df, g1, _ = fire('dragon4', [7, 15, 20, 22, 41, 36], 4, forms['kid_goku'], (2, 2, 3, 5), hold=90, after=90)
    print('   Kid Goku Super Saiyan 4: red Dragon Fist %.1f (form %d)' % (df, g1))
    check('the red Dragon Fist hits in Super Saiyan 4', g1 == forms['kid_goku_ssj4'] and df > 0)
    # Vegeta himself, the debug picker's fourth fighter (his own record and figures). The Kamehameha's code shows frames 0-2 of the pose it sets; his
    # figures' slot 18 is his two-frame Big Bang, so they get a Galick Gun pose of their own (build.py beam_poses): no frame shown may be missing,
    # since a missing one draws junk over other sprites' tiles. His Big Bang keeps its own pose.
    import struct
    rom = open(ROM, 'rb').read()
    pick = [i for i, l in enumerate(base) if l == 'tap A 60'][-1]
    base[pick:pick] = ['tap RIGHT 40'] * 3
    R = 0x03001560 + 4 * 0x68
    FULL = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)]
    for name, skills, slot, presses in (('vegeta_galick', [7, 2, 38], 2, (0,)), ('vegeta_ss_galick', [7, 20, 38], 2, (0, 1)),
                                        ('vegeta_ss2_galick', [7, 20, 35, 38], 3, (0, 1, 2)), ('vegeta_blue_galick', [7, 20, 44, 38], 3, (0, 1, 2))):
        g, f, b = fire(name, skills, slot, presses=presses, watch=True)
        shown = [(fr, struct.unpack_from('<I', rom, a - 0x08000000)[0]) for a, fr in watched if 0x08000000 <= a < 0x0A000000]
        print('   %s: %.1f damage in form %d; (frame shown, frames in the pose) %s' % (name, g, f, sorted(set(shown))))
        check('%s: hits, and every frame its pose shows exists' % name, g > 0 and not b and shown and all(fr < n for fr, n in shown) and max(fr for fr, _ in shown) == 2)
    bb, _, b = fire('vegeta_bigbang', [7, 2, 38], 1)
    check("Vegeta's Big Bang still fires", bb > 0 and not b)
    print('screens in', D)
    if fails: sys.exit('FAILED: %s' % fails)
    print('ALL PASS')
