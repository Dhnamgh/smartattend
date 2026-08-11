"""
Microsoft Graph API Client powered by MSAL and Tenacity.
Supports listing files dynamically inside OneDrive folders.
"""

import io
from typing import Optional, Dict, Any, List
import requests
import msal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import AppConfig, load_config
from exceptions import GraphAPIError, OneDriveFileNotFoundError
from logger import get_logger

logger = get_logger()


class MicrosoftGraphClient:

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self._authority = f"https://login.microsoftonline.com/{self.config.azure.tenant_id}"
        self._scopes = ["https://graph.microsoft.com/.default"]
        self._msal_app = msal.ConfidentialClientApplication(
            client_id=self.config.azure.client_id,
            client_credential=self.config.azure.client_secret,
            authority=self._authority,
        )

    def _get_access_token(self) -> str:
        result = self._msal_app.acquire_token_for_client(scopes=self._scopes)
        if "access_token" in result:
            return result["access_token"]

        error_desc = result.get("error_description", "Unknown authentication error")
        logger.error(f"Authentication failed: {error_desc}")
        raise GraphAPIError(f"Failed to acquire MS Graph token: {error_desc}", status_code=401)

    def _get_headers(self) -> Dict[str, str]:
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, GraphAPIError)),
        reraise=True,
    )
    def list_files_in_folder_id(self, folder_id: str) -> List[Dict[str, Any]]:
        drive_id = self.config.onedrive.drive_id
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}/children"
        headers = self._get_headers()

        logger.info(f"Listing files in Folder ID: {folder_id}")
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"Graph list files error ({response.status_code}): {response.text}")
            raise GraphAPIError(f"Error listing files in folder {folder_id}", status_code=response.status_code)

        data = response.json()
        items = data.get("value", [])
        
        excel_files = [
            item for item in items 
            if "file" in item and item["name"].endswith(".xlsx") and not item["name"].startswith("~$")
        ]
        return excel_files

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, GraphAPIError)),
        reraise=True,
    )
    def download_file_by_folder_id(self, folder_id: str, file_name: str) -> bytes:
        drive_id = self.config.onedrive.drive_id
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}:/{file_name}:/content"
        headers = self._get_headers()

        logger.info(f"Downloading file '{file_name}' from Folder ID: {folder_id}")
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 404:
            raise OneDriveFileNotFoundError(f"File '{file_name}' not found in folder ID {folder_id}")

        if response.status_code not in (200, 302):
            logger.error(f"Graph download error ({response.status_code}): {response.text}")
            raise GraphAPIError(f"Error downloading file {file_name}", status_code=response.status_code)

        return response.content

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, GraphAPIError)),
        reraise=True,
    )
    def upload_file_by_folder_id(self, folder_id: str, file_name: str, content: bytes) -> Dict[str, Any]:
        drive_id = self.config.onedrive.drive_id
        url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{folder_id}:/{file_name}:/content"
        headers = self._get_headers()
        headers["Content-Type"] = "application/octet-stream"

        logger.info(f"Uploading file '{file_name}' to Folder ID: {folder_id} ({len(content)} bytes)")
        response = requests.put(url, headers=headers, data=content, timeout=60)

        if response.status_code not in (200, 201):
            logger.error(f"Graph upload error ({response.status_code}): {response.text}")
            raise GraphAPIError(f"Failed to upload file {file_name}", status_code=response.status_code)

        return response.json()
