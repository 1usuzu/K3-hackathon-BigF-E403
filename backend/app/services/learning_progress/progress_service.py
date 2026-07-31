from datetime import datetime, timezone
from typing import List, Optional, Set, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct

from backend.app.models.flashcard import Flashcard, FlashcardAttempt
from backend.app.models.mindmap import MindmapNode, node_flashcard_association
from backend.app.models.course import LearningProgress, Course
from backend.app.services.job_processing.events import ProgressEvent, global_event_publisher
from backend.app.services.learning_progress.config import MasteryConfig, determine_progress_token
from backend.app.services.learning_progress.dto import ProgressResponseDTO

class LearningProgressService:
    def __init__(self, db: Session, config: Optional[MasteryConfig] = None):
        self.db = db
        self.config = config or MasteryConfig()

    def record_attempt(
        self,
        user_id: str,
        flashcard_id: str,
        is_correct: bool,
        selected_option: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        attempted_at: Optional[datetime] = None
    ) -> Tuple[FlashcardAttempt, ProgressResponseDTO]:
        attempt_time = attempted_at or datetime.now(timezone.utc)

        # Transaction boundary
        with self.db.begin_nested() if self.db.in_transaction() else self.db.begin():
            # 1. Create FlashcardAttempt
            attempt = FlashcardAttempt(
                user_id=user_id,
                flashcard_id=flashcard_id,
                is_correct=is_correct,
                selected_option=selected_option,
                response_time_ms=response_time_ms,
                attempted_at=attempt_time
            )
            self.db.add(attempt)
            self.db.flush()

            # 2. Evaluate Card Progress & Status
            card = self.db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
            if not card:
                raise ValueError(f"Flashcard '{flashcard_id}' not found.")

            # Find all nodes linked to this flashcard
            linked_nodes = card.mindmap_nodes

            # Update progress for all linked nodes and their ancestors up to root
            last_dto = None
            affected_node_ids: Set[str] = set()

            for node in linked_nodes:
                # Collect node and all ancestor node IDs
                curr: Optional[MindmapNode] = node
                while curr:
                    if curr.id not in affected_node_ids:
                        affected_node_ids.add(curr.id)
                        last_dto = self._update_node_progress_in_db(user_id, card.course_id, curr)
                    curr = curr.parent_node

            if not last_dto:
                # If card is not linked to any node yet, compute overall course progress
                last_dto = self.get_course_progress(user_id, card.course_id)

        self.db.commit()
        return attempt, last_dto

    def _get_all_descendant_node_ids(self, node: MindmapNode) -> Set[str]:
        node_ids = {node.id}
        for child in node.child_nodes:
            node_ids.update(self._get_all_descendant_node_ids(child))
        return node_ids

    def _get_unique_flashcards_for_node_subtree(self, node: MindmapNode) -> List[Flashcard]:
        descendant_ids = self._get_all_descendant_node_ids(node)

        # Query UNIQUE flashcards linked to any node in the subtree
        stmt = (
            select(Flashcard)
            .join(node_flashcard_association)
            .where(node_flashcard_association.c.node_id.in_(descendant_ids))
            .distinct()
        )
        return self.db.scalars(stmt).all()

    def evaluate_card_status(self, user_id: str, flashcard_id: str) -> str:
        attempts = self.db.query(FlashcardAttempt).filter(
            FlashcardAttempt.user_id == user_id,
            FlashcardAttempt.flashcard_id == flashcard_id
        ).order_by(FlashcardAttempt.attempted_at.desc()).all()

        if not attempts:
            return "new"

        total = len(attempts)
        correct_count = sum(1 for a in attempts if a.is_correct)
        accuracy = correct_count / total

        # Check consecutive correct attempts from latest
        consecutive_correct = 0
        for a in attempts:
            if a.is_correct:
                consecutive_correct += 1
            else:
                break

        if (
            consecutive_correct >= self.config.consecutive_correct_required
            or (accuracy >= self.config.min_accuracy_ratio and total >= self.config.min_attempts_required)
        ):
            return "mastered"
        elif total >= 2:
            return "reviewing"
        else:
            return "learning"

    def calculate_node_progress_dto(self, user_id: str, node: MindmapNode) -> ProgressResponseDTO:
        # Deduplicated union of flashcards across subtree (Req 1 & 2)
        unique_cards = self._get_unique_flashcards_for_node_subtree(node)
        total_cards = len(unique_cards)

        if total_cards == 0:
            return ProgressResponseDTO(
                completion_percentage=0.0,
                mastery_percentage=0.0,
                completed_cards=0,
                mastered_cards=0,
                total_cards=0,
                status="new",
                progress_token="progress-gray"
            )

        completed_cards = 0
        mastered_cards = 0

        for card in unique_cards:
            status = self.evaluate_card_status(user_id, card.id)
            if status != "new":
                completed_cards += 1
            if status == "mastered":
                mastered_cards += 1

        completion_pct = round((completed_cards / total_cards) * 100.0, 2)
        mastery_pct = round((mastered_cards / total_cards) * 100.0, 2)

        if mastery_pct == 100.0:
            overall_status = "mastered"
        elif completion_pct > 50.0:
            overall_status = "reviewing"
        elif completion_pct > 0.0:
            overall_status = "learning"
        else:
            overall_status = "new"

        token = determine_progress_token(completion_pct, mastery_pct)

        return ProgressResponseDTO(
            completion_percentage=completion_pct,
            mastery_percentage=mastery_pct,
            completed_cards=completed_cards,
            mastered_cards=mastered_cards,
            total_cards=total_cards,
            status=overall_status,
            progress_token=token
        )

    def _update_node_progress_in_db(
        self,
        user_id: str,
        course_id: str,
        node: MindmapNode
    ) -> ProgressResponseDTO:
        dto = self.calculate_node_progress_dto(user_id, node)

        prog_rec = self.db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.mindmap_node_id == node.id
        ).first()

        if not prog_rec:
            prog_rec = LearningProgress(
                user_id=user_id,
                course_id=course_id,
                mindmap_node_id=node.id,
                lesson_id=node.mindmap.lesson_id if node.mindmap else None
            )
            self.db.add(prog_rec)

        prog_rec.completed_flashcards_count = dto.completed_cards
        prog_rec.total_flashcards_count = dto.total_cards
        prog_rec.mastery_percentage = dto.mastery_percentage
        prog_rec.last_studied_at = datetime.now(timezone.utc)

        self.db.flush()
        return dto

    def get_course_progress(self, user_id: str, course_id: str) -> ProgressResponseDTO:
        all_cards = self.db.query(Flashcard).filter(Flashcard.course_id == course_id).all()
        total_cards = len(all_cards)

        if total_cards == 0:
            return ProgressResponseDTO(0.0, 0.0, 0, 0, 0, "new", "progress-gray")

        completed = 0
        mastered = 0
        for card in all_cards:
            st = self.evaluate_card_status(user_id, card.id)
            if st != "new":
                completed += 1
            if st == "mastered":
                mastered += 1

        comp_pct = round((completed / total_cards) * 100.0, 2)
        mast_pct = round((mastered / total_cards) * 100.0, 2)
        token = determine_progress_token(comp_pct, mast_pct)

        return ProgressResponseDTO(
            completion_percentage=comp_pct,
            mastery_percentage=mast_pct,
            completed_cards=completed,
            mastered_cards=mastered,
            total_cards=total_cards,
            status="mastered" if mast_pct == 100.0 else ("learning" if comp_pct > 0 else "new"),
            progress_token=token
        )

    def rebuild_progress_from_history(self, user_id: str, course_id: str) -> int:
        """
        Rebuilds all user progress records from raw FlashcardAttempt history.
        """
        nodes = self.db.query(MindmapNode).join(MindmapNode.mindmap).filter(
            MindmapNode.mindmap.has(course_id=course_id)
        ).all()

        rebuilt_count = 0
        for node in nodes:
            self._update_node_progress_in_db(user_id, course_id, node)
            rebuilt_count += 1

        self.db.commit()
        return rebuilt_count
