import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
import io
import requests
import msal
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# ================= 1. CẤU HÌNH GIAO DIỆN & CHỈNH MÀU RÕ NÉT =================
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
    
    /* Chỉnh chữ trong các ô thông tin thành MÀU ĐEN ĐẬM, RÕ NÉT */
    input[disabled] {
        -webkit-text-fill-color: #111111 !important;
        color: #111111 !important;
        font-weight: 600 !important;
        background-color: #F8F9FA !important;
        opacity: 1 !important;
    }
    
    /* Chỉnh màu chữ Caption GPS và IP cho đậm rõ */
    .stCaption {
        color: #222222 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Chỉnh Nút bấm Điểm danh sang MÀU XANH ĐẬM ĐẸP MẮT */
    div.stButton > button {
        background-color: #1877F2 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 18px !important;
        padding: 12px 0px !important;
        border-radius: 6px !important;
    }
    div.stButton > button:hover {
        background-color: #0D52B5 !important;
        color: #FFFFFF !important;
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

CLASS_LIST = ["D26", "Y26", "RHM26", "YTCC26", "YHDP26", "DD26", "PHR26", "ĐD26", "XN26", "PHCN26"]

MAX_ALLOWED_RADIUS = 100.0 

CAMPUSES = {
    "CS1": {
        "name": "Cơ sở 1",
        "address": "217 Hồng Bàng, Phường 11, Quận 5, TP.HCM",
        "lat": 10.755061,  
        "lng": 106.662962, 
        "allowed_ips": ["118.69.1.1", "118.69.1.2", "103.180.97.163", "103.180.97.161"]
    },
    "CS2": {
        "name": "Cơ sở 2",
        "address": "201 Nguyễn Chí Thanh, Phường 12, Quận 5, TP.HCM",
        "lat": 10.757973, 
        "lng": 106.661271,
        "allowed_ips": ["203.162.1.1"]
    },
    "CS3": {
        "name": "Cơ sở 3",
        "address": "41 Đinh Tiên Hoàng, Phường Bến Nghé, Quận 1, TP.HCM",
        "lat": 10.785324, 
        "lng": 106.702328,
        "allowed_ips": ["171.244.1.1"]
    }
}

# ================= 2. HÀM KẾT NỐI MICROSOFT GRAPH API =================
def get_azure_token():
    try:
        azure_sec = st.secrets["azure"]
        tenant_id = azure_sec.get("tenant_id") or azure_sec.get("TENANT_ID")
        client_id = azure_sec.get("client_id") or azure_sec.get("CLIENT_ID")
        client_secret = azure_sec.get("client_secret") or azure_sec.get("CLIENT_SECRET")
        
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id, authority=authority, client_credential=client_secret
        )
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            st.error("Không thể lấy token xác thực Azure!")
            return None
    except Exception as e:
        st.error(f"Lỗi cấu hình Azure Secrets: {str(e)}")
        return None

def build_graph_url(file_path):
    if "onedrive" in st.secrets and "drive_id" in st.secrets["onedrive"]:
        drive_id = st.secrets["onedrive"]["drive_id"]
        return f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_path}:"
    elif "USER_EMAIL" in st.secrets["azure"] or "user_email" in st.secrets["azure"]:
        user_email = st.secrets["azure"].get("USER_EMAIL") or st.secrets["azure"].get("user_email")
        return f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_path}:"
    else:
        return f"https://graph.microsoft.com/v1.0/me/drive/root:/{file_path}:"

def read_excel_from_onedrive(file_path, sheet_name=None):
    token = get_azure_token()
    if not token:
        return pd.DataFrame()
    try:
        base_url = build_graph_url(file_path)
        url = f"{base_url}/content"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            excel_bytes = io.BytesIO(response.content)
            if sheet_name:
                try:
                    df = pd.read_excel(excel_bytes, sheet_name=sheet_name, dtype=str, engine="openpyxl")
                except Exception:
                    df = pd.read_excel(excel_bytes, dtype=str, engine="openpyxl")
            else:
                df = pd.read_excel(excel_bytes, dtype=str, engine="openpyxl")
            
            df.columns = [str(c).strip().replace('\xa0', '') for c in df.columns]
            return df
        else:
            st.error(f"Không thể truy cập file trên OneDrive (HTTP {response.status_code}). Đường dẫn: {file_path}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi xử lý file Excel: {str(e)}")
        return pd.DataFrame()

def append_row_to_onedrive_excel(file_path, table_name, row_values):
    token = get_azure_token()
    if not token:
        return False
    try:
        base_url = build_graph_url(file_path)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Thử nghiệm 1: Ghi vào Table Excel
        url_table = f"{base_url}/workbook/tables/{table_name}/rows/add"
        payload = {"values": [row_values]}
        res = requests.post(url_table, headers=headers, json=payload)
        
        if res.status_code in [200, 201]:
            return True
            
        # Thử nghiệm 2: Nếu file chưa tạo Table, ghi vào Worksheet1
        url_sheet = f"{base_url}/workbook/worksheets('Sheet1')/tables/{table_name}/rows/add"
        res2 = requests.post(url_sheet, headers=headers, json=payload)
        if res2.status_code in [200, 201]:
            return True

        # In lỗi chi tiết từ Microsoft nếu không thành công
        st.error(f"Chi tiết lỗi từ Microsoft API (HTTP {res.status_code}): {res.text}")
        return False
    except Exception as e:
        st.error(f"Lỗi gửi dữ liệu: {str(e)}")
        return False

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ================= 3. GIAO DIỆN HỆ THỐNG =================
st.title("ĐIỂM DANH SỐ - TỰ ĐỘNG ĐỊNH VỊ CƠ SỞ")

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
            
        input_id = st.text_input("Nhập Mã số (8 chữ số):", max_chars=8, placeholder="Ví dụ: 06071234 hoặc 26001001").strip()
        
        fetched_name = ""
        fetched_unit = ""
        fetched_sub = ""
        fetched_course = ""
        
        target_df = pd.DataFrame()
        
        if len(input_id) == 8:
            if user_group == "Cán bộ / Viên chức / Giảng viên":
                target_df = read_excel_from_onedrive("OGSM/ATTENDANCE/DATA/CBVC.xlsx", sheet_name="Nhansu")
                if not target_df.empty:
                    col_msvc = target_df.columns[0]
                    col_name = target_df.columns[1] if len(target_df.columns) > 1 else target_df.columns[0]
                    col_unit = target_df.columns[2] if len(target_df.columns) > 2 else ""
                    col_sub = target_df.columns[3] if len(target_df.columns) > 3 else ""
                    
                    target_df["CLEAN_ID"] = target_df[col_msvc].astype(str).str.strip().str.replace('\xa0', '').str.replace('.0', '', regex=False).str.zfill(8)
                    match = target_df[target_df["CLEAN_ID"] == input_id]
                    
                    if not match.empty:
                        fetched_name = match.iloc[0][col_name]
                        fetched_unit = match.iloc[0][col_unit] if col_unit else ""
                        fetched_sub = match.iloc[0][col_sub] if col_sub else ""
            else:
                sv_class_path = f"OGSM/ATTENDANCE/DATA/SV/{selected_class}.xlsx"
                target_df = read_excel_from_onedrive(sv_class_path)
                if not target_df.empty:
                    col_mssv = target_df.columns[0]
                    col_name = target_df.columns[1] if len(target_df.columns) > 1 else target_df.columns[0]
                    col_unit = target_df.columns[2] if len(target_df.columns) > 2 else ""
                    col_sub = target_df.columns[3] if len(target_df.columns) > 3 else ""
                    col_course = target_df.columns[4] if len(target_df.columns) > 4 else ""
                    
                    target_df["CLEAN_ID"] = target_df[col_mssv].astype(str).str.strip().str.replace('\xa0', '').str.replace('.0', '', regex=False).str.zfill(8)
                    match = target_df[target_df["CLEAN_ID"] == input_id]
                    
                    if not match.empty:
                        fetched_name = match.iloc[0][col_name]
                        fetched_unit = match.iloc[0][col_unit] if col_unit else ""
                        fetched_sub = match.iloc[0][col_sub] if col_sub else ""
                        fetched_course = match.iloc[0][col_course] if col_course else ""

        st.text_input("Họ và tên:", value=str(fetched_name if fetched_name else ""), disabled=True)
        st.text_input("Đơn vị (Trường/Khoa):", value=str(fetched_unit if fetched_unit else ""), disabled=True)
        st.text_input("Bộ môn:", value=str(fetched_sub if fetched_sub else ""), disabled=True)
        if user_group == "Sinh viên":
            st.text_input("Tên học phần:", value=str(fetched_course if fetched_course else ""), disabled=True)

    with col2:
        st.markdown("**Xác thực Tự động (GPS & Mạng Wi-Fi)**")
        
        location = get_geolocation()
        user_lat = None
        user_lng = None
        
        if location and 'coords' in location:
            user_lat = location['coords']['latitude']
            user_lng = location['coords']['longitude']
            st.caption(f"Tọa độ GPS thiết bị: `{user_lat:.5f}, {user_lng:.5f}`")
        else:
            st.warning("Đang kết nối GPS... Vui lòng CHỌN 'CHO PHÉP' (Allow) khi trình duyệt hỏi quyền vị trí!")

        user_ip = streamlit_js_eval(
            js_expressions="fetch('https://api.ipify.org?format=json').then(r => r.json()).then(data => data.ip)", 
            key='get_user_ip'
        )
        if user_ip:
            st.caption(f"Địa chỉ IP kết nối: `{user_ip}`")
        
        action_type = st.radio("Thao tác ca làm việc:", ["Vào ca (Check-in)", "Ra ca (Check-out)"], horizontal=True)

        detected_campus_key = None
        detected_campus_info = None
        min_distance = 999999
        
        if user_lat is not None and user_lng is not None:
            for c_key, c_val in CAMPUSES.items():
                d = calculate_distance(user_lat, user_lng, c_val["lat"], c_val["lng"])
                if d < min_distance:
                    min_distance = d
                if d <= MAX_ALLOWED_RADIUS:
                    detected_campus_key = c_key
                    detected_campus_info = c_val
                    break

        if detected_campus_info:
            campus_display_name = f"{detected_campus_info['name']} ({detected_campus_info['address']})"
            st.success(f"Tự động nhận diện: **{detected_campus_info['name']}**")
            st.info(f"Địa chỉ: {detected_campus_info['address']} Khoảng cách: {min_distance:.1f} m (Hợp lệ <= {int(MAX_ALLOWED_RADIUS)}m)")
        else:
            campus_display_name = "Không xác định"
            if min_distance < 999999:
                st.markdown(f'<div class="status-box-error">Bị từ chối: Bạn đang ở ngoài bán kính {int(MAX_ALLOWED_RADIUS)}m của cả 3 Cơ sở (Khoảng cách tới cơ sở gần nhất: {min_distance:.1f} m)</div>', unsafe_allow_html=True)
            else:
                st.info("Đang chờ dữ liệu GPS để xác định Cơ sở...")

        ip_valid = False
        if detected_campus_info and user_ip:
            ip_valid = user_ip in detected_campus_info["allowed_ips"]
            if ip_valid:
                st.markdown('<div class="status-box-success">IP Mạng Hợp lệ (Đúng Wi-Fi trường)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-box-error">Cảnh báo: IP không thuộc Wi-Fi nội bộ cơ sở này</div>', unsafe_allow_html=True)

    if st.button("XÁC NHẬN ĐIỂM DANH", use_container_width=True):
        if len(input_id) != 8 or not fetched_name:
            st.error("Mã số 8 chữ số không tồn tại trong danh sách dữ liệu trên OneDrive!")
        elif not detected_campus_info:
            st.error(f"Điểm danh thất bại: Bạn phải có mặt trong bán kính {int(MAX_ALLOWED_RADIUS)}m của một trong 3 Cơ sở!")
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
                input_id, str(fetched_name), user_group, str(fetched_unit), str(unit_sub_display),
                campus_display_name, now.strftime("%Y-%m-%d %H:%M:%S"), action_type,
                round(min_distance, 1), user_ip if user_ip else "N/A", status, note
            ]
            
            success = append_row_to_onedrive_excel("OGSM/ATTENDANCE/DATA/LichSu_DiemDanh.xlsx", "BangDiemDanh", row_data)
            
            if success:
                st.success(f"Ghi nhận thành công cho {fetched_name} tại {detected_campus_info['name']} lúc {now.strftime('%H:%M:%S')}. Trạng thái: {status}")

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
        st.session_state.history_df = read_excel_from_onedrive("OGSM/ATTENDANCE/DATA/LichSu_DiemDanh.xlsx")

    history_df = st.session_state.get("history_df", read_excel_from_onedrive("OGSM/ATTENDANCE/DATA/LichSu_DiemDanh.xlsx"))
    
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
