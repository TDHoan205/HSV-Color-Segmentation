# -*- coding: utf-8 -*-
"""
Test Module: test_data.py
Kiểm thử module data_loader
"""

import unittest
import numpy as np
import cv2
import os
import tempfile
import shutil
from data_loader import DataLoader


class TestDataLoader(unittest.TestCase):
    """Kiểm thử lớp DataLoader"""
    
    def setUp(self):
        """Chuẩn bị test"""
        self.temp_dir = tempfile.mkdtemp()
        self.images_dir = os.path.join(self.temp_dir, 'images')
        self.gt_dir = os.path.join(self.temp_dir, 'ground_truth')
        os.makedirs(self.images_dir)
        os.makedirs(self.gt_dir)
        
        # Tạo ảnh test
        self.test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.test_image[20:80, 20:80] = [0, 0, 255]  # Hình vuông đỏ
        
        # Tạo GT mask test
        self.test_gt = np.zeros((100, 100), dtype=np.uint8)
        self.test_gt[20:80, 20:80] = 255
        
        # Lưu
        cv2.imwrite(os.path.join(self.images_dir, 'test.png'), self.test_image)
        cv2.imwrite(os.path.join(self.gt_dir, 'test.png'), self.test_gt)
    
    def tearDown(self):
        """Dọn dẹp sau test"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_image(self):
        """Test đọc ảnh"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        image = loader.load_image(os.path.join(self.images_dir, 'test.png'))
        
        self.assertEqual(image.shape, (100, 100, 3))
        self.assertEqual(image.dtype, np.uint8)
    
    def test_load_ground_truth(self):
        """Test đọc Ground Truth"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        gt = loader.load_ground_truth(os.path.join(self.gt_dir, 'test.png'))
        
        self.assertEqual(gt.shape, (100, 100))
        self.assertEqual(gt.dtype, np.uint8)
    
    def test_load_image_gt_pair(self):
        """Test đọc cặp ảnh + GT"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        img, gt = loader.load_image_gt_pair(
            os.path.join(self.images_dir, 'test.png'),
            os.path.join(self.gt_dir, 'test.png')
        )
        
        self.assertEqual(img.shape[:2], gt.shape)
        self.assertEqual(img.shape[2], 3)
    
    def test_missing_file(self):
        """Test xử lý file không tồn tại"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        
        with self.assertRaises(FileNotFoundError):
            loader.load_image('nonexistent.png')
    
    def test_data_integrity(self):
        """Test kiểm tra tính toàn vẹn dữ liệu"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        report = loader.check_data_integrity()
        
        self.assertEqual(report['total_images'], 1)
        self.assertEqual(report['valid_pairs'], 1)
        self.assertEqual(len(report['missing_gt']), 0)


if __name__ == '__main__':
    unittest.main()
