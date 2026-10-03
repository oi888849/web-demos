# 宣传片视频存放处

把两个品牌官方宣传片按以下**确切文件名**放进本目录，再 `git push` 即可在落地页「官方宣传片」专区播放：

| 文件名 | 对应影片 |
|---|---|
| `gpt6-astra.mp4` | OpenAI — Introducing GPT-6 Astra（来自抖音 `7681414911264457466`） |
| `claude-fable5.mp4` | Anthropic — Claude Fable 5（来自抖音 `7649615092392720563`） |

## 如何拿到 .mp4
抖音链接无法直接嵌入 GitHub Pages，需先下载为文件：
- 任意「抖音视频下载」工具 / 浏览器插件导出 .mp4；
- 或手机录屏后转存。
- 单文件建议 < 100 MB（GitHub 软限制），宣传片通常几十 MB，没问题。

放入后提交：`git add videos && git commit -m "add promo videos" && git push`。
