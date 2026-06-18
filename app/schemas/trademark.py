from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class TrademarkBase(BaseModel):
    registration_number: str = Field(..., max_length=50, description="商标注册号")
    trademark_name: str = Field(..., max_length=200, description="商标名称")
    international_class: int = Field(..., description="国际类别")
    application_date: Optional[date] = Field(None, description="申请日期")
    registration_date: Optional[date] = Field(None, description="注册日期")
    expiry_date: date = Field(..., description="有效期截止日")
    grace_period_end: Optional[date] = Field(None, description="宽展期截止日")
    designated_countries: Optional[str] = Field(None, max_length=500, description="指定国家")
    status: str = Field(default="draft", description="状态")
    current_stage: Optional[str] = Field(None, max_length=100, description="当前阶段")
    notes: Optional[str] = Field(None, description="备注")
    customer_id: int = Field(..., description="客户ID")
    assigned_agent_id: Optional[int] = Field(None, description="分配的代理人ID")
    has_subject_change: int = Field(default=0, description="是否有主体变更")


class TrademarkCreate(TrademarkBase):
    pass


class TrademarkUpdate(TrademarkBase):
    registration_number: Optional[str] = Field(None, max_length=50)
    trademark_name: Optional[str] = Field(None, max_length=200)
    international_class: Optional[int] = Field(None)
    expiry_date: Optional[date] = Field(None)
    customer_id: Optional[int] = Field(None)


class TrademarkStatusUpdate(BaseModel):
    status: str = Field(..., description="新状态")
    notes: Optional[str] = Field(None, description="变更备注")


class TrademarkResponse(TrademarkBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_expiring_soon: Optional[bool] = None
    is_in_grace_period: Optional[bool] = None
    is_overdue: Optional[bool] = None

    class Config:
        from_attributes = True
