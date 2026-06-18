from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class FeeBase(BaseModel):
    fee_type: str = Field(..., description="费用类型: official/service/total")
    amount: Decimal = Field(..., max_digits=12, decimal_places=2, description="金额")
    currency: str = Field(default="CNY", max_length=10, description="币种")
    payment_deadline: Optional[date] = Field(None, description="付款期限")
    payment_date: Optional[date] = Field(None, description="付款日期")
    payment_method: Optional[str] = Field(None, max_length=50, description="付款方式")
    transaction_id: Optional[str] = Field(None, max_length=100, description="交易流水号")
    status: str = Field(default="unpaid", description="状态")
    is_confirmed: bool = Field(default=False, description="是否已确认")
    confirmed_at: Optional[date] = Field(None, description="确认日期")
    remarks: Optional[str] = Field(None, description="备注")
    trademark_id: int = Field(..., description="商标ID")
    confirmed_by_id: Optional[int] = Field(None, description="确认人ID")


class FeeCreate(FeeBase):
    pass


class FeeUpdate(FeeBase):
    fee_type: Optional[str] = Field(None)
    amount: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    trademark_id: Optional[int] = Field(None)


class FeeResponse(FeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
