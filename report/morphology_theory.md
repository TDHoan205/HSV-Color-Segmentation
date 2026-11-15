# Lý thuyết Toán hình học (Mathematical Morphology)

**Phụ trách:** Nguyễn Quốc Anh — Morphological Operations
**Module trong dự án:** `src/morphology.py`
**Phạm vi:** Task 1 của kế hoạch phân công (Nhóm N05)

---

## 1. Toán hình học là gì?

Toán hình học (Morphology) là nhánh của xử lý ảnh số làm việc trên **cấu trúc hình học** của vật thể thay vì làm việc trên giá trị cường độ từng điểm ảnh.

Các phép toán thông thường (lọc trung vị, lọc Gaussian) đánh giá từng pixel dựa trên vùng lân cận của nó. Ngược lại, phép toán hình học quan tâm đến **quan hệ bao hàm**: một pixel có thuộc về đối tượng hay không phụ thuộc vào việc một mẫu hình học cụ thể có "nằm trọn" trong vùng đối tượng hay không.

Hệ quả quan trọng: toán hình học **bảo toàn hình dạng**. Với một đối tượng hình học rõ ràng (hình vuông, hình tròn, hình tam giác), phép toán hình học với kernel hình học tương ứng sẽ cho ra một đối tượng **cùng loại hình học**, chỉ khác kích thước. Đây chính là lý do Morphology phù hợp cho bài toán phân đoạn màu: nó sửa chữa hình học mà không làm nhòe biên đối tượng như các bộ lọc làm mượt.

Trong dự án này, Morphology được dùng để:

1. **Loại bỏ nhiễu rời rạc** (speck noise) — các đốm trắng nhỏ lơ lửng trong nền.
2. **Lấp đầy lỗ rỗng** (hole) — các vùng đen nằm giữa vùng trắng của cùng một đối tượng.
3. **Làm mượt biên** — loại bỏ các pixel lơ lửng ở rìa vật thể.

---

## 2. Quy ước biểu diễn (Mask Convention)

Bước quan trọng nhất khi đọc lý thuyết Morphology là **hiểu rõ quy ước màu**. Toán hình học cổ điển trên tập con của $\mathbb{R}^2$ coi **điểm thuộc tập** là "điểm đối tượng". Khi ánh xạ sang ảnh số, quy ước này phải được cụ thể hóa.

### Quy ước của dự án

| Thuộc tính | Giá trị | Ý nghĩa |
|---|---|---|
| Số kênh | 1 | Mask nhị phân, không phải ảnh màu |
| Kiểu dữ liệu | `uint8` | Dải 0–255 |
| **Đối tượng (foreground)** | **255** | Pixel thuộc về vật thể — màu trắng |
| **Nền (background)** | **0** | Pixel không thuộc vật thể — màu đen |
| Kích thước | $(H, W)$ | Giữ nguyên so với ảnh gốc |

Như vậy tập hình học $A$ mà các công thức dưới đây thao tác trên chính là:

$$
A = \{(x, y) \in \mathbb{Z}^2 \mid M(x, y) = 255\}
$$

trong đó $M$ là mảng mask. Tập nền là $A^c$.

> **Lưu ý về ảnh nhị phân hiển thị:** nhiều tài liệu học thuật dùng quy ước ngược lại (foreground = 0, background = 255). Vì vậy khi đọc một ví dụ lý thuyết hoặc khi so sánh với người khác, **luôn kiểm tra quy ước trước**. Trong toàn bộ báo cáo này, foreground luôn là 255.

### Vì sao chọn quy ước này?

- Phù hợp với hàm `cv2.inRange` của OpenCV: kết quả trả về 255 cho pixel thuộc ngưỡng, 0 cho pixel còn lại — đúng với quy ước foreground = 255.
- Cho phép dùng chung mã đo IoU/Accuracy với module `src/evaluation.py` mà không cần chuyển đổi.
- Nền đen – đối tượng trắng là cách hiển thị trực quan nhất trên báo cáo in.

---

## 3. Phần tử cấu trúc (Structuring Element $B$)

Phần tử cấu trúc $B$ là "hình dạng" mà phép toán dùng để dò ảnh. Trong OpenCV, $B$ được biểu diễn bằng một ma trận nhị phân nhỏ, mỗi phần tử là 1 (pixel thuộc kernel) hoặc 0.

### 3.1. Ba hình dạng được hỗ trợ

Dự án hỗ trợ ba hình kernel, ánh xạ từ `cv2.getStructuringElement`:

| Hình | Hằng số OpenCV | Mô tả | Số pixel 5×5 | Ứng dụng |
|---|---|---|---:|---|
| Hình chữ nhật | `cv2.MORPH_RECT` | Hình vuông đặc | 25 | Nhanh, phù hợp vật thể vuông |
| Hình elip | `cv2.MORPH_ELLIPSE` | Hình tròn rời rạc hóa | 13 | Mượt hơn, giữ hình tròn |
| Hình chữ thập | `cv2.MORPH_CROSS` | Chữ thập | 9 | Ít nhạy với góc vuông |

Minh họa trực quan ba kernel 5×5 (● = pixel thuộc kernel):

```
        RECT (25)          ELLIPSE (13)         CROSS (9)
     ● ● ● ● ●          ● ● ● ● ●          ●     ●
     ● ● ● ● ●            ● ● ●            ● ● ● ● ●
     ● ● ● ● ●          ● ● ● ● ●          ●     ●
     ● ● ● ● ●            ● ● ●            ● ● ● ● ●
     ● ● ● ● ●          ● ● ● ● ●          ●     ●
```

Hình elip cho đường viền tròn mềm mại nên hiệu quả hơn với vật thể tròn; hình chữ nhật cho biên vuông sắc nét; hình chữ thập rẻ nhất nhưng xử lý kém các góc vuông.

### 3.2. Kích thước kernel

Kích thước kernel **phải là số lẻ dương** (3, 5, 7, 9, ...). Lý do:

- Kernel có tâm đối xứng, cho phép định nghĩa "pixel trung tâm" rõ ràng — đây là điểm neo cho phép phép toán được định nghĩa tại mỗi vị trí.
- Với kernel chẵn, tâm sẽ nằm giữa hai pixel và phép toán trở nên phụ thuộc vị trí lệch (asymmetric), gây hiệu ứng dịch chuyển 1 pixel trên toàn ảnh.

Trong `src/morphology.py`, kích thước kernel và số lần lặp (`iterations`) là hai tham số độc lập. Một kernel 3×3 lặp 3 lần **không** tương đương kernel 9×9: kernel lặp có hiệu ứng giống "chày sạch" (grayscale erosion/dilation) và làm mềm hơn, trong khi kernel lớn giữ các góc vuông sắc hơn.

---

## 4. Phép co (Erosion)

### 4.1. Định nghĩa hình thức

$$
A \ominus B = \{ z \in E \mid B_z \subseteq A \}
$$

trong đó:

- $E$ là miền ảnh (lưới các pixel),
- $B_z$ là bản dịch của $B$ sao cho gốc của $B$ nằm tại pixel $z$,
- $\subseteq$ nghĩa là "là tập con của".

### 4.2. Diễn giải trực quan

**Pixel $z$ được giữ lại khi và chỉ khi toàn bộ phần tử cấu trúc $B$, khi đặt tâm vào $z$, đều nằm trong vùng đối tượng.**

Nói cách khác: đặt "cái khuôn" $B$ lên ảnh. Pixel trung tâm của khuôn được tô trắng nếu khuôn **lót trọn** trong vùng trắng; nếu khuôn chạm ra nền đen thì pixel đó bị xóa.

### 4.3. Tính chất

1. **Co nhỏ:** luôn có $A \ominus B \subseteq A$. Erosion không bao giờ tạo ra pixel mới.
2. **Loại bỏ đốm rời rạc:** một đốm trắng nhỏ hơn kernel sẽ bị xóa hoàn toàn.
3. **Mài mòn biên:** mỗi pixel sát biên bị mất, làm đối tượng co lại.
4. **Phá vỡ cầu nối mỏng:** khoảng nối hẹp giữa hai vùng trắng sẽ bị cắt đứt.
5. **Bất biến với phép dịch:** $(A \oplus B) \ominus B \supseteq A$ — closing luôn bao trọn A (xem mục 6).

### 4.4. Ví dụ

Với một hình vuông trắng 7×7 trên nền đen và kernel vuông 3×3:

```
   TRƯỚC (7×7)              SAU EROSION (5×5)
  ■ ■ ■ ■ ■ ■ ■           □ □ ■ ■ ■ □ □
  ■ ■ ■ ■ ■ ■ ■           □ □ ■ ■ ■ □ □
  ■ ■ ■ ■ ■ ■ ■     ->    ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■           ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■           □ □ ■ ■ ■ □ □
  ■ ■ ■ ■ ■ ■ ■           □ □ ■ ■ ■ □ □
  ■ ■ ■ ■ ■ ■ ■
```

Mỗi cạnh lùi vào 1 pixel vì kernel 3×3 yêu cầu cả 3×3 đều phải trắng.

---

## 5. Phép giãn (Dilation)

### 5.1. Định nghĩa hình thức

$$
A \oplus B = \{ z \in E \mid (B^s)_z \cap A \neq \emptyset \}
$$

trong đó $(B^s)_z$ là bản đối xứng của $B$ đặt tại $z$. Vì $B$ đã đối xứng ở đây nên $(B^s)_z = B_z$.

### 5.2. Diễn giải trực quan

**Pixel $z\) được tô trắng nếu phần tử cấu trúc $B$, khi đặt tâm vào $z$, chạm ít nhất một pixel trắng của $A$.**

Nói cách khác: đặt khuôn $B$ lên mọi pixel trắng, rồi tô trắng toàn bộ vùng khuôn che phủ. Kết quả là $A$ được "nở ra".

### 5.3. Tính chất

1. **Nở rộng:** luôn có $A \subseteq A \oplus B$. Dilation không bao giờ xóa pixel.
2. **Lấp đầy lỗ nhỏ:** một lỗ đen có đường kính nhỏ hơn kernel sẽ bị lấp kín.
3. **Nối liền vật thể:** khoảng cách giữa hai vùng trắng nhỏ hơn kernel sẽ được nối lại.
4. **Làm tròn/gợn núi biên:** các khuyết nhỏ trên biên được lấp đầy, làm biên mượt hơn.
5. **Phụ thuộc thứ tự:** erosion và dilation **không** giao hoán với nhau, tức $A \ominus B \oplus B \neq A \oplus B \ominus B$.

### 5.4. Ví dụ

Với cùng hình vuông 7×7 và kernel vuông 3×3:

```
   TRƯỚC (7×7)              SAU DILATION (9×9)
  ■ ■ ■ ■ ■ ■ ■           □ □ □ ■ ■ ■ □ □ □
  ■ ■ ■ ■ ■ ■ ■           □ □ ■ ■ ■ ■ ■ □ □
  ■ ■ ■ ■ ■ ■ ■     ->    □ ■ ■ ■ ■ ■ ■ ■ □
  ■ ■ ■ ■ ■ ■ ■           ■ ■ ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■           □ ■ ■ ■ ■ ■ ■ ■ □
  ■ ■ ■ ■ ■ ■ ■           □ □ ■ ■ ■ ■ ■ □ □
  ■ ■ ■ ■ ■ ■ ■           □ □ □ ■ ■ ■ □ □ □
```

Mỗi cạnh nở ra 1 pixel.

---

## 6. Phép mở (Opening)

### 6.1. Định nghĩa hình thức

$$
A \circ B = (A \ominus B) \oplus B
$$

Tức là: **co trước, rồi giãn**.

### 6.2. Diễn giải trực quan

1. Erosion xóa sạch các đốm trắng rời rạc nhỏ hơn kernel.
2. Dilation "phục hồi" kích thước của vật thể lớn đã bị co.

Vì vậy opening có tính chất: **loại bỏ đốm rời rạc mà không thay đổi hình dạng của vật thể lớn**.

### 6.3. Tính chất quan trọng

1. **Opening là phép mở rộng:** mở rộng (opening) một tập đã mở không làm thay đổi nó: $(A \circ B) \circ B = A \circ B$.
2. **Anti-extensive:** $A \circ B \subseteq A$. Opening không bao giờ tạo pixel mới.
3. **Loại bỏ cầu nối mỏng:** khoảng nối hẹp bị cắt vì erosion đã cắt trước, và dilation không đủ lớn để nối lại.

### 6.4. Ví dụ

Mask có một đốm trắng 4×4 tách rời và hai hình vuông lớn:

```
   TRƯỚC                   SAU OPENING (kernel 5×5)
  □ ■ □ □ □ □ □           □ □ □ □ □ □ □
  □ ■ ■ ■ □ □ □      ->   □ □ □ □ □ □ □
  □ ■ ■ ■ □ □ □           ■ ■ ■ ■ ■ ■ ■
  □ ■ ■ ■ □ □ □           ■ ■ ■ ■ ■ ■ ■
  □ □ □ □ □ □ □           ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■           □ □ □ □ □ □ □
  ■ ■ ■ ■ ■ ■ ■           □ □ □ □ □ □ □
  □ □ □ □ □ □ □           ■ ■ ■ ■ ■ ■ ■
```

Đốm 4×4 biến mất hoàn toàn; các hình vuông lớn giữ nguyên kích thước.

---

## 7. Phép đóng (Closing)

### 7.1. Định nghĩa hình thức

$$
A \bullet B = (A \oplus B) \ominus B
$$

Tức là: **giãn trước, rồi co**.

### 7.2. Diễn giải trực quan

1. Dilation lấp kín các lỗ đen nhỏ và các khuyết nhỏ trên biên.
2. Erosion "phục hồi" kích thước vật thể đã bị nở.

Vì vậy closing: **lấp đầy lỗ rỗng và khe hở hẹp mà không thay đổi hình dạng của vật thể lớn**.

### 7.3. Tính chất quan trọng

1. **Closing là phép đóng:** $(A \bullet B) \bullet B = A \bullet B$.
2. **Extensive:** $A \subseteq A \bullet B$. Closing không bao giờ xóa pixel.
3. **Nối liền vật thể:** hai vùng trắng cách nhau khoảng trống nhỏ sẽ được nối lại.
4. **Lấp đầy lỗ bên trong:** các lỗ đen nằm hoàn toàn bên trong vùng trắng sẽ bị lấp kín.

### 7.4. Ví dụ

Mask có hai hình vuông lớn, mỗi hình chứa một lỗ đen 3×3:

```
   TRƯỚC                   SAU CLOSING (kernel 5×5)
  ■ ■ ■ ■ ■ ■ ■           ■ ■ ■ ■ ■ ■ ■
  ■ ■ □ □ □ ■ ■           ■ ■ ■ ■ ■ ■ ■
  ■ ■ □ □ □ ■ ■      ->   ■ ■ ■ ■ ■ ■ ■
  ■ ■ □ □ □ ■ ■           ■ ■ ■ ■ ■ ■ ■
  ■ ■ ■ ■ ■ ■ ■           ■ ■ ■ ■ ■ ■ ■
  □ □ □ □ □ □ □           □ □ □ □ □ □ □
```

Lỗ đen 3×3 bị lấp kín hoàn toàn; viền ngoài giữ nguyên.

---

## 8. Bảng so sánh tổng hợp

| Phép toán | Công thức | Ảnh hưởng | Tính chất tập hợp | Dùng để |
|---|---|---|---|---|
| **Erosion** | $A \ominus B$ | Co nhỏ | $A \ominus B \subseteq A$ | Loại đốm rời, mài biên |
| **Dilation** | $A \oplus B$ | Nở rộng | $A \subseteq A \oplus B$ | Lấp lỗ, nối vật thể |
| **Opening** | $(A \ominus B) \oplus B$ | Giữ nguyên vật thể lớn | $A \circ B \subseteq A$ | Loại nhiễu speck |
| **Closing** | $(A \oplus B) \ominus B$ | Giữ nguyên vật thể lớn | $A \subseteq A \bullet B$ | Lấp lỗ, nối khe hẹp |

### 8.1. Các bất biến then chốt

Từ định nghĩa, suy ra ngay:

$$
A \ominus B \subseteq A \subseteq A \oplus B
\qquad\text{và}\qquad
A \circ B \subseteq A \subseteq A \bullet B
$$

Hai bất biến này được dùng để **kiểm chứng tính đúng đắn** của module trong bộ test `tests/test_morphology.py` — mọi cặp kết quả đều được kiểm tra theo đúng các quan hệ trên.

### 8.2. Erosion và Dilation không giao hoán

$$
A \ominus B \oplus B \neq A \oplus B \ominus B
$$

Đây là lý do thứ tự **Median → Closing** trong pipeline không thể đảo thành **Closing → Median**, và cũng giải thích vì sao opening và closing cho kết quả khác nhau dù cùng kernel.

---

## 9. Tham số trong module `src/morphology.py`

| Tham số | Kiểu | Giá trị hợp lệ | Mô tả |
|---|---|---|---|
| `kernel_size` | `int` | Số lẻ dương (3, 5, 7, ...) | Kích thước phần tử cấu trúc |
| `kernel_shape` | `str` | `'rect'`, `'ellipse'`, `'cross'` | Hình dạng kernel |
| `iterations` | `int` | `>= 1` | Số lần lặp phép toán |
| `mask` | `numpy.ndarray` | 1 kênh, `uint8`, 2 chiều | Mask đầu vào |

Giao diện chính:

```python
from src.morphology import MorphologyOperator

op = MorphologyOperator(kernel_size=5, kernel_shape='ellipse')

result = op.erode(mask)
result = op.dilate(mask)
result = op.open(mask)
result = op.close(mask)

# Áp dụng chuỗi phép toán
result = op.apply_sequence(mask, [('close', {'iterations': 1})])
```

### 9.1. Xử lý lỗi

Module ném `ValueError` cho các trường hợp:

- `kernel_size` không phải số lẻ dương.
- `kernel_shape` không thuộc ba hình được hỗ trợ.
- `iterations` nhỏ hơn 1.
- Mask là `None`, rỗng, hoặc không phải mảng 2 chiều.
- Tên phép toán trong `apply_sequence` không được hỗ trợ.

Chi tiết đầy đủ nằm trong `src/README_module_morphology.md`.

---

## 10. Morphology trong pipeline của dự án

### 10.1. Vị trí trong chuỗi xử lý

```
BGR  ->  HSV Segmentation  ->  Median Filter  ->  Morphology  ->  Evaluation
```

Morphology đặt **sau** Median Filter vì:

- Median Filter đã loại bỏ nhiễu muối-tiêu (salt-and-pepper) ở mức pixel đơn lẻ.
- Morphology xử lý ở mức **cấu trúc**: các đốm lớn hơn, các lỗ rỗng, các cầu nối mỏng.
- Đặt Morphology trước Median sẽ làm Median phải xử lý mask đã bị biến dạng, tốn thêm 1 lượt lọc nữa mà không thu được lợi ích gì.

### 10.2. Cấu hình mặc định

Pipeline sử dụng kernel **5×5 hình elip** cho Closing. Lý do chọn 5×5 thay vì 3×3:

- Kernel 3×3 ellipse chỉ lấp được 4/9 pixel của một lỗ đen 3×3 (đo được thực tế), tức **không lấp kín được** lỗ vuông.
- Kernel 5×5 lấp kín hoàn toàn lỗ 3×3 (9/9 pixel) và xóa sạch đốm trắng 4×4.
- 5×5 vẫn đủ nhỏ để không làm mất các cấu trúc mỏng quan trọng trong dữ liệu dự án.

### 10.3. Vì sao dùng Closing chứ không phải Opening trong pipeline?

Trên bộ dữ liệu thật của dự án, đo được:

| Bước | IoU trung bình (10 ảnh) |
|---|---|
| HSV thuần | 0.7137 |
| + Median 5×5 | 0.7135 |
| + Closing 5×5 ellipse | 0.7135 |

Closing **không làm thay đổi** IoU trên dữ liệu thật — không tốt, không xấu. Đây không phải lỗi mà là **kết quả thực nghiệm đúng**: Ground Truth trong `data/gt/` được vẽ bằng hình học vector sạch nên vùng đối tượng không có lỗ rỗng và nền không có đốm nhiễu để xử lý. Chi tiết phân tích đầy đủ nằm trong `report/morphology.md`.

Vì vậy, để **chứng minh** Morphology hoạt động đúng, nhóm sử dụng bộ fixture tổng hợp (`tests/fixtures/morphology.py`) có kiểm soát: đốm trắng 4×4 và lỗ đen 3×3 đặt ở tọa độ cố định, cho phép đo chính xác tác dụng của từng phép toán.

---

## 11. Tóm tắt

1. Toán hình học thao tác trên **quan hệ bao hàm** hình học, không phải trên giá trị cường độ.
2. Quy ước của dự án: foreground = 255, background = 0, 1 kênh, kiểu `uint8`.
3. Phần tử cấu trúc $B$ có kích thước **lẻ** và ba hình dạng: `rect`, `ellipse`, `cross`.
4. **Erosion** giữ pixel khi $B_z \subseteq A$ — làm vật thể co lại.
5. **Dilation** giữ pixel khi $B_z \cap A \neq \emptyset$ — làm vật thể nở ra.
6. **Opening** = erosion rồi dilation — loại đốm rời rạc.
7. **Closing** = dilation rồi erosion — lấp lỗ rỗng và khe hở.
8. Bất biến kiểm chứng: $A \ominus B \subseteq A \subseteq A \oplus B$ và $A \circ B \subseteq A \subseteq A \bullet B$.
9. Trong pipeline, Morphology chạy **sau Median** với kernel **5×5 ellipse** dạng Closing.

---

## Tài liệu tham khảo

- OpenCV, *Morphological Transformations*: https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html
- OpenCV, *Structuring Element*: https://docs.opencv.org/4.x/d4/d86/group__imgproc__filter.html
- Gonzalez & Woods, *Digital Image Processing*, 4th Edition, Chapter 10 — Mathematical Morphology and Its Applications
- Jain, *Fundamentals of Digital Image Processing*, Chapter 5 — Binary Image Processing
- Szeliski, *Computer Vision: Algorithms and Applications*, 2nd Edition, Section 3.3 — Binary Image Processing
