# QA Test Cases - 20 Kịch bản kiểm thử (Feature Requirements)

Dưới đây là 20 Test Case dành riêng cho 4 luồng tính năng mới được yêu cầu. Đây là các kịch bản kiểm thử phần mềm (Software Testing Test Cases), kiểm tra trực tiếp logic, giao diện và luồng hoạt động của hệ thống (không phải Use Case hay bộ eval prompt).

| Test Case ID | Tên chức năng / Tiêu đề | Tiền điều kiện (Pre-condition) | Các bước thực hiện (Steps) | Kết quả mong đợi (Expected Result) |
|:---|:---|:---|:---|:---|
| **TC01** | Mindmap - Sinh cố định | Hệ thống có bộ slide bài học của ngày hôm đó (VD: Slide bài 1) | 1. Nhấn nút "Tạo Tổng kết AI".<br>2. Đợi AI xử lý xong. | Hệ thống sinh ra một cây Mindmap cố định, lấy nội dung chính xác từ bộ slide của ngày hôm đó. |
| **TC02** | Mindmap - Tính nhất quán | Đã sinh Mindmap cho bài học A một lần | 1. Nhấn tạo lại Mindmap cho bài học A. | Mindmap vẫn giữ nguyên cấu trúc nhánh, không bị random ra một cấu trúc hoàn toàn khác (do tính cố định). |
| **TC03** | Flashcard - Toàn bộ bài (30 câu) | Đã sinh xong Mindmap | 1. Chọn scope "Toàn bộ bài học".<br>2. Bấm "Ôn tập" (Flashcard).<br>3. Kiểm tra tổng số câu. | Hệ thống hiển thị đúng 30 câu hỏi trọng tâm bao quát toàn bộ nội dung bài học. |
| **TC04** | Take Quiz - Toàn bộ bài (30 câu) | Đã sinh xong Mindmap | 1. Chọn scope "Toàn bộ bài học".<br>2. Bấm "Take Quiz".<br>3. Kiểm tra tổng số câu. | Hệ thống hiển thị đúng 30 câu hỏi trắc nghiệm (Multiple Choice). |
| **TC05** | Flashcard - Nhánh nhỏ (5 câu) | Mindmap có nhiều nhánh phụ | 1. Click chọn một nhánh phụ bất kỳ (VD: Nhánh "Core JTBD").<br>2. Bấm "Luyện nhánh này" dưới dạng Flashcard. | Hệ thống hiển thị đúng 5 câu hỏi trọng tâm chỉ xoay quanh nội dung nhánh đó. |
| **TC06** | Take Quiz - Nhánh nhỏ (5 câu) | Mindmap có nhiều nhánh phụ | 1. Click chọn một nhánh phụ bất kỳ.<br>2. Bấm "Take Quiz" cho nhánh đó. | Hệ thống hiển thị đúng 5 câu hỏi trắc nghiệm liên quan chặt chẽ tới nhánh được chọn. |
| **TC07** | Mode Flashcard - UI lật thẻ | Đang ở chế độ Flashcard | 1. Xem màn hình hiển thị câu hỏi.<br>2. Click chuột vào thẻ. | Mặt trước hiện câu hỏi và gợi ý lật thẻ. Click vào sẽ lật (flip 3D) sang mặt sau hiển thị Đáp án đúng. |
| **TC08** | Mode Flashcard - Tracking Ôn tập | Đang ở chế độ Flashcard | 1. Lật thẻ xem đáp án.<br>2. Chọn nút "Đã thuộc" (Tích xanh) hoặc "Chưa thuộc" (X đỏ). | Thẻ tự động chuyển sang câu tiếp theo. Hệ thống lưu lại trạng thái thuộc/chưa thuộc. |
| **TC09** | Mode Take Quiz - UI trắc nghiệm | Đang ở chế độ Take Quiz | 1. Xem màn hình hiển thị câu hỏi. | Mặt trước thẻ hiển thị Câu hỏi và 4 Đáp án lựa chọn (A, B, C, D). Không có hiệu ứng flip thẻ. |
| **TC10** | Mode Take Quiz - Chọn đáp án đúng | Đang ở chế độ Take Quiz | 1. Click chọn đáp án đúng. | Nút đáp án vừa chọn hiển thị màu Xanh lá (Correct). Tự động ghi nhận điểm số. |
| **TC11** | Mode Take Quiz - Chọn đáp án sai | Đang ở chế độ Take Quiz | 1. Click chọn đáp án sai. | Nút đáp án vừa chọn hiển thị màu Đỏ (Wrong). Hệ thống đồng thời bôi Xanh đáp án đúng thật sự để học viên học được ngay. |
| **TC12** | Cá nhân hóa - Trạng thái Nút (Chưa học) | Học viên chưa học nhánh A (hoàn thành 0%) | 1. Click vào nhánh A trên Mindmap. | Nút "Cá nhân hóa lỗi sai" bị ẩn (Hidden). |
| **TC13** | Cá nhân hóa - Trạng thái Nút (Đã xong) | Học viên học xong nhánh A (hoàn thành 100%) | 1. Click vào nhánh A trên Mindmap. | Nút "Cá nhân hóa lỗi sai" bị ẩn (Hidden) vì không có lỗi sai nào. |
| **TC14** | Cá nhân hóa - Trạng thái Nút (Đang học) | Học viên đã làm nhánh A, đạt 40% | 1. Click vào nhánh A trên Mindmap. | Nút "Cá nhân hóa lỗi sai" hiện lên rõ ràng. |
| **TC15** | Cá nhân hóa - Trigger sinh thẻ | Click nút "Cá nhân hóa lỗi sai" | 1. Chọn nhánh đang đạt 30%.<br>2. Bấm nút "Cá nhân hóa lỗi sai". | AI tự động sinh lại một bộ 5 thẻ Flashcard mới, tập trung vào các câu hỏi học viên vừa làm sai. |
| **TC16** | Tracking Màu sắc - 100% (Màu Xanh) | Học viên nộp bài Take Quiz cho nhánh A | 1. Làm đúng 5/5 câu của nhánh A.<br>2. Bấm Nộp bài. | Nhánh A trên Mindmap hiển thị badge "100%" và có viền/nền màu Xanh lá (Green). |
| **TC17** | Tracking Màu sắc - 50-99% (Màu Vàng) | Học viên nộp bài Take Quiz cho nhánh B | 1. Làm đúng 3/5 câu (đạt 60%) nhánh B.<br>2. Bấm Nộp bài. | Nhánh B trên Mindmap hiển thị badge "60%" và có viền/nền màu Vàng (Yellow). |
| **TC18** | Tracking Màu sắc - Dưới 50% (Màu Đỏ) | Học viên nộp bài Take Quiz cho nhánh C | 1. Làm đúng 1/5 câu (đạt 20%) nhánh C.<br>2. Bấm Nộp bài. | Nhánh C trên Mindmap hiển thị badge "20%" và có viền/nền màu Đỏ (Red - Needs Work). |
| **TC19** | Tracking Tiến độ - Báo cáo nộp bài | Nộp bài toàn bộ nhánh hoặc bài học | 1. Hoàn thành bộ câu hỏi cuối cùng.<br>2. Bấm Nộp bài. | Có Pop-up hoặc màn hình Toast thông báo "% hoàn thành: X%" ghi nhận thành công lên hệ thống. |
| **TC20** | Tracking Tiến độ - Tổng kết gốc | Làm bài cho các nhánh con lẻ tẻ | 1. Làm được 2 nhánh con (VD: nhánh 1 đạt 100%, nhánh 2 đạt 50%). | Nhánh cha gốc (Toàn bộ bài) tự động cập nhật trung bình cộng tỷ lệ hoàn thành của các nhánh con. |
