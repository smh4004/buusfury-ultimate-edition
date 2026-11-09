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
Vegeta get GT outfits with their transformations (Super Saiyan 4 is its own skill: from Kid Goku's Super Saiyan 3 or GT Vegeta's Super
Saiyan), Gogeta a Super Saiyan 4 look, and Pan, Brapan (BSO's Bulma-Pan fusion) and Uub join the guest slot. Ledgic and Uub are on the Challenge Board.
`python3 ultimate/test_gt.py` plays every look and transformation; `test_ladder.py` plays the GT challenges.

Super Saiyan 4 has its own ki bar. A transformed form spends and drains one pool (Super Saiyan's, drawn yellow over the green EP bar, or
Super Saiyan 3's, orange) and powers down when it runs dry. Super Saiyan 4 uses Super Saiyan 3's pool, drawn purple from the OBJ palette's
own purples (no palette change), and keeps the orange the fighter had left as a second bar. Only one drains at a time, at half Super
Saiyan 3's rate: the purple first, while the orange waits; then the orange, then the form powers down (`outfit.c` `ssj4_hud`, `ssj4_drain`; hooks at 0x0800BCAE and 0x0800E506). Damage: Super Saiyan 4 hits 2.5x
Super Saiyan, Gogeta's 3x (`combat_hook`). `python3 ultimate/test_ki.py` (on the `--debug --enemy` build) plays both.

## Moves, mastery and the post-game (Nov 9)
Skill ids past retail (`build.py`): 35 Super Saiyan 2, 36 Super Saiyan 4, 37 Kaioken, 38 Galick Gun, 39 10x Kamehameha, 40 Final Shine,
41 Super Saiyan 4's red Dragon Fist, 42 Solar Flare, 43 Super Kamehameha, 44 Super Saiyan Blue, 45 Max Power. Each transformation tier is
its own skill (`outfit.c` `ss_can`... `kaioken_use`): a tier goes up from the one below and, pressed in its own form, powers down. No
Super Saiyan during Kaioken and the reverse. Icons: `lib/icons.py` (Super Saiyan 3's icon with a cyan 2 or a purple 4, the Z in red or
blue). Super Saiyan 2's lightning aura, GT Gohan's Super Saiyan 2 and the Blue hair (`ssb_hair`, Super Saiyan Gogeta's blues) are recolours.
Kaioken (Goku from the start, Krillin, Tien, Yamcha, Videl, Hercule): 1.25x, 1.5x and 1.75x by its mastery level, costing health as it goes.
Solar Flare (Tien, Krillin): the power-up's white flash, and every ordinary enemy on screen gets the game's own stun (enemy state 1) for
150 frames; bosses aren't fooled. Galick Gun (Vegeta, Future Trunks), 10x Kamehameha and the red Dragon Fist (Super Saiyan 4 Goku), Final
Shine (Super Saiyan 4 Vegeta) and the Super Kamehameha reuse the base move's code with their own frames and strength.

Mastery: each (character, tier) has a byte in the bench's last group (`MASTERY`). Time spent transformed raises it (Super Saiyan's
class every 10 drain units, Super Saiyan 3's every 45); 100 is level 2, 250 level 3, shown as the skill's level, and a mastered tier
drains slower. After the ending, Goku's mastered Super Saiyan 3 and Vegeta's Super Saiyan 2 teach Super Saiyan Blue (2x), and Goku's
Kamehameha at level 3, used 100 times, the Super Kamehameha. Super Saiyan 4 moves and looks come with the GT unlock, never in the story.
The skill book (record +0x22, `skill_book`): what a fighter knows beyond the six he holds; the pause menu's Skills tab swaps the
highlighted skill with SELECT. Hold L and press a direction to pick the first to fourth skill at once. Pressing R just before an
enemy ki blast lands, facing it, sends it back (a perfect guard). The flight map's mini-map marks every place you can land.

Master Roshi joins at Kame House after the ending (`lib/roshi.py`: Krillin's LoG2 fighting frames with Roshi's head, beard and clothes
from his Buu's Fury sprite; Max Power with a white aura, 1.5x). Post-game gear (rows 162-166 past the game's equipment table, which moves):
Potara Earrings (transformations drain a third slower), Gravity Band (mastery twice as fast), King Kai's Shades (Kaioken costs half),
Turtle Shell (Roshi's, twice the EXP, slow) and Senzu Pouch (health back in a fight). The dragon has a second page of wishes: Super Saiyan 2,
a legendary treasure, hidden potential (75 mastery for every transformation). Bulma's time machine at Capsule Corporation starts New Game+:
the story starts over with the party's levels, skills, gear and unlocks, and enemies hit half again as hard each round.
Tests (`--debug --enemy`): `test_tiers.py`, `test_moves.py`, `test_guests.py`, `test_gear.py`, `test_mastery.py`, `test_loadout.py`;
`test_dragon.py` (wishes, Roshi), `test_ngplus.py` (its own build: see the file).

## Zone 26 and Super 13

The build also needs Prototype D (`BFU_PROTO`), Legacy of Goku II USA (`BFU_LOG2`) and a `log2-decomp` checkout next to this repo (its map index locates the snow tiles). `ultimate/zone26.py` builds areas 26:1-15 from the prototype's layouts and collision with `ultimate/reskin.py`'s tiles; `ultimate/zone26.json` lists the doors. After `python3 ultimate/build.py --debug --zone` (walking down on Snake Way enters the zone), run `python3 ultimate/test_zone26.py`.

Script limits found here: the assembler's `push`/`call x(n)` only encode values up to 255, so write `pushn 622` and then `call flag`. Dialogue lines over roughly 100 characters reset the game; split them.
