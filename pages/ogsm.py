"""
OGSM Portal Main Application Router.
Uses st.navigation for explicit sidebar menu routing.
"""

import sys
import os
from pathlib import Path
import streamlit as st

# Thêm thư mục gốc của project vào sys.path để import các module (config, logger,...)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import các thư viện nội bộ
from config import load_config
from logger import get_logger

logger = get_logger()

# 1. Khai báo các trang trong hệ thống
dashboard_page = st.Page(
    "1_Dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
    default=True
)

ogsm_tree_page = st.Page(
    "2_OGSM_Tree.py",
    title="OGSM Tree",
    icon=":material/account_tree:"
)

strategy_tracker_page = st.Page(
    "3_Strategy_Tracker.py",
    title="Strategy Tracker",
    icon=":material/track_changes:"
)

data_management_page = st.Page(
    "4_Data_Management.py",
    title="Data Management",
    icon=":material/database:"
)

# 2. Khởi tạo Navigation Router
pg = st.navigation(
    {
        "Quản Trị Chiến Lược": [
            dashboard_page,
            ogsm_tree_page,
            strategy_tracker_page,
            data_management_page,
        ]
    }
)

# 3. Cấu hình trang & Sidebar Header
st.set_page_config(
    page_title="OGSM Portal - UMP",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("OGSM Portal")
st.sidebar.caption("Đại học Y Dược TP.HCM")
st.sidebar.markdown("---")

# 4. Thực thi trang được chọn
try:
    load_config()
    pg.run()
except Exception as e:
    st.error(f"Lỗi khởi chạy hệ thống: {e}")
