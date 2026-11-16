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


# ---------------------------------------------------------------------------
# Phase D: DataLoader theo manifest + validator GT thô (bổ sung, không đổi API cũ)
# ---------------------------------------------------------------------------
import hashlib

MANIFEST_SCHEMA_VERSION = 'dataset_manifest_v1'
MANIFEST_COLUMNS = [
    'schema_version', 'sample_id', 'image_id', 'image_path', 'gt_path', 'target_color_id',
    'data_type', 'source_id', 'license_status', 'annotation_method', 'annotation_version',
    'annotator', 'review_status', 'review_note', 'width', 'height', 'image_sha256', 'gt_sha256',
    'scenario', 'lighting', 'background', 'group_id', 'split', 'status', 'exclusion_reason',
    'next_action',
]
MANIFEST_STATUSES = ('approved', 'pending_annotation', 'invalid', 'excluded')
MANIFEST_SPLITS = ('tuning', 'final_test', 'synthetic_reference', 'none')
MANIFEST_DATA_TYPES = ('real', 'synthetic')
_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def file_sha256(path):
    """SHA-256 của file (hex)."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def validate_raw_gt(gt_path, expected_shape=None):
    """
    Validator GT thô: đọc nguyên trạng (không threshold, không resize, không đổi kênh).
    Yêu cầu: PNG, 1 kênh, uint8, giá trị chỉ {0, 255}, không rỗng, đúng (H, W) nếu có.

    Returns:
        dict: {'ok': bool, 'issues': [str], 'info': {...}}; không bao giờ tự sửa file.
    """
    issues, info = [], {}
    if not os.path.isfile(gt_path):
        return {'ok': False, 'issues': [f"GT không tồn tại: {gt_path}"], 'info': info}
    with open(gt_path, 'rb') as f:
        raw = f.read()
    if not raw.startswith(_PNG_SIGNATURE):
        issues.append("GT không phải file PNG")
    gt = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if gt is None:
        issues.append("Không giải mã được GT")
        return {'ok': False, 'issues': issues, 'info': info}
    info.update(shape=tuple(int(v) for v in gt.shape), dtype=str(gt.dtype))
    if gt.ndim != 2:
        issues.append(f"GT phải 1 kênh, nhận shape {gt.shape}")
    if gt.dtype != np.uint8:
        issues.append(f"GT phải uint8, nhận {gt.dtype}")
    values = [int(v) for v in np.unique(gt)]
    info['unique_values'] = values[:10]
    if not set(values) <= {0, 255}:
        issues.append(f"GT chỉ được chứa 0/255, nhận {values[:10]}")
    if gt.ndim == 2 and expected_shape is not None and gt.shape != tuple(expected_shape):
        issues.append(f"Kích thước GT {gt.shape} khác ảnh {tuple(expected_shape)}")
    if not np.any(gt):
        issues.append("GT rỗng (không có vùng đối tượng)")
    return {'ok': not issues, 'issues': issues, 'info': info}


def load_manifest(manifest_path='data/dataset_manifest.csv'):
    """Đọc manifest thành list dict (giữ nguyên chuỗi)."""
    with open(manifest_path, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = [dict(r) for r in reader]
    return header, rows


def validate_manifest(manifest_path='data/dataset_manifest.csv', root='.', check_hash=True):
    """
    Kiểm tra manifest. Không sửa gì; trả về toàn bộ lỗi tìm thấy.

    Returns:
        dict: {'ok', 'errors': [str], 'counts': {...}}
    """
    errors = []
    header, rows = load_manifest(manifest_path)
    if header != MANIFEST_COLUMNS:
        errors.append(f"Header manifest sai schema: {header}")
    seen_ids, seen_images, seen_gt = set(), set(), set()
    group_splits = {}
    for r in rows:
        sid = r.get('sample_id', '')
        where = f"[{sid}]"
        if r.get('schema_version') != MANIFEST_SCHEMA_VERSION:
            errors.append(f"{where} schema_version sai")
        if sid in seen_ids:
            errors.append(f"{where} sample_id trùng")
        seen_ids.add(sid)
        if r.get('status') not in MANIFEST_STATUSES:
            errors.append(f"{where} status không hợp lệ: {r.get('status')}")
        if r.get('split') not in MANIFEST_SPLITS:
            errors.append(f"{where} split không hợp lệ: {r.get('split')}")
        if r.get('data_type') not in MANIFEST_DATA_TYPES:
            errors.append(f"{where} data_type không hợp lệ: {r.get('data_type')}")
        img = r.get('image_path', '')
        if img in seen_images:
            errors.append(f"{where} image_path trùng: {img}")
        seen_images.add(img)
        img_abs = os.path.join(root, img)
        if not os.path.isfile(img_abs):
            errors.append(f"{where} thiếu ảnh: {img}")
        elif check_hash and file_sha256(img_abs) != r.get('image_sha256'):
            errors.append(f"{where} image_sha256 không khớp")
        status = r.get('status')
        if status == 'approved':
            gt = r.get('gt_path', '')
            if not gt:
                errors.append(f"{where} approved nhưng thiếu gt_path")
            else:
                if gt in seen_gt:
                    errors.append(f"{where} gt_path trùng: {gt}")
                seen_gt.add(gt)
                gt_abs = os.path.join(root, gt)
                if not os.path.isfile(gt_abs):
                    errors.append(f"{where} thiếu GT: {gt}")
                else:
                    if check_hash and file_sha256(gt_abs) != r.get('gt_sha256'):
                        errors.append(f"{where} gt_sha256 không khớp")
                    res = validate_raw_gt(gt_abs, (int(r['height']), int(r['width'])))
                    errors.extend(f"{where} {i}" for i in res['issues'])
            if r.get('split') == 'none':
                errors.append(f"{where} approved nhưng split=none")
            if r.get('data_type') == 'synthetic' and r.get('split') != 'synthetic_reference':
                errors.append(f"{where} dữ liệu tổng hợp phải ở split synthetic_reference")
            if r.get('data_type') == 'real' and r.get('split') == 'synthetic_reference':
                errors.append(f"{where} dữ liệu thật không được ở split synthetic_reference")
        else:
            if not r.get('exclusion_reason') or not r.get('next_action'):
                errors.append(f"{where} {status} thiếu exclusion_reason/next_action")
        gid = r.get('group_id', '')
        if gid:
            group_splits.setdefault(gid, set()).add(r.get('split'))
    for gid, splits in group_splits.items():
        if {'tuning', 'final_test'} <= splits:
            errors.append(f"Group {gid} nằm ở cả tuning và final_test (rò rỉ)")
    counts = {s: sum(1 for r in rows if r.get('status') == s) for s in MANIFEST_STATUSES}
    counts['rows'] = len(rows)
    return {'ok': not errors, 'errors': errors, 'counts': counts}


def build_dataset_from_manifest(manifest_path='data/dataset_manifest.csv', root='.',
                                split=None, status='approved', data_type=None,
                                target_color_id=None):
    """
    Dựng danh sách record theo manifest. Mặc định chỉ lấy mẫu `approved`.

    Returns:
        list[dict]: mỗi dict là một dòng manifest cộng 'image_abs' và 'gt_abs'.
    """
    _, rows = load_manifest(manifest_path)
    out = []
    for r in rows:
        if status is not None and r['status'] != status:
            continue
        if split is not None and r['split'] != split:
            continue
        if data_type is not None and r['data_type'] != data_type:
            continue
        if target_color_id is not None and r['target_color_id'] != target_color_id:
            continue
        rec = dict(r)
        rec['image_abs'] = os.path.join(root, r['image_path'])
        rec['gt_abs'] = os.path.join(root, r['gt_path']) if r['gt_path'] else ''
        out.append(rec)
    return out


def load_manifest_sample(record):
    """
    Nạp một record manifest: ảnh BGR và GT thô (không threshold). Raise ValueError nếu GT sai.
    """
    image = cv2.imread(record['image_abs'], cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Không đọc được ảnh: {record['image_abs']}")
    res = validate_raw_gt(record['gt_abs'], image.shape[:2])
    if not res['ok']:
        raise ValueError(f"GT không hợp lệ ({record['sample_id']}): {'; '.join(res['issues'])}")
    gt = cv2.imread(record['gt_abs'], cv2.IMREAD_UNCHANGED)
    return image, gt


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
