# Sprite credits

- Broly Full Power: made by Azure-Oni, ripped by DBZdogs.
- Gogeta (base, SSJ, SSGSS, DBS Broly): ripped by Mister Man, edited by Azure-Oni.
- Android 13 walk sheet and Beerus reference: supplied by the project owner; original artist not stated on the images.

## DBS Gogeta (base, Super Saiyan, Super Saiyan Blue)
Ripped by Mister Man, edited by Azure-Oni. Their sheet came as a JPEG, so `ultimate/gogeta.py` flattens compression noise: one colour table a form, near-white sparks in the hair, one-pixel specks. A PNG of the sheet would replace that step.

## From Legacy of Goku II (the owner's own cart, read at build time, nothing stored here)
Piccolo's sprites (actor r101) and the Special Beam Cannon beam (frames at 0x086E4560 in the USA ROM).

## Spirit Bomb orb
`spirit_bomb.png`, supplied by the project owner. Source not recorded.
- `android13_absorb/`: Android 13 absorbing the cores of 14 and 15, the project owner's 6-frame sheet, cleaned to game colours for Gero's Legacy.
- Cell Games: Cell's forms, the Cell Juniors and the arena come from Legacy of Goku 2 at build time; nothing is stored in this repository.

## Goku Black and Super Saiyan Rose
`goku_black/sheet.png`, supplied by the project owner; original artist not stated on the image. Its frames are Buu's Fury Goku's own poses redrawn. `ultimate/goku_black.py` uses each sheet frame as drawn and fills the poses it lacks with Goku's own frames in Black's and Rose's colours (`goku_black/frames.json` records which sheet frame stands for which pose).
