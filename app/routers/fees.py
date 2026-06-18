from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.fee import FeeType, FeeStatus
from app.schemas.fee import FeeCreate, FeeUpdate, FeeResponse
from app.schemas.common import PaginatedResponse
from app.services import fee_service

router = APIRouter(prefix="/api/fees", tags=["费用管理"])


@router.get("", response_model=PaginatedResponse[FeeResponse])
def list_fees(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    fee_type: Optional[FeeType] = Query(None, description="费用类型"),
    status: Optional[FeeStatus] = Query(None, description="费用状态"),
    is_confirmed: Optional[bool] = Query(None, description="是否已确认"),
    db: Session = Depends(get_db)
):
    items, total = fee_service.list_fees(
        db=db,
        page=page,
        page_size=page_size,
        trademark_id=trademark_id,
        customer_id=customer_id,
        fee_type=fee_type,
        status=status,
        is_confirmed=is_confirmed
    )
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{fee_id}", response_model=FeeResponse)
def get_fee(
    fee_id: int,
    db: Session = Depends(get_db)
):
    return fee_service.get_fee(db, fee_id)


@router.post("", response_model=FeeResponse, status_code=status.HTTP_201_CREATED)
def create_fee(
    fee_in: FeeCreate,
    db: Session = Depends(get_db)
):
    try:
        return fee_service.create_fee(db, fee_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建费用失败: {str(e)}"
        )


@router.put("/{fee_id}", response_model=FeeResponse)
def update_fee(
    fee_id: int,
    fee_in: FeeUpdate,
    db: Session = Depends(get_db)
):
    try:
        return fee_service.update_fee(db, fee_id, fee_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新费用失败: {str(e)}"
        )


@router.post("/{fee_id}/confirm", response_model=FeeResponse)
def confirm_payment(
    fee_id: int,
    payment_date: Optional[date] = Query(None, description="支付日期，默认今天"),
    payment_method: Optional[str] = Query(None, description="支付方式"),
    transaction_id: Optional[str] = Query(None, description="交易流水号"),
    confirmed_by_id: Optional[int] = Query(None, description="确认人ID"),
    db: Session = Depends(get_db)
):
    try:
        return fee_service.confirm_payment(
            db=db,
            fee_id=fee_id,
            payment_date=payment_date,
            payment_method=payment_method,
            transaction_id=transaction_id,
            confirmed_by_id=confirmed_by_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认支付失败: {str(e)}"
        )


@router.delete("/{fee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee(
    fee_id: int,
    db: Session = Depends(get_db)
):
    try:
        fee_service.delete_fee(db, fee_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除费用失败: {str(e)}"
        )
