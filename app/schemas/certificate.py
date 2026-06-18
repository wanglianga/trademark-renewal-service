from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class CertificateBase(BaseModel):
    certificate_number: str = Field(..., max_length=100, description="证书编号")
    certificate_date: date = Field(..., description="证书日期")
    issue_date: Optional[date] = Field(None, description="发证日期")
    expiry_date: Optional[date] = Field(None, description="有效期截止日")
    trademark_registration_number: Optional[str] = Field(None, max_length=50, description="商标注册号")
    trademark_name: Optional[str] = Field(None, max_length=200, description="商标名称")
    international_class: Optional[str] = Field(None, max_length=50, description="国际类别")
    registrant: Optional[str] = Field(None, max_length=200, description="注册人")
    registrant_address: Optional[str] = Field(None, max_length=500, description="注册人地址")
    certificate_type: Optional[str] = Field(None, max_length=50, description="证书类型")
    certificate_content: Optional[str] = Field(None, description="证书内容")
    attached_documents: Optional[str] = Field(None, description="附随文件")
    archive_number: Optional[str] = Field(None, max_length=100, description="归档编号")
    archive_date: Optional[date] = Field(None, description="归档日期")
    archive_location: Optional[str] = Field(None, max_length=200, description="归档位置")
    archivist: Optional[str] = Field(None, max_length=100, description="归档人")
    file_path: Optional[str] = Field(None, max_length=500, description="文件路径")
    file_name: Optional[str] = Field(None, max_length=255, description="文件名")
    file_size: Optional[int] = Field(None, description="文件大小")
    access_permissions: Optional[str] = Field(None, max_length=200, description="访问权限")
    retrieval_records: Optional[str] = Field(None, description="借阅记录")
    destruction_date: Optional[date] = Field(None, description="销毁日期")
    destruction_reason: Optional[str] = Field(None, description="销毁原因")
    remarks: Optional[str] = Field(None, description="备注")
    trademark_id: int = Field(..., description="商标ID")


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(CertificateBase):
    certificate_number: Optional[str] = Field(None, max_length=100)
    certificate_date: Optional[date] = Field(None)
    trademark_id: Optional[int] = Field(None)


class CertificateResponse(CertificateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
