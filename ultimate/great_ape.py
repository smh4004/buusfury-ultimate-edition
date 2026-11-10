"""The Great Ape raid (Nov 9; the owner: "Oozaru raid boss ... Transformation ONLY for GT Kid Goku and GT Vegeta ... Raid-boss fight in a
large wasteland map; beating it unlocks the transformation"). After the ending, once the GT looks are open (zone26.MORE_GT):

  1. Dr. Brief's Lab (4-1F), at Capsule Corporation. Bulma has rebuilt her Blutz Wave Generator: in Dragon Ball GT, the machine that turns
     a Saiyan into a Great Ape without the moon or a tail (Baby used it on himself; Bulma later used it on Vegeta). GT Vegeta wants the
     Great Ape's power back, and Bulma asks the player along in case he loses control. Vegeta himself can't be the one who comes: he is the
     one who changes (playing as him, Bulma asks for someone else: more_get(Q_VEGETA)).
  2. The Giant Crater (a copy of 6-10 in world 26: a big open wasteland with an old space pod at its heart). Bulma switches the generator
     on, Vegeta becomes a Great Ape and loses himself (two scene rooms: Vegeta, the flash, then the ape where he stood; a scene's figures
     can be added but not taken away, so the ape gets a room of his own).
  3. The raid: the Great Ape in the crater (lib/oozaru.py's figure on BF Broly's record and fighting row 10). Two rounds, as a raid boss's
     phases: brought down, it gets back up enraged (a scene room between them) for a stronger second round. Lose either, and it's back
     to the lab with the quest kept (the second round again once the first is won). No rest between the rounds, as Beerus's legs.
  4. Won: Vegeta is himself again, and Bulma retunes the waves to follow a Saiyan's will. From here GT Vegeta and GT Kid Goku (Old Kai gave
     him his tail back in GT) can become Great Apes: the skill (outfit.c ape_can / ape_use, learned in skills_sync), and her Zenie.
Every scene is a step of the West City resident's list (build.py quest_npc), as the other quests' are: its first step sends a talk in the
lab, or an entry into one of the scene rooms, here (`dispatch`). Bulma and Vegeta in the lab are spawn conditions on a copy of its records
(zone26.add_ape)."""

MORE_APE_START, MORE_APE_FIGHT, MORE_APE_HALF, MORE_APE_DONE = 64, 65, 66, 67     # more flags 64+ (outfit.c more_byte: the bench's spare bytes)
Q_VEGETA, Q_AREA = 250, 251                       # more_get queries (outfit.c): Vegeta is the one playing; this area (area << 8 | world)
ENDING = 149                                     # story flag: the ending has been seen
TEXT_BANK = 9                                    # its own dialogue bank (Battle of Gods has 7, Garlic Jr. 8)
LAB, CRATER = (4, 0x1F), (6, 0x10)               # Dr. Brief's Lab; the Giant Crater (copied as the raid's rooms)
BULMA, BULMA_SAYS, VEGETA_SAYS, NARR = 41, 0x11, 0x93, 0x00
BULMA_AT, VEGETA_AT = (352, 424), (304, 424)     # in the lab, below the big orange machine
HOME = (4, 0x1F, 1, 328, 448)                    # back in the lab (warp: world, area, entrance, x, y)
# In the crater's copies: the foe (and where Vegeta stands in the scenes), Bulma, and where the player lands. The camera stops at the map's
# foot, so with the player on the open ground below the bowl the screen shows the bowl's lower slope, where the others stand: above the
# dialogue box (standing on the ground beside the player, they were behind it) and clear of the space pod's pile of rubble in the
# middle, which is drawn over anyone standing higher up the bowl (the first test run had the ape behind it).
FOE_AT, BULMA_SCENE, ARRIVE = (330, 316), (150, 316), (240, 366)
# The rounds: (HP, (level + 50, Strength, Power, Endurance)) on copies of BF Broly's row (10; behaviour 51, the brawler his record goes with).
# Balanced on a level 150 Goku (fightrig.py; test_great_ape.py measures both rounds): a raid boss, longer than Super Garlic Jr. and hitting
# about as hard as Beerus's god fight (test_bog.py: 3-16% a hit). First tries, 60000/70000 HP at Strength 80/86: 30 and 35 of Goku's hits,
# but 18-19% of his health a hit; 90000/100000 at 70/75 (and 70/72): 44-54 hits, but 9-18% a hit from one run to the next (the heavy punch
# is the big one, and a few seconds' exchange lands it or not). Strength 62/66: about three quarters of that ((s + 100) s^2).
BROLY_ROW = 10
ROWS = ((90000, (155, 62, 70, 95)), (100000, (158, 66, 75, 100)))
ZENIE = 250000
ROOMS = ('intro', 'change', 'ape1', 'rage', 'ape2', 'end')
FIGHT_ROOMS = ('ape1', 'ape2')


def put(more_put, f, v): return '    pushn %d, %d\n    call 0x%X\n' % (f, v, more_put)
def get(more_get, f): return '    pushn %d\n    call 0x%X\n' % (f, more_get)


def when(more_get, on, off, extra=''):
    """A spawn condition: the ending seen and the GT looks open, every more flag in `on` set, every one in `off` clear, and `extra`."""
    import zone26
    t = '    pushn %d\n    call flag\n' % ENDING + get(more_get, zone26.MORE_GT) + '    and\n'
    t += ''.join(get(more_get, f) + '    and\n' for f in on)
    t += ''.join(get(more_get, f) + '    push 0\n    eq\n    and\n' for f in off)
    return t + (extra + '    and\n' if extra else '') + '    end\n'


def warp(to, fade=30):
    return '    call 0x78(%d)\n    pushn %d, %d, %d, %d, %d\n    call 0x77\n    call 0x79(30)\n' % ((fade,) + tuple(to))


def room_warp(room, fade=30):
    return warp((26, room, 1) + ARRIVE, fade)


REST = '    call max_hp\n    set hp\n    call max_ki\n    set ki\n'


def after_fight(k, rooms, more_put):
    """Where each round goes when the ape falls (its row's defeat script): the first to the scene where it gets back up (the round is
    kept from here), the second to the end."""
    if k == 0: return put(more_put, MORE_APE_HALF, 1) + room_warp(rooms['rage'], 20) + '    end\n'
    return room_warp(rooms['end'], 20) + '    end\n'


def death_branch(more_put, more_get):
    """The game's death script: in a round of the raid, back to the lab, rested, the quest kept (build.py death_script puts this first;
    `push 4` ends its list)."""
    revive = '    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n'
    return get(more_get, MORE_APE_FIGHT) + '    jz A9\n' + put(more_put, MORE_APE_FIGHT, 0) + revive + warp(HOME) + '    push 4\n    end\nA9:\n'


def places(rooms):
    """(world, area) of everywhere the dispatcher answers: the lab and the scene rooms."""
    return [LAB] + [(26, rooms[r]) for r in ROOMS if r not in FIGHT_ROOMS]


def dispatch(more_get, rooms):
    """Step code: which scene a talk or a room's entry is (labels X*)."""
    g = lambda f: get(more_get, f)
    def at(world_area): return g(Q_AREA) + '    pushn %d\n    eq\n' % (world_area[1] << 8 | world_area[0])
    t = ''
    for k, r in enumerate(r for r in ROOMS if r not in FIGHT_ROOMS):
        t += at((26, rooms[r])) + '    jz X%d\n    push {ape_%s}\n    end\nX%d:\n' % (k, r, k)
    # the lab: done; Vegeta playing; started (lost a round); or the start
    t += g(MORE_APE_DONE) + '    jz X7\n    push {ape_after}\n    end\nX7:\n'
    t += g(Q_VEGETA) + '    jz X8\n    push {ape_vegeta}\n    end\nX8:\n'
    t += g(MORE_APE_START) + '    jz X9\n    push {ape_again}\n    end\nX9:\n    push {ape_call}\n    end\n'
    return t


def lines():
    """Every line the quest says, to check lengths (build.py's NPC scripts refuse 100+ and 64-67 characters)."""
    return [t for _, t in SCENES_TEXT]


SCENES_TEXT = []


def steps(more_get, more_put, rooms, chars):
    """(name, step text) for the host list; {name} becomes that step's number. Starts with 'ape' (step 1's branch jumps there).
    chars: {actor name: character id} for the scenes' figures ('vegeta_gt', 'oozaru')."""
    out = []
    def say(name, who, text):
        if isinstance(who, str): who, text = NARR, '%s: %s' % (who, text)
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, (n, text)
        SCENES_TEXT.append((name, text))
        out.append((name, 'say 0x%02X @%d "%s"\n' % (who, TEXT_BANK, text)))
    def code(name, text): out.append((name, 'code\n' + text))
    def show(char, at): return '    pushn %d, %d, %d\n    call 0x35\n' % (char, at[0], at[1])
    def choose(label, then): return '    call 0x18\n    push 0\n    eq\n    jz %s\n' % label + then + '%s:\n    push {END}\n    end\n' % label
    fight = lambda: '    call 0x8D\n' + put(more_put, MORE_APE_FIGHT, 1)
    vegeta, ape = chars['vegeta_gt'], chars['oozaru']
    del SCENES_TEXT[:]
    code('ape', dispatch(more_get, rooms))
    # 1. the lab
    say('ape_call', VEGETA_SAYS, "Woman! Is that machine of yours ready? I want the Great Ape's power back.")
    say('ape_call2', BULMA_SAYS, "My Blutz Wave Generator! It shines like a full moon. No moon needed, no tail either.")
    say('ape_call3', VEGETA_SAYS, "Then take it to the Giant Crater. A Saiyan's true form needs room to grow.")
    say('ape_call4', BULMA_SAYS, "If he loses control, someone has to stop him. Will you come along with us?")
    say('ape_call5', NARR, "- Let's go!\\n- Not yet")
    code('ape_call_go', choose('C1', put(more_put, MORE_APE_START, 1) + room_warp(rooms['intro']) + '    push {END}\n    end\n'))
    say('ape_vegeta', BULMA_SAYS, "Vegeta, you are not testing that thing alone! Bring someone who can stop you.")
    code('ape_vegeta_end', '    push {END}\n    end\n')
    say('ape_again', BULMA_SAYS, "The Great Ape is still rampaging in the crater! Please, go back and stop him!")
    say('ape_again2', NARR, "- Go to the crater\\n- Not yet")
    code('ape_again_go', choose('A1', REST + fight() + get(more_get, MORE_APE_HALF) + '    jz A2\n' + room_warp(rooms['ape2']) + '    push {END}\n    end\nA2:\n'
                                + room_warp(rooms['ape1']) + '    push {END}\n    end\n'))
    say('ape_after', BULMA_SAYS, "Vegeta trains with the generator every night now. The crater looks like the moon!")
    say('ape_after2', VEGETA_SAYS, "Hmph. A Saiyan who can't master his own power is no true Saiyan at all.")
    code('ape_after_end', '    push {END}\n    end\n')
    # 2. the crater: the change
    code('ape_intro', show(vegeta, FOE_AT) + show(BULMA, BULMA_SCENE) + '    call wait(20)\n    end\n')
    say('ape_intro2', NARR, "The Giant Crater. An old Saiyan space pod still lies buried at its heart.")
    say('ape_intro3', BULMA_SAYS, "Generator on... Blutz waves at full power! Vegeta, look up!")
    say('ape_intro4', VEGETA_SAYS, "Yes... I can feel it! The power of a true Saiyan... RAAAAAGH!")
    code('ape_intro_fx', '    call play_sfx(24)\n    call 0x7A(6)\n    call 0x7B(6)\n    call 0x7A(6)\n    call 0x7B(6)\n'
         + room_warp(rooms['change'], 6) + '    push {END}\n    end\n')
    # the Great Ape where Vegeta stood (0x35 adds a figure to the scene, and nothing takes one away: a room of his own)
    code('ape_change', show(ape, FOE_AT) + show(BULMA, BULMA_SCENE) + '    call play_sfx(24)\n    call 0x7A(6)\n    call 0x7B(30)\n    call wait(20)\n    end\n')
    say('ape_change2', BULMA_SAYS, "Vegeta? Vegeta, can you hear me?! He's lost control!")
    say('ape_change3', NARR, "Stop the Great Ape! It won't stay down after one beating.")
    code('ape_change_go', fight() + room_warp(rooms['ape1'], 20) + '    push {END}\n    end\n')
    # 3. between the rounds: it gets back up
    code('ape_rage', show(ape, FOE_AT) + show(BULMA, BULMA_SCENE) + '    call wait(20)\n    end\n')
    say('ape_rage2', NARR, "The Great Ape crashes down... then rises again, roaring louder than ever!")
    say('ape_rage3', BULMA_SAYS, "He's getting even stronger! Don't give up now!")
    code('ape_rage_go', room_warp(rooms['ape2'], 20) + '    push {END}\n    end\n')
    # 4. won: Vegeta is himself again
    code('ape_end', show(vegeta, FOE_AT) + show(BULMA, BULMA_SCENE) + '    call wait(20)\n    end\n')
    say('ape_end2', NARR, "The Great Ape shrank back down, and Bulma switched the generator off.")
    say('ape_end3', VEGETA_SAYS, "Tch. The Prince of all Saiyans, ruled by his own power. Never again.")
    say('ape_end4', BULMA_SAYS, "Then let me help. I've tuned the waves to follow a Saiyan's will. You'll stay you!")
    say('ape_end5', BULMA_SAYS, "And Goku got his tail back from Old Kai, so it works for him too... as a kid!")
    code('ape_done', put(more_put, MORE_APE_FIGHT, 0) + put(more_put, MORE_APE_DONE, 1) + REST + '    pushn %d\n    call 0xF8\n    push {ape_prize}\n    end\n' % ZENIE)
    say('ape_prize', NARR, "GT Vegeta and GT Kid Goku can now become Great Apes! Got %d Zenie." % ZENIE)
    say('ape_prize2', NARR, "Hold Great Ape in one of your skill slots and press the B Button to change.")
    code('ape_home', warp(HOME, 60) + '    call 0x2F\n    call 0x33(0)\n    push {END}\n    end\n')
    return out
