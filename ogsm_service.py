"""
OGSM Business Logic Service - Chuẩn kết nối ExcelOneDriveRepository
"""

import io
import pandas as pd
from typing import Optional, Dict, Any, List
from excel_repository import ExcelOneDriveRepository
from analytics_service import OGSMAnalyticsService
from logger import get_logger

logger = get_logger()


class OGSMService:

    def __init__(self, repo: Optional[ExcelOneDriveRepository] = None):
        self.repo = repo or ExcelOneDriveRepository()

    def get_full_ogsm_data(self) -> pd.DataFrame:
        """Đọc toàn bộ Master Dataframe từ các file Excel trên OneDrive."""
        try:
            return self.repo.fetch_master_dataframe()
        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu từ Repository OneDrive: {e}")
            return pd.DataFrame()

    def get_available_units(self) -> List[str]:
        """Lấy danh sách mã đơn vị hiện có."""
        df = self.get_full_ogsm_data()
        if "Unit_Code" in df.columns:
            return sorted(df["Unit_Code"].dropna().unique().tolist())
        return []

    def upload_unit_file(self, filename: str, file_bytes: bytes) -> bool:
        """Upload/Cập nhật file báo cáo Excel đơn vị lên OneDrive."""
        try:
            # 1. Đọc nội dung file từ bytes thành DataFrame
            df_unit = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            
            # 2. Gọi hàm ghi đè dữ liệu đơn vị của ExcelOneDriveRepository
            if hasattr(self.repo, "save_unit_dataframe"):
                return self.repo.save_unit_dataframe(filename, df_unit)
            elif hasattr(self.repo, "upload_file"):
                return self.repo.upload_file(filename, file_bytes)
            elif hasattr(self.repo, "save_unit_file"):
                return self.repo.save_unit_file(filename, file_bytes)
            else:
                logger.error("Repository không hỗ trợ phương thức lưu file.")
                return False
        except Exception as e:
            logger.error(f"Lỗi khi upload file {filename}: {e}")
            return False

    def update_measure_actual(self, measure_id: str, new_actual: float, status: str) -> bool:
        """Cập nhật kết quả thực hiện cho từng chỉ số KPI."""
        df_master = self.repo.fetch_master_dataframe()

        mask = df_master["Measure_ID"] == measure_id
        if not mask.any():
            logger.error(f"Measure ID {measure_id} không tồn tại trong các file đơn vị.")
            return False

        source_file = df_master.loc[mask, "Source_File"].iloc[0]
        df_unit = df_master[df_master["Source_File"] == source_file].copy()

        unit_mask = df_unit["Measure_ID"] == measure_id
        df_unit.loc[unit_mask, "Actual"] = new_actual
        df_unit.loc[unit_mask, "Status"] = status

        return self.repo.save_unit_dataframe(source_file, df_unit)

    def get_dashboard_summary(self, unit_filter: Optional[str] = None) -> Dict[str, Any]:
        """Tính toán tổng hợp số liệu cho Dashboard."""
        df = self.get_full_ogsm_data()
        if unit_filter and "Unit_Code" in df.columns:
            df = df[df["Unit_Code"] == unit_filter]
        return OGSMAnalyticsService.compute_summary_kpis(df)
