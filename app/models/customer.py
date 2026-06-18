from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    name = Column(String(200), nullable=False)
    unified_social_credit_code = Column(String(50), unique=True, nullable=False)
    legal_representative = Column(String(100))
    phone = Column(String(20))
    email = Column(String(200))
    address = Column(String(500))
    industry = Column(String(100))
    remarks = Column(Text)

    trademarks = relationship("Trademark", back_populates="customer")
    entrustments = relationship("AgencyEntrustment", back_populates="customer")
    materials = relationship("MaterialVersion", back_populates="customer")
