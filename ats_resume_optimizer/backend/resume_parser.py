import io
import pdfplumber
import docx2txt
from fastapi import UploadFile


async def parse_resume(file: UploadFile) -> str:
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return _parse_pdf(content)
    elif filename.endswith(".docx"):
        return _parse_docx(content)
    elif filename.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def _parse_pdf(content: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def _parse_docx(content: bytes) -> str:
    return docx2txt.process(io.BytesIO(content))
