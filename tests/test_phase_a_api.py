# -*- coding: utf-8 -*-
"""Phase A: kiểm thử API chọn màu (preset, color_id) và hồi quy đường dẫn Red cũ."""

import io
import os
import shutil
import tempfile
import unittest

import cv2
import numpy as np

import main
from src.hsv_segment import COLOR_IDS

PRESET_ROUTE = '/api/color-presets'
UPLOAD_ROUTE = '/api/upload'
PROCESS_ROUTE = '/api/process'


def _make_png(image):
    ok, buf = cv2.imencode('.png', image)
    assert ok
    return io.BytesIO(buf.tobytes())


class TestPhaseAApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Dùng thư mục tạm để không ghi vào uploads/ của dự án
        cls._tmp = tempfile.mkdtemp()
        cls._old_upload = main.app.config['UPLOAD_FOLDER']
        main.app.config['UPLOAD_FOLDER'] = cls._tmp
        main.app.config['TESTING'] = True
        cls.client = main.app.test_client()

        # Ảnh tổng hợp: nền xám, ô đỏ thuần (H=0, S=255, V=255), ô xanh dương
        img = np.full((60, 60, 3), 128, np.uint8)
        img[5:25, 5:25] = (0, 0, 255)
        img[35:55, 35:55] = (255, 0, 0)
        cls.image = img

    @classmethod
    def tearDownClass(cls):
        main.app.config['UPLOAD_FOLDER'] = cls._old_upload
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _upload(self):
        resp = self.client.post(UPLOAD_ROUTE, data={'image': (_make_png(self.image), 'test.png')},
                                content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()['session_id']

    def _process(self, payload):
        return self.client.post(PROCESS_ROUTE, json=payload)

    def test_preset_route_returns_15_unique_presets(self):
        resp = self.client.get(PRESET_ROUTE)
        self.assertEqual(resp.status_code, 200)
        presets = resp.get_json()['presets']
        ids = [p['color_id'] for p in presets]
        self.assertEqual(len(ids), 15)
        self.assertEqual(len(set(ids)), 15)
        self.assertEqual(set(ids), set(COLOR_IDS))

    def test_preset_route_returns_verified_false_for_all(self):
        presets = self.client.get(PRESET_ROUTE).get_json()['presets']
        self.assertTrue(all(p['verified'] is False for p in presets))

    def test_process_with_each_color_id_returns_success(self):
        sid = self._upload()
        for cid in COLOR_IDS:
            with self.subTest(color=cid):
                resp = self._process({'session_id': sid, 'color_id': cid})
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.get_json()['status'], 'success')

    def test_unknown_color_id_returns_400_message(self):
        sid = self._upload()
        resp = self._process({'session_id': sid, 'color_id': 'magenta'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('magenta', resp.get_json()['error'])

    def test_legacy_request_without_color_id_still_works(self):
        sid = self._upload()
        resp = self._process({'session_id': sid})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['status'], 'success')

    def test_red_color_id_matches_legacy_red_output(self):
        sid = self._upload()
        legacy = self._process({'session_id': sid}).get_json()
        red = self._process({'session_id': sid, 'color_id': 'red'}).get_json()
        self.assertEqual(legacy['white_pixels'], red['white_pixels'])

    def test_blue_color_does_not_select_red_square(self):
        sid = self._upload()
        blue = self._process({'session_id': sid, 'color_id': 'blue'}).get_json()
        # Ô đỏ (25x25 - 20x20 = 400 px) không được chọn khi chọn Lam
        self.assertEqual(blue['white_pixels']['raw'], 400)

    def test_white_black_gray_do_not_depend_on_hue_sliders(self):
        sid = self._upload()
        for cid in ('white', 'black', 'gray'):
            with self.subTest(color=cid):
                a = self._process({'session_id': sid, 'color_id': cid, 'h_min_1': 0, 'h_max_1': 1}).get_json()
                b = self._process({'session_id': sid, 'color_id': cid, 'h_min_1': 100, 'h_max_1': 120}).get_json()
                self.assertEqual(a['white_pixels'], b['white_pixels'])


if __name__ == '__main__':
    unittest.main()
