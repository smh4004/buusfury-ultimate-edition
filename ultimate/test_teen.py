#!/usr/bin/env python3
"""Teen Gohan (Nov 12): his own guest, the purple gi (base, Super Saiyan, Super Saiyan 2) and the Saiyan armor that was adult Gohan's.
  python3 ultimate/test_teen.py ROM [work dir]       (a --debug --enemy build; set BFU_COMBO)
1. Read from the ROM, no emulator: every frame of his purple-gi Super Saiyan and Super Saiyan 2 figures is one teen.py makes (the owner's
   approved frames, Nov 11), shown the same way for the same direction (its pixels, its place round the origin, mirrored to the right),
   and nothing of the purple record's own (long black hair) is left in them. His base figure is LoG2's purple record (r50), every slot filled.
   The armor's forms are his (owner 8, his name), not adult Gohan's.
2. In the Bomber fight: each look's ki blast and Kamehameha hit and its Masenko goes, in base, Super Saiyan and Super Saiyan 2, no bad jump,
   and Super Saiyan 2 comes through the Super Saiyan skill with no story flag (ss2_open). The pose the game shows each frame of the
   Kamehameha is the figure's beam pose (its ki blast's wind-up, then its arm out held)."""
import json, os, struct, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, 'lib'), 'tools/scripts']
ROM = sys.argv[1] if len(sys.argv) > 1 else 'ultimate/out/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
D = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix='teen'); os.makedirs(D, exist_ok=True)
rom = open(ROM, 'rb').read(); BASE = 0x08000000
u = lambda o: struct.unpack_from('<I', rom, o)[0]
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
LIST = u(0x3C0) - BASE - 4
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)

import sprites, teen, artclean, goku_black
l2 = open(os.environ['BFU_COMBO'], 'rb').read()[0x800000:]
teen.use(l2)
clean = open('baserom.gba', 'rb').read()
pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
cmap = sprites.log2_colour_map(l2, [i for i in range(1, 256) if i not in artclean.MENU_SLOTS], pal)

def row(form): return rom[0x800000 + 24 * form:0x800000 + 24 * form + 24]
def record(form): return u(LIST + 4 * (struct.unpack_from('<H', row(form), 0x0E)[0] - 9)) - BASE
def canvas(fp):
    """A frame as the game shows it (flips applied), on a 128x128 canvas round the actor's origin (64, 64)."""
    o = fp - BASE; c = np.zeros((128, 128), np.uint8)
    for i in range(u(o)):
        p = o + 8 + 12 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, p); img = goku_black.tiles(rom, u(p + 8) - BASE, w, h)
        a1 = struct.unpack_from('<H', rom, p + 6)[0]
        if a1 & 0x1000: img = img[:, ::-1]
        if a1 & 0x2000: img = img[::-1]
        m = img > 0; c[64 + y:64 + y + h, 64 + x:64 + x + w][m] = img[m]
    return c
def slots(rec):
    out = {}
    for s in range(rom[rec]):
        ap = u(rec + 0x54 + 4 * s)
        if ap: a = ap - BASE; out[s] = [[u(a + 4 + 16 * i + 4 * d) for d in range(4)] for i in range(u(a))]
    return out

# 1. the frames in the ROM. Changes and power-downs (slots 10 and 11, build.py LOG2_CHANGES) show one frame, the front, in every view.
P = teen.REC['P']
def place(px, x, y):
    c = np.zeros((128, 128), np.uint8); h, w = px.shape; c[64 + y:64 + y + h, 64 + x:64 + x + w] = cmap[px]; return c.tobytes()
def made_views(name):
    src = teen.made(name); want = {d: set() for d in range(4)}
    for k in teen.ANIMS[name]:
        for d in range(4):
            for f in range(teen.L.nframes(P, k)):
                px, (x, y, w, h) = src(P, k, d, f); want[d].add(place(px, x, y))
    return want
def own_views():
    want = {d: set() for d in range(4)}
    for k in range(24):
        for d in range(4):
            for f in range(teen.L.nframes(P, k)):
                v = teen.L.raw(P, k, d, f)
                if v is not None: want[d].add(place(v[4], v[0], v[1]))
    return want
VIEWS = {'teen_gohan': own_views(), 'teen_gohan_ss': made_views('ss'), 'teen_gohan_ss2': made_views('ss2')}
NEXT = {'teen_gohan': 'teen_gohan_ss', 'teen_gohan_ss': 'teen_gohan_ss2', 'teen_gohan_ss2': None}
for form in ('teen_gohan', 'teen_gohan_ss', 'teen_gohan_ss2'):
    want = VIEWS[form]; every = set().union(*want.values())
    change = every | (set().union(*VIEWS[NEXT[form]].values()) if NEXT[form] else set()) | (set().union(*VIEWS['teen_gohan'].values()) if form != 'teen_gohan' else set())
    sl = slots(record(forms[form])); n = 0; bad = []
    for s, frames in sl.items():
        for i, fr in enumerate(frames):
            for d in range(4):
                n += 1; c = canvas(fr[d]).tobytes()
                if not (c in want[d] if s not in (10, 11) else c in change): bad.append((s, i, d))
    print('   %s: %d slots, %d frame views; not as made: %s' % (form, len(sl), n, bad[:12]))
    check('%s: every frame is %s, shown as made for its direction' % (form, 'the purple record\'s own' if form == 'teen_gohan' else 'one teen.py makes'), n > 0 and not bad)
    need = [s for s in list(range(24)) + [31] if not (s == 11 and form == 'teen_gohan')]     # (a base form never powers down: no 11, as armour Gohan's and Future Trunks')
    check('%s: every slot a fighter uses is filled (0-23, and the beam pose 31)' % form, all(s in sl for s in need))
for f in ('teen_gohan', 'teen_gohan_ss', 'teen_gohan_ss2', 'gohan_armor', 'gohan_armor_ss', 'gohan_armor_ss2'):
    r = row(forms[f])
    check('%s: owner 8 (the guest), name "Teen Gohan"' % f, r[0x0C] == 8 and struct.unpack_from('<H', r, 2)[0] == 1588)
check('the chain: purple gi base, Super Saiyan, Super Saiyan 2, and back to base',
      row(forms['teen_gohan'])[0x16] == forms['teen_gohan_ss'] and row(forms['teen_gohan_ss'])[0x16] == forms['teen_gohan_ss2']
      and row(forms['teen_gohan_ss'])[0x17] == forms['teen_gohan'] and row(forms['teen_gohan_ss2'])[0x17] == forms['teen_gohan'] and row(forms['teen_gohan_ss2'])[0x16] == 255)

# 2. in the Bomber fight, his figure from the start (the form set during the intro, before the field loads the player's actor)
import test_moves as T
TEEN = [7, 8, 17, 15, 20]                      # ki blasts, rush, Masenko, Kamehameha, Super Saiyan (outfit.c teen)
R = T.R
k_ = [i for i, l in enumerate(T.base) if l == 'tap A 100'][20]
for look in ('teen_gohan', 'gohan_armor'):
    T.base[k_:k_] = ['poke8 %08X %02X' % (R + 0x14, forms[look])]
    for tier, presses in (('base', (0,)), ('ss', (0, 4)), ('ss2', (0, 4, 4))):
        want = forms[look] if tier == 'base' else forms[look + '_' + tier]
        beam = u(record(want) + 0x54 + 4 * 31) if rom[record(want)] > 31 else None
        res = {}
        for slot, move in ((0, 'blast'), (2, 'masenko'), (3, 'kame')):
            hp, form, badpc = T.fire('%s_%s_%s' % (look, tier, move), TEEN, slot, forms[look], presses, watch=(move == 'kame'))
            res[move] = (hp, form, badpc)
        poses = sorted(set(a for a, fr in T.watched))
        print('   %s %s: blast %.1f, Masenko %.1f, Kamehameha %.1f, form %s; Kamehameha poses %s (beam pose %s)' % (
            look, tier, res['blast'][0], res['masenko'][0], res['kame'][0], res['kame'][1], [hex(a) for a in poses], beam and hex(beam)))
        # (the Masenko is thrown up and forward, as Piccolo's and Gohan's are: from beside the Bomber it flies over him, so no damage is asked of it)
        check('%s %s: ki blast and Kamehameha hit, the Masenko goes, all in that form with no bad jump' % (look, tier),
              all(v[1] == want and not v[2] for v in res.values()) and res['blast'][0] > 0 and res['kame'][0] > 0)
        check('%s %s: the Kamehameha shows his beam pose while held' % (look, tier), beam is not None and beam in poses)
    del T.base[k_]
# 3. As the guest (Nov 12, the owner: "add skill and transformation mastery and skill swap for guests if you can but only lore accurate
#    stuff"): in the debug build, Teen Gohan picked on the Switch screen at the start (the guest slot, then his fighter: lib/guestnav.py)
#    plays, with a fight's flag set. His Super Saiyan trains his own mastery byte (the bench's spare field: lib/bench.py GUEST_MASTERY, Teen
#    Gohan's Super Saiyan second), not Goku's; at Level 3 it shows on the skill and drains slower; his moves level with him (his
#    Kamehameha and Masenko at the top level, Level 3, as the party's at 150 and 125; ki blasts have no levels).
import bench as BN, guestnav, subprocess
ZROM = os.path.join(os.path.dirname(ROM), 'BFU_debug_PERSONAL_USE_ONLY.gba')        # (the plain debug build opens the Switch screen after the intro)
R8 = R + 8 * 0x68; G = 0x03001068; COMBAT = 0x03001988
START = open('tools/harness/long.txt').read().split('\n')[1:93]
def guest_run(name, mastery, frames, exp=None, skills=(7, 20)):
    L = ['guardon 0x09000000'] + START + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * 5 + guestnav.keys('teen_gohan') + ['tap A 200', 'run 60']
    L += ['poke8 %08X %02X' % (R8 + 0x0C, len(skills))] + ['poke8 %08X %02X' % (R8 + 0x0D + i, v) for i, v in enumerate(skills)]
    L += ['poke %08X 00000001' % COMBAT, 'run 4'] + BN.ON + ['poke8 %08X %02X' % (BN.GUEST_MASTERY + 1, mastery), 'poke8 %08X 00' % BN.MASTERY]
    if exp is not None: L += ['poke %08X %08X' % (R8 + 0x24, exp)]
    L += ['run 140', 'poke8 %08X 01' % (R8 + 0x15), 'poke8 %08X FF' % (R8 + 0x1A), 'poke8 %08X 03' % (R8 + 0x1B), 'keys B', 'run 2', 'keys', 'run 200']
    L += ['poke8 %08X FF' % (R8 + 0x1E), 'poke8 %08X 03' % (R8 + 0x1F), 'mem %08X 26' % R8, 'mem %08X 4' % BN.GUEST_MASTERY, 'mem %08X 1' % BN.MASTERY]
    L += ['run 30', 'poke %08X 00000001' % COMBAT] * (frames // 30) + ['mem %08X 26' % R8, 'mem %08X 4' % BN.GUEST_MASTERY, 'mem %08X 1' % BN.MASTERY, 'mem %08X 1' % G, 'shot %s' % name]
    open(D + '/%s.txt' % name, 'w').write('\n'.join(L) + '\n')
    o = subprocess.run(['tools/harness/harness', ZROM, D + '/%s.txt' % name, D], capture_output=True, text=True, timeout=900).stdout
    w = lambda a: [[int(v, 16) for v in l.split(':')[1].split()] for l in o.splitlines() if l.startswith('mem %08x' % a)]
    rec = [b''.join(x.to_bytes(4, 'little') for x in r) for r in w(R8)[-2:]]
    gm = [b''.join(x.to_bytes(4, 'little') for x in r) for r in w(BN.GUEST_MASTERY)[-2:]]
    return rec, gm, [r[0] & 255 for r in w(BN.MASTERY)[-2:]], w(G)[-1][0] & 255, 'bad pc' in o
zforms = json.load(open(ZROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
rec, gm, goku, me, bad = guest_run('guest_mastery', 0, 1200)
print('   as the guest: playing %d, form %d, his Super Saiyan mastery %d -> %d, Goku\'s %s' % (me, rec[-1][0x14], gm[0][1], gm[-1][1], goku))
check('as the guest, Teen Gohan\'s Super Saiyan trains his own mastery, not Goku\'s', me == 8 and rec[0][0x14] == zforms['teen_gohan_ss'] and gm[-1][1] > gm[0][1] and goku == [0, 0] and not bad)
rec0, _, _, _, _ = guest_run('guest_drain0', 0, 450)
rec3, gm3, _, _, bad3 = guest_run('guest_drain3', 250, 450)
d0 = struct.unpack_from('<H', rec0[0], 0x1E)[0] - struct.unpack_from('<H', rec0[1], 0x1E)[0]; d3 = struct.unpack_from('<H', rec3[0], 0x1E)[0] - struct.unpack_from('<H', rec3[1], 0x1E)[0]
print('   his Super Saiyan bar drained %d unmastered, %d at Level 3; the skill\'s level byte %d' % (d0, d3, rec3[-1][0x2E + 2]))
check('mastered, his Super Saiyan shows Level 3 and drains about 3/5 as fast', rec3[-1][0x2E + 2] == 2 and d0 > 6 and 0.45 < d3 / d0 < 0.75 and not bad3)
recl, _, _, _, badl = guest_run('guest_levels', 0, 120, exp=0x7FFFFFFF, skills=(7, 20, 15, 17))
print('   at the top level his moves\' levels: %s' % list(recl[-1][0x2E:0x2E + 2 * recl[-1][0x0C]:2]))
check('his moves level with him: at the top level his Kamehameha and Masenko are Level 3; ki blasts have no levels (as the party\'s)',
      recl[-1][0x2E + 4] == 2 and recl[-1][0x2E + 6] == 2 and recl[-1][0x2E] == 0 and not badl)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
