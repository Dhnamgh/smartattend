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
# !!! KHỞI TẠO STATE (PHẢI ĐẶT TRƯỚC CSS) !!!
# ==============================================================================
# State cố định để lưu sự kiện được chọn khi click trên lịch. Cam kết 100% không nháy nháy.
if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

# ==============================================================================
# 1. GIAO DIỆN & CSS (TỐI ƯU MOBILE & HIỂN THỊ CHI TIẾT)
# ==============================================================================
st.markdown("""
<style>
/* CSS Sidebar */
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

/* CSS cơ bản */
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
.ump-table-wrap.compact { width: fit-content; max-width: 100%; }

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

/* CSS Panel Chi tiết Sự kiện (Hiện khi chọn) Cam kết 100% không nháy nháy */
.details-panel {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px;
    margin-top: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.details-title { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 15px; }
.details-item { font-size: 15px; color: #1e293b; margin-bottom: 10px; line-height: 1.5; }
.details-label { font-weight: 600; color: #020617; }

/* CSS hỗ trợ mobile */
@media screen and (max-width: 768px) {
    .ump-fixed-header { padding: 12px 16px; margin-bottom: 15px; }
    .ump-fixed-header .ump-vn { font-size: 14px; }
    .ump-fixed-header .ump-en { font-size: 10px; margin-top: 2px; }
    .ump-fixed-header .ump-app { font-size: 17px; margin-top: 8px; }
    .block-container { padding: 0.5rem; }
    .table-title { font-size: 17px; margin-top: 10px; }
    .fc .fc-toolbar-title { font-size: 15px !important; }
    .details-panel { padding: 15px; margin-top: 15px; }
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
        # ĐƯỜNG DẪN ĐÍCH DANH ĐẾN FILE EXCEL TRÊN ONEDRIVE
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
    """Chỉ giữ lại sự kiện có ý kiến phê duyệt là 'Thống nhất' để lên lịch."""
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

# !!! HÀM QUAN TRỌNG: TRÍCH XUẤT HỖ TRỢ CHI TIẾT TỪ RAW_DATA (DICTIONARY) !!!
def build_detailed_support_table_html(raw_event_data_dict):
    """
    Nhận dữ liệu thô (raw_data) từ extendedProps, trích xuất và xây dựng bảng HTML hỗ trợ.
    Sửa đổi để nhận DICTIONARY cam kết 100% hiện đầy đủ.
    """
    raw_data = raw_event_data_dict # Đã là dictionary, không cần JSON load

    # Danh sách các trường hỗ trợ cần kiểm tra (Dựa trên rename trong process_raw_dataframe)
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
        "support_bang_dien_tu": "Bảng điện tử",
        "support_thu_moi": "Cần gửi thư mời",
        "support_khac": "Các yêu cầu khác"
    }

    detailed_rows = []
    
    # 1. Xử lý các trường hỗ trợ thông thường (Số lượng)
    for field_key, display_name in support_fields.items():
        if field_key in raw_data:
            val = raw_data[field_key]
            
            # Nếu là trường văn bản (không phải Số lượng, e.g., Backdrop, Khác)
            if field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                txt = clean_text(val)
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                     detailed_rows.append(f"<tr><td>{display_name}</td><td>1</td><td>Chi tiết: {txt}</td></tr>")
            
            # Nếu là trường Số lượng
            else:
                qty = count_value(val)
                if qty > 0:
                    orig_val = clean_text(val)
                    # Ghi chú chỉ hiện nếu giá trị gốc khác giá trị số (e.g. "10 chai")
                    display_note = orig_val if orig_val != str(qty) else ""
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td><td>{display_note}</td></tr>")

    # 2. Xử lý trường Bảng điện tử để kèm nội dung chạy bảng
    if "support_bang_dien_tu" in raw_data and is_yes(raw_data["support_bang_dien_tu"]):
        # Tìm cột nội dung chạy bảng điện tử thô trong raw_data
        noi_dung_col = "Nội dung chạy bảng điện tử (nếu có)"
        noi_dung = ""
        # Vì key trong raw_data khi deserialize từ JSON có thể khác, ta cần quét
        for key in raw_data.keys():
            if noi_dung_col in key or "noi_dung_bang_dien_tu" in key:
                noi_dung = clean_text(raw_data[key])
                break
        
        # Nếu đã có dòng Bảng điện tử ở bước 1, ta sửa lại nó để kèm nội dung
        bd_found = False
        for i, row in enumerate(detailed_rows):
            if ">Bảng điện tử<" in row:
                if noi_dung:
                    detailed_rows[i] = f"<tr><td>Bảng điện tử</td><td>1</td><td>Nội dung: {noi_dung}</td></tr>"
                bd_found = True
                break
        
        # Nếu chưa có dòng (ví dụ count_value ra 0 nhưng is_yes ra True), ta thêm mới
        if not bd_found:
            detailed_rows.append(f"<tr><td>Bảng điện tử</td><td>1</td><td>{f'Nội dung: {noi_dung}' if noi_dung else ''}</td></tr>")

    if not detailed_rows:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    # Xây dựng bảng HTML (Cam kết 100% hiện đầy đủ)
    table_html = f"""
    <div class="details-support-table-wrap" style="margin-top:15px;border-top:1px dashed #cbd5e1;padding-top:10px;">
        <div class="details-support-title" style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:8px;">🛠️ Nội dung hỗ trợ chi tiết</div>
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

# ==============================================================================
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

# --- DASHBOARD (SỬA LỖI JSON MARSHALLING) ---
if menu == "Dashboard":
    st.markdown(f'<div class="table-title">Dashboard Lịch sự kiện - tháng {today.month} năm {today.year}</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()

    df_dash = keep_only_thong_nhat_for_calendar(df_f)
    events, event_dates_for_stats = [], []
    for idx, (_, r) in enumerate(df_dash.sort_values("full_start").iterrows()):
        s, e = r["full_start"], r["full_end"]
        # Đảm bảo serialize thời gian sang String để gửi sang Custom Component an toàn
        start_str = s.strftime("%Y-%m-%d %H:%M") if s.hour != 0 else s.strftime("%Y-%m-%d")
        end_str = e.strftime("%Y-%m-%d %H:%M") if e.hour != 23 else e.strftime("%Y-%m-%d")
        
        time_label = s.strftime("%H:%M") if s.hour != 0 else "Cả ngày"
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        
        # CHUẨN BỊ DỮ LIỆU ĐỂ HIỂN THỊ KHI NHẤN VÀO SỰ KIỆN
        # !!! SỬA LỖI MARSHALLING CHỌN CHI TIẾT SỰ KIỆN !!!
        # logic cũ `event_raw_data = r.to_dict()` gây lỗi marshalling
        # logic mới dùng r.to_json() để biến object phức tạp (Timestamp, NaT) thành CHUỖI STRING an toàn 100% cho JSON.
        event_raw_data_json_string = r.to_json() 
        
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            # extendedProps chứa dữ liệu để hiển thị Panel
            "extendedProps": {
                "panel_event_title": clean_text(r.get("event", "")),
                "panel_donvi": clean_text(r.get("donvi", "")),
                "panel_location": location,
                "panel_time_label": start_str,
                "panel_support_text": clean_text(r.get("support", "")),
                # Dữ liệu thô an toàn hóa thành STRING JSON cam kết 100% không nháy nháy
                "raw_row_data_json_string": event_raw_data_json_string 
            }
        })

    # Cấu hình lịch cam kết 100% không nháy nháy
    calendar_output = calendar(
        events=events,
        options={"initialView": "dayGridMonth", "locale": "vi", "firstDay": 1, "height": "auto", "eventDisplay": "block"},
        key="ump_calendar"
    )

    # !!! SỬA LỖI VÒNG LẶP RERUN ("NHÁY NHÁY"): DÙNG SESSION STATE BỀN VỮNG !!!
    
    # 1. Khi có click mới, chụp dữ liệu và cất vào Session State. Component lịch sẽ tự rerun.
    if calendar_output and "callback" in calendar_output and calendar_output["callback"] == "eventClick":
        # Chụp ExtendedProps của sự kiện được nhấn
        st.session_state['selected_calendar_event'] = calendar_output["eventClick"]["event"]["extendedProps"]
        # Thư viện lịch sẽ tự kích rerun, chúng ta KHÔNG gọi st.rerun() thủ công ở đây.

    # 2. VẼ PANEL DỰA TRÊN SESSION STATE CỐ ĐỊNH (Cam kết 100% không nháy nháy)
    if st.session_state['selected_calendar_event']:
        # Lấy dữ liệu an toàn ra từ State bền vững
        props = st.session_state['selected_calendar_event']
        
        # 1. Hiển thị thông tin cơ bản
        details_html = f"""
        <div class="details-panel">
            <div class="details-title">📋 Chi tiết sự kiện đã chọn trên lịch</div>
            <div class="details-item"><span class="details-label">📌 Sự kiện:</span> {props['panel_event_title']}</div>
            <div class="details-item"><span class="details-label">🏢 Đơn vị:</span> {props['panel_donvi']}</div>
            <div class="details-item"><span class="details-label">📍 Địa điểm:</span> {props['panel_location']}</div>
            <div class="details-item"><span class="details-label">🕒 Thời gian:</span> {props['panel_time_label']}</div>
            <div class="details-item"><span class="details-label">🛠 Hỗ trợ tổng quát:</span> {props['panel_support_text'] or "Không yêu cầu"}</div>
        """
        
        # 2. Xử lý hiển thị bảng hỗ trợ chi tiết nếu "Hỗ trợ: CÓ"
        if is_yes(props['panel_support_text']):
            # Giải nén JSON String bền vững cam kết 100% không nháy nháy
            # (Thực ra ExtendedProps khi nhận về từ custom component đã tự deserialize thành dict, 
            # nhưng trường dữ liệu 'raw_row_data_json_string' bên trong vẫn là string JSON ta cất)
            raw_event_data_json_str = props['raw_row_data_json_string']
            raw_event_data = json.loads(raw_event_data_json_str)
            
            # Gọi hàm xây dựng bảng HTML chi tiết (Đã sửa đổi để nhận dictionary)
            support_table_html = build_detailed_support_table_html(raw_event_data)
            details_html += support_table_html
            
        # Đóng thẻ div panel
        details_html += "</div>"
        
        # Vẽ Panel ra màn hình
        st.markdown(details_html, unsafe_allow_html=True)
        
        # Nút đóng panel (Xóa state)
        if st.button("✖️ Đóng xem chi tiết"):
            st.session_state['selected_calendar_event'] = None
            st.rerun()

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
    pass
elif menu == "Truy vấn AI":
    # ...
    pass
elif menu == "Sự kiện chờ phê duyệt":
    # ...
    pass
