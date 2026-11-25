# Talk Show · 中英卡拉 OK 后期

用于已经生成的 9:16 单镜头原片。保留舞台与原声，英文当前词金色高亮、简体中文整句显示。台词结束后才叠加「评论区看解析 ↓」，不提前剧透。这个工具离线合成，不调用 Google Flow，不改 EP001 的流程，也不发布视频。

## 环境与运行

需要 Python 3、FFmpeg/FFprobe（含 libass、libx264 和 AAC 编码器），以及 DejaVu Sans、Noto Sans CJK SC 两种字体。

在仓库根目录执行：

```bash
python3 tools/talkshow_karaoke/render_bilingual.py \
  /path/to/input.mp4 \
  tools/talkshow_karaoke/example_cues.json \
  /path/to/output.mp4
```

示例 JSON 仅用于说明格式，正式制作请复制并按原声调整：

- `cues`：每段的 [起点秒, 终点秒, 英文, 简中]。短句逐段显示，避免提前露出笑点。
- `word_onsets`：每个英文词的**绝对**出声时间，顺序和数量与对应英文短句一致。不要均分时间推算包袱。省略此字段时仅显示静态双语。
- `cta_start`：字幕结束后、原片末尾前，评论提示开始的绝对秒数。`cta_duration` 可设置提示的最短展示时长，默认 1.55 秒；若原片仍有余量则持续到片尾，否则保留最后一帧补足。
- 输出前抽查包袱前、包袱词、评论提示三个位置，并在目标 App 预览确认界面没有盖住字幕或图标。评论提示只指出查看位置，不自动发布或置顶解析。

`talkshow_comment_cta.png`（984 × 240，透明底）可直接用于剪映；`talkshow_comment_cta.svg` 是文字已转曲的母版。渲染器默认使用同目录 PNG，或用 `--badge` 指定另一张透明图。平时不用重做图标；若需要重新生成，`build_badge.py` 需要 fontTools 和 Inkscape，可选传入 Noto Sans CJK Bold 字体文件及简体中文字体索引（该 TTC 通常为 2）。
