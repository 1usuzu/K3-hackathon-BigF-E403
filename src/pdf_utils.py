"""
pdf_utils.py — Smart PDF extraction for VLearn agent.

Strategy:
1. Read ALL pages (no arbitrary 10-page cap).
2. Skip low-value slides: cover/bio pages (very short or containing only metadata keywords).
3. Group content slides into sections using section-header slides ("PHẦN", "PART", "CHAPTER").
4. Return a structured text that preserves section boundaries so the agent
   can build an accurate Mindmap with sections as branches.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

# Slide is considered "metadata only" if it matches these patterns
_METADATA_PATTERNS = [
    r"(?i)instructor\s*:",        # anywhere in slide = cover/bio
    r"(?i)giảng viên\s*:",
    r"(?i)linkedin\s*\|",
    r"(?i)facebook\s*\|",
    r"(?i)^\s*q\s*&\s*a\s*$",
    r"(?i)^hẹn gặp lại",
    r"(?i)^nghỉ giải lao",
    r"(?i)^cảm ơn",
    r"(?i)^thank you",
]

# Section-divider slides (these become branch labels in the Mindmap)
_SECTION_PATTERNS = [
    r"(?i)^phần\s+\d+",
    r"(?i)^part\s+\d+",
    r"(?i)^chapter\s+\d+",
    r"(?i)^module\s+\d+",
    r"(?i)^chương\s+\d+",
]

# Minimum chars for a slide to be considered content-bearing
_MIN_CONTENT_CHARS = 80


class Section(NamedTuple):
    title: str
    pages: list[int]      # 1-indexed page numbers
    content: str


def _is_metadata_slide(text: str) -> bool:
    """True if the slide is cover / bio / admin with no learning content."""
    if not text or len(text.strip()) < 20:
        return True
    # Check metadata keyword patterns anywhere in the slide
    for pat in _METADATA_PATTERNS:
        if re.search(pat, text):
            return True
    return False


def _is_section_header(text: str) -> bool:
    """True if slide is a section-divider (e.g. 'PHẦN 01 — Bức tranh AI')."""
    for pat in _SECTION_PATTERNS:
        if re.match(pat, text.strip()):
            return True
    return False


def extract_structured_text(pdf_path: str | Path, max_chars: int = 100000) -> str:
    """
    Extract and structure text from a PDF for agent consumption.

    Returns a string like:
        [Agenda]
        • Topic 1
        • Topic 2

        [PHẦN 01 — Bức tranh AI]
        Slide 5: AI, ML, Deep Learning ...
        Slide 6: ...

        [PHẦN 02 — Lịch sử AI]
        ...

    Capped at `max_chars` to stay within LLM context limits.
    """
    from pypdf import PdfReader  # lazy import — not always needed

    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)

    # ── 1. Extract all page texts ──────────────────────────────────────────
    pages: list[tuple[int, str]] = []  # (page_number_1indexed, text)
    for i in range(total):
        raw = reader.pages[i].extract_text() or ""
        # Clean up weird unicode chars from slide exports
        raw = re.sub(r"[\ue000-\uf8ff]", "", raw).strip()
        if raw:
            pages.append((i + 1, raw))

    # ── 2. Separate agenda, section headers, and content slides ───────────
    agenda_text = ""
    sections: list[dict] = []   # {title, slides: [(page, text)]}
    current_section: dict | None = None
    orphan_slides: list[tuple[int, str]] = []  # slides before first section

    for page_num, text in pages:
        if _is_metadata_slide(text):
            continue  # skip cover, bio, Q&A, etc.

        # Detect Agenda slide
        if re.search(r"(?i)\bagenda\b|\bnội dung\b|\boutline\b", text[:120]):
            agenda_text = text
            continue

        # Detect section header
        if _is_section_header(text) and len(text) < 250:
            current_section = {"title": text.replace("\n", " ").strip(), "slides": []}
            sections.append(current_section)
            continue

        # Content slide
        if len(text) >= _MIN_CONTENT_CHARS and not _is_metadata_slide(text):
            if current_section is not None:
                current_section["slides"].append((page_num, text))
            else:
                orphan_slides.append((page_num, text))

    # ── 3. Build structured output ─────────────────────────────────────────
    parts: list[str] = []

    if agenda_text:
        parts.append(f"[Agenda — Nội dung buổi học]\n{agenda_text}")

    # Orphan slides (before first section) go into a generic section
    if orphan_slides:
        block = "\n\n".join(f"Slide {p}:\n{t}" for p, t in orphan_slides[:8])
        parts.append(f"[Nội dung]\n{block}")

    for sec in sections:
        if not sec["slides"]:
            # Section header with no content slides — include just the title
            parts.append(f"[{sec['title']}]\n(Xem slide gốc)")
            continue
        slides_text = "\n\n".join(
            f"Slide {p}:\n{t}" for p, t in sec["slides"]
        )
        parts.append(f"[{sec['title']}]\n{slides_text}")

    result = "\n\n---\n\n".join(parts)

    # ── 4. Cap total length ────────────────────────────────────────────────
    if len(result) > max_chars:
        result = result[:max_chars] + "\n\n[... nội dung bị cắt bớt để giới hạn token ...]"

    return result or "[Không trích xuất được nội dung từ file PDF này.]"


def extract_pages_text(pdf_path: str | Path, page_numbers: list[int]) -> str:
    """Extract specific pages (1-indexed). Used for section flashcard gen."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    parts = []
    for pn in page_numbers:
        idx = pn - 1
        if 0 <= idx < total:
            raw = reader.pages[idx].extract_text() or ""
            raw = re.sub(r"[\ue000-\uf8ff]", "", raw).strip()
            if raw:
                parts.append(f"Slide {pn}:\n{raw}")
    return "\n\n".join(parts) or "[Không có nội dung trích xuất được.]"
