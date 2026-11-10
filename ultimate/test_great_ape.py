#!/usr/bin/env python3
"""The Great Ape raid (ultimate/great_ape.py), in Dr. Brief's Lab and the Giant Crater's copies. Needs a zone debug build whose official warps
to the lab:
  BFU_HUB_WARP="4, 31, 1, 328, 448" BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_great_ape.py <dir> [work dir]
After the ending, with the GT looks open: Bulma and GT Vegeta in the lab; playing as Vegeta, Bulma asks for someone else (he's the one who
changes) and nothing starts; as Goku, she takes him to the crater, where Vegeta becomes the Great Ape (two scenes); its first round (lost: back
to the lab, Vegeta gone from it, the quest kept; again from the first round); won, it gets back up (a scene) for the second (lost: again
from the second round); won, Vegeta is himself again (a scene), and home to the lab with the Zenie and the skill learned. Every round's
health checked on the way, every spot the raid puts someone is floor. Goku is a level 150 fighter made the game's way (fightrig.py); each
round starts with a real exchange, and the end checks the balance."""
import json, os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, great_ape, floorcheck, fightrig
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='ape'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
ACTORS = json.load(open(OUT + '/BFU_debug_zone.map.json'))['actors']
FLOOR = floorcheck.Floor(ROM)
G = 0x03001068; PLAYER = 0x03001C34; AT = 0x0300197C; REC0 = 0x03001560; ZENIE = 0x0300155C; ENEMIES = 0x03001BB4; COUNT = 0x03001BB0
FLAGS2 = 0x0203F000 + 20 + 21 * 22
BENCH_ON = ['poke 0203F000 32484342', 'poke 0203F004 00001234', 'poke8 03001559 34', 'poke8 0300155A 12']
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
AREA = lambda wa: wa[1] << 8 | wa[0]
LAB = AREA(great_ape.LAB)
ROOMS = zone26.ape_rooms(); ROOM = {r: AREA((26, n)) for r, n in ROOMS.items()}
APE_SKILL = 48
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
def dump(a, n, name='w'):
    send('dump %s %08X %X' % (name, a, n)); mem(G)
    return open(D + '/%s.bin' % name, 'rb').read()
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, (mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8)
def more_at(n): return 0x0203F00C + n // 8 if n < 32 else FLAGS2 + (n - 32) // 8
def more(n): a = more_at(n); return mem(a & ~3)[0] >> (8 * (a & 3) + n % 8) & 1
def more_poke(n, v):
    a = more_at(n); old = mem(a & ~3)[0] >> (8 * (a & 3)) & 255
    send('poke8 %08X %02X' % (a, old | 1 << n % 8 if v else old & ~(1 << n % 8) & 255))
at = lambda: mem(AT)[0] & 0xFFFF
in_area = lambda a: lambda: at() == a
def standing(x, y):
    """Is someone standing still at (x, y)? A live object (the game's object list at 0x03001C4C: count at +4, pointers from +8) whose
    position words (+0x1A0) are (x, y). (Searching all of work RAM for the words found a freed object's: after the Garlic Jr. quest a
    copy of the Lookout's foe, at Garlic Jr.'s spot, was still in memory.)"""
    n = min(mem(0x03001C50)[0], 96)
    return any(o and mem(o + 0x1A0, 2) == [x << 8, y << 8] for o in (mem(0x03001C54, n) if n else []))
RIG = None
def heal(): RIG.heal()
def scene(x, y, until, presses=40):
    """Talk to (x, y) and press A through the lines (a menu's first choice: A) until `until()`."""
    FLOOR.guard(at(), x, y + 22, 'Goku')
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4')
    for _ in range(presses):
        send('tap A 40')
        if until(): break
    send('run 150'); mem(G)
    return until()
def watch(until, presses=40, shots=()):
    """A scene that plays by itself (a room entered): press A through its lines until `until()`, a screenshot after each press in `shots`."""
    for k in range(presses):
        if until(): break
        send('tap A 40')
        if k in shots: send('shot %s_%d' % (shots[k], k))
    send('run 120'); mem(G)
    return until()
def foes(row=None):
    n = mem(COUNT)[0]
    out = []
    for e in mem(ENEMIES, min(n, 8)) if n else []:
        if e and mem(e + 0x1D0)[0] & 255 != 1 and (row is None or mem(e + 0x224)[0] == row): out.append((e, mem(e + 0x28C)[0] >> 10))
    return out
def beside(x, y):
    """Where Goku stands to fight a foe at (x, y) (positions <<8): just below it facing up, or above, left or right of it, the first that is
    floor here (the crater's open ground runs to the map's foot: below the ape there can be wall, and a Goku put in it was never reached)."""
    for dx, dy, facing in ((0, 20, 1), (0, -20, 0), (-28, 0, 3), (28, 0, 2)):
        if FLOOR.walkable(at() & 0xFF, at() >> 8, (x >> 8) + dx, (y >> 8) + dy): return x + (dx << 8), y + (dy << 8), facing
    return x, y + (20 << 8), 1
def beat(name, fighting, hp=None):
    """The ape left at 2 HP, Goku just below him facing up, three punches; again while `fighting()` (after one real exchange)."""
    if hp is not None:
        f = foes()
        check('%s is there with %d HP' % (name, hp), bool(f) and f[0][1] == hp)
    if name not in RIG.BAL and fighting(): RIG.spar(name, secs=30, spot=beside)     # (a longer exchange: its hits differ a lot, the heavy punch most)
    for _ in range(60):
        if not fighting(): break
        f = [x for x in foes() if x[1] > 0]
        if not f: send('run 160', 'tap A 20'); continue
        foe = f[0][0]; x, y, facing = beside(*mem(foe + 0x1A0, 2)); pl = mem(PLAYER)[0]; heal()
        send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y),
             'poke8 %08X %02X' % (pl + 0x10, facing), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 30')
    send('run 200'); mem(G)
def lose(fighting):
    """Goku nearly out beside the ape: it finishes him (as test_garlic.py's lose)."""
    pl = mem(PLAYER)[0]
    f = [x for x in foes() if x[1] > 0]
    if f:
        x, y, _ = beside(*mem(f[0][0] + 0x1A0, 2))
        send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y), 'run 2')
    down = False
    for _ in range(60):
        if not fighting(): break
        h = mem(REC0 + 0x16)[0] & 0xFFFF
        down = down or h == 0
        if not down and h > 1: send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17))
        send('run 60')
    send('run 200'); mem(G)

# 0. Every place the raid puts someone, and where you stand to talk to them, is floor; the crater's copies are zone 26 rooms with its floor
A = great_ape
spots = [(*A.LAB, 'Bulma', *A.BULMA_AT), (*A.LAB, 'Vegeta', *A.VEGETA_AT), (*A.LAB, 'talk to Bulma', A.BULMA_AT[0], A.BULMA_AT[1] + 22),
         (*A.LAB, 'talk to Vegeta', A.VEGETA_AT[0], A.VEGETA_AT[1] + 22), (A.HOME[0], A.HOME[1], 'home', *A.HOME[3:])]
spots += [(*A.CRATER, 'the Great Ape', *A.FOE_AT), (*A.CRATER, 'Bulma in the crater', *A.BULMA_SCENE), (*A.CRATER, 'Goku arriving', *A.ARRIVE),
          (*A.CRATER, 'Goku below the ape', A.FOE_AT[0], A.FOE_AT[1] + 20)]
walls = [s for s in spots if not FLOOR.walkable(s[0], s[1], s[3], s[4])]
check('all %d places the raid puts someone are on walkable floor%s' % (len(spots), (': not ' + str(walls)) if walls else ''), not walls)
copies = [ROOMS[r] for r in A.ROOMS]
check('the crater\'s %d copies are rooms of zone 26 (%d-%d) with the crater\'s floor' % (len(copies), copies[0], copies[-1]),
      all(FLOOR.walkable(26, r, *A.FOE_AT) and FLOOR.walkable(26, r, *A.ARRIVE) for r in copies) and copies == list(range(copies[0], copies[0] + len(copies))))
check('the raid\'s rooms have no way out', all(FLOOR.rom[FLOOR.record(26, r) + 3] == (0 if r in [ROOMS[f] for f in A.FIGHT_ROOMS] else 1) for r in copies))
rom = open(ROM, 'rb').read()
stats = struct.unpack_from('<I', rom, zone26.STATS_REFS[0])[0] - 0x08000000
rows = [k for hp, st in A.ROWS for k in range(400) if rom[stats + 28 * k + 4:stats + 28 * k + 8] == struct.pack('<I', hp) and rom[stats + 28 * k + 0xC:stats + 28 * k + 0x10] == bytes(st)]
check('both rounds have rows of their own on Broly\'s fighting (behaviour %d)' % rom[0x711274 + 28 * A.BROLY_ROW + 8],
      len(rows) == 2 and all(rom[stats + 28 * k + 8:stats + 28 * k + 12] == rom[0x711274 + 28 * A.BROLY_ROW + 8:0x711274 + 28 * A.BROLY_ROW + 12] for k in rows))
# 1. Into the lab
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
send(*BENCH_ON); more_poke(zone26.MORE_GT, 1); mem(G)
RIG = fightrig.Rig(send, mem, rom)
L150 = RIG.level150(); print('   Goku: level %d -> 150: %d HP, %d ki, Strength/Power/Endurance %s' % L150, flush=True)
check('Goku is a level 150 fighter, made the game\'s way', L150[1] > 4000 and L150[3][0] > 150)
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run 150'); mem(G)
def talk_until(x, y, want, tries=4):
    for _ in range(tries):
        FLOOR.guard(at(), x, y + 22, 'Goku')
        pl = mem(PLAYER)[0]
        send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80', 'run 200'); mem(G)
        if at() == want: return True
    return False
send('run 100'); talk_until(96, 328, AREA((3, 1)))
talk_until(*zone26.HUB_AT, LAB); send('run 100', 'shot lab'); mem(G)
check('the rig reaches Dr. Brief\'s Lab', at() == LAB)
check('Bulma and GT Vegeta wait in the lab', standing(*A.BULMA_AT) and standing(*A.VEGETA_AT))
# 2. Playing as Vegeta: Bulma asks for someone else, and nothing starts (more_get 250 reads who is playing)
send('poke8 %08X 04' % G); mem(G)
scene(*A.BULMA_AT, lambda: False, presses=6); send('shot vegeta_asked'); mem(G)
check('as Vegeta: Bulma asks for someone else, and the raid doesn\'t start', at() == LAB and not more(A.MORE_APE_START))
send('poke8 %08X 00' % G, 'tap B 20', 'run 60'); mem(G)
# 3. As Goku: to the crater, the change
heal(); scene(*A.BULMA_AT, in_area(ROOM['intro'])); send('shot intro'); mem(G)
check('Bulma takes Goku to the Giant Crater (a scene)', at() == ROOM['intro'] and more(A.MORE_APE_START))
watch(in_area(ROOM['change']), shots={1: 'intro_bulma', 2: 'intro_vegeta'}); send('shot change'); mem(G)
check('Vegeta becomes the Great Ape in a flash (a scene room of its own)', at() == ROOM['change'])
watch(in_area(ROOM['ape1']), shots={0: 'change_ape', 1: 'change_bulma'}); send('shot ape1'); mem(G)
check('he has lost control: the first round', at() == ROOM['ape1'] and more(A.MORE_APE_FIGHT))
f = foes()
check('the Great Ape is there with %d HP' % A.ROWS[0][0], bool(f) and f[0][1] == A.ROWS[0][0])
check('it is the ape\'s figure', bool(f) and mem(f[0][0] + 0x58)[0] == struct.unpack_from('<I', rom, 0x840000 + 4 * ACTORS['oozaru'])[0])
heal(); hp0 = mem(REC0 + 0x16)[0] & 0xFFFF; hit = False   # it fights (Broly's row): left alone beside it, Goku is hit
if f:
    x, y, _ = beside(*mem(f[0][0] + 0x1A0, 2)); pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y), 'run 20', 'shot ape_near')
    for k in range(20):
        send('run 30')
        if k in (3, 6, 9): send('shot ape_fights_%d' % k)
        if mem(REC0 + 0x16)[0] & 0xFFFF < hp0: hit = True; break
send('shot ape_hits'); mem(G)
check('the Great Ape fights: left alone beside it, Goku is hit', hit)
lose(in_area(ROOM['ape1'])); send('shot lost1'); mem(G)
check('lost the first round: back in the lab, rested, the quest kept, the round not won', at() == LAB and not more(A.MORE_APE_FIGHT) and more(A.MORE_APE_START) and not more(A.MORE_APE_HALF))
send('run 60'); mem(G)
check('Vegeta isn\'t in the lab while he\'s the Great Ape', standing(*A.BULMA_AT) and not standing(*A.VEGETA_AT))
heal(); scene(*A.BULMA_AT, in_area(ROOM['ape1']), presses=10); send('shot again1'); mem(G)
check('Bulma sends Goku back: the first round again', at() == ROOM['ape1'] and more(A.MORE_APE_FIGHT))
# 4. The first round won: it gets back up
heal(); beat('Great Ape (first round)', in_area(ROOM['ape1']), A.ROWS[0][0]); send('shot rage'); mem(G)
check('down: it gets back up, enraged (a scene); the round is kept from here', at() == ROOM['rage'] and more(A.MORE_APE_HALF))
watch(in_area(ROOM['ape2']), shots={0: 'rage_scene'}); send('shot ape2'); mem(G)
check('the second round', at() == ROOM['ape2'])
lose(in_area(ROOM['ape2'])); send('shot lost2'); mem(G)
check('lost the second round: back in the lab, the first round still won', at() == LAB and not more(A.MORE_APE_FIGHT) and more(A.MORE_APE_HALF))
heal(); scene(*A.BULMA_AT, in_area(ROOM['ape2']), presses=10)
check('and back to the second round', at() == ROOM['ape2'])
heal(); beat('Great Ape (second round)', in_area(ROOM['ape2']), A.ROWS[1][0]); send('shot end'); mem(G)
check('down for good: Vegeta is himself again (a scene)', at() == ROOM['end'])
z0 = mem(ZENIE)[0]
watch(lambda: at() == LAB and more(A.MORE_APE_DONE), presses=30, shots={0: 'end_scene', 3: 'end_bulma'}); send('run 200', 'shot home'); mem(G)
check('the raid is won: home in the lab', at() == LAB and more(A.MORE_APE_DONE) and not more(A.MORE_APE_FIGHT))
check('and %d Zenie' % A.ZENIE, mem(ZENIE)[0] - z0 == A.ZENIE)
check('Vegeta is back in the lab', standing(*A.VEGETA_AT))
send('run 300'); r = bytes(b''.join(struct.pack('<I', w) for w in mem(REC0, 0x68 // 4)))
known = struct.unpack_from('<H', r, 0x22)[0]
check('Goku has learned the Great Ape (held, or known in his book)', APE_SKILL in r[0x0D:0x0D + r[0x0C]] or known >> 15 & 1)
scene(*A.BULMA_AT, lambda: False, presses=4); send('shot after'); mem(G)
check('afterwards Bulma just talks: no new raid', at() == LAB and more(A.MORE_APE_DONE))
# 5. The balance, on a level 150 Goku: the hits he needs for each round and the share of his health each of the ape's takes
B = RIG.BAL
for n in ('Great Ape (first round)', 'Great Ape (second round)'):
    b = B.get(n)
    if not b: check('%s: an exchange was measured' % n, False); continue
    need = 1 / b['hit'] if b['hit'] else 0
    print('   %s: %.0f hits to beat, its hits %.1f%% of Goku\'s health (%d landed)' % (n, need, 100 * b['taken'], b['hurt']))
    check('%s takes 35-80 of level 150 Goku\'s hits (a raid: longer than Super Garlic Jr.\'s 28-70)' % n, 35 <= need <= 80)
    check('%s: its hits take no more than 16%% of his health (Beerus\'s hardest)' % n, b['taken'] <= 0.16)
check('no bad jumps', not bad[0])
send('quit')
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
