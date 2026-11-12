"""Super Saiyan 4 Goku's touch-up for the build (approved Nov 11, 21:01: "Lock that Goku for now"). gt.py makes him from the owner's
sheet as before; build.py ssj4_goku then puts every frame through sprites.composed_actor with the table made here: the frame's
pixels on its own box -> the touched-up frame (v4.frame(slot, frame, view, 'mix')), larger where the new front hair is taller or
wider than the box (composed_actor adds strips for that).

A frame the figure has more than once (his slot 19 is his stance and ki blast again) is touched up as its first place in the figure,
slot by slot, which is how the lists in armhand.py were read. Slots 22 and up (the charged punch, still BF Goku's own) are left."""
import hashlib, os, pickle, struct, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
B = 0x08000000


def boxed(rom, fp):
    """A frame's pieces on its own box, as sprites.composed_actor hands them to its function. -> (image, (x, y, w, h))"""
    import goku_black
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    o = fp - B; bx, by, bw, bh = struct.unpack_from('<bbBB', rom, o + 4); img = np.zeros((bh, bw), np.uint8)
    for j in range(u(o)):
        x, y, w, h = struct.unpack_from('<bbBB', rom, o + 8 + 12 * j)
        img[y - by:y - by + h, x - bx:x - bx + w] = goku_black.tiles(rom, u(o + 16 + 12 * j) - B, w, h)
    return img, (bx, by, bw, bh)


def key(img): return img.tobytes() + bytes(img.shape)


def make(path, aid, gog, cache=None):
    """path: the ROM so far (his actor `aid` as gt.py made him, Super Saiyan 4 Gogeta's `gog`). -> {key(image): image, or
    (image, (dx, dy)) when it outgrew the box}, and how many frames changed."""
    os.environ.update(BFU_SSJ4_ROM=path, BFU_SSJ4_AID=str(aid), BFU_SSJ4_GOG=str(gog))
    sys.path.insert(0, HERE)
    for m in ('lib4', 'v2', 'v3', 'v4', 'hands', 'armhand'): sys.modules.pop(m, None)
    import lib4
    R = lib4.Rom(path); rom = R.rom; u = R.u
    rec = u(R.lst + 4 * aid) - B; n = R.slots(aid); todo = []; seen = set(); h = hashlib.sha1()
    for name in sorted(os.listdir(HERE)):
        if name.endswith('.py'): h.update(open(os.path.join(HERE, name), 'rb').read())
    for a in (gog, 106):
        for d in range(3): h.update(R.frame(a, 0, 0, d).tobytes())
    for s in sorted(n):
        an = u(rec + 0x54 + 4 * s) - B
        for f in range(n[s]):
            for d in range(3):
                fp = u(an + 4 + 4 * (4 * f + d))
                if not fp: continue
                img, box = boxed(rom, fp); k = key(img); h.update(bytes((s, f, d)) + k)
                if s < 22 and k not in seen and img.any(): seen.add(k); todo.append((s, f, d, img, box))
    for d in range(3):                                           # (BF Goku's frames are the guide: all of them count)
        for s, c in R.slots(106).items():
            for f in range(c): h.update(R.frame(106, s, f, d).tobytes())
    digest = h.hexdigest()
    if cache and os.path.exists(cache):
        try:
            got = pickle.load(open(cache, 'rb'))
            if got.get('digest') == digest: return got['table'], got['changed']
        except Exception: pass
    import v4
    table = {}; changed = 0
    for s, f, d, img, (bx, by, bw, bh) in todo:
        top, left = 64 + by, 48 + bx; c0 = R.frame(aid, s, f, d)
        if not (c0[top:top + bh, left:left + bw] == img).all(): sys.exit('ssj4_table: frame %d.%d view %d is not laid out as read' % (s, f, d))
        new = v4.frame(s, f, d, 'mix'); ys, xs = np.nonzero(new)
        up, lf, rt = max(0, top - int(ys.min())), max(0, left - int(xs.min())), max(0, int(xs.max()) + 1 - left - bw)
        if int(ys.max()) + 1 > top + bh or max(up, lf, rt) > 8:
            sys.exit('ssj4_table: frame %d.%d view %d outgrows its box by more than a strip (up %d, left %d, right %d)' % (s, f, d, up, lf, rt))
        out = new[top - up:top + bh, left - lf:left + bw + rt].copy()
        if up or lf or rt: table[key(img)] = (out, (-lf, -up)); changed += 1
        elif not (out == img).all(): table[key(img)] = out; changed += 1
    if cache: pickle.dump({'digest': digest, 'table': table, 'changed': changed}, open(cache, 'wb'))
    return table, changed
