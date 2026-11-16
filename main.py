# -*- coding: utf-8 -*-
"""
Flask Backend Application
Ứng dụng Web xử lý ảnh HSV - Tách và nhận biết màu

Chạy: python main.py
Truy cập: http://localhost:5000
"""

import os
import sys
import re
import copy
import time
import uuid
import struct
import hashlib
import zipfile
import threading
import shutil
import logging
import csv
import platform
import json
from fractions import Fraction
import cv2
import numpy as np
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image
import base64

from src.data_loader import DataLoader
from src.hsv_segment import HSVSegmenter, COLOR_IDS, get_color_preset
from src.median_filter import MedianFilter
from src.morphology import MorphologyOperator
from src.evaluation import SegmentationEvaluator

# Cấu hình Flask
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global session object để lưu trạng thái
session_data = {}

# ---------------------------------------------------------------------
# Phase E: quản lý session / tài nguyên (demo cục bộ, một tiến trình)
# ---------------------------------------------------------------------
logger = logging.getLogger('hsv_app')
SESSION_TTL_SECONDS = 30 * 60                 # TTL 30 phút kể từ lần truy cập cuối
MAX_SESSIONS = 5                              # số session đồng thời tối đa
MAX_DECODED_PIXELS = 25_000_000               # 25 MP, kiểm tra từ header trước khi giải mã
MAX_SESSION_BYTES_TOTAL = 1024 * 1024 * 1024  # 1 GiB cho mảng numpy của mọi session + so sánh
MIN_FREE_DISK_BYTES = 256 * 1024 * 1024       # chừa tối thiểu 256 MiB trống trên ổ uploads
session_lock = threading.RLock()


class CompareError(ValueError):
    """Lỗi nhập liệu có mã HTTP 4xx (định nghĩa sớm để dùng cho Phase E)."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _arrays_bytes(obj):
    return sum(v.nbytes for v in obj.values() if isinstance(v, np.ndarray))


def _session_bytes(session_id):
    entry = session_data.get(session_id)
    total = _arrays_bytes(entry) if entry else 0
    for record in comparison_data.get(session_id, {}).values():
        for item in record['results']:
            if item.get('masks'):
                total += _arrays_bytes(item['masks'])
        for gt in record.get('gt_masks', {}).values():
            total += gt.nbytes
    return total


def total_session_bytes():
    return sum(_session_bytes(sid) for sid in session_data)


def drop_session(session_id):
    """Xóa session, dữ liệu so sánh và file upload của chính session đó."""
    with session_lock:
        entry = session_data.pop(session_id, None)
        comparison_data.pop(session_id, None)
    if entry:
        path = entry.get('filepath')
        folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
        try:
            if path and os.path.abspath(path).startswith(folder + os.sep) and os.path.isfile(path):
                os.remove(path)
        except OSError:
            logger.warning('Không xóa được file upload của session đã hết hạn')
    return entry is not None


def purge_expired_sessions(now=None):
    now = now if now is not None else time.time()
    with session_lock:
        expired = [sid for sid, e in session_data.items()
                   if now - e.get('last_access', now) > SESSION_TTL_SECONDS]
    for sid in expired:
        drop_session(sid)
    return expired


def enforce_budget(protect=None):
    """Đuổi session ít dùng nhất (LRU) tới khi đủ ngân sách; protect không bị đuổi."""
    with session_lock:
        purge_expired_sessions()
        while True:
            over_count = len(session_data) > MAX_SESSIONS
            over_bytes = total_session_bytes() > MAX_SESSION_BYTES_TOTAL
            if not (over_count or over_bytes):
                return
            victims = sorted((e.get('last_access', 0), sid) for sid, e in session_data.items()
                             if sid != protect)
            if not victims:
                raise CompareError('Vượt ngân sách bộ nhớ của server; hãy dùng ảnh nhỏ hơn', 413)
            drop_session(victims[0][1])


def get_active_session(session_id, status=400):
    """Lấy session còn hạn và làm mới last_access; session lạ/hết hạn -> CompareError."""
    with session_lock:
        purge_expired_sessions()
        if not isinstance(session_id, str) or session_id not in session_data:
            raise CompareError('Session không tồn tại hoặc đã hết hạn', status)
        entry = session_data[session_id]
        entry['last_access'] = time.time()
        return entry


def _csv_safe(value):
    """Chống CSV injection: ô chuỗi bắt đầu bằng = + - @ tab CR được thêm dấu nháy đơn."""
    if isinstance(value, str) and value[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


def allowed_file(filename):
    """Kiểm tra file hợp lệ"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def image_to_base64(image):
    """Chuyển ảnh numpy thành base64"""
    _, buffer = cv2.imencode('.png', image)
    base64_str = base64.b64encode(buffer).decode()
    return f"data:image/png;base64,{base64_str}"


def load_image_safe(filepath):
    """Đọc ảnh an toàn"""
    try:
        if not os.path.exists(filepath):
            return None, "File không tồn tại"
        
        image = cv2.imread(filepath)
        if image is None:
            return None, "Không thể đọc file ảnh"
        
        return image, None
    except Exception as e:
        return None, str(e)


@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Tải lên ảnh"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Không có file ảnh'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'Tên file trống'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Định dạng file không được hỗ trợ'}), 400
        
        # Kiểm tra ổ đĩa còn chỗ trước khi ghi
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        if shutil.disk_usage(app.config['UPLOAD_FOLDER']).free < MIN_FREE_DISK_BYTES:
            return jsonify({'error': 'Không đủ dung lượng ổ đĩa để lưu ảnh'}), 507

        # Đọc bytes và kiểm tra kích thước giải mã từ header (chưa giải mã pixel)
        raw = file.read()
        try:
            with Image.open(io.BytesIO(raw)) as probe:
                pw, ph = probe.size
        except Exception:
            return jsonify({'error': 'Không thể đọc file ảnh'}), 400
        if pw * ph > MAX_DECODED_PIXELS:
            return jsonify({'error': f'Ảnh quá lớn: {pw}x{ph} vượt giới hạn {MAX_DECODED_PIXELS} pixel'}), 413

        # Lưu file với tên duy nhất (uuid) để không trùng/ghi đè
        session_id = f"s_{uuid.uuid4().hex}"
        filename = secure_filename(f"{session_id}_{os.path.basename(file.filename)}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'xb') as fh:
            fh.write(raw)
        
        # Đọc ảnh
        image_bgr, error = load_image_safe(filepath)
        if error:
            try:
                os.remove(filepath)
            except OSError:
                pass
            return jsonify({'error': 'Không thể đọc file ảnh'}), 400
        
        # Lưu vào session (có TTL / ngân sách)
        with session_lock:
            session_data[session_id] = {
                'image_bgr': image_bgr,
                'filepath': filepath,
                'filename': file.filename,
                'timestamp': datetime.now(),
                'last_access': time.time(),
                'run_id': 0,
            }
            try:
                enforce_budget(protect=session_id)
                if total_session_bytes() > MAX_SESSION_BYTES_TOTAL:
                    raise CompareError('Vượt ngân sách bộ nhớ của server', 413)
            except CompareError:
                drop_session(session_id)
                raise
        
        # Trả về thông tin ảnh
        h, w = image_bgr.shape[:2]
        return jsonify({
            'session_id': session_id,
            'width': w,
            'height': h,
            'image_base64': image_to_base64(image_bgr),
            'filename': file.filename,
        })
        
    except CompareError as e:
        return jsonify({'error': str(e)}), e.status
    except RequestEntityTooLarge:
        return jsonify({'error': 'File quá lớn'}), 413
    except Exception:
        logger.exception('upload failed')
        return jsonify({'error': 'Lỗi upload'}), 500


@app.route('/api/process', methods=['POST'])
def process_image():
    """Xử lý ảnh với các cấu hình"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Body phải là JSON object'}), 400
        session_id = data.get('session_id')
        
        entry = get_active_session(session_id)
        
        image_bgr = entry['image_bgr'].copy()
        
        # Cấu hình HSV: nếu có color_id thì nạp preset, nếu không giữ cấu hình Red cũ
        color_id = data.get('color_id')
        if color_id is not None:
            try:
                preset = get_color_preset(color_id)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            color_name = preset['name']
            hue_ranges = preset['hue_ranges']
            # Giá trị người dùng chỉnh tay (slider) ghi đè preset; thiếu thì dùng preset
            saturation = [int(data.get('s_min', preset['saturation'][0])),
                          int(data.get('s_max', preset['saturation'][1]))]
            value = [int(data.get('v_min', preset['value'][0])),
                     int(data.get('v_max', preset['value'][1]))]
            if preset['mode'] == 'hue':
                hue_ranges = [
                    [int(data.get('h_min_1', hue_ranges[0][0])), int(data.get('h_max_1', hue_ranges[0][1]))]
                ]
                if len(preset['hue_ranges']) == 2:
                    hue_ranges.append([
                        int(data.get('h_min_2', preset['hue_ranges'][1][0])),
                        int(data.get('h_max_2', preset['hue_ranges'][1][1])),
                    ])
        else:
            # Đường dẫn cũ (tương thích): cấu hình Red mặc định
            color_name = 'Red'
            hue_ranges = [
                [int(data.get('h_min_1', 0)), int(data.get('h_max_1', 10))],
                [int(data.get('h_min_2', 170)), int(data.get('h_max_2', 180))]
            ]
            saturation = [int(data.get('s_min', 100)), int(data.get('s_max', 255))]
            value = [int(data.get('v_min', 100)), int(data.get('v_max', 255))]

        hsv_config = {
            'color_name': color_name,
            'hue_ranges': hue_ranges,
            'saturation': saturation,
            'value': value,
        }
        
        # Phân đoạn HSV
        segmenter = HSVSegmenter(hsv_config)
        mask_raw, image_hsv = segmenter.segment(image_bgr)
        
        # Lọc Median
        median_kernel = int(data.get('median_kernel', 5))
        if median_kernel % 2 == 0:
            median_kernel += 1
        median_filter = MedianFilter(median_kernel)
        mask_median = median_filter.filter(mask_raw)
        
        # Morphology (Phase C): object `morphology` mới được ưu tiên; không có thì đọc đường cũ
        warnings = []
        if 'morphology' in data:
            morph = validate_morphology(data['morphology'])
            branch = 'morphology'
            ignored = [k for k in ('morph_kernel', 'use_closing', 'use_opening') if k in data]
            if ignored:
                warnings.append(f"Trường legacy bị bỏ qua vì đã có object morphology: {ignored}")
        else:
            branch = 'legacy'
            morph_kernel = int(data.get('morph_kernel', 5))
            if morph_kernel % 2 == 0:
                morph_kernel += 1
            legacy_ops = []
            if data.get('use_closing', True):
                legacy_ops.append({'op': 'close', 'iterations': 1})
            if data.get('use_opening', False):
                legacy_ops.append({'op': 'open', 'iterations': 1})
            morph = legacy_to_morphology(morph_kernel, 'ellipse', legacy_ops)

        mask_morph = apply_morphology(mask_median, morph)
        applied_config = {
            'branch': branch,
            'median_kernel': median_kernel,
            'morphology': morph,
            'warnings': warnings,
        }
        
        # Lưu kết quả vào session; run mới -> xóa GT/metrics/visualization cũ (không stale)
        with session_lock:
            if session_id not in session_data:
                raise CompareError('Session không tồn tại hoặc đã hết hạn', 400)
            entry['run_id'] = entry.get('run_id', 0) + 1
            for stale in ('gt_mask', 'metrics', 'visualization', 'gt_sha256', 'metrics_run_id'):
                entry.pop(stale, None)
            entry.update({
                'mask_raw': mask_raw,
                'mask_median': mask_median,
                'mask_morph': mask_morph,
                'image_hsv': image_hsv,
                'applied_hsv': copy.deepcopy(hsv_config),
                'applied_config': copy.deepcopy(applied_config),
                'last_access': time.time(),
            })
            enforce_budget(protect=session_id)
        run_id = entry['run_id']
        
        # Trả về kết quả
        return jsonify({
            'status': 'success',
            'mask_raw': image_to_base64(mask_raw),
            'mask_median': image_to_base64(mask_median),
            'mask_morph': image_to_base64(mask_morph),
            'image_dimensions': {
                'width': image_bgr.shape[1],
                'height': image_bgr.shape[0],
            },
            'white_pixels': {
                'raw': int(np.sum(mask_raw > 0)),
                'median': int(np.sum(mask_median > 0)),
                'morph': int(np.sum(mask_morph > 0)),
            },
            'applied_config': applied_config,
            'run_id': run_id,
            'request_id': data.get('request_id') if isinstance(data.get('request_id'), (str, int)) else None,
        })
        
    except CompareError as e:
        # Tham số morphology sai: 400, session kết quả cũ không bị thay đổi
        return jsonify({'error': str(e)}), e.status
    except (ValueError, TypeError, KeyError, IndexError):
        return jsonify({'error': 'Tham số xử lý không hợp lệ'}), 400
    except Exception:
        logger.exception('process failed')
        return jsonify({'error': 'Lỗi xử lý'}), 500


@app.route('/api/download-mask', methods=['POST'])
def download_mask():
    """Tải xuống Mask"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Body phải là JSON object'}), 400
        session_id = data.get('session_id')
        mask_type = data.get('mask_type', 'morph')  # raw, median, morph
        
        entry = get_active_session(session_id)
        
        if mask_type not in ('raw', 'median', 'morph'):
            return jsonify({'error': 'mask_type phải thuộc raw, median, morph'}), 400
        mask_key = f'mask_{mask_type}'
        if mask_key not in entry:
            return jsonify({'error': f'Mask {mask_type} không được tính toán'}), 400
        
        mask = entry[mask_key]
        
        # Chuyển sang PIL Image
        mask_pil = Image.fromarray(mask)
        
        # Lưu vào buffer
        buffer = io.BytesIO()
        mask_pil.save(buffer, format='PNG')
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'mask_{mask_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        
    except CompareError as e:
        return jsonify({'error': str(e)}), e.status
    except Exception:
        logger.exception('download-mask failed')
        return jsonify({'error': 'Lỗi tải mask'}), 500


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """Đánh giá với Ground Truth"""
    try:
        if 'ground_truth' not in request.files:
            return jsonify({'error': 'Không có Ground Truth file'}), 400
        
        data = request.form
        session_id = data.get('session_id')
        gt_file = request.files['ground_truth']
        
        entry = get_active_session(session_id)
        
        if 'mask_morph' not in entry:
            return jsonify({'error': 'Chưa xử lý ảnh'}), 400
        
        # Phase E: GT raw nghiêm ngặt (PNG 1 kênh uint8 {0,255}, cùng kích thước),
        # đọc từ bộ nhớ: không ghi đĩa, không threshold, không resize
        raw = gt_file.read(COMPARE_GT_MAX_BYTES + 1)
        with session_lock:
            run_id_at_start = entry.get('run_id', 0)
            pred_mask = entry['mask_morph']
        gt_mask = read_strict_gt(raw, pred_mask.shape)
        
        evaluator = SegmentationEvaluator()
        metrics = evaluator.compute_metrics(pred_mask, gt_mask)
        vis = evaluator.create_visualization(pred_mask, gt_mask)
        
        # Chỉ lưu nếu run chưa đổi trong lúc tính (tránh metrics stale)
        with session_lock:
            if session_id not in session_data or entry.get('run_id', 0) != run_id_at_start:
                return jsonify({'error': 'Kết quả xử lý đã thay đổi; hãy đánh giá lại'}), 409
            entry.update({
                'gt_mask': gt_mask,
                'gt_sha256': _sha256_bytes(raw),
                'metrics': metrics,
                'visualization': vis,
                'metrics_run_id': run_id_at_start,
            })
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'visualization': image_to_base64(vis),
            'run_id': run_id_at_start,
        })
        
    except CompareError as e:
        return jsonify({'error': str(e)}), e.status
    except Exception:
        logger.exception('evaluate failed')
        return jsonify({'error': 'Lỗi đánh giá'}), 500


@app.route('/api/get-info', methods=['GET'])
def get_info():
    """Lấy thông tin HSV của ảnh"""
    try:
        session_id = request.args.get('session_id')
        
        entry = get_active_session(session_id)
        
        if 'image_hsv' not in entry:
            return jsonify({'error': 'Chưa tính HSV'}), 400
        
        image_hsv = entry['image_hsv']
        mask_raw = entry['mask_raw']
        
        # Lấy thông tin HSV
        info = HSVSegmenter.get_hsv_info(image_hsv, mask_raw)
        
        return jsonify(info)
        
    except CompareError as e:
        return jsonify({'error': str(e)}), e.status
    except Exception:
        logger.exception('get-info failed')
        return jsonify({'error': 'Lỗi lấy thông tin HSV'}), 500


@app.route('/api/color-presets', methods=['GET'])
def color_presets():
    """Trả về danh sách 15 preset màu (nguồn duy nhất: COLOR_PRESETS)"""
    return jsonify({
        'presets': [get_color_preset(cid) for cid in COLOR_IDS],
    })


@app.route('/api/health', methods=['GET'])
def health():
    """Kiểm tra sức khỏe server"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
    })


# =====================================================================
# Phase B: So sánh nhiều cấu hình ngưỡng HSV
# Trạng thái so sánh nằm trong comparison_data, tách khỏi session_data
# (xử lý đơn /api/process không bị ghi đè và ngược lại).
# =====================================================================
COMPARE_SCHEMA_VERSION = 1
COMPARE_MIN_CONFIGS = 2
COMPARE_MAX_CONFIGS = 6
COMPARE_MAX_PER_SESSION = 20
COMPARE_IMPORT_MAX_BYTES = 1024 * 1024  # 1 MiB
COMPARE_STAGES = ('raw', 'median', 'morph')
COMPARE_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
COMPARE_RANKING_RULE = 'iou_desc_then_f1_desc_ties_share_rank'
COMPARE_DEFAULT_PIPELINE = {
    'median_kernel': 5,
    'morph_kernel': 5,
    'kernel_shape': 'ellipse',
    'operations': [{'op': 'close', 'iterations': 1}],
}

# comparison_data[session_id][comparison_id] = record
comparison_data = {}
comparison_lock = threading.Lock()


def _is_int(value):
    """Số nguyên thật: loại bool và số thực."""
    return isinstance(value, int) and not isinstance(value, bool)


def _compare_error_response(error):
    return jsonify({'error': str(error)}), error.status


# =====================================================================
# Phase C: object morphology dùng chung cho xử lý đơn và so sánh B
#   {"kernel_size": int 1-31 lẻ, "kernel_shape": rect|ellipse|cross,
#    "operations": [{"operation": close|open|erode|dilate, "iterations": int 1-10}, ...]}
# Thứ tự operations do client gửi được giữ nguyên (UI gửi close→open→erode→dilate).
# =====================================================================
MORPH_OPERATIONS = ('close', 'open', 'erode', 'dilate')
MORPH_SHAPES = ('rect', 'ellipse', 'cross')
MORPH_KERNEL_MIN, MORPH_KERNEL_MAX = 1, 31
MORPH_ITER_MIN, MORPH_ITER_MAX = 1, 10
MORPH_KEYS = ('kernel_size', 'kernel_shape', 'operations')


def _morph_int(value, field, low, high):
    """Số nguyên thật (type(value) is int): từ chối bool, float, chuỗi, null; không tự điều chỉnh."""
    if type(value) is not int:
        raise CompareError(
            f"morphology.{field} phải là số nguyên (int), nhận: {value!r} ({type(value).__name__})")
    if not low <= value <= high:
        raise CompareError(f"morphology.{field} phải nằm trong [{low}, {high}], nhận: {value}")
    return value


def validate_morphology(obj):
    """Kiểm tra nghiêm ngặt object morphology mới; trả bản chuẩn hóa, không sửa giá trị sai."""
    if not isinstance(obj, dict):
        raise CompareError(f"morphology phải là object, nhận: {obj!r}")
    unknown = sorted(set(obj) - set(MORPH_KEYS))
    if unknown:
        raise CompareError(f"morphology có trường không hỗ trợ: {unknown}")
    missing = [k for k in MORPH_KEYS if k not in obj]
    if missing:
        raise CompareError(f"morphology thiếu trường bắt buộc: {missing}")
    size = _morph_int(obj['kernel_size'], 'kernel_size', MORPH_KERNEL_MIN, MORPH_KERNEL_MAX)
    if size % 2 == 0:
        raise CompareError(f"morphology.kernel_size phải là số lẻ, nhận: {size} (không tự cộng 1)")
    shape = obj['kernel_shape']
    if type(shape) is not str or shape not in MORPH_SHAPES:
        raise CompareError(f"morphology.kernel_shape phải thuộc {list(MORPH_SHAPES)}, nhận: {shape!r}")
    operations = obj['operations']
    if not isinstance(operations, list):
        raise CompareError(f"morphology.operations phải là danh sách, nhận: {operations!r}")
    if len(operations) > len(MORPH_OPERATIONS):
        raise CompareError(f"morphology.operations tối đa {len(MORPH_OPERATIONS)} phép, nhận {len(operations)}")
    result, seen = [], set()
    for i, op in enumerate(operations):
        label = f"operations[{i}]"
        if not isinstance(op, dict):
            raise CompareError(f"morphology.{label} phải là object, nhận: {op!r}")
        extra = sorted(set(op) - {'operation', 'iterations'})
        if extra:
            raise CompareError(f"morphology.{label} có trường không hỗ trợ: {extra}")
        name = op.get('operation')
        if type(name) is not str or name not in MORPH_OPERATIONS:
            raise CompareError(
                f"morphology.{label}.operation phải thuộc {list(MORPH_OPERATIONS)}, nhận: {name!r}")
        if name in seen:
            raise CompareError(f"morphology.{label}.operation bị trùng: {name!r}")
        seen.add(name)
        if 'iterations' not in op:
            raise CompareError(f"morphology.{label} thiếu iterations")
        iterations = _morph_int(op['iterations'], f'{label}.iterations', MORPH_ITER_MIN, MORPH_ITER_MAX)
        result.append({'operation': name, 'iterations': iterations})
    return {'kernel_size': size, 'kernel_shape': shape, 'operations': result}


def apply_morphology(mask, morph):
    """Adapter: gọi lại MorphologyOperator (set_kernel/apply_sequence) trên bản copy của mask."""
    operator = MorphologyOperator(morph['kernel_size'], morph['kernel_shape'])
    if not morph['operations']:
        return mask.copy()
    return operator.apply_sequence(
        mask, [(o['operation'], {'iterations': o['iterations']}) for o in morph['operations']])


def legacy_to_morphology(kernel_size, kernel_shape, operations):
    """Biểu diễn đường cũ dưới dạng object morphology (không validate lại, giữ hành vi cũ)."""
    return {
        'kernel_size': kernel_size,
        'kernel_shape': kernel_shape,
        'operations': [{'operation': o['op'], 'iterations': o['iterations']} for o in operations],
    }


def validate_range(value, name, maximum, label):
    """Khoảng [min, max] gồm số nguyên thật trong [0, maximum]."""
    if (not isinstance(value, (list, tuple)) or len(value) != 2
            or not all(_is_int(v) for v in value)):
        raise CompareError(f"{label}: {name} phải là [min, max] gồm hai số nguyên, nhận: {value!r}")
    if not (0 <= value[0] <= maximum and 0 <= value[1] <= maximum):
        raise CompareError(f"{label}: {name} phải nằm trong [0, {maximum}], nhận: {list(value)}")
    if value[0] > value[1]:
        raise CompareError(f"{label}: {name} có min > max: {list(value)}")
    return [int(value[0]), int(value[1])]


def validate_compare_config(cfg, index):
    """
    Kiểm tra một cấu hình HSV theo schema mới (H 0-179, S/V 0-255).
    Trả về snapshot đã chuẩn hóa; không đọc/ghi COLOR_PRESETS.
    """
    label = f"Cấu hình #{index + 1}"
    if not isinstance(cfg, dict):
        raise CompareError(f"{label}: phải là object")
    config_id = cfg.get('config_id')
    if not isinstance(config_id, str) or not COMPARE_ID_PATTERN.match(config_id):
        raise CompareError(f"{label}: config_id phải là chuỗi 1-64 ký tự [A-Za-z0-9_-]")
    label = f"Cấu hình '{config_id}'"
    name = cfg.get('name')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 60:
        raise CompareError(f"{label}: name phải là chuỗi không rỗng, tối đa 60 ký tự")
    source_preset = cfg.get('source_preset')
    if source_preset is not None and (not isinstance(source_preset, str) or source_preset not in COLOR_IDS):
        raise CompareError(f"{label}: source_preset không tồn tại: {source_preset!r}")

    hsv = cfg.get('hsv')
    if not isinstance(hsv, dict):
        raise CompareError(f"{label}: thiếu object 'hsv'")
    mode = hsv.get('mode')
    if mode not in ('hue', 'sv'):
        raise CompareError(f"{label}: mode phải là 'hue' hoặc 'sv', nhận: {mode!r}")
    hue_ranges = hsv.get('hue_ranges')
    if not isinstance(hue_ranges, (list, tuple)) or not hue_ranges:
        raise CompareError(f"{label}: hue_ranges phải là danh sách không rỗng")
    hue_ranges = [validate_range(r, 'Hue', 179, label) for r in hue_ranges]
    hue_applied = True
    if mode == 'hue':
        if len(hue_ranges) > 2:
            raise CompareError(f"{label}: mode 'hue' nhận tối đa 2 khoảng Hue")
    else:
        # Màu sv (trắng/đen/xám): Hue không áp dụng, ép toàn miền
        hue_ranges = [[0, 179]]
        hue_applied = False
    return {
        'config_id': config_id,
        'name': name.strip(),
        'source_preset': source_preset,
        'hsv': {
            'mode': mode,
            'hue_ranges': hue_ranges,
            'saturation': validate_range(hsv.get('saturation'), 'Saturation', 255, label),
            'value': validate_range(hsv.get('value'), 'Value', 255, label),
            'hue_applied': hue_applied,
        },
    }


def validate_compare_configs(configs):
    if not isinstance(configs, (list, tuple)):
        raise CompareError("configurations phải là danh sách")
    if not COMPARE_MIN_CONFIGS <= len(configs) <= COMPARE_MAX_CONFIGS:
        raise CompareError(
            f"Cần {COMPARE_MIN_CONFIGS}-{COMPARE_MAX_CONFIGS} cấu hình, nhận: {len(configs)}")
    result, seen = [], set()
    for i, cfg in enumerate(configs):
        item = validate_compare_config(cfg, i)
        if item['config_id'] in seen:
            raise CompareError(f"config_id bị trùng: {item['config_id']}")
        seen.add(item['config_id'])
        result.append(item)
    return result


def validate_fixed_pipeline(pipeline):
    """Pipeline cố định dùng chung; None thì dùng mặc định hiện tại (median 5, ellipse, Closing 1)."""
    if pipeline is None:
        pipeline = COMPARE_DEFAULT_PIPELINE
    if not isinstance(pipeline, dict):
        raise CompareError("fixed_pipeline phải là object")
    median_kernel = pipeline.get('median_kernel', 5)
    if (not _is_int(median_kernel) or median_kernel < 3 or median_kernel > 31
            or median_kernel % 2 == 0):
        raise CompareError(f"median_kernel phải là số nguyên lẻ trong [3, 31], nhận: {median_kernel!r}")
    if 'morphology' in pipeline:
        # Phase C: object morphology dùng chung được ưu tiên; validate nghiêm ngặt, không tự sửa
        morph = validate_morphology(pipeline['morphology'])
        ignored = sorted(k for k in ('morph_kernel', 'kernel_shape', 'operations') if k in pipeline)
        return {
            'median_kernel': int(median_kernel),
            'morph_kernel': morph['kernel_size'],
            'kernel_shape': morph['kernel_shape'],
            'operations': [{'op': o['operation'], 'iterations': o['iterations']}
                           for o in morph['operations']],
            'morphology': morph,
            'morphology_source': 'morphology',
            'ignored_legacy_fields': ignored,
        }
    morph_kernel = pipeline.get('morph_kernel', 5)
    if not _is_int(morph_kernel) or morph_kernel < 1 or morph_kernel > 31 or morph_kernel % 2 == 0:
        raise CompareError(f"morph_kernel phải là số nguyên lẻ trong [1, 31], nhận: {morph_kernel!r}")
    shape = pipeline.get('kernel_shape', 'ellipse')
    if shape not in MorphologyOperator.KERNEL_SHAPES:
        raise CompareError(f"kernel_shape không được hỗ trợ: {shape!r}")
    operations = pipeline.get('operations', COMPARE_DEFAULT_PIPELINE['operations'])
    if not isinstance(operations, (list, tuple)) or len(operations) > 8:
        raise CompareError("operations phải là danh sách tối đa 8 phép toán")
    ops = []
    for op in operations:
        if not isinstance(op, dict):
            raise CompareError("Mỗi operation phải là object {op, iterations}")
        name = op.get('op')
        iterations = op.get('iterations', 1)
        if name not in MorphologyOperator.OPERATIONS:
            raise CompareError(f"Phép toán không được hỗ trợ: {name!r}")
        if not _is_int(iterations) or not 1 <= iterations <= 10:
            raise CompareError(f"iterations phải là số nguyên trong [1, 10], nhận: {iterations!r}")
        ops.append({'op': name, 'iterations': int(iterations)})
    return {
        'median_kernel': int(median_kernel),
        'morph_kernel': int(morph_kernel),
        'kernel_shape': shape,
        'operations': ops,
        # Gói B cũ / payload B cũ: không có object morphology, đọc theo mặc định của phiên bản cũ
        'morphology': legacy_to_morphology(int(morph_kernel), shape, ops),
        'morphology_source': 'legacy_fields',
        'ignored_legacy_fields': [],
    }


def validate_target_color(color_id):
    if not isinstance(color_id, str) or color_id not in COLOR_IDS:
        raise CompareError(f"target_color_id không tồn tại: {color_id!r}")
    return color_id


def validate_stage(stage):
    if stage not in COMPARE_STAGES:
        raise CompareError(f"evaluation_stage phải thuộc {list(COMPARE_STAGES)}, nhận: {stage!r}")
    return stage


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _mask_sha256(mask):
    return _sha256_bytes(np.ascontiguousarray(mask).tobytes())


def _encode_png(mask):
    ok, buffer = cv2.imencode('.png', mask)
    if not ok:
        raise RuntimeError('Không mã hóa được PNG')
    return buffer.tobytes()


def _session_image_hash(entry):
    """SHA-256 của file ảnh đã upload; nếu file không đọc được thì băm pixel đã giải mã."""
    path = entry.get('filepath')
    try:
        with open(path, 'rb') as fh:
            return _sha256_bytes(fh.read()), 'file_bytes'
    except (OSError, TypeError):
        return _mask_sha256(entry['image_bgr']), 'decoded_pixels'


def _fingerprint(image_sha256, target_color_id, configs, pipeline):
    payload = json.dumps({
        'image_sha256': image_sha256,
        'target_color_id': target_color_id,
        'configurations': [{'config_id': c['config_id'], 'hsv': c['hsv']} for c in configs],
        # Chỉ băm 4 trường của B để fingerprint gói B cũ vẫn tái lập được
        'fixed_pipeline': {k: pipeline[k] for k in
                           ('median_kernel', 'morph_kernel', 'kernel_shape', 'operations')},
    }, sort_keys=True, separators=(',', ':'))
    return _sha256_bytes(payload.encode('utf-8'))


def run_pipeline_for_config(image_hsv, hsv, pipeline):
    """Một cấu hình HSV + pipeline chung -> (raw, median, morph). Chỉ HSV khác nhau giữa các cấu hình."""
    segmenter = HSVSegmenter({
        'color_name': 'compare',
        'hue_ranges': hsv['hue_ranges'],
        'saturation': hsv['saturation'],
        'value': hsv['value'],
    })
    mask_raw = segmenter.create_mask(image_hsv)
    mask_median = MedianFilter(pipeline['median_kernel']).filter(mask_raw)
    morph = pipeline.get('morphology') or legacy_to_morphology(
        pipeline['morph_kernel'], pipeline['kernel_shape'], pipeline['operations'])
    mask_morph = apply_morphology(mask_median, morph)
    return mask_raw, mask_median, mask_morph


def _public_config(cfg):
    return copy.deepcopy(cfg)


def _comparison_payload(record, include_masks=True):
    results = []
    for item in record['results']:
        out = {
            'config_id': item['config_id'],
            'name': item['name'],
            'status': item['status'],
            'applied_config': _public_config(item['applied_config']),
            'selected_pixels': item['selected_pixels'],
            'elapsed_ms': item['elapsed_ms'],
            'error': item['error'],
        }
        if include_masks and item['status'] == 'ok':
            out['masks'] = {stage: image_to_base64(item['masks'][stage]) for stage in COMPARE_STAGES}
        results.append(out)
    return {
        'schema_version': COMPARE_SCHEMA_VERSION,
        'comparison_id': record['comparison_id'],
        'created_at': record['created_at'],
        'image': copy.deepcopy(record['image']),
        'target_color_id': record['target_color_id'],
        'evaluation_stage': record['evaluation_stage'],
        'fixed_pipeline': copy.deepcopy(record['fixed_pipeline']),
        'fingerprint': record['fingerprint'],
        'results': results,
        'all_ok': all(r['status'] == 'ok' for r in record['results']),
        'evaluations': copy.deepcopy(record['evaluations']),
    }


def _get_session(session_id):
    return get_active_session(session_id, 404)


def _get_comparison(session_id, comparison_id):
    _get_session(session_id)
    record = comparison_data.get(session_id, {}).get(comparison_id) if isinstance(comparison_id, str) else None
    if record is None:
        raise CompareError('Comparison không tồn tại', 404)
    return record


@app.route('/api/compare-hsv', methods=['POST'])
def compare_hsv():
    """Chạy 2-6 cấu hình HSV trên cùng ảnh bất biến, cùng pipeline cố định."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise CompareError('Body phải là JSON object')
        entry = _get_session(data.get('session_id'))
        # Kiểm tra toàn bộ request trước khi chạy: sai thì không ghi trạng thái nào
        target = validate_target_color(data.get('target_color_id'))
        configs = validate_compare_configs(data.get('configurations'))
        pipeline = validate_fixed_pipeline(data.get('fixed_pipeline'))
        stage = validate_stage(data.get('evaluation_stage', 'raw'))
        record = execute_comparison(data['session_id'], entry, target, configs, pipeline, stage)
        payload = _comparison_payload(record)
        payload['status'] = 'success' if payload['all_ok'] else 'partial_error'
        return jsonify(payload)
    except CompareError as exc:
        return _compare_error_response(exc)
    except Exception as exc:
        return jsonify({'error': f'Lỗi so sánh: {exc}'}), 500


def execute_comparison(session_id, entry, target, configs, pipeline, stage):
    """Chạy các cấu hình đã validate trên bản sao bất biến của ảnh và lưu vào comparison_data."""
    if True:
        with comparison_lock:
            if len(comparison_data.get(session_id, {})) >= COMPARE_MAX_PER_SESSION:
                raise CompareError(
                    f'Đã đạt giới hạn {COMPARE_MAX_PER_SESSION} lượt so sánh trong session này', 409)

        image = entry['image_bgr'].copy()   # nguồn bất biến, copy một lần
        image.setflags(write=False)
        image_sha256, hash_basis = _session_image_hash(entry)
        height, width = image.shape[:2]
        image_hsv = HSVSegmenter().bgr_to_hsv(image)

        results = []
        for cfg in configs:
            item = {
                'config_id': cfg['config_id'], 'name': cfg['name'],
                'applied_config': cfg, 'status': 'ok', 'masks': None,
                'selected_pixels': None, 'elapsed_ms': None, 'error': None,
            }
            started = time.perf_counter()
            try:
                raw, med, morph = run_pipeline_for_config(image_hsv, cfg['hsv'], pipeline)
                item['masks'] = {'raw': raw, 'median': med, 'morph': morph}
                item['selected_pixels'] = {
                    'raw': int(np.count_nonzero(raw)),
                    'median': int(np.count_nonzero(med)),
                    'morph': int(np.count_nonzero(morph)),
                }
            except Exception as exc:  # trạng thái lỗi rõ ràng cho từng cấu hình
                item['status'] = 'error'
                item['error'] = f'{type(exc).__name__}: {exc}'
            item['elapsed_ms'] = round((time.perf_counter() - started) * 1000, 3)
            results.append(item)

        record = {
            'comparison_id': f"cmp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'image': {
                'sha256': image_sha256, 'hash_basis': hash_basis,
                'width': int(width), 'height': int(height),
                'filename': os.path.basename(str(entry.get('filename') or '')),
            },
            'target_color_id': target,
            'evaluation_stage': stage,
            'fixed_pipeline': pipeline,
            'fingerprint': _fingerprint(image_sha256, target, configs, pipeline),
            'results': results,
            'evaluations': {},
        }
        with comparison_lock:
            comparison_data.setdefault(session_id, {})[record['comparison_id']] = record
        return record


PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
COMPARE_GT_MAX_BYTES = 20 * 1024 * 1024
COMPARE_METRIC_KEYS = ('pixel_accuracy', 'iou', 'precision', 'recall', 'f1')


def read_strict_gt(raw_bytes, expected_shape):
    """
    Đọc GT nguyên trạng (không threshold, không resize, không đổi kênh).
    Yêu cầu: PNG, 1 kênh, uint8, cùng H x W, giá trị thuộc {0, 255}.
    """
    if not raw_bytes:
        raise CompareError('Ground Truth rỗng')
    if len(raw_bytes) > COMPARE_GT_MAX_BYTES:
        raise CompareError('Ground Truth vượt quá 20 MiB', 413)
    if not raw_bytes.startswith(PNG_SIGNATURE):
        raise CompareError('Ground Truth phải là file PNG')
    gt = cv2.imdecode(np.frombuffer(raw_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if gt is None:
        raise CompareError('Không giải mã được Ground Truth PNG')
    if gt.ndim != 2:
        raise CompareError(f'Ground Truth phải có đúng 1 kênh, nhận shape {gt.shape}')
    if gt.dtype != np.uint8:
        raise CompareError(f'Ground Truth phải là uint8, nhận {gt.dtype}')
    if gt.shape != tuple(expected_shape):
        raise CompareError(
            f'Kích thước GT {gt.shape[1]}x{gt.shape[0]} khác ảnh '
            f'{expected_shape[1]}x{expected_shape[0]}; hệ thống không tự resize')
    values = [int(v) for v in np.unique(gt)]
    if not set(values) <= {0, 255}:
        raise CompareError(
            f'Ground Truth chỉ được chứa giá trị 0 và 255, nhận các giá trị: {values[:10]}; '
            'hệ thống không tự threshold')
    return gt


def _exact_scores(metrics):
    """IoU và F1 dạng phân số chính xác từ TP/FP/FN, dùng để xếp hạng/đồng hạng."""
    tp, fp, fn = metrics['TP'], metrics['FP'], metrics['FN']
    iou_den = tp + fp + fn
    f1_den = 2 * tp + fp + fn
    iou = Fraction(tp, iou_den) if iou_den else Fraction(0)
    f1 = Fraction(2 * tp, f1_den) if f1_den else Fraction(0)
    return iou, f1


def rank_configurations(entries):
    """
    entries: [(config_id, metrics)]. Xếp hạng IoU giảm dần rồi F1 giảm dần.
    Đồng hạng (cùng IoU và F1 chính xác) chia sẻ hạng; hạng kế tiếp bỏ qua (1,1,3).
    """
    scored = [(cid, *_exact_scores(m)) for cid, m in entries]
    scored.sort(key=lambda t: (-t[1], -t[2], t[0]))
    ranking, previous, rank = [], None, 0
    for position, (cid, iou, f1) in enumerate(scored, start=1):
        if (iou, f1) != previous:
            rank = position
            previous = (iou, f1)
        ranking.append({'config_id': cid, 'rank': rank})
    return ranking


def _metric_view(metrics):
    return {
        'pixel_accuracy': metrics['pixel_accuracy'],
        'iou': metrics['iou'],
        'precision': metrics['precision'],
        'recall': metrics['recall'],
        'f1': metrics['f1'],
        'TP': metrics['TP'], 'TN': metrics['TN'],
        'FP': metrics['FP'], 'FN': metrics['FN'],
    }


def build_evaluation(record, stage, gt_mask, gt_sha256):
    """
    Tính metrics bằng SegmentationEvaluator cho từng cấu hình lỗi-free.
    Không GT: metrics = None, không xếp hạng, không winner.
    Có cấu hình lỗi: không xếp hạng, không winner.
    """
    base = {
        'stage': stage,
        'ranking_rule': COMPARE_RANKING_RULE,
        'zero_division_convention': 'evaluator hiện tại trả 0.0 khi mẫu số bằng 0 (không sửa trong Phase B)',
        'gt': None,
        'metrics': {r['config_id']: None for r in record['results']},
        'ranking': None,
        'best_config_ids': None,
        'status': 'no_ground_truth',
        'reason': 'Không có Ground Truth hợp lệ: metrics là N/A, không công bố cấu hình tốt nhất.',
    }
    if gt_mask is None:
        return base

    base['gt'] = {
        'sha256': gt_sha256,
        'width': int(gt_mask.shape[1]),
        'height': int(gt_mask.shape[0]),
        'dtype': 'uint8',
        'channels': 1,
    }
    evaluator = SegmentationEvaluator()
    scored = []
    failed = []
    for item in record['results']:
        if item['status'] != 'ok':
            failed.append(item['config_id'])
            continue
        try:
            metrics = evaluator.compute_metrics(item['masks'][stage], gt_mask)
        except Exception:
            failed.append(item['config_id'])
            continue
        base['metrics'][item['config_id']] = _metric_view(metrics)
        scored.append((item['config_id'], metrics))

    if failed:
        base['status'] = 'incomplete'
        base['reason'] = ('Cấu hình lỗi hoặc không tính được metrics: '
                          + ', '.join(failed) + '. Không xếp hạng, không công bố cấu hình tốt nhất.')
        return base

    ranking = rank_configurations(scored)
    top = [r['config_id'] for r in ranking if r['rank'] == 1]
    base['ranking'] = ranking
    base['best_config_ids'] = top
    base['status'] = 'ok'
    base['reason'] = ('Đồng hạng nhất giữa: ' + ', '.join(top)) if len(top) > 1 else 'Xếp hạng theo IoU rồi F1.'
    return base


@app.route('/api/compare-hsv/evaluate', methods=['POST'])
def compare_hsv_evaluate():
    """Đánh giá một lượt so sánh với GT (multipart). GT sai bị từ chối, không ghi trạng thái."""
    try:
        form = request.form
        session_id = form.get('session_id')
        comparison_id = form.get('comparison_id')
        record = _get_comparison(session_id, comparison_id)
        stage = validate_stage(form.get('evaluation_stage') or record['evaluation_stage'])

        gt_file = request.files.get('ground_truth')
        gt_mask, gt_sha256 = None, None
        if gt_file is not None and gt_file.filename:
            if form.get('gt_pair_confirmed', '').lower() != 'true':
                raise CompareError(
                    'Cần xác nhận cặp ảnh/nhãn (gt_pair_confirmed=true) cùng màu mục tiêu '
                    f"'{record['target_color_id']}'; kiểm tra kỹ thuật không chứng minh nhãn đúng ngữ nghĩa")
            raw = gt_file.read(COMPARE_GT_MAX_BYTES + 1)
            expected = (record['image']['height'], record['image']['width'])
            gt_mask = read_strict_gt(raw, expected)
            gt_sha256 = _sha256_bytes(raw)
            manifest_image_hash = form.get('gt_image_sha256')
            if manifest_image_hash and manifest_image_hash.lower() != record['image']['sha256']:
                raise CompareError('gt_image_sha256 trong manifest không khớp hash ảnh của lượt so sánh')

        evaluation = build_evaluation(record, stage, gt_mask, gt_sha256)
        with comparison_lock:
            record['evaluations'][stage] = evaluation
            gts = record.setdefault('gt_masks', {})
            if gt_mask is not None:
                gts[stage] = gt_mask
            else:
                gts.pop(stage, None)
        return jsonify({
            'status': 'success',
            'comparison_id': record['comparison_id'],
            'evaluation': copy.deepcopy(evaluation),
        })
    except CompareError as exc:
        return _compare_error_response(exc)
    except Exception as exc:
        return jsonify({'error': f'Lỗi đánh giá so sánh: {exc}'}), 500


def build_export_manifest(record):
    """comparison.json schema v1. Không chứa đường dẫn tuyệt đối; metrics nullable."""
    configurations, results = [], []
    for item in record['results']:
        configurations.append(copy.deepcopy(item['applied_config']))
        entry = {
            'config_id': item['config_id'],
            'status': item['status'],
            'selected_pixels': item['selected_pixels'],
            'elapsed_ms': item['elapsed_ms'],
            'error': item['error'],
            'masks': None,
        }
        if item['status'] == 'ok':
            entry['masks'] = {
                stage: {
                    'file': f"masks/{item['config_id']}_{stage}.png",
                    'sha256': _mask_sha256(item['masks'][stage]),
                } for stage in COMPARE_STAGES
            }
        results.append(entry)
    return {
        'schema_version': COMPARE_SCHEMA_VERSION,
        'comparison_id': record['comparison_id'],
        'created_at': record['created_at'],
        'exported_at': datetime.now().isoformat(),
        'environment': {
            'python': platform.python_version(),
            'opencv': cv2.__version__,
            'numpy': np.__version__,
        },
        'image': copy.deepcopy(record['image']),
        'target_color_id': record['target_color_id'],
        'evaluation_stage': record['evaluation_stage'],
        'fixed_pipeline': copy.deepcopy(record['fixed_pipeline']),
        'fingerprint': record['fingerprint'],
        'ranking_rule': COMPARE_RANKING_RULE,
        'configurations': configurations,
        'results': results,
        'evaluations': copy.deepcopy(record['evaluations']),
        'notes': [
            'Ảnh và GT gốc không được đóng gói; hãy upload lại file có cùng SHA-256.',
            'Metrics trong file là dữ liệu lịch sử, không phải kết quả của lượt chạy mới.',
        ],
    }


@app.route('/api/compare-hsv/export', methods=['POST'])
def compare_hsv_export():
    """Xuất ZIP gồm comparison.json (schema v1) và mask PNG của mọi cấu hình."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise CompareError('Body phải là JSON object')
        record = _get_comparison(data.get('session_id'), data.get('comparison_id'))
        with comparison_lock:
            manifest = build_export_manifest(record)
            pngs = {}
            for item in record['results']:
                if item['status'] != 'ok':
                    continue
                for stage in COMPARE_STAGES:
                    pngs[f"masks/{item['config_id']}_{stage}.png"] = _encode_png(item['masks'][stage])
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('comparison.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            for name, content in pngs.items():
                archive.writestr(name, content)
        buffer.seek(0)
        return send_file(
            buffer, mimetype='application/zip', as_attachment=True,
            download_name=f"{record['comparison_id']}.zip")
    except CompareError as exc:
        return _compare_error_response(exc)
    except Exception as exc:
        return jsonify({'error': f'Lỗi export so sánh: {exc}'}), 500


@app.route('/api/compare-hsv/import-config', methods=['POST'])
def compare_hsv_import_config():
    """
    Nhập comparison.json (multipart: session_id, config_file). Chỉ nhận JSON, tối đa 1 MiB.
    Khôi phục configs/pipeline, chạy lại trên ảnh hiện tại với comparison_id mới.
    Metrics cũ chỉ trả về dạng tham chiếu lịch sử khi hash ảnh khớp; không bao giờ gắn như kết quả mới.
    """
    try:
        session_id = request.form.get('session_id')
        entry = _get_session(session_id)
        upload = request.files.get('config_file')
        if upload is None:
            raise CompareError('Thiếu file config_file (comparison.json)')
        raw = upload.read(COMPARE_IMPORT_MAX_BYTES + 1)
        if len(raw) > COMPARE_IMPORT_MAX_BYTES:
            raise CompareError('File JSON vượt quá 1 MiB', 413)
        if raw[:2] == b'PK':
            raise CompareError('Chỉ nhập comparison.json, không nhập file ZIP')
        try:
            doc = json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            raise CompareError('File không phải JSON UTF-8 hợp lệ')
        if not isinstance(doc, dict):
            raise CompareError('JSON gốc phải là object')
        if doc.get('schema_version') != COMPARE_SCHEMA_VERSION or not _is_int(doc.get('schema_version')):
            raise CompareError(
                f"schema_version không được hỗ trợ: {doc.get('schema_version')!r} (cần {COMPARE_SCHEMA_VERSION})")

        # Chỉ lấy các trường cần thiết; mọi giá trị đều đi qua validator như request thường
        target = validate_target_color(doc.get('target_color_id'))
        configs = validate_compare_configs(doc.get('configurations'))
        pipeline = validate_fixed_pipeline(doc.get('fixed_pipeline'))
        stage = validate_stage(doc.get('evaluation_stage', 'raw'))
        image_meta = doc.get('image')
        if not isinstance(image_meta, dict) or not isinstance(image_meta.get('sha256'), str):
            raise CompareError("Thiếu image.sha256 trong JSON")
        imported_hash = image_meta['sha256'].lower()

        current_hash, _ = _session_image_hash(entry)
        hash_match = imported_hash == current_hash

        record = execute_comparison(session_id, entry, target, configs, pipeline, stage)
        payload = _comparison_payload(record)
        payload['status'] = 'success' if payload['all_ok'] else 'partial_error'
        payload['import'] = {
            'source_comparison_id': doc.get('comparison_id') if isinstance(doc.get('comparison_id'), str) else None,
            'image_hash_match': hash_match,
            'imported_image_sha256': imported_hash,
            'current_image_sha256': current_hash,
            'rerun_comparison_id': record['comparison_id'],
            'fingerprint_match': hash_match and doc.get('fingerprint') == record['fingerprint'],
            'warning': None if hash_match else
                'Ảnh hiện tại khác hash ảnh trong JSON: đã khôi phục cấu hình và chạy lại, '
                'nhưng KHÔNG gắn metrics cũ sang ảnh này.',
            # Metrics lịch sử chỉ để tham khảo, tách khỏi evaluations của lượt mới
            'historical_metrics': doc.get('evaluations') if hash_match and isinstance(doc.get('evaluations'), dict) else None,
        }
        return jsonify(payload)
    except CompareError as exc:
        return _compare_error_response(exc)
    except Exception as exc:
        return jsonify({'error': f'Lỗi nhập cấu hình: {exc}'}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Xử lý file quá lớn"""
    return jsonify({'error': 'File quá lớn (tối đa 50MB)'}), 413


@app.errorhandler(404)
def not_found(error):
    """Xử lý 404"""
    return jsonify({'error': 'Endpoint không tồn tại'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Xử lý lỗi server"""
    return jsonify({'error': 'Lỗi server nội bộ'}), 500


@app.route('/api/release-session', methods=['POST'])
def release_session():
    """Giải phóng session (bộ nhớ + file upload) của chính session đó."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('session_id'), str):
        return jsonify({'error': 'Thiếu session_id'}), 400
    return jsonify({'status': 'success', 'released': drop_session(data['session_id'])})


def _csv_bytes(rows):
    """CSV UTF-8-SIG, mọi ô chuỗi đi qua _csv_safe."""
    buf = io.StringIO(newline='')
    writer = csv.writer(buf, lineterminator='\r\n')
    for row in rows:
        writer.writerow([_csv_safe(c) if isinstance(c, str) else ('' if c is None else c) for c in row])
    return buf.getvalue().encode('utf-8-sig')


def _flatten_metrics(prefix_rows, metrics):
    keys = ('pixel_accuracy', 'iou', 'precision', 'recall', 'f1', 'TP', 'FP', 'FN', 'TN')
    return [prefix_rows + [k, metrics.get(k)] for k in keys if k in metrics]


@app.route('/api/export-results', methods=['POST'])
def export_results():
    """Xuất ZIP của đúng một lượt chạy: single (run_id) hoặc comparison (comparison_id)."""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise CompareError('Body phải là JSON object')
        session_id = data.get('session_id')
        entry = get_active_session(session_id)
        files = {}
        exported_at = datetime.now().isoformat()
        image_name = os.path.basename(str(entry.get('filename', '')))

        if data.get('comparison_id') is not None:
            record = _get_comparison(session_id, data.get('comparison_id'))
            with comparison_lock:
                manifest = build_export_manifest(record)
                files['comparison.json'] = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')
                gts = record.get('gt_masks', {})
                rows = [['config_id', 'stage', 'metric', 'value']]
                stage = record['evaluation_stage']
                ev = record['evaluations'].get(stage)
                for item in record['results']:
                    if item['status'] != 'ok':
                        continue
                    cid = item['config_id']
                    for st in COMPARE_STAGES:
                        files[f'masks/{cid}_{st}.png'] = _encode_png(item['masks'][st])
                    seg = cv2.bitwise_and(entry['image_bgr'], entry['image_bgr'], mask=item['masks'][stage])
                    files[f'segmented/{cid}_{stage}.png'] = _encode_png(seg)
                    if stage in gts:
                        vis = SegmentationEvaluator().create_visualization(item['masks'][stage], gts[stage])
                        files[f'visualization/{cid}_{stage}.png'] = _encode_png(vis)
                    m = ((ev or {}).get('metrics') or {}).get(cid)
                    if m:
                        for k, v in m.items():
                            rows.append([cid, stage, k, v])
                if len(rows) == 1:
                    rows.append(['N/A', 'N/A', 'N/A', 'N/A (chưa có GT)'])
                files['metrics.csv'] = _csv_bytes(rows)
                files['metrics.json'] = json.dumps(
                    {'evaluations': record['evaluations']}, ensure_ascii=False, indent=2).encode('utf-8')
            name = f"{record['comparison_id']}_export.zip"
        else:
            if 'mask_morph' not in entry:
                raise CompareError('Chưa xử lý ảnh', 400)
            run_id = entry.get('run_id', 0)
            req_run = data.get('run_id')
            if req_run is not None and req_run != run_id:
                raise CompareError('run_id không khớp lượt chạy hiện tại', 409)
            with session_lock:
                snap = {k: entry.get(k) for k in (
                    'image_bgr', 'mask_raw', 'mask_median', 'mask_morph', 'gt_mask', 'metrics',
                    'visualization', 'gt_sha256', 'metrics_run_id', 'applied_hsv', 'applied_config')}
            for st in ('raw', 'median', 'morph'):
                files[f'mask_{st}.png'] = _encode_png(snap[f'mask_{st}'])
            files['segmented.png'] = _encode_png(
                cv2.bitwise_and(snap['image_bgr'], snap['image_bgr'], mask=snap['mask_morph']))
            has_gt = snap['metrics'] is not None and snap['metrics_run_id'] == run_id
            if has_gt and snap['visualization'] is not None:
                files['visualization.png'] = _encode_png(snap['visualization'])
            files['config.json'] = json.dumps(
                {'hsv': snap['applied_hsv'], 'pipeline': snap['applied_config']},
                ensure_ascii=False, indent=2).encode('utf-8')
            files['run.json'] = json.dumps({
                'schema_version': 1, 'run_id': run_id, 'exported_at': exported_at,
                'image_filename': image_name,
                'image_sha256': _session_image_hash(entry)[0],
                'gt_sha256': snap['gt_sha256'] if has_gt else None,
                'has_ground_truth': bool(has_gt),
                'environment': {'python': platform.python_version(), 'opencv': cv2.__version__,
                                'numpy': np.__version__},
            }, ensure_ascii=False, indent=2).encode('utf-8')
            if has_gt:
                files['metrics.json'] = json.dumps(
                    snap['metrics'], ensure_ascii=False, indent=2).encode('utf-8')
                rows = [['run_id', 'metric', 'value']] + _flatten_metrics([run_id], snap['metrics'])
            else:
                files['metrics.json'] = json.dumps(
                    {'status': 'N/A', 'reason': 'Chưa có Ground Truth cho run này'}).encode('utf-8')
                rows = [['run_id', 'metric', 'value'], [run_id, 'N/A', 'N/A (chưa có GT)']]
            files['metrics.csv'] = _csv_bytes(rows)
            name = f'run_{run_id}_export.zip'

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            for fname, content in files.items():
                safe = fname.replace('\\', '/')
                if safe.startswith('/') or '..' in safe.split('/'):
                    raise CompareError('Tên file export không hợp lệ')
                archive.writestr(safe, content)
        buffer.seek(0)
        return send_file(buffer, mimetype='application/zip', as_attachment=True, download_name=name)
    except CompareError as exc:
        return jsonify({'error': str(exc)}), exc.status
    except Exception:
        logger.exception('export failed')
        return jsonify({'error': 'Lỗi export'}), 500


if __name__ == '__main__':
    print("Ứng dụng HSV Color Segmentation đang chạy (chỉ localhost)...")
    print("Truy cập: http://127.0.0.1:5000")
    print("Nhấn Ctrl+C để dừng")
    
    app.run(debug=False, host='127.0.0.1', port=5000)
