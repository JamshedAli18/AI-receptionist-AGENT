import re
from pathlib import Path
from datetime import date
from pypdf import PdfReader

CATEGORY_MAP = {
    "appointments_faq.pdf": "appointments",
    "cancellation_policy_faq.pdf": "cancellation_policy",
    "insurance_billing_faq.pdf": "insurance_billing",
    "hours_faq.pdf": "hours",
    "new_patient_faq.pdf": "new_patient",
}

BUSINESS_ID = "brightpath_clinic"   # doubles as the Pinecone namespace


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_by_qa_section(text: str) -> list[str]:
    """
    Splits text into one chunk per Q&A section.
    Drops any section that isn't itself a Q&A block (e.g. the PDF's
    title/metadata header line, which sits before the first '?' heading).
    Falls back to word-based chunking if no question-style headings are found.
    """
    pattern = r'\n(?=[A-Z][^\n]{5,90}\?)'
    raw_sections = re.split(pattern, text.strip())

    chunks = []
    for section in raw_sections:
        section = section.strip()
        if len(section) < 30:
            continue
        first_line = section.split("\n", 1)[0]
        if "?" not in first_line:
            continue
        chunks.append(section)

    if len(chunks) == 0:
        return chunk_by_words(text)

    return chunks


def chunk_by_words(text: str, chunk_size: int = 400, overlap: int = 60) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def build_chunks_for_file(pdf_path: Path) -> list[dict]:
    filename = pdf_path.name
    category = CATEGORY_MAP.get(filename, "general")
    text = extract_text(pdf_path)
    raw_chunks = chunk_by_qa_section(text)

    records = []
    for i, chunk in enumerate(raw_chunks):
        records.append({
            "id": f"{category}-{i}",
            "text": chunk,
            "metadata": {
                "business_id": BUSINESS_ID,
                "category": category,
                "source_file": filename,
                "chunk_index": i,
                "active": True,
                "last_updated": str(date.today()),
            },
        })
    return records