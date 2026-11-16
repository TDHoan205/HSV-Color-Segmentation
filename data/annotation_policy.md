# Chính sách gán nhãn Ground Truth (Phase D)

- `policy_version`: `annotation_policy_v1`
- `manifest_schema_version`: `dataset_manifest_v1`
- Áp dụng cho: mọi GT mới của ảnh thật. 10 GT tổng hợp cũ giữ nguyên, không gán nhãn lại.

## 1. Đối tượng gán nhãn

- Nhãn theo **màu mục tiêu**, không theo vật thể. Foreground = **255** là toàn bộ vùng nhìn thấy thuộc nhóm màu mục tiêu trong ảnh (kể cả nhiều vật cùng màu). Nền = **0**.
- Một ảnh có thể có nhiều màu mục tiêu. Mỗi cặp (ảnh, màu) là một dòng manifest với `sample_id` và file GT riêng.
- 15 `target_color_id` lấy từ preset A: `red, red_orange, orange, yellow_orange, yellow, yellow_green, green, blue_green, blue, blue_purple, purple, red_purple, white, black, gray`.
- Chỉ các màu có dữ liệu approved mới được kết luận chất lượng. Các màu còn lại chỉ có kiểm thử chức năng ở A/B/E.

## 2. Nguyên tắc độc lập với HSV

- Cấm dùng ngưỡng H/S/V của chương trình, mask HSV, median hoặc morphology để sinh hay sửa nhãn. Cấm tự điền vùng khó bằng mask HSV.
- Người gán nhãn mở ảnh gốc, ẩn mọi prediction, rồi quyết định bằng mắt.
- Với `white`, `black`, `gray`, quyết định bằng mắt theo ngữ cảnh ảnh. Không dùng ngưỡng preset làm định nghĩa GT.

## 3. Quy tắc biên và vùng khó

| Tình huống | Quy tắc |
|---|---|
| Rìa vật thể | Vẽ đường biên nhị phân, không chống răng cưa khi xuất mask. |
| Bóng đổ | Pixel nào mắt thấy vẫn mang màu mục tiêu thì thuộc foreground. Bóng xám trung tính trên nền khác thì không. |
| Đốm phản sáng | Pixel cháy sáng gần trắng không còn nhìn ra màu mục tiêu thì là nền. Phần quanh nó vẫn mang màu thì là foreground. |
| Vùng chuyển màu mơ hồ | Ghi vào `review_note`. Nếu quá mơ hồ để quyết định, chuyển `status=excluded` kèm `exclusion_reason`. |
| Vật thể bị che khuất | Chỉ gán nhãn phần nhìn thấy. |
| Ảnh không có màu mục tiêu | Không dùng cho tập positive. Ca negative cần `negative_control` riêng, không có trong v1. |

## 4. Định dạng file GT

- PNG một kênh, `uint8`, giá trị chỉ thuộc `{0, 255}`.
- Cùng chiều rộng và chiều cao với ảnh gốc. Cấm resize để khớp kích thước.
- Kích thước tham chiếu là kích thước ảnh **sau khi áp EXIF Orientation** (cách `cv2.imread` mặc định, `main.py` và `load_manifest_sample` đang đọc). Ảnh Samsung có Orientation=6 (dọc) lưu raw 4032x3024 nhưng hiển thị 3024x4032; GT phải là 3024x4032. Công cụ gán nhãn phải hiển thị ảnh đã xoay đúng như trình xem ảnh.
- Rasterize polygon theo tọa độ ảnh gốc. Tắt anti-alias khi xuất mask.
- Đường dẫn: `data/ground_truth/annotations_v1/<image_stem>__<target_color_id>__v1.png`. Nhãn sửa lưu thành `__v2.png`. Không ghi đè bản cũ. Manifest trỏ bản approved.

## 5. Quy trình annotation và review

1. **Gán nhãn.** Một người (Hoàn) dùng LabelMe hoặc CVAT chạy cục bộ, hoặc trình biên tập ảnh xuất PNG một kênh.
2. **Overlay.** Tạo overlay chỉ từ ảnh và GT (không prediction). Lưu vào `results/phase_d/<run_id>/overlays/`.
3. **Review lần hai.** Làm ở phiên làm việc tách biệt. Duyệt toàn bộ GT. Xem kỹ mọi ảnh khó. Ít nhất 20% ảnh xem ở zoom 100–200%. Ghi lần review, lỗi đã sửa và phương pháp vào `review_note`.
4. **Duyệt.** Chỉ khi review xong mới đặt `review_status=approved` và `status=approved`.
5. Chỉ có một người, nên **không** tuyên bố inter-annotator agreement.

## 6. Điều kiện approved

Một dòng chỉ được `status=approved` khi đồng thời thỏa:

- có `source_id` trong `dataset_sources.json` và `license_status` có bằng chứng;
- có GT độc lập, `annotation_method`, `annotation_version`, `annotator`, `review_status=approved`;
- `image_sha256`, `gt_sha256`, `width`, `height` khớp file thật.

Dòng không thỏa phải ở `pending_annotation`, `invalid` hoặc `excluded`, kèm `exclusion_reason` hoặc `next_action`.

## 7. Phân loại dữ liệu

- `data_type=synthetic`: ảnh sinh hình học. GT sinh từ hình học của generator, không từ HSV. Dùng làm `synthetic_reference`, **không** tính vào tiêu chí ảnh thật.
- `data_type=real`: ảnh chụp thật có nguồn và quyền sử dụng xác minh được.
- Timestamp, tên file hoặc EXIF của máy ảnh không chứng minh tác giả hay giấy phép. Chưa có xác nhận thì `license_status=unknown`.
