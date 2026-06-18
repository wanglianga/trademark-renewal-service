from sqlalchemy import Column, String, Integer, Numeric, Date, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class FeeType(str, enum.Enum):
    OFFICIAL = "official"
    SERVICE = "service"
    TOTAL = "total"


class FeeStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"


class Fee(BaseModel):
    __tablename__ = "fees"

    fee_type = Column(Enum(FeeType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="CNY")
    payment_deadline = Column(Date)
    payment_date = Column(Date)
    payment_method = Column(String(50))
    transaction_id = Column(String(100))
    status = Column(Enum(FeeStatus), default=FeeStatus.UNPAID, nullable=False)
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(Date)
    remarks = Column(Text)

    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)
    confirmed_by_id = Column(Integer, ForeignKey("users.id"))

    trademark = relationship("Trademark", back_populates="fees")
    confirmed_by = relationship("User", back_populates="created_fees")
