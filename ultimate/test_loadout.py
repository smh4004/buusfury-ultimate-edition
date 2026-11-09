#!/usr/bin/env python3
"""The skill loadout (Nov 9): a fighter holds seven skills; the rest of what he knows waits in his skill book, and the pause menu's Skills
tab swaps the highlighted one with SELECT. Also the quick skill wheel (hold L, press a direction). Build `--debug --enemy` first.
  python3 ultimate/test_loadout.py [rom] [work dir]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_moves as T
from PIL import Image
R = T.R
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)
def skills(out):
    w = [[int(v, 16) for v in l.split(':')[1].split()] for l in out.splitlines() if l.startswith('mem %08x' % (R + 0x0C))]
    b = b''.join(x.to_bytes(4, 'little') for x in w[-1])
    return list(b[1:1 + b[0]]), b[9]                      # +0x0D.., +0x15 the selected one

SIX = [7, 15, 19, 20, 22, 35]                                 # full (six: record +0x13 is the equipment's flags byte): Kaioken, which Goku knows from the start, has no room
L = T.setup(SIX, None, (0,)) + ['run 140', 'mem %08X 3' % (R + 0x0C)]
o = T.run(L, 'full'); before, _ = skills(o)
print('   six held:', before)
check('a full fighter keeps his six; Kaioken waits in the book', before == SIX)
M = L + ['tap START 80', 'shot pause', 'tap A 60', 'tap DOWN 60', 'shot skills'] + [v for k in range(3) for v in ['tap SELECT 40'] + (['shot swapped'] if k == 0 else []) + ['mem %08X 3' % (R + 0x0C)]]
o = T.run(M, 'swap')
w = [l for l in o.splitlines() if l.startswith('mem %08x' % (R + 0x0C))]
held = [skills('\n'.join(w[:k + 1]))[0] for k in range(len(w))]          # w[0]: before the menu, then after each SELECT
print('   after each SELECT:', held[1:])
# the book's order for Goku (build.py SKILL_BOOK): 7, 15, 43, 14, 20, 35, 22, 36, 44, 37, 19, ...: the next known one not held comes in
book = (7, 15, 43, 14, 20, 35, 22, 36, 44, 37, 19, 39, 41, 21)
firsts = [h[0] for h in held[1:]]
check('SELECT on the Skills tab swaps the highlighted skill for one from the book (Kaioken among them)', len(held) == 4 and firsts[0] not in SIX and firsts[0] in book and all(h[1:] == SIX[1:] for h in held[1:]) and 37 in firsts and 'bad pc' not in o)
check('round the book and back to the ki blast', 7 in firsts)
# The quick wheel: hold L, press a direction
Q = T.setup([7, 15, 20, 22], None, (0,)) + ['run 4']
picks = []
for key, want in (('UP', 0), ('RIGHT', 1), ('DOWN', 2), ('LEFT', 3), ('UP', 0)):
    Q += ['keys L', 'run 6', 'keys L,' + key, 'run 3', 'keys L', 'run 3', 'keys', 'run 10', 'mem %08X 3' % (R + 0x0C)]
    picks.append(want)
o = T.run(Q + ['shot wheel'], 'wheel')
got = [skills(l)[1] for l in [x for x in o.splitlines() if x.startswith('mem %08x' % (R + 0x0C))]]
print('   wheel picks:', got)
check('L and a direction pick the 1st-4th skill at once', got[-5:] == picks and 'bad pc' not in o)
I = Image.new('RGB', (720, 160))
for i, n in enumerate(('pause', 'skills', 'swapped')): I.paste(Image.open('%s/%s.png' % (T.D, n)), (240 * i, 0))
I.save(T.D + '/loadout.png')
print('screens in', T.D)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
