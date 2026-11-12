#!/usr/bin/env python3
"""Wrath of the Gods (Nov 11): Beerus's own beam. The owner: "Change Beerus beam attack to actually fire from the hand and also give
him his own custom light yellow Frieza style finger beam attack not kamehameha called Wrath of the Gods". lib/wrath.py says how.

Needs two enemy rigs: Beerus, and Kid Buu's figure on the same stats row (any other enemy with this beam must keep the game's):
  BFU_RIG_ENEMY="61 421" BFU_OUT=<beerus dir> python3 ultimate/build.py --debug --enemy
  BFU_RIG_ENEMY="61 47"  BFU_OUT=<kid buu dir> python3 ultimate/build.py --debug --enemy
  python3 ultimate/test_wrath.py <beerus dir> <kid buu dir> [work dir]

In the emulator, for each way he can face: he is put in line with the player and left to fire. Held to:
- the beam's near end is at his fingertip (its place in the game plus the beam's own rows, read back from the built ROM, against his
  place plus lib/wrath.py FINGER), and its middle line runs through his hand;
- it is his beam (not the Kamehameha's table), drawn in the light yellows with none of the Kamehameha's blues left in its tiles;
- his pose is the ki blast's wind-up, then its arm out, held (never the two arm-out frames by turns);
- it hits the player it is aimed at;
- nothing jumps to a bad address.
And Kid Buu's figure on the same row fires the game's own beam from the game's own place, showing the game's own frames."""
import json, os, struct, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, HERE + '/lib']
import numpy as np
import wrath

BEERUS, KIDBUU = sys.argv[1], sys.argv[2]
D = sys.argv[3] if len(sys.argv) > 3 else tempfile.mkdtemp(prefix='wrath'); os.makedirs(D, exist_ok=True)
NAME = '/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
B = 0x08000000; R = 0x03001560; PLAYER = 0x03001C34; BEAM_VT = 0x0804AEF8; GAME_PARAMS = B + wrath.BEAM_PARAMS
BLUES, YELLOWS = set(wrath.TINT), set(wrath.TINT.values())
# (name, the way he faces, where he is put from the player (x, y), how far the player is moved up first)
CASES = (('left', 2, (80, 0), 0), ('right', 3, (-80, 0), 0), ('down', 0, (0, -56), 0), ('up', 1, (0, 70), -44))
clean = open('baserom.gba', 'rb').read()
fails = []


def check(name, ok, note=''):
    print('PASS' if ok else 'FAIL', name, note if not ok else '', flush=True)
    if not ok: fails.append(name)


def s32(v): return v - (1 << 32) if v >> 31 else v


def fire(rom, dx, dy, player_dy, frames=70, keep=False):
    """Put the rig's enemy dx, dy from the player and wait for its beam. -> [per frame {count, frame, facing, e, beam, params, hp}],
    bad jump seen, the player's full health. keep: hold the enemy at that place until the beam starts (Kid Buu: since the flash save (Nov 12)
    the rig's enemy is up and chasing when the route ends, where the EEPROM's save kept him still until after it, and from close by he
    fights hand to hand instead: tools/harness/enemy_test.txt)."""
    base = [l for l in open('tools/harness/enemy_test.txt').read().split('\n') if l and not l.startswith('#') and not l.startswith('mem ')
            and not l.startswith('shot ') and l not in ('tap B 20', 'run 200')]
    env = dict(os.environ); env.pop('HARNESS_SAV', None)
    p = subprocess.Popen(['tools/harness/harness', rom, '/dev/stdin', D], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, env=env)
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

    send(*base); pl = mem(PLAYER)[0]; px, py = mem(pl + 0x1A0, 2); e = mem(0x03001BB4)[0]
    if player_dy:
        py = (py + (player_dy << 8)) & 0xFFFFFFFF; send('poke %08X %x' % (pl + 0x1A4, py), 'run 30')
    send('poke %08X %x' % (e + 0x1A0, (px + (dx << 8)) & 0xFFFFFFFF), 'poke %08X %x' % (e + 0x1A4, (py + (dy << 8)) & 0xFFFFFFFF), 'run 4')
    full = mem(R + 0x18)[0] & 0xFFFF; beam = None; log = []
    for _ in range(1800):
        if beam is None: send('poke8 %08X %02X' % (R + 0x16, full & 255), 'poke8 %08X %02X' % (R + 0x17, full >> 8))    # (unhurt until it starts)
        if beam is None and keep: send('poke %08X %x' % (e + 0x1A0, (px + (dx << 8)) & 0xFFFFFFFF), 'poke %08X %x' % (e + 0x1A4, (py + (dy << 8)) & 0xFFFFFFFF))
        send('run 1')
        if beam is None:
            cnt = mem(0x03001C50)[0]
            for o in (mem(0x03001C54, cnt) if 0 < cnt <= 128 else []):
                if 0x02000000 <= o < 0x02040000 and mem(o)[0] == BEAM_VT: beam = o; break
            if beam is None: continue
        w = mem(beam, 20); ew = mem(e + 0x10, 1)[0]; alive = w[0] == BEAM_VT
        log.append({'count': ew >> 16, 'frame': ew >> 8 & 255, 'facing': ew & 3, 'e': [s32(v) >> 8 for v in mem(e + 0x1A0, 2)],
                    'beam': [s32(w[8]), s32(w[9])] if alive else None, 'params': w[16] if alive else 0, 'hp': mem(R + 0x16)[0] & 0xFFFF})
        if len(log) >= frames: break
    mem(R); p.stdin.close(); p.wait()
    return log, bad[0], full


def rows_of(rom, params):
    """The beam's 64 rows and their tiles as one block, read back from a built ROM by its table of levels. -> (rows, block, base)"""
    head = struct.unpack_from('<I', rom, params - B + 12)[0] - B
    rows = bytearray(rom[head:head + 12 * 4 * wrath.ROWS])
    tiles = [(struct.unpack_from('<I', rows, 12 * k + 8)[0], rows[12 * k + 2] * rows[12 * k + 3]) for k in range(4 * wrath.ROWS)]
    tiles = [(t, n) for t, n in tiles if n and B < t < B + len(rom)]
    a, b = min(t for t, _ in tiles), max(t + n for t, n in tiles)
    return rows, bytes(rom[a - B:b - B]) + bytes(256), a


def end_and_middle(rows, block, base, facing):
    """From the beam's place: where its near end is along its line, and its middle line across it (the brightest column or row)."""
    end = wrath.near_end(rows, block, base, facing)
    img, x, y = wrath.shown(rows, block, base, facing * wrath.ROWS + 3)          # a piece of its body
    ys, xs = np.nonzero(img)
    mid = x + (xs.min() + xs.max()) / 2 if facing < 2 else y + (ys.min() + ys.max()) / 2
    return end, mid


# --- Beerus ---------------------------------------------------------------------------------------------------------------------
rom = open(BEERUS + NAME, 'rb').read()
vt = struct.unpack_from('<I', rom, wrath.ENEMY_BEAM_VT_REF)[0]
check('the enemy beam is named by a copy of its table of functions', vt != B + wrath.ENEMY_BEAM_VT and B < vt < B + len(rom), '%08X' % vt)
ent = [vt + struct.unpack_from('<i', rom, vt - B + 4 * k)[0] for k in range(wrath.VT_ENTRIES)]
game = [B + wrath.ENEMY_BEAM_VT + struct.unpack_from('<i', clean, wrath.ENEMY_BEAM_VT + 4 * k)[0] for k in range(wrath.VT_ENTRIES)]
check('the copy differs from the game\'s in its first two entries only', ent[2:] == game[2:] and ent[0] != game[0] and ent[1] != game[1])
for name, facing, (dx, dy), pdy in CASES:
    log, bad, full = fire(BEERUS + NAME, dx, dy, pdy)
    json.dump(log, open('%s/beerus_%s.json' % (D, name), 'w'))
    check('%s: he fires, facing %s' % (name, name), bool(log) and all(r['facing'] == facing for r in log[:20]), 'frames %d' % len(log))
    if not log: continue
    check('%s: no jump to a bad address' % name, not bad)
    out = [r for r in log if r['beam'] and r['count'] >= 10]
    check('%s: the beam is out' % name, len(out) >= 10, 'frames with it %d' % len(out))
    if not out: continue
    params = out[0]['params']
    check('%s: it is his own beam, not the Kamehameha\'s table' % name, params != GAME_PARAMS and B < params < B + len(rom), '%08X' % params)
    rows, block, base = rows_of(rom, params)
    used = set(block[:-256])
    check('%s: light yellow, none of the Kamehameha\'s blues' % name, not used & BLUES and bool(used & YELLOWS), 'colours %s' % sorted(used & (BLUES | YELLOWS)))
    end, mid = end_and_middle(rows, block, base, facing)
    r = out[0]; bx, by = r['beam'][0] - r['e'][0], r['beam'][1] - r['e'][1]; fx, fy = wrath.FINGER[facing]
    along = (by + end - fy) if facing < 2 else (bx + end - fx); across = (bx + mid - fx) if facing < 2 else (by + mid - fy)
    # (it overlaps his fingertip by a pixel or two: never a gap, never from inside his arm)
    check('%s: the beam\'s near end is at his fingertip' % name, abs(along) <= 3, 'off by %.1f along its line (beam %d, %d from his place)' % (along, bx, by))
    check('%s: its middle line runs through his hand' % name, abs(across) <= 2.5, 'off by %.1f across' % across)
    held = [r['frame'] for r in log if r['count'] >= 3 and r['beam']]
    check('%s: his arm is held out (the one arm-out frame, never the two by turns)' % name, bool(held) and set(held) == {1}, 'frames shown %s' % sorted(set(held)))
    check('%s: it starts from the wind-up' % name, any(r['frame'] == 0 for r in log if r['count'] < 2) or log[0]['count'] >= 2, 'first %s' % log[0])
    check('%s: it hits the player it is aimed at' % name, log[-1]['hp'] < full, 'health %d of %d' % (log[-1]['hp'], full))
ball = struct.unpack_from('<I', rom, params - B + 8)[0] - B
t0, t1 = [struct.unpack_from('<I', rom, ball + 12 * k + 8)[0] - B for k in (0, 1)]
check('nothing shows on his finger while he winds up, then a glint', not any(rom[t0:t0 + 64]) and any(rom[t1:t1 + 256]) and not set(rom[t1:t1 + 256]) & BLUES)

# --- any other enemy with this beam: the game's ---------------------------------------------------------------------------------
log, bad, full = fire(KIDBUU + NAME, 80, 0, 0, keep=True)
out = [r for r in log if r['beam'] and r['count'] >= 10]
check('Kid Buu: he fires', len(out) >= 10 and not bad, 'frames with it %d' % len(out))
if out:
    r = out[0]; step = struct.unpack_from('<ii', clean, wrath.ENEMY_STEPS + 48 + 8 * r['facing'])
    check('Kid Buu: the Kamehameha\'s own table', r['params'] == GAME_PARAMS, '%08X' % r['params'])
    check('Kid Buu: laid where the game lays it', (r['beam'][0] - r['e'][0], r['beam'][1] - r['e'][1]) == tuple(step), '%s, the game\'s %s' % ([r['beam'][0] - r['e'][0], r['beam'][1] - r['e'][1]], step))
    check('Kid Buu: the game\'s own two frames by turns', {1, 2} <= set(q['frame'] for q in log if q['count'] >= 10))
    check('Kid Buu: it hits', log[-1]['hp'] < full)
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
