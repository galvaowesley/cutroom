---
name: cutroom-extract
description: "Extracts documents (PDF, DOCX, PPTX, XLSX, HTML, images, including scanned PDFs) into clean Markdown and JSON with Docling, before the LLM reads them: keeps reading order, headings and tables, runs local OCR and saves figures as files. Use before reading, summarizing, comparing or citing long documents or documents with tables, when a report, deck, video or brand starts from PDFs or spreadsheets, or when reading a PDF directly comes out truncated, scrambled or without its tables. Everything runs locally; the document never leaves the machine. Usage: cutroom-extract <file | folder | URL> [pages=1-10] [ocr]"
metadata:
  version: "2.0.0"
---

# cutroom-extract: documents to Markdown/JSON for the LLM (Docling 2.141)

Read the conventions first: `~/.local/share/cutroom/harness/conventions.md`.

`cutroom` = `~/.local/share/cutroom/bin/cutroom`.

Why: reading a PDF directly costs more tokens and loses structure (tables become running text, columns mix, scanned
pages vanish). Docling returns Markdown with headings, lists and tables in place, and JSON with the page and position
of each passage, for citing.

## Step 0: component

Run `cutroom doctor --json` and check `components.extract.installed`. If false, say `extract` downloads ~2.3 GB (CPU
torch and layout, table and OCR models) and offer `cutroom-init extract`. Stop until it is installed.

## Step 1: convert

1. Run `cutroom job "<title>"` and keep the path as `$J`, or use the piece folder if this is part of a larger piece.
2. Convert into `$J/src/extract`:

```bash
. ~/.local/share/cutroom/env.sh && docling convert "<file|folder|URL>" --to md --to json \
  --image-export-mode referenced --output "$J/src/extract"
```

| Case | Add |
|---|---|
| Scanned PDF or text in images | `--ocr-mode full_page --ocr-lang en,pt` (the document's languages) |
| Some pages only | `--page-range 3-12` |
| Large batch, simple tables | `--table-mode fast` |
| Whole folder | pass the folder as input (one `.md`/`.json` per file) |
| Password-protected PDF | `--pdf-password "<password>"` (ask; never write it to a file) |
| Formulas or code blocks | `--enrich-formula` / `--enrich-code` (downloads ~600 MB of models the first time: warn first) |
| Chunks for RAG | `--to chunks --chunks-max-tokens 512` |

- `--image-export-mode referenced` saves figures as PNG next to the `.md`, ready to reuse. To only read,
  `placeholder` keeps the Markdown smaller.
- Do not use `--enable-remote-services`, `--pipeline vlm` or `--enrich-picture-description` unless asked. The first
  sends content out; the others download vision models of hundreds of MB and are slow on CPU.
- On CPU, conversion takes about 1 to 5 s per page, plus ~10 s to load models per run (~40 s the first time on a
  machine). Large documents: run as a long command, or convert a whole folder at once so models load once.

For what the CLI does not cover, use the Python API in the same environment: `docling-python script.py`.

```python
from docling.document_converter import DocumentConverter
doc = DocumentConverter().convert("file.pdf").document
print(doc.export_to_markdown())
```

## Step 2: read without blowing the context

- Check the size first (`wc -c "$J/src/extract/"*.md`). Up to ~60 KB, read it whole. Above that, list the headings
  (`grep -n '^#' file.md`) and read by section.
- Tables come out as Markdown. For numbers, prefer the table in the `.json` (`tables[*].data`), which keeps merged
  cells.
- Page headers and footers (page numbers, document name, notices) go to the `furniture` layer and stay out of the
  Markdown, but remain in the JSON (`label: page_footer`/`page_header`). To include them:
  `doc.export_to_markdown(included_content_layers={ContentLayer.BODY, ContentLayer.FURNITURE})` with
  `DoclingDocument.load_from_json(...)` in `docling-python`.
- A table that spans pages comes out as two (one per page): join them before adding or comparing. Hyphenated words
  inside cells may come with a space, and a loose symbol may fall into the neighboring cell. Check number cells
  against the PDF. `examples/extract-catalog` in the repository shows the three cases.
- To cite, use the page in the JSON (`prov[0].page_no`): "(report.pdf, p. 7)".
- Check the result: a title, a table and a scanned page, if any. If something came out empty or scrambled, try
  `--ocr-mode full_page` or `--pdf-backend pypdfium2` and say what changed.

## Step 3: deliver

- Paths of `$J/src/extract/*.md`, `*.json` and the figures.
- Say what was left out or is low confidence: pages without text, broken tables, poor OCR.
- If the next step is a report, deck, video or brand, continue with `cutroom-studio` or the piece's skill, using the
  Markdown as the source of facts.

## MCP (optional, Claude Code only)

With the `docling-mcp` component, Claude Code has the `docling` server (`convert_document_into_docling_document`,
`export_docling_document_to_markdown`, `search_for_text_in_document_anchors`...), in the same local environment. Use
it for small documents or to search passages. For large documents use the CLI: the whole Markdown returned by the MCP
enters the context at once.
