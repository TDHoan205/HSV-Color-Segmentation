# -*- coding: utf-8 -*-
"""
Script: generate_dataset.py
Chức năng: Sinh bộ ảnh đầu vào + Ground Truth Mask cho bài toán phân đoạn màu HSV
Phụ trách: Anh Quân (Dữ liệu & Ground Truth)

Mục đích:
    Tạo bộ dữ liệu mẫu tất định (deterministic) gồm 10 ảnh màu đỏ trên nền đa dạng
    kèm Ground Truth nhị phân 0/255 có độ chính xác 100% (mask được vẽ cùng lúc
    với vật thể, không dùng kết quả dự đoán làm nhãn - tuân thủ Quy ước 3).

Cách chạy:
    python scripts/generate_dataset.py
    python scripts/generate_dataset.py --output data --seed 42

Kết quả:
    data/images/*.jpg          - ảnh đầu vào
    data/ground_truth/*.png     - Ground Truth Mask (uint8, 0/255)
    data/metadata.csv           - metadata mô tả tình huống từng ảnh
"""

import argparse
import csv
import os
import sys

import cv2
import numpy as np

# Kích thước chuẩn của mọi ảnh trong bộ dữ liệu
IMG_WIDTH = 480
IMG_HEIGHT = 360

# Màu đỏ chuẩn theo thứ tự BGR (OpenCV)
RED_BGR = (28, 28, 214)


# ----------------------------------------------------------------------
# Tiện ích vẽ
# ----------------------------------------------------------------------

def _base_canvas(height=IMG_HEIGHT, width=IMG_WIDTH, color=(210, 210, 210)):
    """Tạo nền đơn sắc."""
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[:, :] = color
    return canvas


def _add_gradient_background(height, width, top_bgr, bottom_bgr, horizontal=False):
    """Tạo nền chuyển sắc dọc (hoặc ngang)."""
    canvas = np.zeros((height, width, 3), dtype=np.float32)
    top = np.array(top_bgr, dtype=np.float32)
    bottom = np.array(bottom_bgr, dtype=np.float32)

    if horizontal:
        ramp = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :, None]
    else:
        ramp = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None, None]

    canvas[:] = top[None, None, :] * (1.0 - ramp) + bottom[None, None, :] * ramp
    return np.clip(canvas, 0, 255).astype(np.uint8)


def _add_noise(canvas, sigma=4.0, rng=None):
    """Thêm nhiễu cảm giác máy ảnh (Gaussian) vào ảnh."""
    rng = rng or np.random.default_rng(0)
    noise = rng.normal(0.0, sigma, canvas.shape).astype(np.float32)
    return np.clip(canvas.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def _shade_object(shape_mask, canvas, light_center, strength=0.45):
    """
    Tạo hiệu ứng đổ bóng trên vật thể: vùng gần nguồn sáng sáng hơn,
    vùng xa nguồn sáng tối hơn. Chỉ đổi độ sáng (V), không đổi Hue nên
    vẫn giữ được màu đỏ mục tiêu.
    """
    h, w = canvas.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = light_center
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    dist = dist / (dist.max() + 1e-6)
    field = 1.0 - strength * dist

    shaded = canvas.astype(np.float32) * field[:, :, None]
    out = canvas.copy()
    out[shape_mask > 0] = shaded[shape_mask > 0].astype(np.uint8)
    return out


def _cast_shadow(canvas, mask, offset=(18, 14), blur=13, strength=0.55):
    """
    Đổ bóng của vật thể lên nền: vùng bóng chỉ nằm trên nền (không phủ vật thể),
    vì vậy KHÔNG đưa vào Ground Truth.
    """
    h, w = canvas.shape[:2]
    shadow = cv2.GaussianBlur(mask.astype(np.float32), (blur, blur), 0)

    M = np.float32([[1, 0, offset[0]], [0, 1, offset[1]]])
    shadow = cv2.warpAffine(shadow, M, (w, h))
    shadow = np.clip(shadow * strength, 0, 1)

    darkened = canvas.astype(np.float32) * (1.0 - shadow[:, :, None])
    out = np.clip(darkened, 0, 255).astype(np.uint8)

    # Vật thể vẫn giữ nguyên màu gốc (bóng không phủ lên vật thể)
    out[mask > 0] = canvas[mask > 0]
    return out


def _circular_mean_hue(hue_values):
    """
    Tính trung bình Hue theo góc (circular mean).

    Hue trong OpenCV chạy vòng tròn 0 -> 179 -> 0, nên trung bình cộng thông
    thường vô lý: trung bình của 2 và 178 là 90 (vàng) thay vì ~0 (đỏ).
    """
    if hue_values.size == 0:
        return 0.0
    angles = hue_values.astype(np.float64) * (2.0 * np.pi / 180.0)
    mean_angle = np.arctan2(np.sin(angles).mean(), np.cos(angles).mean())
    if mean_angle < 0:
        mean_angle += 2.0 * np.pi
    value = mean_angle * 180.0 / (2.0 * np.pi)
    # Hue chu kỳ theo vòng 0 -> 180 -> 0, chuẩn hóa về [0, 180)
    value = float(value % 180.0)
    if value > 179.5:
        value = 0.0
    return value


def _draw_shape(canvas, mask, shape, params, bgr):
    """
    Vẽ một vật thể màu lên canvas và ghi vùng tương ứng vào mask.

    Vật thể được tô màu THÔNG QUA mask (nhị phân) nên mọi pixel thuộc vật thể
    đều mang đúng màu đích, và Ground Truth khớp tuyệt đối với ảnh đầu vào.
    """
    layer_mask = np.zeros(canvas.shape[:2], dtype=np.uint8)

    if shape == 'circle':
        (cx, cy), r = params
        cv2.circle(layer_mask, (cx, cy), r, 255, -1, cv2.LINE_8)
    elif shape == 'ellipse':
        (cx, cy), (ax, ay), angle = params
        cv2.ellipse(layer_mask, (cx, cy), (ax, ay), angle, 0, 360, 255, -1, cv2.LINE_8)
    elif shape == 'rect':
        (x, y), (w, h) = params
        cv2.rectangle(layer_mask, (x, y), (x + w, y + h), 255, -1, cv2.LINE_8)
    elif shape == 'triangle':
        pts = np.array(params, dtype=np.int32)
        cv2.fillPoly(layer_mask, [pts], 255, cv2.LINE_8)
    else:
        raise ValueError(f"Hình dạng không hỗ trợ: {shape}")

    # Tô màu vật thể theo đúng vùng mask
    canvas = canvas.copy()
    canvas[layer_mask > 0] = bgr

    return canvas, cv2.bitwise_or(mask, layer_mask)


# ----------------------------------------------------------------------
# Các kịch bản ảnh
# ----------------------------------------------------------------------

def build_scenes(rng):
    """
    Định nghĩa 10 kịch bản ảnh, mỗi kịch bản là một tình huống khác nhau về
    nền, ánh sáng và đối tượng. Giá trị trả về là danh sách dict mô tả scene.
    """
    scenes = [
        {
            'id': 'img_01',
            'name': 'red_circle_light_bg',
            'scenario': 'nen_sang',
            'background': 'Nền trắng sáng (trung tính)',
            'lighting': 'Ánh sáng đều, không bóng',
            'note': 'Trường hợp cơ sở: vật thể đỏ rõ nét trên nền sáng',
            'bg': ('solid', (232, 232, 232)),
            'objects': [('circle', ((240, 180), 78), RED_BGR)],
            'shadow': None,
            'shade': (320, 90, 0.40),
            'noise': 3.0,
        },
        {
            'id': 'img_02',
            'name': 'red_square_dark_bg',
            'scenario': 'nen_toi',
            'background': 'Nền xanh đen tối',
            'lighting': 'Ánh sáng yếu, vật thể sáng hơn nền nhiều',
            'note': 'Kiểm tra ngưỡng Value khi nền tối',
            'bg': ('solid', (34, 26, 22)),
            'objects': [('rect', ((160, 110), (165, 140)), RED_BGR)],
            'shadow': None,
            'shade': (250, 60, 0.30),
            'noise': 4.0,
        },
        {
            'id': 'img_03',
            'name': 'red_triangle_shadow',
            'scenario': 'bom_do',
            'background': 'Nền xám trung tính',
            'lighting': 'Nguồn sáng lệch, có bóng đổ sang phải',
            'note': 'Bóng đổ là nền, KHÔNG thuộc Ground Truth',
            'bg': ('solid', (168, 168, 164)),
            'objects': [('triangle', [[150, 250], [320, 250], [235, 95]], RED_BGR)],
            'shadow': ((26, 16), 15, 0.55),
            'shade': (300, 80, 0.35),
            'noise': 4.0,
        },
        {
            'id': 'img_04',
            'name': 'red_multi_objects',
            'scenario': 'nhieu_doi_tuong',
            'background': 'Nền xám sáng',
            'lighting': 'Ánh sáng đều',
            'note': 'Ba vật thể khác hình dạng, kiểm tra gộp vùng đối tượng',
            'bg': ('solid', (196, 196, 192)),
            'objects': [
                ('circle', ((105, 130), 52), RED_BGR),
                ('rect', ((205, 175), (95, 95)), RED_BGR),
                ('ellipse', ((375, 220), (62, 38), 25), RED_BGR),
            ],
            'shadow': None,
            'shade': (330, 70, 0.35),
            'noise': 4.0,
        },
        {
            'id': 'img_05',
            'name': 'red_on_orange_bg',
            'scenario': 'mau_gan_giong',
            'background': 'Nền cam (Hue gần vùng đỏ)',
            'lighting': 'Ánh sáng đều',
            'note': 'Nền có Hue lân cận màu đích - ngưỡng Hue hẹp phải loại được nền',
            'bg': ('solid', (46, 150, 226)),
            'objects': [('circle', ((245, 175), 70), RED_BGR)],
            'shadow': None,
            'shade': (320, 90, 0.35),
            'noise': 4.0,
        },
        {
            'id': 'img_06',
            'name': 'red_on_pink_bg',
            'scenario': 'mau_gan_giong_kho',
            'background': 'Nền hồng đậm (Hue ~172, nằm trong khoảng đỏ thứ hai)',
            'lighting': 'Ánh sáng đều',
            'note': 'Trường hợp khó: Hue nền rơi vào khoảng [170-180] và S cao - ngưỡng mặc định sẽ tách nhầm nền',
            'bg': ('solid', (70, 0, 255)),
            'objects': [('rect', ((170, 95), (150, 165)), RED_BGR)],
            'shadow': None,
            'shade': (320, 80, 0.30),
            'noise': 3.0,
        },
        {
            'id': 'img_07',
            'name': 'red_low_light',
            'scenario': 'anh_sang_yeu',
            'background': 'Nền xám tối',
            'lighting': 'Ánh sáng yếu, toàn cảnh thiếu sáng',
            'note': 'Vật thể có V thấp - kiểm tra ngưỡng Value',
            'bg': ('solid', (72, 68, 66)),
            'objects': [('circle', ((240, 180), 74), (25, 25, 95))],
            'shadow': None,
            'shade': (320, 90, 0.30),
            'noise': 5.0,
        },
        {
            'id': 'img_08',
            'name': 'red_overexposed',
            'scenario': 'anh_sang_manh',
            'background': 'Nền trắng cháy sáng',
            'lighting': 'Ánh sáng quá mạnh, vật thể bị nhạt màu',
            'note': 'Trường hợp khó: S thấp do cháy sáng - kiểm tra ngưỡng Saturation',
            'bg': ('solid', (250, 250, 250)),
            'objects': [('circle', ((240, 180), 72), (170, 175, 235))],
            'shadow': None,
            'shade': (320, 90, 0.15),
            'noise': 4.0,
        },
        {
            'id': 'img_09',
            'name': 'red_gradient_light',
            'scenario': 'anh_sang_khong_deu',
            'background': 'Nền chuyển sắc xanh lá sang trắng',
            'lighting': 'Ánh sáng không đều, một vùng sáng một vùng tối',
            'note': 'Kiểm tra ảnh có nhiều vùng sáng khác nhau trong cùng ảnh',
            'bg': ('gradient', (58, 168, 112), (226, 226, 226)),
            'objects': [('ellipse', ((240, 185), (95, 60), 0), RED_BGR)],
            'shadow': None,
            'shade': (360, 60, 0.40),
            'noise': 4.0,
        },
        {
            'id': 'img_10',
            'name': 'red_noisy_dark_bg',
            'scenario': 'nhieu_tin_hieu',
            'background': 'Nền tối nhiều nhiễu',
            'lighting': 'Ánh sáng yếu kèm nhiễu sensor mạnh',
            'note': 'Kiểm tra vai trò của Median Filter trên Mask thô',
            'bg': ('solid', (58, 52, 50)),
            'objects': [('circle', ((240, 180), 70), (44, 40, 170))],
            'shadow': None,
            'shade': (320, 90, 0.35),
            'noise': 16.0,
        },
    ]
    return scenes


# ----------------------------------------------------------------------
# Sinh ảnh + Ground Truth
# ----------------------------------------------------------------------

def render_scene(scene, rng):
    """
    Dựng một ảnh và Ground Truth tương ứng.

    Returns:
        (image_bgr, gt_mask, stats)
    """
    kind = scene['bg'][0]
    if kind == 'solid':
        canvas = _base_canvas(IMG_HEIGHT, IMG_WIDTH, scene['bg'][1])
    elif kind == 'gradient':
        canvas = _add_gradient_background(IMG_HEIGHT, IMG_WIDTH, scene['bg'][1], scene['bg'][2])
    else:
        raise ValueError(f"Nền không hỗ trợ: {kind}")

    mask = np.zeros((IMG_HEIGHT, IMG_WIDTH), dtype=np.uint8)

    # 1) Vẽ vật thể (đồng thời tạo mask)
    for shape, params, bgr in scene['objects']:
        canvas, mask = _draw_shape(canvas, mask, shape, params, bgr)

    # 2) Đổ bóng lên nền (không đụng tới mask)
    if scene.get('shadow'):
        offset, blur, strength = scene['shadow']
        canvas = _cast_shadow(canvas, mask, offset=offset, blur=blur, strength=strength)

    # 3) Tạo hiệu ứng đổ bóng trên vật thể
    if scene.get('shade'):
        lx, ly, strength = scene['shade']
        canvas = _shade_object(mask, canvas, (lx, ly), strength)

    # 4) Nhiễu cảm giác máy ảnh
    canvas = _add_noise(canvas, sigma=scene.get('noise', 4.0), rng=rng)

    # 5) Thuốc tính thống kê HSV của vùng đối tượng (phục vụ metadata/báo cáo)
    hsv = cv2.cvtColor(canvas, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    obj = mask > 0
    h_obj = h[obj].astype(np.float32)
    stats = {
        'object_pixels': int(obj.sum()),
        'object_ratio': round(float(obj.mean()), 4),
        # Hue là đại lượng tuần hoàn (0-179 rồi về 0) nên phải lấy trung bình
        # theo góc, nếu không trung bình số học sẽ sai (ví dụ 2 và 178 -> 90)
        'h_mean': round(float(_circular_mean_hue(h_obj)), 1),
        'h_min': int(h[obj].min()),
        'h_max': int(h[obj].max()),
        's_mean': round(float(s[obj].mean()), 1),
        's_min': int(s[obj].min()),
        'v_mean': round(float(v[obj].mean()), 1),
        'v_min': int(v[obj].min()),
    }
    return canvas, mask, stats


def generate(output_dir='data', seed=42):
    """Sinh toàn bộ bộ dữ liệu và ghi ra đĩa."""
    images_dir = os.path.join(output_dir, 'images')
    gt_dir = os.path.join(output_dir, 'ground_truth')
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(gt_dir, exist_ok=True)

    rng = np.random.default_rng(seed)
    scenes = build_scenes(rng)
    rows = []

    for scene in scenes:
        image, gt_mask, stats = render_scene(scene, rng)

        img_name = f"{scene['id']}_{scene['name']}.jpg"
        gt_name = f"{scene['id']}_{scene['name']}.png"

        cv2.imwrite(os.path.join(images_dir, img_name), image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cv2.imwrite(os.path.join(gt_dir, gt_name), gt_mask)

        rows.append({
            'image_id': scene['id'],
            'image_file': f"data/images/{img_name}",
            'gt_file': f"data/ground_truth/{gt_name}",
            'width': IMG_WIDTH,
            'height': IMG_HEIGHT,
            'target_color': 'Red',
            'scenario': scene['scenario'],
            'background': scene['background'],
            'lighting': scene['lighting'],
            'object_count': len(scene['objects']),
            'object_pixels': stats['object_pixels'],
            'object_ratio': stats['object_ratio'],
            'h_mean': stats['h_mean'],
            's_mean': stats['s_mean'],
            'v_mean': stats['v_mean'],
            'note': scene['note'],
        })

        print(f"  [{scene['id']}] {img_name:<40} tinh huong={scene['scenario']:<22} "
              f"HSV(mean)={stats['h_mean']}/{stats['s_mean']}/{stats['v_mean']}")

    # Ghi metadata.csv
    csv_path = os.path.join(output_dir, 'metadata.csv')
    fieldnames = list(rows[0].keys())
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDa tao xong: {len(rows)} cap anh + Ground Truth")
    print(f"  - {images_dir}")
    print(f"  - {gt_dir}")
    print(f"  - {csv_path}")
    return rows


def main():
    parser = argparse.ArgumentParser(description="Sinh bo du lieu HSV mau do")
    parser.add_argument('--output', default='data', help='Thu muc dau ra')
    parser.add_argument('--seed', type=int, default=42, help='Seed cho tinh lap')
    args = parser.parse_args()

    print(f"Sinh bo du lieu (output={args.output}, seed={args.seed})...")
    generate(args.output, args.seed)


if __name__ == '__main__':
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
