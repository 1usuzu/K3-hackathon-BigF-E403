import re
from typing import List, Optional

from backend.app.services.content_extraction.extractors.base_extractor import (
    BaseContentExtractor, ExtractedBlockData
)
from backend.app.services.content_extraction.prompt_injection_detector import PromptInjectionDetector

class TextMarkdownContentExtractor(BaseContentExtractor):
    async def extract_blocks(
        self,
        file_bytes: bytes,
        document_id: str,
        document_version_id: str,
        lesson_id: Optional[str] = None
    ) -> List[ExtractedBlockData]:
        extracted_blocks: List[ExtractedBlockData] = []
        text = file_bytes.decode("utf-8", errors="replace")
        seq = 1

        # 1. Split code blocks (fenced code blocks ```lang ... ```)
        code_block_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
        
        # We will parse section by section
        pos = 0
        for match in code_block_pattern.finditer(text):
            start, end = match.span()
            # Non-code text preceding the code block
            preceding_text = text[pos:start].strip()
            if preceding_text:
                blocks = self._parse_markdown_text(preceding_text, seq)
                extracted_blocks.extend(blocks)
                seq += len(blocks)

            # Code block itself (Preserve indentation - Req 4)
            code_lang = match.group(1) or "code"
            code_content = match.group(2)  # Keep exact raw content & indentation!
            has_inj, inj_signals = PromptInjectionDetector.detect(code_content)

            extracted_blocks.append(
                ExtractedBlockData(
                    block_type="code",
                    raw_content=match.group(0),
                    normalized_content=code_content,
                    language="vi",
                    sequence_number=seq,
                    metadata={
                        "code_language": code_lang,
                        "has_prompt_injection": has_inj,
                        "prompt_injection_signals": inj_signals
                    },
                    extraction_confidence=1.0,
                    source_reference="Code Snippet"
                )
            )
            seq += 1
            pos = end

        # Remaining text after last code block
        remaining_text = text[pos:].strip()
        if remaining_text:
            blocks = self._parse_markdown_text(remaining_text, seq)
            extracted_blocks.extend(blocks)

        return extracted_blocks

    def _parse_markdown_text(self, text_segment: str, start_seq: int) -> List[ExtractedBlockData]:
        blocks = []
        seq = start_seq
        paragraphs = text_segment.split("\n\n")

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            has_inj, inj_signals = PromptInjectionDetector.detect(p_clean)
            metadata = {"has_prompt_injection": has_inj, "prompt_injection_signals": inj_signals}

            # 1. Heading check
            if p_clean.startswith(("# ", "## ", "### ", "#### ")):
                blocks.append(
                    ExtractedBlockData(
                        block_type="heading",
                        raw_content=p_clean,
                        normalized_content=p_clean.lstrip("#").strip(),
                        sequence_number=seq,
                        metadata=metadata,
                        extraction_confidence=1.0
                    )
                )
            # 2. Formula check (Req 5: Preserve math formulas)
            elif "$$" in p_clean or p_clean.startswith("\\begin{") or re.search(r"\$[^\$]+\$", p_clean):
                blocks.append(
                    ExtractedBlockData(
                        block_type="formula",
                        raw_content=p_clean,
                        normalized_content=p_clean,
                        sequence_number=seq,
                        metadata=metadata,
                        extraction_confidence=1.0
                    )
                )
            # 3. Table check
            elif "|" in p_clean and "\n" in p_clean:
                blocks.append(
                    ExtractedBlockData(
                        block_type="table",
                        raw_content=p_clean,
                        normalized_content=p_clean,
                        sequence_number=seq,
                        metadata=metadata,
                        extraction_confidence=0.9
                    )
                )
            # 4. List check
            elif p_clean.startswith(("- ", "* ", "1. ", "2. ")):
                blocks.append(
                    ExtractedBlockData(
                        block_type="list",
                        raw_content=p_clean,
                        normalized_content=p_clean,
                        sequence_number=seq,
                        metadata=metadata,
                        extraction_confidence=1.0
                    )
                )
            else:
                blocks.append(
                    ExtractedBlockData(
                        block_type="paragraph",
                        raw_content=p_clean,
                        normalized_content=p_clean,
                        sequence_number=seq,
                        metadata=metadata,
                        extraction_confidence=1.0
                    )
                )
            seq += 1

        return blocks
