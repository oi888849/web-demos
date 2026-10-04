# -*- coding: utf-8 -*-
"""Inspect the giant inline <script> lines of pomodoro/index.html: what keys/assets do they hold?"""
import re, os, base64

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pomodoro', 'index.html')
lines = open(SRC, encoding='utf-8', errors='replace').read().split('\n')

for idx in (1262, 1263, 1267):
    L = lines[idx - 1]
    print('=== 行 %d  (%.2f MB) ===' % (idx, len(L) / 1048576))
    print('  开头:', L[:150])
    # 找出所有 "key": 出现位置，估算每个 value 的长度
    keys = [(m.start(), m.group(1)) for m in re.finditer(r'"([A-Za-z0-9_]+)"\s*:\s*"?', L)]
    for i, (pos, k) in enumerate(keys):
        end = keys[i + 1][0] if i + 1 < len(keys) else len(L)
        print('   %-22s @%-9d  到下个键 %8.2f MB' % (k, pos, (end - pos) / 1048576))
    print()

# 行 1263 里非 base64 的分隔符有哪些？
L = lines[1262]
odd = sorted({c for c in L if not (c.isalnum() or c in '+/=')})
print('行1263 中的非 base64 字符:', ''.join(odd)[:200])
