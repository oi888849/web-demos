# -*- coding: utf-8 -*-
"""Probe which qualities Bilibili will hand out without login (html5 platform, whole-file mp4)."""
import json, urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

BVS = ['BV15gtv6hEjs', 'BV1cQap6UEDY']
QNS = [116, 112, 80, 64, 32, 16]


def get(url, ref=None):
    r = urllib.request.Request(url, headers={'User-Agent': UA})
    if ref:
        r.add_header('Referer', ref)
    return urllib.request.urlopen(r, timeout=30).read().decode('utf-8')


for bv in BVS:
    v = json.loads(get('https://api.bilibili.com/x/web-interface/view?bvid=' + bv))['data']
    cid = v['cid']
    print('=== %s  %s  (%ss, up=%s)' % (bv, v['title'], v['duration'], v['owner']['name']))
    for qn in QNS:
        u = ('https://api.bilibili.com/x/player/playurl?bvid=%s&cid=%s&qn=%d'
             '&otype=json&type=mp4&platform=html5' % (bv, cid, qn))
        try:
            d = json.loads(get(u, 'https://www.bilibili.com/video/' + bv))
        except Exception as e:
            print('   qn=%-4s ERROR %s' % (qn, e)); continue
        if d.get('code') != 0:
            print('   qn=%-4s code=%s %s' % (qn, d.get('code'), d.get('message'))); continue
        dd = d['data']
        du = dd.get('durl') or []
        sizes = ', '.join('%.1fMB' % (x['size'] / 1048576.0) for x in du)
        print('   qn=%-4s -> served q=%-4s seg=%d  %s   accept=%s' % (
            qn, dd.get('quality'), len(du), sizes, dd.get('accept_quality')))
    print()
