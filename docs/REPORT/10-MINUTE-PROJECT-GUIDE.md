# Hướng dẫn 10 phút: Tách và nhận biết màu đối tượng trong không gian HSV

> Tài liệu tạo từ việc đọc code thật và chạy kiểm thử chỉ-đọc ngày 16/11/2026 (commit `46ac43e`).
> Mọi số liệu bên dưới lấy từ code hoặc từ lần chạy thực tế. Chỗ nào chưa chạy được sẽ ghi rõ.

---

## 1. Chương trình làm gì (30 giây)

Web app Flask nhận một ảnh màu, tìm các pixel có màu đỏ (mặc định), tạo **mặt nạ (mask)** đen/trắng
(trắng = đối tượng), làm sạch mask bằng **Median Filter** rồi **Morphology**, và (nếu có ảnh
Ground Truth) tính **Pixel Accuracy, IoU, Precision, Recall, F1, Specificity**.

- **Input:** 1 ảnh (jpg/jpeg/png/bmp/tiff, tối đa 50MB) + các thanh trượt HSV + kernel + checkbox; tùy chọn 1 ảnh Ground Truth.
- **Output:** 3 mask (thô, sau median, sau morphology), bảng chỉ số, ảnh so sánh TP/FP/FN, file PNG mask tải về.

**Thứ tự xử lý** (đúng như `main.py`, hàm `process_image`):

```
Ảnh BGR → HSV → inRange (H,S,V) → mask_raw → Median → mask_median → Morphology → mask_morph → (so với GT) → chỉ số
```

---

## 2. Vai trò từng file

| File | Vai trò |
|---|---|
| `main.py` | Server Flask, các API, nối các module lại |
| `src/hsv_segment.py` | `HSVSegmenter`: BGR→HSV, tạo mask bằng `cv2.inRange` |
| `src/median_filter.py` | `MedianFilter`, `apply_median_filter`, `compare_kernels` (dùng `cv2.medianBlur`) |
| `src/morphology.py` | `MorphologyOperator`: erode, dilate, open, close, `apply_sequence` |
| `src/evaluation.py` | `SegmentationEvaluator`: ma trận nhầm lẫn, các chỉ số, ảnh visualization |
| `src/data_loader.py` | `DataLoader`: nạp ảnh + GT, kiểm tra dữ liệu, đọc `metadata.csv` |
| `src/experiment.py` | `ExperimentRunner`: chạy nhiều cấu hình, xuất CSV (chỉ dùng bằng code, không có nút trên UI) |
| `templates/index.html`, `static/js/app.js` | Giao diện 6 tab và JavaScript gọi API |
| `data/images`, `data/ground_truth`, `data/metadata.csv` | Dữ liệu: 27 ảnh, 10 GT, 10 dòng metadata |
| `tests/` | 5 file test |

---

## 3. HSV cho người mới

- **BGR/RGB:** màu = pha 3 màu (xanh dương, xanh lá, đỏ). Khi trời tối hoặc có bóng, cả 3 số đổi cùng lúc nên khó nói "đây là màu đỏ".
- **HSV:** tách riêng 3 ý:
  - **H (Hue, sắc độ):** "đây là màu gì". OpenCV dùng **0–179** (code chấp nhận cận trên 180).
  - **S (Saturation, độ bão hòa):** màu đậm hay nhạt. 0 = xám/trắng, 255 = màu rực. **0–255**.
  - **V (Value, độ sáng):** sáng hay tối. 0 = đen. **0–255**.
- **Vì sao dùng HSV:** muốn tìm "màu đỏ" chỉ cần lọc H, rồi dùng S và V để loại vùng xám/tối. Dễ hơn nhiều so với lọc BGR.
- **Vì sao có 2 khoảng Hue:** đỏ nằm ở hai đầu vòng màu (gần 0 và gần 180), nên cần `[0,10]` **và** `[170,180]`. Kết quả hai khoảng được OR với nhau (`cv2.bitwise_or` trong `create_mask`), rồi AND với S và V.

---

## 4. Bảng thông số (đọc từ code hiện tại)

### 4.1 HSV (tab "Phân Đoạn HSV", `index.html` + `main.py`)

| Thông số | Ý nghĩa | Phạm vi trên UI | Mặc định | Tăng/giảm thì sao |
|---|---|---|---|---|
| `h_min_1` / `h_max_1` | Khoảng Hue thứ nhất | 0–180 | 0 / 10 | Mở rộng khoảng → nhận thêm màu cam; thu hẹp → chặt hơn, dễ sót đối tượng |
| `h_min_2` / `h_max_2` | Khoảng Hue thứ hai (đầu kia của màu đỏ) | 0–180 | 170 / 180 | Mở rộng → nhận thêm màu hồng/tím đỏ |
| `s_min` / `s_max` | Độ bão hòa | 0–255 | 100 / 255 | Tăng `s_min` → loại vùng nhạt, trắng, xám (nhưng đối tượng bị cháy sáng sẽ mất) |
| `v_min` / `v_max` | Độ sáng | 0–255 | 100 / 255 | Tăng `v_min` → loại vùng tối (nhưng ảnh thiếu sáng sẽ mất đối tượng) |

Ví dụ: ảnh `img_07` (đỏ, thiếu sáng, V trung bình khoảng 85) có V dưới 100 nên mặc định không bắt được. Hạ `v_min` xuống thấp hơn thì bắt được.

Quy tắc kiểm tra trong `HSVSegmenter._validate_range`: mỗi khoảng phải là số nguyên, `0 ≤ min ≤ max ≤ 180` (H) hoặc `≤ 255` (S, V). Nếu vi phạm, server trả lỗi.

### 4.2 Median Filter (tab "Lọc Median")

| Thông số | Ý nghĩa | UI | Mặc định | Ảnh hưởng |
|---|---|---|---|---|
| `median_kernel` | Cửa sổ vuông; mỗi pixel lấy giá trị **trung vị** của vùng lân cận | 3, 5, 7, 9 | **5** | Lớn hơn → khử nhiễu mạnh hơn nhưng bo tròn, làm mất đối tượng nhỏ |

- Backend tự cộng 1 nếu nhận số chẵn (`main.py`).
- Module `median_filter.py` cho phép số lẻ **3–31** (`MAX_KERNEL_SIZE = 31`), mặc định lớp là 5.
- Vì mask chỉ có 0/255, trung vị cho ra 0 hoặc 255, không tạo xám. Điểm trắng lẻ loi (muối tiêu) bị xóa.

### 4.3 Morphology (tab "Morphology")

| Thông số | Ý nghĩa | UI | Mặc định | Ảnh hưởng |
|---|---|---|---|---|
| `morph_kernel` | Kích thước phần tử cấu trúc | 3, 5, 7, 9 | **5** | Lớn hơn → lấp lỗ/xóa nhiễu to hơn, nhưng làm biến dạng viền |
| Kernel shape | Hình dạng phần tử cấu trúc | **Không có trên UI**; `main.py` cố định `'ellipse'` | `ellipse` | Code hỗ trợ `rect`, `ellipse`, `cross` (dùng được qua `ExperimentRunner`) |
| `use_closing` | Closing = Dilation rồi Erosion, lấp lỗ đen nhỏ trong đối tượng | Checkbox | **Bật** | |
| `use_opening` | Opening = Erosion rồi Dilation, xóa đốm trắng nhỏ | Checkbox | **Tắt** | |
| `iterations` | Số lần lặp | Không có trên UI | 1 (cố định trong `main.py`) | |

Thứ tự khi bật cả hai: **Closing trước, Opening sau**. Nếu tắt cả hai, `mask_morph` = `mask_median`.
Erosion/Dilation đơn lẻ có trong `morphology.py` (`erode`, `dilate`) nhưng **không có checkbox** trên UI.
- Erosion: co đối tượng. Dilation: nở đối tượng.

### 4.4 Chỉ số đánh giá (`evaluation.py`)

- TP: mask trắng, GT trắng. TN: cả hai đen. FP: mask trắng, GT đen. FN: mask đen, GT trắng.
- **Pixel Accuracy = (TP + TN) / (TP + TN + FP + FN)**
- **IoU = TP / (TP + FP + FN)**
- Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2PR/(P+R); Specificity = TN/(TN+FP).
- Ảnh visualization: xanh lá = TP, đỏ = FP, xanh dương = FN.
- **Ground Truth** là mask do người vẽ, xem như đáp án đúng. Code nhị phân hóa ở ngưỡng 127 (và `evaluation.py` coi mọi giá trị > 0 là đối tượng).
- Lưu ý khi vấn đáp: Pixel Accuracy dễ bị đẹp giả khi đối tượng nhỏ (nền chiếm phần lớn). Vì vậy nên đọc kèm IoU.

---

## 5. Hướng dẫn sử dụng từng bước

1. Mở PowerShell tại thư mục project, kích hoạt môi trường: `.\.venv\Scripts\Activate.ps1`
2. Chạy: `python main.py`
3. Mở trình duyệt: `http://localhost:5000` (server cũng lắng nghe `0.0.0.0:5000`, chế độ `debug=True`).
4. Tab **Tải Ảnh**: bấm hoặc kéo thả ảnh. Thành công sẽ hiện kích thước ảnh.
5. Tab **Phân Đoạn HSV**: chỉnh 8 thanh trượt (H1, H2, S, V).
6. Tab **Lọc Median** và **Morphology**: chọn kernel, tick Closing/Opening. **Các tab này không tự chạy.**
7. Quay lại tab HSV, bấm **"Xử Lý Ảnh"**. Mọi thông số ở cả 3 tab được gửi đi cùng lúc. Ba ảnh mask (Raw, Median, Morphology) hiện ngay bên dưới.
8. Tab **Đánh Giá**: chọn ảnh Ground Truth **cùng kích thước** với ảnh gốc, bấm "Đánh Giá". Kết quả gồm 6 chỉ số, ma trận TP/FP/FN/TN và ảnh visualization. Chỉ số tính trên mask cuối (`mask_morph`).
9. Tab **Kết Quả**: tải mask thô, median hoặc cuối dạng PNG.

Ghi chú: để lấy ảnh/GT có sẵn, dùng ảnh `img_01`–`img_10` trong `data/images` và `data/ground_truth` (cùng tên gốc).

**Chạy thực nghiệm nhiều cấu hình:**
- `ExperimentRunner` (`src/experiment.py`) có `run_batch_experiments`, `save_results_csv`, `print_summary`. **Không có nút trên giao diện.**
- Hàm `main()` trong `experiment.py` **tự tạo và ghi** ảnh `test_01.png` vào `data/`, nên **đừng chạy trực tiếp** `python src/experiment.py` nếu không muốn đổi dữ liệu. Hãy import `ExperimentRunner` và truyền cặp ảnh/GT thật.
- `scripts/run_median_comparison.py` có `run_comparison` để so sánh kernel median (ghi file vào `results/`).

---

## 6. Kết quả kiểm thử đã chạy thật

**Môi trường:** Python 3.14.6 trong `.venv`; Flask 3.1.3, OpenCV 5.0.0.93, NumPy 2.5.4, pandas 3.1.1, Pillow 13.0.0, Werkzeug 3.1.9, openpyxl 3.1.5. **`pytest` chưa được cài** trong `.venv` (dù có trong `requirements.txt`), nên dùng `unittest`.

| Nhóm | Kết quả |
|---|---|
| `test_hsv` + `test_evaluation` + `test_morphology` + test median thuần (`TestMedianFilterCorrectness`, `Validation`, `KernelComparison`) | **107 test PASS** |
| `tests.test_data.TestRealDataset` | **14 test chạy: 10 PASS, 4 FAIL** (xem dưới) |
| `TestMedianFilterExperiment` (test median có ghi file) | **SKIP có chủ đích**: ghi vào `results/`, vi phạm quy tắc chỉ-đọc |
| `tests.test_data.TestDataLoader` | **Không chạy**: tạo thư mục tạm ngoài project; không cần cho audit |
| Flask `test_client`: `GET /` | 200; `GET /api/health` → `running`; `POST /api/process` session lạ → 400 |
| `/api/upload`, `/api/evaluate`, `/api/download-mask` qua HTTP | **Chưa chạy**: upload ghi file vào `uploads/` |
| Giao diện trên trình duyệt | **Chưa chạy**; chỉ đọc `index.html` và `app.js`. Chưa kiểm chứng bằng mắt |

**4 test FAIL ở `TestRealDataset`: nguyên nhân là dữ liệu, không phải thuật toán.**
`data/images` có 27 ảnh nhưng chỉ có 10 ảnh Ground Truth và 10 dòng `metadata.csv`. 17 ảnh chụp thật (tên kiểu `2025…jpg`, `2026…jpg`) không có GT và không có metadata. Các test đòi mọi ảnh phải có đủ nên báo lỗi (ví dụ "10 != 27").

**Luồng pipeline đã chạy trong bộ nhớ (không ghi file)** trên 10 ảnh có GT, cấu hình: median 5, morph 5, `ellipse`, chỉ Closing.

| Cấu hình HSV | Pixel Accuracy TB (mask cuối) | IoU TB |
|---|---|---|
| Mặc định (H 0–10 & 170–180, S≥100, V≥100) | 0.8951 | 0.7135 |
| Chặt hơn (S≥120, V≥120) | 0.8949 | 0.7121 |
| Rộng hơn (H 0–15 & 165–180, S≥80, V≥80) | 0.9041 | 0.8043 |

Với cấu hình mặc định, từng ảnh: `img_01`–`img_05`, `img_09`, `img_10` cho Accuracy ≥ 0.9995 (IoU ≥ 0.995). **Thất bại có thật ở 3 ảnh:**
- `img_06` (nền hồng, Hue ~172 rơi vào khoảng đỏ thứ hai): Accuracy 0.1451, IoU 0.1451. Mask tách nhầm cả nền.
- `img_07` (thiếu sáng, V thấp): IoU 0.0000.
- `img_08` (cháy sáng, S thấp): IoU 0.0000.

Đây là 3 ca khó được ghi sẵn trong `metadata.csv`, dùng để chứng minh vì sao cần chỉnh ngưỡng.

---

## 7. Đối chiếu yêu cầu đề bài

| Yêu cầu | Mức độ | Bằng chứng |
|---|---|---|
| Tạo mask HSV | **Hoàn thành** | `HSVSegmenter.segment/create_mask`; 11 test PASS; UI có 8 thanh trượt |
| Median Filter | **Hoàn thành** | `median_filter.py` (`cv2.medianBlur`); 22 test PASS; UI chọn kernel 3/5/7/9 |
| Morphology làm sạch mask | **Hoàn thành một phần** | Có đủ erode/dilate/open/close (66 test PASS). UI chỉ có Closing/Opening; không có chọn shape, iterations, erosion, dilation |
| So sánh khi đổi ngưỡng màu | **Hoàn thành một phần** | Đổi ngưỡng và xem lại mask được; có `ExperimentRunner` + dữ liệu 10 tình huống. Nhưng **UI không có chức năng so sánh song song nhiều ngưỡng** hay bảng tổng hợp |
| Đánh giá Pixel Accuracy với GT | **Hoàn thành** | `compute_metrics`, 8 test PASS; tab Đánh Giá; GT có cho 10 ảnh |

---

## 8. Các điểm còn thiếu / lỗi, theo mức độ

| Mức | Vấn đề |
|---|---|
| **Trung bình** | 4 test `TestRealDataset` đang FAIL do 17 ảnh thật không có GT/metadata. Cần có GT cho ảnh thật hoặc tách riêng thư mục |
| **Trung bình** | Không có chức năng so sánh nhiều ngưỡng HSV trên giao diện; phải dùng code (`ExperimentRunner`) |
| **Trung bình** | 3/10 ảnh (img_06, img_07, img_08) thất bại với ngưỡng mặc định; cần chỉnh tay |
| **Trung bình** | Chỉ hỗ trợ đúng một màu (Red); `color_name` bị cố định trong `main.py`; chưa có bộ chọn màu |
| **Thấp** | Morphology UI thiếu shape/iterations/erosion/dilation; shape cố định `ellipse` |
| **Thấp** | Thanh trượt cho phép min > max; backend sẽ từ chối và trả thông báo lỗi chung "Lỗi xử lý" |
| **Thấp** | Thanh trượt H cho đến 180, trong khi ảnh OpenCV chỉ tới 179 (180 được code chấp nhận) |
| **Thấp** | Bấm "Xử Lý Ảnh" mới áp dụng thông số median/morph; đổi ở tab khác không tự cập nhật |
| **Thấp** | `session_data` là biến toàn cục trong bộ nhớ, ảnh trong `uploads/` không bị dọn; chạy `debug=True`, `host=0.0.0.0` chỉ phù hợp demo |
| **Thấp** | `/api/get-info` có trong backend nhưng giao diện không gọi |
| **Thấp** | `pytest` chưa cài; `experiment.py main()` tự ghi dữ liệu vào `data/` |
| **Chưa kiểm chứng** | Hành vi thật của UI và API upload/evaluate/download qua trình duyệt (chỉ mới đọc code) |

Kết luận: lõi thuật toán và đánh giá **đạt yêu cầu** và đã test pass. Phần chưa đủ nằm ở giao diện so sánh ngưỡng, độ đầy đủ của UI morphology và dữ liệu ảnh thật chưa có GT.

---

## 9. Vấn đáp nhanh

**Chương trình giải quyết vấn đề gì?** Tự động tách đối tượng theo màu (mặc định đỏ) khỏi ảnh bằng mask HSV, làm sạch mask và đo độ chính xác so với Ground Truth.

**Input/Output?** Vào: ảnh + ngưỡng H/S/V + kernel (+ GT). Ra: mask thô, mask median, mask cuối, các chỉ số, ảnh TP/FP/FN, file PNG.

**Tại sao HSV?** HSV tách màu (H) khỏi độ sáng (V) và độ đậm (S), nên chọn màu ổn định hơn BGR khi ánh sáng thay đổi.

**H, S, V là gì?** H: màu (0–179 trong OpenCV). S: độ đậm nhạt (0–255). V: độ sáng (0–255).

**Vì sao đỏ cần hai khoảng H?** Vì đỏ nằm ở hai đầu thang H: gần 0 và gần 180. Mặc định `[0,10]` và `[170,180]`.

**Median Filter dùng để làm gì?** Khử nhiễu muối tiêu: mỗi pixel lấy trung vị của vùng kernel, nên điểm trắng lẻ bị xóa mà viền ít bị nhòe. Mặc định kernel 5.

**Opening và Closing khác nhau?** Opening = Erosion rồi Dilation: xóa đốm trắng nhỏ bên ngoài. Closing = Dilation rồi Erosion: lấp lỗ đen nhỏ bên trong. UI mặc định chỉ bật Closing.

**Kernel size/shape?** Kích thước càng lớn càng mạnh nhưng biến dạng nhiều hơn. Shape (rect/ellipse/cross) là hình dạng cửa sổ; project dùng ellipse.

**Pixel Accuracy là gì?** Tỉ lệ pixel dự đoán đúng: (TP+TN)/tổng. Vì nền chiếm nhiều pixel nên nên xem thêm IoU = TP/(TP+FP+FN).

**Ground Truth là gì?** Mask chuẩn do người tạo, dùng làm đáp án để chấm kết quả.

**Đổi ngưỡng HSV thì sao?** Ngưỡng rộng: bắt nhiều hơn nhưng dễ lấy nhầm (FP tăng). Ngưỡng hẹp: sạch hơn nhưng dễ sót (FN tăng). Số liệu: trên 10 ảnh, cấu hình rộng cho Accuracy TB 0.9041 và IoU TB 0.8043, mặc định 0.8951 và 0.7135.

**Hạn chế?** Chỉ một màu đỏ; ảnh quá tối, cháy sáng hoặc nền gần màu đối tượng (img_06/07/08) sai; GT chỉ có cho 10 ảnh tổng hợp, 17 ảnh thật chưa có GT; UI chưa so sánh được nhiều ngưỡng cùng lúc.
