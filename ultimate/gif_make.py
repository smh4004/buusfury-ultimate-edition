"""gif_make.py RAWDIR OUT.gif COLS name[,name...]  : a grid of panels, one per form gif_cap.py captured, each looping its clips with a caption
(env BOX 'x0,y0,x1,y1' the crop, Z the zoom, HOLD frames held at each clip's end)."""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont
RAW, OUT, COLS = sys.argv[1], sys.argv[2], int(sys.argv[3]); names = sys.argv[4].split(',')
BOX = tuple(int(v) for v in os.environ.get('BOX', '0,22,176,118').split(',')); Z = int(os.environ.get('Z', '2')); HOLD = int(os.environ.get('HOLD', '6'))
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
pw, ph = (BOX[2] - BOX[0]) * Z, (BOX[3] - BOX[1]) * Z + 20
panels = []
for n in names:
    d = os.path.join(RAW, n); meta = json.load(open(d + '/clips.json')); frames = []
    for c in meta['clips']:
        for k in range(c['frames']):
            p = '%s/%s_%03d.png' % (d, c['tag'], k)
            if not os.path.exists(p): continue
            im = Image.open(p).convert('RGB').crop(BOX).resize(((BOX[2] - BOX[0]) * Z, (BOX[3] - BOX[1]) * Z), Image.NEAREST)
            fr = Image.new('RGB', (pw, ph), (26, 26, 30)); fr.paste(im, (0, 20))
            ImageDraw.Draw(fr).text((4, 2), '%s: %s' % (meta['label'], c['move']), fill=(255, 214, 102), font=F)
            frames.append(fr)
        frames += [frames[-1]] * HOLD
    panels.append(frames)
rows = (len(panels) + COLS - 1) // COLS; total = max(len(p) for p in panels)
out = []
for t in range(total):
    fr = Image.new('RGB', (COLS * (pw + 4) - 4, rows * (ph + 4) - 4), (0, 0, 0))
    for i, p in enumerate(panels): fr.paste(p[t % len(p)], ((i % COLS) * (pw + 4), (i // COLS) * (ph + 4)))
    out.append(fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
out[0].save(OUT, save_all=True, append_images=out[1:], duration=40, loop=0, optimize=False, disposal=1)
print(OUT, out[0].size, len(out), 'frames', os.path.getsize(OUT) // 1024, 'KB')
