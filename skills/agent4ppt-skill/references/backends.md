# Image backends

Prefer the host's built-in image tool. Inspect reference files first; pass their paths using the tool's supported reference mechanism. Preserve original generated outputs and record provenance. Never invent a callable image tool or silently replace it with code rendering.

For an explicitly selected API workflow, configure `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, and `AGENT4PPT_MODEL`; alternatively use `config --key-env`. Environment values override `${AGENT4PPT_HOME:-~/.agent4ppt}/config.json`. No keys are bundled. API mode is billed by the chosen provider.

`image job.json` runs one generation or edit request. Relative job image/output paths resolve against the current working directory. Use absolute paths for automated dispatch. Example:

```json
{
  "backend": "openai",
  "prompt": "Create one complete Chinese slide. Preserve the attached chart and use the other reference only for style.",
  "images": ["/absolute/style.png", "/absolute/chart.png"],
  "out": "/absolute/page.png",
  "options": {
    "model": "gpt-image-2",
    "size": "2560x1440",
    "quality": "medium",
    "output_format": "png",
    "n": 1
  },
  "attempts": 1,
  "overwrite": false
}
```

Omit `images` for generation. `mask` supports an alpha PNG matching the first input image in the OpenAI adapter. `prompt_file` reads UTF-8 text; `brief` adds structured art direction without changing the original prompt. `options` carries compatible image API fields, including quality, size, background, output_format, output_compression, moderation and input_fidelity where supported. A model's API capabilities are not inferred from its name beyond the documented GPT Image size/alpha restrictions.

`image job.json --dry-run` validates and displays the request without network calls. Optional `downscale_max_dim` saves a separate `-web.png` copy. Multi-image requests use indexed filenames. Existing outputs require `overwrite`.

`batch jobs.jsonl --concurrency 3 --report report.json` supports generation and editing jobs, preserves input order in its report, rejects output collisions, and records per-job failures. `--fail-fast` cancels not-yet-started tasks; already running requests finish. `attempts` can be 1–5; retries are limited to HTTP 429 and selected 5xx statuses, with bounded backoff. Network timeouts are not automatically resubmitted because the provider may already have charged for a completed request.

OpenAI-compatible mode sends JSON to `/images/generations` and multipart data to `/images/edits` under the configured API base. That base should include `/v1` when required by the provider. Base64 and URL responses are supported; URL downloads do not include API authorization headers.

AtlasCloud mode uses `backend: atlascloud` and an AtlasCloud base URL. It submits `/api/v1/model/generateImage`, polls the returned prediction, and decodes completed outputs. Model operation suffixes are selected for generation/editing. PNG/JPEG and multiple references are supported; masks and WebP are rejected. Polling is bounded. An API adapter passing local contract tests is not proof of live account/model access.

Sources for API contracts:
- https://developers.openai.com/api/reference/resources/images/
- https://www.atlascloud.ai/docs/en/openapi-index
- https://www.atlascloud.ai/en/models/openai/gpt-image-2/edit

## 从页面请求到 API 任务

使用 `image-job --request REQUEST --out CANDIDATE --save JOB` 转换已经领取的页面请求。它保留全部参考图、完整提示词和 options，并检查参考图哈希。接着 `image JOB --dry-run` 查看最终内容；正式 `image JOB` 才会调用服务。最后目视检查并通过 `complete` 登记。不能把 `dry-run` 输出当成生成结果。

需要局部修复时，把当前候选作为第一张输入，写清保持区域与修改区域；需要掩膜时保证它与第一张图等大且带透明通道。使用新输出文件名，验收后再替换页面登记。多参考图时明确证据、样张与待编辑图的顺序。

## 当前 CLI 参数能力

下表描述本版本实现的校验范围，不代表每个服务都支持所有组合。服务可能收紧限制，应以实际服务返回为准。

| 任务字段 | 行为 |
|---|---|
| `prompt` / `prompt_file` | 提示词文本或 UTF-8 文件；单任务 `prompt_file: "-"` 可读取标准输入 |
| `brief` / `augment` | 追加结构化美术方向；`augment: false` 禁用追加，保留原提示词 |
| `options.model` | 单任务模型覆盖默认配置，可使用兼容服务的命名 |
| `options.size` | 默认 2560x1440，支持 auto；GPT Image 2 路径按边长、像素总量和比例校验 |
| `options.quality` | low、medium、high、auto |
| `options.n` | 1–10 个候选，输出自动增加序号；正式页只登记选定候选 |
| `options.output_format` | PNG、JPEG、WebP 对应小写参数；文件扩展名必须匹配 |
| `options.output_compression` | JPEG/WebP 的 0–100 整数，PNG 不使用该参数 |
| `options.background` | auto、opaque、transparent；本版本拒绝 GPT Image 2 的 transparent 请求 |
| `options.input_fidelity` | 兼容旧模型的 low/high；GPT Image 2 请求不发送该字段 |
| `options.moderation` | auto 或 low，服务端仍决定是否支持 |
| `images` | 本地输入图片列表，本地预检上限 16 张、单张 50 MiB；服务限制可能更严格 |
| `mask` | 与第一张输入等大的带 alpha PNG；AtlasCloud 适配器不支持 |
| `out` / `out_dir` | 显式文件优先，否则单任务使用目录下 image 文件；批次自动按输入序号命名 |
| `overwrite` | 明确允许覆盖；默认预检拒绝已有输出 |
| `downscale_max_dim` | 另存缩小 PNG，不改原图；`downscale_suffix` 可改默认 -web 后缀 |
| `attempts` | 1–5 次，只有支持的限流和服务端错误会重试 |

图片尺寸不是画布比例的同义词。当前 GPT Image 2 校验要求边长为 16 的倍数，最长边不超过 3840，比例不超过 3:1，像素数在 655360 到 8294400 之间。4:3 示例可用 2048x1536；高分辨率 16:9 示例为 3840x2160。不要把一个后端的具体参数强行传给只接受自然语言比例要求的内置工具。

## 批次默认值与输出

`batch jobs.jsonl --defaults defaults.json --concurrency 3 --report report.json` 接受每行一个 JSON 对象，也接受 JSON 字符串形式的短提示词。defaults 可包含 `out_dir`、`options` 和 `brief`，单条任务覆盖同名字段。未指定 out 时按输入顺序生成 image-001、image-002 等，扩展名由格式决定。不要让所有任务继承同一个 out，否则冲突检查会拒绝。

批次不能共用标准输入提示词，改用每条文本或独立文件。每条可有不同参考图与掩膜，但项目级后端与生成方式要求仍需在登记阶段满足。批次结果按输入顺序返回，并行完成顺序不影响页序；失败退出码非零，报告区分成功、失败与尚未开始就取消的任务。

## 透明素材与边缘处理

简单不透明对象可以先生成与主体不同色的纯色底，再用 `key` 去底；若要求模型原生透明，需要选择实际支持该能力的模型，不自动更换。输出使用 PNG/WebP，JPEG 没有 alpha。

`key --tolerance` 控制背景范围，`--soft --opaque` 构成过渡区；`--sample corners` 或 `border` 用于估计背景色。`--contract` 内缩边缘，`--feather` 羽化，`--despill` 缓解边缘残色。主体带有同背景颜色、半透明材质或细发丝时，逐项观察处理前后，避免把参数拉大后损伤主体。算法实现的像素行为不能视为与其他工具完全一致。

## 常见错误

缺少密钥时先确认确实在用 API，而不是要求内置工具用户另外配账户；认证失败检查服务匹配；端点不存在检查根地址；模型不支持参数时调整已公开参数并记录。服务提交后超时不盲目重发。颜色、错字或构图问题应调整图片请求，不能靠把错误图标成 complete 来跨过检查。

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/f63cd36b42623c1bad0a -->
