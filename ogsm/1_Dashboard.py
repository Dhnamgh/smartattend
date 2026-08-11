"""
Trang Executive Dashboard - Đại học Y Dược TP.HCM
Cập nhật vị trí "Khối Bộ môn" nằm ở sau cùng trong danh sách chọn Khối.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import re
import unicodedata
import datetime
import streamlit as st

st.set_page_config(page_title="Dashboard OGSM - Đại học Y Dược TP.HCM", layout="wide")

# CSS giao diện
st.markdown("""
<style>
    [data-testid="stSidebarNav"] ul li a svg { display: none !important; }
    [data-testid="stSidebarNav"] ul li a {
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin: 3px 0px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    [data-testid="stSidebarNav"] ul li a:hover {
        background-color: #e7f3ff !important;
        color: #1877F2 !important;
        transform: translateX(4px);
    }
    [data-testid="stSidebarNav"] ul li a[aria-current="page"] {
        background-color: #1877F2 !important;
        color: #ffffff !important;
        box-shadow: 0 3px 8px rgba(24, 119, 242, 0.35) !important;
    }
    .main-banner-blue {
        display: inline-block;
        background: #1877F2;
        color: #ffffff !important;
        padding: 10px 24px;
        border-radius: 8px;
        font-size: 22px;
        font-weight: 700;
        box-shadow: 0 4px 10px rgba(24, 119, 242, 0.3);
        margin-bottom: 20px;
    }
    .section-banner-blue {
        display: inline-block;
        background-color: #1877F2;
        color: #ffffff !important;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 700;
        margin: 14px 0px 14px 0px;
        box-shadow: 0 2px 6px rgba(24, 119, 242, 0.25);
    }
    .subsection-header-blue {
        background-color: #ffffff;
        color: #1877F2;
        padding: 8px 14px;
        border-radius: 8px;
        border: 1px solid #e4e6eb;
        font-size: 15px;
        font-weight: 700;
        margin: 8px 0px 10px 0px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    div[data-testid="stRadio"] > div {
        background-color: #f0f2f5;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #e4e6eb;
    }
    div[data-testid="stRadio"] label {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        margin-right: 6px !important;
        font-weight: 600 !important;
        border: 1px solid #e4e6eb !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
    }
    div[data-testid="stRadio"] label:hover {
        background-color: #e7f3ff !important;
        color: #1877F2 !important;
        border-color: #1877F2 !important;
    }
</style>
""", unsafe_allow_html=True)


def get_ascii_key(text: str) -> str:
    """Rút gọn chuỗi thành ký tự A-Z0-9 thuần không dấu"""
    if not text:
        return ""
    s = unicodedata.normalize('NFD', str(text))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('đ', 'd').replace('Đ', 'D').upper()
    return re.sub(r'[^A-Z0-9]', '', s)


def classify_unit_row(row):
    """Phân loại chính xác 100% dựa trên ASCII Key"""
    src = str(row.get("Source_File", ""))
    unit = str(row.get("Unit_Code", ""))
    key = get_ascii_key(src) or get_ascii_key(unit)

    # 1. Khối Bộ môn
    if key.startswith("BM") or "BOMON" in key:
        if "TOAN" in key: return ("BM.Toán", "Khối Bộ môn")
        if "LY" in key and "LLCT" not in key: return ("BM.Lý", "Khối Bộ môn")
        if "SINH" in key: return ("BM.Sinh", "Khối Bộ môn")
        if "HOA" in key: return ("BM.Hóa", "Khối Bộ môn")
        if "GDTC" in key: return ("BM.GDTC", "Khối Bộ môn")
        if "LLCT" in key: return ("BM.LLCT", "Khối Bộ môn")
        if "NN" in key or "NGOAINGU" in key: return ("BM.NN", "Khối Bộ môn")
        return (unit if unit else src, "Khối Bộ môn")

    # 2. Bệnh viện & Phòng khám
    if "BVDHYD" in key or "BENHVIEN" in key or ("BV" in key and "DHYD" in key):
        return ("BV ĐHYD", "Khối Bệnh viện / Phòng khám")
    if "PKCK" in key or "PKRHM" in key:
        return ("PKCK RHM", "Khối Bệnh viện / Phòng khám")

    # 3. Khối Phòng chức năng
    if "HCTH" in key or "HANHCHINH" in key:
        return ("P.HCTH", "Khối Phòng chức năng")
    if "QTGT" in key: return ("P.QTGT", "Khối Phòng chức năng")
    if "TCCB" in key: return ("P.TCCB", "Khối Phòng chức năng")
    if "CTSV" in key: return ("P.CTSV", "Khối Phòng chức năng")
    if "HTQT" in key: return ("P.HTQT", "Khối Phòng chức năng")
    if "KHTC" in key: return ("P.KHTC", "Khối Phòng chức năng")
    if "TTPC" in key: return ("P.TTPC", "Khối Phòng chức năng")
    if "DTSDH" in key: return ("P.ĐTSĐH", "Khối Phòng chức năng")
    if "DTDH" in key: return ("P.ĐTĐH", "Khối Phòng chức năng")
    if "DBCL" in key: return ("P.ĐBCL", "Khối Phòng chức năng")
    if "PKHCN" in key or (key.startswith("P") and "KHCN" in key): return ("P.KHCN", "Khối Phòng chức năng")

    # 4. Khối Trung tâm
    if "KCCLXN" in key: return ("TT.KCCLXN", "Khối Trung tâm")
    if "TTKHCN" in key or "KHCNUMP" in key: return ("TT.KHCN UMP", "Khối Trung tâm")
    if "GDYH" in key and "TT" in key: return ("TT.GDYH", "Khối Trung tâm")
    if "CNTT" in key: return ("TT.CNTT", "Khối Trung tâm")
    if "YSHPT" in key: return ("TT.YSHPT", "Khối Trung tâm")
    if "DTNLYT" in key: return ("TT.ĐTNLYT", "Khối Trung tâm")

    # 5. Khối Trường / Khoa
    if "TRUONGY" in key or key == "Y": return ("TRƯỜNG Y", "Khối Trường / Khoa")
    if "DUOC" in key: return ("T.DƯỢC", "Khối Trường / Khoa")
    if "DDKT" in key or "DDKTYH" in key: return ("T.ĐĐ-KTYH", "Khối Trường / Khoa")
    if "KHCB" in key: return ("K.KHCB", "Khối Trường / Khoa")
    if "YHCT" in key: return ("K.YHCT", "Khối Trường / Khoa")
    if "YTCC" in key: return ("K.YTCC", "Khối Trường / Khoa")
    if "KRHM" in key or (key.startswith("K") and "RHM" in key): return ("K.RHM", "Khối Trường / Khoa")

    # 6. Đơn vị khác
    if "TCYH" in key: return ("TCYH", "Đơn vị khác")
    if "THUVIEN" in key: return ("THƯ VIỆN", "Đơn vị khác")
    if "KTX" in key: return ("KTX", "Đơn vị khác")

    return (src or unit, "Đơn vị khác")


try:
    from ogsm_service import OGSMService
    from analytics_service import OGSMAnalyticsService
    from metrics_cards import render_metrics_cards
    from charts import (
        create_status_donut_chart, 
        create_objective_progress_chart, 
        create_stacked_kpi_by_unit_chart,
        create_total_kpis_by_unit_chart,
        create_completion_rate_by_unit_chart
    )

    st.markdown('<div class="main-banner-blue">Tổng Quan Thực Hiện OGSM - Đại học Y Dược TP.HCM</div>', unsafe_allow_html=True)

    service = OGSMService()
    df_all = service.get_full_ogsm_data()

    if not df_all.empty:
        # Ánh xạ chuẩn hóa thông tin Đơn vị và Khối
        mapped_data = df_all.apply(classify_unit_row, axis=1)
        df_all["Unit_Code"] = [m[0] for m in mapped_data]
        df_all["Unit_Group"] = [m[1] for m in mapped_data]

        loaded_main = df_all[df_all["Unit_Group"] != "Khối Bộ môn"]["Unit_Code"].unique()
        loaded_bm = df_all[df_all["Unit_Group"] == "Khối Bộ môn"]["Unit_Code"].unique()
        
        if len(loaded_bm) > 0:
            st.caption(f"Đã nạp thành công **{len(loaded_main)} / 29 Đơn vị chính thức** và **{len(loaded_bm)} Bộ môn**.")
        else:
            st.caption(f"Đã nạp thành công **{len(loaded_main)} / 29 Đơn vị** vào hệ thống.")

        # DANH SÁCH KHỐI HÀNG NGANG (ĐÃ ĐẶT "Khối Bộ môn" Ở CUỐI)
        GROUPS_LIST = [
            "Tất cả đơn vị",
            "Khối Phòng chức năng",
            "Khối Trường / Khoa",
            "Khối Bệnh viện / Phòng khám",
            "Khối Trung tâm",
            "Đơn vị khác",
            "Khối Bộ môn"
        ]

        st.markdown('<div class="subsection-header-blue">Chọn Khối Đơn Vị Báo Cáo</div>', unsafe_allow_html=True)
        
        selected_group = st.radio(
            "Chọn Khối:",
            options=GROUPS_LIST,
            horizontal=True,
            label_visibility="collapsed",
            key="dash_main_group_radio"
        )

        selected_unit = "Tất cả đơn vị"

        if selected_group == "Tất cả đơn vị":
            selected_unit = "Tất Cả Đơn Vị (Toàn Trường)"
        else:
            df_group_available = df_all[df_all["Unit_Group"] == selected_group]
            available_units_real = sorted(list(df_group_available["Unit_Code"].unique()))
            
            if available_units_real:
                sub_selected = st.radio(
                    f"Chọn đơn vị thuộc [{selected_group}]:",
                    options=[f"Tất cả {selected_group}"] + available_units_real,
                    horizontal=True,
                    key="dash_sub_unit_radio"
                )
                if sub_selected != f"Tất cả {selected_group}":
                    selected_unit = sub_selected
                else:
                    selected_unit = f"GROUP:{selected_group}"
            else:
                st.info(f"Chưa có tệp dữ liệu nào thuộc {selected_group}.")
                selected_unit = f"GROUP:{selected_group}"

        # LỌC DỮ LIỆU BÁO CÁO
        df_filtered = df_all.copy()
        if selected_unit == "Tất Cả Đơn Vị (Toàn Trường)":
            # "Tất cả đơn vị" CHỈ bao gồm 29 Đơn vị chính thức (loại trừ Khối Bộ môn)
            df_filtered = df_all[df_all["Unit_Group"] != "Khối Bộ môn"]
            st.caption("Đại học Y Dược TP. Hồ Chí Minh - Báo Cáo Tổng Hợp Toàn Trường (29 Đơn Vị Chính Thức)")
        elif selected_unit.startswith("GROUP:"):
            g_name = selected_unit.replace("GROUP:", "")
            df_filtered = df_all[df_all["Unit_Group"] == g_name]
            if g_name == "Khối Bộ môn":
                st.caption("Báo Cáo Tổng Hợp: **Tất Cả Các Bộ Môn**")
            else:
                st.caption(f"Báo Cáo Tổng Hợp: **{g_name}**")
        else:
            df_filtered = df_all[df_all["Unit_Code"] == selected_unit]
            st.caption(f"Báo Cáo Tiến Độ Đơn Vị / Bộ Môn: **{selected_unit}**")

        kpis = OGSMAnalyticsService.compute_summary_kpis(df_filtered)
        render_metrics_cards(kpis)

        st.markdown("---")

        col_donut, col_obj = st.columns([0.8, 1.2])
        with col_donut:
            df_status = OGSMAnalyticsService.get_status_distribution(df_filtered)
            fig_donut = create_status_donut_chart(df_status)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_obj:
            fig_obj = create_objective_progress_chart(df_filtered)
            st.plotly_chart(fig_obj, use_container_width=True)

        st.markdown("---")

        fig_bar_all = create_stacked_kpi_by_unit_chart(df_filtered, current_year_only=False)
        st.plotly_chart(fig_bar_all, use_container_width=True)

        st.markdown("---")

        fig_bar_current = create_stacked_kpi_by_unit_chart(df_filtered, current_year_only=True)
        st.plotly_chart(fig_bar_current, use_container_width=True)

        st.markdown("---")

        st.markdown('<div class="section-banner-blue">Thống Kê Chi Tiết Số Lượng & Tỷ Lệ Hoàn Thành Theo Đơn Vị</div>', unsafe_allow_html=True)

        fig_total_kpis = create_total_kpis_by_unit_chart(df_filtered)
        st.plotly_chart(fig_total_kpis, use_container_width=True)

        st.markdown("---")

        fig_rate_current = create_completion_rate_by_unit_chart(df_filtered, current_year_only=True)
        st.plotly_chart(fig_rate_current, use_container_width=True)

        st.markdown("---")

        fig_rate_all = create_completion_rate_by_unit_chart(df_filtered, current_year_only=False)
        st.plotly_chart(fig_rate_all, use_container_width=True)

    else:
        st.warning("Không tìm thấy file dữ liệu đơn vị nào trong thư mục DATA trên OneDrive.")

except Exception as e:
    st.error(f"Lỗi nạp trang Dashboard: {e}")
