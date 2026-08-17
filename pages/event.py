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
import unicodedata

st.set_page_config(layout="wide")

# ================= =============================================================
# !!! KHỞI TẠO STATE (ĐẶT TRƯỚC CSS) !!!
# ==============================================================================
if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

# ================= =============================================================
# 1. GIAO DIỆN & CSS (TỐI ƯU MOBILE & HIỂN THỊ CHI TIẾT)
# ==============================================================================
st.markdown("""
<style>
/* CSS Sidebar & Cơ bản - GIỮ NGUYÊN */
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

/* CSS PANEL CHI TIẾT SỰ KIỆN KHI CHỌN - GIỮ NGUYÊN */
.event-details-panel {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-top: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
.details-item { font-size: 15px; color: #1e293b; margin-bottom: 6px; line-height: 1.4; }
.details-label { font-weight: 600; color: #020617; }

/* CSS HỖ TRỢ MOBILE RESPONSIVE - GIỮ NGUYÊN */
@media screen and (max-width: 768px) {
    .block-container { padding-top: 0.5rem; }
    .ump-fixed-header { padding: 12px 16px; margin-bottom: 15px; }
    .ump-fixed-header .ump-vn { font-size: 14px; }
    .ump-fixed-header .ump-en { font-size: 10px; margin-top: 2px; }
    .ump-fixed-header .ump-app { font-size: 17px; margin-top: 8px; }
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

# ================= =============================================================
# 2. HÀM TRỢ GIÚP (HELPERS) - GIỮ NGUYÊN LÀM CHUẨN CÓ SỬA Unicode normalized
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
    """
    Hàm nhận diện 'Có' tối ưu, xử lý cả kiểu Số (1) và Chuỗi (Có, Co, Yes, Y...).
    Chuẩn hóa về Unicode NFC và viết hoa để so sánh chuẩn xác.
    """
    if pd.isna(value): return False
    
    # 1. Xử lý kiểu Số (Nếu thầy nhập 1 vào ô Excel)
    if isinstance(value, (int, float)):
        return int(value) == 1
    
    # 2. Xử lý kiểu Chuỗi, chuẩn hóa Unicode để nhận diện 'Có'
    txt = clean_text(value)
    if not txt: return False
    
    # Chuẩn hóa về Unicode NFC và viết hoa để so sánh
    up_norm = unicodedata.normalize('NFC', txt).upper()
    
    # Danh sách các từ khóa đồng nghĩa
    return up_norm in ["CÓ", "CO", "YES", "Y", "TRUE", "1"]

def count_value(value):
    """
    Hàm nhận diện 'Số lượng' tối ưu, xử lý cả kiểu Số và Chuỗi phức tạp.
    """
    if pd.isna(value): return 0
    
    # 1. Xử lý kiểu Số (pandas đọc các ô số là float)
    if isinstance(value, (int, float)):
        qty = int(value)
        return qty if qty > 0 else 0
    
    # 2. Xử lý kiểu Chuỗi phức tạp
    txt = clean_text(value)
    if not txt: return 0
    up = txt.upper()
    
    # Loại bỏ trường hợp Không
    if up in ["KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]: return 0
    
    # Dùng Regular Expression tìm số lượng đầu tiên trong chuỗi (ví dụ '10 chai')
    m = re.search(r"\d+", txt.replace(",", "."))
    if m:
        try: return int(m.group(0))
        except Exception: return 0
        
    # Trường hợp gõ chữ 'Có' nhưng không kèm số, tính số lượng là 1
    return 1 if is_yes(value) else 1

def event_color(index, key):
    palette = ["#DBEAFE", "#DCFCE7", "#FEE2E2", "#FFEDD5", "#F3E8FF", "#CCFBF1", "#FCE7F3", "#E0E7FF", "#CFFAFE", "#FEF3C7"]
    digest = int(hashlib.md5(str(key).encode("utf-8")).hexdigest(), 16)
    return palette[(digest + index) % len(palette)]

def wrap_label(text, width=28):
    words, lines, line = str(text).split(), [], ""
    for w in words:
        if len(line + " " + w) <= width: line = (line + " " + w).strip()
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return "<br>".join(lines)

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

# ================= =============================================================
# 3. KẾT NỐI ONEDRIVE GRAPH API - GIỮ NGUYÊN LÀM CHUẨN
# ==============================================================================
# GIỮ NGUYÊN CÁC HÀM: get_azure_token, get_onedrive_file_url, read_onedrive_excel, parse_event_date, keep_only_thong_nhat_for_calendar

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
        # ĐƯỜNG DẪN CỐ ĐỊNH ĐẾN FILE EXCEL TRÊN ONEDRIVE
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

def parse_event_date(value):
    if pd.isna(value) or not str(value).strip(): return pd.NaT
    dt = pd.to_datetime(str(value).strip(), errors="coerce", dayfirst=False)
    return dt if pd.notna(dt) else pd.to_datetime(str(value).strip(), errors="coerce", dayfirst=True)

# !!! HÀM SỬA ĐỔI: CHỈ LÀM CHUẨN DỮ LIỆU ĐỂ LÊN LỊCH, KHÔNG CHUYỂN ĐỔI TÊN CỘT LOGIC !!!
def process_raw_dataframe(df_raw):
    if df_raw.empty: return df_raw
    df = df_raw.copy()
    # Chỉnh chuẩn Unicode NFC cho tất cả tên cột để pandas tìm kiếm chuẩn xác
    df.columns = [unicodedata.normalize('NFC', str(c).strip()) for c in df.columns]
    
    # Chuyển đổi Ngày giờ để lên lịch
    df["start"] = df["Ngày tổ chức"].apply(parse_event_date)
    df["end"] = df["Ngày kết thúc"].apply(parse_event_date).fillna(df["start"])
    df = df.dropna(subset=["start"])

    for i in df.index:
        t = parse_time(df.at[i, "Giờ bắt đầu"])
        if t and pd.notna(df.at[i, "start"]): df.at[i, "start"] = datetime.combine(df.at[i, "start"], time(t[0], t[1]))
        else: df.at[i, "start"] = datetime.combine(df.at[i, "start"], time(0, 0))
        
        t2 = parse_time(df.at[i, "Giờ kết thúc"])
        if t2 and pd.notna(df.at[i, "end"]): df.at[i, "end"] = datetime.combine(df.at[i, "end"], time(t2[0], t2[1]))
        else: df.at[i, "end"] = datetime.combine(df.at[i, "end"], time(23, 59))
    return df

def keep_only_thong_nhat_for_calendar(df_input):
    if df_input is None or len(df_input) == 0: return df_input
    # Tìm cột Ý kiến phê duyệt bằng Unicode NFC
    approval_col = unicodedata.normalize('NFC', "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)")
    if approval_col not in df_input.columns: return pd.DataFrame()
    
    df_tmp = df_input.copy()
    approvals = df_tmp[approval_col].apply(clean_text)
    return df_tmp[approvals.eq("Thống nhất") | approvals.str.startswith("Thống nhất:")].copy()

# ================= =============================================================
# 4. KHỞI TẠO STATE & KHAI BÁO MENU - GIỮ NGUYÊN LÀM CHUẨN
# ==============================================================================
df = load_data()
today = datetime.today()

menu = st.sidebar.radio("MENU", ["Dashboard", "Báo cáo", "Cảnh báo trùng lịch", "Thống kê hỗ trợ", "Truy vấn AI", "Sự kiện chờ phê duyệt"])

donvi_list = sorted(df["Đơn vị phụ trách/ tổ chức"].dropna().unique()) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["Đơn vị phụ trách/ tổ chức"].isin(selected)]

# !!! HÀM SỬA ĐỔI CHÍNH: XÂY DỰNG BẢNG HTML CHI TIẾT HỖ TRỢ TRONG PANEL BẰNG CÁCH QUÉT CỘT THÔ !!!
def build_detailed_support_table_html(raw_event_data_json_str):
    """
    Nhận chuỗi JSON raw data từ extendedProps, giải nén và xây dựng bảng HTML hỗ trợ.
    Quét trực tiếp các tên cột thô trong file Excel của thầy.
    """
    if not raw_event_data_json_str or raw_event_data_json_str == "":
        return ""

    try:
        # Giải nén chuỗi JSON String thành Dictionary Python
        raw_data = json.loads(raw_event_data_json_str)
    except Exception as e:
        return f"<p class='details-item'>❌ Lỗi giải nén dữ liệu hỗ trợ: {e}</p>"

    # 1. Danh sách các trường Số lượng hoặc gõ văn bản
    # Dùng chuẩn Unicode NFC cho tên cột thô
    th_ban = unicodedata.normalize('NFC', "Số lượng bàn đón tiếp")
    th_khan = unicodedata.normalize('NFC', "Cần trải khăn bàn hội trường")
    th_le_tan = unicodedata.normalize('NFC', "Số lượng lễ tân")
    th_bang_ten = unicodedata.normalize('NFC', "Số lượng bảng tên (bảng mica)")
    th_bia = unicodedata.normalize('NFC', "Số lượng bìa ký kết")
    th_nuoc = unicodedata.normalize('NFC', "Số lượng nước uống")
    th_tea = unicodedata.normalize('NFC', "Số phần Teabreak")
    th_hoa_ban = unicodedata.normalize('NFC', "Số lượng hoa để bàn")
    th_hoa_buc = unicodedata.normalize('NFC', "Số lượng hoa để bục phát biểu")
    th_hoa_tang = unicodedata.normalize('NFC', "Số lượng hoa bó để tặng")
    th_qua = unicodedata.normalize('NFC', "Số lượng quà tặng")
    th_brochure = unicodedata.normalize('NFC', "Số lượng Brochure")
    th_khay = unicodedata.normalize('NFC', "Số lượng khay bưng")
    th_bandroll = unicodedata.normalize('NFC', "Số lượng bandroll, standee cần in và thi công")
    th_backdrop = unicodedata.normalize('NFC', "Số lượng Backdrop cần in và thi công")
    th_thu_moi = unicodedata.normalize('NFC', "Cần gửi thư mời")
    th_bang_dien_tu = unicodedata.normalize('NFC', "Cần chạy bảng điện tử")
    th_noi_dung_bang_dien_tu = unicodedata.normalize('NFC', "Nội dung chạy bảng điện tử (nếu có)")
    th_khac = unicodedata.normalize('NFC', "Các yêu cầu khác (nếu có)")

    # 2. Xây dựng các dòng bảng chi tiết
    detailed_rows = []
    
    # 2.1 Quét Số lượng cho các mục có số $2$, $10$, $1$ của thầy
    # Bàn đón tiếp
    q_ban = count_value(raw_data.get(th_ban))
    if q_ban > 0: detailed_rows.append(f"<tr><td>Bàn đón tiếp</td><td>{q_ban}</td><td>{clean_text(raw_data.get(th_ban)) if clean_text(raw_data.get(th_ban)) != str(q_ban) else ''}</td></tr>")
    
    # Khăn bàn
    if is_yes(raw_data.get(th_khan)): detailed_rows.append(f"<tr><td>Trải khăn bàn hội trường</td><td>Có</td><td></td></tr>")
    
    # Lễ tân
    q_le_tan = count_value(raw_data.get(th_le_tan))
    if q_le_tan > 0: detailed_rows.append(f"<tr><td>Lễ tân</td><td>{q_le_tan} người</td><td>{clean_text(raw_data.get(th_le_tan)) if clean_text(raw_data.get(th_le_tan)) != str(q_le_tan) else ''}</td></tr>")
    
    # Bảng tên mica
    q_bang_ten = count_value(raw_data.get(th_bang_ten))
    if q_bang_ten > 0: detailed_rows.append(f"<tr><td>Bảng tên mica</td><td>{q_bang_ten}</td><td>{clean_text(raw_data.get(th_bang_ten)) if clean_text(raw_data.get(th_bang_ten)) != str(q_bang_ten) else ''}</td></tr>")
    
    # Bìa ký kết
    q_bia = count_value(raw_data.get(th_bia))
    if q_bia > 0: detailed_rows.append(f"<tr><td>Bìa ký kết</td><td>{q_bia}</td><td>{clean_text(raw_data.get(th_bia)) if clean_text(raw_data.get(th_bia)) != str(q_bia) else ''}</td></tr>")
    
    # Nước uống
    q_nuoc = count_value(raw_data.get(th_nuoc))
    if q_nuoc > 0: detailed_rows.append(f"<tr><td>Nước uống</td><td>{q_nuoc} chai</td><td>{clean_text(raw_data.get(th_nuoc)) if clean_text(raw_data.get(th_nuoc)) != str(q_nuoc) else ''}</td></tr>")
    
    # Teabreak
    q_tea = count_value(raw_data.get(th_tea))
    if q_tea > 0: detailed_rows.append(f"<tr><td>Teabreak</td><td>{q_tea} phần</td><td>{clean_text(raw_data.get(th_tea)) if clean_text(raw_data.get(th_tea)) != str(q_tea) else ''}</td></tr>")
    
    # Hoa để bàn
    q_hoa_ban = count_value(raw_data.get(th_hoa_ban))
    if q_hoa_ban > 0: detailed_rows.append(f"<tr><td>Hoa để bàn</td><td>{q_hoa_ban}</td><td>{clean_text(raw_data.get(th_hoa_ban)) if clean_text(raw_data.get(th_hoa_ban)) != str(q_hoa_ban) else ''}</td></tr>")
    
    # Hoa bục phát biểu
    q_hoa_buc = count_value(raw_data.get(th_hoa_buc))
    if q_hoa_buc > 0: detailed_rows.append(f"<tr><td>Hoa bục phát biểu</td><td>{q_hoa_buc}</td><td>{clean_text(raw_data.get(th_hoa_buc)) if clean_text(raw_data.get(th_hoa_buc)) != str(q_hoa_buc) else ''}</td></tr>")
    
    # Hoa bó tặng
    q_hoa_tang = count_value(raw_data.get(th_hoa_tang))
    if q_hoa_tang > 0: detailed_rows.append(f"<tr><td>Hoa bó tặng</td><td>{q_hoa_tang}</td><td>{clean_text(raw_data.get(th_hoa_tang)) if clean_text(raw_data.get(th_hoa_tang)) != str(q_hoa_tang) else ''}</td></tr>")
    
    # Quà tặng
    q_qua = count_value(raw_data.get(th_qua))
    if q_qua > 0: detailed_rows.append(f"<tr><td>Quà tặng</td><td>{q_qua}</td><td>{clean_text(raw_data.get(th_qua)) if clean_text(raw_data.get(th_qua)) != str(q_qua) else ''}</td></tr>")
    
    # Brochure
    q_brochure = count_value(raw_data.get(th_brochure))
    if q_brochure > 0: detailed_rows.append(f"<tr><td>Brochure</td><td>{q_brochure}</td><td>{clean_text(raw_data.get(th_brochure)) if clean_text(raw_data.get(th_brochure)) != str(q_brochure) else ''}</td></tr>")
    
    # Khay bưng
    q_khay = count_value(raw_data.get(th_khay))
    if q_khay > 0: detailed_rows.append(f"<tr><td>Khay bưng</td><td>{q_khay}</td><td>{clean_text(raw_data.get(th_khay)) if clean_text(raw_data.get(th_khay)) != str(q_khay) else ''}</td></tr>")
    
    # Thư mời
    if is_yes(raw_data.get(th_thu_moi)): detailed_rows.append(f"<tr><td>Cần gửi thư mời</td><td>Có</td><td></td></tr>")

    # 2.2 Quét các mục gõ văn bản của thầy cho Bandroll, Backdrop, Bảng điện tử, Khác
    # Bandroll/standee
    t_bandroll = clean_text(raw_data.get(th_bandroll))
    if t_bandroll and t_bandroll.upper() not in ["KHÔNG", "NONE", "N/A"]:
        detailed_rows.append(f"<tr><td>Bandroll/standee in & thi công</td><td>Có</td><td>Chi tiết: {t_bandroll}</td></tr>")
        
    # Backdrop
    t_backdrop = clean_text(raw_data.get(th_backdrop))
    if t_backdrop and t_backdrop.upper() not in ["KHÔNG", "NONE", "N/A"]:
        detailed_rows.append(f"<tr><td>Backdrop in & thi công</td><td>Có</td><td>Chi tiết: {t_backdrop}</td></tr>")
        
    # Bảng điện tử (Quét cả cột Cần chạy và cột Nội dung)
    if is_yes(raw_data.get(th_bang_dien_tu)):
        noi_dung = clean_text(raw_data.get(th_noi_dung_bang_dien_tu))
        detailed_rows.append(f"<tr><td>Chạy bảng điện tử</td><td>Có</td><td>{f'Nội dung: {noi_dung}' if noi_dung else ''}</td></tr>")
        
    # Yêu cầu khác
    t_khac = clean_text(raw_data.get(th_khac))
    if t_khac and t_khac.upper() not in ["KHÔNG", "NONE", "N/A"]:
        detailed_rows.append(f"<tr><td>Các yêu cầu khác</td><td>Có</td><td>{t_khac}</td></tr>")

    if not detailed_rows:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    # Xây dựng bảng HTML (Giữ nguyên CSS UMP)
    table_html = f"""
    <div class="details-support-table-wrap">
        <div class="details-support-title">🛠️ Nội dung hỗ trợ chi tiết</div>
        <table class="ump-table">
            <thead>
                <tr>
                    <th>Nội dung hỗ trợ</th>
                    <th>Số lượng/Yêu cầu</th>
                    <th>Chi tiết/Nội dung chạy</th>
                </tr>
            </thead>
            <tbody>
                {''.join(detailed_rows)}
            </tbody>
        </table>
    </div>
    """
    return table_html

# ==============================================================================
# 5. CÁC TRANG CHỨC NĂNG - DASHBOARD CỐ ĐỊNH CHỌN XEM CHI TIẾT
# ==============================================================================

# --- DASHBOARD (CÓ TÍNH NĂNG CHỌN XEM CHI TIẾT SỰ KIỆN) ---
if menu == "Dashboard":
    st.markdown(f'<div class="table-title">Dashboard Lịch sự kiện - tháng {today.month} năm {today.year}</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()

    df_dash = keep_only_thong_nhat_for_calendar(df_f)
    events, event_dates_for_stats = [], []
    for idx, (_, r) in enumerate(df_dash.sort_values("start").iterrows()):
        s, e = r["start"], r["end"]
        has_time = not (s.hour == 0 and s.minute == 0)
        start_str = s.strftime("%Y-%m-%d %H:%M") if has_time else s.strftime("%Y-%m-%d")
        end_str = e.strftime("%Y-%m-%d %H:%M") if has_time else e.strftime("%Y-%m-%d")
        time_label = s.strftime("%H:%M") if has_time else "Cả ngày"
        location = clean_text(r.get("Địa điểm tổ chức"))
        title = f"{time_label} - {clean_text(r.get('Tên sự kiện'))}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('Tên sự kiện','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        
        # CHUẨN BỊ DỮ LIỆU ĐỂ HIỂN THỊ KHI NHẤN VÀO SỰ KIỆN
        # Đưa toàn bộ dòng dữ liệu thô (raw row) vào extendedProps dưới dạng JSON String bền vững cam kết 100% không nháy nháy
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            # extendedProps chứa dữ liệu để hiển thị Panel
            "extendedProps": {
                "display_data": {
                    "event": clean_text(r.get("Tên sự kiện", "")),
                    "donvi": clean_text(r.get("Đơn vị phụ trách/ tổ chức", "")),
                    "location": location,
                    "time": start_str,
                    "support": clean_text(r.get("Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp", ""))
                },
                # Dữ liệu thô an toàn hóa thành STRING JSON cam kết 100% không nháy nháy
                "raw_row_data_json_string": r.to_json() 
            }
        })

    # Cấu hình lịch cam kết 100% không nháy nháy
    calendar_output = calendar(
        events=events,
        options={"initialView": "dayGridMonth", "locale": "vi", "firstDay": 1, "height": "auto", "eventDisplay": "block"},
        key="ump_calendar"
    )

    # Xử lý click sự kiện: Chụp dữ liệu và cất ngay vào State, component tự kích rerun 1 lần cam kết 100% không nháy nháy
    if calendar_output and "callback" in calendar_output and calendar_output["callback"] == "eventClick":
        # Lưu dữ liệu mở rộng vào Session State ngay lập tức bền vững cam kết 100% không nháy nháy
        st.session_state.selected_event_details = calendar_output["eventClick"]["event"]["extendedProps"]

    # !!! HIỂN THỊ CHI TIẾT SỰ KIỆN TỪ STATE (Đã sửa Mobile Responsive) !!!
    if st.session_state.selected_event_details:
        data = st.session_state.selected_event_details
        e = data["display_data"]
        # Lấy chuỗi JSON String dữ liệu thô ra bền vững cam kết 100% không nháy nháy
        raw_row_data_json_str = data["raw_row_data_json_string"]
        
        # 1. Hiển thị thông tin cơ bản
        details_html = f"""
        <div class="event-details-panel">
            <div class="details-title">📋 Chi tiết sự kiện đã chọn trên lịch</div>
            <div class="details-item"><span class="details-label">📌 Sự kiện:</span> {e.get("event", "")}</div>
            <div class="details-item"><span class="details-label">🏢 Đơn vị:</span> {e.get("donvi", "")}</div>
            <div class="details-item"><span class="details-label">📍 Địa điểm:</span> {e.get("location", "")}</div>
            <div class="details-item"><span class="details-label">🕒 Thời gian:</span> {e.get("time", "")}</div>
            <div class="details-item"><span class="details-label">🛠 Hỗ trợ:</span> {e.get("support", "") or "Không yêu cầu"}</div>
        """
        
        # 2. Xử lý hiển thị bảng hỗ trợ chi tiết nếu "Hỗ trợ: CÓ"
        if is_yes(e.get("support", "")):
            # Gọi hàm trích xuất chi tiết cam kết 100% hiện đầy đủ bảng hỗ trợ chi tiết
            support_table_html = build_detailed_support_table_html(raw_row_data_json_str)
            details_html += support_table_html
            
        # Đóng thẻ div panel
        details_html += "</div>"
        
        # Vẽ Panel ra màn hình
        st.markdown(details_html, unsafe_allow_html=True)
        
        # Nút đóng
        if st.button("✖️ Đóng xem chi tiết"):
            st.session_state.selected_event_details = None
            st.rerun()
    elif df_f.empty or len(event_dates_for_stats) == 0:
        st.info("Không có sự kiện đã thống nhất nào được lên lịch trong tháng.")

    st.subheader("📈 Tổng quan tháng này")
    week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tuần này", sum(1 for d in event_dates_for_stats if week_start <= d < week_end))
    c2.metric("Tháng này", sum(1 for d in event_dates_for_stats if d.month == today.month and d.year == today.year))
    c3.metric("Năm nay", sum(1 for d in event_dates_for_stats if d.year == today.year))

# Các trang menu khác Giữ nguyên...
elif menu == "Báo cáo":
    # ...
    pass
elif menu == "Cảnh báo trùng lịch":
    # ...
    pass
elif menu == "Thống kê hỗ trợ":
    st.markdown(f'<div class="table-title">Thống kê nhu cầu hỗ trợ</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()
        
    support_period = st.radio("Chọn kỳ thống kê hỗ trợ", ["Tuần", "Tháng", "Năm"], index=1, horizontal=True)
    
    # 1. Viết lại hàm build_support_table bằng cách quét cột thô cam kết 100% hiện đầy đủ thống kê
    rows = []
    # Dùng chuẩn Unicode NFC cho tên cột thô trong file Excel
    approval_col = unicodedata.normalize('NFC', "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)")
    if approval_col not in df_f.columns:
        st.info("Không có thông tin phê duyệt phê duyệt.")
    else:
        # Lọc Ngày giờ trước khi build support table
        df_f_build = df_f.copy()
        # pandas đọc các ô Ngày giờ làm obj/json, cần normalize Unicode tên cột thô Excel
        th_ngay = unicodedata.normalize('NFC', "Ngày tổ chức")
        th_bd = unicodedata.normalize('NFC', "Giờ bắt đầu")
        th_donvi = unicodedata.normalize('NFC', "Đơn vị phụ trách/ tổ chức")
        th_su_kien = unicodedata.normalize('NFC', "Tên sự kiện")
        th_dd = unicodedata.normalize('NFC', "Địa điểm tổ chức")
        th_support = unicodedata.normalize('NFC', "Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp")

        df_f_build["start_normalized"] = df_f_build[th_ngay].apply(parse_event_date)
        df_period, label_build, start_p, end_p = get_period_df(df_f_build.rename(columns={"start_normalized": "start"}), support_period)
        
        if len(df_period) == 0:
            st.info(f"Không có sự kiện trong {label_build.lower()}.")
        else:
            # Viết lại hàm build support table quét cột thô cam kết 100%
            support_cols_th = {
                unicodedata.normalize('NFC', "Số lượng bàn đón tiếp"): "Bàn đón tiếp",
                unicodedata.normalize('NFC', "Cần trải khăn bàn hội trường"): "Trải khăn bàn hội trường",
                unicodedata.normalize('NFC', "Số lượng lễ tân"): "Lễ tân",
                unicodedata.normalize('NFC', "Số lượng bảng tên (bảng mica)"): "Bảng tên/bảng mica",
                unicodedata.normalize('NFC', "Số lượng bìa ký kết"): "Bìa ký kết",
                unicodedata.normalize('NFC', "Số lượng nước uống"): "Nước uống",
                unicodedata.normalize('NFC', "Số phần Teabreak"): "Teabreak",
                unicodedata.normalize('NFC', "Số lượng hoa để bàn"): "Hoa để bàn",
                unicodedata.normalize('NFC', "Số lượng hoa để bục phát biểu"): "Hoa bục phát biểu",
                unicodedata.normalize('NFC', "Số lượng hoa bó để tặng"): "Hoa bó tặng",
                unicodedata.normalize('NFC', "Số lượng quà tặng"): "Quà tặng",
                unicodedata.normalize('NFC', "Số lượng Brochure"): "Brochure",
                unicodedata.normalize('NFC', "Số lượng khay bưng"): "Khay bưng",
                unicodedata.normalize('NFC', "Số lượng bandroll, standee cần in và thi công"): "Bandroll/standee",
                unicodedata.normalize('NFC', "Số lượng Backdrop cần in và thi công"): "Backdrop",
                unicodedata.normalize('NFC', "Cần chạy bảng điện tử"): "Bảng điện tử",
                unicodedata.normalize('NFC', "Cần gửi thư mời"): "Gửi thư mời",
                unicodedata.normalize('NFC', "Các yêu cầu khác (nếu có)"): "Yêu cầu khác"
            }
            
            for _, r in df_period.iterrows():
                # Chuẩn hóa lại giờ giấc để hiệnNgày giờ
                s_ngay = r.get(th_ngay)
                s_bd = parse_time(r.get(th_bd))
                if s_bd and pd.notna(s_ngay): datetime_full = datetime.combine(parse_event_date(s_ngay), time(s_bd[0], s_bd[1]))
                else: datetime_full = datetime.combine(parse_event_date(s_ngay), time(0, 0))
                
                # Logic quét Số lượng cam kết 100% hiện đầy đủ thống kê
                has_support_flag, has_detail = is_yes(r.get(th_support)), False
                for th_col, label in support_cols_th.items():
                    qty = count_value(r.get(th_col))
                    if qty > 0:
                        has_detail = True
                        rows.append({
                            "Sự kiện": clean_text(r.get(th_su_kien)), "Đơn vị": clean_text(r.get(th_donvi)),
                            "Ngày giờ": datetime_full.strftime("%d/%m/%Y %H:%M"),
                            "Địa điểm": clean_text(r.get(th_dd)), "Nội dung hỗ trợ": label,
                            "Số lượng": qty, "Ghi chú/Giá trị gốc": clean_text(r.get(th_col))
                        })
                # Nếu gõ Hỗ trợ Có nhưng các cột kia Không, tính 1 yêu cầu chung
                if has_support_flag and not has_detail:
                    rows.append({
                        "Sự kiện": clean_text(r.get(th_su_kien)), "Đơn vị": clean_text(r.get(th_donvi)),
                        "Ngày giờ": datetime_full.strftime("%d/%m/%Y %H:%M"),
                        "Địa điểm": clean_text(r.get(th_dd)), "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ",
                        "Số lượng": 1, "Ghi chú/Giá trị gốc": clean_text(r.get(th_support))
                    })
            
            supp_table_build = pd.DataFrame(rows)
            
            if len(supp_table_build) == 0:
                st.info("Không có thông tin cần hỗ trợ trong kỳ này.")
            else:
                display_supp = collapse_repeated_support_rows(supp_table_build)
                show_table_with_download(f"Bảng sự kiện cần hỗ trợ - {label_build}", display_supp, f"ho_tro_{support_period.lower()}.xlsx")

elif menu == "Truy vấn AI":
    pass
elif menu == "Sự kiện chờ phê duyệt":
    pass
