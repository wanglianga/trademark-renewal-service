from sqlalchemy import Column, String, Date, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class ReminderType(str, enum.Enum):
    EXPIRY = "expiry"
    GRACE_PERIOD = "grace_period"
    CORRECTION_DEADLINE = "correction_deadline"
    FEE_PAYMENT = "fee_payment"
    MATERIALS_PENDING = "materials_pending"
    APPEAL_DEADLINE = "appeal_deadline"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Reminder(BaseModel):
    __tablename__ = "reminders"

    reminder_type = Column(String(50), nullable=False)
    reminder_date = Column(Date, nullable=False)
    deadline_date = Column(Date)
    days_remaining = Column(Integer)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    recipient = Column(String(200))
    recipient_email = Column(String(200))
    recipient_phone = Column(String(20))
    status = Column(String(50), default="pending")
    sent_at = Column(String(50))
    acknowledged_at = Column(String(50))
    acknowledged_by = Column(String(100))
    priority = Column(Integer, default=1)
    escalation_level = Column(Integer, default=1)
    notes = Column(Text)

    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)

    trademark = relationship("Trademark", back_populates="reminders")
