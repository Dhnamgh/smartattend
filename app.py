import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
import io
import requests
import msal

# ================= 1. CAU HINH GIAO DIEN & STYLES =================
st.set_page_config(page_title="He Thong Diem Danh So - Azure OneDrive", layout="wide")

st.markdown("""
<style>
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
    .status-box-success {
        background-color: #E7F3FF;
        border-left: 5px solid #1877F2;
        padding: 12px;
        margin-bottom: 10px;
        color: #050505;
    }
    .status-box-error {
        background-color: #FFEBE9;
        border-left: 5px solid #E41E3F;
        padding: 12px;
        margin-bottom: 10px;
        color: #050505;
    }
</style>
""", unsafe_allow_html=True)

# Danh sach cac Lop sinh vien
CLASS_LIST = ["D26", "Y26", "RHM26", "YTCC26", "YHDP26", "DD26", "PHR26", "ĐD26", "XN26", "PHCN26"]

CAMPUSES = {
    "Co so 1": {"lat": 10.77688, "lng": 106.70081, "allowed_ips": ["118.69.1.1", "118.69.1.2"]},
    "Co so 2": {"lat": 10.78012, "lng": 106.69850, "allowed_ips": ["203.162.1.1"]},
    "Co so 3": {"lat": 10.78500, "lng": 106.70500, "allowed_ips": ["171.244.1.1"]}
}

# ================= 2. HAM KET NOI MICROSOFT GRAPH API =================
def get_azure_token():
    tenant_id = st.secrets["azure"]["TENANT_ID"]
    client_id = st.secrets["azure"]["CLIENT_ID"]
    client_secret = st.secrets["azure"]["CLIENT_SECRET"]
    
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, authority=authority, client_credential=client_secret
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" in result:
        return result["access_token"]
    else:
        st.error("Khong the xac thuc voi Microsoft Azure. Vui long kiem tra Secrets!")
        return None

@st.cache_data(ttl=300) # Cache du lieu trong 5 phut de tang toc do truy cap
def read_excel_from_onedrive(file_path):
    token = get_azure_token()
    if not token:
        return pd.DataFrame()
    
    user_email = st.secrets["azure"]["USER_EMAIL"]
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_path}:/content"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return pd.read_excel(io.BytesIO(response.content), dtype=str, engine="openpyxl")
    else:
        return pd.DataFrame()

def append_row_to_onedrive_excel(file_path, table_name, row_values):
    token = get_azure_token()
    if not token:
        return False
    
    user_email = st.secrets["azure"]["USER_EMAIL"]
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/drive/root:/{file_path}:/workbook/tables/{table_name}/rows/add"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"values": [row_values]}
    
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ================= 3. GIAO DIEN HE THONG =================
st.title("HE THONG DIEM DANH SO - TROI XAT TACH FILE ONEDRIVE")

tabs = st.tabs(["THUC HIEN DIEM DANH", "NOP MINH CHUNG / BAO NGHIPHEP", "DASHBOARD BAO CAO"])

# ----------------- TAB 1: DIEM DANH -----------------
with tabs[0]:
    st.subheader("Man hinh Diem danh")
    col1, col2 = st.columns(2)
    
    with col1:
        user_group = st.radio("Nhom doi tuong", ["Can bo / Vien chuc / Giang vien", "Sinh vien"], horizontal=True)
        
        selected_class = ""
        if user_group == "Sinh vien":
            selected_class = st.selectbox("Chon Lop sinh vien:", CLASS_LIST)
            
        input_id = st.text_input("Nhap Ma so (8 chu so):", max_chars=8, placeholder="Vi du: 06071234 hoac 26001001")
        
        fetched_name = ""
        fetched_unit = ""
        fetched_sub = ""
        fetched_course = ""
        
        if len(input_id) == 8:
            if user_group == "Can bo / Vien chuc / Giang vien":
                cbvc_df = read_excel_from_onedrive("ATTENDANCE/DATA/CBVC.xlsx")
                if not cbvc_df.empty:
                    match = cbvc_df[cbvc_df["MSVC"] == input_id]
                    if not match.empty:
                        fetched_name = match.iloc[0]["Họ và tên"]
                        fetched_unit = match.iloc[0]["Đơn vị"]
                        fetched_sub = match.iloc[0]["Bộ môn"]
            else:
                # Doc file Excel rieng cua Lop tu thu muc ATTENDANCE/DATA/SV/
                sv_class_path = f"ATTENDANCE/DATA/SV/{selected_class}.xlsx"
                sv_df = read_excel_from_onedrive(sv_class_path)
                
                if sv_df.empty:
                    st.warning(f"Chua tim thay file danh sach lop {selected_class}.xlsx tren OneDrive.")
                else:
                    match = sv_df[sv_df["MSSV"] == input_id]
                    if not match.empty:
                        fetched_name = match.iloc[0]["Họ và tên"]
                        fetched_unit = match.iloc[0]["Đơn vị (Trường/Khoa)"]
                        fetched_sub = match.iloc[0]["Bộ môn giảng"]
                        fetched_course = match.iloc[0]["Tên học phần"]

        st.text_input("Ho va ten:", value=fetched_name, disabled=True)
        st.text_input("Don vi (Truong/Khoa):", value=fetched_unit, disabled=True)
        st.text_input("Bo mon:", value=fetched_sub, disabled=True)
        if user_group == "Sinh vien":
            st.text_input("Ten hoc phan:", value=fetched_course, disabled=True)
            
        campus_selected = st.selectbox("Chon Co so diem danh:", list(CAMPUSES.keys()))

    with col2:
        st.markdown("**Xac thuc Vi tri & Mang noi bo**")
        user_lat = st.number_input("Vi do GPS (Latitude):", value=10.77685, format="%.5f")
        user_lng = st.number_input("Kinh do GPS (Longitude):", value=106.70080, format="%.5f")
        user_ip = st.text_input("IP Wifi ket noi:", value="118.69.1.1")
        
        action_type = st.radio("Thao tac ca lam viec:", ["Vao ca (Check-in)", "Ra ca (Check-out)"], horizontal=True)
        
        target = CAMPUSES[campus_selected]
        dist = calculate_distance(user_lat, user_lng, target["lat"], target["lng"])
        ip_valid = user_ip in target["allowed_ips"]
        
        st.write(f"Khoang cach den tam co so: **{dist:.1f} m**")
        
        if dist <= 50:
            st.markdown('<div class="status-box-success">Vi tri hop le (Trong pham vi 50m)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box-error">Vi tri KHONG hop le (Vuot qua 50m)</div>', unsafe_allow_html=True)

        if ip_valid:
            st.markdown('<div class="status-box-success">IP Mang Hop le (Ket noi dung Wifi truong)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box-error">IP Mang KHONG hop le (Khong phai Wifi truong)</div>', unsafe_allow_html=True)

    if st.button("XAC NHAN DIEM DANH", type="primary", use_container_width=True):
        if len(input_id) != 8 or not fetched_name:
            st.error("Ma so 8 chu so khong ton tai trong danh sach lop tren OneDrive!")
        elif dist > 50:
            st.error("Diem danh bi tu choi do vi tri nam ngoai pham vi 50m!")
        else:
            now = datetime.now()
            status = "Dung gio"
            unit_sub_display = f"{fetched_sub} ({selected_class})" if user_group == "Sinh vien" else fetched_sub
            note = f"Hoc phan: {fetched_course}" if user_group == "Sinh vien" else ""
            
            if user_group == "Can bo / Vien chuc / Giang vien" and action_type == "Vao ca (Check-in)":
                standard_start = now.replace(hour=7, minute=0, second=0)
                if now > standard_start:
                    late_min = (now - standard_start).total_seconds() / 60
                    if late_min <= 30:
                        status = "Di tre (Co bu gio)"
                        out_time = now.replace(hour=11, minute=0) + timedelta(minutes=late_min)
                        note = f"Di tre {int(late_min)} phut. Gio ra ca sang bat buoc: {out_time.strftime('%H:%M')}"
                    else:
                        status = "Tre > 30 phut"
                        note = "Vuot qua 30 phut. Yeu cau nop don xin nghi phep / minh chung."

            row_data = [
                input_id, fetched_name, user_group, fetched_unit, unit_sub_display,
                campus_selected, now.strftime("%Y-%m-%d %H:%M:%S"), action_type,
                round(dist, 1), user_ip, status, note
            ]
            
            success = append_row_to_onedrive_excel("ATTENDANCE/DATA/LichSu_DiemDanh.xlsx", "BangDiemDanh", row_data)
            
            if success:
                st.success(f"Ghi nhan va dong bo thanh cong len OneDrive luc {now.strftime('%H:%M:%S')}. Trang thai: {status}")
            else:
                st.error("Loi khi ghi du lieu vao file Excel tren OneDrive!")

# ----------------- TAB 2: MINH CHUNG -----------------
with tabs[1]:
    st.subheader("Nop minh chung di tre / Bao xin nghi phep")
    with st.form("form_minh_chung"):
        mc_id = st.text_input("Nhap Ma so 8 chu so:")
        mc_type = st.selectbox("Loai yeu cau:", ["Nghi phep Buoi Sang", "Nghi phep Buoi Chieu", "Nghi phep Ca Ngay", "Minh chung Di tre > 30 phut"])
        mc_reason = st.text_area("Ly do chi tiet:")
        mc_file = st.file_uploader("Tai len file dinh kem (Anh / PDF):", type=["png", "jpg", "pdf"])
        
        btn_submit = st.form_submit_button("GUI YEU CAU")
        if btn_submit:
            st.info("Yeu cau da duoc ghi nhan va chuyen den Ban Giam hieu / Lanh dao Khoa duyet.")

# ----------------- TAB 3: DASHBOARD -----------------
with tabs[2]:
    st.subheader("Bao cao va Thong ke Diem danh")
    
    if st.button("CAP NHAT DU LIEU TU ONEDRIVE"):
        st.session_state.history_df = read_excel_from_onedrive("ATTENDANCE/DATA/LichSu_DiemDanh.xlsx")

    history_df = st.session_state.get("history_df", read_excel_from_onedrive("ATTENDANCE/DATA/LichSu_DiemDanh.xlsx"))
    
    if history_df.empty:
        st.info("Chua co du lieu diem danh tren OneDrive.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tong luot diem danh", len(history_df))
        c2.metric("Luot Dung gio", len(history_df[history_df["TrangThai"] == "Dung gio"]))
        c3.metric("Luot Tre / Vi pham", len(history_df[history_df["TrangThai"] != "Dung gio"]))
        
        st.dataframe(history_df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            history_df.to_excel(writer, sheet_name='DiemDanh', index=False)
            
        st.download_button(
            label="XUAT BAO CAO EXCEL (.XLSX)",
            data=buffer.getvalue(),
            file_name=f"Bao_Cao_Diem_Danh_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
