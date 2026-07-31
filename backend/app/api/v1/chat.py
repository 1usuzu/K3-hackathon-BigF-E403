from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.chat import ChatSession, ChatMessage
from backend.app.services.model_gateway import ModelGateway, MockTextProvider, MockEmbeddingProvider
from backend.app.services.vector_retrieval import HybridRetrievalService, VectorEmbeddingService, AccessDeniedException
from backend.app.services.tutor_agent import TutorAgentService, TutorResponseSchema

router = APIRouter(prefix="/api/v1/chat", tags=["Tutor Chat"])

class SessionCreateRequest(BaseModel):
    user_id: str
    course_id: str
    lesson_id: Optional[str] = None
    title: Optional[str] = "Tutor Chat Session"

class MessageSendRequest(BaseModel):
    user_id: str
    course_id: str
    conversation_id: Optional[str] = None
    question: str
    selected_node_id: Optional[str] = None
    selected_lesson_id: Optional[str] = None
    current_flashcard_id: Optional[str] = None
    response_language: str = "vi"

@router.post("/sessions", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_chat_session(
    req: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    session = ChatSession(
        user_id=req.user_id,
        course_id=req.course_id,
        lesson_id=req.lesson_id,
        title=req.title or "Tutor Chat Session"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "title": session.title, "course_id": session.course_id}

@router.post("/messages", response_model=Dict[str, Any])
async def send_chat_message(
    req: MessageSendRequest,
    db: Session = Depends(get_db)
):
    # Instantiate ModelGateway and Services
    gateway = ModelGateway(text_provider=MockTextProvider(), embedding_provider=MockEmbeddingProvider())
    embed_service = VectorEmbeddingService(gateway=gateway)
    retrieval_service = HybridRetrievalService(db=db, embedding_service=embed_service)
    tutor_service = TutorAgentService(db=db, gateway=gateway, retrieval_service=retrieval_service)

    try:
        msg, response_data = await tutor_service.answer_student_question(
            user_id=req.user_id,
            course_id=req.course_id,
            question=req.question,
            conversation_id=req.conversation_id,
            selected_node_id=req.selected_node_id,
            selected_lesson_id=req.selected_lesson_id,
            current_flashcard_id=req.current_flashcard_id,
            response_language=req.response_language
        )
        return {
            "message_id": msg.id,
            "session_id": msg.session_id,
            "answer": response_data.answer,
            "answer_type": response_data.answer_type,
            "response_language": response_data.response_language,
            "preserved_terms": response_data.preserved_terms,
            "citations": [c.model_dump() for c in response_data.citations],
            "confidence": response_data.confidence,
            "insufficient_context": response_data.insufficient_context,
            "suggested_questions": response_data.suggested_questions
        }
    except AccessDeniedException as err:
        raise HTTPException(status_code=403, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.get("/sessions/{session_id}/history", response_model=Dict[str, Any])
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail=f"ChatSession '{session_id}' not found.")

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    history = []
    for m in messages:
        cits = [
            {
                "document_id": c.document_id,
                "document_version_id": c.document_version_id,
                "chunk_id": c.content_chunk_id,
                "page_number": c.page_number,
                "slide_number": c.slide_number,
                "source_excerpt": c.snippet_text
            }
            for c in m.citations
        ]
        history.append({
            "message_id": m.id,
            "role": m.role,
            "content": m.content,
            "retrieval_metadata": m.retrieval_metadata,
            "citations": cits
        })

    return {"session_id": session.id, "messages": history}
