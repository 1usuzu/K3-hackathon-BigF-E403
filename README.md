# 🚀 V-Learn: Trợ lý ôn tập AI (Hackathon Batch 03)

## 👥 Danh sách thành viên & Phân công công việc
*(Vui lòng điền thông tin nhóm tại đây)*

| Mã Học Viên | Họ và Tên | Vai trò / Phân công công việc |
| :--- | :--- | :--- |
| [Mã HV 1] | [Tên thành viên 1] | [VD: Viết AI Spec, Prompt Engineering] |
| [Mã HV 2] | [Tên thành viên 2] | [VD: Code Frontend (React)] |
| [Mã HV 3] | [Tên thành viên 3] | [VD: Code Backend (Python), Tích hợp LLM] |
| [Mã HV 4] | [Tên thành viên 4] | [VD: User Testing, Xây dựng Golden Set] |
| [Mã HV 5] | [Tên thành viên 5] | [VD: Chuẩn bị Demo Slide, Viết Reflection] |

## 📁 Cấu trúc thư mục nộp bài
Dự án được tổ chức theo quy định của ban tổ chức:

- **`README.md`**: Thông tin nhóm và phân công (File này).
- **`spec.md`**: Bản đặc tả AI (AI Spec).
- **`demo-slides.pdf`**: Slide thuyết trình (Đang cập nhật).
- **`codebase/`**: Source code Prototype.
  - ⚠️ **Lưu ý quan trọng cho Ban giám khảo:** Prototype chạy thật của nhóm hiện đang được tách thành 2 thư mục chính:
    - Thư mục `frontend/`: Chứa giao diện React (Giao diện Mindmap & Flashcard).
    - Thư mục `src/`: Chứa Backend Python (Flask) xử lý logic gọi AI.
- **`eval/`**: Chứa tập `golden_set.md` và các test case đánh giá AI.
- **`validation/`**: Log phản hồi thực tế từ người dùng (User test feedback).
- **`reflection/`**: Chứa các file tự đánh giá rút kinh nghiệm của từng thành viên.

## 🛠 Hướng dẫn chạy Prototype
Prototype của nhóm là bản **Working (Chạy thật)** với LLM.
1. **Chạy Backend Python (API):**
   ```bash
   pip install -r requirements.txt
   python src/app.py
   ```
2. **Chạy Frontend React (Giao diện):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
