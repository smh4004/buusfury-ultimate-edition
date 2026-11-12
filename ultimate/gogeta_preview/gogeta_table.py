"""Super Saiyan 4 Gogeta's fixes for the build (approved Nov 11, 22:35: "Okay good lock it for now"). gt.py makes him from the owner's
sheet as before; build.py gogeta_fix then puts every frame through sprites.composed_actor with the table made here: the frame's pixels
on its own box -> fixed.fixed(slot, frame, view) cut back to that box. fixes.py holds what changes (the idle, walk and run frames,
and from the side the see-through spot over his eye wherever his head is).

A frame the figure has more than once (his slot 19 is his stance and ki blast again, slot 11 his stance) is one picture: the fix
fixes.py lists for it at any of its places is its fix everywhere. If two listed places of one picture would come out differently,
the build stops."""
import hashlib, os, pickle, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
B = 0x08000000


def make(path, gog, goku, cache=None):
    """path: the ROM so far. -> ({key(image): fixed image}, frames changed)"""
    os.environ.update(BFU_GOG_ROM=path, BFU_GOG_AID=str(gog), BFU_GOKU_AID=str(goku))
    sys.path[:0] = [HERE, os.path.join(HERE, '..', 'ssj4_preview')]
    for m in ('frames', 'patch', 'fixes', 'fixed', 'lib4'): sys.modules.pop(m, None)
    import ssj4_table, lib4
    R = lib4.Rom(path); rom = R.rom; u = R.u
    rec = u(R.lst + 4 * gog) - B; n = R.slots(gog); h = hashlib.sha1(); todo = []
    for name in sorted(os.listdir(HERE)):
        if name.endswith('.py'): h.update(open(os.path.join(HERE, name), 'rb').read())
    for s in sorted(n):
        an = u(rec + 0x54 + 4 * s) - B
        for f in range(n[s]):
            for d in range(3):
                fp = u(an + 4 + 4 * (4 * f + d))
                if not fp: continue
                img, box = ssj4_table.boxed(rom, fp); h.update(bytes((s, f, d)) + ssj4_table.key(img))
                if img.any(): todo.append((s, f, d, img, box))
    for d in range(3):
        for s, c in R.slots(106).items():
            for f in range(c): h.update(R.frame(106, s, f, d).tobytes())
    digest = h.hexdigest()
    if cache and os.path.exists(cache):
        try:
            got = pickle.load(open(cache, 'rb'))
            if got.get('digest') == digest: return got['table'], got['changed']
        except Exception: pass
    import fixed, fixes
    got = {}                                                   # picture -> [(listed in fixes.py, place, out)]
    for s, f, d, img, (bx, by, bw, bh) in todo:
        top, left = 64 + by, 48 + bx; c0 = R.frame(gog, s, f, d)
        if not (c0[top:top + bh, left:left + bw] == img).all(): sys.exit('gogeta table: frame %d.%d view %d is not laid out as read' % (s, f, d))
        new = fixed.fixed((s, f, d)); ys, xs = np.nonzero(new)
        if ys.min() < top or ys.max() >= top + bh or xs.min() < left or xs.max() >= left + bw:
            sys.exit('gogeta table: frame %d.%d view %d outgrows its box' % (s, f, d))
        got.setdefault(ssj4_table.key(img), []).append(((s, f, d) in fixes.ALL, (s, f, d), new[top:top + bh, left:left + bw].copy(), img))
    table, changed = {}, 0
    for k, places in got.items():
        listed = [p for p in places if p[0]] or places
        for p in listed[1:]:
            if not (p[2] == listed[0][2]).all():
                sys.exit('gogeta table: frame %d.%d view %d and %d.%d view %d are one picture but would come out differently' % (listed[0][1] + p[1]))
        out, img = listed[0][2], listed[0][3]
        if not (out == img).all(): table[k] = out; changed += 1
    if cache: pickle.dump({'digest': digest, 'table': table, 'changed': changed}, open(cache, 'wb'))
    return table, changed
