"""Extract plain text from supported local documents."""

from __future__ import annotations
from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf"}


def extract_text(file_path: str | Path) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError("The selected document no longer exists.")

    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Please choose a .txt, .docx or .pdf document.")

    if extension == ".txt":
        for encoding in ("utf-8-sig", "utf-16", "cp1252", "latin-1"):
            try:
                content = path.read_text(encoding=encoding)
                # UTF-16 attempt sometimes decodes text only if real BOM is
                # present; reject excess NULs from an incorrect encoding.
                if "\x00" not in content:
                    return content
            except UnicodeError:
                pass
        raise ValueError("Could not decode the selected TXT file.")

    if extension == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("Install DOCX support: python -m pip install python-docx") from exc
        try:
            document = Document(str(path))
            # Compatible with python-docx 1.1+. Collect paragraphs and tables.
            parts = [paragraph.text for paragraph in document.paragraphs]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            return "\n".join(parts)
        except Exception as exc:
            raise ValueError(f"Unable to read this DOCX file: {exc}") from exc

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install PDF support: python -m pip install pypdf") from exc
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ValueError("Password-protected PDFs must be unlocked first.")
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to read this PDF file: {exc}") from exc
