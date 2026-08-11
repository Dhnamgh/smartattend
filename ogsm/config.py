"""
Configuration management for OGSM Portal.
Loads secrets securely from Streamlit secrets.
"""

import streamlit as st
from pydantic import BaseModel, Field, ValidationError


class AzureSettings(BaseModel):
    tenant_id: str = Field(..., description="Azure AD Tenant ID")
    client_id: str = Field(..., description="Azure AD Application (Client) ID")
    client_secret: str = Field(..., description="Azure AD Application Client Secret")


class OneDriveSettings(BaseModel):
    drive_id: str = Field(..., description="OneDrive/SharePoint Drive ID")
    
    ogsm_folder_id: str = Field(..., description="Root OGSM Folder ID")
    data_folder_id: str = Field(..., description="Data Folder ID")
    template_folder_id: str = Field(..., description="Template Folder ID")
    export_folder_id: str = Field(..., description="Export Folder ID")
    archive_folder_id: str = Field(..., description="Archive Folder ID")

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
    try:
        secrets = st.secrets

        azure_data = secrets.get("azure", {})
        onedrive_data = secrets.get("onedrive", {})

        config = AppConfig(
            azure=AzureSettings(
                tenant_id=azure_data["tenant_id"],
                client_id=azure_data["client_id"],
                client_secret=azure_data["client_secret"],
            ),
            onedrive=OneDriveSettings(
                drive_id=onedrive_data["drive_id"],
                ogsm_folder_id=onedrive_data["ogsm_folder_id"],
                data_folder_id=onedrive_data["data_folder_id"],
                template_folder_id=onedrive_data["template_folder_id"],
                export_folder_id=onedrive_data["export_folder_id"],
                archive_folder_id=onedrive_data["archive_folder_id"],
                data_path=onedrive_data["data_path"],
                template_path=onedrive_data["template_path"],
                export_path=onedrive_data["export_path"],
                archive_path=onedrive_data["archive_path"],
            ),
        )
        return config
    except KeyError as ke:
        raise RuntimeError(f"Thiếu khóa cấu hình bắt buộc trong st.secrets: {ke}") from ke
    except ValidationError as ve:
        raise RuntimeError(f"Cấu hình trong st.secrets không hợp lệ: {ve}") from ve
    except Exception as e:
        raise RuntimeError(f"Không thể tải hệ thống secrets: {e}") from e
