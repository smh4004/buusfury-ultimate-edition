# Buu's Fury Ultimate Edition

A log2-decomp checkout must sit beside this repo. No ROMs or built games are stored here: you supply your own carts, and the build reads what it needs from them.

```sh
cp /path/to/clean/buusfury.gba baserom.gba   # USA, SHA-1 f1c4b075...
make extract && make harness
export BFU_COMBO=/path/to/log1-2-combo.gba   # USA, SHA-1 f02d179a...
export BFU_LOG2=/path/to/log2.gba             # Legacy of Goku II (USA): Zone 26's snow tiles, Special Beam Cannon
export BFU_PROTO=/path/to/DBZ3_cart27.GBA     # Prototype D: Super 13 and Zone 26's layouts
export BFU_BSO=/path/to/bso_review            # the owner's Black Star Odyssey review sheet as page PNGs (p-000.png ...): the GT fighters
python3 ultimate/build.py && python3 ultimate/build.py --debug && python3 ultimate/build.py --debug --enemy
python3 ultimate/test_build.py
python3 ultimate/build.py --debug --zone
python3 ultimate/test_zone26.py && python3 ultimate/test_story.py
```
Output goes to `ultimate/out/` (git-ignored). Share only `.bps` patches. New forms are defined in `ultimate/forms.json`.

The ROM is 32 MB: the GT fighters' frames sit above 16 MB, and `ultimate/lib/rom32.py` (from Black Star Odyssey) moves BF's
EEPROM address from 0x0D000000 to 0x0DFFFF00, where a 32 MB cartridge answers (GBATEK; smaller carts answer there too). Saves keep
their 8 KB layout, so a save from a 16 MB build loads. `--rom16` builds the old 16 MB layout as a fallback.
The debug build starts with Vegito and guest Broly, and opens Switch Character then saves when the intro ends.

## Outfits
`ultimate/outfits.json` lists each character's outfits, and `ultimate/src/outfit.c` adds Up and Down to the Switch Character screen.
Only forms with full combat animations belong in the list. An outfit's Super Saiyan row needs `down` set back to that outfit.

## GT
`ultimate/bso_import.py` reads the GT fighters from the owner's Black Star Odyssey review sheet (`BFU_BSO`, never committed: one PNG per
page, page n = BSO's actor n, page 0 the portraits) and lines each page up against the BF actor BSO drew it from. `ultimate/gt.py` builds
them on the BF actor of the form they play as, fills any animation slot the sheet doesn't draw from one of their own, and stores their
tiles WFZ-compressed (`wfz.compress`, from Gero's tools; cached in `ultimate/out/wfz_cache.pkl`). Kid Goku, Gohan, Goten, Trunks and
Vegeta get GT outfits with their transformations (Kid Goku: Super Saiyan 3 pressed again is Super Saiyan 4; GT Vegeta: Super Saiyan
pressed again), Gogeta a Super Saiyan 4 look, and Pan, Brapan (BSO's Bulma-Pan fusion) and Uub join the guest slot. Ledgic and Uub are on the Challenge Board.
`python3 ultimate/test_gt.py` plays every look and transformation; `test_ladder.py` plays the GT challenges.

Super Saiyan 4 has its own ki bar. A transformed form spends and drains one pool (Super Saiyan's, drawn yellow over the green EP bar, or
Super Saiyan 3's, orange) and powers down when it runs dry. Super Saiyan 4 uses Super Saiyan 3's pool, drawn purple from the OBJ palette's
own purples (no palette change), and keeps the orange the fighter had left as a second bar. Only one drains at a time, at half Super
Saiyan 3's rate: the purple first, while the orange waits; then the orange, then the form powers down (`outfit.c` `ssj4_hud`, `ssj4_drain`; hooks at 0x0800BCAE and 0x0800E506). Damage: Super Saiyan 4 hits 2.5x
Super Saiyan, Gogeta's 3x (`combat_hook`). `python3 ultimate/test_ki.py` (on the `--debug --enemy` build) plays both.

## Zone 26 and Super 13

The build also needs Prototype D (`BFU_PROTO`), Legacy of Goku II USA (`BFU_LOG2`) and a `log2-decomp` checkout next to this repo (its map index locates the snow tiles). `ultimate/zone26.py` builds areas 26:1-15 from the prototype's layouts and collision with `ultimate/reskin.py`'s tiles; `ultimate/zone26.json` lists the doors. After `python3 ultimate/build.py --debug --zone` (walking down on Snake Way enters the zone), run `python3 ultimate/test_zone26.py`.

Script limits found here: the assembler's `push`/`call x(n)` only encode values up to 255, so write `pushn 622` and then `call flag`. Dialogue lines over roughly 100 characters reset the game; split them.
