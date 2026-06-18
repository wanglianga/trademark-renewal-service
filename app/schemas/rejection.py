from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class RejectionBase(BaseModel):
    rejection_number: Optional[str] = Field(None, max_length=100, description="驳回通知书编号")
    rejection_date: date = Field(..., description="驳回日期")
    rejection_reason: str = Field(..., description="核驳理由")
    rejection_basis: Optional[str] = Field(None, description="核驳依据")
    review_deadline: Optional[date] = Field(None, description="复审期限")
    is_reviewed: bool = Field(default=False, description="是否已复审")
    review_date: Optional[date] = Field(None, description="复审日期")
    review_result: Optional[str] = Field(None, max_length=100, description="复审结果")
    review_content: Optional[str] = Field(None, description="复审内容")
    review_applicant: Optional[str] = Field(None, max_length=200, description="复审申请人")
    is_rejected_final: bool = Field(default=False, description="是否最终驳回")
    appeal_path: Optional[str] = Field(None, max_length=100, description="上诉途径")
    appeal_deadline: Optional[date] = Field(None, description="上诉期限")
    appeal_status: str = Field(default="not_appealed", max_length=50, description="上诉状态")
    appeal_date: Optional[date] = Field(None, description="上诉日期")
    appeal_result: Optional[str] = Field(None, description="上诉结果")
    processing_notes: Optional[str] = Field(None, description="处理备注")
    trademark_id: int = Field(..., description="商标ID")


class RejectionCreate(RejectionBase):
    pass


class RejectionUpdate(RejectionBase):
    rejection_date: Optional[date] = Field(None)
    rejection_reason: Optional[str] = Field(None)
    trademark_id: Optional[int] = Field(None)


class RejectionResponse(RejectionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
