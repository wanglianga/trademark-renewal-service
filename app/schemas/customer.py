from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class CustomerBase(BaseModel):
    name: str = Field(..., max_length=200, description="客户名称")
    unified_social_credit_code: str = Field(..., max_length=50, description="统一社会信用代码")
    legal_representative: Optional[str] = Field(None, max_length=100, description="法定代表人")
    phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    email: Optional[EmailStr] = Field(None, max_length=200, description="电子邮箱")
    address: Optional[str] = Field(None, max_length=500, description="地址")
    industry: Optional[str] = Field(None, max_length=100, description="所属行业")
    remarks: Optional[str] = Field(None, description="备注")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    name: Optional[str] = Field(None, max_length=200)
    unified_social_credit_code: Optional[str] = Field(None, max_length=50)


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
