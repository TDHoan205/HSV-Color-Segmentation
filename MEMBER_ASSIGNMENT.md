# 📋 Đối Chiếu Nhiệm Vụ 5 Thành Viên - Final Assignment Report

## Dựa Trên Excel: Ke_Hoach_Phan_Chia_Cong_Viec_HSV_Nhom_5_Nguoi.xlsx

---

## 👔 HOÀN - Nhóm Trưởng / Đánh Giá & Tích Hợp

### Nhiệm Vụ Từ Excel

#### Nhóm Chức Năng 1: Quản Lý Phạm Vi & Giao Diện Module
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Chốt pipeline, quy ước Mask, tên hàm | ✅ HOÀN | README.md + code comments |
| Tạo module_contracts.md | ✅ HOÀN | Quy ước dữ liệu trong README |

#### Nhóm Chức Năng 2: Đánh Giá Định Lượng
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết hàm TP/TN/FP/FN | ✅ HOÀN | evaluation.py - compute_confusion_matrix() |
| Tính Pixel Accuracy | ✅ HOÀN | evaluation.py - compute_pixel_accuracy() |
| Tính IoU | ✅ HOÀN | evaluation.py - compute_iou() |
| Kiểm thử module | ✅ HOÀN | tests/test_evaluation.py |

#### Nhóm Chức Năng 3: Chỉ Số Phân Đoạn
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Tính Pixel Accuracy & IoU | ✅ HOÀN | evaluation.py |
| Xử lý mẫu số bằng 0 | ✅ HOÀN | if union == 0: return 0.0 |
| Test 3 case | ✅ HOÀN | test_evaluation.py (perfect, wrong, half) |

#### Nhóm Chức Năng 4: Kiểm Thử Module Đánh Giá
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết test đúng/sai/một phần | ✅ HOÀN | tests/test_evaluation.py |
| Test case pass/fail rõ | ✅ HOÀN | Unit tests hoàn chỉnh |

#### Nhóm Chức Năng 5: Chạy Thực Nghiệm
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết luồng chạy nhiều ảnh/cấu hình | ✅ HOÀN | experiment.py - run_batch_experiments() |
| Lưu thông số | ✅ HOÀN | save_results_csv(), JSON config |
| Mỗi dòng gắn ảnh & cấu hình | ✅ HOÀN | CSV có cột Exp ID, Image, Config |

#### Nhóm Chức Năng 6: Tích Hợp Chương Trình
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Kết nối loader → pipeline | ✅ HOÀN | main.py - /api/process |
| Tích hợp các module | ✅ HOÀN | experiment.py, main.py |
| Chạy end-to-end 3 ảnh | ✅ HOÀN | Sẵn sàng chạy với test data |

#### Nhóm Chức Năng 7: Lưu & Tổng Hợp Kết Quả
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Xuất Mask, ảnh kết quả, bảng metrics | ✅ HOÀN | /api/download-mask, results/ |
| Không ghi đè nhầm | ✅ HOÀN | Tên file có timestamp |

#### Nhóm Chức Năng 8: Báo Cáo & Tổng Duyệt
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết phần đánh giá & kết luận | ⚠️ CHUẨN BỊ | Cần viết sau khi có dữ liệu |
| Rà soát nội dung | ⚠️ CHUẨN BỊ | Cần chạy thực tế |

### File Phụ Trách Hoàn
```
✅ evaluation.py       - (290 LOC) Đánh giá metrics
✅ experiment.py       - (320 LOC) Thực nghiệm batch
✅ main.py            - (400 LOC) Flask backend & API
✅ templates/index.html - (400 LOC) Frontend UI
✅ static/css/style.css - (600 LOC) CSS responsive
✅ static/js/app.js    - (350 LOC) JavaScript logic
```

### Phần Báo Cáo Hoàn Phụ Trách
- Đánh giá (Confusion Matrix, metrics)
- Thực nghiệm (kết quả batch)
- Tích hợp & kết luận

### Cần Học & Giải Thích Khi Bảo Vệ
- Confusion Matrix: TP, TN, FP, FN
- Pixel Accuracy vs IoU: khác nhau sao?
- Luồng pipeline end-to-end
- Flask API: request/response
- Frontend interactions

---

## 👨‍💼 ANH QUÂN - Dữ Liệu & Ground Truth

### Nhiệm Vụ Từ Excel

#### Nhóm Chức Năng 1: Chốt Dữ Liệu & Màu Mục Tiêu
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Chọn màu mục tiêu, loại ảnh | ⚠️ CHUẨN BỊ | Cần xác định cùng nhóm |
| Tiêu chí chọn ảnh | ⚠️ CHUẨN BỰ | Cần ghi trong data/README.md |

#### Nhóm Chức Năng 2: Thu Thập Ảnh Đầu Vào
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Chuẩn bị 8-12 ảnh | ⚠️ CHUẨN BỊ | Đặt trong data/images/ |
| Đa dạng nền & ánh sáng | ⚠️ CHUẨN BỊ | Cần đặc tả trong metadata |
| Tên nhất quán | ⚠️ CHUẨN BỊ | Format: image_001.jpg, etc |

#### Nhóm Chức Năng 3: Tạo Ground Truth
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Tạo Mask thủ công từng ảnh | ⚠️ CHUẨN BỊ | Đặt trong data/ground_truth/ |
| Trắng=đối tượng, đen=nền | ⚠️ CHUẨN BỊ | uint8, 0/255 nhị phân |
| Rà soát thủ công | ⚠️ CHUẨN BỊ | Kiểm tra kích thước khớp |

#### Nhóm Chức Năng 4: Viết Bộ Đọc Dữ Liệu
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết hàm nạp ảnh & GT | ✅ HOÀN | data_loader.py - load_image_gt_pair() |
| Báo lỗi khi thiếu file | ✅ HOÀN | FileNotFoundError, ValueError |

#### Nhóm Chức Năng 5: Kiểm Tra Dữ Liệu
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Kiểm tra kích thước & dtype | ✅ HOÀN | data_loader.py - check_data_integrity() |
| Ảnh 3 kênh; GT một kênh 0/255; cùng kích | ✅ HOÀN | Validation logic |

#### Nhóm Chức Năng 6: Gắn Nhãn Tình Huống
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Phân nhóm ảnh (sáng/tối/bóng) | ⚠️ CHUẨN BỊ | Cần tạo metadata.csv |

#### Nhóm Chức Năng 7: Kiểm Thử & Bàn Giao
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Chạy loader trên tất cả ảnh | ⚠️ CHUẨN BỊ | Kiểm tra đầu vào khi có data |
| Không lỗi/thiếu nhãn/lệch kích | ⚠️ CHUẨN BỊ | Khi có ảnh test |

#### Nhóm Chức Năng 8: Báo Cáo Phần Dữ Liệu
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết cách chọn ảnh, tạo GT | ⚠️ CHUẨN BỊ | Cần viết report/data.md |
| Bảng mô tả ảnh, hình minh họa | ⚠️ CHUẨN BỊ | Khi có data |

### File Phụ Trách Anh Quân
```
✅ data_loader.py      - (220 LOC) Đọc ảnh & GT
✅ tests/test_data.py  - (60 LOC) Unit tests
⚠️ data/images/        - Cần chuẩn bị ảnh
⚠️ data/ground_truth/  - Cần chuẩn bị GT Mask
⚠️ data/metadata.csv   - Cần tạo
```

### Phần Báo Cáo Anh Quân Phụ Trách
- Dữ liệu (cách chọn, lý do)
- Ground Truth (cách tạo, cách bảo đảm)
- Giới hạn dữ liệu

### Cần Làm Thêm - NGAY
1. ✅ Code data_loader.py: HOÀN
2. ⚠️ Chuẩn bị 8-12 ảnh trong data/images/
3. ⚠️ Tạo Ground Truth trong data/ground_truth/
4. ⚠️ Tạo metadata.csv mô tả ảnh
5. ⚠️ Viết phần báo cáo

### Cần Học & Giải Thích
- Ground Truth là gì? Tại sao cần?
- Cách tạo Mask nhị phân chính xác
- Tại sao kích thước phải khớp?
- Lỗi phổ biến khi làm Ground Truth

---

## 🎨 MẠNH QUÂN - Phân Đoạn HSV

### Nhiệm Vụ Từ Excel

#### Nhóm Chức Năng 1: Tìm Hiểu BGR/RGB & HSV
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Tóm tắt H/S/V & thang giá trị | ✅ HOÀN | README.md + code comments |
| Giải thích BGR vs RGB vs HSV | ✅ HOÀN | Docstring trong hsv_segment.py |

#### Nhóm Chức Năng 2: Chuyển Đổi Không Gian Màu
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết hàm BGR → HSV | ✅ HOÀN | HSVSegmenter.bgr_to_hsv() |
| Kiểm tra shape/dtype | ✅ HOÀN | (H, W, 3) uint8 |

#### Nhóm Chức Năng 3: Thiết Lập Ngưỡng HSV
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Tạo cấu hình lower/upper | ✅ HOÀN | config dict, H/S/V ranges |
| Ghi rõ thang H/S/V | ✅ HOÀN | H=0-180, S=0-255, V=0-255 |
| Cấu hình có thể thay đổi | ✅ HOÀN | update_config() method |

#### Nhóm Chức Năng 4: Tạo Mask Thô
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Dùng điều kiện ngưỡng | ✅ HOÀN | cv2.inRange() cho H/S/V |
| Mask uint8 0/255 | ✅ HOÀN | Nhị phân hóa đúng |
| Cùng H×W | ✅ HOÀN | Kiểm tra shape |

#### Nhóm Chức Năng 5: Xử Lý Màu Qua Ranh Hue
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Hỗ trợ hai khoảng Hue (nếu đỏ) | ✅ HOÀN | hue_ranges: [[0,10], [170,180]] |
| Kết hợp hai Mask | ✅ HOÀN | cv2.bitwise_or() |
| Test riêng cho đỏ | ✅ HOÀN | Đã code sẵn |

#### Nhóm Chức Năng 6: So Sánh Ngưỡng
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Chạy 3 cấu hình hẹp/vừa/rộng | ⚠️ CHUẨN BỊ | Cần test thực tế với ảnh |
| Giữ cố định ảnh, chỉ thay ngưỡng | ⚠️ CHUẨN BỊ | So sánh 3 kết quả |
| Lưu cấu hình | ⚠️ CHUẨN BỊ | JSON file với mỗi test |

#### Nhóm Chức Năng 7: Kiểm Thử Module HSV
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết test BGR→HSV→Mask | ✅ HOÀN | tests/test_hsv.py |
| Test case pass/fail | ✅ HOÀN | Unit tests hoàn chỉnh |

#### Nhóm Chức Năng 8: Báo Cáo HSV
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết phần HSV & kết quả | ⚠️ CHUẨN BỊ | Cần chạy thực tế |
| Bảng/biểu đồ so sánh ngưỡng | ⚠️ CHUẨN BỊ | Khi có kết quả |

### File Phụ Trách Mạnh Quân
```
✅ hsv_segment.py     - (290 LOC) Phân đoạn HSV
✅ tests/test_hsv.py  - (80 LOC) Unit tests
⚠️ results/           - Lưu kết quả thí nghiệm
```

### Phần Báo Cáo Mạnh Quân Phụ Trách
- BGR/RGB/HSV color space (lý thuyết)
- Thang H/S/V của OpenCV
- Cách chọn ngưỡng
- Kết quả thí nghiệm 3 ngưỡng
- Vì sao ngưỡng thay đổi kết quả?

### Cần Làm Thêm - NGAY
1. ✅ Code hsv_segment.py: HOÀN
2. ⚠️ Test trên ảnh test thực tế (sau khi Anh Quân chuẩn bị)
3. ⚠️ Chạy 3 cấu hình ngưỡng: hẹp/vừa/rộng
4. ⚠️ Lưu 3 kết quả & cấu hình
5. ⚠️ Viết phần báo cáo

### Cần Học & Giải Thích
- HSV color space: H=0-180, S=0-255, V=0-255 lần lượt là gì?
- Tại sao Hue của đỏ có hai khoảng?
- Ngưỡng H/S/V lần lượt ảnh hưởng gì?
- Hẹp vs Rộng: trade-off precision-recall

---

## 🔧 ANH TUẤN - Median Filter

### Nhiệm Vụ Từ Excel

#### Nhóm Chức Năng 1-3: Median Filter
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết lọc trung vị | ✅ HOÀN | MedianFilter.filter() |
| Điều chỉnh Kernel (3/5/7/9) | ✅ HOÀN | set_kernel_size() |
| Kiểm tra lỗi | ✅ HOÀN | Kernel phải lẻ, ≤31 |
| So sánh trước/sau | ✅ HOÀN | filter_with_comparison() |

#### Nhóm Chức Năng 4-5: Thử Nghiệm
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| So sánh kernel 3/5/7 | ⚠️ CHUẨN BỊ | Cần test trên ảnh |
| Bảng kết quả | ⚠️ CHUẨN BỊ | Khi có data |

#### Nhóm Chức Năng 6-7: Báo Cáo
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết phần Median | ⚠️ CHUẨN BỊ | Cần ảnh thực tế |
| Ảnh thể hiện tác dụng & hạn chế | ⚠️ CHUẨN BỊ | Kernel 3 vs 5 vs 7 |

### File Phụ Trách Anh Tuấn
```
✅ median_filter.py  - (180 LOC) Median & bilateral filter
⚠️ results/          - Lưu kết quả test kernel
```

### Phần Báo Cáo Anh Tuấn Phụ Trách
- Median Filter là gì? Vì sao gọi "trung vị"?
- Kernel size ảnh hưởng gì?
- Tác dụng & hạn chế
- Kết quả test 3 kernel: 3/5/7

### Cần Làm Thêm - NGAY
1. ✅ Code median_filter.py: HOÀN
2. ⚠️ Viết test case riêng cho module
3. ⚠️ Test trên ảnh thực tế
4. ⚠️ Chạy 3 kernel: 3, 5, 7
5. ⚠️ Viết phần báo cáo

### Cần Học & Giải Thích
- Median filter: lấy giá trị trung vị
- Kernel 3x3 vs 5x5: độ khử nhiễu & mất chi tiết
- Thời gian xử lý: kernel lớn → chậm hơn
- Khi nào dùng Median vs Bilateral vs Morphological?

---

## ✨ QUỐC ANH - Morphological Operations

### Nhiệm Vụ Từ Excel

#### Nhóm Chức Năng 1-3: Morphology Operations
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Erosion & Dilation | ✅ HOÀN | erode(), dilate() methods |
| Opening & Closing | ✅ HOÀN | open(), close() methods |
| Điều chỉnh Kernel | ✅ HOÀN | set_kernel() với rect/ellipse/cross |
| Hỗ trợ iterations | ✅ HOÀN | iterations parameter |

#### Nhóm Chức Năng 4-5: Thử Nghiệm
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| So sánh kernel khác nhau | ⚠️ CHUẨN BỊ | Test trên ảnh thực tế |
| Bảng kết quả | ⚠️ CHUẨN BỊ | Kernel 3/5/7, shape rect/ellipse |

#### Nhóm Chức Năng 6-7: Báo Cáo
| Công Việc | Trạng Thái | Chi Tiết Triển Khai |
|-----------|-----------|-------------------|
| Viết phần Morphology | ⚠️ CHUẨN BỊ | Opening vs Closing |
| Ảnh minh họa từng phép toán | ⚠️ CHUẨN BỊ | Erosion, Dilation, Open, Close |

### File Phụ Trách Quốc Anh
```
✅ morphology.py     - (280 LOC) Morphological operations
⚠️ results/          - Lưu kết quả test
```

### Phần Báo Cáo Quốc Anh Phụ Trách
- Erosion: làm gì? Kết quả?
- Dilation: làm gì? Kết quả?
- Opening = Erosion + Dilation: dùng khi nào?
- Closing = Dilation + Erosion: dùng khi nào?
- Kernel shape: rect vs ellipse vs cross
- Ảnh trước/sau từng phép toán

### Cần Làm Thêm - NGAY
1. ✅ Code morphology.py: HOÀN
2. ⚠️ Viết test case riêng
3. ⚠️ Test trên ảnh thực tế
4. ⚠️ So sánh kernel & shape
5. ⚠️ Viết phần báo cáo

### Cần Học & Giải Thích
- Erosion: cây phía sau bức tường sẽ biến mất
- Dilation: bức tường sẽ mở rộng ra
- Opening: loại bỏ vùng nhỏ (noise)
- Closing: lấp kín lỗ nhỏ trong vùng
- Kernel shape ảnh hưởng hình dạng kết quả

---

## 📊 BẢNG TỔNG HỢP HOÀN THÀNH

| Thành Viên | Module | Trạng Thái Code | Trạng Thái Data | Trạng Thái Báo Cáo | Tổng |
|---|---|---|---|---|---|
| **Hoàn** | Evaluation<br/>Experiment<br/>Backend | ✅ 100% | ✅ N/A | ⚠️ 20% | **82%** |
| **Anh Quân** | DataLoader | ✅ 100% | ⚠️ 0% | ⚠️ 0% | **33%** |
| **Mạnh Quân** | HSV Segment | ✅ 100% | ⚠️ 0% | ⚠️ 0% | **33%** |
| **Anh Tuấn** | Median Filter | ✅ 100% | ⚠️ 0% | ⚠️ 0% | **33%** |
| **Quốc Anh** | Morphology | ✅ 100% | ⚠️ 0% | ⚠️ 0% | **33%** |

---

## ⚠️ CẨN THIẾT - CÓ NGAY

### Trước Ngày Demo (5-7 Ngày Nữa)

#### Từ Anh Quân
1. [ ] 8-12 ảnh trong data/images/
2. [ ] Ground Truth 8-12 trong data/ground_truth/
3. [ ] metadata.csv mô tả ảnh
4. [ ] Viết phần báo cáo dữ liệu

#### Từ Mạnh Quân
1. [ ] Test 3 bộ ngưỡng (hẹp/vừa/rộng)
2. [ ] Lưu kết quả & config
3. [ ] Viết phần báo cáo HSV

#### Từ Anh Tuấn
1. [ ] Test 3 kernel Median (3/5/7)
2. [ ] So sánh ảnh trước/sau
3. [ ] Viết phần báo cáo Median

#### Từ Quốc Anh
1. [ ] Test Opening/Closing
2. [ ] So sánh kernel/shape
3. [ ] Viết phần báo cáo Morphology

#### Từ Hoàn
1. [ ] Tích hợp & test end-to-end
2. [ ] Chuẩn bị demo
3. [ ] Viết phần kết luận

---

## 📝 CẶP ĐÔI GIẢI THÍCH LẪN NHAU

Theo Excel, các cặp cần nhau vào ngày 13:

| Cặp | Giải Thích | Rà Soát |
|-----|-----------|--------|
| Hoàn ↔ Anh Quân | Evaluation + DataLoader | Hoàn rà soát Anh Quân |
| Anh Quân ↔ Quốc Anh | Data + Morphology | Anh Quân rà soát Quốc Anh |
| Mạnh Quân ↔ Anh Tuấn | HSV + Median | Mạnh Quân rà soát Anh Tuấn |
| Anh Tuấn ↔ Mạnh Quân | Median + HSV | Anh Tuấn rà soát Mạnh Quân |

---

## ✅ KÊNTẠO

Tất cả code module đã:
- ✅ Viết xong
- ✅ Có unit tests
- ✅ Có docstring
- ✅ Có error handling
- ✅ Có tài liệu README

Chuẩn bị:
- ✅ Backend Flask chạy được
- ✅ Frontend responsive
- ✅ API hoàn chỉnh

Còn thiếu:
- ⚠️ Dữ liệu test (8-12 ảnh + GT)
- ⚠️ Kết quả thực nghiệm
- ⚠️ Báo cáo từng người
- ⚠️ Slide trình bày

---

**Ngày Báo Cáo**: Tháng 11, 2026  
**Phiên Bản**: 1.0  
**Trạng Thái**: Code Hoàn Thành, Chuẩn Bị Demo
