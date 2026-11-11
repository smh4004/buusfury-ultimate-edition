#!/usr/bin/env python3
"""Hyperbolic Time Chamber. Needs a zone debug build whose official warps to Mr. Popo:
  BFU_HUB_WARP="6, 1, 1, 288, 500" BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_chamber.py <dir> [work dir]
Talks to Mr. Popo after the ending, spars with every partner on the list in turn, and checks the fight, the reduced EXP, the way back and Broly's lock."""
import json, os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, floorcheck, barcheck
from PIL import Image
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='chamber'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
FLOOR = floorcheck.Floor(ROM)        # a talk's teleport onto a wall stops the test (lib/floorcheck.py)
G = 0x03001068; PLAYER = 0x03001C34; ENEMIES = 0x03001BB4; AT = 0x0300197C; REC0 = 0x03001560
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
WALK_IN = 150    # frames after the zone 26 door until Goku's walk into West City is over (about 117; 110 left two frames, Nov 9)
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
env = dict(os.environ); env.pop('HARNESS_SAV', None)
p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', D], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
bad = [False]
def send(*ls):
    for l in ls: p.stdin.write(l + '\n')
    p.stdin.flush()
def mem(a, n=1):
    send('mem %08X %d' % (a, n))
    while True:
        l = p.stdout.readline()
        if not l: raise SystemExit('harness ended')
        if 'bad pc' in l: bad[0] = True
        if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
BAR = barcheck.Bar(open(ROM, 'rb').read(), mem)
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, (mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8)
def talk(x, y):
    FLOOR.guard(at(), x, y + 22, 'Goku')
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80')
at = lambda: mem(AT)[0] & 0xFFFF
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run %d' % WALK_IN); mem(G)
talk(96, 328); send('run 200'); mem(G)
send(flag_on(883)); talk(*zone26.HUB_AT); send('run 200', 'shot lookout'); mem(G)
check('the rig lands on the Lookout', at() == (1 << 8 | 6))
send(*['poke8 %08X 96' % (REC0 + o) for o in (0x28, 0x29, 0x2A, 0x2B)], 'poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17))
names = []; rooms = []
room = zone26.spar_first()
W = Image.new('RGB', (8 * 240, 8 * 160)); cell = 0
def sheet(tag):
    global cell
    send('shot ' + tag); mem(G)
    if cell < 64 and not tag.startswith('s2_'): W.paste(Image.open('%s/%s.png' % (D, tag)).convert('RGB'), (cell % 8 * 240, cell // 8 * 160)); cell += 1
exp = []
for c, (cat, people) in enumerate(zone26.SPAR):
    if os.environ.get('ONLY') and str(c) not in os.environ['ONLY']: room += len(people); continue
    for k, (name, row, char) in enumerate(people):
        if name == 'Broly':
            pass
        def pick():
            talk(288, 472); send('run 220')
            if c == 0 and k == 0: sheet('popo_hello')
            send('tap A 20', 'run 100')                           # past his greeting: the categories
            if c == 0 and k == 0: sheet('popo_menu')
            if c >= 3:
                send(*['tap DOWN 12'] * 3, 'tap A 20', 'run 100')
                if c == 3 and k == 0: sheet('popo_more')
                send(*['tap DOWN 12'] * (c - 3), 'tap A 20', 'run 100')
            else: send(*['tap DOWN 12'] * c, 'tap A 20', 'run 100')
            if k == 0: sheet('popo_cat%d' % c)
            send(*['tap DOWN 12'] * k, 'tap A 20', 'run 160')
        pick()
        if name == 'Broly' and not mem(G + 0x55 + 111 // 8)[0] >> (111 % 8) & 1:
            sheet('locked'); check('Broly stays locked until his story fight', at() == (1 << 8 | 6)); send('tap A 20', 'run 60'); send(flag_on(111)); pick()
        check('%s: into the Chamber' % name, at() == (room << 8 | 26))
        seen = barcheck.expect(BAR, send, name, tries=90, full=True)     # the boss bar (outfit.c bossbar)
        check('%s: his bar is up and full: %s' % (name, seen[1]), seen[0])
        sheet('s_' + name.replace(' ', ''))
        e0 = mem(REC0 + 0x24)[0]
        send('run 60')
        sheet('s2_' + name.replace(' ', ''))
        for attempt in range(14):
            if at() != (room << 8 | 26) or not mem(0x03001BB0)[0]: break
            foe = mem(ENEMIES)[0]; x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]
            send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17))
            send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)), 'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 40')
        send('shot end_' + name.replace(' ', '')); mem(G)
        for _ in range(14):
            send('run 180', 'tap A 20')                       # a level-up message waits for A
            if at() == (1 << 8 | 6): break
        send('run 60')
        exp.append((name, mem(REC0 + 0x24)[0] - e0))
        check('%s: the win comes back to the Lookout, rested' % name, at() == (1 << 8 | 6))
        room += 1
print(exp)
# Waves: a group's four in a row with no rest; the first clear gives stat points, a later one Zenie.
FLAGS2 = 0x0203F1E2
def more(n): a = FLAGS2 + (n - 32) // 8; return mem(a & ~3)[0] >> (8 * (a & 3) + n % 8) & 1
for c, (cat, people) in enumerate(list(zone26.SPAR) + [zone26.SPAR[0]]):
    c %= len(zone26.SPAR); again = more(zone26.MORE_WAVE + c)
    talk(288, 472); send('run 220', 'tap A 20', 'run 100', *['tap DOWN 12'] * 3, 'tap A 20', 'run 100', *['tap DOWN 12'] * 3, 'tap A 20', 'run 100')
    if c == 0 and not again: sheet('waves_say')
    send('tap A 20', 'run 100')
    if c == 0 and not again: sheet('waves_menu')
    send(*(['tap DOWN 12'] * c if c < 3 else ['tap DOWN 12'] * 3 + ['tap A 20', 'run 100'] + ['tap DOWN 12'] * (c - 3)), 'tap A 20', 'run 160')
    pts0, z0 = mem(REC0 + 0x2C)[0] & 255, mem(0x0300155C)[0]
    ok = True
    for k, (name, row, char) in enumerate(people):
        room = zone26.challenge_room('wave%d' % c, k)
        for _ in range(10):
            if at() == (room << 8 | 26) and mem(ENEMIES)[0]: break
            send('run 60')
        ok &= at() == (room << 8 | 26)
        if k == 0: sheet('wave%d_%s' % (c, 'again' if again else 'first'))
        for attempt in range(30):                        # some story foes (Buu with Gotenks) don't show in the enemy count: go by the list and the room
            if at() != (room << 8 | 26): break
            foe = mem(ENEMIES)[0]
            if not foe: send('run 60'); continue
            x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]
            send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17))
            send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)), 'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 40')
        ok &= at() != (room << 8 | 26)
    check('wave %s: all four rooms in turn' % cat, ok)
    for _ in range(14):
        send('run 180', 'tap A 20')
        if at() == (1 << 8 | 6): break
    send('run 60')
    check('wave %s: back to the Lookout' % cat, at() == (1 << 8 | 6))
    pts, z = mem(REC0 + 0x2C)[0] & 255, mem(0x0300155C)[0]
    print('   wave %s: points %d -> %d, Zenie %d -> %d' % (cat, pts0, pts, z0, z))       # level-ups on the way add their own points
    if again: check('wave %s again: %d Zenie' % (cat, zone26.WAVE_ZENIE), z - z0 >= zone26.WAVE_ZENIE)
    else: check('wave %s: first clear gives %d stat points and marks it' % (cat, zone26.WAVE_POINTS), pts - pts0 >= zone26.WAVE_POINTS and more(zone26.MORE_WAVE + c) == 1)
# Losing: no game over, back to the Lookout rested, and the next fight works.
def lose(tag):
    room = zone26.spar_first() + 10                              # Kid Buu hits hard and often
    talk(288, 472); send('run 220', 'tap A 20', 'run 100', 'tap DOWN 12', 'tap DOWN 12', 'tap A 20', 'run 100', 'tap DOWN 12', 'tap DOWN 12', 'tap A 20', 'run 160')
    check('%s: in the Chamber' % tag, at() == (room << 8 | 26))
    for k in range(40):
        if at() != (room << 8 | 26) or (k and mem(REC0 + 0x16)[0] & 0xFFFF == 0): break
        foe = mem(ENEMIES)[0]; x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]
        send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (24 << 8)), 'run 200')
    for w in range(30):
        send('run 100')
        if at() == (1 << 8 | 6): break
    send('run 700'); sheet('lost_' + tag)      # past the few seconds after which a mistake here would show the game over
    check('%s: a lost fight comes back to the Lookout, not a game over' % tag, at() == (1 << 8 | 6))
    hp = mem(REC0 + 0x16)[0]
    check('%s: rested' % tag, hp & 0xFFFF > 1)
lose('first'); lose('again')
check('partners pay EXP', any(v > 0 for _, v in exp))
check('no bad jumps', not bad[0])
W.save(D + '/chamber.png'); p.stdin.close()
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', D)
