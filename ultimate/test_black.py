#!/usr/bin/env python3
"""Goku Black and Super Saiyan Rose on the guest slot. Build `--debug` first (it opens every outfit).
  python3 ultimate/test_black.py [rom] [work dir]
Picks him, walks, uses each move, becomes Rose and back; lays the screens out in sheets to look at."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')); import guestnav     # the guest slot's keys (Nov 12)
from PIL import Image
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='black'); os.makedirs(D, exist_ok=True)
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
ROSE_SKILL, BLACK_KAME_SKILL = 32, 33          # build.py's (importing it runs the build)
H = 'tools/harness/harness'; G = 0x03001068; R = 0x03001560 + 8 * 0x68
GUESTS = [o['form'] for o in json.load(open('ultimate/outfits.json'))['characters']['8']]
route = open('tools/harness/long.txt').read().split('\n')[:93]
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
env = dict(os.environ); env.pop('HARNESS_SAV', None)
p = subprocess.Popen([H, ROM, '/dev/stdin', D], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
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
form = lambda: mem(R + 0x14)[0] & 0xFF
sheets = {}
def snap(sheet, tag):
    k = len(sheets.setdefault(sheet, []))
    send('shot %s_%d' % (sheet, k)); mem(G); sheets[sheet].append(tag)
def save_sheets():
    for name, tags in sheets.items():
        W = Image.new('RGB', (6 * 240, (len(tags) + 5) // 6 * 160))
        for k in range(len(tags)): W.paste(Image.open('%s/%s_%d.png' % (D, name, k)).convert('RGB'), (k % 6 * 240, k // 6 * 160))
        W.save('%s/%s.png' % (D, name))
def use(skill, hold=10, then=40, tag=None, sheet='moves', shots=1, gap=12, tap=False):
    rec = mem(R, 26); skills = [(rec[3] >> 8 * i) & 255 for i in (1, 2, 3)] + [rec[4] & 255, rec[4] >> 8 & 255]
    send('poke8 %08X %02X' % (R + 0x15, skills.index(skill)), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D), 'run 2', 'keys B', 'run %d' % hold)
    if tap: send('keys')                         # a blast flies when B is let go
    for i in range(shots): snap(sheet, '%s %d' % (tag or skill, i)); send('run %d' % gap)
    send('keys', 'run %d' % then)
send('guardon 0x09000000', *route); send('tap A 60', 'tap A 60', 'run 30', *['tap RIGHT 40'] * 5, *guestnav.keys('goku_black'), 'run 30'); snap('picker', 'black'); send('tap UP 40', 'run 30'); snap('picker', 'hercule'); send('tap DOWN 40', 'run 30', 'tap A 200', 'run 60')
check('picked Goku Black', form() == forms['goku_black'])
rec = mem(R, 26); skills = [(rec[3] >> 8 * i) & 255 for i in (1, 2, 3)] + [rec[4] & 255, rec[4] >> 8 & 255]
check('his moves: blast, Instant Transmission, Black Kamehameha, Rose', skills[:4] == [7, 14, BLACK_KAME_SKILL, ROSE_SKILL] and rec[3] & 255 == 4)
for key in ('DOWN', 'LEFT', 'RIGHT', 'UP'):
    send('keys ' + key, 'run 16'); snap('walk', key); send('keys', 'run 4'); snap('walk', key)
send('keys LEFT', 'run 4', 'keys', 'run 2')
use(7, 10, 40, 'blast', shots=8, gap=3, tap=True)
use(BLACK_KAME_SKILL, 30, 60, 'kame', shots=4, gap=15)
send('tap A 8', 'run 4'); snap('moves', 'punch'); send('run 30')
print('aura mode', mem(0x03002BB0)[0] & 255)
use(ROSE_SKILL, 4, 0, 'rose', sheet='rose', shots=12, gap=10)
send('run 60')
check('becomes Rose', form() == forms['goku_rose'])
for key in ('DOWN', 'LEFT', 'RIGHT', 'UP'):
    send('keys ' + key, 'run 16'); snap('walk', 'rose ' + key); send('keys', 'run 4'); snap('walk', 'rose ' + key)
send('keys LEFT', 'run 4', 'keys', 'run 2')
use(7, 10, 40, 'rose blast', sheet='rose_moves', shots=6, gap=3, tap=True)
use(BLACK_KAME_SKILL, 30, 60, 'rose kame', sheet='rose_moves', shots=4, gap=15)
use(ROSE_SKILL, 4, 0, 'back', sheet='back', shots=10, gap=10)
send('run 120')
check('changes back to Black', form() == forms['goku_black'])
use(14, 40, 120, 'instant transmission', sheet='it', shots=3, gap=20)
check('still Black after Instant Transmission', form() == forms['goku_black'])
send('tap SELECT 90', 'run 30'); snap('menu', 'select')
for k in range(4): send('tap R 60', 'run 30'); snap('menu', 'R%d' % k)
send('tap SELECT 60', 'run 60')
check('no bad jumps', not bad[0])
p.stdin.close(); save_sheets()
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', D)
