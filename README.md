# Agent4PPT

**Visually rich AI presentations, with selected text editable.**

Generate the complete slide → remove selected text with the image model → restore native text through PowerPoint MCP → render, compare and refine. Full-slide imagery and editable mode share the same accepted original designs.

[中文说明](docs/README.zh-CN.md) · [Current workflow gallery](docs/showcase-current.md) · [Install and use](#get-started)

## Current workflow in action

**Electronic information majors — a complete 10-slide paired presentation.** These are delivered outputs from the current full-slide-first workflow, reused for this showcase rather than newly generated for the README. The right column is a rendered PowerPoint slide with native text, not a second flattened baseline.

| Full-slide image · original design | Editable mode · PowerPoint render |
|---|---|
| ![Original complete slide](docs/assets/full-slide-first/full-slide-image-01.png) | ![Native editable slide](docs/assets/full-slide-first/editable-mode-01.png) |
| ![Chip design and packaging original](docs/assets/full-slide-first/full-slide-image-05.png) | ![Chip design and packaging editable render](docs/assets/full-slide-first/editable-mode-05.png) |
| ![Optoelectronics original](docs/assets/full-slide-first/full-slide-image-07.png) | ![Optoelectronics editable render](docs/assets/full-slide-first/editable-mode-07.png) |

[Download full-slide PPTX](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-full-slide-first-v2/electronics-full-slide-image.pptx) · [Download editable PPTX](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-full-slide-first-v2/electronics-editable-mode.pptx) · [Compare all 10 pages](docs/showcase-current.md)

The two decks each contain 10 slides and 10 speaker-note pages. The editable deck contains **90 native text objects**; the full-slide deck contains none. Native object counts establish editability, not visual equivalence. Fonts, line breaks and small details can differ; graphics and fixed text remain raster artwork. These examples do not establish unattended first-pass quality. [Verification scope](docs/showcase-current.md#verification-and-limits).

## How editable mode works

1. **Create the target:** generate and accept the entire designed page, including text.
2. **Remove selected text:** use the image model to produce the background, preserving the artwork and fixed text.
3. **Restore native objects:** use PowerPoint MCP to set content, position, font, size, color and wrapping against the target.
4. **Render and review:** inspect the actual PowerPoint output, adjust named objects, then retain the accepted checkpoint for export.

Both modes use the shared SQLite queue, leases and revisions. Structured review and raster comparison records prevent skipped or stale artifacts from passing completion. They do not prove that an agent's visual judgment is correct. See [editable workflow](skills/agent4ppt-skill/references/editable-composition.md) and [visual replication](skills/agent4ppt-skill/references/visual-replication.md).

## Historical gallery

The original **10 scenarios × 3 slides** collection remains available. It documents an earlier production approach and is not evidence for the current full-slide-first path. The external gallery site below still hosts that historical collection.

<details>
<summary>Browse the earlier 30-page gallery</summary>

### Earlier visual directions

Ten different visual directions. Each download contains three selected slides. Click a preview to download its PPTX.

| | |
|---|---|
| **Cute comic**<br>[![Cute comic sample slide](https://agent4ppt.ljj040427.chatgpt.site/01-comic/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/01-comic.pptx) | **Research meeting**<br>[![Research meeting sample slide](https://agent4ppt.ljj040427.chatgpt.site/02-lab/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/02-lab.pptx) |
| **Technology launch**<br>[![Technology launch sample slide](https://agent4ppt.ljj040427.chatgpt.site/03-launch/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/03-launch.pptx) | **Paper presentation**<br>[![Paper presentation sample slide](https://agent4ppt.ljj040427.chatgpt.site/04-paper/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/04-paper.pptx) |
| **Job introduction**<br>[![Job introduction sample slide](https://agent4ppt.ljj040427.chatgpt.site/05-career/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/05-career.pptx) | **Club election**<br>[![Club election sample slide](https://agent4ppt.ljj040427.chatgpt.site/06-election/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/06-election.pptx) |
| **Business review**<br>[![Business review sample slide](https://agent4ppt.ljj040427.chatgpt.site/07-report/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/07-report.pptx) | **Product advertising**<br>[![Product advertising sample slide](https://agent4ppt.ljj040427.chatgpt.site/08-ad/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/08-ad.pptx) |
| **Policy briefing**<br>[![Policy briefing sample slide](https://agent4ppt.ljj040427.chatgpt.site/09-policy/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/09-policy.pptx) | **Recruitment**<br>[![Recruitment sample slide](https://agent4ppt.ljj040427.chatgpt.site/10-hiring/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/10-hiring.pptx) |

[View all 30 slides](docs/showcase.md#all-slides) · [Download PPTX samples on GitHub](https://github.com/xy040427-collab/agent4ppt-skill/releases/tag/showcase-v1)

</details>

[Historical gallery site](https://agent4ppt.ljj040427.chatgpt.site/) · [Historical machine-readable summary](https://agent4ppt.ljj040427.chatgpt.site/llms.txt)

## Two production modes

| | Editable composition | Full-slide imagery |
|---|---|---|
| Visuals | Complete design, selective erasure, native content restored | Complete generated slide |
| Editable content | Bundled native text and replaceable pictures; advanced charts/tables through a host extension | Speaker notes; visible slide is an image |
| Export | Shared CLI queue, compose/review, and layered export | Bundled CLI image export |
| Best fit | Research, reports, reusable presentations | Image-led pages needing no separate text edits |

Set `mode: editable` in a brief to use the same SQLite queue, leases and revisions, with `compose` and rendered-page review before completion. The CLI exports native text and independent pictures over the original whole-page artwork. Advanced native charts/tables still use host tools and are not integrated into this CLI review path. This is a skill and portable runtime, not a standalone model or hosted service. See [editable workflow](skills/agent4ppt-skill/references/editable-composition.md).

## Get started

Individuals may use the unmodified tool for their own noncommercial purposes under [LICENSE](LICENSE). Tool modification, redistribution, organizational deployment and commercial use require Jiajun Li's prior written authorization. See [licensing and authorization](docs/licensing.md).

### Install for Codex

Run from the project where you want to use the skill (Node.js/npm and Git required):

```sh
npx skills add xy040427-collab/agent4ppt-skill --skill agent4ppt-skill --agent codex
```

The skill is also indexed in [Awesome Skills](https://www.awesomeskills.dev/en/skill/xy040427-collab-agent4ppt-skill) for people who prefer a directory search.

The public repository was discovered and installed successfully into an isolated project on Windows on 2026-09-10. This verifies installation, not a fresh-host slide-generation run. The validation disabled installation telemetry. Other hosts can use the manual route below; image generation and PPTX authoring are still required.

### Manual setup

1. Obtain `skills/agent4ppt-skill`, keeping its reference files together.
2. Put the folder in your host's supported skills directory, or explicitly ask your agent to read its `SKILL.md`.
3. Enable image generation, PPTX authoring and final-slide rendering. See [host requirements](docs/host-requirements.md).
4. Supply your notes, audience and editable-content requirements.

Try this prompt:

> Use agent4ppt-skill to create a 3-slide research update from these notes. Generate complete slides first, then erase selected titles, conclusions and labels and restore them as native overlays measured from the design. Keep ordinary icons, arrows and decorative structure in the artwork. Register both stages, compose and compare each page against the design, then reopen and render the final PPTX. Deliver the PPTX with previews and label illustrative data clearly.

## What is included

Twelve visual-system guides; source-handling and speaker-note guidance; editable composition instructions; a portable CLI for page leases, revisions, image jobs, native overlays, review records and export. The bundled writer has no slide-authoring library dependency; rendering requires the host.

## Limits

- Quality, latency and cost depend on your host model and image service.
- Background details remain raster images. This is not arbitrary PPTX-to-editable reconstruction.
- Longer replacement text may need layout changes. Rendering and inspection are part of delivery.
- The showcase was checked in PowerPoint 16.0 on Windows. Cross-application parity and fresh-environment end-to-end installation are not established.
- Built-in image generation was used for the showcase. Optional HTTP providers have local protocol tests, not universal live-provider verification.

## Optional full-image CLI

Python 3.10+ and Pillow are required. For permitted personal noncommercial use:

```sh
python skills/agent4ppt-skill/scripts/agent4ppt.py doctor
python skills/agent4ppt-skill/scripts/agent4ppt.py --help
```

See [commands](skills/agent4ppt-skill/references/commands.md) and [verification history](docs/verification.md).

## Feedback

Report your host, expected result, actual result and a sanitized reproduction. Do not include credentials or private slide content. See [contributing](CONTRIBUTING.md).

**If Agent4PPT helps you create better slides, consider starring the repository.** Installation and generation never require a GitHub token or a star.

## Rights and provenance

Maintained by [Jiajun Li](https://github.com/xy040427-collab). Read [LICENSE](LICENSE) for current rights; this personal-use-only project is source-available, not open source. Development lineage and applicable upstream notice are retained in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Raw generated artwork is not claimed as exclusively copyrightable.
