# Example: PDF Catalog → Markdown (cutroom-extract / Docling 2.141)

**Request:** "Turn the skills catalog into a PDF in the cutroom brand and extract it back to Markdown, to verify whether tables survive."

<p align="center"><img src="out/page-1.png" width="800" alt="First page of the PDF catalog"></p>

- **Input:** [`src/catalog.pdf`](src/catalog.pdf), two pages (above, the first).
- **Output:** [`out/catalog.md`](out/catalog.md), with headings, list, and both tables in Markdown, and [`out/catalog.json`](out/catalog.json), with the structured document and the page coordinates of each passage.

## How it was made

```bash
# Data source:
cutroom catalog --json

# Render catalog.html (cutroom brand: Bricolage Grotesque, Inter, Hot Signal, wordmark) to A4 landscape PDF:
cutroom render src/catalog.html -o src/catalog.pdf --size a4

# Convert to Markdown and JSON with Docling:
. ~/.local/share/cutroom/env.sh && docling convert src/catalog.pdf --to md --to json \
  --image-export-mode placeholder --output out

# Render page 1 preview:
pdftoppm -png -r 150 -f 1 -l 1 src/catalog.pdf out/page
```

On CPU (without GPU), 2 pages took ~10 s in total: ~2 s of conversion and the rest to load models into memory. The initial run on the machine took ~50 s to download layout and OCR weights.

## What to check in the result

The example preserves actual extraction quirks and real-world behavior. These are exactly what the skill directs users to inspect before trusting extracted numbers:

- **Split tables across page breaks:** The PDF divides the 12-row table between page 1 (5 rows) and page 2 (7 rows), with Chrome automatically repeating the `<thead>` header. Docling returns two distinct Markdown tables (`tables[0]` and `tables[1]` in the JSON). Rejoin both before running aggregations or analysis.
- **PDF hyphenation & line wraps:** Strings that break across lines within cells or paragraphs can emerge with an extra space. For example, `Kokoro-82M via kokoro-onnx (Apache- 2.0)` acquired a space in `Apache- 2.0`, `cutroom _deck` has an extra space around the underscore, and `cutroom catalog --json .` separated the trailing period. Always cross-check numeric cells against the source PDF or JSON.
- **Furniture layer:** The header eyebrow `CUTROOM · CATALOG` was classified as a page header (`page_header`, `furniture` layer) and kept out of the Markdown export. It remains preserved in `out/catalog.json`. To include furniture layer elements in the text export, use `doc.export_to_markdown(included_content_layers={ContentLayer.BODY, ContentLayer.FURNITURE})` (refer to the `cutroom-extract` skill).
- **Logo OCR:** The footer wordmark was detected as an image (`<!-- image -->`). Docling's default OCR ran across image regions and extracted the text `cutroom` from the raster bitmap, recorded in `out/catalog.json` under `pictures[0]`.

All headings, the skill list, and table cells arrived in proper reading order. Body text originates directly from the PDF text layer; OCR was selectively engaged only on image regions.
