"""Reproduce raw HSV experiments only; leave other pipeline stages untouched.

Run from any directory: python scripts/run_hsv_comparison.py
Outputs: results/hsv_dataset_comparison and report/figures/hsv_*.png.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.hsv_segment import HSVSegmenter
from src.evaluation import SegmentationEvaluator

CONFIGS = {
    'narrow': {'color_name': 'Red', 'hue_ranges': [[0, 5], [175, 179]],
               'saturation': [150, 255], 'value': [150, 255]},
    'medium': {'color_name': 'Red', 'hue_ranges': [[0, 10], [170, 179]],
               'saturation': [100, 255], 'value': [100, 255]},
    'wide': {'color_name': 'Red', 'hue_ranges': [[0, 15], [165, 179]],
             'saturation': [50, 255], 'value': [50, 255]},
}


def save_image(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f'Cannot write {path}')


def panel(image, label):
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    thumb = cv2.resize(image, (240, 180), interpolation=cv2.INTER_NEAREST)
    result = np.full((210, 240, 3), 255, np.uint8)
    result[30:] = thumb
    cv2.putText(result, label, (8, 21), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return result


def theory_figure(figures):
    figure = np.full((460, 900, 3), 255, np.uint8)
    for i, (name, color, rgb, bgr) in enumerate([
        ('Red', (0, 0, 255), '(255,0,0)', '(0,0,255)'),
        ('Green', (0, 255, 0), '(0,255,0)', '(0,255,0)'),
        ('Blue', (255, 0, 0), '(0,0,255)', '(255,0,0)')]):
        x = i * 300
        figure[40:105, x+15:x+285] = color
        for y, text in [(25, name), (128, 'RGB ' + rgb), (151, 'BGR ' + bgr)]:
            cv2.putText(figure, text, (x+15, y), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 1)
    for row, (label, channel) in enumerate([('H: 0..179 (S=V=255)', 0),
                                           ('S: 0..255 (H=0,V=255)', 1),
                                           ('V: 0..255 (H=0,S=255)', 2)]):
        hsv = np.zeros((35, 870, 3), np.uint8)
        hsv[:] = (0, 255, 255)
        hsv[:, :, channel] = np.linspace(0, 179 if channel == 0 else 255, 870).astype(np.uint8)
        y = 180 + row * 90
        cv2.putText(figure, label, (15, y), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 0), 1)
        figure[y+10:y+45, 15:885] = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    save_image(figures / 'hsv_theory.png', figure)


def main():
    out = ROOT / 'results/hsv_dataset_comparison'
    figures = ROOT / 'report/figures'
    out.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    (out / 'configs.json').write_text(json.dumps(CONFIGS, indent=2), encoding='utf-8')
    rows, manifest, comparisons = [], [], {}
    evaluator = SegmentationEvaluator()
    for image_path in sorted((ROOT / 'data/images').glob('*.jpg')):
        gt_path = ROOT / 'data/ground_truth' / (image_path.stem + '.png')
        image = cv2.imread(str(image_path))
        gt = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
        if image is None or gt is None or gt.shape != image.shape[:2]:
            raise ValueError(f'Invalid image/GT pair: {image_path.name}')
        manifest.append({'image': image_path.relative_to(ROOT).as_posix(),
                         'gt': gt_path.relative_to(ROOT).as_posix(),
                         'image_sha256': hashlib.sha256(image_path.read_bytes()).hexdigest(),
                         'gt_sha256': hashlib.sha256(gt_path.read_bytes()).hexdigest()})
        panels = [panel(image, image_path.stem[:6] + ' input'), panel(gt, 'Ground truth')]
        for name, config in CONFIGS.items():
            mask, _ = HSVSegmenter(config).segment(image)
            metrics = evaluator.compute_metrics(mask, gt)
            rows.append({'image': image_path.name, 'config': name,
                         'selected_pixels': int(np.count_nonzero(mask)),
                         'total_pixels': int(mask.size), **metrics})
            save_image(out / image_path.stem / f'mask_{name}.png', mask)
            panels.append(panel(mask, name))
        comparisons[image_path.stem] = np.hstack(panels)
        save_image(out / image_path.stem / 'comparison.png', comparisons[image_path.stem])
    if not rows:
        raise ValueError('No input JPG images found')
    with (out / 'metrics.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    averages = {name: {key: float(np.mean([r[key] for r in rows if r['config'] == name]))
                       for key in ['pixel_accuracy', 'iou', 'precision', 'recall', 'f1']}
                for name in CONFIGS}
    summary = {'dataset': 'Existing AQuan dataset; see scripts/generate_dataset.py for generation',
               'image_count': len(manifest), 'stage': 'raw HSV mask only',
               'versions': {'opencv': cv2.__version__, 'numpy': np.__version__},
               'configs': CONFIGS, 'macro_average': averages, 'inputs': manifest}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    # Preserve exact configurations and measured values with the report in Git.
    (ROOT / 'report/hsv_results.json').write_text(
        json.dumps({**summary, 'measurements': rows}, indent=2), encoding='utf-8')
    # Keep report illustrations versionable; results/ is ignored by the project.
    selected = [key for key in comparisons if key.startswith(('img_01', 'img_05', 'img_06', 'img_07', 'img_08'))]
    save_image(figures / 'hsv_comparison.png', np.vstack([comparisons[key] for key in selected]))
    theory_figure(figures)
    print(json.dumps({'image_count': len(manifest), 'macro_average': averages}, indent=2))


if __name__ == '__main__':
    main()
