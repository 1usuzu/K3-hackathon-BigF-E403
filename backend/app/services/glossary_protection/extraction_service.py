import re
from typing import List, Dict, Set

class GlossaryExtractionService:
    @staticmethod
    def extract_candidate_terms(text: str) -> Dict[str, str]:
        """
        Scans lecture text or content blocks and extracts technical terms,
        algorithm names, code identifiers, framework names, and acronyms.
        """
        if not text:
            return {}

        extracted: Dict[str, str] = {}

        # 1. Multi-word Title Case terms (e.g. "Random Forest", "Gradient Descent", "Cross Entropy Loss")
        title_case_rx = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
        for match in title_case_rx.findall(text):
            if len(match) > 3 and match not in extracted:
                extracted[match] = "Thuật ngữ kỹ thuật được trích xuất từ tài liệu"

        # 2. Tech Acronyms (e.g. "CNN", "RNN", "LSTM", "RAG", "BERT", "LLM", "API", "REST", "JSON")
        acronym_rx = re.compile(r"\b([A-Z]{2,6})\b")
        common_words_exclude = {"OK", "ID", "NO", "VS", "US", "UK"}
        for match in acronym_rx.findall(text):
            if match not in common_words_exclude and match not in extracted:
                extracted[match] = "Tên viết tắt kỹ thuật"

        # 3. Code Identifiers (snake_case or camelCase e.g. "compute_loss", "fetchData", "LossEvaluator")
        code_ident_rx = re.compile(r"\b([a-z0-9]+_[a-z0-9_]+|[a-z]+[A-Z][a-zA-Z0-9]+)\b")
        for match in code_ident_rx.findall(text):
            if len(match) > 3 and match not in extracted:
                extracted[match] = "Code identifier / Tên biến / Tên hàm"

        # 4. LaTeX Math Variables & Greek letters (e.g. "\theta", "\alpha", "\sigma")
        math_rx = re.compile(r"(\\[a-zA-Z]+)")
        latex_commands_exclude = {"\\frac", "\\sum", "\\int", "\\sqrt", "\\begin", "\\end"}
        for match in math_rx.findall(text):
            if match not in latex_commands_exclude and match not in extracted:
                extracted[match] = "Ký hiệu toán học"

        return extracted
