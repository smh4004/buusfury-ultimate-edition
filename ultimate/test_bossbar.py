#!/usr/bin/env python3
"""The boss bar, in the emulator (build `--debug --zone` first; set BFU_PROTO):
  python3 ultimate/test_bossbar.py [work dir] [rom]
Nov 11, the owner: "give every single new boss fight a custom health bar too", "Add health bars to all the bosses in game right now and
reuse Buus fury assets", and, of the bar the mod drew by itself at first: "That's not what I meant by the boss hp bars at all. Use the
ones that already existed in Buus Fury for boss fights."
Buu's Fury has a boss bar (the slanted red bar that slides in at the top right of the story's boss fights); outfit.c bossbar_tick
asks the game for that same one in every fight the mod added (zone26.boss_table) and draws nothing itself. lib/bossbar.py is the
model of the game's bar and lib/barcheck.py reads it back from the actor list, the sprites and their tiles; test_cell, test_ladder,
test_chamber, test_bog and test_garlic call it in their own fights, and test_story looks at the story's own (Broly's) as it always was.
1. The ROM's table: every row the mod adds has its byte (all of them, without playing them) but the Makyans'.
2. On the way to Android 13: no bar. In his room: the game's own bar actor, one of them, slid down to its place, full, its tiles the
   game's art, at the HUD's priority; the fighter's own HUD beside it.
   It is there whether he is on the screen or not.
3. Health taken from him: the bar follows, rounded down as the game's own bars are. Punched: it follows the real damage.
4. He falls: the bar is empty and told to leave (it slides out once the text box that opens there closes, as the game's own
   do). His change (a scene): no bar, none on the list. Super 13: his own bar, full.
5. Sprite memory: the fighters and the game's HUD are still drawn with the bar up, and a free block is left."""
import json, os, struct, subprocess, sys, tempfile, queue, threading
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26, bossbar, barcheck
W = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix='bar'); os.makedirs(W, exist_ok=True)
ROM = sys.argv[2] if len(sys.argv) > 2 else 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
rom = open(ROM, 'rb').read()
PROTO = os.environ['BFU_PROTO']; P = open(PROTO, 'rb').read(); cfg = json.load(open('ultimate/zone26.json'))
D = zone26.links(cfg, {a: zone26.floor_mask(P, PROTO, a) for a in range(1, 16)})
start = open('tools/harness/long.txt').read().split('\n')[1:93] + ['tap A 60'] * 4 + ['run 60', 'keys DOWN', 'run 30', 'keys', 'run 200']
KEYS = 'DOWN UP LEFT RIGHT'.split(); PL = 0x0202E8E4; AT = 0x0300197C; LIST = 0x03001C4C
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)

# 1. the table
bad = barcheck.find_table(rom); tab, groups = zone26.boss_table(); named = zone26.row_names()
print('   %d rows with a bar, %d names' % (len(named), len(groups)))
check('the ROM holds the boss table: %s' % (bad or 'found'), not bad)
check('every row past the game\'s own is named or the Makyans\'', all(n or k == len(zone26.foe_names()) - 1 - len(zone26.garlic.FIGHTS) for k, n in enumerate(zone26.foe_names())))
check('none of the game\'s own rows is in it but Android 13\'s and Super 13\'s (the story\'s fights keep their own bars)',
      sorted(r for r in named if r < zone26.STATS_COUNT) == sorted((zone26.PHASE1_ROW, zone26.BOSS_ROW)))
clean = open('baserom.gba', 'rb').read()
check('the mod\'s bars answer with the game\'s own ten functions, but for "is it shown?" (one table in the ROM)', barcheck.mod_table(rom) is not None)
check('the game\'s boss bar is where lib/bossbar.py says: its art, its columns, its maker in the ROM as in the game',
      all(rom[a:a + n] == clean[a:a + n] for a, n in ((bossbar.ART, bossbar.BYTES), (bossbar.COLUMNS, 16 * bossbar.COLS), (bossbar.MAKE - 0x08000000, 0x80), (bossbar.VTABLE - 0x08000000, 56))))

def door(a):
    d = [x for x in D[a] if x['to'] == {8: 10}.get(a, a + 1) and 'world' not in x][0]; x0, y0, x1, y1 = d['rect']
    return ['poke %08X %08X' % (PL + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (PL + 0x1A4, ((y0 + y1) // 2) << 8), 'keys ' + KEYS[d['key']], 'run 12', 'keys', 'run 110']
env = dict(os.environ); env.pop('HARNESS_SAV', None)
p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', W], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
q = queue.Queue(); crashed = [False]
def drain():
    for line in p.stdout:
        if 'bad pc' in line: crashed[0] = True
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
def blocks():
    """Sprite memory's free blocks, (where, how long) in bytes (the actor list's chain: outfit.c bolt_room)."""
    def rb(a, n):                                    # (a block's record is 10 bytes: read by whole words, cut to it)
        data = b''.join(struct.pack('<I', w) for w in mem(a & ~3, (a % 4 + n + 3) // 4)); return data[a % 4:a % 4 + n]
    out = []; k = mem(LIST)[0] & 255
    while k != 0xFF and len(out) < 64:
        rec = rb(LIST + k * 10 + 0x694, 10); start, size = struct.unpack_from('<HH', rec, 2)
        out.append((start << 6, size << 6)); k = rec[8]
    return out
def free(): return [size for _, size in blocks()]
def drawn():
    """How many sprites are on the screen (OAM entries not switched off and not parked below it)."""
    oam = mem(0x07000000, 256)
    return sum(1 for k in range(128) if (oam[2 * k] >> 8 & 3) != 2 and (oam[2 * k] & 0xFF) < 160)
def settle(bar, tries=40, **kw):
    """The bar slides down for sixteen frames and is drawn in the frame after the health changes: a few looks, a frame apart."""
    for _ in range(tries):
        got, bad = bar.check(**kw)
        if not bad: break
        send('run 1')
    return got, bad

bar = barcheck.Bar(rom, mem)
send('guardon 0x09000000', *start); mem(AT)
got, bad = bar.check(); check('no bar on Snake Way: %s' % (bad or 'none'), got is None and not bad)
for a in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13): send(*door(a))
mem(AT); got, bad = bar.check()
check('no bar on the way to the fight (area %d): %s' % (mem(AT)[0] >> 8 & 255, bad or 'none'), got is None and not bad)
before = free(); n0 = drawn()
send(*door(14), 'run 30'); send('poke8 03001577 7F'); mem(AT)
check('the door leads to Android 13', mem(AT)[0] & 0xFFFF == (15 << 8 | 26))

# 2. Android 13
got, bad = settle(bar); send('shot a13_full'); name, hp, full = bar.boss()
print('   boss %s %d/%d, bar %s' % (name, hp, full, got))
check('Android 13 has his bar, full: %s' % (bad or got), not bad and name == 'Android 13' and got == bossbar.COLS)
acts = bar.actors(); print('   boss bar actors:', [(hex(a), y, sp, c, hex(t), w) for a, y, sp, c, t, w in acts])
check('it is the game\'s bar actor, asked for by the mod, one of them, at rest at its place', len(acts) == 1 and acts[0][1] == bossbar.Y and acts[0][2] == 0 and acts[0][5] == 'mod')
tile = bar.sprites(); oam = mem(0x07000000, 256)
raw = b''.join(struct.pack('<I', w) for w in mem(0x06010000 + tile * 32, bossbar.BYTES // 4)) if tile is not None else b''
check('its tiles are the game\'s art, whole (the full bar)', raw == clean[bossbar.ART:bossbar.ART + bossbar.BYTES])
hud = [k for k in range(128) if oam[2 * k] & 0xFFFF == 0x6008 and oam[2 * k] >> 16 == 0x8008]
check('the fighter\'s own HUD is drawn too, at its place', len(hud) == 1)
after = free()
print('   sprite memory free: %s before the room, %s with the bar up' % (before, after))
check('sprite memory still has a free block of 1 KB with the bar up', max(after or [0]) >= 0x400)
foe = next(e for e in mem(0x03001BB4, mem(0x03001BB0)[0]) if mem(e + 0x224)[0] == bar.table + 28 * zone26.PHASE1_ROW)
pl = mem(0x03001C34)[0]
# 2b. he need not be on the screen: Goku at the arena's bottom and he at its top, the bar stays (Semi-Perfect Cell starts his fight just
# above the screen's top edge)
far = ['poke %08X %08X' % (pl + 0x1A0, 120 << 8), 'poke %08X %08X' % (pl + 0x1A4, 276 << 8), 'poke %08X %08X' % (foe + 0x1A0, 120 << 8), 'poke %08X %08X' % (foe + 0x1A4, 112 << 8)]
send(*far, 'run 20', *far, 'run 2'); who, _, _ = bar.boss(); got, bad = bar.check(); cam = mem(0x030019C0)[0]
print('   he at row 112, the view from row %d: boss %s, bar %s' % (cam, who, got))
check('off the screen, his bar stays up: %s' % (bad or got), who == 'Android 13' and got == bossbar.COLS and not bad)
send('poke8 03001577 7F')
# 3. health taken
send('poke %08X %08X' % (foe + 0x28C, (full // 2) << 10), 'run 3'); got, bad = settle(bar); send('shot a13_half')
check('half his health gone: the bar shows half (%s of %d columns): %s' % (got, bossbar.COLS, bad or 'right'), not bad and got == bossbar.columns(full // 2, full))
send('poke %08X %08X' % (foe + 0x28C, 1 << 10), 'run 3'); got, bad = settle(bar)
check('one point of health left: no column, the bar still there (rounded down, as the game\'s own): %s' % (bad or got), not bad and got == 0)
send('poke %08X %08X' % (foe + 0x28C, (full // 2) << 10), 'run 3')
for _ in range(12):                                  # (whether a punch lands hangs on where he walks: beside him again until one does)
    x, y = mem(foe + 0x1A0, 2)
    send('poke %08X %08X' % (pl + 0x1A0, x), 'poke %08X %08X' % (pl + 0x1A4, y + (20 << 8)), 'keys UP', 'run 6', 'keys', *['tap A 14'] * 3, 'poke8 03001577 7F')
    if bar.boss()[1] < full // 2: break
_, hp2, _ = bar.boss(); got, bad = settle(bar); send('shot a13_hit')
print('   punched: %d -> %d, bar %s' % (full // 2, hp2, got))
check('punched, he loses health and the bar follows: %s' % (bad or got), hp2 < full // 2 and not bad)
# the HUD's own sprites and the fighters are still there (the bar took no one's tiles)
check('with the bar up the fighters and the HUD are still drawn (%d sprites, %d before the room)' % (drawn(), n0), drawn() >= n0 + 3)
# 4. he falls, his change, then Super 13. (Whether a punch lands hangs on where he walks: punch until he has fallen, then press through
# his change until the next room is reached, rather than a fixed count of presses.)
for _ in range(40):
    if bar.boss()[1] <= 0: break
    send('poke %08X %08X' % (foe + 0x28C, 2 << 10), 'poke8 03001577 7F', 'poke %08X %08X' % (pl + 0x1A0, mem(foe + 0x1A0)[0]), 'poke %08X %08X' % (pl + 0x1A4, mem(foe + 0x1A4)[0] + (20 << 8)),
         'keys UP', 'run 6', 'keys', 'tap A 14')
acts = bar.actors(); _, hp3, _ = bar.boss()
print('   he has %d health; boss bar actors: %s' % (hp3, [(hex(a), y, sp, c, w) for a, y, sp, c, t, w in acts]))
# (the game holds its actors still while a text box is up, its own bars too: Broly's stays, empty, through "Goku has reached level 73!")
check('he falls: his bar is empty and on its way out (its speed byte is the game\'s "leave"), or gone already', hp3 <= 0 and (not acts or (acts[0][2] == 0xFF and acts[0][3] == 0)))
seen_change = False
for _ in range(60):
    send('tap A 25'); at = mem(AT)[0] & 0xFFFF
    if at != (15 << 8 | 26) or not mem(0x03001BB0)[0]: break
send('run 130'); got, bad = bar.check(); at = mem(AT)[0] & 0xFFFF; send('shot change')
check('his change (room %d): no bar, none on the list: %s' % (at >> 8, bad or 'none'), got is None and not bad and not bar.actors())
for _ in range(12):
    if mem(AT)[0] & 0xFFFF == (17 << 8 | 26): break
    send('tap A 60', 'tap A 60', 'tap A 60', 'run 100', 'keys UP', 'run 60', 'keys', 'run 120', 'poke8 03001577 7F')
check('the route reaches Super 13', mem(AT)[0] & 0xFFFF == (17 << 8 | 26))
got, bad = settle(bar); send('shot s13_full'); name, hp, full = bar.boss()
print('   boss %s %d/%d, bar %s' % (name, hp, full, got))
check('Super 13 has his own bar, full: %s' % (bad or got), not bad and name == 'Super 13' and got == bossbar.COLS)
check('no crash', not crashed[0])
p.stdin.close(); p.wait()
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
