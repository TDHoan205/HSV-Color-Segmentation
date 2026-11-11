# -*- coding: utf-8 -*-
"""
Module: experiment.py
Chức năng: Điều phối và chạy các thí nghiệm với các cấu hình khác nhau
Phụ trách: Hoàn

Input: Dataset + config + các module
Output: Ảnh trung gian, ảnh cuối, bảng số liệu
"""

import os
import json
import csv
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path

from data_loader import DataLoader
from hsv_segment import HSVSegmenter
from median_filter import MedianFilter
from morphology import MorphologyOperator
from evaluation import SegmentationEvaluator


class ExperimentRunner:
    """Lớp điều phối các thí nghiệm phân đoạn"""
    
    def __init__(self, results_dir="results"):
        """
        Khởi tạo ExperimentRunner
        
        Args:
            results_dir: Thư mục lưu kết quả
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        
        self.data_loader = DataLoader()
        self.evaluator = SegmentationEvaluator()
        self.experiment_results = []
    
    def run_single_experiment(self, image_path, gt_path, config, exp_id):
        """
        Chạy một thí nghiệm đơn lẻ
        
        Args:
            image_path: Đường dẫn ảnh
            gt_path: Đường dẫn Ground Truth
            config: Dict cấu hình chứa HSV, Median, Morphology params
            exp_id: ID thí nghiệm
            
        Returns:
            dict: Kết quả thí nghiệm
        """
        try:
            # 1. Đọc dữ liệu
            image_bgr, gt_mask = self.data_loader.load_image_gt_pair(image_path, gt_path)
            
            # 2. Phân đoạn HSV
            hsv_config = config.get('hsv', {})
            segmenter = HSVSegmenter(hsv_config)
            mask_raw, image_hsv = segmenter.segment(image_bgr)
            
            # 3. Lọc Median
            median_config = config.get('median', {})
            kernel_size = median_config.get('kernel_size', 5)
            median_filter = MedianFilter(kernel_size)
            mask_median = median_filter.filter(mask_raw)
            
            # 4. Morphology
            morph_config = config.get('morphology', {})
            kernel_size_morph = morph_config.get('kernel_size', 5)
            kernel_shape = morph_config.get('kernel_shape', 'ellipse')
            operations = morph_config.get('operations', [('close', {'iterations': 1})])
            
            operator = MorphologyOperator(kernel_size_morph, kernel_shape)
            mask_morph = operator.apply_sequence(mask_median, operations)
            
            # 5. Đánh giá
            metrics = self.evaluator.compute_metrics(mask_morph, gt_mask)
            
            # Lưu kết quả
            result = {
                'exp_id': exp_id,
                'image': image_path,
                'timestamp': datetime.now().isoformat(),
                'config': config,
                'metrics': metrics,
                'masks': {
                    'raw': mask_raw,
                    'median': mask_median,
                    'morph': mask_morph,
                    'gt': gt_mask,
                },
                'images': {
                    'bgr': image_bgr,
                    'hsv': image_hsv,
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'exp_id': exp_id,
                'image': image_path,
                'error': str(e),
                'status': 'failed'
            }
    
    def run_batch_experiments(self, image_files, config_list, save_intermediate=True):
        """
        Chạy batch thí nghiệm với nhiều ảnh và cấu hình
        
        Args:
            image_files: Danh sách (image_path, gt_path) tuples
            config_list: Danh sách các cấu hình
            save_intermediate: Có lưu ảnh trung gian hay không
            
        Returns:
            list: Danh sách kết quả
        """
        all_results = []
        exp_id = 0
        
        for img_file, gt_file in image_files:
            for config in config_list:
                exp_id += 1
                
                # Chạy thí nghiệm
                result = self.run_single_experiment(img_file, gt_file, config, exp_id)
                all_results.append(result)
                
                # Lưu ảnh trung gian
                if save_intermediate and 'masks' in result:
                    self._save_intermediate_images(result)
        
        self.experiment_results = all_results
        return all_results
    
    def _save_intermediate_images(self, result):
        """Lưu ảnh trung gian của một thí nghiệm"""
        exp_id = result['exp_id']
        exp_dir = os.path.join(self.results_dir, f"exp_{exp_id:04d}")
        os.makedirs(exp_dir, exist_ok=True)
        
        # Lưu các mask
        masks = result.get('masks', {})
        cv2.imwrite(os.path.join(exp_dir, "mask_raw.png"), masks.get('raw'))
        cv2.imwrite(os.path.join(exp_dir, "mask_median.png"), masks.get('median'))
        cv2.imwrite(os.path.join(exp_dir, "mask_morph.png"), masks.get('morph'))
        cv2.imwrite(os.path.join(exp_dir, "gt_mask.png"), masks.get('gt'))
        
        # Lưu visualization
        vis = self.evaluator.create_visualization(masks.get('morph'), masks.get('gt'))
        cv2.imwrite(os.path.join(exp_dir, "visualization.png"), vis)
        
        # Lưu config
        with open(os.path.join(exp_dir, "config.json"), 'w', encoding='utf-8') as f:
            json.dump(result['config'], f, indent=2, ensure_ascii=False)
        
        # Lưu metrics
        with open(os.path.join(exp_dir, "metrics.json"), 'w', encoding='utf-8') as f:
            json.dump(result['metrics'], f, indent=2, ensure_ascii=False)
    
    def save_results_csv(self, filename="results.csv"):
        """Lưu kết quả thí nghiệm dưới dạng CSV"""
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Exp ID', 'Image', 'Status', 'TP', 'TN', 'FP', 'FN',
                'Pixel Accuracy', 'IoU', 'Precision', 'Recall', 'F1', 'Specificity'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.experiment_results:
                if 'error' in result:
                    writer.writerow({
                        'Exp ID': result['exp_id'],
                        'Image': result['image'],
                        'Status': 'Failed'
                    })
                else:
                    metrics = result['metrics']
                    writer.writerow({
                        'Exp ID': result['exp_id'],
                        'Image': result['image'],
                        'Status': 'Success',
                        'TP': metrics['TP'],
                        'TN': metrics['TN'],
                        'FP': metrics['FP'],
                        'FN': metrics['FN'],
                        'Pixel Accuracy': f"{metrics['pixel_accuracy']:.4f}",
                        'IoU': f"{metrics['iou']:.4f}",
                        'Precision': f"{metrics['precision']:.4f}",
                        'Recall': f"{metrics['recall']:.4f}",
                        'F1': f"{metrics['f1']:.4f}",
                        'Specificity': f"{metrics['specificity']:.4f}",
                    })
    
    def print_summary(self):
        """In tóm tắt kết quả thí nghiệm"""
        print("\n" + "="*60)
        print("TÓNG TẮT KẾT QUẢ THỰC NGHIỆM")
        print("="*60)
        
        successful = [r for r in self.experiment_results if 'error' not in r]
        failed = [r for r in self.experiment_results if 'error' in r]
        
        print(f"Tổng thí nghiệm: {len(self.experiment_results)}")
        print(f"Thành công: {len(successful)}")
        print(f"Thất bại: {len(failed)}")
        
        if successful:
            metrics_list = [r['metrics'] for r in successful]
            avg_accuracy = np.mean([m['pixel_accuracy'] for m in metrics_list])
            avg_iou = np.mean([m['iou'] for m in metrics_list])
            
            print(f"\nĐộ chính xác trung bình: {avg_accuracy:.4f}")
            print(f"IoU trung bình: {avg_iou:.4f}")
            
            # Tìm kết quả tốt nhất và tệ nhất
            best_result = max(successful, key=lambda r: r['metrics']['iou'])
            worst_result = min(successful, key=lambda r: r['metrics']['iou'])
            
            print(f"\nKết quả tốt nhất (Exp {best_result['exp_id']}): IoU = {best_result['metrics']['iou']:.4f}")
            print(f"Kết quả tệ nhất (Exp {worst_result['exp_id']}): IoU = {worst_result['metrics']['iou']:.4f}")
        
        if failed:
            print(f"\nThí nghiệm thất bại:")
            for r in failed:
                print(f"  Exp {r['exp_id']}: {r['error']}")


def main():
    """Hàm test - tạo dữ liệu giả để test"""
    # Tạo thư mục test
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/ground_truth", exist_ok=True)
    
    # Tạo ảnh test
    test_image = np.zeros((200, 200, 3), dtype=np.uint8)
    test_image[50:150, 50:150] = [0, 0, 255]  # Hình vuông đỏ
    cv2.imwrite("data/images/test_01.png", test_image)
    
    # Tạo Ground Truth
    gt_mask = np.zeros((200, 200), dtype=np.uint8)
    gt_mask[50:150, 50:150] = 255
    cv2.imwrite("data/ground_truth/test_01.png", gt_mask)
    
    # Tạo cấu hình thí nghiệm
    configs = [
        {
            'name': 'Config_1_Tight',
            'hsv': {
                'color_name': 'Red',
                'hue_ranges': [[0, 10], [170, 180]],
                'saturation': [120, 255],
                'value': [120, 255],
            },
            'median': {'kernel_size': 5},
            'morphology': {
                'kernel_size': 5,
                'kernel_shape': 'ellipse',
                'operations': [('close', {'iterations': 1})],
            }
        },
        {
            'name': 'Config_2_Loose',
            'hsv': {
                'color_name': 'Red',
                'hue_ranges': [[0, 15], [165, 180]],
                'saturation': [80, 255],
                'value': [80, 255],
            },
            'median': {'kernel_size': 3},
            'morphology': {
                'kernel_size': 3,
                'kernel_shape': 'rect',
                'operations': [('open', {'iterations': 1})],
            }
        }
    ]
    
    # Chạy thí nghiệm
    runner = ExperimentRunner()
    results = runner.run_batch_experiments(
        [("data/images/test_01.png", "data/ground_truth/test_01.png")],
        configs
    )
    
    # Lưu kết quả
    runner.save_results_csv()
    runner.print_summary()
    
    print(f"\nKết quả đã lưu tại: {runner.results_dir}")


if __name__ == "__main__":
    main()
