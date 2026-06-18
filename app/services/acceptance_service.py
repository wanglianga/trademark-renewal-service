from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.acceptance_receipt import AcceptanceReceipt
from app.models.trademark import Trademark, TrademarkStatus
from app.schemas.acceptance import AcceptanceCreate, AcceptanceUpdate


def get_acceptance(db: Session, acceptance_id: int) -> AcceptanceReceipt:
    acceptance = db.query(AcceptanceReceipt).filter(
        AcceptanceReceipt.id == acceptance_id,
        AcceptanceReceipt.is_deleted == False
    ).first()
    if not acceptance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"受理回执 ID {acceptance_id} 不存在"
        )
    return acceptance


def list_acceptances(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    has_correction_deadline: Optional[int] = None,
    is_correction_overdue: Optional[int] = None,
    keyword: Optional[str] = None
) -> Tuple[List[AcceptanceReceipt], int]:
    query = db.query(AcceptanceReceipt).filter(AcceptanceReceipt.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(AcceptanceReceipt.trademark_id == trademark_id)
    if start_date is not None:
        query = query.filter(AcceptanceReceipt.receipt_date >= start_date)
    if end_date is not None:
        query = query.filter(AcceptanceReceipt.receipt_date <= end_date)
    if has_correction_deadline is not None:
        query = query.filter(AcceptanceReceipt.has_correction_deadline == has_correction_deadline)
    if is_correction_overdue is not None:
        query = query.filter(AcceptanceReceipt.is_correction_overdue == is_correction_overdue)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (AcceptanceReceipt.receipt_number.ilike(search_pattern)) |
            (AcceptanceReceipt.official_file_number.ilike(search_pattern)) |
            (AcceptanceReceipt.trademark_name.ilike(search_pattern)) |
            (AcceptanceReceipt.trademark_registration_number.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(AcceptanceReceipt.receipt_date.desc(), AcceptanceReceipt.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def create_acceptance(db: Session, acceptance_in: AcceptanceCreate) -> AcceptanceReceipt:
    trademark = db.query(Trademark).filter(
        Trademark.id == acceptance_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {acceptance_in.trademark_id} 不存在"
        )

    acceptance_data = acceptance_in.model_dump()
    acceptance = AcceptanceReceipt(**acceptance_data)
    db.add(acceptance)

    trademark.status = TrademarkStatus.ACCEPTED
    trademark.notes = (trademark.notes or "") + f"\n{acceptance.receipt_date} 已受理，受理编号: {acceptance.receipt_number}"

    db.commit()
    db.refresh(acceptance)
    return acceptance


def update_acceptance(
    db: Session,
    acceptance_id: int,
    acceptance_in: AcceptanceUpdate
) -> AcceptanceReceipt:
    acceptance = get_acceptance(db, acceptance_id)
    update_data = acceptance_in.model_dump(exclude_unset=True)

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
        setattr(acceptance, field, value)

    db.commit()
    db.refresh(acceptance)
    return acceptance


def delete_acceptance(db: Session, acceptance_id: int) -> None:
    acceptance = get_acceptance(db, acceptance_id)
    acceptance.is_deleted = True
    db.commit()
