# 页面执行、并行与恢复

新 editable 项目默认 full_slide_first：claim(design) → 完整成稿 → 测量 overlays → record-design → 编辑请求(erase) → record-background → compose → 渲染对照 → complete → export。stage 与实际 artifact 均记录在 runtime；重新 claim 按已登记阶段恢复。后文直接生成留白底图的说明仅适用于 editable_workflow=reserved。完整步骤见 [可编辑流程](editable-composition.md)。

本文件的队列、租约、并发和恢复机制适用于两种模式。`full_slide` 的候选是完整成品图片；`editable` 的候选是一张只排除指定叠加内容的完整底图，先 compose 并渲染检查合成页，再 complete。准确文字和位置在 overlays，固定文字在 raster_text；后文的 bullets/text 写法仅用于 full_slide。协调者负责叠加与整页验收，不把每个标签拆成生图任务。具体命令见 [可编辑流程](editable-composition.md)。

## 完整请求而不是一句任务

`claim` 生成的请求应该让另一位执行者只读这份文件就能制作该页。全局 `context` 写源材料摘要、核心问题、统一术语、比较对象和明确列表；页面 `context` 补充这一页需要的定义、实验口径、前置结论。避免只写“前述框架”“这六项”，应展开具体内容。

`layout` 可以是对象，包含角色、意图、内容区、阅读顺序、与前页关系和间距；`visual_elements` 写主图及辅助标注；`text` 放必须准确呈现的其他文字。`plan.py` 会序列化这些信息，连同完整风格配方进入请求。表格或图表没有真实数据时，不能让模型替作者补数值。

## 样张方法记录

`complete --method-file method.json --sample` 将实际生成方式记入事件，并让后续请求继承。示例：

```json
{
  "backend": "builtin",
  "tool": "image_gen",
  "mode": "edit",
  "input_preparation": "Viewed local references and attached their paths",
  "prompt_source": "requests/page-002.json"
}
```

只填当前真实工具名称。`model`、`size`、`quality` 仅在实际暴露且需要固定时记录。后续完成时提供自己的方法文件；系统检查固定字段。提示词来源可以因页面而不同，不应把样张文件路径伪装为每页实际请求来源。

不带方法文件的旧项目仍能运行，以保留接口兼容；新制作流程应主动填写。数据库检查标签一致不等于验证真实网络调用，因此保留工具返回的原图和调用结果仍然必要。

## 顺序执行

读取 `status`，领取一个 pending 页面，查看请求和参考图，调用所选后端并检查候选图。可接受时 `complete`；需用户决策或工具缺失时 `fail --reason`；需要更多时间用 `renew`。默认租约 900 秒，长生成任务在到期前续租。

图片尚在生成但凭证到期时不能强行提交。重新领取前确认旧任务状态，避免重复计费；必要时保留已生成候选，取得有效新凭证并在上下文、素材未改变的前提下重新审核候选，不伪造第二次生成。

## 并行执行

先完成并验收一张有正文和多个文字区域的代表性样页，再扩大生产。宿主支持页面子 agent 时，一位执行者负责一页；full_slide 执行者交付候选成图，editable 执行者负责该页成稿、图片模型去字、MCP 原生还原、渲染、对照与返修。父 agent 负责总大纲、素材映射、风格和最终接收。使用 [执行指令模板](../prompts/page-worker.md) 传递绝对请求路径、页码和边界。

新 brief 的 `parallelism` 默认 10、最大 10。尽可能用满本项目所需的页面并发，目标为 `min(10, 项目 parallelism, 可执行页面数, 宿主实际可用子 agent 容量)`；扣除已在执行的页面与已占用槽位后补位，不重复创建整池。只有 3 页待做时不启动 10 人；宿主仅容许 3 个子 agent 时就用 3 个，不能把项目设置称为已提高平台上限。父 agent 若也占平台总槽位，应先扣除。没有子 agent 能力时继续串行并如实说明。

运行 `dispatch-plan PROJECT --host-slots N` 获取只读派发建议，N 使用宿主当前真实空闲子 agent 槽数。该命令结合现有租约与可领取页面提供数量及页码，不会领取任务、启动 agent 或修改宿主配置。样张未通过时只执行样张；通过后按建议派发，每完成一页就立即补下一页，不等待整个批次完成。不另外开 QA-only agent 占用可用于页面生产的槽位。

先确认可用执行槽，再领取任务并启动工作；启动失败及时登记失败，不留一个实际上没有执行者的 running 任务。worker 名称记录实际执行者标识，不能编造调度成功。

父 agent 要检查子执行者是否真的能使用相同图片后端和读取图片。一个看不到参考图的执行者，不能仅凭文件名完成证据页。每页使用独立工作目录、草稿和 session，且同一页只有一个写入者。子执行者不得改共享 brief、notes 或最终 PPTX；完成候选后由父 agent 二次检查并登记。

共享 PowerPoint MCP endpoint/process 的修改、保存和渲染全部进入协调者的串行队列，不能仅凭 session ID 不同就并发调用。页面 worker 将该轮所有对象修正交给同一队列，按普通 MCP 接口逐项执行并检查返回，整轮完成后统一保存、登记新检查点和渲染一次；这属于宿主编排，不声称 MCP 原生有 batch 接口。生图、去字、测量和互不影响的看图可继续并行。任何页面仍在执行时，不关闭共享 session，不调用退出 PowerPoint 的操作。

每页初次和最终验收仍须查看所有对象对照图并留下真实逐对象记录；中间迭代重点检查发生变化的区域和告警，同时查看全页是否受影响。父 agent 看每页最终全页对照，复用 worker 的实际对象证据，针对告警、豁免、小字疑点和风格偏差细查，不重复每一次已合格的中间过程。缺字、错误换行、重叠、截断、明显位置/字号/颜色错误必须修；视觉已合格后不为不可感知的笔画或抗锯齿差异反复改稿。所有既有 complete/export 门槛保持，不因提速跳过报告或把真实差异写成误报。

数据库并发上限只限制已领取页面；它不会生成 agent，也不会限制平台外部的其他图片任务。`batch --concurrency` 是 HTTP 批次的并发上限，两者是不同层次。

## 页面状态

```text
pending --claim--> running --complete--> complete
                         \--fail------> failed
failed / complete / running --revise--> pending（新修订）
running 租约过期 --下次 claim 回收--> pending
```

修订会取消旧凭证，保留历史图片。不要删除旧图来模拟覆盖，也不要直接把 failed 改为 complete。`history` 查看事件；`status.json` 只是执行部分命令时更新的快照，需要最新状态时运行 `status`。

## 导出前的统一检查

确认所有计划页已接收；看首尾衔接、术语、单位、配色和重复布局；核对样张是否作为原定页面复用而非额外插入。后端不同、缺图或更改过的图片应先处理，不能通过绕开项目导出检查来隐瞒问题。`assemble` 用于明确的既有图片组装，不替代未完成项目的验收。

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/754da09e3af2e7d32480 -->
