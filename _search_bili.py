# -*- coding: utf-8 -*-
"""Search Bilibili for candidate promo videos and report their real resolution.
Uses view?bvid -> data.dimension (width/height) so we know 1080P before downloading.
Search API is 412-prone: keep queries few, add browser-like headers, sleep between calls.
"""
import json, time, urllib.request, urllib.parse, sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
SEARCH = 'https://api.bilibili.com/x/web-interface/search/type'


def get(url, ref='https://www.bilibili.com/'):
    r = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': ref, 'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9', 'Origin': 'https://www.bilibili.com'})
    return urllib.request.urlopen(r, timeout=30).read().decode('utf-8')


def view(bvid):
    try:
        d = json.loads(get('https://api.bilibili.com/x/web-interface/view?bvid=' + bvid))
        return d.get('data') if d.get('code') == 0 else None
    except Exception:
        return None


def search(kw, page=1):
    u = '%s?search_type=video&keyword=%s&page=%d&order=totalrank' % (
        SEARCH, urllib.parse.quote(kw), page)
    try:
        d = json.loads(get(u, 'https://search.bilibili.com/'))
    except Exception as e:
        print('  !! search failed:', e)
        return []
    if d.get('code') != 0:
        print('  !! code=%s %s' % (d.get('code'), d.get('message')))
        return []
    return (d.get('data') or {}).get('result') or []


def probe(kw, limit=8):
    print('### %s' % kw)
    for it in search(kw)[:limit]:
        bv = it.get('bvid')
        v = view(bv)
        if not v:
            continue
        dim = v.get('dimension') or {}
        w, h = dim.get('width'), dim.get('height')
        tag = '1080P' if (h or 0) >= 1080 or (w or 0) >= 1920 else ('720P' if (h or 0) >= 720 else '低清')
        print('  %-14s %-6s %-9s %5ss  %-18s %s' % (
            bv, tag, '%sx%s' % (w, h), v.get('duration'),
            (v.get('owner') or {}).get('name', '')[:18],
            (it.get('title') or '').replace('<em class="keyword">', '').replace('</em>', '')[:52]))
        time.sleep(0.4)
    print()


for kw in sys.argv[1:]:
    probe(kw)
    time.sleep(1.0)
