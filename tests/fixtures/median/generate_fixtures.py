# -*- coding: utf-8 -*-
"""
Sinh bộ ảnh kiểm thử cho module Median Filter (Anh Tuấn).

Chạy từ thư mục dự án:
    python tests/fixtures/median/generate_fixtures.py

Kết quả (tất định, seed cố định cho từng fixture):
    tests/fixtures/median/noisy_salt_pepper_3x3.png  - mask 0/255 có nhiễu muối tiêu
    tests/fixtures/median/expected_clean_3x3.png    - mask sạch tương ứng
    tests/fixtures/median/dense_noise_clusters.png   - cụm nhiễu dày đặc
    tests/fixtures/median/expected_clean_dense.png   - vùng đối tượng lý tưởng
    tests/fixtures/median/fine_details_edges.png     - chi tiết mảnh, góc nhọn

Mọi ảnh đều là grayscale 1 kênh, dtype uint8, chỉ chứa giá trị 0 và 255.
"""

import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.median_filter import apply_median_filter  # noqa: E402

#: Seed gốc. Mỗi fixture dùng seed riêng để thứ tự sinh không ảnh hưởng kết quả.
SEED = 2024
SEED_SALT_PEPPER = SEED + 1
SEED_DENSE = SEED + 2

IMAGE_SIZE = 120


def _disk_mask(center, radius, size=IMAGE_SIZE):
    """Tạo mask hình tròn đặc (255) trên nền đen (0)."""
    mask = np.zeros((size, size), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, thickness=-1)
    return mask


def _erode(mask, size=3):
    """Erosion với kernel vuông (mặc nạn 1) để lấy vùng 'an toàn'."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
    return cv2.erode(mask, kernel)


def _save(name, mask):
    """Ghi mask ra file PNG (grayscale 1 kênh)."""
    path = os.path.join(HERE, name)
    if not cv2.imwrite(path, mask):
        raise RuntimeError(f"Khong ghi duoc file: {path}")
    print(f"  [OK] {name}  shape={mask.shape} dtype={mask.dtype} "
          f"gia tri={np.unique(mask).tolist()}")
    return path


def build_salt_pepper(rng):
    """
    Sinh cặp 'ảnh nhiễu muối tiêu' + 'ảnh sạch'.

    Nhiễu muối (255 đơn lẻ trên nền) và nhiễu tiêu (0 đơn lẻ trong vùng 255)
    được đặt ở vị trí mà cửa sổ 3x3 quanh chúng chỉ chứa toàn nền hoặc toàn
    vùng đối tượng. Vì vậy kernel 3x3 phải khử sạch hoàn toàn và khớp 100%
    với ảnh sạch.

    Lưu ý: bộ lọc trung vị làm bo tròn mọi biên cong (biên tròn của hình tròn
    bị lùi khoảng 1 pixel). Do đó ảnh "sạch" tham chiếu là ảnh hình học lý
    tưởng ĐÃ đi qua bộ lọc 3x3 - đây chính là ảnh mà bộ lọc phải khôi phục
    lại từ ảnh nhiễu.
    """
    ideal = _disk_mask((IMAGE_SIZE // 2, IMAGE_SIZE // 2), 38)
    clean = apply_median_filter(ideal, 3)

    # Vùng an toàn để đặt nhiễu: vùng lân cận 5x5 phải toàn nền (nhiễu muối)
    # hoặc toàn đối tượng (nhiễu tiêu). Điều kiện 5x5 đảm bảo điểm nhiễu chỉ
    # ảnh hưởng tới chính nó chứ không làm đổi kết quả của các pixel lân cận.
    background = (ideal == 0).astype(np.uint8) * 255
    safe_background = _erode(background, 5)
    safe_object = _erode(ideal, 5)

    salt_positions = _sample_positions(rng, safe_background, count=40, min_distance=3)
    pepper_positions = _sample_positions(rng, safe_object, count=25, min_distance=3)

    noisy = ideal.copy()
    for position in salt_positions:
        noisy[position] = 255
    for position in pepper_positions:
        noisy[position] = 0

    return noisy, clean, len(salt_positions), len(pepper_positions)


def _sample_positions(rng, allowed_mask, count, min_distance):
    """
    Chọn ngẫu nhiên `count` vị trí có giá trị 255 trong `allowed_mask`,
    đảm bảo khoảng cách Euclidean giữa các vị trí >= min_distance.
    """
    candidates = np.argwhere(allowed_mask > 0)
    if candidates.size == 0:
        return []

    chosen = []
    min_distance_sq = min_distance ** 2
    order = rng.permutation(len(candidates))

    for index in order:
        y, x = candidates[index]
        if all((y - cy) ** 2 + (x - cx) ** 2 >= min_distance_sq for cy, cx in chosen):
            chosen.append((int(y), int(x)))
            if len(chosen) >= count:
                break

    return chosen


def build_dense_clusters(rng):
    """
    Sinh mask có cụm nhiễu dày đặc.

    Mỗi cụm nhiễu là 2 khối 2x2 đặt sát nhau, tạo thành vùng nhiễu 2x4. Vùng
    nhiễu như vậy SỐNG SOT với kernel 3x3 (cửa sổ 3x3 chứa 6 pixel trắng trên
    9 pixel) nhưng bị loại bỏ bởi kernel 5x5 (cửa sổ 5x5 chỉ chứa 8 pixel
    trắng trên 25 pixel). Các cụm cách nhau tối thiểu 10 pixel nên không thể
    chồng lấn thành vùng nhiễu lớn hơn.
    """
    ideal = _disk_mask((IMAGE_SIZE // 2, IMAGE_SIZE // 2), 38)
    noisy = ideal.copy()

    # Chỉ đặt nhiễu trên nền, cách vùng đối tượng tối thiểu 4 pixel.
    # Erosion 8x8 bảo đảm cả vùng nhiễu 2x4 (rộng 4 pixel) nằm trọn trên nền.
    background = (ideal == 0).astype(np.uint8) * 255
    safe_background = _erode(background, 8)

    candidates = np.argwhere(safe_background > 0)
    candidates = candidates[(candidates[:, 0] >= 6) & (candidates[:, 0] < IMAGE_SIZE - 6)
                            & (candidates[:, 1] >= 6) & (candidates[:, 1] < IMAGE_SIZE - 6)]
    order = rng.permutation(len(candidates))

    clusters = 0
    used = []
    for index in order:
        y, x = candidates[index]
        if any((y - uy) ** 2 + (x - ux) ** 2 < 100 for uy, ux in used):
            continue
        # Một cụm gồm 2 khối 2x2 đặt cạnh nhau -> vùng nhiễu 2x4.
        for dy in range(2):
            for dx in range(4):
                yy, xx = y + dy, x + dx
                if 0 <= yy < IMAGE_SIZE and 0 <= xx < IMAGE_SIZE:
                    noisy[yy, xx] = 255
        used.append((y, x))
        clusters += 1
        if clusters >= 18:
            break

    return noisy, ideal, clusters


def build_fine_details():
    """
    Sinh mask có chi tiết mảnh: đường thẳng 1-2 pixel, chữ thập mảnh và
    hình vuông nhỏ có góc nhọn.

    - Kernel 3x3 giữ gần như nguyên vẹn các đường 1 pixel.
    - Kernel 5x5/7x7 làm mờ hoặc xóa các đường mảnh và bo tròn các góc nhọn.
    """
    mask = np.zeros((IMAGE_SIZE, IMAGE_SIZE), dtype=np.uint8)

    # Đường thẳng 1 pixel (sẽ bị xóa khi kernel lớn).
    mask[20, 10:110] = 255
    mask[100, 10:110] = 255

    # Đường thẳng 2 pixel.
    mask[30:32, 10:110] = 255

    # Chữ thập mảnh.
    mask[45:85, 59:61] = 255
    mask[63:65, 30:95] = 255

    # Hình vuông nhỏ có góc nhọn (góc sẽ bị bo tròn khi tăng kernel).
    mask[75:95, 75:95] = 255

    # Đường chéo 1 pixel tạo góc nhọn 45 độ.
    for i in range(25):
        mask[95 + i, 20 + i] = 255

    # Đường chéo góc nhọn (tam giác) ở góc dưới bên phải.
    for i in range(30):
        mask[115 - i, 90 + i] = 255

    return mask


def main():
    print("=== SINH BO DU LIEU KIEM THU MEDIAN FILTER ===")

    # 1) Nhiễu muối tiêu + ảnh sạch
    noisy, clean, n_salt, n_pepper = build_salt_pepper(
        np.random.default_rng(SEED_SALT_PEPPER))
    filtered = apply_median_filter(noisy, 3)
    if not np.array_equal(filtered, clean):
        different = int(np.count_nonzero(filtered != clean))
        raise AssertionError(
            "Fixture 'noisy_salt_pepper_3x3' phai duoc loc sach 100% bang kernel 3x3, "
            f"hien con {different} pixel khac."
        )
    _save('noisy_salt_pepper_3x3.png', noisy)
    _save('expected_clean_3x3.png', clean)
    print(f"       -> {n_salt} diem muoi + {n_pepper} diem tieu; khop 100% voi anh sach")

    # 2) Cụm nhiễu dày đặc
    dense, dense_clean, n_clusters = build_dense_clusters(
        np.random.default_rng(SEED_DENSE))
    # Tập pixel nhiễu = pixel trắng trong ảnh nhiễu nhưng thuộc nền của ảnh sạch.
    noise_pixels = (dense == 255) & (dense_clean == 0)
    dense_3 = apply_median_filter(dense, 3)
    dense_5 = apply_median_filter(dense, 5)
    residual_3 = int(np.count_nonzero(noise_pixels & (dense_3 == 255)))
    residual_5 = int(np.count_nonzero(noise_pixels & (dense_5 == 255)))
    if residual_3 == 0:
        raise AssertionError("Kernel 3x3 phai con sot nhieu de minh hoa uu diem cua 5x5.")
    if residual_5 != 0:
        raise AssertionError(f"Kernel 5x5 phai loai het nhieu (con {residual_5} pixel).")
    _save('dense_noise_clusters.png', dense)
    _save('expected_clean_dense.png', dense_clean)
    print(f"       -> {n_clusters} cum nhieu 2x4; 3x3 con sot {residual_3} pixel, "
          f"5x5 con {residual_5} pixel")

    # 3) Chi tiết mảnh / góc nhọn
    fine = build_fine_details()
    change_3 = int(np.count_nonzero(apply_median_filter(fine, 3) != fine))
    change_5 = int(np.count_nonzero(apply_median_filter(fine, 5) != fine))
    change_7 = int(np.count_nonzero(apply_median_filter(fine, 7) != fine))
    if not (change_3 < change_5 < change_7):
        raise AssertionError(
            "So pixel bi thay doi phai tang dan theo kich thuoc kernel "
            f"(3x3={change_3}, 5x5={change_5}, 7x7={change_7})."
        )
    _save('fine_details_edges.png', fine)
    print(f"       -> pixel bi thay doi: 3x3={change_3}, 5x5={change_5}, 7x7={change_7}")

    print("HOAN TAT.")


if __name__ == '__main__':
    main()
