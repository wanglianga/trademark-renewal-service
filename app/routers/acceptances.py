from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.acceptance import AcceptanceCreate, AcceptanceUpdate, AcceptanceResponse
from app.schemas.common import PaginatedResponse
from app.services import acceptance_service

router = APIRouter(prefix="/api/acceptances", tags=["受理回执"])


@router.get("", response_model=PaginatedResponse[AcceptanceResponse])
def list_acceptances(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    has_correction_deadline: Optional[int] = Query(None, description="是否有补正期限"),
    is_correction_overdue: Optional[int] = Query(None, description="补正是否逾期"),
    keyword: Optional[str] = Query(None, description="搜索关键词（受理编号/官方文号/商标名称/注册号）"),
    db: Session = Depends(get_db)
):
    try:
        items, total = acceptance_service.list_acceptances(
            db=db,
            page=page,
            page_size=page_size,
            trademark_id=trademark_id,
            start_date=start_date,
            end_date=end_date,
            has_correction_deadline=has_correction_deadline,
            is_correction_overdue=is_correction_overdue,
            keyword=keyword
        )
        total_pages = (total + page_size - 1) // page_size
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询受理回执失败: {str(e)}"
        )


@router.get("/{acceptance_id}", response_model=AcceptanceResponse)
def get_acceptance(
    acceptance_id: int,
    db: Session = Depends(get_db)
):
    try:
        return acceptance_service.get_acceptance(db, acceptance_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取受理回执失败: {str(e)}"
        )


@router.post("", response_model=AcceptanceResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance(
    acceptance_in: AcceptanceCreate,
    db: Session = Depends(get_db)
):
    try:
        return acceptance_service.create_acceptance(db, acceptance_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建受理回执失败: {str(e)}"
        )


@router.put("/{acceptance_id}", response_model=AcceptanceResponse)
def update_acceptance(
    acceptance_id: int,
    acceptance_in: AcceptanceUpdate,
    db: Session = Depends(get_db)
):
    try:
        return acceptance_service.update_acceptance(db, acceptance_id, acceptance_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新受理回执失败: {str(e)}"
        )


@router.delete("/{acceptance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_acceptance(
    acceptance_id: int,
    db: Session = Depends(get_db)
):
    try:
        acceptance_service.delete_acceptance(db, acceptance_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除受理回执失败: {str(e)}"
        )
