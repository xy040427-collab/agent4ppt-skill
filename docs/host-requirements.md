# Host requirements

Installing the skill does not install an image model or grant model access.

Editable composition needs authorized input-file access, an image-generation tool, a PPTX writer supporting native objects, and a way to reopen and render the exported deck. Charts also need real data and intact workbook references.

The showcase used host-provided image generation, a host-provided presentation library, and PowerPoint 16.0. These host products are not redistributed. A clean-environment end-to-end portability claim is not established.

The entry point is `skills/agent4ppt-skill/SKILL.md`. Keep its reference files together. Use it for image-led presentations, full-slide-image exports and coordinated artwork with editable text. Do not treat it as pixel-perfect reconstruction of arbitrary slide files.

If your host lacks required capabilities, report them before proceeding. Never fake image generation or silently replace requested native charts with screenshots. No GitHub token, automated star or unrelated telemetry is required.
