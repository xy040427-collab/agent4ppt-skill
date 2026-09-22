# Project brief

## Production mode

`editable_workflow` 新建 editable 默认 `full_slide_first`：先生成带全部文字的成稿，再去字和拓印，强制 structured-v1。初始 overlays 坐标暂定；`record-design --overlays-file` 提交从成稿测得的最终坐标与样式，不得改变 IDs、类型和内容。选择 `reserved` 才使用预留区域提示与布局参考。已经初始化且缺少字段的项目继续旧路线，不会自动迁移。

`mode` is `full_slide` (default, preserving existing projects) or `editable`. Generate a starter with `template --mode editable --out brief.json`.

新 editable 项目使用 `review_policy: "structured-v1"`。overlay 可配置 `safe_padding`（0..0.1，按页高归一化，默认 0.012）和 `background_policy`（quiet 或 container）。quiet 排除图形和线条，container 允许简单背景容器但文字内部要清晰。布局图从 overlays 派生，避免维护第二套文字坐标。试排与生图后视觉检查仍由宿主执行。
Both use the same page queue. Editable pages keep one complete background and add only the explicitly selected native overlays.

```json
{
  "title": "处理器学习路线",
  "mode": "editable",
  "backend": "builtin",
  "ratio": "16:9",
  "pages": [{
    "title": "本周前置学习与阅读路线",
    "layout": "生成带标题和标签的完整成稿：三组立体方块，下方连续流程箭头与圆点。整体设计文字与插图。",
    "raster_text": ["×", "="],
    "overlays": [
      {"id": "title", "type": "text", "text": "本周前置学习与阅读路线", "x": 0.03, "y": 0.03, "w": 0.94, "h": 0.10, "font_size": 28, "bold": true},
      {"id": "cpu-label", "type": "text", "text": "CPU", "x": 0.06, "y": 0.20, "w": 0.22, "h": 0.06, "font_size": 18, "align": "center", "color": "0057FF"}
    ],
    "notes": "所有结构为概念示意，不作性能排名。"
  }]
}
```

这里是字段示例，实际页面必须列出所有需要叠加的文字。`title` 在 editable 中是上下文，只有加入 overlays 或 raster_text 才要求可见；不要再用 `bullets/text` 指定可见文字，校验会拒绝以防归属不明。固定符号、无需修改的图标及装饰仍留在整页图中，raster_text 只列出允许生成的文字，不是要求删除所有视觉符号。

`overlays` 非空，按数组顺序从下到上叠放在底图上。每个对象有页内唯一 `id`。坐标 `x/y/w/h` 是相对整页的 0–1 数值，起点在左上；对象必须完整在页面内。输出画布宽 10 英寸（16:9 高 5.625 英寸，4:3 高 7.5 英寸），字号以点计。

- `type: text`：`text` 为准确文案，可含换行；`font` 默认 Microsoft YaHei，`font_size` 默认 20；`color` 为不含 # 的六位十六进制颜色；`bold` 为布尔值；`align` 为 left/center/right；`valign` 为 top/middle/bottom。透明文本框，无自动缩字号，需宿主试排与渲染检查。
- `type: image`：`path` 指向需要独立替换的图片，按 brief 所在目录解析，记录 SHA-256。图片框按指定比例铺满，需自己保持原图比例；图片对象可替换，但不承诺图片内部路径可编辑。只有这类对象才从底图中留空。

图片叠加素材在 claim、compose、complete 和 export 时检查，不能静默换图。刻意替换时用 revise 提供新路径，或移除旧 sha256 后重新计算。需要原生图表等高级对象时走 [宿主扩展](editable-composition.md)，不要把未支持类型填入 schema。

`compose` 生成单页 PPTX 和 `.review.json` 收据；`complete --review-file ... --preview ...` 保留合成稿及已检查预览到项目 `reviews/`，绑定页码、修订、规格与底图。底图继续保存在 `images/`，JSON 状态和 brief 留档不能手动修改来代替 revise。

Paths in `references` resolve relative to the brief file at initialization. Reference paths and SHA-256 values are recorded. If an input changes, update that page deliberately using `revise --page-file` rather than silently regenerating against different evidence.

```json
{
  "title": "研究组周报",
  "language": "Chinese",
  "audience": "导师与同门",
  "ratio": "16:9",
  "backend": "builtin",
  "parallelism": 10,
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

`backend` is `builtin`, `openai`, or `atlascloud`; it is fixed for the project. `ratio` is `16:9` or `4:3`. A brief has 1–500 pages; new briefs default `parallelism` to 10 and accept 1–10. This is a page-worker ceiling, not a promise of host agent capacity. Use `dispatch-plan --host-slots N` to fill available child slots after the sample is accepted; existing databases are not migrated. Pages receive numeric order from the array. Optional `image_options` carries model, size and quality into the request for an API worker. Each reference needs a path and a meaningful role. `context` can also be provided per page.

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
