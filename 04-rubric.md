# Rubric — chấm bài nộp (baseline) + checklist xác minh 6 mốc

> **Phạm vi & nguyên tắc:** rubric này chấm **bài nộp cuối** — chấm sau sự kiện, trên artifact trong repo, mỗi ý điểm trỏ về một file, phúc khảo được. Chấm *chuỗi quyết định có bằng chứng*, không chấm độ hoành tráng. Kết quả đo trung thực (kể cả không đạt bar) ăn trọn điểm mục tương ứng; che giấu hoặc sửa số liệu mất điểm. Điểm vòng demo, chấm chéo zone và thưởng thêm (nếu có) thuộc thể lệ sự kiện công bố lúc khai mạc — không thuộc file này.

## PHẦN 1 — RUBRIC BÀI NỘP: 100 điểm nhóm

### R1 · Bằng chứng & impact — 20 *(spec §1-§2 + log trong repo)*

| Điều kiện | Điểm |
|---|---|
| Evidence đạt chuẩn **A** (khảo sát ≥20 người ngoài nhóm, ≥50% xác nhận, log đủ câu hỏi + từng câu trả lời nguyên văn) và/hoặc **B** (số mining đếm được + ≥5 ví dụ nguyên văn + phương pháp đếm kiểm lại được) | 8 |
| Pain cụ thể: ai — đang làm gì — vướng đâu — hậu quả gì | 4 |
| Bảng impact ≥3 ứng viên có con số (bao nhiêu người × tần suất × tốn gì mỗi lần) | 4 |
| Ứng viên bị loại được giữ lại + lý do chọn bằng số | 4 |

### R2 · Lát cắt & thiết kế — 20 *(spec §4 + §4b)*

| Điều kiện | Điểm |
|---|---|
| Lát cắt đúng format MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả), khớp bản build | 4 |
| ≥3 non-goals, bản build không vi phạm | 3 |
| Automation chọn rõ + lý do theo cost-of-error | 5 |
| ≥4 nguyên tắc HAX/PAIR, **mỗi nguyên tắc trỏ được vào chỗ cụ thể trong prototype** | 8 |

### R3 · Chỗ khó & kịch bản — 15 *(spec §5-§6)*

| Điều kiện | Điểm |
|---|---|
| 4 lớp chỗ khó cụ thể hoá đúng taxonomy (①②③④), không chung chung | 6 |
| ≥8 kịch bản có hành vi mong muốn, phủ đủ 4 lớp | 5 |
| 4 đường đi trải nghiệm (happy / low-confidence / failure / correction) đủ trong spec và thể hiện trong prototype | 4 |

### R4 · Kiểm thử — 20 *(spec §7 + eval/)*

| Điều kiện | Điểm |
|---|---|
| Golden set ≥10 case nhóm tự làm: case thường + ≥2 case/lớp chỗ khó + case hiếm | 5 |
| Mỗi chiều chất lượng có định nghĩa kiểm chứng được (người ngoài nhóm chấm ra cùng kết quả) | 5 |
| Quality bar bằng con số, trong spec.md commit trước 23:59 N1, không bị hạ sau | 4 |
| Bảng kết quả chạy trọn bộ ≥1 lượt, đủ mọi case kể cả fail, có %, đối chiếu bar; không đạt bar → có phân tích vì sao | 6 |

### R5 · Prototype — 10 *(codebase/ + demo)*

| Điều kiện | Điểm |
|---|---|
| Chạy end-to-end theo lát cắt đã khai, không can thiệp tay giữa chừng | 4 |
| ≥1 lời gọi AI thật ở quyết định trung tâm (log/trace trong repo); phần mock ghi rõ | 4 |
| Mức prototype khai báo (Sketch/Mock/Working) khớp thực tế | 2 |

### R6 · Validation với user — 10 *(validation/ + spec §9)*

| Điều kiện | Điểm |
|---|---|
| Feedback log ≥5 mẩu từ ≥5 người ngoài nhóm (có ≥2 willing user đã khai từ CP1), quote nguyên văn + tên/vai | 5 |
| ≥1 thay đổi từ feedback ghi trong Changelog, hoặc giữ nguyên có lý do căn cứ | 5 |

### R7 · Quy trình & repo — 5

| Điều kiện | Điểm |
|---|---|
| Repo đủ cấu trúc chuẩn (xem README) | 2 |
| README phân công có tên người cho từng phần | 2 |
| Artifact các mốc nộp đủ, đúng hạn | 1 |

### Reflection cá nhân *(chấm riêng)*

Vai trò + phần mình làm + AI hỗ trợ thế nào + một bài học từ case fail của chính nhóm — theo rubric reflection của khoá. **Vibe-coding rule:** bị hỏi tại CP5/CP6 mà không giải thích được phần có tên mình → 0 điểm phần cá nhân liên quan.

## PHẦN 2 — CHECKLIST XÁC MINH 6 MỐC *(minh bạch: TA tích đúng những ô này, 2 phút/nhóm)*

Checkpoint để giữ nhịp và cứu nhóm kẹt; artifact mỗi mốc là đầu vào của rubric Phần 1.

| Mốc | K3 | K4 | Nhóm cần show | TA tích Có/Không |
|---|---|---|---|---|
| **CP1 · Canvas** | 10:00 N1 | 15:00 N1 | Canvas 7 dòng (guide §1.5): hướng · job executor · pain 1 câu · 1-2 bằng chứng đầu · lát cắt 1 câu · automation + willing users dự kiến · phân công | ☐ lát cắt đúng format 1 câu ☐ có evidence ban đầu ☐ đủ tên phân công |
| **CP2 · Bấm được** *(mốc cứu hộ — kẹt kỹ thuật thì đây là lúc gọi TA)* | 12:00 N1 | 17:00 N1 | Prototype Sketch/Mock: flow chính bấm đi hết được + commit đầu | ☐ flow chính bấm hết được ☐ repo có commit |
| **CP3 · AI thật + đo lượt đầu** | 16:00 N1 | 10:30 N2 | AI call thật ở quyết định trung tâm + golden set ≥10 + bảng kết quả lượt 1 có % | ☐ AI thật, không hardcode ☐ golden set đủ case khó ☐ bảng đủ mọi case (fail nhiều không sao — trung thực là đạt) |
| **CP4 · Chốt tiến độ** | 17:30 N1 | 12:00 N2 | Spec gần cuối + việc còn thiếu. **Hạn cứng: spec.md commit 23:59 N1, bar khoá từ đó** | ☐ evidence chuẩn A/B có log ☐ bảng impact + ứng viên loại ☐ 4 lớp cụ thể ☐ ≥4 nguyên tắc có chỗ áp ☐ bar bằng số |
| **CP5 · Xác minh + validation + dry run** | 09:00 N2 | 14:00 N2 | Feedback log ≥5 mẩu có tên + changelog + slide final + dry run xong | ☐ log đủ ≥5 có tên ☐ 1 thành viên ngẫu nhiên giải thích được phần có tên mình ☐ dry run xong |
| **CP6 · Demo** | 10:00 N2 | 15:00 N2 | 5' trình bày (slide 6 trang, có case lỗi live + % vs bar) + 5' Q&A: thẻ giám khảo chạy 1 case lạ tại chỗ; mỗi thành viên nói ≥1 phần | — (vòng demo theo thể lệ sự kiện) |
