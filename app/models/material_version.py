from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean, DateTime, Date
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.models.base import BaseModel


class MaterialType(str, enum.Enum):
    BUSINESS_LICENSE = "business_license"
    POWER_OF_ATTORNEY = "power_of_attorney"
    TRADEMARK_LIST = "trademark_list"
    OTHER = "other"
    CORRECTION_POWER_OF_ATTORNEY = "correction_power_of_attorney"
    CORRECTION_SUBJECT_QUALIFICATION = "correction_subject_qualification"
    CORRECTION_CATEGORY_DESCRIPTION = "correction_category_description"
    CORRECTION_CHINESE_TRANSLATION = "correction_chinese_translation"
    CORRECTION_OTHER = "correction_other"


CORRECTION_MATERIAL_TYPES = {
    MaterialType.CORRECTION_POWER_OF_ATTORNEY,
    MaterialType.CORRECTION_SUBJECT_QUALIFICATION,
    MaterialType.CORRECTION_CATEGORY_DESCRIPTION,
    MaterialType.CORRECTION_CHINESE_TRANSLATION,
    MaterialType.CORRECTION_OTHER,
}

CORRECTION_TYPE_MATERIAL_MAP = {
    "power_of_attorney": MaterialType.CORRECTION_POWER_OF_ATTORNEY,
    "subject_qualification": MaterialType.CORRECTION_SUBJECT_QUALIFICATION,
    "主体资格": MaterialType.CORRECTION_SUBJECT_QUALIFICATION,
    "委托书": MaterialType.CORRECTION_POWER_OF_ATTORNEY,
    "category_description": MaterialType.CORRECTION_CATEGORY_DESCRIPTION,
    "类别说明": MaterialType.CORRECTION_CATEGORY_DESCRIPTION,
    "chinese_translation": MaterialType.CORRECTION_CHINESE_TRANSLATION,
    "中文译名": MaterialType.CORRECTION_CHINESE_TRANSLATION,
}


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
    approved_by = Column(String(100))
    approval_notes = Column(Text)

    submitted_at = Column(DateTime)
    handled_by = Column(String(100))
    replaced_reason = Column(Text)
    replaced_by_version_id = Column(Integer, ForeignKey("material_versions.id"))
    is_replaced = Column(Boolean, default=False, nullable=False)
    replaced_at = Column(DateTime)

    correction_id = Column(Integer, ForeignKey("corrections.id"))
    correction_type_required = Column(String(100))

    customer_id = Column(Integer, ForeignKey("customers.id"))
    trademark_id = Column(Integer, ForeignKey("trademarks.id"))

    customer = relationship("Customer", back_populates="materials")
    trademark = relationship("Trademark", back_populates="materials")
    correction = relationship("Correction", back_populates="material_versions")
    replaces_version = relationship(
        "MaterialVersion",
        remote_side="MaterialVersion.id",
        foreign_keys=[replaced_by_version_id],
        backref="replaced_versions"
    )
