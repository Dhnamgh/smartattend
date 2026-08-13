import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
h1, h2, h3, h4, h5, h6, .stSubheader, .fc-toolbar-title, .plotly .gtitle,
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

.ump-table { border-collapse: collapse; font-size: 15px; color: #020617 !important; background: white; }
.ump-table th { background: #f1f5f9; color: #020617 !important; font-weight: 900; border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; white-space: nowrap; }
.ump-table td { color: #020617 !important; font-weight: 650; border: 1px solid #cbd5e1; padding: 7px 10px; vertical-align: top; line-height: 1.35; }
.ump-table.compact th, .ump-table.compact td { white-space: nowrap; }
.ump-table tr:nth-child(even) td { background: #f8fafc; }

.ump-fixed-header {
    background: linear-gradient(90deg, #06145f, #0b2f8a); color: #ffffff; padding: 18px 24px; border-radius: 10px; margin: 0 0 22px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18); display: flex; flex-direction: column; justify-content: center;
}
.ump-fixed-header .ump-vn { font-size: 22px; font-weight: 800; text-transform: uppercase; }
.ump-fixed-header .ump-en { font-size: 13px; font-weight: 600; text-transform: uppercase; margin-top: 4px; opacity: .95; }
.ump-fixed-header .ump-app { font-size: 24px; font-weight: 800; margin-top: 14px; }
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
# 3. KẾT NỐI ONEDRIVE (CHUẨN HOÁ TÊN FILE VÀ BÁO LỖI)
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
    ogsm_id = onedrive_cfg["ogsm_folder_id"]
    # Tên file chuẩn 1 khoảng trắng khớp đúng OneDrive
    file_name = "QUẢN LÝ TỔNG HỢP SỰ KIỆN UMP (sample).xlsx"
    return f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{ogsm_id}:/EVENT/{file_name}:/content"

def read_onedrive_excel() -> pd.DataFrame:
    try:
        token = get_azure_token()
        url = get_onedrive_file_url()
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return pd.read_excel(BytesIO(res.content))
        else:
            st.error(f"❌ Lỗi đọc file OneDrive ({res.status_code}): {res.text}")
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

@st.cache_data(ttl=30)
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
                        "Ngày giờ": r.get("start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("start")) else "",
                        "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": label,
                        "Số lượng": qty, "Ghi chú/Giá trị gốc": clean_text(r.get(col, ""))
                    })
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": r.get("event", ""), "Đơn vị": r.get("donvi", ""),
                "Ngày giờ": r.get("start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("start")) else "",
                "Địa điểm": r.get("location", ""), "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ",
                "Số lượng": 1, "Ghi chú/Giá trị gốc": clean_text(r.get("support", ""))
            })
    return pd.DataFrame(rows)

# ==============================================================================
# 4. KHỞI TẠO STATE & KHAI BÁO MENU
# ==============================================================================
df = load_data()
today = datetime.today()

if "reg_start_date" not in st.session_state: st.session_state.reg_start_date = today.date()
if "reg_end_date" not in st.session_state: st.session_state.reg_end_date = today.date()
if "reg_prev_start_date" not in st.session_state: st.session_state.reg_prev_start_date = st.session_state.reg_start_date

menu = st.sidebar.radio("MENU", ["Dashboard", "Đăng ký", "Báo cáo", "Cảnh báo", "Hỗ trợ", "Truy vấn AI", "Phê duyệt", "Liên hệ"])

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
    if st.button("🔄 Làm mới dữ liệu lịch"):
        st.cache_data.clear()
        st.rerun()

    try:
        fresh_df = load_data_no_cache()
        fresh_df = fresh_df if "Toàn trường" in selected or fresh_df.empty else fresh_df[fresh_df["donvi"].isin(selected)]
        df_f = keep_only_thong_nhat_for_calendar(fresh_df)
    except Exception:
        df_f = keep_only_thong_nhat_for_calendar(df_f)

    events, event_dates_for_stats = [], []
    for idx, (_, r) in enumerate(df_f.sort_values("start").iterrows()):
        s, e = r["start"], r["end"]
        has_time = not (s.hour == 0 and s.minute == 0)
        start_str = s.strftime("%Y-%m-%d %H:%M") if has_time else s.strftime("%Y-%m-%d")
        end_str = e.strftime("%Y-%m-%d %H:%M") if has_time else e.strftime("%Y-%m-%d")
        time_label = s.strftime("%H:%M") if has_time else "Cả ngày"
        location = clean_text(r.get("location", ""))
        title = f"{time_label} - {r['event']}" + (f"\n📍 {location}" if location else "")
        color = event_color(idx, f"{r.get('event','')}-{s}-{location}")

        event_dates_for_stats.append(s)
        events.append({
            "title": title, "start": start_str, "end": end_str,
            "backgroundColor": color, "borderColor": color, "textColor": "#111827",
            "extendedProps": {"event": r.get("event", ""), "donvi": r.get("donvi", ""), "location": location, "time": start_str, "support": clean_text(r.get("support", ""))}
        })

    selected_event = calendar(
        events=events,
        options={"initialView": "dayGridMonth", "locale": "vi", "firstDay": 1, "height": "auto", "eventDisplay": "block", "displayEventTime": False}
    )

    if selected_event and "event" in selected_event:
        e = selected_event["event"]["extendedProps"]
        st.subheader("📋 Chi tiết sự kiện")
        st.write("📌", e.get("event", ""))
        st.write("🏢", e.get("donvi", ""))
        st.write("📍", e.get("location", ""))
        st.write("🕒", e.get("time", ""))
        st.write("🛠", e.get("support", ""))

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
    st.markdown('<div style="font-size:14px;font-weight:700;">📝 Đăng ký sự kiện</div>', unsafe_allow_html=True)
    
    dc1, dc2 = st.columns(2)
    with dc1:
        start_date = st.date_input("Ngày tổ chức", key="reg_start_date")
        start_time = st.time_input("Giờ bắt đầu", value=datetime.strptime("07:30", "%H:%M").time())
    with dc2:
        if st.session_state.reg_start_date != st.session_state.reg_prev_start_date:
            st.session_state.reg_end_date = st.session_state.reg_start_date
            st.session_state.reg_prev_start_date = st.session_state.reg_start_date
        end_date = st.date_input("Ngày kết thúc", key="reg_end_date")
        end_time = st.time_input("Giờ kết thúc", value=datetime.strptime("13:30", "%H:%M").time())

    support_flag = st.selectbox("Có yêu cầu hỗ trợ?", ["KHÔNG", "CÓ"], key="reg_support_flag")

    with st.form("registration_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            event_name = st.text_input("Tên sự kiện")
            donvi = st.text_input("Đơn vị phụ trách/tổ chức")
        with c2:
            location = st.text_input("Địa điểm tổ chức")
            nguoi_phu_trach = st.text_input("Người phụ trách")
            nguoi_dang_ky = st.text_input("Người đăng ký")
            email = st.text_input("Email")

        submitted = st.form_submit_button("Gửi đăng ký")

    if submitted:
        if not event_name or not donvi or not location:
            st.error("Vui lòng nhập tối thiểu: Tên sự kiện, Đơn vị và Địa điểm.")
        else:
            with st.spinner("Đang lưu sự kiện vào file Excel trên OneDrive..."):
                df_excel = read_onedrive_excel()
                
                if df_excel.empty:
                    st.error("Không thể kết nối đọc file Excel từ OneDrive!")
                else:
                    next_id = 1
                    if "Id" in df_excel.columns:
                        valid_ids = pd.to_numeric(df_excel["Id"], errors="coerce").dropna()
                        if not valid_ids.empty: next_id = int(valid_ids.max() + 1)

                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_row = {col: None for col in df_excel.columns}
                    
                    new_row["Id"] = next_id
                    new_row["Thời gian bắt đầu"] = now_str
                    new_row["Thời gian hoàn thành"] = ""
                    new_row["Email"] = email
                    new_row["Tên"] = nguoi_dang_ky
                    new_row["Đơn vị phụ trách/ tổ chức"] = donvi
                    new_row["Tên sự kiện"] = event_name
                    new_row["Ngày tổ chức"] = start_date.strftime("%Y-%m-%d")
                    new_row["Giờ bắt đầu"] = start_time.strftime("%H:%M")
                    new_row["Giờ kết thúc"] = end_time.strftime("%H:%M")
                    new_row["Ngày kết thúc"] = end_date.strftime("%Y-%m-%d")
                    new_row["Địa điểm tổ chức"] = location
                    new_row["Thông tin người phụ trách"] = nguoi_phu_trach
                    new_row["Một số ĐỀ XUẤT HỖ TRỢ từ phòng Hành chính Tổng hợp"] = support_flag

                    updated_df = pd.concat([df_excel, pd.DataFrame([new_row])], ignore_index=True)
                    if save_onedrive_excel(updated_df):
                        st.session_state["approval_msg"] = f"🎉 Đã đăng ký thành công sự kiện (ID: {next_id})!"
                        st.rerun()

# --- BÁO CÁO ---
elif menu == "Báo cáo":
    if not enforce_menu_access(menu): st.stop()
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

# --- CẢNH BÁO ---
elif menu == "Cảnh báo":
    if not enforce_menu_access(menu): st.stop()
    warning_period = st.radio("Chọn phạm vi cảnh báo", ["Tuần", "Tháng", "Năm"], index=0, horizontal=True)
    warn_df, period_label, _, _ = get_period_df(df_f, warning_period)
    
    conflicts = []
    for i in range(len(warn_df)):
        a = warn_df.iloc[i]
        for j in range(i + 1, len(warn_df)):
            b = warn_df.iloc[j]
            if a["start"] < b["end"] and b["start"] < a["end"]:
                same_loc = clean_text(a.get("location", "")).lower() == clean_text(b.get("location", "")).lower()
                conflicts.append({
                    "Thời gian": a["start"].strftime("%d/%m/%Y %H:%M"),
                    "Sự kiện 1": clean_text(a.get("event", "")), "Đơn vị 1": clean_text(a.get("donvi", "")),
                    "Sự kiện 2": clean_text(b.get("event", "")), "Đơn vị 2": clean_text(b.get("donvi", "")),
                    "Mức cảnh báo": "Trùng thời gian & địa điểm" if same_loc else "Trùng thời gian"
                })

    if not conflicts: st.success(f"{period_label} không có lịch trùng.")
    else: show_table_with_download(f"Danh sách trùng lịch - {period_label}", pd.DataFrame(conflicts), "canh_bao_trung_lich.xlsx")

# --- HỖ TRỢ ---
elif menu == "Hỗ trợ":
    if not enforce_menu_access(menu): st.stop()
    support_period = st.radio("Chọn kỳ thống kê hỗ trợ", ["Tuần", "Tháng", "Năm"], index=1, horizontal=True)
    df_supp, supp_label, _, _ = get_period_df(df_f, support_period)
    supp_table = build_support_table(df_supp)
    
    if len(supp_table) == 0: st.info("Không có thông tin cần hỗ trợ")
    else:
        display_supp = collapse_repeated_support_rows(supp_table)
        show_table_with_download(f"Bảng sự kiện cần hỗ trợ - {supp_label}", display_supp, f"ho_tro_{support_period.lower()}.xlsx")

# --- TRUY VẤN AI ---
elif menu == "Truy vấn AI":
    if not enforce_menu_access(menu): st.stop()
    q = st.text_input("Nhập câu hỏi (ví dụ: tuần, tháng, năm, hỗ trợ):")
    if q:
        q_low = q.lower()
        if "tuần" in q_low or "tháng" in q_low or "năm" in q_low:
            p = "Tuần" if "tuần" in q_low else ("Tháng" if "tháng" in q_low else "Năm")
            p_df, label, _, _ = get_period_df(df_f, p)
            show_table_with_download(f"Sự kiện {label}", build_approval_summary_table(p_df), f"su_kien_{p.lower()}.xlsx")
        elif "hỗ trợ" in q_low or "ho tro" in q_low:
            supp_df = build_support_table(df_f[df_f["start"].dt.year == today.year])
            show_table_with_download("Danh sách cần hỗ trợ", collapse_repeated_support_rows(supp_df), "can_ho_tro.xlsx")
        else: st.warning("Hãy nhập từ khóa: tuần, tháng, năm hoặc hỗ trợ")

# --- PHÊ DUYỆT (HIỂN THỊ THÔNG BÁO CHUẨN KHI RERUN) ---
elif menu == "Phê duyệt":
    if not enforce_menu_access(menu): st.stop()
    st.markdown('<div style="font-size:14px;font-weight:700;">📋 Phê duyệt sự kiện</div>', unsafe_allow_html=True)
    
    # Hiển thị thông báo lưu thành công sau khi trang reload
    if "approval_msg" in st.session_state:
        st.success(st.session_state.pop("approval_msg"))

    if st.button("🔄 Làm mới dữ liệu OneDrive"):
        st.cache_data.clear()
        st.rerun()

    approval_df = load_data_no_cache()
    
    if approval_df.empty:
        st.warning("Chưa có dữ liệu sự kiện nào từ OneDrive.")
    else:
        pending_df = approval_df[approval_df.apply(approval_text_from_row, axis=1) == ""].sort_values("start")

        if len(pending_df) == 0:
            st.success("Không có sự kiện nào đang chờ phê duyệt.")
        else:
            show_table_with_download("Danh sách chờ phê duyệt", build_approval_summary_table(pending_df), "cho_phe_duyet.xlsx")
            
            choices = [f"{r.get('start').strftime('%d/%m/%Y %H:%M') if pd.notna(r.get('start')) else ''} - {r.get('event','')} (ID: {r.get('item_id','')})" for _, r in pending_df.iterrows()]
            selected_label = st.selectbox("Chọn sự kiện xử lý", choices)
            selected_idx = choices.index(selected_label)
            selected_row = pending_df.iloc[selected_idx]

            opinion = st.selectbox("Ý kiến của đơn vị quản lý", ["Thống nhất", "Chờ phản hồi", "Không thống nhất"])
            reason = st.text_area("Ghi chú / Lý do")

            if st.button("Cập nhật phê duyệt"):
                item_id = str(selected_row.get("item_id", "")).strip()
                if not item_id:
                    st.error("Sự kiện này chưa có ID hợp lệ trong file Excel!")
                else:
                    with st.spinner("Đang cập nhật kết quả phê duyệt lên OneDrive..."):
                        df_excel = read_onedrive_excel()
                        
                        col_opinion = "Ý kiến của đơn vị quản lý\n (Phòng Hành chính Tổng hợp)"
                        if col_opinion not in df_excel.columns:
                            for c in df_excel.columns:
                                if "Ý kiến" in str(c) and "Phòng Hành chính Tổng hợp" in str(c):
                                    col_opinion = c
                                    break

                        approval_text = opinion if not reason else f"{opinion}: {reason}"
                        
                        # So sánh Id thông minh (xử lý cả kiểu Số và Chuỗi)
                        mask = (df_excel["Id"].astype(str).str.strip().str.replace(".0", "", regex=False) == item_id) | (pd.to_numeric(df_excel["Id"], errors="coerce") == pd.to_numeric(item_id, errors="coerce"))
                        
                        if mask.any():
                            df_excel.loc[mask, col_opinion] = approval_text
                            df_excel.loc[mask, "Thời gian hoàn thành"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            if save_onedrive_excel(df_excel):
                                st.session_state["approval_msg"] = f"🎉 Đã phê duyệt thành công sự kiện ID {item_id}: '{opinion}'!"
                                st.rerun()
                        else:
                            st.error(f"❌ Không tìm thấy Id {item_id} trong file Excel trên OneDrive!")

# --- LIÊN HỆ ---
elif menu == "Liên hệ":
    st.markdown("""
### Phòng Hành chính Tổng hợp - Đại học Y Dược TP.HCM
📍 217 Hồng Bàng, Phường Chợ Lớn, TP.HCM  
☎ (+84-28) 3855 8411 | 3853 7949 | 3855 5780  
📧 hanhchinh@ump.edu.vn
""")

st.markdown("---")
st.markdown("Copyright © 2026 Bản quyền thuộc về Phòng Hành chính Tổng hợp, Đại học Y Dược Thành phố Hồ Chí Minh")
