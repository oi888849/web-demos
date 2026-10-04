# 宣传片视频存放处

落地页「官方宣传片」专区直接播放本目录下的 `.mp4`（相对路径 `videos/xxx.mp4`）。
全部本地直出，不依赖任何外站 iframe，因此不存在站外嵌入被拦截的问题。

| 文件名 | 对应影片 | 时长 | 编码 |
|---|---|---|---|
| `grok-bot.mp4` | xAI · Grok — Grok Bot 官方宣传片 | 75.4s | H.264 + AAC |
| `gpt6-astra.mp4` | OpenAI — Introducing GPT-6 Astra（中文字幕版） | 163.1s | H.264 + AAC |
| `openai-dots.mp4` | OpenAI — OpenAI dots 官方宣传片 | 147.9s | H.264 + AAC |
| `claude-fable5.mp4` | Anthropic — Claude Fable 5.1 | 85.4s | AV1 + AAC |
| `claude-opus-5-5.mp4` | Anthropic — Claude Opus 5.5 | 20.1s | AV1 + AAC |
| `minimax-design.mp4` | MiniMax — Design | 60.1s | AV1 + AAC |
| `minimax-h3.mp4` | MiniMax — H3 | 60.0s | AV1 + AAC |
| `minimax-m3.mp4` | MiniMax — M3 | 50.0s | AV1 + AAC |
| `zhipu-glm-5.mp4` | 智谱 — GLM-5 | 192.3s | AV1 + AAC |
| `zhipu-glm-5-1.mp4` | 智谱 — GLM-5.1 | 70.0s | AV1 + AAC |
| `zhipu-glm-5-2.mp4` | 智谱 — GLM-5.2 | 45.6s | AV1 + AAC |
| `zhipu-glm-5-3.mp4` | 智谱 — GLM-5.3 | 40.0s | AV1 + AAC |
| `zhipu-glm-5-3-flash.mp4` | 智谱 — GLM-5.3-Flash | 59.5s | AV1 + AAC |
| `zhipu-glm-5v-turbo.mp4` | 智谱 — GLM-5V-Turbo | 77.5s | AV1 + AAC |

同名 `.jpg` 为 `<video poster>` 封面图（来自 B站 稿件封面）。

## 约束

- **单文件 < 100 MB**（GitHub 硬限制）。当前最大 17.3 MB，目录合计约 102 MB。
- 文件名使用 ASCII 小写 + 连字符，避免 URL 编码问题。

## 校验与重建

```bash
python _check_mp4.py   # 纯 Python MP4 完整性校验（无需 ffmpeg）：解析 stsz/stsc/stco，确认每个采样都在文件范围内
python _build.py       # 按 CARDS 重新生成 index.html 的 .films 区块
python _grab_bili.py   # 需要新增 B站 片源时：取 720P 直链下载为本地 mp4 + 封面
```

`_grab_bili.py` 的原理：调用 `api.bilibili.com/x/player/playurl?...&platform=html5`
（未登录即可拿到 720P 的整段 mp4，非 DASH 分片），带 `Referer` 下载后落到本地，
从而彻底绕开 B站 对站外 iframe 嵌入的限制。
