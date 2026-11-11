# 🚀 Hướng Dẫn Nhanh - Quick Start Guide

## Bắt Đầu Nhanh (5 Phút)

### 1️⃣ Cài Đặt Thư Viện
```bash
pip install -r requirements.txt
```

### 2️⃣ Chạy Ứng Dụng
```bash
python main.py
```

### 3️⃣ Mở Trình Duyệt
```
http://localhost:5000
```

## 📋 Giao Diện Chính

```
┌─────────────────────────────────────────┐
│         HSV Color Segmentation          │
│     Tách và Nhận Biết Màu Đối Tượng     │
└─────────────────────────────────────────┘

SIDEBAR (Điều Hướng)           MAIN CONTENT (Nội Dung)
├── 📤 Tải Ảnh                 ├── Tải file ảnh
├── 🎨 Phân Đoạn HSV           ├── Điều chỉnh ngưỡng H/S/V
├── 🔧 Lọc Median              ├── Chọn kernel size
├── ✨ Morphology              ├── Chọn phép toán
├── 📊 Đánh Giá                ├── So sánh Ground Truth
└── 📁 Kết Quả                 └── Tải xuống Mask
```

## 🎯 Các Bước Sử Dụng

### Bước 1: Tải Ảnh
- Click **📤 Tải Ảnh**
- Chọn hoặc kéo thả file ảnh
- Hỗ trợ: JPG, PNG, BMP, TIFF (tối đa 50MB)

### Bước 2: Điều Chỉnh HSV
- Click **🎨 Phân Đoạn HSV**
- Kéo các thanh trượt:
  - **H (Hue)**: 0-180 độ màu
  - **S (Saturation)**: 0-255 độ bão hòa
  - **V (Value)**: 0-255 độ sáng
- Nhấp **🔄 Xử Lý Ảnh** để xem kết quả

### Bước 3: Lọc Median (Tùy Chọn)
- Click **🔧 Lọc Median**
- Chọn kernel size: 3, 5, 7, 9
- Kernel lớn = khử nhiễu nhiều hơn

### Bước 4: Morphology (Tùy Chọn)
- Click **✨ Morphology**
- Chọn kernel size
- Tick Closing/Opening

### Bước 5: Đánh Giá (Nếu Có GT)
- Click **📊 Đánh Giá**
- Tải Ground Truth Mask
- Nhấp **🔍 Đánh Giá**
- Xem Pixel Accuracy, IoU, F1 Score

### Bước 6: Tải Xuống
- Click **📁 Kết Quả**
- Tải Mask (Thô, Median, hoặc Cuối)

## 📊 Chỉ Số Đánh Giá

| Chỉ Số | Ý Nghĩa | Công Thức |
|--------|---------|-----------|
| **Pixel Accuracy** | Tỷ lệ pixel đúng | (TP+TN) / (TP+TN+FP+FN) |
| **IoU** | Giao / Hợp | TP / (TP+FP+FN) |
| **Precision** | Độ chính xác | TP / (TP+FP) |
| **Recall** | Độ nhạy | TP / (TP+FN) |
| **F1 Score** | Trung bình hòa | 2×P×R / (P+R) |

## 🎨 Cấu Hình Màu Ví Dụ

### Màu Đỏ (Red)
- H1: 0-10, H2: 170-180
- S: 100-255
- V: 100-255

### Màu Xanh Lá (Green)
- H: 40-80
- S: 100-255
- V: 100-255

### Màu Xanh Dương (Blue)
- H: 100-130
- S: 100-255
- V: 100-255

### Màu Vàng (Yellow)
- H: 15-40
- S: 100-255
- V: 100-255

## 📁 Cấu Trúc Thư Mục

```
HSV-Color-Segmentation/
├── main.py                   # Flask app
├── requirements.txt
├── data_loader.py            # Đọc ảnh
├── hsv_segment.py            # Phân đoạn HSV
├── median_filter.py          # Lọc Median
├── morphology.py             # Hình thái học
├── evaluation.py             # Đánh giá
├── experiment.py             # Thực nghiệm
├── templates/
│   └── index.html            # Trang web
├── static/
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   ├── test_data.py
│   ├── test_hsv.py
│   └── test_evaluation.py
├── data/
│   ├── images/               # Ảnh đầu vào
│   └── ground_truth/         # GT Mask
├── uploads/                  # Upload tạm
└── results/                  # Kết quả
```

## 🧪 Chạy Tests

```bash
# Tất cả tests
python -m unittest discover tests

# Một test file
python -m unittest tests.test_data
python -m unittest tests.test_hsv
python -m unittest tests.test_evaluation
```

## ⚙️ Khắc Phục Sự Cố

### Lỗi: Port 5000 đã dùng
```bash
# Thay đổi port trong main.py:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Lỗi: Module không tìm thấy
```bash
pip install --upgrade flask opencv-python numpy
```

### Kích thước Mask không khớp
- Đảm bảo Ground Truth và ảnh cùng kích thước
- Sử dụng `loader.check_data_integrity()`

## 📚 Tài Liệu Chi Tiết

- **README.md**: Tài liệu đầy đủ
- **Code Comments**: Giải thích trong code
- **Test Files**: Ví dụ sử dụng

## 🔑 Phím Tắt (Gợi Ý)

- **Enter** ở slider: Xử lý ảnh
- **Ctrl+Shift+I**: Mở Developer Tools
- **F5**: Refresh trang

## 📝 Các File Quan Trọng

| File | Chức Năng | Người Phụ Trách |
|------|---------|-----------------|
| data_loader.py | Đọc dữ liệu | Anh Quân |
| hsv_segment.py | Phân đoạn HSV | Mạnh Quân |
| median_filter.py | Lọc Median | Anh Tuấn |
| morphology.py | Hình thái học | Quốc Anh |
| evaluation.py | Đánh giá | Hoàn |
| main.py | Tích hợp | Hoàn |

## 🎓 Học Tập

Mỗi thành viên nên:
1. Đọc code phần của mình
2. Chạy tests để hiểu chức năng
3. Sửa một lỗi để quen với codebase
4. Viết phần báo cáo của mình

## 🤝 Hỗ Trợ

Gặp vấn đề?
1. Kiểm tra terminal xem lỗi gì
2. Chạy tests: `python -m unittest tests.test_xxx`
3. Xem README.md chi tiết
4. Hỏi thành viên khác trong nhóm

---

**Thời gian ước tính**: 5 phút để chạy ứng dụng  
**Phiên bản**: 1.0  
**Ngày**: 2024
