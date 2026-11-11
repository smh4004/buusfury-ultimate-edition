#!/usr/bin/env python3
"""What changed in the figures between two builds (Nov 10): every actor record in the table, slot by slot, compared by the pixels of each
frame in each view, and every form's figure the same way. Run it after any sprite or build change and look at each line it prints:
  python3 ultimate/figure_diff.py OLD.gba NEW.gba        (each with its .map.json beside it)
A slot printed as 'k:a->b' changed from a frames to b (None: empty or not an animation)."""
import sys, json, struct, hashlib, os
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), d) for d in ('', 'lib')]
import sprites
B = 0x08000000
def record_slots(rom, rec):
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    out = {}
    for s in range(rom[rec]):
        ap = u(rec + 0x54 + 4 * s)
        if not B < ap < B + len(rom) or u(ap - B) > 64: out[s] = ap; continue
        fr = []
        for k in range(u(ap - B)):
            for v in range(4):
                fp = u(ap - B + 4 + 16 * k + 4 * v)
                im = sprites.frame_image(rom, fp) if fp and B < fp < B + len(rom) and u(fp - B) == 1 else None
                fr.append(hashlib.md5(im.tobytes()).hexdigest()[:8] if im is not None else hex(fp))
        out[s] = (u(ap - B), tuple(fr))
    return out
def actors(rom):
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    L = u(0x3C0) - B - 4; out = []
    for a in range(1024):
        r = u(L + 4 * a)
        if not B < r < B + len(rom) or not 0 < rom[r - B] <= 40: break
        out.append(record_slots(rom, r - B))
    return out
def show(a, b):
    ch = [s for s in sorted(set(a) | set(b)) if a.get(s) != b.get(s)]
    n = lambda v: v[0] if isinstance(v, tuple) else None
    return ch, ' '.join('%d:%s->%s' % (s, n(a.get(s)), n(b.get(s))) for s in ch)
old, new = open(sys.argv[1], 'rb').read(), open(sys.argv[2], 'rb').read()
ao, an = actors(old), actors(new)
print('actors: %d before, %d after' % (len(ao), len(an)))
for i in range(min(len(ao), len(an))):
    ch, txt = show(ao[i], an[i])
    if ch: print('actor %d: %s' % (i, txt))
fo = json.load(open(sys.argv[1].replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
fn = json.load(open(sys.argv[2].replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
for name in sorted(set(fn) - set(fo), key=fn.get): print('new form %s (%d)' % (name, fn[name]))
for name in sorted(set(fo) - set(fn), key=fo.get): print('FORM GONE %s (%d)' % (name, fo[name]))
for name in sorted(set(fo) & set(fn), key=fn.get):
    if fo[name] != fn[name]: print('FORM ID MOVED %s: %d -> %d (saves read it by number)' % (name, fo[name], fn[name]))
