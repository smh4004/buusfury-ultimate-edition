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
  - The trailer loses the Super Saiyan 4 Dragon Fist shot (cut 8): its two bars went to the Spirit Bomb (the same frames, a little
    slower: after them the two fighters only stand there), the beam struggle, the Skills tab, the first roster shot and the Challenge
    Board. The roster changes fighter every 20 frames, so the first roster shot ends on Kid Buu and the later one starts on Tien's
    first frame (292).
- Nov 11, 11:26, the owner on the previews (the in-game GIFs and the before/now sheet): "Looks good reshoot it and send new rom after
  too". The four GT Vegeta looks stay locked on the new frames. Trailer cut 9 is cut 8 with his Super Saiyan 4 shot retaken on a rig
  built from this code (the same take, place and timing). Delivered: release, debug and debug zone from commit 7dcde33, the very ROMs
  the full suite ran on (32 scripts, 1,101 checks, none failing).

- Nov 11, 11:56, the owner on the trailer's first clip: "Remove the robot in the area with the Broly fight and also remake the trailer
  without that robot in the first clip with Broly".
  - The robot is the original game's post-game Pirate Robot (stats row 100, character 240: the black one with the blue glow, 27,824
    HP, 236,265 EXP), which the game stands in nine places once the ending is seen (condition flag 149, or 180 in the volcano's caves);
    one of them is Volcano Summit (15-32), beside Broly, and the two fight each other. `zone26.clear_summit` takes that one record out of
    the area's list; the other eight stay. Broly (row 10, while flag 111 is clear) and the story's War Machine (row 140, flag 119 until
    the ending) are untouched. `test_story.py`: no fighter with its health in the room, and the area's list in the zone and release ROMs.
  - What the robot had been hiding: Broly's first conversation (script 435) is short of sprite memory. The actor list's allocator
    (0x0801124C; 32 KB, best fit, 64-byte units; a block cut off a larger one is never joined to it again) has one free block of 9,152
    bytes there and the conversation takes all but 960 of it. With the robot in the room the robot's 4 KB was taken instead (it
    vanished as the box opened; nobody missed it). With it gone, a Super Saiyan 2 lost Broly: the lightning's bolts (`outfit.c crackle`)
    were 1 KB sparks, two out together cut 1 KB off that block for good, and the conversation then took Broly's own 4 KB, so he wasn't
    drawn while he spoke (found retaking the clip; base, Super Saiyan and Super Saiyan 3 were fine). A bolt is at most 10 wide and 14
    tall, so each is now stored as the 16x16 piece that holds its four frames (256 bytes, `build.py BOLT_PIECE`; the same pixels on
    screen: 120 frames of a Super Saiyan 2 compared between the builds, none differ), and a bolt is only drawn when a free block holds
    it, never by taking another sprite's memory (`bolt_room`). `test_story.py` reads Broly's sprite memory slot (object +0x0C, 0xFFFF =
    none) while he speaks to Goku, a Super Saiyan and both Super Saiyan 2 looks.
  - Trailer cut 10: the first clip retaken on that build (`v7/broly_talk_new.py`), the same take.

- Nov 11, 12:01-12:06, the owner on the unlock list (`BFU_Unlock_List_Nov11.pdf`): "Keep the Android unlocks from the super 13 fight, keep
  full power Broly. Unlock the saiyan armor for Gohan trunks and vegeta after beating the Cell Games along with future trunks ... Change
  Piccolo Krillin and Videl to tournament unlocks ... make Gogeta DBS and SSB unlock from Battle of Gods ... keep DBZ Gogeta as an unlock
  how he was in base game from getting all the exhibits ... [Super Saiyan 4 Gogeta] the hardest trials or tournament reward for now".
  Every outfit keeps a flag of its own (`outfits.json`; a debug build sets all of those below 2000 at its start, so a prize's own "paid"
  flag can't double as one); what changed is who sets it:
  - Super 13's reward sets 876 (Full Power Broly), 877 (Android 13) and 880 (Androids 17 and 18), and joins Android 13. It no longer
    sets 873-875, 878 or 879, and no longer joins Gogeta.
  - The Cell Games' prize (`cell_won_go`, `CELL_UNLOCKS`) sets 873-875 (the Saiyan armor) and 879 (Future Trunks; it was Piccolo's).
  - Krillin and Videl are on 2000 with Yamcha (the Normal bracket), Piccolo on 2002 with Pikkon (the Hard bracket); the Dojo's Piccolo too.
  - Gogeta (`outfit.c story_sync`, once the ending is seen): the original game's look (878) opens with all 15 Z-Fighter exhibits in the
    museum (their count is the four flags from 346, the official's "of 15 Z-Fighter exhibits"; likely the original's own condition for
    him: its scripts give nobody a reward for the count, so this is the owner's account of it); DBS and SSB Gogeta are on 2053 (Battle of
    Gods finished), Super Saiyan 4 Gogeta on 2046 (all four Trials II). His slot joins the party the first time one of his looks is open,
    wearing it (`gogeta_open`); `gogeta_keep` keeps him on any of them.
  - A save that already has a flag keeps what it opened (873-875, 878, and 879 now means Future Trunks); Piccolo, Krillin and Videl
    wait for the brackets. A look that is worn stays worn; Up and Down only skip it afterwards (`cycle`).
  - Tests: `test_zone26.py` (the reward's flags with all eight cleared first, Android 13's join, Gogeta's join by himself, the
    exhibits' flag with 15 and with 14), `test_cell.py` (the prize's four flags), `test_nov10.py` 6.
  - Still to do from the same list: Vegito as a Potara fusion opened by all four Trials, Super Saiyan 4 Gogeta as a fusion of Super
    Saiyan 4 Goku and Vegeta, and Teen Gohan for the Cell Games (LoG2 has his purple-gi base, record r50; his Super Saiyan and 2 only in
    the armor, r56 and r55, which Gohan's Saiyan armor already uses).

- Nov 11, 13:26, the owner: "Did the super 13 fight with DBZ Gogeta, noticed it swapped back to Goku for the spirit bomb scene and then
  when going back to the switch character menu after winning Gogeta is stuck permanently fused and Goku and Vegeta aren't selectable. I
  guess add a rule to make the Super 13 fight specifically only startable and maybe only playable as Goku just to avoid bugs like this,
  and revert any fusions if a player fuses mid fight for the spirit bomb scene just in case".
  - What a fusion is in the party records (read from the game's code and scripts): record +0 bit 0 = in the party, bit 1 = selectable on
    Switch Character. The Fusion Dance (skill 12, global script 13, script native 0xA8) clears bit 0 of both dancers, sets both bits of
    the fused fighter, writes the dancers' slots into his +2 and his time into +8 (frames; -1 no limit). The fused fighter's own tick
    (0x0800E15C) counts +8 down only while he is the one playing, and at 0 runs global script 14, which runs 503: the fused fighter
    leaves, the dancers join and are made selectable (natives 0x98, 0x97, 0x99), and the dancer who started it plays (0x95).
  - What broke: the Spirit Bomb finish makes Goku play (0x95(0)), which stops that clock for good with Goku and Vegeta still out; and
    Gogeta's "no time limit" as a fighter of his own (`gogeta_keep` on Switch Character, `party_join` from the reward) then fell on the
    danced Gogeta, so nothing could end the fusion. (The same after any scene that picks who plays: a Trial's set hero, the wish.)
  - `outfit.c fusion_end` (after the ending only: the story has fusions of its own): a fused fighter who isn't the one playing leaves
    and his dancers come back, selectable, as script 503 does; one who is playing with no time limit gets one frame, so the game ends
    his fusion itself. It runs with `gogeta_keep` (every 32 frames in play, and on Switch Character), and for Gotenks too. `gogeta_keep`
    and `party_join` give Gogeta "no time limit" only while Goku and Vegeta are both in the party (he is his own fighter then, not a
    dance's). So a save stuck that way puts itself right, and a danced Gogeta keeps his clock and splits when it runs out; once split he
    joins as himself again if a look of his is open (`story_sync`).
  - Super 13's fight is Goku's: the doors into it (zone26.py, area 14's top door: to Android 13, or straight to Super 13 mid-fight) open
    for Goku only (`more_get(252)`) until Super 13 is beaten; for anyone else a trigger on the same ground runs the quest list, which
    says "Only Goku can win this fight. He steps in.", ends any fusion (`more_get(250)` = `fusion_end(1)`), makes Goku play and takes
    him in (`build.py quest_npc_story`, its last two steps). The Fusion Dance can't be used in the fight's four rooms (`fusion_can` on
    skill row 12). The finish calls `more_get(250)` too before it makes Goku play.
  - `test_fusion.py` (debug zone build). The dance's button game can't be played by a script (five random moves; a wrong one gives the
    fat or thin Gogeta, a scene of about five seconds that ends by itself, in the original game too), so a danced Gogeta is set up as
    native 0xA8 leaves him and the next door builds his figure. Checks: his time counts down after the ending (the build before: -1);
    at the door the message, then Goku in the fight's room with Goku and Vegeta back and selectable and Gogeta his own fighter; the
    dance in the fight doesn't start, outside it is danced as ever; his time running out splits him the game's way; the stuck state
    heals with Goku playing and with Gogeta playing.
  - Found by that full run as well: `test_slots.py` pressed RIGHT five times for the guest slot, but a debug build's Gogeta now joins
    by himself (his Dragon Ball Super looks are open there), so the guest is the seventh fighter; and its list of open guests follows
    the moved flags (Future Trunks on 879, Krillin, Videl and Piccolo past 2000). The test's own navigation, not the game.
  - And Super 13 "punching the air" again (`test_super13.py`: a fighter held at the field's left edge, (32, 200), took no hit in twelve
    seconds; Super 13 stood at (56, 208), 24 px across and 8 down, inside the reach `arena_chase` let him stand at, punching). A punch
    goes straight out the way he faces: fighting in place for a second and a half with no hit landing (the fighter's health hasn't
    dropped), he now lines up with the fighter on the nearer axis, then closes to 16 px on the other.
- Nov 11, 13:51 and 14:53, the owner: "can you give every single new boss fight a custom health bar too", then "Add health bars to all
  the bosses in game right now and reuse Buus fury assets for it for now. We can make new bars later." And at 16:01, of the bar the mod
  first drew by itself (the fighter's HUD turned round in the top right corner): "That's not what I meant by the boss hp bars at all.
  Use the ones that already existed in Buus Fury for boss fights."
  - Buu's Fury has a boss bar: the slanted red bar that slides in at the top right of the story's boss fights (Broly's, for one).
    The first attempt was built on a wrong reading ("the game draws no enemy health at all") and never looked for it; it is gone,
    all of it. Look at a story boss fight in the unmodified game before building anything the game may already have.
  - The game's bar: an actor of the HUD's layer (vtable 0x0804CE28) made by 0x080195A8, which the story's scripts call through
    natives 0x8F (a target, the whole bar) and 0x90 (a target and a part of the bar, for a boss in phases); native 0x91 sends it
    away (message 0x13: its speed byte +0x17 becomes 0xFF and it slides up off the screen and off the list). Two 32x8 sprites at
    x 160 and 192 on 0x200 bytes of tiles (art 0x087196E4), 53 slanted columns of four pixels (table 0x087198E4) blacked from the
    right (0x08019658). It shows its target's health (the enemy's method at vtable +0x64, 0x0804F874: health x 53 / the row's
    health, rounded down) plus its byte +0x15, or with no target that byte alone. Its 'shown?' (the fourth of its ten functions) is
    a plain yes, so it stays up through text boxes: Broly's stays, empty, through "Goku has reached level 73!" until his script
    sends it away. `lib/bossbar.py` is its model.
  - The mod's fights have no script that makes one, so `outfit.c bossbar_tick` asks the game for it (the same call as native 0x8F,
    with no target) at the player's input while the HUD is shown, and nothing of the mod's is drawn. Who gets one
    (`zone26.boss_table`, a byte per stats row in the ROM): every row the mod adds (`foe_names`, in the order `rush_rows` makes
    them, which checks the count) but the Makyans' pack, and Android 13's and Super 13's. The room's boss is the foe whose row has
    the most health; foes of one name share the bar (the three Cell Juniors: their health added up, out of the most there was).
    The story's own boss fights are not touched: their rows are not in the table, and while any boss bar is on the list none is
    made (one of the mod's leaves at once if a script makes the fight's own).
  - The mod's bars answer with the game's table of ten functions with one replaced (`bossbar_vt`, filled by build.py: 'shown?',
    asked every frame, is `bossbar_visible`): there the columns are kept by the game's rule (rounded down), and when the boss has
    no health left, or is gone, the bar is emptied and told to leave the game's way (+0x17 = 0xFF). The game holds its actors
    still while a text box is up, so after a fall the empty bar waits for the box to close, exactly as the story's do.
  - It is there from the fight's first moment, on the screen or not (Semi-Perfect Cell starts his fight 33 pixels above the top
    edge; a first version that waited until a boss was seen or hurt came up late there).
  - A table the build fills in after compiling must be `volatile` in outfit.c when the code reads fixed places of it (`boss_tab[0]`):
    the compiler otherwise uses the `{1}` it saw (the bar never came up; `bomb_frames` is read by a variable index, which hid this).
  - `test_bossbar.py` (debug zone build): the ROM's table whole; the game's art, columns, maker and table unchanged in the ROM; the
    mod's table the game's but for 'shown?'; no bar on the way; in Android 13's room the game's bar actor, one, at rest, full, its
    tiles the game's art; there with him off the screen; half, one point (no column: rounded down), a real punch; at his fall
    empty and told to leave; none in his change; Super 13's own. `lib/barcheck.py` reads the bar back from the actor list, OAM
    and sprite memory and is called in the other tests' own fights: `test_cell` (each Cell, the Juniors' shared bar going down as
    they fall), `test_ladder` (Hard bracket, Hercule, Goku Black and Rose, Ledgic, Uub and Majuub, Trials II, the Dojo),
    `test_chamber` (every sparring partner), `test_bog` (Beerus), `test_garlic` (each of them; the Makyans none), and
    `test_story` (Broly's own bar is the game's, made by his script with him as its target: one actor, as before the mod; with him
    fallen it is that one bar, empty, or none, and never one of the mod's; when his last scene is over none is left).
  - The suite (34 tests) passed but for one line of `test_story` (run again by `test_dragon`): it expected no bar at all 500 frames
    after Broly's fall, and the game keeps his, empty, through the level-up text. The line was the test's mistake about the game; it
    now says what the game does, with the end-of-scene check added, and both tests pass on the suite's ROMs.
- Nov 11, previews. Beerus's was approved at 17:56 ("New side view and 34 pixels for sure looks better") and is in the build;
  Teen Gohan's waits for the owner's word and is in no ROM.
  - Beerus (16:01 "improve the Beerus portrait and sprites a lot"; 16:16 "Preserve the front view"; 16:28 "back view isn't that bad
    the side view sucks though"; 16:55 "Don't draw a whole new view just base it off a buus fury shape or the existing sprite
    already and fill it in better"; 16:59 "Maybe super janemba tbh"; 17:02 "Use janemba but fix the eyes and ears and maintain
    visual clarity and attention to detail"; 17:03 "make the sprite a bit taller potentially but not janemba full height").
    `ultimate/beerus_preview.py OUTDIR` makes the pictures he was sent: a new side head on Super Janemba's shape with the owner's
    own ear, eye and earring pixels (`lib/beerus.py HEAD_SIDE_NEW`), and Beerus 2 or 4 rows taller by seams through Kid Buu's bare
    chest and trousers (never his belt, wristbands, shoes or head; `Beerus.frame`), in every frame of all three views. Standing he is
    30 rows before (Goku 31, Super Janemba 59) and 34 now. Both are in the builder, switched by `build.py BEERUS_LOOK`, which says
    `'new,2,2'` since his approval (with `'old,0,0'` the release ROM was byte for byte the one delivered before, sha1 b9c57edd...).
    A frame that outgrows its box keeps its pieces where they are and gets strips of 8 pixels for the rest
    (`sprites.composed_actor`: one 16x8 or 32x8 piece above a standing frame, 8x32 past the feet of a lying one); his largest
    frames then take 1,792 bytes of the 2 KB his record reserves. `test_beerus.py ROM` reads every frame of his back from a built
    ROM as the game lays it out and compares it, pixel for pixel, with what `lib/beerus.py` makes (188 frames, mirrored ones too),
    checks each piece is a size the game draws and fits his sprite memory, and that he stands 34 rows to the front and back and
    33 sideways with his feet where they were. `test_bog` passes with him so, and its screenshots show him whole in his scenes
    and fights.
    He has no portrait: `bog.say` shows his lines in the narrator's box.
  - Teen Gohan in the purple gi, base, Super Saiyan and Super Saiyan 2 (12:01 to 13:12): `ultimate/teen.py` with `lib/headfit.py`
    composes all 212 frames from LoG2's records and checks every one (a frame that can't be placed or fails a check stops it).
    Not wired into the build; his preview PDF and GIFs are with the owner.
    Approved Nov 11, 18:12 ("Teen Gohan looks good to lock"); wiring him in as his own fighter (apart from adult Gohan, both outfits,
    opened by the Cell Games) is still to do.
- Nov 11, 18:55, the owner: "Change Beerus beam attack to actually fire from the hand and also give him his own custom light yellow
  Frieza style finger beam attack not kamehameha called Wrath of the Gods". `lib/wrath.py` tells all of it. What he had was the
  game's enemy beam (Kid Buu's behaviour: start 0x08033002, each frame 0x080330AA, named by the one word at ROM 0x331D0), whose ball
  and beam are laid at steps set for Kid Buu's figure (0x0875925C): on Beerus the beam left from his shins, 11 pixels under his hand,
  and 13 pixels to one side of him from the front and from behind (firing straight up it missed a player standing right above him).
  Now the word at 0x331D0 names a copy of that table whose first two entries are `outfit.c wrath_start` and `wrath_update`: both run
  the game's function and do nothing more unless the fighter's figure is Beerus (`wrath_who`). For him: the beam object gets his own
  table of levels (`wrath_params`: the Kamehameha's damage and strength, his rows), the ball and the beam are moved to his fingertip
  (`wrath_at`, made by `wrath.places` from `FINGER`, his fingertip in the arm-out frame per facing), and his pose is the ki blast's
  wind-up, then its arm out, held (the owner's rule of Nov 10; the game showed the two arm-out frames by turns, which from the front
  are two different arms). Nothing is drawn new: the beam is the Kamehameha's level 1 frames with the near end, body and travelling
  tip squeezed to half their width about the middle line, the glint before it is the Kamehameha's smallest ball, and the blues become
  the game's light yellows (`TINT`: colours the palette already has). Strength, reach, time and what it hits are the enemy beam's.
  The name shows nowhere in a fight: the game has no place for an enemy move's name.
  Trap met on the way: a `const` array that build.py fills after compiling must be `const volatile` when C reads it at a constant
  index, or the compiler folds the placeholder's value in (the first try copied 64 bytes from address 0 into sprite memory).
  `test_wrath.py <beerus rig> <kid buu rig>` (48 checks: rigs `BFU_RIG_ENEMY="61 421"` and `"61 47"`): for each of his four facings
  the beam's near end is at his fingertip and its middle line through his hand (its place in the game plus its rows read back from
  the ROM), its tiles hold the light yellows and none of the blues, the pose is held, it hits the player in line, no bad jump; and
  Kid Buu's figure on the same row fires the game's beam from the game's place with the game's frames. Before/after GIFs of all
  four facings went to the owner at 20:40; his word on the look is awaited.
- Nov 11, evening: Super Saiyan 4 Goku's touch-up, as previews first (the owner, 18:13: "Don't make changes to SSJ4 Goku without
  verifying first"; approved at 21:01, see below). `ultimate/ssj4_preview/preview.py OUTDIR` makes the pictures of the fourth look from
  a ROM built before it (the figure is `v4.frame(slot, frame, view, kind)`). What it holds, with the words that asked for it:
  - 18:44 "use the new Gogeta hair for the front view of SSJ4 Goku only, and leave the side and back views as the original";
    20:10-20:12 "I don't want that gray strands in the front just the same colors as current"; "just the Gogeta front view hair for
    both appropriately colored". The front head's hair is Super Saiyan 4 Gogeta's shape (rows 0-13, then strands: `v4.front_hair`),
    in black and the one dark grey his hair has now. A hand raised beside his head stays in front of the wider hair (`v4.uncovered`).
  - 19:17 "Stop with this head bob on the idle stuff": his second idle frame was the first with its top 16 rows a pixel to the left
    (the sheet's); the two are one frame. (Every other figure's idle: see "the idles" below.)
  - 19:17, 19:29, 19:31, 19:33: "you managed to mess up the fur on the hands and arms"; "make sure the fur is always on his full
    arms in every frame and only his hands without it"; "Do this check for both SSJ4 Goku and Daima SSJ4"; "Don't take fur off the
    tail either". The sheet was drawn on BF Goku's frames, so BF Goku's own frame says what is what: sleeve, arm, wristband, hand.
    `armhand.clean` and `fists` fix what can be told from the two frames alone (a hand is the skin beyond a wristband the sheet also
    has). They cannot tell everything (a band drawn in two pieces, a fist joined to its forearm, the tail lying where BF's hand
    is, an elbow seen from behind, which has no band), so every one of the 146 distinct frames was read as a letter map, BF's beside
    the new one, and the rest is listed by frame in `armhand.py`: `FISTS` (hands drawn as fur), `ARMS` (arms left bare), `BANDS`,
    `SLEEVES` (BF's sleeve kept blue: he has none) and `PIXELS`. 50 frames change. Four frames had it inverted (bare arm, fur
    hand: ki blast and punch from behind, the knockdown). The Kamehameha from the front follows the owner's own Gogeta, drawn on
    the same frame: fur down to the wrists, hands of skin under them (`v4.kame_hands`). The tail is never touched.
    Left alone: the frames that show base Goku's head or bare arms while he changes (slot 10, slot 8's frames 3-10, 13.1) and the
    fusion frames (the owner, 18:25: fine).
  - Eyes gold on the GT form; the back head's stray light pixels gone (`v4.STRAY`).
  - Daima (18:25 "additional Daima SSJ4 recolor"; 18:44 "Make the eyebrows red too"; 18:45 his picture's notes; 19:17 "make his
    eyes the color to match the hair and eyebrows and then fix his boots color so they actually look right with the blue and the
    red stripe in all frames"): two colourings, A (reds) and B (his picture's plum), his choice awaited; boots are BF Goku's own
    where the frames agree and the sheet's own boot elsewhere (`v4.boots`), blue with a red lace in every frame.
  - Asked of the owner and open: whether the GT form's leg, painted boot-black from the thigh down in about ten frames (the sheet's),
    should be trousers as on Daima. (Daima: B, the plum, 20:53.)
- Nov 11, 20:53-21:02, the owner on the fourth look: "Fix the arms raised pose for Goku ssj4 on both where his base form hair is on the
  sides while his ssj4 is in the center. Also use B plum for daima"; "The rest of Goku frames look good on pass"; then "Lock that Goku
  for now and show me ssj4 Gogeta again after"; "Daima ssj4 can be a post game unlock for now just save it".
  - The arms-raised pose (the power-up's second frame, slot 13 frame 1; BF's faces the camera in all three views): the sheet had kept
    BF Goku's whole head (black spikes out past both arms, his shouting face) and furred three columns of four on each arm.
    `v4.arms_up`: BF's head comes off, Super Saiyan 4's front head goes on where BF's eyes are (two rows higher than standing), its hair
    behind the raised arms and fists, the arms fur all the way.
  - In the build since then. `gt.py` makes him from the sheet as before; `build.py ssj4_goku` then puts every frame of that figure
    through `sprites.composed_actor` with the table `ssj4_preview/ssj4_table.py` makes from the ROM so far (the frame's pixels on its
    own box -> `v4.frame(slot, frame, view, 'mix')`): 146 frames change, 39 outgrow their 32x32 piece by up to 3 rows or 2 columns
    (the wider, taller hair) and get strips, as Beerus's taller frames do. A frame the figure has twice is touched up as its first
    place in the figure, slot by slot (the special's frames 4 and 5 are the change's 6 and 7: `armhand.py` lists them under both).
    Slots 22 and up (the charged punch, still BF Goku's own frames: to fix next) are left. The preview tool reads a ROM from before
    the touch-up (`BFU_SSJ4_ROM`; the Nov 11 night delivery is one).
  - `kid_goku_ssj4` is in `locked.json`. `test_ssj4.py ROM` (14 checks, no emulator) holds a built ROM to it: his idle still, the
    front hair's shape and its two colours, gold eyes, no stray pixel behind, every listed hand skin and every listed arm fur, no
    sleeve left blue, the Kamehameha from the front, the arms-raised pose, his tail fur. `test_frames.py` reads frames of several
    pieces whole now (`whole`), since his have strips.
  - Daima's Super Saiyan 4 (plum, his choice of the two) is kept in `ssj4_preview` (`v4.frame(..., 'daima_pic')`, with its boots)
    for a post-game unlock later; it is in no build.
- Nov 11, the idles (the owner, 19:17, of Super Saiyan 4 Goku: "Stop with this head bob on the idle stuff how are we doing this
  again"). The game's own figures breathe: their two idle frames differ by 3 to 15 pixels of the chest. Seven more figures moved
  their head or changed pose (GT Trunks and his Super Saiyan, Majuub, Gohan in armor's Super Saiyan 2: the head a pixel to one side;
  GT Vegeta's Super Saiyan 4 from the side; DBS Gogeta and his Super Saiyan: a second frame with his eyes closed, and a walk frame
  from behind). A rule so it cannot come back with the next figure: `build.py idle_still` makes any playable form's new actor whose
  two idle frames differ by more than 20 pixels in a view show its first frame for both (a pointer, nothing redrawn), and
  `test_frames.py` check 16 fails a ROM where any form's do. The owner was shown all seven now and still (`idle_now_and_still.gif`,
  20:50) with the plan; `vegeta_gt_ssj4` and `vegeta_gt_tank_ssj4` were relocked for it.
- Nov 11, 21:38, the owner, shown Super Saiyan 4 Gogeta again: "Some weird clipping with Ssj4 Gogeta head and neck on side and back
  views especially on walk frames mainly". Read frame by frame against BF Goku's frame under each (`gogeta_preview/three.py`, one canvas
  for BF Goku, Super Saiyan 4 Goku and Gogeta). His frames in the ROM are the owner's sheet pixel for pixel, so it is the sheet's art; its
  standing, walking and running frames (slots 0-2) were made by another road than its fighting frames. Found:
  - from the side his head has two see-through pixels over his eye, in every side frame of every slot;
  - his orange shoulder pads come and go between frames: BF's sleeve was painted vest grey, black or the sash's blue, so a pad is whole in
    one frame, half in the next, gone in the third, with blue on his shoulder (walk and run, all three views; from the front the run's
    pads are grey);
  - arms left bare (often one column of BF's skin down the outside of a fur arm) and fists turned to fur instead, some with a blue ankle
    band across them; his standing side frame's fist is fur too.
  `gogeta_preview/fixes.py` holds the fixes as text patches per frame (28 frames of slots 0-2; pads on BF's sleeves in the pad's
  own two oranges, fur on the whole arm, the dark wristband, skin on the fist only; nothing outside a frame's outline, no colour he didn't
  have), `fixed.py` applies them and fills the see-through spot wherever his side head is, `preview.py` makes the now-and-fixed stills
  and GIFs. **A preview only: he is locked, nothing is in the build until the owner approves** (then `BFU_RELOCK=gogeta_ssj4`). Still to
  read the same way: his fighting frames (slots 3 and up; a first screening flags fists in fur and half-turned arms there too).
  22:25, the owner, of that first preview: "The back ones still doing it it's by a pixel or two moving slightly to the side". Measured
  (his head against his standing head, frame by frame): from behind his head sits one column left in the first walk frame and nowhere
  else (BF Goku's own head does it there, and Super Saiyan 4 Goku's with it), and the first fix laid the pads on BF's shoulders, which
  shift a pixel or two under the head as the arms swing (and BF's run sways the whole body a pixel left, then right). From behind his head
  and his two rows of shoulder pads are now one piece, his standing frame's exactly, in all eight walk and run frames (`('stand', rows
  down, last row)` in `fixes.py`; one row lower on the two contact frames, BF's own bob); the run's sideways sway is taken out below it
  (`('shift', row, columns)`), so only his arms and legs move under his shoulders. A fist that BF shows poking out beside the shoulder
  on the far arm is hidden behind the pad. From the side and the front his head keeps one column through the walk and the run already.
  22:35, the owner, of the second preview: "Okay good lock it for now". In the build: `build.py gogeta_fix`, after Super Saiyan 4
  Goku's touch-up (which reads Gogeta's hair), puts every frame of his figure through `sprites.composed_actor` with the table
  `gogeta_preview/gogeta_table.py` makes from the ROM so far: each picture -> `fixed.fixed` cut back to its box (nothing grows). A
  picture his figure uses more than once (slot 11 and 19 reuse his stance; slot 17 shows one lying frame from the front and the side)
  is one picture, fixed the same everywhere; the build stops if two listed places of one picture disagree. The see-through spot is filled
  wherever his side head is (45 pictures beyond slots 0-2, each checked to be the spot over his eye), 71 pictures in all. Relocked
  (`BFU_RELOCK=gogeta_ssj4`). `test_ssj4.py` holds the ROM to it: from behind his head and pads are one piece in all eight walk and run
  frames, no see-through spot in any frame, the arms fur and fists skin where the fixes put them, his pads in every walk frame from the
  front and the side and in the run from the front (running, the forward arm crosses a shoulder, and from the side in the first run
  frame it is the shoulder itself: BF draws none there); each of these fails on the build before. `figure_diff.py` between the two
  builds: actor 357 (Gogeta) and nothing else; every one of his 294 frames is the approved fix (26 places reuse his standing picture in
  slots 11, 12 and 19 and take its fix). To preview `fixes.py` again, use a ROM from before the fixes (`BFU_GOG_ROM`).
  `figure_diff.py` now lays every frame out whole (it stopped on Super Saiyan 4 Goku's grown frames, whose box is larger than their
  first piece).
  The same reading showed leftovers of the same kind in the locked Super Saiyan 4 Goku's walk and run (from the side, walk frames 2 and
  4: BF's sleeve left as a blue band on his shoulder over a bare upper arm; the run from behind and from the front: part of an arm bare).
  Not touched (the owner, 18:13: "Don't make changes to SSJ4 Goku without verifying first"): to be shown to him as its own preview.
  Nov 12, 00:06, the owner: "Send it what are you waiting for". `ssj4_preview/walkfix.py` reads his walk and run frames the same way
  (against BF Goku's under them) and lists the fixes: BF's sleeve left blue on his shoulder and the arm under it bare, where his standing
  frames have fur (from the side in every walk frame and in the run's arm that swings back; from the front and from behind in the walk
  and the run), and from behind his head one column left in the first walk frame (rows 0-57 moved back in line: his head now keeps
  one column through the walk and the run from behind, as it does from the front; from the side every walk and run frame keeps one
  column too, one left of his standing frame, as BF Goku's do). New fur takes his standing frame's shade at that pixel. Fur from the
  shoulder to the wristband, the wristband blue, the hand skin. `walkpreview.py` makes the now-and-fixed stills and GIFs. A preview
  only: nothing in the build until the owner approves (then `BFU_RELOCK=kid_goku_ssj4`).
  00:24, the owner: "Back view is fucked run frames are fucked". From behind the sheet's tail hangs to the floor in every frame, four
  pixels wide, over his left leg (and in the run past it, in the air): it reads as a red leg and his left boot is gone; and the sheet
  left skin and blue on his trousers there. `walkfix.tail` (frames that show his back only: no face in the head rows): the tail off, BF
  Goku's leg under it back in his own leg colours, his tail Super Saiyan 4 Vegeta's from behind (the owner's approved figure: a curl out
  to the side at his waist). From the side the sheet's tail sticks straight out of his upper back at chest height; as an option, a tail
  from his waist taken from Gogeta's (both drawn on the same BF frames) in his reds.
  00:49, the owner: "You made the tail worse and also I meant his back itself but now both are broken wtf". The tail change is out of
  the preview (the sheet's tail stays). Nothing of this was ever in the build. Asked the owner what is broken on his back, with a
  picture of his back as it is in the game.
  His answer: "Back shape warped and morphed with tail", from behind; where the tail sits: no preference. From behind the sheet's tail
  grows out of his crotch four pixels wide down his left leg to the floor, so his lower body and the tail are one warped shape.
  `walkfix.tail` now: the tail off, his legs whole (BF's legs in his own leg colours), stray skin and blue off his trousers, and a tail
  of his reds hanging from the base of his spine (under the middle of his sash) straight down between his legs to his knees; the first
  walk frame from behind moved whole one column (not his head alone, which bent his back at the seam).
  01:43, the owner: "His back is still totally fucked", "It was fine before wtf did you even do to it", "It should just have his back
  not a tail on top of his back and then another tail at the bottom". So: every walk and run change above is dropped (`walkfix.py`,
  `walkpreview.py` removed; the game never had any of them). What he means: from behind the sheet drew a tail lying over his back (a red
  band shaded like a tail, dark-light-light-mid-dark, from his waist up across his back and over his sash) as well as the tail hanging
  at the bottom. `ssj4_preview/plainback.py`: his back plain, nothing else: where BF Goku has his gi's back above the belt, his fur in
  BF's own shading (dark orange 79 -> 31, 63/64 -> 32, light 65 -> 104), where BF has his belt, the sash's blue across; his hair, arms,
  legs and the tail at the bottom as they are; frames that show his back only (27 of his 61 pictures from behind). A preview.
  06:33, the owner: "Now you fucked the arms up again and there's a transparent pixel on his back at the bottom of his hair in back
  view". The belt rule had taken BF's wristbands for belt where they touch it (walk 1, run 1) and turned his left wristband and arm to
  sash blue. Now the belt is cut to his waist (the columns of BF's gi in the row above it) and only the sheet's fur is repainted; checked
  over every frame: 0 pixels changed on his arms, hands, wristbands or sleeves. The see-through pixel: the sheet's, at the bottom of his
  hair, and not only there: 61 of his 171 pictures (all views) have one boxed in by his hair or outline (Gogeta's sheet has 40). Filled
  with black like the outline round them (`see_through`, `fill`). A preview.
  07:01, the owner: "I meant the fur on his arms ... which no you DID NOT FIX STILL", "Why ... are you working backwards and fucking
  shit up we've already fixed multiple times now". My misreading: at 01:43 ("It was fine before") I dropped the arm fixes with the
  head move and the tail; he had meant the back only. The arm fixes are back (`ssj4_preview/armfur.py`, the 00:06 list without the head
  move): fur from the shoulder to the wristband in every walk and run frame, all three views, under the plain back and the filled
  see-through pixels. Next: the same reading of his arms in every other move.
  07:14, the owner: "Fix the messed up pixel on his right arm in back view". From behind his right arm had two kinds: a see-through
  pixel between his sash and his right wristband (standing, walk 1, 2 and 4, run 2 and 4; his left side has fur there), now his dark
  fur; and a brown dot in its fur (walk 3, run 2-4): BF Goku's darker skin shades 205 and 206, which the sheet left and the arm fixes
  did not map. `armfur.py` maps them to fur too (op 'gap' for the see-through pixel), which also takes four such dots out of the arms
  in the walk and run from the side (inside the same arm boxes; no hand pixel changed). A preview.
  Then his arms in every other move (`armfur.MOVES`, preview `ssj4_preview/armmoves.py`): every picture of slots 0 and 3-21 in all
  three views read pixel by pixel (text grids of his frame beside BF Goku's, then each doubtful one at 14x): BF's wristband
  separates hand from arm, BF's undershirt sleeve marks the shoulder, and where the sheet drew its own pose its own bands do. 44
  pictures change, 340 pixels: bare forearms and upper arms to fur by shade (ki blast and combo wind-ups, the raised back forearm
  in combo 1, combo 2 and the finisher, the hit frames' upper arms, the guard's elbows from behind, charging, jumping, flying,
  spin, getting up, powering up), BF's sleeve blue at the shoulder to fur, two skin pixels in his run sash to blue, one fur pixel
  in his right hand back to skin (finisher frame 4), the white motion streak back across his punching arm in combo 2 (it was
  see-through), and two see-through pixels in the flying frame filled. Left as the sheet has them where arm and hand could not be
  told apart: a few hit, special and charging frames (9,1,2; 21,8-9; 8,3/6/9) and the skin beside his hands in 3,0,1.
  07:49, the owner, on that preview: "Fix the fucking fur on the arms in every single frame holy fuck". No frame left out now
  (`armfur.MORE`): the forearm between the two wristbands in hit 2 from the side, the skin beside his hands in ki blast 1 from
  behind, the bare stripe on his left arm getting up, five lone skin pixels on shoulders, and every patch of blue left on his
  arms from BF's undershirt sleeve or its outline (blue touching his fur and no hand, off his sash and boots; 27 pictures): only
  his wristbands stay blue. In all, 64 pictures and 414 pixels change, and a check confirms each change is skin or sleeve blue to
  fur, a see-through pixel filled, the sash pixels, or the one fur pixel in a hand to skin. `plainback.fixed` reads BF's nearest
  frame where BF has fewer frames in a slot. Preview `ssj4_preview/everyframe.py`: every one of his 142 pictures (slots 0-21),
  and this round's before and after. His charged punch (slots 22-23) is still BF Goku's own frames, the job after this.
  07:59, the owner, on that sheet: "Special 11 and 12 have the wrong hair and the arms are still fucked, spin 2 and spin 3 dont show
  the front of his head properly, spin 1 side either, spind 3 front legs missing, hit 2 is base goku still". `ssj4_preview/heads.py`
  (run last in `plainback.fixed`; `fixed_body` is everything before it): the spin from the side is BF's front frame mirrored and
  moved 16 pixels, every pixel the same, so his face shows; the sheet had put a back of the head there: now his own fixed front
  frame mirrored and moved the same. Spin 3 from the front: holes in his legs where BF has their outline and trousers, filled as
  the sheet colours those legs in spins 1 and 2 (a few holes in spins 1 and 2 too). Hit 2 from the side: the sheet left BF's hair
  shape and painted his face in fur; now Super Saiyan 4 Gogeta's sheet's head for that frame, hair in Goku's black and grey
  (v2.G_MAP), eye gold. The special's last frame (21,10, all views): the sheet left BF's hair and bare crossed arms; now its frame
  before (21,9), drawn in full by the sheet, held. Preview `everyframe.py` -> ssj4_goku_heads_and_legs.png. "Special 11 and 12"
  read as the sheet's two pictures of frame 11 (front; back and side are one picture).
  08:10, the owner: "shoes shouldnt be red" (and the 07:59 list again; he was likely reading the sheet's top row, the preview before
  this round). The spin's legs from the front are now his own boots' and trousers' colours (`heads.LEG_MAP`: BF's boot blues his black
  and dark grey, BF's sole browns his light greys, BF's trousers his yellows), every leg pixel, not only the holes.
  `ssj4_goku_FIXED_spin_hit_special_flying.png` shows only the fixed pictures (the flying frames from behind were always there).
  08:11, the owner: "dont even touch the others just send previews of every SSJ4 form". `ssj4_preview/allforms.py` draws every frame
  of every move in all three views, none left out and none merged (the earlier sheets showed each distinct picture once, which hid
  repeated frames such as the flying ones from behind): a PDF page per move and a GIF of every move, for Super Saiyan 4 Goku (the
  preview), Daima (the saved preview), Gogeta and GT Vegeta (as the game has them; the tank-top look's Super Saiyan 4 is the same
  figure, actor 371). Nothing on Daima, Gogeta or Vegeta changed. Daima was saved on Nov 11 before today's rounds, so he still has
  what they fixed on Goku: the spin from the side shows the back of his head, hit 2 from the side has BF's hair shape, the special's
  last frame BF's hair and pose, and the arm fur rounds (`armfur.MOVES`, `MORE`).
  08:47, the owner: "Apply the back shape removal and the arm fur fixes to daima goku ONLY everyone else is good".
  `ssj4_preview/daimafix.py`: Daima is the same sheet as Super Saiyan 4 Goku recoloured place for place (`v4.frame` 'mix' and
  'daima_pic' recolour one shaped frame), so Goku's arm fixes (`armfur.FIXES`) and plain back (`plainback.plain_back`, from behind,
  with its see-through pixel at the bottom of the hair) carry over by place, in Daima's colours (fur 127/39/40, the sash across his
  back in his sash's colours, skin and wristbands as they are). Also the few arm pixels where the build's Goku (each picture touched
  up at its first place) differs from v4's frame for that place, so the two match class for class. Not carried: heads.py (spin
  sides, hit 2, the special's last frame), the see-through fill in the other views, slot 11's frames 5-8 (a head a pixel over).
  165 of his 327 frames change, 1,723 pixels; checked: in every frame Daima has skin, fur and wristband where Goku's fixed frame
  has them, and no hair pixel changed. Previews: `daimafix.py` -> `ssj4_daima_arms_back_before_fixed.pdf`, `allforms.py daima`
  (now the fixed one; `daima_saved` for the Nov 11 one). In no build.
  09:00, the owner: "Ok preview the other fixes too". `daimafix.fixed`: also the see-through pixels in every view (found on his GT
  frame, filled as the nearest black there: plum in his hair, as his own head has no black) and heads.py in his colours: the spin's
  legs from the front in his boots' blues and trousers' oranges (`LEG_MAP`, read off his standing and walking feet against BF's), the
  spin from the side his fixed front mirrored and moved 16 pixels, hit 2 from the side Gogeta's head with every dark plum (as his own
  head) and the eye his hair's colour, the special's last frame its frame before held. Checked: in every frame but costume out 5-8
  his shape is Goku's preview's exactly (so no see-through pixel Goku hasn't) and his skin and fur are where Goku's are; the spin
  sides are his fronts mirrored. Preview `ssj4_daima_heads_legs_holes_before_fixed.pdf` (57 pictures). In no build.
  09:28, the owner: "fix the tail on some of those back combo frames where it looks disconnected then it'll be good". From behind his
  tail hangs from his crotch to the floor in front of his legs (the sheet's, as on Goku); `v4.boots` had painted BF Goku's boots over
  it, so in combo 2's first frame only its tip was left at the floor and in combo 1's first a gap cut it in two (fewer pixels in the
  walk, run, ki blast, hit, victory, jump and flying from behind). `daimafix.tail`: below his belt (row 62 where BF's arms hide the
  belt), Goku's fur over Daima's boot is his fur again, 87 pixels in 29 frames. In the finisher's first frame (his right leg kicked out
  sideways) the tail's top hangs in the air two rows under his hip, Goku's too: two pixels join it (`BRIDGE`). Preview
  `ssj4_daima_tail_before_fixed.pdf` (his hips to his feet, the combos first). In no build.
- Nov 11, 21:13-22:10, the full suite on 978966a: 36 of its 37 tests with no failure (1,303 checks passed). `test_moves.py` failed one check, "the Super Dragon
  Fist hits in Super Saiyan 4", and it was the check: the Bomber it hits is given 9,000 health and the move takes 10,690, so he died and
  the test read whatever took his place in memory (a huge negative number; an older build happened to leave 0 there, which passed). The
  move takes the same 10,689.7 on the Nov 11 12:37 build and on this one, measured with 30,000. The check now gives him 30,000
  (`fire(..., health=)`) and passes.
- Nov 11, noted for after this (the owner, 19:26 and 19:49): Super Saiyan God Goku's eyes match his red hair; Super Saiyan Blue Goku,
  Vegeta and Gogeta: eyebrows and pupils match their hair, a light cyan glowing aura and Super Saiyan 2's bolts toned down in Blue's
  colour; and, after everything, test all postgame content: every enemy must fight and be a challenge, never wait to be hit.

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
`BFU_RIG_ENEMY="61 <character>"`: he walks, punches, fires Kid Buu's beam and is knocked down). (His beam is his own since Nov 11: Wrath of the Gods, `lib/wrath.py`; see "Nov 11, 18:55".)

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
