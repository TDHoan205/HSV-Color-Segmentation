# Dữ liệu đầu vào & Ground Truth

**Phụ trách:** Anh Quân (Dữ liệu & Ground Truth)
**Màu mục tiêu:** Đỏ (Red)
**Quy ước tuân thủ:** Quy ước 1–3 trong sheet `Quy ước & báo cáo`

---

## 1. Màu mục tiêu và cấu hình HSV

Nhóm thống nhất chọn **màu đỏ** làm màu mục tiêu vì:

- Vùng màu đỏ là vùng hue đặc trưng, tách biệt rõ với phần lớn nền tự nhiên.
- Màu đỏ là trường hợp kinh điển của **hai khoảng Hue** trong không gian HSV, nên bài tập có ý nghĩa khi phải xử lý ranh giới `H = 0 / H = 180`.

Cấu hình ngưỡng mặc định (dùng trong `main.py` và `src/hsv_segment.py`):

| Thành phần | Giá trị | Ghi chú |
|---|---|---|
| Hue | `[0, 10]` ∪ `[170, 180]` | Đỏ nằm ở hai đầu vòng tròn hue |
| Saturation | `[100, 255]` | Loại vùng nhạt / xám |
| Value | `[100, 255]` | Loại vùng tối |

Thang giá trị theo OpenCV: **H = 0–179**, **S = 0–255**, **V = 0–255**.

---

## 2. Tiêu chí chọn ảnh

Một ảnh được đưa vào bộ dữ liệu khi đáp ứng đồng thời các tiêu chí:

### 2.1 Tiêu chí bắt buộc (không có thì loại)

| # | Tiêu chí | Cách kiểm tra |
|---|---|---|
| T1 | Ảnh mở được bằng OpenCV, định dạng JPG/PNG/BMP/TIFF | `cv2.imread()` trả về khác `None` |
| T2 | Ảnh màu 3 kênh, kiểu `uint8` | `image.shape[2] == 3`, `image.dtype == np.uint8` |
| T3 | Có đối tượng màu đỏ nhận dạng được, chiếm tỷ lệ vùng ảnh hợp lý | Tỷ lệ pixel đỏ trong khoảng 5% – 60% |
| T4 | Ground Truth cùng kích thước `H×W` với ảnh | So sánh `shape[:2]` |
| T5 | Ground Truth nhị phân, chỉ chứa giá trị `0` và `255` | `np.unique(gt) ⊆ {0, 255}` |
| T6 | Ground Truth không rỗng (phải có vùng đối tượng) | `np.count_nonzero(gt) > 0` |
| T7 | Có mô tả tình huống trong `metadata.csv` | Đối chiếu `image_id` |

### 2.2 Tiêu chí đa dạng (bắt buộc về mặt phủ mạo)

Ảnh phải bao phủ các tình huống khác nhau để phát hiện giới hạn của thuật toán:

- **Nền sáng** và **nền tối**
- **Màu gần giống** với màu đích (nền cam, nền hồng)
- **Bóng đổ** trên nền
- **Ánh sáng yếu** (vùng đối tượng có V thấp)
- **Ánh sáng quá mạnh** (vùng đối tượng bị nhạt màu, S thấp)
- **Ánh sáng không đều** trong cùng một ảnh
- **Nhiễu cảm giác máy ảnh**
- **Nhiều đối tượng** trong cùng một ảnh

> Nếu toàn bộ ảnh đều "dễ" thì bộ dữ liệu không có giá trị đánh giá: mọi cấu hình ngưỡng đều cho kết quả tốt và không phân biệt được phương pháp nào tốt hơn.

### 2.3 Tiêu chí loại bỏ

- Ảnh trùng lặp hoặc gần trùng lặp (cùng bối cảnh, chỉ khác vài pixel)
- Ảnh không xác định được vùng đối tượng (quá mơ hồ, vật thể nửa trong khung hình)
- Ảnh có đối tượng màu đỏ chiếm gần hết khung hình (không còn vùng nền để đánh giá FP)
- Ảnh chụp màn hình, ảnh đồ họa, ảnh có watermark che vùng đối tượng

---

## 3. Cấu trúc thư mục

```
data/
├── README.md                    # Tài liệu này
├── images/                      # Ảnh đầu vào (JPG)
│   ├── img_01_red_circle_light_bg.jpg
│   ├── img_02_red_square_dark_bg.jpg
│   └── ...
├── ground_truth/                # Ground Truth Mask (PNG nhị phân)
│   ├── img_01_red_circle_light_bg.png
│   ├── img_02_red_square_dark_bg.png
│   └── ...
└── metadata.csv                 # Mô tả tình huống từng ảnh
```

### Quy ước đặt tên

```
<image_id>_<mô_tả_tình_huống>.<ext>
   │            │                  │
   │            │                  └─ phần mở rộng: .jpg (ảnh), .png (GT)
   │            └──────────────────── mô tả ngắn, chữ thường, gạch dưới
   └───────────────────────────── mã ảnh: img_NN, NN từ 01 đến 12
```

Ảnh và Ground Truth **cùng tên, khác phần mở rộng**. Đây là cơ chế khớp cặp mà
`DataLoader.get_gt_path()` sử dụng.

---

## 4. Quy ước kỹ thuật cho dữ liệu

| Thuộc tính | Ảnh đầu vào | Ground Truth |
|---|---|---|
| Số kênh | 3 (BGR) | 1 |
| Kiểu dữ liệu | `uint8` | `uint8` |
| Giá trị | 0–255 | chỉ `0` (nền) và `255` (đối tượng) |
| Kích thước | H×W | **bằng** H×W của ảnh |
| Không gian màu | BGR (không chuyển sang HSV ở bước đọc dữ liệu) | nhị phân |

Lưu ý theo **Quy ước 3**: Ground Truth phải **độc lập** với Mask dự đoán.
Trong bộ dữ liệu này, Ground Truth được tạo trực tiếp từ hình học của vật thể
tại thời điểm vẽ ảnh, **không** dùng kết quả chạy ngưỡng HSV để làm nhãn.
Đây là cách bảo đảm nhãn không bị "rò rỉ" từ thuật toán cần được đánh giá.

---

## 5. Schema của `metadata.csv`

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `image_id` | str | Mã ảnh, duy nhất, ví dụ `img_01` |
| `image_file` | str | Đường dẫn ảnh (tương đối so với thư mục gốc dự án) |
| `gt_file` | str | Đường dẫn Ground Truth |
| `width` | int | Chiều rộng ảnh (px) |
| `height` | int | Chiều cao ảnh (px) |
| `target_color` | str | Màu mục tiêu, toàn bộ là `Red` |
| `scenario` | str | Mã tình huống, ví dụ `nen_sang`, `mau_gan_giong` |
| `background` | str | Mô tả nền |
| `lighting` | str | Mô tả điều kiện ánh sáng |
| `object_count` | int | Số vật thể trong ảnh |
| `object_pixels` | int | Số pixel thuộc vùng đối tượng trong GT |
| `object_ratio` | float | Tỷ lệ vùng đối tượng so với toàn ảnh |
| `h_mean` | float | Hue trung bình của vùng đối tượng (theo trung bình góc) |
| `s_mean` | float | Saturation trung bình của vùng đối tượng |
| `v_mean` | float | Value trung bình của vùng đối tượng |
| `note` | str | Ghi chú, lý do chọn ảnh, điểm khó cần lưu ý |

### Danh mục `scenario`

| Mã | Ý nghĩa |
|---|---|
| `nen_sang` | Nền sáng, trung tính |
| `nen_toi` | Nền tối |
| `bom_do` | Có bóng đổ của vật thể trên nền |
| `nhieu_doi_tuong` | Nhiều vật thể trong một ảnh |
| `mau_gan_giong` | Nền có màu gần màu mục tiêu |
| `mau_gan_giong_kho` | Nền gần giống màu mục tiêu nhưng khó tách (Hue trong khoảng đỏ thứ hai) |
| `anh_sang_yeu` | Ánh sáng yếu, vùng đối tượng có V thấp |
| `anh_sang_manh` | Ánh sáng quá mạnh, vật thể bị nhạt màu (S thấp) |
| `anh_sang_khong_deu` | Ánh sáng không đều trong cùng ảnh |
| `nhieu_tin_hieu` | Nhiễu cảm giác máy ảnh mạnh |

---

## 6. Cách dùng bộ đọc dữ liệu

```python
from src.data_loader import DataLoader

loader = DataLoader("data/images", "data/ground_truth", "data/metadata.csv")

# Duyệt toàn bộ cặp ảnh / Ground Truth
for img_path, gt_path in loader.build_dataset():
    image_bgr, gt_mask = loader.load_image_gt_pair(img_path, gt_path)
    # image_bgr: (H, W, 3) uint8
    # gt_mask:   (H, W)    uint8, giá trị 0/255

# Đọc metadata
for row in loader.load_metadata():
    print(row["image_id"], row["scenario"], row["note"])

# Kiểm tra toàn diện trước khi bàn giao
report = loader.full_check()
print(report["all_ok"])   # True nếu mọi ảnh đạt tiêu chí
```

---

## 7. Kiểm thử

```bash
python -m pytest tests/test_data.py -v
```

Bộ test gồm 2 nhóm:

- `TestDataLoader` — kiểm thử đơn vị với dữ liệu tạm trong thư mục hệ thống
  (load ảnh, load GT, báo lỗi file thiếu, phát hiện lệch kích thước,
  phát hiện GT không nhị phân, đọc metadata).
- `TestRealDataset` — kiểm thử trên **bộ dữ liệu thật** trong `data/`:
  đủ 8–12 ảnh, mỗi ảnh có GT, GT nhị phân 1 kênh, cùng kích thước,
  metadata phủ hết ảnh và đa dạng tình huống.

---

## 8. Tái tạo lại bộ dữ liệu

Bộ ảnh hiện tại được sinh bằng script tất định nên có thể tái tạo đúng y như cũ:

```bash
python scripts/generate_dataset.py --output data --seed 42
```

Script sẽ ghi đè `data/images/`, `data/ground_truth/` và `data/metadata.csv`.

> Khi nhóm thay bằng ảnh chụp thật: giữ nguyên cấu trúc thư mục, đặt tên theo
> quy ước ở mục 3, cập nhật lại `metadata.csv`, rồi chạy lại
> `python -m pytest tests/test_data.py` để xác nhận mọi ảnh vẫn đạt tiêu chí.

---

## 9. Giới hạn của bộ dữ liệu

Xem phần giới hạn chi tiết trong [`report/data.md`](../report/data.md).
