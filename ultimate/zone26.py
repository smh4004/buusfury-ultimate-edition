"""Zone 26: the prototype's cut Super 13 dungeon as new areas 26:1..15. Layouts and collision come from Prototype D, reskinned
by reskin.py. One flat BG3 layer, stored tile pages; the prototype's one-way debug doors are replaced by zone26.json."""
import json, os, struct, sys
import numpy as np
from wfz import decompress_stream
import reskin
sys.path.insert(0, 'tools/scripts')

BASE = 0x08000000
TABLE_LIT, COUNT_INSN, AREAS, COUNT = 0x8A58, 0x125E0, 0x8E2E0, 452
WARP = (0x08007675, 0x0800776D)
TRIGGER = (0x0800742D, 0x080077DF)   # an exit that runs a step list when you're inside its rectangle
LAYER_FN = 0x08008087
GLACIER_NAME_UI = 1534 + 41                          # the banner on the way in
MUSIC_FIELD = 6
GLACIER_SONG, GLACIER_LOG2_SONG = 52, 7              # BF's song table has spare slots 2 and 52: nothing uses them. LoG2 song 7 is "Era of Darkness"


class Writer:
    def __init__(self, rom, at): self.rom, self.cur = rom, at
    def put(self, d):
        a = self.cur; self.rom[a:a + len(d)] = d; self.cur = (a + len(d) + 3) & ~3
        return BASE + a
    def stored(self, d):
        return self.put(struct.pack('<II', 0, len(d)) + bytes(d))


def wfz_copy(W, P, ptr):
    o = ptr - BASE; t, size = struct.unpack_from('<II', P, o)
    data = P[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(P, o + 8, size)[0])
    return W.stored(data)


def tile_map(img):
    """Cut an image into 8x8 tiles, sharing flipped copies. Returns (tiles, {y, x: cell value})."""
    h, w = img.shape; tiles = [bytes(64)]; seen = {tiles[0]: 0}
    cells = np.zeros((h // 8, w // 8), np.uint16)
    for y in range(h // 8):
        for x in range(w // 8):
            t = img[y * 8:y * 8 + 8, x * 8:x * 8 + 8]
            for flag, v in ((0, t), (0x400, t[:, ::-1]), (0x800, t[::-1]), (0xC00, t[::-1, ::-1])):
                b = v.tobytes()
                if b in seen: cells[y, x] = seen[b] | flag; break
            else:
                b = t.tobytes(); seen[b] = len(tiles); cells[y, x] = len(tiles); tiles.append(b)
    if len(tiles) > 896: raise ValueError('%d tiles: over the 896 the largest retail map uses' % len(tiles))
    return tiles, cells


def build_map(W, P, a, img, mask):
    """The map record from one reskinned image; everything else from the prototype's record. Returns bus M."""
    m = reskin.map_of_raw(P, a); w = list(struct.unpack_from('<21I', P, m))
    tiles, cells = tile_map(img); H, Wd = cells.shape
    cw, ch = (Wd + 31) // 32, (H + 31) // 32
    chunks = []
    for cy in range(ch):
        for cx in range(cw):
            c = np.zeros((32, 32), np.uint16); s = cells[cy * 32:cy * 32 + 32, cx * 32:cx * 32 + 32]
            c[:s.shape[0], :s.shape[1]] = s
            chunks.append(W.stored(c.astype('<u2').tobytes()) if c.any() else 0)
    n = W.put(struct.pack('<6I', LAYER_FN, 0x400, 0x400, 0, 0, 0x101) + struct.pack('<I', 0))
    n1 = W.put(struct.pack('<6I', LAYER_FN, 0x400, 0x400, 0x10000, 0x10000, 0x101) + struct.pack('<I', 0))
    n2 = W.put(struct.pack('<6I', LAYER_FN, 0x400, 0x400, 0x20000, 0x20000, 0x101) + struct.pack('<I', 0))
    layer = W.put(struct.pack('<6I', LAYER_FN, 0x400, 0x400, 0, 0, ch << 8 | cw) + struct.pack('<%dI' % len(chunks), *chunks))
    nw = list(w)
    nw[0] = W.put(struct.pack('<6I', WARP[0], WARP[1], 0, 0, 0, 0))    # the map's built-in door: empty, zone26.json lists the doors
    nw[4] = nw[5] = 0
    nw[6], nw[7], nw[8], nw[9] = n, n1, n2, layer
    nw[10] = nw[11] = nw[12] = 0
    nw[14] = W.stored(mask.tobytes()) ; nw[15] = wfz_copy(W, P, w[15])
    nw[17] = 1
    deltas = np.ones(len(tiles), np.int64) * 0                       # ids 0,1,2..: consecutive
    nw[19] = W.stored(deltas.astype('<u2').tobytes())
    pages = [b''.join(tiles[i:i + 256]) for i in range(0, len(tiles), 256)]
    nw[20] = W.put(b''.join(struct.pack('<I', W.stored(p)) for p in pages))
    M = W.cur; nw[18] = BASE + M
    W.put(struct.pack('<21I', *nw))
    return BASE + M, len(tiles)


def floor_mask(P, proto_path, a):
    """Walkable cells, 256 per row: the prototype's mask minus what the reskin draws as solid."""
    m = reskin.map_of_raw(P, a); o = struct.unpack_from('<I', P, m + 0x38)[0] - BASE; t, size = struct.unpack_from('<II', P, o)
    d = P[o + 8:o + 8 + size] if t == 0 else bytes(decompress_stream(P, o + 8, size)[0])
    bits = np.unpackbits(np.frombuffer(d, np.uint8), bitorder='little').reshape(-1, 256).copy()
    b = reskin.blockers(proto_path, a); h, w = min(b.shape[0], bits.shape[0]), min(b.shape[1], 256)
    bits[:h, :w][b[:h, :w]] = 0
    edits = json.load(open('ultimate/zone26.json')).get('ground', {}).get(str(a), {})
    for x0, y0, x1, y1 in edits.get('close', []): bits[y0 // 8:y1 // 8, x0 // 8:x1 // 8] = 0
    for x0, y0, x1, y1 in edits.get('open', []): bits[y0 // 8:y1 // 8, x0 // 8:x1 // 8] = 1
    return bits


def follow_outline(mask, outline, doors):
    """Collision matches the drawn snow: a cell mostly outside the smoothed outline is solid (door cells stay open)."""
    h, w = outline.shape; H, W = h // 8, w // 8
    inside = outline[:H * 8, :W * 8].reshape(H, 8, W, 8).mean((1, 3)) >= 0.5
    out = mask.copy(); hh, ww = min(H, out.shape[0]), min(W, 256)
    out[:hh, :ww] &= inside[:hh, :ww]
    for d in doors:
        x0, y0, x1, y1 = d['rect']; out[y0 // 8:(y1 + 7) // 8, x0 // 8:(x1 + 7) // 8] = mask[y0 // 8:(y1 + 7) // 8, x0 // 8:(x1 + 7) // 8]
    return out


def walkable(mask, x, y):
    """Can a fighter's body stand with its corner at x, y?"""
    if x < 0 or y < 0: return False
    x1, y1 = x + BODY[0] - 1, y + BODY[1] - 1
    if y1 // 8 >= mask.shape[0] or x1 // 8 >= 256: return False
    return bool(mask[y // 8:y1 // 8 + 1, x // 8:x1 // 8 + 1].all())


def audit(a, mask, doors):
    """A fighter's body must be able to walk from each arrival to every door's strip, and stand in it. The game tests the door against
    the fighter's x, y only, so a strip it can't get that point into can't be used, however open the cells look."""
    def spots(d):
        x0, y0, x1, y1 = d['rect']
        return [(x, y) for y in range(y0 & ~3, y1, 4) for x in range(x0 & ~3, x1, 4) if x0 <= x < x1 and y0 <= y < y1 and walkable(mask, x, y)]
    if not doors: return
    start = spots(doors[0])
    if not start: sys.exit('Zone 26: room %d door %s has nowhere to stand' % (a, doors[0]['rect']))
    seen = set(start); q = list(start)
    while q:
        x, y = q.pop()
        for n in ((x + 4, y), (x - 4, y), (x, y + 4), (x, y - 4)):
            if n not in seen and walkable(mask, *n): seen.add(n); q.append(n)
    for d in doors:
        if not seen.intersection(spots(d)):
            sys.exit('Zone 26: room %d door %s cut off from door %s' % (a, d['rect'], doors[0]['rect']))


KEY = {'down': 0, 'up': 1, 'left': 2, 'right': 3}
DEBUG_SPOT = (128, 144, 168, 164)                     # debug zone build: where you start on Snake Way
BODY = (16, 8)                                       # a fighter blocks this many pixels right of and below its x, y (measured in the game)


def door(cfg, a, side, s, e, masks):
    """The strip at this opening and where you land coming through it: (rect, key to walk through, arrival). The strip sits on
    the outermost line of cells you can actually stand on across most of the opening."""
    m = masks[a]; c = (s + e) // 2; n = (e - s) // 8
    open_y = [y for y in range(m.shape[0]) if m[y, s // 8:e // 8].sum() * 2 > n]
    open_x = [x for x in range(256) if m[s // 8:e // 8, x].sum() * 2 > n]
    if side == 'top': t = open_y[0] * 8; return (s, t, e, t + 9), 'up', (c, t + 16)
    if side == 'bottom': t = (open_y[-1] + 1) * 8; return (s, t - 9, e, t), 'down', (c, t - 20)
    if side == 'left': t = open_x[0] * 8; return (t, s, t + 9, e), 'left', (t + 14, c)
    t = (open_x[-1] + 1) * 8; return (t - BODY[0] - 9, s, t, e), 'right', (t - BODY[0] - 18, c)   # a fighter's x is its body's left edge, so it stops BODY[0] short of a right-hand wall


def links(cfg, masks):
    out = {}
    for a, extra in cfg.get('doors', {}).items():
        for d in extra: out.setdefault(int(a), []).append(dict(rect=tuple(d['rect']), key=d['key'], world=d['world'], to=building_room() if d['to'] == 'building' else d['to'], arrive=tuple(d['arrive'])))
    for a, sa, s0, e0, b, sb, s1, e1 in cfg['links']:
        if isinstance(b, list):                       # an exit out of the zone: [world, area, x, y]
            ra, ka, _ = door(cfg, a, sa, s0, e0, masks)
            out.setdefault(a, []).append(dict(rect=ra, key=KEY[ka], world=b[0], to=b[1], arrive=(b[2], b[3])))
            continue
        ra, ka, ta = door(cfg, a, sa, s0, e0, masks); rb, kb, tb = door(cfg, b, sb, s1, e1, masks)
        out.setdefault(a, []).append(dict(rect=ra, key=KEY[ka], to=b, arrive=tb))
        out.setdefault(b, []).append(dict(rect=rb, key=KEY[kb], to=a, arrive=ta))
    return out


STATS = 0x711274
PHASE1_ROW, BOSS_ROW = 113, 114      # placed nowhere else in the game
STATS_COUNT, STATS_REFS = 150, (0xFCE4, 0xFD70, 0x1BA90, 0x24F28, 0x279DC, 0x2CD18, 0x2F5E4, 0x32D3C, 0x335B8, 0x39BD4, 0x39D90, 0x3A384, 0x3A698)
RUSH = ((18, 73), (28, 43), (122, 154), (10, 38), (115, 49), (118, 51), (120, 52), (61, 47), (BOSS_ROW, 'super13'))
# Dabura, Majin Buu, Super Janemba, Broly, Super Buu, Super Buu with Gotenks, Kid Buu, Super 13: enemy row and character from spawns.csv.
# Super Buu with Gohan is row 120: row 119, the other one in his story room, lies still and can't be hit outside his scene.
# World Tournament: each round draws one opponent at random from its own pool, so nobody can come up twice. Enemy row, character. Stats and HP are set per round.
TOUR_POOLS = (((147, 303), (111, 252), (49, 143), (85, 206), (80, 201), (63, 164)),                  # Yamu, Spopovich, Idasa, Olibu, Ninja Boss, Knight Destroyer
              ((91, 224), (39, 123), (130, 269), (18, 73), (129, 221), (0, 31)),                    # Pikkon, Goten, Trunks, Dabura, Pharoah, Airship Warlord
              ((122, 154), (10, 38), (28, 43), (115, 49), (61, 47), (BOSS_ROW, 'super13')))          # Super Janemba, Broly, Majin Buu, Super Buu, Kid Buu, Super 13
TOUR_HP = (15000, 20000, 30000)                     # each opponent adds 10 per place in its pool, so a test can tell them apart
TOUR_STATS = ((145, 60, 40, 60), (145, 70, 50, 65), (150, 75, 85, 70))     # level + 50, Strength, Power, Endurance
TOUR_NAMES = (('Yamu', 'Spopovich', 'Idasa', 'Olibu', 'Ninja Boss', 'Knight Destroyer'), ('Pikkon', 'Goten', 'Trunks', 'Dabura', 'Pharoah', 'Airship Warlord'),
              ('Super Janemba', 'Broly', 'Majin Buu', 'Super Buu', 'Kid Buu', 'Super 13'))
# Custom flag numbers. A flag is a bit counted from G+0x55, and the story's flags stop at 447: above that the same bits are the map's rooms visited (G+0x8D, 410 used, so flags 448-857)
# then the Scouter's entries (G+0xC5 to G+0xE1, flags 896-1127). Only the gaps are free:
#   858-863   858-860 story outfits, 862 debug hook, 861 and 863 spare
#   864-895   864-872 Super Saiyan 2 by owner, 873-880 rewards, 881-886 Super 13, 887-890 Boss Rush and tournament, 891-894 trials won, 895 all trials
#   1128-1143 1128-1131 trials paid, 1132-1140 tournament picks, 1141 ordered tournament test, 1142-1143 spare
TOUR_PICKS, TOUR_PICK, TOUR_GET = 1132, 0xE1, 0xE2    # flags 1132-1140 hold each round's opponent, 3 bits a round; natives tour_pick(round, place) and tour_get(round)
TRIALS = ((0, 'Goku', 91, 224, 'Pikkon', 39, 'Titanium Breastplate'), (1, 'Gohan', 18, 73, 'Dabura', 70, 'Enhanced Energy Gloves'),
          (3, 'Vegeta', 28, 43, 'Majin Buu', 108, 'Clean Boots'), (4, 'Trunks', 39, 123, 'Goten', 159, 'Clean Belt'))     # party slot, name, enemy row, character, opponent, equipment row, its name
TRIAL_GEAR = 160                                   # all four: Geromantium Bandana, with the Senzu Beans below
if os.environ.get('BFU_CLASH_TEST'): TRIALS = ((int(os.environ.get('BFU_CLASH_SLOT', 0)), 'Goku', 61, 47, 'Kid Buu', 39, 'Titanium Breastplate'),) + TRIALS[1:]     # test_clash.py fights the game's beam user
TRIAL_HP, TRIAL_STATS, TRIAL_PRIZE, TRIAL_ITEM, TRIAL_ITEMS = 40000, (148, 65, 60, 65), 30000, 11, 10    # all four: ten Senzu Beans (item 11)
TRIAL_WON, TRIAL_PAID, TRIAL_ALL = 891, 1128, 895
# Hyperbolic Time Chamber: Mr. Popo on the Lookout spars you against anyone from the story, after the ending, in the Chamber's white room. Stats as in the story, EXP cut to SPAR_EXP tenths.
# Category, then (name, enemy row, character). Broly needs flag 111, his story fight. Buu with Gohan (row 119) isn't listed: his health can't be taken down outside his story fight. Rows are the story's own, with at least SPAR_MIN_HP: a few story rows have next to none.
SPAR = (('Tournament', (('Spopovich', 112, 252), ('Yamu', 148, 303), ('Pui Pui', 96, 234), ('Yakon', 145, 300))),
        ('Majin', (('Dabura', 18, 73), ('Majin Vegeta', 70, 282), ('Majin Buu', 28, 43), ('Super Buu', 115, 49))),
        ('Final Buu', (('Buu with Gotenks', 118, 51), ('Buu at full power', 121, 49), ('Kid Buu', 60, 47), ('Evil Piccolo', 90, 222))),
        ('Other World', (('Pikkon', 91, 224), ('Olibu', 85, 206), ('Super Janemba', 122, 154), ('Broly', 10, 38))),
        ('Minibosses', (('Airship Warlord', 0, 31), ('Ninja Boss', 80, 201), ('Knight Destroyer', 63, 164), ('War Machine', 140, 291))),
        ('Friends', (('Goten', 39, 123), ('Trunks', 130, 269), ('Gohan', 35, 110), ('Gotenks', 40, 126))))
# Dragon Ball hunt, after the ending: one ball in each of seven lands, a short walk from the capsule pad you land on. (world, area, x, y). Carrying a ball is the game's own item 16-22.
BALLS = ((5, 1, 264, 344), (7, 1, 152, 112), (8, 1, 144, 104), (11, 1, 160, 40), (13, 1, 96, 120), (15, 1, 368, 352), (14, 1, 96, 128))
BALL_ITEM, BALL_ZENIE, BALL_NATIVE, WISH_NATIVE = 16, 1000000, 0xEA, 0xEB
BUILDING = (0, 92)
MORE_FLAG, MORE_GET, MORE_PUT = 2000, 0xE7, 0xF0    # flags past the story's, kept with the bench (32 of them): an outfit's flag from 2000 up, and natives more_get(n), more_put(n, value)
MORE_YAMCHA, MORE_TIEN, MORE_PIKKON, MORE_HERCULE = 0, 1, 2, 3
MORE_TIER, MORE_RACE, MORE_MUSEUM, MORE_RANK_NEW, MORE_HARD, MORE_HARD_PAID, MORE_ENDLESS_NEW, MORE_HERC_WON = 4, 5, 6, 7, 13, 14, 15, 24
MORE_LEDGIC_WON, MORE_GT, MORE_UUB_WON, MORE_UUB = 27, 28, 29, 30    # Ledgic beaten, not yet told; GT looks and Pan; Uub beaten, not yet told; Uub joined
MORE_BLACK, MORE_BLACK_WON = 25, 26                  # Goku Black: joined; Rose beaten, not yet told    # 8-10 best rank, 11-12 last rank, 16-23 best Endless run (see ladder in outfit.c)
LADDER = 0xDC                                       # native ladder(op): 0 start Endless, gives the first room; 1 is it on; 2 a win: pays, gives the next room; 3 it ended; 4 this run's wins; 5 best run; 6 rank(hp, max); 7 last rank; 8 best rank (1 C, 2 B, 3 A, 4 S)
ENDLESS_STEP, ENDLESS_CAP = 20000, 1000000          # an Endless win pays this times the run's wins, up to the cap
RANK_PRIZE = (50000, 100000, 200000, 300000)        # C, B, A, S
HARD_PRIZE, RACE_PRIZE, MUSEUM_PRIZE, MUSEUM_ITEM, MUSEUM_ITEMS = 300000, 50000, 1000000, 13, 5   # the museum: five Lazarus Crystals as well
# Harder copies of the tournament: tier 1 is the Hard bracket, tier 2 only comes up in Endless. HP and stats by round, as TOUR_HP and TOUR_STATS.
TIER_HP = ((30000, 40000, 60000), (60000, 80000, 120000))
TIER_STATS = (((150, 75, 70, 75), (152, 82, 80, 80), (155, 90, 100, 90)), ((158, 100, 110, 100), (160, 105, 120, 105), (160, 110, 130, 110)))
HERCULE_ROW, HERCULE_CHAR, HERCULE_HP, HERCULE_STATS = 45, 138, 300, (100, 5, 5, 5)     # the dare: he falls at once
# Goku Black's challenge, once the Hard bracket is won: Black, then Rose in a room of her own (health carries over, as in Android 13's fight).
# Kid Buu's row: they fire beams, so they can clash with you. (actor, HP, (level + 50, Strength, Power, Endurance))
BLACK_ROW, BLACK_FIGHT = 61, (('goku_black', 60000, (155, 90, 100, 90)), ('goku_rose', 80000, (158, 100, 115, 100)))
# GT, once Goku Black is on your side: Ledgic (Don Kee's caped bodyguard) brawls with the Bruiser's behaviour (row 12, as in Black Star Odyssey), then Uub and Majuub
# with Kid Buu's (beams). Each fight: its stats row, then [(actor, HP, stats)], then the flag its win sets.
LEDGIC_ROW, LEDGIC_FIGHT = 12, (('ledgic', 70000, (156, 100, 60, 105)),)
UUB_ROW, UUB_FIGHT = 61, (('uub', 60000, (155, 95, 100, 90)), ('majuub', 90000, (160, 105, 120, 105)))
SPAR_EXP, SPAR_MIN_HP, SPAR_ROOM, SPAR_HOME = 4, 2000, (6, 9), (288, 500)
# Trials II (More, then Next): the same four heroes against harder story foes, once the first four are paid. Party slot, name, enemy row, character, opponent, equipment, its name.
TRIALS2 = ((0, 'Goku', 70, 282, 'Majin Vegeta', 42, 'Z Armor'), (1, 'Gohan', 115, 49, 'Super Buu', 75, 'Geromantis Gloves'),
           (3, 'Vegeta', 60, 47, 'Kid Buu', 107, 'Saiyan Boots'), (4, 'Trunks', 122, 154, 'Janemba', 157, 'Black Belt'))
TRIAL2_HP, TRIAL2_STATS, TRIAL2_PRIZE, TRIAL2_GEAR = 70000, (153, 85, 80, 85), 60000, (43, 76, 111)   # all four: Geromantium Kataginu, Gloves and Tabi, with ten Senzu Beans
MORE_WAVE, MORE_T2_WON, MORE_T2_PAID, MORE_T2_ALL = 32, 38, 42, 46        # more flags 32-37 a wave cleared once, 38-41 Trials II won, 42-45 paid, 46 all paid
MORE_POINTS = 255                                   # more_put(MORE_POINTS, n): n stat points to whoever is playing
# Time Chamber waves (Mr. Popo, Waves): a category's four partners in a row, no rest between, 1.5x their health. The first clear of each gives WAVE_POINTS stat points, later ones Zenie.
WAVE_HP, WAVE_POINTS, WAVE_ZENIE = (3, 2), 3, 30000
# Dojo (More, then Next): fight a CPU copy of a fighter you have, on Kid Buu's row (beams, so it can clash with you).
# (name, character number or actor name, what unlocks it: None, ('flag', n) or ('more', n), as their guest outfits)
DOJO = (('Saiyans', (('Goku', 115, None), ('Vegeta', 279, None), ('Gohan', 110, None))),
        ('Friends', (('Piccolo', 'piccolo', ('flag', 879)), ('Android 18', 'android18', ('flag', 880)), ('Pan', 'pan', ('more', MORE_GT)))),
        ('Rivals', (('Broly', 38, ('flag', 111)), ('Goku Black', 'goku_black', ('more', MORE_BLACK)), ('Uub', 'uub', ('more', MORE_UUB)))))
DOJO_HP, DOJO_STATS, DOJO_ROW, DOJO_PRIZE = 40000, (152, 85, 85, 85), 61, 20000


def _challenge(who, fights, end='', room='stadium', home=None, won=None):
    """One challenge: fights [(actor or character, HP or None for its row's, stats or None, row)], each in its own room; the last one's fall
    runs `end`, sets `won` (a more flag) and sends you home (the Challenge Board unless `home` says (area, room, x, y))."""
    return dict(who=who, fights=fights, end=end, room=room, home=home or (3, 1, 208, 134), won=won)


def dojo_list():
    return [f for _, people in DOJO for f in people]


def challenges():
    out = [_challenge('black', [(a, hp, st, BLACK_ROW) for a, hp, st in BLACK_FIGHT], won=MORE_BLACK_WON),
           _challenge('ledgic', [(a, hp, st, LEDGIC_ROW) for a, hp, st in LEDGIC_FIGHT], won=MORE_LEDGIC_WON),
           _challenge('uub', [(a, hp, st, UUB_ROW) for a, hp, st in UUB_FIGHT], won=MORE_UUB_WON)]
    out += [_challenge('trial2_%d' % k, [(char, TRIAL2_HP, TRIAL2_STATS, row)], won=MORE_T2_WON + k) for k, (_, _, row, char, *_r) in enumerate(TRIALS2)]
    for k, (_, people) in enumerate(SPAR):
        prize = ('    pushn %d\n    call 0x%X\n    jz W1\n    pushn %d\n    call 0x%X\n    push 0\n    jz W2\nW1:\n    pushn %d, 1\n    call 0x%X\n    pushn %d, %d\n    call 0x%X\nW2:\n'
                 % (MORE_WAVE + k, MORE_GET, WAVE_ZENIE, ADD_ZENIE, MORE_WAVE + k, MORE_PUT, MORE_POINTS, WAVE_POINTS, MORE_PUT))
        out.append(_challenge('wave%d' % k, [(char, 'wave', None, row) for _, row, char in people], spar_off() + prize, 'white', (6, 1) + SPAR_HOME))
    out += [_challenge('dojo%d' % k, [(actor, DOJO_HP, DOJO_STATS, DOJO_ROW)], '    pushn %d\n    call 0x%X\n' % (DOJO_PRIZE, ADD_ZENIE)) for k, (_, actor, _) in enumerate(dojo_list())]
    return out

# Cell Games, from the Challenge Board: LoG2's arena, four fights in a row. Name, row whose behaviour it uses, HP, (level + 50, Strength, Power, Endurance), actor, how many.
# Perfect Cell takes Kid Buu's row: he fires beams, so he can clash with you. All health carries over, as in the Boss Rush.
CELL = (('Imperfect Cell', 115, 30000, (145, 65, 60, 55), 'cell_imperfect', 1),
        ('Semi-Perfect Cell', 118, 40000, (148, 70, 70, 60), 'cell_semi', 1),
        ('Cell Juniors', 21, 9000, (145, 60, 55, 45), 'cell_junior', 3),
        ('Perfect Cell', 61, 70000, (150, 80, 85, 75), 'cell_perfect', 1))
CELL_MAP, CELL_FOE, CELL_START, CELL_WON, CELL_PAID, CELL_COUNT, CELL_PRIZE, CELL_NAME_UI = 0x4E7668, (444, 432), (444, 520), 1142, 1143, (861, 863), 200000, 1534 + 40
HUB_AT = (208, 112)                                # where the tournament official stands in Hercule City; wins come home just below him
TOUR_ORDERED = 1141                                 # a test sets this to walk every opponent in turn instead of drawing
TOUR_ROOM, TOUR_PRIZE, TOUR_WON, ADD_ZENIE = (7, 6), 100000, 889, 0xE0
RUSH_FIRST, RUSH_WON = 19, 888   # room of the first fight, flag for a win not yet rewarded
RUSH_HP = (10000, 40000, 25840, 20240, 30000, 32000, 34000, 36000, 55000)    # shorter than the story's, since all nine share one health bar


def boss_stats(W, rom, stats):
    """Android 13 first, then Super 13, whose stats top Kid Buu's (150, 66, 110, 100); 105000 HP across the two phases against his 125000. At level 99 with an even build a punch does about 125 to Android 13 and 120 to Super 13, so this is 250 + 620 punches before charged hits and skills, and two of his hits still take a level 99 fighter down. Reloading a room in place loses the player, so each stage
    of the fight is its own copy of the arena: 15 Android 13, 16 his change, 17 Super 13, 18 the Spirit Bomb finish."""
    import bfscript
    def death(flag, area):
        return W.put(bytes(bfscript.asm('    pushn %d\n    call set_flag\n    call 0x78(30)\n    pushn 26, %d, 1, 120, 276\n    call 0x77\n    call 0x79(30)\n    end\n' % (flag, area))))
    def row(n, exp, hp, stat, phys, flag, area):
        r = stats + 28 * n; dabura = stats + 28 * 18
        rom[r:r + 28] = rom[dabura:dabura + 28]
        struct.pack_into('<II', rom, r, exp, hp)
        rom[r + 0xC:r + 0x10] = bytes(stat)
        rom[r + 0x10] = phys
        struct.pack_into('<II', rom, r + 0x14, 0x08708920, death(flag, area))     # this handler is the one that runs death scripts
    row(PHASE1_ROW, 40000, 30000, (150, 60, 90, 90), 128, 881, 16)
    row(BOSS_ROW, 96175, 75000, (160, 70, 115, 105), 96, 886, 18)


def tour_first():
    return RUSH_FIRST + len(RUSH)


def trial_first():
    return tour_first() + len(tour_list())


def trial_end(k):
    """Script run when trial k's opponent falls: home to the Challenge Board, which pays."""
    return '    pushn %d\n    call set_flag\n    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n' % (TRIAL_WON + k)


def spar_first():
    return trial_first() + len(TRIALS)


def spar_end():
    """Script run when a sparring partner falls: rested, back on the Lookout beside Mr. Popo."""
    return spar_off() + '    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn 6, 1, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n' % SPAR_HOME


def spar_list():
    return [who for _, people in SPAR for who in people]


def cell_first():
    return spar_first() + len(spar_list())


def building_room():
    """The house in room 2: a copy of the story's room whose door leads back out to room 2, not to West City."""
    return cell_first() + len(CELL)


def tier_first(t):
    """First room of this tier's tournament."""
    return tour_first() if t == 0 else building_room() + 1 + len(tour_list()) * (t - 1)


def hercule_room():
    return building_room() + 1 + len(tour_list()) * len(TIER_HP)


def challenge_room(name, k=0):
    """Room of fight k of a challenge (CHALLENGES order, each fight its own room after Hercule's)."""
    n = hercule_room() + 1
    for c in CHALLENGES:
        if c['who'] == name: return n + k
        n += len(c['fights'])
    raise KeyError(name)


def black_room(k=0):
    """Goku Black's fight: 0 Black, 1 Rose."""
    return challenge_room('black', k)


def tier_rooms():
    return ','.join(str(tier_first(t)) for t in range(len(TIER_HP) + 1))


def cell_rows():
    """(room, stats base row, HP, stats, actor, x, y) for each fighter: one room each, but the Cell Juniors share theirs."""
    out = []; room = cell_first()
    for name, base, hp, stats, actor, count in CELL:
        for k in range(count): out.append((room, base, hp, stats, actor, CELL_FOE[0] + (k - count // 2) * 56 if count > 1 else CELL_FOE[0], CELL_FOE[1], count > 1))
        room += 1
    return out


def cell_next(room, last):
    """Script run when a Cell Games fighter falls. The Juniors fall in any order: two flags count them, so the third moves on."""
    if last:
        return '    pushn %d\n    call set_flag\n    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n' % CELL_WON
    return '    call 0x78(30)\n    pushn 26, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    end\n' % (room + 1, CELL_START[0], CELL_START[1])


def cell_counted(room):
    a, b = CELL_COUNT
    return ('    pushn %d\n    call flag\n    jz L1\n    pushn %d\n    call clear_flag\n' % (b, b) + cell_next(room, False)
            + 'L1:\n    pushn %d\n    call flag\n    jz L2\n    pushn %d\n    call clear_flag\n    pushn %d\n    call set_flag\n    end\nL2:\n    pushn %d\n    call set_flag\n    end\n' % (a, a, b, a))


def spar_on():
    """Both flags together mean a Chamber fight is on: the Cell Juniors' count, which shares them, never sets both."""
    return ''.join('    pushn %d\n    call set_flag\n' % f for f in CELL_COUNT)


def spar_off():
    return ''.join('    pushn %d\n    call clear_flag\n' % f for f in CELL_COUNT)


CHALLENGES = challenges()


def tour_list():
    return [(rnd, place, row, char) for rnd, pool in enumerate(TOUR_POOLS) for place, (row, char) in enumerate(pool)]


def tour_draw(rnd, tier=0):
    """Script: go to this round's opponent, drawn or picked at the resident's menu."""
    base = tier_first(tier) + sum(len(p) for p in TOUR_POOLS[:rnd])
    return '    call 0x78(30)\n    push 26\n    call 0x%X(%d)\n    push %d\n    add\n    pushn 1, 360, 420\n    call 0x77\n    call 0x79(30)\n' % (TOUR_GET, rnd, base)


def tour_next(k, rnd, tier=0):
    """Script run when opponent k falls. In Endless every opponent just leads to the next."""
    home = '    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n'
    prize = ('    pushn %d\n    call set_flag\n    pushn %d\n    call 0x%X\n' % (TOUR_WON, TOUR_PRIZE, ADD_ZENIE) if tier == 0 else '    pushn %d, 1\n    call 0x%X\n    pushn %d\n    call 0x%X\n' % (MORE_HARD, MORE_PUT, HARD_PRIZE, ADD_ZENIE)) + home
    endless = '    pushn 1\n    call 0x%X\n    jz L0\n    call 0x78(30)\n    push 26\n    pushn 2\n    call 0x%X\n    pushn 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    end\nL0:\n' % (LADDER, LADDER)
    last = len(tour_list()) - 1
    ordered = ('    pushn %d\n    call flag\n    jz L1\n' % TOUR_ORDERED + ('    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    end\n' % (tier_first(tier) + k + 1) if k < last else prize) + 'L1:\n')
    return endless + ordered + (prize if rnd == len(TOUR_POOLS) - 1 else tour_draw(rnd + 1, tier) + '    end\n')


def rush_rows(W, rom, harmless=False):
    """The Boss Rush's copies of the bosses, on new rows of a moved stats table: each death sends you to the next room."""
    import bfscript
    rows = bytearray(rom[STATS:STATS + 28 * STATS_COUNT])
    for k, (row, _) in enumerate(RUSH):
        r = bytearray(rom[STATS + 28 * row:STATS + 28 * (row + 1)])
        struct.pack_into('<I', r, 4, RUSH_HP[k])
        if harmless: r[0xD] = r[0xE] = 0      # debug zone build only: bosses that can't end the test before it reaches the next room
        last = k == len(RUSH) - 1
        if last:     # home to West City, where the resident pays out: a scene can't start in a room that held a boss
            text = '    call hp\n    call max_hp\n    pushn 6\n    call 0x%X\n' % LADDER + '    pushn %d\n    call set_flag\n    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n' % RUSH_WON
        else:
            text = '    call 0x78(30)\n    pushn 26, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    end\n' % (RUSH_FIRST + k + 1, 120, 276)
        struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm(text))))
        rows += r
    for k, (rnd, place, row, _) in enumerate(tour_list()):
        r = bytearray(rom[STATS + 28 * row:STATS + 28 * (row + 1)])
        struct.pack_into('<I', r, 4, TOUR_HP[rnd] + 10 * place)
        r[0xC:0x10] = bytes(TOUR_STATS[rnd])
        if harmless: r[0xD] = r[0xE] = 0
        struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm(tour_next(k, rnd)))))
        rows += r
    for k, (_, _, row, *_rest) in enumerate(TRIALS):
        r = bytearray(rom[STATS + 28 * row:STATS + 28 * (row + 1)])
        struct.pack_into('<I', r, 4, TRIAL_HP)
        r[0xC:0x10] = bytes(TRIAL_STATS)
        if harmless: r[0xD] = r[0xE] = 0
        struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm(trial_end(k)))))
        rows += r
    end = W.put(bytes(bfscript.asm(spar_end())))
    for _, row, _ in spar_list():
        r = bytearray(rom[STATS + 28 * row:STATS + 28 * (row + 1)])
        struct.pack_into('<I', r, 0, struct.unpack_from('<I', r, 0)[0] * SPAR_EXP // 10)
        struct.pack_into('<I', r, 4, max(struct.unpack_from('<I', r, 4)[0], SPAR_MIN_HP))
        struct.pack_into('<II', r, 0x14, 0x08708920, end)
        rows += r
    done = []
    for k, (room, base, hp, stats, _, _, _, shared) in enumerate(cell_rows()):
        r = bytearray(rom[STATS + 28 * base:STATS + 28 * (base + 1)])
        struct.pack_into('<I', r, 4, hp); r[0xC:0x10] = bytes(stats)
        if harmless: r[0xD] = r[0xE] = 0
        last = room == cell_rows()[-1][0]
        struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm(cell_counted(room) if shared else cell_next(room, last)))))
        rows += r
    for tier in range(len(TIER_HP)):
        for k, (rnd, place, row, _) in enumerate(tour_list()):
            r = bytearray(rom[STATS + 28 * row:STATS + 28 * (row + 1)])
            struct.pack_into('<I', r, 4, TIER_HP[tier][rnd] + 10 * place)
            r[0xC:0x10] = bytes(TIER_STATS[tier][rnd])
            if harmless and tier == 0: r[0xD] = r[0xE] = 0     # the top tier stays dangerous, for the test of losing in Endless
            struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm(tour_next(k, rnd, tier + 1)))))
            rows += r
    r = bytearray(rom[STATS + 28 * HERCULE_ROW:STATS + 28 * (HERCULE_ROW + 1)])
    struct.pack_into('<I', r, 4, HERCULE_HP); r[0xC:0x10] = bytes(HERCULE_STATS)
    struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm('    pushn %d, 1\n    call 0x%X\n    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n' % (MORE_HERC_WON, MORE_PUT)))))
    rows += r
    for c in CHALLENGES:                 # Black falls and Rose comes on; Rose falls and you go home, as after Hercule. The same for each challenge.
        fights = c['fights']; arrive = (360, 420) if c['room'] == 'stadium' else (120, 150)
        for k, (_, hp, stats, row) in enumerate(fights):
            r = bytearray(rom[STATS + 28 * row:STATS + 28 * (row + 1)])
            if hp == 'wave':                                   # a Time Chamber wave: the partner's story row, as sparring has it, with half again its health
                struct.pack_into('<I', r, 0, struct.unpack_from('<I', r, 0)[0] * SPAR_EXP // 10)
                struct.pack_into('<I', r, 4, max(struct.unpack_from('<I', r, 4)[0], SPAR_MIN_HP) * WAVE_HP[0] // WAVE_HP[1])
            else:
                struct.pack_into('<I', r, 4, hp); r[0xC:0x10] = bytes(stats)
            if harmless: r[0xD] = r[0xE] = 0
            then = ('    call 0x78(30)\n    pushn 26, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    end\n' % ((challenge_room(c['who'], k + 1),) + arrive) if k + 1 < len(fights) else
                    c['end'] + ('    pushn %d, 1\n    call 0x%X\n' % (c['won'], MORE_PUT) if c['won'] is not None else '')
                    + '    call max_hp\n    set hp\n    call max_ki\n    set ki\n    call 0x78(60)\n    pushn %d, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    call 0x2F\n    call 0x33(0)\n    end\n' % c['home'])
            struct.pack_into('<II', r, 0x14, 0x08708920, W.put(bytes(bfscript.asm(then))))
            rows += r
    at = W.put(bytes(rows))
    for o in STATS_REFS:
        if struct.unpack_from('<I', rom, o)[0] != BASE + STATS:
            sys.exit('stats table reference moved: %X' % o)
        struct.pack_into('<I', rom, o, at)


def hub_person(W, rom):
    """Hercule City's first resident stands aside after Super 13, when the tournament official takes his spot with the same list."""
    e = next(AREAS + 56 * k for k in range(COUNT) if rom[AREAS + 56 * k] == 3 and rom[AREAS + 56 * k + 1] == 1)
    count = rom[e + 4]; lst = struct.unpack_from('<I', rom, e + 0x14)[0] - BASE
    ptrs = list(struct.unpack_from('<%dI' % count, rom, lst))
    old = next(p for p in ptrs if struct.unpack_from('<I', rom, p - BASE)[0] == 0x08017DA3 and struct.unpack_from('<I', rom, p - BASE + 0x10)[0] == 205)
    rec = bytearray(rom[old - BASE:old - BASE + 32])
    struct.pack_into('<I', rom, old - BASE + 4, condition(W, '    pushn 883\n    call not_flag\n    end\n'))
    wander = bytearray(rom[struct.unpack_from('<I', rec, 0x18)[0] - BASE:struct.unpack_from('<I', rec, 0x18)[0] - BASE + 16])
    struct.pack_into('<4H', wander, 8, HUB_AT[0], HUB_AT[1], HUB_AT[0], HUB_AT[1])
    struct.pack_into('<I', rec, 4, condition(W, '    pushn 883\n    call flag\n    end\n'))
    struct.pack_into('<I', rec, 8, HUB_AT[1] << 16 | HUB_AT[0])
    struct.pack_into('<I', rec, 0x10, 192)
    struct.pack_into('<I', rec, 0x18, W.put(bytes(wander)))
    struct.pack_into('<I', rom, e + 0x14, W.put(struct.pack('<%dI' % (count + 1), *ptrs, W.put(bytes(rec)))))
    rom[e + 4] = count + 1


def condition(W, text):
    import bfscript
    return W.put(bytes(bfscript.asm(text)))


def add_balls(W, rom, actor_ids, popo_list):
    """Each ball stands in its land's person list while you've no such ball and the ending has been seen."""
    for k, (world, area, x, y) in enumerate(BALLS):
        e = next(AREAS + 56 * q for q in range(COUNT) if rom[AREAS + 56 * q] == world and rom[AREAS + 56 * q + 1] == area)
        count = rom[e + 4]; lst = struct.unpack_from('<I', rom, e + 0x14)[0]
        ptrs = list(struct.unpack_from('<%dI' % count, rom, lst - BASE)) if count else []
        cond = condition(W, '    call flag(149)\n    call 0x7F(%d)\n    push 0\n    eq\n    and\n    end\n' % (BALL_ITEM + k))
        rec = W.put(struct.pack('<8I', 0x08017DA3, cond, y << 16 | x, popo_list, actor_ids['dragon_ball_%d' % (k + 1)] + 9, 1, 0x080716EC, 0))
        struct.pack_into('<I', rom, e + 0x14, W.put(struct.pack('<%dI' % (count + 1), *ptrs, rec)))
        rom[e + 4] = count + 1


def final_masks(P, proto_path, log2_path, cfg):
    """The collision as built: (masks, doors, reskinned rooms)."""
    masks = {a: floor_mask(P, proto_path, a) for a in range(1, 16)}
    doors = links(cfg, masks)
    res, _ = reskin.build_all(proto_path, log2_path, 'baserom.gba', masks=masks, doors=doors)
    for a, o in reskin.ROUND.items():
        if a >= 6: masks[a] = follow_outline(masks[a], o, doors.get(a, []))
    for a, c in reskin.COVER.items():
        m = masks[a].copy(); b = reskin.BARE[a]; bh, bw = b.shape[0] // 8, b.shape[1] // 8
        bare = b[:bh * 8, :bw * 8].reshape(bh, 8, bw, 8).mean((1, 3)) > 0.5
        m[:min(bh, m.shape[0]), :min(bw, 256)] |= bare[:min(bh, m.shape[0]), :min(bw, 256)]
        masks[a] = follow_outline(m, ~c, doors.get(a, []))
    return masks, doors, res


def apply(rom, clean, proto_path, log2_path, at, actor_ids=None, debug_door=False, quest_list=0, ending_list=0, popo_list=0):
    P = open(proto_path, 'rb').read()
    cfg = json.load(open('ultimate/zone26.json')); W = Writer(rom, at); rows = []; info = {}
    import music
    W.cur = music.port(rom, open(os.environ['BFU_COMBO'], 'rb').read()[0x800000:0x1000000], GLACIER_LOG2_SONG, W.cur, GLACIER_SONG)
    masks, doors, res = final_masks(P, proto_path, log2_path, cfg)
    boss_stats(W, rom, STATS)
    rush_rows(W, rom, debug_door)
    temp = bytes(rom[AREAS + 56 * [k for k in range(COUNT) if rom[AREAS + 56 * k] == 4 and rom[AREAS + 56 * k + 1] == 1][0]:][:56])
    for a, img in res.items():
        mask = masks[a]; audit(a, mask, doors.get(a, []))
        M, nt = build_map(W, P, a, img, np.packbits(mask.reshape(-1), bitorder='little')); info[a] = nt
        ent = bytearray(temp); ac = cfg['areas'].get(str(a), {})
        exits = []
        for d in doors.get(a, []):
            x0, y0, x1, y1 = d['rect']; ax, ay = d['arrive']
            dest = d['key'] | d.get('world', 26) << 8 | d['to'] << 16 | 1 << 24
            o = W.put(struct.pack('<2I4H2I', WARP[0], WARP[1], x0, y0, x1, y1, dest, ay << 16 | ax))
            param = 0
            if a == 14 and d['to'] == 15:                 # coming back mid-fight: straight to Super 13
                param = condition(W, '    pushn 884\n    call not_flag\n    pushn 886\n    call flag\n    or\n    end\n')
            exits.append((param, o))
            if a == 14 and d['to'] == 15:
                o2 = W.put(struct.pack('<2I4H2I', WARP[0], WARP[1], x0, y0, x1, y1, d['key'] | 26 << 8 | 17 << 16 | 1 << 24, ay << 16 | ax))
                exits.append((condition(W, '    pushn 884\n    call flag\n    pushn 886\n    call not_flag\n    and\n    end\n'), o2))
        objs = []
        for e in ac.get('enemies', []):
            objs.append(W.put(struct.pack('<8I', 0x0800FD55, (condition(W, e['script']) if 'script' in e else e.get('condition', 0)), e['row'], e['y'] << 16 | e['x'],
                                          actor_ids[e['actor']] + 9, 0x080555A0, 1, 0x080716EC)))
        struct.pack_into('<I', ent, 0, 26 | a << 8 | 1 << 16 | len(exits) << 24)
        struct.pack_into('<I', ent, 4, len(objs))
        struct.pack_into('<I', ent, 0xC, ac.get('name', GLACIER_NAME_UI))
        struct.pack_into('<I', ent, 0x10, W.put(b''.join(struct.pack('<II', *x) for x in exits)) if exits else 0)
        struct.pack_into('<I', ent, 0x14, W.put(b''.join(struct.pack('<I', o) for o in objs)) if objs else 0)
        struct.pack_into('<I', ent, 0x24, ac.get('music', GLACIER_SONG))
        struct.pack_into('<I', ent, 0x2C, W.put(struct.pack('<I', M + 4)))
        struct.pack_into('<I', ent, 0x30, 0)
        rows.append(bytes(ent))
        if a == 15:                                       # stages of the arena: same map and way out
            base_ent = bytes(ent)
            import bfscript
            for stage, spec in ((16, 'change'), (17, 'boss'), (18, 'scene')):
                st = bytearray(base_ent); struct.pack_into('<B', st, 1, stage)
                ring = W.put(struct.pack('<2I4HI', TRIGGER[0], TRIGGER[1], 0, 0, 1024, 1024, quest_list))
                if spec == 'boss':                        # no scene here: a dialogue box with this boss loaded resets the game
                    ex = exits
                    e = W.put(struct.pack('<8I', 0x0800FD55, 0, BOSS_ROW, 214 << 16 | 120, actor_ids['super13'] + 9, 0x080555A0, 1, 0x080716EC))
                    struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e)))
                else:
                    ex = [(0, ring)]
                    if spec == 'change':                  # walk up to Super 13 to start the fight
                        go = W.put(bytes(bfscript.asm('    call 0x78(20)\n    pushn 26, 17, 1, 120, 276\n    call 0x77\n    call 0x79(20)\n    end\n')))
                        ex.append((0, W.put(struct.pack('<2I4HI', 0x08007387, TRIGGER[1], 72, 226, 168, 258, go))))
                    struct.pack_into('<I', st, 4, 0); struct.pack_into('<I', st, 0x14, 0)
                st[3] = len(ex)
                struct.pack_into('<I', st, 0x10, W.put(b''.join(struct.pack('<II', *x) for x in ex)) if ex else 0)
                rows.append(bytes(st))
            for k, (_, char) in enumerate(RUSH):    # Boss Rush: one room per boss
                st = bytearray(base_ent); st[1] = RUSH_FIRST + k; struct.pack_into('<I', st, 0x24, MUSIC_FIELD)
                e = W.put(struct.pack('<8I', 0x0800FD55, 0, STATS_COUNT + k, 214 << 16 | 120, actor_ids[char] + 9 if isinstance(char, str) else char, 0x080555A0, 1, 0x080716EC))
                struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e)))
                st[3] = len(exits); struct.pack_into('<I', st, 0x10, W.put(b''.join(struct.pack('<II', *x) for x in exits)) if exits else 0)
                rows.append(bytes(st))
    stadium = next(rom[AREAS + 56 * q:AREAS + 56 * q + 56] for q in range(COUNT) if (rom[AREAS + 56 * q], rom[AREAS + 56 * q + 1]) == TOUR_ROOM)
    for k, (_, _, _, char) in enumerate(tour_list()):        # World Tournament: the stadium's own room, empty but for the opponent
        st = bytearray(stadium); st[0] = 26; st[1] = tour_first() + k; st[3] = 0
        e = W.put(struct.pack('<8I', 0x0800FD55, 0, STATS_COUNT + len(RUSH) + k, 366 << 16 | 360, actor_ids[char] + 9 if isinstance(char, str) else char, 0x080555A0, 1, 0x080716EC))
        struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e))); struct.pack_into('<I', st, 0x10, 0)
        rows.append(bytes(st))
    for k, (_, _, _, char, *_rest) in enumerate(TRIALS):          # Trials: the stadium's room again, empty but for the opponent
        st = bytearray(stadium); st[0] = 26; st[1] = trial_first() + k; st[3] = 0
        e = W.put(struct.pack('<8I', 0x0800FD55, 0, STATS_COUNT + len(RUSH) + len(tour_list()) + k, 366 << 16 | 360, char, 0x080555A0, 1, 0x080716EC))
        struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e))); struct.pack_into('<I', st, 0x10, 0)
        rows.append(bytes(st))
    white = next(rom[AREAS + 56 * q:AREAS + 56 * q + 56] for q in range(COUNT) if (rom[AREAS + 56 * q], rom[AREAS + 56 * q + 1]) == SPAR_ROOM)
    for k, (_, _, char) in enumerate(spar_list()):            # Time Chamber: its white room, empty but for the partner. Its story scene stays behind.
        st = bytearray(white); st[0] = 26; st[1] = spar_first() + k; st[3] = 0
        e = W.put(struct.pack('<8I', 0x0800FD55, 0, STATS_COUNT + len(RUSH) + len(tour_list()) + len(TRIALS) + k, 80 << 16 | 120, char, 0x080555A0, 1, 0x080716EC))
        struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e)))
        struct.pack_into('<I', st, 0x10, 0)
        rows.append(bytes(st))
    import mapimport
    l2 = open(os.environ['BFU_COMBO'], 'rb').read()[0x800000:]
    new_map, W.cur = mapimport.import_map(rom, l2, CELL_MAP, W.cur)       # LoG2 14:2, by where it sits in the combo cart. 14:4 has the final beam struggle painted on its ground, and 14:3 a layer class import_map can't convert
    struct.pack_into('<I', rom, new_map - BASE + 0x28, 0)      # no map sprites: with a 4 KB Cell in OBJ memory they turned to noise
    scene = W.put(struct.pack('<I', new_map + 4))
    base_row = STATS_COUNT + len(RUSH) + len(tour_list()) + len(TRIALS) + len(spar_list())
    fighters = cell_rows()
    for room in sorted({c[0] for c in fighters}):               # Cell Games: the LoG2 arena, empty but for the fighters
        st = bytearray(stadium); st[0] = 26; st[1] = room; st[3] = 0
        here = [W.put(struct.pack('<8I', 0x0800FD55, 0, base_row + k, c[6] << 16 | c[5], actor_ids[c[4]] + 9, 0x080555A0, 1, 0x080716EC)) for k, c in enumerate(fighters) if c[0] == room]
        st[4] = len(here); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<%dI' % len(here), *here))); struct.pack_into('<I', st, 0x10, 0)
        struct.pack_into('<I', st, 0x2C, scene); struct.pack_into('<I', st, 0x30, 0); struct.pack_into('<I', st, 0xC, CELL_NAME_UI)
        rows.append(bytes(st))
    house = bytearray(next(rom[AREAS + 56 * q:AREAS + 56 * q + 56] for q in range(COUNT) if (rom[AREAS + 56 * q], rom[AREAS + 56 * q + 1]) == BUILDING))
    n = house[3]; p = struct.unpack_from('<I', house, 0x10)[0] - BASE; ex = list(struct.unpack_from('<%dI' % (2 * n), rom, p)); changed = 0
    for i in range(n):
        o = ex[2 * i + 1] - BASE
        if struct.unpack_from('<I', rom, o)[0] == WARP[0]:
            r = bytearray(rom[o:o + 24]); struct.pack_into('<II', r, 16, 0 | 26 << 8 | 2 << 16 | 1 << 24, 124 << 16 | 188); ex[2 * i + 1] = W.put(bytes(r)); changed += 1
    if changed != 1: sys.exit('the house in room 2 changed: %d doors' % changed)
    house[0] = 26; house[1] = building_room(); struct.pack_into('<I', house, 0x10, W.put(struct.pack('<%dI' % (2 * n), *ex)))
    rows.append(bytes(house))
    tier_row = base_row + len(fighters)
    for tier in range(len(TIER_HP)):
        for k, (_, _, _, char) in enumerate(tour_list()):
            st = bytearray(stadium); st[0] = 26; st[1] = tier_first(tier + 1) + k; st[3] = 0
            e = W.put(struct.pack('<8I', 0x0800FD55, 0, tier_row, 366 << 16 | 360, actor_ids[char] + 9 if isinstance(char, str) else char, 0x080555A0, 1, 0x080716EC)); tier_row += 1
            struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e))); struct.pack_into('<I', st, 0x10, 0)
            rows.append(bytes(st))
    st = bytearray(stadium); st[0] = 26; st[1] = hercule_room(); st[3] = 0
    e = W.put(struct.pack('<8I', 0x0800FD55, 0, tier_row, 366 << 16 | 360, HERCULE_CHAR, 0x080555A0, 1, 0x080716EC))
    struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e))); struct.pack_into('<I', st, 0x10, 0)
    rows.append(bytes(st))
    fights = [(c, k, actor) for c in CHALLENGES for k, (actor, *_r) in enumerate(c['fights'])]
    for i, (c, k, actor) in enumerate(fights):
        st = bytearray(stadium if c['room'] == 'stadium' else white); st[0] = 26; st[1] = challenge_room(c['who'], k); st[3] = 0
        char = actor_ids[actor] + 9 if isinstance(actor, str) else actor
        e = W.put(struct.pack('<8I', 0x0800FD55, 0, tier_row + 1 + i, (366 << 16 | 360) if c['room'] == 'stadium' else (80 << 16 | 120), char, 0x080555A0, 1, 0x080716EC))
        struct.pack_into('<I', st, 4, 1); struct.pack_into('<I', st, 0x14, W.put(struct.pack('<I', e))); struct.pack_into('<I', st, 0x10, 0)
        rows.append(bytes(st))
    hub_person(W, rom)
    add_balls(W, rom, actor_ids, popo_list)
    if debug_door:          # debug: on Snake Way, Down on the very spot you start reaches 26:1 and the rest of the road stays walkable; x 48-96 walk up reaches Broly; x<48 starts the ending
        e = next(AREAS + 56 * k for k in range(COUNT) if rom[AREAS + 56 * k] == 1 and rom[AREAS + 56 * k + 1] == 1)
        o = W.put(struct.pack('<2I4H2I', WARP[0], WARP[1], *DEBUG_SPOT, 0 | 26 << 8 | 1 << 16 | 1 << 24, 200 << 16 | 120))
        old = rom[e + 3]; ptr = struct.unpack_from('<I', rom, e + 0x10)[0]
        list_ = bytes(rom[ptr - BASE:ptr - BASE + 8 * old]) if old else b''
        o2 = W.put(struct.pack('<2I4H2I', WARP[0], WARP[1], 48, 0, 96, 1024, 1 | 15 << 8 | 32 << 16 | 1 << 24, 290 << 16 | 224))   # x 48-96, walk up: story Broly
        o3 = W.put(struct.pack('<2I4HI', TRIGGER[0], TRIGGER[1], 0, 0, 48, 1024, ending_list))   # stand at x<48: the ending from step 67 (build.py makes step 1 jump there)
        struct.pack_into('<I', rom, e + 0x10, W.put(list_ + struct.pack('<IIIIII', 0, o, 0, o2, 0, o3))); rom[e + 3] = old + 3
    n = COUNT + len(rows); tab = W.put(bytes(rom[AREAS:AREAS + 56 * COUNT]) + b''.join(rows))
    struct.pack_into('<I', rom, TABLE_LIT, tab)
    a_ = min(0xFF, n // 2)
    struct.pack_into('<4H', rom, COUNT_INSN, 0x2000 | a_, 0x0040, 0x3000 | (n - 2 * a_), 0x4770)
    return W.cur, info
