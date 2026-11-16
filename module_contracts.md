# Hợp đồng giao diện giữa các module (Module Contracts)

Tài liệu này ghi lại **quy ước dữ liệu** và **chữ ký hàm** mà mọi module trong
dự án phải tuân thủ, để các thành viên có thể ghép module mà không phải sửa
lại code của nhau.

Nguồn chuẩn: `README.md` (mục *Quy Ước Dữ Liệu*), `docs/MEMBER_ASSIGNMENT.md`
và các module hiện có trong `src/`.

---

## 1. Quy ước dữ liệu chung

| Loại dữ liệu | Kiểu | Shape | Giá trị |
|---|---|---|---|
| Ảnh đầu vào | `np.ndarray`, `uint8` | `(H, W, 3)` | BGR (thứ tự kênh OpenCV) |
| Ảnh HSV | `np.ndarray`, `uint8` | `(H, W, 3)` | H: 0–179, S: 0–255, V: 0–255 |
| **Mask** | `np.ndarray`, `uint8` | `(H, W)`, 1 kênh | **chỉ `0` (nền) và `255` (đối tượng)** |

Quy tắc bắt buộc cho mọi mask trong dự án:

1. `mask.ndim == 2` — không dùng mảng 3 kênh cho mask.
2. `mask.dtype == np.uint8`.
3. `set(np.unique(mask)) ⊆ {0, 255}` — tuyệt đối không dùng quy ước `0/1`
   cho mask trong pipeline.
4. Mọi hàm xử lý mask **không được mutate** mảng đầu vào.
5. Mọi hàm xử lý mask **giữ nguyên** `(H, W)` của ảnh đầu vào.
6. Kiểm tra đầu vào phải ném `ValueError` (giá trị sai) hoặc `TypeError`
   (sai kiểu) kèm thông báo rõ ràng.

---

## 2. Hợp đồng từng module

### 2.1 `src/data_loader.py` — Anh Quân

```python
from src.data_loader import DataLoader

loader = DataLoader(images_dir, ground_truth_dir, metadata_path)
image_bgr, gt_mask = loader.load_image_gt_pair(img_path, gt_path)
```

* `load_image(path)` → `(H, W, 3)` uint8 BGR.
* `load_ground_truth(path)` → `(H, W)` uint8, đã nhị phân hóa 0/255.
* `load_image_gt_pair(img, gt)` → cặp ảnh + mask, ném `ValueError` nếu lệch kích thước.
* `build_dataset()` → danh sách cặp `(img_path, gt_path)` có sẵn trên đĩa.

### 2.2 `src/hsv_segment.py` — Mạnh Quân

```python
from src.hsv_segment import HSVSegmenter

segmenter = HSVSegmenter(config)          # config: hue_ranges / saturation / value
mask_raw, image_hsv = segmenter.segment(image_bgr)
```

* `bgr_to_hsv(image_bgr)` → `(H, W, 3)` uint8 HSV.
* `create_mask(image_hsv)` → mask `(H, W)` uint8 0/255.
* `segment(image_bgr)` → `(mask_raw, image_hsv)`.

### 2.3 `src/median_filter.py` — Anh Tuấn

```python
from src.median_filter import apply_median_filter, MedianFilter

mask_median = apply_median_filter(mask_raw, kernel_size=3)   # hàm chuẩn
mask_median = MedianFilter(kernel_size=5).filter(mask_raw)   # API lớp (tương thích)
```

* `apply_median_filter(mask_raw: np.ndarray, kernel_size: int = 3) -> np.ndarray`
  — hàm chuẩn của nhóm. Kiểm tra đầu vào nghiêm ngặt, trả về mask `(H, W)`
  uint8 chỉ chứa 0/255, không mutate đầu vào.
* `median_filter(mask_raw, kernel_size=3)` — alias của hàm trên.
* `compare_kernels(mask_raw, kernel_sizes=(3, 5, 7), ground_truth=None)` →
  dict `{'kernels': {...}, 'metrics': {...}}` để so sánh các kernel.
* `MedianFilter(kernel_size=5)` — lớp giữ nguyên API cũ cho `main.py` và
  `experiment.py`: `filter(mask)`, `filter_with_comparison(mask)`,
  `set_kernel_size(k)`, `get_kernel_size()`.
* Quy tắc kernel: số nguyên, lẻ, `3 <= kernel_size <= 31` (`bool` bị từ chối).
* Ngoại lệ: `ValueError` cho mask `None`/rỗng/sai số chiều/giá trị ngoài
  `{0, 255}` và kernel `< 3`, chẵn hoặc `> 31`; `TypeError` cho mask không phải
  `np.ndarray`, sai `dtype` và kernel không phải số nguyên.

### 2.4 `src/morphology.py` — Quốc Anh

```python
from src.morphology import MorphologyOperator

operator = MorphologyOperator(kernel_size=5, kernel_shape='ellipse')
mask_out = operator.apply_sequence(mask_median, [('close', {'iterations': 1})])
```

### 2.5 `src/evaluation.py` — Hoàn

```python
from src.evaluation import SegmentationEvaluator

metrics = SegmentationEvaluator().compute_metrics(pred_mask, gt_mask)
```

Trả về `TP, TN, FP, FN, pixel_accuracy, iou, precision, recall, f1,
specificity`.

### 2.6 `src/experiment.py` — Hoàn

```python
from src.experiment import ExperimentRunner

runner = ExperimentRunner(results_dir="results")
results = runner.run_batch_experiments(image_files, configs)
```

---

## 3. Luồng pipeline chuẩn

```
Loader → HSV → Median Filter → Morphology → Evaluation
```

Mỗi bước nhận mask `(H, W)` uint8 0/255 và trả về mask cùng định dạng, nên
các module có thể thay thế lẫn nhau mà không cần chuyển đổi kiểu dữ liệu.

## 4. Quy ước đặt tên

* Tên hàm: `verb_noun` (snake_case), ví dụ `apply_median_filter`,
  `compute_iou`, `load_ground_truth`.
* Tên lớp: `PascalCase`, ví dụ `HSVSegmenter`, `MedianFilter`,
  `SegmentationEvaluator`.
* Tên module: `snake_case`, ví dụ `median_filter.py`.
* Tên biến cục bộ/đường dẫn: `snake_case`; hằng số: `UPPER_SNAKE_CASE`.
* Tài liệu: docstring tiếng Việt, mô tả `Args`, `Returns`, `Raises`.
