# 单页执行任务模板

full_slide_first 必须先读 `references/visual-replication.md`：以成稿为视觉目标，在 PowerPoint MCP 中调整同名对象，检查中文 NameFarEast、字号、颜色、换行、边距和正文完整性。保存后用 `compose --native-draft` 登记新检查点，渲染该检查点再对照；协调者亲自复核。仅调整文字外观无需 revise；改变文案、对象归属、成稿或底图仍须 revise。以下“修改映射须 revise”不禁止这条原生外观调整通路。

优先读取 `request.editable_workflow` 和 `stage`。`full_slide_first` 路线：design 阶段生成带全部文案的完整成稿，测量并试排 overlays 后 record-design；读取返回的 erase 请求并附加成稿给编辑工具，仅抹掉可编辑内容；record-background 后 compose、渲染及对照。erase/compose 阶段表示恢复任务，不重复生图。返回成稿、去字底图、映射、预览及收据，QA 增加 design_sha256 和 erasure_clean/artwork_preserved/design_alignment。映射登记后修改须 revise。下文“直接省略 overlays、先预留区域”的指令仅适用于 reserved 兼容路线，不能用于新路线的 design 阶段。

先读取 request.mode、editable_workflow 和 stage。full_slide 与 full_slide_first 的 design 阶段都生成包括文字的完整成稿。仅 reserved 的 background 阶段直接省略 overlays 指定内容；仅 full_slide_first 的 erase 阶段编辑已有成稿去掉指定内容。按 raster_text 保留固定文字，完整插画、普通图标、箭头和圆点不要拆散或删除。支持页面分工时，editable worker 负责该页成稿、去字、原生还原、真实渲染、对照与返修，返回参考成稿、底图、原生草稿、渲染预览及结构化检查结果。协调者独立复核后 complete；压平预览不是可编辑成品，也不能冒充图片模型生成的 full-slide 基准。

适用于宿主已支持且用户范围允许的并行制作。将尖括号内容替换为实际值，不把模板本身当作任务已派发的证据。

```text
制作第 <页码> 页：full_slide 返回完整候选成图；editable 执行该页完整还原闭环。
项目：<项目绝对路径>
请求：<该页请求 JSON 的绝对路径>
任务标识：<实际执行者标识>
页面工作目录：<仅此页可写的绝对目录>
PowerPoint 队列：<协调者管理的共享 endpoint 队列或经核实的独立服务>

先完整读取请求中的 prompt、references、options 和 generation_method。
每张图片先查看再按当前图片工具要求附加。确认哪些是证据图、哪些仅作风格参考。
使用请求规定的后端、工具和生成方式；如果该能力不可调用或素材不可读，报告具体阻塞。
每次生成一张完整页面，包括准确标题和正文。样张用于匹配风格，不复制其主题和内容。
检查中文、数值、裁剪、图例、重叠、素材身份与整体风格。修复后再选择最终候选。
不要用本地排版截图、文字覆盖或程序绘图替代要求的整页图片生成。
不要修改数据库、其他页请求、大纲、讲稿、正式图片目录或成品 PPT。

返回：
- selected_image：工具产生的候选图片绝对路径
- backend：实际后端
- generation_method：实际工具、模式及公开可见的参数
- qa：具体检查结果和仍有的问题
- blocker：有阻塞时说明，不能编造图片路径
```

full_slide 或只委托生图时，父 agent 保留租约凭证并负责 `renew`、`fail`、`complete`。完整 editable 页面 worker 可自行 claim，或接收仅限该页的租约，以便 compose/renew；修改规格必须 revise 后重新 claim，不改数据库。协调者负责 complete。不要把 API key 放进任务描述。

## Editable 页面任务补充

新建纯文本路线须在每次实际渲染后执行 `compare-render`；初次和最终验收查看全页及全部逐对象对照图，中间迭代查看全页、修改对象和告警区域。按报告里的对象名、实际 run 格式和测量偏差通过 MCP 调整。重存检查点、重渲染、重比对后再提交；返回 comparison.json 与每个未解决告警。协调者必须看每页最终全页对照，并针对告警、豁免和细节疑点复核；可复用 worker 的真实逐对象证据，不必重复全部中间轮次。不得把零告警视为自动通过，也不得批量生成误报豁免。详见 visual-replication.md 的 Measured render comparison。

派发时明确该页目录、渲染服务、可用生成次数和实际 worker 名称。full_slide_first 始终以接受的完整成稿为目标，用 MCP 调整已有文字并渲染对照。reserved 兼容任务才先按真实字体试排、检查预留区；若其布局参考图已过时，更新参考后才能重新生图。不能靠持续缩字、删文案或遮盖底图掩饰失败。去字损伤画面时返修底图；预算用尽则返回未解决问题，不能报告通过。

返回 review_file、preview、background、实际查看的对象对照路径、每个对象的 placement/typography/content 观察、各项 checks 和 issues。记录成图、去字、MCP 修正、渲染/复核的开始结束时间和轮次。先看完整页再集中列出该轮所有对象修改，按普通 MCP 接口在一次宿主编排中执行并核对各返回，统一保存、登记和渲染；不假定存在 MCP 原生 batch 接口。共享 PowerPoint endpoint/process 的所有修改、保存、渲染都经协调者串行队列，同一页/session 仅一个写入者；其他页生图、去字、看图继续并行。任务尚在执行时不关闭共享 session 或退出进程。

样张通过后，协调者保持页面 worker 池尽量饱满：新项目 parallelism 默认/最大为 10，实际目标取 10、项目并发、可执行页数和宿主真实子 agent 容量的最小值，计入已运行页后补位。`dispatch-plan PROJECT --host-slots N` 只给出派发建议，不创建 agent；N 必须是真实空闲子 agent 槽数。完成一页即派发下一页，不等待整批结束，不额外启动 QA-only agent 挤占页面池。宿主上限不足 10 时如实使用可用值，不能声称提高了宿主限制。runtime 的 parallelism 只限制活跃租约，也不能证明图片服务端计算并行。

视觉已合格后停止不可感知的字形/抗锯齿微调；缺字、错字、错误换行、重叠、截断和明显位置/字号/颜色问题仍须修复，所有强制比对告警仍须处理。不得靠固定轮数自动通过，也不能省略最后逐对象检查。

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/356a32e5f9c17398c65a -->
