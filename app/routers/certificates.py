from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.schemas.certificate import CertificateCreate, CertificateUpdate, CertificateResponse
from app.schemas.common import PaginatedResponse
from app.services import certificate_service


class ArchiveCertificateRequest(BaseModel):
    archive_number: Optional[str] = Field(None, max_length=100, description="归档编号")
    archive_location: Optional[str] = Field(None, max_length=200, description="归档位置")
    archivist: Optional[str] = Field(None, max_length=100, description="归档人")


router = APIRouter(prefix="/api/certificates", tags=["证书归档管理"])


@router.get("", response_model=PaginatedResponse[CertificateResponse])
def list_certificates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    trademark_id: Optional[int] = Query(None, description="商标ID"),
    certificate_type: Optional[str] = Query(None, description="证书类型"),
    archive_location: Optional[str] = Query(None, description="归档位置"),
    archivist: Optional[str] = Query(None, description="归档人"),
    start_date: Optional[date] = Query(None, description="证书日期开始"),
    end_date: Optional[date] = Query(None, description="证书日期结束"),
    keyword: Optional[str] = Query(None, description="搜索关键词（证书编号/注册号/商标名称/注册人/归档编号）"),
    db: Session = Depends(get_db)
):
    try:
        items, total = certificate_service.list_certificates(
            db=db,
            page=page,
            page_size=page_size,
            trademark_id=trademark_id,
            certificate_type=certificate_type,
            archive_location=archive_location,
            archivist=archivist,
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
            detail=f"查询证书归档记录失败: {str(e)}"
        )


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    try:
        return certificate_service.get_certificate(db, certificate_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取证书归档记录失败: {str(e)}"
        )


@router.post("", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def create_certificate(
    certificate_in: CertificateCreate,
    db: Session = Depends(get_db)
):
    try:
        return certificate_service.create_certificate(db, certificate_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建证书归档记录失败: {str(e)}"
        )


@router.put("/{certificate_id}", response_model=CertificateResponse)
def update_certificate(
    certificate_id: int,
    certificate_in: CertificateUpdate,
    db: Session = Depends(get_db)
):
    try:
        return certificate_service.update_certificate(db, certificate_id, certificate_in)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新证书归档记录失败: {str(e)}"
        )


@router.post("/{certificate_id}/archive", response_model=CertificateResponse)
def archive_certificate(
    certificate_id: int,
    request: ArchiveCertificateRequest,
    db: Session = Depends(get_db)
):
    try:
        return certificate_service.archive_certificate(
            db=db,
            certificate_id=certificate_id,
            archive_number=request.archive_number,
            archive_location=request.archive_location,
            archivist=request.archivist
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归档证书失败: {str(e)}"
        )


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    try:
        certificate_service.delete_certificate(db, certificate_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除证书归档记录失败: {str(e)}"
        )
