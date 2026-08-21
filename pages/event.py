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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO

st.set_page_config(page_title="APP QUẢN LÝ SỰ KIỆN UMP", page_icon="📅", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# 1. GIAO DIỆN & CSS (TỐI ƯU TOÀN DIỆN CHO MOBILE RESPONSIVE)
# ==============================================================================
st.markdown("""
<style>
/* CSS 3 Nút Menu điều hướng trên cùng (1 hàng ngang cố định trên mobile) */
.top-nav-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
    width: 100%;
    margin-bottom: 10px;
}
.top-nav-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px 2px;
    background-color: #1877F2;
    color: #FFFFFF !important;
    border-radius: 6px;
    text-decoration: none !important;
    font-size: 13px;
    font-weight: 600;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: background-color 0.2s ease;
}
.top-nav-btn:hover { background-color: #145dbf; }
.top-nav-btn.active {
    background-color: #0d47a1;
    outline: 2px solid #90caf9;
}

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
html, body { font-family: Arial, sans-serif; font-size: 18px; color: #111827; }
section[data-testid="stSidebar"] { width: 255px !important; min-width: 255px !important; max-width: 255px !important; }
section[data-testid="stSidebar"] * { font-size: 13px !important; }
.block-container { padding-top: 3.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }

div[data-baseweb="notification"] div, .stAlert p { font-size: 13px !important; line-height: 1.4 !important; }
h1, h2, h3, h4, h5, h6, .stSubheader, .plotly .gtitle,
div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3, div[data-testid="stMarkdownContainer"] h4 {
    font-size: 14px !important; font-weight: 700 !important;
}
div[role="radiogroup"] label, div[data-baseweb="radio"] label, .stRadio label, .stRadio div {
    font-size: 14px !important; font-weight: 600 !important;
}

.table-title { font-size: 16px; font-weight: 800; color: #020617; margin-top: 10px; margin-bottom: 8px; }
.ump-table-wrap { width: 100%; overflow-x: auto; margin-bottom: 10px; }
.ump-table-wrap.compact { width: fit-content; max-width: 100%; }

.ump-table { border-collapse: collapse; font-size: 14px; color: #020617 !important; background: white; width: 100%; }
.ump-table th { background: #f1f5f9; color: #020617 !important; font-weight: 800; border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; white-space: nowrap; }
.ump-table td { color: #020617 !important; font-weight: 600; border: 1px solid #cbd5e1; padding: 6px 8px; vertical-align: top; line-height: 1.35; }
.ump-table.compact th, .ump-table.compact td { white-space: nowrap; }
.ump-table tr:nth-child(even) td { background: #f8fafc; }

/* CSS Panel chi tiết sự kiện khi chọn */
.event-details-panel {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-top: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.details-title { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 10px; }
.details-item { font-size: 14px; color: #1e293b; margin-bottom: 5px; line-height: 1.4; }
.details-label { font-weight: 700; color: #020617; }
.details-support-title { font-size: 14px; font-weight: 700; color: #020617; margin-top: 12px; margin-bottom: 6px; }

.stButton>button { width: auto; font-size: 13px !important; }

/* TỐI ƯU MOBILE */
@media screen and (max-width: 768px) {
    html, body { font-size: 13px !important; }
    .block-container { padding: 4px !important; }
    section[data-testid="stSidebar"] { width: 85% !important; min-width: 250px !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label { width: 100% !important; min-width: 100% !important; }

    iframe { max-width: 100% !important; }
    .fc { font-size: 11px !important; }
    .fc .fc-toolbar {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 4px !important;
        margin: 4px 0 !important;
    }
    .fc .fc-toolbar-chunk { display: flex !important; justify-content: center !important; width: 100%; }
    .fc .fc-toolbar-title { font-size: 13px !important; font-weight: 700 !important; text-align: center !important; }
    .fc .fc-button { padding: 3px 8px !important; font-size: 11px !important; }
    .fc-col-header-cell-cushion { font-size: 10px !important; padding: 2px !important; }
    .fc-daygrid-day-number { font-size: 10px !important; padding: 1px 3px !important; }
    .fc-daygrid-event { margin: 1px 0 !important; }
    .fc-event-title { font-size: 9px !important; line-height: 1.1 !important; }

    .event-details-panel { padding: 10px !important; margin-top: 8px !important; }
    .details-title { font-size: 14px !important; }
    .details-item { font-size: 12px !important; margin-bottom: 3px !important; }
    .ump-table { font-size: 11px !important; }
    .ump-table th, .ump-table td { padding: 4px 5px !important; }
}
</style>

<!-- Thanh điều hướng 3 app trên 1 hàng -->
<div class="top-nav-grid">
    <a href="./" target="_self" class="top-nav-btn">Điểm danh</a>
    <a href="./event" target="_self" class="top-nav-btn active">Sự kiện</a>
    <a href="./ogsm" target="_self" class="top-nav-btn">OGSM</a>
</div>

<!-- Tiêu đề Cỡ chữ 16 -->
<div style="font-size: 16px; font-weight: 700; color: #1f2937; margin: 8px 0 22px 0; text-transform: uppercase; letter-spacing: 0.5px; display: block; clear: both;">
    APP QUẢN LÝ SỰ KIỆN UMP
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HÀM TRỢ GIÚP (HELPERS & EMAIL)
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

def send_notification_email(event_name, donvi, start_dt, location):
    try:
        cfg = st.secrets.get("email", {})
        if not cfg or "sender_email" not in cfg: return False
        admin_email = cfg.get("admin_email", "chuyendoiso@ump.edu.vn")
        msg = MIMEMultipart()
        msg['From'] = cfg["sender_email"]
        msg['To'] = admin_email
        msg['Subject'] = f"🔔 [UMP EVENT] Yêu cầu phê duyệt sự kiện mới: {event_name}"
        body = f"""
        Kính gửi Quản trị viên,

        Hệ thống vừa ghi nhận một sự kiện mới cần phê duyệt:
        - Tên sự kiện: {event_name}
        - Đơn vị tổ chức: {donvi}
        - Thời gian: {start_dt.strftime('%d/%m/%Y %H:%M')}
        - Địa điểm: {location}

        Vui lòng truy cập Phân hệ Phê duyệt trên ứng dụng UMP Event để xử lý.
        Trân trọng.
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server = smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"])
        server.starttls()
        server.login(cfg["sender_email"], cfg["sender_password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception: return False

# ==============================================================================
# 3. KẾT NỐI ONEDRIVE CỐ ĐỊNH /OGSM/EVENT/Danh_sach_su_kien.xlsx
# ==============================================================================
def get_azure_token():
    azure_cfg = st.secrets["azure_ogsm"]
    app = msal.ConfidentialClientApplication(
        client_id=azure_cfg["client_id"],
        client_credential=azure_cfg["client_secret"],
        authority=f"https://login.microsoftonline.com/{azure_cfg['tenant_id']}"
    )
    res = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return res.get("access_token")

def get_onedrive_file_url():
    onedrive_cfg = st.secrets["onedrive_ogsm"]
    drive_id = onedrive_cfg["drive_id"]
    return f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/OGSM/EVENT/Danh_sach_su_kien.xlsx:/content"

def read_onedrive_excel() -> pd.DataFrame:
    try:
        token = get_azure_token()
        url = get_onedrive_file_url()
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.read_excel(BytesIO(res.content))
        else:
            st.error(f"❌ Không tìm thấy file '/OGSM/EVENT/Danh_sach_su_kien.xlsx' trên OneDrive (Mã lỗi {res.status_code}).")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối OneDrive: {e}")
        return pd.DataFrame()

def save_onedrive_excel(df: pd.DataFrame) -> bool:
    try:
        token = get_azure_token()
        url = get_onedrive_file_url()
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
        elif res.status_code == 423:
            st.error("⚠️ File Excel đang mở trên trình duyệt/desktop nên bị khóa! Vui lòng ĐÓNG TAB EXCEL trên OneDrive, chờ 10 giây rồi thử lại.")
            return False
        else:
            st.error(f"❌ Lỗi ghi đè file OneDrive ({res.status_code}): {res.text}")
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
        "Cần gửi thư mời": "support_thu_moi", "Các yêu cầu khác (nếu có)": "support_khac",
        "Id": "item_id", "ID": "item_id", "Thời gian bắt đầu": "submitted_at", "Thời gian hoàn thành": "completed_at",
        "Người phụ trách": "nguoi_phu_trach", "Người đăng ký": "nguoi_dang_ky", "Email": "email",
        "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)": "approval_opinion"
    })

    df["start"] = df["start"].apply(parse_event_date)
    df["end"] = df["end"].apply(parse_event_date).fillna(df["start"])
    df = df.dropna(subset=["start"])

    for i in df.index:
        t = parse_time(df.at[i, "start_time"] if "start_time" in df.columns else None)
        if t and pd.notna(df.at[i, "start"]): df.at[i, "start"] = df.at[i, "start"].replace(hour=t[0], minute=t[1])
        t2 = parse_time(df.at[i, "end_time"] if "end_time" in df.columns else None)
        if t2 and pd.notna(df.at[i, "end"]): df.at[i, "end"] = df.at[i, "end"].replace(hour=t2[0], minute=t2[1])

    for col in ["item_id", "event", "donvi", "location", "support", "nguoi_phu_trach", "nguoi_dang_ky", "email", "approval_opinion"]:
        if col not in df.columns: df[col] = ""
        df[col] = df[col].apply(clean_text)
    return df

@st.cache_data(ttl=15)
def load_data():
    return process_raw_dataframe(read_onedrive_excel())

def load_data_no_cache():
    return process_raw_dataframe(read_onedrive_excel())

def approval_text_from_row(row):
    for c in row.index:
        c_norm = re.sub(r"\s+", " ", str(c)).strip()
        if ("Ý kiến" in c_norm and "Phòng Hành chính Tổng hợp" in c_norm) or c == "approval_opinion":
            val = clean_text(row.get(c, ""))
            if val and val.lower() not in ["nan", "none", "nat"]: return val
    return ""

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
        "support_le_tan": "Lễ tân", "support_bang_ten": "Bảng tên mica",
        "support_bia_ky_ket": "Bìa ký kết", "support_nuoc_uong": "Nước uống",
        "support_teabreak": "Teabreak", "support_hoa_ban": "Hoa để bàn",
        "support_hoa_buc": "Hoa bục phát biểu", "support_hoa_tang": "Hoa bó tặng",
        "support_qua_tang": "Quà tặng", "support_brochure": "Brochure",
        "support_khay_bung": "Khay bưng", "support_bandroll_standee": "Bandroll/standee",
        "support_backdrop": "Backdrop", "support_thu_moi": "Gửi thư mời", "support_khac": "Yêu cầu khác"
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
                        "Ngày giờ": r.get("start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("start")) else "",
                        "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": label,
                        "Số lượng": qty
                    })
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": r.get("event", ""), "Đơn vị": r.get("donvi", ""),
                "Ngày giờ": r.get("start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("start")) else "",
                "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ",
                "Số lượng": 1
            })
    return pd.DataFrame(rows)

def build_detailed_support_table_html(raw_data):
    support_fields = {
        "support_ban_don_tiep": "Số lượng bàn đón tiếp",
        "support_khan_ban": "Cần trải khăn bàn hội trường",
        "support_le_tan": "Số lượng lễ tân",
        "support_bang_ten": "Số lượng bảng tên mica",
        "support_bia_ky_ket": "Số lượng bìa ký kết",
        "support_nuoc_uong": "Số lượng nước uống",
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

if "selected_event_details" not in st.session_state:
    st.session_state.selected_event_details = None

if "reg_start_date" not in st.session_state: st.session_state.reg_start_date = today.date()
if "reg_end_date" not in st.session_state: st.session_state.reg_end_date = today.date()
if "reg_prev_start_date" not in st.session_state: st.session_state.reg_prev_start_date = st.session_state.reg_start_date

# Tính toán số lượng sự kiện chờ phê duyệt
num_pending = 0
if not df.empty:
    num_pending = len(df[df.apply(approval_text_from_row, axis=1) == ""])

phe_duyet_label = f"Phê duyệt 🔴 {num_pending}" if num_pending > 0 else "Phê duyệt"

menu_options = ["Dashboard", "Đăng ký", "Báo cáo", "Cảnh báo", "Hỗ trợ", "Truy vấn AI", phe_duyet_label, "Liên hệ"]
selected_menu = st.sidebar.radio("", menu_options, label_visibility="collapsed")

# Chuẩn hóa giá trị menu
menu = "Phê duyệt" if selected_menu.startswith("Phê duyệt") else selected_menu
if not df.empty and "donvi" in df.columns:
    df["donvi"] = df["donvi"].replace({"Khoa Y": "Trường Y"})
donvi_list = sorted(df["donvi"].dropna().unique()) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["donvi"].isin(selected)]

def enforce_menu_access(menu_name):
    if menu_name in ["Dashboard", "Liên hệ"]: return True
    pwd_key = "admin" if menu_name == "Phê duyệt" else "user"
    state_key = f"{pwd_key}_logged_in"
    if st.session_state.get(state_key, False): return True
    st.warning(f"Khu vực này yêu cầu mật khẩu {pwd_key.upper()}.")
    pwd = st.text_input("Nhập mật khẩu", type="password", key=f"{pwd_key}_pwd")
    if st.button("Đăng nhập", key=f"{pwd_key}_btn"):
        correct_pwd = st.secrets.get(pwd_key, {}).get("password", "")
        if pwd == correct_pwd and correct_pwd != "":
            st.session_state[state_key] = True
            st.rerun()
        else: st.error("Mật khẩu không chính xác!")
    return False

# ==============================================================================
# 5. CÁC TRANG CHỨC NĂNG
# ==============================================================================

# --- DASHBOARD ---
if menu == "Dashboard":
    try:
        fresh_df = load_data_no_cache()
        fresh_df = fresh_df if "Toàn trường" in selected or fresh_df.empty else fresh_df[fresh_df["donvi"].isin(selected)]
        df_dash = keep_only_thong_nhat_for_calendar(fresh_df)
    except Exception:
        df_dash = keep_only_thong_nhat_for_calendar(df_f)

    events, event_dates_for_stats = [], []
    
    # Vòng lặp tách sự kiện qua nhiều ngày
    for idx, (_, r) in enumerate(df_dash.sort_values("start").iterrows()):
        s, e = r["start"], r["end"]
        if pd.isna(s): continue
        if pd.isna(e): e = s
        
        has_time = not (s.hour == 0 and s.minute == 0 and e.hour == 0 and e.minute == 0)
        time_label = s.strftime("%H:%M") if has_time else "Cả ngày"
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")
        event_raw_data_json_string = r.to_json()
        
        cur_date = s.date()
        end_date = e.date()
        
        while cur_date <= end_date:
            if has_time:
                cur_s = datetime.combine(cur_date, s.time())
                cur_e = datetime.combine(cur_date, e.time())
                start_str = cur_s.strftime("%Y-%m-%d %H:%M")
                end_str = cur_e.strftime("%Y-%m-%d %H:%M")
                panel_time_label = f"{start_str} - {cur_e.strftime('%H:%M')}"
            else:
                start_str = cur_date.strftime("%Y-%m-%d")
                end_str = cur_date.strftime("%Y-%m-%d")
                panel_time_label = start_str
                
            events.append({
                "title": title, "start": start_str, "end": end_str,
                "backgroundColor": color, "borderColor": color, "textColor": "#111827",
                "extendedProps": {
                    "panel_event_title": clean_text(r.get("event", "")),
                    "panel_donvi": clean_text(r.get("donvi", "")),
                    "panel_location": location,
                    "panel_time_label": panel_time_label,
                    "panel_participants": clean_text(r.get("thanh_phan", "")),
                    "panel_support_text": clean_text(r.get("support", "")),
                    "raw_row_data_json_string": event_raw_data_json_string
                }
            })
            event_dates_for_stats.append(datetime.combine(cur_date, time(0, 0)))
            cur_date += timedelta(days=1)

    calendar_custom_css = """
        .fc-toolbar-title {
            text-transform: capitalize !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            color: #1f2937 !important;
        }
        .fc-col-header-cell-cushion {
            font-size: 13px !important;
            font-weight: 600 !important;
            text-transform: capitalize !important;
        }
    """

    calendar_output = calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "locale": "vi",
            "firstDay": 1,
            "height": "auto",
            "contentHeight": "auto",
            "aspectRatio": 1.1,
            "eventDisplay": "block",
            "displayEventTime": False,
            "headerToolbar": {"left": "prev,next", "center": "title", "right": "today"}
        },
        custom_css=calendar_custom_css,
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
        val_thanh_phan = clean_text(props.get("panel_participants", "")) or clean_text(raw_row_data.get("thanh_phan", ""))
        if val_thanh_phan:
            tp_display = val_thanh_phan.replace("\n", "<br>")
            details_html += f'<div class="details-item"><span class="details-label">👥 Thành phần:</span><br>{tp_display}</div>'
        if content_bang_dien_tu:
            details_html += f'<div class="details-item"><strong>Nội dung chạy bảng điện tử:</strong> <strong>{content_bang_dien_tu}</strong></div>'

        if is_yes(props['panel_support_text']):
            details_html += build_detailed_support_table_html(raw_row_data)
            
        details_html += "</div>"
        st.markdown(details_html, unsafe_allow_html=True)
        
        if st.button("✖️ Đóng xem chi tiết"):
            st.session_state.selected_event_details = None
            st.rerun()

    st.subheader("📈 Tổng quan")
    week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tuần", sum(1 for d in event_dates_for_stats if week_start <= d < week_end))
    c2.metric("Tháng", sum(1 for d in event_dates_for_stats if d.month == today.month and d.year == today.year))
    c3.metric("Năm", sum(1 for d in event_dates_for_stats if d.year == today.year))

# --- ĐĂNG KÝ ---
elif menu == "Đăng ký":
    if not enforce_menu_access(menu): st.stop()
    st.markdown('<div class="table-title">📝 Đăng ký sự kiện</div>', unsafe_allow_html=True)
    if "approval_msg" in st.session_state: st.info(st.session_state.pop("approval_msg"))

    dc1, dc2 = st.columns(2)
    with dc1:
        start_date = st.date_input("Ngày tổ chức", key="reg_start_date")
        session_opt = st.selectbox("Khung giờ tổ chức mặc định", ["Sáng (07:00 - 11:00)", "Chiều (13:00 - 17:00)", "Tùy chọn giờ"])
        if session_opt == "Sáng (07:00 - 11:00)": default_start, default_end = time(7, 0), time(11, 0)
        elif session_opt == "Chiều (13:00 - 17:00)": default_start, default_end = time(13, 0), time(17, 0)
        else: default_start, default_end = time(7, 0), time(11, 0)
        start_time = st.time_input("Giờ bắt đầu", value=default_start)
    with dc2:
        if st.session_state.reg_start_date != st.session_state.reg_prev_start_date:
            st.session_state.reg_end_date = st.session_state.reg_start_date
            st.session_state.reg_prev_start_date = st.session_state.reg_start_date
        end_date = st.date_input("Ngày kết thúc", key="reg_end_date")
        end_time = st.time_input("Giờ kết thúc", value=default_end)
    support_flag = st.selectbox("Có yêu cầu hỗ trợ?", ["KHÔNG", "CÓ"], key="reg_support_flag")

    with st.form("registration_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1: event_name, donvi = st.text_input("Tên sự kiện"), st.text_input("Đơn vị phụ trách/tổ chức")
        with f2: location, nguoi_phu_trach, nguoi_dang_ky, email = st.text_input("Địa điểm"), st.text_input("Người phụ trách"), st.text_input("Người đăng ký"), st.text_input("Email")
        # Thêm ô nhập Thành phần tham dự vào form
    thanh_phan = st.text_area(
        "Thành phần tham dự:",
        placeholder="Ví dụ:\n- Ban Giám hiệu ĐHYD\n- Trưởng, Phó trưởng các phòng chức năng...",
        height=100
    )
        support_ban_don_tiep, support_khan_ban, support_le_tan, support_bang_ten, support_bia_ky_ket, support_nuoc_uong, support_teabreak, support_hoa_ban, support_hoa_buc, support_hoa_tang, support_qua_tang, support_brochure, support_khay_bung, support_bandroll_standee, support_backdrop, support_bang_dien_tu, noi_dung_bang_dien_tu, support_thu_moi, support_khac = 0, "KHÔNG", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "", "", "KHÔNG", "", "KHÔNG", ""
        if support_flag == "CÓ":
            st.markdown('<div class="table-title">Nội dung hỗ trợ từ Phòng HCTH</div>', unsafe_allow_html=True)
            s1, s2, s3 = st.columns(3)
            with s1: 
                support_ban_don_tiep = st.number_input("Số lượng bàn đón tiếp", min_value=0, step=1)
                support_khan_ban = st.selectbox("Trải khăn bàn hội trường", ["KHÔNG", "CÓ"])
                support_le_tan = st.number_input("Số lượng lễ tân", min_value=0, step=1)
                support_bang_ten = st.number_input("Số lượng bảng tên", min_value=0, step=1)
                support_bia_ky_ket = st.number_input("Số lượng bìa ký kết", min_value=0, step=1)
                support_nuoc_uong = st.number_input("Số lượng nước uống", min_value=0, step=1)
            with s2: 
                support_teabreak = st.number_input("Số phần Teabreak", min_value=0, step=1)
                support_hoa_ban = st.number_input("Số lượng hoa để bàn", min_value=0, step=1)
                support_hoa_buc = st.number_input("Hoa bục phát biểu", min_value=0, step=1)
                support_hoa_tang = st.number_input("Số lượng hoa bó tặng", min_value=0, step=1)
                support_qua_tang = st.number_input("Số lượng quà tặng", min_value=0, step=1)
                support_brochure = st.number_input("Số lượng Brochure", min_value=0, step=1)
            with s3: 
                support_khay_bung = st.number_input("Số lượng khay bưng", min_value=0, step=1)
                support_bandroll_standee = st.text_input("Bandroll, standee print/install")
                support_backdrop = st.text_input("Backdrop print/install")
                support_bang_dien_tu = st.selectbox("Chạy bảng điện tử", ["KHÔNG", "CÓ"])
                noi_dung_bang_dien_tu = st.text_area("Nội dung chạy bảng điện tử (nếu có)")
                support_thu_moi = st.selectbox("Gửi thư mời", ["KHÔNG", "CÓ"])
                support_khac = st.text_area("Khác")

        submitted = st.form_submit_button("Gửi đăng ký")

    if submitted:
        if not event_name or not donvi or not location: st.error("Vui lòng nhập tối thiểu: Tên sự kiện, Đơn vị và Địa điểm.")
        else:
            with st.spinner("Đang lưu sự kiện..."):
                df_excel = read_onedrive_excel()
                if df_excel.empty: st.error("Không thể kết nối đọc file OneDrive!")
                else:
                    valid_ids = pd.to_numeric(df_excel["Id"], errors="coerce").dropna()
                    next_id = int(valid_ids.max() + 1) if not valid_ids.empty else 1
                    new_row = {col: None for col in df_excel.columns}
                    new_row["Id"], new_row["Thời gian bắt đầu"], new_row["Email"], new_row["Tên"], new_row["Đơn vị phụ trách/ tổ chức"], new_row["Tên sự kiện"], new_row["Ngày tổ chức"], new_row["Giờ bắt đầu"], new_row["Giờ kết thúc"], new_row["Ngày kết thúc"], new_row["Địa điểm tổ chức"], new_row["Thông tin người phụ trách"], new_row["Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp"] = next_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email, nguoi_dang_ky, donvi, event_name, start_date.strftime("%Y-%m-%d"), start_time.strftime("%H:%M"), end_time.strftime("%H:%M"), end_date.strftime("%Y-%m-%d"), location, nguoi_phu_trach, support_flag
                    
                    new_row["Số lượng bàn đón tiếp"], new_row["Cần trải khăn bàn hội trường"], new_row["Số lượng lễ tân"], new_row["Số lượng bảng tên (bảng mica)"], new_row["Số lượng bìa ký kết"], new_row["Số lượng nước uống"], new_row["Số phần Teabreak"], new_row["Số lượng hoa để bàn"], new_row["Số lượng hoa để bục phát biểu"], new_row["Số lượng hoa bó để tặng"], new_row["Số lượng quà tặng"], new_row["Số lượng Brochure"], new_row["Số lượng khay bưng"], new_row["Số lượng bandroll, standee cần in và thi công"], new_row["Số lượng Backdrop cần in và thi công"], new_row["Cần chạy bảng điện tử"], new_row["Nội dung chạy bảng điện tử (nếu có)"], new_row["Cần gửi thư mời"], new_row["Các yêu cầu khác (nếu có)"] = support_ban_don_tiep, support_khan_ban, support_le_tan, support_bang_ten, support_bia_ky_ket, support_nuoc_uong, support_teabreak, support_hoa_ban, support_hoa_buc, support_hoa_tang, support_qua_tang, support_brochure, support_khay_bung, support_bandroll_standee, support_backdrop, support_bang_dien_tu, noi_dung_bang_dien_tu, support_thu_moi, support_khac
                    
                    if save_onedrive_excel(pd.concat([df_excel, pd.DataFrame([new_row])], ignore_index=True)):
                        send_notification_email(event_name, donvi, datetime.combine(start_date, start_time), location)
                        st.session_state["approval_msg"] = f"🎉 Đăng ký thành công ID {next_id}! Đợi duyệt. Kết quả sẽ hiện trên Dashboard Lịch sau khi duyệt."
                        st.rerun()

# --- BÁO CÁO & CẢNH BÁO & HỖ TRỢ & TRUY VẤN AI ---
elif menu in ["Báo cáo", "Cảnh báo", "Hỗ trợ", "Truy vấn AI"]:
    if not enforce_menu_access(menu): st.stop()
    
    if menu == "Báo cáo":
        st.markdown('<div class="table-title">📊 Báo cáo</div>', unsafe_allow_html=True)
        report_period = st.radio("Kỳ báo cáo", ["Tuần", "Tháng", "Năm"], horizontal=True, label_visibility="collapsed")
        df_report, label, _, _ = get_period_df(df_f, report_period)
        if len(df_report) > 0:
            summary = df_report.groupby("donvi").size().reset_index(name="Sự kiện")
            summary["Đơn vị"] = summary["donvi"].apply(lambda x: wrap_label(x, 20))
            st.plotly_chart(px.bar(summary, x="Sự kiện", y="Đơn vị", text="Sự kiện", orientation="h"), use_container_width=True)
            table_r = summary[["donvi", "Sự kiện"]].rename(columns={"donvi": "Đơn vị"}).reset_index(drop=True)
            table_r.insert(0, "STT", table_r.index + 1)
            show_table_with_download(f"{label}", table_r, f"bc_{report_period}.xlsx", compact=True)
        else: st.info(f"Không có dữ liệu {label}.")
        
    elif menu == "Cảnh báo":
        st.markdown('<div class="table-title">⚠️ Cảnh báo trùng lịch</div>', unsafe_allow_html=True)
        period = st.radio("Cảnh báo", ["Tuần", "Tháng"], horizontal=True, label_visibility="collapsed")
        warn_df, label, _, _ = get_period_df(df_f, period)
        conf = []
        for i, j in [(i, j) for i in range(len(warn_df)) for j in range(i+1, len(warn_df))]:
            a, b = warn_df.iloc[i], warn_df.iloc[j]
            if a["start"] < b["end"] and b["start"] < a["end"]:
                conf.append({"Thời gian": a["start"].strftime("%d/%m/%Y %H:%M"), "Sự kiện 1": clean_text(a["event"]), "Sự kiện 2": clean_text(b["event"]), "Mức độ": "Trùng địa điểm" if clean_text(a["location"]).lower() == clean_text(b["location"]).lower() else "Trùng giờ"})
        if not conf: st.success(f"{label} không trùng lịch.")
        else: show_table_with_download(f"{label}", pd.DataFrame(conf), f"cb_{period}.xlsx", compact=True)
        
    elif menu == "Hỗ trợ":
        st.markdown('<div class="table-title">Hỗ trợ</div>', unsafe_allow_html=True)
        period = st.radio("Hỗ trợ", ["Tuần", "Tháng"], horizontal=True, label_visibility="collapsed")
        df_supp, label, _, _ = get_period_df(df_f, period)
        supp_t = build_support_table(df_supp)
        if not supp_t.empty: show_table_with_download(f"{label}", collapse_repeated_support_rows(supp_t), f"ht_{period}.xlsx", compact=True)
        else: st.info("Không yêu cầu hỗ trợ.")

    elif menu == "Truy vấn AI":
        st.markdown('<div class="table-title">🧠 Truy vấn AI</div>', unsafe_allow_html=True)
        q = st.text_input("Gõ câu hỏi (tuần/tháng/hỗ trợ):")
        if q:
            low = q.lower().strip()
            digits = "".join([c for c in low if c.isdigit()])
            
            if "tháng" in low and digits and 1 <= int(digits) <= 12:
                t_m = int(digits)
                df_m = df_f[pd.to_datetime(df_f["start"], errors="coerce").dt.month == t_m]
                show_table_with_download(f"KQ AI Tháng {t_m}", build_approval_summary_table(df_m), f"ai_thang_{t_m}.xlsx", compact=True)
            elif "tuần" in low or "tháng" in low:
                show_table_with_download("KQ AI", build_approval_summary_table(get_period_df(df_f, "Tuần" if "tuần" in low else "Tháng")[0]), "ai_sq.xlsx", compact=True)
            elif "hỗ trợ" in low or "ht" in low:
                show_table_with_download("KQ AI Hỗ trợ", collapse_repeated_support_rows(build_support_table(df_f)), "ai_ht.xlsx", compact=True)
            else:
                st.warning("Thử lại với: tháng 7, tuần, tháng, hỗ trợ")

# --- PHÊ DUYỆT ---
elif menu == "Phê duyệt":
    if not enforce_menu_access(menu): st.stop()
    st.markdown('<div class="table-title">📋 Phê duyệt sự kiện</div>', unsafe_allow_html=True)
    if "approval_msg" in st.session_state: st.success(st.session_state.pop("approval_msg"))
    approval_df = load_data_no_cache()
    
    if not approval_df.empty:
        pending_df = approval_df[approval_df.apply(approval_text_from_row, axis=1) == ""].sort_values("start")
        
        if len(pending_df) > 0:
            st.error(f"⚠️ {len(pending_df)} SỰ KIỆN ĐANG CHỜ PHÊ DUYỆT!")
            
            if st.button("✅ PHÊ DUYỆT TẤT CẢ", type="primary"):
                with st.spinner("Đang phê duyệt..."):
                    df_ex = read_onedrive_excel()
                    p_ids = pending_df["item_id"].astype(str).str.strip().tolist()
                    op = "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"
                    mask = df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False).isin(p_ids)
                    df_ex.loc[mask, op], df_ex.loc[mask, "Thời gian hoàn thành"] = "Thống nhất", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if save_onedrive_excel(df_ex): 
                        st.session_state["approval_msg"] = f"🎉 Đã phê duyệt {len(p_ids)} sự kiện! Cập nhật trên Dashboard Lịch."
                        st.rerun()

            show_table_with_download("Danh sách chờ phê duyệt", build_approval_summary_table(pending_df), "cho_duyet.xlsx", compact=True)
            st.markdown("---")
            choices = [f"{r.get('start').strftime('%d/%m/%Y %H:%M') if pd.notna(r.get('start')) else ''} - {r.get('event','')} (ID: {r.get('item_id','')})" for _, r in pending_df.iterrows()]
            selected = st.selectbox("Chọn sự kiện xử lý lẻ", choices)
            item_id = choices.index(selected)
            selected_row = pending_df.iloc[item_id]
            opinion = st.selectbox("Ý kiến quản lý", ["Thống nhất", "Chờ phản hồi", "Không thống nhất"])
            reason = st.text_area("Ghi chú/Lý do")
            if st.button("Duyệt sự kiện này"):
                id_s = str(selected_row["item_id"]).strip()
                with st.spinner("Đang cập nhật..."):
                    df_ex, ap_text, op = read_onedrive_excel(), opinion if not reason else f"{opinion}: {reason}", "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"
                    mask = (df_ex["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == id_s) | (pd.to_numeric(df_ex["Id"], errors="coerce") == pd.to_numeric(id_s, errors="coerce"))
                    if mask.any(): 
                        df_ex.loc[mask, op], df_ex.loc[mask, "Thời gian hoàn thành"] = ap_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if save_onedrive_excel(df_ex): 
                        st.session_state["approval_msg"] = f"🎉 Đã phê duyệt ID {id_s}: '{opinion}'. Xem trên Dashboard Lịch."
                        st.rerun()
        else: st.success("🎉 Không có sự kiện nào đang chờ phê duyệt.")

# --- LIÊN HỆ & BẢN QUYỀN ---
elif menu == "Liên hệ":
    st.markdown("""
### Phòng Hành chính Tổng hợp - Đại học Y Dược TP.HCM
217 Hồng Bàng, Phường Chợ Lớn, TP.HCM
(+84-28) 3855 8411 | hanhchinh@ump.edu.vn
""")
st.markdown("---")
st.markdown("Copyright © 2026 Bản quyền thuộc về Phòng Hành chính Tổng hợp, Đại học Y Dược Thành phố Hồ Chí Minh")
