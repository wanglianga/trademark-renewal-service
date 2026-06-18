from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class ReminderBase(BaseModel):
    reminder_type: str = Field(..., max_length=50, description="提醒类型")
    reminder_date: date = Field(..., description="提醒日期")
    deadline_date: Optional[date] = Field(None, description="截止日期")
    days_remaining: Optional[int] = Field(None, description="剩余天数")
    title: str = Field(..., max_length=200, description="提醒标题")
    content: str = Field(..., description="提醒内容")
    recipient: Optional[str] = Field(None, max_length=200, description="接收人")
    recipient_email: Optional[EmailStr] = Field(None, max_length=200, description="接收人邮箱")
    recipient_phone: Optional[str] = Field(None, max_length=20, description="接收人电话")
    status: str = Field(default="pending", max_length=50, description="状态")
    sent_at: Optional[str] = Field(None, max_length=50, description="发送时间")
    acknowledged_at: Optional[str] = Field(None, max_length=50, description="确认时间")
    acknowledged_by: Optional[str] = Field(None, max_length=100, description="确认人")
    priority: int = Field(default=1, description="优先级")
    escalation_level: int = Field(default=1, description="升级级别")
    notes: Optional[str] = Field(None, description="备注")
    trademark_id: int = Field(..., description="商标ID")


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(ReminderBase):
    reminder_type: Optional[str] = Field(None, max_length=50)
    reminder_date: Optional[date] = Field(None)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None)
    trademark_id: Optional[int] = Field(None)


class ReminderResponse(ReminderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
