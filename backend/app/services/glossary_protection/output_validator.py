import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field

@dataclass
class GlossaryValidationResult:
    is_valid: bool
    violations: List[Dict[str, str]] = field(default_factory=list)
    missing_protected_terms: List[str] = field(default_factory=list)

KNOWN_INVALID_TRANSLATIONS: Dict[str, str] = {
    "giảm độ dốc": "Gradient Descent",
    "quá khớp": "Overfitting",
    "dưới khớp": "Underfitting",
    "dương tính giả": "False Positive",
    "âm tính giả": "False Negative",
    "chi phí lỗi": "Cost of Error",
    "mô hình ngôn ngữ lớn": "LLM",
    "học máy": "Machine Learning",
    "mạng thần kinh": "Neural Network",
    "hàm mất mát": "Loss Function"
}

class GlossaryOutputValidator:
    @staticmethod
    def validate_output(
        generated_output: str,
        protected_terms: Dict[str, str]
    ) -> GlossaryValidationResult:
        if not generated_output:
            return GlossaryValidationResult(is_valid=True)

        output_lower = generated_output.lower()
        violations: List[Dict[str, str]] = []

        # 1. Check if any forbidden translated Vietnamese phrase was used instead of English term
        for invalid_trans, english_term in KNOWN_INVALID_TRANSLATIONS.items():
            if invalid_trans in output_lower and english_term in protected_terms:
                # Double check that the English term itself was not present alongside
                if english_term.lower() not in output_lower:
                    violations.append({
                        "type": "translated_term_forbidden",
                        "found_translation": invalid_trans,
                        "expected_term": english_term,
                        "reason": f"Thuật ngữ '{english_term}' đã bị dịch trái phép thành '{invalid_trans}'."
                    })

        # 2. Code Identifier Case-Sensitivity & Exact Word Match Check
        for term in protected_terms.keys():
            # If term is a code identifier like 'snake_case' or 'camelCase' or class name
            if "_" in term or (term[0].isupper() and not term.isupper() and " " not in term and len(term) > 3):
                # If identifier appeared in output with altered case
                matches = re.findall(r"\b" + re.escape(term.lower()) + r"\b", output_lower)
                if matches:
                    exact_matches = re.findall(r"\b" + re.escape(term) + r"\b", generated_output)
                    if not exact_matches:
                        violations.append({
                            "type": "identifier_case_altered",
                            "found_translation": term.lower(),
                            "expected_term": term,
                            "reason": f"Identifier '{term}' đã bị thay đổi chữ hoa/thường hoặc định dạng."
                        })

        is_valid = len(violations) == 0
        return GlossaryValidationResult(
            is_valid=is_valid,
            violations=violations
        )
