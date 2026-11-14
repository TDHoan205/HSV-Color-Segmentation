# HSV Color Segmentation - Tách và Nhận Biết Màu

**Ứng dụng Web xử lý ảnh: Phân đoạn màu trong không gian HSV với các phép toán hình thái học**

## 📋 Tổng Quan

Ứng dụng này cho phép người dùng:
1. Tải ảnh từ máy tính
2. Chuyển đổi ảnh BGR sang không gian màu HSV
3. Phân đoạn vùng ảnh theo màu mục tiêu
4. Khử nhiễu sử dụng Median Filter
5. Xử lý hình thái học (Morphological Operations)
6. Đánh giá hiệu suất so với Ground Truth
7. Tải xuống các kết quả

## 🛠️ Công Nghệ Sử Dụng

- **Backend**: Python 3.14 + Flask
- **Xử Lý Ảnh**: OpenCV, NumPy
- **Frontend**: HTML5, CSS3, JavaScript
- **Biểu Đồ**: Chart.js (nếu cần)

## 📁 Cấu Trúc Dự Án

```
HSV-Color-Segmentation/
├── main.py                      # Flask backend chính
├── requirements.txt             # Các thư viện cần thiết
├── data_loader.py              # Module đọc dữ liệu (Anh Quân)
├── hsv_segment.py              # Module phân đoạn HSV (Mạnh Quân)
├── median_filter.py            # Module lọc Median (Anh Tuấn)
├── morphology.py               # Module hình thái học (Quốc Anh)
├── evaluation.py               # Module đánh giá (Hoàn)
├── experiment.py               # Module thực nghiệm (Hoàn)
├── templates/
│   └── index.html              # Trang web chính
├── static/
│   ├── css/
│   │   └── style.css           # CSS styling
│   └── js/
│       └── app.js              # JavaScript frontend
├── tests/
│   ├── test_data.py            # Test data_loader
│   ├── test_hsv.py             # Test hsv_segment
│   └── test_evaluation.py       # Test evaluation
├── scripts/
│   ├── generate_dataset.py     # Sinh bộ ảnh + Ground Truth (Anh Quân)
│   └── make_report_figures.py  # Sinh hình minh họa cho báo cáo (Anh Quân)
├── data/
│   ├── README.md               # Tiêu chí chọn ảnh, quy ước, schema metadata
│   ├── metadata.csv            # Mô tả tình huống từng ảnh
│   ├── images/                 # Ảnh đầu vào (10 ảnh JPG)
│   └── ground_truth/           # Ground Truth Mask (10 ảnh PNG nhị phân)
├── report/
│   ├── data.md                 # Báo cáo phần dữ liệu (Anh Quân)
│   └── figures/                # Hình minh họa thật cho báo cáo
├── uploads/                    # Thư mục upload tạm thời
└── results/                    # Kết quả thực nghiệm
```

## 🚀 Cài Đặt và Chạy

### 1. Cài Đặt Môi Trường

```bash
# Tạo môi trường ảo (tùy chọn nhưng khuyên dùng)
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Cài Đặt Thư Viện

```bash
pip install -r requirements.txt
```

### 3. Chạy Ứng Dụng

```bash
python main.py
```

Ứng dụng sẽ chạy tại: **http://localhost:5000**

### 4. Chạy Tests

```bash
# Chạy tất cả test
python -m pytest tests/

# Hoặc chạy từng test file
python -m unittest tests.test_data
python -m unittest tests.test_hsv
python -m unittest tests.test_evaluation
```

## 📖 Hướng Dẫn Sử Dụng

### Bước 1: Tải Ảnh
1. Nhấp vào tab "📤 Tải Ảnh"
2. Kéo thả hoặc click để chọn file ảnh (JPG, PNG, BMP, TIFF)
3. Hỗ trợ ảnh tối đa 50MB

### Bước 2: Phân Đoạn HSV
1. Nhấp vào tab "🎨 Phân Đoạn HSV"
2. Điều chỉnh các thanh trượt:
   - **Hue Range 1 & 2**: Để tách màu (VD: Đỏ = 0-10 + 170-180)
   - **Saturation**: Độ bão hòa màu
   - **Value**: Độ sáng
3. Nhấp "🔄 Xử Lý Ảnh" để xem kết quả

### Bước 3: Lọc Median
1. Tab "🔧 Lọc Median"
2. Chọn kích thước kernel (3x3 đến 9x9)
3. Kernel lớn hơn = khử nhiễu nhiều hơn

### Bước 4: Morphology
1. Tab "✨ Morphology"
2. Chọn kích thước kernel
3. Chọn phép toán:
   - **Closing**: Lấp kín lỗ nhỏ bên trong
   - **Opening**: Loại bỏ vùng nhỏ

### Bước 5: Đánh Giá
1. Tab "📊 Đánh Giá"
2. Tải Ground Truth Mask
3. Nhấp "🔍 Đánh Giá"
4. Xem kết quả chỉ số và biểu đồ

### Bước 6: Tải Xuống
1. Tab "📁 Kết Quả"
2. Tải Mask (Thô, Median, hoặc Cuối)

## 📊 Chỉ Số Đánh Giá

Ứng dụng cung cấp các chỉ số:

- **Pixel Accuracy**: Tỷ lệ pixel phân đoạn đúng
- **IoU (Jaccard)**: Giao/Hợp (Intersection over Union)
- **Precision**: Độ chính xác (TP / (TP + FP))
- **Recall**: Độ nhạy (TP / (TP + FN))
- **F1 Score**: Trung bình điều hòa Precision/Recall
- **Specificity**: Độ đặc hiệu (TN / (TN + FP))

Confusion Matrix:
- **TP**: True Positives (dự đoán đúng là đối tượng)
- **TN**: True Negatives (dự đoán đúng là nền)
- **FP**: False Positives (dự đoán sai, coi nền là đối tượng)
- **FN**: False Negatives (dự đoán sai, coi đối tượng là nền)

## 📚 Chi Tiết Các Module

### 1. data_loader.py (Anh Quân)
**Chức năng**: Đọc ảnh BGR và Ground Truth Mask

```python
from src.data_loader import DataLoader

loader = DataLoader("data/images", "data/ground_truth", "data/metadata.csv")
image_bgr, gt_mask = loader.load_image_gt_pair("img_01_red_circle_light_bg.jpg",
                                                "img_01_red_circle_light_bg.png")
```

**API:**
- `load_image(path)`: Đọc ảnh BGR (H, W, 3)
- `load_ground_truth(path)`: Đọc GT Mask (H, W)
- `load_image_gt_pair(img_path, gt_path)`: Đọc cặp
- `build_dataset()`: Dựng danh sách cặp (ảnh, GT) có trên đĩa
- `load_metadata()`: Đọc `data/metadata.csv`
- `get_metadata_by_id(image_id)`: Tra cứu metadata theo mã ảnh
- `validate_pair(img, gt)`: Kiểm tra 1 cặp theo tiêu chí bàn giao
- `check_data_integrity()`: Kiểm tra tính toàn vẹn dữ liệu
- `full_check()`: Kiểm tra toàn diện trước khi bàn giao

### 2. hsv_segment.py (Mạnh Quân)
**Chức năng**: Chuyển BGR → HSV, phân đoạn màu

```python
from hsv_segment import HSVSegmenter

config = {
    'hue_ranges': [[0, 10], [170, 180]],
    'saturation': [100, 255],
    'value': [100, 255],
}
segmenter = HSVSegmenter(config)
mask_raw, hsv_image = segmenter.segment(image_bgr)
```

**API:**
- `bgr_to_hsv(image)`: Chuyển BGR → HSV
- `create_mask(hsv_image)`: Tạo Mask từ HSV
- `segment(image_bgr)`: Phân đoạn đầy đủ
- `update_config(**kwargs)`: Cập nhật cấu hình

### 3. median_filter.py (Anh Tuấn)
**Chức năng**: Khử nhiễu Mask

```python
from median_filter import MedianFilter

median = MedianFilter(kernel_size=5)
mask_filtered = median.filter(mask_raw)
```

**API:**
- `filter(mask)`: Áp dụng lọc Median
- `set_kernel_size(size)`: Đặt kích thước kernel
- `filter_with_comparison(mask)`: So sánh trước/sau

### 4. morphology.py (Quốc Anh)
**Chức năng**: Xử lý hình thái học

```python
from morphology import MorphologyOperator

morph = MorphologyOperator(kernel_size=5, kernel_shape='ellipse')
mask_open = morph.open(mask)
mask_close = morph.close(mask)
```

**API:**
- `erode(mask, iterations)`: Erosion
- `dilate(mask, iterations)`: Dilation
- `open(mask, iterations)`: Opening
- `close(mask, iterations)`: Closing
- `apply_operation(mask, operation, iterations)`: Phép toán tuỳ ý

### 5. evaluation.py (Hoàn)
**Chức năng**: Đánh giá hiệu suất

```python
from evaluation import SegmentationEvaluator

evaluator = SegmentationEvaluator()
metrics = evaluator.compute_metrics(pred_mask, gt_mask)
print(f"Accuracy: {metrics['pixel_accuracy']:.2%}")
print(f"IoU: {metrics['iou']:.2%}")
```

**API:**
- `compute_confusion_matrix(pred, gt)`: TP, TN, FP, FN
- `compute_pixel_accuracy(pred, gt)`: Độ chính xác pixel
- `compute_iou(pred, gt)`: IoU
- `compute_metrics(pred, gt)`: Tất cả chỉ số
- `create_visualization(pred, gt)`: Ảnh visualize

### 6. experiment.py (Hoàn)
**Chức năng**: Chạy thực nghiệm với nhiều cấu hình

```python
from experiment import ExperimentRunner

runner = ExperimentRunner(results_dir="results")
configs = [
    {'hsv': {...}, 'median': {...}, 'morphology': {...}},
]
results = runner.run_batch_experiments(image_files, configs)
runner.save_results_csv("results.csv")
```

## 🔍 Quy Ước Dữ Liệu

1. **Ảnh**: BGR (3 kênh), uint8, đọc từ OpenCV
2. **Mask**: Nhị phân (1 kênh), uint8, nền=0, đối tượng=255
3. **HSV trong OpenCV**: H=0-180, S=0-255, V=0-255
4. **Ground Truth**: Độc lập với dự đoán, tạo thủ công

## ⚙️ Cấu Hình Màu Ví Dụ

### Màu Đỏ
```python
config = {
    'hue_ranges': [[0, 10], [170, 180]],
    'saturation': [100, 255],
    'value': [100, 255],
}
```

### Màu Xanh Lá
```python
config = {
    'hue_ranges': [[40, 80]],
    'saturation': [100, 255],
    'value': [100, 255],
}
```

### Màu Xanh Dương
```python
config = {
    'hue_ranges': [[100, 130]],
    'saturation': [100, 255],
    'value': [100, 255],
}
```

### Màu Vàng
```python
config = {
    'hue_ranges': [[15, 40]],
    'saturation': [100, 255],
    'value': [100, 255],
}
```

## 📊 Tạo Dữ Liệu Test

Bộ dữ liệu chuẩn của nhóm (10 ảnh màu đỏ + Ground Truth + metadata) đã được bàn giao:

```bash
# Kiểm tra sức khỏe bộ dữ liệu
python -m src.data_loader

# Sinh lại bộ dữ liệu từ đầu (tất định, seed 42)
python scripts/generate_dataset.py --output data --seed 42

# Sinh hình minh họa cho báo cáo
python scripts/make_report_figures.py
```

Chi tiết về bộ dữ liệu: [`data/README.md`](data/README.md) và [`report/data.md`](report/data.md).

## 🐛 Khắc Phục Sự Cố

### Lỗi: "No module named 'flask'"
```bash
pip install flask
```

### Lỗi: "No module named 'cv2'"
```bash
pip install opencv-python
```

### Lỗi: Port 5000 đã được sử dụng
```python
# Thay đổi port trong main.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Kích thước Mask không khớp
- Kiểm tra Ground Truth và ảnh có cùng kích thước
- Sử dụng `loader.check_data_integrity()` để kiểm tra

## 📋 Danh Sách Công Việc 5 Thành Viên

| Thành Viên | Module | File | Chức Năng | Trạng Thái |
|---|---|---|---|---|
| Hoàn | Đánh giá & Tích hợp | evaluation.py, experiment.py, main.py | Pixel Accuracy, IoU, thực nghiệm, tích hợp pipeline | ✅ |
| Anh Quân | Dữ liệu | src/data_loader.py, tests/test_data.py, scripts/generate_dataset.py | Đọc ảnh, GT, metadata, kiểm tra dữ liệu, bộ ảnh 10 ảnh + GT | ✅ |
| Mạnh Quân | HSV | src/hsv_segment.py, tests/test_hsv.py | BGR→HSV, ngưỡng, Mask thô | ✅ |
| Anh Tuấn | Median | src/median_filter.py | Lọc trung vị, so sánh kernel | ✅ |
| Quốc Anh | Morphology | src/morphology.py | Erosion, Dilation, Opening, Closing | ✅ |

## 📝 Phần Báo Cáo Mỗi Người

Mỗi thành viên phải viết phần báo cáo tương ứng:

- **Hoàn**: Đánh giá, thực nghiệm, kết quả, kết luận
- **Anh Quân**: Dữ liệu, cách chọn ảnh, Ground Truth
- **Mạnh Quân**: HSV, chọn ngưỡng, kết quả phân đoạn
- **Anh Tuấn**: Median Filter, thử nghiệm kernel
- **Quốc Anh**: Morphology, tác động các phép toán

## 🔗 Tài Liệu Tham Khảo

- OpenCV Documentation: https://docs.opencv.org/
- HSV Color Space: https://en.wikipedia.org/wiki/HSL_and_HSV
- Morphological Operations: https://en.wikipedia.org/wiki/Mathematical_morphology
- Flask Documentation: https://flask.palletsprojects.com/

## 📞 Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra lỗi trong terminal
2. Xem logs trong `uploads/` folder
3. Chạy tests để kiểm tra module

## 📄 License

Dự án cho mục đích giáo dục.

---

**Phiên bản**: 1.0  
**Cập nhật lần cuối**: 2024  
**Nhóm**: HSV Color Segmentation Project
