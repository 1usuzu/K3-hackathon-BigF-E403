import re
from typing import Tuple, List
from backend.app.services.content_extraction.prompt_injection_detector import PromptInjectionDetector

class PromptInjectionDefense:
    @staticmethod
    def sanitize_and_check_query(user_query: str) -> Tuple[str, bool, List[str]]:
        """
        Sanitizes user input query and checks for prompt injection attempts.
        Returns (sanitized_query, is_injection_detected, detected_signals).
        """
        if not user_query:
            return "", False, []

        is_suspicious, signals = PromptInjectionDetector.detect(user_query)

        # Neutralize common injection patterns
        sanitized = re.sub(
            r"(?i)(ignore\s+previous\s+instructions|system\s+prompt|reveal\s+secret|you\s+are\s+now\s+DAN)",
            "[REDACTED_INJECTION_ATTEMPT]",
            user_query
        )

        return sanitized.strip(), is_suspicious, signals
