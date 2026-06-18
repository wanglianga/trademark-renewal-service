from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class CertificateArchive(BaseModel):
    __tablename__ = "certificate_archives"

    certificate_number = Column(String(100), nullable=False)
    certificate_date = Column(Date, nullable=False)
    issue_date = Column(Date)
    expiry_date = Column(Date)
    trademark_registration_number = Column(String(50))
    trademark_name = Column(String(200))
    international_class = Column(String(50))
    registrant = Column(String(200))
    registrant_address = Column(String(500))
    certificate_type = Column(String(50))
    certificate_content = Column(Text)
    attached_documents = Column(Text)
    archive_number = Column(String(100))
    archive_date = Column(Date)
    archive_location = Column(String(200))
    archivist = Column(String(100))
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    access_permissions = Column(String(200))
    retrieval_records = Column(Text)
    destruction_date = Column(Date)
    destruction_reason = Column(Text)
    remarks = Column(Text)

    trademark_id = Column(Integer, ForeignKey("trademarks.id"), nullable=False)

    trademark = relationship("Trademark", back_populates="certificate")
