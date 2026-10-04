# -*- coding: utf-8 -*-
"""Build a minimal Bilibili 'session' (buvid3/buvid4 cookies) to get past the 412 risk control.
Used by _search_bili.py / _grab_bili.py when the plain API returns 412.
"""
import json, time, http.cookiejar, urllib.request, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

CJ = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))


def _req(url, ref='https://www.bilibili.com/'):
    r = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': ref,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9'})
    return OPENER.open(r, timeout=30).read().decode('utf-8')


def bootstrap():
    """Fill buvid3/buvid4 cookies, then hit the search page once so cookies look 'warmed'."""
    try:
        d = json.loads(_req('https://api.bilibili.com/x/frontend/finger/spi'))
        b3 = (d.get('data') or {}).get('b_3')
        b4 = (d.get('data') or {}).get('b_4')
    except Exception as e:
        print('spi failed:', e)
        b3 = b4 = None
    for name, val in (('buvid3', b3), ('buvid4', b4), ('b_nut', str(int(time.time())))):
        if val:
            CJ.set_cookie(http.cookiejar.Cookie(
                0, name, val, None, False, '.bilibili.com', True, False, '/', True,
                False, None, False, None, None, {}))
    try:
        _req('https://search.bilibili.com/', 'https://www.bilibili.com/')
    except Exception:
        pass
    return b3


def get(url, ref='https://www.bilibili.com/'):
    r = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': ref,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Origin': 'https://www.bilibili.com'})
    return OPENER.open(r, timeout=30).read().decode('utf-8')


def search(kw, page=1):
    u = ('https://api.bilibili.com/x/web-interface/search/type?search_type=video'
         '&keyword=%s&page=%d&order=totalrank' % (urllib.parse.quote(kw), page))
    d = json.loads(get(u, 'https://search.bilibili.com/'))
    if d.get('code') != 0:
        raise RuntimeError('code=%s %s' % (d.get('code'), d.get('message')))
    return (d.get('data') or {}).get('result') or []


def view(bvid):
    d = json.loads(get('https://api.bilibili.com/x/web-interface/view?bvid=' + bvid))
    return d.get('data') if d.get('code') == 0 else None


if __name__ == '__main__':
    import sys
    b3 = bootstrap()
    print('buvid3 =', (b3 or 'none')[:24], '...')
    for kw in sys.argv[1:]:
        print('### %s' % kw)
        try:
            res = search(kw)
        except Exception as e:
            print('  !!', e); continue
        for it in res[:8]:
            v = view(it.get('bvid'))
            if not v:
                continue
            w = (v.get('dimension') or {}).get('width')
            h = (v.get('dimension') or {}).get('height')
            tag = '1080P' if (h or 0) >= 1080 else ('720P' if (h or 0) >= 720 else '低清')
            t = (it.get('title') or '')
            for junk in ('<em class="keyword">', '</em>'):
                t = t.replace(junk, '')
            print('  %-14s %-6s %-9s %5ss  %-16s %s' % (
                it.get('bvid'), tag, '%sx%s' % (w, h), v.get('duration'),
                (v.get('owner') or {}).get('name', '')[:16], t[:50]))
            time.sleep(0.35)
        print()
        time.sleep(1.0)
