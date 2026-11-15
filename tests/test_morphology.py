# -*- coding: utf-8 -*-
"""
Test Module: test_morphology.py
Kiểm thử module hình thái học (Morphological Operations)
Phụ trách: Quốc Anh

Bao phủ các tiêu chí bàn giao trong kế hoạch Excel:
  - Task 2: Fixture Mask có vùng trắng rời rạc và lỗ đen nhỏ
  - Task 3: Erosion / Dilation — kích thước không đổi, mô tả được thay đổi vùng trắng
  - Task 4: Opening — loại bỏ vùng trắng nhỏ
  - Task 5: Closing — lấp kín lỗ đen nhỏ
  - Task 6: So sánh kernel 3x3 và 5x5, ghi nhận tác động lên biên/chi tiết
  - Task 7: Kiểm tra operation không hợp lệ, input và đầu ra
"""

import unittest

import numpy as np

from src.morphology import MorphologyOperator, compare_morphology_operations
from tests.fixtures.morphology import (
    HOLE_1,
    HOLE_2,
    SPECK_1,
    SPECK_2,
    SQUARE_A,
    SQUARE_B,
    make_empty_mask,
    make_full_mask,
    make_noisy_mask,
    make_solid_mask,
    make_thin_mask,
)


class TestMorphologyFixtures(unittest.TestCase):
    """Kiểm thử bộ fixture — bảo đảm fixture đúng như thiết kế"""

    def setUp(self):
        self.mask = make_noisy_mask()

    def test_fixture_shape_and_dtype(self):
        """Fixture có shape (H, W), dtype uint8"""
        self.assertEqual(self.mask.shape, (120, 120))
        self.assertEqual(self.mask.ndim, 2)
        self.assertEqual(self.mask.dtype, np.uint8)

    def test_fixture_is_binary(self):
        """Fixture chỉ chứa giá trị 0 và 255 (Quy ước 2 của nhóm)"""
        self.assertTrue(set(np.unique(self.mask).tolist()).issubset({0, 255}))

    def test_fixture_contains_holes_and_specks(self):
        """Fixture có cả lỗ đen bên trong vật thể lẫn đốm trắng rời rạch"""
        # Lỗ đen nằm bên trong vật thể -> giá trị 0
        self.assertEqual(np.count_nonzero(self.mask[HOLE_1]), 0)
        self.assertEqual(np.count_nonzero(self.mask[HOLE_2]), 0)

        # Đốm trắng rời rạch nằm ngoài vật thể -> giá trị 255
        self.assertGreater(np.count_nonzero(self.mask[SPECK_1]), 0)
        self.assertGreater(np.count_nonzero(self.mask[SPECK_2]), 0)

        # Vật thể chính vẫn là vùng trắng
        self.assertGreater(np.count_nonzero(self.mask[SQUARE_A]), 0)
        self.assertGreater(np.count_nonzero(self.mask[SQUARE_B]), 0)

    def test_solid_fixture_has_no_noise(self):
        """Fixture sạch không có lỗ đen cũng không có đốm rời rạch"""
        mask = make_solid_mask()
        self.assertEqual(np.count_nonzero(mask[HOLE_1]), 9)
        self.assertEqual(np.count_nonzero(mask[SPECK_1]), 0)

    def test_edge_fixtures(self):
        """Fixture rỗng và fixture đầy có số pixel đối tượng đúng"""
        self.assertEqual(np.count_nonzero(make_empty_mask()), 0)
        self.assertEqual(np.count_nonzero(make_full_mask()), make_full_mask().size)

    def test_thin_fixture_is_one_pixel_wide(self):
        """Fixture vùng mảnh chỉ dày 1 px"""
        mask = make_thin_mask()
        row = mask[60]
        self.assertGreater(np.count_nonzero(row), 0)
        # Đường ngang nằm ở hàng 60, đường dọc ở cột 60
        self.assertEqual(mask[60, 50], 255)
        self.assertEqual(mask[59, 50], 0)
        self.assertEqual(mask[50, 60], 255)
        self.assertEqual(mask[50, 59], 0)


class TestMorphologyOperatorSetup(unittest.TestCase):
    """Kiểm thử khởi tạo và cấu hình kernel"""

    def test_default_kernel(self):
        """Mặc định kernel 5x5 hình ellipse"""
        operator = MorphologyOperator()
        self.assertEqual(operator.kernel_size, 5)
        self.assertEqual(operator.kernel_shape, 'ellipse')
        self.assertEqual(operator.kernel.shape, (5, 5))

    def test_supported_kernel_shapes(self):
        """Cả ba hình kernel đều được hỗ trợ"""
        for shape in ('rect', 'ellipse', 'cross'):
            operator = MorphologyOperator(3, shape)
            self.assertEqual(operator.kernel.shape, (3, 3))
            self.assertEqual(operator.kernel_shape, shape)

    def test_even_kernel_size_rejected(self):
        """Kernel phải là số lẻ -> số chẵn bị từ chối"""
        with self.assertRaises(ValueError):
            MorphologyOperator(4, 'ellipse')

    def test_non_positive_kernel_size_rejected(self):
        """Kernel size <= 0 bị từ chối"""
        for size in (0, -3):
            with self.assertRaises(ValueError):
                MorphologyOperator(size, 'ellipse')

    def test_unsupported_kernel_shape_rejected(self):
        """Hình kernel không hỗ trợ bị từ chối"""
        with self.assertRaises(ValueError):
            MorphologyOperator(3, 'triangle')

    def test_set_kernel_updates_kernel(self):
        """set_kernel cập nhật cả thuộc tính lẫn ma trận kernel"""
        operator = MorphologyOperator(3, 'rect')
        operator.set_kernel(7, 'cross')
        self.assertEqual(operator.kernel_size, 7)
        self.assertEqual(operator.kernel.shape, (7, 7))
        self.assertEqual(operator.get_kernel_info()['shape'], 'cross')

    def test_get_kernel_info(self):
        """get_kernel_info trả về đủ size, shape và kernel"""
        info = MorphologyOperator(5, 'ellipse').get_kernel_info()
        self.assertEqual(info['size'], 5)
        self.assertEqual(info['shape'], 'ellipse')
        self.assertEqual(info['kernel'].shape, (5, 5))


class TestMorphologyOutputContract(unittest.TestCase):
    """Tiêu chí bàn giao: đầu ra cùng H×W, uint8, nhị phân"""

    def setUp(self):
        self.mask = make_noisy_mask()
        self.operator = MorphologyOperator(3, 'ellipse')

    def _assert_valid_output(self, result, original):
        self.assertEqual(result.shape, original.shape)
        self.assertEqual(result.dtype, np.uint8)
        self.assertTrue(set(np.unique(result).tolist()).issubset({0, 255}))

    def test_all_operations_preserve_size_and_dtype(self):
        """Mọi phép toán giữ nguyên kích thước và kiểu dữ liệu"""
        results = {
            'erode': self.operator.erode(self.mask),
            'dilate': self.operator.dilate(self.mask),
            'open': self.operator.open(self.mask),
            'close': self.operator.close(self.mask),
        }
        for name, result in results.items():
            with self.subTest(operation=name):
                self._assert_valid_output(result, self.mask)

    def test_operations_on_empty_mask(self):
        """Phép toán trên Mask rỗng không lỗi"""
        empty = make_empty_mask()
        for result in (self.operator.erode(empty), self.operator.dilate(empty),
                       self.operator.open(empty), self.operator.close(empty)):
            self._assert_valid_output(result, empty)
            self.assertEqual(np.count_nonzero(result), 0)

    def test_operations_on_full_mask(self):
        """Phép toán trên Mask toàn trắng không lỗi"""
        full = make_full_mask()
        for result in (self.operator.erode(full), self.operator.dilate(full),
                       self.operator.open(full), self.operator.close(full)):
            self._assert_valid_output(result, full)

    def test_input_mask_not_modified(self):
        """Phép toán không sửa đổi Mask đầu vào"""
        original = make_noisy_mask()
        backup = original.copy()
        self.operator.erode(original)
        self.operator.dilate(original)
        self.operator.open(original)
        self.operator.close(original)
        np.testing.assert_array_equal(original, backup)


class TestErosionAndDilation(unittest.TestCase):
    """Task 3: Erosion (co) và Dilation (giãn)"""

    def setUp(self):
        self.mask = make_noisy_mask()
        self.operator = MorphologyOperator(3, 'ellipse')

    def test_erosion_shrinks_white_region(self):
        """Erosion làm vùng trắng nhỏ đi"""
        eroded = self.operator.erode(self.mask)
        self.assertLess(np.count_nonzero(eroded), np.count_nonzero(self.mask))

    def test_dilation_expands_white_region(self):
        """Dilation làm vùng trắng lớn lên"""
        dilated = self.operator.dilate(self.mask)
        self.assertGreater(np.count_nonzero(dilated), np.count_nonzero(self.mask))

    def test_erosion_is_subset_of_input(self):
        """Bất biến: Erosion không thêm pixel mới"""
        eroded = self.operator.erode(self.mask)
        self.assertTrue(np.all((eroded > 0) <= (self.mask > 0)))

    def test_dilation_is_superset_of_input(self):
        """Bất biến: Dilation không mất pixel nào"""
        dilated = self.operator.dilate(self.mask)
        self.assertTrue(np.all((dilated > 0) >= (self.mask > 0)))

    def test_erosion_removes_boundary(self):
        """Erosion ăn mòn biên của vật thể"""
        eroded = self.operator.erode(self.mask)
        # Góc trên-trái của hình vuông A bị cắt bỏ
        self.assertEqual(eroded[SQUARE_A][0, 0], 0)
        # Nhưng phần giữa, xa lỗ đen, vẫn còn trắng
        self.assertEqual(eroded[SQUARE_A][25, 15], 255)

    def test_dilation_grows_outside_boundary(self):
        """Dilation mở rộng ra ngoài biên của vật thể"""
        dilated = self.operator.dilate(self.mask)
        # Góc trên-trái hình vuông A được lấp đầy thêm
        self.assertEqual(dilated[SQUARE_A][0, 0], 255)

    def test_iterations_increase_effect(self):
        """Số lần lặp tăng -> tác động mạnh hơn"""
        once = self.operator.erode(self.mask, iterations=1)
        thrice = self.operator.erode(self.mask, iterations=3)
        self.assertLess(np.count_nonzero(thrice), np.count_nonzero(once))

    def test_erode_matches_opencv_morphology_ex(self):
        """Erosion cho kết quả giống cv2.morphologyEx(MORPH_ERODE)"""
        import cv2
        expected = cv2.morphologyEx(self.mask, cv2.MORPH_ERODE, self.operator.kernel)
        np.testing.assert_array_equal(self.operator.erode(self.mask), expected)

    def test_dilate_matches_opencv_morphology_ex(self):
        """Dilation cho kết quả giống cv2.morphologyEx(MORPH_DILATE)"""
        import cv2
        expected = cv2.morphologyEx(self.mask, cv2.MORPH_DILATE, self.operator.kernel)
        np.testing.assert_array_equal(self.operator.dilate(self.mask), expected)


class TestOpening(unittest.TestCase):
    """Task 4: Opening = Erosion -> Dilation, loại bỏ vùng trắng nhỏ"""

    def setUp(self):
        self.mask = make_noisy_mask()
        self.operator = MorphologyOperator(3, 'ellipse')

    def test_opening_shrinks_small_white_speck(self):
        """Opening làm nhỏ vùng trắng rời rạch (kernel 3x3 chưa xóa hết)"""
        opened = self.operator.open(self.mask)
        speck_before = np.count_nonzero(self.mask[SPECK_1])
        speck_after = np.count_nonzero(opened[SPECK_1])
        self.assertLess(speck_after, speck_before)

    def test_opening_removes_small_white_speck_with_larger_kernel(self):
        """Kernel 5x5 xóa hoàn toàn đốm trắng 4x4 rời rạch"""
        operator = MorphologyOperator(5, 'ellipse')
        opened = operator.open(self.mask)
        self.assertEqual(np.count_nonzero(opened[SPECK_1]), 0)
        self.assertEqual(np.count_nonzero(opened[SPECK_2]), 0)

    def test_opening_keeps_main_object(self):
        """Opening giữ lại vùng đối tượng chính"""
        opened = self.operator.open(self.mask)
        self.assertGreater(np.count_nonzero(opened[SQUARE_A]), 0)
        self.assertGreater(np.count_nonzero(opened[SQUARE_B]), 0)

    def test_opening_is_subset_of_input(self):
        """Bất biến: Opening không thêm pixel mới"""
        opened = self.operator.open(self.mask)
        self.assertTrue(np.all((opened > 0) <= (self.mask > 0)))

    def test_opening_reduces_white_pixels(self):
        """Opening làm giảm tổng số pixel trắng"""
        opened = self.operator.open(self.mask)
        self.assertLess(np.count_nonzero(opened), np.count_nonzero(self.mask))

    def test_opening_equals_erode_then_dilate(self):
        """Opening đúng bằng Erosion -> Dilation"""
        manual = self.operator.dilate(self.operator.erode(self.mask))
        np.testing.assert_array_equal(self.operator.open(self.mask), manual)

    def test_opening_leaves_solid_mask_intact(self):
        """Trên Mask sạch, Opening gần như không thay đổi gì"""
        solid = make_solid_mask()
        opened = self.operator.open(solid)
        self.assertGreater(np.count_nonzero(opened), 0)
        self.assertLessEqual(
            abs(np.count_nonzero(opened) - np.count_nonzero(solid)),
            np.count_nonzero(solid),
        )


class TestClosing(unittest.TestCase):
    """Task 5: Closing = Dilation -> Erosion, lấp kín lỗ đen nhỏ"""

    def setUp(self):
        self.mask = make_noisy_mask()
        self.operator = MorphologyOperator(3, 'ellipse')

    def test_closing_fills_small_black_hole(self):
        """Closing lấp kín lỗ đen nằm bên trong vật thể (kernel 5x5 lấp hết)"""
        operator = MorphologyOperator(5, 'ellipse')
        closed = operator.close(self.mask)
        self.assertEqual(np.count_nonzero(closed[HOLE_1]), 9)
        self.assertEqual(np.count_nonzero(closed[HOLE_2]), 9)

    def test_closing_partially_fills_hole_with_small_kernel(self):
        """Kernel 3x3 chỉ lấp được một phần lỗ 3x3 (4/9 pixel)"""
        closed = self.operator.close(self.mask)
        filled = np.count_nonzero(closed[HOLE_1])
        self.assertGreater(filled, 0)
        self.assertLess(filled, 9)

    def test_closing_keeps_main_object(self):
        """Closing giữ lại vùng đối tượng chính"""
        closed = self.operator.close(self.mask)
        self.assertGreater(np.count_nonzero(closed[SQUARE_A]), 0)
        self.assertGreater(np.count_nonzero(closed[SQUARE_B]), 0)

    def test_closing_is_superset_of_input(self):
        """Bất biến: Closing không mất pixel nào"""
        closed = self.operator.close(self.mask)
        self.assertTrue(np.all((closed > 0) >= (self.mask > 0)))

    def test_closing_increases_white_pixels(self):
        """Closing làm tăng tổng số pixel trắng"""
        closed = self.operator.close(self.mask)
        self.assertGreater(np.count_nonzero(closed), np.count_nonzero(self.mask))

    def test_closing_equals_dilate_then_erode(self):
        """Closing đúng bằng Dilation -> Erosion"""
        manual = self.operator.erode(self.operator.dilate(self.mask))
        np.testing.assert_array_equal(self.operator.close(self.mask), manual)

    def test_opening_and_closing_differ(self):
        """Opening và Closing có tác dụng KHÁC nhau (tiêu chí báo cáo)"""
        opened = self.operator.open(self.mask)
        closed = self.operator.close(self.mask)
        self.assertFalse(np.array_equal(opened, closed))

    def test_opening_removes_speck_but_closing_does_not(self):
        """Opening loại đốm trắng, Closing không loại"""
        opened = MorphologyOperator(5, 'ellipse').open(self.mask)
        closed = self.operator.close(self.mask)
        self.assertEqual(np.count_nonzero(opened[SPECK_1]), 0)
        self.assertGreater(np.count_nonzero(closed[SPECK_1]), 0)

    def test_closing_fills_hole_but_opening_does_not(self):
        """Closing lấp lỗ đen, Opening không lấp"""
        opened = MorphologyOperator(5, 'ellipse').open(self.mask)
        closed = MorphologyOperator(5, 'ellipse').close(self.mask)
        self.assertEqual(np.count_nonzero(closed[HOLE_1]), 9)
        self.assertEqual(np.count_nonzero(opened[HOLE_1]), 0)


class TestKernelComparison(unittest.TestCase):
    """Task 6: So sánh kernel 3x3 và 5x5, tác động lên biên/chi tiết"""

    def setUp(self):
        self.mask = make_noisy_mask()

    def test_same_input_across_kernels(self):
        """Tiêu chí bàn giao: giữ nguyên đầu vào khi so sánh kernel"""
        results = {}
        for size in (3, 5, 7):
            operator = MorphologyOperator(size, 'ellipse')
            results[size] = operator.open(self.mask)
        # Cùng đầu vào -> mọi kết quả cùng kích thước
        for result in results.values():
            self.assertEqual(result.shape, self.mask.shape)

    def test_larger_kernel_erodes_more(self):
        """Kernel lớn hơn -> Erosion mạnh hơn, vùng trắng nhỏ đi"""
        counts = [np.count_nonzero(MorphologyOperator(k, 'ellipse').erode(self.mask))
                  for k in (3, 5, 7)]
        self.assertGreater(counts[0], counts[1])
        self.assertGreater(counts[1], counts[2])

    def test_larger_kernel_dilates_more(self):
        """Kernel lớn hơn -> Dilation mạnh hơn, vùng trắng lớn lên"""
        counts = [np.count_nonzero(MorphologyOperator(k, 'ellipse').dilate(self.mask))
                  for k in (3, 5, 7)]
        self.assertLess(counts[0], counts[1])
        self.assertLess(counts[1], counts[2])

    def test_larger_kernel_opening_removes_more_specks(self):
        """Kernel lớn hơn -> Opening loại được cả đốm to hơn"""
        removed = []
        for size in (3, 5, 7):
            operator = MorphologyOperator(size, 'ellipse')
            opened = operator.open(self.mask)
            removed.append(np.count_nonzero(self.mask) - np.count_nonzero(opened))
        self.assertGreater(removed[0], 0)
        self.assertGreater(removed[1], removed[0])
        self.assertGreater(removed[2], removed[1])

    def test_larger_kernel_closing_fills_more(self):
        """Kernel lớn hơn -> Closing lấp được nhiều lỗ hơn"""
        added = []
        for size in (3, 5, 7):
            operator = MorphologyOperator(size, 'ellipse')
            closed = operator.close(self.mask)
            added.append(np.count_nonzero(closed) - np.count_nonzero(self.mask))
        self.assertGreater(added[0], 0)
        self.assertGreater(added[1], added[0])

    def test_larger_kernel_loses_thin_details(self):
        """Kernel lớn làm mất chi tiết mảnh"""
        thin = make_thin_mask()
        counts = [np.count_nonzero(MorphologyOperator(k, 'ellipse').erode(thin))
                  for k in (3, 5, 7)]
        # Kernel 5x5 và 7x7 xóa hẳn vùng mảnh 1 px
        self.assertEqual(counts[2], 0)

    def test_kernel_shape_changes_result(self):
        """Hình kernel khác nhau cho kết quả khác nhau"""
        rect = MorphologyOperator(3, 'rect').erode(self.mask)
        ellipse = MorphologyOperator(3, 'ellipse').erode(self.mask)
        cross = MorphologyOperator(3, 'cross').erode(self.mask)
        self.assertFalse(np.array_equal(rect, ellipse))
        self.assertFalse(np.array_equal(rect, cross))

    def test_kernel_shape_affects_hole_filling(self):
        """Kernel rect 3x3 không lấp được lỗ 3x3, ellipse thì lấp được một phần"""
        rect = MorphologyOperator(3, 'rect').close(self.mask)
        ellipse = MorphologyOperator(3, 'ellipse').close(self.mask)
        self.assertEqual(np.count_nonzero(rect[HOLE_1]), 0)
        self.assertGreater(np.count_nonzero(ellipse[HOLE_1]), 0)

    def test_compare_morphology_operations_helper(self):
        """Hàm compare_morphology_operations trả về đủ 5 biến thể"""
        results = compare_morphology_operations(self.mask, kernel_size=3)
        self.assertEqual(
            set(results),
            {'original', 'erode', 'dilate', 'open', 'close'},
        )
        for name, result in results.items():
            with self.subTest(variant=name):
                self.assertEqual(result.shape, self.mask.shape)
                self.assertEqual(result.dtype, np.uint8)


class TestApplyOperationAndSequence(unittest.TestCase):
    """Task 7: apply_operation và apply_sequence"""

    def setUp(self):
        self.mask = make_noisy_mask()
        self.operator = MorphologyOperator(3, 'ellipse')

    def test_apply_operation_supported_names(self):
        """Mọi phép toán được hỗ trợ đều chạy được qua apply_operation"""
        for name in ('erode', 'dilate', 'open', 'close', 'gradient', 'tophat', 'blackhat'):
            with self.subTest(operation=name):
                result = self.operator.apply_operation(self.mask, name)
                self.assertEqual(result.shape, self.mask.shape)
                self.assertEqual(result.dtype, np.uint8)

    def test_apply_operation_unsupported_name(self):
        """Phép toán không hỗ trợ bị từ chối"""
        with self.assertRaises(ValueError):
            self.operator.apply_operation(self.mask, 'magic')

    def test_apply_operation_respects_iterations(self):
        """Tham số iterations được truyền xuống đúng"""
        once = self.operator.apply_operation(self.mask, 'erode', iterations=1)
        twice = self.operator.apply_operation(self.mask, 'erode', iterations=2)
        self.assertGreater(np.count_nonzero(once), np.count_nonzero(twice))

    def test_apply_sequence_order_matters(self):
        """Chuỗi phép toán được áp dụng đúng thứ tự (Erosion và Dilation không phải phép nghịch đảo)"""
        erode_then_open = self.operator.apply_sequence(
            self.mask, [('erode', {'iterations': 1}), ('open', {'iterations': 1})])
        open_then_erode = self.operator.apply_sequence(
            self.mask, [('open', {'iterations': 1}), ('erode', {'iterations': 1})])
        self.assertFalse(np.array_equal(erode_then_open, open_then_erode))
        self.assertGreater(np.count_nonzero(open_then_erode), np.count_nonzero(erode_then_open))

    def test_apply_sequence_closing_then_opening_removes_speck(self):
        """Closing rồi Opening vẫn loại được đốm rời rạch (kernel 5x5)"""
        result = MorphologyOperator(5, 'ellipse').apply_sequence(
            self.mask, [('close', {'iterations': 1}), ('open', {'iterations': 1})])
        self.assertEqual(np.count_nonzero(result[SPECK_1]), 0)

    def test_apply_sequence_empty_operations(self):
        """Chuỗi rỗng trả về Mask giống hệt đầu vào"""
        result = self.operator.apply_sequence(self.mask, [])
        np.testing.assert_array_equal(result, self.mask)

    def test_apply_sequence_invalid_operation(self):
        """Phép toán không hợp lệ trong chuỗi bị từ chối"""
        with self.assertRaises(ValueError):
            self.operator.apply_sequence(self.mask, [('magic', {'iterations': 1})])


class TestInvalidInput(unittest.TestCase):
    """Task 7: Kiểm tra input không hợp lệ"""

    def setUp(self):
        self.operator = MorphologyOperator(3, 'ellipse')

    def test_none_mask_rejected(self):
        """Mask None bị từ chối"""
        for method in ('erode', 'dilate', 'open', 'close'):
            with self.subTest(method=method):
                with self.assertRaises(ValueError):
                    getattr(self.operator, method)(None)

    def test_empty_mask_rejected(self):
        """Mask rỗng (0 phần tử) bị từ chối"""
        empty = np.zeros((0, 0), dtype=np.uint8)
        for method in ('erode', 'dilate', 'open', 'close'):
            with self.subTest(method=method):
                with self.assertRaises(ValueError):
                    getattr(self.operator, method)(empty)

    def test_apply_operation_rejects_invalid_mask(self):
        """apply_operation cũng từ chối Mask không hợp lệ"""
        with self.assertRaises(ValueError):
            self.operator.apply_operation(None, 'erode')
        with self.assertRaises(ValueError):
            self.operator.apply_operation(np.zeros((0, 0), np.uint8), 'close')

    def test_apply_sequence_rejects_invalid_mask(self):
        """apply_sequence từ chối Mask không hợp lệ"""
        with self.assertRaises(ValueError):
            self.operator.apply_sequence(None, [('close', {'iterations': 1})])


class TestPipelineIntegration(unittest.TestCase):
    """Module phải tích hợp được theo API đã thống nhất (Tiêu chí Task 7)"""

    def test_mask_survives_median_then_morphology(self):
        """Mask đi qua Median -> Morphology vẫn giữ đúng kích thước và kiểu"""
        from src.median_filter import MedianFilter

        mask = make_noisy_mask()
        filtered = MedianFilter(3).filter(mask)
        morph = MorphologyOperator(3, 'ellipse').close(filtered)

        self.assertEqual(morph.shape, mask.shape)
        self.assertEqual(morph.dtype, np.uint8)
        self.assertTrue(set(np.unique(morph).tolist()).issubset({0, 255}))

    def test_median_fills_single_pixel_hole_that_closing_cannot(self):
        """Median lấp được lỗ 1 px đơn lẻ, Closing (kernel 3x3) thì không"""
        from src.median_filter import MedianFilter

        solid = make_solid_mask()
        holed = solid.copy()
        holed[30, 30] = 0

        filtered = MedianFilter(3).filter(holed)
        # Lỗ 1 px bị Median lấp lại thành trắng
        self.assertEqual(filtered[30, 30], 255)

    def test_closing_fills_cluster_hole_that_median_cannot(self):
        """Closing lấp được lỗ cụm 3x3 mà Median không xử lý được"""
        from src.median_filter import MedianFilter

        solid = make_solid_mask()
        holed = solid.copy()
        holed[32:35, 32:35] = 0     # lỗ cụm 3x3

        filtered = MedianFilter(3).filter(holed)
        # Median không lấp được lỗ cụm -> vẫn còn pixel đen ở giữa
        self.assertEqual(filtered[33, 33], 0)

        closed = MorphologyOperator(5, 'ellipse').close(filtered)
        # Closing lấp kín lỗ cụm
        self.assertEqual(closed[33, 33], 255)

    def test_opening_removes_white_specks_left_after_segmentation(self):
        """Opening loại bỏ đốm trắng rời rạch còn sót lại sau phân đoạn"""
        solid = make_solid_mask()
        with_specks = solid.copy()
        with_specks[8:12, 8:12] = 255
        with_specks[100:104, 100:104] = 255

        opened = MorphologyOperator(5, 'ellipse').open(with_specks)
        # Hai đốm trắng rời rạch bị loại hoàn toàn
        self.assertEqual(np.count_nonzero(opened[8:12, 8:12]), 0)
        self.assertEqual(np.count_nonzero(opened[100:104, 100:104]), 0)
        # Vật thể chính vẫn còn
        self.assertGreater(np.count_nonzero(opened[SQUARE_A]), 0)
        self.assertGreater(np.count_nonzero(opened[SQUARE_B]), 0)


if __name__ == '__main__':
    unittest.main()
