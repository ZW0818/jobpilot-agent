from io import BytesIO

from fastapi import UploadFile


async def extract_text_from_upload(upload: UploadFile) -> str:
    content = await upload.read()
    filename = (upload.filename or "").lower()

    if filename.endswith(".pdf"):
        return _extract_pdf_text(content)
    if filename.endswith(".docx"):
        return _extract_docx_text(content)
    return _decode_text(content)


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return _decode_text(content)

    try:
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return _decode_text(content)


def _extract_docx_text(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        return _decode_text(content)

    try:
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception:
        return _decode_text(content)
