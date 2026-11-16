# Báo cáo triển khai Phase B – So sánh ngưỡng HSV

Ngày: 2026-11-16. HEAD khi bắt đầu và khi kết thúc: `46ac43e19e1b4d8daabc64173a22089a88512b15` (không commit/push).

## 1. File thay đổi (trong allowlist)

| File | Nội dung |
|---|---|
| `main.py` | `comparison_data` + `comparison_lock`, 4 endpoint `/api/compare-hsv`, `/evaluate`, `/export`, `/import-config`; validator, `read_strict_gt`, `rank_configurations` (Fraction), manifest schema v1 |
| `templates/index.html` | Tab "So sánh HSV": cấu hình, banner stale, lưới mask, GT, bảng metrics, biểu đồ |
| `static/js/app.js` | `cmp*` (thêm/xóa/sửa cấu hình, chạy, đánh giá, export, import), `cmpRequestSeq`, `cmpMarkStale` |
| `static/css/style.css` | Style `.cmp-*` |
| `tests/test_phase_b_comparison.py` | Mới: B-T01..B-T09 + hồi quy |
| `docs/REPORT/PHASE-B-IMPLEMENTATION-REPORT.md` | Báo cáo này |

Ghi chú: `src/hsv_segment.py`, `tests/test_hsv.py`, `tests/test_phase_a_api.py` đã ở trạng thái đã sửa/untracked từ trước (Phase A), nằm ngoài allowlist Phase B và không bị sửa thêm trong phiên này. Không xóa/đổi tên/di chuyển file; không sửa dataset, GT, Excel, tài liệu phase khác.

## 2. Kết quả test thực tế

Python 3.14 (`pythoncore-3.14-64`), pytest.

- `tests/test_phase_b_comparison.py` + `tests/test_phase_a_api.py` + `tests/test_hsv.py`: **66 passed, 72 subtests passed**.
- Toàn bộ `tests/`: 184 passed (lần chạy đầu); 4 lỗi trong `tests/test_data.py::TestRealDataset` (số ảnh, thiếu GT cho 24 ảnh, metadata 10/34). Đây là lỗi dữ liệu Phase D đã có từ trước (ảnh mới chưa có GT/metadata), không do Phase B và không được sửa vì ngoài phạm vi. Một lỗi test B-T07 do chính test viết sai đã được sửa và chạy lại pass.

| Mã | Phạm vi kiểm chứng | Kết quả |
|---|---|---|
| B-T01 | 2/3/6 nhận; 0/1/7 bị 400, không tạo state | PASS |
| B-T02 | đỏ 2 khoảng Hue, xanh lục 1, trắng/đen/xám mode sv ép Hue 0–179; preset gốc không đổi | PASS |
| B-T03 | cấu hình giống nhau cho mask giống từng pixel; ảnh nguồn không đổi | PASS |
| B-T04 | min>max, H=180, float, bool, S/V>255, trùng/sai config_id, preset/màu/stage/pipeline/session sai: 4xx, không tạo state | PASS |
| B-T05 | không GT: N/A, không winner; GT 128, RGB, uint16, sai kích thước, không phải PNG, chưa xác nhận cặp, hash ảnh sai: 400, không ghi state | PASS |
| B-T06 | metrics khớp evaluator ≤1e-9; xếp hạng IoU rồi F1; đồng hạng 1,1,3 với Fraction; có cấu hình lỗi: không winner | PASS |
| B-T07 | Kiểm tra bằng đối chiếu mã nguồn JS (`cmpRequestSeq`, `cmpMarkStale` trong upload, bỏ phản hồi sai thứ tự) | PASS ở mức tĩnh. **Chưa chạy thử trong trình duyệt** |
| B-T08 | ZIP có `comparison.json` v1 + 3 mask/cấu hình, mask khớp bộ nhớ, không lộ đường dẫn; import cùng ảnh chạy lại với ID mới và `evaluations` rỗng; khác ảnh: cảnh báo hash, không gắn metrics cũ; ZIP/không JSON/schema sai/quá 1 MiB bị từ chối | PASS |
| B-T09 | `/api/process` không đổi `comparison_data` và ngược lại | PASS |

## 3. Đối chiếu Acceptance Criteria

| Tiêu chí | Trạng thái |
|---|---|
| 2–6 cấu hình từ preset A, validation chặt, preset gốc không đổi | Đạt (B-T01, B-T02, B-T04) |
| Cùng ảnh bất biến, màu mục tiêu và pipeline cố định; state độc lập | Đạt (B-T03, B-T09) |
| Mask cạnh nhau, thông số đầy đủ, bảng + biểu đồ 5 metrics | Đã cài đặt trong HTML/JS/CSS; **chưa kiểm tra bằng mắt/trình duyệt** |
| GT nghiêm ngặt, không threshold/resize, tái dùng evaluator | Đạt (B-T05, B-T06) |
| Xếp hạng IoU→F1, đồng hạng, không winner khi thiếu GT/lỗi | Đạt (B-T05, B-T06) |
| Export ZIP + import, kiểm hash, metrics nhập không là kết quả mới | Đạt (B-T08) |
| Stale + request bất đồng bộ + lỗi | Đạt ở mức mã nguồn/tĩnh (B-T07) |

## 4. Giới hạn

- Test dùng ảnh/GT tổng hợp: chỉ chứng minh logic chức năng, **không đánh giá chất lượng phân đoạn trên ảnh thật**. Chưa chạy so sánh trên dataset thật vì GT thật còn thiếu (Phase D).
- Giao diện chưa được kiểm thử tự động trong trình duyệt.
- Quy ước chia cho 0 theo evaluator hiện tại (trả 0.0), không sửa trong Phase B.
- `comparison_data` nằm trong bộ nhớ, tối đa số lượt/session theo `COMPARE_MAX_PER_SESSION`; mất khi khởi động lại server.
- Hash ảnh tính trên byte file upload (dự phòng: pixel đã giải mã).
- Test dùng thư mục tạm riêng; `uploads/` không bị ghi bởi test Phase B.

## 5. Final File Integrity Check

- HEAD không đổi; không commit/push.
- `git status`: tập file sửa/untracked như lúc đầu, cộng thêm `tests/test_phase_b_comparison.py` (và báo cáo này, trong `docs/REPORT/` đã untracked).
- File ignored (`.pytest_cache/`, `__pycache__/`, `.venv/`, `venv/`, `uploads/`, `results/`, `pytest_output.txt`): không xóa/ghi đè có chủ đích; `.pytest_cache` và `__pycache__` được pytest cập nhật tự động.
- Không có file dataset, GT, Excel hay tài liệu phase khác bị sửa (`git diff --stat` chỉ gồm 6 file đã liệt kê; `main.py`, `templates`, `static`, trong allowlist).
- Chưa lưu hash SHA-256 từng file làm mốc trước khi sửa trong báo cáo này; việc đối chiếu dựa trên `git status`/`git diff --stat` và HEAD.

## 6. Dừng

Phase B hoàn tất ở mức trên. Không chuyển sang Phase C.
