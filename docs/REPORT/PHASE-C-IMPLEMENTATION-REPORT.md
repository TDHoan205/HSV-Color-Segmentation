# Báo cáo triển khai Phase C - Morphology UI/API

Trạng thái: **CHƯA tuyên bố DONE**. Còn các mục chưa xác minh được, liệt kê ở mục 4.

## 1. Thay đổi (trong allowlist)
- `main.py`: object `morphology` dùng chung cho `/api/process` và `/api/compare-hsv`; validate nghiêm ngặt (HTTP 400); nhánh legacy (`use_closing`, `use_opening`, `morph_kernel`); trả `applied_config` và `request_id`; dùng lại `MorphologyOperator`.
- `templates/index.html`, `static/js/app.js`, `static/css/style.css`: 4 phép (Closing, Opening, Erosion, Dilation), 3 kernel shape, kernel lẻ 1-31, iterations 1-10, hiển thị mask_median trước / mask_morph sau, tóm tắt cấu hình, đánh dấu stale, chặn response cũ bằng `processSeq`, đồng bộ tab so sánh.
- `tests/test_phase_c_morphology_api.py`: file test mới.
- `docs/REPORT/PHASE-C-IMPLEMENTATION-REPORT.md`: báo cáo này.

## 2. Kết quả test (chạy thật)
- Phase A + B + C: **64 passed, 55 subtests passed**.
- Toàn bộ `tests`: 202 passed, **4 failed**, tất cả trong `tests/test_data.py::TestRealDataset`
  (metadata.csv có 10 dòng, thư mục ảnh có 34). Đây là vấn đề dữ liệu/Ground Truth của Phase D, ngoài scope Phase C. Tôi không sửa.
- 12 tổ hợp (4 phép x 3 shape) được so khớp từng pixel với gọi trực tiếp `MorphologyOperator` (C-T01).

Ánh xạ test: C-T01 tổ hợp pixel; C-T02 thứ tự operations (`dilate,erode` khác `erode,dilate`); C-T03 iterations; C-T04 validate + biên 1/31 + request lỗi không làm hỏng session; C-T05 legacy; C-T06 request_id; C-T07 đồng bộ compare B; C-T08 kiểm tra markup (thứ tự, min/max).
Lưu ý: test dùng ảnh tổng hợp trong thư mục tạm, không ghi vào dataset.

## 3. Acceptance Criteria đã xác minh bằng test
Thứ tự API giữ nguyên; validate chặt (chẵn, float, bool, string, shape/op sai, trùng, iterations ngoài khoảng); tương thích payload cũ và `applied_config.branch`; `fixed_pipeline.morphology` dùng chung với B.

## 4. Chưa xác minh / hạn chế
- Hành vi UI thực tế trên trình duyệt (stale, chặn response cũ, hiển thị trước/sau) mới được viết, **chưa kiểm thử trên trình duyệt**; chỉ có kiểm tra cú pháp JS và markup.
- Chưa tạo artifact `results/phase_c/<run_id>/`.
- Chưa ghi hash file trước/sau; chưa chạy Final File Integrity Check bằng hash. Chỉ có `git status` (không commit/push, không xóa/đổi tên file; thay đổi có sẵn được giữ).
- 4 test dataset thất bại sẵn có (mục 2).
