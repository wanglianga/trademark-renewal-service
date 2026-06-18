from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.rejection import Rejection
from app.models.trademark import Trademark, TrademarkStatus
from app.schemas.rejection import RejectionCreate, RejectionUpdate


def get_rejection(db: Session, rejection_id: int) -> Rejection:
    rejection = db.query(Rejection).filter(
        Rejection.id == rejection_id,
        Rejection.is_deleted == False
    ).first()
    if not rejection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"驳回记录 ID {rejection_id} 不存在"
        )
    return rejection


def list_rejections(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    is_reviewed: Optional[bool] = None,
    is_rejected_final: Optional[bool] = None,
    appeal_status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    keyword: Optional[str] = None
) -> Tuple[List[Rejection], int]:
    query = db.query(Rejection).filter(Rejection.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(Rejection.trademark_id == trademark_id)
    if is_reviewed is not None:
        query = query.filter(Rejection.is_reviewed == is_reviewed)
    if is_rejected_final is not None:
        query = query.filter(Rejection.is_rejected_final == is_rejected_final)
    if appeal_status is not None:
        query = query.filter(Rejection.appeal_status == appeal_status)
    if start_date is not None:
        query = query.filter(Rejection.rejection_date >= start_date)
    if end_date is not None:
        query = query.filter(Rejection.rejection_date <= end_date)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (Rejection.rejection_number.ilike(search_pattern)) |
            (Rejection.rejection_reason.ilike(search_pattern)) |
            (Rejection.review_applicant.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(Rejection.rejection_date.desc(), Rejection.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def create_rejection(db: Session, rejection_in: RejectionCreate) -> Rejection:
    trademark = db.query(Trademark).filter(
        Trademark.id == rejection_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {rejection_in.trademark_id} 不存在"
        )

    rejection_data = rejection_in.model_dump()
    rejection = Rejection(**rejection_data)
    db.add(rejection)

    trademark.status = TrademarkStatus.REJECTED
    trademark.notes = (trademark.notes or "") + f"\n{date.today()} 已驳回，驳回编号: {rejection.rejection_number or '未分配'}"

    db.commit()
    db.refresh(rejection)
    return rejection


def update_rejection(
    db: Session,
    rejection_id: int,
    rejection_in: RejectionUpdate
) -> Rejection:
    rejection = get_rejection(db, rejection_id)
    update_data = rejection_in.model_dump(exclude_unset=True)

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
        setattr(rejection, field, value)

    db.commit()
    db.refresh(rejection)
    return rejection


def submit_review(
    db: Session,
    rejection_id: int,
    review_content: Optional[str] = None,
    review_result: Optional[str] = None,
    review_applicant: Optional[str] = None
) -> Rejection:
    rejection = get_rejection(db, rejection_id)

    if rejection.is_reviewed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该驳回已复审，请勿重复提交"
        )

    if review_content is not None:
        rejection.review_content = review_content
    if review_result is not None:
        rejection.review_result = review_result
    if review_applicant is not None:
        rejection.review_applicant = review_applicant

    rejection.is_reviewed = True
    rejection.review_date = date.today()

    if review_result and "维持" in review_result:
        rejection.is_rejected_final = True

    trademark = db.query(Trademark).filter(
        Trademark.id == rejection.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if trademark:
        status_note = f"\n{date.today()} 已提交复审，复审申请人: {review_applicant or '未指定'}"
        if review_result:
            status_note += f"，复审结果: {review_result}"
        trademark.notes = (trademark.notes or "") + status_note

    db.commit()
    db.refresh(rejection)
    return rejection


def delete_rejection(db: Session, rejection_id: int) -> None:
    rejection = get_rejection(db, rejection_id)
    rejection.is_deleted = True
    db.commit()
