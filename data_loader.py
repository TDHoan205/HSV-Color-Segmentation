# -*- coding: utf-8 -*-
"""
Module: data_loader.py
Chức năng: Đọc và quản lý dữ liệu ảnh và Ground Truth
Phụ trách: Anh Quân

Input: Đường dẫn ảnh + Ground Truth
Output: image_bgr, gt_mask

Quy ước:
- Ảnh BGR 3 kênh (uint8)
- Ground Truth 1 kênh, uint8, giá trị 0/255
- Cùng kích thước H×W
- Báo lỗi nếu thiếu file hoặc lệch kích thước
"""

import cv2
import os
import numpy as np
from pathlib import Path


class DataLoader:
    """Lớp để đọc và quản lý dữ liệu ảnh đầu vào và nhãn Ground Truth"""
    
    def __init__(self, images_dir="data/images", ground_truth_dir="data/ground_truth"):
        """
        Khởi tạo DataLoader
        
        Args:
            images_dir: Thư mục chứa ảnh đầu vào
            ground_truth_dir: Thư mục chứa Ground Truth Mask
        """
        self.images_dir = images_dir
        self.ground_truth_dir = ground_truth_dir
        self.image_files = []
        self.gt_files = []
        self._validate_directory()
        
    def _validate_directory(self):
        """Kiểm tra sự tồn tại của các thư mục"""
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir, exist_ok=True)
            
        if not os.path.exists(self.ground_truth_dir):
            os.makedirs(self.ground_truth_dir, exist_ok=True)
    
    def load_image(self, image_path):
        """
        Đọc ảnh dưới định dạng BGR
        
        Args:
            image_path: Đường dẫn file ảnh
            
        Returns:
            image_bgr: Ảnh BGR (H, W, 3), uint8
            
        Raises:
            FileNotFoundError: Nếu file không tồn tại
            ValueError: Nếu không thể đọc ảnh
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Ảnh không tồn tại: {image_path}")
        
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            raise ValueError(f"Không thể đọc ảnh: {image_path}")
        
        # Đảm bảo ảnh có 3 kênh
        if len(image_bgr.shape) == 2:
            image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_GRAY2BGR)
        elif image_bgr.shape[2] == 4:
            image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_BGRA2BGR)
        
        return image_bgr
    
    def load_ground_truth(self, gt_path):
        """
        Đọc Ground Truth Mask
        
        Args:
            gt_path: Đường dẫn file Ground Truth
            
        Returns:
            gt_mask: Mask (H, W), uint8, giá trị 0/255
            
        Raises:
            FileNotFoundError: Nếu file không tồn tại
            ValueError: Nếu không thể đọc file hoặc định dạng sai
        """
        if not os.path.exists(gt_path):
            raise FileNotFoundError(f"Ground Truth không tồn tại: {gt_path}")
        
        gt_mask = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
        if gt_mask is None:
            raise ValueError(f"Không thể đọc Ground Truth: {gt_path}")
        
        # Nhị phân hóa: nếu có giá trị ngoài 0/255, chuẩn hóa lại
        gt_mask = cv2.threshold(gt_mask, 127, 255, cv2.THRESH_BINARY)[1]
        
        return gt_mask
    
    def load_image_gt_pair(self, image_path, gt_path):
        """
        Đọc cặp ảnh và Ground Truth, kiểm tra kích thước khớp
        
        Args:
            image_path: Đường dẫn ảnh
            gt_path: Đường dẫn Ground Truth
            
        Returns:
            image_bgr: Ảnh BGR (H, W, 3)
            gt_mask: Mask Ground Truth (H, W)
            
        Raises:
            ValueError: Nếu kích thước không khớp
        """
        image_bgr = self.load_image(image_path)
        gt_mask = self.load_ground_truth(gt_path)
        
        # Kiểm tra kích thước khớp
        if image_bgr.shape[:2] != gt_mask.shape:
            raise ValueError(
                f"Kích thước không khớp - Ảnh: {image_bgr.shape[:2]}, "
                f"GT: {gt_mask.shape}. File: {image_path} vs {gt_path}"
            )
        
        return image_bgr, gt_mask
    
    def list_image_files(self):
        """
        Liệt kê tất cả file ảnh trong thư mục
        
        Returns:
            list: Danh sách tên file ảnh
        """
        if not os.path.exists(self.images_dir):
            return []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_files = [
            f for f in os.listdir(self.images_dir)
            if os.path.splitext(f)[1].lower() in image_extensions
        ]
        return sorted(image_files)
    
    def check_data_integrity(self):
        """
        Kiểm tra tính toàn vẹn của dữ liệu
        
        Returns:
            dict: Báo cáo kiểm tra
        """
        report = {
            'total_images': 0,
            'valid_pairs': 0,
            'missing_gt': [],
            'size_mismatches': [],
            'errors': []
        }
        
        image_files = self.list_image_files()
        report['total_images'] = len(image_files)
        
        for img_file in image_files:
            img_path = os.path.join(self.images_dir, img_file)
            base_name = os.path.splitext(img_file)[0]
            gt_path = os.path.join(self.ground_truth_dir, f"{base_name}.png")
            
            if not os.path.exists(gt_path):
                report['missing_gt'].append(img_file)
                continue
            
            try:
                image_bgr, gt_mask = self.load_image_gt_pair(img_path, gt_path)
                if image_bgr.shape[:2] == gt_mask.shape:
                    report['valid_pairs'] += 1
                else:
                    report['size_mismatches'].append({
                        'image': img_file,
                        'image_size': image_bgr.shape[:2],
                        'gt_size': gt_mask.shape
                    })
            except Exception as e:
                report['errors'].append({
                    'image': img_file,
                    'error': str(e)
                })
        
        return report


def main():
    """Hàm test để kiểm tra module"""
    import sys, io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    loader = DataLoader()
    report = loader.check_data_integrity()
    
    print("[DATA LOADER TEST]")
    print("Total images: {}".format(report['total_images']))
    print("Valid pairs: {}".format(report['valid_pairs']))
    print("Missing GT: {}".format(len(report['missing_gt'])))
    print("Size mismatches: {}".format(len(report['size_mismatches'])))
    print("Errors: {}".format(len(report['errors'])))


if __name__ == "__main__":
    main()
