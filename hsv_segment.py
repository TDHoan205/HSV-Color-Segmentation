# -*- coding: utf-8 -*-
"""
Module: hsv_segment.py
Chức năng: Chuyển đổi HSV và phân đoạn màu
Phụ trách: Mạnh Quân

Input: image_bgr + cấu hình khoảng HSV
Output: mask_raw

Quy ước:
- Mask 1 kênh, uint8 0/255, cùng H×W
- Thang H/S/V của OpenCV:
  * H: 0-180 (nửa của 360 độ để vừa với uint8)
  * S: 0-255
  * V: 0-255
- Xử lý hai khoảng Hue cho màu đỏ nếu cần
"""

import cv2
import numpy as np


class HSVSegmenter:
    """Lớp phân đoạn ảnh dựa trên không gian màu HSV"""
    
    # Cấu hình màu mục tiêu mặc định (đỏ)
    DEFAULT_CONFIG = {
        'color_name': 'Red',
        'hue_ranges': [[0, 10], [170, 180]],  # Đỏ có hai khoảng
        'saturation': [100, 255],
        'value': [100, 255],
    }
    
    def __init__(self, config=None):
        """
        Khởi tạo HSV Segmenter
        
        Args:
            config: Dict chứa cấu hình ngưỡng HSV
                   Cấu trúc: {
                       'color_name': str,
                       'hue_ranges': list của [min, max],
                       'saturation': [min, max],
                       'value': [min, max]
                   }
        """
        self.config = config if config is not None else self.DEFAULT_CONFIG.copy()
        self._validate_config()
    
    def _validate_config(self):
        """Kiểm tra tính hợp lệ của cấu hình"""
        if 'hue_ranges' not in self.config:
            raise ValueError("Cấu hình phải có 'hue_ranges'")
        if 'saturation' not in self.config or 'value' not in self.config:
            raise ValueError("Cấu hình phải có 'saturation' và 'value'")
        
        # Kiểm tra khoảng Hue
        for h_range in self.config['hue_ranges']:
            if not (0 <= h_range[0] <= 180 and 0 <= h_range[1] <= 180):
                raise ValueError(f"Hue phải trong [0, 180], nhận: {h_range}")
        
        # Kiểm tra khoảng S và V
        s_range = self.config['saturation']
        v_range = self.config['value']
        if not (0 <= s_range[0] <= 255 and 0 <= s_range[1] <= 255):
            raise ValueError(f"Saturation phải trong [0, 255], nhận: {s_range}")
        if not (0 <= v_range[0] <= 255 and 0 <= v_range[1] <= 255):
            raise ValueError(f"Value phải trong [0, 255], nhận: {v_range}")
    
    def bgr_to_hsv(self, image_bgr):
        """
        Chuyển ảnh từ BGR sang HSV
        
        Args:
            image_bgr: Ảnh BGR (H, W, 3), uint8
            
        Returns:
            image_hsv: Ảnh HSV (H, W, 3), uint8
                       H: 0-180, S: 0-255, V: 0-255
        """
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Ảnh đầu vào không hợp lệ")
        
        if len(image_bgr.shape) != 3 or image_bgr.shape[2] != 3:
            raise ValueError(f"Ảnh phải có 3 kênh, nhận: {image_bgr.shape}")
        
        image_hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        return image_hsv
    
    def create_mask(self, image_hsv):
        """
        Tạo Mask nhị phân từ ảnh HSV dựa trên cấu hình
        
        Args:
            image_hsv: Ảnh HSV (H, W, 3)
            
        Returns:
            mask_raw: Mask nhị phân (H, W), uint8, giá trị 0/255
        """
        if image_hsv is None or image_hsv.size == 0:
            raise ValueError("Ảnh HSV đầu vào không hợp lệ")
        
        h, s, v = cv2.split(image_hsv)
        
        # Định nghĩa khoảng S và V
        s_min, s_max = self.config['saturation']
        v_min, v_max = self.config['value']
        
        s_mask = cv2.inRange(s, s_min, s_max)
        v_mask = cv2.inRange(v, v_min, v_max)
        
        # Xử lý Hue ranges (có thể có nhiều khoảng)
        h_mask = np.zeros_like(h, dtype=np.uint8)
        
        for h_range in self.config['hue_ranges']:
            h_min, h_max = h_range
            h_range_mask = cv2.inRange(h, h_min, h_max)
            h_mask = cv2.bitwise_or(h_mask, h_range_mask)
        
        # Kết hợp tất cả các mask
        mask_raw = cv2.bitwise_and(h_mask, cv2.bitwise_and(s_mask, v_mask))
        
        return mask_raw
    
    def segment(self, image_bgr):
        """
        Phân đoạn ảnh: chuyển BGR → HSV → tạo Mask
        
        Args:
            image_bgr: Ảnh BGR
            
        Returns:
            mask_raw: Mask nhị phân
            image_hsv: Ảnh HSV (cho mục đích debug/hiển thị)
        """
        image_hsv = self.bgr_to_hsv(image_bgr)
        mask_raw = self.create_mask(image_hsv)
        return mask_raw, image_hsv
    
    def update_config(self, **kwargs):
        """
        Cập nhật cấu hình ngưỡng
        
        Args:
            **kwargs: Các tham số cần cập nhật
                     (color_name, hue_ranges, saturation, value)
        """
        for key in kwargs:
            if key in self.config:
                self.config[key] = kwargs[key]
        
        self._validate_config()
    
    def get_config(self):
        """Trả về cấu hình hiện tại"""
        return self.config.copy()
    
    @staticmethod
    def get_hsv_info(image_hsv, mask=None):
        """
        Lấy thông tin thống kê HSV từ ảnh
        
        Args:
            image_hsv: Ảnh HSV
            mask: Mask tùy chọn để lấy thống kê chỉ từ vùng quan tâm
            
        Returns:
            dict: Thông tin thống kê H/S/V
        """
        h, s, v = cv2.split(image_hsv)
        
        if mask is not None:
            h_masked = h[mask > 0]
            s_masked = s[mask > 0]
            v_masked = v[mask > 0]
        else:
            h_masked = h.flatten()
            s_masked = s.flatten()
            v_masked = v.flatten()
        
        info = {
            'h_min': int(np.min(h_masked)) if h_masked.size > 0 else 0,
            'h_max': int(np.max(h_masked)) if h_masked.size > 0 else 0,
            'h_mean': float(np.mean(h_masked)) if h_masked.size > 0 else 0,
            's_min': int(np.min(s_masked)) if s_masked.size > 0 else 0,
            's_max': int(np.max(s_masked)) if s_masked.size > 0 else 0,
            's_mean': float(np.mean(s_masked)) if s_masked.size > 0 else 0,
            'v_min': int(np.min(v_masked)) if v_masked.size > 0 else 0,
            'v_max': int(np.max(v_masked)) if v_masked.size > 0 else 0,
            'v_mean': float(np.mean(v_masked)) if v_masked.size > 0 else 0,
            'pixel_count': int(np.sum(mask > 0)) if mask is not None else image_hsv.shape[0] * image_hsv.shape[1]
        }
        
        return info


def main():
    """Hàm test module"""
    # Tạo ảnh test
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    # Vẽ một hình vuông màu đỏ
    test_image[20:80, 20:80] = [0, 0, 255]  # BGR: đỏ
    
    # Tạo segmenter
    segmenter = HSVSegmenter()
    
    # Phân đoạn
    mask, hsv_image = segmenter.segment(test_image)
    
    print("=== TEST HSV SEGMENTATION ===")
    print(f"Ảnh BGR shape: {test_image.shape}")
    print(f"Ảnh HSV shape: {hsv_image.shape}")
    print(f"Mask shape: {mask.shape}")
    print(f"Mask dtype: {mask.dtype}")
    print(f"Pixel trắng trong Mask: {np.sum(mask > 0)}")
    print(f"Cấu hình: {segmenter.get_config()}")


if __name__ == "__main__":
    main()
