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
        fighter[] = {2, 7, 8}, a17[] = {5, 7, 8, BLITZ_SKILL, WAVE_SKILL, SUPER17_SKILL}, a18[] = {4, 7, BLITZ_SKILL, DISC_SKILL, WAVE_SKILL}, krillin[] = {5, 7, 15, DISC_SKILL, SOLAR_SKILL, KAIOKEN_SKILL}, videl[] = {2, 7, KAIOKEN_SKILL},
        tien[] = {5, 7, 15, BLITZ_SKILL, SOLAR_SKILL, KAIOKEN_SKILL}, yamcha[] = {3, 7, 15, KAIOKEN_SKILL}, pikkon[] = {3, 7, 8, WAVE_SKILL}, hercule[] = {2, 7, KAIOKEN_SKILL},
        black[] = {4, 7, 14, BLACK_KAME_SKILL, ROSE_SKILL},     /* Goku Black: ki blasts, Instant Transmission, the Black Kamehameha, Rose. Energy Punch and Energy Sword play animation slots Goku's figure fills with other moves */
        trunks[] = {5, 7, 20, 4, 11, GALICK_SKILL},     /* Future Trunks: the same moves as Trunks, and his father's Galick Gun (Nov 9) */
        pan[] = {3, 7, 8, 20}, pan_plain[] = {2, 7, 8},  /* Pan: ki blasts and her rush; Super Saiyan in the two looks that have it. Brapan (the Bulma-Pan fusion) fights as Pan */
        uub[] = {4, 7, 8, 15, MAJUUB_SKILL},     /* Uub: ki blasts, rush, Kamehameha, Majuub */
        roshi[] = {4, 7, 8, 15, MAX_POWER_SKILL},    /* Master Roshi: ki blasts, rush, the Kamehameha (his own), Max Power */
        buu[] = {3, 7, 8, 15};     /* Kid Buu and Majin Buu: the Kamehameha too (Nov 10, the owner: "give all playable Buus forms kamehameha") */
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
    else if (form == FORM_ROSHI || form == FORM_ROSHI_MAX) list = roshi;
    else if (form == FORM_KID_BUU || form == FORM_MAJIN_BUU) list = buu;
    else if (form == FORM_JANEMBA) list = fighter;
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

/* The mastery bytes (outfit.c MASTERY) live in the bench too. Before reading them the bench must be this game's; before the first change a game
   with no bench yet gets a generation, so the save keeps it (a game that never swapped a guest has none, and bench_ready would clear it again). */
static void bench_mine(int writing) { bench_ready(); if (writing && !BENCH.gen) bench_bump(); }
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
int mastery_level(int c, int skill);
/* Battle of Gods (ultimate/bog.py) asks more_get these too: 251 this area (area << 8 | world), 252 Goku playing, 253 the quest can start
   (after the ending and the Garlic Jr. quest (garlic.py: it comes first, the owner's choice), Goku's Super Saiyan mastered, Goku playing).
   250 ends any fusion (fusion_end: Super 13's door and his Spirit Bomb finish ask it before they make Goku play) */
int fusion_end(int now);
void more_get(int *sp) {
    int n = *sp, f = sp[n], me = *(u8 *)0x03001068;
    if (f == 250) sp[n] = fusion_end(1);
    else if (f == 251) sp[n] = *(volatile u16 *)0x0300197C;
    else if (f == 252) sp[n] = me == 0;
    else if (f == 253) sp[n] = GetFlag((void *)0x03001068, 149) && more_flag(MORE_GJ_DONE) && mastery_level(0, 20) == 2 && me == 0;
    else sp[n] = more_flag(f);
}
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
    for (i = 0; i < 8; i++) ((volatile u32 *)0x0203FFB0)[i] = 0;     /* Super Saiyan 4's ki bar state, the Super Dragon Fist, and the rest to 0x0203FFCF */
    BENCH.magic = 0;
    CL.active = 0; CL.cool = 0; CL.surge = 0; CL.p_at = 0; CL.e_at = 0;
    *(u32 *)0x0203F300 = 0;                /* no bomb sprite */
    *(u32 *)0x0203F280 = 0;                /* no boss bar */
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
    else if (owner) {                      /* any fighter's beam can clash: it needs only to be a beam with an owner other than the player */
        if (CL.active && b != CL.e) return;      /* a second fighter's beam while one is clashing goes its own way (two Kid Buus in a Trial) */
        CL.e = b; CL.e_at = FRAMES; clash_answer(b);
    }
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
/* Post-game gear (Nov 9; build.py GEAR): rows past the game's equipment table. Their effects are here, not in effect scripts. */
static int wearing(const u8 *rec, int row) {
    int i;
    for (i = 0; i < 4; i++) if (*(const u32 *)(rec + 0x3C + 4 * i) == (u32)row) return 1;
    return 0;
}
#define GEAR_TICK (*(volatile u8 *)0x0203FFC5)
#define SHADES_TICK (*(volatile u8 *)0x0203FFC6)
#define SSG_TICK (*(volatile u8 *)0x0203F268)          /* every other drain unit of Super Saiyan God is skipped */
static int potara_skip(const u8 *rec) {        /* Potara Earrings: one drain unit in three passes free */
    if (!wearing(rec, GEAR_POTARA)) return 0;
    if (++GEAR_TICK >= 3) { GEAR_TICK = 0; return 1; }
    return 0;
}
#define COMBAT_ON (*(volatile u32 *)0x03001988)
static void pouch_heal(void) {                 /* Senzu Pouch: 1% of health back every two seconds of a fight */
    u8 *rec = RECORDS + *(u8 *)0x03001068 * RECORD_SIZE;
    short *hp = (short *)(rec + 0x16), max = *(short *)(rec + 0x18), add = max / 100;
    if (!COMBAT_ON || *hp <= 0 || *hp >= max || !wearing(rec, GEAR_POUCH)) return;
    if (add < 1) add = 1;
    *hp = *hp + add > max ? max : *hp + add;
}
/* Quick skill wheel (Nov 9): hold L and press a direction to pick a skill at once (up the first, right the second, down the third,
   left the fourth), or A for the fifth and R for the sixth (a fighter holds six: MAX_HELD; the owner asked for more than four). The
   fighter doesn't walk, attack or guard while L is held. A tap of L alone still steps through all of them as before. */
#define wheel_keys ((volatile u16 *)0x0203F25C)      /* (in work RAM: a static would sit in ROM, past the code, where writes go nowhere) */
#define GUARD_AT (*(volatile u32 *)0x0203FFC8)
static u16 *quick_wheel(u16 *keys) {
    static const u8 pick[4] = {1, 3, 0, 2};       /* RIGHT, LEFT, UP, DOWN -> the 2nd, 4th, 1st, 3rd skill */
    u8 *rec = RECORDS + *(u8 *)0x03001068 * RECORD_SIZE;
    int d = keys[2] & 0xF0, i;
    if (keys[2] & 0x100) GUARD_AT = FRAMES;       /* R: the guard's first frame (a perfect guard, guard_msg) */
    if (!(keys[1] & 0x200)) return keys;
    if (d) { for (i = 0; i < 4; i++) if (d & (0x10 << i)) break; d = pick[i]; }
    else if (keys[2] & 0x001) d = 4;              /* A: the fifth */
    else if (keys[2] & 0x100) d = 5;              /* R: the sixth */
    else d = -1;
    if (d >= 0 && d < rec[0x0C] && rec[0x15] != d) { rec[0x15] = d; PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0); }
    for (i = 0; i < 6; i++) wheel_keys[i] = keys[i];
    wheel_keys[1] &= ~0x1F1; wheel_keys[2] &= ~0x1F1;      /* no walking, attack or guard while L is held */
    return (u16 *)wheel_keys;
}
void kk_track(void);
/* Zone 26's snow arena (Android 13, Super 13, the Boss Rush: the rooms in ARENA_ROOMS, bit n = area 26:n, all one map). Two nooks between
   the rocks above the open snowfield are floor too, but on the rocks' layer: a boss who backed into one (Super 13 retreats from a fighter
   below him) was drawn behind the rocks, half see-through, his shadow left below, and no hit reached him; his walk stayed pressed against
   the rocks (Nov 9, the owner: "can't even damage and he's stuck walking up", "couldn't even see it"; reproduced in the emulator: from
   (209, 96) no punch landed for 30 seconds). The open field is x 32-288, y 112-248 (floor mask), so foes stay in x ARENA_X0-ARENA_X1 and
   below y ARENA_Y0; the change and the finish (scenes) are not in the list. The bounds are the open field's own (Nov 10, the owner: "He's
   standing still punching the air not trying to walk to the player and attack"): with 16 px kept off each side a fighter at the field's
   edge (x 32-48) was out of his reach, so he stood at the bound throwing punches. */
#define ARENA_X0 32
#define ARENA_X1 288
#define ARENA_Y0 112
/* The cause of both (same day): an enemy's stats row also picks its behaviour (row +8: its first state in the enemy state table
   0x0870F514), and Super 13 and Android 13 run Dabura's (row 18). Near 60% health Dabura's state 0x7B walks to the point (192, 80) of
   his own story room (a move-to action, vtable 0x08049A3C, made by sub_0802E104: +0x1C, +0x20 the target), waits 180 frames, then goes
   on; nothing touches him meanwhile. In another room that point can be inside the rocks, so he never got there. Every fight the mod set up
   (postgame_foe: Super 13, the Boss Rush, tournament, trials, spars, Battle of Gods) borrows a story boss's behaviour in a room that isn't
   his, so a fixed point of that room means nothing: such a move ends where the foe stands. The state stack: depth at +0x23C, entries of
   {instance, state} from +0x240; a sequence's instance (vtable 0x0804AAF4) holds its step count at +8 and its steps from +0xC. */
#define MOVE_TO_VT 0x08049A3C
#define SEQUENCE_VT 0x0804AAF4
#define IN_EWRAM(p) ((u32)(p) >= 0x02000000 && (u32)(p) < 0x02040000)
static int postgame_foe(const u8 *e);
/* Dabura's flying special (states 0x78-0x7F: he fades, rises off the screen while it flashes white, untouchable, and hits from out of
   sight) is for his own story room. The owner, of Super 13: "replace that shit don't make him do that at 60%". On a copy of his behaviour
   0x78 or 0x79 goes back to his ordinary fighting (0x71), with what the special's start set undone: +0x1CC = 1 (can be hit) and +0x174 = 0
   (the lift). Going to 0x6E re-entered it every frame; leaving it without the reset kept him untouchable (Nov 9, both tried). */
#define STATE_TABLE 0x0870F514
#define DABURA_AI 0x6E                 /* Dabura's first state (his row's +8) */
#define DABURA_SPECIAL 0x79            /* his mid-fight special (0x79-0x7F; 0x78 leads into it) */
#define DABURA_FIGHT 0x71              /* one of his ordinary fighting states */
#define STATE_GOTO(obj, n) ((u32 (*)(void *, ...))(*(u32 *)(obj) + *(int *)(*(u32 *)(obj) + 0x68)))(obj, n)     /* vtable +0x68: the behaviour tree's goto (sub_08018920) */
static void no_story_walk(u8 *e) {
    int depth = *(int *)(e + 0x23C);
    const u8 *row = *(const u8 **)(e + 0x224);
    u32 *seq, k, n;
    if (depth < 1 || depth > 5) return;
    if (depth == 1 && *(const u32 *)(row + 8) == DABURA_AI) {
        u32 st = *(u32 *)(e + 0x244);
        if (st == STATE_TABLE + 8 * (DABURA_SPECIAL - 1) || st == STATE_TABLE + 8 * DABURA_SPECIAL) {
            STATE_GOTO(e, DABURA_FIGHT);
            *(u32 *)(e + 0x1CC) = 1;            /* hittable again (the special clears it) */
            *(u32 *)(e + 0x174) = 0;            /* and back on the ground (the special lifts him: -20 px) */
            return;
        }
    }
    seq = *(u32 **)(e + 0x240 + 8 * (depth - 1));
    if (!IN_EWRAM(seq) || seq[0] != SEQUENCE_VT) return;
    n = seq[2] < 8 ? seq[2] : 8;
    for (k = 0; k < n; k++) {
        u32 *step = (u32 *)seq[3 + k];
        if (IN_EWRAM(step) && step[0] == MOVE_TO_VT) { step[7] = *(u32 *)(e + 0x1A0); step[8] = *(u32 *)(e + 0x1A4); }
    }
}
/* Dabura's behaviour is for his own small room. On the open snowfield (measured Nov 10, a fighter standing still at spots round the field):
   further than about 120 px away he waited with his arms crossed (state 0x6F) for as long as the fighter stayed there, and walking (0x72)
   he took a line that ran him into the field's curved corner (248, 232), where he walked on the spot. So in the arena, a boss who has
   walked without moving for 12 frames steps straight at the fighter (the field is open between them), and one who has waited 90 frames
   with the fighter far off starts walking. Past 60% his behaviour keeps reaching for the flying special, which no_story_walk turns back
   into fighting (0x71), and in 0x71 he stood where he was for the rest of the fight with the fighter out of reach (test_super13: frozen
   at 36% for the last 50 steps, no hit on a fighter standing anywhere): fighting 40 frames without moving with the fighter out of
   reach (past 24 px across or 16 up or down; he stopped 35-36 px off, where his punch barely reached) he steps at him too. (Sent back
   to walking instead, he went into the special and stood for longer.)
   Within that reach his punches can still miss for good (Nov 11: a fighter at the field's left edge, (32, 200), with Super 13 at
   (56, 208), 24 px across and 8 down: twelve seconds of punches, no hit; before, the same in the bottom-left corner after a long
   fight). A punch goes straight out the way he faces, so he has to stand level with the fighter (or straight above or below him):
   fighting in place for a second and a half with none of his hits landing (the fighter's health, record +0x16, hasn't dropped), he
   lines up on the nearer axis, then closes to 16 px on the other. */
#define DABURA_WAIT 0x6F
#define DABURA_WALK 0x72
struct arena_chase { u8 *e; short x, y; u16 still, idle; short hp; u16 miss; };
#define AC (*(struct arena_chase *)0x0203F270)
static void arena_chase(u8 *e) {
    u8 *pl = *(u8 **)0x03001C34;
    u32 st = *(u32 *)(e + 0x244);
    int fx, fy, dx, dy;
    if (!IN_EWRAM(pl) || *(int *)(e + 0x23C) != 1 || *(const u32 *)(*(const u8 **)(e + 0x224) + 8) != DABURA_AI) return;
    fx = *(int *)(e + 0x1A0) >> 8; fy = *(int *)(e + 0x1A4) >> 8;
    dx = (*(int *)(pl + 0x1A0) >> 8) - fx; dy = (*(int *)(pl + 0x1A4) >> 8) - fy;
    if (AC.e != e) { AC.e = e; AC.still = AC.idle = AC.miss = 0; AC.x = fx; AC.y = fy; AC.hp = 0; }
    if (st == STATE_TABLE + 8 * DABURA_WALK && (dx > 36 || dx < -36 || dy > 20 || dy < -20)) {
        if (fx == AC.x && fy == AC.y) { if (AC.still < 1000) AC.still++; } else AC.still = 0;
        if (AC.still > 12) {
            if (dx) *(int *)(e + 0x1A0) += dx > 0 ? 0x180 : -0x180;
            if (dy > 8 || dy < -8) *(int *)(e + 0x1A4) += dy > 0 ? 0x100 : -0x100;
        }
    }
    else if (st == STATE_TABLE + 8 * DABURA_FIGHT && (dx > 24 || dx < -24 || dy > 16 || dy < -16)) {
        if (fx == AC.x && fy == AC.y) { if (AC.still < 1000) AC.still++; } else AC.still = 0;
        if (AC.still > 40) {
            if (dx) *(int *)(e + 0x1A0) += dx > 0 ? 0x180 : -0x180;
            if (dy > 8 || dy < -8) *(int *)(e + 0x1A4) += dy > 0 ? 0x100 : -0x100;
        }
        AC.miss = 0;
    }
    else {
        AC.still = 0;
        if (st == STATE_TABLE + 8 * DABURA_FIGHT) {
            int hp = *(short *)(RECORDS + *(u8 *)0x03001068 * RECORD_SIZE + 0x16);
            int ax = dx < 0 ? -dx : dx, ay = dy < 0 ? -dy : dy;
            if (hp < AC.hp || fx != AC.x || fy != AC.y) AC.miss = 0; else if (AC.miss < 1000) AC.miss++;
            AC.hp = hp;
            if (AC.miss > 90) {
                if (ax >= ay) {
                    if (ay > 2) *(int *)(e + 0x1A4) += dy > 0 ? 0x100 : -0x100;
                    else if (ax > 16) *(int *)(e + 0x1A0) += dx > 0 ? 0x100 : -0x100;
                }
                else {
                    if (ax > 2) *(int *)(e + 0x1A0) += dx > 0 ? 0x100 : -0x100;
                    else if (ay > 16) *(int *)(e + 0x1A4) += dy > 0 ? 0x100 : -0x100;
                }
            }
        }
        else AC.miss = 0;
    }
    if (st == STATE_TABLE + 8 * DABURA_WAIT && (dx > 110 || dx < -110 || dy > 70 || dy < -70)) {
        if (++AC.idle > 90) { AC.idle = 0; STATE_GOTO(e, DABURA_WALK); }
    }
    else AC.idle = 0;
    AC.x = *(int *)(e + 0x1A0) >> 8; AC.y = *(int *)(e + 0x1A4) >> 8;
}
static void arena_keep(void) {
    u16 at = *(volatile u16 *)0x0300197C;
    int i, n = *(volatile int *)0x03001BB0, arena = (at & 0xFF) == 26 && (at >> 8) < 32 && ((ARENA_ROOMS >> (at >> 8)) & 1);
    for (i = 0; i < n && i < 32; i++) {
        u8 *e = ((u8 **)0x03001BB4)[i];
        int *x, *y;
        if (!IN_EWRAM(e) || e[0x1D0] == 1) continue;      /* team 1: the player's side */
        if (postgame_foe(e)) no_story_walk(e);
        if (!arena) continue;
        arena_chase(e);
        x = (int *)(e + 0x1A0); y = (int *)(e + 0x1A4);
        if (*y < ARENA_Y0 << 8) *y = ARENA_Y0 << 8;
        if (*x < ARENA_X0 << 8) *x = ARENA_X0 << 8;
        else if (*x > ARENA_X1 << 8) *x = ARENA_X1 << 8;
    }
}
static void crackle(void);
static void bossbar_tick(void);
void *player_input(void) {
    u16 *keys = (u16 *)0x03003300;
    kk_track();
    arena_keep();
    crackle();
    bossbar_tick();
    if (FRAMES % 120 == 0) pouch_heal();
    keys = quick_wheel(keys);
    /* Battle of Gods: Beerus fights Vegeta at the party, on Capsule Corporation's own grounds, which has no fighting (area record +8
       is 0; the area's load copies it here). While that fight is on, fighting is on there too. */
    if (!COMBAT_ON && *(volatile u16 *)0x0300197C == 0x1404 && more_flag(MORE_BOG_FIGHT)) COMBAT_ON = 1;
    /* what play has earned (the skill book): the fighter in play, and 32 frames later the party in turn. Both in one frame ran over it and
       a fight dropped a frame every 64 (Nov 10). */
    if ((FRAMES & 63) == 0) skills_sync(*(u8 *)0x03001068);
    else if ((FRAMES & 63) == 32) skills_sync((FRAMES >> 6) & 7);
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

/* No ground shadows on this screen (Nov 10, the owner: "Don't render the shadows under characters feet in the switch screen it's blocking
   their name"): a fighter's sprite keeps the shadow its actor record gave it when it was made (+0x5C), drawn below and right of him here,
   over the name. sub_0800ECB0 with a size the game's table doesn't have frees it and leaves none. Only this screen's own sprites. */
#define Sprite_SetShadow ((void (*)(void *, const u32 *))0x0800ECB1)
static void no_shadows(void *obj) {
    static const u32 none[2] = {0, 0};
    int n = *field(obj, OBJ_COUNT), i;
    for (i = 0; i < n; i++) {
        u8 *sprite = (u8 *)*field(obj, OBJ_LIST + 4 + i * 8);
        if (sprite && *(u32 *)(sprite + 0x5C)) Sprite_SetShadow(sprite, none);
    }
}

void gogeta_keep(void);
int picker_update(void *obj) {
    int first = LABEL_OWNER != ((u32)obj ^ SNAP_MAGIC), r;
    gogeta_keep();                             /* before anyone can be picked: a pick of Gogeta with his story fusion's spent time unfused him */
    if (first) restore_borrowed(obj);
    if (first && OUT_FIGHTER) bench_settle(FORM_OF(8));    /* restore_borrowed may have put a different guest on */
    if (KEYS_NEW & KEY_UP) cycle(obj, -1);
    else if (KEYS_NEW & KEY_DOWN) cycle(obj, 1);
    update_label(obj);
    r = orig_update(obj);
    scroll_row(obj, first);
    no_shadows(obj);
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
/* The disc is drawn on BG0, priority 3, the fighters' own: they were drawn over it. bomb_fx(40) puts BG0 in front of them (priority 2; the HUD's
   sprites are 1) for Super 13's finish (Nov 10, the owner: "make the spirit bomb overlay on top of Super 13 so it looks like its hitting him
   rather than going behind him"); bomb_fx(0) puts it back. BG0_KEPT holds the old BG0CNT plus one bit to say it is raised. */
#define BG0CNT (*(volatile u16 *)0x04000008)
#define BG0_KEPT (*(volatile u32 *)0x0203FF7C)
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
#define SKILL_SPRITE_ONLY 1
static void bomb_hide(void) {
    if (BS.actor) BOMB_LIST_REMOVE(ACTOR_LIST, BS.actor);
    BS.actor = 0;
}

static void spirit_draw(void)
{
    /* The skill's bomb is the sprite alone, blast included (Nov 10). The game's disc (native 0xF4, made for the Kid Buu fight's own room)
       takes BG0's map and writes its picture over a few of the area's tiles: in an ordinary area the blast emptied the layer of roofs and
       tree tops, scrambled every ground tile that used those slots (a grid of little squares across West City's grass) and turned
       whatever shared its palette entry cyan (found shooting the trailer; the same in the Nov 9 build). The orb swells to its largest
       picture for the blast and shrinks away; with OBJ memory full it isn't drawn. The story's finish (bomb_at, bomb_fx, in the snow
       arena, whose map the disc suits) keeps the disc. */
    if (SKILL_SPRITE_ONLY) { bomb_show(SB.x, SB.y, SB.r > 48 ? 48 : SB.r); return; }
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
    else if (v == 0) {
        SB.phase = 0; BLDY = 0; bomb_hide();      /* the next room reloads the palette; restoring it here would turn the disc dull during the fade */
        if (BG0_KEPT) { BG0CNT = (u16)BG0_KEPT; BG0_KEPT = 0; }
    }
    else if (v == 40) { if (!BG0_KEPT) BG0_KEPT = BG0CNT | 0x10000; BG0CNT = (BG0CNT & ~3) | 2; }
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
/* Solar Flare (Tien, Krillin; Nov 9). The white flash of the Super Saiyan power-up above, from the same effect slot, while the fighter
   holds a pose; every ordinary enemy on screen is stunned. The stun is the game's own (state 1 of the enemy state table 0x0870F514,
   which Burning Attack's hit pushes: the dizzy pose with a 120-frame timer), pushed through the enemy's vtable (+0x6C, sub_0800AA9C)
   and its timer (the state's second part, {0x080497D4, frames}) set longer. Bosses and duels (any enemy whose stats row has its own
   defeat handler, not the usual 0x08708920) shrug it off. */
#define SOLAR_COST 40
#define CanAfford ((int (*)(u8 *, int))0x080134B9)
#define IN_COMBAT (*(volatile u32 *)0x03001988)
#define SOLAR_STUN 150
#define SOLAR_POSE_FRAMES 30
#define SOLAR_POSE (*(volatile u8 *)0x0203FFC4)
#define ENEMY_COUNT (*(volatile int *)0x03001BB0)
#define ENEMY_LIST ((u8 **)0x03001BB4)
#define VIEW ((volatile int *)0x030019BC)
#define STUN_DESC 0x0870F51C
static int stunned(u8 *e) {
    int depth = *(int *)(e + 0x23C);
    return depth >= 1 && depth <= 5 && *(u32 *)(e + 0x240 + 8 * (depth - 1) + 4) == STUN_DESC;
}
static void stun(u8 *e, int frames) {
    int depth;
    u32 *top, *timer;
    if (!stunned(e)) {
        depth = *(int *)(e + 0x23C);
        if (depth < 1 || depth >= 5) return;
        CALL_V(e, 0x6C)(e, 1);
        if (!stunned(e)) return;
    }
    depth = *(int *)(e + 0x23C);
    top = *(u32 **)(e + 0x240 + 8 * (depth - 1));
    if (!top || top[2] < 2) return;
    timer = (u32 *)top[4];
    if (timer && timer[1] < (u32)frames) timer[1] = frames;
}
static int boss(u8 *e) {        /* an ordinary enemy's stats row (e +0x224) has the usual defeat handler (+0x14); bosses and duels have their own */
    const u8 *row = *(const u8 **)(e + 0x224);
    return !row || *(const u32 *)(row + 0x14) != 0x08708920;
}
#define SOLAR_AT (*(volatile u32 *)0x0203FFCC)
#define SOLAR_REST 360                 /* six seconds before the next one: a stunned crowd can't be kept down for good */
int solar_can(u8 *record) { return IN_COMBAT && !SB.phase && !SOLAR_POSE && (!SOLAR_AT || FRAMES - SOLAR_AT >= SOLAR_REST) && CanAfford(record, SOLAR_COST); }
void solar_use(u8 *record, void *player) {
    int i, n = ENEMY_COUNT, x, y;
    Spend(record, SOLAR_COST);
    SOLAR_AT = FRAMES;
    SB.phase = FLASH_PHASE; SB.frame = 0; *BOMB_OLD = BLDCNT;
    SB.old3 = (void *)EFFECTS[3];
    SB.ticker[0] = (u32)spirit_vt;
    EFFECTS[3] = (u32)SB.ticker;
    SOLAR_POSE = SOLAR_POSE_FRAMES;
    PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x288, 0x40, 0);
    if (n > 32) n = 32;
    for (i = 0; i < n; i++) {
        u8 *e = ENEMY_LIST[i];
        if (!e || *(int *)(e + 0x28C) <= 0 || !*(u8 *)(e + 0x1CC) || *(u8 *)(e + 0x1D0) != 0 || boss(e)) continue;
        x = *(int *)(e + 0x1A0) >> 8; y = *(int *)(e + 0x1A4) >> 8;
        if (x < VIEW[0] - 16 || x > VIEW[2] + 16 || y < VIEW[1] - 16 || y > VIEW[3] + 32) continue;
        stun(e, SOLAR_STUN);
    }
}
static int solar_tick(void *player) {
    if (!SOLAR_POSE) return 0;
    if (--SOLAR_POSE == 0) { slot_pose(player, 0); return 0; }
    if (has_slot(player, 13)) slot_pose(player, 13); else slot_pose(player, SLOT_ARMS_UP);
    return 1;
}

static int spirit_tick(void *player)
{
    if (solar_tick(player)) return 1;
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
void wish_potential(void);
static void new_game_plus(void);
void wish_power(int *sp) {      /* the mod's operations (one native, retail 0xEB, which no script calls): 0 the wish for power, 1 hidden potential, 2 New Game+ */
    int c, i, n = *sp, which = sp[n];
    *sp = n - 1;
    if (which == 1) { wish_potential(); return; }    /* Hidden potential (Nov 9) */
    if (which == 2) { new_game_plus(); return; }
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
    if (c == 7 && (REC(0)[0] & 1) && (REC(4)[0] & 1)) *(int *)(r + 8) = -1;       /* no fusion time limit (story_sync); a Fusion Dance's Gogeta keeps his (gogeta_keep) */
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

static int beam_pose(void *sprite);
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
    Sprite_SetFacing(sprite, beam_pose(sprite));
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
    Sprite_SetFacing(sprite, beam_pose(sprite));
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
/* The Kamehameha's code shows frames 0-2 of the fighter's slot 18. Vegeta's figures hold his two-frame Big Bang there, so build.py gives them a pose
   of their own in slot BEAM_POSE (beam_poses): his wind-up, then Final Flash's push with both hands; and the LoG2 figures, whose slot 18 holds
   Big Bang's code's arm out (held_poses), get their fist in, then the arm out. Every Kamehameha-code move and the Electric Kamehameha's
   (beam_use, black_kame_use, kv_use, kame_use, wave_use) shows it where the figure has one; any other figure uses slot 18 as before. */
#define BEAM_POSE 31
static int beam_pose(void *sprite) {
    const u8 *actor = *(const u8 * const *)((const u8 *)sprite + 0x58);
    return actor && actor[0] > BEAM_POSE && *(const u32 *)(actor + 0x54 + 4 * BEAM_POSE) ? BEAM_POSE : 0x12;
}
static void kv_use(u8 *record, void *sprite, const int *vt) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, beam_pose(sprite));
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
/* Master Roshi's Kamehameha: his own pose (slot BEAM_POSE, build.py roshi_pose), and the beam from his hands. The Kamehameha's update (0x0801BE40)
   places the beam on its 24th frame at the fighter's place plus a step per facing (0x0871E128), set for Goku's reach; Roshi's arms are
   shorter, so it started a few pixels past his hands. His behaviour gets kame_vt (build.py: the Kamehameha's, with this update), which then
   moves the beam (its place: +0x20, +0x24, sub_080207D2) by ROSHI_BEAM per facing (down, up, left, right; measured in the emulator). */
const int kame_vt[9] = {1};
#define Kame_Update ((void (*)(u32 *, u8 *))0x0801BE41)
static const signed char ROSHI_BEAM[4][2] = {{0, 0}, {0, 0}, {5, 0}, {-5, 0}};
void kame_update(u32 *self, u8 *player) {
    Kame_Update(self, player);
    if (*(u16 *)(player + 0x12) == 0x18 && self[2]) {
        u8 *beam = (u8 *)self[2]; int f = player[0x10] & 3;
        *(int *)(beam + 0x20) += ROSHI_BEAM[f][0];
        *(int *)(beam + 0x24) += ROSHI_BEAM[f][1];
    }
}
void kame_use(u8 *record, void *sprite) {
    if (record == RECORDS && derived_level(0, 15) == 2 && MASTERY_BYTES[21] < 255) { bench_mine(1); MASTERY_BYTES[21]++; }
    ((void (*)(u8 *, void *))0x0801A35B)(record, sprite);
    if (beam_pose(sprite) == BEAM_POSE) Sprite_SetFacing(sprite, BEAM_POSE);     /* a figure with a pose of its own (build.py beam_poses, held_poses) */
    if (record[0x14] == FORM_ROSHI || record[0x14] == FORM_ROSHI_MAX) {
        u32 *state = *(u32 **)((u8 *)sprite + 0x14);
        if (state && state[0] == 0x0804D9F8) state[0] = (u32)kame_vt;
    }
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
#define dragon4_live (*(u32 *volatile *)0x0203FFB8)      /* the Super Dragon Fist in play, for combat_hook (after SK) */
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
/* Dragon Fist Explosion (skill 5, the original game's, Gogeta's) is Goku's too as a Super Saiyan 3 (Nov 11, the owner: "give ssj3 Goku
   access to the dragon fist explosion ... not the same one ssj4 Goku has but the one from gogeta"). It comes with Super Saiyan 3
   (skills_sync) and fires only in a Super Saiyan 3 form (ssj3_goku_rows, build.py: his two original looks' and Kid Goku's); Gogeta's is
   as it was. The move's code shows the figure's slot 19 by frame number (0-3, then 2 and 3 in turn), and on Goku's Super Saiyan 3
   figures slot 19 is Instant Transmission's three frames (he would fade away and draw a fourth frame that isn't there): they carry a
   pose for it in slot FIST_POSE (build.py fist_poses: his stance, his ki blast's wind-up, then its arm out, held), shown instead. */
extern const u8 ssj3_goku_rows[];
#define FIST_POSE 29
#define DragonFist_Use ((void (*)(u8 *, void *))0x08019EB9)
static int is_ssj3_goku(int form) {
    const u8 *p;
    for (p = ssj3_goku_rows; *p != 255; p++) if (*p == form) return 1;
    return 0;
}
int dragon_can(u8 *record) { return (record != RECORDS || is_ssj3_goku(record[0x14])) && DragonFist_Can(record); }
void dragon_use(u8 *record, void *sprite) {
    const u8 *actor = *(const u8 * const *)((const u8 *)sprite + 0x58);
    DragonFist_Use(record, sprite);
    if (actor && actor[0] > FIST_POSE && *(const u32 *)(actor + 0x54 + 4 * FIST_POSE)) Sprite_SetFacing(sprite, FIST_POSE);
}
/* The Fusion Dance (skill 12) can't be used in Super 13's fight (Nov 11, the owner: "make the Super 13 fight specifically only startable
   and maybe only playable as Goku"): its finish is Goku's Spirit Bomb. Zone 26's areas 15 to 18: Android 13, his change, Super 13, the finish. */
#define FusionCan ((int (*)(u8 *))0x0801A169)
int fusion_can(u8 *record) {
    u16 at = *(volatile u16 *)0x0300197C;
    if ((at & 0xFF) == 26 && (at >> 8) >= 15 && (at >> 8) <= 18) return 0;
    return FusionCan(record);
}
#define KameCan ((int (*)(u8 *))0x0801A335)
static int is_ssj4(int form);
int ssj4_kame_can(u8 *record) { return is_ssj4(record[0x14]) && KameCan(record); }     /* 10x Kamehameha: Super Saiyan 4 only */

/* Full Power Energy Wave, for the androids: the Electric Kamehameha's code with green frames, as in Gero's Legacy. Gohan keeps the original. */
#define Wave_Start ((void (*)(u32 *, void *))0x0801ADA9)
const u32 wave_params[12] = {1};
const int wave_vt[9] = {1};
static int s13_firing(void) { return *(u8 *)0x03001068 == 8 && FORM_OF(8) == FORM_S13; }
/* His charging ball too (16:59, the owner: "Super 13 beam is facing out of his ass when facing right"): it is made at the fighter's place
   plus a step per facing (0x0871DE94), which facing right put it behind him, at his hip; S13_BALL moves it to his hands (+0x20, x). */
static const signed char S13_BALL[4] = {0, 0, 0, 14};
void wave_start(u32 *self, void *player) {
    u32 *beam;
    Wave_Start(self, player);
    beam = (u32 *)self[2];
    if (beam && s13_firing()) *(int *)((u8 *)beam + 0x20) += S13_BALL[((u8 *)player)[0x10] & 3];
    if (beam) {
        const u32 *mine = &wave_params[self[3] * 4];
        beam[0x40 / 4] = (u32)mine;
        beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = mine[2];
        MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (void *)((u32 *)mine[2])[2], 0x40);
    }
}
/* Super 13's beam comes out of his hands (Nov 10, the owner: "make sure Super 13 beam actually comes out of his hands not below it"). The wave's
   update (0x0801AE32) places the beam on its 24th frame at the fighter's place plus a step per facing (0x0871DEC4), set for a normal fighter's
   hands; his thrust holds them higher and further forward. Then it is moved there: the beam's place is +0x20, +0x24 (sub_080207D2).
   Measured in the emulator: S13_BEAM, per facing (down, up, left, right). */
#define Wave_Update ((void (*)(u32 *, u8 *))0x0801AE33)
static const signed char S13_BEAM[4][2] = {{0, 0}, {0, 0}, {-14, -9}, {18, -9}};
void wave_update(u32 *self, u8 *player) {
    Wave_Update(self, player);
    if (*(u16 *)(player + 0x12) == 0x18 && s13_firing() && self[2]) {
        u8 *beam = (u8 *)self[2]; int f = player[0x10] & 3;
        *(int *)(beam + 0x20) += S13_BEAM[f][0];
        *(int *)(beam + 0x24) += S13_BEAM[f][1];
    }
}
/* Wrath of the Gods: Beerus's own beam (Nov 11, the owner: "Change Beerus beam attack to actually fire from the hand and also give him his
   own custom light yellow Frieza style finger beam attack not kamehameha called Wrath of the Gods"; lib/wrath.py tells it whole).
   He fights on Kid Buu's behaviour, whose beam is the game's enemy beam: a Kamehameha made as a charging ball at the fighter's place plus
   a step per facing and laid as a beam on the behaviour's 9th frame at another (0x0875925C, set for Kid Buu: on Beerus the beam left from
   his shins). The enemy beam's table of functions is the mod's copy for every enemy (build.py: wrath_vt, named by the word at 0x080331D0),
   with its start and its every-frame wrapped here; they add nothing to the game's unless the fighter's figure is Beerus (wrath_who: where
   the actor table keeps his record). For him the glint and the beam go to his fingertip (wrath_at: steps per facing, for the ball, then
   for the beam), the beam object gets his frames as beam_start gives the Special Beam Cannon its (wrath_params: thin, light yellow),
   and his pose is his ki blast's wind-up, then its arm out, held: the game shows the two arm-out frames by turns, which from the front
   are two different arms. The beam's strength, reach and time are the enemy beam's. */
#define EBeam_Start ((void (*)(u32 *, u8 *))0x08033003)
#define EBeam_Update ((void (*)(u32 *, u8 *))0x080330AB)
#define WRATH_ARM_OUT 2                    /* the behaviour's frame his arm goes out on: shown two frames later, as the glint first is (its ball's first row, four frames, is empty) */
const int wrath_vt[9] = {1};
const volatile u32 wrath_params[12] = {1};   /* volatile, as boss_tab: read at fixed places here, and filled in after the compiler has seen {1, 0} */
const volatile u32 wrath_who[1] = {1};
const volatile signed char wrath_at[2][4][2] = {{{1}}};
static int wrath_mine(const u8 *e) { return *(const u32 *)(e + 0x58) == *(const u32 *)wrath_who[0]; }
void wrath_start(u32 *self, u8 *e) {
    u32 *beam;
    const u32 *rows;
    int f;
    EBeam_Start(self, e);
    beam = (u32 *)self[4];
    if (!IN_EWRAM(beam) || !wrath_mine(e)) return;
    f = e[0x10] & 3;
    beam[0x20 / 4] += wrath_at[0][f][0]; beam[0x24 / 4] += wrath_at[0][f][1];
    rows = (const u32 *)wrath_params[2];
    beam[0x40 / 4] = (u32)wrath_params;
    beam[0x44 / 4] = beam[0x48 / 4] = beam[0x4C / 4] = (u32)rows;
    MemCopy((u8 *)0x06010000 + *(u16 *)(beam + 3) * 0x20, (const void *)rows[2], 0x40);
}
void wrath_update(u32 *self, u8 *e) {
    int at = *(u16 *)(e + 0x12), f = e[0x10] & 3;
    u32 *beam;
    EBeam_Update(self, e);
    if (!wrath_mine(e)) return;
    e[0x11] = at >= WRATH_ARM_OUT;
    beam = (u32 *)self[4];
    if (at == 8 && IN_EWRAM(beam)) { beam[0x20 / 4] += wrath_at[1][f][0]; beam[0x24 / 4] += wrath_at[1][f][1]; }
}
void wave_use(u8 *record, void *sprite) {
    int level = record[record[0x15] * 2 + 0x2E];
    u32 *b = Alloc(0x10);
    if (b) { b[0] = (u32)wave_vt; b[1] = 0; b[3] = level; }
    Sprite_SetFacing(sprite, beam_pose(sprite));
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
   None of them works in Kaioken, and Kaioken works only in a base form (and, fully mastered, in Super Saiyan: kaioken_can). A form's up (row +0x16) is the tier above it; Kaioken and Goku's
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
#define EARLY (*(volatile u8 *)0x0203F253)            /* form + 1 a power-up started from, while it plays on its new figure */
/* mastered Kaioken's bar (kk_track, below) */
#define KK_GUARD (*(volatile u16 *)0x0203F250)
#define KK_ON (*(volatile u8 *)0x0203F252)
#define KK_EMPTY (*(volatile u8 *)0x0203F254)       /* 1: the bar ran out, 2: powering down for it */
#define KK_DRAWN (*(volatile u8 *)0x0203F255)       /* the bar's columns on the HUD as last drawn */
#define KK_POOL (*(volatile u16 *)0x0203F256)       /* Super Saiyan's pool + 1, kept while Super Saiyan Kaioken powers down to Super Saiyan */
static void power_to(u8 *record, void *sprite, int form, const void *vt) {
    XFORM = form + 1; XFORM_FROM = record[0x14]; XFORM_AT = FRAMES;
    /* Kaioken and Blue power up on their new figure: the old one's slot 10 is Super Saiyan's (gold hair). build.py powerup_frames makes theirs. */
    Sprite_SetCharacter(sprite, Form_Sprite((void *)(form_table + form * 24)));
    EARLY = record[0x14] + 1;
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
static int is_ssg(int form);
static int is_fp(int form);
/* Super Saiyan 2 follows Super Saiyan in its own skill (Nov 9, the owner: "make it so SS2 follows SS1 and precedes SS3 so it doesn't have
   to be swapped for SS1 in the skill menu"): pressed in a Super Saiyan whose next form is Super Saiyan 2, once the story has opened it, Super
   Saiyan goes up to it; pressed in Super Saiyan 2 (or without the energy to go up) it powers down as before. Super Saiyan 3 then goes up
   from Super Saiyan 2 (ss3_direct). The Super Saiyan 2 skill still works where a fighter holds it. */
static int ss_to_ss2(u8 *record) {
    int form = record[0x14], f = flags_of(form);
    return (f & 1) && !(f & 2) && !is_kaioken(form) && up_of(form) != 255 && is_ss2(up_of(form)) && ss2_open(record, form_table[form * 24 + 0x0C]) && can_step(record);
}
/* A form that isn't transformed and has no form above (Great Saiyaman: up 255, down his outfit) can't use Super Saiyan: the game's SS_Can only
   refuses when up equals down, so it changed him into form 255 and the next form lookup jumped to garbage (Nov 10, audit_moves). */
int ss_can(u8 *record) {
    int form = record[0x14];
    if (!(flags_of(form) & 3) && up_of(form) == 255) return 0;
    return is_kaioken(form) || is_ssg(form) || is_fp(form) ? 0 : ss_to_ss2(record) || SS_Can(record);
}
/* Going up to Super Saiyan 2 plays slot 10 on the Super Saiyan figure, and Goku's is BF's change into Super Saiyan 3 (his hair grows long):
   his Super Saiyan figures carry a change of their own for 2 in slot SS2_POSE (build.py held_poses: his power-up's crouch, then arms up,
   then his stance, front in every view), played instead. Same length as slot 10's, so the power-up ends as before. */
#define SS2_POSE 30
static void to_ss2(u8 *record, void *sprite) {
    const u8 *actor = *(const u8 * const *)((const u8 *)sprite + 0x58);
    SS3_Use(record, sprite);
    if (actor && actor[0] > SS2_POSE && *(const u32 *)(actor + 0x54 + 4 * SS2_POSE)) Sprite_SetFacing(sprite, SS2_POSE);
}
void ss_use(u8 *record, void *sprite) {
    XFORM = 0;
    if (ss_to_ss2(record)) to_ss2(record, sprite);        /* the form's up: Super Saiyan 2, as its own skill goes (ss2_use) */
    else SS_Use(record, sprite);
}
int ss2_can(u8 *record) {
    int form = record[0x14], f = flags_of(form);
    if (is_ss2(form)) return 1;
    return (f & 1) && !(f & 2) && !is_kaioken(form) && up_of(form) != 255 && is_ss2(up_of(form)) && ss2_open(record, form_table[form * 24 + 0x0C]) && can_step(record);
}
void ss2_use(u8 *record, void *sprite) {
    XFORM = 0;
    if (is_ss2(record[0x14])) power_down(record, sprite); else to_ss2(record, sprite);
}
/* The HUD's skill icon (sub_0800B99C asks sub_080135A2 for the held skill's row: icon +4 when it can be used, +8 when not). In Super
   Saiyan 2 reached through Super Saiyan's skill, that skill shows Super Saiyan 2's icon (Nov 10, the owner: "when Goku transforms to SSJ2 the
   icon doesn't reflect SSJ2"). Only the HUD comes here: using the skill still goes through Super Saiyan's row (ss_use). */
#define SkillRow ((const u8 *(*)(u8 *, int))0x080135A3)
const u8 *hud_skill_row(u8 *record, int i) {
    const u8 *row = SkillRow(record, i);
    if (record[0x0C] && record[0x0D + i] == 20 && is_ss2(record[0x14])) row += (SS2_SKILL - 20) * 24;
    return row;
}
/* The HUD's bars (sub_0800B99C) are drawn a column at a time from a 41-column table, and the loops for the two Super Saiyan pools (lengths at
   sp + 0x502 and + 0x503: pool * 41 / the EP maximum) have no upper bound: a pool above the EP maximum walks off the table and writes bytes
   of the bar's picture wherever the next words point, the sprite palette among them (Nov 10, the owner on a move GIF: "ssj4 Gogeta has a
   weird green outline": the capture tool had filled the pools before raising the EP maximum, and the stray bytes turned palette slot 127,
   his fur's shade, green). The skill icon's call comes after the lengths are worked out and before the loops, so it caps them here. */
void hud_row_guard(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global hud_row_guard\nhud_row_guard:\n"
        "movs r3, #5\nlsls r3, r3, #8\nadd r3, sp\n"
        "ldrb r2, [r3, #2]\ncmp r2, #41\nbls 1f\nmovs r2, #41\nstrb r2, [r3, #2]\n1:\n"
        "ldrb r2, [r3, #3]\ncmp r2, #41\nbls 2f\nmovs r2, #41\nstrb r2, [r3, #3]\n2:\n"
        "ldr r3, =hud_skill_row\nbx r3\n.ltorg\n");
static int slot_of(const u8 *rec, int skill);
/* From a Super Saiyan whose next form is Super Saiyan 2: once Super Saiyan 2 is open, the way up is through it (the Super Saiyan skill
   reaches it, held or not: ss_use); before the story opens it, Super Saiyan 3 goes straight on as in the retail game (its form: Super
   Saiyan 2's next). */
static int ss3_direct(u8 *record) {
    int form = record[0x14], ss3;
    if (!(flags_of(form) & 1) || up_of(form) == 255 || !is_ss2(up_of(form))) return -1;
    if (ss2_open(record, form_table[form * 24 + 0x0C])) return -2;
    ss3 = up_of(up_of(form));
    return ss3 != 255 && (flags_of(ss3) & 2) ? ss3 : -2;
}
int ss3_can(u8 *record) {       /* Super Saiyan 3 starts from Super Saiyan 2 where a form has one and it is held */
    int form = record[0x14], d = ss3_direct(record);
    if (is_kaioken(form) || is_ssj4(form) || is_ssg(form) || is_fp(form)) return 0;
    if (d == -2) return 0;
    if (d >= 0) return SS3_Can(record);
    if ((flags_of(form) & 2) && up_of(form) != 255 && is_ssj4(up_of(form))) return 1;        /* Kid Goku's Super Saiyan 3: powers down */
    return SS3_Can(record);
}
void ss3_use(u8 *record, void *sprite) {
    int d = ss3_direct(record);
    XFORM = 0;
    if (d >= 0) { XFORM = d + 1; XFORM_FROM = record[0x14]; XFORM_AT = FRAMES; }      /* xform_hook: Super Saiyan 3, not the form above */
    SS3_Use(record, sprite);
}
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
extern const u8 ssb_map[][2], kaioken_map[][2], ssg_map[][2];
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
    else if (form == FORM_GOGETA_DBS_SS) power_to(record, sprite, FORM_GOGETA_SSB_FORM, ssb_vt);    /* on his Blue figure: his Super Saiyan's power-up showed gold hair in the blue aura */
    else power_to(record, sprite, mapped(ssb_map, form), ssb_vt);
}
/* Kaioken (Goku and the humans): from a base form to its red copy (kaioken_map), a Super Saiyan class form without the +5, as the build
   makes its row, with the red aura. Its bar drains as Super Saiyan's does and it costs health as it goes (ss_tick); hits are 1.25x to 1.75x
   by its mastery. Fully mastered: Goku's Super Saiyan forms have a red copy too (Super Saiyan Kaioken, down to Super Saiyan), and the health
   cost becomes a bar of its own that also takes hits without a stagger (kk_track). */
static int is_kaioken(int form) {
    int i;
    for (i = 0; kaioken_map[i][0] != 255; i++) if (kaioken_map[i][1] == form) return 1;
    return 0;
}
int mastery_level(int c, int skill);
static int kk_mastered(void) { return mastery_level(*(u8 *)0x03001068, KAIOKEN_SKILL) == 2; }
int kaioken_can(u8 *record) {
    int form = record[0x14];
    if (is_kaioken(form)) return 1;
    if (mapped(kaioken_map, form) == 255) return 0;
    if (!(flags_of(form) & 3)) return can_start(record);              /* from a base form */
    return kk_mastered() && can_step(record);                          /* Super Saiyan Kaioken: from Super Saiyan once Kaioken is fully mastered */
}
void kk_down(u8 *record, void *sprite) {       /* out of Kaioken: to its base, or from Super Saiyan Kaioken to Super Saiyan with its pool */
    if (flags_of(form_table[record[0x14] * 24 + 0x17]) & 1) KK_POOL = *(u16 *)(record + 0x1E) + 1;
    SS_Use(record, sprite);
}
void kaioken_use(u8 *record, void *sprite) {
    int form = record[0x14];
    XFORM = 0;
    if (is_kaioken(form)) kk_down(record, sprite);
    else power_to(record, sprite, mapped(kaioken_map, form), ssj4_vt);
}
/* Super Saiyan God (Nov 9): Goku, from a base form to its red-haired copy (ssg_map), with the red aura. Its row is Super Saiyan's class without
   the +5 (taken off in combat_hook): 1.75x, and the pool drains at half Super Saiyan's rate (ss_tick). No other tier goes up from it; pressed
   again it powers down to base. Learned after the Battle of Gods (more flag MORE_BOG_DONE) once Goku's Super Saiyan is mastered (skills_sync). */
static int is_ssg(int form) {
    int i;
    for (i = 0; ssg_map[i][0] != 255; i++) if (ssg_map[i][1] == form) return 1;
    return 0;
}
int ssg_can(u8 *record) {
    int form = record[0x14];
    if (is_ssg(form)) return 1;
    return mapped(ssg_map, form) != 255 && !(flags_of(form) & 3) && can_start(record);
}
void ssg_use(u8 *record, void *sprite) {
    int form = record[0x14];
    XFORM = 0;
    if (is_ssg(form)) SS_Use(record, sprite);
    else power_to(record, sprite, mapped(ssg_map, form), ssj4_vt);
}
/* Skills beyond the six a fighter can hold (Nov 9). Each party character has a book (skill_book, build.py) of up to 16 skills the
   loadout can hold; record +0x22 is a mask over it of the ones they know. Equipped skills sit in the record as always (+0x0D, levels
   +0x2E). The story's natives add (0xA4), remove (0xA5) and replace (0xA6) skills: ours do the same on the record and keep the book's
   mask in step, so a skill swapped out still learns, locks and unlocks. A skill learned with no free slot waits in the book; the
   pause menu's Skills tab swaps one in with SELECT. Skills earned by play (Kaioken, Galick Gun, each tier, the post-game moves, mastery)
   are learned by skills_sync. Retail moves' levels come with the character's level (the level-up script, 0x0877C9E8), so a move swapped
   back in takes the level that gives; a transformation's level is its mastery (mastery bytes in the bench's last group). */
extern const u8 skill_book[8][16], level_steps[][4];
static int ss2_open(const u8 *record, int owner);
#define KNOWN(rec) (*(u16 *)((rec) + 0x22))
#define MAX_HELD 6         /* skills a record holds: +0x0D..+0x12. +0x13 is the equipment's flags byte (Recalculate, 0x08013C67, rewrites it), not a seventh skill */
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
    bench_mine(0);
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
    if (slot_of(rec, skill) < 0 && rec[0x0C] < MAX_HELD) equip(c, rec, rec[0x0C], skill);
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
    if (rec[0x0C] < MAX_HELD) equip(c, rec, rec[0x0C], skill);
}
/* A save from the original game (Nov 9: the owner's 100% Buu's Fury save) went through the story scenes that unlock outfits and Super Saiyan 2
   (outfits.json "unlocks", build.py) before the mod could set its flags there. Once the ending is seen they are all past; a few scenes also
   set a story flag of their own (STORY_MARKS: the unlock's flag, the scene's), which tells it earlier. */
static const u16 story_unlocks[] = STORY_UNLOCKS, story_marks[][2] = STORY_MARKS;
/* Gogeta after the ending: no fusion time limit, and back in the party if a pick unfused him (Nov 10). Only once party_join has given him his
   five skills (a new game's record has three): the reward sets his flag a moment before it joins him, and putting him in between made
   party_join see him joined and skip his form, level and skills (test_zone26, depending on the frame count). */
static int gogeta_open(void) {                 /* is any of Gogeta's looks unlocked? (-1, or the first that is) */
    int first = outfit_index[7][0], n = outfit_index[7][1], i;
    for (i = 0; i < n; i++) if (outfit_open(&outfit_table[first + i])) return first + i;
    return -1;
}
/* A fusion that has gone wrong, after the ending (Nov 11, the owner: "Did the super 13 fight with DBZ Gogeta, noticed it swapped back to
   Goku for the spirit bomb scene and then ... Gogeta is stuck permanently fused and Goku and Vegeta aren't selectable"). A Fusion Dance
   (script native 0xA8) takes both dancers out of the party (record +0 bit 0), puts the fused fighter in, selectable (bits 0 and 1), and
   gives him a time (+8, frames) that the HUD counts down only while he is the one playing; at 0 the game's own script (global script
   503) takes him out again and puts the dancers back, selectable. Two things broke that: a scene that makes someone else play (native
   0x95: the Spirit Bomb finish, a Trial's set hero, a pick on Switch Character) stops the clock for good, and Gogeta's "no time limit"
   as a fighter of his own (gogeta_keep, party_join) fell on a danced Gogeta too, so the dancers never came back.
   fusion_end puts that right the way the game's script does: a fused fighter who isn't the one playing leaves and his dancers come
   back; one who is playing with no time limit gets one frame, so the game ends his fusion itself. `now` (Super 13's door and finish):
   the one playing ends too. -> 1 if a fusion was ended. Only after the ending: the story has fusions of its own, with no limit. */
static const u8 fusions[][3] = {{7, 0, 4}, {5, 2, 3}};       /* the fused fighter, his two dancers */
int fusion_end(int now) {
    int k, did = 0, me = *(u8 *)0x03001068;
    if (!GetFlag(G_FLAGS, 149)) return 0;
    for (k = 0; k < (int)(sizeof fusions / sizeof *fusions); k++) {
        u8 *f = REC(fusions[k][0]), *a = REC(fusions[k][1]), *b = REC(fusions[k][2]);
        if (!(f[0] & 1) || ((a[0] & 1) && (b[0] & 1))) continue;       /* not fused: he isn't in the party, or both dancers are */
        if (me == fusions[k][0] && !now) {
            if (*(int *)(f + 8) < 0) *(int *)(f + 8) = 1;
            continue;
        }
        a[0] |= 3; b[0] |= 3;
        f[0] &= ~1; *(int *)(f + 8) = 0;
        did = 1;
    }
    return did;
}
/* Gogeta as a fighter of his own (a look of his unlocked, after the ending): in the party with no time limit. Not while a Fusion Dance's
   Gogeta is out (his dancers aren't in the party): that one keeps his clock, and joins as himself once it has run out (story_sync). */
void gogeta_keep(void) {
    fusion_end(0);
    if (GetFlag(G_FLAGS, 149) && gogeta_open() >= 0 && (REC(0)[0] & 1) && (REC(4)[0] & 1)) {
        u8 *g = REC(7);
        *(int *)(g + 8) = -1;
        if (g[0x0C] >= 5) g[0] |= 1;
    }
}
static void story_sync(int post) {
    int i;
    for (i = 0; i < (int)(sizeof story_unlocks / sizeof *story_unlocks); i++)
        if (post) FLAG_BYTE(story_unlocks[i]) |= 1 << (story_unlocks[i] & 7);
    for (i = 0; i < (int)(sizeof story_marks / sizeof *story_marks); i++)
        if (GetFlag(G_FLAGS, story_marks[i][1])) FLAG_BYTE(story_marks[i][0]) |= 1 << (story_marks[i][0] & 7);
    /* The guest slot shows on Switch Character only once someone has joined it (record +0 bit 0, party_join). The original game plays it
       without joining (Broly's story fight), so such a save had Broly beaten (flag 111) and no slot to pick him in: he joins it. Only
       Broly: every other guest's flag is set by the script that joins him (party_join), and Broly's own fight sets 111 just before its
       join, which must stay the one that joins him (on his outfit, with the player's unspent stat points; test_story.py). */
    if (!(REC(8)[0] & 1)) {
        int first = outfit_index[8][0], n = outfit_index[8][1];
        for (i = 0; i < n; i++)
            if (outfit_table[first + i].flag == 111 && outfit_open(&outfit_table[first + i])) {
                int st[3] = {2, 8, outfit_table[first + i].form};
                party_join(st);
                break;
            }
    }
    /* Gogeta's unlocks (Nov 11, the owner: "keep DBZ Gogeta as an unlock how he was in base game from getting all the exhibits", "make
       Gogeta DBS and SSB unlock from Battle of Gods", Super Saiyan 4 Gogeta "the hardest trials ... reward"). His first look, the original
       game's (GOGETA_FLAG), opens once the ending is seen with all 15 Z-Fighter exhibits in the museum (their count is the four flags
       from 346: the official's "of 15 Z-Fighter exhibits"); the others have their own flags (outfits.json). His slot joins the party
       the first time one of his looks is open, wearing it; before, the Super 13 reward joined him. */
    if (post) {
        int k;
        if (GetFlag(G_FLAGS, 346) && GetFlag(G_FLAGS, 347) && GetFlag(G_FLAGS, 348) && GetFlag(G_FLAGS, 349))
            FLAG_BYTE(GOGETA_FLAG) |= 1 << (GOGETA_FLAG & 7);
        if (!(REC(7)[0] & 1) && (k = gogeta_open()) >= 0) {
            int st[3] = {2, 7, outfit_table[k].form};
            party_join(st);
        }
    }
    /* Post-game Gogeta stays fused (Nov 10, the owner: "Selected Gogeta in character select and he fucking unfused and got deleted from
       character select"). A fusion's time left is record +8 (frames; -1 = no limit; script native 0xA8 sets it), and the fighter HUD counts
       it down while a fusion form (flags bit 3, Gogeta's form 41) plays, unfusing at 0. The story's fusion ends at 0, and that 0 stayed
       in his record when the post-game joined him, so he unfused the moment he was picked. Joined after the ending: no limit. A save he
       already left gets him back. */
    gogeta_keep();
}
/* The Great Ape is shelved (Nov 10, the owner: "remove the whole great ape thing from the game and shelf it for now ... needs a redo for
   sprites"; its code is on the branch shelf/great-ape). A save from the Nov 9 build can hold one of its forms (now copies of the look it
   changed from: build.py SHELVED_FORMS) or its skills (48 and 49, now empty rows): the fighter goes back to his own look, and those skills
   leave his slots (the selection stays on the skill it was on, or goes to the first). Its book bits (Goku's 15, Vegeta's 10) go too: a bit with no book
   entry is cleared, so a skill given that place later doesn't come known. */
const u8 shelved_skills[] = SHELVED_SKILLS;
const u8 shelved_forms[][2] = SHELVED_FORMS;
static void shelved_fix(int c, u8 *rec) {
    int i, k, n = 0, pick = 0;
    for (k = 0; k < 16; k++) if (skill_book[c][k] == 255) KNOWN(rec) &= ~(1 << k);
    for (k = 0; k < (int)(sizeof shelved_forms / sizeof shelved_forms[0]); k++)
        if (rec[0x14] == shelved_forms[k][0]) rec[0x14] = shelved_forms[k][1];
    for (i = 0; i < rec[0x0C]; i++) {
        int s = rec[0x0D + i], gone = 0;
        for (k = 0; k < (int)sizeof shelved_skills; k++) if (s == shelved_skills[k]) gone = 1;
        if (gone) continue;
        if (i == rec[0x15]) pick = n;
        rec[0x0D + n] = s; rec[0x2E + 2 * n] = rec[0x2E + 2 * i]; rec[0x2F + 2 * n] = rec[0x2F + 2 * i];
        n++;
    }
    if (n == rec[0x0C]) return;
    rec[0x0C] = n;
    rec[0x15] = pick;                 /* the skill he had selected, where it is now; the first if it was one of the shelved */
}
void skills_sync(int c) {
    u8 *rec;
    int i, post = GetFlag(G_FLAGS, 149), gt = more_flag(MORE_GT_FLAG);
    story_sync(post);
    if (c > 7) return;
    rec = rec_of(c);
    shelved_fix(c, rec);
    for (i = 0; i < rec[0x0C]; i++) {
        if (c == 7 && rec[0x0D + i] == 21) rec[0x0D + i] = SSB_SKILL;          /* Gogeta's Super Saiyan Blue, from before it had its own row */
        set_known(c, rec[0x0D + i], 1);
        if (tier_of(rec[0x0D + i]) >= 0) rec[0x2E + 2 * i] = rec[0x2F + 2 * i] = mastery_level(c, rec[0x0D + i]);
    }
    if (book_at(c, 35) >= 0 && (knows(c, 20) || slot_of(rec, 20) >= 0) && ss2_open(rec, c) && !knows(c, 35) && slot_of(rec, 35) < 0)
        set_known(c, 35, 1);            /* Super Saiyan 2 comes through the Super Saiyan skill (ss_use): known, in the book, no slot taken */
    if (c == 0) {
        learn(c, KAIOKEN_SKILL, 1);
        learn(c, 36, gt); learn(c, TENX_SKILL, gt); learn(c, DRAGON4_SKILL, gt);
        {   /* Dragon Fist Explosion comes with Super Saiyan 3 (its book place was the shelved Great Ape's: a Nov 9 save's bit goes) */
            int ss3 = knows(0, 22) || slot_of(rec, 22) >= 0;
            if (!ss3 && slot_of(rec, 5) < 0) set_known(0, 5, 0);
            learn(c, 5, ss3);
        }
        learn(c, SSB_SKILL, post && mastery_level(0, 22) == 2);
        learn(c, SSG_SKILL, post && mastery_level(0, 20) == 2 && (more_flag(MORE_BOG_RITUAL) || more_flag(MORE_BOG_DONE)));     /* from the ritual on */
        learn(c, SUPER_KAME_SKILL, post && derived_level(0, 15) == 2 && KAME_COUNT >= SUPER_KAME_USES);
    }
    if (c == 1) learn(c, FP_SKILL, GetFlag(G_FLAGS, MYSTIC_FLAG));      /* Full Power: with the orange gi */
    if (c == 4) {
        learn(c, GALICK_SKILL, 1);
        learn(c, 36, gt); learn(c, FINAL_SHINE_SKILL, gt);
        learn(c, SSB_SKILL, post && mastery_level(4, 35) == 2);
    }
}
static int can_swap(int c) {                          /* does he know a skill he isn't holding? */
    u8 *rec = rec_of(c);
    int b;
    for (b = 0; b < 16; b++) if (skill_book[c][b] != 255 && KNOWN(rec) >> b & 1 && slot_of(rec, skill_book[c][b]) < 0) return 1;
    return 0;
}
/* the Skills tab (vtable 0x0804B024): SELECT swaps the chosen skill for the next one the fighter knows but isn't holding */
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
    if (c <= 7)                                          /* the hint, beside Select and Cancel (the game's buttons have no SELECT icon); with nothing
                                                            learned beyond what he holds, it says so (Nov 9: the owner took SELECT for broken) */
        AddWidget(obj, NewText(0, obj, 0x84, 0x90, can_swap(c) ? (const u16 *)L"SELECT: Swap" : (const u16 *)L"Nothing to swap", 5, 0, (void *)FONT));
    return r;
}
/* sub_0801C312 ends a power-up by moving the record to its form's up; xform_hook (at 0x0801C35C) lets XFORM choose instead. */
void xform_hook(void);
__asm__(".syntax unified\n.thumb\n.thumb_func\n.global xform_hook\nxform_hook:\n"
        "ldrb r0, [r7, #22]\nadds r1, r4, #0\nbl xform_target\nstrb r0, [r4, #20]\nlsls r3, r0, #1\nadds r0, r3, r0\nldr r3, =0x0801C365\nbx r3\n.ltorg\n");
/* Super Saiyan's drain (sub_0800E3E6) is about to take a unit from the pool (+0x1E): ss_tick sees it first. It returns 1 to skip the unit
   (a mastered form drains slower); in Kaioken it costs health too, and when health runs short the pool empties so the game powers down. */
static int mastery_skip(u8 *rec);
/* Fully mastered Kaioken (level 3) costs no health. It brings a bar of its own instead, half the fighter's health, drawn cyan over the health bar
   (kk_hud): it pays Kaioken's cost as it goes, takes the hits first, and while it lasts hits don't stagger the fighter (kk_absorb). When it runs out
   the Kaioken ends (kk_track). */
static int flags_of(int form);
static void kk_pool_back(u8 *rec) {     /* the power-down empties the pool (retail goes to base): back in Super Saiyan, it has what it had */
    if (KK_POOL && !is_kaioken(rec[0x14]) && (flags_of(rec[0x14]) & 1)) { *(u16 *)(rec + 0x1E) = KK_POOL - 1; KK_POOL = 0; }
}
#define hud_widget (*(u8 * volatile *)0x0203F258)     /* the HUD widget seen while in Kaioken (cleared outside it) */
static int kk_mastered(void);
static void kk_start(const u8 *rec) {
    if (KK_ON) return;
    KK_ON = 1; KK_EMPTY = 0; KK_GUARD = *(const short *)(rec + 0x18) / 2;
}
/* every frame (player_input): the bar's start and end, the HUD's redraw when it changes, and the figure of a power-up that was cut short */
void kk_track(void) {
    u8 *rec = RECORDS + *(u8 *)0x03001068 * RECORD_SIZE, *me = PLAYER_OBJ;
    int form = rec[0x14], max = *(short *)(rec + 0x18), cols;
    /* (These variables aren't cleared at boot: heap_init's timing is tight, and even a few more stores there leave the game a frame behind every
       few dozen. Each is checked before use: EARLY only within a power-up's time, the rest are reset outside Kaioken.) */
    if (EARLY) {
        u32 *state = me ? *(u32 **)(me + 0x14) : 0;
        if (!me || (u16)(FRAMES - XFORM_AT) >= 600) EARLY = 0;
        else if (!state || (state[0] != (u32)ssb_vt && state[0] != (u32)ssj4_vt)) {
            if (form == EARLY - 1) Sprite_SetCharacter(me, Form_Sprite((void *)(form_table + form * 24)));
            EARLY = 0;
        }
    }
    if (!is_kaioken(form)) {
        kk_pool_back(rec);
        if (!(flags_of(form) & 1)) KK_POOL = 0;
        KK_ON = 0; KK_GUARD = 0; KK_EMPTY = 0; KK_DRAWN = 0; hud_widget = 0; return;
    }
    if (kk_mastered()) kk_start(rec);
    if (KK_EMPTY == 1 && me) { KK_EMPTY = 2; kk_down(rec, me); }        /* the bar ran out: Kaioken ends */
    cols = max > 0 ? KK_GUARD * 41 / max : 0;
    if (cols != KK_DRAWN && hud_widget) *(u32 *)(hud_widget + 0x1C) = 0xFFFFFFFF;     /* the HUD redraws when its cached bar lengths differ */
}
int ss_tick(u8 *rec) {
    if (rec != RECORDS + *(u8 *)0x03001068 * RECORD_SIZE) return 0;
    kk_pool_back(rec);                 /* before the drain looks at the pool */
    if (is_kaioken(rec[0x14])) {
        short *hp = (short *)(rec + 0x16), cost = *(short *)(rec + 0x18) / 150;
        if (cost < 1) cost = 1;
        if (wearing(rec, GEAR_SHADES) && (SHADES_TICK ^= 1)) cost = 0;          /* King Kai's Shades: every other unit is free */
        if (kk_mastered()) {                                                     /* mastered: the bar pays */
            kk_start(rec);
            if (KK_GUARD > cost) KK_GUARD -= cost;
            else { KK_GUARD = 0; if (!KK_EMPTY) KK_EMPTY = 1; }
        }
        else if (*hp > cost + 1) *hp -= cost;
        else *(u16 *)(rec + 0x1E) = 0;
    }
    if ((is_ssg(rec[0x14]) || is_fp(rec[0x14])) && (SSG_TICK ^= 1)) return 1;      /* Super Saiyan God and Full Power drain at half the rate */
    if (potara_skip(rec)) return 1;
    if (mastery_skip(rec)) return 1;
    /* Super Saiyan 2 drains 4x as fast as Super Saiyan (Nov 10, the owner: "the SSJ2 ki drain seems to be nonexistent"; measured: it drained
       Super Saiyan's pool at Super Saiyan's rate, 1023 units at about 2.7 a second, over six minutes; Super Saiyan 3's pool lasts about 35
       seconds). Three more units with each one the game takes: about a minute and a half, less what mastery saves (the units it skips). */
    if (is_ss2(rec[0x14])) {
        u16 *pool = (u16 *)(rec + 0x1E);
        *pool = *pool > 4 ? *pool - 3 : 1;
    }
    return 0;
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
    if (wearing(rec, GEAR_GRAVITY)) every = (every + 1) / 2;     /* the Gravity Band: twice as fast */
    MASTERY_TICK++;
    if (MASTERY_TICK % every == 0 && MASTERY[m] < 255) {
        lv = mastery_level(c, tier_skill[t]);
        bench_mine(1); MASTERY[m]++;
        if (mastery_level(c, tier_skill[t]) != lv) PlaySound((void *)0x03003E5C, (void *)SOUND_MOVE, 0x40, 0);
    }
    lv = mastery_level(c, tier_skill[t]);
    return MASTERY_TICK % 5 < lv;
}
static int mastery_skip(u8 *rec) { return mastery_train(rec, 10); }
/* The wish for hidden potential: every party member's transformations gain 75 mastery (MASTERY_L2 is 100, MASTERY_L3 250). */
void wish_potential(void) {
    int i;
    bench_mine(1);
    for (i = 0; i < 21; i++) MASTERY[i] = MASTERY[i] > 255 - 75 ? 255 : MASTERY[i] + 75;
}
/* Uub becomes Majuub with Super Saiyan's mechanics, but without the gold aura (Android 13's power-up); Majuub changes back as a Super Saiyan does. */
extern const int absorb_vt[14];
/* Master Roshi's Max Power (Nov 9): Super Saiyan's power-up with a white aura, then hits 1.5x on Super Saiyan's ki bar. Buu's Fury has no
   bulked-up Roshi, so he keeps his own frames (the owner: "if the sprites exist if not just use the ones that do exist"). */
const u32 maxp_aura_field[9] = {1}, maxp_aura_other[21] = {1};
const int maxp_vt[14] = {1};
void maxp_start(u32 *state, void *sprite) { tinted_start(state, sprite, maxp_aura_field, maxp_aura_other); }
void maxp_use(u8 *record, void *sprite) {
    if (!(form_table[record[0x14] * 24] & 1)) power_up(sprite, maxp_vt);
    else SS_Use(record, sprite);
}
/* Full Power (Nov 9, the owner: "add a full power Mystic form for Mystic Gohan only don't allow any of his other forms to use it"): Gohan
   in his orange gi (form 13: the Elder Kai unlocked his potential) to its copy with white lightning on every frame (fp_map, build.py
   FP_LOOKS), powering up in Max Power's white aura. Its row is Super Saiyan's class without the +5 (taken off in combat_hook): 1.75x, and
   the pool drains at half Super Saiyan's rate (ss_tick), as Super Saiyan God's. No other form of his has it, no tier goes up from it, and
   Super Saiyan doesn't work in it; pressed again it powers down to the orange gi. Learned with the orange gi (MYSTIC_FLAG, skills_sync). */
extern const u8 fp_map[][2];
static int is_fp(int form) {
    int i;
    for (i = 0; fp_map[i][0] != 255; i++) if (fp_map[i][1] == form) return 1;
    return 0;
}
int fp_can(u8 *record) {
    int form = record[0x14];
    if (is_fp(form)) return 1;
    return mapped(fp_map, form) != 255 && !(flags_of(form) & 3) && can_start(record);
}
void fp_use(u8 *record, void *sprite) {
    int form = record[0x14];
    XFORM = 0;
    if (is_fp(form)) SS_Use(record, sprite);
    else power_to(record, sprite, mapped(fp_map, form), maxp_vt);
}
/* The crackle (Nov 9, the owner: "make the SSJ2 and Mystic forms lightnings more visible and more present", "make the lightning move with
   the SSJ or mystic aura", then "a bit too much lightning and too thick, also make the entire thing animated ... all or nothing"): the
   lightning of a Super Saiyan 2 form or Full Power (or powering up into it) is all here, none on the figure's frames: every 7 to 13 frames a
   thin bolt strikes beside his head or shoulders, on either side, and breaks up (four 32x32 frames over about 11 frames, build.py
   crackle_frames: cyan for Super Saiyan 2, white for Full Power), drawn as the hit sparks are (NewSpark on the actor list, gone after its
   last frame), so one or two are out at a time. Timed by the frame counter (the hook can run more than once a frame) and placed by a hash
   of it, so the game's random numbers are left alone. */
const u32 bolt_ss2[36] = {1}, bolt_fp[36] = {1};      /* three bolts x four frames x (origin, attributes, tiles): build.py fills them */
#define BOLT_NEXT (*(volatile u32 *)0x0203F26C)
/* A bolt's sprite memory. NewSpark asks the actor list's allocator (0x0801124C: best fit over the free blocks, in 64-byte units, a chain
   from the list's first byte; block k is 10 bytes at +0x694: +4 its size, +8 the next free one; a block cut off a larger one is never
   joined to it again) and, when nothing is free, makes room (0x08011732) by taking another sprite's tiles. So a bolt is a 16x16 piece
   (build.py BOLT_PIECE: 256 bytes; as 1 KB pieces two bolts out together cut 1 KB off the largest free block for good, and Broly's
   first conversation at Volcano Summit, which needs nearly all of it, took Broly's own tiles: he wasn't drawn while he spoke to a
   Super Saiyan 2, Nov 11), and it is only drawn when a free block holds it: a bolt never takes another sprite's memory. */
#define BOLT_BYTES 0x100
static int bolt_room(int bytes) {
    const u8 *list = (const u8 *)ACTORS;
    int k = list[0], n;
    for (n = 0; k != 0xFF && n < 64; n++, k = list[k * 10 + 0x69C])
        if (*(const u16 *)(list + k * 10 + 0x698) >= (bytes >> 6)) return 1;
    return 0;
}
static u32 bolt_hash(void) { u32 x = FRAMES * 0x9E3779B1u; x ^= x >> 15; x *= 0x85EBCA77u; x ^= x >> 13; return x; }
static void crackle(void) {
    u8 *rec = RECORDS + *(u8 *)0x03001068 * RECORD_SIZE, *me = *(u8 **)0x03001C34;
    int form = rec[0x14], box[4], v[2], pos[2], dx;
    u32 h;
    const u32 *set;
    if (!COMBAT_ON || !IN_EWRAM(me) || AURA_MODE > 1) return;
    if (XFORM && is_fp(XFORM - 1)) form = XFORM - 1;
    if (is_ss2(form)) set = bolt_ss2; else if (is_fp(form)) set = bolt_fp; else return;
    if ((int)(FRAMES - BOLT_NEXT) < 0 && BOLT_NEXT - FRAMES < 60) return;
    h = bolt_hash();
    BOLT_NEXT = FRAMES + 7 + h % 7;
    SpriteBox(box, me); VecOp(v, box, box + 2);
    dx = 5 + (h >> 8) % 6;
    pos[0] = (v[0] >> 1) + (h >> 12 & 1 ? dx : -dx); pos[1] = (v[1] >> 1) - 10 - (int)((h >> 16) % 10);
    if (!bolt_room(BOLT_BYTES)) return;
    { void *spark = NewSpark(0, pos, set + 12 * ((h >> 20) % 3), 4, 0x6000, BOLT_BYTES, 0x38); if (spark) ListAdd(ACTORS, spark); }
}
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
    if (potara_skip(rec)) return 0;
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
extern const u8 ssj4_bar[0x500], kk_bar[0x500];
#define HP_COLS ((const u32 *)0x08071CB0)
static void kk_hud(const u8 *widget, u8 *buf, const u8 *rec) {     /* mastered Kaioken's bar: cyan over the health bar's first columns */
    int max = *(const short *)(rec + 0x18), cols = 0, c, k;
    if (KK_ON && max > 0) {
        hud_widget = (u8 *)widget;
        cols = KK_GUARD * 41 / max;
        if (cols > 41) cols = 41;
        for (c = 0; c < cols; c++) for (k = 0; k < 3; k++) { u32 o = HP_COLS[c * 4 + k]; buf[o] = kk_bar[o]; }
    }
    KK_DRAWN = cols;
}
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
    kk_hud(widget, buf, rec);
    MemCopy((u8 *)0x06010000 + *(const u16 *)(widget + 12) * 32, buf, 0x500);
}
/* Against Super Saiyan's damage, Super Saiyan 2 hits 1.5x as hard and Super Saiyan 3 1.75x. hit[1] is the attack's damage scale (1024 = normal); team 2 is the player's side.
   Damage grows with the cube of the Strength stat, so scaling the stat itself would give about three times the damage.
   Super Saiyan 3 adds 15 to the stats where Super Saiyan adds 5: its attacks count from the Super Saiyan figure, and it keeps the extra Endurance and Speed. */
int mastery_level(int c, int skill);
int ng_cycle(void);
/* Post-game bosses (Nov 9, the owner, after a level 200 Super Saiyan Gogeta beat Super 13 easily and took almost no damage: "want post game
   bosses to be a bit more of a challenge"). They were tuned for a level 99 fighter, and the stats move damage steeply both ways (damage grows
   like (s + 100) * s^2 with the attacking stat, docs/modding.md, and Endurance cuts it as hard): at level 200, stats about 180, a fighter hit
   Super 13 three times as hard and took a fifth of his damage. Against an enemy on a row the mod added (every row past the game's STATS_ROWS,
   and Super 13's PHASE1_ROW and BOSS_ROW), a stat above BOSS_REF counts a quarter of what it is above: the player's Strength and Power on his
   hits (after his form's changes; the form's multiplier stays), his Endurance on the boss's; and the boss's hits grow with the fighter's health
   past BOSS_HP. Levelling still helps, a little. Measured in a rig (Super 13's row, stats 180 vs 100): hits on him a third, his hits on a
   10176-health fighter about 6% each. */
#define STATS_TABLE (*(const u8 * const *)(0x08000000 + STATS_REF))
#define BOSS_REF 110
#define BOSS_HP 4000            /* a fighter with more health than this takes that much more from a post-game boss (at most 3x): a hit stays a hit */
static int postgame_foe(const u8 *e) {
    const u8 *row, *t = STATS_TABLE;
    int i;
    if (!e || e[0x1D0] == 1) return 0;                    /* team 1: the player's side */
    row = *(const u8 * const *)(e + 0x224);
    if (row < t || row >= t + 28 * 1024 || (row - t) % 28) return 0;
    i = (row - t) / 28;
    return i >= STATS_ROWS || i == PHASE1_ROW || i == BOSS_ROW;
}
static u16 boss_stat(int s) { return s > BOSS_REF ? BOSS_REF + (s - BOSS_REF) / 4 : s; }
/* The boss bar (Nov 11, the owner: "give every single new boss fight a custom health bar too", "Add health bars to all the bosses in
   game right now and reuse Buus fury assets", and, of the bar this file drew by itself at first, "That's not what I meant by the boss
   hp bars at all. Use the ones that already existed in Buus Fury for boss fights.").
   Buu's Fury has a boss bar: the slanted red bar that slides in at the top right of the story's boss fights. It is an actor of the
   HUD's layer (vtable 0x0804CE28, made by 0x080195A8, which the story's scripts call through natives 0x8F and 0x90): two 32x8 sprites
   at x 160 and 192 on 0x200 bytes of tiles, 53 slanted columns, blacked from the right as the health goes (0x08019658). It shows its
   target's health (the enemy's method at vtable +0x64: health x 53 / the row's health, rounded down), or, with no target, the
   columns in its byte +0x15.
   The mod's fights have no script that makes one, so this file does, and nothing here draws: the game's own actor, art and code.
   Every fight the mod added (a stats row with a byte in build.py's boss_tab, from zone26.boss_table: the rows the mod adds and
   Android 13's and Super 13's; the Makyans' packs have none) gets the game's bar with no target, and its columns are kept here by
   the game's own rule (rounded down), so that foes of one name share it (the three Cell Juniors: their health added up, out of the
   most there was in this fight; a Junior who has fallen leaves the list). The story's own boss fights are not touched: their
   scripts make their bars as they always did, and while any boss bar is on the list none is made here.
   The room's boss is the foe with a bar whose row has the most health: there from the fight's first moment, as the story's are
   (the mod's bosses stand in their own rooms or come with their scenes; Semi-Perfect Cell starts a little above the screen's top
   edge, and a bar that waited to see him came up late). The bar is made at the player's input while the HUD is shown (0x03001069
   bit 1), so never during a scene. The story's scripts send their bars
   away themselves when the boss has fallen (native 0x91); the mod's fights end in many ways, so the mod's bars look after
   themselves: theirs is the game's table of ten functions with one answered here (bossbar_vt: "is it shown?", which the game asks
   every frame and its own answers with a plain yes). There the columns are kept, and when the boss has no health left, or is no
   longer there, the bar slides out as the story's do (its speed byte +0x17 = 0xFF: it takes itself off the list above the screen). */
struct bossbar { u8 *actor; int max; u16 area; u8 name, pad; };
#define BB (*(struct bossbar *)0x0203F280)
const volatile u32 boss_tab[2] = {1}; /* build.py: how many stats rows have a byte in the table; the table (rows of one name share a number, 255: no bar).
                                         Volatile: the build fills it in after the compiler has seen {1, 0}, which it would otherwise use for good */
#define BOSSBAR_VT 0x0804CE28u                                       /* the game's boss bar */
extern const int bossbar_vt[10];                                     /* the same, but for 'shown?' (build.py fills it) */
#define BossBar_New ((u8 *(*)(u8 *, u8 *, int, int))0x080195A9)      /* (0: allocate it, its target, from and to in hundredths of the bar) */
#define BOSSBAR_COLS 53
#define HUD_ON (*(volatile u8 *)0x03001069 & 2)
static int boss_name(const u8 *e) {
    const u8 *row, *t = STATS_TABLE;
    u32 i;
    if (!IN_EWRAM(e) || e[0x1D0] == 1) return 255;                     /* team 1: the player's side */
    row = *(const u8 * const *)(e + 0x224);
    if (row < t || (row - t) % 28) return 255;
    i = (row - t) / 28;
    return i < boss_tab[0] ? ((const u8 *)boss_tab[1])[i] : 255;
}
static int boss_now(int *hp, int *full) {      /* the room's boss: -> his number (255: nobody); the health of everyone of that name, and their rows' */
    int i, n = ENEMY_COUNT, name = 255, most = -1, sum = 0, all = 0;
    if (n > 32) n = 32;
    for (i = 0; i < n; i++) {
        const u8 *e = ENEMY_LIST[i];
        int k = boss_name(e), whole;
        if (k == 255) continue;
        whole = *(const int *)(*(const u8 * const *)(e + 0x224) + 4);
        if (whole > most) { most = whole; name = k; }
    }
    for (i = 0; i < n && name != 255; i++) {
        const u8 *e = ENEMY_LIST[i];
        int h;
        if (boss_name(e) != name) continue;
        h = *(const int *)(e + 0x28C) >> 10;
        if (h > 0) sum += h;
        all += *(const int *)(*(const u8 * const *)(e + 0x224) + 4);
    }
    *hp = sum; *full = all;
    return name;
}
static u8 *bossbar_listed(const u8 *mine, int other) {   /* a boss bar on the actor list: ours (other 0: -> it, if it is still there) or any but ours */
    const int *shown = (const int *)((const u8 *)ACTOR_LIST + 4), *away = (const int *)((const u8 *)ACTOR_LIST + 0x40C);
    int i, k;
    for (k = 0; k < 2; k++) {                             /* shown, and unloaded for a moment */
        const int *l = k ? away : shown;
        for (i = 0; i < l[0] && i < 128; i++) {
            u8 *a = (u8 *)l[i + 1];
            if (!IN_EWRAM(a) || (*(const u32 *)a != BOSSBAR_VT && *(const u32 *)a != (u32)bossbar_vt)) continue;
            if (other ? a != mine : a == mine) return a;
        }
    }
    return 0;
}
int bossbar_visible(u8 *a) {                              /* every frame, for a bar made here: its columns; away when the boss is */
    int hp, full, name, cols;
    if (a != BB.actor || a[0x17] == 0xFF) return 1;       /* (on its way out already) */
    name = boss_now(&hp, &full);
    if (name != BB.name || hp <= 0) {                     /* fallen, or gone: empty, and out */
        if (name == BB.name) a[0x15] = 0;
        a[0x17] = 0xFF; BB.actor = 0;
        return 1;
    }
    if (full > BB.max) BB.max = full;
    if (hp > BB.max) BB.max = hp;
    cols = (int)((u32)hp * BOSSBAR_COLS / (u32)BB.max);   /* the game's own rule (0x0804F874): rounded down */
    a[0x15] = cols > BOSSBAR_COLS ? BOSSBAR_COLS : cols;
    return 1;
}
static void bossbar_tick(void) {
    int hp, full, name;
    u16 at = *(volatile u16 *)0x0300197C;
    u8 *a = BB.actor ? bossbar_listed(BB.actor, 0) : 0;               /* (the list was emptied under it, or it has left) */
    if (a && a[0x17] == 0xFF) a = 0;                                  /* on its way out (a scene's native 0x91) */
    BB.actor = a;
    name = boss_now(&hp, &full);
    if (name == 255) { BB.name = 255; return; }                       /* nobody: the next boss here is another fight */
    if (a && bossbar_listed(a, 1)) {                                  /* a script has made the fight's own: ours goes at once */
        BOMB_LIST_REMOVE(ACTOR_LIST, a);
        BB.actor = 0;
        return;
    }
    if (a || !HUD_ON || hp <= 0 || bossbar_listed(0, 1)) return;      /* (one leaving has to be gone first) */
    a = BossBar_New(0, 0, 0, 100);                                    /* no target: it shows the columns in +0x15, kept in bossbar_visible */
    if (!a) return;
    *(u32 *)a = (u32)bossbar_vt;
    if (BB.area != at || BB.name != name || (hp >= full && full >= BB.max)) BB.max = 0;       /* another fight, or this one from its start */
    BB.area = at; BB.name = name; BB.actor = a;
    Actor_Add(ACTOR_LIST, a);
}
const int bossbar_vt[10] = {1};
void combat_orig(void *defender, int *hit);
__asm__(".syntax unified\n.thumb\n.thumb_func\ncombat_orig:\npush {r4, r5, r6, r7, lr}\nadds r6, r0, #0\nadds r4, r1, #0\nadds r1, #8\nldr r3, =0x0800E9E1\nbx r3\n.ltorg\n");
void combat_hook(void *defender, int *hit) {
    int scale = hit[1], form = FORM_OF(*(u8 *)0x03001068);
    u16 *stats = (u16 *)((u8 *)hit[3] + 0x1B0), strength = stats[0], power = stats[1];
    int mine = hit[3] && *((u8 *)hit[3] + 0x1D0) == 1;    /* the attacker (hit[3], the owner of a blast) is on the player's side (team 1). hit[0] is the direction */
    u16 *guard = 0, endurance = 0;                        /* the defender's Endurance while a post-game boss hits him */
    if (hit[3] && !mine && *((u8 *)defender + 0x1D0) == 1) {      /* New Game+: enemies hit half again as hard for each time round */
        int k = ng_cycle();
        if (k) hit[1] = scale + (scale >> 1) * k;
    }
    if (mine) {
        if (is_ssj4(form)) {                         /* Super Saiyan 4: 2.5x Super Saiyan's damage, Gogeta's 3x (from Super Saiyan 3's figure where it is that class) */
            hit[1] = form == FORM_GOGETA_SSJ4 ? scale * 3 : scale * 2 + (scale >> 1);
            if ((form_table[form * 24] & 2) && strength > 10 && power > 10) { stats[0] = strength - 10; stats[1] = power - 10; }
        }
        else if (is_ssb(form) || form == FORM_GOGETA_SSB_FORM) {      /* Super Saiyan Blue: 2x, from Super Saiyan's figure as Super Saiyan 3 */
            hit[1] = scale * 2;
            if (strength > 10 && power > 10) { stats[0] = strength - 10; stats[1] = power - 10; }
        }
        else if (is_kaioken(form)) {                 /* Kaioken: 1.25x, 1.5x mastered, 1.75x at its third level, from the fighter's own stats (its row is Super
                                                        Saiyan's class, which adds 5 to Strength and Power on the way in: taken off again, so Kaioken stays below Super Saiyan 2) */
            hit[1] = scale + (scale >> 2) * (1 + mastery_level(*(u8 *)0x03001068, KAIOKEN_SKILL));
            if (!(flags_of(form_table[form * 24 + 0x17]) & 1) && strength > 5 && power > 5) { stats[0] = strength - 5; stats[1] = power - 5; }
            /* (Super Saiyan Kaioken, down to Super Saiyan, keeps Super Saiyan's +5: 1.75x a Super Saiyan's hit) */
        }
        else if (is_ssg(form) || is_fp(form)) {      /* Super Saiyan God and Full Power: 1.75x, without Super Saiyan's +5 */
            hit[1] = scale + (scale >> 1) + (scale >> 2);
            if (strength > 5 && power > 5) { stats[0] = strength - 5; stats[1] = power - 5; }
        }
        else if (is_ss2(form) || form == FORM_MAJUUB || form == FORM_ROSHI_MAX || form == FORM_S13 || form == FORM_S17 || form == FORM_ROSE) hit[1] = scale + (scale >> 1);
        else if ((form_table[form * 24] & 2) && strength > 10 && power > 10) {
            hit[1] = scale + (scale >> 1) + (scale >> 2);
            stats[0] = strength - 10; stats[1] = power - 10;
        }
    }
    if (mine && dragon4_live) hit[1] += hit[1] >> 2;      /* Super Saiyan 4's Super Dragon Fist: 1.25x */
    if (mine && postgame_foe(defender)) { stats[0] = boss_stat(stats[0]); stats[1] = boss_stat(stats[1]); }      /* a post-game boss (above) */
    else if (hit[3] && !mine && postgame_foe((const u8 *)hit[3]) && *((u8 *)defender + 0x1D0) == 1) {
        int top = *(const short *)(RECORDS + *(u8 *)0x03001068 * RECORD_SIZE + 0x18);
        guard = (u16 *)((u8 *)defender + 0x1B0) + 2; endurance = *guard; *guard = boss_stat(endurance);
        if (top > BOSS_HP) hit[1] = hit[1] * (top < 3 * BOSS_HP ? top : 3 * BOSS_HP) / BOSS_HP;     /* and in step with his health */
    }
    combat_orig(defender, hit);
    if (guard) *guard = endurance;
    if (defender == PLAYER_OBJ && KK_ON && KK_GUARD && is_kaioken(form) && hit[6] > 0) {     /* hit[6]: the damage (1/1024ths); 0 means no damage and no stagger */
        int dmg = (hit[6] + 0x3FF) >> 10;
        if (dmg < KK_GUARD) { KK_GUARD -= dmg; hit[6] = 0; }
        else { hit[6] -= KK_GUARD << 10; KK_GUARD = 0; if (!KK_EMPTY) KK_EMPTY = 1; }      /* it breaks: the rest comes through */
    }
    hit[1] = scale; stats[0] = strength; stats[1] = power;
}

/* Markers on the flight map's mini-map (Nov 9; Black Star Odyssey's, bso/maps/worldmap_markers.py): every named place on Earth's map (0:50)
   gets a yellow diamond. The mini-map object's draw (vtable 0x0804D8A0 +0x10, 0x08027A75) draws the red player arrow; this runs it and adds
   one 8x8 8bpp sprite per place, copying the marker to OBJ tile 300. On Buu's Fury's map the controls bar takes tiles 86-213 (Black Star
   Odyssey's tile 150 is in it), two more sprites 206-241, the arrow 242; 300 is free (read from OAM in flight). build.py fills map_marks. */
extern const u8 map_marks[][2];
#define MARK_TILE 300
extern const int map_mark_count;
static const char mark_shape[8][9] = {"...K....", "..KYK...", ".KYYYK..", "KYYWYYK.", ".KYYYK..", "..KYK...", "...K....", "........"};
int minimap_draw(void *self, u32 *ctx) {
    int r = ((int (*)(void *, u32 *))0x08027A75)(self, ctx), i, j;
    u8 *tile = (u8 *)(0x06010000 + MARK_TILE * 32);
    if ((**(u16 **)0x03001980) != (0 | 50 << 8)) return r;
    for (i = 0; i < 8; i++)
        for (j = 0; j < 8; j += 2) {
            char a = mark_shape[i][j], b = mark_shape[i][j + 1];
            *(u16 *)(tile + i * 8 + j) = (a == 'Y' ? 5 : a == 'W' ? 2 : a == 'K' ? 1 : 0) | (b == 'Y' ? 5 : b == 'W' ? 2 : b == 'K' ? 1 : 0) << 8;
        }
    for (i = 0; i < map_mark_count; i++) {
        u16 *oam = (u16 *)ctx[0];
        oam[0] = map_marks[i][1] | 0x2000; oam[1] = map_marks[i][0]; oam[2] = MARK_TILE;
        ctx[0] += 8;
    }
    return r;
}

/* Perfect guard (Nov 9): R pressed just before an enemy's ki blast lands, facing it, sends the blast back at whoever fired it and takes no
   damage. The player's message handler (vtable 0x0804C9F0 +0x24, 0x08010DDF) gets hits as message 0 with the hit's description: team +0,
   box +4..+0x10, direction +0x14, the projectile +0x30. An enemy blast (vtable 0x0804B454) fires again for a new owner when +0x58 is set
   (+0x60 the owner), as a punched one does. */
#define PERFECT_FRAMES 10
#define BLAST_VT 0x0804B454
#define BULLET_VT 0x08049F0C      /* the shots of the gunmen and snipers (likely: seen from the Gunman) */
#define ObjBox ((void (*)(int *, void *))0x0800FE79)
int guard_msg(u8 *player, int msg, u8 *desc, int d) {
    if (msg == 0 && desc && (desc[0] == 0 || desc[0] == 2) && GUARD_AT && FRAMES - GUARD_AT <= PERFECT_FRAMES && IN_COMBAT) {
        u32 *blast = *(u32 **)(desc + 0x30);
        int box[4], *hr = (int *)(desc + 4);
        if (blast && (blast[0] == BLAST_VT || blast[0] == BULLET_VT) && (desc[0x14] ^ 1) == player[0x10]) {
            ObjBox(box, player);
            if (hr[0] < box[2] && box[0] < hr[2] && hr[1] < box[3] && box[1] < hr[3]) {
                u8 *b = (u8 *)blast;
                if (blast[0] == BLAST_VT) { b[0x58] = 1; *(void **)(b + 0x60) = player; }
                else {                                     /* a gunman's shot: turned round and away (direction +0x10, owner +0x1C, velocity +0x40). It can't hurt its
                                                              shooter: its update (0x08027562) builds every hit with team 0, the player's side */
                    b[0x10] ^= 1; b[0x11] = 1; *(void **)(b + 0x1C) = player;
                    *(int *)(b + 0x40) = -*(int *)(b + 0x40); *(int *)(b + 0x44) = -*(int *)(b + 0x44);
                }
                GUARD_AT = 0;
                PlaySound((void *)0x03003E5C, (u8 *)SOUND_HIT + 0x30 * 12, 0x40, 0);
                return blast[0] == BLAST_VT;           /* a shot told "nothing hit" flies on, the other way */
            }
        }
    }
    return ((int (*)(u8 *, int, u8 *, int))0x08010DDF)(player, msg, desc, d);
}

/* New Game+ (Nov 9). The dragon's wish to turn back time takes the party back to the start of the story with everything they have earned: levels, stats,
   skills and their mastery, equipment, the bag, Zenie, items, every post-game unlock (the mod's flags and the bench). What starts over:
   the story's flags 0-857 (its events and the rooms they open; 149 is the ending), the key items (25-82, the Dragon Balls among them),
   and the story's seven fighters' places in the party and their looks (from the start table, 0x086FDA4C: 18 bytes each, the form at
   +10); the opening (global script 38) joins Goku again and the story the rest, as before. Gogeta and the guest slot keep theirs: the
   post-game gave them. Broly's flag (111) stays with his guest outfit. Each time counts (more flags 47-48, up to 3): enemies hit harder
   by half for each (combat_hook). */
#define NG_FLAG 47
int ng_cycle(void) { return more_bits(NG_FLAG, 2); }
static void new_game_plus(void) {
    u8 *g = G_BYTES;
    const u8 *start = (const u8 *)0x086FDA4C;
    int i, c, broly = g[0x55 + 111 / 8] >> (111 % 8) & 1, k = ng_cycle();
    if (k < 3) more_bits_set(NG_FLAG, 2, k + 1);
    for (i = 0x55; i < 0xC0; i++) g[i] = 0;
    if (broly) g[0x55 + 111 / 8] |= 1 << (111 % 8);
    for (i = 25; i <= 82; i++) g[2 + i] = 0;
    for (c = 0; c < 7; c++) {
        u8 *r = RECORDS + c * RECORD_SIZE;
        r[0] = r[1] = r[2] = 0; *(u32 *)(r + 4) = 0;
        r[0x14] = start[18 * c + 10]; r[0x15] = 0;
        R16(r, 0x16) = R16(r, 0x18); R16(r, 0x1A) = R16(r, 0x1C);
    }
    g[0] = 0;
}
