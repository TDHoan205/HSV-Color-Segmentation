# PHASE D — HOÀN THIỆN DATASET VÀ GROUND TRUTH

## 1. MỤC TIÊU PHASE

Xây bộ dữ liệu ảnh thực tế có nguồn rõ, nhãn độc lập, ghép cặp chính xác và split không rò rỉ, đủ để điều chỉnh cấu hình trên tuning và đánh giá cuối ở E. Giữ nguyên dữ liệu cũ, phân biệt ảnh tổng hợp, ảnh thật có nhãn, ảnh chờ nhãn và ảnh không đủ điều kiện học thuật.

Tài liệu này hướng dẫn triển khai tương lai. Không suy ra dữ liệu đã tốt chỉ vì có file GT hoặc báo cáo cũ nói DONE.

## 2. SƠ ĐỒ QUY TRÌNH THỰC HIỆN

```text
Git Status + hash + audit toàn bộ ảnh/GT/metadata
→ Phân loại hợp lệ/thiếu nhãn/nguồn chưa rõ/trùng/lỗi
→ Chốt quy tắc vùng mục tiêu và manifest
→ Tìm ảnh có quyền sử dụng hoặc tự chụp
→ Vẽ nhãn độc lập + tự kiểm tra lần hai
→ Kiểm tra raw file + ghép cặp + DataLoader
→ Chia tuning/final_test theo nhóm cảnh
→ Chọn cấu hình chỉ trên tuning qua B, pipeline C cố định
→ Khóa hash dữ liệu/cấu hình → Báo cáo → Review/toàn vẹn → DỪNG
```

## 3. ĐẦU RA BẮT BUỘC

- Kiểm kê 100% ảnh/GT hiện có, kể cả file không hợp lệ và ảnh thiếu nhãn; không xóa hay di chuyển file để làm đẹp thống kê.
- `data/dataset_manifest.csv`, `data/dataset_sources.json`, `data/annotation_policy.md`, `data/dataset_freeze.json` với schema và phiên bản rõ ràng.
- Tối thiểu **20 cặp ảnh thật được duyệt**, ít nhất 5 màu mục tiêu, ít nhất 5 nhóm tình huống và tối thiểu 8 ảnh final_test; đây là mục tiêu nghiệm thu mới của roadmap, không phải số liệu đã có hoặc yêu cầu mặc định của đề bài.
- Bộ 10 cặp tổng hợp cũ giữ riêng về mặt manifest, không gọi là ảnh chụp thật hoặc dùng thay bằng chứng thực tế.
- Toàn bộ ảnh chưa vào bộ đánh giá có trạng thái, lý do, bước xử lý và mức ưu tiên cụ thể; không còn bản ghi bị bỏ quên.
- DataLoader đọc được toàn bộ tập được duyệt, test theo contract mới, báo cáo `docs/REPORT/PHASE-D-DATASET-REPORT.md` và artifact audit/tuning phiên bản mới.

## 4. NGUYÊN TẮC TRIỂN KHAI

```text
Implementation Owner: Hoàn
Tool Support: Cursor Agent
Excel: Academic Learning Reference
Team Dependency: NONE
```

Hoàn thực hiện thu thập, gán nhãn, tự review và chạy thực nghiệm; không chờ thành viên khác. Các thành viên còn lại học toàn bộ project ở F. Không đổi Excel thành bảng giao việc mới.

### MASTER SCOPE LOCK

- Tuyệt đối không xóa file/thư mục; không rename/move hoặc tái cấu trúc project. Không xóa code, hàm, class hoặc chức năng cũ.
- Chỉ thay file trực tiếp liên quan đã ghi allowlist sau Git Status; không ghi đè code/dữ liệu ngoài scope. Giữ nguyên thay đổi sẵn có của người dùng.
- D là Phase duy nhất được bổ sung/chuẩn hóa Dataset và Ground Truth khi cần. Vẫn không sửa Excel. Ưu tiên file bổ sung có phiên bản, giữ byte ảnh/GT gốc; nhãn sửa lưu đường dẫn mới trong manifest, không đè nhãn cũ.
- Không sửa tài liệu các Phase khác; không commit, push hoặc thay đổi Git history nếu chưa được yêu cầu.
- Trước sửa: ghi HEAD, Git Status, danh mục và hash ảnh/GT/metadata/Excel/code, kể cả file untracked/ignored; nêu danh sách file dự kiến thay đổi.
- Cần ngoài allowlist, sửa thuật toán, hoặc phải thay file gốc: DỪNG và báo lý do/tác động/phương án giữ nguyên bản gốc.
- Final File Integrity Check: đối chiếu trước/sau, không mất file/rename/move; file gốc ngoài allowlist nguyên hash, dữ liệu gốc được giữ, Excel và HEAD không đổi. Liệt kê mọi file mới và file được chỉnh hợp lệ; Git diff không thay kiểm tra untracked/ignored.
- Không tự chạy script sinh lại dataset, không tự dọn/xóa vùng tạm hoặc kết quả cũ. Artifact mới luôn dùng run ID mới.

### HIỆN TRẠNG ĐÃ XÁC MINH NGÀY 16/11/2026

| Hạng mục | Kết quả đọc/kiểm tra chỉ đọc | Giới hạn kết luận |
|---|---|---|
| Ảnh hiện có | 34 file ảnh | Chưa xác minh quyền sử dụng và nội dung của 24 ảnh không GT |
| GT | 10 PNG ghép theo stem, không GT mồ côi theo stem | Đúng size, một kênh uint8, chỉ 0/255; chưa thay kiểm tra ngữ nghĩa |
| Metadata | 10 dòng trong `data/metadata.csv` | Chưa phủ 24 ảnh còn lại |
| Tổng hợp | `scripts/generate_dataset.py`, `data/README.md`, `report/data.md` mô tả sinh hình học | 10 GT độc lập với HSV, nhưng là dữ liệu tổng hợp |
| Ảnh thiếu GT | 17 tên thời gian và 7 tên apple/ball/eggplant/lemon/orange/pngtree | Tên file không chứng minh tác giả, nội dung thật hoặc giấy phép |
| DataLoader | load GT tự threshold 127; `build_dataset` bỏ ảnh thiếu GT | Không dùng kết quả load thành công để chứng nhận raw GT hợp lệ |
| Test dữ liệu | `TestRealDataset` khóa 8–12 ảnh và target Red | Contract cũ không phù hợp multi-color; phải sửa có căn cứ và giữ kiểm tra bộ tổng hợp |
| Báo cáo A | Ghi 24 ảnh thật chưa GT và 4 FAIL dữ liệu lịch sử | Phải chạy lại để biết số FAIL hiện tại, không chép số cũ thành kết quả mới |

Báo cáo Phase 0/1/2 được nhắc trong lịch sử nhưng hiện không thấy các file tương ứng trong `docs/REPORT/`. Không coi tên Phase hay lời kể là bằng chứng nghiệm thu; dùng source, test và artifact có thể truy nguyên.

## 5. ĐIỀU KIỆN BẮT ĐẦU

- Đọc DataLoader, tests dữ liệu, metadata, tài liệu data, script generator chỉ đọc, module contracts, báo cáo A và báo cáo B/C thực tế.
- B đã có khả năng so sánh/lưu cấu hình, C đã khóa pipeline; audit lại bằng code và bằng chứng, không mặc định hoàn thành.
- Chốt mục tiêu nhãn theo **màu**: foreground là toàn bộ vùng nhìn thấy của nhóm màu mục tiêu theo chính sách gán nhãn; không biến đề tài thành instance segmentation hoặc nhận diện vật thể.
- Có công cụ gán nhãn thủ công xuất PNG một kênh, ví dụ LabelMe/CVAT chạy cục bộ hoặc trình biên tập ảnh phù hợp. Chọn một công cụ đơn giản; không cần dựng nền tảng annotation nhiều người.

## 6. PHẠM VI CHỈ LÀM VÀ KHÔNG ĐƯỢC LÀM

**CHỈ LÀM:** audit dữ liệu, truy nguồn/giấy phép, thu thập ảnh phù hợp, gán nhãn độc lập, manifest/split/freeze, adapter DataLoader tối thiểu, cập nhật test contract dữ liệu, tuning qua B và khóa cấu hình.

**KHÔNG ĐƯỢC LÀM:** dùng HSV dự đoán làm GT; tạo/đổi số liệu cho đẹp; bịa giấy phép hoặc tác giả; xóa/di chuyển ảnh thiếu nhãn; sửa preset toàn cục A; tối ưu AI; sửa UI/API hoặc export hệ thống; đo final_test để quay lại chỉnh ngưỡng; viết báo cáo F.

Allowlist dự kiến: file mới `data/dataset_manifest.csv`, `data/dataset_sources.json`, `data/annotation_policy.md`, `data/dataset_freeze.json`; ảnh mới trong `data/images/`, GT mới trong `data/ground_truth/` có tên không trùng; các nhãn nhiều màu/sửa đổi đặt trong thư mục bổ sung `data/ground_truth/annotations_v1/`; `data/README.md`, `src/data_loader.py`, `tests/test_data.py`, script mới `scripts/audit_dataset.py`, báo cáo D và `results/phase_d/<run_id>/`. Giữ nguyên `data/metadata.csv` theo schema cũ và bổ sung manifest thay vì viết lại lịch sử. Khai báo chính xác tên ảnh/nhãn mới sau audit trước khi ghi.

## 7. CÁC TASK TRIỂN KHAI

### TASK D.1 — KIỂM KÊ ẢNH, GT VÀ CẶP DỮ LIỆU

**Mục tiêu:** có danh sách đầy đủ, không bị `build_dataset` che mất ảnh thiếu GT.

**File/module:** `data/images/`, `data/ground_truth/`, metadata, `src/data_loader.py`, script audit mới; đọc generator và báo cáo data.

**Cách thực hiện:** duyệt mọi file, tính SHA-256, decode ảnh và raw GT bằng IMREAD_UNCHANGED; thống kê ảnh hỏng, sai số kênh/dtype, dimensions, GT thiếu, GT mồ côi, stem va chạm nhiều extension, giá trị nhãn lạ, duplicate hash và nhóm near-duplicate cần xem thủ công. Đối chiếu cả đường dẫn manifest và metadata, không chỉ `extract_image_id` vì tên thời gian có thể trùng ID suy diễn. Xuất bảng một dòng cho mỗi file và một bảng cặp, trạng thái kỹ thuật tách khỏi ngữ nghĩa/nguồn. Không resize hoặc threshold để “sửa” trong audit.

**Input:** dữ liệu gốc. **Output:** inventory JSON/CSV mới trong results D, số liệu thật và danh sách việc thiếu.

**DONE checklist:**

- [ ] 100% file có hash/trạng thái, tổng nhóm cộng khớp tổng file.
- [ ] Có missing_gt, orphan_gt, invalid_pair, duplicate và metadata coverage.
- [ ] Không thay byte file gốc, không bỏ qua im lặng.

### TASK D.2 — QUY TẮC GÁN NHÃN VÀ SCHEMA MANIFEST

**Mục tiêu:** mỗi nhãn có ý nghĩa nhất quán và truy nguyên được.

**File/module:** `data/annotation_policy.md`, `data/dataset_manifest.csv`, `data/dataset_sources.json`, `data/README.md`.

**Cách thực hiện:** quy định foreground=255 cho vùng màu mục tiêu nhìn thấy, nền=0; chọn toàn bộ vùng cùng màu trong ảnh thay vì chỉ một vật thể tên cụ thể. Quy định rìa chống răng cưa được vẽ thành đường biên nhị phân, bóng đổ/đốm phản sáng xử lý theo ngữ nghĩa màu quan sát được và chính sách đã ghi; ảnh quá mơ hồ loại khỏi tập định lượng với lý do. Không dùng giới hạn H/S/V của chương trình để quyết định nhãn. Với White/Black/Gray mô tả ví dụ ranh giới bằng mắt, không bê preset làm định nghĩa GT. Không auto-fill vùng khó bằng mask HSV.

Manifest một dòng cho một cặp ảnh–màu mục tiêu, `sample_id` duy nhất; một ảnh có thể có nhiều màu và GT khác nhau, cùng `image_id/group_id/split`. Các cột bắt buộc: `schema_version`, `sample_id`, `image_id`, `image_path`, `gt_path` nullable, `target_color_id`, `data_type` (synthetic/real), `source_id`, `license_status`, `annotation_method`, `annotation_version`, `annotator`, `review_status`, `review_note`, `width`, `height`, `image_sha256`, `gt_sha256`, `scenario`, `lighting`, `background`, `group_id`, `split`, `status`, `exclusion_reason`, `next_action`. `status` gồm approved/pending_annotation/invalid/excluded; `split` tuning/final_test/synthetic_reference/none. Không có GT thì gt_path/hash rỗng và split none; không giả đường dẫn. Dùng đường dẫn tương đối, không cho traversal ngoài project.

**Input:** inventory và 15 color IDs A. **Output:** chính sách và manifest schema có bản ghi ban đầu.

**DONE checklist:**

- [ ] Không dùng HSV dự đoán trong chính sách gán nhãn.
- [ ] Mọi file ảnh hiện có được manifest tham chiếu ít nhất một bản ghi kiểm kê phù hợp.
- [ ] Schema hỗ trợ ảnh thiếu nhãn và nhiều màu mà không đổi tên ảnh cũ.

### TASK D.3 — NGUỒN ẢNH, GIẤY PHÉP VÀ XỬ LÝ THIẾU DỮ LIỆU

**Mục tiêu:** chủ động bổ sung đủ bộ dữ liệu thật có thể dùng và chia sẻ hợp lệ.

**File/module:** `dataset_sources.json`, manifest; ảnh bổ sung mới trong `data/images/`.

**Cách thực hiện:** với 24 ảnh không GT, xem nội dung, khả năng gán nhãn và truy nguồn. Không coi timestamp là bằng chứng Hoàn chụp, không suy đoán giấy phép từ tên pngtree. Nguồn ghi URL trang ảnh gốc, tác giả, tên giấy phép/URL, ngày truy cập, attribution yêu cầu, quyền phân phối, hash. Ảnh tự chụp ghi người chụp/ngày và quyền sử dụng được xác nhận; chưa biết ghi unknown và không vào tập công bố.

Thứ tự xử lý cụ thể: (1) ưu tiên ảnh hiện có có nguồn/quyền rõ, gán nhãn D.4; (2) ảnh nguồn unknown tiếp tục truy nguồn trong thời gian có giới hạn, giữ pending; (3) không xác minh được thì giữ nguyên file nhưng excluded khỏi bộ định lượng/công bố; (4) Hoàn/Cursor tìm ảnh thực tế CC0/CC BY hoặc bộ có segmentation annotation cùng quyền sử dụng, lưu bằng chứng giấy phép trước tải; (5) không có nguồn phù hợp thì Hoàn tự chụp vật dụng có sẵn ở nền sáng/tối, ánh sáng thường/yếu và nền gần màu, không cần người khác. Agent thực hiện audit, truy nguồn và chuẩn bị hàng đợi annotation; thao tác chụp/vẽ không thể tự thực hiện phải ghi yêu cầu thao tác cụ thể theo ảnh, tiếp tục các công việc độc lập khác, không kết thúc Phase là DONE.

Mục tiêu 20 cặp thật, ≥5 màu và ≥5 tình huống được kiểm tra trước freeze. Không bắt buộc tìm đủ dữ liệu học thuật cho cả 15 preset: phải ghi ma trận màu nào đã/chưa được kiểm chứng; 15 màu vẫn có kiểm thử chức năng A/B/E. Không dùng một cảnh chụp 20 lần để giả đa dạng.

**Input:** danh sách thiếu nhãn/nguồn và khoảng thiếu theo màu/tình huống. **Output:** source registry, ảnh mới nếu cần và kế hoạch xử lý cụ thể từng ảnh.

**DONE checklist:**

- [ ] Mỗi ảnh approved có bằng chứng nguồn/quyền sử dụng.
- [ ] Mỗi ảnh chưa approved có lý do và hành động tiếp theo, không bị xóa.
- [ ] Đã chủ động xử lý nguồn/annotation, không chỉ yêu cầu cung cấp toàn bộ dataset rồi dừng.

### TASK D.4 — GÁN NHÃN ĐỘC LẬP VÀ TỰ REVIEW LẦN HAI

**Mục tiêu:** tạo GT ảnh thật đáng tin cậy, không rò rỉ dự đoán.

**File/module:** GT mới, chính sách annotation, manifest và artifact overlay mới trong results D.

**Cách thực hiện:** mở ảnh gốc trong công cụ annotation, ẩn mọi mask HSV/prediction; Hoàn vẽ polygon/brush thủ công theo policy, ghi phiên bản và màu mục tiêu. Có thể dùng nhãn độc lập sẵn có nếu khớp định nghĩa màu và có giấy phép; nhãn object-class không tự động tương đương color-mask, phải xem lại và chỉnh thủ công. Rasterize polygon theo tọa độ gốc, không resize ảnh để né lệch size; xuất PNG một kênh 0/255, tắt antialias khi xuất mask. Tạo overlay chỉ từ ảnh và GT để xem rìa, vùng bỏ sót, đối tượng cùng màu.

Hoàn review lần hai ở phiên làm việc tách biệt, không xem prediction; duyệt mọi GT, kiểm tra kỹ toàn bộ ảnh khó và ít nhất 20% ảnh xem lại ở zoom 100–200%. Ghi lần review, lỗi sửa, phương pháp; đây là tự review, không tuyên bố inter-annotator agreement vì chỉ một người. Nhãn cần sửa lưu bản mới có version, manifest trỏ bản approved; giữ nhãn cũ.

**Input:** ảnh có quyền sử dụng, target/policy. **Output:** GT độc lập và review log.

**DONE checklist:**

- [ ] 100% nhãn approved có annotation_method/version và review_status approved.
- [ ] Không dùng HSV/median/morphology pipeline để sinh hoặc sửa nhãn.
- [ ] Có overlay và ghi nhận vùng mơ hồ; không bịa việc đã review.

### TASK D.5 — VALIDATOR RAW GT VÀ DATA LOADER THEO MANIFEST

**Mục tiêu:** toàn bộ dữ liệu approved đọc được mà không che lỗi gốc.

**File/module:** `src/data_loader.py`, `scripts/audit_dataset.py`, `tests/test_data.py`, manifest.

**Cách thực hiện:** thêm phương thức additive `build_dataset_from_manifest(manifest_path, split=None)` trả danh sách record giữ sample/color/source; không đổi chữ ký các hàm cũ hoặc `build_dataset()` mặc định. Chỉ chọn approved có nguồn hợp lệ, kiểm tra raw file trước `load_image_gt_pair`, kiểm tra hash/dimensions/binary/ràng buộc path; lỗi bản ghi approved phải báo sample ID, không bỏ im lặng. Giữ khả năng đọc 10 cặp tổng hợp cũ. Đối chiếu số record expected và actual để tránh bỏ ảnh thiếu nhãn khỏi thống kê.

Cập nhật `TestRealDataset` theo contract mới, giữ class/hàm cũ và mục đích kiểm tra: test đếm 8–12 và Red trở thành kiểm tra subset `synthetic_reference`; bổ sung test tập approved đa màu theo manifest, không hạ chuẩn chỉ để hết FAIL. Có test manifest thiếu GT/path/hash/split, color lạ, duplicate ID và cùng group ở hai split. `validate_pair` cũ coi GT không foreground là lỗi; giữ quy tắc bộ positive cũ, nếu thêm ca âm tính thì dùng validator manifest riêng cho `negative_control` và báo riêng, không thay hành vi cũ ngầm.

**Input:** manifest/GT đã review. **Output:** DataLoader bổ sung, validator và test contract dữ liệu.

**DONE checklist:**

- [ ] 100% record approved được load; 0 record approved thiếu file hoặc sai raw GT.
- [ ] GT 128/RGB/khác size bị phát hiện trước threshold; không sửa raw file tự động.
- [ ] Các kiểm tra dữ liệu cũ còn ý nghĩa, không bị xóa/skip để che lỗi.

### TASK D.6 — CHIA TUNING VÀ FINAL_TEST, CHỐNG RÒ RỈ

**Mục tiêu:** chọn cấu hình và đo cuối trên hai tập độc lập.

**File/module:** manifest và `data/dataset_freeze.json`.

**Cách thực hiện:** chia theo `group_id` là cảnh/vật thể/chuỗi chụp; ảnh trùng/gần trùng, crop từ cùng ảnh và mọi nhãn màu của một ảnh phải cùng split. Mục tiêu 60% tuning/40% final_test theo nhóm, seed 42; tối thiểu 8 ảnh thật final_test và ít nhất một nhóm mỗi split cho từng màu được đưa vào kết luận so sánh. Nếu thiếu nhóm thì bổ sung ảnh ở D.3, không rút ảnh tổng hợp sang test thật để đủ số. Seed giúp tái lập, không bảo đảm chống rò rỉ nên phải kiểm tra hash/group thực tế. Các ảnh cũ đã dùng báo cáo/điều chỉnh được gắn tuning hoặc synthetic_reference, không làm final_test mới. Khóa split trước tuning; không xem metrics final_test trong D.

**Input:** tập approved và thông tin nhóm/nguồn. **Output:** split cố định, bảng số lượng màu/tình huống/group mỗi tập.

**DONE checklist:**

- [ ] Giao group_id và hash ảnh giữa tuning/final_test là rỗng.
- [ ] Số lượng đạt mục tiêu, thiếu coverage được ghi rõ và xử lý trước freeze.
- [ ] Mọi phiên bản nhãn và đường dẫn được khóa hash.

### TASK D.7 — TUNING QUA B VÀ KHÓA CẤU HÌNH CHO E

**Mục tiêu:** chuẩn bị cấu hình được chọn có căn cứ mà không làm lại chức năng B.

**File/module:** công cụ B, pipeline C; đầu ra `results/phase_d/<run_id>/selected_configs.json`, freeze và báo cáo D. Không sửa preset A hoặc code B/C.

**Cách thực hiện:** thử tối thiểu ba HSV configs hợp lệ cho mỗi màu trong bộ học thuật trên tuning, giữ ảnh/preprocessing/median/morphology/stage cố định. Mặc định chọn theo macro-IoU trên các ảnh tuning cùng màu, rồi macro-F1; đồng hạng ghi rõ và chọn ID ổn định đã quy định trước. Báo năm metrics theo ảnh và macro trung bình số học; không dùng foreground pixel count thay Accuracy. Nếu thay cả H/S/V chỉ kết luận ảnh hưởng cấu hình tổng thể, không gán nguyên nhân riêng cho một kênh. Lưu baseline preset và config được chọn cùng toàn bộ candidate snapshot, stage và hash đầu vào. Không bắt buộc candidate phải thắng preset và không sửa GT nếu điểm thấp.

`dataset_freeze.json` ghi schema/version, manifest hash, hash ảnh/GT, split, policy version, pipeline snapshot, selected config path/hash, phiên bản công cụ, seed, thời điểm và người thực hiện. E dùng trực tiếp freeze để chạy final_test một lần theo giao thức; D không tính/nhìn điểm final_test. Nếu E phát hiện bug code, giữ kết quả lượt lỗi, sửa có ghi nhận và chạy phiên bản mới; nếu thay dữ liệu thì quay lại D với phạm vi được Hoàn cho phép.

**Input:** tuning, công cụ B/C, split đã khóa. **Output:** cấu hình chọn, kết quả tuning và freeze.

**DONE checklist:**

- [ ] Có ≥3 cấu hình/màu trong phạm vi học thuật và pipeline cố định.
- [ ] Chỉ tuning được dùng để chọn, final_test chưa dùng điều chỉnh.
- [ ] Freeze đủ dữ liệu để E chạy lại, preset gốc không bị sửa.

### TASK D.8 — BÁO CÁO, FINAL REVIEW VÀ FINAL FILE INTEGRITY CHECK

**Mục tiêu:** bàn giao dataset có giới hạn minh bạch và toàn vẹn.

**File/module:** báo cáo D, manifest/freeze, artifact D, allowlist.

**Cách thực hiện:** tổng hợp kiểm kê trước/sau, nguồn/giấy phép, annotation/review, lỗi hợp lệ/không hợp lệ, coverage 15 màu, split và tuning. Ghi lệnh và kết quả test thật; mọi pending có next_action. Kiểm tra hash/danh mục trước sau, nhãn gốc còn nguyên, Excel/HEAD không đổi. Mỗi tiêu chí mục 9 có trạng thái và bằng chứng. Không gọi DONE nếu chưa có tối thiểu dữ liệu thật/nhãn độc lập và freeze đúng; nếu thiếu thao tác chụp/vẽ thì bàn giao cụ thể từng sample để Hoàn hoàn tất rồi tiếp tục task, không công bố đã có dữ liệu.

**Input:** toàn bộ đầu ra D. **Output:** báo cáo và biên bản freeze/toàn vẹn.

**DONE checklist:**

- [ ] Có source registry, manifest, policy, GT approved, validator và freeze.
- [ ] Thống kê khớp thực tế, không có số liệu bịa.
- [ ] Không mất file/ngoài scope; không chạy E hoặc F tự động.

## 8. KẾ HOẠCH KIỂM THỬ

| Mã | Kiểm tra | Kỳ vọng |
|---|---|---|
| D-T01 | Quét mọi ảnh/GT, đối chiếu inventory/manifest | 100% được hạch toán, không bỏ sót |
| D-T02 | Decode raw, channels/dtype/dimensions/unique values | 100% approved hợp lệ, mask 0/255 một kênh |
| D-T03 | Missing/orphan/duplicate/path/hash/color sai | Bị báo chính xác, không bỏ im lặng hoặc auto-fix |
| D-T04 | Overlay từng GT và review lần hai | Đúng vùng mục tiêu theo policy, có log |
| D-T05 | DataLoader trên mọi record approved | Số load bằng số expected; không lỗi |
| D-T06 | Kiểm tra giao nhóm/hash giữa split | 0 giao; nhãn của một ảnh cùng split |
| D-T07 | Load bộ tổng hợp cũ và test contract mới | Giữ tương thích, không skip để che lỗi |
| D-T08 | Chạy lại tuning từ config/hash đã lưu | Cùng mask/metrics trong cùng môi trường |

Unit test thuật toán Phase 2 không được viết lại; đây là kiểm thử chất lượng dữ liệu và adapter manifest. E sử dụng tập đã khóa để kiểm thử tích hợp/đo cuối, không gán nhãn lại.

## 9. ACCEPTANCE CRITERIA

| Tiêu chí | Điều kiện đo lường |
|---|---|
| Inventory | 100% file cũ/mới được thống kê, tổng nhóm khớp số file |
| Dữ liệu thật | ≥20 cặp thật approved; ≥5 màu, ≥5 tình huống; ≥8 ảnh thật final_test |
| Quyền sử dụng | 100% approved có source_id và giấy phép/quyền sử dụng có bằng chứng |
| GT độc lập | 100% approved gán nhãn độc lập, review log; 0 GT từ pipeline HSV |
| Kỹ thuật | 0 cặp approved sai kích thước/kênh/dtype/binary/hash/path |
| DataLoader | 100% record approved load được, không mất bản ghi im lặng |
| Split | 0 group/hash giao tuning/test; từng màu kết luận có nhóm ở hai tập |
| Tuning/freeze | ≥3 candidate/màu; chỉ tuning chọn config; manifest/pipeline/config khóa hash |
| Dữ liệu pending | 100% có lý do và next_action; không bị tính vào tập đánh giá |
| Toàn vẹn | 0 file gốc bị xóa/rename/move/ghi đè ngoài phép; Excel/HEAD không đổi |

Chỉ chứng minh chất lượng với các màu/dữ liệu được duyệt. Nếu mục tiêu 20 cặp cần thay do hạn chế thực tế, báo bằng chứng và đề xuất cụ thể để Hoàn quyết định; không tự hạ chuẩn hoặc đánh dấu DONE. Điểm IoU thấp không đồng nghĩa nhãn sai; ghi hạn chế trung thực.

## 10. RỦI RO VÀ PHƯƠNG ÁN XỬ LÝ

- Không xác minh được nguồn ảnh: giữ file, excluded khỏi công bố; tìm nguồn được phép hoặc tự chụp theo D.3.
- Vẽ nhãn khó/tốn thời gian: ưu tiên ảnh vùng mục tiêu rõ, dùng polygon/brush đơn giản, chọn đủ độ đa dạng; không dùng prediction làm lối tắt.
- Nhãn object không khớp nhãn màu: xem thủ công và sửa theo policy, không coi annotation tải về đương nhiên đúng.
- Một người annotation/review: tách phiên review, công khai hạn chế, không bịa độ đồng thuận nhiều người.
- Tập nhỏ hoặc nhiều ảnh cùng cảnh: chia theo group, bổ sung cảnh mới trước freeze, báo khoảng coverage.
- Test cũ khóa Red/8–12: giữ kiểm chứng subset cũ và mở test manifest mới có căn cứ, không xóa test.
- Test/scripting cũ ghi đè `report/`/`data/`: không chạy entrypoint đó; dùng API import với output riêng hoặc script audit mới an toàn.

## 11. DEPENDENCIES

```text
A → B → C → D → E → F
A: color IDs/preset có thật
B/C: công cụ so sánh và pipeline cố định
D: nguồn + GT + manifest + tuning + freeze
E: kiểm thử xuyên hệ thống + chạy final_test theo freeze
F: dùng số liệu E và nguồn D để báo cáo/bảo vệ
```

D sở hữu thu thập, annotation, split, tuning và freeze; không yêu cầu E sửa dữ liệu để hết FAIL. E sở hữu đo cuối, chỉ trả blocker về D nếu dữ liệu sai. F không tính lại kết quả hoặc đổi nhãn. B hoàn tất chức năng trước D, còn kết luận học thuật chỉ hợp lệ sau D/E.

## 12. BÁO CÁO ĐẦU RA

`docs/REPORT/PHASE-D-DATASET-REPORT.md`: bảng inventory trước/sau; danh sách missing/invalid/pending/excluded; nguồn/giấy phép; chính sách nhãn và review; coverage màu/tình huống; split/group; kết quả validator/DataLoader/test; tuning với config/stage/hash; đường dẫn freeze; giới hạn; Acceptance Criteria và Final File Integrity Check. Không ghi điểm final_test trong báo cáo D; phần đó thuộc E.

## 13. FINAL REVIEW

- [ ] TASK D.1–D.8 có bằng chứng DONE.
- [ ] Không GT sinh bởi HSV; mọi nhãn approved review độc lập.
- [ ] Bộ thật đạt mục tiêu, split sạch và freeze đủ thông tin.
- [ ] Mọi dữ liệu gốc còn nguyên, pending có hướng xử lý.
- [ ] Báo cáo không nhầm ảnh tổng hợp thành ảnh chụp thật.

## 14. STOP RULE

Sau freeze, báo cáo và kiểm tra toàn vẹn: **DỪNG**. Không tự chạy E, không commit/push hoặc thay preset A. Blocker cần thao tác thủ công phải ghi rõ ảnh/công cụ/bước làm/đầu ra cần có, tiếp tục công việc độc lập trong D; chỉ dừng toàn Phase khi thực sự bị chặn, không báo DONE giả.

## 15. TỔNG KẾT PHASE VÀ THỨ TỰ THỰC HIỆN

D.1 Inventory → D.2 Policy/manifest → D.3 Nguồn và bổ sung ảnh → D.4 Annotation/review → D.5 Validator/DataLoader → D.6 Split → D.7 Tuning/freeze → D.8 Báo cáo/review/toàn vẹn → DỪNG. Kết quả là dữ liệu và cấu hình có thể truy nguyên, sẵn sàng cho đánh giá cuối E.
