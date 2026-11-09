#!/usr/bin/env python3
"""Beam clashes against Kid Buu, the game's beam user. Needs a zone debug build made with BFU_CLASH_TEST=1, where the first Trial is Kid Buu:
  BFU_CLASH_TEST=1 BFU_OUT=<dir> python3 ultimate/build.py --debug --zone
  python3 ultimate/test_clash.py <dir> [work dir]
Drives the emulator live, so it can react to where he is. Exits non-zero on failure.
For a guest in that Trial, build with BFU_CLASH_SLOT=8 too and set CLASH_FORM to the form's number and CLASH_SKILL to a beam skill."""
import json, os, struct, subprocess, sys, tempfile
H = 'tools/harness/harness'
OUT = sys.argv[1]; d = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='clash'); os.makedirs(d, exist_ok=True)
ROM = OUT + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
G = 0x03001068; REC0 = 0x03001560; CL = 0x0203F200; PLAYER = 0x03001C34; ENEMIES = 0x03001BB4; PL = 0x0202E8E4
SKILL = int(os.environ.get('CLASH_SKILL', '15'))
FORM = int(os.environ.get('CLASH_FORM', '0'))      # a guest's form number: that fighter takes the beam instead of Goku, on the guest slot
if FORM: REC0 += 8 * 0x68
fails = []
def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    if not ok: fails.append(name)
P = open(os.environ['BFU_PROTO'], 'rb').read(); cfg = json.load(open('ultimate/zone26.json'))
door = [x for x in zone26.links(cfg, {a: zone26.floor_mask(P, os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
x0, y0, x1, y1 = door['rect']; KEYS = 'DOWN UP LEFT RIGHT'.split()
flag_on = lambda n: 'poke8 %08X %02X' % (G + 0x55 + n // 8, 1 << n % 8)
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
start += ['poke %08X %08X' % (PL + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (PL + 0x1A4, ((y0 + y1) // 2) << 8), 'keys ' + KEYS[door['key']], 'run 12', 'keys', 'run 110']
strong = ['poke8 %08X %s' % (REC0 + o, v) for o, v in ((0x28, '96'), (0x29, '96'), (0x2A, '96'), (0x2B, '96'), (0x16, 'FF'), (0x17, '7F'))]

class Game:
    def __init__(self):
        self.p = subprocess.Popen([H, ROM, '/dev/stdin', d], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.bad = False
    def send(self, *lines):
        for l in lines: self.p.stdin.write(l + '\n')
        self.p.stdin.flush()
    def mem(self, addr, n=1):
        self.send('mem %08X %d' % (addr, n))
        while True:
            l = self.p.stdout.readline()
            if not l: raise SystemExit('harness ended')
            if 'bad pc' in l: self.bad = True
            if l.startswith('mem %08x' % addr): return [int(x, 16) for x in l.split(':')[1].split()]
    def sync(self): self.mem(G)
    def talk(self, x, y):
        pl = self.mem(PLAYER)[0]
        self.send('poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80')
    def close(self):
        self.p.stdin.close(); self.p.wait(timeout=30)

def into_fight():
    g = Game()
    g.send('guardon 0x09000000', *start, flag_on(862), flag_on(883), *strong); g.sync()
    g.talk(96, 328); g.send('run 200'); g.sync()
    if FORM: g.send('poke8 %08X 01' % REC0, 'poke8 %08X %02X' % (REC0 + 0x14, FORM), 'poke8 %08X FF' % (REC0 + 0x18), 'poke8 %08X 03' % (REC0 + 0x19), 'poke8 %08X FF' % (REC0 + 0x1E), 'poke8 %08X 03' % (REC0 + 0x1F)); g.sync()
    g.talk(*zone26.HUB_AT)
    g.send('run 150', 'tap A 150', 'tap DOWN 12', 'tap DOWN 12', 'tap A 150', 'run 150', 'tap A 150', 'tap A 200', 'run 120', 'shot clash_room'); g.sync()
    g.send('poke8 %08X 01' % (REC0 + 0x0C), 'poke8 %08X %02X' % (REC0 + 0x0D, SKILL), 'poke8 %08X 00' % (REC0 + 0x15), *strong); g.sync()
    return g

def clash(g, mash, tag):
    """Wait for Kid Buu to fire, answer him, and return what happened. Where his beam starts beside him varies from shot to shot (0-32 px
    across), so a shot whose beam doesn't come down in line with Goku's (outfit.c clash_begin: within 16 px) passes it by, as in play;
    then the next one."""
    for shot in range(6):
        for cycle in range(400):
            pl, n = g.mem(PLAYER)[0], g.mem(0x03001BB0)[0]
            if not n: return None
            foe = g.mem(ENEMIES)[0]
            fx, fy = g.mem(foe + 0x1A0, 2)
            g.send('poke %08X %08X' % (pl + 0x1A0, fx), 'poke %08X %08X' % (pl + 0x1A4, fy + (90 << 8)), 'poke8 %08X 01' % (pl + 0x10), 'poke8 %08X FF' % (REC0 + 0x16), 'poke8 %08X 7F' % (REC0 + 0x17), 'poke8 %08X 64' % (REC0 + 0x1A), 'poke8 %08X 00' % (REC0 + 0x1B), 'bp 08033002 8')
            while True:
                l = g.p.stdout.readline()
                if 'bad pc' in l: g.bad = True
                if l.startswith('bp 08033002'): break
            if ' hit' in l and 'not hit' not in l: break
        else:
            return None
        print('   he fired after', cycle, 'tries', flush=True)
        g.send('keys B', 'run 8')
        began = False
        for k in range(120):
            g.send('run 2')
            if g.mem(CL + 0x18)[0]: began = True; break
        if began: break
        print('   his beam passed Goku\'s by (not in line): the next shot', flush=True)
        g.send('keys', 'run 120')
    else:
        return dict(began=False)
    g.send('shot %s_start' % tag)
    rec0 = g.mem(REC0 + 0x18)[0]
    foe = g.mem(CL + 4)[0]; foe = g.mem(foe + 0x50)[0]
    hp0 = g.mem(foe + 0x28C)[0]
    frames = 0; pushes = []; tips = []; energy = []
    line = lambda b: g.mem(b + 0x20, 2)
    aligned = (lambda a, b: a[0] == b[0] or a[1] == b[1])(line(g.mem(CL)[0]), line(g.mem(CL + 4)[0]))
    g.send('keys')
    while frames < 1500:
        if mash: g.send('keys A', 'run 2', 'keys', 'run 4'); frames += 6
        else: g.send('run 6'); frames += 6
        act, push = g.mem(CL + 0x18, 2)
        push = push - (1 << 32) if push >> 31 else push
        pushes.append(push)
        beam_p, beam_e = g.mem(CL, 2)
        if act: energy.append(g.mem(REC0 + 0x18)[0] >> 16)
        if frames == 120 or (mash and frames == 60): g.send('shot %s_mid' % tag)
        if not act: break
    hp1 = g.mem(foe + 0x28C)[0]
    g.send('run 30'); surge = g.mem(beam_p + 0x10)[0] & 255; hp2 = g.mem(foe + 0x28C)[0]
    g.send('run 30', 'shot %s_after' % tag, 'run 200'); g.sync()
    return dict(began=True, frames=frames, pushes=pushes, hp0=hp0, hp1=hp1, hp2=hp2, surge=surge, energy=energy, aligned=aligned, foe=foe)

g = into_fight(); res = clash(g, True, 'win')
check('the two beams clash', bool(res) and res['began'])
if res and res['began']:
    print('   clash lasted', res['frames'], 'frames; pushes', res['pushes'][:3], '...', res['pushes'][-3:], 'HP', res['hp0'] >> 10, res['hp1'] >> 10, flush=True)
    check('mashing wins', res['pushes'][-1] >= 0 and res['hp1'] < res['hp0'])
    check('winning takes a real shove: more than a second', res['frames'] > 60)
    check('winning costs him an eighth of his health or more', (res['hp0'] - res['hp1']) >> 10 >= 40000 // 8 - 200)
    check('no energy is spent while shoving', bool(res['energy']) and max(res['energy']) - min(res['energy']) <= 2)
    check('the beams line up head on', res['aligned'])
    check('the winning beam carries on without holding the button', res['surge'] == 1)
check('no bad jumps winning', not g.bad)
hp = g.mem(g.mem(ENEMIES)[0] + 0x28C)[0]
g.send('keys', 'run 200', 'shot win_later'); g.sync()
check('the game carries on after the win', not g.bad)
g.close()

g = into_fight(); res = clash(g, False, 'lose')
check('the beams clash again', bool(res) and res['began'])
if res and res['began']:
    print('   clash lasted', res['frames'], 'frames; pushes', res['pushes'][:3], '...', res['pushes'][-3:], flush=True)
    check('not mashing loses in a few seconds', res['pushes'][-1] < 0 and 120 < res['frames'] < 400)
    check('and he takes next to no damage: a stray tick, not a shove', res['hp0'] - res['hp1'] <= res['hp0'] // 100)     # with Glacier's song the timing lets one 48 HP tick land mid-clash
check('no bad jumps losing', not g.bad)
g.send('keys', 'run 200', 'tap A 8', 'shot lose_later'); g.sync()
check('the player can move and attack again', not g.bad and g.mem(CL + 0x18)[0] == 0)
g.close()
print('fails:', fails) if fails else print('ALL PASS')
sys.exit(1 if fails else 0)
