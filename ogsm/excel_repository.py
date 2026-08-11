"""
OpenPyXL and Pandas Excel Repository matching official 29 UMP Units + Test Departments (Bộ môn).
Đọc và ghi dữ liệu OGSM trực tiếp qua Microsoft Graph API.
"""

import io
import os
import re
import unicodedata
import pandas as pd
from typing import Optional, List
from graph_client import MicrosoftGraphClient
from base_repository import BaseOGSMRepository
from logger import get_logger
from config import load_config

logger = get_logger()

class ExcelOneDriveRepository(BaseOGSMRepository):

    REQUIRED_COLUMNS = [
        "Objective_ID", "Objective_Title", "Goal_ID", "Goal_Desc",
        "Strategy_ID", "Strategy_Desc", "Measure_ID", "Measure_Desc",
        "Unit", "Target", "Actual", "Owner", "Status"
    ]

    def __init__(self, graph_client: Optional[MicrosoftGraphClient] = None):
        self.graph_client = graph_client or MicrosoftGraphClient()
        self.config = load_config()

    def _clean_unit_code(self, file_name: str) -> str:
        """Chuẩn hóa tên file thành đúng Mã đơn vị / Bộ môn chuẩn."""
        file_name_nfc = unicodedata.normalize('NFC', str(file_name))
        base_name = os.path.splitext(file_name_nfc)[0].strip()
        base_clean = re.sub(r'\s+', ' ', base_name)
        
        # Ánh xạ chuẩn 7 Bộ môn thử nghiệm
        bm_mapping = {
            "BM.TOÁN": "BM.Toán", "BM.TOAN": "BM.Toán", "BM_TOAN": "BM.Toán",
            "BM.LÝ": "BM.Lý", "BM.LY": "BM.Lý", "BM_LY": "BM.Lý",
            "BM.SINH": "BM.Sinh", "BM_SINH": "BM.Sinh",
            "BM.HÓA": "BM.Hóa", "BM.HOA": "BM.Hóa", "BM_HOA": "BM.Hóa",
            "BM.GDTC": "BM.GDTC", "BM_GDTC": "BM.GDTC",
            "BM.LLCT": "BM.LLCT", "BM_LLCT": "BM.LLCT",
            "BM.NN": "BM.NN", "BM_NN": "BM.NN"
        }
        
        upper_clean = base_clean.upper()
        if upper_clean in bm_mapping:
            return bm_mapping[upper_clean]
        if upper_clean.startswith("BM.") or upper_clean.startswith("BM_"):
            return base_clean

        # Bảng ánh xạ linh hoạt 29 Đơn vị chính thức
        mapping = {
            # Khối Phòng chức năng
            "P.HCTH": "P.HCTH", "P. HCTH": "P.HCTH", "PHCTH": "P.HCTH", "P_HCTH": "P.HCTH",
            "P.QTGT": "P.QTGT", "P. QTGT": "P.QTGT", "P.QT": "P.QTGT", "PQTGT": "P.QTGT",
            "P.TCCB": "P.TCCB", "P. TCCB": "P.TCCB", "PTCCB": "P.TCCB",
            "P.CTSV": "P.CTSV", "P. CTSV": "P.CTSV", "PCTSV": "P.CTSV",
            "P.KHCN": "P.KHCN", "P. KHCN": "P.KHCN", "PKHCN": "P.KHCN",
            "P.HTQT": "P.HTQT", "P. HTQT": "P.HTQT", "PHTQT": "P.HTQT",
            "P.KHTC": "P.KHTC", "P. KHTC": "P.KHTC", "PKHTC": "P.KHTC",
            "P.TTPC": "P.TTPC", "P. TTPC": "P.TTPC", "PTTPC": "P.TTPC",
            "P.ĐTSĐH": "P.ĐTSĐH", "P. ĐTSĐH": "P.ĐTSĐH", "P.DTSDH": "P.ĐTSĐH", "PDTSDH": "P.ĐTSĐH",
            "P.ĐTĐH": "P.ĐTĐH", "P. ĐTĐH": "P.ĐTĐH", "P.DTDH": "P.ĐTĐH", "PDTDH": "P.ĐTĐH",
            "P.ĐBCL": "P.ĐBCL", "P. ĐBCL": "P.ĐBCL", "P.DBCL": "P.ĐBCL", "PDBCL": "P.ĐBCL",

            # Khối Trường / Khoa
            "TRƯỜNG Y": "TRƯỜNG Y", "TRUONG Y": "TRƯỜNG Y", "TRƯỜNGY": "TRƯỜNG Y",
            "T.DƯỢC": "T.DƯỢC", "T. DƯỢC": "T.DƯỢC", "T.DUOC": "T.DƯỢC", "K.DUOC": "T.DƯỢC",
            "T.ĐĐ-KTYH": "T.ĐĐ-KTYH", "T.ĐD-KTYH": "T.ĐĐ-KTYH", "T.DD-KTYH": "T.ĐĐ-KTYH", "T. ĐĐ-KTYH": "T.ĐĐ-KTYH",
            "K.KHCB": "K.KHCB", "K. KHCB": "K.KHCB", "KKHCB": "K.KHCB",
            "K.YHCT": "K.YHCT", "K. YHCT": "K.YHCT", "KYHCT": "K.YHCT",
            "K.YTCC": "K.YTCC", "K. YTCC": "K.YTCC", "KYTCC": "K.YTCC",
            "K.RHM": "K.RHM", "K. RHM": "K.RHM", "KRHM": "K.RHM",

            # Khối Trung tâm
            "TT.KCCLXN": "TT.KCCLXN", "TT. KCCLXN": "TT.KCCLXN", "TT.KCXN": "TT.KCCLXN", "TTKCCLXN": "TT.KCCLXN",
            "TT.KHCN UMP": "TT.KHCN UMP", "TT. KHCN UMP": "TT.KHCN UMP", "TT.KHCNUMP": "TT.KHCN UMP", "TT.KHCN": "TT.KHCN UMP", "TTKHCNUMP": "TT.KHCN UMP",
            "TT.GDYH": "TT.GDYH", "TT. GDYH": "TT.GDYH", "TTGDYH": "TT.GDYH",
            "TT.CNTT": "TT.CNTT", "TT. CNTT": "TT.CNTT", "TTCNTT": "TT.CNTT",
            "TT.YSHPT": "TT.YSHPT", "TT. YSHPT": "TT.YSHPT", "TTYSHPT": "TT.YSHPT",
            "TT.ĐTNLYT": "TT.ĐTNLYT", "TT. ĐTNLYT": "TT.ĐTNLYT", "TT.DTNLYT": "TT.ĐTNLYT", "TTDTNLYT": "TT.ĐTNLYT",

            # Khối Bệnh viện / Phòng khám
            "PKCK RHM": "PKCK RHM", "PKCK.RHM": "PKCK RHM", "PK.RHM": "PKCK RHM", "PKCKRHM": "PKCK RHM",
            "BV ĐHYD": "BV ĐHYD", "BV.ĐHYD": "BV ĐHYD", "BV. ĐHYD": "BV ĐHYD", "BVDHYD": "BV ĐHYD", "BV_ĐHYD": "BV ĐHYD", "BV DHYD": "BV ĐHYD", "BV.DHYD": "BV ĐHYD",

            # Đơn vị khác
            "TCYH": "TCYH", "TẠP CHÍ Y HỌC": "TCYH",
            "THƯ VIỆN": "THƯ VIỆN", "THU VIEN": "THƯ VIỆN", "TV": "THƯ VIỆN",
            "KTX": "KTX", "KÝ TÚC XÁ": "KTX"
        }
        
        return mapping.get(base_clean, base_clean)

    def _get_objective_id(self, obj_title: str) -> str:
        obj_lower = str(obj_title).lower()
        if "giáo dục" in obj_lower: return "O1"
        if "nghiên cứu" in obj_lower: return "O2"
        if "phục vụ cộng đồng" in obj_lower: return "O3"
        if "trí tuệ nhân tạo" in obj_lower or "ai" in obj_lower: return "O4"
        if "quản trị đại học" in obj_lower: return "O5"
        return "O1"

    def _get_goal_id_by_text(self, text: str) -> str:
        t = text.lower()
        if "kiểm định" in t or "1.1" in t: return "1.1"
        if "đối sánh" in t or "1.2" in t: return "1.2"
        if "chương trình quốc tế" in t or "trao đổi sinh viên" in t or "1.3" in t: return "1.3"
        if "nhóm nghiên cứu mạnh" in t or "2.1" in t: return "2.1"
        if "bài báo quốc tế" in t or "2.2" in t: return "2.2"
        if "chuyển giao kỹ thuật" in t or "tnhh 1 thành viên" in t or "2.3" in t: return "2.3"
        if "kiểu mẫu" in t or "3.1" in t: return "3.1"
        if "đào tạo liên tục" in t or "3.2" in t: return "3.2"
        if "một cổng" in t or "3.3" in t: return "3.3"
        if "20% số học phần" in t or "4.1" in t: return "4.1"
        if "50 đề tài" in t or "4.2" in t: return "4.2"
        if "hành chính và quản trị" in t or "4.3" in t: return "4.3"
        if "nguồn lực tài chính" in t or "10%/ năm" in t or "5.1" in t: return "5.1"
        if "văn hoá ump" in t or "5.2" in t: return "5.2"
        if "erp" in t or "chuyển đổi số" in t or "5.3" in t: return "5.3"
        return "OTHER_GOAL"

    def _transform_custom_excel(self, df: pd.DataFrame, unit_code: str) -> pd.DataFrame:
        df.columns = [unicodedata.normalize('NFC', str(c)).strip() for c in df.columns]

        def get_col_val(row_data, keywords, default=""):
            for col in df.columns:
                if any(kw.lower() in col.lower() for kw in keywords):
                    val = row_data.get(col)
                    if pd.notna(val):
                        return val
            return default

        rows = []
        for idx, row in df.iterrows():
            measure_desc = str(get_col_val(row, ["Measure (KPI)", "Measure", "KPI", "Chỉ số"], "")).strip()
            if not measure_desc or measure_desc == "nan":
                continue

            obj_title = str(get_col_val(row, ["Objects", "Mục tiêu chiến lược"], "Mục tiêu UMP")).strip()
            obj_id = self._get_objective_id(obj_title)

            goal_ump = str(get_col_val(row, ["Goals UMP", "Goals", "Mục tiêu cụ thể"], "")).strip()
            goal_desc = goal_ump if goal_ump and goal_ump != "nan" else obj_title
            strat_code = self._get_goal_id_by_text(goal_desc)

            target_yr = get_col_val(row, ["Năm đích", "Year"], 2029)

            stt = str(get_col_val(row, ["STT"], idx + 1)).strip()
            
            # Chuẩn hóa trạng thái Tiếng Việt
            status_raw = str(get_col_val(row, ["Trạng thái", "Status"], "Đang thực hiện")).strip()
            st_lower = status_raw.lower()
            if "progress" in st_lower or "đang" in st_lower:
                status = "Đang thực hiện"
            elif "hoàn thành" in st_lower or "complete" in st_lower or "done" in st_lower:
                status = "Hoàn thành"
            elif "chưa" in st_lower or "pending" in st_lower or "not due" in st_lower:
                status = "Chưa đến hạn"
            elif "không" in st_lower or "fail" in st_lower:
                status = "Không đạt"
            else:
                status = status_raw if status_raw != "nan" else "Đang thực hiện"

            actual_val = get_col_val(row, ["Tỷ lệ đạt (%)", "Tỷ lệ đạt", "Actual"], 0.0)
            try:
                actual_val = float(str(actual_val).replace("%", "").strip())
            except Exception:
                actual_val = 0.0

            target_val = 100.0
            val_2026 = get_col_val(row, ["2026"], None)
            if val_2026 is not None:
                try:
                    target_val = float(str(val_2026).replace("%", "").strip())
                except Exception:
                    target_val = 100.0

            rows.append({
                "Objective_ID": obj_id,
                "Objective_Title": obj_title,
                "Goal_ID": f"G_{strat_code}",
                "Goal_Desc": goal_desc,
                "Strategy_ID": f"S_{strat_code}",
                "Strategy_Desc": goal_desc,
                "Measure_ID": f"{unit_code}_M{stt}",
                "Measure_Desc": measure_desc,
                "Unit": "%",
                "Target": target_val,
                "Actual": actual_val,
                "Owner": unit_code,
                "Status": status,
                "Target_Year": target_yr if pd.notna(target_yr) else 2029
            })

        return pd.DataFrame(rows)

    def fetch_master_dataframe(self) -> pd.DataFrame:
        data_folder_id = self.config.onedrive.data_folder_id
        files = self.graph_client.list_files_in_folder_id(data_folder_id)
        if not files:
            return pd.DataFrame(columns=self.REQUIRED_COLUMNS + ["Unit_Code", "Source_File", "Target_Year"])

        aggregated_dfs: List[pd.DataFrame] = []

        for f in files:
            file_name = f["name"]
            unit_code = self._clean_unit_code(file_name)

            try:
                file_bytes = self.graph_client.download_file_by_folder_id(data_folder_id, file_name)
                buffer = io.BytesIO(file_bytes)
                df_raw = pd.read_excel(buffer, engine="openpyxl")

                cols_str = " ".join([str(c) for c in df_raw.columns]).lower()
                has_valid_header = any(k in cols_str for k in ["objects", "measure", "goals", "kpi"])

                if not has_valid_header:
                    header_row = 0
                    for r_idx in range(min(5, len(df_raw))):
                        row_vals = [str(v).lower() for v in df_raw.iloc[r_idx].values]
                        if any("objects" in v or "measure" in v or "goals" in v for v in row_vals):
                            header_row = r_idx + 1
                            break

                    if header_row > 0:
                        buffer.seek(0)
                        df_raw = pd.read_excel(buffer, engine="openpyxl", header=header_row)

                df_transformed = self._transform_custom_excel(df_raw, unit_code)

                if not df_transformed.empty:
                    df_transformed["Unit_Code"] = unit_code
                    df_transformed["Source_File"] = file_name
                    aggregated_dfs.append(df_transformed)

            except Exception as e:
                logger.error(f"Lỗi đọc file {file_name}: {e}")

        if not aggregated_dfs:
            return pd.DataFrame(columns=self.REQUIRED_COLUMNS + ["Unit_Code", "Source_File", "Target_Year"])

        return pd.concat(aggregated_dfs, ignore_index=True)

    def save_unit_dataframe(self, unit_file_name: str, df_unit: pd.DataFrame) -> bool:
        data_folder_id = self.config.onedrive.data_folder_id
        clean_df = df_unit.drop(columns=["Unit_Code", "Source_File", "Target_Year"], errors="ignore")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            clean_df.to_excel(writer, index=False, sheet_name="OGSM")

        buffer.seek(0)
        self.graph_client.upload_file_by_folder_id(data_folder_id, unit_file_name, buffer.read())
        return True

    def save_master_dataframe(self, df: pd.DataFrame) -> bool:
        raise NotImplementedError("Use save_unit_dataframe instead.")
