"""Teen Gohan in Goku's gi from Bojack Unbound (Nov 14, the owner's pictures; "Just take the exact outfit because Goku is honestly
slightly taller and I dont want proportions off"; on Goku's shortened sprite, 14:01: "his fucking neck is invisible, his head randomly
fucking bobbing ... random shading on clothing moving around, random pixels turning invisible"; approved 16:29: "Finally lock that in").
Teen Gohan's own frames as teen.py makes them (the purple gi with his Super Saiyan and Super Saiyan 2 heads), every pixel where it is: only
the colours of his clothes change, to Goku's own LoG2 gi colours (r57). Base is the Super Saiyan frame with the hair black, shaded as
LoG2's black hair is (black(); the owner: "his base hair is the same as his ssj1 hair just black", "not FULLY MATTE BLACK"); Super
Saiyan 2's hair has no brown outline (no_outline(); the owner, 12:41).
  his white undershirt and the purple of his gi above the sash: Goku's orange (lightest to darkest as they are), with the navy V of
    Goku's undershirt under his neck, as Goku's sprite draws it (three pixels, then one: 50 4f d7 / 50);
  the gi's navy edge on his top (its shoulders and the edges round the undershirt): Goku's navy sleeves;
  the reds of his sash and wristbands: Goku's navy;
  his purple trousers: Goku's orange, their navy edge Goku's darkest orange (a leg swung up included);
  the greys of his socks and shoes: Goku's navy boots (their black stays).
Everything is in LoG2 colour indices on teen.py's canvas. frame() makes a look's frame and checks it (problems()): his outline the same
pixel for pixel, nothing but his clothes changed (and the base hair's black, Super Saiyan 2's hair outline), none of the purple gi's
colours left on his clothes. A frame that fails stops the build. made(look) is sprites.log2_anim's frame source for the look's figure."""
import numpy as np
from scipy import ndimage
import teen as T, headfit as F

GOLD = F.cls(T.GOLD_S)
WHITE = 0x02
GREYS = (0x02, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e)
REDS = (0x18, 0x19, 0x1a, 0x1b)
PURPLES = (0x50, 0x51)
EDGE = 0xd3
SHIRT_TO = {0x02: 0x20, 0x09: 0x20, 0x0a: 0x20, 0x0b: 0x21, 0x0c: 0x21, 0x0d: 0x22, 0x0e: 0x23}     # undershirt greys -> Goku's orange
RED_TO = {0x18: 0x4f, 0x19: 0x4f, 0x1a: 0x50, 0x1b: 0x51}                                           # sash, wristbands -> navy
DARK = 0x0f                                                                                          # a shoe's darkest grey
BOOT_TO = {0x02: 0x4f, 0x09: 0x4f, 0x0a: 0x4f, 0x0b: 0x50, 0x0c: 0x50, 0x0d: 0x51, 0x0e: 0x51, DARK: 0xd7}   # socks, shoes -> navy
VEE = ((0x50, 0x4f, 0xd7), (0x50,))                                                                  # Goku's V, front idle rows -8, -7
NECK = 0x17


def n4(m):
    return F.shift(m, 0, 1) | F.shift(m, 0, -1) | F.shift(m, 1, 0) | F.shift(m, -1, 0)


def steps(seed, mask):
    """4-connected steps through mask from seed (inf where it can't reach)."""
    d = np.full(mask.shape, np.inf); front = seed & mask; seen = front.copy(); d[front] = 0; k = 0
    while front.any():
        k += 1; front = n4(front) & mask & ~seen; seen |= front; d[front] = k
    return d


_notes = {}
def head_mask(form, k, d, f, done):
    """The head teen.py put on the frame (the Super Saiyan armor record's head where it lies on it); none where the frame is the
    purple record's own (knocked down: LoG2 draws him black-haired)."""
    key = (form, k, d, 0 if (form == 'ss2' and k == 0) else f)          # (the stance's later frames are its frame 0, blinking)
    if key not in _notes:
        try: _notes[key] = T.MAKERS[form](*key[1:])
        except T.Off: _notes[key] = None
    if _notes[key] is None: return np.zeros(done.shape, bool)
    out, n = _notes[key]
    if n.get('plain'): return np.zeros(done.shape, bool)
    src = n['s2'] if form == 'ss2' else n['s']
    rect = T.head_rect(n['a'], src) if GOLD[src].any() else n['rect']
    if form == 'ss2':
        r1 = n['rect']; rect = (min(rect[0], r1[0]), max(rect[1], r1[1]), min(rect[2], r1[2]), max(rect[3], r1[3]))
    hs = T.head_of(src) & T.box_of(done.shape, rect, 1, 1) & (done != 0)
    # (never his clothes where they lie over that head's place: his gi's purples and navy, the reds of a wristband held up, and a grey
    # that is no light of his hair or white of an eye)
    hs &= ~(np.isin(done, GREYS) & (done != src))                      # (a grey the head's frame hasn't there is the purple frame's own: his collar, a shoe)
    hg = hs & np.isin(done, GREYS)
    keep_grey = F.flood(hg & F.grown(GOLD[done] | F.cls({0x40, 0x41, 0x31, 0x32}, T.SKIN_S)[done], 1), hg, True)   # (and the lights
    hs &= ~(np.isin(done, REDS + PURPLES + (EDGE,)) | (np.isin(done, GREYS) & ~keep_grey))
    # the whites of his eyes, wherever teen.py's head ends: grey and white beside an iris, and what hangs on those inside his face
    iris = F.cls({0x40, 0x41, 0x31, 0x32})[done]
    eyes = np.isin(done, GREYS) & F.grown(iris, 1)
    return hs | eyes


def teen_frame(form, k, d, f):
    """teen.py's frame (k, d, f) of the purple gi the look recolours: Super Saiyan 2's for Super Saiyan 2, the Super Saiyan's for base
    and Super Saiyan."""
    return T.frame('ss2' if form == 'ss2' else 'ss', k, d, f)


def black(c, head):
    """Base: the Super Saiyan head with the hair black, shaded as LoG2's black hair is (the owner, Nov 14, 16:23: "base SSJ1 hair shape
    just BLACK like normal not FULLY MATTE BLACK"): its gold and brown outline black (0x01), its white lights LoG2's dark grey hair light
    (0x0f, as the purple record's own black hair has them: about one pixel in ten), every light of the gold (white that hangs together with
    white beside the gold; one two pixels in from the gold had stayed white, a stray in the walk). His own dark eyes. Nothing else of
    the head changes (the skin the gold shows between its locks stays, as the Super Saiyan head draws it)."""
    out = c.copy()
    gold = head & GOLD[c]
    lights = F.flood(head & (c == WHITE) & F.grown(gold, 1), head & (c == WHITE), True)
    out[gold | (head & (c == 0x14))] = 0x01
    out[lights] = 0x0f
    out[head & (c == 0x40)] = 0x01; out[head & (c == 0x41)] = 0x0f
    return out


def no_outline(c, head):
    """Super Saiyan 2 hair without its brown outline (the owner, 12:41): the hair's brown that doesn't touch his face goes its darkest
    gold (BF 248)."""
    out = c.copy(); skin = F.cls(T.SKIN_S, {0x16})[c]
    out[head & (c == 0x14) & ~(skin | n4(skin))] = 0x26
    return out


def collar(c, head):
    """The greys of his collar that teen.py's head reaches over at his nape (seen from behind): head greys (never white, the hair's
    light and the eyes') against his clothes, and the greys beside those."""
    cloth = np.isin(c, GREYS + PURPLES + (EDGE,)) & ~head
    g = head & np.isin(c, GREYS[1:]) & ~F.grown(GOLD[c] | np.isin(c, (0x40, 0x41, 0x31, 0x32)), 1)
    m = g & n4(cloth)
    for _ in range(2): m |= g & n4(m)
    return m


def vee(c, shirt, head):
    """Goku's V under his neck: under the longest run of the neck's shadow (his neck's brown with undershirt right under it), the
    three pixels under its middle, then the one under those, where his undershirt is."""
    neck = (c == NECK) & F.shift(shirt, 0, -1)
    out = []
    best = None
    for y in np.nonzero(neck.any(1))[0]:
        xs = np.nonzero(neck[y])[0]
        for run in np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1):
            if best is None or len(run) > len(best[1]): best = (y, run)
    if best is None or len(best[1]) < 3: return out
    y, run = best; mid = int(round((run[0] + run[-1]) / 2))
    for i, row in enumerate(VEE):
        for j, col in enumerate(row):
            x = mid - len(row) // 2 + j
            if shirt[y + 1 + i, x]: out.append((y + 1 + i, x, col))
    return out


TORSO = 3                              # rows of his gi's top under his head (front idle: collar -6 to -4 under the chin at -7)


def split(c, head):
    """-> (his upper body, his lower body): the rows down to TORSO under his head, and the rest. Knocked down (no head of teen.py's:
    the purple record's own frame, his long black hair on the ground), the same along his body from his hair."""
    body = (c != 0) & ~head
    if head.any():
        hb = np.nonzero(head.any(1))[0].max()
        up = np.zeros(c.shape, bool); up[:hb + TORSO + 1] = True
        return body & up, body & ~up
    lab, n = ndimage.label(c == 0x01, np.ones((3, 3)))
    skin = F.grown(F.cls(T.SKIN_S)[c], 1)
    hair = None
    for i in range(1, n + 1):
        m = lab == i
        if (m & skin).any() and (hair is None or m.sum() > hair.sum()): hair = m
    if hair is None: return body, np.zeros(c.shape, bool)
    hy, hx = np.argwhere(hair).mean(0); by, bx = np.argwhere(body & ~hair).mean(0)
    ys, xs = np.indices(c.shape)
    if abs(bx - hx) > abs(by - hy):                    # (lying: along the row)
        edge = np.nonzero(hair.any(0))[0]
        up = (xs <= edge.max() + TORSO + 1) if bx > hx else (xs >= edge.min() - TORSO - 1)
    else:
        up = ys <= np.nonzero(hair.any(1))[0].max() + TORSO + 1
    return body & up & ~hair, body & ~up & ~hair


def parts(form, k, d, f):
    """Frame (k, d, f) of a look ('base', 'ss', 'ss2') taken apart: -> dict of the purple gi's frame ('done'), its head ('head'), the
    frame with the look's head ('c': base's black hair, Super Saiyan 2's without its outline) and his clothes: 'shirt' (the greys of his
    top), 'boots' (socks and shoes), 'upper' and 'lower' (his body down to TORSO rows under his head, and the rest), 'legs' (his gi's
    edge on a leg swung up), 'body' (upper | lower). make() dresses them in Goku's colours; another look (trunkten.py) in its own."""
    tf = 'ss2' if form == 'ss2' else 'ss'
    done = teen_frame(form, k, d, f)
    head = head_mask(tf, k, d, f, done)
    head &= ~collar(done, head)
    c = done.copy()
    if form == 'base' and head.any(): c = black(c, head)
    if form == 'ss2' and head.any(): c = no_outline(c, head)
    upper, lower = split(done, head)
    # his undershirt's greys and his socks' and shoes': a piece of grey with his figure round most of it (the undershirt inside his
    # gi, the socks between his trousers and shoes, the lights inside a shoe) is clothing: his socks and shoes where it touches the
    # black of his shoes (their outline and sole, his shadow), else his undershirt. A piece mostly in the open (dizzy stars, a swoosh,
    # a spark) is none of his clothes: it stays as it is.
    # (white by itself is a swoosh, a star, a spark: only a white pixel or two set in the greys of a piece of clothing is its light)
    body_ = upper | lower
    wl, wn = ndimage.label((done == WHITE) & body_, np.ones((3, 3)))
    small_white = np.isin(wl, [i for i in range(1, wn + 1) if (wl == i).sum() <= 2])
    grey = np.isin(done, GREYS[1:] + (DARK,)) & body_
    grey |= small_white & n4(grey)
    lab, n = ndimage.label(grey, np.ones((3, 3)))
    soles = (done == 0x01) & ~head
    if not head.any():                                 # (knocked down: his long black hair is no shoe)
        hl, hn = ndimage.label(soles, np.ones((3, 3)))
        skin = F.grown(F.cls(T.SKIN_S)[done], 1)
        for i in range(1, hn + 1):
            if ((hl == i) & skin).any(): soles &= hl != i
    trousers = lower & np.isin(done, PURPLES + (EDGE,))
    under = F.shift(trousers, 0, 1)                    # (right under his trousers: his socks)
    hair = GOLD[done] | (done == 0x14)
    boots = np.zeros(done.shape, bool); shirt = np.zeros(done.shape, bool)
    for i in range(1, n + 1):
        m = lab == i; ring = F.grown(m, 1) & ~m
        white = (done[m] == WHITE).all()
        if white and (m.sum() >= 3 or (ring & GOLD[done]).any()): continue   # (a swoosh round his arm: pure white)
        shoe = (ring & soles).any() or (m & under).any()
        if (ring & (done != 0)).sum() < 0.5 * ring.sum():
            # in the open: a dizzy star, a swoosh, a spark (white) stays as it is; grey against his shoes' black or his gi is
            # the shoe of a leg he swings out, and grey against his hair from outside his head the shoes behind it (flying at you)
            if white: continue
            if shoe or (ring & np.isin(done, PURPLES + (EDGE,))).any() or ((ring & hair).any() and not (done[m] == WHITE).any()): boots |= m
            continue
        if shoe: boots |= m
        else: shirt |= m                               # (his long hair's dark lights stay: DARK is no undershirt colour)
    # his gi's navy edge: Goku's navy sleeves on his top, his trousers' darkest orange on his legs. Which it is goes by the rows under
    # his head, except for a leg he swings up beside his body: an edge nearer his shoes than his undershirt, through his gi, is his
    # trousers' wherever it is.
    gi = np.isin(done, PURPLES + (EDGE,)) & body_
    dt = steps(gi & upper & F.grown(shirt & upper, 1), gi)
    dl = steps(gi & F.grown(boots, 1), gi)
    legs = gi & upper & (dl < dt)
    return dict(done=done, head=head, c=c, shirt=shirt, boots=boots, upper=upper, lower=lower, legs=legs, body=body_)


def make(form, k, d, f):
    """Frame (k, d, f) of the look ('base', 'ss', 'ss2') on teen.py's canvas, in LoG2 colour indices."""
    p = parts(form, k, d, f)
    done, head, c, shirt, boots, upper, lower, legs, body_ = (p[n] for n in ('done', 'head', 'c', 'shirt', 'boots', 'upper', 'lower', 'legs', 'body'))
    out = c.copy()
    for a, b in SHIRT_TO.items(): out[shirt & (done == a)] = b
    for a, b in BOOT_TO.items(): out[boots & (done == a)] = b
    for a, b in RED_TO.items(): out[done == a] = b
    out[body_ & (done == 0x50)] = 0x20
    out[body_ & (done == 0x51)] = 0x21
    out[upper & ~legs & (done == EDGE)] = 0x50          # (the gi's edge round his undershirt and his shoulders: Goku's navy sleeves)
    out[(lower | legs) & (done == EDGE)] = 0x23         # (his trousers' edge: Goku's darkest orange)
    for y, x, col in vee(done, shirt, head): out[y, x] = col
    return out

CLOTH = set(GREYS) | set(REDS) | set(PURPLES) | {EDGE}
GI_OUT = (0x20, 0x21, 0x22, 0x23, 0x4f, 0x50, 0x51, 0xd7)                 # Goku's gi colours, in a frame made


def problems(form, k, d, f, out):
    """What is wrong with a made frame, against the purple gi's frame with this look's head: his outline changed; a pixel that isn't his
    clothes changed, or one of his head; the purple gi's colours left on him (its reds and navy edge, a grey of its left against Goku's
    colours: clothing missed, never a swoosh round his arm or a light of his hair); a shoe's darkest grey made anything but Goku's navy
    outline beside his boots; his hair's white lights changed."""
    tf = 'ss2' if form == 'ss2' else 'ss'
    done = teen_frame(form, k, d, f)
    head = head_mask(tf, k, d, f, done); head &= ~collar(done, head)
    ref = done.copy()
    if form == 'base' and head.any(): ref = black(ref, head)
    if form == 'ss2' and head.any(): ref = no_outline(ref, head)
    bad = []
    o = (out != 0) != (done != 0)
    if o.any(): bad.append('outline changed %d' % o.sum())
    cloth = np.isin(done, list(CLOTH))
    navy = np.isin(out, (0x4f, 0x50, 0x51, 0xd7, 0x01))
    dark = (done == DARK) & ~head
    x = dark & (out != done) & ((out != 0xd7) | ~F.grown(navy & ~dark, 1))
    if x.any(): bad.append('dark grey made something else %d' % x.sum())
    cloth |= dark & (out == 0xd7)
    x = (out != ref) & ~cloth
    if x.any(): bad.append('non-clothes changed %d' % x.sum())
    x = (out != ref) & head
    if x.any(): bad.append('head changed %d' % x.sum())
    gi_out = np.isin(out, GI_OUT)
    lab, nn = ndimage.label(np.isin(out, GREYS + (DARK,)) & ~head, np.ones((3, 3)))
    left = np.zeros(out.shape, bool)
    for i in range(1, nn + 1):
        m = lab == i; ring = F.grown(m, 1) & ~m
        white = (out[m] == WHITE).all() and (m.sum() >= 3 or (ring & GOLD[out]).any())
        if not white and (ring & (out != 0)).sum() >= 0.5 * ring.sum() and (ring & gi_out).any(): left |= m
        if not (out[m] == WHITE).any() and (ring & gi_out).any(): left |= m
    left |= ~head & (np.isin(out, REDS + (EDGE,)) | ((done == 0x01) & (out != 0x01)))
    if left.any(): bad.append('purple gi colours left %d' % left.sum())
    lights = F.flood(GOLD[done], GOLD[done] | (done == WHITE), True) & ~GOLD[done]
    x = lights & (out != ref)
    if x.any(): bad.append('hair lights changed %d' % x.sum())
    return bad


LOOKS = ('base', 'ss', 'ss2')
_made = {}
def frame(form, k, d, f):
    """Frame (k, view d, f) of the look, made and checked: -> its canvas. Off if it fails a check."""
    if (form, k, d, f) not in _made:
        out = make(form, k, d, f); bad = problems(form, k, d, f, out)
        if bad: raise T.Off("Teen Gohan in Goku's gi, %s, animation %d view %d frame %d: %s" % (form, k, d, f, '; '.join(bad)))
        _made[form, k, d, f] = out
    return _made[form, k, d, f]


def anims(form): return T.ANIMS['ss2' if form == 'ss2' else 'ss']


def every():
    """Every frame the build uses of the three looks, made and checked. -> how many; Off on the first that isn't right."""
    n = 0
    for form in LOOKS:
        for k in anims(form):
            for d in range(T.views(k)):
                for f in range(T.L.nframes(T.REC['P'], k)): frame(form, k, d, f); n += 1
    return n


def made(form):
    """sprites.log2_anim's frame source for the look's figure (teen.made, with this look's frames)."""
    return T.made('ss2' if form == 'ss2' else 'ss', canvas=lambda k, d, f: frame(form, k, d, f), anims=anims(form))
