#!/usr/bin/env python3
"""Emulator test for ultimate/build.py output. Run from the repo root after both builds. Exits non-zero on failure.

Checks: the release build plays the opening with no bad jumps. The debug build opens Switch Character with Goku, Vegito
and Broly, picks Broly, saves, and after a fresh boot continues as Broly on the new form row, who can attack."""
import json, os, re, subprocess, sys, tempfile
H = 'tools/harness/harness'
OUT = 'ultimate/out'
fails = []

def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: fails.append(name)

def run(rom, lines, d, sav=None):
    p = os.path.join(d, 'r.txt'); open(p, 'w').write('\n'.join(lines) + '\n')
    env = dict(os.environ)
    if sav: env['HARNESS_SAV'] = sav
    return subprocess.run([H, rom, p, d], capture_output=True, text=True, env=env, timeout=500).stdout

route = open('tools/harness/long.txt').read().split('\n')[:93]
d = tempfile.mkdtemp(prefix='bfu')
G = 0x03001068; SLOT = 0x03001560; REC = 0x68; FORM = 0x14

tail = ['tap A 60'] * 3 + ['run 60', 'shot release', 'dump g 03001068 8a8']
o = run(OUT + '/BFU_PERSONAL_USE_ONLY.gba', ['guardon 0x09000000'] + route + tail, d)
check('release: opening plays with no bad jumps', 'bad pc' not in o)
rel = open(d + '/g.bin', 'rb').read()
run('baserom.gba', route + tail, d)
base = open(d + '/g.bin', 'rb').read()
# The skill book (Nov 9, outfit.c skills_sync, run for the whole party in turn): each fighter's book mask (+0x22) fills in, and a move he knows
# from the start that wasn't held joins his skills (+0x0C count, +0x0D..): Goku's Kaioken, Vegeta's Galick Gun. Nothing else may change.
import ast
SKILL_BOOK = next(ast.literal_eval(n.value) for n in ast.parse(open('ultimate/build.py').read()).body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'SKILL_BOOK')
held = lambda g, c: list(g[0x4F8 + 0x68 * c + 0x0D:0x4F8 + 0x68 * c + 0x0D + g[0x4F8 + 0x68 * c + 0x0C]])
book = {0x4F8 + 0x68 * c + o for c in range(8) for o in list(range(0x0C, 0x14)) + [0x22, 0x23]}
grown = all(held(rel, c)[:len(held(base, c))] == held(base, c) and set(held(rel, c)[len(held(base, c)):]) <= set(SKILL_BOOK[c]) for c in range(8))
print('   skills added at the start:', {c: held(rel, c)[len(held(base, c)):] for c in range(8) if held(rel, c) != held(base, c)})
check('release: game state matches the clean ROM after the opening, the skill book apart', all(i in book for i in range(len(rel)) if rel[i] != base[i]) and grown and 37 in held(rel, 0))

forms = json.load(open(OUT + '/BFU_debug.map.json'))['forms']; broly = forms['broly']
rom = OUT + '/BFU_debug_PERSONAL_USE_ONLY.gba'; sav = os.path.join(d, 'g.sav')
one = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30', 'shot picker', 'tap RIGHT 40', 'tap RIGHT 40', 'tap RIGHT 40', 'tap RIGHT 40', 'tap RIGHT 40', 'tap A 200', 'run 200',
       'shot picked', 'dump a 03001068 8a8']
o = run(rom, one, d, sav)
check('debug: no bad jumps through picker and save', 'bad pc' not in o)
a = open(d + '/a.bin', 'rb').read()
check('debug: Broly chosen (current character 8)', a[0] == 8)
check('debug: guest slot on form %d' % broly, a[0x4F8 + 8 * REC + FORM] == broly)
check('debug: 64 KB flash save written', os.path.exists(sav) and os.path.getsize(sav) == 0x10000)
two = ['guardon 0x09000000', 'run 600', 'tap START 60', 'tap START 60', 'tap A 90', 'tap A 120', 'shot slots', 'tap A 200', 'tap A 200', 'run 200', 'shot loaded',
       'dump b 03001068 8a8', 'keys RIGHT', 'run 30', 'keys', 'tap A 8', 'shot attack', 'hash']
o = run(rom, two, d, sav)
b = open(d + '/b.bin', 'rb').read()
check('reload: no bad jumps', 'bad pc' not in o)
check('reload: still Broly', b[0] == 8 and b[0x4F8 + 8 * REC + FORM] == broly)

# Select Game: a save whose area this ROM lacks must read as New Game, not stop on "Unable to find area". Reuses the Broly save.
romb = bytearray(open(rom, 'rb').read())
tab = int.from_bytes(romb[0x8A58:0x8A5C], 'little') - 0x08000000
for k in range(467):
    e = tab + 56 * k
    if romb[e] == 1 and romb[e + 1] == 1: romb[e] = 0xEE
foreign = os.path.join(d, 'foreign.gba'); open(foreign, 'wb').write(romb)
before = open(sav, 'rb').read(); sav2 = os.path.join(d, 'foreign.sav'); open(sav2, 'wb').write(before)
sel = ['guardon 0x09000000', 'run 600', 'tap START 60', 'tap START 60', 'tap A 90', 'tap A 120', 'run 60', 'shot foreign_slots', 'tap A 200', 'tap A 200', 'run 200', 'dump f 03001068 8a8', 'hash']
o = run(foreign, sel, d, sav2)
check('foreign save: Select Game survives and New Game starts', 'bad pc' not in o and open(d + '/f.bin', 'rb').read()[1] & 1 == 0)
check('foreign save: the save file itself is untouched', open(sav2, 'rb').read() == before)

# No ground shadows on Switch Character (Nov 10, the owner: "Don't render the shadows under characters feet in the switch screen it's blocking
# their name"): while it is open, none of its sprites has a shadow (+0x5C, outfit.c no_shadows); back in the field the player keeps his. The
# screen's sprites are found in EWRAM as its object's row ({character, sprite} pairs at +0x118, their count at +0x114).
def screen_sprites(ew):
    w = lambda o: int.from_bytes(ew[o:o + 4], 'little')
    for i in range(0, len(ew) - 0x170, 4):
        n = w(i + 0x114)
        if not 3 <= n <= 9: continue
        pairs = [(w(i + 0x118 + 8 * k), w(i + 0x11C + 8 * k)) for k in range(n)]
        if all(0 <= c <= 8 and 0x02000000 <= sp < 0x02040000 for c, sp in pairs) and len({c for c, _ in pairs}) == n:
            return [(c, w(sp - 0x02000000 + 0x5C)) for c, sp in pairs]
    return None
sh = ['guardon 0x09000000'] + route + ['poke8 %08X %02X' % (0x03001560 + 8 * REC + FORM, forms['android17']), 'tap A 60', 'tap A 60', 'run 30', 'tap RIGHT 40', 'tap RIGHT 40',
      'dump e 02000000 40000', 'tap B 60', 'run 200', 'dump f 02000000 40000', 'dump q 03001C34 4']
o = run(rom, sh, d)
on = screen_sprites(open(d + '/e.bin', 'rb').read())
pl = int.from_bytes(open(d + '/q.bin', 'rb').read()[:4], 'little'); fe = open(d + '/f.bin', 'rb').read()
kept = 0x02000000 <= pl < 0x02040000 and int.from_bytes(fe[pl - 0x02000000 + 0x5C:pl - 0x02000000 + 0x60], 'little') != 0
print('   Switch Character sprites (character, shadow):', on, '; the player\'s sprite afterwards', hex(pl))
check('Switch Character draws no ground shadows; the player keeps his in the field', 'bad pc' not in o and on and all(s == 0 for _, s in on) and kept)

# Broly's second skin: Switch Character, last character, Down, A.
bfp = forms['broly_fp']
o = run(rom, ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + ['tap DOWN 40', 'tap A 180', 'run 60', 'keys RIGHT', 'run 30', 'keys', 'tap A 12', 'run 20', 'dump p 03001068 8a8'], d)
p = open(d + '/p.bin', 'rb').read()
check('Broly Full Power can be chosen, walks and attacks', 'bad pc' not in o and p[0] == 8 and p[0x4F8 + 8 * REC + FORM] == bfp)

# Post-game guests and Gogeta. Debug joins Broly; poke Gogeta in and let the save at the end of the menu record what was picked.
R7, R8 = 0x03001560 + 7 * REC, 0x03001560 + 8 * REC
post = ['guardon 0x09000000'] + route + ['poke8 %08X 03' % R7] + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5
sav3 = os.path.join(d, 'post.sav')
o = run(rom, post + ['tap DOWN 40', 'tap DOWN 40', 'shot ssb_menu', 'tap RIGHT 40', 'tap DOWN 40', 'tap DOWN 40', 'shot s13_menu', 'tap LEFT 40', 'tap A 200', 'run 200', 'dump a 03001068 8a8'], d, sav3)
a = open(d + '/a.bin', 'rb').read()
check('post-game: SSB Gogeta and Android 13 can be chosen together', 'bad pc' not in o and a[0] == 7 and a[0x4F8 + 7 * REC + FORM] == forms['gogeta_ssb_skin'] and a[0x4F8 + 8 * REC + FORM] == forms['android13'])
o = run(rom, ['guardon 0x09000000', 'run 600', 'tap START 60', 'tap START 60', 'tap A 90', 'tap A 90', 'tap A 200', 'run 300', 'dump b 03001068 8a8'], d, sav3)
b = open(d + '/b.bin', 'rb').read()
check('post-game: both survive saving and loading', 'bad pc' not in o and b[0] == 7 and b[0x4F8 + 7 * REC + FORM] == forms['gogeta_ssb_skin'] and b[0x4F8 + 8 * REC + FORM] == forms['android13'])
# Skills pick frames by number: Super 13's short animations once sent the Ghost Attack, used facing sideways, into garbage. This sequence crashed there.
R = 0x03001560 + 8 * REC
seq = ['guardon 0x09000000'] + route + ['poke8 %08X %02X' % (R + 0x14, forms['super13']), 'tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + ['tap A 200', 'run 60']
for s_ in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 24, 25):
    seq += ['poke8 %08X 02' % (R + 0xC), 'poke8 %08X 07' % (R + 0xD), 'poke8 %08X %02X' % (R + 0xE, s_), 'poke8 %08X 01' % (R + 0x15), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 00' % (R + 0x1B), 'run 2', 'keys B', 'run 6', 'keys', 'run 150', 'tap B 80', 'run 200', 'keys LEFT', 'run 12', 'keys', 'run 4', 'keys RIGHT', 'run 12', 'keys', 'run 30']
seq += ['mem 03004A8C 1']
o = run(rom, seq, d)
check('Super 13 can use every attack skill in a row', 'bad pc' not in o)
# The guest's third skill follows the fighter: Eraser Cannon on Broly's forms, SS Deadly Bomber on Android 13's and Super 13's, and Cancel puts it back.
g3 = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + ['mem %08X 1' % (R + 0x0C), 'tap DOWN 40', 'tap DOWN 40', 'mem %08X 1' % (R + 0x0C), 'tap DOWN 40', 'mem %08X 1' % (R + 0x0C), 'tap B 60', 'mem %08X 1' % (R + 0x0C)]
o = run(rom, g3, d); got = [int(l.split(':')[1].split()[0], 16) >> 24 & 255 for l in o.splitlines() if l.startswith('mem %08x' % (R + 0x0C))]
check('guest skill follows the outfit', 'bad pc' not in o and len(got) == 4 and got[0] != got[1] and got[1] != got[2] and got[3] == got[0])
print('   guest skill bytes', got)
# The androids: Full Power Energy Wave, and blue blasts for them alone (Broly above, and everyone else, keep the game's).
for who_, downs_, form_ in (('Android 13', 2, 'android13'), ('Android 17', 5, 'android17'), ('Android 18', 6, 'android18')):
    an = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + ['tap DOWN 40'] * downs_ + ['tap A 200', 'run 60', 'dump p 03001068 8a8']
    an += ['poke8 %08X 00' % (R + 0x15), 'run 2', 'keys B', 'run 8', 'keys', 'run 14', 'shot blast_' + form_, 'mem %08X 1' % (R + 0x0C), 'run 100']
    an += ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 00' % (R + 0x1B), 'keys LEFT', 'run 6', 'keys', 'run 10', 'poke8 %08X %02X' % (R + 0x15, 3 if form_ != 'android18' else 3), 'run 2', 'keys B', 'run 16', 'shot charge_' + form_, 'run 40', 'shot wave_' + form_, 'run 60', 'keys', 'run 200']
    o = run(rom, an, d); p = open(d + '/p.bin', 'rb').read(); r8 = p[0x4F8 + 8 * REC:0x4F8 + 9 * REC]
    check('%s has the Full Power Energy Wave' % who_, p[0] == 8 and r8[0x14] == forms[form_] and r8[0x0C] == (4 if form_ == 'android18' else 5) and r8[0x10] == 29)
    check('%s fires blasts and the wave with no bad jumps' % who_, 'bad pc' not in o)
# Piccolo: fifth guest outfit, with Masenko and Special Beam Cannon, and every attack working.
pc = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + ['tap DOWN 40'] * 3 + ['tap A 200', 'run 60', 'dump p 03001068 8a8', 'keys RIGHT', 'run 20', 'keys', 'tap A 12', 'tap A 12', 'tap A 12', 'run 40']
for i_ in (0, 1, 2):
    pc += ['poke8 %08X %02X' % (R + 0x15, i_), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 00' % (R + 0x1B), 'run 2', 'keys B', 'run 90', 'keys', 'run 200', 'shot piccolo%d' % i_]
o = run(rom, pc, d); p = open(d + '/p.bin', 'rb').read(); r8 = p[0x4F8 + 8 * REC:0x4F8 + 9 * REC]
check('Piccolo can be chosen and has Energy Blast, Masenko and Special Beam Cannon', p[0] == 8 and r8[0x14] == forms['piccolo'] and list(r8[0x0C:0x10]) == [3, 7, 17, 26])
check('Piccolo attacks and uses all three skills with no bad jumps', 'bad pc' not in o)
# The Super 13 reward also brings Future Trunks, Android 17 and 18, Krillin and Videl to the guest slot, each with their own moves.
# (Nov 10, the owner: "give all playable Buus forms kamehameha": Majin Buu and Kid Buu hold the Kamehameha too, outfit.c `buu`.)
# Teen Gohan (Nov 12): his own guest, in the purple gi and in the Saiyan armor, with ki blasts, rush, Masenko, Kamehameha and Super Saiyan.
TEEN = [5, 7, 8, 17, 15, 20]
for name_, downs_, want_ in (('Future Trunks', 4, [5, 7, 20, 4, 11, 38]), ('Android 18', 6, [4, 7, 27, 28, 29]), ('Krillin', 7, [5, 7, 15, 28, 42, 37]), ('Videl', 8, [2, 7, 37]), ('Majin Buu', 9, [3, 7, 8, 15]), ('Super Janemba', 10, [2, 7, 8]), ('Kid Buu', 11, [3, 7, 8, 15]), ('Master Roshi', 24, [4, 7, 8, 15, 45]),
                             ('Teen Gohan', 25, TEEN), ('Teen Gohan in armor', 26, TEEN), ('Future Trunks in armor', 27, [5, 7, 20, 4, 11, 38])):
    gl = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + ['tap DOWN 40'] * downs_ + ['tap A 200', 'run 60', 'dump p 03001068 8a8', 'keys RIGHT', 'run 8', 'keys', 'tap A 12', 'tap A 12', 'tap A 12', 'keys A', 'run 60', 'keys', 'run 60']
    for i_ in range(want_[0]):
        gl += ['poke8 %08X %02X' % (R + 0x15, i_), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'run 2', 'keys B', 'run 60', 'keys', 'run 200', 'mem %08X 1' % (R + 0x14), 'shot %s%d' % (name_.replace(' ', ''), i_)]
    o = run(rom, gl, d); p = open(d + '/p.bin', 'rb').read(); r8 = p[0x4F8 + 8 * REC:0x4F8 + 9 * REC]
    check('%s can be chosen with the right moves' % name_, p[0] == 8 and list(r8[0x0C:0x0D + want_[0]]) == want_)
    check('%s attacks and uses every move with no bad jumps' % name_, 'bad pc' not in o)
    if name_.startswith('Future Trunks'):
        base_, ss_ = ('future_trunks', 'future_trunks_ss') if name_ == 'Future Trunks' else ('trunks_armor', 'trunks_armor_ss')
        check('%s goes Super Saiyan, and no further' % name_, r8[0x14] == forms[base_] and [int(l.split(':')[1].split()[0], 16) & 255 for l in o.splitlines() if l.startswith('mem %08x' % (R + 0x14))][1] == forms[ss_])
    if name_.startswith('Teen Gohan'):
        base_ = 'teen_gohan' if name_ == 'Teen Gohan' else 'gohan_armor'
        got_ = [int(l.split(':')[1].split()[0], 16) & 255 for l in o.splitlines() if l.startswith('mem %08x' % (R + 0x14))]
        check('%s: in his look, and Super Saiyan from his last skill' % name_, r8[0x14] == forms[base_] and got_[-1] == forms[base_ + '_ss'])
# Gohan fires Special Beam Cannon without a bad jump (the debug build gives it to him). (In the Saiyan armor until Nov 12: it is Teen Gohan's now.)
R1 = 0x03001560 + REC
gh = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30', 'tap RIGHT 40', 'tap A 200', 'run 60', 'dump h 03001068 8a8']
h1 = None
o = run(rom, gh, d); h1 = open(d + '/h.bin', 'rb').read()[0x4F8 + REC:0x4F8 + 2 * REC]
at_ = list(h1[0x0D:0x0D + h1[0x0C]]).index(26) if 26 in h1[0x0D:0x0D + h1[0x0C]] else 0
check('debug: Gohan has Special Beam Cannon', 26 in h1[0x0D:0x0D + h1[0x0C]])
o = run(rom, gh + ['poke8 %08X %02X' % (R1 + 0x15, at_), 'poke8 %08X FF' % (R1 + 0x1A), 'poke8 %08X 00' % (R1 + 0x1B), 'keys RIGHT', 'run 8', 'keys', 'run 3', 'keys B', 'run 60', 'shot gohan_beam', 'keys', 'run 200'], d)
check('Gohan fires Special Beam Cannon', 'bad pc' not in o)
# Super Saiyan 2 is its own skill (Nov 9), from Super Saiyan. Goku goes on to Super Saiyan 3 from there; back down from the top. VRAM stays intact (slot 10 on Super Saiyan actors).
def chain(c, rights, form, skills, presses, lock=None):
    R_ = 0x03001560 + c * REC
    L = ['guardon 0x09000000'] + route + (['poke8 %08X %02X' % (R_ + 0x14, form)] if form is not None else []) + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * rights + ['tap A 200', 'run 60', 'poke8 %08X %02X' % (R_ + 0x0C, len(skills))]
    if lock: L += ['poke8 %08X 00' % (0x03001068 + 0x55 + lock // 8)]
    L += ['poke8 %08X %02X' % (R_ + 0x0D + i_, v_) for i_, v_ in enumerate(skills)]
    for p_ in presses:
        L += ['poke8 %08X %02X' % (R_ + 0x15, p_), 'poke8 %08X FF' % (R_ + 0x1A), 'poke8 %08X 00' % (R_ + 0x1B), 'run 1', 'tap B 240', 'mem %08X 1' % (R_ + 0x14)]
    o_ = run(rom, L, d)
    return 'bad pc' not in o_, [int(l.split(':')[1].split()[0], 16) & 255 for l in o_.splitlines() if l.startswith('mem %08x' % (R_ + 0x14))]
ok_, got_ = chain(0, 0, None, [7, 20, 35, 22], [1, 2, 3])
check('Goku: Super Saiyan, Super Saiyan 2, Super Saiyan 3', ok_ and got_[:3] == [4, forms['goku_ss2_b'], 6])
ok_, got_ = chain(4, 3, None, [7, 20, 35], [1, 2, 2])
check('Vegeta: Super Saiyan, Super Saiyan 2, back', ok_ and got_[:3] == [28, forms['vegeta_ss2'], 26])
ok_, got_ = chain(8, 5, forms['gohan_armor'], [7, 20, 35], [1, 2])
check('Teen Gohan in armor: Super Saiyan, Super Saiyan 2', ok_ and got_[:2] == [forms['gohan_armor_ss'], forms['gohan_armor_ss2']])
ok_, got_ = chain(8, 5, forms['teen_gohan'], [7, 20, 35], [1, 2, 2])
check('Teen Gohan: Super Saiyan, Super Saiyan 2, back', ok_ and got_[:3] == [forms['teen_gohan_ss'], forms['teen_gohan_ss2'], forms['teen_gohan']])
ok_, got_ = chain(8, 5, forms['teen_gohan'], [7, 20], [1, 1])
check('Teen Gohan: Super Saiyan 2 through the Super Saiyan skill (no story flag needed)', ok_ and got_[:2] == [forms['teen_gohan_ss'], forms['teen_gohan_ss2']])
ok_, got_ = chain(3, 2, None, [7, 20, 35], [1, 2])
check('Trunks: Super Saiyan, Super Saiyan 2', ok_ and got_[:2] == [22, forms['trunks_ss2']])
ok_, got_ = chain(8, 5, forms['trunks_armor'], [7, 20, 35], [1, 2])
check('Future Trunks in armor: Super Saiyan, and no further (his jacket\'s top, Nov 12)', ok_ and got_[:2] == [forms['trunks_armor_ss'], forms['trunks_armor_ss']])
ok_, got_ = chain(6, 4, 39, [7, 20, 35], [1, 2])
check('Vegito: Super Saiyan, Super Saiyan 2', ok_ and got_[:2] == [40, forms['vegito_ss2']])
# Before the story reaches it, Super Saiyan 2 does nothing; Super Saiyan pressed again turns back as in the retail game.
ok_, got_ = chain(4, 3, None, [7, 20, 35], [1, 2, 1], lock=868)
check('locked: Vegeta goes Super Saiyan, no further, then back', ok_ and got_[:3] == [28, 28, 26])
ok_, got_ = chain(0, 0, None, [7, 20, 35], [1, 2, 1], lock=864)
check('locked: Goku goes Super Saiyan, no further, then back', ok_ and got_[:3] == [4, 4, 2])
ok_, got_ = chain(0, 0, None, [7, 20, 22, 35], [1, 3], lock=864)
check('a save with Super Saiyan 3 already has Super Saiyan 2', ok_ and got_[:2] == [4, forms['goku_ss2_b']])
# The story turns each one on at its own scene: read the scripts back out of the release ROM.
sys.path[:0] = ['tools/scripts']
import events, bfscript
rel_rom = open(OUT + '/BFU_PERSONAL_USE_ONLY.gba', 'rb').read()
def sets_flag(at, flag):
    while (t := int.from_bytes(rel_rom[at:at + 4], 'little')) >= 0x08000000:        # the build's edited steps sit past the range events.read_list knows
        at += 4; step = events.parse_step(rel_rom, t - 0x08000000)
        code = step['raw'] if step['type'] == 4 else rel_rom[step['code'][0]:step['code'][1]] if 'code' in step else None
        if code and re.search(r'\b%d\b[^\n]*\n?\s*call set_flag|set_flag\(%d\)' % (flag, flag), bfscript.disasm(code)[0]): return True
    return False
for flag_, at_ in json.load(open(OUT + '/BFU.map.json'))['ss2_lists'].items():
    check('the story sets Super Saiyan 2 flag %s' % flag_, sets_flag(at_, int(flag_)))

# DBS Gogeta transforms twice through the form table and back.
R = 0x03001560 + 7 * REC
dbs = post + ['tap DOWN 40', 'tap A 200', 'run 60'] + ['poke8 %08X 05' % (R + 0x0C), 'poke8 %08X 14' % (R + 0x10), 'poke8 %08X 15' % (R + 0x11), 'poke8 %08X 03' % (R + 0x15), 'run 3', 'tap B 220', 'mem %08X 1' % (R + 0x14), 'poke8 %08X 04' % (R + 0x15), 'run 3', 'tap B 220', 'mem %08X 1' % (R + 0x14), 'tap B 350', 'mem %08X 1' % (R + 0x14)]
o = run(rom, dbs, d); got = [int(l.split(':')[1].split()[0], 16) & 255 for l in o.splitlines() if l.startswith('mem %08x' % (R + 0x14))]
check('DBS Gogeta: Super Saiyan, then Super Saiyan Blue, then back to base', 'bad pc' not in o and got == [forms['gogeta_dbs_ss'], forms['gogeta_ssb'], forms['gogeta_dbs']])
# The story borrows the guest slot for Hercule: the screen puts a joined guest back on an outfit he owns.
o = run(rom, ['guardon 0x09000000'] + route + ['poke8 %08X 2F' % (R8 + 0x14), 'tap A 60', 'tap A 60', 'run 30', 'tap B 120', 'dump a 03001068 8a8'], d)
a = open(d + '/a.bin', 'rb').read()
check('a guest borrowed by the story comes back as Broly', 'bad pc' not in o and a[0x4F8 + 8 * REC + FORM] == forms['broly'])

# Outfit menu: Gohan is the second character. Down twice = orange gi; B cancels; A keeps it.
pick = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30', 'tap RIGHT 40', 'tap DOWN 30', 'tap DOWN 30', 'shot outfit']
o = run(rom, pick + ['tap B 150', 'run 100', 'dump c 03001068 8a8'], d)
c = open(d + '/c.bin', 'rb').read()
GOHAN = 0x4F8 + REC
check('outfit: no bad jumps on cancel', 'bad pc' not in o)
check('story: a story form change overrides the worn outfit (green to school)', c[GOHAN + FORM] == 10)
check('outfit: B restores school uniform and keeps Goku', c[GOHAN + FORM] == 10 and c[0] == 0)
skills = list(c[GOHAN + 0x0D:GOHAN + 0x0D + c[GOHAN + 0x0C]])
sel = '%08x' % (0x03001560 + REC + 0x15)
ss = ss_form = forms['gohan_orange_ss']
o = run(rom, pick + ['tap A 150', 'run 100', 'dump e 03001068 8a8', 'poke8 %s %02x' % (sel, skills.index(20)), 'run 5', 'keys B', 'run 12', 'keys', 'run 300',
                    'shot ss', 'dump f 03001068 8a8', 'tap A 10', 'run 40', 'keys B', 'run 12', 'keys', 'run 300', 'keys B', 'run 12', 'keys', 'run 500', 'shot back', 'dump g 03001068 8a8'], d)   # up to Super Saiyan 2, then back down
check('outfit: no bad jumps through transforming', 'bad pc' not in o)
check('outfit: A keeps orange gi as Gohan', open(d + '/e.bin', 'rb').read()[GOHAN + FORM] == 13)
check('outfit: Super Saiyan uses the new row', open(d + '/f.bin', 'rb').read()[GOHAN + FORM] == ss)
check('outfit: turning back returns to orange gi', open(d + '/g.bin', 'rb').read()[GOHAN + FORM] == 13)

# Great Saiyaman stays a skill and returns to the outfit Gohan wore. Locked outfits are skipped.
s18 = skills.index(18)
def use(n): return ['poke8 %s %02x' % (sel, s18), 'run 5', 'keys B', 'run 12', 'keys', 'run 300', 'dump ' + n + ' 03001068 8a8']
o = run(rom, pick + ['tap A 150', 'run 100'] + use('h') + ['shot saiyaman'] + use('i') + ['shot unsaiyaman'], d)
h = open(d + '/h.bin', 'rb').read()[GOHAN + FORM]; i = open(d + '/i.bin', 'rb').read()[GOHAN + FORM]
check('saiyaman: no bad jumps', 'bad pc' not in o)
check('saiyaman: costume on from the orange gi', h == forms['saiyaman_from_orange'])
check('saiyaman: costume off returns to the orange gi', i == 13)
# A save from before Nov 12 with Gohan in the Saiyan armor (Teen Gohan's now), or in Great Saiyaman over it: the Switch screen puts him in his first
# open look, played or not; out of play the party's sync does it.
arm = '%08x' % (0x03001068 + GOHAN + FORM)
for f_ in ('gohan_armor', 'gohan_armor_ss2', 'saiyaman_from_armor'):
    o = run(rom, ['guardon 0x09000000'] + route + ['poke8 %s %02x' % (arm, forms[f_]), 'run 2', 'tap A 60', 'tap A 60', 'run 30', 'dump j 03001068 8a8', 'tap B 150', 'run 60', 'dump k 03001068 8a8'], d)
    j = open(d + '/j.bin', 'rb').read(); k = open(d + '/k.bin', 'rb').read()
    check('old save, Gohan in %s: the Switch screen gives him his school uniform' % f_, 'bad pc' not in o and j[GOHAN + FORM] == 10 and k[GOHAN + FORM] == 10)
TRUNKS = 0x4F8 + 3 * REC                         # and Trunks in the armor (Future Trunks's since Nov 12): his green gi (form 21)
for f_ in ('trunks_armor', 'trunks_armor_ss2'):
    o = run(rom, ['guardon 0x09000000'] + route + ['poke8 %08x %02x' % (0x03001068 + TRUNKS + FORM, forms[f_]), 'run 2', 'tap A 60', 'tap A 60', 'run 30', 'dump j 03001068 8a8', 'tap B 150', 'run 60'], d)
    j = open(d + '/j.bin', 'rb').read()
    check('old save, Trunks in %s: the Switch screen gives him his green gi' % f_, 'bad pc' not in o and j[TRUNKS + FORM] == 21)
# (the route ends in a conversation, where the field's play code doesn't run: the Switch screen opened and cancelled first puts Goku in play)
o = run(rom, ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30', 'tap B 150', 'run 60', 'poke8 %s %02x' % (arm, forms['gohan_armor']), 'run 600', 'dump j 03001068 8a8'], d)
j = open(d + '/j.bin', 'rb').read()
check('old save, Gohan in the armor while Goku plays: back in his school uniform within 10 s', 'bad pc' not in o and j[0] == 0 and j[GOHAN + FORM] == 10)
flag_byte = lambda f: '%08x' % (0x03001068 + 0x55 + f // 8)
lock = [x for x in pick if x not in ('tap DOWN 30', 'shot outfit')]
at = lock.index('tap RIGHT 40')
lock[at:at] = ['poke8 %s 00' % flag_byte(858)]
o = run(rom, lock + ['tap DOWN 30', 'tap DOWN 30', 'tap A 150', 'run 100', 'dump j 03001068 8a8'], d)
print('flag byte value test')
j = open(d + '/j.bin', 'rb').read()
check('unlocks: locked outfits are skipped (only the GT looks are left: a debug build opens them)', j[GOHAN + FORM] == forms['gohan_gt_noglasses'])

# Saiyan armor: each outfit transforms and returns, attacks, and uses beam skills without hanging. Scrolling keeps sprites inside the frame.
for who, char, rights, key, base, ss in (('TeenGohan', 8, 5, 'DOWN', 'gohan_armor', 'gohan_armor_ss'), ('FutureTrunks', 8, 5, 'DOWN', 'trunks_armor', 'trunks_armor_ss'), ('Vegeta', 4, 3, 'DOWN', 'vegeta_armor', 'vegeta_armor_ss'),
                                        ('TeenGohanGi', 8, 5, 'DOWN', 'teen_gohan', 'teen_gohan_ss')):
    presses = [o_['form'] for o_ in json.load(open('ultimate/outfits.json'))['characters'][str(char)]].index(base)    # the armor's place on the list
    rec = 0x03001560 + REC * char
    pk = ['poke8 %08x %02x' % (rec + 0x0C, 3), 'poke8 %08x %02x' % (rec + 0x0D, 20), 'poke8 %08x %02x' % (rec + 0x0E, 15), 'poke8 %08x %02x' % (rec + 0x0F, 10)]
    def skill(n): return ['poke8 %08x %02x' % (rec + 0x15, n), 'run 5', 'keys B', 'run 12', 'keys', 'run 200']
    lines = ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * rights + ['tap %s 30' % key] * presses + ['tap A 150', 'run 100'] + pk + ['dump k 03001068 8a8', 'shot armor_' + who] + skill(0) + ['dump l 03001068 8a8', 'shot armorss_' + who, 'tap A 8', 'run 30'] + skill(1) + skill(2) + skill(0) + ['run 100'] + skill(0) + ['run 300', 'dump m 03001068 8a8', 'tap A 8', 'run 30', 'keys R', 'run 20', 'keys', 'run 20']
    o = run(rom, lines, d)
    at = 0x4F8 + REC * char + FORM
    check('armor %s: no bad jumps' % who, 'bad pc' not in o)
    check('armor %s: worn' % who, open(d + '/k.bin', 'rb').read()[at] == forms[base])
    check('armor %s: Super Saiyan' % who, open(d + '/l.bin', 'rb').read()[at] == forms[ss])
    check('armor %s: back to armor' % who, open(d + '/m.bin', 'rb').read()[at] == forms[base])

# Charged melee: hold A, release. Measured against a Bomber placed beside the player; every character must survive it.
base = [l for l in open('tools/harness/enemy_test.txt').read().split('\n') if l and not l.startswith('#') and not l.startswith('mem ') and not l.startswith('shot ') and l not in ('tap B 20', 'run 200')]
ENEMY_HP, ENEMY_X, ENEMY_Y, PX = '0202d558', '0202d46c', '0202d470', '0202ce1c'
erom = OUT + '/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
run_txt = run(erom, base + ['mem %s 2' % PX], d)
m = re.search(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % PX, run_txt)
x, y = int(m.group(1), 16), int(m.group(2), 16)
place = ['poke %s %x' % (ENEMY_X, x - (18 << 8)), 'poke %s %x' % (ENEMY_Y, y)]
o = run(erom, ['guardon 0x09000000'] + base + place + ['run 1', 'mem %s 1' % ENEMY_HP, 'keys A', 'run 160'] + place + ['mem %s 1' % ENEMY_HP, 'keys'] + ['run 1', 'mem %s 1' % ENEMY_HP] * 15 + ['run 200', 'shot charged_kill', 'tap A 25', 'run 30'], d)
hp = [(lambda v: v - (1 << 32) if v >= 1 << 31 else v)(int(v, 16)) >> 10 for v in re.findall(r'mem %s: ([0-9a-f]+)' % ENEMY_HP, o)]
hp = hp[:2] + [next((v for v in hp[2:] if v != hp[1]), hp[1])]   # the first change after release: a beaten enemy's memory is soon reused, so later readings mean nothing
print('enemy HP readings', hp)
check('charged: no bad jumps', 'bad pc' not in o)
check('charged: release hurts the enemy', hp[2] < hp[1])
check('charged: stronger than the normal hit before it', hp[1] - hp[2] > hp[0] - hp[1] > 0)
# Super Saiyan 2 hits 1.5x as hard as Super Saiyan, punches and ki. The Bomber waits out of reach during the transformations (it blows itself up near the player). The first press after the walk-in only waits (it was eaten while the EEPROM was writing: tools/harness/enemy_test.txt).
def dmg(presses, blast, wait, form=None, swap=None):
    R_ = 0x03001560; away = ['poke %s %x' % (ENEMY_X, x + (120 << 8)), 'poke %s %x' % (ENEMY_Y, y)]
    L = base + ['poke8 %08X 05' % (R_ + 0x0C)] + ['poke8 %08X %02X' % (R_ + 0x0D + i_, v_) for i_, v_ in enumerate((7, 20, 22, 35, 36))] + ['run %d' % wait]     # slots: 1 SS, 2 SS3, 3 SS2, 4 SS4
    if form is not None: L += ['poke8 %08X %02X' % (R_ + 0x14, form)]           # another look of Goku's (GT Kid Goku) before the presses
    for i_, p_ in enumerate(presses):    # the first press only waits: see tools/harness/enemy_test.txt (it went while the EEPROM was writing)
        L += ['poke8 %08X %02X' % (R_ + 0x15, p_), 'poke8 %08X FF' % (R_ + 0x1A), 'poke8 %08X 03' % (R_ + 0x1B)] + (['keys B', 'run 2', 'keys'] if i_ else ['run 2']) + [v for _ in range(8) for v in away + ['run 30']]
    if swap is not None: L += ['poke8 %08X %02X' % (R_ + 0x14, swap)]           # the form the damage scale reads, on the actor the presses loaded
    o_ = run(erom, L + ['mem %s 2' % PX], d); m_ = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % PX, o_)[-1]
    px, py = int(m_[0], 16), int(m_[1], 16); near = ['poke %s %x' % (ENEMY_X, px - ((40 if blast else 18) << 8)), 'poke %s %x' % (ENEMY_Y, py)]
    L += away + ['run 1', 'poke %s %x' % (ENEMY_HP, 9000 << 10), 'keys LEFT', 'run 2', 'keys', 'run 2']     # the Bomber punches back if it arrives early
    m_ = re.findall(r'mem %s: ([0-9a-f]+) ([0-9a-f]+)' % PX, run(erom, L + ['mem %s 2' % PX], d))[-1]     # the step left covers more ground in the faster forms
    near = ['poke %s %x' % (ENEMY_X, int(m_[0], 16) - ((40 if blast else 18) << 8)), 'poke %s %x' % (ENEMY_Y, int(m_[1], 16))]; L += near
    L += (['poke8 %08X 00' % (R_ + 0x15), 'poke8 %08X FF' % (R_ + 0x1A), 'keys B', 'run 2', 'keys'] + [v for _ in range(6) for v in near + ['run 6']] if blast else ['keys A'] + [v for _ in range(5) for v in near + ['run 2']] + ['keys'] + near + ['run 12'])
    o_ = run(erom, L + ['mem %s 1' % ENEMY_HP, 'mem %08X 1' % (R_ + 0x14)], d)
    return 9000 - int(re.findall(r'mem %s: ([0-9a-f]+)' % ENEMY_HP, o_)[-1], 16) / 1024, int(re.findall(r'mem %08x: ([0-9a-f]+)' % (R_ + 0x14), o_)[-1], 16) & 255
def samples(presses, blast, want, form=None):
    """Three readings at different waits, each one where the presses reached the form `want`. Since the flash save (Nov 12) the Bomber is up
    some 110 frames sooner (tools/harness/enemy_test.txt), and at some waits one of his bombs catches Goku just as he presses, so the press
    does nothing: such a reading is dropped and the next wait tried. A form never reached leaves readings of (0, -1), which fail."""
    got = []
    for w_ in (1, 4, 7, 10, 13, 16, 19):
        v_ = dmg(presses, blast, w_, form)
        if v_[1] == want: got.append(v_)
        if len(got) == 3: break
    return got + [(0, -1)] * (3 - len(got))
for kind, blast_ in (('punch', 0), ('ki blast', 1)):
    a_ = samples([1, 1], blast_, 4); b_ = samples([1, 1, 3], blast_, forms['goku_ss2_b'])
    print(kind, 'Super Saiyan', a_, 'Super Saiyan 2', b_)
    c_ = samples([1, 1, 3, 2], blast_, 6)
    print(kind, 'Super Saiyan 3', c_)
    lo, hi, top = min(v for v, _ in a_), min(v for v, _ in b_), min(v for v, _ in c_)
    check('Super Saiyan 2 %s is about 1.5x Super Saiyan' % kind, all(f_ == 4 for _, f_ in a_) and all(f_ == forms['goku_ss2_b'] for _, f_ in b_) and lo > 0 and 1.3 < hi / lo < 1.7)
    check('Super Saiyan 3 %s is about 1.75x Super Saiyan' % kind, all(f_ == 6 for _, f_ in c_) and lo > 0 and (1.55 < top / lo < 1.95 or 1.55 < top / lo / 1.5 < 1.95))   # a critical hit is 1.5x again
    # GT Kid Goku: Super Saiyan, then Super Saiyan 3 pressed twice is Super Saiyan 4, 2.5x Super Saiyan's damage
    k1 = samples([1, 1], blast_, forms['kid_goku_ssj'], forms['kid_goku']); k4 = samples([1, 1, 2, 4], blast_, forms['kid_goku_ssj4'], forms['kid_goku'])
    print(kind, 'Kid Super Saiyan', k1, 'Kid Super Saiyan 4', k4)
    lo_, s4 = min(v for v, _ in k1), min(v for v, _ in k4)
    check('Kid Goku Super Saiyan 4 %s is about 2.5x his Super Saiyan' % kind, all(f_ == forms['kid_goku_ssj'] for _, f_ in k1) and all(f_ == forms['kid_goku_ssj4'] for _, f_ in k4) and lo_ > 0 and (2.25 < s4 / lo_ < 2.75 or 2.25 < s4 / lo_ / 1.5 < 2.75))
    # Gogeta's Super Saiyan 4 hits 3x as hard as his form would without the boost. The scale goes by the form, so on one loaded actor (Kid
    # Goku's Super Saiyan 4, with his strikes and stats) the form is set to Gogeta's, then to plain Kid Goku's (no boost, and neither is
    # Super Saiyan 3's class, so the stats are the same): the ratio is the boost alone. His own moves are test_gt's.
    g4 = [dmg([1, 1, 2, 4], blast_, w_, forms['kid_goku'], forms['gogeta_ssj4']) for w_ in (1, 4, 7)]
    g1 = [dmg([1, 1, 2, 4], blast_, w_, forms['kid_goku'], forms['kid_goku']) for w_ in (1, 4, 7)]
    print(kind, 'Gogeta Super Saiyan 4', g4, 'unboosted', g1)
    check('Gogeta Super Saiyan 4 %s is 3x unboosted' % kind, all(f_ == forms['gogeta_ssj4'] for _, f_ in g4) and min(v for v, _ in g1) > 0 and any(2.7 < a[0] / b[0] < 3.3 for a, b in zip(g4, g1)))
for name, rights in (('Goku', 0), ('Gohan', 1), ('Trunks', 2), ('Vegeta', 3), ('Vegito', 4), ('Broly', 5)):
    o = run(rom, ['guardon 0x09000000'] + route + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * rights + ['tap A 150', 'run 100', 'keys A', 'run 80', 'shot hold_' + name, 'keys', 'run 3', 'shot hit_' + name, 'run 40', 'tap A 20', 'dump n 03001068 8a8'], d)
    check('charged %s: no bad jumps' % name, 'bad pc' not in o)
print('screens in', d)
sys.exit(1 if fails else 0)
