#!/usr/bin/env python3
"""Tournament brackets, Endless, Hercule's dare, the race and museum rewards, and who they unlock (build `--debug --zone` first; set BFU_PROTO).
  python3 ultimate/test_ladder.py <work dir>"""
import json, os, subprocess, sys
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, floorcheck
D = sys.argv[1]; os.makedirs(D, exist_ok=True)
ROM = 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
FLOOR = floorcheck.Floor(ROM)        # a talk's teleport onto a wall stops the test (lib/floorcheck.py)
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
FLAGS2 = 0x0203F1E2                                    # more flags 32-63: after the bench's 21 entries (outfit.c struct bench)
more_at = lambda n: BENCH_FLAGS + n // 8 if n < 32 else FLAGS2 + (n - 32) // 8
more = lambda n: mem(more_at(n) & ~3)[0] >> (8 * (more_at(n) & 3) + n % 8) & 1
def more_poke(n, v):
    a = more_at(n); old = mem(a & ~3)[0] >> (8 * (a & 3)) & 255
    send('poke8 %08X %02X' % (a, old | 1 << n % 8 if v else old & ~(1 << n % 8) & 255))
at = lambda: mem(AT)[0] & 0xFFFF
zenie = lambda: mem(ZENIE)[0]
def talk(x, y):
    FLOOR.guard(at(), x, y + 22, 'Goku')
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

# GT challengers (Challengers, third line): Ledgic once Goku Black is with you; his fall brings Pan and the GT looks. Then Uub, and Majuub in the next room.
GT_MENU = ['tap A 150', *['tap DOWN 12'] * 3, 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150']
hub_talk(); send(*GT_MENU, 'shot gt_menu', 'tap DOWN 12', 'tap A 150', 'shot no_uub'); dismiss(1)
check('Uub: locked before Ledgic', at() == HUB and more(zone26.MORE_GT) == 0)
hub_talk(); send(*GT_MENU, 'tap A 150', 'shot ledgic', 'tap A 200', 'run 200', 'shot ledgic_room')
check('Ledgic: into his room', at() == zone26.challenge_room('ledgic') << 8 | 26)
foe = mem(ENEMIES)[0]; check('Ledgic: he has %d HP' % zone26.LEDGIC_FIGHT[0][1], foe and mem(foe + 0x28C)[0] >> 10 == zone26.LEDGIC_FIGHT[0][1])
for k in range(6): send('run 20', 'shot ledgic_fight_%d' % k)
check('Ledgic: beaten', beat(zone26.challenge_room('ledgic')))
check('Ledgic: comes home', settle(HUB))
check('Ledgic: the win is waiting to be told', more(zone26.MORE_LEDGIC_WON) == 1)
strong(); talk(*zone26.HUB_AT); send('run 60', 'shot ledgic_won', 'tap A 60', 'run 30', 'shot pan_says', 'tap A 60', 'run 30', 'shot gt_joins'); dismiss(1)
check('Pan and the GT looks open', more(zone26.MORE_GT) == 1 and more(zone26.MORE_LEDGIC_WON) == 0)
hub_talk(); send(*GT_MENU, 'tap DOWN 12', 'tap A 150', 'shot uub', 'tap A 200', 'run 200', 'shot uub_room')
check('Uub: into his room', at() == zone26.challenge_room('uub') << 8 | 26)
foe = mem(ENEMIES)[0]; check('Uub: he has %d HP' % zone26.UUB_FIGHT[0][1], foe and mem(foe + 0x28C)[0] >> 10 == zone26.UUB_FIGHT[0][1])
check('Uub: beaten', beat(zone26.challenge_room('uub')))
for _ in range(12):
    send('run 60')
    if at() == zone26.challenge_room('uub', 1) << 8 | 26 and mem(ENEMIES)[0]: break
send('run 60', 'shot majuub_room')
check('Majuub comes on in the next room', at() == zone26.challenge_room('uub', 1) << 8 | 26)
foe = mem(ENEMIES)[0]; check('Majuub has %d HP' % zone26.UUB_FIGHT[1][1], foe and mem(foe + 0x28C)[0] >> 10 == zone26.UUB_FIGHT[1][1])
check('Majuub: beaten', beat(zone26.challenge_room('uub', 1)))
check('Majuub: comes home', settle(HUB))
strong(); talk(*zone26.HUB_AT); send('run 60', 'shot uub_won', 'tap A 60', 'run 30', 'shot uub_joins'); dismiss(1)
check('Uub joins', more(zone26.MORE_UUB) == 1 and more(zone26.MORE_UUB_WON) == 0)

# More, then Next: Trials II (after the first four Trials are paid) and the Dojo.
NEXT = ['tap A 150', *['tap DOWN 12'] * 3, 'tap A 150', *['tap DOWN 12'] * 3, 'tap A 150']
hub_talk(); send(*NEXT, 'shot more2', 'tap A 150', 'shot no_trials2'); dismiss(1)
check('Trials II: locked before the first four are paid', at() == HUB)
send(flag_on(zone26.TRIAL_ALL)); mem(G)
for k, t in enumerate(zone26.TRIALS2):
    hub_talk(); send(*NEXT, 'tap A 150', 'run 60', 'tap A 150', 'shot trial2_menu', *['tap DOWN 12'] * k, 'tap A 200', 'run 200', 'shot trial2_%d' % k)
    check('Trials II %d: into the room' % (k + 1), at() == zone26.challenge_room('trial2_%d' % k) << 8 | 26)
    check('Trials II %d: %s plays' % (k + 1, t[1]), mem(G)[0] & 255 == t[0])
    foe = mem(ENEMIES)[0]; check('Trials II %d: %s has %d HP' % (k + 1, t[4], zone26.TRIAL2_HP), foe and mem(foe + 0x28C)[0] >> 10 == zone26.TRIAL2_HP)
    check('Trials II %d: beaten' % (k + 1), beat(zone26.challenge_room('trial2_%d' % k)))
    check('Trials II %d: comes home' % (k + 1), settle(HUB))
    z0 = zenie(); talk(*zone26.HUB_AT); send('run 60', 'shot trial2_paid%d' % k); dismiss(1)
    check('Trials II %d: paid %d Zenie' % (k + 1, zone26.TRIAL2_PRIZE), more(zone26.MORE_T2_PAID + k) == 1 and zenie() - z0 == zone26.TRIAL2_PRIZE)
talk(*zone26.HUB_AT); send('run 60', 'shot all2'); dismiss(1)
check('Trials II: all four pay the Geromantium set', more(zone26.MORE_T2_ALL) == 1)
DOJO = NEXT + ['tap DOWN 12', 'tap A 150', 'run 60', 'tap A 150', 'shot dojo_menu']
n = 0
for c, (cat, people) in enumerate(zone26.DOJO):
    for i, (name, actor, lock) in enumerate(people):
        hub_talk(); z0 = zenie(); send(*DOJO, *['tap DOWN 12'] * c, 'tap A 150', *['tap DOWN 12'] * i, 'tap A 200', 'run 200', 'shot dojo%d' % n)
        if lock and lock[0] == 'flag' and not mem(G + 0x55 + lock[1] // 8)[0] >> (lock[1] % 8) & 1:
            check('Dojo %s: locked until met' % name, at() == HUB); dismiss(1); n += 1; continue
        check('Dojo %s: into the room' % name, at() == zone26.challenge_room('dojo%d' % n) << 8 | 26)
        foe = mem(ENEMIES)[0]; check('Dojo %s: %d HP' % (name, zone26.DOJO_HP), foe and mem(foe + 0x28C)[0] >> 10 == zone26.DOJO_HP)
        send('run 30', 'shot dojo%d_fight' % n)
        check('Dojo %s: beaten' % name, beat(zone26.challenge_room('dojo%d' % n)))
        check('Dojo %s: comes home and pays' % name, settle(HUB) and zenie() - z0 == zone26.DOJO_PRIZE)
        n += 1

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
