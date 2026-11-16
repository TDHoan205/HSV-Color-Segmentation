# -*- coding: utf-8 -*-
"""Phase E.4: integration test toàn API (Flask test_client).

Ghi file vào vùng riêng results/phase_e/<run>/it_uploads (không đụng uploads/, data/).
Ngưỡng 413/429 được kiểm bằng cách hạ giới hạn trong app test, không tạo file 50 MiB thật.
"""

import csv
import io
import json
import os
import time
import unittest
import zipfile

import cv2
import numpy as np

import main
from src.evaluation import SegmentationEvaluator

RUN_ID = os.environ.get('PHASE_E_RUN_ID', 'E-20261116-122128')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'results', 'phase_e', RUN_ID, 'it_uploads')


def png(img):
    ok, buf = cv2.imencode('.png', img)
    assert ok
    return buf.tobytes()


def make_image():
    img = np.full((60, 60, 3), 128, np.uint8)
    img[5:25, 5:25] = (0, 0, 255)
    img[35:55, 35:55] = (255, 0, 0)
    return img


def make_gt():
    gt = np.zeros((60, 60), np.uint8)
    gt[5:25, 5:25] = 255
    return gt


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(WORK, exist_ok=True)
        cls._old = main.app.config['UPLOAD_FOLDER']
        main.app.config['UPLOAD_FOLDER'] = WORK
        main.app.config['TESTING'] = True
        cls.client = main.app.test_client()
        cls._saved = (dict(main.session_data), dict(main.comparison_data))
        main.session_data.clear()
        main.comparison_data.clear()

    @classmethod
    def tearDownClass(cls):
        main.session_data.clear()
        main.comparison_data.clear()
        main.session_data.update(cls._saved[0])
        main.comparison_data.update(cls._saved[1])
        main.app.config['UPLOAD_FOLDER'] = cls._old

    def upload(self, img=None, name='a.png'):
        r = self.client.post('/api/upload', data={'image': (io.BytesIO(png(img if img is not None else make_image())), name)},
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        return r.get_json()['session_id']

    def process(self, sid, **kw):
        body = {'session_id': sid, 'color_id': 'red'}
        body.update(kw)
        r = self.client.post('/api/process', json=body)
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        return r.get_json()

    def evaluate(self, sid, gt=None):
        return self.client.post('/api/evaluate', data={
            'session_id': sid, 'ground_truth': (io.BytesIO(png(gt if gt is not None else make_gt())), 'gt.png')},
            content_type='multipart/form-data')


class TestRoutes(Base):
    def test_IT01_health_presets_index(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)
        presets = self.client.get('/api/color-presets').get_json()['presets']
        self.assertEqual(len(presets), 15)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_IT02_unknown_route_404(self):
        r = self.client.get('/api/khong-ton-tai')
        self.assertEqual(r.status_code, 404)
        self.assertIn('error', r.get_json())

    def test_IT03_session_id_is_unguessable_and_unique(self):
        a, b = self.upload(), self.upload()
        self.assertNotEqual(a, b)
        self.assertRegex(a, r'^s_[0-9a-f]{32}$')
        files = {main.session_data[s]['filepath'] for s in (a, b)}
        self.assertEqual(len(files), 2)

    def test_IT04_same_filename_not_overwritten(self):
        a = self.upload(name='same.png')
        b = self.upload(name='same.png')
        self.assertTrue(os.path.isfile(main.session_data[a]['filepath']))
        self.assertTrue(os.path.isfile(main.session_data[b]['filepath']))

    def test_IT05_upload_errors(self):
        c = self.client
        self.assertEqual(c.post('/api/upload', data={}, content_type='multipart/form-data').status_code, 400)
        r = c.post('/api/upload', data={'image': (io.BytesIO(b'not an image'), 'x.png')}, content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)
        r = c.post('/api/upload', data={'image': (io.BytesIO(png(make_image())), 'x.exe')}, content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)
        # MIME/extension giả: đuôi .png nhưng nội dung text
        r = c.post('/api/upload', data={'image': (io.BytesIO(b'<script>alert(1)</script>'), 'x.png')}, content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)
        self.assertNotIn('Traceback', r.get_data(as_text=True))

    def test_IT06_unicode_and_traversal_filename(self):
        for name in ('ảnh đỏ có dấu.png', '..\\..\\evil.png', '../../evil.png', 'a b c.png'):
            sid = self.upload(name=name)
            path = os.path.abspath(main.session_data[sid]['filepath'])
            self.assertTrue(path.startswith(os.path.abspath(WORK) + os.sep), path)
        self.assertFalse(os.path.exists(os.path.join(ROOT, 'evil.png')))

    def test_IT07_pixel_budget_413_before_decode(self):
        old = main.MAX_DECODED_PIXELS
        main.MAX_DECODED_PIXELS = 1000
        try:
            r = self.client.post('/api/upload', data={'image': (io.BytesIO(png(make_image())), 'big.png')},
                                 content_type='multipart/form-data')
            self.assertEqual(r.status_code, 413)
        finally:
            main.MAX_DECODED_PIXELS = old

    def test_IT08_max_content_length_413(self):
        old = main.app.config.get('MAX_CONTENT_LENGTH')
        main.app.config['MAX_CONTENT_LENGTH'] = 1024
        try:
            r = self.client.post('/api/upload', data={'image': (io.BytesIO(b'0' * 5000), 'x.png')},
                                 content_type='multipart/form-data')
            self.assertEqual(r.status_code, 413)
        finally:
            main.app.config['MAX_CONTENT_LENGTH'] = old

    def test_IT09_disk_free_guard(self):
        old = main.MIN_FREE_DISK_BYTES
        main.MIN_FREE_DISK_BYTES = 1 << 62
        try:
            r = self.client.post('/api/upload', data={'image': (io.BytesIO(png(make_image())), 'x.png')},
                                 content_type='multipart/form-data')
            self.assertEqual(r.status_code, 507)
        finally:
            main.MIN_FREE_DISK_BYTES = old

    def test_IT10_process_matches_direct_modules(self):
        from src.hsv_segment import HSVSegmenter, get_color_preset
        from src.median_filter import MedianFilter
        sid = self.upload()
        res = self.process(sid, median_kernel=5)
        p = get_color_preset('red')
        seg = HSVSegmenter({'color_name': 'Red', 'hue_ranges': p['hue_ranges'],
                            'saturation': p['saturation'], 'value': p['value']})
        raw, _ = seg.segment(make_image())
        med = MedianFilter(5).filter(raw)
        e = main.session_data[sid]
        np.testing.assert_array_equal(e['mask_raw'], raw)
        np.testing.assert_array_equal(e['mask_median'], med)
        self.assertEqual(res['white_pixels']['raw'], int(np.sum(raw > 0)))

    def test_IT11_malformed_requests_4xx(self):
        c = self.client
        for route in ('/api/process', '/api/download-mask', '/api/export-results', '/api/release-session'):
            for body in (None, [], 'x', 5):
                r = c.post(route, data=json.dumps(body), content_type='application/json')
                self.assertEqual(r.status_code, 400, (route, body))
            r = c.post(route, data='{bad json', content_type='application/json')
            self.assertEqual(r.status_code, 400, route)
        r = c.post('/api/process', json={'session_id': 'nope'})
        self.assertEqual(r.status_code, 400)
        r = c.post('/api/process', json={'session_id': None})
        self.assertEqual(r.status_code, 400)
        sid = self.upload()
        for bad in ({'h_min_1': 'abc'}, {'median_kernel': 'x'}, {'color_id': 'zzz'}, {'morphology': 'x'}):
            r = c.post('/api/process', json=dict({'session_id': sid, 'color_id': 'red'}, **bad))
            self.assertEqual(r.status_code, 400, bad)
            self.assertNotIn('Traceback', r.get_data(as_text=True))

    def test_IT12_evaluate_before_process_and_get_info(self):
        sid = self.upload()
        self.assertEqual(self.evaluate(sid).status_code, 400)
        self.assertEqual(self.client.get('/api/get-info', query_string={'session_id': sid}).status_code, 400)
        self.assertEqual(self.client.post('/api/download-mask', json={'session_id': sid}).status_code, 400)
        self.assertEqual(self.client.post('/api/export-results', json={'session_id': sid}).status_code, 400)
        self.process(sid)
        self.assertEqual(self.client.get('/api/get-info', query_string={'session_id': sid}).status_code, 200)
        self.assertEqual(self.client.post('/api/download-mask', json={'session_id': sid, 'mask_type': '../x'}).status_code, 400)
        r = self.client.post('/api/download-mask', json={'session_id': sid, 'mask_type': 'raw'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(cv2.imdecode(np.frombuffer(r.data, np.uint8), cv2.IMREAD_UNCHANGED).shape, (60, 60))


class TestGroundTruth(Base):
    def test_IT20_strict_gt_rejections(self):
        sid = self.upload()
        self.process(sid)
        gt = make_gt()
        cases = {
            'size': cv2.resize(gt, (30, 30), interpolation=cv2.INTER_NEAREST),
            'gray_values': np.where(gt > 0, 200, 0).astype(np.uint8),
            'three_channel': cv2.cvtColor(gt, cv2.COLOR_GRAY2BGR),
            'uint16': gt.astype(np.uint16),
        }
        for name, arr in cases.items():
            r = self.evaluate(sid, arr)
            self.assertEqual(r.status_code, 400, name)
            self.assertNotIn('metrics', r.get_json())
            self.assertNotIn('metrics', main.session_data[sid], name)
        # không phải PNG
        ok, jpg = cv2.imencode('.jpg', gt)
        r = self.client.post('/api/evaluate', data={'session_id': sid, 'ground_truth': (io.BytesIO(jpg.tobytes()), 'g.png')},
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/evaluate', data={'session_id': sid, 'ground_truth': (io.BytesIO(b''), 'g.png')},
                             content_type='multipart/form-data')
        self.assertEqual(r.status_code, 400)

    def test_IT21_metrics_equal_evaluator_and_no_gt_written_to_disk(self):
        sid = self.upload()
        self.process(sid)
        before = set(os.listdir(WORK))
        r = self.evaluate(sid)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(os.listdir(WORK)), before)
        exp = SegmentationEvaluator().compute_metrics(main.session_data[sid]['mask_morph'], make_gt())
        for k in ('pixel_accuracy', 'iou', 'precision', 'recall', 'f1'):
            self.assertAlmostEqual(r.get_json()['metrics'][k], exp[k], delta=1e-9)

    def test_IT22_reprocess_invalidates_stale_metrics(self):
        sid = self.upload()
        r1 = self.process(sid)
        self.assertEqual(self.evaluate(sid).status_code, 200)
        self.assertIn('metrics', main.session_data[sid])
        r2 = self.process(sid, color_id='blue')
        self.assertGreater(r2['run_id'], r1['run_id'])
        for k in ('metrics', 'gt_mask', 'visualization', 'gt_sha256'):
            self.assertNotIn(k, main.session_data[sid])
        z = zipfile.ZipFile(io.BytesIO(self.client.post('/api/export-results', json={'session_id': sid}).data))
        self.assertNotIn('visualization.png', z.namelist())
        run = json.loads(z.read('run.json'))
        self.assertFalse(run['has_ground_truth'])
        self.assertEqual(run['run_id'], r2['run_id'])

    def test_IT23_failed_process_keeps_previous_run(self):
        sid = self.upload()
        r1 = self.process(sid)
        self.assertEqual(self.evaluate(sid).status_code, 200)
        bad = self.client.post('/api/process', json={'session_id': sid, 'color_id': 'zzz'})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(main.session_data[sid]['run_id'], r1['run_id'])
        self.assertIn('metrics', main.session_data[sid])


class TestExport(Base):
    def _zip(self, sid, **extra):
        r = self.client.post('/api/export-results', json=dict({'session_id': sid}, **extra))
        self.assertEqual(r.status_code, 200, r.data[:200].decode('utf-8', 'replace') if r.status_code != 200 else '')
        return zipfile.ZipFile(io.BytesIO(r.data))

    def test_IT30_export_round_trip_with_gt(self):
        sid = self.upload()
        res = self.process(sid)
        ev = self.evaluate(sid).get_json()
        z = self._zip(sid, run_id=res['run_id'])
        names = set(z.namelist())
        for n in ('mask_raw.png', 'mask_median.png', 'mask_morph.png', 'segmented.png', 'visualization.png',
                  'config.json', 'run.json', 'metrics.json', 'metrics.csv'):
            self.assertIn(n, names)
        e = main.session_data[sid]
        for st in ('raw', 'median', 'morph'):
            m = cv2.imdecode(np.frombuffer(z.read(f'mask_{st}.png'), np.uint8), cv2.IMREAD_UNCHANGED)
            np.testing.assert_array_equal(m, e[f'mask_{st}'])
            self.assertTrue(set(np.unique(m)) <= {0, 255})
        seg = cv2.imdecode(np.frombuffer(z.read('segmented.png'), np.uint8), cv2.IMREAD_COLOR)
        self.assertEqual(seg.shape, (60, 60, 3))
        self.assertTrue(np.all(seg[e['mask_morph'] == 0] == 0))
        mj = json.loads(z.read('metrics.json'))
        for k in ('pixel_accuracy', 'iou', 'precision', 'recall', 'f1'):
            self.assertAlmostEqual(mj[k], ev['metrics'][k], delta=1e-9)
        raw_csv = z.read('metrics.csv')
        self.assertTrue(raw_csv.startswith(b'\xef\xbb\xbf'))
        rows = list(csv.reader(io.StringIO(raw_csv.decode('utf-8-sig'))))
        vals = {r[1]: float(r[2]) for r in rows[1:] if r[1] in ('iou', 'f1')}
        self.assertAlmostEqual(vals['iou'], ev['metrics']['iou'], delta=1e-9)
        run = json.loads(z.read('run.json'))
        self.assertEqual(run['run_id'], res['run_id'])
        self.assertTrue(run['has_ground_truth'])
        self.assertEqual(len(run['gt_sha256']), 64)
        cfg = json.loads(z.read('config.json'))
        self.assertEqual(cfg['pipeline'], res['applied_config'])

    def test_IT31_export_without_gt_is_na(self):
        sid = self.upload()
        self.process(sid)
        z = self._zip(sid)
        self.assertNotIn('visualization.png', z.namelist())
        self.assertEqual(json.loads(z.read('metrics.json'))['status'], 'N/A')
        self.assertIn('N/A', z.read('metrics.csv').decode('utf-8-sig'))
        self.assertFalse(json.loads(z.read('run.json'))['has_ground_truth'])

    def test_IT32_export_wrong_run_id_409(self):
        sid = self.upload()
        res = self.process(sid)
        r = self.client.post('/api/export-results', json={'session_id': sid, 'run_id': res['run_id'] + 5})
        self.assertEqual(r.status_code, 409)

    def test_IT33_csv_injection_escaped(self):
        self.assertEqual(main._csv_safe('=1+1'), "'=1+1")
        for s in ('+a', '-a', '@a', '\tx', '\rx'):
            self.assertTrue(main._csv_safe(s).startswith("'"))
        self.assertEqual(main._csv_safe('ok'), 'ok')
        data = main._csv_bytes([['=cmd|calc', '+x', 1.5]])
        self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        self.assertIn("'=cmd|calc", data.decode('utf-8-sig'))

    def test_IT34_zip_names_safe(self):
        sid = self.upload(name='..\\..\\=evil.png')
        self.process(sid)
        z = self._zip(sid)
        for n in z.namelist():
            self.assertFalse(n.startswith('/') or '..' in n.split('/'), n)
        self.assertNotIn('..', json.loads(z.read('run.json'))['image_filename'].replace('...', ''))

    def test_IT35_comparison_export_round_trip(self):
        sid = self.upload()
        hsv = lambda hr: {'mode': 'hue', 'hue_ranges': hr, 'saturation': [100, 255], 'value': [100, 255]}
        cfgs = [{'config_id': 'red', 'name': 'red', 'source_preset': None, 'hsv': hsv([[0, 10], [170, 179]])},
                {'config_id': 'blue', 'name': 'blue', 'source_preset': None, 'hsv': hsv([[100, 130]])}]
        r = self.client.post('/api/compare-hsv', json={'session_id': sid, 'target_color_id': 'red', 'configurations': cfgs,
                                                       'evaluation_stage': 'morph'})
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        cid = r.get_json()['comparison_id']
        r = self.client.post('/api/compare-hsv/evaluate', data={
            'session_id': sid, 'comparison_id': cid, 'gt_pair_confirmed': 'true',
            'ground_truth': (io.BytesIO(png(make_gt())), 'gt.png')}, content_type='multipart/form-data')
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        z = self._zip(sid, comparison_id=cid)
        names = set(z.namelist())
        self.assertIn('comparison.json', names)
        self.assertIn('metrics.csv', names)
        self.assertIn('masks/red_morph.png', names)
        self.assertIn('segmented/red_morph.png', names)
        self.assertIn('visualization/red_morph.png', names)
        self.assertTrue(z.read('metrics.csv').startswith(b'\xef\xbb\xbf'))
        # xuất B cũ vẫn đọc được
        r = self.client.post('/api/compare-hsv/export', json={'session_id': sid, 'comparison_id': cid})
        self.assertEqual(r.status_code, 200)
        self.assertIn('comparison.json', zipfile.ZipFile(io.BytesIO(r.data)).namelist())

    def test_IT36_comparison_without_gt_exports_na(self):
        sid = self.upload()
        cfgs = [{'config_id': 'a', 'name': 'a', 'source_preset': None,
                 'hsv': {'mode': 'hue', 'hue_ranges': [[0, 10]], 'saturation': [100, 255], 'value': [100, 255]}},
                {'config_id': 'b', 'name': 'b', 'source_preset': None,
                 'hsv': {'mode': 'hue', 'hue_ranges': [[100, 130]], 'saturation': [100, 255], 'value': [100, 255]}}]
        cid = self.client.post('/api/compare-hsv', json={'session_id': sid, 'target_color_id': 'red',
                                                         'configurations': cfgs}).get_json()['comparison_id']
        z = self._zip(sid, comparison_id=cid)
        self.assertIn('N/A', z.read('metrics.csv').decode('utf-8-sig'))
        self.assertFalse([n for n in z.namelist() if n.startswith('visualization/')])


class TestSession(Base):
    def test_IT40_isolation(self):
        a = self.upload()
        b = self.upload(np.full((40, 40, 3), 50, np.uint8))
        ra, rb = self.process(a), self.process(b)
        self.assertEqual(ra['image_dimensions']['width'], 60)
        self.assertEqual(rb['image_dimensions']['width'], 40)
        self.assertEqual(self.evaluate(a).status_code, 200)
        self.assertNotIn('metrics', main.session_data[b])
        za = zipfile.ZipFile(io.BytesIO(self.client.post('/api/export-results', json={'session_id': a}).data))
        zb = zipfile.ZipFile(io.BytesIO(self.client.post('/api/export-results', json={'session_id': b}).data))
        self.assertIn('visualization.png', za.namelist())
        self.assertNotIn('visualization.png', zb.namelist())

    def test_IT41_ttl_expiry_message_and_file_removed_only_for_that_session(self):
        a, b = self.upload(), self.upload()
        pa, pb = main.session_data[a]['filepath'], main.session_data[b]['filepath']
        main.session_data[a]['last_access'] -= main.SESSION_TTL_SECONDS + 5
        r = self.client.post('/api/process', json={'session_id': a, 'color_id': 'red'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('hết hạn', r.get_json()['error'])
        self.assertNotIn(a, main.session_data)
        self.assertFalse(os.path.exists(pa))
        self.assertTrue(os.path.exists(pb))
        self.assertEqual(self.client.post('/api/process', json={'session_id': b, 'color_id': 'red'}).status_code, 200)

    def test_IT42_session_count_limit_lru(self):
        sids = [self.upload() for _ in range(main.MAX_SESSIONS + 2)]
        self.assertLessEqual(len(main.session_data), main.MAX_SESSIONS)
        self.assertIn(sids[-1], main.session_data)
        self.assertNotIn(sids[0], main.session_data)

    def test_IT43_byte_budget(self):
        old = main.MAX_SESSION_BYTES_TOTAL
        main.MAX_SESSION_BYTES_TOTAL = 10_000
        try:
            r = self.client.post('/api/upload', data={'image': (io.BytesIO(png(make_image())), 'x.png')},
                                 content_type='multipart/form-data')
            self.assertEqual(r.status_code, 413)
            self.assertNotIn('Traceback', r.get_data(as_text=True))
        finally:
            main.MAX_SESSION_BYTES_TOTAL = old

    def test_IT44_release_session(self):
        sid = self.upload()
        path = main.session_data[sid]['filepath']
        r = self.client.post('/api/release-session', json={'session_id': sid})
        self.assertTrue(r.get_json()['released'])
        self.assertFalse(os.path.exists(path))
        self.assertEqual(self.client.post('/api/process', json={'session_id': sid}).status_code, 400)

    def test_IT45_response_ordering_request_id_echo(self):
        sid = self.upload()
        r1 = self.process(sid, request_id=11)
        r2 = self.process(sid, request_id=12)
        self.assertEqual((r1['request_id'], r2['request_id']), (11, 12))
        self.assertGreater(r2['run_id'], r1['run_id'])

    def test_IT46_no_traceback_or_path_in_errors(self):
        orig = main.HSVSegmenter.segment
        main.HSVSegmenter.segment = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('C:\\secret\\path'))
        try:
            sid = self.upload()
            r = self.client.post('/api/process', json={'session_id': sid, 'color_id': 'red'})
            self.assertEqual(r.status_code, 500)
            text = r.get_data(as_text=True)
            self.assertNotIn('secret', text)
            self.assertNotIn('Traceback', text)
        finally:
            main.HSVSegmenter.segment = orig


class TestOperations(unittest.TestCase):
    def test_IT50_entrypoint_localhost_debug_off(self):
        src = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
        self.assertIn("debug=False, host='127.0.0.1'", src)
        self.assertNotIn("host='0.0.0.0'", src)

    def test_IT51_limits_declared(self):
        self.assertEqual(main.SESSION_TTL_SECONDS, 1800)
        self.assertEqual(main.MAX_SESSIONS, 5)
        self.assertEqual(main.MAX_DECODED_PIXELS, 25_000_000)
        self.assertEqual(main.MAX_SESSION_BYTES_TOTAL, 1 << 30)
        self.assertEqual(main.app.config['MAX_CONTENT_LENGTH'], 50 * 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
