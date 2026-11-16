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
from src.data_loader import (DataLoader, build_dataset_from_manifest, load_manifest,
                             load_manifest_sample, validate_manifest, validate_raw_gt)

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


MANIFEST_PATH = os.path.join(PROJECT_ROOT, 'data', 'dataset_manifest.csv')


@unittest.skipUnless(os.path.isfile(MANIFEST_PATH), "Chưa có data/dataset_manifest.csv")
class TestSyntheticReferenceDataset(unittest.TestCase):
    """Hợp đồng cũ (10 ảnh đỏ tổng hợp + GT), nay xác định qua manifest (split=synthetic_reference).
    Thư mục data/images có thêm 24 ảnh thật chưa có GT, nên không còn đếm toàn thư mục."""

    def setUp(self):
        self.loader = DataLoader(REAL_IMAGES_DIR, REAL_GT_DIR, REAL_METADATA)
        self.records = build_dataset_from_manifest(MANIFEST_PATH, PROJECT_ROOT,
                                                   split='synthetic_reference')
        self.files = {os.path.basename(r['image_path']) for r in self.records}

    def _pairs(self):
        return [(r['image_abs'], r['gt_abs']) for r in self.records]

    def test_dataset_has_enough_images(self):
        self.assertGreaterEqual(len(self.records), 8)
        self.assertLessEqual(len(self.records), 12)

    def test_every_synthetic_image_has_ground_truth(self):
        report = self.loader.check_data_integrity()
        self.assertFalse(self.files & set(report['missing_gt']))
        self.assertEqual([e for e in report['errors'] if e['image'] in self.files], [])
        self.assertEqual([e for e in report['size_mismatches'] if e['image'] in self.files], [])

    def test_no_orphan_ground_truth(self):
        self.assertEqual(self.loader.full_check()['orphan_gt'], [])

    def test_synthetic_pairs_pass_full_check(self):
        report = self.loader.full_check()
        bad = [(i['image'], i['issues']) for i in report['per_image']
               if i['image'] in self.files and not i['ok']]
        self.assertEqual(bad, [])

    def test_image_is_color_3_channels_uint8(self):
        for img_path, _ in self._pairs():
            image = cv2.imread(img_path)
            self.assertEqual(image.ndim, 3)
            self.assertEqual(image.shape[2], 3)
            self.assertEqual(image.dtype, np.uint8)

    def test_ground_truth_is_binary_single_channel(self):
        for _, gt_path in self._pairs():
            gt = cv2.imread(gt_path, cv2.IMREAD_UNCHANGED)
            self.assertEqual(gt.ndim, 2)
            self.assertEqual(gt.dtype, np.uint8)
            self.assertTrue(set(np.unique(gt).tolist()).issubset({0, 255}))

    def test_image_and_gt_same_size(self):
        for img_path, gt_path in self._pairs():
            self.assertEqual(cv2.imread(img_path).shape[:2],
                             cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE).shape)

    def test_ground_truth_not_empty(self):
        for _, gt_path in self._pairs():
            self.assertGreater(np.count_nonzero(cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)), 0)

    def test_legacy_metadata_covers_synthetic_images(self):
        ids = {row['image_id'] for row in self.loader.load_metadata()}
        for f in self.files:
            self.assertIn(self.loader.extract_image_id(f), ids)

    def test_metadata_required_fields(self):
        required = ['image_id', 'image_file', 'gt_file', 'target_color',
                    'scenario', 'background', 'lighting', 'note']
        for row in self.loader.load_metadata():
            for field in required:
                self.assertTrue(str(row.get(field, '')).strip(),
                                f"Thiếu trường '{field}' ở {row.get('image_id')}")

    def test_metadata_files_exist(self):
        for row in self.loader.load_metadata():
            for key in ('image_file', 'gt_file'):
                self.assertTrue(os.path.exists(os.path.join(PROJECT_ROOT, row[key])))

    def test_metadata_covers_varied_scenarios(self):
        self.assertGreaterEqual(len({row['scenario'] for row in self.loader.load_metadata()}), 5)

    def test_target_color_is_red(self):
        for row in self.loader.load_metadata():
            self.assertEqual(row['target_color'], 'Red')

    def test_all_loadable(self):
        for img_path, gt_path in self._pairs():
            image, gt = self.loader.load_image_gt_pair(img_path, gt_path)
            self.assertEqual(image.shape[:2], gt.shape)


@unittest.skipUnless(os.path.isfile(MANIFEST_PATH), "Chưa có data/dataset_manifest.csv")
class TestManifestContract(unittest.TestCase):
    """Contract Phase D: manifest, validator, loader theo manifest, split, trung thực dữ liệu thật."""

    def test_manifest_valid_with_hashes(self):
        res = validate_manifest(MANIFEST_PATH, PROJECT_ROOT, check_hash=True)
        self.assertEqual(res['errors'], [])

    def test_manifest_covers_every_image_file(self):
        _, rows = load_manifest(MANIFEST_PATH)
        on_disk = {'data/images/' + f for f in os.listdir(REAL_IMAGES_DIR)
                   if os.path.splitext(f)[1].lower() in DataLoader.IMAGE_EXTENSIONS}
        self.assertEqual({r['image_path'] for r in rows}, on_disk)

    def test_unapproved_have_reason_and_next_action(self):
        _, rows = load_manifest(MANIFEST_PATH)
        for r in rows:
            if r['status'] != 'approved':
                self.assertTrue(r['exclusion_reason'] and r['next_action'], r['sample_id'])
                self.assertEqual(r['gt_path'], '')

    def test_no_synthetic_counted_as_real(self):
        for r in build_dataset_from_manifest(MANIFEST_PATH, PROJECT_ROOT, data_type='real'):
            self.assertNotEqual(r['split'], 'synthetic_reference')

    def test_split_has_no_group_leakage(self):
        _, rows = load_manifest(MANIFEST_PATH)
        by_group = {}
        for r in rows:
            by_group.setdefault(r['group_id'], set()).add(r['split'])
        for g, splits in by_group.items():
            self.assertFalse({'tuning', 'final_test'} <= splits, g)

    def test_no_hash_overlap_between_tuning_and_final_test(self):
        _, rows = load_manifest(MANIFEST_PATH)
        t = {r['image_sha256'] for r in rows if r['split'] == 'tuning'}
        f = {r['image_sha256'] for r in rows if r['split'] == 'final_test'}
        self.assertEqual(t & f, set())

    def test_loader_loads_every_approved_record(self):
        recs = build_dataset_from_manifest(MANIFEST_PATH, PROJECT_ROOT)
        _, rows = load_manifest(MANIFEST_PATH)
        self.assertEqual(len(recs), sum(1 for r in rows if r['status'] == 'approved'))
        for rec in recs:
            img, gt = load_manifest_sample(rec)
            self.assertEqual(img.shape[:2], gt.shape)


class TestRawGtValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, name, arr):
        p = os.path.join(self.tmp, name)
        cv2.imwrite(p, arr)
        return p

    def test_accepts_valid(self):
        gt = np.zeros((10, 12), np.uint8)
        gt[2:5, 3:6] = 255
        self.assertTrue(validate_raw_gt(self._write('ok.png', gt), (10, 12))['ok'])

    def test_rejects_gray_values_without_fixing(self):
        gt = np.full((10, 12), 128, np.uint8)
        p = self._write('gray.png', gt)
        self.assertFalse(validate_raw_gt(p, (10, 12))['ok'])
        self.assertEqual(int(cv2.imread(p, cv2.IMREAD_UNCHANGED).max()), 128)

    def test_rejects_wrong_size_three_channel_empty_and_missing(self):
        gt = np.zeros((10, 12), np.uint8)
        gt[1, 1] = 255
        self.assertFalse(validate_raw_gt(self._write('a.png', gt), (11, 12))['ok'])
        self.assertFalse(validate_raw_gt(self._write('b.png', np.dstack([gt] * 3)), (10, 12))['ok'])
        self.assertFalse(validate_raw_gt(self._write('c.png', np.zeros((10, 12), np.uint8)), (10, 12))['ok'])
        self.assertFalse(validate_raw_gt(os.path.join(self.tmp, 'none.png'))['ok'])

    def test_rejects_non_png_content(self):
        gt = np.zeros((10, 12), np.uint8)
        gt[2:5, 3:6] = 255
        p = self._write('x.jpg', gt)
        self.assertFalse(validate_raw_gt(p, (10, 12))['ok'])


if __name__ == '__main__':
    unittest.main()
