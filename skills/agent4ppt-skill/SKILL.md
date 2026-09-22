---
name: agent4ppt-skill
description: Create Agent4PPT full-slide-image and editable-mode PowerPoint decks and paired comparisons. For every editable page, generate a complete slide first, erase selected text with an image model, then restore native text through PowerPoint MCP and visually match the original. Includes the portable runtime, stage records and review tools.
---

# Agent4PPT

Deliver a presentation that the user can open, inspect and present. Preserve coherent visual design and meaningful generated artwork when adding editability.

For every new editable page, use `full_slide_first`. Read [editable composition](references/editable-composition.md) and [visual replication](references/visual-replication.md) before generating images or writing a production script. The sequence is complete slide generation → accepted original → image-model removal of selected text → native text restoration through PowerPoint MCP → rendered visual comparison and adjustment. Initial layout estimates are not the visual target.

For a two-mode comparison, retain those same accepted generated originals as the full-slide version. Do not flatten the editable deck and label it a full-slide-image baseline. Do not switch to `reserved`, reuse unrelated images or submit an unrendered background as QA evidence to work around a tool failure. Resume existing legacy projects as needed; creating a new reserved project requires an explicit user request for that workflow. If a required tool fails, diagnose/retry within the task scope or report the blocked stage. The runtime cannot prove that a host's visual judgment is truthful.

## Choose the production mode

For built-in image outputs, read [the artifact handoff](references/backend-choice.md#内置图片产物交接) before generation. A display data URL does not mean no local file exists. Resolve the output of the specific tool call, use `import-image` to validate/copy it into the task directory, then inspect and register it with the existing stage command. Importing does not complete or approve a page.

- **Full-slide imagery:** the image model produces each entire page; the bundled CLI maintains jobs and exports rasterized pages with text notes. Use the existing workflow below when this format fits the request.
- **Editable composition:** read [editable composition](references/editable-composition.md). New projects default to `editable_workflow: full_slide_first`: generate a finished slide WITH text and pictures, measure selected native overlays from that design, register it with `record-design`, use its returned erase request to remove ONLY selected content, register the edited background with `record-background`, then compose and review native overlays. Keep the complete artwork and fixed text. Explicit `editable_workflow: reserved` retains the earlier blank-region route. Native charts, tables and connected diagrams still require the documented host extension; the bundled exporter supports text and pictures.

Both modes share planning, style guides, source handling, page leases, revisions, notes and delivery checks. The prompt and exported objects depend on the project mode. Editable does not mean every visible mark must become an object: explicitly allowed fixed text and visual symbols can stay in the image. Do not split a complete scene into many assets merely to make selected text editable. Never flatten a composed page and call the flattened result editable.

New full-slide-first projects enforce `review_policy: structured-v1`. Initial overlay coordinates are provisional; do not constrain the complete design with blank-region guides. Measure positions and typography from the accepted design and preflight native text before `record-design --overlays-file`. Compare the design, erased background and composed render. Check erasure residue, artwork preservation and design alignment in addition to ordinary composition QA. Diagnostic reservation guides remain available for the explicit `reserved` route. With authorized delegation, assign the complete page loop to page workers; the runtime queue does not launch host agents itself.

## Start from the intended result

New text-only full-slide-first projects also enable `visual_comparison: raster-v1`. After each PowerPoint checkpoint render, run `compare-render` as described in [visual replication](references/visual-replication.md#measured-render-comparison). Inspect the overview on every pass and every object panel initially and finally; intermediate passes focus on modified objects and remaining findings. Use the named native object and actual run formatting in its report to correct position, visible size, color and emphasis through MCP. Recompose, rerender and compare again after corrections. Completion recomputes these measurements and rejects stale reports or unaddressed findings. A diagnostic with no flags is not visual approval; it does not recognize words or identify the target font. Do not manufacture exceptions to approve visible mismatches.

New full-slide-first projects containing only native text overlays enforce `native_acceptance: target-v1`: completion requires an adopted `compose --native-draft` checkpoint, a PowerPoint preview exported at the target image dimensions, and observations for every text object. Initial drafts cannot pass this gate. Existing databases and mixed image/text extensions keep their previous compatibility rules. These checks establish artifact completeness, not proof of MCP use or visual quality.

Before batch production, finish one representative content page with multiple separately positioned text blocks, including emphasis and body copy. A cover alone does not validate restoration. Inspect target and render yourself at equal dimensions; fix visible differences before accepting the sample or expanding production. Never prefill pass reports for pages you have not inspected. Use `font_size` in points, not `size`.

After the sample is accepted, use page subagents where the host supports them. New briefs default to `parallelism: 10`, with a maximum of 10. Keep the worker pool as full as useful: target `min(10, project parallelism, ready pages, actual available child-agent capacity)`, accounting for workers already running rather than spawning a duplicate pool. Refill each freed slot immediately instead of waiting for an entire batch. The limit is a ceiling, not a reason to create ten workers for fewer ready pages. Use `dispatch-plan PROJECT --host-slots N` to inspect the runtime's read-only dispatch recommendation; pass actual currently available child slots. This command neither creates agents nor increases the host's own limit. If the host offers fewer slots, use those and report the actual concurrency honestly. See [production](references/production.md).

Assign each editable worker the complete page loop and its own files and session. The coordinator owns the outline, accepted sample, shared notes, final deck and acceptance. Do not consume page-worker slots with redundant QA-only agents. When PowerPoint uses a shared endpoint/process, serialize **all** its mutations, saves and renders through one coordinator-owned queue; separate session IDs alone do not guarantee safe concurrency. Image generation, erasure and independent visual inspection can continue in parallel. Never close shared PowerPoint sessions or quit the shared process while another page is active.

For each correction pass, inspect the page first, prepare all required object changes, then execute ordinary MCP calls together in one orchestration, checking each result; save, adopt and render once after the pass. This is host-side batching, not a new native MCP batch endpoint. Preserve every-object initial and final comparison review and all runtime gates. The coordinator inspects every final page overview and the detailed regions needed to resolve findings, small-text concerns and exceptions, reusing the worker's genuine per-object evidence instead of repeating every successful intermediate pass. Stop polishing imperceptible glyph/antialias differences after visual acceptance; unresolved visible defects or required comparison findings still block completion.

For full-slide-first editable production, read [visual replication](references/visual-replication.md) before composition. Use the accepted design as the visual target, adjust existing native text through PowerPoint MCP, verify East Asian fonts, and register adjusted checkpoints with `compose --native-draft`. Render and compare before completion. This is the normal production loop, not optional post-delivery repair; final export retains adopted text formatting.

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

The following is the unchanged `mode: full_slide` route (also the default for older briefs). For `mode: editable`, follow the shared queue with the additional `compose → render/review → complete` steps in [editable composition](references/editable-composition.md).

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
