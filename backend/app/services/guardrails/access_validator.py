from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.services.vector_retrieval.retrieval_service import AccessDeniedException
from backend.app.services.guardrails.classifier import SecurityEventPublisher, SecurityEvent

class AccessScopeValidator:
    @staticmethod
    def validate_user_access(db: Session, user_id: str, target_course_id: str):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AccessDeniedException(f"User '{user_id}' not found.")

        if user.access_scope and user.access_scope != "ALL":
            allowed = [c.strip() for c in user.access_scope.split(",")]
            if target_course_id not in allowed:
                SecurityEventPublisher.publish(
                    SecurityEvent(
                        event_type="CROSS_COURSE_ATTEMPT",
                        source="access_scope_validator",
                        details=f"User '{user_id}' attempted unauthorized access to course '{target_course_id}'."
                    )
                )
                raise AccessDeniedException(f"Access Denied: User '{user_id}' cannot access course '{target_course_id}'.")
