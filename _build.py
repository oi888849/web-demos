# -*- coding: utf-8 -*-
"""
Regenerate the AI model promo "film wall" (.films section) of index.html.

Availability model (no external zip required):
  - Bilibili cards (kind='bili') are always available (embedded iframe).
  - A local card (kind='local') is available iff videos/<filename> exists.
This is idempotent and re-runnable; re-running just re-splits the same block.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DST  = os.path.join(HERE, 'videos')
IDX  = os.path.join(HERE, 'index.html')

# slug -> (title, brand, chip_class, desc, kind, file_or_bvid)
CARDS = {
  'grok-bot':         ('Grok Bot 官方宣传片', 'xAI · Grok', 'xai', 'xAI 具名 AI 队友 Grok Bot 发布影片。', 'local', 'grok-bot.mp4'),
  'gpt6-astra':       ('Introducing GPT-6 Astra', 'OpenAI', 'oai', 'OpenAI 旗舰模型发布影片（中文字幕版）。', 'local', 'gpt6-astra.mp4'),
  'claude-fable5':    ('Claude Fable 5.1 宣传片', 'Anthropic', 'ant', 'Anthropic Fable 5.1 创意 / 通用能力发布影片（本地直出）。', 'local', 'claude-fable5.mp4'),
  'claude-opus-5-5':  ('Claude Opus 5.5 宣传片', 'Anthropic', 'ant', 'Anthropic Claude Opus 5.5 发布影片。', 'local', 'claude-opus-5-5.mp4'),
  'minimax-design':   ('MiniMax Design 宣传片', 'MiniMax', 'misc', 'MiniMax Design 模型发布影片。', 'local', 'minimax-design.mp4'),
  'minimax-h3':       ('MiniMax H3 宣传片', 'MiniMax', 'misc', 'MiniMax H3 发布影片。', 'local', 'minimax-h3.mp4'),
  'minimax-m3':       ('MiniMax M3 宣传片', 'MiniMax', 'misc', 'MiniMax M3 发布影片。', 'local', 'minimax-m3.mp4'),
  'zhipu-glm-5':      ('智谱 GLM-5 宣传片', '智谱 AI', 'misc', '智谱 GLM-5 系列发布影片。', 'local', 'zhipu-glm-5.mp4'),
  'zhipu-glm-5-1':    ('智谱 GLM-5.1 宣传片', '智谱 AI', 'misc', '智谱 GLM-5.1 发布影片。', 'local', 'zhipu-glm-5-1.mp4'),
  'zhipu-glm-5-2':    ('智谱 GLM-5.2 宣传片', '智谱 AI', 'misc', '智谱 GLM-5.2 发布影片。', 'local', 'zhipu-glm-5-2.mp4'),
  'zhipu-glm-5-3':    ('智谱 GLM-5.3 宣传片', '智谱 AI', 'misc', '智谱 GLM-5.3 发布影片。', 'local', 'zhipu-glm-5-3.mp4'),
  'zhipu-glm-5-3-flash': ('智谱 GLM-5.3-Flash 宣传片', '智谱 AI', 'misc', '智谱 GLM-5.3-Flash 发布影片。', 'local', 'zhipu-glm-5-3-flash.mp4'),
  'zhipu-glm-5v-turbo': ('智谱 GLM-5V-Turbo 宣传片', '智谱 AI', 'misc', '智谱 GLM-5V-Turbo 发布影片。', 'local', 'zhipu-glm-5v-turbo.mp4'),
  'openai-dots':      ('OpenAI dots 宣传片', 'OpenAI', 'oai', 'OpenAI dots 官方发布影片（720P 本地直出）。', 'local', 'openai-dots.mp4'),
}

# optional footnote shown under a card (source attribution)
NOTES = {
  'grok-bot':    '片源 B站 · 量子位Daily（已转本地）',
  'gpt6-astra':  '片源 B站 · AI顾晚宁（已转本地）',
  'openai-dots': '片源 B站 · 花火火花Official（已转本地）',
}

# optional poster image (auto-detected next to the mp4 if present)
def poster_for(src):
    for ext in ('.jpg', '.jpeg', '.png', '.webp'):
        p = src.rsplit('.', 1)[0] + ext
        if os.path.exists(os.path.join(DST, p)):
            return 'videos/' + p
    return ''

ORDER = ['grok-bot','gpt6-astra','claude-fable5','claude-opus-5-5',
         'minimax-design','minimax-h3','minimax-m3','zhipu-glm-5','zhipu-glm-5-1','zhipu-glm-5-2',
         'zhipu-glm-5-3','zhipu-glm-5-3-flash','zhipu-glm-5v-turbo',
         'openai-dots']

# ---- determine which cards are available ----
used = set()
missing_local = []
for slug, (title, brand, chip, desc, kind, src) in CARDS.items():
    if kind == 'bili':
        used.add(slug)
    else:
        if os.path.exists(os.path.join(DST, src)):
            used.add(slug)
        else:
            missing_local.append(slug)

# ---- build HTML block ----
cards_html = []
for slug in ORDER:
    if slug not in used:
        print('MISSING:', slug)
        continue
    title, brand, chip, desc, kind, src = CARDS[slug]
    if kind == 'bili':
        inner = ('      <iframe class="film-iframe" src="https://player.bilibili.com/player.html?bvid=%s&amp;page=1&amp;as_wide=1&amp;danmaku=0" scrolling="no" frameborder="0" allowfullscreen loading="lazy"></iframe>\n'
                 '      <div class="film-meta">\n'
                 '        <span class="chip %s">%s</span>\n'
                 '        <h3>%s</h3>\n'
                 '        <p>%s</p>\n'
                 '        <p class="hint">来自 B站 %s</p>\n'
                 '      </div>') % (src, chip, brand, title, desc, src)
    else:
        note = NOTES.get(slug)
        note_html = ('\n        <p class="hint">%s</p>' % note) if note else ''
        inner = ('      <video class="film-v" controls preload="metadata" playsinline poster="%s">\n'
                 '        <source src="videos/%s" type="video/mp4">\n'
                 '        您的浏览器不支持视频播放。\n'
                 '      </video>\n'
                 '      <div class="film-meta">\n'
                 '        <span class="chip %s">%s</span>\n'
                 '        <h3>%s</h3>\n'
                 '        <p>%s</p>\n'
                 '      </div>') % (poster_for(src), src, chip, brand, title, desc)
        if note_html:
            inner = inner.replace('      </div>', note_html + '\n      </div>')
    cards_html.append('      <article class="film reveal d6">\n' + inner + '\n      </article>')

block = '\n'.join(cards_html)
print('TOTAL CARDS:', len(cards_html), '| missing local:', missing_local)

# ---- regenerate index.html ----
html = open(IDX, encoding='utf-8').read()
if '.chip.misc' not in html:
    html = html.replace(
      '  .chip.ant{background:rgba(244,114,182,.15); color:#f9a8d4; border:1px solid rgba(244,114,182,.4);}',
      '  .chip.ant{background:rgba(244,114,182,.15); color:#f9a8d4; border:1px solid rgba(244,114,182,.4);}\n'
      '  .chip.misc{background:rgba(255,255,255,.10); color:#cdd6ff; border:1px solid rgba(255,255,255,.22);}')
html = re.sub(r'<b>\d+</b>品牌影片', '<b>%d</b>品牌影片' % len(cards_html), html)

# splice the films block between <div class="films"> and its closing </div>
marker = '<div class="films">'
start = html.index(marker) + len(marker)
sec_end = html.index('</section>', start)
films_close = html.rindex('</div>', start, sec_end)
new_html = html[:start] + '\n' + block + '\n      ' + html[films_close:]
open(IDX, 'w', encoding='utf-8').write(new_html)
print('INDEX updated. cards=%d' % len(cards_html))
