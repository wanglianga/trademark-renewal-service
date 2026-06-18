from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.trademark import TrademarkStatus
from app.schemas.trademark import (
    TrademarkCreate,
    TrademarkUpdate,
    TrademarkResponse,
    TrademarkStatusUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services import trademark_service

router = APIRouter(prefix="/api/trademarks", tags=["商标管理"])


@router.get("", response_model=PaginatedResponse[TrademarkResponse])
def list_trademarks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[TrademarkStatus] = Query(None, description="商标状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词（商标名称/注册号）"),
    assigned_agent_id: Optional[int] = Query(None, description="分配的代理人ID"),
    db: Session = Depends(get_db)
):
    items, total = trademark_service.list_trademarks(
        db=db,
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        status=status,
        keyword=keyword,
        assigned_agent_id=assigned_agent_id
    )
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{trademark_id}", response_model=TrademarkResponse)
def get_trademark(
    trademark_id: int,
    db: Session = Depends(get_db)
):
    return trademark_service.get_trademark(db, trademark_id)


@router.post("", response_model=TrademarkResponse, status_code=status.HTTP_201_CREATED)
def create_trademark(
    trademark_in: TrademarkCreate,
    db: Session = Depends(get_db)
):
    try:
        return trademark_service.create_trademark(db, trademark_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建商标失败: {str(e)}"
        )


@router.put("/{trademark_id}", response_model=TrademarkResponse)
def update_trademark(
    trademark_id: int,
    trademark_in: TrademarkUpdate,
    db: Session = Depends(get_db)
):
    try:
        return trademark_service.update_trademark(db, trademark_id, trademark_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新商标失败: {str(e)}"
        )


@router.patch("/{trademark_id}/status", response_model=TrademarkResponse)
def update_trademark_status(
    trademark_id: int,
    status_in: TrademarkStatusUpdate,
    db: Session = Depends(get_db)
):
    try:
        return trademark_service.update_trademark_status(db, trademark_id, status_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新商标状态失败: {str(e)}"
        )


@router.delete("/{trademark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trademark(
    trademark_id: int,
    db: Session = Depends(get_db)
):
    try:
        trademark_service.delete_trademark(db, trademark_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除商标失败: {str(e)}"
        )
