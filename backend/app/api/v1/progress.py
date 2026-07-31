from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.mindmap import MindmapNode
from backend.app.services.learning_progress import LearningProgressService, ProgressResponseDTO

router = APIRouter(prefix="/api/v1/progress", tags=["Learning Progress"])

class AttemptCreateRequest(BaseModel):
    user_id: str
    flashcard_id: str
    is_correct: bool
    selected_option: Optional[str] = None
    response_time_ms: Optional[int] = None

class ProgressRebuildRequest(BaseModel):
    user_id: str
    course_id: str

@router.post("/attempts", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def record_student_attempt(
    req: AttemptCreateRequest,
    db: Session = Depends(get_db)
):
    service = LearningProgressService(db=db)
    try:
        attempt, dto = service.record_attempt(
            user_id=req.user_id,
            flashcard_id=req.flashcard_id,
            is_correct=req.is_correct,
            selected_option=req.selected_option,
            response_time_ms=req.response_time_ms
        )
        return {
            "attempt_id": attempt.id,
            "completion_percentage": dto.completion_percentage,
            "mastery_percentage": dto.mastery_percentage,
            "completed_cards": dto.completed_cards,
            "mastered_cards": dto.mastered_cards,
            "total_cards": dto.total_cards,
            "status": dto.status,
            "progress_token": dto.progress_token
        }
    except ValueError as e:
        print("DEBUG_PROGRESS_ERROR:", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/nodes/{node_id}", response_model=Dict[str, Any])
def get_node_progress(
    node_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    node = db.query(MindmapNode).filter(MindmapNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"MindmapNode '{node_id}' not found.")

    service = LearningProgressService(db=db)
    dto = service.calculate_node_progress_dto(user_id=user_id, node=node)
    
    return {
        "node_id": node.id,
        "node_stable_id": node.node_stable_id,
        "completion_percentage": dto.completion_percentage,
        "mastery_percentage": dto.mastery_percentage,
        "completed_cards": dto.completed_cards,
        "mastered_cards": dto.mastered_cards,
        "total_cards": dto.total_cards,
        "status": dto.status,
        "progress_token": dto.progress_token
    }

@router.post("/rebuild", response_model=Dict[str, Any])
def rebuild_progress_history(
    req: ProgressRebuildRequest,
    db: Session = Depends(get_db)
):
    service = LearningProgressService(db=db)
    count = service.rebuild_progress_from_history(user_id=req.user_id, course_id=req.course_id)
    return {"rebuilt_records_count": count, "message": "Progress rebuilt successfully."}
