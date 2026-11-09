#!/usr/bin/env python3
"""Editable assets for the Buu's Fury disassembly.

  assets.py extract     baserom.gba -> assets/ (editable files + assets/manifest.json)
  assets.py build       assets/ -> build_modern/overrides.json + replacement blobs (only edited assets)

Asset kinds (all pulled from the user's baserom.gba; nothing copyrighted is committed):
  palette   assets/palette/master.txt        512 lines "R G B" (24-bit master palette at 0x080701B0, in place)
  exp       assets/tables/exp.csv            151 x u32 EXP table at 0x086B7084 (in place)
  dialogue  assets/text/dialogue.txt         dialogue lines reached from step records {u16 id, u8 5, u8 speaker, u32 ref}
                                             ref = bank | char_off << 6 | length << 21 (7 WFZ banks, table 0x087B5B64)
                                             Shorter/equal edits are written in place; longer ones go to the end of bank 6
                                             (nearly empty) and every ref to that line is re-pointed.
  ui        assets/text/ui_strings.txt       1534 UTF-16 strings from gUIStringPtrs (0x0806BCE8); any length (data moves)
  maps      assets/maps/<map>/...            all 427 maps: whole-layer CSVs, tile lists, collision masks (mapassets.py)
  tiles     assets/gfx/tiles/page_NNN.png    the 187 global BG tile pages as indexed PNGs (gfx.py)
  sprites   assets/gfx/sprites/<anim>/*.png  sprite frames (single-piece, 256-colour; sprites.py)
  tables    assets/tables/{areas,equipment,items,enemies,spawns,scouter}.csv  game tables (tables.py)
  actors    assets/areas/*.actors            each area's actor list: add/remove enemies and other actors (actors.py)
  script    assets/scripts/items/*.scr       item effect bytecode; scripts/enemies/*.scr enemy death scripts (drops)
  (`extract --previews` also renders every map layer to PNG; slow)
  events    assets/scripts/<label>.evt       every event list (cutscenes, NPC talks, shops...): steps with script
                                             bytecode as text (tools/scripts/events.py, bfscript.py). Steps can be edited,
                                             added and removed; new dialogue can be written inline as "text".
Overrides are applied to the generated data/*.s by tools/assets/apply.py (make modern).
"""
import sys, os, json, struct, hashlib, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'wfz'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
from wfz import unpack
from wfz_compress import compress
import maps as mapsmod
import mapassets
import sprites
import tables
import actors
import events as evmod
import bfscript

ROM = 0x08000000
BANK_TABLE = 0x7B5B64
NBANKS = 7
OVERFLOW_BANK = 6
PALETTE = 0x701B0
EXP = (0x6B7084, 151)
UI_PTRS = (0x6BCE8, 1534)



def sha(path): return hashlib.sha1(open(path, 'rb').read()).hexdigest()
def u32(d, o): return struct.unpack_from('<I', d, o)[0]


# ------------------------------------------------------------------ text escaping
def esc(s):
    out = []
    for ch in s:
        c = ord(ch)
        if ch == '{': out.append('{{')
        elif c < 0x20 or c in (0x7F,): out.append('{%02X}' % c)
        else: out.append(ch)
    return ''.join(out)


def unesc(s):
    return re.sub(r'\{\{|\{([0-9A-Fa-f]{2})\}', lambda m: '{' if m.group(0) == '{{' else chr(int(m.group(1), 16)), s)


def wfz_blocks():
    path = '.analysis/wfz_blocks.json'
    if not os.path.exists(path):
        import subprocess
        os.makedirs('.analysis', exist_ok=True)
        subprocess.check_call([sys.executable, os.path.join(HERE, '..', 'wfz', 'scan_wfz.py'), 'baserom.gba', path, '54FBC', '7B79A4'])
    return json.load(open(path))


def wfz_ranges(d):
    blocks = wfz_blocks()
    return {o: e for o, s, e, t in blocks}


def banks(d):
    offs = [u32(d, BANK_TABLE + 4 * i) - ROM for i in range(NBANKS)]
    return offs, [unpack(d, o)[0].decode('utf-16-le') for o in offs]


def find_textrefs(d, texts):
    """Validated dialogue refs: step records with a neighbouring record id +-1."""
    blocks = wfz_blocks()
    inwfz = bytearray(len(d))
    for o, s, e, t in blocks: inwfz[o:e] = b'\x01' * (e - o)
    refs = {}
    for o in range(0x54FBC, 0x7B79A4 - 8):
        if inwfz[o] or d[o + 2] != 5: continue
        sid = struct.unpack_from('<H', d, o)[0]
        if sid > 0x400: continue
        w = u32(d, o + 4); b, off, ln = w & 0x3F, (w >> 6) & 0x7FFF, w >> 21
        if not (b < NBANKS and ln > 0 and off + ln <= len(texts[b])): continue
        nid, nt = struct.unpack_from('<H', d, o + 8)[0], d[o + 10]
        pid, pt = struct.unpack_from('<H', d, o - 8)[0], d[o - 6]
        if (nid == sid + 1 and nt < 10) or (pid == sid - 1 and pt == 5):
            refs.setdefault((b, off, ln), []).append(o + 4)
    return refs


# ------------------------------------------------------------------ extract
def extract(rom, out):
    d = open(rom, 'rb').read()
    man = {'assets': {}}
    os.makedirs(out, exist_ok=True)

    def reg(name, path, **kw):
        kw['file'] = os.path.relpath(path, out); kw['sha1'] = sha(path)
        man['assets'][name] = kw

    # palette
    p = os.path.join(out, 'palette', 'master.txt'); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write('# Master palette (24-bit RGB). Lines 0-255 BG, 256-511 OBJ. Edit values 0-255.\n')
        for i in range(512):
            r, g, b = d[PALETTE + 3 * i:PALETTE + 3 * i + 3]
            f.write('%3d %3d %3d  # %d\n' % (r, g, b, i))
    reg('palette', p, kind='palette', start=PALETTE, length=512 * 3)

    # EXP table
    p = os.path.join(out, 'tables', 'exp.csv'); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write('index,exp\n')
        for i in range(EXP[1]): f.write('%d,%d\n' % (i, u32(d, EXP[0] + 4 * i)))
    reg('exp', p, kind='exp', start=EXP[0], length=EXP[1] * 4)

    # dialogue
    boffs, texts = banks(d)
    refs = find_textrefs(d, texts)
    p = os.path.join(out, 'text', 'dialogue.txt'); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write('# Dialogue lines. Edit the text line under each "@bank:offset:length" header; keep the header.\n')
        f.write('# {XX} = control character (08 color, 0B page break), {{ = literal brace.\n')
        for (b, off, ln) in sorted(refs):
            f.write('@%d:%d:%d\n%s\n' % (b, off, ln, esc(texts[b][off:off + ln])))
    reg('dialogue', p, kind='dialogue', banks=boffs, refs={'%d:%d:%d' % k: v for k, v in refs.items()})

    # UI strings (u16 strings terminated by 0)
    p = os.path.join(out, 'text', 'ui_strings.txt')
    ptrs = [u32(d, UI_PTRS[0] + 4 * i) - ROM for i in range(UI_PTRS[1])]
    spans = []
    with open(p, 'w', encoding='utf-8') as f:
        f.write('# UI strings: "index<TAB>text". Any length; strings shared by several indexes are listed once.\n')
        seen = set()
        for i, o in enumerate(ptrs):
            e = o
            while struct.unpack_from('<H', d, e)[0] != 0: e += 2
            if o in seen: continue
            seen.add(o); spans.append((i, o, e + 2))
            f.write('%d\t%s\n' % (i, esc(d[o:e].decode('utf-16-le'))))
    reg('ui', p, kind='ui', spans=spans)

    # event lists / scripts
    btexts = [unpack(d, o)[0].decode('utf-16-le') for o in boffs]
    lists = evmod.find_lists(d, btexts)
    owner = {}
    for o, it, term in lists:
        for t in it: owner.setdefault(t, o)
    names = bfscript.load_names()
    sd = os.path.join(out, 'scripts'); os.makedirs(sd, exist_ok=True)
    for o, it, term in lists:
        lab = evmod.L.name_at(o)
        p = os.path.join(sd, '%s.evt' % lab)
        open(p, 'w', encoding='utf-8').write(evmod.export_list(d, o, it, term, btexts, names, owner))
        reg('events:%s' % lab, p, kind='events', start=o, items=it, term=term)
    # speaker ids are not named in the ROM: list a few lines per speaker so they can be identified
    spk = {}
    for o, it, term in lists:
        for t in it:
            if d[t + 2] in (5, 6):
                ref = u32(d, t + 4); b, off, ln = ref & 0x3F, (ref >> 6) & 0x7FFF, ref >> 21
                spk.setdefault(d[t + 3], []).append(btexts[b][off:off + ln].replace('\n', ' '))
    with open(os.path.join(sd, 'SPEAKERS.txt'), 'w', encoding='utf-8') as f:
        f.write('# Speaker ids used by `step N say SPEAKER ...` (the id picks the name and portrait), with sample lines.\n')
        for k in sorted(spk):
            f.write('0x%02X  (%d lines)\n' % (k, len(spk[k])))
            for l in spk[k][:3]: f.write('      %s\n' % re.sub(r'[\x00-\x1f]', '', l)[:90])

    # tile pages, all maps (layers, tile lists, collision masks)
    wfzidx = {o: (o, sz, e, t) for o, sz, e, t in wfz_blocks()}
    mapassets.extract(d, out, reg, wfzidx, previews='--previews' in sys.argv)
    sprites.extract(d, out, reg, wfzidx)

    # game tables and item effect scripts
    td = os.path.join(out, 'tables'); os.makedirs(td, exist_ok=True)
    for tn in tables.SPECS:
        p = os.path.join(td, '%s.csv' % tn); tables.export(d, tn, p)
        reg('table:%s' % tn, p, kind='table', table=tn)
    idir = os.path.join(out, 'scripts', 'items'); os.makedirs(idir, exist_ok=True)
    for i, st, nm in tables.effect_scripts(d):
        p = os.path.join(idir, '%02d_%s.scr' % (i, re.sub(r'\W+', '_', nm).strip('_')))
        e = tables.export_script(d, st, p, 'Item %d effect: %s' % (i, nm), names)
        reg('script:item%d' % i, p, kind='script', start=st, end=e)
    actors.extract(d, out, reg)
    edir = os.path.join(out, 'scripts', 'enemies'); os.makedirs(edir, exist_ok=True)
    for i, st, nm in tables.death_scripts(d):
        p = os.path.join(edir, '%03d_%s.scr' % (i, re.sub(r'\W+', '_', nm).strip('_')[:40]))
        e = tables.export_script(d, st, p, 'Enemy %d death script (item drops): %s' % (i, nm), names)
        reg('script:enemy%d' % i, p, kind='script', start=st, end=e)

    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    print('extracted %d assets to %s' % (len(man['assets']), out))


# ------------------------------------------------------------------ build
def build(rom, src, out):
    d = open(rom, 'rb').read()
    man = json.load(open(os.path.join(src, 'manifest.json')))
    wfz = wfz_ranges(d)
    os.makedirs(out, exist_ok=True)
    ov = []          # {start, end, file}
    changed = []

    def put(start, end, data, tag):
        fn = os.path.join(out, 'ov_%06X_%s.bin' % (start, tag))
        open(fn, 'wb').write(data)
        ov.append({'start': start, 'end': end, 'file': fn})

    text = {'banks': None, 'offs': None, 'touched': set(), 'extra': {}}

    def banks_loaded():
        if text['banks'] is None:
            a = man['assets']['dialogue']
            text['offs'] = a['banks']
            text['banks'] = [list(unpack(d, o)[0].decode('utf-16-le')) for o in a['banks']]
        return text['banks']

    def new_text(s, bank=OVERFLOW_BANK):
        """Append a new dialogue line to the overflow bank (or to an added bank, 7 and up); return its packed text
        ref. The game unpacks a line's whole bank each time it shows the line (Text_LoadString2), so every line
        added to bank 6 makes all bank-6 lines a little slower; new quests keep their lines in banks of their own."""
        if bank >= NBANKS:
            bt = text['extra'].setdefault(bank, [])
        else:
            assert bank == OVERFLOW_BANK, 'new lines go to the overflow bank or an added bank'
            bt = banks_loaded()[OVERFLOW_BANK]
            text['touched'].add(OVERFLOW_BANK)
        off = len(bt); bt.extend(s)
        assert len(bt) < 0x7FFF and len(s) < 0x800, 'bank %d full or line too long' % bank
        return bank | off << 6 | len(s) << 21

    names = bfscript.load_names()
    mctx = mapassets.Ctx(d, {o: (o, sz, e, t) for o, sz, e, t in wfz_blocks()}, out, ov)
    for name, a in man['assets'].items():
        path = os.path.join(src, a['file'])
        if sha(path) == a['sha1']: continue
        changed.append(name)
        k = a['kind']
        if k == 'palette':
            vals = [l.split('#')[0].split() for l in open(path) if l.split('#')[0].strip()]
            data = bytes(int(x) & 0xFF for v in vals[:512] for x in v[:3])
            assert len(data) == 1536, 'palette needs 512 lines'
            put(a['start'], a['start'] + a['length'], data, 'palette')
        elif k == 'exp':
            rows = [l.strip().split(',') for l in open(path)][1:]
            data = b''.join(struct.pack('<I', int(r[1])) for r in rows if len(r) > 1)
            assert len(data) == a['length'], 'exp.csv must keep 151 rows'
            put(a['start'], a['start'] + a['length'], data, 'exp')
        elif k in ('tilepage', 'layer', 'tilelist', 'mask'):
            mapassets.build(d, a, path, mctx)
        elif k == 'sprite':
            sprites.build(d, a, path, mctx)
        elif k == 'table':
            tables.build(d, a['table'], path, mctx)
        elif k == 'actors':
            actors.build(d, a, path, mctx)
        elif k == 'script':
            tables.build_script(d, a, path, mctx, names)
        elif k == 'ui':
            lines = {}
            for l in open(path, encoding='utf-8'):
                if l.startswith('#') or '\t' not in l: continue
                i, t = l.rstrip('\n').split('\t', 1); lines[int(i)] = unesc(t)
            for i, o, e in a['spans']:
                new = lines[i].encode('utf-16-le') + b'\0\0'
                if new != d[o:e]: put(o, e, new, 'ui%d' % i)
        elif k == 'events':
            ov += evmod.compile_list(d, a['start'], a['items'], a['term'], open(path, encoding='utf-8').read(),
                                     names, new_text, out, 'ev')
        elif k == 'dialogue':
            bank_texts = banks_loaded()
            orig = {}
            cur = None
            for l in open(path, encoding='utf-8'):
                l = l.rstrip('\n')
                if cur is None:
                    m = re.match(r'^@(\d+):(\d+):(\d+)$', l)
                    if m: cur = tuple(int(x) for x in m.groups())
                    continue
                orig[cur] = unesc(l); cur = None
            for key, txt in orig.items():
                b, off, ln = key
                if ''.join(bank_texts[b][off:off + ln]) == txt: continue
                if len(txt) <= ln:
                    bank_texts[b][off:off + len(txt)] = list(txt); nb, noff = b, off
                else:
                    nb, noff = OVERFLOW_BANK, len(bank_texts[OVERFLOW_BANK])
                    bank_texts[nb].extend(txt)
                    assert len(bank_texts[nb]) < 0x7FFF, 'overflow bank full'
                text['touched'].add(nb)
                ref = nb | (noff << 6) | (len(txt) << 21)
                for site in a['refs']['%d:%d:%d' % key]:
                    put(site, site + 4, struct.pack('<I', ref), 'ref')
    for b in sorted(text['touched']):
        raw = ''.join(text['banks'][b]).encode('utf-16-le')
        o = text['offs'][b]
        put(o, wfz[o], compress(raw), 'bank%d' % b)
    if text['extra']:
        # added banks: new objects in the appendix, and the bank table (gTextBankTable, read only by
        # Text_LoadString2 through its literal at 0x123CC) grown by their entries, so it moves to the appendix too
        top = max(text['extra'])
        assert sorted(text['extra']) == list(range(NBANKS, top + 1)), 'added banks must be numbered 7, 8, ... in order'
        tab = ['\t.4byte gUnknown_08%06X' % (u32(d, BANK_TABLE + 4 * i) - ROM) for i in range(NBANKS)]
        for b in range(NBANKS, top + 1):
            fn = os.path.join(out, 'new_bank%d.bin' % b)
            open(fn, 'wb').write(compress(''.join(text['extra'][b]).encode('utf-16-le')))
            ov.append({'new': 'gTextBank%d' % b, 'file': fn})
            tab.append('\t.4byte gTextBank%d' % b)
        fn = os.path.join(out, 'ov_%06X_banktable.s' % BANK_TABLE)
        open(fn, 'w').write('\n'.join(tab) + '\n')
        ov.append({'start': BANK_TABLE, 'end': BANK_TABLE + 4 * NBANKS, 'file': fn, 'size': 4 * (top + 1)})
    json.dump(ov, open(os.path.join(out, 'overrides.json'), 'w'), indent=1)
    print('changed assets: %s' % (', '.join(changed) or 'none'))
    print('%d overrides -> %s' % (len(ov), os.path.join(out, 'overrides.json')))


if __name__ == '__main__':
    os.chdir(os.path.join(HERE, '..', '..'))
    if len(sys.argv) < 2 or sys.argv[1] not in ('extract', 'build'):
        sys.exit(__doc__)
    if sys.argv[1] == 'extract': extract('baserom.gba', 'assets')
    else: build('baserom.gba', 'assets', 'build_modern/overrides')
