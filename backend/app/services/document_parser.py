import csv
import json
from pathlib import Path

import docx
import pypdf

from app.core.logging import get_logger

logger = get_logger(__name__)

class DocumentParser:
    """Extracts text content from various file formats."""

    @staticmethod
    def parse(file_path: Path, content_type: str) -> str:
        """Parse a file and return its textual content."""
        if not file_path.exists():
            return ""

        ext = file_path.suffix.lower()
        
        try:
            if ext == ".pdf":
                return DocumentParser._parse_pdf(file_path)
            elif ext == ".docx":
                return DocumentParser._parse_docx(file_path)
            elif ext == ".csv":
                return DocumentParser._parse_csv(file_path)
            elif ext == ".json":
                return DocumentParser._parse_json(file_path)
            elif ext in [".txt", ".md"]:
                return DocumentParser._parse_text(file_path)
            else:
                logger.warning(f"Unsupported document parsing for extension: {ext}")
                return ""
        except Exception as e:
            logger.error(f"Error parsing document {file_path.name}: {e}", exc_info=True)
            return f"[Error parsing document: {e!s}]"

    @staticmethod
    def _parse_pdf(file_path: Path) -> str:
        text = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text.append(f"--- [Page {idx}] ---\n{page_text.strip()}")
        return "\n\n".join(text)

    @staticmethod
    def _parse_docx(file_path: Path) -> str:
        doc = docx.Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    @staticmethod
    def _parse_csv(file_path: Path) -> str:
        text = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for row in reader:
                text.append(",".join(row))
        return "\n".join(text)

    @staticmethod
    def _parse_json(file_path: Path) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return json.dumps(data, indent=2)

    @staticmethod
    def _parse_text(file_path: Path) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
