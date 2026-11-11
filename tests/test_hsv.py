# -*- coding: utf-8 -*-
"""
Test Module: test_hsv.py
Kiểm thử module hsv_segment
"""

import unittest
import numpy as np
import cv2
from src.hsv_segment import HSVSegmenter


class TestHSVSegmenter(unittest.TestCase):
    """Kiểm thử lớp HSVSegmenter"""
    
    def setUp(self):
        """Chuẩn bị test"""
        # Tạo ảnh test có hình vuông đỏ
        self.test_image = np.zeros((200, 200, 3), dtype=np.uint8)
        self.test_image[50:150, 50:150] = [0, 0, 255]  # BGR: đỏ
        
        # Cấu hình HSV cho màu đỏ
        self.red_config = {
            'color_name': 'Red',
            'hue_ranges': [[0, 10], [170, 180]],
            'saturation': [100, 255],
            'value': [100, 255],
        }
    
    def test_bgr_to_hsv(self):
        """Test chuyển BGR sang HSV"""
        segmenter = HSVSegmenter(self.red_config)
        hsv_image = segmenter.bgr_to_hsv(self.test_image)
        
        self.assertEqual(hsv_image.shape, self.test_image.shape)
        self.assertEqual(hsv_image.dtype, np.uint8)
    
    def test_create_mask(self):
        """Test tạo Mask"""
        segmenter = HSVSegmenter(self.red_config)
        hsv_image = segmenter.bgr_to_hsv(self.test_image)
        mask = segmenter.create_mask(hsv_image)
        
        self.assertEqual(mask.shape, (200, 200))
        self.assertEqual(mask.dtype, np.uint8)
        # Kiểm tra mask chỉ chứa 0/255
        unique_values = np.unique(mask)
        self.assertTrue(all(v in [0, 255] for v in unique_values))
    
    def test_segment(self):
        """Test phân đoạn đầy đủ"""
        segmenter = HSVSegmenter(self.red_config)
        mask, hsv_image = segmenter.segment(self.test_image)
        
        self.assertEqual(mask.shape, (200, 200))
        self.assertEqual(hsv_image.shape, (200, 200, 3))
        
        # Kiểm tra có pixel trắng trong mask (do máy của đỏ)
        white_pixels = np.sum(mask > 0)
        self.assertGreater(white_pixels, 0)
    
    def test_update_config(self):
        """Test cập nhật cấu hình"""
        segmenter = HSVSegmenter(self.red_config)
        
        new_config = {
            'saturation': [50, 200],
            'value': [50, 200],
        }
        segmenter.update_config(**new_config)
        
        config = segmenter.get_config()
        self.assertEqual(config['saturation'], [50, 200])
        self.assertEqual(config['value'], [50, 200])
    
    def test_invalid_hue_range(self):
        """Test xử lý khoảng Hue không hợp lệ"""
        invalid_config = {
            'color_name': 'Invalid',
            'hue_ranges': [[0, 200]],  # > 180
            'saturation': [100, 255],
            'value': [100, 255],
        }
        
        with self.assertRaises(ValueError):
            HSVSegmenter(invalid_config)
    
    def test_hsv_info(self):
        """Test lấy thông tin HSV"""
        segmenter = HSVSegmenter(self.red_config)
        hsv_image = segmenter.bgr_to_hsv(self.test_image)
        mask = segmenter.create_mask(hsv_image)
        
        info = HSVSegmenter.get_hsv_info(hsv_image, mask)
        
        self.assertIn('h_min', info)
        self.assertIn('h_max', info)
        self.assertIn('s_min', info)
        self.assertIn('pixel_count', info)


if __name__ == '__main__':
    unittest.main()
