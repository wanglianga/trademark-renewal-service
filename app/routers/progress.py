from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.trademark import TrademarkStatus
from app.schemas.common import ProgressBoardResponse, PaginatedResponse
from app.services import progress_service

router = APIRouter(prefix="/api/progress", tags=["进度看板"])


STAGE_OPTIONS = [
    "材料准备",
    "代理人审核",
    "费用确认",
    "提交申请",
    "官方受理",
    "补正处理",
    "审核通过",
    "证书归档"
]


@router.get("/board", response_model=PaginatedResponse[ProgressBoardResponse])
def get_progress_board(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    assigned_agent_id: Optional[int] = Query(None, description="代理人ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    status: Optional[TrademarkStatus] = Query(None, description="商标状态"),
    current_stage: Optional[str] = Query(None, description=f"当前环节: {', '.join(STAGE_OPTIONS)}"),
    is_blocked: Optional[bool] = Query(None, description="是否阻塞"),
    keyword: Optional[str] = Query(None, description="搜索关键词（商标名称/注册号/客户名称）"),
    db: Session = Depends(get_db)
):
    try:
        items, total = progress_service.get_progress_board(
            db=db,
            page=page,
            page_size=page_size,
            assigned_agent_id=assigned_agent_id,
            customer_id=customer_id,
            status=status.value if status else None,
            current_stage=current_stage,
            is_blocked=is_blocked,
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
            detail=f"获取进度看板失败: {str(e)}"
        )


@router.get("/trademark/{trademark_id}", response_model=ProgressBoardResponse)
def get_trademark_progress(
    trademark_id: int,
    db: Session = Depends(get_db)
):
    try:
        return progress_service.get_trademark_progress(db, trademark_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取商标进度失败: {str(e)}"
        )


@router.get("/statistics")
def get_progress_statistics(
    assigned_agent_id: Optional[int] = Query(None, description="代理人ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    db: Session = Depends(get_db)
):
    try:
        return progress_service.get_progress_statistics(
            db=db,
            assigned_agent_id=assigned_agent_id,
            customer_id=customer_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取进度统计失败: {str(e)}"
        )


@router.get("/stages")
def get_stage_options():
    return {
        "stages": [
            {"code": "materials_preparation", "name": "材料准备"},
            {"code": "agent_review", "name": "代理人审核"},
            {"code": "fee_confirmation", "name": "费用确认"},
            {"code": "submission", "name": "提交申请"},
            {"code": "official_acceptance", "name": "官方受理"},
            {"code": "correction", "name": "补正处理"},
            {"code": "approval", "name": "审核通过"},
            {"code": "certificate_archive", "name": "证书归档"}
        ],
        "statuses": [
            {"code": "not_started", "name": "未开始"},
            {"code": "in_progress", "name": "进行中"},
            {"code": "completed", "name": "已完成"},
            {"code": "blocked", "name": "阻塞"}
        ]
    }


@router.get("/blocked")
def get_blocked_trademarks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    assigned_agent_id: Optional[int] = Query(None, description="代理人ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    db: Session = Depends(get_db)
):
    try:
        items, total = progress_service.get_progress_board(
            db=db,
            page=page,
            page_size=page_size,
            assigned_agent_id=assigned_agent_id,
            customer_id=customer_id,
            is_blocked=True
        )

        blocked_items = []
        for item in items:
            blocked_stage = next((s for s in item.stages if s.notes and s.is_current), None)
            if blocked_stage:
                blocked_items.append({
                    "trademark_id": item.trademark_id,
                    "registration_number": item.registration_number,
                    "trademark_name": item.trademark_name,
                    "customer_name": item.customer_name,
                    "current_stage": item.current_stage,
                    "blocked_reason": blocked_stage.notes,
                    "blocked_days": blocked_stage.duration_days,
                    "assigned_agent": item.assigned_agent,
                    "last_updated": item.last_updated
                })

        total_pages = (total + page_size - 1) // page_size
        return PaginatedResponse(
            items=blocked_items,
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
            detail=f"获取阻塞商标失败: {str(e)}"
        )


@router.get("/by-agent/{agent_id}")
def get_progress_by_agent(
    agent_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    try:
        items, total = progress_service.get_progress_board(
            db=db,
            page=page,
            page_size=page_size,
            assigned_agent_id=agent_id
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
            detail=f"获取代理人进度失败: {str(e)}"
        )


@router.get("/by-customer/{customer_id}")
def get_progress_by_customer(
    customer_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    try:
        items, total = progress_service.get_progress_board(
            db=db,
            page=page,
            page_size=page_size,
            customer_id=customer_id
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
            detail=f"获取客户进度失败: {str(e)}"
        )
