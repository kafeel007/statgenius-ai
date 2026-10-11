"""PDF validation and text extraction (PyMuPDF). Returns per-page text so sources can cite page numbers."""
MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 60

class DocumentError(ValueError): pass

def validate_pdf_bytes(data: bytes, filename: str):
    if not filename.lower().endswith(".pdf"): raise DocumentError("Only .pdf files are supported")
    if len(data) == 0: raise DocumentError("The file is empty")
    if len(data) > MAX_BYTES: raise DocumentError(f"File too large (limit {MAX_BYTES // (1024*1024)} MB)")
    if not data.startswith(b"%PDF-"): raise DocumentError("File content is not a valid PDF")

def extract_pages(data: bytes):
    """Return list of (page_number, text). Raises DocumentError for corrupt/scanned PDFs."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise DocumentError("PyMuPDF is not installed on the server (pip install pymupdf)")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        raise DocumentError("Could not open the PDF (corrupt or encrypted)")
    if doc.page_count > MAX_PAGES: raise DocumentError(f"Too many pages (limit {MAX_PAGES})")
    pages = [(i + 1, doc[i].get_text("text").strip()) for i in range(doc.page_count)]
    if sum(len(t) for _, t in pages) < 40:
        raise DocumentError("No extractable text found. This looks like a scanned PDF; OCR processing is required "
                            "and is not available in this prototype.")
    return pages

def preview(pages, n=1200):
    full = "\n\n".join(f"[Page {p}]\n{t}" for p, t in pages if t)
    return full[:n] + ("..." if len(full) > n else "")
