from dataclasses import dataclass

@dataclass
class ProgressResponseDTO:
    completion_percentage: float
    mastery_percentage: float
    completed_cards: int
    mastered_cards: int
    total_cards: int
    status: str  # "new", "learning", "reviewing", "mastered"
    progress_token: str  # "progress-gray", "progress-green", etc.
