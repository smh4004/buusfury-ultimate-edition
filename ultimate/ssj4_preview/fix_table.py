"""Super Saiyan 4 Goku's preview fixes for the build (the owner, Nov 12 08:47, of every Super Saiyan 4 preview: "everyone else is
good"; 09:55: "Do 174 and 175 now"). After his touch-up (ssj4_table) and Gogeta's fixes (gogeta_preview/gogeta_table), build.py ssj4_fix
puts every frame of his figure through sprites.composed_actor with the table made here: the frame's pixels on its own box ->
plainback.fixed(slot, frame, view) (armfur: fur on the whole arm in every move; the plain back; the see-through pixels filled; heads.py:
the spin's legs and sides, hit 2 from the side, the special's last frame), larger where it outgrows the box (the spin from the side,
mirrored from the front, reaches a few pixels further left; the special's last frame is its frame before, two rows taller).

A picture the figure has at several places (his stance is also his costume change and victory; charging and the power-up face the
camera in all three views; the powering up is also his special) is one picture in the game: its fix is the one for its first place
in the figure, slot by slot, as the touch-up did (armfur lists that place). The preview drew each place by itself, so a place after
the first (charging from behind, say) showed the picture unfixed there; in the game every place shows the fixed picture.
Slots 22 and up (the charged punch, still BF Goku's own) are left."""
import hashlib, os, pickle, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
B = 0x08000000


def places(R, aid):
    """-> [(slot, frame, view, image, box)] for views 0-2 of slots 0-21, in slot order"""
    import ssj4_table
    rec = R.u(R.lst + 4 * aid) - B; n = R.slots(aid); out = []
    for s in sorted(n):
        if s >= 22: continue
        an = R.u(rec + 0x54 + 4 * s) - B
        for f in range(n[s]):
            for d in range(3):
                fp = R.u(an + 4 + 4 * (4 * f + d))
                if fp:
                    img, box = ssj4_table.boxed(R.rom, fp)
                    out.append((s, f, d, img, box))
    return out


def make(path, aid, gog, cache=None):
    """path: the ROM so far (his actor `aid` touched up, Super Saiyan 4 Gogeta's `gog` fixed). -> ({key(image): image, or (image,
    (dx, dy)) when it outgrew its box}, pictures changed)"""
    os.environ.update(BFU_GOG_ROM=path, BFU_GOG_AID=str(gog), BFU_GOKU_AID=str(aid))
    sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
    for m in ('frames', 'plainback', 'armfur', 'heads', 'lib4'): sys.modules.pop(m, None)
    import lib4, ssj4_table
    R = lib4.Rom(path); todo = places(R, aid); h = hashlib.sha1()
    for name in sorted(os.listdir(HERE)):
        if name.endswith('.py'): h.update(open(os.path.join(HERE, name), 'rb').read())
    for s, f, d, img, box in todo: h.update(bytes((s, f, d)) + ssj4_table.key(img) + bytes(np.array(box, np.int8).tobytes()))
    for d in range(3):                                           # BF Goku's frames are the guide; Gogeta's hit 2 gives a head
        for s, c in R.slots(106).items():
            for f in range(c): h.update(R.frame(106, s, f, d).tobytes())
    h.update(R.frame(gog, 9, 1, 2).tobytes())
    digest = h.hexdigest()
    if cache and os.path.exists(cache):
        try:
            got = pickle.load(open(cache, 'rb'))
            if got.get('digest') == digest: return got['table'], got['changed']
        except Exception: pass
    import plainback as P
    first = {}
    for s, f, d, img, box in todo: first.setdefault(ssj4_table.key(img), (s, f, d, img, box))
    table, changed = {}, 0
    for k, (s, f, d, img, (bx, by, bw, bh)) in first.items():
        top, left = 64 + by, 48 + bx; c0 = R.frame(aid, s, f, d)
        if not (c0[top:top + bh, left:left + bw] == img).all(): sys.exit('fix_table: frame %d.%d view %d is not laid out as read' % (s, f, d))
        new = P.fixed((s, f, d)); ys, xs = np.nonzero(new)
        up, lf, rt = max(0, top - int(ys.min())), max(0, left - int(xs.min())), max(0, int(xs.max()) + 1 - left - bw)
        if int(ys.max()) + 1 > top + bh or max(up, lf, rt) > 8:
            sys.exit('fix_table: frame %d.%d view %d outgrows its box by more than a strip (up %d, left %d, right %d, below %d)'
                     % (s, f, d, up, lf, rt, int(ys.max()) + 1 - top - bh))
        out = new[top - up:top + bh, left - lf:left + bw + rt].copy()
        if up or lf or rt: table[k] = (out, (-lf, -up)); changed += 1
        elif not (out == img).all(): table[k] = out; changed += 1
    if cache: pickle.dump({'digest': digest, 'table': table, 'changed': changed}, open(cache, 'wb'))
    return table, changed
