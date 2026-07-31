from backend.app.core.database import Base
from backend.app.models.user import User
from backend.app.models.course import Course, Lesson, LearningProgress
from backend.app.models.document import LearningDocument, DocumentVersion, ContentBlock, ContentChunk, GlossaryTerm
from backend.app.models.job import ProcessingJob, ProcessingTask
from backend.app.models.mindmap import Mindmap, MindmapNode, node_flashcard_association
from backend.app.models.flashcard import Flashcard, FlashcardAttempt
from backend.app.models.chat import ChatSession, ChatMessage, SourceReference
from backend.app.models.model_config import ModelConfiguration

__all__ = [
    "Base",
    "User",
    "Course",
    "Lesson",
    "LearningProgress",
    "LearningDocument",
    "DocumentVersion",
    "ContentBlock",
    "ContentChunk",
    "GlossaryTerm",
    "ProcessingJob",
    "ProcessingTask",
    "Mindmap",
    "MindmapNode",
    "node_flashcard_association",
    "Flashcard",
    "FlashcardAttempt",
    "ChatSession",
    "ChatMessage",
    "SourceReference",
    "ModelConfiguration"
]
