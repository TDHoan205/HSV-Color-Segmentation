# PHASE B — SO SÁNH NHIỀU CẤU HÌNH NGƯỠNG HSV

## 1. MỤC TIÊU PHASE

Cho phép Hoàn tạo, chỉnh sửa, lưu và chạy lại nhiều cấu hình HSV trên cùng một ảnh; xem mask cạnh nhau, bảng và biểu đồ năm chỉ số khi có Ground Truth (GT) hợp lệ. Chỉ kết luận cấu hình tốt nhất trong phạm vi ảnh, màu mục tiêu, giai đoạn mask và dữ liệu đã xác minh.

Đây là tài liệu triển khai tương lai, không phải báo cáo chức năng đã hoàn thành. Mốc đối chiếu: 16/11/2026; phải audit lại khi bắt đầu.

## 2. SƠ ĐỒ QUY TRÌNH THỰC HIỆN

```text
Đọc code + Git Status + chụp mốc toàn vẹn
→ Xác minh hợp đồng Phase A
→ Chốt cấu hình và trạng thái so sánh
→ Backend so sánh trên ảnh bất biến
→ Giao diện quản lý cấu hình + mask cạnh nhau
→ GT hợp lệ → bảng + biểu đồ + xếp hạng
→ Lưu JSON + mask + chạy lại
→ Kiểm thử chức năng B → Báo cáo → Final Review → DỪNG
```

## 3. ĐẦU RA BẮT BUỘC

- Giao diện quản lý 2–6 cấu hình trong một lượt so sánh; tạo mới, nhân bản, đổi tên, chỉnh, bỏ khỏi danh sách làm việc, chọn cấu hình để chạy lại.
- Mask raw và mask cuối của mỗi cấu hình, thông số HSV đầy đủ, trạng thái xử lý và giai đoạn đang xem.
- Bảng và biểu đồ Pixel Accuracy, IoU, Precision, Recall, F1; không có GT thì hiện “Chưa có GT hợp lệ”, không giả lập chỉ số.
- Gói kết quả tải xuống gồm JSON có phiên bản schema, cấu hình đã áp dụng, nhận diện ảnh/GT và mask PNG; nhập cấu hình để tái lập.
- Kiểm thử riêng Phase B và `docs/REPORT/PHASE-B-IMPLEMENTATION-REPORT.md`.

## 4. NGUYÊN TẮC TRIỂN KHAI

### Mô hình thực hiện

```text
Implementation Owner: Hoàn
Tool Support: Cursor Agent
Excel: Academic Learning Reference
Team Dependency: NONE
```

Hoàn thực hiện toàn bộ; không phân công hoặc chờ bàn giao từ bốn thành viên khác. Excel chỉ tham khảo học tập.

### MASTER SCOPE LOCK

- Tuyệt đối không xóa bất kỳ file hoặc thư mục nào; không đổi tên, di chuyển hoặc tái cấu trúc project.
- Không xóa code, hàm, class hay chức năng cũ. Chỉ chỉnh bổ sung tối thiểu trong danh sách file của Phase; không ghi đè code/dữ liệu ngoài phạm vi.
- Không thay Dataset, Ground Truth hoặc Excel; thay đổi dữ liệu chỉ thuộc Phase D khi cần thiết. Upload vận hành phải vào vùng riêng, không vào `data/`.
- Không sửa tài liệu Phase A, C, D, E, F khi triển khai B. Không commit, push hoặc thay đổi Git history nếu chưa được yêu cầu.
- Trước sửa: kiểm tra Git Status, ghi HEAD, danh sách đường dẫn dự kiến thay đổi, hash file hiện có và danh mục file kể cả untracked/ignored liên quan. Giữ nguyên thay đổi có sẵn của người dùng.
- Nếu cần file ngoài danh sách: DỪNG và báo lý do, tác động, đề xuất phạm vi. Không tự mở rộng.
- Bắt buộc Final File Integrity Check: đối chiếu mốc trước/sau, xác minh không mất file, không rename/move, không có thay đổi ngoài phạm vi, dữ liệu và Excel nguyên hash, HEAD không đổi; `git diff` không đủ để kiểm tra file untracked/ignored.
- Lưu kết quả theo run ID mới, không ghi đè lần chạy cũ. Không tự dọn/xóa upload hoặc thư mục kiểm thử.

### Hiện trạng đã đối chiếu

| Thành phần | Bằng chứng trong code | Kết luận cho Phase B |
|---|---|---|
| Phase A | `COLOR_PRESETS`, `get_color_preset`, `build_hsv_config` trong `src/hsv_segment.py`; `/api/color-presets`; palette trong `app.js` | Có 15 preset; `verified=False`, không đồng nghĩa đã kiểm chứng ảnh thật |
| Báo cáo A | `docs/REPORT/PHASE-A-IMPLEMENTATION-REPORT.md` ghi 124/124 test | Bằng chứng lịch sử, không phải kết quả chạy lại ở nhiệm vụ lập kế hoạch |
| Xử lý Web | `/api/process` chỉ lưu một bộ mask vào `session_data` | Chưa có trạng thái so sánh độc lập |
| So sánh cũ | `scripts/run_hsv_comparison.py` có narrow/medium/wide cho Red | Tái sử dụng ý tưởng và module, chưa có UI nhiều màu; script quét mọi JPG nên sẽ gặp ảnh thiếu GT |
| ExperimentRunner | Có batch, CSV/JSON nhưng `run_single_experiment` yêu cầu GT | Không gọi trực tiếp cho upload không GT, không viết lại runner |
| Đánh giá | `SegmentationEvaluator.compute_metrics` có đủ năm chỉ số | Tái sử dụng, không viết công thức thứ hai |

Mọi preset/config mới dùng H 0–179, S/V 0–255. Module cũ chấp nhận cận H=180 để tương thích: giữ đường cũ, chuẩn hóa cấu hình mới và ghi rõ khác biệt, không âm thầm thay cấu hình cũ.

## 5. ĐIỀU KIỆN BẮT ĐẦU

- Đọc Phase mẫu `Phase.md`, Phase A, báo cáo A, `module_contracts.md`, các file bảng trên và test liên quan.
- Xác minh bằng code rằng chọn màu, chỉnh HSV, reset, nhiều Hue và pipeline A còn hoạt động; thiếu chức năng nền thì ghi `[DEPENDENCY — PHASE A]`, không tự làm lại A.
- Ghi trạng thái PASS/FAIL/PARTIAL/NOT VERIFIED riêng cho chức năng A và chất lượng dữ liệu.
- Có ảnh upload hợp lệ; GT không phải điều kiện để xây UI. Muốn thử nhánh metrics trước D, có thể dùng cặp tổng hợp hiện có hoặc fixture riêng, công khai loại dữ liệu.

## 6. PHẠM VI CHỈ LÀM VÀ KHÔNG ĐƯỢC LÀM

**CHỈ LÀM:** quản lý cấu hình HSV; API/UI so sánh; tính metrics trên GT đã kiểm tra; bảng/biểu đồ; lưu và chạy lại kết quả B; kiểm thử riêng B.

**KHÔNG ĐƯỢC LÀM:** AI, tự tối ưu ngưỡng, nhận diện tên vật thể; UI Morphology mới; sửa nhãn; chọn cấu hình bằng tập đánh giá cuối; viết lại Median/Morphology/Evaluator; triển khai export toàn ứng dụng của E; viết báo cáo đồ án F.

Danh sách file cho phép sau audit: `main.py`, `static/js/app.js`, `static/css/style.css`, `templates/index.html`, test mới `tests/test_phase_b_comparison.py`, báo cáo B và đầu ra phiên bản mới dưới `results/phase_b/`. Không mặc định sửa `src/experiment.py` hay script cũ. Có thể bổ sung helper nhỏ ngay trong `main.py`; nếu cần module mới ngoài danh sách phải báo trước.

## 7. CÁC TASK TRIỂN KHAI

### TASK B.1 — AUDIT VÀ KHÓA HỢP ĐỒNG SO SÁNH

**Mục tiêu:** xác định chính xác chỗ tích hợp và dữ liệu bất biến.

**File/module:** `main.py`, `src/hsv_segment.py`, `src/experiment.py`, `src/evaluation.py`, ba file Frontend, test A; chỉ đọc thuật toán và script cũ.

**Cách thực hiện:** lập bảng endpoint/request/response; ghi dữ liệu nào đang bị thay trong session. Chốt hợp đồng sau trước khi code: một lượt gồm `schema_version`, `comparison_id`, ảnh với SHA-256 của file và kích thước, `target_color_id`, danh sách `config_id/name/hsv`, `fixed_pipeline`, `evaluation_stage`, GT tùy chọn với hash và màu mục tiêu. Snapshot cấu hình thực tế thay vì chỉ giữ tên preset có thể đổi sau này. Mặc định chấm `raw`; cho phép chọn `morph` với pipeline cố định. Mỗi lượt chỉ có một màu mục tiêu để cùng GT mang cùng ý nghĩa; muốn so màu khác phải tạo lượt khác hoặc GT riêng, không xếp hạng khác màu bằng một GT.

**Input:** code và báo cáo hiện tại. **Output:** bảng hiện trạng, allowlist, schema, danh sách ca kiểm thử trong báo cáo B.

**DONE checklist:**

- [ ] Đã đọc đủ source, Git Status và chụp mốc toàn vẹn.
- [ ] Phân biệt chức năng đã có, cần bổ sung, phụ thuộc và ngoài phạm vi.
- [ ] Chốt stage, màu, ảnh và cách nhận diện GT; không còn giả định ngầm.

### TASK B.2 — QUẢN LÝ CẤU HÌNH HSV

**Mục tiêu:** tạo được cấu hình có thể chỉnh sửa và lưu độc lập.

**File/module:** `app.js`, `index.html`, `style.css`, validation trong `main.py`; đọc preset qua `/api/color-presets`.

**Cách thực hiện:** lấy preset A làm cấu hình gốc, nhân bản rồi chỉnh H/S/V; tên không rỗng, ID duy nhất, tối đa 6 cấu hình. Không ghi ngược vào preset toàn cục. Cho phép cập nhật, chọn cấu hình và bỏ mục khỏi danh sách trong bộ nhớ; thao tác này không xóa file đã lưu. Red giữ hai khoảng Hue; màu `sv` ép phạm vi H toàn miền và ghi rõ Hue không áp dụng. Kiểm tra số nguyên thực sự, từ chối boolean, số thực, ngoài miền và min>max. UI báo ngay lỗi; Backend vẫn tự kiểm tra. Nhập JSON chỉ nhận schema hỗ trợ, giới hạn số cấu hình, không nhận đường dẫn file tùy ý hoặc mã thực thi.

**Input:** preset A hoặc JSON đã xuất. **Output:** danh sách cấu hình hợp lệ có snapshot HSV.

**DONE checklist:**

- [ ] Tạo/nhân bản/chỉnh/đổi tên/chọn/bỏ khỏi danh sách hoạt động cho cả hue và sv.
- [ ] 15 preset A vẫn là nguồn duy nhất; chỉnh cấu hình không đổi preset.
- [ ] Dữ liệu sai bị chặn ở cả UI và API.

### TASK B.3 — BACKEND CHẠY SO SÁNH CÔNG BẰNG

**Mục tiêu:** trả nhiều kết quả mà không ghi đè trạng thái xử lý đơn.

**File/module:** `main.py`; gọi `HSVSegmenter`, `MedianFilter`, `MorphologyOperator` hiện có.

**Cách thực hiện:** thêm `POST /api/compare-hsv` nhận JSON gồm session, màu, configurations và fixed_pipeline; chạy đồng bộ với giới hạn 2–6 cấu hình. Copy ảnh một lần làm nguồn bất biến, không resize hoặc đổi ánh sáng giữa các cấu hình. Chỉ HSV được khác nhau; median và morphology là một object chung, không nhận bản riêng từng cấu hình. Ghi thứ tự operation, shape, kernel, iterations và config thực tế trong response. Trước C, snapshot hành vi hiện tại: median 5 mặc định, ellipse, Closing 1 rồi Opening 1 nếu bật; sau C nhận cùng schema operations tại C. Lưu kết quả theo comparison ID trong session riêng, không dùng vòng lặp gọi `/api/process` để ghi đè bộ mask đơn. Từ chối toàn request sai trước khi chạy; lỗi xử lý bất ngờ phải có trạng thái rõ, không xếp hạng tập kết quả thiếu.

**Input:** ảnh session, 2–6 HSV configs, pipeline chung. **Output:** comparison ID, hash/snapshot, raw/median/morph PNG, thời gian, selected_pixels, applied_config từng mục.

**DONE checklist:**

- [ ] Cùng ảnh, cùng fixed_pipeline, chỉ HSV thay đổi.
- [ ] Cấu hình giống nhau cho mask giống nhau từng pixel.
- [ ] Chạy so sánh không làm mất kết quả đơn và không mutate ảnh gốc.
- [ ] Session lạ/request sai trả lỗi 4xx rõ ràng; không thành 500 do lỗi nhập liệu.

### TASK B.4 — GT, METRICS VÀ TIÊU CHÍ TỐT NHẤT

**Mục tiêu:** đánh giá đúng mask, đúng GT, không tạo điểm số khi thiếu nhãn.

**File/module:** `main.py`, gọi `SegmentationEvaluator`; `app.js` hiển thị trạng thái.

**Cách thực hiện:** thêm `POST /api/compare-hsv/evaluate` multipart gồm session ID, comparison ID, evaluation_stage và `ground_truth`. Đọc GT chưa chuyển đổi: phải PNG một kênh uint8, cùng H×W, unique values thuộc {0,255}, đã xác nhận cùng ảnh/màu; kiểm tra hash nếu manifest có. Không threshold/resize tự động để làm GT sai thành hợp lệ. Kiểm tra kỹ thuật không tự chứng minh nhãn đúng ngữ nghĩa: người chạy xác nhận cặp ảnh/nhãn, dùng manifest D khi có. Tính đủ năm metrics và TP/TN/FP/FN bằng evaluator hiện tại. Ghi quy ước mẫu số 0: evaluator hiện trả 0, kể cả cả pred/GT đều nền; không sửa công thức trong B. Không gộp ca âm tính vào xếp hạng ảnh có đối tượng mà thiếu giải thích.

Xếp hạng cùng lượt/stage theo IoU giảm dần, rồi F1 giảm dần; bằng nhau ở độ chính xác đầy đủ thì đồng hạng. Hiển thị Pixel Accuracy nhưng không chọn tốt nhất chỉ theo Accuracy. Chỉ gọi là “tốt nhất trong các cấu hình đã thử trên ảnh này”. Thiếu GT hoặc bất kỳ mục lỗi: không công bố người thắng. Khi D có split, chọn cấu hình theo macro-IoU trên tuning; tuyệt đối không dùng kết quả test để điều chỉnh lại.

**Input:** bộ mask so sánh + GT độc lập. **Output:** bảng metrics có nguồn GT/stage, ranking hoặc lý do không xếp hạng.

**DONE checklist:**

- [ ] Không GT → metrics null/N/A, không phải 0 và không winner.
- [ ] GT sai kích thước/kênh/giá trị bị từ chối, không biến đổi nhãn.
- [ ] Năm chỉ số khớp evaluator sai số ≤ 1e-9; xử lý đồng hạng được kiểm tra.

### TASK B.5 — MASK CẠNH NHAU, BẢNG VÀ BIỂU ĐỒ

**Mục tiêu:** người dùng nhìn được tác động của ngưỡng.

**File/module:** `index.html`, `app.js`, `style.css`.

**Cách thực hiện:** thêm vùng so sánh có ảnh gốc, tên cấu hình, toàn bộ Hue ranges/S/V, stage và thumbnail mask cùng tỷ lệ; có xem kích thước gốc. Thay stage cập nhật đồng thời tất cả mask/metrics. Bảng chứa năm chỉ số, đơn vị thống nhất phần trăm khi trình bày, số chuẩn 0–1 trong JSON. Dùng SVG/Canvas hoặc thanh biểu đồ CSS tại chỗ để không phát sinh dependency mạng; trục 0–100%, legend rõ. Không dùng pixel trắng làm Accuracy. Khi đổi ảnh hoặc sửa config/pipeline, đánh dấu kết quả cũ “không còn khớp cấu hình hiện tại”, vô hiệu hóa ranking đến khi chạy lại; không xóa file lịch sử.

**Input:** response so sánh/đánh giá. **Output:** grid mask, bảng, biểu đồ, trạng thái thiếu GT/lỗi/đang chạy.

**DONE checklist:**

- [ ] 2, 3 và 6 mask đọc được trên màn hình rộng, có cuộn/bố cục phù hợp ở 768 px.
- [ ] Tên, HSV, stage và số liệu trên bảng/biểu đồ khớp response.
- [ ] Có trạng thái tải, chống bấm lặp và ngăn hiển thị response cũ đè lượt mới.

### TASK B.6 — LƯU VÀ CHẠY LẠI KẾT QUẢ B

**Mục tiêu:** tái lập được thí nghiệm sau khi session mất.

**File/module:** `main.py`, `app.js`, `index.html`; đầu ra mới `results/phase_b/<run_id>/` nếu lưu server, hoặc gói tải xuống từ bộ nhớ.

**Cách thực hiện:** bổ sung `POST /api/compare-hsv/export` theo comparison ID trả ZIP gồm `comparison.json`, các mask PNG theo ID và thông tin phiên bản Python/OpenCV/NumPy. JSON lưu config đã áp dụng, fixed_pipeline, stage, hashes ảnh/GT, metrics nullable, quy tắc ranking và thời gian; không nhúng đường dẫn tuyệt đối cá nhân. Ảnh/GT gốc không bắt buộc đóng gói: hướng dẫn upload lại file cùng hash. Nút nhập JSON khôi phục configs và pipeline, kiểm tra hash ảnh trước khi gắn metrics cũ. Chạy lại tạo ID mới và tính lại; không tin metrics nhập như kết quả mới. Giới hạn kích thước JSON 1 MiB, schema version=1; không giải nén ZIP nhập trên server, chỉ nhập JSON. Gói CSV toàn hệ thống do E sở hữu, không tạo hệ export thứ hai ở đây.

**Input:** comparison hoàn tất hoặc JSON đã lưu + ảnh gốc. **Output:** gói tái lập và một lượt mới.

**DONE checklist:**

- [ ] Đóng/mở trang, nhập config, upload cùng ảnh và chạy lại cho mask giống từng pixel trong cùng môi trường.
- [ ] JSON sai schema/ảnh khác hash bị báo; metrics cũ không gắn sang ảnh mới.
- [ ] Không ghi đè kết quả cũ và không xóa file để “làm sạch”.

### TASK B.7 — KIỂM THỬ VÀ BÁO CÁO CHỨC NĂNG B

**Mục tiêu:** chứng minh phần mới hoạt động, không nhận thay nghiệm thu E.

**File/module:** `tests/test_phase_b_comparison.py`, test A/HSV liên quan chỉ chạy an toàn; báo cáo B.

**Cách thực hiện:** test API so sánh và UI riêng chức năng B bằng fixture tách biệt, patch upload/results/session sang vùng riêng. Thực hiện toàn bộ ma trận mục 8; kiểm tra script/test có side effect trước khi chạy, không gọi `src/experiment.py` main hoặc script ghi đè report/data. Ghi lệnh, môi trường, số PASS/FAIL/SKIP/NOT RUN và bằng chứng từng tiêu chí. Chỉ gọi kết quả dữ liệu tổng hợp là kiểm chứng chức năng; đánh giá học thuật ảnh thật do D/E cung cấp.

**Input:** chức năng B đã triển khai. **Output:** test và báo cáo B có liên kết artifact.

**DONE checklist:**

- [ ] Ma trận B được chạy hoặc ghi lý do chưa chạy; không tự tuyên bố PASS.
- [ ] Báo cáo ghi rõ chức năng và chất lượng học thuật là hai trạng thái riêng.
- [ ] Không lặp lại bộ unit thuật toán Phase 2; chỉ chạy hồi quy cần thiết.

### TASK B.8 — FINAL REVIEW VÀ FINAL FILE INTEGRITY CHECK

**Mục tiêu:** kết thúc B với diff kiểm soát được.

**File/module:** allowlist và báo cáo B.

**Cách thực hiện:** rà từng Acceptance Criteria, kiểm tra trước/sau theo Master Scope Lock, ghi file thêm/sửa và lý do, bất thường có sẵn, HEAD, hash dữ liệu/Excel. Kiểm tra các file untracked ban đầu vẫn còn nguyên. Đánh dấu B chức năng PASS chỉ khi tất cả tiêu chí bắt buộc đạt; GT học thuật chưa có phải ghi dependency D/E, không tuyên bố project hoàn tất.

**Input:** kết quả B. **Output:** bảng review, bằng chứng toàn vẹn, trạng thái cuối.

**DONE checklist:**

- [ ] Không file bị xóa/di chuyển/đổi tên hoặc sửa ngoài phạm vi.
- [ ] Các tiêu chí có bằng chứng, tồn đọng có chủ Phase và điều kiện đóng.
- [ ] Đã dừng, không tự triển khai C.

## 8. KẾ HOẠCH KIỂM THỬ

| Mã | Ca kiểm thử | Kỳ vọng |
|---|---|---|
| B-T01 | 2/3/6 cấu hình; 1 hoặc 7 cấu hình | Hợp lệ chạy; ngoài giới hạn bị từ chối |
| B-T02 | Red hai Hue, Green một Hue, White/Black/Gray sv | Schema đúng, không áp Hue sai |
| B-T03 | Hai config giống nhau, cùng ảnh/pipeline | Mask bằng nhau từng pixel |
| B-T04 | Min>max, H=180 ở schema mới, float, bool, ID trùng | 4xx có thông báo, không ghi trạng thái dở |
| B-T05 | Thiếu GT; GT 128, RGB, sai size, khác ảnh | N/A khi thiếu; GT không hợp lệ bị từ chối; xác nhận cặp/ngữ nghĩa |
| B-T06 | GT fixture tính tay; IoU/F1 đồng hạng | Năm metrics khớp ≤1e-9; đồng hạng đúng |
| B-T07 | Đổi ảnh/config/stage trong khi request chạy | Không dùng response cũ, không tái sử dụng sai metrics |
| B-T08 | Export/import/chạy lại và ảnh khác hash | Mask tái lập; ảnh khác được cảnh báo/chặn gắn điểm cũ |
| B-T09 | Xử lý đơn sau so sánh và ngược lại | Hai trạng thái không ghi đè nhau |

Chạy kiểm thử B trong vùng riêng; không tự xóa artifact. E sẽ kiểm tra luồng xuyên Phase và tương thích Windows, không viết lại các ca này.

## 9. ACCEPTANCE CRITERIA

| Tiêu chí | Điều kiện đo lường | Bằng chứng |
|---|---|---|
| Quản lý cấu hình | Đủ 6 thao tác của B.2; nhận 2–6 cấu hình | Test và thao tác UI |
| Công bằng | Một hash ảnh, một fixed_pipeline, một target/stage cho cả lượt | JSON + so sánh snapshot |
| Hiển thị | 2–6 mask cạnh nhau, HSV đầy đủ, bảng và biểu đồ năm chỉ số | Ảnh chụp khi triển khai |
| Metrics | GT hợp lệ; sai lệch với evaluator ≤1e-9 | B-T05/06 |
| Xếp hạng | IoU rồi F1; đồng hạng đúng; không GT không winner | B-T06 |
| Tái lập | Export/import tạo lại mask giống từng pixel cùng môi trường | B-T08 |
| Hồi quy | Các ca A liên quan và xử lý đơn không phát sinh lỗi mới | Log có mốc trước/sau |
| Toàn vẹn | 0 file mất/rename/move; 0 thay đổi ngoài allowlist; HEAD không đổi | Final File Integrity Check |

Không đặt ngưỡng chất lượng IoU tùy tiện để hợp thức hóa preset; B nghiệm thu chức năng, không chứng nhận 15 màu tốt trên mọi ảnh.

## 10. RỦI RO VÀ PHƯƠNG ÁN XỬ LÝ

- So sánh sai màu với cùng GT: khóa target một lượt và yêu cầu xác nhận cặp ảnh/nhãn.
- Tốn bộ nhớ vì base64 nhiều ảnh: tối đa 6 cấu hình, một lượt xử lý đang chạy trên UI; E đo và khóa giới hạn ảnh/session.
- Nhãn đầu vào bị tự threshold ở API cũ: nhánh so sánh kiểm tra raw GT nghiêm ngặt, không dùng thành công API cũ làm bằng chứng nhãn hợp lệ.
- Thiếu GT thật: tiếp tục hoàn tất UI và kiểm thử bằng dữ liệu tổng hợp độc lập; D bổ sung GT, E đo cuối.
- Preset thay đổi về sau: snapshot đầy đủ, hash và phiên bản; chạy lại không phụ thuộc tên preset.

## 11. DEPENDENCIES VÀ RANH GIỚI SỞ HỮU

```text
A (hợp đồng màu) → B (so sánh) → C (controls Morphology)
→ D (dữ liệu/GT + tuning + khóa split) → E (kiểm thử + đo test cuối)
→ F (báo cáo + bảo vệ)
D ──GT hợp lệ──→ metrics học thuật của B/E
C ──pipeline mới──→ adapter fixed_pipeline đã định nghĩa ở B
```

Thứ tự triển khai B→C→D→E→F giữ nguyên. B không chờ D để xây UI; kết quả học thuật cuối bắt buộc chờ D. B sở hữu so sánh, ranking và gói tái lập B; C chỉ mở controls và nối schema; D sở hữu dữ liệu/tuning, E sở hữu kiểm thử xuyên hệ thống và export toàn ứng dụng, F chỉ dùng bằng chứng. Mỗi Phase ghi một báo cáo triển khai riêng, không viết lại báo cáo Phase trước.

## 12. BÁO CÁO ĐẦU RA

`docs/REPORT/PHASE-B-IMPLEMENTATION-REPORT.md`: hiện trạng trước sửa; schema/API; file thay đổi; ma trận kiểm thử và lệnh; hình UI; JSON chạy lại; tiêu chí PASS/FAIL/PARTIAL/NOT VERIFIED; giới hạn GT; dependency D/E; Final File Integrity Check. Số liệu cũ chỉ được trích với nguồn, stage và phạm vi; không coi là lượt chạy mới.

## 13. FINAL REVIEW

- [ ] TASK B.1–B.8 có bằng chứng DONE.
- [ ] Acceptance Criteria đã đối chiếu từng hàng.
- [ ] Không xếp hạng vô căn cứ; không sửa Dataset hoặc preset gốc.
- [ ] Báo cáo và kiểm tra toàn vẹn đã hoàn tất.

## 14. STOP RULE

Sau báo cáo và Final Review: **DỪNG**. Không commit/push, không chuyển C hoặc tự làm D. Nếu thiếu dependency hoặc cần ngoài scope: ghi blocker và đề xuất cụ thể. Chỉ triển khai Phase tiếp khi Hoàn yêu cầu/xác nhận; file kế hoạch này không phải xác nhận B DONE.

## 15. TỔNG KẾT PHASE VÀ THỨ TỰ THỰC HIỆN

B.1 Audit → B.2 Quản lý config → B.3 Backend công bằng → B.4 GT/metrics/ranking → B.5 UI → B.6 Lưu/chạy lại → B.7 Kiểm thử/báo cáo → B.8 Review/toàn vẹn → DỪNG. Đầu ra là công cụ so sánh có thể tái lập; chứng minh chất lượng cuối tiếp tục qua D và E.
