from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.submission import SubmissionCreate, SubmissionUpdate, SubmissionResponse
from app.schemas.common import PaginatedResponse
from app.services import submission_service

router = APIRouter(prefix="/api/submissions", tags=["提交记录"])


@router.get("", response_model=PaginatedResponse[SubmissionResponse])
def list_submissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    submission_channel: Optional[str] = Query(None, description="提交渠道"),
    is_duplicate: Optional[int] = Query(None, description="是否重复提交"),
    keyword: Optional[str] = Query(None, description="搜索关键词（提交编号/申请人/跟踪号）"),
    db: Session = Depends(get_db)
):
    try:
        items, total = submission_service.list_submissions(
            db=db,
            page=page,
            page_size=page_size,
            trademark_id=trademark_id,
            start_date=start_date,
            end_date=end_date,
            submission_channel=submission_channel,
            is_duplicate=is_duplicate,
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
            detail=f"查询提交记录失败: {str(e)}"
        )


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db)
):
    try:
        return submission_service.get_submission(db, submission_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提交记录失败: {str(e)}"
        )


@router.get("/{trademark_id}/check-duplicate", response_model=dict)
def check_duplicate_submission(
    trademark_id: int,
    submission_date: date = Query(..., description="提交日期"),
    days_window: int = Query(30, ge=1, le=365, description="检测时间窗口（天）"),
    db: Session = Depends(get_db)
):
    try:
        is_duplicate, existing = submission_service.check_duplicate(
            db,
            trademark_id=trademark_id,
            submission_date=submission_date,
            days_window=days_window
        )
        return {
            "is_duplicate": is_duplicate,
            "existing_record": SubmissionResponse.model_validate(existing).model_dump() if existing else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查重复提交失败: {str(e)}"
        )


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db)
):
    try:
        return submission_service.create_submission(db, submission_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建提交记录失败: {str(e)}"
        )


@router.put("/{submission_id}", response_model=SubmissionResponse)
def update_submission(
    submission_id: int,
    submission_in: SubmissionUpdate,
    db: Session = Depends(get_db)
):
    try:
        return submission_service.update_submission(db, submission_id, submission_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新提交记录失败: {str(e)}"
        )


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db)
):
    try:
        submission_service.delete_submission(db, submission_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除提交记录失败: {str(e)}"
        )
