# Báo cáo Phase D: Dataset và Ground Truth

- Run ID: `D-20261116-120846`
- Ngày: 2026-11-16
- Git HEAD khi bắt đầu: `46ac43e19e1b4d8daabc64173a22089a88512b15` (nhánh `main`, không commit/push)
- Artifact: `results/phase_d/D-20261116-120846/`

## 1. Kết luận

**Phase D: PARTIAL / BLOCKED. Không báo DONE.**

Phần công cụ, manifest, validator, loader, test và khoá cấu hình đã hoàn tất và kiểm chứng. Mục tiêu dữ liệu thật chưa đạt vì không có cặp ảnh thật nào có GT độc lập, người duyệt và nguồn rõ ràng. Việc này cần người (Hoàn) chụp, vẽ và duyệt, AI không được tạo thay.

| Mục tiêu | Yêu cầu | Hiện tại | Đạt |
|---|---|---|---|
| Cặp ảnh thật approved | ≥ 20 | 0 | Không |
| Số màu (thật) | ≥ 5 | 0 | Không |
| Số tình huống (thật) | ≥ 5 | 0 | Không |
| Ảnh thật `final_test` | ≥ 8 | 0 | Không |
| Manifest, sources, policy, freeze | có, đúng schema | có | Có |
| DataLoader theo manifest + validator raw GT | có | có | Có |
| Tuning ≥ 3 cấu hình/màu qua B, pipeline C cố định | có | 4 cấu hình màu đỏ, chỉ trên dữ liệu tổng hợp | Một phần |

## 2. Kiểm kê (D.1, 100% tệp)

Chi tiết trong `audit/` (`inventory_files.csv`, `inventory_images.json`, `inventory_gt.json`, `pairs.json`, `exif_provenance.json`, `summary.json`).

- 34 ảnh, tất cả mở được (34 ok). 10 GT, tất cả hợp lệ.
- 10 cặp hợp lệ (ảnh tổng hợp `img_01`..`img_10`). 24 ảnh thiếu GT.
- GT mồ côi: 0. Trùng byte chính xác: 0.
- Gần trùng (dHash, Hamming ≤ 4): `img_05`..`img_09`. Đã gộp vào nhóm `grp_synth_red_variations` để không bị chia sang hai split khác nhau.
- `metadata.csv` cũ chỉ phủ 10/34 ảnh. File này không bị sửa.
- 17 ảnh Samsung S911B (EXIF cho thấy máy, nhưng chưa ai xác nhận là nhóm tự chụp) và 7 ảnh web (không có URL, tác giả, giấy phép).
- Trạng thái Git ban đầu và hash trước khi sửa: `pre_git.txt`, `pre_snapshot.csv`.

## 3. Phân loại (D.2, D.3)

| Nhóm | Số lượng | `status` | Lý do |
|---|---|---|---|
| Tổng hợp `synthetic_reference` | 10 | approved | GT sinh từ hình học lúc vẽ, không dùng HSV. Không tính là ảnh thật |
| Samsung S911B | 17 | pending_annotation | Chưa có GT, chưa xác nhận người chụp |
| Ảnh web | 7 | excluded | Chưa rõ nguồn và giấy phép |

Mỗi dòng chưa duyệt có `exclusion_reason` và `next_action` trong `data/dataset_manifest.csv`. `annotation_policy.md` quy định GT độc lập HSV, PNG một kênh uint8 0/255, đúng kích thước, cần 2 người (gán nhãn và duyệt). Không có review log nào được tạo, vì chưa có việc review thật.

## 4. Mã nguồn (D.4, D.5)

`src/data_loader.py` thêm hàm (API cũ giữ nguyên): `file_sha256`, `validate_raw_gt`, `load_manifest`, `validate_manifest`, `build_dataset_from_manifest`, `load_manifest_sample`. Validator không sửa file GT, chỉ báo lỗi.

`tests/test_data.py`: `TestRealDataset` cũ đếm toàn thư mục (8–12 ảnh có GT), nay thư mục có 34 ảnh nên 4 test cũ fail (xem `baseline_pytest_before.txt`: 4 failed, 202 passed). Không xoá, không skip: các kiểm tra đó được chuyển sang `TestSyntheticReferenceDataset` (xác định tập qua manifest) và thêm `TestManifestContract`, `TestRawGtValidator`. Kết quả sau: `python -m unittest discover -s tests` chạy 217 test, OK (`unittest_after.txt`). Môi trường không có `pytest` ở `.venv`; baseline trước đó chạy bằng pytest ở môi trường khác.

## 5. Split, tuning, freeze (D.6, D.7)

- Seed 42, chia theo `group_id`. Vì không có mẫu thật approved nên `tuning` và `final_test` thật đều rỗng. Không có điểm `final_test` nào được xem.
- Tuning chạy trên `synthetic_reference` (10 ảnh) với pipeline C cố định (median 5, ellipse 5, close ×1), 4 cấu hình cho màu đỏ, xếp hạng theo macro-IoU rồi macro-F1:

| Hạng | Cấu hình | Macro-IoU | Macro-F1 |
|---|---|---|---|
| 1 | `red_wide_sv` | 0.9013 | 0.9187 |
| 2 | `red_narrow_hue` | 0.7959 | 0.7979 |
| 3 | `red_preset` | 0.7135 | 0.7248 |
| 4 | `red_strict_sv` | 0.7117 | 0.7239 |

- `selected_configs.json` ghi `academic_validity: NOT_REAL_DATA`. Kết quả này chỉ chứng minh công cụ chạy đúng và tất định, không dùng làm kết luận học thuật. Chỉ có màu đỏ; các màu khác chưa có dữ liệu nên không tuning.
- Preset A không bị sửa. Cấu hình chọn chỉ lưu trong artifact và freeze.
- `data/dataset_freeze.json` (status `PARTIAL_BLOCKED`) khoá hash manifest, sources, policy, hash ảnh/GT từng mẫu, pipeline, hash candidates và selected configs.

## 6. Kết quả D-T01..D-T08 (`verification.json`)

| Test | Kết quả | Ghi chú |
|---|---|---|
| D-T01 Manifest phủ 100% ảnh/GT | Đạt | 34/34 ảnh, 10/10 GT |
| D-T02 GT raw hợp lệ | Đạt | 10 GT approved |
| D-T03 Bắt lỗi giả lập | Đạt | thiếu ảnh, sai hash, thiếu GT, trùng, status sai, thiếu next_action, rò rỉ group đều bị phát hiện |
| D-T04 Overlay + review lần hai | **Một phần** | 10 overlay tự sinh trong `overlays/`, chưa có người review nên không ghi review log |
| D-T05 Loader theo manifest | Đạt | 10/10 mẫu nạp được |
| D-T06 Split không rò rỉ | Đạt hình thức | tuning/final_test thật đều rỗng |
| D-T07 Bộ test | Đạt | 217 test OK |
| D-T08 Replay tất định | Đạt | metrics và hash mask khớp giữa hai lần chạy |

Kiểm tra hash freeze khớp với tệp hiện tại: manifest, sources, policy, selected_configs đều đúng.

## 7. Final File Integrity Check

- Không xoá, đổi tên, di chuyển ảnh/GT/`metadata.csv` cũ. `git status` không báo thay đổi nào ở `data/images` đã theo dõi, `data/ground_truth`, `data/metadata.csv`.
- Không sửa Excel, preset A, tài liệu Phase khác. Không commit, không push.
- Tệp mới/sửa trong allowlist: `data/dataset_manifest.csv`, `dataset_sources.json`, `annotation_policy.md`, `dataset_freeze.json`, `data/README.md` (thêm mục 10), `src/data_loader.py`, `tests/test_data.py`, `scripts/audit_dataset.py`, báo cáo này, `results/phase_d/D-20261116-120846/`.
- Các thay đổi trước đó ở `main.py`, `src/hsv_segment.py`, `static/`, `templates/`, `tests/test_hsv.py` thuộc Phase A–C, không do Phase D tạo.
- Lưu ý: `data/README.md` mục 1–9 là nội dung cũ (nhắc `TestRealDataset`, `report/data.md`); chưa chỉnh để giữ metadata cũ, mục 10 là bản cập nhật hiện hành.

## 8. Việc cần Hoàn làm (để đóng blocker)

1. Xác nhận 17 ảnh `cam_*` là nhóm tự chụp (ghi vào `dataset_sources.json`, kèm đồng ý dùng). Với 7 ảnh `web_*`: cung cấp URL gốc, tác giả, giấy phép, nếu không thì giữ `excluded`.
2. Với mỗi ảnh được nhận: chọn `target_color_id`, `scenario`, `lighting`, `background` (điền vào manifest).
3. Vẽ GT bằng công cụ vẽ polygon/brush (ví dụ CVAT hoặc GIMP), không dùng ngưỡng HSV. Xuất PNG một kênh 8-bit, nền 0, vật thể 255, đúng kích thước ảnh gốc, lưu `data/ground_truth/<tên ảnh>.png`. Không lưu JPEG.
4. Người thứ hai xem overlay, ghi review log thật, rồi cập nhật `review_status`, `annotator`, `status=approved`.
5. Chụp thêm cho đủ ≥ 5 màu, ≥ 5 tình huống, ≥ 20 cặp, trong đó ≥ 8 ảnh thật cho `final_test` (thêm theo nhóm ảnh, không cùng cảnh với tuning).
6. Sau đó chạy lại `scripts/audit_dataset.py`, `validate_manifest`, chia split (seed 42), tuning lại và tạo lại freeze.

## 9. Giới hạn

- Mọi số liệu IoU/F1 ở trên là trên ảnh tổng hợp đỏ và có tính tự tham chiếu, không phản ánh chất lượng trên ảnh thật.
- Chưa có split thật nên Phase E không được chạy `final_test` ngoài dữ liệu tổng hợp cho đến khi blocker được giải quyết.
- Đã dừng sau Phase D, không chạy Phase E.

## 10. Lượt bổ sung D-20261116-125512 (xử lý blocker)

Artifact: `results/phase_d/D-20261116-125512/`. Git HEAD `46ac43e19e1b4d8daabc64173a22089a88512b15`, không commit/push. Trạng thái Git, danh mục và SHA-256 trước khi sửa: `pre_git.txt`, `pre_snapshot.csv` (305 tệp). Bản sao trước khi sửa: `backup/dataset_manifest.before.csv`, `backup/dataset_freeze.before.json`.

### 10.1 Audit lại (không làm lại phần đã có bằng chứng)
Audit chạy lại cho kết quả như lượt trước: 34 ảnh mở được, 10 GT hợp lệ, 10 cặp hợp lệ (tổng hợp), 24 ảnh thiếu GT, 0 GT mồ côi, 0 trùng byte (`audit/summary.json`). D.1, D.4, D.5 giữ nguyên. Các mục D.2, D.3, D.6, D.7 vẫn bị chặn vì thiếu dữ liệu thật.

### 10.2 Lỗi mới phát hiện và đã sửa: kích thước theo EXIF
12 ảnh Samsung có EXIF Orientation = 6. `cv2.imread` mặc định (cách `main.py` và `load_manifest_sample` đọc) trả về 3024x4032 (rộng x cao), còn `audit_dataset.py` đọc `IMREAD_UNCHANGED` ra 4032x3024. Manifest ghi 4032x3024. Nếu người vẽ GT theo ảnh đã xoay (3024x4032), `validate_raw_gt` sẽ báo lệch kích thước. Bằng chứng: `audit/orientation_check.csv`.

Đã làm (công cụ `tools/fix_manifest_dims.py`, kiểm tra CSV khứ hồi byte-exact trước khi ghi):
- Đổi `width`/`height` của 12 dòng `pending_annotation` sang 3024/4032 và cập nhật chuỗi kích thước trong `next_action`. Không đổi status, split, hash ảnh, mẫu approved.
- Thêm quy tắc "kích thước sau EXIF Orientation" vào `data/annotation_policy.md`.
- Cập nhật hash manifest/policy trong `data/dataset_freeze.json` và thêm mục `revisions` (status vẫn `PARTIAL_BLOCKED`).
- `validate_manifest`: ok, approved 10, pending 17, excluded 7, invalid 0.

### 10.3 Công cụ GT độc lập (`tools/gt_tools.py`)
- `rasterize <labelme.json> <label> <out.png>`: polygon sang PNG 1 kênh uint8 {0,255}, không anti-alias, không ghi đè tệp có sẵn.
- `check`: kiểm tra mọi PNG trong `data/ground_truth/annotations_v1/` (kích thước, kênh, dtype, nhị phân, không rỗng). Hiện 0 tệp, 0 lỗi.
- `overlay <image> <gt.png> <out.png>`: overlay không có dự đoán HSV, dùng cho người duyệt thứ hai.
Không công cụ nào dùng ngưỡng HSV. Tệp thử nghiệm tạm đã xoá khỏi thư mục run, chưa tạo GT thật nào.

### 10.4 Hàng đợi việc cho Hoàn (`annotation_queue.csv`, 24 dòng)
Mỗi dòng có kích thước đúng, công cụ, đường dẫn GT đầu ra và yêu cầu GT.

**A. 17 ảnh Samsung (`cam_*`), kích thước sau EXIF**
- 3024x4032: `20250603_100502`, `20250620_194513`, `20250622_141438`, `20250628_153417`, `20250713_124728`, `20250813_203833`, `20250912_140210`, `20251103_070809`, `20260224_212112`, `20260510_210129`, `20260630_135052`, `20260702_082641`.
- 5264x3948: `20250707_100818`, `20260302_085606`, `20260403_092806`.
- 3648x2736: `20260326_085513`.
- 3948x4043: `20260726_214840`.

Thao tác cho từng ảnh:
1. Xác nhận ảnh do nhóm tự chụp và đồng ý dùng. Ghi ngày/nơi vào `data/dataset_sources.json` (thay `src_samsung_s911b_unverified`). Ảnh không xác nhận được thì giữ `excluded`.
2. Điền `target_color_id`, `scenario`, `lighting`, `background` trong manifest. Mỗi ảnh có thể có nhiều vật thể, mỗi cặp ảnh/màu cần một GT riêng.
3. Mở ảnh bằng LabelMe hoặc CVAT (hiển thị theo đúng chiều xoay), vẽ polygon quanh vật thể màu mục tiêu, lưu JSON.
4. Chạy `python results/phase_d/D-20261116-125512/tools/gt_tools.py rasterize <json> <label> data/ground_truth/annotations_v1/<stem>__<color>__v1.png`.
5. Chạy `gt_tools.py check`, rồi `gt_tools.py overlay` để sinh ảnh duyệt.
6. Người thứ hai xem overlay, ghi review log thật, sau đó mới đặt `review_status`, `annotator`, `status=approved`.

**B. 7 ảnh web (`web_*`)**: `apple_green`, `apple_red`, `ball_blue`, `eggplant_purple`, `lemon_yellow`, `orange`, `pngtree-pink-rectangular`. Cần URL gốc, tác giả và giấy phép cho từng ảnh. Nếu không có thì giữ `excluded`, không dùng. Ảnh `pngtree` nhiều khả năng cấm dùng lại.

**C. Phủ tiêu chí**: 17 ảnh Samsung chưa đủ ≥ 20 cặp. Cần chụp thêm hoặc gán nhiều màu trên cùng ảnh để đạt ≥ 20 cặp, ≥ 5 màu, ≥ 5 tình huống, ≥ 8 ảnh thật cho `final_test` (chia theo `group_id`, không cùng cảnh với tuning).

### 10.5 Kết quả kiểm tra
- `python -m unittest discover -s tests`: 249 test, OK (`unittest_after.txt`).
- `validate_manifest`: ok, 0 lỗi.
- Không xem điểm `final_test`, không tuning lại, không hạ tiêu chí.

### 10.6 Final File Integrity Check (lượt này)
- So 305 tệp trong `pre_snapshot.csv` với hash hiện tại: không tệp nào mất. Tệp đổi hash: `data/dataset_manifest.csv`, `data/dataset_freeze.json`, `data/annotation_policy.md` (đều là tệp Phase D, có bản sao trước sửa hoặc mô tả ở 10.2), và `results/median_comparison/pytest_check/metrics.csv`, `summary.json` (test `tests/test_median.py` tự ghi lại khi chạy unittest; không phải ảnh/GT).
- Ảnh gốc, GT, `data/metadata.csv`: không đổi (`git diff` rỗng ở `data/ground_truth` và `data/metadata.csv`, hash ảnh khớp snapshot).
- Không sửa Excel, tài liệu Phase khác, preset A. Không xoá, đổi tên, di chuyển. Không commit/push.

### 10.7 Kết luận lượt này
**Phase D vẫn PARTIAL / BLOCKED.** Số cặp ảnh thật approved: 0/20; màu 0/5; tình huống 0/5; `final_test` thật 0/8. Phần AI làm được đã xong; phần còn lại cần xác nhận nguồn và gán nhãn/duyệt bởi người. Đã dừng, không chạy Phase E bổ sung, không chuyển Phase F.
