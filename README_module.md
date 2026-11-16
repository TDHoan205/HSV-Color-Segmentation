# Hướng dẫn tích hợp module Median Filter (Anh Tuấn)

Tài liệu này dành cho **Hoàn** (nhóm trưởng) để ghép module
[`src/median_filter.py`](src/median_filter.py) vào `main.py` và
`experiment.py`.

---

## 1. Vị trí của module trong pipeline

```
DataLoader → HSVSegmenter → Median Filter → MorphologyOperator → SegmentationEvaluator
   (ảnh BGR)     (mask_raw)     (mask_median)      (mask_morph)          (chỉ số)
```

Median Filter đứng **ngay sau bước phân đoạn màu HSV** và **trước bước hình
thái học**, vì:

* `HSVSegmenter.create_mask()` sinh mask bằng cách so sánh ngưỡng trên từng
  kênh, nên trên ảnh nhiễu nặng (sensor nhiễu, ánh sáng yếu) mask thô xuất
  hiện nhiều pixel lẻ (nhiễu muối tiêu) và nhiều lỗ hổng nhỏ bên trong vùng
  đối tượng.
* Lọc trung vị là bộ lọc **phi tuyến, bảo toàn biên**, không làm mờ biên như
  lọc trung bình, nên phù hợp để làm sạch mask mà vẫn giữ được đường viền đối
  tượng.
* Sau khi lọc trung vị, `MorphologyOperator` (Opening/Closing) xử lý tiếp các
  lỗi hình thái còn lại; đặt sai thứ tự sẽ khiến Closing "vá" lại những lỗ
  nhiễu mà Median Filter đã loại bỏ.

---

## 2. Chữ ký hàm và kiểu dữ liệu

### Hàm chuẩn (khuyến nghị dùng)

```python
from src.median_filter import apply_median_filter

mask_median = apply_median_filter(mask_raw, kernel_size=3)
```

| Thành phần | Kiểu | Ghi chú |
|---|---|---|
| `mask_raw` | `np.ndarray` | Bắt buộc 2 chiều `(H, W)`, `dtype == np.uint8`, chỉ chứa `0` và `255`. |
| `kernel_size` | `int` | Số lẻ, `3 <= kernel_size <= 31`. Mặc định `3`. `bool` bị từ chối. |
| **Trả về** | `np.ndarray` | `(H, W)`, `uint8`, chỉ chứa `0`/`255`. Mảng đầu vào **không bị thay đổi**. |

Hàm dùng `cv2.medianBlur(mask_raw, kernel_size)` và chuẩn hóa lại đầu ra về
đúng quy ước mask của nhóm.

### Hàm phụ trợ

```python
from src.median_filter import compare_kernels

result = compare_kernels(mask_raw, kernel_sizes=(3, 5, 7), ground_truth=gt_mask)
result['kernels'][5]   # mask sau khi lọc 5x5
result['metrics'][5]   # {'changed_pixels', 'changed_ratio', 'removed_pixels',
                       #  'added_pixels', 'object_pixels', 'iou', ...}
```

### API lớp (giữ nguyên cho code đang chạy)

```python
from src.median_filter import MedianFilter

median_filter = MedianFilter(kernel_size=5)
mask_median = median_filter.filter(mask_raw)
```

Lớp `MedianFilter` **không đổi API** so với bản trước nên `main.py` và
`experiment.py` hiện tại chạy được nguyên trạng. Lớp dùng chung hàm kiểm tra
đầu vào với hàm chuẩn, nên mọi mask không hợp lệ đều bị báo lỗi ngay.

---

## 3. Ngoại lệ có thể ném ra

| Tình huống | Ngoại lệ | Thông báo |
|---|---|---|
| `mask_raw` là `None` | `ValueError` | "mask_raw không được phép là None…" |
| `mask_raw` không phải `np.ndarray` | `TypeError` | "mask_raw phải là numpy.ndarray, nhận: list" |
| `mask_raw` rỗng (`size == 0`) | `ValueError` | "mask_raw không được phép rỗng…" |
| `mask_raw` nhiều kênh (`ndim == 3`) | `ValueError` | "mask_raw phải là mảng 2 chiều (ndim == 2…), nhận shape (H, W, 3)" |
| `mask_raw` sai `dtype` (`float32`, `int32`…) | `TypeError` | "mask_raw phải có dtype uint8, nhận: float32" |
| `mask_raw` chứa giá trị ngoài `{0, 255}` (ví dụ `128`) | `ValueError` | "mask_raw phải là mask nhị phân chỉ chứa giá trị 0 và 255…" |
| `mask_raw` dùng quy ước `0/1` | `ValueError` | "mask_raw dùng quy ước 0/1, trong khi dự án yêu cầu 0/255…" |
| `kernel_size` chẵn (`2`, `4`) | `ValueError` | "kernel_size phải là số lẻ, nhận: 4" |
| `kernel_size < 3` (`1`, `0`, `-3`) | `ValueError` | "kernel_size phải >= 3, nhận: 1" |
| `kernel_size > 31` (`33`, `51`) | `ValueError` | "kernel_size quá lớn (tối đa 31), nhận: 33" |
| `kernel_size` không phải số nguyên (`3.0`, `'3'`) | `TypeError` | "kernel_size phải là số nguyên (int), nhận: float" |
| `kernel_size` là `bool` | `TypeError` | "kernel_size phải là số nguyên (int), không phải bool." |

> Lưu ý tích hợp: `main.py` hiện đang tự sửa kernel chẵn thành lẻ
> (`if median_kernel % 2 == 0: median_kernel += 1`). Có thể giữ nguyên, hoặc
> chuyển sang kiểm tra nghiêm ngặt để báo lỗi cho người dùng web.

---

## 4. Cách gọi trong `main.py`

Đoạn hiện tại trong `main.py` (dòng khoảng 150) **không cần sửa**:

```python
from src.median_filter import MedianFilter

# Trong @app.route('/api/process')
median_kernel = int(data.get('median_kernel', 5))
if median_kernel % 2 == 0:
    median_kernel += 1
median_filter = MedianFilter(median_kernel)
mask_median = median_filter.filter(mask_raw)
```

Nếu muốn dùng hàm chuẩn (dễ kiểm tra đầu vào hơn):

```python
from src.median_filter import apply_median_filter

mask_median = apply_median_filter(mask_raw, kernel_size=median_kernel)
```

## 5. Cách gọi trong `experiment.py`

Đoạn hiện tại (dòng khoảng 66) cũng **không cần sửa**:

```python
median_config = config.get('median', {})
kernel_size = median_config.get('kernel_size', 5)
median_filter = MedianFilter(kernel_size)
mask_median = median_filter.filter(mask_raw)
```

Có thể bổ sung so sánh nhiều kernel trong cùng một lượt chạy:

```python
from src.median_filter import compare_kernels

comparison = compare_kernels(mask_raw, kernel_sizes=(3, 5, 7), ground_truth=gt_mask)
for kernel_size, metrics in comparison['metrics'].items():
    print(kernel_size, metrics['iou'], metrics['changed_pixels'])
```

---

## 6. Lệnh chạy kiểm thử và sinh ảnh so sánh

```bash
# 1) Sinh lại bộ ảnh kiểm thử (tất định, seed cố định)
python tests/fixtures/median/generate_fixtures.py

# 2) Chạy unit test của module Median Filter
python -m pytest tests/test_median.py -v
python tests/test_median.py          # chạy trực tiếp, không cần pytest

# 3) Chạy toàn bộ test của dự án
python -m pytest tests/ -v

# 4) Sinh ảnh so sánh 3x3 / 5x5 / 7x7 và bảng số liệu
python scripts/run_median_comparison.py
```

Đầu ra của bước 4:

```
results/median_comparison/
├── <tên ảnh>/
│   ├── mask_raw.png          # mask thô từ HSV
│   ├── mask_k3.png           # sau Median 3x3
│   ├── mask_k5.png           # sau Median 5x5
│   ├── mask_k7.png           # sau Median 7x7
│   └── comparison.png        # ảnh ghép: Thô | 3x3 | 5x5 | 7x7
├── fixtures/
│   └── <tên fixture>/…       # tương tự cho các trường hợp tổng hợp
├── metrics.csv               # số liệu từng ảnh × từng kernel
└── summary.json              # số liệu tổng hợp + cấu hình + phiên bản
```

Bản tổng hợp để chèn vào báo cáo nằm ở
[`report/figures/median_comparison.png`](report/figures/median_comparison.png);
phần báo cáo đầy đủ ở [`report/median.md`](report/median.md) và
[`report/median_theory.md`](report/median_theory.md).

---

## 7. Khuyến nghị chọn kernel

| Tình huống | Kernel khuyến nghị |
|---|---|
| Mask từ HSV trên ảnh sạch (đa số bộ dữ liệu của nhóm) | `3×3` — thay đổi vài chục pixel, không làm mất chi tiết |
| Ảnh nhiễu sensor mạnh, nhiễu muối tiêu rời rạc | `3×3` hoặc `5×5` |
| Nhiễu thành cụm (vùng nhiễu 2–3 pixel) | `5×5` |
| Vùng đối tượng nhỏ, cần giữ chi tiết mảnh | `3×3` |
| Mặc định của pipeline web hiện tại | `5×5` (giữ nguyên như `main.py`) |

Chi tiết số liệu và phân tích chi tiết nét mảnh với kernel 7×7 nằm trong
[`report/median.md`](report/median.md).

---

## 8. Danh sách sản phẩm bàn giao

| File | Nội dung |
|---|---|
| `src/median_filter.py` | Module chính: `apply_median_filter`, `compare_kernels`, lớp `MedianFilter` (tương thích ngược) |
| `tests/test_median.py` | 22 unit test (pytest và `python tests/test_median.py`) |
| `tests/fixtures/median/generate_fixtures.py` | Script sinh bộ ảnh kiểm thử tất định |
| `tests/fixtures/median/*.png` | 5 ảnh kiểm thử + `README.md` mô tả |
| `scripts/run_median_comparison.py` | Script chạy thực nghiệm, sinh ảnh so sánh và bảng số liệu |
| `report/median_theory.md` | Tài liệu lý thuyết (nguyên lý, ví dụ tính tay 3×3) |
| `report/median.md` | Báo cáo module (kịch bản, bảng số liệu, khuyến nghị) |
| `module_contracts.md` | Hợp đồng giao diện chung của dự án |
| `README_module.md` | Tài liệu này |
