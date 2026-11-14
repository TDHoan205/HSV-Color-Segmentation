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
from src.data_loader import DataLoader

# Thư mục gốc của dự án (để trỏ tới bộ dữ liệu thật)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_IMAGES_DIR = os.path.join(PROJECT_ROOT, 'data', 'images')
REAL_GT_DIR = os.path.join(PROJECT_ROOT, 'data', 'ground_truth')
REAL_METADATA = os.path.join(PROJECT_ROOT, 'data', 'metadata.csv')


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
    
    def test_build_dataset(self):
        """Test dựng danh sách cặp (ảnh, GT)"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        pairs = loader.build_dataset()
        
        self.assertEqual(len(pairs), 1)
        self.assertTrue(pairs[0][0].endswith('test.png'))
        self.assertTrue(pairs[0][1].endswith('test.png'))
    
    def test_get_gt_path(self):
        """Test suy ra đường dẫn GT từ đường dẫn ảnh"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        gt_path = loader.get_gt_path(os.path.join(self.images_dir, 'test.png'))
        
        self.assertEqual(os.path.basename(gt_path), 'test.png')
        self.assertIn(self.gt_dir, gt_path)
    
    def test_extract_image_id(self):
        """Test trích xuất mã ảnh từ tên file"""
        self.assertEqual(
            DataLoader.extract_image_id('img_01_red_circle.jpg'), 'img_01'
        )
        self.assertEqual(DataLoader.extract_image_id('test.png'), 'test')
    
    def test_validate_pair_detects_size_mismatch(self):
        """Test phát hiện lệch kích thước giữa ảnh và GT"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        
        # Tạo GT lệch kích thước
        bad_gt_path = os.path.join(self.gt_dir, 'bad.png')
        cv2.imwrite(bad_gt_path, np.zeros((50, 50), dtype=np.uint8))
        
        result = loader.validate_pair(
            os.path.join(self.images_dir, 'test.png'), bad_gt_path
        )
        
        self.assertFalse(result['ok'])
        self.assertTrue(any('Kích thước không khớp' in i for i in result['issues']))
    
    def test_validate_pair_detects_non_binary_gt(self):
        """Test phát hiện GT không nhị phân 0/255"""
        loader = DataLoader(self.images_dir, self.gt_dir)
        
        bad_gt_path = os.path.join(self.gt_dir, 'gray.png')
        cv2.imwrite(bad_gt_path, np.full((100, 100), 128, dtype=np.uint8))
        
        result = loader.validate_pair(
            os.path.join(self.images_dir, 'test.png'), bad_gt_path
        )
        
        self.assertFalse(result['ok'])
        self.assertTrue(any('nhị phân' in i for i in result['issues']))
    
    def test_load_metadata(self):
        """Test đọc metadata.csv"""
        csv_path = os.path.join(self.temp_dir, 'metadata.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write('image_id,image_file,scenario\n')
            f.write('img_01,data/images/test.png,nen_sang\n')
        
        loader = DataLoader(self.images_dir, self.gt_dir, csv_path)
        rows = loader.load_metadata()
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['image_id'], 'img_01')
        self.assertEqual(rows[0]['scenario'], 'nen_sang')
        
        # Tra cứu theo mã
        self.assertEqual(loader.get_metadata_by_id('img_01')['scenario'], 'nen_sang')
        self.assertIsNone(loader.get_metadata_by_id('img_99'))
    
    def test_load_metadata_missing_file(self):
        """Test đọc metadata khi file không tồn tại -> trả về danh sách rỗng"""
        loader = DataLoader(self.images_dir, self.gt_dir,
                            os.path.join(self.temp_dir, 'khong_co.csv'))
        self.assertEqual(loader.load_metadata(), [])


@unittest.skipUnless(os.path.isdir(REAL_IMAGES_DIR) and os.listdir(REAL_IMAGES_DIR),
                     "Chưa có bộ dữ liệu thật trong data/images")
class TestRealDataset(unittest.TestCase):
    """Kiểm thử trên bộ dữ liệu thật do Anh Quân bàn giao"""
    
    def setUp(self):
        self.loader = DataLoader(REAL_IMAGES_DIR, REAL_GT_DIR, REAL_METADATA)
    
    def test_dataset_has_enough_images(self):
        """Bộ dữ liệu có đủ 8-12 ảnh theo kế hoạch"""
        count = len(self.loader.list_image_files())
        self.assertGreaterEqual(count, 8)
        self.assertLessEqual(count, 12)
    
    def test_every_image_has_ground_truth(self):
        """Mỗi ảnh đều có Ground Truth tương ứng"""
        report = self.loader.check_data_integrity()
        self.assertEqual(report['missing_gt'], [])
        self.assertEqual(report['size_mismatches'], [])
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['valid_pairs'], report['total_images'])
    
    def test_no_orphan_ground_truth(self):
        """Không có file GT mồ côi (không ảnh tương ứng)"""
        report = self.loader.full_check()
        self.assertEqual(report['orphan_gt'], [])
    
    def test_full_check_passes(self):
        """Toàn bộ ảnh đạt tiêu chí: 3 kênh uint8, GT 1 kênh 0/255, cùng kích thước"""
        report = self.loader.full_check()
        self.assertTrue(report['all_ok'], 
                        f"Các ảnh chưa đạt: {[(i['image'], i['issues']) for i in report['per_image'] if not i['ok']]}")
    
    def test_image_is_color_3_channels_uint8(self):
        """Ảnh màu 3 kênh, kiểu uint8"""
        for img_path, _ in self.loader.build_dataset():
            image = cv2.imread(img_path)
            self.assertEqual(image.ndim, 3)
            self.assertEqual(image.shape[2], 3)
            self.assertEqual(image.dtype, np.uint8)
    
    def test_ground_truth_is_binary_single_channel(self):
        """GT một kênh, uint8, chỉ chứa giá trị 0 và 255"""
        for _, gt_path in self.loader.build_dataset():
            gt = cv2.imread(gt_path, cv2.IMREAD_UNCHANGED)
            self.assertEqual(gt.ndim, 2)
            self.assertEqual(gt.dtype, np.uint8)
            self.assertTrue(set(np.unique(gt).tolist()).issubset({0, 255}),
                            f"GT {gt_path} chứa giá trị ngoài 0/255")
    
    def test_image_and_gt_same_size(self):
        """Ảnh và GT cùng kích thước H×W"""
        for img_path, gt_path in self.loader.build_dataset():
            image = cv2.imread(img_path)
            gt = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
            self.assertEqual(image.shape[:2], gt.shape)
    
    def test_ground_truth_not_empty(self):
        """Mỗi GT có vùng đối tượng (không rỗng)"""
        for _, gt_path in self.loader.build_dataset():
            gt = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
            self.assertGreater(np.count_nonzero(gt), 0)
    
    def test_metadata_covers_all_images(self):
        """metadata.csv mô tả đủ mọi ảnh trong bộ dữ liệu"""
        metadata = self.loader.load_metadata()
        self.assertEqual(len(metadata), len(self.loader.list_image_files()))
        
        metadata_ids = {row['image_id'] for row in metadata}
        for img_file in self.loader.list_image_files():
            self.assertIn(self.loader.extract_image_id(img_file), metadata_ids)
    
    def test_metadata_required_fields(self):
        """Mỗi dòng metadata có đủ trường bắt buộc"""
        required = ['image_id', 'image_file', 'gt_file', 'target_color',
                    'scenario', 'background', 'lighting', 'note']
        
        for row in self.loader.load_metadata():
            for field in required:
                self.assertIn(field, row)
                self.assertTrue(str(row[field]).strip(), 
                                f"Thiếu nội dung trường '{field}' ở ảnh {row.get('image_id')}")
    
    def test_metadata_files_exist(self):
        """Đường dẫn ảnh/GT trong metadata trỏ tới file thật"""
        for row in self.loader.load_metadata():
            for key in ('image_file', 'gt_file'):
                path = row[key]
                if not os.path.isabs(path):
                    path = os.path.join(PROJECT_ROOT, path)
                self.assertTrue(os.path.exists(path), f"{key} không tồn tại: {row[key]}")
    
    def test_metadata_covers_varied_scenarios(self):
        """Bộ dữ liệu đa dạng tình huống như kế hoạch yêu cầu"""
        scenarios = {row['scenario'] for row in self.loader.load_metadata()}
        self.assertGreaterEqual(len(scenarios), 5)
    
    def test_target_color_is_red(self):
        """Màu mục tiêu thống nhất là đỏ"""
        for row in self.loader.load_metadata():
            self.assertEqual(row['target_color'], 'Red')
    
    def test_all_loadable(self):
        """Loader nạp được toàn bộ cặp ảnh/GT mà không lỗi"""
        for img_path, gt_path in self.loader.build_dataset():
            image, gt = self.loader.load_image_gt_pair(img_path, gt_path)
            self.assertEqual(image.shape[:2], gt.shape)
            self.assertEqual(gt.shape, image.shape[:2])


if __name__ == '__main__':
    unittest.main()
