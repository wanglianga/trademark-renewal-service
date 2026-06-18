from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.schemas.correction import CorrectionCreate, CorrectionUpdate, CorrectionResponse
from app.schemas.common import PaginatedResponse
from app.services import correction_service


class SubmitCorrectionRequest(BaseModel):
    correction_content: Optional[str] = Field(None, description="补正内容")
    correction_materials: Optional[str] = Field(None, description="补正材料")
    corrector: Optional[str] = Field(None, max_length=100, description="补正人")


router = APIRouter(prefix="/api/corrections", tags=["补正管理"])


@router.get("", response_model=PaginatedResponse[CorrectionResponse])
def list_corrections(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    correction_type: Optional[str] = Query(None, description="补正类型"),
    correction_status: Optional[str] = Query(None, description="补正状态"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    start_date: Optional[date] = Query(None, description="补正日期开始"),
    end_date: Optional[date] = Query(None, description="补正日期结束"),
    deadline_start: Optional[date] = Query(None, description="补正期限开始"),
    deadline_end: Optional[date] = Query(None, description="补正期限结束"),
    keyword: Optional[str] = Query(None, description="搜索关键词（补正编号/原因/补正人）"),
    db: Session = Depends(get_db)
):
    try:
        items, total = correction_service.list_corrections(
            db=db,
            page=page,
            page_size=page_size,
            trademark_id=trademark_id,
            correction_type=correction_type,
            correction_status=correction_status,
            is_overdue=is_overdue,
            start_date=start_date,
            end_date=end_date,
            deadline_start=deadline_start,
            deadline_end=deadline_end,
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
            detail=f"查询补正记录失败: {str(e)}"
        )


@router.get("/{correction_id}", response_model=CorrectionResponse)
def get_correction(
    correction_id: int,
    db: Session = Depends(get_db)
):
    try:
        return correction_service.get_correction(db, correction_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取补正记录失败: {str(e)}"
        )


@router.get("/{correction_id}/check-overdue", response_model=CorrectionResponse)
def check_overdue(
    correction_id: int,
    db: Session = Depends(get_db)
):
    try:
        return correction_service.check_overdue(db, correction_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查补正逾期失败: {str(e)}"
        )


@router.post("", response_model=CorrectionResponse, status_code=status.HTTP_201_CREATED)
def create_correction(
    correction_in: CorrectionCreate,
    db: Session = Depends(get_db)
):
    try:
        return correction_service.create_correction(db, correction_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建补正记录失败: {str(e)}"
        )


@router.put("/{correction_id}", response_model=CorrectionResponse)
def update_correction(
    correction_id: int,
    correction_in: CorrectionUpdate,
    db: Session = Depends(get_db)
):
    try:
        return correction_service.update_correction(db, correction_id, correction_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新补正记录失败: {str(e)}"
        )


@router.post("/{correction_id}/submit", response_model=CorrectionResponse)
def submit_correction(
    correction_id: int,
    request: SubmitCorrectionRequest,
    db: Session = Depends(get_db)
):
    try:
        return correction_service.submit_correction(
            db=db,
            correction_id=correction_id,
            correction_content=request.correction_content,
            correction_materials=request.correction_materials,
            corrector=request.corrector
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交补正失败: {str(e)}"
        )


@router.delete("/{correction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_correction(
    correction_id: int,
    db: Session = Depends(get_db)
):
    try:
        correction_service.delete_correction(db, correction_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除补正记录失败: {str(e)}"
        )
