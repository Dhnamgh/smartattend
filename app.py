import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import math
import io
import time
import requests
import msal
import plotly.express as px
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# ================= 1. CẤU HÌNH GIAO DIỆN & STYLE =================
st.set_page_config(page_title="HỆ THỐNG ĐIỂM DANH UMP", layout="wide")

st.markdown("""
<style>
    div[data-baseweb="tab-list"] { gap: 6px; }
    button[data-baseweb="tab"] {
        background-color: #1877F2 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        padding: 8px 16px !important;
        font-weight: bold !important;
        font-size: 14px !important;
        border: none !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0D52B5 !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
    }
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
        font-size: 13px !important;
    }
    div.stButton > button {
        background-color: #1877F2 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 17px !important;
        padding: 10px 0px !important;
        border-radius: 6px !important;
    }
    div.stButton > button:hover {
        background-color: #0D52B5 !important;
        color: #FFFFFF !important;
    }
    .status-box-success {
        background-color: #E7F3FF;
        border-left: 5px solid #1877F2;
        padding: 10px;
        margin-bottom: 8px;
        color: #050505;
        font-weight: 500;
    }
    .status-box-error {
        background-color: #FFEBE9;
        border-left: 5px solid #E41E3F;
        padding: 10px;
        margin-bottom: 8px;
        color: #050505;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

CLASS_LIST = ["D26", "Y26", "RHM26", "YTCC26", "YHDP26", "DD26", "PHR26", "ĐD26", "XN26", "PHCN26"]
MAX_ALLOWED_RADIUS = 100.0 
ALLOWED_IP_PREFIXES = ["103.180.97.", "118.69.1.", "203.162.1.", "171.244.1."]

CAMPUSES = {
    "CS1": {"name": "Cơ sở 1", "address": "217 Hồng Bàng, Phường 11, Quận 5, TP.HCM", "lat": 10.754748, "lng": 106.6663334},
    "CS2": {"name": "Cơ sở 2", "address": "201 Nguyễn Chí Thanh, Phường 12, Quận 5, TP.HCM", "lat": 10.757973, "lng": 106.661271},
    "CS3": {"name": "Cơ sở 3", "address": "41 Đinh Tiên Hoàng, Phường Bến Nghé, Quận 1, TP.HCM", "lat": 10.785324, "lng": 106.702328}
}

LESSON_TIMES_THEORY = {
    1:  {"start": (7, 0),   "end": (7, 50)},
    2:  {"start": (7, 50),  "end": (8, 40)},
    3:  {"start": (8, 50),  "end": (9, 40)},
    4:  {"start": (9, 40),  "end": (10, 30)},
    5:  {"start": (10, 30), "end": (11, 20)},
    6:  {"start": (13, 0),  "end": (13, 50)},
    7:  {"start": (13, 50), "end": (14, 40)},
    8:  {"start": (14, 50), "end": (15, 40)},
    9:  {"start": (15, 40), "end": (16, 30)},
    10: {"start": (16, 30), "end": (17, 20)}
}

LESSON_TIMES_PRACTICE = {
    1:  {"start": (7, 30),  "end": (8, 20)},
    2:  {"start": (8, 20),  "end": (9, 10)},
    3:  {"start": (9, 10),  "end": (10, 0)},
    4:  {"start": (10, 0),  "end": (10, 50)},
    5:  {"start": (10, 50), "end": (11, 40)},
    6:  {"start": (13, 30), "end": (14, 20)},
    7:  {"start": (14, 20), "end": (15, 10)},
    8:  {"start": (15, 10), "end": (16, 0)},
    9:  {"start": (16, 0),  "end": (16, 50)},
    10: {"start": (16, 50), "end": (17, 40)}
}

def get_vietnam_now():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))

# ================= 2. HÀM KẾT NỐI MICROSOFT GRAPH API =================
def get_azure_token():
    try:
        azure_sec = st.secrets["azure"]
        tenant_id = azure_sec.get("tenant_id") or azure_sec.get("TENANT_ID")
        client_id = azure_sec.get("client_id") or azure_sec.get("CLIENT_ID")
        client_secret = azure_sec.get("client_secret") or azure_sec.get("CLIENT_SECRET")
        
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
        scopes = ["https://graph.microsoft.com/.default"]
        result = app.acquire_token_for_client(scopes=scopes)
        return result.get("access_token")
    except Exception:
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
    if not token: return pd.DataFrame()
    try:
        url = f"{build_graph_url(file_path)}/content"
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            excel_bytes = io.BytesIO(response.content)
            df = pd.read_excel(excel_bytes, sheet_name=sheet_name if sheet_name else 0, dtype=str, engine="openpyxl")
            df.columns = [str(c).strip().replace('\xa0', '') for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def append_row_to_onedrive_excel(file_path, row_values, custom_cols=None):
    token = get_azure_token()
    if not token: return False
    try:
        base_url = build_graph_url(file_path)
        content_url = f"{base_url}/content"
        get_res = requests.get(content_url, headers={"Authorization": f"Bearer {token}"})
        
        default_cols = ["Mã Số", "Họ Và Tên", "Đối Tượng", "Đơn Vị", "Bộ Môn / Lớp", "Cơ Sở", "Thời Gian", "Thao Tác", "Khoảng Cách (m)", "Địa Chỉ IP", "Trạng Thái", "Ghi Chú"]
        cols = custom_cols if custom_cols else default_cols
        
        if get_res.status_code == 200:
            try:
                df_existing = pd.read_excel(io.BytesIO(get_res.content), dtype=str, engine="openpyxl").dropna(how='all')
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
        
        headers_put = {"Authorization": f"Bearer {token}", "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        for attempt in range(3):
            put_res = requests.put(content_url, headers=headers_put, data=output_buffer.getvalue())
            if put_res.status_code in [200, 201]: return True
            elif put_res.status_code == 423: time.sleep(1.5 * (attempt + 1))
            else: return False
        return False
    except Exception:
        return False

def upload_file_to_onedrive(folder_path, file_name, file_bytes):
    token = get_azure_token()
    if not token: return False
    try:
        full_path = f"{folder_path}/{file_name}"
        content_url = f"{build_graph_url(full_path)}/content"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        res = requests.put(content_url, headers=headers, data=file_bytes)
        return res.status_code in [200, 201]
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
st.title("HỆ THỐNG ĐIỂM DANH UMP")
tabs = st.tabs(["Điểm danh", "Báo nghỉ phép", "Dashboard"])

# ----------------- TAB 1: ĐIỂM DANH -----------------
with tabs[0]:
    col1, col2 = st.columns(2)
    now_vn = get_vietnam_now()
    is_out_of_hours = (now_vn.hour >= 18) or (now_vn.hour < 6)
    
    with col1:
        user_role = st.radio("Chọn đối tượng:", ["Giảng viên", "Viên chức", "Sinh viên"], horizontal=True)
        
        selected_class = ""
        if user_role == "Sinh viên":
            selected_class = st.selectbox("Chọn Lớp sinh viên:", CLASS_LIST)
            
        input_id = st.text_input("Nhập Mã số (8 chữ số):", max_chars=8, placeholder="Ví dụ: 06071234 hoặc 26001001", key="t1_id").strip()
        
        fetched_name, fetched_unit, fetched_sub, fetched_course = "", "", "", ""
        
        if len(input_id) == 8:
            if user_role in ["Giảng viên", "Viên chức"]:
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

        st.text_input("Họ và tên:", value=str(fetched_name if fetched_name else ("Mã số chưa chính xác" if len(input_id)==8 else "")), disabled=True)
        st.text_input("Đơn vị (Trường/Khoa):", value=str(fetched_unit), disabled=True)
        st.text_input("Bộ môn:", value=str(fetched_sub), disabled=True)
        if user_role == "Sinh viên":
            st.text_input("Tên học phần:", value=str(fetched_course), disabled=True)

        start_lesson, end_lesson = 1, 1
        lesson_schedule = LESSON_TIMES_THEORY
        study_type = "Lý thuyết"
        vc_shift = "Ca Sáng (07:00 - 11:00)"

        # HIỂN THỊ KHUNG CHỌN TIẾT / CA CHỈ KHI TRONG GIỜ LÀM VIỆC (06:00 - 18:00)
        if is_out_of_hours:
            st.markdown('<div class="status-box-error">Hệ thống đã đóng điểm danh. Hiện tại nằm ngoài khung giờ làm việc / học tập quy định (06:00 - 18:00)!</div>', unsafe_allow_html=True)
        else:
            if user_role in ["Giảng viên", "Sinh viên"]:
                study_type = st.radio("Hình thức:", ["Lý thuyết", "Thực hành"], horizontal=True)
                lesson_schedule = LESSON_TIMES_PRACTICE if study_type == "Thực hành" else LESSON_TIMES_THEORY
                
                valid_start_lessons = []
                for t in range(1, 11):
                    t_end_h, t_end_m = lesson_schedule[t]["end"]
                    t_end_dt = now_vn.replace(hour=t_end_h, minute=t_end_m, second=0, microsecond=0)
                    if now_vn <= t_end_dt or (t >= 6 and now_vn.hour < 12): 
                        valid_start_lessons.append(t)
                
                if not valid_start_lessons: valid_start_lessons = list(range(1, 11))

                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    start_lesson = st.selectbox("Từ tiết:", valid_start_lessons, index=0)
                
                with c_t2:
                    if start_lesson <= 5:
                        valid_end_lessons = [t for t in range(start_lesson, 6)]
                    else:
                        valid_end_lessons = [t for t in range(start_lesson, 11)]
                        
                    end_lesson = st.selectbox("Đến tiết:", valid_end_lessons, index=min(1, len(valid_end_lessons)-1))
                    
                s_h, s_m = lesson_schedule[start_lesson]["start"]
                e_h, e_m = lesson_schedule[end_lesson]["end"]
                st.caption(f"Thời gian ca ({study_type}): **{s_h:02d}:{s_m:02d} - {e_h:02d}:{e_m:02d}**")

            elif user_role == "Viên chức":
                default_shift_idx = 0 if now_vn.hour < 12 else 1
                vc_shift = st.selectbox("Ca làm việc Viên chức:", ["Ca Sáng (07:00 - 11:00)", "Ca Chiều (13:00 - 17:00)"], index=default_shift_idx)

    with col2:
        st.markdown("**Xác thực Tự động (GPS & Wi-Fi)**")
        location = get_geolocation()
        user_lat, user_lng = None, None
        if location and 'coords' in location:
            user_lat, user_lng = location['coords']['latitude'], location['coords']['longitude']
            st.caption(f"GPS: `{user_lat:.5f}, {user_lng:.5f}`")
        else:
            st.warning("Đang kết nối GPS... CHỌN 'CHO PHÉP' (Allow) vị trí!")

        user_ip = streamlit_js_eval(
            js_expressions="fetch('https://api.ipify.org?format=json').then(r => r.json()).then(data => data.ip)", 
            key='get_user_ip'
        )
        if user_ip: st.caption(f"IP: `{user_ip}`")
        
        action_type = st.radio("Thao tác ca làm việc:", ["Vào ca (Check-in)", "Ra ca (Check-out)"], horizontal=True)

        distances = {}
        auto_detected_key = None
        if user_lat is not None and user_lng is not None:
            for c_key, c_val in CAMPUSES.items():
                distances[c_key] = calculate_distance(user_lat, user_lng, c_val["lat"], c_val["lng"])
            if distances.get("CS1", 9999) <= MAX_ALLOWED_RADIUS:
                auto_detected_key = "CS1"
            else:
                closest_key = min(distances, key=distances.get)
                if distances[closest_key] <= MAX_ALLOWED_RADIUS: auto_detected_key = closest_key

        campus_options = ["Tự động nhận diện", "Cơ sở 1 (217 Hồng Bàng)", "Cơ sở 2 (201 Nguyễn Chí Thanh)", "Cơ sở 3 (41 Đinh Tiên Hoàng)"]
        selected_campus_option = st.selectbox("Cơ sở điểm danh:", campus_options)

        final_campus_key = None
        if selected_campus_option == "Tự động nhận diện": final_campus_key = auto_detected_key
        elif "Cơ sở 1" in selected_campus_option: final_campus_key = "CS1"
        elif "Cơ sở 2" in selected_campus_option: final_campus_key = "CS2"
        elif "Cơ sở 3" in selected_campus_option: final_campus_key = "CS3"

        detected_campus_info = CAMPUSES.get(final_campus_key) if final_campus_key else None
        curr_dist = distances.get(final_campus_key, 0.0) if final_campus_key else 0.0

        if detected_campus_info and curr_dist <= MAX_ALLOWED_RADIUS:
            campus_display_name = f"{detected_campus_info['name']} ({detected_campus_info['address']})"
            st.success(f"Đã chọn: **{detected_campus_info['name']}**")
            st.info(f"GPS: {curr_dist:.1f} m (Bán kính hợp lệ <= {int(MAX_ALLOWED_RADIUS)}m)")
        else:
            campus_display_name = "Không xác định"
            st.markdown(f'<div class="status-box-error">Cảnh báo: Khoảng cách GPS ({curr_dist:.1f}m) nằm ngoài bán kính {int(MAX_ALLOWED_RADIUS)}m!</div>', unsafe_allow_html=True)

        ip_valid = False
        if detected_campus_info and user_ip:
            ip_valid = any(user_ip.startswith(prefix) for prefix in ALLOWED_IP_PREFIXES)
            if ip_valid: st.markdown('<div class="status-box-success">IP Mạng Hợp lệ (Wi-Fi trường)</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="status-box-error">Cảnh báo: IP không thuộc Wi-Fi trường</div>', unsafe_allow_html=True)

    if st.button("XÁC NHẬN ĐIỂM DANH", use_container_width=True):
        if is_out_of_hours:
            st.error(f"Điểm danh thất bại: Hiện tại ({now_vn.strftime('%H:%M')}) nằm ngoài giờ làm việc / học tập quy định!")
        elif curr_dist > MAX_ALLOWED_RADIUS or not detected_campus_info:
            st.error(f"Điểm danh thất bại: Bạn đang ở cách trường {curr_dist:.1f}m (Vượt quá bán kính {int(MAX_ALLOWED_RADIUS)}m cho phép)!")
        elif not ip_valid:
            st.error("Điểm danh thất bại: Thiết bị chưa kết nối vào Wi-Fi nội bộ nhà trường!")
        elif len(input_id) != 8 or not fetched_name:
            st.error("Mã số 8 chữ số không tồn tại trong danh sách dữ liệu trên OneDrive!")
        else:
            file_map = {
                "Giảng viên": "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx",
                "Viên chức": "OGSM/ATTENDANCE/DATA/LichSu_VC.xlsx",
                "Sinh viên": "OGSM/ATTENDANCE/DATA/LichSu_SV.xlsx"
            }
            target_excel_path = file_map.get(user_role, "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx")
            
            existing_df = read_excel_from_onedrive(target_excel_path)
            last_action, last_time_str, last_note = None, "", ""
            
            if not existing_df.empty and "Mã Số" in existing_df.columns:
                existing_df["CLEAN_ID"] = existing_df["Mã Số"].astype(str).str.strip().str.zfill(8)
                user_records = existing_df[existing_df["CLEAN_ID"] == input_id]
                if not user_records.empty:
                    last_record = user_records.iloc[-1]
                    last_action = str(last_record.get("Thao Tác", "")).strip()
                    last_time_str = str(last_record.get("Thời Gian", ""))
                    last_note = str(last_record.get("Ghi Chú", ""))

            can_proceed = True
            
            # --- RÀNG BUỘC THỜI GIAN THEO CA ĐIỂM DANH ---
            if user_role in ["Giảng viên", "Sinh viên"]:
                s_h, s_m = lesson_schedule[start_lesson]["start"]
                e_h, e_m = lesson_schedule[end_lesson]["end"]
                sched_start = now_vn.replace(hour=s_h, minute=s_m, second=0, microsecond=0)
                sched_end = now_vn.replace(hour=e_h, minute=e_m, second=0, microsecond=0)
            else: # Viên chức
                if "Sáng" in vc_shift:
                    sched_start = now_vn.replace(hour=7, minute=0, second=0, microsecond=0)
                    sched_end = now_vn.replace(hour=11, minute=0, second=0, microsecond=0)
                else:
                    sched_start = now_vn.replace(hour=13, minute=0, second=0, microsecond=0)
                    sched_end = now_vn.replace(hour=17, minute=0, second=0, microsecond=0)

                # Kiểm tra trễ > 30 phút đối với Viên chức
                if action_type == "Vào ca (Check-in)":
                    late_limit = sched_start + timedelta(minutes=30)
                    if now_vn > late_limit:
                        st.error(f"Từ chối điểm danh: Đã quá 30 phút so với giờ bắt đầu ca ({sched_start.strftime('%H:%M')})! Giờ hiện tại: {now_vn.strftime('%H:%M')}. Vui lòng sang Tab 'Báo nghỉ phép' để nộp đơn.")
                        can_proceed = False

            if can_proceed:
                if action_type == "Ra ca (Check-out)":
                    if last_action != "Vào ca (Check-in)":
                        st.error("Bạn chưa thực hiện Vào ca (Check-in) cho ca làm việc này!")
                        can_proceed = False
                    elif user_role == "Viên chức" and ("Ca Sáng" in vc_shift and "Sáng" not in last_note and "07:0" not in last_note):
                        st.error("Cảnh báo: Lượt Vào ca trước đó của bạn thuộc Ca Chiều, không thể Ra ca cho Ca Sáng!")
                        can_proceed = False
                    elif now_vn < sched_end - timedelta(minutes=10):
                        time_left = int((sched_end - now_vn).total_seconds() / 60)
                        st.error(f"Chưa hết giờ ca làm việc! Ca kết thúc lúc {sched_end.strftime('%H:%M')}. Bạn còn {time_left} phút nữa mới được phép Ra ca.")
                        can_proceed = False

                elif action_type == "Vào ca (Check-in)":
                    if last_action == "Vào ca (Check-in)":
                        st.warning(f"Bạn đã Vào ca trước đó lúc `{last_time_str}`. Vui lòng thực hiện 'Ra ca (Check-out)' trước khi bắt đầu ca tiếp theo!")
                        can_proceed = False

            if can_proceed:
                status = "Đúng giờ"
                note = ""
                unit_sub_display = f"{fetched_sub} ({selected_class})" if user_role == "Sinh viên" else fetched_sub

                if user_role in ["Giảng viên", "Sinh viên"]:
                    if action_type == "Vào ca (Check-in)":
                        if now_vn > sched_start + timedelta(minutes=15):
                            status = "Vào trễ"
                            note = f"[{study_type}] Tiết {start_lesson} bắt đầu {sched_start.strftime('%H:%M')}. Điểm danh lúc {now_vn.strftime('%H:%M')}."
                        else:
                            note = f"[{study_type}] Lịch Tiết {start_lesson}-{end_lesson} ({sched_start.strftime('%H:%M')} - {sched_end.strftime('%H:%M')})"
                    else:
                        note = f"[{study_type}] Hoàn thành ca Tiết {start_lesson}-{end_lesson}"
                else: # Viên chức
                    if action_type == "Vào ca (Check-in)":
                        if now_vn > sched_start + timedelta(minutes=15):
                            status = "Đi trễ (Có bù giờ)"
                            note = f"[{vc_shift}] Đi trễ {int((now_vn - sched_start).total_seconds()/60)} phút. Giờ vào ca: {sched_start.strftime('%H:%M')}."
                        else:
                            note = f"[{vc_shift}] Đúng giờ ({sched_start.strftime('%H:%M')} - {sched_end.strftime('%H:%M')})"
                    else:
                        note = f"[{vc_shift}] Hoàn thành ca làm việc"

                row_data = [
                    input_id, str(fetched_name), user_role, str(fetched_unit), str(unit_sub_display),
                    campus_display_name, now_vn.strftime("%Y-%m-%d %H:%M:%S"), action_type,
                    round(curr_dist, 1), user_ip if user_ip else "N/A", status, note
                ]
                
                success = append_row_to_onedrive_excel(target_excel_path, row_data)
                if success:
                    st.success(f"Ghi nhận thành công cho {user_role} {fetched_name} tại {detected_campus_info['name']} lúc {now_vn.strftime('%H:%M:%S')}. Trạng thái: {status}")

# ----------------- TAB 2: BÁO NGHỈ PHÉP -----------------
with tabs[1]:
    mc_user_role = st.radio("Chọn đối tượng nộp đơn:", ["Giảng viên", "Viên chức", "Sinh viên"], horizontal=True, key="mc_role_radio")
    
    mc_class = ""
    if mc_user_role == "Sinh viên":
        mc_class = st.selectbox("Chọn Lớp sinh viên:", CLASS_LIST, key="mc_class_select")
        
    mc_id = st.text_input("Nhập Mã số (8 chữ số):", max_chars=8, placeholder="Ví dụ: 06071234 hoặc 26001001", key="mc_id_input").strip()
    
    mc_fetched_name = ""
    mc_fetched_unit = ""
    
    if len(mc_id) == 8:
        if mc_user_role in ["Giảng viên", "Viên chức"]:
            cbvc_df = read_excel_from_onedrive("OGSM/ATTENDANCE/DATA/CBVC.xlsx", sheet_name="Nhansu")
            if not cbvc_df.empty:
                col_msvc = cbvc_df.columns[0]
                col_name = cbvc_df.columns[1] if len(cbvc_df.columns) > 1 else cbvc_df.columns[0]
                col_unit = cbvc_df.columns[2] if len(cbvc_df.columns) > 2 else ""
                
                cbvc_df["CLEAN_ID"] = cbvc_df[col_msvc].astype(str).str.strip().str.replace('\xa0', '').str.replace('.0', '', regex=False).str.zfill(8)
                match = cbvc_df[cbvc_df["CLEAN_ID"] == mc_id]
                if not match.empty:
                    mc_fetched_name = match.iloc[0][col_name]
                    mc_fetched_unit = match.iloc[0][col_unit] if col_unit else ""
        else:
            sv_df = read_excel_from_onedrive(f"OGSM/ATTENDANCE/DATA/SV/{mc_class}.xlsx")
            if not sv_df.empty:
                col_mssv = sv_df.columns[0]
                col_name = sv_df.columns[1] if len(sv_df.columns) > 1 else sv_df.columns[0]
                col_unit = sv_df.columns[2] if len(sv_df.columns) > 2 else ""
                
                sv_df["CLEAN_ID"] = sv_df[col_mssv].astype(str).str.strip().str.replace('\xa0', '').str.replace('.0', '', regex=False).str.zfill(8)
                match = sv_df[sv_df["CLEAN_ID"] == mc_id]
                if not match.empty:
                    mc_fetched_name = match.iloc[0][col_name]
                    mc_fetched_unit = f"{match.iloc[0][col_unit]} - Lớp {mc_class}" if col_unit else f"Lớp {mc_class}"

    col_mc1, col_mc2 = st.columns(2)
    with col_mc1:
        st.text_input("Họ và tên người nộp:", value=str(mc_fetched_name if mc_fetched_name else ("Mã số chưa chính xác" if len(mc_id)==8 else "")), disabled=True, key="mc_name_disp")
    with col_mc2:
        st.text_input("Đơn vị / Lớp:", value=str(mc_fetched_unit if mc_fetched_unit else ""), disabled=True, key="mc_unit_disp")

    has_attended_today = False
    attendance_today_time = ""
    is_morning_attended = False
    is_afternoon_attended = False

    if len(mc_id) == 8 and mc_fetched_name:
        check_paths = [
            "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx",
            "OGSM/ATTENDANCE/DATA/LichSu_VC.xlsx",
            "OGSM/ATTENDANCE/DATA/LichSu_SV.xlsx"
        ]
        today_str = now_vn.strftime("%Y-%m-%d")
        
        for path in check_paths:
            hist_df = read_excel_from_onedrive(path)
            if not hist_df.empty and "Mã Số" in hist_df.columns and "Thời Gian" in hist_df.columns:
                hist_df["CLEAN_ID"] = hist_df["Mã Số"].astype(str).str.strip().str.zfill(8)
                hist_df["DATE_STR"] = hist_df["Thời Gian"].astype(str).str[:10]
                
                records_today = hist_df[(hist_df["CLEAN_ID"] == mc_id) & (hist_df["DATE_STR"] == today_str)]
                if not records_today.empty:
                    has_attended_today = True
                    last_rec = records_today.iloc[-1]
                    attendance_today_time = str(last_rec.get("Thời Gian", ""))
                    
                    for _, r in records_today.iterrows():
                        t_str = str(r.get("Thời Gian", ""))
                        if len(t_str) >= 16:
                            hour = int(t_str[11:13])
                            if hour < 12: is_morning_attended = True
                            else: is_afternoon_attended = True

    with st.form("form_minh_chung_detail"):
        mc_type = st.selectbox("Loại yêu cầu:", ["Nghỉ phép Buổi Sáng", "Nghỉ phép Buổi Chiều", "Nghỉ phép Cả Ngày", "Minh chứng Đi trễ > 30 phút"])
        mc_reason = st.text_area("Lý do chi tiết:")
        mc_file = st.file_uploader("Tải lên file đi kèm (Ảnh / PDF):", type=["png", "jpg", "jpeg", "pdf"])
        
        btn_submit = st.form_submit_button("GỬI YÊU CẦU MINH CHỨNG")
        
        if btn_submit:
            if len(mc_id) != 8 or not mc_fetched_name:
                st.error("Mã số 8 chữ số không tồn tại trong danh sách dữ liệu trên OneDrive! Vui lòng kiểm tra lại.")
            elif not mc_reason:
                st.error("Vui lòng nhập lý do chi tiết!")
            elif mc_type == "Nghỉ phép Cả Ngày" and has_attended_today:
                st.error(f"Từ chối gửi đơn: Bạn đã có lượt điểm danh có mặt trong ngày hôm nay lúc `{attendance_today_time}`! Không thể nộp đơn xin nghỉ cả ngày.")
            elif mc_type == "Nghỉ phép Buổi Sáng" and is_morning_attended:
                st.error("Từ chối gửi đơn: Bạn đã có lượt điểm danh trong Buổi Sáng hôm nay! Không thể nộp đơn xin nghỉ buổi sáng.")
            elif mc_type == "Nghỉ phép Buổi Chiều" and is_afternoon_attended:
                st.error("Từ chối gửi đơn: Bạn đã có lượt điểm danh trong Buổi Chiều hôm nay! Không thể nộp đơn xin nghỉ buổi chiều.")
            else:
                file_saved_name = "Không có file"
                if mc_file is not None:
                    file_ext = mc_file.name.split(".")[-1]
                    timestamp_str = now_vn.strftime("%Y%m%d_%H%M%S")
                    file_saved_name = f"{mc_id}_{timestamp_str}.{file_ext}"
                    
                    upload_file_to_onedrive(
                        "OGSM/ATTENDANCE/DATA/MINHCHUNG_FILES", 
                        file_saved_name, 
                        mc_file.getvalue()
                    )

                mc_cols = ["Mã Số", "Họ Và Tên", "Đối Tượng", "Đơn Vị", "Loại Yêu Cầu", "Lý Do", "File Minh Chứng", "Thời Gian Gửi", "Trạng Thái Duyệt"]
                mc_row = [
                    mc_id, str(mc_fetched_name), mc_user_role, str(mc_fetched_unit),
                    mc_type, mc_reason, file_saved_name, now_vn.strftime("%Y-%m-%d %H:%M:%S"), "Chờ duyệt"
                ]
                
                saved_mc = append_row_to_onedrive_excel("OGSM/ATTENDANCE/DATA/MinhChung_NghiPhep.xlsx", mc_row, custom_cols=mc_cols)
                
                if saved_mc:
                    st.success(f"Yêu cầu xin nghỉ / minh chứng của {mc_user_role} {mc_fetched_name} ({mc_id}) đã được ghi nhận thành công!")
                else:
                    st.error("Lỗi khi gửi dữ liệu lên OneDrive!")

# ----------------- TAB 3: DASHBOARD -----------------
with tabs[2]:
    view_mode = st.radio("Chọn loại báo cáo:", ["Nhật ký điểm danh", "Danh sách đơn minh chứng / nghỉ phép"], horizontal=True, key="db_view_mode")
    
    if view_mode == "Nhật ký điểm danh":
        selected_report_role = st.selectbox("Chọn nhóm dữ liệu xem báo cáo:", ["Giảng viên", "Viên chức", "Sinh viên"], key="report_role_select")
        
        file_map_report = {
            "Giảng viên": "OGSM/ATTENDANCE/DATA/LichSu_GV.xlsx",
            "Viên chức": "OGSM/ATTENDANCE/DATA/LichSu_VC.xlsx",
            "Sinh viên": "OGSM/ATTENDANCE/DATA/LichSu_SV.xlsx"
        }
        report_file_path = file_map_report[selected_report_role]
        
        history_df = read_excel_from_onedrive(report_file_path)
        
        if history_df.empty:
            st.info(f"Chưa có dữ liệu điểm danh trên OneDrive cho nhóm **{selected_report_role}**.")
        else:
            total_records = len(history_df)
            on_time_count = len(history_df[history_df["Trạng Thái"] == "Đúng giờ"])
            late_count = total_records - on_time_count
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Tổng lượt điểm danh ({selected_report_role})", total_records)
            c2.metric("Lượt Đúng giờ", on_time_count)
            c3.metric("Lượt Trễ / Về sớm", late_count)
            
            st.markdown("---")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**Biểu đồ Tỷ lệ Trạng thái Điểm danh**")
                status_counts = history_df["Trạng Thái"].value_counts().reset_index()
                status_counts.columns = ["Trạng Thái", "Số Lượng"]
                fig_pie = px.pie(
                    status_counts, 
                    values="Số Lượng", 
                    names="Trạng Thái", 
                    hole=0.4,
                    color_discrete_sequence=["#1877F2", "#E41E3F", "#FF9900"]
                )
                fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)

            with col_chart2:
                st.markdown("**Biểu đồ Số lượt Điểm danh theo Đơn vị / Lớp**")
                unit_col = "Đơn Vị" if "Đơn Vị" in history_df.columns else history_df.columns[3]
                unit_counts = history_df[unit_col].value_counts().reset_index()
                unit_counts.columns = [unit_col, "Số Lượt"]
                fig_bar = px.bar(
                    unit_counts, 
                    x=unit_col, 
                    y="Số Lượt", 
                    color=unit_col,
                    text_auto=True,
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_bar.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("**Bảng Nhật ký Chi tiết:**")
            st.dataframe(history_df, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                history_df.to_excel(writer, sheet_name='Sheet1', index=False)
                
            st.download_button(
                label=f"XUẤT BÁO CÁO EXCEL {selected_report_role.upper()} (.XLSX)",
                data=buffer.getvalue(),
                file_name=f"Bao_Cao_Diem_Danh_{selected_report_role}_{now_vn.strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        mc_df = read_excel_from_onedrive("OGSM/ATTENDANCE/DATA/MinhChung_NghiPhep.xlsx")
        if mc_df.empty:
            st.info("Chưa có đơn xin nghỉ phép / minh chứng nào được gửi lên hệ thống.")
        else:
            st.metric("Tổng số đơn đã gửi", len(mc_df))
            
            col_mc_chart1, col_mc_chart2 = st.columns(2)
            with col_mc_chart1:
                st.markdown("**Phân loại Đơn theo Đối tượng**")
                role_mc_counts = mc_df["Đối Tượng"].value_counts().reset_index()
                role_mc_counts.columns = ["Đối Tượng", "Số Lượng"]
                fig_mc_role = px.pie(role_mc_counts, values="Số Lượng", names="Đối Tượng", hole=0.3)
                st.plotly_chart(fig_mc_role, use_container_width=True)
                
            with col_mc_chart2:
                st.markdown("**Phân loại theo Loại Yêu cầu**")
                type_mc_counts = mc_df["Loại Yêu Cầu"].value_counts().reset_index()
                type_mc_counts.columns = ["Loại Yêu Cầu", "Số Lượng"]
                fig_mc_type = px.bar(type_mc_counts, x="Loại Yêu Cầu", y="Số Lượng", color="Loại Yêu Cầu", text_auto=True)
                st.plotly_chart(fig_mc_type, use_container_width=True)

            st.dataframe(mc_df, use_container_width=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                mc_df.to_excel(writer, sheet_name='MinhChung', index=False)
                
            st.download_button(
                label="XUẤT BÁO CÁO MINH CHỨNG (.XLSX)",
                data=buffer.getvalue(),
                file_name=f"Bao_Cao_Minh_Chung_{now_vn.strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
