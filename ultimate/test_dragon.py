#!/usr/bin/env python3
"""Dragon Ball hunt: lands at each of the seven lands after the real ending, walks to the ball and takes it; then, holding all seven, talks to Mr. Popo,
summons the dragon and tries each wish. Build `--debug --zone` first.
  python3 ultimate/test_dragon.py [work dir]"""
import sys
src = open('ultimate/test_story.py').read().split("land = e + move(p3, 1250, 1200)")[0]
exec(src)
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
import bench as BN                                         # the guest bench (lib/bench.py)
from PIL import Image
ITEMS = 0x03001068 + 2 + zone26.BALL_ITEM            # the inventory's byte array
LAND = {5: (2888, 1684), 7: (2024, 2120), 8: (864, 1796), 11: (1576, 1064), 13: (792, 876), 15: (2196, 892), 14: (2192, 1212)}
fly = lambda x, y: e + move(p3, x, y) + ['run 4', 'tap A 100', 'run 60', 'keys A', 'run 300', 'keys', 'run 100']
W = Image.new('RGB', (5 * 240, 3 * 160)); cell = [0]
# The flight map's mini-map marks every place you can land (outfit.c minimap_draw): a yellow diamond with a white centre at each.
out = run(e + ['run 30', 'shot flightmap'])
fm = Image.open('%s/flightmap.png' % d).convert('RGB')
src = open('ultimate/build.py').read(); ns = {'struct': struct, 'ROM_BASE': 0x08000000, 'sys': sys}
exec(src[src.index('def map_marks'):src.index('def add_outfits')], ns)
marks = ns['map_marks'](open('baserom.gba', 'rb').read())
lit = sum(1 for x, y in marks if fm.getpixel((x + 3, y + 3))[0] > 200 and fm.getpixel((x + 3, y + 3))[1] > 200)
print('   map markers drawn: %d of %d' % (lit, len(marks)))
check('the flight map marks every place you can land', lit == len(marks) and 'bad pc' not in out)
fm.resize((480, 320)).save(d + '/flightmap_x2.png')
def paste(name):
    W.paste(Image.open('%s/%s.png' % (d, name)).convert('RGB'), (cell[0] % 5 * 240, cell[0] // 5 * 160)); cell[0] += 1
for k, (world, area, x, y) in enumerate(zone26.BALLS):
    l = fly(*LAND[world]) + ['mem 0300197C 1']
    out = run(l); check('landing in land %d' % world, at(out) == (area << 8 | world))
    pl = ptr(l)
    walk = l + move(pl, x, y + 22) + ['run 40', 'shot ball%d_a' % k, 'run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 60', 'run 120', 'shot ball%d_b' % k, 'tap A 40', 'run 100', 'shot ball%d_c' % k, 'mem %08X 1' % (ITEMS + k & ~3), 'mem 0300197C 1']
    out = run(walk); m = [l_ for l_ in out.splitlines() if l_.startswith('mem %08x' % (ITEMS + k & ~3))]
    got = int(m[-1].split(':')[1].split()[0], 16) >> (8 * ((ITEMS + k) & 3)) & 255
    check('ball %d is found' % (k + 1), got == 1 and 'bad pc' not in out)
    paste('ball%d_a' % k); paste('ball%d_c' % k)
W.save(d + '/balls.png')
# Master Roshi on his island (land 5) joins once the story is over: his question, the join, then his line for later.
l = fly(*LAND[5]) + ['mem 0300197C 1']; pl = ptr(l)
talk = l + move(pl, 392, 398) + ['run 40', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 60', 'run 60', 'shot roshi_ask', 'tap A 40', 'run 60', 'shot roshi_joined', 'tap A 40', 'run 60', 'mem %08X 1' % BN.FLAGS, 'tap A 40', 'run 60', 'shot roshi_ready', 'tap A 40', 'run 60', 'dump g 03001068 8a8']
out = run(talk); g = open(d + '/g.bin', 'rb').read()
bench = [int(x.split(':')[1].split()[0], 16) for x in out.splitlines() if x.startswith('mem %08x' % BN.FLAGS)]
check('Master Roshi joins at Kame House after the ending', bench and bench[-1] >> 31 & 1 and 'bad pc' not in out)
check('and gives his Turtle Shell', 165 in [struct.unpack_from('<I', g, 0xE8 + 4 * i)[0] & 0xFFFFFFF for i in range(min(g[0xE4], 250))])
# Summon: hold all seven, land at the Lookout, talk to Mr. Popo.
pokes = ['poke8 %08X 01' % (ITEMS + k) for k in range(7)]
look = fly(648, 1076) + pokes + ['mem 0300197C 1']
out = run(look); check('at the Lookout', at(out) == (1 << 8 | 6))
pl = ptr(look)
start_ = look + move(pl, 288, 494) + ['run 2', 'keys UP', 'run 6', 'keys', 'run 4', 'tap A 80', 'run 180', 'shot sum1', 'tap A 20', 'run 500', 'shot sum2', 'tap A 20', 'run 180', 'shot wish']
before = run(start_ + ['dump g 03001068 8a8']); g0 = open(d + '/g.bin', 'rb').read()
page = lambda downs: ['tap DOWN 12'] * downs + ['tap A 20', 'run 180']          # a line of the dragon's menu; a page's menu shows after its text
MORE = page(3)
WISHES = {'power': page(0), 'rich': page(1), 'fighters': page(2), 'ss2': MORE + page(0), 'potential': MORE + page(2),
          'potara': MORE + page(1) + ['shot treasure'] + page(0), 'pouch': MORE + page(1) + page(3)}      # Nov 9: a second page, and four treasures
MASTERY = BN.MASTERY
for name, keys in WISHES.items():
    t = start_ + keys[:-2] + ['tap A 20', 'run 180', 'shot done_' + name, 'mem %08X 6' % MASTERY, 'tap A 20', 'run 400', 'mem 0300197C 1', 'mem %08X 2' % (ITEMS & ~3), 'mem 0300155C 1', 'shot after_' + name, 'dump g 03001068 8a8']
    out = run(t); g = open(d + '/g.bin', 'rb').read()
    bag = [struct.unpack_from('<I', g, 0xE8 + 4 * i)[0] & 0xFFFFFFF for i in range(min(g[0xE4], 250))]
    if name == 'potential':
        m = [int(v, 16) for v in [l_ for l_ in out.splitlines() if l_.startswith('mem %08x' % MASTERY)][-1].split(':')[1].split()]
        check('hidden potential: every transformation gains mastery', (m[0] & 255) >= 75)
    if name == 'potara': check('a legendary treasure: the Potara Earrings', 162 in bag)
    if name == 'pouch': check('a legendary treasure: the Senzu Pouch', 166 in bag)
    check('wish %s: back at the Lookout' % name, at(out) == (1 << 8 | 6) and 'bad pc' not in out)
    check('wish %s: the balls are gone' % name, all(g[2 + zone26.BALL_ITEM + k] == 0 for k in range(7)))
    if name == 'power': check('greater power: everyone who has joined gains 5 in each stat', g[0x4F8 + 0x28] == g0[0x4F8 + 0x28] + 5)
    if name == 'rich': check('riches: a million Zenie', struct.unpack_from('<I', g, 0x4F4)[0] - struct.unpack_from('<I', g0, 0x4F4)[0] == zone26.BALL_ZENIE)
    if name == 'fighters': check('new fighters join', g[0x55 + 887 // 8] >> (887 % 8) & 1)
    if name == 'ss2': check('Super Saiyan 2 opens', g[0x55 + 864 // 8] & 255 == 255 and g[0x55 + 872 // 8] & 1)
# New Game+: the third page's wish to turn back time. The story starts over (the ending's flag 149 clear), the round counts (more flag 47,
# the bench's flags2), Goku keeps his experience and plays the opening on Snake Way.
NG_BYTE = BN.FLAGS2 + (47 - 32) // 8
t = start_ + MORE + page(3) + page(0) + ['shot time_say', 'tap A 20', 'run 200', 'dump g 03001068 8a8']
before = run(start_ + ['dump g 03001068 8a8']); g0 = open(d + '/g.bin', 'rb').read()
t += [v for k in range(14) for v in ['run 100', 'tap A 30'] + (['shot opening'] if k == 4 else [])] + ['run 200', 'shot ng_after', 'mem 0300197C 1', 'mem %08X 1' % NG_BYTE, 'dump g 03001068 8a8']
out = run(t); g = open(d + '/g.bin', 'rb').read()
ng = [int(l_.split(':')[1].split()[0], 16) for l_ in out.splitlines() if l_.startswith('mem %08x' % NG_BYTE)]
check('New Game+: the ending is undone (flag 149 clear)', not g[0x55 + 149 // 8] >> (149 % 8) & 1)
check('New Game+: the round is counted', ng and ng[-1] >> 7 & 1)
check('New Game+: Goku keeps his experience and skills', g[0x4F8 + 0x24:0x4F8 + 0x28] == g0[0x4F8 + 0x24:0x4F8 + 0x28] and 37 in g[0x4F8 + 0x0D:0x4F8 + 0x0D + g[0x4F8 + 0x0C]])
check('New Game+: the opening plays on Snake Way, Goku in the party', at(out) == (1 << 8 | 1) and g[0x4F8] & 1 and g[0] == 0 and 'bad pc' not in out)
W2 = Image.new('RGB', (5 * 240, 2 * 160))
for i, n in enumerate(('sum1', 'wish', 'treasure', 'done_potara', 'done_potential', 'after_pouch', 'time_say', 'opening', 'ng_after', 'flightmap')):
    W2.paste(Image.open('%s/%s.png' % (d, n)).convert('RGB'), (i % 5 * 240, i // 5 * 160))
W2.save(d + '/summon.png')
if fails: print('FAILED:', fails); sys.exit(1)
print('screens in', d)
