from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AgencyEntrustment(BaseModel):
    __tablename__ = "agency_entrustments"

    entrustment_number = Column(String(50), unique=True, nullable=False)
    entrustment_date = Column(Date)
    effective_date = Column(Date)
    expiry_date = Column(Date)
    service_scope = Column(Text)
    is_active = Column(Boolean, default=True)
    remarks = Column(Text)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)

    customer = relationship("Customer", back_populates="entrustments")
    trademark = relationship("Trademark", back_populates="entrustment")
