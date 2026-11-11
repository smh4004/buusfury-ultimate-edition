"""Android 13's attack poses (Nov 10): his own standing frames from ultimate/art/android13_sheet.png with the near arm redrawn, in the sheet's colours.
Each edit gets a cell as RGB with PAD columns of background added either side, and the sheet's background colour; (y, x) are the cell's own."""
import numpy as np
G = (128, 80, 24); M = (248, 184, 168); I = (224, 152, 128); H = (200, 128, 96)
T = (83, 41, 0); X = (140, 70, 0); Y = (121, 61, 0); Q = (107, 112, 33); A_ = (106, 53, 0)
PAD = 8                          # build.py A13_PAD
def put(a, bg, pts):
    for (y, x), c in pts.items():
        a[y, x + PAD] = bg if c is None else c
def side_clear_arm(a, bg):
    """The near arm hanging at his side (x 4-6, rows 16-20): gone, the torso's edge drawn at x 6."""
    pts = {}
    for y in range(16, 21):
        pts[(y, 4)] = None; pts[(y, 5)] = None; pts[(y, 6)] = G
    put(a, bg, pts)
def glove(y, x):
    g = {}
    for dy, row in enumerate(('.TTT', 'TXXT', 'TXYT', '.TTT')):
        for dx, ch in enumerate(row):
            if ch != '.': g[(y + dy, x + dx)] = {'T': T, 'X': X, 'Y': Y}[ch]
    return g
def side_thrust(a, bg):
    side_clear_arm(a, bg)
    pts = {}
    for x in range(0, 6):
        pts[(15, x)] = G; pts[(16, x)] = M; pts[(17, x)] = I; pts[(18, x)] = G
    pts.update(glove(15, -3))
    put(a, bg, pts)
def side_windup(a, bg):
    side_clear_arm(a, bg)
    pts = {}
    for x in range(7, 12):
        pts[(16, x)] = G; pts[(17, x)] = M; pts[(18, x)] = G
    pts.update(glove(15, 11))
    put(a, bg, pts)
def side_push(a, bg):
    side_thrust(a, bg)
    pts = {}
    for x in range(-1, 6):                               # the far arm below the near one, a shade darker
        if (19, x) not in pts: pts[(19, x)] = H
        pts[(20, x)] = G
    pts.update({k: (Y if v == X else v) for k, v in glove(18, -3).items()})
    put(a, bg, pts)
def front_thrust(a, bg):
    """Facing the camera: his right arm (on the viewer's left, x 3-5, rows 13-21) comes forward, the glove in front of his chest."""
    pts = {}
    for y in range(13, 23):
        for x in (3, 4, 5):
            pts[(y, x)] = None
    for y in range(13, 20): pts[(y, 5)] = G
    pts.update(glove(14, 5))
    put(a, bg, pts)
def front_windup(a, bg):
    pts = {}
    for y in range(13, 23):
        for x in (3, 4, 5): pts[(y, x)] = None
    for y in range(13, 20): pts[(y, 5)] = G
    pts.update(glove(17, 2))
    put(a, bg, pts)
