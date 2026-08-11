"""
Trang Data Management - Quản lý & Tải dữ liệu OGSM
Xử lý đẩy trực tiếp byte dữ liệu tệp Excel lên OneDrive qua Microsoft Graph API.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Data Management - Đại học Y Dược TP.HCM", layout="wide")

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

# DANH SÁCH KHỐI VÀ ĐƠN VỊ / BỘ MÔN CHUẨN
UNITS_BY_GROUP = {
    "Khối Phòng chức năng": [
        "P.HCTH", "P.QTGT", "P.TCCB", "P.CTSV", "P.KHCN", 
        "P.HTQT", "P.KHTC", "P.TTPC", "P.ĐTSĐH", "P.ĐTĐH", "P.ĐBCL"
    ],
    "Khối Trường / Khoa": [
        "TRƯỜNG Y", "T.DƯỢC", "T.ĐD-KTYH", "K.KHCB", "K.YHCT", "K.YTCC", "K.RHM"
    ],
    "Khối Bệnh viện / Phòng khám": [
        "BV ĐHYD", "PKCK RHM"
    ],
    "Khối Trung tâm": [
        "TT.KCCLXN", "TT.KHCN UMP", "TT.GDYH", "TT.CNTT", "TT.YSHPT", "TT.ĐTNLYT"
    ],
    "Đơn vị khác": [
        "TCYH", "THƯ VIỆN", "KTX"
    ],
    "Khối Bộ môn": [
        "BM.Toán", "BM.Lý", "BM.Sinh", "BM.Hóa", "BM.GDTC", "BM.LLCT", "BM.NN"
    ]
}

FILE_NAME_MAP = {
    "BM.Toán": "BM.Toán.xlsx", "BM.Lý": "BM.Lý.xlsx", "BM.Sinh": "BM.Sinh.xlsx",
    "BM.Hóa": "BM.Hóa.xlsx", "BM.GDTC": "BM.GDTC.xlsx", "BM.LLCT": "BM.LLCT.xlsx", "BM.NN": "BM.NN.xlsx",
    "BV ĐHYD": "BV ĐHYD.xlsx", "PKCK RHM": "PKCK RHM.xlsx",
    "P.HCTH": "P.HCTH.xlsx", "P.QTGT": "P.QTGT.xlsx", "P.TCCB": "P.TCCB.xlsx",
    "P.CTSV": "P.CTSV.xlsx", "P.KHCN": "P.KHCN.xlsx", "P.HTQT": "P.HTQT.xlsx",
    "P.KHTC": "P.KHTC.xlsx", "P.TTPC": "P.TTPC.xlsx", "P.ĐTSĐH": "P.ĐTSĐH.xlsx",
    "P.ĐTĐH": "P.ĐTĐH.xlsx", "P.ĐBCL": "P.ĐBCL.xlsx",
    "TRƯỜNG Y": "TRƯỜNG Y.xlsx", "T.DƯỢC": "T.DƯỢC.xlsx", "T.ĐD-KTYH": "T.ĐD-KTYH.xlsx",
    "K.KHCB": "K.KHCB.xlsx", "K.YHCT": "K.YHCT.xlsx", "K.YTCC": "K.YTCC.xlsx", "K.RHM": "K.RHM.xlsx",
    "TT.KCCLXN": "TT.KCCLXN.xlsx", "TT.KHCN UMP": "TT.KHCN UMP.xlsx", "TT.GDYH": "TT.GDYH.xlsx",
    "TT.CNTT": "TT.CNTT.xlsx", "TT.YSHPT": "TT.YSHPT.xlsx", "TT.ĐTNLYT": "TT.ĐTNLYT.xlsx",
    "TCYH": "TCYH.xlsx", "THƯ VIỆN": "THƯ VIỆN.xlsx", "KTX": "KTX.xlsx"
}

st.markdown('<div class="main-banner-blue">Quản Lý & Tải Dữ Liệu OGSM - Đại học Y Dược TP.HCM</div>', unsafe_allow_html=True)

try:
    from ogsm_service import OGSMService
    from excel_repository import ExcelOneDriveRepository

    service = OGSMService()

    # 1. Chọn Khối
    st.markdown('<div class="subsection-header-blue">1. Chọn Khối Đơn Vị / Bộ Môn</div>', unsafe_allow_html=True)
    selected_group = st.radio(
        "Chọn Khối:",
        options=list(UNITS_BY_GROUP.keys()),
        horizontal=True,
        label_visibility="collapsed",
        key="data_group_radio"
    )

    # 2. Chọn Đơn vị thuộc Khối
    st.markdown(f'<div class="subsection-header-blue">2. Chọn Đơn Vị / Bộ Môn Thuộc [{selected_group}]</div>', unsafe_allow_html=True)
    unit_options = UNITS_BY_GROUP[selected_group]
    
    selected_unit = st.radio(
        "Chọn Đơn vị / Bộ môn:",
        options=unit_options,
        horizontal=True,
        label_visibility="collapsed",
        key="data_unit_radio"
    )

    file_target_name = FILE_NAME_MAP.get(selected_unit, f"{selected_unit}.xlsx")

    st.markdown("---")

    col_upload, col_view = st.columns([1, 1])

    with col_upload:
        st.markdown(f'<div class="section-banner-blue">Tải Tệp Lên Cho: {selected_unit}</div>', unsafe_allow_html=True)
        st.write(f"Tệp sẽ được lưu trực tiếp lên OneDrive dưới tên: **`{file_target_name}`**")

        uploaded_file = st.file_uploader(
            f"Chọn tệp Excel (.xlsx) cho {selected_unit}:",
            type=["xlsx", "xls"],
            key="data_file_uploader"
        )

        if uploaded_file is not None:
            if st.button("🚀 Cập nhật tệp dữ liệu lên OneDrive", type="primary"):
                try:
                    # Kiểm tra đọc file dữ liệu
                    df_up = pd.read_excel(uploaded_file, engine="openpyxl")
                    
                    # Khởi tạo Repository lấy kết nối Graph Client
                    repo = getattr(service, "repository", None) or getattr(service, "repo", None) or ExcelOneDriveRepository()
                    
                    # Lấy byte nguyên bản của tệp
                    file_bytes = uploaded_file.getvalue()
                    data_folder_id = repo.config.onedrive.data_folder_id
                    
                    # Đẩy tệp trực tiếp lên OneDrive qua Graph API
                    repo.graph_client.upload_file_by_folder_id(data_folder_id, file_target_name, file_bytes)
                    
                    st.success(f"✅ Đã cập nhật tệp **`{file_target_name}`** thành công lên OneDrive!")
                    st.cache_data.clear()

                except Exception as ex:
                    st.error(f"❌ Lỗi xử lý tệp: {ex}")

    with col_view:
        st.markdown(f'<div class="section-banner-blue">Dữ Liệu Hiện Tại: {selected_unit}</div>', unsafe_allow_html=True)
        try:
            df_all = service.get_full_ogsm_data()
            if not df_all.empty:
                df_unit_curr = df_all[df_all["Source_File"].astype(str).str.contains(selected_unit, case=False, na=False)]
                if df_unit_curr.empty:
                    df_unit_curr = df_all[df_all["Unit_Code"] == selected_unit]

                if not df_unit_curr.empty:
                    st.dataframe(df_unit_curr, use_container_width=True, height=350)
                    
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df_unit_curr.to_excel(writer, index=False, sheet_name="OGSM")
                    
                    st.download_button(
                        label=f"📥 Tải tệp {selected_unit} (.xlsx) về máy",
                        data=buffer.getvalue(),
                        file_name=file_target_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info(f"Chưa có dữ liệu cho **{selected_unit}** trên hệ thống.")
            else:
                st.info("Chưa có dữ liệu nào trên hệ thống.")
        except Exception as e:
            st.error(f"Lỗi khi đọc dữ liệu đơn vị: {e}")

except Exception as e:
    st.error(f"Lỗi nạp trang Data Management: {e}")
