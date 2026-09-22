# Working on Agent4PPT

For presentation production with this repository, first read `skills/agent4ppt-skill/SKILL.md`. For editable mode, also read `references/editable-composition.md` and `references/visual-replication.md` under that skill. Generic presentation guidance must not replace the requested Agent4PPT pipeline. Each editable page starts with an accepted, fully generated slide, then image-model text removal, PowerPoint MCP text restoration and target-based visual review. Use the same accepted originals for a full-slide/editable comparison. A rendered editable slide is not a full-slide image-generation baseline.

Follow explicit user scope. Do not invent authorship, ownership or licensing claims. Respect external dependency licenses.

Keep implementation and commit messages in English. Update the Chinese user documentation when changing commands or behavior. Verify file outputs and state transitions, not just command success. Separate local mock-provider tests from live image-generation evidence.

Preserve substantive capabilities and guidance when rewriting. Do not optimize for archive size, line count or a minimal reference library. Before removing or collapsing a resource, map its decisions, examples and constraints to maintained replacements. Update docs/content-coverage.md and validate that machine-readable guidance reaches actual requests. A shorter implementation is not evidence of equivalent behavior.

Keep credentials, generated decks, runtime databases and test artifacts out of Git. Use the portable CLI as the integration boundary. Before publishing, run the test suite and inspect a real exported deck. Never claim lossless evidence preservation from a generative image edit alone.
