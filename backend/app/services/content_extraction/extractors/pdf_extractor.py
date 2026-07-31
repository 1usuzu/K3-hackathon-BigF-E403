import io
import re
from typing import List, Optional
import pypdf

from backend.app.services.content_extraction.extractors.base_extractor import (
    BaseContentExtractor, ExtractedBlockData
)
from backend.app.services.content_extraction.prompt_injection_detector import PromptInjectionDetector

class PDFContentExtractor(BaseContentExtractor):
    async def extract_blocks(
        self,
        file_bytes: bytes,
        document_id: str,
        document_version_id: str,
        lesson_id: Optional[str] = None
    ) -> List[ExtractedBlockData]:
        extracted_blocks: List[ExtractedBlockData] = []
        seq = 1

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
        except Exception as e:
            # Whole document unreadable/corrupt handling
            return [
                ExtractedBlockData(
                    block_type="note",
                    raw_content="",
                    normalized_content=f"[ERR_PDF_CORRUPT: Entire PDF file unreadable] {str(e)}",
                    language="vi",
                    sequence_number=1,
                    metadata={"error": str(e), "corrupt_file": True},
                    extraction_confidence=0.0,
                    source_reference="Document"
                )
            ]

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                text = page.extract_text() or ""
                lines = [l for l in text.split("\n") if l.strip()]

                # Filter out obvious repetitive page footer/header numbers like "Page 1 of 83" or "Trang 1"
                cleaned_lines = []
                for line in lines:
                    if re.match(r"^(Page|Trang)\s+\d+(\s+of|\s*/)\s*\d+$", line.strip(), re.IGNORECASE):
                        continue
                    cleaned_lines.append(line)

                if not cleaned_lines:
                    continue

                page_text = "\n".join(cleaned_lines)
                
                # Check Prompt Injection
                has_inj, inj_signals = PromptInjectionDetector.detect(page_text)

                # Identify block type heuristics (formula, code, heading, paragraph)
                block_type = "paragraph"
                if re.search(r"(\$\$|\\[a-zA-Z]+|\{equation\}|\$\\sum|\$\\int)", page_text):
                    block_type = "formula"
                elif re.search(r"(def\s+\w+|class\s+\w+|import\s+\w+|public\s+class|function\s+\w+)", page_text) or any(line.startswith("    ") or line.startswith("\t") for line in cleaned_lines):
                    block_type = "code"
                elif len(cleaned_lines) == 1 and len(cleaned_lines[0]) < 80 and cleaned_lines[0].isupper():
                    block_type = "heading"

                metadata = {
                    "has_prompt_injection": has_inj,
                    "prompt_injection_signals": inj_signals,
                    "total_pages": total_pages
                }

                extracted_blocks.append(
                    ExtractedBlockData(
                        block_type=block_type,
                        raw_content=text,
                        normalized_content=page_text,
                        language="vi",
                        page_number=page_num,
                        sequence_number=seq,
                        metadata=metadata,
                        extraction_confidence=0.95,
                        source_reference=f"Page {page_num}"
                    )
                )
                seq += 1
            except Exception as page_err:
                # Partial Failure Isolation (Req 12): Single page failure does NOT break entire doc!
                extracted_blocks.append(
                    ExtractedBlockData(
                        block_type="note",
                        raw_content="",
                        normalized_content=f"[ERR_PAGE_EXTRACTION_FAILED: Page {page_num}] {str(page_err)}",
                        language="vi",
                        page_number=page_num,
                        sequence_number=seq,
                        metadata={"error": str(page_err), "partial_failure": True},
                        extraction_confidence=0.1,  # Low confidence marker for unconfident/failed extraction
                        source_reference=f"Page {page_num}"
                    )
                )
                seq += 1

        return extracted_blocks
