"""
Configuration management for OGSM Portal.
Loads secrets directly from Streamlit secrets.
"""

import streamlit as st
from pydantic import BaseModel, Field, ValidationError


class AzureSettings(BaseModel):
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Azure AD Application (Client) ID")
    client_secret: str = Field(..., description="Azure AD Application Client Secret")


class OneDriveSettings(BaseModel):
    drive_id: str = Field(..., description="OneDrive/SharePoint Drive ID")
    
    # Specific Folder IDs
    ogsm_folder_id: str = Field(..., description="Root OGSM Folder ID")
    data_folder_id: str = Field(..., description="Data Folder ID")
    template_folder_id: str = Field(..., description="Template Folder ID")
    export_folder_id: str = Field(..., description="Export Folder ID")
    archive_folder_id: str = Field(..., description="Archive Folder ID")

    # Folder Paths
    data_path: str = Field(..., description="Data Folder Path")
    template_path: str = Field(..., description="Template Folder Path")
    export_path: str = Field(..., description="Export Folder Path")
    archive_path: str = Field(..., description="Archive Folder Path")


class AppConfig(BaseModel):
    azure: AzureSettings
    onedrive: OneDriveSettings
    app_title: str = "OGSM Portal - Đại học Y Dược TP. Hồ Chí Minh"


@st.cache_resource
def load_config() -> AppConfig:
    """
    Loads and validates application settings directly from st.secrets without fallbacks.
    """
    try:
        secrets = st.secrets

        # Tự động nhận diện cả [azure_ogsm] lẫn [azure]
        azure_data = secrets.get("azure_ogsm") or secrets.get("azure")
        
        # Tự động nhận diện cả [onedrive_ogsm] lẫn [onedrive]
        onedrive_data = secrets.get("onedrive_ogsm") or secrets.get("onedrive")

        if not azure_data or not onedrive_data:
            raise KeyError("Cấu hình trong Streamlit Secrets thiếu mục [azure_ogsm] hoặc [onedrive_ogsm].")

        config = AppConfig(
            azure=AzureSettings(
                tenant_id=str(azure_data["tenant_id"]).strip(),
                client_id=str(azure_data["client_id"]).strip(),
                client_secret=str(azure_data["client_secret"]).strip(),
            ),
            onedrive=OneDriveSettings(
                drive_id=str(onedrive_data["drive_id"]).strip(),
                ogsm_folder_id=str(onedrive_data["ogsm_folder_id"]).strip(),
                data_folder_id=str(onedrive_data["data_folder_id"]).strip(),
                template_folder_id=str(onedrive_data["template_folder_id"]).strip(),
                export_folder_id=str(onedrive_data["export_folder_id"]).strip(),
                archive_folder_id=str(onedrive_data["archive_folder_id"]).strip(),
                data_path=str(onedrive_data["data_path"]).strip(),
                template_path=str(onedrive_data["template_path"]).strip(),
                export_path=str(onedrive_data["export_path"]).strip(),
                archive_path=str(onedrive_data["archive_path"]).strip(),
            ),
        )
        return config
    except KeyError as ke:
        raise RuntimeError(f"Lỗi thiếu khóa trong Streamlit Secrets: {ke}") from ke
    except ValidationError as ve:
        raise RuntimeError(f"Lỗi định dạng Secrets: {ve}") from ve
    except Exception as e:
        raise RuntimeError(f"Không thể nạp cấu hình hệ thống: {e}") from e
