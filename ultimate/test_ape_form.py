#!/usr/bin/env python3
"""The Great Ape form (Nov 9), in the Bomber fight of tools/harness/enemy_test.txt (build `--debug --enemy` first).
  python3 ultimate/test_ape_form.py [rom] [work dir]
GT Kid Goku and GT Vegeta learn it when the Great Ape raid is won (more flag great_ape.MORE_APE_DONE, the bench's spare bytes). From their GT
base looks (build.py APE_LOOKS) it changes them into the Great Ape on its own figure (lib/oozaru.py: the change on that figure, no aura),
hits 2x as hard, and pressed again changes back. Nothing from Super Saiyan, nothing in any other look, no other tier from it. Its icon is
its own (the owner: "a custom oozaru icon to distinguish from SSJ icon").
The Great Ape is drawn twice the size (outfit.c big_check: an affine matrix of half steps), feet where they were, and the fight camera centres
him higher so his head stays on screen (cam_follow). His Chou Makouhou (skill 49, known with the Great Ape: the owner, "a new mouth beam
ability for the great ape form ONLY ... a yellow beam ... wide like the final flash") is Final Flash's code and yellow beam at the top level,
1.5x as strong, twice as wide and up at his mouth (flash_draw), hitting along the ground in every direction; nothing outside the ape."""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'), 'tools/scripts']
import great_ape, icons, oozaru
R, forms = T.R, T.forms
G = 0x03001068
BENCH_ON = ['poke 0203F000 32484342', 'poke 0203F004 00001234', 'poke8 03001559 34', 'poke8 0300155A 12']
POST = ['poke8 %08X %02X' % (G + 0x55 + 149 // 8, 1 << 149 % 8)]
SPARE = 0x0203F000 + 20 + 21 * 22 + 4                 # outfit.c struct bench: spare[0..3] hold more flags 64-95
f = great_ape.MORE_APE_DONE - 64
APE_DONE = BENCH_ON + ['poke8 %08X %02X' % (SPARE + (f >> 3), 1 << (f & 7))]
SS, SS3, KK, APE, BEAM, FLASH = 20, 22, 37, 48, 49, 10
SS_FULL = ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F)]
APES = {forms[n] for n in ('kid_goku_ape', 'vegeta_gt_ape', 'vegeta_gt_tank_ape')}
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

# 0. The rows: three Great Ape forms on the ape's figures, down to their looks; the skill's own icon and name
for n, (base, owner, fig) in (('kid_goku_ape', ('kid_goku', 0, 'oozaru_kid_goku')), ('vegeta_gt_ape', ('vegeta_gt', 4, 'oozaru_vegeta')),
                              ('vegeta_gt_tank_ape', ('vegeta_gt_tank', 4, 'oozaru_vegeta'))):
    row = rom[0x800000 + 24 * forms[n]:0x800000 + 24 * forms[n] + 24]
    check('%s: down to %s, owner %d, Super Saiyan class, nothing above it' % (n, base, owner), row[0x17] == forms[base] and row[0x0C] == owner and row[0] & 1 and row[0x16] == 255)
check("the moustached GT Vegeta has no Great Ape (his change on the owner's sheet is clean-shaven)", 'vegeta_gt_mustache_ape' not in forms)
SKILLS = u(0x13618) - 0x08000000
ss_row, ape_row = rom[SKILLS + 24 * SS:SKILLS + 24 * SS + 24], rom[SKILLS + 24 * APE:SKILLS + 24 * APE + 24]
pics = [rom[p - 0x08000000:p - 0x08000000 + 0x200] for p in struct.unpack_from('<II', ape_row, 4)]
ss_pics = [rom[p - 0x08000000:p - 0x08000000 + 0x200] for p in struct.unpack_from('<II', ss_row, 4)]
want = [icons.drawn(s, oozaru.ICON, k) for s, k in zip(ss_pics, (oozaru.ICON_COLOURS, oozaru.ICON_GREYED))]
check('the Great Ape has its own icon (the ape and the moon, and its greyed copy), not Super Saiyan\'s Z', pics == want and pics[0] != ss_pics[0] and pics[1] != ss_pics[1])
check('its name is the Great Ape', 'Great Ape'.encode('utf-16-le') in rom)

# 1. Learning it: when the raid is won, not before
s, bad = held(POST + APE_DONE, 'learn')
print('   Goku holds', s)
check('Goku learns the Great Ape when the raid is won', APE in s and not bad)
check('not before', APE not in held(POST + BENCH_ON, 'learn_no')[0])

# 2. GT Kid Goku: base to the Great Ape and back, on the ape's own figure while it changes; nothing from it, nothing to it from Super Saiyan
def presses(name, skills, seq, form, watch=False):
    L = T.setup(skills, form, (0,)) + T.AWAY + ['run 2']        # (the first press after the walk-in does nothing: one goes first, as test_ssg's)
    for k in seq:
        L += ['poke8 %08X %02X' % (R + 0x15, k)] + T.FULL + SS_FULL + ['keys B', 'run 2', 'keys']
        if watch: L += [v for _ in range(8) for v in T.AWAY + ['run 4', 'mem %08X 1' % (T.PLAYER_OBJ + 0x58)]]
        L += [v for _ in range(8) for v in T.AWAY + ['run 30']] + ['mem %08X 1' % (R + 0x14)] + ['shot %s_%d' % (name, len(L))]
    o = T.run(L, name)
    return [w[0] & 255 for w in words(o, R + 0x14)], [w[0] for w in words(o, T.PLAYER_OBJ + 0x58)], 'bad pc' in o
kid = forms['kid_goku']
fs, figs, bad = presses('ape', [7, SS, APE], (2, 2), kid, watch=True)
print('   forms', fs, 'figures while changing', [hex(x) for x in figs[:8]])
check('GT Kid Goku: the Great Ape from base, and back to base', fs[0] == forms['kid_goku_ape'] and fs[1] == kid and not bad)
check('he changes on the ape\'s own figure', figs[:8] and all(x == figure(fs[0]) for x in figs[1:8]))
fs, _, bad = presses('ape_ss', [7, SS, APE], (2, 1), kid)
check('no Super Saiyan from it', fs[0] == forms['kid_goku_ape'] and fs[1] == fs[0] and not bad)
fs, _, bad = presses('ape_kk', [7, APE, KK], (1, 2), kid)
check('no Kaioken from it', fs[0] == forms['kid_goku_ape'] and fs[1] == fs[0] and not bad)
fs, _, bad = presses('ss_ape', [7, SS, APE], (1, 2), kid)
check('and none from Super Saiyan', fs[0] == forms['kid_goku_ssj'] and fs[1] == fs[0] and not bad)
fs, _, bad = presses('adult_ape', [7, SS, APE], (2,), 0)
check('not for Goku in his own gi (form 0): GT Kid Goku only', fs[0] == 0 and not bad)

# 3. Its strength: 2x a base Kamehameha
b0, f0, _ = T.fire('kame_kid', [7, 15, APE], 1, kid, presses=(0,))
a0, fa, bb = T.fire('kame_ape', [7, 15, APE], 1, kid, presses=(0, 2))
print('   Kamehameha %.1f as GT Kid Goku (form %d), %.1f as the Great Ape (form %d)' % (b0, f0, a0, fa))
check('the Great Ape: about 2x base', fa == forms['kid_goku_ape'] and b0 > 0 and 1.75 < a0 / b0 < 2.3 and not bb)

# 3b. Twice the size, and the Chou Makouhou
beam_row = rom[SKILLS + 24 * BEAM:SKILLS + 24 * BEAM + 24]
pics = [rom[p - 0x08000000:p - 0x08000000 + 0x200] for p in struct.unpack_from('<II', beam_row, 4)]
check('the Chou Makouhou has its own icon (the ape firing the yellow beam, and its greyed copy), no level',
      pics == [icons.drawn(i, oozaru.BEAM_ICON, k) for i, k in zip(ss_pics, (oozaru.ICON_COLOURS, oozaru.ICON_GREYED))] and beam_row[0] == 0xFF)
check('its name is the Chou Makouhou', 'Chou Makouhou'.encode('utf-16-le') in rom)
check('Goku learns it with the Great Ape (into a free slot), not before', BEAM in held(POST + APE_DONE, 'learn_beam')[0] and BEAM not in held(POST + BENCH_ON, 'learn_beam_no')[0])
SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
         (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
def oam(d, name):
    o = open('%s/%s.bin' % (d, name), 'rb').read(); out = []
    for i in range(128):
        a0, a1, a2 = struct.unpack_from('<3H', o, 8 * i)
        if (a0 >> 8) & 3 == 2 or a0 >> 14 > 2: continue
        w, h = SIZES[(a0 >> 14, a1 >> 14)]; x = a1 & 0x1FF; x -= 512 * (x >= 256); y = a0 & 0xFF; y -= 256 * (y >= 160)
        dbl = (a0 >> 8) & 3 == 3; m = (a1 >> 9) & 31
        mat = [struct.unpack_from('<h', o, 0x20 * m + 6 + 8 * k)[0] for k in range(4)] if (a0 >> 8) & 1 else None
        out.append((w, h, x + (w if dbl else w // 2), y + (h if dbl else h // 2), dbl, mat))      # size, centre, double-size, matrix
    return out
def beam_look(name, skills, slot, face, form=None, presses=(0, 1), level=None):
    """Fire skills[slot] facing `face` at the Bomber 40 px off; -> (HP it lost, the player's feet on screen, OAM mid-beam, bad jump)."""
    form = kid if form is None else form
    L = T.setup(skills, form, presses) + T.AWAY + ['run 1', 'poke %s %x' % (T.ENEMY_HP, 9000 << 10), 'keys %s' % face, 'run 2', 'keys', 'run 30']
    o = T.run(L + ['mem %s 2' % T.PX], name); m = [int(v, 16) for v in re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % T.PX, o)[-1]]
    dx, dy = {'LEFT': (-40, 0), 'RIGHT': (40, 0), 'UP': (0, -40), 'DOWN': (0, 40)}[face]
    near = ['poke %s %x' % (T.ENEMY_X, m[0] + (dx << 8)), 'poke %s %x' % (T.ENEMY_Y, m[1] + (dy << 8))]
    L += near + ['poke8 %08X %02X' % (R + 0x15, slot)] + T.FULL + (['poke8 %08X %02X' % (R + 0x2E + 2 * slot, level)] if level is not None else []) + ['run 1', 'mem %s 1' % T.ENEMY_HP, 'keys B'] + [v for _ in range(80) for v in near + ['run 1']]
    L += ['dump %s 07000000 400' % name, 'mem %08X 2' % (T.PLAYER_OBJ + 0x6C), 'shot %s' % name] + [v for _ in range(20) for v in near + ['run 1']] + ['keys', 'run 40', 'mem %s 1' % T.ENEMY_HP]
    o = T.run(L, name)
    hp = [int(v, 16) for v in re.findall(r'mem %s: ([0-9a-f]+)' % T.ENEMY_HP.lower(), o)]
    feet = [int(v, 16) for v in re.findall(r'mem %08x: ([0-9a-f]+) ([0-9a-f]+)' % (T.PLAYER_OBJ + 0x6C), o)[-1]]
    feet = [v - (1 << 32) if v >= 1 << 31 else v for v in feet]
    return (hp[0] - hp[-1]) / 1024, (feet[0] + 8, feet[1] + 7), oam(T.D, name), 'bad pc' in o
dirs = {}
for face in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
    dirs[face] = beam_look('beam_' + face.lower(), [7, APE, BEAM], 2, face)
    print('   Chou Makouhou facing %s: %.1f; feet at %s' % (face, dirs[face][0], dirs[face][1]))
d0 = dirs['LEFT'][0]
check('the Chou Makouhou hits as the Great Ape, the same in every direction', d0 > 0 and all(abs(v[0] - d0) < 1 and not v[3] for v in dirs.values()))
ape_box = [e for e in dirs['LEFT'][2] if (e[0], e[1]) == (64, 64)]
fx, fy = dirs['LEFT'][1]
print('   the ape\'s piece:', ape_box)
check('the Great Ape is drawn twice the size (a double-size box, half steps)', len(ape_box) == 1 and ape_box[0][4] and ape_box[0][5] in ([128, 0, 0, 128], [-128, 0, 0, 128]))
check('the camera keeps his head on screen (his box starts no more than 24 rows above it: 11 empty rows at 2x)', ape_box and ape_box[0][3] - 64 >= -24)
for face in ('LEFT', 'RIGHT'):
    pieces = [e for e in dirs[face][2] if e[4] and (e[0], e[1]) != (64, 64)]
    fx, fy = dirs[face][1]
    tops, bottoms = [e[3] - e[1] for e in pieces], [e[3] + e[1] for e in pieces]
    print('   %s: %d beam pieces, from %d to %d rows above his feet; across scales %s' % (face, len(pieces), fy - min(tops) if tops else 0, fy - max(bottoms) if bottoms else 0, sorted({abs(e[5][3]) for e in pieces})))
    check('facing %s: the beam is twice as wide (64 rows), from his mouth (60+ rows up) to near the ground (16 or fewer)' % face.lower(),
          len(pieces) >= 3 and all(abs(e[5][3]) == 0x80 and abs(e[5][0]) == 0x100 for e in pieces) and fy - min(tops) >= 60 and fy - max(bottoms) <= 16)
none, nf, _ = T.fire('beam_base', [7, APE, BEAM], 2, kid, presses=(0,))
check('nothing outside the Great Ape: GT Kid Goku in base can\'t fire it', none == 0 and nf == kid)
ff, _, _, _ = beam_look('flash_ape', [7, APE, FLASH], 2, 'LEFT', level=2)          # the same hold, the same target
print('   as the Great Ape: Final Flash (top level) %.1f, Chou Makouhou %.1f' % (ff, d0))
check('the Chou Makouhou: about 1.5x Final Flash at its top level', ff > 0 and 1.3 < d0 / ff < 1.7)

# 4. GT Vegeta (the debug picker's fourth fighter: his own record)
pick = [i for i, l in enumerate(T.base) if l == 'tap A 60'][-1]
T.base[pick:pick] = ['tap RIGHT 40'] * 3
R = T.R = 0x03001560 + 4 * 0x68
T.FULL[:] = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)]
SS_FULL = ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 00' % (R + 0x1F)]
for look in ('vegeta_gt', 'vegeta_gt_tank'):
    fs, figs, bad = presses(look, [7, SS, APE], (2, 2), forms[look], watch=True)
    check('%s: the Great Ape from base on its own figure, and back' % look, fs[0] == forms[look + '_ape'] and fs[1] == forms[look] and not bad
          and figs[:8] and all(x == figure(fs[0]) for x in figs[1:8]))
fs, _, bad = presses('mustache', [7, SS, APE], (2,), forms['vegeta_gt_mustache'])
check('not in the moustached look', fs[0] == forms['vegeta_gt_mustache'] and not bad)
vb = beam_look('beam_vegeta', [7, APE, BEAM], 2, 'RIGHT', forms['vegeta_gt'])
check('GT Vegeta fires the Chou Makouhou as the Great Ape too (twice as wide)', vb[0] > 0 and not vb[3]
      and any(e[4] and abs(e[5][3]) == 0x80 for e in vb[2] if (e[0], e[1]) != (64, 64)))
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
