"""Approved figures stay as approved (Nov 10, the owner: "Reshoot it all and lock changes").

ultimate/locked.json lists forms whose figure the owner approved, each with a fingerprint of all its frames: every animation slot, frame and
view, the frame's box, each piece's place, size, flips and attributes, and its pixels, but not where any of it sits in the ROM (the build
moves things). check() runs on every build: a locked figure whose frames changed stops the build. A form listed with no fingerprint yet
gets one. BFU_RELOCK=<form>[,<form>...] records a new fingerprint for a change the owner asked for.
"""
import hashlib, json, os, struct, sys

BASE = 0x08000000
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locked.json')


def _frame(rom, fp, u):
    from wfz import decompress_stream
    o = fp - BASE; k = u(o); out = bytearray(rom[o + 4:o + 8])
    for j in range(k):
        p = o + 8 + 12 * j; w, h = rom[p + 2], rom[p + 3]; t = u(p + 8) - BASE
        kind, size = u(t), u(t + 4)
        raw = rom[t + 8:t + 8 + size] if kind == 0 else bytes(decompress_stream(rom, t + 8, size)[0])
        out += rom[p:p + 8] + bytes(raw[:w * h])
    return bytes(out)


def fingerprint(rom, rec):
    """SHA-1 of the frames of the actor record at ROM offset rec."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    h = hashlib.sha1(); frames = {}
    for slot in range(rom[rec]):
        ap = u(rec + 0x54 + 4 * slot)
        h.update(bytes([slot]))
        if not ap: h.update(b'-'); continue
        a = ap - BASE; n = u(a); h.update(struct.pack('<I', n))
        for i in range(4 * n):
            fp = u(a + 4 + 4 * i)
            if fp not in frames: frames[fp] = hashlib.sha1(_frame(rom, fp, u)).digest()
            h.update(frames[fp])
    return h.hexdigest()


def check(rom, forms, record_of):
    """forms: {name: form id}; record_of(form id) -> the form's actor record (ROM offset). Exits if a locked figure changed."""
    data = json.load(open(PATH))
    locked = data['forms']; relock = set(filter(None, os.environ.get('BFU_RELOCK', '').split(',')))
    changed, new = [], []
    for name, old in locked.items():
        if name not in forms: sys.exit('locked.json: no form %r in this build' % name)
        now = fingerprint(rom, record_of(forms[name]))
        if old is None or name in relock:
            if old != now: locked[name] = now; new.append(name)
        elif old != now: changed.append(name)
    if changed:
        sys.exit('LOCKED FRAMES CHANGED (approved by the owner): %s. Undo the change, or if the owner asked for it, build with BFU_RELOCK=%s'
                 % (', '.join(changed), ','.join(changed)))
    if new:
        json.dump(data, open(PATH, 'w'), indent=1); open(PATH, 'a').write('\n')
        print('locked figures recorded:', ', '.join(new))
    print('locked figures: %d unchanged' % (len(locked) - len(new)))
