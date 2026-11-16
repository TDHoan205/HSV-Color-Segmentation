# -*- coding: utf-8 -*-
"""
Kiểm thử module Median Filter (src/median_filter.py) - Anh Tuấn.

Chạy bằng pytest:
    python -m pytest tests/test_median.py -v
Chạy trực tiếp:
    python tests/test_median.py
"""

import os
import sys
import unittest

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.evaluation import SegmentationEvaluator  # noqa: E402
from src.hsv_segment import HSVSegmenter  # noqa: E402
from src.median_filter import (  # noqa: E402
    MedianFilter,
    apply_median_filter,
    compare_kernels,
    median_filter,
)

FIXTURE_DIR = os.path.join(ROOT, 'tests', 'fixtures', 'median')
RESULT_DIR = os.path.join(ROOT, 'results', 'median_comparison')


def _load_fixture(name):
    """Đọc một fixture PNG (grayscale 1 kênh) từ tests/fixtures/median."""
    path = os.path.join(FIXTURE_DIR, name)
    if not os.path.exists(path):
        raise unittest.SkipTest(f"Thieu fixture '{name}'. "
                                f"Chay: python tests/fixtures/median/generate_fixtures.py")
    mask = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"Khong doc duoc fixture: {path}")
    return mask


class TestMedianFilterCorrectness(unittest.TestCase):
    """Tính đúng đắn, bảo toàn định dạng và không làm thay đổi đầu vào."""

    def setUp(self):
        self.mask = np.zeros((40, 60), dtype=np.uint8)
        self.mask[10:30, 15:45] = 255

    def test_output_preserves_shape_dtype_and_binary_values(self):
        for kernel_size in (3, 5, 7):
            with self.subTest(kernel_size=kernel_size):
                out = apply_median_filter(self.mask, kernel_size)
                self.assertEqual(out.shape, self.mask.shape)
                self.assertEqual(out.ndim, 2)
                self.assertEqual(out.dtype, np.uint8)
                self.assertTrue(set(np.unique(out)).issubset({0, 255}))

    def test_input_mask_is_not_modified(self):
        original = self.mask.copy()
        out = apply_median_filter(self.mask, 5)
        np.testing.assert_array_equal(self.mask, original)
        # Mảng trả về không được là view của mảng đầu vào.
        self.assertFalse(np.shares_memory(out, self.mask))

    def test_default_kernel_size_is_3(self):
        np.testing.assert_array_equal(
            apply_median_filter(self.mask),
            apply_median_filter(self.mask, 3),
        )

    def test_alias_matches_main_function(self):
        np.testing.assert_array_equal(
            median_filter(self.mask, 5),
            apply_median_filter(self.mask, 5),
        )

    def test_class_api_still_works_for_main_pipeline(self):
        """main.py / experiment.py gọi MedianFilter(kernel).filter(mask)."""
        median = MedianFilter(kernel_size=5)
        out = median.filter(self.mask)
        self.assertEqual(out.shape, self.mask.shape)
        self.assertEqual(out.dtype, np.uint8)
        self.assertTrue(set(np.unique(out)).issubset({0, 255}))
        self.assertEqual(median.get_kernel_size(), 5)

        comparison = median.filter_with_comparison(self.mask)
        self.assertIn('changed_pixels', comparison)
        self.assertEqual(comparison['kernel_size'], 5)

    def test_salt_pepper_fixture_is_cleaned_completely(self):
        """Nhiễu muối tiêu đơn lẻ phải được lọc sạch 100% bởi kernel 3x3."""
        noisy = _load_fixture('noisy_salt_pepper_3x3.png')
        expected = _load_fixture('expected_clean_3x3.png')

        out = apply_median_filter(noisy, 3)
        self.assertEqual(out.shape, expected.shape)
        self.assertEqual(out.dtype, np.uint8)

        matching = int(np.count_nonzero(out == expected))
        self.assertEqual(matching, expected.size,
                         f"Khop {matching}/{expected.size} pixel")
        np.testing.assert_array_equal(out, expected)

    def test_compare_kernels_helper_returns_metrics(self):
        result = compare_kernels(self.mask, (3, 5, 7))
        self.assertEqual(sorted(result['kernels']), [3, 5, 7])
        for kernel_size in (3, 5, 7):
            metrics = result['metrics'][kernel_size]
            self.assertIn('changed_pixels', metrics)
            self.assertIn('changed_ratio', metrics)
            self.assertEqual(result['kernels'][kernel_size].dtype, np.uint8)


class TestMedianFilterValidation(unittest.TestCase):
    """Kiểm tra đầu vào: mọi trường hợp sai phải ném ngoại lệ rõ ràng."""

    def setUp(self):
        self.mask = np.zeros((20, 20), dtype=np.uint8)
        self.mask[5:15, 5:15] = 255

    def test_rejects_even_kernel_sizes(self):
        for kernel_size in (2, 4, 6, 8):
            with self.subTest(kernel_size=kernel_size):
                with self.assertRaises(ValueError):
                    apply_median_filter(self.mask, kernel_size)

    def test_rejects_kernel_sizes_smaller_than_three(self):
        for kernel_size in (1, 0, -3, -10):
            with self.subTest(kernel_size=kernel_size):
                with self.assertRaises(ValueError):
                    apply_median_filter(self.mask, kernel_size)

    def test_rejects_non_integer_kernel_sizes(self):
        for kernel_size in (3.0, 3.5, '3', None, [3], np.float32(3)):
            with self.subTest(kernel_size=kernel_size):
                with self.assertRaises(TypeError):
                    apply_median_filter(self.mask, kernel_size)

    def test_rejects_bool_kernel_size(self):
        with self.assertRaises(TypeError):
            apply_median_filter(self.mask, True)
        with self.assertRaises(TypeError):
            apply_median_filter(self.mask, False)

    def test_rejects_kernel_sizes_larger_than_31(self):
        """Quy ước của nhóm: kernel tối đa 31."""
        for kernel_size in (33, 51, 101):
            with self.subTest(kernel_size=kernel_size):
                with self.assertRaises(ValueError):
                    apply_median_filter(self.mask, kernel_size)
        # 31 vẫn dùng được
        self.assertEqual(apply_median_filter(self.mask, 31).shape, self.mask.shape)

    def test_rejects_none_mask(self):
        with self.assertRaises(ValueError):
            apply_median_filter(None, 3)

    def test_rejects_non_array_mask(self):
        for mask in ([0, 255, 0], 'mask', 255, {'mask': True}):
            with self.subTest(mask=type(mask).__name__):
                with self.assertRaises(TypeError):
                    apply_median_filter(mask, 3)

    def test_rejects_empty_mask(self):
        with self.assertRaises(ValueError):
            apply_median_filter(np.zeros((0, 0), dtype=np.uint8), 3)

    def test_rejects_three_channel_masks(self):
        with self.assertRaises(ValueError):
            apply_median_filter(np.zeros((10, 10, 3), dtype=np.uint8), 3)
        with self.assertRaises(ValueError):
            apply_median_filter(np.zeros((10, 10, 1), dtype=np.uint8), 3)

    def test_rejects_wrong_dtype(self):
        for dtype in (np.float32, np.float64, np.int32, np.int64, np.bool_):
            with self.subTest(dtype=np.dtype(dtype).name):
                mask = self.mask.astype(dtype)
                with self.assertRaises(TypeError):
                    apply_median_filter(mask, 3)

    def test_rejects_values_outside_zero_and_255(self):
        mask = self.mask.copy()
        mask[0, 0] = 128
        with self.assertRaises(ValueError):
            apply_median_filter(mask, 3)

    def test_rejects_zero_one_binary_convention(self):
        """Quy ước của nhóm là 0/255, không phải 0/1."""
        mask = (self.mask > 0).astype(np.uint8)
        with self.assertRaises(ValueError) as context:
            apply_median_filter(mask, 3)
        self.assertIn('0/255', str(context.exception))


class TestKernelComparison(unittest.TestCase):
    """So sánh hành vi của các kích thước kernel 3x3, 5x5, 7x7."""

    def test_dense_clusters_need_larger_kernel(self):
        """3x3 chưa lọc hết cụm nhiễu, 5x5 lọc sạch."""
        noisy = _load_fixture('dense_noise_clusters.png')
        clean = _load_fixture('expected_clean_dense.png')
        noise_pixels = (noisy == 255) & (clean == 0)
        self.assertGreater(int(np.count_nonzero(noise_pixels)), 0)

        residual_3 = int(np.count_nonzero(
            noise_pixels & (apply_median_filter(noisy, 3) == 255)))
        residual_5 = int(np.count_nonzero(
            noise_pixels & (apply_median_filter(noisy, 5) == 255)))

        self.assertGreater(residual_3, 0, "Kernel 3x3 phai con sot mot phan nhieu")
        self.assertEqual(residual_5, 0, "Kernel 5x5 phai loai het nhieu")

    def test_larger_kernel_changes_more_pixels_on_fine_details(self):
        """Tăng kernel làm mất dần chi tiết mảnh và bo tròn góc nhọn."""
        fine = _load_fixture('fine_details_edges.png')
        changed = [int(np.count_nonzero(apply_median_filter(fine, k) != fine))
                   for k in (3, 5, 7)]
        self.assertLess(changed[0], changed[1])
        self.assertLess(changed[1], changed[2])

    def test_thin_lines_disappear_with_large_kernel(self):
        """Đường 1-2 pixel bị xóa dần khi tăng kích thước kernel."""
        line_1px = np.zeros((20, 20), dtype=np.uint8)
        line_1px[10, 2:18] = 255
        # Đường 1 pixel: mọi kernel >= 3 đều xóa hết.
        for kernel_size in (3, 5, 7):
            self.assertEqual(int(np.count_nonzero(apply_median_filter(line_1px, kernel_size))), 0)

        line_2px = np.zeros((20, 20), dtype=np.uint8)
        line_2px[9:11, 2:18] = 255
        # Đường 2 pixel: còn với 3x3 (6/9 pixel trắng) nhưng mất với 5x5.
        self.assertGreater(int(np.count_nonzero(apply_median_filter(line_2px, 3))), 0)
        self.assertEqual(int(np.count_nonzero(apply_median_filter(line_2px, 5))), 0)


class TestMedianFilterExperiment(unittest.TestCase):
    """Thực nghiệm so sánh kernel trên ảnh thực tế của nhóm."""

    def test_comparison_images_are_written(self):
        script_dir = os.path.join(ROOT, 'scripts')
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        import run_median_comparison  # noqa: E402

        image_paths = []
        images_dir = os.path.join(ROOT, 'data', 'images')
        for name in sorted(os.listdir(images_dir)):
            if not name.endswith('.jpg'):
                continue
            stem = name[:-4]
            if os.path.exists(os.path.join(ROOT, 'data', 'ground_truth', stem + '.png')):
                image_paths.append(os.path.join(images_dir, name))
            if len(image_paths) == 2:
                break
        if not image_paths:
            raise unittest.SkipTest('Khong tim thay anh co Ground Truth trong data/images')

        output_dir = os.path.join(RESULT_DIR, 'pytest_check')
        result = run_median_comparison.run_comparison(
            image_paths=image_paths,
            output_dir=output_dir,
            write_figure=False,
            include_fixtures=False,
        )

        self.assertTrue(os.path.isdir(output_dir))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'metrics.csv')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'summary.json')))

        for image_path in image_paths:
            stem = os.path.splitext(os.path.basename(image_path))[0]
            comparison = os.path.join(output_dir, stem, 'comparison.png')
            self.assertTrue(os.path.exists(comparison),
                            f"Thieu anh so sanh: {comparison}")
            strip = cv2.imread(comparison)
            self.assertIsNotNone(strip)
            # 4 ô: Mask thô | 3x3 | 5x5 | 7x7
            self.assertEqual(strip.shape[1], 4 * 240)

        # Ba kích thước kernel cho mỗi ảnh, mọi mask đều nhị phân.
        evaluator = SegmentationEvaluator()
        segmenter = HSVSegmenter()
        image_bgr = cv2.imread(image_paths[0])
        mask_raw, _ = segmenter.segment(image_bgr)
        for kernel_size in (3, 5, 7):
            filtered = apply_median_filter(mask_raw, kernel_size)
            self.assertTrue(set(np.unique(filtered)).issubset({0, 255}))
            metrics = evaluator.compute_metrics(filtered, mask_raw)
            self.assertGreaterEqual(metrics['pixel_accuracy'], 0.0)

        kernel_sizes = {row['kernel_size'] for row in result['rows']}
        self.assertEqual(kernel_sizes, {3, 5, 7})


if __name__ == '__main__':
    unittest.main(verbosity=2)
