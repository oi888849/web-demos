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
  'grok-bot':         ('Grok Bot 官方宣传片', 'xAI · Grok', 'xai', 'xAI 具名 AI 队友 Grok Bot 官方宣传片。', 'bili', 'BV1cLaL6cEJb'),
  'gpt6-astra':       ('Introducing GPT-6 Astra', 'OpenAI', 'oai', 'OpenAI 旗舰模型发布影片——自主操作电脑、从一条指令到实体物件。', 'bili', 'BV1dTtv6aE5y'),
  'claude-fable5':    ('Claude Fable 5.1 宣传片', 'Anthropic', 'ant', 'Anthropic Fable 5.1 创意 / 通用能力发布影片（本地直出）。', 'local', 'claude-fable5.mp4'),
  'kimi-k3':          ('Kimi K3 宣传片', 'Moonshot · Kimi', 'misc', 'Moonshot Kimi K3 发布影片。', 'local', 'kimi-k3.mp4'),
  'grok-4-7':         ('Grok 4.7 宣传片', 'xAI', 'xai', 'xAI Grok 4.7 发布影片。', 'local', 'grok-4-7.mp4'),
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
  'hunyuan-video-foley': ('腾讯混元 Video-Foley 宣传片', '腾讯混元', 'misc', '腾讯混元 Video-Foley 图生视频发布影片。', 'local', 'hunyuan-video-foley.mp4'),
  'hunyuan-t1-show':  ('腾讯混元 T1 · 展示', '腾讯混元', 'misc', '腾讯混元 T1 深度思考模型展示片。', 'local', 'hunyuan-t1-show.mp4'),
  'qwen-audio-3-0':   ('阿里 Qwen-Audio 3.0 宣传片', '阿里 · Qwen', 'misc', '阿里巴巴 Qwen-Audio 3.0 发布影片。', 'local', 'qwen-audio-3-0.mp4'),
  'qwen-audio-3-1':   ('阿里 Qwen-Audio 3.1 宣传片', '阿里 · Qwen', 'misc', '阿里巴巴 Qwen-Audio 3.1 发布影片。', 'local', 'qwen-audio-3-1.mp4'),
  'qwen2-math':       ('阿里 Qwen2-Math 宣传片', '阿里 · Qwen', 'misc', '阿里巴巴 Qwen2-Math 发布影片。', 'local', 'qwen2-math.mp4'),
  'stepfun-step5':    ('阶跃 Step5 宣传片', '阶跃 StepFun', 'misc', '阶跃 StepFun Step5 发布影片。', 'local', 'stepfun-step5.mp4'),
  'ai-promo-extra':   ('阿里 千问办公 宣传片', '阿里 · 通义千问', 'misc', '阿里巴巴通义千问「千问办公」产品发布影片。', 'local', 'ai-promo-extra.mp4'),
  'openai-2026':      ('OpenAI 2026 发布会宣传片', 'OpenAI', 'oai', 'OpenAI 2026 秋季发布会影片（超 100MB，B站直嵌）。', 'bili', 'BV1cQap6UEDY'),
  'hunyuan-t1':       ('腾讯混元 T1 正式版发布', '腾讯混元', 'misc', '腾讯混元 T1 深度思考模型正式版发布影片（超 100MB，B站直嵌）。', 'bili', 'BV1xUoCYEE1L'),
}

ORDER = ['grok-bot','gpt6-astra','claude-fable5','kimi-k3','grok-4-7','claude-opus-5-5',
         'minimax-design','minimax-h3','minimax-m3','zhipu-glm-5','zhipu-glm-5-1','zhipu-glm-5-2',
         'zhipu-glm-5-3','zhipu-glm-5-3-flash','zhipu-glm-5v-turbo','hunyuan-video-foley',
         'hunyuan-t1-show','qwen-audio-3-0','qwen-audio-3-1','qwen2-math','stepfun-step5',
         'ai-promo-extra','openai-2026','hunyuan-t1']

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
        inner = ('      <iframe class="film-iframe" src="https://player.bilibili.com/player.html?bvid=%s&amp;page=1&amp;high_quality=1&amp;danmaku=0" scrolling="no" frameborder="0" allowfullscreen></iframe>\n'
                 '      <div class="film-meta">\n'
                 '        <span class="chip %s">%s</span>\n'
                 '        <h3>%s</h3>\n'
                 '        <p>%s</p>\n'
                 '        <p class="hint">来自 B站 %s</p>\n'
                 '      </div>') % (src, chip, brand, title, desc, src)
    else:
        inner = ('      <video class="film-v" controls preload="metadata" playsinline poster="">\n'
                 '        <source src="videos/%s" type="video/mp4">\n'
                 '        您的浏览器不支持视频播放。\n'
                 '      </video>\n'
                 '      <div class="film-meta">\n'
                 '        <span class="chip %s">%s</span>\n'
                 '        <h3>%s</h3>\n'
                 '        <p>%s</p>\n'
                 '      </div>') % (src, chip, brand, title, desc)
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
