from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class DeviceInfo(BaseModel):
    os_version: str = Field(alias='osVersion')
    app_version: str = Field(alias='appVersion')
    device_model: str = Field(alias='deviceModel')
    timezone: str
    
    class Config:
        populate_by_name = True

class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(..., min_length=64, max_length=255)
    device_info: DeviceInfo

class DeviceRegisterResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None