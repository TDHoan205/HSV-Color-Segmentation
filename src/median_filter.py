# -*- coding: utf-8 -*-
"""
Module: median_filter.py
Chức năng: Lọc trung vị (Median Filter) để khử nhiễu Mask nhị phân
Phụ trách: Anh Tuấn

Input: mask_raw (numpy, uint8, 2D, giá trị 0/255) + kernel_size (số lẻ >= 3)
Output: mask_median (numpy, uint8, 2D, giá trị 0/255)

Quy ước:
- Không đổi kích thước ảnh (H x W giữ nguyên)
- Kernel phải là số lẻ: 3, 5, 7, 9, ...
- Mask là mảng NumPy 2 chiều, 1 kênh, dtype uint8
- Mask chỉ chứa giá trị 0 (nền) và 255 (đối tượng)
- Hàm lọc không thay đổi (mutate) mảng đầu vào

API chuẩn:
    apply_median_filter(mask_raw: np.ndarray, kernel_size: int = 3) -> np.ndarray

API tương thích ngược (giữ cho main.py / experiment.py):
    MedianFilter(kernel_size=5).filter(mask)
"""

import cv2
import numpy as np

#: Giá trị hợp lệ của một pixel trong mask nhị phân theo quy ước của nhóm.
BINARY_VALUES = (0, 255)

#: Kích thước kernel mặc định của lớp ``MedianFilter`` (giữ nguyên từ bản cũ).
DEFAULT_KERNEL_SIZE = 5

#: Kích thước kernel lớn nhất được phép dùng (quy ước của nhóm).
MAX_KERNEL_SIZE = 31


def _validate_kernel_size(kernel_size):
    """
    Kiểm tra kích thước kernel của bộ lọc trung vị.

    Args:
        kernel_size: Kích thước kernel vuông (số lẻ, 3 <= k <= 31).

    Returns:
        int: kernel_size đã được chuẩn hóa về kiểu ``int`` thuần.

    Raises:
        TypeError: Nếu kernel_size không phải số nguyên (hoặc là ``bool``).
        ValueError: Nếu kernel_size < 3, kernel_size chẵn hoặc vượt quá
            ``MAX_KERNEL_SIZE``.
    """
    # bool là lớp con của int nên phải loại trước.
    if isinstance(kernel_size, bool):
        raise TypeError(
            "kernel_size phải là số nguyên (int), không phải bool. "
            "Các giá trị hợp lệ: 3, 5, 7, 9, ..."
        )

    if not isinstance(kernel_size, (int, np.integer)):
        raise TypeError(
            f"kernel_size phải là số nguyên (int), nhận: {type(kernel_size).__name__}. "
            "Các giá trị hợp lệ: 3, 5, 7, 9, ..."
        )

    kernel_size = int(kernel_size)

    if kernel_size < 3:
        raise ValueError(
            f"kernel_size phải >= 3, nhận: {kernel_size}. "
            "Kernel 1x1 không làm khử nhiễu."
        )

    if kernel_size % 2 == 0:
        raise ValueError(
            f"kernel_size phải là số lẻ, nhận: {kernel_size}. "
            "Ví dụ hợp lệ: 3, 5, 7, 9, ..."
        )

    if kernel_size > MAX_KERNEL_SIZE:
        raise ValueError(
            f"kernel_size quá lớn (tối đa {MAX_KERNEL_SIZE}), nhận: {kernel_size}. "
            "Kernel lớn không hiệu quả và làm mất chi tiết đối tượng."
        )

    return kernel_size


def _validate_binary_mask(mask_raw):
    """
    Kiểm tra mask đầu vào theo quy ước mask của nhóm.

    Args:
        mask_raw: Mask 2 chiều, 1 kênh, dtype uint8, chỉ chứa 0 và 255.

    Returns:
        np.ndarray: Mask đã được kiểm tra (không sao chép nếu không cần).

    Raises:
        ValueError: Nếu mask là None, rỗng, không phải 2 chiều, hoặc chứa
            giá trị ngoài {0, 255}.
        TypeError: Nếu mask không phải ``np.ndarray`` hoặc sai dtype.
    """
    if mask_raw is None:
        raise ValueError(
            "mask_raw không được phép là None. "
            "Hãy truyền một mask numpy 2 chiều dtype uint8 (giá trị 0/255)."
        )

    if not isinstance(mask_raw, np.ndarray):
        raise TypeError(
            f"mask_raw phải là numpy.ndarray, nhận: {type(mask_raw).__name__}."
        )

    if mask_raw.size == 0:
        raise ValueError("mask_raw không được phép rỗng (size == 0).")

    if mask_raw.ndim != 2:
        raise ValueError(
            "mask_raw phải là mảng 2 chiều (ndim == 2, một kênh H x W), "
            f"nhận shape {mask_raw.shape} (ndim = {mask_raw.ndim}). "
            "Ảnh màu RGB/BGR phải được chuyển thành mask 1 kênh trước khi lọc."
        )

    if mask_raw.dtype != np.uint8:
        raise TypeError(
            f"mask_raw phải có dtype uint8, nhận: {mask_raw.dtype}."
        )

    unique_values = np.unique(mask_raw)
    if not set(unique_values.tolist()).issubset(set(BINARY_VALUES)):
        if set(unique_values.tolist()).issubset({0, 1}):
            raise ValueError(
                "mask_raw dùng quy ước 0/1, trong khi dự án yêu cầu 0/255. "
                "Hãy nhân mask với 255: (mask * 255).astype(np.uint8)."
            )
        raise ValueError(
            "mask_raw phải là mask nhị phân chỉ chứa giá trị 0 và 255, "
            f"nhận các giá trị: {unique_values.tolist()}."
        )

    return mask_raw


def apply_median_filter(mask_raw, kernel_size=3):
    """
    Áp dụng bộ lọc trung vị (Median Filter) lên mask nhị phân.

    Cửa sổ trượt kích thước ``kernel_size x kernel_size`` được áp dụng trên
    ảnh; với mỗi cửa sổ, ``kernel_size**2`` giá trị pixel được sắp xếp tăng
    dần và phần tử ở vị trí chính giữa (``kernel_size**2 // 2``) được chọn làm
    giá trị mới. Với mask 0/255, phép lọc này khử nhiễu xung (salt-and-pepper)
    mà không làm mờ biên đối tượng như lọc trung bình.

    Args:
        mask_raw: Mask nhị phân đầu vào, mảng NumPy 2 chiều (H, W),
            dtype ``uint8``, chỉ chứa giá trị 0 và 255.
        kernel_size: Kích thước kernel vuông, số lẻ, ``3 <= kernel_size <= 31``.
            Mặc định: 3 (3x3).

    Returns:
        np.ndarray: ``mask_median`` có cùng shape (H, W), dtype ``uint8``,
            chỉ chứa giá trị 0 và 255. Mảng đầu vào không bị thay đổi.

    Raises:
        ValueError: Nếu mask_raw là None, rỗng, không phải 2 chiều, chứa giá trị
            ngoài {0, 255}; hoặc kernel_size < 3, kernel_size chẵn, hoặc
            kernel_size vượt quá 31.
        TypeError: Nếu mask_raw không phải ``np.ndarray``, sai dtype
            (khác ``uint8``); hoặc kernel_size không phải số nguyên (bool bị loại).
        cv2.error: Nếu OpenCV không xử lý được kernel yêu cầu (hiếm gặp).

    Example:
        >>> import numpy as np
        >>> from src.median_filter import apply_median_filter
        >>> mask = np.zeros((5, 5), dtype=np.uint8)
        >>> mask[1:4, 1:4] = 255
        >>> mask[0, 0] = 255           # nhiễu muối tiêu đơn lẻ
        >>> out = apply_median_filter(mask, kernel_size=3)
        >>> out.shape, out.dtype
        ((5, 5), dtype('uint8'))
    """
    kernel_size = _validate_kernel_size(kernel_size)
    mask = _validate_binary_mask(mask_raw)

    # OpenCV yêu cầu mảng liên tục; dùng ascontiguousarray để tránh lỗi
    # với các view không liên tục. Không sửa nội dung mảng gốc.
    mask_contiguous = np.ascontiguousarray(mask)
    mask_median = cv2.medianBlur(mask_contiguous, kernel_size)

    # Bảo đảm đầu ra đúng quy ước: uint8, 2 chiều, chỉ 0/255.
    mask_median = np.asarray(mask_median, dtype=np.uint8)
    mask_median[mask_median > 0] = 255

    return mask_median


#: Alias thuận tiện cho ``apply_median_filter`` (import ngắn gọn hơn).
median_filter = apply_median_filter


def compare_kernels(mask_raw, kernel_sizes=(3, 5, 7), ground_truth=None):
    """
    Chạy bộ lọc trung vị với nhiều kích thước kernel và đo lại sự thay đổi.

    Args:
        mask_raw: Mask nhị phân đầu vào (H, W), uint8, giá trị 0/255.
        kernel_sizes: Danh sách kích thước kernel cần so sánh.
        ground_truth: Mask tham chiếu tuỳ chọn (H, W), uint8, giá trị 0/255.
            Nếu có, sẽ báo thêm IoU của từng kernel.

    Returns:
        dict: {
            'kernels': {kernel_size: mask_median},
            'metrics': {kernel_size: {...}},
        }
        Trong đó mỗi phần metrics chứa các khoá:
        'changed_pixels', 'changed_ratio', 'removed_pixels', 'added_pixels',
        'object_pixels', và nếu có ground_truth thì thêm 'iou',
        'false_positive_pixels', 'false_negative_pixels'.
    """
    mask = _validate_binary_mask(mask_raw)
    kernels, metrics = {}, {}

    for size in kernel_sizes:
        kernel_size = _validate_kernel_size(size)
        filtered = apply_median_filter(mask, kernel_size)
        kernels[kernel_size] = filtered

        changed = int(np.count_nonzero(filtered != mask))
        removed = int(np.count_nonzero((mask == 255) & (filtered == 0)))
        added = int(np.count_nonzero((mask == 0) & (filtered == 255)))

        entry = {
            'changed_pixels': changed,
            'changed_ratio': float(changed / mask.size) if mask.size else 0.0,
            'removed_pixels': removed,
            'added_pixels': added,
            'object_pixels': int(np.count_nonzero(filtered)),
        }

        if ground_truth is not None:
            gt = _validate_binary_mask(ground_truth)
            if gt.shape != filtered.shape:
                raise ValueError(
                    f"ground_truth phải cùng kích thước với mask, nhận: "
                    f"{gt.shape} vs {filtered.shape}"
                )
            inter = int(np.count_nonzero((filtered == 255) & (gt == 255)))
            union = int(np.count_nonzero((filtered == 255) | (gt == 255)))
            entry['iou'] = float(inter / union) if union else 0.0
            entry['false_positive_pixels'] = int(
                np.count_nonzero((filtered == 255) & (gt == 0))
            )
            entry['false_negative_pixels'] = int(
                np.count_nonzero((filtered == 0) & (gt == 255))
            )

        metrics[kernel_size] = entry

    return {'kernels': kernels, 'metrics': metrics}


class MedianFilter:
    """Lớp lọc trung vị để khử nhiễu Mask (API tương thích cho main.py)."""

    def __init__(self, kernel_size=DEFAULT_KERNEL_SIZE):
        """
        Khởi tạo MedianFilter

        Args:
            kernel_size: Kích thước kernel lẻ (3, 5, 7, 9, ...)
                        Mặc định: 5

        Raises:
            TypeError: Nếu kernel_size không phải số nguyên (bool bị loại).
            ValueError: Nếu kernel_size < 3, kernel_size chẵn hoặc vượt quá 31.
        """
        self.set_kernel_size(kernel_size)

    def set_kernel_size(self, kernel_size):
        """
        Đặt kích thước kernel

        Args:
            kernel_size: Kích thước kernel phải là số lẻ, 3 <= kernel_size <= 31

        Raises:
            TypeError: Nếu kernel_size không phải số nguyên.
            ValueError: Nếu kernel_size < 3, kernel_size chẵn hoặc quá lớn.
        """
        self.kernel_size = _validate_kernel_size(kernel_size)

    def filter(self, mask):
        """
        Áp dụng bộ lọc trung vị lên Mask

        Args:
            mask: Mask đầu vào (H, W), uint8, giá trị 0/255.
                 Với khả năng tương thích, mask có dạng (H, W, 1) sẽ được
                 nén về (H, W) trước khi lọc.

        Returns:
            mask_filtered: Mask sau lọc (H, W), uint8, giá trị 0/255

        Raises:
            ValueError: Nếu mask không hợp lệ.
            TypeError: Nếu mask sai dtype.
        """
        if isinstance(mask, np.ndarray) and mask.ndim == 3 and mask.shape[2] == 1:
            mask = mask[:, :, 0]

        return apply_median_filter(mask, self.kernel_size)

    def filter_with_comparison(self, mask):
        """
        Lọc mask và trả về cả ảnh gốc lẫn ảnh lọc để so sánh

        Args:
            mask: Mask đầu vào

        Returns:
            dict: {
                'original': Mask gốc,
                'filtered': Mask sau lọc,
                'diff': Sự khác biệt giữa hai ảnh,
                'kernel_size': Kích thước kernel được dùng,
                'changed_pixels': Số pixel bị thay đổi
            }
        """
        mask_original = mask
        if isinstance(mask_original, np.ndarray) and mask_original.ndim == 3 \
                and mask_original.shape[2] == 1:
            mask_original = mask_original[:, :, 0]

        mask_filtered = self.filter(mask_original)

        # Tính sự khác biệt
        diff = cv2.absdiff(mask_original, mask_filtered)

        return {
            'original': mask_original,
            'filtered': mask_filtered,
            'diff': diff,
            'kernel_size': self.kernel_size,
            'changed_pixels': int(np.sum(diff > 0)),
        }

    def get_kernel_size(self):
        """Trả về kích thước kernel hiện tại"""
        return self.kernel_size


def bilateral_filter(mask, kernel_size=5, sigma_color=75, sigma_space=75):
    """
    Áp dụng bộ lọc hai phía để giữ ranh giới sắc nét hơn

    Args:
        mask: Mask đầu vào
        kernel_size: Kích thước kernel
        sigma_color: Độ lệch chuẩn cho màu sắc
        sigma_space: Độ lệch chuẩn cho không gian

    Returns:
        mask_filtered: Mask sau lọc
    """
    if mask is None or mask.size == 0:
        raise ValueError("Mask đầu vào không hợp lệ")

    # Chuyển đổi nếu cần
    if len(mask.shape) == 3:
        mask = mask[:, :, 0]

    # Bilateral filter giữ ranh giới nhưng vẫn khử nhiễu
    mask_filtered = cv2.bilateralFilter(
        mask,
        kernel_size,
        sigma_color,
        sigma_space
    )

    return mask_filtered


def morphological_close(mask, kernel_size=5):
    """
    Thực hiện phép đóng (Closing) = Dilation + Erosion
    Giúp lấp kín các lỗ nhỏ bên trong đối tượng

    Args:
        mask: Mask đầu vào
        kernel_size: Kích thước kernel

    Returns:
        mask_closed: Mask sau phép đóng
    """
    if mask is None or mask.size == 0:
        raise ValueError("Mask đầu vào không hợp lệ")

    if len(mask.shape) == 3:
        mask = mask[:, :, 0]

    # Tạo kernel
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # Áp dụng Closing
    mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask_closed


def main():
    """Hàm demo nhanh module"""
    # Tạo mask test với nhiễu muối tiêu
    mask_test = np.zeros((100, 100), dtype=np.uint8)
    mask_test[20:80, 20:80] = 255
    mask_noisy = mask_test.copy()
    mask_noisy[10, 10] = 255          # nhiễu muối (điểm trắng lẻ)
    mask_noisy[50, 50] = 0            # nhiễu tiêu (điểm đen lẻ)

    print("=== TEST MEDIAN FILTER ===")

    # Cách dùng chuẩn (hàm)
    for kernel_size in (3, 5, 7):
        result = apply_median_filter(mask_noisy, kernel_size)
        changed = int(np.count_nonzero(result != mask_noisy))
        print(f"Kernel {kernel_size}x{kernel_size}: shape={result.shape}, "
              f"dtype={result.dtype}, giá trị={np.unique(result)}, "
              f"pixel thay đổi={changed}")

    # Cách dùng tương thích (lớp)
    median = MedianFilter(kernel_size=5)
    comparison = median.filter_with_comparison(mask_noisy)
    print(f"Lớp MedianFilter: kernel={comparison['kernel_size']}, "
          f"pixel thay đổi={comparison['changed_pixels']}")

    # So sánh nhiều kernel
    summary = compare_kernels(mask_noisy, (3, 5, 7))
    for kernel_size, metrics in summary['metrics'].items():
        print(f"Kernel {kernel_size}: thay đổi {metrics['changed_pixels']} pixel "
              f"({metrics['changed_ratio']:.2%})")

    # Test bilateral filter
    mask_bilateral = bilateral_filter(mask_noisy)
    print(f"Bilateral filter output shape: {mask_bilateral.shape}")

    # Test morphological close
    mask_closed = morphological_close(mask_noisy)
    print(f"Morphological close output shape: {mask_closed.shape}")


if __name__ == "__main__":
    main()
