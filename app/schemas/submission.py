from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubmissionBase(BaseModel):
    submission_number: str = Field(..., max_length=100, description="提交编号")
    submission_date: date = Field(..., description="提交日期")
    submission_channel: Optional[str] = Field(None, max_length=50, description="提交渠道")
    submission_type: Optional[str] = Field(None, max_length=50, description="提交类型")
    applicant: Optional[str] = Field(None, max_length=200, description="申请人")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    official_fee_paid: int = Field(default=0, description="官费是否已缴")
    official_fee_amount: Optional[str] = Field(None, max_length=50, description="官费金额")
    attached_materials: Optional[str] = Field(None, description="附送材料")
    submission_notes: Optional[str] = Field(None, description="提交说明")
    tracking_number: Optional[str] = Field(None, max_length=100, description="跟踪号")
    is_duplicate: int = Field(default=0, description="是否重复提交")
    duplicate_reason: Optional[str] = Field(None, max_length=500, description="重复原因")
    trademark_id: int = Field(..., description="商标ID")
    submitted_by_id: Optional[int] = Field(None, description="提交人ID")


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(SubmissionBase):
    submission_number: Optional[str] = Field(None, max_length=100)
    submission_date: Optional[date] = Field(None)
    trademark_id: Optional[int] = Field(None)


class SubmissionResponse(SubmissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
