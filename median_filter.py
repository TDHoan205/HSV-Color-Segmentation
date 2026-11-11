# -*- coding: utf-8 -*-
"""
Module: median_filter.py
Chức năng: Lọc trung vị để khử nhiễu Mask
Phụ trách: Anh Tuấn

Input: mask_raw + kernel lẻ
Output: mask_median

Quy ước:
- Không đổi kích thước ảnh
- Kernel phải là số lẻ: 3, 5, 7, ...
- Đầu ra vẫn là Mask nhị phân (0/255)
"""

import cv2
import numpy as np


class MedianFilter:
    """Lớp lọc trung vị để khử nhiễu Mask"""
    
    def __init__(self, kernel_size=5):
        """
        Khởi tạo MedianFilter
        
        Args:
            kernel_size: Kích thước kernel lẻ (3, 5, 7, 9, ...)
                        Mặc định: 5
                        
        Raises:
            ValueError: Nếu kernel_size không phải số lẻ
        """
        self.set_kernel_size(kernel_size)
    
    def set_kernel_size(self, kernel_size):
        """
        Đặt kích thước kernel
        
        Args:
            kernel_size: Kích thước kernel phải là số lẻ
            
        Raises:
            ValueError: Nếu kernel_size không hợp lệ
        """
        if kernel_size <= 0:
            raise ValueError("Kernel size phải > 0")
        
        if kernel_size % 2 == 0:
            raise ValueError(f"Kernel size phải là số lẻ, nhận: {kernel_size}")
        
        if kernel_size > 31:
            raise ValueError(f"Kernel size quá lớn (max 31), nhận: {kernel_size}")
        
        self.kernel_size = kernel_size
    
    def filter(self, mask):
        """
        Áp dụng bộ lọc trung vị lên Mask
        
        Args:
            mask: Ảnh/Mask đầu vào (H, W) hoặc (H, W, 1), uint8
            
        Returns:
            mask_filtered: Ảnh sau lọc (H, W), uint8
            
        Raises:
            ValueError: Nếu mask không hợp lệ
        """
        if mask is None or mask.size == 0:
            raise ValueError("Mask đầu vào không hợp lệ")
        
        # Chuyển đổi nếu mask có 3 kênh
        if len(mask.shape) == 3:
            if mask.shape[2] != 1:
                raise ValueError(f"Mask phải có 1 hoặc không kênh, nhận: {mask.shape}")
            mask = mask[:, :, 0]
        
        # Áp dụng bộ lọc trung vị
        mask_filtered = cv2.medianBlur(mask, self.kernel_size)
        
        return mask_filtered
    
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
                'kernel_size': Kích thước kernel được dùng
            }
        """
        mask_filtered = self.filter(mask)
        
        # Tính sự khác biệt
        diff = cv2.absdiff(mask, mask_filtered)
        
        return {
            'original': mask,
            'filtered': mask_filtered,
            'diff': diff,
            'kernel_size': self.kernel_size,
            'changed_pixels': int(np.sum(diff > 0))
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
    """Hàm test module"""
    # Tạo mask test với nhiễu
    mask_test = np.zeros((100, 100), dtype=np.uint8)
    # Vẽ hình vuông
    mask_test[20:80, 20:80] = 255
    # Thêm nhiễu ngẫu nhiên
    noise = np.random.randint(0, 2, (100, 100)) * 255
    mask_with_noise = cv2.bitwise_or(mask_test, noise.astype(np.uint8))
    
    # Tạo filter
    median_filter = MedianFilter(kernel_size=5)
    
    # Áp dụng lọc
    result = median_filter.filter_with_comparison(mask_with_noise)
    
    print("=== TEST MEDIAN FILTER ===")
    print(f"Kernel size: {result['kernel_size']}")
    print(f"Pixel thay đổi: {result['changed_pixels']}")
    print(f"Original shape: {result['original'].shape}")
    print(f"Filtered shape: {result['filtered'].shape}")
    
    # Test bilateral filter
    mask_bilateral = bilateral_filter(mask_with_noise)
    print(f"Bilateral filter output shape: {mask_bilateral.shape}")
    
    # Test morphological close
    mask_closed = morphological_close(mask_with_noise)
    print(f"Morphological close output shape: {mask_closed.shape}")


if __name__ == "__main__":
    main()
