"""Reproduce the Median Filter experiments; other pipeline stages stay untouched.

Run from any directory: python scripts/run_median_comparison.py
Outputs: results/median_comparison/ (masks, comparison strips, metrics.csv,
summary.json) and report/figures/median_comparison.png for the report.
"""
import csv
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation import SegmentationEvaluator
from src.hsv_segment import HSVSegmenter
from src.median_filter import apply_median_filter

#: Các kích thước kernel được so sánh trong báo cáo.
KERNEL_SIZES = (3, 5, 7)

#: Ngưỡng HSV dùng để tạo mask thô (giữ nguyên ngưỡng mặc định của nhóm).
HSV_CONFIG = {
    'color_name': 'Red',
    'hue_ranges': [[0, 10], [170, 180]],
    'saturation': [100, 255],
    'value': [100, 255],
}

#: Số lần lặp khi đo thời gian xử lý (để giảm ảnh hưởng của nhiễu hệ thống).
TIMING_REPEATS = 20

#: Ảnh dùng để minh họa trong báo cáo.
FIGURE_IMAGES = ('img_01_red_circle_light_bg', 'img_05_red_on_orange_bg',
                 'img_09_red_gradient_light', 'img_10_red_noisy_dark_bg')

#: Các trường hợp tổng hợp trong tests/fixtures/median.
FIXTURE_CASES = (
    ('noisy_salt_pepper_3x3', 'expected_clean_3x3'),
    ('dense_noise_clusters', 'expected_clean_dense'),
)


def save_image(path, image):
    """Ghi ảnh ra đĩa, tạo thư mục nếu chưa có."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f'Cannot write {path}')


def panel(mask, label):
    """Tạo một ô 240x210 có nhãn phía trên, hiển thị mask dạng BGR."""
    if mask.ndim == 2:
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    thumb = cv2.resize(mask, (240, 180), interpolation=cv2.INTER_NEAREST)
    result = np.full((210, 240, 3), 255, np.uint8)
    result[30:] = thumb
    cv2.putText(result, label, (8, 21), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return result


def compare_masks(mask_raw, filtered_masks):
    """
    Ghép ngang: Mask thô | Kernel 3x3 | Kernel 5x5 | Kernel 7x7.

    Args:
        mask_raw: Mask thô (H, W) uint8.
        filtered_masks: Dict {kernel_size: mask_median}.

    Returns:
        np.ndarray: Ảnh BGR ghép ngang.
    """
    panels = [panel(mask_raw, 'Raw mask')]
    for kernel_size in sorted(filtered_masks):
        panels.append(panel(filtered_masks[kernel_size],
                             f'Kernel {kernel_size}x{kernel_size}'))
    return np.hstack(panels)


def _measure_time(mask_raw, kernel_size):
    """Đo thời gian lọc trung bình theo TIMING_REPEATS lần lặp (ms)."""
    start = time.perf_counter()
    for _ in range(TIMING_REPEATS):
        apply_median_filter(mask_raw, kernel_size)
    return (time.perf_counter() - start) * 1000.0 / TIMING_REPEATS


def _evaluate_case(mask_raw, gt, evaluator):
    """Tính toàn bộ số liệu cho một mask thô và các kernel 3x3, 5x5, 7x7."""
    rows = []
    filtered_masks = {}
    for kernel_size in KERNEL_SIZES:
        filtered = apply_median_filter(mask_raw, kernel_size)
        filtered_masks[kernel_size] = filtered

        metrics = evaluator.compute_metrics(filtered, gt)
        changed = int(np.count_nonzero(filtered != mask_raw))
        noise_remaining = int(np.count_nonzero((filtered == 255) & (gt == 0)))

        rows.append({
            'kernel_size': kernel_size,
            'raw_object_pixels': int(np.count_nonzero(mask_raw)),
            'filtered_object_pixels': int(np.count_nonzero(filtered)),
            'changed_pixels_vs_raw': changed,
            'changed_ratio_vs_raw': round(changed / float(mask_raw.size), 6),
            'noise_pixels_remaining': noise_remaining,
            'false_positive_pixels': metrics['FP'],
            'false_negative_pixels': metrics['FN'],
            'pixel_accuracy': metrics['pixel_accuracy'],
            'iou': metrics['iou'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1': metrics['f1'],
            'processing_ms': round(_measure_time(mask_raw, kernel_size), 4),
        })
    return rows, filtered_masks


def run_comparison(image_paths=None, output_dir=None, write_figure=True,
                   include_fixtures=True):
    """
    Chạy thực nghiệm Median Filter trên các ảnh có Ground Truth.

    Args:
        image_paths: Danh sách đường dẫn ảnh đầu vào. Mặc định là toàn bộ
            ảnh JPG trong `data/images/` có Ground Truth tương ứng.
        output_dir: Thư mục kết quả. Mặc định `results/median_comparison`.
        write_figure: Có ghi thêm hình tổng hợp vào `report/figures/` hay không.
        include_fixtures: Có chạy thêm các trường hợp tổng hợp trong
            `tests/fixtures/median/` hay không.

    Returns:
        dict: {'rows': [...], 'summary': {...}}
    """
    output_dir = Path(output_dir) if output_dir else ROOT / 'results/median_comparison'
    output_dir.mkdir(parents=True, exist_ok=True)

    if image_paths is None:
        # Chỉ dùng ảnh có Ground Truth tương ứng (giống DataLoader.build_dataset).
        candidates = sorted((ROOT / 'data/images').glob('*.jpg'))
        image_paths = [
            path for path in candidates
            if (ROOT / 'data/ground_truth' / (path.stem + '.png')).exists()
        ]
    else:
        image_paths = [Path(p) for p in image_paths]

    segmenter = HSVSegmenter(HSV_CONFIG)
    evaluator = SegmentationEvaluator()
    rows = []
    comparisons = {}

    for image_path in image_paths:
        gt_path = ROOT / 'data/ground_truth' / (image_path.stem + '.png')
        image = cv2.imread(str(image_path))
        gt = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
        if image is None or gt is None or gt.shape != image.shape[:2]:
            raise ValueError(f'Invalid image/GT pair: {image_path.name}')

        mask_raw, _ = segmenter.segment(image)
        case_rows, filtered_masks = _evaluate_case(mask_raw, gt, evaluator)
        for row in case_rows:
            rows.append({'source': 'dataset', 'image': image_path.name, **row})
            save_image(output_dir / image_path.stem / f"mask_k{row['kernel_size']}.png",
                       filtered_masks[row['kernel_size']])

        save_image(output_dir / image_path.stem / 'mask_raw.png', mask_raw)
        comparison = compare_masks(mask_raw, filtered_masks)
        comparisons[image_path.stem] = comparison
        save_image(output_dir / image_path.stem / 'comparison.png', comparison)

    fixture_comparisons = []
    if include_fixtures:
        fixture_dir = ROOT / 'tests/fixtures/median'
        fixture_comparisons = []
        for mask_name, gt_name in FIXTURE_CASES:
            mask_path = fixture_dir / f'{mask_name}.png'
            gt_path = fixture_dir / f'{gt_name}.png'
            if not mask_path.exists() or not gt_path.exists():
                continue
            mask_raw = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            gt = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
            if mask_raw is None or gt is None:
                continue

            case_rows, filtered_masks = _evaluate_case(mask_raw, gt, evaluator)
            for row in case_rows:
                rows.append({'source': 'fixture', 'image': mask_name, **row})
                save_image(output_dir / 'fixtures' / mask_name
                           / f"mask_k{row['kernel_size']}.png",
                           filtered_masks[row['kernel_size']])

            save_image(output_dir / 'fixtures' / mask_name / 'mask_raw.png', mask_raw)
            comparison = compare_masks(mask_raw, filtered_masks)
            save_image(output_dir / 'fixtures' / mask_name / 'comparison.png', comparison)
            fixture_comparisons.append(comparison)

    if not rows:
        raise ValueError('No input JPG images found')

    with (output_dir / 'metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    metric_keys = ('pixel_accuracy', 'iou', 'precision', 'recall', 'f1',
                    'changed_ratio_vs_raw', 'processing_ms',
                    'noise_pixels_remaining', 'false_negative_pixels')

    macro_average = {}
    for source in sorted({row['source'] for row in rows}):
        for kernel_size in KERNEL_SIZES:
            subset = [row for row in rows
                      if row['kernel_size'] == kernel_size and row['source'] == source]
            macro_average.setdefault(source, {})[f'{kernel_size}x{kernel_size}'] = {
                key: float(np.mean([row[key] for row in subset]))
                for key in metric_keys
            }

    per_image = {}
    for row in rows:
        per_image.setdefault(f"{row['source']}:{row['image']}", {})[
            f"{row['kernel_size']}x{row['kernel_size']}"] = {
                'iou': row['iou'],
                'pixel_accuracy': row['pixel_accuracy'],
                'noise_pixels_remaining': row['noise_pixels_remaining'],
                'changed_pixels_vs_raw': row['changed_pixels_vs_raw'],
                'processing_ms': row['processing_ms'],
            }

    summary = {
        'stage': 'HSV raw mask -> Median Filter (3x3 / 5x5 / 7x7)',
        'hsv_config': HSV_CONFIG,
        'kernel_sizes': list(KERNEL_SIZES),
        'image_count': len({row['image'] for row in rows if row['source'] == 'dataset'}),
        'versions': {'opencv': cv2.__version__, 'numpy': np.__version__},
        'timing_repeats': TIMING_REPEATS,
        'macro_average': macro_average,
        'per_case': per_image,
        'measurements': rows,
    }
    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

    if write_figure:
        selected = [key for key in comparisons if key in FIGURE_IMAGES]
        if selected:
            figures = ROOT / 'report/figures'
            save_image(figures / 'median_comparison.png',
                       np.vstack([comparisons[key] for key in selected]))
        if fixture_comparisons:
            figures = ROOT / 'report/figures'
            save_image(figures / 'median_fixtures.png',
                       np.vstack(fixture_comparisons))

    return {'rows': rows, 'summary': summary}


def main():
    result = run_comparison()
    print(json.dumps(result['summary']['macro_average'], indent=2))
    print(f"Ket qua: {ROOT / 'results/median_comparison'}")


if __name__ == '__main__':
    main()
