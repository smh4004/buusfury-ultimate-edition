#!/usr/bin/env python3
"""The Garlic Jr. quest (ultimate/garlic.py), in the game's own areas and the Lookout's copies. Needs a zone debug build whose official warps
to the Lookout:
  BFU_HUB_WARP="6, 1, 1, 312, 400" BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_garlic.py <dir> [work dir]
After the ending: Dende's hint on the Lookout and Mr. Popo's carpet to Hercule City; the mist there (its people stand aside, the tournament
official keeps his post) and the two Makyans (one beaten, then lost to: both back; both beaten: Hercule comes out); Hercule to Korin's
Tower; Korin's water and the town cured; Hercule to the Lookout, where Garlic Jr. and the Spice Boys hold it (Dende and Mr. Popo gone);
the Spice Boys one after another with their scenes between (lost at Mustard: back to the Lookout, from Spice again), Garlic Jr. (lost:
from him again), his change, Super Garlic Jr., the Dead Zone seal (the press-fast meter), and home: Dende and Mr. Popo back, the necklace
and the Zenie. Every foe's health and every room checked on the way; every spot the quest puts someone is floor.
Goku is a level 150 fighter made the game's way (fightrig.py); every fight starts with a real exchange, and the end checks the balance:
the hits he needs for each foe and the share of his health each of theirs takes."""
import json, os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, garlic, floorcheck, fightrig, barcheck
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='garlic'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
ACTORS = json.load(open(OUT + '/BFU_debug_zone.map.json'))['actors']
FLOOR = floorcheck.Floor(ROM)
G = 0x03001068; PLAYER = 0x03001C34; AT = 0x0300197C; REC0 = 0x03001560; ZENIE = 0x0300155C; ENEMIES = 0x03001BB4; COUNT = 0x03001BB0
import bench as BN
FLAGS2 = BN.FLAGS2
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
WALK_IN = 150
AREA = lambda wa: wa[1] << 8 | wa[0]
LOOKOUT, KORIN, SATAN = (AREA(a) for a in (garlic.LOOKOUT, garlic.KORIN, garlic.SATAN))
ROOMS = zone26.garlic_rooms(); ROOM = {r: AREA((26, n)) for r, n in ROOMS.items()}
HP = {name: hp for name, _, hp, _ in garlic.FIGHTS}
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
more = lambda f: mem(FLAGS2 + (f - 32 >> 3))[0] >> ((f - 32) & 7) & 1
at = lambda: mem(AT)[0] & 0xFFFF
in_area = lambda a: lambda: at() == a
def standing(x, y):
    """Is someone standing still at (x, y)? A live object (the game's object list at 0x03001C4C: count at +4, pointers from +8) whose
    position words (+0x1A0) are (x, y). (Searching all of work RAM for the words found a freed object's: after the Garlic Jr. quest a
    copy of the Lookout's foe, at Garlic Jr.'s spot, was still in memory.)"""
    n = min(mem(0x03001C50)[0], 96)
    return any(o and mem(o + 0x1A0, 2) == [x << 8, y << 8] for o in (mem(0x03001C54, n) if n else []))
RIG = None                                        # fightrig.Rig: a level 150 Goku, heal(), spar() (set once the harness runs)
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
def watch(until, presses=40):
    """A scene that plays by itself (a room entered): press A through its lines until `until()`."""
    for _ in range(presses):
        if until(): break
        send('tap A 40')
    send('run 120'); mem(G)
    return until()
BAR = barcheck.Bar(open(ROM, 'rb').read(), mem)
def foes(row=None):
    """[(object, HP)] of the foes on the screen (the enemy list; team 1 is the player's side); only those of stats row `row` if given
    (the object's +0x224 points at its row)."""
    n = mem(COUNT)[0]
    out = []
    for e in mem(ENEMIES, min(n, 8)) if n else []:
        if e and mem(e + 0x1D0)[0] & 255 != 1 and (row is None or mem(e + 0x224)[0] == row): out.append((e, mem(e + 0x28C)[0] >> 10))
    return out
def beat(name, fighting, hp=None, row=None):
    """The first foe (of `row`, if given) left at 2 HP, Goku just below him facing up, three punches; again while `fighting()`."""
    if hp is not None:
        f = foes(row)
        check('%s is there with %d HP' % (name, hp), bool(f) and f[0][1] == hp)
        who = zone26.row_names().get((mem(f[0][0] + 0x224)[0] - BAR.table) // 28) if f else None     # the boss bar (outfit.c bossbar)
        seen = barcheck.expect(BAR, send, who, full=True) if who else (False, 'his stats row has no name')
        check('%s: his bar is up and full (%s): %s' % (name, who, seen[1]), seen[0])
    if name not in RIG.BAL and fighting(): RIG.spar(name, row)
    for _ in range(60):
        if not fighting(): break
        f = [x for x in foes(row) if x[1] > 0]
        if not f: send('run 160', 'tap A 20'); continue
        foe = f[0][0]; x, y = mem(foe + 0x1A0, 2); pl = mem(PLAYER)[0]; heal()
        send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)),
             'poke8 %08X 01' % (pl + 0x10), 'run 2', 'tap A 14', 'tap A 14', 'tap A 14', 'run 30')
    send('run 200'); mem(G)
def lose(fighting, row=None):
    """Goku nearly out beside the foe: the foe finishes him. Only while the fight is on and Goku still up (poked to 1 HP after the game's
    revive, he walked into the next fight at 1 HP and fell to its first hit). He doesn't fight back (at level 150 his punches won)."""
    pl = mem(PLAYER)[0]
    f = [x for x in foes(row) if x[1] > 0]
    if f:
        x, y = mem(f[0][0] + 0x1A0, 2)
        send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (24 << 8)), 'run 2')
    down = False
    for _ in range(40):
        if not fighting(): break
        h = mem(REC0 + 0x16)[0] & 0xFFFF
        down = down or h == 0                     # once he has fallen, never again: the game revives him before the warp home
        if not down and h > 1: send('poke8 %08X 01' % (REC0 + 0x16), 'poke8 %08X 00' % (REC0 + 0x17))
        send('run 60')
    send('run 200'); mem(G)

# 0. Every place the quest puts someone, and where you stand to talk to them, is floor; the street's fights stand clear of its doors
L, K, S = garlic.LOOKOUT, garlic.KORIN, garlic.SATAN
people = [(L, 'Dende', garlic.DENDE_AT), (L, 'Garlic Jr.', garlic.GARLIC_AT)] + [(L, n, a) for n, a in zip(('Spice', 'Vinegar', 'Mustard', 'Salt'), garlic.SPICE_AT)]
people += [(K, 'Korin', garlic.KORIN_AT), (S, 'Hercule', garlic.HERCULE_AT)]
spots = [(*wa, n, x, y) for wa, n, (x, y) in people] + [(*wa, 'talk to ' + n, x, y + 22) for wa, n, (x, y) in people]
spots += [(*S, 'Makyan', x, y) for x, y in garlic.MAKYANS] + [(*S, 'Goku below a Makyan', x, y + 20) for x, y in garlic.MAKYANS]
spots += [(*L, 'the foe in the Lookout\'s copies', *garlic.LOOK_FOE), (*L, 'Goku arriving there', *garlic.LOOK_ARRIVE), (*L, 'Goku below the foe', garlic.LOOK_FOE[0], garlic.LOOK_FOE[1] + 20)]
spots += [(*L, 'Dende freed', *garlic.FREED[0]), (*L, 'Mr. Popo freed', *garlic.FREED[1])]
spots += [(w, a, 'arrival', x, y) for w, a, _, x, y in (garlic.HOME, garlic.SATAN_AT, garlic.KORIN_ARRIVE)]
walls = [s for s in spots if not FLOOR.walkable(*s[:2], *s[3:])]
check('all %d places the quest puts someone are on walkable floor%s' % (len(spots), (': not ' + str(walls)) if walls else ''), not walls)
street = [(*S, 'Makyan', x, y) for x, y in garlic.MAKYANS] + [(*S, 'Hercule', *garlic.HERCULE_AT), (*S, 'Goku arrives', *garlic.SATAN_AT[3:])]
doors = [(s, FLOOR.near_trigger(s[0], s[1], s[3], s[4])) for s in street]
doors = [d for d in doors if d[1]]
check('the street\'s fights and Hercule stand clear of its doors%s' % ((': not ' + str(doors)) if doors else ''), not doors)
copies = [ROOMS[r] for r in garlic.ROOMS]
check('the Lookout\'s %d copies are rooms of zone 26 (%d-%d) with the Lookout\'s floor' % (len(copies), copies[0], copies[-1]),
      all(FLOOR.walkable(26, r, *garlic.LOOK_FOE) for r in copies) and copies == list(range(copies[0], copies[0] + len(copies))))
rom = open(ROM, 'rb').read()
stats = struct.unpack_from('<I', rom, zone26.STATS_REFS[0])[0] - 0x08000000
MAKYAN_ROW = next(0x08000000 + stats + 28 * k for k in range(400) if rom[stats + 28 * k + 4:stats + 28 * k + 8] == struct.pack('<I', garlic.MAKYAN[2])
                  and rom[stats + 28 * k + 0xC:stats + 28 * k + 0x10] == bytes(garlic.MAKYAN[3]))
import bfscript
e = FLOOR.record(*garlic.SATAN); names = bfscript.load_names(); kept, hidden, other = [], [], []
for k in range(rom[e + 4]):
    q = FLOOR.u32(FLOOR.u32(e + 0x14) - 0x08000000 + 4 * k) - 0x08000000; w = struct.unpack_from('<8I', rom, q)
    char = w[3] if w[0] == zone26.WANDER_SPAWN else w[4]
    text = ''
    if w[1] > 0x08000000:
        dis = bfscript.disasm(rom[w[1] - 0x08000000:w[1] - 0x08000000 + 200], names=names); text = (dis[0] if isinstance(dis, tuple) else dis).split('    end\n')[0]
    mist = 'pushn %d' % garlic.GJ_START in text and 'pushn %d' % garlic.GJ_CURED in text
    if char in zone26.GARLIC_KEEP or w[1] == 1: kept.append(char)
    elif mist or char in (ACTORS['makyan'] + 9, garlic.HERCULE): hidden.append(char)
    else: other.append((char, hex(w[1])))
check('every one of Hercule City\'s people and foes stands aside while the mist is up, but the official (%d kept, %d with the mist\'s test)%s'
      % (len(kept), len(hidden), (': not ' + str(other)) if other else ''), not other and len(hidden) >= 10)
supers = [k for k in range(400) if rom[stats + 28 * k + 4:stats + 28 * k + 8] == struct.pack('<I', HP['super_garlic']) and rom[stats + 28 * k + 0xC:stats + 28 * k + 0x10] == bytes(garlic.FIGHTS[-1][3])]
check('Super Garlic Jr.\'s row takes full physical damage', len(supers) == 1 and rom[stats + 28 * supers[0] + 0x10] == garlic.SUPER_PHYS)
# 1. To Hercule City, then the official's warp to the Lookout; Dende's hint
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
RIG = fightrig.Rig(send, mem, rom)
L150 = RIG.level150(); print('   Goku: level %d -> 150: %d HP, %d ki, Strength/Power/Endurance %s' % L150, flush=True)
check('Goku is a level 150 fighter, made the game\'s way', L150[1] > 4000 and L150[3][0] > 150)
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run %d' % WALK_IN); mem(G)
def talk_until(x, y, want, tries=4):
    for _ in range(tries):
        FLOOR.guard(at(), x, y + 22, 'Goku')
        pl = mem(PLAYER)[0]
        send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80', 'run 200'); mem(G)
        if at() == want: return True
    return False
send('run 100'); talk_until(96, 328, SATAN)
check('before the quest, Hercule City is as it was: no Makyans', at() == SATAN and not any(hp == garlic.MAKYAN[2] for _, hp in foes()))
talk_until(*zone26.HUB_AT, LOOKOUT); send('run 100', 'shot lookout_hint'); mem(G)
check('the rig reaches the Lookout', at() == LOOKOUT)
# (the Makyans are post-game foes: they reach Goku seconds after the carpet lands, and this new save's 135 HP, which Dende's heal
# restores, would fall to them before the fight below: Goku gets the test's full health the moment he lands)
scene(*garlic.DENDE_AT, lambda: at() == SATAN and (heal() or True)); send('run 100', 'shot mist'); mem(G)
check('Dende tells of the Dead Zone and the Makyo Star, and Mr. Popo\'s carpet takes Goku to Hercule City', at() == SATAN and more(garlic.GJ_START))
# 2. The mist: two Makyans; the street's people gone, the official at his post
f = foes()
check('two Makyans of %d HP are on the main street' % garlic.MAKYAN[2], sum(hp == garlic.MAKYAN[2] for _, hp in f) == 2)
check('the tournament official keeps his post', standing(*zone26.HUB_AT))
alive = lambda: [e for e, hp in foes(MAKYAN_ROW) if hp > 0]
got, wrong = BAR.check(); check('the Makyans, a pack and nobody\'s boss fight, have no boss bar: %s' % (wrong or got), got is None and not wrong and BAR.boss()[0] is None)
heal(); beat('a Makyan', lambda: len(alive()) >= 2, row=MAKYAN_ROW)
for _ in range(20):                               # (his defeat script runs once he has fallen and faded, and any level-up box is closed)
    if more(garlic.GJ_FIGHT): break
    send('tap A 10', 'run 50')
check('one Makyan down counts', more(garlic.GJ_FIGHT) and not more(garlic.GJ_MIST) and len(alive()) == 1)
lose(lambda: at() == SATAN and len(alive()) == 1, MAKYAN_ROW); send('run 120', 'shot mist_lost'); mem(G)
seen = (hex(at()), more(garlic.GJ_FIGHT), more(garlic.GJ_MIST), [hp for _, hp in foes(MAKYAN_ROW)], mem(REC0 + 0x16)[0] & 0xFFFF, mem(REC0 + 0x18)[0] & 0xFFFF)
check('lost to the other: back on the street, rested, both Makyans back, the count clear (area, count, mist, Makyans, health: %s)' % (seen,),
      seen[0] == hex(SATAN) and not seen[1] and not seen[2] and seen[3] == [garlic.MAKYAN[2]] * 2 and seen[4] == seen[5])
heal(); beat('both Makyans', lambda: not more(garlic.GJ_MIST), row=MAKYAN_ROW)
send('run 100', 'shot cleared'); mem(G)
check('both down: the street is clear and Hercule comes out', at() == SATAN and more(garlic.GJ_MIST) and not more(garlic.GJ_FIGHT) and standing(*garlic.HERCULE_AT))
# 3. Hercule to Korin, Korin's water, the town cured
scene(*garlic.HERCULE_AT, in_area(KORIN)); send('shot korin'); mem(G)
check('Hercule sends Goku up Korin\'s Tower', at() == KORIN)
scene(*garlic.KORIN_AT, lambda: more(garlic.GJ_CURED) and at() == SATAN); send('run 100', 'shot cured'); mem(G)
check('Korin\'s Sacred Water cures the town: back on the street, no Makyans', at() == SATAN and more(garlic.GJ_CURED) and not foes(MAKYAN_ROW))
scene(*garlic.HERCULE_AT, in_area(LOOKOUT)); send('run 100', 'shot held'); mem(G)
check('Hercule sends Goku to the Lookout', at() == LOOKOUT)
check('Garlic Jr. and the four Spice Boys hold the Lookout', standing(*garlic.GARLIC_AT) and all(standing(*a) for a in garlic.SPICE_AT))
check('Dende and Mr. Popo are gone (his prisoners)', not standing(*garlic.DENDE_AT) and not standing(*garlic.POPO_AT))
# 4. The Spice Boys, with their scenes between; lost at Mustard: back to the Lookout, from Spice again
scene(*garlic.GARLIC_AT, in_area(ROOM['spice'])); send('shot spice'); mem(G)
check('talking to Garlic Jr. starts the fights: Spice, in a copy of the Lookout', at() == ROOM['spice'] and more(garlic.GJ_FIGHT))
heal(); beat('Spice', in_area(ROOM['spice']), HP['spice'])
check('Spice down: Vinegar steps up (a scene of his own)', at() == ROOM['i_vinegar'])
watch(in_area(ROOM['vinegar'])); send('shot vinegar'); mem(G)
heal(); beat('Vinegar', in_area(ROOM['vinegar']), HP['vinegar']); watch(in_area(ROOM['mustard']))
check('then Mustard', at() == ROOM['mustard'])
lose(in_area(ROOM['mustard'])); send('shot lost_mustard'); mem(G)
check('lost to Mustard: back on the Lookout, the fights over, the Spice Boys not beaten', at() == LOOKOUT and not more(garlic.GJ_FIGHT) and not more(garlic.GJ_SPICE))
scene(*garlic.GARLIC_AT, in_area(ROOM['spice']))
check('and talking to Garlic Jr. again starts from Spice', at() == ROOM['spice'])
for name, after in (('spice', 'i_vinegar'), ('vinegar', 'i_mustard'), ('mustard', 'i_salt'), ('salt', 'i_garlic')):
    if at() != ROOM[name]: watch(in_area(ROOM[name]))
    heal(); beat(name.title(), in_area(ROOM[name]), HP[name])
    check('%s down: on to the next scene' % name.title(), at() == ROOM[after])
check('Salt down: the Spice Boys are beaten', more(garlic.GJ_SPICE))
watch(in_area(ROOM['garlic_jr'])); send('shot garlic'); mem(G)
check('Garlic Jr. fights himself', at() == ROOM['garlic_jr'])
lose(in_area(ROOM['garlic_jr']))
check('lost to Garlic Jr.: back on the Lookout, the Spice Boys gone, Garlic Jr. waiting', at() == LOOKOUT and more(garlic.GJ_SPICE) and standing(*garlic.GARLIC_AT)
      and not any(standing(*a) for a in garlic.SPICE_AT))
scene(*garlic.GARLIC_AT, in_area(ROOM['garlic_jr']), presses=60)
check('talking to him again goes straight to him', at() == ROOM['garlic_jr'])
# 5. Garlic Jr., his change, Super Garlic Jr., the seal
heal(); beat('Garlic Jr.', in_area(ROOM['garlic_jr']), HP['garlic_jr']); send('shot change'); mem(G)
check('Garlic Jr. down: his change into Super Garlic Jr. (a scene)', at() == ROOM['change'])
watch(in_area(ROOM['super_garlic'])); send('shot super'); mem(G)
check('then Super Garlic Jr.', at() == ROOM['super_garlic'])
heal(); f = foes(); hp0 = mem(REC0 + 0x16)[0] & 0xFFFF; hit = False   # he fights (Spopovich's row 112 and frames): left alone, he hits Goku
if f:
    x, y = mem(f[0][0] + 0x1A0, 2); pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (24 << 8)), 'run 30', 'shot super_near')
    for _ in range(20):
        send('run 60')
        if mem(REC0 + 0x16)[0] & 0xFFFF < hp0: hit = True; break
send('shot super_hits'); mem(G)
check('Super Garlic Jr. fights: left alone beside him, Goku is hit', hit)
heal(); beat('Super Garlic Jr.', in_area(ROOM['super_garlic']), HP['super_garlic']); send('shot seal'); mem(G)
check('Super Garlic Jr. down: the Dead Zone opens (a scene)', at() == ROOM['seal'])
z0 = mem(ZENIE)[0]
for k in range(80):                               # press A about six times a second through the lines and the meter, as test_zone26.py does
    if more(garlic.GJ_DONE) and at() == LOOKOUT: break
    send('tap A 5', 'run 5')
send('run 200', 'shot home'); mem(G)
g = dump(G, 0x8A8, 'g'); bag = [struct.unpack_from('<I', g, 0xE8 + 4 * i)[0] & 0xFFFFFFF for i in range(min(g[0xE4], 250))]
check('pushed into the Dead Zone: the quest is done, home on the Lookout', more(garlic.GJ_DONE) and not more(garlic.GJ_FIGHT) and at() == LOOKOUT)
check('Garlic Jr.\'s Necklace (gear %d) is Goku\'s' % garlic.GEAR_NECKLACE, garlic.GEAR_NECKLACE in bag)
check('and %d Zenie' % garlic.ZENIE, mem(ZENIE)[0] - z0 == garlic.ZENIE)
send('run 120'); mem(G)
seen = (standing(*garlic.DENDE_AT), standing(*garlic.POPO_AT), standing(*garlic.GARLIC_AT))
check('Dende and Mr. Popo are back at their spots; Garlic Jr. is gone (Dende, Mr. Popo, Garlic Jr. standing: %s)' % (seen,), seen == (True, True, False))
# 6. The balance, on a level 150 Goku (the owner, Nov 9: "Test these with a level 150 Goku or something so he doesnt die so much and has
# some balancing"; garlic.FIGHTS): from each real exchange (fightrig.spar), the hits he needs and the share of his health each of theirs takes
B = RIG.BAL
need = lambda n: 1 / B[n]['hit'] if n in B and B[n]['hit'] else 0
boys = [need(n) for n in ('Spice', 'Vinegar', 'Mustard', 'Salt')]
print('   hits to beat: Makyan %.0f, Spice Boys %s, Garlic Jr. %.0f, Super Garlic Jr. %.0f' % (need('a Makyan'), ['%.0f' % b for b in boys], need('Garlic Jr.'), need('Super Garlic Jr.')))
check('a Makyan takes 6-20 of level 150 Goku\'s hits', 6 <= need('a Makyan') <= 20)
check('each Spice Boy takes 10-35', all(10 <= b <= 35 for b in boys))
check('Garlic Jr. takes 18-50', 18 <= need('Garlic Jr.') <= 50)
check('Super Garlic Jr. takes 28-70, the most of the quest', 28 <= need('Super Garlic Jr.') <= 70 and need('Super Garlic Jr.') > max(boys + [need('Garlic Jr.')]))
hurts = {n: b['taken'] for n, b in B.items() if b['hurt']}
check('no hit of theirs takes more than 12%% of his health, Super Garlic Jr.\'s at most 10%% (Beerus\'s stay the hardest): %s'
      % ', '.join('%s %.1f%%' % (n, 100 * t) for n, t in hurts.items()), all(t <= 0.12 for t in hurts.values()) and hurts.get('Super Garlic Jr.', 0) <= 0.10)
check('no bad jumps', not bad[0])
send('quit')
print('screens in', D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
