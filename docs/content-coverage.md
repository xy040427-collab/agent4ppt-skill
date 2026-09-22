# 内容保留与实现对应

## 成稿优先转换修订

新 editable 默认 full_slide_first；旧项目缺少 workflow 字段仍按 reserved 执行，full_slide 不变。plan.py 将完整文案编入 design 请求，conversion.py 将成稿及选定对象编入实际 erase 请求。record-design 保存成稿与测量映射，record-background 保存去字底图并绑定成稿哈希；project.py 的 compose/complete/export 验证阶段与修订。CLI、模板、SKILL、page-worker、brief、commands 和 editable-composition 均描述相同路线。新增测试覆盖跳步、错误底图、旧 token、修订失效、租约恢复、QA 缺项和成稿样张继承。

保留原有对象归属、固定文字、普通图标、独立图片、原生图表宿主扩展、样张、租约、并发、备注、保真边界及诊断布局图。布局图和预留区域规则仅改变默认适用路线，没有删除。生成字体识别、坐标测量、真实图片编辑、PowerPoint 渲染和视觉判断仍由宿主执行；新增阶段不等于自动 OCR 或像素级无损转换。

## 整页底图叠加修订

当前 editable 主流程已接入 mode、overlays/raster_text、SQLite 页面队列、compose 收据、合成预览登记与 layered export。仍每页生成一张完整图，仅排除指定原生内容；plan.py 的内容边界实际进入 claim/prepare/image-job，而非只写在 Markdown。旧 brief 默认为 full_slide。

| 原有决策、示例或约束 | 当前保留位置与变化 |
|---|---|
| 整体设计、字体试排、留白与避免遮盖 | editable-composition.md 保留，新增完整底图优先与圆点/编号示例 |
| 独立图标和素材分工 | 仅在选定可替换对象时采用；默认按页分工，不拆散场景 |
| 对象 ID、局部修改和未变素材保留 | composition.py 原生命名；revise 可复用底图并重新合成；独立读取和修改测试 |
| 图表工作簿、连接线、矢量声明与桌面验收 | 原指导完整保留在宿主扩展；未声称 bundled CLI 支持这些对象 |
| 原页面状态、并发、失败恢复 | project.py 共用原队列；compose 在 running 中记录证据，不新增素材调度体系 |
| 原图片输出和备注 | full_slide/assemble 行为保留；editable 在同一底图之后写入原生对象 |
| 完成证据与完整性 | complete 验证合成收据和预览，export 复查接受的文件与素材；视觉正确性仍由宿主判断 |

后文“未新增可编辑脚本”等表述是此前试验记录，不代表本次工作版本的能力。

本次修订针对早期精简版丢失细节的问题。保留的是可用内容、操作能力和约束，不要求沿用旧文件组织、命令名字或存储格式。本文是维护清单，不是全题材效果相同的证明。

可编辑图文试验：新增 `references/editable-composition.md` 和入口分流。保留原有风格与整页生成能力，不新增运行脚本或依赖。宿主试验完成三页原生文字与时间线、背景素材生成、导出后修改及重新渲染；不是 bundled CLI 新增了可编辑导出，也不是全题材视觉等价证明。

## 工作流资源

| 内容类别 | 当前文件 | 保留的具体内容 |
|---|---|---|
| 入口与阶段推进 | SKILL.md、references/workflow.md | 材料、大纲、风格、样张、正式生成、检查与交付；草稿、决策记录和进度证据 |
| 图片后端选择 | references/backend-choice.md | 实际可调用能力检查、内置工具优先、API 适用条件、后端一致与失败处理 |
| API 使用 | references/backends.md | 生成、编辑、输入图、掩膜、参数、尺寸、透明处理、批次、重试、排错 |
| 环境配置 | references/configuration.md | 独立环境、配置位置、环境覆盖、服务根地址、密钥与诊断边界 |
| 大纲和样张 | references/planning.md | 页面角色、真实文案、素材映射、已有风格提取、代表内容页、样张复用和修订 |
| 制作与执行者 | references/production.md | 自包含上下文、完整请求、样张方法、并发、父子职责、过期租约与阻塞 |
| 单页指令 | prompts/page-worker.md | 请求路径、输入职责、指定工具、候选检查、返回结果与共享文件边界 |
| 用户素材 | references/assets.md | 证据与风格分离、真实附图、哈希、保真要求、修图、透明边缘与迁移 |
| 备注和组装 | references/notes-and-delivery.md | 讲述风格、长度、视觉走读、页码映射、逐页 QA、两条导出路径与交付证据 |
| 个人风格库 | references/style-library.md | 实际渲染后提取、完整字段、去除项目内容、外置存储、同名规则和自动发现 |

专项说明均可从 SKILL.md 找到；不是把文档加进压缩包后让 agent 无从发现。重复的共享原则集中维护，题材特有的规则留在独立风格资源。

## 十二种完整风格

每种均含用途、画布、密度、配色及语义、字体层级、页面变体、候选布局、图像处理、允许/避免元素、生成约束和检查点。JSON 用于 CLI，Markdown 用于 agent 选择与调整。

| 风格 | 重点保留的区别 | 资源 ID |
|---|---|---|
| 清爽专业 | 明亮蓝绿、进展复盘、机制、里程碑、证据与风险 | professional |
| 创意杂志 | 不对称、字号反差、裁切、编辑网格与视觉张力 | editorial |
| 墨水阅读 | 纸墨主题、衬线标题、元信息、重点页与安静页交替 | ink |
| 数据分析 | 明亮仪表盘、KPI、趋势、构成、状态与数据口径 | dashboard |
| 学术汇报 | 中高密度、真实图表、任务分解、平台、风险与成果考核 | research |
| 复古插画 | 统一轮廓、有限平涂、纸感、连续场景和对象标注 | retro |
| 白板讨论 | 马克笔、讨论路径、圈注、便签与待定事项 | whiteboard |
| 技术手绘 | 小而精确的中心图、细线、淡色、无白板杂物 | technical-sketch |
| 温暖手作 | 纸片、柔和色、触感与人本故事 | handmade |
| 咨询简报 | 标题设计、单一商业隐喻、分析主结构、矩阵与执行路线 | consulting |
| 公共事务 | 正式红色身份、可变标题、政策与工作证据、真实标识 | public |
| 教学演示 | 多学科材料、概念、比较、案例、练习及学习收束 | teaching |

不能仅凭同为十二种就判定内容等价；本次逐种恢复的依据是这些视觉决策。具体色值与措辞已重新设计，布局数量按实际用途扩展，而不是保留少量缩略标签。

## 源码能力对应

新增 editable 版式验收：`layout.py` 从原生对象导出预留区和诊断图，`layout-guide` 提供 CLI 入口，`plan.py` 将安全区及边界规则传入实际请求。`structured-v1` 通过 `complete --qa-report` 绑定修订、规格、底图、草稿、预览与结构化视觉判断，并在导出时核对归档报告。它不做底图语义分割，也不自动证明视觉正确。页面 worker 模板已覆盖生图、合成、宿主渲染和返修，协调者独立验收。真实生图案例与单元测试结果分别记录在工作目录，不打包试验成品。

| 能力 | 当前实现 | 验证方式 |
|---|---|---|
| 需求校验与提示词准备 | plan.py、planning.py、template / prepare | 示例可初始化；完整风格与结构化字段进入请求 |
| 全局和局部背景、准确文字、布局结构 | plan.py | 对象序列化与字段传递测试 |
| 结构化及 Markdown 素材 | plan.reference、image-job | 路径、角色、哈希和全部附图传递测试 |
| 已认可样张复用 | complete --sample | 样张加入后续请求；无需额外增加页面 |
| 样张生成方式约束 | project.py、--method-file | 方法继承、缺失和不匹配拒绝测试 |
| 任务状态、派发、结果、阻塞 | project.py、cli.py | 并发唯一领取、限额、失败、续租、修订与陈旧结果拒绝 |
| 配置及共享环境 | runtime.py | 配置和诊断测试；不要求真实 API 凭据 |
| 单图、多候选、图片编辑与掩膜 | imaging.py、providers.py | 参数测试和本地 HTTP 文件闭环 |
| OpenAI 兼容及异步图片协议 | providers.py | 本地请求、轮询、失败和超时测试；在线账户未验证 |
| 批量默认值、短提示词与输出目录 | normalize_batch、batch | 多任务预检、参数覆盖和输出不冲突 |
| 标准输入、结构化提示词增强 | prepare | 支持 prompt_file 为 -，augment 可关闭 |
| 缩小副本与多图命名 | imaging.py | 输出原图与真实缩小 PNG；自定义后缀 |
| 色键、软边、估色、内缩与去色溢出 | chroma | 保留能力入口；精细边缘效果仍需更多样本，不声称逐像素等价 |
| PPTX、页序、比例、备注、压缩 | package.py | 独立读取与图片字节验证，已有导出回归 |
| 安装资源及排除中间文件 | pyproject.toml、.clawhubignore、发布脚本 | 检查安装后的风格可查询，发布包排除数据库与缓存 |

## 有意保留的接口差异

- 一组旧命令的职责由统一 CLI 承担，不提供只为保持名字而存在的空壳。
- SQLite 管理任务，JSON 是请求或快照；不能手动编辑 JSON 来标记完成。
- 风格以完整 JSON 配方保存并配有指南；个人库仍在安装目录之外。
- 图片名含页码、修订和哈希，导出从数据库取顺序，不依赖扫描固定名称。
- 预览图统一保存 PNG；原图仍保留，不保证所有工具的缩图编码策略一致。
- 用户已授权直接成品时不重复确认；并行依宿主能力和授权决定，不将无法创建子执行者自动视为失败。

这些差异应在比较时公开，不能把“覆盖同一用途”说成“所有细节完全一样”。本次不恢复原封不动的源码或说明，不靠重复文字、空文件或示例大图增加包体积。

## 仍需扩展的实测

第二轮可编辑试验完成日程图标替换、长标题与多行说明修改，以及原生图表图例位置调整；实验数值和原始内嵌工作簿保持一致。发现宿主再次导出会丢失工作簿关联、SVG兼容图片及部分对象描述，试验中分别恢复原工作簿、使用透明PNG图标并核对几何位置。只将资源选择与验收原则写入指导，没有向skill新增修复脚本或依赖。桌面PowerPoint/WPS、复杂前后景穿插及各风格的视觉等价仍未验证。

后续根据用户PowerPoint截图复现折线偏移，将两条自动连接线换为明确路径的原生折线。两份样张已使用本机PowerPoint 16.0打开并导出检查，其他文件部件保持原始字节；这补充了该样张的桌面验证，不代表WPS或其他页面都已通过。修复后的折线不自动跟随节点。修复工具保留在实验目录，skill只补充目标软件核对与折线选择说明。

进一步将两路输入按可见内容居中对齐，先汇合再由短箭头指向RRF融合，已用PowerPoint重新导出核对。仅调整相关文字位置与连线路径，其他对象及数据保持一致。

十二种配方均测试了从文件到请求的完整传递；视觉输出本轮只实际检查学术汇报验证页。其他风格需要分别用相应题材生成并观察，不能以文字检查代替。真实 API、极端密度、精密科学图和复杂透明素材也需要专项样本。
# 原生还原能力补充

加载与执行修订：根 AGENTS.md 明确仓库制作入口；skill 的发现描述和 agents/openai.yaml 指向完整成稿、模型去字、MCP 还原与视觉对照。worker 模板将旧预留区指令限定到 reserved，保留历史能力但禁止新任务擅自降级。生成及恢复请求返回安装位置下可直接读取的绝对指南路径。complete 拒绝与底图同尺寸同像素的假预览，包含重新编码的副本；该检查不声称能识别任意伪造预览，也不替代主 agent 视觉验收。

- `references/visual-replication.md` 保留目标图测量、图片模型去字、MCP 原位编辑、逐次渲染对照和协调者验收；SKILL、page-worker 和实际请求 `native_review` 均指向此闭环。
- `scripts/powerpoint-fonts.ps1` 补足部分 MCP 的 NameFarEast/边距接口缺口，仅处理指定文件和指定对象，不包含试验主题或字体资产。
- `compose --native-draft`、`native.py` 和 exporter 保留已调整文本，校验原底图、画布、对象 ID/内容与显式字体格式；仍以原租约、修订、收据和 QA 约束完成。复杂图表/可替换图片的原有指导未删除，不声称新入口支持它们。
内置图片产物交接：`references/backend-choice.md` 说明自动保存文件与具体工具调用的关联；`import-image` 只校验和原样复制明确指定的图片，拒绝覆盖，不改变状态机。`tests/test_ingest.py` 覆盖字节一致、错误哈希、坏文件、缺失文件与已有目标保护；不宣称完成真实生图或视觉 QA。
目标图还原验收：新建纯文字 full-slide-first 项目在 create 冻结 `native_acceptance: target-v1`；claim 下发该字段，complete 拒绝初稿、非同尺寸预览和缺少逐对象观察的 QA，export 复核 native 标记。`test_conversion.py` 覆盖字号错名、初稿拒绝、预览尺寸、对象观察、旧数据库兼容。正文样页、分散文字分对象与实际逐页视觉比较由 SKILL/visual-replication 指导；不把脚本校验当作视觉真实性证明。
# Raster comparison coverage

生产效率：新 brief/template 的页面并发默认与最大值均为 10。`Project.dispatch_plan` / CLI `dispatch-plan` 根据当前空闲子 agent 槽位、已在执行的租约、可领页面和样张状态给出补位计划；只读建议，不冒充 agent 启动器。生成与去字请求携带 `execution` 指引，恢复阶段仍可发现同一执行规范。既有租约、修订、图像生成与验收路径保留。`mcp_batch.py` / `mcp-batch` 校验整页原生修改计划，分离全量名称预检与顺序调用，保护混合样式文本；宿主执行后仍经原有保存、adopt、实际渲染和 compare-render。SKILL、production、visual-replication 与 worker 模板统一说明页面池补位、共享 PowerPoint 串行、初次/最终完整检查和停止无意义微调。测试覆盖调度容量、过期/失败状态、只读性和整批非法输入拒绝；不把这些测试称为真实 10-agent 并行生图测速。

`scripts/agent4ppt/comparison.py` implements receipt-bound target/background/render diagnostics, native object/run extraction, four-panel region images and current-artifact remeasurement. `compare-render` is exposed through the CLI; new text-only projects require its report and archive it during completion. Claim, erase, composition responses and the worker prompt expose the policy. `references/visual-replication.md` documents thresholds, false-positive handling and the MCP adjustment loop, including the lack of OCR/font inference. Tests cover controlled position, size, color, missing text, palette loss and contamination, plus rejection of missing reports/unaddressed findings and archived report tampering. These are synthetic checks, not evidence of a live Luna production run.
