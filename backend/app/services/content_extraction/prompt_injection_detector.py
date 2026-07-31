import re
from typing import Tuple, List

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(above|previous)\s+(text|instructions)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(your\s+)?(rules|instructions)", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(dan|developer\s+mode|jailbroken)", re.IGNORECASE),
    re.compile(r"override\s+(system|safety)\s+(settings|rules)", re.IGNORECASE),
    re.compile(r"act\s+as\s+an?\s+unfiltered", re.IGNORECASE),
    re.compile(r"\[SYSTEM\s+MESSAGE\]", re.IGNORECASE)
]

class PromptInjectionDetector:
    @staticmethod
    def detect(text: str) -> Tuple[bool, List[str]]:
        if not text:
            return False, []

        detected_signals = []
        for pattern in PROMPT_INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                detected_signals.append(match.group(0))

        return len(detected_signals) > 0, detected_signals
