#!/usr/bin/env python3
"""Fusions after the ending, and Super 13's fight as Goku only, played in the emulator (build `--debug --zone` first; set BFU_PROTO):
  python3 ultimate/test_fusion.py [work dir] [debug zone rom]
Nov 11, the owner: "Did the super 13 fight with DBZ Gogeta, noticed it swapped back to Goku for the spirit bomb scene and then when going
back to the switch character menu after winning Gogeta is stuck permanently fused and Goku and Vegeta aren't selectable. I guess add a
rule to make the Super 13 fight specifically only startable and maybe only playable as Goku just to avoid bugs like this, and revert any
fusions if a player fuses mid fight for the spirit bomb scene just in case".
What happened: a Fusion Dance takes Goku and Vegeta out of the party and gives Gogeta a time that only runs while he plays; the finish
made Goku play, and Gogeta's "no time limit" as a fighter of his own fell on the danced Gogeta as well. outfit.c fusion_end, gogeta_keep.
The Fusion Dance's button game can't be played by a script (five random moves to repeat; a wrong one makes the fat or thin Gogeta,
a scene of a few seconds that ends by itself, in the original game too). So a fused Gogeta is set up as a successful dance leaves him
(script native 0xA8: Gogeta in the party with five minutes, both dancers out, their slots in his record +2, Gogeta the one playing), and
the next door builds the player's figure from the party record, as every area change does.
1. A danced Gogeta keeps his time limit after the ending, counting down (not "no limit"). At the fight's door anyone but Goku is told
   so, the fusion ends, Goku and Vegeta are back in the party, selectable, Goku plays and is taken in, and Gogeta is in the party as
   himself (a debug build has his looks open).
2. The Fusion Dance can't be used in the fight; outside it is danced as ever (with a wrong move: the fat or thin Gogeta, who splits
   again by himself).
3. A danced Gogeta's time running out ends the fusion the game's own way, and all three are in the party after it.
4. The state the owner's save is in (Gogeta in the party with no time limit, Goku and Vegeta out) puts itself right, whoever plays:
   with Goku playing by itself; with the danced Gogeta playing the game ends the fusion itself.
Nov 12, the owner: "SSJ4 Gogeta and Potara Vegito and let's also implement the Potara mechanic now", then "Fusion dance is already a
skill so can we make a separate Potara skill" (outfit.c potara_*, dance_use, fusion_native):
5. The Potara (skill 50) is learned by Goku and Vegeta with all four Trials won, and not before; the Fusion Dance (12) after the ending
   (Goku's is his book's seventeenth place, its bit in the bench). Used by Goku in a fight, the Potara: Vegito plays (his look, his record
   in the party and selectable, Goku and Vegeta out, an hour on his clock, counting down, the dancers in his record), and Gogeta as
   himself stays in the party all along.
6. Vegito's hour running out splits him the game's way (Goku plays, Goku and Vegeta back and selectable, Vegito out), Gogeta untouched.
   Vegito left in the party with Goku playing (a save stuck that way) splits by himself.
7. As Super Saiyan 4, with Vegeta knowing it, Goku's Fusion Dance: done right, Super Saiyan 4 Gogeta plays, a third of the dance's time.
   The button game can't be played by a script: at the fusion native the outcome is set to a right dance's (Gogeta's form, five minutes).
   Gogeta's own progress (a debug build has him as himself, with his own experience, stats and gear) comes back whole when the
   fusion's time runs out."""
import json, os, struct, subprocess, sys
sys.path[:0] = ['ultimate', 'ultimate/lib', 'tools/scripts']
import zone26
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/fusion'; os.makedirs(OUT, exist_ok=True)
ROM = sys.argv[2] if len(sys.argv) > 2 else 'ultimate/out/BFU_debug_zone_PERSONAL_USE_ONLY.gba'
PROTO = os.environ['BFU_PROTO']; P = open(PROTO, 'rb').read()
cfg = json.load(open('ultimate/zone26.json'))
D = zone26.links(cfg, {a: zone26.floor_mask(P, PROTO, a) for a in range(1, 16)})
RECS, RS, G, AREA, PLAYER, COMBAT = 0x03001560, 0x68, 0x03001068, 0x0300197C, 0x03001C34, 0x03001988
KEYS = 'DOWN UP LEFT RIGHT'.split()
START = open('tools/harness/long.txt').read().split('\n')[1:93]
DANCE = 12
POTARA, SS4 = 50, 36
MAP = json.load(open(ROM.replace('_PERSONAL_USE_ONLY.gba', '.map.json')))['forms']
fails = []
def check(name, ok):
    print('PASS' if ok else 'FAIL', name, flush=True)
    if not ok: fails.append(name)

class Game:
    """The debug zone build from its start (Goku on Snake Way), out of the debug door into Zone 26's first area."""
    def __init__(self):
        self.p = subprocess.Popen(['tools/harness/harness', ROM, '/dev/stdin', OUT], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
        self.bad = False
        self.send('guardon 0x09000000', *START, *['tap A 60'] * 4, 'run 60', 'keys DOWN', 'run 30', 'keys', 'run 200')
    def send(self, *ls):
        for l in ls: self.p.stdin.write(l + '\n')
        self.p.stdin.flush()
    def mem(self, a, n=1):
        self.send('mem %08X %d' % (a, n))
        while True:
            l = self.p.stdout.readline()
            if not l: raise SystemExit('harness ended')
            if 'bad pc' in l: self.bad = True
            if l.startswith('mem %08x' % a): return [int(x, 16) for x in l.split(':')[1].split()]
    def me(self): return self.mem(G)[0] & 255
    def area(self): return self.mem(AREA)[0] & 0xFFFF            # area << 8 | world
    def bits(self, c): return self.mem(RECS + c * RS)[0] & 3      # 1 in the party, 2 selectable
    def time(self, c): v = self.mem(RECS + c * RS + 8)[0]; return v - (1 << 32) if v >> 31 else v
    def party(self): return {c: self.bits(c) for c in (0, 4, 7)}
    def set_bits(self, c, v): self.send('poke8 %08X %02X' % (RECS + c * RS, (self.mem(RECS + c * RS)[0] & 0xFC) | v))
    def set_time(self, c, v): self.send('poke %08X %08X' % (RECS + c * RS + 8, v & 0xFFFFFFFF))
    def through(self, door, settle=110):
        """Stand in a door's ground and walk into it."""
        x0, y0, x1, y1 = door['rect']; pl = self.mem(PLAYER)[0]
        self.send('poke %08X %08X' % (pl + 0x1A0, (x0 + x1) // 2 << 8), 'poke %08X %08X' % (pl + 0x1A4, (y0 + y1) // 2 << 8), 'keys ' + KEYS[door['key']], 'run 12', 'keys', 'run %d' % settle)
    def to_door(self, fused=False):
        """Through the zone to area 14, whose top door is the fight's; `fused`: as a danced Gogeta from area 12 on."""
        for a in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13):
            if fused and a == 12: self.fuse()
            self.through([x for x in D[a] if x['to'] == {8: 10}.get(a, a + 1) and 'world' not in x][0])
        return self.area() == (14 << 8 | 26)
    def fight_door(self): self.through([x for x in D[14] if x['to'] == 15][0])
    def fuse(self):
        """What a successful Fusion Dance leaves (native 0xA8), by hand; the next door builds Gogeta's figure."""
        self.set_bits(0, 2); self.set_bits(4, 2); self.set_bits(7, 3); self.set_time(7, 300 * 60)
        self.send('poke8 %08X 29' % (RECS + 7 * RS + 0x14), 'poke8 %08X 40' % (RECS + 7 * RS + 2), 'poke8 %08X 00' % (RECS + 7 * RS + 3), 'poke8 %08X 07' % G)
    def dance(self, finish=True):
        """Whoever plays holds the Fusion Dance in his first slot and presses B (skills need a fight going: the game's flag for one is set).
        -> did the dance start? Its button game is an object of its own (sub_08028144, vtable 0x0804C9C8, "Watch This!"), in work
        memory a few seconds after the dancers meet. With `finish` the dance is then seen through with wrong moves (the fat or thin
        Gogeta plays for a few seconds, then splits again)."""
        r = RECS + self.me() * RS
        def games():
            self.send('dump w 02000000 40000'); self.me(); w = open(OUT + '/w.bin', 'rb').read()
            return sum(w[k:k + 4] == struct.pack('<I', 0x0804C9C8) for k in range(0, len(w), 4))
        before = games()
        up = ['poke8 %08X 7F' % (r + 0x17), 'run 37']            # (Android 13 is in the room: the fighter stays up meanwhile)
        self.send('poke8 %08X 01' % (r + 0x0C), 'poke8 %08X %02X' % (r + 0x0D, DANCE), 'poke8 %08X 00' % (r + 0x15), 'poke %08X 00000001' % COMBAT, 'run 4', 'keys B', *up[:1], 'run 30', 'keys', *up * 10)
        started = games() > before
        if finish:
            self.send('run 350'); seen = False
            for i in range(14):
                self.send('tap %s 24' % ('LEFT', 'RIGHT')[i & 1]); seen |= self.me() == 7
            self.send('run 600')
            return started and seen
        return started
    def flag_on(self, n): self.send('poke8 %08X %02X' % (G + 0x55 + n // 8, (self.mem(G + 0x55 + n // 8)[0] & 255) | 1 << n % 8))
    def rec(self, c): return b''.join(struct.pack('<I', v) for v in self.mem(RECS + c * RS, RS // 4))
    def fusion(self, skill, after=40):
        """Whoever plays holds this skill (the Potara, the dance) in his first slot and presses B in a fight (the game's flag for one set)."""
        r = RECS + self.me() * RS
        self.send('poke8 %08X 01' % (r + 0x0C), 'poke8 %08X %02X' % (r + 0x0D, skill), 'poke8 %08X 00' % (r + 0x15), 'poke %08X 00000001' % COMBAT, 'run 4', 'keys B', 'run 30', 'keys', 'run %d' % after)
    def close(self):
        self.p.stdin.close(); self.p.wait()

# 1. a danced Gogeta walks up to the fight
g = Game()
ok = g.to_door(fused=True); t = g.time(7); p = g.party()
print('   a danced Gogeta before the fight: playing %d, party bits (Goku, Vegeta, Gogeta) %s, his time %d' % (g.me(), p, t))
check('a danced Gogeta walks through Zone 26 to the area before the fight, Goku and Vegeta out of the party', ok and g.me() == 7 and p[0] & 1 == 0 and p[4] & 1 == 0 and p[7] == 3)
g.send('run 200'); t2 = g.time(7)
check('his fusion keeps its time limit, counting down (%d, then %d), not "no limit"' % (t, t2), 0 < t2 < t < 300 * 60)
g.fight_door(); g.send('shot door_gogeta')
check('at the door he is still outside, still Gogeta, while the message is up', g.area() == (14 << 8 | 26) and g.me() == 7)
g.send('tap A 60', *['poke8 %08X 7F' % (RECS + 0x17), 'run 40'] * 6, 'shot door_unfused'); p = g.party()      # (Android 13 is on him at once: Goku stays up)
print('   after the door: playing %d, party bits %s, Gogeta\'s time %d' % (g.me(), p, g.time(7)))
check('then the fusion is over: Goku plays in the fight\'s room, Goku and Vegeta are in the party and selectable', g.area() == (15 << 8 | 26) and g.me() == 0 and p[0] == 3 and p[4] == 3)
check('and Gogeta is in the party as himself, with no time limit (a debug build has his looks open)', p[7] & 1 == 1 and g.time(7) == -1)
# 2. the Fusion Dance in the fight, and outside it
before = g.party(); started = g.dance(finish=False); g.send('shot dance_fight')
print('   the dance in the fight: started %s, playing %d, area %04x, party %s' % (started, g.me(), g.area(), g.party()))
check('in the fight the Fusion Dance does nothing: no dance, Goku plays on, nobody leaves the party', not started and g.me() == 0 and g.party() == before and g.area() == (15 << 8 | 26))
check('no bad jumps (the door as Gogeta, the dance in the fight)', not g.bad); g.close()
g = Game(); g.to_door(); own = g.rec(7)
started = g.dance(); g.send('shot dance_outside', 'run 200'); p = g.party(); back = g.rec(7)
check('outside the fight the Fusion Dance is danced as ever (a wrong move: the short-lived Gogeta, then Goku and Vegeta again) %s' % p, started and g.me() in (0, 4) and p[0] == 3 and p[4] == 3 and g.area() == (14 << 8 | 26))
# Nov 12: the script puts the outcome's Gogeta (here the fat or thin one) in record 7 before the fusion native, which kept that as his own
# look: after a wrong dance the debug build's Gogeta stayed the fat one.
print('   Gogeta as himself before the dance: form %d; after it: form %d, in the party %d, time %d' % (own[0x14], back[0x14], back[0] & 1, g.time(7)))
check('and Gogeta as himself is his own look again after it, in the party', back[0x14] == own[0x14] and back[0] & 1 and g.time(7) == -1)
check('no bad jumps (the dance outside)', not g.bad); g.close()

# 3. a danced Gogeta's time runs out
g = Game(); ok = g.to_door(fused=True) and g.me() == 7
g.set_time(7, 40); g.send('run 700', 'shot timeout'); p = g.party()
print('   after his time ran out: playing %d, party bits %s, Gogeta\'s time %d' % (g.me(), p, g.time(7)))
check('a danced Gogeta whose time runs out splits the game\'s own way: a dancer plays, both are in the party and selectable', ok and g.me() in (0, 4) and p[0] == 3 and p[4] == 3)
check('and Gogeta is in the party as himself after it, with no time limit', p[7] & 1 == 1 and g.time(7) == -1)
check('no bad jumps (the time running out)', not g.bad); g.close()

# 4. the owner's save: Gogeta in the party with no time limit, Goku and Vegeta out
g = Game(); g.send('run 100')
g.set_bits(0, 2); g.set_bits(4, 2); g.set_bits(7, 3); g.set_time(7, -1); g.send('run 140'); p = g.party()
print('   stuck, Goku playing: after two seconds party bits %s, Gogeta\'s time %d' % (p, g.time(7)))
check('stuck with Goku playing: Goku and Vegeta come back, selectable, and Gogeta stays as himself', g.me() == 0 and p[0] == 3 and p[4] == 3 and p[7] & 1 == 1 and g.time(7) == -1)
check('no bad jumps (stuck, Goku playing)', not g.bad); g.close()
g = Game(); ok = g.to_door(fused=True) and g.me() == 7 and g.party()[0] & 1 == 0
g.set_time(7, -1); g.send('run 700', 'shot stuck_gogeta'); p = g.party()
print('   stuck, Gogeta playing: afterwards playing %d, party bits %s, Gogeta\'s time %d' % (g.me(), p, g.time(7)))
check('stuck with the danced Gogeta playing: the game ends the fusion itself, a dancer plays, Goku and Vegeta are back, selectable', ok and g.me() in (0, 4) and p[0] == 3 and p[4] == 3)
check('and Gogeta is in the party as himself', p[7] & 1 == 1 and g.time(7) == -1)
check('no bad jumps (stuck, Gogeta playing)', not g.bad); g.close()

# 5. the Potara: learned with all four Trials; the dance after the ending
import ast, bench as BN
BOOKS = next(ast.literal_eval(n.value) for n in ast.parse(open('ultimate/build.py').read()).body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'SKILL_BOOK')
def knows(g, c, skill):
    b = BOOKS[c].index(skill)
    return g.mem(RECS + c * RS + 0x22)[0] >> b & 1 if b < 16 else g.mem(BN.SPARE + 4 + c)[0] >> (b - 16) & 1
g = Game(); g.send('run 140')
before = (knows(g, 0, POTARA), knows(g, 4, POTARA))
g.flag_on(zone26.TRIAL_ALL); g.send('run 600')
after = (knows(g, 0, POTARA), knows(g, 4, POTARA)); dance = (knows(g, 0, DANCE), knows(g, 4, DANCE))
print('   the Potara known (Goku, Vegeta): before the Trials %s, after %s; the Fusion Dance %s' % (before, after, dance))
check('the Potara is learned by Goku and Vegeta with all four Trials won, not before', before == (0, 0) and after == (1, 1))
check('the Fusion Dance by both after the ending (Goku\'s in the bench: his book\'s seventeenth)', dance == (1, 1))
gogeta = g.rec(7)
g.fusion(POTARA); p = g.party(); v = g.mem(RECS + 6 * RS)[0]; t = g.time(6)
print('   after the Potara: playing %d, Vegito form %d bits %d time %d dancers %04x, party %s' % (g.me(), g.mem(RECS + 6 * RS + 0x14)[0] & 255, v & 3, t, g.mem(RECS + 6 * RS)[0] >> 16, p))
g.send('shot potara')
check('the Potara: Vegito plays, in his look, in the party and selectable, Goku and Vegeta out of it', g.me() == 6 and g.mem(RECS + 6 * RS + 0x14)[0] & 255 == 39 and v & 3 == 3 and p[0] & 1 == 0 and p[4] & 1 == 0)
check('his clock: an hour of his fighting (%d frames), counting down; the dancers Goku and Vegeta in his record' % t, 3590 * 60 < t <= 3600 * 60 and (g.mem(RECS + 6 * RS)[0] >> 16) & 0xFF in (0x40, 0x04))
g.send('run 300'); p = g.party()
check('Gogeta as himself stays in the party, with no time limit, while Vegito has the dancers', p[7] & 1 == 1 and g.time(7) == -1 and g.me() == 6 and g.time(6) < t)
# 6. his hour runs out
g.set_time(6, 40); g.send('run 700', 'shot potara_end'); p = g.party()
print('   after Vegito\'s time ran out: playing %d, party %s, Vegito bits %d' % (g.me(), p, g.mem(RECS + 6 * RS)[0] & 3))
check('Vegito\'s time running out splits him the game\'s way: Goku plays, Goku and Vegeta back and selectable, Vegito out of the party',
      g.me() == 0 and p[0] == 3 and p[4] == 3 and g.mem(RECS + 6 * RS)[0] & 1 == 0)
check('and Gogeta is as he was: in the party as himself, his record untouched', p[7] & 1 == 1 and g.time(7) == -1 and g.rec(7)[0x18:0x2C] == gogeta[0x18:0x2C])
check('no bad jumps (the Potara)', not g.bad)
g.set_bits(0, 2); g.set_bits(4, 2); g.set_bits(6, 3); g.set_time(6, -1); g.send('poke8 %08X 40' % (RECS + 6 * RS + 2), 'run 140'); p = g.party()     # (as the Potara leaves him: his dancers in +2)
check('stuck with Vegito in the party and Goku playing: Goku and Vegeta come back and Vegito leaves', g.me() == 0 and p[0] == 3 and p[4] == 3 and g.mem(RECS + 6 * RS)[0] & 1 == 0)
g.close()
# 7. Super Saiyan 4: the Fusion Dance, and Super Saiyan 4 Gogeta
g = Game(); g.send('run 140'); g.flag_on(zone26.TRIAL_ALL); g.send('run 140')
g.send('poke8 %08X %02X' % (RECS + 7 * RS + 0x24, 0x77), 'poke8 %08X %02X' % (RECS + 7 * RS + 0x28, 61), 'run 70')     # Gogeta's own experience and a stat, to see them come back
gogeta = g.rec(7)
vk = g.mem(RECS + 4 * RS + 0x22)[0] & 0xFFFF; g.send('poke8 %08X %02X' % (RECS + 4 * RS + 0x22, (vk | 1 << 3) & 255))     # Vegeta knows Super Saiyan 4 (his book's fourth)
g.send('poke8 %08X %02X' % (RECS + 0x14, MAP['kid_goku_ssj4']), 'run 4')
g.fusion(DANCE, after=10)
# The button game shows the moves ("Watch This!"), then waits for the player's ("Your Turn!"); a script can't know them. Moves are
# pressed one at a time (wrong ones), each inside a short wait for the fusion native (0x08002EE2, bp: the harness runs frames until it).
# There the outcome is set to a right dance's, as script 13's success branch has it: Gogeta's form in record 7 (0x9D(7, 102)) and five
# minutes on the native's stack (its last argument, at r0 + 4 * the count).
def bp(addr, frames):
    g.send('bp %08X %d' % (addr, frames), 'mem %08X 1' % G)        # (the mem after it flushes the harness's output: bp's own lines aren't)
    lines = []
    while True:
        l = g.p.stdout.readline()
        if not l: raise SystemExit('harness ended')
        if l.startswith('mem %08x' % G): return lines
        lines.append(l)
g.send('run 300'); hit = False; regs = None
for i in range(24):
    for k in ('keys %s' % ('LEFT', 'RIGHT')[i & 1], 'keys'):
        g.send(k); lines = bp(0x08002EE2, 30)
        b_ = [l for l in lines if l.startswith('bp ')]
        if b_ and 'not hit' not in b_[0]:                           # ("bp ADDR not hit at frame N" when it didn't come)
            hit = True; regs = [int(x, 16) for x in [l for l in lines if l.strip().startswith('regs:')][0].split(':')[1].split()]; break
    if hit: break
g.send('keys')
if hit:
    n = g.mem(regs[0])[0]; args = g.mem(regs[0] + 4, n)
    print('   the fusion native: arguments %s, record 7 form %d' % (args, g.mem(RECS + 7 * RS + 0x14)[0] & 255))
    g.send('poke8 %08X %02X' % (RECS + 7 * RS + 0x14, 41), 'poke %08X %08X' % (regs[0] + 4 * n, 300))
print('   the dance\'s button game returned: %s' % ('set to success' if hit else 'never'))
g.send('run 900', 'shot ssj4_gogeta'); p = g.party(); t = g.time(7)
print('   after the dance: playing %d, Gogeta form %d, time %d, party %s' % (g.me(), g.mem(RECS + 7 * RS + 0x14)[0] & 255, t, p))
check('as Super Saiyan 4 the Fusion Dance gives Super Saiyan 4 Gogeta, playing, Goku and Vegeta out', hit and g.me() == 7 and g.mem(RECS + 7 * RS + 0x14)[0] & 255 == MAP['gogeta_ssj4'] and p[0] & 1 == 0 and p[4] & 1 == 0)
check('with a third of the dance\'s time (%d frames)' % t, 80 * 60 < t <= 100 * 60)
g.set_time(7, 40); g.send('run 700', 'shot ssj4_gogeta_end'); p = g.party(); back = g.rec(7)
print('   after his time ran out: playing %d, party %s, Gogeta form %d' % (g.me(), p, back[0x14]))
check('his time running out splits him; Goku and Vegeta back', g.me() in (0, 4) and p[0] == 3 and p[4] == 3)
check('and Gogeta is himself again: in the party, his own look, experience, stats and gear back as they were',
      p[7] & 1 == 1 and g.time(7) == -1 and back[0x14] == gogeta[0x14] and back[0x18:0x1A] == gogeta[0x18:0x1A] and back[0x1C:0x1E] == gogeta[0x1C:0x1E] and back[0x24:0x2C] == gogeta[0x24:0x2C] and back[0x3C:0x4C] == gogeta[0x3C:0x4C])
check('no bad jumps (Super Saiyan 4 Gogeta)', not g.bad); g.close()

print('screens in', OUT)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
