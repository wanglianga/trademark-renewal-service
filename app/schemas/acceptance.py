from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class AcceptanceBase(BaseModel):
    receipt_number: str = Field(..., max_length=100, description="受理通知书编号")
    receipt_date: date = Field(..., description="受理通知书日期")
    official_file_number: Optional[str] = Field(None, max_length=100, description="官方文号")
    acceptance_date: Optional[date] = Field(None, description="受理日期")
    applicant: Optional[str] = Field(None, max_length=200, description="申请人")
    trademark_registration_number: Optional[str] = Field(None, max_length=50, description="商标注册号")
    trademark_name: Optional[str] = Field(None, max_length=200, description="商标名称")
    international_class: Optional[str] = Field(None, max_length=50, description="国际类别")
    receipt_content: Optional[str] = Field(None, description="通知内容")
    attached_documents: Optional[str] = Field(None, description="附文")
    deadline_for_correction: Optional[date] = Field(None, description="补正期限")
    delivery_method: Optional[str] = Field(None, max_length=50, description="送达方式")
    received_date: Optional[date] = Field(None, description="收到日期")
    processing_person: Optional[str] = Field(None, max_length=100, description="处理人")
    remarks: Optional[str] = Field(None, description="备注")
    has_correction_deadline: int = Field(default=0, description="是否有补正期限")
    is_correction_overdue: int = Field(default=0, description="补正是否逾期")
    trademark_id: int = Field(..., description="商标ID")


class AcceptanceCreate(AcceptanceBase):
    pass


class AcceptanceUpdate(AcceptanceBase):
    receipt_number: Optional[str] = Field(None, max_length=100)
    receipt_date: Optional[date] = Field(None)
    trademark_id: Optional[int] = Field(None)


class AcceptanceResponse(AcceptanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
