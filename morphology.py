# -*- coding: utf-8 -*-
"""
Module: morphology.py
Chức năng: Các phép toán hình thái học để làm sạch Mask
Phụ trách: Quốc Anh

Input: Mask + operation + kernel
Output: mask_morph

Quy ước:
- Hỗ trợ: Opening, Closing, Erosion, Dilation
- Ghi rõ kernel sử dụng
- Đầu ra cùng H×W, uint8 0/255
"""

import cv2
import numpy as np


class MorphologyOperator:
    """Lớp thực hiện các phép toán hình thái học"""
    
    # Các phép toán được hỗ trợ
    OPERATIONS = {
        'erode': cv2.MORPH_ERODE,
        'dilate': cv2.MORPH_DILATE,
        'open': cv2.MORPH_OPEN,
        'close': cv2.MORPH_CLOSE,
        'gradient': cv2.MORPH_GRADIENT,
        'tophat': cv2.MORPH_TOPHAT,
        'blackhat': cv2.MORPH_BLACKHAT,
    }
    
    # Các hình kernel được hỗ trợ
    KERNEL_SHAPES = {
        'rect': cv2.MORPH_RECT,
        'ellipse': cv2.MORPH_ELLIPSE,
        'cross': cv2.MORPH_CROSS,
    }
    
    def __init__(self, kernel_size=5, kernel_shape='ellipse'):
        """
        Khởi tạo MorphologyOperator
        
        Args:
            kernel_size: Kích thước kernel (lẻ), mặc định 5
            kernel_shape: Hình dạng kernel ('rect', 'ellipse', 'cross')
        """
        self.set_kernel(kernel_size, kernel_shape)
    
    def set_kernel(self, kernel_size, kernel_shape='ellipse'):
        """
        Đặt kernel
        
        Args:
            kernel_size: Kích thước kernel phải là số lẻ
            kernel_shape: Hình dạng kernel
        """
        if kernel_size <= 0 or kernel_size % 2 == 0:
            raise ValueError(f"Kernel size phải là số lẻ dương, nhận: {kernel_size}")
        
        if kernel_shape not in self.KERNEL_SHAPES:
            raise ValueError(f"Kernel shape không được hỗ trợ: {kernel_shape}")
        
        self.kernel_size = kernel_size
        self.kernel_shape = kernel_shape
        
        # Tạo kernel
        shape_type = self.KERNEL_SHAPES[kernel_shape]
        self.kernel = cv2.getStructuringElement(
            shape_type,
            (kernel_size, kernel_size)
        )
    
    def erode(self, mask, iterations=1):
        """
        Erosion: Thu nhỏ vùng trắng
        
        Args:
            mask: Mask đầu vào
            iterations: Số lần lặp lại
            
        Returns:
            mask_eroded: Mask sau Erosion
        """
        if mask is None or mask.size == 0:
            raise ValueError("Mask không hợp lệ")
        
        mask_eroded = cv2.erode(mask, self.kernel, iterations=iterations)
        return mask_eroded
    
    def dilate(self, mask, iterations=1):
        """
        Dilation: Mở rộng vùng trắng
        
        Args:
            mask: Mask đầu vào
            iterations: Số lần lặp lại
            
        Returns:
            mask_dilated: Mask sau Dilation
        """
        if mask is None or mask.size == 0:
            raise ValueError("Mask không hợp lệ")
        
        mask_dilated = cv2.dilate(mask, self.kernel, iterations=iterations)
        return mask_dilated
    
    def open(self, mask, iterations=1):
        """
        Opening: Erosion + Dilation
        Loại bỏ vùng nhỏ, tách các đối tượng gắn nhau
        
        Args:
            mask: Mask đầu vào
            iterations: Số lần lặp lại
            
        Returns:
            mask_opened: Mask sau Opening
        """
        if mask is None or mask.size == 0:
            raise ValueError("Mask không hợp lệ")
        
        mask_opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel, iterations=iterations)
        return mask_opened
    
    def close(self, mask, iterations=1):
        """
        Closing: Dilation + Erosion
        Lấp kín các lỗ nhỏ bên trong, nối các đối tượng gần nhau
        
        Args:
            mask: Mask đầu vào
            iterations: Số lần lặp lại
            
        Returns:
            mask_closed: Mask sau Closing
        """
        if mask is None or mask.size == 0:
            raise ValueError("Mask không hợp lệ")
        
        mask_closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel, iterations=iterations)
        return mask_closed
    
    def apply_operation(self, mask, operation, iterations=1):
        """
        Áp dụng phép toán hình thái học
        
        Args:
            mask: Mask đầu vào
            operation: Tên phép toán ('erode', 'dilate', 'open', 'close', ...)
            iterations: Số lần lặp lại
            
        Returns:
            mask_result: Mask sau phép toán
        """
        if operation not in self.OPERATIONS:
            raise ValueError(f"Phép toán không được hỗ trợ: {operation}")
        
        if mask is None or mask.size == 0:
            raise ValueError("Mask không hợp lệ")
        
        op_code = self.OPERATIONS[operation]
        mask_result = cv2.morphologyEx(mask, op_code, self.kernel, iterations=iterations)
        
        return mask_result
    
    def apply_sequence(self, mask, operations):
        """
        Áp dụng một chuỗi phép toán
        
        Args:
            mask: Mask đầu vào
            operations: Danh sách các phép toán
                       Ví dụ: [
                           ('close', {'iterations': 1}),
                           ('open', {'iterations': 1}),
                       ]
            
        Returns:
            mask_result: Mask sau tất cả phép toán
        """
        mask_result = mask.copy()
        
        for op_name, op_kwargs in operations:
            if op_name not in self.OPERATIONS:
                raise ValueError(f"Phép toán không được hỗ trợ: {op_name}")
            
            mask_result = self.apply_operation(mask_result, op_name, **op_kwargs)
        
        return mask_result
    
    def get_kernel_info(self):
        """Trả về thông tin kernel hiện tại"""
        return {
            'size': self.kernel_size,
            'shape': self.kernel_shape,
            'kernel': self.kernel.copy(),
        }
    
    def set_iterations_adaptive(self, mask_size, target_reduction=0.2):
        """
        Tính số lần lặp tự động dựa trên kích thước mask
        
        Args:
            mask_size: Kích thước mask (H, W)
            target_reduction: Tỷ lệ giảm mục tiêu
            
        Returns:
            iterations: Số lần lặp đề xuất
        """
        # Công thức đơn giản: dựa trên kích thước kernel và mask
        h, w = mask_size
        small_dim = min(h, w)
        iterations = max(1, int(np.log(small_dim / self.kernel_size) + 1))
        return iterations


def compare_morphology_operations(mask, kernel_size=5):
    """
    So sánh các phép toán hình thái học trên cùng một mask
    
    Args:
        mask: Mask đầu vào
        kernel_size: Kích thước kernel
        
    Returns:
        dict: Các kết quả từ các phép toán khác nhau
    """
    operator = MorphologyOperator(kernel_size, 'ellipse')
    
    results = {
        'original': mask.copy(),
        'erode': operator.erode(mask),
        'dilate': operator.dilate(mask),
        'open': operator.open(mask),
        'close': operator.close(mask),
    }
    
    return results


def main():
    """Hàm test module"""
    # Tạo mask test
    mask_test = np.zeros((100, 100), dtype=np.uint8)
    # Vẽ hình vuông
    mask_test[20:80, 20:80] = 255
    # Thêm một vài điểm nhiễu
    mask_test[30:35, 30:35] = 0
    mask_test[70:75, 70:75] = 0
    
    # Tạo operator
    operator = MorphologyOperator(kernel_size=5, kernel_shape='ellipse')
    
    # Thử các phép toán
    print("=== TEST MORPHOLOGY OPERATIONS ===")
    print(f"Original image shape: {mask_test.shape}")
    print(f"Original white pixels: {np.sum(mask_test > 0)}")
    
    # Erosion
    mask_erode = operator.erode(mask_test)
    print(f"\nErosion white pixels: {np.sum(mask_erode > 0)}")
    
    # Dilation
    mask_dilate = operator.dilate(mask_test)
    print(f"Dilation white pixels: {np.sum(mask_dilate > 0)}")
    
    # Opening
    mask_open = operator.open(mask_test)
    print(f"Opening white pixels: {np.sum(mask_open > 0)}")
    
    # Closing
    mask_close = operator.close(mask_test)
    print(f"Closing white pixels: {np.sum(mask_close > 0)}")
    
    # Kernel info
    kernel_info = operator.get_kernel_info()
    print(f"\nKernel shape: {kernel_info['shape']}")
    print(f"Kernel size: {kernel_info['size']}")


if __name__ == "__main__":
    main()
