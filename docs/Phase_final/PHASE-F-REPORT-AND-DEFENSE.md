# PHASE F — BÁO CÁO, CHUẨN BỊ BẢO VỆ VÀ BÀN GIAO

## 1. MỤC TIÊU PHASE

Biến project đã kiểm thử thành bộ sản phẩm có thể cài đặt, chạy, trình bày, học và bàn giao: README đúng code, báo cáo đồ án, PowerPoint, sơ đồ, hình và số liệu truy nguyên, kịch bản demo, câu hỏi vấn đáp và tài liệu học toàn đề tài cho cả 5 thành viên.

Hoàn vẫn là người duy nhất triển khai. Không phân công thành viên viết code/tài liệu hoặc chờ bàn giao; việc học của từng thành viên được đánh giá riêng, không tự nhận họ đã hiểu khi chưa có kiểm chứng.

Đây là kế hoạch tương lai, không phải báo cáo project đã hoàn tất 100%. Chỉ công bố hoàn tất khi yêu cầu có bằng chứng nghiệm thu A–E và bộ bàn giao F thực sự sẵn sàng.

## 2. SƠ ĐỒ QUY TRÌNH THỰC HIỆN

```text
Đọc code và báo cáo thực tế A–E + kiểm tra freeze/artifact
→ Lập bảng bằng chứng và rà tài liệu sai lệch
→ Đồng bộ README/docs hướng dẫn
→ Viết báo cáo đồ án + sơ đồ + bảng thông số
→ Chọn hình/bảng/biểu đồ đúng run ID
→ Tạo PowerPoint và ghi chú thuyết trình
→ Kịch bản demo + Q&A + tài liệu học toàn bộ cho 5 người
→ Kiểm tra cài/chạy từ bản bàn giao riêng
→ Final Review/toàn vẹn → Bàn giao → DỪNG
```

## 3. ĐẦU RA BẮT BUỘC

- README và các tài liệu hướng dẫn hiện hành trong `docs/` thống nhất với code; báo cáo lịch sử được giữ và ghi chú trạng thái thay vì sửa số cũ.
- `docs/REPORT/FINAL-PROJECT-REPORT.md`: báo cáo đồ án có lý thuyết, kiến trúc, cài đặt, thực nghiệm và giới hạn.
- `docs/REPORT/HSV-COLOR-SEGMENTATION-DEFENSE.pptx`: PowerPoint mở được, khoảng 12–15 slide chính, ghi chú trình bày và phụ lục khi cần.
- `docs/REPORT/DEFENSE-SLIDE-OUTLINE.md`: nội dung slide/notes theo thứ tự, làm nguồn đối chiếu với PPTX.
- `docs/REPORT/DEMO-AND-HANDOVER.md`: cài đặt, chạy, demo, lỗi thường gặp, kiểm tra bản bàn giao.
- `docs/REPORT/TEAM-LEARNING-AND-VIVA.md`: tài liệu toàn đề tài, ma trận học của 5 người và ít nhất 30 câu hỏi/trả lời có chỉ nguồn code/bằng chứng.
- `docs/REPORT/PHASE-F-FINALIZATION-REPORT.md`, artifact chọn lọc mới trong `report/figures/final/`, gói bàn giao phiên bản mới và checksum trong `results/phase_f/<run_id>/`.

Các file này chỉ tạo khi triển khai F; nhiệm vụ hiện tại chỉ tạo tài liệu roadmap này. Không mặc định PowerPoint hoặc bộ bàn giao đã tồn tại.

## 4. NGUYÊN TẮC TRIỂN KHAI

```text
Implementation Owner: Hoàn
Tool Support: Cursor Agent
Excel: Academic Learning Reference
Team Dependency: NONE
```

Hoàn chuẩn bị toàn bộ nội dung, Cursor hỗ trợ đối chiếu và tạo sản phẩm. Excel dùng để tham khảo kiến thức học tập, không phân công người triển khai và không sửa workbook.

### MASTER SCOPE LOCK

- Tuyệt đối không xóa file/thư mục; không đổi tên/di chuyển hoặc tái cấu trúc project. Không xóa code, hàm, class hoặc chức năng cũ.
- Không sửa Frontend/Backend/tests/thuật toán/dependency để làm báo cáo khớp; chỉ thay tài liệu và artifact đúng allowlist. Không ghi đè dữ liệu hoặc code ngoài phạm vi, giữ mọi thay đổi có sẵn.
- Không thay Dataset, Ground Truth, metadata/manifest/freeze hoặc Excel; D sở hữu thay đổi dữ liệu khi cần.
- Không sửa tài liệu kế hoạch các Phase khác và báo cáo nghiệm thu A–E. Không commit, push hoặc thay đổi Git history khi chưa được yêu cầu.
- Trước sửa: Git Status, HEAD, danh sách file dự kiến thay đổi, danh mục và hash file hiện có kể cả untracked/ignored liên quan; đọc file đích trước cập nhật, bảo toàn phần có giá trị.
- Cần sửa ngoài scope hoặc thấy lỗi chức năng: DỪNG nhánh phụ thuộc, ghi evidence và Phase phụ trách; không tự mở scope hoặc sửa số liệu cho khớp.
- Final File Integrity Check: không file mất/rename/move; không sửa ngoài allowlist; code/tests/data/GT/Excel/freeze và HEAD nguyên hash; kiểm tra cả file untracked/ignored.
- Artifact/gói bàn giao lưu run ID mới, không ghi đè hình/kết quả cũ, không tự xóa thư mục tạm hoặc upload để “làm sạch”. Loại file khỏi danh sách đóng gói không đồng nghĩa xóa file gốc.

### HIỆN TRẠNG TÀI LIỆU PHẢI XỬ LÝ

| Tài liệu/thành phần | Điều đã thấy ngày 16/11/2026 | Cách xử lý trong F |
|---|---|---|
| README | Cây module ở root nhưng source ở `src/`; mô tả chủ yếu Red; ghi năm 2024, 10 ảnh | Cập nhật theo trạng thái đã nghiệm thu thật |
| README/data docs | Một số ví dụ H=180 và cấu hình cũ | Giải thích ảnh OpenCV H 0–179, cận 180 legacy; hướng dẫn cấu hình mới đúng |
| Hướng dẫn 10 phút | Viết trước A, còn mô tả chỉ Red và số liệu 27 ảnh | Giữ dấu mốc lịch sử, bổ sung ghi chú và bản hướng dẫn hiện hành đúng code |
| `report/hsv.md`, median/morphology | Có lý thuyết và kết quả theo cấu hình/giai đoạn khác nhau | Tái sử dụng kiến thức, không trộn raw HSV với mask cuối hoặc điểm cũ với final_test |
| Docs phân công cũ | Có bảng thành viên và công việc lịch sử | Giữ thông tin lịch sử, ghi mô hình hiện tại Hoàn triển khai; không tạo phụ thuộc |
| Báo cáo A | Có chức năng 15 màu nhưng preset verified=False | Phân biệt hỗ trợ chức năng 15 màu và màu đã kiểm chứng GT thật |

Không lấy tên file `FINAL_SUMMARY` hoặc checklist có dấu tích làm bằng chứng thay E. Đọc lại nội dung thực tế khi triển khai F.

## 5. ĐIỀU KIỆN BẮT ĐẦU

- Có báo cáo E với Integration/E2E, export và kết quả final_test thực tế; không còn blocker chức năng bắt buộc.
- D có nguồn/giấy phép, GT độc lập, split và freeze; kết quả E trỏ đúng freeze và config.
- Đọc source cuối cùng, README, `module_contracts.md`, hướng dẫn Web/quickstart, các báo cáo module và A–E. Xác minh đường dẫn/hàm/default/range, không dựa bản mô tả cũ.
- Có công cụ tạo và mở PPTX (PowerPoint/LibreOffice hoặc thư viện có sẵn). Nếu thiếu công cụ xuất, chuẩn bị nội dung hoàn chỉnh và thực hiện đường xuất khả thi; không gọi outline Markdown là PPTX đã xong.

## 6. PHẠM VI CHỈ LÀM VÀ KHÔNG ĐƯỢC LÀM

**CHỈ LÀM:** tài liệu, báo cáo, sơ đồ/hình minh họa từ bằng chứng, slide, demo, học/vấn đáp, hướng dẫn và kiểm tra gói bàn giao trong bản sao riêng.

**KHÔNG ĐƯỢC LÀM:** sửa code/test/dependency, điều chỉnh preset, chạy tuning mới hoặc đổi số liệu/GT/split, làm lại nghiệm thu E, AI, triển khai cloud/public, commit/push hoặc phân công người khác triển khai.

Allowlist tài liệu hiện có có thể cập nhật sau audit: `README.md`, `README_module.md`, `module_contracts.md` (chỉ mô tả đúng hợp đồng, không đổi hợp đồng), `docs/QUICKSTART.md`, `docs/HUONG_DAN_SU_DUNG_WEB.md`, `docs/PROJECT_SUMMARY.md`, `docs/FINAL_SUMMARY.md`, `docs/DELIVERY_CHECKLIST.md`, `docs/MEMBER_ASSIGNMENT.md`, `docs/REPORT/10-MINUTE-PROJECT-GUIDE.md`. Với tài liệu lịch sử chỉ bổ sung ghi chú phiên bản/đường dẫn nguồn mới, không thay kết quả thực nghiệm cũ. File mới theo mục 3, `report/figures/final/` và artifact mới `results/phase_f/<run_id>/`. Các báo cáo `PHASE-A/B/C/D/E-*` và thư mục `docs/Phase_final/` chỉ đọc khi thực hiện F.

## 7. CÁC TASK TRIỂN KHAI

### TASK F.1 — ĐỐI CHIẾU CODE, YÊU CẦU VÀ BẰNG CHỨNG

**Mục tiêu:** biết mọi tuyên bố trong tài liệu được chứng minh ở đâu.

**File/module:** toàn bộ code/modules, báo cáo A–E, freeze/config và metrics E chỉ đọc; báo cáo F.

**Cách thực hiện:** lập bảng yêu cầu đề bài → hàm/API/UI → test ID → ảnh/bảng số liệu/run ID. Ghi số ảnh/cặp approved theo loại/split/màu, phiên bản chương trình và môi trường. Mỗi kết quả dùng stage/config/hash cụ thể; phân biệt kết quả tổng hợp lịch sử, tuning D, final_test E và fixture chức năng. Liệt kê mâu thuẫn tài liệu và nguồn chuẩn thay thế, đánh dấu chưa kiểm chứng, không tự tuyên bố 100% nếu thiếu.

**Input:** source cuối và artifact có thật. **Output:** bảng chứng cứ và danh sách tài liệu cần đồng bộ.

**DONE checklist:**

- [ ] 100% yêu cầu bắt buộc có bằng chứng hoặc blocker rõ.
- [ ] Không có số liệu không truy được run/config/stage/dataset.
- [ ] Git Status/allowlist/hash baseline đã ghi.

### TASK F.2 — ĐỒNG BỘ README VÀ HƯỚNG DẪN

**Mục tiêu:** người mới cài và sử dụng theo tài liệu hiện hành được ngay.

**File/module:** tài liệu hiện có trong allowlist, `DEMO-AND-HANDOVER.md`.

**Cách thực hiện:** sửa cây thư mục/import/lệnh cho đúng `src/`; ghi Python và dependencies đã xác minh, cách tạo venv/cài requirements/chạy server cục bộ, URL/port thực tế và cách đổi cấu hình nếu có. Lệnh PowerShell dùng đường dẫn có khoảng trắng được quote và call operator phù hợp. Nêu chính xác upload formats/size/pixel limit/session TTL theo code E, mọi đường đi controls A–C, compare/GT/export, cách chạy kiểm thử an toàn và nơi xem artifact. Cảnh báo rõ script generator/ExperimentRunner main/script thực nghiệm cũ có ghi dữ liệu; không hướng dẫn sinh lại `data/` như thao tác cài đặt bình thường. Hướng dẫn không tự xóa upload/dataset, quản lý dung lượng bằng báo cáo và quyết định của Hoàn.

Các docs có bảng phân công lịch sử giữ thông tin nguồn, thêm tuyên bố mô hình hiện tại Hoàn là implementation owner; bốn người còn lại học toàn bộ nội dung, không chờ bàn giao. Không dùng checkbox cũ để khẳng định nghiệm thu mới.

**Input:** code/config E thực tế. **Output:** tài liệu hiện hành nhất quán và link nội bộ còn dùng được.

**DONE checklist:**

- [ ] Lệnh chạy đúng môi trường đã kiểm chứng, đường dẫn/file/API tồn tại.
- [ ] Chức năng mới được mô tả đúng; giới hạn và ca thiếu GT rõ.
- [ ] Tài liệu cũ có ngữ cảnh phiên bản, không xóa lịch sử có giá trị.

### TASK F.3 — BÁO CÁO ĐỒ ÁN VÀ SƠ ĐỒ

**Mục tiêu:** giải thích vấn đề, thiết kế và thuật toán gắn với code thật.

**File/module:** `FINAL-PROJECT-REPORT.md`, hình mới trong `report/figures/final/`; module/báo cáo lý thuyết hiện có chỉ đọc.

**Cách thực hiện:** viết cấu trúc: bài toán và phạm vi; yêu cầu; nền tảng HSV/Median/Morphology/Evaluation; kiến trúc; thiết kế dữ liệu/API; thực hiện; thực nghiệm; ưu/nhược; kết luận; cài đặt; tài liệu tham khảo. Dùng Mermaid hoặc công cụ sẵn có tạo sơ đồ tổng thể Browser HTML/JS ↔ Flask ↔ module xử lý ↔ session/upload/export, và sơ đồ Input → Processing → Output. Sơ đồ chỉ có thành phần thật, không thêm DB/auth/AI. Có sequence mô tả upload/process/evaluate/export nếu giúp giải thích.

Giải thích BGR khác RGB, OpenCV H 0–179, S/V 0–255, Red OR hai Hue và AND S/V, White/Black/Gray full Hue; preset là khởi điểm chứ không nhận diện vật thể. Median dùng trung vị, không trung bình; mất chi tiết khi kernel lớn. Erosion co, Dilation nở, Open co→nở, Close nở→co, thứ tự và iterations theo code. Chỉ số ghi công thức PA=(TP+TN)/N, IoU=TP/(TP+FP+FN), Precision=TP/(TP+FP), Recall=TP/(TP+FN), F1=2PR/(P+R), quy ước chia 0 theo evaluator; giải thích nền nhiều làm PA cao dù bỏ sót. Visualization dùng màu hiển thị đã kiểm chứng, ghi chú BGR/RGB để không đảo FP/FN khi chèn hình.

**Input:** yêu cầu, source và lý thuyết đã đối chiếu. **Output:** báo cáo có hai sơ đồ bắt buộc và giải thích đầy đủ.

**DONE checklist:**

- [ ] Mọi khối kiến trúc/hàm quan trọng có đường dẫn thực tế.
- [ ] Công thức, thứ tự pipeline và ý nghĩa thuật toán chính xác.
- [ ] Có nguồn trích dẫn thật; không tạo citation/DOI hoặc số liệu giả.

### TASK F.4 — BẢNG THÔNG SỐ VÀ HƯỚNG DẪN SỬ DỤNG

**Mục tiêu:** cả người dùng và người bảo vệ hiểu từng control đang có.

**File/module:** báo cáo đồ án, hướng dẫn demo và tài liệu học; đọc Frontend/main/modules chỉ đọc.

**Cách thực hiện:** lập bảng cho color_id/preset, mode, toàn bộ Hue ranges, S/V min/max, median kernel, morph size/shape, từng operation/iterations/thứ tự, stage so sánh, số configurations, GT và export. Mỗi hàng có tên UI, key payload, ý nghĩa, miền hợp lệ, default thực tế, nguồn file/hàm, tác động tăng/giảm, ví dụ. Tách default preset, module và UI nếu khác nhau, không tự đặt lại. Giải thích kernel=1 morphology có thể đồng nhất, median có miền riêng, legacy H=180 là cận tương thích chứ pixel Hue không đạt 180.

Viết từng bước mở project → venv → server → upload → palette → chỉnh/reset → median/morph → chạy → tạo configs/compare → GT đúng ảnh/màu → bảng/biểu đồ → export/mở file → chạy lại JSON. Dùng một ví dụ thành công và một thất bại từ artifact E, nêu số đo thật, không dựng ví dụ thành kết quả thực nghiệm.

**Input:** controls/contracts cuối. **Output:** bảng tham số đầy đủ và walkthrough.

**DONE checklist:**

- [ ] 100% controls/params người dùng đang gặp được giải thích.
- [ ] Default/range đối chiếu source; mọi khác biệt legacy ghi rõ.
- [ ] Người mới đi theo hướng dẫn tới export mà không phải đoán bước.

### TASK F.5 — HÌNH, BẢNG, BIỂU ĐỒ VÀ PHÂN TÍCH KẾT QUẢ

**Mục tiêu:** trình bày kết quả có thể truy nguyên và có phân tích lỗi.

**File/module:** metrics/config E, nguồn D chỉ đọc; báo cáo, hình `report/figures/final/` mới.

**Cách thực hiện:** chọn ít nhất sáu bộ ảnh minh họa có nguồn rõ: ảnh gốc, GT, raw, median, morphology, so sánh HSV và visualization; phải có ca thành công và ca khó nền gần màu/thiếu sáng/cháy sáng nếu bộ dữ liệu có. Không bắt buộc sáu ảnh khác nhau cho mỗi loại, nhưng ghi sample ID/stage/config/run ID. Chỉ thu nhỏ để trình bày, metrics tính ở độ phân giải gốc. Tạo bảng baseline so selected config, năm metrics theo màu/tổng macro, số mẫu và độ phân tán, tách synthetic/tuning/final_test. Biểu đồ dùng đúng CSV/JSON E, có trục, đơn vị, legend và phạm vi; không tự chạy tuning/đo lại trong F.

Phân tích FP/FN, tác dụng tăng/giảm HSV, mất viền sau median/morphology, ánh sáng/nền trùng màu, giới hạn GT một người, bộ nhỏ và màu chưa có GT. Không khẳng định morphology luôn cải thiện hoặc một config tốt cho mọi ảnh. Attribution giấy phép ảnh giữ theo registry D; nếu không cho phép phân phối thì không đóng gói ảnh và ghi giới hạn, không xóa file gốc.

**Input:** artifact E và provenance D. **Output:** bộ hình/bảng/biểu đồ và đoạn phân tích có nguồn.

**DONE checklist:**

- [ ] ≥6 bộ minh họa, có cả ca tốt và ca lỗi.
- [ ] Bảng/biểu đồ khớp số gốc ≤1e-9 trước làm tròn; đơn vị rõ.
- [ ] Mọi hình có sample/config/stage/run/source, không trộn các tập.

### TASK F.6 — TẠO POWERPOINT BẢO VỆ

**Mục tiêu:** có file slide thật, dễ trình bày trong khoảng 10 phút.

**File/module:** `DEFENSE-SLIDE-OUTLINE.md`, `HSV-COLOR-SEGMENTATION-DEFENSE.pptx`, hình final.

**Cách thực hiện:** thiết kế 12–15 slide chính: đề tài/bài toán; mục tiêu; Input/Output; kiến trúc; HSV/preset; Median; Morphology; dữ liệu/GT độc lập; UI/so sánh; metrics; kết quả/baseline; lỗi/hạn chế; demo; kết luận/hướng phát triển. Điều chỉnh gộp slide cho thời gian, có notes và phút dự kiến, tổng 8–10 phút chưa tính hỏi đáp. Phụ lục bảng thông số và câu hỏi kỹ thuật khi cần. Font tiếng Việt dễ đọc, hình có caption và nguồn, số liệu khớp E, không nhồi code dài.

Dùng PowerPoint/LibreOffice hoặc công cụ xuất PPTX có sẵn; không sửa requirements ứng dụng để thêm thư viện trình chiếu. Nếu phải cài công cụ ngoài phạm vi, hoàn thiện outline/hình/notes trước và báo bước xuất cụ thể; F chưa DONE cho tới khi có PPTX thật. Mở file kiểm tra font, dấu tiếng Việt, hình, biểu đồ, notes và slide bị tràn; xem thử slideshow, không chỉ kiểm tra file ZIP tồn tại.

**Input:** báo cáo/hình/bảng đã khóa. **Output:** PPTX và outline/notes khớp nhau.

**DONE checklist:**

- [ ] Có PPTX mở được và 12–15 slide chính, notes/time rõ.
- [ ] Kiến trúc, dữ liệu, thuật toán, metrics, kết quả và hạn chế đều xuất hiện.
- [ ] Đã kiểm tra bằng công cụ trình chiếu, không coi outline là sản phẩm thay thế.

### TASK F.7 — DEMO HOÀN CHỈNH VÀ PHƯƠNG ÁN DỰ PHÒNG

**Mục tiêu:** trình diễn có thể lặp lại, giải thích được kết quả và lỗi.

**File/module:** `DEMO-AND-HANDOVER.md`, gói config/artifact E chỉ đọc, slide.

**Cách thực hiện:** viết demo 5–7 phút: chạy server → ảnh/màu cụ thể → preset rồi chỉnh một tham số → so 3 cấu hình cùng pipeline → xem trước/sau median/morph → upload GT → đọc PA và IoU → export → mở CSV/JSON/PNG. Mỗi bước có thao tác, file/sample ID, config/stage, kết quả mong đợi dựa trên E, lời giải thích và thời gian. Chèn một ca thất bại có kiểm soát để trình bày giới hạn. Chuẩn bị bộ ảnh/GT/config có quyền sử dụng và bản kết quả đã đo sẵn; dự phòng offline bằng ảnh/slide/artifact, không giả là live demo khi dùng bản dự phòng.

Diễn tập một lượt trên bản bàn giao riêng; đây là rehearsal/cài đặt, không tạo lại chiến dịch test E hay chọn ngưỡng theo điểm test. Ghi thời gian thật, vấn đề và cách điều chỉnh nội dung trình bày; lỗi chức năng phải báo E, không tự sửa code ở F.

**Input:** chương trình E đã đạt và artifact minh chứng. **Output:** kịch bản live/offline, checklist trước buổi bảo vệ.

**DONE checklist:**

- [ ] Kịch bản có file/config/thao tác/kết quả rõ cho mọi bước.
- [ ] Có phương án mất mạng, port bận, session mất và thiếu thời gian.
- [ ] Một lượt rehearsal được ghi nhận trung thực, không bịa thời gian.

### TASK F.8 — BỘ HỌC TOÀN ĐỀ TÀI VÀ VẤN ĐÁP CHO 5 THÀNH VIÊN

**Mục tiêu:** mọi thành viên có cùng tài liệu để hiểu và giải thích toàn bộ hệ thống.

**File/module:** `TEAM-LEARNING-AND-VIVA.md`, hướng dẫn 10 phút và outline slide.

**Cách thực hiện:** viết ba mức học: bản 10 phút khái quát; lộ trình 60–90 phút đọc source theo main → HSV → Median → Morphology → Evaluation → DataLoader/ExperimentRunner → Frontend; bộ thực hành tự giải thích và thao tác. Lập ma trận năm người (Hoàn, Anh Quân, Mạnh Quân, Anh Tuấn, Quốc Anh) × tám chủ đề: bài toán/Input/Output; kiến trúc/API; HSV; Median; Morphology; GT/split/nguồn; metrics/so sánh; demo/export/hạn chế. Tất cả ô có cùng yêu cầu, không chia “mỗi người chỉ học module mình”. Trạng thái ban đầu CHƯA XÁC MINH, kèm bằng chứng/ngày tự kiểm tra; Hoàn chuẩn bị toàn bộ tài liệu, không giao người khác viết phần còn thiếu.

Chuẩn bị ≥30 câu hỏi, mỗi câu có đáp ngắn dễ nhớ, giải thích sâu hơn, đường dẫn hàm/artifact và lỗi trả lời cần tránh. Phủ tối thiểu: tại sao HSV; BGR/RGB; H 179/180; hai Hue Red; màu sv; median vs mean; kernel/shape/iterations; Open/Close/thứ tự; GT độc lập; nguồn/giấy phép; tuning/test leakage; PA/IoU/Precision/Recall/F1; mẫu số 0; ranking; công bằng so sánh; export; session; hiệu năng; ca lỗi/hạn chế; vì sao không gọi là AI nhận diện vật thể.

Rubric tự kiểm tra cho mỗi người: giải thích pipeline 3 phút không nhìn tài liệu; chỉnh và giải thích ≥5 thông số; tự đi luồng demo tới export; trả lời đúng ≥8/10 câu chọn từ toàn bộ nhóm chủ đề, không chỉ một module; phân tích một ca FP/FN từ E. Ghi kết quả chỉ khi họ thực sự thực hiện. Đầu ra chuẩn bị tài liệu không phụ thuộc bàn giao của ai; trạng thái “5 người đã sẵn sàng” chỉ PASS khi cả năm có evidence, nếu chưa thì ghi riêng chưa xác minh và lịch tự ôn, không tuyên bố thay họ.

**Input:** code và bằng chứng đã tổng hợp. **Output:** tài liệu học/Q&A/ma trận/rubric dùng chung.

**DONE checklist:**

- [ ] ≥30 Q&A có chỉ nguồn, đủ chủ đề toàn hệ thống.
- [ ] Cả 5 người có cùng lộ trình và tiêu chí, không nhiệm vụ viết code hay chờ bàn giao.
- [ ] Tách “bộ tài liệu sẵn sàng” với “mức hiểu của từng người đã xác minh”.

### TASK F.9 — ĐÓNG GÓI VÀ KIỂM TRA BÀN GIAO

**Mục tiêu:** người nhận có thể cài/chạy từ gói độc lập.

**File/module:** `DEMO-AND-HANDOVER.md`, checklist, gói mới trong `results/phase_f/<run_id>/`; source gốc chỉ đọc.

**Cách thực hiện:** lập danh sách include rõ: code/Frontend, requirements, hướng dẫn, test, dữ liệu approved được phép phân phối và manifest/license, freeze, cấu hình chọn và kết quả minh chứng, báo cáo/PPTX. Exclude khỏi gói `.venv`, `.git`, cache, session/upload riêng tư và output thừa; không xóa bản gốc. Tạo archive ID mới và file checksum SHA-256, listing và version/HEAD cùng ghi chú local modifications vì repo có thay đổi chưa commit. Không nói bản bàn giao tương đương commit thuần nếu chưa commit.

Giải nén sang vùng mới không trùng project, tạo venv riêng, cài đúng requirements có sẵn, chạy lệnh tài liệu và smoke upload/process/export trên vùng riêng; ghi hệ điều hành/interpreter, lệnh, kết quả, giới hạn offline. Đây là smoke cài đặt, tham chiếu kết quả hệ thống E thay vì chạy lại toàn suite. Không chép credentials/dữ liệu cá nhân; ghi đường dẫn tương đối và nguồn/attribution. Nếu cần sửa dependency/code để cài được, báo về E với evidence, không âm thầm chỉnh ở F.

**Input:** danh sách sản phẩm và giấy phép dữ liệu. **Output:** gói bàn giao, checksum/listing và biên bản smoke cài đặt.

**DONE checklist:**

- [ ] Archive/checksum có thật, không ghi đè gói cũ.
- [ ] Gói mở được và smoke theo hướng dẫn trên bản sao riêng có kết quả.
- [ ] Không include venv/private upload/secrets; nguồn ảnh và giới hạn giấy phép được giữ.

### TASK F.10 — BÁO CÁO, FINAL REVIEW VÀ FINAL FILE INTEGRITY CHECK

**Mục tiêu:** kết luận sản phẩm và mức sẵn sàng bảo vệ một cách trung thực.

**File/module:** `PHASE-F-FINALIZATION-REPORT.md`, toàn bộ allowlist và artifact F.

**Cách thực hiện:** kiểm bảng mục 9, link/hình/citation, số liệu, PPTX, demo, gói cài đặt và ma trận học. Báo trạng thái sản phẩm kỹ thuật và trạng thái học của 5 người riêng: tài liệu có thể hoàn tất trong khi mức học chưa được chứng minh; không gom thành “100% sẵn sàng bảo vệ”. Đối chiếu hash/danh mục/Git/HEAD trước sau, code/tests/data/GT/Excel/freeze phải nguyên; mọi tài liệu sửa có lý do. Ghi tồn đọng/giới hạn có tác động thật, không tự nhận chất lượng ngoài tập đã đo.

**Input:** sản phẩm F và bằng chứng A–E. **Output:** báo cáo bàn giao cuối với trạng thái đo lường được.

**DONE checklist:**

- [ ] Sản phẩm kỹ thuật đủ và sử dụng được; mọi claim có nguồn.
- [ ] Mức sẵn sàng 5 người không bị đánh dấu PASS khi chưa kiểm chứng.
- [ ] Final File Integrity Check đạt; không commit/push hoặc sửa code.

## 8. KẾ HOẠCH KIỂM THỬ TÀI LIỆU VÀ BÀN GIAO

| Mã | Kiểm tra | Kỳ vọng |
|---|---|---|
| F-T01 | Links/paths/imports/API/commands | 0 link nội bộ bắt buộc hỏng, tên hàm/route đúng code |
| F-T02 | Bảng thông số/default/range | 100% controls có nguồn, không tự đặt default |
| F-T03 | Bảng/biểu đồ/hình so CSV/JSON E | Khớp trước làm tròn ≤1e-9, đúng stage/split/config |
| F-T04 | Mở PPTX/slideshow | Không font lỗi, tràn slide, thiếu hình/notes |
| F-T05 | Rehearsal demo | Tới export bằng dữ liệu/config đã chỉ rõ; có dự phòng |
| F-T06 | Archive/hash/cài đặt bản sao | Checksum khớp, smoke thành công theo hướng dẫn |
| F-T07 | Rubric 5 người | Ghi thực tế từng người; chưa thực hiện = chưa xác minh |
| F-T08 | Final integrity | Code/tests/data/GT/Excel/freeze/HEAD nguyên, không mất file |

F kiểm tra tài liệu, trình chiếu, rehearsal và khả năng bàn giao; Unit/Integration/E2E và đánh giá chất lượng chính đã thuộc E. Không chạy lại thí nghiệm để chọn kết quả đẹp hơn trong F.

## 9. ACCEPTANCE CRITERIA

| Tiêu chí | Điều kiện đo lường |
|---|---|
| Đồng bộ docs | 100% tài liệu hiện hành trong allowlist đối chiếu, 0 hướng dẫn chức năng không tồn tại |
| Báo cáo | Có bài toán, hai sơ đồ bắt buộc, thuật toán, dữ liệu, thực nghiệm, hạn chế, cài đặt và tham khảo |
| Thông số | 100% controls/params quan trọng có nghĩa/range/default/tác động/ví dụ/nguồn |
| Bằng chứng | ≥6 bộ minh họa; năm metrics và biểu đồ có run/config/stage/split; không số giả |
| PowerPoint | PPTX thật mở được, 12–15 slide chính, notes và lịch 8–10 phút |
| Demo | Kịch bản 5–7 phút và một rehearsal; có đường live/offline tới export |
| Bộ học chung | ≥30 Q&A, lộ trình đọc source và rubric đủ 8 chủ đề cho cả 5 người |
| Sẵn sàng cá nhân | Chỉ PASS khi từng người đạt rubric F.8; thiếu evidence phải ghi CHƯA XÁC MINH |
| Bàn giao | Archive mới + SHA-256/listing + smoke cài/chạy trên bản sao riêng |
| Toàn vẹn | 0 code/test/data/GT/Excel/freeze thay đổi; 0 file mất/rename/move; HEAD không đổi |

Tách nghiệm thu **sản phẩm/tài liệu** và **khả năng giải thích của cả 5 người**. Không dùng Team Dependency để biến việc học thành phụ thuộc triển khai; Hoàn hoàn thành sản phẩm chủ động, còn khẳng định mức hiểu phải có kiểm chứng thực tế. Không tuyên bố toàn bộ mục tiêu bảo vệ hoàn tất khi còn ô chưa xác minh.

## 10. RỦI RO VÀ PHƯƠNG ÁN XỬ LÝ

- Tài liệu cũ sai trạng thái: đối chiếu code/E, thêm ngữ cảnh lịch sử và nguồn hiện hành, giữ kết quả cũ đúng phạm vi.
- Trộn raw với final hoặc tuning với test: mỗi hình/bảng phải có stage/split/config/run ID.
- Không có công cụ xuất PPTX: chuẩn bị outline/hình/notes trước, thực hiện xuất bằng công cụ khả dụng hoặc ghi blocker thao tác cụ thể; không giả đã có PowerPoint.
- Thành viên chỉ học module riêng: dùng ma trận chung và câu hỏi rút từ mọi chủ đề, tài liệu do Hoàn chuẩn bị toàn bộ.
- Thiếu chứng cứ mức hiểu: ghi chưa xác minh, không đoán hoặc đặt dấu tích thay người học.
- Lỗi demo/cài đặt: dùng bản sao và artifact dự phòng; bug chức năng chuyển E, không sửa code trong F.
- Giấy phép ảnh hạn chế: tuân theo source D, có attribution và danh sách exclude khi đóng gói; không xóa file gốc.

## 11. DEPENDENCIES VÀ SƠ ĐỒ TỔNG THỂ

```text
PHASE A — MULTI-COLOR HSV
              ↓
PHASE B — HSV COMPARISON
              ↓
PHASE C — MORPHOLOGY UI
              ↓
PHASE D — DATASET & GROUND TRUTH
              ↓
PHASE E — SYSTEM TESTING + FINAL EVALUATION
              ↓
PHASE F — REPORT & DEFENSE

D ──GT hợp lệ + split/freeze──→ kết luận học thuật B/E
B/C ──công cụ + pipeline──→ tuning D và đánh giá E
E ──artifact đã kiểm chứng──→ báo cáo/slide/demo F
```

B có thể xây giao diện với ảnh upload trước D; kết quả học thuật cuối không được bỏ dependency GT/split D. F không làm lại dữ liệu, export hoặc test hệ thống. Nếu phát hiện sai bằng chứng, ghi blocker đúng Phase, không che bằng cách chỉnh câu chữ/số liệu.

## 12. BÁO CÁO ĐẦU RA

`docs/REPORT/PHASE-F-FINALIZATION-REPORT.md`: danh sách sản phẩm/phiên bản; tài liệu đã đồng bộ; bảng truy nguyên yêu cầu; link báo cáo/PPTX/hình/Q&A/demo/gói bàn giao; kết quả kiểm tra F-T01–08; trạng thái sản phẩm và mức sẵn sàng từng người; giới hạn; file thay đổi và Final File Integrity Check. Không viết lại báo cáo E hoặc nhận số test E thành số test mới ở F.

## 13. FINAL REVIEW

- [ ] TASK F.1–F.10 có bằng chứng, không chỉ file khung.
- [ ] Báo cáo/slide/hướng dẫn khớp code và kết quả E.
- [ ] Bộ học đủ giúp cả 5 người giải thích toàn project; trạng thái cá nhân trung thực.
- [ ] Demo, gói bàn giao và cài/chạy có xác minh.
- [ ] Source/dữ liệu/Excel nguyên, không thay Git history.

## 14. STOP RULE

Sau bàn giao và báo cáo: **DỪNG**. Không commit/push, không tự publish/deploy hoặc chuyển Phase mới. Nếu còn blocker chức năng, thiếu PPTX hoặc thiếu kiểm chứng cá nhân, báo rõ phần hoàn thành và phần chưa xác minh; không tuyên bố “100% hoàn tất” thay cho bằng chứng. Hoàn quyết định bước tiếp theo.

## 15. TỔNG KẾT PHASE VÀ THỨ TỰ THỰC HIỆN

F.1 Bằng chứng → F.2 Docs → F.3 Báo cáo/sơ đồ → F.4 Thông số/hướng dẫn → F.5 Hình/số liệu/phân tích → F.6 PowerPoint → F.7 Demo → F.8 Học/vấn đáp → F.9 Bàn giao → F.10 Review/toàn vẹn → DỪNG. Sản phẩm cuối là chương trình có bằng chứng, tài liệu dễ học, slide thật và hướng dẫn bàn giao có thể sử dụng trực tiếp.
