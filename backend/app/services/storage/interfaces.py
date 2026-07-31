from abc import ABC, abstractmethod
from typing import Optional

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file_bytes: bytes, target_path: str) -> str:
        """Saves file bytes to the storage location and returns storage URI/path."""
        pass

    @abstractmethod
    async def get_file(self, target_path: str) -> bytes:
        """Retrieves file bytes from storage."""
        pass

    @abstractmethod
    async def delete_file(self, target_path: str) -> bool:
        """Deletes file from storage."""
        pass

    @abstractmethod
    async def exists(self, target_path: str) -> bool:
        """Checks if file exists in storage."""
        pass
