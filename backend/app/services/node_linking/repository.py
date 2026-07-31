from typing import List, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, delete

from backend.app.models.flashcard import Flashcard
from backend.app.models.mindmap import MindmapNode, node_flashcard_association

class NodeLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def link_flashcard_to_nodes(
        self,
        flashcard_id: str,
        node_ids: List[str]
    ) -> int:
        if not node_ids:
            return 0

        inserted_count = 0
        for nid in node_ids:
            # Check if relationship already exists (Idempotent insertion)
            stmt = select(node_flashcard_association).where(
                node_flashcard_association.c.node_id == nid,
                node_flashcard_association.c.flashcard_id == flashcard_id
            )
            existing = self.db.execute(stmt).first()
            if not existing:
                ins_stmt = insert(node_flashcard_association).values(
                    node_id=nid,
                    flashcard_id=flashcard_id
                )
                self.db.execute(ins_stmt)
                inserted_count += 1

        self.db.commit()
        return inserted_count

    def relink_flashcards_on_mindmap_regeneration(
        self,
        old_mindmap_id: str,
        new_mindmap_id: str
    ) -> Dict[str, int]:
        """
        When a Mindmap is regenerated, uses `node_stable_id` to preserve all flashcard
        links to the corresponding new nodes if node_stable_id matches!
        """
        # 1. Fetch old nodes and their associated flashcard IDs
        old_nodes = self.db.query(MindmapNode).filter(MindmapNode.mindmap_id == old_mindmap_id).all()
        stable_id_to_flashcard_ids: Dict[str, List[str]] = {}

        for old_node in old_nodes:
            fc_ids = [fc.id for fc in old_node.flashcards]
            if fc_ids:
                stable_id_to_flashcard_ids[old_node.node_stable_id] = fc_ids

        # 2. Fetch new nodes
        new_nodes = self.db.query(MindmapNode).filter(MindmapNode.mindmap_id == new_mindmap_id).all()
        relinked_count = 0

        # 3. Relink flashcards to new nodes matching node_stable_id
        for new_node in new_nodes:
            target_fc_ids = stable_id_to_flashcard_ids.get(new_node.node_stable_id, [])
            if target_fc_ids:
                for fc_id in target_fc_ids:
                    count = self.link_flashcard_to_nodes(fc_id, [new_node.id])
                    relinked_count += count

        return {
            "relinked_nodes_count": len(stable_id_to_flashcard_ids),
            "total_links_relinked": relinked_count
        }
