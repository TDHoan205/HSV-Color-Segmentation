#!/usr/bin/env python
"""Phase E.7 - Đánh giá final_test với baseline/config đã khoá ở Phase D.

Quy tắc:
  * Chỉ ĐỌC data/, không ghi vào dataset/GT/manifest/freeze.
  * Xác minh hash freeze D trước. Sai hash/thiếu file/freeze PARTIAL_BLOCKED/final_test rỗng
    -> dừng nhánh đánh giá, ghi trạng thái trung thực, exit code 2 (báo về Phase D).
  * Không tuning theo điểm final_test; không bỏ ca lỗi (ca lỗi được ghi vào kết quả).

Dùng: python scripts/run_final_evaluation.py --run-id E-... [--out results/phase_e/<run_id>]
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FREEZE = os.path.join(ROOT, 'data', 'dataset_freeze.json')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_freeze(freeze):
    """Trả về (danh sách lỗi, danh sách kiểm tra đã làm)."""
    errors, checks = [], []
    for name, ref in freeze.get('files', {}).items():
        p = os.path.join(ROOT, ref['path'])
        if not os.path.isfile(p):
            errors.append(f'{name}: thiếu file {ref["path"]}')
            continue
        actual = sha256_file(p)
        ok = actual == ref['sha256']
        checks.append({'item': name, 'path': ref['path'], 'ok': ok})
        if not ok:
            errors.append(f'{name}: hash lệch ({ref["path"]})')
    return errors, checks


def load_manifest():
    with open(os.path.join(ROOT, 'data', 'dataset_manifest.csv'), encoding='utf-8-sig', newline='') as fh:
        return {r['sample_id']: r for r in csv.DictReader(fh)}


def verify_final_samples(freeze, manifest):
    errors = []
    by_id = {s['sample_id']: s for s in freeze['samples']}
    for sid in freeze['split'].get('final_test', []):
        s, m = by_id.get(sid), manifest.get(sid)
        if not s or not m:
            errors.append(f'{sid}: không có trong freeze/manifest')
            continue
        ip = os.path.join(ROOT, m['image_path'])
        gp = os.path.join(ROOT, m['gt_path']) if m['gt_path'] else ''
        if not os.path.isfile(ip) or sha256_file(ip) != s['image_sha256']:
            errors.append(f'{sid}: ảnh thiếu hoặc hash lệch')
        if not gp or not os.path.isfile(gp) or sha256_file(gp) != s['gt_sha256']:
            errors.append(f'{sid}: GT thiếu hoặc hash lệch')
        if s.get('status') != 'approved':
            errors.append(f'{sid}: status {s.get("status")} không phải approved')
    return errors


def evaluate_final(freeze, manifest):
    import cv2
    import numpy as np
    import main as app
    from src.evaluation import SegmentationEvaluator

    sel_path = os.path.join(ROOT, freeze['tuning']['selected_configs_path'])
    if sha256_file(sel_path) != freeze['tuning']['selected_configs_sha256']:
        raise RuntimeError('selected_configs hash lệch')
    with open(sel_path, encoding='utf-8') as fh:
        selected = json.load(fh)['selected']
    pipeline = freeze['pipeline']
    rows = []
    for sid in freeze['split']['final_test']:
        m = manifest[sid]
        row = {'sample_id': sid, 'color': m['target_color_id'], 'status': 'ok', 'error': ''}
        try:
            cfg = selected[m['target_color_id']]
            img = cv2.imdecode(np.fromfile(os.path.join(ROOT, m['image_path']), np.uint8), cv2.IMREAD_COLOR)
            with open(os.path.join(ROOT, m['gt_path']), 'rb') as fh:
                gt = app.read_strict_gt(fh.read(), img.shape[:2])
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            _, _, morph = app.run_pipeline_for_config(hsv, cfg['hsv'], pipeline)
            row.update(SegmentationEvaluator().compute_metrics(morph, gt))
        except Exception as e:  # ca lỗi được ghi, không bỏ
            row.update(status='error', error=type(e).__name__)
        rows.append(row)
    ok = [r for r in rows if r['status'] == 'ok']
    summary = {}
    for k in ('iou', 'f1', 'precision', 'recall', 'pixel_accuracy'):
        summary[f'macro_{k}'] = sum(r[k] for r in ok) / len(ok) if ok else None
    return rows, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(ROOT, 'results', 'phase_e', args.run_id)
    os.makedirs(out, exist_ok=True)

    result = {
        'run_id': args.run_id,
        'time': datetime.now(timezone.utc).isoformat(),
        'freeze_path': 'data/dataset_freeze.json',
        'freeze_sha256': sha256_file(FREEZE),
        'status': None,
        'blockers': [],
        'hash_checks': [],
        'per_sample': [],
        'summary': None,
    }
    with open(FREEZE, encoding='utf-8') as fh:
        freeze = json.load(fh)
    result['freeze_status'] = freeze.get('status')
    result['freeze_run_id'] = freeze.get('run_id')

    errors, checks = verify_freeze(freeze)
    result['hash_checks'] = checks
    manifest = load_manifest()
    if freeze.get('status') != 'FROZEN':
        errors.append(f'freeze status = {freeze.get("status")}: {freeze.get("blocker", "")}')
    if not freeze['split'].get('final_test'):
        errors.append('final_test rỗng: không có mẫu thật approved để đánh giá')
    if not errors:
        errors += verify_final_samples(freeze, manifest)

    if errors:
        result['status'] = 'BLOCKED_DEPENDENCY_PHASE_D'
        result['blockers'] = errors
        result['note'] = 'Nhánh đánh giá real final_test đã DỪNG; không có số liệu giả. Báo về Phase D.'
    else:
        rows, summary = evaluate_final(freeze, manifest)
        result['per_sample'] = rows
        result['summary'] = summary
        result['status'] = 'COMPLETED' if all(r['status'] == 'ok' for r in rows) else 'COMPLETED_WITH_ERRORS'

    with open(os.path.join(out, 'final_evaluation.json'), 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in ('status', 'freeze_status', 'blockers')}, ensure_ascii=False, indent=2))
    return 0 if result['status'].startswith('COMPLETED') else 2


if __name__ == '__main__':
    sys.exit(main())
