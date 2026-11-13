#!/usr/bin/env python3
"""The enemy beam from the hand (Nov 12; lib/beam_hands.py tells it). The owner, 21:40: "Make the beam actually come from Cell's hand too not
the floor", "Scan all NPCs too for this especially big sized ones".

Needs enemy rigs on Kid Buu's stats row, one per figure to check (character = actor + 9):
  BFU_RIG_ENEMY="61 351" BFU_OUT=<cell dir> python3 ultimate/build.py --debug --enemy       (Perfect Cell)
  BFU_RIG_ENEMY="61 47"  BFU_OUT=<kid buu dir> python3 ultimate/build.py --debug --enemy    (Kid Buu)
  python3 ultimate/test_hands.py <work dir> name=<rig dir> ...        (name: a lib/beam_hands.py HANDS key)

Held, for each figure and each way he can face (put in line with the player and left to fire):
- the beam is drawn from his fingertip (hands.HANDS): its near end there and its middle line through his hand (its place in the game, plus
  what outfit.c hand_screen draws it moved by, plus the beam's own rows read back from the built ROM);
- what it hits is where the game's beam hits (its place across its line the game's: the enemy lines up with the player by his place);
- the ball (while he charges) is centred on that fingertip;
- he fires in his own two-handed beam's frames if he has them (beam_hands.POSE: the owner, 22:09), else the ki blast's, and the hands
  or the arm are held out (frame 1) while the beam is out, never frames 1 and 2 by turns;
- it hits the player it is aimed at, and nothing jumps to a bad address.
And on the built ROM, for every figure in HANDS: the side points are his ki blast's arm-out frame's outermost pixels (his hand), so a
changed figure can't leave the beam behind. Screenshots of each facing go in the work dir (<name>_<facing>_*.png)."""
import json, os, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, HERE + '/lib']
import numpy as np
import wrath, goku_black
import beam_hands as hands

D = sys.argv[1]; os.makedirs(D, exist_ok=True)
RIGS = dict(a.split('=', 1) for a in sys.argv[2:])
NAME = '/BFU_debug_enemy_PERSONAL_USE_ONLY.gba'
B = 0x08000000; R = 0x03001560; PLAYER = 0x03001C34; BEAM_VT = 0x0804AEF8; GAME_PARAMS = B + wrath.BEAM_PARAMS; ACTORS_AT = 0x850000
CASES = (('down', 0, (0, -56), 0), ('up', 1, (0, 70), -44), ('left', 2, (80, 0), 0), ('right', 3, (-80, 0), 0))
clean = open('baserom.gba', 'rb').read()
fails = []


def check(name, ok, note=''):
    print('PASS' if ok else 'FAIL', name, note if not ok else '', flush=True)
    if not ok: fails.append(name)


def s32(v): return v - (1 << 32) if v >> 31 else v


def fire(rom, dx, dy, player_dy, tag, frames=70):
    """Put the rig's enemy dx, dy from the player, held there until his beam starts. -> [per frame {count, frame, facing, e, beam, params,
    hp}], bad jump seen, the player's full health. (lib: as test_wrath.py's)"""
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

    send('guardon 0x09000000', *base); pl = mem(PLAYER)[0]; px, py = mem(pl + 0x1A0, 2); e = mem(0x03001BB4)[0]
    if player_dy:
        py = (py + (player_dy << 8)) & 0xFFFFFFFF; send('poke %08X %x' % (pl + 0x1A4, py), 'run 30')
    full = mem(R + 0x18)[0] & 0xFFFF; beam = None; log = []
    for _ in range(2400):
        if beam is None:
            send('poke8 %08X %02X' % (R + 0x16, full & 255), 'poke8 %08X %02X' % (R + 0x17, full >> 8),
                 'poke %08X %x' % (e + 0x1A0, (px + (dx << 8)) & 0xFFFFFFFF), 'poke %08X %x' % (e + 0x1A4, (py + (dy << 8)) & 0xFFFFFFFF))
        send('run 1')
        if beam is None:
            cnt = mem(0x03001C50)[0]
            for o in (mem(0x03001C54, cnt) if 0 < cnt <= 128 else []):
                if 0x02000000 <= o < 0x02040000 and mem(o)[0] == BEAM_VT: beam = o; break
            if beam is None: continue
        w = mem(beam, 20); ew = mem(e + 0x10, 1)[0]; alive = w[0] == BEAM_VT
        log.append({'count': ew >> 16, 'frame': ew >> 8 & 255, 'facing': ew & 3, 'e': [s32(v) >> 8 for v in mem(e + 0x1A0, 2)], 'anim': mem(e + 0x50)[0], 'fig': mem(e + 0x58)[0],
                    'beam': [s32(w[8]), s32(w[9])] if alive else None, 'params': w[16] if alive else 0, 'hp': mem(R + 0x16)[0] & 0xFFFF})
        if len(log) in (1, 4, 12, 30): send('shot %s_%02d' % (tag, len(log)))
        if len(log) >= frames: break
    mem(R); p.stdin.close(); p.wait()
    return log, bad[0], full


def rows_of(rom, params):
    head = struct.unpack_from('<I', rom, params - B + 12)[0] - B
    rows = bytearray(rom[head:head + 12 * 4 * wrath.ROWS])
    tiles = [(struct.unpack_from('<I', rows, 12 * k + 8)[0], rows[12 * k + 2] * rows[12 * k + 3]) for k in range(4 * wrath.ROWS)]
    tiles = [(t, n) for t, n in tiles if n and B < t < B + len(rom)]
    a, b = min(t for t, _ in tiles), max(t + n for t, n in tiles)
    return rows, bytes(rom[a - B:b - B]) + bytes(256), a


def end_and_middle(rows, block, base, facing):
    end = wrath.near_end(rows, block, base, facing)
    img, x, y = wrath.shown(rows, block, base, facing * wrath.ROWS + 3)
    ys, xs = np.nonzero(img)
    return end, (x + (xs.min() + xs.max()) / 2 if facing < 2 else y + (ys.min() + ys.max()) / 2)


def actor_of(name, rom_map):
    return hands.RETAIL[name] if name in hands.RETAIL else rom_map[name]


def arm_out(rom, actor, view, slot=3):
    """The arm-out frame (frame 1) of the slot he fires in (his own beam's, beam_hands.POSE, or the ki blast's, 3) in one view: its
    pixels' place-relative x and y."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    rec = u(ACTORS_AT + 4 * actor) - B; ap = u(rec + 0x54 + 4 * slot) - B; k = u(ap)
    o = u(ap + 4 + 16 * min(1, k - 1) + 4 * view) - B; xs, ys = [], []
    for i in range(min(u(o), 64)):
        p = o + 8 + 12 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, p); at = struct.unpack_from('<H', rom, p + 6)[0]
        img = goku_black.tiles(rom, u(p + 8) - B, w, h)
        if at & 0x1000: img = img[:, ::-1]
        if at & 0x2000: img = img[::-1]
        yy, xx = np.nonzero(img); xs += list(xx + x); ys += list(yy + y)
    return np.array(xs), np.array(ys)


# --- the side points against the frames, every figure -------------------------------------------------------------------------
first = next(iter(RIGS.values())) + NAME
rom = open(first, 'rb').read()
amap = json.load(open(first.replace('_PERSONAL_USE_ONLY.gba', '.map.json'))).get('actors', {})
off = []
for name, f in hands.HANDS.items():
    if name not in hands.RETAIL and name not in amap: off.append((name, 'not in the map')); continue
    a = actor_of(name, amap)
    for view, side in ((2, 'left'), (3, 'right')):
        xs, ys = arm_out(rom, a, view, hands.POSE.get(name, 3))
        edge = xs.min() if view == 2 else xs.max(); m = abs(xs - edge) <= 3          # (the hand: its four outermost columns, their rows' mean)
        if edge != f[view][0] or abs(ys[m].mean() - f[view][1]) > 1.5: off.append((name, side, int(edge), float(ys[m].mean()), f[view]))
check('the side points are each figure\'s hand (its arm-out frame\'s outermost pixel)', not off, str(off))

# --- in the game ---------------------------------------------------------------------------------------------------------------
for name, rig in RIGS.items():
    rom = open(rig + NAME, 'rb').read(); finger = hands.HANDS[name]
    ball_steps, move, lift = hands.steps(clean)[name]
    for side, facing, (dx, dy), pdy in CASES:
        log, bad, full = fire(rig + NAME, dx, dy, pdy, '%s_%s' % (name, side))
        json.dump(log, open('%s/%s_%s.json' % (D, name, side), 'w'))
        check('%s %s: he fires, facing %s' % (name, side, side), bool(log) and all(r['facing'] == facing for r in log[:20]), 'frames %d' % len(log))
        if not log: continue
        check('%s %s: no jump to a bad address' % (name, side), not bad)
        out = [r for r in log if r['beam'] and r['count'] >= 10]
        check('%s %s: the beam is out' % (name, side), len(out) >= 10, 'frames with it %d' % len(out))
        if not out: continue
        check('%s %s: the game\'s beam (the Kamehameha\'s table)' % (name, side), out[0]['params'] == GAME_PARAMS, '%08X' % out[0]['params'])
        rows, block, base = rows_of(rom, out[0]['params'])
        end, mid = end_and_middle(rows, block, base, facing)
        r = out[0]; bx, by = r['beam'][0] - r['e'][0], r['beam'][1] - r['e'][1]; fx, fy = finger[facing]
        game = struct.unpack_from('<ii', clean, wrath.ENEMY_STEPS + 48 + 8 * facing)
        check('%s %s: it hits where the game\'s beam hits (its place across its line the game\'s)' % (name, side), (bx if facing < 2 else by) == game[facing >= 2 and 1 or 0],
              'beam %d, %d from his place, the game\'s %s' % (bx, by, game))
        dx, dy = bx + lift[facing][0], by + lift[facing][1]                 # where it is drawn from (outfit.c hand_screen)
        along = (dy + end - fy) if facing < 2 else (dx + end - fx); across = (dx + mid - fx) if facing < 2 else (dy + mid - fy)
        check('%s %s: the beam\'s near end is drawn at his fingertip' % (name, side), abs(along) <= 3, 'off by %.1f along its line (drawn %d, %d from his place)' % (along, dx, dy))
        check('%s %s: its middle line is drawn through his hand' % (name, side), abs(across) <= 2.5, 'off by %.1f across' % across)
        early = [q for q in log if q['beam'] and q['count'] < 8]
        if early and early[0]['count'] == 0:                                   # (made this frame: before, he may have been moved by the test)
            q = early[0]; game = struct.unpack_from('<ii', clean, wrath.ENEMY_STEPS + 12 * facing)
            check('%s %s: the ball is moved to his fingertip (the game\'s step plus his)' % (name, side),
                  [q['beam'][0] - q['e'][0], q['beam'][1] - q['e'][1]] == [game[0] + ball_steps[facing][0], game[1] + ball_steps[facing][1]],
                  '%s' % ([q['beam'][0] - q['e'][0], q['beam'][1] - q['e'][1]],))
        slot = hands.POSE.get(name, 3); fig = out[0]['fig'] - B
        want = struct.unpack_from('<I', rom, fig + 0x54 + 4 * slot)[0]
        check('%s %s: he fires in %s (slot %d)' % (name, side, 'his own two-handed beam' if name in hands.POSE else 'the ki blast', slot),
              all(q['anim'] == want for q in out), '%s, the slot\'s %08X' % (sorted(set('%08X' % q['anim'] for q in out)), want))
        held = [q['frame'] for q in log if q['count'] >= 3 and q['beam']]
        check('%s %s: his arm is held out (frame 1, never 1 and 2 by turns)' % (name, side), bool(held) and set(held) == {1}, 'frames shown %s' % sorted(set(held)))
        check('%s %s: it hits the player it is aimed at' % (name, side), log[-1]['hp'] < full, 'health %d of %d' % (log[-1]['hp'], full))
print('%d failed' % len(fails) if fails else 'all passed')
sys.exit(1 if fails else 0)
