# Agent4PPT

**先完整成图，再图片模型去字，通过 PowerPoint MCP 还原可编辑文字并渲染对照。**

## 新版流程实测展示

《电子信息类专业》：完整 **10 页双模式**，左侧是 full-slide 原始成图，右侧是带原生文字的 PowerPoint 实际渲染。本次复用已交付的新流程成品更新展示，没有重新生图，也没有修饰预览来隐藏差异。

| Full-slide 原图 | Editable 实际渲染 |
|---|---|
| ![整页成图](assets/full-slide-first/full-slide-image-01.png) | ![可编辑页面](assets/full-slide-first/editable-mode-01.png) |
| ![芯片方向原图](assets/full-slide-first/full-slide-image-05.png) | ![芯片方向可编辑版](assets/full-slide-first/editable-mode-05.png) |

[下载整页图片版](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-full-slide-first-v2/electronics-full-slide-image.pptx) · [下载可编辑版](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-full-slide-first-v2/electronics-editable-mode.pptx) · [查看全部 10 页对比](showcase-current.md)

两份文件均为 10 页，附 10 页备注；可编辑版包含 **90 个原生文字对象**。对象数量证明可编辑结构，不代表像素级一致；插画与固定文字仍在底图中，字形、换行与细节可能存在差异。此处不把实测样例表述为无人干预的一次生成保证。

[历史 30 页画廊](showcase.md)与旧展示站继续保留，并与当前流程的实测证据分开标注。

## 工作流程与使用

制作效率：新 brief 的页面并发默认及最大为 **10**。先验收一张复杂正文样页，再尽量用满 `min(10, 项目并发, 可执行页面数, 宿主实际子 agent 容量)` 的页面 worker 池，完成一页立即补位；每位 editable worker 负责完整的成图→图片模型去字→MCP 还原→渲染对照闭环。`dispatch-plan PROJECT --host-slots N` 读取当前队列，给出可派页码及数量，不创建 agent、不改变宿主平台限制。共享 PowerPoint endpoint 的修改、保存、渲染串行执行，其余图片工作并行；每页集中修改后统一渲染，保留初次和最终逐对象检查与所有验收门槛。主 agent 看每页最终对照，复用真实 worker 记录并重点复核异常；视觉合格后不再反复打磨不可感知的字形差异。详见 [页面调度](../skills/agent4ppt-skill/references/production.md)及 [还原与验收](../skills/agent4ppt-skill/references/visual-replication.md#efficient-correction-and-review)。

可编辑文字对照新增 `compare-render`：读取同一页的原图、去字底图、真实 PPT 渲染图，输出全页对照与逐文字区域四联图；报告绑定原生对象名称和当前字体/字号/颜色，测量位置、可见宽高、前景量和颜色分布差异。新建纯文本项目在 complete 时重新计算报告，拦截缺失、过期报告及未处理告警；真正的测量误报须逐项写明原因与视觉依据，不能用通用“通过”跳过。原图字体识别、OCR 和真实观感仍由 agent 检查，本次不是自动保证视觉一致。去字依然由图片模型完成，诊断裁剪不参与生成底图。旧数据库与 full-slide 路线不自动变更。使用方法见 [视觉比对](../skills/agent4ppt-skill/references/visual-replication.md#measured-render-comparison)。

可编辑模式的新默认路线：先生成带完整文案的 full-slide 成稿，再测量所选原生对象，局部去掉对应内容，最后原位叠加可编辑文字/图片。`record-design → record-background → compose → 渲染对照 → complete → export` 共用原有租约和版本流程。旧项目保持兼容；新建时可显式设置 `editable_workflow: reserved` 选择旧预留区域路线。见 [详细流程](../skills/agent4ppt-skill/references/editable-composition.md)。

面向 AI agent 的图像式 PPT 制作工具：从资料和参考图出发，生成完整页面，记录逐页任务与版本，写入演讲备注并导出 PowerPoint。

**当前工作版本新增整页底图＋原生叠加流程。** `mode: full_slide`（默认）继续导出整张图片；`mode: editable` 共用 SQLite、领取、租约、修订和导出流程，每页仍生成一张完整底图，只把选定内容留给原生文字或可替换图片。通过 `compose` 生成单页合成稿，宿主渲染检查后带 `--review-file` 和 `--preview` 登记完成。原生图表、表格等高级内容仍依赖宿主扩展，未接入 CLI 合成验收。详见[可编辑图文指导](../skills/agent4ppt-skill/references/editable-composition.md)和 [brief 字段](../skills/agent4ppt-skill/references/brief.md)。历史样例与当前代码验证范围分开记录在 [验证报告](verification.md)，不把本地模拟测试理解为所有在线服务均已通过实测。

## 使用

把 `skills/agent4ppt-skill` 文件夹放入 agent 的技能目录，或让 agent 读取其中的 `SKILL.md`。例如：

> 使用 agent4ppt-skill，把这些实验结果做成 8 页组会 PPT。保留原始图表，直接给我成品。

整个 skill 可复制使用；具体制作仍需要宿主提供相应的模型和工具。下面是可选的图像页 CLI：Python 3.10+，唯一运行依赖是 Pillow。可使用现有 Python，或执行：

```sh
python skills/agent4ppt-skill/scripts/agent4ppt.py setup
python skills/agent4ppt-skill/scripts/agent4ppt.py doctor
```

需要独立 CLI 时，在仓库根目录执行 `pip install .`，随后使用 `agent4ppt --help`。没有自动安装到用户的全局技能目录，也不会自动访问账户或发布 GitHub 仓库。

## 能力

- 内置图像工具优先；支持参考图编辑、统一风格、逐页检查和修复。
- OpenAI 兼容 API、AtlasCloud 异步任务；生成、编辑、批量执行、受控重试。
- SQLite 事务队列、任务租约、并发上限、失败恢复、修订记录和输入校验。
- 直接写入 PPTX 文件结构，保留图片质量，支持 16:9 / 4:3 和中英文演讲备注。
- 十二种视觉方案与安装目录之外的个人风格库。
- 每种风格包含完整机器配方与独立使用指南，按名称初始化时冻结配方，并传入后续页面请求。
- 支持结构化内容、Markdown 素材引用、样张方法记录及带图片的 API 任务转换。
- 图片压缩、预览缩小副本、可选色键透明处理。

命令、项目格式与后端说明均在 [skill 入口](../skills/agent4ppt-skill/SKILL.md) 中索引。新的接口和项目格式不兼容旧脚本名称；已有页面可通过 `assemble` 显式导入。

## 开发验证

```sh
python -m pip install Pillow python-pptx
python -m unittest discover -s tests -v
```

`python-pptx` 仅作为测试中的独立读取器，不是运行时导出依赖。测试覆盖本地协议、文件结果和任务状态；视觉质量需要真实图像生成并人工/agent 目视检查。

Pillow 和测试依赖 python-pptx 为外部依赖，未随仓库打包，各自适用其自身许可。

## 内容维护原则

更新以内容与能力覆盖为依据，不以压缩包大小或源码行数为目标。风格、工作流和边界说明可以重新组织，不能因为暂未在样例中用到就删除。详细覆盖记录见 [内容保留说明](content-coverage.md)。

## 权利与来源标识

本项目目前采用[个人非商业使用许可](../LICENSE)，署名为 Jiajun Li，允许个人非商业使用原版；修改和二次开发工具、再分发、机构部署及商业使用须经本人书面授权并留存证明；不是开放源代码许可。源码含非执行的来源注释，无联网追踪。[上游及第三方许可](../THIRD_PARTY_NOTICES.md)单独保留，不受本项目限制覆盖。详见[身份记录](../AUTHORS.md)及[发布与追溯说明](rights-and-provenance.md)。

## GitHub 展示与下载

[查看十种场景、共三十页预览](showcase.md#all-slides)，或在 [GitHub Release](https://github.com/xy040427-collab/agent4ppt-skill/releases/tag/showcase-v1) 下载十份可编辑 PPTX。每份为三页选页展示。图片通过公开展示网站加载，PPTX 作为 Release 附件，不增加 skill 安装目录体积。

## 一条命令安装到 Codex

在目标项目目录运行（需要 Node.js/npm 和 Git）：

```sh
npx skills add xy040427-collab/agent4ppt-skill --skill agent4ppt-skill --agent codex
```

2026-09-10 已在 Windows 独立目录验证公开仓库发现和安装成功；这不等同于新环境完整生图验证。宿主仍需提供生图、PPTX 制作和渲染能力。
# 目标图驱动的可编辑还原

使用本项目制作时，先读取 `skills/agent4ppt-skill/SKILL.md`。新 editable 任务必须按完整成稿、图片模型去字、PowerPoint MCP 还原文字、渲染对照的顺序执行。两模式对比使用同一批生成的完整成稿，不能把 editable 截图称为 full-slide 生图基准。旧 reserved 仅用于恢复历史任务或用户明确指定的旧流程，不能因工具失败自动切换。complete 现在会拒绝与底图同尺寸同像素的预览；真正的视觉验收仍由主 agent 负责。

新的 editable 制作以完整成稿为视觉目标，沿用图片模型定向去字，再通过 PowerPoint MCP 调整原生文字并渲染对照。中文须核对 Latin/NameFarEast 字体，不能只设置 Font.Name。

新增 `compose PROJECT --page N --token TOKEN --image background.png --native-draft adjusted.pptx --out checkpoint.pptx`：登记在 PowerPoint 中调好的单页文本稿。使用返回的新收据完成验收；最终 export 保留其实际文字格式和位置。当前限原 compose 尺寸、一张未改底图和相同 ID/内容的文本框，不支持任意外部 PPT 无损导入。每次改动都须登记新检查点、重新渲染，最终整套文件仍需视觉检查。

详见 [还原操作流程](../skills/agent4ppt-skill/references/visual-replication.md)。主 agent 对照目标图验收属于正常生产步骤，不依赖用户发现问题后再修。
# 内置图片文件交接补充

新建 full-slide-first 纯文字还原项目增加 `target-v1` 验收：必须提交原生校准稿、与目标图同像素尺寸的渲染、逐对象位置/样式/内容观察记录。初稿不能直接 complete；export 复核原生稿标记。旧数据库不自动迁移；混合图片叠加仍走已有兼容路径。`size` 不是文字字号字段，须改为 `font_size`。这些限制验证材料与顺序，不能证明 MCP 操作或视觉质量；每页仍需主 agent 对照看图，先验证复杂正文样页再展开。

内置生图返回 data URL 时，先检查该次调用自动保存的本地图片，不要通过终端传输大段 Base64。使用 `python skills/agent4ppt-skill/scripts/agent4ppt.py import-image --source <本次输出路径> --out <任务图片路径>` 校验并复制，再按原流程登记成稿或去字图。该命令不改变 runtime 状态，也不替代视觉 QA。详见 [图片产物交接](../skills/agent4ppt-skill/references/backend-choice.md#内置图片产物交接)。
