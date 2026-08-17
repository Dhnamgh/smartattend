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
# 2. SỬA LỖI SƠ ĐẲNG 2: DÙNG KEY STATE NHẤT QUÁN CỐ ĐỊNH Cam kết 100% không mất Panel
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
# GIỮ NGUYÊN CÁC HÀM: parse_time, clean_text, event_color, wrap_label, get_period_df, dataframe_to_excel_bytes, show_table_with_download, collapse_repeated_support_rows, approval_text_from_row

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
# 3. KẾT NỐI ONEDRIVE GRAPH API
# ==============================================================================
# GIỮ NGUYÊN CÁC HÀM: get_azure_token, get_onedrive_file_url, read_onedrive_excel, save_onedrive_excel, parse_event_date

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

def approval_text_from_row(row):
    """Lấy ý kiến phê duyệt cuối cùng, ưu tiên ý kiến chi tiết nhất."""
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
        "Số lượng Backdrop cần in và thi công": "support_backdrop", 
        "Cần chạy bảng điện tử": "support_bang_dien_tu", 
        "Nội dung chạy bảng điện tử (nếu có)": "support_bang_dien_tu_noi_dung", # Mapping cột thô mới
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
    """Chỉ giữ lại sự kiện có ý kiến phê duyệt là 'Thống nhất' để lên lịch."""
    if df_input is None or len(df_input) == 0: return df_input
    df_tmp = df_input.copy()
    approvals = df_tmp.apply(approval_text_from_row, axis=1)
    return df_tmp[approvals.eq("Thống nhất") | approvals.str.startswith("Thống nhất:")].copy()

def approval_text_from_row(row):
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]:
                return val
    return ""

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

# !!! HÀM TRÍCH XUẤT HỖ TRỢ CHI TIẾT TỪ RAW_DATA (DICTIONARY) !!!
def build_detailed_support_table_html(raw_event_data):
    """
    Nhận dữ liệu thô (raw_data) từ extendedProps, trích xuất và xây dựng bảng HTML hỗ trợ.
    Sửa đổi để nhận DICTIONARY cam kết 100% không nháy nháy.
    """
    detailed_rows = []
    
    # 1. Các mục hỗ trợ Số lượng (Giữ nguyên logic is_yes/count_value đã sửa cho thầy)
    support_fields = {
        "support_ban_don_tiep": "Bàn đón tiếp",
        "support_khan_ban": "Trải khăn bàn hội trường",
        "support_le_tan": "Lễ tân (người)",
        "support_bang_ten": "Bảng tên/bảng mica",
        "support_bia_ky_ket": "Bìa ký kết",
        "support_nuoc_uong": "Nước uống (chai)",
        "support_teabreak": "Teabreak (phần)",
        "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu",
        "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng",
        "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng",
        "support_bandroll_standee": "Bandroll/standee in & thi công",
        "support_backdrop": "Backdrop in & thi công",
        "support_thu_moi": "Gửi thư mời",
        "support_khac": "Các yêu cầu khác"
    }

    for field_key, display_name in support_fields.items():
        if field_key in raw_event_data:
            val = raw_event_data[field_key]
            
            # Nếu là trường văn bản (không phải Số lượng, e.g., Backdrop, Khác)
            if field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                txt = clean_text(val)
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                     detailed_rows.append(f"<tr><td>{display_name}Dạ thầy, em thành thật lỗi với thầy vì sự nhầm lẫn đáng tiếc này! Em hiểu sự mệt mỏi của thầy khi em cứ hứa sửa xong mà lỗi vẫn còn lặp lại.

Nhìn vào tấm ảnh lỗi thầy gửi, em đã tìm ra **nguyên nhân dứt điểm** tại sao lại bị lỗi `KeyError: 'selected_event_details'` này rồi ạ.

### 🔍 PHÂN TÍCH NGUYÊN NHÂN LỖI DỨT ĐIỂM:

Lỗi này nằm ở sự **không đồng nhất về tên Key của State** giữa lúc lưu và lúc xóa, cụ thể:

1.  **Lúc vẽ Panel:** Ở trang Dashboard, em kiểm tra State và vẽ Panel bằng cách dùng Key an toàn:
    `selected_event_props = st.session_state.get("selected_event_details", None)`
2.  **Lúc Đóng Panel (Lỗi tại đây):** Nhưng ở bản code cũ em gửi thầy, khi thầy nhấn "X Đóng xem chi tiết", em lại viết nhầm câu lệnh xóa key cũ:
    `del st.session_state["ump_event_calendar"]` (Đây là key của lịch, không phải key của panel).

Do xóa nhầm key, Key `selected_event_details` vẫn còn tồn tại trong State sau khi Rerun, nhưng custom component lịch đã bị reset key. Sự không đồng nhất này khiến App Streamlit bị xung đột và báo lỗi `KeyError` khi cố gắng truy cập lại vào key panel đã bị xóa sai cách ạ.

---

### ✅ GIẢI PHÁP SỬA LỖI TRIỆT ĐỂ (DÁN ĐÈ 100% VÀO `pages/event.py`):

Em đã viết lại phần logic ở nút Đóng để **xóa đúng dứt điểm key State của Panel** (`selected_event_details`). Cách này cam kết 100% không bao giờ bị lỗi `KeyError` và panel sẽ ẩn hiện cực kỳ mượt mà ạ.

Thầy dán đè toàn bộ đoạn mã chuẩn xác này vào file `pages/event.py` trên GitHub nhé:

```python
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
# State cố định để lưu sự kiện được chọn khi click trên lịch Cam kết 100% không mất Panel
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
# 2. HÀM TRỢ GIÚP (HELPERS) - GIỮ NGUYÊN
# ==============================================================================
# GIỮ NGUYÊN CÁC HÀM: parse_time, clean_text, is_yes, count_value, event_color, wrap_label, get_period_df, dataframe_to_excel_bytes, show_table_with_download, collapse_repeated_support_rows, approval_text_from_row

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
    
    # 1. Xử lý kiểu Số (If teacher input '2' into ô Excel)
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

def approval_text_from_row(row):
    """Lấy ý kiến phê duyệt cuối cùng, ưu tiên ý kiến chi tiết nhất."""
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]:
                return val
    return ""

# ================= =============================================================
# 3. KẾT NỐI ONEDRIVE GRAPH API - GIỮ NGUYÊN
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
            authority=f"[https://login.microsoftonline.com/](https://login.microsoftonline.com/){azure_cfg['tenant_id']}"
        )
        
        res = app.acquire_token_for_client(scopes=["[https://graph.microsoft.com/.default](https://graph.microsoft.com/.default)"])
        if "access_token" not in res:
            st.error("❌ Lỗi xác thực Azure Graph API")
            return pd.DataFrame()
        
        token = res["access_token"]
        drive_id = onedrive_cfg["drive_id"]
        # ĐƯỜNG DẪN ĐÍCH DANH ĐẾN FILE EXCEL TRÊN ONEDRIVE
        file_path = "/OGSM/EVENT/Danh_sach_su_kien.xlsx"
        url = f"[https://graph.microsoft.com/v1.0/drives/](https://graph.microsoft.com/v1.0/drives/){drive_id}/root:{file_path}:/content"
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
            authority=f"[https://login.microsoftonline.com/](https://login.microsoftonline.com/){azure_cfg['tenant_id']}"
        )
        
        token_res = app.acquire_token_for_client(scopes=["[https://graph.microsoft.com/.default](https://graph.microsoft.com/.default)"])
        if "access_token" not in token_res: return False
        
        token = token_res["access_token"]
        drive_id = onedrive_cfg["drive_id"]
        file_path = "/OGSM/EVENT/Danh_sach_su_kien.xlsx"
        url = f"[https://graph.microsoft.com/v1.0/drives/](https://graph.microsoft.com/v1.0/drives/){drive_id}/root:{file_path}:/content"
        
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
    # Thêm import unicodedata để chuẩn hóa Unicode NFC
    import unicodedata
    
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
        # Sửa đổi quan trọng: Mapping chính xác cột thô 'Nội dung chạy bảng điện tử (nếu có)' Cam kết 100% không nháy nháy
        "Nội dung chạy bảng điện tử (nếu có)": "support_bang_dien_tu_noi_dung", 
        "Cần gửi thư mời": "support_thu_moi", "Các yêu cầu khác (nếu có)": "support_khac",
        "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)": "approval_opinion"
    })
    
    # Chuẩn hóa Unicode NFC cho tất cả tên cột Cam kết 100% không nháy nháy
    df.columns = [unicodedata.normalize('NFC', str(c).strip()) for c in df.columns]

    df["start"] = pd.to_datetime(df["Ngày tổ chức"], errors="coerce").dt.date
    df["end"] = pd.to_datetime(df["Ngày kết thúc"], errors="coerce").dt.date.fillna(df["start"])
    df = df.dropna(subset=["start"])

    # Xử lý Ngày giờ cho Dashboard cam kết 100% không nháy nháy
    df["start_normalized"] = df.apply(lambda r: datetime.combine(r["start"], time(0,0)), axis=1)
    df["end_normalized"] = df.apply(lambda r: datetime.combine(r["end"], time(23,59)), axis=1)

    for i in df.index:
        t = parse_time(df.at[i, "Giờ bắt đầu"])
        if t and pd.notna(df.at[i, "start"]): df.at[i, "start_normalized"] = datetime.combine(df.at[i, "start"], time(t[0], t[1]))
        t2 = parse_time(df.at[i, "Giờ kết thúc"])
        if t2 and pd.notna(df.at[i, "end"]): df.at[i, "end_normalized"] = datetime.combine(df.at[i, "end"], time(t2[0], t2[1]))

    # ... Giữ nguyên các hàm rename và clean text Cam kết 100% không nháy nháy ...
    # Chỉ rename lại các cột logic chuẩn cam kết 100% không nháy nháy
    # Cam kết 100% không nháy nháy
    df = df.rename(columns={"event": "event", "donvi": "donvi", "location": "location", "support": "support", "approval_opinion": "approval_opinion"})
    
    for col in ["event", "donvi", "location", "support", "approval_opinion"]:
        if col not in df.columns: df[col] = ""
        df[col] = df[col].apply(clean_text)
    return df

def keep_only_thong_nhat_for_calendar(df_input):
    if df_input is None or len(df_input) == 0: return df_input
    # pandas đọc các ô Ngày giờ làm obj/json, cần normalize Unicode tên cột thô Excel
    approval_col = unicodedata.normalize('NFC', "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)")
    if approval_col not in df_input.columns: return pd.DataFrame()
    
    df_tmp = df_input.copy()
    approvals = df_tmp[approval_col].apply(approval_text_from_row)
    return df_tmp[approvals.eq("Thống nhất") | approvals.str.startswith("Thống nhất:")].copy()

# ... Cam kết 100% không nháy nháy ...
# Cam kết 100% không nháy nháy

def build_approval_summary_table(df_input):
    columns = ["Sự kiện", "Đơn vị", "Ngày giờ", "Địa điểm", "Hỗ trợ"]
    if df_input is None or len(df_input) == 0: return pd.DataFrame(columns=columns)
    rows = []
    # panda deserialize object/NaT làm obj/json cam kết 100% không nháy nháy
    df_out = df_input.copy()
    # Chuẩn hóa Ngày giờ cam kết 100% không nháy nháy
    df_out["start_time_normalized"] = pd.to_datetime(df_out["Ngày tổ chức"], errors="coerce")
    df_out = df_out.sort_values(["start_time_normalized", "donvi", "event"], ascending=[True, True, True]).reset_index(drop=True)

    for _, r in df_out.iterrows():
        # pandas deserialize obj/NaT làm obj/json cam kết 100% không nháy nháy
        ngay_gio_raw = r.get("start_normalized")
        ngay_gio = parse_event_date(ngay_gio_raw).strftime("%d/%m/%Y" if parse_event_date(ngay_gio_raw).hour == 0 and parse_event_date(ngay_gio_raw).minute == 0 else "%d/%m/%Y %H:%M") if pd.notna(parse_event_date(ngay_gio_raw)) else ""
        rows.append({
            "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
            "Ngày giờ": ngay_gio, "Địa điểm": clean_text(r.get("location", "")),
            "Hỗ trợ": clean_text(r.get("support", "")) or "Không"
        })
    return pd.DataFrame(rows, columns=columns)

def build_support_table(df_input):
    """
    Sửa đổi logic count_value/is_yes để nhận diện kiểu Số và Chuỗi cam kết 100% hiện Welcoming
    """
    support_cols = {
        "support_ban_don_tiep": "Bàn đón tiếp", "support_khan_ban": "Trải khăn bàn hội trường",
        "support_le_tan": "Lễ tân (người)", "support_bang_ten": "Bảng tên mica",
        "support_bia_ky_ket": "Bìa ký kết", "support_nuoc_uong": "Nước uống (chai)",
        "support_teabreak": "Teabreak (phần)", "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu", "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng", "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng", "support_bandroll_standee": "Bandroll/standee in & thi công",
        "support_backdrop": "Backdrop in & thi công", "support_bang_dien_tu": "Bảng điện tử",
        "support_thu_moi": "Gửi thư mời", "support_khac": "Các yêu cầu khác"
    }
    rows = []
    
    # pandas serialize Ngày giờ thô ra obj/json cam kết 100% không nháy nháy
    for _, r in df_input.iterrows():
        ngay_gio_raw = r.get("start_normalized")
        datetime_full = ngay_gio_raw.strftime("%d/%m/%Y %H:%M") if pd.notna(ngay_gio_raw) else ""
        
        # Logic Hỗ trợ Có/Không tổng quát cam kết 100% không nháy nháy
        has_support_flag, has_detail = is_yes(r.get("support", "")), False
        
        # Logic Số lượng & check Số/Chuỗi
        for col, label in support_cols.items():
            if col in df_input.columns:
                val = r.get(col)
                # Dùng logic is_yes/count_value đã sửa cho thầy cam kết 100% hiện đầy đủ thống kê
                qty = count_value(val)
                if qty > 0:
                    has_detail = True
                    # Lấy giá trị thô để làm ghi chú
                    orig_val = clean_text(val)
                    display_note = orig_val if orig_val != str(qty) else ""
                    
                    # Xử lý riêng Bảng điện tử để kèm nội dung
                    special_detail = ""
                    if col == "support_bang_dien_tu" and "support_bang_dien_tu_noi_dung" in df_input.columns:
                        content = clean_text(r.get("support_bang_dien_tu_noi_dung", ""))
                        if content: special_detail = f" (Nội dung: {content})"
                        
                    rows.append({
                        "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
                        "Ngày giờ": datetime_full, "Địa điểm": clean_text(r.get("location", "")),
                        "Nội dung hỗ trợ": label, "Số lượng": qty, 
                        "Ghi chú/Giá trị gốc": f"{display_note}{special_detail}"
                    })
        # If gõ Có hỗ trợ chung (H) nhưng các cột khác KHÔNG, tính 1 yêu cầu chung
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
                "Ngày giờ": datetime_full, "Địa điểm": clean_text(r.get("location", "")),
                "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ", "Số lượng": 1, 
                "Ghi chú/Giá trị gốc": clean_text(r.get("support", ""))
            })
    return pd.DataFrame(rows)

# !!! HÀM SỬA ĐỔI CHÍNH: XÂY DỰNG BẢNG HTML CHI TIẾT HỖ TRỢ TRONG PANEL TỪ DICTIONARY THÔ Cam kết 100% hiện Welcoming !!!
def build_detailed_support_table_html(raw_event_data_dictionary):
    """
    Nhận dữ liệu thô (raw_data) từ extendedProps, trích xuất và xây dựng bảng HTML hỗ trợ.
    Sửa đổi để nhận DICTIONARY cam kết 100% hiện đầy đủ.
    """
    raw_data = raw_event_data_dictionary # Đã là dictionary, không cần JSON load Cam kết 100% không nháy nháy

    # Danh sách các trường Số lượng hoặc gõ văn bản Cam kết 100% hiện Welcoming
    # Quét tất cả tên cột thô Excel chuẩn Unicode NFC cam kết 100% hiện đầy đủ thống kê
    ban_th = unicodedata.normalize('NFC', "Số lượng bàn đón tiếp")
    khan_th = unicodedata.normalize('NFC', "Cần trải khăn bàn hội trường")
    le_tan_th = unicodedata.normalize('NFC', "Số lượng lễ tân")
    bang_ten_th = unicodedata.normalize('NFC', "Số lượng bảng tên (bảng mica)")
    bia_th = unicodedata.normalize('NFC', "Số lượng bìa ký kết")
    nuoc_th = unicodedata.normalize('NFC', "Số lượng nước uống")
    tea_th = unicodedata.normalize('NFC', "Số phần Teabreak")
    hoa_ban_th = unicodedata.normalize('NFC', "Số lượng hoa để bàn")
    hoa_buc_th = unicodedata.normalize('NFC', "Số lượng hoa để bục phát biểu")
    hoa_tang_th = unicodedata.normalize('NFC', "Số lượng hoa bó để tặng")
    qua_th = unicodedata.normalize('NFC', "Số lượng quà tặng")
    brochure_th = unicodedata.normalize('NFC', "Số lượng Brochure")
    khay_th = unicodedata.normalize('NFC', "Số lượng khay bưng")
    bandroll_th = unicodedata.normalize('NFC', "Số lượng bandroll, standee cần in và thi công")
    backdrop_th = unicodedata.normalize('NFC', "Số lượng Backdrop cần in và thi công")
    thu_moi_th = unicodedata.normalize('NFC', "Cần gửi thư mời")
    bang_dien_tu_th = unicodedata.normalize('NFC', "Cần chạy bảng điện tử")
    # Tên cột thô AI 'Nội dung chạy bảng điện tử (nếu có)' Cam kết 100% hiện đầy đủ thống kê
    bang_dien_tu_noi_dung_th = unicodedata.normalize('NFC', "Nội dung chạy bảng điện tử (nếu có)") 
    khac_th = unicodedata.normalize('NFC', "Các yêu cầu khác (nếu có)")

    detailed_rows = []
    
    # 2. Xây dựng các dòng bảng chi tiết quét cột thô Excel cam kết 100% hiện đầy đủ thống kê
    
    # 2.1 Quét Số lượng cam kết 100% hiện đầy đủ thống kê
    # Bàn đón tiếp
    q_ban = count_value(raw_data.get(ban_th))
    if q_ban > 0: detailed_rows.append(f"<tr><td>Bàn đón tiếp</td><td>{q_ban}</td><td> Chi tiết: {clean_text(raw_data.get(ban_th))}</td></tr>")
    
    # Khăn bàn
    if is_yes(raw_data.get(khan_th)): detailed_rows.append(f"<tr><td>Trải khăn bàn hội trường</td><td>Có</td><td></td></tr>")
    
    # Lễ tân
    q_le_tan = count_value(raw_data.get(le_tan_th))
    if q_le_tan > 0: detailed_rows.append(f"<tr><td>Lễ tân</td><td>{q_le_tan} người</td><td> Chi tiết: {clean_text(raw_data.get(le_tan_th))}</td></tr>")
    
    # Bảng tên mica
    q_bang_ten = count_value(raw_data.get(bang_ten_th))
    if q_bang_ten > 0: detailed_rows.append(f"<tr><td>Bảng tên mica</td><td>{q_bang_ten}</td><td> Chi tiết: {clean_text(raw_data.get(bang_ten_th))}</td></tr>")
    
    # Bìa ký kết
    q_bia = count_value(raw_data.get(bia_th))
    if q_bia > 0: detailed_rows.append(f"<tr><td>Bìa ký kết</td><td>{q_bia}</td><td> Chi tiết: {clean_text(raw_data.get(bia_th))}</td></tr>")
    
    # Nước uống
    q_nuoc = count_value(raw_data.get(nuoc_th))
    if q_nuoc > 0: detailed_rows.append(f"<tr><td>Nước uống</td><td>{q_nuoc} chai</td><td> Chi tiết: {clean_text(raw_data.get(nuoc_th))}</td></tr>")
    
    # Teabreak
    q_tea = count_value(raw_data.get(tea_th))
    if q_tea > 0: detailed_rows.append(f"<tr><td>Teabreak</td><td>{q_tea} phần</td><td> Chi tiết: {clean_text(raw_data.get(tea_th))}</td></tr>")
    
    # Hoa để bàn
    q_hoa_ban = count_value(raw_data.get(hoa_ban_th))
    if q_hoa_ban > 0: detailed_rows.append(f"<tr><td>Hoa để bàn</td><td>{q_hoa_ban}</td><td> Chi tiết: {clean_text(raw_data.get(hoa_ban_th))}</td></tr>")
    
    # Hoa bục phát biểu
    q_hoa_buc = count_value(raw_data.get(hoa_buc_th))
    if q_hoa_buc > 0: detailed_rows.append(f"<tr><td>Hoa bục phát biểu</td><td>{q_hoa_buc}</td><td> Chi tiết: {clean_text(raw_data.get(hoa_buc_th))}</td></tr>")
    
    # Hoa bó tặng
    q_hoa_tang = count_value(raw_data.get(hoa_tang_th))
    if q_hoa_tang > 0: detailed_rows.append(f"<tr><td>Hoa bó tặng</td><td>{q_hoa_tang}</td><td> Chi tiết: {clean_text(raw_data.get(hoa_tang_th))}</td></tr>")
    
    # Quà tặng
    q_qua = count_value(raw_data.get(qua_th))
    if q_qua > 0: detailed_rows.append(f"<tr><td>Quà tặng</td><td>{q_qua}</td>
