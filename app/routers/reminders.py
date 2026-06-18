from datetime import date
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.reminder import ReminderType, ReminderStatus
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.schemas.common import PaginatedResponse, BulkOperationResponse
from app.services import reminder_service

router = APIRouter(prefix="/api/reminders", tags=["提醒管理"])


@router.get("", response_model=PaginatedResponse[ReminderResponse])
def list_reminders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    reminder_type: Optional[ReminderType] = Query(None, description="提醒类型"),
    status: Optional[ReminderStatus] = Query(None, description="提醒状态"),
    priority: Optional[int] = Query(None, ge=1, le=3, description="优先级"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    try:
        items, total = reminder_service.list_reminders(
            db=db,
            page=page,
            page_size=page_size,
            trademark_id=trademark_id,
            reminder_type=reminder_type,
            status=status,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
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
            detail=f"获取提醒列表失败: {str(e)}"
        )


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    try:
        return reminder_service.get_reminder(db, reminder_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提醒详情失败: {str(e)}"
        )


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db)
):
    try:
        return reminder_service.create_reminder(db, reminder_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建提醒失败: {str(e)}"
        )


@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    reminder_in: ReminderUpdate,
    db: Session = Depends(get_db)
):
    try:
        return reminder_service.update_reminder(db, reminder_id, reminder_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新提醒失败: {str(e)}"
        )


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    try:
        reminder_service.delete_reminder(db, reminder_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除提醒失败: {str(e)}"
        )


@router.post("/generate-expiry", response_model=BulkOperationResponse)
def generate_expiry_reminders(
    days_threshold: int = Query(180, ge=1, le=365, description="临期天数阈值"),
    only_pending: bool = Query(True, description="仅生成未处理的提醒"),
    db: Session = Depends(get_db)
):
    try:
        count, reminders = reminder_service.generate_expiry_reminders(
            db=db,
            days_threshold=days_threshold,
            only_pending=only_pending
        )
        return BulkOperationResponse(
            success=True,
            processed_count=count,
            failed_count=0,
            errors=[],
            results=[
                {
                    "id": r.id,
                    "title": r.title,
                    "trademark_id": r.trademark_id,
                    "days_remaining": r.days_remaining
                }
                for r in reminders
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成临期提醒失败: {str(e)}"
        )


@router.post("/generate-correction", response_model=BulkOperationResponse)
def generate_correction_reminders(
    days_threshold: int = Query(15, ge=1, le=60, description="补正期限天数阈值"),
    only_pending: bool = Query(True, description="仅生成未处理的提醒"),
    db: Session = Depends(get_db)
):
    try:
        count, reminders = reminder_service.generate_correction_reminders(
            db=db,
            days_threshold=days_threshold,
            only_pending=only_pending
        )
        return BulkOperationResponse(
            success=True,
            processed_count=count,
            failed_count=0,
            errors=[],
            results=[
                {
                    "id": r.id,
                    "title": r.title,
                    "trademark_id": r.trademark_id,
                    "days_remaining": r.days_remaining
                }
                for r in reminders
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成补正提醒失败: {str(e)}"
        )


@router.post("/{reminder_id}/send", response_model=ReminderResponse)
def send_reminder(
    reminder_id: int,
    sent_by: Optional[str] = Query(None, description="发送人"),
    db: Session = Depends(get_db)
):
    try:
        return reminder_service.send_reminder(db, reminder_id, sent_by)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送提醒失败: {str(e)}"
        )


@router.post("/{reminder_id}/acknowledge", response_model=ReminderResponse)
def acknowledge_reminder(
    reminder_id: int,
    acknowledged_by: str = Query(..., description="确认人"),
    db: Session = Depends(get_db)
):
    try:
        return reminder_service.acknowledge_reminder(db, reminder_id, acknowledged_by)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认提醒失败: {str(e)}"
        )
