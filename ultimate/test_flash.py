#!/usr/bin/env python3
"""The 64 KB flash save (Nov 12) across emulators: mGBA (tools/harness), VBA-M's libretro core with a
frontend's save memory (RetroArch; likely Manic EMU's VBA-M core), Delta's VBA-M (GBADeltaCore pins VBA-M 453fa0d, Nov 2018:
utilGBAFindSave, CPUReadBatteryFile / CPUWriteBatteryFile) and gpSP's libretro core, through tools/harness/lr_harness.py.
  BFU_SLOT_TEST=1 BFU_OUT=<flash dir> python3 ultimate/build.py --debug --zone       (<eeprom dir>: such a build from before the flash, kept)
  BFU_VBAM_CORE=<vbam_libretro.so> BFU_DELTA_CORE=<.so> BFU_GPSP_CORE=<gpsp_libretro.so> python3 ultimate/test_flash.py <flash dir> <eeprom dir> [work dir]
Cores: VBA-M's libretro core (cmake -DBUILD_LIBRETRO / ENABLE_LIBRETRO); Delta's: VBA-M 453fa0d `make -C src/libretro`, linked again
without link.T so CPUReadBatteryFile and the rest are exported; gpSP: libretro/gpsp `make`. Needs BFU_PROTO (zone 26's maps).
Routes are test_slots.py's: a new game, a guest swap that saves, and a reload where the bench brings the first guest back. The other
cores play the new game's intro on other frames (the flash build's start-up waits out mGBA's EEPROM time, which VBA-M never took),
so their saves are made from mGBA's (load, swap, save), and Delta's core plays the new game with the EEPROM build only."""
import json, os, shutil, struct, subprocess, sys, tempfile
FDIR, EDIR = sys.argv[1], sys.argv[2]
d = sys.argv[3] if len(sys.argv) > 3 else tempfile.mkdtemp(prefix='flash'); os.makedirs(d, exist_ok=True)
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
import bench as BN                                   # the guest bench (lib/bench.py)
import guestnav                                      # the guest slot's keys (lib/guestnav.py)
FL = FDIR + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'; EE = EDIR + '/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
forms = json.load(open(FDIR + '/BFU_debug_zone.map.json'))['forms']
LR = ['python3', 'tools/harness/lr_harness.py']
EMU = {'mgba': ['tools/harness/harness'],
       'vbam': LR + [os.environ['BFU_VBAM_CORE'], 'retroarch'],
       'delta': LR + [os.environ['BFU_DELTA_CORE'], 'delta'],
       'gpsp': LR + [os.environ['BFU_GPSP_CORE'], 'retroarch']}
SIZE = {'mgba': 0x10000, 'vbam': 0x10000, 'delta': 0x10000, 'gpsp': 0x20000}       # gpSP keeps 128 KB of save memory whatever the chip
G = 0x03001068; RECS = 0x03001560; REC = 0x68; R8 = RECS + 8 * REC; GEN_AT = 0x4F1; BENCH_OFFSET = 0x1A20
fails = []
def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)
    if not ok: fails.append(name)
def run(emu, lines, sav, rom=FL):
    p = d + '/s.txt'; open(p, 'w').write('\n'.join(lines) + '\n')
    env = dict(os.environ); env['HARNESS_SAV'] = sav
    r = subprocess.run(EMU[emu] + [rom, p, d], capture_output=True, text=True, env=env, timeout=900)
    return r.stdout + r.stderr
def state(name): return ['dump %s %08X 8a8' % (name, G)]
def read(name):
    g = open('%s/%s.bin' % (d, name), 'rb').read(); r = g[0x4F8 + 8 * REC:0x4F8 + 9 * REC]
    return dict(cur=g[0], form=r[0x14], exp=struct.unpack_from('<I', r, 0x24)[0], stat=r[0x28], gen=g[GEN_AT] | g[GEN_AT + 1] << 8, out=g[GEN_AT + 2])
def unblock(f): return b''.join(f[i:i + 8][::-1] for i in range(0, len(f), 8))
ROM_BYTES = open(FL, 'rb').read()
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
def talk_at(emu, base, x, y, sav=None, rom=FL):
    lines = list(base)
    if sav: shutil.copy(sav, d + '/probe.sav'); sav = d + '/probe.sav'
    else:
        sav = d + '/probe.sav'
        if os.path.exists(sav): os.remove(sav)
    out = run(emu, lines + ['mem 03001C34 1'], sav, rom)
    pl = int([l for l in out.splitlines() if l.startswith('mem 03001c34')][-1].split()[2], 16)
    return lines + ['poke %08X %08X' % (pl + 0x1A0, x << 8), 'poke %08X %08X' % (pl + 0x1A4, (y + 22) << 8), 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80']
GUEST = ['tap RIGHT 30'] * 6; DOWN = lambda n: ['tap DOWN 30'] * n; UP = lambda n: ['tap UP 30'] * n
CONFIRM = ['tap A 200', 'run 120']
BOOT = ['run 600', 'tap START 60', 'tap START 60', 'tap A 90', 'tap A 120', 'tap A 200', 'tap A 200', 'run 300']
P = open(os.environ['BFU_PROTO'], 'rb').read(); cfg = json.load(open('ultimate/zone26.json'))
door = [x for x in zone26.links(cfg, {a: zone26.floor_mask(P, os.environ['BFU_PROTO'], a) for a in range(1, 16)})[1] if 'world' in x][0]
KEYS = 'DOWN UP LEFT RIGHT'.split(); PL = 0x0202E8E4
x0, y0, x1, y1 = door['rect']
home = start + ['poke %08X %08X' % (PL + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (PL + 0x1A4, ((y0 + y1) // 2) << 8), 'keys ' + KEYS[door['key']], 'run 12', 'keys', 'run 150']
FLAGS = ['poke8 %08X %02X' % (G + 0x55 + 862 // 8, 1 << 862 % 8), 'poke8 %08X %02X' % (G + 0x55 + 883 // 8, 1 << 883 % 8)]

def swap_save(emu, rom=FL, tag=''):
    """New game, Broly out with 111111 exp, swap to Piccolo and save. -> (save file, state)"""
    hub = talk_at(emu, home + FLAGS, 96, 328, rom=rom)
    hub = talk_at(emu, hub + ['run 200'], *zone26.HUB_AT, rom=rom)
    to_piccolo = guestnav.keys('piccolo', start='broly', wait=30) if rom == FL else DOWN(3)     # (the Nov 12 EEPROM build: Down through every look)
    s1 = hub + ['poke %08X %08X' % (R8 + 0x24, 111111), 'poke8 %08X %02X' % (R8 + 0x28, 11)] + GUEST + to_piccolo + CONFIRM + ['shot swap_%s%s' % (emu, tag)] + state('b')
    sav = '%s/%s%s.sav' % (d, emu, tag)
    if os.path.exists(sav): os.remove(sav)
    out = run(emu, s1, sav, rom)
    return sav, read('b'), out

def reload(emu, src, tag, was='piccolo', move=None, now='broly'):
    """Boot from the save, load the game (`was` out), swap (`now` from the bench) and save again."""
    sav = '%s/re_%s.sav' % (d, tag); shutil.copy(src, sav)
    move = move or guestnav.keys(now, start=was, wait=30)
    back = talk_at(emu, BOOT + state('r'), *zone26.HUB_AT, sav=sav) + GUEST + move + CONFIRM + ['shot back_%s' % tag] + state('i')
    shutil.copy(src, sav)
    out = run(emu, back, sav)
    r, i = read('r'), read('i')
    ok = r['form'] == forms[was] and r['exp'] == 111111 and i['form'] == forms[now] and i['exp'] == 111111 and i['stat'] == 11
    return sav, ok, r, i

def saved_ok(emu, sav):
    f = open(sav, 'rb').read()
    return len(f) == SIZE[emu] and struct.unpack_from('<I', f, BN.sector(0))[0] == BN.MAGIC and set(f[BN.sector(0) + BN.SIZE:]) == {0xFF} and set(f[0x2000:BN.sector(0)]) <= {0xFF}

made = {}
for emu in ('mgba',):
    sav, b, out = swap_save(emu)
    f = open(sav, 'rb').read(); raw = unblock(f)
    head = struct.unpack_from('<III', f, BN.sector(0))
    print(emu, 'save', len(f), 'bytes; state', b)
    check('%s: new game, swap to Piccolo' % emu, b['form'] == forms['piccolo'] and b['exp'] == 111111 and b['gen'] != 0)
    check('%s: a 64 KB flash save' % emu, len(f) == 0x10000)
    check('%s: the game in the first 8 KB, in the EEPROM file\'s layout, and the bench in its own sector' % emu, head[0] == BN.MAGIC and head[1] == b['gen'] and raw[0x10:0x18] != b'\xff' * 8)
    check('%s: nothing else past the first 8 KB' % emu, set(f[0x2000:BN.sector(0)]) <= {0xFF} and set(f[BN.sector(0) + BN.SIZE:]) == {0xFF})
    made[emu] = sav
for emu in ('mgba', 'vbam', 'delta', 'gpsp'):
    sav, ok, r, i = reload(emu, made['mgba'], 'mgba_to_%s' % emu)
    check('mGBA save in %s: loads (Piccolo out), Broly back from the bench' % emu, ok)
    check('mGBA save in %s: saved again (%d KB)' % (emu, SIZE[emu] >> 10), saved_ok(emu, sav))
    if emu != 'mgba':
        sav2, ok, r, i = reload('mgba', sav, '%s_back_to_mgba' % emu, 'broly', None, 'piccolo')
        check('and that %s save in mGBA: Broly out, Piccolo back from the bench' % emu, ok)
for emu in ('delta',):                 # a save Delta's core wrote, back in it
    sav, ok, r, i = reload(emu, d + '/re_mgba_to_delta.sav', 'delta_to_%s' % emu, 'broly', None, 'piccolo')
    check('Delta save in %s: loads (Broly out), Piccolo back from the bench' % emu, ok and saved_ok(emu, sav))
# an old 8 KB EEPROM save (the EEPROM build, mGBA)
old, b, out = swap_save('mgba', EE, '_eeprom')
check('EEPROM build: an 8 KB save', len(open(old, 'rb').read()) == 0x2000 and b['form'] == forms['piccolo'])
for emu in ('mgba', 'vbam', 'gpsp', 'delta'):
    sav, ok, r, i = reload(emu, old, 'eeprom_to_%s' % emu)
    print('%s: old 8 KB save %s' % (emu, 'loads' if ok else 'does not load'), r, i)
    if emu != 'delta': check('%s: old 8 KB EEPROM save loads into the flash build' % emu, ok and saved_ok(emu, sav))
    else: check('delta: an 8 KB file is read as EEPROM, not flash (expected: blank)', not ok)
pad = d + '/padded.sav'; open(pad, 'wb').write(open(old, 'rb').read() + b'\xff' * 0xE000)
sav, ok, r, i = reload('delta', pad, 'padded_to_delta')
check('delta: the old save padded to 64 KB loads', ok and saved_ok('delta', sav))
# a save Delta made with the EEPROM build, padded to 64 KB
old, b, out = swap_save('delta', EE, '_eeprom')
f = open(old, 'rb').read()
diff = [i for i in range(0x2000) if unblock(f)[i] != unblock(open(d + '/mgba_eeprom.sav', 'rb').read())[i]]
print('Delta\'s EEPROM save against mGBA\'s, bytes that differ:', [hex(i) for i in diff])
check('Delta, EEPROM build: an 8 KB save in mGBA\'s layout (a few bytes of play differ)', len(f) == 0x2000 and b['form'] == forms['piccolo'] and len(diff) < 32)
pad = d + '/delta_padded.sav'; open(pad, 'wb').write(f + b'\xff' * 0xE000)
for emu in ('delta', 'mgba', 'vbam'):
    sav, ok, r, i = reload(emu, pad, 'delta_eeprom_padded_to_%s' % emu)
    check('Delta\'s EEPROM save, padded to 64 KB, in %s' % emu, ok and saved_ok(emu, sav))
print('FAILED: %s' % fails if fails else 'ALL PASS')
sys.exit(1 if fails else 0)
