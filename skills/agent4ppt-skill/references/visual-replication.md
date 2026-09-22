# Target-driven editable production

Use this loop for every full-slide-first editable page, not only when a user complains.
The accepted complete design is the visual target. The coordinator owns visual acceptance.

## Object mapping and acceptance gate

Treat pre-generation coordinates as provisional. After inspecting the target, map every spatially independent label to a separate named text object. Four card labels need four objects, not one four-line box. Preserve mixed emphasis with formatted runs. If the initial brief grouped text incorrectly, use `revise --page-file` to correct IDs and exact line breaks, re-claim, and explicitly re-register the still-applicable generated design/background after review; do not pretend they were regenerated. Complete this mapping before locking `record-design`.

First validate a representative body page, then expand production. For each page, inspect the actual target, erased background and PowerPoint render before writing the report. Update existing objects through MCP and repeat save → adoption → rendering when differences remain. Do not accept a smaller plain title when the target uses large mixed-color text, or move labels away from their associated panels to make them fit.

New text-only full-slide-first projects use `native_acceptance: target-v1`. Export the PowerPoint preview with explicit width/height equal to the target image pixels. Complete rejects initial compose drafts and requires `native_draft: true` from a real adoption receipt. QA must additionally contain `objects`, keyed by every overlay ID, each with nonempty `placement`, `typography` and `content` observations describing the comparison actually performed:

```json
{"objects":{"title":{"placement":"Centered over the four cards; compared top and left edges with the target.","typography":"Compared title size, weight and blue emphasis with the target.","content":"Exact title and original line break retained."}}}
```

Use page-specific observations; this example is not a pass template. Failed comparisons stay as unresolved issues and cannot complete. Hash-bound receipts and object observations do not prove that MCP was used or that a model honestly looked at the images. The coordinator remains responsible for visual judgment. Legacy projects without target-v1 and mixed image/text extensions retain their prior rules; this does not waive visual review.

1. Generate and inspect the complete slide. Preserve all selected text, including small body copy. Record each text object's stable ID, exact content and line breaks, visible bounds, font family/weight, size, color and alignment. Derive geometry from the target image; do not replace it with a generic layout. Mixed colors can use runs within the same named object. Identify separate objects before registering the design.
2. Use the existing image-model edit request to erase only selected text. Attach the complete target image. Do not crop, cut out text, paint rectangles or reconstruct the artwork programmatically. Compare target/background for residue and changes to noneditable lettering, icons and decoration. Generative edits are not pixel-lossless.
3. Run `compose` for an initial single-page native draft. Open that draft through the available PowerPoint MCP. Read page size: the bundled 16:9 canvas is 720 × 405 points, not an assumed 960 × 540. Convert target pixels with `x_pt=x_px*slide_width/image_width` (likewise y/width/height). Scale font estimates to the actual page size. Locate objects by stable name and verify text before changing them; do not trust old shape indexes after edits.
4. Adjust the existing text objects using MCP. Set explicit size, color, Latin and East Asian font, weight, margins, alignment and autofit. Preserve target line breaks. Do not delete body copy or shrink everything to conceal errors. Inspect tool payload success, not merely transport success. Keep one writer per page/session. If multiple pages share a PowerPoint endpoint/process, serialize all mutations, saves and renders through one coordinator-owned queue. Never close shared sessions or quit PowerPoint while another page is active: some bridges invalidate all sessions on close.
5. **Chinese font check:** some bridges set `Font.Name` but leave `Font.NameFarEast` at the theme default. Read both back. If the bridge lacks the latter or margins, run the narrow helper below against the exact open file and named objects. Choose installed fonts by comparison with the target; there is no universal heading font. A Black font face need not also have synthetic bold. Treat font substitution as unresolved until rendered.
6. Save through MCP. Register the adjusted draft using `compose --native-draft adjusted.pptx --out accepted-v2.pptx` with the same project/page/token/background. This creates a new immutable checkpoint and review receipt without regenerating the background. Render **accepted-v2.pptx** in PowerPoint, compare with the target at the same image dimensions, and inspect enlarged text regions. Check title hierarchy, color emphasis, exact content, baseline/position, wrapping, body density and preservation of artwork. Change the working copy and repeat registration/rendering when needed. Never edit a checkpoint after its receipt is created.
7. Complete with the latest receipt, actual render and structured QA. No missing text, wrong emphasis, overflow, unintended wrapping or obvious displacement may be marked pass. The coordinator must inspect the comparison, even when a worker handled the page. Hashes establish provenance, not visual equivalence. If the budget is exhausted with differences, report them instead of marking complete.
8. Export preserves adopted native text XML (including runs and East Asian fonts), instead of rebuilding those text boxes from initial estimates. Reopen and render the final deck; verify it still matches the accepted checkpoints. Supply original and editable previews for comparison.

## Measured render comparison

Run after rendering the immutable checkpoint in real PowerPoint, at the original design pixel dimensions:

```sh
A4P compare-render PROJECT --review-file checkpoint.review.json --preview rendered.png --out comparison-attempt-01
```

Use a fresh output directory for each attempt. This command reads the registered original and erased background, checks the receipt against project history and draft hash, and reads native object names, positions (normalized and points), run text, sizes, Latin/East Asian fonts and colors from the actual PPTX. It does not edit the deck or approve it. It also works diagnostically on existing full-slide-first text projects; only newly initialized text-only projects require it at completion.

Open `overview.png` and **every** numbered object panel for the initial comparison and the final acceptance comparison of each page. For intermediate correction passes, inspect the overview, all modified objects and all remaining findings; do not substitute intermediate sampling for the final every-object review. Each panel shows TARGET / ERASED BACKGROUND / PPT RENDER / ABS DIFFERENCE for the union of the measured original box and current native box. These crops are diagnostic views only: text removal still uses the image model on the full original. Never use a diagnostic crop as a replacement slide background.

`comparison.json` associates each region with the stable MCP object name. It measures foreground footprints relative to the erased background using an RGB difference threshold of 32. Findings include center displacement (> max(3 pixels, 15% of target footprint height)), width/height changes (>20%), foreground amount changes (>35%), median channel color difference (>35) and coarse palette distance (>0.35). Dense changed regions (>65%) and absent target pixels are marked unreliable. One-pixel background dimension rounding is aligned only for measurement. These are diagnostic thresholds, not a guarantee of legibility or fidelity.

For a position finding, inspect the region and use `suggested_shift_pt` as an initial correction to the named object's position. It is a measurement hint, not an automatic edit. For size/wrapping or ink findings, inspect the visible glyph height, line breaks, width, font weight, textbox margins and run sizes together. For color/emphasis findings, restore the target's individual colored runs rather than applying one color to the whole box. Check exact text visually against the original: this version does **not** perform OCR, infer the target font family, or recover an exact point size from pixels. Noneditable artwork changes, residual text and overlapping regions may contaminate a footprint. Correct erasure or mapping when necessary; do not tune typography to compensate for a damaged background.

After MCP corrections save a new working draft, adopt a new checkpoint, render it, and run compare-render again. Inspect a representative complex content page before expanding to the rest of the deck. The main agent owns final side-by-side acceptance, including small body text and emphasis even when no diagnostic flags remain.

## Efficient correction and review

Keep the full-slide-first sequence unchanged. After the sample passes, page workers can run independent page loops concurrently under the pool limits in [production](production.md). Each worker reviews every object initially and finally, and returns the actual inspected files, object observations, remaining findings and stage timings. The coordinator reviews every final overview plus detailed regions with findings, exceptions, uncertain small text or inconsistent emphasis; it may reuse the worker's genuine per-object evidence without redoing every successful intermediate pass. This does not delegate away final acceptance or permit generic prefilled QA.

Measure and plan the whole page before editing: collect changes by stable object name, execute the necessary ordinary MCP calls together in one host orchestration, inspect each payload result, then save/adopt/render once for that correction pass. There is no assumed native MCP batch endpoint. Shared-process edits and rendering remain serialized while image generation, erasure and independent inspection run concurrently. If an MCP operation fails, recover and verify that object before adopting the pass. Preserve immutable reviewed checkpoints.

After actual visual inspection, stop iterations for imperceptible glyph contour, antialias or subpixel differences that do not affect accepted appearance. Continue fixing missing text, unintended wrapping, overlap, clipping, wrong emphasis or noticeable geometry/color differences. All required comparison findings must still be resolved or individually documented as genuine measurement false positives; this stopping rule does not waive diagnostic gates, authorize unexplained differences or set an automatic pass after a fixed number of rounds. Record generation, erasure, MCP correction and render/review timings separately so future speed claims reflect measured work.

Add the absolute `comparison_file` path to the existing bound QA JSON. On new projects `complete` recomputes the current comparison, rejects changed/stale measurements and requires every flagged finding to be resolved. A genuine measurement false positive can be documented under `comparison_exceptions[object_id][flag]` with two nonempty fields: `reason` (specific cause of invalid measurement) and `visual_evidence` (what the inspected target/render region actually shows). An exception is not permission to accept an actual visible difference. Never copy generic exceptions across objects, auto-generate them from the flag list, or mark unread images pass. All exceptions remain in the archived QA for review; software cannot prove that a visual explanation is truthful. If the mismatch remains, leave the page incomplete and report it.

The accepted comparison is archived and hash-checked during export. New text-only projects automatically carry this policy; existing databases, full-slide production and mixed-object extensions retain their compatibility rules. Do not edit the database or downgrade the mode to bypass findings.

## Host font compatibility helper

Prepare a UTF-8 JSON array such as `[{"id":"title","font":"Noto Sans SC Black","wrap":false}]`, using actual installed fonts and object names. Run:

```powershell
powershell -NoProfile -File <skill>/scripts/powerpoint-fonts.ps1 -PresentationPath <absolute-open-draft.pptx> -ObjectsFile <objects.json> -SlideIndex 1
```

Requires Windows PowerShell 5.1 and desktop PowerPoint. It attaches to the exact full path, validates all IDs first, sets both font families and zero margins, disables autofit and returns read-back values/bounds. It does not save, quit PowerPoint or modify other decks. MCP remains the normal editor; this helper supplies missing font/margin access. Do not claim this helper was used if it was not. Without a desktop renderer, report the verification limitation.

## Adoption boundary

`compose PROJECT --page N --token TOKEN --image registered-background.png --native-draft adjusted.pptx --out checkpoint.pptx`

Adoption accepts one unchanged full-canvas background and the exact named editable text objects on the original compose canvas. IDs, text and explicit line breaks must match; each run must carry explicit size, color and Latin/East Asian fonts. Theme-linked formatting, hyperlinks, extra objects, replaced backgrounds and multi-slide inputs are rejected. Do not silently flatten unsupported content. Rich text formatting is retained inside each accepted named box. Other editable objects keep the existing bundled route or documented host extension.

Styling/position corrections in a native draft do not change the locked content mapping or require `revise`. Changing content, IDs, target design or background does require `revise` and re-registration. Native drafts are immutable reviewed results, not a general round-trip importer. Image compression is disallowed when exporting adopted pages so reviewed background bytes remain unchanged.
