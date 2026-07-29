# Data pack — VLearn

## Có sẵn trong pack

- `chatlog/chat_history_anonymized_for_hackathon.csv` — **2.522 dòng hội thoại thật** học viên × AI tutor, đã ẩn danh toàn bộ ID (user/conversation/turn/message → mã U/C/T/M) và đã quét sạch thông tin nhạy cảm.
- `chatlog/DATA_DICTIONARY.md` — mô tả từng field của file trên (đọc trước khi mining).

## Sẽ bổ sung trước sự kiện

- `transcript/` — transcript bài giảng (kèm timestamp) · `slides/` — slide bài giảng · `hoc-lieu/` — tài liệu đọc.

## Luật dùng

- Dùng để mining evidence, dựng golden set, và làm context cho prototype.
- Không đổ nguyên file lên repo public của nhóm — trích ngắn để minh hoạ được.
- Không cố suy ngược danh tính từ mã ẩn danh.
