import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar
import plotly.express as px
import re
import hashlib
import json
import requests
import msal
from io import BytesIO

st.set_page_config(layout="wide")

# ==============================================================================
# !!! KHỞI TẠO STATE & ĐỌC MẬT KHẨU TỪ SECRETS !!!
# ==============================================================================
if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

if "auth_dang_ky" not in st.session_state:
    st.session_state.auth_dang_ky = False

if "auth_phe_duyet" not in st.session_state:
    st.session_state.auth_phe_duyet = False

# Đọc chính xác cấu trúc secrets [user] và [admin]
PASSWORD_DANG_KY = st.secrets["user"]["password"]
PASSWORD_PHE_DUYET = st.secrets["admin"]["password"]

# ==============================================================================
# 1. GIAO DIỆN & CSS
# ==============================================================================
st.markdown("""
<style>
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 8px !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    width: 170px !important; min-width: 170px !important; max-width: 170px !important;
    min-height: 42px !important; background: #0f5c99 !important; border-radius: 8px !important;
    padding: 10px 14px !important; margin: 5px 0 !important; border: 1px solid #0b4a7a !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.18) !important; display: flex !important; align-items: center !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #0b4a7a !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: #073b63 !important; border-left: 5px solid #facc15 !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] input[type="radio"] { display: none !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
    color: #ffffff !important; font-size: 15px !important; font-weight: 700 !important; margin: 0 !important; opacity: 1 !important;
}

html, body { font-family: Arial, sans-serif; font-size:20px; color:#111827; }
section[data-testid="stSidebar"] { width:255px !important; min-width:255px !important; max-width:255px !important; }
section[data-testid="stSidebar"] * { font-size: 13px !important; }
.block-container { padding-top: 1rem; }

div[data-baseweb="notification"] div, .stAlert p { font-size: 13px !important; line-height: 1.4 !important; }
h1, h2, h3, h4, h5, h6, .stSubheader, .fc-toolbar-title, plotly .gtitle,
div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3, div[data-testid="stMarkdownContainer"] h4 {
    font-size: 14px !important; font-weight: 700 !important;
}
div[role="radiogroup"] label, div[data-baseweb="radio"] label, .stRadio label, .stRadio div {
    font-size: 14px !important; font-weight: 600 !important;
}

.table-title { font-size: 22px; font-weight: 900; color: #020617; margin-top: 18px; margin-bottom: 10px; letter-spacing: -0.2px; }
.ump-table-wrap { width: 100%; overflow-x: auto; margin-bottom: 10px; }

.ump-table { border-collapse: collapse; font-size: 15px; color: #020617 !important; background: white; width: 100%; }
.ump-table th { background: #f1f5f9; color: #020617 !important; font-weight: 900; border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; white-space: nowrap; }
.ump-table td { color: #020617 !important; font-weight: 650; border: 1px solid #cbd5e1; padding: 7px 10px; vertical-align: top; line-height: 1.35; }
.ump-table tr:nth-child(even) td { background: #f8fafc; }

.ump-fixed-header {
    background: linear-gradient(90deg, #06145f, #0b2f8a); color: #ffffff; padding: 18px 24px; border-radius: 10px; margin: 0 0 22px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18); display: flex; flex-direction: column; justify-content: center;
}
.ump-fixed-header .ump-vn { font-size: 22px; font-weight: 800; text-transform: uppercase; }
.ump-fixed-header .ump-en { font-size: 13px; font-weight: 600; text-transform: uppercase; margin-top: 4px; opacity: .95; }
.ump-fixed-header .ump-app { font-size: 24px; font-weight: 800; margin-top: 14px; }

.event-details-panel {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-top: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
.details-item { font-size: 15px; color: #1e293b; margin-bottom: 6px; line-height: 1.4; }
.details-label { font-weight: 700; color: #020617; }
.details-support-title { font-size: 16px; font-weight: 700; color: #020617; margin-top: 14px; margin-bottom: 8px; }

@media screen and (max-width: 768px) {
    .ump-fixed-header { padding: 12px 16px; margin-bottom: 15px; }
    .ump-fixed-header .ump-vn { font-size: 14px; }
    .ump-fixed-header .ump-en { font-size: 10px; margin-top: 2px; }
    .ump-fixed-header .ump-app { font-size: 17px; margin-top: 8px; }
    .block-container { padding: 0.5rem; }
    .table-title { font-size: 17px; margin-top: 10px; }
    .fc .fc-toolbar-title { font-size: 15px !important; }
    .event-details-panel { padding: 12px; margin-top: 10px; }
    .details-title { font-size: 16px; }
    .details-item { font-size: 14px; }
    .ump-table { font-size: 13px; }
    .ump-table th, .ump-table td { padding: 6px 8px; }
}
</style>

<div class="ump-fixed-header">
  <div class="ump-vn">ĐẠI HỌC Y DƯỢC TP. HỒ CHÍ MINH</div>
  <div class="ump-en">UNIVERSITY OF MEDICINE AND PHARMACY AT HCMC</div>
  <div class="ump-app">Hệ thống quản trị sự kiện UMP</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HÀM TRỢ GIÚP (HELPERS)
# ==============================================================================
def parse_time(text):
    if pd.isna(text): return None
    text = str(text).strip().lower()
    if not text or text in ["nan", "none"]: return None
    m = re.search(r"(\d{1,2})\s*[gh:]\s*(\d{0,2})", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59: return hour, minute
    m = re.fullmatch(r"\d{1,2}", text)
    if m:
        hour = int(text)
        if 0 <= hour <= 23: return hour, 0
    return None

def clean_text(value):
    if pd.isna(value): return ""
    return str(value).strip()

def is_yes(value):
    return clean_text(value).upper() in ["CÓ", "CO", "YES", "Y", "TRUE", "1"]

def count_value(value):
    txt = clean_text(value)
    if not txt: return 0
    up = txt.upper()
    if up in ["KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]: return 0
    m = re.search(r"\d+", txt.replace(",", "."))
    if m:
        try: return int(m.group(0))
        except Exception: return 0
    return 1 if up in ["CÓ", "CO", "YES", "Y", "TRUE"] else 1

def event_color(index, key):
    palette = ["#DBEAFE", "#DCFCE7", "#FEE2E2", "#FFEDD5", "#F3E8FF", "#CCFBF1", "#FCE7F3", "#E0E7FF", "#CFFAFE", "#FEF3C7"]
    digest = int(hashlib.md5(str(key).encode("utf-8")).hexdigest(), 16)
    return palette[(digest + index) % len(palette)]

def get_period_df(df_input, period):
    now = datetime.today()
    if period == "Tuần":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        label = f"Tuần {start.strftime('%d/%m/%Y')} - {(end - timedelta(days=1)).strftime('%d/%m/%Y')}"
    elif period == "Tháng":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
        label = f"Tháng {now.month}/{now.year}"
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
        label = f"Năm {now.year}"
    return df_input[(df_input["start"] >= start) & (df_input["start"] < end)].copy(), label, start, end

def dataframe_to_excel_bytes(dataframe):
    html = f"""<html><head><meta charset="utf-8"><style>table {{ border-collapse: collapse; font-family: Arial; }} th {{ background: #e5e7eb; font-weight: bold; }} th, td {{ border: 1px solid #999; padding: 6px; }}</style></head><body>{dataframe.to_html(index=False, escape=False)}</body></html>"""
    return html.encode("utf-8-sig")

def show_table_with_download(title, dataframe, file_name, compact=False):
    st.markdown(f'<div class="table-title">{title}</div>', unsafe_allow_html=True)
    if dataframe is None or len(dataframe) == 0:
        st.info("Không có dữ liệu")
        return
    css_class = "ump-table compact" if compact else "ump-table"
    wrap_class = "ump-table-wrap compact" if compact else "ump-table-wrap"
    st.markdown(f'<div class="{wrap_class}">{dataframe.to_html(index=False, escape=False, classes=css_class)}</div>', unsafe_allow_html=True)
    st.download_button("⬇️ Tải về Excel", data=dataframe_to_excel_bytes(dataframe), file_name=str(file_name).rsplit(".", 1)[0] + ".xls", mime="application/vnd.ms-excel")

def collapse_repeated_support_rows(dataframe):
    if dataframe is None or len(dataframe) == 0: return dataframe
    df_out = dataframe.copy()
    group_cols = [c for c in ["Sự kiện", "Đơn vị", "Ngày giờ", "Địa điểm"] if c in df_out.columns]
    if not group_cols: return df_out
    last_key = None
    for idx in df_out.index:
        key = tuple(df_out.at[idx, c] for c in group_cols)
        if key == last_key:
            for c in group_cols: df_out.at[idx, c] = ""
        else: last_key = key
    return df_out

# ==============================================================================
# 3. KẾT NỐI ONEDRIVE GRAPH API
# ==============================================================================
@st.cache_data(ttl=15)
def load_data():
    try:
        azure_cfg = st.secrets["azure_ogsm"]
        onedrive_cfg = st.secrets["onedrive_ogsm"]
        
        app = msal.ConfidentialClientApplication(
            client_id=azure_cfg["client_id"],
            client_credential=azure_cfg["client_secret"],
            authority=f"https://login.microsoftonline.com/{azure_cfg['tenant_id']}"
        )
        
        res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in res:
            st.error("❌ Lỗi xác thực Azure Graph API")
            return pd.DataFrame()
        
        token = res["access_token"]
        drive_id = onedrive_cfg["drive_id"]
        file_path = "/OGSM/EVENT/Danh_sach_su_kien.xlsx"
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{file_path}:/content"
        headers = {"Authorization": f"Bearer {token}"}
        
        excel_res = requests.get(url, headers=headers)
        if excel_res.status_code == 200:
            df_raw = pd.read_excel(BytesIO(excel_res.content))
            return process_raw_dataframe(df_raw)
        else:
            st.error(f"❌ Lỗi đọc file OneDrive ({excel_res.status_code})")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Lỗi kết nối OneDrive: {e}")
        return pd.DataFrame()

def save_onedrive_excel(df: pd.DataFrame) -> bool:
    try:
        azure_cfg = st.secrets["azure_ogsm"]
        onedrive_cfg = st.secrets["onedrive_ogsm"]
        
        app = msal.ConfidentialClientApplication(
            client_id=azure_cfg["client_id"],
            client_credential=azure_cfg["client_secret"],
            authority=f"https://login.microsoftonline.com/{azure_cfg['tenant_id']}"
        )
        
        token_res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in token_res: return False
        
        token = token_res["access_token"]
        drive_id = onedrive_cfg["drive_id"]
        file_path = "/OGSM/EVENT/Danh_sach_su_kien.xlsx"
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{file_path}:/content"
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        res = requests.put(url, headers=headers, data=output.getvalue())
        if res.status_code in [200, 201]:
            st.cache_data.clear()
            return True
        else:
            st.error(f"❌ Lỗi ghi file OneDrive ({res.status_code}): {res.text}")
            return False
    except Exception as e:
        st.error(f"❌ Lỗi xử lý ghi file: {e}")
        return False

def process_raw_dataframe(df_raw):
    if df_raw.empty: return df_raw
    df = df_raw.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.rename(columns={
        "Tên sự kiện": "event", "Đơn vị phụ trách/ tổ chức": "donvi",
        "Ngày tổ chức": "start", "Ngày kết thúc": "end", "Địa điểm tổ chức": "location",
        "Hỗ trợ": "support", "Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp": "support",
        "Giờ bắt đầu": "start_time", "Giờ kết thúc": "end_time",
        "Số lượng bàn đón tiếp": "support_ban_don_tiep", "Cần trải khăn bàn hội trường": "support_khan_ban",
        "Số lượng lễ tân": "support_le_tan", "Số lượng bảng tên (bảng mica)": "support_bang_ten",
        "Số lượng bìa ký kết": "support_bia_ky_ket", "Số lượng nước uống": "support_nuoc_uong",
        "Số phần Teabreak": "support_teabreak", "Số lượng hoa để bàn": "support_hoa_ban",
        "Số lượng hoa để bục phát biểu": "support_hoa_buc", "Số lượng hoa bó để tặng": "support_hoa_tang",
        "Số lượng quà tặng": "support_qua_tang", "Số lượng Brochure": "support_brochure",
        "Số lượng khay bưng": "support_khay_bung", "Số lượng bandroll, standee cần in và thi công": "support_bandroll_standee",
        "Số lượng Backdrop cần in và thi công": "support_backdrop", "Cần chạy bảng điện tử": "support_bang_dien_tu",
        "Cần gửi thư mời": "support_thu_moi", "Các yêu cầu khác (nếu có)": "support_khac",
        "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)": "approval_opinion"
    })

    df["start"] = pd.to_datetime(df["start"], errors="coerce").dt.date
    df["end"] = pd.to_datetime(df["end"], errors="coerce").dt.date.fillna(df["start"])
    df = df.dropna(subset=["start"])

    df["full_start"] = pd.NaT
    df["full_end"] = pd.NaT

    for i in df.index:
        s, e = df.at[i, "start"], df.at[i, "end"]
        t = parse_time(df.at[i, "start_time"] if "start_time" in df.columns else None)
        t2 = parse_time(df.at[i, "end_time"] if "end_time" in df.columns else None)
        if t: df.at[i, "full_start"] = datetime.combine(s, time(t[0], t[1]))
        else: df.at[i, "full_start"] = datetime.combine(s, time(0, 0))
        if t2: df.at[i, "full_end"] = datetime.combine(e, time(t2[0], t2[1]))
        else: df.at[i, "full_end"] = datetime.combine(e, time(23, 59))

    for col in ["event", "donvi", "location", "support", "approval_opinion"]:
        if col not in df.columns: df[col] = ""
        df[col] = df[col].apply(clean_text)
    return df

def approval_text_from_row(row):
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]:
                return val
    return ""

def keep_only_thong_nhat_for_calendar(df_input):
    if df_input is None or len(df_input) == 0: return df_input
    df_tmp = df_input.copy()
    approvals = df_tmp.apply(approval_text_from_row, axis=1)
    return df_tmp[approvals.eq("Thống nhất") | approvals.str.startswith("Thống nhất:")].copy()

def build_approval_summary_table(df_input):
    columns = ["Sự kiện", "Đơn vị", "Ngày giờ", "Địa điểm", "Hỗ trợ", "Ý kiến phê duyệt"]
    if df_input is None or len(df_input) == 0: return pd.DataFrame(columns=columns)
    rows = []
    df_out = df_input.copy()
    df_out["_sort_time"] = pd.to_datetime(df_out["full_start"], errors="coerce")
    df_out = df_out.sort_values(["_sort_time", "donvi", "event"], ascending=[True, True, True]).reset_index(drop=True)

    for _, r in df_out.iterrows():
        s = r.get("full_start")
        ngay_gio = s.strftime("%d/%m/%Y" if s.hour == 0 and s.minute == 0 else "%d/%m/%Y %H:%M") if pd.notna(s) else ""
        rows.append({
            "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
            "Ngày giờ": ngay_gio, "Địa điểm": clean_text(r.get("location", "")),
            "Hỗ trợ": clean_text(r.get("support", "")) or "Không",
            "Ý kiến phê duyệt": approval_text_from_row(r) or "Chưa phê duyệt"
        })
    return pd.DataFrame(rows, columns=columns)

def build_support_table(df_input):
    support_cols = {
        "support_ban_don_tiep": "Bàn đón tiếp", "support_khan_ban": "Trải khăn bàn hội trường",
        "support_le_tan": "Lễ tân (người)", "support_bang_ten": "Bảng tên mica",
        "support_bia_ky_ket": "Bìa ký kết", "support_nuoc_uong": "Nước uống (chai)",
        "support_teabreak": "Teabreak (phần)", "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu", "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng", "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng", "support_bandroll_standee": "Bandroll/standee in & thi công",
        "support_backdrop": "Backdrop in & thi công", "support_thu_moi": "Gửi thư mời",
        "support_khac": "Các yêu cầu khác"
    }
    rows = []
    for _, r in df_input.iterrows():
        datetime_full = r.get("full_start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("full_start")) else ""
        has_support_flag, has_detail = is_yes(r.get("support", "")), False
        for col, label in support_cols.items():
            if col in df_input.columns:
                qty = count_value(r.get(col, ""))
                if qty > 0:
                    has_detail = True
                    rows.append({
                        "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
                        "Ngày giờ": datetime_full, "Địa điểm": clean_text(r.get("location", "")),
                        "Nội dung hỗ trợ": label, "Số lượng": qty
                    })
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
                "Ngày giờ": datetime_full, "Địa điểm": clean_text(r.get("location", "")),
                "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ", "Số lượng": 1
            })
    return pd.DataFrame(rows)

def build_detailed_support_table_html(raw_event_data_dictionary):
    raw_data = raw_event_data_dictionary

    support_fields = {
        "support_ban_don_tiep": "Số lượng bàn đón tiếp",
        "support_khan_ban": "Cần trải khăn bàn hội trường",
        "support_le_tan": "Số lượng lễ tân (người)",
        "support_bang_ten": "Số lượng bảng tên mica",
        "support_bia_ky_ket": "Số lượng bìa ký kết",
        "support_nuoc_uong": "Số lượng nước uống (chai)",
        "support_teabreak": "Số phần Teabreak",
        "support_hoa_ban": "Số lượng hoa để bàn",
        "support_hoa_buc": "Số lượng hoa để bục phát biểu",
        "support_hoa_tang": "Số lượng hoa bó để tặng",
        "support_qua_tang": "Số lượng quà tặng",
        "support_brochure": "Số lượng Brochure",
        "support_khay_bung": "Số lượng khay bưng",
        "support_bandroll_standee": "Bandroll/standee in & thi công",
        "support_backdrop": "Backdrop in & thi công",
        "support_thu_moi": "Cần gửi thư mời",
        "support_khac": "Các yêu cầu khác"
    }

    detailed_rows = []
    
    for field_key, display_name in support_fields.items():
        if field_key in raw_data:
            val = raw_data[field_key]
            
            if field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                txt = clean_text(val)
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>Có</td></tr>")
            
            else:
                qty = count_value(val)
                if qty > 0:
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td></tr>")

    if not detailed_rows:
        return ""

    return f"""
    <div class="details-support-table-wrap">
        <div class="details-support-title"><strong>Nội dung hỗ trợ chi tiết</strong></div>
        <table class="ump-table compact">
            <thead>
                <tr>
                    <th>Nội dung hỗ trợ</th>
                    <th>Số lượng/Yêu cầu</th>
                </tr>
            </thead>
            <tbody>
                {''.join(detailed_rows)}
            </tbody>
        </table>
    </div>
    """

# ==============================================================================
# 4. KHỞI TẠO STATE & KHAI BÁO MENU
# ==============================================================================
df = load_data()
today = datetime.today()

menu = st.sidebar.radio("MENU", [
    "Dashboard", 
    "Đăng ký sự kiện", 
    "Phê duyệt sự kiện", 
    "Báo cáo", 
    "Cảnh báo trùng lịch", 
    "Thống kê hỗ trợ", 
    "Truy vấn AI"
])

donvi_list = sorted(df["donvi"].dropna().unique()) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["donvi"].isin(selected)]

# ==============================================================================
# 5. CÁC TRANG CHỨC NĂNG
# ==============================================================================

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.markdown(f'<div class="table-title">Dashboard Lịch sự kiện - tháng {today.month} năm {today.year}</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()

    df_dash = keep_only_thong_nhat_for_calendar(df_f)
    events, event_dates_for_stats = [], []
    for idx, (_, r) in enumerate(df_dash.sort_values("full_start").iterrows()):
        s, e = r["full_start"], r["full_end"]
        start_str = s.strftime("%Y-%m-%d %H:%M") if s.hour != 0 else s.strftime("%Y-%m-%d")
        end_str = e.strftime("%Y-%m-%d %H:%M") if e.hour != 23 else e.strftime("%Y-%m-%d")
        
        time_label = s.strftime("%H:%M") if s.hour != 0 else "Cả ngày"
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        event_raw_data_json_string = r.to_json() 
        
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            "extendedProps": {
                "panel_event_title": clean_text(r.get("event", "")),
                "panel_donvi": clean_text(r.get("donvi", "")),
                "panel_location": location,
                "panel_time_label": start_str,
                "panel_support_text": clean_text(r.get("support", "")),
                "raw_row_data_json_string": event_raw_data_json_string 
            }
        })

    calendar_output = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth", 
            "locale": "vi", 
            "firstDay": 1, 
            "height": "auto", 
            "eventDisplay": "block",
            "displayEventTime": False
        },
        key="ump_calendar"
    )

    if calendar_output and "callback" in calendar_output and calendar_output["callback"] == "eventClick":
        st.session_state.selected_event_details = calendar_output["eventClick"]["event"]["extendedProps"]

    selected_event_props = st.session_state.get("selected_event_details", None)
    
    if selected_event_props:
        props = selected_event_props
        raw_row_data = {}
        try:
            raw_row_data = json.loads(props['raw_row_data_json_string'])
        except Exception:
            pass

        content_bang_dien_tu = clean_text(raw_row_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
        val_bang_dt = clean_text(raw_row_data.get("support_bang_dien_tu", ""))
        if not content_bang_dien_tu and val_bang_dt and val_bang_dt.upper() not in ["CÓ", "CO", "YES", "Y", "TRUE", "1", "KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]:
            content_bang_dien_tu = val_bang_dt

        details_html = f"""
        <div class="event-details-panel">
            <div class="details-title">📋 Chi tiết sự kiện đã chọn trên lịch</div>
            <div class="details-item"><span class="details-label">📌 Sự kiện:</span> {props['panel_event_title']}</div>
            <div class="details-item"><span class="details-label">🏢 Đơn vị:</span> {props['panel_donvi']}</div>
            <div class="details-item"><span class="details-label">📍 Địa điểm:</span> {props['panel_location']}</div>
            <div class="details-item"><span class="details-label">🕒 Thời gian:</span> {props['panel_time_label']}</div>
            <div class="details-item"><strong>Hỗ trợ:</strong> {props['panel_support_text'] or "Không yêu cầu"}</div>
        """
        
        if content_bang_dien_tu:
            details_html += f'<div class="details-item"><strong>Nội dung chạy bảng điện tử:</strong> <strong>{content_bang_dien_tu}</strong></div>'

        if is_yes(props['panel_support_text']):
            details_html += build_detailed_support_table_html(raw_row_data)
            
        details_html += "</div>"
        st.markdown(details_html, unsafe_allow_html=True)
        
        if st.button("✖️ Đóng xem chi tiết"):
            st.session_state.selected_event_details = None
            st.rerun()

    st.subheader("📈 Tổng quan tháng này")
    week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tuần này", sum(1 for d in event_dates_for_stats if week_start <= d < week_end))
    c2.metric("Tháng này", sum(1 for d in event_dates_for_stats if d.month == today.month and d.year == today.year))
    c3.metric("Năm nay", sum(1 for d in event_dates_for_stats if d.year == today.year))

# --- 2. ĐĂNG KÝ SỰ KIỆN ---
elif menu == "Đăng ký sự kiện":
    st.markdown('<div class="table-title">📝 Đăng ký Sự kiện Mới</div>', unsafe_allow_html=True)
    
    if not st.session_state.auth_dang_ky:
        pwd_dk = st.text_input("🔒 Nhập mật khẩu để mở form đăng ký:", type="password", key="pwd_dk_input")
        if st.button("Xác nhận mở khóa", key="btn_auth_dk"):
            if pwd_dk == PASSWORD_DANG_KY:
                st.session_state.auth_dang_ky = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác. Vui lòng thử lại!")
    else:
        col_auth1, col_auth2 = st.columns([6, 1])
        with col_auth2:
            if st.button("🔒 Khóa lại", key="btn_lock_dk"):
                st.session_state.auth_dang_ky = False
                st.rerun()
                
        with st.form("form_dang_ky_su_kien"):
            c1, c2 = st.columns(2)
            ten_sk = c1.text_input("Tên sự kiện (*)", placeholder="Nhập tên sự kiện")
            don_vi = c2.text_input("Đơn vị phụ trách/tổ chức (*)", placeholder="Ví dụ: Phòng HCTH, Khoa Dược...")
            
            c3, c4 = st.columns(2)
            ngay_bd = c3.date_input("Ngày tổ chức (*)", value=datetime.today())
            ngay_kt = c4.date_input("Ngày kết thúc", value=datetime.today())
            
            c5, c6 = st.columns(2)
            gio_bd = c5.text_input("Giờ bắt đầu", placeholder="Ví dụ: 08:00 hoặc 8h")
            gio_kt = c6.text_input("Giờ kết thúc", placeholder="Ví dụ: 11:30 hoặc 11h30")
            
            dia_diem = st.text_input("Địa điểm tổ chức", placeholder="Ví dụ: Hội trường A, Phòng họp 1...")
            
            st.markdown("---")
            st.markdown("**Đề xuất hỗ trợ từ phòng Hành chính Tổng hợp:**")
            co_ho_tro = st.checkbox("Có yêu cầu hỗ trợ", value=False)
            
            col_s1, col_s2, col_s3 = st.columns(3)
            ban_don_tiep = col_s1.text_input("Số lượng bàn đón tiếp")
            khan_ban = col_s2.selectbox("Cần trải khăn bàn hội trường", ["Không", "Có"])
            le_tan = col_s3.text_input("Số lượng lễ tân")
            
            bang_ten = col_s1.text_input("Số lượng bảng tên mica")
            bia_ky_ket = col_s2.text_input("Số lượng bìa ký kết")
            nuoc_uong = col_s3.text_input("Số lượng nước uống")
            
            teabreak = col_s1.text_input("Số phần Teabreak")
            hoa_ban = col_s2.text_input("Số lượng hoa để bàn")
            hoa_buc = col_s3.text_input("Số lượng hoa bục phát biểu")
            
            hoa_tang = col_s1.text_input("Số lượng hoa bó tặng")
            qua_tang = col_s2.text_input("Số lượng quà tặng")
            brochure = col_s3.text_input("Số lượng Brochure")
            
            khay_bung = col_s1.text_input("Số lượng khay bưng")
            bandroll = col_s2.text_input("Bandroll/Standee cần in & thi công")
            backdrop = col_s3.text_input("Backdrop cần in & thi công")
            
            bang_dien_tu = col_s1.selectbox("Cần chạy bảng điện tử", ["Không", "Có"])
            noi_dung_bdt = col_s2.text_area("Nội dung chạy bảng điện tử (nếu có)")
            thu_moi = col_s3.selectbox("Cần gửi thư mời", ["Không", "Có"])
            
            yeu_cau_khac = st.text_area("Các yêu cầu khác (nếu có)")
            
            submitted = st.form_submit_button("🚀 Gửi đăng ký sự kiện")
            if submitted:
                if not ten_sk.strip() or not don_vi.strip():
                    st.error("❌ Vui lòng điền đầy đủ Tên sự kiện và Đơn vị tổ chức!")
                else:
                    new_row = {
                        "Tên sự kiện": ten_sk.strip(),
                        "Đơn vị phụ trách/ tổ chức": don_vi.strip(),
                        "Ngày tổ chức": ngay_bd.strftime("%Y-%m-%d"),
                        "Ngày kết thúc": ngay_kt.strftime("%Y-%m-%d"),
                        "Giờ bắt đầu": gio_bd.strip(),
                        "Giờ kết thúc": gio_kt.strip(),
                        "Địa điểm tổ chức": dia_diem.strip(),
                        "Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp": "CÓ" if co_ho_tro else "KHÔNG",
                        "Số lượng bàn đón tiếp": ban_don_tiep.strip(),
                        "Cần trải khăn bàn hội trường": khan_ban,
                        "Số lượng lễ tân": le_tan.strip(),
                        "Số lượng bảng tên (bảng mica)": bang_ten.strip(),
                        "Số lượng bìa ký kết": bia_ky_ket.strip(),
                        "Số lượng nước uống": nuoc_uong.strip(),
                        "Số phần Teabreak": teabreak.strip(),
                        "Số lượng hoa để bàn": hoa_ban.strip(),
                        "Số lượng hoa để bục phát biểu": hoa_buc.strip(),
                        "Số lượng hoa bó để tặng": hoa_tang.strip(),
                        "Số lượng quà tặng": qua_tang.strip(),
                        "Số lượng Brochure": brochure.strip(),
                        "Số lượng khay bưng": khay_bung.strip(),
                        "Số lượng bandroll, standee cần in và thi công": bandroll.strip(),
                        "Số lượng Backdrop cần in và thi công": backdrop.strip(),
                        "Cần chạy bảng điện tử": bang_dien_tu,
                        "Nội dung chạy bảng điện tử (nếu có)": noi_dung_bdt.strip(),
                        "Cần gửi thư mời": thu_moi,
                        "Các yêu cầu khác (nếu có)": yeu_cau_khac.strip(),
                        "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)": ""
                    }
                    df_to_save = df.copy() if not df.empty else pd.DataFrame()
                    df_to_save = pd.concat([df_to_save, pd.DataFrame([new_row])], ignore_index=True)
                    if save_onedrive_excel(df_to_save):
                        st.success("🎉 Đăng ký sự kiện thành công và đã lưu vào hệ thống!")
                        st.cache_data.clear()
                        st.rerun()

# --- 3. PHÊ DUYỆT SỰ KIỆN ---
elif menu == "Phê duyệt sự kiện":
    st.markdown('<div class="table-title">⚖️ Phê duyệt Sự kiện (Dành cho Quản trị viên)</div>', unsafe_allow_html=True)
    
    if not st.session_state.auth_phe_duyet:
        pwd_pd = st.text_input("🔒 Nhập mật khẩu quản trị viên để vào trang phê duyệt:", type="password", key="pwd_pd_input")
        if st.button("Xác nhận mở khóa", key="btn_auth_pd"):
            if pwd_pd == PASSWORD_PHE_DUYET:
                st.session_state.auth_phe_duyet = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác. Quyền truy cập bị từ chối!")
    else:
        col_auth1, col_auth2 = st.columns([6, 1])
        with col_auth2:
            if st.button("🔒 Đăng xuất", key="btn_lock_pd"):
                st.session_state.auth_phe_duyet = False
                st.rerun()
                
        if st.button("🔄 Tải lại danh sách"):
            st.cache_data.clear()
            st.rerun()
            
        if df.empty:
            st.info("Chưa có dữ liệu sự kiện.")
        else:
            approvals = df.apply(approval_text_from_row, axis=1)
            df_pending = df[~approvals.eq("Thống nhất") & ~approvals.str.startswith("Thống nhất:")].copy()
            
            if df_pending.empty:
                st.success("✅ Hiện không có sự kiện nào đang chờ phê duyệt.")
            else:
                st.write(f"Đang có **{len(df_pending)}** sự kiện chờ xử lý:")
                for idx, r in df_pending.iterrows():
                    with st.expander(f"📌 {r['event']} - {r['donvi']} ({r['start'].strftime('%d/%m/%Y') if pd.notna(r['start']) else ''})"):
                        st.write(f"**Thời gian:** {r.get('start_time', '')} - {r.get('end_time', '')}")
                        st.write(f"**Địa điểm:** {r.get('location', 'Chưa rõ')}")
                        st.write(f"**Yêu cầu hỗ trợ:** {r.get('support', 'Không')}")
                        
                        y_kien = st.text_input("Ý kiến phê duyệt:", value=r.get("approval_opinion", ""), key=f"yk_{idx}")
                        col_b1, col_b2 = st.columns(2)
                        
                        if col_b1.button("✅ Thống nhất (Duyệt)", key=f"btn_ok_{idx}"):
                            opinion_str = f"Thống nhất: {y_kien.strip()}" if y_kien.strip() else "Thống nhất"
                            df_to_save = df.copy()
                            df_to_save.at[idx, "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"] = opinion_str
                            if save_onedrive_excel(df_to_save):
                                st.success(f"Đã duyệt sự kiện: {r['event']}")
                                st.cache_data.clear()
                                st.rerun()
                            
                    if col_b2.button("❌ Không thống nhất", key=f"btn_no_{idx}"):
                        opinion_str = f"Không thống nhất: {y_kien.strip()}" if y_kien.strip() else "Không thống nhất"
                        df_to_save = df.copy()
                        df_to_save.at[idx, "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"] = opinion_str
                        if save_onedrive_excel(df_to_save):
                            st.warning(f"Đã từ chối sự kiện: {r['event']}")
                            st.cache_data.clear()
                            st.rerun()

# --- 4. BÁO CÁO ---
elif menu == "Báo cáo":
    period = st.radio("Xem theo", ["Tuần", "Tháng", "Năm"], horizontal=True)
    df_p, lbl, _, _ = get_period_df(df_f, period)
    show_table_with_download(f"Báo cáo sự kiện ({lbl})", build_approval_summary_table(df_p), f"Bao_cao_su_kien_{period}.xlsx")

# --- 5. CẢNH BÁO TRÙNG LỊCH ---
elif menu == "Cảnh báo trùng lịch":
    df_app = keep_only_thong_nhat_for_calendar(df_f)
    conflicts = []
    for i in range(len(df_app)):
        for j in range(i + 1, len(df_app)):
            r1, r2 = df_app.iloc[i], df_app.iloc[j]
            if r1["location"] and r1["location"] == r2["location"]:
                if max(r1["full_start"], r2["full_start"]) < min(r1["full_end"], r2["full_end"]):
                    conflicts.append({
                        "Địa điểm": r1["location"],
                        "Sự kiện 1": r1["event"],
                        "Thời gian 1": r1["full_start"].strftime("%d/%m/%Y %H:%M"),
                        "Sự kiện 2": r2["event"],
                        "Thời gian 2": r2["full_start"].strftime("%d/%m/%Y %H:%M")
                    })
    show_table_with_download("Cảnh báo trùng lịch địa điểm", pd.DataFrame(conflicts), "Canh_bao_trung_lich.xlsx")

# --- 6. THỐNG KÊ HỖ TRỢ ---
elif menu == "Thống kê hỗ trợ":
    period = st.radio("Xem theo", ["Tuần", "Tháng", "Năm"], horizontal=True, key="tk_period")
    df_p, lbl, _, _ = get_period_df(df_f, period)
    df_sup = build_support_table(df_p)
    show_table_with_download(f"Thống kê chi tiết hỗ trợ ({lbl})", collapse_repeated_support_rows(df_sup), f"Thong_ke_ho_tro_{period}.xlsx")

# --- 7. TRUY VẤN AI ---
elif menu == "Truy vấn AI":
    st.markdown('<div class="table-title">🤖 Trợ lý AI Phân tích Sự kiện</div>', unsafe_allow_html=True)
    user_q = st.text_input("Nhập câu hỏi cần tra cứu hoặc thống kê sự kiện:")
    if user_q:
        st.info("Tính năng truy vấn sự kiện dựa trên dữ liệu Excel đang được xử lý.")
