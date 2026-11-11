# -*- coding: utf-8 -*-
"""
Test Module: test_evaluation.py
Kiểm thử module evaluation
"""

import unittest
import numpy as np
from evaluation import SegmentationEvaluator


class TestSegmentationEvaluator(unittest.TestCase):
    """Kiểm thử lớp SegmentationEvaluator"""
    
    def setUp(self):
        """Chuẩn bị test"""
        # Tạo GT mask
        self.gt_mask = np.zeros((100, 100), dtype=np.uint8)
        self.gt_mask[20:80, 20:80] = 255
        
        # Tạo pred mask (chính xác 100%)
        self.pred_perfect = self.gt_mask.copy()
        
        # Tạo pred mask (sai 100%)
        self.pred_wrong = np.zeros((100, 100), dtype=np.uint8)
        self.pred_wrong[0:20, 0:20] = 255
        
        # Tạo pred mask (50% chính xác)
        self.pred_half = np.zeros((100, 100), dtype=np.uint8)
        self.pred_half[20:60, 20:80] = 255
    
    def test_confusion_matrix_perfect(self):
        """Test ma trận nhầm lẫn - dự đoán hoàn hảo"""
        evaluator = SegmentationEvaluator()
        cm = evaluator.compute_confusion_matrix(self.pred_perfect, self.gt_mask)
        
        # Tất cả pixel đúng
        self.assertGreater(cm['TP'], 0)
        self.assertEqual(cm['FP'], 0)
        self.assertEqual(cm['FN'], 0)
    
    def test_confusion_matrix_wrong(self):
        """Test ma trận nhầm lẫn - dự đoán sai hoàn toàn"""
        evaluator = SegmentationEvaluator()
        cm = evaluator.compute_confusion_matrix(self.pred_wrong, self.gt_mask)
        
        self.assertEqual(cm['TP'], 0)
        self.assertGreater(cm['FP'], 0)
        self.assertGreater(cm['FN'], 0)
    
    def test_pixel_accuracy_perfect(self):
        """Test độ chính xác pixel - hoàn hảo"""
        evaluator = SegmentationEvaluator()
        accuracy = evaluator.compute_pixel_accuracy(self.pred_perfect, self.gt_mask)
        
        self.assertAlmostEqual(accuracy, 1.0, places=2)
    
    def test_iou_perfect(self):
        """Test IoU - hoàn hảo"""
        evaluator = SegmentationEvaluator()
        iou = evaluator.compute_iou(self.pred_perfect, self.gt_mask)
        
        self.assertAlmostEqual(iou, 1.0, places=2)
    
    def test_iou_half(self):
        """Test IoU - 50% chính xác"""
        evaluator = SegmentationEvaluator()
        iou = evaluator.compute_iou(self.pred_half, self.gt_mask)
        
        # IoU phải trong khoảng hợp lý (giữa 0 và 1)
        self.assertGreater(iou, 0)
        self.assertLess(iou, 1)
    
    def test_compute_metrics(self):
        """Test tính toàn bộ chỉ số"""
        evaluator = SegmentationEvaluator()
        metrics = evaluator.compute_metrics(self.pred_perfect, self.gt_mask)
        
        self.assertIn('TP', metrics)
        self.assertIn('TN', metrics)
        self.assertIn('FP', metrics)
        self.assertIn('FN', metrics)
        self.assertIn('pixel_accuracy', metrics)
        self.assertIn('iou', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1', metrics)
    
    def test_size_mismatch(self):
        """Test xử lý kích thước không khớp"""
        evaluator = SegmentationEvaluator()
        wrong_size = np.zeros((50, 50), dtype=np.uint8)
        
        with self.assertRaises(ValueError):
            evaluator.compute_metrics(wrong_size, self.gt_mask)
    
    def test_visualization(self):
        """Test tạo ảnh visualize"""
        evaluator = SegmentationEvaluator()
        vis = evaluator.create_visualization(self.pred_half, self.gt_mask)
        
        self.assertEqual(vis.shape, (100, 100, 3))
        self.assertEqual(vis.dtype, np.uint8)


if __name__ == '__main__':
    unittest.main()
