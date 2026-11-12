"""Every Super Saiyan 4 figure, every frame of every move in all three views (no frame left out, none merged with another that looks
the same), so the owner can check each one (Nov 12 08:11: "dont even touch the others just send previews of every SSJ4 form").
Nothing here changes a figure; it only draws them.
  goku    Super Saiyan 4 Goku as the preview has him (plainback.fixed: the arms, plain back, heads and legs; not in the game yet);
          the charged punch (slots 22, 23) as the game has it          BFU_GOG_ROM=<debug build>
  daima   Daima Super Saiyan 4 Goku, the saved preview (v4.frame(..., 'daima_pic'); in no build)
                                                                       BFU_SSJ4_ROM=<a build from before the touch-up>
  gogeta  Super Saiyan 4 Gogeta as the game has him                    BFU_GOG_ROM=<debug build>
  vegeta  GT Vegeta's Super Saiyan 4 as the game has him (the tank-top look's Super Saiyan 4 uses the same figure)
                                                                       BFU_GOG_ROM=<debug build>
  python3 ultimate/ssj4_preview/allforms.py <which> <out dir>
-> <out>/ssj4_<which>_every_frame.pdf (a page per move: its frames left to right, front, back and side top to bottom) and
   <out>/ssj4_<which>_every_move.gif (each move played twice, front, back and side side by side)."""
import os, sys, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'gogeta_preview')]
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MOVE = {0: 'standing', 1: 'walk', 2: 'run', 3: 'ki blast', 4: 'combo 1', 5: 'combo 2', 6: 'finisher', 7: 'guard', 8: 'charging',
        9: 'hit', 10: 'powering up', 11: 'costume out', 12: 'victory', 13: 'power-up', 14: 'jump', 15: 'flying', 16: 'spin',
        17: 'knocked down', 18: 'getting up', 19: 'costume in', 20: 'burst', 21: 'special', 22: 'charged punch, part 1',
        23: 'charged punch, part 2'}
VIEW = ('front', 'back', 'side')
BG = (88, 120, 88); DARK = (30, 40, 30); WHITE = (255, 255, 255)


def source(which):
    """-> (title, note, R, slots {slot: frames}, frame(slot, f, view) -> 96x96 indices, note per slot)"""
    if which == 'daima':
        import v4
        R, aid = v4.R, v4.AID
        slots = {s: n for s, n in R.slots(aid).items() if s < 22}
        return ('Daima Super Saiyan 4 Goku', 'the saved preview (not in the game), as it was saved: nothing changed', R, slots,
                lambda s, f, d: v4.frame(s, f, d, 'daima_pic'), {})
    from frames import R
    rom = os.environ.get('BFU_GOG_ROM', 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba')
    forms = json.load(open(rom.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
    aid = lambda n: struct.unpack_from('<H', R.rom, 0x800000 + 24 * forms[n] + 0x0E)[0] - 9
    if which == 'goku':
        import plainback as P
        a = aid('kid_goku_ssj4')
        def frame(s, f, d): return P.fixed((s, f, d)) if s < 22 else R.frame(a, s, f, d)
        late = 'as the game has it: still BF Goku\'s own frames (not done yet)'
        return ('Super Saiyan 4 Goku', 'the preview with every fix so far (not in the game yet)', R, R.slots(a), frame,
                {22: late, 23: late})
    if which == 'gogeta':
        a = aid('gogeta_ssj4')
        return ('Super Saiyan 4 Gogeta', 'as the game has him now: nothing changed', R, R.slots(a),
                lambda s, f, d: R.frame(a, s, f, d), {})
    a = aid('vegeta_gt_ssj4')
    assert a == aid('vegeta_gt_tank_ssj4')
    return ('GT Vegeta, Super Saiyan 4 (also his tank-top look\'s)', 'as the game has him now: nothing changed', R, R.slots(a),
            lambda s, f, d: R.frame(a, s, f, d), {})


def main(which, out):
    os.makedirs(out, exist_ok=True)
    title, note, R, slots, frame, late = source(which)
    pics = {(s, f, d): frame(s, f, d) for s in sorted(slots) for f in range(slots[s]) for d in range(3)}
    on = np.zeros((96, 96), bool)
    for c in pics.values(): on |= c != 0
    ys, xs = np.nonzero(on); box = (max(ys.min() - 2, 0), min(ys.max() + 3, 96), max(xs.min() - 2, 0), min(xs.max() + 3, 96))
    H, W = box[1] - box[0], box[3] - box[2]

    def rgb(c):
        c = c[box[0]:box[1], box[2]:box[3]]; im = R.rgb(c).copy(); im[c == 0] = BG; return im

    # the pages
    z = 4; per = 6; left = 70; F = ImageFont.load_default(size=16); FT = ImageFont.load_default(size=22); FS = ImageFont.load_default(size=15)
    pages = []
    for s in sorted(slots):
        n = slots[s]; chunks = [list(range(i, min(n, i + per))) for i in range(0, n, per)]
        top = 70; band = 22
        hgt = top + len(chunks) * (band + 3 * (H * z + 6) + 14)
        img = Image.new('RGB', (left + per * (W * z + 6), hgt), DARK); d = ImageDraw.Draw(img)
        d.text((10, 8), '%s: %s (%d frame%s)' % (title, MOVE.get(s, 'slot %d' % s), n, '' if n == 1 else 's'), fill=WHITE, font=FT)
        d.text((10, 38), late.get(s, note), fill=(255, 230, 140), font=FS)
        y = top
        for ch in chunks:
            for j, f in enumerate(ch):
                d.text((left + j * (W * z + 6) + 4, y + 2), 'frame %d' % (f + 1), fill=WHITE, font=F)
            y += band
            for v in range(3):
                d.text((8, y + H * z // 2 - 8), VIEW[v], fill=WHITE, font=F)
                for j, f in enumerate(ch):
                    im = Image.fromarray(rgb(pics[s, f, v])).resize((W * z, H * z), Image.NEAREST)
                    img.paste(im, (left + j * (W * z + 6), y))
                y += H * z + 6
            y += 14
        pages.append(img)
    pages[0].save(out + '/ssj4_%s_every_frame.pdf' % which, save_all=True, append_images=pages[1:], resolution=96)

    # the animation
    z = 5; band = 24; frames = []; durs = []
    for s in sorted(slots):
        n = slots[s]
        for _ in range(2):
            for f in range(n):
                img = Image.new('RGB', (3 * W * z + 8, band + 18 + H * z), DARK); d = ImageDraw.Draw(img)
                d.text((6, 4), '%s, frame %d of %d' % (MOVE.get(s, 'slot %d' % s), f + 1, n), fill=WHITE, font=FS)
                for v in range(3):
                    d.text((v * (W * z + 4) + 4, band), VIEW[v], fill=WHITE, font=FS)
                    img.paste(Image.fromarray(rgb(pics[s, f, v])).resize((W * z, H * z), Image.NEAREST), (v * (W * z + 4), band + 18))
                frames.append(img); durs.append(400 if n <= 2 else 160)
    frames[0].save(out + '/ssj4_%s_every_move.gif' % which, save_all=True, append_images=frames[1:], duration=durs, loop=0)
    print(which, len(slots), 'moves,', len(pics), 'frames (all views), box', box)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
