#!/usr/bin/env python3
"""Super 13 fought by hand, the way a player does (build `--debug --zone` first; set BFU_PROTO):
  python3 ultimate/test_super13.py [work dir] [rom]
The zone's route to Super 13 (as test_zone26.py), then a fighter with stats 180 walks up to him and punches from whichever side he
stands, for about 100 seconds, with no teleports. Nov 9, the owner: "can't even damage and he's stuck walking up". He ran Dabura's
behaviour, whose mid-fight scene walks to a point of Dabura's own room, inside this arena's rocks; up there he was drawn behind them and
no hit reached him; then "replace that, don't make him do that at 60%": his flying special (outfit.c arena_keep, no_story_walk). Checks: he
never starts the special, takes most of his damage, and stays on the open snowfield."""
import json, os, struct, subprocess, sys, tempfile, queue, threading
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
W = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='s13'); os.makedirs(W, exist_ok=True)
ROM = sys.argv[2] if len(sys.argv) > 2 else 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
PROTO = os.environ['BFU_PROTO']; P = open(PROTO, 'rb').read(); cfg = json.load(open('ultimate/zone26.json'))
D = zone26.links(cfg, {a: zone26.floor_mask(P, PROTO, a) for a in range(1, 16)})
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
KEYS = 'DOWN UP LEFT RIGHT'.split(); PL = 0x0202E8E4
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
route = list(start)
for a in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14):
    door = [x for x in D[a] if x['to'] == {8: 10}.get(a, a + 1) and 'world' not in x][0]; x0, y0, x1, y1 = door['rect']
    route += ['poke %08X %08X' % (PL + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (PL + 0x1A4, ((y0 + y1) // 2) << 8), 'keys ' + KEYS[door['key']], 'run 12', 'keys', 'run 110']

env = dict(os.environ); env.pop('HARNESS_SAV', None)
p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', W], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
q = queue.Queue(); bad = [False]
def drain():
    for line in p.stdout:
        if 'bad pc' in line: bad[0] = True
        if line.startswith('mem '): q.put(line)
threading.Thread(target=drain, daemon=True).start()
def send(*ls):
    for l in ls: p.stdin.write(l + '\n')
    p.stdin.flush()
def mem(a, n=1):
    send('mem %08X %d' % (a, n))
    while True:
        l = q.get(timeout=600)
        if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
def find(hp):
    send('dump w 02000000 40000'); mem(0x03001068); w = open(W + '/w.bin', 'rb').read(); i = w.find(struct.pack('<I', hp << 10))
    return 0x02000000 + i if i >= 0 else None

send(*route, 'run 30'); mem(0x03001068)
# Android 13 (phase one) is test_zone26.py's: leave him 2 HP and punch, then his change and the walk up to Super 13
a = find(30000); pl = mem(0x03001C34)[0]; x, y = mem(a - 0xEC, 2)
send('poke %08X %08X' % (a, 2 << 10), 'poke8 03001577 7F', 'poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)),
     'keys UP', 'run 6', 'keys', 'tap A 14', 'tap A 14', 'tap A 14', 'poke8 03001577 7F', *['tap A 25'] * 11, 'tap A 41', 'run 130',
     'tap A 60', 'tap A 60', 'tap A 60', 'run 300', 'keys UP', 'run 60', 'keys', 'run 120')
check('the route reaches Super 13', mem(0x0300197C)[0] & 0xFFFF == (17 << 8 | 26))
a = find(75000); check('Super 13 has 75000 HP', a is not None)
if a is None: sys.exit('FAILED: %s' % fails)
foe = a - 0x28C; pl = mem(0x03001C34)[0]
send('poke %08X %08X' % (pl + 0x1B0, 180 | 180 << 16), 'poke %08X %08X' % (pl + 0x1B4, 180 | 180 << 16), 'run 2')     # a level 200 fighter's stats
hps, spots, special = [], [], []
frames0 = mem(0x03000F94)[0]                                      # the game's frame counter: does it keep up with the emulator?
emu = 0
for k in range(150):
    hp = mem(foe + 0x28C)[0] >> 10; fx, fy = [v >> 8 for v in mem(foe + 0x1A0, 2)]; px, py = [v >> 8 for v in mem(pl + 0x1A0, 2)]
    state = (mem(foe + 0x244)[0] - 0x0870F514) // 8
    if 0x79 <= state <= 0x7F: special.append((k, hex(state)))          # Dabura's flying special (outfit.c no_story_walk)
    hps.append(hp); spots.append((fx, fy))
    if hp < 8000: send('poke %08X %08X' % (foe + 0x28C, 30000 << 10))     # keep him in the fight (once he chased, this fighter beat him in 95 steps)
    dx, dy = fx - px, fy - py
    send('poke8 03001577 7F')                                          # the fighter stays up
    if abs(dx) <= 22 and abs(dy) <= 26:
        send('keys ' + (('RIGHT' if dx > 0 else 'LEFT') if abs(dx) > abs(dy) else ('DOWN' if dy > 0 else 'UP')), 'run 2', 'keys')
        send(*['keys A', 'run 3', 'keys', 'run 3'] * 3, 'run 8')
    else:
        key = ('RIGHT' if dx > 14 else 'LEFT' if dx < -14 else '') + (' DOWN' if dy > 18 else ' UP' if dy < -18 else '')
        send('keys ' + (key.strip() or 'UP'), 'run 32', 'keys')
    send('run 8')
    emu += 8 + (2 + 3 * 6 + 8 if abs(dx) <= 22 and abs(dy) <= 26 else 32)
    if k % 30 == 0: send('shot fight_%03d' % k)
print('   HP every 15 steps:', hps[::15])
print('   game frames %d in %d emulated' % (mem(0x03000F94)[0] - frames0, emu))
check('punches land on him', hps[-1] < 75000)
check('he never goes into Dabura\'s flying special (rising off screen, the white flash)%s' % ((': ' + str(special[:4])) if special else ''), not special)
# How much he loses is chaotic: the same fight played on builds an unrelated change apart took him to 36%, 41% and 73% (Nov 9). What the
# fix is about: he takes damage all fight, never a long untouchable stretch (the bug: 8% in all, nothing after he reached the rocks).
check('he loses at least a quarter of his health in about 100 seconds (the build before the fix: 8%%): %d%%' % ((75000 - min(hps)) * 100 // 75000), min(hps) < 56250)
still = max(len(list(g)) for _, g in __import__('itertools').groupby(hps))
check('no stretch of 45 steps (about 30 seconds) without a hit landing: longest %d' % still, still < 45)
out = [(x, y) for x, y in spots if y < 112 or not 32 <= x <= 288]
check('he stays on the open snowfield, out of the rocks%s' % ((': ' + str(out[:5])) if out else ''), not out)
# He comes and hits a fighter standing still anywhere on the field (Nov 10, the owner: "He's standing still punching the air not trying to
# walk to the player and attack"): from seven spots round it, 12 seconds each, the fighter's health (record +0x16) must drop.
REC = 0x03001560 + (mem(0x03001068)[0] & 255) * 0x68; reach = []
send('poke %08X %08X' % (pl + 0x1B0, 1 | 1 << 16), 'poke %08X %08X' % (pl + 0x1B4, 1 | 1 << 16))       # a fighter who barely hurts him
for sx, sy in ((32, 200), (288, 200), (160, 112), (160, 240), (60, 130), (260, 130), (40, 240)):
    hp0 = mem(REC + 0x16)[0] & 0xFFFF; low = hp0
    for k in range(72):
        send('poke %08X %08X' % (pl + 0x1A0, sx << 8), 'poke %08X %08X' % (pl + 0x1A4, sy << 8), 'run 10')
        low = min(low, mem(REC + 0x16)[0] & 0xFFFF)
    reach.append(((sx, sy), hp0 - low))
    send('poke8 %08X %02X' % (REC + 0x16, hp0 & 255), 'poke8 %08X %02X' % (REC + 0x17, hp0 >> 8), 'run 30')
print('   damage he did at each spot:', reach)
# All seven must land. (Nov 10 left a gap: after the long fight above, a fighter held in the bottom-left corner (40, 240) took no hits,
# Super 13 standing beside him punching at head height. Nov 11 the full run had the same at the left edge, (32, 200): he stood at (56, 208),
# inside the reach arena_chase let him stand at, and no punch landed in twelve seconds. He lines up with the fighter now when none land.)
check('he reaches and hits a fighter standing still anywhere on the field, the edges and the bottom-left corner too', all(d > 0 for _, d in reach))
check('no bad jumps', not bad[0])
p.stdin.close(); p.wait(timeout=60)
print('screens in', W)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
