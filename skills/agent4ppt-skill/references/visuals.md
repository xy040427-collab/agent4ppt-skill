# Images, style and quality

Use the user's original figure, screenshot, logo or photograph as a named input, not merely a topic suggestion. Each reference role should distinguish evidence, product identity, edit target and style. Inspect every local reference before the model call. For charts, state exactly what must remain fixed: values, axes, colors, legend and labels. For products, verify appearance against the original after generation. Image editing is probabilistic; report material changes and regenerate rather than claiming pixel-perfect preservation.

For a sample, pick a representative content page if it better demonstrates the intended layouts. Inspect it before marking it as a style reference. Subsequent pages should retain palette and type hierarchy but use compositions suited to their content: large evidence figure, comparison, timeline, process, cover, or explanation. Repetition of the same three cards is not a requirement.

The `styles` command lists twelve built-in visual recipes and user overrides. Recipes are newly written descriptions, not fixed templates. A custom recipe JSON contains `guidance`, and may include `palette`, `layouts`, `typography`, `image_treatment`, `use` and `constraints`. Save with `styles --name NAME --save recipe.json`; collisions require `--overwrite`. Personal recipes are in `${AGENT4PPT_HOME:-~/.agent4ppt}/styles`, outside installation.

To extract a reusable style from a PDF/PPTX/image, first view actual rendered pages. Inspect a cover, a content page and a data/diagram page when available. Record visual rules and layout variation, excluding private text, data and required source assets. Do not derive an entire visual identity from extracted text or XML alone.

Final QA must include large-enough page images. Check exact numbers and names, Chinese glyphs, text truncation, overlaps and evidence fidelity. Write speaker notes as a usable talk track, connecting each figure to a point and explaining limitations. Do not fill notes with repetitive descriptions of the page. Reopen the exported file independently; rendering, object parsing and a successful ZIP check verify different things.

<!-- a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/9556aea92409ccd06aa8 -->
