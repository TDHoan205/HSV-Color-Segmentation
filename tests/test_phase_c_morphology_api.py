# -*- coding: utf-8 -*-
"""Phase C: kiểm thử Morphology API (C-T01..C-T08 + hồi quy) bằng dữ liệu tổng hợp.

Dữ liệu tổng hợp chỉ chứng minh logic chức năng. File tạm nằm trong thư mục tạm riêng.
"""

import base64
import io
import shutil
import tempfile
import unittest

import cv2
import numpy as np

import main
from src.morphology import MorphologyOperator
from src.median_filter import MedianFilter
from src.hsv_segment import HSVSegmenter

OPS = ('close', 'open', 'erode', 'dilate')
SHAPES = ('rect', 'ellipse', 'cross')


def _png(image):
    ok, buf = cv2.imencode('.png', image)
    assert ok
    return io.BytesIO(buf.tobytes())


def decode_mask(data_url):
    raw = base64.b64decode(data_url.split(',', 1)[1])
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)


class PhaseCBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp()
        cls._old_upload = main.app.config['UPLOAD_FOLDER']
        main.app.config['UPLOAD_FOLDER'] = cls._tmp
        main.app.config['TESTING'] = True
        cls.client = main.app.test_client()
        # Ảnh đỏ có lỗ, điểm nhiễu và cạnh răng cưa để mỗi phép cho kết quả khác nhau
        rng = np.random.RandomState(7)
        img = np.full((64, 64, 3), 128, np.uint8)
        img[8:40, 8:40] = (0, 0, 255)
        img[20:24, 20:24] = 128
        for _ in range(40):
            y, x = rng.randint(0, 64, 2)
            img[y, x] = (0, 0, 255)
        cls.image = img
        resp = cls.client.post('/api/upload', data={'image': (_png(img), 'a.png')},
                               content_type='multipart/form-data')
        cls.sid = resp.get_json()['session_id']

    @classmethod
    def tearDownClass(cls):
        main.app.config['UPLOAD_FOLDER'] = cls._old_upload
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def process(self, **extra):
        payload = {'session_id': self.sid, 'color_id': 'red', 'median_kernel': 3}
        payload.update(extra)
        return self.client.post('/api/process', json=payload)

    def expected_median(self):
        seg = HSVSegmenter({'color_name': 'Red', 'hue_ranges': [[0, 10], [170, 180]],
                            'saturation': [100, 255], 'value': [100, 255]})
        raw, _ = seg.segment(self.image)
        return MedianFilter(3).filter(raw)


def morph(size=5, shape='ellipse', ops=None):
    return {'kernel_size': size, 'kernel_shape': shape,
            'operations': [{'operation': o, 'iterations': 1} for o in (ops or [])]}


class TestC01_to_C03_Combinations(PhaseCBase):
    def test_c_t01_twelve_combinations_pixel_exact(self):
        median = self.expected_median()
        for op in OPS:
            for shape in SHAPES:
                with self.subTest(op=op, shape=shape):
                    r = self.process(morphology=morph(5, shape, [op]))
                    self.assertEqual(r.status_code, 200, r.get_json())
                    d = r.get_json()
                    expected = MorphologyOperator(5, shape).apply_sequence(
                        median, [(op, {'iterations': 1})])
                    self.assertTrue(np.array_equal(decode_mask(d['mask_morph']), expected))
                    self.assertTrue(np.array_equal(decode_mask(d['mask_median']), median))
                    self.assertEqual(d['applied_config']['morphology']['kernel_shape'], shape)

    def test_c_t02_order_preserved(self):
        median = self.expected_median()
        a = self.process(morphology=morph(5, 'rect', ['dilate', 'erode'])).get_json()
        b = self.process(morphology=morph(5, 'rect', ['erode', 'dilate'])).get_json()
        ops_a = [o['operation'] for o in a['applied_config']['morphology']['operations']]
        self.assertEqual(ops_a, ['dilate', 'erode'])
        exp_a = MorphologyOperator(5, 'rect').apply_sequence(
            median, [('dilate', {'iterations': 1}), ('erode', {'iterations': 1})])
        self.assertTrue(np.array_equal(decode_mask(a['mask_morph']), exp_a))
        self.assertFalse(np.array_equal(decode_mask(a['mask_morph']), decode_mask(b['mask_morph'])))

    def test_c_t03_iterations(self):
        median = self.expected_median()
        m = {'kernel_size': 3, 'kernel_shape': 'rect',
             'operations': [{'operation': 'erode', 'iterations': 3}]}
        d = self.process(morphology=m).get_json()
        exp = MorphologyOperator(3, 'rect').apply_sequence(median, [('erode', {'iterations': 3})])
        self.assertTrue(np.array_equal(decode_mask(d['mask_morph']), exp))
        self.assertEqual(d['applied_config']['morphology']['operations'][0]['iterations'], 3)

    def test_empty_operations_returns_median_copy(self):
        d = self.process(morphology=morph(5, 'rect', [])).get_json()
        self.assertTrue(np.array_equal(decode_mask(d['mask_morph']), decode_mask(d['mask_median'])))


class TestC04_Validation(PhaseCBase):
    def assert_400(self, m):
        r = self.process(morphology=m)
        self.assertEqual(r.status_code, 400, m)
        self.assertIn('error', r.get_json())

    def test_c_t04_invalid_values_rejected(self):
        bad = [
            morph(4), morph(0), morph(33), morph(-1),
            {'kernel_size': 5.0, 'kernel_shape': 'rect', 'operations': []},
            {'kernel_size': '5', 'kernel_shape': 'rect', 'operations': []},
            {'kernel_size': True, 'kernel_shape': 'rect', 'operations': []},
            {'kernel_size': None, 'kernel_shape': 'rect', 'operations': []},
            morph(5, 'star'),
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': 'close'},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [{'operation': 'blur', 'iterations': 1}]},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [{'operation': 'close', 'iterations': 0}]},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [{'operation': 'close', 'iterations': 11}]},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [{'operation': 'close', 'iterations': 1.5}]},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [{'operation': 'close', 'iterations': True}]},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [{'operation': 'close'}]},
            {'kernel_size': 5, 'kernel_shape': 'rect',
             'operations': [{'operation': 'close', 'iterations': 1}, {'operation': 'close', 'iterations': 1}]},
            {'kernel_size': 5, 'kernel_shape': 'rect', 'operations': [], 'extra': 1},
            {'kernel_size': 5, 'operations': []},
            'close', None, [], 5,
        ]
        for m in bad:
            with self.subTest(m=m):
                self.assert_400(m)

    def test_boundaries_accepted(self):
        for size in (1, 31):
            with self.subTest(size=size):
                m = {'kernel_size': size, 'kernel_shape': 'rect',
                     'operations': [{'operation': 'close', 'iterations': 10}]}
                self.assertEqual(self.process(morphology=m).status_code, 200)

    def test_invalid_request_keeps_previous_session_result(self):
        self.process(morphology=morph(5, 'rect', ['close']))
        before = main.session_data[self.sid]['mask_morph'].copy()
        self.assertEqual(self.process(morphology=morph(4, 'rect', ['open'])).status_code, 400)
        self.assertTrue(np.array_equal(main.session_data[self.sid]['mask_morph'], before))


class TestC05_Legacy(PhaseCBase):
    def test_c_t05_legacy_payload(self):
        median = self.expected_median()
        d = self.process(morph_kernel=4, use_closing=True, use_opening=True).get_json()
        cfg = d['applied_config']
        self.assertEqual(cfg['branch'], 'legacy')
        self.assertEqual(cfg['morphology']['kernel_size'], 5)  # legacy: chẵn tự +1
        self.assertEqual(cfg['morphology']['kernel_shape'], 'ellipse')
        exp = MorphologyOperator(5, 'ellipse').apply_sequence(
            median, [('close', {'iterations': 1}), ('open', {'iterations': 1})])
        self.assertTrue(np.array_equal(decode_mask(d['mask_morph']), exp))

    def test_legacy_defaults(self):
        cfg = self.process().get_json()['applied_config']
        self.assertEqual(cfg['branch'], 'legacy')
        self.assertEqual([o['operation'] for o in cfg['morphology']['operations']], ['close'])

    def test_new_object_takes_precedence_over_legacy(self):
        d = self.process(morphology=morph(3, 'cross', ['dilate']), use_closing=True,
                         morph_kernel=9).get_json()
        cfg = d['applied_config']
        self.assertEqual(cfg['branch'], 'morphology')
        self.assertEqual(cfg['morphology']['kernel_size'], 3)
        self.assertTrue(cfg['warnings'])


class TestC06_RequestId(PhaseCBase):
    def test_request_id_echoed(self):
        d = self.process(morphology=morph(3, 'rect', ['close']), request_id=42).get_json()
        self.assertEqual(d['request_id'], 42)

    def test_request_id_absent(self):
        self.assertIsNone(self.process(morphology=morph(3, 'rect', ['close'])).get_json()['request_id'])


class TestC07_CompareSync(PhaseCBase):
    def compare(self, pipeline):
        cfgs = [{'config_id': f'c{i}', 'name': f'c{i}', 'source_preset': 'red',
                 'hsv': {'mode': 'hue', 'hue_ranges': [[0, 10]], 'saturation': [100, 255],
                         'value': [100, 255]}} for i in range(2)]
        return self.client.post('/api/compare-hsv', json={
            'session_id': self.sid, 'target_color_id': 'red', 'evaluation_stage': 'morph',
            'fixed_pipeline': pipeline, 'configurations': cfgs})

    def test_c_t07_compare_uses_shared_object(self):
        m = morph(5, 'cross', ['open', 'dilate'])
        r = self.compare({'median_kernel': 3, 'morphology': m})
        self.assertEqual(r.status_code, 200, r.get_json())
        fp = r.get_json()['fixed_pipeline']
        self.assertEqual(fp['morphology'], m)
        self.assertEqual(fp['kernel_shape'], 'cross')

    def test_compare_rejects_invalid_morphology(self):
        r = self.compare({'median_kernel': 3, 'morphology': morph(4, 'cross', ['open'])})
        self.assertEqual(r.status_code, 400)

    def test_legacy_fixed_pipeline_still_works(self):
        r = self.compare({'median_kernel': 3, 'morph_kernel': 5, 'kernel_shape': 'ellipse',
                          'operations': [{'op': 'close', 'iterations': 1}]})
        self.assertEqual(r.status_code, 200, r.get_json())
        fp = r.get_json()['fixed_pipeline']
        self.assertEqual(fp['morphology']['operations'], [{'operation': 'close', 'iterations': 1}])

    def test_compare_morph_matches_process_morph(self):
        m = morph(5, 'rect', ['close', 'erode'])
        proc = self.process(morphology=m).get_json()
        r = self.compare({'median_kernel': 3, 'morphology': m})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['fixed_pipeline']['morphology'],
                         proc['applied_config']['morphology'])


class TestC08_Static(unittest.TestCase):
    def test_c_t08_ui_markup_order_and_limits(self):
        client = main.app.test_client()
        html = client.get('/').get_data(as_text=True)
        ids = ['use_closing', 'use_opening', 'use_erosion', 'use_dilation']
        pos = [html.index(f'id="{i}"') for i in ids]
        self.assertEqual(pos, sorted(pos))
        for i in ('iter_close', 'iter_open', 'iter_erode', 'iter_dilate'):
            self.assertRegex(html, rf'id="{i}"[^>]*min="1"[^>]*max="10"')
        self.assertRegex(html, r'id="morph_kernel"[^>]*min="1"[^>]*max="31"')
        for shape in SHAPES:
            self.assertIn(f'value="{shape}"', html)
        self.assertIn('Sau Morphology', html)


if __name__ == '__main__':
    unittest.main()

