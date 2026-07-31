from dataclasses import dataclass

@dataclass
class MasteryConfig:
    consecutive_correct_required: int = 3
    min_accuracy_ratio: float = 0.80
    min_attempts_required: int = 3

def determine_progress_token(completion_percentage: float, mastery_percentage: float) -> str:
    if completion_percentage == 0.0:
        return "progress-gray"
    elif completion_percentage == 100.0 and mastery_percentage == 100.0:
        return "progress-purple"
    elif completion_percentage <= 20.0:
        return "progress-red"
    elif completion_percentage <= 40.0:
        return "progress-orange"
    elif completion_percentage <= 60.0:
        return "progress-yellow"
    elif completion_percentage <= 80.0:
        return "progress-blue"
    else:
        return "progress-green"
