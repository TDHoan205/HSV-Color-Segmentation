# -*- coding: utf-8 -*-
"""
Flask Backend Application
Ứng dụng Web xử lý ảnh HSV - Tách và nhận biết màu

Chạy: python main.py
Truy cập: http://localhost:5000
"""

import os
import json
import cv2
import numpy as np
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import base64

from data_loader import DataLoader
from hsv_segment import HSVSegmenter
from median_filter import MedianFilter
from morphology import MorphologyOperator
from evaluation import SegmentationEvaluator

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
        
        # Lưu file
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Đọc ảnh
        image_bgr, error = load_image_safe(filepath)
        if error:
            return jsonify({'error': error}), 400
        
        # Lưu vào session
        session_id = datetime.now().isoformat()
        session_data[session_id] = {
            'image_bgr': image_bgr,
            'filepath': filepath,
            'filename': file.filename,
            'timestamp': datetime.now(),
        }
        
        # Trả về thông tin ảnh
        h, w = image_bgr.shape[:2]
        return jsonify({
            'session_id': session_id,
            'width': w,
            'height': h,
            'image_base64': image_to_base64(image_bgr),
            'filename': file.filename,
        })
        
    except Exception as e:
        return jsonify({'error': f'Lỗi upload: {str(e)}'}), 500


@app.route('/api/process', methods=['POST'])
def process_image():
    """Xử lý ảnh với các cấu hình"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session không tồn tại'}), 400
        
        image_bgr = session_data[session_id]['image_bgr'].copy()
        
        # Cấu hình HSV
        hsv_config = {
            'color_name': 'Red',
            'hue_ranges': [
                [int(data.get('h_min_1', 0)), int(data.get('h_max_1', 10))],
                [int(data.get('h_min_2', 170)), int(data.get('h_max_2', 180))]
            ],
            'saturation': [int(data.get('s_min', 100)), int(data.get('s_max', 255))],
            'value': [int(data.get('v_min', 100)), int(data.get('v_max', 255))],
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
        
        # Morphology
        morph_kernel = int(data.get('morph_kernel', 5))
        if morph_kernel % 2 == 0:
            morph_kernel += 1
        
        operator = MorphologyOperator(morph_kernel, 'ellipse')
        operations = []
        
        if data.get('use_closing', True):
            operations.append(('close', {'iterations': 1}))
        
        if data.get('use_opening', False):
            operations.append(('open', {'iterations': 1}))
        
        if operations:
            mask_morph = operator.apply_sequence(mask_median, operations)
        else:
            mask_morph = mask_median
        
        # Lưu kết quả vào session
        session_data[session_id].update({
            'mask_raw': mask_raw,
            'mask_median': mask_median,
            'mask_morph': mask_morph,
            'image_hsv': image_hsv,
        })
        
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
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Lỗi xử lý: {str(e)}'}), 500


@app.route('/api/download-mask', methods=['POST'])
def download_mask():
    """Tải xuống Mask"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        mask_type = data.get('mask_type', 'morph')  # raw, median, morph
        
        if session_id not in session_data:
            return jsonify({'error': 'Session không tồn tại'}), 400
        
        mask_key = f'mask_{mask_type}'
        if mask_key not in session_data[session_id]:
            return jsonify({'error': f'Mask {mask_type} không được tính toán'}), 400
        
        mask = session_data[session_id][mask_key]
        
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
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """Đánh giá với Ground Truth"""
    try:
        if 'ground_truth' not in request.files:
            return jsonify({'error': 'Không có Ground Truth file'}), 400
        
        data = request.form
        session_id = data.get('session_id')
        gt_file = request.files['ground_truth']
        
        if session_id not in session_data:
            return jsonify({'error': 'Session không tồn tại'}), 400
        
        if 'mask_morph' not in session_data[session_id]:
            return jsonify({'error': 'Chưa xử lý ảnh'}), 400
        
        # Lưu Ground Truth
        gt_filename = secure_filename(f"gt_{session_id}.png")
        gt_filepath = os.path.join(app.config['UPLOAD_FOLDER'], gt_filename)
        gt_file.save(gt_filepath)
        
        # Đọc Ground Truth
        gt_mask, error = load_image_safe(gt_filepath)
        if error:
            return jsonify({'error': error}), 400
        
        # Chuyển sang grayscale
        if len(gt_mask.shape) == 3:
            gt_mask = cv2.cvtColor(gt_mask, cv2.COLOR_BGR2GRAY)
        
        # Nhị phân hóa
        gt_mask = cv2.threshold(gt_mask, 127, 255, cv2.THRESH_BINARY)[1]
        
        # Đánh giá
        pred_mask = session_data[session_id]['mask_morph']
        
        if pred_mask.shape != gt_mask.shape:
            return jsonify({
                'error': f'Kích thước Mask không khớp - Dự đoán: {pred_mask.shape}, GT: {gt_mask.shape}'
            }), 400
        
        evaluator = SegmentationEvaluator()
        metrics = evaluator.compute_metrics(pred_mask, gt_mask)
        vis = evaluator.create_visualization(pred_mask, gt_mask)
        
        # Lưu
        session_data[session_id].update({
            'gt_mask': gt_mask,
            'metrics': metrics,
            'visualization': vis,
        })
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'visualization': image_to_base64(vis),
        })
        
    except Exception as e:
        return jsonify({'error': f'Lỗi đánh giá: {str(e)}'}), 500


@app.route('/api/get-info', methods=['GET'])
def get_info():
    """Lấy thông tin HSV của ảnh"""
    try:
        session_id = request.args.get('session_id')
        
        if session_id not in session_data:
            return jsonify({'error': 'Session không tồn tại'}), 400
        
        if 'image_hsv' not in session_data[session_id]:
            return jsonify({'error': 'Chưa tính HSV'}), 400
        
        image_hsv = session_data[session_id]['image_hsv']
        mask_raw = session_data[session_id]['mask_raw']
        
        # Lấy thông tin HSV
        info = HSVSegmenter.get_hsv_info(image_hsv, mask_raw)
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Kiểm tra sức khỏe server"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
    })


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


if __name__ == '__main__':
    print("🚀 Ứng dụng HSV Color Segmentation đang chạy...")
    print("📖 Truy cập: http://localhost:5000")
    print("🛑 Nhấn Ctrl+C để dừng")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
