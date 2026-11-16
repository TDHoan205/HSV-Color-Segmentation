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
  * H: 0-179 (nửa của 360 độ; upper bound 180 được chấp nhận)
  * S: 0-255
  * V: 0-255
- Xử lý hai khoảng Hue cho màu đỏ nếu cần
"""

import cv2
import numpy as np


# Nguồn preset duy nhất cho 15 nhóm màu (Phase A).
# Hue theo thang OpenCV 0-179. Các ngưỡng là GIÁ TRỊ KHỞI ĐIỂM,
# chưa kiểm chứng trên ảnh thực tế nên verified = False.
# Màu trắng/đen/xám không dùng Hue: hue_ranges = [0, 179] (không lọc Hue).
COLOR_PRESETS = {
    'red':           {'name': 'Đỏ',           'hex': '#FF0000', 'mode': 'hue', 'hue_ranges': [[0, 10], [170, 179]], 'saturation': [100, 255], 'value': [100, 255]},
    'red_orange':    {'name': 'Đỏ cam',        'hex': '#FF4500', 'mode': 'hue', 'hue_ranges': [[9, 16]],          'saturation': [60, 255], 'value': [60, 255]},
    'orange':        {'name': 'Cam',           'hex': '#FF8000', 'mode': 'hue', 'hue_ranges': [[17, 22]],        'saturation': [60, 255], 'value': [60, 255]},
    'yellow_orange': {'name': 'Vàng cam',      'hex': '#FFB000', 'mode': 'hue', 'hue_ranges': [[23, 27]],        'saturation': [60, 255], 'value': [60, 255]},
    'yellow':        {'name': 'Vàng',          'hex': '#FFFF00', 'mode': 'hue', 'hue_ranges': [[28, 35]],        'saturation': [60, 255], 'value': [60, 255]},
    'yellow_green':  {'name': 'Vàng lục',      'hex': '#9ACD32', 'mode': 'hue', 'hue_ranges': [[36, 44]],        'saturation': [60, 255], 'value': [60, 255]},
    'green':         {'name': 'Lục',           'hex': '#00A000', 'mode': 'hue', 'hue_ranges': [[45, 85]],        'saturation': [60, 255], 'value': [60, 255]},
    'blue_green':    {'name': 'Lục lam',       'hex': '#00A0A0', 'mode': 'hue', 'hue_ranges': [[86, 100]],       'saturation': [60, 255], 'value': [60, 255]},
    'blue':          {'name': 'Lam',           'hex': '#0000FF', 'mode': 'hue', 'hue_ranges': [[101, 125]],      'saturation': [60, 255], 'value': [60, 255]},
    'blue_purple':   {'name': 'Lam tím',       'hex': '#6A00FF', 'mode': 'hue', 'hue_ranges': [[126, 140]],      'saturation': [60, 255], 'value': [60, 255]},
    'purple':        {'name': 'Tím',           'hex': '#800080', 'mode': 'hue', 'hue_ranges': [[141, 155]],      'saturation': [60, 255], 'value': [60, 255]},
    'red_purple':    {'name': 'Đỏ tím',        'hex': '#C00080', 'mode': 'hue', 'hue_ranges': [[156, 169]],      'saturation': [60, 255], 'value': [60, 255]},
    'white':         {'name': 'Trắng',         'hex': '#FFFFFF', 'mode': 'sv',  'hue_ranges': [[0, 179]],        'saturation': [0, 40],   'value': [200, 255]},
    'black':         {'name': 'Đen',           'hex': '#000000', 'mode': 'sv',  'hue_ranges': [[0, 179]],        'saturation': [0, 255],  'value': [0, 50]},
    'gray':          {'name': 'Xám',           'hex': '#808080', 'mode': 'sv',  'hue_ranges': [[0, 179]],        'saturation': [0, 40],   'value': [60, 199]},
}

COLOR_IDS = tuple(COLOR_PRESETS)


def get_color_preset(color_id):
    """Trả về bản sao preset của màu; ném ValueError nếu color_id không tồn tại"""
    if not isinstance(color_id, str) or color_id not in COLOR_PRESETS:
        raise ValueError(f"Màu không tồn tại: {color_id}")
    preset = COLOR_PRESETS[color_id]
    return {
        'color_id': color_id,
        'name': preset['name'],
        'hex': preset['hex'],
        'mode': preset['mode'],
        'hue_ranges': [list(r) for r in preset['hue_ranges']],
        'saturation': list(preset['saturation']),
        'value': list(preset['value']),
        'verified': False,
    }


def build_hsv_config(color_id):
    """Tạo config tương thích HSVSegmenter từ preset của màu"""
    preset = get_color_preset(color_id)
    return {
        'color_name': preset['name'],
        'hue_ranges': preset['hue_ranges'],
        'saturation': preset['saturation'],
        'value': preset['value'],
    }


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
        self.config = config.copy() if config is not None else self.DEFAULT_CONFIG.copy()
        self._validate_config()
    
    def _validate_config(self):
        """Kiểm tra tính hợp lệ của cấu hình"""
        if 'hue_ranges' not in self.config:
            raise ValueError("Cấu hình phải có 'hue_ranges'")
        if 'saturation' not in self.config or 'value' not in self.config:
            raise ValueError("Cấu hình phải có 'saturation' và 'value'")
        
        hue_ranges = self.config['hue_ranges']
        if not isinstance(hue_ranges, (list, tuple)) or not hue_ranges:
            raise ValueError("'hue_ranges' phải là danh sách không rỗng các khoảng [min, max]")

        # OpenCV uint8 H values are 0-179; 180 is accepted as an inclusive upper bound.
        for h_range in hue_ranges:
            self._validate_range(h_range, 'Hue', 180)

        self._validate_range(self.config['saturation'], 'Saturation', 255)
        self._validate_range(self.config['value'], 'Value', 255)

    @staticmethod
    def _validate_range(value_range, name, maximum):
        if (not isinstance(value_range, (list, tuple)) or len(value_range) != 2
                or not all(isinstance(value, (int, np.integer)) for value in value_range)
                or not 0 <= value_range[0] <= value_range[1] <= maximum):
            raise ValueError(f"{name} cần khoảng [min, max] trong [0, {maximum}], nhận: {value_range}")
    
    def bgr_to_hsv(self, image_bgr):
        """
        Chuyển ảnh từ BGR sang HSV
        
        Args:
            image_bgr: Ảnh BGR (H, W, 3), uint8
            
        Returns:
            image_hsv: Ảnh HSV (H, W, 3), uint8
                       H: 0-179, S: 0-255, V: 0-255
        """
        if not isinstance(image_bgr, np.ndarray) or image_bgr.size == 0:
            raise ValueError("Ảnh đầu vào không hợp lệ")
        
        if len(image_bgr.shape) != 3 or image_bgr.shape[2] != 3:
            raise ValueError(f"Ảnh phải có 3 kênh, nhận: {image_bgr.shape}")

        if image_bgr.dtype != np.uint8:
            raise ValueError(f"Ảnh BGR phải có dtype uint8, nhận: {image_bgr.dtype}")
        
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
        if not isinstance(image_hsv, np.ndarray) or image_hsv.size == 0:
            raise ValueError("Ảnh HSV đầu vào không hợp lệ")

        if image_hsv.ndim != 3 or image_hsv.shape[2] != 3 or image_hsv.dtype != np.uint8:
            raise ValueError("Ảnh HSV phải có shape (H, W, 3) và dtype uint8")
        
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
        updated = self.config.copy()
        updated.update({key: value for key, value in kwargs.items() if key in updated})
        previous = self.config
        self.config = updated
        try:
            self._validate_config()
        except ValueError:
            self.config = previous
            raise
    
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
