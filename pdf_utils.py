"""Extract text from an uploaded PDF CV."""
from pypdf import PdfReader

MAX_CHARS = 8000  # keep prompts small (and quota-friendly)


def extract_pdf_text(file) -> str:
    """Return the text of a PDF (path or file-like object). Empty string if none found."""
    reader = PdfReader(file)
    pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(pages).strip()
    return text[:MAX_CHARS]