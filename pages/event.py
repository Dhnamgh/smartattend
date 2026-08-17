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

# ================= =============================================================
# !!! KHỞI TẠO STATE (ĐẶT TRƯỚC CSS) !!!
# ==============================================================================
if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

# ==============================================================================
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

/* CSS BẢNG HỖ TRỢ CHI TIẾT TRONG PANEL - GIỮ NGUYÊN */
.details-support-table-wrap { margin-top: 15px; border-top: 1px dashed #cbd5e1; padding-top: 10px; }
.details-support-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }

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

# ==============================================================================
# !!! PHẦN SỬA ĐỔI CHÍNH: VIẾT LẠI LOGIC NHẬN DIỆN "CÓ" VÀ "SỐ LƯỢNG" TỐI ƯU !!!
# ==============================================================================

def is_yes(value):
    """
    Hàm nhận diện 'Có' tối ưu, xử lý cả kiểu Số (1) và Chuỗi (Có, Co, Yes, Y...).
    Đặc biệt xử lý các định dạng chữ 'Có' của thầy ạ.
    """
    if pd.isna(value): return False
    
    # 1. Xử lý kiểu Số (Nếu thầy nhập 1 vào ô Excel)
    if isinstance(value, (int, float)):
        return int(value) == 1
    
    # 2. Xử lý kiểu Chuỗi, chuẩn hóa Unicode để nhận diện 'Có'
    txt = clean_text(value)
    if not txt: return False
    
    # Chuẩn hóa về Unicode NFC và viết hoa để so sánh
    import unicodedata
    up_norm = unicodedata.normalize('NFC', txt).upper()
    
    # Danh sách các từ khóa đồng nghĩa
    return up_norm in ["CÓ", "CO", "YES", "Y", "TRUE", "1"]

def count_value(value):
    """
    Hàm nhận diện 'Số lượng' tối ưu, xử lý cả kiểu Số và Chuỗi phức tạp.
    """
    if pd.isna(value): return 0
    
    # 1. Xử lý kiểu Số (Nếu thầy nhập '2' vào ô Bàn đón tiếp)
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

# ================= =============================================================
# CÁC HÀM HELPERS KHÁC GIỮ NGUYÊN
# ==============================================================================
# GIỮ NGUYÊN CÁC HÀM: event_color, wrap_label, get_period_df, dataframe_to_excel_bytes, show_table_with_download, collapse_repeated_support_rows, approval_text_from_row

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

def approval_text_from_row(row):
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]:
                return val
    return ""

# ================= =============================================================
# CÁC HÀM KẾT NỐI & DỮ LIỆU GIỮ NGUYÊN
# ==============================================================================
# GIỮ NGUYÊN CÁC HÀM: get_azure_token, get_onedrive_file_url, read_onedrive_excel, save_onedrive_excel, parse_event_date, process_raw_dataframe, keep_only_thong_nhat_for_calendar, build_approval_summary_table, build_support_table, build_detailed_support_table_html

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

def parse_event_date(value):
    if pd.isna(value) or not str(value).strip(): return pd.NaT
    dt = pd.to_datetime(str(value).strip(), errors="coerce", dayfirst=False)
    return dt if pd.notna(dt) else pd.to_datetime(str(value).strip(), errors="coerce", dayfirst=True)

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
        "Nội dung chạy bảng điện tử (nếu có)": "support_bang_dien_tu_noi_dung", # Giữ nguyên tên cột thô
        "Cần gửi thư mời": "support_thu_moi", "Các yêu cầu khác (nếu có)": "support_khac",
        "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)": "approval_opinion"
    })

    df["start"] = df["start"].apply(parse_event_date)
    df["end"] = df["end"].apply(parse_event_date).fillna(df["start"])
    df = df.dropna(subset=["start"])

    for i in df.index:
        t = parse_time(df.at[i, "start_time"] if "start_time" in df.columns else None)
        if t and pd.notna(df.at[i, "start"]): df.at[i, "start"] = datetime.combine(df.at[i, "start"], time(t[0], t[1]))
        else: df.at[i, "start"] = datetime.combine(df.at[i, "start"], time(0, 0))
        t2 = parse_time(df.at[i, "end_time"] if "end_time" in df.columns else None)
        if t2 and pd.notna(df.at[i, "end"]): df.at[i, "end"] = datetime.combine(df.at[i, "end"], time(t2[0], t2[1]))
        else: df.at[i, "end"] = datetime.combine(df.at[i, "end"], time(23, 59))

    for col in ["event", "donvi", "location", "support", "approval_opinion"]:
        if col not in df.columns: df[col] = ""
        df[col] = df[col].apply(clean_text)
    return df

def keep_only_thong_nhat_for_calendar(df_input):
    if df_input is None or len(df_input) == 0: return df_input
    df_tmp = df_input.copy()
    approvals = df_tmp.apply(approval_text_from_row, axis=1)
    return df_tmp[approvals.eq("Thống nhất") | approvals.str.startswith("Thống nhất:")].copy()

def build_approval_summary_table(df_input):
    columns = ["Sự kiện", "Đơn vị", "Ngày giờ", "Địa điểm", "Hỗ trợ"]
    if df_input is None or len(df_input) == 0: return pd.DataFrame(columns=columns)
    rows = []
    df_out = df_input.copy()
    df_out["_sort_time"] = pd.to_datetime(df_out["start"], errors="coerce")
    df_out = df_out.sort_values(["_sort_time", "donvi", "event"], ascending=[True, True, True]).reset_index(drop=True)

    for _, r in df_out.iterrows():
        s = r.get("start")
        ngay_gio = s.strftime("%d/%m/%Y" if s.hour == 0 and s.minute == 0 else "%d/%m/%Y %H:%M") if pd.notna(s) else ""
        rows.append({
            "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
            "Ngày giờ": ngay_gio, "Địa điểm": clean_text(r.get("location", "")),
            "Hỗ trợ": clean_text(r.get("support", "")) or "Không"
        })
    return pd.DataFrame(rows, columns=columns)

def build_support_table(df_input):
    support_cols = {
        "support_ban_don_tiep": "Bàn đón tiếp", "support_khan_ban": "Trải khăn bàn hội trường",
        "support_le_tan": "Lễ tân (người)", "support_bang_ten": "Bảng tên/bảng mica",
        "support_bia_ky_ket": "Bìa ký kết", "support_nuoc_uong": "Nước uống (chai)",
        "support_teabreak": "Teabreak (phần)", "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu", "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng", "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng", "support_bandroll_standee": "Bandroll/standee in & thi công",
        "support_backdrop": "Backdrop in & thi công", "support_bang_dien_tu": "Bảng điện tử",
        "support_thu_moi": "Gửi thư mời", "support_khac": "Yêu cầu khác"
    }
    rows = []
    for _, r in df_input.iterrows():
        has_support_flag, has_detail = is_yes(r.get("support", "")), False
        for col, label in support_cols.items():
            if col in df_input.columns:
                # Xử lý trường Số lượng hoặc gõ CÓ
                qty = count_value(r.get(col, ""))
                if qty > 0:
                    has_detail = True
                    # Lấy giá trị thô để làm ghi chú
                    orig_val = clean_text(r.get(col, ""))
                    # Xử lý riêng Bảng điện tử để kèm nội dung
                    special_detail = ""
                    if col == "support_bang_dien_tu" and "support_bang_dien_tu_noi_dung" in df_input.columns:
                        content = clean_text(r.get("support_bang_dien_tu_noi_dung", ""))
                        if content: special_detail = f" (Nội dung: {content})"
                        
                    rows.append({
                        "Sự kiện": r.get("event", ""), "Đơn vị": r.get("donvi", ""),
                        "Ngày giờ": r.get("start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("start")) else "",
                        "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": label,
                        "Số lượng": qty, "Ghi chú/Giá trị gốc": f"{orig_val}{special_detail}"
                    })
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": r.get("event", ""), "Đơn vị": r.get("donvi", ""),
                "Ngày giờ": r.get("start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("start")) else "",
                "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ",
                "Số lượng": 1, "Ghi chú/Giá trị gốc": clean_text(r.get("support", ""))
            })
    return pd.DataFrame(rows)

def build_detailed_support_table_html(dataframe_support_table):
    """
    Xây dựng bảng HTML chi tiết hỗ trợ chuẩn UMP từ DataFrame thống kê.
    Dùng DataFrame đã trích xuất sẵn từ build_support_table để đảm bảo logic count_value/is_yes chuẩn xác.
    """
    if dataframe_support_table is None or len(dataframe_support_table) == 0:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    detailed_rows = []
    
    # 1. Gom các mục hỗ trợ thông thường và Số lượng
    for _, r in dataframe_support_table.iterrows():
        label = r["Nội dung hỗ trợ"]
        qty = r["Số lượng"]
        orig = r["Ghi chú/Giá trị gốc"]
        
        # Nếu số lượng là 1 (Cần khăn, Cần thư mời, hoặc gõ CÓ)
        if qty == 1 and orig.upper() in ["CÓ", "CO", "Y", "YES", "TRUE", "1"]:
             detailed_rows.append(f"<tr><td>{label}</td><td>Có</td><td></td></tr>")
        
        # Mặc định là số lượng
        else:
            # Tách nội dung đặc biệt của bảng điện tử ra khỏi ghi chú nếu có
            display_qty = str(qty)
            display_note = orig
            
            # Nếu nội dung gốc chứa ghi chú số lượng trùng với qty (ví dụ orig='10 chai' -> ' chai')
            match_qty = re.search(r"^\d+\s*", orig)
            if match_qty and len(orig) > len(match_qty.group(0)):
                display_note = orig[len(match_qty.group(0)):].strip()
            
            detailed_rows.append(f"<tr><td>{label}</td><td>{display_qty}</td><td>{display_note}</td></tr>")

    if not detailed_rows:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    # Xây dựng bảng HTML
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

# ================= =============================================================
# 4. KHỞI TẠO STATE & KHAI BÁO MENU - GIỮ NGUYÊN
# ==============================================================================
df = load_data()
today = datetime.today()

menu = st.sidebar.radio("MENU", ["Dashboard", "Báo cáo", "Cảnh báo trùng lịch", "Thống kê hỗ trợ", "Truy vấn AI", "Sự kiện chờ phê duyệt"])

donvi_list = sorted(df["donvi"].dropna().unique()) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["donvi"].isin(selected)]

# ==============================================================================
# 5. CÁC TRANG CHỨC NĂNG
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
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        
        # CHUẨN BỊ DỮ LIỆU ĐỂ HIỂN THỊ KHI NHẤN VÀO SỰ KIỆN
        # Đưa toàn bộ dòng dữ liệu thô (raw row) vào extendedProps
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            # extendedProps chứa dữ liệu gốc
            "extendedProps": {
                "display_data": {
                    "event": r.get("event", ""),
                    "donvi": r.get("donvi", ""),
                    "location": location,
                    "time": start_str,
                    "support": clean_text(r.get("support", ""))
                },
                # Dữ liệu thô để trích xuất bảng hỗ trợ chi tiết
                "raw_row_data_json_string": r.to_json() 
            }
        })

    # Cấu hình lịch
    calendar_output = calendar(
        events=events,
        options={"initialView": "dayGridMonth", "locale": "vi", "firstDay": 1, "height": "auto", "eventDisplay": "block"},
        key="ump_calendar"
    )

    # Xử lý click sự kiện
    if calendar_output and "callback" in calendar_output and calendar_output["callback"] == "eventClick":
        # Lưu dữ liệu mở rộng vào Session State ngay lập tức
        st.session_state.selected_event_details = calendar_output["eventClick"]["event"]["extendedProps"]
        st.rerun()

    # !!! HIỂN THỊ CHI TIẾT SỰ KIỆN (CÓ BẢNG HỖ TRỢ CHI TIẾT) !!!
    if st.session_state.selected_event_details:
        data = st.session_state.selected_event_details
        e = data["display_data"]
        # Giải nén chuỗi JSON String dữ liệu thô
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
            # Chuyển JSON String ngược lại DataFrame để dùng build_support_table
            try:
                raw_row_df = pd.DataFrame([json.loads(raw_row_data_json_str)])
                # Xử lý lại full_start để build_support_table nhận diện
                raw_row_df["start"] = pd.to_datetime(raw_row_df["start"], errors="coerce")
                raw_row_df["end"] = pd.to_datetime(raw_row_df["end"], errors="coerce")
                
                # Trích xuất DataFrame thống kê chi tiết của RIÊNG SỰ KIỆN NÀY
                specific_support_table = build_support_table(raw_row_df)
                
                # Gọi hàm xây dựng bảng HTML chi tiết
                support_table_html = build_detailed_support_table_html(specific_support_table)
                details_html += support_table_html
            except Exception as e:
                 details_html += f"<p class='details-item'>❌ Lỗi giải nén dữ liệu hỗ trợ: {e}</p>"
            
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
    df_supp, supp_label, _, _ = get_period_df(df_f, support_period)
    supp_table = build_support_table(df_supp)
    
    if len(supp_table) == 0:
        st.info("Không có thông tin cần hỗ trợ")
    else:
        display_supp = collapse_repeated_support_rows(supp_table)
        show_table_with_download(f"Bảng sự kiện cần hỗ trợ - {supp_label}", display_supp, f"ho_tro_{support_period.lower()}.xlsx")

elif menu == "Truy vấn AI":
    # ...
    pass
elif menu == "Sự kiện chờ phê duyệt":
    # ...
    pass
