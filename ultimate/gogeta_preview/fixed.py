"""A frame of Super Saiyan 4 Gogeta with fixes.py's patches on it. Since Nov 11 22:35 the build does this (build.py gogeta_fix through
gogeta_table.py), so to look at the fixes again use a ROM from before them (BFU_GOG_ROM; e.g. a build of 978966a): run on a ROM that has
them, 'shift' and the patches would land a second time."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'ssj4_preview'), os.path.join(HERE, '..')]
import numpy as np
import patch, fixes
from frames import fr, GOG, BF


def hole(c):
    """The two see-through pixels over his eye from the side: two rows above the eye's blue, a step behind it. Filled wherever his side
    head is (black, then the hair's darkest red, as the outline runs on either side of them)."""
    out = c.copy()
    for y, x in np.argwhere(c == 176):
        if c[y, x + 1] == 2 and c[y, x + 2] == 77 and c[y - 2, x + 1] == 0 and c[y - 2, x + 2] == 0 and c[y - 2, x] == 1 and c[y - 2, x + 3] == 1:
            out[y - 2, x + 1] = 1; out[y - 2, x + 2] = 62
    return out


def fixed(key):
    """key: (slot, frame, view) -> his frame as it would be"""
    g = hole(fr(GOG, *key))           # (wherever his side head is: a frame can be used in more than one view, e.g. lying down)
    return patch.apply(g, fr(BF, *key), fixes.ALL[key]) if key in fixes.ALL else g


if __name__ == '__main__':
    keys = [tuple(int(x) for x in k.split('/')) for k in sys.argv[1:]]
    for k in keys: patch.show(k, (48, 66), (42, 72), after=fixed(k))
