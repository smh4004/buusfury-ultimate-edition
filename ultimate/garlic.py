"""The Garlic Jr. quest (Nov 9; the plan the owner answered, $S/deliver/BFU_Garlic_Jr_Quest_Plan.pdf, and his notes the same evening: "make it
somewhat thorough ... adapt the Garlic Jr Dead Zone movie a bit ... condense it like how the Broly fight is"). The Garlic Jr. saga of the
anime moved to after Buu, with Dende as guardian, and the Dead Zone movie told along the way. It opens with the ending and comes before
Battle of Gods (Whis waits for it: outfit.c, more_get 253).

  1. The hint. On the Lookout (6-01), Dende and Mr. Popo tell the movie: Garlic Jr. wished on the Dragon Balls for eternal life and attacked
     Kami, and Gohan's hidden power sent him into his own Dead Zone. Now the Makyo Star is close, and Hercule City feels wrong (GJ_START).
  2. The Black Water Mist. Hercule City's main street (3-01): its people are gone, and two of them, turned into Makyans, attack. Each
     Makyan's fall counts (GJ_FIGHT holds the first); the second clears the street (GJ_MIST) and Hercule comes out: they were his fans.
  3. He sends the player up Korin's Tower (6-0D). Korin knows the mist, and his Sacred Water, carried back down, cures the town (GJ_CURED);
     Hercule says the mist came from the Lookout.
  4. The Lookout: Garlic Jr. holds it with the Spice Boys; Dende and Mr. Popo are his prisoners; Piccolo stands against him. Talking to him
     starts the fights, one after another in copies of the Lookout (world 26 rooms: no exits, fighting on): Spice, then Vinegar, Mustard and
     Salt, each stepping up in a short scene of his own (a room of its own: a dialogue box with a boss loaded resets the game), back to back
     as the Cell Games. Salt down (GJ_SPICE), Garlic Jr. calls them useless and fights himself; beaten, he draws on the Makyo Star and becomes
     Super Garlic Jr. (a scene); beaten again, he opens the Dead Zone, and the player pushes him into it (a scene: the press-fast meter, as the
     Spirit Bomb's), as Gohan did in the movie. Dende and Mr. Popo are free (GJ_DONE).
     Lose any fight, and it's back to the Lookout with the quest kept (from Spice again, or from Garlic Jr. once the Spice Boys are beaten).
  5. Garlic Jr.'s Necklace (+END +Ki) and Zenie.
Every scene is a step of the West City resident's list (build.py quest_npc), as Battle of Gods' are: its first step sends a talk on the
Lookout, at Korin's or in Hercule City, or an entry into one of the scene rooms, here (`dispatch`). The quest's people and foes are spawn
conditions on copies of the areas' records (zone26.add_garlic). Garlic Jr., Super Garlic Jr., the Spice Boys and the Makyans are
lib/garlic_art.py's."""

GJ_START, GJ_FIGHT, GJ_MIST, GJ_CURED, GJ_SPICE, GJ_DONE = 58, 59, 60, 61, 62, 63    # more flags (the last six free: Bojack will need a second word)
Q_AREA = 251                                     # more_get query: this area (area << 8 | world)
LOOKOUT, KORIN, SATAN = (6, 0x01), (6, 0x0D), (3, 0x01)
ENDING = 149                                     # story flag: the ending has been seen
TEXT_BANK = 8                                    # its own dialogue bank (Battle of Gods has 7)
DENDE, POPO, KORIN_CHAR, HERCULE, PICCOLO = 77, 193, 165, 138, 222      # character ids (Piccolo: the Lookout's own, after the ending)
DENDE_AT, POPO_AT, KORIN_AT, HERCULE_AT = (312, 328), (288, 472), (136, 152), (312, 136)
GARLIC_AT = (312, 300)                           # on the Lookout, with the Spice Boys either side
SPICE_AT = ((264, 300), (360, 300), (224, 324), (400, 324))
MAKYANS = ((312, 136), (424, 136))               # the two on the main street (zone26's fight spots there)
LOOK_FOE, LOOK_ARRIVE = (312, 300), (312, 364)   # in the Lookout's copies: the foe, and where the player lands
FREED = ((272, 300), (352, 300))                 # Dende and Mr. Popo, freed, in the seal scene
HOME = (6, 0x01, 1, 312, 400)                    # back on the Lookout (warp: world, area, entrance, x, y)
SATAN_AT = (3, 0x01, 1, 312, 176)                # Hercule City's main street, below Hercule
KORIN_ARRIVE = (6, 0x0D, 1, 136, 174)            # Korin's talk spot
# The fights: (who, actor, base row (its behaviour), HP, (level + 50, Strength, Power, Endurance)). Balanced on a level 150 Goku (the owner,
# Nov 9: "Test these with a level 150 Goku ... and has some balancing"; test_garlic.py measures every fight, fightrig.py): mashing beside
# them he beats a Makyan in about 10 hits, a Spice Boy in about 15-20, Garlic Jr. in about 30, Super Garlic Jr. in about 40-45 (he took
# 4, 10-15, 20 and 35 at the first numbers); their hits take 4-10% of his health, Super Garlic Jr.'s no more than Beerus's (test_bog.py:
# his god fight's legs take 22-43 seconds of mashing and hit 3-9%: the hardest fights stay Battle of Gods').
MAKYAN = ('makyan', 68, 30000, (145, 55, 40, 55))
FIGHTS = (('spice', 70, 40000, (150, 70, 70, 70)),
          ('vinegar', 85, 40000, (150, 72, 60, 72)),
          ('mustard', 49, 40000, (150, 74, 60, 74)),
          ('salt', 130, 40000, (150, 70, 75, 70)),
          ('garlic_jr', 39, 55000, (152, 70, 90, 80)),
          ('super_garlic', 112, 75000, (155, 72, 90, 95)))   # Spopovich's fullest row (his figure's; behaviour 560, the one with most states)
SUPER_PHYS = 128                                 # every physical hit lands in full (Yakon's row, his first, took a twentieth)
# The Lookout's copies, in room order: a fight room's foe is FIGHTS[name]; the others are scenes (entered, they play their steps)
ROOMS = ('spice', 'i_vinegar', 'vinegar', 'i_mustard', 'mustard', 'i_salt', 'salt', 'i_garlic', 'garlic_jr', 'change', 'super_garlic', 'seal')
FIGHT_ROOMS = tuple(f[0] for f in FIGHTS)
NEXT = {'spice': 'i_vinegar', 'vinegar': 'i_mustard', 'mustard': 'i_salt', 'salt': 'i_garlic', 'garlic_jr': 'change', 'super_garlic': 'seal'}
GEAR_NECKLACE, ZENIE = 167, 300000


def put(more_put, f, v): return '    pushn %d, %d\n    call 0x%X\n' % (f, v, more_put)
def get(more_get, f): return '    pushn %d\n    call 0x%X\n' % (f, more_get)


def when(more_get, on, off, story=None):
    """A spawn condition: every more flag in `on` set, every one in `off` clear, and the story flag `story` set if given."""
    parts = [get(more_get, f) for f in on] + [get(more_get, f) + '    push 0\n    eq\n' for f in off]
    if story is not None: parts.append('    pushn %d\n    call flag\n' % story)
    return parts[0] + ''.join(p + '    and\n' for p in parts[1:]) + '    end\n'


def warp(to, fade=30):
    return '    call 0x78(%d)\n    pushn %d, %d, %d, %d, %d\n    call 0x77\n    call 0x79(30)\n' % ((fade,) + tuple(to))


def room_warp(room, fade=30):
    return warp((26, room, 1) + LOOK_ARRIVE, fade)


REST = '    call max_hp\n    set hp\n    call max_ki\n    set ki\n'


def makyan_fall(more_put, more_get):
    """A Makyan falls: the first sets the count; the second clears the street (and the count), and Hercule comes out (the street reloads with
    him in it, below him). (A defeat script waits while a level-up box is open.)"""
    return (get(more_get, GJ_FIGHT) + '    jz M1\n' + put(more_put, GJ_FIGHT, 0) + put(more_put, GJ_MIST, 1) + REST + warp(SATAN_AT, 40)
            + '    end\nM1:\n' + put(more_put, GJ_FIGHT, 1) + '    end\n')


def fight_fall(name, rooms, more_put):
    """Where a Lookout fight goes when its foe falls: the next scene (Salt's fall: the Spice Boys are beaten; the rest comes in the scene)."""
    extra = put(more_put, GJ_SPICE, 1) if name == 'salt' else ''
    return extra + room_warp(rooms[NEXT[name]], 20) + '    end\n'


def death_branch(more_put, more_get):
    """The game's death script: in a Garlic Jr. fight, the quest goes on (build.py death_script puts this first; `push 4` ends its
    list). Lost on the Lookout: back there, rested, the quest kept. Lost to the Makyans: back on the main street, the count reset (both
    come back), rested."""
    revive = '    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n'
    out = get(more_get, GJ_CURED) + get(more_get, GJ_FIGHT) + '    and\n    jz J1\n' + put(more_put, GJ_FIGHT, 0) + revive + warp(HOME) + '    push 4\n    end\nJ1:\n'
    out += (get(more_get, GJ_START) + get(more_get, GJ_MIST) + '    push 0\n    eq\n    and\n    jz J2\n' + put(more_put, GJ_FIGHT, 0) + revive + warp(SATAN_AT)
            + '    push 4\n    end\nJ2:\n')
    return out


def places(rooms):
    """(world, area) of everywhere the dispatcher answers: the quest's people's areas and the scene rooms."""
    return [LOOKOUT, KORIN, SATAN] + [(26, rooms[r]) for r in ROOMS if r not in FIGHT_ROOMS]


def dispatch(more_get, rooms):
    """Step code: which scene a talk or a room's entry is (labels Z*)."""
    g = lambda f: get(more_get, f)
    def at(world_area): return g(Q_AREA) + '    pushn %d\n    eq\n' % (world_area[1] << 8 | world_area[0])
    t = ''
    for k, r in enumerate(r for r in ROOMS if r not in FIGHT_ROOMS):
        t += at((26, rooms[r])) + '    jz Y%d\n    push {gj_%s}\n    end\nY%d:\n' % (k, r, k)
    t += at(KORIN) + '    jz Z3\n    push {gj_korin}\n    end\nZ3:\n'
    t += at(SATAN) + '    jz Z4\n' + g(GJ_CURED) + '    jz Z5\n    push {gj_cured}\n    end\nZ5:\n    push {gj_hercule}\n    end\nZ4:\n'
    # the Lookout: Garlic Jr. (after the cure), or Dende: his hint, then where to go
    t += g(GJ_CURED) + '    jz Z6\n' + g(GJ_SPICE) + '    jz Z7\n    push {gj_again}\n    end\nZ7:\n    push {gj_lookout}\n    end\n'
    t += 'Z6:\n' + g(GJ_MIST) + '    jz Z8\n    push {gj_dende_korin}\n    end\nZ8:\n' + g(GJ_START) + '    jz Z9\n    push {gj_dende_mist}\n    end\n'
    t += 'Z9:\n    push {gj_hint}\n    end\n'
    return t


def lines():
    """Every line the quest says, to check lengths (build.py's NPC scripts refuse 100+ and 64-67 characters)."""
    return [t for _, t in SCENES_TEXT]


NARR, DENDE_SAYS, POPO_SAYS, KORIN_SAYS = 0x00, 0x19, 0x63, 0x59
SCENES_TEXT = []


def steps(more_get, more_put, rooms, chars):
    """(name, step text) for the host list; {name} becomes that step's number. Starts with 'garlic' (step 1's branch jumps there).
    chars: {actor name: character id} for the scenes' figures."""
    out = []
    def say(name, who, text):
        if isinstance(who, str): who, text = NARR, '%s: %s' % (who, text)
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, (n, text)
        SCENES_TEXT.append((name, text))
        out.append((name, 'say 0x%02X @%d "%s"\n' % (who, TEXT_BANK, text)))
    def code(name, text): out.append((name, 'code\n' + text))
    def show(char, at): return '    pushn %d, %d, %d\n    call 0x35\n' % (char, at[0], at[1])
    def stage(name, figure): code(name, show(chars[figure], LOOK_FOE) + '    call wait(20)\n    end\n')
    del SCENES_TEXT[:]
    code('garlic', dispatch(more_get, rooms))
    # 1. Dende and Mr. Popo on the Lookout: the movie, and the hint
    say('gj_hint', DENDE_SAYS, "A dark star is drawing close to Earth. Mr. Popo calls it the Makyo Star.")
    say('gj_hint2', POPO_SAYS, "Long ago, Garlic Jr. wished on the Dragon Balls for eternal life, then attacked Kami.")
    say('gj_hint3', POPO_SAYS, "Gohan's hidden power threw him into his own Dead Zone. He is trapped there forever.")
    say('gj_hint4', DENDE_SAYS, "But the Makyo Star feeds him power... and the people of Hercule City feel wrong.")
    say('gj_hint5', DENDE_SAYS, "Please, go and see! Let me heal you first.")
    code('gj_hint_go', REST + put(more_put, GJ_START, 1) + '    push {gj_carpet}\n    end\n')
    say('gj_dende_mist', DENDE_SAYS, "A black mist hangs over Hercule City. Hurry, please!")
    code('gj_dende_mist_go', REST + '    push {gj_carpet}\n    end\n')
    # Mr. Popo's magic carpet takes you down to Hercule City
    say('gj_carpet', POPO_SAYS, "Mr. Popo will take you on his magic carpet.")
    say('gj_carpet2', NARR, "- Fly to Hercule City\\n- Not yet")
    code('gj_carpet_go', '    call 0x18\n    push 0\n    eq\n    jz P1\n' + warp(SATAN_AT) + 'P1:\n    push {END}\n    end\n')
    say('gj_dende_korin', DENDE_SAYS, "The Black Water Mist! Only Korin's Sacred Water can cure it.")
    say('gj_dende_korin2', DENDE_SAYS, "Korin's Tower is just below the Lookout. Let me heal you first.")
    say('gj_dende_korin3', NARR, "- Go down to Korin\\n- Not yet")
    code('gj_dende_korin_go', REST + '    call 0x18\n    push 0\n    eq\n    jz K1\n' + warp(KORIN_ARRIVE) + 'K1:\n    push {END}\n    end\n')
    # 2-3. Hercule City, after the Makyans fall; Korin; the cure
    say('gj_hercule', 'HERCULE', "Hey! Those weren't crooks, those were my fans! Some black mist got them!")
    say('gj_hercule2', 'HERCULE', "Their eyes went red, and they started biting folks like vampires!")
    say('gj_hercule3', 'HERCULE', "I hear Korin's Sacred Water cures anything. Up the tower you go, champ!")
    say('gj_hercule4', NARR, "- Go to Korin's Tower\\n- Not yet")
    code('gj_hercule_go', '    call 0x18\n    push 0\n    eq\n    jz H1\n' + warp(KORIN_ARRIVE) + 'H1:\n    push {END}\n    end\n')
    say('gj_korin', KORIN_SAYS, "The Black Water Mist, eh? So Garlic Jr. is out of the Dead Zone again.")
    say('gj_korin2', KORIN_SAYS, "His Spice Boys poured it down from Kami's Lookout. Take my Sacred Water.")
    say('gj_korin3', KORIN_SAYS, "A few drops on the wind, and the mist is gone. Go on!")
    code('gj_korin_go', put(more_put, GJ_CURED, 1) + '    call play_sfx(24)\n    call 0x7A(20)\n    call 0x7B(20)\n' + warp(SATAN_AT, 20) + '    push {END}\n    end\n')
    say('gj_cured', 'HERCULE', "Everyone's back to normal! I knew my training would pull them through!")
    say('gj_cured2', 'HERCULE', "They say the mist came down from Kami's Lookout. You'd better check on it!")
    say('gj_cured3', NARR, "- Go to the Lookout\\n- Not yet")
    code('gj_cured_go', '    call 0x18\n    push 0\n    eq\n    jz C1\n' + warp(HOME) + 'C1:\n    push {END}\n    end\n')
    # 4. The Lookout: Garlic Jr., the Spice Boys and Piccolo
    say('gj_lookout', 'GARLIC JR.', "So you're the one who cured my slaves. Dende and Mr. Popo are my guests now.")
    say('gj_lookout2', 'PICCOLO', "Garlic Jr.! Your father lost the guardian's post to Kami. You still want it?")
    say('gj_lookout3', 'GARLIC JR.', "Kami is gone, Piccolo. Under the Makyo Star, this Lookout is mine!")
    say('gj_lookout4', 'SPICE', "Leave this weakling to the Spice Boys, master.")
    code('gj_lookout_go', '    call 0x8D\n' + put(more_put, GJ_FIGHT, 1) + room_warp(rooms['spice']) + '    push {END}\n    end\n')
    say('gj_again', 'GARLIC JR.', "Back for more? This time the Dead Zone will have you for good!")
    code('gj_again_go', '    call 0x8D\n' + put(more_put, GJ_FIGHT, 1) + room_warp(rooms['i_garlic']) + '    push {END}\n    end\n')
    # each Spice Boy steps up in turn (scene rooms), then Garlic Jr.
    for room, figure, text in (('i_vinegar', 'vinegar', "Spice went down? Then I'll tear you apart myself!"),
                               ('i_mustard', 'mustard', "Under the Makyo Star I'm twice as strong. Come on!"),
                               ('i_salt', 'salt', "Heh, they were soft. Watch how a real demon fights!")):
        stage('gj_' + room, figure)
        say('gj_%s_say' % room, figure.upper(), text)
        code('gj_%s_go' % room, room_warp(rooms[figure], 20) + '    push {END}\n    end\n')
    code('gj_i_garlic', REST + show(chars['garlic_jr'], LOOK_FOE) + '    call wait(20)\n    end\n')     # (the Spice Boys beaten: a rest)
    say('gj_i_garlic2', 'GARLIC JR.', "Useless, all four of you! Fine. I'll do it myself.")
    say('gj_i_garlic3', 'GARLIC JR.', "I can never die, fool. The Dragon Balls made sure of that!")
    code('gj_i_garlic_go', room_warp(rooms['garlic_jr'], 20) + '    push {END}\n    end\n')
    # his change: the Makyo Star
    stage('gj_change', 'garlic_jr')
    say('gj_change2', 'GARLIC JR.', "Immortal, remember? Makyo Star, give me your power!")
    code('gj_change_fx', '    call play_sfx(24)\n    call 0x7A(6)\n    call 0x7B(6)\n    call 0x7A(6)\n    call 0x7B(6)\n    call 0x7A(24)\n'
         + show(chars['super_garlic'], LOOK_FOE) + '    call wait(30)\n    call 0x7B(40)\n    call wait(20)\n    push {gj_change3}\n    end\n')
    say('gj_change3', NARR, "Garlic Jr. grew into a giant: Super Garlic Jr.!")
    code('gj_change_go', room_warp(rooms['super_garlic'], 20) + '    push {END}\n    end\n')
    # 5. The seal: he opens the Dead Zone, and goes into it himself, as in the movie; Dende and Mr. Popo freed
    stage('gj_seal', 'super_garlic')
    say('gj_seal2', 'SUPER GARLIC JR.', "Enough! The Dead Zone will swallow you and this whole planet!")
    say('gj_seal3', NARR, "The Dead Zone opens! Push him into it! Press the A Button fast!")
    code('gj_seal_push', '    call 0xC6\n    end\n')
    code('gj_seal_fx', '    call play_sfx(24)\n    pushn 5, 200, 200, 255, 10\n    call 0x4C\n    call wait(30)\n    call 0x7A(20)\n'
         + show(chars['super_garlic'], (0, 0)) + '    call 0x7B(30)\n    call wait(20)\n    push {gj_seal4}\n    end\n')
    say('gj_seal4', NARR, "As Gohan once did, you send Garlic Jr. into his own Dead Zone. The Makyo Star fades.")
    code('gj_freed', show(DENDE, FREED[0]) + show(POPO, FREED[1]) + '    call wait(20)\n    push {gj_thanks}\n    end\n')
    say('gj_thanks', DENDE_SAYS, "You saved us all! Mr. Popo and I are free, and the Lookout is safe again.")
    say('gj_thanks2', POPO_SAYS, "Garlic Jr. left this behind. Mr. Popo thinks that you should wear it.")
    code('gj_done', put(more_put, GJ_FIGHT, 0) + put(more_put, GJ_DONE, 1) + REST + '    call 0x93(%d)\n    pushn %d\n    call 0xF8\n    push {gj_prize}\n    end\n'
         % (GEAR_NECKLACE, ZENIE))
    say('gj_prize', NARR, "Got Garlic Jr.'s Necklace and %d Zenie!" % ZENIE)
    code('gj_home', warp(HOME, 60) + '    call 0x2F\n    call 0x33(0)\n    push {END}\n    end\n')
    return out
