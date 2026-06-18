from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.trademark import Trademark, TrademarkStatus
from app.models.customer import Customer
from app.schemas.trademark import TrademarkCreate, TrademarkUpdate, TrademarkStatusUpdate
from app.utils.date_utils import calculate_grace_period_end


def get_trademark(db: Session, trademark_id: int) -> Trademark:
    trademark = db.query(Trademark).filter(
        Trademark.id == trademark_id,
        Trademark.is_deleted == False
    ).first()
    if not trademark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商标 ID {trademark_id} 不存在"
        )
    return trademark


def list_trademarks(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    customer_id: Optional[int] = None,
    status: Optional[TrademarkStatus] = None,
    keyword: Optional[str] = None,
    assigned_agent_id: Optional[int] = None
) -> Tuple[List[Trademark], int]:
    query = db.query(Trademark).filter(Trademark.is_deleted == False)

    if customer_id is not None:
        query = query.filter(Trademark.customer_id == customer_id)
    if status is not None:
        query = query.filter(Trademark.status == status)
    if assigned_agent_id is not None:
        query = query.filter(Trademark.assigned_agent_id == assigned_agent_id)
    if keyword:
        query = query.filter(
            (Trademark.trademark_name.ilike(f"%{keyword}%")) |
            (Trademark.registration_number.ilike(f"%{keyword}%"))
        )

    total = query.count()
    items = query.order_by(Trademark.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return items, total


def create_trademark(db: Session, trademark_in: TrademarkCreate) -> Trademark:
    if trademark_in.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == trademark_in.customer_id,
            Customer.is_deleted == False
        ).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"客户 ID {trademark_in.customer_id} 不存在"
            )

    existing = db.query(Trademark).filter(
        Trademark.registration_number == trademark_in.registration_number,
        Trademark.is_deleted == False
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"注册号 {trademark_in.registration_number} 已存在"
        )

    trademark_data = trademark_in.model_dump()
    if not trademark_data.get("grace_period_end") and trademark_data.get("expiry_date"):
        trademark_data["grace_period_end"] = calculate_grace_period_end(
            trademark_data["expiry_date"]
        )

    try:
        status_enum = TrademarkStatus(trademark_data["status"])
    except (ValueError, KeyError):
        status_enum = TrademarkStatus.DRAFT
    trademark_data["status"] = status_enum

    trademark = Trademark(**trademark_data)
    db.add(trademark)
    db.commit()
    db.refresh(trademark)
    return trademark


def update_trademark(
    db: Session,
    trademark_id: int,
    trademark_in: TrademarkUpdate
) -> Trademark:
    trademark = get_trademark(db, trademark_id)
    update_data = trademark_in.model_dump(exclude_unset=True)

    if update_data.get("customer_id"):
        customer = db.query(Customer).filter(
            Customer.id == update_data["customer_id"],
            Customer.is_deleted == False
        ).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"客户 ID {update_data['customer_id']} 不存在"
            )

    if update_data.get("registration_number"):
        existing = db.query(Trademark).filter(
            Trademark.registration_number == update_data["registration_number"],
            Trademark.id != trademark_id,
            Trademark.is_deleted == False
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"注册号 {update_data['registration_number']} 已存在"
            )

    if "expiry_date" in update_data and update_data["expiry_date"]:
        update_data["grace_period_end"] = calculate_grace_period_end(
            update_data["expiry_date"]
        )

    if "status" in update_data and update_data["status"]:
        try:
            update_data["status"] = TrademarkStatus(update_data["status"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值: {update_data['status']}"
            )

    for field, value in update_data.items():
        setattr(trademark, field, value)

    db.commit()
    db.refresh(trademark)
    return trademark


def update_trademark_status(
    db: Session,
    trademark_id: int,
    status_in: TrademarkStatusUpdate
) -> Trademark:
    trademark = get_trademark(db, trademark_id)

    try:
        new_status = TrademarkStatus(status_in.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态值: {status_in.status}"
        )

    trademark.status = new_status
    if status_in.notes:
        trademark.notes = (trademark.notes or "") + f"\n状态变更备注: {status_in.notes}"

    db.commit()
    db.refresh(trademark)
    return trademark


def delete_trademark(db: Session, trademark_id: int) -> None:
    trademark = get_trademark(db, trademark_id)
    trademark.is_deleted = True
    db.commit()
