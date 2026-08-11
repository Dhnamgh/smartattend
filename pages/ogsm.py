import sys
import os
from pathlib import Path
import streamlit as st

# 1. Định vị và nạp môi trường cho thư mục ogsm/
OGSM_DIR = Path(__file__).resolve().parent.parent / "ogsm"
if str(OGSM_DIR) not in sys.path:
    sys.path.insert(0, str(OGSM_DIR))

from config import load_config
from logger import get_logger

logger = get_logger()

try:
    load_config()
except Exception as e:
    logger.error(f"Lỗi load config OGSM: {e}")

# 2. Tiêu đề phân hệ
st.title("QUẢN TRỊ CHIẾN LƯỢC OGSM")
st.caption("Đại học Y Dược TP.HCM")

# 3. Danh sách trang con trỏ thẳng vào thư mục ogsm/
ogsm_subpages = {
    "Dashboard": OGSM_DIR / "1_Dashboard.py",
    "OGSM Tree": OGSM_DIR / "2_OGSM_Tree.py",
    "Strategy Tracker": OGSM_DIR / "3_Strategy_Tracker.py",
    "Data Management": OGSM_DIR / "4_Data_Management.py"
}

# 4. Thanh chuyển trang dạng nút bấm nằm ngang (Chữ thuần túy, không Icon)
selected_page_name = st.radio(
    label="Phân hệ OGSM",
    options=list(ogsm_subpages.keys()),
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# 5. Thực thi trang được chọn
target_file_path = ogsm_subpages[selected_page_name]

if target_file_path.exists():
    with open(target_file_path, encoding="utf-8") as f:
        code = f.read()
        exec(code, globals())
else:
    st.error(f"Không tìm thấy file giao diện tại: {target_file_path}")
