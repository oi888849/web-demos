# -*- coding: utf-8 -*-
"""Idempotently inject _addon.js into pomodoro/index.html right before </body>.
Re-running replaces the previously injected block instead of duplicating it.
"""
import os, io

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '_addon.js')
DST = os.path.join(HERE, 'pomodoro', 'index.html')

BEGIN = '<!-- MP2_ADDON_BEGIN -->'
END = '<!-- MP2_ADDON_END -->'

addon = io.open(SRC, encoding='utf-8').read()
if '</script' in addon.lower():
    raise SystemExit('addon 里不能出现 </script，否则会提前关闭脚本标签')

html = io.open(DST, encoding='utf-8', errors='replace').read()

# 去掉旧的注入块
n_before = len(html)
if BEGIN in html and END in html:
    a = html.index(BEGIN)
    b = html.index(END) + len(END)
    html = html[:a] + html[b:]
    print('已移除旧注入块（%d 字符）' % (n_before - len(html)))

block = '\n%s\n<script>\n%s\n</script>\n%s\n' % (BEGIN, addon.rstrip(), END)

tail = '</body>'
pos = html.rfind(tail)
if pos < 0:
    raise SystemExit('找不到 </body>')
html = html[:pos] + block + html[pos:]

io.open(DST, 'w', encoding='utf-8').write(html)
print('注入完成：+%.1f KB，文件现 %.2f MB' % (len(block) / 1024.0, os.path.getsize(DST) / 1048576.0))
