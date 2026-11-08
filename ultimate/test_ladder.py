#!/usr/bin/env python3
"""Tournament brackets, Endless, Hercule's dare, the race and museum rewards, and who they unlock (build `--debug --zone` first; set BFU_PROTO).
  python3 ultimate/test_ladder.py <work dir>"""
import json, os, subprocess, sys
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
D = sys.argv[1]; os.makedirs(D, exist_ok=True)
ROM = 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
G, AT, PLAYER, ENEMIES, REC0, ZENIE, BENCH_FLAGS = 0x03001068, 0x0300197C, 0x03001C34, 0x03001BB4, 0x03001560, 0x0300155C, 0x0203F00C
HUB = 1 << 8 | 3
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
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, (mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8)
more = lambda n: mem(BENCH_FLAGS + (n >> 3 & ~3))[0] >> ((n & 31)) & 1
def more_poke(n, v):
    a = BENCH_FLAGS + n // 8; old = mem(a & ~3)[0] >> (8 * (a & 3)) & 255
    send('poke8 %08X %02X' % (a, old | 1 << n % 8 if v else old & ~(1 << n % 8) & 255))
at = lambda: mem(AT)[0] & 0xFFFF
zenie = lambda: mem(ZENIE)[0]
def talk(x, y):
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80')
strong = lambda: send(*['poke8 %08X 96' % (REC0 + o) for o in (0x28, 0x29, 0x2A, 0x2B)], 'poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17))
def hub_talk(): strong(); talk(*zone26.HUB_AT); send('run 150')
def dismiss(n=2):
    """Past n lines, then B out of the board's menu. Another A here would talk to him again and pick a challenge."""
    for _ in range(n): send('tap A 60')
    send('tap B 60', 'tap B 60', 'tap B 60', 'run 60'); mem(G)
def beat(room):
    """Leave the opponent 2 HP, stand below it and punch, until the room changes."""
    for attempt in range(14):
        if at() != room << 8 | 26: return True
        foe = mem(ENEMIES)[0]
        if foe:
            x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]
            send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17))
            send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)), 'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 40')
        else: send('tap A 30', 'run 120')
    return at() != room << 8 | 26
def settle(want, tries=20):
    for _ in range(tries):
        send('run 150', 'tap A 20')                           # a level-up message waits for A
        if at() == want: return True
    return False
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x and x['to'] != zone26.building_room()][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run 110'); mem(G)
talk(96, 328); send('run 200'); mem(G)
check('the rig reaches Hercule City', at() == HUB)
for n in range(4): more_poke(n, 0)
send(flag_on(883)); mem(G)
send('shot board0')

# The bracket menu only appears once Normal is won.
hub_talk(); send('tap A 150', 'shot menu', 'tap DOWN 12', 'tap A 150', 'shot before_win', 'tap B 120', 'run 60')
check('before a win there is no bracket choice: B leaves from the old menu', at() == HUB)
send(flag_on(890)); more_poke(zone26.MORE_YAMCHA, 1); mem(G)

# Hard: a bracket of three, on its own rooms.
z0 = zenie(); first = zone26.tier_first(1)
hub_talk(); send('tap A 150', 'tap DOWN 12', 'tap A 150', 'shot tiers', 'tap DOWN 12', 'tap A 150', 'shot hard_mode', 'tap A 200', 'run 150', 'shot hard1')
room = at() >> 8
check('Hard: first opponent in its own rooms (room %d)' % room, first <= room < first + 6)
for rnd in range(3):
    size = sum(len(q) for q in zone26.TOUR_POOLS[:rnd]); r = at() >> 8
    check('Hard round %d is in the right rooms' % (rnd + 1), first + size <= r < first + size + 6)
    foe = mem(ENEMIES)[0]; hp = mem(foe + 0x28C)[0] >> 10
    check('Hard round %d has its HP (%d)' % (rnd + 1, hp), zone26.TIER_HP[0][rnd] <= hp <= zone26.TIER_HP[0][rnd] + 50)
    if not beat(r): check('Hard round %d: beaten' % (rnd + 1), False); break
    if rnd < 2: settle(lambda: 0) if False else None; [send('run 100') for _ in range(2)]; mem(G)
check('Hard: winning comes home', settle(HUB))
check('Hard: pays 300,000', zenie() - z0 >= zone26.HARD_PRIZE)
check('Hard: flag set', more(zone26.MORE_HARD) == 1)
strong(); talk(*zone26.HUB_AT); send('run 100', 'shot hard_won'); dismiss(2)
check('Hard: Pikkon unlocked', more(zone26.MORE_PIKKON) == 1)

# Endless: each win pays more, a loss comes home with the money, and the best is kept.
z0 = zenie()
hub_talk(); send('tap A 150', 'tap DOWN 12', 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'shot endless', 'tap A 200', 'run 200', 'shot endless1')
room = at() >> 8
check('Endless: starts in a Normal round (room %d)' % room, zone26.tier_first(0) <= room < zone26.tier_first(0) + 18)
paid = [zenie()]
rooms = [room]
for k in range(13):
    r = at() >> 8
    if not beat(r): check('Endless fight %d beaten' % (k + 1), False); break
    for _ in range(12):
        send('run 100', 'tap A 20')
        if at() >> 8 != r and at() & 255 == 26 and mem(ENEMIES)[0]: break
    rooms.append(at() >> 8); paid.append(zenie())
    if k < 12: send('run 60')
print('   rooms', rooms)
print('   paid', [b - a for a, b in zip(paid, paid[1:])])
check('Endless: each win pays more', all(b - a == (i + 1) * zone26.ENDLESS_STEP for i, (a, b) in enumerate(zip(paid, paid[1:]))))
check('Endless: later fights use the harder rooms', any(zone26.tier_first(1) <= r < zone26.tier_first(2) for r in rooms) and rooms[-1] >= zone26.tier_first(2))
# Lose: no game over, home, money kept.
money = zenie()
for k in range(60):
    if at() == HUB or (k and mem(REC0 + 0x16)[0] & 0xFFFF == 0): break
    foe = mem(ENEMIES)[0]
    if foe:
        x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]
        send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (24 << 8)), 'run 120')
    else: send('run 120')
for _ in range(30):
    send('run 100')
    if at() == HUB: break
send('run 700', 'shot endless_lost')
check('Endless: a lost fight comes home, not a game over', at() == HUB)
check('Endless: rested', mem(REC0 + 0x16)[0] & 0xFFFF > 1)
check('Endless: keeps the money', zenie() >= money)
strong(); talk(*zone26.HUB_AT); send('run 60', 'shot endless_done'); dismiss(2)
check('Endless: best run saved', mem(BENCH_FLAGS)[0] >> 16 & 255 == 13)

# Hercule's dare: on the second page.
hub_talk(); send('tap A 150', *['tap DOWN 12'] * 3, 'tap A 150', 'shot more', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'shot challengers', 'tap A 150', 'shot dare', 'tap A 200', 'run 200', 'shot hercule')
check("Hercule's dare: into his room", at() == zone26.hercule_room() << 8 | 26)
foe = mem(ENEMIES)[0]; check("Hercule's dare: he has %d HP" % zone26.HERCULE_HP, mem(foe + 0x28C)[0] >> 10 == zone26.HERCULE_HP)
check("Hercule's dare: beaten", beat(zone26.hercule_room()))
check("Hercule's dare: comes home", settle(HUB))
strong(); talk(*zone26.HUB_AT); send('run 60', 'shot herc_won'); dismiss(2)
check('Hercule unlocked', more(zone26.MORE_HERCULE) == 1)

# Goku Black: Challengers, second line, once the Hard bracket is won. Black, then Rose in her own room with your health as it was.
check('Goku Black: not joined yet', more(zone26.MORE_BLACK) == 0)
hub_talk(); send('tap A 150', *['tap DOWN 12'] * 3, 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'tap DOWN 12', 'tap A 150', 'shot black', 'tap A 200', 'run 200', 'shot black_room')
check('Goku Black: into his room', at() == zone26.black_room(0) << 8 | 26)
foe = mem(ENEMIES)[0]; check('Goku Black: he has %d HP' % zone26.BLACK_FIGHT[0][1], mem(foe + 0x28C)[0] >> 10 == zone26.BLACK_FIGHT[0][1])
check('Goku Black: beaten', beat(zone26.black_room(0)))
for _ in range(12):
    send('run 60')
    if at() == zone26.black_room(1) << 8 | 26 and mem(ENEMIES)[0]: break
send('run 60', 'shot rose_room')
check('Rose comes on in the next room', at() == zone26.black_room(1) << 8 | 26)
foe = mem(ENEMIES)[0]; check('Rose has %d HP' % zone26.BLACK_FIGHT[1][1], foe and mem(foe + 0x28C)[0] >> 10 == zone26.BLACK_FIGHT[1][1])
check('Rose: beaten', beat(zone26.black_room(1)))
check('Rose: comes home', settle(HUB))
check('the win is waiting to be told', more(zone26.MORE_BLACK_WON) == 1)
strong(); talk(*zone26.HUB_AT); send('run 60', 'shot black_won'); send('tap A 60', 'run 30', 'shot black_joins'); dismiss(1)
check('Goku Black joins', more(zone26.MORE_BLACK) == 1 and more(zone26.MORE_BLACK_WON) == 0)

# Race and museum.
z0 = zenie(); send(flag_on(234)); mem(G)
hub_talk(); send('shot race_won'); dismiss(2)
check('Race: pays once', zenie() - z0 == zone26.RACE_PRIZE and more(zone26.MORE_RACE) == 1)
z0 = zenie(); hub_talk(); dismiss(1)
check('Race: not twice', zenie() == z0)
def bits(start, n, v):
    for i in range(n):
        a = G + 0x55 + (start + i) // 8; b = mem(a & ~3)[0] >> (8 * (a & 3)) & 255; m = 1 << (start + i) % 8
        send('poke8 %08X %02X' % (a, b | m if v >> i & 1 else b & ~m & 255))
    mem(G)
bits(341, 5, 24); bits(346, 4, 15)
z0 = zenie(); hub_talk(); send('shot not_yet'); dismiss(1)
check('Museum: 24 of 25 pays nothing', zenie() == z0)
bits(341, 5, 25)
z0 = zenie(); i0 = mem(G + 2 + zone26.MUSEUM_ITEM & ~3)[0]; hub_talk(); send('shot museum'); dismiss(2)
check('Museum: pays a million once complete', zenie() - z0 == zone26.MUSEUM_PRIZE and more(zone26.MORE_MUSEUM) == 1)
z0 = zenie(); hub_talk(); dismiss(1)
check('Museum: not twice', zenie() == z0)
# The Rewards page shows the numbers.
hub_talk(); send('tap A 150', *['tap DOWN 12'] * 3, 'tap A 150', 'tap DOWN 12', 'tap A 150')
for k in range(9): send('run 40', 'shot rew%d' % k, 'tap A 30')
send('run 60'); mem(G)
check('no bad jumps', not bad[0])
send('shot end'); p.stdin.close(); p.wait(20)
print('FAILED:' if fails else 'all passed', fails or '')
sys.exit(1 if fails else 0)
