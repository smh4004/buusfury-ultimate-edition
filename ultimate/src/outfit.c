/* Outfit selection on the Switch Character screen. Up and Down cycle the highlighted character's outfits.
   A keeps the choice; B restores every character's form as it was when the screen opened.
   Addresses come from build.py as -D defines. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;

#define KEYS_NEW (*(volatile u16 *)0x03003304)
#define KEY_UP 0x40
#define KEY_DOWN 0x80
#define RECORDS ((u8 *)0x03001560)
#define RECORD_SIZE 0x68
#define FORM_OF(c) (RECORDS[(c) * RECORD_SIZE + 0x14])
#define OBJ_SELECTED 0x160
#define OBJ_LIST 0x118             /* {character, sprite} pairs */
#define SNAP_OWNER (*(u32 *)0x0203FF20)
#define SNAP_FORMS ((u8 *)0x0203FF24)
#define SNAP_MAGIC 0x4F465431

typedef int (*update_fn)(void *);
typedef int (*input_fn)(void *, void *, int, int);
#define orig_update ((update_fn)0x0802EBA5)
#define orig_input ((input_fn)0x0802ECEB)
#define Form_Sprite ((void *(*)(void *))0x0801713D)
#define Sprite_SetCharacter ((void (*)(void *, void *))0x0800EDF9)
#define Sprite_SetFacing ((void (*)(void *, int))0x0800ECDB)
#define Sprite_SetBehaviour ((void (*)(void *, void *))0x0800ED19)
#define GetFlag ((int (*)(void *, int))0x08004365)
#define PlaySound ((void (*)(void *, void *, int, int))0x0803E379)

struct outfit { u8 form; u8 also; u16 flag; const u16 *name; };  /* flag 0 = always available */
extern const u16 outfit_index[9][2];           /* first entry, count, per character */
extern const struct outfit outfit_table[];
extern const u8 form_table[];

/* The guest slot has one skill list but different fighters, so the list follows the outfit. A story form (Hercule, say) leaves it alone. */
static void guest_sync(void) {
    static const u8 broly[] = {3, 7, 8, ERASER_SKILL}, thirteen[] = {5, 7, 8, BOMBER_SKILL, WAVE_SKILL, SUPER13_SKILL}, piccolo[] = {3, 7, 17, BEAM_SKILL},
        fighter[] = {2, 7, 8}, a17[] = {5, 7, 8, BLITZ_SKILL, WAVE_SKILL, SUPER17_SKILL}, a18[] = {4, 7, BLITZ_SKILL, DISC_SKILL, WAVE_SKILL}, krillin[] = {3, 7, 15, DISC_SKILL}, videl[] = {1, 7},
        tien[] = {3, 7, 15, BLITZ_SKILL}, yamcha[] = {2, 7, 15}, pikkon[] = {3, 7, 8, WAVE_SKILL}, hercule[] = {1, 7},
        black[] = {4, 7, 14, BLACK_KAME_SKILL, ROSE_SKILL},     /* Goku Black: ki blasts, Instant Transmission, the Black Kamehameha, Rose. Energy Punch and Energy Sword play animation slots Goku's figure fills with other moves */
        trunks[] = {4, 7, 20, 4, 11},            /* Future Trunks: the same moves as Trunks */
        pan[] = {3, 7, 8, 20}, pan_plain[] = {2, 7, 8},  /* Pan: ki blasts and her rush; Super Saiyan in the two looks that have it. Brapan (the Bulma-Pan fusion) fights as Pan */
        uub[] = {4, 7, 8, 15, MAJUUB_SKILL};     /* Uub: ki blasts, rush, Kamehameha, Majuub */
    u8 *r = RECORDS + 8 * RECORD_SIZE;
    int form = FORM_OF(8), i;
    const u8 *list;
    if (form == FORM_BROLY || form == FORM_FP) list = broly;
    else if (form == FORM_A13 || form == FORM_S13) list = thirteen;
    else if (form == FORM_PICCOLO) list = piccolo;
    else if (form == FORM_ANDROID17 || form == FORM_S17) list = a17;
    else if (form == FORM_ANDROID18) list = a18;
    else if (form == FORM_KRILLIN) list = krillin;
    else if (form == FORM_VIDEL) list = videl;
    else if (form == FORM_TIEN) list = tien;
    else if (form == FORM_YAMCHA) list = yamcha;
    else if (form == FORM_PIKKON) list = pikkon;
    else if (form == FORM_HERCULE) list = hercule;
    else if (form == FORM_BLACK || form == FORM_ROSE) list = black;
    else if (form == FORM_FUTURE_TRUNKS) list = trunks;
    else if (form >= FORM_PAN && form < FORM_PAN + 4) list = pan;          /* pan, pan_ssj, pan_nobandana, pan_ssj_spiky */
    else if (form >= FORM_PAN + 4 && form <= FORM_PAN_LAST) list = pan_plain;
    else if (form == FORM_UUB || form == FORM_MAJUUB) list = uub;
    else if (form == FORM_KID_BUU || form == FORM_MAJIN_BUU || form == FORM_JANEMBA) list = fighter;
    else return;
    r[0x0C] = list[0];
    for (i = 0; i < list[0]; i++) r[0x0D + i] = list[i + 1];
    if (r[0x15] >= r[0x0C]) r[0x15] = 0;
}

/* Separate progress for the guest slot's fighters. The party still has nine records; the one in slot 8 belongs to whichever guest is out, and the others wait on a bench.
   Nothing here touches the game's save blocks: the bench has its own space after them, and a save that never swapped a guest never writes it.
   Which bench goes with which save is decided by a generation number kept in three spare bytes of the save itself, so a reload without saving, a new game,
   a deleted game or another slot simply fails to match and reads the right bench or none. */
#define G_BYTES ((u8 *)0x03001068)
#define GEN_AT 0x4F1                         /* padding after the byte at 0x4F0: generation (2 bytes), then who is out, plus one */
#define OUT_FIGHTER (G_BYTES[GEN_AT + 2])
#define MIRROR (*(u8 **)0x03004A64)
#define BENCH_OFFSET 0x1A20                  /* the three game blocks end here; EEPROM ends at 0x2000 */
#define SAVE_BLOCK 0x8B0
/* Version 2 of the bench: every fighter gets the same 22 bytes, so 21 fit where version 1 held 15. What it leaves out comes back by itself:
   health and ki (a benched fighter returns rested) and skill levels past the fifth (no guest has more than five moves; build.py checks).
   A level is 0-3, so each skill's two bytes go in two nibbles. */
#define BENCH_MAGIC 0x32484342
#define GROUPS 21
struct entry { u8 gear[4], maxhp[2], maxki[2], exp[4], stats[4], unspent, levels[5]; };
struct bench { u32 magic, gen, sum; u8 flags[4], used[4]; struct entry e[GROUPS]; u8 flags2[4], spare[10]; };   /* flags2: more flags 32-63 (older saves: zero) */
#define BENCH (*(struct bench *)0x0203F000)
typedef char bench_size_ok[sizeof(struct bench) == 496 && sizeof(struct entry) == 22 ? 1 : -1];
/* Version 1, as earlier builds saved it: read once and converted. 11 full entries, then 4 small ones running through the tail and on into more[]. */
#define V1_MAGIC 0x31484342
#define V1_FULL 11
#define V1_SMALL 4
#define V1_SMALL_SIZE 21                     /* used, exp[3] in sixteens, stats[4], unspent, levels[12] */
struct v1_entry { u8 used, gear[4], vitals[8], exp[4], stats[4], unspent, levels[14]; };
struct v1_bench { u32 magic, gen, sum; u8 flags[4], more[12]; struct v1_entry e[V1_FULL]; u8 tail[72]; };
typedef char v1_size_ok[sizeof(struct v1_bench) == 496 ? 1 : -1];
#define Recalculate ((void (*)(void *))0x08013C67)
#define FRAMES (*(volatile u32 *)0x03000F94)
#define VCOUNT (*(volatile u16 *)0x04000006)
/* Which fighter an outfit belongs to: Full Power is Broly, Super 13 is Android 13 and Rose is Goku Black (an outfit's "also" form). Order follows the guest list in
   outfits.json; build.py checks it. Groups 0-14 are where version 1 kept the same fighters. */
static const u8 bench_group[] = {BENCH_GROUP_LIST};
#define NO_GEAR ((const int *)0x080555B8)            /* each equipment slot's empty row */
#define BAG_COUNT (*(int *)(G_BYTES + 0xE4))
#define BAG ((u32 *)(G_BYTES + 0xE8))                /* row, with the wearer's slot plus one in the top four bits */
#define GUEST_WEARS (9u << 28)

static int group_of(int form) {
    int first = outfit_index[8][0], n = outfit_index[8][1], i;
    for (i = 0; i < n && i < (int)sizeof bench_group; i++)
        if (outfit_table[first + i].form == form || outfit_table[first + i].also == form) return bench_group[i];
    return -1;
}
static void bytes_copy(u8 *to, const u8 *from, int n) { while (n-- > 0) *to++ = *from++; }
static void bytes_zero(u8 *to, int n) { while (n-- > 0) *to++ = 0; }
static u32 gen_of(const u8 *game) { return game[GEN_AT] | game[GEN_AT + 1] << 8; }
static u32 sum_bytes(u32 sum, const u8 *p, int n) { while (n-- > 0) sum = sum * 31 + *p++; return sum; }
static u32 bench_sum(const struct bench *b) {
    u32 sum = sum_bytes(b->gen ^ 0x5A5B, b->flags, sizeof b->flags + sizeof b->used + sizeof b->e + sizeof b->flags2 + sizeof b->spare);
    return sum;
}
static u32 v1_sum(const struct v1_bench *b) {
    const u8 *p = (const u8 *)b->e; u32 sum = b->gen ^ 0x5A5A, i;
    for (i = 0; i < sizeof b->e + sizeof b->tail; i++) sum = sum * 31 + p[i];
    p = b->flags;
    for (i = 0; i < sizeof b->flags + sizeof b->more; i++) if (p[i]) sum = sum * 31 + p[i] + i;
    return sum;
}
static const u8 *saved_at(int slot) { return MIRROR + BENCH_OFFSET + slot * sizeof(struct bench); }
static const struct bench *saved_bench(int slot) { return (const struct bench *)saved_at(slot); }
static int bench_valid(const struct bench *b, u32 gen) { return b->magic == BENCH_MAGIC && b->gen == gen && b->sum == bench_sum(b); }
static int v1_valid(const struct v1_bench *b, u32 gen) { return b->magic == V1_MAGIC && b->gen == gen && b->sum == v1_sum(b); }

static void put_le(u8 *to, u32 v, int n) { while (n-- > 0) { *to++ = v; v >>= 8; } }
static u32 get_le(const u8 *from, int n) { u32 v = 0; int i; for (i = 0; i < n; i++) v |= (u32)from[i] << (8 * i); return v; }
static int nib(int v) { return v < 0 ? 0 : v > 15 ? 15 : v; }
static void levels_pack(u8 *to, const u8 *two_bytes) { int i; for (i = 0; i < 5; i++) to[i] = nib(two_bytes[2 * i]) | nib(two_bytes[2 * i + 1]) << 4; }
static void levels_unpack(u8 *to, const u8 *from) { int i; for (i = 0; i < 5; i++) { to[2 * i] = from[i] & 15; to[2 * i + 1] = from[i] >> 4; } }
static void mark_used(int g) { BENCH.used[g >> 3] |= 1 << (g & 7); }

static void v1_convert(const struct v1_bench *o) {
    int g, i;
    bytes_zero((u8 *)&BENCH, sizeof BENCH);
    BENCH.magic = BENCH_MAGIC; BENCH.gen = o->gen; bytes_copy(BENCH.flags, o->flags, 4);
    for (g = 0; g < V1_FULL; g++) {
        const struct v1_entry *e = &o->e[g]; struct entry *n = &BENCH.e[g];
        if (!e->used) continue;
        mark_used(g);
        bytes_copy(n->gear, e->gear, 4); bytes_copy(n->maxhp, e->vitals + 2, 2); bytes_copy(n->maxki, e->vitals + 6, 2);
        bytes_copy(n->exp, e->exp, 4); bytes_copy(n->stats, e->stats, 4); n->unspent = e->unspent; levels_pack(n->levels, e->levels);
    }
    for (g = 0; g < V1_SMALL; g++) {
        u8 b[V1_SMALL_SIZE]; struct entry *n = &BENCH.e[V1_FULL + g];
        for (i = 0; i < V1_SMALL_SIZE; i++) { int at = g * V1_SMALL_SIZE + i; b[i] = at < (int)sizeof o->tail ? o->tail[at] : o->more[at - sizeof o->tail]; }
        if (!b[0]) continue;
        mark_used(V1_FULL + g);
        for (i = 0; i < 4; i++) n->gear[i] = NO_GEAR[i];      /* small entries kept no gear and no maximum health: zero there means "as the record has it" */
        put_le(n->exp, get_le(b + 1, 3) << 4, 4); bytes_copy(n->stats, b + 4, 4); n->unspent = b[8]; levels_pack(n->levels, b + 9);
    }
}

/* Make the bench in memory the one that goes with this game. */
static void bench_ready(void) {
    u32 gen = gen_of(G_BYTES); int s;
    if (gen && BENCH.magic == BENCH_MAGIC && BENCH.gen == gen) return;
    if (gen && MIRROR) {
        for (s = 0; s < 3; s++)
            if (bench_valid(saved_bench(s), gen)) { bytes_copy((u8 *)&BENCH, saved_at(s), sizeof(struct bench)); return; }
        for (s = 0; s < 3; s++)
            if (v1_valid((const struct v1_bench *)saved_at(s), gen)) { v1_convert((const struct v1_bench *)saved_at(s)); return; }
    }
    bytes_zero((u8 *)&BENCH, sizeof BENCH);
    BENCH.magic = BENCH_MAGIC; BENCH.gen = gen;
}


/* Gear goes back in the bag when its wearer sits out, so it can't be worn twice; bench_fetch puts it back on if nobody else has taken it. */
static void bench_store(int g, u8 *r) {
    struct entry *e = &BENCH.e[g]; int i;
    mark_used(g);
    for (i = 0; i < 4; i++) {
        e->gear[i] = *(const u32 *)(r + 0x3C + i * 4);
        *(u32 *)(r + 0x3C + i * 4) = NO_GEAR[i];
    }
    for (i = 0; i < BAG_COUNT; i++) if (BAG[i] >> 28 == 9) BAG[i] &= 0x0FFFFFFF;
    bytes_copy(e->maxhp, r + 0x18, 2); bytes_copy(e->maxki, r + 0x1C, 2);
    bytes_copy(e->exp, r + 0x24, 4); bytes_copy(e->stats, r + 0x28, 4);
    e->unspent = r[0x2C]; levels_pack(e->levels, r + 0x2E);
}
static void bench_fetch(int g, u8 *r) {
    const struct entry *e = &BENCH.e[g]; int i, k;
    for (i = 0; i < 4; i++) {
        if ((int)e->gear[i] == NO_GEAR[i]) continue;
        for (k = 0; k < BAG_COUNT; k++)
            if (BAG[k] == e->gear[i]) { BAG[k] |= GUEST_WEARS; *(u32 *)(r + 0x3C + i * 4) = e->gear[i]; break; }
    }
    if (get_le(e->maxhp, 2)) bytes_copy(r + 0x18, e->maxhp, 2);
    if (get_le(e->maxki, 2)) bytes_copy(r + 0x1C, e->maxki, 2);
    bytes_copy(r + 0x24, e->exp, 4); bytes_copy(r + 0x28, e->stats, 4);
    r[0x2C] = e->unspent; levels_unpack(r + 0x2E, e->levels);
}
static int group_used(int g) { return BENCH.used[g >> 3] >> (g & 7) & 1; }
static void bench_bump(void) {
    u32 gen = (BENCH.gen * 25173 + 13849 + FRAMES * 16 + VCOUNT) & 0xFFFF;
    if (!gen || gen == BENCH.gen) gen = (BENCH.gen + 1) & 0xFFFF;
    if (!gen) gen = 1;
    BENCH.gen = gen;
    G_BYTES[GEN_AT] = gen; G_BYTES[GEN_AT + 1] = gen >> 8;
}

/* Saved flags past the story's, kept with the bench. The story's flag array has no room left. */
static u8 *more_byte(int f) { return f < 32 ? &BENCH.flags[f >> 3] : &BENCH.flags2[(f - 32) >> 3]; }   /* 0-31, then 32-63 */
int more_flag(int f) { bench_ready(); return *more_byte(f) >> (f & 7) & 1; }
static void more_flag_set(int f, int on) {
    bench_ready();
    if ((*more_byte(f) >> (f & 7) & 1) == on) return;
    if (on) *more_byte(f) |= 1 << (f & 7); else *more_byte(f) &= ~(1 << (f & 7));
    bench_bump();
}
/* Script natives: more_get(n) and more_put(n, value). more_put(MORE_POINTS, n) instead gives whoever is playing n stat points to spend (a Time Chamber wave's prize). */
#define MORE_POINTS 255
void more_get(int *sp) { int n = *sp; sp[n] = more_flag(sp[n]); }
void more_put(int *sp) {
    int n = *sp, f = sp[n - 1], v = sp[n];
    *sp = n - 2;
    if (f == MORE_POINTS) {
        u8 *r = RECORDS + *(u8 *)0x03001068 * RECORD_SIZE;
        r[0x2C] = r[0x2C] + v > 255 ? 255 : r[0x2C] + v;
        return;
    }
    more_flag_set(f, v != 0);
}

#define MORE_FLAG 0x7D0                      /* an outfit's flag from here up is more_flag(flag - MORE_FLAG) */
static int outfit_open(const struct outfit *o) {
    if (!o->flag) return 1;
#ifdef DEBUG_OPEN
    if (o->flag >= MORE_FLAG) return 1;                  /* debug builds start with everyone, and with a save that hasn't touched the bench */
#endif
    return o->flag >= MORE_FLAG ? more_flag(o->flag - MORE_FLAG) : GetFlag((void *)0x03001068, o->flag);
}

/* Endless and the Boss Rush rank. The run itself lives in memory only, so a reset can't leave one going; the best of each is saved in the flags above. */
#define ENDLESS_ON (*(u32 *)0x0203FFA0)
#define ENDLESS_WINS (*(u32 *)0x0203FFA4)
static const u8 tier_rooms[] = {TIER_ROOMS};
static int more_bits(int f, int n) { int v = 0, i; for (i = 0; i < n; i++) v |= more_flag(f + i) << i; return v; }
static void more_bits_set(int f, int n, int v) { int i; for (i = 0; i < n; i++) more_flag_set(f + i, v >> i & 1); }
static int endless_room(void) {
    int wins = ENDLESS_WINS, tier = wins < 6 ? 0 : wins < 12 ? 1 : 2;
    return tier_rooms[tier] + 6 * (wins % 3) + ((FRAMES * 25173 + VCOUNT) >> 4 & 0xFFFF) % 6;
}
void ladder(int *sp) {
    int n = *sp, op = sp[n], out = -1;
    switch (op) {
    case 0: ENDLESS_ON = 1; ENDLESS_WINS = 0; out = endless_room(); break;
    case 1: out = ENDLESS_ON; break;
    case 2: {
        u32 pay = ++ENDLESS_WINS * ENDLESS_STEP;
        *(u32 *)0x0300155C += pay > ENDLESS_CAP ? ENDLESS_CAP : pay;
        if ((int)ENDLESS_WINS > more_bits(16, 8) && ENDLESS_WINS < 256) more_bits_set(16, 8, ENDLESS_WINS);
        out = endless_room(); break; }
    case 3: ENDLESS_ON = 0; more_flag_set(15, 1); break;
    case 4: out = ENDLESS_WINS; break;
    case 5: out = more_bits(16, 8); break;
    case 6: {
        int hp = sp[n - 2], max = sp[n - 1], pct = max > 0 ? hp * 100 / max : 0, rank = pct >= 75 ? 4 : pct >= 50 ? 3 : pct >= 25 ? 2 : 1;
        more_bits_set(11, 2, rank - 1);
        if (rank > more_bits(8, 3)) more_bits_set(8, 3, rank);
        more_flag_set(7, 1);
        *sp = n - 3; return; }
    case 7: out = more_bits(11, 2) + 1; break;
    case 8: out = more_bits(8, 3); break;
    }
    if (out >= 0) sp[n] = out; else *sp = n - 1;
}

static void bench_settle(int was) {
    u8 *r = RECORDS + 8 * RECORD_SIZE;
    int now = group_of(FORM_OF(8)), out = OUT_FIGHTER - 1;
    if (now < 0) return;
    if (out < 0 || out >= GROUPS) out = group_of(was);
    if (out < 0 || out == now) return;
    bench_ready();
    bench_store(out, r);
    if (group_used(now)) bench_fetch(now, r);       /* a first swap starts level with the guest who was out, with nothing equipped */
    bench_bump();
    OUT_FIGHTER = now + 1;
    Recalculate(r);
    *(u16 *)(r + 0x16) = *(u16 *)(r + 0x18);          /* and every fighter comes back rested */
    *(u16 *)(r + 0x1A) = *(u16 *)(r + 0x1C);
}

/* The game's EEPROM write, whole, with the bench written after a game block when that slot doesn't already hold it. Same steps as the original at 0x0803FBDE. */
#define Copy ((void (*)(void *, const void *, int))0x08049145)
#define SoundPause ((void (*)(u32))0x0803F279)
#define SoundResume ((void (*)(u32))0x0803F28F)
#define TimersStop ((void (*)(void))0x080401DB)
#define TimersStart ((void (*)(void))0x080401F5)
#define EepromWrite8 ((void (*)(int, const void *))0x08040B5D)
#define IME (*(volatile u16 *)0x04000208)
#define SOUND_OBJ (**(u32 **)0x0803FCA8)
static void eeprom_write(int offset, const void *src, int len) {
    int i;
    Copy(MIRROR + offset, src, len);
    SoundPause(SOUND_OBJ);
    TimersStop();
    IME = 0;
    for (i = 0; i < len; i += 8) EepromWrite8((offset + i) >> 3 & 0xFFFF, (const u8 *)src + i);
    IME = 1;
    TimersStart();
    SoundResume(SOUND_OBJ);
}
void save_write(int *save, int offset, const u8 *src, int len) {
    int slot;
    u32 gen;
    if (!*save) return;
    eeprom_write(offset, src, len);
    if (len != SAVE_BLOCK || offset < 0x10) return;
    slot = (offset - 0x10) / SAVE_BLOCK;
    if (slot > 2 || offset != 0x10 + slot * SAVE_BLOCK) return;
    gen = gen_of(src);
    if (!gen || gen != gen_of(G_BYTES)) return;              /* nothing swapped, or a deleted game */
    bench_ready();
    BENCH.sum = bench_sum(&BENCH);
    if (saved_bench(slot)->magic == BENCH_MAGIC && saved_bench(slot)->gen == gen && saved_bench(slot)->sum == BENCH.sum) return;
    eeprom_write(BENCH_OFFSET + slot * sizeof(struct bench), &BENCH, sizeof(struct bench));
}

struct clash { u8 *p, *e; u32 p_at, e_at, cool, surge; int active, push, start, near_p, near_e, tick; u16 energy[3]; u16 shadow[6]; };
#define CL (*(struct clash *)0x0203F200)

/* The heap's first block, as the game sets it up, a little shorter: the top of work RAM is kept for this code's variables. Only those are cleared, since boot timing is tight. */
void heap_init(void) {
    u16 *block = (u16 *)0x02000800;
    volatile u32 *vars = (volatile u32 *)0x0203FF20;
    int i;
    for (i = 0; i < 24; i++) vars[i] = 0;
    for (i = 0; i < 8; i++) ((volatile u32 *)0x0203FFB0)[i] = 0;     /* Super Saiyan 4's ki bar state, the red Dragon Fist, and the rest to 0x0203FFCF */
    BENCH.magic = 0;
    CL.active = 0; CL.cool = 0; CL.surge = 0; CL.p_at = 0; CL.e_at = 0;
    *(u32 *)0x0203F300 = 0;                /* no bomb sprite */
    ENDLESS_ON = 0; ENDLESS_WINS = 0;
    *(u32 *)0x03003488 = (u32)block;
    block[0] = 0; block[1] = HEAP_WORDS; block[2] = 0;
    *((u8 *)block + 6) = 0;
    block[4] = 0; block[5] = 0;
}

/* Beam clashes. When the player's beam and an enemy's meet head on, both stop at the point where they meet and it becomes a shoving match: A or B pushes,
   the enemy pushes back all the time, and whoever reaches the other's hands wins. The player's beam stays on without holding B and costs no energy meanwhile.
   All beams share one update, so the watch lives there; a beam that stops updating simply stops counting. */
#define Beam_Update ((void (*)(u8 *, int))0x0802084D)
#define PLAYER_OBJ (*(u8 **)0x03001C34)
#define FLAG_BYTE(f) (*(volatile u8 *)(0x03001068 + 0x55 + (f) / 8))
#define ENEMY_VT 0x0804C484
#define NewSpark ((void *(*)(int, int *, const void *, int, int, int, int))0x0802A81D)
#define ListAdd ((void (*)(void *, void *))0x0801191B)
#define ACTORS ((void *)0x03001C4C)
#define Rand ((int (*)(int))0x0803FACD)
#define KEY_A_B 3
#define CLASH_TAP 16
#define CLASH_PULL 1
#define CLASH_WIN 256
#define CLASH_HANDS 20                       /* pixels short of the loser's hands where it ends */
#define CLASH_COOLDOWN 150
#define CLASH_SURGE 60                       /* frames the winning beam keeps going by itself, to reach him */
#define CLASH_ANSWER 48                      /* how close the enemy's tip gets before a charging player's beam fires to meet it */
#define BEAM_STATE(b) ((b)[0x10])
#define BEAM_AXIS(b) (*(int *)((b) + 0x3C) < 2 ? 1 : 0)   /* 0 x, 1 y */
#define BEAM_ORIGIN(b) (*(int *)((b) + 0x20 + 4 * BEAM_AXIS(b)))
#define BEAM_CROSS(b) (*(int *)((b) + 0x20 + 4 * !BEAM_AXIS(b)))
#define BEAM_SIGN(b) (*(int *)((b) + 0x30 + 4 * BEAM_AXIS(b)))
#define BEAM_LEN(b) (*(int *)((b) + 0x38))
#define BEAM_TIP(b) (BEAM_ORIGIN(b) + BEAM_LEN(b) * BEAM_SIGN(b))

static int abs_int(int v) { return v < 0 ? -v : v; }
static u16 *clash_energy(void) { return (u16 *)(RECORDS + *(u8 *)0x03001068 * RECORD_SIZE); }

static void clash_begin(void) {
    u8 *p = CL.p, *e = CL.e, *rec = (u8 *)clash_energy();
    int sign = BEAM_SIGN(p), op = BEAM_ORIGIN(p), oe = BEAM_ORIGIN(e), tp = BEAM_TIP(p), te = BEAM_TIP(e);
    if (BEAM_STATE(p) != 1 || BEAM_STATE(e) != 1 || FRAMES < CL.cool) return;
    if ((*(int *)(p + 0x3C) ^ 1) != *(int *)(e + 0x3C)) return;   /* facing each other: down and up, or left and right */
    if (abs_int(BEAM_CROSS(p) - BEAM_CROSS(e)) > 16) return;
    if ((oe - op) * sign < 2 * CLASH_HANDS + 8) return;           /* point blank: no room for it */
    if ((te - tp) * sign > 24) return;                            /* the tips haven't met. The game's own hit test stops them about this far apart */
    CL.active = 1;
    CL.push = 0;
    CL.tick = 0;
    CL.start = (tp + te) / 2;
    CL.near_p = op + sign * CLASH_HANDS;
    CL.near_e = oe - sign * CLASH_HANDS;
    if ((CL.start - CL.near_p) * sign < 0) CL.start = CL.near_p;
    if ((CL.near_e - CL.start) * sign < 0) CL.start = CL.near_e;
    {   /* a beam may start a little to one side of the other's: line them up so they meet head on */
        int a = BEAM_AXIS(p), line = (BEAM_CROSS(p) + BEAM_CROSS(e)) / 2;
        *(int *)(p + 0x20 + 4 * !a) = line; *(int *)(e + 0x20 + 4 * !a) = line;
    }
    CL.energy[0] = *(u16 *)(rec + 0x1A); CL.energy[1] = *(u16 *)(rec + 0x1E); CL.energy[2] = *(u16 *)(rec + 0x20);
}

static void clash_end(int won) {
    u8 *foe = *(u8 **)(CL.e + 0x50), *me = PLAYER_OBJ;
    CL.active = 0;
    CL.cool = FRAMES + CLASH_COOLDOWN;
    if (won && *(u32 *)foe != ENEMY_VT) {
        /* A rival built on the player's own object, as a versus mode's will be: it stops firing the way the player does. Its damage belongs to that mode. */
        int vt = *(int *)foe;
        ((void (*)(u8 *, int))(*(int *)(vt + 0x28) + vt))(foe, 0);
        CL.surge = FRAMES + CLASH_SURGE;
    } else if (won) {
        /* The enemy's attack runs out as it normally does, which ends its beam safely, and the player's carries on into him. */
        u8 *stats = *(u8 **)(foe + 0x224);
        int hurt = (*(int *)(stats + 4) << 10) / 8, hp = *(int *)(foe + 0x28C);
        *(u16 *)(foe + 0x12) = 0x5B;
        hp -= hurt;
        *(int *)(foe + 0x28C) = hp < (1 << 10) ? (1 << 10) : hp;
        CL.surge = FRAMES + CLASH_SURGE;
    } else {
        /* The player stops firing, as if B had been let go, and the enemy's beam comes through. */
        int vt = *(int *)me;
        ((void (*)(u8 *, int))(*(int *)(vt + 0x28) + vt))(me, 0);
    }
}

static void clash_shove(void) {
    u8 *rec = (u8 *)clash_energy(), *foe = *(u8 **)(CL.e + 0x50);
    if (CL.e_at + 1 < FRAMES || BEAM_STATE(CL.e) != 1) { CL.active = 0; CL.cool = FRAMES + CLASH_COOLDOWN; return; }
    if (KEYS_NEW & KEY_A_B) CL.push += CLASH_TAP;
    CL.push -= CLASH_PULL;
    *(u16 *)(rec + 0x1A) = CL.energy[0]; *(u16 *)(rec + 0x1E) = CL.energy[1]; *(u16 *)(rec + 0x20) = CL.energy[2];
    *(u16 *)(foe + 0x12) = 0x20;           /* his attack's clock waits */
    CL.tick++;
    if (CL.tick % 6 == 0) {
        int a = BEAM_AXIS(CL.p), pos[2], mid = CL.start;
        pos[a] = 0; pos[!a] = BEAM_CROSS(CL.p);
        mid += (CL.push >= 0 ? (CL.near_e - CL.start) * CL.push : (CL.start - CL.near_p) * CL.push) / CLASH_WIN;
        pos[a] = mid + Rand(13) - 6;
        pos[!a] += Rand(13) - 6;
        { void *spark = NewSpark(0, pos, (const void *)0x08712FDC, 4, Rand(0x4000) + 0x1000, 0x400, 0x38); if (spark) ListAdd(ACTORS, spark); }
        PlaySound((void *)0x03003E5C, (void *)(0x083192A8 + (Rand(2) + 0x30) * 12), 0x40, 0);
    }
    if (CL.push >= CLASH_WIN) clash_end(1);
    else if (CL.push <= -CLASH_WIN) clash_end(0);
}

/* A charging player whose beam isn't ready when the enemy's arrives would just be knocked down, since his takes a third of the time. So if the player is facing it,
   in line with it, and it is nearly there, the charge finishes now and the two meet. */
static void clash_answer(u8 *e) {
    u8 *me = PLAYER_OBJ;
    int a = BEAM_AXIS(e), along, across;
    if (CL.p_at + 1 < FRAMES || BEAM_STATE(CL.p) != 0 || FRAMES < CL.cool || !me) return;
    if ((me[0x10] ^ 1) != *(int *)(e + 0x3C)) return;
    along = ((*(int *)(me + 0x1A0 + 4 * a) >> 8) - BEAM_TIP(e)) * BEAM_SIGN(e);
    across = (*(int *)(me + 0x1A0 + 4 * !a) >> 8) - BEAM_CROSS(e);
    if (along < 0 || along > CLASH_ANSWER || abs_int(across) > 16) return;
    if (*(u16 *)(me + 0x12) < 0x17) *(u16 *)(me + 0x12) = 0x17;
}

void beam_update(u8 *b, int arg) {
    int state = BEAM_STATE(b);
    u8 *owner = *(u8 **)(b + 0x50);
    Beam_Update(b, arg);                   /* a beam that finished has freed itself here, so only live ones are touched after */
    if (state == 0 && owner == PLAYER_OBJ) { CL.p = b; CL.p_at = FRAMES; return; }
    if (state != 1) return;
    if (owner == PLAYER_OBJ) { CL.p = b; CL.p_at = FRAMES; }
    else if (owner) { CL.e = b; CL.e_at = FRAMES; clash_answer(b); }     /* any fighter's beam can clash: it needs only to be a beam with an owner other than the player */
    else return;
    if (!CL.active) {
        if (CL.p_at + 1 >= FRAMES && CL.e_at + 1 >= FRAMES) clash_begin();
        if (!CL.active) return;
    }
    if (b == CL.p) clash_shove();
    if (CL.active && (b == CL.p || b == CL.e)) {
        int mid = CL.start + (CL.push >= 0 ? (CL.near_e - CL.start) * CL.push : (CL.start - CL.near_p) * CL.push) / CLASH_WIN;
        BEAM_LEN(b) = abs_int(mid - BEAM_ORIGIN(b));
    }
}

/* The player's keys: during a clash, and as the winning beam surges on, the fire button counts as held, so mashing it doesn't let the beam go. */
void skills_sync(int c);
void *player_input(void) {
    u16 *keys = (u16 *)0x03003300;
    if ((FRAMES & 63) == 0) skills_sync(*(u8 *)0x03001068);       /* what play has earned (outfit.c: the skill book) */
    if (CL.active && CL.p_at + 2 < FRAMES) CL.active = 0;
    if (!CL.active && FRAMES >= CL.surge) return keys;
    CL.shadow[0] = keys[0]; CL.shadow[1] = keys[1] | 2; CL.shadow[2] = 0; CL.shadow[3] = keys[3]; CL.shadow[4] = keys[4]; CL.shadow[5] = keys[5];
    return CL.shadow;
}

static u32 *field(void *obj, int off) { return (u32 *)((u8 *)obj + off); }

static void snapshot(void *obj) {
    int i;
    if (SNAP_OWNER == ((u32)obj ^ SNAP_MAGIC)) return;
    for (i = 0; i < 9; i++) SNAP_FORMS[i] = FORM_OF(i);
    SNAP_OWNER = (u32)obj ^ SNAP_MAGIC;
}

static void cycle(void *obj, int dir) {
    int sel = *field(obj, OBJ_SELECTED), c = *field(obj, OBJ_LIST + sel * 8), i, at = -1, n, first, cur;
    void *sprite = (void *)*field(obj, OBJ_LIST + 4 + sel * 8);
    if (c < 0 || c > 8) return;
    first = outfit_index[c][0]; n = outfit_index[c][1]; cur = FORM_OF(c);
    for (i = 0; i < n; i++) if (outfit_table[first + i].form == cur || outfit_table[first + i].also == cur) at = i;
    if (at < 0 || n < 2) return;       /* transformed or story form: leave it alone */
    for (i = 1; i < n; i++) {
        const struct outfit *o = &outfit_table[first + (at + dir * i + n * 2) % n];
        if (!outfit_open(o)) continue;
        snapshot(obj);
        /* back to the look the screen opened on: its own variant (Goku's halo while he is dead is form 2, the "also" of his gi) */
        FORM_OF(c) = (o->also != 255 && SNAP_FORMS[c] == o->also && c != 8) ? o->also : o->form;
        guest_sync();
        Sprite_SetCharacter(sprite, Form_Sprite((void *)(form_table + FORM_OF(c) * 24)));
        Sprite_SetFacing(sprite, 1);
        Sprite_SetBehaviour(sprite, (void *)0x03001B58);
        PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
        return;
    }
}

#define LABEL_OWNER (*(u32 *)0x0203FF30)
#define LABEL_WIDGET (*(u32 **)0x0203FF34)
#define NewText ((u32 *(*)(void *, void *, int, int, const u16 *, int, int, void *))0x08014125)
#define AddWidget ((void (*)(void *, void *))0x0800664F)
static const u16 no_name[] = {0};

/* The outfit name under the sprites follows the highlighted character. Setting +0x110 to 0 makes the screen redraw. */
static void update_label(void *obj) {
    int sel = *field(obj, OBJ_SELECTED), c = *field(obj, OBJ_LIST + sel * 8), i, first, n;
    const u16 *name = no_name;
    if (LABEL_OWNER != ((u32)obj ^ SNAP_MAGIC)) {
        LABEL_WIDGET = NewText(0, obj, 0x78, 0x70, no_name, 5, 1, (void *)FONT);
        AddWidget(obj, LABEL_WIDGET);
        LABEL_OWNER = (u32)obj ^ SNAP_MAGIC;
    }
    if (c >= 0 && c <= 8) {
        first = outfit_index[c][0]; n = outfit_index[c][1];
        if (n > 1)
            for (i = 0; i < n; i++)
                if (outfit_table[first + i].form == FORM_OF(c) || outfit_table[first + i].also == FORM_OF(c)) name = outfit_table[first + i].name;
    }
    if ((const u16 *)LABEL_WIDGET[5] != name) {
        LABEL_WIDGET[5] = (u32)name;
        *field(obj, 0x110) = 0;
    }
}

/* Scrolling row: the highlighted character sits in the middle, neighbours at one spacing, and the rest off screen. */
#define SCROLL (*(int *)0x0203FF38)
#define SPACING 0x48
#define CENTRE 0x78
#define OBJ_COUNT 0x114
#define SPRITE_X 0x6C

static void scroll_row(void *obj, int first_frame) {
    int sel = *field(obj, OBJ_SELECTED), n = *field(obj, OBJ_COUNT), want = sel * SPACING, i;
    if (first_frame) SCROLL = want;
    if (SCROLL < want) { SCROLL += 8; if (SCROLL > want) SCROLL = want; }
    if (SCROLL > want) { SCROLL -= 8; if (SCROLL < want) SCROLL = want; }
    for (i = 0; i < n; i++) {
        u8 *sprite = (u8 *)*field(obj, OBJ_LIST + 4 + i * 8);
        int x = CENTRE + i * SPACING - SCROLL;
        *(int *)(sprite + SPRITE_X) = (x < 0x28 || x > 0xC8) ? 0x100 : x;
    }
}

/* The story borrows the guest slot for Hercule and Android 18. Afterwards it holds that form, which the guest's outfit list doesn't have,
   so a joined guest comes back in the first outfit it has unlocked when the screen opens. Skipped if that form is the one being played. */
static void restore_borrowed(void *obj) {
    int n = *field(obj, OBJ_COUNT), s, i;
    for (s = 0; s < n; s++) {
        int c = *field(obj, OBJ_LIST + s * 8), first, count, have = 0;
        if (c != 7 && c != 8) continue;
        if (c == *(u8 *)0x03001068) continue;
        first = outfit_index[c][0]; count = outfit_index[c][1];
        for (i = 0; i < count; i++) if (outfit_table[first + i].form == FORM_OF(c) || outfit_table[first + i].also == FORM_OF(c)) have = 1;
        if (have) continue;
        for (i = 0; i < count; i++) {
            const struct outfit *o = &outfit_table[first + i];
            if (!outfit_open(o)) continue;
            FORM_OF(c) = o->form;
            guest_sync();
            Sprite_SetCharacter((void *)*field(obj, OBJ_LIST + 4 + s * 8), Form_Sprite((void *)(form_table + o->form * 24)));
            Sprite_SetFacing((void *)*field(obj, OBJ_LIST + 4 + s * 8), 1);
            Sprite_SetBehaviour((void *)*field(obj, OBJ_LIST + 4 + s * 8), (void *)0x03001B58);
            break;
        }
    }
}

int picker_update(void *obj) {
    int first = LABEL_OWNER != ((u32)obj ^ SNAP_MAGIC), r;
    if (first) restore_borrowed(obj);
    if (first && OUT_FIGHTER) bench_settle(FORM_OF(8));    /* restore_borrowed may have put a different guest on */
    if (KEYS_NEW & KEY_UP) cycle(obj, -1);
    else if (KEYS_NEW & KEY_DOWN) cycle(obj, 1);
    update_label(obj);
    r = orig_update(obj);
    scroll_row(obj, first);
    return r;
}

int picker_input(void *obj, void *widget, int id, int extra) {
    if (id == 0 || id == 1) LABEL_OWNER = 0;
    if ((id == 0 || id == 1) && SNAP_OWNER == ((u32)obj ^ SNAP_MAGIC)) {
        if (id == 1) { int i; for (i = 0; i < 9; i++) FORM_OF(i) = SNAP_FORMS[i]; guest_sync(); }
        else bench_settle(SNAP_FORMS[8]);
        SNAP_OWNER = 0;
    }
    return orig_input(obj, widget, id, extra);
}

/* Great Saiyaman stays a skill. It returns to whichever outfit Gohan wore, so the outfit survives the costume change and saving. */
extern const u8 saiyaman_map[][2];
extern const int saiyaman_count;
int saiyaman_in(int cur) {
    int i;
    for (i = 0; i < saiyaman_count; i++) if (saiyaman_map[i][0] == cur) return saiyaman_map[i][1];
    return 14;
}
int saiyaman_out(int cur) { return form_table[cur * 24 + 0x17]; }
__asm__(
".syntax unified\n.thumb\n.global saiyaman_hook_in, saiyaman_hook_out\n.thumb_func\nsaiyaman_hook_in:\n"
"push {lr}\nldrb r0, [r5, #0x14]\nbl saiyaman_in\nstrb r0, [r5, #0x14]\nmovs r1, #24\nmuls r0, r1\nadds r0, r0, r6\npop {r1}\nadds r1, #5\nbx r1\n"
".thumb_func\nsaiyaman_hook_out:\npush {lr}\nldrb r0, [r5, #0x14]\nbl saiyaman_out\nstrb r0, [r5, #0x14]\nmovs r1, #24\nmuls r0, r1\nadds r0, r0, r6\nldr r2, =0x0801711D\nbl 1f\npop {r1}\nadds r1, #7\nbx r1\n1: bx r2\n.ltorg\n");

/* Charged melee, from Legacy of Goku II: hold A until charged, release for one strong hit. Melee and movement states
   call these wrappers once per frame. The hit reuses the game's melee code with temporarily raised strength. */
#define CHARGE_FRAMES 30
#define CHARGE_COUNT (*(u16 *)0x0203FF3C)
#define CURRENT_CHARACTER (*(u8 *)0x03001068)
#define COMBAT_AREA (*(u32 *)0x03001988)
#define Melee ((void (*)(void *))0x08012A25)
#define SpriteSlot ((void (*)(void *, int))0x0800ECDB)
#define CALL_V(obj, off) ((u32 (*)(void *, ...))(*(u32 *)(obj) + *(int *)(*(u32 *)(obj) + (off))))

static int has_slot(void *player, int slot) {
    u8 *actor = (u8 *)*(u32 *)((u8 *)player + 0x58);
    return (*(u32 *)actor & 0xFF) > (u32)slot && *(u32 *)(actor + 0x54 + slot * 4) != 0;
}

#define SLOT_CHARGE 22
#define SLOT_HIT 23
static int has_slot(void *player, int slot);
static void play_slot(void *player, int slot);
/* Same hit as the game's melee (sub_08012A24), with its 0x400 power value raised. */
#define CHARGED_POWER 0xA00
#define RectAt ((void (*)(void *, const void *, int *))0x08052FD5)
#define HitObjects ((int (*)(void *, int, void *))0x08011C0D)
#define Random ((int (*)(int))0x0803FACD)
#define Quake ((void (*)(int, int))0x0800797D)
static void charged_hit(void *player) {
    u32 hit[16];
    int pos[2], i, *p = (int *)player;
    for (i = 0; i < 16; i++) hit[i] = 0;
    pos[0] = p[0x68] >> 8; pos[1] = p[0x69] >> 8;
    *(u8 *)&hit[0] = 1;
    RectAt(&hit[1], (const u8 *)MELEE_RECTS + *((u8 *)player + 0x10) * 0x10, pos);
    *(u8 *)&hit[5] = *((u8 *)player + 0x10);
    hit[6] = CHARGED_POWER;
    hit[7] = 0x086B8098;
    hit[8] = (u32)player;
    hit[12] = (u32)player;
    if (HitObjects((void *)0x03001C4C, 0, hit)) {
        PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + (Random(2) + 0x30) * 12, 0x40, 0);
        Quake(0xF, 0x4B);
    }
    CALL_V(player, 0x28)(player, 4 + Random(3));
    if (has_slot(player, SLOT_HIT)) play_slot(player, SLOT_HIT);
}


static void play_slot(void *player, int slot) {
    SpriteSlot(player, slot);
    *(u32 *)((u8 *)player + 0x4C) = 0;      /* the halo table has no entries past slot 21 */
    *((u8 *)player + 0x11) = 0;
    *(u16 *)((u8 *)player + 0x12) = 0;
}

/* The arms-raised or LoG2 charge pose, shown while standing still. */
static void charge_pose(void *player) {
    int slot = has_slot(player, SLOT_CHARGE) ? SLOT_CHARGE : 13;
    u8 *actor = (u8 *)*(u32 *)((u8 *)player + 0x58);
    if (!has_slot(player, slot)) return;
    if (*(u32 *)((u8 *)player + 0x50) == *(u32 *)(actor + 0x54 + slot * 4)) return;
    play_slot(player, slot);
}

static void charged_melee(void *player) {
    u8 *input = (u8 *)CALL_V(player, 0x84)(player);
    int held = *(u16 *)(input + 2) & 1, n = CHARGE_COUNT;
    if (!COMBAT_AREA) { CHARGE_COUNT = 0; return; }
    if (held) {
        if (n < 255) CHARGE_COUNT = ++n;
        if (n == CHARGE_FRAMES) PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
        if (n >= CHARGE_FRAMES && !(*(u16 *)(input + 2) & 0xF0)) charge_pose(player);
        return;
    }
    CHARGE_COUNT = 0;
    if (n >= CHARGE_FRAMES) charged_hit(player);
}

typedef void (*state_fn)(void *, void *, int, int);
static int spirit_tick(void *player);
#define WRAP(name, addr) void name(void *s, void *p, int a, int b) { if (spirit_tick(p)) return; charged_melee(p); ((state_fn)(addr))(s, p, a, b); }
WRAP(state_a, 0x08012D8B)
WRAP(state_b, 0x08012DEF)
WRAP(state_c, 0x08013023)
WRAP(state_d, 0x080131BB)


/* Select Game: a save this ROM can't place (say another game's save that the emulator attached) used to stop the game with
   "Unable to find area". Such a slot now reads as empty, so it shows New Game. */
int slot_read(u8 *buffer, int slot)
{
    int result = ((int (*)(u8 *, int))0x080048A1)(buffer, slot);
    if (buffer[1] & 1) {
        const u8 *row = *(const u8 **)0x08008A58;
        int n = ((int (*)(void))0x080125E1)();
        while (n > 0 && (row[0] != buffer[0x8A0] || row[1] != buffer[0x8A1])) { row += 56; n--; }
        if (n <= 0) buffer[1] &= ~1;
    }
    return result;
}

void *slot_area(u8 *buffer)
{
    return ((void *(*)(int, int))0x080089FD)(buffer[0x8A0], buffer[0x8A1]);
}


/* Spirit Bomb (skill 19). Goku holds his arms up while the game's own ending disc grows over his head, then it flies the way he
   faces and bursts, hitting everything nearby hard. It needs no action object: the movement states call spirit_tick each frame.
   The disc takes effect slot 0; whatever was there goes back afterwards. */
#define Enough ((int (*)(void *, int))0x080134B9)
#define Spend ((void (*)(void *, int))0x08013599)
#define NativeDisc ((void (*)(int *))0x08003B95)
#define NativeAlpha ((void (*)(int *))0x08000959)
#define NativeFlash ((void (*)(int *))0x08001305)
#define SetEffect ((void (*)(void *, int, void *))0x0800927F)
#define EFFECTS (*(u32 **)(*(u32 *)0x08003C44 + 0x10))
#define ALPHA_MIRROR (*(u8 **)0x08009900)
struct spirit { u16 frame; u16 phase; int x, y, r; void *old, *old3; u32 ticker[2]; u8 eva, evb; u16 backdrop; u8 dir, speed; u16 travelled; u8 disc; };
extern const int spirit_vt[6];
#define SB (*(struct spirit *)0x0203FF40)
#define GROW_FRAMES 90
#define WINDUP_FRAMES 10
#define THROW_HOLD 22
#define THROW_DISTANCE 130
#define THROW_SIDE 100       /* so the blast's centre stays on screen: it starts over his head, so upward it has less room */
#define THROW_UP 60
#define BURST_FRAMES 24
#define SPIRIT_POWER 0x8000
static const int BURST_RECT[4] = {-100, -80, 200, 160};   /* x, y, width, height */

static int spirit_cost(u8 *rec) { int c = *(u16 *)(rec + 0x1C) / 2; return c < 30 ? 30 : c; }

int spirit_usable(u8 *rec)
{
    if (!COMBAT_AREA || SB.phase) return 0;
    return Enough(rec, spirit_cost(rec));
}

/* The disc is filled with one palette colour, the game's 80 by default, which is pale. Its own entry (BOMB_INDEX) pulses deep blue to pale for the
   bomb's life, and goes back afterwards. */
#define BLDCNT (*(volatile u16 *)0x04000050)
#define BLDY (*(volatile u16 *)0x04000054)
#define BOMB_PAL ((volatile u16 *)0x05000000)[BOMB_INDEX]
#define BOMB_INDEX 255
static u16 *const BOMB_OLD = (u16 *)0x0203FF78;
static void bomb_glow(int frame)
{
    BOMB_PAL = 0x7F80;          /* a steady cyan */
    (void)frame;
}

/* The bomb's sprite. A 64x64 sprite holds one 4 KB frame in OBJ memory: sizes up to 64 across are drawn whole, larger ones as a quarter mirrored four ways.
   build.py writes one frame per 8 pixels of size. If OBJ memory is too full, spirit_draw falls back on the disc. */
#define Alloc ((u32 *(*)(int))0x0803D5B9)
#define MemCopy ((void (*)(void *, const void *, int))0x08049139)
#define FreeMem ((void (*)(void *))0x0803D63D)
#define BOMB_SIZES 12
#define BOMB_TILE_BYTES 0x1000
const u32 bomb_frames[BOMB_SIZES] = {1};
struct bomb_sprite { u8 *actor; int x, y, size, loaded;  int want; };
extern const int bomb_vt[14];
#define BOMB_LIST_REMOVE ((void (*)(void *, void *))0x08011945)
#define OBJ_ALLOC ((int (*)(void *, int))0x0801124D)
#define OBJ_MAKE_ROOM ((void (*)(void *, int))0x08011733)
#define OBJ_FREE ((void (*)(void *, int))0x0801142B)
#define SCREEN_X (*(int *)0x030019BC)
#define SCREEN_Y (*(int *)0x030019C0)
#define OBJ_TILES 0x06010000
#define ACTOR_LIST ((void *)0x03001C4C)
#define Actor_Add ((void (*)(void *, void *))0x0801191B)
#define BS (*(struct bomb_sprite *)0x0203F300)

void bomb_destroy(u8 *actor, int free_it) {
    OBJ_FREE(ACTOR_LIST, *(u16 *)(actor + 0xC));
    if (BS.actor == actor) BS.actor = 0;
    if (free_it) FreeMem(actor);
}
void bomb_nop(void) {}
int bomb_zero(void) { return 0; }
int bomb_one(void) { return 1; }
static u32 *bomb_piece(u32 *oam, const u8 *actor, int x, int y, u32 flips) {
    if (x <= -64 || x >= 240 || y <= -64 || y >= 160) return oam;
    oam[0] = 0xC0002000 | flips | (x & 0x1FF) << 16 | (y & 0xFF);
    oam[1] = (*(u16 *)(actor + 0xC) & 0x3FF) | 3 << 10;
    return oam + 2;
}
int bomb_draw_oam(u8 *actor, u32 **cursor) {
    int x = BS.x - SCREEN_X, y = BS.y - SCREEN_Y;
    u32 *oam = *cursor;
    if (BS.size <= 64) oam = bomb_piece(oam, actor, x - 32, y - 32, 0);
    else {
        oam = bomb_piece(oam, actor, x - 64, y - 64, 0);
        oam = bomb_piece(oam, actor, x, y - 64, 1u << 28);
        oam = bomb_piece(oam, actor, x - 64, y, 1u << 29);
        oam = bomb_piece(oam, actor, x, y, 3u << 28);
    }
    *cursor = oam;
    return 1;
}
static int bomb_show(int x, int y, int r) {
    int k = r / 4 - 1, i;
    if (k < 0) k = 0;
    if (k >= BOMB_SIZES) k = BOMB_SIZES - 1;
    if (!BS.actor) {
        u32 *a = Alloc(0x20);
        int tile;
        if (!a) return 0;
        for (i = 0; i < 8; i++) a[i] = 0;
        tile = OBJ_ALLOC(ACTOR_LIST, BOMB_TILE_BYTES);
        if (tile == -1) { OBJ_MAKE_ROOM(ACTOR_LIST, BOMB_TILE_BYTES); tile = OBJ_ALLOC(ACTOR_LIST, BOMB_TILE_BYTES); }
        if (tile == -1) { FreeMem(a); return 0; }
        a[0] = (u32)bomb_vt;
        *((u8 *)a + 8) = 0x38;
        *(u16 *)((u8 *)a + 0xC) = tile;
        *(u16 *)((u8 *)a + 0xE) = BOMB_TILE_BYTES;
        BS.actor = (u8 *)a;
        BS.loaded = -1; BS.want = k;
        Actor_Add(ACTOR_LIST, a);
    }
    /* OAM changes at the next vblank but tile memory changes at once, so a new picture waits one frame for its layout: the switch to the mirrored quarters would otherwise flash. */
    if (BS.loaded != BS.want) {
        MemCopy((u8 *)OBJ_TILES + *(u16 *)(BS.actor + 0xC) * 0x20, (void *)bomb_frames[BS.want], BOMB_TILE_BYTES);
        BS.loaded = BS.want;
    }
    BS.want = k;
    BS.x = x; BS.y = y; BS.size = (k + 1) * 8;
    ((int *)BS.actor)[1] = y;
    return 1;
}
static void bomb_hide(void) {
    if (BS.actor) BOMB_LIST_REMOVE(ACTOR_LIST, BS.actor);
    BS.actor = 0;
}

static void spirit_draw(void)
{
    if (SB.phase < 3 && bomb_show(SB.x, SB.y, SB.r)) return;
    if (!SB.disc) {                 /* the disc takes effect slot 0; whatever was there goes back afterwards. An empty slot can't wait: the game calls every slot it thinks is in use */
        int st[3] = {2, 100, 15};
        SB.disc = 1;
        SB.old = (void *)EFFECTS[0];
        EFFECTS[0] = 0;
        SB.eva = ALPHA_MIRROR[2]; SB.evb = ALPHA_MIRROR[3]; SB.backdrop = BOMB_PAL;
        NativeAlpha(st);
    }
    {
        int st[5] = {4, SB.x, SB.y, SB.r, BOMB_INDEX};
        NativeDisc(st);
        bomb_glow(SB.frame);
        if (SB.phase == 3) bomb_show(SB.x, SB.y, SB.r > 48 ? 48 : SB.r);      /* the orb stays as the bright heart of the blast */
    }
}

/* Script native bomb_at(x, y, r): the story's Spirit Bomb, drawn the same way. */
void bomb_at(int *sp)
{
    int n = *sp, x = sp[n - 2], y = sp[n - 1], r = sp[n];
    *sp = n - 3;
    if (!bomb_show(x, y, r)) { int st[5] = {4, x, y, r, BOMB_INDEX}; NativeDisc(st); bomb_glow(0); }
}

/* Impact frames: the whole screen white, black, then white, a few frames each. Keep BLDCNT's other bits for afterwards. */
static void impact(int step)
{
    if (step == 0) { *BOMB_OLD = BLDCNT; }
    if (step < 3 || (step >= 6 && step < 9)) { BLDCNT = 0x00BF; BLDY = 16; }
    else if (step < 6) { BLDCNT = 0x00FF; BLDY = 16; }
    else { BLDCNT = *BOMB_OLD; BLDY = 0; }
}

#define SLOT_ARMS_UP 12
#define SLOT_THROW 18      /* the pose held while firing a skill: slot 8 only has a front view */
static void slot_pose(void *player, int slot) {
    u8 *actor = (u8 *)*(u32 *)((u8 *)player + 0x58);
    if (!has_slot(player, slot)) return;
    if (*(u32 *)((u8 *)player + 0x50) == *(u32 *)(actor + 0x54 + slot * 4)) return;
    play_slot(player, slot);
}

/* Script native bomb_fx(n) for the story's Spirit Bomb: 1 glow on, 0 glow off, 2 one frame of the impact sequence starting over */
void bomb_fx(int *sp)
{
    int n = *sp, v = sp[n];
    if (v == 1) {
        void *player = *(void **)0x03001C34;
        if (!SB.phase) SB.phase = 9;
        SB.frame++; bomb_glow(SB.frame);
        if (player) slot_pose(player, SLOT_ARMS_UP);
    }
    else if (v == 0) { SB.phase = 0; BLDY = 0; bomb_hide(); }      /* the next room reloads the palette; restoring it here would turn the disc dull during the fade */
    else { impact(v - 2); }
    *sp = n - 1;
}

static void spirit_end(void)
{
    bomb_hide();
    if (SB.disc) {
        /* The disc stays on screen for one more frame after its slot goes back, so its colour must wait or it shows as whatever the map keeps in that entry. */
        SetEffect(EFFECTS, 0, SB.old);
        ALPHA_MIRROR[2] = SB.eva; ALPHA_MIRROR[3] = SB.evb;
        SB.disc = 2;
    }
    SB.phase = 4; SB.frame = 0;
}

static void spirit_done(void)
{
    if (SB.disc == 2) BOMB_PAL = SB.backdrop;
    SB.disc = 0;
    SB.phase = 0;
    EFFECTS[3] = SB.old3;
    { int st[6] = {5, 5, 200, 200, 255, 10}; NativeFlash(st); }      /* takes an effect slot itself, so only once the bomb has let go */
}

const int bomb_vt[14] = {1};
const int spirit_vt[6] = {0x53A1, 0x53A2, 0x53A3, 0x53A4, 0x53A5, 0x53A6};   /* offsets from itself, filled in by build.py */

void spirit_use(u8 *rec, void *player)
{
    int *p = (int *)player;
    Spend(rec, spirit_cost(rec));
    SB.disc = 0;
    SB.x = p[0x68] >> 8; SB.y = (p[0x69] >> 8) - 58; SB.r = 4;
    SB.frame = 0; SB.phase = 1;
    SB.old3 = (void *)EFFECTS[3];
    SB.ticker[0] = (u32)spirit_vt;
    EFFECTS[3] = (u32)SB.ticker;
    PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
    spirit_draw();
}

static void spirit_burst(void *player)
{
    u32 hit[16];
    int pos[2], i;
    for (i = 0; i < 16; i++) hit[i] = 0;
    pos[0] = SB.x; pos[1] = SB.y;
    *(u8 *)&hit[0] = 1;
    RectAt(&hit[1], BURST_RECT, pos);
    *(u8 *)&hit[5] = *((u8 *)player + 0x10);
    hit[6] = SPIRIT_POWER;
    hit[7] = 0x086B8098;
    hit[8] = (u32)player;
    hit[12] = (u32)player;
    HitObjects((void *)0x03001C4C, 0, hit);
    Quake(0x20, 0x4B);
    PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x30 * 12, 0x40, 0);
}

/* The bomb keeps going even if Goku is knocked about, so it runs from an effect slot, which the game updates every frame. */
void spirit_nop(void) {}

/* Android 13 and Android 17 transform with Super Saiyan's mechanics, then the white flash from Gero's Legacy: a quick strobe, hold white, fade. It shares the bomb's effect slot, so the two never overlap. */
#define WAIT_PHASE 10
#define FLASH_PHASE 11
static const u8 flash_levels[46] = {6, 12, 16, 16, 16, 16, 10, 4, 0, 8, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 15, 14, 14, 13, 12, 12, 11, 10, 10, 9, 8, 8, 7, 6, 6, 5, 4, 4, 3, 2, 2, 1, 0};
#define SS_Can ((int (*)(u8 *))0x0801A4C5)
/* Android 13's power-up is Super Saiyan's without the gold aura, which would hide the two cores he is pulling in. */
const int absorb_vt[14] = {1};
void absorb_start(u32 *state, void *sprite) {
    state[2] = 0; state[3] = 0;
    ((void (*)(void *, void *))0x0800DE61)(state, sprite);
    PlaySound((void *)0x03003E5C, (u8 *)*(u32 *)0x0801C6A4 + 0x288, 0x40, 0);      /* the power-up's own sound, as the state it replaces finds it */
}
/* Goku Black becoming Rose: Super Saiyan's power-up with its aura in Rose's pink. The start is the game's (0x0801C3EC) with the aura's frames swapped;
   build.py fills the frames (the field's three and the other mode's seven, recoloured) and the rest of the state's methods. */
const u32 rose_aura_field[9] = {1}, rose_aura_other[21] = {1};
const int rose_vt[14] = {1};
/* Super Saiyan 4 (Kid Goku's, GT Vegeta's): the same power-up with the aura red */
const u32 ssj4_aura_field[9] = {1}, ssj4_aura_other[21] = {1};
const int ssj4_vt[14] = {1};
/* Super Saiyan Blue: the same power-up with the aura blue */
const u32 ssb_aura_field[9] = {1}, ssb_aura_other[21] = {1};
const int ssb_vt[14] = {1};
#define SpriteBox ((void (*)(int *, void *))0x0800FDFB)
#define VecOp ((void (*)(int *, const int *, const int *))0x08052FB5)
#define AURA_MODE (*(volatile u8 *)0x03002BB0)
static void tinted_start(u32 *state, void *sprite, const u32 *aura_field, const u32 *aura_other) {
    int box[4], v[2], u[2], w[2], pos[2];
    u32 *spark;
    state[2] = 0;
    ((void (*)(void *, void *))0x0800DE61)(state, sprite);
    PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x288, 0x40, 0);
    state[3] = 0;
    if (AURA_MODE > 1) return;
    SpriteBox(box, sprite); VecOp(v, box, box + 2);
    u[0] = v[0] >> 1; u[1] = v[1] >> 1; w[0] = 0; w[1] = AURA_MODE ? 2 : 1;
    VecOp(pos, u, w);
    if (AURA_MODE) { ListAdd(ACTORS, NewSpark(0, pos, aura_other, 7, 0xC88, 1024, 0x38)); return; }
    spark = Alloc(0x48);
    if (spark) { NewSpark((int)spark, pos, aura_field, 3, 0x4000, 1024, 0x38); spark[0] = 0x0804B9E0; spark[0x44 / 4] = (u32)aura_field; }
    state[3] = (u32)spark;
    ListAdd(ACTORS, spark);
}
void rose_start(u32 *state, void *sprite) { tinted_start(state, sprite, rose_aura_field, rose_aura_other); }
void ssj4_start(u32 *state, void *sprite) { tinted_start(state, sprite, ssj4_aura_field, ssj4_aura_other); }
void ssb_start(u32 *state, void *sprite) { tinted_start(state, sprite, ssb_aura_field, ssb_aura_other); }
void rose_use(u8 *record, void *sprite) {
    if (!(form_table[record[0x14] * 24] & 1)) {
        u32 *state = Alloc(0x10);
        if (state) { *(u8 *)&state[1] = 4; state[0] = (u32)rose_vt; }
        Sprite_SetFacing(sprite, 10);
        Sprite_SetBehaviour(sprite, state);
    }
    else ((void (*)(u8 *, void *))0x0801A513)(record, sprite);
}
int super_can(u8 *record) { return SB.phase ? 0 : SS_Can(record); }
void super_use(u8 *record, void *sprite) {
    if (!(form_table[record[0x14] * 24] & 1)) {
        SB.phase = WAIT_PHASE; SB.frame = 0; SB.disc = 0;
        SB.old3 = (void *)EFFECTS[3];
        SB.ticker[0] = (u32)spirit_vt;
        EFFECTS[3] = (u32)SB.ticker;
    }
    if (record[0x14] == FORM_A13) {
        u32 *state = Alloc(0x10);
        if (state) { *(u8 *)&state[1] = 4; state[0] = (u32)absorb_vt; }
        play_slot(sprite, 10);
        Sprite_SetBehaviour(sprite, state);
        return;
    }
    ((void (*)(u8 *, void *))0x0801A513)(record, sprite);
}

void spirit_update(void)
{
    void *player = *(void **)0x03001C34;
    SB.frame++;
    if (SB.phase == 1) {
        if (SB.r < 48 && SB.frame % 2 == 0) SB.r++;
        spirit_draw();
        if (SB.frame >= GROW_FRAMES) { SB.phase = 2; SB.frame = 0; SB.dir = *((u8 *)player + 0x10); SB.speed = 0; SB.travelled = 0; }
    } else if (SB.phase == 2) {
        /* The throw: the bomb rises a little over the raised arms, then goes the way Goku faced, picking up speed until it lands. */
        if (SB.frame <= WINDUP_FRAMES) SB.y -= 1;
        else {
            if (SB.speed < 7 && SB.frame % 3 == 0) SB.speed++;
            if (SB.dir == 0) SB.y += SB.speed; else if (SB.dir == 1) SB.y -= SB.speed; else if (SB.dir == 2) SB.x -= SB.speed; else SB.x += SB.speed;
            SB.travelled += SB.speed;
        }
        spirit_draw();
        if (SB.travelled >= (SB.dir == 1 ? THROW_UP : SB.dir == 0 ? THROW_DISTANCE : THROW_SIDE)) { spirit_burst(player); SB.phase = 3; SB.frame = 0; }
    } else if (SB.phase == 3) {
        if (SB.frame > BURST_FRAMES - 10) SB.r -= 8;      /* the blast collapses at the end instead of blinking out */
        else if (SB.r < 96) SB.r += 4;                    /* much larger than this hangs the disc code */
        spirit_draw();
        if (SB.frame <= 10) impact(SB.frame - 1);
        if (SB.frame % 6 == 0) spirit_burst(player);      /* it keeps hitting as it bursts */
        if (SB.frame >= BURST_FRAMES) spirit_end();
    } else if (SB.phase == 4) {
        if (SB.frame >= 2) spirit_done();
    } else if (SB.phase == WAIT_PHASE) {
        /* Waiting for the power-up to finish: the white flash starts on the frame the form changes. */
        if (form_table[FORM_OF(*(u8 *)0x03001068) * 24] & 1) { SB.phase = FLASH_PHASE; SB.frame = 0; *BOMB_OLD = BLDCNT; }
        else if (SB.frame > 240) { SB.phase = 0; EFFECTS[3] = SB.old3; }
    } else if (SB.phase == FLASH_PHASE) {
        if (SB.frame > (int)sizeof flash_levels) { BLDCNT = *BOMB_OLD; BLDY = 0; SB.phase = 0; EFFECTS[3] = SB.old3; }
        else { BLDCNT = 0x00BF; BLDY = flash_levels[SB.frame - 1]; }
    }
}

void spirit_destroyed(void) {
    if (SB.phase == FLASH_PHASE) { BLDCNT = *BOMB_OLD; BLDY = 0; }
    SB.phase = 0; SB.disc = 0; BS.actor = 0;
}     /* a new area clears every effect, this one included */

/* Non-zero while Goku is busy with the bomb: the state's normal update is skipped so he stands still. */
static int spirit_tick(void *player)
{
    if (SB.phase == 1) { slot_pose(player, SLOT_ARMS_UP); return 1; }     /* the arms-up pose of the Kid Buu fight */
    if (SB.phase == 2) {
        if (SB.frame <= WINDUP_FRAMES) { slot_pose(player, SLOT_ARMS_UP); return 1; }
        if (SB.frame <= WINDUP_FRAMES + THROW_HOLD) { slot_pose(player, SLOT_THROW); return 1; }
        if (SB.frame == WINDUP_FRAMES + THROW_HOLD + 1) slot_pose(player, 0);      /* back to standing, still facing the same way */
    }
    return 0;
}

/* Script native add_zenie(amount): the World Tournament's prize. */
void add_zenie(int *sp) {
    int n = *sp;
    *(u32 *)0x0300155C += sp[n];
    *sp = n - 1;
}

/* Script native: which Dragon Ball lives in this room, plus one; 0 anywhere else. */
void ball_here(int *sp) {
    static const u16 areas[7] = BALL_AREAS;
    int i, v = 0, now = *(u32 *)0x0300197C & 0xFFFF;
    for (i = 0; i < 7; i++) if (areas[i] == now) v = i + 1;
    *sp += 1; sp[*sp] = v;
}

/* Script native: the wish for greater power. Every fighter who has joined gains 5 in each stat. */
void wish_power(int *sp) {
    int c, i;
    (void)sp;
    for (c = 0; c < 9; c++) {
        u8 *r = RECORDS + c * RECORD_SIZE;
        if (!(r[0] & 1)) continue;
        for (i = 0x28; i < 0x2C; i++) r[i] = r[i] > 250 ? 255 : r[i] + 5;
        Recalculate(r);
    }
}

/* World Tournament bracket: each round's opponent lives in three story flags, kept with the save. */
void tour_pick(int *sp) {
    int n = *sp, round = sp[n - 1], place = sp[n], i;
    for (i = 0; i < 3; i++) {
        int f = TOUR_PICK_FLAG + 3 * round + i;
        if (place >> i & 1) FLAG_BYTE(f) |= 1 << (f % 8);
        else FLAG_BYTE(f) &= ~(1 << (f % 8));
    }
    *sp = n - 2;
}
void tour_get(int *sp) {
    int n = *sp, round = sp[n], place = 0, i;
    for (i = 0; i < 3; i++) {
        int f = TOUR_PICK_FLAG + 3 * round + i;
        place |= (FLAG_BYTE(f) >> (f % 8) & 1) << i;
    }
    sp[n] = place;
}

/* Trailer build only: push a warp's arguments (world, area, 1, x, y) from RAM a filming script pokes. */
void trailer_warp(int *sp) {
    int n = *sp, i;
    for (i = 0; i < 5; i++) sp[n + 1 + i] = ((volatile int *)0x0203FF60)[i];
    *sp = n + 5;
}

void trailer_slot(int *sp) {
    int n = *sp;
    sp[n + 1] = ((volatile int *)0x0203FF60)[5];
    *sp = n + 1;
}

/* Script native party_join(character, form). The first time a post-game character joins, they start level with whoever is playing, leaning towards
   how they fight, with their own skills. Later calls change nothing, so an outfit chosen earlier stays on. */
#define REC(c) (RECORDS + (c) * RECORD_SIZE)
#define R16(r, o) (*(u16 *)((r) + (o)))
#define EXP(r) (*(u32 *)((r) + 0x24))
static const u8 gogeta_skills[] = {5, 7, 3, 5, 20, SSB_SKILL};     /* count, his own three, Super Saiyan, Super Saiyan Blue */
static int scale(int v, int pct) { v = v * pct / 100; return v > 255 ? 255 : v; }
void party_join(int *sp) {
    int n = *sp, form = sp[n], c = sp[n - 1], i;
    u8 *r = REC(c), *cur = REC(*(u8 *)0x03001068);
    const u8 *skills = gogeta_skills;
    static const u8 lean[2][3] = {{110, 110, 110}, {120, 85, 110}};    /* strength, power, endurance: Gogeta, Broly */
    const u8 *l = lean[c == 8];
    *sp = n - 2;
    if (r[0] & 1) return;
    r[0] |= 1;
    FORM_OF(c) = form;
    if (EXP(cur) > EXP(r)) EXP(r) = EXP(cur);
    if (R16(cur, 0x18) > R16(r, 0x18)) R16(r, 0x18) = R16(cur, 0x18);
    if (R16(cur, 0x1C) > R16(r, 0x1C)) R16(r, 0x1C) = R16(cur, 0x1C);
    R16(r, 0x16) = R16(r, 0x18); R16(r, 0x1A) = R16(r, 0x1C);
    for (i = 0; i < 3; i++) {
        int v = scale(cur[0x28 + i], l[i]);
        if (v > r[0x28 + i]) r[0x28 + i] = v;
    }
    if (cur[0x2C] > r[0x2C]) r[0x2C] = cur[0x2C];   /* unspent stat points */
    if (c != 8) {
        r[0x0C] = skills[0];
        for (i = 0; i < skills[0]; i++) r[0x0D + i] = skills[1 + i];
    }
    r[0x15] = 0;
    guest_sync();
}

/* Eraser Cannon and SS Deadly Bomber: Big Bang's code with their own frames and strength. Big Bang's start makes the ball from its parameter table, so this runs it,
   then points the ball at the same entry of the move's table (the last word of an entry scales the damage). */
#define BigBang_Start ((void (*)(u32 *, void *))0x0801A7C1)
#define Alloc ((u32 *(*)(int))0x0803D5B9)
const u32 eraser_params[12] = {1}, bomber_params[12] = {1}, blitz_params[12] = {1}, disc_params[12] = {1};   /* build.py fills these */
const int eraser_vt[9] = {1}, bomber_vt[9] = {1}, blitz_vt[9] = {1}, disc_vt[9] = {1};
static void ball_start(u32 *self, void *player, const u32 *table) {
    u32 *ball;
    BigBang_Start(self, player);
    ball = (u32 *)self[1];
    if (ball) {
        const u32 *mine = &table[self[2] * 4];
        u32 *old = (u32 *)ball[0x4C / 4];
        int shift = (int)mine[2] - (int)old[2];
        ball[0x4C / 4] = (u32)mine;
        ball[0x50 / 4] += shift;
        ball[0x18 / 4] += shift;
    }
}
static void ball_use(u8 *record, void *sprite, const int *vt) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x14);
    if (b) { b[0] = (u32)vt; b[2] = level; b[3] = 0; b[4] = 0; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}
void blitz_start(u32 *self, void *player) { ball_start(self, player, blitz_params); }
void disc_start(u32 *self, void *player) {     /* a thrown disc flies six times as fast as Big Bang's slow ball */
    ball_start(self, player, disc_params);
    if (self[1]) { u32 *ball = (u32 *)self[1]; ball[0x44 / 4] *= 6; ball[0x48 / 4] *= 6; }
}
void eraser_start(u32 *self, void *player) { ball_start(self, player, eraser_params); }
void bomber_start(u32 *self, void *player) { ball_start(self, player, bomber_params); }
void blitz_use(u8 *record, void *sprite) { ball_use(record, sprite, blitz_vt); }
void disc_use(u8 *record, void *sprite) { ball_use(record, sprite, disc_vt); }
void eraser_use(u8 *record, void *sprite) { ball_use(record, sprite, eraser_vt); }
void bomber_use(u8 *record, void *sprite) { ball_use(record, sprite, bomber_vt); }

/* Special Beam Cannon: the Kamehameha's code with its own frames, the same way. */
#define MemCopy ((void (*)(void *, const void *, int))0x08049139)
#define Kamehameha_Start ((void (*)(u32 *, void *))0x0801BDD5)
const u32 beam_params[12] = {1};
const int beam_vt[9] = {1};
void beam_start(u32 *self, void *player) {
    u32 *beam;
    Kamehameha_Start(self, player);
    beam = (u32 *)self[2];
    if (beam) {                                /* the charging ball's frames, and its first frame already copied to VRAM */
        const u32 *mine = &beam_params[self[3] * 4];
        beam[0x40 / 4] = (u32)mine;
        beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = mine[2];
        MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (void *)((u32 *)mine[2])[2], 0x40);
    }
}
void beam_use(u8 *record, void *sprite) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)beam_vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}

/* The Black Kamehameha: the Kamehameha's code with Black's purple frames, or Rose's pink ones. */
const u32 black_params[12] = {1}, rose_params[12] = {1};
const int black_kame_vt[9] = {1};
void black_kame_start(u32 *self, void *player) {
    u32 *beam;
    Kamehameha_Start(self, player);
    beam = (u32 *)self[2];
    if (beam) {
        const u32 *mine = &(FORM_OF(8) == FORM_ROSE ? rose_params : black_params)[self[3] * 4];
        beam[0x40 / 4] = (u32)mine;
        beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = mine[2];
        MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (void *)((u32 *)mine[2])[2], 0x40);
    }
}
void black_kame_use(u8 *record, void *sprite) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)black_kame_vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}

/* More beams on the Kamehameha's code, each with its own frames and strength (build.py KAME_VARIANTS): Vegeta's Galick Gun (violet) and
   Super Saiyan 4's 10x Kamehameha (red). The behaviour is 0x10 bytes as the retail one; +12 is the skill level. */
#define KV_COUNT 3
const u32 kv_params[KV_COUNT][12] = {{1}};
const int kv_vt[KV_COUNT][9] = {{1}};
static void kv_begin(u32 *self, void *player, const u32 *params) {
    u32 *beam;
    Kamehameha_Start(self, player);
    beam = (u32 *)self[2];
    if (beam) {
        const u32 *mine = &params[self[3] * 4];
        beam[0x40 / 4] = (u32)mine;
        beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = mine[2];
        MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (void *)((u32 *)mine[2])[2], 0x40);
    }
}
static void kv_use(u8 *record, void *sprite, const int *vt) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}
void galick_start(u32 *self, void *player) { kv_begin(self, player, kv_params[0]); }
void galick_use(u8 *record, void *sprite) { kv_use(record, sprite, kv_vt[0]); }
void tenx_start(u32 *self, void *player) { kv_begin(self, player, kv_params[1]); }
void tenx_use(u8 *record, void *sprite) { kv_use(record, sprite, kv_vt[1]); }
void superkame_start(u32 *self, void *player) { kv_begin(self, player, kv_params[2]); }
void superkame_use(u8 *record, void *sprite) { kv_use(record, sprite, kv_vt[2]); }
/* Goku's Kamehameha counts its uses at its top level towards the Super Kamehameha (skills_sync) */
static int derived_level(int c, int skill);
#define MASTERY_BYTES ((u8 *)BENCH.e[GROUPS - 1].gear)
void kame_use(u8 *record, void *sprite) {
    if (record == RECORDS && derived_level(0, 15) == 2 && MASTERY_BYTES[21] < 255) MASTERY_BYTES[21]++;
    ((void (*)(u8 *, void *))0x0801A35B)(record, sprite);
}
static int is_ssj4(int form);
/* Final Shine: Final Flash's code (behaviour 0x0804D9D4) firing a green beam. Its update (0x0801B4EC) makes the beam on its 24th frame
   (0x08036FA2, which reads the level's row of 0x0876174C: frames, 8, damage); ours then points the beam at our rows and redraws it.
   The behaviour is allocated 0x14 bytes so +0x10 can mark the switch done. */
const u32 shine_params[9] = {1};
const int shine_vt[9] = {1};
#define FinalFlash_Update ((void (*)(u32 *, int *))0x0801B4ED)
#define Beam_Frame ((void (*)(u32 *))0x08036F6D)
void shine_update(u32 *self, int *player) {
    u32 *beam;
    FinalFlash_Update(self, player);
    beam = (u32 *)self[1];
    if (beam && !self[4]) {
        const u32 *mine = &shine_params[self[3] * 3];
        beam[0x10] = (u32)mine; beam[0xF] = mine[0] + beam[0xE] * 0x18;
        Beam_Frame(beam);
        self[4] = 1;
    }
}
void shine_use(u8 *record, void *sprite) {
    u32 *b = Alloc(0x14);
    if (b) { b[0] = (u32)shine_vt; b[1] = b[2] = b[4] = 0; b[3] = record[record[0x15] * 2 + 0x2E]; }
    Sprite_SetFacing(sprite, 0x13);
    Sprite_SetBehaviour(sprite, b);
}
#define FlashCan ((int (*)(u8 *))0x0801A0AB)
int ssj4_flash_can(u8 *record) { return is_ssj4(record[0x14]) && FlashCan(record); }       /* Final Shine: Super Saiyan 4 only */
/* Super Saiyan 4's Dragon Fist: Dragon Fist's code (behaviour 0x0804D9B0) with a red dragon, hitting 1.25x as hard. Its update
   (0x0801ABBE) makes the dragon on its 16th frame (0x08038AD8: a head and five segments chained through +0x48, each showing its rows of
   0x0877AD10 through +0x5C and +0x18); ours moves each segment onto the red rows. +0x10 marks it done (0x14 bytes allocated). */
const u32 red_dragon[48] = {1};
const int dragon4_vt[9] = {1};
#define dragon4_live (*(u32 *volatile *)0x0203FFB8)      /* the red Dragon Fist in play, for combat_hook (after SK) */
#define DragonFist_Update ((void (*)(u32 *, int *))0x0801ABBF)
#define DragonFist_End ((void (*)(u32 *))0x0801AB97)
#define DragonFist_Can ((int (*)(u8 *))0x08019E9F)
#define Segment_Refresh ((void (*)(u32 *))0x08019B4F)
#define DRAGON_ROWS 0x0877AD10
#define DRAGON4_COST 45
#define CanAfford ((int (*)(u8 *, int))0x080134B9)
void dragon4_update(u32 *self, int *player) {
    u32 *seg;
    DragonFist_Update(self, player);
    if (self[1] && !self[4]) {
        for (seg = (u32 *)self[1]; seg; seg = (u32 *)seg[0x12]) {
            if (seg[0x17] >= DRAGON_ROWS && seg[0x17] < DRAGON_ROWS + 0xC0) seg[0x17] = (u32)red_dragon + (seg[0x17] - DRAGON_ROWS);
            if (seg[6] >= DRAGON_ROWS && seg[6] < DRAGON_ROWS + 0xC0) seg[6] = (u32)red_dragon + (seg[6] - DRAGON_ROWS);
            Segment_Refresh(seg);
        }
        self[4] = 1;
    }
    dragon4_live = self;
}
void dragon4_end(u32 *self) { if (dragon4_live == self) dragon4_live = 0; DragonFist_End(self); }
void dragon4_use(u8 *record, void *sprite) {
    u32 *b = Alloc(0x14);
    if (b) { b[0] = (u32)dragon4_vt; b[1] = b[2] = b[3] = b[4] = 0; }
    Spend(record, DRAGON4_COST);         /* from the form's own pool: Super Saiyan 4's holds 90, where retail's 300 comes from the EP bar */
    Sprite_SetFacing(sprite, 0x13);
    Sprite_SetBehaviour(sprite, b);
}
int ssj4_dragon_can(u8 *record) { return is_ssj4(record[0x14]) && CanAfford(record, DRAGON4_COST); }
#define KameCan ((int (*)(u8 *))0x0801A335)
static int is_ssj4(int form);
int ssj4_kame_can(u8 *record) { return is_ssj4(record[0x14]) && KameCan(record); }     /* 10x Kamehameha: Super Saiyan 4 only */

/* Full Power Energy Wave, for the androids: the Electric Kamehameha's code with green frames, as in Gero's Legacy. Gohan keeps the original. */
#define Wave_Start ((void (*)(u32 *, void *))0x0801ADA9)
const u32 wave_params[12] = {1};
const int wave_vt[9] = {1};
void wave_start(u32 *self, void *player) {
    u32 *beam;
    Wave_Start(self, player);
    beam = (u32 *)self[2];
    if (beam) {
        const u32 *mine = &wave_params[self[3] * 4];
        beam[0x40 / 4] = (u32)mine;
        beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = mine[2];
        MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (void *)((u32 *)mine[2])[2], 0x40);
    }
}
void wave_use(u8 *record, void *sprite) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)wave_vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, 0x12);
    Sprite_SetBehaviour(sprite, b);
}

/* The androids' ki blasts are blue, also as in Gero's Legacy. Enemies and everyone else keep the game's. The impact burst stays as it is. */
const u8 blue_blast[192] = {1};            /* build.py fills this: the blast's frame table, pointing at blue tiles */
const u8 black_blast[192] = {1}, rose_blast[192] = {1};      /* Goku Black's purple and Rose's pink, the same way */
const u8 *blast_frames(int facing) {
    const u8 *frames = (const u8 *)0x0871370C;
    if (*(u8 *)0x03001068 == 8) {
        int form = FORM_OF(8);
        if (form == FORM_A13 || form == FORM_S13 || form == FORM_ANDROID17 || form == FORM_S17 || form == FORM_ANDROID18) frames = blue_blast;
        else if (form == FORM_BLACK) frames = black_blast;
        else if (form == FORM_ROSE) frames = rose_blast;
    }
    return frames + facing * 48;
}
__asm__(
".syntax unified\n.thumb\n.global blast_hook\n.thumb_func\nblast_hook:\n"
"ldrb r0, [r4, #0x10]\npush {r0}\nbl blast_frames\nadds r1, r0, #0\npop {r0}\nstr r1, [r4, #0x50]\n"         /* the code after this still uses r0 facing, r1 frames and r2 the table */
"lsls r2, r0, #1\nadds r2, r2, r0\nlsls r2, r2, #4\nsubs r2, r1, r2\nldr r3, =0x08019801\nbx r3\n.ltorg\n");

/* Super Saiyan 2 sits between Super Saiyan and the next form with no skill of its own (a character holds six at most): pressing Super Saiyan again goes up to it.
   Forms chain through the table's up: a Super Saiyan form whose up is also Super Saiyan-class (flag bit 0) has SS2 above it. */
#define SS_Use ((void (*)(u8 *, void *))0x0801A513)
#define SS3_Use ((void (*)(u8 *, void *))0x0801A5BD)
#define SS3_Can ((int (*)(u8 *))0x0801A55F)
extern const u8 ss2_rows[];
static int is_ss2(int form) {
    const u8 *p;
    for (p = ss2_rows; *p != 255; p++) if (*p == form) return 1;
    return 0;
}
/* The story sets SS2_FLAG + owner when that character reaches it. Goku learns Super Saiyan 3 in the same scene, so a save made after it counts too. */
static int ss2_open(const u8 *record, int owner) {
    int i;
    if (GetFlag((void *)0x03001068, SS2_FLAG + owner)) return 1;
    for (i = 0; i < record[0x0C]; i++) if (record[0x0D + i] == 22) return 1;
    return 0;
}
static void power_up(void *sprite, const void *vt);
static int is_ssj4(int form);
static void ssj4_pending(const u8 *record);
static int is_kaioken(int form);
/* Each tier is its own skill (Nov 9): Super Saiyan (20) powers up from base and back down from any Super Saiyan class form; Super Saiyan 2
   (SS2_SKILL), 3 (22), 4 (SS4_SKILL) and Blue (SSB_SKILL) each go up from the tier below, and pressed in their own form power down.
   None of them works in Kaioken, and Kaioken works only in a base form. A form's up (row +0x16) is the tier above it; Kaioken and Goku's
   and Vegeta's Super Saiyan Blue aren't up anywhere, so their skills ask sub_0801C312 for their form through XFORM (xform_target). */
#define IN_COMBAT (*(volatile u32 *)0x03001988)
#define XFORM (*(volatile u8 *)0x0203FFBC)            /* form + 1 the next power-up ends in, or 0 */
#define XFORM_FROM (*(volatile u8 *)0x0203FFBD)       /* the form it was pressed in */
#define XFORM_AT (*(volatile u16 *)0x0203FFBE)        /* and when (frame counter's low half) */
#define FRAMES (*(volatile u32 *)0x03000F94)
static int flags_of(int form) { return form_table[form * 24]; }
static int up_of(int form) { return form_table[form * 24 + 0x16]; }
static void power_down(u8 *record, void *sprite) {             /* the retail way out of the form's class */
    if (flags_of(record[0x14]) & 2) SS3_Use(record, sprite); else SS_Use(record, sprite);
}
static void power_to(u8 *record, void *sprite, int form, const void *vt) {
    XFORM = form + 1; XFORM_FROM = record[0x14]; XFORM_AT = FRAMES;
    power_up(sprite, vt);
}
int xform_target(int up, u8 *record) {                          /* sub_0801C312's new form */
    int t = XFORM;
    XFORM = 0;
    if (t && record[0x14] == XFORM_FROM && (u16)(FRAMES - XFORM_AT) < 600) return t - 1;
    return up;
}
static void power_up(void *sprite, const void *vt) {
    u32 *state = Alloc(0x10);
    if (state) { *(u8 *)&state[1] = 4; state[0] = (u32)vt; }
    Sprite_SetFacing(sprite, 10);
    Sprite_SetBehaviour(sprite, state);
}
static int can_step(u8 *record) { return IN_COMBAT && CanAfford(record, 10); }   /* a tier up, as retail Super Saiyan 3: a fight and 10 ki */
static int can_start(u8 *record) { return can_step(record) && *(u32 *)(record + 4) == 0; }   /* from base, as retail Super Saiyan: no cool-down either */
int ss_can(u8 *record) { return is_kaioken(record[0x14]) ? 0 : SS_Can(record); }
void ss_use(u8 *record, void *sprite) { XFORM = 0; SS_Use(record, sprite); }
int ss2_can(u8 *record) {
    int form = record[0x14], f = flags_of(form);
    if (is_ss2(form)) return 1;
    return (f & 1) && !(f & 2) && !is_kaioken(form) && up_of(form) != 255 && is_ss2(up_of(form)) && ss2_open(record, form_table[form * 24 + 0x0C]) && can_step(record);
}
void ss2_use(u8 *record, void *sprite) {
    XFORM = 0;
    if (is_ss2(record[0x14])) power_down(record, sprite); else SS3_Use(record, sprite);
}
int ss3_can(u8 *record) {       /* Super Saiyan 3 starts from Super Saiyan 2 where a form has one, not from Super Saiyan */
    int form = record[0x14];
    if (is_kaioken(form) || is_ssj4(form)) return 0;
    if ((flags_of(form) & 1) && up_of(form) != 255 && is_ss2(up_of(form))) return 0;
    if ((flags_of(form) & 2) && up_of(form) != 255 && is_ssj4(up_of(form))) return 1;        /* Kid Goku's Super Saiyan 3: powers down */
    return SS3_Can(record);
}
void ss3_use(u8 *record, void *sprite) { XFORM = 0; SS3_Use(record, sprite); }
int ss4_can(u8 *record) {      /* from the form below Super Saiyan 4 (Kid Goku's Super Saiyan 3, GT Vegeta's Super Saiyan) */
    int form = record[0x14];
    if (is_ssj4(form)) return form != FORM_GOGETA_SSJ4;
    return (flags_of(form) & 3) && up_of(form) != 255 && is_ssj4(up_of(form)) && can_step(record);
}
void ss4_use(u8 *record, void *sprite) {
    XFORM = 0;
    if (is_ssj4(record[0x14])) power_down(record, sprite);
    else { ssj4_pending(record); power_up(sprite, ssj4_vt); }
}
/* Super Saiyan Blue: DBS Gogeta's from his Super Saiyan (its up); Goku's and Vegeta's from theirs through ssb_map (their up is Super Saiyan 2). */
extern const u8 ssb_map[][2], kaioken_map[][2];
static int mapped(const u8 (*m)[2], int form) {
    int i;
    for (i = 0; m[i][0] != 255; i++) if (m[i][0] == form) return m[i][1];
    return 255;
}
static int is_ssb(int form) {
    int i;
    for (i = 0; ssb_map[i][0] != 255; i++) if (ssb_map[i][1] == form) return 1;
    return 0;
}
#define FORM_GOGETA_SSB_FORM (form_table[FORM_GOGETA_DBS_SS * 24 + 0x16])
int ssb_can(u8 *record) {
    int form = record[0x14];
    if (is_ssb(form) || form == FORM_GOGETA_SSB_FORM) return 1;
    if (form == FORM_GOGETA_DBS_SS) return can_step(record);
    return (flags_of(form) & 1) && mapped(ssb_map, form) != 255 && can_step(record);
}
void ssb_use(u8 *record, void *sprite) {
    int form = record[0x14];
    XFORM = 0;
    if (is_ssb(form) || form == FORM_GOGETA_SSB_FORM) power_down(record, sprite);
    else if (form == FORM_GOGETA_DBS_SS) power_up(sprite, ssb_vt);
    else power_to(record, sprite, mapped(ssb_map, form), ssb_vt);
}
/* Kaioken (Goku and the humans): from a base form to its red copy (kaioken_map), a Super Saiyan class form without the +5, as the build
   makes its row, with the red aura. Its bar drains as Super Saiyan's does and it costs health as it goes (ss_tick); hits are 1.5x. */
static int is_kaioken(int form) {
    int i;
    for (i = 0; kaioken_map[i][0] != 255; i++) if (kaioken_map[i][1] == form) return 1;
    return 0;
}
int kaioken_can(u8 *record) {
    int form = record[0x14];
    if (is_kaioken(form)) return 1;
    return !(flags_of(form) & 3) && mapped(kaioken_map, form) != 255 && can_start(record);
}
void kaioken_use(u8 *record, void *sprite) {
    int form = record[0x14];
    XFORM = 0;
    if (is_kaioken(form)) SS_Use(record, sprite);
    else power_to(record, sprite, mapped(kaioken_map, form), ssj4_vt);
}
/* Skills beyond the seven a fighter can hold (Nov 9). Each party character has a book (skill_book, build.py) of up to 16 skills the
   loadout can hold; record +0x22 is a mask over it of the ones they know. Equipped skills sit in the record as always (+0x0D, levels
   +0x2E). The story's natives add (0xA4), remove (0xA5) and replace (0xA6) skills: ours do the same on the record and keep the book's
   mask in step, so a skill swapped out still learns, locks and unlocks. A skill learned with no free slot waits in the book; the
   pause menu's Skills tab swaps one in with SELECT. Skills earned by play (Kaioken, Galick Gun, each tier, the post-game moves, mastery)
   are learned by skills_sync. Retail moves' levels come with the character's level (the level-up script, 0x0877C9E8), so a move swapped
   back in takes the level that gives; a transformation's level is its mastery (mastery bytes in the bench's last group). */
extern const u8 skill_book[8][16], level_steps[][4];
static int ss2_open(const u8 *record, int owner);
#define KNOWN(rec) (*(u16 *)((rec) + 0x22))
#define GetLevel ((int (*)(u8 *))0x080135D3)
#define G_FLAGS ((void *)0x03001068)
#define MASTERY ((u8 *)BENCH.e[GROUPS - 1].gear)           /* 22 bytes: one per (character, tier) in mastery_slot order, then Goku's Kamehameha count */
static u8 *rec_of(int c) { return RECORDS + c * RECORD_SIZE; }
static int book_at(int c, int skill) {
    int i;
    if (c > 7) return -1;
    for (i = 0; i < 16; i++) if (skill_book[c][i] == skill) return i;
    return -1;
}
static int slot_of(const u8 *rec, int skill) {
    int i;
    for (i = 0; i < rec[0x0C]; i++) if (rec[0x0D + i] == skill) return i;
    return -1;
}
static int knows(int c, int skill) { int b = book_at(c, skill); return b >= 0 && KNOWN(rec_of(c)) >> b & 1; }
static void set_known(int c, int skill, int on) {
    int b = book_at(c, skill);
    if (b < 0) return;
    if (on) KNOWN(rec_of(c)) |= 1 << b; else KNOWN(rec_of(c)) &= ~(1 << b);
}
/* the tiers whose level is mastery, and where each character's byte is */
static const u8 tier_skill[6] = {20, 35, 22, 36, 44, 37};      /* SS, SS2, SS3, SS4, Blue, Kaioken */
static const signed char mastery_slot[8][6] = {{0, 1, 2, 3, 4, 5}, {6, 7, -1, -1, -1, -1}, {8, -1, -1, -1, -1, -1}, {9, 10, -1, -1, -1, -1},
                                      {11, 12, -1, 13, 14, -1}, {15, -1, 16, -1, -1, -1}, {17, 18, -1, -1, -1, -1}, {19, -1, -1, -1, 20, -1}};
#define KAME_COUNT (MASTERY[21])
static int tier_of(int skill) { int i; for (i = 0; i < 6; i++) if (tier_skill[i] == skill) return i; return -1; }
int mastery_level(int c, int skill) {          /* 0, 1, 2: shown as Level 1-3 */
    int t = tier_of(skill), m;
    if (t < 0 || c > 7 || (m = mastery_slot[c][t]) < 0) return 0;
    return MASTERY[m] >= MASTERY_L3 ? 2 : MASTERY[m] >= MASTERY_L2 ? 1 : 0;
}
static int derived_level(int c, int skill) {    /* a move's level from the character's level, as the level-up script grants it */
    int lv = GetLevel(rec_of(c)), i;
    if (tier_of(skill) >= 0) return mastery_level(c, skill);
    for (i = 0; level_steps[i][0] != 255; i++)
        if (level_steps[i][0] == c && level_steps[i][1] == skill) return (lv >= level_steps[i][3]) + (lv >= level_steps[i][2] || level_steps[i][2] == 0);
    return 0;
}
static void equip(int c, u8 *rec, int at, int skill) {     /* put a skill in slot `at` (at == count: a new slot) with its level */
    int lv = derived_level(c, skill);
    rec[0x0D + at] = skill; rec[0x2E + 2 * at] = lv; rec[0x2F + 2 * at] = lv;
    if (at == rec[0x0C]) rec[0x0C]++;
}
/* the natives */
void skill_add(int *sp) {
    int n = *sp, skill = sp[n], c = sp[n - 1];
    u8 *rec = rec_of(c);
    *sp = n - 2;
    set_known(c, skill, 1);
    if (slot_of(rec, skill) < 0 && rec[0x0C] < 7) equip(c, rec, rec[0x0C], skill);
}
void skill_remove(int *sp) {
    int n = *sp, skill = sp[n], c = sp[n - 1];
    *sp = n - 2;
    set_known(c, skill, 0);
    ((void (*)(u8 *, int))0x08013ABB)(rec_of(c), skill);
}
void skill_replace(int *sp) {
    int n = *sp, to = sp[n], from = sp[n - 1], c = sp[n - 2];
    *sp = n - 3;
    if (knows(c, from) || book_at(c, from) < 0) { set_known(c, from, 0); set_known(c, to, 1); }
    ((void (*)(u8 *, int, int))0x08013B13)(rec_of(c), from, to);
}
/* what play has earned: run for the fighter in control now and then, and for a character as the Skills tab opens */
static void learn(int c, int skill, int ok) {
    u8 *rec = rec_of(c);
    if (!ok || knows(c, skill) || slot_of(rec, skill) >= 0) { if (ok && slot_of(rec, skill) >= 0) set_known(c, skill, 1); return; }
    set_known(c, skill, 1);
    if (rec[0x0C] < 7) equip(c, rec, rec[0x0C], skill);
}
void skills_sync(int c) {
    u8 *rec;
    int i, post = GetFlag(G_FLAGS, 149), gt = more_flag(MORE_GT_FLAG);
    if (c > 7) return;
    rec = rec_of(c);
    for (i = 0; i < rec[0x0C]; i++) {
        if (c == 7 && rec[0x0D + i] == 21) rec[0x0D + i] = SSB_SKILL;          /* Gogeta's Super Saiyan Blue, from before it had its own row */
        set_known(c, rec[0x0D + i], 1);
        if (tier_of(rec[0x0D + i]) >= 0) rec[0x2E + 2 * i] = rec[0x2F + 2 * i] = mastery_level(c, rec[0x0D + i]);
    }
    if (book_at(c, 35) >= 0) learn(c, 35, (knows(c, 20) || slot_of(rec, 20) >= 0) && ss2_open(rec, c));
    if (c == 0) {
        learn(c, KAIOKEN_SKILL, 1);
        learn(c, 36, gt); learn(c, TENX_SKILL, gt); learn(c, DRAGON4_SKILL, gt);
        learn(c, SSB_SKILL, post && mastery_level(0, 22) == 2);
        learn(c, SUPER_KAME_SKILL, post && derived_level(0, 15) == 2 && KAME_COUNT >= SUPER_KAME_USES);
    }
    if (c == 4) {
        learn(c, GALICK_SKILL, 1);
        learn(c, 36, gt); learn(c, FINAL_SHINE_SKILL, gt);
        learn(c, SSB_SKILL, post && mastery_level(4, 35) == 2);
    }
}
/* the Skills tab (vtable 0x0804B024): R swaps the chosen skill for the next one the fighter knows but isn't holding */
void skills_swap(int c, int at) {
    u8 *rec = rec_of(c);
    int i, b0, cur;
    if (c > 7 || at < 0 || at >= rec[0x0C]) return;
    cur = rec[0x0D + at]; b0 = book_at(c, cur);
    for (i = 1; i <= 16; i++) {
        int b = ((b0 < 0 ? -1 : b0) + i) & 15, s = skill_book[c][b];
        if (s == 255 || !(KNOWN(rec) >> b & 1) || slot_of(rec, s) >= 0) continue;
        set_known(c, cur, 1);
        equip(c, rec, at, s);
        return;
    }
}
/* The Skills tab: SELECT swaps (slot 10, keys: L and R change tabs there); opening it learns what play has earned (slot 1, setup). */
#define KEYS_NEW (*(volatile u16 *)0x03003304)
#define SkillTab_Keys ((int (*)(u8 *))0x080175FD)
#define SkillTab_Setup ((int (*)(u8 *, int, int, int))0x080171A9)
int skilltab_keys(u8 *obj) {
    if (KEYS_NEW & 0x4) {
        int c = *(int *)(obj + 0x114);
        skills_swap(c, *(int *)(obj + 0x120));
        PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
        *(int *)(obj + 0x118) = rec_of(c)[0x0C];
        *(int *)(obj + 0x110) = 0;
    }
    return SkillTab_Keys(obj);
}
int skilltab_setup(u8 *obj, int a, int b, int d) {
    int c = *(int *)(obj + 0x114), r;
    skills_sync(c);
    *(int *)(obj + 0x118) = c <= 8 ? rec_of(c)[0x0C] : *(int *)(obj + 0x118);
    r = SkillTab_Setup(obj, a, b, d);
    if (c <= 7)                                          /* the hint, beside Select and Cancel (the game's buttons have no SELECT icon) */
        AddWidget(obj, NewText(0, obj, 0x84, 0x90, (const u16 *)L"SELECT: Swap", 5, 0, (void *)FONT));
    return r;
}
/* sub_0801C312 ends a power-up by moving the record to its form's up; xform_hook (at 0x0801C35C) lets XFORM choose instead. */
void xform_hook(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global xform_hook\nxform_hook:\n"
        "ldrb r0, [r7, #22]\nadds r1, r4, #0\nbl xform_target\nstrb r0, [r4, #20]\nlsls r3, r0, #1\nadds r0, r3, r0\nldr r3, =0x0801C365\nbx r3\n.ltorg\n");
/* Super Saiyan's drain (sub_0800E3E6) is about to take a unit from the pool (+0x1E): ss_tick sees it first. It returns 1 to skip the unit
   (a mastered form drains slower); in Kaioken it costs health too, and when health runs short the pool empties so the game powers down. */
static int mastery_skip(u8 *rec);
int ss_tick(u8 *rec) {
    if (rec != RECORDS + *(u8 *)0x03001068 * RECORD_SIZE) return 0;
    if (is_kaioken(rec[0x14])) {
        short *hp = (short *)(rec + 0x16), cost = *(short *)(rec + 0x18) / 150;
        if (cost < 1) cost = 1;
        if (*hp > cost + 1) *hp -= cost;
        else *(u16 *)(rec + 0x1E) = 0;
    }
    return mastery_skip(rec);
}
void ss_drain_hook(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global ss_drain_hook\nss_drain_hook:\n"
        "push {r0}\nbl ss_tick\nadds r3, r0, #0\npop {r0}\nadds r1, r0, #0\nadds r1, #30\nldrh r2, [r1]\n"
        "cmp r3, #0\nbne 1f\ncmp r2, #0\nldr r3, =0x0800E435\nbx r3\n1:\nldr r3, =0x0800E467\nbx r3\n.ltorg\n");
/* Mastery: each drain unit in a tier's form trains it (one point per MASTERY_EVERY units: about every 3 seconds in either class); at
   MASTERY_L2 and MASTERY_L3 points the tier reaches Level 2 and 3 and drains a fifth and two fifths slower. */
#define MASTERY_TICK (*(volatile u8 *)0x0203FFC0)
static int form_tier(int form) {
    int f = form_table[form * 24];
    if (is_kaioken(form)) return 5;
    if (is_ssj4(form)) return 3;
    if (is_ssb(form) || form == FORM_GOGETA_SSB_FORM) return 4;
    if (is_ss2(form)) return 1;
    if (f & 2) return 2;
    if (f & 1) return 0;
    return -1;
}
static int mastery_train(u8 *rec, int every) {        /* -> 1 to skip this drain unit */
    int c = *(u8 *)0x03001068, t = form_tier(rec[0x14]), m, lv;
    if (c > 7 || t < 0 || (m = mastery_slot[c][t]) < 0) return 0;
    MASTERY_TICK++;
    if (MASTERY_TICK % every == 0 && MASTERY[m] < 255) {
        lv = mastery_level(c, tier_skill[t]);
        MASTERY[m]++;
        if (mastery_level(c, tier_skill[t]) != lv) PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
    }
    lv = mastery_level(c, tier_skill[t]);
    return MASTERY_TICK % 5 < lv;
}
static int mastery_skip(u8 *rec) { return mastery_train(rec, 10); }
/* Uub becomes Majuub with Super Saiyan's mechanics, but without the gold aura (Android 13's power-up); Majuub changes back as a Super Saiyan does. */
extern const int absorb_vt[14];
void majuub_use(u8 *record, void *sprite) {
    if (!(form_table[record[0x14] * 24] & 1)) power_up(sprite, absorb_vt);
    else SS_Use(record, sprite);
}
extern const u8 ssj4_rows[];
static int is_ssj4(int form) {   /* the Super Saiyan 4 forms (build.py: every form whose name ends in ssj4) */
    const u8 *p;
    for (p = ssj4_rows; *p != 255; p++) if (*p == form) return 1;
    return 0;
}
/* Super Saiyan 4's own ki bar. A transformed form spends and drains one pool: Super Saiyan's (record +0x1E, drawn yellow over the green EP
   bar) or Super Saiyan 3's (+0x20, orange over that), and powers down when it runs dry. Super Saiyan 4 is Super Saiyan 3's class, so its
   pool is +0x20 too; here it is drawn purple, and the orange ki the fighter had when he went Super Saiyan 4 (Kid Goku's Super Saiyan 3 bar)
   is put aside (SK.rest) as a bar of its own. Only one drains at a time: the purple first, while the orange stays as it is; when the
   purple runs out the orange takes over, then the form powers down. Either drains at half Super Saiyan 3's rate.
   SK.pending: set on pressing for Super Saiyan 4; the first look at the record in that form takes it (Gogeta, already Super Saiyan 4: none). */
struct ssj4ki { u16 rest, pending_rest; u8 pending, active, purple, tick; };
#define SK (*(volatile struct ssj4ki *)0x0203FFB0)
static void ssj4_track(const u8 *rec) {
    int form = rec[0x14];
    if (!is_ssj4(form)) { SK.active = 0; if (!(form_table[form * 24] & 3)) SK.pending = 0; return; }
    if (!SK.active) { SK.active = 1; SK.purple = 1; SK.tick = 0; SK.rest = SK.pending ? SK.pending_rest : 0; SK.pending = 0; }
}
static void ssj4_pending(const u8 *record) { SK.pending_rest = *(const u16 *)(record + 0x20); SK.pending = 1; }
/* The Super Saiyan 3 class's drain (0x0800E4C4) is about to take `need` (whole units, when its accumulator rolls over) from the pool;
   returns what it takes. Super Saiyan 4: when the purple is down to its last, the orange put aside takes its place; then every other
   unit is skipped, which halves the rate (a skipped unit takes nothing, so the empty-pool check only fires on a pool already empty). */
static int mastery_train(u8 *rec, int every);
int ssj4_refill(u8 *rec, int need) {
    u16 *pool = (u16 *)(rec + 0x20);
    if (rec != RECORDS + *(u8 *)0x03001068 * RECORD_SIZE) return need;
    ssj4_track(rec);
    if (mastery_train(rec, 45)) return 0;            /* a mastered tier drains slower */
    if (!SK.active) return need;
    if (SK.purple && *pool <= need) {
        SK.purple = 0;
        if (SK.rest) { *pool += SK.rest; SK.rest = 0; }
    }
    SK.tick ^= 1;
    return SK.tick ? 0 : need;
}
void ssj4_drain(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global ssj4_drain\nssj4_drain:\n"
        "asrs r1, r1, #16\npush {r0}\nbl ssj4_refill\nadds r2, r0, #0\npop {r0}\n"
        "adds r1, r0, #0\nadds r1, #32\nldrh r3, [r1]\ncmp r3, r2\nble 1f\nldr r3, =0x0800E513\nbx r3\n1:\nldr r3, =0x0800E525\nbx r3\n.ltorg\n");
/* The HUD (0x0800B99C) has drawn the bars into buf (orange for the first +0x20 columns); before it goes to VRAM, Super Saiyan 4 paints
   those columns purple and the orange left under it after them. 41 columns, three pixels each at the offsets in BAR_COLS. */
extern const u8 ssj4_bar[0x500];
#define BAR_COLS ((const u32 *)0x08071F40)
#define ORANGE_BAR ((const u8 *)0x08713FD8)
void ssj4_hud(const u8 *widget, u8 *buf) {
    const u8 *rec = RECORDS + *(u8 *)0x03001068 * RECORD_SIZE;
    int max = *(const short *)(rec + 0x1C), np, no, c, k;
    ssj4_track(rec);
    if (SK.active && SK.purple && max > 0) {
        np = *(const u16 *)(rec + 0x20) * 41 / max; no = SK.rest * 41 / max;
        if (np > 41) np = 41;
        if (no > 41) no = 41;
        for (c = 0; c < np; c++) for (k = 0; k < 3; k++) { u32 o = BAR_COLS[c * 4 + k]; buf[o] = ssj4_bar[o]; }
        for (; c < no; c++) for (k = 0; k < 3; k++) { u32 o = BAR_COLS[c * 4 + k]; buf[o] = ORANGE_BAR[o]; }
    }
    MemCopy((u8 *)0x06010000 + *(const u16 *)(widget + 12) * 32, buf, 0x500);
}
/* Against Super Saiyan's damage, Super Saiyan 2 hits 1.5x as hard and Super Saiyan 3 1.75x. hit[1] is the attack's damage scale (1024 = normal); team 2 is the player's side.
   Damage grows with the cube of the Strength stat, so scaling the stat itself would give about three times the damage.
   Super Saiyan 3 adds 15 to the stats where Super Saiyan adds 5: its attacks count from the Super Saiyan figure, and it keeps the extra Endurance and Speed. */
void combat_orig(void *defender, int *hit);
__asm__(".syntax unified\n.thumb\n.thumb_func\ncombat_orig:\npush {r4, r5, r6, r7, lr}\nadds r6, r0, #0\nadds r4, r1, #0\nadds r1, #8\nldr r3, =0x0800E9E1\nbx r3\n.ltorg\n");
void combat_hook(void *defender, int *hit) {
    int scale = hit[1], form = FORM_OF(*(u8 *)0x03001068);
    u16 *stats = (u16 *)((u8 *)hit[3] + 0x1B0), strength = stats[0], power = stats[1];
    int mine = hit[3] && *((u8 *)hit[3] + 0x1D0) == 1;    /* the attacker (hit[3], the owner of a blast) is on the player's side (team 1). hit[0] is the direction */
    if (mine) {
        if (is_ssj4(form)) {                         /* Super Saiyan 4: 2.5x Super Saiyan's damage, Gogeta's 3x (from Super Saiyan 3's figure where it is that class) */
            hit[1] = form == FORM_GOGETA_SSJ4 ? scale * 3 : scale * 2 + (scale >> 1);
            if ((form_table[form * 24] & 2) && strength > 10 && power > 10) { stats[0] = strength - 10; stats[1] = power - 10; }
        }
        else if (is_ssb(form) || form == FORM_GOGETA_SSB_FORM) {      /* Super Saiyan Blue: 2x, from Super Saiyan's figure as Super Saiyan 3 */
            hit[1] = scale * 2;
            if (strength > 10 && power > 10) { stats[0] = strength - 10; stats[1] = power - 10; }
        }
        else if (is_ss2(form) || form == FORM_MAJUUB || form == FORM_S13 || form == FORM_S17 || form == FORM_ROSE || is_kaioken(form)) hit[1] = scale + (scale >> 1);
        else if ((form_table[form * 24] & 2) && strength > 10 && power > 10) {
            hit[1] = scale + (scale >> 1) + (scale >> 2);
            stats[0] = strength - 10; stats[1] = power - 10;
        }
    }
    if (mine && dragon4_live) hit[1] += hit[1] >> 2;      /* Super Saiyan 4's red Dragon Fist: 1.25x */
    combat_orig(defender, hit);
    hit[1] = scale; stats[0] = strength; stats[1] = power;
}
