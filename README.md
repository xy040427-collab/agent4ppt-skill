# Agent4PPT

**Visually rich AI presentations, with the important parts editable.**

An agent skill for creating PowerPoint slides from notes, papers and outlines. Generate coherent, text-free artwork, then add editable text, numbers, formulas, charts and tables with your agent's presentation tools.

Early preview · Host image generation and PPTX tools required · [中文说明](docs/README.zh-CN.md)

## See what it makes

[Explore the public gallery and download the sample decks](https://agent4ppt.ljj040427.chatgpt.site/)

**10 scenarios × 3 selected slides**: comics, research meetings, technology launches, paper presentations, job introductions, club elections, business reviews, product ads, policy briefings and recruitment.

The 30 pages were exported and visually checked in PowerPoint 16.0. Representative titles, chart values and table cells were edited and saved in test copies. Layout corrections were made; these examples do not establish unattended first-pass quality. See [showcase evidence](docs/showcase.md).

## Preview gallery

Ten different visual directions. Each download contains three selected slides. Click a preview to download its PPTX.

| | |
|---|---|
| **Cute comic**<br>[![Cute comic sample slide](https://agent4ppt.ljj040427.chatgpt.site/01-comic/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/01-comic.pptx) | **Research meeting**<br>[![Research meeting sample slide](https://agent4ppt.ljj040427.chatgpt.site/02-lab/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/02-lab.pptx) |
| **Technology launch**<br>[![Technology launch sample slide](https://agent4ppt.ljj040427.chatgpt.site/03-launch/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/03-launch.pptx) | **Paper presentation**<br>[![Paper presentation sample slide](https://agent4ppt.ljj040427.chatgpt.site/04-paper/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/04-paper.pptx) |
| **Job introduction**<br>[![Job introduction sample slide](https://agent4ppt.ljj040427.chatgpt.site/05-career/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/05-career.pptx) | **Club election**<br>[![Club election sample slide](https://agent4ppt.ljj040427.chatgpt.site/06-election/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/06-election.pptx) |
| **Business review**<br>[![Business review sample slide](https://agent4ppt.ljj040427.chatgpt.site/07-report/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/07-report.pptx) | **Product advertising**<br>[![Product advertising sample slide](https://agent4ppt.ljj040427.chatgpt.site/08-ad/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/08-ad.pptx) |
| **Policy briefing**<br>[![Policy briefing sample slide](https://agent4ppt.ljj040427.chatgpt.site/09-policy/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/09-policy.pptx) | **Recruitment**<br>[![Recruitment sample slide](https://agent4ppt.ljj040427.chatgpt.site/10-hiring/preview/1.jpg)](https://github.com/xy040427-collab/agent4ppt-skill/releases/download/showcase-v1/10-hiring.pptx) |

[View all 30 slides](docs/showcase.md#all-slides) · [Download PPTX samples on GitHub](https://github.com/xy040427-collab/agent4ppt-skill/releases/tag/showcase-v1)

## Two production modes

| | Editable composition | Full-slide imagery |
|---|---|---|
| Visuals | Text-free generated artwork | Complete generated slide |
| Editable content | Native text, charts and tables composed by the host | Speaker notes; visible slide is an image |
| Export | Host PPTX authoring tools | Optional bundled Python CLI |
| Best fit | Research, reports, reusable presentations | Image-led pages needing no separate text edits |

The CLI does **not** generate editable slides. Editable composition is a skill-guided workflow, not a standalone model or hosted service.

## Get started

Individuals may use the unmodified tool for their own noncommercial purposes under [LICENSE](LICENSE). Tool modification, redistribution, organizational deployment and commercial use require Jiajun Li's prior written authorization. See [licensing and authorization](docs/licensing.md).

### Install for Codex

Run from the project where you want to use the skill (Node.js/npm and Git required):

```sh
npx skills add xy040427-collab/agent4ppt-skill --skill agent4ppt-skill --agent codex
```

The public repository was discovered and installed successfully into an isolated project on Windows on 2026-09-10. This verifies installation, not a fresh-host slide-generation run. The validation disabled installation telemetry. Other hosts can use the manual route below; image generation and PPTX authoring are still required.

### Manual setup

1. Obtain `skills/agent4ppt-skill`, keeping its reference files together.
2. Put the folder in your host's supported skills directory, or explicitly ask your agent to read its `SKILL.md`.
3. Enable image generation, PPTX authoring and final-slide rendering. See [host requirements](docs/host-requirements.md).
4. Supply your notes, audience and editable-content requirements.

Try this prompt:

> Use agent4ppt-skill to create a 3-slide research update from these notes. Generate coherent text-free backgrounds, then add native editable titles, conclusions and chart data. Vary the layout by slide purpose. Reopen and render the final PPTX, inspect every slide, and deliver the PPTX with previews. Label any illustrative data clearly.

## What is included

Twelve visual-system guides; source-handling and speaker-note guidance; editable composition instructions; an optional portable CLI for full-image jobs, retries and export. No particular PPTX library is required for the editable workflow.

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
