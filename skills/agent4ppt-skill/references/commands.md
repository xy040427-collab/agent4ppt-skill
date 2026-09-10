# Command reference

All examples use `A4P` as shorthand for `python <skill>/scripts/agent4ppt.py`, not an installed shell command. After `pip install .` in the repository, the equivalent installed command is `agent4ppt`.

```text
A4P init ./deck --brief ./brief.json
A4P prepare ./deck
A4P claim ./deck --worker agent-1 --page 1 --lease 900
A4P renew ./deck --page 1 --token TOKEN --lease 900
A4P complete ./deck --page 1 --token TOKEN --image ./candidate.png --backend builtin --qa "Text and source figure checked" --sample
A4P status ./deck
A4P history ./deck
A4P fail ./deck --page 2 --token TOKEN --reason "Image service unavailable"
A4P revise ./deck --page 2 --reason "Tighten text" --page-file ./new-page.json
A4P export ./deck --out ./presentation.pptx
```

`claim` returns the exact prompt, reference paths, token, revision and deadline. `complete` checks that the token is still valid, backend matches, inputs have not changed, and the output is an actual image. The QA note records the agent's visual review; it is not an automated OCR guarantee.

`template --out brief.json` creates a starter brief without overwriting existing content. `prepare` saves all page prompts under `plans/` for review; these are not leases or completed work.

For new production, add `--method-file method.json` to `complete`. The file records the actual `tool`, `mode` and optional exposed model/size/quality/input preparation. Using it with `--sample` makes later requests inherit the method; mismatching result declarations are rejected. It records a declaration, not independent proof of a remote tool invocation.

For an API project, preserve every reference when creating the executable job:

```text
A4P image-job --request ./deck/requests/page-001.json --out ./candidate.png --save ./image-job.json
A4P image ./image-job.json --dry-run
A4P image ./image-job.json
```

`image-job` validates reference hashes and carries all images into the edit path. It does not acquire a lease, call a service, or mark the page complete. Built-in requests are rejected by this conversion; execute those through the host image tool.

`export` embeds original PNG/JPEG bytes by default. Other supported Pillow formats are converted to PNG. Optional `--max-image-mb 2` enables lossy compression for size-constrained delivery. Output is staged then atomically replaced. Never enable lossy compression for scientific evidence without considering legibility.

Use `assemble` for existing images without falsely recording a generation history:

```text
A4P assemble --images ./page1.png ./page2.png --notes ./notes.md --ratio 4:3 --out ./slides.pptx
```

The explicit image order determines slide order. It supports PNG, JPEG, GIF, BMP and other Pillow-readable formats. Missing/corrupt input is an error, not a silently missing page. It does not require a project database.

```text
A4P doctor
A4P setup
A4P config --model gpt-image-2 --base-url https://api.openai.com/v1 --key-env MY_IMAGE_KEY
A4P doctor --check-api
A4P styles
A4P styles --name 学术汇报
A4P styles --name 黑金画册 --save ./recipe.json
A4P key ./green.png --out ./transparent.png --color "#00ff00" --soft --opaque 96 --despill
```

`key` supports hard/soft mattes, corners/border key estimation, `--contract`, `--feather`, PNG/WebP output and explicit `--overwrite`. It is for user-authorized asset processing. CLI JSON is UTF-8 on Windows. Nonzero exit codes mean failure; batch partial failure also returns nonzero. Credentials must be configured locally, not pasted into chat.

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/d3022627c09908b45a58 -->
