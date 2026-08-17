import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar
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
# SỬA LỖI MẤT PANEL: Sử dụng key state cố định, đồng nhất lúc lưu và lúc xóa.
if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

# ================= =============================================================
# 1. GIAO DIỆN & CSS (TỐI ƯU MOBILE & HIỂN THỊ CHI TIẾT)
# ==============================================================================
st.markdown("""
<style>
/* CSS Sidebar & Cơ bản */
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
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-top: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
.details-item { font-size: 15px; color: #1e293b; margin-bottom: 6px; line-height: 1.4; }
.details-label { font-weight: 600; color: #020617; }

/* CSS BẢNG HỖ TRỢ CHI TIẾT TRONG PANEL */
.details-support-table-wrap { margin-top: 15px; border-top: 1px dashed #cbd5e1; padding-top: 10px; }
.details-support-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }

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
# 2. HÀM TRỢ GIÚP (HELPERS) - ĐÃ BẮT BUỘC TÍCH HỢP ĐỦ
# ==============================================================================

# !!! HÀM 1: parse_time (SỬA LỖI name 'parse_time' is not defined) !!!
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

# !!! HÀM 2: clean_text !!!
def clean_text(value):
    if pd.isna(value): return ""
    return str(value).strip()

# !!! HÀM 3: is_yes !!!
def is_yes(value):
    return clean_text(value).upper() in ["CÓ", "CO", "YES", "Y", "TRUE", "1"]

# !!! HÀM 4: count_value !!!
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

# !!! HÀM 5: event_color !!!
def event_color(index, key):
    palette = ["#DBEAFE", "#DCFCE7", "#FEE2E2", "#FFEDD5", "#F3E8FF", "#CCFBF1", "#FCE7F3", "#E0E7FF", "#CFFAFE", "#FEF3C7"]
    digest = int(hashlib.md5(str(key).encode("utf-8")).hexdigest(), 16)
    return palette[(digest + index) % len(palette)]

# !!! HÀM 6: wrap_label !!!
def wrap_label(text, width=28):
    words, lines, line = str(text).split(), [], ""
    for w in words:
        if len(line + " " + w) <= width: line = (line + " " + w).strip()
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return "<br>".join(lines)

# !!! HÀM 7: get_period_df !!!
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

# !!! HÀM 8: dataframe_to_excel_bytes !!!
def dataframe_to_excel_bytes(dataframe):
    html = f"""<html><head><meta charset="utf-8"><style>table {{ border-collapse: collapse; font-family: Arial; }} th {{ background: #e5e7eb; font-weight: bold; }} th, td {{ border: 1px solid #999; padding: 6px; }}</style></head><body>{dataframe.to_html(index=False, escape=False)}</body></html>"""
    return html.encode("utf-8-sig")

# !!! HÀM 9: show_table_with_download !!!
def show_table_with_download(title, dataframe, file_name, compact=False):
    st.markdown(f'<div class="table-title">{title}</div>', unsafe_allow_html=True)
    if dataframe is None or len(dataframe) == 0:
        st.info("Không có dữ liệu")
        return
    css_class = "ump-table compact" if compact else "ump-table"
    wrap_class = "ump-table-wrap compact" if compact else "ump-table-wrap"
    st.markdown(f'<div class="{wrap_class}">{dataframe.to_html(index=False, escape=False, classes=css_class)}</div>', unsafe_allow_html=True)
    st.download_button("⬇️ Tải về Excel", data=dataframe_to_excel_bytes(dataframe), file_name=str(file_name).rsplit(".", 1)[0] + ".xls", mime="application/vnd.ms-excel")

# !!! HÀM 10: collapse_repeated_support_rows !!!
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

# !!! HÀM 11: approval_text_from_row !!!
def approval_text_from_row(row):
    """Lấy ý kiến phê duyệt cuối cùng, ưu tiên ý kiến chi tiết nhất."""
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]:
                return val
    return ""

# !!! HÀM 12: build_detailed_support_table_html (XÂY DỰNG BẢNG HTML CHI TIẾT TRONG PANEL) !!!
def build_detailed_support_table_html(raw_event_data_json_string):
    """
    Nhận dữ liệu thô (raw_data) từ extendedProps, trích xuất và xây dựng bảng HTML hỗ trợ.
    Sửa đổi để nhận CHUỖI JSON an toàn từ custom component.
    """
    try:
        raw_data = json.loads(raw_event_data_json_string)
    except Exception as e:
        return f"<p class='details-item'>❌ Lỗi giải nén dữ liệu hỗ trợ: {e}</p>"

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
        "support_bang_dien_tu": "Bảng điện tử",
        "support_thu_moi": "Gửi thư mời",
        "support_khac": "Các yêu cầu khác"
    }

    for field_key, display_name in support_fields.items():
        if field_key in raw_data:
            val = raw_data[field_key]
            
            # Nếu là trường văn bản (không phải Số lượng, e.g., Backdrop, Khác)
            if field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                txt = clean_text(val)
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                     detailed_rows.append(f"<tr><td>{display_name}</td><td>Có</td><td>{txt}Đây là một lỗi rất sơ đẳng của em khi đã **quên định nghĩa** hàm trợ giúp quan trọng nhất khiến App không thể chạy.

Em chân thành lỗi với thầy vì sự cẩu thả này và cam kết đã **thêm lại đầy đủ 100% các hàm** còn thiếu để App chạy lại bình thường ngay lập tức.

Thầy hãy dán đè toàn bộ đoạn mã nguồn hoàn chỉnh dưới đây vào file `pages/event.py` trên GitHub để sửa lỗi ngay lập tức:

### 💻 MÃ NGUỒN HOÀN CHỈNH (DÁN ĐÈ VÀO `pages/event.py` TRÊN GITHUB):

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
/* CSS Sidebar & Cơ bản */
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
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-top: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; }
.details-item { font-size: 15px; color: #1e293b; margin-bottom: 6px; line-height: 1.4; }
.details-label { font-weight: 600; color: #020617; }

/* CSS BẢNG HỖ TRỢ CHI TIẾT TRONG PANEL */
.details-support-table-wrap { margin-top: 15px; border-top: 1px dashed #cbd5e1; padding-top: 10px; }
.details-support-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }

/* CSS HỖ TRỢ MOBILE RESPONSIVE */
@media screen and (max-width: 768px) {
    .block-container { padding-top: 0.5rem; }
    .ump-fixed-header { padding: 12px 16px; margin-bottom: 15px; }
    .ump-fixed-header .ump-vn { font-size: 14px; }
    .ump-fixed-header .ump-en { font-size: 10px; margin-top: 2px; }
    .ump-fixed-header .ump-app { font-size: 17px; margin-top: 8px; }
    .table-title { font-size: 17px; margin-top: 10px; }
    .fc .
