# PHASE E: BÁO CÁO KIỂM THỬ HỆ THỐNG

- Run ID: `E-20261116-122128` (artifact: `results/phase_e/E-20261116-122128/`)
- Python 3.14.6, Windows 11 (10.0.26300), cv2 5.0.0, numpy 2.5.2
- HEAD khi bắt đầu: `46ac43e19e1b4d8daabc64173a22089a88512b15` (nhánh `main`, ahead 2). Git status, danh sách ignored và `pre_snapshot.csv` (204 file, SHA-256) lưu trong thư mục run.

## 1. Kết luận

**Trạng thái: PARTIAL / BLOCKED (không PASS).**

- Các tầng integration, E2E trình duyệt, bảo mật cơ bản và benchmark đã chạy và đạt.
- Nhánh đánh giá `final_test` thật **NOT RUN**: Phase D freeze có `status = PARTIAL_BLOCKED`, 0 ảnh thật được approved, `final_test` rỗng. Không có số liệu cuối nào được tạo hoặc bịa.
- Blocker này thuộc Phase D, không thuộc Phase E. Cần D bổ sung GT và duyệt quyền sử dụng, rồi chạy lại `scripts/run_final_evaluation.py`.

## 2. Phụ thuộc Phase D (bằng chứng thực tế)

| Mục | Kết quả |
|---|---|
| SHA-256 `data/dataset_freeze.json` | `582235b41484cf14db409ad9df9e6eb68589dc4e136550281e9f17e6e5685fd7` (khớp snapshot trước và sau test) |
| Hash manifest, sources, policy so với freeze | 3/3 khớp |
| Freeze status / run | `PARTIAL_BLOCKED` / `D-20261116-120846` |
| Ảnh approved | 0 (24/34 ảnh thật chưa có GT được lập và chưa rõ quyền sử dụng) |
| `final_test` | rỗng |

`scripts/run_final_evaluation.py` dừng ở trạng thái `BLOCKED_DEPENDENCY_PHASE_D`, ghi `final_evaluation.json` với `per_sample = []`, `summary = null`. Script không tuning và không bỏ ca nào.

## 3. Kết quả theo tầng

| Tầng | Kết quả |
|---|---|
| Unit + integration + hồi quy (`python -m pytest -q`) | **249 passed**, 162 subtests passed (2.36 s), gồm `tests/test_system_integration.py` |
| E2E trình duyệt (Cursor browser, CDP) | Đạt các mục ở mục 5 |
| Bảo mật cơ bản | Đạt (mục 6) |
| Benchmark | Đã đo (mục 7) |
| Đánh giá `final_test` thật | **NOT RUN** (blocker D) |

## 4. Thay đổi trong allowlist

- `main.py`: endpoint `/api/export-results`, kiểm tra session/TTL/budget, validation chặt, lỗi an toàn, `debug=False`, host `127.0.0.1`.
- `templates/index.html`, `static/js/app.js`, `static/css/style.css`: nút export tối thiểu và sửa lỗi frontend (bug 1 và 2 bên dưới).
- Mới: `tests/test_system_integration.py`, `scripts/run_final_evaluation.py`, báo cáo này, artifact trong `results/phase_e/`.

Export ZIP chứa: `mask_raw.png`, `mask_median.png`, `mask_morph.png`, `segmented.png`, `config.json`, `run.json`, `metrics.json`, `metrics.csv` (UTF-8-SIG, chống CSV injection). Có GT thì thêm `visualization.png`. Không có GT thì metrics ghi N/A. Export với `run_id` không khớp run hiện tại trả HTTP 409.

## 5. E2E trình duyệt (số thực tế)

Ảnh thử 192×128 gồm 6 ô 64×64: đỏ, lục, lam, trắng, đen, xám. Mỗi ô có 4096 pixel.

| Kịch bản | Kết quả |
|---|---|
| Red (Hue 2 đoạn) | Chỉ ô đỏ có pixel trắng (4096) |
| Hue khác (green, blue) | Chỉ ô tương ứng (4096) |
| Mode sv (white, black, gray) | Chỉ ô tương ứng (4096) |
| 15 preset | Màu có trong ảnh khớp ô đúng. Các preset trung gian (cam, tím, ...) cho 0 pixel trên ảnh màu thuần, đúng kỳ vọng |
| Không GT | Hiện `❌ Vui lòng chọn Ground Truth Mask`, không có metrics |
| Morphology kernel chẵn (4) | Hiện `❌ morphology.kernel_size phải là số lẻ, nhận: 4 (không tự cộng 1)`, `run_id` không đổi |
| Controls C | Đổi checkbox Opening: banner pending hiện (`block`). Sau Áp dụng: ẩn (`none`), chuỗi áp dụng `Closing ×1 → Opening ×1; kernel 5×5 ellipse` |
| Response đảo thứ tự | Request 1 (đỏ) bị làm trễ 1200 ms, request 2 (lục) xong trước. UI chỉ hiển thị kết quả lục (ô lục 4096 pixel, các ô khác 0), `run_id` = 2 |
| GT round-trip | GT là ô lục. TP 4088, FP 0, FN 8, IoU 99.80%, F1 0.9990 (8 pixel FN do median/morphology ở biên) |
| Export round-trip | HTTP 200, ZIP hợp lệ (`PK`), 2388 byte, đủ 9 file như mục 4. `run_id` cũ (run−1) trả 409 |

Hạn chế: thư mục `screens/` trống, tôi không lưu ảnh chụp màn hình. Bằng chứng là số liệu đọc trực tiếp từ DOM/CDP ở trên, không phải ảnh chụp. Nếu cần ảnh, chụp thủ công theo các bước ở mục 9.

## 6. Bảo mật và vận hành

- Server chỉ bind `127.0.0.1:5000`, `debug=False` (`main.py` dòng 1458).
- Tên file upload chứa `..`/`evil` được làm sạch, file lưu có tiền tố session (xem `it_uploads/`).
- Test integration phủ path traversal, CSV injection, GT sai định dạng, session isolation/TTL/budget, metrics không stale sau run mới.
- Server thử nghiệm đã tắt (PID 32112), cổng 5000 không còn lắng nghe.

## 7. Benchmark (warm-up + 5 lượt đo, rồi 10 lượt liên tiếp)

| Kích thước | Upload (mean/median) | Process (mean/median) | 10 lượt liên tiếp (process) | RSS trước → sau |
|---|---|---|---|---|
| 512×512 | 26.7 / 26.9 ms | 7.40 / 6.94 ms | 6.29–7.36 ms | 70.0 → 71.4 MiB (+1.3) |
| 1152×868 (~1 MP) | 64.3 / 64.3 ms | 21.8 / 21.8 ms | 20.71–22.14 ms | 74.7 → 76.0 MiB (+1.3) |

`peak_working_set` không đo được (null). RSS đo bằng `psapi.GetProcessMemoryInfo` vì không có `psutil`. Sau mỗi case `sessions_left = 0`.

## 8. Bug log

| # | Lỗi | Nguyên nhân | Sửa | Retest |
|---|---|---|---|---|
| 1 | Banner "Morphology không còn khớp" luôn hiện sau khi Áp dụng | `appliedMorphKey` so sánh bằng `JSON.stringify` nhưng server trả key theo thứ tự khác UI | Thêm `morphCanonicalKey` (thứ tự cố định), dùng ở `appliedMorphKey` và `morphUpdatePending` | `pending_after_apply = none` |
| 2 | Lỗi 400 từ server (kernel chẵn) bị bỏ, UI không hiện lỗi | Response lỗi không có `request_id` nên bị coi là response cũ | Chỉ yêu cầu khớp `request_id` với response thành công | Thông báo lỗi hiện, `run_id` không đổi |
| 3 | `rss: null` trong benchmark | Không có `psutil` trên Python 3.14 | Dùng `ctypes` + `psapi` | RSS được ghi |

Không còn bug critical mở.

## 9. NOT RUN và hướng dẫn thủ công

- **`final_test` thật**: chờ Phase D. Sau khi D có freeze `READY` với `final_test` không rỗng, chạy `python scripts/run_final_evaluation.py`. Script xác minh hash freeze, dùng config đã khóa, không tuning.
- **Ảnh chụp màn hình E2E**: chạy `python main.py`, mở `http://127.0.0.1:5000`, tải ảnh, chọn từng preset, Áp dụng, chụp màn hình vào `results/phase_e/<run_id>/screens/`.
- **Peak working set**: đo thủ công bằng Task Manager hoặc `psutil` khi có.

## 10. Acceptance Criteria

| Tiêu chí | Trạng thái |
|---|---|
| Traceability yêu cầu/route | Đạt (qua `tests/test_system_integration.py`) |
| Export dùng chung, đúng run, UTF-8-SIG, chống injection/traversal | Đạt |
| Validation GT, không metrics stale, session isolation/TTL/budget | Đạt |
| Integration + hồi quy | Đạt (249 passed) |
| E2E trình duyệt | Đạt (không có ảnh chụp, xem mục 5) |
| Benchmark 512² và ~1 MP | Đạt (trừ peak working set) |
| Đánh giá `final_test` thật | **KHÔNG ĐẠT / NOT RUN** (blocker D) |
| Không còn blocker/critical | **Không**: còn blocker Phase D |

## 11. Final File Integrity Check

So sánh 204 file trong `pre_snapshot.csv` với hiện tại (SHA-256), không file nào bị mất:

- Đổi, trong allowlist: `main.py`, `static/js/app.js`, `templates/index.html`.
- Đổi ngoài allowlist: `results/median_comparison/pytest_check/metrics.csv` và `summary.json`. Hai file này nằm trong thư mục bị `.gitignore` (`results/`) và do test có sẵn `tests/test_median.py` (dòng 263) ghi lại khi chạy pytest. Đây là side effect của test, không phải do tôi sửa tay. Nội dung được tạo lại tự động.
- Không đổi: `data/dataset_freeze.json` (`582235b4…5fd7`), `data/dataset_manifest.csv` (`EA9DA29B…41CC`), dataset, GT, Excel, tài liệu Phase A–D.
- Không xóa, đổi tên, di chuyển file. Không commit, không push.

**Đã DỪNG sau Phase E, không chuyển sang Phase F.**
