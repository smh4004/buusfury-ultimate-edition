#!/usr/bin/env python3
"""Battle of Gods (ultimate/bog.py), in the game's own areas. Needs a zone debug build whose official warps to Capsule Corporation:
  BFU_HUB_WARP="4, 20, 1, 192, 196" BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_bog.py <dir> [work dir]
After the ending and the Garlic Jr. quest, with Goku's Super Saiyan mastered: Whis at Capsule Corporation, King Kai's planet (Grand Kai's) and the fight Goku loses,
Bulma's party at Capsule Corporation and Vegeta's fight there (with fighting on), the ritual (Super Saiyan God learned), the god fight
across West City (lost: back to the party; West City's own people stand aside meanwhile), the forest and the desert, then home, where
Beerus spares the Earth. Goku is a level 150 fighter made the game's way (fightrig.py); each Beerus fight starts with a real exchange,
measured (the Garlic Jr. quest is balanced below these)."""
import os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, bog, floorcheck, fightrig
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='bog'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
FLOOR = floorcheck.Floor(ROM)        # a talk's teleport onto a wall stops the test (lib/floorcheck.py)
G = 0x03001068; PLAYER = 0x03001C34; AT = 0x0300197C; REC0 = 0x03001560
MASTERY = 0x0203F000 + 20 + 20 * 22; FLAGS2 = 0x0203F000 + 20 + 21 * 22
BENCH_ON = ['poke 0203F000 32484342', 'poke 0203F004 00001234', 'poke8 03001559 34', 'poke8 0300155A 12']
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
WALK_IN = 150    # frames after the zone 26 door until Goku's walk into West City is over (about 117; 110 left two frames, Nov 9)
AREA = lambda wa: wa[1] << 8 | wa[0]
CAPSULE, KAI, WEST, FOREST, DESERT = (AREA(a) for a in (bog.CAPSULE, bog.KAI, bog.WEST_CITY, bog.FOREST, bog.DESERT))
COMBAT = 0x03001988                    # fighting on in this area (the area's +8, copied on load)
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
def scene(x, y, until, presses=40, menu=False):
    """Talk to (x, y) and press A through the lines until `until()` (after the Switch Character menu: B)."""
    FLOOR.guard(at(), x, y + 22, 'Goku')
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4')
    for k in range(presses):
        send('tap A 40')
        if menu and k > 6: send('tap B 30')
        if until(): break
    send('run 150'); mem(G)
    return until()
in_area = lambda a: lambda: at() == a
def held():
    r = dump(REC0, 0x68)
    return list(r[0x0D:0x0D + r[0x0C]]) + [k for k in range(64) if k < 16 * 8 and False]
def boss(hp):
    w = dump(0x02000000, 0x40000); i = w.find(struct.pack('<I', hp << 10))
    return (0x02000000 + i,) + struct.unpack_from('<II', w, i - 0xEC) if i >= 0 else (None, 0, 0)
ENEMIES = 0x03001BB4
def beat(hp, name, fighting):
    """As test_cell.py: Beerus (the first enemy) left at 2 HP, Goku just below him facing up, three punches; again while `fighting()`."""
    foe = mem(ENEMIES)[0]
    check('%s: Beerus is there with %d HP' % (name, hp), foe and mem(foe + 0x28C)[0] == hp << 10)
    if fighting(): RIG.spar('Beerus, ' + name)
    for _ in range(60):
        if not fighting(): break
        foe = mem(ENEMIES)[0]
        if not foe: send('run 160', 'tap A 20'); continue
        x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]; full()
        send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)),
             'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 30')
    for _ in range(14):
        if not fighting(): break
        send('run 160', 'tap A 20')
    send('run 200'); mem(G)
def lose(fighting):
    """Goku nearly out: Beerus finishes him."""
    send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17))
    for _ in range(20):
        send('run 60')
        if not fighting(): break
    send('run 200'); mem(G)
def standing(x, y):
    """Is someone standing still at (x, y)? (an object's position words, +0x1A0, in work RAM)"""
    return dump(0x02000000, 0x40000).find(struct.pack('<ii', x << 8, y << 8)) >= 0
RIG = None                           # fightrig.Rig: a level 150 Goku (the owner, Nov 9: "Test these with a level 150 Goku"), heal(), spar()
def full():
    """Goku's health and ki back to his maximum: a level 150 fighter's (fightrig.level150), not poked numbers (0x7FFF went negative)."""
    RIG.heal()

# 0. Every place the quest puts someone (people, Beerus, Goku's arrivals, the spot below each person where you talk) is floor
spots = [(*wa, n, x, y) for wa, people, _ in bog.PEOPLE for n, x, y in people] + [(*wa, 'talk to ' + n, x, y + 22) for wa, people, _ in bog.PEOPLE for n, x, y in people]
spots += [(*wa, 'Beerus', x, y) for wa, x, y, _ in bog.FOES] + [(w, a, 'Goku arrives', x, y) for w, a, _, x, y in bog.ARRIVE]
spots += [(*bog.CAPSULE, 'Whis', *bog.WHIS_AT), (*bog.CAPSULE, 'talk to Whis', bog.WHIS_AT[0], bog.WHIS_AT[1] + 22), (bog.HOME[0], bog.HOME[1], 'home', *bog.HOME[3:])]
walls = [s for s in spots if not FLOOR.walkable(*s[:2], *s[3:])]
check('all %d places the quest puts someone are on walkable floor%s' % (len(spots), (': not ' + str(walls)) if walls else ''), not walls)
fights = [(*wa, 'Beerus', x, y) for wa, x, y, _ in bog.FOES] + [(*wa, 'Goku below him', x, y + 20) for wa, x, y, _ in bog.FOES] + [(w, a, 'Goku arrives', x, y) for w, a, _, x, y in bog.ARRIVE]
doors = [(s, FLOOR.near_trigger(s[0], s[1], s[3], s[4])) for s in fights]
doors = [d for d in doors if d[1]]
check('every fight stands clear of its area\'s doors, capsule and gates%s' % ((': not ' + str(doors)) if doors else ''), not doors)
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
RIG = fightrig.Rig(send, mem, open(ROM, 'rb').read())
L150 = RIG.level150(); print('   Goku: level %d -> 150: %d HP, %d ki, Strength/Power/Endurance %s' % L150, flush=True)
door = [x for x in zone26.links(__import__('json').load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run %d' % WALK_IN); mem(G)
def talk_until(x, y, want, tries=4):
    """Talk to someone who sends you elsewhere; residents wander, so try again until it happens."""
    for _ in range(tries):
        talk(x, y, 1, 80); send('run 200'); mem(G)
        if at() == want: return True
    return False
send('run 100')
check('the West City resident stands at his spot (as the check in West City below expects)', standing(320, 360))
talk_until(96, 328, 0x103)
send(*BENCH_ON, 'poke8 %08X FA' % MASTERY)        # Goku's Super Saiyan mastered
import garlic                                     # and the Garlic Jr. quest done: Battle of Gods waits for it (outfit.c more_get 253)
b = FLAGS2 + (garlic.GJ_DONE - 32 >> 3); send('poke8 %08X %02X' % (b, (mem(b)[0] & 255) | 1 << ((garlic.GJ_DONE - 32) & 7)))
# 1. Whis, then King Kai's planet (Grand Kai's)
send(flag_on(883)); talk_until(*zone26.HUB_AT, CAPSULE); send('run 100', 'shot cc_whis'); mem(G)
check('the rig lands at Capsule Corporation', at() == CAPSULE)
full(); scene(*bog.WHIS_AT, in_area(KAI)); send('shot kai'); mem(G)
check('Whis takes Goku to King Kai\'s planet (Grand Kai\'s Planet, the real area)', at() == KAI and more(bog.MORE_BOG_START))
scene(152, 176, lambda: more(bog.MORE_BOG_FIGHT)); send('run 100', 'shot kai_fight'); mem(G)
a, _, _ = boss(bog.ROWS[0][0])
check('after the talk, Beerus fights Goku there with %d HP' % bog.ROWS[0][0], at() == KAI and more(bog.MORE_BOG_FIGHT) and a is not None)
lose(in_area(KAI)); send('shot party')
check('losing to him carries on to Bulma\'s party at Capsule Corporation (no game over)', at() == CAPSULE and more(bog.MORE_BOG_LOST) and not more(bog.MORE_BOG_FIGHT))
check('there is no fighting at Capsule Corporation outside the quest\'s fight', mem(COMBAT)[0] == 0)
# 2. The party, then Vegeta's fight (won), on Capsule Corporation's grounds
scene(136, 232, lambda: more(bog.MORE_BOG_FIGHT), menu=True); send('run 100', 'shot party_fight'); mem(G)
check('the party scene leads to the fight with Beerus, at Capsule Corporation with fighting on', at() == CAPSULE and mem(COMBAT)[0] == 1)
full(); beat(bog.ROWS[1][0], 'the party', lambda: more(bog.MORE_BOG_FIGHT))
send('shot ritual'); mem(G)
check('beating him there leads on to the ritual, and fighting is off again', at() == CAPSULE and more(bog.MORE_BOG_PARTY) and mem(COMBAT)[0] == 0)
# 3. The ritual: Super Saiyan God; the god fight starts in West City
scene(104, 264, in_area(WEST), menu=True); send('shot god_west'); mem(G)
for _ in range(5):          # skills_sync grants it within 64 frames of the ritual's flag (Nov 9: one run checked a few frames too soon)
    if 46 in held(): break
    send('run 16'); mem(G)
check('the ritual makes Goku a Super Saiyan God (the skill is his)', more(bog.MORE_BOG_RITUAL) and 46 in held())
a, _, _ = boss(bog.ROWS[2][0])
check('then Goku faces Beerus in West City', at() == WEST and a is not None)
check('the West City resident stands aside meanwhile', not standing(320, 360))
# 4. The god fight: lost in West City, back to the party; again, then West City, the forest, the desert, home
lose(in_area(WEST)); send('shot god_lost')
check('losing the god fight goes back to the party', at() == CAPSULE and not more(bog.MORE_BOG_FIGHT) and not more(bog.MORE_BOG_DONE))
scene(104, 264, in_area(WEST), menu=True)
check('and from there you can try again', at() == WEST)
full(); beat(bog.ROWS[2][0], 'West City', in_area(WEST)); send('shot god_forest'); mem(G)
check('beating him in West City carries the fight to the forest', at() == FOREST and more(bog.MORE_BOG_GOD2) and more(bog.MORE_BOG_FIGHT))
full(); beat(bog.ROWS[3][0], 'the forest', in_area(FOREST)); send('shot god_desert'); mem(G)
check('and from the forest to the desert', at() == DESERT and more(bog.MORE_BOG_GOD3))
lose(in_area(DESERT))
check('losing in the desert goes back to the party', at() == CAPSULE and not more(bog.MORE_BOG_DONE))
scene(104, 264, in_area(DESERT), menu=True)
check('and trying again goes straight back to the desert', at() == DESERT)
full(); beat(bog.ROWS[4][0], 'the desert', in_area(DESERT)); send('shot home'); mem(G)
check('winning there brings Goku home to Capsule Corporation', at() == CAPSULE and more(bog.MORE_BOG_DONE) and not more(bog.MORE_BOG_FIGHT))
scene(264, 232, lambda: more(bog.MORE_BOG_TOLD)); send('shot told'); mem(G)
check('where Beerus spares the Earth', more(bog.MORE_BOG_TOLD))
check('and Super Saiyan God stays Goku\'s', 46 in held())
check('no bad jumps', not bad[0])
send('quit')
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
