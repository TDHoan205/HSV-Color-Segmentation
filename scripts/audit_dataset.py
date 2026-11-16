# -*- coding: utf-8 -*-
"""
Script: audit_dataset.py (Phase D, D.1)
Kiểm kê CHỈ ĐỌC toàn bộ ảnh / GT / metadata. Không resize, không threshold, không sửa file.
Kết quả ghi vào results/phase_d/<run_id>/ (run_id mới; từ chối ghi đè).

Dùng:  python scripts/audit_dataset.py --run-id D-YYYYMMDD-HHMMSS
"""

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def dhash(img, size=8):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    s = cv2.resize(g, (size + 1, size), interpolation=cv2.INTER_AREA)
    bits = (s[:, 1:] > s[:, :-1]).flatten()
    return int(''.join('1' if b else '0' for b in bits), 2)


def list_files(rel_dir):
    full = os.path.join(ROOT, rel_dir)
    out = []
    for dirpath, _, files in os.walk(full):
        for fn in sorted(files):
            if os.path.splitext(fn)[1].lower() in IMG_EXT:
                out.append(os.path.relpath(os.path.join(dirpath, fn), ROOT).replace('\\', '/'))
    return sorted(out)


def inspect_image(rel):
    path = os.path.join(ROOT, rel)
    row = {'path': rel, 'kind': 'image', 'sha256': sha256(path),
           'bytes': os.path.getsize(path), 'status': 'ok', 'issues': []}
    raw = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if raw is None:
        row['status'] = 'undecodable'
        row['issues'].append('không decode được')
        return row, None
    row.update(height=int(raw.shape[0]), width=int(raw.shape[1]),
               channels=int(raw.shape[2]) if raw.ndim == 3 else 1, dtype=str(raw.dtype))
    if raw.ndim != 3 or raw.shape[2] != 3:
        row['issues'].append('ảnh không phải 3 kênh')
    if raw.dtype != np.uint8:
        row['issues'].append('ảnh không phải uint8')
    if row['issues']:
        row['status'] = 'invalid_format'
    bgr = raw if (raw.ndim == 3 and raw.shape[2] == 3) else None
    row['dhash'] = format(dhash(bgr), '016x') if bgr is not None else ''
    return row, bgr


def inspect_gt(rel):
    path = os.path.join(ROOT, rel)
    row = {'path': rel, 'kind': 'gt', 'sha256': sha256(path),
           'bytes': os.path.getsize(path), 'status': 'ok', 'issues': []}
    raw = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if raw is None:
        row['status'] = 'undecodable'
        row['issues'].append('không decode được')
        return row
    row.update(height=int(raw.shape[0]), width=int(raw.shape[1]),
               channels=int(raw.shape[2]) if raw.ndim == 3 else 1, dtype=str(raw.dtype))
    uniq = np.unique(raw).tolist()
    row['unique_values'] = uniq if len(uniq) <= 8 else uniq[:8] + ['...']
    row['foreground_pixels'] = int(np.count_nonzero(raw))
    if raw.ndim != 2:
        row['issues'].append('GT không phải 1 kênh')
    if raw.dtype != np.uint8:
        row['issues'].append('GT không phải uint8')
    if not set(uniq).issubset({0, 255}):
        row['issues'].append('GT có giá trị ngoài 0/255')
    if row['foreground_pixels'] == 0:
        row['issues'].append('GT rỗng')
    if row['issues']:
        row['status'] = 'invalid_gt'
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    ap.add_argument('--images-dir', default='data/images')
    ap.add_argument('--gt-dir', default='data/ground_truth')
    ap.add_argument('--metadata', default='data/metadata.csv')
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, 'results', 'phase_d', args.run_id, 'audit')
    if os.path.exists(out_dir):
        sys.exit(f'Từ chối ghi đè: {out_dir} đã tồn tại')
    os.makedirs(out_dir)

    image_rows, gt_rows, dhashes = [], [], {}
    for rel in list_files(args.images_dir):
        row, _ = inspect_image(rel)
        image_rows.append(row)
        if row.get('dhash'):
            dhashes[rel] = int(row['dhash'], 16)
    for rel in list_files(args.gt_dir):
        gt_rows.append(inspect_gt(rel))

    # Ghép cặp theo stem (đường dẫn đầy đủ, không chỉ extract_image_id)
    gt_by_stem = defaultdict(list)
    for g in gt_rows:
        gt_by_stem[os.path.splitext(os.path.basename(g['path']))[0]].append(g)
    img_stems = defaultdict(list)
    for i in image_rows:
        img_stems[os.path.splitext(os.path.basename(i['path']))[0]].append(i)

    pairs = []
    for stem, imgs in sorted(img_stems.items()):
        gts = gt_by_stem.get(stem, [])
        for im in imgs:
            pair = {'image': im['path'], 'gt': gts[0]['path'] if gts else '',
                    'stem_collision': len(imgs) > 1 or len(gts) > 1, 'issues': []}
            if not gts:
                pair['state'] = 'missing_gt'
            else:
                g = gts[0]
                if im['status'] != 'ok' or g['status'] != 'ok':
                    pair['state'] = 'invalid_pair'
                    pair['issues'] += im['issues'] + g['issues']
                elif (im['height'], im['width']) != (g['height'], g['width']):
                    pair['state'] = 'invalid_pair'
                    pair['issues'].append('lệch kích thước ảnh/GT')
                else:
                    pair['state'] = 'valid_pair'
            pairs.append(pair)
    orphan_gt = [g['path'] for stem, gs in gt_by_stem.items() if stem not in img_stems for g in gs]

    # Trùng byte và gần trùng (dHash, khoảng cách Hamming <= 5) -> chỉ đánh dấu xem thủ công
    by_hash = defaultdict(list)
    for r in image_rows:
        by_hash[r['sha256']].append(r['path'])
    dup_exact = [v for v in by_hash.values() if len(v) > 1]
    paths = sorted(dhashes)
    near = []
    for a in range(len(paths)):
        for b in range(a + 1, len(paths)):
            d = bin(dhashes[paths[a]] ^ dhashes[paths[b]]).count('1')
            if d <= 5 and by_hash and image_rows:
                near.append({'a': paths[a], 'b': paths[b], 'hamming': d})

    # Metadata
    meta_rows = []
    if os.path.exists(os.path.join(ROOT, args.metadata)):
        with open(os.path.join(ROOT, args.metadata), newline='', encoding='utf-8-sig') as f:
            meta_rows = list(csv.DictReader(f))
    meta_images = {m.get('image_file', '').replace('\\', '/') for m in meta_rows}
    image_paths = {r['path'] for r in image_rows}
    metadata_cov = {
        'metadata_rows': len(meta_rows),
        'images_in_metadata': sorted(image_paths & meta_images),
        'images_without_metadata': sorted(image_paths - meta_images),
        'metadata_pointing_to_missing_file': sorted(p for p in meta_images if p and p not in image_paths),
    }

    state_counts = defaultdict(int)
    for p in pairs:
        state_counts[p['state']] += 1
    summary = {
        'run_id': args.run_id,
        'total_image_files': len(image_rows),
        'total_gt_files': len(gt_rows),
        'image_status': {s: sum(1 for r in image_rows if r['status'] == s)
                         for s in sorted({r['status'] for r in image_rows})},
        'gt_status': {s: sum(1 for r in gt_rows if r['status'] == s)
                      for s in sorted({r['status'] for r in gt_rows})},
        'pair_states': dict(state_counts),
        'orphan_gt': orphan_gt,
        'exact_duplicate_groups': dup_exact,
        'near_duplicate_candidates_manual_review': near,
        'metadata': {k: (v if not isinstance(v, list) else len(v)) for k, v in metadata_cov.items()},
        'accounting_check': {
            'pairs_total_equals_image_files': sum(state_counts.values()) == len(image_rows),
        },
    }

    def dump(name, obj):
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    dump('inventory_images.json', image_rows)
    dump('inventory_gt.json', gt_rows)
    dump('pairs.json', pairs)
    dump('metadata_coverage.json', metadata_cov)
    dump('summary.json', summary)
    with open(os.path.join(out_dir, 'inventory_files.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['path', 'kind', 'bytes', 'sha256', 'width', 'height', 'channels', 'dtype', 'status', 'issues'])
        for r in image_rows + gt_rows:
            w.writerow([r['path'], r['kind'], r['bytes'], r['sha256'], r.get('width', ''),
                        r.get('height', ''), r.get('channels', ''), r.get('dtype', ''),
                        r['status'], '; '.join(r['issues'])])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
