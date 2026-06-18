from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Rejection(BaseModel):
    __tablename__ = "rejections"

    rejection_number = Column(String(100))
    rejection_date = Column(Date, nullable=False)
    rejection_reason = Column(Text, nullable=False)
    rejection_basis = Column(Text)
    review_deadline = Column(Date)
    is_reviewed = Column(Boolean, default=False)
    review_date = Column(Date)
    review_result = Column(String(100))
    review_content = Column(Text)
    review_applicant = Column(String(200))
    is_rejected_final = Column(Boolean, default=False)
    appeal_path = Column(String(100))
    appeal_deadline = Column(Date)
    appeal_status = Column(String(50), default="not_appealed")
    appeal_date = Column(Date)
    appeal_result = Column(Text)
    processing_notes = Column(Text)
    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)

    trademark = relationship("Trademark", back_populates="rejections")
