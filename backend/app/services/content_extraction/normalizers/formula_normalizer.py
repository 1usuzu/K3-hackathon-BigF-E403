import re
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class FormulaOutput:
    formula_id: str
    original_representation: str
    latex: str
    variables: List[str]
    surrounding_explanation: str
    confidence_score: float
    needs_review: bool
    source_reference: str = ""
    image_crop_path: Optional[str] = None

class FormulaNormalizer:
    @staticmethod
    def normalize_formula(
        raw_text: str,
        source_reference: str = "",
        surrounding_explanation: str = "",
        image_crop_path: Optional[str] = None,
        is_ocr: bool = False
    ) -> FormulaOutput:
        formula_id = str(uuid.uuid4())
        original = raw_text.strip()

        # Extract LaTeX representation
        latex_str = original
        # Strip outer delimiters if present: $...$ or $$...$$ or \[...\]
        if latex_str.startswith("$$") and latex_str.endswith("$$"):
            latex_str = latex_str[2:-2].strip()
        elif latex_str.startswith("$") and latex_str.endswith("$"):
            latex_str = latex_str[1:-1].strip()
        elif latex_str.startswith("\\[") and latex_str.endswith("\\]"):
            latex_str = latex_str[2:-2].strip()

        # Variable extraction heuristic (Greek letters or single/subscripted letter symbols)
        var_pattern = re.compile(r"(\\[a-zA-Z]+|[a-zA-Z]_\{\w+\}|[a-zA-Z]_\w|[a-zA-Z])")
        matches = var_pattern.findall(latex_str)
        
        # Exclude common LaTeX commands that are not variables
        latex_commands = {"\\frac", "\\sum", "\\int", "\\sqrt", "\\left", "\\right", "\\begin", "\\end", "\\limits", "\\matrix"}
        variables = sorted(list(set(m for m in matches if m not in latex_commands and len(m) > 0)))

        # Confidence Score calculation
        confidence = 0.95
        if is_ocr:
            confidence -= 0.3  # OCR extracted math has lower confidence
        
        # Check for unconfident / ambiguous tokens
        if "?" in original or "UNKNOWN_SYMBOL" in original or len(original) == 0:
            confidence = min(confidence, 0.4)

        needs_review = confidence < 0.7

        return FormulaOutput(
            formula_id=formula_id,
            original_representation=original,
            latex=latex_str,
            variables=variables,
            surrounding_explanation=surrounding_explanation.strip(),
            confidence_score=round(confidence, 2),
            needs_review=needs_review,
            source_reference=source_reference,
            image_crop_path=image_crop_path
        )
