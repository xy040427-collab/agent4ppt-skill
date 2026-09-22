# Command reference

## Import a host-generated image

```sh
A4P import-image --source <exact-tool-output.png> --out <task/page-001-design.png>
# Optionally add --sha256 <expected-tool-output-hash>.
```

校验图片可解码并原样复制，返回 path、source、sha256、尺寸、格式和字节数；拒绝覆盖文件。不自动查找最新图，不修改项目状态，不代替 record-design / record-background / complete。文件与本次调用的关联方法见 [产物交接](backend-choice.md#内置图片产物交接)。

## Full-slide-first editable workflow (new default)

新建纯文本叠加项目自动启用 `native_acceptance: target-v1`。初稿 compose 后须通过 PowerPoint MCP 校准，保存为工作稿，再执行 `compose ... --native-draft adjusted.pptx --out checkpoint.pptx`；complete 使用 checkpoint 的收据。预览必须从 PowerPoint 按目标图像素宽高导出。QA 除原绑定字段和 checks 外，须包含每个 overlay ID 的 `objects[id].placement/typography/content` 观察记录。未实际看图不得填写通过。旧数据库与混合图片叠加扩展保持原兼容行为。

文本字号字段为 `font_size`，传 `size` 会报错，包括同时传两个字段的情况；修正任务 JSON，不要为错误输入修改 runtime。

新建 editable 默认先生成完整成稿，以下命令都使用 claim 返回的页码和有效 token。`measured.json` 是从成稿测量并试排后的 overlays 数组，不是整个 brief。generate/edit 方法文件分别记录真实工具及 mode。

```sh
A4P record-design PROJECT --page 1 --token TOKEN --image design.png --overlays-file measured.json --method-file generate.json --qa "已检查成稿和测量"
# Read returned erase prompt and references; execute the image edit with the host.
A4P record-background PROJECT --page 1 --token TOKEN --image erased.png --method-file edit.json --qa "去字干净，画面保留"
A4P compose PROJECT --page 1 --token TOKEN --image erased.png --out draft.pptx
# Use PowerPoint MCP to adjust draft.pptx against design.png and save adjusted.pptx.
A4P compose PROJECT --page 1 --token TOKEN --image erased.png --native-draft adjusted.pptx --out checkpoint.pptx
# Render checkpoint.pptx at design.png dimensions, inspect both, then write bound QA with per-object observations.
A4P compare-render PROJECT --review-file checkpoint.review.json --preview rendered.png --out comparison-attempt-01
# Open overview and every object panel, fix findings via MCP and repeat with a new checkpoint.
# QA must include absolute comparison_file; see visual-replication.md for genuine measurement false positives.
A4P complete PROJECT --page 1 --token TOKEN --image erased.png --backend builtin --method-file edit.json --review-file checkpoint.review.json --preview rendered.png --qa-report qa.json --qa "实际视觉检查结果" --sample
A4P export PROJECT --out presentation.pptx
```

QA 比原五项增加 erasure_clean、artwork_preserved、design_alignment，并绑定 design_sha256。同一修订下阶段只能登记一次；更换成稿、映射或底图须 revise 后重新 claim。重新 claim 可恢复已登记阶段。旧版预留区域路线须显式 `editable_workflow: reserved`；下面“直接生成无字底图”的描述仅用于该兼容路线。

## Editable whole-page composition

`compare-render PROJECT --review-file checkpoint.review.json --preview rendered.png --out NEW_DIRECTORY` 生成同尺寸全页对照、逐对象四联图（原图/去字底图/PPT 渲染/差异）和文字位置、可见大小、颜色分布诊断，读取实际 PPT 的对象名及格式。新建纯文本项目启用 `visual_comparison: raster-v1`，complete 重新计算并核对报告，未处理告警不能直接通过；旧项目可主动运行诊断但不自动迁移。报告不等于 OCR 或视觉验收，详见 [测量与处理流程](visual-replication.md#measured-render-comparison)。

Use `A4P template --mode editable --out brief.json`, then set the real content and explicit `overlays`. Use the same init/prepare/claim/renew/fail/revise commands. After generating ONE whole-page background with the reserved content omitted:

```text
A4P compose ./deck --page 1 --token TOKEN --image ./background.png --out ./draft.pptx
```

Reopen and render that PPTX with the host, inspect it, then register the ORIGINAL background and reviewed composition:

```text
A4P complete ./deck --page 1 --token TOKEN --image ./background.png --backend builtin --qa "Native labels and complete artwork checked" --review-file ./draft.review.json --preview ./rendered.png --qa-report ./qa.json --method-file ./method.json --sample
A4P export ./deck --out ./presentation.pptx
```

Use a new draft filename for each compose attempt. Compose validates the lease and records an event but leaves the page running. Completion requires its matching revision/spec/background receipt and an actual preview image, retaining hashed copies of the draft and preview. The renderer and visual review are supplied by the host; file checks cannot prove a preview's origin or visual correctness. Edit overlay content/positions via revise, then re-claim and re-compose; reuse the original background when still suitable. Export supports native text and independent pictures, not native charts/tables. Final deck rendering remains required.

新 editable 模板启用 `review_policy: structured-v1`，需要上述 `--qa-report`。报告格式和失败处理见 [editable composition](editable-composition.md#验收)。旧项目未设置此策略时仍兼容旧参数。

需要诊断布局图时，在初始化之前运行 `A4P layout-guide --page-file page.json --out guide.png --ratio 16:9`，将返回的 path 与 role 加入该页 references。该命令还返回原生框交叠问题；它不测量字体，也不检测底图语义遮挡。修改布局后需生成新文件名，避免静默改变已有参考哈希。

The commands below also describe the original full_slide route; full_slide completion needs no composition receipt.

All examples use `A4P` as shorthand for `python <skill>/scripts/agent4ppt.py`, not an installed shell command. After `pip install .` in the repository, the equivalent installed command is `agent4ppt`.

```text
A4P init ./deck --brief ./brief.json
A4P prepare ./deck
A4P claim ./deck --worker agent-1 --page 1 --lease 900
A4P renew ./deck --page 1 --token TOKEN --lease 900
A4P complete ./deck --page 1 --token TOKEN --image ./candidate.png --backend builtin --qa "Text and source figure checked" --sample
A4P status ./deck
A4P history ./deck
A4P fail ./deck --page 2 --token TOKEN --reason "Image service unavailable"
A4P revise ./deck --page 2 --reason "Tighten text" --page-file ./new-page.json
A4P export ./deck --out ./presentation.pptx
```

`claim` returns the exact prompt, reference paths, token, revision and deadline. `complete` checks that the token is still valid, backend matches, inputs have not changed, and the output is an actual image. The QA note records the agent's visual review; it is not an automated OCR guarantee.

`template --out brief.json` creates a starter brief without overwriting existing content. `prepare` saves all page prompts under `plans/` for review; these are not leases or completed work.

For new production, add `--method-file method.json` to `complete`. The file records the actual `tool`, `mode` and optional exposed model/size/quality/input preparation. Using it with `--sample` makes later requests inherit the method; mismatching result declarations are rejected. It records a declaration, not independent proof of a remote tool invocation.

For an API project, preserve every reference when creating the executable job:

```text
A4P image-job --request ./deck/requests/page-001.json --out ./candidate.png --save ./image-job.json
A4P image ./image-job.json --dry-run
A4P image ./image-job.json
```

`image-job` validates reference hashes and carries all images into the edit path. It does not acquire a lease, call a service, or mark the page complete. Built-in requests are rejected by this conversion; execute those through the host image tool.

`export` embeds original PNG/JPEG bytes by default. Other supported Pillow formats are converted to PNG. Optional `--max-image-mb 2` enables lossy compression for size-constrained delivery. Output is staged then atomically replaced. Never enable lossy compression for scientific evidence without considering legibility.

Use `assemble` for existing images without falsely recording a generation history:

```text
A4P assemble --images ./page1.png ./page2.png --notes ./notes.md --ratio 4:3 --out ./slides.pptx
```

The explicit image order determines slide order. It supports PNG, JPEG, GIF, BMP and other Pillow-readable formats. Missing/corrupt input is an error, not a silently missing page. It does not require a project database.

```text
A4P doctor
A4P setup
A4P config --model gpt-image-2 --base-url https://api.openai.com/v1 --key-env MY_IMAGE_KEY
A4P doctor --check-api
A4P styles
A4P styles --name 学术汇报
A4P styles --name 黑金画册 --save ./recipe.json
A4P key ./green.png --out ./transparent.png --color "#00ff00" --soft --opaque 96 --despill
```

`key` supports hard/soft mattes, corners/border key estimation, `--contract`, `--feather`, PNG/WebP output and explicit `--overwrite`. It is for user-authorized asset processing. CLI JSON is UTF-8 on Windows. Nonzero exit codes mean failure; batch partial failure also returns nonzero. Credentials must be configured locally, not pasted into chat.

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/d3022627c09908b45a58 -->
# Adopt adjusted native text

## Fill the page-worker pool

`A4P dispatch-plan PROJECT --host-slots 9 --sample-page 3`

`--host-slots` 是宿主当前空闲的子 agent 槽位，已扣除主 agent、正在运行及无关的任务。命令只读数据库，不领取租约或启动 agent。样张尚未接受时最多建议一页（可用 `--sample-page` 指定正文样张）；样张接受后按待处理页面、项目剩余额度、空闲槽位与上限 10 尽量补满。每次完成后重新计算；实际 `claim` 仍事务性校验额度。失败页先按既有 `revise` 流程恢复。宿主更低的限制不能靠此参数突破。

## Batch native corrections in one host pass

`A4P mcp-batch --spec corrections.json --out batch-plan.json`

输入示例（坐标与字号都是 PowerPoint 点数；对象映射来自当前 MCP 检查）：

```json
{"session_id":"ACTUAL_SESSION","slide_index":1,"objects":{"title":{"shape_index":2,"mixed_runs":false}},"edits":[{"id":"title","position":{"left":28,"top":20},"font_size":34,"color":"#071E49","bold":true}]}
```

命令先校验整批再生成 `preflight` 与 `calls`；不会编辑 PPT，也不是 MCP 服务新增了批量端点。宿主一次编排中先执行全部 preflight，确认返回对象名与 expected_name 一致，再顺序 await 每个修改调用，检查 MCP 内容中的 success/isError，任一失败即停止。共享 PowerPoint 服务只有一个调用队列。完成整页修改后统一 save-copy-as → adopt → render → compare-render；不要每个属性都重新渲染。失败后先重新读取页面状态，此批次不具备事务回滚。

可选修改字段：`position`、`size`、`font_size`、`font_name`、`bold`、`color`、`alignment`。标记 `mixed_runs:true` 的对象仅允许几何调整，局部颜色/字体仍用支持 rich runs 的接口，避免整框覆盖强调。此入口不更改文字内容、底图、收据或 QA 规则。东亚字体仍按视觉还原指南核对。

宿主执行形态示例（`plan` 为已读取的计划）：

```javascript
function checked(result) {
  if (result.isError) throw new Error('MCP transport error');
  const payload = JSON.parse(result.content.find(x => x.type === 'text').text);
  if (payload.success !== true) throw new Error(JSON.stringify(payload));
  return payload;
}
for (const c of plan.preflight) {
  const p = checked(await tools.mcp__powerpoint__shape(c.arguments));
  if (p.name !== c.expected_name) throw new Error('Shape mapping changed; inspect again');
}
for (const c of plan.calls) {
  const result = c.tool === 'shape'
    ? await tools.mcp__powerpoint__shape(c.arguments)
    : await tools.mcp__powerpoint__textframe(c.arguments);
  checked(result);
}
```

## Adopt the reviewed checkpoint

`compose PROJECT --page N --token TOKEN --image background.png --native-draft adjusted.pptx --out checkpoint.pptx`

Adopts a saved single-slide PowerPoint text draft on the original compose canvas. Returns a new review receipt; render this checkpoint and submit its preview/QA through complete. Export retains the reviewed text formatting. See [visual replication](visual-replication.md) for validation boundaries and MCP/CJK handling. Omitting `--native-draft` retains existing compose behavior.
