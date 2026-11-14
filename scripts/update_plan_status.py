# -*- coding: utf-8 -*-
"""
Script: update_plan_status.py
Cập nhật trạng thái tiến độ của Anh Quân trong file kế hoạch Excel.
"""

import openpyxl

FILE = 'Ke_Hoach_Phan_Chia_Cong_Viec_HSV_N05.xlsx'

NOTES = {
    2: 'Màu mục tiêu: Đỏ (Hue [0-10] ∪ [170-180]). Tiêu chí chọn ảnh + quy ước dữ liệu ghi tại data/README.md',
    3: '10 ảnh JPG trong data/images/ (img_01..img_10), đặt tên thống nhất, đủ 10 tình huống',
    4: '10 Ground Truth PNG nhị phân 0/255 tại data/ground_truth/, sinh cùng lúc vẽ ảnh nên khớp 100%, đã rà soát thủ công',
    5: 'src/data_loader.py: load_image_gt_pair(), build_dataset(), load_metadata(), validate_pair(), full_check()',
    6: 'Kiểm tra shape/dtype/số kênh/giá trị Mask + báo cáo kiểm tra dữ liệu. Kết quả: 10/10 cặp đạt, 0 lỗi',
    7: 'data/metadata.csv: 16 cột, 10 dòng, mã ảnh + tình huống + thống kê HSV + ghi chú',
    8: 'tests/test_data.py: 26 test đạt (gồm nhóm TestRealDataset trên bộ dữ liệu thật). report/data_handover_results.csv',
    9: 'report/data.md kèm 5 hình minh họa thật trong report/figures/',
}

wb = openpyxl.load_workbook(FILE)

# ------------------------------------------------------------------
# 1) Sheet "Anh Quân - Dữ liệu"
# ------------------------------------------------------------------
ws = wb['Anh Quân - Dữ liệu']
for row in range(2, 10):
    ws.cell(row, 11).value = 'Hoàn thành'
    ws.cell(row, 12).value = 1.0
    ws.cell(row, 13).value = NOTES.get(row, '')

# ------------------------------------------------------------------
# 2) Sheet "Tổng quan"
# ------------------------------------------------------------------
ws = wb['Tổng quan']
ws.cell(3, 5).value = 8          # Hoàn thành
ws.cell(3, 6).value = 1.0        # Tiến độ
ws.cell(3, 8).value = 'Bàn giao data/images (10 ảnh) + data/ground_truth (10 GT) + data/metadata.csv, kiểm thử 26/26 đạt, báo cáo report/data.md'

total_done = 8 + 7              # Anh Quân + Hoàn
ws.cell(7, 5).value = total_done
ws.cell(7, 6).value = total_done / 40

# ------------------------------------------------------------------
# 3) Sheet "Kế hoạch 14 ngày" - các dòng của Anh Quân
# ------------------------------------------------------------------
ws = wb['Kế hoạch 14 ngày']
plan_notes = {
    3:  'Đã chốt màu đỏ và tiêu chí chọn ảnh tại data/README.md',
    8:  '10 ảnh tại data/images/, đặt tên img_NN_<tinh_huong>.jpg',
    13: '10 Ground Truth tại data/ground_truth/, khớp pixel tuyệt đối với ảnh',
    18: 'src/data_loader.py hoàn chỉnh, load_image_gt_pair() chạy độc lập',
    23: 'Báo cáo kiểm tra dữ liệu: 10/10 cặp hợp lệ, 0 lệch kích thước',
    28: 'Bổ sung đủ tình huống nền sáng/tối/màu gần giống/bóng đổ/ánh sáng yếu/cháy sáng/nhiễu',
    33: 'data/ hoàn chỉnh + metadata.csv + data/README.md',
    38: 'Bàn giao module: 26/26 test đạt, pipeline chạy end-to-end 10/10 ảnh',
    43: 'Đã rà soát: không còn cặp ảnh/GT lệch kích thước',
    48: 'Đã bàn giao bảng ảnh khó img_06/img_07/img_08 kèm nhận xét tình huống trong report/data.md',
    53: 'report/data.md bản hoàn chỉnh kèm 5 hình minh họa thật',
    58: 'Bộ hình đã chú thích nằm tại report/figures/',
    63: 'Sẵn sàng rà soát slide dữ liệu cùng nhóm',
    68: 'Dataset demo đầy đủ 10 ảnh + 10 GT, vị trí data/images và data/ground_truth',
}
for row in range(1, ws.max_row + 1):
    if ws.cell(row, 2).value == 'Anh Quân':
        ws.cell(row, 6).value = 'Hoàn thành'
        ws.cell(row, 7).value = 1.0
        ws.cell(row, 8).value = plan_notes.get(row, '')

wb.save(FILE)
print('Da cap nhat trang thai Excel.')
