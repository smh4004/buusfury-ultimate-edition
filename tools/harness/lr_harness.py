#!/usr/bin/env python3
"""The mGBA harness's script commands on a libretro GBA core (VBA-M), for save-type tests.
usage: lr_harness.py CORE MODE ROM SCRIPT OUTDIR      env HARNESS_SAV=<save file>
MODE retroarch: the save file is copied into the core's save memory after loading (up to its size) and written back from it at the end,
                as RetroArch and other libretro frontends do.
MODE delta:     Delta's GBA core (GBADeltaCore, VBA-M of Nov 2018): the save type from utilGBAFindSave, flash size 64 KB, then
                CPUReadBatteryFile / CPUWriteBatteryFile on the save file (needs a core built with those symbols exported).
Commands: run N | keys K,K | tap K [N] | poke ADDR VAL | poke8 ADDR VAL | mem ADDR [N] | dump NAME ADDR LEN | shot NAME"""
import ctypes as C, os, struct, sys, zlib

CORE, MODE, ROM, SCRIPT, OUT = sys.argv[1:6]
SAV = os.environ.get('HARNESS_SAV')
lib = C.CDLL(os.path.abspath(CORE))
ENV = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
STATE = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
LOGF = C.CFUNCTYPE(None, C.c_int, C.c_char_p)            # retro_log_printf_t (its variadic arguments are not read)


class Desc(C.Structure):
    _fields_ = [('flags', C.c_uint64), ('ptr', C.c_void_p), ('offset', C.c_size_t), ('start', C.c_size_t), ('select', C.c_size_t),
                ('disconnect', C.c_size_t), ('len', C.c_size_t), ('addrspace', C.c_char_p)]


class Map(C.Structure):
    _fields_ = [('descriptors', C.POINTER(Desc)), ('num', C.c_uint)]


class Var(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]


class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]


DIR = C.c_char_p(os.path.abspath(OUT).encode())
regions = []          # (start, len, address of byte 0)
fmt = [0]; frame = [None]; pressed = [0]
LOG = []


def env(cmd, data):
    cmd &= 0xFFFF
    if cmd in (9, 31):                                   # system / save directory
        C.cast(data, C.POINTER(C.c_char_p))[0] = DIR.value; return True
    if cmd == 10:
        fmt[0] = C.cast(data, C.POINTER(C.c_uint))[0]; return True
    if cmd == 15:
        C.cast(data, C.POINTER(Var))[0].value = None; return False
    if cmd == 17:
        C.cast(data, C.POINTER(C.c_bool))[0] = False; return True
    if cmd == 27:
        C.cast(data, C.POINTER(C.c_void_p))[0] = C.cast(cbs[6], C.c_void_p).value; return True
    if cmd == 36:
        m = C.cast(data, C.POINTER(Map))[0]
        for i in range(m.num):
            d = m.descriptors[i]
            if d.ptr and d.len: regions.append((d.start, d.len, d.ptr + d.offset))
        return True
    return False


def video(data, w, h, pitch):
    if data: frame[0] = (C.string_at(data, pitch * h), w, h, pitch)


def batch(data, n): return n


BITS = {'B': 0, 'SELECT': 2, 'START': 3, 'UP': 4, 'DOWN': 5, 'LEFT': 6, 'RIGHT': 7, 'A': 8, 'L': 10, 'R': 11}


def state(port, device, index, id_):
    if port or device != 1: return 0
    if id_ == 256: return pressed[0]
    return 1 if pressed[0] >> id_ & 1 else 0


def logf(level, fmt):
    if os.environ.get('LR_LOG'): print('log', level, fmt)


cbs = [ENV(env), VIDEO(video), AUDIO(lambda l, r: None), BATCH(batch), POLL(lambda: None), STATE(state), LOGF(logf)]
lib.retro_set_environment(cbs[0])
lib.retro_init()
lib.retro_set_video_refresh(cbs[1]); lib.retro_set_audio_sample(cbs[2]); lib.retro_set_audio_sample_batch(cbs[3])
lib.retro_set_input_poll(cbs[4]); lib.retro_set_input_state(cbs[5])
rom = open(ROM, 'rb').read(); buf = C.create_string_buffer(rom, len(rom))
gi = GameInfo(os.path.abspath(ROM).encode(), C.cast(buf, C.c_void_p), len(rom), None)
lib.retro_load_game.restype = C.c_bool
if not lib.retro_load_game(C.byref(gi)): sys.exit('load failed')
lib.retro_set_controller_port_device(0, 1)                # a joypad in port 1, as a frontend sets it
lib.retro_get_memory_data.restype = C.c_void_p; lib.retro_get_memory_size.restype = C.c_size_t
if MODE == 'retroarch':
    size = lib.retro_get_memory_size(0); ptr = lib.retro_get_memory_data(0)
    print('save memory %d bytes' % size)
    if SAV and os.path.exists(SAV) and size:
        b = open(SAV, 'rb').read()[:size]; C.memmove(ptr, b, len(b))
elif MODE == 'delta':
    lib._Z15utilGBAFindSavei(len(rom))
    lib._Z12flashSetSizei(0x10000)
    lib._Z8CPUResetv()
    print('save type %d' % C.c_int.in_dll(lib, 'saveType').value)
    if SAV and os.path.exists(SAV): lib._Z18CPUReadBatteryFilePKc(SAV.encode())


def where(a):
    for s, n, p in regions:
        if s <= a < s + n: return p + a - s
    sys.exit('no memory at %08X' % a)


def rd(a, n): return C.string_at(where(a), n)


def wr(a, b): C.memmove(where(a), b, len(b))


def run(n):
    for _ in range(n): lib.retro_run()


def png(path):
    data, w, h, pitch = frame[0]; rows = []
    for y in range(h):
        row = data[y * pitch:(y + 1) * pitch]; px = bytearray()
        for x in range(w):
            if fmt[0] == 1:
                b, g, r = row[4 * x], row[4 * x + 1], row[4 * x + 2]
            else:
                v = row[2 * x] | row[2 * x + 1] << 8
                if fmt[0] == 2: r, g, b = (v >> 11 & 31) << 3, (v >> 5 & 63) << 2, (v & 31) << 3
                else: r, g, b = (v >> 10 & 31) << 3, (v >> 5 & 31) << 3, (v & 31) << 3
            px += bytes((r, g, b))
        rows.append(b'\0' + bytes(px))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))


keys = 0
for line in open(SCRIPT):
    line = line.split('#')[0].split()
    if not line: continue
    c, a = line[0], line[1:]
    parse = lambda s: sum(1 << BITS[k] for k in s.replace(',', ' ').split() if k in BITS)
    if c == 'keys': keys = parse(a[0]) if a else 0; pressed[0] = keys
    elif c == 'run': run(int(a[0]))
    elif c == 'tap':
        pressed[0] = keys | parse(a[0]); run(4); pressed[0] = keys; run(int(a[1]) if len(a) > 1 else 30)
    elif c == 'poke': wr(int(a[0], 16), struct.pack('<I', int(a[1], 16)))
    elif c == 'poke8': wr(int(a[0], 16), bytes((int(a[1], 16),)))
    elif c == 'mem':
        ad = int(a[0], 16); n = int(a[1]) if len(a) > 1 else 4
        print('mem %08x:' % ad + ''.join(' %08x' % v for v in struct.unpack('<%dI' % n, rd(ad, 4 * n))), flush=True)
    elif c == 'dump': open('%s/%s.bin' % (OUT, a[0]), 'wb').write(rd(int(a[1], 16), int(a[2], 16)))
    elif c == 'shot': png('%s/%s.png' % (OUT, a[0]))
if MODE == 'retroarch' and SAV:
    size = lib.retro_get_memory_size(0)
    if size: open(SAV, 'wb').write(C.string_at(lib.retro_get_memory_data(0), size))
elif MODE == 'delta' and SAV:
    lib._Z19CPUWriteBatteryFilePKc(SAV.encode())
