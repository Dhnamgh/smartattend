"""
OGSM Portal - Phân hệ Quản trị Chiến lược UMP
"""

import sys
import os
from pathlib import Path
import streamlit as st

# 1. Thêm thư mục gốc dự án vào sys.path để import config, logger...
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import các thư viện nội bộ của OGSM
from config import load_config
from logger import get_logger

logger = get_logger()

# Nạp cấu hình hệ thống OGSM
try:
    load_config()
except Exception as e:
    logger.error(f"Lỗi load config OGSM: {e}")

# 2. Tiêu đề phân hệ OGSM
st.title("QUẢN TRỊ CHIẾN LƯỢC OGSM")
st.caption("Đại học Y Dược TP.HCM")

# 3. Danh sách các trang con (Đã BỎ HOÀN TOÀN Icon và chỉ định đúng đường dẫn trong pages/)
ogsm_subpages = {
    "Dashboard": "pages/1_Dashboard.py",
    "OGSM Tree": "pages/2_OGSM_Tree.py",
    "Strategy Tracker": "pages/3_Strategy_Tracker.py",
    "Data Management": "pages/4_Data_Management.py"
}

# 4. Thanh chuyển phân hệ dạng nút bấm nằm ngang (Thay thế cho st.navigation cũ)
selected_page_name = st.radio(
    label="Phân hệ OGSM",
    options=list(ogsm_subpages.keys()),
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# 5. Thực thi file giao diện tương ứng với phân hệ được chọn
target_file_path = ogsm_subpages[selected_page_name]

if os.path.exists(target_file_path):
    with open(target_file_path, encoding="utf-8") as f:
        code = f.read()
        exec(code, globals())
else:
    st.error(f"Không tìm thấy file giao diện: {target_file_path}")
