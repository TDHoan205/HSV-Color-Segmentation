# -*- coding: utf-8 -*-
"""
Module: evaluation.py
Chức năng: Đánh giá hiệu suất phân đoạn
Phụ trách: Hoàn

Input: pred_mask + gt_mask
Output: TP/TN/FP/FN, Accuracy, IoU

Quy ước:
- Hai Mask cùng kích thước
- Nhị phân hóa nhất quán
- Xử lý mẫu số bằng 0
"""

import numpy as np
import cv2


class SegmentationEvaluator:
    """Lớp đánh giá hiệu suất phân đoạn"""
    
    def __init__(self):
        """Khởi tạo Evaluator"""
        pass
    
    @staticmethod
    def _validate_masks(pred_mask, gt_mask):
        """
        Kiểm tra tính hợp lệ của các Mask
        
        Args:
            pred_mask: Mask dự đoán
            gt_mask: Ground Truth Mask
            
        Raises:
            ValueError: Nếu Mask không hợp lệ
        """
        if pred_mask is None or gt_mask is None:
            raise ValueError("Mask không được phép là None")
        
        if pred_mask.size == 0 or gt_mask.size == 0:
            raise ValueError("Mask không được phép rỗng")
        
        if pred_mask.shape != gt_mask.shape:
            raise ValueError(
                f"Kích thước Mask không khớp - Dự đoán: {pred_mask.shape}, "
                f"GT: {gt_mask.shape}"
            )
        
        if len(pred_mask.shape) > 2:
            raise ValueError(f"Mask phải là 2D, nhận: {pred_mask.shape}")
    
    @staticmethod
    def _binarize_mask(mask):
        """
        Nhị phân hóa Mask (0/255 → 0/1)
        
        Args:
            mask: Mask đầu vào
            
        Returns:
            mask_binary: Mask nhị phân (0/1)
        """
        if mask.dtype == np.bool_:
            return mask.astype(np.uint8)
        
        # Chuyển đổi 0/255 hoặc bất kỳ giá trị thành 0/1
        return (mask > 0).astype(np.uint8)
    
    @staticmethod
    def compute_confusion_matrix(pred_mask, gt_mask):
        """
        Tính ma trận nhầm lẫn: TP, TN, FP, FN
        
        Args:
            pred_mask: Mask dự đoán
            gt_mask: Ground Truth Mask
            
        Returns:
            dict: {
                'TP': True Positives,
                'TN': True Negatives,
                'FP': False Positives,
                'FN': False Negatives,
                'total_pixels': Tổng pixel
            }
        """
        SegmentationEvaluator._validate_masks(pred_mask, gt_mask)
        
        # Nhị phân hóa
        pred_binary = SegmentationEvaluator._binarize_mask(pred_mask)
        gt_binary = SegmentationEvaluator._binarize_mask(gt_mask)
        
        # Tính TP, TN, FP, FN
        tp = np.sum((pred_binary == 1) & (gt_binary == 1))
        tn = np.sum((pred_binary == 0) & (gt_binary == 0))
        fp = np.sum((pred_binary == 1) & (gt_binary == 0))
        fn = np.sum((pred_binary == 0) & (gt_binary == 1))
        
        return {
            'TP': int(tp),
            'TN': int(tn),
            'FP': int(fp),
            'FN': int(fn),
            'total_pixels': int(pred_mask.size)
        }
    
    @staticmethod
    def compute_pixel_accuracy(pred_mask, gt_mask):
        """
        Tính Pixel Accuracy (độ chính xác pixel)
        
        Công thức: (TP + TN) / (TP + TN + FP + FN)
        
        Args:
            pred_mask: Mask dự đoán
            gt_mask: Ground Truth Mask
            
        Returns:
            float: Pixel Accuracy (0 đến 1)
        """
        cm = SegmentationEvaluator.compute_confusion_matrix(pred_mask, gt_mask)
        
        total = cm['TP'] + cm['TN'] + cm['FP'] + cm['FN']
        
        if total == 0:
            return 0.0
        
        accuracy = (cm['TP'] + cm['TN']) / total
        return float(accuracy)
    
    @staticmethod
    def compute_iou(pred_mask, gt_mask):
        """
        Tính Intersection over Union (IoU) / Jaccard Index
        
        Công thức: Intersection / Union = TP / (TP + FP + FN)
        
        Args:
            pred_mask: Mask dự đoán
            gt_mask: Ground Truth Mask
            
        Returns:
            float: IoU (0 đến 1)
        """
        cm = SegmentationEvaluator.compute_confusion_matrix(pred_mask, gt_mask)
        
        intersection = cm['TP']
        union = cm['TP'] + cm['FP'] + cm['FN']
        
        if union == 0:
            return 0.0
        
        iou = intersection / union
        return float(iou)
    
    @staticmethod
    def compute_metrics(pred_mask, gt_mask):
        """
        Tính tất cả các chỉ số đánh giá
        
        Args:
            pred_mask: Mask dự đoán
            gt_mask: Ground Truth Mask
            
        Returns:
            dict: Chứa TP, TN, FP, FN, Accuracy, IoU, F1, Precision, Recall
        """
        cm = SegmentationEvaluator.compute_confusion_matrix(pred_mask, gt_mask)
        
        # Pixel Accuracy
        total = cm['TP'] + cm['TN'] + cm['FP'] + cm['FN']
        pixel_accuracy = (cm['TP'] + cm['TN']) / total if total > 0 else 0.0
        
        # IoU
        union = cm['TP'] + cm['FP'] + cm['FN']
        iou = cm['TP'] / union if union > 0 else 0.0
        
        # Precision (Độ chính xác)
        tp_fp = cm['TP'] + cm['FP']
        precision = cm['TP'] / tp_fp if tp_fp > 0 else 0.0
        
        # Recall (Độ nhạy)
        tp_fn = cm['TP'] + cm['FN']
        recall = cm['TP'] / tp_fn if tp_fn > 0 else 0.0
        
        # F1 Score
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0
        
        # Specificity (Độ đặc hiệu)
        tn_fp = cm['TN'] + cm['FP']
        specificity = cm['TN'] / tn_fp if tn_fp > 0 else 0.0
        
        return {
            'TP': cm['TP'],
            'TN': cm['TN'],
            'FP': cm['FP'],
            'FN': cm['FN'],
            'total_pixels': cm['total_pixels'],
            'pixel_accuracy': float(pixel_accuracy),
            'iou': float(iou),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'specificity': float(specificity),
        }
    
    @staticmethod
    def create_visualization(pred_mask, gt_mask):
        """
        Tạo ảnh visualize so sánh dự đoán và GT
        
        Args:
            pred_mask: Mask dự đoán
            gt_mask: Ground Truth Mask
            
        Returns:
            np.ndarray: Ảnh visualize RGB
                       Xanh lá: TP (dự đoán đúng)
                       Đỏ: FP (dự đoán sai, không có GT)
                       Xanh dương: FN (bỏ sót, có GT nhưng không dự đoán)
        """
        SegmentationEvaluator._validate_masks(pred_mask, gt_mask)
        
        # Nhị phân hóa
        pred_binary = SegmentationEvaluator._binarize_mask(pred_mask)
        gt_binary = SegmentationEvaluator._binarize_mask(gt_mask)
        
        # Tạo ảnh RGB
        h, w = pred_mask.shape
        vis = np.zeros((h, w, 3), dtype=np.uint8)
        
        # TP: Xanh lá (0, 255, 0)
        tp_mask = (pred_binary == 1) & (gt_binary == 1)
        vis[tp_mask] = [0, 255, 0]
        
        # FP: Đỏ (0, 0, 255)
        fp_mask = (pred_binary == 1) & (gt_binary == 0)
        vis[fp_mask] = [0, 0, 255]
        
        # FN: Xanh dương (255, 0, 0)
        fn_mask = (pred_binary == 0) & (gt_binary == 1)
        vis[fn_mask] = [255, 0, 0]
        
        return vis


def main():
    """Hàm test module"""
    # Tạo GT mask
    gt_mask = np.zeros((100, 100), dtype=np.uint8)
    gt_mask[20:80, 20:80] = 255
    
    # Tạo pred mask (hơi khác GT)
    pred_mask = np.zeros((100, 100), dtype=np.uint8)
    pred_mask[25:75, 25:75] = 255
    pred_mask[30:35, 30:35] = 0  # Lỗ nhỏ
    
    # Tạo evaluator
    evaluator = SegmentationEvaluator()
    
    # Tính chỉ số
    metrics = evaluator.compute_metrics(pred_mask, gt_mask)
    
    print("=== SEGMENTATION EVALUATION ===")
    print(f"TP: {metrics['TP']}")
    print(f"TN: {metrics['TN']}")
    print(f"FP: {metrics['FP']}")
    print(f"FN: {metrics['FN']}")
    print(f"Pixel Accuracy: {metrics['pixel_accuracy']:.4f}")
    print(f"IoU: {metrics['iou']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1']:.4f}")
    print(f"Specificity: {metrics['specificity']:.4f}")
    
    # Visualize
    vis = evaluator.create_visualization(pred_mask, gt_mask)
    print(f"\nVisualization shape: {vis.shape}")


if __name__ == "__main__":
    main()
