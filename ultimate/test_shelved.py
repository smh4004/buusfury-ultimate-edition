#!/usr/bin/env python3
"""The shelved Great Ape and a save from the Nov 9 build (build `--debug --zone` first; set BFU_PROTO):
  python3 ultimate/test_shelved.py [work dir] [rom]
A Nov 9 save can hold the Great Ape's forms (159-161) and skills (48, 49) and their book bits (Goku's 15, Vegeta's 10). Goku and GT Vegeta
are given all of that, then an area loads (Goku's figure is made from his form then: the shelved rows are copies of the GT looks) and the
party sync runs (outfit.c shelved_fix). Checks: no bad jumps, both back in their own looks, the skills out of their slots in order, the
selection on the same skill or the first, the stale book bits cleared, and the form table's shelved rows the GT looks' own figures."""
import json, os, struct, subprocess, sys, tempfile
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
W = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='shelved'); os.makedirs(W, exist_ok=True)
ROM = sys.argv[2] if len(sys.argv) > 2 else 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
G, REC, SIZE, AT = 0x03001068, 0x03001560, 0x68, 0x0300197C
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)

rom = open(ROM, 'rb').read()
for k, n in enumerate(('kid_goku', 'vegeta_gt', 'vegeta_gt_tank')):
    f, base = 159 + k, forms[n]
    row, own = rom[0x800000 + 24 * f:0x800000 + 24 * f + 24], rom[0x800000 + 24 * base:0x800000 + 24 * base + 24]
    check('form %d (the shelved Great Ape of %s) is that look\'s figure, owner and portraits' % (f, n), forms.get('shelved_ape_' + n) == f and row[0x0C:0x16] == own[0x0C:0x16])

P = open(os.environ['BFU_PROTO'], 'rb').read()
door = [x for x in zone26.links(json.load(open('ultimate/zone26.json')), {a: zone26.floor_mask(P, os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
x0, y0, x1, y1 = door['rect']
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
env = dict(os.environ); env.pop('HARNESS_SAV', None)
p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', W], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
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
def rec(c):
    return b''.join(w.to_bytes(4, 'little') for w in mem(REC + c * SIZE, SIZE // 4))
def poke(c, skills, sel, form, bit):
    R = REC + c * SIZE; known = struct.unpack_from('<H', rec(c), 0x22)[0] | 1 << bit
    send('poke8 %08X %02X' % (R + 0x0C, len(skills)), *['poke8 %08X %02X' % (R + 0x0D + i, s) for i, s in enumerate(skills)],
         *['poke8 %08X 01' % (R + 0x2E + 2 * i) for i in range(len(skills))], 'poke8 %08X %02X' % (R + 0x15, sel), 'poke8 %08X %02X' % (R + 0x14, form),
         'poke8 %08X %02X' % (R + 0x22, known & 255), 'poke8 %08X %02X' % (R + 0x23, known >> 8))

send('guardon 0x09000000', *start); mem(G)
send('poke8 %08X 00' % G)                                  # Goku in play
poke(0, [15, 48, 7, 49], 1, 159, 15)                       # Goku as the Great Ape, the Great Ape and the Chou Makouhou held, the Great Ape selected
poke(4, [7, 48, 20], 2, 160, 10)                           # GT Vegeta as the Great Ape, Super Saiyan selected
pl = mem(0x03001C34)[0]
send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8),
     'keys ' + 'DOWN UP LEFT RIGHT'.split()[door['key']], 'run 12', 'keys', 'run 200', 'shot shelved_arrive')    # an area loads with Goku in form 159
check('an area loads with a Nov 9 Great Ape form', mem(AT)[0] & 0xFFFF != 0 and not bad[0])
send('run 700', 'shot shelved_after')
g, v = rec(0), rec(4)
print('   Goku: form %d, skills %s, selected %d, book %04x; Vegeta: form %d, skills %s, selected %d, book %04x' % (
    g[0x14], list(g[0x0D:0x0D + g[0x0C]]), g[0x15], struct.unpack_from('<H', g, 0x22)[0], v[0x14], list(v[0x0D:0x0D + v[0x0C]]), v[0x15], struct.unpack_from('<H', v, 0x22)[0]))
check('Goku is back in GT Kid Goku\'s look', g[0x14] == forms['kid_goku'])
check('GT Vegeta is back in his own look', v[0x14] == forms['vegeta_gt'])
check('Goku keeps the Kamehameha and the ki blast, in order, without the Great Ape\'s two', list(g[0x0D:0x0D + g[0x0C]]) == [15, 7])
check('GT Vegeta keeps the ki blast and Super Saiyan, without the Great Ape', list(v[0x0D:0x0D + v[0x0C]]) == [7, 20])
check('Goku\'s selection moved off the Great Ape to his first slot', g[0x15] == 0)
check('GT Vegeta\'s selection stays on Super Saiyan, now his second slot', v[0x15] == 1)
check('the Great Ape\'s book bits are cleared (Goku 15, Vegeta 10)', not struct.unpack_from('<H', g, 0x22)[0] >> 15 & 1 and not struct.unpack_from('<H', v, 0x22)[0] >> 10 & 1)
check('no bad jumps', not bad[0])
p.stdin.close(); p.wait(timeout=60)
if fails: sys.exit('FAILED: %s' % fails)
print('all passed; screens in', W)
