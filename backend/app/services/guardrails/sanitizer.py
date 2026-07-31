import re

class InputSanitizer:
    @staticmethod
    def sanitize_text(text: str) -> str:
        if not text:
            return ""

        # 1. Strip script and iframe tags
        cleaned = re.sub(r"(?i)<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", "[REDACTED_SCRIPT]", text)
        cleaned = re.sub(r"(?i)<iframe\b[^<]*(?:(?!</iframe>)<[^<]*)*</iframe>", "[REDACTED_IFRAME]", cleaned)

        # 2. Strip event handlers (onerror=, onload=, onclick=)
        cleaned = re.sub(r"(?i)on\w+\s*=\s*[\"'].*?[\"']", "[REDACTED_EVENT_HANDLER]", cleaned)

        # 3. Strip javascript: URIs
        cleaned = re.sub(r"(?i)javascript:", "[REDACTED_JS_URI]", cleaned)

        return cleaned.strip()
