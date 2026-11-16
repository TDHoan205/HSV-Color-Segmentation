# PHASE E — KIỂM THỬ TOÀN HỆ THỐNG

## 1. MỤC TIÊU PHASE

Xác minh ứng dụng hoạt động từ Upload → Chọn màu → Xử lý → So sánh → Đánh giá → Export, với dữ liệu hợp lệ và đầu vào lỗi. Bổ sung tối thiểu phần export toàn ứng dụng và kiểm soát vận hành còn thiếu; đo chất lượng cuối theo freeze D, không điều chỉnh ngưỡng dựa vào final_test.

Đây là kế hoạch thực hiện, không phải chứng nhận hệ thống đã PASS. Phải đọc source và báo cáo thực tế khi bắt đầu.

## 2. SƠ ĐỒ QUY TRÌNH THỰC HIỆN

```text
Audit A–D và Git Status → Lập ma trận yêu cầu/API/rủi ro
→ Cô lập vùng kiểm thử → Chốt lỗi và bổ sung tối thiểu
→ Integration Test API/module/session/export
→ Kiểm thử UI và End-to-End trên trình duyệt
→ Windows + tài nguyên + hiệu năng + bảo mật cơ bản
→ Xác minh freeze D → Chạy final_test và lưu bằng chứng
→ Báo cáo → Final Review/toàn vẹn → DỪNG
```

## 3. ĐẦU RA BẮT BUỘC

- Ma trận traceability: mỗi yêu cầu đề bài → chức năng → test ID → kết quả → bằng chứng.
- Integration tests trong `tests/test_system_integration.py`, kịch bản E2E trong báo cáo E và bằng chứng trình duyệt. Dùng công cụ có sẵn; không bắt buộc thêm framework E2E nặng.
- Export thống nhất cho mask, ảnh phân đoạn, visualization nếu có GT, metrics JSON/CSV và cấu hình; tái sử dụng gói B.
- Bug log có severity, nguyên nhân, bản sửa và retest; phân biệt lỗi có sẵn với lỗi mới.
- Benchmark trên máy Windows thực tế, giới hạn tài nguyên được đo và kiểm soát, bản chạy demo không debug.
- `results/phase_e/<run_id>/` chứa log/artifact/metrics cuối và `docs/REPORT/PHASE-E-SYSTEM-TEST-REPORT.md`.

## 4. NGUYÊN TẮC TRIỂN KHAI

```text
Implementation Owner: Hoàn
Tool Support: Cursor Agent
Excel: Academic Learning Reference
Team Dependency: NONE
```

Hoàn chạy test, sửa tối thiểu và nghiệm thu; không phụ thuộc người khác. Excel chỉ dùng học tập.

### MASTER SCOPE LOCK

- Tuyệt đối không xóa file/thư mục; không rename, move hoặc tái cấu trúc project. Không xóa code, hàm, class hoặc chức năng cũ.
- Không ghi đè code/dữ liệu ngoài phạm vi; giữ nguyên thay đổi có sẵn. Chỉ thay file trong allowlist phục vụ lỗi/thiếu chức năng tối thiểu của E.
- Không thay Dataset, Ground Truth, manifest/freeze D hoặc Excel. Nếu dữ liệu sai phải báo dependency về D, không tự sửa ở E.
- Không sửa tài liệu các Phase khác; không commit, push hoặc thay đổi Git history nếu chưa được yêu cầu.
- Trước sửa: Git Status, HEAD, allowlist, danh mục và hash file hiện có kể cả untracked/ignored có liên quan; kiểm tra side effect từng test/script.
- Cần sửa ngoài danh sách, đổi thuật toán hoặc bổ sung tính năng lớn: DỪNG và báo lý do/tác động/scope tối thiểu. Không dùng kiểm thử để mở rộng đề tài.
- Final File Integrity Check đối chiếu mốc trước/sau: 0 file mất/rename/move, 0 sửa ngoài phép, dữ liệu/GT/Excel/freeze nguyên hash, HEAD không đổi; kiểm tra cả file không được Git theo dõi.
- Test/upload/export chỉ ghi vùng mới theo run ID; không xóa artifact, không dọn uploads cũ. Giải phóng tham chiếu session trong bộ nhớ được phép, không xóa file trên đĩa.

### HIỆN TRẠNG VÀ RỦI RO ĐÃ THẤY TRONG SOURCE

Mốc 16/11/2026: Flask có `/`, `/api/upload`, `/api/process`, `/api/download-mask`, `/api/evaluate`, `/api/get-info`, `/api/color-presets`, `/api/health`; các endpoint B/C chỉ được coi có sau khi audit code thực tế. API upload giới hạn 50 MiB nhưng chưa có giới hạn pixel/session; tên file dựa timestamp giây có nguy cơ trùng; `session_data` toàn cục và không hết hạn; `resetSession()` chỉ reset UI. Process có thể giữ metrics/GT cũ sau xử lý lại. Evaluate cũ đọc GT thành ảnh màu rồi threshold 127, có thể che nhãn không nhị phân. Chạy trực tiếp `main.py` dùng debug=True và host 0.0.0.0. Web hiện mới export mask; ExperimentRunner có CSV/JSON nhưng chưa phải export Web. Đây là các điểm cần xác minh lại, không phải kết quả exploit hoặc kết luận test đã chạy.

## 5. ĐIỀU KIỆN BẮT ĐẦU

- Đọc báo cáo A/B/C/D, `module_contracts.md`, source Backend/Frontend, tests và freeze D; xác minh chức năng thực tế.
- A–C đạt tiêu chí chức năng; D có dữ liệu approved và freeze có hash/split/config. Thiếu thì ghi `[DEPENDENCY — PHASE ...]`, không đánh dấu pass nhờ file tồn tại.
- Xác định interpreter/dependencies thật; `requirements.txt` có pytest nhưng báo cáo cũ nói môi trường chưa cài. Kiểm tra hiện tại, có thể dùng unittest; không chép version cũ làm version mới.
- Có vùng `results/phase_e/<run_id>/` mới và cấu hình upload riêng cho kiểm thử, không sử dụng upload/session của người dùng.

## 6. PHẠM VI CHỈ LÀM VÀ KHÔNG ĐƯỢC LÀM

**CHỈ LÀM:** Integration/E2E, hồi quy có chọn lọc, kiểm thử lỗi/tài nguyên/Windows, sửa validation/session/export thiếu tối thiểu, đo final_test theo D, ghi báo cáo E.

**KHÔNG ĐƯỢC LÀM:** viết lại unit suite Phase 2, làm lại A/B/C/D, đổi nhãn/split/ngưỡng theo điểm test, thêm AI, auth/database/cloud hay benchmark quy mô sản phẩm, viết slide/báo cáo đồ án F.

Allowlist: `main.py`, `templates/index.html`, `static/js/app.js`, `static/css/style.css`, test mới `tests/test_system_integration.py`, script mới `scripts/run_final_evaluation.py`, báo cáo E và artifact trong `results/phase_e/<run_id>/`. Các `src/*.py`, test Phase trước, Dataset/GT/freeze/Excel mặc định chỉ đọc. Thiếu thư viện kiểm thử thì ưu tiên công cụ đã có; nếu cần sửa requirements phải báo ngoài scope trước.

## 7. CÁC TASK TRIỂN KHAI

### TASK E.1 — AUDIT, MA TRẬN KIỂM THỬ VÀ MỐC TRƯỚC SỬA

**Mục tiêu:** biết chính xác yêu cầu nào có bằng chứng và phần thiếu tối thiểu.

**File/module:** main, Frontend, tất cả module/tests chỉ đọc, báo cáo A–D và freeze.

**Cách thực hiện:** lập inventory toàn route/method/payload/status; bổ sung routes B/C thật vào danh sách, không chỉ test route đề xuất. Mỗi requirement có test ID, dữ liệu, expected, actual, PASS/FAIL/SKIP/NOT RUN và artifact. Chạy kiểm tra khởi động/health an toàn, phân loại lỗi có sẵn, lập allowlist chi tiết trước sửa. Đọc test có ghi file trước khi chạy; không gọi main trong ExperimentRunner hoặc generator và không chạy script ghi đè report.

**Input:** code/báo cáo/freeze. **Output:** ma trận, bug log ban đầu, môi trường và baseline toàn vẹn.

**DONE checklist:**

- [ ] Toàn route và yêu cầu đề bài được ánh xạ.
- [ ] Bằng chứng cũ và test mới tách biệt; không nhận số PASS lịch sử là kết quả E.
- [ ] Có allowlist và vùng kiểm thử tách biệt.

### TASK E.2 — BỔ SUNG EXPORT TOÀN ỨNG DỤNG TỐI THIỂU

**Mục tiêu:** hoàn thành các đầu ra bắt buộc còn thiếu mà không xây hệ export thứ hai.

**File/module:** `main.py`, Frontend; đọc export B và `ExperimentRunner.save_results_csv` để đối chiếu key.

**Cách thực hiện:** giữ `/api/download-mask`. Nếu B chưa có export dùng chung cho xử lý đơn, thêm `POST /api/export-results` nhận session ID và run/comparison ID, không nhận path người dùng. Trả ZIP từ bộ nhớ hoặc vùng riêng: `mask_raw.png`, `mask_median.png`, `mask_morph.png`, `segmented.png` là `bitwise_and` ảnh gốc với final mask, visualization TP/FP/FN khi có GT, `config.json`, `metrics.json`, `metrics.csv` và `run.json`. Với comparison, gọi cơ chế export B và mở rộng có tương thích để đủ CSV/ảnh kết quả, không tái tính pipeline hoặc tự dựng lại config. Nếu chức năng này đã có thì chỉ test và sửa lỗi cần thiết.

JSON lưu số đầy đủ 0–1, applied_config, stage, hashes, schema/version và lý do metrics null khi thiếu GT. CSV một dòng cho mỗi sample/config/stage, các cột ID, target, TP/TN/FP/FN, năm metrics, status; giá trị không có để trống, không xuất 0 giả. Encoding UTF-8-SIG cho Excel trên Windows, dùng csv writer xử lý tên có dấu/phẩy/newline, tránh công thức bảng tính từ tên do người dùng nhập. Filename trong ZIP do server tạo từ ID an toàn, không dùng path client; không có đường dẫn tuyệt đối hoặc dữ liệu session khác. Export chưa process trả 400; export sau process nhưng chưa GT vẫn được, metrics N/A. UI có nút và hướng dẫn rõ.

**Input:** kết quả hợp lệ hiện có. **Output:** ZIP/JSON/CSV/PNG nhất quán và không tính lại ngầm.

**DONE checklist:**

- [ ] Đủ mask, ảnh phân đoạn, config, metrics JSON/CSV; visualization có điều kiện.
- [ ] Nội dung export khớp run hiện hành, không lấy metrics stale.
- [ ] B không có hai hệ export khác nhau; gói cũ vẫn đọc được.

### TASK E.3 — VALIDATION, SESSION VÀ VẬN HÀNH TỐI THIỂU

**Mục tiêu:** sửa đúng lỗi cản trở độ ổn định và an toàn demo đã xác minh.

**File/module:** `main.py`, `app.js`, `index.html` khi cần thông báo trạng thái.

**Cách thực hiện:** chốt contract lỗi: dữ liệu sai JSON/null/list/thiếu field/params → 400; session không tồn tại giữ 400 theo API hiện hữu; route lạ → 404; quá tải tài nguyên → 429 có lý do; quá 50 MiB → 413. Sai kiểu, float/bool, kernel sai, min>max phải được kiểm tra trước khi gọi module. Không trả traceback hoặc đường dẫn máy cho client. Giữ legacy payload theo contract B/C, ghi applied_config, không âm thầm đổi schema mới.

Với GT Web, validate raw PNG một kênh uint8 0/255 và size trước evaluator; không threshold/resize nhãn sai rồi chấm. Khi process/compare tạo run mới, gắn run ID và vô hiệu hóa metrics/visualization cũ; UI không export nhầm lượt. GT được tái sử dụng chỉ khi có liên kết ảnh/hash/target hợp lệ và tính lại metrics. Session ID dùng token khó đoán thay timestamp nhưng vẫn là chuỗi tương thích client. Upload dùng UUID không trùng và `secure_filename`, kiểm tra bytes decode thật; file lạ/path traversal không thoát vùng upload.

Giới hạn đề xuất phải hiện trong config và test biên: 50 MiB/file, tối đa 6 cấu hình/lượt, morphology theo C, tối đa 5 session đang giữ và TTL 30 phút; guard kích thước ảnh dựa bước E.6 trước decode ảnh lớn khi có thể. Mỗi session lưu estimated byte arrays, trả lỗi khi vượt budget đã đo; chỉ giải phóng tham chiếu bộ nhớ khi hết TTL, không tự xóa upload trên đĩa. Kiểm tra dung lượng vùng upload trước ghi; thiếu dung lượng trả lỗi rõ thay vì tiếp tục. Demo mặc định bind 127.0.0.1, debug=False; vẫn cho cấu hình dev rõ ràng nếu cần, không mở triển khai public trong E.

**Input:** lỗi cụ thể từ E.1 và contract mới. **Output:** bản sửa nhỏ, validation/session/config vận hành được kiểm thử.

**DONE checklist:**

- [ ] Đầu vào sai không gây 500 do validation thiếu.
- [ ] Không metrics stale, filename trùng hay truy cập file ngoài vùng cho phép.
- [ ] Session hết hạn có thông báo; file cũ vẫn còn nguyên.
- [ ] Demo chạy cục bộ không debug; không thêm kiến trúc ngoài đề tài.

### TASK E.4 — INTEGRATION TEST TOÀN API

**Mục tiêu:** kiểm tra Flask nối đúng module, trạng thái và export.

**File/module:** `tests/test_system_integration.py`, `main.py`, modules chỉ đọc; vùng upload/results riêng.

**Cách thực hiện:** dùng Flask test_client, cô lập `session_data` và app.config trong từng nhóm test, giữ/khôi phục tham chiếu cũ; mọi fixture ghi vào vùng E mới, không xóa file sau test. Kiểm tra route thật theo E.1, content-type, status và schema. Pipeline một request phải bằng gọi trực tiếp module cùng config; đánh giá bằng evaluator trên cùng mask/GT; PNG export decode có shape/binary đúng; CSV/JSON khớp response ≤1e-9. Test hai session độc lập, xử lý lại làm cũ metrics, không process mà evaluate/download/export, session lạ/hết hạn, lỗi GT, lỗi file, tên Unicode/path traversal, request sai/malformed, 413 và lỗi ghi đĩa giả lập. Không tạo file 50 MiB thật chỉ để test 413: dùng giới hạn thấp trong app test hoặc stream có kiểm soát, ghi rõ phương pháp.

**Input:** API sau sửa tối thiểu và fixtures. **Output:** log integration theo test ID.

**DONE checklist:**

- [ ] 100% route thực tế có ca thành công hoặc ca có điều kiện và ca lỗi phù hợp.
- [ ] Kiểm tra session isolation, stale state và export round-trip.
- [ ] Không ghi vào data hoặc upload của người dùng.

### TASK E.5 — FRONTEND VÀ END-TO-END TRÊN TRÌNH DUYỆT

**Mục tiêu:** chứng minh thao tác người dùng hoạt động, không chỉ test_client.

**File/module:** Frontend, Backend, artifact ảnh chụp/log trong E.

**Cách thực hiện:** chạy server cục bộ bằng upload folder E, mở trình duyệt và ghi môi trường/viewport. Thực hiện ít nhất ba luồng đầy đủ: Red hai Hue với GT; một màu hue khác với GT; White/Black/Gray chế độ sv với fixture độc lập hoặc ảnh thật có GT, ghi rõ loại dữ liệu. Mỗi luồng Upload → palette/slider/reset → median → morphology → process → 3 configs compare → GT → bảng/biểu đồ → export → mở PNG/CSV/JSON kiểm chứng. Bổ sung luồng không GT phải có N/A và export hợp lệ, một ảnh/GT lỗi, đổi ảnh/reset, thao tác nhanh khiến response về đảo thứ tự, refresh/session mất.

Kiểm tra đủ 15 palette nạp đúng config, H 0–179 ở controls mới; sv vô hiệu Hue; Red giữ hai khoảng; mọi control C có thể dùng và payload đúng. Kiểm tra tab navigation bằng click/keyboard, trạng thái loading, disable khi thiếu input, viewport 1366×768 và 768 px, không lỗi JavaScript nghiêm trọng hoặc request lỗi bị giấu. Dùng ảnh chụp làm bằng chứng trực quan khi có thể, không ghi “đã kiểm tra bằng mắt” chỉ dựa DOM. Nếu công cụ trình duyệt không dùng được, ghi NOT RUN và hướng dẫn Hoàn thao tác từng bước, không coi E2E đã PASS.

**Input:** ứng dụng chạy và cặp ảnh/GT đã xác định. **Output:** biên bản E2E, screenshots, console/network log và file export.

**DONE checklist:**

- [ ] Ba luồng đầy đủ và nhánh không GT/lỗi được thực hiện có bằng chứng.
- [ ] UI/config/applied_config/metrics/export cùng run ID.
- [ ] Không còn lỗi UI nghiêm trọng chặn đường đi bắt buộc.

### TASK E.6 — WINDOWS, TÀI NGUYÊN, HIỆU NĂNG VÀ BẢO MẬT CƠ BẢN

**Mục tiêu:** có giới hạn demo dựa trên phép đo thật và xử lý tài nguyên có kiểm soát.

**File/module:** config `main.py`, test hệ thống, artifact benchmark E; không sửa Dataset.

**Cách thực hiện:** ghi Windows/Python/dependency/CPU/RAM; chạy từ đường dẫn có khoảng trắng, tên upload tiếng Việt, file cùng tên, path dài hợp lý; test lỗi permission/disk qua giả lập. Kiểm tra server restart khiến session mất được thông báo, RAM TTL giải phóng tham chiếu nhưng upload cũ không bị xóa. Lập thống kê dung lượng trước/sau, thêm guard/cảnh báo và tài liệu thao tác bảo trì, không tự dọn file.

Benchmark pipeline và compare 3 cấu hình: warm-up 1 lượt rồi 5 lượt đo ở 512×512 và khoảng 1 MP; ghi median/p95 (p95 từ 5 mẫu chỉ mô tả mẫu nhỏ), dung lượng input/output và process memory hoặc phương pháp đo được hỗ trợ. Mục tiêu demo đề xuất tại 1 MP: xử lý đơn p95 ≤5 giây, so sánh 3 config ≤15 giây; E2E 10 lượt liên tiếp không crash. Đây là mục tiêu mới cần đo, không là số hiệu năng đã đạt. Khởi đầu giới hạn 1 MP decoded và 6 config, dùng ảnh fixture riêng; nếu cần hỗ trợ ảnh lớn hơn, tăng chỉ sau đo RAM/time, không tự resize âm thầm. Nếu mục tiêu không đạt, sửa lãng phí rõ ràng trong adapter/serialization, công bố số thật và đề xuất giới hạn cụ thể, không giảm kiểm thử để PASS.

Kiểm tra MIME/extension giả, ảnh decode lỗi, kích thước/pixel budget trước cấp phát lớn khi đọc header được, path traversal, ZIP filename, XSS qua tên config/file bằng textContent/escape, CSV formula injection, JSON quá lớn, 2 session không lẫn dữ liệu, debug off và lỗi không lộ traceback. Không yêu cầu pentest, auth hay triển khai Internet.

**Input:** bộ ca và giới hạn vận hành. **Output:** bảng hiệu năng/tài nguyên, kết quả Windows/bảo mật cơ bản và limit đã chứng minh.

**DONE checklist:**

- [ ] Có phép đo thật và giới hạn được test tại biên/vượt biên.
- [ ] Chạy 10 lượt liên tiếp không crash; không tăng RAM không giới hạn do giữ session cũ.
- [ ] Không path traversal, XSS/CSV injection hoặc lộ session khác trong các ca đã thử.
- [ ] 0 thao tác xóa file để quản lý dung lượng.

### TASK E.7 — ĐÁNH GIÁ CUỐI THEO FREEZE D

**Mục tiêu:** cung cấp số liệu học thuật cuối độc lập với tuning.

**File/module:** script mới `scripts/run_final_evaluation.py`, DataLoader manifest và module hiện có chỉ đọc; freeze/config D chỉ đọc; output E.

**Cách thực hiện:** xác minh tất cả hash trong freeze, phiên bản config/pipeline/stage, split và group trước chạy. Script nhận `--freeze` và `--output` trỏ thư mục run mới, không cho ghi đè. Dùng DataLoader manifest để lấy đúng final_test, không quét mọi JPG như script cũ. Chạy baseline preset đã khóa và config được chọn từ tuning theo từng màu, cùng ảnh/pipeline/stage, không chọn cấu hình thắng trên final_test để quay lại chỉnh. Lưu mỗi sample/config mask raw/median/morph, ảnh phân đoạn, visualization, năm metrics, TP/TN/FP/FN, status và thời gian; tổng hợp macro theo ảnh và theo màu với số mẫu/độ phân tán min/max/std. Nếu báo micro thì cộng confusion matrix rồi tính lại và ghi tên rõ, không trộn với macro. Báo ảnh tổng hợp riêng nếu dùng kiểm tra hồi quy.

Không định ngưỡng IoU tùy tiện; báo cả thất bại ánh sáng/nền gần màu và giới hạn dữ liệu nhỏ. Các màu chưa có GT thật chỉ được tuyên bố chức năng, không chất lượng học thuật. Re-run để kiểm tra tái lập được phép cùng freeze; lỗi code phải có run/version mới và nêu lý do, không xóa kết quả xấu. Nếu dữ liệu/hash sai, DỪNG nhánh đánh giá và báo về D; phần kiểm thử độc lập vẫn tiếp tục.

**Input:** freeze D và cấu hình đã chọn. **Output:** CSV/JSON cuối, hình và bảng biểu có run ID để F trích dẫn.

**DONE checklist:**

- [ ] 100% final_test approved được chạy, 0 bỏ ảnh lỗi im lặng.
- [ ] Cấu hình không được chọn lại theo final_test; hash/stage/pipeline được ghi.
- [ ] Bảng/biểu đồ truy nguyên đến metrics từng ảnh, không bịa hoặc lọc chỉ ca tốt.

### TASK E.8 — BÁO CÁO, FINAL REVIEW VÀ FINAL FILE INTEGRITY CHECK

**Mục tiêu:** kết luận hệ thống dựa bằng chứng và bàn giao F.

**File/module:** báo cáo E, bug log, ma trận và artifact E.

**Cách thực hiện:** thống kê số test theo tầng riêng, retest lỗi đã sửa và nhóm hồi quy bị ảnh hưởng. Blocker/Critical là crash, sai mask/metrics, lẫn session, hỏng export hoặc chặn luồng bắt buộc; không được còn mở. Minor không ảnh hưởng tiêu chí được ghi rõ, không gọi thiếu chức năng bắt buộc là minor. Đối chiếu Acceptance Criteria và mốc toàn vẹn; ghi file đã sửa, hash dữ liệu/freeze/Excel và HEAD không đổi. Kết luận PASS chỉ khi mọi tiêu chí bắt buộc đã kiểm chứng; E2E chưa chạy không được thay bằng API test.

**Input:** toàn bộ kết quả E. **Output:** báo cáo, trạng thái release nội bộ và danh sách bằng chứng cho F.

**DONE checklist:**

- [ ] Không blocker/critical; tất cả lỗi sửa có retest.
- [ ] Có số PASS/FAIL/SKIP/NOT RUN riêng Unit/Integration/E2E/dữ liệu.
- [ ] Báo cáo và toàn vẹn đầy đủ; không tự sang F.

## 8. KẾ HOẠCH KIỂM THỬ VÀ PHÂN BIỆT CÁC TẦNG

| Tầng | Phạm vi | Trách nhiệm |
|---|---|---|
| Unit Test Phase 2 | HSV/Median/Morphology/Evaluation riêng lẻ | Tái sử dụng và chạy hồi quy, không viết lại suite |
| Test chức năng A/B/C | Palette, manager, compare, morphology controls | Dùng lại bằng chứng và chạy ca bị ảnh hưởng |
| Dữ liệu D | Raw GT, manifest, nguồn/split/hash | E xác minh freeze, không gán nhãn lại |
| Integration E | Flask ↔ modules ↔ session ↔ files/export | E.4, so sánh dữ liệu thật giữa các thành phần |
| End-to-End E | Thao tác trình duyệt tới file tải xuống | E.5, không thay bằng test_client |
| Vận hành E | Windows, tài nguyên, lỗi/bảo mật cơ bản | E.6 |
| Đánh giá cuối E | Final_test cố định | E.7, không tuning |

Ma trận tối thiểu: 8 route gốc và mọi route mới thực có; 15 preset; 4 phép/3 shape qua C test đã có và smoke tích hợp; 3 luồng E2E có GT + không GT + lỗi; export đủ định dạng; session độc lập/hết hạn; validation JSON/HSV/kernel/GT; lỗi decode/413/disk; 10 lượt liên tiếp và hai kích thước benchmark. Mỗi case có expected rõ và artifact; không ghi “test đầy đủ” bằng một số tổng không truy được.

## 9. ACCEPTANCE CRITERIA

| Tiêu chí | Điều kiện đo lường |
|---|---|
| Traceability | 100% yêu cầu bắt buộc và route thực tế có test ID/kết quả |
| Integration | Tất cả ca bắt buộc E.4 PASS; mask bằng module, metrics sai lệch ≤1e-9 |
| Frontend/E2E | 3 luồng có GT + nhánh không GT/lỗi PASS; đủ 15 palette hoạt động |
| Export | PNG decode đúng; JSON/CSV/config khớp run; metrics thiếu GT là N/A |
| Validation/session | Đầu vào sai có 4xx đúng contract; không lẫn session hoặc metrics stale |
| Windows/tài nguyên | Ca tên có dấu/khoảng trắng PASS; 10 lượt không crash; limit/TTL được kiểm tra |
| Hiệu năng | Có số thật, mục tiêu 1 MP đơn ≤5s/3 config ≤15s p95 hoặc blocker + phương án được Hoàn chấp thuận |
| Bảo mật cơ bản | Ca traversal/XSS/CSV injection/traceback đã nêu PASS; demo debug off |
| Đánh giá cuối | 100% sample final_test chạy theo freeze, không điều chỉnh bằng test |
| Kết luận | 0 blocker/critical; không tiêu chí bắt buộc NOT RUN; báo cáo có bằng chứng |
| Toàn vẹn | Dataset/GT/freeze/Excel/HEAD nguyên; 0 file mất hoặc sửa ngoài scope |

## 10. RỦI RO VÀ PHƯƠNG ÁN XỬ LÝ

- Các test cũ có side effect: đọc trước, cô lập output và không gọi script main nguy hiểm; giữ artifact thay vì xóa.
- Kiểm thử UI bị thiếu công cụ: thực hiện API/fixture độc lập, ghi kịch bản thủ công cụ thể; E2E chưa được xác minh vẫn là blocker nghiệm thu.
- Thiếu export: E.2 bổ sung một đường tối thiểu dùng chung B, không làm hệ thống quản lý báo cáo.
- Dataset/freeze lỗi: ghi hash/sample, chuyển sửa về D theo yêu cầu Hoàn; không âm thầm chỉnh trong E.
- RAM/disk tăng: giới hạn admission, TTL trong RAM và cảnh báo dung lượng; không tự xóa file người dùng.
- Điểm test thấp: báo nguyên nhân/ảnh thất bại; không quay lại chọn ngưỡng theo final_test hoặc sửa GT để tăng điểm.

## 11. DEPENDENCIES

```text
A → B → C → D → E → F
A/B/C cung cấp chức năng; D cung cấp dữ liệu/config đã khóa
E cung cấp nghiệm thu tích hợp/E2E, export hoàn chỉnh và số liệu cuối
F chỉ sử dụng artifact đã xác minh để viết báo cáo, slide và demo
```

E không viết lại Unit Test Phase 2, không làm lại D hoặc manager/ranking B. Báo cáo E là nguồn nghiệm thu hệ thống; F liên kết nguồn này, không copy thành một lượt test mới.

## 12. BÁO CÁO ĐẦU RA

`docs/REPORT/PHASE-E-SYSTEM-TEST-REPORT.md`: môi trường/lệnh/run ID; ma trận requirements/API; kết quả theo tầng; bug log trước/sau và retest; thay đổi tối thiểu; E2E/screenshots; export round-trip; Windows/performance/security; kết quả final_test với freeze; giới hạn; Acceptance Criteria; Final File Integrity Check; trạng thái PASS/FAIL/PARTIAL/NOT VERIFIED.

## 13. FINAL REVIEW

- [ ] TASK E.1–E.8 hoàn thành và có bằng chứng.
- [ ] Luồng người dùng hoạt động, export đủ, không metrics stale.
- [ ] Kết quả test cuối độc lập tuning, dữ liệu không bị sửa.
- [ ] Không lỗi nghiêm trọng và không thiếu kiểm chứng bắt buộc.
- [ ] Báo cáo/toàn vẹn hoàn tất.

## 14. STOP RULE

**DỪNG** sau báo cáo/review; không commit/push, không tự viết báo cáo F. Chức năng bắt buộc thiếu lớn hoặc cần sửa ngoài allowlist phải báo scope cụ thể. Dữ liệu/thuật toán sai trả đúng Phase phụ trách, không mở rộng E âm thầm.

## 15. TỔNG KẾT PHASE VÀ THỨ TỰ THỰC HIỆN

E.1 Audit → E.2 Export tối thiểu → E.3 Validation/session → E.4 Integration → E.5 E2E → E.6 Windows/tài nguyên/hiệu năng → E.7 Đánh giá cuối → E.8 Báo cáo/review/toàn vẹn → DỪNG. F nhận bằng chứng đã khóa, không phải danh sách việc kiểm thử còn bỏ ngỏ.
