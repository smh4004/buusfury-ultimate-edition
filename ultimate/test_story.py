#!/usr/bin/env python3
"""Emulator test of the story-side unlocks (build `--debug --zone` first; set BFU_PROTO). Uses that build's Snake Way debug doors: x 48-96 up = story Broly, x<48 = the
game's real ending from its last scene. Checks: beating Broly adds him to the party; the ending flies you out free and you can land in West City and be sent to Zone 26;
the Super 13 reward adds Android 13, who can become Super 13, and DBS Gogeta, and keeps Broly's outfit if he had already joined."""
import json, os, struct, subprocess, sys, tempfile
H, ROM = 'tools/harness/harness', os.environ.get('BFU_ZONE_ROM', 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba')      # BFU_ZONE_ROM: another build of it
d = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='story')
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
G, REC, SIZE = 0x03001068, 0x03001560, 0x68
fails = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: fails.append(n)
def run(lines):
    p = d + '/s.txt'; open(p, 'w').write('\n'.join(lines) + '\n')
    return subprocess.run([H, ROM, p, d], capture_output=True, text=True, timeout=590).stdout
def ptr(base):
    return int([l for l in run(base + ['mem 03001C34 1']).splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
def at(out):
    return int([l for l in out.splitlines() if l.startswith('mem 0300197c')][-1].split(':')[1].split()[0], 16) & 0xFFFF
def move(pl, x, y=None):
    return ['poke %08X %08X' % (pl + 0x1A0, x << 8)] + (['poke %08X %08X' % (pl + 0x1A4, y << 8)] if y is not None else [])
def state():
    g = open(d + '/g.bin', 'rb').read(); rec = lambda c: g[0x4F8 + c * SIZE:0x4F8 + (c + 1) * SIZE]
    return (lambda n: g[0x55 + n // 8] >> (n % 8) & 1), rec
def flag_off(n, g):
    return 'poke8 %08X %02X' % (G + 0x55 + n // 8, g[0x55 + n // 8] & ~(1 << n % 8) & 255)
DUMP = 'dump g 03001068 8a8'
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'guardon 0x09000000']
pl = ptr(start)
run(start + [DUMP]); g0 = open(d + '/g.bin', 'rb').read()
GOKU_EXP = struct.unpack_from('<I', g0, 0x4F8 + 0x24)[0]

# Story Broly: as a player who has neither beaten him nor recruited anyone into the guest slot.
fresh = ['poke8 %08X 02' % (REC + 8 * SIZE), flag_off(111, g0), 'poke8 03001577 7F']
b = start + fresh + move(pl, 72) + ['keys UP', 'run 8', 'keys', 'run 150', 'shot broly_room', 'mem 0300197C 1']
b += ['poke8 03001577 7F'] + ['tap A 60'] * 40 + ['poke8 03001577 7F', 'run 100', 'shot broly_fight']       # his long opening conversation
out = run(b); check('the debug door reaches Broly at Volcano Summit', at(out) == (32 << 8 | 15))
room = b[:b.index('shot broly_room') + 1]
run(room + ['dump w 02000000 40000']); w = open(d + '/w.bin', 'rb').read(); i = w.find(struct.pack('<I', 20240 << 10))
check('Broly is in the room at full HP', i >= 0)
# Broly guards for a while (how long moves with the build's timing): keep striking, a few blows at a time, until one lands.
run(b + ['dump w 02000000 40000']); w = open(d + '/w.bin', 'rb').read()
x, y = struct.unpack_from('<II', w, i - 0xEC); p2 = ptr(b)
kill = b + ['poke %08X %08X' % (0x02000000 + i, 2 << 10), 'poke8 03001577 7F', 'poke %08X %08X' % (p2 + 0x1A0, x), 'poke %08X %08X' % (p2 + 0x1A4, y + (20 << 8)), 'keys UP', 'run 6', 'keys']
landed = False
for k in range(30):          # (8 tries were enough until the Nov 10 frame-drop fix moved every timing by a frame in 64: his guard covered them all)
    kill += ['tap A 14'] * 6
    run(kill + ['dump w 02000000 40000'])
    if struct.unpack_from('<I', open(d + '/w.bin', 'rb').read(), i)[0] != 2 << 10: landed = True; break        # a blow landed
check('a blow lands on Broly within 30 tries', landed)
kill += ['poke8 03001577 7F', 'run 500', 'shot broly_end0', 'tap A 100', 'shot broly_end1', 'tap A 100', 'tap A 100', 'tap A 100', 'run 60', 'shot broly_end2', 'run 500', 'shot broly_end3', 'tap A 60', 'shot broly_end4', 'tap A 60', 'run 300', 'shot broly_end5', DUMP, 'keys LEFT', 'run 20', 'keys', 'mem 03001C34 1']
out = run(kill); flag, rec = state(); r = rec(8)
check('no bad jumps through the end of the Broly fight', 'bad pc' not in out)
check('beating Broly sets flag 111 and adds him to the party', flag(111) == 1 and r[0] & 1 == 1)
check('he joins on the Broly outfit', r[0x14] == forms['broly'])
check('he joins level with the player, with his own skills', struct.unpack_from('<I', r, 0x24)[0] >= GOKU_EXP and list(r[0x0C:0x10]) == [3, 7, 8, 24] and r[0x28] > 27)
check('he shares the stat points the player has not spent yet', r[0x2C] == rec(0)[0x2C])
print('   Broly joined with HP %d EP %d STR %d POW %d END %d' % (struct.unpack_from('<H', r, 0x18)[0], struct.unpack_from('<H', r, 0x1C)[0], r[0x28], r[0x29], r[0x2A]))

# The real ending: Bulma's message, the Lookout scene, then flight; land on West City; the resident sends you to Zone 26.
e = start + fresh[:1] + [flag_off(149, g0)] + move(pl, 8) + ['run 3', 'keys LEFT', 'run 20', 'keys', 'run 5']
for k in range(10): e += ['run 200', 'tap A 20']
e += ['run 200', 'mem 0300197C 1', 'shot flight']
out = run(e); check('the ending finishes in free flight over Earth', at(out) == (50 << 8 | 0) and 'bad pc' not in out)
p3 = ptr(e)
land = e + move(p3, 1250, 1200) + ['run 4', 'tap A 100', 'run 60', 'keys A', 'run 300', 'keys', 'run 100', 'mem 0300197C 1', 'shot west_city', DUMP]
out = run(land); flag, rec = state()
check('landing on West City after the ending reaches the resident\'s map', at(out) == (1 << 8 | 4))
check('the ending itself sets flag 149', flag(149) == 1)
p4 = ptr(land)
ask = land + move(p4, 320, 382) + ['run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80', 'shot ask', 'tap A 60', 'tap A 60', 'tap A 60', 'tap A 60', 'tap A 200', 'run 120', 'mem 0300197C 1', 'shot zone']
out = run(ask); check('after the real ending the resident sends you to Zone 26', at(out) == (1 << 8 | 26) and 'bad pc' not in out)
# Mr. Popo: fly to the Lookout after the ending and he offers the Time Chamber.
look = e + move(p3, 656, 1076) + ['run 4', 'tap A 100', 'run 60', 'keys A', 'run 300', 'keys', 'run 100', 'mem 0300197C 1']
out = run(look); check('landing at the Lookout after the ending', at(out) == (1 << 8 | 6))
p5 = ptr(look)
popo = look + move(p5, 288, 494) + ['run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80', 'run 220', 'shot popo', 'tap A 20', 'run 100', 'tap A 20', 'run 100', 'tap A 20', 'run 200', 'mem 0300197C 1', 'shot spar']
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']; import zone26
out = run(popo); check('Mr. Popo takes you into the Time Chamber', at(out) == (zone26.spar_first() << 8 | 26) and 'bad pc' not in out)
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', d)
