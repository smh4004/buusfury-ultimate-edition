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
41 Super Saiyan 4's Super Dragon Fist, 42 Solar Flare, 43 Super Kamehameha, 44 Super Saiyan Blue, 45 Max Power, 46 Super Saiyan God, 47 Full
Power. Each transformation tier is its own skill (`outfit.c` `ss_can`... `kaioken_use`): a tier goes up from the one below and, pressed in
its own form, powers down. Super Saiyan 2 also follows Super Saiyan in Super Saiyan's own skill (Nov 9, the owner: "so it doesn't have to be
swapped for SS1"): once the story opens Super Saiyan 2, Super Saiyan pressed in Super Saiyan goes up to it (Super Saiyan 3 then goes up from
there), and pressed in Super Saiyan 2 powers down; Super Saiyan 2 is known but takes no slot (`ss_to_ss2`, `skills_sync`). No
Super Saiyan during Kaioken, and no Kaioken in Super Saiyan until Kaioken is fully mastered. Full Power (Nov 9): Mystic Gohan only, from
his orange gi (form 13) and none of his other forms, learned with the orange gi (outfit flag 860): his own figure with white lightning
crackling around him (`build.py FP_LOOKS`), Max Power's white aura, 1.75x without Super Saiyan's +5, half Super Saiyan's drain, back
to the orange gi; no Super Saiyan from it (`fp_can`, `test_fp.py`). Orange-gi Gohan's Super Saiyan and 2 (forms 58, 79) are his own
frames with the school Super Saiyan's gold hair (`lib/sprites.py hairswap_actor`: the pixels where actor 104 differs from 98, laid over 101;
the power-down's 32x32 frames on the idle's grid); before, he changed into the school uniform as he powered up. Icons: `lib/icons.py` (Super Saiyan 3's icon with a cyan 2 or a purple 4, the Z in red or
blue). GT Gohan's Super Saiyan 2 and the Blue hair (`ssb_hair`, Super Saiyan Gogeta's blues) are recolours. Super Saiyan 2's and Full
Power's lightning (Nov 9, the owner: "more visible and more present", "move with the aura", then "a bit too much lightning and too thick,
also make the entire thing animated ... all or nothing"): none of it is on the figure's frames (the Super Saiyan 2 forms and Full Power use
their source figure under their own actor id, `same_as`); all of it is the crackle, a thin bolt (one pixel and a one-pixel edge) that
strikes beside his head or shoulders every 7-13 frames and breaks up over about 11 (`outfit.c crackle`, frames from `build.py
crackle_frames`, drawn as hit sparks), cyan for Super Saiyan 2, white for Full Power; `test_fp.py` counts the strikes.
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
slot 31 (`build.py` `beam_poses`: his wind-up, then Final Flash's two-handed push; in Saiyan armour, `armour_pose`), and the build stops if another of Vegeta's figures or a Kamehameha-using guest's
would show a missing frame (it draws junk over other sprites' tiles).

Mastery: each (character, tier) has a byte in the bench's last group (`MASTERY`). Time spent transformed raises it (Super Saiyan's
class every 10 drain units, Super Saiyan 3's every 45); 100 is level 2, 250 level 3, shown as the skill's level, and a mastered tier
drains slower. After the ending, Goku's mastered Super Saiyan 3 and Vegeta's Super Saiyan 2 teach Super Saiyan Blue (2x), and Goku's
Kamehameha at level 3, used 100 times, the Super Kamehameha. Super Saiyan 4 moves and looks come with the GT unlock, never in the story.
The skill book (record +0x22, `skill_book`): what a fighter knows beyond the six he holds; the pause menu's Skills tab swaps the
highlighted skill with SELECT (a fighter holds six; the tab shows four at a time and scrolls). Hold L and press a direction to pick the
first to fourth skill at once, A for the fifth and R for the sixth; a tap of L steps through all six. Pressing R just before an
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
- The guest slot shows on Switch Character only once someone has joined it (record +0 bit 0); the original game plays it without
  joining, so an old save had Broly unlocked (flag 111) and no slot to pick him in. `story_sync` joins him then. Only him: every other
  guest's flag is set by the script that joins him, and when it joined any unlocked guest it got in ahead of Broly's own join after his
  fight in a rig with post-game guests unlocked (`test_story.py`: wrong outfit, no shared stat points).
- Battle of Gods had more flags 47-48, which are New Game+'s round count (`outfit.c NG_FLAG`): starting the quest would have made
  enemies hit 1.5x, and 2.5x after King Kai's planet. It uses 49-57 now (58-63 are free).
- Trials and Trials II had party slots 3 and 4 the wrong way round ("Vegeta vs Majin Buu" played as Trunks); `test_zone26.py` now
  checks each trial's name against its slot.
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
- Super 13 got stuck and couldn't be hurt (the owner, on the Nov 9 build: "can't even damage and he's stuck walking up", "his ability
  looks fucked ... couldn't even see it"). An enemy's stats row also picks its behaviour (row +8: its first state in the enemy state table
  0x0870F514), and Super 13 and Android 13 run Dabura's (row 18). Near 60% health Dabura's mid-fight scene (states 0x78-0x7F) walks to
  (192, 80) of his own story room, which in the snow arena is inside the rocks: Super 13 backed into a nook between them, was drawn behind
  them, and no punch landed (reproduced: none for 30 seconds from any side). `outfit.c arena_keep` (every frame) keeps foes of the snow
  arena's fight rooms (`zone26.arena_rooms`: Android 13, Super 13, the Boss Rush) on the open snowfield (x 48-272, y 120 and down), and
  `no_story_walk` ends any such walk where the foe stands, for every fight the mod set up (`postgame_foe`): they all borrow a story boss's
  behaviour in a room that isn't his. The owner then: "replace that shit don't make him do that at 60%" (Dabura's flying special, states
  0x78-0x7F: he faded, rose off the top of the screen while it flashed white, untouchable, and hit from out of sight). On a copy of
  Dabura's behaviour (row +8 = 0x6E, in any fight the mod set up) `no_story_walk` turns 0x78 or 0x79 back to his ordinary fighting state
  0x71 and undoes what the special's start did: +0x1CC = 1 (hittable) and +0x174 = 0 (the lift). Going to 0x6E instead re-entered the
  special every frame, and leaving at 0x79 without the reset kept him untouchable. Story Dabura keeps his special. `test_super13.py`
  fights him by hand (no teleports) for about 100 seconds.
- Battle of Gods' Beerus runs on those rules too. His Strength sets his big hits: at 115-120 three floored that fighter (2400-2600 each,
  measured by poking his object's stats, +0x1B0, in an enemy rig). The god fight's legs are 85/90/95 now: about 880, 1040 and 1220 a hit
  (12/14/16%, measured the same way): the hardest fights in the game, above Super 13, as the owner wants Beerus to be the strongest
  (Garlic Jr.'s planned quest comes before).
- The firing pose (the owner, on the trailer: "Don't know wtf is going on with Uubs head after the kamehameha", "the head is way too far
  back in that one side view"). The Kamehameha holds frame 0 of slot 18 (the charge, hands at the hip), then shows frames 1 and 2 in turn
  while the beam is out (logged in the emulator). A playable form's animations are made as long as a retail player's, and slot 18 was
  spread out ([0,0,1,1,2,2] for three frames), so frame 1 was the charge again: every GT fighter dropped back into it every few frames
  while firing. `sprites.INDEXED` slots keep each frame at its number and repeat the last. DBS Gogeta's own firing cells ended on the
  wind-up (`gogeta.py` 'fire').
- Uub's and Majuub's flying (slot 15; "Those flying frames are super fucked for Uub/Majuub"): the sheet draws Majuub's on base Gotenks',
  whose torso his big hair covers, so he flew as a head with a strip of trousers. `gt.repair` gives him Uub's flying (kid Goten's) in his
  own colours, as the sheet does for every move it builds on Goten for both, and clears what Goten's legs and boot soles left round their
  smaller head seen from the front (a green tuft, grey specks), and Goten's sleeve flicker (dark purple specks) everywhere.
- Broly Full Power floated over his shadow ("fix Broly looking like he's floating"): BF's Broly record puts the feet 15 rows under the
  origin, a fighter's 7, and the sheet's frames were lined up like a fighter's; they are drawn 8 rows lower (`origin_dy`). Then "Remove
  the shadow beneath Broly's feet too cause it looks off": an actor record's +0xA/+0xB is its shadow's size, looked up in 0x086B759C
  (4x2, 10x4, 16x6, 24x10) when the object is made; both Brolys (actor 29, the story's too, and Full Power) get a size not in it, so the
  draw (sub_0800EF94) has no shadow piece (`sprites` `_no_shadow`; checked in the emulator's OAM).
- `test_frames.py` reads every one of these from a built ROM: firing poses in order for every added actor, Majuub's and Uub's flying,
  no specks, feet on the same row for forms on the same template, no shadow under either Broly.

## Fixes from the trailer (Nov 10)
- GT Vegeta's change ("his ssj4 transformation he did was the fusion dance not transformation frames"): the BSO sheet draws no change
  (slot 10) for him, and `gt.FILL`'s first choice is his slot 21, the sheet's "special", which starts with the arms flung out to one side
  and then the other. Every GT Vegeta look (base, tank top, moustache, Super Saiyan, Super Saiyan 4) now changes on his own power-up
  (slot 13): the crouch twice, the shout eight times, his stance, a retail change's 11 frames (`gt.actors`). (Third pass: the next form's
  crouch and stance, without the shout.) (Nov 11: the game's own change pose instead, see "Nov 11, 09:07" below.)
- Final Shine ("his final shine frames are broken"): Final Flash's code (Final Shine's too) shows slot 19's frames by number: 0 and 1 by
  turns while charging, 2, then 3 and 4 by turns while the beam is out (sub_0801B4EC). The sheet's five frames, grown to a retail
  player's ten by spreading, put the charge (sheet 1 and 2) at 3 and 4, so GT Vegeta never pushed his Final Flash or Final Shine out.
  His figures keep each frame at its number (`sprites` `indexed`, the per-figure `INDEXED`).
- Super Saiyan Blue Gogeta's hair ("still fucked too looks totally wrong. Use SSB Goku as a basis and get the color and shape fully
  accurate"): cut 3 gave each frame BF Super Saiyan Blue Goku's hair (the closest shape in the same view). Replaced in the second pass
  below.

Second pass, from the owner's notes on cut 3 ("Goku hand still red on 10x kame, Gogeta hair still wrong, and final shine still off"), and
the owner's notes on its review images ("You got rid of the fur on his ARMS I said his HANDS only", "Literally look at SSJ Gogeta, turn
that hair blue colored and use SSB Gokus hair as a reference but DONT CHANGE THE SSJ GOGETA HAIR SHAPE JUST USE THE SSB GOKU FOR REFERENCE
FOR EXACT COLOR/SHADING", "Vegeta final shine is fine"):
- Super Saiyan 4 Kid Goku's hands on the 10x Kamehameha (`gt.ssj4_hands`): the BSO sheet draws his Super Saiyan 4 on BF Goku (actor
  106) frame for frame and turned the arms' skin to red fur, hands and all. In his firing pose seen from the side (slot 18,
  `gt.HAND_SLOTS`, `HAND_VIEWS`) each frame is
  laid on BF Goku's at their best overlap, and a hand-sized patch of BF skin the sheet made fur on the far side of a wristband (fur on
  both sides of the band: the other side is his forearm) gets BF's skin back, its band the sheet's blue. Only the hands: his forearms keep
  their fur, and every other pose is the sheet's own. (A first try also changed patches past sleeve ends and the push seen from the
  front, which took the fur off his arms: gone.) From the front and back his hands stay as the sheet drew them.
- Super Saiyan Blue Gogeta (`lib/ssb.py` `gogeta_frames`; the owner: "Get the fucking hair RIGHT according to BUUS FURY GOGETA"): Buu's
  Fury's own Super Saiyan Gogeta (actor 93, forms 41 and 44), every frame, the same figure and hair shape, his hair in Blue Goku's colours
  shade for shade. His gold runs 25 (outline, darkest), 26, 27, 28, 29, 30; each takes the Blue of the Goku gold of the same shade, as
  Goku's own does (202 the blue, 201 the shade, 28 the cyan, 29 and white the near-white, 16 the dark blue): 25 the blue, 26 and 27 the
  shade, 28 the cyan, 29 and 30 the near-white, and the skin shades (202, 201, 16) among his hair as Goku's. His figure has no slots 8,
  10 or 11: the ki blast's (9), his power-up's two poses as a retail change's 11 frames, his stance (0). His knockdown seen from the side
  (slot 16) is stored mirrored with the mirror bit set, which `goku_black.actor_frames` doesn't read (`ssb.actor_frames` does; likely
  the same for Goku Black's and Rose's slot 16 side view, from BF Goku's mirrored frames: unchecked). He still changes to it from DBS
  Gogeta's Super Saiyan. (Three earlier tries on DBS Gogeta's sheet figure, Blue Goku's hair on it, its own Blue cells, its Super Saiyan
  hair recoloured, are gone.) DBS Gogeta's eyes were see-through in his base and Super Saiyan looks: the sheet's eyes are near its
  background's teal, so `gogeta.cut` dropped them (and a few pinholes); `gogeta.frame` now gives a see-through patch of up to 4 pixels
  that his figure closes round the sheet's colour there (or his hair's, for a pinhole in his hair).
- Blue Goku's and Blue Vegeta's hair, every pixel (`lib/ssb.py` `tint`; the owner: "FIX SSB GOKUS HAIR NOT BEING FULLY BLUE WHY IS THERE
  STILL YELLOW"): BF's Super Saiyan hair and skin share colours, so `ssb_hair` took a ramp pixel for hair only within 3 pixels of the
  hair's highlights and nearer them than the face: the spike tips, the outline far from a highlight and the hairline stayed gold, and
  Vegeta's palest gold (246) wasn't in the ramp at all. Each Super Saiyan frame is now laid on the base figure's same frame (where the game
  draws them): a ramp pixel is hair where the base has its black hair or nothing, kept with the patch holding the hair's highlights (so an
  arm a pose moved stays skin); the old rule's pixels count too, and alone where the base lacks the frame (the armour's Blue). 246 is in
  `SSB_HAIR` as the near-white.
- Blue Goku's and Blue Vegeta's faces (the owner: "Fix some of SSB Goku and vegetas face pixels being blue"). Three causes, all fixed in
  `lib/ssb.py`:
  - The eyes' whites are white (2), which is also the hair's brightest colour, so the old rule took them, and the skin within 3 pixels of
    them, for hair. White beside an eye's green (215, 216) is now the eye (`eye_whites`).
  - Goku's Super Saiyan side figure stands 2 pixels left of his base one, so the base hair landed on his profile. `base_under` now moves
    the base figure (up to 3 pixels) to where its body matches.
  - Where the base figure's hair hung over the face or neck (Vegeta's brow and jaw), the outline turned blue. A pixel only the base
    figure makes hair stays skin if the body is to its left, its right or above it. The hairline, with the face only below it, stays
    hair.
  - Check: test_frames 7 (no eye white changed, no changed skin shade beside the face).
  - Then (the owner: "YOU STILL HAVE LEFT YELLOW ON THE SIDES OF GOKU SSB", "THE SIDES OF GOKUS HAIR AROUND HIS EARS ARE YELLOW STILL",
    "DONT MAKE THEIR FUCKING FOREHEAD SKIN BLUE OR THEIR EARS EITHER JUST THE HAIR"), the base figure, lined up under each frame, settles
    hair against skin:
    - Skin: a skin shade (16, 202, 201) the Super Saiyan figure draws exactly as the base figure does is never blue. That covers his face,
      his forehead between the bangs, his ears, and Vegeta's forehead under his widow's peak. The one exception is a pixel walled in by
      hair on all four sides.
    - Hair: `ssb.fill` turns the hair's shades left gold at its edge blue: a gap in the bangs, the hair's last row over the face, a side
      lock's end, and once, the hair's inner corner by the temple (these last two only within 4 pixels of an eye, so a running
      shoulder's top stays skin). `ssb.sideburns` turns blue a hair shade drawn over the base figure's skin with hair beside or above it
      and no eye beside it, e.g. Goku's sideburn in front of his ear. It applies to Goku only, from the side only (one eye), and only behind
      the eye on the eye's rows, because it put a blue pixel on Vegeta's cheek (the owner: "you put the blue pixel back in vegetas face
      again"). The two repeat until nothing changes.
    - Pixels touching the face's skin or an eye at their left, right or top stay skin. A blue stub cut off from the hair (under
      Vegeta's ear) is dropped.
    - The armour's Blue Vegeta has no base figure to check against, so it keeps the old rule (with the eye fix).
  - Check: test_frames 7, against the retail ROM's base figures: no skin pixel blue, no face outline blue (except Goku's sideburn), no
    gap left gold, and Goku's sideburn blue.
    It fails on the builds the owner screenshotted.
  - Vegeta's glove and boot highlights are white too and still turn pale blue. That is unchanged and was not asked for; the owner was
    asked.
- Switch Character draws no ground shadows (the owner: "Don't render the shadows under characters feet in the switch screen it's blocking
  their name"). A fighter's sprite keeps the shadow its actor record gave it when it was made (+0x5C). On this screen it was drawn below
  and to the right of him, over the name, e.g. Super Janemba's in the old trailer. Each frame, `outfit.c` `no_shadows` frees it with
  sub_0800ECB0 and a size the game's table doesn't have. This affects only the screen's own sprites; back in the field the player
  keeps his shadow. Checked in `test_build.py`. A few guests (Piccolo, Tien, Krillin, Android 17/18, Future Trunks, Roshi) also have a
  small shadow drawn into their own frames under the feet. It stays, because those are their sprites (likely from the source sheets).
- Super Saiyan 4 Vegeta's Final Shine wind-up (`gt.shine_charge`, approved): seen from the side, slot 19's frames 0-2 (charging, then the
  pull back) had his neck see-through and a glove turned to hair: the sheet's head swap took them with BF's head. Each gets BF Vegeta's
  (actor 270) gloves back over the hair, BF's neck and collar where the page left nothing, and BF's charge glow where it edges him, each
  in the page's own colour for that BF colour. The glow is still Final Flash's yellow (the frames are shared with his Final Flash). The
  other GT Vegeta pages lose a few neck pixels the same way, too few to show: left as they are.
  `test_frames.py` 7-9 check all of these on the built ROM.

Third pass, from the owner's notes on cut 4 (15:16: "Why doesn't SSJ4 vegeta have transformation frames. Why doesn't Broly have attack
frames for shooting his eraser cannon. Why is vegeta fucking punching while shooting the galick gun and not holding his hands out normally
like the kamehameha frames do. Why the fuck is super android 13s beam attack frames so glitched out", "PREVIEW BEFORE RESHOOT"), and 15:40
("Also replace the SSJ4 Gogeta with this one"):
- (Superseded on Nov 11 for the four looks with a form above them: see "Nov 11, 09:07" below.)
  GT Vegeta's changes show the new form: slot 10 is his power-up's crouch (slot 13 frame 0) for two frames, then the form he changes into
  (`gt.GT_NEXT`: Super Saiyan, then Super Saiyan 4; the tank top's the same) in the same crouch for eight and its stance, as BF's own
  changes go (Goku 106: the old hair for two frames, the new form from the third). Before, all eleven were his own figure, so the hair
  changed only when the change ended. The moustache look and Super Saiyan 4 (no next form) keep their own. Not the shout (slot 13 frame
  1, as cut 4 had): BF Vegeta's fists are up over his head there and the sheet's bigger hair covers his arms, so his arms vanished (the
  owner, 16:04: "why are vegetas arms disappearing on transforming"). His power-up itself (slot 13) still has that frame.
- Broly Full Power fires with his hand out: slots 3 (ki blast) and 18 (the pose Eraser Cannon's Big Bang code holds) were his idle. Both
  are now the sheet's strike, the wind-up then the open hand thrust, each frame kept at its number (`sprites` `indexed`, now also for
  `slots` sheets), so the hand is out from the second frame on.
- Vegeta in Saiyan armour (LoG2's figures: base, Super Saiyan, 2, Blue) fired the Galick Gun with slot 18, LoG2's own firing animation,
  a slash with arcs: the Kamehameha code's frames 1 and 2 were the arcs by turns. Each gets a Galick Gun pose in slot 31 as BF's Vegeta
  does (`build.py` `armour_pose`, from his own frames): side, his ki blast's wind-up, then its arm out with the far arm laid under it (a
  shade darker, where nothing is in front) and the far fist taken off his back (`ARMOUR_FIST`, checked pixel by pixel: the build stops if
  the frame differs); front, LoG2's ki charge (animation 14, base Vegeta's new slot 24: LoG2's Super Saiyan has none) under each figure's
  own head, hands together, then at his chest with the ki in them; back, the wind-up, then the power-up's back, arms out of sight. These go
  with the sprites (the code area is full).
- Super Android 13's beam (the Electric Kamehameha's code: frame 0 charging, then 1 and 2 by turns): the prototype's slot 18 is the
  charge, the thrust, then four frames of him flexing with his arms up, so the thrust and a flex flickered by turns. The playable figure's
  slot 18 is the charge, then the thrust held (`sprites` `reframe`). The boss keeps the prototype's.
- Super Saiyan 4 Gogeta is BSO's finished one, from the owner's four "every frame" sheets (`bso_import.SHEETS`: a folder
  `gogeta_ssj4_v2` in `BFU_BSO`, p1.png to p4.png, 4x on the green field, never committed; every slot's frame count is checked). Their
  slot 10 is BSO's change into him from base Gogeta (black hair); this look never changes form, so it is left out and his power-up stands
  in if a skill plays it.
- Shown to the owner as before/now sheets from the build before any reshoot. `test_frames.py` 6 checks the GT Vegeta changes.
- From the owner's 16:28 notes ("fix roshis kamehameha frames too", "make sure SSJ4 vegeta transformation frames all match the front view,
  that "side view" one is missing the arms still and they should all be the same anyways", "make sure Super 13 beam actually comes out of
  his hands not below it"):
  - GT Vegeta's changes: every view of slot 10 is the front view, frame for frame (relocked with `BFU_RELOCK`).
  - Master Roshi's figure is Krillin's (LoG2 r73: animation 5, the ki throw, in slot 18) with his head and clothes, so his Kamehameha
    charged with a hand up behind his head and fired one-handed. He gets a pose of his own in slot 31 (`build.py` `roshi_pose`): from the
    side, the throw's frame with the thrown arm off and both hands cupped at his back hip (`ROSHI_HANDS`), then both pushed out (the far
    arm under the near one, as the armour Vegeta's); from the front, the throw's crouch; from behind, his back with his arms down.
    `outfit.c` `kame_use` plays it for him, and gives his behaviour `kame_vt` (the Kamehameha's, with its update wrapped:
    `kame_update`) so the beam starts at his hands (the game places it for Goku's reach, 5 pixels past his: `ROSHI_BEAM`).
  - Super 13's beam: the wave's update (0x0801AE32) places the beam on its 24th frame at the fighter's place plus a step per facing
    (0x0871DEC4), set for a normal fighter; his thrust holds his hands higher and further out. `outfit.c` `wave_update` moves it there
    for him (`S13_BEAM`: left 14 back and 9 up, right 18 and 9 up; measured in the emulator, both ways). His charging ball, made at
    the fighter's place plus a step per facing (0x0871DE94), sat behind him at his hip facing right (16:59: "Super 13 beam is facing out
    of his ass when facing right"): `wave_start` moves it 14 pixels forward to his hands (`S13_BALL`), the mirror of facing left.
- Approved figures are locked (16:08, "Reshoot it all and lock changes"): `ultimate/locked.json` lists the forms with a fingerprint of all
  their frames (`lib/lock.py`: every slot, frame and view, each piece's box, attributes and pixels, not where they sit in the ROM), and
  every build stops with LOCKED FRAMES CHANGED if one differs. Locked: GT Vegeta's looks, Broly Full Power, the four armour Vegetas,
  Super 13, SSJ4 Gogeta, and the Blue looks approved earlier that day (Goku's two, Vegeta's two, Gogeta); Master Roshi from 17:05
  ("Approve all fixed"). A listed form with no
  fingerprint gets one on the next build; `BFU_RELOCK=<form>[,...]` records a change the owner asked for.

## Fixes from the owner's play, Nov 10 evening
The owner, 17:19-17:39, with a long list ("Should never be this many issues EVER don't let this happen again TEST THOROUGHLY"). Each fix was
played in the emulator; `ultimate/audit_moves.py` and `test_frames.py` 10-13 now check the whole cast (below).
- Fights dropped a frame every 64: `player_input` ran `skills_sync` twice in that frame (the fighter in play and a party member in turn).
  The party member's runs 32 frames later. Measured: 10 stalls in 640 frames before, none after.
- Switch Character: Gogeta unfused and left the party when picked. A fusion's time left is record +8 (frames, -1 = no limit; native 0xA8
  sets it); the HUD counts it down while a fusion form (flags bit 3, his form 41) plays and unfuses at 0. The story's fusion leaves 0 there,
  and the post-game's join (`party_join`) kept it. Now `gogeta_keep` (from `story_sync` and every frame of Switch Character) gives a
  post-game Gogeta no limit and puts him back in a party he already left; `party_join` sets it too.
- The HUD's skill icon shows Super Saiyan 2 when Super Saiyan's skill took him there (`hud_skill_row`: the HUD's call to sub_080135A2 at
  0x0800BAE6 goes through a veneer in the retail native table's old place, 0x55098, free since the table moved). Super Saiyan 2's mastery
  trains (checked: 0 to 4 in about 15 seconds).
- The Skills tab scrolls to a fighter's fifth and sixth skills: its draw kept the first one shown no more than 4 before the cursor's row
  (0x08017392 `subs r1, #4`), so rows 3 sat off the two-row window; now 2.
- Super Saiyan 2's ki drained at Super Saiyan's rate (over six minutes): `ss_tick` takes three more units with each one the game takes,
  4x, about a minute and a half, less what mastery saves.
- Spirit Bomb's icon was the Kamehameha's (a retail stub row): a round ball in the bomb's colours, its greyed copy in the greyed icon's.
- Super 13 punched the air: the snow arena kept foes 16 px inside the open field, so a fighter at its edge was out of reach. Now the field's
  own bounds (x 32-288, y from 112). Dabura's behaviour also waited with his arms crossed while the fighter was far, and walked into the
  field's curved corner and stayed: `arena_chase` steps a boss that has walked 12 frames without moving straight at the fighter, and starts
  one walking after 90 frames of waiting. Checked from seven spots round the field: he reaches and hits a fighter standing at each.
- Super 13's finish: the Kid Buu fight's Spirit Bomb (the game's own disc, native 0xF4, in steady cyan) instead of the sprite, and the
  screen flashes white on impact (natives 0x7A/0x7B, the change's own flash; 0x4C only tints a character), the disc gone into him.
  19:39, "make the spirit bomb overlay on top of Super 13 so it looks like its hitting him rather than going behind him": the disc is
  drawn on BG0 at the fighters' priority (3), so they stood over it. `bomb_fx(40)` raises BG0 to 2 for the scene (`bomb_fx(0)` puts it
  back), and the bomb grows up from Goku's hands (its bottom edge stays put as it grows), so it covers Super 13 and never Goku or the
  text boxes.
- The LoG2 figures (armour Gohan, Trunks and Vegeta, Future Trunks, Android 17 and 18, Krillin, Tien, Piccolo): their slots were mapped from
  a misread of LoG2's numbering. Read off the frames: 2 is being hurt (it was their run), 4 a flinch (Gohan's and Trunks' ki blast), 5 the
  ki (fist in, palm out, arm out), 9 the change into the next form, 11 the power-up, 12 flying, 13 the dash (the run), 18 a sword or ki slash
  (armour Vegeta's Big Bang threw it). `actors.json` and `build.py` now give run 13 (or the walk where a record has none), ki blast 5,
  hit 2, power-up 11, flying 12, change 9; slot 18, held while Big Bang's code fires (frames 0 and 1 by turns), the arm out only;
  Kamehameha-code and wave moves a pose of their own in slot 31 (`held_poses`: the fist in, then the arm out; `beam_pose` in every
  such move's use). Armour Vegeta's Final Flash is his Galick Gun pose's charge and push. Gohan's (and Piccolo's) Masenko, slot 12, is
  arms up then the arm out. Armour Gohan's two Super Saiyan records were the wrong way round (LoG2's r56 is Super Saiyan, with its
  change into 2; r55 is 2).
- Changes and power-downs (`fighter_poses`): LoG2's own change where a record has one (base Vegeta, Trunks and Future Trunks to Super
  Saiyan; armour Gohan's Super Saiyan to 2), else the GT Vegeta pattern; powering down plays the change backwards, or the stance and
  the base's. It played the template's: retail green-gi Gohan, Great Saiyaman, kid Trunks. A `same_as` figure (Super Saiyan 2) took
  its source's record before `_powerup` replaced it, so it kept the template's; `build_actors` now re-points them. `_powerup` (the
  change on a Super Saiyan figure, into 2) was the figure's slot 21 or 9: punches, kicks, being hit, Gohan's green gi turning to stone;
  now his own power-up. Every mod figure's change and power-down shows its front in every view (`front_changes`), except approved
  figures and the owner's every-frame sheets.
- Broly: the playable one has his own copy of BF's figure (`broly_player`; the story boss keeps his), with his Eraser Cannon pose his
  ki blast's hand out; Full Power Broly's frame 0 there was the wind-up, so it flickered (relocked); his hit reaction is his stance,
  not a strike.
- Android 13 had only a walk sheet, so every move showed his stance or a step: `lib/a13_pose.py` redraws his near arm on his own frames
  (fist back, arm out, both arms out).
- Pan, every look (18:31, "Replace all Pan frames as well with these we fixed her walk frames"): the owner's every-frame sheets (bso_import
  `SHEETS`, folders `pan_v2` ... in `BFU_BSO`).
- Found by the whole-cast audit after the owner's list: Goku's Super Saiyan into 2 (Super Saiyan's skill again, or 2's) played the change
  into 3, his hair growing (`ss2_use` changes through `SS3_Use`); now his power-up in a slot of its own, 30 (`SS2_POSE`, `held_poses`;
  `to_ss2`). Pikkon's wave fired with his being-hit frames (slot 18 filled from 9): his ki blast's thrust, held. GT Gohan's Super Saiyan
  into 2 went back to black hair and glasses first (his Super Saiyan figure's slot 10 was the base's change): `_powerup` (test_frames 14).
- Great Saiyaman: from the Saiyan armour he came back in the school uniform (no `saiyaman_from_` row for it); now `saiyaman_from_armor`
  (form 162, forms.json `rows_after`: new forms go after the shelved Great Ape's 159-161 so no saved form id moves), and build.py stops on
  a Gohan outfit with no way back. His change into the costume was ten frames of his ki push (LoG2's default map): his arms up, then the
  school uniform's white flash into Great Saiyaman. Super Saiyan pressed as Great Saiyaman changed him into form 255 and the game jumped
  to garbage (the retail `SS_Can` only refuses when up equals down): `ss_can` now refuses a base form with no form above.
- Energy Punch (skill 8) and Gogeta's Dragon Fist Explosion (skill 5) show slot 19's frames 0-3 by number, then 2 and 3 in turn: slot 19 now keeps its
  frames in place when stretched (`sprites.INDEXED`; Majin Buu's, Janemba's and Super 13's longer boss attacks stay spread, `even`).
  Pikkon, Kid Buu, Android 13 and Full Power Broly held their stance (Broly his boss barrier); GT Goten a flying kick; Super Saiyan 4 Gogeta (the owner's sheet)
  vanished; Blue Gogeta never reached his arm out: their ki blast's wind-up, then the arm out (`fighter_poses`). DBS Gogeta's sheet map
  read slots 3, 7, 9 and 19 as charge, hurt, ki and idle: his ki blast showed the power-up and a hit the ki blast's arm out (`gogeta.py`).
- GT Trunks fired his Flame Kamehameha lying on the ground (slot 18 from his BSO figure, where 18 is getting up): found in the in-game
  move GIFs made for the owner (20:35, "Preview every fix as an animated gif too for everyones beam/ki blast frames at least");
  test_frames now checks no figure fires with its knockdown frames.
  The same footage showed Great Saiyaman over any other outfit flash the school uniform on the way back (BF's figure ends its change
  there): the `saiyaman_from_` forms now wear a copy, `saiyaman_outfit`, that ends on the white figure. And Broly's Energy Punch was his
  boss barrier (a golden shell): his ki blast's wind-up and arm out, as the other guests'.
- Gogeta after the ending: `gogeta_keep` put him in the party as soon as his flag was set, a moment before the reward's join, which then
  skipped his form, level and skills (test_zone26, by frame count); now only once he has his five skills.
- Super 13 after 60%: Dabura's behaviour keeps reaching for the flying special, which `no_story_walk` turns back into fighting (0x71), and
  there he stood where he was for the rest of the fight. `arena_chase` now also steps him at a fighter out of reach while fighting
  (40 frames without moving). test_super13 keeps him above 8000 HP for its 150 steps (once he chased, its fighter beat him) and checks he
  hits a fighter held at six spots round the field; a fighter held in the bottom-left corner after the long fight still takes no hits
  (likely: a boss moved by hand never landed a hit to his left in s13diag; from a fresh fight he hits there).
- Relocked as asked: the armour Vegetas, Broly Full Power; also Master Roshi (Krillin's frames under him had the same ki-blast and hit
  mix-up) and Blue Vegeta's two looks (their Blue power-up was his slot 21's punches). Each is in the review sent to the owner.
- 21:00, the owner on the move GIFs: "SSJ4 Goku does instant transmission on dragon fist and ssj4 Gogeta has a weird green outline also
  give all playable Buus forms kamehameha also fat Majin Buu energy punch looks bugged".
  - Super Saiyan 4 Goku's slot 19 (his BSO figure's, from base Goku) is Instant Transmission: the stance, a fade, a line. The Super Dragon
    Fist is the Dragon Fist's code, which shows slot 19 by frame number and carries him along with the dragon, so he vanished (Goku's
    Super Saiyan 3 has no Dragon Fist to do it with: see Nov 11 below). His slot 19 is now his stance, his ki blast's wind-up, then its arm out held. No
    form in that figure has Instant Transmission, so nothing else plays it.
  - The green on Super Saiyan 4 Gogeta was not in the game: the capture tool filled the Super Saiyan pools (+0x1E, +0x20) before it raised
    the EP maximum. The HUD (0x0800B99C) draws each pool as pool * 41 / the EP maximum columns from a 41-column table, and its two pool
    loops have no bound: past the table they wrote bar pixels wherever the next words pointed, here over sprite palette slots (127, his
    fur's shade, turned green). The same stray writes went on in every capture and audit of the evening. The tools now set the EP maximum
    first, `gif_cap.py` (the GIF previews' capture, with `gif_make.py`) checks the sprite palette is the game's own at the end of each
    capture, and the game caps both lengths at 41 itself
    (`outfit.c` `hud_row_guard`, on the way to `hud_skill_row`; test_nov10 7 reads the lengths at 0x0800BB8A: 0x8F each before, 41 now).
  - Kid Buu and Majin Buu have the Kamehameha (`guest_sync` `buu`; Janemba keeps his three moves). Their slot 18 is a boss move (Kid Buu's
    rush, Majin Buu's antenna beam), so the beam has a pose of its own (slot 31, `BEAM_FORMS`): the ki blast's wind-up while it charges,
    then its arm out, held. Neither figure has a frame with both hands out. The rule for any figure with no beam frames (21:20, the
    owner, on a try at Majin Buu's guard for the charge: "Never use guards as an attack frame, use ki blast frames but dont loop them
    just make it one smooth sustained transition on beams if none exist"): test_frames checks no attack shows a guard frame and a built
    beam pose holds one frame while the beam is out.
  - Majin Buu's Energy Punch was his boss record's attack spread over the ten frames (lightning round his head while held, and no punch):
    his ki blast's wind-up, then its arm out held, as the other guests'.
- Found that night, testing and shooting the trailer:
  - The World Tournament's Spopovich was stats row 111, the story's fight with Videl. Its behaviour (states 550-559) has a grab (558-559,
    `sub_0802C644`) that holds the fighter in the held pose only Videl's figure has, until five presses of the D-pad: anyone else became
    scrambled tiles, Spopovich's hold with him, for as long as the D-pad wasn't mashed. test_zone26 had passed while the grab's timing
    missed its fighter; after the frame-drop fix it was grabbed before the first punch and never got out (the suite's "opponent 2 took
    12 tries" was this, not timing: the loop is back at 12). He is row 112 now, as in the Time Chamber and under Super Garlic Jr. (no
    grab in that tree), and `zone26.rush_rows` stops the build on any post-game row with the 550-559 behaviour.
  - The Spirit Bomb skill's blast used the game's disc (native 0xF4, made for the Kid Buu fight's own room). It takes BG0's map and
    writes its picture over a few of the area's tiles, so in an ordinary area the blast emptied the layer of roofs and tree tops,
    scrambled every ground tile in those slots (a grid of little squares across West City's grass) and turned whatever shared its
    palette entry cyan; the Nov 9 build did the same. The skill now draws the sprite only: the orb swells to its largest picture for
    the blast and shrinks away (`spirit_draw`, `SKILL_SPRITE_ONLY`). The story's finish against Super 13 keeps the disc (the snow
    arena's map suits it). The white, black, white impact flash is as designed (`impact`).
- Nov 11, 00:15, the owner: "Fix those three things you mentioned SSJ3 goku too" (the three listed to him with the trailer: the Spirit
  Bomb skill's sprite-only blast, the tournament's Spopovich, and "the original game's Super Saiyan 3 Goku also vanishes during Dragon
  Fist Explosion"). The first two are the fixes above, now approved. The third was a wrong report, and nothing was changed for it:
  - No Goku can use a Dragon Fist as a Super Saiyan 3. Dragon Fist Explosion (skill 5, the retail row: can `0x08019E9F`, use
    `0x08019EB9`) is Gogeta's in the original game and here (`gogeta_skills`; the owner's 100% save: Goku holds 7, 15, 14, 20, 22, 12,
    Gogeta 7, 3, 5), and the Super Dragon Fist (41) is refused outside Super Saiyan 4 (`ssj4_dragon_can`). Skill 5 isn't in Goku's book.
  - The original Gogeta doesn't vanish either: his figure's slot 19 (actor 93, four frames) is the move's own wind-up and arm out, held
    at the dragon's tail while it flies.
  - The vanish was seen only with skill 5 poked into Super Saiyan 3 Goku's skills by a capture: his slot 19 (forms 5 and 6, actors 111
    and 112) is Instant Transmission's three frames, so he fades, and the move's fourth frame isn't there (junk tiles). Not reachable
    in play. If Super Saiyan 3 Goku is ever given the move, he needs a pose slot of his own for it (as `BEAM_POSE`), since Instant
    Transmission plays slot 19 too.
- Nov 11, 09:07, the owner: "Vegeta ssj4 transformation frames still off and can you remove the ssj4 Goku dragon fist scene and also
  give ssj3 Goku access to the dragon fist explosion or whatever not the same one ssj4 Goku has but the one from gogeta or whatever".
  - GT Vegeta's change (`gt.vegeta_changes`; this replaces the crouch of Nov 10 for the four looks with a form above them). The crouch
    was the wrong pose: his gloves are in front of his trousers in it, and under the change's aura that read as a lavender blob with
    no arms. His sheet does draw the game's change of form (slot 10, eleven frames: fists out, then the arms held out to both sides
    with a brighter flicker frame between, then the arms coming down), but only for the base looks. Now: base into Super Saiyan plays
    the sheet's own frames with the Super Saiyan stance's head from frame 2 (`_swap_head`: BF's changes show the old hair for two
    frames); Super Saiyan into Super Saiyan 4 plays the gold frames for two and then Super Saiyan 4's figure, made from the tank
    top's frames by the rules his sheet follows between the two (`_ssj4_body`: arms and shoulders to fur `V_FUR`, a bare chest strip
    under the neckline `V_CHEST`, the belt to trousers, the darker glove shade, the stance's head, and the tail from slot 19 frame 2
    drawn only where nothing else is, one row below the sheet's anchor so the fist doesn't hide it: `V_TAIL_LOWER`). Checked pixel for
    pixel against the pairs the sheet does draw (stance, crouch, Final Flash). Every view is the front's. The moustache look and
    Super Saiyan 4 itself have no form above them and keep the old pattern (never played). `test_frames.py` 6. Relocked with
    `BFU_RELOCK=vegeta_gt,vegeta_gt_tank,vegeta_gt_ssj,vegeta_gt_tank_ssj` (the owner asked for the change).
  - Super Saiyan 3 Goku has the Dragon Fist Explosion (skill 5, Gogeta's move, not the Super Dragon Fist 41). It is the 16th and last
    place in Goku's book (`SKILL_BOOK[0]`; the known bits are a u16, so his book is full) and comes with Super Saiyan 3
    (`skills_sync`: known once Super Saiyan 3 is known or held, into a free slot as every learned skill; with six held, SELECT on the
    Skills tab swaps it in; the place was the shelved Great Ape's, so a bit with no Super Saiyan 3 is cleared). Only a Super Saiyan 3
    can use it (`dragon_can`: the form is in `ssj3_goku_rows`, forms 5-8 and Kid Goku's; Gogeta's record is let through as before);
    it costs the retail 300, from the Super Saiyan 3 pool by his form's flags. The retail code shows slot 19's frames 0-3 by number,
    and Goku's slot 19 is Instant Transmission, so `dragon_use` runs the retail use and then points the sprite at `FIST_POSE` (slot
    29, `build.py fist_poses`, on actors 111, 112 and Kid Goku's Super Saiyan 3): his stance, his ki blast's wind-up, then its arm out
    for frames 2 and 3 (the move shows those two in turn while the dragon is steered: one held picture, no loop, no guard frame; the
    owner's rule of Nov 10). The update code shows frames by number without resetting the slot, so the pose stays. The row is patched
    before the skill table is copied out (the game reads the copy at the pointer in `0x13618`). Its text (UI string 1321) says who
    can use it. `test_nov11.py` (in game: the pose on every Super Saiyan 3 form facing left and down, the cost, Instant Transmission
    after it, no other Goku form, Gogeta's unchanged, the book), `test_frames.py` 15.
  - The trailer loses the Super Saiyan 4 Dragon Fist shot (cut 8).

### Checking every move
`python3 ultimate/figure_diff.py OLD.gba NEW.gba` lists every actor slot whose frames changed between two builds (by pixels, every view)
and any form id that moved: run it after each sprite or build change and account for every line. `python3 ultimate/pose_strip.py` draws
the poses an audit recorded as clean strips for the owner's previews.
`python3 ultimate/audit_moves.py ROM OUTDIR [form ...]` (a `--debug` build, no `--enemy`) plays every wearable form in the field: walking
four ways, running, the punch combo, each skill held and let go, its changes up and down; every pose the game shows is drawn from the ROM,
one sheet per form (`NOPNG=1`: only the poses), and `report.txt` flags poses with no frame, another retail character's frames, being-hit
frames in a move, a double-tap that didn't run and a change that didn't happen. It fills Super Saiyan's and Super Saiyan 3's pools
(+0x1E, +0x20) before picking a form and before each change, or a Super Saiyan 3 or Blue form drops back on the Switch screen; the EP
maximum (+0x1C) goes up first, as a pool above it is outside what the game ever holds (see the green outline above). Some flags
are the design, not faults: a change that didn't happen where it is gated (Super Saiyan 3 only from 2, Super Saiyan 4 only in a GT look,
Blue and God after the Battle of Gods), and likely scene-only retail forms (1, 9, 11, 12, 23, 24, 32, 33, 42, 43, 48, 51, 53: not on the Switch
screen) with no ki-blast or run animation, as in the retail game. Look at every sheet after: a wrong pose (a wind-up where
the arm should be out) isn't something it can see. `test_frames.py` 10-13 check the ROM directly: no template leftovers in any playable
figure; Big Bang's code's two held frames one pose; run, ki blast and beams not the being-hit frames; changes and power-downs one view.

### Reading a fight from memory (for captures and tests; from the trailer's reshoot, Nov 10 night)
The owner, on the trailer: "maintain absolute certain no bugs show in any clips or any stupid behaviors by the bot/player that make no
sense". A recorded fight take is kept only when the recorder has seen, frame by frame, that the move landed, that a follow-up strike
landed, and that the fighter was not touched. What it reads:
- A foe's health is the word at its object +0x28C (>> 10): a frame where it falls is a hit that landed. A guarded beam still costs a
  little each frame (4-10 where an open hit costs 70-150).
- The fighter's health can't show a hit on him: with a capture's raised stats a hit costs 0 (a red "0" over him) and his health never
  moves. His object's word at +0x34 is the red hit flash's palette, 0 when he isn't flashing: that is the test. His animation (+0x50)
  being his figure's slot 9 or 17 (hit, knocked down) is a second one. Slot 18 is not "getting up" here: it is the beam pose for a
  figure with no slot 31, so it mustn't be in that test. The Super Dragon Fist lights the fighter through +0x34 too (no flash test
  during it).
- Standing a fighter a fixed distance beside a foe "wherever he is" can put him behind a ledge (the Cell Games' last room) or outside
  what the camera can show (the Time Chamber's right side): stand the foe on open floor first.
- Seen while shooting, and likely the fighters' own behaviours from the original game (not faults): Kid Buu splits in two a few
  seconds into a fight (each with half his health; a clash take needs the copy beaten first), Super Buu fires his beam as soon as a
  fighter stands in line with him, the tournament's fighters and Majin Vegeta are out of reach of a strike thrown from 40 pixels
  (Future Trunks's sword landed from 24), and Broly leaps away after a combo.

## The Great Ape: shelved (Nov 10)
The owner: "Remove the whole great ape thing from the game and shelf it for now it just looks bad honestly needs a redo for sprites". The
raid, the form, the Chou Makouhou, the twice-size drawing and the camera lift are out of the build; all of it, with its notes, is on the
branch `shelf/great-ape` (commit aeac6a6). Its ids stay taken so a save from the Nov 9 build reads nothing past a table: skills 48 and 49
are empty rows and forms 159-161 copies of the GT looks they changed from (`build.py` `SHELVED_SKILLS`, `SHELVED_FORMS`), and
`outfit.c shelved_fix` puts such a fighter back in his own look, takes those skills out of his slots (the selection stays on the skill it
was on) and clears book bits with no book entry (`test_shelved.py`). Such a save may also hold the raid's more flags 64-67 in the bench's
first four spare bytes: clear them before giving those bytes another use.

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
  progress (more flags 49-57). Natives 0xF8-0xFF are all taken, so the quest asks `more_get` (251 area, 252 Goku playing, 253 the quest can
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
- Made thorough like Garlic Jr.'s (the owner, Nov 9: "Same for Battle of Gods too if possible"): Beerus waking and the Oracle Fish's
  prophecy, King Kai's warning, Vegeta's Bingo dance, Buu and the pudding, the others falling at the party, Whis as Beerus's teacher, the
  god ki fading but staying with Goku (58 steps). Battle of Gods now waits for the Garlic Jr. quest (`outfit.c` `more_get(253)` needs
  `MORE_GJ_DONE`).

## The Garlic Jr. quest (Nov 9, post-game, before Battle of Gods)
The owner: "adapt the Garlic Jr Dead Zone movie a bit ... condense it like how the Broly fight is", Garlic Jr. "based off Pilaf/Yakon",
"make sure his outfit is accurate". `ultimate/garlic.py` holds the quest (66 steps, 39 lines, 2,500 characters in dialogue bank 8);
`test_garlic.py` plays all of it (its rig's official warps to the Lookout: `BFU_HUB_WARP="6, 1, 1, 312, 400"`).
- After the ending, Dende and Mr. Popo on the Lookout tell the Dead Zone story (Garlic Jr.'s wish for immortality, Kami, Gohan sealing him)
  and of the Makyo Star; Mr. Popo's carpet takes Goku to Hercule City under the Black Water Mist: the street's people stand aside, two
  Makyans fight (beat one: the count; lose to the other: both back; both down: the street clears and Hercule comes out). Hercule sends Goku
  up Korin's Tower; Korin's Sacred Water cures the town; Hercule sends him to the Lookout, which Garlic Jr. and the Spice Boys hold (Dende
  and Mr. Popo his prisoners, Piccolo's line about his father and the guardian's post). The Spice Boys one by one with a scene between
  each (lost: back to the Lookout, from Spice again), Garlic Jr. himself (lost: from him again), the Makyo Star's change, Super Garlic Jr.,
  and the Dead Zone seal as in the movie (the press-fast meter), Dende and Mr. Popo freed, Garlic Jr.'s Necklace (gear 167) and 300,000
  Zenie. More flags 58-63; the Lookout's fights and scenes are twelve copies of the Lookout in zone 26 (a dialogue box with a boss loaded
  resets the game, so every scene has its own room).
- Garlic Jr. (`lib/garlic_art.py`): Pilaf's head on kid Goten's fighting body (every slot; no fusion or Super Saiyan frames, "he doesn't
  need them"), the white cloak with its red lining, the black cassock with the castle shield, cyan cuffs and hem, blue shoes (Budokai
  Tenkaichi 2's artwork and Dead Zone stills). The Spice Boys and the Makyans are fighters of the same build recoloured (ranked search):
  Spice = BF Vegeta, Vinegar = Olibu, Mustard = Idasa, Salt = kid Trunks, the Makyans = the Majin fighter.
- Super Garlic Jr. (`lib/super_garlic.py`; the owner: "make his Brain look right remove the back spikes give him his big ears ... if you
  gotta use someone else like Spopovich legs and frames try it", "Remove the singlet too and use the half of his body without the singlet
  to duplicate ... fill his abs in PERFECTLY accurate to the art style, and then remove the majin head symbol and give him the brain
  grooves", "Fix the pants and waistband too and don't let it ever overlap the arms"): Spopovich's frames (actor 243; Yakon's had one
  three-quarter figure for every view and spikes on his back). Per frame and view (`sprites.viewed_actor`, `tint_of` with `by_view`):
  the singlet off (front and back: the bare half mirrored about the body's measured axis; what the mirror can't give, and side views, his
  own skin reflected across the gap's edge), the Majin mark found and replaced by the cranium's folds (a central crease, grooves curving
  down the sides), broad pointed ears drawn only where they meet his head, a snarl with fangs over a shut mouth; below the waist the skin is
  shared between arms and legs by a walk from his upper body and from his boots that never crosses an outline (an arm wins a tie), so the
  baggy black trousers and the white sash (with its cord in front) never cover an arm; teal skin, pale teal boots. `FRAMES` holds what
  can't be measured in nine of the 57 frames (flying, kneeling, a head hidden). He fights on Spopovich's row 112 (also the spar's).
  `test_frames.py` checks every frame: Spopovich's slots, no tan skin or yellow boots, no Majin mark, teal, the sash, the ears.
- Balance (the owner: "Test these with a level 150 Goku or something so he doesnt die so much and has some balancing"): `fightrig.py`
  makes the tests' Goku a level 150 fighter the game's way (EXP at the cap, health and ki grown by the game's level-up formula with
  average rolls: 7,503 and 3,540; the 420 points spent evenly: Strength, Power, Endurance 167/167/166) and measures each fight with a real
  exchange. The old tests poked Goku's health to 0x7FFF, which the quests' level-ups pushed past 32767 into negative numbers. At level 150
  he needs about 10 hits for a Makyan (30,000 HP), 16-24 for a Spice Boy (40,000), 25 for Garlic Jr. (55,000) and 42 for Super Garlic Jr.
  (75,000); their hits take 2-9% of his health, Super Garlic Jr.'s about 7%, no more than Beerus's (3-9%; his god fight's legs take
  22-43 seconds of mashing each, measured the same way in `test_bog.py`). `test_garlic.py` checks these ranges.
- Found on the way: a defeat script waits while a level-up box is open (the Makyans' count looked broken in the tests until the box was
  closed), and a test that poked Goku to 1 HP after the game had already revived him walked him into the next fight at 1 HP.

## Zone 26 and Super 13

The build also needs Prototype D (`BFU_PROTO`), Legacy of Goku II USA (`BFU_LOG2`) and a `log2-decomp` checkout next to this repo (its map index locates the snow tiles). `ultimate/zone26.py` builds areas 26:1-15 from the prototype's layouts and collision with `ultimate/reskin.py`'s tiles; `ultimate/zone26.json` lists the doors. After `python3 ultimate/build.py --debug --zone` (walking down on Snake Way enters the zone), run `python3 ultimate/test_zone26.py`.

Script limits found here: the assembler's `push`/`call x(n)` only encode values up to 255, so write `pushn 622` and then `call flag`. Dialogue lines over roughly 100 characters reset the game; split them.
