#!/usr/bin/env python3
"""Emulator test for Zone 26 (build `--debug --zone` first; set BFU_PROTO). From Snake Way (debug door) plays every door both ways,
then the Super 13 fight and its reward, and the West City resident who starts the quest."""
import json, os, re, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
H, ROM = 'tools/harness/harness', 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
PROTO = os.environ['BFU_PROTO']; P = open(PROTO, 'rb').read()
cfg = json.load(open('ultimate/zone26.json'))
masks = {a: zone26.floor_mask(P, PROTO, a) for a in range(1, 16)}
D = zone26.links(cfg, masks)
fails = []
def check(n, ok):
    print(('PASS ' if ok else 'FAIL ') + n)
    if not ok: fails.append(n)
d = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='z26')
def run(lines):
    p = d + '/s.txt'; open(p, 'w').write('\n'.join(lines) + '\n')
    return subprocess.run([H, ROM, p, d], capture_output=True, text=True, timeout=500).stdout
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
AT = '0300197C'; KEYS = 'DOWN UP LEFT RIGHT'.split()
PL, BOSS_PL = 0x0202E8E4, 0x0202E238   # the player object: where it lives in a plain room and with Android 13 loaded
def go(lines, door, pl, tag, settle=110):     # out to West City: settle=150 (Goku's walk-in takes about 117 frames; Nov 9)
    x0, y0, x1, y1 = door['rect']
    lines += ['poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, ((y0 + y1) // 2) << 8),
              'keys ' + KEYS[door['key']], 'run 12', 'keys', 'run %d' % settle, 'mem %s 1' % AT, 'shot ' + tag]
lines = list(start); moves = []; seen = set()
def walk(a):
    for door in D[a]:
        b = door['to']
        if 'world' in door or (a, b) in seen: continue
        seen.update(((a, b), (b, a))); moves.append((a, b)); go(lines, door, BOSS_PL if a == 15 else PL, 'm%02d' % len(moves))
        walk(b)
        back = [x for x in D[b] if x['to'] == a][0]; moves.append((b, a)); go(lines, back, BOSS_PL if b == 15 else PL, 'm%02d' % len(moves))
walk(1)
out = run(lines); got = [int(l.split(':')[1].split()[0], 16) for l in out.splitlines() if l.startswith('mem 0300197c')]
bad = [(m, hex(g)) for m, g in zip(moves, got) if (g & 255, g >> 8 & 255) != (26, m[1])]
check('all %d door moves land in the right room' % len(moves), len(got) == len(moves) and not bad)
if bad: print(bad)
check('no bad jumps through the zone', 'bad pc' not in out)

def talk_at(base, x, y):
    pl = int([l for l in run(base + ['mem 03001C34 1']).splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
    return base + ['poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80']
HUB = 0x0103
def hub_talk(base):
    """Debug: the West City tournament resident takes you to Hercule City (flag 660), then talk to the official on the Challenge Board."""
    return talk_at(talk_at(base + ['poke8 %08X %02X' % (0x03001068 + 0x55 + 862 // 8, 1 << 862 % 8)], 96, 328) + ['run 200'], *zone26.HUB_AT)
def talk_to(base):
    """He wanders later, so right after arriving he's still at his spawn: stand just below him and press A."""
    pl = int([l for l in run(base + ['mem 03001C34 1']).splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
    return base + ['poke %08X %08X' % (pl + 0x1A0, 320 << 8), 'poke %08X %08X' % (pl + 0x1A4, 382 << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80']


route = list(start)
for a in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14):
    nxt = {8: 10}.get(a, a + 1); go(route, [x for x in D[a] if x['to'] == nxt and 'world' not in x][0], PL, 'r%02d' % a)
def ptr(base):
    return int([l for l in run(base + ['mem 03001C34 1']).splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
def boss(base, hp):
    run(base + ['dump w 02000000 40000']); w = open(d + '/w.bin', 'rb').read(); i = w.find(struct.pack('<I', hp << 10))
    return (0x02000000 + i, ) + struct.unpack_from('<II', w, i - 0xEC) if i >= 0 else (None, 0, 0)
def kill(base, hp):
    """Leave the boss 2 HP, stand below it and punch."""
    pl = ptr(base); a, x, y = boss(base, hp)
    return base + ['poke %08X %08X' % (a, 2 << 10), 'poke8 03001577 7F', 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)),
                   'keys UP', 'run 6', 'keys', 'tap A 14', 'tap A 14', 'tap A 14']
def at(out):
    return int([l for l in out.splitlines() if l.startswith('mem 0300197c')][-1].split(':')[1].split()[0], 16) & 0xFFFF
base = route + ['run 30', 'shot arena']
hp1 = boss(base, 30000)[0]; check('Android 13 is in the arena with 30000 HP', hp1 is not None)
phase = kill(base, 30000) + ['poke8 03001577 7F'] + ['tap A 25'] * 11 + ['shot absorb0', 'tap A 41', 'shot absorb1', 'run 30', 'shot absorb2', 'run 30', 'shot absorb3', 'run 70', 'shot change', 'mem 0300197C 1']
out = run(phase); check('beating Android 13 starts his change', at(out) == (16 << 8 | 26))
two = phase + ['shot change_say', 'tap A 60', 'tap A 60', 'tap A 60', 'run 300', 'keys UP', 'run 60', 'keys', 'run 120', 'shot phase2', 'mem 0300197C 1']
out = run(two); check('walking up to him starts phase two', at(out) == (17 << 8 | 26))
hp2 = boss(two, 75000)[0]; check('Super 13 has 75000 HP', hp2 is not None)
end = kill(two, 75000) + ['poke8 03001577 7F'] + ['tap A 30'] * 16 + ['shot struggle'] + ['keys A', 'run 5', 'keys', 'run 5'] * 60      # A 6 times a second: a person can (build.py MASH_PATCHES)
end += ['shot bomb', 'run 500', 'shot home_after', 'mem 0300197C 1', 'tap A 40', 'keys LEFT', 'run 10', 'keys', 'dump g 03001068 8a8']
out = run(end); g = open(d + '/g.bin', 'rb').read(); flag = lambda n: g[0x55 + n // 8] >> (n % 8) & 1; g_flag_off = g[0x55 + 149 // 8] & ~(1 << 149 % 8)
check('no bad jumps through the whole fight', 'bad pc' not in out)
check('beating Super 13 plays the finish and sets flag 621', flag(882) == 1 and flag(886) == 1)
check('the finish returns you to West City', at(out) == 0x0104)
talk = lambda b: talk_to(b)
home = end[:end.index('tap A 40')]
# Join state as in a real game: neither Gogeta nor the guest yet (debug joins the guest at the start), and so Broly's story fight not won
# either (flag 111): with it set and the guest slot empty, skills_sync's story_sync joins Broly there (a save from the original game), every
# 64 frames, and whether one of those came between the poke and the reward depended on the frame count (Nov 9: it did after the Great Ape).
no_broly = 'poke8 %08X %02X' % (0x03001068 + 0x55 + 111 // 8, g[0x55 + 111 // 8] & ~(1 << 111 % 8))
# The reward's unlocks (Nov 11, the owner's list): Full Power Broly (876), Android 13 (877), Androids 17 and 18 (880). The Saiyan armor
# (873-875) and Future Trunks (879) are the Cell Games' now, Piccolo, Krillin and Videl the tournament's, and Gogeta no longer joins
# here (878: his own unlocks, below). A debug build starts with every outfit flag set, so all eight are cleared first.
def clear(*flags):
    by = {}
    for f in flags: by[f // 8] = by.get(f // 8, g[0x55 + f // 8]) & ~(1 << f % 8)
    return ['poke8 %08X %02X' % (0x03001068 + 0x55 + k, v) for k, v in by.items()]
reward = talk(home + ['poke8 %08X 02' % (0x03001560 + 8 * 0x68), no_broly] + clear(*range(873, 881), 883)) + ['shot said', 'tap A 60', 'shot said2'] + ['tap A 60'] * 7 + ['run 60', 'shot after', 'dump g 03001068 8a8']
out = run(reward); g = open(d + '/g.bin', 'rb').read()
print('   reward flags 873-880, 883:', [flag(n) for n in list(range(873, 881)) + [883]])
check('the resident gives the rewards: Full Power Broly, Android 13, Androids 17 and 18', all(flag(n) for n in (876, 877, 880, 883)))
check('and no longer the Saiyan armor, Future Trunks or Gogeta (the Cell Games\' and the exhibits\' now)', not any(flag(n) for n in (873, 874, 875, 878, 879)))
forms = json.load(open('ultimate/out/BFU_debug_zone.map.json'))['forms']; rec = lambda c: g[0x4F8 + c * 0x68:0x4F8 + (c + 1) * 0x68]
check('the reward adds Android 13 to the party', rec(8)[0] & 1 == 1 and rec(8)[0x14] == forms['android13'])
check('joining as Android 13, the guest has SS Deadly Bomber, not Eraser Cannon, and can become Super 13', list(rec(8)[0x0C:0x12]) == [5, 7, 8, 25, 29, 30])
check('Gohan learns Special Beam Cannon from the reward', 26 in list(rec(1)[0x0D:0x0D + rec(1)[0x0C]]))
# Gogeta's own unlocks (outfit.c story_sync, after the ending): his slot joins the first time one of his looks is open, wearing it. A debug
# build has every look past flag 2000 open (DBS, SSB, Super Saiyan 4), so with the original's flag (878) clear he joins as DBS Gogeta;
# with all 15 Z-Fighter exhibits in the museum (their count is the four flags from 346) the original's flag comes on, and a Gogeta not
# yet joined joins as the original game's (form 41).
EX = (346, 347, 348, 349)
unjoin = 'poke8 %08X 02' % (0x03001560 + 7 * 0x68)
out = run(home + clear(878, *EX) + [unjoin, 'run 200', 'dump g 03001068 8a8']); g = open(d + '/g.bin', 'rb').read()
check('Gogeta joins by himself once one of his looks is open (a debug build: DBS Gogeta), with his moves and both transformations',
      rec(7)[0] & 1 == 1 and rec(7)[0x14] == forms['gogeta_dbs'] and list(rec(7)[0x0C:0x12]) == [5, 7, 3, 5, 20, 44] and not flag(878))
on = lambda *flags: ['poke8 %08X %02X' % (0x03001068 + 0x55 + k, v) for k, v in {f // 8: g[0x55 + f // 8] | sum(1 << x % 8 for x in flags if x // 8 == f // 8) for f in flags}.items()]
out = run(home + clear(878) + on(*EX) + [unjoin, 'run 200', 'dump g 03001068 8a8']); g = open(d + '/g.bin', 'rb').read()
check('all 15 Z-Fighter exhibits open the original game\'s Gogeta (flag 878), and he joins wearing it', flag(878) == 1 and rec(7)[0] & 1 == 1 and rec(7)[0x14] == 41)
out = run(home + clear(878) + on(346, 347, 348) + clear(349) + ['run 200', 'dump g 03001068 8a8']); g = open(d + '/g.bin', 'rb').read()
check('fourteen exhibits don\'t', flag(878) == 0)
print('   Gogeta joined at', list(rec(7)[0x28:0x2B]), 'guest at', list(rec(8)[0x28:0x2B]))

# Start of the quest: from 26:1's road back to West City, walk up to the same resident, get sent in.
intro = list(start); go(intro, [x for x in D[1] if 'world' in x][0], PL, 'home', settle=150)
intro = talk(intro) + ['shot ask', 'tap A 60', 'shot ask2', 'tap A 60', 'shot ask3', 'tap A 60', 'tap A 60', 'tap A 200', 'run 120', 'mem %s 1' % AT, 'shot zone']
out = run(intro); ats = [l for l in out.splitlines() if l.startswith('mem 0300197c')]
check('the resident sends you to Zone 26 once the game is beaten', int(ats[-1].split(':')[1].split()[0], 16) & 0xFFFF == 0x011A)

# Boss Rush: once Super 13 is beaten the resident offers it. Nine bosses in a row, then the reward back in West City.
flag_on = lambda n: 'poke8 %08X %02X' % (0x03001068 + 0x55 + n // 8, 1 << n % 8)
rush = list(start); go(rush, [x for x in D[1] if 'world' in x][0], PL, 'rhome', settle=150)
rush = hub_talk(rush + [flag_on(883)]) + ['poke8 03001588 96', 'poke8 03001589 96', 'poke8 0300158A 96', 'poke8 0300158B 96', 'poke8 03001576 FF', 'poke8 03001577 7F', 'run 150', 'tap A 150', 'shot board', 'tap A 200', 'tap A 200', 'run 120', 'mem %s 1' % AT, 'shot rush0']
out = run(rush); check('the resident offers the Boss Rush and sends you to its first room', at(out) == (zone26.RUSH_FIRST << 8 | 26))
def boss_any(base):
    """The living boss after the test has already cut its HP."""
    run(base + ['dump w 02000000 40000']); w = open(d + '/w.bin', 'rb').read(); best = (None, 0, 0)
    for i in range(0x28C, len(w) - 4, 4):
        v = struct.unpack_from('<i', w, i)[0]
        if 0 < v <= 64 << 10 and struct.unpack_from('<I', w, i - 0x28C)[0] == 0x0804C484:
            best = (0x02000000 + i, ) + struct.unpack_from('<II', w, i - 0xEC)
    return best
def rush_boss(base, hp):
    """The boss by its class and HP, allowing for the test's strong Goku landing stray punches on the way in."""
    run(base + ['dump w 02000000 40000']); w = open(d + '/w.bin', 'rb').read(); best = (None, 0, 0)
    for i in range(0x28C, len(w) - 4, 4):
        v = struct.unpack_from('<i', w, i)[0]
        if (hp // 2) << 10 < v <= hp << 10 and struct.unpack_from('<I', w, i - 0x28C)[0] == 0x0804C484:
            best = (0x02000000 + i, ) + struct.unpack_from('<II', w, i - 0xEC)
    return best
for k, _ in enumerate(zone26.RUSH):
    hp = zone26.RUSH_HP[k]
    here = at(run(rush + ['mem %s 1' % AT]))
    found = rush_boss(rush, hp)
    check('Boss Rush fight %d is there with %d HP' % (k + 1, hp), found[0] is not None)
    if found[0] is None: break
    # The bosses move and teleport, so look again and try again until the room changes. Going down here would end at the title screen, whose A presses start a new game, so his HP is kept up in both places it lives.
    for attempt in range(12):
        found = rush_boss(rush, hp)
        if found[0] is None: found = boss_any(rush)
        if found[0] is None:         # already beaten and on its way out: dismiss any boxes and wait
            rush = rush + ['tap A 30'] * 4 + ['run 200', 'mem %s 1' % AT]; out = run(rush)
            if 'bad pc' in out or at(out) != here: break
            continue
        a_, x_, y_ = found; pl_ = ptr(rush)
        heal = ['poke8 03001577 7F']
        near = ['poke %08X %08X' % (pl_ + 0x1A0, x_), 'poke %08X %08X' % (pl_ + 0x1A4, y_ + (20 << 8))]
        rush = rush + heal + ['poke %08X %08X' % (a_, 2 << 10)] + near + ['keys UP', 'run 3', 'keys', 'tap A 14'] + heal + ['tap A 30'] * 6 + heal + ['run 150', 'mem %s 1' % AT]
        out = run(rush)
        if 'bad pc' in out or at(out) != here: break
    print('   fight %d took %d tries' % (k + 1, attempt + 1))
    run(rush + ['shot rush%d' % (k + 1)])
    if k < len(zone26.RUSH) - 1: check('beating it moves on to the next room', 'bad pc' not in out and at(out) == ((zone26.RUSH_FIRST + k + 1) << 8 | 26))
check('beating the last one brings you back to the board', at(out) == HUB)
done = talk_at(rush + ['poke8 %08X %02X' % (0x03001068 + 0x55 + 888 // 8, 1 << 888 % 8)], *zone26.HUB_AT) + ['shot rushtalk', 'tap A 60', 'tap A 60', 'tap A 60', 'tap A 60', 'run 60', 'shot rushdone', 'dump g 03001068 8a8']
out = run(done); g = open(d + '/g.bin', 'rb').read()
check('the board pays the reward', flag(887) == 1 and 'bad pc' not in out)
out = run(done + ['mem 0203F00C 1']); more = int([l for l in out.splitlines() if l.startswith('mem 0203f00c')][-1].split()[-1], 16)
check('the Boss Rush earns a rank, and its message is over', more >> 8 & 7 in (1, 2, 3, 4) and not more >> 7 & 1)
again = talk_at(done, *zone26.HUB_AT) + ['shot rushagain', 'run 150', 'tap A 150', 'tap A 200', 'tap A 200', 'run 120', 'mem %s 1' % AT]
out = run(again); check('after the reward the board still offers the Boss Rush', at(out) == (zone26.RUSH_FIRST << 8 | 26))
print('rush screens in', d)

# World Tournament: first walk every opponent in turn (flag TOUR_ORDERED), then check that a real entry draws at random.
tour = list(start); go(tour, [x for x in D[1] if 'world' in x][0], PL, 'thome', settle=150)
strong = ['poke8 03001588 96', 'poke8 03001589 96', 'poke8 0300158A 96', 'poke8 0300158B 96', 'poke8 03001576 FF', 'poke8 03001577 7F']
home = list(tour); first = zone26.tour_first(); pool1 = len(zone26.TOUR_POOLS[0])
drawn = set()
TO_MENU = ['run 150', 'tap A 150', 'tap DOWN 12', 'tap A 150']       # past the greeting, down to World Tournament: the bracket menu is on screen
def pick_rival(place):
    """A menu shows three opponents and More: the second page has the other three and Back."""
    page = ['run 120', 'tap A 120']      # past the round's opening line
    if place >= 3: page += ['tap DOWN 12'] * 3 + ['tap A 120']
    return page + ['tap DOWN 12'] * (place % 3) + ['tap A 150']
menu = hub_talk(home + [flag_on(883)] + strong) + TO_MENU
check('Not now stays by the board', at(run(menu + ['tap DOWN 12', 'tap DOWN 12', 'tap A 120', 'run 60', 'shot tournot', 'mem %s 1' % AT])) == HUB)
check('B leaves the menu', at(run(menu + ['tap B 120', 'run 60', 'mem %s 1' % AT])) == HUB)
check('Back returns to the first page', at(run(menu + ['tap DOWN 12', 'tap A 120', 'run 120', 'tap A 120'] + ['tap DOWN 12'] * 3 + ['tap A 120'] + ['tap DOWN 12'] * 3 + ['tap A 120', 'tap B 120', 'run 60', 'mem %s 1' % AT])) == HUB)
for wait in (1, 37, 91, 143, 211, 277):
    o_ = hub_talk(home + ['run %d' % wait, flag_on(883)] + strong) + TO_MENU + ['tap A 200', 'run 120', 'mem %s 1' % AT]
    drawn.add(at(run(o_)))
print('   first-round rooms drawn', sorted(hex(v) for v in drawn))
check('entering draws a first-round opponent at random', len(drawn) >= 2 and all(first <= v >> 8 < first + pool1 and v & 255 == 26 for v in drawn))
tour = hub_talk(home + [flag_on(883), 'poke8 %08X %02X' % (0x03001068 + 0x55 + zone26.TOUR_ORDERED // 8, 1 << zone26.TOUR_ORDERED % 8)] + strong) + ['shot tourboard'] + TO_MENU + ['shot tourmenu', 'tap A 200', 'run 120', 'mem %s 1' % AT, 'mem 0300155C 1', 'shot tour0']
out = run(tour)
check('the resident sends you to the World Tournament', at(out) == (first << 8 | 26))
before = int([l for l in out.splitlines() if l.startswith('mem 0300155c')][-1].split()[-1], 16)
everyone = zone26.tour_list()
for k, (rnd, place, row, _) in enumerate(everyone):
    hp = zone26.TOUR_HP[rnd] + 10 * place
    here = at(run(tour + ['mem %s 1' % AT])); found = rush_boss(tour, hp)
    check('tournament opponent %d (enemy row %d) is there with %d HP' % (k + 1, row, hp), found[0] is not None)
    if found[0] is None: break
    for attempt in range(12):
        found = rush_boss(tour, hp)
        if found[0] is None: found = boss_any(tour)
        if found[0] is None:
            tour = tour + ['tap A 30'] * 4 + ['run 200', 'mem %s 1' % AT]; out = run(tour)
            if 'bad pc' in out or at(out) != here: break
            continue
        a_, x_, y_ = found; pl_ = ptr(tour)
        heal = ['poke8 03001577 7F']
        near = ['poke %08X %08X' % (pl_ + 0x1A0, x_), 'poke %08X %08X' % (pl_ + 0x1A4, y_ + (20 << 8))]
        tour = tour + heal + ['poke %08X %08X' % (a_, 2 << 10)] + near + ['keys UP', 'run 3', 'keys', 'tap A 14'] + heal + ['tap A 30'] * 6 + heal + ['run 150', 'mem %s 1' % AT]
        out = run(tour)
        if 'bad pc' in out or at(out) != here: break
    print('   opponent %d took %d tries' % (k + 1, attempt + 1))
    run(tour + ['shot tour%d' % (k + 1)])
    if k < len(everyone) - 1: check('beating them moves on', 'bad pc' not in out and at(out) == ((first + k + 1) << 8 | 26))
check('winning the final brings you back to the board', at(out) == HUB)
said = talk_at(tour + ['mem 0300155C 1'], *zone26.HUB_AT) + ['shot tourwon', 'tap A 60', 'tap A 60', 'tap A 60', 'tap A 60', 'run 60', 'dump g 03001068 8a8']
out = run(said); g = open(d + '/g.bin', 'rb').read()
paid = int([l for l in out.splitlines() if l.startswith('mem 0300155c')][-1].split()[-1], 16)
print('   zenie', before, paid)
check('the tournament pays its prize', paid - before >= zone26.TOUR_PRIZE)
check('the board congratulates you once', flag(890) == 1 and 'bad pc' not in out)

# A picked bracket: the second page of round one, the first of round two and the last place of the final (Super 13).
wanted = (4, 2, 5)
pick = hub_talk(home + [flag_on(883)] + strong) + TO_MENU + ['tap DOWN 12', 'tap A 120']
for w in wanted: pick += pick_rival(w)
pick += ['run 120', 'mem %s 1' % AT, 'shot pick0']
out = run(pick)
for rnd, place in enumerate(wanted):
    room = first + sum(len(p) for p in zone26.TOUR_POOLS[:rnd]) + place
    check('round %d is the picked opponent' % (rnd + 1), at(out) == (room << 8 | 26))
    hp = zone26.TOUR_HP[rnd] + 10 * place
    for attempt in range(12):
        found = rush_boss(pick, hp)
        if found[0] is None: found = boss_any(pick)
        if found[0] is None:
            pick = pick + ['tap A 30'] * 4 + ['run 200', 'mem %s 1' % AT]; out = run(pick)
            if 'bad pc' in out or at(out) != room << 8 | 26: break
            continue
        a_, x_, y_ = found; pl_ = ptr(pick)
        heal = ['poke8 03001577 7F']
        near = ['poke %08X %08X' % (pl_ + 0x1A0, x_), 'poke %08X %08X' % (pl_ + 0x1A4, y_ + (20 << 8))]
        pick = pick + heal + ['poke %08X %08X' % (a_, 2 << 10)] + near + ['keys UP', 'run 3', 'keys', 'tap A 14'] + heal + ['tap A 30'] * 6 + heal + ['run 150', 'mem %s 1' % AT]
        out = run(pick)
        if 'bad pc' in out or at(out) != room << 8 | 26: break
    print('   picked opponent %d took %d tries' % (rnd + 1, attempt + 1))
check('winning a picked bracket brings you back to the board', at(out) == HUB)

# Trials: each is one fight as a set hero. Back at the board it pays, and all four earn the rare prize.
SLOT_NAMES = {0: 'Goku', 1: 'Gohan', 2: 'Goten', 3: 'Trunks', 4: 'Vegeta'}      # party slots (the save's records)
check('each trial names the hero it plays (party slot)', all(SLOT_NAMES[t[0]] == t[1] for t in zone26.TRIALS + zone26.TRIALS2))
trial = hub_talk(home + [flag_on(883)] + strong) + ['run 150', 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'run 150', 'tap A 150', 'shot trials', 'tap B 120', 'run 60']
tf = zone26.trial_first()
for k, t in enumerate(zone26.TRIALS):
    trial = talk_at(trial, *zone26.HUB_AT) + ['run 150', 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'run 150', 'tap A 150'] + ['tap DOWN 12'] * k + ['tap A 200', 'run 120', 'mem %s 1' % AT, 'mem 03001068 1', 'shot trial%d' % k]
    out = run(trial)
    check('trial %d is the right room' % (k + 1), at(out) == ((tf + k) << 8 | 26))
    who = [l for l in out.splitlines() if l.startswith('mem 03001068')][-1].split(':')[1].split()[0]
    check('trial %d makes %s the player' % (k + 1, t[1]), int(who, 16) & 255 == t[0])
    room = (tf + k) << 8 | 26
    for attempt in range(12):
        found = rush_boss(trial, zone26.TRIAL_HP)
        if found[0] is None: found = boss_any(trial)
        if found[0] is None:
            trial = trial + ['tap A 30'] * 4 + ['run 200', 'mem %s 1' % AT]; out = run(trial)
            if 'bad pc' in out or at(out) != room: break
            continue
        a_, x_, y_ = found; pl_ = ptr(trial)
        rec_ = 0x03001560 + t[0] * 0x68 + 0x17
        heal = ['poke8 %08X 7F' % rec_]
        near = ['poke %08X %08X' % (pl_ + 0x1A0, x_), 'poke %08X %08X' % (pl_ + 0x1A4, y_ + (20 << 8))]
        trial = trial + heal + ['poke %08X %08X' % (a_, 2 << 10)] + near + ['keys UP', 'run 3', 'keys', 'tap A 14'] + heal + ['tap A 30'] * 6 + heal + ['run 150', 'mem %s 1' % AT]
        out = run(trial)
        if 'bad pc' in out or at(out) != room: break
    print('   trial %d took %d tries' % (k + 1, attempt + 1))
    check('winning trial %d brings you back to the board' % (k + 1), at(out) == HUB and 'bad pc' not in out)
    trial = talk_at(trial + ['mem 0300155C 1'], *zone26.HUB_AT) + ['shot trialpay%d' % k, 'run 150', 'tap A 120', 'run 30', 'mem 0300155C 1', 'dump g 03001068 8a8'] + (['shot tien', 'tap A 120', 'run 30', 'mem 0203F00C 1'] if k == 0 else [])
    out = run(trial); g = open(d + '/g.bin', 'rb').read()
    if k == 0: check('the first trial won brings Tien', int([l for l in out.splitlines() if l.startswith('mem 0203f00c')][-1].split()[-1], 16) >> zone26.MORE_TIEN & 1 == 1)
    z = [int(l.split()[-1], 16) for l in out.splitlines() if l.startswith('mem 0300155c')]
    check('trial %d pays 30,000 Zenie at the board' % (k + 1), flag(zone26.TRIAL_PAID + k) == 1 and z[-1] - z[-2] == zone26.TRIAL_PRIZE)
    gear = struct.unpack_from('<%dI' % struct.unpack_from('<I', g, 0xE4)[0], g, 0xE8)
    check('trial %d gives the %s' % (k + 1, t[6]), t[5] in gear)
all4 = talk_at(trial, *zone26.HUB_AT) + ['shot trialall', 'run 150', 'tap A 120', 'run 30', 'dump g 03001068 8a8']
out = run(all4); g = open(d + '/g.bin', 'rb').read()
check('all four trials earn the ten Senzu Beans', flag(zone26.TRIAL_ALL) == 1 and g[2 + zone26.TRIAL_ITEM] >= zone26.TRIAL_ITEMS)
check('all four trials earn the Geromantium Bandana', zone26.TRIAL_GEAR in struct.unpack_from('<%dI' % struct.unpack_from('<I', g, 0xE4)[0], g, 0xE8))


# Spirit Bomb: Goku has it in this build (skill 19). Select it, use it next to Super 13, and it should hurt him and spend energy.
# Its slot: wherever he holds it (the skill book adds Kaioken to his skills, so the order varies)
held = bytes.fromhex(''.join(int(v, 16).to_bytes(4, 'little').hex() for v in [l for l in run(route + ['run 30', 'mem 03001560 6']).splitlines() if l.startswith('mem 03001560')][-1].split(':')[1].split()))
held = list(held[0x0D:0x0D + held[0x0C]]); print('   Goku holds', held)
a13, x, y = boss(route + ['run 30'], 30000); hpa = a13
sb = route + ['run 30', 'poke %08X %08X' % (BOSS_PL + 0x1A0, x), 'poke %08X %08X' % (BOSS_PL + 0x1A4, y + (64 << 8)), 'keys UP', 'run 4', 'keys', 'run 4',
              'poke8 03001575 %d' % held.index(19), 'poke8 0300157B 00', 'poke8 0300157A 64', 'poke8 03001577 7F', 'mem 03001578 2', 'tap B 10', 'mem %08X 1' % hpa]
for i, n in enumerate((40, 40, 40, 30, 30, 20, 20, 30)):
    sb += ['poke8 03001577 7F', 'run %d' % n, 'shot sb%d' % i]
sb += ['mem %08X 1' % hpa, 'mem 03001578 2', 'mem 0203FF40 1']
out = run(sb); mems = [l for l in out.splitlines() if l.startswith('mem')]
left = lambda l: int(l.split(':')[1].split()[0], 16)
check('no bad jumps with the Spirit Bomb', 'bad pc' not in out)
hps = [m for m in mems if m.startswith('mem %08x' % hpa)]
check('the Spirit Bomb hits hard', len(hps) >= 2 and left(hps[-1]) < left(hps[0]) - (800 << 10))
print('bomb memory', mems[-1], hps)
check('the Spirit Bomb finishes', left(mems[-1]) >> 16 == 0)

# The Z-Mart's front door works too, and opens onto the game's own shop.
shop = list(start)
for a in (1,):
    go(shop, [x for x in D[a] if x['to'] == 2 and 'world' not in x][0], PL, 'to2')
go(shop, [x for x in D[2] if 'world' in x][0], PL, 'shop', settle=150)
out = run(shop); ats = [l for l in out.splitlines() if l.startswith('mem 0300197c')]
check("the Z-Mart door opens the shop in its own copy of the room", int(ats[-1].split(':')[1].split()[0], 16) & 0xFFFF == zone26.building_room() << 8 | 26)

# Before the ending (flag 149 clear) he still only talks about ghosts: no way in.
early = list(start); go(early, [x for x in D[1] if 'world' in x][0], PL, 'home2')
early += ['poke8 %08X %02X' % (0x03001068 + 0x55 + 149 // 8, g_flag_off)]
early = talk(early) + ['shot ghost', 'tap A 60', 'tap A 60', 'tap A 60', 'run 120', 'mem %s 1' % AT]
out = run(early); ats = [l for l in out.splitlines() if l.startswith('mem 0300197c')]
check('before the ending he stays a normal resident', int(ats[-1].split(':')[1].split()[0], 16) & 0xFFFF == 0x0104)
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', d)
