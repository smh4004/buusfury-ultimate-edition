#!/usr/bin/env python3
"""Cell Games: from the Challenge Board through the four fights to the prize. Build `--debug --zone` first.
  python3 ultimate/test_cell.py [work dir]"""
import json, os, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, floorcheck
from PIL import Image
ROM = 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
FLOOR = floorcheck.Floor(ROM)        # a talk's teleport onto a wall stops the test (lib/floorcheck.py)
D = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='cell'); os.makedirs(D, exist_ok=True)
G = 0x03001068; PLAYER = 0x03001C34; ENEMIES = 0x03001BB4; COUNT = 0x03001BB0; AT = 0x0300197C; REC0 = 0x03001560; ZENIE = 0x0300155C
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
        if 'bad pc' in l: bad[0] = True; print(l.strip()[:160], flush=True)
        if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, (mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8)
flag = lambda n: mem(G + 0x55 + n // 8)[0] >> (n % 8) & 1
at = lambda: mem(AT)[0] & 0xFFFF
def talk(x, y):
    FLOOR.guard(at(), x, y + 22, 'Goku')
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80')
strong = lambda: ['poke8 %08X 96' % (REC0 + o) for o in (0x28, 0x29, 0x2A, 0x2B)] + ['poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17)]
W = Image.new('RGB', (6 * 240, 5 * 160)); cell = [0]
def sheet(tag):
    send('shot ' + tag); mem(G)
    if cell[0] < 30: W.paste(Image.open('%s/%s.png' % (D, tag)).convert('RGB'), (cell[0] % 6 * 240, cell[0] // 6 * 160)); cell[0] += 1
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run %d' % WALK_IN); mem(G)
talk(96, 328); send('run 200'); mem(G)
send(flag_on(883)); send(*strong())
talk(*zone26.HUB_AT); send('run 150', 'tap A 20', 'run 80'); sheet('board')
send('tap DOWN 12', 'tap DOWN 12', 'tap DOWN 12', 'tap A 20', 'run 80'); sheet('more')
send('tap A 20', 'run 200'); sheet('cell_say')
send('tap A 20', 'run 150')
rooms = sorted({c[0] for c in zone26.cell_rows()})
for k, room in enumerate(rooms):
    check('fight %d is in its room' % (k + 1), at() == (room << 8 | 26))
    send(*strong()); sheet('f%d_a' % k)
    n = mem(COUNT)[0]
    check('fight %d has %d fighter(s)' % (k + 1, sum(1 for c in zone26.cell_rows() if c[0] == room)), n == sum(1 for c in zone26.cell_rows() if c[0] == room))
    for direction in ('DOWN', 'LEFT', 'RIGHT', 'UP'):
        pl = mem(PLAYER)[0]; foe = mem(ENEMIES)[0]; x, y = mem(foe + 0x1A0, 2)
        send(*strong(), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (70 << 8)), 'run 60')
    sheet('f%d_b' % k)
    send('run 90', *strong()); sheet('f%d_c' % k)
    for attempt in range(60):
        if at() != (room << 8 | 26) or not mem(COUNT)[0]: break
        foe = mem(ENEMIES)[0]; x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]
        send(*strong(), 'poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)), 'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 30')
    for w in range(14):
        send('run 160', 'tap A 20')
        if at() != (room << 8 | 26): break
    send('run 60')
check('the last fall brings you home', at() == (1 << 8 | 3))
check('and the flag is set', flag(zone26.CELL_WON) == 1)
z0 = mem(ZENIE)[0]
talk(*zone26.HUB_AT); send('run 200'); sheet('prize'); send('tap A 20', 'run 60')
check('the board pays the prize', mem(ZENIE)[0] - z0 == zone26.CELL_PRIZE and flag(zone26.CELL_PAID) == 1)
check('no bad jumps', not bad[0])
W.save(D + '/cell.png'); p.stdin.close()
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', D)
