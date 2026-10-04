# -*- coding: utf-8 -*-
"""Pure-python MP4 integrity check (no ffprobe): verify every media sample lies inside the file."""
import os, struct

DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')

CONTAINERS = (b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'udta')


def iter_boxes(f, end):
    """Yield (type, body_start, box_end) for boxes within [f.tell(), end).
    Always seeks absolutely, so callers may move the file pointer freely."""
    while f.tell() < end:
        pos = f.tell()
        hdr = f.read(8)
        if len(hdr) < 8:
            return
        size, typ = struct.unpack('>I4s', hdr)
        hdrlen = 8
        if size == 1:
            ext = f.read(8)
            if len(ext) < 8:
                return
            size = struct.unpack('>Q', ext)[0]
            hdrlen = 16
        elif size == 0:
            size = end - pos
        if size < hdrlen:
            return
        yield typ, pos + hdrlen, pos + size
        f.seek(pos + size)


def scan(f, end, out):
    for typ, body, stop in iter_boxes(f, end):
        out.setdefault(typ, []).append((body, stop))
        if typ in CONTAINERS:
            f.seek(body)
            scan(f, stop, out)


def parse_mvhd(f, body):
    f.seek(body)
    ver = struct.unpack('>B', f.read(1))[0]
    f.read(3)
    if ver == 1:
        f.read(16)
        ts = struct.unpack('>I', f.read(4))[0]
        dur = struct.unpack('>Q', f.read(8))[0]
    else:
        f.read(8)
        ts = struct.unpack('>I', f.read(4))[0]
        dur = struct.unpack('>I', f.read(4))[0]
    return dur / float(ts or 1)


def parse_stbl(f, body, stop):
    st = {}
    for typ, b, e in iter_boxes(f, stop):
        f.seek(b)
        f.read(4)                      # version(1) + flags(3)
        if typ == b'stsz':
            ss, cnt = struct.unpack('>II', f.read(8))
            st['sizes'] = [ss] * cnt if ss else list(struct.unpack('>%dI' % cnt, f.read(4 * cnt)))
        elif typ == b'stsc':
            cnt = struct.unpack('>I', f.read(4))[0]
            st['stsc'] = [struct.unpack('>III', f.read(12)) for _ in range(cnt)]
        elif typ == b'stco':
            cnt = struct.unpack('>I', f.read(4))[0]
            st['offs'] = list(struct.unpack('>%dI' % cnt, f.read(4 * cnt)))
        elif typ == b'co64':
            cnt = struct.unpack('>I', f.read(4))[0]
            st['offs'] = list(struct.unpack('>%dQ' % cnt, f.read(8 * cnt)))
        elif typ == b'stsd':
            cnt = struct.unpack('>I', f.read(4))[0]   # entry_count
            f.read(4)                                  # first entry size
            st['codec'] = f.read(4).decode('latin-1')
            st['entries'] = cnt
    return st


def sample_bounds_ok(f, st, fs):
    sizes, stsc, offs = st.get('sizes'), st.get('stsc'), st.get('offs')
    if not (sizes and stsc and offs):
        return True, 0, None
    idx = 0
    nsamp = 0
    for i, (first, per, _sdi) in enumerate(stsc):
        nxt = stsc[i + 1][0] if i + 1 < len(stsc) else len(offs) + 1
        for c in range(first, nxt):
            if c - 1 >= len(offs):
                break
            off = offs[c - 1]
            for _k in range(per):
                if idx >= len(sizes):
                    break
                sz = sizes[idx]
                if sz and off + sz > fs:
                    return False, nsamp, off
                off += sz
                idx += 1
                nsamp += 1
    return True, nsamp, None


def check(path):
    fs = os.path.getsize(path)
    f = open(path, 'rb')
    out = {}
    scan(f, fs, out)
    msgs = []
    for t in (b'moov', b'mdat', b'mvhd'):
        if t not in out:
            msgs.append('MISSING ' + t.decode())
    dur = parse_mvhd(f, out[b'mvhd'][0][0]) if b'mvhd' in out else None
    total = 0
    codecs = set()
    for b, e in out.get(b'stbl', []):
        f.seek(b)
        st = parse_stbl(f, b, e)
        if st.get('codec'):
            codecs.add(st['codec'])
        ok, n, off = sample_bounds_ok(f, st, fs)
        total += n
        if not ok:
            msgs.append('sample out of file @%d' % off)
    f.close()
    return (not msgs), msgs, dur, total, '/'.join(sorted(codecs)) or '?'


bad = 0
names = [n for n in sorted(os.listdir(DST)) if n.lower().endswith('.mp4')]
for n in names:
    p = os.path.join(DST, n)
    ok, msgs, dur, nsamp, codec = check(p)
    if not ok:
        bad += 1
    print('%s %-26s %6.2f MB  %7s  samples=%-6d %-6s %s' % (
        'OK ' if ok else 'BAD', n, os.path.getsize(p) / 1048576.0,
        ('%.1fs' % dur) if dur else '?', nsamp, codec,
        ('| ' + '; '.join(msgs)) if msgs else ''))
print('\nfiles=%d  BAD=%d' % (len(names), bad))
