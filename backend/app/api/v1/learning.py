from typing import Optional, List, Dict, Any
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import SessionLocal, get_db
from backend.app.models.mindmap import Mindmap, MindmapNode, node_flashcard_association
from backend.app.models.flashcard import Flashcard
from backend.app.services.learning_progress.progress_service import LearningProgressService

router = APIRouter(prefix="/api/v1/learning", tags=["Learning"])

class FlashcardDTO(BaseModel):
    id: str
    question: str
    answer: str
    options: List[str]
    tag: str
    slide_ref: str
    difficulty: str

@router.get("/mindmaps/{course_id}")
def get_course_mindmap(course_id: str, user_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    mindmap = db.query(Mindmap).filter(Mindmap.course_id == course_id).first()
    if not mindmap:
        # Fallback default mindmap tree structure for Day 02
        fallback_tree = [
            {
                "id": "root-1",
                    "node_stable_id": "n-root",
                    "label": "XÁC ĐỊNH BÀI TOÁN AI",
                    "slide_ref": "Toàn bộ bài",
                    "children": [
                        {
                            "id": "n1",
                            "node_stable_id": "n1-jtbd",
                            "label": "Phần 1: User & Job (JTBD)",
                            "slide_ref": "Slide 5-15",
                            "children": [
                                {"id": "n1-1", "node_stable_id": "n1-1-core", "label": "Core JTBD", "slide_ref": "Slide 8", "children": []},
                                {"id": "n1-2", "node_stable_id": "n1-2-alt", "label": "Alternatives", "slide_ref": "Slide 12", "children": []}
                            ]
                        },
                        {
                            "id": "n2",
                            "node_stable_id": "n2-criteria",
                            "label": "Phần 2: 5 Tiêu chí nghiệm thu",
                            "slide_ref": "Slide 16-25",
                            "children": [
                                {"id": "n2-1", "node_stable_id": "n2-1-cut", "label": "Lát cắt 1 câu", "slide_ref": "Slide 18", "children": []},
                                {"id": "n2-2", "node_stable_id": "n2-2-proof", "label": "Bằng chứng", "slide_ref": "Slide 22", "children": []}
                            ]
                        },
                        {
                            "id": "n3",
                            "node_stable_id": "n3-risk",
                            "label": "Phần 3: Các lớp rủi ro AI",
                            "slide_ref": "Slide 26-40",
                            "children": [
                                {
                                    "id": "n3-1",
                                    "node_stable_id": "n3-1-cost",
                                    "label": "Cost of error",
                                    "slide_ref": "Slide 28",
                                    "children": [
                                        {"id": "n3-1-1", "node_stable_id": "n3-1-1-auto", "label": "Automate", "slide_ref": "Slide 30", "children": []},
                                        {"id": "n3-1-2", "node_stable_id": "n3-1-2-aug", "label": "Augment", "slide_ref": "Slide 32", "children": []}
                                    ]
                                },
                                {"id": "n3-2", "node_stable_id": "n3-2-hard", "label": "4 Lớp chỗ khó", "slide_ref": "Slide 38", "children": []}
                            ]
                        }
                    ]
                }
            ]
        
        def inject_mock_progress(nodes):
            for n in nodes:
                # Giả lập tiến độ cho demo
                if n["id"] == "n1":
                    n["completion_percentage"] = 100.0
                    n["status"] = "mastered"
                elif n["id"] == "n2":
                    n["completion_percentage"] = 60.0
                    n["status"] = "reviewing"
                elif n["id"] == "n3":
                    n["completion_percentage"] = 30.0
                    n["status"] = "learning"
                else:
                    n["completion_percentage"] = 0.0
                    n["status"] = "new"
                if "children" in n and n["children"]:
                    inject_mock_progress(n["children"])
                    
        if user_id:
            inject_mock_progress(fallback_tree)

        return {
            "mindmap_id": "mm-default-d2",
            "title": "XÁC ĐỊNH BÀI TOÁN AI",
            "tree": fallback_tree
        }

    # Format DB mindmap nodes into tree
    nodes = db.query(MindmapNode).filter(MindmapNode.mindmap_id == mindmap.id).all()
    service = LearningProgressService(db=db) if user_id else None
    node_dict = {}
    for n in nodes:
        comp_pct = 0.0
        status = "new"
        if service:
            dto = service.calculate_node_progress_dto(user_id, n)
            comp_pct = dto.completion_percentage
            status = dto.status

        node_dict[n.id] = {
            "id": n.id,
            "node_stable_id": n.node_stable_id,
            "label": n.label,
            "slide_ref": f"Slide {n.page_number}" if n.page_number else "Tài liệu",
            "parent_node_id": n.parent_node_id,
            "completion_percentage": comp_pct,
            "status": status,
            "children": []
        }
    
    roots = []
    for n_id, n_data in node_dict.items():
        parent_id = n_data["parent_node_id"]
        if parent_id and parent_id in node_dict:
            node_dict[parent_id]["children"].append(n_data)
        else:
            roots.append(n_data)

    return {
        "mindmap_id": mindmap.id,
        "title": mindmap.title,
        "tree": roots
    }

# Structured Flashcards & Quizzes Dataset (30 items total across 6 topics, 5 items per topic)
BRANCH_LEARNING_DATA = {
    "n1-jtbd": {
        "review": [
            {"id": "fc-jtbd-1", "question": "Khái niệm JTBD (Jobs To Be Done) trong sản phẩm AI là gì?", "answer": "Là công việc/mục tiêu cốt lõi mà người dùng muốn hoàn thành trong thực tế.", "tag": "Core JTBD", "slide_ref": "Slide 5"},
            {"id": "fc-jtbd-2", "question": "Câu hỏi cốt lõi để xác định đúng JTBD là gì?", "answer": "Khách hàng đang cố gắng hoàn thành công việc gì trong bối cảnh thực tế?", "tag": "Core JTBD", "slide_ref": "Slide 8"},
            {"id": "fc-jtbd-3", "question": "Tại sao phân biệt JTBD và Tính năng (Feature) lại quan trọng?", "answer": "Tính năng AI có thể thay đổi nhanh, nhưng nhu cầu JTBD của con người mang tính ổn định.", "tag": "Core JTBD", "slide_ref": "Slide 8"},
            {"id": "fc-jtbd-4", "question": "Điểm mấu chốt để thiết kế AI Agent giải quyết JTBD hiệu quả?", "answer": "Tập trung giải quyết rào cản (Anxieties) và tối ưu luồng công việc thực tế.", "tag": "Core JTBD", "slide_ref": "Slide 10"},
            {"id": "fc-jtbd-5", "question": "Khái niệm 'Alternative' (Giải pháp thay thế) trong JTBD là gì?", "answer": "Các phương pháp người dùng đang dùng (Excel, thủ công, thuê người) trước khi có AI.", "tag": "JTBD Alternatives", "slide_ref": "Slide 12"}
        ],
        "quiz": [
            {"id": "qz-jtbd-1", "question": "Khi xác định JTBD cho sản phẩm AI, trọng tâm cốt lõi là gì?", "answer": "B. Công việc/mục tiêu thực tế mà người dùng muốn hoàn thành", "options": ["A. Số lượng thuật toán AI phức tạp", "B. Công việc/mục tiêu thực tế mà người dùng muốn hoàn thành", "C. Giao diện người dùng có màu đẹp hay không", "D. Mã nguồn mở hay mã nguồn đóng"], "tag": "Core JTBD", "slide_ref": "Slide 5"},
            {"id": "qz-jtbd-2", "question": "Câu hỏi đúng nhất để khám phá Core JTBD của học viên là gì?", "answer": "C. Khách hàng đang cố hoàn thành việc gì trong bối cảnh thực tế?", "options": ["A. Khách hàng muốn tính năng AI nào?", "B. Khách hàng thích dùng model nào của OpenAI?", "C. Khách hàng đang cố hoàn thành việc gì trong bối cảnh thực tế?", "D. Khách hàng có thích nút bấm màu xanh không?"], "tag": "Core JTBD", "slide_ref": "Slide 8"},
            {"id": "qz-jtbd-3", "question": "Tại sao nhà phát triển AI nên ưu tiên thiết kế theo JTBD thay vì chạy theo tính năng?", "answer": "A. Vì tính năng công nghệ dễ lỗi thời, còn JTBD của người dùng mang tính bền vững", "options": ["A. Vì tính năng công nghệ dễ lỗi thời, còn JTBD của người dùng mang tính bền vững", "B. Vì thiết kế theo tính năng rẻ tiền hơn", "C. Vì JTBD không cần viết mã lập trình", "D. Vì AI không thể chạy nếu thiếu JTBD"], "tag": "Core JTBD", "slide_ref": "Slide 8"},
            {"id": "qz-jtbd-4", "question": "Khi thiết kế AI Agent giải quyết JTBD, yếu tố nào cần được tối ưu?", "answer": "B. Giải quyết rào cản lo âu (Anxieties) và mượt mà luồng công việc", "options": ["A. Tăng dung lượng file tải về", "B. Giải quyết rào cản lo âu (Anxieties) và mượt mà luồng công việc", "C. Yêu cầu đăng nhập 3 lần", "D. Tăng thời gian chờ phản hồi"], "tag": "Core JTBD", "slide_ref": "Slide 10"},
            {"id": "qz-jtbd-5", "question": "Trong khung JTBD, 'Alternative' đại diện cho yếu tố nào?", "answer": "A. Giải pháp thay thế người dùng đang áp dụng trước khi có AI", "options": ["A. Giải pháp thay thế người dùng đang áp dụng trước khi có AI", "B. Một model AI đối thủ", "C. Lỗi hệ thống phát sinh", "D. Màn hình cài đặt tài khoản"], "tag": "JTBD Alternatives", "slide_ref": "Slide 12"}
        ]
    },
    "n1-1-core": {
        "review": [
            {"id": "fc-core-1", "question": "Khái niệm Core JTBD tập trung vào khía cạnh nào?", "answer": "Mục đích cốt lõi đằng sau hành vi tiêu dùng của khách hàng.", "tag": "Core JTBD", "slide_ref": "Slide 8"},
            {"id": "fc-core-2", "question": "Yếu tố quyết định sự thành bại của AI Agent theo Core JTBD?", "answer": "Mức độ đáp ứng đầu ra hoàn chỉnh của công việc cần làm.", "tag": "Core JTBD", "slide_ref": "Slide 9"},
            {"id": "fc-core-3", "question": "Cách phân biệt nhu cầu thực sự và yêu cầu hình thức?", "answer": "Hỏi 'tại sao' 5 lần đằng sau yêu cầu tính năng ban đầu.", "tag": "Core JTBD", "slide_ref": "Slide 9"},
            {"id": "fc-core-4", "question": "Core JTBD hỗ trợ đội ngũ sản phẩm như thế nào?", "answer": "Giúp tập trung nguồn lực vào tính năng quan trọng nhất.", "tag": "Core JTBD", "slide_ref": "Slide 10"},
            {"id": "fc-core-5", "question": "Dấu hiệu của một phát biểu Core JTBD chất lượng?", "answer": "Mô tả kết quả công việc độc lập với bất kỳ giải pháp kỹ thuật nào.", "tag": "Core JTBD", "slide_ref": "Slide 11"}
        ],
        "quiz": [
            {"id": "qz-core-1", "question": "Phát biểu nào mô tả chính xác mục tiêu của Core JTBD?", "answer": "A. Xác định lý do cốt lõi người dùng chọn giải pháp", "options": ["A. Xác định lý do cốt lõi người dùng chọn giải pháp", "B. Tối ưu hóa thời gian chạy CPU", "C. Tạo biểu mẫu thu thập dữ liệu", "D. Viết tài liệu hướng dẫn sử dụng"], "tag": "Core JTBD", "slide_ref": "Slide 8"},
            {"id": "qz-core-2", "question": "Cách hiệu quả nhất để xác định Core JTBD cho AI?", "answer": "C. Phỏng vấn sâu hành vi thực tế và kết quả người dùng mong muốn", "options": ["A. Tự đoán theo sở thích cá nhân", "B. Xem mã nguồn của dự án khác", "C. Phỏng vấn sâu hành vi thực tế và kết quả người dùng mong muốn", "D. Đọc thông số phần cứng"], "tag": "Core JTBD", "slide_ref": "Slide 9"},
            {"id": "qz-core-3", "question": "Khi người dùng yêu cầu 'thêm nút xuất Excel', Core JTBD tương ứng là gì?", "answer": "B. Người dùng muốn báo cáo số liệu dễ dàng chia sẻ cho quản lý", "options": ["A. Người dùng thích màu xanh của Excel", "B. Người dùng muốn báo cáo số liệu dễ dàng chia sẻ cho quản lý", "C. Người dùng muốn máy tính chạy nhanh hơn", "D. Người dùng muốn học lập trình"], "tag": "Core JTBD", "slide_ref": "Slide 9"},
            {"id": "qz-core-4", "question": "Thành phần nào KHÔNG nằm trong mô hình Core JTBD?", "answer": "D. Tốc độ quạt tản nhiệt của máy chủ", "options": ["A. Bối cảnh công việc (Context)", "B. Kết quả mong đợi (Outcome)", "C. Rào cản thực hiện (Pain)", "D. Tốc độ quạt tản nhiệt của máy chủ"], "tag": "Core JTBD", "slide_ref": "Slide 10"},
            {"id": "qz-core-5", "question": "Tại sao phát biểu Core JTBD không nên chứa tên công nghệ?", "answer": "A. Vì công nghệ thay đổi liên tục nhưng nhu cầu cốt lõi ít thay đổi", "options": ["A. Vì công nghệ thay đổi liên tục nhưng nhu cầu cốt lõi ít thay đổi", "B. Vì công nghệ là bí mật thương mại", "C. Vì luật pháp cấm", "D. Vì máy tính không hiểu tên công nghệ"], "tag": "Core JTBD", "slide_ref": "Slide 11"}
        ]
    },
    "n1-2-alt": {
        "review": [
            {"id": "fc-alt-1", "question": "Giải pháp thay thế (Alternative) cạnh tranh với AI như thế nào?", "answer": "Cạnh tranh trực tiếp về thói quen, chi phí và mức độ tin tưởng.", "tag": "Alternatives", "slide_ref": "Slide 12"},
            {"id": "fc-alt-2", "question": "Lý do người dùng từ chối AI để quay lại giải pháp truyền thống?", "answer": "Do lo ngại độ tin cậy thấp hoặc thao tác AI quá phức tạp.", "tag": "Alternatives", "slide_ref": "Slide 13"},
            {"id": "fc-alt-3", "question": "Động lực đẩy (Push) trong phân tích giải pháp cũ là gì?", "answer": "Sự bất tiện, tốn thời gian và sai sót của phương pháp cũ.", "tag": "Alternatives", "slide_ref": "Slide 14"},
            {"id": "fc-alt-4", "question": "Động lực kéo (Pull) đối với sản phẩm AI mới là gì?", "answer": "Sự nhanh chóng, thông minh và giá trị vượt trội AI mang lại.", "tag": "Alternatives", "slide_ref": "Slide 14"},
            {"id": "fc-alt-5", "question": "Mục tiêu khi so sánh AI với các giải pháp thay thế?", "answer": "Đảm bảo lợi ích của AI vượt trội ít nhất 3x-5x so với cách làm cũ.", "tag": "Alternatives", "slide_ref": "Slide 15"}
        ],
        "quiz": [
            {"id": "qz-alt-1", "question": "Trong phân tích JTBD, 'Push' được định nghĩa là gì?", "answer": "B. Những điểm đau và sự bất tiện từ giải pháp hiện tại đẩy người dùng đi tìm giải pháp mới", "options": ["A. Lực đẩy vật lý trên màn hình", "B. Những điểm đau và sự bất tiện từ giải pháp hiện tại đẩy người dùng đi tìm giải pháp mới", "C. Thông báo push notification", "D. Lệnh push code lên GitHub"], "tag": "Alternatives", "slide_ref": "Slide 14"},
            {"id": "qz-alt-2", "question": "Đối thủ cạnh tranh lớn nhất của một AI Agent mới ra mắt thường là gì?", "answer": "C. Thói quen xử lý thủ công hoặc file Excel hiện có của người dùng", "options": ["A. Các tập đoàn công nghệ lớn", "B. Trình duyệt web", "C. Thói quen xử lý thủ công hoặc file Excel hiện có của người dùng", "D. Các trò chơi điện tử"], "tag": "Alternatives", "slide_ref": "Slide 12"},
            {"id": "qz-alt-3", "question": "Yếu tố 'Habit' (Thói quen) ảnh hưởng thế nào đến việc áp dụng AI?", "answer": "A. Làm người dùng ngại thay đổi dù AI có thể tốt hơn", "options": ["A. Làm người dùng ngại thay đổi dù AI có thể tốt hơn", "B. Giúp AI chạy nhanh hơn 2 lần", "C. Giảm dung lượng lưu trữ", "D. Tự động sửa lỗi sai trong code"], "tag": "Alternatives", "slide_ref": "Slide 13"},
            {"id": "qz-alt-4", "question": "Để người dùng sẵn sàng bỏ giải pháp cũ sang dùng AI, sản phẩm AI cần đạt điều kiện gì?", "answer": "B. Sức hút (Pull) + Sự thúc đẩy (Push) phải lớn hơn Thói quen (Habit) + Sự lo âu (Anxiety)", "options": ["A. Giá thành phải là 0 đồng", "B. Sức hút (Pull) + Sự thúc đẩy (Push) phải lớn hơn Thói quen (Habit) + Sự lo âu (Anxiety)", "C. Phải có giao diện màu vàng", "D. Phải chạy trên điện thoại di động"], "tag": "Alternatives", "slide_ref": "Slide 14"},
            {"id": "qz-alt-5", "question": "Cách thu thập dữ liệu về giải pháp thay thế chính xác nhất?", "answer": "A. Quan sát thực tế người dùng thao tác với công cụ cũ", "options": ["A. Quan sát thực tế người dùng thao tác với công cụ cũ", "B. Tự suy đoán trong phòng họp", "C. Hỏi ý kiến lập trình viên backend", "D. Đọc tin tức trên báo chí"], "tag": "Alternatives", "slide_ref": "Slide 15"}
        ]
    },
    "n2-criteria": {
        "review": [
            {"id": "fc-crit-1", "question": "Định nghĩa tiêu chí 'Lát cắt 1 câu' (One-sentence slice)?", "answer": "Câu mô tả ngắn chứa đúng đầu vào, hành động AI và đầu ra đo lường được.", "tag": "Lát cắt 1 câu", "slide_ref": "Slide 18"},
            {"id": "fc-crit-2", "question": "Tại sao tiêu chí nghiệm thu AI phải đo lường bằng con số?", "answer": "Để có thể chạy bài kiểm tra tự động (Eval) và đánh giá khách quan.", "tag": "5 Tiêu chí", "slide_ref": "Slide 19"},
            {"id": "fc-crit-3", "question": "Yếu tố nào làm nên một Golden Set kiểm thử chất lượng?", "answer": "Dữ liệu đa dạng, phủ đủ ca thông thường và ca biên (edge cases).", "tag": "Golden Set", "slide_ref": "Slide 20"},
            {"id": "fc-crit-4", "question": "Thế nào là 'Bằng chứng nghiệm thu' (Proof)?", "answer": "Kết quả đo thực tế trên tập Golden Set kèm log hệ thống minh bạch.", "tag": "Bằng chứng", "slide_ref": "Slide 22"},
            {"id": "fc-crit-5", "question": "Quy trình xử lý khi kết quả Eval thấp hơn Quality Bar?", "answer": "Thực hiện Gap Analysis (Phân tích khoảng cách) và điều chỉnh prompt/RAG.", "tag": "Gap Analysis", "slide_ref": "Slide 24"}
        ],
        "quiz": [
            {"id": "qz-crit-1", "question": "Tiêu chí nghiệm thu AI nào dưới đây là chuẩn mực?", "answer": "A. AI tự động trích xuất đúng >=90% khái niệm từ slide PDF dưới 5 giây", "options": ["A. AI tự động trích xuất đúng >=90% khái niệm từ slide PDF dưới 5 giây", "B. AI trả lời hay và tạo ấn tượng tốt", "C. Mô hình AI sử dụng công nghệ mới nhất năm 2026", "D. Hệ thống hoạt động siêu nhanh"], "tag": "5 Tiêu chí", "slide_ref": "Slide 18"},
            {"id": "qz-crit-2", "question": "Điểm khác biệt lớn nhất giữa nghiệm thu AI và phần mềm truyền thống?", "answer": "C. Nghiệm thu AI dựa trên xác suất và chấp nhận ngưỡng sai số được xác định trước", "options": ["A. Phần mềm truyền thống không cần viết test", "B. AI không bao giờ gây ra lỗi", "C. Nghiệm thu AI dựa trên xác suất và chấp nhận ngưỡng sai số được xác định trước", "D. AI chỉ nghiệm thu 1 lần duy nhất"], "tag": "5 Tiêu chí", "slide_ref": "Slide 19"},
            {"id": "qz-crit-3", "question": "Tập Golden Set dùng trong nghiệm thu AI chứa thông tin gì?", "answer": "B. Bộ dữ liệu đầu vào mẫu kèm kết quả đáp án chuẩn đã thẩm định", "options": ["A. Danh sách các lỗi lập trình", "B. Bộ dữ liệu đầu vào mẫu kèm kết quả đáp án chuẩn đã thẩm định", "C. Mật khẩu tài khoản admin", "D. Lịch sử giao dịch ngân hàng"], "tag": "Golden Set", "slide_ref": "Slide 20"},
            {"id": "qz-crit-4", "question": "Yếu tố nào thể hiện tính minh bạch của bằng chứng nghiệm thu?", "answer": "A. Log chạy chi tiết kèm đường dẫn kết quả kiểm thử trên từng test case", "options": ["A. Log chạy chi tiết kèm đường dẫn kết quả kiểm thử trên từng test case", "B. Lời hứa của trưởng nhóm", "C. Ảnh chụp màn hình không rõ số liệu", "D. Bản cam kết bảo mật"], "tag": "Bằng chứng", "slide_ref": "Slide 22"},
            {"id": "qz-crit-5", "question": "Nếu điểm Quality Bar quy định là 85% nhưng AI chỉ đạt 78%, nhóm cần làm gì?", "answer": "D. Phân tích nguyên nhân khoảng cách (Gap) và đề xuất phương án tối ưu", "options": ["A. Sửa lại điểm Quality Bar thành 75%", "B. Xoá bớt các bài test khó", "C. Báo cáo dối gian là đạt 85%", "D. Phân tích nguyên nhân khoảng cách (Gap) và đề xuất phương án tối ưu"], "tag": "Gap Analysis", "slide_ref": "Slide 24"}
        ]
    },
    "n2-1-cut": {
        "review": [
            {"id": "fc-cut-1", "question": "Cấu trúc tiêu chuẩn của một 'Lát cắt 1 câu'?", "answer": "[Đối tượng] + [Hành động AI] + [Chỉ số nghiệm thu đo lường].", "tag": "Lát cắt 1 câu", "slide_ref": "Slide 18"},
            {"id": "fc-cut-2", "question": "Tại sao lại gọi là 'Lát cắt' (Slice)?", "answer": "Vì nó cắt dọc từ giao diện đầu vào tới kết quả đầu ra trọn vẹn.", "tag": "Lát cắt 1 câu", "slide_ref": "Slide 18"},
            {"id": "fc-cut-3", "question": "Tác hại của tiêu chí mơ hồ như 'Trả lời thông minh'?", "answer": "Không thể lập trình bài kiểm thử tự động và dễ gây tranh cãi.", "tag": "Lát cắt 1 câu", "slide_ref": "Slide 19"},
            {"id": "fc-cut-4", "question": "Một lát cắt nghiệm thu có cần chứa thời gian phản hồi không?", "answer": "Có, chỉ số Latency (thời gian xử lý) là một thành phần bắt buộc.", "tag": "Lát cắt 1 câu", "slide_ref": "Slide 19"},
            {"id": "fc-cut-5", "question": "Cách viết lát cắt 1 câu cho tính năng tạo Quiz tự động?", "answer": "AI tạo 5 câu quiz chuẩn từ nhánh slide được chọn trong dưới 3 giây.", "tag": "Lát cắt 1 câu", "slide_ref": "Slide 19"}
        ],
        "quiz": [
            {"id": "qz-cut-1", "question": "Tiêu chí 'Lát cắt 1 câu' giúp giải quyết vấn đề gì trong dự án AI?", "answer": "A. Biến yêu cầu mơ hồ thành thước đo cụ thể có thể kiểm thử tự động", "options": ["A. Biến yêu cầu mơ hồ thành thước đo cụ thể có thể kiểm thử tự động", "B. Tăng dung lượng lưu trữ server", "C. Giảm tiền mua tên miền", "D. Tạo hình ảnh minh họa cho slide"], "tag": "Lát cắt 1 câu", "slide_ref": "Slide 18"},
            {"id": "qz-cut-2", "question": "Đâu là thành phần BẮT BUỘC có trong một câu nghiệm thu chuẩn?", "answer": "C. Chỉ số thành công đo lường được bằng số liệu", "options": ["A. Tên tác giả bài viết", "B. Danh sách lập trình viên", "C. Chỉ số thành công đo lường được bằng số liệu", "D. Địa chỉ MAC của máy tính"], "tag": "Lát cắt 1 câu", "slide_ref": "Slide 18"},
            {"id": "qz-cut-3", "question": "Khi viết câu nghiệm thu AI, từ ngữ nào sau đây NÊN TRÁNH dùng?", "answer": "B. 'Rất mượt mà', 'siêu thông minh'", "options": ["A. 'Chính xác >=90%'", "B. 'Rất mượt mà', 'siêu thông minh'", "C. 'Thời gian xử lý < 2 giây'", "D. 'Tỉ lệ bỏ sót < 5%'"], "tag": "Lát cắt 1 câu", "slide_ref": "Slide 19"},
            {"id": "qz-cut-4", "question": "Tại sao câu nghiệm thu cần định nghĩa rõ đối tượng người dùng?", "answer": "A. Vì mỗi đối tượng người dùng có kỳ vọng và bối cảnh khác nhau", "options": ["A. Vì mỗi đối tượng người dùng có kỳ vọng và bối cảnh khác nhau", "B. Để đăng ký bản quyền", "C. Để thiết kế logo", "D. Để mua thẻ SIM"], "tag": "Lát cắt 1 câu", "slide_ref": "Slide 19"},
            {"id": "qz-cut-5", "question": "Khái niệm Vertical Slice (Lát cắt dọc) ám chỉ điều gì?", "answer": "C. Kiểm thử trọn vẹn từ giao diện người dùng tới xử lý AI backend", "options": ["A. Cắt nhỏ màn hình hiển thị", "B. Chia đôi cơ sở dữ liệu", "C. Kiểm thử trọn vẹn từ giao diện người dùng tới xử lý AI backend", "D. Xoá bớt dữ liệu rác"], "tag": "Lát cắt 1 câu", "slide_ref": "Slide 19"}
        ]
    },
    "n2-2-proof": {
        "review": [
            {"id": "fc-prf-1", "question": "Khái niệm 'Proof of Acceptance' trong AI Agent là gì?", "answer": "Là chứng cứ bằng số liệu và log chạy khẳng định AI đáp ứng tiêu chí.", "tag": "Bằng chứng", "slide_ref": "Slide 22"},
            {"id": "fc-prf-2", "question": "Tập dữ liệu nào được dùng làm gốc để lấy bằng chứng?", "answer": "Golden Set chứa các test case đã được dán nhãn chuẩn.", "tag": "Golden Set", "slide_ref": "Slide 22"},
            {"id": "fc-prf-3", "question": "Chỉ số Precision và Recall phản ánh điều gì trong Eval?", "answer": "Precision đo độ chính xác kết quả trả về, Recall đo khả năng tránh bỏ sót.", "tag": "Eval Metrics", "slide_ref": "Slide 23"},
            {"id": "fc-prf-4", "question": "Tại sao cần lưu vết Scaffold Log khi thử nghiệm?", "answer": "Để theo dõi nguyên văn phản hồi người dùng và các lỗi phát sinh.", "tag": "Validation Log", "slide_ref": "Slide 24"},
            {"id": "fc-prf-5", "question": "Mục đích của việc đo lường thời gian phản hồi (Latency)?", "answer": "Đảm bảo trải nghiệm người dùng không bị gián đoạn do AI phản hồi quá chậm.", "tag": "Bằng chứng", "slide_ref": "Slide 25"}
        ],
        "quiz": [
            {"id": "qz-prf-1", "question": "Bằng chứng nghiệm thu AI đạt chuẩn cần minh bạch yếu tố nào?", "answer": "A. Kết quả chạy tự động trên tập Golden Set kèm log thời gian thực", "options": ["A. Kết quả chạy tự động trên tập Golden Set kèm log thời gian thực", "B. Cảm nhận cá nhân của người kiểm thử", "C. Số lượng dòng bình luận trong code", "D. Giấy chứng nhận bảo hành"], "tag": "Bằng chứng", "slide_ref": "Slide 22"},
            {"id": "qz-prf-2", "question": "Trong việc đánh giá bài toán tìm kiếm (Retrieval), chỉ số Recall = 100% có nghĩa là gì?", "answer": "B. AI không bỏ sót bất kỳ tài liệu liên quan nào", "options": ["A. AI không bao giờ trả lời sai", "B. AI không bỏ sót bất kỳ tài liệu liên quan nào", "C. AI chạy trong 0 giây", "D. AI tự động sửa lỗi tiếng Việt"], "tag": "Eval Metrics", "slide_ref": "Slide 23"},
            {"id": "qz-prf-3", "question": "Scaffold Log ghi nhận những thông tin gì trong kỳ kiểm thử?", "answer": "C. Người dùng thử, câu hỏi nguyên văn, phản hồi AI và mức độ nghiêm trọng của lỗi", "options": ["A. Địa chỉ IP nhà riêng của lập trình viên", "B. Thông tin tài khoản ngân hàng", "C. Người dùng thử, câu hỏi nguyên văn, phản hồi AI và mức độ nghiêm trọng của lỗi", "D. Danh sách các bài hát đã nghe"], "tag": "Validation Log", "slide_ref": "Slide 24"},
            {"id": "qz-prf-4", "question": "Khi kết quả chạy Eval cho thấy AI hay bị ảo giác (hallucination), giải pháp là gì?", "answer": "A. Cải thiện quy trình RAG, bổ sung Prompt Guardrails và tài liệu nguồn", "options": ["A. Cải thiện quy trình RAG, bổ sung Prompt Guardrails và tài liệu nguồn", "B. Tắt máy tính đi bật lại", "C. Đổi tên ứng dụng", "D. Tăng giá bán sản phẩm"], "tag": "Gap Analysis", "slide_ref": "Slide 24"},
            {"id": "qz-prf-5", "question": "Thời gian phản hồi (Latency) lý tưởng cho một Trợ lý AI hội thoại là bao nhiêu?", "answer": "B. Dưới 2-3 giây cho câu trả lời đầu tiên", "options": ["A. Dưới 10 phút", "B. Dưới 2-3 giây cho câu trả lời đầu tiên", "C. Đúng 60 giây", "D. Không quan trọng thời gian"], "tag": "Bằng chứng", "slide_ref": "Slide 25"}
        ]
    },
    "n3-risk": {
        "review": [
            {"id": "fc-risk-1", "question": "Khái niệm 'Cost of Error' (Chi phí rủi ro sai sót) là gì?", "answer": "Tổn thất phát sinh khi AI đưa ra quyết định hoặc phản hồi sai.", "tag": "Cost of error", "slide_ref": "Slide 28"},
            {"id": "fc-risk-2", "question": "Sự khác biệt giữa Automate và Augment?", "answer": "Automate AI thực thi tự động; Augment AI đưa gợi ý để con người duyệt.", "tag": "Automate vs Augment", "slide_ref": "Slide 30"},
            {"id": "fc-risk-3", "question": "False Positive (Dương tính giả) gây hậu quả gì?", "answer": "Nhận nhầm đối tượng bình thường thành lỗi (vd: khóa nhầm tài khoản thật).", "tag": "False Positive", "slide_ref": "Slide 32"},
            {"id": "fc-risk-4", "question": "False Negative (Âm tính giả) gây tổn thất gì?", "answer": "Bỏ sót lỗi thực tế (vd: bỏ sót hồ sơ gian lận hoặc ứng viên giỏi).", "tag": "False Negative", "slide_ref": "Slide 32"},
            {"id": "fc-risk-5", "question": "Giải pháp giảm thiểu rủi ro khi Cost of Error rất cao?", "answer": "Áp dụng mô hình Augment có con người can thiệp (Human-in-the-loop).", "tag": "Rủi ro AI", "slide_ref": "Slide 35"}
        ],
        "quiz": [
            {"id": "qz-risk-1", "question": "Trong bài toán AI lọc tự động CV xin việc, đâu là rủi ro 'False Negative' nguy hiểm nhất?", "answer": "A. AI loại bỏ nhầm một ứng viên rất xuất sắc", "options": ["A. AI loại bỏ nhầm một ứng viên rất xuất sắc", "B. AI chọn nhầm ứng viên không đạt", "C. AI xử lý CV mất 10 giây", "D. AI không đọc được file docx"], "tag": "Cost of error", "slide_ref": "Slide 28"},
            {"id": "qz-risk-2", "question": "Khi nào nên sử dụng chiến lược 'Automate' thay vì 'Augment'?", "answer": "A. Khi Cost of Error thấp và tốc độ xử lý hàng loạt là ưu tiên hàng đầu", "options": ["A. Khi Cost of Error thấp và tốc độ xử lý hàng loạt là ưu tiên hàng đầu", "B. Khi quyết định liên quan trực tiếp đến tính mạng con người", "C. Khi dữ liệu đầu vào cực kỳ mơ hồ", "D. Khi không có dữ liệu huấn luyện"], "tag": "Automate vs Augment", "slide_ref": "Slide 30"},
            {"id": "qz-risk-3", "question": "Thuật ngữ 'Human-in-the-loop' đóng vai trò gì trong việc giảm thiểu rủi ro AI?", "answer": "A. Giữ con người ở bước phê duyệt cuối cùng trước khi thực thi", "options": ["A. Giữ con người ở bước phê duyệt cuối cùng trước khi thực thi", "B. Ép con người phải tự gõ lại toàn bộ văn bản", "C. Thay thế AI bằng nhân sự thủ công", "D. Tăng chi phí API gấp đôi"], "tag": "Human-in-the-loop", "slide_ref": "Slide 30"},
            {"id": "qz-risk-4", "question": "Giả sử hệ thống phát hiện gian lận ngân hàng báo động sai cho tài khoản hợp lệ, đây là loại lỗi gì?", "answer": "A. False Positive (Dương tính giả)", "options": ["A. False Positive (Dương tính giả)", "B. False Negative (Âm tính giả)", "C. True Negative", "D. System Crash"], "tag": "False Positive", "slide_ref": "Slide 32"},
            {"id": "qz-risk-5", "question": "Để bảo vệ AI Agent khỏi rủi ro Prompt Injection, biện pháp nào hiệu quả nhất?", "answer": "A. Đặt lớp Guardrails kiểm tra và lọc dữ liệu đầu vào/đầu ra", "options": ["A. Đặt lớp Guardrails kiểm tra và lọc dữ liệu đầu vào/đầu ra", "B. Tăng dung lượng RAM máy chủ", "C. Đổi tên model AI", "D. Khóa màn hình máy tính"], "tag": "Prompt Injection", "slide_ref": "Slide 35"}
        ]
    },
    "n3-1-cost": {
        "review": [
            {"id": "fc-cst-1", "question": "Làm sao để định lượng Cost of Error của ứng dụng AI?", "answer": "Tính toán chi phí tài chính, rủi ro pháp lý và thiệt hại uy tín khi AI sai.", "tag": "Cost of error", "slide_ref": "Slide 28"},
            {"id": "fc-cst-2", "question": "Ví dụ bài toán AI có Cost of Error cực kỳ cao?", "answer": "Chẩn đoán y tế tự động hoặc tự động phê duyệt khoản vay ngân hàng.", "tag": "Cost of error", "slide_ref": "Slide 28"},
            {"id": "fc-cst-3", "question": "Ví dụ bài toán AI có Cost of Error thấp?", "answer": "Gợi ý bài hát, tự động sửa lỗi chính tả văn bản.", "tag": "Cost of error", "slide_ref": "Slide 29"},
            {"id": "fc-cst-4", "question": "Mối quan hệ giữa Cost of Error và mức độ kiểm duyệt?", "answer": "Cost of Error càng cao thì mức độ kiểm duyệt của con người phải càng chặt.", "tag": "Cost of error", "slide_ref": "Slide 29"},
            {"id": "fc-cst-5", "question": "Lỗi hallucination (ảo giác) của LLM ảnh hưởng thế nào đến Cost of Error?", "answer": "Làm tăng rủi ro đưa tin sai sự thật, làm giảm lòng tin người dùng.", "tag": "Cost of error", "slide_ref": "Slide 29"}
        ],
        "quiz": [
            {"id": "qz-cst-1", "question": "Trong 4 ứng dụng AI sau, ứng dụng nào có Cost of Error cao nhất?", "answer": "C. AI tự động điều khiển xe ô tô không người lái", "options": ["A. AI gợi ý danh sách xem phim", "B. AI tự tạo ảnh nghệ thuật", "C. AI tự động điều khiển xe ô tô không người lái", "D. AI kiểm tra lỗi chính tả tiếng Anh"], "tag": "Cost of error", "slide_ref": "Slide 28"},
            {"id": "qz-cst-2", "question": "Tại sao việc xác định Cost of Error lại bắt buộc trước khi lập trình AI?", "answer": "A. Để lựa chọn kiến trúc hệ thống (Automate vs Augment) và mức độ Guardrails phù hợp", "options": ["A. Để lựa chọn kiến trúc hệ thống (Automate vs Augment) và mức độ Guardrails phù hợp", "B. Để tính tiền thuế doanh nghiệp", "C. Để chọn ngôn ngữ lập trình Python hay Java", "D. Để in tài liệu quảng cáo"], "tag": "Cost of error", "slide_ref": "Slide 28"},
            {"id": "qz-cst-3", "question": "Khi Cost of Error của bài toán rất thấp, chiến lược thiết kế AI tối ưu nhất là gì?", "answer": "B. Cho phép AI phản hồi tự động trực tiếp để tối ưu tốc độ và chi phí", "options": ["A. Thuê 100 người kiểm duyệt thủ công", "B. Cho phép AI phản hồi tự động trực tiếp để tối ưu tốc độ và chi phí", "C. Dừng dự án không triển khai", "D. Yêu cầu người dùng xác minh bằng CCCD"], "tag": "Cost of error", "slide_ref": "Slide 29"},
            {"id": "qz-cst-4", "question": "Hậu quả nặng nề nhất khi bỏ qua việc phân tích Cost of Error?", "answer": "D. Sản phẩm AI gây thiệt hại nghiêm trọng cho người dùng và sụp đổ uy tín thương hiệu", "options": ["A. Máy tính bị hết pin", "B. Chuột máy tính bị hỏng", "C. Màn hình bị giật lag", "D. Sản phẩm AI gây thiệt hại nghiêm trọng cho người dùng và sụp đổ uy tín thương hiệu"], "tag": "Cost of error", "slide_ref": "Slide 29"},
            {"id": "qz-cst-5", "question": "Chỉ số nào dùng để đo lường mức tổn thất tài chính trung bình trên mỗi lỗi của AI?", "answer": "A. Expected Error Cost = Probability(Error) * Severity(Damage)", "options": ["A. Expected Error Cost = Probability(Error) * Severity(Damage)", "B. Tốc độ quạt server", "C. Số trang tài liệu PDF", "D. Số lượng icon trên ứng dụng"], "tag": "Cost of error", "slide_ref": "Slide 29"}
        ]
    },
    "n3-1-1-auto": {
        "review": [
            {"id": "fc-aut-1", "question": "Ưu điểm lớn nhất của mô hình Automate là gì?", "answer": "Tốc độ xử lý tức thì và khả năng mở rộng quy mô lớn không tốn nhân sự.", "tag": "Automate", "slide_ref": "Slide 30"},
            {"id": "fc-aut-2", "question": "Điều kiện cần để áp dụng mô hình Automate an toàn?", "answer": "Bài toán có Cost of Error thấp và độ chính xác của AI đã được kiểm chứng cao.", "tag": "Automate", "slide_ref": "Slide 30"},
            {"id": "fc-aut-3", "question": "Rủi ro khi Automate một quy trình chưa chuẩn hóa?", "answer": "Nhân rộng lỗi sai với tốc độ nhanh hơn và khó khắc phục hậu quả.", "tag": "Automate", "slide_ref": "Slide 31"},
            {"id": "fc-aut-4", "question": "Cơ chế fallback trong Automate là gì?", "answer": "Chuyển giao cho con người xử lý khi chỉ số tin cậy của AI dưới ngưỡng.", "tag": "Automate Fallback", "slide_ref": "Slide 31"},
            {"id": "fc-aut-5", "question": "Cách đo lường hiệu quả của mô hình Automate?", "answer": "Tỷ lệ quy trình được xử lý hoàn toàn tự động không cần can thiệp (Straight-through rate).", "tag": "Automate Metrics", "slide_ref": "Slide 31"}
        ],
        "quiz": [
            {"id": "qz-aut-1", "question": "Tính năng nào sau đây phù hợp nhất để triển khai theo mô hình Automate?", "answer": "B. Phân loại email rác (Spam Filter) với độ tin cậy cao", "options": ["A. Phẫu thuật y tế từ xa", "B. Phân loại email rác (Spam Filter) với độ tin cậy cao", "C. Phê duyệt giải ngân khoản vay 10 tỷ đồng", "D. Thẩm định pháp lý hợp đồng mua bán nhà"], "tag": "Automate", "slide_ref": "Slide 30"},
            {"id": "qz-aut-2", "question": "Khái niệm Confidence Score Threshold (Ngưỡng tin cậy) trong Automate có tác dụng gì?", "answer": "A. Nếu AI tự tin >= 95% thì tự động thực thi, ngược lại chuyển cho con người duyệt", "options": ["A. Nếu AI tự tin >= 95% thì tự động thực thi, ngược lại chuyển cho con người duyệt", "B. Đặt giá cho sản phẩm", "C. Tự động xoá dữ liệu người dùng", "D. Tắt ứng dụng khi hết giờ làm việc"], "tag": "Automate", "slide_ref": "Slide 30"},
            {"id": "qz-aut-3", "question": "Khi hệ thống Automate gặp ca biên (Edge Case) chưa từng thấy, cơ chế an toàn nhất là gì?", "answer": "C. Chuyển hồ sơ sang kênh xử lý thủ công (Human Fallback Log)", "options": ["A. Tự đoán ngẫu nhiên một đáp án", "B. Đóng ứng dụng ngay lập tức", "C. Chuyển hồ sơ sang kênh xử lý thủ công (Human Fallback Log)", "D. Trả về thông báo lỗi vô nghĩa"], "tag": "Automate Fallback", "slide_ref": "Slide 31"},
            {"id": "qz-aut-4", "question": "Chỉ số Straight-Through Processing (STP) phản ánh điều gì?", "answer": "A. Tỷ lệ phần trăm giao dịch được AI hoàn tất từ A-Z mà không cần con người đụng tay", "options": ["A. Tỷ lệ phần trăm giao dịch được AI hoàn tất từ A-Z mà không cần con người đụng tay", "B. Tốc độ đường truyền internet", "C. Chi phí tiền điện máy tính", "D. Số dòng lệnh code trong project"], "tag": "Automate Metrics", "slide_ref": "Slide 31"},
            {"id": "qz-aut-5", "question": "Tại sao không nên áp dụng Automate 100% cho mọi bài toán AI?", "answer": "D. Vì AI luôn có xác suất sai sót và một số bài toán cần đến đạo đức/cảm xúc con người", "options": ["A. Vì tốn nhiều băng thông mạng", "B. Vì giao diện màn hình không đủ chỗ", "C. Vì máy tính sẽ bị quá nhiệt", "D. Vì AI luôn có xác suất sai sót và một số bài toán cần đến đạo đức/cảm xúc con người"], "tag": "Automate", "slide_ref": "Slide 31"}
        ]
    },
    "n3-1-2-aug": {
        "review": [
            {"id": "fc-aug-1", "question": "Bản chất của mô hình Augment (Gia tăng năng lực) là gì?", "answer": "AI đóng vai trò làm trợ lý gợi ý, con người giữ quyền ra quyết định.", "tag": "Augment", "slide_ref": "Slide 32"},
            {"id": "fc-aug-2", "question": "Trường hợp nào bắt buộc phải dùng mô hình Augment?", "answer": "Khi bài toán phức tạp, đòi hỏi trách nhiệm pháp lý hoặc đạo đức cao.", "tag": "Augment", "slide_ref": "Slide 32"},
            {"id": "fc-aug-3", "question": "Cách thiết kế UX cho mô hình Augment hiệu quả?", "answer": "Hiển thị rõ lý do AI gợi ý (Explainability) và cho phép chỉnh sửa dễ dàng.", "tag": "Augment UX", "slide_ref": "Slide 33"},
            {"id": "fc-aug-4", "question": "Lợi ích kép của mô hình Augment đối với AI?", "answer": "Tăng năng suất con người đồng thời thu thập phản hồi để huấn luyện AI tốt hơn.", "tag": "Augment Benefits", "slide_ref": "Slide 33"},
            {"id": "fc-aug-5", "question": "Điểm cân bằng giữa tốc độ và độ an toàn trong Augment?", "answer": "Giảm bớt các bước gõ phím thừa nhưng giữ lại nút bấm xác nhận cuối cùng.", "tag": "Augment Design", "slide_ref": "Slide 33"}
        ],
        "quiz": [
            {"id": "qz-aug-1", "question": "Mô hình thiết kế Augment đặt con người vào vị trí nào?", "answer": "B. Người giám sát và ra quyết định cuối cùng (Human-in-the-loop)", "options": ["A. Lập trình viên sửa lỗi", "B. Người giám sát và ra quyết định cuối cùng (Human-in-the-loop)", "C. Nạn nhân chịu lỗi", "D. Khách xem truyền hình"], "tag": "Augment", "slide_ref": "Slide 32"},
            {"id": "qz-aug-2", "question": "Đâu là ví dụ điển hình của mô hình Augment?", "answer": "A. AI gợi ý mã sơ bộ cho lập trình viên xem xét và nhấn Tab để chấp nhận", "options": ["A. AI gợi ý mã sơ bộ cho lập trình viên xem xét và nhấn Tab để chấp nhận", "B. Hệ thống trừ tiền tài khoản tự động", "C. Email tự động gửi rác", "D. Máy bán hàng tự động"], "tag": "Augment", "slide_ref": "Slide 32"},
            {"id": "qz-aug-3", "question": "Yếu tố 'Explainable AI' (AI có thể giải thích) trợ giúp mô hình Augment thế nào?", "answer": "C. Giúp con người hiểu tại sao AI đưa ra gợi ý đó để ra quyết định chính xác hơn", "options": ["A. Dịch tự động ra tiếng Pháp", "B. Đọc to văn bản lên loa", "C. Giúp con người hiểu tại sao AI đưa ra gợi ý đó để ra quyết định chính xác hơn", "D. Tự động đổi font chữ"], "tag": "Augment UX", "slide_ref": "Slide 33"},
            {"id": "qz-aug-4", "question": "Làm thế nào để đo lường mức độ tiết kiệm thời gian của mô hình Augment?", "answer": "A. So sánh thời gian con người tự làm 100% vs thời gian con người kiểm duyệt gợi ý của AI", "options": ["A. So sánh thời gian con người tự làm 100% vs thời gian con người kiểm duyệt gợi ý của AI", "B. Đo chiều dài bàn làm việc", "C. Đếm số lượng từ trong tài liệu", "D. Đo nhiệt độ phòng làm việc"], "tag": "Augment Benefits", "slide_ref": "Slide 33"},
            {"id": "qz-aug-5", "question": "Ưu điểm lớn nhất của Augment đối với việc tích lũy dữ liệu huấn luyện?", "answer": "B. Hành động chấp nhận/chỉnh sửa của con người là phản hồi RLHF chất lượng cao", "options": ["A. Giúp tăng tốc độ mạng", "B. Hành động chấp nhận/chỉnh sửa của con người là phản hồi RLHF chất lượng cao", "C. Tự động xóa file rác", "D. Giảm dung lượng pin tiêu thụ"], "tag": "Augment Design", "slide_ref": "Slide 33"}
        ]
    }
}

@router.get("/flashcards/{course_id}")
def get_course_flashcards(
    course_id: str,
    node_id: Optional[str] = Query(None),
    mode: Optional[str] = Query("review"),
    db: Session = Depends(get_db)
):
    target_mode = mode if mode in ["review", "quiz"] else "review"
    
    # If specific node_id requested, check DB first
    if node_id:
        card_ids = [r.flashcard_id for r in db.execute(node_flashcard_association.select().where(node_flashcard_association.c.node_id == node_id)).all()]
        if card_ids:
            cards = db.query(Flashcard).filter(Flashcard.id.in_(card_ids)).all()
            if cards:
                res = []
                for c in cards:
                    opts = c.options_json if isinstance(c.options_json, list) else [c.answer]
                    res.append({
                        "id": c.id,
                        "question": c.question,
                        "answer": c.answer,
                        "options": opts,
                        "tag": "Khái niệm",
                        "slide_ref": "Slide 1",
                        "difficulty": c.difficulty or "MEDIUM"
                    })
                return res
        
        # Branch fallback from BRANCH_LEARNING_DATA (5 items)
        if node_id in BRANCH_LEARNING_DATA:
            return BRANCH_LEARNING_DATA[node_id].get(target_mode, BRANCH_LEARNING_DATA[node_id]["review"])

    # If no node_id (Full Course), combine DB cards + fallback to guarantee 30 items
    cards = db.query(Flashcard).filter(Flashcard.course_id == course_id).all()
    res = []
    if cards:
        for c in cards:
            opts = c.options_json if isinstance(c.options_json, list) else [c.answer]
            res.append({
                "id": c.id,
                "question": c.question,
                "answer": c.answer,
                "options": opts,
                "tag": "Khái niệm",
                "slide_ref": "Slide 1",
                "difficulty": c.difficulty or "MEDIUM"
            })

    if len(res) >= 30:
        return res[:30]

    # Full course fallback (30 items)
    all_items = []
    for nid, data in BRANCH_LEARNING_DATA.items():
        if nid in ["n1-jtbd", "n1-2-alt", "n2-criteria", "n2-2-proof", "n3-risk", "n3-1-1-auto"]:
            items = data.get(target_mode, data["review"])
            all_items.extend(items)
            
    combined = res + all_items
    return combined[:30]

@router.post("/summary/generate")
def generate_summary_job(payload: Dict[str, Any], db: Session = Depends(get_db)):
    course_id = payload.get("course_id", "c-hackathon-d2")
    return {
        "job_id": f"job-summary-{course_id}",
        "status": "processing",
        "progress_percentage": 100,
        "message": "Đã hoàn thành trích xuất Mindmap & Flashcard."
    }

@router.post("/flashcards/personalize")
def personalize_flashcards(payload: Dict[str, Any], db: Session = Depends(get_db)):
    # payload: {"user_id": "...", "node_id": "...", "course_id": "..."}
    # Mock generating personalized flashcards based on wrong attempts
    return [
        {
            "id": "fc-pers-1",
            "question": "[Cá nhân hoá] Bạn đã trả lời sai phần Cost of Error. Hãy chọn lại: 'False Positive' nghĩa là gì?",
            "answer": "B. Nhận diện sai một thứ bình thường thành lỗi",
            "options": [
                "A. Bỏ sót lỗi",
                "B. Nhận diện sai một thứ bình thường thành lỗi",
                "C. Kết quả hoàn hảo",
                "D. Hệ thống sập"
            ],
            "tag": "Ôn tập lỗi sai",
            "slide_ref": "Slide 32",
            "difficulty": "HARD"
        },
        {
            "id": "fc-pers-2",
            "question": "[Cá nhân hoá] Khái niệm Automate khác Augment ở điểm nào?",
            "answer": "B. Automate giao toàn quyền, Augment hỗ trợ gợi ý",
            "options": [
                "A. Automate rẻ hơn",
                "B. Automate giao toàn quyền, Augment hỗ trợ gợi ý",
                "C. Không khác biệt",
                "D. Augment chạy độc lập"
            ],
            "tag": "Ôn tập lỗi sai",
            "slide_ref": "Slide 30",
            "difficulty": "MEDIUM"
        }
    ]
