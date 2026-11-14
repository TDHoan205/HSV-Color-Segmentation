# -*- coding: utf-8 -*-
"""
Script: make_report_figures.py
Chức năng: Sinh các hình minh họa thật cho phần báo cáo dữ liệu (report/data.md)
Phụ trách: Anh Quân (Dữ liệu & Ground Truth)

Cách chạy:
    python scripts/make_report_figures.py
"""

import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DataLoader
from src.hsv_segment import HSVSegmenter
from src.evaluation import SegmentationEvaluator

OUTPUT_DIR = os.path.join('report', 'figures')


def _safe_text(text):
    """
    OpenCV putText không hỗ trợ Unicode nên nhãn hình chỉ dùng ASCII.
    Hàm này chuyển văn bản có dấu thành không dấu.
    """
    replacements = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    }
    out = []
    for ch in text:
        low = ch.lower()
        if low in replacements:
            out.append(replacements[low].upper() if ch.isupper() else replacements[low])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            out.append('?')
    return ''.join(out)


def _label_strip(width, text, height=26):
    """Tạo dải nhãn nền đen phía trên ảnh."""
    strip = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(strip, _safe_text(text), (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA)
    return strip


def _with_label(image, text):
    """Gắn nhãn lên trên ảnh (hỗ trợ ảnh xám 1 kênh)."""
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return np.vstack([_label_strip(image.shape[1], text), image])


def figure_dataset_overview(loader, metadata):
    """Lưới toàn bộ ảnh đầu vào kèm mã và tình huống."""
    files = loader.list_image_files()
    cols, rows = 5, 2
    cell_w, cell_h = 320, 240
    canvas = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)

    for idx, img_file in enumerate(files):
        image = loader.load_image(os.path.join(loader.images_dir, img_file))
        resized = cv2.resize(image, (cell_w, cell_h - 26))
        image_id = DataLoader.extract_image_id(img_file)
        scenario = next((r['scenario'] for r in metadata if r['image_id'] == image_id), '')
        cell = _with_label(resized, f"{image_id}  {scenario}")

        r, c = divmod(idx, cols)
        canvas[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w] = cell

    path = os.path.join(OUTPUT_DIR, 'dataset_overview.png')
    cv2.imwrite(path, canvas)
    return path


def figure_input_vs_gt(loader):
    """So sánh ảnh đầu vào và Ground Truth cho 4 ảnh tiêu biểu."""
    picks = [
        'img_01_red_circle_light_bg.jpg',
        'img_03_red_triangle_shadow.jpg',
        'img_04_red_multi_objects.jpg',
        'img_09_red_gradient_light.jpg',
    ]
    available = set(loader.list_image_files())
    picks = [p for p in picks if p in available]

    cell_w, cell_h = 400, 300
    rows = len(picks)
    canvas = np.zeros((rows * cell_h, 2 * cell_w, 3), dtype=np.uint8)

    for r, img_file in enumerate(picks):
        img_path = os.path.join(loader.images_dir, img_file)
        gt_path = loader.get_gt_path(img_path)
        image, gt = loader.load_image_gt_pair(img_path, gt_path)

        image_r = cv2.resize(image, (cell_w, cell_h - 26))
        gt_r = cv2.resize(gt, (cell_w, cell_h - 26))

        canvas[r * cell_h:(r + 1) * cell_h, 0:cell_w] = _with_label(image_r, f"INPUT  {img_file}")
        canvas[r * cell_h:(r + 1) * cell_h, cell_w:2 * cell_w] = _with_label(gt_r, f"GROUND TRUTH  {os.path.basename(gt_path)}")

    path = os.path.join(OUTPUT_DIR, 'input_vs_gt.png')
    cv2.imwrite(path, canvas)
    return path


def figure_hard_cases(loader):
    """Các tình huống khó: nền gần giống, ánh sáng yếu, cháy sáng, nhiễu."""
    hard = [
        'img_05_red_on_orange_bg.jpg',
        'img_06_red_on_pink_bg.jpg',
        'img_07_red_low_light.jpg',
        'img_08_red_overexposed.jpg',
        'img_10_red_noisy_dark_bg.jpg',
    ]
    available = set(loader.list_image_files())
    hard = [h for h in hard if h in available]

    cell_w, cell_h = 320, 240
    cols = len(hard)
    canvas = np.zeros((cell_h, cols * cell_w, 3), dtype=np.uint8)

    for c, img_file in enumerate(hard):
        image = loader.load_image(os.path.join(loader.images_dir, img_file))
        resized = cv2.resize(image, (cell_w, cell_h - 26))
        canvas[0:cell_h, c * cell_w:(c + 1) * cell_w] = _with_label(
            resized, DataLoader.extract_image_id(img_file))

    path = os.path.join(OUTPUT_DIR, 'hard_cases.png')
    cv2.imwrite(path, canvas)
    return path


def figure_hsv_histogram(loader):
    """Biểu đồ phân bố Hue của vùng đối tượng và vùng nền trên một ảnh tiêu biểu."""
    img_file = 'img_01_red_circle_light_bg.jpg'
    if img_file not in set(loader.list_image_files()):
        return None

    img_path = os.path.join(loader.images_dir, img_file)
    gt_path = loader.get_gt_path(img_path)
    image, gt = loader.load_image_gt_pair(img_path, gt_path)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    obj = gt > 0

    hist = np.zeros((256, 3), dtype=np.uint8)
    bins = np.linspace(0, 180, 181).astype(np.int32)

    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        obj_count = int(np.count_nonzero((h >= lo) & (h < hi) & obj))
        bg_count = int(np.count_nonzero((h >= lo) & (h < hi) & (~obj)))
        if obj_count > 0:
            hist[i, 2] = 255
        if bg_count > 0:
            hist[i, 1] = 255

    bar = cv2.applyColorMap(hist, cv2.COLORMAP_JET)
    bar = cv2.resize(bar, (900, 260), interpolation=cv2.INTER_NEAREST)

    strip = _label_strip(900, 'Phan bo Hue (xanh = nen, do = vung doi tuong) - img_01', 26)
    canvas = np.vstack([strip, bar])

    path = os.path.join(OUTPUT_DIR, 'hue_distribution.png')
    cv2.imwrite(path, canvas)
    return path


def figure_default_config_vs_gt(loader):
    """Chạy cấu hình HSV mặc định và so sánh với Ground Truth (kiểm tra sức khỏe dữ liệu)."""
    evaluator = SegmentationEvaluator()
    segmenter = HSVSegmenter()

    rows = []
    for img_path, gt_path in loader.build_dataset():
        image, gt = loader.load_image_gt_pair(img_path, gt_path)
        pred, _ = segmenter.segment(image)
        metrics = evaluator.compute_metrics(pred, gt)
        rows.append((os.path.basename(img_path), metrics))

    cell_w, cell_h = 400, 300
    canvas = np.zeros((cell_h, 2 * cell_w, 3), dtype=np.uint8)

    name, metrics = rows[0]
    img_path = os.path.join(loader.images_dir, name)
    image, gt = loader.load_image_gt_pair(img_path, loader.get_gt_path(img_path))
    pred, _ = segmenter.segment(image)

    canvas[0:cell_h, 0:cell_w] = _with_label(
        cv2.resize(image, (cell_w, cell_h - 26)), f"INPUT  {name}")
    canvas[0:cell_h, cell_w:2 * cell_w] = _with_label(
        cv2.resize(pred, (cell_w, cell_h - 26)),
        f"HSV DEFAULT  IoU={metrics['iou']:.3f}  Acc={metrics['pixel_accuracy']:.3f}")

    path = os.path.join(OUTPUT_DIR, 'default_config_example.png')
    cv2.imwrite(path, canvas)
    return path


def build_metrics_table(loader):
    """Tính bảng số liệu kiểm tra sức khỏe dữ liệu với cấu hình HSV mặc định."""
    evaluator = SegmentationEvaluator()
    segmenter = HSVSegmenter()

    table = []
    for img_path, gt_path in loader.build_dataset():
        image, gt = loader.load_image_gt_pair(img_path, gt_path)
        pred, _ = segmenter.segment(image)
        m = evaluator.compute_metrics(pred, gt)
        table.append({
            'image': os.path.basename(img_path),
            'accuracy': m['pixel_accuracy'],
            'iou': m['iou'],
            'precision': m['precision'],
            'recall': m['recall'],
        })
    return table


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    loader = DataLoader()
    metadata = loader.load_metadata()

    paths = [
        figure_dataset_overview(loader, metadata),
        figure_input_vs_gt(loader),
        figure_hard_cases(loader),
        figure_hsv_histogram(loader),
        figure_default_config_vs_gt(loader),
    ]

    print("Da sinh hinh minh hoa:")
    for p in paths:
        if p:
            print(f"  - {p}")

    print("\nBang kiem tra suc khoe du lieu voi cau hinh HSV mac dinh:")
    table = build_metrics_table(loader)
    print(f"{'Anh':<38} {'Accuracy':>9} {'IoU':>7} {'Precision':>10} {'Recall':>8}")
    for row in table:
        print(f"{row['image']:<38} {row['accuracy']:>9.4f} {row['iou']:>7.4f} "
              f"{row['precision']:>10.4f} {row['recall']:>8.4f}")
    avg_acc = np.mean([r['accuracy'] for r in table])
    avg_iou = np.mean([r['iou'] for r in table])
    print(f"{'TRUNG BINH':<38} {avg_acc:>9.4f} {avg_iou:>7.4f}")


if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
