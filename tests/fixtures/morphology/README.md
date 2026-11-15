# Test Fixtures - Morphology

**Phụ trách:** Quốc Anh (Morphological Operations)

Thư mục này chứa các **Mask kiểm thử tự tạo** cho module `src/morphology.py`.

---

## 1. Vì sao cần fixture tổng hợp

Theo kế hoạch Excel (Task 2): *"Tạo Mask có vùng trắng rời rạc và lỗ đen nhỏ"*.

Theo checklist tích hợp mục 2: *"TV2–TV4 dùng ảnh/Mask fixture tự tạo để code trước, không phải chờ dataset"*.

Lý do không dùng bộ dữ liệu thật (`data/`) cho test:
- Ground Truth trong `data/` được vẽ bằng hình học sạch (hình tròn, vuông, tam giác)
  nên **không có nhiễu pixel rời rạch** và **không có lỗ đen bên trong vật thể**.
- Vì vậy trên dữ liệu thật, Opening và Closing gần như không thay đổi gì
  (đã đo: IoU trung bình 0.7137 → 0.7135).
- Fixture tổng hợp cố tình chứa đúng hai loại nhiễu mà hình thái học giải quyết được,
  nhờ đó test có ý nghĩa và **tự chứng minh** tác dụng của từng phép toán.

## 2. Cấu trúc fixture chính

`make_noisy_mask()` — Mask 120×120, uint8, giá trị 0/255:

```
+--------------------------------------------------+
|  ▪▪▪ (đốm trắng 4x4, rời rạch)                   |
|      ┌──────────────┐                           |
|      │       ▪▪▪    │  <- lỗ đen 3x3            |
|      │       ▪▪▪    │  <- lỗ đen 3x3            |
|      └──────────────┘                           |
|                                                  |
|                        ┌──────────────┐         |
|                        │              │         |
|                        └──────────────┘         |
|  ▪▪▪ (đốm trắng 4x4, rời rạch)                  |
+--------------------------------------------------+
```

| Thành phần | Vị trí (row, col) | Kích thước | Vai trò |
|---|---|---|---|
| Hình vuông A | `(20:50, 20:50)` | 30×30 | Vùng đối tượng chính |
| Hình vuông B | `(70:95, 70:95)` | 25×25 | Vùng đối tượng chính |
| Lỗ đen 1 | `(26:29, 26:29)` | 3×3 | **Closing** lấp kín |
| Lỗ đen 2 | `(36:39, 36:39)` | 3×3 | **Closing** lấp kín |
| Đốm trắng 1 | `(8:12, 8:12)` | 4×4 | **Opening** loại bỏ |
| Đốm trắng 2 | `(100:104, 100:104)` | 4×4 | **Opening** loại bỏ |

Tổng: 1539 pixel trắng (1507 vật thể + 32 đốm rời rạch), 18 pixel lỗ đen.

## 3. Các fixture khác

| Hàm | Mô tả | Dùng để kiểm thử |
|---|---|---|
| `make_noisy_mask()` | Vùng trắng rời rạch + lỗ đen nhỏ | Hành vi chính của 4 phép toán |
| `make_solid_mask()` | Chỉ có vật thể, hoàn hảo | Phép toán không làm thay đổi gì |
| `make_thin_mask()` | Vùng đối tượng mảnh 1 px | Hạn chế của kernel lớn |
| `make_empty_mask()` | Toàn nền (0 px đối tượng) | Trường hợp biên |
| `make_full_mask()` | Toàn đối tượng (255) | Trường hợp biên ngược lại |

## 4. Kết quả đo tham chiếu

Đo thực tế trên `make_noisy_mask()` (1539 px trắng) với kernel hình ellipse:

| Kernel | Opening loại bỏ | Closing lấp thêm | Lỗ 3×3 còn lại | Đốm 4×4 còn lại |
|---|---|---|---|---|
| 3×3 | 16 px | 8 px | 4/9 px | 12/16 px |
| 5×5 | 48 px | 18 px | **0** (lấp hết) | **0** (loại hết) |
| 7×7 | 74 px | 18 px | 0 | 0 |

**Kết luận quan trọng:** kernel 3×3 **không đủ** để lấp hẳn lỗ 3×3 hay xóa hẳn
đốm 4×4. Cần kernel **≥ 5×5** mới thực sự lấp kín lỗ và loại sạch đốm.
Đây là lý do test dùng kernel 5×5 cho các khẳng định "lấp hết" / "loại hết".

So sánh hình kernel:

| Shape | 3×3 lấp lỗ | 3×3 loại đốm | 5×5 loại đốm |
|---|---|---|---|
| `rect` | 0/9 px | 0/16 px | 32 px |
| `ellipse` | 4/9 px | 4/16 px | 48 px |
| `cross` | 4/9 px | 4/16 px | 64 px |

## 5. Cách dùng

```python
from tests.fixtures.morphology import make_noisy_mask, SQUARE_A, HOLE_1

mask = make_noisy_mask()

# Vùng lỗ đen trước xử lý
print(mask[HOLE_1].sum())        # 0 -> Closing sẽ lấp thành 255
print(mask[SQUARE_A].sum())      # số pixel vật thể
```

Trong test, fixture được import trực tiếp:

```python
from tests.fixtures.morphology import make_noisy_mask
```

## 6. Sinh lại file PNG mẫu

```bash
python -m tests.fixtures.morphology
```

Kết quả được ghi vào `tests/fixtures/morphology/output/`:

| File | Nội dung |
|---|---|
| `fixture_noisy.png` | Fixture chính (có nhiễu) |
| `fixture_solid.png` | Fixture sạch |
| `fixture_thin.png` | Fixture vùng mảnh |
| `fixture_empty.png` | Fixture rỗng |
| `fixture_full.png` | Fixture đầy |

## 7. Quy ước

- Mask luôn là ảnh **1 kênh, uint8, nền = 0, đối tượng = 255** (Quy ước 2 của nhóm).
- Fixture **tất định** — không dùng ngẫu nhiên, nên kết quả test luôn ổn định.
- Không fixture nào phụ thuộc vào bộ dữ liệu thật trong `data/`.
