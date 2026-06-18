from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models import User
from app.schemas import (
    AgencyCreate,
    AgencyUpdate,
    AgencyResponse,
    PaginatedResponse
)
from app.services import agency_service

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


@router.get("", response_model=PaginatedResponse[AgencyResponse])
def list_agencies(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    is_active: Optional[bool] = Query(None, description="是否有效"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    skip = (page - 1) * page_size
    agencies, total = agency_service.list_agencies(
        db,
        skip=skip,
        limit=page_size,
        customer_id=customer_id,
        trademark_id=trademark_id,
        is_active=is_active,
        keyword=keyword
    )
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=agencies,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{agency_id}", response_model=AgencyResponse)
def get_agency(
    agency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return agency_service.get_agency(db, agency_id)


@router.post("", response_model=AgencyResponse, status_code=status.HTTP_201_CREATED)
def create_agency(
    agency_in: AgencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return agency_service.create_agency(db, agency_in)


@router.put("/{agency_id}", response_model=AgencyResponse)
def update_agency(
    agency_id: int,
    agency_in: AgencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return agency_service.update_agency(db, agency_id, agency_in)


@router.delete("/{agency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agency(
    agency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    agency_service.delete_agency(db, agency_id)
