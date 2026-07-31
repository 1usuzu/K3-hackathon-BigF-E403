import os
import re
from typing import Optional

API_KEY_PATTERNS = [
    (re.compile(r"(api[_-]?key|secret|token|auth_header)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", re.IGNORECASE), r"\1: [REDACTED_SECRET]"),
    (re.compile(r"(sk-[a-zA-Z0-9_\-]{20,})"), r"[REDACTED_SECRET]"),
    (re.compile(r"(Bearer\s+[a-zA-Z0-9_\-\.]{15,})", re.IGNORECASE), r"Bearer [REDACTED_SECRET]")
]

class LogRedactor:
    @staticmethod
    def redact_text(text: str, max_chars: int = 150) -> str:
        if not text:
            return ""
        
        redacted = text
        for pattern, replacement in API_KEY_PATTERNS:
            redacted = pattern.sub(replacement, redacted)

        # Truncate long document text to avoid logging full untrusted document payload
        if len(redacted) > max_chars:
            return redacted[:max_chars] + f"... [TRUNCATED_{len(redacted)}_CHARS]"
        return redacted

    @staticmethod
    def get_api_key_from_env(env_var_name: str) -> Optional[str]:
        if not env_var_name:
            return None
        return os.getenv(env_var_name)
