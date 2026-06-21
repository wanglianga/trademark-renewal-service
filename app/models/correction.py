from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Correction(BaseModel):
    __tablename__ = "corrections"

    correction_number = Column(String(100))
    correction_date = Column(Date)
    correction_type = Column(String(50))
    correction_reason = Column(Text, nullable=False)
    correction_requirements = Column(Text, nullable=False)
    required_materials = Column(Text)
    deadline = Column(Date, nullable=False)
    is_overdue = Column(Boolean, default=False)
    correction_status = Column(String(50), default="pending")
    correction_content = Column(Text)
    corrector = Column(String(100))
    correction_complete_date = Column(Date)
    resubmission_date = Column(Date)
    resubmission_number = Column(String(100))
    official_response = Column(Text)
    correction_notes = Column(Text)
    reminder_count = Column(Integer, default=0)
    last_reminder_date = Column(Date)

    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)

    trademark = relationship("Trademark", back_populates="corrections")
    material_versions = relationship("MaterialVersion", back_populates="correction")
