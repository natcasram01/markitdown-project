import os
import io
import re
import sys
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from markitdown import MarkItDown
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32" or not Path("/data").exists():
    COUNTER_FILE = Path("counter.json")
else:
    COUNTER_FILE = Path("/data/counter.json")


def read_counter() -> int:
    try:
        if COUNTER_FILE.exists():
            data = json.loads(COUNTER_FILE.read_text())
            return data.get("total", 0)
        return 0
    except Exception:
        return 0


def increment_counter() -> int:
    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        count = read_counter() + 1
        COUNTER_FILE.write_text(json.dumps({"total": count}))
        return count
    except Exception:
        return 0


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "20971520"))
RATE_LIMIT = os.getenv("RATE_LIMIT", "10/minute")
LOG_LEVEL = os.getenv("LOG_LEVEL", "error")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

SEO_PAGES = {
    "pdf": {
        "title": "Convert PDF to Markdown Online Free | Fast & Private",
        "meta_description": "Convert PDF to clean Markdown instantly. No signup, no storage, and privacy-focused processing. Fast, accurate and free online tool.",
        "h1": "Convert PDF to Markdown",
        "h2_1": "Fast PDF to Markdown conversion",
        "h2_2": "Why use our PDF to Markdown tool?",
        "h2_3": "How it works",
        "description": "Upload your PDF file and convert it into clean, structured Markdown in seconds. Tables, headings, and formatting are preserved for easy reuse.",
        "schema_name": "PDF to Markdown Converter",
        "schema_description": "Convert PDF files to Markdown instantly with structure preservation.",
        "format": "PDF",
        "use_cases": ["Documentation", "Research papers", "Technical files"]
    },
    "docx": {
        "title": "Convert Word (DOCX) to Markdown Online | Free & Secure",
        "meta_description": "Convert DOCX files to Markdown instantly. Preserve formatting, headings, and lists. No signup required and files are not stored.",
        "h1": "Convert DOCX to Markdown",
        "h2_1": "Fast Word to Markdown conversion",
        "h2_2": "Why use our DOCX to Markdown tool?",
        "h2_3": "How it works",
        "description": "Turn your Word documents into clean Markdown. Perfect for documentation, blogs, and content workflows.",
        "schema_name": "DOCX to Markdown Converter",
        "schema_description": "Convert Word documents to Markdown instantly with formatting preserved.",
        "format": "DOCX",
        "use_cases": ["Documentation", "Blog posts", "Content workflows"]
    },
    "pptx": {
        "title": "Convert PowerPoint (PPTX) to Markdown Online",
        "meta_description": "Convert PowerPoint slides into Markdown format quickly. Extract structured content from presentations in seconds.",
        "h1": "Convert PPTX to Markdown",
        "h2_1": "Fast PowerPoint to Markdown conversion",
        "h2_2": "Why use our PPTX to Markdown tool?",
        "h2_3": "How it works",
        "description": "Extract content from PowerPoint slides and convert it into structured Markdown for easy editing and reuse.",
        "schema_name": "PPTX to Markdown Converter",
        "schema_description": "Convert PowerPoint slides into structured Markdown in seconds.",
        "format": "PPTX",
        "use_cases": ["Presentations", "Slide notes", "Content repurposing"]
    },
    "xlsx": {
        "title": "Convert Excel (XLSX) to Markdown Tables Online",
        "meta_description": "Convert Excel files into Markdown tables instantly. Clean output, no signup, and privacy-focused processing.",
        "h1": "Convert XLSX to Markdown",
        "h2_1": "Fast Excel to Markdown conversion",
        "h2_2": "Why use our XLSX to Markdown tool?",
        "h2_3": "How it works",
        "description": "Transform Excel spreadsheets into Markdown tables. Ideal for documentation, reports, and data sharing.",
        "schema_name": "XLSX to Markdown Converter",
        "schema_description": "Convert Excel spreadsheets into Markdown tables instantly.",
        "format": "XLSX",
        "use_cases": ["Data tables", "Reports", "Documentation"]
    }
}

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://plausible.io; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self' https://plausible.io; "
            "frame-ancestors 'none';"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Static files y templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuración
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".pptx"}
MAX_FILE_SIZES = {
    ".pdf":  20 * 1024 * 1024,   # 20 MB
    ".docx": 20 * 1024 * 1024,   # 20 MB
    ".xlsx": 10 * 1024 * 1024,   # 10 MB
    ".xls":  10 * 1024 * 1024,   # 10 MB
    ".pptx": 20 * 1024 * 1024,   # 20 MB
}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def sanitize_filename(filename: str) -> str:
    """Elimina caracteres peligrosos del nombre del archivo."""
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = filename.strip()
    filename = filename[:255]
    return filename or "archivo"


def validate_content_safety(content: bytes, ext: str) -> None:
    """Comprueba firmas de archivo para verificar que coinciden
    con la extensión declarada."""
    signatures = {
        ".pdf":  [b"%PDF"],
        ".docx": [b"PK\x03\x04"],
        ".xlsx": [b"PK\x03\x04"],
        ".xls":  [b"\xd0\xcf\x11\xe0"],
        ".pptx": [b"PK\x03\x04"],
    }
    expected = signatures.get(ext, [])
    if expected and not any(content.startswith(sig) for sig in expected):
        raise HTTPException(
            status_code=400,
            detail="El contenido del archivo no coincide con su extensión."
        )


def validate_file(file: UploadFile, content: bytes) -> str:
    """Valida extensión, MIME type y tamaño. Devuelve la extensión."""
    filename = sanitize_filename(file.filename or "")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido. Usa: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido."
        )

    max_size = MAX_FILE_SIZES.get(ext, 20 * 1024 * 1024)
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo permitido: {max_size // (1024 * 1024)} MB"
        )

    return ext


# ── Rutas ──────────────────────────────────────────────────────────────────────

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/icons/letra-m.png", media_type="image/png")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html")


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html")


@app.get("/counter")
async def get_counter():
    return {"total": read_counter()}


@app.get("/{filetype}-to-markdown", response_class=HTMLResponse)
async def seo_page(request: Request, filetype: str):
    if filetype not in SEO_PAGES:
        raise HTTPException(status_code=404, detail="Page not found")
    return templates.TemplateResponse(
        request=request,
        name="converter.html",
        context={"page": SEO_PAGES[filetype]}
    )


@app.post("/convert")
@limiter.limit(RATE_LIMIT)
async def convert(request: Request, file: UploadFile = File(...)):
    """
    Convierte un archivo a Markdown.
    - Procesado en memoria: el archivo nunca se guarda en disco.
    - Sin metadatos en la salida.
    - Rate limiting: 10 peticiones por minuto por IP.
    """
    content = await file.read()

    ext = validate_file(file, content)
    validate_content_safety(content, ext)

    try:
        md = MarkItDown()
        stream = io.BytesIO(content)
        stream.name = f"file{ext}"
        result = md.convert_stream(stream)
        markdown_text = result.text_content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error al convertir el archivo. Comprueba que el archivo no está dañado."
        )

    safe_name = sanitize_filename(file.filename or "archivo")
    output_filename = os.path.splitext(safe_name)[0] + ".md"
    count = increment_counter()

    return JSONResponse(content={
        "markdown": markdown_text,
        "filename": output_filename,
        "total_conversions": count,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
        access_log=False,
        log_level=LOG_LEVEL,
    )