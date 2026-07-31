# Bài thu hoạch cá nhân (Reflection)

- **Họ và tên:** Lê Thị Trúc Linh
- **Mã Học Viên:** 2A202601322
- **Vai trò trong dự án:** User Testing, Xây dựng Golden Set

## 1. Những đóng góp của tôi trong dự án
- Thu thập dữ liệu thực tế từ sinh viên (qua Discord chatlog, Google Form) để chứng minh tính cấp thiết của bài toán.
- Xây dựng bộ `golden_set.md` với các kịch bản test (Test cases) bám sát các edge cases thực tế (ví dụ: slide toàn hình ảnh, slide bị lỗi font).
- Chịu trách nhiệm chính trong việc chạy thử (User Testing): Trực tiếp phát hiện ra các lỗi chí mạng như lỗi không cuộn được trang PDF số 1, lỗi kéo thả Mindmap, và lỗi sinh Quiz bị lẫn lộn dữ liệu giữa các bài giảng khác nhau.
- Viết báo cáo Validation và tổng hợp phản hồi vào file `user_feedback_log.md`.

## 2. Bài học lớn nhất tôi rút ra được từ góc độ Xây dựng sản phẩm AI (AI Product)
- **Edge cases trong AI rất khó đoán:** Người dùng có những hành vi không lường trước được (ví dụ nhảy liên tục giữa các bài giảng PDF rồi mới bấm tạo Quiz), làm lộ ra các lỗ hổng về logic lưu trữ trạng thái của hệ thống.
- **Chất lượng đánh giá (Evaluation) định hình sản phẩm:** Một bộ Golden Set tốt giúp cả team yên tâm khi sửa Prompt mà không sợ làm hỏng các tính năng cũ (Regression).

## 3. Khó khăn lớn nhất gặp phải và cách giải quyết
- Việc định lượng độ "chính xác" của Mindmap và Flashcard do AI sinh ra rất cảm tính.
- **Cách giải quyết:** Tôi đã phải định nghĩa lại các tiêu chí đánh giá thật rõ ràng (ví dụ: Không được sai kiến thức lõi, số trang tham chiếu phải đúng, phương án gây nhiễu phải hợp lý).

## 4. Nếu có thêm thời gian, tôi sẽ làm gì khác đi?
- Tôi sẽ tự động hóa bộ Golden Set bằng code Python (Evaluation Framework) thay vì phải chạy test tay và chấm điểm thủ công từng trường hợp.
