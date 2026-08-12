import sys
import os
from pathlib import Path
import streamlit as st

import sys
import os
from pathlib import Path
import streamlit as st

# 0. ==================== KÍCH HOẠT KHÓA BẢO MẬT OGSM ====================
def check_ogsm_password():
    if st.session_state.get("ogsm_authenticated", False):
        return True

    st.title("🔒 BẢO MẬT PHÂN HỆ OGSM")
    st.caption("Vui lòng nhập mật khẩu để truy cập hệ thống Quản trị OGSM.")

    # Đọc mật khẩu ogsm_password ở đầu file Secrets
    correct_password = st.secrets.get("ogsm_password")

    with st.form("ogsm_login_form"):
        user_input = st.text_input("Mật khẩu truy cập OGSM:", type="password")
        if st.form_submit_button("Đăng nhập"):
            if user_input == correct_password:
                st.session_state["ogsm_authenticated"] = True
                st.success("Xác thực thành công!")
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác!")
    
    st.stop() # Dừng không cho tải dữ liệu bên dưới nếu chưa đăng nhập

check_ogsm_password()

# Nút Đăng xuất ở góc màn hình
col_title, col_logout = st.columns([8, 2])
with col_logout:
    if st.button("🔒 Đăng xuất"):
        st.session_state["ogsm_authenticated"] = False
        st.rerun()

# 1. Định vị thư mục ogsm/ và đưa lên vị trí ƯU TIÊN HÀNG ĐẦU trong sys.path
OGSM_DIR = Path(__file__).resolve().parent.parent / "ogsm"
if str(OGSM_DIR) not in sys.path:
    sys.path.insert(0, str(OGSM_DIR))

# 2. Import các module nội bộ nằm trong thư mục ogsm/
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

# 3. Danh sách các trang con nằm trong thư mục ogsm/
ogsm_subpages = {
    "Dashboard": OGSM_DIR / "1_Dashboard.py",
    "OGSM Tree": OGSM_DIR / "2_OGSM_Tree.py",
    "Strategy Tracker": OGSM_DIR / "3_Strategy_Tracker.py",
    "Data Management": OGSM_DIR / "4_Data_Management.py"
}

# 4. Thanh chuyển phân hệ dạng nút bấm nằm ngang (Chữ thuần túy)
selected_page_name = st.radio(
    label="Phân hệ OGSM",
    options=list(ogsm_subpages.keys()),
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

# 5. Thực thi file giao diện tương ứng
target_file_path = ogsm_subpages[selected_page_name]

if target_file_path.exists():
    with open(target_file_path, encoding="utf-8") as f:
        code = f.read()
        exec(code, globals())
else:
    st.error(f"Không tìm thấy file giao diện tại: {target_file_path}")
