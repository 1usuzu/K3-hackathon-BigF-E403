from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional
from backend.app.schemas.enums import JobStatus

@dataclass
class ProgressEvent:
    job_id: str
    status: JobStatus
    progress_percentage: int
    completed_tasks: int
    total_tasks: int
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ProgressEventPublisher:
    def __init__(self):
        self._listeners: List[Callable[[ProgressEvent], None]] = []

    def subscribe(self, listener: Callable[[ProgressEvent], None]):
        self._listeners.append(listener)

    def publish(self, event: ProgressEvent):
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

# Global Singleton Event Publisher
global_event_publisher = ProgressEventPublisher()
