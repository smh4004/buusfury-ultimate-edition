#!/usr/bin/env python3
"""GT: every look on the Switch Character screen and every transformation, with its moves. Build `--debug` first (it opens every outfit).
  python3 ultimate/test_gt.py [rom] [work dir]
One emulator per case, in parallel: open Switch Character at the end of the debug intro, cycle to the look, confirm, then walk, fire each
move and go through the transformation chain, checking the form after each step. Sheets of what it looks like go in the work dir."""
import json, os, subprocess, sys, tempfile, threading
from PIL import Image
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='gt'); os.makedirs(D, exist_ok=True)
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
SETTLE = int(os.environ.get('GT_SETTLE', 240))
MAJUUB = 34                                     # build.py's MAJUUB_SKILL (importing it runs the build)
H = 'tools/harness/harness'; G = 0x03001068; RECS = 0x03001560; RS = 0x68
OUTFITS = json.load(open('ultimate/outfits.json'))['characters']
route = open('tools/harness/long.txt').read().split('\n')[:93]
F = lambda v: v if isinstance(v, int) else forms[v]
fails = []; lock = threading.Lock()
def check(case, name, ok):
    with lock:
        print('PASS' if ok else 'FAIL', case + ':', name, flush=True)
        if not ok: fails.append(case + ': ' + name)


class Rig:
    def __init__(self, name):
        self.name = name; self.bad = False; self.shots = []
        env = dict(os.environ); env.pop('HARNESS_SAV', None)
        self.p = subprocess.Popen([H, ROM, '/dev/stdin', D], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
    def send(self, *ls):
        for l in ls: self.p.stdin.write(l + '\n')
        self.p.stdin.flush()
    def mem(self, a, n=1):
        self.send('mem %08X %d' % (a, n))
        while True:
            l = self.p.stdout.readline()
            if not l: raise SystemExit('harness ended')
            if 'bad pc' in l: self.bad = True
            if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
    def forms(self): return [self.mem(RECS + c * RS + 0x14)[0] & 255 for c in range(9)]
    def snap(self, tag):
        f = '%s_%d' % (self.name, len(self.shots)); self.send('shot ' + f); self.mem(G); self.shots.append((f, tag))
    def sheet(self):
        n = len(self.shots); W = Image.new('RGB', (6 * 240, (n + 5) // 6 * 160))
        for k, (f, _) in enumerate(self.shots): W.paste(Image.open('%s/%s.png' % (D, f)).convert('RGB'), (k % 6 * 240, k // 6 * 160))
        W.save('%s/%s.png' % (D, self.name))
    def close(self): self.p.stdin.close(); self.p.wait()


def picker_order():
    """Picker position of each character at the end of the debug intro: one Down on each, see whose form moves, then cancel."""
    r = Rig('order'); r.send('guardon 0x09000000', *route); r.send('tap A 60', 'tap A 60', 'run 30'); r.mem(G)
    pos = {}
    for k in range(9):
        before = r.forms(); r.send('tap DOWN 40', 'run 10'); after = r.forms()
        moved = [c for c in range(9) if before[c] != after[c]]
        if moved: pos[moved[0]] = k; r.send('tap UP 40', 'run 10')
        r.send('tap RIGHT 40', 'run 10')
    r.close()
    return pos


def outfit_steps(c, start, want):
    """Down presses from the look `start` to the look `want` on character c's list (every look is open in a debug build)."""
    lst = OUTFITS[str(c)]
    idx = lambda f: next(i for i, o in enumerate(lst) if F(o['form']) == f or F(o.get('also', 255)) == f)
    return (idx(F(want)) - idx(start)) % len(lst)


def case(name, c, look, skills, steps, pos, poke_form=None):
    """steps: (skill, the form it should leave, tag). skills: the record's skill list for the test (all learned)."""
    if c not in pos:                                     # not in this party (Gogeta): the form, worn by whoever is first on the picker
        poke_form = poke_form or look; c = min(pos, key=pos.get)
    r = Rig(name); R = RECS + c * RS
    r.send('guardon 0x09000000', *route); r.send('tap A 60', 'tap A 60', 'run 30'); r.mem(G)
    if poke_form is not None:
        r.send(*['tap RIGHT 40'] * pos[c]); r.send('poke8 %08X %02X' % (R + 0x14, F(poke_form)), 'run 4'); r.snap('picker'); r.send('tap A 200', 'run 60')
    else:
        r.send(*['tap RIGHT 40'] * pos[c]); cur = r.forms()[c]
        r.send(*['tap DOWN 40'] * outfit_steps(c, cur, look), 'run 20'); r.snap('picker'); r.send('tap A 200', 'run 60')
    check(name, 'wearing it', r.forms()[c] == F(poke_form if poke_form is not None else look) and r.mem(G)[0] & 255 == c)
    if c != 8: r.send('poke8 %08X %02X' % (R + 0x0C, len(skills)), *['poke8 %08X %02X' % (R + 0x0D + i, s) for i, s in enumerate(skills)])
    rec = r.mem(R, 26); have = [(rec[3] >> 8 * i) & 255 for i in (1, 2, 3)] + [rec[4] & 255, rec[4] >> 8 & 255]
    check(name, 'moves %s' % skills, have[:len(skills)] == skills and rec[3] & 255 == len(skills))
    def walk(tag):
        for key in ('DOWN', 'LEFT', 'RIGHT', 'UP'):
            r.send('keys ' + key, 'run 16'); r.snap('%s %s' % (tag, key)); r.send('keys', 'run 4')
    def use(skill, hold=10, then=60, shots=2, gap=12, tap=False):
        rec = r.mem(R, 26); have = [(rec[3] >> 8 * i) & 255 for i in (1, 2, 3)] + [rec[4] & 255, rec[4] >> 8 & 255]
        r.send('poke8 %08X %02X' % (R + 0x15, have.index(skill)), 'poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D), 'run 2', 'keys B', 'run %d' % hold)
        if tap: r.send('keys')
        for i in range(shots): r.snap('%d' % skill); r.send('run %d' % gap)
        r.send('keys', 'run %d' % then)
    walk('stand')
    r.send('keys LEFT', 'run 4', 'keys', 'run 2', 'tap A 8', 'run 4'); r.snap('punch'); r.send('run 30')
    for s in skills:
        if s in (7, 8, 15, 16, 17): use(s, 30 if s == 15 else 10, 60, shots=3, gap=10, tap=s == 7)
    for skill, want, tag in steps:
        use(skill, 4, 0, shots=6, gap=10)
        for _ in range(20):                          # a transformation takes a few seconds (Majuub's longer), and so does changing back
            if r.forms()[c] == F(want): break
            r.send('run 30')
        check(name, '%s -> %s' % (tag, want), r.forms()[c] == F(want))
        r.send('run %d' % (SETTLE * 5 if F(want) == F(look) else SETTLE))   # after changing back the game won't transform again for a while (retail Goku the same)
        if want != look: walk(tag)
        for s in skills:
            if s == 15 and want != look: use(15, 30, 60, shots=2, gap=15)
    r.send('run 30'); check(name, 'no bad jumps', not r.bad)
    r.close(); r.sheet()


pos = picker_order()
print('picker positions', pos, flush=True)
CASES = [
    ('goku', 0, 2, [7, 15, 20, 22], [(20, 4, 'SS'), (20, 'goku_ss2_b', 'SS2'), (20, 2, 'SS2 off'), (20, 4, 'SS again'), (20, 'goku_ss2_b', 'SS2'), (22, 6, 'SS3'), (22, 2, 'SS3 off')]),     # retail Goku (form 2: dead, with his halo), the same presses
    ('kid_goku', 0, 'kid_goku', [7, 15, 20, 22], [(20, 'kid_goku_ssj', 'SS'), (20, 'kid_goku', 'SS off'), (20, 'kid_goku_ssj', 'SS'), (22, 'kid_goku_ssj3', 'SS3'),
                                                  (22, 'kid_goku_ssj4', 'SS4'), (22, 'kid_goku', 'SS4 off')]),
    ('gohan_gt', 1, 'gohan_gt', [7, 17, 20], [(20, 'gohan_gt_ssj', 'SS'), (20, 'gohan_gt', 'SS off')]),
    ('gohan_gt_ng', 1, 'gohan_gt_noglasses', [7, 17, 20], [(20, 'gohan_gt_ng_ssj', 'SS'), (20, 'gohan_gt_noglasses', 'SS off')]),
    ('goten_gt', 2, 'goten_gt', [7, 16, 20], [(20, 'goten_gt_ssj', 'SS'), (20, 'goten_gt', 'SS off')]),
    ('goten_gt_green', 2, 'goten_gt_green', [7, 16, 20], [(20, 'goten_gt_green_ssj', 'SS'), (20, 'goten_gt_green', 'SS off')]),
    ('trunks_gt', 3, 'trunks_gt', [7, 20], [(20, 'trunks_gt_ssj', 'SS'), (20, 'trunks_gt', 'SS off')]),
    ('vegeta_gt', 4, 'vegeta_gt', [7, 20], [(20, 'vegeta_gt_ssj', 'SS'), (20, 'vegeta_gt_ssj4', 'SS4'), (20, 'vegeta_gt', 'SS4 off')]),
    ('vegeta_gt_tank', 4, 'vegeta_gt_tank', [7, 20], [(20, 'vegeta_gt_tank_ssj', 'SS'), (20, 'vegeta_gt_tank_ssj4', 'SS4'), (20, 'vegeta_gt_tank', 'SS4 off')]),
    ('vegeta_gt_mustache', 4, 'vegeta_gt_mustache', [7, 20], [(20, 'vegeta_gt_mustache', 'no Super Saiyan')]),
    ('pan', 8, 'pan', [7, 8, 20], [(20, 'pan_ssj', 'SS'), (20, 'pan', 'SS off')]),
    ('pan_nobandana', 8, 'pan_nobandana', [7, 8, 20], [(20, 'pan_ssj_spiky', 'SS'), (20, 'pan_nobandana', 'SS off')]),
    ('pan_gi_tan', 8, 'pan_gi_tan', [7, 8], []), ('pan_gi_red', 8, 'pan_gi_red', [7, 8], []),
    ('pan_bug', 8, 'pan_bug', [7, 8], []), ('pan_brapan', 8, 'pan_brapan', [7, 8], []),
    ('uub', 8, 'uub', [7, 8, 15, MAJUUB], [(MAJUUB, 'majuub', 'Majuub'), (MAJUUB, 'uub', 'Majuub off')]),
]
EXTRA = [('gogeta_ssj4', 0, None, [7, 15], [], 'gogeta_ssj4')]
only = os.environ.get('GT_ONLY')
jobs = [threading.Thread(target=case, args=(n, c, l, s, st, pos)) for n, c, l, s, st in CASES if not only or n in only.split(',')]
jobs += [threading.Thread(target=case, args=(n, c, l, s, st, pos, pf)) for n, c, l, s, st, pf in EXTRA if not only or n in only.split(',')]
for k in range(0, len(jobs), 6):                     # six emulators at a time
    for j in jobs[k:k + 6]: j.start()
    for j in jobs[k:k + 6]: j.join()
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', D)
