from datetime import date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.fee import Fee, FeeType, FeeStatus
from app.models.trademark import Trademark
from app.schemas.fee import FeeCreate, FeeUpdate


def get_fee(db: Session, fee_id: int) -> Fee:
    fee = db.query(Fee).filter(
        Fee.id == fee_id,
        Fee.is_deleted == False
    ).first()
    if not fee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"费用 ID {fee_id} 不存在"
        )
    return fee


def list_fees(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    trademark_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    fee_type: Optional[FeeType] = None,
    status: Optional[FeeStatus] = None,
    is_confirmed: Optional[bool] = None
) -> Tuple[List[Fee], int]:
    query = db.query(Fee).filter(Fee.is_deleted == False)

    if trademark_id is not None:
        query = query.filter(Fee.trademark_id == trademark_id)
    if customer_id is not None:
        query = query.join(Trademark).filter(
            Trademark.customer_id == customer_id,
            Trademark.is_deleted == False
        )
    if fee_type is not None:
        query = query.filter(Fee.fee_type == fee_type)
    if status is not None:
        query = query.filter(Fee.status == status)
    if is_confirmed is not None:
        query = query.filter(Fee.is_confirmed == is_confirmed)

    total = query.count()
    items = query.order_by(Fee.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def create_fee(db: Session, fee_in: FeeCreate) -> Fee:
    trademark = db.query(Trademark).filter(
        Trademark.id == fee_in.trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {fee_in.trademark_id} 不存在"
        )

    fee_data = fee_in.model_dump()

    try:
        fee_type_enum = FeeType(fee_data["fee_type"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的费用类型: {fee_data['fee_type']}"
        )
    fee_data["fee_type"] = fee_type_enum

    try:
        status_enum = FeeStatus(fee_data["status"])
    except (ValueError, KeyError):
        status_enum = FeeStatus.UNPAID
    fee_data["status"] = status_enum

    fee = Fee(**fee_data)
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


def update_fee(db: Session, fee_id: int, fee_in: FeeUpdate) -> Fee:
    fee = get_fee(db, fee_id)
    update_data = fee_in.model_dump(exclude_unset=True)

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

    if "fee_type" in update_data and update_data["fee_type"]:
        try:
            update_data["fee_type"] = FeeType(update_data["fee_type"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的费用类型: {update_data['fee_type']}"
            )

    if "status" in update_data and update_data["status"]:
        try:
            update_data["status"] = FeeStatus(update_data["status"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值: {update_data['status']}"
            )

    for field, value in update_data.items():
        setattr(fee, field, value)

    db.commit()
    db.refresh(fee)
    return fee


def confirm_payment(
    db: Session,
    fee_id: int,
    payment_date: Optional[date] = None,
    payment_method: Optional[str] = None,
    transaction_id: Optional[str] = None,
    confirmed_by_id: Optional[int] = None
) -> Fee:
    fee = get_fee(db, fee_id)

    if fee.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"费用 ID {fee_id} 已确认支付，无需重复确认"
        )

    fee.is_confirmed = True
    fee.status = FeeStatus.PAID
    fee.confirmed_at = payment_date or date.today()
    fee.payment_date = payment_date or date.today()
    if payment_method:
        fee.payment_method = payment_method
    if transaction_id:
        fee.transaction_id = transaction_id
    if confirmed_by_id:
        fee.confirmed_by_id = confirmed_by_id

    db.commit()
    db.refresh(fee)
    return fee


def delete_fee(db: Session, fee_id: int) -> None:
    fee = get_fee(db, fee_id)
    fee.is_deleted = True
    db.commit()
