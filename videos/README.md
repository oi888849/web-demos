# 宣传片视频存放处

落地页「官方宣传片」专区直接播放本目录下的 `.mp4`（相对路径 `videos/xxx.mp4`）。
全部本地直出，不依赖任何外站 iframe，因此不存在站外嵌入被拦截的问题。

| 文件名 | 对应影片 | 时长 | 分辨率 | 编码 |
|---|---|---|---|---|
| `gpt6-astra.mp4` | OpenAI — GPT-6 Astra 官方宣传片（精校中英字幕） | 162.9s | 1280x720 | H.264 + AAC |
| `openai-dots.mp4` | OpenAI — Dots 官方宣传片（双语字幕） | 147.7s | 1280x720 | H.264 + AAC |
| `claude-fable5.mp4` | Anthropic — Claude Fable 5.1 | 85.4s | 1920x1080 | H.264 + AAC |
| `claude-opus-5-5.mp4` | Anthropic — Claude Opus 5.5 | 20.1s | 1920x1080 | AV1 + AAC |
| `minimax-design.mp4` | MiniMax — Design | 60.1s | 1920x1080 | AV1 + AAC |
| `minimax-h3.mp4` | MiniMax — H3 | 60.0s | 1920x1080 | AV1 + AAC |
| `minimax-m3.mp4` | MiniMax — M3 | 50.0s | 1920x1080 | AV1 + AAC |
| `zhipu-glm-5.mp4` | 智谱 — GLM-5 | 192.3s | 1920x1080 | AV1 + AAC |
| `zhipu-glm-5-1.mp4` | 智谱 — GLM-5.1 | 70.0s | 1920x1080 | AV1 + AAC |
| `zhipu-glm-5-2.mp4` | 智谱 — GLM-5.2 | 45.6s | 1920x1080 | AV1 + AAC |
| `zhipu-glm-5-3.mp4` | 智谱 — GLM-5.3 | 40.0s | 1920x1080 | AV1 + AAC |
| `zhipu-glm-5-3-flash.mp4` | 智谱 — GLM-5.3-Flash | 59.5s | 1920x1080 | AV1 + AAC |
| `zhipu-glm-5v-turbo.mp4` | 智谱 — GLM-5V-Turbo | 77.5s | 1920x1080 | AV1 + AAC |

同名 `.jpg` 为 `<video poster>` 封面图（来自 B站 稿件封面）。

## 约束

- **单文件 < 100 MB**（GitHub 硬限制）。当前最大 17.3 MB，目录合计约 95 MB。
- **分辨率**：13 个文件中 11 个为 1920x1080；`gpt6-astra` / `openai-dots` 受 B站 未登录限制只能取到 720P
  （源片是 1080P，已挑码率最高的稿子，11.1MB / 9.7MB）。要真正 1080P 需带 SESSDATA 的登录 Cookie。
- 文件名使用 ASCII 小写 + 连字符，避免 URL 编码问题。

## 校验与重建

```bash
python _check_mp4.py   # 纯 Python MP4 完整性校验（无需 ffmpeg）：解析 stsz/stsc/stco，确认每个采样都在文件范围内
python _build.py       # 按 CARDS 重新生成 index.html 的 .films 区块
python _grab_bili.py   # 需要新增 B站 片源时：取直链下载为本地 mp4 + 封面
python _bili_session.py "关键词"  # 带 buvid cookie 搜索（绕过 412 风控），会打印每个稿子的真实分辨率
python _probe_qn.py    # 探测某个 BV 未登录能拿到的最高清晰度
```

`_grab_bili.py` 的原理：调用 `api.bilibili.com/x/player/playurl?...&platform=html5`
（未登录即可拿到 720P 的整段 mp4，非 DASH 分片），带 `Referer` 下载后落到本地，
从而彻底绕开 B站 对站外 iframe 嵌入的限制。
