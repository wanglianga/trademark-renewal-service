from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SubmissionRecord(BaseModel):
    __tablename__ = "submission_records"

    submission_number = Column(String(100), nullable=False)
    submission_date = Column(Date, nullable=False)
    submission_channel = Column(String(50))
    submission_type = Column(String(50))
    applicant = Column(String(200))
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    official_fee_paid = Column(Integer, default=0)
    official_fee_amount = Column(String(50))
    attached_materials = Column(Text)
    submission_notes = Column(Text)
    tracking_number = Column(String(100))
    is_duplicate = Column(Integer, default=0)
    duplicate_reason = Column(String(500))

    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)
    submitted_by_id = Column(Integer, ForeignKey("users.id"))

    trademark = relationship("Trademark", back_populates="submissions")
    submitted_by = relationship("User", back_populates="submitted_records")
