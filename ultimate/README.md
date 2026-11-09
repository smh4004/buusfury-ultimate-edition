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
41 Super Saiyan 4's Super Dragon Fist, 42 Solar Flare, 43 Super Kamehameha, 44 Super Saiyan Blue, 45 Max Power. Each transformation tier is
its own skill (`outfit.c` `ss_can`... `kaioken_use`): a tier goes up from the one below and, pressed in its own form, powers down. No
Super Saiyan during Kaioken, and no Kaioken in Super Saiyan until Kaioken is fully mastered. Icons: `lib/icons.py` (Super Saiyan 3's icon with a cyan 2 or a purple 4, the Z in red or
blue). Super Saiyan 2's lightning aura, GT Gohan's Super Saiyan 2 and the Blue hair (`ssb_hair`, Super Saiyan Gogeta's blues) are recolours.
Kaioken (Goku from the start, Krillin, Tien, Yamcha, Videl, Hercule): 1.25x, 1.5x and 1.75x by its mastery level, costing health as it goes.
Fully mastered (level 3) it changes (`outfit.c` `kk_track`, `kk_hud`, `combat_hook`): no health cost; it brings a cyan bar of its own over the
health bar, half the fighter's health (`build.py` `kk_bar`), which pays the cost as it goes and takes the hits instead of health, with no
stagger (super armor: the hit's damage is zeroed, so the reaction never starts); when the bar is empty the Kaioken ends. Goku and Kid Goku
can then use it from Super Saiyan too (Super Saiyan Kaioken, 1.75x on top of Super Saiyan; pressed again it goes back to Super Saiyan with
the Super Saiyan pool it had). Those three forms come after Blue's in the form list, so every older form keeps its number.
Kaioken and Blue power up on their own figure (`power_to` sets the new figure at the start; `build.py` `powerup_frames`): Kaioken's shout
keeps Goku's black hair and Blue's is blue, where both used to show the Super Saiyan gold. Vegeta's Blue figures have power-up frames too.
Solar Flare (Tien, Krillin): the power-up's white flash, and every ordinary enemy on screen gets the game's own stun (enemy state 1) for
150 frames; bosses aren't fooled. Galick Gun (Vegeta, Future Trunks), 10x Kamehameha and the Super Dragon Fist (Super Saiyan 4 Goku), Final
Shine (Super Saiyan 4 Vegeta) and the Super Kamehameha reuse the base move's code with their own frames and strength. The Kamehameha's code
shows frames 0-2 of the fighter's slot 18; Vegeta's figures hold his two-frame Big Bang there, so they get a Galick Gun pose of their own in
slot 31 (`build.py` `beam_poses`: his wind-up, then Final Flash's two-handed push), and the build stops if another of Vegeta's figures or a Kamehameha-using guest's
would show a missing frame (it draws junk over other sprites' tiles).

Mastery: each (character, tier) has a byte in the bench's last group (`MASTERY`). Time spent transformed raises it (Super Saiyan's
class every 10 drain units, Super Saiyan 3's every 45); 100 is level 2, 250 level 3, shown as the skill's level, and a mastered tier
drains slower. After the ending, Goku's mastered Super Saiyan 3 and Vegeta's Super Saiyan 2 teach Super Saiyan Blue (2x), and Goku's
Kamehameha at level 3, used 100 times, the Super Kamehameha. Super Saiyan 4 moves and looks come with the GT unlock, never in the story.
The skill book (record +0x22, `skill_book`): what a fighter knows beyond the six he holds; the pause menu's Skills tab swaps the
highlighted skill with SELECT. Hold L and press a direction to pick the first to fourth skill at once. Pressing R just before an
enemy shot lands, facing it, takes no damage: a ki blast goes back at its shooter, a gunman's shot is turned away (a perfect guard). The flight map's mini-map marks every place you can land.

Master Roshi joins at Kame House after the ending (`lib/roshi.py`: Krillin's LoG2 fighting frames with Roshi's head, beard and clothes
from his Buu's Fury sprite; Max Power with a white aura, 1.5x). Post-game gear (rows 162-166 past the game's equipment table, which moves):
Potara Earrings (transformations drain a third slower), Gravity Band (mastery twice as fast), King Kai's Shades (Kaioken costs half),
Turtle Shell (Roshi's, twice the EXP, slow) and Senzu Pouch (health back in a fight). The dragon has a second page of wishes: Super Saiyan 2,
a legendary treasure, hidden potential (75 mastery for every transformation); a third page turns back time: New Game+,
the story starts over with the party's levels, skills, gear and unlocks, and enemies hit half again as hard each round.
Tests (`--debug --enemy`): `test_tiers.py`, `test_moves.py`, `test_guests.py`, `test_gear.py`, `test_mastery.py`, `test_loadout.py`, `test_ssg.py`;
`test_kaioken.py` (the mastered Kaioken),
`test_dragon.py` (wishes, Roshi, New Game+, the flight map's marks), `test_guard.py` (its own rig: see the file; also the mastered Kaioken under fire).
Tests teleport characters by writing their position, which skips collision. The route tests (`test_bog`, `test_cell`, `test_chamber`,
`test_clash`, `test_ladder`) check each talk's teleport with `lib/floorcheck.py` (the built ROM's floor mask of the current area) and stop
with a FAIL rather than put Goku inside scenery when a route has gone wrong (Nov 9: "don't allow this clipping").
Variables added since Nov 9 live in work RAM from 0x0203F250 (the Kaioken bar, the power-up figure, the wheel's keys, the HUD widget) and are checked
when used: `heap_init` is left alone, because even a few more stores there made the game drop a frame in fifteen. `outfit.c` can't have
writable statics (they'd link into ROM); the build stops if one appears.

## Fixes from the owner's play (Nov 9, with a 100% save from the original game)
- Saves from the original game: the story scenes that unlock outfits and Super Saiyan 2 (outfits.json "unlocks") had passed before the
  mod could set its flags, so Gohan's outfits, and Super Saiyan 2 for Gohan, Trunks, Vegeta and the fusion, never came. `outfit.c
  story_sync` (in skills_sync) sets them all once the ending is seen, and earlier where the scene sets a story flag of its own
  (`build.py STORY_MARKS`). Checked on the owner's save: the flags come on, Super Saiyan 2 goes into free slots.
- The Skills tab says "Nothing to swap" instead of "SELECT: Swap" when the fighter knows nothing beyond what he holds (the owner took
  SELECT for broken: with that save only Goku and Vegeta had anything to swap).
- Beam bodies (`build.py body_block`): the Kamehameha's body rows for levels 1-2 run on into level 3's (one 12-row block at 0x721188);
  copying nine rows per level put the beam's head pieces in rows 9-11, so the Galick Gun, Special Beam Cannon, Black's Kamehameha,
  10x and Super Kamehameha drew a row of round heads along the beam every other frame ("galick gun sprite is messed up").
- The press-fast meter (native 0xC6: the Z-Sword, both Spirit Bomb pushes): +16 a press and 127/128 kept a frame, where it was +10 and
  31/32 (at least 1 a frame), which needed 12+ presses a second. Now about 5 a second fill it in 3 seconds, 6 in 2 (measured in the
  emulator, reading the meter at 0x0804D5BC objects); `test_zone26.py` presses it 6 times a second.
- Post-game bosses (`outfit.c postgame_foe`): every enemy on a row the mod added, and Super 13's, counts the player's stats above 110 at a
  quarter (his Strength and Power on his hits, his Endurance on the boss's), and its hits grow with the fighter's health past 4000 (at most
  3x). In a Super 13 rig with stats 180 (a level 200 fighter): his hits on Super 13 a third, Super 13's about 6.7% of the fighter's health a
  hit (it was about 1.5%). The owner: "want post game bosses to be a bit more of a challenge". Below 110 and 4000 nothing changes.

## Beerus (Nov 9, for the Battle of Gods post-game)
Buu's Fury has no Beerus, so `lib/beerus.py` makes every frame from BF Kid Buu's (actor 38): the same 15 x 31 build as the owner's front sprite
(`art/beerus_reference.jpg`), a bare torso, baggy trousers, wristbands, and the boss's 19 slots, so a fight on Kid Buu's enemy row plays all
of them. Kid Buu's head (antenna and all) is found by matching his standing heads (and turned or mirrored ones), cleared, and Beerus's is drawn
chin on chin, facing the same way: the owner's sprite from the front, the same head from behind, a profile with the ear standing like
Janemba's from the side. A few frames (a scream, the dash's blur) have their head placed by hand (`MANUAL`, keyed by the frame's pixels). Then
the collar under the chin, purple skin, gold wristbands, dark blue trousers with a navy waist and an orange gem, a gold hem, brown shoes; effects
keep their colours. Kid Buu's slot 17 (dissolving, likely only his ending) becomes a hit, then the knockdown. Frames go through
`sprites.composed_actor`, which keeps each frame's own pieces (a boss frame can have two). Actor `beerus` is the last new actor, so no other
actor's id moves; `<rom>.map.json` records its id (character = id + 9). Checked on a sheet and in the emulator (an enemy rig with
`BFU_RIG_ENEMY="61 <character>"`: he walks, punches, fires Kid Buu's beam and is knocked down).

## Battle of Gods and Super Saiyan God (Nov 9)
The owner: "build the entire movie Battle of Gods and super saiyan god ritual into the post game and once completed grant access to SSG",
Super Saiyan God "upon mastery of the super saiyan skill". `ultimate/bog.py` holds the quest; `test_bog.py` plays all of it (its rig's
official warps to Capsule Corporation: `BFU_HUB_WARP="4, 20, 1, 192, 196"`).
- Every scene is in the game's own areas, the movie's places where Buu's Fury has them (the owner, Nov 9: "don't have BoG take place in
  zone 26 use the accurate locations from the movie if you can"; it had been in zone 26 copies of the areas).
- After the ending, with Goku's Super Saiyan mastered and Goku playing, Whis waits at Capsule Corporation. King Kai calls; Whis takes Goku to
  King Kai's planet. Buu's Fury has no North Kai's planet (Cell destroyed it; in the Buu saga King Kai lives on Grand Kai's), so it is
  Grand Kai's Planet (1-0B). Beerus asks about a Super Saiyan God and they fight. Beerus can't really be beaten there; when Goku falls,
  the game's death script carries on to the party instead of the game over (`bog.death_branch`).
- Bulma's party at Capsule Corporation (4-14), as in the movie, with Bulma, Vegeta, Gohan, Videl, Goten, Trunks, Beerus and Whis: the
  pudding, Bulma's slap, Vegeta's fury; the Switch Character menu opens for his fight, on the party grounds. The area has no fighting
  (record +8 = 0; its load copies that to 0x03001988), so `outfit.c player_input` turns fighting on there while MORE_BOG_FIGHT is set.
  Win or fall, the ritual follows.
- The ritual: Shenron, five Saiyans and Videl's baby. Super Saiyan God is Goku's from here (outfit.c skills_sync). Then the god fight along
  the movie's path: West City (4-01), a forest (Fukurou Forest, 13-01), the desert's rock formations (Diablo Desert, 11-01); the cavern and
  the sky have no area here. Each leg is a Beerus row; a won leg carries the fight to the next place at once (no rest), the last brings
  everyone home to Capsule Corporation, where Beerus spares the Earth. A lost leg goes back to the party, to try that leg again.
- Who stands where is all spawn conditions (`zone26.add_bog`, on new copies of the records): the quest's people at their stages (`bog.PEOPLE`),
  Beerus as an enemy while his fight is on (`bog.FOES`, more flag 52), and in West City and the desert the people and enemies who live there
  stand aside meanwhile (their own condition, a story flag or a short script, and flag 52 clear: `zone26.unless`).
- Every scene is a step of the West City resident's event list (`build.py quest_npc` appends them); its first step sends talks at Capsule
  Corporation and on Grand Kai's Planet (`more_get(251)`: area << 8 | world) to the quest's dispatcher, which picks the scene by the story's
  progress (more flags 47-55). Natives 0xF8-0xFF are all taken, so the quest asks `more_get` (251 area, 252 Goku playing, 253 the quest can
  start) instead of new natives.
- Beerus's rows are copies of Kid Buu's (row 61): 250000 HP on King Kai's planet (2,000,000 broke Kid Buu's behaviour: likely an overflow in
  its health checks; he stopped attacking and the game crashed), 20000 at the party, 35000 / 40000 / 50000 for the god fight's legs; they
  are never made harmless in debug builds, since losing is part of the story.
- Script constants above 255 need `pushn` (`push` keeps one byte).
- Super Saiyan God (skill 46, a crimson Z): Goku's three base looks with crimson hair (`build.py ssg_hair`: his hair is the only big black
  patch on him), from base with the red aura, 1.75x without Super Saiyan's +5, half Super Saiyan's drain (`ss_tick`), back to base; no other
  tier from it. Form rows after Super Saiyan Kaioken's, so older forms keep their numbers. `test_ssg.py`.
- Whis (`lib/whis.py`): Kibito's frames (actor 149) in Whis's colours: pale blue skin, burgundy robe, black cuirass, the turquoise ring at
  his neck (Kibito's orange trims just under his chin), white hair.
- Its 2,446 characters of lines are in dialogue bank 7, a bank of their own (`bog.TEXT_BANK`; an evt line `say 0x02 @7 "..."`). The game
  unpacks a line's whole bank every time it shows the line (`Text_LoadString2`, no cache), so in bank 6 (7,613 characters of the mod's
  other new lines) they would make every bank-6 line slower to appear. `tools/assets/assets.py` adds banks 7 and up as new objects and
  grows the bank table (`gTextBankTable`, read only through the literal at 0x123CC), which moves it to the appendix. Later quests should
  do the same.
- The resident's story steps end his list with `push 25` (one past their last step). With the scenes appended, step 25 is the quest's
  dispatcher, so `quest_npc` repoints those ends past the scenes (found by the suite: after the ending he ran the dispatcher instead).
- The suite's route tests had waited 110 frames after the zone 26 door before teleporting to a West City resident; Goku's walk into the
  city ends about frame 117 (it starts a frame later since Super Saiyan God's commit), so the walk carried him off the talk spot. They wait
  150 now (`WALK_IN`; `test_zone26.go(settle=150)`).

## Zone 26 and Super 13

The build also needs Prototype D (`BFU_PROTO`), Legacy of Goku II USA (`BFU_LOG2`) and a `log2-decomp` checkout next to this repo (its map index locates the snow tiles). `ultimate/zone26.py` builds areas 26:1-15 from the prototype's layouts and collision with `ultimate/reskin.py`'s tiles; `ultimate/zone26.json` lists the doors. After `python3 ultimate/build.py --debug --zone` (walking down on Snake Way enters the zone), run `python3 ultimate/test_zone26.py`.

Script limits found here: the assembler's `push`/`call x(n)` only encode values up to 255, so write `pushn 622` and then `call flag`. Dialogue lines over roughly 100 characters reset the game; split them.
