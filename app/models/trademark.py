from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import date
from app.models.base import BaseModel


class TrademarkStatus(str, enum.Enum):
    DRAFT = "draft"
    MATERIALS_PENDING = "materials_pending"
    MATERIALS_RECEIVED = "materials_received"
    REVIEWING = "reviewing"
    FEE_PENDING = "fee_pending"
    FEE_CONFIRMED = "fee_confirmed"
    READY_TO_SUBMIT = "ready_to_submit"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    CORRECTION_REQUIRED = "correction_required"
    CORRECTION_SUBMITTED = "correction_submitted"
    REJECTED = "rejected"
    APPROVED = "approved"
    CERTIFIED = "certified"
    ARCHIVED = "archived"


class Trademark(BaseModel):
    __tablename__ = "trademarks"

    registration_number = Column(String(50), nullable=False, index=True)
    trademark_name = Column(String(200), nullable=False)
    international_class = Column(Integer, nullable=False)
    application_date = Column(Date)
    registration_date = Column(Date)
    expiry_date = Column(Date, nullable=False)
    grace_period_end = Column(Date)
    designated_countries = Column(String(500))
    status = Column(Enum(TrademarkStatus), default=TrademarkStatus.DRAFT, nullable=False)
    current_stage = Column(String(100))
    notes = Column(Text)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"))
    has_subject_change = Column(Integer, default=0)

    customer = relationship("Customer", back_populates="trademarks")
    assigned_agent = relationship("User", back_populates="assigned_trademarks")
    entrustment = relationship("AgencyEntrustment", back_populates="trademark", uselist=False)
    fees = relationship("Fee", back_populates="trademark")
    materials = relationship("MaterialVersion", back_populates="trademark")
    submissions = relationship("SubmissionRecord", back_populates="trademark")
    acceptance = relationship("AcceptanceReceipt", back_populates="trademark", uselist=False)
    corrections = relationship("Correction", back_populates="trademark")
    rejections = relationship("Rejection", back_populates="trademark")
    certificate = relationship("CertificateArchive", back_populates="trademark", uselist=False)
    reminders = relationship("Reminder", back_populates="trademark")

    @property
    def is_expiring_soon(self) -> bool:
        if not self.expiry_date:
            return False
        days_until_expiry = (self.expiry_date - date.today()).days
        return 0 <= days_until_expiry <= 180

    @property
    def is_in_grace_period(self) -> bool:
        if not self.expiry_date or not self.grace_period_end:
            return False
        today = date.today()
        return self.expiry_date < today <= self.grace_period_end

    @property
    def is_overdue(self) -> bool:
        if not self.grace_period_end:
            return False
        return date.today() > self.grace_period_end
