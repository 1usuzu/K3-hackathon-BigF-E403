import os
import sys

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.user import User
from backend.app.models.course import Course, Lesson
from backend.app.models.mindmap import Mindmap, MindmapNode, node_flashcard_association
from backend.app.models.flashcard import Flashcard
from backend.app.services.node_linking import NodeLinkRepository

def seed_initial_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create Default User
        user = db.query(User).filter(User.id == "usr-student-1").first()
        if not user:
            user = User(
                id="usr-student-1",
                email="student@vlearn.edu.vn",
                full_name="Học Viên VLearn",
                access_scope="ALL"
            )
            db.add(user)

        # 2. Create Default Course
        course = db.query(Course).filter(Course.id == "c-hackathon-d2").first()
        if not course:
            course = Course(
                id="c-hackathon-d2",
                code="COMP2010",
                title="DAY 02: Xác định bài toán cho AI",
                description="Lecture material Day 02 AI Problem Definition"
            )
            db.add(course)

        db.commit()

        # 3. Create Default Mindmap & Nodes
        mindmap = db.query(Mindmap).filter(Mindmap.course_id == "c-hackathon-d2").first()
        if not mindmap:
            mindmap = Mindmap(
                id="mm-d2-master",
                course_id="c-hackathon-d2",
                title="XÁC ĐỊNH BÀI TOÁN AI"
            )
            db.add(mindmap)
            db.commit()

            root = MindmapNode(
                id="n-root-d2",
                mindmap_id=mindmap.id,
                node_stable_id="n-root",
                label="XÁC ĐỊNH BÀI TOÁN AI",
                page_number=1,
                depth=0
            )
            db.add(root)
            db.commit()

            n1 = MindmapNode(id="n1-jtbd", mindmap_id=mindmap.id, parent_node_id=root.id, node_stable_id="n1-jtbd", label="Phần 1: User & Job (JTBD)", page_number=5, depth=1)
            n2 = MindmapNode(id="n2-criteria", mindmap_id=mindmap.id, parent_node_id=root.id, node_stable_id="n2-criteria", label="Phần 2: 5 Tiêu chí nghiệm thu", page_number=16, depth=1)
            n3 = MindmapNode(id="n3-risk", mindmap_id=mindmap.id, parent_node_id=root.id, node_stable_id="n3-risk", label="Phần 3: Các lớp rủi ro AI", page_number=26, depth=1)

            db.add_all([n1, n2, n3])
            db.commit()

            n1_1 = MindmapNode(id="n1-1-core", mindmap_id=mindmap.id, parent_node_id=n1.id, node_stable_id="n1-1-core", label="Core JTBD", page_number=8, depth=2)
            n1_2 = MindmapNode(id="n1-2-alt", mindmap_id=mindmap.id, parent_node_id=n1.id, node_stable_id="n1-2-alt", label="Alternatives", page_number=12, depth=2)
            
            n2_1 = MindmapNode(id="n2-1-cut", mindmap_id=mindmap.id, parent_node_id=n2.id, node_stable_id="n2-1-cut", label="Lát cắt 1 câu", page_number=18, depth=2)
            n2_2 = MindmapNode(id="n2-2-proof", mindmap_id=mindmap.id, parent_node_id=n2.id, node_stable_id="n2-2-proof", label="Bằng chứng", page_number=22, depth=2)
            
            n3_1 = MindmapNode(id="n3-1-cost", mindmap_id=mindmap.id, parent_node_id=n3.id, node_stable_id="n3-1-cost", label="Cost of error", page_number=28, depth=2)

            db.add_all([n1_1, n1_2, n2_1, n2_2, n3_1])
            db.commit()

            n3_1_1 = MindmapNode(id="n3-1-1-auto", mindmap_id=mindmap.id, parent_node_id=n3_1.id, node_stable_id="n3-1-1-auto", label="Automate", page_number=30, depth=3)
            n3_1_2 = MindmapNode(id="n3-1-2-aug", mindmap_id=mindmap.id, parent_node_id=n3_1.id, node_stable_id="n3-1-2-aug", label="Augment", page_number=32, depth=3)

            db.add_all([n3_1_1, n3_1_2])
            db.commit()

        # 4. Create Flashcards
        card1 = db.query(Flashcard).filter(Flashcard.id == "fc-d2-1").first()
        if not card1:
            card1 = Flashcard(
                id="fc-d2-1",
                course_id="c-hackathon-d2",
                question="Nếu AI lọc CV, 'Cost of error' lớn nhất là gì?",
                answer="B. Loại nhầm ứng viên giỏi (False Negative)",
                options_json=[
                    "A. Tốn tiền mua API",
                    "B. Loại nhầm ứng viên giỏi (False Negative)",
                    "C. Giao diện khó dùng",
                    "D. Chạy chậm"
                ],
                difficulty="EASY"
            )
            card2 = Flashcard(
                id="fc-d2-2",
                course_id="c-hackathon-d2",
                question="Câu hỏi cốt lõi để xác định JTBD (Job) là gì?",
                answer="C. Khách hàng đang cố hoàn thành việc gì?",
                options_json=[
                    "A. Khách hàng muốn tính năng gì?",
                    "B. Khách hàng sẵn sàng trả bao nhiêu?",
                    "C. Khách hàng đang cố hoàn thành việc gì?",
                    "D. Đối thủ đang làm gì?"
                ],
                difficulty="EASY"
            )
            card3 = Flashcard(
                id="fc-d2-3",
                course_id="c-hackathon-d2",
                question="Tiêu chí nghiệm thu AI nên có yếu tố nào?",
                answer="A. Lát cắt 1 câu, có thể đo lường",
                options_json=[
                    "A. Lát cắt 1 câu, có thể đo lường",
                    "B. Viết bằng mã code",
                    "C. Độ dài 10 trang",
                    "D. Chứa thuật toán phức tạp"
                ],
                difficulty="MEDIUM"
            )
            db.add_all([card1, card2, card3])
            db.commit()

            repo = NodeLinkRepository(db)
            repo.link_flashcard_to_nodes("fc-d2-1", ["n3-1-cost", "n3-1-1-auto"])
            repo.link_flashcard_to_nodes("fc-d2-2", ["n1-1-core"])
            repo.link_flashcard_to_nodes("fc-d2-3", ["n2-1-cut"])

        print("Successfully seeded initial VLearn course data into database!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_data()
