import sys
import os
from pathlib import Path

# 1. Ép Python nhận diện thư mục gốc làm môi trường tìm kiếm module
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from config import load_config
from logger import get_logger

logger = get_logger()

try:
    load_config()
except Exception as e:
    logger.error(f"Lỗi load config OGSM: {e}")

# ================= GIAO DIỆN PHÂN HỆ OGSM =================
st.title("QUẢN TRỊ CHIẾN LƯỢC OGSM")
st.caption("Đại học Y Dược TP.HCM")

# Đường dẫn trỏ trực tiếp đến các file ở thư mục gốc (như cấu trúc trong ảnh)
ogsm_subpages = {
    "Dashboard": "1_Dashboard.py",
    "OGSM Tree": "2_OGSM_Tree.py",
    "Strategy Tracker": "3_Strategy_Tracker.py",
    "Data Management": "4_Data_Management.py"
}

# Thanh menu chuyển phân hệ dạng nút nằm ngang (Không icon)
selected_page_name = st.radio(
    label="Phân hệ OGSM",
    options=list(ogsm_subpages.keys()),
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# Load và chạy trực tiếp file tương ứng
target_file_path = ogsm_subpages[selected_page_name]

if os.path.exists(target_file_path):
    with open(target_file_path, encoding="utf-8") as f:
        code = f.read()
        exec(code, globals())
else:
    st.error(f"Không tìm thấy file giao diện: {target_file_path}")
