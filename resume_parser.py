import re

import fitz  # PyMuPDF
import pdfplumber


def clean_text(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_with_pymupdf(pdf_path):
    text_parts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def extract_with_pdfplumber(pdf_path):
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def extract_resume_text(pdf_path):
    full_text = ""

    try:
        full_text = extract_with_pymupdf(pdf_path)
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")

    if not full_text or len(full_text.strip()) < 50:
        try:
            full_text = extract_with_pdfplumber(pdf_path)
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")

    cleaned = clean_text(full_text)

    print(f"\n[DEBUG] Resume parsed from: {pdf_path}")
    print(f"[DEBUG] Extracted text length: {len(cleaned)}")
    print(f"[DEBUG] Preview: {cleaned[:300]}")

    if len(cleaned) < 50:
        print("⚠️ Warning: Very little text extracted. This PDF may be scanned/image-based.")

    return cleaned