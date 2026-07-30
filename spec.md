# AI SPEC — Tổng kết Mindmap & Flashcard · Nhóm [XX] · Zone [X]
Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ): Sinh viên đại học muốn ôn tập nhanh nội dung bài giảng sau khi đọc slide dài trên VLearn.
- Core JTBD (không tên sản phẩm/AI trong câu): "Giúp tôi nhanh chóng nắm bắt cấu trúc ý chính của bài giảng và tự kiểm tra lại kiến thức cốt lõi ngay tại chỗ, để tôi không bị quên kiến thức vừa học."
- Problem statement (KHÔNG chữ AI): Sinh viên phải đối mặt với các bộ slide PDF dài (hàng chục trang), chứa rất nhiều chữ khiến họ dễ nản, khó tổng hợp cấu trúc tổng thể và tốn thời gian lật lại để tìm ý chính khi ôn thi.
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - Số liệu mining / kết quả khảo sát (n = ?, % xác nhận): (Nhóm bổ sung số liệu khảo sát vào đây)
  - ≥5 quote/ví dụ nguyên văn + nguồn: (Nhóm bổ sung quote của sinh viên vào đây)

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên (bao nhiêu người · tần suất · tốn gì mỗi lần · khả thi):
  - Ứng viên 1: Chatbot QA giải đáp thắc mắc.
  - Ứng viên 2: Nút bấm Tóm tắt bài giảng bằng văn bản dài.
  - Ứng viên 3: Tự động sinh Mindmap và Flashcard trắc nghiệm.
- Ứng viên ĐÃ LOẠI + vì sao: Chatbot QA (Sinh viên lười gõ câu hỏi, thường không biết phải hỏi gì khi chưa hiểu bài). Tóm tắt văn bản (Vẫn là đọc một đoạn chữ dài, dễ gây nhàm chán).
- Ứng viên CHỌN + vì sao (bằng số): Mindmap & Flashcard (Ứng viên 3). Vì Mindmap giúp nhìn bao quát cấu trúc (Top-down), Flashcard trắc nghiệm giúp kiểm tra chi tiết (Bottom-up). Trực quan, bấm là học được ngay, tăng % tương tác lên cao.

## §3. Giải pháp tương tự đã nghiên cứu
- Quizlet: Tạo flashcard ôn tập rất tốt nhưng quy trình tạo thẻ phải nhập thủ công từng câu, mất thời gian.
- ChatGPT/Claude: Có thể tóm tắt tốt nhưng giao diện chat thuần túy không hỗ trợ Mindmap trực quan, phải prompt phức tạp.

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả): Sinh viên đang xem slide trên VLearn, bấm nút AI, hệ thống tự động đọc trang slide và xuất ra Cây Mindmap ý chính cùng Bộ Flashcard trắc nghiệm để ôn tập ngay lập tức.
- Non-goals (≥3 thứ KHÔNG build): KHÔNG tự động giải bài tập về nhà. KHÔNG thay thế hoàn toàn việc đọc sách giáo trình. KHÔNG sinh ra slide thuyết trình.
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [x] Working — Mock phần giao diện VLearn gốc, Working phần thao tác với giao diện AI Mindmap/Flashcard.
- Automation: [ ] augment [ ] conditional [x] automate — AI tự động tổng hợp toàn bộ bài giảng, sinh viên chỉ việc học (Cost-of-error thấp vì sinh viên vẫn có thể bấm nút "Xem Slide gốc" trên từng nhánh Mindmap để đối chiếu).
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | Make clear what the system can do | Nút bấm "Cây Đũa Thần" nổi bật ở mép phải màn hình báo hiệu tính năng AI sinh tổng kết. |
  | Make clear how well the system can do what it does | Hiển thị màn hình Loading với các dòng chữ "Đang phân tích 83 trang slide..." để báo hiệu tiến trình. |
  | Support efficient invocation | Chỉ cần 1 click để kích hoạt toàn bộ luồng, không bắt user gõ prompt. |
  | Support efficient dismissal | Nút "Trở về bài giảng" giúp người dùng thoát khỏi AI Dashboard nhanh chóng bất kỳ lúc nào. |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]
1. Thông tin không có trong tài liệu (Chống Hallucination): Đưa vào slide trống/kết luận -> AI không được tự bịa định nghĩa ngoài ngành vào.
2. Mơ hồ, thiếu ngữ cảnh: Đưa vào slide chỉ chứa tiêu đề -> AI phải báo lỗi không đủ thông tin tổng hợp.
3. Đòi thứ không được phép làm: Slide chứa đề thi/bài tập -> AI không được sinh Flashcard có đáp án trực tiếp làm lộ đề.
4. Trả lời sai gây hậu quả thật: Tổng hợp sai/ngược kiến thức lõi -> Flashcard có nút "Xem Slide gốc" để sinh viên tra cứu chéo nguồn minh bạch.

## §6. Bốn đường đi của trải nghiệm
- Happy path: Sinh viên bấm nút -> Chờ AI xử lý -> Nhận Mindmap + Flashcard -> Click Flashcard học trắc nghiệm -> Đánh dấu Đã thuộc/Chưa thuộc -> Xong.
- Low-confidence (②): AI không phân tách được nhánh chính phụ rõ ràng -> Gom chung vào một nhánh "Khái niệm khác".
- Failure/không căn cứ (①): Slide rỗng -> Báo lỗi "Không tìm thấy nội dung để tổng hợp".
- Correction (user sửa): (Không áp dụng, sinh viên chỉ tiêu thụ nội dung).
- Khi bị đòi ngoài phạm vi (③): Không áp dụng (luồng đóng).
- Case đặc thù domain (④): Slide chứa code hoặc bảng biểu -> Flashcard giữ nguyên cấu trúc code.

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được: Mindmap không bị trùng nhánh, Flashcard trắc nghiệm đưa ra phương án nhiễu hợp lý, không lấy sai định nghĩa.
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/): Đã chuẩn bị bộ 20 test cases, lấy nguồn từ Discord chatlog của sinh viên thắc mắc và slide thực tế.
- Quality bar (chốt từ 23:59, giữ nguyên sau đó): "Đạt khi ≥ 80% slide đầu vào sinh ra Mindmap/Flashcard đúng chuẩn, và KHÔNG MỘT LẦN NÀO AI bịa đặt sai kiến thức học thuật."
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6): Chưa có dữ liệu.

## §8. Phân công & kế hoạch
- Phân công có tên: spec (??) / evidence (??) / prompt (??) / code (??) / demo (??)
- Willing users (≥3 tên) + kế hoạch vòng validation CP5 (3 câu hỏi, ai log): Khảo sát 3 sinh viên đang học môn COMP2010.
- Multi-prototype (nếu làm): Không áp dụng.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 30/07/2026 | Khởi tạo file spec.md | Chuẩn bị nộp mốc CP4 trước 23:59 |
