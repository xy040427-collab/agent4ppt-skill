> 新版英文入口已更新可编辑模式与 30 页样例验证；以下保留 CLI 使用说明。现允许个人非商业使用；工具二次开发、再分发、机构部署和商业使用须另获本人书面授权。

# agent4ppt-skill

面向 AI agent 的图像式 PPT 制作工具：从资料和参考图出发，生成完整页面，记录逐页任务与版本，写入演讲备注并导出 PowerPoint。

**CLI 当前为 0.2.0 验证版本。** CLI 导出页面为整张图片，文字不能单独编辑。skill 另有[可编辑图文试验指导](../skills/agent4ppt-skill/references/editable-composition.md)，由 agent 使用宿主现有工具执行，不增加安装依赖；已试做三种页面，尚不代表全部视觉能力等价。实现覆盖与实际验证范围见 [验证报告](verification.md)，不能把本地模拟测试理解为所有在线服务均已通过实测。

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
