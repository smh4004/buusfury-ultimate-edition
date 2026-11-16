/* Headless mGBA harness for smoke/shift tests.
 *
 * usage: harness rom.gba script.txt outdir
 * script commands (one per line, '#' comments):
 *   keys A,START,...   set held keys (empty = none)
 *   run N              run N frames with the held keys
 *   tap KEY [N]        hold KEY for 4 frames then release, wait N frames (default 30)
 *   shot NAME          write outdir/NAME.png and print a frame hash
 *   audio FILE         write the game's sound to FILE, 16-bit stereo 44100 Hz (`audio -` stops)
 *   hash               print frame hash only
 *   layer ID 0|1       hide or show a video layer (0-3 BG0-3, 4 sprites), for clean backdrops
 *   dump NAME ADDR LEN write raw bus memory to outdir/NAME.bin
 *   bp ADDR N          single-step up to N frames until PC == ADDR; print regs, stack and recent ROM jumps
 *   until LO HI N      single-step (max N frames) until LO <= PC < HI in a non-IRQ mode; print regs + stack
 *   mem ADDR N         print N words at ADDR (ADDR may be rK or rK+0xOFF, or [rK+0xOFF] for one dereference)
 *   watch ADDR N       single-step N frames; print PC/regs whenever the byte at ADDR changes
 *   hist N             single-step N frames and print the 16 most frequent PCs (find hangs)
 *   pc                 print the CPU PC
 *   syncpc ADDR        from now on, count run/tap time in passes of the game loop through ADDR, not video frames
 *                      (0 = video frames). Buu's Fury: 0x0803F42C, just after the VBlank wait in sub_0803F3F4
 *   capture LIST DIR N snapshot regs + RAM/IO/VRAM at the first N entries of each listed function (hex list)
 *   watchon ADDR       from now on, run/tap single-step and report every change of the word at ADDR
 *   guardon ROMEND     from now on, run/tap single-step and report the first PC outside valid memory
 *   guard N ROMEND     single-step up to N frames; stop and print the last 64 PCs when execution
 *                      leaves BIOS/EWRAM/IWRAM/ROM[0x08000000,ROMEND) (catches jumps through stale pointers)
 * Original code for the buusfury disassembly project.
 */
#include <mgba/flags.h>          /* first: core.h lays mCore out by these flags (USE_DEBUGGERS moves enableVideoLayer) */
#include <mgba/core/core.h>
#include <mgba/core/blip_buf.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <mgba/internal/arm/arm.h>
#include <mgba-util/vfs.h>
#include <png.h>
#include <zlib.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static unsigned W, H;
static color_t* vbuf;
static uint64_t frame_no;
static uint32_t guard_end;           /* "guardon ROMEND": check PC on every instruction during run/tap */
static int guard_hit;
static uint32_t gring[64]; static int gri;
static uint32_t watch_addr, watch_val; static int watch_on;
/* "capture LIST OUTDIR MAXHITS": snapshot full state at entry of listed functions (Thumb, ROM) */
static uint8_t* cap_bits; static uint16_t* cap_hits; static int cap_max; static char cap_dir[400]; static int cap_on;
static long cap_total;
static void snap(struct mCore* core, uint32_t pc) {
    struct ARMCore* cpu = core->cpu;
    uint32_t idx = (pc - 0x08000000) >> 1;
    char p[600]; snprintf(p, sizeof p, "%s/%08X_%d.snap", cap_dir, pc, cap_hits[idx]);
    FILE* f = fopen(p, "wb"); if (!f) return;
    uint32_t hdr[18]; for (int r = 0; r < 16; r++) hdr[r] = cpu->gprs[r];
    hdr[15] = pc;                                 /* entry address (gprs[15] runs one instruction ahead) */
    hdr[16] = cpu->cpsr.packed; hdr[17] = (uint32_t) frame_no;
    fwrite(hdr, 4, 18, f);
    static const uint32_t reg[][2] = {{0x02000000,0x40000},{0x03000000,0x8000},{0x04000000,0x400},{0x05000000,0x400},{0x06000000,0x18000},{0x07000000,0x400}};
    static uint8_t buf[0x40000], zb[0x50000];
    for (int k = 0; k < 6; k++) {
        for (uint32_t i = 0; i < reg[k][1]; i += 4) { uint32_t v = core->rawRead32(core, reg[k][0] + i, -1); memcpy(buf + i, &v, 4); }
        uLongf zl = sizeof zb; compress2(zb, &zl, buf, reg[k][1], 1);
        uint32_t h2[3] = {reg[k][0], reg[k][1], (uint32_t) zl}; fwrite(h2, 4, 3, f); fwrite(zb, 1, zl, f);
    }
    fclose(f); cap_hits[idx]++; cap_total++;
}   /* "watchon ADDR": report writes during run/tap */

static uint32_t sync_pc;              /* "syncpc ADDR": one `run` step = one pass of the game loop through ADDR */

static FILE* audio_f;
static void frame_inner(struct mCore* core);
/* `audio FILE`: from now on write the game's sound to FILE (16-bit stereo, 44100 Hz); `audio -` stops. */
static void frame(struct mCore* core) {
    frame_inner(core);
    if (!audio_f) return;
    blip_t* l = core->getAudioChannel(core, 0); blip_t* r = core->getAudioChannel(core, 1);
    static short buf[8192];
    int n;
    while ((n = blip_samples_avail(l)) > 0) {
        if (n > 4096) n = 4096;
        blip_read_samples(l, buf, n, 1); blip_read_samples(r, buf + 1, n, 1);
        fwrite(buf, 4, n, audio_f);
    }
}
static void frame_inner(struct mCore* core) {
    if (sync_pc) {
        /* Game-loop time instead of video time: step until the game passes its frame-sync point once (or at most
         * 8 video frames during loads). Lag frames then don't shift when inputs arrive, so builds that run at a
         * different speed (the C decomp build) can be compared with the original. */
        struct ARMCore* cpu = core->cpu;
        uint64_t f0 = core->frameCounter(core);
        int left = 0;
        for (;;) {
            core->step(core);
            uint32_t pc = cpu->gprs[15] - ((cpu->cpsr.packed & 0x20) ? 2 : 4);
            if (pc != sync_pc) left = 1;
            else if (left) break;
            if (core->frameCounter(core) - f0 >= 8) break;
        }
        return;
    }
    if ((!guard_end || guard_hit) && !watch_on && !cap_on) { core->runFrame(core); return; }
    struct ARMCore* cpu = core->cpu;
    uint64_t fc = core->frameCounter(core);
    while (core->frameCounter(core) == fc) {
        core->step(core);
        uint32_t pc = cpu->gprs[15];
        gring[gri++ & 63] = pc;
        /* mGBA keeps gprs[15] one Thumb instruction ahead (pipeline): the next instruction is at pc - 2 */
        if (cap_on && pc >= 0x08000002 && pc < 0x08100002 && (cpu->cpsr.packed & 0x20)) {
            uint32_t idx = (pc - 2 - 0x08000000) >> 1;
            if ((cap_bits[idx >> 3] >> (idx & 7) & 1) && cap_hits[idx] < cap_max) snap(core, pc - 2);
        }
        if (watch_on) {
            uint32_t v = core->busRead32(core, watch_addr);
            if (v != watch_val) {
                printf("watchon %08x: %08x -> %08x at frame %llu pc %08x lr %08x r0-r3 %08x %08x %08x %08x\n", watch_addr, watch_val, v,
                       (unsigned long long) frame_no, pc, cpu->gprs[14], cpu->gprs[0], cpu->gprs[1], cpu->gprs[2], cpu->gprs[3]);
                watch_val = v;
            }
        }
        if (!guard_end || guard_hit) continue;
        int ok = pc < 0x4000 || (pc >= 0x02000000 && pc < 0x02040000) ||
                 (pc >= 0x03000000 && pc < 0x03008000) || (pc >= 0x08000000 && pc < guard_end);
        if (!ok) {
            guard_hit = 1;
            printf("guardon: bad pc %08x at frame %llu; previous pcs:", pc, (unsigned long long) frame_no);
            for (int k = 0; k < 64; k++) printf(" %08x", gring[(gri + k) & 63]);
            printf("\n  regs:"); for (int r = 0; r < 16; r++) printf(" %08x", cpu->gprs[r]); printf("\n");
            return;
        }
    }
}

static void quiet_log(struct mLogger* l, int cat, enum mLogLevel lvl, const char* fmt, va_list a) {
    (void) l; (void) cat; (void) lvl; (void) fmt; (void) a;
}
static struct mLogger logger = { .log = quiet_log };

static const char* KEYN[] = { "A", "B", "SELECT", "START", "RIGHT", "LEFT", "UP", "DOWN", "R", "L" };
static uint32_t parse_keys(const char* s) {
    uint32_t k = 0;
    char buf[256]; strncpy(buf, s, 255); buf[255] = 0;
    for (char* t = strtok(buf, ", \t\n"); t; t = strtok(NULL, ", \t\n"))
        for (int i = 0; i < 10; i++) if (!strcmp(t, KEYN[i])) k |= 1u << i;
    return k;
}

static uint64_t fhash(void) {
    uint64_t h = 1469598103934665603ull;
    for (unsigned y = 0; y < H; y++)
        for (unsigned x = 0; x < W; x++) { h ^= (uint32_t) vbuf[y * 256 + x] & 0xFFFFFF; h *= 1099511628211ull; }
    return h;
}

static void shot(const char* path) {
    FILE* f = fopen(path, "wb");
    if (!f) return;
    png_structp p = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
    png_infop info = png_create_info_struct(p);
    png_init_io(p, f);
    png_set_IHDR(p, info, W, H, 8, PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_write_info(p, info);
    unsigned char* row = malloc(W * 3);
    for (unsigned y = 0; y < H; y++) {
        for (unsigned x = 0; x < W; x++) {
            uint32_t c = vbuf[y * 256 + x];
            row[x * 3] = c & 0xFF; row[x * 3 + 1] = (c >> 8) & 0xFF; row[x * 3 + 2] = (c >> 16) & 0xFF;
        }
        png_write_row(p, row);
    }
    png_write_end(p, NULL);
    png_destroy_write_struct(&p, &info);
    free(row); fclose(f);
}

int main(int argc, char** argv) {
    if (argc < 4) { fprintf(stderr, "usage: %s rom script outdir\n", argv[0]); return 1; }
    setvbuf(stdout, NULL, _IOLBF, 0);   /* a script on a pipe can read each answer before sending the next line */
    mLogSetDefaultLogger(&logger);
    struct mCore* core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) { fprintf(stderr, "core init failed\n"); return 1; }
    mCoreInitConfig(core, NULL);
    core->desiredVideoDimensions(core, &W, &H);
    vbuf = calloc(256 * 256, sizeof(color_t));
    core->setVideoBuffer(core, vbuf, 256);
    if (!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "load failed\n"); return 1; }
    { const char* sav = getenv("HARNESS_SAV"); if (sav) core->loadSave(core, VFileOpen(sav, O_CREAT | O_RDWR)); }
    core->reset(core);
    FILE* sc = fopen(argv[2], "r");
    if (!sc) { perror("script"); return 1; }
    char line[512];
    uint32_t keys = 0;
    while (fgets(line, sizeof line, sc)) {
        char* c = strchr(line, '#'); if (c) *c = 0;
        char cmd[64] = "", a1[256] = "", a2[64] = "", a3[64] = "";
        if (sscanf(line, "%63s %255s %63s %63s", cmd, a1, a2, a3) < 1) continue;
        if (!strcmp(cmd, "keys")) { keys = parse_keys(a1); core->setKeys(core, keys); }
        else if (!strcmp(cmd, "run")) { int n = atoi(a1); for (int i = 0; i < n; i++) { frame(core); frame_no++; } }
        else if (!strcmp(cmd, "audio")) {
            if (audio_f) { fclose(audio_f); audio_f = 0; }
            if (strcmp(a1, "-")) {
                core->setAudioBufferSize(core, 4096);
                blip_set_rates(core->getAudioChannel(core, 0), core->frequency(core), 44100);
                blip_set_rates(core->getAudioChannel(core, 1), core->frequency(core), 44100);
                audio_f = fopen(a1, "wb");
            }
        }
        else if (!strcmp(cmd, "guardon")) { guard_end = strtoul(a1, 0, 16); }
        else if (!strcmp(cmd, "syncpc")) { sync_pc = strtoul(a1, 0, 16); }
        else if (!strcmp(cmd, "capture")) {
            cap_bits = calloc(0x80000 / 8, 1); cap_hits = calloc(0x80000, 2);
            FILE* lf = fopen(a1, "r"); char ln[64];
            while (lf && fgets(ln, sizeof ln, lf)) { uint32_t ad = strtoul(ln, 0, 16); if (ad >= 0x08000000 && ad < 0x08100000) { uint32_t i = (ad - 0x08000000) >> 1; cap_bits[i >> 3] |= 1 << (i & 7); } }
            if (lf) fclose(lf);
            strncpy(cap_dir, a2, sizeof cap_dir - 1); cap_max = atoi(a3); cap_on = 1;
        }
        else if (!strcmp(cmd, "capstat")) printf("captured %ld snapshots\n", cap_total);
        else if (!strcmp(cmd, "watchon")) { watch_addr = strtoul(a1, 0, 16); watch_val = core->busRead32(core, watch_addr); watch_on = 1; }
        else if (!strcmp(cmd, "tap")) {
            int n = a2[0] ? atoi(a2) : 30;
            core->setKeys(core, keys | parse_keys(a1));
            for (int i = 0; i < 4; i++) { frame(core); frame_no++; }
            core->setKeys(core, keys);
            for (int i = 0; i < n; i++) { frame(core); frame_no++; }
        }
        else if (!strcmp(cmd, "shot")) {
            char p[600]; snprintf(p, sizeof p, "%s/%s.png", argv[3], a1); shot(p);
            printf("shot %s frame %llu hash %016llx\n", a1, (unsigned long long) frame_no, (unsigned long long) fhash());
        }
        else if (!strcmp(cmd, "hash")) printf("hash frame %llu %016llx\n", (unsigned long long) frame_no, (unsigned long long) fhash());
        else if (!strcmp(cmd, "pc")) {
            struct ARMCore* cpu = core->cpu;
            printf("pc %08x frame %llu video %llu\n", (unsigned) cpu->gprs[15], (unsigned long long) frame_no, (unsigned long long) core->frameCounter(core));
        }
        else if (!strcmp(cmd, "guard")) {
            int n = atoi(a1); uint32_t romend = strtoul(a2, 0, 16);
            struct ARMCore* cpu = core->cpu;
            uint32_t ring[64]; int ri = 0; int bad = 0;
            uint32_t romring[32]; int rr = 0; uint32_t lastrom = 0;
            for (int f = 0; f < n && !bad; f++) {
                uint64_t fc = core->frameCounter(core);
                while (core->frameCounter(core) == fc) {
                    core->step(core);
                    uint32_t pc = cpu->gprs[15];
                    ring[ri++ & 63] = pc;
                    if (pc >= 0x08000000 && (pc < lastrom || pc > lastrom + 8)) romring[rr++ & 31] = pc;
                    if (pc >= 0x08000000) lastrom = pc;
                    int ok = pc < 0x4000 || (pc >= 0x02000000 && pc < 0x02040000) ||
                             (pc >= 0x03000000 && pc < 0x03008000) || (pc >= 0x08000000 && pc < romend);
                    if (!ok) { bad = 1; break; }
                }
                frame_no++;
            }
            if (bad) {
                printf("guard: bad pc at frame %llu; last pcs:\n", (unsigned long long) frame_no);
                for (int k = 0; k < 64; k++) printf("  %08x\n", ring[(ri + k) & 63]);
                printf("  last ROM jumps:");
                for (int k = 0; k < 32; k++) printf(" %08x", romring[(rr + k) & 31]);
                printf("\n");
                printf("  r0-r3 %08x %08x %08x %08x lr %08x\n", cpu->gprs[0], cpu->gprs[1], cpu->gprs[2], cpu->gprs[3], cpu->gprs[14]);
            } else printf("guard: ok through frame %llu\n", (unsigned long long) frame_no);
        }
        else if (!strcmp(cmd, "bp")) {
            uint32_t want = strtoul(a1, 0, 16); int n = atoi(a2);
            struct ARMCore* cpu = core->cpu;
            uint32_t romring[16]; int rr = 0; uint32_t lastrom = 0; int hit = 0;
            for (int f = 0; f < n && !hit; f++) {
                uint64_t fc = core->frameCounter(core);
                while (core->frameCounter(core) == fc) {
                    core->step(core);
                    uint32_t pc = cpu->gprs[15];
                    if (pc >= 0x08000000 && (pc < lastrom || pc > lastrom + 8)) romring[rr++ & 15] = pc;
                    if (pc >= 0x08000000) lastrom = pc;
                    if ((pc & ~1u) == want || (pc - 8) == want || (pc - 4) == want) { hit = 1; break; }
                }
                if (!hit) frame_no++;
            }
            printf("bp %08x %s at frame %llu\n", want, hit ? "hit" : "not hit", (unsigned long long) frame_no);
            if (hit) {
                printf("  regs:"); for (int r = 0; r < 16; r++) printf(" %08x", cpu->gprs[r]);
                printf("\n  rom:"); for (int k = 0; k < 16; k++) printf(" %08x", romring[(rr + k) & 15]);
                printf("\n");
            }
        }
        else if (!strcmp(cmd, "until")) {
            uint32_t lo_ = strtoul(a1, 0, 16), hi_ = strtoul(a2, 0, 16); int n = atoi(a3);
            struct ARMCore* cpu = core->cpu; int hit = 0;
            for (int f = 0; f < n && !hit; f++) {
                uint64_t fc = core->frameCounter(core);
                while (core->frameCounter(core) == fc) {
                    core->step(core);
                    uint32_t pc = cpu->gprs[15];
                    if (pc >= lo_ && pc < hi_ && (cpu->cpsr.packed & 0x1F) != 0x12) { hit = 1; break; }
                }
                if (!hit) frame_no++;
            }
            printf("until %s frame %llu\n  regs:", hit ? "hit" : "miss", (unsigned long long) frame_no);
            for (int r = 0; r < 16; r++) printf(" %08x", cpu->gprs[r]);
            printf("\n  stack:");
            for (int k = 0; k < 40; k++) printf(" %08x", core->busRead32(core, cpu->gprs[13] + 4 * k));
            printf("\n");
        }
        else if (!strcmp(cmd, "mem")) {
            struct ARMCore* cpu = core->cpu;
            char* e = a1; int deref = 0; uint32_t ad;
            if (*e == '[') { deref = 1; e++; }
            if (*e == 'r') { int r = strtol(e + 1, &e, 10); ad = cpu->gprs[r]; if (*e == '+') ad += strtoul(e + 1, &e, 16); }
            else ad = strtoul(e, &e, 16);
            if (deref) ad = core->busRead32(core, ad);
            int n = a2[0] ? atoi(a2) : 4;
            printf("mem %08x:", ad);
            for (int k = 0; k < n; k++) printf(" %08x", core->busRead32(core, ad + 4 * k));
            printf("\n");
        }
        else if (!strcmp(cmd, "watch")) {
            uint32_t ad = strtoul(a1, 0, 16); int n = atoi(a2);
            struct ARMCore* cpu = core->cpu;
            uint8_t last = core->busRead8(core, ad);
            for (int f = 0; f < n; f++) {
                uint64_t fc = core->frameCounter(core);
                while (core->frameCounter(core) == fc) {
                    core->step(core);
                    uint8_t v = core->busRead8(core, ad);
                    if (v != last) {
                        printf("watch %08x: %02x -> %02x at frame %llu pc %08x lr %08x r0-r7", ad, last, v,
                               (unsigned long long) frame_no, cpu->gprs[15], cpu->gprs[14]);
                        for (int r = 0; r < 8; r++) printf(" %08x", cpu->gprs[r]);
                        printf("\n");
                        last = v;
                    }
                }
                frame_no++;
            }
        }
        else if (!strcmp(cmd, "hist")) {
            int n = atoi(a1);
            struct ARMCore* cpu = core->cpu;
            enum { HN = 1 << 16 };
            static uint32_t hk[HN], hv[HN];
            memset(hk, 0, sizeof hk); memset(hv, 0, sizeof hv);
            for (int f = 0; f < n; f++) {
                uint64_t fc = core->frameCounter(core);
                while (core->frameCounter(core) == fc) {
                    core->step(core);
                    uint32_t pc = cpu->gprs[15], h = (pc * 2654435761u) >> 16;
                    while (hk[h] && hk[h] != pc) h = (h + 1) & (HN - 1);
                    hk[h] = pc; hv[h]++;
                }
                frame_no++;
            }
            for (int k = 0; k < 16; k++) {
                int best = -1;
                for (int i = 0; i < HN; i++) if (hv[i] && (best < 0 || hv[i] > hv[best])) best = i;
                if (best < 0) break;
                printf("  %08x %u\n", hk[best], hv[best]); hv[best] = 0;
            }
            printf("  regs:"); for (int r = 0; r < 16; r++) printf(" %08x", cpu->gprs[r]); printf("\n  stack:");
            for (int k = 0; k < 24; k++) printf(" %08x", core->busRead32(core, cpu->gprs[13] + 4 * k));
            printf("\n");
        }
        else if (!strcmp(cmd, "poke")) { core->busWrite32(core, strtoul(a1, 0, 16), strtoul(a2, 0, 16)); }
        else if (!strcmp(cmd, "poke8")) { core->busWrite8(core, strtoul(a1, 0, 16), strtoul(a2, 0, 16)); }
        else if (!strcmp(cmd, "layer")) { core->enableVideoLayer(core, atoi(a1), atoi(a2) != 0); }   /* layer ID 0|1: 0-3 BG0-3, 4 OBJ (mGBA ids) */
        else if (!strcmp(cmd, "reset")) { core->reset(core); }
        else if (!strcmp(cmd, "dump")) {
            char p[600]; snprintf(p, sizeof p, "%s/%s.bin", argv[3], a1);
            uint32_t ad = strtoul(a2, 0, 16), n = strtoul(a3, 0, 16);
            FILE* f = fopen(p, "wb");
            for (uint32_t i = 0; i < n; i++) fputc(core->busRead8(core, ad + i), f);
            fclose(f);
        }
        fflush(stdout);
    }
    core->deinit(core);
    return 0;
}
