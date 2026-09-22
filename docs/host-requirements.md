# Host requirements

Installing the skill does not install an image model or grant model access.

Editable composition needs authorized input-file access, an image-generation tool, and a way to reopen and render the exported deck. The bundled CLI writes one whole-page background plus native text and independent pictures, using the shared page queue and composition review. Advanced native charts/tables require the host's authoring tools; charts also need real data and intact workbook references. This advanced extension is not yet part of the CLI composition receipt path.

The showcase used host-provided image generation, a host-provided presentation library, and PowerPoint 16.0. These host products are not redistributed. A clean-environment end-to-end portability claim is not established.

The entry point is `skills/agent4ppt-skill/SKILL.md`. Keep its reference files together. Use it for image-led presentations, full-slide-image exports and coordinated artwork with editable text. Do not treat it as pixel-perfect reconstruction of arbitrary slide files.

If your host lacks required capabilities, report them before proceeding. Never fake image generation or silently replace requested native charts with screenshots. No GitHub token, automated star or unrelated telemetry is required.
# PowerPoint 原生还原补充

full-slide-first editable 的宿主应执行 [目标图还原闭环](../skills/agent4ppt-skill/references/visual-replication.md)。Windows 桌面 PowerPoint MCP 负责修改原生对象和导出实际预览；若桥接器缺少 East Asian 字体或边距接口，使用随 skill 提供的 powerpoint-fonts.ps1，仅定位明确指定的打开文件和对象。该助手依赖 Windows PowerShell 5.1，不应在非 Windows 宿主上伪称成功。其他宿主保留原生制作能力，但必须明确实际渲染器及未验证的兼容性。
