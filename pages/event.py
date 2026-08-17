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
# !!! KHỞI TẠO STATE (ĐẶT TRƯỚC CSS) !!!
# ==============================================================================
# 1. State để lưu trữ dữ liệu mở rộng (extendedProps) của sự kiện được chọn
if "selected_event_props" not in st.session_state:
    st.session_state.selected_event_props = None

# 2. State để lưu trữ dữ liệu thô (raw row) của sự kiện được chọn (để trích xuất hỗ trợ chi tiết)
if "selected_event_raw_row" not in st.session_state:
    st.session_state.selected_event_raw_row = None

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

/* CSS PANEL CHI TIẾT SỰ KIỆN KHI CHỌN */
.event-details-panel {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-top: 20px; margin-bottom: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
.details-item { font-size: 15px; color: #1e293b; margin-bottom: 6px; line-height: 1.4; }
.details-label { font-weight: 600; color: #020617; }

/* CSS HỖ TRỢ MOBILE RESPONSIVE */
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
}
</style>

<div class="ump-fixed-header">
  <div class="ump-vn">ĐẠI HỌC Y DƯỢC TP. HỒ CHÍ MINH</div>
  <div class="ump-en">UNIVERSITY OF MEDICINE AND PHARMACY AT HCMC</div>
  <div class="ump-app">Hệ thống quản trị sự kiện UMP</div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HÀM TRỢ GIÚP (HELPERS) - GIỮ NGUYÊN
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

# ==============================================================================
# 3. KẾT NỐI ONEDRIVE GRAPH API - GIỮ NGUYÊN
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

def approval_text_from_row(row):
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]:
                return val
    return ""

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
    df_out["_sort_time"] = pd.to_datetime(df_out["full_start"], errors="coerce")
    df_out = df_out.sort_values(["_sort_time", "donvi", "event"], ascending=[True, True, True]).reset_index(drop=True)

    for _, r in df_out.iterrows():
        s = r.get("full_start")
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
        "support_le_tan": "Lễ tân", "support_bang_ten": "Bảng tên/bảng mica",
        "support_bia_ky_ket": "Bìa ký kết", "support_nuoc_uong": "Nước uống",
        "support_teabreak": "Teabreak", "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu", "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng", "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng", "support_bandroll_standee": "Bandroll/standee",
        "support_backdrop": "Backdrop", "support_bang_dien_tu": "Bảng điện tử",
        "support_thu_moi": "Gửi thư mời", "support_khac": "Yêu cầu khác"
    }
    rows = []
    for _, r in df_input.iterrows():
        has_support_flag, has_detail = is_yes(r.get("support", "")), False
        for col, label in support_cols.items():
            if col in df_input.columns:
                qty = count_value(r.get(col, ""))
                if qty > 0:
                    has_detail = True
                    rows.append({
                        "Sự kiện": r.get("event", ""), "Đơn vị": r.get("donvi", ""),
                        "Ngày giờ": r.get("full_start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("full_start")) else "",
                        "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": label,
                        "Số lượng": qty, "Ghi chú/Giá trị gốc": clean_text(r.get(col, ""))
                    })
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": r.get("event", ""), "Đơn vị": r.get("donvi", ""),
                "Ngày giờ": r.get("full_start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("full_start")) else "",
                "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ",
                "Số lượng": 1, "Ghi chú/Giá trị gốc": clean_text(r.get("support", ""))
            })
    return pd.DataFrame(rows)

# ==============================================================================
# !!! HÀM MỚI BỔ SUNG: XÂY DỰNG BẢNG HTML CHI TIẾT HỖ TRỢ TRONG PANEL !!!
# ==============================================================================
def build_detailed_support_table_html(raw_event_data):
    """
    Trích xuất dữ liệu hỗ trợ chi tiết từ dữ liệu sự kiện thô lấy từ Session State
    và xây dựng bảng HTML chuẩn UMP.
    """
    if not raw_event_data:
        return ""

    # Danh sách các trường hỗ trợ cần kiểm tra trong Session State
    support_fields = {
        "Số lượng bàn đón tiếp": "Số lượng bàn đón tiếp",
        "Cần trải khăn bàn hội trường": "Cần trải khăn bàn hội trường",
        "Số lượng lễ tân": "Số lượng lễ tân (người)",
        "Số lượng bảng tên (bảng mica)": "Số lượng bảng tên mica",
        "Số lượng bìa ký kết": "Số lượng bìa ký kết",
        "Số lượng nước uống": "Số lượng nước uống (chai)",
        "Số phần Teabreak": "Số phần Teabreak",
        "Số lượng hoa để bàn": "Số lượng hoa để bàn",
        "Số lượng hoa để bục phát biểu": "Số lượng hoa để bục phát biểu",
        "Số lượng hoa bó để tặng": "Số lượng hoa bó để tặng",
        "Số lượng quà tặng": "Số lượng quà tặng",
        "Số lượng Brochure": "Số lượng Brochure",
        "Số lượng khay bưng": "Số lượng khay bưng",
        "Số lượng bandroll, standee cần in và thi công": "Bandroll/standee in & thi công",
        "Số lượng Backdrop cần in và thi công": "Backdrop in & thi công",
        "Cần gửi thư mời": "Cần gửi thư mời",
        "Các yêu cầu khác (nếu có)": "Các yêu cầu khác"
    }

    detailed_rows = []
    
    # 1. Xử lý các trường hỗ trợ thông thường
    for field_key, display_name in support_fields.items():
        if field_key in raw_event_data:
            val = raw_event_data[field_key]
            
            # Nếu là trường Cần/Không
            if field_key in ["Cần trải khăn bàn hội trường", "Cần gửi thư mời"]:
                if is_yes(val):
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>Có</td><td></td></tr>")
            
            # Nếu là trường văn bản/số lượng khác (Backdrop, Bandroll, Khác...)
            elif field_key in ["Số lượng bandroll, standee cần in và thi công", "Số lượng Backdrop cần in và thi công", "Các yêu cầu khác (nếu có)"]:
                txt = clean_text(val)
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                     detailed_rows.append(f"<tr><td>{display_name}</td><td>1</td><td>{txt}</td></tr>")
            
            # Mặc định là trường Số lượng
            else:
                qty = count_value(val)
                if qty > 0:
                    orig_val = clean_text(val)
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td><td>{orig_val if orig_val != str(qty) else ''}</td></tr>")

    # 2. Xử lý riêng trường Bảng điện tử (có nội dung chạy)
    if "Cần chạy bảng điện tử" in raw_event_data:
        if is_yes(raw_event_data["Cần chạy bảng điện tử"]):
            content = clean_text(raw_event_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
            detailed_rows.append(f"<tr><td>Chạy bảng điện tử</td><td>Có</td><td>{f'Nội dung: {content}' if content else ''}</td></tr>")

    if not detailed_rows:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    # Xây dựng bảng HTML hoàn chỉnh
    table_html = f"""
    <div class="details-support-table-wrap">
        <div class="details-support-title">🛠️ Nội dung hỗ trợ chi tiết</div>
        <table class="ump-table">
            <thead>
                <tr>
                    <th>Nội dung hỗ trợ</th>
                    <th>Số lượng</th>
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

# --- DASHBOARD (TỐI ƯU HIỂN THỊ CHI TIẾT KHI CLICK SỰ KIỆN) ---
if menu == "Dashboard":
    st.markdown(f'<div class="table-title">Dashboard Lịch sự kiện - tháng {today.month} năm {today.year}</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()

    events, event_dates_for_stats = [], []
    for idx, (_, r) in enumerate(df_f.sort_values("full_start").iterrows()):
        # Chỉ lên lịch những sự kiện có ý kiến quản lý là "Thống nhất"
        if not ("thống nhất" in r.get("approval_opinion", "").lower()):
            continue

        s, e = r["full_start"], r["full_end"]
        start_str = s.strftime("%Y-%m-%d %H:%M") if s.hour != 0 else s.strftime("%Y-%m-%d")
        end_str = e.strftime("%Y-%m-%d %H:%M") if e.hour != 23 else e.strftime("%Y-%m-%d")
        time_label = s.strftime("%H:%M") if s.hour != 0 else "Cả ngày"
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        
        # CHUẨN BỊ DỮ LIỆU ĐỂ HIỂN THỊ KHI NHẤN VÀO SỰ KIỆN
        # Đưa toàn bộ dòng dữ liệu thô (raw row) vào extendedProps
        event_raw_data = r.to_dict()
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            # extendedProps chứa dữ liệu để hiển thị Panel
            "extendedProps": {
                "display_data": {
                    "event": r.get("event", ""),
                    "donvi": r.get("donvi", ""),
                    "location": location,
                    "time": start_str,
                    "support": clean_text(r.get("support", ""))
                },
                # Dữ liệu thô để trích xuất bảng hỗ trợ chi tiết
                "raw_row_data": event_raw_data
            }
        })

    # CẤU HÌNH LỊCH, CÓ CALLBACK KHI NHẤN SỰ KIỆN
    selected_event = calendar(
        events=events,
        options={"initialView": "dayGridMonth", "locale": "vi", "firstDay": 1, "height": "auto", "eventDisplay": "block"},
        key="ump_calendar"
    )

    # !!! PHẦN SỬA LỖI CHÍNH: LƯU LẠI STATE KHI CLICK !!!
    # Xử lý click sự kiện: Lấy dữ liệu từ output của calendar component
    if selected_event and "callback" in selected_event and selected_event["callback"] == "eventClick":
        # Lưu dữ liệu mở rộng vào Session State ngay lập tức
        st.session_state.selected_event_details = selected_event["eventClick"]["event"]["extendedProps"]
        # Tải lại trang để vẽ Panel
        st.rerun()

    # !!! HIỂN THỊ CHI TIẾT SỰ KIỆN (CÓ BẢNG HỖ TRỢ CHI TIẾT) !!!
    if st.session_state.selected_event_details:
        data = st.session_state.selected_event_details
        e = data["display_data"]
        raw_data = data["raw_row_data"]
        
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
            # Gọi hàm xây dựng bảng HTML chi tiết
            support_table_html = build_detailed_support_table_html(raw_data)
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

# Các trang menu khác (Báo cáo, Cảnh báo...) giữ nguyên
elif menu == "Báo cáo":
    st.markdown(f'<div class="table-title">Báo cáo thống kê sự kiện</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()
        
    report_period = st.radio("Chọn kỳ báo cáo", ["Tuần", "Tháng", "Năm"], index=1, horizontal=True)
    df_report, report_label, _, _ = get_period_df(df_f, report_period)
    
    if len(df_report) == 0:
        st.info(f"Không có sự kiện trong {report_label.lower()}")
    else:
        summary = df_report.groupby("donvi").size().reset_index(name="Số sự kiện").sort_values("Số sự kiện", ascending=True)
        summary["Đơn vị hiển thị"] = summary["donvi"].apply(lambda x: wrap_label(x, 36))
        
        fig = px.bar(summary, x="Số sự kiện", y="Đơn vị hiển thị", text="Số sự kiện", color="donvi", orientation="h")
        st.plotly_chart(fig, use_container_width=True)

        table_report = summary[["donvi", "Số sự kiện"]].rename(columns={"donvi": "Đơn vị"}).reset_index(drop=True)
        table_report.insert(0, "STT", range(1, len(table_report) + 1))
        show_table_with_download(f"Bảng báo cáo - {report_label}", table_report, f"bao_cao_{report_period.lower()}.xlsx", compact=True)

elif menu == "Cảnh báo trùng lịch":
    st.markdown(f'<div class="table-title">Cảnh báo trùng lịch sự kiện</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()
        
    warning_period = st.radio("Chọn phạm vi cảnh báo", ["Tuần", "Tháng", "Năm"], index=0, horizontal=True)
    warn_df, period_label, _, _ = get_period_df(df_f, warning_period)
    
    conflicts = []
    for i in range(len(warn_df)):
        a = warn_df.iloc[i]
        for j in range(i + 1, len(warn_df)):
            b = warn_df.iloc[j]
            # Kiểm tra giao nhau của khoảng thời gian
            if a["full_start"] < b["full_end"] and b["full_start"] < a["full_end"]:
                same_loc = clean_text(a.get("location", "")).lower() == clean_text(b.get("location", "")).lower()
                conflicts.append({
                    "Thời gian": a["full_start"].strftime("%d/%m/%Y %H:%M"),
                    "Sự kiện 1": clean_text(a.get("event", "")),
                    "Đơn vị 1": clean_text(a.get("donvi", "")),
                    "Sự kiện 2": clean_text(b.get("event", "")),
                    "Đơn vị 2": clean_text(b.get("donvi", "")),
                    "Mức cảnh báo": "Trùng thời gian & địa điểm" if same_loc else "Trùng thời gian"
                })

    if not conflicts:
        st.success(f"{period_label} không có lịch trùng.")
    else:
        show_table_with_download(f"Danh sách trùng lịch - {period_label}", pd.DataFrame(conflicts), "canh_bao_trung_lich.xlsx")

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
    st.markdown(f'<div class="table-title">Truy vấn AI - Trợ lý thông minh</div>', unsafe_allow_html=True)
    st.info("💡 Trợ lý AI đang được tích hợp. Hiện tại thầy có thể nhập từ khóa đơn giản để tra cứu nhanh.")
    
    q = st.text_input("Nhập câu hỏi (ví dụ: tuần, tháng, năm, hỗ trợ):")
    if q:
        q_low = q.lower()
        if "tuần" in q_low or "tháng" in q_low or "năm" in q_low:
            p = "Tuần" if "tuần" in q_low else ("Tháng" if "tháng" in q_low else "Năm")
            p_df, label, _, _ = get_period_df(df_f, p)
            show_table_with_download(f"Sự kiện {label}", build_approval_summary_table(p_df), f"su_kien_{p.lower()}.xlsx")
        elif "hỗ trợ" in q_low or "ho tro" in q_low:
            supp_df = build_support_table(df_f[df_f["full_start"].dt.year == today.year])
            show_table_with_download("Danh sách cần hỗ trợ", collapse_repeated_support_rows(supp_df), "can_ho_tro.xlsx")
        else:
            st.warning("Hãy nhập từ khóa: tuần, tháng, năm hoặc hỗ trợ")

elif menu == "Sự kiện chờ phê duyệt":
    st.markdown(f'<div class="table-title">Danh sách sự kiện chờ phê duyệt</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()
        
    st.cache_data.clear()
    approval_df = read_onedrive_excel() # Không dùng cache
    if not approval_df.empty:
        df_renamed = process_raw_dataframe(approval_df)
        pending_df = df_renamed[df_renamed.apply(approval_text_from_row, axis=1) == ""].sort_values("full_start")

        if len(pending_df) == 0:
            st.success("Không có sự kiện nào đang chờ phê duyệt.")
        else:
            show_table_with_download("Danh sách chờ phê duyệt", build_approval_summary_table(pending_df), "cho_phe_duyet.xlsx")
            st.write(f"Tổng cộng: {len(pending_df)} sự kiện.")
            st.info("💡 Ban tổ chức vào OneDrive để phê duyệt. App sẽ cập nhật dữ liệu sau 15 giây hoặc khi thầy nhấn Làm mới.")

st.markdown("---")
st.markdown("Copyright © 2026 Bản quyền thuộc về Phòng Hành chính Tổng hợp, Đại học Y Dược Thành phố Hồ Chí Minh")
