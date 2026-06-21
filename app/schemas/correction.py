from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CorrectionBase(BaseModel):
    correction_number: Optional[str] = Field(None, max_length=100, description="补正编号")
    correction_date: Optional[date] = Field(None, description="补正通知日期")
    correction_type: Optional[str] = Field(None, max_length=50, description="补正类型")
    correction_reason: str = Field(..., description="补正原因")
    correction_requirements: str = Field(..., description="补正要求")
    required_materials: Optional[str] = Field(None, description="要求补齐的材料类型列表（逗号分隔）：power_of_attorney/subject_qualification/category_description/chinese_translation/other")
    deadline: date = Field(..., description="补正期限")
    is_overdue: bool = Field(default=False, description="是否逾期")
    correction_status: str = Field(default="pending", max_length=50, description="补正状态")
    correction_content: Optional[str] = Field(None, description="补正内容")
    correction_materials: Optional[str] = Field(None, description="补正材料")
    corrector: Optional[str] = Field(None, max_length=100, description="补正人")
    correction_complete_date: Optional[date] = Field(None, description="补正完成日期")
    resubmission_date: Optional[date] = Field(None, description="重新提交日期")
    resubmission_number: Optional[str] = Field(None, max_length=100, description="重新提交编号")
    official_response: Optional[str] = Field(None, description="官方回复")
    correction_notes: Optional[str] = Field(None, description="补正备注")
    reminder_count: int = Field(default=0, description="提醒次数")
    last_reminder_date: Optional[date] = Field(None, description="最后提醒日期")
    trademark_id: int = Field(..., description="商标ID")


class CorrectionCreate(CorrectionBase):
    pass


class CorrectionUpdate(CorrectionBase):
    correction_reason: Optional[str] = Field(None)
    correction_requirements: Optional[str] = Field(None)
    deadline: Optional[date] = Field(None)
    trademark_id: Optional[int] = Field(None)


class CorrectionResponse(CorrectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
