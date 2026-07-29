# Mini Hackathon AI — Batch 03 · SPEC → Prototype → Demo

> Không phải cuộc thi code. Là cuộc thi **tư duy sản phẩm AI**.
> 1,5 ngày · nhóm 4-5 người · zone tối đa 5 nhóm · thi theo lớp.

## Bộ tài liệu — đọc theo thứ tự

| # | File | Là gì | Dùng khi nào |
|---|---|---|---|
| 1 | `01-de-bai.md` | Đề bài 3 hướng + 5 tiêu chí nghiệm thu + ràng buộc | Ngay khi phát đề |
| 2 | `02-guide.md` | Hướng dẫn xuyên suốt 5 giai đoạn (khám phá → spec → build → đo & validate → demo) | Suốt sự kiện — đứng ở giai đoạn nào đọc mục đó |
| 3 | `03-template-ai-spec.md` | Template AI Spec — deliverable trung tâm | Từ CP1, chốt 23:59 N1 |
| 4 | `04-rubric.md` | Rubric chấm bài + checklist xác minh từng mốc | Đọc NGAY từ đầu — biết trước mình được chấm bằng gì |
| — | `data/` | Data thật đã ẩn danh (chatlog VLearn tutor...) | Mining evidence + golden set |
| — | `tham-khao/` | JTBD Playbook (PDF) + worksheet JTBD đầy đủ | Khi muốn đào sâu |

## Sáu mốc (chi tiết từng mốc: `04-rubric.md`)

| Mốc | Khoá 3 | Khoá 4 |
|---|---|---|
| Khai mạc + phát đề | 09:00 N1 | 14:00 N1 |
| CP1 · Chốt Canvas | 10:00 N1 | 15:00 N1 |
| CP2 · Show được thứ bấm được | 12:00 N1 | 17:00 N1 |
| CP3 · AI chạy thật + đo lượt đầu | 16:00 N1 | 10:30 N2 |
| CP4 · Chốt tiến độ (spec — hạn cứng 23:59 N1) | 17:30 N1 | 12:00 N2 |
| CP5 · Xác minh + validation + dry run | 09:00 N2 | 14:00 N2 |
| CP6 · Demo | 10:00 N2 | 15:00 N2 |

## Nộp bài — 1 repo nhóm, spec chốt 23:59 N1, bản cuối trước CP6

```
repo/
├── README.md          ← thành viên (mã HV + tên) + phân công có tên từng phần
├── spec.md            ← AI Spec theo 03-template-ai-spec.md
├── demo-slides.pdf    ← slide 6 trang theo 02-guide.md §5.1
├── codebase/          ← prototype (ghi rõ phần nào mock)
├── eval/              ← golden set + bảng kết quả các lượt chạy
├── validation/        ← feedback log từ vòng user test
└── reflection/        ← mỗi người 1 file
```

## Chấm điểm — minh bạch từ đầu

Bài nộp được chấm bằng **rubric baseline 100 điểm** (chi tiết từng ý điểm: `04-rubric.md`) — chấm sau sự kiện, trên artifact trong repo, mỗi con điểm trỏ về một file cụ thể, **phúc khảo được**:

| Khối | Điểm | Chấm từ |
|---|---|---|
| R1 · Bằng chứng & impact (evidence chuẩn A/B có log, bảng impact ≥3 ứng viên) | 20 | spec §1-§2 + log |
| R2 · Lát cắt & thiết kế (1 câu chuẩn, non-goals, automation theo cost-of-error, ≥4 nguyên tắc HAX/PAIR có trỏ chỗ áp) | 20 | spec §4 |
| R3 · Chỗ khó & kịch bản (4 lớp taxonomy, ≥8 kịch bản, 4 đường đi trải nghiệm) | 15 | spec §5-§6 |
| R4 · Kiểm thử (golden set ≥10 tự làm, định nghĩa đo được, bar khoá trước, kết quả trung thực) | 20 | spec §7 + eval/ |
| R5 · Prototype (end-to-end, ≥1 AI call thật, mock khai rõ) | 10 | codebase/ + demo |
| R6 · Validation (≥5 feedback có tên + thay đổi từ feedback) | 10 | validation/ + changelog |
| R7 · Quy trình & repo | 5 | repo |

Reflection cá nhân chấm riêng theo rubric của khoá. Điểm vòng demo, chấm chéo trong zone và thưởng thêm (nếu có) thuộc thể lệ sự kiện công bố lúc khai mạc — không thuộc rubric baseline này.

**Nguyên tắc chấm quan trọng nhất:** chấm *chuỗi quyết định có bằng chứng*, không chấm độ hoành tráng. **Kết quả đo trung thực — kể cả không đạt bar tự đặt — ăn trọn điểm; che giấu hoặc sửa số liệu mất hết.**

## Luật xuyên suốt

- **Prototype 3 mức Sketch / Mock / Working — mức nào cũng bắt buộc ≥1 lời gọi AI chạy thật.**
- Vibe-coding rule: không giải thích được phần có tên mình = 0 điểm phần đó (kiểm tại CP5).
- Quality bar khoá tại spec.md 23:59 N1 — không hạ bar sau đó.
- Chỉ dùng data trong `data/` hoặc data giả tự sinh; không data thật của người thật; không commit API key; không đổ nguyên data pack lên repo public (trích ngắn minh hoạ được).
