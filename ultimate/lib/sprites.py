"""Insert new sprite animations into Buu's Fury (format in RE_NOTES "Actors and animations").

Animation = u32 frame_count, then frame_count x 4 frame pointers (dir 0 down, 1 up, 2 side, 3 = side mirrored).
Frame = u32 piece_count, pieces of 16 bytes: [s8 x, s8 y, u8 w, u8 h][same 4 bytes][u32 OAM attr0|attr1<<16][u32 tile ptr].
Pieces are placed relative to the actor origin, which sits 8 px right of the piece's left edge for a 16-wide sprite and
8 px above its bottom (x = 8 - w/2 for a centred piece, y = 8 - h). Dir 3 mirrors dir 2: x3 = 16 - w - x2, attr1 |= 0x1000.
Tiles are stored uncompressed (WFZ type 0), 8bpp, 1D mapping order; colours are OBJ palette indices.
"""
import struct
import sys
import numpy as np

SHAPE = {(8, 8): (0, 0), (16, 16): (0, 1), (32, 32): (0, 2), (64, 64): (0, 3), (16, 8): (1, 0), (32, 8): (1, 1),
         (32, 16): (1, 2), (64, 32): (1, 3), (8, 16): (2, 0), (8, 32): (2, 1), (16, 32): (2, 2), (32, 64): (2, 3)}
BASE = 0x08000000


def tiles_8bpp(idx):
    h, w = idx.shape
    out = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            out += idx[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].astype(np.uint8).tobytes()
    return bytes(out)


_WFZ = {}
def wfz_cache():
    if 'c' not in _WFZ:
        import os, pickle
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'out', 'wfz_cache.pkl')
        try: _WFZ['c'] = pickle.load(open(path, 'rb'))
        except Exception: _WFZ['c'] = {}
        _WFZ['path'] = path
    return _WFZ['c']


def wfz_cache_save():
    import os, pickle
    c = _WFZ.get('c')
    if c and c.pop('_dirty', False):
        os.makedirs(os.path.dirname(_WFZ['path']), exist_ok=True); pickle.dump(c, open(_WFZ['path'], 'wb'))


class Inserter:
    def __init__(self, rom, at):
        self.rom, self.cur = rom, at

    def put(self, data):
        if getattr(self, 'high_on', False):           # an actor marked high: the area above 16 MB (32 MB builds)
            a = self.hcur; self.rom[a:a + len(data)] = data; self.hcur = (a + len(data) + 3) & ~3
            return BASE + a
        a = self.cur; self.rom[a:a + len(data)] = data; self.cur = (a + len(data) + 3) & ~3
        return BASE + a

    def tiles(self, raw):
        """A tile block (8bpp tiles) -> pointer: stored (WFZ type 0), or with self.compress WFZ type 1 like BF's own
        frames (the game's tile loader 0x0803D96E decodes both), identical blocks once (wfz.compress from Gero's tools).
        Compressed blocks are cached in ultimate/out/wfz_cache.pkl: the encoder is slow."""
        raw = bytes(raw)
        if not getattr(self, 'compress', False): return self.put(struct.pack('<II', 0, len(raw)) + raw)
        seen = self.__dict__.setdefault('_tiles', {})
        if raw not in seen:
            cache = wfz_cache()
            if raw not in cache:
                import wfz
                cache[raw] = wfz.container(raw); cache['_dirty'] = True
            seen[raw] = self.put(cache[raw])
        return seen[raw]

    def piece(self, img, mirror=False, dx=0, dy=0):
        """img: h x w index array (an OBJ size). Returns the 16-byte piece."""
        h, w = img.shape
        sh, sz = SHAPE[(w, h)]
        tile = self.tiles(tiles_8bpp(img))
        x = 8 - w // 2 + dx; y = 8 - h + dy
        a1 = (sz << 14)
        if mirror: x = 16 - w - x; a1 |= 0x1000
        a0 = (sh << 14) | 0x2000                       # 8bpp
        box = struct.pack('<bbBB', x, y, w, h)
        return box + box + struct.pack('<HHI', a0, a1, tile), tile

    def frame(self, img, mirror=False):
        """Crop the cell to its art and cover it with as few/small OBJ pieces as possible (VRAM budget per frame).
        The cell's bottom-centre stays the actor origin. Identical frames are written once (frame cache)."""
        key = (img.shape, img.tobytes(), mirror, getattr(self, 'oy', 0))
        cache = self.__dict__.setdefault('_frames', {})
        if key not in cache: cache[key] = self._frame(img, mirror)
        return cache[key]

    def _frame(self, img, mirror=False):
        ch, cw = img.shape
        ys, xs = np.nonzero(img)
        if not len(ys): ys, xs = np.array([ch - 1]), np.array([cw // 2])
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        pieces = cover(x1 - x0, y1 - y0)
        # the engine draws ONE piece per character frame and reserves 1 KB of VRAM (32x32 8bpp) for it: anything
        # bigger is cut off or overwrites the next actor's tiles, so refuse it here instead of shipping a clipped sprite
        assert pieces and len(pieces) == 1 and pieces[0][2] * pieces[0][3] <= getattr(self, 'frame_limit', 1024) and \
            pieces[0][2] >= x1 - x0 and pieces[0][3] >= y1 - y0, \
            'sprite frame %dx%d does not fit one 32x32 piece (art must be shrunk to fit, see artclean.place_in_cell)' \
            % (x1 - x0, y1 - y0)
        out = []
        for (px, py, w, h) in pieces:
            sub = np.zeros((h, w), np.uint8)
            part = img[y0 + py:min(y1, y0 + py + h), x0 + px:min(x1, x0 + px + w)]
            sub[:part.shape[0], :part.shape[1]] = part
            # offsets relative to the 16-wide/8-below origin convention, measured from the cell's bottom centre
            dx = (x0 + px) - (cw // 2 - 8) - (8 - w // 2)
            dy = (y0 + py) - (ch - 8) - (8 - h) + getattr(self, 'oy', 0)   # oy: cell bottom below origin+8
            pc, _ = self.piece(sub, mirror, dx, dy)
            if mirror:                                   # mirror the whole layout, not just each piece
                x = 16 - w - ((x0 + px) - (cw // 2 - 8))
                pc = struct.pack('<bbBB', x, pc[1] if pc[1] < 128 else pc[1] - 256, w, h) * 2 + pc[8:]
            out.append(pc)
        self.budget_max = max(getattr(self, 'budget_max', 0), sum(w * h for _, _, w, h in pieces))
        return self.put(struct.pack('<I', len(out)) + b''.join(out))

    def anim(self, frames_by_dir):
        """frames_by_dir: [down_frames, up_frames, side_frames] (lists of index arrays, same length)."""
        n = len(frames_by_dir[0])
        ptrs = []
        for k in range(n):
            d, u, s = frames_by_dir[0][k], frames_by_dir[1][k], frames_by_dir[2][k]
            ptrs += [self.frame(d), self.frame(u), self.frame(s), self.frame(s, mirror=True)]
        return self.put(struct.pack('<I', n) + struct.pack('<%dI' % len(ptrs), *ptrs))


def cover(w, h, multi=False):
    """Smallest OBJ shape covering a w x h box. Character/NPC actors only ever use ONE piece per frame (no BF
    class 2/4 frame has more, and a second piece is not drawn), so multi-piece layouts are opt-in."""
    best = None
    for (W, H) in SHAPE:
        if W >= w and H >= h and (best is None or W * H < best[0]): best = (W * H, [(0, 0, W, H)])
    if not multi and best: return best[1]
    for split in ('v', 'h'):
        for (W1, H1) in SHAPE:
            for (W2, H2) in SHAPE:
                if split == 'v' and W1 >= w and W2 >= w and H1 + H2 >= h and H1 < h:
                    cand = (W1 * H1 + W2 * H2, [(0, 0, W1, H1), (0, H1, W2, H2)])
                elif split == 'h' and H1 >= h and H2 >= h and W1 + W2 >= w and W1 < w:
                    cand = (W1 * H1 + W2 * H2, [(0, 0, W1, H1), (W1, 0, W2, H2)])
                else: continue
                if best is None or cand[0] < best[0]: best = cand
    return best[1]


def grow_box(img, fbox, sx, sy):
    """From Gero's Legacy (Super 17): scale a LoG2 frame about the feet with nearest-neighbour sampling. img (h x w) is drawn at box (x, y) from the
    object's anchor, whose feet point is (8, 8). Returns (image, (x, y, w, h)) of one OBJ shape covering the result; a wide pose grows less so it stays one 32-wide piece."""
    x, y = fbox[0], fbox[1]
    ys_, xs_ = np.nonzero(img)
    if not len(ys_): return img, fbox
    X0, X1 = x + xs_.min(), x + xs_.max() + 1; Y0, Y1 = y + ys_.min(), y + ys_.max() + 1
    sx = min(sx, 31.5 / (2 * max(8 - X0, X1 - 8, 1)))
    nx0, nx1 = int(np.floor(8 + (X0 - 8) * sx)), int(np.ceil(8 + (X1 - 8) * sx))
    ny0, ny1 = int(np.floor(8 + (Y0 - 8) * sy)), int(np.ceil(8 + (Y1 - 8) * sy))
    (W, H), = [(p[2], p[3]) for p in cover(nx1 - nx0, ny1 - ny0)]
    ox, oy = nx0 - (W - (nx1 - nx0)) // 2, ny1 - H              # keep the feet: pad above and on both sides
    gy = np.floor(8 + (oy + np.arange(H) + 0.5 - 8) / sy).astype(int) - y
    gx = np.floor(8 + (ox + np.arange(W) + 0.5 - 8) / sx).astype(int) - x
    out = np.zeros((H, W), img.dtype)
    vy, vx = (gy >= 0) & (gy < img.shape[0]), (gx >= 0) & (gx < img.shape[1])
    out[np.ix_(vy, vx)] = img[np.ix_(gy[vy], gx[vx])]
    return out, (ox, oy, W, H)


def set_slot(rom, actor_id, slot, anim_ptr, actor_list=0x6B6BD8):
    p = struct.unpack_from('<I', rom, actor_list + 4 * actor_id)[0] - BASE
    n = struct.unpack_from('<I', rom, p)[0] & 0xFF
    assert slot < n
    struct.pack_into('<I', rom, p + 0x54 + 4 * slot, anim_ptr)


# ---------- actor table relocation + new actors ----------
ACTOR_LIST, ACTOR_COUNT = 0x6B6BD8, 298
ACTOR_LITERALS = (0x3C0, 0x1715C)        # both hold list+4; code reads [lit + 4*idx - 0x28] (game idx = actor id + 10)


def sheet_frames(clean_dir, sid):
    import os
    from PIL import Image
    out = []; n = 0
    while os.path.exists(os.path.join(clean_dir, '%s_%02d.png' % (sid, n))):
        out.append(np.array(Image.open(os.path.join(clean_dir, '%s_%02d.png' % (sid, n))))); n += 1
    return out


def by_direction(frames, mode=None):
    """Sheets are ordered DOWN frames, UP frames, RIGHT frames (equal thirds). A sheet that isn't a multiple of 3 is
    treated as single-view and reused for every direction; mode 'side' / 'front' forces that (e.g. a 3-frame side-only KO)."""
    if mode is None and len(frames) % 3 == 0 and frames:
        k = len(frames) // 3; return [frames[:k], frames[k:2 * k], frames[2 * k:]]
    return [frames, frames, frames]


def slot_frames(clean_dir, spec):
    """Slot spec: 'SHEET', 'SHEET@a:b' (frames a..b-1 of each direction), with an optional '!side' / '!front' suffix
    for single-view sheets. Returns [down, up, side] frame lists or None."""
    mode = None
    if '!' in spec: spec, mode = spec.split('!')
    raw = None                                     # 'SHEET#a:b' = frames a..b-1 of the sheet itself, before the split
    if '#' in spec:
        spec, r = spec.split('#'); a_, b_ = r.split(':'); raw = slice(int(a_), int(b_))
    sl = None
    if '@' in spec:
        spec, r = spec.split('@'); a, b = r.split(':'); sl = slice(int(a), int(b))
    fr = sheet_frames(clean_dir, spec)
    if raw: fr = fr[raw]
    if not fr: return None
    dirs = by_direction(fr, mode)
    return [d[sl] for d in dirs] if sl else dirs


# Slots whose frames a skill picks by number rather than plays in order: the Kamehameha holds frame 0 of slot 18 (the charge, hands at the hip) and
# then shows frames 1 and 2 in turn while the beam is out (test_moves.fire(watch=True) logged 18:0 x12, then 18:2 / 18:1 alternating). Spreading a
# 3-frame slot over 6 ([0,0,1,1,2,2]) made frame 1 the charge again, so every GT fighter dropped back into the charge pose every few frames while
# firing (Nov 9, the owner on Majuub: "the head is way too far back in that one side view"). Made longer, these keep every frame at its own
# number and repeat the last one.
INDEXED = {18, 19}      # skills pick these frames by number: slot 18 the pose held while firing, 19 the charged ball's and Final Flash's (Nov 10:
                        # Blue Gogeta's four were spread over ten, so his skill 5 never reached the arm out)


def longer(k, n, slot=None, indexed=False):
    """Frame indices that make a k-frame animation n frames long: spread evenly, or for an INDEXED slot (or one a figure's 'indexed' names) each
    in place and then the last."""
    return [min(i, k - 1) if indexed or slot in INDEXED else i * k // n for i in range(n)]


def stretch(dirs, n, slot=None, indexed=False):
    """Repeat frames so each direction has n frames (the replaced slot's own count: fight code may time hits and effects by frame index)."""
    if not n or len(dirs[0]) >= n: return dirs
    idx = longer(len(dirs[0]), n, slot, indexed)
    return [[d[i] for i in idx] for d in dirs]


HIGH_END = None


def build_actors(rom, cfg, clean_dir, at, l2=None, colour_ctx=None, proto=None, high=None):
    """cfg: {name: {"template": actor id, "slots": {slot: sheet id}}}. Moves the actor table to `at`, appends one
    actor per entry (record cloned from the template, animation slots replaced), returns ({name: actor id}, end)."""
    ins = Inserter(rom, at + 4 * (ACTOR_COUNT + len(cfg)) + 16)
    ins.hcur = high                                        # start of the high area, or None: everything goes low
    table = list(struct.unpack_from('<%dI' % ACTOR_COUNT, rom, ACTOR_LIST))
    ids = {}; anims = {}
    for name, a in cfg.items():
        if name.startswith('_'): continue
        ins.compress = a.get('compress', False)            # WFZ-compressed tile blocks (only the actors that ask)
        ins.high_on = bool(a.get('high')) and high is not None
        target = a.get('replace')                          # modify an existing actor instead of adding one
        if 'hairswap' in a:                                # an outfit's Super Saiyan: its base's frames with another outfit's gold hair (hairswap_actor)
            h = a['hairswap']; at_ = lambda x: table[x] - BASE
            rec, made, kept = hairswap_actor(ins, rom, at_(h['base']), at_(h['ref']), at_(h['ss']), {int(k): tuple(v) for k, v in h.get('slots', {}).items()}, h.get('idle_slots', ()))
            print('%s: %d frames made, %d left as the source Super Saiyan\'s' % (name, made, kept))
            if kept > h.get('kept_max', 0): sys.exit('%s: %d frames could not be matched (allowed %d)' % (name, kept, h.get('kept_max', 0)))
            ids[name] = len(table); table.append(ins.put(bytes(rec)))
            continue
        if 'blue_hair' in a:                               # a Super Saiyan figure with blue hair (blue_hair_actor): its base and Super Saiyan built first
            h = a['blue_hair']; at_ = lambda x: (table[x] if isinstance(x, int) else table[ids[x]]) - BASE
            rec, made = blue_hair_actor(ins, rom, at_(h['base']), at_(h['ss']), {'shared': set(h['shared'])}, {int(k): v for k, v in h['to'].items()}, h.get('transplant'))
            print('%s: %d frames with blue hair%s' % (name, made, ' (recoloured by the transplant)' if h.get('transplant') else ''))
            ids[name] = len(table); table.append(ins.put(bytes(rec)))
            continue
        if 'same_as' in a:                                 # another actor id for the same record (Super Saiyan 2 and Full Power: their lightning
            src = a['same_as']                             # is the crackle drawn around the fighter, outfit.c crackle, not part of the frames)
            ids[name] = len(table); table.append(table[src] if isinstance(src, int) else table[ids[src]])
            continue
        if 'roshi_of' in a:                                # Master Roshi: Krillin's frames (built first) with Roshi's head and clothes (lib/roshi.py)
            import roshi, headswap
            src = table[ids[a['roshi_of']]]; srec = src - BASE
            stand = struct.unpack_from('<I', rom, srec + 0x54)[0] - BASE
            kst = {v: frame_image(rom, struct.unpack_from('<I', rom, stand + 4 + 4 * v)[0]) for v in (0, 1, 2)}
            rst = {v: headswap.bf_stand(rom, ACTOR_LIST, a['head_of'], v) for v in (0, 1, 2)}
            conv = roshi.Roshi(kst, rst, a['chin'][0], a['chin'][1])
            rec = viewed_actor(ins, rom, srec, conv.apply); ids[name] = len(table); table.append(ins.put(bytes(rec)))
            print('%s: heads placed %d, missed %d, clothes %d' % (name, conv.hits, conv.misses, conv.dressed))
            continue
        if 'beerus_of' in a:                               # Beerus: Kid Buu's frames with Beerus's head, collar and clothes (lib/beerus.py)
            import beerus
            src = table[a['beerus_of']]; srec = src - BASE
            stand = struct.unpack_from('<I', rom, srec + 0x54)[0]
            kst = {v: frame_image(rom, struct.unpack_from('<I', rom, stand - BASE + 4 + 4 * v)[0]) for v in (0, 1, 2)}
            tall = tuple(a.get('tall', (0, 0)))
            conv = beerus.Beerus(kst, a['one'], side=beerus.HEAD_SIDE_NEW if a.get('side') == 'new' else None, tall=tall)
            rec = composed_actor(ins, rom, srec, conv.frame if any(tall) else conv.apply, {int(k): v for k, v in a.get('remap', {}).items()})
            ids[name] = len(table); table.append(ins.put(bytes(rec)))
            print('%s: heads placed %d (%d by hand), missed %d%s' % (name, conv.hits, conv.manual, conv.misses,
                  '; %d leg and %d torso seams, %d not made; %d bytes of sprite memory a frame' % (conv.seams['leg'], conv.seams['torso'], conv.seams['not made'], struct.unpack_from('<H', rec, 2)[0]) if any(tall) else ''))
            if conv.misses: sys.exit('%s: Kid Buu\'s head not found in %d frames (add them to beerus.MANUAL)' % (name, conv.misses))
            continue
        if 'tint_of' in a:                                 # a recoloured copy of an actor (built first): Kaioken's red
            src = a['tint_of']; src = table[src] if isinstance(src, int) else table[ids[src]]
            rec = (viewed_actor if a.get('by_view') else tinted_actor)(ins, rom, src - BASE, a['tint'])     # by_view: the tint sees the view
            if 'change' in a: change_slot(ins, rom, rec, a['change'], table[a['change']['actor']] if isinstance(a['change']['actor'], int) else table[ids[a['change']['actor']]])
            for slot, frm in a.get('fill', {}).items():    # a slot the copy's behaviour may play that its figure never had: another of its own
                if int(slot) < rec[0] and not struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]:
                    struct.pack_into('<I', rec, 0x54 + 4 * int(slot), struct.unpack_from('<I', rec, 0x54 + 4 * frm)[0])
            ids[name] = len(table); table.append(ins.put(bytes(rec)))
            continue
        if 'proto_actor' in a:                             # whole actor copied from the Prototype D cart
            if proto is None: continue
            rec = proto_actor(ins, proto, a['proto_actor']); n = rec[0]
            for slot, src in a.get('fill', {}).items():    # the prototype never played these on a boss; a playable form does
                if not struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]:
                    struct.pack_into('<I', rec, 0x54 + 4 * int(slot), struct.unpack_from('<I', rec, 0x54 + 4 * src)[0])
        else:
            if 'template_orig' in a:                       # BF's own record, even if that actor was replaced above
                tp = struct.unpack_from('<I', rom, ACTOR_LIST + 4 * a['template_orig'])[0] - BASE
            else:
                tp = table[target if target is not None else a['template']] - BASE
            flags = struct.unpack_from('<I', rom, tp)[0]; n = flags & 0xFF
            rec = bytearray(rom[tp:tp + 0x54 + 4 * n])
        if 'extra_slots' in a:                             # Ultimate: grow the record for animations past the 22 slots
            total = 22 + len(a['extra_slots'])
            rec = bytearray(rec[:0x54 + 4 * min(n, 22)]) + bytes(4 * (total - min(n, 22)))
            struct.pack_into('<I', rec, 0, (struct.unpack_from('<I', rec, 0)[0] & ~0xFF) | total)
            n = total
        if a.get('reserve'): struct.pack_into('<H', rec, 2, a['reserve'])     # OBJ memory per frame (retail characters 1 KB)
        if not a.get('halo'):                              # record +0x50 = per-slot halo/attachment table (Other World)
            struct.pack_into('<I', rec, 0x50, 0)
        if 'log2_record' in a and l2 is not None:          # animations taken from a LoG2 actor
            usable, pal_rgb = colour_ctx(a.get('act'))
            cmap = log2_colour_map(l2, usable, pal_rgb); cache = {}
            edit = None; post = None
            if a.get('head_of') is not None:               # another character's head on these frames: lib/headswap.py
                import headswap
                src = log2_rec(l2, a['log2_record'])
                hs = headswap.HeadSwap({v: cmap[headswap.l2_stand(l2, src, v)] for v in (0, 1, 2)}, {v: headswap.bf_stand(rom, ACTOR_LIST, a['head_of'], v) for v in (0, 1, 2)}, {int(k): v for k, v in a['head_shift'].items()}, pal_rgb)
                post = hs.apply
            if a.get('log2_edit'):                         # {"onearm": [mode per direction], "ssj": bool, "skip": [anims]}
                import onearm                              # applies to the actor's own log2_record only
                ed = a['log2_edit']; modes, skip, ssj = ed.get('onearm'), ed.get('skip', []), ed.get('ssj')
                def edit(r, k, d, img, base=log2_rec(l2, a['log2_record'])):
                    if r != base: return None, img
                    m = 'none' if (k in skip or not modes) else modes[d]
                    key = (m, ssj)
                    if img is not None:
                        img = onearm.remove_arm(img, m)
                        if ssj: img = onearm.ssj_hair(img)
                    return key, img
            for slot, k in {**a.get('log2_slots', {}), **a.get('log2_overrides', {}), **a.get('extra_slots', {})}.items():
                if int(slot) >= n: continue                # the template has fewer slots (e.g. Goku 106 has 16)
                old = struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]
                want = struct.unpack_from('<I', rom, old - BASE)[0] if a.get('stretch') and old else 0
                src = a['log2_record']
                if str(k).startswith('r'): src, k = str(k).split(':', 1)    # "r51:3@0:2" = LoG2 actor 51, anim 3
                k, sl = (str(k).split('@') + [None])[:2]
                sl = ([int(v) for v in sl.split(',')] if ',' in sl else slice(*map(int, sl.split(':')))) if sl else None   # a..b or an exact list of frames
                ptr = log2_anim(ins, l2, log2_rec(l2, src), int(k), cmap, cache, want, sl, edit, a.get('log2_scale', {}).get(str(src)), a.get('size_scale'), a.get('reserve', 1024), post, a.get('log2_source'))
                if ptr: struct.pack_into('<I', rec, 0x54 + 4 * int(slot), ptr)
        ins.frame_limit = 4096 if a.get('big') else 1024   # boss-class actors may use one 64x64 piece
        if 'raw_frames' in a:                              # frames given as arrays of BF OBJ indices (tools/doors.py:
            ins.oy = a.get('origin_dy', 0)                 # map door regions already draw with the BF OBJ palette)
            for slot, dirs in a['raw_frames'].items():
                if int(slot) >= n: continue
                struct.pack_into('<I', rec, 0x54 + 4 * int(slot), ins.anim(dirs))
            ins.oy = 0
        for d, box in a.get('boxes', {}).items():          # per-direction (x, y, w, h) box override
            struct.pack_into('<4i', rec, 0x14 + 16 * int(d), *box)
        ins.oy = a.get('origin_dy', 0)                     # sheet frames drawn lower than the cell's bottom (Broly Full Power: see build.py)
        for slot, spec in a.get('slots', {}).items():
            if int(slot) >= n: continue                    # the template has fewer slots
            old = struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]
            want = struct.unpack_from('<I', rom, old - BASE)[0] if (target is not None or a.get('stretch')) and old else 0
            ix = int(slot) in INDEXED or int(slot) in a.get('indexed', ())
            key = (spec, want, ix, ins.oy)
            if key not in anims:
                dirs = slot_frames(clean_dir, spec)
                anims[key] = ins.anim(stretch(dirs, want, int(slot), ix)) if dirs else None
            if anims[key]: struct.pack_into('<I', rec, 0x54 + 4 * int(slot), anims[key])
        ins.oy = 0
        if 'proto_actor' not in a:
            for slot, src in a.get('fill', {}).items():    # a retail actor that never played these: its own frames stand in, as on the prototype's bosses
                if int(slot) < rec[0] and not struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]:
                    struct.pack_into('<I', rec, 0x54 + 4 * int(slot), struct.unpack_from('<I', rec, 0x54 + 4 * src)[0])
        for slot, want in a.get('grow', {}).items():       # a playable form's animations must be at least as long as a retail player's
            if int(slot) >= n: continue
            ap = struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]
            if not ap: continue
            k = struct.unpack_from('<I', rom, ap - BASE)[0]
            if k >= want: continue
            old = struct.unpack_from('<%dI' % (4 * k), rom, ap - BASE + 4)
            idx = ([min(i, k - 1) for i in range(want)] if int(slot) in a.get('indexed', ())        # 'indexed': as INDEXED, this figure only
                   else [i * k // want for i in range(want)] if int(slot) in a.get('even', ())     # 'even': spread out even in an INDEXED slot
                   else longer(k, want, int(slot)))
            grown = [old[j * 4 + d] for j in idx for d in range(4)]
            struct.pack_into('<I', rec, 0x54 + 4 * int(slot), ins.put(struct.pack('<I', want) + struct.pack('<%dI' % len(grown), *grown)))
        for slot, idx in a.get('reframe', {}).items():   # an animation's own frames in another order (frame numbers past its end: its last)
            ap = struct.unpack_from('<I', rec, 0x54 + 4 * int(slot))[0]
            if int(slot) >= n or not ap: continue
            k = struct.unpack_from('<I', rom, ap - BASE)[0]; old = struct.unpack_from('<%dI' % (4 * k), rom, ap - BASE + 4)
            seq = [old[min(j, k - 1) * 4 + d] for j in idx for d in range(4)]
            struct.pack_into('<I', rec, 0x54 + 4 * int(slot), ins.put(struct.pack('<I', len(idx)) + struct.pack('<%dI' % len(seq), *seq)))
        if a.get('stance_back'):                           # slot 11 is the change back: an animation as long as a retail one takes four seconds, the stance one
            struct.pack_into('<I', rec, 0x54 + 44, struct.unpack_from('<I', rec, 0x54)[0])
        if target is not None:
            table[target] = ins.put(bytes(rec)); ids[name] = target
        else:
            ids[name] = len(table); table.append(ins.put(bytes(rec)))
    # Transforming plays slot 10, and an empty one draws junk from address 0 over other sprites' tiles. Gohan's orange gi (actor 101) never transformed in the original; here it does.
    # Going from Super Saiyan to Super Saiyan 2 plays the power-up on the Super Saiyan actor, and most have no slot 10 (Goku's does): 11 frames of their own ki pose, as long as a retail power-up.
    ins.high_on = False
    # The frames: his own power-up (slot 13: the crouch, then arms up), front view in every view, ending on his stance, as GT Vegeta's change
    # (approved Nov 10). They were his slot 21 or 9, so these figures powered up with punches, kicks, being hit, or Gohan's green gi turning
    # to stone (Nov 10, the owner: "ssj2 he punches while transforming").
    for key in [*cfg.get('_powerup', ()), *cfg.get('_powerup_still', ())]:
        still = key in cfg.get('_powerup_still', ())     # the crouch all through, no arms up (Full Power Mystic's: the owner, Nov 12)
        at_ = key if isinstance(key, int) else ids[key]
        o = table[at_] - BASE; n = struct.unpack_from('<I', rom, o)[0] & 0xFF; rec = bytearray(rom[o:o + 0x54 + 4 * n])
        up, stand = (struct.unpack_from('<I', rec, 0x54 + 4 * s)[0] for s in (13, 0))
        if not up or struct.unpack_from('<I', rom, up - BASE)[0] < 2: sys.exit('_powerup %s: no two-frame power-up (slot 13)' % key)
        front = lambda ap, k: struct.unpack_from('<I', rom, ap - BASE + 4 + 16 * k)[0]
        seq = [front(up, 0)] * (10 if still else 2) + ([] if still else [front(up, 1)] * 8) + [front(stand, 0)]
        struct.pack_into('<I', rec, 0x54 + 40, ins.put(struct.pack('<I', 11) + struct.pack('<44I', *[f for f in seq for d in range(4)])))
        table[at_] = ins.put(bytes(rec))
    # A same_as actor took its source's record as it was when it was made: point it at the record the source ends up with (_powerup above
    # makes a new one), or armour Gohan's Super Saiyan 2 kept the template's power-down (retail green-gi Gohan) after his own had changed.
    for name, a in cfg.items():
        if isinstance(a, dict) and 'same_as' in a and name not in cfg.get('_powerup', ()) and name not in cfg.get('_powerup_still', ()):      # (one with a power-up of its own keeps it: Full Power)
            src = a['same_as']
            table[ids[name]] = table[src] if isinstance(src, int) else table[ids[src]]
    # Actors drawn with no ground shadow (cfg '_no_shadow': ids or names). Record bytes +0xA/+0xB are the shadow's size, looked up when the
    # object is made (sub_08013E38 in 0x086B759C: 4x2, 10x4, 16x6, 24x10); a size not in the table gives none, and the draw (sub_0800EF94)
    # skips the piece. The record is copied, so nothing else changes.
    for key in cfg.get('_no_shadow', ()):
        at_ = key if isinstance(key, int) else ids[key]
        o = table[at_] - BASE; n = struct.unpack_from('<I', rom, o)[0] & 0xFF; rec = bytearray(rom[o:o + 0x54 + 4 * n])
        rec[0xA] = rec[0xB] = 0
        table[at_] = ins.put(bytes(rec))
    rom[at:at + 4 * len(table)] = struct.pack('<%dI' % len(table), *table)
    for lit in ACTOR_LITERALS:
        struct.pack_into('<I', rom, lit, BASE + at + 4)
    ins.compress = ins.high_on = False
    wfz_cache_save()
    global HIGH_END
    HIGH_END = ins.hcur
    return ids, ins.cur


# ---------- LoG2 actors ----------
L2_BASE, L2_PAL = 0x08800000, 0x3ECD1C
L2_ACTORS = 0x3B4F30             # LoG2 actor list (154 records)


def log2_rec(l2, ref):
    """A LoG2 actor record: "0x..." = slice offset of the record, "rN" = entry N of the actor list."""
    if str(ref).startswith('r'): return struct.unpack_from('<I', l2, L2_ACTORS + 4 * int(str(ref)[1:]))[0] - L2_BASE
    return int(ref, 16)


def log2_colour_map(l2, usable, pal_rgb):
    """LoG2 OBJ index -> BF OBJ index (CIE94 nearest among `usable`)."""
    import artclean as A
    pl = np.frombuffer(l2[L2_PAL + 768:L2_PAL + 1536], np.uint8).reshape(256, 3).astype(np.int64)
    ul = A.srgb_to_lab(pal_rgb[usable])
    m = np.array(usable)[A.de94(A.srgb_to_lab(pl)[:, None], ul[None]).argmin(1)]
    m[0] = 0
    return m.astype(np.uint8)


def log2_anim(ins, l2, rec, k, cmap, cache, want=0, sl=None, edit=None, scale=None, grow=None, limit=1024, post=None, source=None):
    """Convert LoG2 animation k of the actor record at slice offset `rec` into a BF animation. Returns ptr or 0.
    sl = frames a..b-1 only (a slice with a step, e.g. 3:-5:-1, plays them backwards); want = repeat frames evenly to
    that count (the replaced BF slot's own frame count). edit(k, d, pixels) -> (key, pixels): optional pixel edit of each
    frame (LoG2 colour indices, h x w) before conversion, e.g. tools/onearm.py. scale: shrink each frame by this factor
    (majority vote per block) and fit it into one 32x32 piece (big LoG2 actors such as Cell are 64x64; BF characters
    get 1 KB of OBJ VRAM per frame). source(rec, k, d, f) -> (32x32 LoG2 colour indices as shown, (x, y, 32, 32) as
    shown) or None: a frame made elsewhere (teen.py's Teen Gohan) in place of the record's own, in the place and with
    the flips of the record's entry for that view (a mirrored entry stores its pixels turned back; the box is where the
    frame is shown, as the game stores a mirrored frame's)."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', l2, o)[0]
    dirs = [u(rec + 0x4C + 16 * k + 4 * d) for d in range(4)]
    if not any(dirs): return 0
    us = sorted(set(x for x in dirs if x)); gaps = [b - a for a, b in zip(us, us[1:])]
    n = min(gaps) // 12 if gaps else 1          # directions are consecutive runs; some share one run (e.g. a KO)
    if not gaps:                                # one run for every direction: count frames until the next record
        n = 1
        while n < 12:
            r = us[0] - L2_BASE + 12 * n; x, y, w, h = struct.unpack_from('<bbBB', l2, r)
            tp = u(r + 8)
            if not (w and h and w * h <= 4096 and L2_BASE <= tp < L2_BASE + len(l2)): break
            n += 1
    idx = sl if isinstance(sl, list) else list(range(n))[sl] if sl else list(range(n))
    if want and len(idx) < want: idx = [idx[i * len(idx) // want] for i in range(want)]
    ptrs = []
    for f in idx:
        for d in range(4):
            r = (dirs[d] or dirs[2] or us[0]) - L2_BASE + 12 * f
            x, y, w, h = struct.unpack_from('<bbBB', l2, r)
            attr, tp = struct.unpack_from('<II', l2, r + 4)
            assert scale or w * h <= limit, 'LoG2 frame %dx%d at %x is over the 1 KB one-piece budget' % (w, h, r)
            got = source(rec, k, d, f) if source else None
            if got is not None:                          # a frame made elsewhere: one 32x32 8bpp piece
                img, fbox = got
                img = np.asarray(img, np.uint8)
                if img.shape != (32, 32) or tuple(fbox[2:]) != (32, 32): raise ValueError('log2_anim source: not one 32x32 piece')
                if attr & 0x10000000: img = img[:, ::-1]      # shown mirrored: stored turned back
                data = cmap[img].reshape(4, 8, 4, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
                key = ('source', data, tuple(fbox))
                if key not in cache: cache[key] = (cache.get(('source', data)) or ins.put(struct.pack('<II', 0, len(data)) + data), tuple(fbox))
                cache[('source', data)] = cache[key][0]
                tptr, fbox = cache[key]
                box = struct.pack('<bbBB', *fbox)
                ptrs.append(ins.put(struct.pack('<I', 1) + box + box + struct.pack('<II', (attr & 0x30000000) | 0x80002000, tptr)))
                continue
            ek = edit(rec, k, d, None)[0] if edit else None
            key = (tp, ek, scale, grow and tuple(grow))
            if key not in cache:
                o = tp - L2_BASE; t, size = struct.unpack_from('<II', l2, o)
                data = l2[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(l2, o + 8, size)[0])
                px = np.frombuffer(data, np.uint8).copy()
                img = px[:w * h].reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
                if ek is not None: img = edit(rec, k, d, img)[1]
                fbox = (x, y, w, h)
                if scale:
                    img, fbox = _shrink_fit(img, x, y, scale)
                bf = cmap[img]
                if post: bf = post(bf, None if len(set(dirs)) == 1 else min(d, 2))
                if grow: bf, fbox = grow_box(bf, fbox, *grow)
                hh, ww = bf.shape
                data = bf.reshape(hh // 8, 8, ww // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
                cache[key] = (ins.put(struct.pack('<II', 0, len(data)) + data), fbox)
            tptr, fbox = cache[key]
            if scale: attr = (attr & 0x30000000) | 0x80002000        # one 32x32 8bpp piece, keep the flip bits
            if grow:                                             # the grown piece's own OBJ shape and size
                sh, sz = SHAPE[(fbox[2], fbox[3])]
                attr = (attr & 0x30000000) | (sz << 30) | (sh << 14) | 0x2000
                assert fbox[2] * fbox[3] <= limit, 'grown frame over the actor budget'
            box = struct.pack('<bbBB', *fbox)
            ptrs.append(ins.put(struct.pack('<I', 1) + box + box + struct.pack('<II', attr, tptr)))
    return ins.put(struct.pack('<I', len(idx)) + struct.pack('<%dI' % len(ptrs), *ptrs))


def _shrink_fit(img, x, y, s):
    """Shrink a LoG2 frame (colour indices, 0 = clear) by factor s with a majority vote per source block, then cut the
    32x32 window around its content. Returns (32x32 image, (x, y, 32, 32) box relative to the origin)."""
    h, w = img.shape
    oh, ow = max(1, int(round(h * s))), max(1, int(round(w * s)))
    out = np.zeros((oh, ow), np.uint8)
    for j in range(oh):
        for i in range(ow):
            blk = img[int(j / s):max(int(j / s) + 1, int((j + 1) / s)), int(i / s):max(int(i / s) + 1, int((i + 1) / s))]
            v = blk[blk > 0]
            if len(v) * 2 >= blk.size:
                vals, cnt = np.unique(v, return_counts=True); out[j, i] = vals[cnt.argmax()]
    ox, oy = int(round(x * s)), int(round(y * s))              # the shrunk frame's top-left, relative to the origin
    ys, xs = np.nonzero(out)
    if not len(ys): return np.zeros((32, 32), np.uint8), (-16, -24, 32, 32)
    # 32x32 window: bottom-aligned to the feet, centred on the content
    y1 = ys.max() + 1; y0 = max(0, y1 - 32)
    cx = (xs.min() + xs.max() + 1) // 2; x0 = max(0, min(cx - 16, ow - 32)) if ow >= 32 else cx - 16
    win = np.zeros((32, 32), np.uint8)
    for j in range(32):
        for i in range(32):
            sy, sx = y0 + j, x0 + i
            if 0 <= sy < oh and 0 <= sx < ow: win[j, i] = out[sy, sx]
    return win, (ox + x0, oy + y0, 32, 32)


# ---------- Prototype D actors ----------
PROTO_ACTOR_LIST = 0x6A1BBC      # Prototype D (DBZ3_cart27): 280 actors, same record / animation / frame format as retail



def tinted_actor(ins, rom, rec_at, remap):
    """A copy of an actor with every frame's pixels through `remap`: 256 bytes (as bytes.translate; Kaioken's red), or a function of each
    piece as an index image (Super Saiyan Blue's hair). Tiles are stored raw."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    n = u(rec_at) & 0xFF; rec = bytearray(rom[rec_at:rec_at + 0x54 + 4 * n])
    done, frames, anims = {}, {}, {}
    def tile(tp, w, h):
        if tp not in done:
            o = tp - BASE; t, size = u(o), u(o + 4)
            raw = rom[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(rom, o + 8, size)[0])
            if callable(remap):                            # a function of the whole piece (tiles laid out as an image)
                img = np.frombuffer(bytes(raw[:w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
                data = np.asarray(remap(img), np.uint8).reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
            else:
                data = bytes(raw[:w * h]).translate(remap)
            done[tp] = ins.put(struct.pack('<II', 0, len(data)) + data)
        return done[tp]
    def frame(fp):
        if fp not in frames:
            o = fp - BASE; k = u(o); body = bytearray(rom[o:o + 4 + 16 * k])
            for j in range(k):
                w, h = body[4 + 16 * j + 2], body[4 + 16 * j + 3]
                struct.pack_into('<I', body, 4 + 16 * j + 12, tile(u(o + 4 + 16 * j + 12), w, h))
            frames[fp] = ins.put(bytes(body))
        return frames[fp]
    for s in range(n):
        ap = u(rec_at + 0x54 + 4 * s)
        if not ap: continue
        if ap not in anims:
            o = ap - BASE; k = u(o)
            ptrs = [frame(u(o + 4 + 4 * j)) if u(o + 4 + 4 * j) else 0 for j in range(4 * k)]
            anims[ap] = ins.put(struct.pack('<I', k) + struct.pack('<%dI' % len(ptrs), *ptrs))
        struct.pack_into('<I', rec, 0x54 + 4 * s, anims[ap])
    return rec


def change_slot(ins, rom, rec, ch, base_at):
    """Super Saiyan Blue's change (slot 10 of the record `rec`; Nov 12, the owner: "Gokus hair turns SSJ3 in the SSB transformation", and
    for Vegeta "do the normal pose"): the base figure's own change (`base_at`'s slot 10), its frames ch['seq'] (a number: that frame of the
    change, 'stance': the record's own stance) with each piece through ch['tint'](piece, the pixels of change frame ch['ref'] under it)."""
    import ssb
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    bap = u(base_at - BASE + 0x54 + 40) - BASE; sap = struct.unpack_from('<I', rec, 0x54)[0] - BASE
    made = {}
    def frame(fp, ref):
        if fp in made: return made[fp]
        unders = ssb.piece_unders(rom, fp, ref)
        k = u(fp); body = bytearray(rom[fp:fp + 4 + 16 * k])
        for j in range(k):
            w, h = body[4 + 16 * j + 2], body[4 + 16 * j + 3]; tp = u(fp + 4 + 16 * j + 12) - BASE
            t, size = u(tp), u(tp + 4)
            raw = rom[tp + 8:tp + 8 + size] if t == 0 else bytes(decompress_stream(rom, tp + 8, size)[0])
            img = np.frombuffer(bytes(raw[:w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
            data = np.asarray(ch['tint'](img, unders.get(j)), np.uint8).reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
            struct.pack_into('<I', body, 4 + 16 * j + 12, ins.put(struct.pack('<II', 0, len(data)) + data))
        made[fp] = ins.put(bytes(body))
        return made[fp]
    ptrs = []
    for f in ch['seq']:
        for d in range(4):
            if f == 'stance': ptrs.append(u(sap + 4 + 4 * d)); continue
            ptrs.append(frame(u(bap + 4 + 16 * f + 4 * d) - BASE, u(bap + 4 + 16 * ch['ref'] + 4 * d) - BASE))
    struct.pack_into('<I', rec, 0x54 + 40, ins.put(struct.pack('<I', len(ch['seq'])) + struct.pack('<%dI' % len(ptrs), *ptrs)))


def viewed_actor(ins, rom, rec_at, fn):
    """A copy of an actor with every frame's piece through fn(image, view): view 0 front, 1 back, 2 side (the mirrored side shares the
    side's tiles). Master Roshi's frames from Krillin's (lib/roshi.py). Tiles are stored raw."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    n = u(rec_at) & 0xFF; rec = bytearray(rom[rec_at:rec_at + 0x54 + 4 * n])
    done, frames, anims = {}, {}, {}
    def tile(tp, w, h, view):
        if (tp, view) not in done:
            o = tp - BASE; t, size = u(o), u(o + 4)
            raw = rom[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(rom, o + 8, size)[0])
            img = np.frombuffer(bytes(raw[:w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
            data = np.asarray(fn(img, view), np.uint8).reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
            done[tp, view] = ins.put(struct.pack('<II', 0, len(data)) + data)
        return done[tp, view]
    def frame(fp, view):
        if (fp, view) not in frames:
            o = fp - BASE; k = u(o); body = bytearray(rom[o:o + 4 + 16 * k])
            for j in range(k):
                w, h = body[4 + 16 * j + 2], body[4 + 16 * j + 3]
                struct.pack_into('<I', body, 4 + 16 * j + 12, tile(u(o + 4 + 16 * j + 12), w, h, view))
            frames[fp, view] = ins.put(bytes(body))
        return frames[fp, view]
    for s in range(n):
        ap = u(rec_at + 0x54 + 4 * s)
        if not ap: continue
        if ap not in anims:
            o = ap - BASE; k = u(o)
            ptrs = [frame(u(o + 4 + 4 * j), min(j % 4, 2)) if u(o + 4 + 4 * j) else 0 for j in range(4 * k)]
            anims[ap] = ins.put(struct.pack('<I', k) + struct.pack('<%dI' % len(ptrs), *ptrs))
        struct.pack_into('<I', rec, 0x54 + 4 * s, anims[ap])
    return rec


def composed_actor(ins, rom, rec_at, fn, remap=None):
    """A copy of an actor with every frame through fn(image, view) as a whole: a frame's pieces (a boss's can have two, e.g. Kid Buu's 32x32
    over 32x16) are put together on the frame's box, changed, and cut back into the same pieces, so the layout, OAM attributes and OBJ
    memory stay the actor's own. Frame = u32 count, box (s8 x, s8 y, u8 w, u8 h), then count x (box, OAM attr, tile container) of 12 bytes.
    remap: {slot: [(slot, frame), ...]} builds that slot from other slots' frames (Beerus: no death by dissolving). Tiles are stored raw.
    fn may also return (image, (dx, dy)): a larger image whose corner goes (dx, dy) from the frame's own (a taller Beerus). The frame's
    pieces stay where they are and what the image has beyond them goes into strips of 8 pixels above, left or right of the box (new
    pieces, only where they hold a pixel); the record's sprite memory a frame (its word at +2) is raised to the largest frame's."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    n = u(rec_at) & 0xFF; rec = bytearray(rom[rec_at:rec_at + 0x54 + 4 * n])
    tiles, frames, anims = {}, {}, {}
    def piece(tp, w, h):
        o = tp - BASE; t, size = u(o), u(o + 4)
        raw = rom[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(rom, o + 8, size)[0])
        raw = bytes(raw[:w * h]).ljust(w * h, b'\0')
        return np.frombuffer(raw, np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)
    def frame(fp, view):
        if (fp, view) in frames: return frames[fp, view]
        o = fp - BASE; c = u(o); bx, by, bw, bh = struct.unpack_from('<bbBB', rom, o + 4)
        img = np.zeros((bh, bw), np.uint8); boxes = []
        for j in range(c):
            x, y, w, h = struct.unpack_from('<bbBB', rom, o + 8 + 12 * j)
            img[y - by:y - by + h, x - bx:x - bx + w] = piece(u(o + 16 + 12 * j), w, h); boxes.append((x, y, w, h))
        out = fn(img, view); off = (0, 0)
        if isinstance(out, tuple): out, off = out
        out = np.asarray(out, np.uint8)
        body = bytearray(rom[o:o + 8 + 12 * c]); cut = [(x - bx, y - by, w, h) for x, y, w, h in boxes]
        if out.shape != img.shape or off != (0, 0):
            out, cut, body = grown(o, out, off, (bx, by, bw, bh), boxes, body)
        used[0] = max(used[0], sum(w * h for _, _, w, h in cut))
        for j, (x, y, w, h) in enumerate(cut):
            data = out[y:y + h, x:x + w].reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
            if data not in tiles: tiles[data] = ins.put(struct.pack('<II', 0, len(data)) + data)
            struct.pack_into('<I', body, 16 + 12 * j, tiles[data])
        frames[fp, view] = ins.put(bytes(body))
        return frames[fp, view]
    used = [0]
    SHAPES = {(8, 8): (0, 0), (16, 8): (1, 0), (32, 8): (1, 1), (8, 16): (2, 0), (8, 32): (2, 1)}      # (w, h) -> OAM shape, size
    def grown(o, out, off, box, boxes, body):
        """A frame whose image outgrew its box: -> (the image on the grown box, [(x, y, w, h) of every piece on it], the frame's
        bytes with the new pieces and box). The pieces it had keep their place on the screen. A mirrored frame's pieces are stored
        where they are shown (x = 16 - w - x of the frame as drawn), so its side strips change sides."""
        bx, by, bw, bh = box; dx, dy = off; H, W = out.shape
        a0, a1 = struct.unpack_from('<HH', rom, o + 12); flip = a1 & 0x1000
        top, left, right = -dy, -dx, W + dx - bw
        if dy > 0 or dx > 0 or H + dy != bh or max(top, left, right) > 8 or min(top, left, right) < 0 or bw % 8 or bh % 8:
            sys.exit('composed_actor: a frame grew in a way that is not handled (box %s, image %dx%d at %s)' % (box, W, H, off))
        if flip and any((x, w) != (bx, bw) for x, y, w, h in boxes) and (left or right):
            sys.exit('composed_actor: a mirrored frame of several narrow pieces cannot grow sideways')
        pt, pl, pr = 8 * (top > 0), 8 * (left > 0), 8 * (right > 0)          # the grown box: 8 more on each side that grew
        P = np.zeros((bh + pt, bw + pl + pr), np.uint8)
        P[pt + dy:pt + dy + H, pl + dx:pl + dx + W] = out
        cut = [(x - bx + pl, y - by + pt, w, h) for x, y, w, h in boxes]; new = []
        def strips(x0, y0, w, h, tall):                        # cover w x h at (x0, y0) of P with pieces 8 thick that hold a pixel
            sizes = (32, 16, 8); at = 0; length = h if tall else w
            while at < length:
                n = next(k for k in sizes if k <= length - at)
                r = (x0, y0 + at, 8, n) if tall else (x0 + at, y0, n, 8)
                if P[r[1]:r[1] + r[3], r[0]:r[0] + r[2]].any(): new.append(r)
                at += n
        if pt: strips(0, 0, bw + pl + pr, 8, False)
        if pl: strips(0, pt, 8, bh, True)
        if pr: strips(bw + pl, pt, 8, bh, True)
        nbx = bx - (pr if flip else pl); nby = by - pt
        for (x, y, w, h) in new:
            shape, size = SHAPES[w, h]
            sx = (bw + pl + pr - w - x) if flip else x          # where it is shown on a mirrored frame
            body += struct.pack('<bbBBHHI', nbx + sx, nby + y, w, h, (a0 & 0x3FFF) | shape << 14, (a1 & 0x3FFF) | size << 14, 0)
        struct.pack_into('<I', body, 0, len(boxes) + len(new))
        struct.pack_into('<bbBB', body, 4, nbx, nby, bw + pl + pr, bh + pt)
        return P, cut + new, body
    for s in range(n):
        ap = u(rec_at + 0x54 + 4 * s)
        if not ap or s in (remap or {}): continue             # a remapped slot's own frames aren't needed
        if ap not in anims:
            o = ap - BASE; k = u(o)
            ptrs = [frame(u(o + 4 + 4 * j), min(j % 4, 2)) if u(o + 4 + 4 * j) else 0 for j in range(4 * k)]
            anims[ap] = (k, ptrs, ins.put(struct.pack('<I', k) + struct.pack('<%dI' % len(ptrs), *ptrs)))
        struct.pack_into('<I', rec, 0x54 + 4 * s, anims[ap][2])
    for s, seq in (remap or {}).items():
        ptrs = []
        for src, f in seq:
            k, p, _ = anims[u(rec_at + 0x54 + 4 * src)]
            ptrs += p[4 * f:4 * f + 4]
        struct.pack_into('<I', rec, 0x54 + 4 * int(s), ins.put(struct.pack('<I', len(seq)) + struct.pack('<%dI' % len(ptrs), *ptrs)))
    need = (used[0] + 63) & ~63                                # the allocator's unit is 64 bytes
    if need > struct.unpack_from('<H', rec, 2)[0]: struct.pack_into('<H', rec, 2, need)
    return rec


def frame_image(rom, fp):
    """The single piece of a BF-format frame as an index image."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    o = fp - BASE; w, h = rom[o + 6], rom[o + 7]; tp = u(o + 16) - BASE
    t, size = u(tp), u(tp + 4)
    raw = rom[tp + 8:tp + 8 + size] if t == 0 else bytes(decompress_stream(rom, tp + 8, size)[0])
    return np.frombuffer(bytes(raw[:w * h]), np.uint8).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3).reshape(h, w)


def hairswap_actor(ins, rom, base_at, ref_at, ss_at, slot_map=None, idle_slots=()):
    """An outfit's Super Saiyan made from three retail actors of one character (Nov 9: orange-gi Gohan went Super Saiyan in his school
    uniform, because the game has no orange-gi Super Saiyan). `ss_at` (Super Saiyan in another outfit) gives the record and its slots;
    in each of its frames the pixels that differ from the same frame of `ref_at` (that outfit's base: the gold hair, the green eyes) are
    laid over the same frame of `base_at` (the new outfit's base), so the body and clothes are the outfit's own. slot_map {ss slot:
    (ref slot, base slot)} where the actors number a slot differently; idle_slots (the power-down, which the base forms lack) are diffed
    against the Super Saiyan's idle and laid over the new idle. Returns (record, frames made, frames left as the Super Saiyan's)."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    slot_map = slot_map or {}
    def anim(rec_at, s):
        n = u(rec_at) & 0xFF
        ap = u(rec_at + 0x54 + 4 * s) if s < n else 0
        if not ap: return None
        k = u(ap - BASE); return [u(ap - BASE + 4 + 4 * i) for i in range(4 * k)]
    def one_piece(fp): return fp and u(fp - BASE) == 1
    def origin(fp): return struct.unpack_from('<bb', rom, fp - BASE + 4)      # the piece's x, y from the sprite's origin
    def put_frame(fp, img):
        o = fp - BASE; body = bytearray(rom[o:o + 4 + 16])
        h, w = img.shape
        data = np.ascontiguousarray(img, np.uint8).reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
        struct.pack_into('<I', body, 4 + 12, ins.put(struct.pack('<II', 0, len(data)) + data))
        return ins.put(bytes(body))
    n = u(ss_at) & 0xFF; rec = bytearray(rom[ss_at:ss_at + 0x54 + 4 * n])
    made = kept = 0
    ss_idle, new_idle = anim(ss_at, 0), {}
    for s in range(n):
        ss = anim(ss_at, s)
        if not ss: continue
        if s in idle_slots:
            pairs = [(ss_idle[d % 4], None) for d in range(len(ss))]     # against the idle's first frame, the same view
        else:
            rs, bs = slot_map.get(s, (s, s)); ref, base = anim(ref_at, rs), anim(base_at, bs)
            pairs = list(zip(ref, base)) if ref and base and len(ref) == len(ss) == len(base) else [(None, None)] * len(ss)
        out = []
        for i, fp in enumerate(ss):
            rp, bp = pairs[i]
            if s in idle_slots: bp = new_idle.get(i % 4)
            base_ok = isinstance(bp, np.ndarray) or (bp is not None and one_piece(bp))
            if not fp or not one_piece(fp) or not one_piece(rp) or not base_ok:
                out.append(fp); kept += bool(fp); continue
            a, r = frame_image(rom, fp), frame_image(rom, rp)
            b = bp if isinstance(bp, np.ndarray) else frame_image(rom, bp)
            if s in idle_slots and r.shape == b.shape and r.shape != a.shape:
                # the power-down's frames are 32x32 where the idle is 16x32: the idle on the frame's grid, by the pieces' own offsets
                (ax, ay), (rx, ry) = origin(fp), origin(rp)
                dx, dy = rx - ax, ry - ay
                if 0 <= dx and 0 <= dy and dx + r.shape[1] <= a.shape[1] and dy + r.shape[0] <= a.shape[0]:
                    def grid(img):
                        g = np.zeros_like(a); g[dy:dy + img.shape[0], dx:dx + img.shape[1]] = img; return g
                    r, b = grid(r), grid(b)
            if not (a.shape == r.shape == b.shape):
                out.append(fp); kept += 1; continue
            img = b.copy(); m = a != r; img[m] = a[m]
            if s == 0 and i < 4: new_idle[i] = img
            out.append(put_frame(fp, img)); made += 1
        struct.pack_into('<I', rec, 0x54 + 4 * s, ins.put(struct.pack('<I', len(ss) // 4) + struct.pack('<%dI' % len(out), *out)))
    return rec, made, kept


def blue_hair_actor(ins, rom, base_at, ss_at, gold, to, transplant=None):
    """A Super Saiyan figure with its hair turned blue, frame for frame (Nov 9, the owner: SSB Gogeta's sheet frames were a noisy blob with
    a glow round the hair, "recolor SSJ GOGETA ... just remove the halo"). `gold` are the Super Saiyan hair's colours; a pixel is hair when
    it is one of them where the base figure (same slot and frame, laid on the same grid by the pieces' offsets) is black hair or empty, or
    when it is one of the colours only the hair uses (`to`'s keys minus the shared ones are all hair). to: {gold index: blue index}.
    transplant(a, b, view, slot) -> (canvas, its corner from the frame's, a score) instead gives each frame its own new hair or colours
    (Nov 10, for Blue Gogeta, since replaced by lib/ssb.py); the canvas is cut back to its art in one piece (at most 32x32, 1 KB of OBJ memory, the feet kept). Returns (record, frames recoloured)."""
    u = lambda o: struct.unpack_from('<I', rom, o)[0]
    def anim(rec_at, s):
        n = u(rec_at) & 0xFF
        ap = u(rec_at + 0x54 + 4 * s) if s < n else 0
        if not ap: return None
        k = u(ap - BASE); return [u(ap - BASE + 4 + 4 * i) for i in range(4 * k)]
    def one_piece(fp): return fp and u(fp - BASE) == 1
    def origin(fp): return struct.unpack_from('<bb', rom, fp - BASE + 4)
    def put_frame(fp, img, at=None):
        o = fp - BASE; body = bytearray(rom[o:o + 4 + 16])
        if at is not None:                             # a canvas whose corner is `at` from the frame's: cut to its art, one piece of 1 KB at most
            x, y, w0, h0 = struct.unpack_from('<bbBB', body, 4)
            a0, a1 = struct.unpack_from('<HH', body, 12); flip = a1 & 0x1000
            ys, xs = np.nonzero(img)
            y1 = ys.max() + 1; y0 = max(ys.min(), y1 - 32)            # the feet kept: anything over 32 rows goes from the top
            x0, x1 = xs.min(), xs.max() + 1
            if x1 - x0 > 32: x0 = (x0 + x1) // 2 - 16; x1 = x0 + 32
            w, h = min(((W, H) for (W, H) in SHAPE if W * H <= 1024 and W >= x1 - x0 and H >= y1 - y0), key=lambda s: s[0] * s[1])
            cut = np.zeros((h, w), np.uint8); part = img[y0:y0 + h, x0:x0 + w]; cut[:part.shape[0], :part.shape[1]] = part
            img = cut
            ux = (16 - w0 - x if flip else x) + at[0] + x0          # the unmirrored layout's x, then mirrored back if the piece is flipped
            nx, ny = (16 - w - ux if flip else ux), y + at[1] + y0
            assert -128 <= nx < 128 and -128 <= ny < 128
            struct.pack_into('<bbBBbbBB', body, 4, nx, ny, w, h, nx, ny, w, h)
            sh, sz = SHAPE[(w, h)]
            struct.pack_into('<HH', body, 12, (a0 & 0x3FFF) | sh << 14, (a1 & 0x3FFF) | sz << 14)
        h, w = img.shape
        data = np.ascontiguousarray(img, np.uint8).reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1).tobytes()
        struct.pack_into('<I', body, 4 + 12, ins.put(struct.pack('<II', 0, len(data)) + data))
        return ins.put(bytes(body))
    only_hair = [k for k in to if k not in gold['shared']]
    lut = np.arange(256, dtype=np.uint8)
    for k, v in to.items(): lut[k] = v
    n = u(ss_at) & 0xFF; rec = bytearray(rom[ss_at:ss_at + 0x54 + 4 * n])
    done, made = {}, 0
    for s in range(n):
        ss, base = anim(ss_at, s), anim(base_at, s)
        if not ss: continue
        out = []
        for i, fp in enumerate(ss):
            if not one_piece(fp): out.append(fp); continue
            bp = base[i] if base and i < len(base) and one_piece(base[i]) else None
            key = (fp, bp)
            if key not in done:
                a = frame_image(rom, fp)
                b = np.zeros_like(a)
                if bp:
                    bi = frame_image(rom, bp); (ax, ay), (bx, by) = origin(fp), origin(bp)
                    dx, dy = bx - ax, by - ay
                    y0, x0 = max(0, dy), max(0, dx); y1, x1 = min(a.shape[0], dy + bi.shape[0]), min(a.shape[1], dx + bi.shape[1])
                    if y1 > y0 and x1 > x0: b[y0:y1, x0:x1] = bi[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
                at = None
                if transplant:
                    img, at, iou = transplant(a, b, i % 4, s)
                    ins.__dict__.setdefault('_hair_iou', []).append(iou)
                else:
                    hair = np.isin(a, only_hair) | (np.isin(a, list(gold['shared'])) & np.isin(b, [0, 1]))
                    img = a.copy(); img[hair] = lut[a[hair]]
                done[key] = put_frame(fp, img, at); made += 1
            out.append(done[key])
        struct.pack_into('<I', rec, 0x54 + 4 * s, ins.put(struct.pack('<I', len(ss) // 4) + struct.pack('<%dI' % len(out), *out)))
    return rec, made


def proto_actor(ins, P, i):
    """Copy actor i of Prototype D: the record, its animations, frames and WFZ tile blocks (verbatim: the prototype
    master palette equals retail's, so colour indices carry over). Returns the record (pointers rebased)."""
    from wfz import decompress_stream
    u = lambda o: struct.unpack_from('<I', P, o)[0]
    p = u(PROTO_ACTOR_LIST + 4 * i) - BASE; n = u(p) & 0xFF
    rec = bytearray(P[p:p + 0x54 + 4 * n])
    struct.pack_into('<I', rec, 0x50, 0)                   # no halo table
    for o in range(4, 0x10, 4):                            # any other pointer field would point into the prototype
        assert not (BASE <= struct.unpack_from('<I', rec, o)[0] < BASE + len(P)), 'proto actor %d: pointer at +%x' % (i, o)
    tiles = ins.__dict__.setdefault('_proto_tiles', {}); frames = ins.__dict__.setdefault('_proto_frames', {})
    def tile(tp):
        if tp not in tiles:
            o = tp - BASE; t, size = u(o), u(o + 4)
            end = decompress_stream(P, o + 8, size)[1] if t else o + 8 + size
            tiles[tp] = ins.put(P[o:end])
        return tiles[tp]
    def frame(fp):
        if fp not in frames:
            o = fp - BASE; k = u(o); body = bytearray(P[o:o + 4 + 16 * k])
            for j in range(k): struct.pack_into('<I', body, 4 + 16 * j + 12, tile(u(o + 4 + 16 * j + 12)))
            frames[fp] = ins.put(bytes(body))
        return frames[fp]
    for s in range(n):
        ap = u(p + 0x54 + 4 * s)
        if not ap: continue
        o = ap - BASE; k = u(o)
        ptrs = [frame(u(o + 4 + 4 * j)) if u(o + 4 + 4 * j) else 0 for j in range(4 * k)]
        struct.pack_into('<I', rec, 0x54 + 4 * s, ins.put(struct.pack('<I', k) + struct.pack('<%dI' % len(ptrs), *ptrs)))
    return rec
