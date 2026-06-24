# MarkDownConverter

A privacy-focused web app that converts PDF, DOCX, PPTX, and XLSX files to clean Markdown instantly. No signup, no file storage. Powered by [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

---

## Project structure

```
markitdown-project/
├── main.py                  # FastAPI application — all routes, validation, and conversion logic
├── requirements.txt         # Python dependencies
├── CLAUDE.md                # Instructions for Claude Code (AI assistant context)
│
├── templates/
│   ├── base.html            # Shared layout: <head>, header, footer, CSS, JS blocks
│   ├── index.html           # Main converter page (extends base.html)
│   ├── converter.html       # SEO landing pages per format, e.g. /pdf-to-markdown (extends base.html)
│   ├── privacy.html         # Privacy policy page (extends base.html)
│   └── terms.html           # Terms of service page (extends base.html)
│
└── static/
    ├── css/
    │   ├── style.css        # Global resets, component styles, responsive breakpoints
    │   └── inter.css        # Self-hosted Inter font via @font-face
    ├── fonts/               # Inter font files (.woff2)
    └── icons/
        ├── letra-m.png      # Favicon / app icon
        ├── pdf.svg          # Badge icon for PDF
        ├── word.svg         # Badge icon for Word/DOCX
        ├── excel.svg        # Badge icon for Excel/XLSX
        └── ppt.svg          # Badge icon for PowerPoint/PPTX
```

---

## Key files

| File | Purpose |
|---|---|
| `main.py` | Single-file FastAPI app. Defines all routes, `validate_file()`, `sanitize_filename()`, the `SEO_PAGES` dict, rate limiter, and the `/convert` endpoint. |
| `templates/base.html` | Master layout inherited by all pages. Contains the full CSS, header, footer (with license text and icon attribution), and `{% block %}` slots for title, meta, schema, content, and scripts. |
| `templates/index.html` | Main landing page at `/`. Has the upload drag-and-drop zone, preview section, and bento grid. |
| `templates/converter.html` | Reusable SEO page template for `/pdf-to-markdown`, `/docx-to-markdown`, `/pptx-to-markdown`, `/xlsx-to-markdown`. SEO content is hidden on load and revealed after a successful conversion. |
| `templates/privacy.html` | Static privacy policy page at `/privacy`. |
| `templates/terms.html` | Static terms of service page at `/terms`. |
| `static/css/style.css` | Shared styles: upload card, spinner, preview panel, error message, toast, bento grid. |
| `static/css/inter.css` | `@font-face` declarations for the self-hosted Inter typeface. |
| `requirements.txt` | All Python dependencies (FastAPI, Uvicorn, MarkItDown, SlowAPI, python-dotenv). |

---

## Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Main converter page |
| `GET` | `/favicon.ico` | Serves `static/icons/letra-m.png` |
| `GET` | `/privacy` | Privacy policy |
| `GET` | `/terms` | Terms of service |
| `GET` | `/{filetype}-to-markdown` | SEO landing page; `filetype` must be `pdf`, `docx`, `pptx`, or `xlsx` |
| `POST` | `/convert` | File upload and conversion endpoint (rate-limited: 10 req/min per IP) |

---

## Setup and running

### Prerequisites

- Python 3.10+
- `pip`

### Install

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Development server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or directly
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

### Environment variables

Create a `.env` file in the project root if needed (loaded automatically via `python-dotenv`). No required variables for basic use.

---

## How it works

1. The user uploads a file via drag-and-drop or file picker (`POST /convert`).
2. `validate_file()` checks extension, MIME type, and file size — all enforced before touching file content.
3. The file is read into `io.BytesIO` in memory (never written to disk) and passed to `MarkItDown.convert_stream()`.
4. The result is returned as JSON `{ markdown, filename }`.
5. The frontend displays a preview and offers copy / `.md` download — all client-side.

---

## Security notes

- Files are **never written to disk** — always processed via `io.BytesIO`.
- `sanitize_filename()` is called on every user-supplied filename.
- Triple validation (extension + MIME type + size) runs before any conversion.
- The `/convert` endpoint is rate-limited via `slowapi` (10 requests/min per IP).

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `python-multipart` | Multipart form / file upload parsing |
| `markitdown[all]` | Microsoft MarkItDown conversion engine |
| `slowapi` | Rate limiting for FastAPI |
| `python-dotenv` | `.env` file loading |

---

## License

This project is an independent work and is not affiliated with Microsoft.
Microsoft MarkItDown is licensed under the MIT License — © Microsoft Corporation.