from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class AgencyBase(BaseModel):
    entrustment_number: str = Field(..., max_length=50, description="委托编号")
    entrustment_date: Optional[date] = Field(None, description="委托日期")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    service_scope: Optional[str] = Field(None, description="服务范围")
    is_active: bool = Field(default=True, description="是否有效")
    remarks: Optional[str] = Field(None, description="备注")
    customer_id: int = Field(..., description="客户ID")
    trademark_id: int = Field(..., description="商标ID")


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(AgencyBase):
    entrustment_number: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[int] = Field(None)
    trademark_id: Optional[int] = Field(None)


class AgencyResponse(AgencyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
