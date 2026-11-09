#!/usr/bin/env python3
"""Separate progress for the guest slot's fighters. Needs a zone debug build made with BFU_SLOT_TEST=1, where the official opens Switch Character and then saves:
  BFU_SLOT_TEST=1 BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_slots.py <dir> <old debug rom> [work dir]
Exits non-zero on failure."""
import json, os, shutil, struct, subprocess, sys, tempfile
H = 'tools/harness/harness'
OUT = sys.argv[1]; OLD = sys.argv[2]
d = sys.argv[3] if len(sys.argv) > 3 else tempfile.mkdtemp(prefix='slots'); os.makedirs(d, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
forms = json.load(open(OUT + '/BFU_debug_zone.map.json'))['forms']
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
G = 0x03001068; RECS = 0x03001560; REC = 0x68; R8 = RECS + 8 * REC; GEN_AT = 0x4F1; BENCH = 0x0203F000; BENCH_SIZE = 496; BENCH_OFFSET = 0x1A20
fails = []
def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    if not ok: fails.append(name)
def run(lines, sav=None, rom=ROM):
    p = d + '/s.txt'; open(p, 'w').write('\n'.join(lines) + '\n')
    env = dict(os.environ); env.pop('HARNESS_SAV', None)
    if sav: env['HARNESS_SAV'] = sav
    return subprocess.run([H, rom, p, d], capture_output=True, text=True, env=env, timeout=550).stdout
ROM_BYTES = open(ROM, 'rb').read()
ROW = 39; SLOT = ROM_BYTES[0x6F8300 + ROW * 0x2C]
EMPTY = (0, 0x2C, 0x4D, 0x70)
def wear(row, count=1):
    """Put this row in the bag and on the guest, as the equipment screen does."""
    return ['poke %08X %08X' % (G + 0xE4, count), 'poke %08X %08X' % (G + 0xE8, row | 9 << 28), 'poke %08X %08X' % (R8 + 0x3C + SLOT * 4, row)]
def poke_rec(exp=None, stat=None, gear=None, hp=None):
    o = []
    if exp is not None: o.append('poke %08X %08X' % (R8 + 0x24, exp))
    if stat is not None: o.append('poke8 %08X %02X' % (R8 + 0x28, stat))
    if gear is not None: o += wear(gear)
    if hp is not None: o += ['poke8 %08X %02X' % (R8 + 0x16, hp & 255), 'poke8 %08X %02X' % (R8 + 0x17, hp >> 8)]
    return o
def state(name='x'):
    return ['dump %s %08X 8a8' % (name, G)]
def read(name='x'):
    g = open('%s/%s.bin' % (d, name), 'rb').read()
    r = g[0x4F8 + 8 * REC:0x4F8 + 9 * REC]
    return dict(cur=g[0], form=r[0x14], hp=struct.unpack_from('<H', r, 0x16)[0], maxhp=struct.unpack_from('<H', r, 0x18)[0], exp=struct.unpack_from('<I', r, 0x24)[0], stat=r[0x28],
                gear=struct.unpack_from('<4I', r, 0x3C), gen=g[GEN_AT] | g[GEN_AT + 1] << 8, out=g[GEN_AT + 2], bag=struct.unpack_from('<%dI' % struct.unpack_from('<I', g, 0xE4)[0], g, 0xE8), raw=g)
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
def talk_at(base, x, y, sav=None):
    lines = list(base)
    pl = int([l for l in run(lines + ['mem 03001C34 1'], sav).splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
    return lines + ['poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80']
TO_GUEST = ['tap RIGHT 30'] * 5
DOWN = lambda n: ['tap DOWN 30'] * n
UP = lambda n: ['tap UP 30'] * n
CONFIRM = ['tap A 200', 'run 120']
CANCEL = ['tap B 200', 'run 120']
# The guests this route has open, in picker order (the rest stay locked and the picker skips them). Older builds lack Goku Black and GT.
OPEN = ['broly', 'broly_fp', 'android13', 'piccolo', 'tien', 'yamcha', 'pikkon', 'hercule', 'goku_black',
        'pan', 'pan_nobandana', 'pan_gi_tan', 'pan_gi_red', 'pan_bug', 'pan_brapan', 'uub', 'roshi']     # Master Roshi (Nov 9)
OPEN_V1 = OPEN[:8]
def go(a, b, open_=OPEN):
    """Down presses from guest a to guest b, round the list."""
    return DOWN((open_.index(b) - open_.index(a)) % len(open_))
ORDER = ['broly', 'broly_fp', 'android13', 'piccolo', 'future_trunks', 'android17', 'android18', 'krillin', 'videl', 'majin_buu', 'super_janemba', 'kid_buu']

# 1. A save from before this change is the same save: same route, same bytes, with the new area untouched.
one = open('tools/harness/long.txt').read().split('\n')[:93] + ['tap A 60', 'tap A 60', 'run 30'] + TO_GUEST + CONFIRM + ['run 80'] + state('o')
old_sav, new_sav = d + '/oldrom.sav', d + '/newrom.sav'
for f in (old_sav, new_sav):
    if os.path.exists(f): os.remove(f)
out = run(one, old_sav, OLD); ga = open(d + '/o.bin', 'rb').read()
newdebug = OUT + '/BFU_debug_PERSONAL_USE_ONLY.gba'
out2 = run(one, new_sav, newdebug); gb = open(d + '/o.bin', 'rb').read()
check('no bad jumps in old or new', 'bad pc' not in out + out2)
moved = list(range(0x55 + 75, 0x55 + 85)) + list(range(0xC0, 0xC5)) + [0xE2, 0xE3]      # only the custom flags moved
# the skill book (Nov 9) learns what play has earned as soon as a record syncs (Goku's Kaioken, Vegeta's Galick Gun...): skills, their levels, the book's mask
moved += [0x4F8 + c * 0x68 + o for c in range(9) for o in list(range(0x0C, 0x14)) + [0x15, 0x22, 0x23] + list(range(0x2E, 0x3C))]
strip = lambda g: bytes(b for i, b in enumerate(g) if i not in moved)
check('the same route leaves the same game state, apart from where the new flags live', strip(ga) == strip(gb))
sa, sb = open(old_sav, 'rb').read(), open(new_sav, 'rb').read()
check('nothing is written after the game blocks', set(sb[0x1A20:]) == {255})
two = ['run 600', 'tap START 60', 'tap START 60', 'tap A 90', 'tap A 120', 'tap A 200', 'tap A 200', 'run 200'] + state('l')
run(two, old_sav, OLD); la = open(d + '/l.bin', 'rb').read()
keep = d + '/k.sav'; shutil.copy(old_sav, keep)
out = run(two, keep, newdebug); lb = open(d + '/l.bin', 'rb').read()
check('an old save loads into the new build unchanged (the skill book apart)', 'bad pc' not in out and strip(la) == strip(lb) and lb[0] == 8)
check('loading writes nothing', open(keep, 'rb').read() == sa)

# 2. Fresh variables, whatever the save held: the memory that used to overlap the save mirror.
fresh = d + '/fresh.sav'
if os.path.exists(fresh): os.remove(fresh)
out = run(['run 300', 'mem 0203FF20 24', 'mem 03004A64 1'], fresh)
mems = [l for l in out.splitlines() if l.startswith('mem')]
check('variables start clear on an empty save', set(mems[0].split(':')[1].split()) == {'00000000'})
mirror = int(mems[1].split()[2], 16)
check('the save mirror is below the kept memory', mirror + 0x2000 <= 0x0203F000)

# 3. Swaps. Each run replays from a new game, so the save file starts empty each time.
sav = d + '/g.sav'
def fresh(lines):
    if os.path.exists(sav): os.remove(sav)
    return run(lines, sav)
P = open(os.environ['BFU_PROTO'], 'rb').read(); cfg = json.load(open('ultimate/zone26.json'))
door = [x for x in zone26.links(cfg, {a: zone26.floor_mask(P, os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
KEYS = 'DOWN UP LEFT RIGHT'.split(); PL = 0x0202E8E4
home = list(start)
x0, y0, x1, y1 = door['rect']
home += ['poke %08X %08X' % (PL + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (PL + 0x1A4, ((y0 + y1) // 2) << 8), 'keys ' + KEYS[door['key']], 'run 12', 'keys', 'run 110']
hub = talk_at(home + ['poke8 %08X %02X' % (G + 0x55 + 862 // 8, 1 << 862 % 8), 'poke8 %08X %02X' % (G + 0x55 + 883 // 8, 1 << 883 % 8)], 96, 328)
hub = talk_at(hub + ['run 200'], *zone26.HUB_AT)           # the picker is open now
at = lambda base: talk_at(base, *zone26.HUB_AT, sav=None)
s = hub + ['shot hub0'] + TO_GUEST + ['shot hub1'] + CONFIRM + ['shot hub2'] + state('a')
out = fresh(s); a = read('a')
check('no bad jumps reaching the picker', 'bad pc' not in out)
check('picking without changing outfit swaps nothing', a['gen'] == 0 and a['out'] == 0 and a['form'] == forms['broly'])
check('and the save stays clean', set(open(sav, 'rb').read()[0x1A20:]) == {255})
base_stats = a

s1 = hub + poke_rec(exp=111111, stat=11, gear=ROW, hp=77) + TO_GUEST + DOWN(3) + CONFIRM + state('b')
out = fresh(s1); b = read('b')
check('first swap: Piccolo on', 'bad pc' not in out and b['form'] == forms['piccolo'])
check('first swap: level and stats start from the guest who was out', b['exp'] == 111111 and b['stat'] == 11)
check('first swap: rested', b['hp'] == b['maxhp'])
check('first swap: nothing equipped, and the gear is back in the bag', b['gear'] == EMPTY and b['bag'] == (ROW,))
check('first swap: generation and fighter recorded', b['gen'] != 0 and b['out'] == 3)
def eeprom(path):
    """The save file holds each 8-byte block back to front."""
    f = open(path, 'rb').read()
    return b''.join(f[i:i + 8][::-1] for i in range(0, len(f), 8))
raw = eeprom(sav)
head = struct.unpack_from('<III', raw, BENCH_OFFSET)
check('the bench reached the save', head[0] == 0x32484342 and head[1] == b['gen'])
check('other games\' benches and the end of the save are untouched', set(raw[BENCH_OFFSET + BENCH_SIZE:]) == {255})

s2 = talk_at(s1, *zone26.HUB_AT) + poke_rec(exp=222222, stat=22, hp=88) + TO_GUEST + UP(3) + CONFIRM + state('c')
out = fresh(s2); c = read('c')
check('back to Broly: his own progress returns, rested', 'bad pc' not in out and c['form'] == forms['broly'] and c['exp'] == 111111 and c['stat'] == 11 and c['hp'] == c['maxhp'] and c['gear'][SLOT] == ROW and c['bag'] == (ROW | 9 << 28,))
s3 = talk_at(s2, *zone26.HUB_AT) + TO_GUEST + DOWN(1) + CONFIRM + state('e')
out = fresh(s3); e = read('e')
check('Full Power is still Broly', 'bad pc' not in out and e['form'] == forms['broly_fp'] and e['exp'] == 111111 and e['gen'] == c['gen'] and e['gear'][SLOT] == ROW)
s4 = talk_at(s3, *zone26.HUB_AT) + TO_GUEST + DOWN(2) + CANCEL + state('f')
out = fresh(s4); f = read('f')
check('B leaves everything alone', 'bad pc' not in out and f['form'] == forms['broly_fp'] and f['exp'] == 111111 and f['gen'] == c['gen'])
s5 = talk_at(s4, *zone26.HUB_AT) + TO_GUEST + DOWN(2) + CONFIRM + state('h')
out = fresh(s5); h = read('h')
check('Piccolo\'s progress is his', 'bad pc' not in out and h['form'] == forms['piccolo'] and h['exp'] == 222222 and h['stat'] == 22 and h['hp'] == h['maxhp'] and h['gear'] == EMPTY and h['bag'] == (ROW,))
# Only the guest who is out wears anything, so one piece worn by two fighters goes on whichever of them comes out, and is never in two places.
g1 = talk_at(s5, *zone26.HUB_AT) + wear(ROW) + TO_GUEST + UP(3) + CONFIRM + state('j')
out = fresh(g1); j = read('j')
check('shared gear goes on the fighter who comes out', 'bad pc' not in out and j['form'] == forms['broly'] and j['gear'][SLOT] == ROW and j['bag'] == (ROW | 9 << 28,))
g2 = talk_at(g1, *zone26.HUB_AT) + TO_GUEST + DOWN(3) + CONFIRM + state('k')
out = fresh(g2); k = read('k')
check('and moves with the next swap', 'bad pc' not in out and k['form'] == forms['piccolo'] and k['gear'][SLOT] == ROW and k['bag'] == (ROW | 9 << 28,))
walk = s5 + ['keys RIGHT', 'run 30', 'keys', 'tap A 8', 'run 30', 'shot piccolo_walks'] + state('w')
out = fresh(walk)
check('the swapped fighter walks and attacks', 'bad pc' not in out)

# 4. Off and on again: the whole bench comes back from the save.
after = d + '/after.sav'
def from_save(lines, src=None):
    shutil.copy(src or sav, after)
    return run(lines, after)
BOOT = ['run 600', 'tap START 60', 'tap START 60', 'tap A 90', 'tap A 120', 'tap A 200', 'tap A 200', 'run 300']
out = from_save(BOOT + state('r')); r = read('r')
check('reload: Piccolo as saved', 'bad pc' not in out and r['form'] == forms['piccolo'] and r['exp'] == h['exp'] and r['gen'] == h['gen'])
shutil.copy(sav, after); back = talk_at(BOOT, *zone26.HUB_AT, sav=after) + TO_GUEST + UP(3) + CONFIRM + state('i')
out = from_save(back); i = read('i')
check('reload: Broly comes back from the save', 'bad pc' not in out and i['form'] == forms['broly'] and i['exp'] == 111111 and i['stat'] == 11 and i['gear'][SLOT] == ROW and i['bag'] == (ROW | 9 << 28,))

# 5. A swap that was never saved, then a reload of the game while still powered on: memory holds a newer bench than the save. Simulated by making the bench in memory look
# newer and full of nonsense: the next swap must read the save's bench, not this.
bad = []
for k in range(4): bad.append('poke %08X %08X' % (BENCH + 4 + k * 4, 0x00123456 + k))
shutil.copy(sav, after); s6 = talk_at(BOOT, *zone26.HUB_AT, sav=after) + bad + TO_GUEST + UP(3) + CONFIRM + state('n')
out = from_save(s6); n = read('n')
check('a stale bench in memory is ignored', 'bad pc' not in out and n['exp'] == 111111 and n['gear'][SLOT] == ROW)

# 6. Damage: a corrupt bench is an empty bench, not a crash, and nothing else in the save changes.
broken = d + '/broken.sav'; raw = bytearray(open(sav, 'rb').read()); raw[BENCH_OFFSET + 40] ^= 0x55; open(broken, 'wb').write(raw)      # any byte of the block will do
shutil.copy(broken, after); s7 = talk_at(BOOT, *zone26.HUB_AT, sav=after) + TO_GUEST + UP(3) + CONFIRM + state('q')
out = from_save(s7, broken); q = read('q')
check('a damaged bench starts empty', 'bad pc' not in out and q['form'] == forms['broly'] and q['exp'] == h['exp'] and q['gear'] == EMPTY)

# 7. The newest fighters' smaller records, Hercule's running on past the tail, and the saved flags beside them.
t1 = hub + poke_rec(exp=500016, stat=9, gear=ROW) + TO_GUEST + go('broly', 'tien') + CONFIRM + state('t1')
out = fresh(t1); a = read('t1')
check('small: Tien on, and gear back in the bag', 'bad pc' not in out and a['form'] == forms['tien'] and a['bag'] == (ROW,))
t2 = talk_at(t1, *zone26.HUB_AT) + poke_rec(exp=600000, stat=31) + TO_GUEST + DOWN(3) + CONFIRM + state('t2')
out = fresh(t2); a = read('t2')
check('small: Hercule on, level with the guest who was out', 'bad pc' not in out and a['form'] == forms['hercule'] and a['exp'] == 600000)
t3 = talk_at(t2, *zone26.HUB_AT) + poke_rec(exp=700000, stat=41, hp=5) + ['poke8 %08X 3C' % (BENCH + 12)] + TO_GUEST + UP(3) + CONFIRM + state('t3') + ['dump m 0203F00C 4']
out = fresh(t3); a = read('t3')
check('small: back to Tien, his own progress, rested', 'bad pc' not in out and a['form'] == forms['tien'] and a['exp'] == 600000 and a['stat'] == 31 and a['hp'] == a['maxhp'])
check('small: only three bench sizes of data: the save stops where it should', set(eeprom(sav)[BENCH_OFFSET + BENCH_SIZE:]) == {255})
shutil.copy(sav, after); t4 = talk_at(BOOT, *zone26.HUB_AT, sav=after) + TO_GUEST + DOWN(3) + CONFIRM + state('t4') + ['dump m 0203F00C 4']
out = from_save(t4); a = read('t4')
check('small: Hercule comes back from the save', 'bad pc' not in out and a['form'] == forms['hercule'] and a['exp'] == 700000 and a['stat'] == 41)
check('the saved flags come back too', open(d + '/m.bin', 'rb').read()[0] == 0x3C)

# 7b. Goku Black, a fighter version 1 had no room for: his own progress too, and Rose is him.
b1 = talk_at(t2, *zone26.HUB_AT) + poke_rec(exp=800000, stat=61) + TO_GUEST + go('hercule', 'goku_black') + CONFIRM + state('b1')
out = fresh(b1); a = read('b1')
check('Goku Black on, level with the guest who was out', 'bad pc' not in out and a['form'] == forms['goku_black'] and a['exp'] == 800000)
b2 = talk_at(b1, *zone26.HUB_AT) + poke_rec(exp=900000, stat=71) + TO_GUEST + go('goku_black', 'hercule') + CONFIRM + state('b2')
out = fresh(b2); a = read('b2')
check('back to Hercule: his own progress', 'bad pc' not in out and a['form'] == forms['hercule'] and a['exp'] == 800000 and a['stat'] == 61)
b3 = talk_at(b2, *zone26.HUB_AT) + TO_GUEST + go('hercule', 'goku_black') + CONFIRM + state('b3')
out = fresh(b3); a = read('b3')
check('and Goku Black\'s back', 'bad pc' not in out and a['form'] == forms['goku_black'] and a['exp'] == 900000 and a['stat'] == 71)

# 7c. GT: Pan's six looks are one fighter (one bench group); Uub is another.
c1 = talk_at(b3, *zone26.HUB_AT) + poke_rec(exp=1000000, stat=75) + TO_GUEST + go('goku_black', 'pan') + CONFIRM + state('c1')
out = fresh(c1); a = read('c1')
check('Pan on, level with the guest who was out', 'bad pc' not in out and a['form'] == forms['pan'] and a['exp'] == 1000000)
c2 = talk_at(c1, *zone26.HUB_AT) + poke_rec(exp=1100000, stat=80) + TO_GUEST + go('pan', 'pan_gi_red') + CONFIRM + state('c2')
out = fresh(c2); a = read('c2')
check('another of Pan\'s looks is still Pan: same progress', 'bad pc' not in out and a['form'] == forms['pan_gi_red'] and a['exp'] == 1100000 and a['stat'] == 80)
c3 = talk_at(c2, *zone26.HUB_AT) + TO_GUEST + go('pan_gi_red', 'uub') + CONFIRM + poke_rec(exp=1200000, stat=90) + state('c3')
c4 = talk_at(c3, *zone26.HUB_AT) + TO_GUEST + go('uub', 'pan_bug') + CONFIRM + state('c4')
out = fresh(c4); a = read('c4')
check('Uub keeps his own; Pan comes back with hers', 'bad pc' not in out and a['form'] == forms['pan_bug'] and a['exp'] == 1100000 and a['stat'] == 80)

# 8. A bench saved by a build before version 2 (pass its slot-test ROM as a fourth argument): every fighter's progress carries over.
OLD_SLOT = sys.argv[4] if len(sys.argv) > 4 else None
if OLD_SLOT:
    def old(lines):
        if os.path.exists(sav): os.remove(sav)
        return run(lines, sav, OLD_SLOT)
    maxhp = lambda v: ['poke8 %08X %02X' % (R8 + 0x18, v & 255), 'poke8 %08X %02X' % (R8 + 0x19, v >> 8)]
    m1 = hub + poke_rec(exp=333333, stat=33, gear=ROW) + maxhp(345) + ['poke8 %08X %02X' % (R8 + 0x2E + i, v) for i, v in enumerate((3, 3, 2, 2, 1, 1))] + TO_GUEST + go('broly', 'piccolo', OPEN_V1) + CONFIRM
    m2 = talk_at(m1, *zone26.HUB_AT) + poke_rec(exp=444448, stat=44) + TO_GUEST + go('piccolo', 'tien', OPEN_V1) + CONFIRM
    m3 = talk_at(m2, *zone26.HUB_AT) + poke_rec(exp=555552, stat=55) + TO_GUEST + go('tien', 'yamcha', OPEN_V1) + CONFIRM + state('m3')
    out = old(m3); a = read('m3')
    check('old build: Yamcha out after Piccolo and Tien', 'bad pc' not in out and a['form'] == forms['yamcha'])
    check('old build saved a version 1 bench', struct.unpack_from('<I', eeprom(sav), BENCH_OFFSET)[0] == 0x31484342)
    v1 = d + '/v1.sav'; shutil.copy(sav, v1)
    t = talk_at(BOOT, *zone26.HUB_AT, sav=v1) + TO_GUEST + go('yamcha', 'broly') + CONFIRM + state('m4')
    out = from_save(t, v1); a = read('m4')
    check('new build: Broly from a version 1 bench', 'bad pc' not in out and a['form'] == forms['broly'] and a['exp'] == 333333 and a['stat'] == 33 and a['maxhp'] == 345 and a['gear'][SLOT] == ROW and a['hp'] == a['maxhp'])
    lv = a['raw'][0x4F8 + 8 * REC + 0x2E:0x4F8 + 8 * REC + 0x34]
    check('and his skill levels', tuple(lv) == (3, 3, 2, 2, 1, 1))
    check('the bench is version 2 once saved', struct.unpack_from('<I', eeprom(after), BENCH_OFFSET)[0] == 0x32484342)
    shutil.copy(after, v1 + '2'); t = talk_at(BOOT, *zone26.HUB_AT, sav=v1 + '2') + TO_GUEST + go('broly', 'tien') + CONFIRM + state('m5')
    out = from_save(t, v1 + '2'); a = read('m5')
    check('new build: Tien\'s small entry carried over', 'bad pc' not in out and a['form'] == forms['tien'] and a['exp'] == 555552 and a['stat'] == 55)
    shutil.copy(after, v1 + '3'); t = talk_at(BOOT, *zone26.HUB_AT, sav=v1 + '3') + TO_GUEST + go('tien', 'piccolo') + CONFIRM + state('m6')
    out = from_save(t, v1 + '3'); a = read('m6')
    check('new build: Piccolo\'s full entry carried over', 'bad pc' not in out and a['form'] == forms['piccolo'] and a['exp'] == 444448 and a['stat'] == 44)
    shutil.copy(after, v1 + '4'); t = talk_at(BOOT, *zone26.HUB_AT, sav=v1 + '4') + TO_GUEST + go('piccolo', 'yamcha') + CONFIRM + state('m7')
    out = from_save(t, v1 + '4'); a = read('m7')
    check('new build: Yamcha too', 'bad pc' not in out and a['form'] == forms['yamcha'] and a['exp'] == 555552 and a['stat'] == 55)

print('fails:', fails) if fails else print('ALL PASS')
sys.exit(1 if fails else 0)
