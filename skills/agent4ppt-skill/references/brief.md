# Project brief

Paths in `references` resolve relative to the brief file at initialization. Reference paths and SHA-256 values are recorded. If an input changes, update that page deliberately using `revise --page-file` rather than silently regenerating against different evidence.

```json
{
  "title": "研究组周报",
  "language": "Chinese",
  "audience": "导师与同门",
  "ratio": "16:9",
  "backend": "builtin",
  "parallelism": 3,
  "style_name": "学术汇报",
  "style": "浅色学术风格，深蓝标题，实验图占页面主体",
  "context": "本周验证了检索方法；数据来自自建小样本，不能推广到公开基准。",
  "pages": [
    {
      "title": "实验结果",
      "bullets": ["比较方法与评价口径", "明确观察到的结果与限制"],
      "layout": "大图在左，右侧两段结论，底部写数据来源",
      "notes": "解释实验条件、失败案例和下一步。",
      "constraints": ["不得改变结果图中的数值和标签"],
      "references": [
        {"path": "assets/result.png", "role": "实验结果原图；保留数据、坐标与图例"}
      ]
    }
  ]
}
```

`backend` is `builtin`, `openai`, or `atlascloud`; it is fixed for the project. `ratio` is `16:9` or `4:3`. A brief has 1–500 pages; `parallelism` is 1–32. Pages receive numeric order from the array. Optional `image_options` carries model, size and quality into the request for an API worker. Each reference needs a path and a meaningful role. `context` can also be provided per page.

The database is authoritative. `brief.json` and `status.json` are readable snapshots, not a way to modify live state. Edit notes directly in `notes.md` using `## Slide N: Title` or `## 第 N 页：标题` headings. Change page copy or references through `revise` with a replacement page JSON; its reference paths resolve against the project folder. Update that page's notes when the story changes.

Project files: `project.sqlite3`, `brief.json`, `notes.md`, `requests/page-NNN.json`, `images/NNN-rREV-HASH.ext`, and `presentation.pptx`. Revision images are retained for comparison. Leases expire by default after 15 minutes; heartbeat with `renew` for long generations. Only `claim` reclaims expired jobs.

## 完整字段与结构化内容

`template --out brief.json` 写出可编辑示例，拒绝覆盖已有文件。示例不含真实结果，需要先替换内容。`prepare PROJECT` 为所有页生成 `plans/` 下的可检查请求快照，不领取任务；正式执行仍用 `claim`。

| 字段 | 用途 |
|---|---|
| `style_name` | 查询内置或个人完整风格，在初始化时冻结为 `style_recipe` |
| `style` | 当前项目额外视觉方向，可以是文本或对象 |
| `style_recipe` | 直接提供临时完整配方；有 `style_name` 时由查询结果覆盖 |
| `context` | 全局概念、术语、事实范围；页面也可提供自己的上下文 |
| `canvas` | 背景、内容区、密度等，页面设置优先 |
| `generation_method` | 工具、模式和实际可见参数约束，详见 production.md |
| 页面 `role` | 当前页承担的叙事角色 |
| 页面 `layout` | 可以含 intent、composition、zones、reading_order、relationship_to_previous |
| 页面 `visual_elements` | 主视觉与辅助标注的结构化说明 |
| 页面 `text` | 除标题及 bullets 外需要精确呈现的图注、标签等 |
| 页面 `image_options` | 覆盖全局 image_options 中的同名 API 参数 |
| 素材 `fidelity` | 素材内容不能改变的具体边界 |

结构化字段会作为 JSON 写入提示词，而不是 Python 字典的字符串形式。`notes` 仅用于讲稿，不自动成为页面可见文字。用户临时更改的风格文件不会影响已经冻结的项目配方。

每条 `references` 也支持含 Markdown 图片的字符串，例如 `"实验结果；不得重绘 ![真实曲线](assets/result.png)"`。路径中有空格时可用 `![说明](<assets/my figure.png>)`。使用对象形式更适合精细约束。

完整风格不是 API 参数。不要把 `style_recipe` 塞进请求 options；提示词负责视觉规则，options 只负责服务支持的生成参数。图片 API 的具体字段由 `image-job` 和 `image` 处理，不能只把 claim 的提示词复制出去而丢掉参考图。

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/11c2ce45621599b16bf6 -->
