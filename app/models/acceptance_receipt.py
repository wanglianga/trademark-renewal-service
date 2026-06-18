from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AcceptanceReceipt(BaseModel):
    __tablename__ = "acceptance_receipts"

    receipt_number = Column(String(100), nullable=False)
    receipt_date = Column(Date, nullable=False)
    official_file_number = Column(String(100))
    acceptance_date = Column(Date)
    applicant = Column(String(200))
    trademark_registration_number = Column(String(50))
    trademark_name = Column(String(200))
    international_class = Column(String(50))
    receipt_content = Column(Text)
    attached_documents = Column(Text)
    deadline_for_correction = Column(Date)
    delivery_method = Column(String(50))
    received_date = Column(Date)
    processing_person = Column(String(100))
    remarks = Column(Text)
    has_correction_deadline = Column(Integer, default=0)
    is_correction_overdue = Column(Integer, default=0)

    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)

    trademark = relationship("Trademark", back_populates="acceptance")
