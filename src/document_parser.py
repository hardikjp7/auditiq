# /workspace/shared/audit_validator/src/document_parser.py

import re
import pdfplumber
from pypdf import PdfReader
from pathlib import Path

def parse_pdf(filepath: str) -> dict:
    """
    Extract text from PDF with metadata.
    Returns dict with full_text, pages, word_count, char_count.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    result = {
        "filename"   : filepath.name,
        "filepath"   : str(filepath),
        "pages"      : [],
        "full_text"  : "",
        "word_count" : 0,
        "char_count" : 0,
        "page_count" : 0
    }

    # Primary: pdfplumber (better for tables + structured docs)
    try:
        with pdfplumber.open(filepath) as pdf:
            result["page_count"] = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                text = clean_text(text)
                result["pages"].append({
                    "page_num" : i + 1,
                    "text"     : text,
                    "char_len" : len(text)
                })
        result["full_text"] = "\n\n".join(p["text"] for p in result["pages"])

    except Exception:
        # Fallback: pypdf
        reader = PdfReader(filepath)
        result["page_count"] = len(reader.pages)
        for i, page in enumerate(reader.pages):
            text = clean_text(page.extract_text() or "")
            result["pages"].append({"page_num": i+1, "text": text, "char_len": len(text)})
        result["full_text"] = "\n\n".join(p["text"] for p in result["pages"])

    result["word_count"] = len(result["full_text"].split())
    result["char_count"] = len(result["full_text"])
    return result


def parse_text_file(filepath: str) -> dict:
    """Parse plain .txt files"""
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)
    return {
        "filename"   : filepath.name,
        "filepath"   : str(filepath),
        "full_text"  : text,
        "pages"      : [{"page_num": 1, "text": text, "char_len": len(text)}],
        "word_count" : len(text.split()),
        "char_count" : len(text),
        "page_count" : 1
    }


def parse_document(filepath: str) -> dict:
    """Auto-detect file type and parse"""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(filepath)
    elif ext in [".txt", ".md"]:
        return parse_text_file(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .txt, .md")


def chunk_document(doc: dict, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Split document text into overlapping chunks for RAG.
    Returns list of dicts with chunk text + metadata.
    """
    words = doc["full_text"].split()
    chunks = []
    start  = 0
    idx    = 0

    while start < len(words):
        end        = min(start + chunk_size, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append({
            "chunk_id"    : f"{doc['filename']}_chunk_{idx}",
            "source_file" : doc["filename"],
            "chunk_index" : idx,
            "text"        : chunk_text,
            "word_count"  : len(chunk_text.split()),
            "start_word"  : start,
            "end_word"    : end
        })
        start += chunk_size - overlap
        idx   += 1

    return chunks


def clean_text(text: str) -> str:
    """Remove junk characters, normalize whitespace"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'(\n\s*){3,}', '\n\n', text)
    return text.strip()