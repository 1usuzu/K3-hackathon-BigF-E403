---
name: generate_quiz
description: Sinh bài kiểm tra trắc nghiệm từ các thẻ Flashcard chưa hiểu (thẻ yếu). Yêu cầu có câu hỏi tình huống cho các khái niệm khó và bỏ qua các thẻ không mang tính học thuật.
---

# `generate_quiz`

Công cụ này dùng để sinh bài kiểm tra dựa trên danh sách các khái niệm/câu hỏi mà người dùng đánh dấu là chưa hiểu.

## Khi nào sử dụng:
- Khi người dùng muốn làm Quiz ôn tập, hoặc kích hoạt tính năng "Tạo Quiz từ thẻ yếu".

## Cấu trúc Argument:
- `questions`: Một mảng các object chứa:
  - `question_text`: Nội dung câu hỏi trắc nghiệm.
  - `options`: Mảng 4 chuỗi đáp án (có đáp án nhiễu).
  - `correct_answer`: Chuỗi đáp án đúng (phải khớp hoàn toàn với 1 option).
  - `explanation`: Giải thích ngắn gọn tại sao đáp án này đúng.
