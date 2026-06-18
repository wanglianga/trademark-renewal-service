from datetime import date, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.submission_record import SubmissionRecord
from app.models.trademark import Trademark, TrademarkStatus
from app.schemas.submission import SubmissionCreate, SubmissionUpdate


def get_submission(db: Session, submission_id: int) -> SubmissionRecord:
    submission = db.query(SubmissionRecord).filter(
        SubmissionRecord.id == submission_id,
        SubmissionRecord.is_deleted == False
    ).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"提交记录 ID {submission_id} 不存在"
        )
    return submission


def list_submissions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    submission_channel: Optional[str] = None,
    is_duplicate: Optional[int] = None,
    keyword: Optional[str] = None
) -> Tuple[List[SubmissionRecord], int]:
    query = db.query(SubmissionRecord).filter(SubmissionRecord.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(SubmissionRecord.trademark_id == trademark_id)
    if start_date is not None:
        query = query.filter(SubmissionRecord.submission_date >= start_date)
    if end_date is not None:
        query = query.filter(SubmissionRecord.submission_date <= end_date)
    if submission_channel is not None:
        query = query.filter(SubmissionRecord.submission_channel == submission_channel)
    if is_duplicate is not None:
        query = query.filter(SubmissionRecord.is_duplicate == is_duplicate)
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (SubmissionRecord.submission_number.ilike(search_pattern)) |
            (SubmissionRecord.applicant.ilike(search_pattern)) |
            (SubmissionRecord.tracking_number.ilike(search_pattern))
        )

    total = query.count()
    items = query.order_by(SubmissionRecord.submission_date.desc(), SubmissionRecord.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def check_duplicate(
    db: Session,
    trademark_id: int,
    submission_date: date,
    days_window: int = 30
) -> Tuple[bool, Optional[SubmissionRecord]]:
    start_date = submission_date - timedelta(days=days_window)
    end_date = submission_date + timedelta(days=days_window)

    existing = db.query(SubmissionRecord).filter(
        SubmissionRecord.trademark_id == trademark_id,
        SubmissionRecord.submission_date >= start_date,
        SubmissionRecord.submission_date <= end_date,
        SubmissionRecord.is_deleted == False
    ).first()

    if existing:
        return True, existing
    return False, None


def create_submission(db: Session, submission_in: SubmissionCreate) -> SubmissionRecord:
    trademark = db.query(Trademark).filter(
        Trademark.id == submission_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {submission_in.trademark_id} 不存在"
        )

    is_dup, dup_record = check_duplicate(
        db,
        trademark_id=submission_in.trademark_id,
        submission_date=submission_in.submission_date
    )

    submission_data = submission_in.model_dump()
    if is_dup:
        submission_data["is_duplicate"] = 1
        submission_data["duplicate_reason"] = (
            f"该商标在 {dup_record.submission_date} 已有提交记录（编号: {dup_record.submission_number}）"
        )

    submission = SubmissionRecord(**submission_data)
    db.add(submission)

    trademark.status = TrademarkStatus.SUBMITTED
    trademark.notes = (trademark.notes or "") + f"\n{submission.submission_date} 已提交，提交编号: {submission.submission_number}"

    db.commit()
    db.refresh(submission)
    return submission


def update_submission(
    db: Session,
    submission_id: int,
    submission_in: SubmissionUpdate
) -> SubmissionRecord:
    submission = get_submission(db, submission_id)
    update_data = submission_in.model_dump(exclude_unset=True)

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

    if update_data.get("trademark_id") or update_data.get("submission_date"):
        check_trademark_id = update_data.get("trademark_id", submission.trademark_id)
        check_submission_date = update_data.get("submission_date", submission.submission_date)
        is_dup, dup_record = check_duplicate(
            db,
            trademark_id=check_trademark_id,
            submission_date=check_submission_date
        )
        if is_dup and dup_record.id != submission.id:
            update_data["is_duplicate"] = 1
            update_data["duplicate_reason"] = (
                f"该商标在 {dup_record.submission_date} 已有提交记录（编号: {dup_record.submission_number}）"
            )

    for field, value in update_data.items():
        setattr(submission, field, value)

    db.commit()
    db.refresh(submission)
    return submission


def delete_submission(db: Session, submission_id: int) -> None:
    submission = get_submission(db, submission_id)
    submission.is_deleted = True
    db.commit()
