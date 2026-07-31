import re

class SensitiveDataRedactor:
    PATTERNS = [
        re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE),
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}", re.IGNORECASE),
        re.compile(r"Bearer\s+[a-zA-Z0-9\._-]{10,}", re.IGNORECASE),
        re.compile(r"api_key\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE),
        re.compile(r"secret\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE),
    ]

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        if not text:
            return ""

        redacted = text
        for pattern in cls.PATTERNS:
            redacted = pattern.sub("[REDACTED_SECRET_KEY]", redacted)

        return redacted
