#!/usr/bin/env python3
"""Buu's Fury Ultimate Edition build. Run from the repo root.

    python3 ultimate/build.py [--debug]

Needs baserom.gba (clean USA Buu's Fury, checked by SHA-1) and assets from `make extract`.
Steps: apply edits to assets (debug only for now), `make modern`, move the form table past the ROM's old end,
append ultimate/forms.json rows, then write ultimate/out/BFU[_debug].bps and a personal-use .gba.
Asset edits are always undone afterwards, so assets/ stays a clean extract.
"""
import colorsys, hashlib, json, os, re, shutil, struct, subprocess, sys, tempfile
sys.path.insert(0, os.path.join('tools'))
sys.path.insert(0, 'ultimate/lib')
import bps
import numpy as np
import sprites, artclean, wfz
sys.path.insert(0, 'ultimate')
import gogeta
import goku_black
import gt

CLEAN_SHA1 = 'f1c4b07554d2a3b1ad2f325307051e775ce68087'
ROM_BASE = 0x08000000
FORMS, FORM_COUNT, FORM_SIZE = 0x6B82EC, 54, 24
NATIVES = 0x55098
CODE_END = 0x54FBC
HEAP_WORDS = 0xFDFE - 0x400      # the top 4 KB of work RAM belongs to outfit.c
SPACE = 0x800000                 # new data starts at the old 8 MB end: forms, then code
ACTORS_AT = 0x840000             # moved actor table and imported sprites
COMBO_SHA1 = 'f02d179accbeb9b68bcaef8720eb0ae426dde6ee'
PROTO = os.environ.get('BFU_PROTO', 'protoD.gba')   # Prototype D cart: Super 13 and Zone 26
LOG2 = os.environ.get('BFU_LOG2', 'log2.gba')      # Legacy of Goku II (USA): Zone 26's snow tiles
COMBO = os.environ.get('BFU_COMBO', 'combo.gba')   # Legacy of Goku I & II cart; LoG2 = its second 8 MB
JOIN_NATIVE = 0xE8               # party_join in outfit.c; no game script calls this native
JOIN_OLD = 0x08003891
ERASER_SKILL = 24                # a new row past the retail table: Big Bang's code with green frames
ERASER_UI = 1534                 # strings past the retail table: name, description of each new move
BOMBER_SKILL = 25
PORTRAITS = (20, 90, 94)         # LoG2 portrait table: Android 17, Future Trunks, Super Saiyan Future Trunks = speaker ids 163, 164, 165
SS2_FLAG = 864                   # + the owner's party slot: set where the story reaches Super Saiyan 2
BLITZ_SKILL = 27                 # Android 17 and 18
DISC_SKILL = 28                  # Krillin and Android 18: LoG2's spinning gold disc on Big Bang's code
POWER_UP_VT = 0x4E2B0            # the state a transformation runs in
SUPER13_SKILL, SUPER17_SKILL = 30, 31     # Android 13 and Android 17 transform: Super Saiyan's mechanics under their own names
WAVE_SKILL = 29                  # Full Power Energy Wave, from Gero's Legacy: the Electric Kamehameha's code with green frames
BEAM_SKILL = 26                  # Special Beam Cannon: the Kamehameha's code with gold and purple frames
ROSE_SKILL, BLACK_KAME_SKILL = 32, 33      # Goku Black: Super Saiyan Rose (Super Saiyan's mechanics), Black Kamehameha (the Kamehameha's code, purple, or pink as Rose)
BLACK_NAME_UI, ROSE_NAME_UI = 1534 + 42, 1534 + 43     # form names, after Glacier's
GT_NAME_UI = 1534 + 44            # Pan, Uub, Majuub, Brapan (forms.json uses these numbers)
MAJUUB_SKILL = 34                # Uub becomes Majuub: Super Saiyan's mechanics, Android 13's aura-less power-up
BLACK_PORTRAIT = 166             # speaker ids: Goku Black, then Rose
# The Kamehameha's colours, by brightness: a cyan set (levels 1-2) and a gold set (level 3). Black's ki is dark purple and Rose's pink.
KAME_TINT = {'black': {2: (240, 208, 248), 76: (216, 144, 240), 195: (176, 80, 224), 75: (120, 32, 176), 74: (56, 0, 88),
                       30: (240, 208, 248), 29: (224, 168, 248), 28: (208, 128, 240), 5: (176, 80, 224), 27: (144, 48, 200), 110: (120, 32, 176), 109: (88, 16, 136), 4: (56, 0, 88)},
             'rose': {2: (255, 232, 248), 76: (248, 184, 232), 195: (240, 136, 216), 75: (224, 64, 192), 74: (144, 0, 120),
                      30: (255, 232, 248), 29: (248, 200, 240), 28: (248, 168, 232), 5: (240, 136, 216), 27: (232, 104, 208), 110: (224, 64, 192), 109: (184, 24, 160), 4: (144, 0, 120)}}
BLAST_HUE = {'black': 280, 'rose': 320}    # their ki blasts
# Strength against Big Bang per skill level: 2.5x and 2x in total damage. Each hit rounds down, which costs low levels more, so they get a bigger multiplier (measured on Android 13 at Power 80).
NEW_MOVES = (('eraser', ERASER_SKILL, (2.95, 2.85, 2.45), 'Eraser Cannon', 'Press the B Button and release to emit a large ball of green energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (0.2, 0.6, 1, 0, 0.15, 0.6)),
             ('bomber', BOMBER_SKILL, (2.4, 2.2, 2), 'SS Deadly Bomber', 'Press the B Button and release to emit a large ball of reddish pink energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (1, 0, 0.03, 0.55, 0.12, 0.45)),
             ('blitz', BLITZ_SKILL, (1, 1, 1), 'Power Blitz', 'Press the B Button and release to emit a large ball of golden energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (1, 0, 0.75, 0.1, 0.05, 0.3)),
             ('disc', DISC_SKILL, (2.4, 2.2, 2), 'Destructo Disc', 'Press the B Button and release to throw a spinning disc of energy that explodes on contact.  Hold the B Button longer to make the attack stronger.', (1, 0, 0.85, 0.15, 0.1, 0.8)))
SUPER_BLUE_SKILL = 21            # a skill row with stubs only: becomes Super Saiyan Blue
BROLY_DEFEAT = 'assets/scripts/gUnknown_0879321C.evt'
DEBUG_NATIVE = 0xF5              # debug builds only: "save to slot 1". Not 0xF7: the death script uses that one
OUT = os.environ.get('BFU_OUT', 'ultimate/out')
SAIYAMAN = [(10, 14), (15, 'saiyaman_from_green'), (13, 'saiyaman_from_orange'), ('gohan_gt', 'saiyaman_from_gt'), ('gohan_gt_noglasses', 'saiyaman_from_gt_ng')]
SS2_LIKE = ('vegeta_gt_ssj4', 'vegeta_gt_tank_ssj4')      # GT Vegeta's Super Saiyan 4 sits where Super Saiyan 2 would: Super Saiyan pressed again
ACTORS_FILE = 'assets/areas/a033_w01_01_Snakeway.actors'
INTRO = 'assets/scripts/gUnknown_0877CBF0.evt'
ENDING = 'assets/scripts/gUnknown_08796114.evt'
FIELD = 'assets/scripts/gUnknown_08780550.evt'


SKILL_ROWS, UI_TABLE = 0x71DAF8, 0x6BCE8
SKILLS, SPIRIT_SKILL, SPIRIT_NAME = 0x71DB04, 19, 1050      # UI 1050 and 1053 are unused text
UI = 'assets/text/ui_strings.txt'
ACTOR_BASE = 298


def new_actor_ids():
    """Ids add_actors will give: actors.json's new actors in order, then Super 13 and Android 13. Checked after the build."""
    cfg = json.load(open('ultimate/actors.json'))
    n = ACTOR_BASE + sum(1 for k, a in cfg.items() if not k.startswith('_') and 'replace' not in a)
    return {'super13': n, 'android13': n + 1, 'broly_fp': n + 2, 'gogeta_dbs': n + 3, 'gogeta_dbs_ss': n + 4, 'gogeta_ssb': n + 5, 'android13_player': n + 6, 'super13_player': n + 7, 'goku_ss2': n + 8, 'goku_ss2_b': n + 9, 'gohan_ss2': n + 10, 'gohan_green_ss2': n + 11, 'vegeta_ss2': n + 12, 'vegeta_ss2_b': n + 13, 'vegeta_armor_ss2': n + 14, 'gohan_armor_ss2': n + 15, 'trunks_ss2': n + 16, 'trunks_armor_ss2': n + 17, 'vegito_ss2': n + 18, 'super17': n + 19, 'android13_absorb': n + 20, 'cell_imperfect': n + 21, 'cell_semi': n + 22, 'cell_perfect': n + 23, 'cell_junior': n + 24, **{'dragon_ball_%d' % (k + 1): n + 25 + k for k in range(7)}, 'goku_black': n + 32, 'goku_rose': n + 33, **{k: n + 34 + i for i, k in enumerate(gt.ACTORS)}}


DEATH_SCRIPT = 'assets/scripts/gUnknown_0877C5A4.evt'
POPO_NPC = 'assets/scripts/gUnknown_08786E68.evt'   # Mr. Popo on the Lookout: after the ending, the Hyperbolic Time Chamber
HUB_NPC = 'assets/scripts/gUnknown_08783D30.evt'    # a Hercule City resident: post-game, the tournament official's Challenge Board
TOUR_NPC = 'assets/scripts/gUnknown_08785590.evt'   # the West City resident to the west
QUEST_NPC = 'assets/scripts/gUnknown_08785580.evt'   # the West City resident outside the Z-Mart


UI_EDITS = {1051: 'Press the B Button to transform into a Super Saiyan Blue. You must already be a Super Saiyan to use this technique.', 1052: 'Android 13', 1054: 'DBS Gogeta', 1055: 'SSB Gogeta', 1056: 'Super 13', 1057: 'Super Saiyan Blue'}


def form_row(name):
    rows = json.load(open('ultimate/forms.json'))['rows']
    return FORM_COUNT + [r['id'] for r in rows].index(name)


def broly_defeat(src):
    """Beating Broly in the story adds him to the party, and says so once the fight's closing scene has played."""
    head = '    call set_flag(111)\n'
    tail = '    call 0x7B(50)\n    call 0x33(0)\n    end\n'
    if src.count(head) != 1 or not src.endswith(tail):
        sys.exit('Broly defeat script changed')
    src = src.replace(head, head + '    pushn 8, %d\n    call 0x%X\n' % (form_row('broly'), JOIN_NATIVE))
    return src[:-len(tail)] + '''    call 0x7B(50)
    end
step 2 say 0x00 "Broly joins you! Pick him on the Switch Character menu."
step 3 code
    call 0x33(0)
    end
'''


def quest_npc(src):
    """Post-game, this resident sends you to Zone 26, and rewards you once Super 13 is beaten (his death script runs this list).
    A step's `push N` jumps to the Nth step counting from 0, the same number the following step's position gets; past the last step ends the list."""
    head, old = src.split('step 1 say', 1)
    ids = new_actor_ids(); super13 = ids['super13'] + 9; absorb = ids['android13_absorb'] + 9
    return head + '''step 1 code
    pushn 888
    call flag
    pushn 887
    call not_flag
    and
    jz L8
    push 22
    end
L8:
    pushn 881
    call flag
    pushn 884
    call not_flag
    and
    jz L4
    push 13
    end
L4:
    pushn 886
    call flag
    pushn 882
    call not_flag
    and
    jz L5
    push 16
    end
L5:
    pushn 883
    call flag
    jz L1
    push 11
    end
L1:
    pushn 882
    call flag
    jz L2
    push 7
    end
L2:
    pushn 884
    call flag
    jz L7
    push 25
    end
L7:
    call flag(149)
    jz L3
    push 3
L3:
    end
step 2 say''' + old.rstrip() + '''
step auto code
    push 25
    end
step auto say 0x85 "Something's wrong past the Z-Mart. Dr. Gero's old computer has woken up!"
step auto say 0x85 "It built one last Android, up in the snow. Hurry!"
step auto code
    call 0x78(30)
    pushn 26, 1, 1, 128, 240
    call 0x77
    call 0x79(30)
    end
step auto code
    push 25
    end
step auto say 0x85 "The signal stopped! You beat Super 13!"
step auto say 0x85 "Saiyan armor from Capsule Corp, and new allies! See the Switch Character menu."
step auto say 0x85 "And Goku, you learned the Spirit Bomb! Press L to select it."
step auto code
    pushn 883
    call set_flag
    pushn 0, 19
    call 0xA4
    pushn 1, 26
    call 0xA4
    pushn 873
    call set_flag
    pushn 874
    call set_flag
    pushn 875
    call set_flag
    pushn 876
    call set_flag
    pushn 877
    call set_flag
    pushn 878
    call set_flag
    pushn 879
    call set_flag
    pushn 880
    call set_flag
    pushn 8, %d
    call 0x%X
    pushn 7, %d
    call 0x%X
    push 25
    end
step auto say 0x85 "Want a real fight? Hercule City has a Challenge Board now. Ask the tournament official!"
step auto code
    push 25
    end
step auto code
    pushn %d, 120, 214
    call 0x35
    end
step auto say 0x00 "Android 13 pulls in the broken parts of 14 and 15!"
step auto code
    pushn 884
    call set_flag
    call play_sfx(24)
    call wait(120)
    call 0x7A(6)
    call 0x7B(6)
    call 0x7A(6)
    call 0x7B(6)
    call 0x7A(24)
    pushn %d, 120, 214
    call 0x35
    pushn %d, 17, 0
    call 0x51
    call 0x7B(40)
    call wait(50)
    pushn 5, 200, 200, 255, 10
    call 0x4C
    pushn %d, 20, 0
    call 0x51
    call wait(40)
    push 25
    end
step auto say 0x02 "He's still standing! I need everyone's energy!"
step auto code
    call 0x95(0)
    pushn %d, 120, 214
    call 0x35
    pushn 100, 15
    call 0x2A
    push 120
    set 0x04
    push 236
    set 0x05
    push 6
    set 0x06
    push 42
    loop_begin
L1:
    call 0x04
    call 0x05
    call 0x06
    call 0xE6
    call 0xE5(1)
    inc 0x06
    call wait(2)
    loop L1
    end
step auto say 0x00 "Push the Spirit Bomb! Press the A Button fast!"
step auto code
    call 0xC6
    end
step auto code
    pushn 5, 200, 200, 255, 10
    call 0x4C
    push 40
    loop_begin
L1:
    call 0x04
    call 0x05
    call 0x06
    call 0xE6
    call 0xE5(1)
    dec 0x05
    call wait(1)
    loop L1
    pushn %d, 9, 0
    call 0x51
    push 90
    loop_begin
L3:
    call 0x04
    call 0x05
    call 0x06
    call 0xE6
    call 0xE5(1)
    call 0x19(10)
    push 0
    eq
    jz L4
    call play_sfx(24)
    pushn 5, 200, 200, 255, 10
    call 0x4C
L4:
    call wait(1)
    loop L3
    pushn %d, 16, 0
    call 0x51
    call play_sfx(24)
    call 0xE5(2)
    call wait(3)
    call 0xE5(5)
    call wait(3)
    call 0xE5(8)
    call wait(3)
    call 0xE5(11)
    push 5
    loop_begin
L2:
    pushn 5, 200, 200, 255, 10
    call 0x4C
    call wait(15)
    loop L2
    call 0xE5(0)
    pushn 882
    call set_flag
    call max_hp
    set hp
    call max_ki
    set ki
    call 0x78(60)
    pushn 4, 1, 1, 320, 392
    call 0x77
    call 0x79(30)
    call 0x2F
    call 0x33(0)
    end
step auto code
    push 25
    end
step auto say 0x85 "You beat all nine! Majin Buu, Super Janemba and Kid Buu join you. See Switch Character."
step auto code
    pushn 887
    call set_flag
    push 25
    end
step auto code
    end
''' % (form_row('android13'), JOIN_NATIVE, form_row('gogeta_dbs'), JOIN_NATIVE, absorb, super13, super13, super13, super13, super13, super13)


def tournament_npc(src):
    """The West City resident who ran the World Tournament now sends you to Hercule City. A debug zone build also uses him as a test's way into that city."""
    head, old = src.split('step 1 say', 1)
    warp = '    call 0xE4\n    call 0x95\n    call 0xE3\n' if '--trailer' in sys.argv else '    pushn 3, 1, 1, 208, 134\n'     # a trailer build takes the room from RAM a filming script pokes
    hook = '    pushn 862\n    call flag\n    jz L0\n    call 0x78(30)\n' + warp + '    call 0x77\n    call 0x79(30)\n    push 4\n    end\nL0:\n' if '--zone' in sys.argv else ''
    credits = '''step 2 say 0x00 "Buu's Fury: Ultimate Edition\\nComing Soon"
step auto say 0x00 "An unofficial fan project. Dragon Ball Z and Buu's Fury belong to their owners."
step auto say 0x00 "Broly Full Power sprites by Azure-Oni, ripped by DBZdogs."
step auto say 0x00 "Gogeta sprites ripped by Mister Man, edited by Azure-Oni."
step auto code
    push 7
    end
''' if '--trailer' in sys.argv else None
    if credits:
        return head + 'step 1 code\n' + hook.replace('push 4', 'push 7') + """    pushn 883
    call flag
    jz L2
    push 5
    end
L2:
    end
""" + credits + """step auto say 0x5E "The World Tournament has moved to Hercule City. Ask the tournament official!"
step auto code
    end
"""
    return head + 'step 1 code\n' + hook + """    pushn 883
    call flag
    jz L2
    push 2
    end
L2:
    end
step 2 say""" + old.rstrip() + """
step auto say 0x5E "The World Tournament has moved to Hercule City. Ask the tournament official!"
step auto code
    end
"""


def death_script(src):
    """The game's death script: a lost Time Chamber fight rests you and goes back to the Lookout, the way the Lazarus Crystal revives you."""
    import zone26
    first = 'step 7 zcode'
    if first not in src: sys.exit('death script changed')
    head, rest = src.split(first, 1)
    line, body = rest.split('\n', 1)
    home = zone26.spar_off() + '    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n    call 0x78(30)\n    pushn 6, 1, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    push 4\n    end\n' % zone26.SPAR_HOME     # steps count from 0 here: 4 is the list's end, while just `end` would run on into the next step and the game over
    new = '    pushn %d\n    call flag\n    pushn %d\n    call flag\n    and\n    jz L9\n' % zone26.CELL_COUNT + home + 'L9:\n'
    endless = '    pushn 1\n    call 0x%X\n    jz L8\n    pushn 3\n    call 0x%X\n    call max_hp\n    set hp\n    pushn 0, 0\n    call 0x3C\n    call 0xF7(5)\n    call 0x78(30)\n    pushn 3, 1, 1, 208, 134\n    call 0x77\n    call 0x79(30)\n    push 4\n    end\nL8:\n' % (zone26.LADDER, zone26.LADDER)
    return head + first + line + '\n' + endless + new + body


def symbol_items_icon(item):
    """Where the item's menu icon is in the base ROM (items.csv names it)."""
    import csv
    rows = list(csv.reader(open('assets/tables/items.csv', encoding='latin1')))
    head = next(r for r in rows if r and r[0] == 'index')
    row = next(r for r in rows if r and r[0] == str(item))
    return int(row[head.index('icon')].split('_')[1], 16) - ROM_BASE


def popo_npc(src):
    """After the ending Mr. Popo opens the Hyperbolic Time Chamber: a category, then a partner, up to four to a page. Before it he says what he always said."""
    import zone26
    speaker = 0x63
    steps = []
    def say(name, text):
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, text      # long lines reset the game; 64-67 look like ROM pointers to the shifter
        steps.append((name, 'say 0x%02X "%s"\n' % (speaker, text)))
    def code(name, text): steps.append((name, 'code\n' + text))
    def choose(name, targets):
        code(name, ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    push {%s}\n    end\nL%d:\n' % (k, k + 1, t, k + 1) for k, t in enumerate(targets)) + '    push {END}\n    end\n')
    say('hello', "The Hyperbolic Time Chamber is open. A day inside is a year outside. Train against who?")
    pages = zone26.SPAR
    say('menu1', '\\n'.join('- %s' % c for c, _ in pages[:3]) + '\\n- More')
    choose('menu1_go', ['cat0', 'cat1', 'cat2', 'menu2'])
    say('menu2', '\\n'.join('- %s' % c for c, _ in pages[3:]) + '\\n- Back')
    choose('menu2_go', ['cat3', 'cat4', 'cat5', 'menu1'])
    room = zone26.spar_first()
    for c, (_, people) in enumerate(pages):
        say('cat%d' % c, '\\n'.join('- %s' % p[0] for p in people))
        choose('cat%d_go' % c, ['p%d' % (room + k) for k in range(len(people))])
        room += len(people)
    say('locked', "You have not met that one yet.")
    code('locked_end', '    push {END}\n    end\n')
    room = zone26.spar_first()
    for _, people in pages:
        for name, row, _ in people:
            gate = '    call flag(111)\n    jz L1\n' if name == 'Broly' else ''
            tail = 'L1:\n    push {locked}\n    end\n' if name == 'Broly' else ''
            code('p%d' % room, gate + zone26.spar_on() + '    call 0x78(30)\n    pushn 26, %d, 1, 120, 150\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % room + tail)
            room += 1
    # The Dragon Balls. A ball on the map starts this same list, so the first thing it does is ask where it is.
    balls = new_actor_ids()
    for k in range(7):
        steps.append(('ball%d' % k, 'say 0x00 "You found the %d-Star Dragon Ball!"\n' % (k + 1)))
        code('ball%d_go' % k, '    call 0x80(%d)\n    pushn %d, 0, 0\n    call 0x35\n    push {END}\n    end\n' % (zone26.BALL_ITEM + k, balls['dragon_ball_%d' % (k + 1)] + 9))
    steps.append(('summon', 'say 0x%02X "All seven Dragon Balls! Stand back. I will call the Eternal Dragon."\n' % speaker))
    code('summon_go', '    call music(40)\n    call play_sfx(23)\n    call 0x7A(20)\n    pushn 4, 20, 2, 120, 176\n    call load_scene\n    pushn 0, 228, 221\n    call 0x69\n    pushn 1, 244, 221\n    call 0x69\n    pushn 2, 220, 236\n    call 0x69\n    pushn 3, 236, 236\n    call 0x69\n    pushn 4, 252, 236\n    call 0x69\n    pushn 5, 228, 251\n    call 0x69\n    pushn 6, 244, 251\n    call 0x69\n    call 0x64(0)\n    call 0x64(1)\n    call 0x64(2)\n    call 0x64(3)\n    call 0x64(4)\n    call 0x64(5)\n    call 0x64(6)\n    call 0x7B(90)\n    end\n')
    dragon = 0x7A
    steps.append(('wish_say', 'say 0x%02X "You who have gathered the Dragon Balls, speak your wish!"\n' % dragon))
    steps.append(('wish', 'say 0x%02X "- Greater power\\n- Riches\\n- New fighters\\n- Super Saiyan 2"\n' % dragon))
    choose('wish_go', ['w_power', 'w_rich', 'w_fighters', 'w_ss2'])
    code('w_power', '    call 0x%X\n    push {done}\n    end\n' % zone26.WISH_NATIVE)
    code('w_rich', '    pushn %d\n    call 0x%X\n    push {done}\n    end\n' % (zone26.BALL_ZENIE, zone26.ADD_ZENIE))
    code('w_fighters', '    pushn 887\n    call set_flag\n    push {done}\n    end\n')
    code('w_ss2', ''.join('    pushn %d\n    call set_flag\n' % (SS2_FLAG + k) for k in range(9)) + '    push {done}\n    end\n')
    steps.append(('done', 'say 0x%02X "It is done. Farewell!"\n' % dragon))
    code('wish_end', ''.join('    call take_item(%d)\n' % (zone26.BALL_ITEM + k) for k in range(7)) + '    call 0x7A(30)\n    pushn 6, 1, 1, %d, %d\n    call 0x77\n    call 0x7B(40)\n    push {END}\n    end\n' % zone26.SPAR_HOME)
    code('last', '    end\n')
    number = {n: k + 2 for k, (n, _) in enumerate(steps)}; number['END'] = len(steps) + 2      # counted from 0; the first two are his old line
    head, old = src.split('step 1 code', 1)
    if '    push 5\n' not in old or not old.rstrip().endswith('call 0x16\n    end'):
        sys.exit("Mr. Popo's script changed")
    old = old.replace('    push 5\n', '    push %d\n' % number['END']).rstrip()
    old = old[:-len('end')] + 'push %d\n    end\n' % number['END']
    first = ''.join('\n    call 0x%X\n    push %d\n    eq\n    jz B%d\n    push %d\n    end\nB%d:' % (zone26.BALL_NATIVE, k + 1, k, number['ball%d' % k], k) for k in range(7))
    all7 = ''.join('\n    call 0x7F(%d)%s' % (zone26.BALL_ITEM + k, '\n    and' if k else '') for k in range(7))
    first += all7 + '\n    jz A9\n    call flag(149)\n    jz A9\n    push %d\n    end\nA9:' % number['summon']
    first += '\n    call flag(149)\n    jz L9\n    push %d\n    end\nL9:' % number['hello']
    line, rest = old.split('\n', 1)
    return head + 'step 1 code' + line + first + '\n' + rest + ''.join('step auto %s' % re.sub(r'\{(\w+)\}', lambda m: str(number[m.group(1)]), t) for _, t in steps)


def hub_npc(src):
    """Hercule City's tournament official (character 192, speaker 0x62), once Super 13 is beaten: the Challenge Board. Before that his list is the resident's old line."""
    import zone26
    head, old = src.split('step 1 say', 1)
    speaker = 0x62
    steps = []                                 # (name, text of the step); a {name} in the text becomes that step's number
    def say(name, text):
        n = len(text.replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, text      # long lines reset the game; 64-67 look like ROM pointers to the shifter
        steps.append((name, 'say 0x%02X "%s"\n' % (speaker, text)))
    def code(name, text): steps.append((name, 'code\n' + text))
    trials = zone26.TRIALS
    won = lambda k: zone26.TRIAL_WON + k
    paid = lambda k: zone26.TRIAL_PAID + k
    picker_first = '    call 0x8D\n    call 0x%X\n    push {END}\n    end\n' % DEBUG_NATIVE if os.environ.get('BFU_SLOT_TEST') else ''   # test_slots.py: open Switch Character and save here
    if os.environ.get('BFU_HUB_EVENT'): picker_first = '    pushn %s, 0, 0\n    call run_event\n    push {END}\n    end\n' % os.environ['BFU_HUB_EVENT']     # a test plays one of the game's scripts by talking to the official
    if os.environ.get('BFU_HUB_WARP'): picker_first = '    pushn %s\n    call 0x77\n    push {END}\n    end\n' % os.environ['BFU_HUB_WARP']     # a test goes straight to a room by talking to the official
    more = lambda n: '    pushn %d\n    call 0x%X\n' % (n, zone26.MORE_GET)
    put = lambda n, v: '    pushn %d, %d\n    call 0x%X\n' % (n, v, zone26.MORE_PUT)
    lad = lambda op: '    pushn %d\n    call 0x%X\n' % (op, zone26.LADDER)
    def pending(test, name, lab): return test + '    jz %s\n    push {%s}\n    end\n%s:\n' % (lab, name, lab)
    museum_done = '    pushn 341, 5\n    call 0xBA\n    push 25\n    eq\n    pushn 346, 4\n    call 0xBA\n    push 15\n    eq\n    and\n'
    race_won = '    call 0x7F(61)\n    pushn 234\n    call flag\n    or\n'
    start = picker_first + """    pushn 883
    call not_flag
    jz L0
    end
L0:
""" + pending(more(zone26.MORE_RANK_NEW), 'rank', 'P1') + pending(more(zone26.MORE_ENDLESS_NEW), 'endless_done', 'P2') + pending(more(zone26.MORE_HARD) + more(zone26.MORE_HARD_PAID) + '    push 0\n    eq\n    and\n', 'hard_won', 'P3') + pending(more(zone26.MORE_HERC_WON) + more(zone26.MORE_HERCULE) + '    push 0\n    eq\n    and\n', 'herc_won', 'P4') + pending(more(zone26.MORE_BLACK_WON), 'black_won', 'P7') + pending(more(zone26.MORE_LEDGIC_WON), 'ledgic_won', 'P8') + pending(more(zone26.MORE_UUB_WON), 'uub_won', 'P9') + pending(race_won + more(zone26.MORE_RACE) + '    push 0\n    eq\n    and\n', 'race_won', 'P5') + pending(museum_done + more(zone26.MORE_MUSEUM) + '    push 0\n    eq\n    and\n', 'museum_won', 'P6') + """
    pushn 889
    call flag
    pushn 890
    call not_flag
    and
    jz L1
    push {tour_won}
    end
L1:
    pushn 888
    call flag
    pushn 887
    call not_flag
    and
    jz L2
    push {rush_won}
    end
L2:
    pushn %d
    call flag
    pushn %d
    call not_flag
    and
    jz C1
    push {cell_won}
    end
C1:
""" % (zone26.CELL_WON, zone26.CELL_PAID)
    for k in range(len(trials)):
        start += '    pushn %d\n    call flag\n    pushn %d\n    call not_flag\n    and\n    jz T%d\n    push {trial%d}\n    end\nT%d:\n' % (won(k), paid(k), k, k, k)
    allpaid = ''.join('    pushn %d\n    call flag\n%s' % (paid(k), '    and\n' if k else '') for k in range(len(trials)))
    start += allpaid + '    pushn %d\n    call not_flag\n    and\n    jz L3\n    push {all_won}\n    end\nL3:\n    push {board}\n    end\n' % zone26.TRIAL_ALL
    code('start', start)
    steps.append(('old', 'say' + old.rstrip() + '\n'))
    code('after_old', '    push {END}\n    end\n')
    say('board', "Welcome to the Challenge Board! Pick your challenge!")
    say('menu', "- Boss Rush\\n- World Tournament\\n- Trials\\n- More")
    code('menu_go', """    call 0x18
    push 0
    eq
    jz L1
    push {rush}
    end
L1:
    call 0x18
    push 1
    eq
    jz L2
    push {bracket}
    end
L2:
    call 0x18
    push 2
    eq
    jz L3
    push {trials}
    end
L3:
    call 0x18
    push 3
    eq
    jz L4
    push {more}
    end
L4:
    push {END}
    end
""")
    say('rush', "Boss Rush! Nine bosses, one health bar. Good luck!")
    code('rush_go', """    call 0x78(30)
    pushn 26, %d, 1, 120, 276
    call 0x77
    call 0x79(30)
    push {END}
    end
""" % zone26.RUSH_FIRST)
    code('bracket', '    pushn 890\n    call flag\n    jz L1\n    push {tier}\n    end\nL1:\n' + put(zone26.MORE_TIER, 0) + '    push {mode}\n    end\n')
    say('tier', "- Normal bracket\\n- Hard bracket\\n- Endless\\n- Not now")
    code('tier_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n' + put(zone26.MORE_TIER, 0) + '    push {mode}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n' + put(zone26.MORE_TIER, 1) + '    push {mode}\n    end\nL2:\n    call 0x18\n    push 2\n    eq\n    jz L3\n' + more(zone26.MORE_HARD) + '    jz L4\n    push {endless}\n    end\nL4:\n    push {locked}\n    end\nL3:\n    push {END}\n    end\n')
    say('locked', "Win the Hard bracket first and Endless opens up.")
    code('locked_go', '    push {END}\n    end\n')
    say('endless', "Endless! Fight until you fall. Every win pays more, and you keep it all.")
    code('endless_go', '    call 0x78(30)\n    push 26\n' + lad(0) + '    pushn 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n')
    steps.append(('endless_done', 'saycode 0x%02X "That run: %%d wins. Your best: %%d."\n' % speaker + lad(4) + lad(5) + '    end\n'))
    code('endless_done_go', put(zone26.MORE_ENDLESS_NEW, 0) + '    push {start}\n    end\n')
    say('hard_won', "Hard bracket cleared! 300,000 Zenie, Endless is open, and Pikkon joins you.")
    code('hard_won_go', put(zone26.MORE_HARD_PAID, 1) + put(zone26.MORE_PIKKON, 1) + '    push {start}\n    end\n')
    say('herc_won', "Hercule says he let you win, and he's joining your team to teach you more!")
    code('herc_won_go', put(zone26.MORE_HERCULE, 1) + '    push {start}\n    end\n')
    steps.append(('black_won', 'say 0x%02X "A mortal, beating a god? Very well. I will fight at your side, for now."\n' % (BLACK_PORTRAIT + 1)))
    code('black_won_go', put(zone26.MORE_BLACK, 1) + put(zone26.MORE_BLACK_WON, 0) + '    push {black_joins}\n    end\n')
    say('black_joins', "Goku Black joins you! See Switch Character.")
    code('black_joins_go', '    push {start}\n    end\n')
    say('ledgic_won', "Ledgic is down! Someone in the crowd saw the whole thing...")
    steps.append(('pan_says', 'say 0x%02X "That was amazing! I\'m coming with you too. Grandpa would want me to!"\n' % gt.portrait_id('pan')))
    code('ledgic_won_go', put(zone26.MORE_GT, 1) + put(zone26.MORE_LEDGIC_WON, 0) + '    push {gt_joins}\n    end\n')
    say('gt_joins', "Pan joins you, and the GT looks are open! See Switch Character.")
    code('gt_joins_go', '    push {start}\n    end\n')
    say('uub_won', "Uub says that was the best fight he's had. He wants to train with you!")
    code('uub_won_go', put(zone26.MORE_UUB, 1) + put(zone26.MORE_UUB_WON, 0) + '    push {uub_joins}\n    end\n')
    say('uub_joins', "Uub joins you! See Switch Character.")
    code('uub_joins_go', '    push {start}\n    end\n')
    say('race_won', "You beat the school's race record! Here's 50,000 Zenie.")
    code('race_won_go', put(zone26.MORE_RACE, 1) + '    pushn %d\n    call 0x%X\n    push {start}\n    end\n' % (zone26.RACE_PRIZE, zone26.ADD_ZENIE))
    say('museum_won', "The museum is complete, all 40 exhibits! A million Zenie and five Lazarus Crystals!")
    code('museum_won_go', put(zone26.MORE_MUSEUM, 1) + '    pushn %d\n    call 0x%X\n    pushn %d, %d\n    call 0x81\n    push {start}\n    end\n' % (zone26.MUSEUM_PRIZE, zone26.ADD_ZENIE, zone26.MUSEUM_ITEM, zone26.MUSEUM_ITEMS))
    code('rank', ''.join(lad(7) + '    push %d\n    eq\n    jz R%d\n    push {rank%d}\n    end\nR%d:\n' % (r, r, r, r) for r in (4, 3, 2)) + '    push {rank1}\n    end\n')
    for r, (letter, words) in enumerate((('C', "You made it, barely."), ('B', "A solid run."), ('A', "A fine run!"), ('S', "Barely a scratch!")), 1):
        say('rank%d' % r, "Boss Rush rank: %s! %s That's %s Zenie." % (letter, words, format(zone26.RANK_PRIZE[r - 1], ',')))
        code('rank%d_go' % r, put(zone26.MORE_RANK_NEW, 0) + '    pushn %d\n    call 0x%X\n    push {start}\n    end\n' % (zone26.RANK_PRIZE[r - 1], zone26.ADD_ZENIE))
    say('mode', "How's your bracket?\\n- Random draw\\n- Pick my opponents\\n- Not now")
    draw = ''.join('    pushn %d\n    call 0x19(%d)\n    call 0x%X\n' % (r, len(p), zone26.TOUR_PICK) for r, p in enumerate(zone26.TOUR_POOLS))
    code('mode_go', """    call 0x18
    push 0
    eq
    jz L1
""" + draw + """    push {enter}
    end
L1:
    call 0x18
    push 1
    eq
    jz L2
    push {pick0}
    end
L2:
    push {END}
    end
""")
    for r, title in enumerate(("First round. Pick your opponent!", "Second round. Who's next?", "The final! Who do you want?")):
        names = zone26.TOUR_NAMES[r]; nxt = 'pick%d' % (r + 1) if r < 2 else 'enter'
        def picks(base): return ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    pushn %d, %d\n    call 0x%X\n    push {%s}\n    end\nL%d:\n' % (v, v + 1, r, base + v, zone26.TOUR_PICK, nxt, v + 1) for v in range(3))
        say('pick%d' % r, title)
        say('a%d' % r, '\\n'.join('- ' + n for n in names[:3] + ('More',)))
        code('a%d_go' % r, picks(0) + '    call 0x18\n    push 3\n    eq\n    jz L9\n    push {b%d}\n    end\nL9:\n    push {END}\n    end\n' % r)
        say('b%d' % r, '\\n'.join('- ' + n for n in names[3:] + ('Back',)))
        code('b%d_go' % r, picks(3) + '    push {a%d}\n    end\n' % r)
    code('enter', more(zone26.MORE_TIER) + '    jz H1\n    pushn %d\n    call flag\n    jz H2\n    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\nH2:\n' % (zone26.TOUR_ORDERED, zone26.tier_first(1)) + zone26.tour_draw(0, 1) + '    push {END}\n    end\nH1:\n' + """    pushn %d
    call flag
    jz L1
    call 0x78(30)
    pushn 26, %d, 1, 360, 420
    call 0x77
    call 0x79(30)
    push {END}
    end
L1:
%s    push {END}
    end
""" % (zone26.TOUR_ORDERED, zone26.tour_first(), zone26.tour_draw(0)))
    say('trials', "Four trials, as the hero named. Zenie and gear for each, and a prize for all four!")
    say('trial_menu', '\\n'.join('- %s vs %s' % (t[1], t[4]) for t in trials))
    code('trial_go', ''.join('    call 0x18\n    push %d\n    eq\n    jz L%d\n    call 0x95(%d)\n    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\nL%d:\n' % (k, k + 1, t[0], zone26.trial_first() + k, k + 1) for k, t in enumerate(trials)) + '    push {END}\n    end\n')
    def status(name, flag, done, todo, nxt):
        code(name, '    pushn %d\n    call flag\n    jz L1\n    push {%s_done}\n    end\nL1:\n    push {%s_todo}\n    end\n' % (flag, name, name))
        say(name + '_done', done)
        code(name + '_skip', '    push {%s}\n    end\n' % nxt)
        say(name + '_todo', todo)
        code(name + '_next', '    push {%s}\n    end\n' % nxt)
    status('rewards', 887, "Boss Rush: cleared! Majin Buu, Super Janemba and Kid Buu are on your side.", "Boss Rush: win it and Majin Buu, Super Janemba and Kid Buu join you.", 'rew2')
    status('rew2', 890, "World Tournament: cleared! Each win pays 100,000 Zenie.", "World Tournament: each win pays 100,000 Zenie.", 'rew3')
    status('rew3', zone26.TRIAL_ALL, "Trials: all four cleared! You earned the Geromantium Bandana.", "Trials: Zenie and gear each. All four: Geromantium Bandana and ten Senzu Beans.", 'rew5')
    status('rew5', zone26.CELL_PAID, "Cell Games: cleared! You earned 200,000 Zenie.", "Cell Games: beat all four fights to win 200,000 Zenie.", 'rew6')
    say('rew6', "Dragon Balls: seven lie near the landing pads of seven lands. Bring them to Mr. Popo.")
    code('rew6_go', '    push {rew4}\n    end\n')
    say('rew4', "Time Chamber: Mr. Popo on Kami's Lookout lets you spar with old foes, for less EXP.")
    code('rew4_go', '    push {rew_rank}\n    end\n')
    code('rew_rank', ''.join(lad(8) + '    push %d\n    eq\n    jz R%d\n    push {best%d}\n    end\nR%d:\n' % (r, r, r, r) for r in (4, 3, 2, 1)) + '    push {best0}\n    end\n')
    for r, text in enumerate(("Boss Rush rank: not yet earned. The more health you finish with, the better.", "Boss Rush best rank: C.", "Boss Rush best rank: B.", "Boss Rush best rank: A.", "Boss Rush best rank: S!")):
        say('best%d' % r, text)
        code('best%d_go' % r, '    push {rew_ladder}\n    end\n')
    steps.append(('rew_ladder', 'saycode 0x%02X "Endless: your best run is %%d wins."\n' % speaker + lad(5) + '    end\n'))
    steps.append(('rew_museum', 'saycode 0x%02X "Museum: %%d of 25 Hercule and %%d of 15 Z-Fighter exhibits."\n' % speaker + '    pushn 341, 5\n    call 0xBA\n    pushn 346, 4\n    call 0xBA\n    end\n'))
    code('rew_museum_go', '    push {END}\n    end\n')
    say('more', "- Cell Games\\n- Rewards\\n- Challengers\\n- Back")
    code('more_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n    push {cell}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n    push {rewards}\n    end\nL2:\n    call 0x18\n    push 2\n    eq\n    jz L3\n    push {challengers}\n    end\nL3:\n    push {menu}\n    end\n')
    say('challengers', "- Hercule's dare\\n- Goku Black\\n- GT challengers\\n- Back")
    code('challengers_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n    pushn 890\n    call flag\n    jz L4\n    push {dare}\n    end\nL4:\n    push {no_dare}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n' + more(zone26.MORE_HARD) + '    jz L5\n    push {black}\n    end\nL5:\n    push {no_black}\n    end\nL2:\n    call 0x18\n    push 2\n    eq\n    jz L3\n    push {gt}\n    end\nL3:\n    push {more}\n    end\n')
    say('gt', "- Ledgic\\n- Uub\\n- Back")
    code('gt_go', '    call 0x18\n    push 0\n    eq\n    jz L1\n' + more(zone26.MORE_BLACK) + '    jz L4\n    push {ledgic}\n    end\nL4:\n    push {no_ledgic}\n    end\nL1:\n    call 0x18\n    push 1\n    eq\n    jz L2\n' + more(zone26.MORE_GT) + '    jz L5\n    push {uub}\n    end\nL5:\n    push {no_uub}\n    end\nL2:\n    push {challengers}\n    end\n')
    say('no_ledgic', "A huge caped bodyguard wants whoever beat Goku Black. Come back when that's you.")
    code('no_ledgic_go', '    push {END}\n    end\n')
    say('ledgic', "Ledgic, Don Kee's bodyguard, wants a fight. He's huge, and he hits just as hard!")
    code('ledgic_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.challenge_room('ledgic'))
    say('no_uub', "Uub is training far from here. Beat Ledgic and he may hear about you.")
    code('no_uub_go', '    push {END}\n    end\n')
    say('uub', "Uub came all this way to test himself against you. He says he's got a trick or two!")
    code('uub_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.challenge_room('uub'))
    say('no_black', "A man in a black gi is asking for the Hard bracket's champion. That's not you yet.")
    code('no_black_go', '    push {END}\n    end\n')
    steps.append(('black', 'say 0x%02X "So you are the champion. Show me how far a mortal can climb."\n' % BLACK_PORTRAIT))
    code('black_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.black_room(0))
    say('no_dare', "Hercule only fights champions. Win a tournament first!")
    code('no_dare_go', '    push {END}\n    end\n')
    say('dare', "Hercule dares you to fight him! He's sure it's a dream match. For him, that is.")
    code('dare_go', '    call 0x78(30)\n    pushn 26, %d, 1, 360, 420\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % zone26.hercule_room())
    say('cell', "The Cell Games! Four fights in a row at the old arena. Your health carries over. Good luck!")
    code('cell_go', '    pushn %d\n    call clear_flag\n    pushn %d\n    call clear_flag\n    call 0x78(30)\n    pushn 26, %d, 1, %d, %d\n    call 0x77\n    call 0x79(30)\n    push {END}\n    end\n' % (*zone26.CELL_COUNT, zone26.cell_first(), *zone26.CELL_START))
    say('cell_won', "You beat Perfect Cell! Here's 200,000 Zenie, champion!")
    code('cell_won_go', '    pushn %d\n    call set_flag\n    pushn %d\n    call 0x%X\n    push {END}\n    end\n' % (zone26.CELL_PAID, zone26.CELL_PRIZE, zone26.ADD_ZENIE))
    say('tour_won', "You won the World Tournament! 100,000 Zenie, and Yamcha wants to join you!")
    code('tour_won_go', '    pushn 890\n    call set_flag\n' + put(zone26.MORE_YAMCHA, 1) + '    push {END}\n    end\n')
    say('rush_won', "You beat all nine! Majin Buu, Super Janemba and Kid Buu join you. See Switch Character.")
    code('rush_won_go', '    pushn 887\n    call set_flag\n    push {END}\n    end\n')
    for k, t in enumerate(trials):
        say('trial%d' % k, "Well done, %s! You beat %s! Take 30,000 Zenie and the %s." % (t[1], t[4], t[6]))
        code('trial%d_go' % k, '    pushn %d\n    call set_flag\n    pushn %d\n    call 0x%X\n    call 0x93(%d)\n' % (paid(k), zone26.TRIAL_PRIZE, zone26.ADD_ZENIE, t[5]) + more(zone26.MORE_TIEN) + '    jz L1\n    push {END}\n    end\nL1:\n    push {tien}\n    end\n')
    say('tien', "Tien saw that fight, and he'd like to join you. See Switch Character.")
    code('tien_go', put(zone26.MORE_TIEN, 1) + '    push {END}\n    end\n')
    say('all_won', "All four trials cleared! Take this Geromantium Bandana and ten Senzu Beans.")
    code('all_won_go', '    pushn %d\n    call set_flag\n    pushn %d, %d\n    call 0x81\n    call 0x93(%d)\n    push {END}\n    end\n' % (zone26.TRIAL_ALL, zone26.TRIAL_ITEM, zone26.TRIAL_ITEMS, zone26.TRIAL_GEAR))
    code('last', '    end\n')
    for name, text in steps:
        for m in re.finditer(r'say(?:code)? 0x\w+ "([^"]*)"', text):
            n = len(m.group(1).replace('\\n', ' ')); assert n < 100 and not 64 <= n <= 67, m.group(1)
    number = {n: k for k, (n, _) in enumerate(steps)}; number['END'] = len(steps)
    return head + ''.join('step auto %s' % re.sub(r'\{(\w+)\}', lambda m: str(number[m.group(1)]), t) for _, t in steps)


def debug_edits(first_form):
    """Join Vegito and guest Broly at the start, and open the picker, then save, when the intro ends."""
    heal = ''.join('    push %d\n    set %s\n' % (v, n) for v, n in ((500, 'max_hp'), (500, 'hp'), (100, 'max_ki'), (100, 'ki')))
    import zone26
    flags = ''.join('    pushn %d\n    call set_flag\n' % f for f in sorted({o['flag'] for l in json.load(open('ultimate/outfits.json'))['characters'].values() for o in l if o['flag'] and o['flag'] < zone26.MORE_FLAG}))
    flags += ''.join('    pushn %d\n    call set_flag\n' % u['flag'] for u in json.load(open('ultimate/outfits.json'))['unlocks'] if u['flag'] >= SS2_FLAG)
    if '--zone' in sys.argv: flags += '    pushn 149\n    call set_flag\n    pushn 0, 19\n    call 0xA4\n'
    join = ('step auto code\n' + flags + '    call 0x97(1)\n    call 0x97(3)\n    call 0x97(4)\n    call 0x97(6)\n    call 0x97(8)\n    call 0x95(3)\n' + heal + '    call 0xD0(21)\n    call 0x95(4)\n' + heal + '    call 0xD0(26)\n    call 0x95(1)\n' + heal + '    call 0xD0(15)\n    pushn 1, 107\n    call 0x9D\n    call 0xA4(1, 18)\n    call 0xA4(1, %d)\n' % BEAM_SKILL + '    call 0x95(6)\n' + heal + '    call 0x95(8)\n' + heal + '    pushn 8, 8\n    call 0xA4\n    pushn 8, %d\n    call 0xA4\n' % ERASER_SKILL +
            '    call 0xD0(%d)\n    call 0x95(0)\n    end\n' % first_form)
    s = open(INTRO).read()
    assert 'step 19 raw' in s
    open(INTRO, 'w').write(s.replace('step 19 raw', join + 'step 19 raw', 1))
    if '--zone' in sys.argv:                             # the debug door to the ending starts from its last scene
        e = open(ENDING).read()
        e, n = re.subn(r'(?m)^(step 1 z?code[^\n]*\n)', r'\1    push 66\n    end\n', e, 1)
        if n != 1: sys.exit('ending step 1 is not code')
        open(ENDING, 'w').write(e)
    if '--enemy' in sys.argv:
        open(ACTORS_FILE, 'a').write('enemy 8 0x70 0xB0 34   ; debug: a Bomber to test attacks on\n')
    s = open(FIELD).read()
    zone = '--zone' in sys.argv
    tail = '    set 0x10\n    end\n'
    i = s.rfind(tail)
    assert i > 0
    open(FIELD, 'w').write(s[:i] + (tail if zone else '    set 0x10\n    call 0x8D\n    call 0x%X\n    end\n' % DEBUG_NATIVE) + s[i + len(tail):])


def unlock_edits():
    """Set each outfit's unlock flag where the story first gives that outfit."""
    cfg = json.load(open('ultimate/outfits.json'))
    touched = {}
    for u in cfg['unlocks']:
        p = 'assets/scripts/%s.evt' % u['list']
        s = open(p).read()
        touched.setdefault(p, s)
        site = u.get('after', u.get('find'))
        if site not in s:
            sys.exit('unlock site not found in ' + p)
        flag = '    pushn %d\n    call set_flag\n' % u['flag']
        open(p, 'w').write(s.replace(site, site + flag if 'after' in u else flag + site, 1))
    return touched


def unlock_edits_paths():
    cfg = json.load(open('ultimate/outfits.json'))
    return {'assets/scripts/%s.evt' % u['list']: open('assets/scripts/%s.evt' % u['list']).read() for u in cfg['unlocks']}


def save_stub(addr):
    """Thumb native: sub_08004962(&G, the slot being played, position, 0), the game's full save call."""
    src = """.syntax unified
.thumb
push {r4, lr}
sub sp, #8
ldr r0, =0x03001068
ldr r1, =0x03001910
ldrb r1, [r1]
movs r2, #0
str r2, [sp]
movs r2, #120
str r2, [sp, #4]
mov r2, sp
movs r3, #0
ldr r4, =0x08004963
bl 1f
add sp, #8
pop {r4}
pop {r0}
bx r0
1: bx r4
.ltorg
"""
    d = tempfile.mkdtemp()
    open(d + '/s.s', 'w').write(src)
    subprocess.run(['arm-none-eabi-as', '-mthumb', '-mcpu=arm7tdmi', d + '/s.s', '-o', d + '/s.o'], check=True)
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', d + '/s.o', d + '/s.bin'], check=True)
    return open(d + '/s.bin', 'rb').read()


def find_once(rom, needle, what):
    i = rom.find(needle)
    if i < 0 or rom.find(needle, i + 1) >= 0:
        sys.exit('%s: expected exactly one match' % what)
    return i


ANDROID13_SLOTS = {str(s): 'a13_idle' for s in range(22)}
ANDROID13_SLOTS.update({'10': 'a13_absorb!front', '1': 'a13_walk', '2': 'a13_walk', '4': 'a13_lunge', '5': 'a13_lunge', '6': 'a13_lunge', '9': 'a13_lunge', '18': 'a13_lunge', '19': 'a13_lunge', '20': 'a13_lunge', '21': 'a13_lunge'})


def android13_frames(out, usable, pal):
    """Cut the walk sheet into 32x32 indexed cells (cap version), dropping the shadow drawn into each frame: the game adds its own."""
    from PIL import Image
    sheet = np.array(Image.open('ultimate/art/android13_sheet.png').convert('RGB')).astype(int)
    bg = sheet[0, 0]
    cols, rows = ((75, 93), (99, 117), (123, 141)), ((1, 32), (33, 64), (66, 96), (97, 128))
    u = np.array(usable); p = pal[u].astype(int)
    def cell(r, c):
        (y0, y1), (x0, x1) = rows[r], cols[c]
        a = sheet[y0:y1, x0 - 1:x1 + 1]; m = (a != bg).any(2)
        black = (a.sum(2) == 0)
        foot = m.shape[0] - 5                               # the shadow: pure black in the bottom rows
        m[foot:][black[foot:]] = False
        ys = np.nonzero(m.any(1))[0]; h = ys[-1] + 1
        img = np.zeros((32, 32), np.uint8); w = a.shape[1]; ox = (32 - w) // 2; oy = 32 - h
        for y in range(h):
            for x in range(w):
                if m[y, x]:
                    q = a[y, x]; ch = lambda v: np.stack([v[..., 0] - v[..., 1], v[..., 1] - v[..., 2]], -1)
                    d = ((p - q) ** 2).sum(1) + 6 * ((ch(p) - ch(q)) ** 2).sum(1)
                    img[y + oy, x + ox] = u[d.argmin()]
        return img
    DOWN, UP, RIGHT = 2, 0, 3                               # the engine's side frames face left, so that's the row it wants
    def save(name, frames):
        for i, f in enumerate(frames):
            Image.fromarray(f).save('%s/%s_%02d.png' % (out, name, i))
    save('a13_idle', [cell(d, 1) for d in (DOWN, UP, RIGHT)])
    save('a13_walk', [cell(d, c) for d in (DOWN, UP, RIGHT) for c in (1, 0, 1, 2)])
    save('a13_lunge', [cell(d, c) for d in (DOWN, UP, RIGHT) for c in (0, 2)])
    for i in range(6):                                      # absorbing 14's and 15's cores: the owner's sheet as cleaned for Gero's Legacy, already in the game's OBJ colours
        Image.fromarray(np.array(Image.open('ultimate/art/android13_absorb/a%d.png' % i))).save('%s/a13_absorb_%02d.png' % (out, i))


# Broly Full Power: made by Azure-Oni, ripped by DBZdogs. Frames as (x0, x1) on the down, up and side rows.
BROLY_FRAMES = {
    'idle': (((0, 46),), ((0, 46),), ((0, 27),)),
    'walk': (((94, 140), (158, 199), (225, 266), (287, 333)), ((93, 133), (153, 199), (218, 264), (289, 329)), ((98, 123), (142, 168), (172, 200), (205, 231))),
    'combo': (((347, 390), (406, 455), (478, 514)), ((349, 396), (410, 460), (462, 506)), ((327, 366), (372, 422), (444, 494))),
    'slam': (((600, 662), (665, 721)), ((585, 647), (658, 721)), ((599, 632), (647, 702))),
    'strike': (((756, 804), (817, 858)), ((754, 801), (816, 857)), ((750, 788), (822, 871))),
}
BROLY_SLOTS = {str(s): 'bfp_idle' for s in range(22)}
BROLY_SLOTS.update({'1': 'bfp_walk', '2': 'bfp_walk', '4': 'bfp_combo', '5': 'bfp_strike', '6': 'bfp_slam', '8': 'bfp_slam', '9': 'bfp_strike', '10': 'bfp_slam', '13': 'bfp_slam', '14': 'bfp_strike', '20': 'bfp_strike', '21': 'bfp_slam'})


def indexer(usable, pal):
    """RGB to the game's OBJ palette, with colour shifts weighted so neutrals don't land on tints."""
    u = np.array(usable); p = pal[u].astype(int); cache = {}
    def ch(v): return np.stack([v[..., 0] - v[..., 1], v[..., 1] - v[..., 2]], -1)
    def one(q):
        q = np.asarray(q, dtype=int)         # a uint8 colour would wrap in the differences below
        k = tuple(int(v) for v in q)
        if k not in cache:
            d = ((p - q) ** 2).sum(1) + 6 * ((ch(p) - ch(q)) ** 2).sum(1)
            cache[k] = int(u[d.argmin()])
        return cache[k]
    return one


def broly_frames(out, usable, pal):
    from PIL import Image
    sheet = np.array(Image.open('ultimate/art/broly_full_power_sheet.png').convert('RGB')).astype(int)
    bg = sheet[0, 0]; one = indexer(usable, pal)
    fg = (sheet[:232] != bg).any(2)
    def cell(row, x0, x1):
        # this frame's rows: the row-th block of ink in its own columns (the sheet's rows aren't level)
        ink = fg[:, x0:x1 + 1].any(1); ys = np.nonzero(ink)[0]
        blocks = np.split(ys, np.nonzero(np.diff(ys) > 2)[0] + 1)
        blocks = [k for k in blocks if len(k) > 20]
        y0, y1 = blocks[row][0], blocks[row][-1] + 1
        a = sheet[y0:y1, x0:x1 + 1]; m = fg[y0:y1, x0:x1 + 1]
        h, w = m.shape
        if h > 64 or w > 64: sys.exit('Broly frame %dx%d is over the 64x64 sprite limit' % (w, h))
        img = np.zeros((64, 64), np.uint8)
        for y, x in zip(*np.nonzero(m)):
            img[64 - h + y, (64 - w) // 2 + x] = one(a[y, x])
        return img
    for name, rows in BROLY_FRAMES.items():
        n = 0
        for row, spans in enumerate(rows):
            for x0, x1 in spans:
                c = cell(row, x0, x1)
                if row == 2: c = c[:, ::-1]        # the sheet's side views face the way this game's don't
                Image.fromarray(c).save('%s/bfp_%s_%02d.png' % (out, name, n)); n += 1


def player_anim_lengths(clean):
    """Longest animation per slot across the retail player forms. Skills pick a frame by number, assuming a player's animation is as long as these, and
    past the end of a shorter one they read garbage as a frame (that is how Super 13's three-frame slot 19 crashed the Ghost Attack)."""
    u = lambda o: struct.unpack_from('<I', clean, o)[0]
    table = sprites.ACTOR_LIST; out = {}
    for f in range(FORM_COUNT):
        char = struct.unpack_from('<H', clean, FORMS + FORM_SIZE * f + 0x0E)[0]
        if char < 9: continue
        rec = u(table + 4 * (char - 9)) - ROM_BASE
        for s in range(u(rec) & 0xFF):
            a = u(rec + 0x54 + 4 * s)
            if a: out[s] = max(out.get(s, 0), u(a - ROM_BASE))
    return out


def add_actors(rom, clean):
    combo = open(COMBO, 'rb').read()
    if hashlib.sha1(combo).hexdigest() != COMBO_SHA1:
        sys.exit('%s is not the Legacy of Goku I & II (USA) cart (SHA-1 mismatch); set BFU_COMBO.' % COMBO)
    cfg = json.load(open('ultimate/actors.json'))
    slots = cfg.pop('_slots')
    for k, a in cfg.items():
        if not k.startswith('_') and 'replace' not in a and 'log2_record' in a: a['log2_slots'] = {k: v for k, v in slots.items() if int(k) not in a.get('keep_own', ())}
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    usable = [i for i in range(1, 256) if i not in artclean.MENU_SLOTS]
    cfg['super13'] = {'proto_actor': 230}
    clean_dir = tempfile.mkdtemp()
    android13_frames(clean_dir, usable, pal)
    cfg['android13'] = {'template': 157, 'slots': ANDROID13_SLOTS}
    broly_frames(clean_dir, usable, pal)
    cfg['broly_fp'] = {'template': 29, 'slots': BROLY_SLOTS, 'big': True, 'stretch': True}
    one = indexer(usable, pal); lengths = player_anim_lengths(clean)
    cfg['broly_fp']['grow'] = lengths
    for actor, form in (('gogeta_dbs', 'base'), ('gogeta_dbs_ss', 'ssj'), ('gogeta_ssb', 'ssb')):
        gogeta.write_frames(clean_dir, form, one)
        cfg[actor] = {'template': 93, 'slots': gogeta.slots(form), 'stretch': True, 'grow': lengths}
    for name in ('piccolo', 'android17', 'android18', 'krillin', 'future_trunks', 'future_trunks_ss', 'videl_player', 'kid_buu_player', 'majin_buu_player', 'super_janemba_player', 'tien_player', 'yamcha_player', 'pikkon_player', 'hercule_player'):
        cfg[name]['grow'] = lengths
    for a in cfg.values():      # slot 18 is the pose held while firing a skill: LoG2's own firing pose when it has one, else its ki pose
        if isinstance(a, dict) and 'log2_record' in a and 'replace' not in a:
            rec = sprites.log2_rec(combo[0x800000:], a['log2_record'])
            has = struct.unpack_from('<I', combo, 0x800000 + rec + 0x4C + 16 * 18 + 8)[0]
            a.setdefault('log2_overrides', {}).setdefault('18', 18 if 0x08800000 <= has < 0x09000000 else 5)
    cfg['android13_player'] = {'template': 93, 'slots': ANDROID13_SLOTS, 'stretch': True, 'grow': lengths, 'reserve': 4096}    # the boss's small record can't carry a playable form
    cfg['super13_player'] = {'proto_actor': 230, 'stance_back': True, 'fill': {8: 9, 10: 9, 11: 0, 12: 0, 13: 9, 14: 4, 15: 7, 16: 17}, 'grow': lengths}
    bright = (one(np.array((96, 248, 248))), one(np.array((200, 248, 248))))     # cyan: Super Saiyan 2's lightning
    for name, source in (('goku_ss2', 109), ('goku_ss2_b', 110), ('gohan_ss2', 104), ('gohan_green_ss2', 105), ('vegeta_ss2', 273), ('vegeta_ss2_b', 274), ('vegeta_armor_ss2', 'vegeta_armor_ss'), ('gohan_armor_ss2', 'gohan_armor_ss2_art'), ('trunks_ss2', 261), ('trunks_armor_ss2', 'trunks_armor_ss'), ('vegito_ss2', 276)):
        cfg[name] = {'bolts_of': source, 'bolt_colours': bright}
    cfg['android17']['reserve'] = 2048                  # the same as Super 17's: a change of size on transforming re-allocates OBJ memory and scrambled other sprites
    cfg['super17'] = {**cfg['android17'], 'size_scale': [1.12, 1.1], 'reserve': 2048}     # slightly taller and bulkier, as in Gero's Legacy
    cfg['android13_absorb'] = {'template': 152, 'slots': {'0': 'a13_absorb!front', '1': 'a13_absorb!front'}}     # a cutscene figure: only an idle animation plays by itself, as in Gero's Legacy
    for name, rec in (('cell_imperfect', 'r25'), ('cell_semi', 'r26'), ('cell_perfect', 'r27'), ('cell_junior', 'r28')):      # LoG2's own sprites, whole: 64x64 like the prototype's Super 13 (the Juniors are smaller)
        cfg[name] = {'template': 38, 'stretch': True, 'reserve': 1024 if name == 'cell_junior' else 4096, 'log2_record': rec,
                     'log2_slots': {**{str(k): 0 for k in range(22)}, '1': 1, '2': 1, '4': 6, '5': 7, '6': 7, '7': '3@0:1' if name != 'cell_junior' else '2@0:1', '8': 5, '9': 5, '10': 5, '13': 5, '14': 6, '15': 2, '16': 3 if name != 'cell_junior' else 2, '17': 3 if name != 'cell_junior' else 2, '18': 5, '19': 5, '20': 6, '21': 5}}
    for k in range(7):                                   # the game's own item icons, as things you can walk up to
        p = symbol_items_icon(16 + k)
        t, size = struct.unpack_from('<II', clean, p); icon = np.frombuffer(bytes(wfz.decompress_stream(clean, p + 8, size)[0]), np.uint8).reshape(16, 16)
        cfg['dragon_ball_%d' % (k + 1)] = {'template': 152, 'raw_frames': {str(sl): [[icon], [icon], [icon]] for sl in (0, 1)}}
    looks, _ = goku_black.build(clean, one)      # Goku Black and Rose: every frame of Goku and Super Saiyan Goku, from the owner's sheet or in its colours
    cfg['goku_black'] = {'template': goku_black.SOURCE['black'], 'raw_frames': {str(k): v for k, v in looks['black'].items()}}
    cfg['goku_rose'] = {'template': goku_black.SOURCE['rose'], 'raw_frames': {str(k): v for k, v in looks['rose'].items()}}
    cfg.update(gt.actors(clean, pal, lengths))      # GT: Black Star Odyssey's fighters (bso_import.py; BFU_BSO points at the owner's sheet)
    cfg['_powerup'] = [101, 104, 105, 273, 274, 261, 276, 'vegeta_armor_ss', 'gohan_armor_ss', 'trunks_armor_ss']
    ids, end = sprites.build_actors(rom, cfg, clean_dir, ACTORS_AT, combo[0x800000:], lambda act: (usable, pal), open(PROTO, 'rb').read())
    return ids, end


def patch_forms(rom, clean, cfg, actors):
    old = find_once(rom, clean[FORMS:FORMS + FORM_SIZE * FORM_COUNT], 'form table')
    rows = bytearray(rom[old:old + FORM_SIZE * FORM_COUNT])
    index = {}
    ids = {r['id']: k for k, r in enumerate(cfg['rows'])}
    for k, r in enumerate(cfg['rows']):
        row = bytearray(rows[FORM_SIZE * r['copy']:FORM_SIZE * (r['copy'] + 1)])
        if 'name' in r:
            struct.pack_into('<HH', row, 2, r['name'], r.get('status_name', r['name']))
        row[0x0C] = r['owner']
        struct.pack_into('<H', row, 0x0E, actors[r['actor']] + 9 if 'actor' in r else r['character'])
        if 'portrait' in r:                                 # one speaker id, or the six expressions; "gt:<name>" a GT portrait
            ps = r['portrait'] if isinstance(r['portrait'], list) else [r['portrait']] * 6
            row[0x10:0x16] = bytes(gt.portrait_id(v[3:]) if isinstance(v, str) else v for v in ps)
        for off, key in ((0x16, 'up'), (0x17, 'down')):
            v = r.get(key, 255)
            row[off] = v if isinstance(v, int) else FORM_COUNT + ids[v]
        if 'flags' in r:
            struct.pack_into('<H', row, 0, r['flags'])
            if r['flags'] & 1: struct.pack_into('<I', row, 8, 0x03001B78)     # the Super Saiyan behaviour object: a guest's row was copied from a form without it
        rows += row
        index[r['id']] = FORM_COUNT + k
    for k, e in cfg.get('edit', {}).items():
        o = FORM_SIZE * int(k)
        if 'up' in e: rows[o + 0x16] = index[e['up']]
        if 'down' in e: rows[o + 0x17] = index[e['down']]
    for f in range(len(rows) // FORM_SIZE):                 # a form that can transform needs slot 10 (see sprites.py)
        up, char = rows[FORM_SIZE * f + 0x16], struct.unpack_from('<H', rows, FORM_SIZE * f + 0x0E)[0]
        if up != 255 and char >= 9:
            rec = struct.unpack_from('<I', rom, ACTORS_AT + 4 * (char - 9))[0] - ROM_BASE
            if struct.unpack_from('<I', rom, rec)[0] & 0xFF <= 10 or not struct.unpack_from('<I', rom, rec + 0x54 + 40)[0]:
                sys.exit('form %d can transform but its actor has no slot 10' % f)
    for f in range(len(rows) // FORM_SIZE):                 # changing back plays slot 11, and an empty one draws junk from address 0 over other sprites' tiles: a short stance instead
        char = struct.unpack_from('<H', rows, FORM_SIZE * f + 0x0E)[0]
        if rows[FORM_SIZE * f] & 1 and rows[FORM_SIZE * f + 0x17] != 255 and char >= 9:
            rec = struct.unpack_from('<I', rom, ACTORS_AT + 4 * (char - 9))[0] - ROM_BASE
            if rom[rec] <= 11:
                sys.exit('form %d changes back but its actor has no slot 11' % f)
            if not struct.unpack_from('<I', rom, rec + 0x54 + 44)[0]:
                print('form %d: slot 11 was empty' % f)
                struct.pack_into('<I', rom, rec + 0x54 + 44, struct.unpack_from('<I', rom, rec + 0x54)[0])
    if len(rows) // FORM_SIZE > 255:
        sys.exit('too many forms: 255 is the "none" marker')
    rom[SPACE:SPACE + len(rows)] = rows
    n = 0
    for o in range(0, CODE_END, 4):
        if struct.unpack_from('<I', rom, o)[0] == ROM_BASE + old:
            struct.pack_into('<I', rom, o, ROM_BASE + SPACE)
            n += 1
    if n != 37:
        sys.exit('form table: expected 37 code references, found %d' % n)
    return index, SPACE + len(rows)


def symbol(name):
    out = subprocess.run(['arm-none-eabi-nm', 'buusfury_modern.elf'], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        p = line.split()
        if p[-1] == name:
            return int(p[0], 16)
    sys.exit('symbol %s not found' % name)


BENCH_OLD = ('broly', 'broly_fp', 'android13', 'piccolo', 'future_trunks', 'android17', 'android18', 'krillin', 'videl', 'majin_buu', 'super_janemba', 'kid_buu', 'tien', 'yamcha', 'pikkon', 'hercule')
BENCH_GROUPS = 21                # outfit.c's GROUPS: fighters the save can keep progress for


def bench_groups(guests):
    """Each guest outfit's bench group (outfit.c bench_group): the fighters saves already hold keep their groups (Full Power is Broly's), and new ones take the next."""
    names = [o['form'] for o in guests]
    if tuple(names[:len(BENCH_OLD)]) != BENCH_OLD:
        sys.exit('guest list changed: older saves keep progress by this order; add new guests at the end')
    out = [0, 0] + list(range(1, len(BENCH_OLD) - 1)); shared = {}
    for o in guests[len(BENCH_OLD):]:               # new guests take the next groups; looks of one fighter ("bench") share theirs
        key = o.get('bench', o['form'])
        if key not in shared: shared[key] = max(out) + 1
        out.append(shared[key])
    if max(out) >= BENCH_GROUPS:
        sys.exit('more guests than the save has room for (%d)' % BENCH_GROUPS)
    src = open('ultimate/src/outfit.c').read(); body = src[src.index('static void guest_sync'):]; body = body[:body.index('u8 *r =')]
    for name, count in re.findall(r'(\w+)\[\] = \{(\d+),', body):
        if int(count) > 5:
            sys.exit('%s has %s moves: the bench keeps five skill levels' % (name, count))
    return out


def add_outfits(rom, clean, at, art):
    """Compile the outfit code with its table at `at`, then point the Switch Character screen's vtable at it."""
    cfg = json.load(open('ultimate/outfits.json'))['characters']
    index, table = [], []
    fm = json.load(open(OUT + '/_forms.json'))
    for c in range(9):
        lst = cfg.get(str(c), [])
        index.append('{%d,%d}' % (len(table), len(lst)))
        form = lambda v: v if isinstance(v, int) else fm[v]
        table += ['{%d,%d,%d,(const u16 *)L"%s"}' % (form(o['form']), form(o.get('also', 255)), o['flag'], o['name']) for o in lst]
    d = tempfile.mkdtemp()
    pairs = ['{%d,%d}' % (base if isinstance(base, int) else fm[base], 14 if row == 14 else fm[row]) for base, row in SAIYAMAN]
    c = open('ultimate/src/outfit.c').read() + '\nconst u16 outfit_index[9][2] = {%s};\nconst struct outfit outfit_table[] = {%s};\nconst u8 saiyaman_map[][2] = {%s};\nconst int saiyaman_count = %d;\nconst u8 ss2_rows[] = {%s,255};\nconst u8 ssj4_rows[] = {%s,255};\n' % (','.join(index), ','.join(table) or '{0,0,0,0}', ','.join(pairs), len(pairs), ','.join(str(v) for k, v in fm.items() if k.endswith(('_ss2', '_ss2_b')) or k in SS2_LIKE), ','.join(str(v) for k, v in fm.items() if k.endswith('ssj4')))
    open(d + '/o.c', 'w').write(c)
    import zone26
    groups = bench_groups(cfg['8'])
    flags = ['-mthumb', '-mcpu=arm7tdmi', '-O2', '-ffreestanding', '-fno-builtin', '-nostdlib', '-fshort-wchar', '-DHEAP_WORDS=0x%X' % HEAP_WORDS, '-DERASER_SKILL=%d' % ERASER_SKILL, '-DBOMBER_SKILL=%d' % BOMBER_SKILL, '-DBEAM_SKILL=%d' % BEAM_SKILL, '-DWAVE_SKILL=%d' % WAVE_SKILL, '-DSUPER13_SKILL=%d' % SUPER13_SKILL, '-DSUPER17_SKILL=%d' % SUPER17_SKILL, '-DBLITZ_SKILL=%d' % BLITZ_SKILL, '-DFORM_KID_BUU=%d' % fm['kid_buu'], '-DFORM_MAJIN_BUU=%d' % fm['majin_buu'], '-DFORM_JANEMBA=%d' % fm['super_janemba'], '-DDISC_SKILL=%d' % DISC_SKILL, '-DFORM_ANDROID17=%d' % fm['android17'], '-DFORM_ANDROID18=%d' % fm['android18'], '-DFORM_KRILLIN=%d' % fm['krillin'], '-DFORM_VIDEL=%d' % fm['videl'], *(['-DDEBUG_OPEN'] if '--debug' in sys.argv else []), '-DTIER_ROOMS=%s' % zone26.tier_rooms(), '-DENDLESS_STEP=%d' % zone26.ENDLESS_STEP, '-DENDLESS_CAP=%d' % zone26.ENDLESS_CAP, '-DFORM_TIEN=%d' % fm['tien'], '-DFORM_BLACK=%d' % fm['goku_black'], '-DFORM_ROSE=%d' % fm['goku_rose'], '-DFORM_PAN=%d' % fm['pan'], '-DFORM_PAN_LAST=%d' % fm['pan_brapan'], '-DFORM_UUB=%d' % fm['uub'], '-DFORM_MAJUUB=%d' % fm['majuub'], '-DMAJUUB_SKILL=%d' % MAJUUB_SKILL, '-DROSE_SKILL=%d' % ROSE_SKILL, '-DBLACK_KAME_SKILL=%d' % BLACK_KAME_SKILL, '-DBENCH_GROUP_LIST=%s' % ','.join(map(str, groups)), '-DFORM_YAMCHA=%d' % fm['yamcha'], '-DFORM_PIKKON=%d' % fm['pikkon'], '-DFORM_HERCULE=%d' % fm['hercule'], '-DFORM_FUTURE_TRUNKS=%d' % fm['future_trunks'], '-DSS2_FLAG=%d' % SS2_FLAG, '-DTOUR_PICK_FLAG=%d' % zone26.TOUR_PICKS, '-DFORM_BROLY=%d' % fm['broly'], '-DFORM_FP=%d' % fm['broly_fp'], '-DFORM_PICCOLO=%d' % fm['piccolo'], '-DFORM_A13=%d' % fm['android13'], '-DBALL_AREAS={%s}' % ','.join(str(b[1] << 8 | b[0]) for b in zone26.BALLS), '-DFORM_S13=%d' % fm['super13'], '-DFORM_S17=%d' % fm['super17'], '-DSOUND_MOVE=0x%X' % symbol('gUnknown_0831947C'), '-DFONT=0x%X' % symbol('gUnknown_0807012C'), '-DMELEE_RECTS=0x083C344C', '-DSOUND_HIT=0x%X' % symbol('gUnknown_083192A8')]
    syms = ['-Wl,--defsym=form_table=0x%X' % (ROM_BASE + SPACE), '-Wl,-Ttext=0x%X' % (ROM_BASE + at), '-Wl,-e,picker_update', '-Wl,--no-warn-rwx-segments']
    lib = subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mcpu=arm7tdmi', '-print-libgcc-file-name'], capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(['arm-none-eabi-gcc'] + flags + syms + [d + '/o.c', lib, '-o', d + '/o.elf'], check=True)
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', d + '/o.elf', d + '/o.bin'], check=True)
    code = open(d + '/o.bin', 'rb').read()
    nm = subprocess.run(['arm-none-eabi-nm', d + '/o.elf'], capture_output=True, text=True, check=True).stdout
    sym = {l.split()[2]: int(l.split()[0], 16) for l in nm.splitlines() if len(l.split()) == 3}
    if set(rom[at:at + len(code)]) != {0xFF}:
        sys.exit('outfit code space is not free')
    rom[at:at + len(code)] = code
    vt = symbol('_0804A5E0') - ROM_BASE
    for slot, want, name in ((5, 0x0802EBA5, 'picker_update'), (8, 0x0802ECEB, 'picker_input')):
        if ROM_BASE + vt + struct.unpack_from('<i', rom, vt + 4 * slot)[0] != want:
            sys.exit('vtable slot %d changed' % slot)
        struct.pack_into('<i', rom, vt + 4 * slot, (sym[name] | 1) - (ROM_BASE + vt))
    for vt, want, name in ((0x4C384, 0x08012D8B, 'state_a'), (0x4BEF0, 0x08012DEF, 'state_b'), (0x4C790, 0x08013023, 'state_c'), (0x4C3A8, 0x080131BB, 'state_d')):
        if ROM_BASE + vt + struct.unpack_from('<i', rom, vt + 8)[0] != want:
            sys.exit('state vtable changed at 0x%X' % vt)
        struct.pack_into('<i', rom, vt + 8, (sym[name] | 1) - (ROM_BASE + vt))
    if rom[0x3C344C:0x3C348C] != clean[0x3C344C:0x3C348C]:
        sys.exit('melee rectangles moved')
    IN, OUT_SITE = 0x1C5F2, 0x1C2D2
    if rom[IN:IN + 10] != bytes.fromhex('0e202875301cff305130') or rom[OUT_SITE:OUT_SITE + 8] != bytes.fromhex('0a202875301cf030'):
        sys.exit('Great Saiyaman code changed')
    rom[IN:IN + 10] = bytes.fromhex('0149fe460847') + struct.pack('<I', sym['saiyaman_hook_in'] | 1)
    rom[OUT_SITE:OUT_SITE + 12] = bytes.fromhex('0149fe460847') + struct.pack('<I', sym['saiyaman_hook_out'] | 1) + bytes.fromhex('c046')
    patch_slot_read(rom, sym)
    vt = sym['spirit_vt'] - ROM_BASE                      # 0 delete, 2 update every frame, others do nothing
    for k, name in enumerate(('spirit_destroyed', 'spirit_nop', 'spirit_update', 'spirit_nop', 'spirit_nop', 'spirit_nop')):
        struct.pack_into('<i', rom, vt + 4 * k, (sym[name] | 1) - (ROM_BASE + vt))
    tab = find_once(rom, clean[NATIVES:NATIVES + 64], 'native table')
    if struct.unpack_from('<I', rom, tab + 4 * JOIN_NATIVE)[0] != JOIN_OLD:
        sys.exit('native 0x%X changed' % JOIN_NATIVE)
    struct.pack_into('<I', rom, tab + 4 * JOIN_NATIVE, sym['party_join'] | 1)
    struct.pack_into('<I', rom, tab + 4 * 0xE0, sym['add_zenie'] | 1)
    struct.pack_into('<I', rom, tab + 4 * zone26.MORE_GET, sym['more_get'] | 1)
    struct.pack_into('<I', rom, tab + 4 * zone26.LADDER, sym['ladder'] | 1)
    struct.pack_into('<I', rom, tab + 4 * zone26.MORE_PUT, sym['more_put'] | 1)
    struct.pack_into('<I', rom, tab + 4 * 0xE5, sym['bomb_fx'] | 1)
    struct.pack_into('<I', rom, tab + 4 * zone26.BALL_NATIVE, sym['ball_here'] | 1)
    struct.pack_into('<I', rom, tab + 4 * zone26.WISH_NATIVE, sym['wish_power'] | 1)
    struct.pack_into('<I', rom, tab + 4 * 0xE6, sym['bomb_at'] | 1)
    import zone26
    struct.pack_into('<I', rom, tab + 4 * zone26.TOUR_PICK, sym['tour_pick'] | 1)
    struct.pack_into('<I', rom, tab + 4 * zone26.TOUR_GET, sym['tour_get'] | 1)
    if '--trailer' in sys.argv: struct.pack_into('<I', rom, tab + 4 * 0xE3, sym['trailer_warp'] | 1)
    if '--trailer' in sys.argv: struct.pack_into('<I', rom, tab + 4 * 0xE4, sym['trailer_slot'] | 1)
    row = SKILLS + 24 * SUPER_BLUE_SKILL                  # Super Saiyan 3's code runs on the form table's up and down, so only the words change
    if struct.unpack_from('<II', rom, row + 4) != (0x08019D25, 0x08019D29):
        sys.exit('skill row %d is in use' % SUPER_BLUE_SKILL)
    rom[row:row + 24] = rom[SKILLS + 24 * 22:SKILLS + 24 * 23]
    struct.pack_into('<HH', rom, row, 1057, 1051)
    row = SKILLS + 24 * SPIRIT_SKILL                     # an unused skill row: its stubs become the Spirit Bomb
    if struct.unpack_from('<II', rom, row + 4) != (0x08019D25, 0x08019D29):
        sys.exit('skill row %d is in use' % SPIRIT_SKILL)
    struct.pack_into('<HHII', rom, row, SPIRIT_NAME, SPIRIT_NAME + 3, sym['spirit_usable'] | 1, sym['spirit_use'] | 1)
    rom[row + 12:row + 24] = rom[SKILLS + 24 * 15 + 12:SKILLS + 24 * 15 + 24]
    row = SKILLS + 24 * 20                               # Super Saiyan's use goes up to Super Saiyan 2 where a form has one; Super Saiyan 3 waits for it
    if struct.unpack_from('<I', rom, row + 8)[0] != 0x0801A513 or struct.unpack_from('<I', rom, SKILLS + 24 * 22 + 4)[0] != 0x0801A55F:
        sys.exit('Super Saiyan skill rows changed')
    struct.pack_into('<I', rom, row + 8, sym['ss_use'] | 1)
    struct.pack_into('<I', rom, SKILLS + 24 * 22 + 4, sym['ss3_can'] | 1)
    if struct.unpack_from('<I', rom, SKILLS + 24 * 22 + 8)[0] != 0x0801A5BD: sys.exit('Super Saiyan 3 use changed')
    struct.pack_into('<I', rom, SKILLS + 24 * 22 + 8, sym['ss3_use'] | 1)       # Kid Goku: Super Saiyan 3 pressed again goes on to Super Saiyan 4
    # The flag array runs into other bit arrays: map rooms visited at G+0x8D (flag 448 up) and Scouter entries at G+0xC5 . Custom flags live in their gaps: see zone26.py.
    rooms = max(struct.unpack_from('<H', rom, struct.unpack_from('<I', rom, struct.unpack_from('<I', rom, 0x74C948 + 4 * w)[0] - ROM_BASE + 0x18 + 4 * i)[0] - ROM_BASE + 2)[0]
                for w in range(0x37) for i in range(struct.unpack_from('<i', rom, struct.unpack_from('<I', rom, 0x74C948 + 4 * w)[0] - ROM_BASE + 0x14)[0]))
    if rooms >= 410:
        sys.exit('map rooms now reach flag %d' % (448 + rooms))
    HEAP = 0x3D4D0                   # the heap's setup: heap_init replaces it, keeping the top of work RAM out of the heap
    if rom[HEAP:HEAP + 8] != bytes.fromhex('97489849984a0860') or struct.unpack_from('<I', rom, 0x3D738)[0] != 0xFDFE:
        sys.exit('heap setup changed')
    rom[HEAP:HEAP + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['heap_init'] | 1)
    WRITE = 0x3FBDE                  # the EEPROM write: save_write replaces it. The address isn't word-aligned, so the literal starts 10 bytes in
    if rom[WRITE:WRITE + 14] != bytes.fromhex('f8b50068171c0e1c1d1c002825d0'):
        sys.exit('EEPROM write changed: %s' % rom[WRITE:WRITE + 14].hex())
    rom[WRITE:WRITE + 14] = bytes.fromhex('10b4014ca44610bc6047') + struct.pack('<I', sym['save_write'] | 1)
    for vt, slot, want, name in ((0x4AEF8, 0x28, 0x0802084D, 'beam_update'), (0x4C9F0, 0x84, 0x0804F8C9, 'player_input')):     # every beam's update, and the player's keys
        if ROM_BASE + vt + struct.unpack_from('<i', rom, vt + slot)[0] != want:
            sys.exit('vtable changed at 0x%X' % (vt + slot))
        struct.pack_into('<i', rom, vt + slot, (sym[name] | 1) - (ROM_BASE + vt))
    DAMAGE = 0xE9D8                  # Combat_Damage's first 8 bytes: combat_orig runs them, then comes back
    if rom[DAMAGE:DAMAGE + 8] != bytes.fromhex('f0b5061c0c1c0831'):
        sys.exit('Combat_Damage changed: %s' % rom[DAMAGE:DAMAGE + 8].hex())
    rom[DAMAGE:DAMAGE + 8] = bytes.fromhex('004b1847') + struct.pack('<I', sym['combat_hook'] | 1)
    end, art = add_eraser(rom, clean, sym, at + len(code), art)    # after the row edits above: it moves the skill table
    i = rom.find(bytes.fromhex('092c'), 0x4C70, 0x4C84)    # Select Game draws 8 characters, not the guest slot: Broly's size covered the text
    if i < 0:
        sys.exit('Select Game party loop changed')
    rom[i:i + 2] = bytes.fromhex('082c')
    return end, art


def add_eraser(rom, clean, sym, at, art):
    """Eraser Cannon and SS Deadly Bomber: recoloured copies of Big Bang's two ball animations and icons, each move's parameter table (its last word scales the damage)
    and behaviour, new skill rows, and new UI strings."""
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    one = indexer([i for i in range(1, 256) if i not in artclean.MENU_SLOTS], pal)
    def put(data):
        nonlocal at
        at = (at + 3) & ~3; o = at; rom[o:o + len(data)] = data; at += len(data)
        return ROM_BASE + o
    def put_art(data):                           # tiles: with the sprites, past the code area
        nonlocal art
        art = (art + 3) & ~3; o = art; rom[o:o + len(data)] = data; art += len(data)
        return ROM_BASE + o
    PARAMS, OLD_VT = 0x76ACC0, 0x4D05C                    # Big Bang's table: levels 1 and 2 cyan ball, level 3 gold
    icons = struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 2 + 4)
    rows, strings = {}, []
    for name, skill, power, title, text, tint in NEW_MOVES:
        def recolour(v):
            if v == 0: return 0
            r, g, b = (int(x) for x in pal[v]); top = max(r, g, b); pale = min(r, g, b) / 255
            return one(np.array((top * (tint[0] + tint[1] * pale), top * (tint[2] + tint[3] * pale), top * (tint[4] + tint[5] * pale))).astype(int))
        remap = bytes(recolour(v) for v in range(256)); copies = {}
        def ball(rec):
            """One animation: four facings of 120 bytes, each up to ten {header, attributes, tile data} rows."""
            out = bytearray(clean[rec:rec + 480])
            for k in range(0, 480, 12):
                head, _, tiles = struct.unpack_from('<III', out, k)
                if tiles:
                    if tiles not in copies:
                        o = tiles - ROM_BASE; copies[tiles] = put(bytes(clean[o:o + (head >> 16 & 255) * (head >> 24 & 255)]).translate(remap))
                    struct.pack_into('<I', out, k + 8, copies[tiles])
            return put(bytes(out))
        if name == 'disc':
            l2u = open(LOG2, 'rb').read()      # USA cart: palette and tiles at the addresses its decomp gives
            l2pal = np.frombuffer(l2u[0x3ECEA4:0x3ECEA4 + 768], np.uint8).reshape(256, 3)
            l2map = bytes(0 if v == 0 else one(l2pal[v]) for v in range(256))
            spin = [put(l2u[t:t + 512].translate(l2map)) for t in (0x6DDA34, 0x6DDC34)]
            def ball(rec, place=((16, 4), (16, 12), (28, 8), (4, 8))):
                """The same rows and timing as Big Bang's ball, showing the two 32x16 frames of the disc in turn."""
                out = bytearray(clean[rec:rec + 480])
                for k in range(0, 480, 12):
                    if struct.unpack_from('<I', out, k + 8)[0]:
                        x, y = place[k // 120]
                        struct.pack_into('<4BII', out, k, x, y, 32, 16, 0x80006000, spin[(k // 12) & 1])
                return put(bytes(out))
        balls = {}; table = sym[name + '_params'] - ROM_BASE
        for i in range(3):
            a, b, rec, strength = struct.unpack_from('<4I', clean, PARAMS + 16 * i)
            balls.setdefault(rec, ball(rec - ROM_BASE))
            struct.pack_into('<4I', rom, table + 16 * i, a, b, balls[rec], int(strength * power[i]))
        vt = sym[name + '_vt'] - ROM_BASE                 # the behaviour's other methods stay Big Bang's: only the start differs
        for k in range(9):
            fn = ROM_BASE + OLD_VT + struct.unpack_from('<i', clean, OLD_VT + 4 * k)[0]
            struct.pack_into('<i', rom, vt + 4 * k, ((sym[name + '_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
        row = bytearray(clean[SKILL_ROWS + 24 * 2:SKILL_ROWS + 24 * 3])
        struct.pack_into('<II', row, 4, *[put(bytes(clean[p - ROM_BASE:p - ROM_BASE + 0x200]).translate(remap)) for p in icons])
        struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
        struct.pack_into('<I', row, 20, sym[name + '_use'] | 1)
        rows[skill] = bytes(row)
        strings += [put(t.encode('utf-16-le') + b'\0\0') for t in (title, text)]
    # Special Beam Cannon: copies of the Kamehameha's frame records, each {header, attributes, tile data} rows. The core goes pale yellow, the middle gold, and the rim purple.
    BEAM_TINT = {2: (248, 248, 216), 30: (248, 248, 216), 29: (248, 248, 144), 76: (248, 248, 72), 28: (248, 248, 72), 5: (248, 248, 72), 195: (248, 208, 0), 27: (248, 208, 0), 110: (248, 208, 0),
                 75: (168, 48, 224), 109: (168, 48, 224), 74: (112, 24, 168), 4: (112, 24, 168)}
    def beam_colour(v):
        if v == 0: return 0
        return one(np.array(BEAM_TINT.get(v, tuple(pal[v])), dtype=int))
    remap = bytes(beam_colour(v) for v in range(256)); copies = {}
    def frames(o, count):
        out = bytearray(clean[o:o + 12 * count])
        for k in range(0, 12 * count, 12):
            tiles = struct.unpack_from('<I', out, k + 8)[0]
            if not 0x08700000 <= tiles < 0x08800000: continue
            if tiles not in copies:
                t = tiles - ROM_BASE; copies[tiles] = put(bytes(clean[t:t + out[k + 2] * out[k + 3]]).translate(remap))
            struct.pack_into('<I', out, k + 8, copies[tiles])
        return put(bytes(out))
    BEAM_PARAMS, BEAM_VT = 0x71DA68, 0x4D9F8
    # The beam itself is LoG2's Special Beam Cannon: 7 rows a facing (muzzle 2, body 3, tip 2) laid into BF's 16-row facings (muzzle 0-1, body 3-5 and spare frame 6, tip 7-8 and 10-11).
    # Rows 13-14, a small end piece LoG2 doesn't have, keep the recoloured Kamehameha's. Every level uses this one thin shape.
    l2 = open(LOG2, 'rb').read(); L2_ART = 0x6E4560
    l2pal = np.frombuffer(l2[0x3ECEA4:0x3ECEA4 + 768], np.uint8).reshape(256, 3).astype(int)    # sprite palette in the USA cart
    l2map = bytes(0 if v == 0 else one(l2pal[v]) for v in range(256)); l2tiles = {}
    record = bytearray(rom[frames(struct.unpack_from('<I', clean, BEAM_PARAMS + 12)[0] - ROM_BASE, 64) - ROM_BASE:][:768])
    for facing in range(4):
        for bf, row in ((0, 0), (1, 1), (3, 2), (4, 3), (5, 4), (7, 5), (8, 6), (10, 5), (11, 6)):
            hdr, attr, tiles = struct.unpack_from('<III', l2, L2_ART + 12 * (facing * 7 + row))
            if tiles not in l2tiles:                     # always the whole 256-byte block: a short row still has the engine copy all of it
                t = tiles - ROM_BASE; l2tiles[tiles] = put(l2[t:t + 256].translate(l2map))
            struct.pack_into('<III', record, 12 * (facing * 16 + bf), hdr, attr, l2tiles[tiles])
        struct.pack_into('<I', record, 12 * (facing * 16 + 6) + 8, struct.unpack_from('<I', record, 12 * (facing * 16 + 5) + 8)[0])
    beam_art = put(bytes(record))
    shape, table = {}, sym['beam_params'] - ROM_BASE
    for i in range(3):
        a, strength, body, head = struct.unpack_from('<4I', clean, BEAM_PARAMS + 16 * i)
        shape.setdefault(body, frames(body - ROM_BASE, 9))
        struct.pack_into('<4I', rom, table + 16 * i, a, strength, shape[body], beam_art)
    vt = sym['beam_vt'] - ROM_BASE
    for k in range(9):
        fn = ROM_BASE + BEAM_VT + struct.unpack_from('<i', clean, BEAM_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['beam_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
    row = bytearray(clean[SKILL_ROWS + 24 * 15:SKILL_ROWS + 24 * 16])
    struct.pack_into('<II', row, 4, *[put(bytes(clean[p - ROM_BASE:p - ROM_BASE + 0x200]).translate(remap)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 15 + 4)])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['beam_use'] | 1)
    rows[BEAM_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Special Beam Cannon', 'Press the B Button and hold it to charge, then release to fire a thin beam of energy from your fingertips.', 'Android 17', 'Future Trunks')]
    # Full Power Energy Wave and the androids' blue blasts. The hues and the method are Gero's Legacy's (tools/kifx.py); here they're copies, since Gohan and everyone else keep the originals.
    def shifted(hue):
        def colour(v):
            if v == 0: return 0
            h, s, b = colorsys.rgb_to_hsv(*(pal[v] / 255.0))
            if s < 0.12: return v                     # whites and greys stay: the hot core
            return one((np.array(colorsys.hsv_to_rgb(hue, s, b)) * 255).astype(int))
        return bytes(colour(v) for v in range(256))
    green, blue = shifted(125 / 360), shifted(215 / 360)
    WAVE_PARAMS, WAVE_VT, BALL_TILES, BALL_RECS, WAVE_TILES = 0x725018, 0x4E2D8, (0x720864, 0x721164), (0x721164, 0x721218), (0x721218, 0x724718)
    if struct.unpack_from('<I', clean, 0x1AE1C)[0] != ROM_BASE + WAVE_PARAMS:
        sys.exit('wave table moved')
    moved = []                                        # every tile pointer falls in one of these blocks. A frame can have the engine copy more than its width and height say, so whole blocks are copied
    for lo, hi in (BALL_TILES, WAVE_TILES):
        moved.append((lo, hi, put(clean[lo:hi].translate(green))))
    def rebase(p):
        for lo, hi, new in moved:
            if lo <= p - ROM_BASE < hi: return new + p - ROM_BASE - lo
        sys.exit('wave frame outside its tiles: 0x%X' % p)
    def wave_records(lo, hi):
        out = bytearray(clean[lo:hi])
        for k in range(0, hi - lo, 12):
            p = struct.unpack_from('<I', out, k + 8)[0]
            if p: struct.pack_into('<I', out, k + 8, rebase(p))
        return out
    ball_new = put(bytes(wave_records(*BALL_RECS)))
    table = sym['wave_params'] - ROM_BASE
    for i in range(3):
        a, strength, ball_rec, head = struct.unpack_from('<4I', clean, WAVE_PARAMS + 16 * i)
        struct.pack_into('<4I', rom, table + 16 * i, a, strength, ball_new + ball_rec - ROM_BASE - BALL_RECS[0], put(bytes(wave_records(head - ROM_BASE, head - ROM_BASE + 768))))
    vt = sym['wave_vt'] - ROM_BASE
    for k in range(9):
        fn = ROM_BASE + WAVE_VT + struct.unpack_from('<i', clean, WAVE_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['wave_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
    row = bytearray(clean[SKILL_ROWS + 24 * 6:SKILL_ROWS + 24 * 7])
    struct.pack_into('<II', row, 4, *[put(bytes(clean[p - ROM_BASE:p - ROM_BASE + 0x200]).translate(green)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 6 + 4)])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['wave_use'] | 1)
    rows[WAVE_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Full Power Energy Wave', 'Press the B Button and hold it to charge, then release to fire a wave of green energy.  Hold the B Button to keep firing.')]
    for skill, name, text in ((SUPER13_SKILL, 'Super 13', 'Press the B Button to absorb the cores of Android 14 and Android 15 and become Super 13: attacks hit 1.5x as hard. Press it again to change back.'),
                              (SUPER17_SKILL, 'Super 17', 'Press the B Button to become Super 17: attacks hit 1.5x as hard. Press it again to change back.')):
        row = bytearray(clean[SKILL_ROWS + 24 * 20:SKILL_ROWS + 24 * 21])
        struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
        struct.pack_into('<II', row, 16, sym['super_can'] | 1, sym['super_use'] | 1)
        rows[skill] = bytes(row)
        strings += [put(t.encode('utf-16-le') + b'\0\0') for t in (name, text)]
    # Goku Black. Rose is Super Saiyan's row under its own name (its use is ss_use, as Goku's). The Black Kamehameha is the Kamehameha's code with Black's purple frames,
    # or Rose's pink ones: black_kame_start picks by form. Its icons are the Kamehameha's in Black's purple.
    row = bytearray(rom[SKILLS - 12 + 24 * 20:SKILLS - 12 + 24 * 21])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    pink = shifted(325 / 360)                   # Rose's aura and icon: Super Saiyan's, pink
    struct.pack_into('<II', row, 4, *[put(bytes(clean[p - ROM_BASE:p - ROM_BASE + 0x200]).translate(pink)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 20 + 4)])
    struct.pack_into('<I', row, 20, sym['rose_use'] | 1)
    rows[ROSE_SKILL] = bytes(row)
    red = shifted(4 / 360)                      # Super Saiyan 4's aura: Super Saiyan's, red
    for who, tint in (('rose', pink), ('ssj4', red)):
        for name, at_, count in ((who + '_aura_field', 0x752D28, 3), (who + '_aura_other', 0x7520D4, 7)):
            out = bytearray(clean[at_:at_ + 12 * count])
            for k in range(0, 12 * count, 12):
                t = struct.unpack_from('<I', out, k + 8)[0] - ROM_BASE
                struct.pack_into('<I', out, k + 8, put_art(clean[t:t + out[k + 2] * out[k + 3]].translate(tint)))
            rom[sym[name] - ROM_BASE:sym[name] - ROM_BASE + 12 * count] = out
        vt = sym[who + '_vt'] - ROM_BASE
        for k in range(14):
            fn = (sym[who + '_start'] | 1) if k == 0 else ROM_BASE + POWER_UP_VT + struct.unpack_from('<i', clean, POWER_UP_VT + 4 * k)[0]
            struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Super Saiyan Rose', 'Press the B Button to transform into Super Saiyan Rose: attacks hit 1.5x as hard.  Press it again to change back.')]
    for form in ('black', 'rose'):
        tint = KAME_TINT[form]
        remap = bytes(0 if v == 0 else one(np.array(tint.get(v, tuple(pal[v])), dtype=int)) for v in range(256)); copies = {}
        def frames(o, count):
            out = bytearray(clean[o:o + 12 * count])
            for k in range(0, 12 * count, 12):
                tiles = struct.unpack_from('<I', out, k + 8)[0]
                if not 0x08700000 <= tiles < 0x08800000: continue
                if tiles not in copies:
                    t = tiles - ROM_BASE; copies[tiles] = put_art(bytes(clean[t:t + out[k + 2] * out[k + 3]]).translate(remap))
                struct.pack_into('<I', out, k + 8, copies[tiles])
            return put(bytes(out))
        shape, table = {}, sym[form + '_params'] - ROM_BASE
        for i in range(3):
            a, strength, body, head = struct.unpack_from('<4I', clean, BEAM_PARAMS + 16 * i)
            shape.setdefault(body, frames(body - ROM_BASE, 9)); shape.setdefault(head, frames(head - ROM_BASE, 64))
            struct.pack_into('<4I', rom, table + 16 * i, a, strength, shape[body], shape[head])
        if form == 'black': icon_map = remap
    vt = sym['black_kame_vt'] - ROM_BASE
    for k in range(9):
        fn = ROM_BASE + BEAM_VT + struct.unpack_from('<i', clean, BEAM_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, ((sym['black_kame_start'] | 1) if k == 0 else fn) - (ROM_BASE + vt))
    row = bytearray(clean[SKILL_ROWS + 24 * 15:SKILL_ROWS + 24 * 16])
    struct.pack_into('<II', row, 4, *[put(bytes(clean[p - ROM_BASE:p - ROM_BASE + 0x200]).translate(icon_map)) for p in struct.unpack_from('<II', clean, SKILL_ROWS + 24 * 15 + 4)])
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['black_kame_use'] | 1)
    rows[BLACK_KAME_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Black Kamehameha', 'Hold the B Button to emit a long beam of dark energy.')]
    import zone26 as z26
    if ERASER_UI + len(strings) > z26.CELL_NAME_UI: sys.exit('move CELL_NAME_UI up')
    while ERASER_UI + len(strings) < z26.CELL_NAME_UI: strings.append(put(b'\0\0'))
    strings.append(put('The Cell Games Arena'.encode('utf-16-le') + b'\0\0'))
    strings.append(put('Glacier'.encode('utf-16-le') + b'\0\0'))
    if ERASER_UI + len(strings) != BLACK_NAME_UI: sys.exit('form names moved')
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Goku Black', 'Super Saiyan Rose')]
    if ERASER_UI + len(strings) != GT_NAME_UI: sys.exit('GT names moved')
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Pan', 'Uub', 'Majuub', 'Brapan')]
    row = bytearray(clean[SKILL_ROWS + 24 * 20:SKILL_ROWS + 24 * 21])          # Majuub: Super Saiyan's row, its own name and use
    struct.pack_into('<HH', row, 12, ERASER_UI + len(strings), ERASER_UI + len(strings) + 1)
    struct.pack_into('<I', row, 20, sym['majuub_use'] | 1)
    rows[MAJUUB_SKILL] = bytes(row)
    strings += [put(t.encode('utf-16-le') + b'\0\0') for t in ('Majuub', 'Press the B Button to draw on Majin Buu\'s power and become Majuub: attacks hit 1.5x as hard.  Press it again to change back.')]
    BLAST_TILES, BLAST_TABLE, BLAST_SITE = (0x71300C, 0x71370C), 0x71370C, 0x197F2
    if rom[BLAST_SITE:BLAST_SITE + 14] != bytes.fromhex('207cbc4a41000918090189182165'):
        sys.exit('player blast code changed')
    blue_new = put(clean[BLAST_TILES[0]:BLAST_TILES[1]].translate(blue))
    frames_new = bytearray(clean[BLAST_TABLE:BLAST_TABLE + 192])
    for k in range(0, 192, 12):
        p = struct.unpack_from('<I', frames_new, k + 8)[0]
        if not BLAST_TILES[0] <= p - ROM_BASE < BLAST_TILES[1]:
            sys.exit('blast frame outside its tiles: 0x%X' % p)
        struct.pack_into('<I', frames_new, k + 8, blue_new + p - ROM_BASE - BLAST_TILES[0])
    rom[sym['blue_blast'] - ROM_BASE:sym['blue_blast'] - ROM_BASE + 192] = frames_new
    for form, hue in BLAST_HUE.items():         # Goku Black's and Rose's, the same way
        tiles_new = put_art(clean[BLAST_TILES[0]:BLAST_TILES[1]].translate(shifted(hue / 360)))
        fr = bytearray(clean[BLAST_TABLE:BLAST_TABLE + 192])
        for k in range(0, 192, 12):
            struct.pack_into('<I', fr, k + 8, tiles_new + struct.unpack_from('<I', fr, k + 8)[0] - ROM_BASE - BLAST_TILES[0])
        rom[sym[form + '_blast'] - ROM_BASE:sym[form + '_blast'] - ROM_BASE + 192] = fr
    rom[BLAST_SITE:BLAST_SITE + 14] = bytes.fromhex('01490847c046') + struct.pack('<I', sym['blast_hook'] | 1) + bytes.fromhex('c046c046')
    # The Spirit Bomb's sprite: ultimate/art/spirit_bomb.png, a whole picture on plain white. One 64x64 frame per 8 pixels of size: up to 64 across the whole orb, above that its top left quarter.
    from PIL import Image
    orb = np.array(Image.open('ultimate/art/spirit_bomb.png').convert('RGB'))
    colours = {(7, 238, 255): 7, (158, 255, 245): 195, (247, 255, 255): 196, (255, 255, 255): 0}
    idx = np.zeros(orb.shape[:2], np.uint8)
    for rgb, v in colours.items(): idx[(orb == rgb).all(2)] = v
    if len(set(map(tuple, orb.reshape(-1, 3)))) != 4:
        sys.exit('spirit_bomb.png has colours the build does not know')
    def nearest(a, w, h):
        ys = (np.arange(h) * a.shape[0] // h); xs = (np.arange(w) * a.shape[1] // w)
        return a[ys][:, xs]
    def linear(img):
        return b''.join(img[y:y + 8, x:x + 8].tobytes() for y in range(0, 64, 8) for x in range(0, 64, 8))
    table = sym['bomb_frames'] - ROM_BASE
    for k in range(12):
        size = (k + 1) * 8; cell = np.zeros((64, 64), np.uint8)
        if size <= 64:
            o = (64 - size) // 2; cell[o:o + size, o:o + size] = nearest(idx, size, size)
        else:
            whole = nearest(idx, size, size); q = whole[:size // 2, :size // 2]; cell[64 - size // 2:, 64 - size // 2:] = q
        struct.pack_into('<I', rom, table + 4 * k, put(linear(cell)))
    vt = sym['bomb_vt'] - ROM_BASE; BEAM_ACTOR_VT = 0x4AEF8
    mine = {0: 'bomb_destroy', 2: 'bomb_nop', 3: 'bomb_one', 4: 'bomb_draw_oam', 6: 'bomb_zero', 9: 'bomb_zero', 10: 'bomb_nop'}
    for k in range(14):
        fn = (sym[mine[k]] | 1) if k in mine else ROM_BASE + BEAM_ACTOR_VT + struct.unpack_from('<i', clean, BEAM_ACTOR_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    vt = sym['absorb_vt'] - ROM_BASE
    for k in range(14):
        fn = (sym['absorb_start'] | 1) if k == 0 else ROM_BASE + POWER_UP_VT + struct.unpack_from('<i', clean, POWER_UP_VT + 4 * k)[0]
        struct.pack_into('<i', rom, vt + 4 * k, fn - (ROM_BASE + vt))
    if struct.unpack_from('<I', rom, 0x13618)[0] != ROM_BASE + SKILL_ROWS:
        sys.exit('skill table reference moved')
    struct.pack_into('<I', rom, 0x13618, put(bytes(rom[SKILL_ROWS:SKILL_ROWS + 24 * ERASER_SKILL]) + b''.join(rows[k] for k in sorted(rows))))
    ptrs = find_once(rom, clean[UI_TABLE:UI_TABLE + 64], 'UI string table')
    new = put(bytes(rom[ptrs:ptrs + 4 * ERASER_UI]) + struct.pack('<%dI' % len(strings), *strings))
    n = 0
    for o in range(0, CODE_END, 4):
        if struct.unpack_from('<I', rom, o)[0] == ROM_BASE + ptrs:
            struct.pack_into('<I', rom, o, new); n += 1
    if n != 51:
        sys.exit('UI table: expected 51 references, found %d' % n)
    return at, art


def add_portraits(rom, clean, at):
    """Android 17 and Future Trunks: LoG2's portraits (the import Gero's Legacy uses) in Buu's Fury's gold frame, on speaker ids past the 163 retail ones."""
    LIT, TABLE, COUNT, TEMPLATE = 0x12194, 0x6F393C, 163, 9        # the frame comes from Android 18's portrait
    if struct.unpack_from('<I', rom, LIT)[0] != ROM_BASE + TABLE:
        sys.exit('portrait table reference moved')
    combo = open(COMBO, 'rb').read()[0x800000:]
    l2pal = np.frombuffer(combo[0x3ECD1C + 768:0x3ECD1C + 1536], np.uint8).reshape(256, 3)
    pal = np.frombuffer(clean[0x701B0 + 768:0x701B0 + 1536], np.uint8).reshape(256, 3)
    one = indexer([i for i in range(1, 256) if i not in artclean.MENU_SLOTS], pal)
    remap = np.array([one(l2pal[v]) for v in range(256)], np.uint8)
    def art(data, o):
        kind, size = struct.unpack_from('<II', data, o)
        raw = data[o + 8:o + 8 + 4096] if kind == 0 else bytes(wfz.decompress_stream(data, o + 8, 4096)[0])
        return np.frombuffer(raw, np.uint8).reshape(64, 64)
    frame = art(clean, struct.unpack_from('<I', clean, TABLE + 4 * TEMPLATE)[0] - ROM_BASE)
    table = list(struct.unpack_from('<%dI' % COUNT, clean, TABLE))
    table_at = (at + 3) & ~3; cur = table_at + 4 * 256
    for k in PORTRAITS:
        img = frame.copy()
        img[4:60, 4:60] = remap[art(combo, struct.unpack_from('<I', combo, 0x3ECB6C + 4 * k)[0] - 0x08800000)[4:60, 4:60]]
        rom[cur:cur + 4104] = struct.pack('<II', 0, 4096) + img.tobytes()
        table.append(ROM_BASE + cur); cur += 4104
    if len(table) != BLACK_PORTRAIT: sys.exit('portrait ids moved')
    for img in goku_black.portraits(one).values():        # Goku Black and Rose, from the owner's sheet, frame and all
        rom[cur:cur + 4104] = struct.pack('<II', 0, 4096) + img.astype(np.uint8).tobytes()
        table.append(ROM_BASE + cur); cur += 4104
    if len(table) != gt.FIRST_PORTRAIT: sys.exit('GT portrait ids moved')
    for img in gt.portraits(one):                        # GT, from the owner's Black Star Odyssey sheet, frame and all
        rom[cur:cur + 4104] = struct.pack('<II', 0, 4096) + img.astype(np.uint8).tobytes()
        table.append(ROM_BASE + cur); cur += 4104
    rom[table_at:table_at + 4 * 256] = struct.pack('<%dI' % len(table), *table) + bytes(4 * (256 - len(table)))
    struct.pack_into('<I', rom, LIT, ROM_BASE + table_at)
    return cur


def thumb_bl(at, to):
    d = (to - (at + 4)) >> 1
    return struct.pack('<HH', 0xF000 | (d >> 11 & 0x7FF), 0xF800 | (d & 0x7FF))


def patch_slot_read(rom, sym):
    """Send the game's three save-slot reads through slot_read. Code that far away is out of bl range, so sub_08004A76's
    18 bytes become two veneers; its one job moves to slot_area."""
    AREA, VENEER = 0x4A76, 0x4A7A
    if rom[AREA:AREA + 18] != bytes.fromhex('45214901401808b54178007803f0bbff08bd'):
        sys.exit('sub_08004A76 changed: %s' % rom[AREA:AREA + 18].hex())
    rom[AREA:AREA + 18] = bytes.fromhex('024a1047024a1047') + bytes(2) + struct.pack('<II', sym['slot_area'] | 1, sym['slot_read'] | 1)
    sites = [i for i in range(0x4000, 0x30000, 2) if rom[i:i + 4] == thumb_bl(i, 0x48A0)]
    if len(sites) != 3:
        sys.exit('expected 3 save-slot reads, found %s' % [hex(i) for i in sites])
    for i in sites:
        rom[i:i + 4] = thumb_bl(i, VENEER)


def main():
    debug = '--debug' in sys.argv
    clean = open('baserom.gba', 'rb').read()
    if hashlib.sha1(clean).hexdigest() != CLEAN_SHA1:
        sys.exit("baserom.gba isn't the clean Buu's Fury (USA) ROM (SHA-1 mismatch).")
    if not os.path.exists('assets/manifest.json'):
        subprocess.run(['make', 'extract'], check=True, stdout=subprocess.DEVNULL)
    cfg = json.load(open('ultimate/forms.json'))
    saved = {p: open(p).read() for p in (INTRO, FIELD, ACTORS_FILE, ENDING)}
    try:
        for p, s in unlock_edits_paths().items():
            saved.setdefault(p, s)
        unlock_edits()
        saved.setdefault(QUEST_NPC, open(QUEST_NPC).read())
        saved.setdefault(UI, open(UI).read())
        open(UI, 'w').write(re.sub(r'(?m)^1053\t.*$', '1053\tPress the B Button to gather energy above you, then throw it. It uses half your energy.', re.sub(r'(?m)^1050\t.*$', '1050\tSpirit Bomb', saved[UI])))
        saved.setdefault(BROLY_DEFEAT, open(BROLY_DEFEAT).read())
        open(BROLY_DEFEAT, 'w').write(broly_defeat(saved[BROLY_DEFEAT]))
        ui = open(UI).read()
        for k, v in UI_EDITS.items():
            ui, n = re.subn(r'(?m)^%d\t.*$' % k, '%d\t%s' % (k, v), ui)
            if n != 1: sys.exit('UI string %d not found' % k)
        open(UI, 'w').write(ui)
        npc = quest_npc(saved[QUEST_NPC])
        open(QUEST_NPC, 'w').write(npc)
        saved.setdefault(TOUR_NPC, open(TOUR_NPC).read())
        open(TOUR_NPC, 'w').write(tournament_npc(saved[TOUR_NPC]))
        saved.setdefault(HUB_NPC, open(HUB_NPC).read())
        open(HUB_NPC, 'w').write(hub_npc(saved[HUB_NPC]))
        saved.setdefault(POPO_NPC, open(POPO_NPC).read())
        open(POPO_NPC, 'w').write(popo_npc(saved[POPO_NPC]))
        saved.setdefault(DEATH_SCRIPT, open(DEATH_SCRIPT).read())
        open(DEATH_SCRIPT, 'w').write(death_script(saved[DEATH_SCRIPT]))
        if debug:
            debug_edits(FORM_COUNT)
        subprocess.run(['make', 'modern'], check=True, stdout=subprocess.DEVNULL)
    finally:
        for p, s in saved.items():
            open(p, 'w').write(s)
    rom = bytearray(open('buusfury_modern.gba', 'rb').read())
    if len(rom) != 0x800000 or set(rom[-16:]) != {0xFF}:
        sys.exit('modern ROM has outgrown the 8 MB base; move SPACE')
    rom += b'\xff' * 0x800000
    actors, actors_end = add_actors(rom, clean)
    index, free = patch_forms(rom, clean, cfg, actors)
    os.makedirs(OUT, exist_ok=True)
    json.dump(index, open(OUT + '/_forms.json', 'w'))
    free, actors_end = add_outfits(rom, clean, (free + 3) & ~3, actors_end)
    sys.path.insert(0, 'ultimate')
    import zone26
    zone_end, zone_info = zone26.apply(rom, clean, PROTO, LOG2, actors_end, actors, debug and '--zone' in sys.argv, symbol('gUnknown_08785580'), symbol('gUnknown_08796114'), symbol('gUnknown_08786E68'))
    print('zone 26 tiles:', zone_info)
    actors_end = add_portraits(rom, clean, zone_end)      # 4 KB each: they live with the art, past the code area
    if {k: actors[k] for k in new_actor_ids()} != new_actor_ids():
        sys.exit('actor ids differ from the ones the quest script used')
    npc = symbol('gUnknown_080783A0') - ROM_BASE      # the quest giver stands still: his wander box shrinks to his own spot
    struct.pack_into('<4H', rom, npc - 8, 320, 360, 320, 360)
    struct.pack_into('<4H', rom, symbol('gUnknown_080783CC') - ROM_BASE - 8, 96, 328, 96, 328)      # and so does the tournament's
    struct.pack_into('<4H', rom, symbol('gUnknown_08078EA0') - ROM_BASE + 8, 288, 472, 288, 472)   # and Mr. Popo: he opens the Time Chamber
    if debug:
        at = (free + 3) & ~3
        code = save_stub(at)
        rom[at:at + len(code)] = code
        tab = find_once(rom, clean[NATIVES:NATIVES + 64], 'native table')
        struct.pack_into('<I', rom, tab + 4 * DEBUG_NATIVE, ROM_BASE + at + 1)
    os.makedirs(OUT, exist_ok=True)
    name = ('BFU_debug_enemy' if '--enemy' in sys.argv else 'BFU_debug_zone' if '--zone' in sys.argv else 'BFU_debug') if debug else 'BFU'
    print('room left: code %d KB, art %d KB' % ((ACTORS_AT - free) >> 10, (0x1000000 - actors_end) >> 10))
    if free >= ACTORS_AT or actors_end > 0x1000000:
        sys.exit('ROM layout overflow: code ends %X (limit %X), sprites end %X' % (free, ACTORS_AT, actors_end))
    size = (actors_end + 0xFFFFF) & ~0xFFFFF
    out = bytes(rom[:size])
    if bps.apply(clean, bps.make(clean, out)) != out:
        sys.exit('BPS round trip failed')
    open('%s/%s.bps' % (OUT, name), 'wb').write(bps.make(clean, out))
    open('%s/%s_PERSONAL_USE_ONLY.gba' % (OUT, name), 'wb').write(out)
    ss2_lists = {str(u['flag']): symbol(u['list']) - ROM_BASE for u in json.load(open('ultimate/outfits.json'))['unlocks'] if u['flag'] >= SS2_FLAG}
    json.dump({'forms': index, 'first_free': hex(free), 'ss2_lists': ss2_lists}, open('%s/%s.map.json' % (OUT, name), 'w'), indent=1)
    print('%s: %d bytes, sha1 %s, patch %d bytes, forms %s' % (name, len(out), hashlib.sha1(out).hexdigest(),
          os.path.getsize('%s/%s.bps' % (OUT, name)), index))


main()
