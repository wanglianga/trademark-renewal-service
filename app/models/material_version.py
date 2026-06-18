from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class MaterialType(str, enum.Enum):
    BUSINESS_LICENSE = "business_license"
    POWER_OF_ATTORNEY = "power_of_attorney"
    TRADEMARK_LIST = "trademark_list"
    OTHER = "other"


class MaterialVersion(BaseModel):
    __tablename__ = "material_versions"

    material_type = Column(Enum(MaterialType), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_hash = Column(String(64))
    is_current = Column(Boolean, default=True, nullable=False)
    uploaded_by = Column(String(100))
    description = Column(Text)
    review_notes = Column(Text)
    is_approved = Column(Boolean, default=False)
    approved_at = Column(String(50))

    customer_id = Column(Integer, ForeignKey("customers.id"))
    trademark_id = Column(Integer, ForeignKey("trademarks.id"))

    customer = relationship("Customer", back_populates="materials")
    trademark = relationship("Trademark", back_populates="materials")
