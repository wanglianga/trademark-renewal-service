from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.certificate_archive import CertificateArchive
from app.models.trademark import Trademark, TrademarkStatus
from app.schemas.certificate import CertificateCreate, CertificateUpdate


def get_certificate(db: Session, certificate_id: int) -> CertificateArchive:
    certificate = db.query(CertificateArchive).filter(
        CertificateArchive.id == certificate_id,
        CertificateArchive.is_deleted == False
    ).first()
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"证书归档记录 ID {certificate_id} 不存在"
        )
    return certificate


def list_certificates(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    certificate_type: Optional[str] = None,
    archive_location: Optional[str] = None,
    archivist: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    keyword: Optional[str] = None
) -> Tuple[List[CertificateArchive], int]:
    query = db.query(CertificateArchive).filter(CertificateArchive.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(CertificateArchive.trademark_id == trademark_id)
    if certificate_type is not None:
        query = query.filter(CertificateArchive.certificate_type == certificate_type)
    if archive_location is not None:
        query = query.filter(CertificateArchive.archive_location == archive_location)
    if archivist is not None:
        query = query.filter(CertificateArchive.archivist == archivist)
    if start_date is not None:
        query = query.filter(CertificateArchive.certificate_date >= start_date)
    if end_date is not None:
        query = query.filter(CertificateArchive.certificate_date <= end_date)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (CertificateArchive.certificate_number.ilike(search_pattern)) |
            (CertificateArchive.trademark_registration_number.ilike(search_pattern)) |
            (CertificateArchive.trademark_name.ilike(search_pattern)) |
            (CertificateArchive.registrant.ilike(search_pattern)) |
            (CertificateArchive.archive_number.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(CertificateArchive.certificate_date.desc(), CertificateArchive.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def create_certificate(db: Session, certificate_in: CertificateCreate) -> CertificateArchive:
    trademark = db.query(Trademark).filter(
        Trademark.id == certificate_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {certificate_in.trademark_id} 不存在"
        )

    certificate_data = certificate_in.model_dump()
    certificate = CertificateArchive(**certificate_data)
    db.add(certificate)

    db.commit()
    db.refresh(certificate)
    return certificate


def update_certificate(
    db: Session,
    certificate_id: int,
    certificate_in: CertificateUpdate
) -> CertificateArchive:
    certificate = get_certificate(db, certificate_id)
    update_data = certificate_in.model_dump(exclude_unset=True)

    if update_data.get("trademark_id"):
        trademark = db.query(Trademark).filter(
            Trademark.id == update_data["trademark_id"],
            Trademark.is_deleted == False
        ).first()
        if not trademark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"商标 ID {update_data['trademark_id']} 不存在"
            )

    for field, value in update_data.items():
        setattr(certificate, field, value)

    db.commit()
    db.refresh(certificate)
    return certificate


def archive_certificate(
    db: Session,
    certificate_id: int,
    archive_number: Optional[str] = None,
    archive_location: Optional[str] = None,
    archivist: Optional[str] = None
) -> CertificateArchive:
    certificate = get_certificate(db, certificate_id)

    if certificate.archive_date is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该证书已归档，请勿重复操作"
        )

    if archive_number is not None:
        certificate.archive_number = archive_number
    if archive_location is not None:
        certificate.archive_location = archive_location
    if archivist is not None:
        certificate.archivist = archivist

    certificate.archive_date = date.today()

    trademark = db.query(Trademark).filter(
        Trademark.id == certificate.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if trademark:
        trademark.status = TrademarkStatus.ARCHIVED
        trademark.notes = (trademark.notes or "") + f"\n{date.today()} 证书已归档，归档人: {archivist or '未指定'}"

    db.commit()
    db.refresh(certificate)
    return certificate


def delete_certificate(db: Session, certificate_id: int) -> None:
    certificate = get_certificate(db, certificate_id)
    certificate.is_deleted = True
    db.commit()
