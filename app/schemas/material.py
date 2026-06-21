from datetime import datetime, date
from typing import Optional, List
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

    submitted_at: Optional[datetime] = Field(None, description="提交时间")
    handled_by: Optional[str] = Field(None, max_length=100, description="处理人")
    replaced_reason: Optional[str] = Field(None, description="被替换原因")
    replaced_by_version_id: Optional[int] = Field(None, description="被哪个版本替换")
    is_replaced: bool = Field(default=False, description="是否已被替换")
    replaced_at: Optional[datetime] = Field(None, description="被替换时间")

    correction_id: Optional[int] = Field(None, description="关联的补正记录ID")
    correction_type_required: Optional[str] = Field(None, max_length=100, description="官方要求补正的类型")

    customer_id: Optional[int] = Field(None, description="客户ID")
    trademark_id: Optional[int] = Field(None, description="商标ID")


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    material_type: Optional[str] = Field(None)
    file_name: Optional[str] = Field(None, max_length=255)
    file_path: Optional[str] = Field(None, max_length=500)
    is_current: Optional[bool] = Field(None)
    is_approved: Optional[bool] = Field(None)
    is_replaced: Optional[bool] = Field(None)


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
    replaced_previous: bool = False
    replaced_previous_version: Optional[int] = None
    replaced_reason_recorded: Optional[str] = None


class CorrectionMaterialUploadRequest(BaseModel):
    correction_id: int = Field(..., description="补正记录ID")
    correction_type_required: Optional[str] = Field(None, description="官方要求补正的类型：power_of_attorney/subject_qualification/category_description/chinese_translation/other")
    replaced_reason: Optional[str] = Field(None, description="替换上一版本的原因说明")
    handled_by: Optional[str] = Field(None, description="处理人")


class MaterialVersionHistoryItem(BaseModel):
    id: int
    version: int
    file_name: str
    material_type: str
    uploaded_by: Optional[str]
    handled_by: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]
    is_current: bool
    is_replaced: bool
    is_approved: bool
    replaced_reason: Optional[str]
    replaced_at: Optional[datetime]
    correction_id: Optional[int]
    correction_type_required: Optional[str]


class CorrectionMaterialSummary(BaseModel):
    correction_id: int
    correction_number: Optional[str]
    required_types: List[str]
    required_materials: List[str]
    uploaded_count: int
    total_versions: int
    current_versions: List[MaterialVersionHistoryItem]
    all_versions: List[MaterialVersionHistoryItem]
    missing_types: List[str]
    missing_materials: List[str]
