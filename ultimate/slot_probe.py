"""slot_probe.py ROM OUTDIR FORM WHAT: which animation slot each control or skill plays, watched in the game (a --debug build; run from
the repo root). The field player's current animation pointer (object 0x0202D328 +0x50, at 0x0202D378) is read every 2 frames and
matched to the slots of the figure FORM names. WHAT: basic (the buttons), more (long idle, long walks, an enemy), dash, run, enemy,
fly, or skill ids "13,23" (each poked as the only skill, B held then let go). Nov 13: what plays Gotenks's slots (adult_gotenks.SLOTS)."""
import json, struct, subprocess, sys
ROM, OUTD, FORM = sys.argv[1], sys.argv[2], int(sys.argv[3])
rom = open(ROM, 'rb').read(); u = lambda o: struct.unpack_from('<I', rom, o)[0]
actor = struct.unpack_from('<H', rom, 0x800000 + 24 * FORM + 0xE)[0] - 9
rec = u(0x850000 + 4 * actor) - 0x08000000; n = u(rec) & 0xFF
anims = {}
for s in range(n):
    p = u(rec + 0x54 + 4 * s)
    if p: anims.setdefault(p, []).append(s)
POS = {0: 0, 1: 1, 3: 2, 4: 3, 6: 4, 8: 5, 7: 5}
ROUTE = [l for l in open('tools/harness/long.txt').read().split('\n')[:93] if not l.startswith('shot ')]
owner = rom[0x800000 + 24 * FORM + 0x0C]; c = owner if owner in POS else 8; R = 0x03001560 + c * 0x68
FULL = ['poke8 %08X FF' % (R + k) for k in (0x1A, 0x1C, 0x1E, 0x20)] + ['poke8 %08X 03' % (R + k) for k in (0x1B, 0x1D, 0x1F, 0x21)]
L = ['guardon 0x09000000'] + ROUTE + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * POS[c] + ['poke8 %08X %02X' % (R + 0x14, FORM), 'run 4', 'tap A 200', 'run 60', 'mem %08X 8' % (R + 0x0C), 'mark own']
def watch(k): return ['run 2', 'mem 0202D378 1'] * k
tests = []
def T(name, steps):
    tests.append(name); L.extend(['mark ' + name] + steps + ['run 90'] + FULL)
BASIC = sys.argv[4] == 'basic'
if BASIC: T('idle', watch(20))
if BASIC: T('walk (hold LEFT)', ['keys LEFT'] + watch(30) + ['keys'])
if BASIC: T('tap A once', ['keys A', 'run 2', 'keys'] + watch(30))
if BASIC: T('tap A x4 (combo)', sum([['keys A', 'run 3', 'keys', 'run 6'] + watch(2) for _ in range(6)], []) + watch(20))
if BASIC: T('hold A 80 then let go', ['keys A'] + watch(40) + ['keys'] + watch(30))
if BASIC: T('tap B', ['keys B', 'run 2', 'keys'] + watch(30))
if BASIC: T('hold B 80 then let go', ['keys B'] + watch(40) + ['keys'] + watch(40))
if BASIC: T('tap R', ['keys R', 'run 2', 'keys'] + watch(30))
if BASIC: T('hold R', ['keys R'] + watch(30) + ['keys'] + watch(10))
if BASIC: T('tap L', ['keys L', 'run 2', 'keys'] + watch(30))
if BASIC: T('hold L', ['keys L'] + watch(30) + ['keys'] + watch(10))
if BASIC: T('LEFT+R (dash?)', ['keys LEFT,R'] + watch(30) + ['keys'] + watch(10))
if BASIC: T('LEFT+B', ['keys LEFT,B'] + watch(30) + ['keys'] + watch(10))
if BASIC: T('A+B', ['keys A,B'] + watch(30) + ['keys'] + watch(20))
if sys.argv[4] == 'fly':
    use = ['poke8 %08X 01' % (R + 0x0C), 'poke8 %08X 0C' % (R + 0x0D), 'poke8 %08X 00' % (R + 0x15)] + FULL
    for d in ('LEFT', 'RIGHT', 'UP', 'DOWN', 'UP,LEFT', 'DOWN,RIGHT'):
        T('fly then hold ' + d, use + ['tap B 20', 'keys ' + d] + watch(40) + ['keys'] + watch(20) + ['tap B 20'] + watch(20))
    T('fly, hold A', use + ['tap B 20', 'keys A'] + watch(30) + ['keys'] + watch(20))
    T('fly, tap R', use + ['tap B 20', 'keys R'] + watch(30) + ['keys'] + watch(20))
if sys.argv[4] == 'enemy':
    T('walk at the enemies (down-left) and stand', ['keys DOWN,LEFT'] + watch(60) + ['keys'] + watch(200))
    T('stand by them, attacked', watch(300))
    T('ghost attack near them', ['poke8 %08X 01' % (R + 0x0C), 'poke8 %08X 0D' % (R + 0x0D), 'poke8 %08X 00' % (R + 0x15)] + FULL + ['keys LEFT', 'run 2', 'keys', 'keys B'] + watch(22) + ['keys'] + watch(250))
if sys.argv[4] == 'more':
    T('stand still 900 frames, nothing pressed', watch(450))
    T('hold LEFT 300 frames', ['keys LEFT'] + watch(150) + ['keys'] + watch(10))
    T('hold UP 300 frames', ['keys UP'] + watch(150) + ['keys'] + watch(10))
    T('walk into the brown enemy (down-left) and stay', ['keys DOWN,LEFT'] + watch(70) + ['keys DOWN'] + watch(30) + ['keys RIGHT'] + watch(30) + ['keys'] + watch(600))
if sys.argv[4] == 'run':
    T('L+LEFT', ['keys L,LEFT'] + watch(60) + ['keys'] + watch(10))
    T('double-tap LEFT, hold', ['keys LEFT', 'run 3', 'keys', 'run 3', 'keys LEFT'] + watch(60) + ['keys'] + watch(10))
    T('B+LEFT held long', ['keys B,LEFT'] + watch(80) + ['keys'] + watch(20))
    T('A+LEFT', ['keys A,LEFT'] + watch(40) + ['keys'] + watch(20))
    T('SELECT', ['keys SELECT', 'run 3', 'keys'] + watch(40))
    T('L+R', ['keys L,R'] + watch(40) + ['keys'] + watch(20))
    T('L+A', ['keys L,A'] + watch(40) + ['keys'] + watch(20))
    T('L+B', ['keys L,B'] + watch(40) + ['keys'] + watch(20))
    T('R+A', ['keys R,A'] + watch(40) + ['keys'] + watch(20))
    T('R+B', ['keys R,B'] + watch(40) + ['keys'] + watch(20))
if sys.argv[4] == 'dash':
    for d in ('RIGHT', 'UP', 'DOWN'):
        T('double-tap %s, hold' % d, ['keys ' + d, 'run 3', 'keys', 'run 3', 'keys ' + d] + watch(60) + ['keys'] + watch(30))
        T('double-tap %s, let go' % d, ['keys ' + d, 'run 3', 'keys', 'run 3', 'keys ' + d, 'run 3', 'keys'] + watch(60))
if sys.argv[4] == 'change':
    sel = lambda sk: ['poke8 %08X 01' % (R + 0x0C), 'poke8 %08X %02X' % (R + 0x0D, sk), 'poke8 %08X 00' % (R + 0x15)]
    T('Super Saiyan (skill 20), pressed', sel(20) + FULL + ['keys B', 'run 2', 'keys'] + watch(120))
    T('pressed again', ['keys B', 'run 2', 'keys'] + watch(120))
    T('Super Saiyan again, then his energy emptied', sel(20) + FULL + ['keys B', 'run 2', 'keys'] + watch(60) + ['poke8 %08X 00' % (R + 0x1A), 'poke8 %08X 00' % (R + 0x1B)] + watch(300))
for sk in ([] if BASIC or sys.argv[4] in ('fly', 'enemy', 'more', 'run', 'dash', 'change') else [int(x) for x in sys.argv[4].split(',')]):
    T('skill %d (B held, let go)' % sk, ['poke8 %08X 01' % (R + 0x0C), 'poke8 %08X %02X' % (R + 0x0D, sk), 'poke8 %08X 00' % (R + 0x15)] + FULL +
      ['keys LEFT', 'run 2', 'keys', 'run 10', 'keys B'] + watch(22) + ['keys'] + watch(60))
import os; os.makedirs(OUTD, exist_ok=True); open(OUTD + '/p.txt', 'w').write('\n'.join(l for l in L if not l.startswith('mark ')) + '\n')
# run, then split the mem lines by test (each test's lines counted)
o = subprocess.run(['tools/harness/harness', ROM, OUTD + '/p.txt', OUTD], capture_output=True, text=True, timeout=3000).stdout
lines = [l for l in o.split('\n') if l.startswith('mem ')]
own = lines[0]; vals = [int(l.split(':')[1].split()[0], 16) for l in lines[1:]]
print('own skills (record +0C):', own, 'bad pc' in o)
counts = []
for l in L:
    if l.startswith('mark '): counts.append([l[5:], 0])
    elif l == 'mem 0202D378 1' and counts: counts[-1][1] += 1
i = 0; res = {}
for name, k in counts[1:]:
    seq = []
    for v in vals[i:i + k]:
        s = anims.get(v, ['?%08X' % v])
        tag = '/'.join(map(str, s))
        if not seq or seq[-1][0] != tag: seq.append([tag, 1])
        else: seq[-1][1] += 1
    i += k; res[name] = seq
    print('%-28s %s' % (name, '  '.join('%s(x%d)' % (t, n) for t, n in seq)))
json.dump({'res': res, 'bad': 'bad pc' in o}, open(OUTD + '/res_%d.json' % FORM, 'w'))
