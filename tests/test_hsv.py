# -*- coding: utf-8 -*-
"""Tests for HSV conversion, thresholding, and binary masks."""

import unittest

import cv2
import numpy as np

from src.hsv_segment import HSVSegmenter


class TestHSVSegmenter(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((40, 80, 3), dtype=np.uint8)
        self.image[:, :20] = (0, 0, 255)       # Pure red, hue near 0.
        self.image[:, 20:40] = (0, 20, 255)    # Orange-red, hue near 2.
        self.image[:, 40:60] = (0, 0, 128)     # Dark red.
        self.image[:, 60:] = (255, 0, 0)       # Blue.

    @staticmethod
    def config(hue_ranges, saturation=(0, 255), value=(0, 255)):
        return {
            "color_name": "Red",
            "hue_ranges": [list(bounds) for bounds in hue_ranges],
            "saturation": list(saturation),
            "value": list(value),
        }

    def test_bgr_to_hsv_preserves_shape_and_uint8_dtype(self):
        hsv = HSVSegmenter().bgr_to_hsv(self.image)
        self.assertEqual(hsv.shape, self.image.shape)
        self.assertEqual(hsv.dtype, np.uint8)

    def test_conversion_rejects_wrong_shape_or_dtype(self):
        segmenter = HSVSegmenter()
        with self.assertRaises(ValueError):
            segmenter.bgr_to_hsv(np.zeros((10, 10), dtype=np.uint8))
        with self.assertRaises(ValueError):
            segmenter.bgr_to_hsv(np.zeros((10, 10, 3), dtype=np.float32))

    def test_mask_is_binary_and_selects_only_red_pixels(self):
        segmenter = HSVSegmenter(self.config([(0, 10), (170, 180)], value=(200, 255)))
        mask, hsv = segmenter.segment(self.image)
        self.assertEqual(mask.shape, self.image.shape[:2])
        self.assertEqual(mask.dtype, np.uint8)
        np.testing.assert_array_equal(np.unique(mask), [0, 255])
        self.assertTrue(np.all(mask[:, :40] == 255))
        self.assertTrue(np.all(mask[:, 40:] == 0))
        self.assertTrue(np.all(mask[ :, :20][hsv[:, :20, 2] == 255] == 255))

    def test_hue_ranges_cover_both_sides_of_red_boundary(self):
        hues = np.array([[0, 179]], dtype=np.uint8)
        hsv = np.stack([hues, np.full_like(hues, 255), np.full_like(hues, 255)], axis=2)
        mask = HSVSegmenter(self.config([(0, 5), (175, 180)])).create_mask(hsv)
        np.testing.assert_array_equal(mask, [[255, 255]])

    def test_narrow_medium_wide_thresholds_on_same_image(self):
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        configs = [
            self.config([(0, 0)], (255, 255), (255, 255)),
            self.config([(0, 3)], (200, 255), (100, 255)),
            self.config([(0, 10), (170, 180)], (0, 255), (0, 255)),
        ]
        masks = [HSVSegmenter(config).create_mask(hsv) for config in configs]
        counts = [int(np.count_nonzero(mask)) for mask in masks]
        self.assertLess(counts[0], counts[1])
        self.assertLessEqual(counts[1], counts[2])
        for mask in masks:
            self.assertEqual(mask.shape, self.image.shape[:2])
            self.assertTrue(set(np.unique(mask)).issubset({0, 255}))

    def test_update_config_is_atomic_when_invalid(self):
        segmenter = HSVSegmenter()
        original = segmenter.get_config()
        with self.assertRaises(ValueError):
            segmenter.update_config(saturation=[200, 100])
        self.assertEqual(segmenter.get_config(), original)

    def test_invalid_hue_range_is_rejected(self):
        with self.assertRaises(ValueError):
            HSVSegmenter(self.config([(0, 181)]))

    def test_monochrome_images(self):
        for bgr, selected in [((0, 0, 255), 255), ((255, 0, 0), 0),
                              ((128, 128, 128), 0), ((0, 0, 0), 0)]:
            with self.subTest(bgr=bgr):
                image = np.full((12, 17, 3), bgr, dtype=np.uint8)
                mask, hsv = HSVSegmenter().segment(image)
                self.assertEqual(mask.shape, (12, 17))
                self.assertEqual(mask.dtype, np.uint8)
                self.assertTrue(np.all(mask == selected))
                self.assertEqual(hsv.shape, image.shape)

    def test_red_on_nearby_orange_and_pink_backgrounds(self):
        # Use HSV-defined backgrounds, then exercise the full BGR input pipeline.
        for background in [(15, 220, 220), (165, 80, 240)]:
            with self.subTest(background=background):
                hsv = np.full((20, 30, 3), background, dtype=np.uint8)
                hsv[5:15, 10:20] = (0, 255, 230)
                bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                mask, _ = HSVSegmenter().segment(bgr)
                expected = np.zeros((20, 30), dtype=np.uint8)
                expected[5:15, 10:20] = 255
                np.testing.assert_array_equal(mask, expected)

    def test_inclusive_hsv_bounds(self):
        hsv = np.array([[[5, 100, 100], [10, 255, 255], [11, 255, 255],
                         [5, 99, 100], [5, 100, 99]]], dtype=np.uint8)
        mask = HSVSegmenter(self.config([(5, 10)], (100, 255), (100, 255))).create_mask(hsv)
        np.testing.assert_array_equal(mask, [[255, 255, 0, 0, 0]])

    def test_hsv_info(self):
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        mask = HSVSegmenter(self.config([(0, 10), (170, 180)])).create_mask(hsv)
        info = HSVSegmenter.get_hsv_info(hsv, mask)
        self.assertEqual(info["pixel_count"], int(np.count_nonzero(mask)))
        self.assertLessEqual(info["h_min"], info["h_max"])


if __name__ == "__main__":
    unittest.main()
