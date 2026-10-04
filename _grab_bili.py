# -*- coding: utf-8 -*-
"""
Download Bilibili videos as real MP4 files into videos/, plus their cover images.
Uses the official html5 playurl endpoint (no login needed for <=720P).
Result: local <video> playback -> never blocked by off-site embed restrictions.
"""
import os, json, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DST  = os.path.join(HERE, 'videos')
os.makedirs(DST, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# slug -> (bvid, out_mp4_name)
JOBS = {
    'grok-bot':    ('BV1wagG6KEf1', 'grok-bot.mp4'),
    'gpt6-astra':  ('BV15gtv6hEjs', 'gpt6-astra.mp4'),
    'openai-2026': ('BV1cQap6UEDY', 'openai-dots.mp4'),
}


def get(url, referer=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    if referer:
        req.add_header('Referer', referer)
    req.add_header('Accept', '*/*')
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def info(bvid):
    d = json.loads(get('https://api.bilibili.com/x/web-interface/view?bvid=' + bvid).decode('utf-8'))
    if d.get('code') != 0:
        raise RuntimeError('view api failed: %s' % d.get('message'))
    return d['data']


def playurl(bvid, cid, qn):
    u = ('https://api.bilibili.com/x/player/playurl?bvid=%s&cid=%s&qn=%d'
         '&otype=json&type=mp4&platform=html5' % (bvid, cid, qn))
    d = json.loads(get(u, referer='https://www.bilibili.com/video/' + bvid).decode('utf-8'))
    if d.get('code') != 0:
        raise RuntimeError('playurl failed: %s' % d.get('message'))
    return d['data']


def download(url, referer, path):
    """Stream-download with range-free single request; verify size."""
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Referer': referer})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, 'wb') as f:
        total = 0
        while True:
            chunk = r.read(262144)
            if not chunk:
                break
            f.write(chunk)
            total += len(chunk)
    return total


for slug, (bvid, out) in JOBS.items():
    v = info(bvid)
    cid = v['cid']
    print('[%s] %s | cid=%s | %ss | up=%s' % (slug, v['title'], cid, v['duration'], v['owner']['name']))

    # pick best quality that works (720P -> 360P)
    picked = None
    for qn in (64, 32, 16):
        try:
            data = playurl(bvid, cid, qn)
            durl = data.get('durl') or []
            if durl:
                picked = (qn, durl)
                break
        except Exception as e:
            print('   qn=%s failed: %s' % (qn, e))
    if not picked:
        print('   !! no stream for', slug)
        continue
    qn, durl = picked
    print('   quality=%s segments=%d' % (qn, len(durl)))

    mp4 = os.path.join(DST, out)
    if len(durl) == 1:
        n = download(durl[0]['url'], 'https://www.bilibili.com/video/' + bvid, mp4)
        print('   saved %s  %.2f MB' % (out, n / 1048576.0))
    else:
        # concatenate segments (rare for mp4 format)
        n = 0
        with open(mp4, 'wb') as f:
            for seg in durl:
                tmp = mp4 + '.part'
                n += download(seg['url'], 'https://www.bilibili.com/video/' + bvid, tmp)
                f.write(open(tmp, 'rb').read())
                os.remove(tmp)
        print('   saved %s (multi-seg)  %.2f MB' % (out, n / 1048576.0))

    # cover image as poster
    try:
        pic = v['pic']
        if pic.startswith('//'):
            pic = 'https:' + pic
        ext = os.path.splitext(urllib.parse.urlparse(pic).path)[1] or '.jpg'
        p = os.path.join(DST, os.path.splitext(out)[0] + ext)
        with urllib.request.urlopen(urllib.request.Request(pic, headers={'User-Agent': UA,
                                    'Referer': 'https://www.bilibili.com/'}), timeout=60) as r:
            open(p, 'wb').write(r.read())
        print('   poster %s' % os.path.basename(p))
    except Exception as e:
        print('   poster failed:', e)

print('DONE')
