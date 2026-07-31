import os
from pathlib import Path
from backend.app.services.storage.interfaces import StorageProvider

class PathTraversalException(Exception):
    pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "./uploads"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, target_path: str) -> Path:
        # Strip leading slashes to make relative to base_dir
        clean_relative = target_path.lstrip("/\\")
        full_path = (self.base_dir / clean_relative).resolve()
        
        # Security check: Ensure target path is inside base_dir (anti path traversal)
        if not str(full_path).startswith(str(self.base_dir)):
            raise PathTraversalException(f"Path traversal detected in path: '{target_path}'")
        return full_path

    async def save_file(self, file_bytes: bytes, target_path: str) -> str:
        safe_path = self._resolve_safe_path(target_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_bytes(file_bytes)
        return str(safe_path)

    async def get_file(self, target_path: str) -> bytes:
        safe_path = self._resolve_safe_path(target_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        return safe_path.read_bytes()

    async def delete_file(self, target_path: str) -> bool:
        safe_path = self._resolve_safe_path(target_path)
        if safe_path.exists():
            safe_path.unlink()
            return True
        return False

    async def exists(self, target_path: str) -> bool:
        safe_path = self._resolve_safe_path(target_path)
        return safe_path.exists()
