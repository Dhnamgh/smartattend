"""
Custom Exception Hierarchy for OGSM Portal.
"""


class OGSMBaseException(Exception):
    """Base exception for all domain-specific errors."""
    pass


class GraphAPIError(OGSMBaseException):
    """Raised when Microsoft Graph API calls fail after retries."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class DataValidationError(OGSMBaseException):
    """Raised when input Excel files or rows fail validation."""
    pass


class OneDriveFileNotFoundError(OGSMBaseException):
    """Raised when a required Excel file is missing in OneDrive."""
    pass
