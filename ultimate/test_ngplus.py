#!/usr/bin/env python3
"""New Game+ (Nov 9): Bulma's time machine at Capsule Corporation, after the ending. Needs a zone debug build whose official warps there:
  BFU_HUB_WARP="4, 20, 1, 232, 280" BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_ngplus.py <dir> [work dir]
Before the ending Bulma asks about the World Tournament as she always did; after it she offers the time machine. Going back clears the
story (the ending's flag 149 among it), keeps the party's levels, skills and bag, counts the round (more flags 47-48), and plays the
story's opening on Snake Way with Goku."""
import json, os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
OUT = sys.argv[1]; D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='ngplus'); os.makedirs(D, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
G = 0x03001068; PLAYER = 0x03001C34; AT = 0x0300197C; REC0 = 0x03001560; BENCH = 0x0203F000
NG_BYTE = BENCH + 482 + (47 - 32) // 8          # bench flags2: more flags 32-63
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
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
flag = lambda n: mem(G + 0x55 + n // 8)[0] >> (n % 8) & 1
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, (mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8)
def talk(x, y):
    pl = mem(PLAYER)[0]
    send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80')
at = lambda: mem(AT)[0] & 0xFFFF
send('guardon 0x09000000', *start); mem(G)
send(flag_on(149)); send(flag_on(862)); send(flag_on(883)); mem(G)
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(open(os.environ['BFU_PROTO'], 'rb').read(), os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
pl = mem(PLAYER)[0]; x0, y0, x1, y1 = door['rect']
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run 110'); mem(G)
talk(96, 328); send('run 200'); mem(G)
send(flag_on(883)); talk(*zone26.HUB_AT); send('run 200', 'shot capsule'); mem(G)
check('the rig reaches Capsule Corporation', at() == (20 << 8 | 4))
exp0 = mem(REC0 + 0x24)[0]; send('poke %08X %08X' % (REC0 + 0x24, exp0 + 123456)); exp0 += 123456
lv_skills = mem(REC0 + 0x0C, 2)
talk(232, 248); send('run 120', 'shot bulma_offer', 'tap A 60', 'run 60', 'shot bulma_menu', 'tap A 60', 'run 120', 'shot bulma_sure', 'tap A 60')
for k in range(12):
    send('run 100', 'tap A 30')
    if k == 3: send('shot opening')
send('run 200', 'shot after'); mem(G)
check('the ending is undone (flag 149 clear)', flag(149) == 0)
check('the round is counted (more flag 47)', mem(NG_BYTE)[0] >> 7 & 1)
check("Goku keeps his experience", mem(REC0 + 0x24)[0] == exp0)
check('the opening plays: Snake Way with Goku in the party', at() == (1 << 8 | 1) and mem(REC0)[0] & 1 and mem(G)[0] & 255 == 0)
check('no bad jumps', not bad[0])
send('dump g 03001068 8a8'); mem(G)
g = open(D + '/g.bin', 'rb').read()
print('   Goku after: skills %s, form %d' % (list(g[0x4F8 + 0x0D:0x4F8 + 0x0D + g[0x4F8 + 0x0C]]), g[0x4F8 + 0x14]))
p.stdin.close(); p.wait()
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
