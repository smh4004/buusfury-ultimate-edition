# Editable assets, WFZ compressor and the modern build (Phase 3)

```sh
make extract                       # baserom.gba -> assets/ (editable files; git-ignored, never commit them)
python3 tools/assets/demo_edits.py # optional: the three demo edits below
make modern                        # assets/ -> buusfury_modern.gba (unchanged assets keep their original bytes)
```
With no edits, `make modern` reproduces the original ROM byte for byte (SHA-1 checked).

## Asset kinds
| File | Source in ROM | Edit rules |
|---|---|---|
| `assets/text/dialogue.txt` | 7 WFZ text banks (table `gTextBankTable` 0x087B5B64), 2,294 lines reached from dialogue step records | Edit the line under its `@bank:offset:length` header. Shorter or equal text is written in place. Longer text goes to the end of bank 6 (nearly empty, about 32k characters free) and every reference to that line is repointed. Event lists can also add lines to new banks 7, 8, ... (`say 0x02 @7 "..."`; docs/modding.md). `{XX}` is a control character (`{08}` colour, `{0B}` page break) |
| `assets/text/ui_strings.txt` | 1,534 UTF-16 strings (`gUIStringPtrs` 0x0806BCE8) | Any length. A longer string moves to the appendix (see below) |
| `assets/palette/master.txt` | `gMasterPalette` 0x080701B0, 512 x 24-bit (0-255 BG, 256-511 OBJ) | Edit values in place |
| `assets/tables/exp.csv` | `gExpTable` 0x086B7084, 151 x u32 | Edit values. Keep 151 rows |
| `assets/scripts/*.evt`, `scripts/items/*.scr` | 533 event lists and 24 item effects (bytecode) | See `docs/modding.md` |
| `assets/maps/<map>/...` | All 427 map records: whole-layer CSVs, tile lists, collision masks | See `docs/modding.md` |
| `assets/gfx/tiles/*.png`, `gfx/sprites/*/*.png` | 187 BG tile pages, 7,240 sprite frames | Same size; palette-matched |
| `assets/tables/*.csv` | Area table, equipment, items, scouter | Same row count; pointer columns take labels |

Formats come from the earlier RE session's notes (RE_NOTES). Each was re-checked here by rendering or by running the result in the emulator.

## Demo (verified in mGBA, headless)
1. Dialogue: "Previously in DRAGON BALL Z: LEGACY OF GOKU **2**..." becomes "...LEGACY OF GOKU **4**, edited from the disassembly source...". The line is longer, so it went to bank 6 and its ref was repointed.
2. Palette: colour 119 (Snake Way road blue) becomes red.
3. Map tile: Snake Way BG1 chunk 0, entry (row 18, col 25) becomes a cloud tile (a yellow 8x8 tile appears on the road).

All three show up in game, and the long test route (intro, Snake Way, pause menu, 60 random walks) plays through.
`tools/assets/demo_edits.py` now also edits a script, a map layer, sprites and the tables. See `docs/modding.md`, which is the main modding guide.

## WFZ compressor (`tools/wfz/wfz_compress.py`)
* Inverse of the game's decoder (ported to `tools/wfz/wfz.py`, checked against the ARM routine `Wfz_Decompress` at 0x03000040).
  Uses literals, a 1-byte copy (offset 1-14 or a zero byte), short matches (offset 1-127, length 2-5),
  gamma matches with the decoder's length bonus, and repeat-offset matches. Every output is verified by decoding it before use.
* Size: 102.8% of the original compressor on 800 random blocks (all round-trip). **Stress test:** all 13,183 containers
  recompressed and rebuilt; the long route is pixel-identical to the original except the 2 title-menu checkpoints
  (stack-read quirk, see shifting.md).
* Stream setup: the decoder takes its initial literal width from the container *type* (r3) and its literal base from a
  caller register (r4, uninitialised), so a stream **must** start with the literal-mode switch (`001 0000 0 1`). Original
  streams and ours both do.

### Where stored (type 0) containers work
`Wfz_LoadContainer` (0x0803D940, 64 call sites) and `sub_0803D966` (1 site) read the type word: **type 0 = stored**
(memcpy), types 1 and 2 = compressed. These cover tile pages, chunks, text banks and most bitmaps.
Eight sites call the decompressor **directly** and need a compressed stream:
0x08004098 (script loader), 0x08009B12 (`Tiles_Animate1`, animated-tile frames `{u32 duration, raw stream}`),
0x08011FC6, 0x08011FD6, 0x08013E64, 0x08027FB8, 0x08028034, 0x08030AB0. The compressor always writes type 1, which works everywhere.

## How edited data gets into the ROM (`tools/assets/apply.py`)
`make modern` turns edited assets into *overrides* (byte range to new file) and rewrites the generated `data/*.s` into
`build_modern/src/`. The default mode preserves the layout, because the game has layout dependencies that aren't pointers:
* **Fits (same size or smaller):** written in place and zero-padded to the original size. Nothing moves.
* **Grows:** the original bytes stay put, and the new object goes to `rodata_appendix.s` at the end of .rodata under the same
  label, so every symbolic pointer follows it. The ROM may grow past 8 MB (fine for emulators and flash carts).
* **Pinned objects** (`config/pinned.txt`, 83 ranges) are reached by code as `symbol ± constant`. Example: the code loads
  the WFZ blob at 0x0807248C, then reads `blob - 0xC + 8` and 16 bytes at `blob + 0x38`. These must keep their size and position, so
  the build refuses to grow them. The list is generated by `tools/bfdis/pinned.py` from code patterns.
* `--shift` mode instead splices replacements in place and moves everything after them. It also passes the stress test,
  but the relocate mode is the safer default.

## Known limits / next steps
* Dialogue lines not reached from step records (about 4-22% of each bank: system messages, battle text) aren't listed yet.
  The next step is to find the other ref holders (battle and system text) by tracing `Text_LoadString` calls in the harness.
* Equipment, area table, sprites (frame records `[OAM attr][ptr][count][bbox][bbox]`), collision masks and tile pages
  (PNG import) aren't exported yet. The same override mechanism covers them: same-size tables in place, recompressed blobs relocated.
* `assets/` is derived from your ROM: keep it local, never commit or share it. Share `.bps` patches instead.
