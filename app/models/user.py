from sqlalchemy import Column, String, Integer, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    FINANCE = "finance"
    CLIENT = "client"


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.AGENT, nullable=False)

    assigned_trademarks = relationship("Trademark", back_populates="assigned_agent")
    created_fees = relationship("Fee", back_populates="confirmed_by")
    submitted_records = relationship("SubmissionRecord", back_populates="submitted_by")
