#!/usr/bin/env python3
"""Event lists ("cutscenes", NPC talks, triggers) <-> editable .evt text files.

An event list is an array of u32 pointers to steps, normally 0-terminated (a few aren't; their length can't change).
The game's global script table (gUnknown_0879B704, 522 entries) points at most of them; the rest are found by
scanning .rodata. A step is [u16 id][u8 type][...]; ids are usually 1, 2, 3... but some lists use other numbers
(the id is what dialogue choices and jumps refer to), so the text keeps them:
  type 0  code         bytecode (bfscript) until `end`
  type 3  text         [u8 pad] + UTF-16 text up to a 0 character (shop menus and similar)
  type 4  zcode        [u8 pad] + WFZ bitstream of bytecode (decompressed into a 2 KB buffer by sub_08004098)
  type 5  say          [u8 speaker][u32 text ref]   (text ref = bank | offset << 6 | length << 21)
  type 6  say+code     [u8 speaker][u32 text ref] + bytecode
  other   raw          kept as bytes
Lists are found by scanning .rodata for pointer arrays whose targets carry ids 1, 2, 3... and decode cleanly.

.evt syntax:
  step ID code            ; followed by indented bytecode lines (see bfscript.py)
  step ID zcode           ; same, stored compressed
  step ID say SPEAKER @bank:off:len        or   step ID say SPEAKER "new text"
  step ID saycode SPEAKER @bank:off:len    then indented bytecode
  step ID text "UTF-16 text"
  step ID raw TYPE hexbytes                (bytes after the 3-byte header)
  step ref LABEL                           reuse an existing step object unchanged
Steps can be added, removed and reordered in 0-terminated lists. In lists numbered 1, 2, 3... (almost all) the build
renumbers steps by position, because the game finds the next step by id; there the written id only says which original
step a line is, and new steps can use `auto`. Lists with other ids (dialogue trees) keep the ids exactly as written.
"""
import os, sys, struct, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'wfz'), os.path.join(HERE, '..', 'assets')]
import bfscript as B
import wfz
from wfz_compress import compress_stream
import labels as L

ROM = 0x08000000
RODATA = (0x54FBC, 0x7B79A4)
ZBUF = 0x800                   # type-4 steps are decompressed into a 2 KB heap block


def u32(d, o): return struct.unpack_from('<I', d, o)[0]
def u16(d, o): return struct.unpack_from('<H', d, o)[0]
def isptr(v): return ROM + RODATA[0] <= v < ROM + RODATA[1]


def zdecode(d, t):
    out, end = wfz.decompress_stream(d, t + 4, 0, lit_bits=0)
    return out, end


def parse_step(d, t, banks=None):
    """-> dict(type, ...) or raises. `end` = first byte after the step's own data (None = unknown, use the label)."""
    ty = d[t + 2]
    if ty == 0:
        ins, e = B.decode(d, t + 3); return {'type': 0, 'code': (t + 3, e), 'end': e}
    if ty == 3:
        e = t + 4
        while u16(d, e): e += 2
        txt = d[t + 4:e].decode('utf-16-le')
        return {'type': 3, 'pad': d[t + 3], 'text': txt, 'end': e + 2}
    if ty == 4:
        if t % 4: raise B.BadCode('unaligned zcode')
        out, e = zdecode(d, t)
        if len(out) > ZBUF: raise B.BadCode('zcode too big')
        B.decode(out, 0); return {'type': 4, 'pad': d[t + 3], 'raw': out, 'end': e}
    if ty in (5, 6):
        ref = u32(d, t + 4); b, off, ln = ref & 0x3F, (ref >> 6) & 0x7FFF, ref >> 21
        if b >= 7 or ln == 0 or (banks and off + ln > len(banks[b])): raise B.BadCode('bad text ref')
        s = {'type': ty, 'speaker': d[t + 3], 'ref': (b, off, ln), 'end': t + 8}
        if ty == 6:
            ins, e = B.decode(d, t + 8); s['code'] = (t + 8, e); s['end'] = e
        return s
    if ty in (1, 2, 7, 8, 9):
        return {'type': ty, 'end': None}
    raise B.BadCode('unknown step type %d' % ty)


def read_list(d, o):
    items = []; p = o
    while isptr(u32(d, p)): items.append(u32(d, p) - ROM); p += 4
    return items, u32(d, p) == 0


def valid_list(d, o, items, banks):
    if not items or L.name_at(o) is None: return False
    try:
        for t in items:
            if L.name_at(t) is None: return False
            parse_step(d, t, banks)
    except (B.BadCode, IndexError, ValueError, UnicodeDecodeError):
        return False
    return True


GLOBAL_TABLE = 0x79B704


def find_lists(d, banks=None):
    """-> [(offset, items, terminated)] sorted by offset."""
    found = {}
    # 1. the global script table
    p = GLOBAL_TABLE
    while isptr(u32(d, p)):
        o = u32(d, p) - ROM; p += 4
        if o in found: continue
        items, term = read_list(d, o)
        if valid_list(d, o, items, banks): found[o] = (items, term)
    # 2. scan for 0-terminated pointer arrays whose targets look like steps with ids 1, 2, 3...
    o = RODATA[0]
    while o < RODATA[1] - 4:
        if not isptr(u32(d, o)) or isptr(u32(d, o - 4)) or o in found:
            o += 4; continue
        items, term = read_list(d, o)
        if term and all(u16(d, t) == i + 1 for i, t in enumerate(items)) and valid_list(d, o, items, banks):
            found[o] = (items, term); o += 4 * (len(items) + 1)
        else:
            o += 4
    return sorted((o, it, term) for o, (it, term) in found.items())


def preview(banks, ref, n=48):
    b, off, ln = ref
    if not banks: return ''
    s = banks[b][off:off + ln].replace('\n', ' ')
    s = re.sub(r'[\x00-\x1f]', '', s)
    return s[:n] + ('...' if len(s) > n else '')


def indent(text): return text.rstrip('\n')


_gi = None
_refs = None


def global_index(d):
    global _gi
    if _gi is None:
        _gi = {}; p = GLOBAL_TABLE; i = 0
        while isptr(u32(d, p)):
            _gi.setdefault(u32(d, p) - ROM, i); p += 4; i += 1
    return _gi


def referrers(d):
    """rodata offset -> labels of the objects holding a pointer to it (outside the global table)."""
    global _refs
    if _refs is None:
        _refs = {}
        at, keys = L.index()
        import bisect
        for p in range(RODATA[0], RODATA[1] - 3, 4):
            v = u32(d, p)
            if isptr(v) and not GLOBAL_TABLE <= p < GLOBAL_TABLE + 4 * 600:
                i = bisect.bisect_right(keys, p) - 1
                if i >= 0:
                    nm = at[keys[i]]
                    lst = _refs.setdefault(v - ROM, [])
                    if nm not in lst: lst.append(nm)
    return _refs


def qstr(t):
    return '"%s"' % t.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def export_list(d, o, items, term, banks, names, owner):
    """`owner`: step offset -> list offset that writes it in full (shared steps become `step ref`)."""
    lab = L.name_at(o)
    out = ['# Event list %s (0x%08X), %d steps%s.' % (lab, ROM + o, len(items),
           '' if term else ', FIXED LENGTH (no 0 terminator: steps can be edited, not added or removed)'),
           '# Syntax: see the top of tools/scripts/events.py. Native names: config/script_natives.txt.']
    gi = global_index(d).get(o)
    if gi is not None: out.append('# Global script %d: other scripts start it with run_event(%d, a, b).' % (gi, gi))
    refs = referrers(d).get(o)
    if refs: out.append('# Pointed to from: %s' % ', '.join(refs[:8]) + (' ...' if len(refs) > 8 else ''))
    out.append('')
    for t in items:
        s = parse_step(d, t, banks); tl = L.name_at(t); sid = u16(d, t)
        if owner.get(t, o) != o:
            out.append('step ref %s' % tl); continue
        ty = s['type']
        if ty == 0:
            out.append('step %d code        ; %s' % (sid, tl)); out.append(indent(B.disasm(d[:s['code'][1]], s['code'][0], names)[0]))
        elif ty == 3:
            out.append('step %d text%s %s   ; %s' % (sid, '' if s['pad'] == 0 else ' pad=%d' % s['pad'], qstr(s['text']), tl))
        elif ty == 4:
            out.append('step %d zcode%s       ; %s (stored compressed)' % (sid, '' if s['pad'] == 0 else ' pad=%d' % s['pad'], tl))
            out.append(indent(B.disasm(s['raw'], 0, names, stop=len(s['raw']))[0]))
        elif ty in (5, 6):
            kw = 'say' if ty == 5 else 'saycode'
            out.append('step %d %s 0x%02X @%d:%d:%d    ; %s "%s"' % (sid, kw, s['speaker'], *s['ref'], tl, preview(banks, s['ref'])))
            if ty == 6: out.append(indent(B.disasm(d[:s['code'][1]], s['code'][0], names)[0]))
        else:
            e = L.object_end(t)
            out.append('step %d raw %d %s   ; %s' % (sid, ty, d[t + 3:e].hex(' '), tl))
    return '\n'.join(out).rstrip('\n') + '\n'


# ------------------------------------------------------------------ compile
def parse_evt(text):
    """-> list of steps: dict(id, kind, rest, body lines, line)."""
    steps = []; cur = None
    for ln, l in enumerate(text.split('\n'), 1):
        if l.startswith('#') or not l.strip():
            if cur is not None and cur.get('body') is not None: cur['body'].append('')
            continue
        if l.startswith('step '):
            m = re.match(r'^step\s+ref\s+(\w+)', l)
            if m:
                cur = {'id': None, 'kind': 'ref', 'rest': m.group(1), 'line': ln, 'body': None}; steps.append(cur); continue
            m = re.match(r'^step\s+(\d+|auto)\s+(\w+)\s*(.*)$', l)
            if not m: raise ValueError('line %d: expected `step ID KIND ...`' % ln)
            kind, rest = m.group(2), m.group(3)
            if '"' not in rest: rest = rest.split(';')[0]
            cur = {'id': m.group(1), 'kind': kind, 'rest': rest.strip(), 'line': ln,
                   'body': [] if kind in ('code', 'zcode', 'saycode') else None}
            steps.append(cur); continue
        if cur is None or cur['body'] is None: raise ValueError('line %d: code outside a code step' % ln)
        cur['body'].append(l)
    ids = [int(x['id']) for x in steps if x['id'] not in (None, 'auto')]
    nxt = max(ids, default=0) + 1
    for x in steps:
        if x['id'] == 'auto': x['id'] = nxt; nxt += 1
        elif x['id'] is not None: x['id'] = int(x['id'])
    return steps


def unquote(s):
    m = re.match(r'^"((?:[^"\\]|\\.)*)"', s.strip())
    if not m: raise ValueError('expected a "quoted string": %r' % s)
    return re.sub(r'\\(.)', lambda k: {'n': '\n', 'r': '\r'}.get(k.group(1), k.group(1)), m.group(1))


def parse_text_arg(rest):
    """`0x02 @3:100:20` or `0x02 "Hello"` -> (speaker, ref tuple or str). `0x02 @7 "Hello"` puts a new line in
    dialogue bank 7 (a bank added after the game's own seven; see tools/assets/assets.py) -> (speaker, (7, str))."""
    m = re.match(r'^(\S+)\s+@(\d+):(\d+):(\d+)', rest)
    if m: return int(m.group(1), 0), tuple(int(x) for x in m.group(2, 3, 4))
    m = re.match(r'^(\S+)\s+@(\d+)\s+(".*)$', rest)
    if m: return int(m.group(1), 0), (int(m.group(2)), unquote(m.group(3)))
    m = re.match(r'^(\S+)\s+(".*)$', rest)
    if m: return int(m.group(1), 0), unquote(m.group(2))
    raise ValueError('expected SPEAKER @bank:off:len or SPEAKER "text": %r' % rest)


def _pad(rest):
    m = re.match(r'^pad=(\d+)\s*(.*)$', rest)
    return (int(m.group(1)), m.group(2)) if m else (0, rest)


def step_bytes(step, names, new_text):
    """Encode one step. new_text(str) -> packed ref for a new dialogue line."""
    k = step['kind']; sid = step['id']
    types = {'code': 0, 'text': 3, 'zcode': 4, 'say': 5, 'saycode': 6}
    if k == 'raw':
        p = step['rest'].split(';')[0].split()
        return struct.pack('<HB', sid, int(p[0])) + bytes.fromhex(''.join(p[1:]))
    if k not in types: raise ValueError('line %d: unknown step kind %s' % (step['line'], k))
    hdr = struct.pack('<HB', sid, types[k])
    if k == 'code': return hdr + B.asm('\n'.join(step['body']), names)
    if k == 'text':
        pad, rest = _pad(step['rest'])
        return hdr + bytes([pad]) + unquote(rest).encode('utf-16-le') + b'\0\0'
    if k == 'zcode':
        pad, _ = _pad(step['rest'])
        raw = B.asm('\n'.join(step['body']), names)
        if len(raw) > ZBUF: raise ValueError('zcode step longer than %d bytes' % ZBUF)
        return hdr + bytes([pad]) + compress_stream(raw)
    spk, ref = parse_text_arg(step['rest'])
    if isinstance(ref, str): r = new_text(ref)
    elif len(ref) == 2: r = new_text(ref[1], ref[0])
    else: r = ref[0] | ref[1] << 6 | ref[2] << 21
    b = hdr + bytes([spk]) + struct.pack('<I', r)
    if k == 'saycode': b += B.asm('\n'.join(step['body']), names)
    return b


def compile_list(d, o, items, term, text, names, new_text, outdir, tag):
    """Compare an edited .evt with the original list; return overrides (tools/assets/apply.py format)."""
    steps = parse_evt(text)
    if not term and len(steps) != len(items):
        raise ValueError('%s: this list has no 0 terminator, so it must keep %d steps' % (L.name_at(o), len(items)))
    ov = []; ptrs = []
    # lists numbered 1, 2, 3... must stay that way (the game finds the next step by id): renumber by position.
    # Written ids still say which original step a line is, so unchanged steps keep their objects.
    seq = all(u16(d, t) == i + 1 for i, t in enumerate(items))
    by_id = {}
    for t in items: by_id.setdefault(u16(d, t), []).append(t)
    for i, st in enumerate(steps):
        if st['kind'] == 'ref':
            ptrs.append(st['rest']); continue
        wid = st['id']
        if seq: st = dict(st, id=i + 1)
        data = step_bytes(st, names, new_text)
        # the original object of this step: same id (ids identify steps; positions change when steps are inserted)
        cand = [x for x in by_id.get(wid, []) if L.name_at(x) not in ptrs]   # unused objects with this id
        t = cand[0] if cand else None
        if t is not None:
            # the step's own bytes only: some steps are followed by unlabelled data (reached as label + offset)
            e = parse_step(d, t)['end'] or L.object_end(t)
            if st['kind'] == 'zcode' and d[t + 2] == 4:
                same = u16(d, t) == st['id'] and d[t + 3] == data[3] and \
                    B.asm('\n'.join(st['body']), names) == zdecode(d, t)[0]
            else:
                same = data == d[t:e]
            if not same:
                if st['kind'] == 'zcode' and t % 4 == 0 and len(data) % 4: data += bytes(4 - len(data) % 4)
                fn = os.path.join(outdir, 'ov_%06X_%s.bin' % (t, tag)); open(fn, 'wb').write(data)
                ov.append({'start': t, 'end': e, 'file': fn})
            ptrs.append(L.name_at(t))
        else:
            name = 'Event_%06X_s%d_%d' % (o, i, st['id'])
            fn = os.path.join(outdir, 'new_%s.bin' % name); open(fn, 'wb').write(data)
            ov.append({'new': name, 'file': fn}); ptrs.append(name)
    if len(ptrs) != len(items) or any(p != L.name_at(t) for p, t in zip(ptrs, items)):
        src = ''.join('\t.4byte %s\n' % p for p in ptrs) + ('\t.4byte 0\n' if term else '')
        fn = os.path.join(outdir, 'ov_%06X_%s_list.s' % (o, tag)); open(fn, 'w').write(src)
        ov.append({'start': o, 'end': o + 4 * (len(items) + (1 if term else 0)), 'file': fn,
                   'size': 4 * (len(ptrs) + (1 if term else 0))})
    return ov


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Disassemble one event list or script')
    ap.add_argument('addr', help='ROM address of an event list (0x08...)')
    a = ap.parse_args()
    os.chdir(os.path.join(HERE, '..', '..'))
    d = open('baserom.gba', 'rb').read()
    o = int(a.addr, 16) - ROM
    items, term = read_list(d, o)
    print(export_list(d, o, items, term, None, B.load_names(), {}))
