---
name: agent4ppt-skill
description: Create visually coherent, image-led PowerPoint presentations from notes, papers, reports or outlines. Supports full-slide imagery and an experimental workflow combining generated artwork with editable text, numbers, formulas, charts and diagrams; requires host image-generation, PPTX-authoring and rendering tools.
---

# Agent4PPT

Deliver a presentation that the user can open, inspect and present. Preserve coherent visual design and meaningful generated artwork when adding editability.

## Choose the production mode

- **Full-slide imagery:** the image model produces each entire page; the bundled CLI maintains jobs and exports rasterized pages with text notes. Use the existing workflow below when this format fits the request.
- **Editable composition (experimental):** when the user requests editable content, read [editable composition](references/editable-composition.md). Plan artwork and native text together, then compose them with the host's available presentation tools. This route does not require the bundled CLI or a particular library. Pilots cover photographic pages, a schedule with replaceable icons, and a native chart with an embedded workbook. Broader visual parity and desktop application behavior are not established.

The CLI project schema, full-page worker prompt and image-only generation/export rules below and in their operational references apply to full-slide imagery. Do not feed a flattened hybrid page into that exporter and call it editable. Reuse the style guides, source-handling principles and speaking guidance in either mode.

## Start from the intended result

Read the supplied material and determine audience, purpose, language and approximate length. Verify changing factual claims against authoritative sources. Extract required figures and screenshots before planning layouts. Keep original assets and their sources with the project.

Offer a concise outline and a representative sample when the user wants collaboration. If they ask for the finished result directly, choose a reasonable style and proceed; do not repeatedly request permission for already authorized work. Record important choices in the brief. Do not require the user to configure an API when a built-in image tool is available.

Use a coherent palette and typography across pages while varying composition by content. Prefer large evidence figures and meaningful photographs over decorative filler. Put detailed explanation in `notes.md`.

## Read the guidance needed for the current phase

The references are operational resources, not optional filler. Read the applicable ones before making the decisions they govern; do not load all twelve style guides for every deck.

| Task | Read |
|---|---|
| Decide phases, approvals, progress and recovery | [Workflow](references/workflow.md) |
| Write outline, map sources and choose a representative sample | [Planning](references/planning.md) |
| Choose built-in tool or API | [Backend choice](references/backend-choice.md) |
| Set up Python, diagnose API access or configure credentials | [Configuration](references/configuration.md) |
| Use figures, screenshots, photos or identity assets | [Assets](references/assets.md) |
| Prepare full-context requests, dispatch workers or recover leases | [Production](references/production.md) |
| Invoke API generation/editing, batching or transparency processing | [Backends](references/backends.md) |
| Write talk tracks, inspect results and export | [Notes and delivery](references/notes-and-delivery.md) |
| Extract a reusable visual system | [Style library](references/style-library.md) |

Use [brief schema](references/brief.md) for data fields and [commands](references/commands.md) for executable syntax. When authorized delegation is available, use [the page worker handoff](prompts/page-worker.md). The coordinator owns final result acceptance.

## Full visual systems

Run `styles` to discover built-in and personal recipes. A known `style_name` in the brief freezes the entire recipe at initialization; subsequent claims include it. Read the chosen guide, not just its name. Each guide links its machine-readable recipe containing canvas, palette, typography, page variants, composition options, image treatment, constraints and review criteria.

| Visual system | Detailed guide |
|---|---|
| 清爽专业 | [Professional](references/styles/professional.md) |
| 创意杂志 | [Editorial](references/styles/editorial.md) |
| 墨水阅读 | [Ink](references/styles/ink.md) |
| 数据分析 | [Dashboard](references/styles/dashboard.md) |
| 学术汇报 | [Research](references/styles/research.md) |
| 复古插画 | [Retro](references/styles/retro.md) |
| 白板讨论 | [Whiteboard](references/styles/whiteboard.md) |
| 技术手绘 | [Technical sketch](references/styles/technical-sketch.md) |
| 温暖手作 | [Handmade](references/styles/handmade.md) |
| 咨询简报 | [Consulting](references/styles/consulting.md) |
| 公共事务 | [Public affairs](references/styles/public.md) |
| 教学演示 | [Teaching](references/styles/teaching.md) |

## Run a full-slide image project

The portable entry point is `python <skill>/scripts/agent4ppt.py`. Run it with Python 3.10+ and Pillow. `doctor` reports the current runtime; `setup` creates a separate runtime if needed. See [commands.md](references/commands.md) for commands and [brief.md](references/brief.md) for the brief schema.

1. Write a brief containing the actual page titles, exact visible copy, layout direction, notes, context, and image references. `init PROJECT --brief brief.json` validates it and creates a SQLite-backed project.
2. `claim PROJECT --worker NAME --page N` produces a self-contained request and a lease token. Read that request. The token is required when returning a result; do not manufacture one or edit the database.
3. With `backend: builtin`, inspect every local reference image using the available image viewing tool, then call the built-in image generation/editing tool with the request's prompt and explicit reference paths. Generate one complete page per call. Python cannot invoke or detect a host's built-in image tool. If it is unavailable, report this and discuss the API route rather than silently switching providers.
4. Inspect the generated page at readable size: title and numbers, clipping, overlaps, layout, asset identity, and figure labels. Repair with the same image backend. Do not substitute locally drawn final pages or paste text over model-generated pages to conceal a failed generation. `key` is an optional asset preprocessing tool, not a final-page renderer.
5. `complete PROJECT --page N --token TOKEN --image PATH --backend builtin --qa "..." --method-file method.json` records the chosen original output and actual tool/mode. Use `--sample` for the first style reference; subsequent claims include the image and method contract. Sample acceptance means the user accepted it or explicitly delegated the visual decision. Record only exposed model/size/quality settings, never guessed host internals. Older projects may omit method evidence, but new production should retain it.
6. Continue the other pages. Independent workers may claim separate pages when the host supports delegation and it is authorized. Otherwise work sequentially. Every worker must receive the claimed request, inspect its references, and use its fixed backend. `renew` extends a lease; `fail` records a blocker; `revise` invalidates stale work and starts a new revision.
7. Complete `notes.md`, inspect every page, and run `export PROJECT`. Export rejects unfinished pages or changed result files. Reopen the PPTX with an independent reader; check page count, notes, and visual output. Report any reader limitations honestly.

For CLI/API image execution, read [backends.md](references/backends.md). API credentials, rate limits and model access are independent of the built-in tool.

## Deliver and retain useful evidence

Provide the PPTX and an easily viewable preview when possible. Briefly state page count, which content is editable, material limitations, and what was actually tested. Keep the working materials appropriate to the chosen mode outside the reusable skill. Do not confuse a mocked HTTP test with a real provider call or a reused image with a newly generated page.

When a reusable custom style emerged, offer to save its visual recipe using `styles --save`; include no private slide content in the saved style. User styles live outside the installed skill and survive updates.

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/465b6219cd8d813e9758 -->
