"""Whis (Nov 9, Battle of Gods): Buu's Fury has no Whis, so his frames are Kibito's (actor 149: tall, slim, a long robe, white hair; idle,
walk, arms raised, knocked down: all an attendant needs) in Whis's colours. Pale blue skin; Kibito's red robe and blue sleeves turn
burgundy; his orange tabard becomes Whis's black cuirass with orange and white marks; the orange trims around the neck, just under the
chin, become the turquoise ring Whis wears there. The white hair stays. All colours are ones the game has (`one`)."""
import numpy as np

SKIN = {36: (176, 208, 224), 35: (136, 176, 208), 34: (112, 144, 184)}
SHADOW = (72, 96, 136)                       # Kibito's darker reds next to his face: its shading
ROBE = {31: (64, 8, 24), 32: (104, 16, 48), 33: (144, 32, 72), 157: (64, 8, 24), 173: (104, 16, 48), 188: (144, 32, 72), 174: (104, 16, 48), 184: (144, 32, 72)}
RING = {79: (16, 96, 120), 63: (32, 144, 168), 64: (64, 184, 208), 4: (120, 208, 232), 109: (120, 208, 232), 250: (200, 240, 248)}
CUIRASS = {79: (16, 16, 24), 63: (40, 40, 48), 64: (64, 64, 72), 4: (88, 88, 96), 109: (248, 128, 0), 250: (240, 240, 240)}


def recolour(one):
    lut = lambda d: {k: one(np.array(v)) for k, v in d.items()}
    skin, robe, ring, cuirass, shadow = lut(SKIN), lut(ROBE), lut(RING), lut(CUIRASS), one(np.array(SHADOW))
    def fn(img):
        out = img.copy()
        face = np.isin(img, list(SKIN))
        if not face.any():
            return img
        near = np.zeros_like(face)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near |= np.roll(np.roll(face, dy, 0), dx, 1)
        from scipy import ndimage                   # the face: the skin patch reaching highest (hands come lower; from behind there's none)
        lab, n = ndimage.label(face, np.ones((3, 3)))
        top = lab[np.nonzero(face)[0].min()][face[np.nonzero(face)[0].min()]][0]
        ys = np.nonzero(lab == top)[0]
        band = np.zeros_like(face)
        if ys.max() - ys.min() >= 4: band[max(ys.max() - 3, 0):ys.max() + 4] = True
        for k, v in skin.items(): out[img == k] = v
        out[near & np.isin(img, (32, 33)) & ~face] = shadow
        for k, v in robe.items(): out[(img == k) & ~(near & np.isin(img, (32, 33)))] = v
        for k in RING:
            out[(img == k) & band] = ring[k]
            out[(img == k) & ~band] = cuirass[k]
        return out
    return fn
