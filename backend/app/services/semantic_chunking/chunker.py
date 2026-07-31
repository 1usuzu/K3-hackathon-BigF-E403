import re
import math
from typing import List, Optional, Dict, Any, Tuple
from backend.app.models.document import ContentBlock
from backend.app.services.semantic_chunking.chunk_dto import SemanticChunkData

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    words = text.split()
    return math.ceil(len(words) * 1.3)

class SemanticChunker:
    def __init__(
        self,
        max_tokens: int = 500,
        min_tokens: int = 40,
        overlap_tokens: int = 30
    ):
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_blocks(
        self,
        blocks: List[ContentBlock],
        document_id: str,
        document_version_id: str,
        known_glossary_terms: Optional[List[str]] = None
    ) -> List[SemanticChunkData]:
        if not blocks:
            return []

        known_terms = known_glossary_terms or []
        chunks: List[SemanticChunkData] = []
        
        # 1. Group blocks by Lesson (Strict Rule: Never mix content from two different lessons)
        lesson_groups: Dict[Optional[str], List[ContentBlock]] = {}
        for block in blocks:
            les_id = block.lesson_id
            if les_id not in lesson_groups:
                lesson_groups[les_id] = []
            lesson_groups[les_id].append(block)

        global_seq = 1

        for les_id, les_blocks in lesson_groups.items():
            # 2. Group blocks by Parent Heading / Section
            sections = self._group_by_sections(les_blocks)

            for section_title, sec_blocks in sections:
                # 3. Create semantic chunks for each section
                sec_chunks = self._chunk_section_blocks(
                    sec_blocks,
                    document_id=document_id,
                    document_version_id=document_version_id,
                    lesson_id=les_id,
                    section_title=section_title,
                    known_terms=known_terms
                )

                for chunk in sec_chunks:
                    chunk.sequence_number = global_seq
                    chunk.checksum = chunk.compute_checksum()
                    chunks.append(chunk)
                    global_seq += 1

        # 4. Generate semantic overlap summary between consecutive chunks
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            prev_snippet = prev_chunk.content[-150:].strip() if len(prev_chunk.content) > 150 else prev_chunk.content
            chunks[i].overlap_summary = f"[Overlap from Prev Chunk #{prev_chunk.sequence_number}]: {prev_snippet}"

        return chunks

    def _group_by_sections(self, blocks: List[ContentBlock]) -> List[Tuple[str, List[ContentBlock]]]:
        sections: List[Tuple[str, List[ContentBlock]]] = []
        current_title = "Giới thiệu chung"
        current_blocks: List[ContentBlock] = []

        for block in blocks:
            if block.block_type == "heading":
                if current_blocks:
                    sections.append((current_title, current_blocks))
                    current_blocks = []
                current_title = block.normalized_content.strip()
            current_blocks.append(block)

        if current_blocks:
            sections.append((current_title, current_blocks))

        return sections

    def _chunk_section_blocks(
        self,
        blocks: List[ContentBlock],
        document_id: str,
        document_version_id: str,
        lesson_id: Optional[str],
        section_title: str,
        known_terms: List[str]
    ) -> List[SemanticChunkData]:
        # Atomic grouping: Attach formulas/code to surrounding explanation/heading blocks
        atomic_units = self._build_atomic_units(blocks)

        chunks: List[SemanticChunkData] = []
        current_unit_blocks: List[ContentBlock] = []
        current_tokens = 0

        for unit in atomic_units:
            unit_text = "\n\n".join(b.normalized_content for b in unit)
            unit_tokens = estimate_tokens(unit_text)

            # If unit itself exceeds max_tokens, split it while trying to keep code/formula intact
            if unit_tokens > self.max_tokens:
                if current_unit_blocks:
                    chunks.append(self._build_chunk_dto(
                        current_unit_blocks, document_id, document_version_id, lesson_id, section_title, known_terms
                    ))
                    current_unit_blocks = []
                    current_tokens = 0

                # Split large unit
                split_chunks = self._split_oversized_unit(unit, document_id, document_version_id, lesson_id, section_title, known_terms)
                chunks.extend(split_chunks)
                continue

            if current_tokens + unit_tokens > self.max_tokens and current_unit_blocks:
                chunks.append(self._build_chunk_dto(
                    current_unit_blocks, document_id, document_version_id, lesson_id, section_title, known_terms
                ))
                current_unit_blocks = list(unit)
                current_tokens = unit_tokens
            else:
                current_unit_blocks.extend(unit)
                current_tokens += unit_tokens

        if current_unit_blocks:
            # If undersized final chunk can be merged into previous chunk within same section
            if current_tokens < self.min_tokens and chunks:
                last_chunk = chunks[-1]
                merged_blocks_content = last_chunk.content + "\n\n" + "\n\n".join(b.normalized_content for b in current_unit_blocks)
                if estimate_tokens(merged_blocks_content) <= self.max_tokens:
                    last_chunk.content = merged_blocks_content
                    last_chunk.token_estimate = estimate_tokens(merged_blocks_content)
                    last_chunk.content_block_ids.extend([b.id for b in current_unit_blocks if hasattr(b, "id") and b.id])
                else:
                    chunks.append(self._build_chunk_dto(
                        current_unit_blocks, document_id, document_version_id, lesson_id, section_title, known_terms
                    ))
            else:
                chunks.append(self._build_chunk_dto(
                    current_unit_blocks, document_id, document_version_id, lesson_id, section_title, known_terms
                ))

        return chunks

    def _build_atomic_units(self, blocks: List[ContentBlock]) -> List[List[ContentBlock]]:
        """
        Groups formula blocks with preceding/following explanation paragraphs,
        and code blocks with preceding headings/paragraphs to prevent atomic splitting.
        """
        units: List[List[ContentBlock]] = []
        i = 0
        n = len(blocks)

        while i < n:
            curr = blocks[i]
            unit = [curr]

            # If current block is formula or code, attach next paragraph if it's an explanation
            if curr.block_type in ["formula", "code"]:
                if i + 1 < n and blocks[i + 1].block_type in ["paragraph", "note"]:
                    unit.append(blocks[i + 1])
                    i += 1
            # If current block is heading/paragraph and next block is formula or code, group them together
            elif curr.block_type in ["heading", "paragraph"]:
                if i + 1 < n and blocks[i + 1].block_type in ["formula", "code"]:
                    unit.append(blocks[i + 1])
                    i += 1
                    # Also include explanation after code/formula if present
                    if i + 1 < n and blocks[i + 1].block_type in ["paragraph", "note"]:
                        unit.append(blocks[i + 1])
                        i += 1

            units.append(unit)
            i += 1

        return units

    def _split_oversized_unit(
        self,
        unit: List[ContentBlock],
        document_id: str,
        document_version_id: str,
        lesson_id: Optional[str],
        section_title: str,
        known_terms: List[str]
    ) -> List[SemanticChunkData]:
        chunks: List[SemanticChunkData] = []
        for block in unit:
            text = block.normalized_content
            toks = estimate_tokens(text)
            if toks <= self.max_tokens:
                chunks.append(self._build_chunk_dto([block], document_id, document_version_id, lesson_id, section_title, known_terms))
            else:
                # Split text by paragraphs or sentences
                paragraphs = text.split("\n\n")
                sub_blocks = []
                sub_toks = 0
                for p in paragraphs:
                    p_toks = estimate_tokens(p)
                    if sub_toks + p_toks > self.max_tokens and sub_blocks:
                        merged_txt = "\n\n".join(sub_blocks)
                        c = SemanticChunkData(
                            document_id=document_id,
                            document_version_id=document_version_id,
                            sequence_number=1,
                            content=merged_txt,
                            title=section_title,
                            lesson_id=lesson_id,
                            token_estimate=estimate_tokens(merged_txt),
                            content_types=[block.block_type]
                        )
                        chunks.append(c)
                        sub_blocks = [p]
                        sub_toks = p_toks
                    else:
                        sub_blocks.append(p)
                        sub_toks += p_toks
                if sub_blocks:
                    merged_txt = "\n\n".join(sub_blocks)
                    c = SemanticChunkData(
                        document_id=document_id,
                        document_version_id=document_version_id,
                        sequence_number=1,
                        content=merged_txt,
                        title=section_title,
                        lesson_id=lesson_id,
                        token_estimate=estimate_tokens(merged_txt),
                        content_types=[block.block_type]
                    )
                    chunks.append(c)

        return chunks

    def _build_chunk_dto(
        self,
        unit_blocks: List[ContentBlock],
        document_id: str,
        document_version_id: str,
        lesson_id: Optional[str],
        section_title: str,
        known_terms: List[str]
    ) -> SemanticChunkData:
        content = "\n\n".join(b.normalized_content for b in unit_blocks)
        content_types = sorted(list(set(b.block_type for b in unit_blocks)))
        block_ids = [b.id for b in unit_blocks if hasattr(b, "id") and b.id]
        
        source_refs = []
        for b in unit_blocks:
            if hasattr(b, "source_reference") and b.source_reference:
                source_refs.append(b.source_reference)
            elif hasattr(b, "page_number") and b.page_number:
                source_refs.append(f"Page {b.page_number}")
            elif hasattr(b, "slide_number") and b.slide_number:
                source_refs.append(f"Slide {b.slide_number}")

        source_refs = sorted(list(set(source_refs)))

        # Find glossary terms matching chunk text
        matched_glossary = [term for term in known_terms if re.search(r"\b" + re.escape(term) + r"\b", content, re.IGNORECASE)]

        return SemanticChunkData(
            document_id=document_id,
            document_version_id=document_version_id,
            sequence_number=1,
            content=content,
            title=section_title,
            lesson_id=lesson_id,
            content_block_ids=block_ids,
            content_types=content_types,
            token_estimate=estimate_tokens(content),
            glossary_terms=matched_glossary,
            source_references=source_refs
        )
