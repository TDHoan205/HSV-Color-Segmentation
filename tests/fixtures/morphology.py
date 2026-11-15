# -*- coding: utf-8 -*-
"""
Module: fixtures/morphology.py
Chức năng: Sinh Mask kiểm thử cho module hình thái học
Phụ trách: Quốc Anh

Mục đích:
    Theo kế hoạch (Task 2): "Tạo Mask có vùng trắng rời rạc và lỗ đen nhỏ"
    để thấy rõ tác dụng của Opening (loại bỏ vùng trắng nhỏ) và
    Closing (lấp kín lỗ đen nhỏ).

    Theo checklist tích hợp mục 2: "TV2–TV4 dùng ảnh/Mask fixture tự tạo
    để code trước, không phải chờ dataset". Vì vậy fixture ở đây là
    hình học tổng hợp, hoàn toàn độc lập với bộ dữ liệu thật.

Quy ước:
- Mask 1 kênh, uint8, nền = 0, đối tượng = 255 (Quy ước 2 của nhóm)
- Fixture tất định: cùng seed -> cùng kết quả

Cấu trúc fixture chính (`make_noisy_mask`):
    - 2 hình vuông lớn (vùng đối tượng chính)
    - 2 lỗ đen 3x3 bên trong vật thể  -> Closing lấp được
    - 2 đốm trắng 4x4 rời rạch ngoài vật thể -> Opening loại được
"""

import cv2
import numpy as np


# Kích thước chuẩn của fixture
FIXTURE_HEIGHT = 120
FIXTURE_WIDTH = 120

# Tọa độ các thành phần trong fixture chính (hàng, cột)
SQUARE_A = (slice(20, 50), slice(20, 50))
SQUARE_B = (slice(70, 95), slice(70, 95))
HOLE_1 = (slice(26, 29), slice(26, 29))
HOLE_2 = (slice(36, 39), slice(36, 39))
SPECK_1 = (slice(8, 12), slice(8, 12))
SPECK_2 = (slice(100, 104), slice(100, 104))


def make_noisy_mask(height=FIXTURE_HEIGHT, width=FIXTURE_WIDTH):
    """
    Tạo Mask kiểm thử có vùng trắng rời rạc và lỗ đen nhỏ.

    Args:
        height: Chiều cao Mask
        width: Chiều rộng Mask

    Returns:
        mask: Mask (H, W) uint8, giá trị 0/255
    """
    mask = np.zeros((height, width), dtype=np.uint8)

    # 1. Vùng đối tượng chính: hai hình vuông
    mask[SQUARE_A] = 255
    mask[SQUARE_B] = 255

    # 2. Lỗ đen nhỏ BÊN TRONG vật thể -> Closing lấp kín được
    mask[HOLE_1] = 0
    mask[HOLE_2] = 0

    # 3. Đốm trắng nhỏ RỜI RẠCH ngoài vật thể -> Opening loại bỏ được
    mask[SPECK_1] = 255
    mask[SPECK_2] = 255

    return mask


def make_solid_mask(height=FIXTURE_HEIGHT, width=FIXTURE_WIDTH):
    """
    Tạo Mask "sạch": chỉ có vùng đối tượng, không lỗ đen, không đốm lạc lõng.

    Dùng để chứng minh phép toán hình thái học không làm thay đổi gì
    trên một Mask vốn đã hoàn hảo.

    Args:
        height: Chiều cao Mask
        width: Chiều rộng Mask

    Returns:
        mask: Mask (H, W) uint8, giá trị 0/255
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[SQUARE_A] = 255
    mask[SQUARE_B] = 255
    return mask


def make_empty_mask(height=FIXTURE_HEIGHT, width=FIXTURE_WIDTH):
    """
    Tạo Mask hoàn toàn nền (không có pixel đối tượng).

    Dùng để kiểm thử trường hợp biên: phép toán trên Mask rỗng.

    Args:
        height: Chiều cao Mask
        width: Chiều rộng Mask

    Returns:
        mask: Mask (H, W) uint8, toàn 0
    """
    return np.zeros((height, width), dtype=np.uint8)


def make_full_mask(height=FIXTURE_HEIGHT, width=FIXTURE_WIDTH):
    """
    Tạo Mask toàn trắng (mọi pixel đều là đối tượng).

    Dùng để kiểm thử trường hợp biên ngược lại với make_empty_mask.

    Args:
        height: Chiều cao Mask
        width: Chiều rộng Mask

    Returns:
        mask: Mask (H, W) uint8, toàn 255
    """
    return np.full((height, width), 255, dtype=np.uint8)


def make_thin_mask(height=FIXTURE_HEIGHT, width=FIXTURE_WIDTH):
    """
    Tạo Mask chứa vùng đối tượng mảnh (độ dày 1 px).

    Dùng để chứng minh hạn chế của kernel lớn: kernel 5x5 sẽ xóa hẳn
    vùng mảnh, còn kernel 3x3 thì chỉ làm mờ biên.

    Args:
        height: Chiều cao Mask
        width: Chiều rộng Mask

    Returns:
        mask: Mask (H, W) uint8, giá trị 0/255
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[60, 10:110] = 255   # đường ngang mảnh 1 px
    mask[10:110, 60] = 255   # đường dọc mảnh 1 px
    return mask


def save_fixtures(output_dir):
    """
    Lưu các fixture ra thư mục dưới dạng PNG để tiện xem trực quan
    và dùng lại trong báo cáo.

    Args:
        output_dir: Thư mục đích (sẽ được tạo nếu chưa có)

    Returns:
        list: Danh sách đường dẫn file đã ghi
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    fixtures = {
        'fixture_noisy.png': make_noisy_mask(),
        'fixture_solid.png': make_solid_mask(),
        'fixture_thin.png': make_thin_mask(),
        'fixture_empty.png': make_empty_mask(),
        'fixture_full.png': make_full_mask(),
    }

    written = []
    for name, mask in fixtures.items():
        path = os.path.join(output_dir, name)
        if not cv2.imwrite(path, mask):
            raise RuntimeError(f'Không ghi được fixture: {path}')
        written.append(path)

    return written


def main():
    """Hàm test: in thông tin fixture và tạo file mẫu."""
    import os
    import sys

    if sys.stdout.encoding != 'utf-8':
        sys.stdout = sys.stdout.reconfigure(encoding='utf-8')

    mask = make_noisy_mask()
    print('=== FIXTURE MORPHOLOGY ===')
    print(f'Shape: {mask.shape}, dtype: {mask.dtype}')
    print(f'Giá trị: {np.unique(mask).tolist()}')
    print(f'Tổng pixel trắng: {np.count_nonzero(mask)}')
    print(f'  - Vùng đối tượng chính: {np.count_nonzero(mask[SQUARE_A]) + np.count_nonzero(mask[SQUARE_B])}')
    print(f'  - Lỗ đen (phải lấp): {np.count_nonzero(mask[HOLE_1]) + np.count_nonzero(mask[HOLE_2])}')
    print(f'  - Đốm trắng rời rạc (phải loại): {np.count_nonzero(mask[SPECK_1]) + np.count_nonzero(mask[SPECK_2])}')

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'morphology', 'output')
    written = save_fixtures(out_dir)
    print(f'\nĐã lưu {len(written)} fixture vào: {out_dir}')

if __name__ == '__main__':
    main()
