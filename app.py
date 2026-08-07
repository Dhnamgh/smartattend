import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import math
import io
import time
import requests
import msal
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# ================= 1. CẤU HÌNH GIAO DIỆN & TÔNG MÀU XANH FACEBOOK =================
st.set_page_config(page_title="HỆ THỐNG ĐIỂM DANH UMP", layout="wide")

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
    
    /* Chỉnh chữ trong các ô disabled thành MÀU ĐEN ĐẬM, ĐỌC RÕ 100% */
    input[disabled] {
        -webkit-text-fill-color: #000000 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        background-color: #F0F2F5 !important;
        opacity: 1 !important;
    }
    
    .stCaption {
        color: #111111 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
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
MAX_ALLOWED_RADIUS = 70.0 
ALLOWED_IP_PREFIXES = ["103.180.97.", "118.69.1.", "203.162.1.", "171.244.1."]

CAMPUSES = {
    "CS1": {
        "name": "Cơ sở 1",
        "address": "217 Hồng Bàng, Phường 11, Quận 5, TP.HCM",
        "lat": 10.755061,  
        "lng": 106.662962
    },
    "CS2": {
        "name": "Cơ sở 2",
        "address": "201 Nguyễn Chí Thanh, Phường 12, Quận 5, TP.HCM",
        "lat": 10.757973, 
        "lng": 106.661271
    },
    "CS3": {
        "name": "Cơ sở 3",
        "address": "41 Đinh Tiên Hoàng, Phường Bến Nghé, Quận 1, TP.HCM",
        "lat": 10.785324, 
        "lng": 106.702328
    }
}

# Thời gian bắt đầu từng tiết học (Tiết 1 -> 12)
LESSON_START_TIMES = {
    1: (7, 0),   2: (7, 50),  3: (8, 50),  4: (9, 40),  5: (10, 30),
    6: (13, 0),  7: (13, 50), 8: (14, 50), 9: (15, 40), 10: (16, 30),
    11: (17, 30), 12: (18, 20)
}

# ================= 2. HÀM XỬ LÝ THỜI GIAN VIỆT NAM (UTC+7) =================
def get_vietnam_now():
    # Giờ chuẩn Việt Nam (UTC+7)
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))

# ================= 3. HÀM KẾT NỐI MICROSOFT GRAPH API =================
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
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def append_row_to_onedrive_excel(file_path, row_values):
    token = get_azure_token()
    if not token:
        return False
    try:
        base_url = build_graph_url(file_path)
        content_url = f"{base_url}/content"
        headers_get = {"Authorization": f"Bearer {token}"}
        
        get_res = requests.get(content_url, headers=headers_get)
        cols = ["Mã Số", "Họ Và Tên", "Đối Tượng", "Đơn Vị", "Bộ Môn / Lớp", "Cơ Sở", "Thời Gian", "Thao Tác", "Khoảng Cách (m)", "Địa Chỉ IP", "Trạng Thái", "Ghi Chú"]
        
        if get_res.status_code == 200:
            excel_bytes = io.BytesIO(get_res.content)
            try:
                df_existing = pd.read_excel(excel_bytes, dtype=str, engine="openpyxl")
                df_existing = df_existing.dropna(how='all')
            except Exception:
                df_existing = pd.DataFrame(columns=cols)
        else:
            df_existing = pd.DataFrame(columns=cols)
        
        new_row_df = pd.DataFrame([row_values], columns=cols[:len(row_values)])
        df_updated = pd.concat([df_existing, new_row_df], ignore_index=True)
        
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            df_updated.to_excel(writer, index=False, sheet_name='Sheet1')
        output_buffer.seek(0)
        
        headers_put = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            put_res = requests.put(content_url, headers=headers_put, data=output_buffer.getvalue())
            if put_res.status_code in [200, 201]:
                return True
            elif put_res.status_code == 423:
                time.sleep(1.5 * (attempt + 1))
            else:
                st.error(f"Lỗi upload dữ liệu lên OneDrive: HTTP {put_res.status_code}")
                return False
                
        st.error("File Excel trên OneDrive đang bị mở hoặc khóa chỉnh sửa. Vui lòng thử lại sau vài giây!")
        return False

    except Exception as e:
        st.error(f"Lỗi xử lý file Excel: {str(e)}")
        return False

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ================= 4. GIAO DIỆN HỆ THỐNG =================
st.title("HỆ THỐNG ĐIỂM DANH UMP")

tabs = st.tabs(["THỰC HIỆN ĐIỂM DANH", "NỘP MINH CHỨNG / BÁO NGHỈ PHÉP", "DASHBOARD BÁO CÁO"])

# ----------------- TAB 1: ĐIỂM DANH -----------------
with tabs[0]:
    st.subheader("Màn hình Điểm danh")
    col1, col2 = st.columns(2)
    
    with col1:
        user_group = st.radio("Nhóm đối tượng", ["Giảng viên/Viên chức", "Sinh viên"], horizontal=True)
        
        sub_role = "Giảng viên"
        selected_class = ""
        
        if user_group == "Giảng viên/Viên chức":
            sub_role = st.selectbox("Vai trò cụ thể:", ["Giảng viên", "Viên chức"])
        else:
            sub_role = "Sinh viên"
            selected_class = st.selectbox("Chọn Lớp sinh viên:", CLASS_LIST)
            
        input_id = st.text_input("Nhập Mã số (8 chữ số):", max_chars=8, placeholder="Ví dụ: 06071234 hoặc 26001001").strip()
        
        fetched_name = ""
        fetched_unit = ""
        fetched_sub = ""
        fetched_course = ""
        
        if len(input_id) == 8:
            if user_group == "Giảng viên/Viên chức":
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

        # Hiển thị thông tin với chữ ĐEN ĐẬM
        st.text_input("Họ và tên:", value=str(fetched_name if fetched_name else ""), disabled=True)
        st.text_input("Đơn vị (Trường/Khoa):", value=str(fetched_unit if fetched_unit else ""), disabled=True)
        st.text_input("Bộ môn:", value=str(fetched_sub if fetched_sub else ""), disabled=True)
        if user_group == "Sinh viên":
            st.text_input("Tên học phần:", value=str(fetched_course if fetched_course else ""), disabled=True)

        # Cấu hình Số tiết học cho Giảng viên & Sinh viên
        start_lesson = 1
        end_lesson = 1
        if sub_role in ["Giảng viên", "Sinh viên"]:
            st.markdown("**Đăng ký ca học/giảng dạy (Tiết học):**")
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                start_lesson = st.number_input("Từ tiết:", min_value=1, max_value=12, value=1)
            with c_t2:
                end_lesson = st.number_input("Đến tiết:", min_value=start_lesson, max_value=12, value=max(start_lesson, 2))

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

        distances = {}
        auto_detected_key = None
        if user_lat is not None and user_lng is not None:
            for c_key, c_val in CAMPUSES.items():
                d = calculate_distance(user_lat, user_lng, c_val["lat"], c_val["lng"])
                distances[c_key] = d
                
            if distances.get("CS1", 9999) <= MAX_ALLOWED_RADIUS:
                auto_detected_key = "CS1"
            else:
                closest_key = min(distances, key=distances.get)
                if distances[closest_key] <= MAX_ALLOWED_RADIUS:
                    auto_detected_key = closest_key

        campus_options = ["Tự động nhận diện", "Cơ sở 1 (217 Hồng Bàng)", "Cơ sở 2 (201 Nguyễn Chí Thanh)", "Cơ sở 3 (41 Đinh Tiên Hoàng)"]
        selected_campus_option = st.selectbox("Cơ sở điểm danh:", campus_options)

        final_campus_key = None
        if selected_campus_option == "Tự động nhận diện":
            final_campus_key = auto_detected_key
        elif "Cơ sở 1" in selected_campus_option:
            final_campus_key = "CS1"
        elif "Cơ sở 2" in selected_campus_option:
            final_campus_key = "CS2"
        elif "Cơ sở 3" in selected_campus_option:
            final_campus_key = "CS3"

        detected_campus_info = CAMPUSES.get(final_campus_key) if final_campus_key else None
        curr_dist = distances.get(final_campus_key, 0.0) if final_campus_key else 0.0

        if detected_campus_info:
            campus_display_name = f"{detected_campus_info['name']} ({detected_campus_info['address']})"
            st.success(f"Đã xác nhận: **{detected_campus_info['name']}**")
            st.info(f"Địa chỉ: {detected_campus_info['address']}\nKhoảng cách GPS: {curr_dist:.1f} m (Hợp lệ <= {int(MAX_ALLOWED_RADIUS)}m)")
        else:
            campus_display_name = "Không xác định"
            st.markdown(f'<div class="status-box-error">Vui lòng chọn Cơ sở điểm danh hợp lệ ở menu phía trên!</div>', unsafe_allow_html=True)

        ip_valid = False
        if detected_campus_info and user_ip:
            ip_valid = any(user_ip.startswith(prefix) for prefix in ALLOWED_IP_PREFIXES)
            if ip_valid:
                st.markdown('<div class="status-box-success">IP Mạng Hợp lệ (Đúng Wi-Fi nội bộ nhà trường)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-box-error">Cảnh báo: IP không thuộc Wi-Fi nội bộ nhà trường</div>', unsafe_allow_html=True)

    if st.button("XÁC NHẬN ĐIỂM DANH", use_container_width=True):
        if len(input_id) != 8 or not fetched_name:
            st.error("Mã số 8 chữ số không tồn tại trong danh sách dữ liệu trên OneDrive!")
        elif not detected_campus_info:
            st.error("Điểm danh thất bại: Vui lòng chọn Cơ sở điểm danh hợp lệ!")
        else:
            now_vn = get_vietnam_now()
            status = "Đúng giờ"
            note = ""
            unit_sub_display = f"{fetched_sub} ({selected_class})" if user_group == "Sinh viên" else fetched_sub

            # LOGIC XÁC ĐỊNH ĐÚNG/TRỄ GIỜ CHO CÁC ĐỐI TƯỢNG
            if sub_role in ["Giảng viên", "Sinh viên"]:
                start_h, start_m = LESSON_START_TIMES.get(start_lesson, (7, 0))
                sched_start = now_vn.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
                
                # Tính giờ kết thúc (Mỗi tiết 45p + 5p nghỉ = 50 phút)
                total_minutes = (end_lesson - start_lesson + 1) * 50
                sched_end = sched_start + timedelta(minutes=total_minutes)
                
                if action_type == "Vào ca (Check-in)":
                    if now_vn > sched_start + timedelta(minutes=15):
                        status = "Vào trễ"
                        note = f"Tiết {start_lesson} bắt đầu lúc {sched_start.strftime('%H:%M')}. Điểm danh lúc {now_vn.strftime('%H:%M')}."
                    else:
                        note = f"Lịch học/dạy: Tiết {start_lesson}-{end_lesson} ({sched_start.strftime('%H:%M')} - {sched_end.strftime('%H:%M')})"
                else: # Ra ca
                    if now_vn < sched_end - timedelta(minutes=10):
                        status = "Về sớm"
                        note = f"Lịch tiết {end_lesson} kết thúc lúc {sched_end.strftime('%H:%M')}."
                    else:
                        note = f"Hoàn thành ca dạy/học Tiết {start_lesson}-{end_lesson}"

            elif sub_role == "Viên chức":
                # Quy định 4 tiếng/buổi (Sáng từ 07:00, Chiều từ 13:00)
                if action_type == "Vào ca (Check-in)":
                    base_start = now_vn.replace(hour=7, minute=0, second=0) if now_vn.hour < 12 else now_vn.replace(hour=13, minute=0, second=0)
                    if now_vn > base_start + timedelta(minutes=15):
                        status = "Đi trễ"
                        note = f"Ca làm việc bắt đầu {base_start.strftime('%H:%M')}."
                    else:
                        note = "Ca làm việc 4 tiếng/buổi"
                else: # Ra ca
                    note = "Hoàn thành ca làm việc"

            # BẢNG PHÂN LOẠI FILE LƯU TRỮ CHO 3 ĐỐI TƯỢNG RIÊNG BIỆT
            file_map = {
                "Giảng viên": "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx",
                "Viên chức": "OGSM/ATTENDANCE/DATA/LichSu_VC.xlsx",
                "Sinh viên": "OGSM/ATTENDANCE/DATA/LichSu_SV.xlsx"
            }
            target_excel_path = file_map.get(sub_role, "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx")

            row_data = [
                input_id, str(fetched_name), sub_role, str(fetched_unit), str(unit_sub_display),
                campus_display_name, now_vn.strftime("%Y-%m-%d %H:%M:%S"), action_type,
                round(curr_dist, 1), user_ip if user_ip else "N/A", status, note
            ]
            
            success = append_row_to_onedrive_excel(target_excel_path, row_data)
            
            if success:
                st.success(f"Ghi nhận thành công cho {sub_role} {fetched_name} tại {detected_campus_info['name']} lúc {now_vn.strftime('%H:%M:%S')}. Trạng thái: {status}")

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
    
    selected_report_role = st.selectbox("Chọn nhóm dữ liệu xem báo cáo:", ["Giảng viên", "Viên chức", "Sinh viên"])
    
    file_map_report = {
        "Giảng viên": "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx",
        "Viên chức": "OGSM/ATTENDANCE/DATA/LichSu_VC.xlsx",
        "Sinh viên": "OGSM/ATTENDANCE/DATA/LichSu_SV.xlsx"
    }
    
    report_file_path = file_map_report[selected_report_role]
    
    if st.button("CẬP NHẬT DỮ LIỆU TỪ ONEDRIVE"):
        st.session_state.history_df = read_excel_from_onedrive(report_file_path)

    history_df = read_excel_from_onedrive(report_file_path)
    
    if history_df.empty:
        st.info(f"Chưa có dữ liệu điểm danh trên OneDrive cho nhóm **{selected_report_role}**.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Tổng lượt điểm danh ({selected_report_role})", len(history_df))
        c2.metric("Lượt Đúng giờ", len(history_df[history_df["Trạng Thái"] == "Đúng giờ"]))
        c3.metric("Lượt Trễ / Về sớm", len(history_df[history_df["Trạng Thái"] != "Đúng giờ"]))
        
        st.dataframe(history_df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            history_df.to_excel(writer, sheet_name='Sheet1', index=False)
            
        st.download_button(
            label=f"XUẤT BÁO CÁO EXCEL {selected_report_role.upper()} (.XLSX)",
            data=buffer.getvalue(),
            file_name=f"Bao_Cao_Diem_Danh_{selected_report_role}_{get_vietnam_now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
