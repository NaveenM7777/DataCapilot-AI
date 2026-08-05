import os
from pypdf import PdfReader


DEFAULT_PDF_PATH = os.path.join("data", "company_doc.pdf")


def get_file_modified_time():
    """Returns the file's last-modified timestamp, or None if it doesn't exist."""

    if not os.path.exists(DEFAULT_PDF_PATH):
        return None

    return os.path.getmtime(DEFAULT_PDF_PATH)


def extract_text_from_pdf(file_obj):

    try:
        reader = PdfReader(file_obj)

        page_texts = []

        for page in reader.pages:
            text = page.extract_text() or ""
            page_texts.append(text)

        full_text = "\n\n".join(page_texts)

        if not full_text.strip():
            return None, None, None, (
                "No extractable text found. This PDF may be scanned/image-based "
                "and would need OCR, which isn't supported yet."
            )

        return full_text, page_texts, len(reader.pages), None

    except Exception as e:
        return None, None, None, f"Failed to read PDF: {str(e)}"


def load_default_pdf():
    """
    Loads the company PDF fresh from disk every time it's called, so
    updates to the file are picked up automatically without restarting.
    """

    if not os.path.exists(DEFAULT_PDF_PATH):
        return None, None, None, (
            f"PDF not found at '{DEFAULT_PDF_PATH}'. "
            "Place your company PDF there and restart the app."
        )

    with open(DEFAULT_PDF_PATH, "rb") as f:
        return extract_text_from_pdf(f)


def chunk_text(page_texts, chunk_size=1500, overlap=200):

    chunks = []

    for page_num, text in enumerate(page_texts, start=1):

        if not text.strip():
            continue

        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            chunks.append({"text": chunk, "pages": [page_num]})

            start = end - overlap

    return chunks