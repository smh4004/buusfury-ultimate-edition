"""Every move of every playable form, played in the emulator (Nov 10, the owner: "Should never be this many issues EVER don't let this happen
again TEST THOROUGHLY"). Build `--debug` first (no --enemy: a nearby foe's hits mix being-hit frames into the moves).
  python3 ultimate/audit_moves.py ROM OUTDIR [FORM ...]      (no forms: all of them; party forms run once per six of their book's skills)
Plays each playable form in the field (Switch Character -> the form) through
walking (4 ways), running, the punch combo, every skill it has (held, then let go), and its transformations up and down. Every distinct pose
the game shows (animation slot, frame, view) is drawn from the ROM at 3x, in order, one row per step, with two screenshots per step.
OUTDIR/<form>.png per form; OUTDIR/<form>.json lists the poses; OUTDIR/report.txt flags what to look at first:
- a pose the game played with no frame there (junk is drawn: an empty slot or a frame number past the animation's end),
- a frame of another retail character than the figure's own stance (a template's leftover: armour Gohan powering down as Great Saiyaman),
- being-hit frames (slot 9) in an attack or a change (no foe is near: the move's own slot holds them),
- a double-tap that didn't run (slot 2), a form change that didn't happen.
Then look at every sheet: the report can't see a pose that is merely wrong (a wind-up where the arm should be out)."""
import sys, os, json, struct, subprocess
sys.path[:0] = ['ultimate', 'ultimate/lib']
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import goku_black
ROM, OUT = sys.argv[1:3]; WANT = sys.argv[3:]; TAG = ''
os.makedirs(OUT, exist_ok=True)
rom = open(ROM, 'rb').read(); clean = open('baserom.gba', 'rb').read(); B = 0x08000000
u = lambda o: struct.unpack_from('<I', rom, o)[0]
forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3).copy()
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
RECS, RS, G = 0x03001560, 0x68, 0x03001068
POS = {0: 0, 1: 1, 3: 2, 4: 3, 6: 4, 8: 5, 7: 5}
ROUTE = [l for l in open('tools/harness/long.txt').read().split('\n')[:93] if not l.startswith('shot ')]
# skills (outfit.c guest_sync); transformations and their way back
BLITZ, DISC, WAVE, BEAM, ERASER, BOMBER, S13, S17, ROSE, BKAME, MAJUUB, KK, SOLAR, GALICK, MAXP = 27, 28, 29, 26, 24, 25, 30, 31, 32, 33, 34, 37, 42, 38, 45
GUEST = {'broly': [7, 8, ERASER], 'broly_fp': [7, 8, ERASER], 'android13': [7, 8, 25, WAVE, S13], 'super13': [7, 8, 25, WAVE],
         'piccolo': [7, 17, BEAM], 'android17': [7, 8, BLITZ, WAVE, S17], 'super17': [7, 8, BLITZ, WAVE], 'android18': [7, BLITZ, DISC, WAVE],
         'krillin': [7, 15, DISC, SOLAR, KK], 'videl': [7, KK], 'tien': [7, 15, BLITZ, SOLAR, KK], 'yamcha': [7, 15, KK], 'pikkon': [7, 8, WAVE],
         'hercule': [7, KK], 'goku_black': [7, 14, BKAME, ROSE], 'goku_rose': [7, 14, BKAME], 'future_trunks': [7, 20, 4, 11, GALICK],
         'future_trunks_ss': [7, 4, 11, GALICK, 20], 'uub': [7, 8, 15, MAJUUB], 'majuub': [7, 8, 15], 'roshi': [7, 8, 15, MAXP], 'roshi_max': [7, 8, 15],
         'kid_buu': [7, 8, 15], 'majin_buu': [7, 8, 15], 'super_janemba': [7, 8]}
for p in ('pan', 'pan_ssj', 'pan_nobandana', 'pan_ssj_spiky'): GUEST[p] = [7, 8, 20]
for p in ('pan_bug', 'pan_gi_tan', 'pan_gi_red', 'pan_brapan'): GUEST[p] = [7, 8]
TRANSFORM = {20, 35, 22, 36, 44, 37, S13, S17, ROSE, MAJUUB, MAXP, 46, 47}
L_ = u(0x3C0) - B - 4
def rec_of(f):
    a = struct.unpack_from('<H', rom, 0x800000 + 24 * f + 0x0E)[0] - 9
    if a < 0: return None                                    # a scene-only form (no figure of its own)
    r = u(L_ + 4 * a) - B
    return r if 0 < r < len(rom) else None
def frame_px(fp):
    CH, CW, OY, OX = 110, 120, 84, 60
    c = np.zeros((CH, CW), np.uint8); o = fp - B
    if not B < fp < B + len(rom): return c
    for i in range(min(u(o), 64)):
        p = o + 8 + 12 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, p); t = u(p + 8)
        img = goku_black.tiles(rom, t - B, w, h)
        at = struct.unpack_from('<H', rom, p + 6)[0]
        if at & 0x1000: img = img[:, ::-1]
        if at & 0x2000: img = img[::-1, :]
        for r in range(h):
            for k in range(w):
                R_, C = OY + y + r, OX + x + k
                if img[r, k] and 0 <= R_ < CH and 0 <= C < CW: c[R_, C] = img[r, k]
    return c
def play(name):
    f0 = forms[name]; owner = rom[0x800000 + 24 * f0 + 0x0C]
    c = 8 if name in GUEST or owner == 8 else owner
    if c not in POS: c = 8                                   # Goten, Gotenks: wear it in the guest slot
    skills = SKILLS_OVERRIDE or GUEST.get(name) or [7]
    R = RECS + c * RS
    p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', OUT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    bad = [False]; where = ['start']
    def send(*ls):
        for l in ls: p.stdin.write(l + '\n')
        p.stdin.flush()
    def mem(a, n=1):
        send('mem %08X %d' % (a, n))
        while True:
            l = p.stdout.readline()
            if not l: raise SystemExit('harness ended')
            if 'bad pc' in l and not bad[0]: bad[0] = '%s (%s)' % (where[0], l.strip()[:60])
            if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
    send('guardon 0x09000000', *ROUTE)
    if c == 7: send('poke8 %08X 03' % R)
    send('tap A 60', 'tap A 60', 'run 30'); mem(G)
    # Super Saiyan 3 and Blue forms drop back on the Switch screen when their pool (+0x1E Super Saiyan's, +0x20 Super Saiyan 3's) is empty
    # (the EP maximum first: the HUD draws each pool as pool * 41 / the EP maximum columns, and the retail loop has no bound, so a pool above
    # the maximum wrote bar pixels over the sprite palette and whatever else the next table words pointed at. The game caps it now, outfit.c
    # hud_row_guard; the audit still never asks for it)
    POOLS = ['poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)] + ['poke8 %08X FF' % (R + 0x1E), 'poke8 %08X 03' % (R + 0x1F), 'poke8 %08X FF' % (R + 0x20), 'poke8 %08X 03' % (R + 0x21)]
    send(*['tap RIGHT 40'] * POS[c]); send(*POOLS, 'poke8 %08X %02X' % (R + 0x14, f0), 'run 4', 'tap A 200', *POOLS, 'run 60')
    send('poke8 %08X %02X' % (R + 0x0C, len(skills)), *['poke8 %08X %02X' % (R + 0x0D + i, s) for i, s in enumerate(skills)], 'run 30')
    ok = (mem(R + 0x14)[0] & 255) == f0 and (mem(G)[0] & 255) == c
    FULL = ['poke8 %08X FF' % (R + 0x1A), 'poke8 %08X 03' % (R + 0x1B), 'poke8 %08X FF' % (R + 0x1C), 'poke8 %08X 03' % (R + 0x1D)]
    steps = []; nshot = [0]
    def watch(label, n, keys=None, every=2):
        where[0] = label
        poses = []; shots = []
        if keys: send('keys ' + keys)
        for i in range(n // every):
            send('run %d' % every)
            po = mem(0x03001C34)[0]; an = mem(po + 0x50)[0]; w = mem(po + 0x10)[0]; f = mem(R + 0x14)[0] & 255
            rec = rec_of(f); slot = {u(rec + 0x54 + 4 * s): s for s in range(rom[rec])}.get(an) if rec is not None else None
            fr, view = w >> 8 & 255, w & 3
            fp = None
            if B < an < B + len(rom) - 4:                     # also an animation from another figure's record (Kaioken's and SS4's change plays the new figure's)
                cnt = u(an - B)
                if fr < cnt < 64: fp = u(an - B + 4 + 16 * fr + 4 * view)
            key = (f, slot, fr, view)
            if not poses or poses[-1][0] != key: poses.append((key, fp))
            if i in (n // every // 3, 2 * n // every // 3):
                s = 'p_%s_%d' % (name, nshot[0]); nshot[0] += 1; send('shot ' + s); mem(G); shots.append(s)
        if keys: send('keys')
        steps.append((label, poses, shots))
    watch('stand', 12)
    watch('walk left', 16, 'LEFT'); watch('walk right', 16, 'RIGHT'); watch('walk up', 12, 'UP'); watch('walk down', 12, 'DOWN')
    send('keys LEFT', 'run 3', 'keys', 'run 3'); watch('run left', 30, 'LEFT'); watch('stop', 20)
    send('keys RIGHT', 'run 3', 'keys', 'run 3'); watch('run right', 30, 'RIGHT'); watch('stop', 20)
    send('keys LEFT', 'run 2', 'keys')
    for k in range(5): send('keys A', 'run 2', 'keys'); watch('punch %d' % (k + 1), 8)
    watch('after punches', 40)
    for i, s in enumerate(skills):
        if s in TRANSFORM: continue
        send('keys LEFT', 'run 2', 'keys', 'run 10', 'poke8 %08X %02X' % (R + 0x15, i), *FULL)
        watch('skill %d held' % s, 40, 'B'); watch('skill %d let go' % s, 70); send('run 90')
    for i, s in enumerate(skills):
        if s not in TRANSFORM: continue
        send('keys DOWN', 'run 2', 'keys', 'run 10', 'poke8 %08X %02X' % (R + 0x15, i), *FULL, *POOLS, 'keys B', 'run 4', 'keys')
        watch('transform (%d)' % s, 200, every=3)
        f1 = mem(R + 0x14)[0] & 255
        if f1 == f0: continue
        watch('walk left (new form)', 12, 'LEFT')
        if 7 in skills:
            send('poke8 %08X %02X' % (R + 0x15, skills.index(7)), *FULL); watch('ki blast (new form)', 30, 'B'); watch('', 30)
        send('run 200', 'poke8 %08X %02X' % (R + 0x15, i), *FULL, 'keys B', 'run 4', 'keys')
        watch('power down (%d)' % s, 260, every=3)
        send('run 200')
    p.stdin.close(); p.wait()
    if os.environ.get('NOPNG'):
        json.dump([(label, [list(k) + [fp or 0] for k, fp in poses]) for label, poses, _ in steps], open('%s/%s%s.json' % (OUT, name, TAG), 'w'))
        for s in os.listdir(OUT):
            if s.startswith('p_%s_' % name): os.remove(os.path.join(OUT, s))
        print(name + TAG, 'ok' if ok else 'NOT WORN', 'bad pc' if bad[0] else '', flush=True)
        REPORT.extend(flags(name + TAG, f0, steps, ok, bad[0])); return
    # sheet
    cache = {}
    allpx = []
    for _, poses, _ in steps:
        for key, fp in poses:
            if fp and fp not in cache: cache[fp] = frame_px(fp)
            if fp: allpx.append(cache[fp])
    m = np.zeros((110, 120), bool)
    for c_ in allpx: m |= c_ > 0
    ys, xs = np.nonzero(m) if m.any() else (np.array([0, 109]), np.array([0, 119]))
    y0, y1, x0, x1 = max(ys.min() - 2, 0), min(ys.max() + 3, 110), max(xs.min() - 2, 0), min(xs.max() + 3, 120)
    Z = 3; cw, ch = (x1 - x0) * Z, (y1 - y0) * Z
    def cell(fp, view):
        a = cache[fp][y0:y1, x0:x1]
        if view == 3: pass
        im = pal[a].copy(); im[a == 0] = (92, 140, 96)
        return Image.fromarray(np.kron(im, np.ones((Z, Z, 1), np.uint8)))
    rowh = max(ch, 160) + 22
    maxp = max(len(ps) for _, ps, _ in steps)
    W = 10 + min(maxp, 12) * (cw + 3) + 2 * 243; H = 30 + sum(rowh * ((len(ps) + 11) // 12 or 1) for _, ps, _ in steps)
    im = Image.new('RGB', (max(W, 900), H), (26, 26, 30)); d = ImageDraw.Draw(im)
    d.text((6, 6), '%s (form %d, character %d) skills %s %s' % (name, f0, c, skills, '' if ok else 'NOT WORN'), fill=(255, 214, 102), font=FONT)
    y = 30; log = []
    for label, poses, shots in steps:
        d.text((6, y + 2), label + '  ' + ' '.join('s%s/f%d/v%d' % (k[1], k[2], k[3]) + ('' if k[0] == f0 else '[%d]' % k[0]) for k, _ in poses)[:200], fill=(230, 230, 230), font=FONT)
        log.append((label, [list(k) + [fp or 0] for k, fp in poses]))
        yy = y + 20
        for i, (k, fp) in enumerate(poses):
            xx = 10 + (i % 12) * (cw + 3)
            if i and i % 12 == 0: yy += rowh
            if fp: im.paste(cell(fp, k[3]), (xx, yy))
            else: d.text((xx, yy), 'none', fill=(255, 80, 80), font=FONT)
        for j, s in enumerate(shots):
            im.paste(Image.open('%s/%s.png' % (OUT, s)).convert('RGB'), (10 + min(maxp, 12) * (cw + 3) + j * 243, y + 20))
        y += rowh * ((len(poses) + 11) // 12 or 1)
    im = im.crop((0, 0, im.width, y + 4))
    im.save('%s/%s%s.png' % (OUT, name, TAG)); json.dump(log, open('%s/%s%s.json' % (OUT, name, TAG), 'w'))
    for s in os.listdir(OUT):
        if s.startswith('p_%s_' % name): os.remove(os.path.join(OUT, s))
    print(name + TAG, 'ok' if ok else 'NOT WORN', 'bad pc' if bad[0] else '', im.size, flush=True)
    REPORT.extend(flags(name + TAG, f0, steps, ok, bad[0]))
# retail frames by owner (clean ROM), for the leftover flag
CL_ = struct.unpack_from('<I', clean, 0x3C0)[0] - B - 4; RETAIL = {}
k_ = 0
while B < struct.unpack_from('<I', clean, CL_ + 4 * k_)[0] < B + len(clean):
    r_ = struct.unpack_from('<I', clean, CL_ + 4 * k_)[0] - B
    for sl in range(clean[r_]):
        ap = struct.unpack_from('<I', clean, r_ + 0x54 + 4 * sl)[0]
        if B < ap < B + len(clean) and struct.unpack_from('<I', clean, ap - B)[0] <= 64:
            for i in range(4 * struct.unpack_from('<I', clean, ap - B)[0]): RETAIL.setdefault(struct.unpack_from('<I', clean, ap - B + 4 + 4 * i)[0], set()).add(k_)
    k_ += 1
def own_retail(f):
    rec = rec_of(f); out = set()
    if rec is None: return out
    for sl in (0, 1):
        ap = u(rec + 0x54 + 4 * sl)
        if ap:
            for i in range(4 * u(ap - B)): out |= RETAIL.get(u(ap - B + 4 + 4 * i), set())
    if rom[0x800000 + 24 * f + 0x0C] == 1: out.add(102)          # Gohan's Great Saiyaman costume change is his own
    return out
REPORT = []
FLASH = {(forms['gohan_armor'], 19): {98}}     # armour Gohan's Great Saiyaman change ends in the school uniform's flash (build.py fighter_poses)
def flags(name, f0, steps, ok, bad):
    out = []
    if not ok: out.append('%s: not worn (the picker kept another look)' % name)
    if bad: out.append('%s: the game jumped to a bad address%s' % (name, ', during %s' % bad if isinstance(bad, str) else ''))
    owns = {}
    for label, poses, _ in steps:
        for (f, slot, fr, view), fp in poses:
            if slot is not None and not fp: out.append('%s: %s: form %d slot %s frame %d view %d has no frame (junk is drawn)' % (name, label, f, slot, fr, view))
            if fp and fp in RETAIL:
                own = owns.setdefault(f, own_retail(f)) | FLASH.get((f, slot), set())
                if RETAIL[fp] - own and not (RETAIL[fp] & own): out.append('%s: %s: form %d slot %s shows retail actor %s\'s frame' % (name, label, f, slot, sorted(RETAIL[fp])))
            if slot == 9 and (label.startswith('skill') or label.startswith('transform') or label.startswith('power') or label.startswith('ki blast')):
                out.append('%s: %s: being-hit frames (slot 9)' % (name, label))
        if label == 'run right' and not any(k[1] == 2 for k, _ in poses): out.append('%s: a double-tap right did not run (slot 2)' % name)
        if label.startswith('transform') and all(k[0] == f0 for k, _ in poses): out.append('%s: %s: the form did not change' % (name, label))
    return sorted(set(out), key=out.index)
SKILL_BOOK = {0: (7, 15, 43, 14, 20, 35, 22, 36, 44, 37, 19, 39, 41, 21, 46, 5), 1: (7, 20, 35, 6, 17, 18, 26, 21, 47), 2: (7, 20, 16, 8, 12, 21),
              3: (7, 20, 35, 4, 11, 12, 21), 4: (7, 20, 35, 36, 44, 10, 2, 38, 40, 21), 5: (7, 20, 22, 13, 23, 21), 6: (7, 20, 35, 1, 9, 21),
              7: (7, 3, 5, 20, 44)}
SKILLS_OVERRIDE = None
if WANT[:1] == ['--report']:     # the report again from the json in OUTDIR (and any more dirs after it)
    for d in [OUT] + WANT[1:]:
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.json'): continue
            name = fn[:-5]; parts = name.rsplit('_', 1)
            base = parts[0] if len(parts) == 2 and parts[1].isdigit() and (parts[0] in forms or parts[0].startswith('retail')) else name
            f0 = forms[base] if base in forms else int(base[6:]) if base.startswith('retail') else None
            steps = [(label, [(tuple(q[:4]), q[4]) for q in poses], []) for label, poses in json.load(open(os.path.join(d, fn)))]
            REPORT.extend(flags(name, f0, steps, True, False))
    WANT = []
if not WANT and not REPORT:     # every form a player can wear (a Super Saiyan-class form is reached by changing into it, so it's played from the form below)
    wearable = lambda f: (rom[0x800000 + 24 * f + 0x0C] <= 8 and struct.unpack_from('<H', rom, 0x800000 + 24 * f + 0x0E)[0] >= 9
                          and not (rom[0x800000 + 24 * f] & 1 and rom[0x800000 + 24 * f + 0x17] != 255))
    WANT = [str(f) for f in range(54) if wearable(f)] + [n for n, f in sorted(forms.items(), key=lambda x: x[1]) if f >= 54 and wearable(f) and not n.startswith('shelved')]
for n in WANT:
    if n.isdigit(): forms['retail%s' % n] = int(n); n = 'retail%s' % n
    owner = rom[0x800000 + 24 * forms[n] + 0x0C]
    if n in GUEST or owner == 8:
        SKILLS_OVERRIDE = None; TAG = ''; play(n); continue
    book = [s for s in SKILL_BOOK.get(owner, (7,)) if s != 21]
    attacks = [s for s in book if s not in TRANSFORM]; tfs = [s for s in book if s in TRANSFORM]
    chunks = [attacks[i:i + 6] for i in range(0, len(attacks), 6)] + [[7] + tfs[i:i + 5] for i in range(0, len(tfs), 5)]
    for k, ch in enumerate(chunks):
        SKILLS_OVERRIDE = ch; TAG = '' if k == 0 else '_%d' % k; play(n)
open(os.path.join(OUT, 'report.txt'), 'w').write('\n'.join(REPORT) + '\n')
print('%d flags (report.txt)' % len(REPORT))
