# Bài thu hoạch cá nhân (Reflection)

- **Họ và tên:** Nguyễn Thị Huyền Trang
- **Mã Học Viên:** 2A20260160
- **Vai trò trong dự án:** Code Backend (Python), Tích hợp AI

## 1. Những đóng góp của tôi trong dự án
- Xây dựng server API bằng Flask để làm cầu nối giữa giao diện React và mô hình AI Gemini.
- Xử lý luồng đọc file PDF: Bỏ giới hạn cắt trang (limit), cho phép AI đọc toàn bộ text của file slide (thậm chí 80-100 trang) để lấy ngữ cảnh đầy đủ nhất.
- Tích hợp Tool Calling cho Agent: Đóng gói các hàm `generate_mindmap`, `generate_flashcards` để ép AI trả về dữ liệu chuẩn cấu trúc JSON.
- Xử lý logic chèn tự động `topic` (Tên nhánh) vào dữ liệu trả về của Flashcard để Frontend có dữ liệu hiển thị nhãn phân loại cho người dùng.

## 2. Bài học lớn nhất tôi rút ra được từ góc độ Xây dựng sản phẩm AI (AI Product)
- **Xử lý dữ liệu đầu vào là then chốt:** AI sẽ sinh ra kết quả rác (garbage in, garbage out) nếu text trích xuất từ PDF bị lỗi font hoặc bị cắt cụt. Việc mở rộng context window cho phép AI nhìn thấy toàn cảnh bài giảng là một quyết định đúng đắn.
- Việc bóc tách logic Backend và Frontend thông qua REST API giúp quá trình làm việc nhóm trơn tru hơn rất nhiều.

## 3. Khó khăn lớn nhất gặp phải và cách giải quyết
- Đảm bảo AI luôn gọi đúng Tool Call thay vì trả về text tự do (plain text), điều này làm sập toàn bộ logic phân tích JSON của hệ thống.
- **Cách giải quyết:** Thiết lập `system_instruction` cực kỳ khắt khe và dùng cơ chế bắt lỗi `try-except` trong Python để nếu AI trả về lỗi, hệ thống sẽ trả về message thân thiện cho Frontend thay vì crash Server.

## 4. Nếu có thêm thời gian, tôi sẽ làm gì khác đi?
- Tôi sẽ tối ưu tốc độ phản hồi của API bằng cách triển khai Streaming (trả dữ liệu về từng chữ một thay vì bắt người dùng đợi 20 giây mới hiện ra toàn bộ Mindmap).
