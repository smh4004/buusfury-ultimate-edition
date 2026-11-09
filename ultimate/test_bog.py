#!/usr/bin/env python3
"""Battle of Gods (ultimate/bog.py). Needs a zone debug build whose official warps to Capsule Corporation:
  BFU_HUB_WARP="4, 20, 1, 192, 196" BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_bog.py <dir> [work dir]
After the ending, with Goku's Super Saiyan mastered: Whis at Capsule Corporation, King Kai's planet and the fight Goku loses, Bulma's party
and Vegeta's fight, the ritual (Super Saiyan God learned), the god fight lost (back to the party) and won (home, Beerus spares the Earth)."""
import os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, bog, floorcheck
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='bog'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
FLOOR = floorcheck.Floor(ROM)        # a talk's teleport onto a wall stops the test (lib/floorcheck.py)
G = 0x03001068; PLAYER = 0x03001C34; AT = 0x0300197C; REC0 = 0x03001560
MASTERY = 0x0203F000 + 20 + 20 * 22; FLAGS2 = 0x0203F000 + 20 + 21 * 22
BENCH_ON = ['poke 0203F000 32484342', 'poke 0203F004 00001234', 'poke8 03001559 34', 'poke8 0300155A 12']
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
WALK_IN = 150    # frames after the zone 26 door until Goku's walk into West City is over (about 117; 110 left two frames, Nov 9)
FIRST = zone26.bog_first()
ROOM = {r[0]: (bog.room_of(r[0], FIRST) << 8 | 26) for r in bog.ROOMS}
CAPSULE = bog.CAPSULE[1] << 8 | bog.CAPSULE[0]
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
def dump(a, n):
    send('dump w %08X %X' % (a, n)); mem(G)
    return open(D + '/w.bin', 'rb').read()
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, (mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8)
more = lambda f: mem(FLAGS2 + (f - 32 >> 3))[0] >> ((f - 32) & 7) & 1
def talk(x, y, presses=14, gap=60):
    FLOOR.guard(at(), x, y + 22, 'Goku')
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4')
    for _ in range(presses): send('tap A %d' % gap)
    send('run 120'); mem(G)
at = lambda: mem(AT)[0] & 0xFFFF
def scene(x, y, want, presses=40, menu=False):
    """Talk to (x, y) and press A through the lines until the scene moves you to `want` (after the Switch Character menu: B)."""
    FLOOR.guard(at(), x, y + 22, 'Goku')
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4')
    for k in range(presses):
        send('tap A 40')
        if menu and k > 6: send('tap B 30')
        if at() == want: break
    send('run 150'); mem(G)
    return at() == want
def held():
    r = dump(REC0, 0x68)
    return list(r[0x0D:0x0D + r[0x0C]]) + [k for k in range(64) if k < 16 * 8 and False]
def boss(hp):
    w = dump(0x02000000, 0x40000); i = w.find(struct.pack('<I', hp << 10))
    return (0x02000000 + i,) + struct.unpack_from('<II', w, i - 0xEC) if i >= 0 else (None, 0, 0)
ENEMIES = 0x03001BB4
def beat(hp, name, room):
    """As test_cell.py: Beerus (the first enemy) left at 2 HP, Goku just below him facing up, three punches; again until he falls and the
    story moves on."""
    foe = mem(ENEMIES)[0]
    check('%s: Beerus is there with %d HP' % (name, hp), foe and mem(foe + 0x28C)[0] == hp << 10)
    for _ in range(60):
        if at() != room: break
        foe = mem(ENEMIES)[0]
        if not foe: send('run 160', 'tap A 20'); continue
        x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]; full()
        send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)),
             'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 30')
    for _ in range(14):
        if at() != room: break
        send('run 160', 'tap A 20')
    send('run 200'); mem(G)
def full():
    send('poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17))

# 0. Every place the quest puts someone (people, Beerus, Goku's arrivals, the spot below each person where you talk) is floor
spots = [(26, bog.room_of(name, FIRST), who, x, y) for name, wa, npcs, foe, arrive in bog.ROOMS
         for who, x, y in [(n, x, y) for n, x, y in npcs] + [('talk to ' + n, x, y + 22) for n, x, y in npcs]
         + ([('Beerus', foe[1], foe[2])] if foe else []) + [('Goku arrives', arrive[0], arrive[1])]]
spots += [(bog.CAPSULE[0], bog.CAPSULE[1], 'Whis', bog.WHIS_AT[0], bog.WHIS_AT[1]), (bog.CAPSULE[0], bog.CAPSULE[1], 'talk to Whis', bog.WHIS_AT[0], bog.WHIS_AT[1] + 22),
          (bog.HOME[0], bog.HOME[1], 'home', bog.HOME[3], bog.HOME[4])]
walls = [s for s in spots if not FLOOR.walkable(*s[:2], *s[3:])]
check('all %d places the quest puts someone are on walkable floor%s' % (len(spots), (': not ' + str(walls)) if walls else ''), not walls)
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
door = [x for x in zone26.links(__import__('json').load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run %d' % WALK_IN); mem(G)
def talk_until(x, y, want, tries=4):
    """Talk to someone who sends you elsewhere; residents wander, so try again until it happens."""
    for _ in range(tries):
        talk(x, y, 1, 80); send('run 200'); mem(G)
        if at() == want: return True
    return False
send('run 100'); talk_until(96, 328, 0x103)
send(*BENCH_ON, 'poke8 %08X FA' % MASTERY)        # Goku's Super Saiyan mastered
# 1. Whis, then King Kai's planet
send(flag_on(883)); talk_until(*zone26.HUB_AT, CAPSULE); send('run 100', 'shot cc_whis'); mem(G)
check('the rig lands at Capsule Corporation', at() == CAPSULE)
full(); scene(*bog.WHIS_AT, ROOM['kai']); send('shot kai'); mem(G)
check('Whis takes Goku to King Kai\'s planet', at() == ROOM['kai'] and more(bog.MORE_BOG_START))
scene(152, 176, ROOM['kai_fight']); send('shot kai_fight'); mem(G)
check('after the talk, Beerus fights Goku there', at() == ROOM['kai_fight'] and more(bog.MORE_BOG_FIGHT))
a, _, _ = boss(bog.ROWS[0][0])
check('there he has %d HP' % bog.ROWS[0][0], a is not None)
send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17))      # Goku nearly out: Beerus finishes him
for _ in range(20):
    send('run 60')
    if at() != ROOM['kai_fight']: break
send('run 200', 'shot party'); mem(G)
check('losing to him carries on to Bulma\'s party (no game over)', at() == ROOM['party'] and more(bog.MORE_BOG_LOST) and not more(bog.MORE_BOG_FIGHT))
# 2. The party, then Vegeta's fight (won)
scene(136, 232, ROOM['party_fight'], menu=True); send('shot party_fight'); mem(G)
check('the party scene leads to the fight with Beerus', at() == ROOM['party_fight'])
full(); beat(bog.ROWS[1][0], 'the party', ROOM['party_fight'])
send('shot ritual'); mem(G)
check('beating him there leads on to the ritual', at() == ROOM['ritual'] and more(bog.MORE_BOG_PARTY))
# 3. The ritual: Super Saiyan God
scene(104, 264, ROOM['god_fight'], menu=True); send('shot god_fight'); mem(G)
s = held()
check('the ritual makes Goku a Super Saiyan God (the skill is his)', more(bog.MORE_BOG_RITUAL) and 46 in s)
check('then Goku faces Beerus on the Lookout', at() == ROOM['god_fight'])
# 4. The god fight: lost, back to the party; then won, home
send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17))
for _ in range(20):
    send('run 60')
    if at() != ROOM['god_fight']: break
send('run 200', 'shot god_lost'); mem(G)
check('losing the god fight goes back to the party', at() == ROOM['ritual'] and not more(bog.MORE_BOG_DONE))
scene(104, 264, ROOM['god_fight'], menu=True)
check('and from there you can try again', at() == ROOM['god_fight'])
full(); beat(bog.ROWS[2][0], 'the god fight', ROOM['god_fight'])
send('shot home'); mem(G)
check('winning it brings Goku home to Capsule Corporation', at() == CAPSULE and more(bog.MORE_BOG_DONE))
scene(*bog.WHIS_AT, -1, 20); send('shot told'); mem(G)
check('where Beerus spares the Earth', more(bog.MORE_BOG_TOLD))
check('and Super Saiyan God stays Goku\'s', 46 in held())
check('no bad jumps', not bad[0])
send('quit')
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
