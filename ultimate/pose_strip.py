#!/usr/bin/env python3
"""Clean pose strips for the owner's previews (Nov 10): the poses the game showed in audit_moves steps, in order (repeats dropped), at 3x, no
markings, a plain caption per row.
  python3 ultimate/pose_strip.py ROM OUT.png TITLE  AUDIT.json:label[+label...]=caption ...
label is an audit step's label (prefix match: 'skill 7 held', 'transform (20)', 'run right'). The frame pointers in an audit's json are the
ROM's it played: give that ROM, or set POSE_ROMS='dir=rom,dir=rom' to pick one per audit directory."""
import sys, json, struct, os
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), d) for d in ('', 'lib')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import goku_black
ROM, OUT, TITLE = sys.argv[1:4]; ITEMS = sys.argv[4:]
clean = open('baserom.gba', 'rb').read(); B = 0x08000000
ROMS = {}
PICK = dict(kv.split('=', 1) for kv in os.environ.get('POSE_ROMS', '').split(',') if '=' in kv)
def rom_for(path):     # each audit's poses point into the ROM it played
    return PICK.get(os.path.basename(os.path.dirname(os.path.abspath(path))), ROM)
rom = None
u = lambda o: struct.unpack_from('<I', rom, o)[0]
pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3).copy()
F1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22); F2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
def frame_px(fp):
    CH, CW, OY, OX = 110, 120, 84, 60
    c = np.zeros((CH, CW), np.uint8); o = fp - B
    if not B < fp < B + len(rom): return c
    for i in range(min(u(o), 64)):
        p = o + 8 + 12 * i; x, y, w, h = struct.unpack_from('<bbBB', rom, p); t = u(p + 8)
        img = goku_black.tiles(rom, t - B, w, h); at = struct.unpack_from('<H', rom, p + 6)[0]
        if at & 0x1000: img = img[:, ::-1]
        if at & 0x2000: img = img[::-1, :]
        for r in range(h):
            for k in range(w):
                R_, C = OY + y + r, OX + x + k
                if img[r, k] and 0 <= R_ < CH and 0 <= C < CW: c[R_, C] = img[r, k]
    return c
rows = []
for it in ITEMS:
    spec, cap = it.split('=', 1); path, labels = spec.split(':', 1)
    steps = json.load(open(path)); fps = []; rp = rom_for(path)
    for lab in labels.split('+'):
        for l, poses in steps:
            if l.startswith(lab):
                for q in poses:
                    if q[4] and (not fps or fps[-1] != (rp, q[4])): fps.append((rp, q[4]))
                break
    rows.append((cap, fps))
cache = {}
for _, fps in rows:
    for rp, fp in fps:
        if (rp, fp) not in cache:
            if rp not in ROMS: ROMS[rp] = open(rp, 'rb').read()
            rom = ROMS[rp]; cache[(rp, fp)] = frame_px(fp)
m = np.zeros((110, 120), bool)
for c in cache.values(): m |= c > 0
ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
Z = 3; cw, ch = (x1 - x0) * Z, (y1 - y0) * Z; PER = 11
nrow = sum((len(f) + PER - 1) // PER or 1 for _, f in rows)
W = 12 + PER * (cw + 6); H = 50 + len(rows) * 30 + nrow * (ch + 6)
im = Image.new('RGB', (W, H), (26, 26, 30)); d = ImageDraw.Draw(im)
d.text((12, 10), TITLE, fill=(255, 214, 102), font=F1); y = 46
for cap, fps in rows:
    d.text((12, y), cap, fill=(235, 235, 235), font=F2); y += 28
    for i, fp in enumerate(fps):
        if i and i % PER == 0: y += ch + 6
        a = cache[fp][y0:y1, x0:x1]; c = pal[a].copy(); c[a == 0] = (92, 140, 96)      # fp is (rom, pointer)
        im.paste(Image.fromarray(np.kron(c, np.ones((Z, Z, 1), np.uint8))), (12 + (i % PER) * (cw + 6), y))
    y += ch + 8
im.crop((0, 0, W, y + 4)).save(OUT); print(OUT, (W, y + 4))
