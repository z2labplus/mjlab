from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field("", description="响应消息")
    code: int = Field(200, description="业务状态码")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    request_id: Optional[str] = Field(None, description="请求ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "message": "操作成功",
                "code": 200,
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req_123456"
            }
        }

class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = Field(False, description="请求失败")
    data: None = Field(None, description="错误时数据为空")
    message: str = Field(..., description="错误消息")
    code: int = Field(..., description="错误代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    error_details: Optional[dict] = Field(None, description="详细错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "data": None,
                "message": "操作失败",
                "code": 400,
                "timestamp": "2024-01-01T00:00:00Z",
                "error_details": {
                    "field": "game_id",
                    "reason": "游戏不存在"
                }
            }
        } 