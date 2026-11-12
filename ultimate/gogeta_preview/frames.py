"""Super Saiyan 4 Gogeta's frames out of a built ROM, with BF Goku's (the frame each was drawn on) and Super Saiyan 4 Goku's, all on the
canvas lib4.Rom.frame lays a frame out on (96 x 96, the actor's own place at row 64, column 48), so one pixel is one place in all three.
  BFU_GOG_ROM: a debug build (its .map.json beside it); default ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'ssj4_preview'), os.path.join(HERE, '..')]
import json, struct
import numpy as np
from lib4 import Rom

ROM = os.environ.get('BFU_GOG_ROM', 'ultimate/out/BFU_debug_PERSONAL_USE_ONLY.gba')
R = Rom(ROM); forms = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
aid = lambda n: struct.unpack_from('<H', R.rom, 0x800000 + 24 * forms[n] + 0x0E)[0] - 9
GOG, GOKU, BF = aid('gogeta_ssj4'), aid('kid_goku_ssj4'), 106
NS = {a: R.slots(a) for a in (GOG, GOKU, BF)}
_c = {}


def fr(a, s, f, d):
    if (a, s, f, d) not in _c: _c[a, s, f, d] = R.frame(a, s, f, d)
    return _c[a, s, f, d]
