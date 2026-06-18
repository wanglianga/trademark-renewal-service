from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MaterialBase(BaseModel):
    material_type: str = Field(..., description="材料类型")
    version: int = Field(default=1, description="版本号")
    file_name: str = Field(..., max_length=255, description="文件名")
    file_path: str = Field(..., max_length=500, description="文件路径")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    file_hash: Optional[str] = Field(None, max_length=64, description="文件哈希")
    is_current: bool = Field(default=True, description="是否为当前版本")
    uploaded_by: Optional[str] = Field(None, max_length=100, description="上传人")
    description: Optional[str] = Field(None, description="描述")
    review_notes: Optional[str] = Field(None, description="审核意见")
    is_approved: bool = Field(default=False, description="是否已审核通过")
    approved_at: Optional[str] = Field(None, max_length=50, description="审核通过时间")
    customer_id: Optional[int] = Field(None, description="客户ID")
    trademark_id: Optional[int] = Field(None, description="商标ID")


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    material_type: Optional[str] = Field(None)
    file_name: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=500)


class MaterialResponse(MaterialBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaterialUploadResponse(BaseModel):
    success: bool
    material_id: int
    file_name: str
    file_path: str
    version: int
    message: str
