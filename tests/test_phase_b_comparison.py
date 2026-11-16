# -*- coding: utf-8 -*-
"""Phase B: kiểm thử so sánh ngưỡng HSV (B-T01..B-T09) bằng dữ liệu tổng hợp.

Dữ liệu tổng hợp chỉ chứng minh logic chức năng, không đánh giá chất lượng trên ảnh thật.
Mọi file tạm nằm trong thư mục tạm riêng và được xóa khi kết thúc (không đụng uploads/, data/).
"""

import copy
import io
import json
import shutil
import tempfile
import unittest
import zipfile

import cv2
import numpy as np

import main
from src.hsv_segment import COLOR_IDS, COLOR_PRESETS
from src.evaluation import SegmentationEvaluator

PRESET_ROUTE = '/api/color-presets'
UPLOAD_ROUTE = '/api/upload'
PROCESS_ROUTE = '/api/process'
COMPARE_ROUTE = '/api/compare-hsv'
EVAL_ROUTE = '/api/compare-hsv/evaluate'
EXPORT_ROUTE = '/api/compare-hsv/export'
IMPORT_ROUTE = '/api/compare-hsv/import-config'
METRIC_KEYS = ('pixel_accuracy', 'iou', 'precision', 'recall', 'f1')


def _png_bytes(image):
    ok, buf = cv2.imencode('.png', image)
    assert ok
    return buf.tobytes()


def _png(image):
    return io.BytesIO(_png_bytes(image))


def _cfg(config_id, hue_ranges, s=(100, 255), v=(100, 255), mode='hue', source=None):
    return {
        'config_id': config_id, 'name': config_id, 'source_preset': source,
        'hsv': {'mode': mode, 'hue_ranges': [list(r) for r in hue_ranges],
                'saturation': list(s), 'value': list(v)},
    }


class PhaseBBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp()
        cls._old_upload = main.app.config['UPLOAD_FOLDER']
        main.app.config['UPLOAD_FOLDER'] = cls._tmp
        main.app.config['TESTING'] = True
        cls.client = main.app.test_client()
        # Nền xám, ô đỏ [5:25] (H=0), ô xanh dương [35:55] (H=120)
        img = np.full((60, 60, 3), 128, np.uint8)
        img[5:25, 5:25] = (0, 0, 255)
        img[35:55, 35:55] = (255, 0, 0)
        cls.image = img
        gt = np.zeros((60, 60), np.uint8)
        gt[5:25, 5:25] = 255
        cls.gt = gt
        cls.presets = {p['color_id']: p for p in cls.client.get(PRESET_ROUTE).get_json()['presets']}

    @classmethod
    def tearDownClass(cls):
        main.app.config['UPLOAD_FOLDER'] = cls._old_upload
        shutil.rmtree(cls._tmp, ignore_errors=True)

    # ---- helpers ----
    def upload(self, image=None):
        image = self.image if image is None else image
        resp = self.client.post(UPLOAD_ROUTE, data={'image': (_png(image), 'test.png')},
                                content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()['session_id']

    def red_cfg(self, config_id='red'):
        p = self.presets['red']
        return _cfg(config_id, p['hue_ranges'], p['saturation'], p['value'], p['mode'], 'red')

    def blue_cfg(self, config_id='blue'):
        return _cfg(config_id, [[100, 130]])

    def all_cfg(self, config_id='all'):
        return _cfg(config_id, [[0, 179]], (0, 255), (0, 255))

    def compare(self, sid, configs, **extra):
        body = {'session_id': sid, 'target_color_id': 'red', 'configurations': configs,
                'evaluation_stage': 'raw'}
        body.update(extra)
        return self.client.post(COMPARE_ROUTE, json=body)

    def evaluate(self, sid, cid, gt_bytes=None, confirmed=True, stage=None):
        form = {'session_id': sid, 'comparison_id': cid}
        if stage:
            form['evaluation_stage'] = stage
        if gt_bytes is not None:
            form['ground_truth'] = (io.BytesIO(gt_bytes), 'gt.png')
            if confirmed:
                form['gt_pair_confirmed'] = 'true'
        return self.client.post(EVAL_ROUTE, data=form, content_type='multipart/form-data')

    def export_zip(self, sid, cid):
        resp = self.client.post(EXPORT_ROUTE, json={'session_id': sid, 'comparison_id': cid})
        self.assertEqual(resp.status_code, 200)
        return zipfile.ZipFile(io.BytesIO(resp.data))

    @staticmethod
    def zip_mask(archive, name):
        return cv2.imdecode(np.frombuffer(archive.read(name), np.uint8), cv2.IMREAD_UNCHANGED)

    def comparisons(self, sid):
        return main.comparison_data.get(sid, {})


class TestBT01Count(PhaseBBase):
    def test_2_3_6_accepted(self):
        sid = self.upload()
        pool = [self.red_cfg('a'), self.blue_cfg('b'), self.all_cfg('c'),
                _cfg('d', [[0, 5]]), _cfg('e', [[6, 10]]), _cfg('f', [[11, 20]])]
        for n in (2, 3, 6):
            resp = self.compare(sid, pool[:n])
            self.assertEqual(resp.status_code, 200, resp.get_json())
            self.assertEqual(len(resp.get_json()['results']), n)

    def test_1_and_7_and_0_rejected_without_state(self):
        sid = self.upload()
        pool = [_cfg('c%d' % i, [[i, i + 1]]) for i in range(7)]
        for n in (0, 1, 7):
            self.assertEqual(self.compare(sid, pool[:n]).status_code, 400)
        self.assertEqual(self.comparisons(sid), {})


class TestBT02Presets(PhaseBBase):
    def test_preset_modes(self):
        self.assertEqual(len(self.presets['red']['hue_ranges']), 2)
        self.assertEqual(len(self.presets['green']['hue_ranges']), 1)
        for cid in ('white', 'black', 'gray'):
            self.assertEqual(self.presets[cid]['mode'], 'sv')

    def test_sv_mode_forces_full_hue_and_presets_unchanged(self):
        before = copy.deepcopy(COLOR_PRESETS)
        sid = self.upload()
        p = self.presets['white']
        cfg = _cfg('w', [[10, 20]], p['saturation'], p['value'], 'sv', 'white')
        resp = self.compare(sid, [cfg, self.red_cfg()], target_color_id='white')
        self.assertEqual(resp.status_code, 200, resp.get_json())
        applied = resp.get_json()['results'][0]['applied_config']['hsv']
        self.assertEqual(applied['hue_ranges'], [[0, 179]])
        self.assertFalse(applied['hue_applied'])
        self.assertEqual(COLOR_PRESETS, before)
        after = {x['color_id']: x for x in self.client.get(PRESET_ROUTE).get_json()['presets']}
        self.assertEqual(after, self.presets)


class TestBT03Fairness(PhaseBBase):
    def test_identical_configs_identical_masks_and_source_unchanged(self):
        sid = self.upload()
        snapshot = main.session_data[sid]['image_bgr'].copy()
        resp = self.compare(sid, [self.red_cfg('x'), self.red_cfg('y')])
        self.assertEqual(resp.status_code, 200)
        cid = resp.get_json()['comparison_id']
        res = {r['config_id']: r for r in self.comparisons(sid)[cid]['results']}
        for stage in ('raw', 'median', 'morph'):
            self.assertTrue(np.array_equal(res['x']['masks'][stage], res['y']['masks'][stage]))
        self.assertTrue(np.array_equal(main.session_data[sid]['image_bgr'], snapshot))

    def test_different_configs_differ_and_share_pipeline(self):
        sid = self.upload()
        resp = self.compare(sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()
        px = {r['config_id']: r['selected_pixels']['raw'] for r in resp['results']}
        self.assertEqual(px['r'], 400)
        self.assertEqual(px['b'], 400)
        self.assertIn('fixed_pipeline', resp)


class TestBT04Validation(PhaseBBase):
    def _bad(self, mutate):
        sid = self.upload()
        a, b = self.red_cfg('a'), self.blue_cfg('b')
        mutate(a, b)
        resp = self.compare(sid, [a, b])
        self.assertIn(resp.status_code, (400, 404, 409, 413), resp.get_json())
        self.assertEqual(self.comparisons(sid), {})

    def test_min_greater_than_max(self):
        self._bad(lambda a, b: b['hsv'].update(saturation=[200, 100]))

    def test_hue_180(self):
        self._bad(lambda a, b: b['hsv'].update(hue_ranges=[[100, 180]]))

    def test_float_value(self):
        self._bad(lambda a, b: b['hsv'].update(value=[10.5, 200]))

    def test_bool_value(self):
        self._bad(lambda a, b: b['hsv'].update(saturation=[True, 200]))

    def test_out_of_range_sv(self):
        self._bad(lambda a, b: b['hsv'].update(value=[0, 256]))

    def test_duplicate_config_id(self):
        self._bad(lambda a, b: b.update(config_id='a'))

    def test_bad_config_id(self):
        self._bad(lambda a, b: b.update(config_id='../x'))

    def test_unknown_source_preset(self):
        self._bad(lambda a, b: b.update(source_preset='nope'))

    def test_bad_target_and_stage_and_pipeline_and_session(self):
        sid = self.upload()
        cfgs = [self.red_cfg('a'), self.blue_cfg('b')]
        self.assertEqual(self.compare(sid, cfgs, target_color_id='zzz').status_code, 400)
        self.assertEqual(self.compare(sid, cfgs, evaluation_stage='x').status_code, 400)
        self.assertEqual(self.compare(sid, cfgs, fixed_pipeline={'median_kernel': 4}).status_code, 400)
        self.assertEqual(self.compare(sid, cfgs, fixed_pipeline={'operations': [{'op': 'bad'}]}).status_code, 400)
        self.assertEqual(self.compare('nope', cfgs).status_code, 404)
        self.assertEqual(self.comparisons(sid), {})


class TestBT05GroundTruth(PhaseBBase):
    def setUp(self):
        self.sid = self.upload()
        self.cid = self.compare(self.sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()['comparison_id']

    def test_no_gt_is_na_and_no_winner(self):
        ev = self.evaluate(self.sid, self.cid).get_json()['evaluation']
        self.assertEqual(ev['status'], 'no_ground_truth')
        self.assertIsNone(ev['best_config_ids'])
        self.assertIsNone(ev['ranking'])
        self.assertTrue(all(v is None for v in ev['metrics'].values()))

    def _rejected(self, data, confirmed=True):
        resp = self.evaluate(self.sid, self.cid, data, confirmed)
        self.assertEqual(resp.status_code, 400, resp.get_json())
        self.assertEqual(self.comparisons(self.sid)[self.cid]['evaluations'], {})

    def test_value_128_rejected(self):
        gt = self.gt.copy()
        gt[0, 0] = 128
        self._rejected(_png_bytes(gt))

    def test_rgb_rejected(self):
        self._rejected(_png_bytes(cv2.cvtColor(self.gt, cv2.COLOR_GRAY2BGR)))

    def test_wrong_size_rejected(self):
        self._rejected(_png_bytes(np.zeros((30, 30), np.uint8)))

    def test_uint16_rejected(self):
        self._rejected(_png_bytes(self.gt.astype(np.uint16)))

    def test_non_png_rejected(self):
        ok, buf = cv2.imencode('.jpg', self.gt)
        self._rejected(buf.tobytes())

    def test_unconfirmed_pair_rejected(self):
        self._rejected(_png_bytes(self.gt), confirmed=False)

    def test_mismatched_manifest_image_hash_rejected(self):
        form = {'session_id': self.sid, 'comparison_id': self.cid, 'gt_pair_confirmed': 'true',
                'gt_image_sha256': '0' * 64, 'ground_truth': (io.BytesIO(_png_bytes(self.gt)), 'gt.png')}
        resp = self.client.post(EVAL_ROUTE, data=form, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 400)

    def test_valid_gt_accepted(self):
        resp = self.evaluate(self.sid, self.cid, _png_bytes(self.gt))
        self.assertEqual(resp.status_code, 200, resp.get_json())
        self.assertEqual(resp.get_json()['evaluation']['status'], 'ok')

    def test_gt_not_modified(self):
        raw = _png_bytes(self.gt)
        ev = self.evaluate(self.sid, self.cid, raw).get_json()['evaluation']
        import hashlib
        self.assertEqual(ev['gt']['sha256'], hashlib.sha256(raw).hexdigest())


class TestBT06MetricsRanking(PhaseBBase):
    def test_metrics_match_evaluator_and_ranking(self):
        sid = self.upload()
        cid = self.compare(sid, [self.blue_cfg('b'), self.red_cfg('r'), self.all_cfg('all')]).get_json()['comparison_id']
        ev = self.evaluate(sid, cid, _png_bytes(self.gt)).get_json()['evaluation']
        record = self.comparisons(sid)[cid]
        evaluator = SegmentationEvaluator()
        for item in record['results']:
            expected = evaluator.compute_metrics(item['masks']['raw'], self.gt)
            got = ev['metrics'][item['config_id']]
            for k in METRIC_KEYS:
                self.assertLessEqual(abs(got[k] - expected[k]), 1e-9, k)
        ranks = {r['config_id']: r['rank'] for r in ev['ranking']}
        self.assertEqual(ranks['r'], 1)
        self.assertEqual(ev['best_config_ids'], ['r'])
        self.assertGreater(ranks['all'], 1)
        self.assertGreater(ranks['b'], 1)
        self.assertEqual(ev['ranking'][0]['config_id'], 'r')

    def test_tie_shares_rank_and_skips_next(self):
        sid = self.upload()
        cid = self.compare(sid, [self.red_cfg('r1'), self.red_cfg('r2'), self.blue_cfg('b')]).get_json()['comparison_id']
        ev = self.evaluate(sid, cid, _png_bytes(self.gt)).get_json()['evaluation']
        ranks = {r['config_id']: r['rank'] for r in ev['ranking']}
        self.assertEqual((ranks['r1'], ranks['r2'], ranks['b']), (1, 1, 3))
        self.assertEqual(sorted(ev['best_config_ids']), ['r1', 'r2'])

    def test_rank_function_iou_then_f1_exact_ties(self):
        # Cùng IoU 1/2 (TP=1,FP=1,FN=0 vs TP=1,FP=0,FN=1) và F1 cùng 2/3 -> đồng hạng
        m1 = {'TP': 1, 'FP': 1, 'FN': 0}
        m2 = {'TP': 1, 'FP': 0, 'FN': 1}
        m3 = {'TP': 2, 'FP': 1, 'FN': 1}   # IoU 1/2 nhưng F1 4/6 = 2/3 -> cũng bằng
        m4 = {'TP': 3, 'FP': 0, 'FN': 3}   # IoU 1/2, F1 2/3
        out = main.rank_configurations([('a', m1), ('b', m2), ('c', m3), ('d', m4)])
        self.assertTrue(all(r['rank'] == 1 for r in out))
        better = main.rank_configurations([('a', m1), ('z', {'TP': 5, 'FP': 0, 'FN': 0})])
        self.assertEqual({r['config_id']: r['rank'] for r in better}, {'z': 1, 'a': 2})

    def test_failed_config_means_no_winner(self):
        sid = self.upload()
        cid = self.compare(sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()['comparison_id']
        self.comparisons(sid)[cid]['results'][1]['status'] = 'error'
        ev = self.evaluate(sid, cid, _png_bytes(self.gt)).get_json()['evaluation']
        self.assertEqual(ev['status'], 'incomplete')
        self.assertIsNone(ev['best_config_ids'])
        self.assertIsNone(ev['ranking'])


class TestBT07Stale(unittest.TestCase):
    """Trạng thái cũ và request bất đồng bộ nằm ở app.js: kiểm tra bằng đối chiếu mã nguồn."""

    @classmethod
    def setUpClass(cls):
        with open('static/js/app.js', encoding='utf-8') as fh:
            cls.js = fh.read()
        with open('templates/index.html', encoding='utf-8') as fh:
            cls.html = fh.read()

    def test_stale_hooks_present(self):
        for token in ('cmpRequestSeq', 'cmpMarkStale', 'cmpRun', 'cmpEvaluate'):
            self.assertIn(token, self.js)
        upload_body = self.js.split('function uploadImage')[1].split('function processImage')[0]
        self.assertIn('cmpMarkStale(', upload_body)

    def test_out_of_order_responses_ignored(self):
        self.assertRegex(self.js, r'seq\s*!==\s*cmpRequestSeq|cmpRequestSeq\s*!==\s*seq')

    def test_html_has_compare_section(self):
        self.assertIn('id="compare"', self.html)


class TestBT08ExportImport(PhaseBBase):
    def test_export_zip_contents(self):
        sid = self.upload()
        cid = self.compare(sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()['comparison_id']
        self.evaluate(sid, cid, _png_bytes(self.gt))
        z = self.export_zip(sid, cid)
        names = z.namelist()
        self.assertIn('comparison.json', names)
        for c in ('r', 'b'):
            for s in ('raw', 'median', 'morph'):
                self.assertIn(f'masks/{c}_{s}.png', names)
        doc = json.loads(z.read('comparison.json'))
        self.assertEqual(doc['schema_version'], 1)
        self.assertEqual(len(doc['configurations']), 2)
        self.assertNotIn(self._tmp, json.dumps(doc))
        rec = self.comparisons(sid)[cid]
        mask = self.zip_mask(z, 'masks/r_raw.png')
        self.assertTrue(np.array_equal(mask, rec['results'][0]['masks']['raw']))

    def test_export_unknown_comparison(self):
        sid = self.upload()
        resp = self.client.post(EXPORT_ROUTE, json={'session_id': sid, 'comparison_id': 'x'})
        self.assertEqual(resp.status_code, 404)

    def _import(self, sid, raw):
        return self.client.post(IMPORT_ROUTE, data={'session_id': sid, 'config_file': (io.BytesIO(raw), 'c.json')},
                                content_type='multipart/form-data')

    def test_import_same_image_reruns(self):
        sid = self.upload()
        cid = self.compare(sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()['comparison_id']
        self.evaluate(sid, cid, _png_bytes(self.gt))
        doc = self.export_zip(sid, cid).read('comparison.json')
        sid2 = self.upload()
        resp = self._import(sid2, doc)
        self.assertEqual(resp.status_code, 200, resp.get_json())
        body = resp.get_json()
        self.assertTrue(body['import']['image_hash_match'])
        self.assertNotEqual(body['comparison_id'], cid)
        self.assertEqual(body['evaluations'], {})          # metrics cũ không thành kết quả mới
        self.assertEqual(len(body['results']), 2)

    def test_import_different_image_hash_mismatch(self):
        sid = self.upload()
        cid = self.compare(sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()['comparison_id']
        self.evaluate(sid, cid, _png_bytes(self.gt))
        doc = self.export_zip(sid, cid).read('comparison.json')
        other = self.image.copy()
        other[0, 0] = (1, 2, 3)
        sid2 = self.upload(other)
        body = self._import(sid2, doc).get_json()
        self.assertFalse(body['import']['image_hash_match'])
        self.assertIsNotNone(body['import']['warning'])
        self.assertIsNone(body['import']['historical_metrics'])
        self.assertEqual(body['evaluations'], {})

    def test_import_rejects_bad_input(self):
        sid = self.upload()
        self.assertEqual(self._import(sid, b'PK\x03\x04zip').status_code, 400)
        self.assertEqual(self._import(sid, b'not json').status_code, 400)
        self.assertEqual(self._import(sid, b'{"schema_version": 2}').status_code, 400)
        bad = json.dumps({'schema_version': 1, 'target_color_id': 'red', 'image': {'sha256': 'a'},
                          'configurations': [self.red_cfg('a')]}).encode()
        self.assertEqual(self._import(sid, bad).status_code, 400)
        self.assertEqual(self._import(sid, b' ' * (1024 * 1024 + 1)).status_code, 413)
        self.assertEqual(self.comparisons(sid), {})


class TestBT09Isolation(PhaseBBase):
    def test_process_does_not_touch_comparison_and_vice_versa(self):
        sid = self.upload()
        cid = self.compare(sid, [self.red_cfg('r'), self.blue_cfg('b')]).get_json()['comparison_id']
        record_snapshot = {k: copy.deepcopy(v) for k, v in self.comparisons(sid)[cid].items()
                           if k != 'results'}
        mask_before = self.comparisons(sid)[cid]['results'][0]['masks']['raw'].copy()
        self.assertNotIn('mask_raw', main.session_data[sid])     # so sánh không ghi session_data
        resp = self.client.post(PROCESS_ROUTE, json={'session_id': sid, 'color_id': 'green'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('mask_raw', main.session_data[sid])
        rec = self.comparisons(sid)[cid]
        self.assertEqual({k: v for k, v in rec.items() if k != 'results'}, record_snapshot)
        self.assertTrue(np.array_equal(rec['results'][0]['masks']['raw'], mask_before))
        raw_single = main.session_data[sid]['mask_raw'].copy()
        self.compare(sid, [self.red_cfg('x'), self.blue_cfg('y')])
        self.assertTrue(np.array_equal(main.session_data[sid]['mask_raw'], raw_single))
        self.assertEqual(len(self.comparisons(sid)), 2)


class TestRegressionPhaseA(PhaseBBase):
    def test_presets_endpoint_and_process_legacy(self):
        self.assertGreaterEqual(len(self.presets), 8)
        sid = self.upload()
        self.assertEqual(self.client.post(PROCESS_ROUTE, json={'session_id': sid}).status_code, 200)
        self.assertEqual(self.client.post(PROCESS_ROUTE, json={'session_id': sid, 'color_id': 'zzz'}).status_code, 400)
        self.assertEqual(self.client.get('/api/health').status_code, 200)


if __name__ == '__main__':
    unittest.main()
