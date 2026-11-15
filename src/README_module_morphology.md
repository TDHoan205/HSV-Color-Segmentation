# README Module — `morphology.py`

**Phụ trách:** Quốc Anh (Morphological Operations)
**File module:** `src/morphology.py`

---

## 1. Chức năng

Module thực hiện các **phép toán hình thái học** dùng để làm sạch Mask nhị phân
sau khi phân đoạn HSV và lọc trung vị.

| Phép toán | Công thức | Tác dụng trên Mask (trắng = đối tượng) |
|---|---|---|
| **Erosion** (co) | — | Thu nhỏ vùng trắng, ăn mòn biên vật thể |
| **Dilation** (giãn) | — | Mở rộng vùng trắng, phình biên vật thể |
| **Opening** (mở) | Erosion → Dilation | **Loại bỏ** vùng trắng nhỏ rời rạch (nhiễu) |
| **Closing** (đóng) | Dilation → Erosion | **Lấp kín** lỗ đen nhỏ bên trong vật thể |

Ba phép toán mở rộng: `gradient`, `tophat`, `blackhat`.

## 2. Quy ước

- Mask: **1 kênh, `uint8`, nền = 0, đối tượng = 255** (Quy ước 2 của nhóm).
- Đầu ra **giữ nguyên kích thước H×W** và kiểu `uint8`, giá trị chỉ 0 hoặc 255.
- `kernel_size` phải là **số lẻ dương** (OpenCV yêu cầu kernel lõi có tâm).
- `kernel_shape`: `rect`, `ellipse` (mặc định), `cross`.
- Module **không sửa đổi** Mask đầu vào.

## 3. API

### Khởi tạo

```python
from src.morphology import MorphologyOperator

operator = MorphologyOperator(kernel_size=5, kernel_shape='ellipse')
```

| Tham số | Mặc định | Ràng buộc |
|---|---|---|
| `kernel_size` | `5` | Số lẻ dương → nếu sai sẽ `ValueError` |
| `kernel_shape` | `'ellipse'` | Một trong `rect` / `ellipse` / `cross` |

### Các phương thức

| Hàm | Tham số | Trả về |
|---|---|---|
| `erode(mask, iterations=1)` | Mask đầu vào | Mask sau Erosion |
| `dilate(mask, iterations=1)` | Mask đầu vào | Mask sau Dilation |
| `open(mask, iterations=1)` | Mask đầu vào | Mask sau Opening |
| `close(mask, iterations=1)` | Mask đầu vào | Mask sau Closing |
| `apply_operation(mask, operation, iterations=1)` | Tên phép toán | Mask sau phép toán |
| `apply_sequence(mask, operations)` | Danh sách phép toán | Mask sau cả chuỗi |
| `set_kernel(kernel_size, kernel_shape='ellipse')` | — | Đổi kernel |
| `get_kernel_info()` | — | `dict` gồm `size`, `shape`, `kernel` |
| `set_iterations_adaptive(mask_size, target_reduction=0.2)` | Kích thước mask | Số lần lặp gợi ý |

### Hàm module

```python
from src.morphology import compare_morphology_operations

results = compare_morphology_operations(mask, kernel_size=3)
# -> dict: 'original', 'erode', 'dilate', 'open', 'close'
```

## 4. Ví dụ input / output

```python
import numpy as np
from src.morphology import MorphologyOperator

# Mask 100x100: một hình vuông trắng 20:80 (60x60 = 3600 px)
mask = np.zeros((100, 100), dtype=np.uint8)
mask[20:80, 20:80] = 255

operator = MorphologyOperator(kernel_size=5, kernel_shape='ellipse')

eroded = operator.erode(mask)          # 3600 px -> 3136 px (biên bị ăn mòn)
dilated = operator.dilate(mask)        # 3600 px -> 4088 px (biên nở ra)
opened = operator.open(mask)           # loại vùng trắng nhỏ
closed = operator.close(mask)          # lấp lỗ đen nhỏ

print(eroded.shape, eroded.dtype)       # (100, 100) uint8
```

Kết quả `compare_morphology_operations` trên fixture có lỗ đen 3×3 và đốm trắng 4×4:

| Kernel (ellipse) | Opening loại bỏ | Closing lấp thêm |
|---|---|---|
| 3×3 | 16 px | 8 px |
| 5×5 | 48 px | 18 px |
| 7×7 | 74 px | 18 px |

> **Lưu ý quan trọng:** kernel 3×3 **chưa đủ** để lấp hẳn lỗ 3×3 (chỉ lấp được 4/9 px)
> hay xóa hẳn đốm trắng 4×4 (còn 12/16 px). Cần kernel **≥ 5×5** mới lấp kín và loại sạch.

## 5. Chạy test

```bash
# Chạy riêng module này
python -m unittest tests.test_morphology -v

# Hoặc chạy toàn bộ
python -m unittest discover -s tests -v
```

Bộ test dùng fixture tổng hợp tại `tests/fixtures/morphology/`:

```python
from tests.fixtures.morphology import make_noisy_mask
```

Sinh lại file PNG mẫu:

```bash
python -m tests.fixtures.morphology
```

## 6. Tích hợp vào pipeline

Vị trí của module trong luồng chính:

```
BGR → HSV → Mask thô → Median Filter → Morphology → Đánh giá
                                    ↑
                              morphology.py
```

Cách dùng trong `src/experiment.py` và `main.py`:

```python
operator = MorphologyOperator(kernel_size_morph, kernel_shape)

# Một phép toán
mask_morph = operator.close(mask_median)

# Hoặc chuỗi phép toán
mask_morph = operator.apply_sequence(mask_median, [
    ('close', {'iterations': 1}),
    ('open',  {'iterations': 1}),
])
```

## 7. Xử lý lỗi

| Trường hợp | Hành vi |
|---|---|
| `kernel_size` chẵn hoặc ≤ 0 | `ValueError` — *"Kernel size phải là số lẻ dương"* |
| `kernel_shape` không hỗ trợ | `ValueError` — *"Kernel shape không được hỗ trợ"* |
| `mask` là `None` hoặc rỗng | `ValueError` — *"Mask không hợp lệ"* |
| `operation` không hỗ trợ | `ValueError` — *"Phép toán không được hỗ trợ"* |

Tất cả phép toán đều kiểm tra input trước khi xử lý, trả về `ValueError`
thay vì lỗi runtime không rõ ràng.

## 8. Bất biến toán học (được test bảo đảm)

Với mọi Mask và kernel hợp lệ:

```
Erosion(A) ⊆ A ⊆ Dilation(A)
Opening(A) ⊆ A ⊆ Closing(A)
```

Ngoài ra:
- Kích thước, dtype và tập giá trị của đầu ra không đổi.
- Mask đầu vào không bị sửa đổi.
- Kernel lớn hơn → Erosion mạnh hơn, Dilation mạnh hơn.
- Kernel lớn hơn → xóa được vùng trắng nhỏ hơn, lấp được lỗ lớn hơn.
- Vùng mảnh 1 px bị xóa hẳn khi kernel ≥ 5×5 (hạn chế cần biết).

## 9. Liên hệ

Theo sheet `Quy ước & báo cáo`, phần báo cáo phụ trách của Quốc Anh là
*"Erosion, Dilation, Opening, Closing"*, người rà soát là Anh Quân.
Báo cáo chi tiết: [`report/morphology.md`](../../report/morphology.md).
