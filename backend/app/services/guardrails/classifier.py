import logging
from dataclasses import dataclass
from typing import List, Tuple
from backend.app.services.content_extraction.prompt_injection_detector import PromptInjectionDetector

logger = logging.getLogger("ContentClassifier")

@dataclass
class SecurityEvent:
    event_type: str  # PROMPT_INJECTION, CROSS_COURSE_ATTEMPT, SECRET_EXFILTRATION_ATTEMPT, FAKE_CITATION
    source: str
    details: str

class SecurityEventPublisher:
    _events: List[SecurityEvent] = []

    @classmethod
    def publish(cls, event: SecurityEvent):
        cls._events.append(event)
        # Security: Log metadata only, do NOT log raw sensitive prompt contents!
        logger.warning(f"[SECURITY EVENT] Type: {event.event_type} | Source: {event.source}")

    @classmethod
    def get_events(cls) -> List[SecurityEvent]:
        return list(cls._events)

    @classmethod
    def clear(cls):
        cls._events.clear()

class ContentClassifier:
    @staticmethod
    def classify_and_detect_injection(text: str, source_label: str = "untrusted_input") -> Tuple[bool, List[str]]:
        if not text:
            return False, []

        is_suspicious, signals = PromptInjectionDetector.detect(text)

        if is_suspicious:
            event = SecurityEvent(
                event_type="PROMPT_INJECTION",
                source=source_label,
                details=f"Detected injection patterns: {', '.join(signals)}"
            )
            SecurityEventPublisher.publish(event)

        return is_suspicious, signals
