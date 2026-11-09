"""Battle of Gods (Nov 9). The owner: "build the entire movie Battle of Gods and super saiyan god ritual into the post game and once
completed grant access to SSG", Super Saiyan God "upon mastery of the super saiyan skill".

After the ending, once Goku's Super Saiyan is mastered and he's the one playing, Whis waits at Capsule Corporation (`more_get(Q_READY)`).
  1. King Kai's planet (a copy of Grand Kai's Planet): King Kai warns Goku, Beerus asks about a Super Saiyan God, and they fight. Beerus
     can't be beaten there (`ROWS[0]`): Goku goes down, and the death script carries on instead of the game over.
  2. Bulma's birthday party (a copy of Capsule Corporation): the pudding, Bulma's slap, Vegeta's fury. Vegeta (or whoever the player picks)
     fights Beerus: landing enough blows, or falling, both carry the story on.
  3. The ritual, at the party: Shenron tells of five righteous Saiyans pouring their power into a sixth; Videl's baby makes the sixth.
     Goku becomes a Super Saiyan God: the skill is his from here (outfit.c skills_sync, with Super Saiyan mastered).
  4. Goku against Beerus on the Lookout (a copy of Kami's Lookout): a real fight. Win, and Whis brings everyone home to Capsule Corporation,
     where Beerus spares the Earth. Lose, and it's back to the party to try again (or home, and Whis takes you back later).
Every scene is a step of one event list: the West City resident's (build.py quest_npc), whose first step asks where you are (`Q_AREA`)
and how far the story has got (more flags 47-53). Beerus, Whis, King Kai and the party guests all point at that list.
Beerus is lib/beerus.py's (Kid Buu's frames, on Kid Buu's beam-firing enemy row 61); Whis is lib/whis.py's (Kibito's)."""

MORE_BOG_START, MORE_BOG_LOST, MORE_BOG_PARTY, MORE_BOG_RITUAL, MORE_BOG_DONE, MORE_BOG_FIGHT, MORE_BOG_TOLD = 47, 48, 49, 50, 51, 52, 53
Q_AREA, Q_GOKU, Q_READY = 251, 252, 253          # more_get queries (outfit.c): this area (room << 8 | world), Goku playing, the quest can start
KID_BUU_ROW = 61
CAPSULE = (4, 0x14)                              # the real Capsule Corporation
WHIS_AT = (192, 152)                             # where Whis waits there (beside Mrs. Brief's spot at 128, 136)
HOME = (4, 0x14, 1, 192, 192)                    # warp: world, area, entrance, x, y (just below Whis)

# The movie's places: zone 26 copies of these areas, each with its people (character keys: an int, or an actor name from build.py's
# actors) and, for a fight, Beerus on his row; `arrive` is where you land. Room numbers follow the challenges' (zone26.bog_first).
PARTY = (('bulma', 136, 232), ('vegeta', 168, 232), ('whis', 232, 232), ('beerus', 264, 232), ('gohan', 104, 264), ('videl', 136, 264),
         ('goten', 264, 272), ('trunks', 296, 272))           # all on the screen you land on (it shows the map from about 80, 200)
ROOMS = (('kai', (1, 0x0B), (('king_kai', 200, 176), ('beerus', 152, 176), ('whis', 120, 176)), None, (200, 216)),
         ('kai_fight', (1, 0x0B), (), (0, 152, 176), (200, 216)),
         ('party', CAPSULE, PARTY, None, (200, 280)),
         ('party_fight', CAPSULE, (), (1, 168, 232), (200, 280)),
         ('ritual', CAPSULE, PARTY, None, (200, 280)),
         ('god_fight', (6, 0x01), (), (2, 312, 328), (288, 440)))
CHARS = {'king_kai': 161, 'bulma': 41, 'vegeta': 279, 'gohan': 123, 'videl': 287, 'goten': 166, 'trunks': 269}
# Beerus's rows (copies of Kid Buu's): HP and (level + 50, Strength, Power, Endurance). On King Kai's planet he can't really be beaten
# (250000 HP and hits that floor Goku; 2,000,000 broke Kid Buu's behaviour: likely an overflow in its health checks, it stopped attacking and crashed).
ROWS = ((250000, (160, 140, 140, 200)), (20000, (152, 85, 85, 80)), (120000, (162, 120, 130, 115)))


def room_of(name, first):
    return first + [r[0] for r in ROOMS].index(name)


def warp(name, first):
    r = ROOMS[[x[0] for x in ROOMS].index(name)]
    return '    call 0x78(30)\n    pushn 26, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n' % ((room_of(name, first),) + r[4])


def put(more_put, f, v): return '    pushn %d, %d\n    call 0x%X\n' % (f, v, more_put)
def get(more_get, f): return '    pushn %d\n    call 0x%X\n' % (f, more_get)


def after_fight(k, first, more_put, lost):
    """Where each Beerus fight goes, won (his death script) or lost (the game's death script): rested, on to the next scene. Lost, Goku
    is revived the way the game's own death script does it for a lost Time Chamber fight (build.py death_script)."""
    flags = put(more_put, MORE_BOG_FIGHT, 0)
    if k == 0: flags += put(more_put, MORE_BOG_LOST, 1); to = warp('party', first)        # King Kai's planet: Goku is out cold either way
    elif k == 1: flags += put(more_put, MORE_BOG_PARTY, 1); to = warp('ritual', first)    # Vegeta's fury: the ritual is next
    elif lost: to = warp('ritual', first)                                                 # the god fight lost: back to the party
    else:
        flags += put(more_put, MORE_BOG_DONE, 1)
        to = '    call 0x78(60)\n    pushn %d, %d, %d, %d, %d\n    call 0x77\n    call 0x79(30)\n' % HOME
    if lost:
        return flags + '    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n' + to
    return flags + '    call max_hp\n    set hp\n    call max_ki\n    set ki\n' + to


def death_branch(first, more_put, more_get):
    """The game's death script: in a Beerus fight, the story goes on (build.py death_script puts this first). `push 4` ends its list."""
    out = get(more_get, MORE_BOG_FIGHT) + '    jz B9\n'
    out += get(more_get, MORE_BOG_LOST) + '    jz B1\n' + get(more_get, MORE_BOG_PARTY) + '    jz B2\n'
    out += after_fight(2, first, more_put, True) + '    push 4\n    end\n'
    out += 'B1:\n' + after_fight(0, first, more_put, True) + '    push 4\n    end\n'
    out += 'B2:\n' + after_fight(1, first, more_put, True) + '    push 4\n    end\nB9:\n'
    return out


def lines():
    """Every line the quest says, to check lengths (build.py's NPC scripts refuse 100+ and 64-67 characters)."""
    return [t for _, t in SCENES_TEXT]


BEERUS, WHIS, NARR, GOKU, KING_KAI, BULMA, VEGETA, GOHAN, VIDEL, SHENRON = 'BEERUS', 'WHIS', 0x00, 0x02, 0x57, 0x11, 0x93, 0x26, 0x99, 0x74
SCENES_TEXT = []
# The quest's lines live in a dialogue bank of their own (tools/assets/assets.py). The game unpacks a line's whole bank
# to show it, so its 2,446 characters in bank 6 (7,613 without them) would make every bank-6 line slower to appear.
TEXT_BANK = 7


def steps(more_get, more_put, first):
    """(name, step text) for the host list; {name} becomes that step's number. Starts with 'bog' (step 1's branch jumps there)."""
    out = []
    def say(name, who, text):
        if isinstance(who, str): who, text = 0x00, '%s: %s' % (who, text)
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, (n, text)
        SCENES_TEXT.append((name, text))
        out.append((name, 'say 0x%02X @%d "%s"\n' % (who, TEXT_BANK, text)))
    def code(name, text): out.append((name, 'code\n' + text))
    def area_is(world_area): return get(more_get, Q_AREA) + '    pushn %d\n    eq\n' % (world_area[1] << 8 | world_area[0])
    def room_is(name): return area_is((26, room_of(name, first)))
    g = lambda f: get(more_get, f)
    # where you are and how far the story has got
    code('bog', area_is(CAPSULE) + '    jz Q1\n'
         + g(MORE_BOG_DONE) + '    jz Q2\n' + g(MORE_BOG_TOLD) + '    jz Q3\n    push {after}\n    end\nQ3:\n    push {told}\n    end\n'
         + 'Q2:\n' + g(MORE_BOG_START) + '    jz Q4\n    push {resume}\n    end\n'
         + 'Q4:\n' + g(Q_READY) + '    jz Q5\n    push {call}\n    end\nQ5:\n    push {idle}\n    end\n'
         + 'Q1:\n' + room_is('kai') + '    jz Q6\n    push {kai}\n    end\n'
         + 'Q6:\n' + room_is('party') + '    jz Q7\n    push {party}\n    end\n'
         + 'Q7:\n' + room_is('ritual') + '    jz Q8\n' + g(MORE_BOG_RITUAL) + '    jz Q9\n    push {again}\n    end\nQ9:\n    push {ritual}\n    end\n'
         + 'Q8:\n    push {END}\n    end\n')
    # Capsule Corporation: King Kai's call, and Whis
    say('call', KING_KAI, "Goku! Goku, can you hear me? It's King Kai! The God of Destruction is awake!")
    say('call2', KING_KAI, "Lord Beerus is on my planet, asking about a Super Saiyan God! Stay away, Goku!")
    say('call3', GOKU, "A god? He must be crazy strong! I've gotta meet him!")
    say('call4', WHIS, "Oh my, how eager. I'm Whis, Lord Beerus's attendant. Shall I take you to him?")
    say('call5', NARR, "- Let's go!\\n- Not yet")
    code('call_go', '    call 0x18\n    push 0\n    eq\n    jz C1\n' + put(more_put, MORE_BOG_START, 1) + warp('kai', first) + '    push {END}\n    end\nC1:\n    push {END}\n    end\n')
    say('idle', WHIS, "What lovely weather on this planet. Don't mind me, I'm only sightseeing.")
    code('idle_end', '    push {END}\n    end\n')
    say('resume', WHIS, "Shall I take you back to Lord Beerus?")
    say('resume2', NARR, "- Let's go!\\n- Not yet")
    code('resume_go', '    call 0x18\n    push 0\n    eq\n    jz R9\n' + g(MORE_BOG_LOST) + '    jz R1\n' + g(MORE_BOG_PARTY) + '    jz R2\n'
         + warp('ritual', first) + '    push {END}\n    end\nR1:\n' + warp('kai', first) + '    push {END}\n    end\nR2:\n' + warp('party', first)
         + '    push {END}\n    end\nR9:\n    push {END}\n    end\n')
    # 1. King Kai's planet
    say('kai', KING_KAI, "Goku, you fool! Show some respect! This is Lord Beerus, the God of Destruction!")
    say('kai2', BEERUS, "So you're the Saiyan who beat Majin Buu. Ever heard of a Super Saiyan God?")
    say('kai3', GOKU, "A Super Saiyan God? Nope! But how about a fight, Lord Beerus?")
    say('kai4', BEERUS, "Heh. Fine. Show me the strongest form you've got.")
    say('kai5', WHIS, "Do try not to break the planet, Lord Beerus. King Kai only just got it back.")
    code('kai_go', put(more_put, MORE_BOG_FIGHT, 1) + warp('kai_fight', first) + '    push {END}\n    end\n')
    # 2. Bulma's party
    say('party', NARR, "Two taps were all it took. Goku was out cold, and Beerus went on to Earth...")
    say('party2', BULMA, "Welcome to my birthday party, everybody! Wait... who are you two, now?")
    say('party3', WHIS, "Oh my! This pudding is divine! Lord Beerus, you simply must try it!")
    say('party4', NARR, "But Majin Buu ate the very last pudding. Beerus did not take it well.")
    say('party5', BEERUS, "No pudding? Then I'll destroy this planet!")
    say('party6', BULMA, "Nobody threatens the Earth at my party! Take that!")
    say('party6b', NARR, "Bulma slapped Beerus... and Beerus slapped her right back.")
    say('party7', VEGETA, "You... hit... MY BULMA!!! Kakarot, stay out of this! He's mine!")
    say('party8', NARR, "Fight Beerus! Vegeta's fury is yours: pick him on the Switch Character menu.")
    code('party_go', '    call 0x8D\n' + put(more_put, MORE_BOG_FIGHT, 1) + warp('party_fight', first) + '    push {END}\n    end\n')
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
    say('ritual8', GOKU, "Lord Beerus, this time I'm ready! Let's go somewhere we won't wreck the party!")
    say('ritual9', NARR, "Goku faces Beerus! Make sure Goku is the one fighting.")
    code('ritual_go', '    call 0x8D\n' + put(more_put, MORE_BOG_FIGHT, 1) + warp('god_fight', first) + '    push {END}\n    end\n')
    say('again', WHIS, "Lord Beerus is waiting. Shall we continue?")
    say('again2', NARR, "- Fight Beerus\\n- Go home")
    code('again_go', '    call 0x18\n    push 0\n    eq\n    jz A1\n    call 0x8D\n' + put(more_put, MORE_BOG_FIGHT, 1) + warp('god_fight', first)
         + '    push {END}\n    end\nA1:\n    call 0x78(30)\n    pushn %d, %d, %d, %d, %d\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % HOME)
    # 4. The god fight won: Beerus spares the Earth (told at Capsule Corporation)
    say('told', BEERUS, "Heh... You're the second strongest I've ever fought, Son Goku.")
    say('told2', GOKU, "Second? Who's first?")
    say('told3', WHIS, "Lord Beerus, you can't destroy a planet with pudding this good. Time to go home.")
    say('told4', BEERUS, "...I'm sleepy. The Earth stays, for now. Save me some pudding.")
    say('told5', NARR, "Goku keeps the power of a Super Saiyan God!")
    code('told_end', put(more_put, MORE_BOG_TOLD, 1) + '    push {END}\n    end\n')
    say('after', WHIS, "Lord Beerus is napping back home. Oh, is that more pudding? How kind!")
    code('after_end', '    push {END}\n    end\n')
    return out
