import re
import hashlib
from typing import Tuple

class InvalidFileFormatException(Exception):
    pass

class FileTooLargeException(Exception):
    pass

class DangerousFileContentException(Exception):
    pass

# File Signatures (Magic Bytes)
MAGIC_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "pptx": [b"PK\x03\x04"],  # PPTX is OpenXML Zip archive
    "webm": [b"\x1a\x45\xdf\xa3"], # WebM / Matroska
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"], # MP3 ID3 or Frame Sync
    "wav": [b"RIFF"], # WAV RIFF header
}

DANGEROUS_MAGIC_HEADERS = [
    b"MZ",          # Windows EXE/DLL
    b"\x7fELF",     # Linux Executable
    b"\xca\xfe\xba\xbe", # Java Class file / Mach-O binary
]

DEFAULT_MAX_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB for media files

class FileValidator:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename:
            return "unnamed_document"
        
        # Remove any path traversal components or path separators
        clean_name = filename.replace("\\", "/").split("/")[-1]
        clean_name = re.sub(r"\.\.+", ".", clean_name)
        
        # Replace spaces and dangerous characters with underscores
        clean_name = re.sub(r"[^\w\.\-]", "_", clean_name)
        
        # Limit length to 200 characters
        if len(clean_name) > 200:
            ext = clean_name.split(".")[-1] if "." in clean_name else ""
            clean_name = clean_name[:180] + (f".{ext}" if ext else "")
            
        return clean_name

    @staticmethod
    def compute_sha256(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def validate(file_bytes: bytes, filename: str, max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES) -> Tuple[str, str]:
        """
        Validates file size, file signature (magic bytes), and sanitizes filename.
        Returns tuple of (sanitized_filename, mime_type).
        """
        # 1. Size Check
        if len(file_bytes) > max_size_bytes:
            raise FileTooLargeException(f"File size ({len(file_bytes)} bytes) exceeds max limit of {max_size_bytes} bytes.")

        if len(file_bytes) == 0:
            raise InvalidFileFormatException("File is empty (0 bytes).")

        # 2. Dangerous File Header Check
        for dang_header in DANGEROUS_MAGIC_HEADERS:
            if file_bytes.startswith(dang_header):
                raise DangerousFileContentException("Executable or binary script file signature detected.")

        # 3. Extension & Magic Signature Check
        sanitized_name = FileValidator.sanitize_filename(filename)
        ext = sanitized_name.split(".")[-1].lower() if "." in sanitized_name else ""

        if ext == "pdf":
            if not any(file_bytes.startswith(sig) for sig in MAGIC_SIGNATURES["pdf"]):
                raise InvalidFileFormatException("File has .pdf extension but invalid PDF magic bytes signature (%PDF-).")
            mime_type = "application/pdf"
        elif ext in ["pptx", "ppt"]:
            if not any(file_bytes.startswith(sig) for sig in MAGIC_SIGNATURES["pptx"]):
                raise InvalidFileFormatException("File has .pptx extension but invalid PPTX/Zip archive magic bytes.")
            mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        elif ext in ["txt", "md", "markdown"]:
            try:
                file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                raise InvalidFileFormatException("Text/Markdown file contains invalid binary non-UTF-8 characters.")
            mime_type = "text/markdown" if ext in ["md", "markdown"] else "text/plain"
        elif ext == "mp4":
            # MP4 magic check: ftyp at offset 4
            if len(file_bytes) >= 8 and file_bytes[4:8] == b"ftyp":
                mime_type = "video/mp4"
            else:
                mime_type = "video/mp4" # Soft check for container streams
        elif ext == "webm":
            if not any(file_bytes.startswith(sig) for sig in MAGIC_SIGNATURES["webm"]):
                raise InvalidFileFormatException("File has .webm extension but invalid WebM magic bytes.")
            mime_type = "video/webm"
        elif ext == "mov":
            mime_type = "video/quicktime"
        elif ext == "mp3":
            mime_type = "audio/mpeg"
        elif ext == "wav":
            if not any(file_bytes.startswith(sig) for sig in MAGIC_SIGNATURES["wav"]):
                raise InvalidFileFormatException("File has .wav extension but invalid WAV RIFF header.")
            mime_type = "audio/wav"
        elif ext == "m4a":
            mime_type = "audio/mp4"
        else:
            raise InvalidFileFormatException(f"Unsupported file extension '.{ext}'. Supported extensions: .pdf, .pptx, .txt, .md, .mp4, .webm, .mov, .mp3, .wav, .m4a")

        return sanitized_name, mime_type
