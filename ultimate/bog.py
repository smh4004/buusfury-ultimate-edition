"""Battle of Gods (Nov 9). The owner: "build the entire movie Battle of Gods and super saiyan god ritual into the post game and once
completed grant access to SSG", Super Saiyan God "upon mastery of the super saiyan skill"; then "don't have BoG take place in zone 26 use
the accurate locations from the movie if you can". Every scene is in the game's own areas, the movie's places where Buu's Fury has them:

After the ending, once Goku's Super Saiyan is mastered and he's the one playing, Whis waits at Capsule Corporation (`more_get(Q_READY)`).
  1. King Kai's planet. Buu's Fury has no North Kai's planet (Cell destroyed it; King Kai lives on Grand Kai's Planet then), so it is
     Grand Kai's Planet (1-0B). King Kai warns Goku, Beerus asks about a Super Saiyan God, and they fight. Beerus can't be beaten there
     (`ROWS[0]`): Goku goes down, and the game's death script carries on instead of the game over.
  2. Bulma's birthday party at Capsule Corporation (4-14), as in the movie: the pudding, Bulma's slap, Vegeta's fury. Vegeta (or whoever
     the player picks) fights Beerus on the party grounds (outfit.c turns fighting on there while the fight lasts: the area has none).
  3. The ritual, at the party: Shenron tells of five righteous Saiyans pouring their power into a sixth; Videl's baby makes the sixth.
     Goku becomes a Super Saiyan God: the skill is his from here (outfit.c skills_sync, with Super Saiyan mastered).
  4. Goku against Beerus, along the movie's path: West City (4-01), a forest (Fukurou Forest, 13-01), the desert's rock formations
     (Diablo Desert, 11-01). (The cavern and the sky over the clouds have no area in Buu's Fury.) Each leg is one of Beerus's rows; winning
     one carries the fight on to the next place without a rest. Win the last, and Whis brings everyone home to Capsule Corporation, where
     Beerus spares the Earth. Lose any leg, and it's back to the party to try that leg again.
Every scene is a step of one event list: the West City resident's (build.py quest_npc), whose first step sends talks at Capsule
Corporation and on Grand Kai's Planet here; the story's progress is more flags 49-57. Who stands where is the actors' spawn conditions
(zone26.apply): the quest's people appear at each stage, Beerus as an enemy while a fight is on (MORE_BOG_FIGHT), and the people and
enemies who live in West City and the desert stand aside meanwhile.
Beerus is lib/beerus.py's (Kid Buu's frames, on Kid Buu's beam-firing enemy row 61); Whis is lib/whis.py's (Kibito's)."""

MORE_BOG_START, MORE_BOG_LOST, MORE_BOG_PARTY, MORE_BOG_RITUAL, MORE_BOG_DONE, MORE_BOG_FIGHT, MORE_BOG_TOLD = 49, 50, 51, 52, 53, 54, 55
# (more flags 47-48 are New Game+'s round count, outfit.c NG_FLAG: the quest had them as started and lost, so starting it made enemies hit harder)
MORE_BOG_GOD2, MORE_BOG_GOD3 = 56, 57            # the god fight has reached the forest / the desert (58-63 are free)
Q_AREA, Q_GOKU, Q_READY = 251, 252, 253          # more_get queries (outfit.c): this area (area << 8 | world), Goku playing, the quest can start
KID_BUU_ROW = 61
CAPSULE = (4, 0x14)                              # Capsule Corporation
KAI = (1, 0x0B)                                  # Grand Kai's Planet, standing in for King Kai's
WEST_CITY, FOREST, DESERT = (4, 0x01), (13, 0x01), (11, 0x01)
WHIS_AT = (192, 152)                             # where Whis waits there (beside Mrs. Brief's spot at 128, 136)
HOME = (4, 0x14, 1, 192, 192)                    # warp: world, area, entrance, x, y (just below Whis)
PARTY_AT = (4, 0x14, 1, 200, 280)                # the party: you land among the guests
KAI_AT = (1, 0x0B, 1, 200, 216)

# Who stands where (character keys: an int, or an actor name from build.py's actors), and when: `when` is (more flags set, more flags clear).
PARTY = (('bulma', 136, 232), ('vegeta', 168, 232), ('whis', 232, 232), ('beerus', 264, 232), ('gohan', 104, 264), ('videl', 136, 264),
         ('goten', 264, 272), ('trunks', 296, 272))           # all on the screen you land on (it shows the map from about 80, 200)
PEOPLE = ((KAI, (('king_kai', 200, 176), ('beerus', 152, 176), ('whis', 120, 176)), ((MORE_BOG_START,), (MORE_BOG_LOST, MORE_BOG_FIGHT))),
          (CAPSULE, PARTY, ((MORE_BOG_LOST,), (MORE_BOG_TOLD, MORE_BOG_FIGHT))))
# Beerus's fights: (where, x, y, when), one per row of ROWS; `arrive` is where Goku lands for it.
FOES = ((KAI, 152, 176, ((MORE_BOG_START, MORE_BOG_FIGHT), (MORE_BOG_LOST,))),
        (CAPSULE, 168, 232, ((MORE_BOG_LOST, MORE_BOG_FIGHT), (MORE_BOG_PARTY,))),
        (WEST_CITY, 240, 336, ((MORE_BOG_RITUAL, MORE_BOG_FIGHT), (MORE_BOG_GOD2, MORE_BOG_DONE))),
        (FOREST, 144, 168, ((MORE_BOG_GOD2, MORE_BOG_FIGHT), (MORE_BOG_GOD3, MORE_BOG_DONE))),
        (DESERT, 96, 208, ((MORE_BOG_GOD3, MORE_BOG_FIGHT), (MORE_BOG_DONE,))))
# Each fight stands clear of the area's doors, save capsule and gates (area record +0x10): A beside the desert's gate said "Goku cannot open
# this gate!" instead of punching, and West City's first spot was in a building's door (test_bog.py checks the distance).
ARRIVE = (KAI_AT, PARTY_AT, (4, 0x01, 1, 240, 392), (13, 0x01, 1, 144, 224), (11, 0x01, 1, 96, 264))
ASIDE = (WEST_CITY, DESERT)                      # areas whose own people and enemies stand aside while a Beerus fight is on
CHARS = {'king_kai': 161, 'bulma': 41, 'vegeta': 279, 'gohan': 123, 'videl': 287, 'goten': 166, 'trunks': 269}
# Beerus's rows (copies of Kid Buu's): HP and (level + 50, Strength, Power, Endurance). On King Kai's planet he can't really be beaten
# (250000 HP and hits that floor Goku; 2,000,000 broke Kid Buu's behaviour: likely an overflow in its health checks, it stopped attacking and crashed).
# The god fight is three legs, 125000 in all (it was one 120000 fight), a little stronger each time. His Strength sets his big hits: the
# post-game boss rules (outfit.c combat_hook) make those grow with the player's health, and at 115-120 three of them floored a Goku of
# 7563 HP and 180 in every stat (2400-2600 each, Nov 9). At 85/90/95 they take 880/1040/1220 (12/14/16%), against Super 13's 7%:
# the hardest fights in the game, still won by blocking and dodging. (Power, 125-130, only sets a light 1-2 HP a frame beside him.)
ROWS = ((250000, (160, 140, 140, 200)), (20000, (152, 85, 85, 80)),
        (35000, (160, 85, 125, 110)), (40000, (161, 90, 128, 112)), (50000, (162, 95, 130, 115)))
GOD_LEGS = (2, 3, 4)


def put(more_put, f, v): return '    pushn %d, %d\n    call 0x%X\n' % (f, v, more_put)
def get(more_get, f): return '    pushn %d\n    call 0x%X\n' % (f, more_get)


def when(more_get, on, off, extra=''):
    """A spawn condition: every flag in `on` set and every one in `off` clear (and `extra`'s value, if any, true)."""
    t = ''.join(get(more_get, f) + ('    and\n' if k else '') for k, f in enumerate(on))
    t += ''.join(get(more_get, f) + '    push 0\n    eq\n' + ('    and\n' if on or k else '') for k, f in enumerate(off))
    return t + (extra + '    and\n' if extra else '') + '    end\n'


def warp(to, fade=30):
    return '    call 0x78(%d)\n    pushn %d, %d, %d, %d, %d\n    call 0x77\n    call 0x79(30)\n' % ((fade,) + tuple(to))


def god_warp(more_get):
    """To the leg of the god fight it has reached (labels W1/W2/W9)."""
    return (get(more_get, MORE_BOG_GOD3) + '    jz W1\n' + warp(ARRIVE[4]) + '    jmp W9\nW1:\n' + get(more_get, MORE_BOG_GOD2) + '    jz W2\n'
            + warp(ARRIVE[3]) + '    jmp W9\nW2:\n' + warp(ARRIVE[2]) + 'W9:\n')


def after_fight(k, more_put, lost):
    """Where each Beerus fight goes, won (his death script) or lost (the game's death script). Lost, Goku is revived the way the game's own
    death script does it for a lost Time Chamber fight (build.py death_script), and the story goes on (King Kai's planet, the party) or
    back to the party (the god fight). Won: the party's fight leads to the ritual; a leg of the god fight carries on to the next place at
    once, as the movie's fight moves on; the last brings everyone home."""
    if lost:
        flags = put(more_put, MORE_BOG_FIGHT, 0) + (put(more_put, MORE_BOG_LOST, 1) if k == 0 else put(more_put, MORE_BOG_PARTY, 1) if k == 1 else '')
        return flags + '    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n' + warp(PARTY_AT)
    rest = '    call max_hp\n    set hp\n    call max_ki\n    set ki\n'
    if k == 0: return put(more_put, MORE_BOG_FIGHT, 0) + put(more_put, MORE_BOG_LOST, 1) + rest + warp(PARTY_AT)
    if k == 1: return put(more_put, MORE_BOG_FIGHT, 0) + put(more_put, MORE_BOG_PARTY, 1) + rest + warp(PARTY_AT)
    if k == 2: return put(more_put, MORE_BOG_GOD2, 1) + warp(ARRIVE[3], 20)
    if k == 3: return put(more_put, MORE_BOG_GOD3, 1) + warp(ARRIVE[4], 20)
    return put(more_put, MORE_BOG_FIGHT, 0) + put(more_put, MORE_BOG_DONE, 1) + rest + warp(HOME, 60)


def death_branch(more_put, more_get):
    """The game's death script: in a Beerus fight, the story goes on (build.py death_script puts this first). `push 4` ends its list."""
    out = get(more_get, MORE_BOG_FIGHT) + '    jz B9\n'
    out += get(more_get, MORE_BOG_LOST) + '    jz B1\n' + get(more_get, MORE_BOG_PARTY) + '    jz B2\n'
    out += after_fight(2, more_put, True) + '    push 4\n    end\n'
    out += 'B1:\n' + after_fight(0, more_put, True) + '    push 4\n    end\n'
    out += 'B2:\n' + after_fight(1, more_put, True) + '    push 4\n    end\nB9:\n'
    return out


def lines():
    """Every line the quest says, to check lengths (build.py's NPC scripts refuse 100+ and 64-67 characters)."""
    return [t for _, t in SCENES_TEXT]


BEERUS, WHIS, NARR, GOKU, KING_KAI, BULMA, VEGETA, GOHAN, VIDEL, SHENRON = 'BEERUS', 'WHIS', 0x00, 0x02, 0x57, 0x11, 0x93, 0x26, 0x99, 0x74
SCENES_TEXT = []
# The quest's lines live in a dialogue bank of their own (tools/assets/assets.py). The game unpacks a line's whole bank
# to show it, so its 2,446 characters in bank 6 (7,613 without them) would make every bank-6 line slower to appear.
TEXT_BANK = 7


def steps(more_get, more_put):
    """(name, step text) for the host list; {name} becomes that step's number. Starts with 'bog' (step 1's branch jumps there for a talk
    at Capsule Corporation or on Grand Kai's Planet)."""
    out = []
    def say(name, who, text):
        if isinstance(who, str): who, text = 0x00, '%s: %s' % (who, text)
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, (n, text)
        SCENES_TEXT.append((name, text))
        out.append((name, 'say 0x%02X @%d "%s"\n' % (who, TEXT_BANK, text)))
    def code(name, text): out.append((name, 'code\n' + text))
    def area_is(world_area): return get(more_get, Q_AREA) + '    pushn %d\n    eq\n' % (world_area[1] << 8 | world_area[0])
    g = lambda f: get(more_get, f)
    fight = lambda: put(more_put, MORE_BOG_FIGHT, 1)
    # who you're talking to is told by where you are and how far the story has got
    code('bog', area_is(KAI) + '    jz Q1\n' + g(MORE_BOG_LOST) + '    jz Q0\n    push {END}\n    end\nQ0:\n    push {kai}\n    end\n'
         + 'Q1:\n' + g(MORE_BOG_DONE) + '    jz Q2\n' + g(MORE_BOG_TOLD) + '    jz Q3\n    push {after}\n    end\nQ3:\n    push {told}\n    end\n'
         + 'Q2:\n' + g(MORE_BOG_LOST) + '    jz Q4\n' + g(MORE_BOG_PARTY) + '    jz Q5\n' + g(MORE_BOG_RITUAL) + '    jz Q6\n    push {again}\n    end\n'
         + 'Q6:\n    push {ritual}\n    end\nQ5:\n    push {party}\n    end\n'
         + 'Q4:\n' + g(MORE_BOG_START) + '    jz Q7\n    push {resume}\n    end\n'
         + 'Q7:\n' + g(Q_READY) + '    jz Q8\n    push {call}\n    end\nQ8:\n    push {idle}\n    end\n')
    # Capsule Corporation: the movie's opening, King Kai's call, and Whis
    say('call', NARR, "Far across the universe, Beerus, the God of Destruction, woke from a 39-year sleep.")
    say('call1', NARR, "The Oracle Fish foretold a rival for him: a Super Saiyan God. He went looking.")
    say('call1b', KING_KAI, "Goku! Goku, can you hear me? It's King Kai! The God of Destruction is awake!")
    say('call2', KING_KAI, "Lord Beerus is on my planet, asking about a Super Saiyan God! Stay away, Goku!")
    say('call3', GOKU, "A god? He must be crazy strong! I've gotta meet him!")
    say('call4', WHIS, "Oh my, how eager. I'm Whis, Lord Beerus's attendant. Shall I take you to him?")
    say('call5', NARR, "- Let's go!\\n- Not yet")
    code('call_go', '    call 0x18\n    push 0\n    eq\n    jz C1\n' + put(more_put, MORE_BOG_START, 1) + warp(KAI_AT) + '    push {END}\n    end\nC1:\n    push {END}\n    end\n')
    say('idle', WHIS, "What lovely weather on this planet. Don't mind me, I'm only sightseeing.")
    code('idle_end', '    push {END}\n    end\n')
    say('resume', WHIS, "Shall I take you back to Lord Beerus?")
    say('resume2', NARR, "- Let's go!\\n- Not yet")
    code('resume_go', '    call 0x18\n    push 0\n    eq\n    jz R9\n' + warp(KAI_AT) + '    push {END}\n    end\nR9:\n    push {END}\n    end\n')
    # 1. King Kai's planet (Grand Kai's)
    say('kai', KING_KAI, "Goku, you fool! Show some respect! This is Lord Beerus, the God of Destruction!")
    say('kai2', BEERUS, "So you're the Saiyan who beat Majin Buu. Ever heard of a Super Saiyan God?")
    say('kai3', GOKU, "A Super Saiyan God? Nope! But how about a fight, Lord Beerus?")
    say('kai4', BEERUS, "Heh. Fine. Show me the strongest form you've got.")
    say('kai5', WHIS, "Do try not to break the planet, Lord Beerus. Grand Kai is rather fond of it.")
    code('kai_go', fight() + warp(KAI_AT) + '    push {END}\n    end\n')
    # 2. Bulma's party, at Capsule Corporation
    say('party', NARR, "Goku went Super Saiyan 3. Two taps were all it took. Beerus went on to Earth...")
    say('party2', BULMA, "Welcome to my birthday party, everybody! Wait... who are you two, now?")
    say('party2b', VEGETA, "(Lord Beerus... I saw him put his foot on my father's head. Keep him happy!)")
    say('party2c', VEGETA, "Ahem. Bingo! Bingo! Lord Beerus, more food? Anything you like!")
    say('party3', WHIS, "Oh my! This pudding is divine! Lord Beerus, you simply must try it!")
    say('party4', 'MAJIN BUU', "Pudding? Mine! Buu won't share. Go away, kitty!")
    say('party5', BEERUS, "No pudding? Then I'll destroy this planet!")
    say('party5b', NARR, "Beerus took on Gotenks, Piccolo, Gohan, Android 18 and Tien, and floored each in a blink.")
    say('party6', BULMA, "Nobody threatens the Earth at my party! Take that!")
    say('party6b', NARR, "Bulma slapped Beerus... and Beerus slapped her right back.")
    say('party7', VEGETA, "You... hit... MY BULMA!!! Kakarot, stay out of this! He's mine!")
    say('party8', NARR, "Fight Beerus! Vegeta's fury is yours: pick him on the Switch Character menu.")
    code('party_go', '    call 0x8D\n' + fight() + warp(PARTY_AT) + '    push {END}\n    end\n')
    # 3. Shenron and the ritual
    say('ritual', BEERUS, "Not bad, Vegeta. But still no Super Saiyan God? Then the Earth is finished.")
    say('ritual2', NARR, "Bulma gathers the Dragon Balls. The sky goes dark...")
    code('ritual_fx', '    call play_sfx(24)\n    call 0x7A(6)\n    call 0x7B(6)\n    call 0x7A(6)\n    call 0x7B(30)\n    call wait(30)\n    push {ritual3}\n    end\n')
    say('ritual3', SHENRON, "A Super Saiyan God? Five righteous Saiyans must join hands and pour their power into one more.")
    say('ritual4', GOKU, "Vegeta, Gohan, Goten, Trunks... That's only four besides me!")
    say('ritual5', VIDEL, "Um... There is one more. Gohan and I are going to have a baby.")
    say('ritual6', GOHAN, "Videl! Then that's five! Everyone, join hands around Dad!")
    code('ritual_god', '    call play_sfx(24)\n    pushn 5, 255, 64, 64, 10\n    call 0x4C\n    call wait(40)\n    call 0x7A(24)\n    call 0x7B(40)\n'
         + put(more_put, MORE_BOG_RITUAL, 1) + '    push {ritual7}\n    end\n')
    say('ritual7', NARR, "Goku became a Super Saiyan God! Select the skill and press the B Button.")
    say('ritual8', GOKU, "Lord Beerus, this time I'm ready! Let's take this away from the party!")
    say('ritual9', NARR, "Their fight crosses West City, a forest and the desert. Goku must fight it!")
    code('ritual_go', '    call 0x8D\n' + fight() + god_warp(more_get) + '    push {END}\n    end\n')
    say('again', WHIS, "Lord Beerus is waiting. Shall we continue?")
    say('again2', NARR, "- Fight Beerus\\n- Not yet")
    code('again_go', '    call 0x18\n    push 0\n    eq\n    jz A1\n    call 0x8D\n' + fight() + god_warp(more_get) + '    push {END}\n    end\nA1:\n    push {END}\n    end\n')
    # 4. The god fight won: Beerus spares the Earth (told at Capsule Corporation)
    say('told', BEERUS, "Heh... You're the second strongest I've ever fought, Son Goku.")
    say('told2', GOKU, "Second? Who's first?")
    say('told2b', WHIS, "Me, of course. I'm Lord Beerus's teacher. Oh, did he not mention it?")
    say('told2c', GOKU, "The god ki's gone... but I can still feel its power. Whoa, this is great!")
    say('told3', WHIS, "Lord Beerus, you can't destroy a planet with pudding this good. Time to go home.")
    say('told4', BEERUS, "...I'm sleepy. The Earth stays, for now. Save me some pudding.")
    say('told5', NARR, "Goku keeps the power of a Super Saiyan God!")
    say('told6', NARR, "Gogeta's Dragon Ball Super looks are open now! See Switch Character.")     # outfits.json: flag 2000 + MORE_BOG_DONE
    code('told_end', put(more_put, MORE_BOG_TOLD, 1) + '    push {END}\n    end\n')
    say('after', WHIS, "Lord Beerus is napping back home. Oh, is that more pudding? How kind!")
    code('after_end', '    push {END}\n    end\n')
    return out
