# Hướng Dẫn Sử Dụng Web HSV Color Segmentation

> Truy cập: http://localhost:5000

## 1. Chương trình này làm gì?

Chương trình **tách đối tượng ra khỏi nền dựa theo màu sắc**:
Ảnh màu (BGR) → chuyển sang không gian màu **HSV** → giữ lại pixel có màu nằm trong ngưỡng H/S/V → ra **Mask nhị phân** (trắng = đối tượng, đen = nền) → **lọc nhiễu Median** → **làm sạch bằng Morphology** → **chấm điểm so với Ground Truth**.

Ví dụ: muốn tách quả táo đỏ → chỉnh ngưỡng Hue đỏ → Mask trắng là vùng táo đỏ.

## 2. Ý nghĩa thanh menu (sidebar)

| Menu | URL hash | Ý nghĩa | Cách dùng |
|------|----------|---------|-----------|
| 📤 Tải Ảnh | `#upload` | Nạp ảnh đầu vào, tạo `session_id` | Click/kéo-thả ảnh (JPG/PNG/BMP/TIFF ≤ 50MB). Bắt buộc làm đầu tiên |
| 🎨 Phân Đoạn HSV | `#hsv` | Chỉnh ngưỡng H/S/V rồi bấm xử lý | Kéo 8 slider H1/H2/S/V → bấm **🔄 Xử Lý Ảnh** → xem 3 Mask: Thô / Median / Morph |
| 🔧 Lọc Median | `#filter` | Chọn kernel khử nhiễu trước khi xử lý | Chọn 3/5/7/9. Kernel càng lớn càng sạch nhưng mất chi tiết nhỏ |
| ✨ Morphology | `#morph` | Chọn phép làm sạch Mask | Tick **Closing** (lấp lỗ đen trong vật) và/hoặc **Opening** (xóa chấm trắng nhiễu). Chọn kernel rồi quay lại tab HSV bấm xử lý |
| 📊 Đánh Giá | `#evaluation` | Chấm điểm Mask so với đáp án chuẩn | Tải Ground Truth Mask (cùng kích thước ảnh) → bấm **🔍 Đánh Giá** → xem Accuracy/IoU/Precision/Recall/F1 + ảnh Visualization |
| 📁 Kết Quả | `#results` | Tải Mask về máy | 3 nút: Mask Thô / Mask Median / Mask Cuối (tốt nhất) |

## 3. Riêng tab `#hsv` là gì?

`#hsv` chỉ là anchor tới tab **Phân Đoạn HSV** — nơi làm việc chính:

- **Hue Range 1 (0–10)** + **Hue Range 2 (170–180)**: dải màu sắc. Mặc định là màu **đỏ** (đỏ nằm vắt qua 2 đầu thang Hue 0–180 nên cần 2 khoảng).
- **Saturation (100–255)**: độ đậm màu. Kéo min lên để loại màu nhạt/phai.
- **Value (100–255)**: độ sáng. Kéo min lên để loại vùng tối/bóng.
- Nút **🔄 Xử Lý Ảnh**: gửi toàn bộ tham số (HSV + kernel Median + Morphology) lên `/api/process`, server chạy pipeline `HSVSegmenter → MedianFilter → MorphologyOperator` và trả về 3 ảnh Mask.

## 4. Ngưỡng mẫu

- Đỏ: H1 0–10, H2 170–180, S 100–255, V 100–255
- Xanh lá: H 40–80 | Xanh dương: H 100–130 | Vàng: H 15–40 (chỉ cần H1, H2 bỏ qua)

## 5. Quy trình chuẩn (5 phút)

1. `#upload`: tải ảnh → thấy preview là OK
2. `#filter` + `#morph`: chọn kernel (mặc định 5x5, Closing bật sẵn là đủ)
3. `#hsv`: chỉnh slider → **Xử Lý Ảnh** → so sánh 3 Mask
4. `#evaluation` (nếu có GT): tải Mask chuẩn → Đánh Giá
5. `#results`: tải Mask Cuối về

## 6. Đọc kết quả đánh giá

- **Pixel Accuracy**: % pixel đúng tổng thể
- **IoU**: độ chồng lấp vùng dự đoán/Ground Truth (quan trọng nhất)
- **Precision**: trong vùng dự đoán, bao nhiêu là đúng
- **Recall**: trong vùng thật, bắt được bao nhiêu
- Ảnh Visualization: 🟢 TP đúng | 🔴 FP bắt nhầm | 🔵 FN bỏ sót
