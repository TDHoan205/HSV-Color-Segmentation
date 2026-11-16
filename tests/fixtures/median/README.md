# Bộ dữ liệu kiểm thử cho Median Filter

Thư mục này chứa các mask nhị phân tổng hợp dùng để kiểm thử module
[`src/median_filter.py`](../../../src/median_filter.py) (Anh Tuấn).

Mọi ảnh đều là **PNG grayscale 1 kênh**, `dtype = uint8`, chỉ chứa đúng hai
giá trị **0** (nền) và **255** (đối tượng) — đúng quy ước mask của dự án.

## Sinh lại dữ liệu

```bash
python tests/fixtures/median/generate_fixtures.py
```

Script có seed cố định (`SEED = 2024`, mỗi fixture một seed riêng) nên chạy
lại luôn cho ra đúng những file giống nhau. Script tự kiểm tra các tính chất
bắt buộc trước khi ghi file; nếu một tính chất không đạt thì script dừng lại
bằng `AssertionError`.

## Danh sách file

| File | Kích thước | Mô tả |
|---|---|---|
| `noisy_salt_pepper_3x3.png` | 120 × 120 | Hình tròn đặc (bán kính 38) bị chèn **40 điểm muối** (255 đơn lẻ trên nền) và **25 điểm tiêu** (0 đơn lẻ trong vùng đối tượng). Mỗi điểm nhiễu nằm ở vị trí mà vùng lân cận 5×5 chỉ chứa toàn nền hoặc toàn đối tượng. |
| `expected_clean_3x3.png` | 120 × 120 | Ảnh tham chiếu: hình tròn lý tưởng **đã đi qua bộ lọc 3×3**. Vì bộ lọc trung vị bo tròn biên cong, ảnh này nhỏ hơn hình gốc khoảng 1 pixel ở biên. Lọc ảnh nhiễu bằng kernel 3×3 phải cho ra đúng ảnh này (khớp 100 %). |
| `dense_noise_clusters.png` | 120 × 120 | Hình tròn lý tưởng cộng **18 cụm nhiễu 2×4** (mỗi cụm ghép từ hai khối 2×2) đặt trên nền, cách đối tượng tối thiểu 4 pixel. |
| `expected_clean_dense.png` | 120 × 120 | Vùng đối tượng lý tưởng của `dense_noise_clusters.png` (không nhiễu), dùng làm nhãn tham chiếu. |
| `fine_details_edges.png` | 120 × 120 | Các chi tiết mảnh: đường thẳng 1 pixel, đường thẳng 2 pixel, chữ thập 2 pixel, hình vuông nhỏ có góc nhọn và hai đường chéo 1 pixel. Dùng để minh họa tác dụng phụ của kernel lớn (xóa chi tiết mảnh, bo tròn góc). |

## Tính chất đã được kiểm chứng khi sinh

| Fixture | Kiểm chứng |
|---|---|
| `noisy_salt_pepper_3x3` | `apply_median_filter(noisy, 3)` khớp 100 % với `expected_clean_3x3` (0 pixel khác biệt). |
| `dense_noise_clusters` | Kernel 3×3 còn sót **72 pixel nhiễu**; kernel 5×5 loại sạch (**0 pixel**). |
| `fine_details_edges` | Số pixel bị thay đổi tăng đơn điệu theo kernel: 3×3 = 271, 5×5 = 663, 7×7 = 679. |

## Cách dùng trong unit test

```python
import cv2

noisy = cv2.imread('tests/fixtures/median/noisy_salt_pepper_3x3.png', cv2.IMREAD_GRAYSCALE)
clean = cv2.imread('tests/fixtures/median/expected_clean_3x3.png', cv2.IMREAD_GRAYSCALE)
```

Bộ test tương ứng nằm ở [`tests/test_median.py`](../../test_median.py).
