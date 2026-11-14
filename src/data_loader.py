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
import csv
import os
import numpy as np
from pathlib import Path


class DataLoader:
    """Lớp để đọc và quản lý dữ liệu ảnh đầu vào và nhãn Ground Truth"""
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    
    def __init__(self, images_dir="data/images", ground_truth_dir="data/ground_truth",
                 metadata_path="data/metadata.csv"):
        """
        Khởi tạo DataLoader
        
        Args:
            images_dir: Thư mục chứa ảnh đầu vào
            ground_truth_dir: Thư mục chứa Ground Truth Mask
            metadata_path: Đường dẫn file metadata.csv mô tả tình huống ảnh
        """
        self.images_dir = images_dir
        self.ground_truth_dir = ground_truth_dir
        self.metadata_path = metadata_path
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
        
        image_files = [
            f for f in os.listdir(self.images_dir)
            if os.path.splitext(f)[1].lower() in self.IMAGE_EXTENSIONS
        ]
        return sorted(image_files)
    
    def list_ground_truth_files(self):
        """
        Liệt kê tất cả file Ground Truth trong thư mục
        
        Returns:
            list: Danh sách tên file Ground Truth
        """
        if not os.path.exists(self.ground_truth_dir):
            return []
        
        gt_files = [
            f for f in os.listdir(self.ground_truth_dir)
            if os.path.splitext(f)[1].lower() in self.IMAGE_EXTENSIONS
        ]
        return sorted(gt_files)
    
    def get_gt_path(self, image_path):
        """
        Suy ra đường dẫn Ground Truth tương ứng với một ảnh.
        Quy ước: ảnh `img_01_ten.jpg` -> GT `data/ground_truth/img_01_ten.png`
        
        Args:
            image_path: Đường dẫn ảnh đầu vào
        
        Returns:
            str: Đường dẫn Ground Truth dự kiến
        """
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        return os.path.join(self.ground_truth_dir, f"{base_name}.png")
    
    def build_dataset(self):
        """
        Dựng danh sách cặp (image_path, gt_path) từ thư mục ảnh.
        Chỉ trả về các cặp có GT tồn tại trên đĩa.
        
        Returns:
            list: Danh sách tuple (image_path, gt_path)
        """
        pairs = []
        for img_file in self.list_image_files():
            img_path = os.path.join(self.images_dir, img_file)
            gt_path = self.get_gt_path(img_path)
            if os.path.exists(gt_path):
                pairs.append((img_path, gt_path))
        return pairs
    
    def load_metadata(self):
        """
        Đọc file metadata.csv mô tả tình huống của từng ảnh.
        
        Returns:
            list: Danh sách dict, mỗi dict là một ảnh.
                    Trả về [] nếu file không tồn tại.
        """
        if not os.path.exists(self.metadata_path):
            return []
        
        rows = []
        with open(self.metadata_path, 'r', newline='', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))
        return rows
    
    @staticmethod
    def extract_image_id(filename):
        """
        Lấy mã ảnh từ tên file theo quy ước `<image_id>_<tên>.ext`,
        ví dụ 'img_01_red_circle_light_bg.jpg' -> 'img_01'.
        
        Args:
            filename: Tên file (kèm hoặc không kèm đường dẫn)
        
        Returns:
            str: Mã ảnh
        """
        base = os.path.splitext(os.path.basename(filename))[0]
        parts = base.split('_')
        if len(parts) >= 2:
            return f"{parts[0]}_{parts[1]}"
        return base
    
    def get_metadata_by_id(self, image_id):
        """
        Lấy metadata của một ảnh theo mã (image_id).
        
        Args:
            image_id: Mã ảnh, ví dụ 'img_01'
        
        Returns:
            dict hoặc None: Metadata của ảnh, None nếu không tìm thấy
        """
        for row in self.load_metadata():
            if row.get('image_id') == image_id:
                return row
        return None
    
    def validate_pair(self, image_path, gt_path):
        """
        Kiểm tra chi tiết một cặp ảnh / Ground Truth theo đúng tiêu chí bàn giao:
          - Ảnh màu 3 kênh, uint8
          - Ground Truth 1 kênh, uint8, chỉ chứa giá trị 0 hoặc 255
          - Hai ảnh cùng kích thước H×W
          - Vùng đối tượng trong GT không rỗng
        
        Args:
            image_path: Đường dẫn ảnh
            gt_path: Đường dẫn Ground Truth
        
        Returns:
            dict: Kết quả kiểm tra gồm 'ok' (bool) và 'issues' (list)
        """
        issues = []
        info = {}
        
        # 1) Ảnh
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            return {'ok': False, 'issues': [f"Không đọc được ảnh: {image_path}"], 'info': {}}
        
        if image.ndim != 3 or image.shape[2] != 3:
            issues.append(f"Ảnh phải có 3 kênh màu, nhận shape {image.shape}")
        if image.dtype != np.uint8:
            issues.append(f"Ảnh phải là uint8, nhận {image.dtype}")
        
        info['image_shape'] = image.shape
        info['image_dtype'] = str(image.dtype)
        info['width'] = image.shape[1]
        info['height'] = image.shape[0]
        
        # 2) Ground Truth
        gt_raw = cv2.imread(gt_path, cv2.IMREAD_UNCHANGED)
        if gt_raw is None:
            return {'ok': False, 'issues': [f"Không đọc được Ground Truth: {gt_path}"], 'info': info}
        
        if gt_raw.ndim != 2:
            issues.append(f"Ground Truth phải là ảnh 1 kênh, nhận shape {gt_raw.shape}")
        if gt_raw.dtype != np.uint8:
            issues.append(f"Ground Truth phải là uint8, nhận {gt_raw.dtype}")
        
        unique_values = np.unique(gt_raw)
        if not set(unique_values.tolist()).issubset({0, 255}):
            issues.append(f"Ground Truth phải nhị phân 0/255, nhận các giá trị {unique_values.tolist()}")
        
        # 3) Kích thước
        if image.shape[:2] != gt_raw.shape[:2]:
            issues.append(
                f"Kích thước không khớp - Ảnh: {image.shape[:2]}, GT: {gt_raw.shape[:2]}"
            )
        
        # 4) Vùng đối tượng
        object_pixels = int(np.count_nonzero(gt_raw))
        info['object_pixels'] = object_pixels
        info['object_ratio'] = round(object_pixels / float(gt_raw.size), 4) if gt_raw.size else 0.0
        if object_pixels == 0:
            issues.append("Ground Truth rỗng (không có vùng đối tượng)")
        
        info['gt_shape'] = gt_raw.shape
        info['gt_dtype'] = str(gt_raw.dtype)
        info['gt_values'] = unique_values.tolist()
        
        return {'ok': len(issues) == 0, 'issues': issues, 'info': info}
    
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
    
    def full_check(self):
        """
        Kiểm tra toàn diện: tính toàn vẹn + tuân thủ tiêu chí dữ liệu + đối chiếu metadata.
        Đây là hàm dùng để bàn giao dữ liệu cho cả nhóm.
        
        Returns:
            dict: Báo cáo chi tiết theo từng ảnh
        """
        integrity = self.check_data_integrity()
        metadata = self.load_metadata()
        metadata_ids = {row.get('image_id') for row in metadata}
        
        per_image = []
        all_ok = True
        
        for img_file in self.list_image_files():
            img_path = os.path.join(self.images_dir, img_file)
            gt_path = self.get_gt_path(img_path)
            base_name = os.path.splitext(img_file)[0]
            
            if not os.path.exists(gt_path):
                per_image.append({
                    'image': img_file, 'ok': False,
                    'issues': [f"Thiếu Ground Truth: {gt_path}"], 'info': {}
                })
                all_ok = False
                continue
            
            result = self.validate_pair(img_path, gt_path)
            image_id = self.extract_image_id(img_file)
            
            issues = list(result['issues'])
            if metadata and image_id not in metadata_ids:
                issues.append(f"Không có metadata cho ảnh '{image_id}'")
            
            ok = result['ok'] and not issues
            all_ok = all_ok and ok
            
            per_image.append({
                'image': img_file,
                'image_id': image_id,
                'ok': ok,
                'issues': issues,
                'info': result['info'],
            })
        
        # Ảnh có GT nhưng không có ảnh tương ứng
        image_ids_in_dir = {self.extract_image_id(f) for f in self.list_image_files()}
        orphan_gt = [
            gt for gt in self.list_ground_truth_files()
            if self.extract_image_id(gt) not in image_ids_in_dir
        ]
        
        return {
            'total_images': integrity['total_images'],
            'total_gt': len(self.list_ground_truth_files()),
            'valid_pairs': integrity['valid_pairs'],
            'missing_gt': integrity['missing_gt'],
            'orphan_gt': orphan_gt,
            'size_mismatches': integrity['size_mismatches'],
            'errors': integrity['errors'],
            'metadata_entries': len(metadata),
            'per_image': per_image,
            'all_ok': all_ok and not orphan_gt,
        }


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
    
    # Kiểm tra toàn diện theo tiêu chí bàn giao
    full = loader.full_check()
    print("\n[Kiem tra toan dien]")
    print("Anh co metadata: {}".format(full['metadata_entries']))
    print("Tat ca anh dat yeu cau: {}".format(full['all_ok']))
    for item in full['per_image']:
        status = 'OK' if item['ok'] else 'LOI'
        print("  [{}] {} {}".format(status, item['image'], '; '.join(item['issues'])))
    if full['orphan_gt']:
        print("  GT khong co anh tuong ung: {}".format(full['orphan_gt']))


if __name__ == "__main__":
    main()
