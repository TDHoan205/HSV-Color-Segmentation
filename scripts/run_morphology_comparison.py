# -*- coding: utf-8 -*-
"""
Script: run_morphology_comparison.py
Chức năng: Thực nghiệm và sinh hình minh họa cho phần báo cáo Morphology
Phụ trách: Quốc Anh (Morphological Operations)

Cách chạy:
    python scripts/run_morphology_comparison.py

Kết quả:
    results/morphology_comparison/   - mask, số liệu CSV/JSON
    report/figures/morphology_*.png   - hình minh họa cho report/morphology.md
    report/morphology_results.json    - tham số + toàn bộ số liệu đo được

Nguyên tắc (theo Quy ước 4): script chỉ ĐỌC module của người khác,
không sửa logic bên trong. Mọi phép đo chạy trên dữ liệu thật của nhóm.
"""

import csv
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_loader import DataLoader
from src.evaluation import SegmentationEvaluator
from src.hsv_segment import HSVSegmenter
from src.median_filter import MedianFilter
from src.morphology import MorphologyOperator

sys.path.insert(0, str(ROOT / 'scripts'))
from make_report_figures import _with_label  # noqa: E402  (tiện ích gắn nhãn)

RESULTS_DIR = ROOT / 'results/morphology_comparison'
FIGURES_DIR = ROOT / 'report/figures'

# Cấu hình HSV dùng làm đầu vào cho mọi phép đo (ngưỡng "vừa" của nhóm)
HSV_CONFIG = {
    'color_name': 'Red',
    'hue_ranges': [[0, 10], [170, 180]],
    'saturation': [100, 255],
    'value': [100, 255],
}

# Cấu hình Median cố định để cô lập tác dụng của Morphology
MEDIAN_KERNEL = 5

# Các kernel hình thái so sánh
KERNEL_SIZES = [3, 5, 7]
KERNEL_SHAPES = ['rect', 'ellipse', 'cross']


# ----------------------------------------------------------------------
# 1. Thực nghiệm trên bộ dữ liệu thật
# ----------------------------------------------------------------------

def run_on_real_dataset():
    """
    Chạy pipeline HSV -> Median -> Morphology trên toàn bộ 10 ảnh thật,
    đo IoU/Accuracy trước và sau từng phép toán hình thái.

    Returns:
        list: danh sách dict kết quả theo từng ảnh
    """
    loader = DataLoader()
    evaluator = SegmentationEvaluator()
    segmenter = HSVSegmenter(HSV_CONFIG)
    median = MedianFilter(MEDIAN_KERNEL)

    rows = []
    for img_path, gt_path in loader.build_dataset():
        image, gt = loader.load_image_gt_pair(img_path, gt_path)
        mask_raw, _ = segmenter.segment(image)
        mask_median = median.filter(mask_raw)

        base = {
            'image': Path(img_path).name,
            'raw_px': int(np.count_nonzero(mask_raw)),
            'median_px': int(np.count_nonzero(mask_median)),
            'iou_raw': evaluator.compute_iou(mask_raw, gt),
            'iou_median': evaluator.compute_iou(mask_median, gt),
            'acc_raw': evaluator.compute_pixel_accuracy(mask_raw, gt),
            'acc_median': evaluator.compute_pixel_accuracy(mask_median, gt),
        }

        for size in KERNEL_SIZES:
            for shape in KERNEL_SHAPES:
                operator = MorphologyOperator(size, shape)
                for op_name, result in (
                    ('erode', operator.erode(mask_median)),
                    ('dilate', operator.dilate(mask_median)),
                    ('open', operator.open(mask_median)),
                    ('close', operator.close(mask_median)),
                ):
                    rows.append({
                        **base,
                        'kernel_size': size,
                        'kernel_shape': shape,
                        'operation': op_name,
                        'result_px': int(np.count_nonzero(result)),
                        'iou': evaluator.compute_iou(result, gt),
                        'acc': evaluator.compute_pixel_accuracy(result, gt),
                    })

    return rows


# ----------------------------------------------------------------------
# 2. Thực nghiệm trên fixture tổng hợp
# ----------------------------------------------------------------------

def run_on_fixture():
    """
    Đo tác dụng từng phép toán trên fixture có lỗ đen và đốm trắng rời rạch.
    Đây là nơi Morphology thực sự thể hiện tác dụng vì Ground Truth trong
    data/ được vẽ bằng hình học sạch nên không có nhiễu để xử lý.

    Returns:
        list: danh sách dict kết quả
    """
    from tests.fixtures.morphology import (
        HOLE_1, HOLE_2, SPECK_1, SPECK_2, SQUARE_A, SQUARE_B,
        make_noisy_mask,
    )

    mask = make_noisy_mask()
    rows = []

    for size in KERNEL_SIZES:
        for shape in KERNEL_SHAPES:
            operator = MorphologyOperator(size, shape)
            for op_name, result in (
                ('erode', operator.erode(mask)),
                ('dilate', operator.dilate(mask)),
                ('open', operator.open(mask)),
                ('close', operator.close(mask)),
            ):
                rows.append({
                    'kernel_size': size,
                    'kernel_shape': shape,
                    'operation': op_name,
                    'total_px': int(np.count_nonzero(result)),
                    'px_removed': int(np.count_nonzero(mask) - np.count_nonzero(result)),
                    'speck1_px': int(np.count_nonzero(result[SPECK_1])),
                    'speck2_px': int(np.count_nonzero(result[SPECK_2])),
                    'hole1_px': int(np.count_nonzero(result[HOLE_1])),
                    'hole2_px': int(np.count_nonzero(result[HOLE_2])),
                    'objectA_px': int(np.count_nonzero(result[SQUARE_A])),
                    'objectB_px': int(np.count_nonzero(result[SQUARE_B])),
                })

    return rows


# ----------------------------------------------------------------------
# 3. Sinh hình minh họa
# ----------------------------------------------------------------------

def figure_four_operations(fixture_mask):
    """
    Hình 1: 4 phép toán chính trên cùng một fixture, kernel 5x5 ellipse.
    Bố cục: hàng đầu là 4 phép toán, hàng dưới là chênh lệch so với gốc.
    """
    operator = MorphologyOperator(5, 'ellipse')
    panels = [
        ('Original (fixture)', fixture_mask),
        ('Erosion', operator.erode(fixture_mask)),
        ('Dilation', operator.dilate(fixture_mask)),
        ('Opening', operator.open(fixture_mask)),
        ('Closing', operator.close(fixture_mask)),
    ]

    cell_w, cell_h = 260, 260
    canvas = np.zeros((2 * cell_h, len(panels) * cell_w, 3), dtype=np.uint8)

    for idx, (label, mask) in enumerate(panels):
        cell = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        cell = cv2.resize(cell, (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST)
        canvas[0:cell_h, idx * cell_w:(idx + 1) * cell_w] = _with_label(cell, label)

        # Hàng dưới: vùng thay đổi so với gốc (đỏ = bị mất, xanh = được thêm)
        diff = np.zeros((*mask.shape, 3), dtype=np.uint8)
        diff[(mask == 0) & (fixture_mask > 0)] = (0, 0, 255)     # đỏ: mất pixel
        diff[(mask > 0) & (fixture_mask == 0)] = (0, 255, 0)     # xanh: thêm pixel
        diff[(mask > 0) & (fixture_mask > 0)] = (200, 200, 200)  # xám: giữ nguyên
        diff = cv2.resize(diff, (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST)
        canvas[cell_h:2 * cell_h, idx * cell_w:(idx + 1) * cell_w] = _with_label(
            diff, label + ' - diff')

    path = FIGURES_DIR / 'morphology_operations.png'
    cv2.imwrite(str(path), canvas)
    return path


def figure_kernel_comparison(fixture_mask):
    """
    Hình 2: so sánh kernel 3x3, 5x5, 7x7 cho Opening và Closing.
    """
    cell_w, cell_h = 260, 260
    cols = len(KERNEL_SIZES) * 2
    canvas = np.zeros((2 * cell_h, cols * cell_w, 3), dtype=np.uint8)

    for idx, size in enumerate(KERNEL_SIZES):
        operator = MorphologyOperator(size, 'ellipse')
        opening = operator.open(fixture_mask)
        closing = operator.close(fixture_mask)

        canvas[0:cell_h, idx * cell_w:(idx + 1) * cell_w] = _with_label(
            cv2.resize(cv2.cvtColor(opening, cv2.COLOR_GRAY2BGR),
                       (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST),
            f'Opening {size}x{size}')
        canvas[0:cell_h, (len(KERNEL_SIZES) + idx) * cell_w:(len(KERNEL_SIZES) + idx + 1) * cell_w] = _with_label(
            cv2.resize(cv2.cvtColor(closing, cv2.COLOR_GRAY2BGR),
                       (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST),
            f'Closing {size}x{size}')

        # Hàng dưới: diff so với gốc
        for col, result, name in (
            (idx, opening, 'Opening'),
            (len(KERNEL_SIZES) + idx, closing, 'Closing'),
        ):
            diff = np.zeros((*result.shape, 3), dtype=np.uint8)
            diff[(result == 0) & (fixture_mask > 0)] = (0, 0, 255)
            diff[(result > 0) & (fixture_mask == 0)] = (0, 255, 0)
            diff[(result > 0) & (fixture_mask > 0)] = (200, 200, 200)
            diff = cv2.resize(diff, (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST)
            canvas[cell_h:2 * cell_h, col * cell_w:(col + 1) * cell_w] = _with_label(
                diff, f'{name} {size}x{size} - diff')

    path = FIGURES_DIR / 'morphology_kernel_comparison.png'
    cv2.imwrite(str(path), canvas)
    return path


def figure_kernel_shapes(fixture_mask):
    """
    Hình 3: so sánh 3 hình kernel (rect, ellipse, cross) ở kernel 5x5.
    """
    cell_w, cell_h = 260, 260
    canvas = np.zeros((2 * cell_h, 6 * cell_w, 3), dtype=np.uint8)

    for idx, shape in enumerate(KERNEL_SHAPES):
        operator = MorphologyOperator(5, shape)
        opening = operator.open(fixture_mask)
        closing = operator.close(fixture_mask)

        canvas[0:cell_h, idx * cell_w:(idx + 1) * cell_w] = _with_label(
            cv2.resize(cv2.cvtColor(opening, cv2.COLOR_GRAY2BGR),
                       (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST),
            f'Opening {shape}')
        canvas[0:cell_h, (3 + idx) * cell_w:(4 + idx) * cell_w] = _with_label(
            cv2.resize(cv2.cvtColor(closing, cv2.COLOR_GRAY2BGR),
                       (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST),
            f'Closing {shape}')

        for col, result, name in (
            (idx, opening, 'Opening'),
            (3 + idx, closing, 'Closing'),
        ):
            diff = np.zeros((*result.shape, 3), dtype=np.uint8)
            diff[(result == 0) & (fixture_mask > 0)] = (0, 0, 255)
            diff[(result > 0) & (fixture_mask == 0)] = (0, 255, 0)
            diff[(result > 0) & (fixture_mask > 0)] = (200, 200, 200)
            diff = cv2.resize(diff, (cell_w, cell_h - 26), interpolation=cv2.INTER_NEAREST)
            canvas[cell_h:2 * cell_h, col * cell_w:(col + 1) * cell_w] = _with_label(
                diff, f'{name} {shape} - diff')

    path = FIGURES_DIR / 'morphology_kernel_shapes.png'
    cv2.imwrite(str(path), canvas)
    return path


def figure_real_dataset_effect(loader):
    """
    Hình 4: tác dụng thực tế của Closing trên bộ dữ liệu thật.
    Mỗi hàng là một ảnh: input, mask sau Median, mask sau Closing.
    """
    evaluator = SegmentationEvaluator()
    segmenter = HSVSegmenter(HSV_CONFIG)
    median = MedianFilter(MEDIAN_KERNEL)

    picks = [
        'img_01_red_circle_light_bg.jpg',
        'img_03_red_triangle_shadow.jpg',
        'img_06_red_on_pink_bg.jpg',
        'img_10_red_noisy_dark_bg.jpg',
    ]
    available = set(loader.list_image_files())
    picks = [p for p in picks if p in available]

    cell_w, cell_h = 320, 240
    canvas = np.zeros((len(picks) * cell_h, 3 * cell_w, 3), dtype=np.uint8)
    operator = MorphologyOperator(5, 'ellipse')

    for r, img_file in enumerate(picks):
        img_path = os.path.join(loader.images_dir, img_file)
        image, gt = loader.load_image_gt_pair(img_path, loader.get_gt_path(img_path))
        mask_raw, _ = segmenter.segment(image)
        mask_median = median.filter(mask_raw)
        mask_closed = operator.close(mask_median)

        iou_m = evaluator.compute_iou(mask_median, gt)
        iou_c = evaluator.compute_iou(mask_closed, gt)

        canvas[r * cell_h:(r + 1) * cell_h, 0:cell_w] = _with_label(
            cv2.resize(image, (cell_w, cell_h - 26)), f'INPUT {img_file[:7]}')
        canvas[r * cell_h:(r + 1) * cell_h, cell_w:2 * cell_w] = _with_label(
            cv2.resize(mask_median, (cell_w, cell_h - 26)),
            f'AFTER MEDIAN IoU={iou_m:.4f}')
        canvas[r * cell_h:(r + 1) * cell_h, 2 * cell_w:3 * cell_w] = _with_label(
            cv2.resize(mask_closed, (cell_w, cell_h - 26)),
            f'AFTER CLOSING IoU={iou_c:.4f}')

    path = FIGURES_DIR / 'morphology_real_dataset.png'
    cv2.imwrite(str(path), canvas)
    return path


# ----------------------------------------------------------------------
# 4. Hàm chính
# ----------------------------------------------------------------------

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    loader = DataLoader()

    print('=== THUC NGHIEM MORPHOLOGY ===')
    print('\n[1/4] Chay tren bo du lieu that...')
    real_rows = run_on_real_dataset()
    print(f'  {len(real_rows)} phep do tren {len(loader.build_dataset())} anh')

    print('[2/4] Chay tren fixture tong hop...')
    fixture_rows = run_on_fixture()
    print(f'  {len(fixture_rows)} phep do tren fixture')

    # Lưu CSV
    for name, rows in (('real_dataset.csv', real_rows), ('fixture.csv', fixture_rows)):
        if rows:
            path = RESULTS_DIR / name
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            print(f'  -> {path}')

    # Sinh hình
    print('[3/4] Sinh hinh minh hoa...')
    from tests.fixtures.morphology import make_noisy_mask
    fixture_mask = make_noisy_mask()

    figures = [
        figure_four_operations(fixture_mask),
        figure_kernel_comparison(fixture_mask),
        figure_kernel_shapes(fixture_mask),
        figure_real_dataset_effect(loader),
    ]
    for path in figures:
        print(f'  -> {path}')

    # Tổng hợp số liệu cho báo cáo
    print('[4/4] Tong hop so lieu...')
    summary = build_summary(real_rows, fixture_rows)
    (ROOT / 'report/morphology_results.json').write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print('\n--- KET QUA TREN BO DU LIEU THAT ---')
    print_summary(real_rows)

    print('\n--- KET QUA TREN FIXTURE ---')
    print_fixture_summary(fixture_rows)


def build_summary(real_rows, fixture_rows):
    """Tổng hợp số liệu để lưu vào report/morphology_results.json."""
    evaluator = SegmentationEvaluator()

    # Tác dụng trung bình của từng phép toán (kernel 5x5 ellipse) trên dữ liệu thật
    per_op = {}
    for op in ('erode', 'dilate', 'open', 'close'):
        subset = [r for r in real_rows
                  if r['operation'] == op and r['kernel_size'] == 5
                  and r['kernel_shape'] == 'ellipse']
        if subset:
            per_op[op] = {
                'mean_iou': float(np.mean([r['iou'] for r in subset])),
                'mean_acc': float(np.mean([r['acc'] for r in subset])),
                'mean_px_change': float(np.mean([r['result_px'] - r['median_px'] for r in subset])),
                'images_improved': sum(1 for r in subset if r['iou'] > r['iou_median']),
                'images_worsened': sum(1 for r in subset if r['iou'] < r['iou_median']),
                'images_unchanged': sum(1 for r in subset if r['iou'] == r['iou_median']),
            }

    return {
        'stage': 'Morphology after HSV + Median',
        'versions': {'opencv': cv2.__version__, 'numpy': np.__version__},
        'hsv_config': HSV_CONFIG,
        'median_kernel': MEDIAN_KERNEL,
        'kernel_sizes': KERNEL_SIZES,
        'kernel_shapes': KERNEL_SHAPES,
        'real_dataset': {
            'image_count': len({r['image'] for r in real_rows}),
            'baseline_mean_iou_raw': float(np.mean([r['iou_raw'] for r in real_rows])),
            'baseline_mean_iou_median': float(np.mean([r['iou_median'] for r in real_rows])),
            'per_operation_kernel5_ellipse': per_op,
        },
        'fixture': {
            'note': 'Fixture tong hop co lo den 3x3 va dot trang 4x4',
            'rows': fixture_rows,
        },
    }


def print_summary(real_rows):
    """In bảng tổng kết trên dữ liệu thật."""
    images = sorted({r['image'] for r in real_rows})
    subset = [r for r in real_rows if r['kernel_size'] == 5
              and r['kernel_shape'] == 'ellipse' and r['operation'] == 'close']

    print(f"{'Anh':<38} {'IoU raw':>9} {'IoU med':>9} {'IoU close':>10} {'Do lech':>9}")
    for img in images:
        row = next(r for r in subset if r['image'] == img)
        delta = row['iou'] - row['iou_median']
        print(f"{img:<38} {row['iou_raw']:>9.4f} {row['iou_median']:>9.4f} "
              f"{row['iou']:>10.4f} {delta:>+9.4f}")

    print(f"{'TRUNG BINH':<38} "
          f"{np.mean([r['iou_raw'] for r in subset]):>9.4f} "
          f"{np.mean([r['iou_median'] for r in subset]):>9.4f} "
          f"{np.mean([r['iou'] for r in subset]):>10.4f} "
          f"{np.mean([r['iou'] - r['iou_median'] for r in subset]):>+9.4f}")


def print_fixture_summary(fixture_rows):
    """In bảng tổng kết trên fixture."""
    print(f"{'Shape':<9} {'K':>3} {'op':<8} {'Tong px':>9} {'Loai bo':>9} {'Dot con':>9} {'Lo con':>8}")
    for row in fixture_rows:
        if row['kernel_shape'] != 'ellipse':
            continue
        print(f"{row['kernel_shape']:<9} {row['kernel_size']:>3} {row['operation']:<8} "
              f"{row['total_px']:>9} {row['px_removed']:>+9} "
              f"{row['speck1_px']:>9} {row['hole1_px']:>8}")


if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
