from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.schemas.rejection import RejectionCreate, RejectionUpdate, RejectionResponse
from app.schemas.common import PaginatedResponse
from app.services import rejection_service


class SubmitReviewRequest(BaseModel):
    review_content: Optional[str] = Field(None, description="复审内容")
    review_result: Optional[str] = Field(None, max_length=100, description="复审结果")
    review_applicant: Optional[str] = Field(None, max_length=200, description="复审申请人")


router = APIRouter(prefix="/api/rejections", tags=["驳回管理"])


@router.get("", response_model=PaginatedResponse[RejectionResponse])
def list_rejections(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    is_reviewed: Optional[bool] = Query(None, description="是否已复审"),
    is_rejected_final: Optional[bool] = Query(None, description="是否最终驳回"),
    appeal_status: Optional[str] = Query(None, description="上诉状态"),
    start_date: Optional[date] = Query(None, description="驳回日期开始"),
    end_date: Optional[date] = Query(None, description="驳回日期结束"),
    keyword: Optional[str] = Query(None, description="搜索关键词（驳回编号/理由/复审申请人）"),
    db: Session = Depends(get_db)
):
    try:
        items, total = rejection_service.list_rejections(
            db=db,
            page=page,
            page_size=page_size,
            trademark_id=trademark_id,
            is_reviewed=is_reviewed,
            is_rejected_final=is_rejected_final,
            appeal_status=appeal_status,
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
            detail=f"查询驳回记录失败: {str(e)}"
        )


@router.get("/{rejection_id}", response_model=RejectionResponse)
def get_rejection(
    rejection_id: int,
    db: Session = Depends(get_db)
):
    try:
        return rejection_service.get_rejection(db, rejection_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取驳回记录失败: {str(e)}"
        )


@router.post("", response_model=RejectionResponse, status_code=status.HTTP_201_CREATED)
def create_rejection(
    rejection_in: RejectionCreate,
    db: Session = Depends(get_db)
):
    try:
        return rejection_service.create_rejection(db, rejection_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建驳回记录失败: {str(e)}"
        )


@router.put("/{rejection_id}", response_model=RejectionResponse)
def update_rejection(
    rejection_id: int,
    rejection_in: RejectionUpdate,
    db: Session = Depends(get_db)
):
    try:
        return rejection_service.update_rejection(db, rejection_id, rejection_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新驳回记录失败: {str(e)}"
        )


@router.post("/{rejection_id}/submit-review", response_model=RejectionResponse)
def submit_review(
    rejection_id: int,
    request: SubmitReviewRequest,
    db: Session = Depends(get_db)
):
    try:
        return rejection_service.submit_review(
            db=db,
            rejection_id=rejection_id,
            review_content=request.review_content,
            review_result=request.review_result,
            review_applicant=request.review_applicant
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交复审失败: {str(e)}"
        )


@router.delete("/{rejection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rejection(
    rejection_id: int,
    db: Session = Depends(get_db)
):
    try:
        rejection_service.delete_rejection(db, rejection_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除驳回记录失败: {str(e)}"
        )
