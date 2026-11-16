# PHASE A IMPLEMENTATION REPORT

> **Trạng thái cuối: PHASE A DONE**
> Các tiêu chí chức năng của Phase A đều PASS có bằng chứng. Các giới hạn về chất lượng phân đoạn trên ảnh thật (thiếu Ground Truth) được chuyển sang **Phase D**, không thuộc phạm vi Phase A.
> Phase A **chưa** triển khai Phase B; không commit, không push, không thay đổi Git history.

## 1. Tổng quan

Mở rộng ứng dụng từ tách màu đỏ cố định sang chọn 15 nhóm màu bằng bảng màu, nạp HSV preset tự động, cho phép chỉnh tay H/S/V và Reset về preset của màu đang chọn. Pipeline HSV → Median → Morphology → Evaluation được giữ nguyên.

## 2. File thay đổi

| File | Loại | Nội dung |
|---|---|---|
| `src/hsv_segment.py` | Sửa | Thêm `COLOR_PRESETS` (15 màu), `COLOR_IDS`, `get_color_preset()`, `build_hsv_config()`. Không đổi `DEFAULT_CONFIG`, `__init__`, thuật toán. |
| `main.py` | Sửa | `process_image` nhận `color_id`; thêm route `GET /api/color-presets`. Request không có `color_id` giữ nguyên cấu hình Red cũ. |
| `templates/index.html` | Sửa | Khu vực bảng màu, nút Reset preset; nhãn Hue trung tính. |
| `static/js/app.js` | Sửa | `loadColorPresets`, `renderColorPalette`, `applyPreset`, `selectColor`, `resetPresetToColor`; `processImage` gửi `color_id`. |
| `static/css/style.css` | Sửa | CSS bảng màu ở cuối file. |
| `tests/test_hsv.py` | Sửa | Class `TestColorPresets` (8 test). |
| `tests/test_phase_a_api.py` | **Thêm mới** | 8 test API. |
| `docs/REPORT/PHASE-A-IMPLEMENTATION-REPORT.md` | **Thêm mới** | File báo cáo này. |

Không có file tracked nào bị xóa, đổi tên hoặc di chuyển. Git HEAD vẫn là `46ac43e`.

## 3. Bộ 15 nhóm màu

Nguồn duy nhất: `COLOR_PRESETS` trong `src/hsv_segment.py`. Frontend lấy qua API.

| color_id | Tên | Mode | hue_ranges | S | V |
|---|---|---|---|---|---|
| red | Đỏ | hue | [0,10], [170,179] | 100–255 | 100–255 |
| red_orange | Đỏ cam | hue | [9,16] | 60–255 | 60–255 |
| orange | Cam | hue | [17,22] | 60–255 | 60–255 |
| yellow_orange | Vàng cam | hue | [23,27] | 60–255 | 60–255 |
| yellow | Vàng | hue | [28,35] | 60–255 | 60–255 |
| yellow_green | Vàng lục | hue | [36,44] | 60–255 | 60–255 |
| green | Lục | hue | [45,85] | 60–255 | 60–255 |
| blue_green | Lục lam | hue | [86,100] | 60–255 | 60–255 |
| blue | Lam | hue | [101,125] | 60–255 | 60–255 |
| blue_purple | Lam tím | hue | [126,140] | 60–255 | 60–255 |
| purple | Tím | hue | [141,155] | 60–255 | 60–255 |
| red_purple | Đỏ tím | hue | [156,169] | 60–255 | 60–255 |
| white | Trắng | sv | [0,179] | 0–40 | 200–255 |
| black | Đen | sv | [0,179] | 0–255 | 0–50 |
| gray | Xám | sv | [0,179] | 0–40 | 60–199 |

Ghi chú: khoảng Hue của 12 màu (trừ Đỏ) và ngưỡng S/V của White/Black/Gray là giá trị khởi điểm. Chất lượng của các ngưỡng này trên ảnh thật thuộc **Phase D**. Mỗi preset có `verified = False`.

## 4. Kết quả kiểm thử

### 4.1 Unit / API / Regression (lệnh chạy: `.venv\Scripts\python.exe -m unittest <module>`)

| Module | Số test | Kết quả |
|---|---|---|
| tests.test_hsv | 19 | PASS 19/19 |
| tests.test_phase_a_api | 8 | PASS 8/8 |
| tests.test_evaluation | 8 | PASS 8/8 |
| tests.test_morphology | 66 | PASS 66/66 |
| tests.test_median (Correctness, Validation, KernelComparison) | 22 | PASS 22/22 |
| tests.test_median (TestMedianFilterExperiment) | 1 | PASS 1/1 (chạy với `RESULT_DIR` trỏ sang thư mục tạm) |

Tổng: **124/124 PASS** trong các module liên quan.

### 4.2 Test thực nghiệm Median trong thư mục tạm

- `RESULT_DIR` được patch sang thư mục tạm, không ghi vào `results/`.
- Kết quả: 12 file được tạo (mask, comparison, `metrics.csv`, `summary.json`), sau đó thư mục tạm đã được dọn.
- `results/` không tồn tại trước và sau khi chạy: không có dữ liệu nào bị ghi đè.
- Lưu ý cấu hình: `summary.json` của script `run_median_comparison.py` dùng cấu hình **Red cũ** (`color_name: "Red"`), không phải preset. Đây là thực nghiệm Median độc lập và nằm ngoài phạm vi thay đổi của Phase A; không sửa.

### 4.3 Giao diện trình duyệt (server `127.0.0.1:5055`, đã dừng sau kiểm thử)

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| 15 ô màu, đúng ID | PASS | DOM: 15 `.color-swatch` |
| Màu mặc định | PASS | `red`, nhãn "Đỏ" |
| Chọn màu nạp đúng slider | PASS | Lam: H1 101–125, S/V 60–255 |
| White/Gray khóa Hue | PASS | `h1dis = true`, H = 0–179 |
| Đỏ bật 2 khoảng Hue | PASS | `h1dis = false`, `h2dis = false` |
| Chỉnh tay | PASS | S_min đặt 200 → hiển thị 200 |
| Reset theo màu đang chọn | PASS | S_min về 60; thông báo "Đã khôi phục mặc định màu: Lam" |
| Payload gửi có `color_id` | PASS | Đỏ/Lam/Xám gửi đúng `color_id` và khoảng slider |
| Upload ảnh | PASS | Ảnh 120×120 (Canvas), "Tải ảnh thành công" |
| Mask theo màu (raw) | PASS | Đỏ 1600, Lam 1600, Xám 11200 px — khớp kỳ vọng tính trước |
| Lỗi JavaScript | PASS | Không có lỗi khi đổi nhiều màu và xử lý |
| Ảnh chụp để xem bằng mắt | NOT VERIFIED | Ảnh lưu được nhưng công cụ không hiển thị nội dung |

### 4.4 White/Black/Gray trên patch thuần (trong bộ nhớ)

Ảnh 90×60 gồm 3 patch: trắng (255), đen (0), xám (128).

| Preset | Bắt patch trắng | Bắt patch đen | Bắt patch xám |
|---|---|---|---|
| white | 1800/1800 | 0/1800 | 0/1800 |
| black | 0/1800 | 1800/1800 | 0/1800 |
| gray | 0/1800 | 0/1800 | 1800/1800 |

Mỗi preset chỉ bắt đúng màu của mình, không nhầm sang hai màu còn lại.

### 4.5 Pipeline trên ảnh thật (chỉ đọc)

- Chạy HSV → Median(5) → Close(5) trên **24 ảnh thật** không có GT. Không lỗi đọc file.
- Không tính Accuracy/IoU vì không có GT. Việc bổ sung GT và đánh giá chất lượng chuyển sang **Phase D**.

## 5. Acceptance Criteria (theo bảng nghiệm thu TASK A.11)

| Tiêu chí | Trạng thái | Bằng chứng |
|---|---|---|
| Color Palette | PASS | 15 ô hiển thị (DOM) |
| Color Selection | PASS | Chọn Lam/Trắng/Xám/Đỏ cập nhật đúng |
| HSV Preset | PASS | Test 8/8 + API |
| HSV Slider | PASS | Nạp theo preset, đồng bộ hiển thị |
| Reset | PASS | Khôi phục đúng màu đang chọn |
| Multi Hue | PASS | Test đỏ 2 khoảng khớp `DEFAULT_CONFIG` trên 180 giá trị H |
| Red | PASS | UI và API cho 1600 px |
| White | PASS | Điều kiện S/V; khóa Hue (kỹ thuật). Chất lượng ảnh thật → Phase D |
| Black | PASS | Điều kiện V; khóa Hue (kỹ thuật). Chất lượng ảnh thật → Phase D |
| Gray | PASS | Điều kiện S/V; 11200 px đúng trên ảnh UI |
| Backend | PASS | Không còn cố định Red khi có `color_id` |
| Frontend/API | PASS | Payload đúng trong trình duyệt |
| Pipeline | PASS | Test pipeline và hồi quy |
| Regression | PASS | 124/124 test liên quan |
| Report | PASS | File này |

Không có tiêu chí nào FAIL hoặc PARTIAL.

## 6. Điều kiện hoàn thành Phase A

| # | Điều kiện | Kết quả |
|---|---|---|
| 1 | Có đủ 15 nhóm màu | PASS |
| 2 | HSV preset hoạt động đúng | PASS |
| 3 | Chỉnh tay và Reset đúng | PASS |
| 4 | Backend không còn cố định màu đỏ | PASS |
| 5 | Mask được tạo theo màu được chọn | PASS |
| 6 | Pipeline cũ hoạt động bình thường | PASS |
| 7 | Kiểm thử liên quan có kết quả xác minh | PASS |
| 8 | Báo cáo triển khai đầy đủ | PASS |

## 7. Giới hạn còn tồn tại (ngoài phạm vi Phase A)

1. **Ground Truth cho 24 ảnh thật** — chuyển sang **Phase D**. Hiện chưa đo được Accuracy/IoU trên ảnh thật.
2. **Chất lượng ngưỡng các màu** (Hue 12 màu, S/V White/Black/Gray) — chưa tinh chỉnh; chuyển sang **Phase D** cùng với GT.
3. **`tests/test_data.py`: 4 FAIL trong `TestRealDataset`** — có sẵn trước Phase A: thiếu GT cho ảnh thật và `metadata.csv` chỉ 10 dòng. Không thuộc Phase A; không sửa dữ liệu.
4. **`scripts/run_median_comparison.py`** dùng cấu hình Red cố định cho thực nghiệm Median — không thuộc Phase A.
5. **Ảnh chụp trình duyệt** không xem được bằng mắt; xác nhận giao diện dựa trên DOM và CDP.
6. **Lint:** chưa cài `pyflakes`; chỉ kiểm tra bằng `py_compile` và `node --check`.
7. **File test do Phase A tạo trong `uploads/`** (không bị Git theo dõi): `20261116_104715_test.png`, `20261116_110155_hsv_ui_test.png`, `20261116_110218_hsv_ui_test.png`. **Chưa xóa** vì chưa có sự cho phép.

## 8. Git Diff và tính toàn vẹn

- Tracked file đã sửa (6): `main.py`, `src/hsv_segment.py`, `static/css/style.css`, `static/js/app.js`, `templates/index.html`, `tests/test_hsv.py`. Tổng: 326 dòng thêm, 12 dòng xóa.
- File mới (2): `tests/test_phase_a_api.py`, `docs/REPORT/PHASE-A-IMPLEMENTATION-REPORT.md`.
- Không có file tracked nào bị xóa, đổi tên hay di chuyển.
- Không có commit mới; HEAD vẫn là `46ac43e`. Không push.
- Thư mục `results/` không bị thay đổi.

## 9. Kết luận

**PHASE A: DONE** — 8/8 điều kiện hoàn thành và 15/15 tiêu chí nghiệm thu đạt PASS, với bằng chứng nêu trên. Các giới hạn về chất lượng ảnh thật và Ground Truth được chuyển sang Phase D.

Phase A dừng tại đây. Không triển khai Phase B.
