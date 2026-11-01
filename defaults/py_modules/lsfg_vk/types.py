from typing import List, Optional, TypedDict


class InstallationResponse(TypedDict):
    success: bool
    message: str
    error: Optional[str]


class UninstallationResponse(InstallationResponse):
    removed_files: Optional[List[str]]
