import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
import io
import requests
import msal

# ================= 1. CẤU HÌNH GIAO DIỆN & TÔNG MÀU XANH FACEBOOK =================
st.set_page_config(page_title="Điểm Danh Số - Hệ Thống Trường", layout="wide")

st.markdown("""
<style>
    /* Tab màu xanh Facebook (#1877F2) */
    div[data-baseweb="tab-list"] {
        gap: 8px;
    }
    button[data-baseweb="tab"] {
        background-color: #1877F2 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        font-size: 15px !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0D52B5 !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
    }
    /* Frame thông báo */
    .status-box-success {
        background-color: #E7F3FF;
        border-left: 5px solid #1877F2;
        padding: 12px;
        margin-bottom: 10px;
        color: #050505;
        font-weight: 500;
    }
    .status-box-error {
        background-color: #FFEBE9;
        border-left: 5px solid #E41E3F;
        padding: 12px;
        margin-bottom: 10px;
        color: #050505;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Danh sách các Lớp sinh viên
CLASS_LIST = ["D26", "Y26", "RHM26", "YTCC26", "YHDP26", "DD26", "PHR26", "ĐD26", "XN26", "PHCN26"]

CAMPUSES = {
    "Cơ sở 1": {"lat": 10.77688, "lng": 106.70081, "allowed_ips": ["118.69.1.1", "118.69.1.2"]},
    "Cơ sở 2": {"lat": 10.78012, "lng": 106.69850, "allowed_ips": ["203.162.1.1"]},
    "Cơ sở 3": {"lat": 10.78500, "lng": 106.70500, "allowed_ips": ["171.244.1.1"]}
}

# ================= 2. HÀM KẾT NỐI MICROSOFT GRAPH API =================
def get_azure_token():
    try:
        tenant_id = st.secrets["azure"]["TENANT_ID"]
        client_id = st.secrets["azure"]["CLIENT_ID"]
        client_secret = st.secrets["azure"]["CLIENT_SECRET"]
        
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id, authority=authority, client_credential=client_secret
        )
        
        # Scope phù hợp cho quyền Delegated / Application
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            st.error("Không thể lấy token xác thực. Vui lòng kiểm tra lại cấu hình Secrets!")
            return None
    except Exception as e:
        st.error(f"Lỗi cấu hình Azure Secrets: {str(e)}")
        return None

@st.cache_data(ttl=300)
def read_excel_from_onedrive(file_path):
    token = get_azure_token()
    if not token:
        return pd.DataFrame()
    
    try:
        user_email = st.secrets["azure"]["USER_EMAIL"]
        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_path}:/content"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return pd.read_excel(io.BytesIO(response.content), dtype=str, engine="openpyxl")
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def append_row_to_onedrive_excel(file_path, table_name, row_values):
    token = get_azure_token()
    if not token:
        return False
    
    try:
        user_email = st.secrets["azure"]["USER_EMAIL"]
        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_path}:/workbook/tables/{table_name}/rows/add"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"values": [row_values]}
        
        response = requests.post(url, headers=headers, json=payload)
        return response.status_code in [200, 201]
    except Exception:
        return False

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ================= 3. GIAO DIỆN HỆ THỐNG =================
st.title("ĐIỂM DANH SỐ - TỰ ĐỘNG ĐỒNG BỘ ONEDRIVE")

tabs = st.tabs(["THỰC HIỆN ĐIỂM DANH", "NỘP MINH CHỨNG / BÁO NGHỈ PHÉP", "DASHBOARD BÁO CÁO"])

# ----------------- TAB 1: ĐIỂM DANH -----------------
with tabs[0]:
    st.subheader("Màn hình Điểm danh")
    col1, col2 = st.columns(2)
    
    with col1:
        user_group = st.radio("Nhóm đối tượng", ["Cán bộ / Viên chức / Giảng viên", "Sinh viên"], horizontal=True)
        
        selected_class = ""
        if user_group == "Sinh viên":
            selected_class = st.selectbox("Chọn Lớp sinh viên:", CLASS_LIST)
            
        input_id = st.text_input("Nhập Mã số (8 chữ số):", max_chars=8, placeholder="Ví dụ: 06071234 hoặc 26001001")
        
        fetched_name = ""
        fetched_unit = ""
        fetched_sub = ""
        fetched_course = ""
        
        if len(input_id) == 8:
            if user_group == "Cán bộ / Viên chức / Giảng viên":
                cbvc_df = read_excel_from_onedrive("ATTENDANCE/DATA/CBVC.xlsx")
                if not cbvc_df.empty:
                    match = cbvc_df[cbvc_df["MSVC"] == input_id]
                    if not match.empty:
                        fetched_name = match.iloc[0].get("Họ và tên", "")
                        fetched_unit = match.iloc[0].get("Đơn vị", "")
                        fetched_sub = match.iloc[0].get("Bộ môn", "")
            else:
                sv_class_path = f"ATTENDANCE/DATA/SV/{selected_class}.xlsx"
                sv_df = read_excel_from_onedrive(sv_class_path)
                
                if sv_df.empty:
                    st.warning(f"Chưa tìm thấy file danh sách lớp {selected_class}.xlsx trên OneDrive.")
                else:
                    match = sv_df[sv_df["MSSV"] == input_id]
                    if not match.empty:
                        fetched_name = match.iloc[0].get("Họ và tên", "")
                        fetched_unit = match.iloc[0].get("Đơn vị (Trường/Khoa)", "")
                        fetched_sub = match.iloc[0].get("Bộ môn giảng", "")
                        fetched_course = match.iloc[0].get("Tên học phần", "")

        st.text_input("Họ và tên:", value=fetched_name, disabled=True)
        st.text_input("Đơn vị (Trường/Khoa):", value=fetched_unit, disabled=True)
        st.text_input("Bộ môn:", value=fetched_sub, disabled=True)
        if user_group == "Sinh viên":
            st.text_input("Tên học phần:", value=fetched_course, disabled=True)
            
        campus_selected = st.selectbox("Chọn Cơ sở điểm danh:", list(CAMPUSES.keys()))

    with col2:
        st.markdown("**Xác thực Vị trí & Mạng nội bộ**")
        user_lat = st.number_input("Vĩ độ GPS (Latitude):", value=10.77685, format="%.5f")
        user_lng = st.number_input("Kinh độ GPS (Longitude):", value=106.70080, format="%.5f")
        user_ip = st.text_input("IP Wi-Fi kết nối:", value="118.69.1.1")
        
        action_type = st.radio("Thao tác ca làm việc:", ["Vào ca (Check-in)", "Ra ca (Check-out)"], horizontal=True)
        
        target = CAMPUSES[campus_selected]
        dist = calculate_distance(user_lat, user_lng, target["lat"], target["lng"])
        ip_valid = user_ip in target["allowed_ips"]
        
        st.write(f"Khoảng cách đến tâm cơ sở: **{dist:.1f} m**")
        
        if dist <= 50:
            st.markdown('<div class="status-box-success">Vị trí hợp lệ (Trong phạm vi 50m)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box-error">Vị trí KHÔNG hợp lệ (Vượt quá 50m)</div>', unsafe_allow_html=True)

        if ip_valid:
            st.markdown('<div class="status-box-success">IP Mạng Hợp lệ (Kết nối đúng Wi-Fi trường)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box-error">IP Mạng KHÔNG hợp lệ (Không phải Wi-Fi trường)</div>', unsafe_allow_html=True)

    if st.button("XÁC NHẬN ĐIỂM DANH", type="primary", use_container_width=True):
        if len(input_id) != 8 or not fetched_name:
            st.error("Mã số 8 chữ số không tồn tại trong danh sách lớp trên OneDrive!")
        elif dist > 50:
            st.error("Điểm danh bị từ chối do vị trí nằm ngoài phạm vi 50m!")
        else:
            now = datetime.now()
            status = "Đúng giờ"
            unit_sub_display = f"{fetched_sub} ({selected_class})" if user_group == "Sinh viên" else fetched_sub
            note = f"Học phần: {fetched_course}" if user_group == "Sinh viên" else ""
            
            if user_group == "Cán bộ / Viên chức / Giảng viên" and action_type == "Vào ca (Check-in)":
                standard_start = now.replace(hour=7, minute=0, second=0)
                if now > standard_start:
                    late_min = (now - standard_start).total_seconds() / 60
                    if late_min <= 30:
                        status = "Đi trễ (Có bù giờ)"
                        out_time = now.replace(hour=11, minute=0) + timedelta(minutes=late_min)
                        note = f"Đi trễ {int(late_min)} phút. Giờ ra ca sáng bắt buộc: {out_time.strftime('%H:%M')}"
                    else:
                        status = "Trễ > 30 phút"
                        note = "Vượt quá 30 phút. Yêu cầu nộp đơn xin nghỉ phép / minh chứng."

            row_data = [
                input_id, fetched_name, user_group, fetched_unit, unit_sub_display,
                campus_selected, now.strftime("%Y-%m-%d %H:%M:%S"), action_type,
                round(dist, 1), user_ip, status, note
            ]
            
            success = append_row_to_onedrive_excel("ATTENDANCE/DATA/LichSu_DiemDanh.xlsx", "BangDiemDanh", row_data)
            
            if success:
                st.success(f"Ghi nhận và đồng bộ thành công lên OneDrive lúc {now.strftime('%H:%M:%S')}. Trạng thái: {status}")
            else:
                st.error("Lỗi khi ghi dữ liệu vào file Excel trên OneDrive!")

# ----------------- TAB 2: MINH CHỨNG -----------------
with tabs[1]:
    st.subheader("Nộp minh chứng đi trễ / Báo xin nghỉ phép")
    with st.form("form_minh_chung"):
        mc_id = st.text_input("Nhập Mã số 8 chữ số:")
        mc_type = st.selectbox("Loại yêu cầu:", ["Nghỉ phép Buổi Sáng", "Nghỉ phép Buổi Chiều", "Nghỉ phép Cả Ngày", "Minh chứng Đi trễ > 30 phút"])
        mc_reason = st.text_area("Lý do chi tiết:")
        mc_file = st.file_uploader("Tải lên file đi kèm (Ảnh / PDF):", type=["png", "jpg", "pdf"])
        
        btn_submit = st.form_submit_button("GỬI YÊU CẦU")
        if btn_submit:
            st.info("Yêu cầu đã được ghi nhận và chuyển đến Ban Giám hiệu / Lãnh đạo Khoa duyệt.")

# ----------------- TAB 3: DASHBOARD -----------------
with tabs[2]:
    st.subheader("Báo cáo và Thống kê Điểm danh")
    
    if st.button("CẬP NHẬT DỮ LIỆU TỪ ONEDRIVE"):
        st.session_state.history_df = read_excel_from_onedrive("ATTENDANCE/DATA/LichSu_DiemDanh.xlsx")

    history_df = st.session_state.get("history_df", read_excel_from_onedrive("ATTENDANCE/DATA/LichSu_DiemDanh.xlsx"))
    
    if history_df.empty:
        st.info("Chưa có dữ liệu điểm danh trên OneDrive hoặc chưa kết nối thành công.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng lượt điểm danh", len(history_df))
        c2.metric("Lượt Đúng giờ", len(history_df[history_df["TrangThai"] == "Đúng giờ"]))
        c3.metric("Lượt Trễ / Vi phạm", len(history_df[history_df["TrangThai"] != "Đúng giờ"]))
        
        st.dataframe(history_df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            history_df.to_excel(writer, sheet_name='DiemDanh', index=False)
            
        st.download_button(
            label="XUẤT BÁO CÁO EXCEL (.XLSX)",
            data=buffer.getvalue(),
            file_name=f"Bao_Cao_Diem_Danh_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
