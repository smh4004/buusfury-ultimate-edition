"""gif_cap.py ROM OUTDIR name:label:skills[:kind] ...  (a --debug build; run from the repo root; then gif_make.py)
In-game footage of a form's moves for the owner's previews ("Preview every fix as an animated gif too", Nov 10): the form worn in the field
(audit_moves' setup), each skill held and let go (kind 'a', facing left; 'aD', 'aU', 'aR' down, up, right), or pressed as a transformation
(kind 't': each skill in turn, no power-down between), a screenshot every
2 frames into OUTDIR/<name>/<clip>_<n>.png, and clips.json naming the clips."""
import sys, json, struct, subprocess, os
ROM, OUT = sys.argv[1:3]
rom = open(ROM, 'rb').read()
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
POS = {0: 0, 1: 1, 3: 2, 4: 3, 6: 4, 8: 5, 7: 5}
ROUTE = [l for l in open('tools/harness/long.txt').read().split('\n')[:93] if not l.startswith('shot ')]
NAMES = {1: 'Banshee Blast', 2: 'Big Bang', 3: 'Big Bang Kamehameha', 4: 'Burning Attack', 5: 'Dragon Fist Explosion', 6: 'Electric Kamehameha', 7: 'Energy Blast',
         8: 'Energy Punch', 9: 'Energy Sword', 10: 'Final Flash', 11: 'Flame Kamehameha', 13: 'Super Kamikaze Ghost Attack', 15: 'Kamehameha', 16: 'Kamekameha',
         17: 'Masenko', 18: 'Great Saiyaman', 19: 'Spirit Bomb', 20: 'Super Saiyan', 23: 'Ultra Volleyball Attack', 24: 'Eraser Cannon', 25: 'SS Deadly Bomber',
         26: 'Special Beam Cannon', 27: 'Blitz', 28: 'Destructo Disc', 29: 'Energy wave', 33: 'Black Kamehameha', 35: 'Super Saiyan 2', 38: 'Galick Gun',
         39: '10x Kamehameha', 40: 'Final Shine', 41: 'Super Dragon Fist', 43: 'Super Kamehameha', 14: 'Instant Transmission', 22: 'Super Saiyan 3',
         36: 'Super Saiyan 4', 44: 'Super Saiyan Blue', 37: 'Kaioken'}
for spec in sys.argv[3:]:
    parts = spec.split(':'); name, label, skills = parts[0], parts[1], [int(x) for x in parts[2].split(',')]; kind = parts[3] if len(parts) > 3 else 'a'
    d = os.path.join(OUT, name + ('' if kind == 'a' else '_' + kind)); os.makedirs(d, exist_ok=True)
    f0 = int(name) if name.isdigit() else forms[name]; owner = rom[0x800000 + 24 * f0 + 0x0C]
    c = owner if owner in POS else 8
    R = 0x03001560 + c * 0x68
    FULL = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)]
    POOLS = ['poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)] + ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 03' % (R + 0x1F), 'poke8 %08X FF' % (R + 0x20), 'poke8 %08X 03' % (R + 0x21)]     # the EP maximum first: a pool above it broke the HUD's bar loops (palette)
    held = sorted(set(skills), key=skills.index)[:6]
    L = ['guardon 0x09000000'] + ROUTE + (['poke8 %08X 03' % R] if c == 7 else []) + ['tap A 60', 'tap A 60', 'run 30'] + ['tap RIGHT 40'] * POS[c] + POOLS
    L += ['poke8 %08X %02X' % (R + 0x14, f0), 'run 4', 'tap A 200'] + POOLS + ['run 60']
    L += ['poke8 %08X %02X' % (R + 0x0C, len(held))] + ['poke8 %08X %02X' % (R + 0x0D + i, s) for i, s in enumerate(held)] + ['run 30']
    clips = []
    for k, s in enumerate(skills):
        tag = 'c%d' % k; n = 0
        def shots(count):
            global n
            out = []
            for _ in range(count): out.extend(['run 2', 'shot %s_%03d' % (tag, n)]); n += 1
            return out
        if kind[0] == 'a':          # 'a' faces left; 'aD', 'aU', 'aR' face down, up, right
            L += ['keys %s' % {'D': 'DOWN', 'U': 'UP', 'R': 'RIGHT'}.get(kind[1:], 'LEFT'), 'run 2', 'keys', 'run 10', 'poke8 %08X %02X' % (R + 0x15, held.index(s))] + FULL + ['keys B'] + shots(22) + ['keys'] + shots(28) + ['run 90']
        else:
            L += ['keys DOWN', 'run 2', 'keys', 'run 10', 'poke8 %08X %02X' % (R + 0x15, held.index(s))] + FULL + POOLS + ['shot %s_%03d' % (tag, 0), 'keys B', 'run 4', 'keys']; n = 1
            L += shots(75) + ['run 120']
        clips.append({'tag': tag, 'frames': n, 'move': NAMES.get(s, 'skill %d' % s)})
    L += ['mem %08X 1' % (R + 0x14), 'mem 05000200 128']
    open(d + '/r.txt', 'w').write('\n'.join(L) + '\n')
    o = subprocess.run(['tools/harness/harness', ROM, d + '/r.txt', d], capture_output=True, text=True, timeout=1500).stdout
    # the sprite palette at the end is the game's own: anything else means the capture itself disturbed the game
    words = [l for l in o.split('\n') if l.startswith('mem 05000200')][-1].split(':', 1)[1].split()
    hw = [v for w in words for v in (int(w, 16) & 0x7FFF, int(w, 16) >> 16 & 0x7FFF)]
    clean = open('baserom.gba', 'rb').read()[0x701B0 + 768:0x701B0 + 1536]
    want = [(clean[3 * i] >> 3) | (clean[3 * i + 1] >> 3) << 5 | (clean[3 * i + 2] >> 3) << 10 for i in range(256)]
    palbad = [i for i in range(1, 256) if hw[i] != want[i]]
    json.dump({'label': label, 'clips': clips, 'bad': 'bad pc' in o, 'palette': palbad}, open(d + '/clips.json', 'w'))
    print(name, kind, len(clips), 'clips', 'BAD PC' if 'bad pc' in o else '', ('PALETTE CHANGED %s' % palbad) if palbad else '', flush=True)
