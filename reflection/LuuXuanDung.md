# Bài thu hoạch cá nhân (Reflection)

- **Họ và tên:** Lưu Xuân Dũng
- **Mã Học Viên:** 2A202601774
- **Vai trò trong dự án:** Viết AI Spec, Prompt Engineering

## 1. Những đóng góp của tôi trong dự án
- Hoàn thiện tài liệu AI Spec, xác định rõ chân dung người dùng (sinh viên) và bài toán cần giải quyết (khó nắm bắt cấu trúc bài giảng dài).
- Trực tiếp tinh chỉnh Prompt cho Agent: Ép LLM trả về đúng định dạng JSON cho Mindmap và Flashcard.
- Cải tiến Prompt để AI nhận diện chính xác "Nguồn Slide" (ví dụ: ép buộc AI trả về khoảng trang "10-15" thay vì chỉ trang 10 nếu ý tưởng trải dài).
- Tối ưu hóa logic sinh Quiz: Gỡ bỏ các quy tắc quá khắt khe khiến AI từ chối tạo câu hỏi, đảm bảo tính năng Quiz luôn hoạt động mượt mà khi người dùng có thẻ yếu.

## 2. Bài học lớn nhất tôi rút ra được từ góc độ Xây dựng sản phẩm AI (AI Product)
- **Prompt Engineering không chỉ là ra lệnh:** Mà là việc lường trước các trường hợp "ảo giác" (hallucination) của AI. Việc yêu cầu AI trích xuất chính xác nguồn slide giúp tăng độ tin cậy của sản phẩm lên rất nhiều.
- **Giữ cân bằng giữa sự chặt chẽ và trải nghiệm người dùng:** Ban đầu tôi set luật quá khắt khe khiến AI hay báo lỗi từ chối tạo Quiz. Tôi nhận ra trong thực tế, đôi khi cần nới lỏng một chút để đảm bảo người dùng luôn nhận được kết quả thay vì một thông báo lỗi khó hiểu.

## 3. Khó khăn lớn nhất gặp phải và cách giải quyết
- Khó khăn lớn nhất là LLM thường xuyên "lười" hoặc sinh ra số trang sai (hallucinate).
- **Cách giải quyết:** Áp dụng kỹ thuật Prompt chặt chẽ, thêm các ví dụ (Few-shot) và dùng câu lệnh "BẮT BUỘC" (ví dụ: "BẮT BUỘC ghi TỪ trang bắt đầu ĐẾN trang kết thúc").

## 4. Nếu có thêm thời gian, tôi sẽ làm gì khác đi?
- Tôi sẽ thử nghiệm thêm các kỹ thuật RAG (Retrieval-Augmented Generation) tiên tiến hơn để trích xuất nội dung từ các file PDF phức tạp có chứa nhiều biểu đồ và hình ảnh, thay vì chỉ đọc text thuần túy.
