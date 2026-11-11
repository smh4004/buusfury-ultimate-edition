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
   with Goku playing by itself; with the danced Gogeta playing the game ends the fusion itself."""
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
g = Game(); g.to_door()
started = g.dance(); g.send('shot dance_outside'); p = g.party()
check('outside the fight the Fusion Dance is danced as ever (a wrong move: the short-lived Gogeta, then Goku and Vegeta again) %s' % p, started and g.me() in (0, 4) and p[0] == 3 and p[4] == 3 and g.area() == (14 << 8 | 26))
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

print('screens in', OUT)
if fails: sys.exit('FAILED: %s' % fails)
print('ALL PASS')
