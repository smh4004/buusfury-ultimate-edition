#!/usr/bin/env python3
"""Android 13 into Super 13 and Android 17 into Super 17, on the guest slot. Build `--debug` first.
  python3 ultimate/test_transform.py [rom] [work dir]
The skill changes form, the screen flashes white and comes back, attacks work and the form goes back; lays out what it looks like."""
import json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')); import guestnav     # the guest slot's keys (Nov 12)
from PIL import Image
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='tf'); os.makedirs(D, exist_ok=True)
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
H = 'tools/harness/harness'; G = 0x03001068; R = 0x03001560 + 8 * 0x68
route = open('tools/harness/long.txt').read().split('\n')[:93]
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
for who, downs, base, sup, skill in (('13', 2, 'android13', 'super13', 30), ('17', 5, 'android17', 'super17', 31)):
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
            if 'bad pc' in l or 'guard' in l.lower() and 'reject' in l.lower(): bad[0] = True
            if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
    form = lambda: mem(R + 0x14)[0] & 0xFF
    send('guardon 0x09000000', *route); send('tap A 60', 'tap A 60', 'run 30', *['tap RIGHT 40'] * 5, *guestnav.keys(base), 'tap A 200', 'run 60')
    check('%s: picked as the base form' % who, form() == forms[base])
    rec = mem(R, 26); skills = [(rec[3] >> 8 * i) & 255 for i in (1, 2, 3)] + [rec[4] & 255, rec[4] >> 8 & 255]
    check('%s: the skill is on the list' % who, skill in skills)
    send('poke8 %08X %02X' % (R + 0x15, skills.index(skill)), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D))
    send('keys DOWN', 'run 4', 'keys', 'run 2', 'keys B', 'run 4', 'keys')
    W = Image.new('RGB', (6 * 240, 7 * 160)); changed = None; bright = []
    for i in range(42):
        send('run 5', 'shot t%s_%d' % (who, i)); fm = form(); 
        im = Image.open('%s/t%s_%d.png' % (D, who, i)).convert('RGB'); W.paste(im, (i % 6 * 240, i // 6 * 160))
        if im.convert('L').getextrema()[0] > 200: bright.append(i)
        if changed is None and fm == forms[sup]: changed = i
    W.save('%s/transform_%s.png' % (D, who))
    print('  changed at', changed, 'white frames', bright)
    check('%s: becomes the super form' % who, changed is not None and form() == forms[sup])
    check('%s: the screen flashes white' % who, sum(bright) > 0)
    send('run 60', 'shot after' + who); mem(G)
    check('%s: and comes back' % who, Image.open('%s/after%s.png' % (D, who)).convert('L').getextrema()[0] < 100)
    # Walking and each attack in the new form
    S = Image.new('RGB', (6 * 240, 3 * 160)); n = 0
    def snap(tag):
        global n
        send('shot s%s_%d' % (who, n)); mem(G); S.paste(Image.open('%s/s%s_%d.png' % (D, who, n)).convert('RGB'), (n % 6 * 240, n // 6 * 160)); n += 1
    for key in ('DOWN', 'LEFT', 'RIGHT', 'UP'):
        send('keys ' + key, 'run 16'); snap(key); send('keys', 'run 4'); snap(key)
    send('poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 03' % (R + 0x1F))
    send('poke8 %08X 00' % (R + 0x15), 'keys LEFT', 'run 4', 'keys', 'run 2', 'keys B', 'run 10', 'keys'); snap('blast'); send('run 40')
    send('poke8 %08X 03' % (R + 0x15), 'keys B', 'run 40'); snap('wave'); send('run 30', 'keys', 'run 40'); snap('wave2')
    send('run 120', 'poke8 %08X %02X' % (R + 0x15, skills.index(skill)), 'run 2', 'keys B', 'run 4', 'keys', 'run 60'); snap('back')
    for _ in range(3):
        pl_ = mem(0x03001C34)[0]; act = mem(pl_ + 0x50, 3)[2] if 0 else mem(pl_ + 0x58)[0]; rec_ = mem(act + 0x54, 24)
        print('   later', hex(form()), hex(mem(pl_ + 0x14)[0]), 'slot', rec_.index(mem(pl_ + 0x50)[0]) if mem(pl_ + 0x50)[0] in rec_ else None, 'frame', hex(mem(pl_ + 0x10)[0])); send('run 80')
    snap('back2')
    print('  back', hex(form()), 'skills', mem(R + 0x0C, 2))
    S.save('%s/moves_%s.png' % (D, who))
    check('%s: the skill changes back' % who, form() == forms[base])
    check('%s: no bad jumps' % who, not bad[0]); p.stdin.close()
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', D)
