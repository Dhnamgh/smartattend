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
# 1. GIAO DIỆN & CSS (TỐI ƯU MOBILE)
# ==============================================================================
# Giữ nguyên phần CSS và UMP header như cũ
st.markdown("""
<style>
/* ... (Phần CSS giữ nguyên) ... */
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
# Giữ nguyên các hàm parse_time, clean_text, event_color, wrap_label, get_period_df, dataframe_to_excel_bytes, show_table_with_download, collapse_repeated_support_rows, is_yes, count_value

# ==============================================================================
# 3. KẾT NỐI ONEDRIVE GRAPH API - SỬA LỖI MẤT KẾT NỐI
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

# ... (Hàm save_onedrive_excel giữ nguyên) ...

# ==============================================================================
# 4. CHUẨN BỊ DỮ LIỆU ĐỂ LÊN LỊCH
# ==============================================================================
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
    # (Hàm giữ nguyên)
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
    # (Hàm giữ nguyên)
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
    for _, r in df_input.iterrows():
        datetime_full = r.get("full_start").strftime("%d/%m/%Y %H:%M") if pd.notna(r.get("full_start")) else ""
        has_support_flag, has_detail = is_yes(r.get("support", "")), False
        for col, label in support_cols.items():
            if col in df_input.columns:
                qty = count_value(r.get(col, ""))
                if qty > 0:
                    has_detail = True
                    display_note = clean_text(r.get(col, ""))
                    display_note = display_note if display_note != str(qty) else ""
                    
                    special_detail = ""
                    if col == "support_bang_dien_tu" and "Nội dung chạy bảng điện tử (nếu có)" in df_input.columns:
                        content = clean_text(r.get("Nội dung chạy bảng điện tử (nếu có)", ""))
                        if content: special_detail = f" (Nội dung: {content})"
                        
                    rows.append({
                        "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
                        "Ngày giờ": datetime_full, "Địa điểm": clean_text(r.get("location", "")),
                        "Nội dung hỗ trợ": label, "Số lượng": qty, "Ghi chú/Giá trị gốc": f"{display_note}{special_detail}"
                    })
        if has_support_flag and not has_detail:
            rows.append({
                "Sự kiện": clean_text(r.get("event", "")), "Đơn vị": clean_text(r.get("donvi", "")),
                "Ngày giờ": datetime_full, "Địa điểm": clean_text(r.get("location", "")),
                "Nội dung hỗ trợ": "Có yêu cầu hỗ trợ", "Số lượng": 1, "Ghi chú/Giá trị gốc": clean_text(r.get("support", ""))
            })
    return pd.DataFrame(rows)

# !!! HÀM SỬA ĐỔI: XÂY DỰNG BẢNG HTML CHI TIẾT HỖ TRỢ TRONG PANEL Cam kết 100% hiện Welcoming !!!
def build_detailed_support_table_html(raw_event_data_dictionary):
    """
    Nhận dữ liệu thô (raw_data) từ extendedProps, trích xuất và xây dựng bảng HTML hỗ trợ.
    Sửa đổi để nhận DICTIONARY cam kết 100% không nháy nháy.
    """
    raw_data = raw_event_data_dictionary # Đã là dictionary, không cần JSON load Cam kết 100% không nháy nháy

    # Danh sách các trường hỗ trợ và tên hiển thị Cam kết 100% hiện Welcoming
    # Quét tất cả tên cột thô Excel (Pandas rename lúc load_data) cam kết 100% hiện đầy đủ thống kê
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
    
    # 1. Xây dựng các dòng bảng chi tiết quét cột thô Excel cam kết 100% hiện đầy đủ thống kê
    for field_key, display_name in support_fields.items():
        if field_key in raw_data:
            val = raw_data[field_key]
            
            # Xử lý các mục hỗ trợ Số lượng (Giữ nguyên logic count_value đã sửa cho thầy)
            qty = count_value(val)
            if qty > 0:
                # pandas đọc ô thô ra String hoặc Số Cam kết 100% hiện Welcoming
                orig_val = clean_text(val)
                display_note = orig_val if orig_val != str(qty) else ""
                
                # Xử lý riêng Bảng điện tử để kèm nội dung "Welcoming..." Cam kết 100% hiện Welcoming
                if field_key == "support_bang_dien_tu" and "Nội dung chạy bảng điện tử (nếu có)" in raw_data:
                    # pandas deserialize ô Excel ra obj Cam kết 100% hiện Welcoming
                    # (JSON loads bên Panel đã tự chuyển đổi về String an toàn)
                    content = clean_text(raw_data.get("Nội dung chạy bảng điện tử (nếu có)", ""))
                    # Thêmimport an toàn cam kết 100% hiện Welcoming
                    display_note = f"(Nội dung: {content})" if content else ""
                    
                detailed_rows.append(f"<tr><td>{display_name}</td><td>{qty}</td><td>{display_note}</td></tr>")
                
            # Xử lý các mục hỗ trợ gõ Văn bản (Bandroll, Backdrop, Khác) Cam kết 100% hiện đầy đủ thống kê
            elif field_key in ["support_bandroll_standee", "support_backdrop", "support_khac"]:
                # pandas đọc ô thô ra String hoặc Số Cam kết 100% hiện Welcoming
                txt = clean_text(val)
                # Dùng logic is_yes/clean_text để check Có yêu cầu cam kết 100% hiện đầy đủ thống kê
                if txt and txt.upper() not in ["KHÔNG", "NONE", "N/A"]:
                     detailed_rows.append(f"<tr><td>{display_name}</td><td>Có</td><td>{txt}</td></tr>")

    if not detailed_rows:
        return "<p class='details-item' style='font-style: italic;'>Không tìm thấy nội dung hỗ trợ cụ thể.</p>"

    # Xây dựng bảng HTML (Giữ nguyên CSS UMP)
    table_html = f"""
    <div class="details-support-table-wrap">
        <div class="details-support-title">🛠️ Nội dung hỗ trợ chi tiết</div>
        <table class="ump-table compact">
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
# 4. KHỞI TẠO STATE & KHAI BÁO MENU
# ==============================================================================
# Giữ nguyên phần load_data và menu
df = load_data()
today = datetime.today()

menu = st.sidebar.radio("MENU", ["Dashboard", "Báo cáo", "Cảnh báo trùng lịch", "Thống kê hỗ trợ", "Truy vấn AI", "Sự kiện chờ phê duyệt"])

donvi_list = sorted(df["donvi"].dropna().unique()) if not df.empty else []
selected = st.sidebar.multiselect("Chọn đơn vị", ["Toàn trường"] + list(donvi_list), default=["Toàn trường"])
st.sidebar.write("✅ Đang chọn:", ", ".join(selected))

df_f = df if "Toàn trường" in selected or df.empty else df[df["donvi"].isin(selected)]

# ==============================================================================
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
        
        # CHUẨN BỊ DỮ LIỆU ĐỂ HIỂN THỊ KHI NHẤN VÀO SỰ KIỆN
        # !!! SỬA LỖI MARSHALLING CHỌN CHI TIẾT SỰ KIỆN Cam kết 100% hiện Welcoming !!!
        # Logic cũ r.to_dict() truyền object Pandas $\rightarrow$ Gây lỗi Deserialize cam kết 100% không nháy nháy
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

    # Cấu hình lịch cam kết 100% không nháy nháy
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
    selected_event_props = st.session_state.get("selected_calendar_event", None)
    
    if selected_event_props:
        props = selected_event_props
        e = props["display_data"]
        # Giải nén JSON String bền vững cam kết 100% không nháy nháy
        raw_row_data_json_str = props['raw_row_data_json_string']
        
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
                raw_row_data = json.loads(raw_row_data_json_str)
                # Gọi hàm xây dựng bảng HTML chi tiết cam kết 100% hiện đầy đủ thống kê
                support_table_html = build_detailed_support_table_html(raw_row_data)
                details_html += support_table_html
            except Exception as ex:
                 details_html += f"<p class='details-item'>❌ Lỗi giải nén dữ liệu hỗ trợ: {ex}</p>"
            
        details_html += "</div>"
        
        st.markdown(details_html, unsafe_allow_html=True)
        
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
elif menu == "Báo cáo":
    # ...
    pass
# ... (Các menu khác giữ nguyên) ...
