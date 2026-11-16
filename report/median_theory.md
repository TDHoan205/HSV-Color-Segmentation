# Lý thuyết Bộ lọc Trung Vị (Median Filter)

Tài liệu lý thuyết cho module [`src/median_filter.py`](../src/median_filter.py)
của Anh Tuấn. Phần báo cáo ứng dụng nằm ở [median.md](median.md).

---

## 1. Định nghĩa

Bộ lọc trung vị là một bộ lọc **phi tuyến** (non-linear) thay thế giá trị mỗi
pixel bằng **giá trị trung vị** (median) của các pixel lân cận nó nằm trong
một cửa sổ vuông. Với cửa sổ kích thước $k \times k$:

$$\tilde{I}(x, y) = \operatorname{median}\{ I(i, j) \mid |i-x| \leq r,\; |j-y| \leq r \},\qquad r = \tfrac{k-1}{2}$$

Giá trị trung vị của một tập $N = k^2$ số là phần tử ở vị trí
$\lfloor N/2 \rfloor$ sau khi sắp xếp tăng dần (với $N$ lẻ, vị trí chính
giữa là duy nhất). Với $k = 3$ thì $N = 9$ và vị trí chính giữa là $\lfloor
9/2 \rfloor = 4$ (đánh số từ 0).

## 2. Thuật toán

1. Duyệt từng pixel $(x, y)$ của ảnh.
2. Thu thập $k^2$ giá trị trong cửa sổ vuông $k \times k$ lấy $(x, y)$ làm tâm.
3. Sắp xếp tăng dần $k^2$ giá trị đó.
4. Chọn phần tử ở vị trí $\lfloor k^2/2 \rfloor$ làm giá trị mới của pixel.
5. Với biên ảnh, OpenCV lấy giá trị biên bằng phép nội suy `BORDER_REPLICATE`
   (nhân bản hàng/cột biên), nên kích thước ảnh không thay đổi.

Trong `median_filter.py`, các bước trên do `cv2.medianBlur(mask_raw,
kernel_size)` thực hiện với thuật toán đếm histogram cho ảnh 8 bit, nên độ
phức tạp thực tế là $O(H \cdot W \cdot k)$ thay vì $O(H \cdot W \cdot k^2)$
của cách sắp xếp trực tiếp.

## 3. Vì sao trung vị khử nhiễu xung tốt hơn trung bình

### 3.1. Lọc trung bình là phép trung bình tuyến tính

Bộ lọc trung bình (Mean) và lọc Gaussian đều thay pixel bằng **tổng có trọng
số** của các pixel lân cận:

$$\operatorname{mean} = \frac{1}{k^2}\sum I(i,j),\qquad G = \sum w(i,j)\, I(i,j),\;\; \sum w = 1$$

Mỗi pixel nhiễu đóng góp **một phần** vào kết quả, nên giá trị đầu ra bị kéo
lệch. Với một điểm nhiễu trắng 255 giữa vùng nền 0 trong cửa sổ $3 \times 3$:

$$\operatorname{mean} = \frac{255}{9} \approx 28{,}3 \;\longrightarrow\; \text{làm mờ vùng nền}$$

Hai hậu quả nghiêm trọng với mask nhị phân:

* **Tạo ra mức xám trung gian** (28, 43, 172…) - vi phạm quy ước mask chỉ
  gồm `0` và `255` của dự án, và làm hỏng ngưỡng nhị phân ở bước đánh giá.
* **Làm mờ biên**: vùng đối tượng và vùng nền bị trộn lẫn, đường viền đối
  tượng lùi vào trong, đặc biệt nghiêm trọng với vùng đối tượng nhỏ.

### 3.2. Trung vị là thống kê thứ tự (rank statistic)

Trung vị **không phải** tổng các pixel nên nó không bị "kéo" bởi một điểm nhiễu
đơn lẻ. Xét cửa sổ $k \times k$ có $N = k^2$ pixel, trong đó $m$ pixel bị
nhiễu và $N - m$ pixel là tín hiệu. Trung vị chỉ đổi khi số pixel nhiễu đủ
lớn để thay đổi phần tử ở vị trí chính giữa:

$$m < \frac{k^2 + 1}{2} \;\Longrightarrow\; \operatorname{median} = \text{giá trị tín hiệu}$$

Với $k = 3$: chỉ cần **4 pixel nhiễu trên tổng 9** là có thể làm đổi kết quả.
Vì vậy bộ lọc trung vị loại bỏ được nhiễu xung (salt-and-pepper) rất hiệu quả:
một điểm nhiễu đơn lẻ chiếm 1/9 cửa sổ, không thể ảnh hưởng tới phần tử chính
giữa.

### 3.3. Tính phi tuyến và bảo toàn biên

Với mask nhị phân chỉ chứa hai giá trị $\{0, 255\}$, trung vị của một cửa sổ
bất kỳ **luôn là 0 hoặc 255** (trung vị của tập hai giá trị là một trong hai
giá trị đó). Hệ quả:

* Bộ lọc **không sinh ra mức xám trung gian**, không vi phạm quy ước mask.
* Biên được bảo toàn theo nghĩa: một pixel nằm trên biên chỉ bị đổi khi trong
  cửa sổ của nó có **quá nửa** số pixel thuộc vùng bên kia biên. Ngược lại,
  lọc trung bình làm biên **mờ dần** ở mọi vị trí.
* Tính phi tuyến còn cho một tính chất quan trọng: bộ lọc **không bảo toàn
  trung bình cục bộ** (không phải bộ lọc "đồng nhất theo cấp xám"), nên nó
  không kéo theo hiệu ứng làm mờ vùng đồng nhất.

Tóm lại, bộ lọc trung vị là bộ lọc **bảo toàn cạnh** (edge-preserving) và
**loại bỏ nhiễu xung**, đúng hai đặc tính cần cho bước làm sạch mask trong
pipeline này.

## 4. Ví dụ tính tay trên ma trận 3 × 3

### 4.1. Nhiễu muối (điểm trắng 255 nằm giữa vùng nền 0)

Xét một cửa sổ $3 \times 3$ lấy tâm là một điểm nhiễu trắng nằm giữa vùng
nền đen:

$$
\begin{bmatrix}
0 & 0 & 0 \\
0 & 255 & 0 \\
0 & 0 & 0
\end{bmatrix}
$$

Bước 1 - thu thập 9 phần tử của cửa sổ:
`0, 0, 0, 0, 255, 0, 0, 0, 0`

Bước 2 - sắp xếp tăng dần:
`0, 0, 0, 0, 0, 0, 0, 0, 255`

Bước 3 - lấy phần tử tại vị trí $\lfloor 9/2 \rfloor = 4$ (đánh số từ 0):
`0`

**Kết luận:** pixel nhiễu 255 bị thay bằng 0, điểm nhiễu biến mất khỏi mask.
Trong khi đó, lọc trung bình trên cùng cửa sổ cho $255/9 \approx 28$ - tức
là nền bị "bẩn" bởi một giá trị trung gian không hợp lệ với mask nhị phân.

### 4.2. Nhiễu tiêu (điểm đen 0 nằm giữa vùng đối tượng 255)

$$
\begin{bmatrix}
255 & 255 & 255 \\
255 & 0 & 255 \\
255 & 255 & 255
\end{bmatrix}
$$

Thu thập: `255, 255, 255, 255, 0, 255, 255, 255, 255`
Sắp xếp: `0, 255, 255, 255, 255, 255, 255, 255, 255`
Phần tử tại vị trí 4: `255`

**Kết luận:** lỗ đen đơn lẻ bị lấp đầy, vùng đối tượng trở lại liền mạch.

### 4.3. Khi nào phép lọc trung vị *không* khử được nhiễu

Với cùng cửa sổ $3 \times 3$, nếu có **5 pixel nhiễu trở lên** thì phần tử ở
vị trí chính giữa có thể là pixel nhiễu:

$$
\begin{bmatrix}
255 & 255 & 0 \\
255 & 255 & 0 \\
0 & 0 & 0
\end{bmatrix}
\quad\Rightarrow\quad
\text{sắp xếp: } 0,0,0,0,255,255,255,255,255 \;\Rightarrow\; \text{trung vị} = 255
$$

Đây chính là lý do cụm nhiễu 2 × 4 trong fixture `dense_noise_clusters.png`
sống sót qua kernel 3 × 3 nhưng bị loại bỏ bởi kernel 5 × 5: cửa sổ 5 × 5
chỉ chứa 8 pixel trắng trên 25 pixel, nên trung vị trở về 0.

## 5. Tác dụng phụ khi tăng kích thước kernel

Bộ lọc trung vị không chỉ khử nhiễu mà còn **xóa các cấu trúc mảnh** và **bo
tròn các góc nhọn**:

* Một đường mảnh có bề rộng $w$ sống sót khi $w$ chiếm hơn một nửa cửa sổ,
  tức là khi $w \geq \lceil k/2 \rceil$. Với $k = 3$: đường 1 pixel bị xóa,
  đường 2 pixel còn; với $k = 5$: đường 2 pixel cũng bị xóa.
* Góc nhọn của vùng đối tượng bị bo tròn dần theo kích thước kernel, vì góc
  nhọn là nơi mà số pixel thuộc vùng bên trong trong cửa sổ chưa đủ đa số.
* Biên cong bị lùi vào trong khoảng $k/2$ pixel (đây chính là lý do ảnh tham
  chiếu `expected_clean_3x3.png` nhỏ hơn hình tròn gốc khoảng 1 pixel).

Vì vậy kernel lớn hơn không đồng nghĩa với kết quả tốt hơn: phải cân bằng
giữa khả năng khử nhiễu và mức độ bảo toàn chi tiết.

## 6. Bảng so sánh nhanh các bộ lọc

| Đặc tính | Trung bình (Mean) | Gaussian | Trung vị (Median) |
|---|---|---|---|
| Tính chất | Tuyến tính | Tuyến tính | **Phi tuyến** |
| Xử lý nhiễu xung (salt-and-pepper) | Kém | Kém | **Rất tốt** |
| Xử lý nhiễu Gaussian | Tốt | Rất tốt | Trung bình |
| Bảo toàn biên | Kém | Kém | **Tốt** |
| Tạo mức xám trung gian trên mask 0/255 | Có | Có | **Không** |
| Chi phí tính toán | Thấp | Thấp | Trung bình ($O(k)$ mỗi pixel với 8 bit) |

## 7. Tài liệu tham khảo

* OpenCV Documentation - Image Processing: *Smoothing Images*
  (https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html)
* Gonzalez, R. C.; Woods, R. E. — *Digital Image Processing*, chương 3
  (Image Enhancement in the Spatial Domain), mục *Median Filtering*.
* Wikipedia — *Median filter*
  (https://en.wikipedia.org/wiki/Median_filter)
