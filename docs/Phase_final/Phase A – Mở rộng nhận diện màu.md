# PHASE A — MỞ RỘNG NHẬN DIỆN MÀU TRONG KHÔNG GIAN HSV (MULTI-COLOR HSV RECOGNITION)

## 🎯 MỤC TIÊU PHASE A

Mở rộng chương trình từ việc chỉ tách màu đỏ thành chương trình cho phép người dùng lựa chọn nhiều nhóm màu thông qua bảng màu trực quan.

Khi người dùng chọn một màu, hệ thống tự động thiết lập ngưỡng HSV tương ứng. Người dùng vẫn có thể điều chỉnh thủ công các thông số H, S, V để cải thiện kết quả phân đoạn.

Phase A tập trung giải quyết:

- Loại bỏ logic Backend cố định màu đỏ.
- Xây dựng bảng chọn 15 nhóm màu.
- Tự động cập nhật ngưỡng HSV khi chọn màu.
- Cho phép tinh chỉnh HSV thủ công.
- Đồng bộ lựa chọn màu giữa Frontend và Backend.
- Giữ nguyên toàn bộ pipeline xử lý ảnh hiện tại.

**Phase A chỉ mở rộng khả năng phân đoạn theo màu, không xây dựng hệ thống nhận diện vật thể bằng AI hoặc Deep Learning.**

Luồng xử lý mục tiêu:

```text
Người dùng tải ảnh
        ↓
Chọn màu trên bảng màu
        ↓
Nạp ngưỡng HSV mặc định
        ↓
Tự động cập nhật H, S, V
        ↓
Người dùng tinh chỉnh HSV (nếu cần)
        ↓
Chuyển ảnh BGR → HSV
        ↓
Tạo Mask theo màu đã chọn
        ↓
Median Filter
        ↓
Morphology
        ↓
Hiển thị kết quả
        ↓
Evaluation (nếu có Ground Truth)
        ↓
PHASE A DONE
```

Đầu ra Phase A là chức năng chọn và phân đoạn nhiều nhóm màu được tích hợp vào project hiện tại, kèm kiểm thử và báo cáo nghiệm thu.

---

## 1. NGUYÊN TẮC TRIỂN KHAI

### 1.1 — Source-First Rule

Đọc code hiện tại trước khi chỉnh sửa.

Tối thiểu phải kiểm tra:

```text
main.py

src/
├── hsv_segment.py
├── data_loader.py
├── median_filter.py
├── morphology.py
├── evaluation.py
└── experiment.py

templates/
└── index.html

static/
├── css/
│   └── style.css
└── js/
    └── app.js

tests/
├── test_hsv.py
├── test_evaluation.py
├── test_morphology.py
└── các test liên quan khác
```

Nếu cấu trúc thực tế khác danh sách trên, phải tìm đúng file tương ứng.

Phân loại code:

```text
[EXISTING]      Đã tồn tại
[IMPLEMENTED]   Đã triển khai
[NEED UPDATE]   Cần mở rộng
[MISSING]       Chưa có
[BUG]           Có lỗi
[DEPENDENCY]    Phụ thuộc thành phần khác
[OUT OF SCOPE]  Ngoài phạm vi Phase A
```

Không viết lại module đang hoạt động nếu chỉ cần bổ sung chức năng.

### 1.2 — Single-Executor Rule

```text
Implementation Owner: Hoàn

Tool Support: Cursor Agent

Excel Assignments: Academic Context Only

Team Dependency: NONE
```

Hoàn là người trực tiếp thực hiện toàn bộ dự án.

Cursor Agent hỗ trợ đọc code, lập trình, kiểm thử và sửa lỗi.

Không chờ bàn giao từ bất kỳ thành viên nào.

### 1.3 — OpenCV HSV Rule

Sử dụng đúng thang giá trị HSV của OpenCV:

```text
H (Hue):        0 – 179
S (Saturation): 0 – 255
V (Value):      0 – 255
```

Không sử dụng nhầm thang Hue 0–360 khi truyền trực tiếp vào OpenCV.

Mọi khoảng HSV phải nằm trong giới hạn hợp lệ.

### 1.4 — Preserve Existing Features Rule

Không được làm hỏng các chức năng:

```text
Image Upload
HSV Segmentation
Median Filter
Morphology
Evaluation
ExperimentRunner
Mask Download
Metrics Export (nếu hiện có)
```

Các chức năng cũ phải tiếp tục hoạt động sau khi mở rộng nhận diện màu.

### 1.5 — Single Source of Truth Rule

Bộ cấu hình HSV mặc định của 15 nhóm màu phải có một nguồn quản lý thống nhất.

Không để Frontend và Backend tự khai báo hai bộ ngưỡng khác nhau dẫn đến sai lệch.

Ưu tiên quản lý preset ở Backend và cung cấp cho Frontend thông qua API hiện có hoặc API phù hợp.

---

## 2. ⚠️ ĐIỀU KIỆN BẮT ĐẦU

Phase A chỉ bắt đầu triển khai khi:

```text
Project hiện tại đã được kiểm tra
          +
Đã xác định logic HSV đang sử dụng
          +
Đã xác định API xử lý ảnh
          +
Đã xác định cấu trúc thanh trượt H, S, V
          +
Đã xác định vị trí cố định màu đỏ trong Backend
          +
Đã xác định cách Frontend gửi thông số HSV
```

Nếu chưa biết một thành phần nằm ở đâu:

```text
[DEPENDENCY — CODEBASE DISCOVERY]
```

Phải đọc và xác định trước khi chỉnh sửa.

Không tự ý viết lại cấu trúc chương trình để giải quyết vấn đề.

---

## 3. ⚠️ PHẠM VI PHASE A

### CHỈ LÀM

```text
Loại bỏ màu đỏ cố định
Xây dựng bộ 15 màu lựa chọn
Xây dựng HSV preset tương ứng
Hiển thị bảng màu trên giao diện
Tự động cập nhật H, S, V khi chọn màu
Cho phép chỉnh HSV thủ công
Khôi phục HSV mặc định
Hỗ trợ nhiều khoảng Hue
Xử lý riêng White, Black, Gray
Đồng bộ Frontend và Backend
Tạo Mask theo màu được chọn
Kiểm thử chức năng mới
Kiểm thử hồi quy chức năng cũ
Ghi báo cáo Phase A
```

### ❌ KHÔNG ĐƯỢC LÀM

```text
Không triển khai chức năng so sánh nhiều cấu hình HSV
(Không thuộc Phase A, thực hiện ở Phase B)

Không xây dựng AI / Deep Learning
Không nhận diện tên vật thể
Không triển khai ExperimentRunner mới
Không mở rộng chức năng Morphology
Không thay đổi thuật toán Median Filter
Không viết lại Evaluation
Không tự thay đổi Dataset và Ground Truth
Không thêm chức năng ngoài phạm vi Phase A
Không xóa chức năng cũ
Không tự chuyển sang Phase B
```

---

# TASK A.1 — AUDIT CODE HSV HIỆN TẠI

## 🎯 Mục tiêu

Xác định chính xác chương trình đang xử lý màu đỏ như thế nào và những phần cần mở rộng.

## Cách làm

Đọc các thành phần:

```text
src/hsv_segment.py
main.py
templates/index.html
static/js/app.js
static/css/style.css
```

Kiểm tra:

```text
1. Vị trí khai báo color_name.
2. Vị trí đang cố định màu đỏ.
3. Cách định nghĩa lower HSV và upper HSV.
4. Có hỗ trợ nhiều khoảng Hue không?
5. Cách chuyển BGR sang HSV.
6. Cách tạo binary mask.
7. Cách Frontend gửi HSV qua API.
8. Cách Backend nhận và kiểm tra HSV.
9. Cách cập nhật kết quả Mask trên giao diện.
10. Các thông số HSV mặc định đang sử dụng.
```

Với từng file ghi nhận:

```text
File path
Class / Function liên quan
Chức năng hiện tại
Vị trí cần thay đổi
Chức năng cần giữ nguyên
Rủi ro khi thay đổi
```

## DONE

Có bảng:

| File | Hiện trạng | Cần thay đổi | Ghi chú |
|---|---|---|---|
| hsv_segment.py | EXISTING | NEED UPDATE | Hỗ trợ preset nhiều màu |
| main.py | EXISTING | NEED UPDATE | Loại bỏ màu đỏ cố định |
| index.html | EXISTING | NEED UPDATE | Bổ sung bảng màu |
| app.js | EXISTING | NEED UPDATE | Đồng bộ màu và HSV |
| style.css | EXISTING | NEED UPDATE | Thiết kế bảng màu |
| test_hsv.py | EXISTING | NEED UPDATE | Kiểm thử nhiều màu |

Chỉ xác nhận đúng file sau khi đã đọc source thực tế.

---

# TASK A.2 — XÂY DỰNG BỘ 15 MÀU LỰA CHỌN

## 🎯 Mục tiêu

Cho phép người dùng chọn màu trực quan thay vì phải tự kéo thanh trượt HSV khi chưa biết màu cần tách.

Bảng màu gồm 15 lựa chọn.

### 12 nhóm màu theo vòng tròn màu

```text
01. RED
02. RED-ORANGE
03. ORANGE
04. YELLOW-ORANGE
05. YELLOW
06. YELLOW-GREEN
07. GREEN
08. BLUE-GREEN
09. BLUE
10. BLUE-PURPLE
11. PURPLE
12. RED-PURPLE
```

### 3 màu đặc biệt

```text
13. WHITE
14. BLACK
15. GRAY
```

### Yêu cầu

Mỗi nhóm màu cần có:

```text
Color ID
Color Name
Display Name (tiếng Việt)
Display Color (mã HEX)
HSV Preset
HSV Range
Description
```

Ví dụ cấu trúc cấu hình:

```python
COLOR_PRESETS = {
    "red": {
        "name": "Đỏ",
        "mode": "hue",
        "hue_ranges": [
            [0, 10],
            [170, 179]
        ],
        "s_min": "...",
        "s_max": 255,
        "v_min": "...",
        "v_max": 255
    }
}
```

Đây chỉ là ví dụ cấu trúc, không phải bộ thông số mặc định bắt buộc.

### Quy tắc thiết lập HSV

- Không chia Hue thành 12 khoảng bằng nhau một cách máy móc.
- Thiết lập các khoảng phù hợp với từng nhóm màu.
- Cho phép các khoảng màu có vùng biên giao nhau nếu cần thiết.
- Kiểm chứng ngưỡng bằng ảnh thực tế.
- Lưu rõ nguồn gốc và trạng thái kiểm chứng của từng preset.
- Không tự tuyên bố preset đã chính xác nếu chưa có dữ liệu kiểm chứng.

Riêng màu đỏ:

```text
RED
├── Hue Range 1: vùng gần đầu thang H
└── Hue Range 2: vùng gần cuối thang H
```

Phải tạo Mask bằng cách kết hợp hai khoảng Hue.

Đối với White, Black, Gray:

```text
WHITE:
Ưu tiên điều kiện Saturation thấp
và Value cao.

BLACK:
Ưu tiên điều kiện Value thấp.

GRAY:
Ưu tiên điều kiện Saturation thấp
và Value nằm trong khoảng phù hợp.
```

Không sử dụng Hue làm điều kiện chính cho ba màu đặc biệt này.

Các giới hạn S/V phải được hiệu chỉnh và kiểm chứng trên ảnh thực tế.

### DONE

Có cấu hình đầy đủ cho 15 màu.

| Color | Preset | HSV Mode | Verified |
|---|---|---|---|
| Red | YES | Hue ranges | NEED TEST |
| Red-Orange | YES | Hue | NEED TEST |
| Orange | YES | Hue | NEED TEST |
| Yellow-Orange | YES | Hue | NEED TEST |
| Yellow | YES | Hue | NEED TEST |
| Yellow-Green | YES | Hue | NEED TEST |
| Green | YES | Hue | NEED TEST |
| Blue-Green | YES | Hue | NEED TEST |
| Blue | YES | Hue | NEED TEST |
| Blue-Purple | YES | Hue | NEED TEST |
| Purple | YES | Hue | NEED TEST |
| Red-Purple | YES | Hue | NEED TEST |
| White | YES | S/V | NEED TEST |
| Black | YES | V | NEED TEST |
| Gray | YES | S/V | NEED TEST |

Không đánh dấu Verified nếu chưa kiểm tra.

---

# TASK A.3 — XÂY DỰNG HSV PRESET MANAGER

## 🎯 Mục tiêu

Xây dựng cơ chế quản lý HSV preset để khi chọn màu, hệ thống tự động nạp thông số tương ứng.

## Cách làm

Xác định vị trí phù hợp trong cấu trúc hiện tại để quản lý preset.

Mỗi preset cần hỗ trợ:

```text
color_id
color_name
mode
hue_ranges
s_min
s_max
v_min
v_max
```

Đối với màu có nhiều khoảng Hue, phải lưu được nhiều khoảng độc lập.

Đối với White, Black và Gray, hỗ trợ chế độ lọc theo S/V mà không phụ thuộc Hue.

### Quy tắc hoạt động

```text
Người dùng chọn màu
        ↓
Tìm COLOR_PRESET
        ↓
Lấy thông số HSV mặc định
        ↓
Cập nhật thanh trượt
        ↓
Gửi thông số đến Backend
        ↓
Tạo Mask
```

### Khôi phục mặc định

Khi người dùng nhấn Reset:

```text
Lấy preset của màu hiện tại
        ↓
Khôi phục toàn bộ HSV
        ↓
Cập nhật thanh trượt
        ↓
Cập nhật trạng thái chỉnh sửa
```

Không được Reset về màu đỏ mặc định một cách cố định.

Reset phải khôi phục đúng màu đang được chọn.

### DONE

- Mỗi màu có preset riêng.
- Chọn màu lấy đúng preset.
- Reset khôi phục đúng preset.
- Chỉnh thủ công không làm mất lựa chọn màu.
- Không có hai nguồn HSV preset mâu thuẫn nhau.

---

# TASK A.4 — THIẾT KẾ COLOR PALETTE TRÊN FRONTEND

## 🎯 Mục tiêu

Tạo bảng màu trực quan giúp người dùng chọn nhanh màu cần phân đoạn.

## Cách làm

Đọc:

```text
templates/index.html
static/css/style.css
static/js/app.js
```

Bổ sung khu vực:

```text
CHỌN MÀU CẦN TÁCH

[ RED ]              [ RED-ORANGE ] 
[ ORANGE ]           [ YELLOW-ORANGE ]
[ YELLOW ]           [ YELLOW-GREEN ]
[ GREEN ]            [ BLUE-GREEN ]
[ BLUE ]             [ BLUE-PURPLE ]
[ PURPLE ]           [ RED-PURPLE ]

[ WHITE ]            [ BLACK ] 
[ GRAY ]
```

Mỗi lựa chọn hiển thị:

```text
Ô màu trực quan
Tên màu
Trạng thái đang được chọn
```

### Trạng thái giao diện

Khi chọn một màu:

- Màu được chọn phải có viền hoặc dấu hiệu nổi bật.
- Hiển thị tên màu hiện tại.
- Các thanh trượt HSV được cập nhật.
- Không làm mất ảnh đang tải.
- Không làm mất các thiết lập Median Filter và Morphology không liên quan.

### Yêu cầu thiết kế

- Giao diện dễ nhìn, rõ ràng.
- Bố cục thích ứng với màn hình.
- Các màu không bị nhầm lẫn khi hiển thị.
- Người dùng biết chính xác màu nào đang được chọn.
- Không làm thay đổi bố cục các chức năng cũ ngoài phạm vi cần thiết.

### DONE

- Hiển thị đủ 15 lựa chọn.
- Bấm vào từng màu đều hoạt động.
- Trạng thái lựa chọn được cập nhật đúng.
- Không có màu nào bị thiếu hoặc không thể chọn.

---

# TASK A.5 — ĐỒNG BỘ HSV SLIDER VỚI COLOR PALETTE

## 🎯 Mục tiêu

Kết hợp bảng màu chọn sẵn với thanh trượt H, S, V để người dùng vừa sử dụng nhanh vừa có thể tinh chỉnh chuyên sâu.

## Cách làm

Khi người dùng chọn màu:

```text
Select Color
      ↓
Load Preset
      ↓
Update H Slider
      ↓
Update S Slider
      ↓
Update V Slider
      ↓
Update Displayed Values
```

### Các yêu cầu

1. Chọn màu mới thì thanh trượt cập nhật theo preset mới.
2. Người dùng có thể điều chỉnh thủ công.
3. Giá trị hiển thị phải khớp với giá trị thực tế gửi tới Backend.
4. Khi điều chỉnh thủ công, không được tự động chuyển lựa chọn sang màu khác.
5. Nút Reset phải khôi phục preset hiện tại.
6. Không dùng thông số cũ của màu trước sau khi chuyển màu mới.

### Xử lý nhiều khoảng Hue

Đối với màu đỏ:

- Phải thể hiện được cả hai khoảng Hue.
- Nếu UI hiện tại đã có hai cặp Hue Min/Max thì tận dụng.
- Không ép khoảng thứ hai về 0 nếu điều đó khiến mask thay đổi sai.

Đối với các màu khác:

- Chỉ sử dụng các khoảng cần thiết.
- Không truyền dữ liệu không hợp lệ.
- Nếu giao diện hiện tại chưa thể thể hiện nhiều khoảng Hue, cần bổ sung cách điều khiển phù hợp trong phạm vi Phase A.

### Đối với White, Black và Gray

- Các thanh trượt H có thể bị vô hiệu hóa hoặc được đánh dấu không áp dụng.
- Người dùng vẫn có thể tinh chỉnh S/V.
- Hiển thị rõ thông số nào thực sự được sử dụng.

### DONE

- Chọn màu và cập nhật HSV đồng bộ.
- Chỉnh thủ công hoạt động đúng.
- Reset hoạt động đúng.
- Không còn tình trạng thanh trượt hiển thị một giá trị nhưng Backend nhận giá trị khác.

---

# TASK A.6 — CẬP NHẬT BACKEND VÀ HSV SEGMENTATION

## 🎯 Mục tiêu

Loại bỏ logic chỉ xử lý màu đỏ và cho phép Backend xử lý màu được người dùng lựa chọn.

## Cách làm

Kiểm tra:

```text
main.py
src/hsv_segment.py
```

### Yêu cầu

1. Loại bỏ việc cố định `color_name = red` trong logic xử lý.
2. Backend tiếp nhận màu được chọn và cấu hình HSV tương ứng.
3. Kiểm tra dữ liệu đầu vào.
4. Hỗ trợ một hoặc nhiều khoảng Hue.
5. Hỗ trợ chế độ lọc S/V cho White, Black và Gray.
6. Kết hợp các khoảng Mask đúng cách.
7. Trả về Mask và thông tin xử lý theo API hiện tại.

### Quy tắc tạo Mask

Với nhóm màu có Hue:

```text
BGR Image
    ↓
Convert to HSV
    ↓
Mask from Hue Range 1
    +
Mask from Hue Range 2 (nếu có)
    ↓
Combine Masks (OR)
    ↓
Apply S/V Threshold
    ↓
Final Binary Mask
```

Với White, Black, Gray:

```text
BGR Image
    ↓
Convert to HSV
    ↓
Apply S/V Conditions
    ↓
Final Binary Mask
```

### Kiểm tra dữ liệu đầu vào

Các trường hợp phải xử lý:

```text
Color ID không tồn tại
Thiếu thông số HSV
H nằm ngoài 0–179
S hoặc V nằm ngoài 0–255
Min lớn hơn Max
Hue range không hợp lệ
Sai kiểu dữ liệu
Không có ảnh đầu vào
```

Phải trả về thông báo lỗi dễ hiểu, không để lỗi nội bộ làm chương trình dừng bất thường.

### Tương thích API

Đọc API hiện tại trước khi thay đổi.

Ưu tiên giữ nguyên endpoint đang được Frontend sử dụng.

Nếu cần mở rộng request payload, phải bảo đảm các chức năng cũ không bị hỏng.

Ưu tiên tận dụng `/api/get-info` hiện có nếu phù hợp để cung cấp dữ liệu preset cho Frontend; chỉ tạo endpoint mới khi thực sự cần thiết.

### DONE

- Backend xử lý được cả 15 lựa chọn màu.
- Không còn logic chỉ cố định màu đỏ.
- Mask được tạo theo đúng preset và thông số người dùng.
- Hỗ trợ nhiều khoảng Hue.
- Xử lý đúng White, Black và Gray.
- API trả lỗi rõ ràng khi dữ liệu không hợp lệ.

---

# TASK A.7 — TÍCH HỢP VÀO PIPELINE HIỆN TẠI

## 🎯 Mục tiêu

Đảm bảo chức năng chọn màu mới hoạt động với toàn bộ hệ thống hiện có.

## Pipeline bắt buộc giữ nguyên

```text
Image Upload
     ↓
HSV Segmentation
     ↓
Median Filter
     ↓
Morphology
     ↓
Final Mask
     ↓
Evaluation (optional)
```

### Kiểm tra

- Chọn màu trước khi xử lý.
- Đổi màu sau khi đã tải ảnh.
- Chỉnh HSV sau khi chọn màu.
- Xử lý lại cùng một ảnh với màu khác.
- Không làm mất ảnh đầu vào.
- Không ghi đè tùy tiện các kết quả trước.
- Không phá vỡ cơ chế tải Mask.
- Không phá vỡ chức năng Evaluation.
- Không phá vỡ ExperimentRunner.

ExperimentRunner phải tiếp tục hoạt động với các cấu hình cũ.

Nếu cần bảo đảm tương thích với cấu trúc HSV mới, chỉ điều chỉnh phần liên quan tối thiểu và kiểm thử hồi quy.

### DONE

Toàn bộ pipeline hoạt động với màu được chọn mà không phải viết lại các thuật toán hiện tại.

---

# TASK A.8 — KIỂM THỬ HSV PRESET VÀ MULTI-COLOR

## 🎯 Mục tiêu

Chứng minh chức năng chọn 15 màu hoạt động đúng, không chỉ hiển thị đẹp trên giao diện.

## 8.1 — Kiểm thử 15 preset

Kiểm tra từng lựa chọn:

```text
[ ] RED
[ ] RED-ORANGE
[ ] ORANGE
[ ] YELLOW-ORANGE
[ ] YELLOW
[ ] YELLOW-GREEN
[ ] GREEN
[ ] BLUE-GREEN
[ ] BLUE
[ ] BLUE-PURPLE
[ ] PURPLE
[ ] RED-PURPLE
[ ] WHITE
[ ] BLACK
[ ] GRAY
```

Với từng màu kiểm tra:

```text
Preset tồn tại
HSV hợp lệ
Frontend nạp đúng thông số
Backend nhận đúng thông số
Mask được tạo thành công
```

## 8.2 — Kiểm thử riêng màu đỏ

Kiểm tra:

```text
Hue Range 1
Hue Range 2
Mask Range 1
Mask Range 2
Combined Mask
```

Đảm bảo không bỏ mất các vùng màu đỏ nằm gần hai đầu thang Hue.

## 8.3 — Kiểm thử màu đặc biệt

Kiểm tra:

```text
WHITE:
Saturation thấp + Value cao.

BLACK:
Value thấp.

GRAY:
Saturation thấp + Value trung gian.
```

Đảm bảo không bắt buộc Hue đối với các nhóm màu này.

## 8.4 — Kiểm thử chỉnh thủ công

```text
Chọn RED
    ↓
Điều chỉnh H/S/V
    ↓
Xử lý
    ↓
Kiểm tra Mask

Chọn GREEN
    ↓
Điều chỉnh H/S/V
    ↓
Reset
    ↓
Kiểm tra preset GREEN được khôi phục
```

## 8.5 — Kiểm thử chuyển đổi màu

```text
RED → GREEN
GREEN → BLUE
BLUE → YELLOW
YELLOW → WHITE
WHITE → BLACK
BLACK → GRAY
GRAY → RED-PURPLE
```

Đảm bảo không giữ lại thông số không phù hợp của màu trước.

## 8.6 — Kiểm thử hồi quy

Chạy lại các test hiện có liên quan:

```text
test_hsv
test_median_filter
test_morphology
test_evaluation
test_experiment
```

Sử dụng tên test theo cấu trúc thực tế của project.

Không tự ý bỏ test FAIL hoặc sửa test chỉ để đạt PASS.

Nếu test có nguy cơ ghi dữ liệu vào Dataset, Ground Truth hoặc thư mục kết quả, phải kiểm tra trước và không chạy khi chưa bảo đảm an toàn.

## DONE

Có báo cáo:

```text
Total Tests
PASS
FAIL
SKIP
Not Run
```

Ghi rõ nguyên nhân từng test FAIL hoặc SKIP.

Không tuyên bố 15 màu đã được kiểm chứng chất lượng chỉ dựa vào việc API trả về Mask thành công.

Phải phân biệt:

```text
Preset Loading: PASS
Mask Generation: PASS
Real Image Validation: PASS / NOT VERIFIED
```

---

# TASK A.9 — KIỂM THỬ THỰC TẾ TRÊN ẢNH

## 🎯 Mục tiêu

Kiểm tra khả năng phân đoạn của các preset bằng ảnh thực tế.

## Cách làm

Sử dụng ảnh hiện có trong project hoặc ảnh thử nghiệm phù hợp.

Ưu tiên ảnh có màu mục tiêu rõ ràng, nền không quá phức tạp và điều kiện ánh sáng khác nhau.

Với mỗi nhóm màu, kiểm tra:

```text
Ảnh gốc
Mask kết quả
Ảnh sau Median Filter
Ảnh sau Morphology
```

Ghi nhận:

```text
Tên ảnh
Màu được chọn
HSV Preset
Mask có tạo đúng không?
Đối tượng có được tách không?
Nền có bị nhận nhầm không?
Lỗi quan sát được
```

Nếu có Ground Truth hợp lệ:

```text
Pixel Accuracy
IoU
Precision
Recall
F1 (nếu module hiện tại hỗ trợ)
```

Không tự tạo Ground Truth bằng chính thuật toán đang được đánh giá.

Không bắt buộc mọi preset phải đạt cùng một mức Accuracy nếu không có tiêu chí được quy định trong đề bài. Nhưng các preset phải được kiểm tra trên những ảnh phù hợp trước khi tuyên bố chất lượng.

### DONE

Có bảng tổng hợp kết quả thực nghiệm và những giới hạn của từng nhóm màu.

---

# TASK A.10 — GHI BÁO CÁO PHASE A

## 🎯 Mục tiêu

Ghi lại toàn bộ kết quả triển khai và kiểm thử.

Tạo báo cáo theo đúng cấu trúc project hiện tại, ưu tiên:

```text
docs/REPORT/PHASE-A-IMPLEMENTATION-REPORT.md
```

Nếu project đang có quy tắc đặt tên khác, tuân theo quy tắc hiện hành.

### Báo cáo gồm

```markdown
# PHASE A IMPLEMENTATION REPORT

## 1. Tổng quan Phase A

## 2. Các file đã thay đổi

## 3. Chức năng đã triển khai

## 4. Bộ 15 nhóm màu HSV

## 5. Cách hoạt động của Color Palette

## 6. Kết quả đồng bộ Frontend và Backend

## 7. Kết quả kiểm thử Unit Test

## 8. Kết quả kiểm thử API

## 9. Kết quả kiểm thử thực tế

## 10. Lỗi còn tồn tại

## 11. Những giới hạn chưa giải quyết

## 12. Acceptance Criteria

## 13. Kết luận Phase A
```

Báo cáo phải dựa vào code và test thực tế.

Không tự tạo số liệu hoặc tuyên bố chức năng hoàn thành khi chưa có bằng chứng.

---

# TASK A.11 — PHASE A FINAL REVIEW

## 🎯 Mục tiêu

Đánh giá Phase A trước khi chuyển sang Phase B.

### DONE Checklist

```text
[ ] TASK A.1 đã audit code HSV hiện tại

[ ] TASK A.2 đã xây dựng đủ 15 nhóm màu

[ ] TASK A.3 đã xây dựng HSV Preset Manager

[ ] TASK A.4 đã có Color Palette trên giao diện

[ ] TASK A.5 đã đồng bộ HSV Slider

[ ] TASK A.6 đã loại bỏ logic cố định màu đỏ ở Backend

[ ] TASK A.7 đã tích hợp vào pipeline hiện tại

[ ] TASK A.8 đã kiểm thử 15 preset và hồi quy

[ ] TASK A.9 đã kiểm tra ảnh thực tế

[ ] TASK A.10 đã tạo báo cáo triển khai

[ ] TASK A.11 đã review toàn bộ tiêu chí nghiệm thu
```

### Acceptance Criteria

| Tiêu chí | Điều kiện đạt |
|---|---|
| Color Palette | Hiển thị đủ 15 nhóm màu |
| Color Selection | Chọn được từng màu |
| HSV Preset | Nạp đúng preset tương ứng |
| HSV Slider | Cập nhật và chỉnh tay được |
| Reset | Khôi phục đúng màu đang chọn |
| Multi Hue | Hỗ trợ nhiều khoảng Hue |
| Red | Xử lý hai khoảng Hue |
| White | Xử lý bằng điều kiện S/V phù hợp |
| Black | Xử lý bằng điều kiện V phù hợp |
| Gray | Xử lý bằng điều kiện S/V phù hợp |
| Backend | Không còn cố định màu đỏ |
| Frontend/API | Đồng bộ chính xác thông số |
| Pipeline | Không phá vỡ các bước xử lý cũ |
| Regression | Không làm hỏng chức năng cũ |
| Report | Có bằng chứng và kết quả kiểm thử |

Mỗi tiêu chí phải có trạng thái:

```text
PASS
FAIL
PARTIAL
NOT VERIFIED
```

Không đánh dấu PASS nếu chưa có bằng chứng.

### Điều kiện hoàn thành Phase A

Phase A chỉ được xem là hoàn thành khi:

1. Có đủ 15 nhóm màu lựa chọn.
2. HSV preset hoạt động đúng.
3. Chỉnh tay và Reset hoạt động đúng.
4. Backend không còn cố định màu đỏ.
5. Mask được tạo theo màu được chọn.
6. Pipeline cũ hoạt động bình thường.
7. Các kiểm thử liên quan có kết quả được xác minh.
8. Báo cáo triển khai đầy đủ.

Nếu còn tiêu chí quan trọng FAIL hoặc PARTIAL, phải ghi rõ Phase A chưa hoàn thành.

---

## 🛑 STOP RULE

Sau khi hoàn thành Phase A:

**DỪNG.**

Không tự chuyển sang Phase B.

Không tự triển khai chức năng so sánh nhiều ngưỡng HSV trong Phase A.

Chỉ khi người dùng xác nhận:

```text
PHASE A DONE
```

mới được chuyển tiếp:

```text
PHASE B — SO SÁNH NGƯỠNG HSV
```

---

# 📋 TỔNG KẾT PHASE A

```text
PHASE A — MULTI-COLOR HSV RECOGNITION
│
├── TASK A.1
│   └── Audit Code HSV hiện tại
│
├── TASK A.2
│   └── Xây dựng 15 nhóm màu
│
├── TASK A.3
│   └── HSV Preset Manager
│
├── TASK A.4
│   └── Color Palette Frontend
│
├── TASK A.5
│   └── HSV Slider Synchronization
│
├── TASK A.6
│   └── Backend Multi-Color Segmentation
│
├── TASK A.7
│   └── Tích hợp Pipeline
│
├── TASK A.8
│   └── Unit Test & Regression Test
│
├── TASK A.9
│   └── Real Image Validation
│
├── TASK A.10
│   └── Implementation Report
│
└── TASK A.11
    └── Phase A Final Review
```

---

## THỨ TỰ THỰC THI

```text
Audit Code hiện tại
        ↓
Xác định logic màu đỏ cố định
        ↓
Thiết kế 15 Color Presets
        ↓
Xây dựng HSV Preset Manager
        ↓
Thiết kế Color Palette
        ↓
Đồng bộ HSV Slider
        ↓
Cập nhật Backend
        ↓
Tích hợp Pipeline
        ↓
Unit Test + Regression Test
        ↓
Kiểm thử ảnh thực tế
        ↓
Tạo Implementation Report
        ↓
Review Acceptance Criteria
        ↓
PHASE A DONE
        ↓
STOP
```

---

## NGUYÊN TẮC QUAN TRỌNG NHẤT

Phase A không chỉ là thêm 15 ô màu lên giao diện.

Phase A phải giải quyết hoàn chỉnh luồng:

```text
SELECT COLOR
      ↓
LOAD HSV PRESET
      ↓
ADJUST HSV
      ↓
SEND TO BACKEND
      ↓
GENERATE MASK
      ↓
PROCESS MASK
      ↓
DISPLAY RESULT
```

Người dùng phải có thể chọn màu trực quan, hiểu được thông số HSV đang sử dụng và chủ động tinh chỉnh khi kết quả chưa tốt.

**Mục tiêu cuối cùng: Chuyển chương trình từ một công cụ chỉ tách màu đỏ thành một công cụ phân đoạn nhiều nhóm màu có thể lựa chọn và điều chỉnh bằng HSV, đồng thời giữ nguyên các chức năng xử lý ảnh đã có.**