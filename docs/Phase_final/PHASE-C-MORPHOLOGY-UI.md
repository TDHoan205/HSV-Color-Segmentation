# PHASE C — HOÀN THIỆN GIAO DIỆN MORPHOLOGY

## 1. MỤC TIÊU PHASE

Đưa Erosion, Dilation, Opening, Closing, Kernel Shape, Kernel Size và Iterations lên Web; hiển thị trước/sau; đồng bộ giá trị hiển thị, payload, cấu hình Backend thực dùng và snapshot so sánh B. Tận dụng `src/morphology.py`, không viết lại thuật toán đúng.

Tài liệu là prompt triển khai tương lai. Hiện trạng được đọc ngày 16/11/2026, phải xác minh lại trước sửa.

## 2. SƠ ĐỒ QUY TRÌNH THỰC HIỆN

```text
Audit source và báo cáo A/B → Khóa contract Morphology
→ Controls + validation → Adapter Backend dùng MorphologyOperator
→ Hiển thị trước/sau → Đồng bộ fixed_pipeline của B
→ Kiểm thử riêng C → Báo cáo → Final Review/toàn vẹn → DỪNG
```

Pipeline giữ nguyên: ảnh BGR → HSV → mask_raw → Median → mask_median → Morphology theo thứ tự → mask_morph → Evaluation tùy chọn. “Trước Morphology” luôn là `mask_median`, không nhầm với ảnh gốc hoặc mask raw.

## 3. ĐẦU RA BẮT BUỘC

- Controls cho đủ bốn phép toán; bật/tắt từng phép, thứ tự áp dụng hiển thị rõ.
- Rectangle (`rect`), Ellipse (`ellipse`), Cross (`cross`); kernel lẻ 1–31; iterations nguyên 1–10 cho mỗi bước.
- Nút áp dụng và hiển thị mask trước/sau cùng kích thước; trạng thái kết quả cũ khi đổi thông số.
- Payload chuẩn, validation hai phía, thông báo lỗi 4xx với đầu vào sai; đường tương thích request cũ.
- B sử dụng được pipeline mới mà vẫn giữ các tham số cố định giữa các HSV configs.
- `tests/test_phase_c_morphology_api.py` và `docs/REPORT/PHASE-C-IMPLEMENTATION-REPORT.md`.

## 4. NGUYÊN TẮC TRIỂN KHAI

```text
Implementation Owner: Hoàn
Tool Support: Cursor Agent
Excel: Academic Learning Reference
Team Dependency: NONE
```

Hoàn tự triển khai; Excel chỉ học tập, không phân công lập trình, không chờ người khác.

### MASTER SCOPE LOCK

- Tuyệt đối không xóa file/thư mục; không rename, move, tái cấu trúc. Không xóa code, hàm, class hoặc chức năng cũ.
- Không ghi đè code/dữ liệu ngoài phạm vi; giữ nguyên thay đổi sẵn có của người dùng. Chỉ sửa file trực tiếp liên quan trong allowlist.
- Không sửa Dataset, Ground Truth hoặc Excel; thay đổi dữ liệu chỉ thuộc D khi thực sự cần. Upload/test nằm vùng riêng.
- Không sửa tài liệu các Phase khác. Không commit, push hoặc thay đổi Git history nếu chưa được yêu cầu.
- Trước sửa: Git Status, HEAD, danh sách dự kiến thay đổi, hash và danh mục file hiện có kể cả untracked/ignored liên quan.
- Cần file ngoài danh sách hoặc thay thuật toán: DỪNG, báo lý do/tác động, không tự mở scope.
- Final File Integrity Check bắt buộc: đối chiếu trước/sau; 0 file bị mất/rename/move, 0 sửa ngoài phạm vi, dữ liệu/GT/Excel nguyên hash, HEAD không đổi; kiểm tra cả file không được Git theo dõi.
- Kết quả lưu theo ID mới, không ghi đè hoặc tự xóa artifact để dọn dẹp.

### HIỆN TRẠNG LÀM CĂN CỨ

| Thành phần | Trạng thái đọc được | Hành động C |
|---|---|---|
| `MorphologyOperator` | `erode`, `dilate`, `open`, `close`, `apply_sequence`; 3 shape | Gọi lại các hàm hiện có |
| `main.py` | shape cố định ellipse, iterations=1, Closing rồi Opening | Mở tham số bằng adapter, giữ nhánh cũ |
| `index.html`/`app.js` | kernel 3/5/7/9 và hai checkbox | Bổ sung controls, không viết lại trang |
| Tests module | Có `tests/test_morphology.py`; báo cáo A ghi 66 test PASS | Chạy hồi quy cần thiết, không viết lại unit suite |
| Kết quả cuối | UI đang gọi mask cuối là “kết quả tốt nhất” | Sửa nhãn thành “sau Morphology”; không đảm bảo luôn tốt hơn |

Module hỗ trợ thêm gradient/tophat/blackhat nhưng không bắt buộc mở UI trong C. Giới hạn kernel/iterations ở đây là giới hạn Web đề xuất để bảo vệ tài nguyên; không tuyên bố module hiện đã áp các giới hạn này.

## 5. ĐIỀU KIỆN BẮT ĐẦU

- Đọc `main.py`, `src/morphology.py`, `src/median_filter.py`, Frontend, `module_contracts.md`, test morphology và báo cáo A/B nếu đã có.
- Xác minh chức năng A và contract fixed_pipeline của B đã có bằng chứng, không dựa vào tên tài liệu. Nếu B chưa triển khai thì đánh dấu `[DEPENDENCY — PHASE B CONTRACT]`, không tự xây lại B.
- Xác định thứ tự morphology đang chạy, defaults và nơi lưu applied_config trong B.
- Có fixture riêng chứa vùng trắng, lỗ đen, điểm nhiễu và chi tiết mảnh; không cần đổi Dataset hoặc chờ D.

## 6. PHẠM VI CHỈ LÀM VÀ KHÔNG ĐƯỢC LÀM

**CHỈ LÀM:** controls bốn phép, shape/size/iterations, contract request, adapter Backend, trước/sau, nối vào B, kiểm thử riêng C và báo cáo.

**KHÔNG ĐƯỢC LÀM:** viết lại Morphology/Median/HSV/Evaluation, morphology tự thích nghi, mở thêm thuật toán nâng cao, sửa nhãn hoặc dataset, làm lại manager/ranking/export B, export toàn hệ thống E, viết báo cáo F.

Allowlist: `main.py`, `templates/index.html`, `static/js/app.js`, `static/css/style.css`, test mới `tests/test_phase_c_morphology_api.py`, báo cáo C, artifact mới `results/phase_c/<run_id>/`. `src/morphology.py` mặc định chỉ đọc; nếu phát hiện bug thật phải báo phạm vi trước sửa.

## 7. CÁC TASK TRIỂN KHAI

### TASK C.1 — AUDIT VÀ CHỐT CONTRACT

**Mục tiêu:** có một cách biểu diễn pipeline dùng chung giữa xử lý đơn và so sánh.

**File/module:** `main.py`, `app.js`, `index.html`, `src/morphology.py`, báo cáo B; module thuật toán chỉ đọc.

**Cách thực hiện:** ghi defaults thực tế; chốt object `morphology` gồm `kernel_size`, `kernel_shape`, `operations`. Mỗi operation có `operation` trong erode/dilate/open/close và `iterations`; danh sách rỗng = bỏ qua morphology. UI dùng bốn checkbox theo thứ tự cố định **close → open → erode → dilate**, mỗi phép một lần, iterations riêng. Hiển thị chuỗi thực tế, không dùng một nhãn chung mơ hồ. API giữ nguyên thứ tự danh sách được gửi, tối đa bốn operation, không trùng; UI không cần drag/drop. Defaults mới vẫn ellipse, size 5, close một lần. Median giữ default riêng 5 và quy tắc 3–31 của module.

**Input:** source hiện tại và contract B. **Output:** schema, mapping UI/API và allowlist trong báo cáo C.

**DONE checklist:**

- [ ] Defaults, thứ tự cũ và mới được ghi chính xác.
- [ ] Một object morphology phục vụ cả xử lý đơn và B.
- [ ] Không thay thuật toán hoặc defaults ngầm.

### TASK C.2 — CONTROLS VÀ VALIDATION FRONTEND

**Mục tiêu:** người dùng thao tác đủ chức năng và nhìn rõ giá trị có hiệu lực.

**File/module:** `index.html`, `app.js`, `style.css`.

**Cách thực hiện:** giữ checkbox Closing/Opening và ID cũ; bổ sung Erosion/Dilation, select shape, input kernel số lẻ 1–31, input iterations 1–10 cho mỗi phép. Checkbox tắt thì iterations bị disable và không đưa vào operations. Có nút áp dụng tại tab Morphology gọi pipeline đang có; chưa upload ảnh thì báo lỗi rõ. Khi thay controls chỉ đánh dấu “chưa áp dụng”, không tự chạy liên tục. Tên “Rectangle” gửi `rect`; mô tả Open là co rồi nở, Close là nở rồi co, kernel 1 có thể là phép đồng nhất.

**Input:** thao tác người dùng. **Output:** object morphology hợp lệ và trạng thái đã/chưa áp dụng.

**DONE checklist:**

- [ ] Đủ 4 phép, 3 shape, size và iterations riêng.
- [ ] Min/max/step và giá trị hiển thị khớp payload số nguyên.
- [ ] Có thông báo tại controls, không chỉ lỗi console.

### TASK C.3 — ADAPTER BACKEND VÀ TƯƠNG THÍCH

**Mục tiêu:** Backend áp đúng cấu hình, không âm thầm sửa đầu vào mới.

**File/module:** `main.py`; gọi `MorphologyOperator.set_kernel/apply_sequence` sẵn có.

**Cách thực hiện:** nếu có `morphology`, validate object và mọi trường trước xử lý; `type(value)` phải là int, từ chối bool/float/string trong schema mới, null, shape lạ, operation lạ, trùng operation, size chẵn/ngoài 1–31, iterations ngoài 1–10. Không tự cộng 1 cho size chẵn ở nhánh mới. Tạo operator một lần, chuyển danh sách sang tuples của module, chạy trên bản copy `mask_median`. `operations=[]` trả copy tương đương mask trước. Trả applied_config thực dùng trong response, giữ các key mask cũ.

Nếu request không có object mới, đọc `morph_kernel/use_closing/use_opening` như đường cũ và giữ thứ tự Closing→Opening, ellipse, iteration 1. Nếu gửi cả hai, object mới được ưu tiên; response ghi rõ nhánh và cảnh báo legacy fields bị bỏ qua. Không xóa nhánh cũ, không đổi chữ ký module. Lỗi tham số trả 400 JSON; session không tồn tại giữ contract hiện hữu; lỗi ngoài dự kiến mới là 500.

**Input:** payload mới hoặc payload cũ. **Output:** mask_morph, applied_config, lỗi xác định.

**DONE checklist:**

- [ ] Kết quả API bằng gọi trực tiếp module với cùng tham số từng pixel.
- [ ] Nhánh mới từ chối giá trị sai, không tự điều chỉnh.
- [ ] Request cũ cho kết quả như baseline, các key response cũ còn nguyên.

### TASK C.4 — HIỂN THỊ TRƯỚC/SAU VÀ TRẠNG THÁI KẾT QUẢ

**Mục tiêu:** nhìn được tác dụng morphology trên cùng mask đầu vào.

**File/module:** `app.js`, `index.html`, `style.css`, response `main.py`.

**Cách thực hiện:** đặt mask_median bên trái, mask_morph bên phải, cùng tỷ lệ và tên đầy đủ; ghi shape, size, chuỗi phép toán/iterations thực áp dụng từ response. Có số pixel trắng trước/sau nhưng không gọi đó là chất lượng. Thay đổi ảnh/HSV/median/morphology làm kết quả và metrics cũ mất hiệu lực; hiển thị stale và yêu cầu xử lý/đánh giá lại. Không dùng metrics của mask trước cho mask mới. Bất kỳ lỗi nào không được thay mask hợp lệ bằng hình rỗng mà thiếu thông báo.

**Input:** response xử lý và các sự kiện đổi controls. **Output:** cặp mask và thông tin nhất quán.

**DONE checklist:**

- [ ] Nhãn “trước” là median, “sau” là morph, size H×W không đổi.
- [ ] Không gọi mask cuối là tốt nhất mặc định.
- [ ] Đổi thông số không giữ metrics cũ như kết quả hiện tại.

### TASK C.5 — ĐỒNG BỘ VỚI SO SÁNH B

**Mục tiêu:** mở controls không làm phép so ngưỡng mất công bằng.

**File/module:** adapter/payload trong `main.py` và `app.js` đã tạo ở B.

**Cách thực hiện:** dùng cùng builder/validator morphology cho process và compare. Snapshot toàn bộ object mới vào `fixed_pipeline.morphology`; chỉ một bản chung cho tất cả configurations. Đổi controls sau lượt chạy đánh dấu stale, lượt chạy mới có ID mới; export B tự ghi object đã áp dụng qua schema có sẵn. Các gói B cũ thiếu trường mới được đọc với defaults của phiên bản cũ, không áp defaults hiện tại rồi gọi là tái lập. Không thay ranking hoặc tạo export mới.

**Input:** fixed_pipeline B và controls C. **Output:** so sánh B hoạt động với đủ bốn phép/ba shape.

**DONE checklist:**

- [ ] Mọi config trong một lượt có morphology giống nhau hoàn toàn.
- [ ] Process và compare cho cùng mask khi HSV/pipeline/ảnh giống nhau.
- [ ] Import gói B cũ có xử lý phiên bản rõ ràng.

### TASK C.6 — KIỂM THỬ VÀ BÁO CÁO C

**Mục tiêu:** xác minh kết nối controls với module, không lặp unit thuật toán Phase 2.

**File/module:** `tests/test_phase_c_morphology_api.py`, test hồi quy morphology/A/B cần thiết, báo cáo C.

**Cách thực hiện:** thực hiện ma trận mục 8. Fixture tạo riêng, không ghi `data/`; patch upload/session/results, kiểm tra side effect trước chạy. Tận dụng expected từ module và fixture đã có để kiểm tra adapter; không sao chép 66 unit test. Ghi kết quả riêng mới chạy, log, ảnh trước/sau, payload/applied_config. Không dùng metrics cao hơn làm điều kiện bắt buộc cho mọi phép: erosion có thể làm mất chi tiết là hành vi cần giải thích.

**Input:** chức năng C. **Output:** test, bằng chứng UI/API và báo cáo.

**DONE checklist:**

- [ ] Có số PASS/FAIL/SKIP/NOT RUN và lý do.
- [ ] Đủ đường mới, legacy, bypass và invalid parameters.
- [ ] B không mất tính công bằng và khả năng tái lập.

### TASK C.7 — FINAL REVIEW VÀ FINAL FILE INTEGRITY CHECK

**Mục tiêu:** đóng Phase với thay đổi tối thiểu.

**File/module:** allowlist và báo cáo C.

**Cách thực hiện:** kiểm từng tiêu chí mục 9, đối chiếu hash/danh mục/Git/HEAD trước sau; kiểm tra không xóa code cũ, không sửa `src/morphology.py` hoặc dataset ngoài phép. Ghi mọi thay đổi có sẵn không thuộc C và giới hạn chưa kiểm chứng, không tự nhận chúng là kết quả C.

**Input:** test và diff cuối. **Output:** bảng review có trạng thái và chứng cứ toàn vẹn.

**DONE checklist:**

- [ ] Tất cả tiêu chí bắt buộc có bằng chứng.
- [ ] 0 file mất/rename/move và 0 sửa ngoài allowlist.
- [ ] Báo cáo hoàn chỉnh, không tự chuyển D.

## 8. KẾ HOẠCH KIỂM THỬ

| Mã | Ca | Kỳ vọng |
|---|---|---|
| C-T01 | 4 phép × 3 shape, kernel 3, iterations 1 | 12 ca API bằng module từng pixel |
| C-T02 | Kernel 1, 5, 31; iterations 1, 2, 10 | Đúng applied_config, mask nhị phân cùng size |
| C-T03 | Không phép nào; Close→Open; 4 phép | Bypass đúng, thứ tự thực thi đúng |
| C-T04 | Shape/operation lạ, kernel 0/2/32, iterations 0/11, float/bool/null | 400, lỗi rõ trường, không mutate session kết quả |
| C-T05 | Request legacy Closing/Opening | Bằng baseline trước sửa |
| C-T06 | Chỉnh UI rồi áp dụng; reset/đổi ảnh | Controls, payload, response khớp; kết quả cũ được đánh dấu |
| C-T07 | So sánh B với pipeline mới và import cũ | Cố định tham số, tái lập được theo phiên bản |
| C-T08 | Mask nhỏ/chi tiết mảnh, nhiều phép liên tiếp | Không crash; giải thích được thay đổi viền |

Kernel/iterations lớn kiểm tra trên fixture nhỏ để kiểm chứng contract; E đo hiệu năng trên ảnh thật. E không viết lại ma trận unit, chỉ kiểm tra C trong luồng toàn ứng dụng.

## 9. ACCEPTANCE CRITERIA

| Tiêu chí | Điều kiện đạt đo lường được |
|---|---|
| Độ phủ controls | 4 phép + 3 shape + size + iterations đều chọn và áp dụng được |
| Tính đúng adapter | 12/12 tổ hợp C-T01 giống module từng pixel |
| Validation | 100% ca sai C-T04 trả 4xx rõ ràng, không âm thầm sửa giá trị mới |
| Trước/sau | Hai mask cùng H×W, uint8, chỉ 0/255; nhãn và config đúng |
| Tương thích | C-T05 giữ kết quả cũ; không mất chức năng A/B |
| Công bằng B | Một fixed_pipeline cho toàn lượt, snapshot đúng object mới |
| Trạng thái | Không dùng metrics cũ sau khi mask/config đổi |
| Toàn vẹn | Không sửa thuật toán đang đúng; 0 file mất/ngoài scope; HEAD không đổi |

Không còn lỗi nghiêm trọng bắt buộc; mỗi hàng ghi PASS/FAIL/PARTIAL/NOT VERIFIED và liên kết bằng chứng. Có hàng chưa xác minh thì chưa tuyên bố C DONE.

## 10. RỦI RO VÀ PHƯƠNG ÁN XỬ LÝ

- Bốn phép dùng liên tiếp có thể triệt tiêu hoặc phá chi tiết: chuỗi áp dụng luôn hiển thị, mặc định giữ close 1; giải thích tác dụng chứ không tự tối ưu.
- Frontend chỉ cấm nhập nhưng API nhận sai: validator Backend bắt buộc và test payload trực tiếp.
- Kernel chẵn bị cộng 1 theo đường cũ: nhánh mới từ chối rõ ràng, legacy tách biệt và ghi config thực dùng.
- Response cũ về muộn: gắn request ID, chỉ hiển thị kết quả đúng lượt hiện tại.
- Phát hiện bug thuật toán thật: ghi bằng chứng tối thiểu, DỪNG xin scope điều chỉnh thay vì viết lại module.

## 11. DEPENDENCIES

```text
A → B → C → D → E → F
B cung cấp fixed_pipeline + lưu/chạy lại
C cung cấp object morphology thống nhất cho xử lý đơn và B
D cung cấp GT hợp lệ; C không phụ thuộc GT để hoàn thiện controls
E xác minh xuyên Phase; F giải thích và trình bày bằng chứng
```

C không làm lại manager, ranking hoặc export B. D hiệu chỉnh HSV bằng công cụ B sau khi pipeline C đã khóa. E kiểm thử tích hợp và export toàn ứng dụng; F không sửa lỗi chức năng trong khi viết báo cáo.

## 12. BÁO CÁO ĐẦU RA

`docs/REPORT/PHASE-C-IMPLEMENTATION-REPORT.md`: hiện trạng; file thay đổi; controls và schema; defaults/legacy mapping; ma trận 12 ca và lỗi; ảnh trước/sau; bằng chứng B vẫn công bằng; số test; giới hạn; Acceptance Criteria; Final File Integrity Check. Không ghi lại báo cáo A/B hoặc chép kết quả cũ thành test mới.

## 13. FINAL REVIEW

- [ ] TASK C.1–C.7 DONE có chứng cứ.
- [ ] Người dùng thao tác được toàn bộ chức năng bắt buộc.
- [ ] Thuật toán cũ được tái sử dụng, defaults và nhánh cũ được giữ.
- [ ] Báo cáo và toàn vẹn hoàn tất.

## 14. STOP RULE

**DỪNG** sau review và báo cáo. Không commit/push, không tự chuẩn hóa dữ liệu hoặc chuyển D. Nếu có blocker ngoài phạm vi, nêu file/hành vi/bằng chứng và thay đổi tối thiểu cần thiết; chờ Hoàn yêu cầu bước tiếp theo.

## 15. TỔNG KẾT PHASE VÀ THỨ TỰ THỰC HIỆN

C.1 Contract → C.2 Controls → C.3 Backend adapter → C.4 Trước/sau → C.5 Nối B → C.6 Kiểm thử/báo cáo → C.7 Review/toàn vẹn → DỪNG. Kết quả C là một giao diện phản ánh đúng module Morphology và pipeline đã áp dụng.
