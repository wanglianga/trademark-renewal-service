from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.correction import Correction
from app.models.trademark import Trademark, TrademarkStatus
from app.schemas.correction import CorrectionCreate, CorrectionUpdate


def get_correction(db: Session, correction_id: int) -> Correction:
    correction = db.query(Correction).filter(
        Correction.id == correction_id,
        Correction.is_deleted == False
    ).first()
    if not correction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"补正记录 ID {correction_id} 不存在"
        )
    return correction


def list_corrections(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    correction_type: Optional[str] = None,
    correction_status: Optional[str] = None,
    is_overdue: Optional[bool] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    deadline_start: Optional[date] = None,
    deadline_end: Optional[date] = None,
    keyword: Optional[str] = None
) -> Tuple[List[Correction], int]:
    query = db.query(Correction).filter(Correction.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(Correction.trademark_id == trademark_id)
    if correction_type is not None:
        query = query.filter(Correction.correction_type == correction_type)
    if correction_status is not None:
        query = query.filter(Correction.correction_status == correction_status)
    if is_overdue is not None:
        query = query.filter(Correction.is_overdue == is_overdue)
    if start_date is not None:
        query = query.filter(Correction.correction_date >= start_date)
    if end_date is not None:
        query = query.filter(Correction.correction_date <= end_date)
    if deadline_start is not None:
        query = query.filter(Correction.deadline >= deadline_start)
    if deadline_end is not None:
        query = query.filter(Correction.deadline <= deadline_end)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (Correction.correction_number.ilike(search_pattern)) |
            (Correction.correction_reason.ilike(search_pattern)) |
            (Correction.corrector.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(Correction.correction_date.desc(), Correction.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def check_overdue(db: Session, correction_id: int) -> Correction:
    correction = get_correction(db, correction_id)
    today = date.today()

    if correction.deadline and today > correction.deadline:
        correction.is_overdue = True
        correction.correction_status = "overdue"
        db.commit()
        db.refresh(correction)

    return correction


def create_correction(db: Session, correction_in: CorrectionCreate) -> Correction:
    trademark = db.query(Trademark).filter(
        Trademark.id == correction_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {correction_in.trademark_id} 不存在"
        )

    correction_data = correction_in.model_dump()
    correction = Correction(**correction_data)
    db.add(correction)

    trademark.status = TrademarkStatus.CORRECTION_REQUIRED
    trademark.notes = (trademark.notes or "") + f"\n{date.today()} 需补正，补正编号: {correction.correction_number or '未分配'}"

    db.commit()
    db.refresh(correction)

    check_overdue(db, correction.id)

    return correction


def update_correction(
    db: Session,
    correction_id: int,
    correction_in: CorrectionUpdate
) -> Correction:
    correction = get_correction(db, correction_id)
    update_data = correction_in.model_dump(exclude_unset=True)

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
        setattr(correction, field, value)

    db.commit()
    db.refresh(correction)

    check_overdue(db, correction.id)

    return correction


def submit_correction(
    db: Session,
    correction_id: int,
    correction_content: Optional[str] = None,
    correction_materials: Optional[str] = None,
    corrector: Optional[str] = None
) -> Correction:
    correction = get_correction(db, correction_id)

    if correction.correction_status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该补正已提交，请勿重复提交"
        )

    if correction_content is not None:
        correction.correction_content = correction_content
    if correction_materials is not None:
        correction.correction_materials = correction_materials
    if corrector is not None:
        correction.corrector = corrector

    correction.correction_status = "submitted"
    correction.correction_complete_date = date.today()

    trademark = db.query(Trademark).filter(
        Trademark.id == correction.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if trademark:
        trademark.status = TrademarkStatus.CORRECTION_SUBMITTED
        trademark.notes = (trademark.notes or "") + f"\n{date.today()} 补正已提交，补正人: {corrector or '未指定'}"

    db.commit()
    db.refresh(correction)
    return correction


def delete_correction(db: Session, correction_id: int) -> None:
    correction = get_correction(db, correction_id)
    correction.is_deleted = True
    db.commit()
