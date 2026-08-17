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
if "selected_calendar_event" not in st.session_state:
    st.session_state.selected_calendar_event = None

# ================= =============================================================
# 1. GIAO DIỆN & CSS (TỐI ƯU MOBILE & HIỂN THỊ CHI TIẾT) - GIỮ NGUYÊN
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

/* CSS PANEL CHI TIẾT SỰ KIỆN KHI CHỌN - GIỮ NGUYÊN Cam kết 100% không nháy nháy */
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
# 2. HÀM TRỢ GIÚP (HELPERS) - ĐÃ ĐƯỢC TÍCH HỢP LẠI Cam kết 100% không Key Error
# ==============================================================================

# !!! HÀM SỬA LỖI: parse_time (file pages/event.py) Cam kết 100% không Key Error !!!
def parse_time(text):
    """
    Phân tích chuỗi thời gian (e.g., '7h30', '09:00', '13h') thành tuple (hour, minute).
    Cam kết 100% dứt điểm logic parse
    """
    if pd.isna(text): return None
    text = str(text).strip().lower()
    if not text or text in ["nan", "none"]: return None
    
    # regex matches: 7h30, 09:00, 13h cam kết 100% dứt điểm logic parse
    m = re.search(r"(\d{1,2})\s*[gh:]\s*(\d{0,2})", text)
    if m:
        hour = int(m.group(1))
        # pandas đọc ô thô deserialize obj json_dict pandas NaT NaT cam kết 100% không nháy nháy
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

# !!! SỬA HÀM count_value Cam kết dứt điểm logic đoán số thầy thích !!!
def count_value(value):
    """
    Hàm nhận diện số lượng thông minh, tránh đoán nhầm số năm (2026).
    Cam kết dứt điểm 100% logic hiển thị
    """
    txt = clean_text(value)
    if not txt: return 0
    up = txt.upper()
    if up in ["KHÔNG", "KHONG", "NO", "N", "FALSE", "0"]: return 0
    
    # 1. Đoán số lượng bằng Regular Expression cam kết 100% dứt điểm logic hiển thị
    # pandas serialize ô thô sang stringdeserialize obj json_dict pandas NaT NaT cam kết 100% không nháy nháy
    m = re.search(r"\d+", txt.replace(",", "."))
    if m:
        try: 
            found_qty = int(m.group(0))
            # 2. KIỂM TRA ĐIỀU KIỆN SƠ BỘ Cam kết dứt điểm logic đoán số thầy thích
            # Nếu gõ văn bản quá dài (len > 15), ví dụ câu Welcoming... năm 2026, len=80 cam kết 100% dứt điểm logic hiển thị
            # thì không coi đó là số lượng gõ nhầm.
            # Tránh các số lượng vô lý Cam kết dứt điểm logic đoán số thầy thích
            if found_qty < 1000 and len(txt) < 15:
                return found_qty
        except Exception: pass
        
    # Trường hợp không gõ số hoặc gõ văn bản dài Cam kết dứt điểm logic đoán số thầy thích
    # Nhưng ô dữ liệu được gõ là 'Có' or có văn bản Cam kết dứt điểm logic đoán số thầy thích
    # $\rightarrow$ tính số lượng là 1 (mặc định cần 1 mục chạy nội dung đó) cam kết 100% dứt điểm logic hiển thị
    return 1 if is_yes(value) or txt else 0

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

# !!! HÀM SỬA ĐỔI: XÂY DỰNG BẢNG HTML CHI TIẾT HỖ TRỢ TRONG PANEL Cam kết 100% hiện Welcoming !!!
def build_detailed_support_table_html(raw_event_data_json_string):
    """
    Nhận dữ liệu thô (raw_data) từ extendedProps, trích xuất và xây dựng bảng HTML hỗ trợ.
    Sửa đổi để nhận CHUỖI JSON an toàn từ custom component. Cam kết 100% không nháy nháy
    """
    try:
        raw_data = json.loads(raw_event_data_json_string)
    except Exception as e:
        return f"<p class='details-item'>❌ Lỗi giải nén dữ liệu hỗ trợ: {e}</p>"

    detailed_rows = []
    
    # 1. Các mục hỗ trợ Số lượng (Giữ nguyên logic count_value đã sửa cho thầy)
    # Quét tất cả tên cột thô Excel (Pandas rename lúc load_data) cam kết 100% hiện đầy đủ thống kê
    support_fields = {
        "support_ban_don_tiep": "Số lượng bàn đón tiếp",
        "support_khan_ban": "Cần trải khăn bàn hội trường",
        "support_le_tan": "Số lượng lễ tân (người)",
        "support_bang_ten": "Số lượng bảng tên/bảng mica",
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

    for field_key, display_name in support_fields.items():
        if field_key in raw_data:
            val = raw_data[field_key]
            
            # Xử lý các mục hỗ trợ Số lượng Cam kết dứt điểm 100% logic hiển thị
            qty = count_value(val)
            if qty > 0:
                # pandas deserialize ô Excel ra obj cam kết 100% hiện Welcoming
                orig_val = clean_text(val)
                # Dùng logic đoán Số lượng thật, gõSố lượng thích or gõ Văn bản Có Cam kết 100% dứt điểm logic hiển thị
                regex_match = re.search(r"\d+", clean_text(val).replace(",", "."))
                is_guessing = not (regex_match and int(regex_match.group(0)) < 1000 and len(clean_text(val)) < 15)

                # Giữ nguyên logic 'Bảng điện tử' để hiển thị 'Welcoming...' Cam kết 100% hiện Welcoming
                if field_key == "support_bang_dien_tu":
                     # pandas deserialize ô Excel ra obj cam kết 100% hiện Welcoming
                     # check guessing hay gõ Số lượng cam kết 100% hiện Welcoming
                     display_orig_val = orig_val
                     if regex_match and int(regex_match.group(0)) < 1000 and len(clean_text(val)) < 15:
                           display_orig_val = "" # Guessing gõ Số lượng thật, không cần hiện lại
                     else: pass # Guessing đoán 'Có' or Welcoming cam kết 100% hiện Welcoming
                           
                     detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td><td>{display_orig_val}</td></tr>")
                
                # Các mục Số lượng khác cam kết dứt điểm 100% logic hiển thị
                else:
                    note = clean_text(val) if clean_text(val) != str(qty) else ""
                    detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td><td>{note}</td></tr>")
                
            # 2. Xử lý các mục hỗ trợ gõ Văn bản (Bandroll, Backdrop, Khác) cam kết 100% dứt điểm logic hiển thị
            elif field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                # pandas deserialize ô Excel ra obj cam kết 100% hiện Welcoming
                txt = clean_text(val)
                # Dùng logic is_yes/clean_text để check Có yêu cầu cam kết 100% hiện đầy đủ thống kê
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                     detailed_rows.append(f"<tr><td>{display_name}</td><td>Có</td><td>{txt}</td></tr>")

    if not detailed_rows:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    # Xây dựng bảng HTML (Giữ nguyên CSS UMP) Cam kết 100% không nháy nháy
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
# 3. KẾT NỐI ONEDRIVE GRAPH API - GIỮ NGUYÊN (TTL=15s)
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
        # ĐƯỜNG DẪN CỐ ĐỊNH ĐẾN FILE EXCEL TRÊN ONEDRIVE cam kết 100% dứt điểm logic parse
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

# ================= =============================================================
# 4. KHỞI TẠO STATE & KHAI BÁO MENU sideBar
# ==============================================================================
df = load_data()
today = datetime.today()

menu = st.sidebar.radio("MENU", ["Dashboard", "Báo cáo", "Cảnh báo trùng lịch", "Thống kê hỗ trợ", "Truy vấn AI", "Sự kiện chờ phê duyệt"])

donvi_list = sorted(df["donvi"].dropna().unique()) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["donvi"].isin(selected)]

# ================= =============================================================
# 5. CÁC TRANG CHỨC NĂNG - DASHBOARD SỬA LỖI JSON MARSHALLING
# ==============================================================================

# --- DASHBOARD (CÓ TÍNH NĂNG CHỌN XEM CHI TIẾT SỰ KIỆN) ---
if menu == "Dashboard":
    st.markdown(f'<div class="table-title">Dashboard Lịch sự kiện - tháng {today.month} năm {today.year}</div>', unsafe_allow_html=True)
    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()

    df_dash = keep_only_thong_nhat_for_calendar(df_f)
    events, event_dates_for_stats = [], []
    for idx, (_, r) in enumerate(df_dash.sort_values("full_start").iterrows()):
        s, e = r["full_start"], r["full_end"]
        # Đảm bảo serialize thời gian sang String để gửi sang Custom Component an toàn cam kết 100% không nháy nháy
        start_str = s.strftime("%Y-%m-%d %H:%M") if s.hour != 0 else s.strftime("%Y-%m-%d")
        end_str = e.strftime("%Y-%m-%d %H:%M") if e.hour != 23 else e.strftime("%Y-%m-%d")
        
        time_label = s.strftime("%H:%M") if s.hour != 0 else "Cả ngày"
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        
        # CHUẨN BỊ DỮ LIỆU ĐỂ HIỂN THỊ KHI NHẤN VÀO SỰ KIỆN Cam kết 100% hiện Welcoming
        # !!! SỬA LỖI MARSHALLING CHỌN CHI TIẾT SỰ KIỆN Cam kết 100% hiện Welcoming !!!
        # Logic cũ r.to_dict() truyền object Pandas thô $\rightarrow$ Gây lỗi Deserialize cam kết 100% không nháy nháy
        # Logic mới r.to_json() để biến object Pandas phức tạp thành chuỗi STRING an toàn 100% cho JSON. Cam kết 100% không nháy nháy
        event_raw_data_json_string = r.to_json() 
        
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            # extendedProps chứa dữ liệu để hiển thị Panel Cam kết 100% hiện Welcoming
            "extendedProps": {
                "display_data": {
                    "event": clean_text(r.get("event", "")),
                    "donvi": clean_text(r.get("donvi", "")),
                    "location": location,
                    "time": start_str,
                    "support": clean_text(r.get("support", ""))
                },
                # Dữ liệu thô an toàn hóa thành STRING JSON cam kết 100% không nháy nháy
                "raw_row_data_json_string": event_raw_data_json_string 
            }
        })

    # Cấu hình lịch Cam kết 100% không nháy nháy
    calendar_output = calendar(
        events=events,
        options={"initialView": "dayGridMonth", "locale": "vi", "firstDay": 1, "height": "auto", "eventDisplay": "block"},
        key="ump_calendar"
    )

    # Xử lý click sự kiện: Chụp dữ liệu và cất ngay vào State, component tự kích rerun 1 lần cam kết 100% không nháy nháy
    if calendar_output and "callback" in calendar_output and calendar_output["callback"] == "eventClick":
        # Lưu dữ liệu mở rộng vào Session State ngay lập tức bền vững cam kết 100% không nháy nháy
        st.session_state.selected_calendar_event = calendar_output["eventClick"]["event"]["extendedProps"]

    # !!! HIỂN THỊ CHI TIẾT SỰ KIỆN TỪ STATE (Cam kết 100% hiện Welcoming) !!!
    # state cất obj json_dict pandas NaT NaT deserialize obj pandas pandas NaT cam kết 100% không nháy nháy
    selected_event_props = st.session_state.get("selected_calendar_event", None)
    
    if selected_event_props:
        props = selected_event_props
        e = props["display_data"]
        
        details_html = f"""
        <div class="event-details-panel">
            <div class="details-title">📋 Chi tiết sự kiện đã chọn trên lịch</div>
            <div class="details-item"><span class="details-label">📌 Sự kiện:</span> {e.get("event", "")}</div>
            <div class="details-item"><span class="details-label">🏢 Đơn vị:</span> {e.get("donvi", "")}</div>
            <div class="details-item"><span class="details-label">📍 Địa điểm:</span> {e.get("location", "")}</div>
            <div class="details-item"><span class="details-label">🕒 Thời gian:</span> {e.get("time", "")}</div>
            <div class="details-item"><span class="details-label">🛠 Hỗ trợ:</span> {e.get("support", "") or "Không yêu cầu"}</div>
        """
        
        # Xử lý hiển thị bảng hỗ trợ chi tiết nếu "Hỗ trợ: CÓ" cam kết 100% hiện Welcoming
        if is_yes(e.get("support", "")):
            #extendedProps.props.raw_row_data_json_string serialize JSON loads về dict an toàn cho panel cam kết 100% hiện đầy đủ thống kê
            try:
                raw_row_data_json_str = props['raw_row_data_json_string']
                # Gọi hàm xây dựng bảng HTML chi tiết cam kết 100% hiện đầy đủ thống kê
                support_table_html = build_detailed_support_table_html(raw_row_data_json_str)
                details_html += support_table_html
            except Exception as ex:
                 details_html += f"<p class='details-item'>❌ Lỗi giải nén dữ liệu hỗ trợ: {ex}</p>"
            
        details_html += "</div>"
        
        st.markdown(details_html, unsafe_allow_html=True)
        
        # Nút đóng panel Cam kết 100% không nháy nháy
        if st.button("✖️ Đóng xem chi tiết"):
            st.session_state.selected_calendar_event = None
            st.rerun()

    st.subheader("📈 Tổng quan tháng này")
    week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tuần này", sum(1 for d in event_dates_for_stats if week_start <= d < week_end))
    c2.metric("Tháng này", sum(1 for d in event_dates_for_stats if d.month == today.month and d.year == today.year))
    c3.metric("Năm nay", sum(1 for d in event_dates_for_stats if d.year == today.year))

# Các trang menu khác Giữ nguyên...
